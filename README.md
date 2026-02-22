# Droplet Plus

<!-- BEGIN SHARED:repo-sync:badges -->
<!-- Synced by repo-sync on 2026-02-22 -->

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/alexdelprete/ha-droplet-plus?style=for-the-badge)](https://github.com/alexdelprete/ha-droplet-plus/releases)
[![GitHub Downloads](https://img.shields.io/github/downloads/alexdelprete/ha-droplet-plus/total?style=for-the-badge)](https://github.com/alexdelprete/ha-droplet-plus/releases)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/alexdelprete)
[![Lint](https://img.shields.io/github/actions/workflow/status/alexdelprete/ha-droplet-plus/lint.yml?style=for-the-badge&label=Lint)](https://github.com/alexdelprete/ha-droplet-plus/actions/workflows/lint.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/alexdelprete/ha-droplet-plus/test.yml?style=for-the-badge&label=Tests)](https://github.com/alexdelprete/ha-droplet-plus/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/codecov/c/github/alexdelprete/ha-droplet-plus?style=for-the-badge)](https://codecov.io/gh/alexdelprete/ha-droplet-plus)
[![Validate](https://img.shields.io/github/actions/workflow/status/alexdelprete/ha-droplet-plus/validate.yml?style=for-the-badge&label=Validate)](https://github.com/alexdelprete/ha-droplet-plus/actions/workflows/validate.yml)

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

<!-- BEGIN SHARED:repo-sync:installation -->
<!-- Synced by repo-sync on 2026-02-20 -->

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

<!-- BEGIN SHARED:repo-sync:contributing -->
<!-- Synced by repo-sync on 2026-02-20 -->

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
1. Create a feature branch (`git checkout -b feature/my-feature`)
1. Make your changes
1. Run linting: `uvx pre-commit run --all-files`
1. Commit your changes (`git commit -m "feat: add my feature"`)
1. Push to your branch (`git push origin feature/my-feature`)
1. Open a Pull Request

Please ensure all CI checks pass before requesting a review.

<!-- END SHARED:repo-sync:contributing -->

<!-- BEGIN SHARED:repo-sync:license -->
<!-- Synced by repo-sync on 2026-02-20 -->

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<!-- END SHARED:repo-sync:license -->
