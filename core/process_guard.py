# -*- coding: utf-8 -*-
"""
Non-blocking process monitoring and termination guard for Steam & CS2.
"""

import asyncio
import psutil


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
    Returns (steam_running, cs2_running).
    """
    steam_on = False
    cs2_on = False
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if "cs2.exe" in name:
                cs2_on = True
            elif "steam.exe" in name:
                steam_on = True
            if steam_on and cs2_on:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return steam_on, cs2_on


def terminate_processes(name_substr: str) -> int:
    """
    Terminate all active processes matching name_substr.
    Returns the count of terminated processes.
    """
    target = name_substr.lower()
    terminated_count = 0
    matched_procs: list[psutil.Process] = []

    for proc in psutil.process_iter(["name"]):
        try:
            p_name = proc.info.get("name")
            if p_name and target in p_name.lower():
                matched_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for p in matched_procs:
        try:
            p.terminate()
            terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if matched_procs:
        gone, alive = psutil.wait_procs(matched_procs, timeout=1.5)
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    return terminated_count


def terminate_all_game_processes() -> dict[str, int]:
    """
    Terminate CS2, Steam and CEF helpers.
    Returns dictionary with counts per process group.
    """
    c_cs2 = terminate_processes("cs2.exe")
    c_steam = terminate_processes("steam.exe")
    c_cef = terminate_processes("steamwebhelper.exe")
    c_service = terminate_processes("steamservice.exe")
    return {
        "cs2": c_cs2,
        "steam": c_steam,
        "cef": c_cef + c_service,
        "total": c_cs2 + c_steam + c_cef + c_service,
    }


async def check_processes_async() -> tuple[bool, bool]:
    """Asynchronously check running processes off the main asyncio thread."""
    return await asyncio.to_thread(check_processes_running)


async def terminate_game_processes_async() -> dict[str, int]:
    """Asynchronously terminate game processes without blocking GUI events."""
    return await asyncio.to_thread(terminate_all_game_processes)
