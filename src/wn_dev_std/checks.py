"""Repository conformance checks used by the example CLI."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from xml.etree import ElementTree


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

CSHARP_REQUIRED_PATHS = (
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "Directory.Build.props",
    "README.md",
    "build.ps1",
    "src",
    "tests",
    "wn-dev-std.toml",
)

CSHARP_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/contracts",
    "docs/releases",
)

CSHARP_ANALYZER_PROPS = (
    ("EnforceCodeStyleInBuild", "true"),
    ("EnableNETAnalyzers", "true"),
)

CSHARP_EDITORCONFIG_RULES = (
    "dotnet_diagnostic.CA1502.severity = error",
    "dotnet_diagnostic.CA1505.severity = error",
    "dotnet_diagnostic.CA1506.severity = error",
)

JAVASCRIPT_WEB_REQUIRED_PATHS = (
    "src",
    "tests/rack.toml",
)

JAVASCRIPT_WEB_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "src",
    "tests",
    "wn-dev-std.toml",
)

PYTHON_JS_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "src",
    "tests",
    "wn-dev-std.toml",
)

JAVASCRIPT_WEB_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/javascript-standard.html",
    "docs/contracts",
    "docs/releases",
)

PYTHON_JS_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/javascript-standard.html",
    "docs/contracts",
    "docs/releases",
)

JS_CSS_EXCLUDED_PARTS = {"vendor", "lib", "_build", "node_modules"}
STANDARD_COMMAND_VERBS = ("install", "update", "build", "test", "signoff")

CLANG_FORMAT_REQUIRED_SETTINGS = {
    "BasedOnStyle": "LLVM",
    "BreakBeforeBraces": "Allman",
    "IndentWidth": "4",
    "ColumnLimit": "100",
    "PointerAlignment": "Left",
    "SortIncludes": "true",
    "IncludeBlocks": "Preserve",
}

ProfileName = Literal[
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
]
SUPPORTED_PROFILES = (
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
)


def run_basic_checks(root: Path) -> tuple[CheckResult, ...]:
    """Run lightweight repository checks for a Python standards project."""
    resolved_root = root.resolve()
    pyproject = _load_pyproject(resolved_root)
    config = _load_standard_config(resolved_root, pyproject)
    profile = _project_profile(config)
    checks = [
        _check_required_paths(resolved_root, "root files", _required_root_files(profile)),
        _check_required_paths(resolved_root, "documentation", _required_doc_paths(profile)),
        _check_no_env_file(resolved_root),
    ]
    if profile != "csharp-app":
        checks.append(_check_required_paths(resolved_root, "rack suite", ("tests/rack.toml",)))
    if profile not in {"cpp-library", "csharp-app", "javascript-web-app"}:
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
    if profile == "csharp-app":
        checks.extend(
            [
                _check_required_paths(resolved_root, "C# files", CSHARP_REQUIRED_PATHS),
                _check_dotnet_project_policy(resolved_root),
                _check_dotnet_analyzer_policy(resolved_root),
            ]
        )
    if profile in {"javascript-web-app", "python-js-app"}:
        checks.extend(
            [
                _check_required_paths(
                    resolved_root,
                    "web app files",
                    JAVASCRIPT_WEB_REQUIRED_PATHS,
                ),
                _check_web_source_policy(resolved_root),
                _check_web_typecheck_policy(resolved_root),
                _check_web_css_token_policy(resolved_root),
                _check_web_command_surface_policy(resolved_root),
                _check_web_signoff_policy(resolved_root),
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
    if profile == "csharp-app":
        return CSHARP_REQUIRED_PATHS
    if profile == "javascript-web-app":
        return JAVASCRIPT_WEB_REQUIRED_ROOT_FILES
    if profile == "python-js-app":
        return PYTHON_JS_REQUIRED_ROOT_FILES
    return REQUIRED_ROOT_FILES


def _required_doc_paths(profile: ProfileName) -> tuple[str, ...]:
    if profile == "csharp-app":
        return CSHARP_REQUIRED_DOC_PATHS
    if profile in {"javascript-web-app", "python-js-app"}:
        return PYTHON_JS_REQUIRED_DOC_PATHS
    return REQUIRED_DOC_PATHS


def _check_uv_lock(root: Path) -> CheckResult:
    for candidate in (root, *root.parents):
        if (candidate / "uv.lock").exists():
            detail = (
                "uv.lock is committed"
                if candidate == root
                else f"uv.lock is committed at workspace root {candidate}"
            )
            return CheckResult("uv lock", True, detail)
        if (candidate / ".git").exists():
            break
    return CheckResult(
        "uv lock",
        False,
        "uv.lock is required at the package or workspace root",
    )


def _load_pyproject(root: Path) -> Mapping[str, object] | None:
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return cast(Mapping[str, object], tomllib.load(handle))


def _load_standard_config(
    root: Path,
    pyproject: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    standalone = root / "wn-dev-std.toml"
    if standalone.exists():
        with standalone.open("rb") as handle:
            raw = cast(Mapping[str, object], tomllib.load(handle))
        tool_raw = raw.get("tool")
        if isinstance(tool_raw, dict):
            tool = cast(Mapping[str, object], tool_raw)
            config_raw = tool.get("wn_dev_std")
            if isinstance(config_raw, dict):
                return cast(Mapping[str, object], config_raw)
        return raw

    if pyproject is None:
        return None
    tool_raw = pyproject.get("tool")
    if not isinstance(tool_raw, dict):
        return None
    tool = cast(Mapping[str, object], tool_raw)
    config_raw = tool.get("wn_dev_std")
    if not isinstance(config_raw, dict):
        return None
    return cast(Mapping[str, object], config_raw)


def _project_profile(config: Mapping[str, object] | None) -> ProfileName:
    if config is None:
        return "python-package"
    profile = config.get("profile")
    if profile == "python-package":
        return "python-package"
    if profile == "python-native-wasm":
        return "python-native-wasm"
    if profile == "cpp-library":
        return "cpp-library"
    if profile == "csharp-app":
        return "csharp-app"
    if profile == "javascript-web-app":
        return "javascript-web-app"
    if profile == "python-js-app":
        return "python-js-app"
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


def _check_dotnet_project_policy(root: Path) -> CheckResult:
    source_projects = sorted((root / "src").rglob("*.csproj")) if (root / "src").exists() else []
    test_projects = sorted((root / "tests").rglob("*.csproj")) if (root / "tests").exists() else []
    if not source_projects:
        return CheckResult("dotnet projects", False, "at least one source .csproj is required")
    if not test_projects:
        return CheckResult("dotnet projects", False, "at least one test .csproj is required")
    return CheckResult("dotnet projects", True, "source and test projects are present")


def _check_dotnet_analyzer_policy(root: Path) -> CheckResult:
    props_path = root / "Directory.Build.props"
    editorconfig_path = root / ".editorconfig"
    if not props_path.exists():
        return CheckResult("dotnet analyzer policy", False, "Directory.Build.props is required")
    if not editorconfig_path.exists():
        return CheckResult("dotnet analyzer policy", False, ".editorconfig is required")

    props = _msbuild_properties(props_path)
    missing_props = [
        f"{name}={expected}"
        for name, expected in CSHARP_ANALYZER_PROPS
        if props.get(name) != expected
    ]
    editorconfig = editorconfig_path.read_text(encoding="utf-8")
    missing_rules = [rule for rule in CSHARP_EDITORCONFIG_RULES if rule not in editorconfig]
    if missing_props or missing_rules:
        expected = missing_props + missing_rules
        return CheckResult("dotnet analyzer policy", False, "expected " + ", ".join(expected))
    return CheckResult(
        "dotnet analyzer policy",
        True,
        "code style, analyzers, and complexity gates are configured",
    )


def _owned_web_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    src = root / "src"
    if not src.exists():
        return []
    files: list[Path] = []
    for suffix in suffixes:
        for path in src.rglob(suffix):
            relative_parts = set(path.relative_to(root).parts)
            if JS_CSS_EXCLUDED_PARTS & relative_parts:
                continue
            if path.name.endswith(".min.js") or path.name.endswith(".min.css"):
                continue
            files.append(path)
    return sorted(files)


def _stray_minified_web_files(root: Path) -> list[str]:
    stray: list[str] = []
    for suffix in ("*.min.js", "*.min.css"):
        for path in root.rglob(suffix):
            relative_parts = set(path.relative_to(root).parts)
            if JS_CSS_EXCLUDED_PARTS & relative_parts:
                continue
            stray.append(path.relative_to(root).as_posix())
    return sorted(stray)


def _check_web_source_policy(root: Path) -> CheckResult:
    owned_js = _owned_web_files(root, ("*.js", "*.mjs", "*.jsx", "*.ts", "*.tsx"))
    owned_css = _owned_web_files(root, ("*.css",))
    if not owned_js:
        return CheckResult(
            "web source",
            False,
            "at least one owned JS/TS source file is required under src/",
        )
    if not owned_css:
        return CheckResult(
            "web source",
            False,
            "at least one owned CSS source file is required under src/",
        )

    stray_minified = _stray_minified_web_files(root)
    if stray_minified:
        return CheckResult(
            "web source",
            False,
            "minified/generated JS/CSS must live under vendor/, lib/, _build/, "
            "or node_modules/: " + ", ".join(stray_minified[:5]),
        )
    return CheckResult(
        "web source",
        True,
        f"{len(owned_js)} owned JS/TS and {len(owned_css)} owned CSS file(s) found",
    )


def _check_web_typecheck_policy(root: Path) -> CheckResult:
    owned_js = _owned_web_files(root, ("*.js", "*.mjs", "*.jsx"))
    owned_ts = _owned_web_files(root, ("*.ts", "*.tsx"))
    has_jsconfig = (root / "jsconfig.json").exists()
    has_tsconfig = (root / "tsconfig.json").exists()
    if owned_ts and not has_tsconfig:
        return CheckResult("web typecheck", False, "TypeScript source requires tsconfig.json")
    if has_jsconfig or has_tsconfig:
        config = "tsconfig.json" if has_tsconfig else "jsconfig.json"
        return CheckResult("web typecheck", True, f"{config} is present")

    missing_ts_check = [
        path.relative_to(root).as_posix() for path in owned_js if not _has_ts_check_comment(path)
    ]
    if missing_ts_check:
        return CheckResult(
            "web typecheck",
            False,
            "expected jsconfig.json, tsconfig.json, or // @ts-check in "
            + ", ".join(missing_ts_check[:5]),
        )
    return CheckResult("web typecheck", True, "owned JavaScript files use // @ts-check")


def _has_ts_check_comment(path: Path) -> bool:
    first_lines = path.read_text(encoding="utf-8").splitlines()[:8]
    return any(line.strip() == "// @ts-check" for line in first_lines)


def _check_web_css_token_policy(root: Path) -> CheckResult:
    owned_css = _owned_web_files(root, ("*.css",))
    token_files = [
        path.relative_to(root).as_posix() for path in owned_css if _css_uses_custom_properties(path)
    ]
    if token_files:
        return CheckResult("web CSS tokens", True, "CSS custom properties are present")
    return CheckResult(
        "web CSS tokens",
        False,
        "owned CSS must define or consume CSS custom properties for design constants",
    )


def _css_uses_custom_properties(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "var(--" in text:
        return True
    return any(line.lstrip().startswith("--") and ":" in line for line in text.splitlines())


def _check_web_command_surface_policy(root: Path) -> CheckResult:
    providers = {
        "package.json scripts": _package_script_verbs(root),
        "Makefile targets": _makefile_verbs(root),
        "scripts/dev.py": _dev_py_verbs(root),
        "root or scripts verb files": _script_file_verbs(root),
    }
    required = set(STANDARD_COMMAND_VERBS)
    for provider, verbs in providers.items():
        if required <= verbs:
            return CheckResult("command surface", True, f"{provider} exposes standard verbs")
    return CheckResult(
        "command surface",
        False,
        "expected install, update, build, test, and signoff through package.json, Makefile, "
        "scripts/dev.py, or verb-named scripts",
    )


def _package_script_verbs(root: Path) -> set[str]:
    path = root / "package.json"
    if not path.exists():
        return set()
    raw_data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return set()
    data = cast(Mapping[str, object], raw_data)
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return set()
    scripts_mapping = cast(Mapping[str, object], scripts)
    return {key for key in scripts_mapping if key in STANDARD_COMMAND_VERBS}


def _makefile_verbs(root: Path) -> set[str]:
    verbs: set[str] = set()
    for path in (root / "Makefile", root / "makefile"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            for verb in STANDARD_COMMAND_VERBS:
                if stripped.startswith(f"{verb}:"):
                    verbs.add(verb)
    return verbs


def _dev_py_verbs(root: Path) -> set[str]:
    path = root / "scripts" / "dev.py"
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return {verb for verb in STANDARD_COMMAND_VERBS if verb in text}


def _script_file_verbs(root: Path) -> set[str]:
    verbs: set[str] = set()
    suffixes = (".ps1", ".sh", ".bat", ".cmd")
    for verb in STANDARD_COMMAND_VERBS:
        for directory in (root, root / "scripts"):
            if any((directory / f"{verb}{suffix}").exists() for suffix in suffixes):
                verbs.add(verb)
    return verbs


def _check_web_signoff_policy(root: Path) -> CheckResult:
    missing_scripts = [
        relative
        for relative in ("scripts/js_hygiene.py", "scripts/css_hygiene.py")
        if not (root / relative).exists()
    ]
    if not missing_scripts:
        return CheckResult("web signoff", True, "JS and CSS hygiene scripts are present")
    if (root / "package.json").exists():
        return CheckResult("web signoff", True, "package.json is present for JS/CSS tooling")
    return CheckResult(
        "web signoff",
        False,
        "expected scripts/js_hygiene.py and scripts/css_hygiene.py, or package.json",
    )


def _msbuild_properties(path: Path) -> dict[str, str]:
    root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    properties: dict[str, str] = {}
    for property_group in root.findall("PropertyGroup"):
        for child in list(property_group):
            if child.text is not None:
                properties[child.tag] = child.text.strip().lower()
    return properties


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
