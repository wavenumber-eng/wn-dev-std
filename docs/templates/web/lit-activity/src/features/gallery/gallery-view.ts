import { html, type TemplateResult } from "lit";

export function galleryView(): TemplateResult {
  return html`
    <section class="panel flow" aria-labelledby="gallery-title">
      <div class="eyebrow">ROOT SWITCH TARGET · COMPONENT GALLERY</div>
      <h1 id="gallery-title">Design-language states</h1>
      <p class="lede">
        Native elements carry semantics; shared classes and tokens carry the visual language.
      </p>
      <div class="gallery-grid">
        <section class="gallery-group flow">
          <h2>Actions and inputs</h2>
          <div class="actions">
            <button class="button primary">Primary</button>
            <button class="button">Secondary</button>
            <button class="button" disabled>Disabled</button>
          </div>
          <label class="field"><span>Text input</span><input value="Focus me" /></label>
          <label class="choice"><input type="checkbox" checked /><span>Enabled option</span></label>
          <progress aria-label="Loading example" max="100" value="64">64%</progress>
        </section>
        <section class="gallery-group flow">
          <h2>Status and notification</h2>
          <p class="banner success">Saved successfully.</p>
          <p class="banner warning">A review is required.</p>
          <p class="banner error">The operation failed.</p>
          <div class="dialog-example" role="dialog" aria-modal="false" aria-labelledby="dialog-title">
            <strong id="dialog-title">Dialog surface</strong>
            <p>Hosts own overlays; activities own the workflow behind them.</p>
          </div>
        </section>
      </div>
      <div class="table-wrap">
        <table>
          <caption>Compact table language</caption>
          <thead><tr><th>Contract</th><th>Authority</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>Project</td><td>TypeSpec</td><td>Current</td></tr>
            <tr><td>Activity result</td><td>TypeScript</td><td>Local</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  `;
}
