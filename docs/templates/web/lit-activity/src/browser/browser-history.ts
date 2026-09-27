import type { ActivityEngine, ActivitySnapshot } from "../activity";

interface ReferenceHistoryState {
  readonly owner: "wn-activity-reference";
  readonly depth: number;
  readonly activeKey: string | undefined;
}

export interface HistoryPort {
  readonly state: unknown;
  pushState(state: ReferenceHistoryState): void;
  replaceState(state: ReferenceHistoryState): void;
  back(): void;
  onPopState(listener: (state: unknown) => void): () => void;
}

export class WindowHistoryPort implements HistoryPort {
  get state(): unknown {
    return globalThis.history.state;
  }

  pushState(state: ReferenceHistoryState): void {
    globalThis.history.pushState(state, "");
  }

  replaceState(state: ReferenceHistoryState): void {
    globalThis.history.replaceState(state, "");
  }

  back(): void {
    globalThis.history.back();
  }

  onPopState(listener: (state: unknown) => void): () => void {
    const handler = (event: PopStateEvent) => listener(event.state as unknown);
    globalThis.addEventListener("popstate", handler);
    return () => globalThis.removeEventListener("popstate", handler);
  }
}

export interface BrowserHistoryOptions {
  readonly restoreForward?: (target: {
    readonly depth: number;
    readonly activeKey: string | undefined;
  }) => Promise<boolean>;
  readonly onFailure?: (error: unknown) => void;
}

export class BrowserHistoryCoordinator {
  readonly #engine: ActivityEngine;
  readonly #port: HistoryPort;
  readonly #restoreForward: BrowserHistoryOptions["restoreForward"];
  readonly #onFailure: BrowserHistoryOptions["onFailure"];
  #lastDepth = 0;
  #lastKey: string | undefined;
  #initialized = false;
  #handlingPop = false;
  #ignoreNextPop = false;
  #unsubscribe: (() => void) | undefined;
  #removePopListener: (() => void) | undefined;

  constructor(engine: ActivityEngine, port: HistoryPort, options: BrowserHistoryOptions = {}) {
    this.#engine = engine;
    this.#port = port;
    this.#restoreForward = options.restoreForward;
    this.#onFailure = options.onFailure;
  }

  attach(): void {
    this.#removePopListener = this.#port.onPopState((state) => {
      void this.#onPopState(state).catch((error: unknown) => {
        this.#port.pushState(historyState(this.#engine.snapshot));
        this.#onFailure?.(error);
      });
    });
    this.#unsubscribe = this.#engine.subscribe((snapshot) => this.#onSnapshot(snapshot));
  }

  detach(): void {
    this.#unsubscribe?.();
    this.#unsubscribe = undefined;
    this.#removePopListener?.();
    this.#removePopListener = undefined;
  }

  #onSnapshot(snapshot: ActivitySnapshot): void {
    const depth = snapshot.stack.length;
    if (depth === 0) {
      return;
    }
    const state = historyState(snapshot);
    if (!this.#initialized) {
      this.#initialized = true;
      this.#port.replaceState(state);
    } else if (depth > this.#lastDepth && !this.#handlingPop) {
      this.#port.pushState(state);
    } else if (depth < this.#lastDepth && !this.#handlingPop) {
      this.#ignoreNextPop = true;
      this.#port.back();
    } else if (
      depth === this.#lastDepth &&
      snapshot.activeKey !== this.#lastKey &&
      !this.#handlingPop
    ) {
      this.#port.replaceState(state);
    }
    this.#lastDepth = depth;
    this.#lastKey = snapshot.activeKey;
  }

  async #onPopState(value: unknown): Promise<void> {
    if (this.#ignoreNextPop) {
      this.#ignoreNextPop = false;
      return;
    }
    const target = parseHistoryState(value);
    if (target === undefined || !this.#initialized) {
      return;
    }
    if (target.depth < this.#lastDepth) {
      this.#handlingPop = true;
      try {
        while (this.#engine.snapshot.stack.length > target.depth) {
          const moved = await this.#engine.requestBack();
          if (!moved) {
            this.#port.pushState(historyState(this.#engine.snapshot));
            return;
          }
        }
        if (this.#engine.snapshot.activeKey !== target.activeKey) {
          this.#port.pushState(historyState(this.#engine.snapshot));
        }
      } finally {
        this.#handlingPop = false;
      }
      return;
    }
    if (target.depth > this.#lastDepth || target.activeKey !== this.#lastKey) {
      this.#handlingPop = true;
      try {
        const restored = (await this.#restoreForward?.(target)) ?? false;
        if (!restored) {
          this.#ignoreNextPop = true;
          this.#port.back();
        }
      } finally {
        this.#handlingPop = false;
      }
    }
  }
}

function historyState(snapshot: ActivitySnapshot): ReferenceHistoryState {
  return {
    owner: "wn-activity-reference",
    depth: snapshot.stack.length,
    activeKey: snapshot.activeKey,
  };
}

function parseHistoryState(value: unknown): ReferenceHistoryState | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  if (
    record["owner"] !== "wn-activity-reference" ||
    typeof record["depth"] !== "number" ||
    !Number.isInteger(record["depth"]) ||
    record["depth"] < 1 ||
    (record["activeKey"] !== undefined && typeof record["activeKey"] !== "string")
  ) {
    return undefined;
  }
  return {
    owner: "wn-activity-reference",
    depth: record["depth"],
    activeKey: record["activeKey"] as string | undefined,
  };
}
