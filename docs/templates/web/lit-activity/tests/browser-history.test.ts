import { describe, expect, it, vi } from "vitest";
import { ActivityEngine, ActivityRegistry, defineActivity, type LeaveState } from "../src/activity";
import { BrowserHistoryCoordinator, type HistoryPort } from "../src/browser/browser-history";

class FakeHistory implements HistoryPort {
  state: unknown;
  readonly pushed: unknown[] = [];
  readonly replaced: unknown[] = [];
  backCount = 0;
  #listener: ((state: unknown) => void) | undefined;

  pushState(state: unknown): void {
    this.state = state;
    this.pushed.push(state);
  }

  replaceState(state: unknown): void {
    this.state = state;
    this.replaced.push(state);
  }

  back(): void {
    this.backCount += 1;
  }

  onPopState(listener: (state: unknown) => void): () => void {
    this.#listener = listener;
    return () => {
      this.#listener = undefined;
    };
  }

  pop(state: unknown): void {
    this.#listener?.(state);
  }
}

describe("BrowserHistoryCoordinator", () => {
  it("maps browser back to activity back without putting history in the kernel", async () => {
    const { engine, child } = await engineWithRoot();
    const history = new FakeHistory();
    const coordinator = new BrowserHistoryCoordinator(engine, history);
    coordinator.attach();
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    expect(history.pushed).toHaveLength(1);

    history.pop({ owner: "wn-activity-reference", depth: 1, activeKey: "root" });
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("root"));
    await expect(outcome).resolves.toEqual({ status: "cancelled" });
    coordinator.detach();
  });

  it("restores history when a dirty activity rejects browser back", async () => {
    const { engine, child } = await engineWithRoot({ status: "dirty", reason: "Unsaved" });
    const history = new FakeHistory();
    const coordinator = new BrowserHistoryCoordinator(engine, history);
    coordinator.attach();
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));

    history.pop({ owner: "wn-activity-reference", depth: 1, activeKey: "root" });
    await vi.waitFor(() => expect(history.pushed).toHaveLength(2));
    expect(engine.snapshot.activeKey).toBe("child");
    await engine.cancel();
    await outcome;
    coordinator.detach();
  });

  it("unwinds every activity frame in a multi-entry browser jump", async () => {
    const registry = new ActivityRegistry();
    const root = defineActivity<void, never>({ key: "root", create: () => activity() });
    const child = defineActivity<void, void>({ key: "child", create: () => activity() });
    const grandchild = defineActivity<void, void>({ key: "grandchild", create: () => activity() });
    registry.register(root);
    registry.register(child);
    registry.register(grandchild);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const history = new FakeHistory();
    const coordinator = new BrowserHistoryCoordinator(engine, history);
    coordinator.attach();
    const childOutcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    const grandchildOutcome = engine.push(grandchild, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("grandchild"));

    history.pop({ owner: "wn-activity-reference", depth: 1, activeKey: "root" });

    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("root"));
    await expect(grandchildOutcome).resolves.toEqual({ status: "cancelled" });
    await expect(childOutcome).resolves.toEqual({ status: "cancelled" });
    coordinator.detach();
  });

  it("restores authoritative history and reports a back-transition failure", async () => {
    let failLeave = false;
    const registry = new ActivityRegistry();
    const root = defineActivity<void, never>({ key: "root", create: () => activity() });
    const child = defineActivity<void, void>({
      key: "child",
      create: () => ({
        initialize: () => undefined,
        leaveState: () => {
          if (failLeave) {
            throw new Error("leave failed");
          }
          return { status: "clean" as const };
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const history = new FakeHistory();
    const failures: unknown[] = [];
    const coordinator = new BrowserHistoryCoordinator(engine, history, {
      onFailure: (error) => failures.push(error),
    });
    coordinator.attach();
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    failLeave = true;

    history.pop({ owner: "wn-activity-reference", depth: 1, activeKey: "root" });
    await vi.waitFor(() => expect(failures).toHaveLength(1));
    expect(history.pushed.at(-1)).toEqual(
      expect.objectContaining({ depth: 2, activeKey: "child" }),
    );

    failLeave = false;
    history.pop({ owner: "wn-activity-reference", depth: 1, activeKey: "root" });
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("root"));
    await expect(outcome).resolves.toEqual({ status: "cancelled" });
    coordinator.detach();
  });

  it("restores browser forward without duplicating the browser history entry", async () => {
    const { engine, child } = await engineWithRoot();
    const history = new FakeHistory();
    let childOutcome: ReturnType<typeof engine.push> | undefined;
    const coordinator = new BrowserHistoryCoordinator(engine, history, {
      restoreForward: async (target) => {
        if (target.depth !== 2 || target.activeKey !== "child") {
          return false;
        }
        childOutcome = engine.push(child, undefined);
        await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
        return true;
      },
    });
    coordinator.attach();

    history.pop({ owner: "wn-activity-reference", depth: 2, activeKey: "child" });

    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    expect(history.pushed).toEqual([]);
    await engine.cancel();
    await expect(childOutcome).resolves.toEqual({ status: "cancelled" });
    coordinator.detach();
  });
});

async function engineWithRoot(leaveState?: LeaveState) {
  const registry = new ActivityRegistry();
  const root = defineActivity<void, never>({ key: "root", create: () => activity() });
  const child = defineActivity<void, void>({ key: "child", create: () => activity(leaveState) });
  registry.register(root);
  registry.register(child);
  const engine = new ActivityEngine(registry);
  await engine.start(root, undefined);
  return { engine, child };
}

function activity(leaveState?: LeaveState) {
  return {
    initialize: () => undefined,
    leaveState: () => leaveState ?? { status: "clean" as const },
    render: () => undefined,
  };
}
