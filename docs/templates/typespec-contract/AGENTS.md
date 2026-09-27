# Contract Template Agent Guide

- Treat the `.tsp` sources under `contracts/`, rooted at
  `contracts/main.tsp`, as structural authority.
- Never hand-edit `generated/`.
- Pin compiler, library, emitter, and code-generator versions exactly.
- Generate only projections with a real consumer.
- Add accepted and rejected conformance vectors for compatibility changes.
- Run `npm run generate` after TypeSpec changes and `npm run signoff` before review.
- Keep behavioral domain code outside generated projections.
