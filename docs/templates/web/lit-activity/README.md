# Lit Activity Application

This private, copy-owned reference demonstrates Wavenumber's preferred
workflow-oriented web architecture:

- a rendering-independent activity kernel;
- clean composition-root registration;
- typed input, result, cancellation, and root switching;
- activity-local state with explicit promotion;
- centralized backend transports and feature clients;
- Lit views hosted by a shell with named profiles;
- swappable design tokens and approved Wavenumber backgrounds.

The running reference contains a workspace root, an editor child, a nested
picker, a root-switch component gallery, four shell profiles, browser-history
and shutdown adapters, a semantic backend client, and protocol-selection
examples. Each piece is intentionally small enough to copy and change.

## Start here

1. Run `npm ci`.
2. Run `npm run dev` and open the printed local URL.
3. Read `docs/architecture.md` and `docs/activity-model.md`.
4. Follow `docs/creating-an-activity.md` for the first feature.
5. Run `npm run signoff` before review.
6. Run `dev-std audit . --scope application` with the version declared in
   `dev-std.toml`.

The template is a starting point, not a shared runtime framework. Copy it,
rename the package and application, then own the result.

## Guide map

- `docs/activity-model.md`: stack, results, lifecycle, errors, and illegal operations;
- `docs/state-management.md`: how to choose the narrowest state owner;
- `docs/creating-an-activity.md`: the repeatable feature recipe;
- `docs/host-lifecycle.md`: browser history, forward restoration, and shutdown;
- `docs/backend-integration.md`: transport and semantic-client boundaries;
- `docs/shell-profiles.md`: shell-owned presentation policy;
- `docs/theming.md`: replaceable primitives, semantic roles, and variants;
- `docs/copying.md`: turning this reference into a new project.
