# -*- coding: utf-8 -*-
"""
Platform native helpers: Windows clipboard copy, Explorer navigation, and logging to %TEMP%.
"""

import os
import sys
import ctypes
from ctypes import wintypes
import subprocess
import datetime
from core.models import CacheItem

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


def open_path_in_explorer(target_path: str) -> tuple[bool, str, str]:
    """
    Safely open a file or directory in Windows File Explorer.
    - If target_path is a file and exists: selects the file in Explorer.
    - If target_path is a directory and exists: opens the directory in Explorer.
    - If target_path does not exist: opens closest existing parent directory.
    Returns (success, user_message, opened_path).
    """
    if not target_path:
        return False, "Путь не указан", ""

    if sys.platform != "win32":
        return False, "Поддерживается только в среде Windows", ""

    try:
        norm = os.path.normpath(str(target_path).strip('"').strip("'"))

        # 1. Existing file: reveal in explorer with /select
        if os.path.isfile(norm):
            subprocess.Popen(["explorer", f"/select,{norm}"])
            return True, f"Файл выделен в Проводнике: {norm}", norm

        # 2. Existing directory: open directory
        if os.path.isdir(norm):
            os.startfile(norm)
            return True, f"Директория открыта в Проводнике: {norm}", norm

        # 3. Path does not exist yet: find nearest parent directory
        parent = os.path.dirname(norm)
        while parent and not os.path.isdir(parent):
            next_parent = os.path.dirname(parent)
            if next_parent == parent:
                break
            parent = next_parent

        if parent and os.path.isdir(parent):
            os.startfile(parent)
            return True, f"Элемент еще не создан на диске. Открыта папка: {parent}", parent

        return False, f"Путь не найден на диске: {norm}", ""
    except Exception as ex:
        return False, f"Ошибка при открытии Проводника: {ex}", ""


def get_item_paths_info(item: CacheItem) -> tuple[str, str, str]:
    """
    Resolve item display path, full multiline tooltip, and primary target path for explorer.
    Returns (display_path, full_tooltip, primary_path).
    """
    if item.path:
        display = item.path
        tooltip = f"Открыть в Проводнике Windows:\n{item.path}"
        primary = item.path
        return display, tooltip, primary

    if item.paths_list:
        valid_paths = [p for p in item.paths_list if p]
        count = len(valid_paths)
        if count == 0:
            return "Путь не определен", "Путь не определен", ""
        if count == 1:
            display = valid_paths[0]
            tooltip = f"Открыть в Проводнике Windows:\n{valid_paths[0]}"
            primary = valid_paths[0]
            return display, tooltip, primary

        try:
            common = os.path.commonpath([os.path.dirname(p) for p in valid_paths])
        except Exception:
            common = os.path.dirname(valid_paths[0])

        display = f"{common} ({count} файла)"
        lines = [f"• {p}" for p in valid_paths]
        tooltip = f"Открыть расположение в Проводнике ({common}):\n" + "\n".join(lines)
        existing = next((p for p in valid_paths if os.path.exists(p)), None)
        primary = existing if existing else (common or valid_paths[0])
        return display, tooltip, primary

    return "Путь не определен", "Путь не определен", ""


def open_cache_item_in_explorer(item: CacheItem) -> tuple[bool, str, str]:
    """Open CacheItem's target directory or file in Windows Explorer."""
    _, _, primary_path = get_item_paths_info(item)
    if not primary_path:
        return False, f"Не удалось определить путь для {item.label}", ""
    return open_path_in_explorer(primary_path)
