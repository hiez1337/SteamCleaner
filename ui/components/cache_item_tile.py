# -*- coding: utf-8 -*-
"""
Cache item tile component with isolated stats badge rendering.
"""

import flet as ft
from core.models import CacheItem, format_size
from ui.theme import (
    CARD_INNER_BG,
    CARD_HOVER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_WARNING,
    TEXT_SECONDARY,
)


class CacheItemTile(ft.Container):
    """
    Individual cache item row with toggle, description and dynamic size badge.
    Updates badge using isolated control.update() without full-tree re-render.
    """

    def __init__(self, item: CacheItem, on_toggle: callable):
        self.item = item
        self.on_toggle = on_toggle

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
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        desc_container = ft.Container(
            content=ft.Text(item.desc, size=10, color=TEXT_SECONDARY),
            padding=ft.Padding.only(left=28),
        )

        super().__init__(
            content=ft.Column(
                controls=[top_row, desc_container],
                spacing=1,
            ),
            padding=ft.Padding.symmetric(vertical=4, horizontal=8),
            border_radius=6,
            bgcolor=CARD_INNER_BG,
        )

    def _handle_change(self, e):
        if self.on_toggle:
            self.on_toggle(self.item.id, self.checkbox.value)

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
