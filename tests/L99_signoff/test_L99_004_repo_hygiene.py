from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks import REQUIRED_ROOT_FILES, run_basic_checks

ROOT = Path(__file__).resolve().parents[2]


def test_required_open_source_hygiene_files_exist() -> None:
    for relative_path in REQUIRED_ROOT_FILES:
        assert (ROOT / relative_path).exists(), relative_path
    assert (ROOT / "SECURITY.md").exists()
    assert (ROOT / "CODE_OF_CONDUCT.md").exists()


def test_secret_and_local_result_paths_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", ".venv/", "dist/", "rack_results/"):
        assert pattern in gitignore
    assert not (ROOT / ".env").exists()


def test_sdist_excludes_temporary_plans_and_research() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = cast(Mapping[str, object], tomllib.load(handle))
    tool = cast(Mapping[str, object], pyproject["tool"])
    hatch = cast(Mapping[str, object], tool["hatch"])
    build = cast(Mapping[str, object], hatch["build"])
    targets = cast(Mapping[str, object], build["targets"])
    sdist = cast(Mapping[str, object], targets["sdist"])
    exclude = cast(Sequence[str], sdist["exclude"])
    assert "docs/plans/**" in exclude
    assert "docs/research/**" in exclude


def test_runtime_schema_contracts_are_packaged() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = cast(Mapping[str, object], tomllib.load(handle))
    tool = cast(Mapping[str, object], pyproject["tool"])
    hatch = cast(Mapping[str, object], tool["hatch"])
    build = cast(Mapping[str, object], hatch["build"])
    targets = cast(Mapping[str, object], build["targets"])
    wheel = cast(Mapping[str, object], targets["wheel"])
    force_include = cast(Mapping[str, object], wheel["force-include"])

    assert (
        force_include["docs/contracts/command_manifest.a0.schema.json"]
        == "wn_dev_std/contracts/command_manifest.a0.schema.json"
    )


def test_binary_distribution_policy_is_documented() -> None:
    setup_doc = (ROOT / "docs" / "setup.html").read_text(encoding="utf-8")
    mixed_mode_doc = (ROOT / "docs" / "design" / "mixed-mode.html").read_text(encoding="utf-8")
    assert "dist/native/windows-x64/" in setup_doc
    assert "dist/wasm/browser/" in setup_doc
    assert "dist/native/windows-x64/" in mixed_mode_doc
    assert "dist/wasm/browser/" in mixed_mode_doc
    assert "installed-wheel validation" in mixed_mode_doc


def test_rack_and_signoff_quality_model_is_documented() -> None:
    architecture = (ROOT / "docs" / "architecture.html").read_text(encoding="utf-8")
    for expected in (
        "Quality Model",
        "Rack answers",
        "Signoff answers",
        "Every project needs a signoff gate",
        "L99_signoff",
        "complexity, file",
        "tests/rack.toml",
        "dev-std audit .",
        "fast edit-loop check",
        "release-facing gate",
        "baselines can make existing debt visible",
    ):
        assert expected in architecture
    assert r"C:\ELI" not in architecture


def test_readme_documents_public_rack_package_and_project_model() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in (
        "https://pypi.org/project/wn-rack/",
        "uv add --dev wn-rack",
        "Projects using this standard should use the Rack model",
        "Non-Python projects should still follow the same model",
        "Every project needs a signoff gate",
        "L99_signoff",
        "complexity, file size, function size",
        "tests/",
        "dev-std audit .",
        "package signoff",
        "tests/rack.toml",
    ):
        assert expected in readme
    assert r"C:\ELI" not in readme


def test_cpp_tooling_policy_is_documented_and_templated() -> None:
    cpp_doc = (ROOT / "docs" / "design" / "cpp-standard.html").read_text(encoding="utf-8")
    clang_format = (ROOT / "docs" / "templates" / "cpp" / ".clang-format").read_text(
        encoding="utf-8"
    )
    clang_tidy = (ROOT / "docs" / "templates" / "cpp" / ".clang-tidy").read_text(encoding="utf-8")
    signoff = (ROOT / "docs" / "templates" / "cpp" / "signoff.toml").read_text(encoding="utf-8")
    for expected in (
        "BasedOnStyle: LLVM",
        "BreakBeforeBraces: Allman",
        "IndentWidth: 4",
        "ColumnLimit: 100",
        "PointerAlignment: Left",
        "SortIncludes: true",
        "IncludeBlocks: Preserve",
    ):
        assert expected in cpp_doc
        assert expected in clang_format
    assert "CMAKE_EXPORT_COMPILE_COMMANDS=ON" in cpp_doc
    assert "max_cyclomatic_complexity = 10" in cpp_doc
    assert "max_cyclomatic_complexity = 10" in signoff
    assert 'lizard = "fail"' in signoff
    assert "clang-analyzer-*" in clang_tidy
    assert "google-runtime-int" in clang_tidy


