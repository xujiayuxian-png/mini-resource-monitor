#!/usr/bin/python3
import gi
import subprocess
import threading
import ctypes as C
import math
from pathlib import Path
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkX11

class Monitor(Gtk.Window):
    def __init__(self):
        super().__init__(title='迷你资源监控')
        self.set_wmclass('MiniResources', 'MiniResources')
        self.set_decorated(False)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_resizable(False)
        self.set_accept_focus(True)
        self.set_focus_on_map(False)
        self.connect('size-allocate', self.round_shape)
        self.connect('realize', lambda *_: GLib.idle_add(self.round_shape))
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.stick()
        self.set_keep_below(False)
        self.set_default_size(242, -1)
        self.set_name('monitor')
        self.last_cpu = None
        self.gpu_busy = False
        css = Gtk.CssProvider()
        css.load_from_data(b'''
#monitor { background: #18212b; color: #e6edf3; border-radius: 9px; }
label { font-family: "Noto Sans CJK SC"; font-size: 12px; }
#title { color: #73c9ef; font-weight: bold; }
#pin { padding: 1px 5px; min-height: 20px; min-width: 22px; color: #9aa8b5; background: transparent; border: none; box-shadow: none; }
#pin:checked { color: #ffffff; background: #217bb5; }
#pin:checked label { color: #ffffff; }
#pin:hover { background: #304659; }
progressbar trough { min-height: 4px; background: #303c49; border: none; }
progressbar progress { min-height: 4px; border: none; background: #73c9ef; }
#ram progress { background: #9ddc9b; }
#gpu progress { background: #f6ba73; }
#vram progress { background: #c4a5e7; }
''')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(12)
        self.input_surface = Gtk.EventBox()
        self.input_surface.set_visible_window(False)
        self.input_surface.set_above_child(True)
        self.input_surface.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.input_surface.connect('button-press-event', self.pointer_press)
        self.input_surface.connect('button-release-event', self.pointer_release)
        self.input_surface.connect('motion-notify-event', self.pointer_motion)
        self.input_surface.add(box)
        self.add(self.input_surface)
        self.pointer_start = None
        header = Gtk.Box(spacing=8)
        title = Gtk.Label(label='资源监控', xalign=0)
        title.set_name('title')
        header.pack_start(title, True, True, 0)
        self.pin = Gtk.ToggleButton()
        self.pin.set_name('pin')
        self.pin.set_label('置顶')
        self.pin.set_tooltip_text('点击置顶；取消后置底')
        self.pin.connect('toggled', self.toggle_pin)
        header.pack_end(self.pin, False, False, 0)
        box.pack_start(header, False, False, 0)
        self.rows = {}
        for key, name in [('cpu','CPU'),('ram','内存'),('gpu','GPU'),('vram','显存')]:
            row = Gtk.Box()
            row.pack_start(Gtk.Label(label=name, xalign=0), False, False, 0)
            value = Gtk.Label(label='—', xalign=1)
            row.pack_end(value, True, True, 0)
            bar = Gtk.ProgressBar()
            bar.set_name(key)
            box.pack_start(row, False, False, 0)
            box.pack_start(bar, False, False, 0)
            self.rows[key] = (value, bar)
        self.connect('destroy', Gtk.main_quit)
        self.show_all()
        screen = self.get_screen()
        monitor = screen.get_monitor_workarea(screen.get_primary_monitor())
        self.move(monitor.x + monitor.width - 266, monitor.y + 40)
        GLib.timeout_add(300, self.lower_window)
        self.tick()
        GLib.timeout_add_seconds(2, self.tick)

    def lower_window(self):
        if self.get_window():
            self.get_window().lower()
        return False

    def round_shape(self, *_):
        window = self.get_window()
        if not window:
            return False
        w, h = self.get_allocated_width(), self.get_allocated_height()
        radius = 9
        class Rect(C.Structure):
            _fields_ = [('x', C.c_short), ('y', C.c_short), ('width', C.c_ushort), ('height', C.c_ushort)]
        rects = (Rect * h)()
        for y in range(h):
            dy = max(radius - y - .5, y + .5 - (h - radius), 0)
            inset = math.ceil(radius - math.sqrt(max(0, radius*radius - dy*dy))) if dy else 0
            rects[y] = Rect(inset, y, max(0, w - 2*inset), 1)
        x = C.CDLL('libX11.so.6')
        ext = C.CDLL('libXext.so.6')
        x.XOpenDisplay.restype = C.c_void_p
        x.XCloseDisplay.argtypes = [C.c_void_p]
        ext.XShapeCombineRectangles.argtypes = [C.c_void_p,C.c_ulong,C.c_int,C.c_int,C.c_int,C.POINTER(Rect),C.c_int,C.c_int,C.c_int]
        d = x.XOpenDisplay(None)
        if d:
            ext.XShapeCombineRectangles(d, window.get_xid(), 0, 0, 0, rects, h, 0, 0)
            x.XCloseDisplay(d)
        return False

    def over_pin(self, event):
        px, py = self.pin.translate_coordinates(self.input_surface, 0, 0)
        return px <= event.x < px + self.pin.get_allocated_width() and py <= event.y < py + self.pin.get_allocated_height()

    def pointer_press(self, widget, event):
        if event.button != 1:
            return False
        self.pointer_start = (event.x_root, event.y_root, *self.get_position(), self.over_pin(event))
        return True

    def pointer_motion(self, widget, event):
        if self.pointer_start and event.state & Gdk.ModifierType.BUTTON1_MASK:
            sx, sy, wx, wy, pin = self.pointer_start
            if not pin:
                self.move(round(wx + event.x_root - sx), round(wy + event.y_root - sy))
        return True

    def pointer_release(self, widget, event):
        start, self.pointer_start = self.pointer_start, None
        if event.button == 1 and start:
            if start[4] and self.over_pin(event):
                self.pin.set_active(not self.pin.get_active())
        return True

    def toggle_pin(self, button):
        pinned = button.get_active()
        button.set_label('已置顶' if pinned else '置顶')
        GLib.idle_add(self.apply_layer, pinned)
        button.set_tooltip_text('已置顶，点击恢复置底' if pinned else '已置底，点击置顶')

    def apply_layer(self, pinned):
        position = self.get_position()
        self.hide()
        self.unrealize()
        self.set_keep_above(pinned)
        self.set_keep_below(False)
        self.show_all()
        self.move(*position)
        if not pinned:
            GLib.timeout_add(120, self.lower_window)
        return False

    def update_row(self, key, text, percent):
        value, bar = self.rows[key]
        value.set_text(text)
        bar.set_fraction(max(0, min(1, percent / 100)))
        return False

    def gpu(self):
        try:
            out = subprocess.check_output(['nvidia-smi','--id=0','--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu','--format=csv,noheader,nounits'], timeout=2, stderr=subprocess.DEVNULL, text=True)
            usage, used, total, temp = map(float, out.strip().split(','))
            GLib.idle_add(self.update_row, 'gpu', f'{usage:.0f}% · {temp:.0f}°C', usage)
            GLib.idle_add(self.update_row, 'vram', f'{used/1024:.1f} / {total/1024:.1f} GiB', used/total*100)
        except Exception:
            GLib.idle_add(self.update_row, 'gpu', '暂不可读', 0)
        finally:
            self.gpu_busy = False

    def tick(self):
        values = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
        total, idle = sum(values), values[3]+values[4]
        usage = 0
        if self.last_cpu:
            dt, di = total-self.last_cpu[0], idle-self.last_cpu[1]
            usage = 100*(dt-di)/dt if dt else 0
        self.last_cpu = (total, idle)
        temp = ''
        for hw in Path('/sys/class/hwmon').glob('hwmon*'):
            try:
                if (hw/'name').read_text().strip() == 'coretemp':
                    temp = f" · {int((hw/'temp1_input').read_text())/1000:.0f}°C"
            except OSError:
                pass
        self.update_row('cpu', f'{usage:.0f}%{temp}', usage)
        mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
        used = mem['MemTotal']-mem['MemAvailable']
        self.update_row('ram', f"{used/1048576:.1f} / {mem['MemTotal']/1048576:.1f} GiB", used/mem['MemTotal']*100)
        if not self.gpu_busy:
            self.gpu_busy = True
            threading.Thread(target=self.gpu, daemon=True).start()
        return True

Monitor()
Gtk.main()
