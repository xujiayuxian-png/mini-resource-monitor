#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
APP_DIR="$DATA_HOME/mini-resource-monitor"
BIN_DIR="$HOME/.local/bin"
APP_MENU="$DATA_HOME/applications"
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
AUTOSTART="$CONFIG_HOME/autostart"
if ! /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk, Gdk, GdkX11" >/dev/null 2>&1; then
  printf '%s\n' 'Missing GTK 3 Python bindings. On Ubuntu, install: python3-gi gir1.2-gtk-3.0' >&2
  exit 1
fi
command -v /usr/bin/flock >/dev/null || { printf '%s\n' 'Missing flock (util-linux).' >&2; exit 1; }
mkdir -p "$APP_DIR" "$BIN_DIR" "$APP_MENU" "$AUTOSTART"
install -m 0644 "$ROOT/src/monitor.py" "$APP_DIR/monitor.py"
install -m 0755 "$ROOT/scripts/launch.sh" "$BIN_DIR/mini-resource-monitor"
for entry in mini-resource-monitor mini-resource-monitor-autostart; do
  sed "s|@HOME@|$HOME|g" "$ROOT/share/$entry.desktop" > "$APP_MENU/$entry.desktop.tmp"
  install -m 0644 "$APP_MENU/$entry.desktop.tmp" "$APP_MENU/$entry.desktop"
  rm "$APP_MENU/$entry.desktop.tmp"
done
install -m 0644 "$APP_MENU/mini-resource-monitor-autostart.desktop" "$AUTOSTART/mini-resource-monitor.desktop"
if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate "$APP_MENU/mini-resource-monitor.desktop"
  desktop-file-validate "$AUTOSTART/mini-resource-monitor.desktop"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_MENU" >/dev/null 2>&1 || true
fi
printf '%s\n' 'Installed Mini Resource Monitor.' 'Launch it from the Applications menu or run: mini-resource-monitor'