def test_zephyr_policy_is_documented_and_templated() -> None:
    zephyr_doc = (ROOT / "docs" / "design" / "zephyr-standard.html").read_text(encoding="utf-8")
    clang_format = (ROOT / "docs" / "templates" / "zephyr" / ".clang-format").read_text(
        encoding="utf-8"
    )
    signoff = (ROOT / "docs" / "templates" / "zephyr" / "signoff.toml").read_text(encoding="utf-8")
    for expected in (
        "zephyr-firmware",
        "CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "max_cyclomatic_complexity = 10",
        "Xtensa",
    ):
        assert expected in zephyr_doc
    assert "BreakBeforeBraces: Allman" in clang_format
    assert "PointerAlignment: Left" in clang_format
    assert "SortIncludes: true" in clang_format
    assert "IncludeBlocks: Preserve" in clang_format
    assert 'profile = "zephyr-firmware"' in signoff
    assert "max_cyclomatic_complexity = 10" in signoff


def test_javascript_web_policy_is_documented() -> None:
    web_doc = (ROOT / "docs" / "design" / "javascript-standard.html").read_text(encoding="utf-8")
    for expected in (
        "jsconfig.json",
        "// @ts-check",
        "JSDoc",
        "node:test",
        "node --test",
        "CSS custom properties",
        "Web Components",
        "wn-*",
        "Wasmer",
        "Wasmtime",
        "install",
        "update",
        "build",
        "test",
        "signoff",
    ):
        assert expected in web_doc


def test_typescript_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    ts_doc = (ROOT / "docs" / "design" / "typescript-standard.html").read_text(encoding="utf-8")
    js_doc = (ROOT / "docs" / "design" / "javascript-standard.html").read_text(encoding="utf-8")
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    cli_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")
    requirement = (
        ROOT
        / "docs"
        / "core"
        / "requirements"
        / "core-req-0007-greenfield-typescript-guardrails.md"
    )
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0007-typescript-first-browser-standard.md"

    for path in (requirement, adr, ROOT / "docs" / "design" / "typescript-standard.html"):
        assert path.exists(), path

    for expected in (
        "typescript-web-app",
        "python-ts-app",
        "noUncheckedIndexedAccess",
        "exactOptionalPropertyTypes",
        "noPropertyAccessFromIndexSignature",
        "verbatimModuleSyntax",
        "allowJs",
        "skipLibCheck",
        "[typescript.migration]",
        "[typescript.exceptions]",
        "package_extends",
        "local-file",
        "unknown",
        "discriminated unions",
    ):
        assert expected in ts_doc
        assert expected in readme or expected in audit_doc or expected in cli_doc

    assert "TypeScript Standard" in js_doc
    assert 'status = "implemented"' in requirement.read_text(encoding="utf-8")
    assert 'status = "accepted"' in adr.read_text(encoding="utf-8")
    assert 'data-doc-status="accepted"' in ts_doc


def test_rust_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rust_doc = (ROOT / "docs" / "design" / "rust-standard.html").read_text(encoding="utf-8")
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    cli_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")
    documentation_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )
    requirement = (
        ROOT / "docs" / "core" / "requirements" / "core-req-0008-rust-project-guardrails.md"
    )
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0008-rust-application-and-embedded-standard.md"

    for path in (requirement, adr, ROOT / "docs" / "design" / "rust-standard.html"):
        assert path.exists(), path

    for expected in (
        "rust-app",
        "rust-firmware",
        "Cargo.toml",
        "Cargo.lock",
        "rust-toolchain.toml",
        "cargo fmt --all -- --check",
        'RUSTDOCFLAGS="-D warnings"',
        "source_root",
        "src/rs",
        "no_std",
        "memory.x",
        "link.x",
        "Embed.toml",
        "probe-rs",
        "cargo-embed",
        "Tokio",
        "Embassy",
        "[rust.firmware]",
        "[rust.exceptions]",
        "ambient_toolchain",
    ):
        assert expected in rust_doc
        assert (
            expected in readme
            or expected in audit_doc
            or expected in cli_doc
            or expected in documentation_doc
        )

    assert 'status = "implemented"' in requirement.read_text(encoding="utf-8")
    assert 'status = "accepted"' in adr.read_text(encoding="utf-8")
    assert 'data-doc-status="accepted"' in rust_doc


