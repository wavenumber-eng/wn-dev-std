# Contributing

Thank you for contributing to `wn-dev-std`.

## Development Workflow

1. Create a branch from `main`.
2. Make focused changes.
3. Run signoff:

   ```bash
   uv sync --all-extras
   uv run rack run --all
   uv run python -m build
   uv run twine check dist/*
   ```

4. Open a pull request.

## PR Merge Policy

Public changes should merge through reviewed pull requests with required CI.
Use squash merge into `main` so public history stays linear and focused. Do not
use merge commits or accumulated local branch history unless a documented
project-specific release exception requires that history to be preserved.

## Standards Changes

Standards changes should update all affected surfaces:

- implementation
- tests
- `docs/design/*.html`
- explicit `data-doc-status` markers for HTML design docs
- `docs/contracts/*`
- `README.md` when user-facing behavior changes
- `CHANGELOG.md`
- `docs/releases/<YYYY-MM-DD>.md` for release-facing changes

## Exceptions

Strict rules are the default. Exceptions must include rationale, scope, owner or
review context, and a clear reason the rule cannot currently be met.
