# -*- coding: utf-8 -*-
"""
Footer Bar component showing deterministic progress bar and descriptive status label.
"""

import flet as ft
from ui.theme import (
    CARD_BG,
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_DANGER,
    TEXT_SECONDARY,
)


class FooterBar(ft.Container):
    """Bottom status bar with isolated progress bar and message updates."""

    def __init__(self):
        self.progress_bar = ft.ProgressBar(
            value=0,
            color=ACCENT_PRIMARY,
            bgcolor=CARD_INNER_BG,
            height=4,
            visible=False,
        )

        self.status_icon = ft.Icon(ft.Icons.INFO_OUTLINE, size=15, color=ACCENT_PRIMARY)
        self.status_label = ft.Text("Готов к работе.", size=12, color=TEXT_SECONDARY)

        super().__init__(
            content=ft.Column(
                controls=[
                    self.progress_bar,
                    ft.Row(
                        controls=[
                            self.status_icon,
                            self.status_label,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=CARD_BG,
            border_radius=8,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            padding=ft.Padding.symmetric(vertical=6, horizontal=12),
        )

    def set_progress(self, value: float | None, visible: bool = True):
        """Update progress bar value and visibility with isolated update."""
        self.progress_bar.visible = visible
        self.progress_bar.value = value
        self.progress_bar.update()

    def set_status(self, message: str, is_error: bool = False):
        """Update status message and icon with isolated update."""
        self.status_label.value = message
        self.status_label.color = ACCENT_DANGER if is_error else TEXT_SECONDARY
        self.status_icon.color = ACCENT_DANGER if is_error else ACCENT_PRIMARY
        self.status_label.update()
        self.status_icon.update()
