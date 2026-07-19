"""Shared standard profile model types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProfileName = Literal[
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
    "typescript-web-app",
    "python-ts-app",
    "rust-app",
    "rust-firmware",
    "zephyr-firmware",
]

STANDARD_VERSION = "2026.7.18"


@dataclass(frozen=True, slots=True)
class StrictRule:
    """A strict rule with a short rationale."""

    key: str
    value: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable rule dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class PythonStandard:
    """Current strict project standard profile."""

    name: str
    version: str
    status: str
    rules: tuple[StrictRule, ...]
    required_files: tuple[str, ...]
    required_docs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable standard dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "rules": [rule.to_dict() for rule in self.rules],
            "required_files": list(self.required_files),
            "required_docs": list(self.required_docs),
        }
