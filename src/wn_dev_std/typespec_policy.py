"""Cross-cutting TypeSpec contract-unit audit policy."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks_types import CheckResult
from wn_dev_std.policy_paths import declared_path as _declared_path
from wn_dev_std.policy_paths import is_within as _within

UNIT_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
EXACT_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
PROJECTION_KINDS = {"json-schema", "openapi", "python", "rust", "typescript", "other"}
PROJECTION_SUPPORT = {"supported", "experimental", "extension"}
COMPATIBILITY_MODES = {"versioned", "internal", "upstream"}
EXCEPTION_KINDS = {
    "upstream-authority",
    "unsupported-construct",
    "lossy-projection",
    "legacy-migration",
}


def check_typespec_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> tuple[CheckResult, ...]:
    """Validate declared TypeSpec contract units without executing project commands."""
    if config is None or "contracts" not in config:
        return ()
    contracts = _mapping(config.get("contracts"))
    if contracts is None:
        return (
            CheckResult(
                "TypeSpec contract units",
                False,
                "contracts must be a table",
                "contracts",
            ),
        )
    declaration_failures: list[str] = []
    units = _mapping_list(contracts.get("units"), "contracts.units", declaration_failures)
    if not units:
        detail = "[contracts] requires at least one [[contracts.units]] declaration"
        if declaration_failures:
            detail = "; ".join((*declaration_failures, detail))
        return (
            CheckResult(
                "TypeSpec contract units",
                False,
                detail,
                "contracts",
            ),
        )

    toolchain_failures: list[str] = []
    projection_failures: list[str] = []
    signoff_failures: list[str] = []
    seen_ids: set[str] = set()
    for index, unit in enumerate(units):
        label = _unit_label(unit, index)
        _check_declaration(root, unit, label, seen_ids, declaration_failures)
        _check_toolchain(root, unit, label, toolchain_failures)
        _check_projections(root, unit, label, projection_failures)
        _check_signoff(unit, label, signoff_failures)

    return (
        _result("TypeSpec contract units", units, declaration_failures),
        _result("TypeSpec toolchain", units, toolchain_failures),
        _result("TypeSpec projections", units, projection_failures),
        _result("TypeSpec signoff", units, signoff_failures),
    )


def _check_declaration(
    root: Path,
    unit: Mapping[str, object],
    label: str,
    seen_ids: set[str],
    failures: list[str],
) -> None:
    _check_unit_identity(unit, label, seen_ids, failures)
    _check_unit_authority(unit, label, failures)

    unit_root = _declared_path(root, unit.get("root"), f"{label} root", failures, directory=True)
    entrypoint = _declared_path(root, unit.get("entrypoint"), f"{label} entrypoint", failures)
    _declared_path(root, unit.get("config"), f"{label} config", failures)
    _declared_path(root, unit.get("generated_policy"), f"{label} generated_policy", failures)
    if unit_root is not None and entrypoint is not None and not _within(unit_root, entrypoint):
        failures.append(f"{label} entrypoint must be inside its declared root")
    _check_exceptions(unit, label, failures)


def _check_unit_identity(
    unit: Mapping[str, object],
    label: str,
    seen_ids: set[str],
    failures: list[str],
) -> None:
    unit_id = _string(unit.get("id"))
    if unit_id is None or UNIT_ID_RE.fullmatch(unit_id) is None:
        failures.append(f"{label} id must match {UNIT_ID_RE.pattern}")
    elif unit_id in seen_ids:
        failures.append(f"{label} duplicates contract unit id {unit_id!r}")
    else:
        seen_ids.add(unit_id)


def _check_unit_authority(
    unit: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    if _string(unit.get("authority")) != "typespec":
        failures.append(f"{label} authority must be 'typespec'")
    compatibility = _string(unit.get("compatibility"))
    if compatibility not in COMPATIBILITY_MODES:
        failures.append(f"{label} compatibility must be versioned, internal, or upstream")


def _check_toolchain(
    root: Path,
    unit: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    manifest = _declared_path(
        root,
        unit.get("toolchain_manifest"),
        f"{label} toolchain_manifest",
        failures,
    )
    _declared_path(root, unit.get("lockfile"), f"{label} lockfile", failures)
    packages = (
        "@typespec/compiler",
        *_string_list(
            unit.get("emitter_packages"),
            f"{label} emitter_packages",
            failures,
        ),
    )
    if manifest is None:
        return
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{label} cannot parse toolchain manifest: {exc}")
        return
    dependencies = _package_dependencies(payload)
    for package in packages:
        version = dependencies.get(package)
        if version is None:
            failures.append(f"{label} toolchain manifest must pin {package}")
        elif EXACT_VERSION_RE.fullmatch(version) is None:
            failures.append(f"{label} {package} version {version!r} must be exact")


def _check_projections(
    root: Path,
    unit: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    projections = _mapping_list(unit.get("projections"), f"{label} projections", failures)
    if not projections:
        failures.append(f"{label} requires at least one projection")
        return
    kinds: set[str] = set()
    for index, projection in enumerate(projections):
        _check_projection(root, projection, label, index, kinds, failures)


def _check_projection(
    root: Path,
    projection: Mapping[str, object],
    unit_label: str,
    index: int,
    kinds: set[str],
    failures: list[str],
) -> None:
    label = f"{unit_label} projection[{index}]"
    kind = _string(projection.get("kind"))
    if kind not in PROJECTION_KINDS:
        failures.append(f"{label} has unsupported kind {kind!r}")
    elif kind in kinds:
        failures.append(f"{unit_label} duplicates projection kind {kind!r}")
    else:
        kinds.add(kind)
    support = _string(projection.get("support"))
    if support not in PROJECTION_SUPPORT:
        failures.append(f"{label} has unsupported support level {support!r}")
    _declared_path(root, projection.get("output"), f"{label} output", failures, directory=True)
    if projection.get("required") is not True:
        return
    if support != "supported":
        failures.append(f"{label} required projection must be supported")
    if not _string_list(
        projection.get("consumer_evidence"),
        f"{label} consumer_evidence",
        failures,
    ):
        failures.append(f"{label} requires consumer_evidence")


def _check_signoff(
    unit: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    commands = _mapping(unit.get("commands"))
    if commands is None:
        failures.append(f"{label} requires commands.generate, freshness, and conformance")
        return
    for key in ("generate", "freshness", "conformance"):
        if _string(commands.get(key)) is None:
            failures.append(f"{label} commands.{key} must be a non-empty string")


def _check_exceptions(
    unit: Mapping[str, object],
    label: str,
    failures: list[str],
) -> None:
    exceptions = _mapping_list(unit.get("exceptions"), f"{label} exceptions", failures)
    for index, exception in enumerate(exceptions):
        exception_label = f"{label} exception[{index}]"
        if _string(exception.get("kind")) not in EXCEPTION_KINDS:
            failures.append(f"{exception_label} has unsupported kind")
        for key in ("scope", "rationale", "tracking_ref", "review_when"):
            if _string(exception.get(key)) is None:
                failures.append(f"{exception_label} {key} must be non-empty")


def _result(
    name: str,
    units: Sequence[Mapping[str, object]],
    failures: Sequence[str],
) -> CheckResult:
    if failures:
        return CheckResult(name, False, "; ".join(failures), "contracts")
    return CheckResult(name, True, f"{len(units)} contract unit(s) passed", "contracts")


def _package_dependencies(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    result: dict[str, str] = {}
    package = cast(dict[object, object], payload)
    for key in ("dependencies", "devDependencies"):
        table = package.get(key)
        if not isinstance(table, dict):
            continue
        for name, version in cast(dict[object, object], table).items():
            if isinstance(name, str) and isinstance(version, str):
                result[name] = version
    return result


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, dict):
        return None
    return cast(Mapping[str, object], value)


def _mapping_list(
    value: object,
    label: str,
    failures: list[str],
) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{label} must be an array of tables")
        return ()
    result: list[Mapping[str, object]] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict):
            failures.append(f"{label}[{index}] must be a table")
            continue
        result.append(cast(Mapping[str, object], item))
    return tuple(result)


def _string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_list(value: object, label: str, failures: list[str]) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{label} must be an array of non-empty strings")
        return ()
    result: list[str] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{label}[{index}] must be a non-empty string")
            continue
        result.append(item.strip())
    return tuple(result)


def _unit_label(unit: Mapping[str, object], index: int) -> str:
    return f"contract unit {_string(unit.get('id')) or f'[{index}]'}"
