"""Tests for Droplet diagnostics."""

from __future__ import annotations

from pytest_homeassistant.common import MockConfigEntry

from custom_components.droplet_plus.const import VERSION
from custom_components.droplet_plus.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant


async def test_diagnostics_structure(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics returns expected structure."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)

    assert "config" in result
    assert "device" in result
    assert "coordinator" in result
    assert "buffers" in result


async def test_diagnostics_config(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics config section."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)
    config = result["config"]

    assert config["integration_version"] == VERSION
    assert config["domain"] == "droplet_plus"
    assert "options" in config


async def test_diagnostics_redaction(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics redacts sensitive data."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)

    # Host and token should be redacted in config data
    config_data = result["config"]["data"]
    assert config_data.get("host") == "**REDACTED**"
    assert config_data.get("token") == "**REDACTED**"

    # Serial number should be redacted in device data
    assert result["device"]["serial_number"] == "**REDACTED**"


async def test_diagnostics_device(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics device section."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)
    device = result["device"]

    assert device["model"] == "Droplet"
    assert device["manufacturer"] == "LIXIL"
    assert device["firmware"] == "1.2.3"
    assert "available" in device


async def test_diagnostics_coordinator(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics coordinator section."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)
    coord = result["coordinator"]

    assert "lifetime_volume" in coord
    assert "daily_volume" in coord
    assert "flow_rate" in coord
    assert "water_leak_detected" in coord
    assert "water_tariff" in coord


async def test_diagnostics_buffers(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics buffers section."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)
    buffers = result["buffers"]

    assert "flow_samples_count" in buffers
    assert "hourly_consumption_count" in buffers
    assert "daily_consumption_count" in buffers
    assert "hourly_flow_stats_count" in buffers
