"""Tests for Droplet sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.droplet.const import DOMAIN
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er


async def test_flow_rate_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test water flow rate sensor after a device update."""
    coordinator = mock_setup_entry.runtime_data

    # Trigger a device update so the coordinator captures the mock values
    coordinator._on_update(None)
    await hass.async_block_till_done()

    states = [s for s in hass.states.async_all("sensor") if "flow_rate" in s.entity_id]
    assert len(states) > 0
    state = states[0]
    assert state.state == "2.5"


async def test_volume_delta_sensor_disabled_by_default(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test water volume delta sensor is disabled by default."""
    ent_reg = er.async_get(hass)
    entries = [
        e
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and "volume_delta" in e.entity_id
    ]
    # Disabled by default means it should NOT have a state
    assert len(entries) == 1
    assert entries[0].disabled_by is not None


async def test_server_status_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test server status sensor is diagnostic."""
    ent_reg = er.async_get(hass)
    entries = [
        e
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and "server_status" in e.entity_id
    ]
    assert len(entries) == 1
    assert entries[0].entity_category == EntityCategory.DIAGNOSTIC


async def test_signal_quality_sensor(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test signal quality sensor is diagnostic."""
    ent_reg = er.async_get(hass)
    entries = [
        e
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and "signal_quality" in e.entity_id
    ]
    assert len(entries) == 1
    assert entries[0].entity_category == EntityCategory.DIAGNOSTIC


async def test_consumption_sensors_exist(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test all consumption period sensors are created."""
    ent_reg = er.async_get(hass)
    sensor_keys = [
        e.entity_id
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and e.domain == "sensor"
    ]

    # Check period sensors exist
    periods = ["hourly", "daily", "weekly", "monthly", "yearly", "lifetime"]
    for period in periods:
        matches = [s for s in sensor_keys if f"consumption_{period}" in s]
        assert len(matches) == 1, f"Missing consumption_{period} sensor"


async def test_cost_sensors_exist(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test all cost sensors are created."""
    ent_reg = er.async_get(hass)
    sensor_keys = [
        e.entity_id
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and e.domain == "sensor"
    ]

    cost_periods = ["daily", "weekly", "monthly", "yearly", "lifetime"]
    for period in cost_periods:
        matches = [s for s in sensor_keys if f"cost_{period}" in s]
        assert len(matches) == 1, f"Missing cost_{period} sensor"


async def test_statistics_sensors_exist(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test all statistics sensors are created."""
    ent_reg = er.async_get(hass)
    sensor_keys = [
        e.entity_id
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and e.domain == "sensor"
    ]

    stat_keys = [
        "avg_flow_1h",
        "peak_flow_24h",
        "peak_flow_7d",
        "min_flow_24h",
        "avg_hourly_24h",
        "peak_hourly_24h",
        "peak_hourly_7d",
        "avg_daily_7d",
        "avg_daily_30d",
        "peak_daily_30d",
    ]
    for key in stat_keys:
        matches = [s for s in sensor_keys if key in s]
        assert len(matches) == 1, f"Missing statistics sensor {key}"


async def test_total_sensor_count(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test total number of sensor entities is 25."""
    ent_reg = er.async_get(hass)
    sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "sensor"
    ]
    assert len(sensors) == 25


async def test_sensor_has_entity_name(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test sensors use has_entity_name pattern."""
    ent_reg = er.async_get(hass)
    sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "sensor"
    ]
    for sensor in sensors:
        assert sensor.has_entity_name is True


async def test_sensor_unique_ids(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test sensors have unique IDs based on coordinator unique_id."""
    ent_reg = er.async_get(hass)
    sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "sensor"
    ]
    unique_ids = {s.unique_id for s in sensors}
    assert len(unique_ids) == 25  # All unique


async def test_sensor_device_association(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test sensors are associated with the device."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    device = dev_reg.async_get_device(identifiers={(DOMAIN, mock_setup_entry.unique_id)})
    assert device is not None

    sensors = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "sensor"
    ]
    for sensor in sensors:
        assert sensor.device_id == device.id