def test_compatibility_pruning_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    python_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")
    for text in (readme, python_doc):
        assert "compatibility_pruning" in text
        assert "forbidden_patterns" in text
        assert "excluded_parts" in text


def test_public_pr_hygiene_policy_is_documented_and_installed() -> None:
    workflow_template = (ROOT / "docs" / "templates" / "github" / "pr-hygiene.yml").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github" / "workflows" / "pr-hygiene.yml").read_text(encoding="utf-8")
    pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    pr_template_source = (
        ROOT / "docs" / "templates" / "github" / "pull_request_template.md"
    ).read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    python_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")

    assert workflow == workflow_template
    assert pr_template == pr_template_source
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    for text in (workflow, readme, python_doc):
        assert "Linked issue:" in text
        assert "Conventional Commit" in text
        assert "Claude" in text or ("AI-vendor" in text and "attribution" in text)
    for text in (readme, python_doc, agents, contributing):
        normalized = " ".join(text.lower().split())
        assert "squash" in normalized
        assert "main" in normalized
        assert "non-linear public" in normalized or "linear" in normalized

    hygiene_check = next(
        result for result in run_basic_checks(ROOT) if result.name == "public PR hygiene"
    )
    assert hygiene_check.passed


def test_ci_governance_first_policy_is_documented_and_installed() -> None:
    ci_doc = (ROOT / "docs" / "design" / "ci-standard.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    setup_doc = (ROOT / "docs" / "setup.html").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for expected in (
        'data-doc-status="accepted"',
        "GitHub Actions",
        "GitLab CI",
        "governance",
        "dev-std audit .",
        "needs: governance",
        'needs: ["governance"]',
        "expensive",
    ):
        assert expected in ci_doc

    for text in (readme, setup_doc):
        assert "CI Standard" in text
        assert "dev-std audit ." in text
        assert "governance" in text
        assert "expensive" in text

    assert "governance:" in workflow
    assert "Run dev-std governance audit" in workflow
    assert "uv run dev-std audit ." in workflow
    assert "needs: governance" in workflow


def test_design_doc_status_policy_is_documented_and_clean() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    standard_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )
    for text in (readme, standard_doc):
        assert "data-doc-status" in text
        assert "draft" in text
        assert "proposal" in text
        assert "accepted" in text
        assert "superseded" in text
        assert "design-doc intent audit" in text or "design-doc-intent-audit" in text
        assert "implemented behavior" in text

    status_check = next(
        result for result in run_basic_checks(ROOT) if result.name == "design doc status"
    )
    assert status_check.passed
    assert "draft/proposal docs" not in status_check.detail


def test_audit_and_plan_log_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    documentation_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )

    for text in (readme, audit_doc, documentation_doc):
        normalized = " ".join(text.split())
        assert "TOML front matter" in normalized
        assert "plan_log" in normalized
        assert "complete" in normalized
        assert "[[steps]]" in normalized
        assert "design-doc-intent-audit" in normalized
        assert "external-review" in normalized

    for expected in (
        "Approved roots are allowed locations, not required folders",
        "docs.plans",
        "plan",
        "plan create",
        "plan status",
        "log",
        "log show",
        "log create",
        "adr create",
        "requirement create",
        "--body-file",
        "command-line length",
        "rogue",
        "v1_1_log.md",
        "worklogs",
        "L99_signoff",
        "signoff checklist",
        "package root",
        "wn-dev-std.toml",
        "[tool.wn_dev_std]",
        ".git",
    ):
        assert expected in audit_doc


