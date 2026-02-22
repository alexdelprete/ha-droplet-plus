"""Config flow for Droplet."""

from __future__ import annotations

import logging
from typing import Any

from pydroplet.droplet import DropletConnection, DropletDiscovery
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithConfigEntry,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import (
    CONF_DEVICE_ID,
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    DEFAULT_WATER_LEAK_THRESHOLD,
    DEFAULT_WATER_TARIFF,
    DOMAIN,
)
from .helpers import normalize_pairing_code

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Required(CONF_TOKEN): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
    }
)


class DropletConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Droplet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._port: int = DropletConnection.DEFAULT_PORT
        self._token: str | None = None
        self._device_id: str | None = None
        self._service_name: str | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> DropletOptionsFlow:
        """Get the options flow for this handler."""
        return DropletOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step (manual setup)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = normalize_pairing_code(user_input[CONF_TOKEN])

            device_id = await self._async_try_connect(host, self._port, token, errors)
            if device_id:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                self._host = host
                self._token = token
                self._device_id = device_id
                return await self.async_step_options()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        self._host = str(discovery_info.host)
        self._port = discovery_info.port or DropletConnection.DEFAULT_PORT
        self._service_name = discovery_info.name

        _LOGGER.debug(
            "Zeroconf discovered Droplet at %s:%s (%s)",
            self._host,
            self._port,
            self._service_name,
        )

        # Use service name as a preliminary unique ID
        await self.async_set_unique_id(self._service_name)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host, CONF_PORT: self._port})

        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle pairing code entry for discovered device."""
        host = self._host  # Set by async_step_zeroconf
        if host is None:
            return self.async_abort(reason="unknown")
        errors: dict[str, str] = {}

        if user_input is not None:
            token = normalize_pairing_code(user_input[CONF_TOKEN])

            device_id = await self._async_try_connect(host, self._port, token, errors)
            if device_id:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                self._token = token
                self._device_id = device_id
                return await self.async_step_options()

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"host": host},
        )

    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options configuration after connection validation."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Droplet ({self._host})",
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_TOKEN: self._token,
                    CONF_DEVICE_ID: self._device_id,
                },
                options={
                    CONF_WATER_TARIFF: user_input[CONF_WATER_TARIFF],
                    CONF_WATER_LEAK_THRESHOLD: user_input[CONF_WATER_LEAK_THRESHOLD],
                },
            )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WATER_TARIFF,
                        default=DEFAULT_WATER_TARIFF,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=100,
                            step=0.01,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_WATER_LEAK_THRESHOLD,
                        default=DEFAULT_WATER_LEAK_THRESHOLD,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=10,
                            step=0.01,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = normalize_pairing_code(user_input[CONF_TOKEN])

            device_id = await self._async_try_connect(host, self._port, token, errors)
            if device_id:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_mismatch()

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    title=f"Droplet ({host})",
                    data_updates={
                        CONF_HOST: host,
                        CONF_PORT: self._port,
                        CONF_TOKEN: token,
                        CONF_DEVICE_ID: device_id,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=reconfigure_entry.data.get(CONF_HOST),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                    vol.Required(CONF_TOKEN): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )

    async def _async_try_connect(
        self,
        host: str,
        port: int,
        token: str,
        errors: dict[str, str],
    ) -> str | None:
        """Try connecting to the device, return device_id or None on failure."""
        session = async_get_clientsession(self.hass)
        discovery = DropletDiscovery(host, port, "")

        try:
            if not await discovery.try_connect(session, token):
                errors["base"] = "cannot_connect"
                return None
            return await discovery.get_device_id()
        except Exception:
            _LOGGER.exception("Error connecting to Droplet at %s:%s", host, port)
            errors["base"] = "cannot_connect"
            return None


class DropletOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle Droplet options flow."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WATER_TARIFF,
                        default=current.get(CONF_WATER_TARIFF, DEFAULT_WATER_TARIFF),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=100,
                            step=0.01,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_WATER_LEAK_THRESHOLD,
                        default=current.get(
                            CONF_WATER_LEAK_THRESHOLD,
                            DEFAULT_WATER_LEAK_THRESHOLD,
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=10,
                            step=0.01,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
