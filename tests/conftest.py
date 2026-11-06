"""Fixtures for Droplet tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.droplet_plus.const import (
    CONF_DEVICE_ID,
    CONF_WATER_LEAK_THRESHOLD,
    CONF_WATER_TARIFF,
    DEFAULT_WATER_LEAK_THRESHOLD,
    DEFAULT_WATER_TARIFF,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant

TEST_HOST = "192.168.1.100"
TEST_PORT = 443
TEST_TOKEN = "ABCD1234"  # noqa: S105
TEST_DEVICE_ID = "droplet-test-123"
TEST_MODEL = "Droplet"
TEST_MANUFACTURER = "LIXIL"
TEST_FW_VERSION = "1.2.3"
TEST_SERIAL = "SN123456"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def mock_config_entry_data() -> dict:
    """Return mock config entry data."""
    return {
        CONF_HOST: TEST_HOST,
        CONF_PORT: TEST_PORT,
        CONF_TOKEN: TEST_TOKEN,
        CONF_DEVICE_ID: TEST_DEVICE_ID,
    }


@pytest.fixture
def mock_config_entry_options() -> dict:
    """Return mock config entry options."""
    return {
        CONF_WATER_TARIFF: DEFAULT_WATER_TARIFF,
        CONF_WATER_LEAK_THRESHOLD: DEFAULT_WATER_LEAK_THRESHOLD,
    }


@pytest.fixture
def mock_config_entry(
    mock_config_entry_data: dict,
    mock_config_entry_options: dict,
) -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Droplet ({TEST_HOST})",
        data=mock_config_entry_data,
        options=mock_config_entry_options,
        unique_id=TEST_DEVICE_ID,
        version=1,
    )


@pytest.fixture
def mock_droplet_device() -> MagicMock:
    """Create a mock Droplet device instance."""
    device = MagicMock()
    device.get_flow_rate.return_value = 2.5
    device.get_volume_delta.return_value = 50.0
    device.get_server_status.return_value = "connected"
    device.get_signal_quality.return_value = "strong_signal"
    device.get_availability.return_value = True
    device.version_info_available.return_value = True
    device.get_model.return_value = TEST_MODEL
    device.get_manufacturer.return_value = TEST_MANUFACTURER
    device.get_device_id.return_value = TEST_DEVICE_ID
    device.get_fw_version.return_value = TEST_FW_VERSION
    device.get_sn.return_value = TEST_SERIAL
    device.connected = True
    device.listen_forever = AsyncMock()
    device.stop_listening = AsyncMock()
    device.disconnect = AsyncMock()
    device.connect = AsyncMock(return_value=True)

    # Accumulator mocks — dictionary-backed for realistic behavior
    device._accumulated_volumes = {
        "hourly": 0.0,
        "daily": 0.0,
        "weekly": 0.0,
        "monthly": 0.0,
        "yearly": 0.0,
        "lifetime": 0.0,
    }
    device.get_accumulated_volume = MagicMock(
        side_effect=lambda name: device._accumulated_volumes.get(name, 0.0)
    )
    device.add_accumulator = MagicMock()
    device.reset_accumulator = MagicMock(
        side_effect=lambda name, reset_time: device._accumulated_volumes.__setitem__(name, 0.0)
    )
    device.remove_accumulator = MagicMock()

    return device


@pytest.fixture
def mock_droplet(mock_droplet_device: MagicMock):
    """Patch pydroplet.Droplet constructor to return mock device."""
    with patch(
        "custom_components.droplet_plus.coordinator.Droplet",
        return_value=mock_droplet_device,
    ):
        yield mock_droplet_device


@pytest.fixture
def mock_discovery():
    """Patch pydroplet.DropletDiscovery for config flow tests."""
    with patch("custom_components.droplet_plus.config_flow.DropletDiscovery") as mock_cls:
        instance = mock_cls.return_value
        instance.try_connect = AsyncMock(return_value=True)
        instance.get_device_id = AsyncMock(return_value=TEST_DEVICE_ID)
        instance.close = AsyncMock()
        instance.is_valid.return_value = True
        yield instance


@pytest.fixture
async def mock_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_droplet: MagicMock,
) -> MockConfigEntry:
    """Set up the integration with a mock config entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
