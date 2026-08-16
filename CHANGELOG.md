# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-08-16

First stable release of the Droplet Plus integration.

### Changed

- Minimum supported Home Assistant version raised to 2026.3.0 (Python 3.14 baseline)
- pydroplet requirement bumped to `~=2.4.0`

### Fixed

- Flow rate sensors now default to gal/min on imperial (US customary) installs,
  matching the volume sensors shown in gallons (Reported in #12)

### Quality

- Test coverage raised to 100% (113 tests)
- Type checking (ty) added to the lint pipeline

## [0.1.0-beta.1] - 2026-02-22

First beta release of the Droplet Plus integration.

### Added

- Full Droplet integration with pydroplet accumulators
- Automatic device discovery via Zeroconf
- Real-time water flow rate and volume monitoring
- Consumption tracking (hourly, daily, weekly, monthly, yearly, lifetime)
- Water cost estimation with configurable tariff
- Flow statistics (averages, peaks, minimums over various periods)
- Leak detection with configurable threshold
- Device triggers for leak events
- Diagnostics support
- Config flow with manual and Zeroconf setup
- Options flow for tariff and leak threshold configuration

[Unreleased]: https://github.com/alexdelprete/ha-droplet-plus/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/alexdelprete/ha-droplet-plus/compare/v0.1.0-beta.1...v1.0.0
[0.1.0-beta.1]: https://github.com/alexdelprete/ha-droplet-plus/releases/tag/v0.1.0-beta.1
