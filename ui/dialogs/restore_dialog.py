# -*- coding: utf-8 -*-
"""
Confirmation modal dialog before restoring CS2 configurations from a backup ZIP.
"""

import flet as ft
from ui.theme import (
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_WARNING,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_BG,
    WARNING_BORDER,
)


class RestoreDialog(ft.AlertDialog):
    """
    Modal dialog confirming restoration of CS2 userdata from a backup archive.
    """

    def __init__(self, backup_info: dict, on_confirm: callable):
        self.on_confirm = on_confirm

        info_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"• Файл: {backup_info.get('filename', '')}", weight=ft.FontWeight.BOLD, size=12, color=ACCENT_PRIMARY),
                    ft.Text(f"• Дата создания: {backup_info.get('date_str', '—')}", size=11, color=TEXT_SECONDARY),
                    ft.Text(f"• Объем: {backup_info.get('size_str', '—')} ({backup_info.get('files_count', 0)} файлов)", size=11, color=TEXT_SECONDARY),
                ],
                spacing=4,
            ),
            bgcolor=CARD_INNER_BG,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=8,
            padding=10,
        )

        warning_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ACCENT_WARNING, size=24),
                    ft.Text(
                        "Текущие файлы конфигурации CS2 выбранного аккаунта будут перезаписаны файлами из архива.",
                        size=11,
                        color=TEXT_SECONDARY,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=WARNING_BG,
            border=ft.Border.all(1, WARNING_BORDER),
            border_radius=8,
            padding=10,
        )

        super().__init__(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.RESTORE, color=ACCENT_PRIMARY, size=24),
                    ft.Text("Восстановление настроек CS2", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    ft.Text("Вы подтверждаете восстановление из выбранной копии?", color=TEXT_PRIMARY),
                    info_box,
                    warning_box,
                ],
                spacing=8,
                tight=True,
            ),
            actions=[
                ft.TextButton("Отмена", on_click=self._handle_cancel),
                ft.FilledButton(
                    "Восстановить",
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(bgcolor=ACCENT_PRIMARY, color="#11111b"),
                    on_click=self._handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            open=True,
        )

    def _handle_cancel(self, e):
        self.open = False
        self.update()

    def _handle_confirm(self, e):
        self.open = False
        self.update()
        if self.on_confirm:
            self.on_confirm()
