# TypeSpec Contract Package

This is a private, copy-owned reference for a contract authority that can be
used without a web application. Rename the package, namespace, schema IDs, and
sample domain after copying it.

Create a version-matched copy with
`dev-std template copy typespec-contract <destination>`.

## Start here

1. Run `npm ci` and `uv sync`.
2. Run `npm run signoff` to compile TypeSpec, generate JSON Schema, OpenAPI, and
   TypeScript declarations, check freshness, and run Node and Python
   conformance consumers.
3. Edit the authoritative `.tsp` sources under `contracts/`, rooted at
   `contracts/main.tsp`; never edit files under `generated/`.
4. Regenerate with `npm run generate` and commit reviewed projections.
5. Update `dev-std.toml` when projections or consumer evidence change.

## Authority

The TypeSpec sources under `contracts/`, rooted at `contracts/main.tsp`, own
structural contract data. Generated files are projections and must not be
hand-edited. Handwritten runtimes own behavior, effects, transactions, and
non-structural invariants.

The example deliberately proves a non-web path: a TypeScript library consumer
and an independent Python JSON Schema consumer use the same conformance
fixtures. Rust or Python source generators can be added through the documented
extension seam when their emitters are independently pinned and tested.

See:

- `docs/architecture.md` for ownership and dependency direction;
- `docs/generated-files.md` for regeneration and release policy;
- `docs/adding-a-projection.md` for emitter and consumer evidence;
- `docs/conformance.md` for shared accepted/rejected vectors.
