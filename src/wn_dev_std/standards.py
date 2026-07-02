"""Standard profile data exposed by the reference package."""

from __future__ import annotations

import json
from dataclasses import dataclass
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

STANDARD_VERSION = "2026.7.2"


@dataclass(frozen=True, slots=True)
class StrictRule:
    """A strict rule with a short rationale."""

    key: str
    value: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable rule dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class PythonStandard:
    """Current strict project standard profile."""

    name: str
    version: str
    status: str
    rules: tuple[StrictRule, ...]
    required_files: tuple[str, ...]
    required_docs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable standard dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "rules": [rule.to_dict() for rule in self.rules],
            "required_files": list(self.required_files),
            "required_docs": list(self.required_docs),
        }


COMPATIBILITY_PRUNING_RULE = StrictRule(
    "compatibility-pruning",
    "configured forbidden legacy surface",
    "Old compatibility shims, environment variables, and aliases need a signoff gate.",
)
PUBLIC_PR_HYGIENE_RULE = StrictRule(
    "pr-hygiene.public",
    "linked issue + Conventional Commit CI",
    "Public PRs need reviewable issue context and machine-checkable metadata.",
)

MIXED_MODE_RULES = (
    StrictRule("workflow.python", "uv", "Use one Python environment and lock workflow."),
    StrictRule("workflow.native", "cmake + ctest", "Keep native builds portable."),
    StrictRule("workflow.wasm", "pinned emsdk or equivalent", "Keep browser builds reproducible."),
    StrictRule(
        "complexity.native",
        "new code cyclomatic_complexity <= 10",
        "Use Lizard signoff and baselines so old debt is visible without allowing new debt.",
    ),
    StrictRule(
        "signoff.native",
        "signoff.toml with lizard=fail",
        "Make native source size, function size, and complexity gates project-local.",
    ),
    StrictRule(
        "inherits",
        "cpp-library",
        "Use the same formatter, preset, warning, and native signoff rules.",
    ),
    StrictRule("lockfile", "commit uv.lock", "Make Python installs reproducible."),
    StrictRule(
        "build-backend",
        "documented native wheel backend",
        "Bundled executable wheels need explicit build hooks.",
    ),
    StrictRule(
        "native-artifacts",
        "dist/native/<platform>/",
        "Keep committed runtime binaries grouped by OS and architecture.",
    ),
    StrictRule(
        "wasm-artifacts",
        "dist/wasm/<target>/",
        "Keep browser, worker, and test builds separated by runtime target.",
    ),
    StrictRule(
        "artifact-manifest",
        "dist/README.md or manifest",
        "Document artifact roles, regeneration, and release policy.",
    ),
    StrictRule(
        "version-sync",
        "package, CMake, CLI, ABI",
        "Prevent mismatched Python/native/runtime releases.",
    ),
    StrictRule("test-runner", "rack + pytest + ctest", "Cover Python and native strata."),
    StrictRule("typing", "pyright strict", "Catch Python wrapper interface drift early."),
    StrictRule("lint", "ruff + clang-format", "Keep Python and native style automated."),
    StrictRule("static-analysis", "pyright + clang-tidy", "Catch wrapper and native drift early."),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
    StrictRule("ci.os", "ubuntu, windows, macos", "Build platform wheels on real targets."),
    StrictRule("ci.wasm", "separate wasm lane", "Avoid hiding browser/toolchain failures."),
    StrictRule("release", "GitHub Release published", "Allow final review before publish."),
)

MIXED_MODE_REQUIRED_FILES = (
    ".clang-format",
    ".clang-tidy",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CMakeLists.txt",
    "CMakePresets.json",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "setup.py",
    "tests/rack.toml",
)

MIXED_MODE_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/distribution.html",
    "docs/design/native-interface.html",
    "docs/design/python-package.html",
    "docs/design/wasm.html",
    "docs/contracts/",
    "docs/releases/",
)

