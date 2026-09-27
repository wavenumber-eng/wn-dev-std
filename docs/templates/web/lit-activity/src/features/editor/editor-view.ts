import { html, type TemplateResult } from "lit";

export interface EditorViewModel {
  readonly name: string;
  readonly busy: boolean;
  readonly error: string | undefined;
  readonly template: string | undefined;
  readonly onNameChanged: (name: string) => void;
  readonly onChooseTemplate: () => void;
  readonly onSave: () => void;
  readonly onCancel: () => void;
}

export function editorView(model: EditorViewModel): TemplateResult {
  return html`
    <section class="panel flow" aria-labelledby="editor-title">
      <div class="eyebrow">CHILD ACTIVITY</div>
      <h1 id="editor-title">Create project</h1>
      <p class="lede">
        This frame owns its draft, reports dirty or in-flight state, and returns a typed result.
      </p>
      <label class="field">
        <span>Project name</span>
        <input
          .value=${model.name}
          ?disabled=${model.busy}
          @input=${(event: Event) =>
            model.onNameChanged((event.currentTarget as HTMLInputElement).value)}
        />
      </label>
      <div class="inline-setting">
        <span>Template: ${model.template ?? "none"}</span>
        <button class="button" ?disabled=${model.busy} @click=${model.onChooseTemplate}>
          Push nested picker
        </button>
      </div>
      ${model.error === undefined ? "" : html`<p class="error" role="alert">${model.error}</p>`}
      <div class="actions">
        <button class="button primary" ?disabled=${model.busy} @click=${model.onSave}>
          ${model.busy ? "Saving..." : "Save and return"}
        </button>
        <button class="button" ?disabled=${model.busy} @click=${model.onCancel}>Cancel</button>
      </div>
    </section>
  `;
}
