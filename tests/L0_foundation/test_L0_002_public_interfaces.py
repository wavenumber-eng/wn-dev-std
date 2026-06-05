from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from wn_dev_std import (
    PythonStandard,
    StrictRule,
    default_cpp_standard,
    default_csharp_standard,
    default_javascript_web_standard,
    default_mixed_mode_standard,
    default_python_standard,
    default_standard,
    render_cpp_standard,
    render_csharp_standard,
    render_javascript_web_standard,
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


def test_default_csharp_standard_contains_dotnet_analyzer_rules() -> None:
    standard = default_csharp_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "build-system" and "dotnet" in rule.value for rule in standard.rules)
    assert any(rule.key == "complexity" and "CA1502" in rule.value for rule in standard.rules)
    assert ".editorconfig" in standard.required_files
    assert "Directory.Build.props" in standard.required_files


def test_default_javascript_web_standard_contains_no_build_rules() -> None:
    standard = default_javascript_web_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "workflow" and "no-build" in rule.value for rule in standard.rules)
    assert any(rule.key == "typecheck.javascript" for rule in standard.rules)
    assert any(rule.key == "test.javascript" for rule in standard.rules)
    assert any(rule.key == "css" for rule in standard.rules)
    assert any(rule.key == "css.tokens" for rule in standard.rules)
    assert any(rule.key == "web-components" for rule in standard.rules)
    assert any(rule.key == "wasm.testing" for rule in standard.rules)
    assert any(rule.key == "commands" for rule in standard.rules)
    assert "src" in standard.required_files
    assert "docs/design/javascript-standard.html" in standard.required_docs


def test_default_python_js_standard_contains_web_and_python_rules() -> None:
    standard = default_standard("python-js-app")
    assert isinstance(standard, PythonStandard)
    assert any(
        rule.key == "inherits" and rule.value == "javascript-web-app" for rule in standard.rules
    )
    assert any(rule.key == "server" for rule in standard.rules)
    assert "pyproject.toml" in standard.required_files


def test_default_standard_selects_profiles() -> None:
    assert default_standard("python-package").name == "python-package"
    assert default_standard("python-native-wasm").name == "python-native-wasm"
    assert default_standard("cpp-library").name == "cpp-library"
    assert default_standard("csharp-app").name == "csharp-app"
    assert default_standard("javascript-web-app").name == "javascript-web-app"
    assert default_standard("python-js-app").name == "python-js-app"


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


def test_render_csharp_standard_json_round_trips() -> None:
    rendered = render_csharp_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "csharp-app"
    assert parsed["version"] == "2026.6.4"


def test_render_javascript_web_standard_json_round_trips() -> None:
    rendered = render_javascript_web_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "javascript-web-app"
    assert parsed["version"] == "2026.6.4"


