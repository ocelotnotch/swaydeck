#!/usr/bin/env bash
set -Eeuo pipefail
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$SOURCE_DIR/swaydeck"
PACKAGE="$SOURCE_DIR/src/swaydeck"
BIN_DIR="$HOME/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_HOME/swaydeck"
DEST="$BIN_DIR/swaydeck"
COMPAT="$BIN_DIR/displayctl"

for cmd in python3 swaymsg fzf; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing required dependency: $cmd" >&2; exit 1; }
done
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || {
  echo 'SwayDeck requires Python 3.10 or newer.' >&2; exit 1;
}
[[ -f "$LAUNCHER" && -d "$PACKAGE" ]] || { echo 'Incomplete SwayDeck source tree.' >&2; exit 1; }
python3 -m py_compile "$LAUNCHER" "$PACKAGE"/*.py

mkdir -p "$BIN_DIR" "$DATA_HOME"
STAGE="$(mktemp -d "$DATA_HOME/.swaydeck-stage.XXXXXX")"
OLD_APP=""
OLD_DEST=""
cleanup() {
  rc=$?
  if (( rc != 0 )); then
    rm -rf "$STAGE" 2>/dev/null || true
    rm -rf "$APP_DIR" 2>/dev/null || true
    [[ -n "$OLD_APP" && -e "$OLD_APP" ]] && mv "$OLD_APP" "$APP_DIR"
    rm -f "$DEST" 2>/dev/null || true
    [[ -n "$OLD_DEST" && -e "$OLD_DEST" ]] && mv "$OLD_DEST" "$DEST"
  fi
  exit "$rc"
}
trap cleanup EXIT

mkdir -p "$STAGE/src/swaydeck"
install -m 0755 "$LAUNCHER" "$STAGE/swaydeck"
for f in "$PACKAGE"/*.py; do install -m 0644 "$f" "$STAGE/src/swaydeck/"; done
PYTHONPATH="$STAGE/src" python3 -m swaydeck --version >/dev/null

if [[ -e "$APP_DIR" || -L "$APP_DIR" ]]; then
  OLD_APP="${APP_DIR}.old.$$"; mv "$APP_DIR" "$OLD_APP"
fi
if [[ -e "$DEST" || -L "$DEST" ]]; then
  OLD_DEST="${DEST}.old.$$"; mv "$DEST" "$OLD_DEST"
fi
mv "$STAGE" "$APP_DIR"; STAGE=""
ln -s "$APP_DIR/swaydeck" "$DEST"
"$DEST" --version >/dev/null
rm -rf "$OLD_APP" "$OLD_DEST" 2>/dev/null || true
OLD_APP=""; OLD_DEST=""

echo "✓ Installed runtime: $APP_DIR"
echo "✓ Launcher: $DEST"

if [[ -L "$COMPAT" ]]; then
  : # Existing compatibility symlink remains valid if it targets $DEST.
elif [[ -e "$COMPAT" ]]; then
  echo "NOTE: existing path left unchanged: $COMPAT"
else
  ln -s "$DEST" "$COMPAT"
  echo "✓ Compatibility link: $COMPAT -> $DEST"
fi
command -v wl-mirror >/dev/null 2>&1 || echo 'NOTE: wl-mirror is missing; Duplicate mode is unavailable.'
trap - EXIT
