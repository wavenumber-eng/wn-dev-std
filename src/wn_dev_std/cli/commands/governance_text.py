"""Shared text-formatting helpers for governance read commands."""

from __future__ import annotations

from dataclasses import dataclass

from wn_dev_std.cli.commands.text_format import ansi_style
from wn_dev_std.doc_governance import ADR_STATUSES, REQUIREMENT_STATUSES

ANSI_BADGE_STYLES = {
    "accepted": "\033[1;37;42m",
    "active": "\033[1;37;42m",
    "deprecated": "\033[1;37;41m",
    "draft": "\033[30;43m",
    "implemented": "\033[1;37;42m",
    "proposed": "\033[30;43m",
    "superseded": "\033[30;47m",
    "default": "\033[30;47m",
}
ANSI_ROLE_STYLES = {
    "record": "\033[30;47m",
}
STATUS_SECTION_COLORS = {
    "accepted": "green",
    "active": "green",
    "deprecated": "red",
    "draft": "yellow",
    "implemented": "green",
    "proposed": "yellow",
    "superseded": "cyan",
}


@dataclass(frozen=True, slots=True)
class GovernanceListSection:
    """Display metadata for one governance-list text section."""

    status: str
    title: str
    color: str


ADR_LIST_SECTIONS = tuple(
    GovernanceListSection(status, status.title(), STATUS_SECTION_COLORS[status])
    for status in ADR_STATUSES
)
REQUIREMENT_LIST_SECTIONS = tuple(
    GovernanceListSection(status, status.title(), STATUS_SECTION_COLORS[status])
    for status in REQUIREMENT_STATUSES
)


def status_token(status: str, use_color: bool) -> str:
    """Render a status badge."""
    token = f"[{status}]"
    if not use_color:
        return token
    style_value = ANSI_BADGE_STYLES.get(status, ANSI_BADGE_STYLES["default"])
    return ansi_style(token, style_value, use_color)


def role_style(text: str, role: str, use_color: bool) -> str:
    """Apply ANSI styling for a semantic role when enabled."""
    return ansi_style(text, ANSI_ROLE_STYLES[role], use_color)
