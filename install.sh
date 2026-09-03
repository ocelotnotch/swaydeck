#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &&
    pwd
)"

SOURCE="$SOURCE_DIR/swaydeck"
BIN_DIR="$HOME/.local/bin"
DEST="$BIN_DIR/swaydeck"
LEGACY="$BIN_DIR/displayctl"

for cmd in swaymsg jq fzf; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required dependency: $cmd" >&2
        exit 1
    fi
done

[[ -f "$SOURCE" ]] || {
    echo "Missing source: $SOURCE" >&2
    exit 1
}

bash -n "$SOURCE"

mkdir -p "$BIN_DIR"

install -m 0755 "$SOURCE" "$DEST"

echo "✓ Installed: $DEST"

if [[ -L "$LEGACY" ]]; then
    LEGACY_TARGET="$(readlink -f -- "$LEGACY" 2>/dev/null || true)"

    if [[ "$LEGACY_TARGET" == "$DEST" ]]; then
        echo "✓ Compatibility link already valid:"
        echo "  $LEGACY -> $DEST"
    else
        echo
        echo "NOTE:"
        echo "Existing path left unchanged:"
        echo "  $LEGACY"
    fi

elif [[ -e "$LEGACY" ]]; then
    echo
    echo "NOTE:"
    echo "Existing path left unchanged:"
    echo "  $LEGACY"

else
    ln -s "$DEST" "$LEGACY"

    echo "✓ Compatibility link created:"
    echo "  $LEGACY -> $DEST"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo
    echo "NOTE:"
    echo "$BIN_DIR is not currently in PATH."
    echo "Launch directly with:"
    echo "  $DEST"
fi

if ! command -v wl-mirror >/dev/null 2>&1; then
    echo
    echo "NOTE:"
    echo "wl-mirror is not installed."
    echo "Duplicate mode will be unavailable."
fi
