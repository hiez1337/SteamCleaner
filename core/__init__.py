# -*- coding: utf-8 -*-
"""Core logic package for Steam & CS2 Cache Cleaner."""

from core.models import (
    AccountInfo,
    CacheItem,
    ScanStats,
    CleanResult,
    format_size,
)
from core.hardware import (
    detect_steam_path,
    detect_steam_accounts,
    detect_cs2_path,
    build_targets_manifest,
)
from core.process_guard import (
    is_process_running,
    check_processes_async,
    terminate_game_processes_async,
)
from core.cleaner_engine import (
    scan_manifest_async,
    clean_items_async,
)
from core.backup_service import (
    create_backup_async,
    restore_backup_async,
    get_backup_info,
)
from core.platform_utils import (
    write_temp_log,
    copy_to_windows_clipboard,
    LOG_FILE_PATH,
)

__all__ = [
    "AccountInfo",
    "CacheItem",
    "ScanStats",
    "CleanResult",
    "format_size",
    "detect_steam_path",
    "detect_steam_accounts",
    "detect_cs2_path",
    "build_targets_manifest",
    "is_process_running",
    "check_processes_async",
    "terminate_game_processes_async",
    "scan_manifest_async",
    "clean_items_async",
    "create_backup_async",
    "restore_backup_async",
    "get_backup_info",
    "write_temp_log",
    "copy_to_windows_clipboard",
    "LOG_FILE_PATH",
]
