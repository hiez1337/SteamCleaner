# -*- coding: utf-8 -*-
"""
High-performance file scanning and cache purging engine.
"""

import os
import asyncio
from core.models import CacheItem, ScanStats, CleanResult, format_size


def get_dir_stats(path: str) -> tuple[int, int]:
    """Calculate file count and total size in bytes for a directory or single file."""
    if not path or not os.path.exists(path):
        return 0, 0
    if os.path.isfile(path):
        try:
            return 1, os.path.getsize(path)
        except Exception:
            return 1, 0

    count = 0
    total_size = 0
    for root, _, files in os.walk(path):
        count += len(files)
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
            except Exception:
                pass
    return count, total_size


def scan_cache_item(item: CacheItem) -> tuple[int, int]:
    """Calculate file count and bytes for a single CacheItem."""
    c, s = 0, 0
    if item.target_type == "dir_contents":
        if item.path and os.path.exists(item.path):
            c, s = get_dir_stats(item.path)
    elif item.target_type == "file_list":
        for fp in item.paths_list:
            if fp and os.path.isfile(fp):
                cc, ss = get_dir_stats(fp)
                c += cc
                s += ss
    elif item.target_type == "dir_list_contents":
        for dp in item.paths_list:
            if dp and os.path.isdir(dp):
                cc, ss = get_dir_stats(dp)
                c += cc
                s += ss
    item.count = c
    item.bytes = s
    return c, s


def delete_file(file_path: str) -> tuple[int, int, int]:
    """
    Safely delete a single file.
    Returns (deleted_count, deleted_bytes, skipped_locked_count).
    """
    try:
        sz = os.path.getsize(file_path)
        os.chmod(file_path, 0o777)
        os.remove(file_path)
        return 1, sz, 0
    except PermissionError:
        return 0, 0, 1
    except Exception:
        return 0, 0, 0


def purge_dir_contents(dir_path: str) -> tuple[int, int, int]:
    """
    Safely purge all contents of a directory while leaving the root directory intact.
    Returns (deleted_files, deleted_bytes, skipped_locked).
    """
    d_files, d_bytes, s_locked = 0, 0, 0
    try:
        entries = os.listdir(dir_path)
    except Exception:
        return d_files, d_bytes, s_locked

    for entry in entries:
        full_p = os.path.join(dir_path, entry)
        if os.path.isfile(full_p) or os.path.islink(full_p):
            df, db, sl = delete_file(full_p)
            d_files += df
            d_bytes += db
            s_locked += sl
        elif os.path.isdir(full_p):
            for root, _, files in os.walk(full_p, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    df, db, sl = delete_file(fp)
                    d_files += df
                    d_bytes += db
                    s_locked += sl
                try:
                    os.rmdir(root)
                except Exception:
                    pass
    return d_files, d_bytes, s_locked


def clean_cache_item(item: CacheItem) -> tuple[int, int, int]:
    """Execute cleanup for a single CacheItem."""
    d_files, d_bytes, s_locked = 0, 0, 0
    if item.target_type == "dir_contents":
        if item.path and os.path.isdir(item.path):
            d_files, d_bytes, s_locked = purge_dir_contents(item.path)
    elif item.target_type == "file_list":
        for fp in item.paths_list:
            if fp and os.path.isfile(fp):
                df, db, sl = delete_file(fp)
                d_files += df
                d_bytes += db
                s_locked += sl
    elif item.target_type == "dir_list_contents":
        for dp in item.paths_list:
            if dp and os.path.isdir(dp):
                df, db, sl = purge_dir_contents(dp)
                d_files += df
                d_bytes += db
                s_locked += sl
    return d_files, d_bytes, s_locked


async def scan_manifest_async(
    manifest: dict[str, list[CacheItem]],
    on_item_scanned=None,
) -> ScanStats:
    """
    Scan all items in manifest asynchronously with per-item progress callbacks.
    """
    stats = ScanStats()
    flat_items: list[tuple[str, CacheItem]] = []
    for cat_name, items in manifest.items():
        stats.category_sizes[cat_name] = 0
        for item in items:
            flat_items.append((cat_name, item))

    def _scan_worker(item: CacheItem):
        return scan_cache_item(item)

    for cat_name, item in flat_items:
        c, s = await asyncio.to_thread(_scan_worker, item)
        stats.total_files += c
        stats.total_bytes += s
        stats.category_sizes[cat_name] += s

        if item.id in ["nv_dxcache", "nv_glcache", "nv_computecache", "dx_d3dscache", "amd_dxcache"]:
            stats.gpu_bytes += s
        elif item.id == "steam_htmlcache":
            stats.cef_bytes += s
        elif item.id == "acc_gamerecordings":
            stats.rec_bytes += s

        if on_item_scanned:
            on_item_scanned(item, cat_name, stats.category_sizes[cat_name])

    return stats


async def clean_items_async(
    items: list[CacheItem],
    on_progress=None,
    on_log=None,
) -> CleanResult:
    """
    Clean all selected items sequentially off the main thread with progress updates.
    """
    result = CleanResult()
    total_count = len(items)

    for idx, item in enumerate(items):
        if on_log:
            on_log(f"Очистка: {item.label}...", "CLEAN")

        df, db, sl = await asyncio.to_thread(clean_cache_item, item)
        result.deleted_files += df
        result.deleted_bytes += db
        result.skipped_files += sl

        if df > 0 and on_log:
            on_log(f"  ✓ Удалено {df} файлов ({format_size(db)})", "SUCCESS")
        if sl > 0 and on_log:
            on_log(f"  ⚠ Пропущено заблокированных файлов драйвером/системой: {sl}", "WARN")

        # Zero out the item stats since it was purged
        item.count = 0
        item.bytes = 0

        if on_progress:
            progress_ratio = (idx + 1) / total_count
            on_progress(progress_ratio, item, df, db)

    return result
