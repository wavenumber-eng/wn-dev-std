// @vitest-environment node

import { describe, expect, it, vi } from "vitest";
import {
  type Activity,
  type ActivityContext,
  ActivityEngine,
  ActivityRegistry,
  defineActivity,
  type LeaveState,
} from "../src/activity";

describe("ActivityEngine", () => {
  it("pushes a typed child and returns its result to the caller", async () => {
    const registry = new ActivityRegistry();
    let childContext: ActivityContext<number> | undefined;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => simpleActivity(),
    });
    const child = defineActivity<{ readonly seed: number }, number>({
      key: "child",
      create: () => ({
        initialize: (_input, context) => {
          childContext = context;
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);

    const outcome = engine.push(child, { seed: 40 });
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    await childContext?.pop(42);

    await expect(outcome).resolves.toEqual({ status: "completed", value: 42 });
    expect(engine.snapshot.activeKey).toBe("root");
  });

  it("does not navigate back when the active activity reports dirty state", async () => {
    const registry = new ActivityRegistry();
    const root = defineActivity<void, never>({ key: "root", create: () => simpleActivity() });
    const child = defineActivity<void, void>({
      key: "dirty-child",
      create: () => simpleActivity({ status: "dirty", reason: "Unsaved changes" }),
    });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("dirty-child"));

    await expect(engine.requestBack()).resolves.toBe(false);
    expect(engine.snapshot.activeKey).toBe("dirty-child");
    await engine.cancel();
    await outcome;
  });

  it("aborts the frame signal and disposes exactly once", async () => {
    const registry = new ActivityRegistry();
    let signal: AbortSignal | undefined;
    let disposeCount = 0;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => ({
        initialize: (_input, context) => {
          signal = context.signal;
        },
        dispose: () => {
          disposeCount += 1;
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    await engine.dispose();
    await engine.dispose();

    expect(signal?.aborted).toBe(true);
    expect(disposeCount).toBe(1);
  });
});

function simpleActivity(leaveState?: LeaveState): Activity<void, never> {
  return {
    initialize: () => undefined,
    leaveState: () => leaveState ?? { status: "clean" },
    render: () => undefined,
  };
}
