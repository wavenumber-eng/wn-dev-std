"""Native-code complexity helpers for repository checks."""

from __future__ import annotations

from pathlib import Path

LIZARD_SIGNOFF_EXCLUDED_PARTS = {"__pycache__", ".venv", "rack_results"}
LIZARD_MISSING_DETAIL = "C/C++ projects require a Lizard complexity gate under tests/"


def check_lizard_gate(root: Path) -> tuple[bool, str]:
    """Return whether tests include a Lizard-based native complexity gate."""
    tests_dir = root / "tests"
    if tests_dir.exists():
        for path in tests_dir.rglob("*"):
            if _mentions_lizard(path):
                return True, "Lizard complexity gate is present"
    return False, LIZARD_MISSING_DETAIL


def _mentions_lizard(path: Path) -> bool:
    if not path.is_file() or any(part in LIZARD_SIGNOFF_EXCLUDED_PARTS for part in path.parts):
        return False
    try:
        return "lizard" in path.read_text(encoding="utf-8").lower()
    except UnicodeDecodeError:
        return False
