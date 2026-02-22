"""Binary sensor platform for Droplet."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DropletConfigEntry
from .const import DOMAIN, KEY_WATER_LEAK
from .coordinator import DropletCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DropletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Droplet binary sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities([DropletLeakSensor(coordinator)])


class DropletLeakSensor(CoordinatorEntity[DropletCoordinator], BinarySensorEntity):
    """Representation of the Droplet water leak binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_translation_key = KEY_WATER_LEAK

    def __init__(self, coordinator: DropletCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_{KEY_WATER_LEAK}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available

    @property
    def is_on(self) -> bool:
        """Return True if a water leak is detected."""
        return self.coordinator.water_leak_detected
