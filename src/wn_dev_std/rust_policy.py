"""Static repository policy checks for Rust standard profiles."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from wn_dev_std.check_profiles import ProfileName
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.rust_cargo_workspace import (
    CargoMember,
    mapping_value,
    member_metadata_failures,
    metadata_failures,
    unsafe_lint_targets,
    workspace_failures,
    workspace_member_manifests,
)
from wn_dev_std.rust_command_surface import check_rust_command_surface

EXCLUDED_SOURCE_PARTS = {
    ".git",
    "_build",
    "bindings",
    "generated",
    "node_modules",
    "target",
    "third_party",
    "vendor",
}
HOST_UNSAFE_LEVELS = {"forbid"}
FIRMWARE_UNSAFE_LEVELS = {"forbid", "deny"}
FIRMWARE_FIELDS = (
    "target",
    "no_std_ref",
    "panic_ref",
    "allocator_ref",
    "hardware_ref",
    "memory_layout",
    "runner",
)


def check_rust_policy(
    root: Path,
    config: Mapping[str, object] | None,
    profile: ProfileName,
) -> list[CheckResult]:
    """Return Rust profile policy checks."""
    checks = [
        _check_rust_source_policy(root, config),
        _check_cargo_metadata_policy(root, config, profile),
        _check_rust_toolchain_policy(root, config, profile),
        _check_rust_command_surface_policy(root, config, profile),
    ]
    if profile == "rust-firmware":
        checks.append(_check_rust_firmware_policy(root, config))
    return checks


def _check_rust_source_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> CheckResult:
    source_root = _source_root(config)
    resolved_or_error = _validated_local_path(root, source_root, "rust.source_root")
    if isinstance(resolved_or_error, str):
        return CheckResult("Rust source", False, resolved_or_error)

    source_path = resolved_or_error
    if not source_path.exists():
        return CheckResult("Rust source", False, f"{source_root} is required")
    if not source_path.is_dir():
        return CheckResult("Rust source", False, f"{source_root} must be a directory")

    owned_files = _owned_rust_files(source_path)
    if not owned_files:
        return CheckResult(
            "Rust source",
            False,
            f"at least one owned .rs file is required under {source_root}",
        )
    return CheckResult("Rust source", True, f"owned Rust source under {source_root}")


def _check_cargo_metadata_policy(
    root: Path,
    config: Mapping[str, object] | None,
    profile: ProfileName,
) -> CheckResult:
    cargo_path = root / "Cargo.toml"
    if not cargo_path.exists():
        return CheckResult("Cargo metadata", False, "Cargo.toml is required")

    cargo = _load_toml_mapping(cargo_path, "Cargo.toml")
    if isinstance(cargo, str):
        return CheckResult("Cargo metadata", False, cargo)

    failures, warning = _cargo_metadata_failures(root, cargo, config, profile)
    if failures:
        return CheckResult("Cargo metadata", False, "; ".join(failures))
    return CheckResult("Cargo metadata", True, _cargo_metadata_detail(warning), warning=warning)


def _check_rust_toolchain_policy(
    root: Path,
    config: Mapping[str, object] | None,
    profile: ProfileName,
) -> CheckResult:
    toolchain_path = root / "rust-toolchain.toml"
    if not toolchain_path.exists():
        exception = _exception_ref(config, "ambient_toolchain")
        failure = _ref_failure(root, exception, "rust.exceptions.ambient_toolchain")
        if exception and failure is None:
            return CheckResult(
                "Rust toolchain",
                True,
                "ambient stable Rust toolchain exception is documented",
                warning=True,
            )
        detail = "rust-toolchain.toml is required"
        if failure is not None:
            detail += f"; {failure}"
        return CheckResult("Rust toolchain", False, detail)

    toolchain = _load_toml_mapping(toolchain_path, "rust-toolchain.toml")
    if isinstance(toolchain, str):
        return CheckResult("Rust toolchain", False, toolchain)

    failures = _toolchain_failures(root, config, toolchain, profile)
    if failures:
        return CheckResult("Rust toolchain", False, "; ".join(failures))
    return CheckResult("Rust toolchain", True, "stable rustup toolchain is configured")


def _check_rust_command_surface_policy(
    root: Path,
    config: Mapping[str, object] | None,
    profile: ProfileName,
) -> CheckResult:
    passed, detail = check_rust_command_surface(root, profile, _firmware_runner(config))
    return CheckResult("Rust command surface", passed, detail)


def _check_rust_firmware_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> CheckResult:
    firmware = _firmware_config(config)
    if firmware is None:
        return CheckResult("Rust firmware", False, "[rust.firmware] metadata is required")

    failures: list[str] = []
    values = _required_firmware_values(firmware, failures)
    _firmware_ref_failures(root, values, failures)
    _cargo_config_failures(root, values.get("target"), failures)

    if failures:
        return CheckResult("Rust firmware", False, "; ".join(failures))
    return CheckResult("Rust firmware", True, "embedded target, runner, and docs are declared")


def _cargo_metadata_failures(
    root: Path,
    cargo: Mapping[str, object],
    config: Mapping[str, object] | None,
    profile: ProfileName,
) -> tuple[list[str], bool]:
    failures: list[str] = []
    package = mapping_value(cargo, "package")
    workspace = mapping_value(cargo, "workspace")
    workspace_package = mapping_value(workspace, "package") if workspace is not None else None
    members = workspace_member_manifests(root, workspace, failures)
    if package is None and workspace is None:
        failures.append("Cargo.toml requires [package] or [workspace]")
    if package is not None:
        metadata_failures(package, "package", failures, workspace_package)
    if workspace is not None:
        workspace_failures(workspace, package is None, failures)
        member_metadata_failures(members, workspace_package, failures)
    if _lockfile_missing(root):
        failures.append("Cargo.lock is required for Rust profiles")
    warning = _unsafe_lint_failures(root, cargo, config, profile, failures, members)
    _release_profile_failures(cargo, profile, failures)
    return failures, warning


def _cargo_metadata_detail(warning: bool) -> str:
    detail = "Cargo package/workspace metadata is explicit"
    if warning:
        detail += "; unsafe exception metadata is documented"
    return detail


def _release_profile_failures(
    cargo: Mapping[str, object],
    profile: ProfileName,
    failures: list[str],
) -> None:
    if profile == "rust-firmware" and mapping_value(cargo, "profile.release") is None:
        failures.append("rust-firmware requires explicit [profile.release] settings")


def _unsafe_lint_failures(
    root: Path,
    cargo: Mapping[str, object],
    config: Mapping[str, object] | None,
    profile: ProfileName,
    failures: list[str],
    members: tuple[CargoMember, ...],
) -> bool:
    exception = _exception_ref(config, "unsafe")
    exception_failure = _ref_failure(root, exception, "rust.exceptions.unsafe")
    if exception_failure is not None:
        failures.append(exception_failure)

    allowed = FIRMWARE_UNSAFE_LEVELS if profile == "rust-firmware" else HOST_UNSAFE_LEVELS
    for target in unsafe_lint_targets(cargo, members, failures):
        if _unsafe_lint_allowed(profile, target.level, bool(exception), allowed):
            continue
        label = None if target.label in {"package", "workspace"} else target.label
        _append_unsafe_lint_failure(target.level, allowed, failures, label)
    return bool(exception)


def _unsafe_lint_allowed(
    profile: ProfileName,
    level: str | None,
    has_exception: bool,
    allowed: set[str],
) -> bool:
    if level in allowed:
        return True
    if profile == "rust-firmware" and has_exception and level is not None:
        return True
    return profile == "rust-app" and has_exception and level == "deny"


def _append_unsafe_lint_failure(
    level: str | None,
    allowed: set[str],
    failures: list[str],
    label: str | None = None,
) -> None:
    expected = " or ".join(sorted(allowed))
    field = "lints.rust.unsafe_code"
    if label is not None:
        field = f"{label} {field}"
    if level is None:
        failures.append(f"{field} must be {expected}")
        return
    failures.append(f"{field} is {level!r}; expected {expected}")


def _toolchain_failures(
    root: Path,
    config: Mapping[str, object] | None,
    toolchain: Mapping[str, object],
    profile: ProfileName,
) -> list[str]:
    failures: list[str] = []
    table = mapping_value(toolchain, "toolchain")
    if table is None:
        return ["rust-toolchain.toml requires [toolchain]"]

    channel = _string_value(table.get("channel"))
    if channel is None:
        failures.append("toolchain.channel is required")
    elif not _is_stable_channel(channel):
        failures.append("toolchain.channel must be stable or an explicit stable version")

    components = _string_array(table.get("components"))
    for component in ("rustfmt", "clippy"):
        if component not in components:
            failures.append(f"toolchain.components must include {component}")

    if profile == "rust-firmware":
        target = _firmware_target(config)
        if target is None:
            failures.append("rust.firmware.target is required")
        else:
            failures.extend(_toolchain_target_failures(root, table, target))
    return failures


def _toolchain_target_failures(
    root: Path,
    table: Mapping[str, object],
    target: str,
) -> list[str]:
    if target.endswith(".json"):
        resolved_or_error = _validated_local_path(root, target, "rust.firmware.target")
        if isinstance(resolved_or_error, str):
            return [resolved_or_error]
        if not resolved_or_error.exists():
            return [f"custom target spec {target} does not exist"]
        return []

    targets = _string_array(table.get("targets"))
    if target not in targets:
        return [f"toolchain.targets must include {target}"]
    return []


def _required_firmware_values(
    firmware: Mapping[str, object],
    failures: list[str],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in FIRMWARE_FIELDS:
        value = _string_value(firmware.get(field))
        if value is None:
            failures.append(f"rust.firmware.{field} is required")
        else:
            values[field] = value
    return values


def _firmware_ref_failures(
    root: Path,
    values: Mapping[str, str],
    failures: list[str],
) -> None:
    fields = (
        "no_std_ref",
        "panic_ref",
        "allocator_ref",
        "hardware_ref",
        "memory_layout",
        "runner",
    )
    for field in fields:
        value = values.get(field)
        if value is not None:
            failure = _local_existing_path_failure(root, value, f"rust.firmware.{field}")
            if failure is not None:
                failures.append(failure)


def _cargo_config_failures(
    root: Path,
    target: str | None,
    failures: list[str],
) -> None:
    cargo_config_path = root / ".cargo" / "config.toml"
    if not cargo_config_path.exists():
        failures.append(".cargo/config.toml is required for rust-firmware")
        return
    cargo_config = _load_toml_mapping(cargo_config_path, ".cargo/config.toml")
    if isinstance(cargo_config, str):
        failures.append(cargo_config)
        return
    if target is None:
        return
    if not _cargo_config_mentions_target(cargo_config, target):
        failures.append(f".cargo/config.toml must declare target {target}")


def _source_root(config: Mapping[str, object] | None) -> str:
    rust = _rust_config(config)
    value = _string_value(rust.get("source_root")) if rust is not None else None
    return value or "src"


def _firmware_target(config: Mapping[str, object] | None) -> str | None:
    firmware = _firmware_config(config)
    if firmware is None:
        return None
    return _string_value(firmware.get("target"))


def _firmware_config(config: Mapping[str, object] | None) -> Mapping[str, object] | None:
    rust = _rust_config(config)
    if rust is None:
        return None
    firmware = rust.get("firmware")
    if not isinstance(firmware, dict):
        return None
    return cast(Mapping[str, object], firmware)


def _exception_ref(config: Mapping[str, object] | None, key: str) -> str | None:
    rust = _rust_config(config)
    if rust is None:
        return None
    exceptions = rust.get("exceptions")
    if not isinstance(exceptions, dict):
        return None
    return _string_value(cast(Mapping[str, object], exceptions).get(key))


def _rust_config(config: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if config is None:
        return None
    rust = config.get("rust")
    if not isinstance(rust, dict):
        return None
    return cast(Mapping[str, object], rust)


def _load_toml_mapping(path: Path, label: str) -> Mapping[str, object] | str:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        return f"{label} is invalid TOML: {exc}"
    return cast(Mapping[str, object], data)


def _lockfile_missing(root: Path) -> bool:
    return not (root / "Cargo.lock").exists()


def _owned_rust_files(source_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(source_root.rglob("*.rs"))
        if path.is_file() and not _has_excluded_part(source_root, path)
    ]


def _has_excluded_part(source_root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(source_root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_SOURCE_PARTS for part in parts)


def _cargo_config_mentions_target(config: Mapping[str, object], target: str) -> bool:
    build = mapping_value(config, "build")
    if build is not None and _string_value(build.get("target")) == target:
        return True
    target_table = config.get("target")
    return isinstance(target_table, dict) and target in target_table


def _firmware_runner(config: Mapping[str, object] | None) -> str | None:
    firmware = _firmware_config(config)
    if firmware is None:
        return None
    return _string_value(firmware.get("runner"))


def _validated_local_path(root: Path, value: str, label: str) -> Path | str:
    raw_path = Path(value)
    if raw_path.is_absolute():
        return f"{label} must be a relative path"
    if ".." in raw_path.parts:
        return f"{label} must not contain '..'"
    resolved = (root / raw_path).resolve()
    if not _is_within_root(root, resolved):
        return f"{label} resolves outside the repository root"
    return resolved


def _local_existing_path_failure(root: Path, value: str, label: str) -> str | None:
    local_value = _local_ref_path(value)
    resolved_or_error = _validated_local_path(root, local_value, label)
    if isinstance(resolved_or_error, str):
        return resolved_or_error
    if not resolved_or_error.exists():
        return f"{label} {local_value} does not exist"
    return None


def _ref_failure(root: Path | None, value: str | None, label: str) -> str | None:
    if value is None:
        return None
    if _looks_external_ref(value):
        return None
    if root is None:
        return None
    return _local_existing_path_failure(root, value, label)


def _looks_external_ref(value: str) -> bool:
    if "://" in value:
        return True
    path, separator, fragment = value.partition("#")
    return bool(separator and fragment.isdecimal() and len(path.split("/")) == 2)


def _local_ref_path(value: str) -> str:
    return value.split("#", 1)[0]


def _is_within_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_stable_channel(channel: str) -> bool:
    normalized = channel.strip().lower()
    return normalized == "stable" or normalized[0].isdigit()


def _string_value(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        text = _string_value(item)
        if text is not None:
            items.append(text)
    return tuple(items)
