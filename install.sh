#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &&
    pwd
)"

LAUNCHER_SOURCE="$SOURCE_DIR/swaydeck"
PACKAGE_SOURCE="$SOURCE_DIR/src/swaydeck"

BIN_DIR="$HOME/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_HOME/swaydeck"

DEST="$BIN_DIR/swaydeck"
COMPAT="$BIN_DIR/displayctl"

for cmd in python3 swaymsg fzf; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required dependency: $cmd" >&2
        exit 1
    fi
done

python3 -c '
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
' || {
    echo "SwayDeck requires Python 3.10 or newer." >&2
    exit 1
}

[[ -f "$LAUNCHER_SOURCE" ]] || {
    echo "Missing launcher: $LAUNCHER_SOURCE" >&2
    exit 1
}

[[ -d "$PACKAGE_SOURCE" ]] || {
    echo "Missing Python package: $PACKAGE_SOURCE" >&2
    exit 1
}

# Validate source before touching an existing installation.
python3 -m py_compile \
    "$LAUNCHER_SOURCE" \
    "$PACKAGE_SOURCE"/*.py

mkdir -p "$BIN_DIR" "$DATA_HOME"

STAGE="$(mktemp -d "$DATA_HOME/.swaydeck-stage.XXXXXX")"
NEW_DEST="${DEST}.new.$$"
OLD_APP="${APP_DIR}.old.$$"
OLD_DEST="${DEST}.old.$$"

APP_BACKED_UP=0
DEST_BACKED_UP=0
APP_INSTALLED=0
DEST_INSTALLED=0

rollback_install() {
    rc=$?

    if (( rc != 0 )); then
        [[ -n "$STAGE" ]] && rm -rf -- "$STAGE" 2>/dev/null || true
        [[ -n "$NEW_DEST" ]] && rm -f -- "$NEW_DEST" 2>/dev/null || true

        if (( DEST_INSTALLED )); then
            rm -f -- "$DEST" 2>/dev/null || true
        fi

        if (( APP_INSTALLED )); then
            rm -rf -- "$APP_DIR" 2>/dev/null || true
        fi

        if (( DEST_BACKED_UP )) && [[ -e "$OLD_DEST" || -L "$OLD_DEST" ]]; then
            mv -- "$OLD_DEST" "$DEST"
        fi

        if (( APP_BACKED_UP )) && [[ -e "$OLD_APP" || -L "$OLD_APP" ]]; then
            mv -- "$OLD_APP" "$APP_DIR"
        fi
    fi

    exit "$rc"
}

trap rollback_install EXIT

mkdir -p "$STAGE/src/swaydeck"

install -m 0755 \
    "$LAUNCHER_SOURCE" \
    "$STAGE/swaydeck"

for file in "$PACKAGE_SOURCE"/*.py; do
    install -m 0644 \
        "$file" \
        "$STAGE/src/swaydeck/"
done

# Critical safety gate: complete staged runtime must work before the
# current APP_DIR or DEST are moved.
PYTHONPATH="$STAGE/src" \
python3 -m swaydeck --version >/dev/null

rm -f -- "$NEW_DEST"
ln -s "$APP_DIR/swaydeck" "$NEW_DEST"

if [[ -e "$APP_DIR" || -L "$APP_DIR" ]]; then
    [[ ! -e "$OLD_APP" && ! -L "$OLD_APP" ]] || {
        echo "Backup path already exists: $OLD_APP" >&2
        exit 1
    }

    mv -- "$APP_DIR" "$OLD_APP"
    APP_BACKED_UP=1
fi

if [[ -e "$DEST" || -L "$DEST" ]]; then
    [[ ! -e "$OLD_DEST" && ! -L "$OLD_DEST" ]] || {
        echo "Backup path already exists: $OLD_DEST" >&2
        exit 1
    }

    mv -- "$DEST" "$OLD_DEST"
    DEST_BACKED_UP=1
fi

mv -- "$STAGE" "$APP_DIR"
STAGE=""
APP_INSTALLED=1

mv -T -- "$NEW_DEST" "$DEST"
NEW_DEST=""
DEST_INSTALLED=1

# Verify final installed path.
"$DEST" --version >/dev/null

# Commit the install transaction.
if (( DEST_BACKED_UP )); then
    rm -rf -- "$OLD_DEST"
    DEST_BACKED_UP=0
fi

if (( APP_BACKED_UP )); then
    rm -rf -- "$OLD_APP"
    APP_BACKED_UP=0
fi

APP_INSTALLED=0
DEST_INSTALLED=0

echo "✓ Installed runtime:"
echo "  $APP_DIR"
echo
echo "✓ Launcher:"
echo "  $DEST -> $APP_DIR/swaydeck"

if [[ -L "$COMPAT" ]]; then
    COMPAT_TARGET="$(readlink -f -- "$COMPAT" 2>/dev/null || true)"
    DEST_TARGET="$(readlink -f -- "$DEST" 2>/dev/null || true)"

    if [[ -n "$DEST_TARGET" && "$COMPAT_TARGET" == "$DEST_TARGET" ]]; then
        echo
        echo "✓ Compatibility link already valid:"
        echo "  $COMPAT -> $DEST"
    else
        echo
        echo "NOTE:"
        echo "Existing compatibility path left unchanged:"
        echo "  $COMPAT"
    fi

elif [[ -e "$COMPAT" ]]; then
    echo
    echo "NOTE:"
    echo "Existing compatibility path left unchanged:"
    echo "  $COMPAT"

else
    ln -s "$DEST" "$COMPAT"

    echo
    echo "✓ Compatibility link created:"
    echo "  $COMPAT -> $DEST"
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

trap - EXIT
