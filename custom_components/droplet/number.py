"""Number platform for Droplet."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import EntityCategory, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_system import METRIC_SYSTEM

from . import DropletConfigEntry
from .const import (
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    DEFAULT_WATER_LEAK_THRESHOLD,
    DEFAULT_WATER_TARIFF,
    DOMAIN,
    KEY_WATER_LEAK_THRESHOLD,
    KEY_WATER_TARIFF,
)
from .coordinator import DropletCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class DropletNumberEntityDescription(NumberEntityDescription):
    """Describes a Droplet number entity."""

    option_key: str
    default_value: float
    value_fn: Callable[[DropletCoordinator], float]


def _get_tariff_descriptions(
    hass: HomeAssistant,
) -> tuple[DropletNumberEntityDescription, ...]:
    """Build number entity descriptions with locale-aware tariff unit."""
    if hass.config.units is METRIC_SYSTEM:
        tariff_unit = f"{hass.config.currency}/m\u00b3"
    else:
        tariff_unit = f"{hass.config.currency}/gal"

    return (
        DropletNumberEntityDescription(
            key=KEY_WATER_TARIFF,
            entity_category=EntityCategory.CONFIG,
            native_min_value=0,
            native_max_value=100,
            native_step=0.01,
            mode=NumberMode.BOX,
            native_unit_of_measurement=tariff_unit,
            option_key=CONF_WATER_TARIFF,
            default_value=DEFAULT_WATER_TARIFF,
            value_fn=lambda c: c.water_tariff,
        ),
        DropletNumberEntityDescription(
            key=KEY_WATER_LEAK_THRESHOLD,
            entity_category=EntityCategory.CONFIG,
            native_min_value=0,
            native_max_value=10,
            native_step=0.01,
            mode=NumberMode.BOX,
            native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
            option_key=CONF_WATER_LEAK_THRESHOLD,
            default_value=DEFAULT_WATER_LEAK_THRESHOLD,
            value_fn=lambda c: c.water_leak_threshold,
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DropletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Droplet number entities."""
    coordinator = entry.runtime_data
    descriptions = _get_tariff_descriptions(hass)
    async_add_entities(DropletNumber(coordinator, description) for description in descriptions)


class DropletNumber(CoordinatorEntity[DropletCoordinator], NumberEntity):
    """Representation of a Droplet number entity."""

    _attr_has_entity_name = True
    entity_description: DropletNumberEntityDescription

    def __init__(
        self,
        coordinator: DropletCoordinator,
        description: DropletNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator)

    async def async_set_native_value(self, value: float) -> None:
        """Update the value."""
        self.hass.config_entries.async_update_entry(
            self.coordinator.config_entry,
            options={
                **self.coordinator.config_entry.options,
                self.entity_description.option_key: value,
            },
        )
        self.async_write_ha_state()
