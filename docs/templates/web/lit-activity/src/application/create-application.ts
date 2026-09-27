import { ActivityEngine, ActivityRegistry } from "../activity";
import { createEditorActivity } from "../features/editor";
import { galleryActivity } from "../features/gallery";
import { createHomeActivity } from "../features/home";
import { pickerActivity } from "../features/picker";
import { ProjectClient } from "../features/projects";
import { DemoTransport } from "../transport";

export interface ReferenceApplication {
  readonly engine: ActivityEngine;
  readonly start: () => Promise<void>;
  readonly showWorkspace: () => Promise<void>;
  readonly showGallery: () => Promise<void>;
}

export function createApplication(onFailure: (error: unknown) => void): ReferenceApplication {
  const registry = new ActivityRegistry();
  const transport = new DemoTransport();
  const projects = new ProjectClient(transport);
  const editor = createEditorActivity(projects, pickerActivity);
  const home = createHomeActivity(editor);

  registry.register(pickerActivity);
  registry.register(editor);
  registry.register(home);
  registry.register(galleryActivity);

  const engine = new ActivityEngine(registry);
  engine.subscribeFailures(onFailure);
  return {
    engine,
    start: () => engine.start(home, { title: "Wavenumber activity reference" }),
    showWorkspace: () => engine.switchRoot(home, { title: "Wavenumber activity reference" }),
    showGallery: () => engine.switchRoot(galleryActivity, { source: "shell-navigation" }),
  };
}
