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

## Documentation

- [Setup](docs/setup.html)
- [Architecture](docs/architecture.html)
- [CLI Design](docs/design/cli.html)
- [Python Standard Design](docs/design/python-standard.html)
- [Release Notes](docs/releases/2026-06-04.md)

## License

MIT. See [LICENSE](LICENSE).
