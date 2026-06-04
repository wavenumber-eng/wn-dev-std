"""Repository conformance checks used by the example CLI."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Single conformance check result."""

    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
)

REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/contracts",
    "docs/releases",
)

MIXED_MODE_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "CMakeLists.txt",
    "CMakePresets.json",
    "dist/README.md",
    "scripts/validate_native.py",
    "scripts/validate_python_package.py",
)

CPP_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "CMakeLists.txt",
    "CMakePresets.json",
)

CLANG_FORMAT_REQUIRED_SETTINGS = {
    "BasedOnStyle": "LLVM",
    "BreakBeforeBraces": "Allman",
    "IndentWidth": "4",
    "ColumnLimit": "100",
    "PointerAlignment": "Left",
    "SortIncludes": "true",
    "IncludeBlocks": "Preserve",
}

ProfileName = Literal["python-package", "python-native-wasm", "cpp-library"]
SUPPORTED_PROFILES = ("python-package", "python-native-wasm", "cpp-library")


def run_basic_checks(root: Path) -> tuple[CheckResult, ...]:
    """Run lightweight repository checks for a Python standards project."""
    resolved_root = root.resolve()
    pyproject = _load_pyproject(resolved_root)
    profile = _project_profile(pyproject)
    checks = [
        _check_required_paths(resolved_root, "root files", _required_root_files(profile)),
        _check_required_paths(resolved_root, "documentation", REQUIRED_DOC_PATHS),
        _check_required_paths(resolved_root, "rack suite", ("tests/rack.toml",)),
        _check_no_env_file(resolved_root),
    ]
    if profile != "cpp-library":
        checks.extend(
            [
                _check_uv_lock(resolved_root),
                _check_pyproject_backend(resolved_root, pyproject, profile),
            ]
        )
    if profile == "cpp-library":
        checks.extend(
            [
                _check_required_paths(resolved_root, "C++ files", CPP_REQUIRED_PATHS),
                _check_clang_format_policy(resolved_root),
                _check_cmake_presets_policy(resolved_root),
            ]
        )
    if profile == "python-native-wasm":
        checks.extend(
            [
                _check_required_paths(resolved_root, "mixed-mode files", MIXED_MODE_REQUIRED_PATHS),
                _check_clang_format_policy(resolved_root),
                _check_cmake_presets_policy(resolved_root),
                _check_dist_root_policy(resolved_root),
            ]
        )
    return tuple(checks)


def format_results(results: tuple[CheckResult, ...], output_format: str) -> str:
    """Format check results as text or JSON."""
    if output_format == "json":
        payload: dict[str, object] = {"passed": all(result.passed for result in results)}
        payload["checks"] = [result.to_dict() for result in results]
        return json.dumps(payload, indent=2, sort_keys=True)

    lines: list[str] = []
    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        lines.append(f"[{marker}] {result.name}: {result.detail}")
    return "\n".join(lines)


def _check_required_paths(root: Path, name: str, relative_paths: tuple[str, ...]) -> CheckResult:
    missing = [
        relative_path for relative_path in relative_paths if not (root / relative_path).exists()
    ]
    if missing:
        return CheckResult(name, False, "missing " + ", ".join(missing))
    return CheckResult(name, True, "all required paths are present")


def _check_no_env_file(root: Path) -> CheckResult:
    if (root / ".env").exists():
        return CheckResult("secret hygiene", False, ".env must not be committed")
    return CheckResult("secret hygiene", True, ".env is not present")


def _required_root_files(profile: ProfileName) -> tuple[str, ...]:
    if profile == "cpp-library":
        return tuple(path for path in REQUIRED_ROOT_FILES if path != "pyproject.toml")
    return REQUIRED_ROOT_FILES


def _check_uv_lock(root: Path) -> CheckResult:
    if (root / "uv.lock").exists():
        return CheckResult("uv lock", True, "uv.lock is committed")
    return CheckResult("uv lock", False, "uv.lock is required for reproducible installs")


def _load_pyproject(root: Path) -> Mapping[str, object] | None:
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return cast(Mapping[str, object], tomllib.load(handle))


def _project_profile(pyproject: Mapping[str, object] | None) -> ProfileName:
    if pyproject is None:
        return "python-package"
    tool_raw = pyproject.get("tool")
    if not isinstance(tool_raw, dict):
        return "python-package"
    tool = cast(Mapping[str, object], tool_raw)
    config_raw = tool.get("wn_dev_std")
    if not isinstance(config_raw, dict):
        return "python-package"
    config = cast(Mapping[str, object], config_raw)
    profile = config.get("profile")
    if profile == "python-package":
        return "python-package"
    if profile == "python-native-wasm":
        return "python-native-wasm"
    if profile == "cpp-library":
        return "cpp-library"
    return "python-package"


