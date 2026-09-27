import { createHash } from "node:crypto";
import { readFile, readdir, writeFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const generatedRoot = resolve(root, "generated");
const manifestPath = resolve(generatedRoot, "manifest.json");
const fixedSourcePaths = [
  "tspconfig.yaml",
  "package.json",
  "package-lock.json",
  "scripts/clean-generated.mjs",
  "scripts/generated-manifest.mjs",
];

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

async function generatedFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...await generatedFiles(path));
    } else if (path !== manifestPath) {
      files.push(path);
    }
  }
  return files.sort();
}

async function sourcePaths() {
  const contracts = await generatedFiles(resolve(root, "contracts"));
  const contractPaths = contracts
    .filter((path) => path.endsWith(".tsp"))
    .map((path) => relative(root, path).replaceAll("\\", "/"));
  return [...contractPaths, ...fixedSourcePaths].sort();
}

async function buildManifest() {
  const source = {};
  for (const path of await sourcePaths()) {
    source[path] = sha256(await readFile(resolve(root, path)));
  }
  const generated = {};
  for (const path of await generatedFiles(generatedRoot)) {
    generated[relative(root, path).replaceAll("\\", "/")] = sha256(await readFile(path));
  }
  return { schema_version: 1, source, generated };
}

const rendered = `${JSON.stringify(await buildManifest(), null, 2)}\n`;
if (process.argv.includes("--check")) {
  const committed = await readFile(manifestPath, "utf8");
  if (rendered !== committed) {
    throw new Error("generated outputs are stale; run npm run generate");
  }
} else {
  await writeFile(manifestPath, rendered);
}
