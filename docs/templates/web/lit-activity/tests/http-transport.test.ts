import { describe, expect, it, vi } from "vitest";
import { HttpTransport, type TransportError } from "../src/transport";

describe("HttpTransport", () => {
  it("refuses absolute paths before forwarding configured headers", async () => {
    const fetcher = vi.fn<typeof fetch>();
    const transport = new HttpTransport({
      baseUrl: new URL("http://127.0.0.1:4170/api/"),
      fetcher,
      headers: { authorization: "Bearer local-capability" },
    });

    await expect(
      transport.request({ method: "GET", path: "https://example.invalid/collect" }),
    ).rejects.toMatchObject({ kind: "policy" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("preserves text error details in a normalized HTTP failure", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response("service unavailable", {
        status: 503,
        headers: { "content-type": "text/plain" },
      }),
    );
    const transport = new HttpTransport({ baseUrl: new URL("https://service.test/"), fetcher });

    await expect(transport.request({ method: "GET", path: "/status" })).rejects.toMatchObject({
      name: "TransportError",
      kind: "http",
      status: 503,
      detail: "service unavailable",
    });
  });

  it("normalizes network and successful invalid-JSON failures", async () => {
    const network = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("connection refused"));
    const networkTransport = new HttpTransport({
      baseUrl: new URL("https://service.test/"),
      fetcher: network,
    });
    await expect(
      networkTransport.request({ method: "GET", path: "/status" }),
    ).rejects.toMatchObject({ kind: "network" });

    const invalid = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("not-json", { status: 200 }));
    const invalidTransport = new HttpTransport({
      baseUrl: new URL("https://service.test/"),
      fetcher: invalid,
    });
    await expect(invalidTransport.request({ method: "GET", path: "/status" })).rejects.toEqual(
      expect.objectContaining<Partial<TransportError>>({ kind: "protocol", status: 200 }),
    );
  });

  it("accepts empty success responses", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }));
    const transport = new HttpTransport({ baseUrl: new URL("https://service.test/"), fetcher });

    await expect(
      transport.request({ method: "DELETE", path: "/projects/42" }),
    ).resolves.toBeUndefined();
  });
});
