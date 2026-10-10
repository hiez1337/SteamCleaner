import sys
import time
import subprocess
import ctypes
from ctypes import wintypes
import os
import psutil
from PIL import ImageGrab

os.makedirs("screenshots", exist_ok=True)
output_img = sys.argv[1] if len(sys.argv) > 1 else "screenshots/test.png"

# Kill any existing flet or steamcleaner processes first
for p in psutil.process_iter(['name', 'cmdline']):
    try:
        name = (p.info.get('name') or '').lower()
        cmd = ' '.join(p.info.get('cmdline') or []).lower()
        if 'flet' in name or 'steamcleaner' in name or 'steam_cleaner' in cmd:
            p.kill()
    except Exception:
        pass

time.sleep(0.5)

# Start the clean Flet app process
proc = subprocess.Popen([sys.executable, "steam_cleaner_flet.py"])

try:
    user32 = ctypes.windll.user32
    hwnd = 0
    start_time = time.time()
    while time.time() - start_time < 15:
        hwnd = user32.FindWindowW(None, "CS2 & Steam Deep Cache Cleaner")
        if hwnd:
            break
        time.sleep(0.5)

    if not hwnd:
        print("Window not found, capturing full screen")
        im = ImageGrab.grab()
        im.save(output_img)
    else:
        # Give UI 6 seconds to connect to Flutter, scan, and render fully
        time.sleep(6.0)
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        user32.SetForegroundWindow(hwnd)
        user32.SwitchToThisWindow(hwnd, True)
        time.sleep(1.0)

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        print(f"Window bounds: {bbox}")

        if rect.right > rect.left and rect.bottom > rect.top:
            im = ImageGrab.grab(bbox=bbox)
        else:
            im = ImageGrab.grab()
        im.save(output_img)
        print(f"Saved screenshot to {output_img} ({im.size})")
finally:
    # Recursively kill python and any spawned child flet processes
    try:
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception:
        pass
    for p in psutil.process_iter(['name']):
        try:
            if 'flet' in p.info['name'].lower():
                p.kill()
        except Exception:
            pass
