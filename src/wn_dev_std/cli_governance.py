"""CLI command governance checks."""

from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import cast

from wn_dev_std.json_contracts import validate_json_schema_file
from wn_dev_std.root_discovery import load_pyproject, load_standard_config
from wn_dev_std.typed_refs import (
    is_within_root,
    required_string,
    string_value,
    validate_typed_ref,
)

DEFAULT_A0_MANIFEST_PATH = Path("docs/contracts/command_manifest.a0.json")
DEFAULT_A0_SCHEMA_PATH = Path("docs/contracts/command_manifest.a0.schema.json")
A0_SCHEMA = "wn_dev_std.command_manifest.a0"
ENFORCED_STATUSES = {"public", "experimental", "deprecated"}
COMMAND_STATUSES = {"public", "experimental", "deprecated", "hidden", "deferred"}


@dataclass(frozen=True, slots=True)
class CliGovernanceReport:
    """CLI governance check result."""

    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class CliCommandRecord:
    """Normalized command manifest entry."""

    command_id: str
    path: tuple[str, ...]
    data_command: str
    status: str
    aliases: tuple[tuple[str, ...], ...]
    design_doc: str
    label: str


def check_cli_governance_policy(root: Path) -> CliGovernanceReport:
    """Check optional CLI command governance manifests."""
    resolved_root = root.resolve()
    config = load_standard_config(resolved_root, load_pyproject(resolved_root))
    cli_config = _cli_config(config)
    failures: list[str] = []
    enforced_statuses = _enforced_statuses(cli_config, failures)
    manifest_path = _manifest_path(resolved_root, cli_config, failures)
    if manifest_path is None:
        if failures:
            return CliGovernanceReport(False, _summarize_failures("cli", failures))
        return CliGovernanceReport(True, "no CLI command manifest found")

    payload = _load_json_mapping(manifest_path, failures)
    if payload is None:
        return CliGovernanceReport(False, _summarize_failures("cli", failures))

    manifest_format = _manifest_format(resolved_root, manifest_path, payload, failures)
    if manifest_format == "a0":
        schema_failures = validate_json_schema_file(
            manifest_path,
            _standard_a0_schema_path(),
            instance_label=_rel(resolved_root, manifest_path),
            schema_label=DEFAULT_A0_SCHEMA_PATH.as_posix(),
        )
        failures.extend(schema_failures)
        records = (
            ()
            if schema_failures
            else _validate_a0_manifest(
                resolved_root,
                manifest_path,
                payload,
                enforced_statuses,
                failures,
            )
        )
    elif manifest_format == "v0":
        records = _validate_v0_manifest(resolved_root, manifest_path, payload, failures)
    else:
        records = ()
    _validate_inventory_provider(resolved_root, cli_config, records, enforced_statuses, failures)

    if failures:
        return CliGovernanceReport(False, _summarize_failures("cli", failures))
    return CliGovernanceReport(
        True,
        f"{len(records)} CLI command(s) passed governance checks",
    )


def _validate_a0_manifest(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, object],
    enforced_statuses: set[str],
    failures: list[str],
) -> tuple[CliCommandRecord, ...]:
    commands = _command_items(root, manifest_path, payload, failures)
    seen: set[str] = set()
    records: list[CliCommandRecord] = []
    for index, command in enumerate(commands, start=1):
        label = f"{_rel(root, manifest_path)}: commands[{index}]"
        record = _validate_a0_command(root, label, command, enforced_statuses, seen, failures)
        if record is not None:
            records.append(record)
    return tuple(records)


def _validate_a0_command(
    root: Path,
    label: str,
    command: Mapping[str, object],
    enforced_statuses: set[str],
    seen: set[str],
    failures: list[str],
) -> CliCommandRecord | None:
    path = _canonical_command_path(label, command, seen, failures)
    if path is None:
        return None
    command_id = " ".join(path)
    status = _validate_command_status(label, command, failures)
    _validate_summary(label, command, failures)
    design_doc = _validate_design_doc_field(label, command, failures)
    data_command = string_value(command.get("data_command")) or command_id
    aliases = _alias_paths(command, path)
    _validate_design_ref(root, label, design_doc, data_command, failures)
    _validate_command_refs(root, label, command, failures)
    _validate_command_evidence(label, command, status, enforced_statuses, failures)

    return CliCommandRecord(
        command_id=command_id,
        path=path,
        data_command=data_command,
        status=status or "public",
        aliases=aliases,
        design_doc=design_doc,
        label=label,
    )


