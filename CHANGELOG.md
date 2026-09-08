# Changelog

All notable changes to SwayDeck are documented in this file.

## Unreleased

## v0.3.1 — 2026-09-08

### Fixed

- Updated the installer for the modular Python runtime
- Install both the SwayDeck launcher and the `src/swaydeck` Python package
- Replaced the previous Bash-specific launcher validation
- Removed the obsolete `jq` runtime requirement from the main installer
- Added Python 3.10+ runtime validation
- Updated the uninstaller for the managed Python runtime
- Added installer and uninstaller regression coverage

### Changed

- The managed runtime is now installed under:

  `~/.local/share/swaydeck/`

- The user-facing launcher remains available at:

  `~/.local/bin/swaydeck`

- Updated installation and version documentation for the Python runtime

## v0.3.0 — 2026-09-08

### Added

- Modular Python runtime
- Typed Sway output models
- Pure display topology logic
- Deterministic display-operation planners
- Explicit display operation executor
- Sway IPC command layer
- High-level display workflows
- `wl-mirror` lifecycle management
- Python-based Duplicate workflow
- Display scale workflow
- Display orientation workflow
- Persistent Sway layout serialization
- Layout syntax validation
- Persistent layout backup
- Reload verification and automatic rollback
- Python CLI
- `python -m swaydeck` entry point
- Python-based `fzf` TUI
- Python package metadata through `pyproject.toml`
- Regression and integration test coverage for the migrated runtime

### Changed

- Migrated the primary SwayDeck runtime from the original ~2,000-line Bash
  implementation to a modular Python architecture
- The repository root `swaydeck` executable now launches the Python runtime
- Display behavior is separated into models, topology, planning, execution,
  Sway IPC, workflows, mirroring, settings, persistence, UI, and CLI layers

### Compatibility

- PC screen only
- Duplicate via `wl-mirror`
- Extend
- Second screen only
- Right / Left / Above / Below display arrangement
- Per-display scaling
- Landscape and portrait orientation
- Persistent display layouts

### Migration

The previous Bash implementation is retained byte-for-byte at:

`legacy/swaydeck.bash`

It remains available as a rollback and behavioral reference during the v0.3
release cycle.

## v0.2.0 — 2026-09-04

### Added

- `--help` / `-h` command-line help
- `--version` / `-V` version reporting
- Persistent current-layout saving through the TUI or `--save-layout`

### Changed

- Hardened installation and uninstallation workflow
- Added non-destructive `displayctl` compatibility handling
- Expanded installation, uninstallation, and Waybar documentation

## v0.1.0 — 2026-09-03

First public freeze of SwayDeck.

### Added

- PC screen only mode
- Duplicate mode via `wl-mirror`
- Extend mode
- Second screen only mode
- Right / Left / Above / Below topology
- Multi-monitor positioning support
- Per-display scale controls
- Per-display orientation controls
- Interactive `fzf` TUI
- Tokyo Night-inspired terminal styling
- Waybar integration
- Super+P launcher integration
