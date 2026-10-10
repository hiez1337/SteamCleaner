# -*- coding: utf-8 -*-
"""
Confirmation modal dialog before performing destructive cache purge.
"""

import flet as ft
from core.models import CacheItem, format_size
from ui.theme import (
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_WARNING,
    ACCENT_DANGER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_BG,
    WARNING_BORDER,
)


class ConfirmCleanDialog(ft.AlertDialog):
    """
    Modal dialog providing an itemized breakdown of data to be purged
    and strong warnings if convar resets are selected.
    """

    def __init__(self, selected_items: list[CacheItem], on_confirm: callable):
        self.on_confirm = on_confirm
        has_config_reset = any(it.id == "cfg_convars_reset" for it in selected_items)
        total_files = sum(it.count for it in selected_items)
        total_bytes = sum(it.bytes for it in selected_items)

        items_col = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"• Файлов к удалению: {total_files:,}".replace(",", " "),
                        weight=ft.FontWeight.BOLD,
                        color=ACCENT_PRIMARY,
                        size=12,
                    ),
                    ft.Text(
                        f"• Дисковое пространство: {format_size(total_bytes)}",
                        weight=ft.FontWeight.BOLD,
                        color=ACCENT_SUCCESS,
                        size=12,
                    ),
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
                    ft.Icon(ft.Icons.WARNING_ROUNDED, color=ACCENT_WARNING, size=24),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "ВНИМАНИЕ: Выбран сброс конфигурации CS2!",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ACCENT_WARNING,
                            ),
                            ft.Text(
                                "Квары, бинды и видеоконфиг будут сброшены. "
                                "Автоматический бэкап будет сохранен в папку backups.",
                                size=11,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=WARNING_BG,
            border=ft.Border.all(1, WARNING_BORDER),
            border_radius=8,
            padding=10,
            visible=has_config_reset,
        )

        content_column = ft.Column(
            controls=[
                ft.Text("Вы собираетесь выполнить глубокую очистку выбранного кэша:", color=TEXT_PRIMARY),
                items_col,
                warning_box,
                ft.Text(
                    "Шейдеры GPU, CEF кэш и буферы видеозаписи будут безвозвратно удалены.",
                    size=11,
                    color=TEXT_SECONDARY,
                ),
            ],
            spacing=8,
            tight=True,
        )

        super().__init__(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ACCENT_WARNING, size=24),
                    ft.Text("Подтверждение очистки", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ],
                spacing=8,
            ),
            content=content_column,
            actions=[
                ft.TextButton("Отмена", on_click=self._handle_cancel),
                ft.FilledButton(
                    "Подтвердить очистку",
                    icon=ft.Icons.DELETE_SWEEP,
                    style=ft.ButtonStyle(bgcolor=ACCENT_DANGER, color="#11111b"),
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
