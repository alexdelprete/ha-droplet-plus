"""Sensor platform for Droplet."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfVolume, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DropletConfigEntry
from .const import (
    DOMAIN,
    KEY_SERVER_STATUS,
    KEY_SIGNAL_QUALITY,
    KEY_WATER_AVG_DAILY_7D,
    KEY_WATER_AVG_DAILY_30D,
    KEY_WATER_AVG_FLOW_1H,
    KEY_WATER_AVG_HOURLY_24H,
    KEY_WATER_CONSUMPTION_DAILY,
    KEY_WATER_CONSUMPTION_HOURLY,
    KEY_WATER_CONSUMPTION_LIFETIME,
    KEY_WATER_CONSUMPTION_MONTHLY,
    KEY_WATER_CONSUMPTION_WEEKLY,
    KEY_WATER_CONSUMPTION_YEARLY,
    KEY_WATER_COST_DAILY,
    KEY_WATER_COST_LIFETIME,
    KEY_WATER_COST_MONTHLY,
    KEY_WATER_COST_WEEKLY,
    KEY_WATER_COST_YEARLY,
    KEY_WATER_FLOW_RATE,
    KEY_WATER_MIN_FLOW_24H,
    KEY_WATER_PEAK_DAILY_30D,
    KEY_WATER_PEAK_FLOW_7D,
    KEY_WATER_PEAK_FLOW_24H,
    KEY_WATER_PEAK_HOURLY_7D,
    KEY_WATER_PEAK_HOURLY_24H,
    KEY_WATER_VOLUME_DELTA,
)
from .coordinator import DropletCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class DropletSensorEntityDescription(SensorEntityDescription):
    """Describes a Droplet sensor entity."""

    value_fn: Callable[[DropletCoordinator], float | str | None]
    last_reset_fn: Callable[[DropletCoordinator], datetime | None] = lambda _: None
    is_cost: bool = False


SENSOR_DESCRIPTIONS: tuple[DropletSensorEntityDescription, ...] = (
    # -- Core sensors --
    DropletSensorEntityDescription(
        key=KEY_WATER_FLOW_RATE,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        value_fn=lambda c: c.flow_rate,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_VOLUME_DELTA,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.volume_delta,
        last_reset_fn=lambda c: c.volume_last_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_SERVER_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.server_status,
    ),
    DropletSensorEntityDescription(
        key=KEY_SIGNAL_QUALITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.signal_quality,
    ),
    # -- Period consumption sensors --
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_HOURLY,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.hourly_volume, 3),
        last_reset_fn=lambda c: c.hourly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_DAILY,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.daily_volume, 3),
        last_reset_fn=lambda c: c.daily_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_WEEKLY,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.weekly_volume, 3),
        last_reset_fn=lambda c: c.weekly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_MONTHLY,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.monthly_volume, 3),
        last_reset_fn=lambda c: c.monthly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_YEARLY,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.yearly_volume, 3),
        last_reset_fn=lambda c: c.yearly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_CONSUMPTION_LIFETIME,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: round(c.lifetime_volume, 3),
    ),
    # -- Cost sensors --
    DropletSensorEntityDescription(
        key=KEY_WATER_COST_DAILY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        is_cost=True,
        value_fn=lambda c: round(c.daily_cost, 2),
        last_reset_fn=lambda c: c.daily_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_COST_WEEKLY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        is_cost=True,
        value_fn=lambda c: round(c.weekly_cost, 2),
        last_reset_fn=lambda c: c.weekly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_COST_MONTHLY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        is_cost=True,
        value_fn=lambda c: round(c.monthly_cost, 2),
        last_reset_fn=lambda c: c.monthly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_COST_YEARLY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        is_cost=True,
        value_fn=lambda c: round(c.yearly_cost, 2),
        last_reset_fn=lambda c: c.yearly_reset,
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_COST_LIFETIME,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        is_cost=True,
        value_fn=lambda c: round(c.lifetime_cost, 2),
    ),
    # -- Statistics: flow --
    DropletSensorEntityDescription(
        key=KEY_WATER_AVG_FLOW_1H,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        value_fn=lambda c: _round_or_none(c.avg_flow_1h, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_PEAK_FLOW_24H,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        value_fn=lambda c: _round_or_none(c.peak_flow_24h, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_PEAK_FLOW_7D,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        value_fn=lambda c: _round_or_none(c.peak_flow_7d, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_MIN_FLOW_24H,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        value_fn=lambda c: _round_or_none(c.min_flow_24h, 3),
    ),
    # -- Statistics: hourly consumption --
    DropletSensorEntityDescription(
        key=KEY_WATER_AVG_HOURLY_24H,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.avg_hourly_24h, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_PEAK_HOURLY_24H,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.peak_hourly_24h, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_PEAK_HOURLY_7D,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.peak_hourly_7d, 3),
    ),
    # -- Statistics: daily consumption --
    DropletSensorEntityDescription(
        key=KEY_WATER_AVG_DAILY_7D,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.avg_daily_7d, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_AVG_DAILY_30D,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.avg_daily_30d, 3),
    ),
    DropletSensorEntityDescription(
        key=KEY_WATER_PEAK_DAILY_30D,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda c: _round_or_none(c.peak_daily_30d, 3),
    ),
)


def _round_or_none(value: float | None, precision: int) -> float | None:
    """Round a value if not None."""
    if value is None:
        return None
    return round(value, precision)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DropletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Droplet sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        DropletSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class DropletSensor(CoordinatorEntity[DropletCoordinator], SensorEntity):
    """Representation of a Droplet sensor."""

    _attr_has_entity_name = True
    entity_description: DropletSensorEntityDescription

    def __init__(
        self,
        coordinator: DropletCoordinator,
        description: DropletSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
            manufacturer=coordinator.device_manufacturer,
            model=coordinator.device_model,
            name=coordinator.config_entry.title,
            sw_version=coordinator.device_firmware,
            serial_number=coordinator.device_serial,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def last_reset(self) -> datetime | None:
        """Return the last reset time."""
        return self.entity_description.last_reset_fn(self.coordinator)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.entity_description.is_cost:
            return self.hass.config.currency
        return self.entity_description.native_unit_of_measurement
