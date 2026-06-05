"""Configurable pruning checks for retired compatibility surfaces."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class CompatibilityPruningCheck:
    """Result payload for the compatibility pruning policy."""

    passed: bool
    detail: str


DEFAULT_PRUNING_EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "_build",
    "build",
    "dist",
    "node_modules",
    "out",
    "rack_results",
}
DEFAULT_PRUNING_TEXT_SUFFIXES = (
    ".bat",
    ".cmd",
    ".cfg",
    ".cs",
    ".csproj",
    ".css",
    ".editorconfig",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".props",
    ".ps1",
    ".py",
    ".sh",
    ".targets",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
)
DEFAULT_PRUNING_TEXT_NAMES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "Makefile",
    "makefile",
    "README.md",
)
DEFAULT_PRUNING_EXCLUDED_NAMES = (
    "pyproject.toml",
    "wn-dev-std.toml",
)
CandidatePolicy = tuple[set[str], set[str], set[str], tuple[str, ...], tuple[str, ...]]


def check_compatibility_pruning_policy(
    root: Path,
    raw_config: object,
) -> CompatibilityPruningCheck:
    """Scan for configured compatibility surfaces that should stay removed."""
    config = _config_mapping(raw_config)
    if config is None:
        return _fail("compatibility_pruning must be a TOML table")

    patterns_or_error = _compiled_patterns(config)
    if isinstance(patterns_or_error, str):
        return _fail(patterns_or_error)
    if not patterns_or_error:
        return _fail("compatibility_pruning.forbidden_patterns is required")

    scan_root = _pruning_root(root, config)
    if not scan_root.exists():
        return _fail(f"scan root does not exist: {scan_root}")

    violations, scanned_count = _scan_for_violations(scan_root, config, patterns_or_error)
    if violations:
        return _fail(_violation_detail(violations))
    return CompatibilityPruningCheck(
        True,
        f"scanned {scanned_count} file(s) for {len(patterns_or_error)} forbidden pattern(s)",
    )


def _fail(detail: str) -> CompatibilityPruningCheck:
    return CompatibilityPruningCheck(False, detail)


def _config_mapping(raw_config: object) -> dict[str, object] | None:
    if isinstance(raw_config, dict):
        return cast(dict[str, object], raw_config)
    return None


def _compiled_patterns(config: dict[str, object]) -> tuple[re.Pattern[str], ...] | str:
    raw_patterns = _string_list(config.get("forbidden_patterns"))
    if raw_patterns is None:
        return ()

    compiled: list[re.Pattern[str]] = []
    for pattern in raw_patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as exc:
            return f"invalid forbidden pattern {pattern!r}: {exc}"
    return tuple(compiled)


def _pruning_root(root: Path, config: dict[str, object]) -> Path:
    raw_root = config.get("root")
    if isinstance(raw_root, str):
        return (root / raw_root).resolve()
    return root


def _scan_for_violations(
    root: Path,
    config: dict[str, object],
    patterns: tuple[re.Pattern[str], ...],
) -> tuple[list[str], int]:
    violations: list[str] = []
    scanned_count = 0
    for path in _candidate_files(root, config):
        scanned_count += 1
        violations.extend(_path_violations(root, path, patterns))
    return violations, scanned_count


def _candidate_files(root: Path, config: dict[str, object]) -> list[Path]:
    policy = _candidate_policy(config)
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if _should_scan(path, root, policy):
            files.append(path)
    return files


def _candidate_policy(config: dict[str, object]) -> CandidatePolicy:
    excluded_parts = DEFAULT_PRUNING_EXCLUDED_PARTS | set(
        _string_list(config.get("excluded_parts")) or ()
    )
    excluded_paths = {
        _normalize_relative_path(path) for path in _string_list(config.get("excluded_paths")) or ()
    }
    excluded_names = set(DEFAULT_PRUNING_EXCLUDED_NAMES) | set(
        _string_list(config.get("excluded_names")) or ()
    )
    suffixes = tuple(_string_list(config.get("suffixes")) or DEFAULT_PRUNING_TEXT_SUFFIXES)
    names = tuple(_string_list(config.get("names")) or DEFAULT_PRUNING_TEXT_NAMES)
    return excluded_parts, excluded_paths, excluded_names, suffixes, names


def _should_scan(
    path: Path,
    root: Path,
    policy: CandidatePolicy,
) -> bool:
    excluded_parts, excluded_paths, excluded_names, suffixes, names = policy
    if not path.is_file():
        return False
    relative_path = path.relative_to(root)
    if path.name in excluded_names:
        return False
    if relative_path.as_posix() in excluded_paths:
        return False
    if excluded_parts & set(relative_path.parts):
        return False
    return path.name in names or path.suffix.lower() in suffixes


def _path_violations(
    root: Path,
    path: Path,
    patterns: tuple[re.Pattern[str], ...],
) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError:
        return []

    relative_path = path.relative_to(root).as_posix()
    violations: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        violations.extend(_line_violations(relative_path, line_number, line, patterns))
    return violations


def _line_violations(
    relative_path: str,
    line_number: int,
    line: str,
    patterns: tuple[re.Pattern[str], ...],
) -> list[str]:
    return [
        f"{relative_path}:{line_number}: {pattern.pattern}"
        for pattern in patterns
        if pattern.search(line)
    ]


def _violation_detail(violations: list[str]) -> str:
    shown = violations[:10]
    extra = "" if len(violations) <= len(shown) else f"; +{len(violations) - len(shown)} more"
    return "forbidden compatibility references found: " + "; ".join(shown) + extra


def _string_list(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    raw_items = cast(list[object], value)
    if not all(isinstance(item, str) for item in raw_items):
        return None
    return tuple(cast(str, item) for item in raw_items)


def _normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")
