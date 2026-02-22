"""The Droplet integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import DropletCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.NUMBER,
    Platform.SENSOR,
]

type DropletConfigEntry = ConfigEntry[DropletCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: DropletConfigEntry) -> bool:
    """Set up Droplet from a config entry."""
    coordinator = DropletCoordinator(hass, entry)

    try:
        await coordinator.async_setup()
    except Exception as err:
        _LOGGER.error("Failed to set up Droplet: %s", err)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="connection_timeout",
        ) from err

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DropletConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
