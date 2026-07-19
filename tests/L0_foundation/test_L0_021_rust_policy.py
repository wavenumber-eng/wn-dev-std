from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult


def test_rust_app_profile_language_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)

    results = run_language_checks(tmp_path)

    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_rust_profile_accepts_polyglot_src_rs_root(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        extra_config='[rust]\nsource_root = "src/rs"\n',
        source_root="src/rs",
    )
    write_file(tmp_path / "src" / "py" / "data_models" / "example.py", "VALUE = 1\n")
    write_file(tmp_path / "src" / "cpp" / "data_models" / "example.cpp", "int value = 1;\n")
    write_file(
        tmp_path / "src" / "js" / "data_models" / "example.js",
        "export const value = 1;\n",
    )

    source = named_result(run_language_checks(tmp_path), "Rust source")

    assert source.passed
    assert "src/rs" in source.detail


def test_rust_profile_requires_cargo_toml(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    (tmp_path / "Cargo.toml").unlink()

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "Cargo.toml is required" in cargo.detail


def test_rust_profile_requires_cargo_lock(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    (tmp_path / "Cargo.lock").unlink()

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "Cargo.lock is required" in cargo.detail


def test_rust_profile_requires_toolchain_or_ambient_exception(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    (tmp_path / "rust-toolchain.toml").unlink()

    toolchain = named_result(run_language_checks(tmp_path), "Rust toolchain")

    assert not toolchain.passed
    assert "rust-toolchain.toml is required" in toolchain.detail


def test_rust_profile_accepts_ambient_stable_toolchain_exception(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        extra_config="""
        [rust.exceptions]
        ambient_toolchain = "docs/design/rust-toolchain-exception.html"
        """,
    )
    (tmp_path / "rust-toolchain.toml").unlink()
    write_file(
        tmp_path / "docs" / "design" / "rust-toolchain-exception.html",
        '<!doctype html><html><body data-doc-status="accepted">Stable</body></html>\n',
    )

    toolchain = named_result(run_language_checks(tmp_path), "Rust toolchain")

    assert toolchain.passed
    assert toolchain.warning


def test_rust_profile_rejects_toolchain_without_required_components(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        toolchain=dedent(
            """
            [toolchain]
            channel = "stable"
            components = ["rustfmt"]
            """
        ).lstrip(),
    )

    toolchain = named_result(run_language_checks(tmp_path), "Rust toolchain")

    assert not toolchain.passed
    assert "toolchain.components must include clippy" in toolchain.detail


def test_rust_profile_rejects_missing_package_metadata(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=dedent(
            """
            [package]
            name = "example"
            version = "0.1.0"

            [lints.rust]
            unsafe_code = "forbid"
            """
        ).lstrip(),
    )

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "package.edition is required" in cargo.detail
    assert "package.rust-version is required" in cargo.detail


def test_rust_workspace_profile_accepts_resolver_and_workspace_lints(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=dedent(
            """
            [workspace]
            members = ["crates/app"]
            resolver = "3"

            [workspace.package]
            edition = "2024"
            rust-version = "1.85"

            [workspace.lints.rust]
            unsafe_code = "forbid"
            """
        ).lstrip(),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert cargo.passed


def test_rust_workspace_rejects_member_without_lints_workspace_opt_in(
    tmp_path: Path,
) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=workspace_manifest(),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=False)

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "workspace member crates/app must declare lints.workspace = true" in cargo.detail


def test_rust_workspace_rejects_member_unsafe_lint_override(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=hybrid_workspace_manifest(),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(
        tmp_path,
        inherit_metadata=True,
        inherit_lints=False,
        unsafe_lint="allow",
    )

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "workspace member crates/app lints.rust.unsafe_code is 'allow'" in cargo.detail


def test_rust_workspace_honors_exclude_and_ignores_glob_files(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=workspace_manifest(members='["crates/*"]', exclude='["crates/ignored"]'),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    write_file(tmp_path / "crates" / "README.md", "workspace notes\n")
    write_file(
        tmp_path / "crates" / "ignored" / "Cargo.toml",
        dedent(
            """
            [package]
            name = "ignored"
            version = "0.1.0"

            [lints.rust]
            unsafe_code = "allow"
            """
        ).lstrip(),
    )

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert cargo.passed


def test_rust_workspace_rejects_edition_2024_without_resolver_3(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=workspace_manifest(resolver="2"),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert 'Edition 2024 workspaces require resolver = "3"' in cargo.detail


def test_rust_profile_requires_lockfile_in_audited_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    write_minimal_rust_project(project)
    (project / "Cargo.lock").unlink()
    write_file(tmp_path / "Cargo.lock", "stray parent lock\n")

    cargo = named_result(run_language_checks(project), "Cargo metadata")

    assert not cargo.passed
    assert "Cargo.lock is required" in cargo.detail


def test_rust_app_allows_unsafe_deny_with_documented_exception(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=cargo_manifest().replace('unsafe_code = "forbid"', 'unsafe_code = "deny"'),
        extra_config="""
        [rust.exceptions]
        unsafe = "docs/design/unsafe-boundary.html"
        """,
    )
    write_file(
        tmp_path / "docs" / "design" / "unsafe-boundary.html",
        '<!doctype html><html><body data-doc-status="accepted">Unsafe boundary</body></html>\n',
    )

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert cargo.passed
    assert cargo.warning


def test_rust_exception_local_anchor_still_requires_existing_doc(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=cargo_manifest().replace('unsafe_code = "forbid"', 'unsafe_code = "deny"'),
        extra_config="""
        [rust.exceptions]
        unsafe = "docs/design/missing-unsafe.html#boundary"
        """,
    )

    cargo = named_result(run_language_checks(tmp_path), "Cargo metadata")

    assert not cargo.passed
    assert "docs/design/missing-unsafe.html does not exist" in cargo.detail


def test_rust_profile_rejects_missing_rustdoc_warning_gate(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    rack = (tmp_path / "tests" / "rack.toml").read_text(encoding="utf-8")
    rack = rack.replace(
        'command = "RUSTDOCFLAGS=\\"-D warnings\\" cargo doc --workspace --no-deps --locked"\n',
        "",
    )
    write_file(tmp_path / "tests" / "rack.toml", rack)

    command = named_result(run_language_checks(tmp_path), "Rust command surface")

    assert not command.passed
    assert "RUSTDOCFLAGS" in command.detail
    assert "cargo doc" in command.detail


def test_rust_command_surface_requires_locked_marker_per_command(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    rack = (tmp_path / "tests" / "rack.toml").read_text(encoding="utf-8")
    rack = rack.replace(
        'command = "cargo test --workspace --locked"\n',
        'command = "cargo test --workspace"\n',
    )
    write_file(tmp_path / "tests" / "rack.toml", rack)

    command = named_result(run_language_checks(tmp_path), "Rust command surface")

    assert not command.passed
    assert "cargo test --locked" in command.detail


def test_rust_firmware_profile_language_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path, profile="rust-firmware", firmware=True)

    results = run_language_checks(tmp_path)

    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_rust_firmware_profile_requires_memory_layout_metadata(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path, profile="rust-firmware", firmware=True)
    config = (tmp_path / "dev-std.toml").read_text(encoding="utf-8")
    config = config.replace('memory_layout = "memory.x"\n', "")
    write_file(tmp_path / "dev-std.toml", config)

    firmware = named_result(run_language_checks(tmp_path), "Rust firmware")

    assert not firmware.passed
    assert "rust.firmware.memory_layout is required" in firmware.detail


def test_rust_firmware_profile_rejects_target_not_in_toolchain(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        profile="rust-firmware",
        firmware=True,
        toolchain=dedent(
            """
            [toolchain]
            channel = "stable"
            components = ["rustfmt", "clippy"]
            targets = ["thumbv6m-none-eabi"]
            """
        ).lstrip(),
    )

    toolchain = named_result(run_language_checks(tmp_path), "Rust toolchain")

    assert not toolchain.passed
    assert "toolchain.targets must include thumbv7em-none-eabihf" in toolchain.detail


def test_rust_firmware_profile_rejects_cargo_config_target_mismatch(
    tmp_path: Path,
) -> None:
    write_minimal_rust_project(tmp_path, profile="rust-firmware", firmware=True)
    cargo_config = (tmp_path / ".cargo" / "config.toml").read_text(encoding="utf-8")
    cargo_config = cargo_config.replace("thumbv7em-none-eabihf", "thumbv6m-none-eabi")
    write_file(tmp_path / ".cargo" / "config.toml", cargo_config)

    firmware = named_result(run_language_checks(tmp_path), "Rust firmware")

    assert not firmware.passed
    assert ".cargo/config.toml must declare target thumbv7em-none-eabihf" in firmware.detail


def test_rust_firmware_profile_accepts_project_runner_wrapper(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path, profile="rust-firmware", firmware=True)
    config = (tmp_path / "dev-std.toml").read_text(encoding="utf-8")
    config = config.replace('runner = "Embed.toml"', 'runner = "scripts/flash.ps1"')
    rack = (tmp_path / "tests" / "rack.toml").read_text(encoding="utf-8")
    rack = rack.replace(
        'command = "cargo embed --chip STM32F407VGTx"',
        'command = "pwsh scripts/flash.ps1"',
    )
    write_file(tmp_path / "dev-std.toml", config)
    write_file(tmp_path / "tests" / "rack.toml", rack)
    write_file(tmp_path / "scripts" / "flash.ps1", "Write-Output flash\n")

    command = named_result(run_language_checks(tmp_path), "Rust command surface")
    firmware = named_result(run_language_checks(tmp_path), "Rust firmware")

    assert command.passed
    assert firmware.passed


def run_language_checks(root: Path) -> tuple[CheckResult, ...]:
    return run_audit_checks(root, ("language",))


def named_result(results: tuple[CheckResult, ...], name: str) -> CheckResult:
    return next(result for result in results if result.name == name)


def write_minimal_rust_project(
    root: Path,
    *,
    profile: str = "rust-app",
    extra_config: str = "",
    cargo_toml: str | None = None,
    toolchain: str | None = None,
    source_root: str = "src",
    firmware: bool = False,
) -> None:
    for relative_path in (
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "README.md",
        "Cargo.lock",
    ):
        write_file(root / relative_path, "placeholder\n")
    write_file(root / "Cargo.toml", cargo_toml or cargo_manifest(firmware=firmware))
    write_file(root / "rust-toolchain.toml", toolchain or rust_toolchain(firmware=firmware))
    write_file(root / source_root / "main.rs", "fn main() {}\n")
    write_file(root / "tests" / "rack.toml", rack_manifest(firmware=firmware))
    write_file(
        root / "dev-std.toml",
        standard_config(
            profile,
            f"""
            distribution = "internal"
            languages = ["rust"]
            strict = true
            artifact_policy = "transient-dist"
            {dedent(extra_config).strip()}
            {firmware_config() if firmware else ""}
            """,
        ),
    )
    if firmware:
        write_minimal_firmware_files(root)


def cargo_manifest(*, firmware: bool = False) -> str:
    release_profile = ""
    if firmware:
        release_profile = """
        [profile.release]
        panic = "abort"
        lto = true
        codegen-units = 1
        """
    return dedent(
        f"""
        [package]
        name = "example"
        version = "0.1.0"
        edition = "2024"
        rust-version = "1.85"

        [lints.rust]
        unsafe_code = "forbid"

        {dedent(release_profile).strip()}
        """
    ).lstrip()


def workspace_manifest(
    *,
    resolver: str = "3",
    members: str = '["crates/app"]',
    exclude: str = "",
) -> str:
    exclude_line = f"exclude = {exclude}" if exclude else ""
    return dedent(
        f"""
        [workspace]
        members = {members}
        {exclude_line}
        resolver = "{resolver}"

        [workspace.package]
        edition = "2024"
        rust-version = "1.85"

        [workspace.lints.rust]
        unsafe_code = "forbid"
        """
    ).lstrip()


def hybrid_workspace_manifest() -> str:
    return dedent(
        """
        [package]
        name = "root"
        version = "0.1.0"
        edition = "2024"
        rust-version = "1.85"

        [lints.rust]
        unsafe_code = "forbid"

        [workspace]
        members = ["crates/app"]
        resolver = "3"

        [workspace.package]
        edition = "2024"
        rust-version = "1.85"

        [workspace.lints.rust]
        unsafe_code = "forbid"
        """
    ).lstrip()


def write_workspace_member_manifest(
    root: Path,
    *,
    inherit_metadata: bool,
    inherit_lints: bool,
    unsafe_lint: str | None = None,
) -> None:
    metadata = (
        "edition.workspace = true\nrust-version.workspace = true"
        if inherit_metadata
        else 'edition = "2024"\nrust-version = "1.85"'
    )
    if unsafe_lint is not None:
        lints = f'[lints.rust]\nunsafe_code = "{unsafe_lint}"'
    elif inherit_lints:
        lints = "[lints]\nworkspace = true"
    else:
        lints = ""
    write_file(
        root / "crates" / "app" / "Cargo.toml",
        dedent(
            f"""
            [package]
            name = "app"
            version = "0.1.0"
            {metadata}

            {lints}
            """
        ).lstrip(),
    )


def rust_toolchain(*, firmware: bool = False) -> str:
    targets = '\ntargets = ["thumbv7em-none-eabihf"]' if firmware else ""
    return dedent(
        f"""
        [toolchain]
        channel = "stable"
        components = ["rustfmt", "clippy"]{targets}
        """
    ).lstrip()


def rack_manifest(*, firmware: bool = False) -> str:
    target_arg = " --target thumbv7em-none-eabihf" if firmware else ""
    check_targets = "" if firmware else " --all-targets"
    clippy_targets = "" if firmware else " --all-targets --all-features"
    clippy_command = f"cargo clippy --workspace{clippy_targets}{target_arg} --locked -- -D warnings"
    firmware_commands = ""
    if firmware:
        firmware_commands = """
        [[subtests]]
        id = "firmware-build"
        command = "cargo build --release --target thumbv7em-none-eabihf --locked"

        [[subtests]]
        id = "firmware-runner"
        command = "cargo embed --chip STM32F407VGTx"
        """
    return dedent(
        f"""
        [[subtests]]
        id = "fmt"
        command = "cargo fmt --all -- --check"

        [[subtests]]
        id = "check"
        command = "cargo check --workspace{check_targets}{target_arg} --locked"

        [[subtests]]
        id = "clippy"
        command = "{clippy_command}"

        [[subtests]]
        id = "test"
        command = "cargo test --workspace --locked"

        [[subtests]]
        id = "doctest"
        command = "cargo test --doc --workspace --locked"

        [[subtests]]
        id = "doc"
        command = "RUSTDOCFLAGS=\\"-D warnings\\" cargo doc --workspace --no-deps --locked"

        {dedent(firmware_commands).strip()}
        """
    ).lstrip()


def firmware_config() -> str:
    return dedent(
        """
        [rust.firmware]
        target = "thumbv7em-none-eabihf"
        no_std_ref = "docs/design/rust-firmware-runtime.html"
        panic_ref = "docs/design/rust-firmware-runtime.html"
        allocator_ref = "docs/design/rust-firmware-runtime.html"
        hardware_ref = "docs/setup.html"
        memory_layout = "memory.x"
        runner = "Embed.toml"
        """
    ).strip()


def write_minimal_firmware_files(root: Path) -> None:
    write_file(
        root / ".cargo" / "config.toml",
        dedent(
            """
            [build]
            target = "thumbv7em-none-eabihf"

            [target.thumbv7em-none-eabihf]
            runner = "probe-rs run --chip STM32F407VGTx"
            """
        ).lstrip(),
    )
    write_file(root / "memory.x", "MEMORY { FLASH : ORIGIN = 0x08000000, LENGTH = 512K }\n")
    write_file(root / "Embed.toml", '[default.general]\nchip = "STM32F407VGTx"\n')
    write_file(
        root / "docs" / "design" / "rust-firmware-runtime.html",
        (
            '<!doctype html><html><body data-doc-status="accepted">'
            "no_std panic allocator</body></html>\n"
        ),
    )
    write_file(root / "docs" / "setup.html", "hardware setup\n")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
