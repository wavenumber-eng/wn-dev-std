import "@typespec/json-schema";

using TypeSpec.JsonSchema;

namespace Example.Catalog.Contracts.V1 {
  @minLength(1)
  @maxLength(80)
  scalar CatalogItemId extends string;

  model CatalogItem {
    id: CatalogItemId;
    name: string;
    description?: string;
  }

  @jsonSchema
  @id("https://schemas.example.invalid/catalog/snapshot/v1.json")
  @extension("title", "Catalog snapshot v1")
  model CatalogSnapshot {
    type: "catalog.snapshot";
    version: "v1";
    revision: safeint;
    items: CatalogItem[];
  }

  @jsonSchema
  model UpsertCatalogItem {
    kind: "upsert";
    item: CatalogItem;
  }

  @jsonSchema
  model RemoveCatalogItem {
    kind: "remove";
    item_id: CatalogItemId;
  }

  @jsonSchema
  union CatalogCommand {
    upsert: UpsertCatalogItem,
    remove: RemoveCatalogItem,
  }
}
