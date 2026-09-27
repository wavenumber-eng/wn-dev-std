export type ActivityKey = string;

export type LeaveState =
  | { readonly status: "clean" }
  | { readonly status: "dirty"; readonly reason: string }
  | { readonly status: "in-flight"; readonly reason: string }
  | { readonly status: "blocked"; readonly reason: string };

export type ActivityOutcome<Output> =
  | { readonly status: "completed"; readonly value: Output }
  | { readonly status: "cancelled" };

export interface ActivityDefinition<Input, Output> {
  readonly key: ActivityKey;
  readonly shellProfile?: string;
  readonly create: () => Activity<Input, Output>;
}

export interface ActivityContext<Output> {
  readonly signal: AbortSignal;
  push<Input, ChildOutput>(
    definition: ActivityDefinition<Input, ChildOutput>,
    input: Input,
  ): Promise<ActivityOutcome<ChildOutput>>;
  pop(value: Output): Promise<void>;
  cancel(): Promise<void>;
  switchRoot<Input, RootOutput>(
    definition: ActivityDefinition<Input, RootOutput>,
    input: Input,
  ): Promise<void>;
  requestExit(): Promise<boolean>;
  changed(): void;
  reportFailure(error: unknown): void;
}

export interface ActivityFailureReporter {
  reportFailure(error: unknown): void;
}

export interface Activity<Input, Output> {
  initialize(input: Input, context: ActivityContext<Output>): void | Promise<void>;
  activate?(): void | Promise<void>;
  deactivate?(): void | Promise<void>;
  leaveState?(): LeaveState | Promise<LeaveState>;
  dispose?(): void | Promise<void>;
  render(): unknown;
}

export interface ActivityStackEntry {
  readonly key: ActivityKey;
  readonly leaveState: LeaveState["status"];
  readonly shellProfile: string | undefined;
}

export interface ActivitySnapshot {
  readonly stack: readonly ActivityStackEntry[];
  readonly activeKey: ActivityKey | undefined;
  readonly canGoBack: boolean;
}

export type ActivitySubscriber = (snapshot: ActivitySnapshot) => void;
export type ActivityFailureSubscriber = (error: unknown) => void;

export function defineActivity<Input, Output>(
  definition: ActivityDefinition<Input, Output>,
): ActivityDefinition<Input, Output> {
  return Object.freeze(definition);
}

export function observeActivityTask(
  reporter: ActivityFailureReporter,
  operation: Promise<unknown>,
): void {
  void operation.catch((error: unknown) => reporter.reportFailure(error));
}
