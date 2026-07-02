"""Governed surface traceability checks."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class SurfaceGovernanceReport:
    """Governed surface check result."""

    passed: bool
    detail: str


DEFAULT_SURFACE_PATH = Path("docs/governance/governed_surfaces.toml")
DEFAULT_DOMAIN_REGISTRY_PATH = Path("docs/governance/domain_registry.toml")
ACTIVE_SURFACE_STATUSES = {"active", "implemented"}
EXCEPTION_STATUSES_REQUIRING_ISSUES = {"deferred", "missing_capability"}
LOCAL_REF_KINDS = {"local_file", "local_pytest", "fixture_file"}
EXTERNAL_REF_KINDS = {
    "external_source",
    "external_test",
    "external_pytest",
    "external_cpp_test",
}


def check_surface_governance_policy(root: Path) -> SurfaceGovernanceReport:
    """Check optional governed surface manifests."""
    resolved_root = root.resolve()
    manifest_path = resolved_root / DEFAULT_SURFACE_PATH
    if not manifest_path.exists():
        return SurfaceGovernanceReport(True, "no governed surface manifest found")
    payload = _load_toml(manifest_path)
    failures: list[str] = []
    domain_ids = _domain_ids(resolved_root)
    surfaces = _table_array(payload.get("surfaces"))
    exceptions = _table_array(payload.get("exceptions"))
    exception_surface_refs = _validate_exceptions(
        resolved_root,
        manifest_path,
        exceptions,
        failures,
    )
    _validate_surfaces(
        resolved_root, manifest_path, surfaces, domain_ids, exception_surface_refs, failures
    )
    if failures:
        return SurfaceGovernanceReport(False, _summarize_failures("surface", failures))
    return SurfaceGovernanceReport(
        True,
        f"{len(surfaces)} governed surface(s) passed governance checks",
    )


def _validate_surfaces(
    root: Path,
    manifest_path: Path,
    surfaces: tuple[Mapping[str, object], ...],
    domain_ids: set[str] | None,
    exception_surface_refs: set[str],
    failures: list[str],
) -> None:
    if not surfaces:
        failures.append(f"{_rel(root, manifest_path)}: missing [[surfaces]] entries")
        return
    seen: set[str] = set()
    for index, surface in enumerate(surfaces, start=1):
        label = f"{_rel(root, manifest_path)}: surfaces[{index}]"
        surface_id = _required_string(surface, "id", label, failures)
        domain = _required_string(surface, "domain", label, failures)
        _required_string(surface, "kind", label, failures)
        status = _required_string(surface, "status", label, failures)
        _required_string(surface, "purpose", label, failures)
        _validate_surface_identity(label, surface_id, seen, failures)
        _validate_surface_domain(label, domain, domain_ids, failures)
        _validate_reference_list(root, label, "implementation_refs", surface, failures)
        _validate_verification_refs(root, label, surface, failures)
        _validate_fixture_refs(root, label, surface, failures)
        _validate_active_surface_coverage(
            label, surface_id, status, surface, exception_surface_refs, failures
        )


def _validate_surface_identity(
    label: str,
    surface_id: str,
    seen: set[str],
    failures: list[str],
) -> None:
    if not surface_id:
        return
    if surface_id in seen:
        failures.append(f"{label}: duplicate surface id {surface_id!r}")
    seen.add(surface_id)


def _validate_surface_domain(
    label: str,
    domain: str,
    domain_ids: set[str] | None,
    failures: list[str],
) -> None:
    if domain and domain_ids is not None and domain not in domain_ids:
        failures.append(f"{label}: unknown domain {domain!r}")


def _validate_active_surface_coverage(
    label: str,
    surface_id: str,
    status: str,
    surface: Mapping[str, object],
    exception_surface_refs: set[str],
    failures: list[str],
) -> None:
    if status not in ACTIVE_SURFACE_STATUSES:
        return
    verification_refs = _table_array(surface.get("verification_refs"))
    has_exception = bool(surface_id and surface_id in exception_surface_refs)
    if not verification_refs and not has_exception:
        failures.append(f"{label}: active/implemented surface needs verification_refs or exception")


def _validate_reference_list(
    root: Path,
    label: str,
    key: str,
    surface: Mapping[str, object],
    failures: list[str],
) -> None:
    refs = _string_array(surface.get(key))
    if surface.get(key) is not None and not refs:
        failures.append(f"{label}: {key} must be a string array")
        return
    for ref in refs:
        _validate_local_path_ref(root, f"{label}: {key}", ref, failures)


def _validate_verification_refs(
    root: Path,
    label: str,
    surface: Mapping[str, object],
    failures: list[str],
) -> None:
    refs = _table_array(surface.get("verification_refs"))
    if surface.get("verification_refs") is not None and not refs:
        failures.append(f"{label}: verification_refs must be an array of tables")
        return
    for index, ref in enumerate(refs, start=1):
        _validate_one_typed_ref(root, f"{label}: verification_refs[{index}]", ref, failures)


def _validate_fixture_refs(
    root: Path,
    label: str,
    surface: Mapping[str, object],
    failures: list[str],
) -> None:
    refs = _table_array(surface.get("fixture_refs"))
    if surface.get("fixture_refs") is not None and not refs:
        failures.append(f"{label}: fixture_refs must be an array of tables")
        return
    for index, ref in enumerate(refs, start=1):
        _validate_one_typed_ref(root, f"{label}: fixture_refs[{index}]", ref, failures)


def _validate_one_typed_ref(
    root: Path,
    label: str,
    ref: Mapping[str, object],
    failures: list[str],
) -> None:
    kind = _required_string(ref, "kind", label, failures)
    target = _required_string(ref, "target", label, failures)
    _required_string(ref, "coverage_mode", label, failures)
    _required_string(ref, "rationale", label, failures)
    if kind in LOCAL_REF_KINDS:
        _validate_local_typed_ref(root, label, kind, target, failures)
    elif kind in EXTERNAL_REF_KINDS:
        _validate_external_typed_ref(label, ref, failures)
    elif kind:
        failures.append(f"{label}: unknown kind {kind!r}")


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
    path = (root / path_text).resolve()
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")
    if kind == "local_pytest" and "::" not in target:
        failures.append(f"{label}: local_pytest target should include :: test selector")


def _validate_external_typed_ref(
    label: str,
    ref: Mapping[str, object],
    failures: list[str],
) -> None:
    if not _string_value(ref.get("repo")):
        failures.append(f"{label}: external refs require repo")


def _validate_local_path_ref(
    root: Path,
    label: str,
    target: str,
    failures: list[str],
) -> None:
    if not target:
        return
    path_text = target.replace("\\", "/").split("#", 1)[0].split("?", 1)[0]
    path = (root / path_text).resolve()
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")


def _validate_exceptions(
    root: Path,
    manifest_path: Path,
    exceptions: tuple[Mapping[str, object], ...],
    failures: list[str],
) -> set[str]:
    refs: set[str] = set()
    for index, exception in enumerate(exceptions, start=1):
        label = f"{_rel(root, manifest_path)}: exceptions[{index}]"
        _required_string(exception, "id", label, failures)
        surface_ref = _required_string(exception, "surface_ref", label, failures)
        status = _required_string(exception, "status", label, failures)
        _required_string(exception, "rationale", label, failures)
        if status in EXCEPTION_STATUSES_REQUIRING_ISSUES:
            _validate_issue_refs(exception, label, failures)
        if surface_ref:
            refs.add(surface_ref)
    return refs


def _validate_issue_refs(
    exception: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    issue_refs = _string_array(exception.get("issue_refs"))
    if not issue_refs:
        failures.append(f"{label}: status requires issue_refs")


def _domain_ids(root: Path) -> set[str] | None:
    registry_path = root / DEFAULT_DOMAIN_REGISTRY_PATH
    if not registry_path.exists():
        return None
    payload = _load_toml(registry_path)
    domains = _table_array(payload.get("domains"))
    return {domain_id for domain in domains if (domain_id := _string_value(domain.get("id")))}


def _load_toml(path: Path) -> Mapping[str, object]:
    with path.open("rb") as handle:
        return cast(Mapping[str, object], tomllib.load(handle))


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
        if isinstance(item, dict):
            items.append(cast(Mapping[str, object], item))
        else:
            return ()
    return tuple(items)


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _summarize_failures(label: str, failures: Sequence[str], limit: int = 10) -> str:
    shown = list(failures[:limit])
    suffix = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
    return f"{label} governance failures: " + "; ".join(shown) + suffix
