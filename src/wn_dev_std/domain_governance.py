"""Domain registry and file-ownership governance checks."""

from __future__ import annotations

import fnmatch
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.doc_governance import load_governance_catalog


@dataclass(frozen=True, slots=True)
class DomainGovernanceReport:
    """Domain governance check result."""

    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class DomainRegistry:
    """Parsed domain registry."""

    path: Path
    domains: tuple[Mapping[str, object], ...]
    file_groups: tuple[Mapping[str, object], ...]
    owned_roots: tuple[str, ...]
    ignore: tuple[str, ...]


DOMAIN_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DEFAULT_REGISTRY_PATH = Path("docs/governance/domain_registry.toml")
DEFAULT_IGNORES = (
    ".git/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".venv/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "node_modules/**",
)


def check_domain_governance_policy(root: Path) -> DomainGovernanceReport:
    """Check optional docs domain registry and file ownership coverage."""
    resolved_root = root.resolve()
    registry = _load_registry(resolved_root)
    if registry is None:
        return DomainGovernanceReport(True, "no domain registry found")
    failures: list[str] = []
    domain_ids = _validate_domains(resolved_root, registry, failures)
    matched_files = _validate_file_groups(resolved_root, registry, domain_ids, failures)
    _validate_owned_file_coverage(resolved_root, registry, matched_files, failures)
    _validate_governance_doc_domains(resolved_root, domain_ids, failures)
    if failures:
        return DomainGovernanceReport(False, _summarize_failures("domain", failures))
    return DomainGovernanceReport(True, f"{len(domain_ids)} domain(s) passed governance checks")


def _load_registry(root: Path) -> DomainRegistry | None:
    path = root / DEFAULT_REGISTRY_PATH
    if not path.exists():
        return None
    with path.open("rb") as handle:
        payload = cast(Mapping[str, object], tomllib.load(handle))
    config = _mapping(payload.get("domain_governance"))
    domains = _mapping_tuple(payload.get("domains"))
    file_groups = _mapping_tuple(payload.get("file_groups"))
    owned_roots = _string_tuple(config.get("owned_roots") if config else None)
    ignore = _string_tuple(config.get("ignore") if config else None)
    return DomainRegistry(path, domains, file_groups, owned_roots, ignore)


def _validate_domains(
    root: Path,
    registry: DomainRegistry,
    failures: list[str],
) -> set[str]:
    domain_ids: set[str] = set()
    if not registry.domains:
        failures.append(f"{_rel(root, registry.path)}: missing [[domains]] entries")
        return domain_ids
    for index, domain in enumerate(registry.domains, start=1):
        label = f"{_rel(root, registry.path)}: domains[{index}]"
        domain_id = _required_string(domain, "id", label, failures)
        _required_string(domain, "title", label, failures)
        _required_string(domain, "status", label, failures)
        _required_string(domain, "purpose", label, failures)
        if domain_id and not DOMAIN_ID_RE.fullmatch(domain_id):
            failures.append(f"{label}: invalid id {domain_id!r}")
        if domain_id in domain_ids:
            failures.append(f"{label}: duplicate domain id {domain_id!r}")
        if domain_id:
            domain_ids.add(domain_id)
        _validate_domain_html(root, registry, domain, label, failures)
    return domain_ids


