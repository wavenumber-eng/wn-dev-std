import { describe, expect, it } from "vitest";
import { selectProtocol } from "../src/transport";

describe("selectProtocol", () => {
  it("uses HTTP for finite commands and queries", () => {
    expect(
      selectProtocol({
        finite: true,
        direction: "request-response",
        latency: "ordinary",
        updateFrequency: "infrequent",
      }),
    ).toBe("http");
  });

  it("distinguishes server streams and polling", () => {
    expect(
      selectProtocol({
        finite: false,
        direction: "server-to-client",
        latency: "ordinary",
        updateFrequency: "continuous",
      }),
    ).toBe("sse");
    expect(
      selectProtocol({
        finite: false,
        direction: "server-to-client",
        latency: "ordinary",
        updateFrequency: "infrequent",
      }),
    ).toBe("polling");
  });

  it.each([
    ["bidirectional ordinary-latency sessions", "bidirectional", "ordinary"],
    ["low-latency server streams", "server-to-client", "low"],
  ] as const)("uses WebSocket for %s", (_case, direction, latency) => {
    expect(
      selectProtocol({
        finite: false,
        direction,
        latency,
        updateFrequency: "continuous",
      }),
    ).toBe("websocket");
  });
});
