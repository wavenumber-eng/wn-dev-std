"""Shared list implementation for governance read commands."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.governance_common import (
    context_from_args,
    output_format,
    print_catalog_failures,
    records_for_type,
)
from wn_dev_std.doc_governance import GovernanceRecord


def run_list_command(
    args: argparse.Namespace,
    record_type: str,
    title: str,
    payload_key: str,
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