CPP_RULES = (
    StrictRule("build-system", "cmake", "Keep native builds portable across toolchains."),
    StrictRule("presets", "CMakePresets.json", "Make configure/build/test lanes repeatable."),
    StrictRule("generator", "ninja", "Ninja is the default generator for native projects."),
    StrictRule(
        "compile-commands",
        "CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "Required for clang-tidy and editor tooling.",
    ),
    StrictRule("format", "clang-format", "All owned C++ must use the committed formatter."),
    StrictRule(
        "format.style",
        "LLVM base, Allman, 4 spaces, 100 columns",
        "Matches the current native-library convention.",
    ),
    StrictRule("static-analysis", "clang-tidy", "New native code starts with analysis enabled."),
    StrictRule(
        "integer-widths",
        "std::int32_t/std::uint32_t/std::int64_t/std::uint64_t",
        "Owned integer storage uses fixed-width spellings instead of short, long, or long long.",
    ),
    StrictRule(
        "warnings",
        "MSVC /W4, Clang/GCC -Wall -Wextra -Wpedantic",
        "Catch compiler-visible defects early.",
    ),
    StrictRule(
        "warnings-as-errors",
        "owned code in CI",
        "Release-facing code should not accumulate warning debt.",
    ),
    StrictRule("test-runner", "ctest", "Register native tests with CTest."),
    StrictRule("test-orchestration", "rack", "Expose native lanes and release gates explicitly."),
    StrictRule(
        "complexity.native",
        "new code cyclomatic_complexity <= 10",
        "Use Lizard signoff and baselines so old debt is visible without allowing new debt.",
    ),
    StrictRule(
        "signoff.native",
        "signoff.toml with lizard=fail",
        "Make native source size, function size, and complexity gates project-local.",
    ),
    StrictRule(
        "sanitizers",
        "asan+ubsan where supported",
        "Run memory and undefined-behavior checks outside MSVC-only lanes.",
    ),
    StrictRule(
        "public-headers",
        "deliberate include/ boundary",
        "Keep public API surface reviewable and stable.",
    ),
    StrictRule(
        "private-headers",
        "internal/ or private source tree",
        "Prevent accidental downstream dependency on internals.",
    ),
    StrictRule(
        "c-abi",
        "versioned when exposed",
        "Never throw C++ exceptions across C, Python, or WASM boundaries.",
    ),
    StrictRule(
        "third-party",
        "pinned provenance and license",
        "Vendored or fetched dependencies must be auditable.",
    ),
    StrictRule(
        "generated-code",
        "document generator and regeneration command",
        "Generated native sources need a maintained source of truth.",
    ),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
    StrictRule("ci.os", "ubuntu, windows, macos", "Catch compiler and platform differences early."),
)

CPP_REQUIRED_FILES = (
    ".clang-format",
    ".clang-tidy",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CMakeLists.txt",
    "CMakePresets.json",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "signoff.toml",
    "tests/rack.toml",
)

CPP_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/cpp-standard.html",
    "docs/contracts/",
    "docs/releases/",
)

ZEPHYR_RULES = (
    StrictRule("inherits", "cpp-library", "Use the same C/C++ formatter and static-analysis base."),
    StrictRule(
        "workflow", "west + app-local scripts", "Keep Zephyr builds reproducible and simple."
    ),
    StrictRule(
        "scope",
        "owned application code first",
        "Exclude Zephyr, west modules, generated code, vendor code, and build output by default.",
    ),
    StrictRule(
        "compile-commands",
        "CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "clang-tidy and editor tooling need the active Zephyr build arguments.",
    ),
    StrictRule(
        "format",
        "clang-format prebuild report/fail lane",
        "Formatting should be visible in the normal build loop before it becomes a hard gate.",
    ),
    StrictRule(
        "static-analysis",
        "clang-tidy postbuild report/fail lane",
        "Analyze only files present in the active compile database.",
    ),
    StrictRule(
        "complexity.native",
        "new code cyclomatic_complexity <= 10",
        "Embedded control paths need small, testable functions; use baselines for legacy debt.",
    ),
    StrictRule(
        "size.file",
        "physical lines <= 2200",
        "Large owned files should be split before they become unreviewable.",
    ),
    StrictRule(
        "size.function",
        "function lines <= 220",
        "Large functions need decomposition even when cyclomatic complexity is low.",
    ),
    StrictRule(
        "target-toolchains",
        "document clang target gaps",
        "Xtensa and other non-host LLVM gaps may be report-only until a matching clang exists.",
    ),
    StrictRule(
        "setup-doc",
        "document Windows and CI tools",
        "Zephyr machines need explicit west, SDK, dtc, LLVM, lizard, and flashing setup.",
    ),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
)

