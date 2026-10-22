#!/bin/sh
set -eu
app_dir="${XDG_DATA_HOME:-$HOME/.local/share}/mini-resource-monitor"
runtime_dir="${XDG_RUNTIME_DIR:-/tmp}"
exec /usr/bin/flock -n "$runtime_dir/mini-resource-monitor.lock" \
  /usr/bin/env GDK_BACKEND=x11 /usr/bin/python3 "$app_dir/monitor.py"
