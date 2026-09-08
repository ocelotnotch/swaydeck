# SwayDeck

**TUI display manager for Sway.**

![SwayDeck TUI](docs/assets/swaydeck-main.png)

SwayDeck provides a compact terminal interface for common multi-monitor
operations without requiring a full graphical display settings application.

## Features

- PC screen only
- Duplicate display via `wl-mirror`
- Extended desktop
- Second screen only
- Right / Left / Above / Below display topology
- Per-display scaling
- Landscape and portrait orientation
- Save current layout for future Sway sessions
- Multi-monitor aware
- Interactive `fzf` interface
- Terminal-native transparent background
- Tokyo Night-inspired foreground palette
- Optional Waybar integration
- Optional `Super+P` binding

## Requirements

### Core

- Sway (`swaymsg`)
- Python 3.10 or newer
- `fzf`

### Duplicate mode

- `wl-mirror`

### Optional

- `notify-send`
- Ghostty for the example launcher configuration
- Waybar for the example panel integration
- Font Awesome or a Nerd Font for the example Waybar icon

## Fedora

```bash
sudo dnf install python3 fzf wl-mirror
```

## Installation

Clone the repository:

```bash
git clone https://github.com/ocelotnotch/swaydeck.git
cd swaydeck
./install.sh
```

The installer stores the managed Python runtime at:

```text
~/.local/share/swaydeck/
```

and exposes the launcher at:

```text
~/.local/bin/swaydeck
```

No Python site-packages or virtual environment are modified.

When `~/.local/bin/displayctl` is unused, the installer also creates a
compatibility symlink:

```text
~/.local/bin/displayctl -> ~/.local/bin/swaydeck
```

An existing `displayctl` file or unrelated symlink is never overwritten.

Then run:

```bash
swaydeck
```

If `~/.local/bin` is not in your `PATH`, run:

```bash
~/.local/bin/swaydeck
```

The installer does not modify your Sway or Waybar configuration.

## Uninstallation

From the cloned repository:

```bash
./uninstall.sh
```

The uninstaller removes the managed Python runtime, launcher, and its compatibility symlink when applicable.

Existing unrelated `displayctl` files or symlinks are never removed.

Sway and Waybar configuration are intentionally left unchanged.

## Command-line options

Show usage information:

```bash
swaydeck --help
```

Show the current version:

```bash
swaydeck --version
```

Short forms:

```text
-h    help
-V    version
```

These metadata options do not require an active Sway session.

Save the current display layout from the shell:

```bash
swaydeck --save-layout
```

## Persistent layout

SwayDeck can save the current Sway output state so it is restored by Sway on future sessions.

The managed file is:

```text
~/.config/sway/config.d/90-swaydeck-layout.conf
```

Saving captures active/disabled state, mode, refresh rate, scale, orientation, and position. SwayDeck validates the generated config, reloads Sway, and restores the previous managed layout if verification fails.

Duplicate mode is not persisted because it is implemented through `wl-mirror` rather than native Sway output mirroring.

## Keyboard workflow

### Main menu

| Key | Action |
| --- | --- |
| `1` | PC screen only |
| `2` | Duplicate |
| `3` | Extend |
| `4` | Second screen only |
| `5` | Display settings |
| `6` | Save current layout |
| `q` | Exit |

### Extend

Example: place the external display above the primary display.

```text
3 + Enter
a + Enter
3 + Enter
```

Available positions:

| Key | Position |
| --- | --- |
| `1` | Right |
| `2` | Left |
| `3` | Above |
| `4` | Below |

## Display settings

SwayDeck supports per-display:

- scaling from `1.00x` through `3.00x`
- landscape
- portrait
- landscape flipped
- portrait flipped

For a standard two-monitor setup, SwayDeck attempts to preserve the existing
display relationship after scale or orientation changes.

## Waybar

