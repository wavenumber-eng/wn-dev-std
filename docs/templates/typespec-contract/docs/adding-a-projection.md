# Adding A Projection

1. Choose an independently installable generator and pin its exact version.
2. Add its package to `emitter_packages` in `dev-std.toml`.
3. Add deterministic generation to `npm run generate`.
4. Declare the projection output, support level, and whether it is required.
5. Add a real compiling or validating consumer.
6. Reuse the shared accepted and rejected conformance vectors.
7. Add the output to the generated manifest and release policy.
8. Run `npm run signoff`.

Use `supported` only when the generator and consumer are exercised in signoff.
Use `experimental` while behavior may change. Use `extension` to document a
future seam without claiming an implemented projection.
