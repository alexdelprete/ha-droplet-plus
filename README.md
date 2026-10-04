# Droplet Plus

<!-- BEGIN SHARED:repo-sync:badges -->
<!-- Synced by repo-sync on 2026-09-04 -->

[![GitHub Release](https://img.shields.io/github/v/release/alexdelprete/ha-droplet-plus?style=for-the-badge)](https://github.com/alexdelprete/ha-droplet-plus/releases)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/alexdelprete)
[![Tests](https://img.shields.io/github/actions/workflow/status/alexdelprete/ha-droplet-plus/test.yml?style=for-the-badge&label=Tests)](https://github.com/alexdelprete/ha-droplet-plus/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/codecov/c/github/alexdelprete/ha-droplet-plus?style=for-the-badge)](https://codecov.io/gh/alexdelprete/ha-droplet-plus)
[![GitHub Downloads](https://img.shields.io/github/downloads/alexdelprete/ha-droplet-plus/total?style=for-the-badge)](https://github.com/alexdelprete/ha-droplet-plus/releases)

<!-- END SHARED:repo-sync:badges -->

A Home Assistant custom integration for the
[Droplet](https://www.dropletwater.com/) water monitor by Hydrific.
Connects locally via Zeroconf discovery and provides real-time water
usage monitoring, consumption tracking, cost estimates, and leak detection.

## Features

- Automatic device discovery via Zeroconf
- Real-time water flow rate and volume monitoring
- Consumption tracking (hourly, daily, weekly, monthly, yearly, lifetime)
- Water cost estimation with configurable tariff
- Flow statistics (averages, peaks, minimums over various periods)
- Leak detection with configurable threshold
- Device triggers for leak events
- Diagnostics support
- Metric and imperial units: volumes and flow rates follow your Home Assistant
  unit system (gallons and gal/min on US customary installs)

## Requirements

- Home Assistant **2026.8.0** or newer
- A Droplet device reachable on your local network

<!-- BEGIN SHARED:repo-sync:installation -->
<!-- Synced by repo-sync on 2026-09-04 -->

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
1. Click on "Integrations"
1. Click the three dots menu in the top right corner
1. Select "Custom repositories"
1. Add `https://github.com/alexdelprete/ha-droplet-plus` as an Integration
1. Click "Download" and install the integration
1. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/alexdelprete/ha-droplet-plus/releases)
1. Extract the `custom_components/droplet_plus` folder
1. Copy it to your Home Assistant `config/custom_components/` directory
1. Restart Home Assistant

<!-- END SHARED:repo-sync:installation -->

## Configuration

1. Go to **Settings** > **Devices & Services**
1. Click **Add Integration**
1. Search for **Droplet Plus**
1. If your device is on the network, it will be discovered automatically via Zeroconf
1. Enter the device host and pairing code when prompted
1. Optionally configure water tariff and leak threshold in the integration options

### Tiered water tariffs

The integration's cost sensors use a single flat tariff, and the monthly totals reset on the 1st of each month. If
your utility charges by usage bands or bills on a different day, build the cost with two Home Assistant helpers
instead. Both are created from the UI under **Settings** > **Devices & Services** > **Helpers** > **Create helper**.

**1. A meter that resets on your billing day.** Choose **Utility Meter** and set:

- **Name**: `Water billing cycle`
- **Input sensor**: the Droplet Plus **Water consumption lifetime** sensor
- **Meter reset cycle**: Monthly
- **Meter reset offset**: the number of days after the 1st that your billing cycle starts, e.g. `11` for a cycle that
  starts on the 12th (maximum 28)

The meter counts in the same unit as the source sensor: gallons on US customary installs, liters on metric ones.

**2. A tiered cost sensor.** Choose **Template** > **Template a sensor** and set:

- **Name**: `Water bill current cycle`
- **Unit of measurement**: your currency, e.g. `USD` or `EUR`
- **Device class**: Monetary
- **State class**: Total
- **State template**:

```jinja
{% set used = states('sensor.water_billing_cycle') | float(0) %}
{% set tiers = [[5000, 0.0045], [10000, 0.005], [20000, 0.0055], [none, 0.007]] %}
{% set ns = namespace(cost=0, prev=0) %}
{% for limit, rate in tiers %}
  {% if used > ns.prev %}
    {% set upper = used if limit is none else [used, limit] | min %}
    {% set ns.cost = ns.cost + (upper - ns.prev) * rate %}
  {% endif %}
  {% if limit is not none %}{% set ns.prev = limit %}{% endif %}
{% endfor %}
{{ ns.cost | round(2) }}
```

Each entry in `tiers` is `[upper limit of the band, price per unit]`, and the last band uses `none` for no upper limit.
Each band is charged at its own rate: with the example above, 12,000 gal costs
5,000 × 0.0045 + 5,000 × 0.005 + 2,000 × 0.0055 = 58.50. If your utility instead charges all the water at the rate of
the highest band reached, the template needs to be adapted.

On metric installs the meter counts liters. To use bands and prices per m³, change the first line to
`{% set used = states('sensor.water_billing_cycle') | float(0) / 1000 %}`.

If you use this sensor, you can leave the integration's own water tariff at `0`; its cost sensors then report zero.

<!-- BEGIN SHARED:repo-sync:contributing -->
<!-- Synced by repo-sync on 2026-09-04 -->

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
1. Create a feature branch (`git checkout -b feature/my-feature`)
1. Make your changes
1. Run linting: `pre-commit run --all-files`
1. Commit your changes (`git commit -m "feat: add my feature"`)
1. Push to your branch (`git push origin feature/my-feature`)
1. Open a Pull Request

Please ensure all CI checks pass before requesting a review.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development environment (devcontainer, tests, live
Home Assistant instance) and the Windows caveats.

<!-- END SHARED:repo-sync:contributing -->

<!-- BEGIN SHARED:repo-sync:license -->
<!-- Synced by repo-sync on 2026-09-04 -->

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<!-- END SHARED:repo-sync:license -->
