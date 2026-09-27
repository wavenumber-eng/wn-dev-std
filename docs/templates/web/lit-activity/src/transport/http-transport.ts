import { type JsonRequest, type JsonTransport, TransportError } from "./transport";

export interface HttpTransportOptions {
  readonly baseUrl: URL;
  readonly fetcher?: typeof fetch;
  readonly headers?: Readonly<Record<string, string>>;
}

export class HttpTransport implements JsonTransport {
  readonly #baseUrl: URL;
  readonly #fetcher: typeof fetch;
  readonly #headers: Readonly<Record<string, string>>;

  constructor(options: HttpTransportOptions) {
    this.#baseUrl = options.baseUrl;
    this.#fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
    this.#headers = options.headers ?? {};
  }

  async request(request: JsonRequest): Promise<unknown> {
    const init: RequestInit = {
      method: request.method,
      headers: { "content-type": "application/json", ...this.#headers },
      credentials: "same-origin",
    };
    if (request.body !== undefined) {
      init.body = JSON.stringify(request.body);
    }
    if (request.signal !== undefined) {
      init.signal = request.signal;
    }
    const url = this.#requestUrl(request.path);
    let response: Response;
    try {
      response = await this.#fetcher(url, init);
    } catch (error: unknown) {
      if (request.signal?.aborted === true || isAbortError(error)) {
        throw new TransportError("Backend request was cancelled.", "cancelled", undefined, error);
      }
      throw new TransportError(
        "Backend request could not reach the service.",
        "network",
        undefined,
        error,
      );
    }
    const detail = await responseDetail(response);
    if (!response.ok) {
      throw new TransportError("Backend request failed.", "http", response.status, detail);
    }
    return detail;
  }

  #requestUrl(path: string): URL {
    if (/^[a-z][a-z\d+.-]*:/i.test(path) || path.startsWith("//")) {
      throw new TransportError(
        "Backend request paths must be relative to the configured service origin.",
        "policy",
        undefined,
        path,
      );
    }
    let url: URL;
    try {
      url = new URL(path, this.#baseUrl);
    } catch (error: unknown) {
      throw new TransportError("Backend request path is invalid.", "policy", undefined, error);
    }
    if (url.origin !== this.#baseUrl.origin) {
      throw new TransportError(
        "Backend request path escaped the configured service origin.",
        "policy",
        undefined,
        path,
      );
    }
    return url;
  }
}

async function responseDetail(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }
  const text = await response.text();
  if (text.trim() === "") {
    return undefined;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch (error: unknown) {
    if (!response.ok) {
      return text;
    }
    throw new TransportError("Backend returned invalid JSON.", "protocol", response.status, error);
  }
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
