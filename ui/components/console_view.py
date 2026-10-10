# -*- coding: utf-8 -*-
"""
High-performance buffered console view with telemetry pills and clipboard copy.
"""

import asyncio
import datetime
import flet as ft
from core.models import format_size
from ui.theme import (
    CARD_BG,
    CARD_INNER_BG,
    OUTLINE_VARIANT,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_WARNING,
    ACCENT_DANGER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class ConsoleView(ft.Container):
    """
    Console log widget with debounced UI batching to prevent main thread rendering stutter.
    """

    def __init__(self, on_copy_click: callable):
        self.on_copy_click = on_copy_click
        self._buffer: list[ft.Text] = []
        self._flush_task: asyncio.Task | None = None

        self.stat_gpu_text = ft.Text("GPU: 0 B", size=10, weight=ft.FontWeight.W_600, color=ACCENT_PRIMARY)
        self.stat_cef_text = ft.Text("CEF: 0 B", size=10, weight=ft.FontWeight.W_600, color=ACCENT_WARNING)
        self.stat_rec_text = ft.Text("Записи: 0 B", size=10, weight=ft.FontWeight.W_600, color=ACCENT_DANGER)

        self.stat_gpu_box = self._make_stat_pill(self.stat_gpu_text, "#1b233a")
        self.stat_cef_box = self._make_stat_pill(self.stat_cef_text, "#2d231a")
        self.stat_rec_box = self._make_stat_pill(self.stat_rec_text, "#2d1a20")

        self.stats_strip = ft.Row(
            controls=[self.stat_gpu_box, self.stat_cef_box, self.stat_rec_box],
            spacing=6,
        )

        self.console_list = ft.ListView(
            expand=True,
            spacing=2,
            auto_scroll=True,
        )

        header_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TERMINAL, color=ACCENT_PRIMARY, size=18),
                ft.Text("Журнал операций", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.COPY_ALL_OUTLINED,
                    icon_size=18,
                    tooltip="Копировать журнал в буфер",
                    on_click=self._handle_copy,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLEAR_ALL,
                    icon_size=18,
                    tooltip="Очистить журнал",
                    on_click=self.clear_logs,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        console_container = ft.Container(
            content=self.console_list,
            bgcolor=CARD_INNER_BG,
            border_radius=8,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            padding=10,
            expand=True,
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    header_row,
                    self.stats_strip,
                    console_container,
                ],
                spacing=8,
                expand=True,
            ),
            bgcolor=CARD_BG,
            border_radius=10,
            border=ft.Border.all(1, OUTLINE_VARIANT),
            padding=12,
            expand=True,
        )

    def _make_stat_pill(self, text_widget: ft.Text, bg_color: str) -> ft.Container:
        return ft.Container(
            content=text_widget,
            bgcolor=bg_color,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

    def _handle_copy(self, e):
        if self.on_copy_click:
            self.on_copy_click(self.get_full_text())

    def clear_logs(self, e=None):
        """Clear all messages and update list view."""
        self.console_list.controls.clear()
        self.console_list.update()

    def get_full_text(self) -> str:
        """Extract full plain text of all log entries."""
        lines = []
        for line_widget in self.console_list.controls:
            if hasattr(line_widget, "spans") and line_widget.spans:
                lines.append("".join([s.text for s in line_widget.spans]))
            elif hasattr(line_widget, "value") and line_widget.value:
                lines.append(str(line_widget.value))
        return "".join(lines)

    def append_log(self, message: str, level: str = "INFO"):
        """Queue log message for buffered non-blocking UI flush."""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        color = TEXT_PRIMARY
        if level == "SUCCESS":
            color = ACCENT_SUCCESS
        elif level == "CLEAN":
            color = ACCENT_PRIMARY
        elif level == "WARN":
            color = ACCENT_WARNING
        elif level == "ERROR":
            color = ACCENT_DANGER

        line = ft.Text(
            spans=[
                ft.TextSpan(f"[{now_str}] ", style=ft.TextStyle(color=TEXT_SECONDARY, size=11, font_family="Consolas")),
                ft.TextSpan(f"[{level}] ", style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD, size=11, font_family="Consolas")),
                ft.TextSpan(f"{message}\n", style=ft.TextStyle(color=color, size=11, font_family="Consolas")),
            ]
        )
        self._buffer.append(line)

        if not self._flush_task or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._flush_buffer())

    async def _flush_buffer(self):
        """Debounce UI update by 40ms to batch rapid log lines."""
        await asyncio.sleep(0.04)
        if not self._buffer:
            return

        self.console_list.controls.extend(self._buffer)
        self._buffer.clear()
        if len(self.console_list.controls) > 300:
            del self.console_list.controls[:-300]

        self.console_list.update()

    def update_quick_stats(self, gpu_bytes: int, cef_bytes: int, rec_bytes: int):
        """Update top telemetry stat pills."""
        self.stat_gpu_text.value = f"GPU: {format_size(gpu_bytes)}"
        self.stat_cef_text.value = f"CEF: {format_size(cef_bytes)}"
        self.stat_rec_text.value = f"Записи: {format_size(rec_bytes)}"
        self.stats_strip.update()
