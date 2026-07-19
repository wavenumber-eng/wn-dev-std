"""Rust standard profile data."""

from __future__ import annotations

RUST_APP_RULE_ITEMS = (
    (
        "workflow",
        "Cargo with locked signoff",
        "Cargo owns build/test/docs while --locked keeps dependency resolution deterministic.",
    ),
    (
        "toolchain",
        "rust-toolchain.toml or documented ambient stable",
        "Rustup metadata makes channel, components, and targets reviewable.",
    ),
    (
        "metadata",
        "edition and rust-version",
        "Rust projects need an explicit edition and MSRV policy.",
    ),
    (
        "format",
        "cargo fmt --all -- --check",
        "Use the standard formatter before source review.",
    ),
    (
        "static-analysis",
        "cargo clippy -- -D warnings",
        "Let Clippy and rustc own Rust semantic checks.",
    ),
    (
        "typecheck",
        "cargo check",
        "Catch compilation and feature-surface drift without emitting artifacts.",
    ),
    (
        "test-runner",
        "cargo test plus cargo test --doc",
        "Keep unit, integration, and doctest behavior in the normal signoff path.",
    ),
    (
        "docs.rustdoc",
        'RUSTDOCFLAGS="-D warnings" cargo doc',
        "Rustdoc warnings are a project quality gate for public and internal APIs.",
    ),
    (
        "unsafe",
        'unsafe_code = "forbid"',
        "Unsafe code is exception-only in host application-owned Rust.",
    ),
    (
        "workspace",
        "resolver and workspace metadata",
        "Multi-crate projects centralize package, lint, dependency, and profile policy.",
    ),
    (
        "source-root",
        "src or configured src/rs",
        "Polyglot repositories may partition Rust source beside other languages.",
    ),
    (
        "runtime",
        "Tokio recommended for host async",
        "Async I/O and service runtimes should default to Tokio or document an alternative.",
    ),
    (
        "third-party",
        "auditable dependency policy",
        "Dependency, license, and generated/vendor boundaries need explicit review.",
    ),
    (
        "ci.os",
        "ubuntu, windows, macos",
        "Catch toolchain, filesystem, and platform drift early.",
    ),
)

RUST_FIRMWARE_RULE_ITEMS = (
    ("inherits", "rust-app", "Use the Cargo, rustup, rustfmt, Clippy, test, and rustdoc base."),
    (
        "target",
        "target triple or custom target spec",
        "Cross-compilation target selection must be explicit and reviewable.",
    ),
    (
        "no_std",
        "metadata and docs",
        "Firmware intent is declared without fragile Python parsing of Rust attributes.",
    ),
    (
        "cargo-config",
        ".cargo/config.toml",
        "Target, runner, linker, and rustflags live in Cargo-visible configuration.",
    ),
    (
        "memory-layout",
        "memory.x, link.x provider, or linker script",
        "Embedded memory and linker behavior is a required review artifact.",
    ),
    (
        "runner",
        "Embed.toml, probe-rs, cargo-embed, or wrapper",
        "Flashing and debug commands must be repeatable outside one developer machine.",
    ),
    (
        "panic",
        "documented panic strategy",
        "Panic behavior affects size, diagnostics, and field failure modes.",
    ),
    (
        "allocator",
        "documented allocation policy",
        "Firmware allocation must be absent, bounded, or explicitly reviewed.",
    ),
    (
        "unsafe",
        "reviewed hardware/FFI/register boundaries",
        "Embedded unsafe is allowed only where low-level interfaces require it.",
    ),
    (
        "hardware-signoff",
        "document setup, flashing, debug, and release tests",
        "Board-specific validation needs durable setup and evidence.",
    ),
    (
        "runtime",
        "Embassy recommended for supported async firmware",
        "Async firmware should use Embassy where target and HAL maturity fit.",
    ),
)

RUST_APP_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "Cargo.toml",
    "Cargo.lock",
    "rust-toolchain.toml",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

RUST_FIRMWARE_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    ".cargo/config.toml",
    "Cargo.toml",
    "Cargo.lock",
    "rust-toolchain.toml",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

RUST_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/rust-standard.html",
    "docs/contracts/",
    "docs/releases/",
)
