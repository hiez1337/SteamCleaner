# -*- coding: utf-8 -*-
"""
Non-blocking process monitoring and termination guard for Steam & CS2.
"""

import os
import sys
import asyncio
import subprocess
import psutil

# Windows flag to prevent flashing console windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def is_process_running(name_substr: str) -> bool:
    """Check if any process matching name_substr is currently active."""
    target = name_substr.lower()
    for proc in psutil.process_iter(["name"]):
        try:
            p_name = proc.info.get("name")
            if p_name and target in p_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def check_processes_running() -> tuple[bool, bool]:
    """
    Check running status for steam and cs2 in a single process scan pass.
    Excludes background Windows service 'steamservice.exe'.
    Returns (steam_running, cs2_running).
    """
    steam_on = False
    cs2_on = False
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if "cs2.exe" in name:
                cs2_on = True
            elif name == "steam.exe":
                steam_on = True
            if steam_on and cs2_on:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return steam_on, cs2_on


def terminate_processes(name_substr: str) -> int:
    """
    Terminate all active processes matching name_substr using native silent taskkill
    on Windows and a safe psutil sweep fallback.
    Returns the count of terminated processes.
    """
    target = name_substr.lower()
    terminated_count = 0

    # 1. Native Windows taskkill executed silently without flashing console window
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/T", "/IM", name_substr],
                capture_output=True,
                text=True,
                check=False,
                creationflags=CREATE_NO_WINDOW,
            )
            c = res.stdout.count("SUCCESS") + res.stdout.count("УСПЕХ")
            if c > 0:
                terminated_count += c
            elif res.returncode == 0:
                terminated_count += 1
        except Exception:
            pass

    # 2. psutil sweep for any remaining matching processes (handles permissions safely)
    matched_procs: list[psutil.Process] = []
    for proc in psutil.process_iter(["name"]):
        try:
            p_name = proc.info.get("name")
            if p_name and target in p_name.lower():
                matched_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue

    for p in matched_procs:
        try:
            p.kill()
            terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue

    if matched_procs:
        try:
            psutil.wait_procs(matched_procs, timeout=0.8)
        except Exception:
            pass

    return terminated_count


def terminate_all_game_processes() -> dict[str, int]:
    """
    Terminate CS2, Steam, CEF helpers and overlay.
    Excludes Windows service 'steamservice.exe' to prevent UAC / access denied errors.
    Returns dictionary with counts per process group.
    """
    c_cs2 = terminate_processes("cs2.exe")
    c_steam = terminate_processes("steam.exe")
    c_cef = terminate_processes("steamwebhelper.exe")
    c_overlay = terminate_processes("gameoverlayui.exe")

    total_cef_overlay = c_cef + c_overlay
    return {
        "cs2": c_cs2,
        "steam": c_steam,
        "cef": total_cef_overlay,
        "total": c_cs2 + c_steam + total_cef_overlay,
    }


async def check_processes_async() -> tuple[bool, bool]:
    """Asynchronously check running processes off the main asyncio thread."""
    return await asyncio.to_thread(check_processes_running)


async def terminate_game_processes_async() -> dict[str, int]:
    """Asynchronously terminate game processes without blocking GUI events."""
    return await asyncio.to_thread(terminate_all_game_processes)
