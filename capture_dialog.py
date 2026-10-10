import sys
import time
import subprocess
import ctypes
from ctypes import wintypes
import os
import psutil
from PIL import ImageGrab

os.makedirs("screenshots", exist_ok=True)
output_img = "screenshots/iter_10_final.png"

# Kill any existing flet processes first
for p in psutil.process_iter(['name']):
    try:
        if 'flet' in p.info['name'].lower():
            p.kill()
    except Exception:
        pass

time.sleep(0.5)

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

    if hwnd:
        time.sleep(6.0)
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        if rect.right > rect.left and rect.bottom > rect.top:
            im = ImageGrab.grab(bbox=bbox)
        else:
            im = ImageGrab.grab()
        im.save(output_img)
        print(f"Saved final screenshot to {output_img} ({im.size})")
finally:
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
