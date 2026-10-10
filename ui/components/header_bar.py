# -*- coding: utf-8 -*-
"""
Header Bar component displaying application title, process telemetry and termination button.
"""

import asyncio
import flet as ft
from ui.theme import (
    CARD_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_WARNING,
    ACCENT_DANGER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SUCCESS_BG,
    SUCCESS_BORDER,
    WARNING_BG,
    WARNING_BORDER,
    DANGER_BG,
    DANGER_BORDER,
)


class HeaderBar(ft.Container):
    """Modern header with active process status and killer action."""

    def __init__(self, on_terminate_click: callable):
        self.on_terminate_click = on_terminate_click

        self.status_dot = ft.Icon(ft.Icons.CIRCLE, size=9, color=ACCENT_SUCCESS)
        self.status_text = ft.Text(
            "Steam и CS2 закрыты",
            size=11,
            weight=ft.FontWeight.W_600,
            color=ACCENT_SUCCESS,
        )

        self.proc_status_badge = ft.Container(
            content=ft.Row(
                controls=[self.status_dot, self.status_text],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=SUCCESS_BG,
            border=ft.Border.all(1, SUCCESS_BORDER),
            border_radius=16,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )

        self.terminate_btn = ft.OutlinedButton(
            "Закрыть Steam & CS2",
            icon=ft.Icons.STOP_CIRCLE_OUTLINED,
            height=34,
            disabled=True,
            on_click=self._handle_terminate,
            style=ft.ButtonStyle(
                color=TEXT_PRIMARY,
                side=ft.BorderSide(1, OUTLINE_VARIANT),
            ),
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.SPEED, size=24, color=ACCENT_PRIMARY),
                        bgcolor="#1e2238",
                        border=ft.Border.all(1, "#363a56"),
                        border_radius=10,
                        padding=8,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "CS2 & Steam Deep Cache Cleaner",
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Оптимизация фреймтайма и 1% Low FPS: очистка шейдеров GPU, кэша инвентаря, CEF и legacy-конфигов",
                                size=11,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    self.proc_status_badge,
                    self.terminate_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=CARD_BG,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        )

    async def _handle_terminate(self, e):
        if self.on_terminate_click:
            self.terminate_btn.disabled = True
            self.terminate_btn.update()
            try:
                res = self.on_terminate_click(e)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                self.terminate_btn.disabled = False
                self.terminate_btn.update()
    def update_process_status(self, steam_on: bool, cs2_on: bool):
        """Update telemetry badge without repainting the entire page."""
        if cs2_on:
            self.status_text.value = "ВНИМАНИЕ: CS2 запущена"
            self.status_text.color = ACCENT_DANGER
            self.status_dot.color = ACCENT_DANGER
            self.proc_status_badge.bgcolor = DANGER_BG
            self.proc_status_badge.border = ft.Border.all(1, DANGER_BORDER)
            self.terminate_btn.disabled = False
        elif steam_on:
            self.status_text.value = "Steam запущен"
            self.status_text.color = ACCENT_WARNING
            self.status_dot.color = ACCENT_WARNING
            self.proc_status_badge.bgcolor = WARNING_BG
            self.proc_status_badge.border = ft.Border.all(1, WARNING_BORDER)
            self.terminate_btn.disabled = False
        else:
            self.status_text.value = "Steam и CS2 закрыты"
            self.status_text.color = ACCENT_SUCCESS
            self.status_dot.color = ACCENT_SUCCESS
            self.proc_status_badge.bgcolor = SUCCESS_BG
            self.proc_status_badge.border = ft.Border.all(1, SUCCESS_BORDER)
            self.terminate_btn.disabled = True

        self.update()
