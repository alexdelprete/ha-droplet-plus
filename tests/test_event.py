"""Tests for Droplet event entity."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant.common import MockConfigEntry

from custom_components.droplet_plus.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util


async def test_event_entity_exists(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak event entity is created."""
    ent_reg = er.async_get(hass)
    events = [e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "event"]
    assert len(events) == 1
    assert "water_leak" in events[0].entity_id


async def test_event_types(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test event entity has correct event types."""
    ent_reg = er.async_get(hass)
    events = [e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "event"]
    state = hass.states.get(events[0].entity_id)
    assert state is not None


async def test_event_fires_on_leak_detected(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test event fires when leak is detected."""
    coordinator = mock_setup_entry.runtime_data

    # Simulate leak detection
    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.5) for i in range(24)]
    coordinator._evaluate_leak()
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    # Verify event was consumed
    assert coordinator.pending_leak_event is None
    assert coordinator.water_leak_detected is True


async def test_event_fires_on_leak_cleared(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test event fires when leak is cleared."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._water_leak_detected = True

    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.0) for i in range(24)]
    coordinator._evaluate_leak()
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    assert coordinator.pending_leak_event is None
    assert coordinator.water_leak_detected is False
