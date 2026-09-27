"""Shared rendering for profile and capability standards."""

from __future__ import annotations

import json
from typing import Literal

from wn_dev_std.standard_model import PythonStandard


def render_standard_data(
    standard: PythonStandard,
    output_format: Literal["text", "json"],
) -> str:
    """Render standard data as text or JSON."""
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
