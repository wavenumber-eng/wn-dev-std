from __future__ import annotations

import errno
import io
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_L0_021_rust_policy import (
    cargo_manifest,
    hybrid_workspace_manifest,
    named_result,
    run_language_checks,
    workspace_manifest,
    write_file,
    write_minimal_rust_project,
    write_workspace_member_manifest,
)

from wn_dev_std import rust_format_external, rust_format_policy


@pytest.mark.parametrize(
    "command",
    [
        "cargo fmt --all -- --check",
        "cargo fmt --package example -- --check",
        "cargo fmt -p example -- --check",
    ],
)
def test_single_root_accepts_full_or_explicit_owned_format(tmp_path: Path, command: str) -> None:
    manifest = cargo_manifest()
    if command != "cargo fmt --all -- --check":
        manifest += '\n[workspace]\nresolver = "3"\n'
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    set_format_command(tmp_path, command)

    assert_format_result(tmp_path, passed=True)


@pytest.mark.parametrize("selector", ["--package", "-p"])
def test_nested_application_formats_only_its_root_with_external_path_dependencies(
    tmp_path: Path, selector: str
) -> None:
    root = tmp_path / "appz" / "cli" / "pcb-engine"
    domain = tmp_path / "appz" / "data_models" / "domain"
    manifest = cargo_manifest() + (
        '\n[workspace]\nresolver = "3"\n'
        '\n[dependencies]\ndomain = { path = "../../data_models/domain" }\n'
    )
    write_minimal_rust_project(root, cargo_toml=manifest)
    write_minimal_rust_project(
        domain, cargo_toml=cargo_manifest().replace('name = "example"', 'name = "domain"')
    )
    external_manifest = (domain / "Cargo.toml").read_bytes()
    set_format_command(root, f"cargo fmt {selector} example -- --check")

    assert_format_result(root, passed=True)
    assert (domain / "Cargo.toml").read_bytes() == external_manifest


@pytest.mark.parametrize(
    "command",
    [
        "cargo fmt -- --check",
        "cargo fmt --package other -- --check",
        "cargo fmt --package EXAMPLE -- --check",
        "cargo fmt --package example -p other -- --check",
        "cargo fmt --all --package other -- --check",
        "cargo fmt --package example --manifest-path other/Cargo.toml -- --check",
    ],
)
def test_owned_format_requires_one_exact_root_selector(tmp_path: Path, command: str) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    set_format_command(tmp_path, command)

    assert_format_result(tmp_path, passed=False)


@pytest.mark.parametrize(
    "command",
    [
        "echo cargo fmt --all -- --check",
        "# cargo fmt --all -- --check",
        "printf 'cargo fmt --all -- --check'",
        "cargo fmtextra --all -- --check",
        "cargo fmt --package example -- --check-extra",
        "cargo fmt --package example -- --check && echo done",
    ],
)
def test_command_text_cannot_impersonate_a_format_check(tmp_path: Path, command: str) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    set_format_command(tmp_path, command)

    assert_format_result(tmp_path, passed=False)


@pytest.mark.parametrize("members", ['["crates/app"]', '["crates/*"]'])
def test_owned_workspace_member_requires_full_format_lane(tmp_path: Path, members: str) -> None:
    manifest = hybrid_workspace_manifest().replace('["crates/app"]', members)
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    set_format_command(tmp_path, "cargo fmt --package root -- --check")

    assert_format_result(tmp_path, passed=False)
    set_format_command(tmp_path, "cargo fmt --all -- --check")
    assert_format_result(tmp_path, passed=True)


