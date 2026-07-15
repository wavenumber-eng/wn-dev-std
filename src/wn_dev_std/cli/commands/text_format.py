"""Shared terminal text-formatting helpers for CLI read commands."""

from __future__ import annotations

import os
import shutil
import sys
import textwrap

ANSI_RESET = "\033[0m"
ANSI_COLORS = {
    "cyan": "\033[36m",
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
}
MAX_TEXT_WIDTH = 100
MIN_TEXT_WIDTH = 60
FIELD_VALUE_INDENT = "      "


def should_use_color() -> bool:
    """Return whether CLI output should include ANSI styling."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def output_width() -> int:
    """Return normalized terminal text width."""
    return normalized_width(shutil.get_terminal_size((MAX_TEXT_WIDTH, 20)).columns)


def normalized_width(width: int) -> int:
    """Clamp text width to the formatter-supported range."""
    return min(max(width, MIN_TEXT_WIDTH), MAX_TEXT_WIDTH)


def wrap_indented_text(text: str, *, indent: str, width: int) -> list[str]:
    """Wrap text under an already-rendered field label."""
    available_width = max(width - len(indent), 24)
    wrapped = textwrap.wrap(
        text,
        width=available_width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [indent + line for line in wrapped]


def ansi_style(text: str, ansi_code: str, use_color: bool) -> str:
    """Apply an explicit ANSI code when enabled."""
    if not use_color:
        return text
    return f"{ansi_code}{text}{ANSI_RESET}"


def style(text: str, color: str, use_color: bool) -> str:
    """Apply an ANSI foreground color when enabled."""
    if not use_color:
        return text
    return f"{ANSI_COLORS[color]}{text}{ANSI_RESET}"
