"""Repository conformance checks used by the example CLI."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast


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


def run_basic_checks(root: Path) -> tuple[CheckResult, ...]:
    """Run lightweight repository checks for a Python standards project."""
    resolved_root = root.resolve()
    checks = [
        _check_required_paths(resolved_root, "root files", REQUIRED_ROOT_FILES),
        _check_required_paths(resolved_root, "documentation", REQUIRED_DOC_PATHS),
        _check_required_paths(resolved_root, "rack suite", ("tests/rack.toml",)),
        _check_no_env_file(resolved_root),
        _check_uv_lock(resolved_root),
        _check_pyproject_backend(resolved_root),
    ]
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


def _check_uv_lock(root: Path) -> CheckResult:
    if (root / "uv.lock").exists():
        return CheckResult("uv lock", True, "uv.lock is committed")
    return CheckResult("uv lock", False, "uv.lock is required for reproducible installs")


def _check_pyproject_backend(root: Path) -> CheckResult:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return CheckResult("build backend", False, "pyproject.toml is missing")

    with pyproject_path.open("rb") as handle:
        pyproject = cast(Mapping[str, object], tomllib.load(handle))
    build_system = _mapping(pyproject.get("build-system"), "build-system")
    backend = build_system.get("build-backend")
    if backend == "hatchling.build":
        return CheckResult("build backend", True, "pure Python package uses Hatchling")
    return CheckResult("build backend", False, "expected build-backend = hatchling.build")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise ValueError(f"expected [{label}] to be a mapping")
