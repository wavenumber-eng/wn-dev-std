"""Secret hygiene helpers for repository checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def check_root_env_policy(root: Path) -> tuple[bool, str]:
    """Return whether a root .env file is absent or safely ignored."""
    if not (root / ".env").exists():
        return True, ".env is not present"
    if _git_returncode(root, "ls-files", "--error-unmatch", "--", ".env") == 0:
        return False, ".env is tracked and must be removed from git"
    ignored_status = _git_returncode(root, "check-ignore", "--quiet", "--", ".env")
    if ignored_status == 0:
        return True, ".env is present locally and ignored by git"
    if ignored_status is None:
        return False, ".env exists; git ignore status could not be verified"
    return False, ".env exists but is not ignored by git"


def _git_returncode(root: Path, *args: str) -> int | None:
    try:
        result = subprocess.run(
            ("git", *args),
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    return result.returncode
