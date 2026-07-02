"""Build-document governance checks."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class BuildDocGovernanceReport:
    """Build-document governance check result."""

    passed: bool
    detail: str


BUILD_DOC_CANDIDATES = (
    Path("docs/build.html"),
    Path("docs/build.md"),
)
REQUIRED_TOPIC_GROUPS = {
    "tools/setup": ("tool", "setup", "prerequisite", "dependency"),
    "commands/invocation": ("command", "invoke", "run", "build"),
    "outputs/artifacts": ("output", "artifact", "dist", "package", "wheel"),
    "validation/signoff": ("test", "validate", "signoff", "smoke"),
}


def check_build_doc_policy(root: Path) -> BuildDocGovernanceReport:
    """Check for a canonical build document with minimal metadata and topics."""
    resolved_root = root.resolve()
    path = _build_doc_path(resolved_root)
    if path is None:
        return BuildDocGovernanceReport(
            False,
            "missing canonical build doc: docs/build.html or docs/build.md",
        )
    failures = _validate_build_doc(resolved_root, path)
    if failures:
        return BuildDocGovernanceReport(
            False,
            f"{path.relative_to(resolved_root).as_posix()}: " + "; ".join(failures),
        )
    return BuildDocGovernanceReport(
        True,
        f"{path.relative_to(resolved_root).as_posix()} passed build-doc governance",
    )


def _build_doc_path(root: Path) -> Path | None:
    for relative_path in BUILD_DOC_CANDIDATES:
        path = root / relative_path
        if path.exists():
            return path
    return None


def _validate_build_doc(root: Path, path: Path) -> list[str]:
    if path.suffix.lower() == ".html":
        return _validate_html_build_doc(path)
    if path.suffix.lower() == ".md":
        return _validate_markdown_build_doc(root, path)
    return ["unsupported build doc format"]


def _validate_html_build_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not re.search(r"\bdata-doc=[\"']build[\"']", text):
        failures.append('missing data-doc="build"')
    status = _html_attr(text, "data-doc-status")
    if status != "accepted":
        failures.append('data-doc-status must be "accepted"')
    failures.extend(_missing_topic_failures(text))
    return failures


def _validate_markdown_build_doc(root: Path, path: Path) -> list[str]:
    del root
    metadata, body = _parse_front_matter(path)
    failures: list[str] = []
    if metadata.get("type") != "build_doc":
        failures.append('front matter type must be "build_doc"')
    for key in ("id", "title"):
        if not _string_value(metadata.get(key)):
            failures.append(f"missing {key}")
    if metadata.get("status") != "accepted":
        failures.append('status must be "accepted"')
    failures.extend(_missing_topic_failures(body))
    return failures


def _parse_front_matter(path: Path) -> tuple[Mapping[str, object], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return {}, text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            raw_front_matter = "\n".join(lines[1:index])
            metadata = cast(Mapping[str, object], tomllib.loads(raw_front_matter))
            body = "\n".join(lines[index + 1 :])
            return metadata, body
    return {}, text


def _missing_topic_failures(text: str) -> list[str]:
    normalized = text.lower()
    failures: list[str] = []
    for topic, tokens in REQUIRED_TOPIC_GROUPS.items():
        if not any(token in normalized for token in tokens):
            failures.append(f"missing build topic {topic}")
    return failures


def _html_attr(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=[\"']([^\"']+)[\"']", text)
    return match.group(1).strip().lower() if match else ""


def _string_value(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""
