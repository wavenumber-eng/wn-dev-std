"""Small Markdown renderer for generated governance pages."""

from __future__ import annotations

import html
import re

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
STRONG_RE = re.compile(r"\*\*([^*]+)\*\*")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def render_governance_markdown(markdown: str) -> str:
    """Render the supported governance Markdown subset to semantic HTML."""
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            _flush_paragraph(paragraph, blocks)
            _flush_list(list_items, blocks)
            index = _consume_code_block(lines, index, blocks)
        elif _is_table_start(lines, index):
            _flush_paragraph(paragraph, blocks)
            _flush_list(list_items, blocks)
            index = _consume_table(lines, index, blocks)
        elif heading := _heading_html(stripped):
            _flush_paragraph(paragraph, blocks)
            _flush_list(list_items, blocks)
            blocks.append(heading)
            index += 1
        elif _is_unordered_list_item(stripped):
            _flush_paragraph(paragraph, blocks)
            list_items.append(_inline_html(stripped[2:].strip()))
            index += 1
        elif not stripped:
            _flush_paragraph(paragraph, blocks)
            _flush_list(list_items, blocks)
            index += 1
        else:
            _flush_list(list_items, blocks)
            paragraph.append(stripped)
            index += 1
    _flush_paragraph(paragraph, blocks)
    _flush_list(list_items, blocks)
    return '<div class="dev-std-gov-body">\n' + "\n".join(blocks) + "\n</div>"


def _consume_code_block(lines: list[str], index: int, blocks: list[str]) -> int:
    language = lines[index].strip().removeprefix("```").strip()
    code_lines: list[str] = []
    cursor = index + 1
    while cursor < len(lines) and not lines[cursor].strip().startswith("```"):
        code_lines.append(lines[cursor])
        cursor += 1
    language_class = f" language-{html.escape(language)}" if language else ""
    code = html.escape("\n".join(code_lines))
    blocks.append(
        f'<pre class="dev-std-gov-code-block"><code class="dev-std-gov-code{language_class}">'
        f"{code}</code></pre>"
    )
    return cursor + 1 if cursor < len(lines) else cursor


def _consume_table(lines: list[str], index: int, blocks: list[str]) -> int:
    headers = _table_cells(lines[index])
    cursor = index + 2
    rows: list[list[str]] = []
    while cursor < len(lines) and lines[cursor].strip().startswith("|"):
        rows.append(_table_cells(lines[cursor]))
        cursor += 1
    head = "".join(f"<th>{_inline_html(cell)}</th>" for cell in headers)
    body_rows: list[str] = []
    for row in rows:
        cells = "".join(f"<td>{_inline_html(cell)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    blocks.append(
        '<table class="dev-std-gov-table">'
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )
    return cursor


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return lines[index].strip().startswith("|") and _is_table_separator(lines[index + 1])


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    cells = _table_cells(stripped)
    return bool(cells) and all(set(cell.strip()) <= {"-", ":"} for cell in cells)


def _table_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _heading_html(stripped: str) -> str:
    match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
    if not match:
        return ""
    level = len(match.group(1))
    content = _inline_html(match.group(2).strip())
    return f'<h{level} class="dev-std-gov-h dev-std-gov-h{level}">{content}</h{level}>'


def _is_unordered_list_item(stripped: str) -> bool:
    return stripped.startswith("- ") or stripped.startswith("* ")


def _flush_paragraph(paragraph: list[str], blocks: list[str]) -> None:
    if not paragraph:
        return
    content = _inline_html(" ".join(paragraph))
    blocks.append(f'<p class="dev-std-gov-p">{content}</p>')
    paragraph.clear()


def _flush_list(list_items: list[str], blocks: list[str]) -> None:
    if not list_items:
        return
    items = "".join(f'<li class="dev-std-gov-list-item">{item}</li>' for item in list_items)
    blocks.append(f'<ul class="dev-std-gov-list">{items}</ul>')
    list_items.clear()


def _inline_html(text: str) -> str:
    escaped = html.escape(text)
    linked = LINK_RE.sub(_link_replacement, escaped)
    coded = INLINE_CODE_RE.sub(r'<code class="dev-std-gov-code-inline">\1</code>', linked)
    return STRONG_RE.sub(r'<strong class="dev-std-gov-strong">\1</strong>', coded)


def _link_replacement(match: re.Match[str]) -> str:
    label = match.group(1)
    href = match.group(2)
    return f'<a class="dev-std-gov-link" href="{href}">{label}</a>'
