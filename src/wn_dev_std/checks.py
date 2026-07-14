"""Repository conformance checks used by the example CLI."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

from wn_dev_std.audit_config import (
    config_kind,
    effective_scopes,
    rel,
    scope_is_selected,
    standard_config_checks,
    validated_member_path,
    with_member,
    workspace_members,
)
from wn_dev_std.check_profiles import (
    CLANG_FORMAT_REQUIRED_SETTINGS,
    CPP_REQUIRED_PATHS,
    CSHARP_ANALYZER_PROPS,
    CSHARP_EDITORCONFIG_RULES,
    CSHARP_REQUIRED_PATHS,
    MIXED_MODE_REQUIRED_PATHS,
    ZEPHYR_REQUIRED_PATHS,
    ProfileName,
    project_profile,
    required_doc_paths,
    required_path_exists,
    required_root_files,
)
from wn_dev_std.check_profiles import (
    REQUIRED_ROOT_FILES as REQUIRED_ROOT_FILES,
)
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.compatibility_pruning import check_compatibility_pruning_policy
from wn_dev_std.cpp_policy import check_clang_tidy_policy
from wn_dev_std.design_doc_status import check_design_doc_status_policy
from wn_dev_std.governance_checks import governance_doc_checks
from wn_dev_std.native_complexity import check_lizard_gate, check_native_signoff_config
from wn_dev_std.plan_hygiene import check_plan_hygiene_policy
from wn_dev_std.pr_hygiene import check_pr_hygiene_policy
from wn_dev_std.root_discovery import load_pyproject, load_standard_config, standard_config_path
from wn_dev_std.secret_hygiene import check_root_env_policy
from wn_dev_std.web_policy import check_web_policy

JAVASCRIPT_STANDARD_DOC_PATHS = (
    "docs/design/javascript-standard.html",
    "docs/design/standards/javascript.html",
)


def run_basic_checks(root: Path) -> tuple[CheckResult, ...]:
    """Run lightweight repository checks for a Python standards project."""
    return run_audit_checks(root, ("all",))


def run_audit_checks(
    root: Path,
    scopes: Sequence[str] | None = None,
) -> tuple[CheckResult, ...]:
    """Run repository audit checks for the requested scopes."""
    resolved_root = root.resolve()
    pyproject = load_pyproject(resolved_root)
    config = load_standard_config(resolved_root, pyproject)
    config_checks = standard_config_checks(resolved_root, config)
    if config_kind(config) == "workspace":
        workspace_checks = _workspace_audit_checks(resolved_root, config, scopes)
        return (*config_checks, *workspace_checks)

    requested_scopes = effective_scopes(scopes, config)
    checks = _run_selected_audit_checks(resolved_root, requested_scopes, pyproject, config)
    return (*config_checks, *checks)


def _run_selected_audit_checks(
    root: Path,
    requested_scopes: Sequence[str],
    pyproject: Mapping[str, object] | None = None,
    config: Mapping[str, object] | None = None,
) -> tuple[CheckResult, ...]:
    """Run only the repository audit checks needed for the requested scopes."""
    resolved_root = root.resolve()
    resolved_pyproject = pyproject if pyproject is not None else load_pyproject(resolved_root)
    resolved_config = (
        config if config is not None else load_standard_config(resolved_root, resolved_pyproject)
    )
    profile = project_profile(resolved_config)
    checks = _common_checks(resolved_root, profile, resolved_config, requested_scopes)
    checks.extend(
        _python_package_checks(resolved_root, resolved_pyproject, profile, requested_scopes)
    )
    checks.extend(_language_checks(resolved_root, profile, requested_scopes))
    checks.extend(_compat_checks(resolved_root, resolved_config, requested_scopes))
    checks.extend(_ci_checks(resolved_root, resolved_config, requested_scopes))
    checks.extend(_plan_checks(resolved_root, resolved_config, requested_scopes))
    checks.extend(governance_doc_checks(resolved_root, requested_scopes))
    return tuple(checks)


def _python_package_checks(
    root: Path,
    pyproject: Mapping[str, object] | None,
    profile: ProfileName,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    if not _needs_python_package_checks(profile) or not scope_is_selected("repo", requested_scopes):
        return []
    return [
        _check_uv_lock(root),
        _check_pyproject_backend(root, pyproject, profile),
    ]


def _language_checks(
    root: Path,
    profile: ProfileName,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    if not scope_is_selected("language", requested_scopes):
        return []
    return _scoped_results(_profile_specific_checks(root, profile), "language")


def _compat_checks(
    root: Path,
    config: Mapping[str, object] | None,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    pruning_config = _compatibility_pruning_config(config)
    if pruning_config is None or not scope_is_selected("compat", requested_scopes):
        return []
    pruning_result = check_compatibility_pruning_policy(root, pruning_config)
    return [
        CheckResult(
            "compatibility pruning",
            pruning_result.passed,
            pruning_result.detail,
            "compat",
        )
    ]


def _ci_checks(
    root: Path,
    config: Mapping[str, object] | None,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    pr_hygiene_config = _pr_hygiene_config(config)
    if pr_hygiene_config is None or not scope_is_selected("ci", requested_scopes):
        return []
    pr_hygiene_result = check_pr_hygiene_policy(root, pr_hygiene_config)
    return [
        CheckResult(
            "public PR hygiene",
            pr_hygiene_result.passed,
            pr_hygiene_result.detail,
            "ci",
        )
    ]


def _plan_checks(
    root: Path,
    config: Mapping[str, object] | None,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    if not scope_is_selected("docs.plans", requested_scopes):
        return []
    plan_hygiene_result = check_plan_hygiene_policy(root, config)
    return [
        CheckResult(
            "docs.plans",
            plan_hygiene_result.passed,
            plan_hygiene_result.detail,
            "docs.plans",
        )
    ]


def _common_checks(
    root: Path,
    profile: ProfileName,
    config: Mapping[str, object] | None,
    requested_scopes: Sequence[str],
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    if scope_is_selected("repo", requested_scopes):
        checks.append(_check_required_paths(root, "root files", required_root_files(profile)))
    if scope_is_selected("docs", requested_scopes):
        checks.append(
            _scoped_result(_check_required_documentation_paths(root, profile, config), "docs")
        )
    if scope_is_selected("docs.design", requested_scopes):
        checks.append(_scoped_result(_check_design_doc_status(root), "docs.design"))
    if scope_is_selected("repo", requested_scopes):
        checks.append(_check_no_env_file(root))
    if profile != "csharp-app" and scope_is_selected("repo", requested_scopes):
        checks.append(_check_required_paths(root, "rack suite", ("tests/rack.toml",)))
    return checks


def _needs_python_package_checks(profile: ProfileName) -> bool:
    native_or_non_python = {"cpp-library", "csharp-app", "javascript-web-app", "zephyr-firmware"}
    return profile not in native_or_non_python


def _profile_specific_checks(root: Path, profile: ProfileName) -> list[CheckResult]:
    if profile == "cpp-library":
        return _cpp_checks(root)
    if profile == "zephyr-firmware":
        return _zephyr_checks(root)
    if profile == "python-native-wasm":
        return _mixed_mode_checks(root)
    if profile == "csharp-app":
        return _csharp_checks(root)
    if profile in {"javascript-web-app", "python-js-app"}:
        return _web_checks(root)
    return []


def _cpp_checks(root: Path) -> list[CheckResult]:
    return [
        _check_required_paths(root, "C++ files", CPP_REQUIRED_PATHS),
        _check_clang_format_policy(root),
        _check_clang_tidy_policy(root),
        _check_cmake_presets_policy(root),
        _check_native_signoff_config(root),
        _check_lizard_complexity_policy(root),
    ]


def _zephyr_checks(root: Path) -> list[CheckResult]:
    return [
        _check_required_paths(root, "Zephyr files", ZEPHYR_REQUIRED_PATHS),
        _check_clang_format_policy(root),
        _check_clang_tidy_policy(root),
        _check_native_signoff_config(root),
        _check_lizard_complexity_policy(root),
    ]


def _mixed_mode_checks(root: Path) -> list[CheckResult]:
    return [
        _check_required_paths(root, "mixed-mode files", MIXED_MODE_REQUIRED_PATHS),
        _check_clang_format_policy(root),
        _check_clang_tidy_policy(root),
        _check_cmake_presets_policy(root),
        _check_lizard_complexity_policy(root),
        _check_dist_root_policy(root),
    ]


def _csharp_checks(root: Path) -> list[CheckResult]:
    return [
        _check_required_paths(root, "C# files", CSHARP_REQUIRED_PATHS),
        _check_dotnet_project_policy(root),
        _check_dotnet_analyzer_policy(root),
    ]


def _web_checks(root: Path) -> list[CheckResult]:
    return check_web_policy(root)


def _workspace_audit_checks(
    root: Path,
    config: Mapping[str, object] | None,
    scopes: Sequence[str] | None,
) -> tuple[CheckResult, ...]:
    marker_path = standard_config_path(root)
    members = workspace_members(config)
    if not members:
        detail = "workspace config requires [workspace].members"
        if marker_path is not None:
            detail = f"{rel(root, marker_path)} requires [workspace].members"
        return (CheckResult("workspace members", False, detail),)

    checks: list[CheckResult] = []
    seen_members: set[str] = set()
    seen_member_paths: dict[Path, str] = {}
    for member in members:
        member_key = member.replace("\\", "/").strip("/")
        if member_key in seen_members:
            checks.append(
                _workspace_member_failure(member_key, f"duplicate workspace member {member_key!r}")
            )
            continue
        seen_members.add(member_key)

        member_path_or_error = validated_member_path(root, member)
        if isinstance(member_path_or_error, str):
            checks.append(_workspace_member_failure(member_key, member_path_or_error))
            continue

        member_path = member_path_or_error
        first_member_for_path = seen_member_paths.get(member_path)
        if first_member_for_path is not None:
            checks.append(
                _workspace_member_failure(
                    member_key,
                    f"workspace member {member_key!r} duplicates {first_member_for_path!r}",
                )
            )
            continue
        seen_member_paths[member_path] = member_key

        member_result = _workspace_member_checks(member_path, member_key, scopes)
        checks.extend(member_result)

    return tuple(checks)


def _workspace_member_checks(
    member_path: Path,
    member_key: str,
    scopes: Sequence[str] | None,
) -> tuple[CheckResult, ...]:
    member_marker = standard_config_path(member_path)
    if member_marker is None:
        return (
            _workspace_member_failure(
                member_key,
                f"registered member {member_key!r} has no dev-std config marker",
            ),
        )

    member_config = load_standard_config(member_path)
    if config_kind(member_config) == "workspace":
        return (
            _workspace_member_failure(
                member_key,
                f"registered member {member_key!r} must not be kind='workspace'",
            ),
        )

    member_checks = run_audit_checks(member_path, scopes)
    return with_member(member_checks, member_key)


def _workspace_member_failure(member_key: str, detail: str) -> CheckResult:
    return CheckResult("workspace member", False, detail, "repo", member_key)


def format_results(results: tuple[CheckResult, ...], output_format: str) -> str:
    """Format check results as text or JSON."""
    if output_format == "json":
        payload: dict[str, object] = {"passed": all(result.passed for result in results)}
        payload["checks"] = [result.to_dict() for result in results]
        return json.dumps(payload, indent=2, sort_keys=True)

    lines: list[str] = []
    for result in results:
        marker = "WARN" if result.warning else "PASS" if result.passed else "FAIL"
        name = result.name if result.member is None else f"{result.member}: {result.name}"
        lines.append(f"[{marker}] {name}: {result.detail}")
    return "\n".join(lines)


def _scoped_result(result: CheckResult, scope: str) -> CheckResult:
    return CheckResult(result.name, result.passed, result.detail, scope)


def _scoped_results(results: Sequence[CheckResult], scope: str) -> list[CheckResult]:
    return [_scoped_result(result, scope) for result in results]


def _check_required_paths(root: Path, name: str, relative_paths: tuple[str, ...]) -> CheckResult:
    missing = [
        relative_path
        for relative_path in relative_paths
        if not required_path_exists(root, relative_path)
    ]
    if missing:
        return CheckResult(name, False, "missing " + ", ".join(missing))
    return CheckResult(name, True, "all required paths are present")


def _check_required_documentation_paths(
    root: Path,
    profile: ProfileName,
    config: Mapping[str, object] | None,
) -> CheckResult:
    required_paths = required_doc_paths(profile)
    if profile not in {"javascript-web-app", "python-js-app"}:
        return _check_required_paths(root, "documentation", required_paths)

    base_required = tuple(
        path for path in required_paths if path != JAVASCRIPT_STANDARD_DOC_PATHS[0]
    )
    missing = [
        relative_path for relative_path in base_required if not (root / relative_path).exists()
    ]
    if missing:
        return CheckResult("documentation", False, "missing " + ", ".join(missing))

    standard_doc_paths = _javascript_standard_doc_paths(config)
    if any((root / path).exists() for path in standard_doc_paths):
        return CheckResult("documentation", True, "all required paths are present")
    return CheckResult(
        "documentation",
        False,
        "missing " + " or ".join(standard_doc_paths),
    )


def _javascript_standard_doc_paths(config: Mapping[str, object] | None) -> tuple[str, ...]:
    configured_path = _configured_standard_doc_path(config, "javascript")
    if configured_path:
        return (configured_path,)
    return JAVASCRIPT_STANDARD_DOC_PATHS


def _configured_standard_doc_path(
    config: Mapping[str, object] | None,
    language: str,
) -> str | None:
    if config is None:
        return None
    documentation = config.get("documentation")
    if not isinstance(documentation, dict):
        return None
    documentation_config = cast(Mapping[str, object], documentation)
    standard_docs = documentation_config.get("standard_docs")
    if not isinstance(standard_docs, dict):
        return None
    standard_doc_config = cast(Mapping[str, object], standard_docs)
    value = standard_doc_config.get(language)
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _check_design_doc_status(root: Path) -> CheckResult:
    result = check_design_doc_status_policy(root)
    return CheckResult("design doc status", result.passed, result.detail)


def _check_no_env_file(root: Path) -> CheckResult:
    passed, detail = check_root_env_policy(root)
    return CheckResult("secret hygiene", passed, detail)


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


def _compatibility_pruning_config(config: Mapping[str, object] | None) -> object | None:
    if config is None:
        return None
    return config.get("compatibility_pruning")


def _pr_hygiene_config(config: Mapping[str, object] | None) -> object | None:
    if config is None:
        return None
    return config.get("pr_hygiene")


def _check_pyproject_backend(
    root: Path,
    pyproject: Mapping[str, object] | None,
    profile: ProfileName,
) -> CheckResult:
    if pyproject is None:
        return CheckResult("build backend", False, "pyproject.toml is missing")

    build_system_raw = pyproject.get("build-system")
    if not isinstance(build_system_raw, dict):
        return CheckResult("build backend", False, "pyproject.toml is missing [build-system]")
    build_system = cast(Mapping[str, object], build_system_raw)
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
    return _check_clang_format_settings(root, CLANG_FORMAT_REQUIRED_SETTINGS)


def _check_clang_format_settings(
    root: Path,
    required_settings: Mapping[str, str],
) -> CheckResult:
    path = root / ".clang-format"
    if not path.exists():
        return CheckResult("clang-format policy", False, ".clang-format is required")
    settings = _read_simple_yaml_map(path)
    missing_or_wrong = [
        f"{key}={value}" for key, value in required_settings.items() if settings.get(key) != value
    ]
    if missing_or_wrong:
        return CheckResult(
            "clang-format policy",
            False,
            "expected " + ", ".join(missing_or_wrong),
        )
    return CheckResult("clang-format policy", True, "formatter matches C++ baseline")


def _check_clang_tidy_policy(root: Path) -> CheckResult:
    passed, detail = check_clang_tidy_policy(root)
    return CheckResult("clang-tidy policy", passed, detail)


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


def _check_lizard_complexity_policy(root: Path) -> CheckResult:
    passed, detail = check_lizard_gate(root)
    return CheckResult("native complexity", passed, detail)


def _check_native_signoff_config(root: Path) -> CheckResult:
    passed, detail = check_native_signoff_config(root)
    return CheckResult("native signoff config", passed, detail)


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
