from __future__ import annotations

import hashlib
from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config, standard_pyproject_tool_config
from pytest import MonkeyPatch

from wn_dev_std import release_artifacts
from wn_dev_std.checks import CheckResult, run_audit_checks
from wn_dev_std.standards import STANDARD_VERSION


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


def test_docs_release_default_mode_shape_validates_promoted_artifacts(
    tmp_path: Path,
) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        paths = ["*.whl"]
        required = "yes"
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert not result.passed
    assert "required must be true or false" in result.detail
    assert "static directory prefix" in result.detail


def test_docs_release_default_mode_fails_promoted_artifact_path_escape(
    tmp_path: Path,
) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        paths = ["../dist/*.whl"]
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert not result.passed
    assert "path pattern escapes repository root" in result.detail


def test_docs_release_default_mode_requires_runtime_artifact_metadata(
    tmp_path: Path,
) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "native"
        kind = "native_bundle"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "windows-runtime"
        kind = "runtime_binary"
        paths = ["dist/native/windows-x64/*.exe"]
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert not result.passed
    assert "missing target" in result.detail
    assert "missing build_profile" in result.detail
    assert "missing abi" in result.detail
    assert "missing license_refs" in result.detail


def test_docs_release_default_mode_does_not_require_payload_files(tmp_path: Path) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        paths = ["dist/wn_dev_std-*.whl"]
        required = true
        """,
    )

    result = scope_result(tmp_path, "docs.release")

    assert result.passed


def test_docs_release_release_mode_fails_missing_required_payload(
    tmp_path: Path,
) -> None:
    write_release_catalog_with_wheel(tmp_path)

    result = release_scope_result(tmp_path)

    assert not result.passed
    assert "missing required promoted artifact" in result.detail


def test_docs_release_release_mode_passes_bounded_glob_payload(tmp_path: Path) -> None:
    write_release_catalog_with_wheel(tmp_path)
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16-py3-none-any.whl", "wheel\n")

    result = release_scope_result(tmp_path)

    assert result.passed


def test_docs_release_release_mode_fails_uncataloged_payload(tmp_path: Path) -> None:
    write_release_catalog_with_wheel(tmp_path)
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16-py3-none-any.whl", "wheel\n")
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16.tar.gz", "sdist\n")

    result = release_scope_result(tmp_path)

    assert not result.passed
    assert "uncataloged promoted artifact" in result.detail
    assert "dist/wn_dev_std-2026.7.16.tar.gz" in result.detail


def test_docs_release_release_mode_allows_shared_root_payloads_across_channels(
    tmp_path: Path,
) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_file(tmp_path / "dist" / "pkg-1.0-py3-none-any.whl", "wheel\n")
    write_file(tmp_path / "dist" / "pkg-1.0.zip", "archive\n")
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        paths = ["dist/pkg-*.whl"]
        required = true

        [[channels]]
        id = "github"
        kind = "github_release"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "release-archive"
        kind = "release_evidence"
        paths = ["dist/pkg-*.zip"]
        required = true
        """,
    )

    result = release_scope_result(tmp_path)

    assert result.passed


