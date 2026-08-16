"""Tests for Droplet device triggers."""

from __future__ import annotations

import pytest
import voluptuous as vol

from custom_components.droplet_plus.const import DOMAIN
from custom_components.droplet_plus.device_trigger import (
    TRIGGER_SCHEMA,
    TRIGGER_TYPES,
    async_get_triggers,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import HomeAssistant


async def test_async_get_triggers(hass: HomeAssistant) -> None:
    """Test triggers are returned for both connectivity states."""
    triggers = await async_get_triggers(hass, "test-device-id")

    assert len(triggers) == 2
    assert {trigger[CONF_TYPE] for trigger in triggers} == TRIGGER_TYPES
    for trigger in triggers:
        assert trigger[CONF_DEVICE_ID] == "test-device-id"
        assert trigger[CONF_DOMAIN] == DOMAIN


def test_trigger_schema_valid() -> None:
    """Test the trigger schema accepts a valid trigger config."""
    config = TRIGGER_SCHEMA(
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": "test-device-id",
            "type": "device_offline",
        }
    )
    assert config["type"] == "device_offline"


def test_trigger_schema_invalid_type() -> None:
    """Test the trigger schema rejects an unknown trigger type."""
    with pytest.raises(vol.Invalid):
        TRIGGER_SCHEMA(
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": "test-device-id",
                "type": "device_exploded",
            }
        )
