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

## Standards Changes

Standards changes should update all affected surfaces:

- implementation
- tests
- `docs/design/*.html`
- `docs/contracts/*`
- `README.md` when user-facing behavior changes
- `CHANGELOG.md`
- `docs/releases/<YYYY-MM-DD>.md` for release-facing changes

## Exceptions

Strict rules are the default. Exceptions must include rationale, scope, owner or
review context, and a clear reason the rule cannot currently be met.
