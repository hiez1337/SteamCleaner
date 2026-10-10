#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS2 & Steam Deep Cache Cleaner (Flet GUI)
Modern, high-performance GUI to analyze and purge bloated Steam, GPU, DirectX, and CS2 caches.
Built with Flet 1.0 (Flutter for Python), fully modularized and responsive.
"""

import os
import asyncio
import flet as ft

from core import (
    AccountInfo,
    CacheItem,
    format_size,
    check_processes_async,
    terminate_game_processes_async,
    scan_manifest_async,
    clean_items_async,
    create_backup_async,
    restore_backup_async,
    get_backup_info,
    copy_to_windows_clipboard,
    open_cache_item_in_explorer,
    open_path_in_explorer,
    LOG_FILE_PATH,
)
from ui import get_app_theme, AppState
from ui.theme import (
    BG_COLOR,
    CARD_BG,
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_DANGER,
    TEXT_PRIMARY,
)
from ui.components import (
    HeaderBar,
    ConfigBar,
    CacheCategoryCard,
    ConsoleView,
    FooterBar,
)
from ui.dialogs import ConfirmCleanDialog, RestoreDialog


def select_directory_dialog(title="Выберите директорию установки Steam") -> str | None:
    """Native directory picker off the main event loop."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path or None


def select_file_dialog(title="Выберите архив резервной копии CS2", initialdir=None) -> str | None:
    """Native file picker off the main event loop."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title=title,
        initialdir=initialdir,
        filetypes=[("ZIP Archives", "*.zip"), ("All Files", "*.*")],
    )
    root.destroy()
    return path or None


async def main(page: ft.Page):
    """Main application lifecycle and layout entry point."""
    page.title = "CS2 & Steam Deep Cache Cleaner"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = get_app_theme()
    page.window.width = 1140
    page.window.height = 840
    page.window.min_width = 960
    page.window.min_height = 680
    page.window.bgcolor = BG_COLOR
    page.bgcolor = BG_COLOR
    page.padding = 16
    await page.window.center()

    state = AppState()

    # Category Cards registry: cat_name -> CacheCategoryCard
    category_cards: dict[str, CacheCategoryCard] = {}

    snack_bar = ft.SnackBar(
        content=ft.Text(""),
        bgcolor=ACCENT_PRIMARY,
        open=False,
    )
    page.overlay.append(snack_bar)

    def show_snack(message: str, is_error: bool = False):
        """Safe SnackBar presentation using dedicated control update."""
        snack_bar.content = ft.Text(message, color="#11111b" if not is_error else TEXT_PRIMARY)
        snack_bar.bgcolor = ACCENT_DANGER if is_error else ACCENT_PRIMARY
        snack_bar.open = True
        snack_bar.update()

    async def handle_copy_log(text: str):
        if text:
            ok = await asyncio.to_thread(copy_to_windows_clipboard, text)
            if ok:
                show_snack("Журнал скопирован в буфер обмена")
            else:
                show_snack(f"Лог сохранен: {LOG_FILE_PATH}")

    # 1. Header Bar
    async def handle_terminate_procs(e):
        console_view.append_log("Завершение процессов CS2, Steam и steamwebhelper...", "WARN")
        try:
            res = await terminate_game_processes_async()
            msg = f"Завершено процессов: {res['total']} (CS2={res['cs2']}, Steam={res['steam']}, CEF={res['cef']})"
            console_view.append_log(msg, "SUCCESS")
            show_snack(f"Завершено {res['total']} процессов Steam / CS2")
        except Exception as ex:
            console_view.append_log(f"Ошибка при завершении процессов: {ex}", "ERROR")
            show_snack(f"Ошибка завершения процессов: {ex}", is_error=True)
        finally:
            steam_on, cs2_on = await check_processes_async()
            header_bar.update_process_status(steam_on, cs2_on)
    header_bar = HeaderBar(on_terminate_click=handle_terminate_procs)

    # 2. Console View
    console_view = ConsoleView(on_copy_click=handle_copy_log)

    # 3. Footer Bar
    footer_bar = FooterBar()

    # 4. Summary badge in targets toolbar
    summary_text = ft.Text("0 ф. (0 B)", size=11, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY)
    summary_badge = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=14, color=ACCENT_PRIMARY),
                summary_text,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=CARD_INNER_BG,
        border=ft.Border.all(1, OUTLINE_VARIANT),
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )

    def update_summary_ui():
        """Targeted update of summary badge only."""
        files, bytes_cnt = state.get_summary()
        summary_text.value = f"Выбрано: {files:,} ф. ({format_size(bytes_cnt)})".replace(",", " ")
        summary_badge.update()

    def handle_item_toggle(item_id: str, is_checked: bool):
        state.toggle_item(item_id, is_checked)
        update_summary_ui()

    def handle_category_toggle(cat_name: str):
        items = state.manifest.get(cat_name, [])
        all_checked = all(it.id in state.selected_item_ids for it in items)
        new_val = not all_checked
        state.toggle_category(cat_name, new_val)
        card = category_cards.get(cat_name)
        if card:
            for it in items:
                tile = card.tiles_by_id.get(it.id)
                if tile:
                    if new_val and not it.safe:
                        continue
                    tile.set_checked(new_val)
        update_summary_ui()

    # Checklist Scrollable Column
    checklist_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    async def handle_open_cache_path(item: CacheItem):
        ok, msg, opened_path = await asyncio.to_thread(open_cache_item_in_explorer, item)
        if ok:
            console_view.append_log(msg, "INFO")
            show_snack(f"Открыто: {opened_path}")
        else:
            console_view.append_log(msg, "WARN")
            show_snack(msg, is_error=True)

    def rebuild_checklist_ui():
        checklist_column.controls.clear()
        category_cards.clear()

        for cat_name, items in state.manifest.items():
            card = CacheCategoryCard(
                category_name=cat_name,
                items=items,
                on_item_toggle=handle_item_toggle,
                on_category_toggle=handle_category_toggle,
                on_open_path=handle_open_cache_path,
            )
            category_cards[cat_name] = card
            checklist_column.controls.append(card)

        checklist_column.controls.append(ft.Container(height=8))
        checklist_column.update()
        update_summary_ui()

    # Toolbar preset buttons
    def on_preset(e):
        state.select_preset_recommended()
        for cat_name, card in category_cards.items():
            for it_id, tile in card.tiles_by_id.items():
                tile.set_checked(tile.item.safe)
        update_summary_ui()
        console_view.append_log("Применен безопасный рекомендуемый пресет.", "INFO")

    def on_select_all(e):
        state.select_all(include_unsafe=False)
        for cat_name, card in category_cards.items():
            for it_id, tile in card.tiles_by_id.items():
                tile.set_checked(tile.item.safe)
        update_summary_ui()

    def on_deselect_all(e):
        state.deselect_all()
        for cat_name, card in category_cards.items():
            for it_id, tile in card.tiles_by_id.items():
                tile.set_checked(False)
        update_summary_ui()

    preset_btn = ft.OutlinedButton(
        "Рекомендуемое",
        icon=ft.Icons.AUTO_AWESOME,
        height=32,
        on_click=on_preset,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY,
            padding=ft.Padding.symmetric(horizontal=10),
            side=ft.BorderSide(1, OUTLINE_VARIANT),
        ),
    )
    select_all_btn = ft.OutlinedButton(
        "Выбрать все",
        icon=ft.Icons.DONE_ALL,
        height=32,
        on_click=on_select_all,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY,
            padding=ft.Padding.symmetric(horizontal=10),
            side=ft.BorderSide(1, OUTLINE_VARIANT),
        ),
    )
    deselect_all_btn = ft.OutlinedButton(
        "Снять все",
        icon=ft.Icons.REMOVE_DONE,
        height=32,
        on_click=on_deselect_all,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY,
            padding=ft.Padding.symmetric(horizontal=10),
            side=ft.BorderSide(1, OUTLINE_VARIANT),
        ),
    )

    targets_toolbar = ft.Row(
        controls=[
            ft.Row(controls=[preset_btn, select_all_btn, deselect_all_btn], spacing=6),
            summary_badge,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Scanning Logic
    async def run_scan():
        if state.is_busy:
            return
        state.is_busy = True
        config_bar.set_busy(True)
        footer_bar.set_progress(None, visible=True)
        footer_bar.set_status("Выполняется глубокий анализ кэша...")
        console_view.append_log("Начало сканирования кэша...", "INFO")

        def on_item_scanned(item: CacheItem, cat_name: str, cat_total_bytes: int):
            card = category_cards.get(cat_name)
            if card:
                tile = card.tiles_by_id.get(item.id)
                if tile:
                    tile.update_stats(item.count, item.bytes)
                card.update_category_size(cat_total_bytes)
            update_summary_ui()

        stats = await scan_manifest_async(state.manifest, on_item_scanned=on_item_scanned)
        state.scan_stats = stats

        console_view.update_quick_stats(stats.gpu_bytes, stats.cef_bytes, stats.rec_bytes)
        footer_bar.set_progress(0, visible=False)
        footer_bar.set_status(f"Анализ завершен. Всего кэша на диске: {format_size(stats.total_bytes)}")
        console_view.append_log(
            f"Анализ завершен: {stats.total_files:,} файлов ({format_size(stats.total_bytes)}).".replace(",", " "),
            "SUCCESS",
        )
        console_view.append_log(f"  • GPU Шейдеры: {format_size(stats.gpu_bytes)}", "INFO")
        console_view.append_log(f"  • CEF Браузер: {format_size(stats.cef_bytes)}", "INFO")
        console_view.append_log(f"  • Видеозаписи Steam: {format_size(stats.rec_bytes)}", "INFO")

        state.is_busy = False
        config_bar.set_busy(False)

    # Cleaning Logic
    async def perform_clean_operation(selected_items: list[CacheItem]):
        steam_on, cs2_on = await check_processes_async()
        if steam_on or cs2_on:
            console_view.append_log("Внимание: Steam или CS2 запущены. Рекомендуется закрыть их перед очисткой.", "WARN")

        # Auto-backup CS2 config if convar reset is checked
        if any(it.id == "cfg_convars_reset" for it in selected_items):
            console_view.append_log("Пункт сброса конфигурации выбран. Создание резервной копии...", "WARN")
            ok, zip_p, err = await create_backup_async(state.steam_path, state.selected_account_id, state.backup_dir)
            if ok:
                console_view.append_log(f"Резервная копия создана: {os.path.basename(zip_p)}", "SUCCESS")
            else:
                console_view.append_log(f"Ошибка автоматического бэкапа: {err}", "ERROR")

        state.is_busy = True
        config_bar.set_busy(True)
        footer_bar.set_progress(0.0, visible=True)
        footer_bar.set_status("Выполняется очистка выбранных кэшей...")
        console_view.append_log("--- СТАРТ ОЧИСТКИ ВЫБРАННЫХ ДИРЕКТОРИЙ ---", "INFO")

        def on_clean_progress(ratio: float, item: CacheItem, df: int, db: int):
            footer_bar.set_progress(ratio)
            footer_bar.set_status(f"Очищено {item.label}: удалено {df} файлов")
            for _, card in category_cards.items():
                tile = card.tiles_by_id.get(item.id)
                if tile:
                    tile.update_stats(0, 0)
            update_summary_ui()

        result = await clean_items_async(
            items=selected_items,
            on_progress=on_clean_progress,
            on_log=lambda msg, lvl: console_view.append_log(msg, lvl),
        )

        console_view.append_log("--- ИТОГ ОЧИСТКИ ---", "INFO")
        console_view.append_log(f"Удалено файлов: {result.deleted_files}", "SUCCESS")
        console_view.append_log(f"Освобождено дискового пространства: {format_size(result.deleted_bytes)}", "SUCCESS")
        if result.skipped_files > 0:
            console_view.append_log(f"Пропущено файлов, заблокированных процессами: {result.skipped_files}", "WARN")

        show_snack(f"Очистка завершена! Освобождено {format_size(result.deleted_bytes)}")
        state.is_busy = False
        config_bar.set_busy(False)
        await run_scan()

    async def handle_clean_click(e):
        if state.is_busy:
            return
        selected = state.get_selected_items()
        if not selected:
            show_snack("Выберите хотя бы один пункт для очистки.", is_error=True)
            return

        def on_confirmed():
            asyncio.create_task(perform_clean_operation(selected))

        dialog = ConfirmCleanDialog(selected_items=selected, on_confirm=on_confirmed)
        page.overlay.append(dialog)
        page.update()

    # Backup & Restore Handlers
    async def handle_backup_click(e):
        if not state.selected_account_id or not state.steam_path:
            show_snack("Аккаунт Steam не выбран.", is_error=True)
            return

        footer_bar.set_status("Создание резервной копии настроек CS2...")
        ok, zip_p, err = await create_backup_async(state.steam_path, state.selected_account_id, state.backup_dir)
        if ok:
            fn = os.path.basename(zip_p)
            console_view.append_log(f"Создана резервная копия CS2: {fn}", "SUCCESS")
            show_snack(f"Резервная копия создана: {fn}")
            footer_bar.set_status(f"Резервная копия сохранена в backups/{fn}")
        else:
            console_view.append_log(f"Ошибка бэкапа: {err}", "ERROR")
            show_snack(f"Ошибка создания бэкапа: {err}", is_error=True)
            footer_bar.set_status("Ошибка создания бэкапа.", is_error=True)

    async def handle_restore_click(e):
        if not state.selected_account_id or not state.steam_path:
            show_snack("Аккаунт Steam не выбран.", is_error=True)
            return

        zip_path = await asyncio.to_thread(select_file_dialog, "Выберите архив резервной копии CS2", state.backup_dir)
        if not zip_path:
            return

        info = get_backup_info(zip_path)
        if not info:
            show_snack("Не удалось прочитать архив бэкапа.", is_error=True)
            return

        async def perform_restore():
            steam_on, cs2_on = await check_processes_async()
            if steam_on or cs2_on:
                console_view.append_log("Внимание: Закройте Steam и CS2 перед восстановлением настроек!", "WARN")
                show_snack("Закройте Steam и CS2 перед восстановлением!", is_error=True)
                return

            ok, err = await restore_backup_async(zip_path, state.steam_path, state.selected_account_id)
            if ok:
                fn = os.path.basename(zip_path)
                console_view.append_log(f"Конфигурация CS2 успешно восстановлена из: {fn}", "SUCCESS")
                show_snack("Конфигурация CS2 успешно восстановлена!")
                await run_scan()
            else:
                console_view.append_log(f"Ошибка восстановления: {err}", "ERROR")
                show_snack(f"Ошибка восстановления: {err}", is_error=True)

        dialog = RestoreDialog(backup_info=info, on_confirm=lambda: asyncio.create_task(perform_restore()))
        page.overlay.append(dialog)
        page.update()

    # Browse & Account Change Handlers
    async def handle_browse_steam(e):
        path = await asyncio.to_thread(select_directory_dialog, "Выберите директорию установки Steam")
        if path and os.path.isdir(path):
            state.set_steam_path(path)
            config_bar.update_paths(
                steam_path=state.steam_path,
                cs2_path=state.cs2_path,
                accounts=state.accounts,
                selected_acc_id=state.selected_account_id,
            )
            rebuild_checklist_ui()
            await run_scan()

    async def handle_account_select(acc_id: str):
        state.set_account_id(acc_id)
        console_view.append_log(f"Выбран профиль SteamID: {acc_id}", "INFO")
        rebuild_checklist_ui()
        await run_scan()

    # Config Bar Component
    config_bar = ConfigBar(
        steam_path=state.steam_path,
        cs2_path=state.cs2_path,
        accounts=state.accounts,
        selected_account_id=state.selected_account_id,
        on_browse_click=handle_browse_steam,
        on_account_change=handle_account_select,
        on_scan_click=lambda e: asyncio.create_task(run_scan()),
        on_clean_click=handle_clean_click,
        on_backup_click=handle_backup_click,
        on_restore_click=handle_restore_click,
    )

    # Assemble Split View (Left: Targets & Toolbar, Right: Console)
    split_row = ft.Row(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        targets_toolbar,
                        ft.Container(
                            content=checklist_column,
                            expand=True,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        ),
                    ],
                    spacing=8,
                    expand=True,
                ),
                expand=3,
            ),
            ft.Container(
                content=console_view,
                expand=2,
            ),
        ],
        expand=True,
        spacing=12,
    )

    page.add(
        ft.Column(
            controls=[
                header_bar,
                config_bar,
                ft.Container(content=split_row, expand=True),
                footer_bar,
            ],
            spacing=8,
            expand=True,
        )
    )

    # Populate initial checklist UI
    rebuild_checklist_ui()
    console_view.append_log("Приложение инициализировано на модульной архитектуре Flet 1.0.", "INFO")

    # Background monitoring loop for Steam & CS2 processes (non-blocking)
    async def process_monitor_loop():
        last_steam = None
        last_cs2 = None
        while True:
            try:
                steam_on, cs2_on = await check_processes_async()
                if steam_on != last_steam or cs2_on != last_cs2:
                    header_bar.update_process_status(steam_on, cs2_on)
                    last_steam = steam_on
                    last_cs2 = cs2_on
            except Exception:
                pass
            await asyncio.sleep(3)

    asyncio.create_task(process_monitor_loop())
    asyncio.create_task(run_scan())


if __name__ == "__main__":
    ft.run(main)
