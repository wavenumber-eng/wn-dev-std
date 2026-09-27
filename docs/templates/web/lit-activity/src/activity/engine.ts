import type { ActivityRegistry } from "./registry";
import type {
  Activity,
  ActivityContext,
  ActivityDefinition,
  ActivityFailureSubscriber,
  ActivityOutcome,
  ActivitySnapshot,
  ActivitySubscriber,
  LeaveState,
} from "./types";

interface Deferred<Value> {
  readonly promise: Promise<Value>;
  readonly resolve: (value: Value) => void;
  readonly reject: (reason: unknown) => void;
}

interface Frame {
  readonly definition: ActivityDefinition<unknown, unknown>;
  readonly instance: Activity<unknown, unknown>;
  readonly controller: AbortController;
  readonly completion: Deferred<ActivityOutcome<unknown>> | undefined;
  currentLeave: LeaveState;
  disposed: boolean;
}

function deferred<Value>(): Deferred<Value> {
  let resolvePromise: ((value: Value) => void) | undefined;
  let rejectPromise: ((reason: unknown) => void) | undefined;
  const promise = new Promise<Value>((resolve, reject) => {
    resolvePromise = resolve;
    rejectPromise = reject;
  });
  if (resolvePromise === undefined || rejectPromise === undefined) {
    throw new Error("Promise callbacks were not initialized.");
  }
  return { promise, resolve: resolvePromise, reject: rejectPromise };
}

const CLEAN: LeaveState = { status: "clean" };
const NO_FAILURE = Symbol("no lifecycle failure");

async function captureFailure(
  failure: unknown,
  operation: () => void | Promise<void>,
  message: string,
): Promise<unknown> {
  try {
    await operation();
    return failure;
  } catch (error: unknown) {
    return failure === NO_FAILURE ? error : new AggregateError([failure, error], message);
  }
}

export class ActivityEngine {
  readonly #registry: ActivityRegistry;
  readonly #stack: Frame[] = [];
  readonly #subscribers = new Set<ActivitySubscriber>();
  readonly #failureSubscribers = new Set<ActivityFailureSubscriber>();
  #transition: Promise<void> = Promise.resolve();

  constructor(registry: ActivityRegistry) {
    this.#registry = registry;
  }

  get active(): Activity<unknown, unknown> | undefined {
    return this.#stack.at(-1)?.instance;
  }

