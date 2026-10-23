// Security floor for the October 2026 CA incident. Keep this copy project-owned.
import { pathToFileURL } from "node:url";

export function isSupportedNode(version) {
  const [major, minor, patch] = version.split(".").map(Number);
  const floor = { 22: [23, 4], 24: [22, 1], 26: [12, 1] }[major];
  return Boolean(floor && (minor > floor[0] || (minor === floor[0] && patch >= floor[1])));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!isSupportedNode(process.versions.node)) {
    console.error(
      "Use Node 22.23.4+, 24.22.1+, or 26.12.1+ on those release lines (CA security fix).",
    );
    process.exitCode = 1;
  }
}
