# Creating And Registering An Activity

1. Create `src/features/<feature>/<feature>-activity.ts` with typed input,
   output, and an activity definition created by `defineActivity`.
2. Choose activity-local fields unless multiple activities in the same feature
   genuinely share state.
3. Implement the controller in `<feature>-activity.ts` using only injected
   capabilities and public definitions.
4. Implement the Lit view in `<feature>-view.ts`. Render controller state and
   report user intent; do not construct backend transports.
5. Export only the public definition and contract types from the feature's
   `index.ts`. Other features import this index, never the implementation or
   view file.
6. Register the definition and inject dependencies in
   `src/application/create-application.ts`. Activities never self-register.
7. Select a named `shellProfile` on the activity definition. The activity
   requests presentation policy but never manipulates shell regions.
8. Invoke another activity with `context.push(definition, input)` and handle
   both completed and cancelled outcomes.
9. Return with `context.pop(output)` or `context.cancel()`.
10. Tie requests, streams, timers, and subscriptions to `context.signal` or
   dispose them explicitly.
11. Wrap promises launched from synchronous UI callbacks with
    `observeActivityTask(context, promise)` so unexpected failures reach the
    host error boundary instead of becoming unhandled rejections.
12. Test input, result, cancellation, retained caller state, leave policy,
    cleanup, and missing/duplicate registration.
13. Run `npm run signoff`.

Minimal shape:

```ts
class ChoosePartActivity implements Activity<ChoosePartInput, PartSummary> {
  initialize(input: ChoosePartInput, context: ActivityContext<PartSummary>): void {
    // Retain only this frame's input, context, and transient state.
  }

  render(): unknown {
    // Return host-renderable output and report user intent through callbacks.
  }
}

export const choosePartActivity = defineActivity({
  key: "choose-part",
  shellProfile: "focused",
  create: () => new ChoosePartActivity(),
});
```

Navigation is an event-time operation. Do not push or switch while
`initialize` is still running: lifecycle transitions are serialized, so an
initializer that awaits a new transition would wait on itself. Initialize the
frame, render it, then navigate from a user intent, command completion, or host
event.

Forbidden dependencies: sibling activity implementation, sibling store, sibling
view, shell implementation, global registry, raw fetch, EventSource, WebSocket,
or feature-local theme constants.
