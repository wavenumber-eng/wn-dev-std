import { afterEach, describe, expect, it, vi } from "vitest";
import { BackgroundRotator } from "../src/shell/background-rotator";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("background rotator", () => {
  it("cancels pending image work and timers when stopped", () => {
    vi.useFakeTimers();
    const images: HTMLImageElement[] = [];
    const OriginalImage = globalThis.Image;
    class TrackingImage extends OriginalImage {
      constructor() {
        super();
        images.push(this);
      }
    }
    vi.stubGlobal("Image", TrackingImage);
    const layers = [document.createElement("div"), document.createElement("div")] as const;
    const rotator = new BackgroundRotator({
      layers,
      assets: ["/backgrounds/one.jpg", "/backgrounds/two.jpg"],
      intervalMs: 20_000,
      reducedMotion: false,
    });

    rotator.start();
    expect(images).toHaveLength(1);
    expect(vi.getTimerCount()).toBe(1);
    rotator.stop();
    images[0]?.dispatchEvent(new Event("load"));

    expect(vi.getTimerCount()).toBe(0);
    expect(layers[0].style.getPropertyValue("--shell-background-image")).toBe("");
  });

  it("uses the CSS motion token after suppressing only the initial transition", () => {
    const images: HTMLImageElement[] = [];
    const OriginalImage = globalThis.Image;
    class TrackingImage extends OriginalImage {
      constructor() {
        super();
        images.push(this);
      }
    }
    vi.stubGlobal("Image", TrackingImage);
    const layers = [document.createElement("div"), document.createElement("div")] as const;
    const rotator = new BackgroundRotator({
      layers,
      assets: ["/backgrounds/one.jpg", "/backgrounds/two.jpg"],
      intervalMs: 20_000,
      reducedMotion: true,
    });

    rotator.start();
    images[0]?.dispatchEvent(new Event("load"));
    expect(layers[0].style.getPropertyValue("--shell-background-crossfade")).toBe("0ms");

    rotator.next();
    images[1]?.dispatchEvent(new Event("load"));
    expect(layers[1].style.getPropertyValue("--shell-background-crossfade")).toBe("");
  });

  it("clears stale active layers when a new host rotator starts", () => {
    const images: HTMLImageElement[] = [];
    const OriginalImage = globalThis.Image;
    class TrackingImage extends OriginalImage {
      constructor() {
        super();
        images.push(this);
      }
    }
    vi.stubGlobal("Image", TrackingImage);
    const layers = [document.createElement("div"), document.createElement("div")] as const;
    const options = {
      layers,
      assets: ["/backgrounds/one.jpg", "/backgrounds/two.jpg"],
      intervalMs: 20_000,
      reducedMotion: true,
    } as const;
    const first = new BackgroundRotator(options);
    first.start();
    images[0]?.dispatchEvent(new Event("load"));
    first.next();
    images[1]?.dispatchEvent(new Event("load"));
    expect(layers[1].classList.contains("active")).toBe(true);
    first.stop();

    const replacement = new BackgroundRotator(options);
    replacement.start();

    expect(layers[1].classList.contains("active")).toBe(false);
    images[2]?.dispatchEvent(new Event("load"));
    expect(layers.filter((layer) => layer.classList.contains("active"))).toHaveLength(1);
  });
});
