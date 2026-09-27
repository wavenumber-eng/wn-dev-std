import {
  type Activity,
  type ActivityContext,
  type ActivityDefinition,
  defineActivity,
  observeActivityTask,
} from "../../activity";
import type { EditorInput, EditorOutput } from "../editor";
import { homeView } from "./home-view";

export interface HomeInput {
  readonly title: string;
}

class HomeActivity implements Activity<HomeInput, never> {
  readonly #editor: ActivityDefinition<EditorInput, EditorOutput>;
  #context: ActivityContext<never> | undefined;
  #lastProject: string | undefined;

  constructor(editor: ActivityDefinition<EditorInput, EditorOutput>) {
    this.#editor = editor;
  }

  initialize(_input: HomeInput, context: ActivityContext<never>): void {
    this.#context = context;
  }

  render(): unknown {
    const context = this.#requireContext();
    return homeView({
      lastProject: this.#lastProject,
      onCreate: () => observeActivityTask(context, this.#createProject()),
    });
  }

  async #createProject(): Promise<void> {
    const context = this.#requireContext();
    const outcome = await context.push(this.#editor, { suggestedName: "Board library" });
    if (outcome.status === "completed") {
      this.#lastProject = outcome.value.name;
      context.changed();
    }
  }

  #requireContext(): ActivityContext<never> {
    if (this.#context === undefined) {
      throw new Error("Home activity has not been initialized.");
    }
    return this.#context;
  }
}

export function createHomeActivity(editor: ActivityDefinition<EditorInput, EditorOutput>) {
  return defineActivity<HomeInput, never>({
    key: "home",
    shellProfile: "workspace",
    create: () => new HomeActivity(editor),
  });
}
