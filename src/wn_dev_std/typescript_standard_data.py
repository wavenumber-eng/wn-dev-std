"""TypeScript standard profile data."""

from __future__ import annotations

TYPESCRIPT_WEB_RULE_ITEMS = (
    (
        "workflow",
        "TypeScript-first browser runtime",
        "New owned browser and JavaScript-facing source should start in TypeScript.",
    ),
    (
        "toolchain",
        "package.json plus committed lockfile",
        "Make TypeScript, lint, test, and build tooling reproducible.",
    ),
    (
        "typecheck.typescript",
        "strict tsconfig guardrails",
        "Catch implicit any, nullability, indexed access, optional-property, and module drift.",
    ),
    (
        "source.typescript",
        "owned .ts/.tsx under src/",
        "Keep greenfield implementation source typed by default.",
    ),
    (
        "source.javascript",
        "migration-only allowJs and owned JS",
        "Checked JS is a porting lane, not the greenfield target.",
    ),
    (
        "boundaries",
        "explicit public parameter and return types",
        "Functions, callbacks, events, payloads, and exports need TypeScript-visible contracts.",
    ),
    (
        "runtime-inputs",
        "unknown until validated",
        "External JSON, browser, storage, and message payloads need guard or schema narrowing.",
    ),
    (
        "state-modeling",
        "discriminated unions and literal types",
        "Make invalid modes, actions, and protocol states hard to represent.",
    ),
    (
        "lint.typescript",
        "TypeScript-aware public-boundary lint",
        "Let TS-aware tools enforce source-level annotation and escape-hatch rules.",
    ),
    (
        "tsconfig.extends",
        "local-file inheritance or documented package exception",
        "Audit can resolve local configs but cannot inspect uninstalled package configs.",
    ),
    (
        "skipLibCheck",
        "false or documented exception",
        "Third-party declaration drift should not be hidden silently.",
    ),
    (
        "css.tokens",
        "CSS custom properties when owned CSS exists",
        "Colors, spacing, z-index, radii, and typography values need named tokens.",
    ),
    (
        "commands",
        "build typecheck lint test signoff",
        "Projects need a single signoff surface that invokes typecheck, lint, and tests.",
    ),
    (
        "ci.os",
        "ubuntu, windows, macos",
        "Catch filesystem, package-manager, and browser-runtime drift early.",
    ),
)

TYPESCRIPT_WEB_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "package.json",
    "tsconfig.json",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)

TYPESCRIPT_WEB_REQUIRED_DOCS = (
    "docs/setup.html",
    "docs/architecture.html",
    "docs/design/",
    "docs/design/typescript-standard.html",
    "docs/contracts/",
    "docs/releases/",
)

PYTHON_TS_RULE_ITEMS = (
    ("inherits", "typescript-web-app", "Use the greenfield TypeScript web standard."),
    ("workflow.python", "uv", "Use one Python environment and lock workflow."),
    ("lockfile.python", "commit uv.lock", "Make Python installs reproducible."),
    ("build-backend", "hatchling", "Use modern pyproject-native builds."),
    (
        "test-runner",
        "rack + pytest + package scripts",
        "Keep backend, API, TypeScript, and browser smoke strata explicit.",
    ),
    (
        "typing.python",
        "pyright strict or documented ratchet",
        "Catch Python API drift early.",
    ),
    ("lint.python", "ruff", "Keep Python style and common bug checks automated."),
    (
        "server",
        "FastAPI or documented server boundary",
        "Keep browser static serving, JSON APIs, and WebSocket endpoints explicit.",
    ),
    (
        "contracts",
        "document Python-to-TypeScript JSON/WebSocket APIs",
        "Frontend state and API payloads need reviewable contracts.",
    ),
)

PYTHON_TS_REQUIRED_FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "package.json",
    "pyproject.toml",
    "tsconfig.json",
    "src",
    "tests",
    "tests/rack.toml",
    "dev-std.toml",
)
