"""Tests for Droplet coordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.droplet_plus.const import (
    EVENT_WATER_LEAK_CLEARED,
    EVENT_WATER_LEAK_DETECTED,
    L_TO_GAL,
)
from custom_components.droplet_plus.coordinator import DropletCoordinator
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .conftest import TEST_DEVICE_ID


async def test_on_update_captures_delta(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test _on_update captures volume delta and flow rate."""
    coordinator = mock_setup_entry.runtime_data

    mock_droplet.get_flow_rate.return_value = 3.0
    mock_droplet.get_volume_delta.return_value = 100.0  # mL

    # Simulate pydroplet accumulating 100 mL
    mock_droplet._accumulated_volumes["lifetime"] = 100.0
    coordinator._on_update(None)

    assert coordinator.flow_rate == 3.0
    assert coordinator.volume_delta == 100.0
    assert coordinator.lifetime_volume == pytest.approx(0.1)  # 100 mL = 0.1 L


async def test_volume_properties_combine_baseline_and_accumulator(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test volume properties combine baseline with pydroplet accumulator."""
    coordinator = mock_setup_entry.runtime_data

    # Set baseline from persistence
    coordinator._baseline_hourly = 5.0
    coordinator._baseline_daily = 100.0
    coordinator._baseline_lifetime = 8500.0

    # Simulate pydroplet accumulated volume (in mL)
    mock_droplet._accumulated_volumes["hourly"] = 500.0  # 0.5 L
    mock_droplet._accumulated_volumes["daily"] = 1000.0  # 1.0 L
    mock_droplet._accumulated_volumes["lifetime"] = 2000.0  # 2.0 L

    assert coordinator.hourly_volume == pytest.approx(5.5)
    assert coordinator.daily_volume == pytest.approx(101.0)
    assert coordinator.lifetime_volume == pytest.approx(8502.0)


async def test_on_update_skips_when_unavailable(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test _on_update skips processing when device unavailable."""
    coordinator = mock_setup_entry.runtime_data
    mock_droplet.get_availability.return_value = False

    coordinator._on_update(None)

    assert coordinator.lifetime_volume == 0.0
    mock_droplet.get_volume_delta.assert_not_called()


async def test_hourly_boundary_crossing(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test hourly period boundary resets accumulator."""
    coordinator = mock_setup_entry.runtime_data

    # Set accumulated volume for current hour
    coordinator._baseline_hourly = 0.5
    mock_droplet._accumulated_volumes["hourly"] = 500.0  # 0.5 L more

    # Force hour boundary crossing
    coordinator._hourly_reset = dt_util.now() - timedelta(hours=2)
    mock_droplet.get_volume_delta.return_value = 10.0
    coordinator._on_update(None)

    # Hourly baseline should be reset (accumulator was reset by mock side_effect)
    assert coordinator._baseline_hourly == 0.0
    mock_droplet.reset_accumulator.assert_any_call(
        "hourly", mock_droplet.reset_accumulator.call_args_list[0][0][1]
    )
    # Hourly consumption buffer should have the finalized hour
    assert len(coordinator._hourly_consumption) == 1
    assert coordinator._hourly_consumption[0][1] == pytest.approx(1.0)


async def test_daily_boundary_crossing(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test daily period boundary resets accumulator."""
    coordinator = mock_setup_entry.runtime_data

    coordinator._baseline_daily = 4.0
    mock_droplet._accumulated_volumes["daily"] = 1000.0  # 1.0 L

    # Force day boundary
    coordinator._daily_reset = dt_util.now() - timedelta(days=2)
    coordinator._hourly_reset = dt_util.now() - timedelta(hours=2)
    mock_droplet.get_volume_delta.return_value = 100.0
    coordinator._on_update(None)

    assert coordinator._baseline_daily == 0.0
    assert len(coordinator._daily_consumption) == 1
    assert coordinator._daily_consumption[0][1] == pytest.approx(5.0)


async def test_flow_samples_recorded(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test flow samples are recorded on each update."""
    coordinator = mock_setup_entry.runtime_data

    mock_droplet.get_flow_rate.return_value = 1.5
    mock_droplet.get_volume_delta.return_value = 10.0
    coordinator._on_update(None)

    mock_droplet.get_flow_rate.return_value = 2.5
    coordinator._on_update(None)

    assert len(coordinator._flow_samples) == 2
    assert coordinator._flow_samples[0][1] == 1.5
    assert coordinator._flow_samples[1][1] == 2.5


async def test_hourly_flow_stats_tracking(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test hourly max/min flow tracking."""
    coordinator = mock_setup_entry.runtime_data

    mock_droplet.get_volume_delta.return_value = 10.0

    mock_droplet.get_flow_rate.return_value = 1.0
    coordinator._on_update(None)

    mock_droplet.get_flow_rate.return_value = 5.0
    coordinator._on_update(None)

    mock_droplet.get_flow_rate.return_value = 2.0
    coordinator._on_update(None)

    assert coordinator._hourly_max_flow == 5.0
    assert coordinator._hourly_min_flow == 1.0


async def test_cost_calculation_metric(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test cost calculation with metric units."""
    coordinator = mock_setup_entry.runtime_data

    # Set tariff to 5.0 per m³
    hass.config_entries.async_update_entry(
        mock_setup_entry,
        options={**mock_setup_entry.options, "water_tariff": 5.0},
    )

    # Simulate 1000L = 1m³ via baseline
    coordinator._baseline_daily = 1000.0
    assert coordinator.daily_cost == pytest.approx(5.0)


async def test_cost_calculation_zero_tariff(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test cost is zero when tariff is zero."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._baseline_daily = 1000.0
    assert coordinator.daily_cost == 0.0


async def test_statistics_avg_flow_1h(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test average flow 1h computation."""
    coordinator = mock_setup_entry.runtime_data

    # No samples yet
    assert coordinator.avg_flow_1h is None

    # Add samples
    mock_droplet.get_volume_delta.return_value = 10.0
    mock_droplet.get_flow_rate.return_value = 2.0
    coordinator._on_update(None)

    mock_droplet.get_flow_rate.return_value = 4.0
    coordinator._on_update(None)

    assert coordinator.avg_flow_1h == pytest.approx(3.0)


async def test_leak_detection_triggered(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak detection triggers when min_flow > threshold."""
    coordinator = mock_setup_entry.runtime_data

    # Set threshold to 0 (default)
    # Set hourly flow stats with min > 0
    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.5) for i in range(24)]

    # Evaluate leak
    coordinator._evaluate_leak()

    assert coordinator.water_leak_detected is True
    assert coordinator.pending_leak_event is not None
    assert coordinator.pending_leak_event[0] == EVENT_WATER_LEAK_DETECTED


async def test_leak_detection_cleared(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak detection clears when min_flow <= threshold."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._water_leak_detected = True

    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts - 3600 * i, 2.0, 0.0) for i in range(24)]

    coordinator._evaluate_leak()

    assert coordinator.water_leak_detected is False
    assert coordinator.pending_leak_event is not None
    assert coordinator.pending_leak_event[0] == EVENT_WATER_LEAK_CLEARED


async def test_leak_no_change(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test leak detection does nothing when state unchanged."""
    coordinator = mock_setup_entry.runtime_data

    # No flow stats → min_flow is None → no change
    coordinator._evaluate_leak()
    assert coordinator.water_leak_detected is False
    assert coordinator.pending_leak_event is None


async def test_consume_leak_event(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test consuming a pending leak event."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._pending_leak_event = (
        EVENT_WATER_LEAK_DETECTED,
        {"min_flow": 0.5, "threshold": 0.0},
    )

    coordinator.consume_leak_event()
    assert coordinator.pending_leak_event is None


async def test_persistence_save_load(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test data persistence save and load cycle."""
    coordinator = mock_setup_entry.runtime_data

    # Set some baseline data
    coordinator._baseline_lifetime = 8500.5
    coordinator._baseline_daily = 123.4
    coordinator._water_leak_detected = True

    # Save
    await coordinator._async_save_data()

    # Reset values
    coordinator._baseline_lifetime = 0.0
    coordinator._baseline_daily = 0.0
    coordinator._water_leak_detected = False

    # Load
    await coordinator._async_load_data()

    assert coordinator._baseline_lifetime == pytest.approx(8500.5)
    assert coordinator._baseline_daily == pytest.approx(123.4)
    assert coordinator._water_leak_detected is True


async def test_buffer_trimming(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test buffer trimming removes old entries."""
    coordinator = mock_setup_entry.runtime_data
    now_ts = dt_util.now().timestamp()

    # Add old and new flow samples
    coordinator._flow_samples = [
        (now_ts - 7200, 1.0),  # 2h old (should be trimmed)
        (now_ts - 1800, 2.0),  # 30min old (should remain)
    ]

    coordinator._trim_buffers(now_ts)

    assert len(coordinator._flow_samples) == 1
    assert coordinator._flow_samples[0][1] == 2.0


async def test_accumulators_registered_on_setup(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test pydroplet accumulators are registered during setup."""
    registered_names = [call[0][0] for call in mock_droplet.add_accumulator.call_args_list]
    assert "hourly" in registered_names
    assert "daily" in registered_names
    assert "weekly" in registered_names
    assert "monthly" in registered_names
    assert "yearly" in registered_names
    assert "lifetime" in registered_names


async def test_identity_properties(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test device_id and volume_last_reset properties."""
    coordinator = mock_setup_entry.runtime_data
    assert coordinator.device_id == TEST_DEVICE_ID
    assert coordinator.volume_last_reset is not None


async def test_cost_calculation_us_customary(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test cost calculation uses gallons on US customary installs."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    coordinator = mock_setup_entry.runtime_data

    # Set tariff to 5.0 per gallon
    hass.config_entries.async_update_entry(
        mock_setup_entry,
        options={**mock_setup_entry.options, "water_tariff": 5.0},
    )

    # Simulate 1 gallon of consumption via baseline (in liters)
    coordinator._baseline_daily = L_TO_GAL
    assert coordinator.daily_cost == pytest.approx(5.0)


async def test_setup_waits_for_metadata(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test setup polls until device metadata becomes available."""
    availability = iter([False, True])
    mock_droplet.version_info_available.side_effect = lambda: next(availability, True)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_setup_metadata_timeout(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_droplet: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test setup logs a warning when device metadata never arrives."""
    mock_droplet.version_info_available.return_value = False

    with patch("custom_components.droplet_plus.coordinator.FW_VERSION_TIMEOUT", 0):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert "Timeout waiting for device metadata" in caplog.text


async def test_shutdown_cancels_running_listener(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test shutdown stops and cancels a still-running listen task."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._listen_task = hass.loop.create_task(asyncio.sleep(300))

    await coordinator.async_shutdown()

    assert coordinator._listen_task is None
    mock_droplet.stop_listening.assert_awaited()

    # Second shutdown is a no-op (no save timer, no listen task)
    await coordinator.async_shutdown()
    assert coordinator._listen_task is None


async def test_all_period_boundaries_crossing(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> None:
    """Test weekly, monthly, and yearly boundaries reset accumulators."""
    coordinator = mock_setup_entry.runtime_data

    past = dt_util.now() - timedelta(days=400)
    coordinator._hourly_reset = past
    coordinator._daily_reset = past
    coordinator._weekly_reset = past
    coordinator._monthly_reset = past
    coordinator._yearly_reset = past

    mock_droplet.get_volume_delta.return_value = 10.0
    coordinator._on_update(None)

    reset_names = [call[0][0] for call in mock_droplet.reset_accumulator.call_args_list]
    for name in ("hourly", "daily", "weekly", "monthly", "yearly"):
        assert name in reset_names

    assert coordinator._baseline_weekly == 0.0
    assert coordinator._baseline_monthly == 0.0
    assert coordinator._baseline_yearly == 0.0
    assert coordinator._weekly_reset > past
    assert coordinator._monthly_reset > past
    assert coordinator._yearly_reset > past


async def test_hourly_boundary_without_min_flow(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test hourly boundary skips flow stats when no flow was tracked."""
    coordinator = mock_setup_entry.runtime_data

    coordinator._hourly_reset = dt_util.now() - timedelta(hours=2)
    coordinator._hourly_min_flow = None
    coordinator._check_period_boundaries(dt_util.now())

    assert coordinator._hourly_flow_stats == []
    assert len(coordinator._hourly_consumption) == 1


async def test_stale_boundaries_on_restart(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test stale period boundaries are finalized after a restart."""
    coordinator = mock_setup_entry.runtime_data

    past = dt_util.now() - timedelta(days=400)
    coordinator._hourly_reset = past
    coordinator._daily_reset = past
    coordinator._weekly_reset = past
    coordinator._monthly_reset = past
    coordinator._yearly_reset = past
    coordinator._baseline_hourly = 1.0
    coordinator._baseline_daily = 2.0
    coordinator._baseline_weekly = 3.0
    coordinator._baseline_monthly = 4.0
    coordinator._baseline_yearly = 5.0

    coordinator._handle_stale_boundaries()

    assert coordinator._baseline_hourly == 0.0
    assert coordinator._baseline_daily == 0.0
    assert coordinator._baseline_weekly == 0.0
    assert coordinator._baseline_monthly == 0.0
    assert coordinator._baseline_yearly == 0.0
    assert len(coordinator._hourly_consumption) == 1
    assert coordinator._hourly_consumption[0][1] == pytest.approx(1.0)
    assert len(coordinator._daily_consumption) == 1
    assert coordinator._daily_consumption[0][1] == pytest.approx(2.0)
    assert coordinator._yearly_reset > past


async def test_leak_below_threshold_when_not_leaking(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test no leak event when min flow is below threshold and not leaking."""
    coordinator = mock_setup_entry.runtime_data

    now_ts = dt_util.now().timestamp()
    coordinator._hourly_flow_stats = [(now_ts, 2.0, 0.0)]

    coordinator._evaluate_leak()

    assert coordinator.water_leak_detected is False
    assert coordinator.pending_leak_event is None


async def test_save_periodic(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test the periodic save callback persists data."""
    coordinator = mock_setup_entry.runtime_data
    coordinator._baseline_lifetime = 42.0

    await coordinator._async_save_periodic(dt_util.now())

    data = await coordinator._store.async_load()
    assert data is not None
    assert data["lifetime_volume"] == pytest.approx(42.0)


async def test_parse_dt_fallback(
    hass: HomeAssistant,
) -> None:
    """Test _parse_dt returns the default for missing or invalid input."""
    default = dt_util.now()
    assert DropletCoordinator._parse_dt(None, default) is default
    assert DropletCoordinator._parse_dt("not-a-datetime", default) is default
