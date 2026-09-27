import { html, type TemplateResult } from "lit";

export interface PickerViewModel {
  readonly options: readonly string[];
  readonly selected: string | undefined;
  readonly onSelect: (value: string) => void;
  readonly onChoose: () => void;
  readonly onCancel: () => void;
}

export function pickerView(model: PickerViewModel): TemplateResult {
  return html`
    <section class="panel flow" aria-labelledby="picker-title">
      <div class="eyebrow">NESTED CHILD ACTIVITY</div>
      <h1 id="picker-title">Choose a project template</h1>
      <p class="lede">Until a selection is made, this activity reports a blocked leave state.</p>
      <div class="choice-grid" role="radiogroup" aria-label="Project templates">
        ${model.options.map(
          (option) => html`
            <label class="choice">
              <input
                type="radio"
                name="project-template"
                .value=${option}
                .checked=${model.selected === option}
                @change=${() => model.onSelect(option)}
              />
              <span>${option}</span>
            </label>
          `,
        )}
      </div>
      <div class="actions">
        <button class="button primary" ?disabled=${model.selected === undefined} @click=${model.onChoose}>
          Return selection
        </button>
        <button class="button" @click=${model.onCancel}>Cancel explicitly</button>
      </div>
    </section>
  `;
}