def _validate_domain_html(
    root: Path,
    registry: DomainRegistry,
    domain: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    domain_id = _string_value(domain.get("id"))
    html_path = _string_value(domain.get("html"))
    if not html_path:
        failures.append(f"{label}: missing html")
        return
    path = (root / html_path).resolve()
    if not _is_within_root(root, path):
        failures.append(f"{label}: html target escapes repository root {html_path!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing html target {html_path!r}")
        return
    text = path.read_text(encoding="utf-8")
    if f'data-domain="{domain_id}"' not in text:
        failures.append(f"{_rel(root, path)}: missing data-domain={domain_id!r}")
    if "data-domain-status=" not in text:
        failures.append(f"{_rel(root, path)}: missing data-domain-status")
    if _rel(root, registry.path) not in text:
        failures.append(f"{_rel(root, path)}: missing registry source reference")


def _validate_file_groups(
    root: Path,
    registry: DomainRegistry,
    domain_ids: set[str],
    failures: list[str],
) -> set[str]:
    matched_files: set[str] = set()
    if not registry.file_groups:
        failures.append(f"{_rel(root, registry.path)}: missing [[file_groups]] entries")
        return matched_files
    for index, group in enumerate(registry.file_groups, start=1):
        label = f"{_rel(root, registry.path)}: file_groups[{index}]"
        matched_files.update(_validate_one_file_group(root, group, label, domain_ids, failures))
    return matched_files


def _validate_one_file_group(
    root: Path,
    group: Mapping[str, object],
    label: str,
    domain_ids: set[str],
    failures: list[str],
) -> set[str]:
    primary = _required_string(group, "primary_domain", label, failures)
    if primary and primary not in domain_ids:
        failures.append(f"{label}: unknown primary_domain {primary!r}")
    _validate_supporting_domains(group, label, domain_ids, failures)
    paths = _string_tuple(group.get("paths"))
    if not paths:
        failures.append(f"{label}: missing paths")
        return set()
    group_matches = _matched_group_files(root, paths)
    if not group_matches and group.get("pending") is not True:
        failures.append(f"{label}: paths do not match any files")
    return group_matches


def _validate_supporting_domains(
    group: Mapping[str, object],
    label: str,
    domain_ids: set[str],
    failures: list[str],
) -> None:
    for domain_id in _string_tuple(group.get("supporting_domains")):
        if domain_id not in domain_ids:
            failures.append(f"{label}: unknown supporting_domain {domain_id!r}")


def _validate_owned_file_coverage(
    root: Path,
    registry: DomainRegistry,
    matched_files: set[str],
    failures: list[str],
) -> None:
    if not registry.owned_roots:
        failures.append(f"{_rel(root, registry.path)}: missing domain_governance.owned_roots")
        return
    ignored = DEFAULT_IGNORES + registry.ignore
    unowned = [
        path
        for path in _owned_files(root, registry.owned_roots, ignored)
        if path not in matched_files
    ]
    if unowned:
        shown = ", ".join(unowned[:10])
        suffix = "" if len(unowned) <= 10 else f"; +{len(unowned) - 10} more"
        failures.append(
            f"{_rel(root, registry.path)}: unowned files under owned_roots: {shown}{suffix}"
        )


def _validate_governance_doc_domains(
    root: Path,
    domain_ids: set[str],
    failures: list[str],
) -> None:
    catalog = load_governance_catalog(root)
    for record in catalog.adrs + catalog.requirements:
        if record.domain not in domain_ids:
            failures.append(
                f"{record.relative_path}: domain {record.domain!r} is not in domain registry"
            )


def _matched_group_files(root: Path, patterns: tuple[str, ...]) -> set[str]:
    files = _all_files(root)
    return {
        file_path
        for file_path in files
        if any(_path_matches(file_path, pattern) for pattern in patterns)
    }


def _owned_files(root: Path, owned_roots: tuple[str, ...], ignore: tuple[str, ...]) -> list[str]:
    files: list[str] = []
    for owned_root in owned_roots:
        base = root / owned_root
        if not base.exists():
            continue
        paths = (
            [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        )
        for path in paths:
            relative = _rel(root, path)
            if not any(_path_matches(relative, pattern) for pattern in ignore):
                files.append(relative)
    return files


def _all_files(root: Path) -> list[str]:
    return [_rel(root, path) for path in sorted(root.rglob("*")) if path.is_file()]


def _path_matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/").strip("/")
    return fnmatch.fnmatchcase(path, normalized)


def _required_string(
    metadata: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> str:
    value = _string_value(metadata.get(key))
    if value:
        return value
    failures.append(f"{label}: missing {key}")
    return ""


def _string_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return tuple(items)


def _mapping(value: object) -> Mapping[str, object] | None:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else None


def _mapping_tuple(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    items: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if isinstance(item, dict):
            items.append(cast(Mapping[str, object], item))
    return tuple(items)


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _is_within_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _summarize_failures(label: str, failures: list[str], limit: int = 10) -> str:
    shown = failures[:limit]
    suffix = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
    return f"{label} governance failures: " + "; ".join(shown) + suffix
