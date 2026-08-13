"""Bazel-preferred native build-system policy with CMake compatibility."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast


def check_native_build_policy(root: Path) -> tuple[bool, str]:
    """Validate a preferred Bazel surface or a permitted CMake/Ninja surface."""
    if (root / "MODULE.bazel").exists():
        return _check_bazel_policy(root)
    if (root / "CMakeLists.txt").exists() or (root / "CMakePresets.json").exists():
        return _check_cmake_policy(root)
    return (
        False,
        "native projects require preferred Bazel (MODULE.bazel) or permitted CMake "
        "(CMakeLists.txt plus CMakePresets.json)",
    )


def _check_bazel_policy(root: Path) -> tuple[bool, str]:
    failures = _missing_bazel_file_failures(root)
    module_text = (root / "MODULE.bazel").read_text(encoding="utf-8")
    failures.extend(
        _required_marker_failures(
            module_text, (("module(", "MODULE.bazel must declare module(...)"),)
        )
    )
    failures.extend(
        []
        if _has_bazel_build_file(root)
        else ["at least one BUILD.bazel or BUILD file is required"]
    )
    version_path = root / ".bazelversion"
    failures.extend(_bazel_version_failures(version_path))
    rack_path = root / "tests" / "rack.toml"
    rack_text = rack_path.read_text(encoding="utf-8").lower() if rack_path.exists() else ""
    failures.extend(
        _required_marker_failures(
            rack_text,
            (
                ("bazel build", "tests/rack.toml must declare bazel build"),
                ("bazel test", "tests/rack.toml must declare bazel test"),
                (
                    "compile_commands",
                    "tests/rack.toml must declare Bazel compile_commands generation",
                ),
            ),
        )
    )
    if failures:
        return False, "; ".join(failures)
    return True, "preferred Bazel/Bzlmod build, test, lock, and compile_commands lanes are declared"


def _check_cmake_policy(root: Path) -> tuple[bool, str]:
    loaded = _load_cmake_presets(root)
    if isinstance(loaded, str):
        return False, loaded
    presets = loaded
    generators = [value for preset in presets if isinstance(value := preset.get("generator"), str)]
    if not generators:
        return False, "at least one CMake configure preset must set generator"
    if any(generator != "Ninja" for generator in generators):
        return False, "Ninja remains the required CMake compatibility generator"
    if not any(_compile_commands_enabled(preset) for preset in presets):
        return False, "a CMake preset must set CMAKE_EXPORT_COMPILE_COMMANDS=ON"
    return True, "permitted CMake compatibility build uses Ninja and compile commands"


def _missing_bazel_file_failures(root: Path) -> list[str]:
    required = {
        "MODULE.bazel.lock": (
            "MODULE.bazel.lock is required for Bazel projects; generate it with "
            "bazel mod deps --lockfile_mode=update using the pinned Bazel version"
        ),
        ".bazelrc": ".bazelrc is required for Bazel projects",
        ".bazelversion": ".bazelversion is required for Bazel projects",
    }
    return [message for relative, message in required.items() if not (root / relative).is_file()]


def _required_marker_failures(
    text: str,
    requirements: tuple[tuple[str, str], ...],
) -> list[str]:
    return [message for marker, message in requirements if marker not in text]


def _bazel_version_failures(path: Path) -> list[str]:
    if not path.exists() or _pinned_bazel_version(path.read_text(encoding="utf-8")):
        return []
    return [".bazelversion must pin a numeric Bazel release"]


def _load_cmake_presets(root: Path) -> list[Mapping[str, object]] | str:
    if not (root / "CMakeLists.txt").exists():
        return "CMake compatibility projects require CMakeLists.txt"
    path = root / "CMakePresets.json"
    if not path.exists():
        return "CMake compatibility projects require CMakePresets.json"
    loaded = _load_json(path)
    if isinstance(loaded, str):
        return loaded
    raw_presets = loaded.get("configurePresets")
    if not isinstance(raw_presets, list):
        return "CMake configurePresets array is required"
    return [
        cast(Mapping[str, object], item)
        for item in cast(list[object], raw_presets)
        if isinstance(item, dict)
    ]


def _load_json(path: Path) -> Mapping[str, object] | str:
    try:
        raw_data: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"CMakePresets.json is invalid JSON: {exc}"
    if not isinstance(raw_data, dict):
        return "CMakePresets.json must contain an object"
    return cast(Mapping[str, object], raw_data)


def _has_bazel_build_file(root: Path) -> bool:
    excluded = {".git", "bazel-bin", "bazel-out", "bazel-testlogs", "build", "vendor"}
    return any(
        path.is_file() and path.name in {"BUILD.bazel", "BUILD"}
        for path in root.rglob("*")
        if not any(part in excluded for part in path.relative_to(root).parts)
    )


def _pinned_bazel_version(text: str) -> bool:
    value = text.strip()
    parts = value.split(".")
    return len(parts) >= 2 and all(part.isdecimal() for part in parts)


def _compile_commands_enabled(preset: Mapping[str, object]) -> bool:
    raw = preset.get("cacheVariables")
    if not isinstance(raw, dict):
        return False
    cache = cast(Mapping[str, object], raw)
    value = cache.get("CMAKE_EXPORT_COMPILE_COMMANDS")
    if isinstance(value, str):
        return value.upper() in {"ON", "TRUE", "1", "YES"}
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        nested = cast(Mapping[str, object], value).get("value")
        return isinstance(nested, str) and nested.upper() in {"ON", "TRUE", "1", "YES"}
    return False