def _canonical_command_path(
    label: str,
    command: Mapping[str, object],
    seen: set[str],
    failures: list[str],
) -> tuple[str, ...] | None:
    path = _command_path(command)
    name = string_value(command.get("name"))
    if not path and name:
        path = tuple(name.split())
    if not path:
        failures.append(f"{label}: missing path or name")
        return None
    command_id = " ".join(path)
    if name and name != command_id:
        failures.append(f"{label}: name {name!r} does not match canonical path {command_id!r}")
    if command_id in seen:
        failures.append(f"{label}: duplicate command identity {command_id!r}")
    seen.add(command_id)
    return path


def _validate_command_status(
    label: str,
    command: Mapping[str, object],
    failures: list[str],
) -> str:
    status = _required_non_empty_string(command, "status", label, failures)
    if status and status not in COMMAND_STATUSES:
        failures.append(f"{label}: invalid status {status!r}")
    return status


def _validate_summary(
    label: str,
    command: Mapping[str, object],
    failures: list[str],
) -> None:
    if not _summary(command):
        failures.append(f"{label}: missing summary or description")


def _validate_design_doc_field(
    label: str,
    command: Mapping[str, object],
    failures: list[str],
) -> str:
    return _required_non_empty_string(command, "design_doc", label, failures)


def _validate_command_refs(
    root: Path,
    label: str,
    command: Mapping[str, object],
    failures: list[str],
) -> None:
    _validate_contract_refs(root, label, "config_contracts", command, failures)
    _validate_contract_refs(root, label, "output_contracts", command, failures)
    _validate_typed_ref_array(root, label, "implementation_refs", command, failures)
    _validate_typed_ref_array(root, label, "verification_refs", command, failures)


def _validate_command_evidence(
    label: str,
    command: Mapping[str, object],
    status: str,
    enforced_statuses: set[str],
    failures: list[str],
) -> None:
    if status in enforced_statuses and not _has_evidence_disposition(command):
        failures.append(
            f"{label}: enforced command needs surface_ref, verification_refs, "
            "exception_refs, or issue_refs"
        )
    if status == "deferred" and not _string_array(command.get("issue_refs")):
        failures.append(f"{label}: deferred command requires issue_refs")


def _validate_v0_manifest(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, object],
    failures: list[str],
) -> tuple[CliCommandRecord, ...]:
    commands = _command_items(root, manifest_path, payload, failures)
    records: list[CliCommandRecord] = []
    seen: set[str] = set()
    for index, command in enumerate(commands, start=1):
        label = f"{_rel(root, manifest_path)}: commands[{index}]"
        name = required_string(command, "name", label, failures)
        if not name:
            continue
        if name in seen:
            failures.append(f"{label}: duplicate command identity {name!r}")
        seen.add(name)
        design_doc = required_string(command, "design_doc", label, failures)
        data_command = string_value(command.get("data_command")) or name
        _validate_design_ref(root, label, design_doc, data_command, failures)
        records.append(
            CliCommandRecord(
                command_id=name,
                path=(name,),
                data_command=data_command,
                status=string_value(command.get("status")) or "public",
                aliases=_alias_paths(command, (name,)),
                design_doc=design_doc,
                label=label,
            )
        )
    return tuple(records)


def _validate_design_ref(
    root: Path,
    label: str,
    design_doc: str,
    data_command: str,
    failures: list[str],
) -> None:
    if not design_doc:
        return
    path = (root / design_doc).resolve()
    if not is_within_root(root, path):
        failures.append(f"{label}: design_doc escapes repository root {design_doc!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing design_doc {design_doc!r}")
        return
    text = path.read_text(encoding="utf-8")
    if "data-doc-status=" not in text:
        failures.append(f"{label}: design_doc {design_doc!r} missing data-doc-status")
    if f'data-command="{data_command}"' not in text:
        failures.append(f"{label}: design_doc {design_doc!r} missing data-command={data_command!r}")


def _validate_contract_refs(
    root: Path,
    label: str,
    key: str,
    command: Mapping[str, object],
    failures: list[str],
) -> None:
    value = command.get(key)
    if value is None:
        return
    refs = _mapping_array_field(value, label, key, failures)
    if refs is None:
        return
    for index, ref in enumerate(refs, start=1):
        ref_label = f"{label}: {key}[{index}]"
        path_text = required_string(ref, "path", ref_label, failures)
        required_string(ref, "mode", ref_label, failures)
        _validate_contract_path(root, ref_label, path_text, failures)


