import ctypes
import ctypes.wintypes as wt
import time
import sys

user32 = ctypes.windll.user32

def find_window(title_part):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        n = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, n, 512)
        if title_part.lower() in n.value.lower():
            out.append((hwnd, n.value))
        return True

    user32.EnumWindows(cb, 0)
    return out

def get_rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r

def move_mouse(x, y):
    user32.SetCursorPos(int(x), int(y))

wins = find_window("OurClient")
if not wins:
    print("NO_VENTANA")
    sys.exit(0)

hwnd, title = wins[0]
r = get_rect(hwnd)
cx = (r.left + r.right) // 2
cy = (r.top + r.bottom) // 2
w = r.right - r.left
h = r.bottom - r.top

try:
    user32.SetForegroundWindow(hwnd)
except Exception:
    pass
time.sleep(0.3)

# patron de movimiento realista: circulos alrededor del centro de la
# ventana (el angulo cambia continuamente, power alto, como un jugador)
import math
d0 = 0.42 * min(w, h) // 2
t0 = time.time()
steps = 0
while time.time() - t0 < float(sys.argv[1]) if len(sys.argv) > 1 else 8.0:
    tt = time.time() - t0
    ang = tt * 1.8
    mx = cx + int(d0 * math.cos(ang))
    my = cy + int(d0 * math.sin(ang) * 0.7)
    move_mouse(mx, my)
    steps += 1
    time.sleep(0.03)

print("MOUSE_PATRON_OK steps=%d win=(%d,%d) final=(%d,%d)" % (steps, w, h, mx, my))