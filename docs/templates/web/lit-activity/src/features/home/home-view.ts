import { html, type TemplateResult } from "lit";

export interface HomeViewModel {
  readonly lastProject: string | undefined;
  readonly onCreate: () => void;
}

export function homeView(model: HomeViewModel): TemplateResult {
  return html`
    <section class="panel flow" aria-labelledby="home-title">
      <div class="eyebrow">ROOT ACTIVITY</div>
      <h1 id="home-title">A small, composable application</h1>
      <p class="lede">
        The shell hosts one active activity. Open the editor to see typed push, result, pop, and
        cancellation behavior without global workflow state.
      </p>
      <div class="actions">
        <button class="button primary" @click=${model.onCreate}>Push editor activity</button>
      </div>
      ${
        model.lastProject === undefined
          ? html`<p class="status">No child result has returned yet.</p>`
          : html`<p class="status success">Returned project: ${model.lastProject}</p>`
      }
    </section>
  `;
}
