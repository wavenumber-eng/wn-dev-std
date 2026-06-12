"""Native-code complexity helpers for repository checks."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import cast

LIZARD_SIGNOFF_EXCLUDED_PARTS = {"__pycache__", ".venv", "rack_results"}
LIZARD_MISSING_DETAIL = "C/C++ projects require a Lizard complexity gate under tests/"
MAX_FILE_LINES = 2200
MAX_FUNCTION_LINES = 220
MAX_CYCLOMATIC_COMPLEXITY = 10


def check_lizard_gate(root: Path) -> tuple[bool, str]:
    """Return whether tests include a Lizard-based native complexity gate."""
    tests_dir = root / "tests"
    if tests_dir.exists():
        for path in tests_dir.rglob("*"):
            if _mentions_lizard(path):
                return True, "Lizard complexity gate is present"
    return False, LIZARD_MISSING_DETAIL


def check_native_signoff_config(root: Path) -> tuple[bool, str]:
    """Return whether signoff.toml carries canonical native code limits."""
    path = root / "signoff.toml"
    if not path.exists():
        return False, "signoff.toml is required for native signoff"

    try:
        with path.open("rb") as handle:
            data = cast(Mapping[str, object], tomllib.load(handle))

        limits = _mapping(data.get("limits"), "limits")
        tools = _mapping(data.get("tools"), "tools")
    except (tomllib.TOMLDecodeError, ValueError) as exc:
        return False, f"invalid native signoff config: {exc}"
    problems: list[str] = []
    _check_upper_limit(
        limits,
        "max_file_lines",
        MAX_FILE_LINES,
        problems,
    )
    _check_upper_limit(
        limits,
        "max_function_lines",
        MAX_FUNCTION_LINES,
        problems,
    )
    _check_upper_limit(
        limits,
        "max_cyclomatic_complexity",
        MAX_CYCLOMATIC_COMPLEXITY,
        problems,
    )
    if _string(tools.get("lizard")) != "fail":
        problems.append("tools.lizard must be fail")
    if _string(tools.get("clang_format")) not in {"report", "fail"}:
        problems.append("tools.clang_format must be report or fail")
    if _string(tools.get("clang_tidy")) not in {"report", "fail"}:
        problems.append("tools.clang_tidy must be report or fail")

    if problems:
        return False, "expected " + ", ".join(problems)
    return (
        True,
        "signoff.toml sets lizard fail and canonical native limits "
        f"(cc<={MAX_CYCLOMATIC_COMPLEXITY})",
    )


def _mentions_lizard(path: Path) -> bool:
    if not path.is_file() or any(part in LIZARD_SIGNOFF_EXCLUDED_PARTS for part in path.parts):
        return False
    try:
        return "lizard" in path.read_text(encoding="utf-8").lower()
    except UnicodeDecodeError:
        return False


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise ValueError(f"expected [{label}] to be a mapping")


def _check_upper_limit(
    limits: Mapping[str, object],
    key: str,
    maximum: int,
    problems: list[str],
) -> None:
    value = limits.get(key)
    if type(value) is not int:
        problems.append(f"limits.{key} must be integer <= {maximum}")
        return
    if value > maximum:
        problems.append(f"limits.{key} must be <= {maximum}")


def _string(value: object) -> str:
    if isinstance(value, str):
        return value
    return ""
