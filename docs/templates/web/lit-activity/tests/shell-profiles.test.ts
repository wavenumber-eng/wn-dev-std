import { describe, expect, it } from "vitest";
import { SHELL_PROFILES, shellProfile } from "../src/shell/shell-profile";

describe("shell profiles", () => {
  it("defines workspace, focused, background-only, and bare host policies", () => {
    expect(Object.keys(SHELL_PROFILES)).toEqual([
      "workspace",
      "focused",
      "background-only",
      "bare",
    ]);
    expect(shellProfile("workspace").showRootNavigation).toBe(true);
    expect(shellProfile("focused").showRootNavigation).toBe(false);
    expect(shellProfile("workspace").showHeader).toBe(true);
    expect(shellProfile("focused").showHeader).toBe(true);
    expect(shellProfile("background-only").showHeader).toBe(false);
    expect(shellProfile("bare").showHeader).toBe(false);
    expect(shellProfile("background-only").showStatusChrome).toBe(false);
    expect(shellProfile("bare").showStatusChrome).toBe(false);
    expect(shellProfile("background-only").showBackground).toBe(true);
    expect(shellProfile("bare").showBackground).toBe(false);
  });
});
