"""Tests for Droplet binary sensor entity."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant.common import MockConfigEntry

from custom_components.droplet_plus.const import DOMAIN
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util


async def test_binary_sensor_exists(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak binary sensor is created."""
    ent_reg = er.async_get(hass)
    binary_sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "binary_sensor"
    ]
    assert len(binary_sensors) == 1
    assert "water_leak" in binary_sensors[0].entity_id


async def test_binary_sensor_off_by_default(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak binary sensor is off when no leak."""
    ent_reg = er.async_get(hass)
    binary_sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "binary_sensor"
    ]
    state = hass.states.get(binary_sensors[0].entity_id)
    assert state is not None
    assert state.state == "off"


async def test_binary_sensor_on_when_leak(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test leak binary sensor turns on when leak detected."""
    coordinator = mock_setup_entry.runtime_data

    # Simulate leak detection
    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.5) for i in range(24)]
    coordinator._evaluate_leak()
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    binary_sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "binary_sensor"
    ]
    state = hass.states.get(binary_sensors[0].entity_id)
    assert state is not None
    assert state.state == "on"


async def test_binary_sensor_device_class(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak binary sensor has moisture device class."""
    ent_reg = er.async_get(hass)
    binary_sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "binary_sensor"
    ]
    assert binary_sensors[0].original_device_class == BinarySensorDeviceClass.MOISTURE
