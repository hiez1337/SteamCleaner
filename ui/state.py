# -*- coding: utf-8 -*-
"""
Application State management for Steam & CS2 Cache Cleaner.
Decouples business logic and cache selections from UI controls.
"""

import os
from typing import Optional
from core.models import AccountInfo, CacheItem, ScanStats
from core.hardware import (
    detect_steam_path,
    detect_cs2_path,
    detect_steam_accounts,
    build_targets_manifest,
)


class AppState:
    """Central reactive application state container."""

    def __init__(self, backup_dir: Optional[str] = None):
        self.steam_path: str = detect_steam_path()
        self.cs2_path: str = detect_cs2_path(self.steam_path)
        self.accounts: list[AccountInfo] = detect_steam_accounts(self.steam_path)
        self.selected_account_id: str = self.accounts[0].steamid3 if self.accounts else ""

        if backup_dir:
            self.backup_dir = backup_dir
        else:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.backup_dir = os.path.join(root_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.manifest: dict[str, list[CacheItem]] = {}
        self.selected_item_ids: set[str] = set()
        self.is_busy: bool = False
        self.steam_running: bool = False
        self.cs2_running: bool = False
        self.scan_stats: ScanStats = ScanStats()

        self.refresh_manifest()

    def refresh_manifest(self):
        """Rebuild manifest and initialize default safe selections."""
        self.manifest = build_targets_manifest(
            steam_path=self.steam_path,
            cs2_path=self.cs2_path,
            selected_account_id=self.selected_account_id,
        )
        # Select safe items by default
        self.selected_item_ids.clear()
        for _, items in self.manifest.items():
            for it in items:
                if it.safe:
                    self.selected_item_ids.add(it.id)

    def set_steam_path(self, new_path: str):
        """Update steam path and re-detect CS2 and accounts."""
        if not new_path or not os.path.isdir(new_path):
            return
        self.steam_path = os.path.normpath(new_path)
        self.cs2_path = detect_cs2_path(self.steam_path)
        self.accounts = detect_steam_accounts(self.steam_path)
        if self.accounts:
            self.selected_account_id = self.accounts[0].steamid3
        else:
            self.selected_account_id = ""
        self.refresh_manifest()

    def set_account_id(self, account_id: str):
        """Switch active steam account and rebuild manifest."""
        self.selected_account_id = account_id
        self.refresh_manifest()

    def toggle_item(self, item_id: str, is_checked: bool):
        """Toggle single item selection."""
        if is_checked:
            self.selected_item_ids.add(item_id)
        else:
            self.selected_item_ids.discard(item_id)

    def toggle_category(self, cat_name: str, new_val: bool):
        """Toggle all items in a category."""
        items = self.manifest.get(cat_name, [])
        for it in items:
            if new_val:
                # Do not auto-select unsafe items on generic toggle
                if it.safe:
                    self.selected_item_ids.add(it.id)
            else:
                self.selected_item_ids.discard(it.id)

    def select_preset_recommended(self):
        """Select only items marked safe."""
        self.selected_item_ids.clear()
        for _, items in self.manifest.items():
            for it in items:
                if it.safe:
                    self.selected_item_ids.add(it.id)

    def select_all(self, include_unsafe: bool = False):
        """Select all items, optionally including unsafe items."""
        self.selected_item_ids.clear()
        for _, items in self.manifest.items():
            for it in items:
                if it.safe or include_unsafe:
                    self.selected_item_ids.add(it.id)

    def deselect_all(self):
        """Deselect all items."""
        self.selected_item_ids.clear()

    def get_selected_items(self) -> list[CacheItem]:
        """Return list of currently selected CacheItem objects."""
        selected: list[CacheItem] = []
        for _, items in self.manifest.items():
            for it in items:
                if it.id in self.selected_item_ids:
                    selected.append(it)
        return selected

    def get_summary(self) -> tuple[int, int]:
        """Calculate total (files_count, total_bytes) for selected items."""
        total_files = 0
        total_bytes = 0
        for it in self.get_selected_items():
            total_files += it.count
            total_bytes += it.bytes
        return total_files, total_bytes

    def get_item_by_id(self, item_id: str) -> Optional[CacheItem]:
        """Lookup item across all categories by ID."""
        for _, items in self.manifest.items():
            for it in items:
                if it.id == item_id:
                    return it
        return None
