# -*- coding: utf-8 -*-
"""
Config Bar component implementing responsive Steam & CS2 path controls and action buttons.
"""

import os
import asyncio
import flet as ft
from core.models import AccountInfo
from ui.theme import (
    CARD_BG,
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SUCCESS_BG,
    SUCCESS_BORDER,
)


class ConfigBar(ft.Container):
    """
    Configuration toolbar using ft.ResponsiveRow to support dynamic resizing
    without horizontal overflow.
    """

    def __init__(
        self,
        steam_path: str,
        cs2_path: str,
        accounts: list[AccountInfo],
        selected_account_id: str,
        on_browse_click: callable,
        on_account_change: callable,
        on_scan_click: callable,
        on_clean_click: callable,
        on_backup_click: callable,
        on_restore_click: callable,
    ):
        self.steam_path = steam_path
        self.cs2_path = cs2_path
        self.on_browse_click = on_browse_click
        self.on_account_change = on_account_change
        self.on_scan_click = on_scan_click
        self.on_clean_click = on_clean_click
        self.on_backup_click = on_backup_click
        self.on_restore_click = on_restore_click

        # Steam path text & explorer click
        self.steam_path_text = ft.Text(
            steam_path or "Не найден",
            size=12,
            color=ACCENT_PRIMARY,
            weight=ft.FontWeight.W_500,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )

        self.steam_path_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.steam_path_text,
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=13, color=TEXT_SECONDARY),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=CARD_INNER_BG,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            tooltip="Открыть директорию Steam в Проводнике",
            on_click=self._open_steam_in_explorer,
        )

        self.browse_btn = ft.OutlinedButton(
            "Обзор...",
            icon=ft.Icons.FOLDER_OPEN,
            height=34,
            on_click=self._handle_browse,
            style=ft.ButtonStyle(
                color=TEXT_PRIMARY,
                side=ft.BorderSide(1, OUTLINE_VARIANT),
            ),
        )

        self.cs2_status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE if cs2_path else ft.Icons.ERROR_OUTLINE,
            size=13,
            color=ACCENT_SUCCESS if cs2_path else TEXT_SECONDARY,
        )
        self.cs2_status_text = ft.Text(
            "CS2 найдена" if cs2_path else "CS2 не найдена",
            size=11,
            color=ACCENT_SUCCESS if cs2_path else TEXT_SECONDARY,
            weight=ft.FontWeight.W_600,
        )

        self.cs2_status_pill = ft.Container(
            content=ft.Row(
                controls=[self.cs2_status_icon, self.cs2_status_text],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=SUCCESS_BG if cs2_path else CARD_INNER_BG,
            border=ft.Border.all(1, SUCCESS_BORDER if cs2_path else OUTLINE_VARIANT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )

        # Account dropdown
        dropdown_options = [
            ft.DropdownOption(
                key=acc.steamid3,
                text=f"{acc.persona} ({acc.account}) [ID3: {acc.steamid3}]",
            )
            for acc in accounts
        ] if accounts else [ft.DropdownOption(key="", text="Аккаунты не найдены")]

        self.account_dropdown = ft.Dropdown(
            options=dropdown_options,
            value=selected_account_id if accounts else "",
            text_size=12,
            height=38,
            on_select=self._handle_account_change,
        )

        # Action buttons
        self.scan_btn = ft.FilledButton(
            "Сканировать кэш",
            icon=ft.Icons.SEARCH,
            height=38,
            style=ft.ButtonStyle(bgcolor=ACCENT_PRIMARY, color="#11111b"),
            on_click=self._handle_scan,
        )

        self.clean_btn = ft.FilledButton(
            "Очистить кэш",
            icon=ft.Icons.DELETE_SWEEP,
            height=38,
            style=ft.ButtonStyle(bgcolor=ACCENT_SUCCESS, color="#11111b"),
            on_click=self._handle_clean,
        )

        self.backup_btn = ft.OutlinedButton(
            "Бэкап CS2",
            icon=ft.Icons.BACKUP,
            height=38,
            on_click=self._handle_backup,
            style=ft.ButtonStyle(
                color=TEXT_PRIMARY,
                side=ft.BorderSide(1, OUTLINE_VARIANT),
            ),
        )

        self.restore_btn = ft.OutlinedButton(
            "Восстановить",
            icon=ft.Icons.RESTORE,
            height=38,
            on_click=self._handle_restore,
            style=ft.ButtonStyle(
                color=TEXT_PRIMARY,
                side=ft.BorderSide(1, OUTLINE_VARIANT),
            ),
        )

        # Responsive row for paths and accounts
        paths_row = ft.ResponsiveRow(
            columns=12,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 7, "lg": 7},
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, color=TEXT_SECONDARY, size=18),
                            ft.Text("Путь к Steam:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            self.steam_path_container,
                            self.browse_btn,
                            self.cs2_status_pill,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    col={"sm": 12, "md": 5, "lg": 5},
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ACCOUNT_CIRCLE_OUTLINED, color=TEXT_SECONDARY, size=18),
                            ft.Text("Аккаунт:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Container(content=self.account_dropdown, expand=True),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
        )

        actions_row = ft.Row(
            controls=[
                self.scan_btn,
                self.clean_btn,
                ft.Container(width=16),
                self.backup_btn,
                self.restore_btn,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    paths_row,
                    ft.Divider(color=OUTLINE_VARIANT, height=1),
                    actions_row,
                ],
                spacing=10,
            ),
            bgcolor=CARD_BG,
            border_radius=10,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            padding=12,
        )

    def _open_steam_in_explorer(self, e):
        if self.steam_path and os.path.isdir(self.steam_path):
            os.startfile(self.steam_path)

    async def _handle_browse(self, e):
        if self.on_browse_click:
            res = self.on_browse_click(e)
            if asyncio.iscoroutine(res):
                await res

    async def _handle_account_change(self, e):
        if self.on_account_change:
            res = self.on_account_change(self.account_dropdown.value)
            if asyncio.iscoroutine(res):
                await res

    async def _handle_scan(self, e):
        if self.on_scan_click:
            res = self.on_scan_click(e)
            if asyncio.iscoroutine(res):
                await res

    async def _handle_clean(self, e):
        if self.on_clean_click:
            res = self.on_clean_click(e)
            if asyncio.iscoroutine(res):
                await res

    async def _handle_backup(self, e):
        if self.on_backup_click:
            res = self.on_backup_click(e)
            if asyncio.iscoroutine(res):
                await res

    async def _handle_restore(self, e):
        if self.on_restore_click:
            res = self.on_restore_click(e)
            if asyncio.iscoroutine(res):
                await res
    def update_paths(self, steam_path: str, cs2_path: str, accounts: list[AccountInfo], selected_acc_id: str):
        """Update display when path or accounts change."""
        self.steam_path = steam_path
        self.cs2_path = cs2_path
        self.steam_path_text.value = steam_path or "Не найден"

        self.cs2_status_icon.name = ft.Icons.CHECK_CIRCLE if cs2_path else ft.Icons.ERROR_OUTLINE
        self.cs2_status_icon.color = ACCENT_SUCCESS if cs2_path else TEXT_SECONDARY
        self.cs2_status_text.value = "CS2 найдена" if cs2_path else "CS2 не найдена"
        self.cs2_status_text.color = ACCENT_SUCCESS if cs2_path else TEXT_SECONDARY
        self.cs2_status_pill.bgcolor = SUCCESS_BG if cs2_path else CARD_INNER_BG
        self.cs2_status_pill.border = ft.Border.all(1, SUCCESS_BORDER if cs2_path else OUTLINE_VARIANT)

        if accounts:
            self.account_dropdown.options = [
                ft.DropdownOption(
                    key=acc.steamid3,
                    text=f"{acc.persona} ({acc.account}) [ID3: {acc.steamid3}]",
                )
                for acc in accounts
            ]
            self.account_dropdown.value = selected_acc_id
        else:
            self.account_dropdown.options = [ft.DropdownOption(key="", text="Аккаунты не найдены")]
            self.account_dropdown.value = ""

        self.update()

    def set_busy(self, is_busy: bool):
        """Enable or disable interactive action buttons."""
        self.scan_btn.disabled = is_busy
        self.clean_btn.disabled = is_busy
        self.backup_btn.disabled = is_busy
        self.restore_btn.disabled = is_busy
        self.browse_btn.disabled = is_busy
        self.account_dropdown.disabled = is_busy
        self.update()
