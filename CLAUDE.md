# Claude Code Development Guidelines for Droplet Integration

## Critical Initial Steps

> **MANDATORY: At the START of EVERY session, you MUST read this entire CLAUDE.md file.**

**At every session start, you MUST:**

1. **Read this entire CLAUDE.md file** for project context and mandatory procedures
1. **Review recent git commits**: `git log --oneline -20`
1. **Check current status**: `git status`

## Project Overview

### What is Droplet?

A Home Assistant custom integration for Droplet.

### Integration Type

- **Type**: Hub
- **IoT Class**: Local Polling

### File Structure

```text
custom_components/droplet_plus/
├── __init__.py          # Integration setup
├── config_flow.py       # Config flow
├── const.py             # Constants
├── coordinator.py       # Data coordinator
├── sensor.py            # Sensor entities
├── diagnostics.py       # Diagnostics
├── device_trigger.py    # Device triggers
├── helpers.py           # Helper functions
├── repairs.py           # Repair flows
├── manifest.json        # Integration metadata
├── quality_scale.yaml   # Quality scale tracking
├── icons.json           # Entity icons
└── translations/        # Translations
```

## Code Architecture

### Core Components

<!-- TODO: Document each component's responsibilities specific to this integration -->

1. **`__init__.py`** - Integration lifecycle management
   - `async_setup_entry()` - initialize coordinator and platforms
   - `async_unload_entry()` - clean shutdown and resource cleanup
   - `async_migrate_entry()` - config migration logic

1. **`config_flow.py`** - UI configuration
   - ConfigFlow for initial setup
   - OptionsFlowWithReload for runtime options
   - Reconfigure flow for connection settings

1. **`const.py`** - Constants and sensor definitions

1. **`coordinator.py`** - Data update coordination
   - Manages polling cycles and data refresh
   - Error handling and retry logic

1. **`api.py`** - Device communication layer
   <!-- TODO: Document protocol (REST, MQTT, Modbus, Telnet, etc.) and connection management -->

1. **`sensor.py`** - Sensor entity platform

1. **`helpers.py`** - Shared utilities and logging helpers

## Integration-Specific Features

<!-- TODO: Document protocol details, device constants, special values, sensor definitions, etc. -->

## Key Files to Review

<!-- TODO: Update with integration-specific critical files -->

- `const.py` - constants and sensor definitions
- `helpers.py` - shared utilities and logging helpers
- `api.py` - device communication layer
- `sensor.py` - sensor entities
- `CHANGELOG.md` - release history overview
- `docs/releases/` - detailed release notes

## Project-Specific Release Steps

<!-- TODO: Document any extensions to the shared release workflow -->

This project follows the shared release workflow documented below. Add project-specific
release steps here as needed (e.g., specific linting tools, release notes file usage).

## Project-Specific Do's and Don'ts

<!-- TODO: Add integration-specific guidelines beyond the shared ones -->

In addition to the shared Do's and Don'ts below:

**DO:**

- (Add integration-specific guidelines here)

**NEVER:**

- (Add integration-specific restrictions here)

<!-- BEGIN SHARED:repo-sync -->
<!-- Synced by repo-sync on 2026-02-22 -->

## Context7 for Documentation

Always use Context7 MCP tools automatically (without being asked) when:

- Generating code that uses external libraries
- Providing setup or configuration steps
- Looking up library/API documentation

Use `resolve-library-id` first to get the library ID, then `get-library-docs` to fetch documentation.

## GitHub MCP for Repository Operations

Always use GitHub MCP tools (`mcp__github__*`) for GitHub operations instead of the `gh` CLI:

- **Issues**: `issue_read`, `issue_write`, `list_issues`, `search_issues`, `add_issue_comment`
- **Pull Requests**: `list_pull_requests`, `create_pull_request`, `pull_request_read`, `merge_pull_request`
- **Reviews**: `pull_request_review_write`, `add_comment_to_pending_review`
- **Repositories**: `search_repositories`, `get_file_contents`, `list_branches`, `list_commits`
- **Releases**: `list_releases`, `get_latest_release`, `list_tags`

Benefits over `gh` CLI:

- Direct API access without shell escaping issues
- Structured JSON responses
- Better error handling
- No subprocess overhead

## CI Workflow Status and Logs

> **IMPORTANT**: Always use `gh` CLI for CI workflow status and logs — it's more efficient than GitHub MCP.

The project has 3 CI workflows: **Lint**, **Tests**, and **Validate**.

**List recent workflow runs:**

```bash
gh run list --repo alexdelprete/ha-droplet-plus --limit 5
```

**Get workflow status for a specific run:**

```bash
gh run view <run_id> --repo alexdelprete/ha-droplet-plus
```

**Get test coverage from Tests workflow logs:**

