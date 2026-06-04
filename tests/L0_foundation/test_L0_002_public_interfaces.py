from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from wn_dev_std import (
    PythonStandard,
    StrictRule,
    default_cpp_standard,
    default_mixed_mode_standard,
    default_python_standard,
    default_standard,
    render_cpp_standard,
    render_mixed_mode_standard,
    render_python_standard,
    render_standard,
)
from wn_dev_std.checks import run_basic_checks


def test_default_python_standard_contains_strict_rules() -> None:
    standard = default_python_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "typing" and rule.value == "pyright strict" for rule in standard.rules)
    assert "AGENTS.md" in standard.required_files


def test_default_mixed_mode_standard_contains_native_and_wasm_rules() -> None:
    standard = default_mixed_mode_standard()
    assert isinstance(standard, PythonStandard)
    assert any(
        rule.key == "workflow.native" and rule.value == "cmake + ctest" for rule in standard.rules
    )
    assert any(rule.key == "wasm-artifacts" for rule in standard.rules)
    assert "CMakeLists.txt" in standard.required_files


def test_default_cpp_standard_contains_formatter_and_preset_rules() -> None:
    standard = default_cpp_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "generator" and rule.value == "ninja" for rule in standard.rules)
    assert any(rule.key == "format.style" for rule in standard.rules)
    assert ".clang-format" in standard.required_files
    assert "CMakePresets.json" in standard.required_files


def test_default_standard_selects_profiles() -> None:
    assert default_standard("python-package").name == "python-package"
    assert default_standard("python-native-wasm").name == "python-native-wasm"
    assert default_standard("cpp-library").name == "cpp-library"


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


def test_render_mixed_mode_standard_json_round_trips() -> None:
    rendered = render_mixed_mode_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-native-wasm"
    assert parsed["version"] == "2026.6.4"


def test_render_cpp_standard_json_round_trips() -> None:
    rendered = render_cpp_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "cpp-library"
    assert parsed["version"] == "2026.6.4"


def test_render_standard_json_round_trips_for_named_profile() -> None:
    rendered = render_standard("cpp-library", "json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "cpp-library"


def test_cpp_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_cpp_repo(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def write_minimal_cpp_repo(root: Path) -> None:
    for relative_path in (
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "README.md",
        ".clang-tidy",
        "CMakeLists.txt",
        "tests/rack.toml",
        "docs/setup.html",
        "docs/architecture.html",
    ):
        write_file(root / relative_path, "placeholder\n")
    for relative_dir in ("docs/design", "docs/contracts", "docs/releases"):
        (root / relative_dir).mkdir(parents=True, exist_ok=True)

    write_file(
        root / "pyproject.toml",
        dedent(
            """
            [tool.wn_dev_std]
            profile = "cpp-library"
            """
        ).lstrip(),
    )
    write_file(
        root / ".clang-format",
        dedent(
            """
            BasedOnStyle: LLVM
            BreakBeforeBraces: Allman
            IndentWidth: 4
            ColumnLimit: 100
            PointerAlignment: Left
            SortIncludes: true
            IncludeBlocks: Preserve
            """
        ).lstrip(),
    )
    write_file(
        root / "CMakePresets.json",
        dedent(
            """
            {
              "version": 6,
              "configurePresets": [
                {
                  "name": "default",
                  "generator": "Ninja",
                  "binaryDir": "${sourceDir}/build",
                  "cacheVariables": {
                    "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
                  }
                }
              ]
            }
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
