"""Tests for Droplet config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from custom_components.droplet.const import (
    CONF_DEVICE_ID,
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    DOMAIN,
)
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .conftest import TEST_DEVICE_ID, TEST_HOST, TEST_PORT, TEST_TOKEN


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_WATER_TARIFF: 3.50, CONF_WATER_LEAK_THRESHOLD: 0.05},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Droplet ({TEST_HOST})"
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_PORT] == TEST_PORT
    assert result["data"][CONF_TOKEN] == TEST_TOKEN
    assert result["data"][CONF_DEVICE_ID] == TEST_DEVICE_ID
    assert result["options"][CONF_WATER_TARIFF] == 3.50
    assert result["options"][CONF_WATER_LEAK_THRESHOLD] == 0.05


async def test_user_flow_cannot_connect(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
) -> None:
    """Test user flow with connection failure."""
    mock_discovery.try_connect = AsyncMock(return_value=False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_exception(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
) -> None:
    """Test user flow with unexpected exception."""
    mock_discovery.try_connect = AsyncMock(side_effect=Exception("Boom"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
    mock_config_entry,
) -> None:
    """Test user flow aborts when device already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_flow(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
) -> None:
    """Test zeroconf discovery flow."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=TEST_HOST,
        ip_addresses=[TEST_HOST],
        hostname="droplet.local.",
        name="Droplet-1234._droplet._tcp.local.",
        port=TEST_PORT,
        properties={},
        type="_droplet._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_WATER_TARIFF: 3.50, CONF_WATER_LEAK_THRESHOLD: 0.05},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_DEVICE_ID] == TEST_DEVICE_ID
    assert result["options"][CONF_WATER_TARIFF] == 3.50
    assert result["options"][CONF_WATER_LEAK_THRESHOLD] == 0.05


async def test_options_flow(
    hass: HomeAssistant,
    mock_setup_entry,
) -> None:
    """Test options flow."""
    result = await hass.config_entries.options.async_init(mock_setup_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_WATER_TARIFF: 5.50, CONF_WATER_LEAK_THRESHOLD: 0.1},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_WATER_TARIFF] == 5.50
    assert result["data"][CONF_WATER_LEAK_THRESHOLD] == 0.1


async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_setup_entry,
    mock_discovery: MagicMock,
) -> None:
    """Test reconfigure flow."""
    result = await mock_setup_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    new_host = "192.168.1.200"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_TOKEN: TEST_TOKEN},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
