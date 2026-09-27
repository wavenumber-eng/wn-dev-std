import { describe, expect, it } from "vitest";
import { ProjectClient } from "../src/features/projects";
import type { JsonRequest, JsonTransport } from "../src/transport";

describe("ProjectClient", () => {
  it("keeps HTTP-shaped mechanics behind a semantic feature operation", async () => {
    const requests: JsonRequest[] = [];
    const transport: JsonTransport = {
      request: (request) => {
        requests.push(request);
        return Promise.resolve({ id: "project-1", name: "Control board" });
      },
    };
    const client = new ProjectClient(transport);

    await expect(client.saveDraft("Control board", new AbortController().signal)).resolves.toEqual({
      id: "project-1",
      name: "Control board",
    });
    expect(requests).toHaveLength(1);
    expect(requests[0]).toMatchObject({ method: "POST", path: "/projects" });
  });

  it("rejects invalid response contracts", async () => {
    const transport: JsonTransport = { request: () => Promise.resolve({ id: 7 }) };
    const client = new ProjectClient(transport);

    await expect(client.saveDraft("Broken", new AbortController().signal)).rejects.toThrow(
      "invalid contract",
    );
  });
});
