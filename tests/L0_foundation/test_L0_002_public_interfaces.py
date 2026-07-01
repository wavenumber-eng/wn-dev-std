from __future__ import annotations

import json
import subprocess
from pathlib import Path
from textwrap import dedent

from wn_dev_std import (
    PythonStandard,
    StrictRule,
    __version__,
    default_cpp_standard,
    default_csharp_standard,
    default_javascript_web_standard,
    default_mixed_mode_standard,
    default_python_standard,
    default_standard,
    default_zephyr_standard,
    render_cpp_standard,
    render_csharp_standard,
    render_javascript_web_standard,
    render_mixed_mode_standard,
    render_python_standard,
    render_standard,
    render_zephyr_standard,
)
from wn_dev_std.checks import run_basic_checks
from wn_dev_std.pr_hygiene import (
    check_pr_hygiene_policy,
    conventional_subject_pattern,
    is_conventional_subject,
)

ROOT = Path(__file__).resolve().parents[2]


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
    assert any(rule.key == "complexity.native" and "<= 10" in rule.value for rule in standard.rules)
    assert any(rule.key == "wasm-artifacts" for rule in standard.rules)
    assert "CMakeLists.txt" in standard.required_files


def test_default_cpp_standard_contains_formatter_and_preset_rules() -> None:
    standard = default_cpp_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "generator" and rule.value == "ninja" for rule in standard.rules)
    assert any(rule.key == "format.style" for rule in standard.rules)
    assert any(rule.key == "integer-widths" for rule in standard.rules)
    assert any(rule.key == "complexity.native" and "<= 10" in rule.value for rule in standard.rules)
    assert ".clang-format" in standard.required_files
    assert "CMakePresets.json" in standard.required_files
    assert "signoff.toml" in standard.required_files


def test_default_zephyr_standard_contains_embedded_signoff_rules() -> None:
    standard = default_zephyr_standard()
    assert isinstance(standard, PythonStandard)
    assert any(rule.key == "inherits" and rule.value == "cpp-library" for rule in standard.rules)
    assert any(rule.key == "complexity.native" and "<= 10" in rule.value for rule in standard.rules)
    assert any(rule.key == "target-toolchains" for rule in standard.rules)
    assert "signoff.toml" in standard.required_files
    assert "docs/design/zephyr-standard.html" in standard.required_docs


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
    assert any(rule.key == "docs.javascript-standard" for rule in standard.rules)
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
    assert default_standard("zephyr-firmware").name == "zephyr-firmware"


def test_strict_rule_serializes_to_json_ready_dict() -> None:
    rule = StrictRule("complexity.production", "<= 8", "Keep functions reviewable.")
    assert rule.to_dict() == {
        "key": "complexity.production",
        "value": "<= 8",
        "rationale": "Keep functions reviewable.",
    }


def test_pr_hygiene_subject_validation_uses_conventional_commits() -> None:
    assert is_conventional_subject("fix: handle missing board outline")
    assert is_conventional_subject("feat(kicad): add HTTP library setup")
    assert is_conventional_subject("ci!: require linked issues")
    assert not is_conventional_subject("Handle missing board outline")
    assert not is_conventional_subject("misc: update things")
    assert "build|chore|ci|deps|docs|feat|fix" in conventional_subject_pattern()


def test_render_python_standard_json_round_trips() -> None:
    rendered = render_python_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-package"
    assert parsed["version"] == __version__


def test_render_mixed_mode_standard_json_round_trips() -> None:
    rendered = render_mixed_mode_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-native-wasm"
    assert parsed["version"] == __version__


def test_render_cpp_standard_json_round_trips() -> None:
    rendered = render_cpp_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "cpp-library"
    assert parsed["version"] == __version__


def test_render_csharp_standard_json_round_trips() -> None:
    rendered = render_csharp_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "csharp-app"
    assert parsed["version"] == __version__


def test_render_javascript_web_standard_json_round_trips() -> None:
    rendered = render_javascript_web_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "javascript-web-app"
    assert parsed["version"] == __version__


