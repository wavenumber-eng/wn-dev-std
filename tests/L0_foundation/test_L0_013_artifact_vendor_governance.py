from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_pyproject_tool_config

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_vendors_fails_uncataloged_third_party_source(tmp_path: Path) -> None:
    write_file(tmp_path / "third_party" / "zlib" / "zlib.h", "/* zlib */\n")

    result = scope_result(tmp_path, "docs.vendors")

    assert not result.passed
    assert "missing docs/governance/vendors.toml" in result.detail
    assert "third_party/zlib/zlib.h" in result.detail


def test_docs_vendors_passes_cataloged_third_party_source(tmp_path: Path) -> None:
    write_file(tmp_path / "third_party" / "zlib" / "zlib.h", "/* zlib */\n")
    write_file(
        tmp_path / "docs" / "governance" / "vendors.toml",
        """
        [[vendors]]
        id = "zlib"
        kind = "source"
        name = "zlib"
        upstream_url = "https://zlib.net/"
        version = "1.3.1"
        license = "Zlib"
        owner = "native"
        update_command = "scripts/update-zlib.ps1"
        paths = ["third_party/zlib/**"]
        consumers = ["native-build"]
        """,
    )

    result = scope_result(tmp_path, "docs.vendors")

    assert result.passed


def test_docs_artifacts_fails_uncataloged_tracked_binary(tmp_path: Path) -> None:
    write_file(tmp_path / "public_release" / "examples" / "assets" / "part.step", "STEP\n")

    result = scope_result(tmp_path, "docs.artifacts")

    assert not result.passed
    assert "missing docs/governance/artifacts.toml" in result.detail
    assert "public_release/examples/assets/part.step" in result.detail


def test_docs_artifacts_public_assets_win_over_nested_output_name(tmp_path: Path) -> None:
    write_file(
        tmp_path
        / "public_release"
        / "examples"
        / "assets"
        / "projects"
        / "demo"
        / "output"
        / "netlist"
        / "simple_netlist.json",
        "{}\n",
    )

    result = scope_result(tmp_path, "docs.artifacts")

    assert not result.passed
    assert "public_release/examples/assets/projects/demo/output/netlist/simple_netlist.json" in (
        result.detail
    )


def test_docs_artifacts_passes_cataloged_reference_asset(tmp_path: Path) -> None:
    write_file(tmp_path / "public_release" / "examples" / "assets" / "part.step", "STEP\n")
    write_artifacts_catalog(
        tmp_path,
        """
        [[artifacts]]
        id = "public-example-assets"
        kind = "public_reference_asset"
        paths = ["public_release/examples/assets/**"]
        tracked = "required"
        produced_by = "hand-authored public examples"
        included_in_release = "public-examples"
        retention = "committed"
        """,
    )

    result = scope_result(tmp_path, "docs.artifacts")

    assert result.passed


def test_docs_artifacts_ignores_default_transient_dist_output(tmp_path: Path) -> None:
    write_file(tmp_path / "dist" / "native" / "windows-x64" / "demo.exe", "binary\n")

    result = scope_result(tmp_path, "docs.artifacts")

    assert result.passed
    assert "no tracked artifact candidates" in result.detail


def test_docs_artifacts_fails_uncataloged_generated_source(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "cpp" / "src" / "generated" / "api.cpp", "int x;\n")

    result = scope_result(tmp_path, "docs.artifacts")

    assert not result.passed
    assert "src/cpp/src/generated/api.cpp" in result.detail


def test_docs_artifacts_generated_source_requires_regeneration_metadata(
    tmp_path: Path,
) -> None:
    write_file(tmp_path / "src" / "cpp" / "src" / "generated" / "api.cpp", "int x;\n")
    write_artifacts_catalog(
        tmp_path,
        """
        [[artifacts]]
        id = "cpp-generated-api"
        kind = "generated_source"
        paths = ["src/cpp/src/generated/**"]
        tracked = "required"
        produced_by = "generator"
        included_in_release = "source"
        retention = "committed"
        """,
    )

    result = scope_result(tmp_path, "docs.artifacts")

    assert not result.passed
    assert "missing source_of_truth" in result.detail
    assert "missing regeneration_command" in result.detail


def test_docs_artifacts_generated_source_passes_with_regeneration_metadata(
    tmp_path: Path,
) -> None:
    write_file(tmp_path / "src" / "cpp" / "src" / "generated" / "api.cpp", "int x;\n")
    write_file(tmp_path / "scripts" / "generate_cpp_api.py", "print('generate')\n")
    write_artifacts_catalog(
        tmp_path,
        """
        [[artifacts]]
        id = "cpp-generated-api"
        kind = "generated_source"
        paths = ["src/cpp/src/generated/**"]
        tracked = "required"
        produced_by = "scripts/generate_cpp_api.py"
        included_in_release = "source"
        retention = "committed"
        source_of_truth = "scripts/generate_cpp_api.py"
        regeneration_command = "uv run python scripts/generate_cpp_api.py"
        """,
    )

    result = scope_result(tmp_path, "docs.artifacts")

    assert result.passed


def test_docs_release_requires_catalog_for_configured_pypi_distribution(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        standard_pyproject_tool_config(extra='distribution = "pypi"'),
    )

    result = scope_result(tmp_path, "docs.release")

    assert not result.passed
    assert "distribution 'pypi' requires docs/governance/release.toml" in result.detail


def test_docs_release_passes_matching_pypi_channel(tmp_path: Path) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        standard_pyproject_tool_config(extra='distribution = "pypi"'),
    )
    write_file(tmp_path / "docs" / "releases" / "process.md", "# Release\n")
    write_file(
        tmp_path / "docs" / "governance" / "release.toml",
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert result.passed


def test_docs_release_requires_build_doc(tmp_path: Path) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        standard_pyproject_tool_config(extra='distribution = "pypi"'),
    )
    write_file(tmp_path / "docs" / "releases" / "process.md", "# Release\n")
    write_file(
        tmp_path / "docs" / "governance" / "release.toml",
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert not result.passed
    assert "missing build_doc" in result.detail


def test_docs_release_not_required_without_standard_config(tmp_path: Path) -> None:
    result = scope_result(tmp_path, "docs.release")

    assert result.passed
    assert "not required" in result.detail


def test_docs_artifacts_fails_catalog_path_escape(tmp_path: Path) -> None:
    write_artifacts_catalog(
        tmp_path,
        """
        [[artifacts]]
        id = "bad"
        kind = "runtime_binary"
        paths = ["../outside/**"]
        tracked = "required"
        produced_by = "build"
        included_in_release = "native"
        retention = "committed"
        """,
    )

    result = scope_result(tmp_path, "docs.artifacts")

    assert not result.passed
    assert "path pattern escapes repository root" in result.detail


def scope_result(root: Path, scope: str) -> CheckResult:
    results = run_audit_checks(root, (scope,))
    return next(result for result in results if result.scope == scope)


def write_artifacts_catalog(root: Path, body: str) -> None:
    write_file(root / "docs" / "governance" / "artifacts.toml", body)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8", newline="\n")
