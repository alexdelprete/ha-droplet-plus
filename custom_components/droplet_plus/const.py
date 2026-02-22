"""Constants for the Droplet integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "droplet_plus"
VERSION: Final = "0.1.0-beta.2"
MANUFACTURER: Final = "Hydrific"

# Configuration keys (CONF_HOST, CONF_PORT, CONF_TOKEN from homeassistant.const)
CONF_DEVICE_ID: Final = "device_id"

# Options keys
CONF_WATER_TARIFF: Final = "water_tariff"
CONF_WATER_LEAK_THRESHOLD: Final = "water_leak_threshold"

# Defaults
DEFAULT_WATER_TARIFF: Final = 0.0
DEFAULT_WATER_LEAK_THRESHOLD: Final = 0.0

# Connection
CONNECT_DELAY: Final = 5
FW_VERSION_TIMEOUT: Final = 5

# Storage
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_data"
SAVE_INTERVAL: Final = 300

# Unit conversion
ML_TO_L: Final = 1000.0
L_TO_M3: Final = 1000.0
L_TO_GAL: Final = 3.78541

# Core sensor keys
KEY_WATER_FLOW_RATE: Final = "water_flow_rate"
KEY_WATER_VOLUME_DELTA: Final = "water_volume_delta"
KEY_SERVER_STATUS: Final = "server_status"
KEY_SIGNAL_QUALITY: Final = "signal_quality"

# Period consumption keys
KEY_WATER_CONSUMPTION_HOURLY: Final = "water_consumption_hourly"
KEY_WATER_CONSUMPTION_DAILY: Final = "water_consumption_daily"
KEY_WATER_CONSUMPTION_WEEKLY: Final = "water_consumption_weekly"
KEY_WATER_CONSUMPTION_MONTHLY: Final = "water_consumption_monthly"
KEY_WATER_CONSUMPTION_YEARLY: Final = "water_consumption_yearly"
KEY_WATER_CONSUMPTION_LIFETIME: Final = "water_consumption_lifetime"

# Cost sensor keys
KEY_WATER_COST_DAILY: Final = "water_cost_daily"
KEY_WATER_COST_WEEKLY: Final = "water_cost_weekly"
KEY_WATER_COST_MONTHLY: Final = "water_cost_monthly"
KEY_WATER_COST_YEARLY: Final = "water_cost_yearly"
KEY_WATER_COST_LIFETIME: Final = "water_cost_lifetime"

# Statistics sensor keys
KEY_WATER_AVG_FLOW_1H: Final = "water_avg_flow_1h"
KEY_WATER_PEAK_FLOW_24H: Final = "water_peak_flow_24h"
KEY_WATER_PEAK_FLOW_7D: Final = "water_peak_flow_7d"
KEY_WATER_MIN_FLOW_24H: Final = "water_min_flow_24h"
KEY_WATER_AVG_HOURLY_24H: Final = "water_avg_hourly_24h"
KEY_WATER_PEAK_HOURLY_24H: Final = "water_peak_hourly_24h"
KEY_WATER_PEAK_HOURLY_7D: Final = "water_peak_hourly_7d"
KEY_WATER_AVG_DAILY_7D: Final = "water_avg_daily_7d"
KEY_WATER_AVG_DAILY_30D: Final = "water_avg_daily_30d"
KEY_WATER_PEAK_DAILY_30D: Final = "water_peak_daily_30d"

# Leak detection
KEY_WATER_LEAK: Final = "water_leak"
EVENT_WATER_LEAK_DETECTED: Final = "water_leak_detected"
EVENT_WATER_LEAK_CLEARED: Final = "water_leak_cleared"

# Number entity keys
KEY_WATER_TARIFF: Final = "water_tariff"
KEY_WATER_LEAK_THRESHOLD: Final = "water_leak_threshold"