```bash
gh run view <run_id> --repo alexdelprete/ha-droplet-plus --log 2>&1 | grep "TOTAL"
```

**Quick one-liner to get latest Tests run coverage:**

```bash
# Get latest Tests run ID and fetch coverage
gh run list --repo alexdelprete/ha-droplet-plus --limit 5 | grep Tests
# Then use the run ID from the output
gh run view <run_id> --repo alexdelprete/ha-droplet-plus --log 2>&1 | grep "TOTAL"
```

## Coding Standards

### Data Storage Pattern

**DO use `runtime_data`** (modern pattern):

```python
entry.runtime_data = MyData(device_name=name)
```

**DO NOT use `hass.data[DOMAIN]`** (deprecated pattern)

### Logging

Use structured logging:

```python
_LOGGER.debug("Sensor %s subscribed to %s", key, topic)
```

**DO NOT** use f-strings in logger calls (deferred formatting is more efficient)

Use centralized logging helpers from `helpers.py` when available:

- `log_debug(logger, context, message, **kwargs)`
- `log_info(logger, context, message, **kwargs)`
- `log_warning(logger, context, message, **kwargs)`
- `log_error(logger, context, message, **kwargs)`

Always include context parameter (function name). Format: `(function_name) [key=value]: message`

**Never log manually what HA logs automatically:**

- **DataUpdateCoordinator**: Just raise `UpdateFailed` — HA handles logging automatically
- **ConfigEntryNotReady**: HA logs automatically — don't log manually
- This prevents log spam during extended outages

### Error Handling

- Use custom exceptions (not `return False`) for proper entity availability tracking
- Raise exceptions in the API layer and let the coordinator handle retries
- Define integration-specific exceptions (e.g., `ConnectionError`, `DataError`)

### Type Hints

Always use type hints for function signatures.

### Async/Await Conventions

- All coordinator methods are async
- API methods use async/await properly
- Config entry methods follow HA conventions:
  - `add_update_listener()` — sync
  - `async_on_unload()` — sync (despite the name)
  - `async_forward_entry_setups()` — async
  - `async_unload_platforms()` — async
- Never use blocking calls in async context

## Configuration Best Practices

Following HA best practices, configuration is split between `data` (initial config) and `options` (runtime tuning):

### config_entry.data (changed via Reconfigure flow)

Connection and identity parameters: name, host, port, device ID, etc.

### config_entry.options (changed via Options flow)

Runtime tuning parameters: scan_interval, timeout, etc. Use OptionsFlowWithReload for auto-reload.

### Config Flow Patterns

- Use `vol.Clamp()` for numeric inputs with min/max bounds (better UX than validation errors)
- Use `async_update_reload_and_abort()` for reconfigure flows
- Implement config entry migration (`async_migrate_entry()`) when changing config schema versions

## Entity and Device Patterns

### Device Registry

- Device identifier tuple: `(DOMAIN, unique_id)` where `unique_id` is MAC address, serial number, or similar
- Use `DeviceInfo` with manufacturer, model, sw_version, and configuration_url
- Changing host/IP should not affect entity IDs or historical data

### Entity Unique IDs

- Sensor unique_id pattern: `{device_unique_id}_{sensor_key}`
- Use stable identifiers (MAC address, serial number) — not connection parameters (IP, hostname)
- Config entry type alias: `type MyConfigEntry = ConfigEntry[RuntimeData]`

## Dependencies Best Practices

### Dependency Update Checklist

**Before updating any dependency version in `manifest.json`:**

1. Verify the new version exists on PyPI: `https://pypi.org/project/PACKAGE_NAME/`
1. Check release notes for breaking changes
1. Test locally if possible

> **WARNING**: Always verify PyPI availability before committing dependency updates. Upstream maintainers
> sometimes create GitHub releases but forget to publish to PyPI, breaking the integration for users.

## Git Workflow

### Commit Messages

Use conventional commits with Claude attribution:

```text
feat(api): implement new feature

[Description]

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Branch Strategy

- Default branch (`main` or `master`) = next release
- Create tags for releases
- Use pre-release flag for beta versions

## Pre-Commit Configuration

Linting tools and settings are defined in `.pre-commit-config.yaml`:

| Hook        | Tool                           | Purpose                      |
| ----------- | ------------------------------ | ---------------------------- |
| ruff        | `ruff check --no-fix`          | Python linting               |
| ruff-format | `ruff format --check`          | Python formatting            |
| jsonlint    | `uvx --from demjson3 jsonlint` | JSON validation              |
| yamllint    | `uvx yamllint -d "{...}"`      | YAML linting (inline config) |
| pymarkdown  | `pymarkdown scan`              | Markdown linting             |

All hooks use `language: system` (local tools) with `verbose: true` for visibility.

## Pre-Commit Checks (MANDATORY)

> **CRITICAL: ALWAYS run pre-commit checks before ANY git commit.**
> This is a hard rule - no exceptions. Never commit without passing all checks.

```bash
uvx pre-commit run --all-files
```

Or run individual tools:

```bash
# Python formatting and linting
ruff format .
ruff check . --fix

