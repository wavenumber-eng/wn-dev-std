"""Governance-document checks for ADRs, requirements, links, and traceability."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class GovernanceRequiredFields:
    """Common required governance metadata."""

    metadata_type: str
    doc_id: str
    domain: str
    status: str


@dataclass(frozen=True, slots=True)
class DocGovernanceReport:
    """Governance-document check result."""

    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class GovernanceDocument:
    """Parsed governance document."""

    relative_path: str
    metadata: Mapping[str, object]
    body: str


@dataclass(frozen=True, slots=True)
class GovernanceRecord:
    """Parsed ADR or requirement record."""

    record_id: str
    record_type: str
    domain: str
    status: str
    title: str
    created: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class GovernanceCatalog:
    """Validated ADR and requirement catalog."""

    root: Path
    adrs: tuple[GovernanceRecord, ...]
    requirements: tuple[GovernanceRecord, ...]
    failures: tuple[str, ...]


ADR_STATUSES = ("proposed", "accepted", "deprecated", "superseded")
REQUIREMENT_STATUSES = ("draft", "active", "implemented", "deprecated", "superseded")
DOC_SUFFIXES = (".md", ".html")
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
LOCAL_REF_KINDS = {"local_file", "local_pytest", "design_doc", "schema", "contract"}
EXTERNAL_REF_KINDS = {"external_test", "external_pytest", "external_cpp_test", "external_source"}
ISSUE_REF_RE = re.compile(r"^(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#\d+$")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r"\bhref=[\"']([^\"']+)[\"']")
STALE_ACCEPTED_ADR_PATTERNS = (
    re.compile(r"\bbefore\s+v\d+(?:\.\d+)*\s+exit\b", re.IGNORECASE),
    re.compile(r"\bv\d+(?:\.\d+)*\s+(?:release\s+)?exit\b", re.IGNORECASE),
    re.compile(r"^\s*#+\s+open questions?\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*#+\s+todo\b", re.IGNORECASE | re.MULTILINE),
)


def check_adr_policy(root: Path) -> DocGovernanceReport:
    """Check ADR documents for canonical metadata and standing-decision hygiene."""
    resolved_root = root.resolve()
    failures: list[str] = []
    adrs = _load_records_for_type(resolved_root, "adr", ADR_STATUSES, failures)
    return _report("ADR", adrs, failures)


def check_requirement_policy(root: Path) -> DocGovernanceReport:
    """Check requirement documents for canonical metadata and verification traces."""
    resolved_root = root.resolve()
    failures: list[str] = []
    requirements = _load_records_for_type(
        resolved_root,
        "requirement",
        REQUIREMENT_STATUSES,
        failures,
    )
    return _report("requirement", requirements, failures)


def load_governance_catalog(root: Path) -> GovernanceCatalog:
    """Load and validate ADR and requirement governance documents."""
    resolved_root = root.resolve()
    failures: list[str] = []
    adrs = _load_records_for_type(resolved_root, "adr", ADR_STATUSES, failures)
    requirements = _load_records_for_type(
        resolved_root,
        "requirement",
        REQUIREMENT_STATUSES,
        failures,
    )
    return GovernanceCatalog(
        resolved_root,
        tuple(sorted(adrs, key=lambda item: item.record_id)),
        tuple(sorted(requirements, key=lambda item: item.record_id)),
        tuple(failures),
    )


def check_traceability_policy(root: Path) -> DocGovernanceReport:
    """Check typed traceability references in governance docs."""
    failures: list[str] = []
    docs = _governance_documents(root)
    for doc in docs:
        _validate_string_ref_array(doc, "issue_refs", failures)
        _validate_string_ref_array(doc, "plan_refs", failures)
        _validate_string_ref_array(doc, "adr_refs", failures)
        _validate_string_ref_array(doc, "requirement_refs", failures)
        _validate_path_ref_array(root, doc, "design_refs", failures)
        _validate_path_ref_array(root, doc, "schema_refs", failures)
        _validate_typed_refs(root, doc, "verification_refs", failures)
        _validate_typed_refs(root, doc, "implementation_refs", failures)
    return _report("traceability", docs, failures)


def check_link_policy(root: Path) -> DocGovernanceReport:
    """Check local documentation links in Markdown and HTML documents."""
    from wn_dev_std.governance_links import check_governance_link_resolution

    failures: list[str] = []
    docs = _documentation_files(root)
    for path in docs:
        _validate_document_links(root, path, failures)
    link_report = check_governance_link_resolution(root)
    for issue in link_report.issues:
        failures.append(f"{issue.relative_path}: {issue.message}")
    return _report("documentation link", docs, failures)


def _load_records_for_type(
    root: Path,
    expected_type: str,
    statuses: Sequence[str],
    failures: list[str],
) -> list[GovernanceRecord]:
    records: list[GovernanceRecord] = []
    directory_name = "adr" if expected_type == "adr" else "requirements"
    for path in _candidate_governance_paths(root, directory_name):
        relative_path = path.relative_to(root).as_posix()
        doc = _parse_document(root, path)
        if doc is None:
            type_label = expected_type_label(expected_type)
            failures.append(f"{relative_path}: {type_label} missing TOML front matter")
            continue
        before = len(failures)
        _validate_governance_doc_common(doc, expected_type, statuses, failures)
        if expected_type == "adr" and _string_value(doc.metadata, "status") == "accepted":
            _validate_accepted_adr_body(doc, failures)
        if expected_type == "requirement":
            _validate_requirement_verification(root, doc, failures)
        if len(failures) == before:
            records.append(_record_from_document(doc, expected_type))
    return records


def expected_type_label(expected_type: str) -> str:
    """Return user-facing governance type label."""
    return "ADR" if expected_type == "adr" else "requirement"


def _candidate_governance_paths(root: Path, directory_name: str) -> tuple[Path, ...]:
    if not (root / "docs").exists():
        return ()
    paths: list[Path] = []
    for path in sorted((root / "docs").rglob("*.md")):
        if _is_excluded(path, root):
            continue
        if path.name.lower() == "readme.md":
            continue
        if directory_name in {part.lower() for part in path.parts}:
            paths.append(path)
    return tuple(paths)


def _record_from_document(
    doc: GovernanceDocument,
    expected_type: str,
) -> GovernanceRecord:
    return GovernanceRecord(
        _string_value(doc.metadata, "id"),
        expected_type,
        _string_value(doc.metadata, "domain"),
        _string_value(doc.metadata, "status"),
        _string_value(doc.metadata, "title"),
        _created_text(doc.metadata),
        doc.relative_path,
    )


def _created_text(metadata: Mapping[str, object]) -> str:
    value = metadata.get("created")
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, datetime | date):
        return value.isoformat()
    return ""


def _governance_documents(root: Path) -> tuple[GovernanceDocument, ...]:
    docs: list[GovernanceDocument] = []
    if not (root / "docs").exists():
        return ()
    for path in sorted((root / "docs").rglob("*.md")):
        if _is_excluded(path, root):
            continue
        parsed = _parse_document(root, path)
        if parsed is None:
            continue
        if _string_value(parsed.metadata, "type") in {"adr", "requirement", "plan"}:
            docs.append(parsed)
    return tuple(docs)


def _documentation_files(root: Path) -> tuple[Path, ...]:
    if not (root / "docs").exists():
        return ()
    docs: list[Path] = []
    for suffix in DOC_SUFFIXES:
        for path in (root / "docs").rglob(f"*{suffix}"):
            if not _is_excluded(path, root):
                docs.append(path)
    return tuple(sorted(docs))


def _parse_document(root: Path, path: Path) -> GovernanceDocument | None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            raw_front_matter = "\n".join(lines[1:index])
            try:
                parsed = tomllib.loads(raw_front_matter)
            except tomllib.TOMLDecodeError:
                return None
            return GovernanceDocument(
                path.relative_to(root).as_posix(),
                cast(Mapping[str, object], parsed),
                "\n".join(lines[index + 1 :]).strip(),
            )
    return None


def _validate_governance_doc_common(
    doc: GovernanceDocument,
    expected_type: str,
    statuses: Sequence[str],
    failures: list[str],
) -> None:
    fields = _required_governance_fields(doc, failures)
    _required_string(doc, "title", failures)
    _required_created(doc, failures)
    _validate_doc_type(doc, fields.metadata_type, expected_type, failures)
    _validate_doc_status(doc, fields.status, statuses, failures)
    _validate_doc_id_and_filename(doc, fields.doc_id, fields.domain, expected_type, failures)
    _validate_domain_matches_path(doc, fields.domain, expected_type, failures)


def _required_governance_fields(
    doc: GovernanceDocument,
    failures: list[str],
) -> GovernanceRequiredFields:
    return GovernanceRequiredFields(
        _required_string(doc, "type", failures),
        _required_string(doc, "id", failures),
        _required_string(doc, "domain", failures),
        _required_string(doc, "status", failures),
    )


def _validate_doc_type(
    doc: GovernanceDocument,
    metadata_type: str,
    expected_type: str,
    failures: list[str],
) -> None:
    if metadata_type and metadata_type != expected_type:
        failures.append(
            f"{doc.relative_path}: expected type {expected_type!r}, got {metadata_type!r}"
        )


def _validate_doc_status(
    doc: GovernanceDocument,
    status: str,
    statuses: Sequence[str],
    failures: list[str],
) -> None:
    if status and status not in statuses:
        failures.append(
            f"{doc.relative_path}: invalid status {status!r}; expected " + ", ".join(statuses)
        )


def _validate_doc_id_and_filename(
    doc: GovernanceDocument,
    doc_id: str,
    domain: str,
    expected_type: str,
    failures: list[str],
) -> None:
    if domain and doc_id:
        type_token = "req" if expected_type == "requirement" else expected_type
        expected_prefix = f"{domain}-{type_token}-"
        if not doc_id.startswith(expected_prefix):
            failures.append(f"{doc.relative_path}: id must start with {expected_prefix!r}")
    if doc_id and not Path(doc.relative_path).stem.startswith(doc_id):
        failures.append(f"{doc.relative_path}: filename must start with id {doc_id!r}")


def _validate_domain_matches_path(
    doc: GovernanceDocument,
    domain: str,
    expected_type: str,
    failures: list[str],
) -> None:
    if not domain:
        return
    parts = Path(doc.relative_path).parts
    if len(parts) < 3 or parts[0] != "docs":
        failures.append(f"{doc.relative_path}: governance document must live under docs/")
        return
    expected_dir = "adr" if expected_type == "adr" else "requirements"
    path_domain = _path_domain_before(parts, expected_dir)
    if path_domain is None:
        failures.append(f"{doc.relative_path}: expected docs/<domain>/{expected_dir}/ layout")
        return
    if path_domain != domain:
        failures.append(
            f"{doc.relative_path}: domain {domain!r} does not match path domain {path_domain!r}"
        )


def _path_domain_before(parts: Sequence[str], directory_name: str) -> str | None:
    try:
        type_index = parts.index(directory_name)
    except ValueError:
        return None
    if type_index <= 1:
        return None
    return parts[type_index - 1]


def _validate_accepted_adr_body(doc: GovernanceDocument, failures: list[str]) -> None:
    for pattern in STALE_ACCEPTED_ADR_PATTERNS:
        if pattern.search(doc.body):
            failures.append(
                f"{doc.relative_path}: accepted ADR contains stale active-work language"
            )
            return


def _validate_requirement_verification(
    root: Path,
    doc: GovernanceDocument,
    failures: list[str],
) -> None:
    status = _string_value(doc.metadata, "status")
    if status not in {"active", "implemented"}:
        return
    refs = _table_array(doc.metadata.get("verification_refs"))
    if refs:
        _validate_typed_refs(root, doc, "verification_refs", failures)
        return
    issue_refs = _string_array(doc.metadata.get("issue_refs"))
    verification_status = _string_value(doc.metadata, "verification_status")
    if verification_status == "unverified" and issue_refs:
        return
    failures.append(
        f"{doc.relative_path}: active/implemented requirement needs verification_refs "
        'or verification_status = "unverified" with issue_refs'
    )


def _validate_string_ref_array(
    doc: GovernanceDocument,
    key: str,
    failures: list[str],
) -> None:
    value = doc.metadata.get(key)
    if value is None:
        return
    items = _string_array(value)
    if not items:
        failures.append(f"{doc.relative_path}: {key} must be a string array")
        return
    if key == "issue_refs":
        for item in items:
            if not ISSUE_REF_RE.fullmatch(item):
                failures.append(f"{doc.relative_path}: invalid issue ref {item!r}")


def _validate_path_ref_array(
    root: Path,
    doc: GovernanceDocument,
    key: str,
    failures: list[str],
) -> None:
    value = doc.metadata.get(key)
    if value is None:
        return
    items = _string_array(value)
    if not items:
        failures.append(f"{doc.relative_path}: {key} must be a string array")
        return
    for item in items:
        if _is_external_link(item):
            continue
        target = _path_ref_target(root, item)
        if not _is_within_root(root, target):
            failures.append(f"{doc.relative_path}: {key} target escapes repository root {item!r}")
            continue
        if not target.exists():
            failures.append(f"{doc.relative_path}: missing {key} target {item!r}")


def _validate_typed_refs(
    root: Path,
    doc: GovernanceDocument,
    key: str,
    failures: list[str],
) -> None:
    value = doc.metadata.get(key)
    if value is None:
        return
    refs = _table_array(value)
    if not refs:
        failures.append(f"{doc.relative_path}: {key} must be an array of tables")
        return
    for index, ref in enumerate(refs, start=1):
        _validate_one_typed_ref(root, doc, key, index, ref, failures)


def _validate_one_typed_ref(
    root: Path,
    doc: GovernanceDocument,
    key: str,
    index: int,
    ref: Mapping[str, object],
    failures: list[str],
) -> None:
    label = f"{doc.relative_path}: {key}[{index}]"
    kind = _string_value(ref, "kind")
    target = _string_value(ref, "target")
    repo = _string_value(ref, "repo")
    if not kind:
        failures.append(f"{label}: missing kind")
    if not target:
        failures.append(f"{label}: missing target")
    if kind in LOCAL_REF_KINDS:
        _validate_local_typed_ref(root, label, kind, target, failures)
    elif kind in EXTERNAL_REF_KINDS:
        _validate_external_typed_ref(label, repo, failures)
    elif kind:
        failures.append(f"{label}: unknown kind {kind!r}")


def _validate_external_typed_ref(
    label: str,
    repo: str,
    failures: list[str],
) -> None:
    if not repo:
        failures.append(f"{label}: external refs require repo")


def _validate_local_typed_ref(
    root: Path,
    label: str,
    kind: str,
    target: str,
    failures: list[str],
) -> None:
    if not target:
        return
    path_text = target.split("::", 1)[0]
    path = _path_ref_target(root, path_text)
    if not _is_within_root(root, path):
        failures.append(f"{label}: local target escapes repository root {target!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")
    if kind == "local_pytest" and "::" not in target:
        failures.append(f"{label}: local_pytest target should include :: test selector")


def _validate_document_links(root: Path, path: Path, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    relative_path = path.relative_to(root).as_posix()
    links = list(MARKDOWN_LINK_RE.findall(text)) + list(HTML_HREF_RE.findall(text))
    for raw_link in links:
        target = _local_document_link_target(path, raw_link)
        if target is None:
            continue
        target_path, link = target
        _validate_generated_governance_link_policy(path, relative_path, link, target_path, failures)
        _validate_local_document_link(root, relative_path, link, target_path, failures)


def _local_document_link_target(
    path: Path,
    raw_link: str,
) -> tuple[Path, str] | None:
    link = raw_link.strip()
    if not link or _is_external_link(link) or link.startswith("#"):
        return None
    target_text = link.split("#", 1)[0].split("?", 1)[0]
    if not target_text:
        return None
    return (path.parent / target_text).resolve(), link


def _validate_local_document_link(
    root: Path,
    relative_path: str,
    link: str,
    target: Path,
    failures: list[str],
) -> None:
    try:
        target.relative_to(root.resolve())
    except ValueError:
        failures.append(f"{relative_path}: link escapes repository root: {link!r}")
        return
    if not target.exists():
        failures.append(f"{relative_path}: missing local link target {link!r}")


def _validate_generated_governance_link_policy(
    source_path: Path,
    relative_path: str,
    link: str,
    target: Path,
    failures: list[str],
) -> None:
    if source_path.suffix.lower() != ".html":
        return
    if target.suffix.lower() != ".md":
        return
    if not _is_raw_governance_source_path(target):
        return
    failures.append(
        f"{relative_path}: HTML docs must link generated governance pages, not raw source {link!r}"
    )


def _is_raw_governance_source_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return bool(parts.intersection({"adr", "requirements"}))


def _required_string(doc: GovernanceDocument, key: str, failures: list[str]) -> str:
    value = _string_value(doc.metadata, key)
    if value:
        return value
    failures.append(f"{doc.relative_path}: missing {key}")
    return ""


def _required_created(doc: GovernanceDocument, failures: list[str]) -> None:
    value = doc.metadata.get("created")
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, datetime | date):
        return
    failures.append(f"{doc.relative_path}: missing created")


def _string_value(metadata: Mapping[str, object], key: str) -> str:
    value = metadata.get(key)
    return value.strip() if isinstance(value, str) else ""


def _string_array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item.strip():
            return ()
        items.append(item.strip())
    return tuple(items)


def _table_array(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    items: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            return ()
        items.append(cast(Mapping[str, object], item))
    return tuple(items)


def _path_ref_target(root: Path, item: str) -> Path:
    normalized = item.replace("\\", "/").split("#", 1)[0].split("?", 1)[0]
    return (root / normalized).resolve()


def _is_within_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_external_link(link: str) -> bool:
    lowered = link.lower()
    return (
        "://" in lowered
        or lowered.startswith("mailto:")
        or lowered.startswith("tel:")
        or lowered.startswith("urn:")
    )


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return bool(EXCLUDED_PARTS.intersection(parts))


def _report(
    label: str,
    docs: Sequence[object],
    failures: Sequence[str],
    limit: int = 10,
) -> DocGovernanceReport:
    if failures:
        shown = list(failures[:limit])
        suffix = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
        detail = f"{label} governance failures: " + "; ".join(shown) + suffix
        return DocGovernanceReport(False, detail)
    if not docs:
        return DocGovernanceReport(True, f"no {label} documents found")
    return DocGovernanceReport(True, f"{len(docs)} {label} document(s) passed governance checks")
