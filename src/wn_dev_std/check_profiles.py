"""Profile-specific conformance constants for repository checks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

ProfileName = Literal[
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
    "zephyr-firmware",
]
SUPPORTED_PROFILES = (
    "python-package",
    "python-native-wasm",
    "cpp-library",
    "csharp-app",
    "javascript-web-app",
    "python-js-app",
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

ZEPHYR_REQUIRED_PATHS = (
    ".clang-format",
    ".clang-tidy",
    "signoff.toml",
    "src",
    "tests/rack.toml",
    "wn-dev-std.toml",
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
    "wn-dev-std.toml",
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
    "wn-dev-std.toml",
)

PYTHON_JS_REQUIRED_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "src",
    "tests",
    "wn-dev-std.toml",
)

PYTHON_JS_REQUIRED_DOC_PATHS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design",
    "docs/design/javascript-standard.html",
    "docs/contracts",
    "docs/releases",
)

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
    if profile == "cpp-library":
        return tuple(path for path in REQUIRED_ROOT_FILES if path != "pyproject.toml")
    if profile == "zephyr-firmware":
        return (
            ".clang-format",
            ".clang-tidy",
            ".gitattributes",
            ".gitignore",
            "AGENTS.md",
            "README.md",
            "signoff.toml",
            "wn-dev-std.toml",
        )
    if profile == "csharp-app":
        return CSHARP_REQUIRED_PATHS
    if profile == "javascript-web-app":
        return JAVASCRIPT_WEB_REQUIRED_ROOT_FILES
    if profile == "python-js-app":
        return PYTHON_JS_REQUIRED_ROOT_FILES
    return REQUIRED_ROOT_FILES


def required_doc_paths(profile: ProfileName) -> tuple[str, ...]:
    """Return documentation paths required for a profile."""
    if profile == "csharp-app":
        return CSHARP_REQUIRED_DOC_PATHS
    if profile in {"javascript-web-app", "python-js-app"}:
        return PYTHON_JS_REQUIRED_DOC_PATHS
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
