# -*- coding: utf-8 -*-
"""
Material 3 Dark Theme and design tokens for Steam & CS2 Cache Cleaner.
Catppuccin Mocha inspired dark palette.
"""

import flet as ft

# Primary Palette
BG_COLOR = "#11111b"              # Base background
CARD_BG = "#1e1e2e"               # Surface container
CARD_INNER_BG = "#181825"         # Surface container low (inputs, pills)
CARD_HOVER_BG = "#252538"         # Surface container high
OUTLINE_VARIANT = "#313244"       # Subtle card borders
OUTLINE_FOCUSED = "#45475a"

# Semantic Accents
ACCENT_PRIMARY = "#89b4fa"        # Blue
ACCENT_SUCCESS = "#a6e3a1"        # Green
ACCENT_WARNING = "#fab387"        # Peach / Orange
ACCENT_DANGER = "#f38ba8"         # Red / Coral

# Typography Colors
TEXT_PRIMARY = "#cdd6f4"          # High emphasis text
TEXT_SECONDARY = "#a6adc8"        # Medium emphasis / subtext
TEXT_MUTED = "#6c7086"            # Low emphasis

# Badges & Status backgrounds
SUCCESS_BG = "#14261f"
SUCCESS_BORDER = "#275940"
WARNING_BG = "#2e251a"
WARNING_BORDER = "#5d4527"
DANGER_BG = "#2e1a22"
DANGER_BORDER = "#5d2738"


def get_app_theme() -> ft.Theme:
    """Build modern Material 3 Dark theme."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ACCENT_PRIMARY,
            on_primary="#11111b",
            secondary=ACCENT_SUCCESS,
            on_secondary="#11111b",
            tertiary=ACCENT_WARNING,
            on_tertiary="#11111b",
            error=ACCENT_DANGER,
            on_error="#11111b",
            surface=CARD_BG,
            on_surface=TEXT_PRIMARY,
            outline=OUTLINE_FOCUSED,
            outline_variant=OUTLINE_VARIANT,
            surface_container=CARD_BG,
            surface_container_low=CARD_INNER_BG,
            surface_container_high=CARD_HOVER_BG,
        ),
        font_family="Segoe UI",
    )


def card_border(color: str = OUTLINE_VARIANT, width: int = 1) -> ft.Border:
    """Standard border helper."""
    return ft.Border.all(width, color)
