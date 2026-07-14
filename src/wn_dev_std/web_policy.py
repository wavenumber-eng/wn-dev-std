"""JavaScript and browser-app audit checks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from wn_dev_std.check_profiles import JAVASCRIPT_WEB_REQUIRED_PATHS, required_path_exists
from wn_dev_std.checks_types import CheckResult

JS_CSS_EXCLUDED_PARTS = {"vendor", "lib", "_build", "node_modules"}
STANDARD_COMMAND_VERBS = ("install", "update", "build", "test", "signoff")


def check_web_policy(root: Path) -> list[CheckResult]:
    """Return browser application policy checks."""
    return [
        _check_required_paths(root, "web app files", JAVASCRIPT_WEB_REQUIRED_PATHS),
        _check_web_source_policy(root),
        _check_web_typecheck_policy(root),
        _check_web_css_token_policy(root),
        _check_web_command_surface_policy(root),
        _check_web_signoff_policy(root),
    ]


def _check_required_paths(root: Path, name: str, relative_paths: tuple[str, ...]) -> CheckResult:
    missing = [
        relative_path
        for relative_path in relative_paths
        if not required_path_exists(root, relative_path)
    ]
    if missing:
        return CheckResult(name, False, "missing " + ", ".join(missing))
    return CheckResult(name, True, "all required paths are present")


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
