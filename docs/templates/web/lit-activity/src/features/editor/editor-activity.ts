import {
  type Activity,
  type ActivityContext,
  type ActivityDefinition,
  defineActivity,
  type LeaveState,
  observeActivityTask,
} from "../../activity";
import type { PickerInput } from "../picker";
import type { ProjectApi, SavedProject } from "../projects";
import { editorView } from "./editor-view";

export interface EditorInput {
  readonly suggestedName: string;
}

export type EditorOutput = SavedProject;

class EditorActivity implements Activity<EditorInput, EditorOutput> {
  readonly #projects: ProjectApi;
  readonly #picker: ActivityDefinition<PickerInput, string>;
  #context: ActivityContext<EditorOutput> | undefined;
  #initialName = "";
  #name = "";
  #busy = false;
  #error: string | undefined;
  #template: string | undefined;

  constructor(projects: ProjectApi, picker: ActivityDefinition<PickerInput, string>) {
    this.#projects = projects;
    this.#picker = picker;
  }

  initialize(input: EditorInput, context: ActivityContext<EditorOutput>): void {
    this.#initialName = input.suggestedName;
    this.#name = input.suggestedName;
    this.#context = context;
  }

  leaveState(): LeaveState {
    if (this.#busy) {
      return { status: "in-flight", reason: "The project is being saved." };
    }
    if (this.#name !== this.#initialName) {
      return { status: "dirty", reason: "The project name has unsaved changes." };
    }
    return { status: "clean" };
  }

  render(): unknown {
    const context = this.#requireContext();
    return editorView({
      name: this.#name,
      busy: this.#busy,
      error: this.#error,
      template: this.#template,
      onNameChanged: (name) => {
        this.#name = name;
        this.#error = undefined;
        this.#requireContext().changed();
      },
      onChooseTemplate: () => observeActivityTask(context, this.#chooseTemplate()),
      onSave: () => observeActivityTask(context, this.#save()),
      onCancel: () => observeActivityTask(context, context.cancel()),
    });
  }

  async #chooseTemplate(): Promise<void> {
    const context = this.#requireContext();
    const outcome = await context.push(this.#picker, {
      options: ["Blank board", "Power supply", "Sensor module"],
    });
    if (outcome.status === "completed") {
      this.#template = outcome.value;
      context.changed();
    }
  }

  async #save(): Promise<void> {
    const context = this.#requireContext();
    this.#busy = true;
    this.#error = undefined;
    context.changed();
    let result: SavedProject;
    try {
      result = await this.#projects.saveDraft(this.#name.trim() || "Untitled", context.signal);
    } catch (error: unknown) {
      if (!context.signal.aborted) {
        this.#busy = false;
        this.#error = error instanceof Error ? error.message : "The project could not be saved.";
        context.changed();
      }
      return;
    }
    await context.pop(result);
  }

  #requireContext(): ActivityContext<EditorOutput> {
    if (this.#context === undefined) {
      throw new Error("Editor activity has not been initialized.");
    }
    return this.#context;
  }
}

export function createEditorActivity(
  projects: ProjectApi,
  picker: ActivityDefinition<PickerInput, string>,
) {
  return defineActivity<EditorInput, EditorOutput>({
    key: "project-editor",
    shellProfile: "focused",
    create: () => new EditorActivity(projects, picker),
  });
}
