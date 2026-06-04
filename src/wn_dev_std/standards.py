"""Python standard data exposed by the reference package."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal


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
    """Current strict Python package standard."""

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


def default_python_standard() -> PythonStandard:
    """Return the current strict Python package standard."""
    return PythonStandard(
        name="python-package",
        version="2026.6.4",
        status="initial",
        rules=(
            StrictRule("workflow", "uv", "Use one environment and lock workflow."),
            StrictRule("lockfile", "commit uv.lock", "Make installs reproducible."),
            StrictRule("build-backend", "hatchling", "Use modern pyproject-native builds."),
            StrictRule("test-runner", "rack", "Keep strata, concerns, and signoff explicit."),
            StrictRule("typing", "pyright strict", "Catch interface drift early."),
            StrictRule("lint", "ruff", "Keep style and common bug checks automated."),
            StrictRule("complexity.production", "<= 8", "Favor simple, reviewable functions."),
            StrictRule("complexity.tests", "<= 10", "Tests may orchestrate more setup."),
            StrictRule("docs.design", "HTML", "Keep docs human-readable and machine-checkable."),
            StrictRule("release", "GitHub Release published", "Allow final review before publish."),
            StrictRule("ci.os", "ubuntu, windows, macos", "Catch platform differences early."),
        ),
        required_files=(
            ".gitattributes",
            ".gitignore",
            "AGENTS.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "README.md",
            "pyproject.toml",
        ),
        required_docs=(
            "docs/setup.html",
            "docs/architecture.html",
            "docs/design/",
            "docs/contracts/",
            "docs/releases/",
        ),
    )


def render_python_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current Python standard as text or JSON."""
    standard = default_python_standard()
    if output_format == "json":
        return json.dumps(standard.to_dict(), indent=2, sort_keys=True)

    lines = [
        f"{standard.name} {standard.version} ({standard.status})",
        "",
        "Rules:",
    ]
    for rule in standard.rules:
        lines.append(f"- {rule.key}: {rule.value} ({rule.rationale})")
    lines.append("")
    lines.append("Required files:")
    lines.extend(f"- {path}" for path in standard.required_files)
    lines.append("")
    lines.append("Required docs:")
    lines.extend(f"- {path}" for path in standard.required_docs)
    return "\n".join(lines)
