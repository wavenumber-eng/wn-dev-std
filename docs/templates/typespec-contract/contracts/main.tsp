import "@typespec/http";
import "./models.tsp";

using TypeSpec.Http;

@service(#{ title: "Example catalog API" })
@route("/api/catalog/v1")
namespace Example.Catalog.Http.V1 {
  @route("/snapshot")
  @get
  op readSnapshot(): Contracts.V1.CatalogSnapshot;

  @route("/commands")
  @post
  op applyCommand(
    @body command: Contracts.V1.CatalogCommand,
  ): Contracts.V1.CatalogSnapshot;
}
