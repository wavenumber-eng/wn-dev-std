+++
type = "requirement"
id = "core-req-0008"
domain = "core"
status = "implemented"
title = "Rust Projects Use Cargo Toolchain Guardrails"
created = "2026-07-18"
plan_refs = ["rust-standard"]
adr_refs = ["core-adr-0008"]
design_refs = [
  "docs/design/rust-standard.html",
  "docs/design/audit-standard.html",
  "docs/design/cli.html",
  "docs/design/documentation-standard.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/rust_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/rust_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/rust_standard_profiles.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/standard_model.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/check_profiles.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/standards.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/checks.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/cli/commands/standard.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/contracts/wn_dev_std_config.schema.v0.json"

[[implementation_refs]]
kind = "local_file"
target = "docs/contracts/interface_manifest.v0.json"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_default_rust_app_standard_contains_cargo_guardrails"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_default_rust_firmware_standard_contains_embedded_guardrails"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_021_rust_policy.py::test_rust_app_profile_language_checks_pass_for_minimal_repo"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_021_rust_policy.py::test_rust_profile_accepts_polyglot_src_rs_root"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_021_rust_policy.py::test_rust_firmware_profile_language_checks_pass_for_minimal_repo"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_002_docs_contracts.py::test_config_schema_matches_runtime_config_surface"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_004_repo_hygiene.py::test_rust_policy_is_documented"
+++

# Rust Projects Use Cargo Toolchain Guardrails

New Wavenumber Rust projects must use Cargo, rustup toolchain metadata, rustfmt,
Clippy, rustdoc, and Rack or equivalent signoff to make project shape and
defect-prevention guardrails visible before source is reviewed.

The implementation must add two first-slice profiles:

- `rust-app` for host-side Rust applications, services, CLIs, and ordinary
  `std` libraries with application-owned signoff.
- `rust-firmware` for embedded Rust firmware that needs `no_std` intent,
  cross-compilation targets, linker or memory layout metadata, runner or
  flashing metadata, and hardware-aware signoff.

Rust profile audits must require `Cargo.toml`, `Cargo.lock`,
`rust-toolchain.toml`, a Rust-owned source root, `tests/rack.toml`, and a
documented Rust standard design doc unless a documented ambient-toolchain
exception is declared. The first slice requires `Cargo.lock` for applications,
firmware, and workspaces; library-only relaxation is a future policy change.

The audit must parse Cargo and rustup TOML with `tomllib`. It must validate
package or workspace metadata, `edition`, `rust-version`, workspace resolver
policy, lint posture for `unsafe_code`, toolchain channel/components/targets,
and signoff command declarations. It must not parse Rust source syntax.

Rust projects may configure a language-partitioned source root such as
`src/rs` or `src/rust` for polyglot repositories where Python, C++, C#, Rust,
and JavaScript implement the same contracts. The audit must inspect only the
configured Rust root for owned Rust source and must not treat sibling language
roots as Rust-owned implementation.

All Rust profiles must declare signoff coverage for `cargo fmt --all --
--check`, `cargo check`, `cargo clippy`, `cargo test`, and
`RUSTDOCFLAGS="-D warnings" cargo doc`. Cargo commands in CI must use
deterministic locked dependency resolution, typically through `--locked`.

Embedded Rust projects must additionally declare target metadata,
`.cargo/config.toml`, memory or linker artifacts such as `memory.x` or a
documented `link.x` provider, runner or flashing metadata such as `Embed.toml`,
`probe-rs`, `cargo-embed`, or a project wrapper, `no_std` intent, panic policy,
allocator policy, hardware setup, and a host-test strategy.

Tokio and Embassy are recommended scenario defaults rather than required
dependencies. Host async or networked Rust applications should consider Tokio
unless they document a synchronous, smaller-executor, or framework-owned
runtime choice. Embedded async firmware should consider Embassy when target
and HAL support are mature enough, but simpler loops, RTIC, vendor SDKs, or
RTOS schedulers may document a different model.