# Markdown linting
pymarkdown scan .
```

All checks must pass before committing. This applies to ALL commits, not just releases.

### Windows Shell Notes

When running shell commands on Windows, stray `nul` files may be created (Windows null device artifact).
Check for and delete them after command execution:

```bash
rm nul  # if it exists
```

## Testing

> **CRITICAL: NEVER run pytest locally. The local environment cannot be set up correctly for
> Home Assistant integration tests. ALWAYS use GitHub Actions CI to run tests.**

To run tests:

1. Commit and push changes to the repository
1. GitHub Actions will automatically run the test workflow
1. Check the workflow results in the Actions tab or use `mcp__github__*` tools

> **CRITICAL: NEVER modify production code to make tests pass. Always fix the tests instead.**
> Production code is the source of truth. If tests fail, the tests are wrong - not the production code.
> The only exception is when production code has an actual bug that tests correctly identified.

## Quality Scale Tracking (MUST DO)

This integration tracks [Home Assistant Quality Scale][qs] rules in `quality_scale.yaml`.

**When implementing new features or fixing bugs:**

1. Check if the change affects any quality scale rules
1. Update `quality_scale.yaml` status accordingly:
   - `done` - Rule is fully implemented
   - `todo` - Rule needs implementation
   - `exempt` with `comment` - Rule doesn't apply (explain why)
1. Aim to complete all Bronze tier rules first, then Silver, Gold, Platinum

[qs]: https://developers.home-assistant.io/docs/core/integration-quality-scale/

## Release Management - CRITICAL

> **STOP: NEVER create git tags or GitHub releases without explicit user command.**
> This is a hard rule. Always stop after commit/push and wait for user instruction.

**Published releases are FROZEN** - Never modify documentation for released versions.

**Master branch = Next Release** - All commits target the next version with version bumped
in manifest.json and const.py.

### Version Bumping Rules

> **IMPORTANT: Do NOT bump version during a session. All changes go into the CURRENT unreleased version.**

- The version in `manifest.json` and `const.py` represents the NEXT release being prepared
- **NEVER bump version until user commands "tag and release"**
- Multiple features/fixes can be added to the same unreleased version
- Only bump to a NEW version number AFTER the current version is released

### Version Locations (Must Be Synchronized)

1. `custom_components/droplet_plus/manifest.json` → `"version": "X.Y.Z"`
1. `custom_components/droplet_plus/const.py` → `VERSION = "X.Y.Z"`

### Complete Release Workflow

> **IMPORTANT: Version Validation**
> The release workflow VALIDATES that tag, manifest.json, and const.py versions all match.
> You MUST update versions BEFORE creating the release, not after.

| Step | Tool           | Action                                                                  |
| ---- | -------------- | ----------------------------------------------------------------------- |
| 1    | Edit           | Update `CHANGELOG.md` with version summary                              |
| 2    | Write          | Create `docs/releases/vX.Y.Z.md` release notes (see format below)      |
| 3    | Edit           | Ensure `manifest.json` and `const.py` have correct version              |
| 4    | Bash           | Run linting: `uvx pre-commit run --all-files`                           |
| 5    | Bash           | `git add . && git commit -m "..."`                                      |
| 6    | Bash           | `git push`                                                              |
| 7    | **STOP**       | Wait for user "tag and release" command                                 |
| 8    | **CI Check**   | Verify ALL CI workflows pass (see CI Verification below)                |
| 9    | **RRR**        | Display Release Readiness Report (see below)                            |
| 10   | Bash           | `git tag -a vX.Y.Z -m "Release vX.Y.Z"`                                |
| 11   | Bash           | `git push --tags`                                                       |
| 12   | gh CLI         | `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file docs/releases/vX.Y.Z.md` |
| 13   | GitHub Actions | Validates versions match, then auto-uploads ZIP asset                   |
| 14   | Edit           | Bump versions in `manifest.json` and `const.py` to next version         |

### CI Verification (MANDATORY)

> **CRITICAL: Before tagging/releasing, ALWAYS verify ALL CI workflows are passing.**
> Use GitHub MCP tools to list workflow runs, then use `gh` CLI to get detailed logs if needed.
> NEVER proceed if any workflow is failing.

**Verification steps:**

1. Use `mcp__GitHub_MCP_Remote__actions_list` to list recent workflow runs:

   ```text
   actions_list(method="list_workflow_runs", owner="alexdelprete", repo="ha-droplet-plus")
   ```

1. Check that ALL workflows show `conclusion: "success"`:
   - Lint workflow
   - Validate workflow
   - Tests workflow

1. If any workflow is failing, use `gh` CLI to get detailed failure logs:

   ```bash
   # View failed run logs (replace <run_id> with actual ID from step 1)
   gh run view <run_id> --log-failed

   # Or view full logs for a specific run
   gh run view <run_id> --log
   ```

1. Fix failing tests/issues, commit, push, and re-verify before proceeding

### Release Notes Format (MANDATORY)

Create a release notes file at `docs/releases/vX.Y.Z.md` using this template.
This file is then used as the body when creating the GitHub release.

```markdown
# Release vX.Y.Z

