"""Tests for Droplet number entities."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.droplet_plus.const import (
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    DOMAIN,
)
from homeassistant.components.number import ATTR_STEP, ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_number_entities_exist(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test both number entities are created."""
    ent_reg = er.async_get(hass)
    numbers = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "number"
    ]
    assert len(numbers) == 2

    keys = {e.translation_key for e in numbers}
    assert "water_tariff" in keys
    assert "water_leak_threshold" in keys


async def test_number_entity_category(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test number entities have CONFIG category."""
    ent_reg = er.async_get(hass)
    numbers = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and e.domain == "number"
    ]
    for number in numbers:
        assert number.entity_category == EntityCategory.CONFIG


async def test_tariff_initial_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test water tariff initial value is 0.0."""
    ent_reg = er.async_get(hass)
    tariff_entries = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and "tariff" in e.entity_id
    ]
    assert len(tariff_entries) == 1
    state = hass.states.get(tariff_entries[0].entity_id)
    assert state is not None
    assert float(state.state) == 0.0


async def test_set_tariff_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test setting water tariff value updates options."""
    ent_reg = er.async_get(hass)
    tariff_entries = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and "tariff" in e.entity_id
    ]
    entity_id = tariff_entries[0].entity_id

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 4.50},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert mock_setup_entry.options[CONF_WATER_TARIFF] == 4.50


async def test_set_sub_cent_tariff_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test water tariff accepts sub-cent values (e.g. $5.50 per 1000 gal)."""
    ent_reg = er.async_get(hass)
    tariff_entries = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and "tariff" in e.entity_id
    ]
    entity_id = tariff_entries[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes[ATTR_STEP] == 0.0001

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 0.0055},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert mock_setup_entry.options[CONF_WATER_TARIFF] == 0.0055


async def test_set_leak_threshold_value(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test setting leak threshold value updates options."""
    ent_reg = er.async_get(hass)
    threshold_entries = [
        e for e in ent_reg.entities.values() if e.platform == DOMAIN and "threshold" in e.entity_id
    ]
    entity_id = threshold_entries[0].entity_id

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 0.05},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert mock_setup_entry.options[CONF_WATER_LEAK_THRESHOLD] == 0.05
