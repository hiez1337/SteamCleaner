# -*- coding: utf-8 -*-
"""
Cache category card component grouping items with category-wide toggle and stats badge.
"""

import flet as ft
from core.models import CacheItem, format_size
from ui.components.cache_item_tile import CacheItemTile
from ui.theme import (
    CARD_BG,
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    TEXT_SECONDARY,
)


CATEGORY_ICONS = {
    "GPU & DirectX Кэш Шейдеров": ft.Icons.MEMORY,
    "Steam Client & Web CEF Браузер": ft.Icons.LANGUAGE,
    "Кэш Аккаунта Steam & Инвентаря": ft.Icons.ACCOUNT_BALANCE_WALLET,
    "Движок CS2 & Внутриигровой Кэш": ft.Icons.SPORTS_ESPORTS,
    "Сброс Конфига CS2 (С Автоматическим Бэкапом)": ft.Icons.SETTINGS_BACKUP_RESTORE,
}


class CacheCategoryCard(ft.Container):
    """
    Card grouping cache items under a category.
    Allows toggling all category items and displays category aggregate size.
    """

    def __init__(
        self,
        category_name: str,
        items: list[CacheItem],
        on_item_toggle: callable,
        on_category_toggle: callable,
    ):
        self.category_name = category_name
        self.on_category_toggle = on_category_toggle
        self.tiles_by_id: dict[str, CacheItemTile] = {}

        cat_icon = CATEGORY_ICONS.get(category_name, ft.Icons.FOLDER)

        self.cat_badge_text = ft.Text(
            "0 B",
            size=10,
            weight=ft.FontWeight.W_600,
            color=TEXT_SECONDARY,
        )

        self.cat_badge_container = ft.Container(
            content=self.cat_badge_text,
            bgcolor=CARD_INNER_BG,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        header_row = ft.Row(
            controls=[
                ft.Icon(cat_icon, color=ACCENT_PRIMARY, size=16),
                ft.Text(
                    category_name,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ACCENT_PRIMARY,
                ),
                ft.Container(expand=True),
                self.cat_badge_container,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        header_container = ft.Container(
            content=header_row,
            tooltip="Нажмите для переключения выбора всех элементов категории",
            on_click=self._handle_category_click,
        )

        self.items_column = ft.Column(spacing=4)
        for item in items:
            tile = CacheItemTile(item=item, on_toggle=on_item_toggle)
            self.tiles_by_id[item.id] = tile
            self.items_column.controls.append(tile)

        super().__init__(
            content=ft.Column(
                controls=[
                    header_container,
                    ft.Divider(color=OUTLINE_VARIANT, height=1),
                    self.items_column,
                ],
                spacing=6,
            ),
            bgcolor=CARD_BG,
            border_radius=10,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            padding=10,
        )

    def _handle_category_click(self, e):
        if self.on_category_toggle:
            self.on_category_toggle(self.category_name)

    def update_category_size(self, total_bytes: int):
        """Targeted update of category badge without repainting the page."""
        self.cat_badge_text.value = format_size(total_bytes)
        self.cat_badge_text.color = ACCENT_PRIMARY if total_bytes > 0 else TEXT_SECONDARY
        self.cat_badge_container.update()