def _validate_contract_path(
    root: Path,
    label: str,
    path_text: str,
    failures: list[str],
) -> None:
    path = _resolved_contract_path(root, label, path_text, failures)
    if path is None:
        return
    payload = _load_json_mapping(path, failures)
    if payload is None:
        return
    if not string_value(payload.get("$schema")):
        failures.append(f"{label}: contract {path_text!r} missing $schema")
    if not string_value(payload.get("title")):
        failures.append(f"{label}: contract {path_text!r} missing title")


def _resolved_contract_path(
    root: Path,
    label: str,
    path_text: str,
    failures: list[str],
) -> Path | None:
    if not path_text:
        return None
    configured_path = Path(path_text)
    if configured_path.is_absolute():
        failures.append(f"{label}: contract path must be repository-relative")
        return None
    path = (root / path_text).resolve()
    if not is_within_root(root, path):
        failures.append(f"{label}: contract path escapes repository root {path_text!r}")
        return None
    contracts_root = (root / "docs" / "contracts").resolve()
    if not is_within_root(contracts_root, path):
        failures.append(f"{label}: contract path must live under docs/contracts")
        return None
    if not path.exists():
        failures.append(f"{label}: missing contract {path_text!r}")
        return None
    return path


def _validate_typed_ref_array(
    root: Path,
    label: str,
    key: str,
    command: Mapping[str, object],
    failures: list[str],
) -> None:
    value = command.get(key)
    if value is None:
        return
    refs = _mapping_array_field(value, label, key, failures)
    if refs is None:
        return
    for index, ref in enumerate(refs, start=1):
        validate_typed_ref(root, f"{label}: {key}[{index}]", ref, failures)


def _validate_inventory_provider(
    root: Path,
    cli_config: Mapping[str, object],
    records: tuple[CliCommandRecord, ...],
    enforced_statuses: set[str],
    failures: list[str],
) -> None:
    provider = _mapping_value(cli_config.get("inventory_provider"))
    if provider is None:
        return
    provider_paths = _provider_paths(root, provider, failures)
    if provider_paths is None:
        return
    manifest_paths = _manifest_visible_paths(records, enforced_statuses)
    missing = sorted(_path_text(path) for path in provider_paths - manifest_paths)
    extra = sorted(_path_text(path) for path in manifest_paths - provider_paths)
    if missing:
        failures.append("inventory provider commands missing from manifest: " + ", ".join(missing))
    if extra:
        failures.append("manifest commands missing from inventory provider: " + ", ".join(extra))


def _provider_paths(
    root: Path,
    provider: Mapping[str, object],
    failures: list[str],
) -> set[tuple[str, ...]] | None:
    label = "documentation.cli.inventory_provider"
    kind = string_value(provider.get("kind"))
    if kind == "python_parser":
        return _python_parser_provider_paths(provider, label, failures)
    if kind == "static_json":
        return _static_json_provider_paths(root, provider, label, failures)
    if kind:
        failures.append(f"{label}: unsupported kind {kind!r}")
    else:
        failures.append(f"{label}: missing kind")
    return None


def _python_parser_provider_paths(
    provider: Mapping[str, object],
    label: str,
    failures: list[str],
) -> set[tuple[str, ...]] | None:
    module_name = required_string(provider, "module", label, failures)
    function_name = required_string(provider, "function", label, failures)
    max_depth = _positive_int(provider.get("max_depth"), default=1)
    if not module_name or not function_name:
        return None
    try:
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        parser = cast(Callable[[], object], function)()
    except Exception as exc:  # pragma: no cover - diagnostic path
        failures.append(f"{label}: failed to load python_parser provider: {exc}")
        return None
    if not isinstance(parser, argparse.ArgumentParser):
        failures.append(f"{label}: provider did not return argparse.ArgumentParser")
        return None
    return {
        path
        for path in _parser_command_paths(parser, max_depth=max_depth)
        if len(path) <= max_depth
    }


def _static_json_provider_paths(
    root: Path,
    provider: Mapping[str, object],
    label: str,
    failures: list[str],
) -> set[tuple[str, ...]] | None:
    path_text = required_string(provider, "path", label, failures)
    if not path_text:
        return None
    path = (root / path_text).resolve()
    if not is_within_root(root, path):
        failures.append(f"{label}: static_json path escapes repository root {path_text!r}")
        return None
    payload = _load_json_mapping(path, failures)
    if payload is None:
        return None
    return _static_inventory_paths(payload, label, failures)