def test_render_standard_json_round_trips_for_named_profile() -> None:
    rendered = render_standard("python-js-app", "json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-js-app"


def test_cpp_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_cpp_repo(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_csharp_profile_basic_checks_pass_for_minimal_nested_project(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_javascript_web_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_javascript_web_project(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_python_js_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_compatibility_pruning_check_passes_for_clean_configured_repo(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    add_compatibility_pruning_config(tmp_path)

    results = run_basic_checks(tmp_path)
    pruning = next(result for result in results if result.name == "compatibility pruning")

    assert pruning.passed


def test_compatibility_pruning_check_fails_on_forbidden_reference(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    add_compatibility_pruning_config(tmp_path)
    write_file(
        tmp_path / "src" / "static" / "app.js",
        '// @ts-check\nconst root = "WN_LIBZ_ROOT";\nwindow.App = { root };\n',
    )

    results = run_basic_checks(tmp_path)
    pruning = next(result for result in results if result.name == "compatibility pruning")

    assert not pruning.passed
    assert "src/static/app.js:2" in pruning.detail
    assert "WN_LIBZ_ROOT" in pruning.detail


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


def write_minimal_csharp_project(root: Path) -> None:
    for relative_path in (
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "Directory.Build.props",
        "README.md",
        "build.ps1",
        "docs/setup.html",
        "docs/architecture.html",
    ):
        write_file(root / relative_path, "placeholder\n")
    for relative_dir in ("docs/design", "docs/contracts", "docs/releases"):
        (root / relative_dir).mkdir(parents=True, exist_ok=True)
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            """
            profile = "csharp-app"
            distribution = "internal"
            languages = ["csharp"]
            strict = true
            artifact_policy = "committed-extension-dist"
            """
        ).lstrip(),
    )
    write_file(
        root / "Directory.Build.props",
        dedent(
            """
            <Project>
              <PropertyGroup>
                <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
                <EnableNETAnalyzers>true</EnableNETAnalyzers>
              </PropertyGroup>
            </Project>
            """
        ).lstrip(),
    )
    write_file(
        root / ".editorconfig",
        dedent(
            """
            root = true

            [*.cs]
            dotnet_diagnostic.CA1502.severity = error
            dotnet_diagnostic.CA1505.severity = error
            dotnet_diagnostic.CA1506.severity = error
            """
        ).lstrip(),
    )
    write_file(root / "src" / "app" / "app.csproj", '<Project Sdk="Microsoft.NET.Sdk" />\n')
    write_file(
        root / "tests" / "app.tests" / "app.tests.csproj",
        '<Project Sdk="Microsoft.NET.Sdk" />\n',
    )


def write_minimal_web_files(root: Path) -> None:
    for relative_path in (
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "README.md",
        "tests/rack.toml",
        "docs/setup.html",
        "docs/architecture.html",
        "docs/design/javascript-standard.html",
        "scripts/js_hygiene.py",
        "scripts/css_hygiene.py",
        "scripts/dev.py",
        "jsconfig.json",
    ):
        write_file(root / relative_path, "placeholder\n")
    for relative_dir in ("docs/design", "docs/contracts", "docs/releases"):
        (root / relative_dir).mkdir(parents=True, exist_ok=True)
    write_file(root / "src" / "static" / "app.js", "// @ts-check\nwindow.App = {};\n")
    write_file(
        root / "src" / "static" / "style.css",
        ":root { --wn-space-0: 0; }\nbody { margin: var(--wn-space-0); }\n",
    )
    write_file(root / "src" / "static" / "vendor" / "dep.min.js", "/* vendor */\n")
    write_file(
        root / "scripts" / "dev.py",
        "COMMANDS = ('install', 'update', 'build', 'test', 'signoff')\n",
    )
    write_file(
        root / "jsconfig.json",
        dedent(
            """
            {
              "compilerOptions": {
                "allowJs": true,
                "checkJs": true,
                "noEmit": true
              },
              "include": ["src/**/*.js"]
            }
            """
        ).lstrip(),
    )


def write_minimal_javascript_web_project(root: Path) -> None:
    write_minimal_web_files(root)
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            """
            profile = "javascript-web-app"
            distribution = "internal"
            languages = ["javascript", "css", "html"]
            strict = true
            artifact_policy = "transient-dist"
            """
        ).lstrip(),
    )


def write_minimal_python_js_project(root: Path) -> None:
    write_minimal_web_files(root)
    write_file(root / "CHANGELOG.md", "placeholder\n")
    write_file(root / "CONTRIBUTING.md", "placeholder\n")
    write_file(root / "LICENSE", "placeholder\n")
    write_file(root / "uv.lock", "placeholder\n")
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            """
            profile = "python-js-app"
            distribution = "internal"
            languages = ["python", "javascript", "css", "html"]
            strict = true
            artifact_policy = "transient-dist"
            """
        ).lstrip(),
    )
    write_file(
        root / "pyproject.toml",
        dedent(
            """
            [project]
            name = "example"
            version = "0.1.0"

            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"
            """
        ).lstrip(),
    )


def add_compatibility_pruning_config(root: Path) -> None:
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            r"""
            profile = "python-js-app"
            distribution = "internal"
            languages = ["python", "javascript", "css", "html"]
            strict = true
            artifact_policy = "transient-dist"

            [compatibility_pruning]
            root = "."
            forbidden_patterns = [
              "\\bWN_LIBZ_ROOT\\b",
              "\\bwn_pcb\\b",
            ]
            excluded_parts = ["test_cases"]
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
