"""Resolve governance HTML links command."""

from __future__ import annotations

import argparse
from pathlib import Path

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.governance_links import configured_governance_output_root, resolve_governance_links


def register(subparsers: SubparserRegistry) -> None:
    """Register the resolve subcommand."""
    parser = subparsers.add_parser(
        "resolve",
        help="Resolve stable governance refs in HTML docs",
        description=(
            "Validate or rewrite data-dev-std-gov-ref hooks in downstream HTML docs "
            "so they point at generated governance pages."
        ),
    )
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument(
        "--output",
        help=(
            "Generated governance HTML output directory. Defaults to [governance.html] "
            "output or docs/generated/governance."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite href/data-dev-std-gov-href values in place",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the resolve command."""
    root = Path(_string_attr(args, "root"))
    output = _optional_string_attr(args, "output")
    output_root = Path(output) if output is not None else configured_governance_output_root(root)
    report = resolve_governance_links(root, output_root, write=bool(args.write))
    if report.issues:
        print(
            f"Governance link resolution failed for {len(report.issues)} issue(s) "
            f"under {report.root}"
        )
        for issue in report.issues:
            print(f"- {issue.relative_path}: {issue.message}")
        return 1
    mode = "updated" if args.write else "validated"
    print(
        f"Governance links {mode}: {report.resolved_count} ref(s) across "
        f"{len(report.checked_files)} HTML file(s); output={report.output_root}"
    )
    if report.changed_files:
        for path in report.changed_files:
            print(f"- changed {path}")
    return 0


def _string_attr(args: argparse.Namespace, name: str) -> str:
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")


def _optional_string_attr(args: argparse.Namespace, name: str) -> str | None:
    value = getattr(args, name)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")
