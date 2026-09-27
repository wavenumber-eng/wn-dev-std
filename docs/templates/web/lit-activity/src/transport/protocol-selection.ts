export type ClientProtocol = "http" | "sse" | "websocket" | "polling";

export interface InteractionNeeds {
  readonly finite: boolean;
  readonly direction: "request-response" | "server-to-client" | "bidirectional";
  readonly latency: "ordinary" | "low";
  readonly updateFrequency: "infrequent" | "continuous";
}

export function selectProtocol(needs: InteractionNeeds): ClientProtocol {
  if (needs.finite) {
    return "http";
  }
  if (needs.direction === "bidirectional" || needs.latency === "low") {
    return "websocket";
  }
  if (needs.direction === "server-to-client" && needs.updateFrequency === "continuous") {
    return "sse";
  }
  return "polling";
}
