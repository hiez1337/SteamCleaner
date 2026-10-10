# -*- coding: utf-8 -*-
"""
Cache item tile component with isolated stats badge rendering and Explorer reveal action.
"""

import asyncio
import flet as ft
from core.models import CacheItem, format_size
from core.platform_utils import get_item_paths_info, open_cache_item_in_explorer
from ui.theme import (
    CARD_INNER_BG,
    CARD_HOVER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_WARNING,
    TEXT_SECONDARY,
    TEXT_MUTED,
)


class CacheItemTile(ft.Container):
    """
    Individual cache item row with toggle, description, dynamic size badge,
    and direct navigation to the target directory or file in Windows Explorer.
    """

    def __init__(self, item: CacheItem, on_toggle: callable, on_open_path: callable = None):
        self.item = item
        self.on_toggle = on_toggle
        self.on_open_path = on_open_path

        display_path, full_tooltip, primary_path = get_item_paths_info(item)
        self.display_path = display_path
        self.full_tooltip = full_tooltip
        self.primary_path = primary_path

        self.checkbox = ft.Checkbox(
            label=item.label,
            value=item.safe,
            on_change=self._handle_change,
            label_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_500),
        )

        self.badge_text = ft.Text(
            "Ожидание...",
            size=11,
            color=TEXT_SECONDARY,
        )

        self.badge_box = ft.Container(
            content=self.badge_text,
            bgcolor=CARD_INNER_BG,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        self.open_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=13, color=TEXT_SECONDARY),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            tooltip=full_tooltip,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=7, vertical=3),
            bgcolor=CARD_INNER_BG,
            ink=True,
            on_click=self._handle_open_click,
        )

        warning_chip = ft.Container(
            content=ft.Text("БЭКАП", size=9, weight=ft.FontWeight.BOLD, color=ACCENT_WARNING),
            bgcolor="#2d231a",
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
            visible=not item.safe,
        )

        top_row = ft.Row(
            controls=[
                self.checkbox,
                warning_chip,
                ft.Container(expand=True),
                self.badge_box,
                self.open_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

        desc_container = ft.Container(
            content=ft.Text(item.desc, size=10, color=TEXT_SECONDARY),
            padding=ft.Padding.only(left=28),
        )

        path_text = ft.Text(
            display_path,
            size=9.5,
            color=TEXT_MUTED,
            font_family="Consolas",
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
            expand=True,
        )

        path_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SUBDIRECTORY_ARROW_RIGHT_ROUNDED, size=12, color=TEXT_MUTED),
                    path_text,
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=10, color=TEXT_MUTED),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            tooltip=full_tooltip,
            padding=ft.Padding.only(left=28, top=2, bottom=1),
            ink=True,
            on_click=self._handle_open_click,
        )

        super().__init__(
            content=ft.Column(
                controls=[top_row, desc_container, path_container],
                spacing=1,
            ),
            padding=ft.Padding.symmetric(vertical=4, horizontal=8),
            border_radius=6,
            bgcolor=CARD_INNER_BG,
        )

    def _handle_change(self, e):
        if self.on_toggle:
            self.on_toggle(self.item.id, self.checkbox.value)

    async def _handle_open_click(self, e):
        if self.on_open_path:
            res = self.on_open_path(self.item)
            if asyncio.iscoroutine(res):
                await res
        else:
            open_cache_item_in_explorer(self.item)

    def set_checked(self, value: bool, notify: bool = False):
        """Set checkbox state programmatically."""
        self.checkbox.value = value
        self.checkbox.update()
        if notify and self.on_toggle:
            self.on_toggle(self.item.id, value)

    def update_stats(self, count: int, size_bytes: int):
        """Targeted update of size badge only."""
        self.item.count = count
        self.item.bytes = size_bytes
        if count > 0:
            self.badge_text.value = f"{count:,} ф. · {format_size(size_bytes)}".replace(",", " ")
            self.badge_text.color = ACCENT_PRIMARY
            self.badge_box.bgcolor = CARD_HOVER_BG
        else:
            self.badge_text.value = "0 B"
            self.badge_text.color = TEXT_SECONDARY
            self.badge_box.bgcolor = CARD_INNER_BG
        self.badge_box.update()