def test_json_contract_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    json_doc = (ROOT / "docs" / "design" / "json-contract-standard.html").read_text(
        encoding="utf-8"
    )
    python_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")

    for text in (readme, json_doc, python_doc):
        normalized = " ".join(text.split())
        assert "type" in normalized
        assert "version" in normalized
        assert "kind" in normalized
        assert "JSON Schema" in normalized
    for expected in (
        "Draft 2020-12",
        "real JSON Schema validator",
        "path-addressed",
        "schema-labeled",
        "Pydantic",
        "FastAPI",
        "$schema",
        "$id",
        "compatibility inputs",
    ):
        assert expected in json_doc


def test_vendor_manifest_policy_is_documented() -> None:
    vendor_doc = (ROOT / "docs" / "design" / "artifact-vendor-governance.html").read_text(
        encoding="utf-8"
    )
    for expected in (
        "docs/governance/vendors.toml",
        "[[vendors]]",
        "vendor_manifest.a0.json",
        "schema",
        "compatibility inputs",
        "minified JavaScript",
        "WASM",
        "fonts",
    ):
        assert expected in vendor_doc


def test_release_mode_artifact_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    artifact_doc = (ROOT / "docs" / "design" / "artifact-vendor-governance.html").read_text(
        encoding="utf-8"
    )
    cli_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0006-release-mode-artifact-audit.md"
    requirement = (
        ROOT / "docs" / "core" / "requirements" / "core-req-0006-release-mode-artifact-audit.md"
    )
    design = ROOT / "docs" / "core" / "design" / "release-mode-artifact-audit.html"

    for path in (adr, requirement, design):
        assert path.exists(), path

    for text in (readme, audit_doc, artifact_doc, cli_doc):
        normalized = " ".join(text.split())
        assert "--mode release" in normalized
        assert "docs.release" in normalized

    for expected in (
        "channels.promoted_artifacts",
        "dist/wn_dev_std-*.whl",
        "shape-validates",
        "source-commit",
        "fnmatch",
        "catalog-wide",
        "Workspace",
    ):
        assert expected in artifact_doc or expected in design.read_text(encoding="utf-8")

    assert 'status = "accepted"' in adr.read_text(encoding="utf-8")
    assert 'status = "implemented"' in requirement.read_text(encoding="utf-8")
    assert 'data-doc-status="accepted"' in design.read_text(encoding="utf-8")


def test_adr_requirement_traceability_policy_is_documented_and_clean() -> None:
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    documentation_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )
    cli_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")

    for expected in (
        "docs.adrs",
        "docs.build",
        "docs.domains",
        "docs.requirements",
        "docs.surfaces",
        "docs.test_strategy",
        "docs.traceability",
        "docs.links",
        "tests",
        "no ADR inventory",
        "no requirement inventory",
        "no domain registry",
        "Rack evidence",
        "TOML front matter",
        "external_cpp_test",
        "minimal bootstrap",
        "generic signoff",
        "governance html",
        "governance resolve",
        "data-dev-std-gov-type",
        "data-dev-std-gov-ref",
        "fixture_governance",
    ):
        assert expected in audit_doc or expected in documentation_doc
    for expected in (
        "docs.adrs",
        "docs.build",
        "docs.domains",
        "docs.requirements",
        "docs.surfaces",
        "docs.test_strategy",
        "docs.traceability",
        "docs.links",
        "tests",
        "governance html",
        "governance resolve",
        "adr create",
        "requirement create",
    ):
        assert expected in cli_doc

    results = run_basic_checks(ROOT)
    for name in (
        "docs.adrs",
        "docs.build",
        "docs.domains",
        "docs.requirements",
        "docs.surfaces",
        "docs.test_strategy",
        "docs.traceability",
        "docs.links",
        "test suite governance",
    ):
        result = next(item for item in results if item.name == name)
        assert result.passed


