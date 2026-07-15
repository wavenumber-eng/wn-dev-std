"""Shared text-formatting helpers for plan-log read commands."""

from __future__ import annotations

import textwrap

from wn_dev_std.cli.commands.text_format import ansi_style

ANSI_ROLE_STYLES = {
    "log": "\033[30;47m",
    "plan": "\033[30;47m",
    "step": "\033[1;33m",
}
LOG_ENTRY_VALUE_INDENT = "          "


def wrap_body_text(body: str, *, width: int) -> list[str]:
    """Wrap plain Markdown paragraphs while preserving structural lines."""
    lines: list[str] = []
    paragraph: list[str] = []
    in_code_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if _is_code_fence(stripped):
            _flush_paragraph(paragraph, lines, width)
            lines.append(line)
            in_code_fence = not in_code_fence
        elif in_code_fence or _is_preserved_markdown_line(line):
            _flush_paragraph(paragraph, lines, width)
            lines.append(line)
        elif not stripped:
            _flush_paragraph(paragraph, lines, width)
            lines.append("")
        else:
            paragraph.append(stripped)
    _flush_paragraph(paragraph, lines, width)
    return lines


def _flush_paragraph(paragraph: list[str], lines: list[str], width: int) -> None:
    if not paragraph:
        return
    lines.extend(
        textwrap.wrap(
            " ".join(paragraph),
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )
    paragraph.clear()


def _is_code_fence(stripped: str) -> bool:
    return stripped.startswith("```") or stripped.startswith("~~~")


def _is_preserved_markdown_line(line: str) -> bool:
    stripped = line.lstrip()
    return (
        line.startswith(("    ", "\t"))
        or stripped.startswith(("#", "-", "*", "+", ">", "|"))
        or stripped[:2].isdigit()
    )


def role_style(text: str, role: str, use_color: bool) -> str:
    """Apply ANSI styling for a semantic role when enabled."""
    return ansi_style(text, ANSI_ROLE_STYLES[role], use_color)
