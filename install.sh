#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &&
    pwd
)"

SOURCE="$SOURCE_DIR/swaydeck"
DEST="$HOME/.local/bin/swaydeck"

for cmd in swaymsg jq fzf; do
    command -v "$cmd" >/dev/null 2>&1 || {
        echo "Missing required dependency: $cmd" >&2
        exit 1
    }
done

[[ -f "$SOURCE" ]] || {
    echo "Missing source: $SOURCE" >&2
    exit 1
}

bash -n "$SOURCE"

mkdir -p "$HOME/.local/bin"

install \
    -m 0755 \
    "$SOURCE" \
    "$DEST"

echo "✓ Installed: $DEST"

if ! command -v wl-mirror >/dev/null 2>&1; then
    echo
    echo "NOTE:"
    echo "wl-mirror is not installed."
    echo "Duplicate mode will be unavailable."
fi
