#!/usr/bin/env bash
set -Eeuo pipefail

BIN_DIR="$HOME/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

APP_DIR="$DATA_HOME/swaydeck"
DEST="$BIN_DIR/swaydeck"
COMPAT="$BIN_DIR/displayctl"

DEST_TARGET="$(readlink -f -- "$DEST" 2>/dev/null || true)"

if [[ -L "$COMPAT" ]]; then
    COMPAT_LINK="$(readlink -- "$COMPAT" 2>/dev/null || true)"
    COMPAT_TARGET="$(readlink -f -- "$COMPAT" 2>/dev/null || true)"

    if [[ "$COMPAT_LINK" == "$DEST" ]] || \
       [[ -n "$DEST_TARGET" && "$COMPAT_TARGET" == "$DEST_TARGET" ]]; then
        rm -f -- "$COMPAT"
        echo "✓ Removed compatibility link: $COMPAT"
    else
        echo "Existing compatibility path left unchanged:"
        echo "  $COMPAT"
    fi
fi

if [[ -L "$DEST" ]]; then
    TARGET="$(readlink -f -- "$DEST" 2>/dev/null || true)"
    EXPECTED="$(readlink -f -- "$APP_DIR/swaydeck" 2>/dev/null || true)"

    if [[ -n "$EXPECTED" && "$TARGET" == "$EXPECTED" ]]; then
        rm -f -- "$DEST"
        echo "✓ Removed launcher: $DEST"
    else
        echo "Existing launcher symlink left unchanged:"
        echo "  $DEST"
    fi

elif [[ -f "$DEST" ]]; then
    # Compatibility with pre-v0.3 managed launcher installs.
    if grep -q 'SwayDeck' "$DEST" 2>/dev/null; then
        rm -f -- "$DEST"
        echo "✓ Removed legacy SwayDeck launcher: $DEST"
    else
        echo "Existing non-SwayDeck file left unchanged:"
        echo "  $DEST"
    fi
fi

if [[ -d "$APP_DIR" ]]; then
    rm -rf -- "$APP_DIR"
    echo "✓ Removed runtime: $APP_DIR"
fi

echo
echo "Sway and Waybar configuration are intentionally left unchanged."
echo "Saved SwayDeck layouts and backups are also left unchanged."
