#!/bin/sh
set -eu
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
APP_DIR="$DATA_HOME/mini-resource-monitor"
# Stop only processes whose command line points to this exact installed entry.
/usr/bin/python3 - "$APP_DIR/monitor.py" <<'PY'
import os, signal, sys
expected = os.fsencode(sys.argv[1])
for name in os.listdir('/proc'):
    if not name.isdigit():
        continue
    try:
        args = open(f'/proc/{name}/cmdline', 'rb').read().split(b'\0')
        if expected in args:
            os.kill(int(name), signal.SIGTERM)
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
PY
for file in \
  "$DATA_HOME/applications/mini-resource-monitor.desktop" \
  "$DATA_HOME/applications/mini-resource-monitor-autostart.desktop" \
  "$CONFIG_HOME/autostart/mini-resource-monitor.desktop" \
  "$HOME/.local/bin/mini-resource-monitor"; do
  [ ! -e "$file" ] || rm "$file"
done
[ ! -e "$APP_DIR/monitor.py" ] || rm "$APP_DIR/monitor.py"
[ ! -d "$APP_DIR" ] || rmdir "$APP_DIR"
printf '%s\n' 'Uninstalled Mini Resource Monitor.'
printf '%s\n' 'Configuration and cached system data were not modified.'
