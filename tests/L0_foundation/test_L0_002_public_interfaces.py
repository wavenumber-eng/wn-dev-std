from __future__ import annotations

import json

from wn_dev_std import (
    PythonStandard,
    StrictRule,
    default_python_standard,
    render_python_standard,
)


def test_default_python_standard_contains_strict_rules() -> None:
    standard = default_python_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "typing" and rule.value == "pyright strict" for rule in standard.rules)
    assert "AGENTS.md" in standard.required_files


def test_strict_rule_serializes_to_json_ready_dict() -> None:
    rule = StrictRule("complexity.production", "<= 8", "Keep functions reviewable.")
    assert rule.to_dict() == {
        "key": "complexity.production",
        "value": "<= 8",
        "rationale": "Keep functions reviewable.",
    }


def test_render_python_standard_json_round_trips() -> None:
    rendered = render_python_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-package"
    assert parsed["version"] == "2026.6.4"