@pytest.mark.parametrize(
    "table",
    [
        "dependencies",
        "dev-dependencies",
        "build-dependencies",
        "target.'cfg(windows)'.dependencies",
        "workspace.dependencies",
    ],
)
def test_in_root_path_dependency_prevents_single_package_format(tmp_path: Path, table: str) -> None:
    manifest = cargo_manifest() + (
        f'\n[workspace]\nresolver = "3"\n\n[{table}]\nhelper = {{ path = "crates/helper" }}\n'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_file(
        tmp_path / "crates" / "helper" / "Cargo.toml",
        cargo_manifest().replace('name = "example"', 'name = "helper"'),
    )
    write_file(tmp_path / "crates" / "helper" / "src" / "lib.rs", "pub fn helper() {}\n")
    set_format_command(tmp_path, "cargo fmt -p example -- --check")

    assert_format_result(tmp_path, passed=False)
    set_format_command(tmp_path, "cargo fmt --all -- --check")
    assert_format_result(tmp_path, passed=True)


def test_virtual_workspace_retains_full_format_requirement(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=workspace_manifest(),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    set_format_command(tmp_path, "cargo fmt --package app -- --check")

    assert_format_result(tmp_path, passed=False)
    set_format_command(tmp_path, "cargo fmt --all -- --check")
    assert_format_result(tmp_path, passed=True)


def test_package_without_self_workspace_cannot_claim_owned_format(tmp_path: Path) -> None:
    root = tmp_path / "monorepo" / "cli" / "example"
    write_minimal_rust_project(root)
    write_file(
        tmp_path / "monorepo" / "Cargo.toml",
        '[workspace]\nmembers = ["cli/example", "domain"]\nresolver = "3"\n',
    )
    write_file(tmp_path / "monorepo" / "domain" / "Cargo.toml", cargo_manifest())
    set_format_command(root, "cargo fmt -p example -- --check")

    assert_format_result(root, passed=False)


def test_package_workspace_redirect_cannot_claim_owned_format(tmp_path: Path) -> None:
    manifest = cargo_manifest().replace(
        'version = "0.1.0"', 'version = "0.1.0"\nworkspace = "../other"'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest + '\n[workspace]\nresolver = "3"\n')
    set_format_command(tmp_path, "cargo fmt -p example -- --check")

    assert_format_result(tmp_path, passed=False)


@pytest.mark.parametrize("member_key", ["default-members", "exclude"])
def test_nonempty_workspace_scope_cannot_claim_owned_format(
    tmp_path: Path, member_key: str
) -> None:
    manifest = cargo_manifest() + (
        f'\n[workspace]\nresolver = "3"\n{member_key} = ["crates/helper"]\n'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    set_format_command(tmp_path, "cargo fmt -p example -- --check")

    assert_format_result(tmp_path, passed=False)


def test_undeclared_nested_crate_cannot_be_silently_skipped(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    write_file(tmp_path / "crates" / "forgotten" / "Cargo.toml", cargo_manifest())
    set_format_command(tmp_path, "cargo fmt -p example -- --check")

    assert_format_result(tmp_path, passed=False)


def test_internal_dependency_stays_owned_inside_transient_directory(tmp_path: Path) -> None:
    manifest = cargo_manifest() + (
        '\n[workspace]\nresolver = "3"\n\n[dependencies]\nhelper = { path = "target/helper" }\n'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_file(tmp_path / "target" / "helper" / "Cargo.toml", cargo_manifest())
    set_format_command(tmp_path, "cargo fmt -p example -- --check")

    assert_format_result(tmp_path, passed=False)


@pytest.mark.parametrize(
    ("table", "dependency"),
    [("patch.crates-io", "helper"), ("replace", '"helper:0.1.0"')],
)
def test_internal_path_overrides_cannot_hide_in_pruned_output(
    tmp_path: Path, table: str, dependency: str
) -> None:
    manifest = cargo_manifest() + (
        f'\n[workspace]\nresolver = "3"\n\n[{table}]\n{dependency} = {{ path = "build/helper" }}\n'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_file(tmp_path / "build" / "helper" / "Cargo.toml", cargo_manifest())

    assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p example -- --check"])
    assert rust_format_policy.has_format_lane(tmp_path, ["cargo fmt --all -- --check"])


@pytest.mark.parametrize("kind", ["directory", "symlink"])
def test_nonregular_root_manifest_refuses_before_any_content_read(
    tmp_path: Path, kind: str
) -> None:
    root = tmp_path / "application"
    root.mkdir()
    manifest = root / "Cargo.toml"
    if kind == "directory":
        manifest.mkdir()
    else:
        external = tmp_path / "external.toml"
        write_file(external, cargo_manifest() + '\n[workspace]\nresolver = "3"\n')
        create_symlink(manifest, external, directory=False)

    with patch.object(Path, "open", side_effect=AssertionError("content was read")):
        assert not rust_format_policy.has_format_lane(root, ["cargo fmt -p example -- --check"])


def test_nontransient_directory_link_prevents_owned_inventory_proof(tmp_path: Path) -> None:
    root = tmp_path / "application"
    write_minimal_rust_project(
        root, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    external = tmp_path / "external"
    write_file(external / "Cargo.toml", cargo_manifest())
    create_symlink(root / "shared", external, directory=True)

    assert not rust_format_policy.has_format_lane(root, ["cargo fmt -p example -- --check"])


def test_lexical_internal_dependency_does_not_escape_through_link(tmp_path: Path) -> None:
    root = tmp_path / "application"
    manifest = cargo_manifest() + (
        '\n[workspace]\nresolver = "3"\n\n[dependencies]\nhelper = { path = "target/helper" }\n'
    )
    write_minimal_rust_project(root, cargo_toml=manifest)
    external = tmp_path / "external"
    write_file(external / "Cargo.toml", cargo_manifest())
    (root / "target").mkdir()
    create_symlink(root / "target" / "helper", external, directory=True)

    assert not rust_format_policy.has_format_lane(root, ["cargo fmt -p example -- --check"])


def test_manifest_growth_is_bounded_at_the_read_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    limit = 1024
    monkeypatch.setattr(rust_format_policy, "MAX_MANIFEST_BYTES", limit)
    reads: list[int | None] = []

    class GrowingFile(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            reads.append(size)
            return super().read(size)

    grown = manifest.encode() + b" " * (limit + 1)
    with patch.object(Path, "open", return_value=GrowingFile(grown)):
        assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p example -- --check"])
    assert reads
    assert all(size is not None and 0 <= size <= limit + 1 for size in reads)


def test_inventory_exhaustion_cannot_prove_single_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    command = ["cargo fmt -p example -- --check"]
    assert rust_format_policy.has_format_lane(tmp_path, command)
    monkeypatch.setattr(rust_format_policy, "MAX_INVENTORY_ENTRIES", 1)

    assert not rust_format_policy.has_format_lane(tmp_path, command)


def test_unreadable_nested_inventory_cannot_prove_single_package(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    denied = tmp_path / "private"
    denied.mkdir()
    scan = os.scandir

    def denied_scan(path: str | Path) -> object:
        if Path(path) == denied:
            raise PermissionError("inventory is unreadable")
        return scan(path)

    with patch.object(rust_format_policy.os, "scandir", side_effect=denied_scan):
        assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p example -- --check"])


@pytest.mark.parametrize("budget", ["MAX_DEPENDENCY_DEPTH", "MAX_DEPENDENCY_ENTRIES"])
def test_dependency_proof_exhaustion_retains_only_full_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    root = tmp_path / "application"
    manifest = cargo_manifest() + (
        '\n[workspace]\nresolver = "3"\n'
        "\n[target.'cfg(windows)'.dependencies]\nhelper = { path = \"../domain\" }\n"
    )
    write_minimal_rust_project(root, cargo_toml=manifest)
    write_file(tmp_path / "domain" / "Cargo.toml", cargo_manifest())
    owned = ["cargo fmt -p example -- --check"]
    assert rust_format_policy.has_format_lane(root, owned)
    monkeypatch.setattr(rust_format_policy, budget, 0)

    assert not rust_format_policy.has_format_lane(root, owned)
    assert rust_format_policy.has_format_lane(root, ["cargo fmt --all -- --check"])


def test_toml_recursion_refuses_owned_format_without_disabling_full_lane(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path, cargo_toml=cargo_manifest() + '\n[workspace]\nresolver = "3"\n'
    )
    with patch.object(
        rust_format_policy.tomllib, "loads", side_effect=RecursionError("nested TOML")
    ):
        assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p example -- --check"])
        assert rust_format_policy.has_format_lane(tmp_path, ["cargo fmt --all -- --check"])


def test_dependency_table_budget_precedes_path_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = cargo_manifest() + '\n[workspace]\nresolver = "3"\n\n[dependencies]\n'
    write_minimal_rust_project(tmp_path, cargo_toml=base)
    monkeypatch.setattr(rust_format_policy, "MAX_DEPENDENCY_ENTRIES", 16)
    owned = ["cargo fmt -p example -- --check"]
    # The complete root metadata and empty table fit this unchanged budget.
    assert rust_format_policy.has_format_lane(tmp_path, owned)
    write_file(
        tmp_path / "Cargo.toml",
        base + 'one = { path = "../one" }\ntwo = { path = "../two" }\n',
    )

    with patch.object(
        rust_format_policy, "_table_paths", side_effect=AssertionError("paths materialized")
    ):
        assert not rust_format_policy.has_format_lane(tmp_path, owned)


def test_patch_table_budget_precedes_path_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = cargo_manifest() + '\n[workspace]\nresolver = "3"\n\n[patch.crates-io]\n'
    write_minimal_rust_project(tmp_path, cargo_toml=base)
    monkeypatch.setattr(rust_format_policy, "MAX_DEPENDENCY_ENTRIES", 17)
    owned = ["cargo fmt -p example -- --check"]
    assert rust_format_policy.has_format_lane(tmp_path, owned)
    write_file(
        tmp_path / "Cargo.toml",
        base + 'one = { path = "../one" }\ntwo = { path = "../two" }\n',
    )

    with patch.object(
        rust_format_policy, "_patch_paths", side_effect=AssertionError("paths materialized")
    ):
        assert not rust_format_policy.has_format_lane(tmp_path, owned)


@pytest.mark.parametrize(
    "command",
    [
        "cargo fmt --package root --package app -- --check",
        "cargo fmt -p app -p root -- --check",
        "cargo fmt --package app -p root -- --check",
    ],
)
def test_literal_workspace_accepts_complete_owned_selection(tmp_path: Path, command: str) -> None:
    write_minimal_rust_project(tmp_path, cargo_toml=hybrid_workspace_manifest())
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    set_format_command(tmp_path, command)

    assert_format_result(tmp_path, passed=True)


@pytest.mark.parametrize(
    "selectors",
    [
        "-p root",
        "-p app",
        "-p root -p app -p foreign",
        "-p root -p app -p app",
        "-p root -p root -p app",
        "-p root -p 'app*'",
        "-p root -p app --all",
        "-p root -p app --manifest-path Cargo.toml",
    ],
)
def test_workspace_selectors_must_cover_each_package_once(tmp_path: Path, selectors: str) -> None:
    write_minimal_rust_project(tmp_path, cargo_toml=hybrid_workspace_manifest())
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)

    assert not rust_format_policy.has_format_lane(tmp_path, [f"cargo fmt {selectors} -- --check"])
    assert rust_format_policy.has_format_lane(tmp_path, ["cargo fmt --all -- --check"])


def test_declared_internal_dependencies_are_resolved_from_each_member(tmp_path: Path) -> None:
    root_manifest = hybrid_workspace_manifest().replace(
        '["crates/app"]', '["crates/app", "crates/helper"]'
    )
    root_manifest += '\n[dependencies]\napp = { path = "crates/app" }\n'
    write_minimal_rust_project(tmp_path, cargo_toml=root_manifest)
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    member = tmp_path / "crates" / "app" / "Cargo.toml"
    write_file(member, member.read_text() + '\n[dependencies]\nhelper = { path = "../helper" }\n')
    write_file(
        tmp_path / "crates" / "helper" / "Cargo.toml",
        cargo_manifest().replace('name = "example"', 'name = "helper"'),
    )
    commands = ["cargo fmt -p root -p helper -p app -- --check"]

    assert rust_format_policy.has_format_lane(tmp_path, commands)
    write_file(member, member.read_text().replace("../helper", "../../target/hidden"))
    write_file(tmp_path / "target" / "hidden" / "Cargo.toml", cargo_manifest())
    assert not rust_format_policy.has_format_lane(tmp_path, commands)


@pytest.mark.parametrize(
    "members",
    [
        '["crates/app", "crates/app"]',
        '["crates/app", "crates/./app"]',
        '["crates/*"]',
        '["../app"]',
        '["crates/app", "target/hidden"]',
    ],
)
def test_workspace_members_require_literal_unique_inventory(tmp_path: Path, members: str) -> None:
    manifest = hybrid_workspace_manifest().replace('["crates/app"]', members)
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    selectors = "-p root -p app"
    if "target/hidden" in members:
        selectors += " -p hidden"
        write_file(
            tmp_path / "target" / "hidden" / "Cargo.toml",
            cargo_manifest().replace('name = "example"', 'name = "hidden"'),
        )

    assert not rust_format_policy.has_format_lane(tmp_path, [f"cargo fmt {selectors} -- --check"])


@pytest.mark.parametrize("member_name", ["root", "app"])
def test_duplicate_workspace_package_names_refuse_selection(
    tmp_path: Path, member_name: str
) -> None:
    manifest = hybrid_workspace_manifest().replace(
        '["crates/app"]', '["crates/app", "crates/other"]'
    )
    write_minimal_rust_project(tmp_path, cargo_toml=manifest)
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    write_file(
        tmp_path / "crates" / "other" / "Cargo.toml",
        cargo_manifest().replace('name = "example"', f'name = "{member_name}"'),
    )

    assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p root -p app -- --check"])


@pytest.mark.parametrize("redirect", ["\n[workspace]\n", "\n"])
def test_member_cannot_redirect_workspace_ownership(tmp_path: Path, redirect: str) -> None:
    write_minimal_rust_project(tmp_path, cargo_toml=hybrid_workspace_manifest())
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    member = tmp_path / "crates" / "app" / "Cargo.toml"
    source = member.read_text()
    if redirect == "\n":
        source = source.replace("[package]", '[package]\nworkspace = "../../outside"')
    write_file(member, source + redirect)

    assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p root -p app -- --check"])


def test_workspace_proof_reads_only_direct_external_identity(tmp_path: Path) -> None:
    root = (tmp_path / "app").resolve()
    external = (tmp_path / "external" / "Cargo.toml").resolve()
    write_minimal_rust_project(root, cargo_toml=hybrid_workspace_manifest())
    write_workspace_member_manifest(root, inherit_metadata=True, inherit_lints=True)
    member = root / "crates" / "app" / "Cargo.toml"
    write_file(
        member, member.read_text() + '\n[dependencies]\nexternal = { path = "../../../external" }\n'
    )
    write_file(
        external,
        '[package]\nname="external"\nversion="0.1.0"\n'
        '[dependencies]\nhidden={path="../app/target/hidden"}\n',
    )
    write_file(root / "target" / "hidden" / "Cargo.toml", "Not valid TOML.\n")
    original_open = Path.open

    def owned_open(path: Path, *args: object, **kwargs: object) -> object:
        assert path == external or path.resolve().is_relative_to(root.resolve()), path
        assert "hidden" not in path.parts, f"transitive read: {path}"
        return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

    with patch.object(Path, "open", owned_open):
        assert rust_format_policy.has_format_lane(root, ["cargo fmt -p root -p app -- --check"])


@pytest.mark.parametrize("workspace", [False, True])
def test_external_workspace_redirect_cannot_hide_automatic_members(
    tmp_path: Path, workspace: bool
) -> None:
    root, external, command = external_fixture(tmp_path, workspace=workspace)
    write_file(
        external,
        '[package]\nname="external"\nversion="0.1.0"\nworkspace="../app"\n'
        '[dependencies]\nhidden={path="../app/target/hidden"}\n',
    )
    write_file(root / "target" / "hidden" / "Cargo.toml", cargo_manifest())

    assert not rust_format_policy.has_format_lane(root, [command])
    assert rust_format_policy.has_format_lane(root, ["cargo fmt --all -- --check"])


@pytest.mark.parametrize("identity", ["", "[workspace]\n", '[package]\nworkspace="../separate"\n'])
def test_separate_external_workspace_identities_are_accepted(tmp_path: Path, identity: str) -> None:
    root, external, command = external_fixture(tmp_path)
    base = '[package]\nname="external"\nversion="0.1.0"\n'
    source = base + identity
    if identity.startswith("[package]"):
        source = base + 'workspace="../separate"\n'
    write_file(external, source)
    write_file(tmp_path / "separate" / "Cargo.toml", "[workspace]\nmembers=[]\n")

    assert rust_format_policy.has_format_lane(root, [command])


@pytest.mark.parametrize(
    "identity",
    [
        "invalid TOML",
        "[workspace]\n",
        '[package]\nname=""\n',
        '[package]\nname="external"\nworkspace=5\n',
        '[package]\nname="external"\nworkspace=""\n',
    ],
)
def test_uncertain_external_identity_refuses_selectors(tmp_path: Path, identity: str) -> None:
    root, external, command = external_fixture(tmp_path)
    write_file(external, identity)

    assert not rust_format_policy.has_format_lane(root, [command])


@pytest.mark.parametrize("kind", ["missing", "directory", "denied"])
def test_unreadable_external_identity_refuses_selectors(tmp_path: Path, kind: str) -> None:
    root, external, command = external_fixture(tmp_path)
    if kind == "missing":
        external.unlink()
    elif kind == "directory":
        external.unlink()
        external.mkdir()
    original_open = Path.open

    def external_open(path: Path, *args: object, **kwargs: object) -> object:
        if kind == "denied" and path == external:
            raise PermissionError("external identity unreadable")
        return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

    with patch.object(Path, "open", external_open):
        assert not rust_format_policy.has_format_lane(root, [command])


@pytest.mark.parametrize(
    "budget", ["MAX_EXTERNAL_MANIFESTS", "MAX_EXTERNAL_MANIFEST_BYTES", "MAX_MANIFEST_BYTES"]
)
def test_external_identity_budgets_refuse_unproven_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    root, _external, command = external_fixture(tmp_path)
    assert rust_format_policy.has_format_lane(root, [command])
    monkeypatch.setattr(rust_format_external, budget, 0)

    assert not rust_format_policy.has_format_lane(root, [command])
    assert rust_format_policy.has_format_lane(root, ["cargo fmt --all -- --check"])


def test_direct_external_identity_is_read_once_across_owned_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, external, command = external_fixture(tmp_path)
    member = root / "crates" / "app" / "Cargo.toml"
    write_file(
        member, member.read_text() + '\n[dependencies]\nexternal={path="../../../external"}\n'
    )
    monkeypatch.setattr(rust_format_external, "MAX_EXTERNAL_MANIFESTS", 1)
    original_open = Path.open
    opened: list[Path] = []

    def identity_open(path: Path, *args: object, **kwargs: object) -> object:
        if path == external:
            opened.append(path)
        return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

    with patch.object(Path, "open", identity_open):
        assert rust_format_policy.has_format_lane(root, [command])
    assert opened == [external]


def test_external_identity_aggregate_budget_spans_distinct_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, external, command = external_fixture(tmp_path)
    write_file(tmp_path / "other" / "Cargo.toml", external.read_text().replace("external", "other"))
    manifest = root / "Cargo.toml"
    write_file(manifest, manifest.read_text() + 'other={path="../other"}\n')
    assert rust_format_policy.has_format_lane(root, [command])
    monkeypatch.setattr(
        rust_format_external, "MAX_EXTERNAL_MANIFEST_BYTES", external.stat().st_size
    )

    assert not rust_format_policy.has_format_lane(root, [command])


def test_external_identity_growth_is_bounded_at_read_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, external, command = external_fixture(tmp_path)
    limit = 128
    monkeypatch.setattr(rust_format_external, "MAX_MANIFEST_BYTES", limit)
    source = external.read_bytes() + b" " * (limit + 1)
    original_open = Path.open
    reads: list[int | None] = []

    class GrowingFile(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            reads.append(size)
            return super().read(size)

    def identity_open(path: Path, *args: object, **kwargs: object) -> object:
        if path == external:
            return GrowingFile(source)
        return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

    with patch.object(Path, "open", identity_open):
        assert not rust_format_policy.has_format_lane(root, [command])
    assert reads and all(size is not None and 0 <= size <= limit + 1 for size in reads)


def test_linked_external_manifest_refuses_before_content_read(tmp_path: Path) -> None:
    root, external, command = external_fixture(tmp_path)
    target = tmp_path / "identity.toml"
    external.replace(target)
    create_symlink(external, target, directory=False)

    assert not rust_format_policy.has_format_lane(root, [command])


@pytest.mark.parametrize("scope", ["root", "external"])
def test_python312_resolve_loop_refuses_uncertain_identity(tmp_path: Path, scope: str) -> None:
    root, external, command = external_fixture(tmp_path)
    target = root if scope == "root" else external.parent
    original_resolve = Path.resolve

    def loop_resolve(path: Path, *args: object, **kwargs: object) -> Path:
        if path == target:
            raise RuntimeError("Symlink loop (Python 3.12)")
        return original_resolve(path, *args, **kwargs)  # type: ignore[arg-type]

    with patch.object(Path, "resolve", loop_resolve):
        assert not rust_format_policy.has_format_lane(root, [command])
        assert rust_format_policy.has_format_lane(root, ["cargo fmt --all -- --check"])


def external_fixture(tmp_path: Path, *, workspace: bool = True) -> tuple[Path, Path, str]:
    root = (tmp_path / "app").resolve()
    manifest = hybrid_workspace_manifest() if workspace else cargo_manifest() + "\n[workspace]\n"
    write_minimal_rust_project(
        root, cargo_toml=manifest + '\n[dependencies]\nexternal={path="../external"}\n'
    )
    if workspace:
        write_workspace_member_manifest(root, inherit_metadata=True, inherit_lints=True)
    external = (tmp_path / "external" / "Cargo.toml").resolve()
    write_file(external, '[package]\nname="external"\nversion="0.1.0"\n')
    command = (
        "cargo fmt -p root -p app -- --check" if workspace else "cargo fmt -p example -- --check"
    )
    return root, external, command


def test_member_manifest_link_refuses_complete_selection(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path, cargo_toml=hybrid_workspace_manifest())
    target = tmp_path / "member.toml"
    write_file(target, cargo_manifest().replace('name = "example"', 'name = "app"'))
    member = tmp_path / "crates" / "app" / "Cargo.toml"
    member.parent.mkdir(parents=True)
    create_symlink(member, target, directory=False)

    assert not rust_format_policy.has_format_lane(tmp_path, ["cargo fmt -p root -p app -- --check"])


def create_symlink(link: Path, target: Path, *, directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as error:
        if getattr(error, "winerror", None) == 1314 or error.errno in (
            errno.EPERM,
            errno.EACCES,
            errno.ENOSYS,
            errno.ENOTSUP,
        ):
            pytest.skip(f"OS does not permit symlink creation: {error}")
        raise


def set_format_command(root: Path, command: str) -> None:
    rack = root / "tests" / "rack.toml"
    text = rack.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    command_index = next(
        index + 1 for index, line in enumerate(lines) if line.strip() == 'id = "fmt"'
    )
    lines[command_index] = f"command = {json.dumps(command)}\n"
    write_file(rack, "".join(lines))


def assert_format_result(root: Path, *, passed: bool) -> None:
    result = named_result(run_language_checks(root), "Rust command surface")
    assert result.passed is passed, result.to_dict()
