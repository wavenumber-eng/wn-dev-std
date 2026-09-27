export type ShellProfileId = "workspace" | "focused" | "background-only" | "bare";

export interface ShellProfile {
  readonly id: ShellProfileId;
  readonly label: string;
  readonly productName: string;
  readonly productMark: string;
  readonly showHeader: boolean;
  readonly showBrand: boolean;
  readonly showBack: boolean;
  readonly showRootNavigation: boolean;
  readonly showBackground: boolean;
  readonly showExitCheck: boolean;
  readonly showStatusChrome: boolean;
}

export const SHELL_PROFILES: Readonly<Record<ShellProfileId, ShellProfile>> = {
  workspace: {
    id: "workspace",
    label: "Workspace",
    productName: "Wavenumber Activity Reference",
    productMark: "WN",
    showHeader: true,
    showBrand: true,
    showBack: true,
    showRootNavigation: true,
    showBackground: true,
    showExitCheck: true,
    showStatusChrome: true,
  },
  focused: {
    id: "focused",
    label: "Focused",
    productName: "Focused task",
    productMark: "F",
    showHeader: true,
    showBrand: true,
    showBack: true,
    showRootNavigation: false,
    showBackground: false,
    showExitCheck: true,
    showStatusChrome: true,
  },
  "background-only": {
    id: "background-only",
    label: "Background only",
    productName: "Background host",
    productMark: "BG",
    showHeader: false,
    showBrand: false,
    showBack: false,
    showRootNavigation: false,
    showBackground: true,
    showExitCheck: false,
    showStatusChrome: false,
  },
  bare: {
    id: "bare",
    label: "Bare",
    productName: "Bare host",
    productMark: "B",
    showHeader: false,
    showBrand: false,
    showBack: false,
    showRootNavigation: false,
    showBackground: false,
    showExitCheck: false,
    showStatusChrome: false,
  },
};

export function shellProfile(id: ShellProfileId): ShellProfile {
  return SHELL_PROFILES[id];
}