ZEPHYR_REQUIRED_FILES = (
    ".clang-format",
    ".clang-tidy",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "signoff.toml",
    "tests/rack.toml",
    "dev-std.toml",
)

ZEPHYR_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/zephyr-standard.html",
    "docs/contracts/",
    "docs/releases/",
)

CSHARP_RULES = (
    StrictRule("build-system", "dotnet sdk-style projects", "Keep C# builds scriptable."),
    StrictRule("props", "Directory.Build.props", "Centralize analyzer and language policy."),
    StrictRule("format", ".editorconfig", "Keep C# style and analyzer severities explicit."),
    StrictRule(
        "analyzers",
        "EnableNETAnalyzers + EnforceCodeStyleInBuild",
        "Surface maintainability and style issues during build.",
    ),
    StrictRule(
        "complexity",
        "CA1502/CA1505/CA1506 errors",
        "Block new overly complex methods, unmaintainable code, and excessive coupling.",
    ),
    StrictRule(
        "nullable",
        "explicit project policy",
        "Declare nullable enable/disable/ratchet state instead of inheriting defaults.",
    ),
    StrictRule("test-runner", "dotnet test", "Unit-test pure helpers outside host runtime."),
    StrictRule(
        "host-boundaries",
        "thin unmockable boundary code",
        "Route host API behavior through pure helpers that can be unit-tested.",
    ),
    StrictRule(
        "artifact-policy",
        "document dist/ or installer output",
        "Separate committed runtime packages from local build scratch.",
    ),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
    StrictRule(
        "ci.os", "windows plus portable helper tests", "Catch .NET and host differences early."
    ),
)

CSHARP_REQUIRED_FILES = (
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

CSHARP_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/contracts/",
    "docs/releases/",
)

JAVASCRIPT_WEB_RULES = (
    StrictRule(
        "workflow",
        "no-build browser runtime first",
        "Prefer plain HTML, CSS, and browser JavaScript until a build step pays for itself.",
    ),
    StrictRule(
        "toolchain",
        "optional package.json with lockfile",
        "Use Node only when dependencies, bundling, or browser test tooling justify it.",
    ),
    StrictRule(
        "modules",
        "ES modules or manifest-ordered IIFEs",
        "Browser load order and global namespace ownership must be documented.",
    ),
    StrictRule(
        "typecheck.javascript",
        "checked JS with JSDoc or TypeScript",
        "Use jsconfig/tsconfig and @ts-check before moving reusable code to TypeScript.",
    ),
    StrictRule(
        "test.javascript",
        "deterministic tests for non-DOM logic",
        "Algorithmic, CAD, parsing, and state code needs known-input/known-output tests.",
    ),
    StrictRule(
        "vendor-js",
        "vendor/, lib/, _build/, or *.min.js isolated",
        "Third-party and generated browser assets must not be mixed with owned source.",
    ),
    StrictRule(
        "css",
        "owned CSS with explicit layout/component boundaries",
        "Keep styling reviewable and avoid implicit global sprawl.",
    ),
    StrictRule(
        "css.tokens",
        "CSS custom properties for design constants",
        "Colors, spacing, z-index, radii, and typography values need named tokens.",
    ),
    StrictRule(
        "vendor-css",
        "vendor/, lib/, _build/, or *.min.css isolated",
        "Third-party and generated styles must not be mixed with owned source.",
    ),
    StrictRule(
        "web-components",
        "owned reusable UI primitives",
        "Use wn-* custom elements for repeated stateful UI, not one-off page layout.",
    ),
    StrictRule(
        "hygiene.javascript",
        "js_hygiene or eslint/biome ratchet",
        "Block new large files, complex functions, deep nesting, and whitespace drift.",
    ),
    StrictRule(
        "hygiene.css",
        "css_hygiene ratchet",
        "Block new oversized stylesheets, trailing whitespace, and invalid CSS basics.",
    ),
    StrictRule(
        "html",
        "semantic landmarks and accessible controls",
        "Browser apps need usable structure before visual polish.",
    ),
    StrictRule(
        "browser-smoke",
        "DOM/runtime smoke tests",
        "Exercise browser behavior without relying only on manual clicking.",
    ),
    StrictRule(
        "agent-visual",
        "browser inspection for UI changes",
        "Agents changing UI must inspect rendered output and keep core logic testable.",
    ),
    StrictRule(
        "contracts",
        "document browser data and event contracts",
        "Frontend state, URL, storage, and API payloads need reviewable contracts.",
    ),
    StrictRule(
        "docs.javascript-standard",
        "root or foldered JavaScript standard design doc",
        "Use docs/design/javascript-standard.html, docs/design/standards/javascript.html, "
        "or configure [documentation.standard_docs].javascript.",
    ),
    StrictRule(
        "wasm.testing",
        "test the JS-to-WASM boundary",
        "Browser WASM needs wrapper tests; Wasmer or Wasmtime is optional for core WASM.",
    ),
    StrictRule(
        "commands",
        "install update build test signoff",
        "Projects need a simple cross-platform command surface even when shells differ.",
    ),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
    StrictRule(
        "ci.os",
        "ubuntu, windows, macos",
        "Catch filesystem and browser-runtime drift early.",
    ),
)

