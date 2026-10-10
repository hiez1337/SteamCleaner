# -*- coding: utf-8 -*-
"""
CS2 configuration backup and restore services with ZIP verification.
"""

import os
import zipfile
import datetime
import asyncio
from core.models import format_size


def create_backup(
    steam_path: str,
    account_id: str,
    backup_dir: str,
) -> tuple[bool, str, str]:
    """
    Synchronously create a ZIP archive of the CS2 (AppID 730) userdata folder.
    Returns (success, zip_path_or_filename, error_message).
    """
    if not steam_path or not account_id:
        return False, "", "Аккаунт Steam или путь к Steam не указан."

    cfg_dir = os.path.join(steam_path, "userdata", account_id, "730")
    if not os.path.isdir(cfg_dir):
        return False, "", f"Папка конфигурации CS2 не найдена: {cfg_dir}"

    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"backup_cs2_acc_{account_id}_{ts}.zip"
    zip_path = os.path.join(backup_dir, zip_filename)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(cfg_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, cfg_dir)
                    zf.write(full_p, rel_p)
        return True, zip_path, ""
    except Exception as ex:
        return False, "", str(ex)


def restore_backup(
    zip_path: str,
    steam_path: str,
    account_id: str,
) -> tuple[bool, str]:
    """
    Synchronously extract a backup ZIP archive into userdata/account_id/730.
    Returns (success, error_message).
    """
    if not os.path.isfile(zip_path):
        return False, f"Файл архива не найден: {zip_path}"

    if not steam_path or not account_id:
        return False, "Аккаунт Steam или путь к Steam не указан."

    dest_dir = os.path.join(steam_path, "userdata", account_id, "730")

    try:
        os.makedirs(dest_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Basic validation
            namelist = zf.namelist()
            if not namelist:
                return False, "Архив пуст."
            zf.extractall(dest_dir)
        return True, ""
    except Exception as ex:
        return False, str(ex)


def get_backup_info(zip_path: str) -> dict:
    """Retrieve metadata about a backup ZIP file."""
    if not os.path.isfile(zip_path):
        return {}
    try:
        size = os.path.getsize(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            files_count = len(zf.namelist())
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(zip_path))
        return {
            "filename": os.path.basename(zip_path),
            "path": zip_path,
            "size_str": format_size(size),
            "files_count": files_count,
            "date_str": mtime.strftime("%d.%m.%Y %H:%M:%S"),
        }
    except Exception:
        return {}


async def create_backup_async(
    steam_path: str,
    account_id: str,
    backup_dir: str,
) -> tuple[bool, str, str]:
    """Asynchronous wrapper for creating CS2 backups."""
    return await asyncio.to_thread(create_backup, steam_path, account_id, backup_dir)


async def restore_backup_async(
    zip_path: str,
    steam_path: str,
    account_id: str,
) -> tuple[bool, str]:
    """Asynchronous wrapper for restoring CS2 backups."""
    return await asyncio.to_thread(restore_backup, zip_path, steam_path, account_id)