The optional indicator shows a monitor icon and adds a count only when more
than one Sway output is active. Its tooltip lists output names, active/inactive
status, and the current resolution and refresh rate for active outputs.

| Active layout | Indicator |
| --- | --- |
| Laptop only | Icon |
| Laptop and one external display | Icon + 2 |
| Laptop and two external displays | Icon + 3 |
| External display only, laptop output disabled | Icon |

This counts active Sway outputs, not connected cables or unique desktop images.
Duplicate mode still counts both active outputs. Disconnected outputs may disappear
from the tooltip; a connected, disabled output is listed when Sway reports it.

### Install the optional helper

Requires Python 3, `swaymsg`, Waybar, and a running Sway session. It uses only the
Python standard library. From the repository root:

```bash
mkdir -p "$HOME/.local/bin"
install -m 0755 contrib/waybar/swaydeck-waybar "$HOME/.local/bin/swaydeck-waybar"
```

The main installer does not install this optional helper. Back up an existing
helper before replacing it. Back up your Waybar config before editing it, then
merge `custom/swaydeck` from [examples/waybar.jsonc](examples/waybar.jsonc)
into your existing config and add its name to the desired module list. Do not
replace your entire config with the example. Optional styling is in
[examples/waybar.css](examples/waybar.css).

The example click action uses Ghostty; change it to your terminal's launch syntax
if needed. The icon requires Font Awesome or a compatible Nerd Font.

The helper prints an initial snapshot and then listens for Sway output events.
It does not poll periodically. A small listener process stays resident; Waybar
restarts it after three seconds if it exits. Do not add an `interval` alongside
this streaming configuration. Tooltips describe the current state, not history.

Test one snapshot and reload a running Waybar:

```bash
python3 "$HOME/.local/bin/swaydeck-waybar" --once
pkill -USR2 -u "$(id -u)" -x waybar
```

Check the tooltip and click action, then activate/deactivate an external output
to verify that the count changes. Run the fixture tests without Sway using:

```bash
python3 -m unittest discover -s tests
```

To remove the integration, remove the module entry and definition from your
Waybar config, reload Waybar, and delete `~/.local/bin/swaydeck-waybar`.
The main SwayDeck uninstaller leaves this optional helper unchanged.

## Sway binding

Example:

```conf
bindsym $mod+p exec ghostty -e ~/.local/bin/swaydeck
```

## Duplicate mode

Sway does not provide native output mirroring.

SwayDeck therefore uses `wl-mirror` for Duplicate mode. The underlying
outputs remain real Sway outputs while `wl-mirror` presents the primary
display fullscreen on the external output.

## Tested baseline

SwayDeck v0.3.x has been developed and live-tested on:

- Fedora 44
- Sway / Wayland
- internal eDP display
- external HDMI display
- Ghostty
- Waybar

Other distributions may work but are not yet part of the tested baseline.

## Version

Latest release:

```text
v0.3.2
```

Current version on `main`:

```text
0.3.2
```

Previous release:

```text
v0.3.1
```

## License

MIT

## Python architecture

The v0.3 release line uses a modular Python runtime, replacing the original
Bash monolith while preserving its behavior as the migration reference.

Runtime layers:

- `models.py`: typed Sway output state
- `topology.py`: pure topology logic
- `plans.py`: deterministic display-operation plans
- `executor.py`: plan execution
- `sway.py`: Sway IPC boundary
- `workflows.py`: projection workflows
- `mirror.py`: wl-mirror lifecycle
- `settings.py`: scale and orientation workflows
- `layout.py`: persistent layout, backup, verification and rollback
- `ui.py`: fzf TUI
- `cli.py`: command-line entry point

The previous Bash implementation is retained byte-for-byte at
`legacy/swaydeck.bash` as a rollback and behavioral reference for the v0.3
release cycle.

Repository-local commands remain:

    ./swaydeck
    ./swaydeck --help
    ./swaydeck --version
    ./swaydeck --save-layout
