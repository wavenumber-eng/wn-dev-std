// @vitest-environment node

import { describe, expect, it, vi } from "vitest";
import {
  type Activity,
  type ActivityContext,
  ActivityEngine,
  ActivityRegistry,
  defineActivity,
  observeActivityTask,
} from "../src/activity";

describe("ActivityEngine edge behavior", () => {
  it("requires explicit, unique composition-root registration", async () => {
    const registry = new ActivityRegistry();
    const registered = defineActivity<void, never>({
      key: "registered",
      create: () => simpleActivity(),
    });
    const missing = defineActivity<void, never>({
      key: "missing",
      create: () => simpleActivity(),
    });
    registry.register(registered);

    expect(() => registry.register(registered)).toThrow("already registered");
    await expect(new ActivityEngine(registry).start(missing, undefined)).rejects.toThrow(
      "not registered",
    );
  });

  it("rolls back a failed child activation and resumes its parent", async () => {
    const registry = new ActivityRegistry();
    let parentActivations = 0;
    let failedDisposals = 0;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => ({
        initialize: () => undefined,
        activate: () => {
          parentActivations += 1;
        },
        render: () => undefined,
      }),
    });
    const failing = defineActivity<void, void>({
      key: "failing",
      create: () => ({
        initialize: () => undefined,
        activate: () => {
          throw new Error("activation failed");
        },
        dispose: () => {
          failedDisposals += 1;
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    registry.register(failing);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);

    await expect(engine.push(failing, undefined)).rejects.toThrow("activation failed");
    expect(engine.snapshot.activeKey).toBe("root");
    expect(parentActivations).toBe(2);
    expect(failedDisposals).toBe(1);
  });

  it("switches a root only when no caller is waiting", async () => {
    const registry = new ActivityRegistry();
    const first = defineActivity<void, never>({ key: "first", create: () => simpleActivity() });
    const second = defineActivity<void, never>({ key: "second", create: () => simpleActivity() });
    const child = defineActivity<void, void>({ key: "child", create: () => simpleActivity() });
    registry.register(first);
    registry.register(second);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(first, undefined);
    await engine.switchRoot(second, undefined);
    expect(engine.snapshot.activeKey).toBe("second");

    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    await expect(engine.switchRoot(first, undefined)).rejects.toThrow("no child activity");
    await engine.cancel();
    await outcome;
  });

  it("binds navigation capabilities to the frame that received them", async () => {
    const registry = new ActivityRegistry();
    let rootContext: ActivityContext<never> | undefined;
    let childContext: ActivityContext<void> | undefined;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => ({
        initialize: (_input, context) => {
          rootContext = context;
        },
        render: () => undefined,
      }),
    });
    const child = defineActivity<void, void>({
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

    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));
    await expect(rootContext?.cancel()).rejects.toThrow("no longer the active frame");
    expect(engine.snapshot.activeKey).toBe("child");
    await childContext?.cancel();
    await expect(outcome).resolves.toEqual({ status: "cancelled" });
    await expect(childContext?.pop()).rejects.toThrow("root activity cannot pop");
    expect(engine.snapshot.activeKey).toBe("root");
  });

  it("cleans a failed child transition and resumes the parent before surfacing errors", async () => {
    const registry = new ActivityRegistry();
    let parentActivations = 0;
    let childDisposals = 0;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => ({
        initialize: () => undefined,
        activate: () => {
          parentActivations += 1;
        },
        render: () => undefined,
      }),
    });
    const child = defineActivity<void, void>({
      key: "child",
      create: () => ({
        initialize: () => undefined,
        deactivate: () => {
          throw new Error("child deactivation failed");
        },
        dispose: () => {
          childDisposals += 1;
          throw new Error("child disposal failed");
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const outcome = engine.push(child, undefined);
    const outcomeFailure = outcome.then(
      () => undefined,
      (error: unknown) => error,
    );
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));

    await expect(engine.cancel()).rejects.toThrow("deactivation and disposal both failed");
    expect(await outcomeFailure).toBeInstanceOf(AggregateError);
    expect(engine.snapshot.activeKey).toBe("root");
    expect(parentActivations).toBe(2);
    expect(childDisposals).toBe(1);
  });

  it("continues disposing every frame after an earlier disposal failure", async () => {
    const registry = new ActivityRegistry();
    const disposed: string[] = [];
    const root = defineActivity<void, never>({
      key: "root",
      create: () => failingDisposeActivity("root", disposed),
    });
    const child = defineActivity<void, void>({
      key: "child",
      create: () => failingDisposeActivity("child", disposed),
    });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));

    await expect(engine.dispose()).rejects.toThrow("Multiple activity shutdown");
    await expect(outcome).resolves.toEqual({ status: "cancelled" });
    expect(disposed).toEqual(["child", "root"]);
    expect(engine.snapshot.stack).toEqual([]);
  });

  it("reports queued leave-state failures instead of creating an unhandled rejection", async () => {
    const registry = new ActivityRegistry();
    let context: ActivityContext<never> | undefined;
    let leaveChecks = 0;
    const root = defineActivity<void, never>({
      key: "root",
      create: () => ({
        initialize: (_input, activityContext) => {
          context = activityContext;
        },
        leaveState: () => {
          leaveChecks += 1;
          if (leaveChecks > 1) {
            throw new Error("leave-state failed");
          }
          return { status: "clean" };
        },
        render: () => undefined,
      }),
    });
    registry.register(root);
    const engine = new ActivityEngine(registry);
    const failures: unknown[] = [];
    engine.subscribeFailures((error) => failures.push(error));
    await engine.start(root, undefined);

    context?.changed();

    await vi.waitFor(() => expect(failures).toHaveLength(1));
    expect(failures[0]).toEqual(expect.objectContaining({ message: "leave-state failed" }));
  });

  it("routes observed event-time promise failures to the host boundary", async () => {
    const failures: unknown[] = [];
    const expected = new Error("event task failed");

    observeActivityTask(
      { reportFailure: (error) => failures.push(error) },
      Promise.reject(expected),
    );

    await vi.waitFor(() => expect(failures).toEqual([expected]));
  });

  it("isolates throwing observers from transitions and waiting child results", async () => {
    const registry = new ActivityRegistry();
    const root = defineActivity<void, never>({ key: "root", create: () => simpleActivity() });
    const child = defineActivity<void, void>({ key: "child", create: () => simpleActivity() });
    registry.register(root);
    registry.register(child);
    const engine = new ActivityEngine(registry);
    const observed: string[] = [];
    const failures: unknown[] = [];
    let observerShouldThrow = false;
    engine.subscribe(() => {
      if (observerShouldThrow) {
        throw new Error("host observer failed");
      }
    });
    engine.subscribe((snapshot) => observed.push(snapshot.activeKey ?? "none"));
    engine.subscribeFailures(() => {
      throw new Error("failure observer failed");
    });
    engine.subscribeFailures((error) => failures.push(error));
    await engine.start(root, undefined);
    const outcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));

    observerShouldThrow = true;
    await expect(engine.cancel()).resolves.toBeUndefined();
    await expect(outcome).resolves.toEqual({ status: "cancelled" });

    expect(observed.at(-1)).toBe("root");
    expect(failures).toEqual([expect.objectContaining({ message: "host observer failed" })]);
  });

  it("keeps back evaluation and the resulting pop in one atomic transition", async () => {
    const registry = new ActivityRegistry();
    let childContext: ActivityContext<void> | undefined;
    let releaseLeave: (() => void) | undefined;
    let leaveChecks = 0;
    const leaveGate = new Promise<void>((resolve) => {
      releaseLeave = resolve;
    });
    const root = defineActivity<void, never>({ key: "root", create: () => simpleActivity() });
    const child = defineActivity<void, void>({
      key: "child",
      create: () => ({
        initialize: (_input, context) => {
          childContext = context;
        },
        leaveState: async () => {
          leaveChecks += 1;
          if (leaveChecks > 1) {
            await leaveGate;
          }
          return { status: "clean" };
        },
        render: () => undefined,
      }),
    });
    const grandchild = defineActivity<void, void>({
      key: "grandchild",
      create: () => simpleActivity(),
    });
    registry.register(root);
    registry.register(child);
    registry.register(grandchild);
    const engine = new ActivityEngine(registry);
    await engine.start(root, undefined);
    const childOutcome = engine.push(child, undefined);
    await vi.waitFor(() => expect(engine.snapshot.activeKey).toBe("child"));

    const back = engine.requestBack();
    await vi.waitFor(() => expect(leaveChecks).toBe(2));
    const latePush = childContext?.push(grandchild, undefined);
    releaseLeave?.();

    await expect(back).resolves.toBe(true);
    await expect(childOutcome).resolves.toEqual({ status: "cancelled" });
    await expect(latePush).rejects.toThrow("no longer the active frame");
    expect(engine.snapshot.activeKey).toBe("root");
  });
});

function simpleActivity(): Activity<void, never> {
  return { initialize: () => undefined, render: () => undefined };
}

function failingDisposeActivity<Output>(key: string, disposed: string[]): Activity<void, Output> {
  return {
    initialize: () => undefined,
    dispose: () => {
      disposed.push(key);
      throw new Error(`${key} disposal failed`);
    },
    render: () => undefined,
  };
}
