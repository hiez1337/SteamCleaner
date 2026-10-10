# -*- coding: utf-8 -*-
"""
Data models and utility functions for Steam & CS2 Cache Cleaner.
"""

from dataclasses import dataclass, field
from typing import Literal


CacheTargetType = Literal["dir_contents", "file_list", "dir_list_contents"]


@dataclass
class AccountInfo:
    """Steam account details from userdata and loginusers.vdf."""
    steamid3: str
    persona: str
    account: str


@dataclass
class CacheItem:
    """Represents a single cleaning target (directory, file list, or dir list)."""
    id: str
    label: str
    desc: str
    target_type: CacheTargetType
    path: str = ""
    paths_list: list[str] = field(default_factory=list)
    safe: bool = True
    count: int = 0
    bytes: int = 0


@dataclass
class ScanStats:
    """Aggregated cache statistics across all scanned targets."""
    total_files: int = 0
    total_bytes: int = 0
    gpu_bytes: int = 0
    cef_bytes: int = 0
    rec_bytes: int = 0
    category_sizes: dict[str, int] = field(default_factory=dict)


@dataclass
class CleanResult:
    """Results of a cache purge operation."""
    deleted_files: int = 0
    deleted_bytes: int = 0
    skipped_files: int = 0


def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string representation."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
