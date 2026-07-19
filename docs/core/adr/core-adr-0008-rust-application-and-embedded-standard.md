+++
type = "adr"
id = "core-adr-0008"
domain = "core"
status = "accepted"
title = "Rust Has Host And Firmware Profiles"
created = "2026-07-18"
plan_refs = ["rust-standard"]
requirement_refs = ["core-req-0008"]
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
+++

# Rust Has Host And Firmware Profiles

The decision is to approve Rust as a greenfield Wavenumber implementation
language when project ownership justifies the toolchain, with two first-slice
profiles: `rust-app` and `rust-firmware`.

`rust-app` covers host-side Rust applications, services, CLIs, and ordinary
libraries where `std` is available and the project owns application signoff.
The profile requires Cargo metadata, a committed lockfile, a checked-in
toolchain file or documented ambient-stable exception, Rust-owned source,
unsafe-code lint posture, and signoff commands that run rustfmt, Cargo check,
Clippy, tests, and rustdoc warnings.

`rust-firmware` is separate because embedded Rust adds cross targets, `no_std`
intent, linker and memory layout artifacts, flashing runners, panic and
allocator policy, and hardware signoff. Those concerns are not optional
variants of a host application profile; they are a different audit boundary.

Cargo, rustfmt, Clippy, rustdoc, rustup, and Rack are the default tooling
surface. Stable Rust is the default channel. Nightly is exception-only and must
be pinned with rationale and a review trigger.

Unsafe code is forbidden by default for `rust-app`. Firmware may use reviewed
unsafe at hardware, register, generated-binding, or FFI boundaries, but the
exception must name the scope and review trigger. The audit validates the
configuration and lint posture; Rust source semantics remain the responsibility
of rustc, Clippy, rustdoc, and project tests.

Tokio and Embassy are recommended baselines, not required dependencies. Tokio
fits host async I/O, networking, timers, and service runtimes. Embassy fits
supported embedded async firmware. Projects may remain synchronous, use a
framework-owned runtime, use RTIC, or use a vendor or RTOS scheduler when that
choice is documented.

Polyglot contract repositories may keep Rust under `src/rs` or `src/rust`
beside other language implementations. The Rust checker validates the
configured Rust root and Cargo shape without claiming sibling language roots.
