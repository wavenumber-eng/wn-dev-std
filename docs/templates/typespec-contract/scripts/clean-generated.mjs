import { mkdir, rm } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
for (const directory of ["schema", "openapi", "typescript"]) {
  const path = resolve(root, "generated", directory);
  await rm(path, { force: true, recursive: true });
  await mkdir(path, { recursive: true });
}
