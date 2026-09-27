import type { JsonRequest, JsonTransport } from "./transport";

export class DemoTransport implements JsonTransport {
  async request(request: JsonRequest): Promise<unknown> {
    if (request.method !== "POST" || request.path !== "/projects") {
      throw new Error("The demo transport only implements POST /projects.");
    }
    await Promise.resolve();
    if (request.signal?.aborted === true) {
      throw request.signal.reason;
    }
    const body = request.body as { readonly name?: unknown } | undefined;
    const name = typeof body?.name === "string" ? body.name : "Untitled";
    return { id: crypto.randomUUID(), name };
  }
}