def test_docs_release_release_mode_validates_sha256(tmp_path: Path) -> None:
    write_pypi_pyproject(tmp_path)
    write_release_docs(tmp_path)
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16-py3-none-any.whl", "wheel\n")
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        path = "dist/wn_dev_std-2026.7.16-py3-none-any.whl"
        sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        """,
    )

    result = release_scope_result(tmp_path)

    assert not result.passed
    assert "sha256 does not match" in result.detail


def test_docs_release_release_mode_accepts_matching_declared_metadata(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    write_versioned_pypi_pyproject(tmp_path, "2026.7.18")
    write_release_docs(tmp_path)
    artifact_text = "wheel\n"
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.18-py3-none-any.whl", artifact_text)
    artifact_sha = hashlib.sha256(artifact_text.encode()).hexdigest()

    def fake_git_head(_root: Path) -> str:
        return "abcdef1234567890abcdef1234567890abcdef12"

    monkeypatch.setattr(
        release_artifacts,
        "_git_head",
        fake_git_head,
    )
    write_release_catalog(
        tmp_path,
        f"""
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        path = "dist/wn_dev_std-2026.7.18-py3-none-any.whl"
        version = "2026.7.18"
        source_commit = "abcdef1"
        sha256 = "{artifact_sha}"
        """,
    )

    result = release_scope_result(tmp_path)

    assert result.passed


def test_docs_release_release_mode_fails_version_mismatch(tmp_path: Path) -> None:
    write_versioned_pypi_pyproject(tmp_path, "2026.7.18")
    write_release_docs(tmp_path)
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.18-py3-none-any.whl", "wheel\n")
    write_release_catalog(
        tmp_path,
        """
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        path = "dist/wn_dev_std-2026.7.18-py3-none-any.whl"
        version = "2026.7.16"
        """,
    )

    result = release_scope_result(tmp_path)

    assert not result.passed
    assert "does not match project version" in result.detail


def test_docs_release_release_mode_fails_source_commit_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    write_release_catalog_with_wheel(tmp_path, extra='source_commit = "1234567"')
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16-py3-none-any.whl", "wheel\n")

    def fake_git_head(_root: Path) -> str:
        return "abcdef1234567890abcdef1234567890abcdef12"

    monkeypatch.setattr(
        release_artifacts,
        "_git_head",
        fake_git_head,
    )

    result = release_scope_result(tmp_path)

    assert not result.passed
    assert "source_commit" in result.detail
    assert "does not match HEAD" in result.detail


def test_docs_release_release_mode_runs_when_all_is_selected(tmp_path: Path) -> None:
    write_release_catalog_with_wheel(tmp_path)

    results = run_audit_checks(tmp_path, ("all",), mode="release")
    result = next(check for check in results if check.scope == "docs.release")

    assert not result.passed
    assert "missing required promoted artifact" in result.detail


def test_docs_artifacts_release_mode_keeps_default_behavior(tmp_path: Path) -> None:
    write_file(tmp_path / "dist" / "wn_dev_std-2026.7.16-py3-none-any.whl", "wheel\n")

    result = run_audit_checks(tmp_path, ("docs.artifacts",), mode="release")[0]

    assert result.passed
    assert "no tracked artifact candidates" in result.detail


def test_workspace_release_mode_runs_per_member_catalog(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        f"""
        standard_version = "{STANDARD_VERSION}"
        kind = "workspace"

        [workspace]
        members = ["app"]
        """,
    )
    write_release_catalog_with_wheel(tmp_path / "app")

    result = next(
        check
        for check in run_audit_checks(tmp_path, ("docs.release",), mode="release")
        if check.scope == "docs.release"
    )

    assert not result.passed
    assert result.member == "app"
    assert "missing required promoted artifact" in result.detail


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


def release_scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.release",), mode="release")
    return next(result for result in results if result.scope == "docs.release")


def write_artifacts_catalog(root: Path, body: str) -> None:
    write_file(root / "docs" / "governance" / "artifacts.toml", body)


def write_release_catalog(root: Path, body: str) -> None:
    write_file(root / "docs" / "governance" / "release.toml", body)


def write_release_catalog_with_wheel(root: Path, extra: str = "") -> None:
    write_pypi_pyproject(root)
    write_release_docs(root)
    extra_lines = "\n" + extra if extra else ""
    write_release_catalog(
        root,
        f"""
        [[channels]]
        id = "pypi"
        kind = "pypi"
        status = "active"
        owner = "release"
        process_doc = "docs/releases/process.md"
        build_doc = "docs/releases/process.md"

        [[channels.promoted_artifacts]]
        id = "wheel"
        kind = "package_distribution"
        paths = ["dist/wn_dev_std-*.whl"]
        required = true{extra_lines}
        """,
    )


def write_pypi_pyproject(root: Path) -> None:
    write_file(
        root / "pyproject.toml",
        standard_pyproject_tool_config(extra='distribution = "pypi"'),
    )


def write_versioned_pypi_pyproject(root: Path, version: str) -> None:
    write_file(
        root / "pyproject.toml",
        f"""
        [project]
        name = "example"
        version = "{version}"

        [tool.wn_dev_std]
        {standard_config(extra='distribution = "pypi"')}
        """,
    )


def write_release_docs(root: Path) -> None:
    write_file(root / "docs" / "releases" / "process.md", "# Release\n")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8", newline="\n")
