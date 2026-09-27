export interface JsonRequest {
  readonly method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly path: string;
  readonly body?: unknown;
  readonly signal?: AbortSignal;
}

export interface JsonTransport {
  request(request: JsonRequest): Promise<unknown>;
}

export type TransportErrorKind = "cancelled" | "http" | "network" | "policy" | "protocol";

export class TransportError extends Error {
  readonly kind: TransportErrorKind;
  readonly status: number | undefined;
  readonly detail: unknown;

  constructor(
    message: string,
    kind: TransportErrorKind,
    status: number | undefined,
    detail: unknown,
  ) {
    super(message);
    this.name = "TransportError";
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}
