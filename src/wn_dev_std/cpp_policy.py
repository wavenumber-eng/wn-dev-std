"""C++ policy helpers for repository checks."""

from __future__ import annotations

from pathlib import Path

CLANG_TIDY_REQUIRED_CHECKS = ("google-runtime-int",)


def check_clang_tidy_policy(root: Path) -> tuple[bool, str]:
    """Return whether clang-tidy enforces required C++ checks."""
    path = root / ".clang-tidy"
    if not path.exists():
        return False, ".clang-tidy is required"
    text = path.read_text(encoding="utf-8")
    checks = _clang_tidy_field_value(text, "Checks")
    warnings_as_errors = _clang_tidy_field_value(text, "WarningsAsErrors")
    missing_checks = [check for check in CLANG_TIDY_REQUIRED_CHECKS if check not in checks]
    if missing_checks:
        return False, "expected Checks to include " + ", ".join(missing_checks)
    missing_errors = [
        check for check in CLANG_TIDY_REQUIRED_CHECKS if check not in warnings_as_errors
    ]
    if missing_errors:
        return False, "expected WarningsAsErrors to include " + ", ".join(missing_errors)
    return True, "google-runtime-int is configured as an error"


def _clang_tidy_field_value(text: str, field: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped.startswith(f"{field}:"):
            continue
        _, remainder = stripped.split(":", 1)
        values = [remainder.strip()]
        for child in lines[index + 1 :]:
            if child.strip() and not child[0].isspace() and ":" in child:
                break
            values.append(child.strip())
        return "\n".join(values)
    return ""
