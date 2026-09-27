import { afterEach, describe, expect, it, vi } from "vitest";
import "../src/shell/reference-app";
import type { ReferenceApp } from "../src/shell/reference-app";

afterEach(() => {
  vi.useRealTimers();
  document.body.replaceChildren();
  document.documentElement.removeAttribute("data-theme");
});

describe("reference app", () => {
  it("hosts the root activity in a Lit application shell", async () => {
    const element = document.createElement("wn-reference-app") as ReferenceApp;
    document.body.append(element);
    await element.updateComplete;
    await vi.waitFor(() =>
      expect(element.querySelector(".panel h1")?.textContent).toContain("small"),
    );

    expect(element.querySelector(".app-header")).not.toBeNull();
    expect(element.querySelectorAll(".background-layer")).toHaveLength(2);
    expect(element.textContent).toContain("home:clean");
  });

  it.each([
    ["workspace", true, true],
    ["focused", true, false],
    ["background-only", false, true],
    ["bare", false, false],
  ] as const)(
    "renders the %s shell profile policy",
    async (profile, showsHeader, showsBackground) => {
      const element = document.createElement("wn-reference-app") as ReferenceApp;
      document.body.append(element);
      await element.updateComplete;
      await vi.waitFor(() =>
        expect(element.querySelector(".profile-select select")).not.toBeNull(),
      );
      const select = element.querySelector<HTMLSelectElement>(".profile-select select");
      if (select === null) {
        throw new Error("Profile selector was not rendered.");
      }
      select.value = profile;
      select.dispatchEvent(new Event("change"));
      await element.updateComplete;

      expect(element.querySelector(".app-header") !== null).toBe(showsHeader);
      expect(element.querySelector(".activity-meta") !== null).toBe(showsHeader);
      expect(element.querySelector(".shell-recovery") !== null).toBe(!showsHeader);
      expect(element.querySelector(".backgrounds")?.classList.contains("backgrounds-hidden")).toBe(
        !showsBackground,
      );
      if (!showsHeader) {
        const restore = [...element.querySelectorAll<HTMLButtonElement>("button")].find(
          (button) => button.textContent?.trim() === "Restore activity shell",
        );
        expect(restore).not.toBeUndefined();
        restore?.click();
        await element.updateComplete;
        expect(element.querySelector(".app-header")).not.toBeNull();
        expect(element.querySelector(".shell-recovery")).toBeNull();
      }
      element.remove();
    },
  );

  it("restarts shell-owned background work when the same host reconnects", async () => {
    vi.useFakeTimers();
    const element = document.createElement("wn-reference-app") as ReferenceApp;
    document.body.append(element);
    await element.updateComplete;
    await Promise.resolve();
    expect(vi.getTimerCount()).toBe(1);

    element.remove();
    expect(vi.getTimerCount()).toBe(0);

    document.body.append(element);
    await element.updateComplete;
    await Promise.resolve();
    expect(vi.getTimerCount()).toBe(1);

    const pause = [...element.querySelectorAll<HTMLButtonElement>("button")].find(
      (button) => button.textContent?.trim() === "Pause background",
    );
    pause?.click();
    expect(vi.getTimerCount()).toBe(0);
    element.remove();
    document.body.append(element);
    await element.updateComplete;
    await Promise.resolve();
    expect(vi.getTimerCount()).toBe(0);
  });
});
