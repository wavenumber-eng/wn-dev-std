"""Rust standard profile factories."""

from __future__ import annotations

from typing import Literal

from wn_dev_std.rust_standard_data import (
    RUST_APP_REQUIRED_FILES,
    RUST_APP_RULE_ITEMS,
    RUST_FIRMWARE_REQUIRED_FILES,
    RUST_FIRMWARE_RULE_ITEMS,
    RUST_REQUIRED_DOCS,
)
from wn_dev_std.standard_model import STANDARD_VERSION, PythonStandard, StrictRule

COMPATIBILITY_PRUNING_RULE = StrictRule(
    "compatibility-pruning",
    "configured forbidden legacy surface",
    "Old compatibility shims, environment variables, and aliases need a signoff gate.",
)
PUBLIC_PR_HYGIENE_RULE = StrictRule(
    "pr-hygiene.public",
    "linked issue + Conventional Commit CI",
    "Public PRs need reviewable issue context and machine-checkable metadata.",
)
RUST_APP_RULES = (
    *(StrictRule(key, value, rationale) for key, value, rationale in RUST_APP_RULE_ITEMS),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
)
RUST_FIRMWARE_RULES = (
    *(StrictRule(key, value, rationale) for key, value, rationale in RUST_FIRMWARE_RULE_ITEMS),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
)


def default_rust_app_standard() -> PythonStandard:
    """Return the current host-side Rust application and library standard."""
    return PythonStandard(
        name="rust-app",
        version=STANDARD_VERSION,
        status="initial",
        rules=RUST_APP_RULES,
        required_files=RUST_APP_REQUIRED_FILES,
        required_docs=RUST_REQUIRED_DOCS,
    )


def default_rust_firmware_standard() -> PythonStandard:
    """Return the current embedded Rust firmware standard."""
    return PythonStandard(
        name="rust-firmware",
        version=STANDARD_VERSION,
        status="initial",
        rules=RUST_FIRMWARE_RULES,
        required_files=RUST_FIRMWARE_REQUIRED_FILES,
        required_docs=RUST_REQUIRED_DOCS,
    )


def render_rust_app_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current host-side Rust standard as text or JSON."""
    from wn_dev_std.standards import render_standard

    return render_standard("rust-app", output_format)


def render_rust_firmware_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current embedded Rust firmware standard as text or JSON."""
    from wn_dev_std.standards import render_standard

    return render_standard("rust-firmware", output_format)
