# wn-dev-std

`wn-dev-std` is Wavenumber's development standards reference package. It gives
new projects a strict Python baseline for packaging, tests, documentation,
contracts, release hygiene, and agent-readable repo structure.

The repository is also a working example. It installs as a Python package and
exposes a small CLI whose code, docs, contracts, tests, and release metadata are
kept in sync by Rack signoff.

## Status

Initial Python support. This repository is a model/reference package and is not
published to PyPI. C++, C#, and JavaScript profiles are present; C, Rust, and
Zephyr profiles will reuse the same base rules as they are added.

## Install

For normal tool use:

```bash
uv tool install git+https://github.com/wavenumber-eng/wn-dev-std.git
wn-dev-std --version
```

For one-shot use:

```bash
uvx --from git+https://github.com/wavenumber-eng/wn-dev-std.git wn-dev-std --help
```

For local development:

```bash
uv sync --all-extras
uv run wn-dev-std check .
uv run rack run --all
```

## Use Cases

- Start a new strict Python package with known Wavenumber defaults.
- Check whether a repository has required public project hygiene files.
- Provide agents with a concrete example of Rack, signoff, docs, contracts, and
  release metadata working together.
- Serve as the base vocabulary for future C/C++/C#/JS/Rust/Zephyr standards.

## CLI Examples

Show version and major internal dependency versions:

```bash
wn-dev-std version
wn-dev-std --version
```

Print the current Python standard summary:

```bash
wn-dev-std standard
wn-dev-std standard --format json
wn-dev-std standard --profile cpp-library
wn-dev-std standard --profile python-native-wasm
wn-dev-std standard --profile csharp-app
wn-dev-std standard --profile javascript-web-app
wn-dev-std standard --profile python-js-app
```

Run the basic conformance checks against the current repo:

```bash
wn-dev-std check .
wn-dev-std check . --format json
```

## Python Baseline

Pure Python packages use:

- `uv` for environment, locking, and tool workflows
- committed `uv.lock`
- `pyproject.toml` with Hatchling
- Rack for test orchestration
- Ruff and Pyright
- strict typing
- HTML design docs with explicit `data-doc-status` markers and JSON contracts
- date-based releases
- GitHub Release published events for release validation
- optional PyPI trusted publishing for projects that choose that distribution
- CI on Ubuntu, Windows, and macOS

## C++ Baseline

The first native profile is `cpp-library`, modeled on the Geometer and
`altium_monkey_cpp` C++ conventions.

C++ projects use:

- CMake, CTest, and `CMakePresets.json`
- Ninja as the default generator
- `CMAKE_EXPORT_COMPILE_COMMANDS=ON`
- committed `.clang-format` and `.clang-tidy`
- clang-format style based on LLVM, Allman braces, 4-space indentation, 100
  columns, left pointer alignment, sorted includes, and preserved include
  blocks
- fixed-width integer spellings in owned C/C++ code
  (`std::int32_t`, `std::uint32_t`, `std::int64_t`, `std::uint64_t`) instead
  of `short`, `long`, or `long long`
- compiler warnings on owned code, with release-facing CI treating warnings as
  errors where feasible
- Rack strata for native foundation, algorithms, CLI/API integration, and L99
  release signoff

## Mixed-Mode Baseline

The first mixed-mode profile is `python-native-wasm`, modeled on Geometer-style
packages that combine Python wrappers, CMake/C++ native builds, platform wheels,
and WASM runtime artifacts.

Mixed-mode packages add:

- CMake and CTest for native builds
- grouped committed runtime artifacts under `dist/native/<platform>/` and
  `dist/wasm/<target>/`
- documented custom wheel hooks when platform wheels bundle executables
- native validation before package validation
- installed-wheel smoke tests that prove the bundled executable is used
- separate CI lanes for Python, native, platform wheels, WASM, and release
  validation

## JavaScript Web Baseline

The first browser profile is `javascript-web-app`, with `python-js-app` for
FastAPI-style packages that serve the browser runtime.

Web apps use:

- no-build HTML, CSS, and browser JavaScript by default
- optional Node tooling only when dependencies, bundling, or browser test
  infrastructure justify it
- checked JavaScript through `jsconfig.json`, `tsconfig.json`, JSDoc, or
  per-file `// @ts-check`
- deterministic `node:test` coverage for algorithmic JavaScript, parsers, CAD
  state, and data transforms
- CSS custom properties for design constants before hard-coded color, spacing,
  z-index, radius, or typography values spread through files
- owned `wn-*` Web Components for repeated stateful UI primitives such as
  dialogs, toast regions, panels, toolbars, and property rows
- JS-to-WASM wrapper tests for browser-facing WebAssembly, with Wasmer or
  Wasmtime optional for core WASM checks when useful
- standard command verbs: `install`, `update`, `build`, `test`, and `signoff`
- explicit ES module or manifest-ordered IIFE ownership
- isolated `vendor/`, `lib/`, `_build/`, `node_modules/`, and minified assets
- JS and CSS hygiene ratchets for file size, complexity, nesting, generated
  asset placement, and whitespace
- Rack signoff for browser smoke tests and Python-to-browser API contracts

## Compatibility Pruning

Projects that are retiring old names, environment variables, setup shims, or
compatibility aliases can opt into a repository scan in `wn-dev-std.toml`:

```toml
[compatibility_pruning]
root = ".."
forbidden_patterns = [
  "\\bWN_LIBZ_ROOT\\b",
  "\\bwn_pcb\\b",
]
excluded_parts = ["test_cases", "fixtures"]
```

The check is intentionally configurable because legacy cleanup is project
specific. It should be part of L99 signoff when a repo has known old surfaces to
prune, with generated files and captured fixtures excluded explicitly.

## Design Doc Status

HTML design docs under `docs/design` must declare `data-doc-status` with one of
`draft`, `proposal`, `accepted`, or `superseded`. The check fails unmarked or
invalid design docs and reports draft/proposal pages for release review.

## Documentation

- [Setup](docs/setup.html)
- [Architecture](docs/architecture.html)
- [CLI Design](docs/design/cli.html)
- [Documentation Standard](docs/design/documentation-standard.html)
- [Python Standard Design](docs/design/python-standard.html)
- [C++ Standard](docs/design/cpp-standard.html)
- [Mixed Mode Standard](docs/design/mixed-mode.html)
- [JavaScript Web App Standard](docs/design/javascript-standard.html)
- [Release Notes](docs/releases/2026-06-10.md)

## License

MIT. See [LICENSE](LICENSE).
