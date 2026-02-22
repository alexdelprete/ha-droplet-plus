"""Event platform for Droplet."""

from __future__ import annotations

from typing import ClassVar

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DropletConfigEntry
from .const import DOMAIN, EVENT_WATER_LEAK_CLEARED, EVENT_WATER_LEAK_DETECTED, KEY_WATER_LEAK
from .coordinator import DropletCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DropletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Droplet event entities."""
    coordinator = entry.runtime_data
    async_add_entities([DropletLeakEvent(coordinator)])


class DropletLeakEvent(CoordinatorEntity[DropletCoordinator], EventEntity):
    """Representation of the Droplet water leak event."""

    _attr_has_entity_name = True
    _attr_translation_key = KEY_WATER_LEAK
    _attr_event_types: ClassVar[list[str]] = [EVENT_WATER_LEAK_DETECTED, EVENT_WATER_LEAK_CLEARED]

    def __init__(self, coordinator: DropletCoordinator) -> None:
        """Initialize the event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_{KEY_WATER_LEAK}_event"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update and fire pending leak events."""
        pending = self.coordinator.pending_leak_event
        if pending:
            event_type, event_data = pending
            self._trigger_event(event_type, event_data)
            self.coordinator.consume_leak_event()
        self.async_write_ha_state()
