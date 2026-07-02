"""Resolve stable governance refs to generated governance HTML pages."""

from __future__ import annotations

import html
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.doc_governance import load_governance_catalog
from wn_dev_std.plan_hygiene import load_plan_catalog
from wn_dev_std.root_discovery import load_pyproject, load_standard_config


@dataclass(frozen=True, slots=True)
class GovernanceLinkIssue:
    """One governance link resolution issue."""

    relative_path: str
    message: str


@dataclass(frozen=True, slots=True)
class GovernanceLinkReport:
    """Governance link resolution result."""

    root: Path
    output_root: Path
    checked_files: tuple[str, ...]
    resolved_count: int
    changed_files: tuple[str, ...]
    issues: tuple[GovernanceLinkIssue, ...]

    @property
    def passed(self) -> bool:
        """Return whether all governance refs resolved cleanly."""
        return not self.issues


GOV_REF_START_TAG_RE = re.compile(
    r"<(?P<tag>[A-Za-z][A-Za-z0-9:-]*)(?P<attrs>[^>]*)\bdata-dev-std-gov-ref="
    r"(?P<quote>[\"'])(?P<ref>[^\"']+)(?P=quote)(?P<tail>[^>]*)>",
    re.IGNORECASE,
)
HREF_RE = re.compile(r"\bhref=(?P<quote>[\"'])(?P<href>[^\"']*)(?P=quote)", re.IGNORECASE)
GOV_HREF_RE = re.compile(
    r"\bdata-dev-std-gov-href=(?P<quote>[\"'])(?P<href>[^\"']*)(?P=quote)",
    re.IGNORECASE,
)
DEFAULT_GOVERNANCE_HTML_OUTPUT = "docs/generated/governance"
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "rack_results",
}


def check_governance_link_resolution(root: Path) -> GovernanceLinkReport:
    """Validate stable governance refs in downstream HTML docs."""
    resolved_root = root.resolve()
    output_root = configured_governance_output_root(resolved_root)
    return resolve_governance_links(resolved_root, output_root, write=False)


def resolve_governance_links(
    root: Path,
    output_root: Path | None = None,
    *,
    write: bool = False,
) -> GovernanceLinkReport:
    """Resolve or rewrite stable governance refs in downstream HTML docs."""
    resolved_root = root.resolve()
    resolved_output = (
        output_root.resolve()
        if output_root is not None
        else configured_governance_output_root(resolved_root)
    )
    index = governance_link_index(resolved_root, resolved_output)
    issues: list[GovernanceLinkIssue] = []
    changed_files: list[str] = []
    checked_files: list[str] = []
    resolved_count = 0

    for path in _candidate_html_docs(resolved_root, resolved_output):
        relative_path = path.relative_to(resolved_root).as_posix()
        text = path.read_text(encoding="utf-8")
        checked_files.append(relative_path)
        resolved_in_file = 0

        def replacement(
            match: re.Match[str],
            *,
            current_path: Path = path,
            current_relative_path: str = relative_path,
        ) -> str:
            nonlocal resolved_count, resolved_in_file
            rewritten, resolved = _resolve_match(
                resolved_root,
                resolved_output,
                current_path,
                current_relative_path,
                match,
                index,
                issues,
                write=write,
            )
            if resolved:
                resolved_count += 1
                resolved_in_file += 1
            return rewritten

        new_text = GOV_REF_START_TAG_RE.sub(replacement, text)
        if write and new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed_files.append(relative_path)
        elif resolved_in_file:
            # Keep resolved_count independent of whether the document needed edits.
            pass

    return GovernanceLinkReport(
        resolved_root,
        resolved_output,
        tuple(checked_files),
        resolved_count,
        tuple(changed_files),
        tuple(issues),
    )


def governance_link_index(root: Path, output_root: Path) -> Mapping[str, Path]:
    """Return governance id to generated-page path mapping."""
    pyproject = load_pyproject(root)
    config = load_standard_config(root, pyproject)
    plan_catalog = load_plan_catalog(root, config)
    governance_catalog = load_governance_catalog(root)
    index: dict[str, Path] = {}
    for plan in plan_catalog.plans:
        index[plan.plan_id] = output_root / "plan" / f"{_safe_filename(plan.plan_id)}.html"
    for log in plan_catalog.logs:
        index[log.log_id] = output_root / "plan_log" / f"{_safe_filename(log.log_id)}.html"
    for adr in governance_catalog.adrs:
        index[adr.record_id] = output_root / "adr" / f"{_safe_filename(adr.record_id)}.html"
    for requirement in governance_catalog.requirements:
        index[requirement.record_id] = (
            output_root / "requirement" / f"{_safe_filename(requirement.record_id)}.html"
        )
    return index


