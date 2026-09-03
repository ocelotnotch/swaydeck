#!/usr/bin/env bash
set -Eeuo pipefail

DEST="$HOME/.local/bin/swaydeck"

if [[ -e "$DEST" || -L "$DEST" ]]; then
    rm -f "$DEST"
    echo "✓ Removed: $DEST"
else
    echo "SwayDeck is not installed at:"
    echo "$DEST"
fi

echo
echo "Waybar and Sway configuration are intentionally left unchanged."
