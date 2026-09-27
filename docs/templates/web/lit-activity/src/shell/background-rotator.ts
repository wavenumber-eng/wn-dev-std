export interface BackgroundRotatorOptions {
  readonly layers: readonly [HTMLElement, HTMLElement];
  readonly assets: readonly string[];
  readonly intervalMs: number;
  readonly reducedMotion: boolean;
}

export class BackgroundRotator {
  readonly #options: BackgroundRotatorOptions;
  #activeLayer = 0;
  #assetIndex = 0;
  #timer: number | undefined;
  #pendingImage: HTMLImageElement | undefined;
  #pendingLoad: (() => void) | undefined;
  #pendingError: (() => void) | undefined;

  constructor(options: BackgroundRotatorOptions) {
    this.#options = options;
  }

  start(): void {
    this.stop();
    for (const layer of this.#options.layers) {
      layer.classList.remove("active");
    }
    this.#assetIndex = Math.floor(Math.random() * this.#options.assets.length);
    this.#show(this.#activeLayer, this.#assetIndex, true);
    if (!this.#options.reducedMotion && this.#options.assets.length > 1) {
      this.#timer = window.setInterval(() => this.next(), this.#options.intervalMs);
    }
  }

  next(): void {
    const nextLayer = this.#activeLayer === 0 ? 1 : 0;
    this.#assetIndex = (this.#assetIndex + 1) % this.#options.assets.length;
    this.#show(nextLayer, this.#assetIndex, false);
  }

  stop(): void {
    if (this.#timer !== undefined) {
      window.clearInterval(this.#timer);
      this.#timer = undefined;
    }
    this.#cancelPendingImage();
  }

  #show(layerIndex: number, assetIndex: number, initial: boolean): void {
    const target = layerIndex === 0 ? this.#options.layers[0] : this.#options.layers[1];
    const current = this.#activeLayer === 0 ? this.#options.layers[0] : this.#options.layers[1];
    const source = this.#options.assets[assetIndex];
    if (source === undefined) {
      return;
    }
    this.#cancelPendingImage();
    const image = new Image();
    const onLoad = (): void => {
      if (this.#pendingImage !== image) {
        return;
      }
      this.#clearPendingReferences();
      target.style.setProperty("--shell-background-image", `url("${escapeCssUrl(source)}")`);
      if (initial) {
        target.style.setProperty("--shell-background-crossfade", "0ms");
      } else {
        target.style.removeProperty("--shell-background-crossfade");
      }
      target.classList.add("active");
      if (target !== current) {
        current.classList.remove("active");
      }
      this.#activeLayer = layerIndex;
    };
    const onError = (): void => this.#clearPendingReferences();
    this.#pendingImage = image;
    this.#pendingLoad = onLoad;
    this.#pendingError = onError;
    image.addEventListener("load", onLoad, { once: true });
    image.addEventListener("error", onError, { once: true });
    image.src = source;
  }

  #cancelPendingImage(): void {
    const image = this.#pendingImage;
    if (image === undefined) {
      return;
    }
    if (this.#pendingLoad !== undefined) {
      image.removeEventListener("load", this.#pendingLoad);
    }
    if (this.#pendingError !== undefined) {
      image.removeEventListener("error", this.#pendingError);
    }
    image.src = "";
    this.#clearPendingReferences();
  }

  #clearPendingReferences(): void {
    this.#pendingImage = undefined;
    this.#pendingLoad = undefined;
    this.#pendingError = undefined;
  }
}

function escapeCssUrl(value: string): string {
  return value.replace(/["\\]/g, "\\$&");
}