def configured_governance_output_root(root: Path) -> Path:
    """Return configured generated governance HTML output root."""
    pyproject = load_pyproject(root)
    config = load_standard_config(root, pyproject)
    output = _configured_output_value(config)
    if output is None:
        output = DEFAULT_GOVERNANCE_HTML_OUTPUT
    output_path = Path(output)
    return output_path.resolve() if output_path.is_absolute() else (root / output_path).resolve()


def _configured_output_value(config: Mapping[str, object] | None) -> str | None:
    if config is None:
        return None
    output = _nested_output(config, "governance", "html")
    if output is not None:
        return output
    return _nested_output(config, "documentation", "governance")


def _nested_output(config: Mapping[str, object], first_key: str, second_key: str) -> str | None:
    first = config.get(first_key)
    if not isinstance(first, dict):
        return None
    second = cast(Mapping[str, object], first).get(second_key)
    if not isinstance(second, dict):
        return None
    output = cast(Mapping[str, object], second).get("output")
    if isinstance(output, str) and output.strip():
        return output.strip()
    return None


def _resolve_match(
    root: Path,
    output_root: Path,
    path: Path,
    relative_path: str,
    match: re.Match[str],
    index: Mapping[str, Path],
    issues: list[GovernanceLinkIssue],
    *,
    write: bool,
) -> tuple[str, bool]:
    ref_id = html.unescape(match.group("ref")).strip()
    target = index.get(ref_id)
    if target is None:
        issues.append(GovernanceLinkIssue(relative_path, f"unknown governance ref {ref_id!r}"))
        return match.group(0), False
    if not _is_within_root(root, target):
        issues.append(
            GovernanceLinkIssue(relative_path, f"governance ref {ref_id!r} output escapes root")
        )
        return match.group(0), False
    href = _relative_href(path, target)
    tag = match.group("tag").lower()
    start_tag = match.group(0)
    if tag == "a":
        return _resolve_attribute(
            start_tag,
            "href",
            _href_value(start_tag),
            href,
            ref_id,
            relative_path,
            issues,
            write=write,
        )
    return _resolve_attribute(
        start_tag,
        "data-dev-std-gov-href",
        _gov_href_value(start_tag),
        href,
        ref_id,
        relative_path,
        issues,
        write=write,
    )


def _resolve_attribute(
    start_tag: str,
    attribute: str,
    current_href: str | None,
    expected_href: str,
    ref_id: str,
    relative_path: str,
    issues: list[GovernanceLinkIssue],
    *,
    write: bool,
) -> tuple[str, bool]:
    if write:
        return _set_attribute(start_tag, attribute, expected_href), True
    _append_attribute_issue(attribute, current_href, expected_href, ref_id, relative_path, issues)
    return start_tag, current_href == expected_href


def _append_attribute_issue(
    attribute: str,
    current_href: str | None,
    expected_href: str,
    ref_id: str,
    relative_path: str,
    issues: list[GovernanceLinkIssue],
) -> None:
    if current_href is None:
        issues.append(
            GovernanceLinkIssue(
                relative_path,
                f"governance ref {ref_id!r} missing {attribute}; expected {expected_href!r}",
            )
        )
        return
    if current_href != expected_href:
        issues.append(
            GovernanceLinkIssue(
                relative_path,
                f"governance ref {ref_id!r} {attribute} {current_href!r} "
                f"should be {expected_href!r}",
            )
        )


def _candidate_html_docs(root: Path, output_root: Path) -> tuple[Path, ...]:
    docs_root = root / "docs"
    if not docs_root.exists():
        return ()
    paths: list[Path] = []
    for path in sorted(docs_root.rglob("*.html")):
        if _is_excluded(path, root):
            continue
        if _is_within_root(output_root, path.resolve()):
            continue
        paths.append(path)
    return tuple(paths)


def _href_value(tag: str) -> str | None:
    match = HREF_RE.search(tag)
    return html.unescape(match.group("href")) if match else None


def _gov_href_value(tag: str) -> str | None:
    match = GOV_HREF_RE.search(tag)
    return html.unescape(match.group("href")) if match else None


def _set_attribute(tag: str, name: str, value: str) -> str:
    escaped_value = html.escape(value, quote=True)
    if name == "href":
        pattern = HREF_RE
    elif name == "data-dev-std-gov-href":
        pattern = GOV_HREF_RE
    else:
        raise ValueError(f"unsupported attribute: {name}")
    if pattern.search(tag):
        return pattern.sub(f'{name}="{escaped_value}"', tag, count=1)
    insert_at = tag.rfind(">")
    if insert_at < 0:
        return tag
    return f'{tag[:insert_at]} {name}="{escaped_value}"{tag[insert_at:]}'


def _is_within_root(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return bool(EXCLUDED_PARTS.intersection(parts))


def _relative_href(source: Path, target: Path) -> str:
    return os.path.relpath(target, source.parent).replace("\\", "/")


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
