import { html, LitElement, type TemplateResult } from "lit";
import type { ActivitySnapshot } from "../activity";
import { createApplication, type ReferenceApplication } from "../application/create-application";
import { BrowserHistoryCoordinator, WindowHistoryPort } from "../browser/browser-history";
import { BrowserLifecycleCoordinator } from "../browser/browser-lifecycle";
import { BackgroundRotator } from "./background-rotator";
import { SHELL_PROFILES, type ShellProfileId, shellProfile } from "./shell-profile";

const BACKGROUNDS = [
  "/backgrounds/bg0.jpg",
  "/backgrounds/bg1.jpg",
  "/backgrounds/bg2.jpg",
  "/backgrounds/bg3.jpg",
  "/backgrounds/bg4.jpg",
  "/backgrounds/bg5.jpg",
] as const;

export class ReferenceApp extends LitElement {
  #application: ReferenceApplication | undefined;
  #snapshot: ActivitySnapshot | undefined;
  #unsubscribe: (() => void) | undefined;
  #history: BrowserHistoryCoordinator | undefined;
  #lifecycle: BrowserLifecycleCoordinator | undefined;
  #rotator: BackgroundRotator | undefined;
  #profileOverride: ShellProfileId | undefined;
  #backgroundRunning = true;
  #notice = "";

