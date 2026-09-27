import type { ActivityDefinition, ActivityKey } from "./types";

type RegisteredActivity = ActivityDefinition<unknown, unknown>;

export class ActivityRegistry {
  readonly #definitions = new Map<ActivityKey, RegisteredActivity>();

  register<Input, Output>(definition: ActivityDefinition<Input, Output>): void {
    if (this.#definitions.has(definition.key)) {
      throw new Error(`Activity key "${definition.key}" is already registered.`);
    }
    this.#definitions.set(definition.key, definition as RegisteredActivity);
  }

  registerAll(definitions: readonly RegisteredActivity[]): void {
    for (const definition of definitions) {
      this.register(definition);
    }
  }

  require<Input, Output>(
    definition: ActivityDefinition<Input, Output>,
  ): ActivityDefinition<Input, Output> {
    const registered = this.#definitions.get(definition.key);
    if (registered !== definition) {
      throw new Error(`Activity "${definition.key}" is not registered by the composition root.`);
    }
    return definition;
  }

  keys(): readonly ActivityKey[] {
    return [...this.#definitions.keys()];
  }
}
