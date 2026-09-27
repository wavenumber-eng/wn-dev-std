import type { paths } from "../generated/typescript/api.js";

export type CatalogSnapshotResponse =
  paths["/api/catalog/v1/snapshot"]["get"]["responses"]["200"]["content"]["application/json"];

export function summarize(snapshot: CatalogSnapshotResponse): string {
  return `${snapshot.revision}:${snapshot.items.length}`;
}