def _check_pyproject_backend(
    root: Path,
    pyproject: Mapping[str, object] | None,
    profile: ProfileName,
) -> CheckResult:
    if pyproject is None:
        return CheckResult("build backend", False, "pyproject.toml is missing")

    build_system = _mapping(pyproject.get("build-system"), "build-system")
    backend = build_system.get("build-backend")
    if backend == "hatchling.build":
        return CheckResult("build backend", True, "pure Python package uses Hatchling")
    if profile == "python-native-wasm" and backend == "setuptools.build_meta":
        if (root / "setup.py").exists():
            return CheckResult(
                "build backend", True, "mixed-mode package uses custom setuptools hook"
            )
        return CheckResult("build backend", False, "setuptools native wheel hook requires setup.py")
    return CheckResult("build backend", False, "expected build-backend = hatchling.build")


def _check_dist_root_policy(root: Path) -> CheckResult:
    dist = root / "dist"
    if not dist.exists():
        return CheckResult("dist policy", False, "mixed-mode profile requires dist/README.md")
    allowed_files = {".gitkeep", "README.md"}
    allowed_dirs = {"native", "wasm"}
    unexpected = [
        child.name
        for child in dist.iterdir()
        if (child.is_file() and child.name not in allowed_files)
        or (child.is_dir() and child.name not in allowed_dirs)
    ]
    if unexpected:
        return CheckResult(
            "dist policy", False, "unexpected root dist entries: " + ", ".join(unexpected)
        )
    return CheckResult("dist policy", True, "dist/ uses grouped native and WASM paths")


def _check_clang_format_policy(root: Path) -> CheckResult:
    path = root / ".clang-format"
    if not path.exists():
        return CheckResult("clang-format policy", False, ".clang-format is required")
    settings = _read_simple_yaml_map(path)
    missing_or_wrong = [
        f"{key}={value}"
        for key, value in CLANG_FORMAT_REQUIRED_SETTINGS.items()
        if settings.get(key) != value
    ]
    if missing_or_wrong:
        return CheckResult(
            "clang-format policy",
            False,
            "expected " + ", ".join(missing_or_wrong),
        )
    return CheckResult("clang-format policy", True, "formatter matches C++ baseline")


def _check_cmake_presets_policy(root: Path) -> CheckResult:
    path = root / "CMakePresets.json"
    if not path.exists():
        return CheckResult("CMake presets", False, "CMakePresets.json is required")
    raw_data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return CheckResult("CMake presets", False, "CMakePresets.json must contain an object")
    data = cast(Mapping[str, object], raw_data)
    raw_presets = data.get("configurePresets")
    if not isinstance(raw_presets, list):
        return CheckResult("CMake presets", False, "configurePresets array is required")

    raw_preset_items = cast(list[object], raw_presets)
    presets = _mapping_list(raw_preset_items)
    generator_values = _preset_generators(presets)
    if not generator_values:
        return CheckResult(
            "CMake presets", False, "at least one configure preset must set generator"
        )
    non_ninja = [value for value in generator_values if value != "Ninja"]
    if non_ninja:
        return CheckResult("CMake presets", False, "Ninja is the default generator")

    if not _has_compile_commands_enabled(presets):
        return CheckResult(
            "CMake presets",
            False,
            "at least one configure preset must set CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        )
    return CheckResult("CMake presets", True, "Ninja and compile commands are configured")


def _read_simple_yaml_map(path: Path) -> dict[str, str]:
    settings: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        settings[key.strip()] = value.strip().strip('"').strip("'")
    return settings


def _mapping_list(values: list[object]) -> list[Mapping[str, object]]:
    items: list[Mapping[str, object]] = []
    for value in values:
        if isinstance(value, dict):
            items.append(cast(Mapping[str, object], value))
    return items


def _preset_generators(presets: list[Mapping[str, object]]) -> list[str]:
    generators: list[str] = []
    for preset in presets:
        generator = preset.get("generator")
        if isinstance(generator, str):
            generators.append(generator)
    return generators


def _has_compile_commands_enabled(presets: list[Mapping[str, object]]) -> bool:
    for preset in presets:
        cache_variables_raw = preset.get("cacheVariables")
        if not isinstance(cache_variables_raw, dict):
            continue
        cache_variables = cast(Mapping[str, object], cache_variables_raw)
        value = cache_variables.get("CMAKE_EXPORT_COMPILE_COMMANDS")
        if value is True or value == "ON":
            return True
    return False


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise ValueError(f"expected [{label}] to be a mapping")