def test_render_standard_json_round_trips_for_named_profile() -> None:
    rendered = render_standard("python-js-app", "json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "python-js-app"


def test_render_zephyr_standard_json_round_trips() -> None:
    rendered = render_zephyr_standard("json")
    parsed = json.loads(rendered)
    assert parsed["name"] == "zephyr-firmware"
    assert parsed["version"] == __version__


def test_cpp_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_cpp_repo(tmp_path)
    results = run_basic_checks(tmp_path)
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_cpp_profile_requires_lizard_complexity_gate(tmp_path: Path) -> None:
    write_minimal_cpp_repo(tmp_path, include_lizard=False)
    results = run_basic_checks(tmp_path)
    complexity = next(result for result in results if result.name == "native complexity")

    assert not complexity.passed
    assert "Lizard complexity gate" in complexity.detail


def test_cpp_profile_requires_canonical_native_signoff_limit(tmp_path: Path) -> None:
    write_minimal_cpp_repo(tmp_path, max_cyclomatic_complexity=35)
    results = run_basic_checks(tmp_path)
    signoff = next(result for result in results if result.name == "native signoff config")

    assert not signoff.passed
    assert "max_cyclomatic_complexity" in signoff.detail
    assert "<= 10" in signoff.detail


def test_zephyr_profile_basic_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_zephyr_project(tmp_path)
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


def test_python_js_profile_accepts_foldered_javascript_standard_doc(
    tmp_path: Path,
) -> None:
    write_minimal_python_js_project(tmp_path)
    (tmp_path / "docs" / "design" / "javascript-standard.html").unlink()
    write_file(
        tmp_path / "docs" / "design" / "standards" / "javascript.html",
        (
            '<!doctype html><html><body data-doc-status="accepted">'
            "<h1>JavaScript Standard</h1></body></html>\n"
        ),
    )

    results = run_basic_checks(tmp_path)
    documentation = next(result for result in results if result.name == "documentation")

    assert documentation.passed
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_python_js_profile_accepts_configured_javascript_standard_doc(
    tmp_path: Path,
) -> None:
    write_minimal_python_js_project(tmp_path)
    (tmp_path / "docs" / "design" / "javascript-standard.html").unlink()
    write_file(
        tmp_path / "docs" / "design" / "project" / "javascript-standard.html",
        (
            '<!doctype html><html><body data-doc-status="accepted">'
            "<h1>JavaScript Standard</h1></body></html>\n"
        ),
    )
    write_file(
        tmp_path / "wn-dev-std.toml",
        (tmp_path / "wn-dev-std.toml").read_text(encoding="utf-8")
        + (
            "\n[documentation.standard_docs]\n"
            'javascript = "docs/design/project/javascript-standard.html"\n'
        ),
    )

    results = run_basic_checks(tmp_path)
    documentation = next(result for result in results if result.name == "documentation")

    assert documentation.passed
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_python_js_profile_reports_javascript_standard_doc_alternatives(
    tmp_path: Path,
) -> None:
    write_minimal_python_js_project(tmp_path)
    (tmp_path / "docs" / "design" / "javascript-standard.html").unlink()

    results = run_basic_checks(tmp_path)
    documentation = next(result for result in results if result.name == "documentation")

    assert not documentation.passed
    assert "docs/design/javascript-standard.html" in documentation.detail
    assert "docs/design/standards/javascript.html" in documentation.detail


def test_secret_hygiene_passes_for_ignored_local_env(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    write_file(tmp_path / ".gitignore", ".env\n")
    write_file(tmp_path / ".env", "R2_SECRET_ACCESS_KEY=test\n")
    init_git_repo(tmp_path)

    results = run_basic_checks(tmp_path)
    secret = next(result for result in results if result.name == "secret hygiene")

    assert secret.passed
    assert "ignored by git" in secret.detail


def test_secret_hygiene_fails_for_non_ignored_env(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    write_file(tmp_path / ".env", "R2_SECRET_ACCESS_KEY=test\n")
    init_git_repo(tmp_path)

    results = run_basic_checks(tmp_path)
    secret = next(result for result in results if result.name == "secret hygiene")

    assert not secret.passed
    assert "not ignored" in secret.detail


def test_secret_hygiene_fails_for_tracked_env(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    write_file(tmp_path / ".gitignore", ".env\n")
    write_file(tmp_path / ".env", "R2_SECRET_ACCESS_KEY=test\n")
    init_git_repo(tmp_path)
    run_git(tmp_path, "add", "-f", ".env")

    results = run_basic_checks(tmp_path)
    secret = next(result for result in results if result.name == "secret hygiene")

    assert not secret.passed
    assert "tracked" in secret.detail


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


def test_pr_hygiene_policy_passes_for_installed_templates(tmp_path: Path) -> None:
    install_pr_hygiene_templates(tmp_path)

    result = check_pr_hygiene_policy(tmp_path, {"enabled": True})

    assert result.passed


def test_pr_hygiene_policy_fails_when_workflow_is_missing(tmp_path: Path) -> None:
    result = check_pr_hygiene_policy(tmp_path, {"enabled": True})

    assert not result.passed
    assert ".github/workflows/pr-hygiene.yml" in result.detail


def test_pr_hygiene_check_runs_when_configured(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    install_pr_hygiene_templates(tmp_path)
    write_file(
        tmp_path / "wn-dev-std.toml",
        (tmp_path / "wn-dev-std.toml").read_text(encoding="utf-8")
        + "\n[pr_hygiene]\nenabled = true\n",
    )

    results = run_basic_checks(tmp_path)
    hygiene = next(result for result in results if result.name == "public PR hygiene")

    assert hygiene.passed
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_design_doc_status_check_fails_on_unmarked_html(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    write_file(
        tmp_path / "docs" / "design" / "draft-topic.html",
        "<!doctype html><html><body><h1>Draft Topic</h1></body></html>\n",
    )

    results = run_basic_checks(tmp_path)
    status = next(result for result in results if result.name == "design doc status")

    assert not status.passed
    assert "missing data-doc-status" in status.detail
    assert "docs/design/draft-topic.html" in status.detail


def test_design_doc_status_check_reports_draft_and_proposal_docs(tmp_path: Path) -> None:
    write_minimal_python_js_project(tmp_path)
    write_file(
        tmp_path / "docs" / "design" / "draft-topic.html",
        ('<!doctype html><html><body data-doc-status="draft"><h1>Draft Topic</h1></body></html>\n'),
    )
    write_file(
        tmp_path / "docs" / "design" / "proposal-topic.html",
        (
            '<!doctype html><html><main data-doc-status="proposal">'
            "<h1>Proposal Topic</h1></main></html>\n"
        ),
    )

    results = run_basic_checks(tmp_path)
    status = next(result for result in results if result.name == "design doc status")

    assert status.passed
    assert "draft/proposal docs" in status.detail
    assert "docs/design/draft-topic.html=draft" in status.detail
    assert "docs/design/proposal-topic.html=proposal" in status.detail


def write_minimal_cpp_repo(
    root: Path,
    *,
    include_lizard: bool = True,
    max_cyclomatic_complexity: int = 10,
) -> None:
    for relative_path in (
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "README.md",
        "CMakeLists.txt",
        "tests/rack.toml",
        "docs/setup.html",
        "docs/architecture.html",
    ):
        write_file(root / relative_path, "placeholder\n")
    for relative_dir in ("docs/design", "docs/contracts", "docs/releases"):
        (root / relative_dir).mkdir(parents=True, exist_ok=True)

    write_file(
        root / ".clang-tidy",
        dedent(
            """
            Checks: >
              -*,
              google-runtime-int

            WarningsAsErrors: >
              google-runtime-int
            """
        ).lstrip(),
    )
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
        root / "signoff.toml",
        dedent(
            f"""
            schema = 1
            profile = "cpp-library"
            baseline = "scripts/signoff_baseline.json"

            [limits]
            max_file_lines = 2200
            max_function_lines = 220
            max_cyclomatic_complexity = {max_cyclomatic_complexity}

            [tools]
            lizard = "fail"
            clang_format = "report"
            clang_tidy = "report"
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
    if include_lizard:
        write_file(
            root / "tests" / "L99_signoff" / "test_lizard_complexity.py",
            "def test_lizard_complexity_gate_is_configured():\n    assert 'lizard'\n",
        )


def write_minimal_zephyr_project(root: Path) -> None:
    for relative_path in (
        ".clang-format",
        ".clang-tidy",
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "README.md",
        "tests/rack.toml",
        "docs/setup.html",
        "docs/architecture.html",
        "docs/design/zephyr-standard.html",
    ):
        write_file(root / relative_path, "placeholder\n")
    for relative_dir in ("docs/contracts", "docs/releases", "src/app/src"):
        (root / relative_dir).mkdir(parents=True, exist_ok=True)
    write_file(
        root / "docs" / "design" / "zephyr-standard.html",
        (
            '<!doctype html><html><body data-doc-status="accepted">'
            "<h1>Zephyr Standard</h1></body></html>\n"
        ),
    )
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            """
            profile = "zephyr-firmware"
            distribution = "internal"
            languages = ["c", "cpp"]
            strict = true
            artifact_policy = "transient-dist"
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
        root / ".clang-tidy",
        dedent(
            """
            Checks: >
              -*,
              google-runtime-int

            WarningsAsErrors: >
              google-runtime-int
            """
        ).lstrip(),
    )
    write_file(
        root / "signoff.toml",
        dedent(
            """
            schema = 1
            profile = "zephyr-firmware"
            baseline = "scripts/signoff_baseline.json"

            [limits]
            max_file_lines = 2200
            max_function_lines = 220
            max_cyclomatic_complexity = 10

            [tools]
            lizard = "fail"
            clang_format = "report"
            clang_tidy = "report"
            """
        ).lstrip(),
    )
    write_file(
        root / "tests" / "L99_signoff" / "test_lizard_complexity.py",
        "def test_lizard_complexity_gate_is_configured():\n    assert 'lizard'\n",
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
        root / "docs" / "design" / "javascript-standard.html",
        (
            '<!doctype html><html><body data-doc-status="accepted">'
            "<h1>JavaScript Standard</h1></body></html>\n"
        ),
    )
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


def install_pr_hygiene_templates(root: Path) -> None:
    write_file(
        root / ".github" / "workflows" / "pr-hygiene.yml",
        (ROOT / "docs" / "templates" / "github" / "pr-hygiene.yml").read_text(encoding="utf-8"),
    )
    write_file(
        root / ".github" / "pull_request_template.md",
        (ROOT / "docs" / "templates" / "github" / "pull_request_template.md").read_text(
            encoding="utf-8"
        ),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_git_repo(root: Path) -> None:
    run_git(root, "init", "--initial-branch=main")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
