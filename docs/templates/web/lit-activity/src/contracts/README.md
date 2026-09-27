# Contract Projection Boundary

`generated/project-service.ts` is a compile-ready fixture that makes the
dependency direction visible. Before connecting a real backend, replace that
fixture with exports from the project's TypeSpec-owned contract package. Do
not grow a parallel set of handwritten wire interfaces here.

The contract package should be created from the independent
`typespec-contract` template, publish or expose a pinned TypeScript projection,
and verify generation freshness in signoff. This web template then consumes
that projection only through `src/contracts/index.ts`, keeping generated code
replaceable and feature imports stable.
