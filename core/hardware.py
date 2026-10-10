# -*- coding: utf-8 -*-
"""
Hardware, registry and path detection utilities for Steam, CS2 and GPU drivers.
"""

import os
import re
import winreg
from core.models import AccountInfo, CacheItem


def detect_steam_path() -> str:
    """Detect Steam installation directory from Windows Registry."""
    reg_locations = [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ]
    for hkey, subkey, val_name in reg_locations:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                val, _ = winreg.QueryValueEx(key, val_name)
                norm = os.path.normpath(str(val))
                if os.path.isdir(norm):
                    return norm
        except Exception:
            continue

    default_path = r"C:\Program Files (x86)\Steam"
    if os.path.isdir(default_path):
        return default_path
    return ""


def detect_steam_accounts(steam_path: str) -> list[AccountInfo]:
    """
    Detect all Steam accounts present in the userdata directory.
    Parses loginusers.vdf to resolve persona and account names.
    """
    accounts: list[AccountInfo] = []
    if not steam_path or not os.path.isdir(steam_path):
        return accounts

    userdata_dir = os.path.join(steam_path, "userdata")
    if not os.path.isdir(userdata_dir):
        return accounts

    user_info: dict[str, dict[str, str]] = {}
    login_vdf = os.path.join(steam_path, "config", "loginusers.vdf")
    if os.path.isfile(login_vdf):
        try:
            with open(login_vdf, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            blocks = re.findall(r'"(\d{17})"\s*\{([^}]+)\}', content)
            for sid64, body in blocks:
                try:
                    sid3 = str(int(sid64) - 76561197960265728)
                except ValueError:
                    continue
                pname_match = re.search(r'"PersonaName"\s*"([^"]+)"', body)
                aname_match = re.search(r'"AccountName"\s*"([^"]+)"', body)
                pname = pname_match.group(1) if pname_match else "Unknown"
                aname = aname_match.group(1) if aname_match else "Unknown"
                user_info[sid3] = {"persona": pname, "account": aname}
        except Exception:
            pass

    for entry in os.listdir(userdata_dir):
        full_p = os.path.join(userdata_dir, entry)
        if os.path.isdir(full_p) and entry.isdigit() and int(entry) > 0:
            info = user_info.get(entry, {"persona": "User", "account": entry})
            accounts.append(
                AccountInfo(
                    steamid3=entry,
                    persona=info["persona"],
                    account=info["account"],
                )
            )
    return accounts


def detect_cs2_path(steam_path: str) -> str:
    """Detect Counter-Strike 2 installation directory from libraryfolders.vdf."""
    if not steam_path or not os.path.isdir(steam_path):
        return ""

    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    candidate_libraries = [steam_path]

    if os.path.isfile(vdf_path):
        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            paths = re.findall(r'"path"\s*"([^"]+)"', content)
            for p in paths:
                p_norm = os.path.normpath(p.replace("\\\\", "\\"))
                if os.path.isdir(p_norm) and p_norm not in candidate_libraries:
                    candidate_libraries.append(p_norm)
        except Exception:
            pass

    for lib in candidate_libraries:
        possible_cs2 = os.path.join(lib, "steamapps", "common", "Counter-Strike Global Offensive")
        if os.path.isdir(possible_cs2):
            return possible_cs2

    return ""


def build_targets_manifest(
    steam_path: str,
    cs2_path: str,
    selected_account_id: str,
) -> dict[str, list[CacheItem]]:
    """Build structured manifest of all purgeable caches and config targets."""
    local_app = os.environ.get("LOCALAPPDATA", "")
    app_data = os.environ.get("APPDATA", "")
    temp_dir = os.environ.get("TEMP", "")
    s_path = steam_path or ""
    c_path = cs2_path or ""

    u_dir = (
        os.path.join(s_path, "userdata", selected_account_id)
        if (s_path and selected_account_id)
        else ""
    )
    cs2_u730 = os.path.join(u_dir, "730") if u_dir else ""

    return {
        "GPU & DirectX Кэш Шейдеров": [
            CacheItem(
                id="nv_dxcache",
                label="NVIDIA DXCache (DirectX 11 / 12)",
                desc="Скомпилированные шейдеры NVIDIA (*.nvbx). Устраняет микрофризы при дыме и взрывах.",
                path=os.path.join(local_app, "NVIDIA", "DXCache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="nv_glcache",
                label="NVIDIA GLCache (OpenGL / Vulkan)",
                desc="Шейдерные бинарники Vulkan и OpenGL видеокарт NVIDIA.",
                path=os.path.join(local_app, "NVIDIA", "GLCache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="nv_computecache",
                label="NVIDIA ComputeCache",
                desc="Общий вычислительный кэш GPU Compute pipelines.",
                path=os.path.join(app_data, "NVIDIA", "ComputeCache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="dx_d3dscache",
                label="DirectX D3D Shader Cache",
                desc="Системный конвейерный шейдерный кэш Microsoft Direct3D.",
                path=os.path.join(local_app, "D3DSCache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="amd_dxcache",
                label="AMD DxCache & GLCache",
                desc="Шейдерный кэш DirectX и Vulkan для видеокарт AMD Radeon.",
                path=os.path.join(local_app, "AMD", "DxCache"),
                target_type="dir_contents",
                safe=True,
            ),
        ],
        "Steam Client & Web CEF Браузер": [
            CacheItem(
                id="steam_htmlcache",
                label="Steam CEF Browser Cache (htmlcache)",
                desc="Кэш браузера Chromium (steamwebhelper.exe). Снижает фоновую нагрузку на CPU.",
                path=os.path.join(local_app, "Steam", "htmlcache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="steam_appcache",
                label="Steam Appcache (HTTP & Library)",
                desc="Локальный веб-кэш баннеров и структуры страниц библиотеки Steam.",
                path=os.path.join(s_path, "appcache", "httpcache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="steam_librarycache",
                label="Steam Library Artwork Cache",
                desc="Кэшированные постеры и обложки установленных игр в клиенте Steam.",
                path=os.path.join(s_path, "appcache", "librarycache"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="steam_logs_dumps",
                label="Steam Client Logs & Crash Dumps",
                desc="Накопленные текстовые журналы работы и дампы сбоев клиента Steam.",
                path=os.path.join(s_path, "logs"),
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="steam_shadercache_730",
                label="Steam Shader Pre-Cache (CS2 AppID 730)",
                desc="Устаревшие pre-compiled pipelines Fossilize из папки shadercache/730.",
                path=os.path.join(s_path, "steamapps", "shadercache", "730"),
                target_type="dir_contents",
                safe=True,
            ),
        ],
        "Кэш Аккаунта Steam & Инвентаря": [
            CacheItem(
                id="acc_gamerecordings",
                label="Steam Game Recording (Буфер видеозаписи)",
                desc="Фоновая циклическая видеозапись Steam. Занимает гигабайты диска и снижает FPS!",
                path=os.path.join(u_dir, "gamerecordings") if u_dir else "",
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="acc_inventorymsgcache",
                label="CS2 Inventory Message Cache",
                desc="Локальный кэш скинов и сообщений инвентаря. Ускоряет отклик Panorama UI.",
                path=os.path.join(u_dir, "inventorymsgcache") if u_dir else "",
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="acc_ugcmsgcache",
                label="UGC Workshop Message Cache",
                desc="Кэш объектов мастерской Steam и пользовательских предметов.",
                path=os.path.join(u_dir, "ugcmsgcache") if u_dir else "",
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="acc_socache",
                label="Shared Object Cache (socache.dt)",
                desc="Кэш координатора сети предметов CS2 (local и remote socache.dt).",
                paths_list=[
                    os.path.join(cs2_u730, "local", "socache.dt"),
                    os.path.join(cs2_u730, "remote", "socache.dt"),
                ]
                if cs2_u730
                else [],
                target_type="file_list",
                safe=True,
            ),
            CacheItem(
                id="acc_pet_telemetry",
                label="CS2 Performance Telemetry (pet)",
                desc="Локальные книги телеметрии производительности матчей CS2.",
                paths_list=[
                    os.path.join(cs2_u730, "local", "pet"),
                    os.path.join(cs2_u730, "remote", "pet"),
                ]
                if cs2_u730
                else [],
                target_type="dir_list_contents",
                safe=True,
            ),
        ],
        "Движок CS2 & Внутриигровой Кэш": [
            CacheItem(
                id="cs2_iconcache",
                label="CS2 Dynamic Item Icons (_iconcache)",
                desc="Кэш динамических иконок скинов оружия в game\\csgo\\_iconcache.",
                path=os.path.join(c_path, "game", "csgo", "_iconcache") if c_path else "",
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="cs2_rpt_reports",
                label="CS2 Crash Reports & Diagnostics (rpt)",
                desc="Отчеты об ошибках и дампы падений движка Source 2.",
                path=os.path.join(c_path, "game", "csgo", "rpt") if c_path else "",
                target_type="dir_contents",
                safe=True,
            ),
            CacheItem(
                id="win_temp",
                label="Windows Temp Files (%TEMP%)",
                desc="Временные файлы Windows, вызывающие излишние фоновые дисковые операции I/O.",
                path=temp_dir,
                target_type="dir_contents",
                safe=True,
            ),
        ],
        "Сброс Конфига CS2 (С Автоматическим Бэкапом)": [
            CacheItem(
                id="cfg_convars_reset",
                label="Сброс мусорных кваров (cs2_machine_convars)",
                desc="Сбрасывает устаревшие legacy-квары CS:GO. Бэкап создается автоматически!",
                paths_list=[
                    os.path.join(cs2_u730, "local", "cfg", "cs2_machine_convars.vcfg"),
                    os.path.join(cs2_u730, "local", "cfg", "cs2_user_convars_0_slot0.vcfg"),
                    os.path.join(cs2_u730, "remote", "cs2_user_convars.vcfg"),
                    os.path.join(cs2_u730, "remotecache.vdf"),
                ]
                if cs2_u730
                else [],
                target_type="file_list",
                safe=False,
            )
        ],
    }
