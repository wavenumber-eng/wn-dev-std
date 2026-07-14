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
- HTML design docs must declare `data-doc-status` as `draft`, `proposal`,
  `accepted`, or `superseded`; release signoff must review any draft/proposal
  docs before treating them as contract evidence.
- C++ profile templates live under `docs/templates/cpp/`; keep them aligned
  with `docs/design/cpp-standard.html` and the checker policy.

## Release Rules

- `main` should represent the latest released/tagged source.
- Public changes should merge through PRs with required CI.
- Public PRs should squash merge into `main`; avoid merge commits or preserved
  branch history that creates non-linear public history unless a documented
  release exception requires it.
- GitHub Release publication triggers release validation for this model repo.
- Publish released `wn-dev-std` versions to PyPI so downstream projects can pin
  a reviewed governance tool version in CI.
- Date-based versions are standard, for example `2026.6.4`.
- Same-day follow-up releases append a fourth segment, for example
  `2026.6.4.1`.
- `CHANGELOG.md` and `docs/releases/<YYYY-MM-DD>.md` must mention the current
  version.

## Generated Files

Generated files must document their source of truth, regeneration command, and
release inclusion policy. Do not commit local result directories such as
`rack_results/`, `dist/`, or `.venv/`.

Mixed-mode projects are the exception to the blanket `dist/` rule. They may
commit grouped runtime artifacts such as `dist/native/<platform>/` and
`dist/wasm/<target>/` when the artifact policy is documented and covered by
release signoff. Root-level `dist/` files should remain limited to manifests or
artifact documentation.

C++ projects use Ninja as the default CMake generator, commit `.clang-format`
and `.clang-tidy`, and enable `CMAKE_EXPORT_COMPILE_COMMANDS=ON` in presets.

## Exceptions

The default standard is strict. Any exception must have documented rationale,
scope, and review trigger. Legacy projects may use baselines or ratchets, but
new code must meet the current standard.
