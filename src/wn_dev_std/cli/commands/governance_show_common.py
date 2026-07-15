"""Shared show implementation for governance read commands."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.governance_common import (
    context_from_args,
    find_record,
    output_format,
    print_catalog_failures,
    record_body,
    string_attr,
)
from wn_dev_std.cli.commands.governance_text import (
    role_style,
    status_token,
)
from wn_dev_std.cli.commands.text_format import (
    FIELD_VALUE_INDENT,
    normalized_width,
    output_width,
    should_use_color,
    wrap_indented_text,
)
from wn_dev_std.doc_governance import GovernanceRecord


def run_show_command(
    args: argparse.Namespace,
    record_type: str,
    title: str,
    id_arg: str,
    *,
    pretty_text: bool = False,
) -> int:
    """Run a governance record show command."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    record_id = string_attr(args, id_arg)
    record = find_record(context.catalog, record_type, record_id)
    if record is None:
        print(f"{record_type} not found: {record_id}")
        return 1
    body = record_body(context.catalog, record)
    if output_format(args) == "json":
        print(json.dumps(_record_payload(record, body), indent=2, sort_keys=True))
        return 0
    if pretty_text:
        print(
            _format_pretty_record_show_text(
                title,
                record,
                body,
                use_color=should_use_color(),
                width=output_width(),
            )
        )
        return 0
    print(_format_record_show_text(title, record, body))
    return 0


def _record_payload(record: GovernanceRecord, body: str) -> dict[str, object]:
    return {
        "id": record.record_id,
        "type": record.record_type,
        "domain": record.domain,
        "status": record.status,
        "title": record.title,
        "created": record.created,
        "path": record.relative_path,
        "body": body,
    }


def _format_record_show_text(title: str, record: GovernanceRecord, body: str) -> str:
    lines = [
        f"{title}: {record.record_id}",
        f"Status: {record.status}",
        f"Domain: {record.domain}",
        f"Title: {record.title}",
        f"Created: {record.created}",
        f"Path: {record.relative_path}",
    ]
    if body:
        lines.extend(["", body])
    return "\n".join(lines)


def _format_pretty_record_show_text(
    title: str,
    record: GovernanceRecord,
    body: str,
    *,
    use_color: bool = False,
    width: int = 100,
) -> str:
    formatted_width = normalized_width(width)
    record_id = role_style(record.record_id, "record", use_color)
    lines = [
        f"{title}:",
        f"  - {record_id} {status_token(record.status, use_color)}",
        f"    created: {record.created}",
        f"    domain: {record.domain}",
        "    title:",
        *wrap_indented_text(record.title, indent=FIELD_VALUE_INDENT, width=formatted_width),
        "    path:",
        *wrap_indented_text(
            record.relative_path,
            indent=FIELD_VALUE_INDENT,
            width=formatted_width,
        ),
    ]
    if body:
        lines.extend(["", body])
    return "\n".join(lines) + "\n"