def _parser_command_paths(
    parser: argparse.ArgumentParser,
    *,
    max_depth: int,
    prefix: tuple[str, ...] = (),
) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    if len(prefix) >= max_depth:
        return paths
    for action in cast(Sequence[object], parser._actions):
        choices = getattr(action, "choices", None)
        if not isinstance(choices, dict) or not choices:
            continue
        for name, child in cast(Mapping[str, object], choices).items():
            if not name:
                continue
            path = (*prefix, name)
            paths.add(path)
            if isinstance(child, argparse.ArgumentParser):
                paths.update(_parser_command_paths(child, max_depth=max_depth, prefix=path))
        break
    return paths


def _static_inventory_paths(
    payload: Mapping[str, object],
    label: str,
    failures: list[str],
) -> set[tuple[str, ...]] | None:
    value = payload.get("command_paths")
    if not isinstance(value, list):
        failures.append(f"{label}: static_json requires command_paths")
        return None
    paths: set[tuple[str, ...]] = set()
    for index, item in enumerate(cast(list[object], value), start=1):
        path = _path_value(item)
        if not path:
            failures.append(f"{label}: command_paths[{index}] must be a string or string array")
            continue
        paths.add(path)
    return paths


def _manifest_visible_paths(
    records: tuple[CliCommandRecord, ...],
    enforced_statuses: set[str],
) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    for record in records:
        if record.status not in enforced_statuses:
            continue
        paths.add(record.path)
        paths.update(record.aliases)
    return paths


def _command_items(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, object],
    failures: list[str],
) -> tuple[Mapping[str, object], ...]:
    commands = _mapping_array(payload.get("commands"))
    if not commands:
        failures.append(f"{_rel(root, manifest_path)}: commands must be a non-empty array")
    return commands


def _manifest_path(
    root: Path,
    cli_config: Mapping[str, object],
    failures: list[str],
) -> Path | None:
    configured = string_value(cli_config.get("manifest_path")) or string_value(
        cli_config.get("manifest")
    )
    if configured:
        configured_path = Path(configured)
        if configured_path.is_absolute():
            failures.append("documentation.cli.manifest_path must be repository-relative")
            return None
        manifest_path = (root / configured).resolve()
        if not is_within_root(root, manifest_path):
            failures.append(
                f"documentation.cli.manifest_path escapes repository root {configured!r}"
            )
            return None
        return manifest_path
    a0 = root / DEFAULT_A0_MANIFEST_PATH
    if a0.exists():
        return a0.resolve()
    return None


def _cli_config(config: Mapping[str, object] | None) -> Mapping[str, object]:
    documentation = _mapping_value(config.get("documentation") if config else None)
    if documentation is None:
        return {}
    return _mapping_value(documentation.get("cli")) or {}


def _enforced_statuses(
    cli_config: Mapping[str, object],
    failures: list[str],
) -> set[str]:
    value = cli_config.get("enforced_statuses")
    label = "documentation.cli.enforced_statuses"
    if value is None:
        return set(ENFORCED_STATUSES)
    if not isinstance(value, list):
        failures.append(f"{label} must be an array")
        return set(ENFORCED_STATUSES)
    statuses: set[str] = set()
    if not value:
        failures.append(f"{label} must not be empty")
        return set(ENFORCED_STATUSES)
    for index, item in enumerate(cast(list[object], value), start=1):
        status = string_value(item)
        if not status:
            failures.append(f"{label}[{index}] must be a non-empty string")
            continue
        if status not in COMMAND_STATUSES:
            failures.append(f"{label}[{index}]: invalid status {status!r}")
            continue
        statuses.add(status)
    return statuses or set(ENFORCED_STATUSES)


def _is_a0_manifest(payload: Mapping[str, object]) -> bool:
    return string_value(payload.get("schema")) == A0_SCHEMA


