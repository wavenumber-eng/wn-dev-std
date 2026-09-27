import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

const root = new URL("../../", import.meta.url);

async function loadJson(relativePath) {
  return JSON.parse(await readFile(new URL(relativePath, root), "utf8"));
}

async function snapshotSchema() {
  const schemaDir = new URL("generated/schema/", root);
  for (const name of await readdir(schemaDir)) {
    if (!name.endsWith(".json")) {
      continue;
    }
    const schema = JSON.parse(await readFile(join(fileURLToPath(schemaDir), name), "utf8"));
    if (schema.$id === "https://schemas.example.invalid/catalog/snapshot/v1.json") {
      return schema;
    }
  }
  throw new Error("catalog snapshot schema was not generated");
}

test("shared conformance vectors match the generated JSON Schema", async () => {
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  const validate = ajv.compile(await snapshotSchema());
  assert.equal(validate(await loadJson("fixtures/catalog-snapshot.valid.json")), true);
  assert.equal(validate(await loadJson("fixtures/catalog-snapshot.invalid.json")), false);
});