[![GitHub Downloads](https://img.shields.io/github/downloads/alexdelprete/ha-droplet-plus/vX.Y.Z/total?style=for-the-badge)](https://github.com/alexdelprete/ha-droplet-plus/releases/tag/vX.Y.Z)

**Release Date:** YYYY-MM-DD

**Type:** [Major/Minor/Patch/Beta] release - Brief description.

## What's Changed

### Added

- Feature 1

### Changed

- Change 1

### Fixed

- Fix 1

**Full Changelog**:
[compare/vPREV...vX.Y.Z](https://github.com/alexdelprete/ha-droplet-plus/compare/vPREV...vX.Y.Z)
```

### Release Readiness Report (MANDATORY)

> **When user commands "tag and release", ALWAYS display the Release Readiness Report (RRR) BEFORE proceeding.**

Check CI workflows and display:

```markdown
## Release Readiness Report (RRR)

| Check | Status | Details |
|-------|--------|---------|
| **Lint** | status | date |
| **Tests** | status | date |
| **Validate** | status | date |
| **Test Coverage** | status | Minimum required: 97% |
| **Version** | X.Y.Z | manifest.json + const.py |
| **CHANGELOG.md** | status | Updated |
| **Release notes** | status | docs/releases/vX.Y.Z.md |
| **Working Tree** | status | No uncommitted changes |
```

**Test Coverage Requirement:**

> **CRITICAL: Test coverage MUST be at minimum 97%.**
> If coverage drops below 97%, flag it and do not proceed with release until fixed.

**How to get test coverage:**

```bash
gh run list --repo alexdelprete/ha-droplet-plus --limit 5 | grep Tests
gh run view <run_id> --repo alexdelprete/ha-droplet-plus --log 2>&1 | grep "TOTAL"
```

The coverage percentage is the last column in the TOTAL line.

### Issue References in Release Notes

When a release fixes a specific GitHub issue:

- Reference the issue number in release notes (e.g., "Fixes #42")
- Thank the user who opened the issue by name and GitHub handle
- **NEVER close the issue** — the user will do it manually

### After Publishing a Release

1. Immediately bump versions in `manifest.json` and `const.py` to next version
1. Create new release notes file for next version
1. Mark previous version's documentation as frozen

### Release Documentation Structure

#### Stable/Official Release Notes (e.g., v1.0.0)

- **Scope**: ALL changes since previous stable release
- **Example**: v1.1.0 includes everything since v1.0.0
- **Purpose**: Complete picture for users upgrading from last stable

#### Beta Release Notes (e.g., v1.0.0-beta.1)

- **Scope**: Only incremental changes in this beta
- **Example**: v1.0.0-beta.2 shows only what's new since beta.1
- **Purpose**: Help beta testers focus on what to test

### Documentation Files

- **`CHANGELOG.md`** (root) — quick overview of all releases, Keep a Changelog format
- **`docs/releases/`** — detailed release notes (one file per version)
- **`docs/releases/README.md`** — release directory guide and templates

## Do's and Don'ts

**DO:**

- Run `uvx pre-commit run --all-files` before EVERY commit
- Read CLAUDE.md at session start
- Use `runtime_data` for data storage (not `hass.data[DOMAIN]`)
- Use `@callback` decorator for message handlers
- Log with `%s` formatting (not f-strings)
- Handle missing data gracefully
- Update both manifest.json AND const.py for version bumps
- Get approval before creating tags/releases
- Use custom exceptions for error handling
- Verify PyPI availability before updating dependencies

**NEVER:**

- Commit without running pre-commit checks first
- Modify production code to make tests pass - fix the tests instead
- Use `hass.data[DOMAIN][entry_id]` - use `runtime_data` instead
- Shadow Python builtins (A001)
- Use f-strings in logging (G004)
- Create git tags or GitHub releases without explicit user instruction
- Forget to update VERSION in both manifest.json AND const.py
- Use blocking calls in async context
- Close GitHub issues without explicit user instruction
- Log manually what HA logs automatically (coordinator errors, ConfigEntryNotReady)
- Create documentation files without user request

<!-- END SHARED:repo-sync -->

## Reference Documentation

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
