# Activity Model

An `Activity<Input, Output>` is an independent workflow with typed input, typed
completion, owned transient state, and a frame-scoped cancellation signal.

- `push` retains the caller, deactivates it, and opens a child. The caller
  awaits a completed or cancelled outcome.
- `pop` completes a non-root frame successfully and resumes its caller.
- `cancel` completes a non-root frame without a successful value.
- `switch` replaces the root only when no caller awaits a result.
- root exit is a host operation, never `pop`.

`push` returns `Promise<ActivityOutcome<Output>>`. Successful `pop` resolves a
`completed` outcome. Explicit cancel or host back resolves `cancelled`. A child
that cannot initialize or activate rejects the push, disposes its partial
frame, and resumes the caller. Calling `pop` or `cancel` on the root is an
error. Calling `switchRoot` while a child has a waiting caller is also an error.

An activity context is frame-bound. Once that frame is inactive or disposed,
its navigation operations cannot act on whichever frame happens to be active;
stale navigation rejects and stale `changed()` notifications are ignored. This
prevents retained callbacks from growing workflow tentacles.

Lifecycle transitions are serialized. A created frame is disposed exactly once,
including failed initialization or activation. Disposal aborts requests,
streams, timers, observers, and subscriptions tied to the frame.

Normal lifecycle order is:

1. deactivate the retained caller;
2. create and initialize a child frame;
3. activate the child;
4. render and handle intent while the frame is active;
5. deactivate and dispose the child exactly once;
6. complete its result and reactivate the caller.

Lifecycle cleanup is best-effort across every required step. If deactivation,
disposal, or parent reactivation fails, the engine still attempts the remaining
cleanup, rejects the waiting result, and reports the unexpected failure to the
host boundary. Shutdown deactivates the active frame and attempts to dispose
every frame even when an earlier hook fails.

Promise-returning activity work should normally be awaited. When a synchronous
view callback starts it, use `observeActivityTask(context, promise)`. The
helper reports rejection through the engine's failure channel, which the host
subscribes to as its error boundary, and prevents an unhandled rejection.
Snapshot observers are isolated from lifecycle transitions: a throwing host
observer is reported through that failure channel without blocking remaining
observers, cleanup, root replacement, or a waiting child result. A throwing
failure observer is likewise isolated from other failure observers.

The composition root owns registration. Definitions are explicit values, not
global names discovered at runtime. Duplicate keys and unregistered definitions
fail immediately. The kernel serializes lifecycle changes but never imports
Lit, DOM, browser history, networking, shell code, or a feature.

The engine and registry suites run in Vitest's Node environment, while the Lit
host and browser adapters run separately in jsdom. That neutral test host is
the executable portability proof: the kernel requires no browser global.

This is loosely inspired by Android activities, intents, results, and the back
stack. It does not reproduce Android manifests, implicit intents, process
ownership, or its large operating-system lifecycle.