def test_test_strategy_doc_policy_is_documented_and_clean() -> None:
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0003-test-strategy-documents-are-audited.md"
    requirement = (
        ROOT / "docs" / "core" / "requirements" / "core-req-0003-test-strategy-doc-audit.md"
    )
    design = ROOT / "docs" / "core" / "design" / "test-strategy-doc-audit.html"
    strategy_doc = (ROOT / "docs" / "test-strategy.html").read_text(encoding="utf-8")
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    cli_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for path in (adr, requirement, design):
        assert path.exists(), path

    adr_text = adr.read_text(encoding="utf-8")
    requirement_text = requirement.read_text(encoding="utf-8")
    design_text = design.read_text(encoding="utf-8")

    assert 'id = "core-adr-0003"' in adr_text
    assert 'status = "accepted"' in adr_text
    assert "core-req-0003" in adr_text
    assert "src/wn_dev_std/test_strategy_doc_governance.py" in adr_text

    assert 'id = "core-req-0003"' in requirement_text
    assert 'status = "implemented"' in requirement_text
    assert "core-adr-0003" in requirement_text
    assert "tests/L0_foundation/test_L0_017_test_strategy_doc_governance.py" in requirement_text

    assert 'data-doc-status="accepted"' in design_text
    assert "docs.test_strategy" in design_text
    assert "core-adr-0003" in design_text
    assert "core-req-0003" in design_text

    for expected in (
        'data-doc="test-strategy"',
        'data-doc-status="accepted"',
        "Rack",
        "L99_signoff",
        "Python/C++ parity lanes",
        "oracle",
        "missing or orphaned test material",
        "docs.test_strategy",
    ):
        assert expected in strategy_doc

    for text in (audit_doc, cli_doc, readme):
        assert "docs.test_strategy" in text
        assert "test strategy" in text.lower()

    result = next(item for item in run_basic_checks(ROOT) if item.name == "docs.test_strategy")
    assert result.passed


def test_plan_runtime_impact_closeout_policy_is_documented_and_clean() -> None:
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0004-closeout-test-runtime-review.md"
    requirement = (
        ROOT / "docs" / "core" / "requirements" / "core-req-0004-closeout-test-runtime-review.md"
    )
    design = ROOT / "docs" / "core" / "design" / "closeout-test-runtime-impact-audit.html"
    audit_doc = (ROOT / "docs" / "design" / "audit-standard.html").read_text(encoding="utf-8")
    documentation_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for path in (adr, requirement, design):
        assert path.exists(), path

    adr_text = adr.read_text(encoding="utf-8")
    requirement_text = requirement.read_text(encoding="utf-8")
    design_text = design.read_text(encoding="utf-8")

    assert 'id = "core-adr-0004"' in adr_text
    assert 'status = "accepted"' in adr_text
    assert "core-req-0004" in adr_text
    assert "src/wn_dev_std/plan_hygiene.py" in adr_text

    assert 'id = "core-req-0004"' in requirement_text
    assert 'status = "implemented"' in requirement_text
    assert "core-adr-0004" in requirement_text
    assert "test-runtime-impact-audit" in requirement_text

    for expected in (
        'data-doc-status="accepted"',
        "core-adr-0004",
        "core-req-0004",
        "docs/test-strategy.html",
        "minute-scale tests",
    ):
        assert expected in design_text

    for text in (audit_doc, documentation_doc, readme):
        normalized = " ".join(text.split())
        assert "test-runtime-impact-audit" in text
        assert "New tests are listed and runtime impact is reviewed" in normalized


def test_test_suite_governance_audit_has_durable_docs() -> None:
    adr = ROOT / "docs" / "core" / "adr" / "core-adr-0002-test-suite-governance-audit.md"
    requirement = (
        ROOT / "docs" / "core" / "requirements" / "core-req-0002-test-suite-governance-audit.md"
    )
    design = ROOT / "docs" / "core" / "design" / "test-suite-governance-audit.html"

    for path in (adr, requirement, design):
        assert path.exists(), path

    adr_text = adr.read_text(encoding="utf-8")
    requirement_text = requirement.read_text(encoding="utf-8")
    design_text = design.read_text(encoding="utf-8")

    assert 'id = "core-adr-0002"' in adr_text
    assert 'status = "accepted"' in adr_text
    assert "core-req-0002" in adr_text
    assert "src/wn_dev_std/test_governance.py" in adr_text

    assert 'id = "core-req-0002"' in requirement_text
    assert 'status = "implemented"' in requirement_text
    assert "core-adr-0002" in requirement_text
    assert "tests/L0_foundation/test_L0_016_test_suite_governance.py" in requirement_text

    for expected in (
        'data-doc-status="accepted"',
        "core-adr-0002",
        "core-req-0002",
        "[tests]",
        "signoff_strata",
        "failing audit command",
    ):
        assert expected in design_text
