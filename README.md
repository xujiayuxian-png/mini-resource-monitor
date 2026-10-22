# Mini Resource Monitor

A compact, draggable Linux desktop widget for CPU, memory, GPU and VRAM usage. It is designed for Ubuntu and GNOME, including GNOME Remote Desktop sessions.

迷你资源监控是一个紧凑、可拖动的 Linux 桌面小组件，用于显示 CPU、内存、GPU 和显存占用。面向 Ubuntu 与 GNOME，包括 GNOME 远程桌面会话。

## Features / 功能

- CPU usage and package temperature when a `coretemp` sensor is available.
- System memory usage.
- NVIDIA GPU utilization, temperature, and VRAM usage when `nvidia-smi` is available. GPU fields show an unavailable state otherwise.
- Colored utilization bars, refreshed every two seconds.
- Drag the widget from an empty area. Click **Pin** to keep it above other windows; click again to return it to the normal desktop stacking order.
- Starts near the upper-right corner and can launch automatically after login.
- Reads local kernel counters and the local NVIDIA driver only. It does not send telemetry over the network.

- 显示 CPU 使用率；存在 `coretemp` 温度传感器时同时显示 CPU 温度。
- 显示系统内存使用量。
- 安装 NVIDIA 驱动且 `nvidia-smi` 可用时显示 GPU 使用率、温度和显存；否则显示不可用状态。
- 彩色占用条，每两秒更新一次。
- 按住组件空白处可拖动。点击“置顶”使组件浮在其他窗口上方，再点一次恢复普通桌面层级。
- 默认放在屏幕右上方，可设置为登录桌面后自动启动。
- 数据来自本机内核计数器和 NVIDIA 驱动，不向网络发送遥测数据。

## Requirements / 运行要求

- Ubuntu 24.04 or a compatible Linux desktop with GTK 3 and an X11 display (including XWayland).
- Python 3, PyGObject, GTK 3 introspection data, `flock`, and the X11/Xext client libraries.
- NVIDIA driver and `nvidia-smi` are optional. CPU and memory monitoring work without them.

On Ubuntu, install dependencies with:

```sh
sudo apt install python3-gi gir1.2-gtk-3.0 util-linux libx11-6 libxext6
```

For NVIDIA metrics, install a supported NVIDIA driver that provides `nvidia-smi`.

## Install / 安装

```sh
git clone <repository-url>
cd mini-resource-monitor
./install.sh
```

The installer uses only the current user's home directory and does not require root. Find **Mini Resource Monitor / 迷你资源监控** in the Applications menu, or run:

```sh
mini-resource-monitor
```

The installer adds a per-user autostart entry. Log out and back in, or start it manually after installation. To uninstall:

```sh
./uninstall.sh
```

Uninstall removes this application's files and stops only its own running process. It does not remove system packages or alter other applications.

## Notes / 说明

- The current implementation targets X11/XWayland because it uses XShape for clean rounded corners. Native Wayland support is not implemented.
- Window stacking behavior is managed by the desktop window manager. The Pin button requests an always-above state; unpinned mode returns the widget to normal stacking.
- GPU values are sampled with `nvidia-smi`; this is lightweight polling and does not run a model or GPU benchmark.
- CPU temperature depends on available kernel hwmon sensors. This version looks for `coretemp` (common on Intel systems).

## License

MIT. See [LICENSE](LICENSE).
