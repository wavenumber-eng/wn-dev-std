"""Profile-specific conformance constants for repository checks."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from wn_dev_std.root_discovery import LEGACY_STANDALONE_CONFIG, PREFERRED_STANDALONE_CONFIG

ProfileName = Literal[
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
    "typescript-web-app",
    "python-ts-app",
    "rust-app",
    "rust-firmware",
    "zephyr-firmware",
]
SUPPORTED_PROFILES = (
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
    "typescript-web-app",
    "python-ts-app",
    "rust-app",
    "rust-firmware",
    "zephyr-firmware",
)

REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
)

REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/contracts",
    "docs/releases",
)

MIXED_MODE_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "CMakeLists.txt",
    "CMakePresets.json",
    "dist/README.md",
    "scripts/validate_native.py",
    "scripts/validate_python_package.py",
)

CPP_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "CMakeLists.txt",
    "CMakePresets.json",
    "signoff.toml",
)
CPP_REQUIRED_ROOT_FILES = tuple(path for path in REQUIRED_ROOT_FILES if path != "pyproject.toml")

ZEPHYR_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "signoff.toml",
    "src",
    "tests/rack.toml",
    "dev-std.toml",
)

CSHARP_REQUIRED_PATHS = (
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "Directory.Build.props",
    "README.md",
    "build.ps1",
    "src",
    "tests",
    "dev-std.toml",
)

CSHARP_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/contracts",
    "docs/releases",
)

CSHARP_ANALYZER_PROPS = (
    ("EnforceCodeStyleInBuild", "true"),
    ("EnableNETAnalyzers", "true"),
)

CSHARP_EDITORCONFIG_RULES = (
    "dotnet_diagnostic.CA1502.severity = error",
    "dotnet_diagnostic.CA1505.severity = error",
    "dotnet_diagnostic.CA1506.severity = error",
)

JAVASCRIPT_WEB_REQUIRED_PATHS = (
    "src",
    "tests/rack.toml",
)

JAVASCRIPT_WEB_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "src",
    "tests",
    "dev-std.toml",
)

PYTHON_JS_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "src",
    "tests",
    "dev-std.toml",
)

PYTHON_JS_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/javascript-standard.html",
    "docs/contracts",
    "docs/releases",
)

TYPESCRIPT_WEB_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "package.json",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

PYTHON_TS_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "package.json",
    "pyproject.toml",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

TYPESCRIPT_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/typescript-standard.html",
    "docs/contracts",
    "docs/releases",
)

RUST_APP_REQUIRED_ROOT_FILES = (
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

RUST_FIRMWARE_REQUIRED_ROOT_FILES = (
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

RUST_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/rust-standard.html",
    "docs/contracts",
    "docs/releases",
)

ZEPHYR_REQUIRED_ROOT_FILES = (
    ".clang-format",
    ".clang-tidy",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "signoff.toml",
    "dev-std.toml",
)
PROFILE_REQUIRED_ROOT_FILES = {
    "cpp-library": CPP_REQUIRED_ROOT_FILES,
    "zephyr-firmware": ZEPHYR_REQUIRED_ROOT_FILES,
    "csharp-app": CSHARP_REQUIRED_PATHS,
    "javascript-web-app": JAVASCRIPT_WEB_REQUIRED_ROOT_FILES,
    "python-js-app": PYTHON_JS_REQUIRED_ROOT_FILES,
    "typescript-web-app": TYPESCRIPT_WEB_REQUIRED_ROOT_FILES,
    "python-ts-app": PYTHON_TS_REQUIRED_ROOT_FILES,
    "rust-app": RUST_APP_REQUIRED_ROOT_FILES,
    "rust-firmware": RUST_FIRMWARE_REQUIRED_ROOT_FILES,
}

CLANG_FORMAT_REQUIRED_SETTINGS = {
    "BasedOnStyle": "LLVM",
    "BreakBeforeBraces": "Allman",
    "IndentWidth": "4",
    "ColumnLimit": "100",
    "PointerAlignment": "Left",
    "SortIncludes": "true",
    "IncludeBlocks": "Preserve",
}


def project_profile(config: Mapping[str, object] | None) -> ProfileName:
    """Return the configured profile, defaulting to the Python package profile."""
    if config is None:
        return "python-package"
    profile = config.get("profile")
    if isinstance(profile, str) and profile in SUPPORTED_PROFILES:
        return profile
    return "python-package"


def required_root_files(profile: ProfileName) -> tuple[str, ...]:
    """Return root paths required for a profile."""
    return PROFILE_REQUIRED_ROOT_FILES.get(profile, REQUIRED_ROOT_FILES)


def required_doc_paths(profile: ProfileName) -> tuple[str, ...]:
    """Return documentation paths required for a profile."""
    if profile == "csharp-app":
        return CSHARP_REQUIRED_DOC_PATHS
    if profile in {"javascript-web-app", "python-js-app"}:
        return PYTHON_JS_REQUIRED_DOC_PATHS
    if profile in {"typescript-web-app", "python-ts-app"}:
        return TYPESCRIPT_REQUIRED_DOC_PATHS
    if profile in {"rust-app", "rust-firmware"}:
        return RUST_REQUIRED_DOC_PATHS
    if profile == "zephyr-firmware":
        return (
            "docs/setup.html",
            "docs/architecture.html",
            "docs/design",
            "docs/design/zephyr-standard.html",
            "docs/contracts",
            "docs/releases",
        )
    return REQUIRED_DOC_PATHS


def required_path_exists(root: Path, relative_path: str) -> bool:
    """Return whether a required path exists, including compatibility markers."""
    if (root / relative_path).exists():
        return True
    if relative_path == PREFERRED_STANDALONE_CONFIG:
        return (root / LEGACY_STANDALONE_CONFIG).exists()
    return False