  override createRenderRoot(): HTMLElement | DocumentFragment {
    return this;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this.#application = createApplication((error) => this.#handleActivityFailure(error));
    this.#unsubscribe = this.#application.engine.subscribe((snapshot) => {
      this.#snapshot = snapshot;
      this.requestUpdate();
    });
    this.#history = new BrowserHistoryCoordinator(
      this.#application.engine,
      new WindowHistoryPort(),
      { onFailure: (error) => this.#handleActivityFailure(error) },
    );
    this.#history.attach();
    this.#lifecycle = new BrowserLifecycleCoordinator(this.#application.engine);
    this.#lifecycle.attach();
    void this.#application.start().catch((error: unknown) => this.#handleActivityFailure(error));
    void this.updateComplete.then(() => this.#ensureBackgroundRotator());
  }

  override disconnectedCallback(): void {
    this.#rotator?.stop();
    this.#rotator = undefined;
    this.#history?.detach();
    this.#history = undefined;
    this.#lifecycle?.detach();
    this.#lifecycle = undefined;
    this.#unsubscribe?.();
    this.#unsubscribe = undefined;
    if (this.#application !== undefined) {
      void this.#application.engine
        .dispose()
        .catch((error: unknown) => this.#handleActivityFailure(error));
      this.#application = undefined;
    }
    super.disconnectedCallback();
  }

  protected override firstUpdated(): void {
    this.#ensureBackgroundRotator();
  }

  #ensureBackgroundRotator(): void {
    if (this.#rotator !== undefined) {
      return;
    }
    const layers = this.querySelectorAll<HTMLElement>(".background-layer");
    const first = layers.item(0);
    const second = layers.item(1);
    if (first === null || second === null) {
      return;
    }
    this.#rotator = new BackgroundRotator({
      layers: [first, second],
      assets: BACKGROUNDS,
      intervalMs: 20_000,
      reducedMotion: globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false,
    });
    if (this.#backgroundRunning) {
      this.#rotator.start();
    }
  }

  protected override render(): TemplateResult {
    const requestedProfile = this.#snapshot?.stack.at(-1)?.shellProfile;
    const activityProfile =
      requestedProfile !== undefined && isShellProfileId(requestedProfile)
        ? requestedProfile
        : "workspace";
    const profile = shellProfile(this.#profileOverride ?? activityProfile);
    const active = this.#application?.engine.active;
    const canSwitchRoot = this.#snapshot?.stack.length === 1;
    const backgroundsVisible = profile.showBackground && this.#backgroundRunning;
    return html`
      <div class="backgrounds ${backgroundsVisible ? "" : "backgrounds-hidden"}">
        <div class="background-layer" aria-hidden="true"></div>
        <div class="background-layer" aria-hidden="true"></div>
      </div>
      <div class="shell-scrim" aria-hidden="true"></div>
      <div
        class=${profile.showHeader ? "app-shell" : "app-shell shell-no-header"}
        data-shell-profile=${profile.id}
      >
        ${
          profile.showHeader
            ? html`<header class="app-header">
          <div class="header-leading">
            ${
              profile.showBrand
                ? html`<div class="brand">
                  <span class="brand-mark">${profile.productMark}</span>
                  <span>${profile.productName}</span>
                </div>`
                : html`<span class="profile-label">${profile.label} shell profile</span>`
            }
            ${
              profile.showRootNavigation
                ? html`<nav class="root-navigation" aria-label="Root activities">
                  <button
                    class="button quiet"
                    aria-current=${this.#snapshot?.activeKey === "home" ? "page" : "false"}
                    ?disabled=${!canSwitchRoot}
                    @click=${() => this.#observeHostTask(this.#switchRoot("workspace"))}
                  >Workspace</button>
                  <button
                    class="button quiet"
                    aria-current=${this.#snapshot?.activeKey === "component-gallery" ? "page" : "false"}
                    ?disabled=${!canSwitchRoot}
                    @click=${() => this.#observeHostTask(this.#switchRoot("gallery"))}
                  >Gallery</button>
                </nav>`
                : ""
            }
          </div>
          <div class="header-actions">
            ${
              profile.showBack
                ? html`<button
                  class="button quiet"
                  ?disabled=${this.#snapshot?.canGoBack !== true}
                  @click=${() => this.#observeHostTask(this.#goBack())}
                >Back</button>`
                : ""
            }
            ${this.#renderProfileSelect("Shell")}
            <button class="button quiet" @click=${this.#toggleBackground}>
              ${this.#backgroundRunning ? "Pause background" : "Resume background"}
            </button>
            <button class="button quiet" @click=${this.#toggleTheme}>Theme</button>
            ${
              profile.showExitCheck
                ? html`<button class="button quiet" @click=${() => this.#observeHostTask(this.#checkExit())}>
                  Check exit
                </button>`
                : ""
            }
          </div>
        </header>`
            : ""
        }
        <main class="app-main">
          ${
            profile.showStatusChrome
              ? html`<div class="activity-meta">
            <span>STACK</span>
            <code>${
              this.#snapshot?.stack
                .map((entry) => `${entry.key}:${entry.leaveState}`)
                .join(" / ") ?? "starting"
            }</code>
          </div>
          ${this.#notice === "" ? "" : html`<p class="notice" role="status">${this.#notice}</p>`}`
              : ""
          }
          <div class="activity-host">${active?.render() ?? html`<p>Starting...</p>`}</div>
        </main>
        ${
          !profile.showHeader && this.#profileOverride !== undefined
            ? html`<aside class="shell-recovery" aria-label="Shell preview controls">
              <button class="button quiet" @click=${this.#restoreActivityProfile}>
                Restore activity shell
              </button>
              ${this.#renderProfileSelect("Preview")}
            </aside>`
            : ""
        }
      </div>
    `;
  }

  #renderProfileSelect(label: string): TemplateResult {
    return html`<label class="profile-select">
      <span>${label}</span>
      <select @change=${this.#selectProfile} .value=${this.#profileOverride ?? "auto"}>
        <option value="auto">Activity default</option>
        ${Object.values(SHELL_PROFILES).map(
          (candidate) => html`<option value=${candidate.id}>${candidate.label}</option>`,
        )}
      </select>
    </label>`;
  }

  async #goBack(): Promise<void> {
    const moved = await this.#application?.engine.requestBack();
    this.#notice = moved === false ? "The active activity is not ready to leave." : "";
    this.requestUpdate();
  }

  async #switchRoot(target: "workspace" | "gallery"): Promise<void> {
    try {
      if (target === "workspace") {
        await this.#application?.showWorkspace();
      } else {
        await this.#application?.showGallery();
      }
      this.#notice = "Root activity switched without a return result.";
    } catch (error: unknown) {
      this.#notice = error instanceof Error ? error.message : "The root activity could not switch.";
    }
    this.requestUpdate();
  }

  async #checkExit(): Promise<void> {
    const allowed = await this.#application?.engine.requestExit();
    this.#notice = allowed === true ? "The active activity may exit cleanly." : "Exit is blocked.";
    this.requestUpdate();
  }

  #selectProfile(event: Event): void {
    const value = (event.currentTarget as HTMLSelectElement).value;
    if (value === "auto") {
      this.#profileOverride = undefined;
      this.requestUpdate();
    } else if (isShellProfileId(value)) {
      this.#profileOverride = value;
      this.requestUpdate();
    }
  }

  #restoreActivityProfile(): void {
    this.#profileOverride = undefined;
    this.requestUpdate();
  }

  #toggleBackground(): void {
    this.#backgroundRunning = !this.#backgroundRunning;
    if (this.#backgroundRunning) {
      this.#rotator?.start();
    } else {
      this.#rotator?.stop();
    }
    this.requestUpdate();
  }

  #toggleTheme(): void {
    const root = document.documentElement;
    root.dataset["theme"] = root.dataset["theme"] === "high-contrast" ? "default" : "high-contrast";
  }

  #handleActivityFailure(error: unknown): void {
    this.#notice =
      error instanceof Error ? error.message : "An unexpected activity failure occurred.";
    this.requestUpdate();
  }

  #observeHostTask(operation: Promise<unknown>): void {
    void operation.catch((error: unknown) => this.#handleActivityFailure(error));
  }
}

function isShellProfileId(value: string): value is ShellProfileId {
  return (
    value === "workspace" || value === "focused" || value === "background-only" || value === "bare"
  );
}

customElements.define("wn-reference-app", ReferenceApp);
