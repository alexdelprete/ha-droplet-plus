"""DataUpdateCoordinator for Droplet."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timedelta
import logging
import time
from typing import Any

from pydroplet.droplet import Droplet

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    CONF_DEVICE_ID,
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    CONNECT_DELAY,
    DEFAULT_WATER_LEAK_THRESHOLD,
    DEFAULT_WATER_TARIFF,
    DOMAIN,
    EVENT_WATER_LEAK_CLEARED,
    EVENT_WATER_LEAK_DETECTED,
    L_TO_GAL,
    L_TO_M3,
    ML_TO_L,
    SAVE_INTERVAL,
    STORAGE_KEY,
    STORAGE_VERSION,
    VERSION_TIMEOUT,
)
from .helpers import (
    compute_average,
    compute_max,
    is_new_day,
    is_new_hour,
    is_new_month,
    is_new_week,
    is_new_year,
    next_day,
    next_hour,
    next_month,
    next_week,
    next_year,
)

_LOGGER = logging.getLogger(__name__)

HOUR_SECONDS = 3600
DAY_SECONDS = 86400
WEEK_SECONDS = 604800


class DropletCoordinator(DataUpdateCoordinator[None]):
    """Coordinator for Droplet integration."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            config_entry=config_entry,
        )

        self._droplet = Droplet(
            host=config_entry.data[CONF_HOST],
            session=async_get_clientsession(hass),
            token=config_entry.data[CONF_TOKEN],
            port=config_entry.data[CONF_PORT],
            logger=_LOGGER,
        )

        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}_{config_entry.entry_id}",
        )

        # Current values (updated each WebSocket callback)
        self._flow_rate: float = 0.0
        self._volume_delta: float = 0.0
        self._volume_last_reset: datetime = dt_util.now()

        # Period baselines (liters) — persisted values; live totals combine
        # these with pydroplet accumulator readings
        self._baseline_lifetime: float = 0.0
        self._baseline_hourly: float = 0.0
        self._baseline_daily: float = 0.0
        self._baseline_weekly: float = 0.0
        self._baseline_monthly: float = 0.0
        self._baseline_yearly: float = 0.0

        # Period reset timestamps
        now = dt_util.now()
        self._hourly_reset: datetime = now
        self._daily_reset: datetime = now
        self._weekly_reset: datetime = now
        self._monthly_reset: datetime = now
        self._yearly_reset: datetime = now

        # Hourly flow tracking (for hourly_flow_stats buffer)
        self._hourly_max_flow: float = 0.0
        self._hourly_min_flow: float | None = None

        # Statistics buffers
        self._flow_samples: list[tuple[float, float]] = []  # (ts, L/min)
        self._hourly_consumption: list[tuple[float, float]] = []  # (ts, L)
        self._daily_consumption: list[tuple[float, float]] = []  # (ts, L)
        self._hourly_flow_stats: list[tuple[float, float, float]] = []  # (ts, max, min)

        # Leak detection
        self._water_leak_detected: bool = False
        self._pending_leak_event: tuple[str, dict[str, float]] | None = None

        # Background task handles
        self._listen_task: asyncio.Task[None] | None = None
        self._save_unsub: CALLBACK_TYPE | None = None

    # -- Identity --

    @property
    def unique_id(self) -> str:
        """Return unique ID for this coordinator."""
        return self.config_entry.unique_id or self.config_entry.entry_id

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.config_entry.data[CONF_DEVICE_ID]

    # -- Device metadata --

    @property
    def device_model(self) -> str:
        """Return the device model."""
        return self._droplet.get_model()

    @property
    def device_manufacturer(self) -> str:
        """Return the device manufacturer."""
        return self._droplet.get_manufacturer()

    @property
    def device_firmware(self) -> str:
        """Return the firmware version."""
        return self._droplet.get_fw_version()

    @property
    def device_serial(self) -> str:
        """Return the serial number."""
        return self._droplet.get_sn()

    # -- Availability --

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return self._droplet.get_availability()

    # -- Current values --

    @property
    def flow_rate(self) -> float:
        """Return current flow rate in L/min."""
        return self._flow_rate

    @property
    def volume_delta(self) -> float:
        """Return last captured volume delta in mL."""
        return self._volume_delta

    @property
    def volume_last_reset(self) -> datetime:
        """Return timestamp of last volume delta reset."""
        return self._volume_last_reset

    @property
    def server_status(self) -> str | None:
        """Return server status string."""
        return self._droplet.get_server_status()

    @property
    def signal_quality(self) -> str | None:
        """Return signal quality string."""
        return self._droplet.get_signal_quality()

    # -- Period consumption (liters) --

    @property
    def hourly_volume(self) -> float:
        """Return current hour consumption in liters."""
        return self._baseline_hourly + self._droplet.get_accumulated_volume("hourly") / ML_TO_L

    @property
    def daily_volume(self) -> float:
        """Return current day consumption in liters."""
        return self._baseline_daily + self._droplet.get_accumulated_volume("daily") / ML_TO_L

    @property
    def weekly_volume(self) -> float:
        """Return current week consumption in liters."""
        return self._baseline_weekly + self._droplet.get_accumulated_volume("weekly") / ML_TO_L

    @property
    def monthly_volume(self) -> float:
        """Return current month consumption in liters."""
        return self._baseline_monthly + self._droplet.get_accumulated_volume("monthly") / ML_TO_L

    @property
    def yearly_volume(self) -> float:
        """Return current year consumption in liters."""
        return self._baseline_yearly + self._droplet.get_accumulated_volume("yearly") / ML_TO_L

    @property
    def lifetime_volume(self) -> float:
        """Return lifetime consumption in liters."""
        return self._baseline_lifetime + self._droplet.get_accumulated_volume("lifetime") / ML_TO_L

    # -- Period resets --

    @property
    def hourly_reset(self) -> datetime:
        """Return hourly period reset timestamp."""
        return self._hourly_reset

    @property
    def daily_reset(self) -> datetime:
        """Return daily period reset timestamp."""
        return self._daily_reset

    @property
    def weekly_reset(self) -> datetime:
        """Return weekly period reset timestamp."""
        return self._weekly_reset

    @property
    def monthly_reset(self) -> datetime:
        """Return monthly period reset timestamp."""
        return self._monthly_reset

    @property
    def yearly_reset(self) -> datetime:
        """Return yearly period reset timestamp."""
        return self._yearly_reset

    # -- Cost calculation --

    @property
    def water_tariff(self) -> float:
        """Return the configured water tariff."""
        return self.config_entry.options.get(CONF_WATER_TARIFF, DEFAULT_WATER_TARIFF)

    @property
    def water_leak_threshold(self) -> float:
        """Return the configured leak detection threshold."""
        return self.config_entry.options.get(
            CONF_WATER_LEAK_THRESHOLD, DEFAULT_WATER_LEAK_THRESHOLD
        )

    @property
    def is_metric(self) -> bool:
        """Return True if the HA instance uses metric units."""
        return self.hass.config.units is METRIC_SYSTEM

    def _cost_for_volume(self, volume_l: float) -> float:
        """Calculate cost for a volume in liters using the configured tariff."""
        tariff = self.water_tariff
        if tariff == 0.0:
            return 0.0
        if self.is_metric:
            return volume_l / L_TO_M3 * tariff
        return volume_l / L_TO_GAL * tariff

    @property
    def daily_cost(self) -> float:
        """Return current day cost."""
        return self._cost_for_volume(self.daily_volume)

    @property
    def weekly_cost(self) -> float:
        """Return current week cost."""
        return self._cost_for_volume(self.weekly_volume)

    @property
    def monthly_cost(self) -> float:
        """Return current month cost."""
        return self._cost_for_volume(self.monthly_volume)

    @property
    def yearly_cost(self) -> float:
        """Return current year cost."""
        return self._cost_for_volume(self.yearly_volume)

    @property
    def lifetime_cost(self) -> float:
        """Return lifetime cost."""
        return self._cost_for_volume(self.lifetime_volume)

    # -- Statistics --

    @property
    def avg_flow_1h(self) -> float | None:
        """Return average flow rate over the last hour."""
        return compute_average(self._flow_samples, HOUR_SECONDS, time.time())

    @property
    def peak_flow_24h(self) -> float | None:
        """Return peak flow rate over the last 24 hours."""
        if not self._hourly_flow_stats:
            return None
        cutoff = time.time() - DAY_SECONDS
        valid = [mx for ts, mx, _mn in self._hourly_flow_stats if ts >= cutoff]
        return max(valid) if valid else None

    @property
    def peak_flow_7d(self) -> float | None:
        """Return peak flow rate over the last 7 days."""
        if not self._hourly_flow_stats:
            return None
        cutoff = time.time() - WEEK_SECONDS
        valid = [mx for ts, mx, _mn in self._hourly_flow_stats if ts >= cutoff]
        return max(valid) if valid else None

    @property
    def min_flow_24h(self) -> float | None:
        """Return minimum flow rate over the last 24 hours."""
        if not self._hourly_flow_stats:
            return None
        cutoff = time.time() - DAY_SECONDS
        valid = [mn for ts, _mx, mn in self._hourly_flow_stats if ts >= cutoff]
        return min(valid) if valid else None

    @property
    def avg_hourly_24h(self) -> float | None:
        """Return average hourly consumption over the last 24 hours."""
        return compute_average(self._hourly_consumption, DAY_SECONDS, time.time())

    @property
    def peak_hourly_24h(self) -> float | None:
        """Return peak hourly consumption over the last 24 hours."""
        return compute_max(self._hourly_consumption, DAY_SECONDS, time.time())

    @property
    def peak_hourly_7d(self) -> float | None:
        """Return peak hourly consumption over the last 7 days."""
        return compute_max(self._hourly_consumption, WEEK_SECONDS, time.time())

    @property
    def avg_daily_7d(self) -> float | None:
        """Return average daily consumption over the last 7 days."""
        return compute_average(self._daily_consumption, WEEK_SECONDS, time.time())

    @property
    def avg_daily_30d(self) -> float | None:
        """Return average daily consumption over the last 30 days."""
        return compute_average(self._daily_consumption, DAY_SECONDS * 30, time.time())

    @property
    def peak_daily_30d(self) -> float | None:
        """Return peak daily consumption over the last 30 days."""
        return compute_max(self._daily_consumption, DAY_SECONDS * 30, time.time())

    # -- Buffer counts (for diagnostics) --

    @property
    def flow_samples_count(self) -> int:
        """Return the number of flow samples in the buffer."""
        return len(self._flow_samples)

    @property
    def hourly_consumption_count(self) -> int:
        """Return the number of hourly consumption entries."""
        return len(self._hourly_consumption)

    @property
    def daily_consumption_count(self) -> int:
        """Return the number of daily consumption entries."""
        return len(self._daily_consumption)

    @property
    def hourly_flow_stats_count(self) -> int:
        """Return the number of hourly flow stats entries."""
        return len(self._hourly_flow_stats)

    # -- Leak detection --

    @property
    def water_leak_detected(self) -> bool:
        """Return True if a water leak is detected."""
        return self._water_leak_detected

    @property
    def pending_leak_event(self) -> tuple[str, dict[str, float]] | None:
        """Return pending leak event data, if any."""
        return self._pending_leak_event

    @callback
    def consume_leak_event(self) -> None:
        """Consume the pending leak event (called by event entity)."""
        self._pending_leak_event = None

    # -- Setup / Teardown --

    async def async_setup(self) -> None:
        """Set up the coordinator: load data, start WebSocket, start save timer."""
        await self._async_load_data()
        self._handle_stale_boundaries()
        self._register_accumulators()

        self._listen_task = self.config_entry.async_create_background_task(
            self.hass,
            self._droplet.listen_forever(CONNECT_DELAY, self._on_update),
            f"{DOMAIN}_listen_{self.config_entry.entry_id}",
        )

        # Wait for device metadata
        for _ in range(VERSION_TIMEOUT * 10):
            if self._droplet.version_info_available():
                break
            await asyncio.sleep(0.1)

        if not self._droplet.version_info_available():
            _LOGGER.warning(
                "Timeout waiting for device metadata from %s",
                self.config_entry.data[CONF_HOST],
            )

        # Periodic save
        self._save_unsub = async_track_time_interval(
            self.hass,
            self._async_save_periodic,
            timedelta(seconds=SAVE_INTERVAL),
        )

    async def async_shutdown(self) -> None:
        """Shut down the coordinator: stop listener, save data."""
        if self._save_unsub:
            self._save_unsub()
            self._save_unsub = None

        if self._listen_task and not self._listen_task.done():
            await self._droplet.stop_listening()
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        await self._droplet.disconnect()
        await self._async_save_data()

    async def _async_update_data(self) -> None:
        """Not used — push-based integration."""

    # -- WebSocket callback --

    @callback
    def _on_update(self, _data: Any) -> None:
        """Handle WebSocket update (called from event loop by pydroplet)."""
        if not self._droplet.get_availability():
            self.async_set_updated_data(None)
            return

        now = dt_util.now()
        now_ts = now.timestamp()

        # Capture volume delta for the delta sensor (resets on read!).
        # Volume accumulation is handled by pydroplet accumulators.
        self._volume_delta = self._droplet.get_volume_delta()

        # Store current values
        self._flow_rate = self._droplet.get_flow_rate()
        self._volume_last_reset = now

        # Track hourly flow stats
        if self._hourly_min_flow is None:
            self._hourly_min_flow = self._flow_rate
        else:
            self._hourly_min_flow = min(self._hourly_min_flow, self._flow_rate)
        self._hourly_max_flow = max(self._hourly_max_flow, self._flow_rate)

        # Check period boundaries
        self._check_period_boundaries(now)

        # Record flow sample
        self._flow_samples.append((now_ts, self._flow_rate))

        # Trim expired buffer entries
        self._trim_buffers(now_ts)

        # Evaluate leak detection
        self._evaluate_leak()

        # Notify entities
        self.async_set_updated_data(None)

    def _check_period_boundaries(self, now: datetime) -> None:
        """Check and handle period boundary crossings."""
        if is_new_hour(self._hourly_reset, now):
            # Finalize: baseline + pydroplet accumulated volume
            finalized = self.hourly_volume
            self._hourly_consumption.append((self._hourly_reset.timestamp(), finalized))
            if self._hourly_min_flow is not None:
                self._hourly_flow_stats.append(
                    (
                        self._hourly_reset.timestamp(),
                        self._hourly_max_flow,
                        self._hourly_min_flow,
                    )
                )
            # Reset accumulator and baseline
            self._droplet.reset_accumulator("hourly", next_hour(now))
            self._baseline_hourly = 0.0
            self._hourly_reset = now
            self._hourly_max_flow = 0.0
            self._hourly_min_flow = None

        if is_new_day(self._daily_reset, now):
            finalized = self.daily_volume
            self._daily_consumption.append((self._daily_reset.timestamp(), finalized))
            self._droplet.reset_accumulator("daily", next_day(now))
            self._baseline_daily = 0.0
            self._daily_reset = now

        if is_new_week(self._weekly_reset, now):
            self._droplet.reset_accumulator("weekly", next_week(now))
            self._baseline_weekly = 0.0
            self._weekly_reset = now

        if is_new_month(self._monthly_reset, now):
            self._droplet.reset_accumulator("monthly", next_month(now))
            self._baseline_monthly = 0.0
            self._monthly_reset = now

        if is_new_year(self._yearly_reset, now):
            self._droplet.reset_accumulator("yearly", next_year(now))
            self._baseline_yearly = 0.0
            self._yearly_reset = now

    def _handle_stale_boundaries(self) -> None:
        """Handle period boundaries that were crossed during restart."""
        now = dt_util.now()

        if is_new_hour(self._hourly_reset, now):
            self._hourly_consumption.append((self._hourly_reset.timestamp(), self._baseline_hourly))
            self._baseline_hourly = 0.0
            self._hourly_reset = now
            self._hourly_max_flow = 0.0
            self._hourly_min_flow = None

        if is_new_day(self._daily_reset, now):
            self._daily_consumption.append((self._daily_reset.timestamp(), self._baseline_daily))
            self._baseline_daily = 0.0
            self._daily_reset = now

        if is_new_week(self._weekly_reset, now):
            self._baseline_weekly = 0.0
            self._weekly_reset = now

        if is_new_month(self._monthly_reset, now):
            self._baseline_monthly = 0.0
            self._monthly_reset = now

        if is_new_year(self._yearly_reset, now):
            self._baseline_yearly = 0.0
            self._yearly_reset = now

    def _register_accumulators(self) -> None:
        """Register pydroplet accumulators for all period volumes."""
        now = dt_util.now()
        self._droplet.add_accumulator("hourly", next_hour(now))
        self._droplet.add_accumulator("daily", next_day(now))
        self._droplet.add_accumulator("weekly", next_week(now))
        self._droplet.add_accumulator("monthly", next_month(now))
        self._droplet.add_accumulator("yearly", next_year(now))
        self._droplet.add_accumulator("lifetime", datetime(9999, 12, 31, tzinfo=now.tzinfo))

    def _trim_buffers(self, now_ts: float) -> None:
        """Trim expired entries from statistics buffers."""
        # Flow samples: keep 1h
        cutoff_1h = now_ts - HOUR_SECONDS
        self._flow_samples = [(ts, v) for ts, v in self._flow_samples if ts >= cutoff_1h]

        # Hourly consumption + flow stats: keep 7d
        cutoff_7d = now_ts - WEEK_SECONDS
        self._hourly_consumption = [
            (ts, v) for ts, v in self._hourly_consumption if ts >= cutoff_7d
        ]
        self._hourly_flow_stats = [
            (ts, mx, mn) for ts, mx, mn in self._hourly_flow_stats if ts >= cutoff_7d
        ]

        # Daily consumption: keep 30d
        cutoff_30d = now_ts - DAY_SECONDS * 30
        self._daily_consumption = [(ts, v) for ts, v in self._daily_consumption if ts >= cutoff_30d]

    def _evaluate_leak(self) -> None:
        """Evaluate leak detection based on min_flow_24h vs threshold."""
        min_flow = self.min_flow_24h
        threshold = self.water_leak_threshold

        if min_flow is None:
            return

        was_leaking = self._water_leak_detected

        if min_flow > threshold and not was_leaking:
            self._water_leak_detected = True
            self._pending_leak_event = (
                EVENT_WATER_LEAK_DETECTED,
                {"min_flow": min_flow, "threshold": threshold},
            )
            _LOGGER.warning(
                "Water leak detected: min flow %.3f L/min exceeds threshold %.3f L/min",
                min_flow,
                threshold,
            )
            async_create_issue(
                self.hass,
                DOMAIN,
                EVENT_WATER_LEAK_DETECTED,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key=EVENT_WATER_LEAK_DETECTED,
            )

        elif min_flow <= threshold and was_leaking:
            self._water_leak_detected = False
            self._pending_leak_event = (
                EVENT_WATER_LEAK_CLEARED,
                {"min_flow": min_flow, "threshold": threshold},
            )
            _LOGGER.info("Water leak cleared: min flow %.3f L/min", min_flow)
            async_delete_issue(self.hass, DOMAIN, EVENT_WATER_LEAK_DETECTED)

    # -- Persistence --

    async def _async_save_periodic(self, _now: datetime) -> None:
        """Periodic save callback."""
        await self._async_save_data()

    async def _async_save_data(self) -> None:
        """Save persistent data to store."""
        data = {
            "lifetime_volume": self.lifetime_volume,
            "hourly_volume": self.hourly_volume,
            "hourly_reset": self._hourly_reset.isoformat(),
            "daily_volume": self.daily_volume,
            "daily_reset": self._daily_reset.isoformat(),
            "weekly_volume": self.weekly_volume,
            "weekly_reset": self._weekly_reset.isoformat(),
            "monthly_volume": self.monthly_volume,
            "monthly_reset": self._monthly_reset.isoformat(),
            "yearly_volume": self.yearly_volume,
            "yearly_reset": self._yearly_reset.isoformat(),
            "hourly_max_flow": self._hourly_max_flow,
            "hourly_min_flow": self._hourly_min_flow,
            "flow_samples": [[ts, v] for ts, v in self._flow_samples],
            "hourly_consumption": [[ts, v] for ts, v in self._hourly_consumption],
            "daily_consumption": [[ts, v] for ts, v in self._daily_consumption],
            "hourly_flow_stats": [[ts, mx, mn] for ts, mx, mn in self._hourly_flow_stats],
            "water_leak_detected": self._water_leak_detected,
        }
        await self._store.async_save(data)

    async def _async_load_data(self) -> None:
        """Load persistent data from store."""
        data = await self._store.async_load()
        if not data:
            return

        now = dt_util.now()

        self._baseline_lifetime = data.get("lifetime_volume", 0.0)
        self._baseline_hourly = data.get("hourly_volume", 0.0)
        self._hourly_reset = self._parse_dt(data.get("hourly_reset"), now)
        self._baseline_daily = data.get("daily_volume", 0.0)
        self._daily_reset = self._parse_dt(data.get("daily_reset"), now)
        self._baseline_weekly = data.get("weekly_volume", 0.0)
        self._weekly_reset = self._parse_dt(data.get("weekly_reset"), now)
        self._baseline_monthly = data.get("monthly_volume", 0.0)
        self._monthly_reset = self._parse_dt(data.get("monthly_reset"), now)
        self._baseline_yearly = data.get("yearly_volume", 0.0)
        self._yearly_reset = self._parse_dt(data.get("yearly_reset"), now)

        self._hourly_max_flow = data.get("hourly_max_flow", 0.0)
        self._hourly_min_flow = data.get("hourly_min_flow")

        self._flow_samples = [(s[0], s[1]) for s in data.get("flow_samples", [])]
        self._hourly_consumption = [(s[0], s[1]) for s in data.get("hourly_consumption", [])]
        self._daily_consumption = [(s[0], s[1]) for s in data.get("daily_consumption", [])]
        self._hourly_flow_stats = [(s[0], s[1], s[2]) for s in data.get("hourly_flow_stats", [])]

        self._water_leak_detected = data.get("water_leak_detected", False)

    @staticmethod
    def _parse_dt(value: str | None, default: datetime) -> datetime:
        """Parse ISO datetime string, returning default on failure."""
        if value:
            parsed = dt_util.parse_datetime(value)
            if parsed:
                return parsed
        return default
