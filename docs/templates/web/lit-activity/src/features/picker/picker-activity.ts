import {
  type Activity,
  type ActivityContext,
  defineActivity,
  type LeaveState,
  observeActivityTask,
} from "../../activity";
import { pickerView } from "./picker-view";

export interface PickerInput {
  readonly options: readonly string[];
}

class PickerActivity implements Activity<PickerInput, string> {
  #context: ActivityContext<string> | undefined;
  #options: readonly string[] = [];
  #selected: string | undefined;

  initialize(input: PickerInput, context: ActivityContext<string>): void {
    this.#options = input.options;
    this.#context = context;
  }

  leaveState(): LeaveState {
    return this.#selected === undefined
      ? { status: "blocked", reason: "Choose an option or use explicit cancel." }
      : { status: "clean" };
  }

  render(): unknown {
    const context = this.#requireContext();
    return pickerView({
      options: this.#options,
      selected: this.#selected,
      onSelect: (value) => {
        this.#selected = value;
        this.#requireContext().changed();
      },
      onChoose: () => {
        if (this.#selected !== undefined) {
          observeActivityTask(context, context.pop(this.#selected));
        }
      },
      onCancel: () => observeActivityTask(context, context.cancel()),
    });
  }

  #requireContext(): ActivityContext<string> {
    if (this.#context === undefined) {
      throw new Error("Picker activity has not been initialized.");
    }
    return this.#context;
  }
}

export const pickerActivity = defineActivity<PickerInput, string>({
  key: "project-template-picker",
  shellProfile: "focused",
  create: () => new PickerActivity(),
});
