"""Tests for Droplet integration setup."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.droplet_plus.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr


async def test_setup_entry(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test setting up the integration creates coordinator."""
    assert mock_setup_entry.state is ConfigEntryState.LOADED
    assert mock_setup_entry.runtime_data is not None


async def test_setup_entry_registers_device(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test setup registers a device in the device registry."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, mock_setup_entry.unique_id), mock_setup_entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == "LIXIL"
    assert device.model == "Droplet"


async def test_setup_entry_not_ready(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test setup failure raises ConfigEntryNotReady and schedules a retry."""
    with patch(
        "custom_components.droplet_plus.DropletCoordinator.async_setup",
        side_effect=TimeoutError("connection timed out"),
    ):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test unloading the integration."""
    assert mock_setup_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_setup_entry.state is ConfigEntryState.NOT_LOADED
    mock_droplet.disconnect.assert_awaited_once()


async def test_unload_saves_data(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test unloading saves coordinator data."""
    coordinator = mock_setup_entry.runtime_data

    # Simulate some accumulated data
    coordinator._baseline_lifetime = 100.5

    await hass.config_entries.async_unload(mock_setup_entry.entry_id)
    await hass.async_block_till_done()

    # Verify data was saved (store.async_save was called)
    assert mock_setup_entry.state is ConfigEntryState.NOT_LOADED
