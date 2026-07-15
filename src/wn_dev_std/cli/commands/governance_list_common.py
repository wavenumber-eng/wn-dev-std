"""Shared list implementation for governance read commands."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from wn_dev_std.cli.commands.governance_common import (
    context_from_args,
    output_format,
    print_catalog_failures,
    records_for_type,
)
from wn_dev_std.cli.commands.governance_text import (
    ADR_LIST_SECTIONS,
    REQUIREMENT_LIST_SECTIONS,
    GovernanceListSection,
    role_style,
    status_token,
)
from wn_dev_std.cli.commands.text_format import (
    FIELD_VALUE_INDENT,
    normalized_width,
    output_width,
    should_use_color,
    style,
    wrap_indented_text,
)
from wn_dev_std.doc_governance import GovernanceRecord


def run_list_command(
    args: argparse.Namespace,
    record_type: str,
    title: str,
    payload_key: str,
    *,
    pretty_text: bool = False,
) -> int:
    """Run a governance record list command."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    records = records_for_type(context.catalog, record_type)
    if output_format(args) == "json":
        print(
            json.dumps(
                {
                    "root": str(context.catalog.root),
                    "marker": context.discovered_root.marker,
                    payload_key: [_record_payload(record) for record in records],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if pretty_text:
        print(
            _format_pretty_record_list_text(
                context.catalog.root,
                title,
                records,
                _sections_for_type(record_type),
                use_color=should_use_color(),
                width=output_width(),
            )
        )
        return 0
    print(_format_record_list_text(context.catalog.root, title, records))
    return 0


def _record_payload(record: GovernanceRecord) -> dict[str, object]:
    return {
        "id": record.record_id,
        "type": record.record_type,
        "domain": record.domain,
        "status": record.status,
        "title": record.title,
        "created": record.created,
        "path": record.relative_path,
    }


def _format_record_list_text(
    root: object,
    title: str,
    records: tuple[GovernanceRecord, ...],
) -> str:
    if not records:
        return f"No compliant {title} found under {root}"
    lines = [f"{title} under {root}:"]
    for record in records:
        lines.append(
            f"- {record.record_id} [{record.status}] {record.relative_path} "
            f"domain={record.domain} title={record.title}"
        )
    return "\n".join(lines)


def _format_pretty_record_list_text(
    root: object,
    title: str,
    records: tuple[GovernanceRecord, ...],
    sections: tuple[GovernanceListSection, ...],
    *,
    use_color: bool = False,
    width: int = 100,
) -> str:
    if not records:
        return f"No compliant {title} found under {root}"
    formatted_width = normalized_width(width)
    grouped = _group_records(records, sections)
    lines = [
        f"{title} under {root}:",
        "",
        "Summary:",
        *_format_group_summary_lines(grouped, sections),
    ]
    for section in sections:
        section_records = grouped[section.status]
        if not section_records:
            continue
        lines.extend(["", style(section.title, section.color, use_color)])
        lines.append(style("-" * len(section.title), section.color, use_color))
        for index, record in enumerate(section_records):
            if index:
                lines.append("")
            lines.extend(_format_pretty_record_entry(record, use_color, formatted_width))
    return "\n".join(lines) + "\n"


def _sections_for_type(record_type: str) -> tuple[GovernanceListSection, ...]:
    if record_type == "adr":
        return ADR_LIST_SECTIONS
    if record_type == "requirement":
        return REQUIREMENT_LIST_SECTIONS
    raise ValueError(f"unsupported pretty list record type: {record_type}")


def _group_records(
    records: Sequence[GovernanceRecord],
    sections: tuple[GovernanceListSection, ...],
) -> dict[str, list[GovernanceRecord]]:
    grouped: dict[str, list[GovernanceRecord]] = {section.status: [] for section in sections}
    for record in records:
        if record.status not in grouped:
            grouped[record.status] = []
        grouped[record.status].append(record)
    return grouped


def _format_group_summary_lines(
    grouped: dict[str, list[GovernanceRecord]],
    sections: tuple[GovernanceListSection, ...],
) -> list[str]:
    return [f"  {section.status}: {len(grouped[section.status])}" for section in sections]


def _format_pretty_record_entry(
    record: GovernanceRecord,
    use_color: bool,
    width: int,
) -> list[str]:
    record_id = role_style(record.record_id, "record", use_color)
    lines = [
        f"  - {record_id} {status_token(record.status, use_color)}",
        f"    created: {record.created}",
        f"    domain: {record.domain}",
        "    title:",
        *wrap_indented_text(record.title, indent=FIELD_VALUE_INDENT, width=width),
        "    path:",
        *wrap_indented_text(record.relative_path, indent=FIELD_VALUE_INDENT, width=width),
    ]
    return lines
