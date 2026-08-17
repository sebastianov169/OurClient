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

def set_foreground(hwnd):
    try:
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

def move_mouse(x, y):
    user32.SetCursorPos(int(x), int(y))

action = sys.argv[1] if len(sys.argv) > 1 else "status"

wins = find_window("OurClient")
if not wins:
    print("NO_VENTANA")
    sys.exit(0)

hwnd, title = wins[0]
r = get_rect(hwnd)
cx = (r.left + r.right) // 2
cy = (r.top + r.bottom) // 2

print("WIN=%s rect=(%d,%d,%d,%d) center=(%d,%d)" % (title, r.left, r.top, r.right, r.bottom, cx, cy))

if action == "right":
    set_foreground(hwnd)
    time.sleep(0.3)
    # mover a la derecha del centro en pasos suaves (genera MOUSEMOTION)
    for i in range(1, 21):
        move_mouse(cx + int(320 * i / 20), cy)
        time.sleep(0.02)
    # mantener 6s
    move_mouse(cx + 320, cy)
    time.sleep(6)
    print("MOUSE_DERECHA_OK pos=(%d,%d)" % (cx + 320, cy))
elif action == "left":
    set_foreground(hwnd)
    time.sleep(0.3)
    for i in range(1, 21):
        move_mouse(cx - int(320 * i / 20), cy)
        time.sleep(0.02)
    move_mouse(cx - 320, cy)
    time.sleep(6)
    print("MOUSE_IZQUIERDA_OK pos=(%d,%d)" % (cx - 320, cy))
elif action == "center":
    set_foreground(hwnd)
    move_mouse(cx, cy)
    print("MOUSE_CENTRO_OK pos=(%d,%d)" % (cx, cy))