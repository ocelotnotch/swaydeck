#!/usr/bin/env bash
set -Eeuo pipefail
BIN_DIR="$HOME/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_HOME/swaydeck"
DEST="$BIN_DIR/swaydeck"
COMPAT="$BIN_DIR/displayctl"

if [[ -L "$COMPAT" ]]; then
  TARGET="$(readlink -- "$COMPAT" 2>/dev/null || true)"
  [[ "$TARGET" == "$DEST" ]] && { rm -f "$COMPAT"; echo "✓ Removed compatibility link: $COMPAT"; }
fi
if [[ -L "$DEST" ]]; then
  TARGET="$(readlink -f -- "$DEST" 2>/dev/null || true)"
  EXPECTED="$(readlink -f -- "$APP_DIR/swaydeck" 2>/dev/null || true)"
  [[ -n "$EXPECTED" && "$TARGET" == "$EXPECTED" ]] && { rm -f "$DEST"; echo "✓ Removed launcher: $DEST"; }
elif [[ -f "$DEST" ]] && grep -q 'SwayDeck' "$DEST" 2>/dev/null; then
  rm -f "$DEST"; echo "✓ Removed legacy launcher: $DEST"
fi
[[ -d "$APP_DIR" ]] && { rm -rf "$APP_DIR"; echo "✓ Removed runtime: $APP_DIR"; }
echo 'Sway/Waybar config, saved layouts, and backups were left unchanged.'
