"""Shared test config fixture rendering."""

from __future__ import annotations

from textwrap import dedent

from wn_dev_std.standards import STANDARD_VERSION


def standard_config(profile: str | None = "python-package", extra: str = "") -> str:
    """Return standalone dev-std config TOML with the current standard version."""
    lines = [f'standard_version = "{STANDARD_VERSION}"']
    if profile is not None:
        lines.append(f'profile = "{profile}"')
    if extra.strip():
        lines.extend(["", dedent(extra).lstrip().rstrip()])
    return "\n".join(lines).rstrip() + "\n"


def standard_pyproject_tool_config(
    profile: str | None = "python-package",
    extra: str = "",
) -> str:
    """Return pyproject TOML containing a current [tool.wn_dev_std] config."""
    return "[tool.wn_dev_std]\n" + standard_config(profile, extra)
