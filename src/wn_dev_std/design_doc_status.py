"""HTML design-document status marker checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DesignDocStatusReport:
    """Design-document status check result."""

    passed: bool
    detail: str


DESIGN_DOC_STATUS_VALUES = ("draft", "proposal", "accepted", "superseded")
DESIGN_DOC_REPORT_STATUSES = {"draft", "proposal"}


def check_design_doc_status_policy(root: Path) -> DesignDocStatusReport:
    """Check HTML design docs for explicit maturity markers."""
    design_root = root / "docs" / "design"
    if not design_root.exists():
        return DesignDocStatusReport(
            True,
            "docs/design is absent; required documentation check owns this path",
        )

    docs = sorted(design_root.rglob("*.html"))
    if not docs:
        return DesignDocStatusReport(True, "no HTML design docs found")

    statuses = _classify_design_docs(root, docs)
    failure = _status_failure_detail(statuses)
    if failure:
        return DesignDocStatusReport(False, failure)
    return DesignDocStatusReport(True, _status_success_detail(statuses))


def _classify_design_docs(root: Path, docs: list[Path]) -> dict[str, list[str]]:
    statuses: dict[str, list[str]] = {
        "accepted": [],
        "invalid": [],
        "missing": [],
        "reportable": [],
    }
    for path in docs:
        relative_path = path.relative_to(root).as_posix()
        _append_status(statuses, relative_path, _design_doc_status(path))
    return statuses


def _append_status(statuses: dict[str, list[str]], relative_path: str, status: str) -> None:
    if status == "":
        statuses["missing"].append(relative_path)
    elif status not in DESIGN_DOC_STATUS_VALUES:
        statuses["invalid"].append(f"{relative_path}={status}")
    elif status in DESIGN_DOC_REPORT_STATUSES:
        statuses["reportable"].append(f"{relative_path}={status}")
    else:
        statuses["accepted"].append(relative_path)


def _status_failure_detail(statuses: dict[str, list[str]]) -> str:
    details: list[str] = []
    if statuses["missing"]:
        details.append("missing data-doc-status in " + _summarize_items(statuses["missing"]))
    if statuses["invalid"]:
        details.append(
            "invalid status in "
            + _summarize_items(statuses["invalid"])
            + "; expected "
            + ", ".join(DESIGN_DOC_STATUS_VALUES)
        )
    return "; ".join(details)


def _status_success_detail(statuses: dict[str, list[str]]) -> str:
    accepted_count = len(statuses["accepted"])
    if statuses["reportable"]:
        return f"{accepted_count} accepted/superseded; draft/proposal docs: " + _summarize_items(
            statuses["reportable"]
        )
    return f"all {accepted_count} HTML design doc(s) are accepted or superseded"


def _design_doc_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\bdata-doc-status=[\"']([^\"']+)[\"']", text)
    return match.group(1).strip().lower() if match else ""


def _summarize_items(items: list[str], limit: int = 5) -> str:
    shown = items[:limit]
    suffix = "" if len(items) <= limit else f" and {len(items) - limit} more"
    return ", ".join(shown) + suffix
