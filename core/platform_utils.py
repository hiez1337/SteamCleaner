# -*- coding: utf-8 -*-
"""
Platform native helpers: Windows clipboard copy and logging to %TEMP%.
"""

import os
import sys
import ctypes
from ctypes import wintypes
import datetime

LOG_FILE_PATH = os.path.join(os.environ.get("TEMP", os.getcwd()), "steam_cleaner.log")


def write_temp_log(message: str, level: str = "INFO"):
    """Append log line to %TEMP%/steam_cleaner.log with timestamp."""
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{now_str}] [{level}] {message}\n")
    except Exception:
        pass


def copy_to_windows_clipboard(text: str) -> bool:
    """
    Safely copy unicode text to Windows system clipboard using native Win32 API.
    Does not require external dependencies or active event loops.
    """
    if not text:
        return False

    if sys.platform != "win32":
        return False

    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.restype = wintypes.BOOL

        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        if not user32.OpenClipboard(None):
            return False

        try:
            user32.EmptyClipboard()
            data = (text + "\0").encode("utf-16le")
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not h_mem:
                return False

            ptr = kernel32.GlobalLock(h_mem)
            if not ptr:
                return False

            ctypes.memmove(ptr, data, len(data))
            kernel32.GlobalUnlock(h_mem)

            res = user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            return bool(res)
        finally:
            user32.CloseClipboard()
    except Exception:
        return False
