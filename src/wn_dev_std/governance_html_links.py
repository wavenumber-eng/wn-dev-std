"""Rewrite links embedded in generated governance HTML bodies."""

from __future__ import annotations

import html
import os
import re
from collections.abc import Mapping
from pathlib import Path

from wn_dev_std.governance_markdown import render_governance_markdown

RENDERED_MARKDOWN_HREF_RE = re.compile(
    r'(?P<prefix><a class="dev-std-gov-link" href=")(?P<href>[^"]+)(?P<suffix>")'
)


def render_document_markdown(
    root: Path,
    output_path: Path,
    source_path: str,
    body: str,
    source_output_index: Mapping[Path, Path],
) -> str:
    """Render a body and rewrite its source-relative links for generated HTML."""
    rendered = render_governance_markdown(body)
    source = (root / source_path).resolve()

    def replace_href(match: re.Match[str]) -> str:
        href = html.unescape(match.group("href"))
        if _is_external_href(href):
            return match.group(0)
        href_path, suffix = _split_href_suffix(href)
        if not href_path:
            return match.group(0)
        source_target = (source.parent / href_path).resolve()
        output_target = source_output_index.get(source_target, source_target)
        rewritten = _relative_href(output_path, output_target) + suffix
        return match.group("prefix") + html.escape(rewritten, quote=True) + match.group("suffix")

    return RENDERED_MARKDOWN_HREF_RE.sub(replace_href, rendered)


def _split_href_suffix(href: str) -> tuple[str, str]:
    positions = [index for marker in ("?", "#") if (index := href.find(marker)) >= 0]
    if not positions:
        return href, ""
    split_at = min(positions)
    return href[:split_at], href[split_at:]


def _is_external_href(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:", "#", "/"))


def _relative_href(source: Path, target: Path) -> str:
    return Path(os.path.relpath(target, start=source.parent)).as_posix()
