import type { SavedProject, SaveProjectRequest } from "../../contracts";
import type { JsonTransport } from "../../transport";

export type { SavedProject } from "../../contracts";

export interface ProjectApi {
  saveDraft(name: string, signal: AbortSignal): Promise<SavedProject>;
}

export class ProjectClient implements ProjectApi {
  readonly #transport: JsonTransport;

  constructor(transport: JsonTransport) {
    this.#transport = transport;
  }

  async saveDraft(name: string, signal: AbortSignal): Promise<SavedProject> {
    const request: SaveProjectRequest = { name };
    const value = await this.#transport.request({
      method: "POST",
      path: "/projects",
      body: request,
      signal,
    });
    if (!isRecord(value) || typeof value["id"] !== "string" || typeof value["name"] !== "string") {
      throw new Error("POST /projects returned an invalid contract.");
    }
    return { id: value["id"], name: value["name"] };
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