def _manifest_format(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, object],
    failures: list[str],
) -> str | None:
    schema = string_value(payload.get("schema"))
    schema_version = string_value(payload.get("schema_version"))
    if _is_a0_manifest_path(manifest_path):
        if schema != A0_SCHEMA:
            failures.append(
                f"{_rel(root, manifest_path)}: a0 manifest path requires schema "
                f"{A0_SCHEMA!r}; migrate the manifest to the a0 contract or run "
                "the migration command when one exists"
            )
        return "a0"
    if _is_legacy_manifest_path(manifest_path):
        if _is_a0_manifest(payload):
            failures.append(
                f"{_rel(root, manifest_path)}: a0 manifest payload belongs in "
                "command_manifest.a0.json; rename the manifest or run the "
                "migration command when one exists"
            )
            return None
        return "v0"
    if _is_a0_manifest(payload):
        return "a0"
    failures.append(
        f"{_rel(root, manifest_path)}: unsupported command manifest schema_version "
        f"{schema_version!r}; use command_manifest.a0.json or an explicit legacy "
        "v0 path during migration; run the migration command when one exists"
    )
    return None


def _is_a0_manifest_path(manifest_path: Path) -> bool:
    return ".a0." in manifest_path.name.lower()


def _is_legacy_manifest_path(manifest_path: Path) -> bool:
    name = manifest_path.name.lower()
    return ".v0." in name


def _standard_a0_schema_path() -> Path:
    source_checkout_schema = Path(__file__).resolve().parents[2] / DEFAULT_A0_SCHEMA_PATH
    if source_checkout_schema.exists():
        return source_checkout_schema
    package_schema = resources.files("wn_dev_std").joinpath(
        "contracts",
        DEFAULT_A0_SCHEMA_PATH.name,
    )
    return Path(str(package_schema))


def _command_path(command: Mapping[str, object]) -> tuple[str, ...]:
    return _path_array_value(command.get("path"))


def _alias_paths(
    command: Mapping[str, object],
    command_path: tuple[str, ...],
) -> tuple[tuple[str, ...], ...]:
    aliases = _string_array(command.get("aliases"))
    values: list[tuple[str, ...]] = []
    for alias in aliases:
        alias_path = tuple(alias.split())
        if len(alias_path) == 1 and len(command_path) > 1:
            alias_path = (*command_path[:-1], alias_path[0])
        if alias_path:
            values.append(alias_path)
    return tuple(values)


def _path_value(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(part for part in value.split() if part)
    if not isinstance(value, list):
        return ()
    return _path_array_value(cast(list[object], value))


def _path_array_value(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    parts: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item.strip():
            return ()
        parts.append(item.strip())
    return tuple(parts)


def _summary(command: Mapping[str, object]) -> str:
    return string_value(command.get("summary")) or string_value(command.get("description"))


def _has_evidence_disposition(command: Mapping[str, object]) -> bool:
    return bool(
        string_value(command.get("surface_ref"))
        or _mapping_array(command.get("verification_refs"))
        or _string_array(command.get("exception_refs"))
        or _string_array(command.get("issue_refs"))
    )


def _load_json_mapping(path: Path, failures: list[str]) -> Mapping[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{path.as_posix()}: invalid JSON: {exc}")
        return None
    if not isinstance(raw, dict):
        failures.append(f"{path.as_posix()}: JSON document must be an object")
        return None
    return cast(Mapping[str, object], raw)


def _mapping_array(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    items: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            return ()
        items.append(cast(Mapping[str, object], item))
    return tuple(items)


def _mapping_array_field(
    value: object,
    label: str,
    key: str,
    failures: list[str],
) -> tuple[Mapping[str, object], ...] | None:
    if not isinstance(value, list):
        failures.append(f"{label}: {key} must be an array of objects")
        return None
    items: list[Mapping[str, object]] = []
    for index, item in enumerate(cast(list[object], value), start=1):
        if not isinstance(item, dict):
            failures.append(f"{label}: {key}[{index}] must be an object")
            continue
        items.append(cast(Mapping[str, object], item))
    return tuple(items)


def _mapping_value(value: object) -> Mapping[str, object] | None:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    return None


def _string_array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item.strip():
            return ()
        items.append(item.strip())
    return tuple(items)


def _required_non_empty_string(
    metadata: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> str:
    if key not in metadata:
        failures.append(f"{label}: missing {key}")
        return ""
    value = metadata.get(key)
    if not isinstance(value, str):
        failures.append(f"{label}: {key} must be a string")
        return ""
    if not value.strip():
        failures.append(f"{label}: {key} must be a non-empty string")
        return ""
    return value.strip()


def _positive_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return default


def _path_text(path: tuple[str, ...]) -> str:
    return " ".join(path)


def _rel(root: Path, path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _summarize_failures(label: str, failures: Sequence[str], limit: int = 10) -> str:
    shown = list(failures[:limit])
    suffix = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
    return f"{label} governance failures: " + "; ".join(shown) + suffix