JAVASCRIPT_WEB_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "src",
    "tests/rack.toml",
    "dev-std.toml",
)

JAVASCRIPT_WEB_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/javascript-standard.html",
    "docs/contracts/",
    "docs/releases/",
)

PYTHON_JS_RULES = (
    StrictRule("inherits", "javascript-web-app", "Use the no-build JS/CSS browser standard."),
    StrictRule("workflow.python", "uv", "Use one Python environment and lock workflow."),
    StrictRule("lockfile", "commit uv.lock", "Make Python installs reproducible."),
    StrictRule("build-backend", "hatchling", "Use modern pyproject-native builds."),
    StrictRule(
        "test-runner",
        "rack + pytest",
        "Keep backend, API, and browser smoke strata explicit.",
    ),
    StrictRule("typing", "pyright strict or documented ratchet", "Catch Python API drift early."),
    StrictRule("lint.python", "ruff", "Keep Python style and common bug checks automated."),
    StrictRule(
        "server",
        "FastAPI or documented server boundary",
        "Keep browser static serving, JSON APIs, and WebSocket endpoints explicit.",
    ),
    StrictRule(
        "contracts",
        "document Python-to-browser JSON/WebSocket APIs",
        "Frontend state and API payloads need reviewable contracts.",
    ),
    COMPATIBILITY_PRUNING_RULE,
    PUBLIC_PR_HYGIENE_RULE,
)

PYTHON_JS_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

PYTHON_JS_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/javascript-standard.html",
    "docs/contracts/",
    "docs/releases/",
)


def default_python_standard() -> PythonStandard:
    """Return the current strict Python package standard."""
    return PythonStandard(
        name="python-package",
        version=STANDARD_VERSION,
        status="initial",
        rules=(
            StrictRule("workflow", "uv", "Use one environment and lock workflow."),
            StrictRule("lockfile", "commit uv.lock", "Make installs reproducible."),
            StrictRule("build-backend", "hatchling", "Use modern pyproject-native builds."),
            StrictRule("test-runner", "rack", "Keep strata, concerns, and signoff explicit."),
            StrictRule("typing", "pyright strict", "Catch interface drift early."),
            StrictRule("lint", "ruff", "Keep style and common bug checks automated."),
            StrictRule("complexity.production", "<= 8", "Favor simple, reviewable functions."),
            StrictRule("complexity.tests", "<= 10", "Tests may orchestrate more setup."),
            StrictRule("docs.design", "HTML", "Keep docs human-readable and machine-checkable."),
            COMPATIBILITY_PRUNING_RULE,
            PUBLIC_PR_HYGIENE_RULE,
            StrictRule("release", "GitHub Release published", "Allow final review before publish."),
            StrictRule("ci.os", "ubuntu, windows, macos", "Catch platform differences early."),
        ),
        required_files=(
            ".gitattributes",
            ".gitignore",
            "AGENTS.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "README.md",
            "pyproject.toml",
        ),
        required_docs=(
            "docs/setup.html",
            "docs/architecture.html",
            "docs/design/",
            "docs/contracts/",
            "docs/releases/",
        ),
    )


def default_mixed_mode_standard() -> PythonStandard:
    """Return the current Python plus native/WASM mixed-mode standard."""
    return PythonStandard(
        name="python-native-wasm",
        version=STANDARD_VERSION,
        status="initial",
        rules=MIXED_MODE_RULES,
        required_files=MIXED_MODE_REQUIRED_FILES,
        required_docs=MIXED_MODE_REQUIRED_DOCS,
    )


