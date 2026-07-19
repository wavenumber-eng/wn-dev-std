"""Rack command-surface helpers for Rust policy checks."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class CommandRequirement:
    """Text markers that prove a command lane is declared."""

    label: str
    markers: tuple[str, ...]
    excluded_markers: tuple[str, ...] = ()


HOST_COMMANDS = (
    CommandRequirement("cargo fmt --all -- --check", ("cargo fmt", "--all", "-- --check")),
    CommandRequirement("cargo check --locked", ("cargo check", "--locked")),
    CommandRequirement(
        "cargo clippy --locked -- -D warnings",
        ("cargo clippy", "--locked", "-d warnings"),
    ),
    CommandRequirement("cargo test --locked", ("cargo test", "--locked"), ("--doc",)),
    CommandRequirement("cargo test --doc --locked", ("cargo test", "--doc", "--locked")),
    CommandRequirement(
        'RUSTDOCFLAGS="-D warnings" cargo doc --locked',
        ("rustdocflags", "-d warnings", "cargo doc", "--locked"),
    ),
)
FIRMWARE_COMMANDS = (
    CommandRequirement("cargo check --target --locked", ("cargo check", "--target", "--locked")),
    CommandRequirement(
        "cargo clippy --target --locked -- -D warnings",
        ("cargo clippy", "--target", "--locked", "-d warnings"),
    ),
    CommandRequirement(
        "cargo build --release --target --locked",
        ("cargo build", "--release", "--target", "--locked"),
    ),
)
RUNNER_MARKERS = ("cargo embed", "probe-rs", "cargo-embed")


def check_rust_command_surface(
    root: Path,
    profile: str,
    runner: str | None,
) -> tuple[bool, str]:
    """Return whether declared Rack commands satisfy Rust lane requirements."""
    rack_path = root / "tests" / "rack.toml"
    if not rack_path.exists():
        return False, "tests/rack.toml is required"

    commands = _rack_commands(rack_path)
    if isinstance(commands, str):
        return False, commands

    required = list(HOST_COMMANDS)
    if profile == "rust-firmware":
        required.extend(FIRMWARE_COMMANDS)

    missing = [item.label for item in required if not _has_command_markers(commands, item)]
    if profile == "rust-firmware" and not _has_runner_command(commands, runner):
        missing.append("hardware runner command")
    if missing:
        return False, "missing " + ", ".join(missing)
    return True, "Cargo guardrail commands are declared"


def _rack_commands(path: Path) -> tuple[str, ...] | str:
    data = _load_toml_mapping(path, "tests/rack.toml")
    if isinstance(data, str):
        return data
    commands: list[str] = []
    _collect_command_values(data, commands)
    if not commands:
        return "tests/rack.toml must declare command entries"
    return tuple(_normalized_text(command) for command in commands)


def _load_toml_mapping(path: Path, label: str) -> Mapping[str, object] | str:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        return f"{label} is invalid TOML: {exc}"
    return cast(Mapping[str, object], data)


def _collect_command_values(value: object, commands: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in cast(Mapping[str, object], value).items():
            if key == "command" and isinstance(item, str):
                commands.append(item)
            else:
                _collect_command_values(item, commands)
    elif isinstance(value, list):
        for item in cast(list[object], value):
            _collect_command_values(item, commands)


def _has_runner_command(commands: Sequence[str], runner: str | None) -> bool:
    if any(marker in command for marker in RUNNER_MARKERS for command in commands):
        return True
    if runner is None:
        return False
    runner_path = _normalized_ref(runner)
    runner_name = Path(runner_path).name
    return any(runner_path in command or runner_name in command for command in commands)


def _normalized_ref(value: str) -> str:
    return value.split("#", 1)[0].replace("\\", "/").lower()


def _normalized_text(text: str) -> str:
    return " ".join(text.lower().replace("\r\n", "\n").replace("\\", "/").split())


def _has_command_markers(commands: Sequence[str], requirement: CommandRequirement) -> bool:
    return any(_command_matches_requirement(command, requirement) for command in commands)


def _command_matches_requirement(command: str, requirement: CommandRequirement) -> bool:
    return all(marker in command for marker in requirement.markers) and not any(
        marker in command for marker in requirement.excluded_markers
    )
