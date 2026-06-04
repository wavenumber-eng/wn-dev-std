# Agent Guide

This repository is the reference implementation for Wavenumber development
standards. Treat it as both production code and an executable example for new
projects.

## Setup

Use `uv` for all Python workflows:

```bash
uv sync --all-extras
```

Do not hand-edit `uv.lock`. Update it with `uv lock` and verify it with
`uv lock --check`.

## Test And Signoff

Run the full local signoff before release-facing changes:

```bash
uv run rack run --all
uv run python -m build
uv run twine check dist/*
```

Fast development checks can run individual Rack strata:

```bash
uv run rack run L0_foundation
uv run rack run L99_signoff
```

## Architecture Boundaries

- `src/wn_dev_std/cli/main.py` is the thin CLI entry point.
- Each public command lives in its own file under
  `src/wn_dev_std/cli/commands/`.
- Reusable standard data and checks live outside the CLI package.
- `docs/design/*.html` and `docs/contracts/*` are source-of-truth public
  contracts, not generated scratch output.

## Release Rules

- `main` should represent the latest released/tagged source.
- Public changes should merge through PRs with required CI.
- GitHub Release publication triggers release validation for this model repo.
- Do not publish this repository to PyPI.
- Date-based versions are standard, for example `2026.6.4`.
- Same-day follow-up releases append a fourth segment, for example
  `2026.6.4.1`.
- `CHANGELOG.md` and `docs/releases/<YYYY-MM-DD>.md` must mention the current
  version.

## Generated Files

Generated files must document their source of truth, regeneration command, and
release inclusion policy. Do not commit local result directories such as
`rack_results/`, `dist/`, or `.venv/`.

## Exceptions

The default standard is strict. Any exception must have documented rationale,
scope, and review trigger. Legacy projects may use baselines or ratchets, but
new code must meet the current standard.
