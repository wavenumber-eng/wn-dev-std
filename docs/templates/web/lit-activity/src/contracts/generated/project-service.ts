/**
 * @generated-template-seam
 * Source of truth: the owning project's TypeSpec contract package.
 * Regeneration: replace this fixture with the package's generated TypeScript projection.
 * Release policy: generated projections are reviewed, freshness-checked, and committed or pinned.
 *
 * This compile-ready fixture demonstrates the dependency boundary only. It is
 * not a substitute for adopting the TypeSpec contract template before a real
 * backend is connected.
 */

export interface SaveProjectRequest {
  readonly name: string;
}

export interface SavedProject {
  readonly id: string;
  readonly name: string;
}
