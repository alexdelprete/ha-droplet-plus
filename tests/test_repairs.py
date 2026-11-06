"""Tests for Droplet repair issues."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant.common import MockConfigEntry

from custom_components.droplet_plus.const import DOMAIN, EVENT_WATER_LEAK_DETECTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import async_get as async_get_issue_registry
from homeassistant.util import dt as dt_util


async def test_repair_created_on_leak(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test repair issue is created when leak is detected."""
    coordinator = mock_setup_entry.runtime_data

    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.5) for i in range(24)]
    coordinator._evaluate_leak()

    issue_registry = async_get_issue_registry(hass)
    issue = issue_registry.async_get_issue(DOMAIN, EVENT_WATER_LEAK_DETECTED)
    assert issue is not None


async def test_repair_resolved_on_clear(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test repair issue is resolved when leak clears."""
    coordinator = mock_setup_entry.runtime_data

    # First, trigger a leak
    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.5) for i in range(24)]
    coordinator._evaluate_leak()

    issue_registry = async_get_issue_registry(hass)
    issue = issue_registry.async_get_issue(DOMAIN, EVENT_WATER_LEAK_DETECTED)
    assert issue is not None

    # Now clear the leak
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.0) for i in range(24)]
    coordinator._evaluate_leak()

    issue = issue_registry.async_get_issue(DOMAIN, EVENT_WATER_LEAK_DETECTED)
    assert issue is None


async def test_no_repair_when_no_leak(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test no repair issue when no leak."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._evaluate_leak()

    issue_registry = async_get_issue_registry(hass)
    issue = issue_registry.async_get_issue(DOMAIN, EVENT_WATER_LEAK_DETECTED)
    assert issue is None