def default_cpp_standard() -> PythonStandard:
    """Return the current C++ library and native executable standard."""
    return PythonStandard(
        name="cpp-library",
        version=STANDARD_VERSION,
        status="initial",
        rules=CPP_RULES,
        required_files=CPP_REQUIRED_FILES,
        required_docs=CPP_REQUIRED_DOCS,
    )


def default_zephyr_standard() -> PythonStandard:
    """Return the current Zephyr firmware standard."""
    return PythonStandard(
        name="zephyr-firmware",
        version=STANDARD_VERSION,
        status="initial",
        rules=ZEPHYR_RULES,
        required_files=ZEPHYR_REQUIRED_FILES,
        required_docs=ZEPHYR_REQUIRED_DOCS,
    )


def default_csharp_standard() -> PythonStandard:
    """Return the current C# application and plugin standard."""
    return PythonStandard(
        name="csharp-app",
        version=STANDARD_VERSION,
        status="initial",
        rules=CSHARP_RULES,
        required_files=CSHARP_REQUIRED_FILES,
        required_docs=CSHARP_REQUIRED_DOCS,
    )


def default_javascript_web_standard() -> PythonStandard:
    """Return the current no-build browser JavaScript and CSS standard."""
    return PythonStandard(
        name="javascript-web-app",
        version=STANDARD_VERSION,
        status="initial",
        rules=JAVASCRIPT_WEB_RULES,
        required_files=JAVASCRIPT_WEB_REQUIRED_FILES,
        required_docs=JAVASCRIPT_WEB_REQUIRED_DOCS,
    )


def default_python_js_standard() -> PythonStandard:
    """Return the current Python plus browser JavaScript app standard."""
    return PythonStandard(
        name="python-js-app",
        version=STANDARD_VERSION,
        status="initial",
        rules=PYTHON_JS_RULES,
        required_files=PYTHON_JS_REQUIRED_FILES,
        required_docs=PYTHON_JS_REQUIRED_DOCS,
    )


def default_standard(profile: ProfileName = "python-package") -> PythonStandard:
    """Return the current standard for a named profile."""
    if profile == "python-package":
        return default_python_standard()
    if profile == "python-native-wasm":
        return default_mixed_mode_standard()
    if profile == "cpp-library":
        return default_cpp_standard()
    if profile == "csharp-app":
        return default_csharp_standard()
    if profile == "javascript-web-app":
        return default_javascript_web_standard()
    if profile == "python-js-app":
        return default_python_js_standard()
    if profile == "zephyr-firmware":
        return default_zephyr_standard()
    raise ValueError(f"unsupported profile: {profile}")


def render_python_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current Python standard as text or JSON."""
    return render_standard("python-package", output_format)


def render_mixed_mode_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current mixed-mode standard as text or JSON."""
    return render_standard("python-native-wasm", output_format)


def render_cpp_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current C++ standard as text or JSON."""
    return render_standard("cpp-library", output_format)


def render_csharp_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current C# standard as text or JSON."""
    return render_standard("csharp-app", output_format)


def render_javascript_web_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current no-build browser JavaScript and CSS standard as text or JSON."""
    return render_standard("javascript-web-app", output_format)


def render_python_js_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current Python plus browser JavaScript standard as text or JSON."""
    return render_standard("python-js-app", output_format)


def render_zephyr_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the current Zephyr firmware standard as text or JSON."""
    return render_standard("zephyr-firmware", output_format)


def render_standard(
    profile: ProfileName = "python-package",
    output_format: Literal["text", "json"] = "text",
) -> str:
    """Render a named standard profile as text or JSON."""
    standard = default_standard(profile)
    if output_format == "json":
        return json.dumps(standard.to_dict(), indent=2, sort_keys=True)

    lines = [
        f"{standard.name} {standard.version} ({standard.status})",
        "",
        "Rules:",
    ]
    for rule in standard.rules:
        lines.append(f"- {rule.key}: {rule.value} ({rule.rationale})")
    lines.append("")
    lines.append("Required files:")
    lines.extend(f"- {path}" for path in standard.required_files)
    lines.append("")
    lines.append("Required docs:")
    lines.extend(f"- {path}" for path in standard.required_docs)
    return "\n".join(lines)