  get snapshot(): ActivitySnapshot {
    const stack = this.#stack.map((frame) => ({
      key: frame.definition.key,
      leaveState: frame.currentLeave.status,
      shellProfile: frame.definition.shellProfile,
    }));
    return {
      stack,
      activeKey: stack.at(-1)?.key,
      canGoBack: stack.length > 1,
    };
  }

  subscribe(subscriber: ActivitySubscriber): () => void {
    this.#subscribers.add(subscriber);
    this.#notifySubscriber(subscriber, this.snapshot);
    return () => this.#subscribers.delete(subscriber);
  }

  subscribeFailures(subscriber: ActivityFailureSubscriber): () => void {
    this.#failureSubscribers.add(subscriber);
    return () => this.#failureSubscribers.delete(subscriber);
  }

  async start<Input, Output>(
    definition: ActivityDefinition<Input, Output>,
    input: Input,
  ): Promise<void> {
    await this.#enqueue(async () => {
      if (this.#stack.length !== 0) {
        throw new Error("The activity engine already has a root activity.");
      }
      const frame = await this.#createFrame(definition, input, undefined);
      this.#stack.push(frame);
      try {
        await frame.instance.activate?.();
      } catch (error: unknown) {
        this.#stack.pop();
        const failure = await captureFailure(
          error,
          () => this.#dispose(frame),
          "Root activation and cleanup both failed.",
        );
        throw failure;
      }
      this.#notify();
    });
  }

  async push<Input, Output>(
    definition: ActivityDefinition<Input, Output>,
    input: Input,
  ): Promise<ActivityOutcome<Output>> {
    return this.#pushFrom(undefined, definition, input);
  }

  async #pushFrom<Input, Output>(
    expectedParent: Frame | undefined,
    definition: ActivityDefinition<Input, Output>,
    input: Input,
  ): Promise<ActivityOutcome<Output>> {
    const completion = await this.#enqueue(async () => {
      const parent = this.#requireActive();
      this.#requireExpectedActive(expectedParent, parent);
      try {
        await parent.instance.deactivate?.();
      } catch (error: unknown) {
        const failure = await captureFailure(
          error,
          async () => {
            await parent.instance.activate?.();
          },
          "Parent deactivation and recovery both failed.",
        );
        throw failure;
      }
      const childCompletion = deferred<ActivityOutcome<unknown>>();
      let frame: Frame | undefined;
      try {
        frame = await this.#createFrame(definition, input, childCompletion);
        this.#stack.push(frame);
        await frame.instance.activate?.();
        this.#notify();
        return childCompletion;
      } catch (error: unknown) {
        let failure: unknown = error;
        if (frame !== undefined) {
          const frameIndex = this.#stack.indexOf(frame);
          if (frameIndex >= 0) {
            this.#stack.splice(frameIndex, 1);
          }
          failure = await captureFailure(
            failure,
            () => this.#dispose(frame as Frame),
            "Child activation and cleanup both failed.",
          );
        }
        failure = await captureFailure(
          failure,
          async () => {
            await parent.instance.activate?.();
          },
          "Child transition and parent recovery both failed.",
        );
        throw failure;
      }
    });
    return completion.promise as Promise<ActivityOutcome<Output>>;
  }

  async pop(value: unknown): Promise<void> {
    await this.#finishChild(undefined, { status: "completed", value });
  }

  async cancel(): Promise<void> {
    await this.#finishChild(undefined, { status: "cancelled" });
  }

  async switchRoot<Input, Output>(
    definition: ActivityDefinition<Input, Output>,
    input: Input,
  ): Promise<void> {
    await this.#switchRootFrom(undefined, definition, input);
  }

  async #switchRootFrom<Input, Output>(
    expectedCurrent: Frame | undefined,
    definition: ActivityDefinition<Input, Output>,
    input: Input,
  ): Promise<void> {
    await this.#enqueue(async () => {
      if (this.#stack.length !== 1) {
        throw new Error("Root switching is only legal when no child activity is open.");
      }
      const current = this.#requireActive();
      this.#requireExpectedActive(expectedCurrent, current);
      const leave = await this.#leaveState(current);
      current.currentLeave = leave;
      if (leave.status !== "clean") {
        throw new Error(`The root activity cannot be switched while it is ${leave.status}.`);
      }
      const replacement = await this.#createFrame(definition, input, undefined);
      try {
        await current.instance.deactivate?.();
        await replacement.instance.activate?.();
      } catch (error: unknown) {
        let failure = await captureFailure(
          error,
          () => this.#dispose(replacement),
          "Root switch and replacement cleanup both failed.",
        );
        failure = await captureFailure(
          failure,
          async () => {
            await current.instance.activate?.();
          },
          "Root switch and current-root recovery both failed.",
        );
        throw failure;
      }
      this.#stack[0] = replacement;
      this.#notify();
      await this.#dispose(current);
    });
  }

  async requestBack(): Promise<boolean> {
    return this.#enqueue(async () => {
      const current = this.#requireActive();
      current.currentLeave = await this.#leaveState(current);
      this.#notify();
      if (current.currentLeave.status !== "clean" || this.#stack.length === 1) {
        return false;
      }
      await this.#finishChildNow(current, { status: "cancelled" });
      return true;
    });
  }

  async requestExit(): Promise<boolean> {
    return this.#requestExitFrom(undefined);
  }

  async #requestExitFrom(expectedCurrent: Frame | undefined): Promise<boolean> {
    return this.#enqueue(async () => {
      const current = this.#requireActive();
      this.#requireExpectedActive(expectedCurrent, current);
      current.currentLeave = await this.#leaveState(current);
      this.#notify();
      return current.currentLeave.status === "clean";
    });
  }

  changed(): void {
    this.#changedFrom(undefined);
  }

  #changedFrom(expectedCurrent: Frame | undefined): void {
    void this.#enqueue(async () => {
      const active = this.#stack.at(-1);
      if (active !== undefined && (expectedCurrent === undefined || active === expectedCurrent)) {
        active.currentLeave = await this.#leaveState(active);
        this.#notify();
      }
    }).catch((error: unknown) => this.#reportFailure(error));
  }

  canExitCached(): boolean {
    return this.#stack.at(-1)?.currentLeave.status === "clean";
  }

  async dispose(): Promise<void> {
    await this.#enqueue(async () => {
      const frames = this.#stack.splice(0).reverse();
      let failure: unknown = NO_FAILURE;
      for (const [index, frame] of frames.entries()) {
        frame.completion?.resolve({ status: "cancelled" });
        if (index === 0) {
          failure = await captureFailure(
            failure,
            async () => {
              await frame.instance.deactivate?.();
            },
            "Multiple activity shutdown lifecycle operations failed.",
          );
        }
        failure = await captureFailure(
          failure,
          () => this.#dispose(frame),
          "Multiple activity shutdown lifecycle operations failed.",
        );
      }
      this.#notify();
      if (failure !== NO_FAILURE) {
        throw failure;
      }
    });
  }

  async #finishChild(
    expectedChild: Frame | undefined,
    outcome: ActivityOutcome<unknown>,
  ): Promise<void> {
    await this.#enqueue(() => this.#finishChildNow(expectedChild, outcome));
  }

  async #finishChildNow(
    expectedChild: Frame | undefined,
    outcome: ActivityOutcome<unknown>,
  ): Promise<void> {
    if (this.#stack.length < 2) {
      throw new Error("The root activity cannot pop or cancel itself.");
    }
    this.#requireExpectedActive(expectedChild, this.#requireActive());
    const child = this.#stack.pop();
    if (child === undefined) {
      throw new Error("Activity stack underflow.");
    }
    let failure = await captureFailure(
      NO_FAILURE,
      async () => {
        await child.instance.deactivate?.();
      },
      "Child deactivation failed.",
    );
    failure = await captureFailure(
      failure,
      () => this.#dispose(child),
      "Child deactivation and disposal both failed.",
    );
    const parent = this.#requireActive();
    failure = await captureFailure(
      failure,
      async () => {
        await parent.instance.activate?.();
      },
      "Child cleanup and parent reactivation both failed.",
    );
    this.#notify();
    if (failure !== NO_FAILURE) {
      child.completion?.reject(failure);
      throw failure;
    }
    child.completion?.resolve(outcome);
  }

  async #createFrame<Input, Output>(
    definition: ActivityDefinition<Input, Output>,
    input: Input,
    completion: Deferred<ActivityOutcome<unknown>> | undefined,
  ): Promise<Frame> {
    this.#registry.require(definition);
    const controller = new AbortController();
    const typedInstance = definition.create();
    const frame: Frame = {
      definition: definition as ActivityDefinition<unknown, unknown>,
      instance: typedInstance as Activity<unknown, unknown>,
      controller,
      completion,
      currentLeave: CLEAN,
      disposed: false,
    };
    const context: ActivityContext<Output> = {
      signal: controller.signal,
      push: (childDefinition, childInput) => this.#pushFrom(frame, childDefinition, childInput),
      pop: (value) => this.#finishChild(frame, { status: "completed", value }),
      cancel: () => this.#finishChild(frame, { status: "cancelled" }),
      switchRoot: (rootDefinition, rootInput) =>
        this.#switchRootFrom(frame, rootDefinition, rootInput),
      requestExit: () => this.#requestExitFrom(frame),
      changed: () => this.#changedFrom(frame),
      reportFailure: (error) => this.#reportFailure(error),
    };
    try {
      await typedInstance.initialize(input, context);
      frame.currentLeave = await this.#leaveState(frame);
    } catch (error: unknown) {
      const failure = await captureFailure(
        error,
        () => this.#dispose(frame),
        "Activity initialization and cleanup both failed.",
      );
      throw failure;
    }
    return frame;
  }

  async #leaveState(frame: Frame): Promise<LeaveState> {
    return (await frame.instance.leaveState?.()) ?? CLEAN;
  }

  async #dispose(frame: Frame): Promise<void> {
    if (frame.disposed) {
      return;
    }
    frame.disposed = true;
    frame.controller.abort();
    await frame.instance.dispose?.();
  }

  #requireActive(): Frame {
    const frame = this.#stack.at(-1);
    if (frame === undefined) {
      throw new Error("The activity engine has not been started.");
    }
    return frame;
  }

  #requireExpectedActive(expected: Frame | undefined, active: Frame): void {
    if (expected !== undefined && expected !== active) {
      throw new Error("The activity context is no longer the active frame.");
    }
  }

  #enqueue<Value>(operation: () => Value | Promise<Value>): Promise<Value> {
    const result = this.#transition.then(operation, operation);
    this.#transition = result.then(
      () => undefined,
      () => undefined,
    );
    return result;
  }

  #notify(): void {
    const snapshot = this.snapshot;
    for (const subscriber of this.#subscribers) {
      this.#notifySubscriber(subscriber, snapshot);
    }
  }

  #notifySubscriber(subscriber: ActivitySubscriber, snapshot: ActivitySnapshot): void {
    try {
      subscriber(snapshot);
    } catch (error: unknown) {
      this.#reportFailure(error);
    }
  }

  #reportFailure(error: unknown): void {
    for (const subscriber of this.#failureSubscribers) {
      try {
        subscriber(error);
      } catch {
        // Failure observers cannot be allowed to break lifecycle transitions.
      }
    }
  }
}
