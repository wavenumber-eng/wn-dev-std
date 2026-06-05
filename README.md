# wn-dev-std

`wn-dev-std` is Wavenumber's development standards reference package. It gives
new projects a strict Python baseline for packaging, tests, documentation,
contracts, release hygiene, and agent-readable repo structure.

The repository is also a working example. It installs as a Python package and
exposes a small CLI whose code, docs, contracts, tests, and release metadata are
kept in sync by Rack signoff.

## Status

Initial Python support. This repository is a model/reference package and is not
published to PyPI. C, C++, C#, JavaScript, Rust, and Zephyr profiles will reuse
the same base rules as they are added.

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
- HTML design docs and JSON contracts
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

## Documentation

- [Setup](docs/setup.html)
- [Architecture](docs/architecture.html)
- [CLI Design](docs/design/cli.html)
- [Python Standard Design](docs/design/python-standard.html)
- [C++ Standard](docs/design/cpp-standard.html)
- [Mixed Mode Standard](docs/design/mixed-mode.html)
- [Release Notes](docs/releases/2026-06-04.md)

## License

MIT. See [LICENSE](LICENSE).
