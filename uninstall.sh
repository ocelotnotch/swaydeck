#!/usr/bin/env bash
set -Eeuo pipefail

BIN_DIR="$HOME/.local/bin"
DEST="$BIN_DIR/swaydeck"
LEGACY="$BIN_DIR/displayctl"

if [[ -L "$LEGACY" ]]; then
    LEGACY_TARGET="$(readlink -f -- "$LEGACY" 2>/dev/null || true)"

    if [[ "$LEGACY_TARGET" == "$DEST" ]]; then
        rm -f -- "$LEGACY"
        echo "✓ Removed compatibility link: $LEGACY"
    else
        echo "Existing compatibility path left unchanged:"
        echo "  $LEGACY"
    fi
fi

if [[ -e "$DEST" || -L "$DEST" ]]; then
    rm -f -- "$DEST"
    echo "✓ Removed: $DEST"
else
    echo "SwayDeck is not installed at:"
    echo "  $DEST"
fi

echo
echo "Waybar and Sway configuration are intentionally left unchanged."
