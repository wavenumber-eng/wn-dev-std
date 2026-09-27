"""Dependency-free safety checks shared by packaging and release tests."""

from __future__ import annotations

from pathlib import Path

IGNORED_WORKING_DIRECTORIES = (
    ".cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
)
SENSITIVE_NAMES = frozenset({".npmrc", ".pypirc", "credentials.json", "secrets.json"})
SENSITIVE_SUFFIXES = frozenset({".key", ".p12", ".pem", ".pfx"})


def sensitive_template_files(source: Path) -> tuple[Path, ...]:
    """Return non-transient template files that may contain credentials or keys."""
    offenders: list[Path] = []
    for path in source.rglob("*"):
        if not path.is_file() or set(path.parts).intersection(IGNORED_WORKING_DIRECTORIES):
            continue
        name = path.name.lower()
        env_secret = name == ".env" or (name.startswith(".env.") and name != ".env.example")
        if env_secret or name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
            offenders.append(path)
    return tuple(sorted(offenders))
