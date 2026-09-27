import type { ActivityEngine } from "../activity";

export class BrowserLifecycleCoordinator {
  readonly #engine: ActivityEngine;
  readonly #handler: (event: BeforeUnloadEvent) => void;

  constructor(engine: ActivityEngine) {
    this.#engine = engine;
    this.#handler = (event) => {
      if (!this.#engine.canExitCached()) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
  }

  attach(): void {
    globalThis.addEventListener("beforeunload", this.#handler);
  }

  detach(): void {
    globalThis.removeEventListener("beforeunload", this.#handler);
  }
}
