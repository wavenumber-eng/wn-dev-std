import { readdir, readFile } from "node:fs/promises";
import { dirname, extname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = join(root, "src");
const violations = [];
const RAW_DESIGN_UNIT =
  /(?<![\w.-])(?:\d*\.)?\d+(?:px|r?em|ex|ch|cap|ic|r?lh|v[whib]|vmin|vmax|cm|mm|in|pt|pc|q)\b/i;

for (const file of await filesUnder(sourceRoot)) {
  const content = await readFile(file, "utf8");
  const projectPath = relative(root, file).split(sep).join("/");
  const isTypeScript = [".ts", ".tsx"].includes(extname(file));
  if (isTypeScript && projectPath.startsWith("src/activity/")) {
    checkActivityKernel(projectPath, content);
  }
  if (isTypeScript) {
    checkTransportOwnership(projectPath, content);
    checkFeatureImports(file, projectPath, content);
    checkInlineStyles(projectPath, content);
  }
  if (extname(file) === ".css" && projectPath !== "src/theme/primitives.css") {
    checkDesignTokens(projectPath, content);
  }
}

if (violations.length > 0) {
  process.stderr.write(`${violations.map((value) => `- ${value}`).join("\n")}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write("Architecture boundaries: OK\n");
}

async function filesUnder(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      result.push(...(await filesUnder(path)));
    } else {
      result.push(path);
    }
  }
  return result;
}

function checkActivityKernel(path, content) {
  const forbidden = ["lit", "../features", "../transport", "../shell", "window.", "document."];
  for (const token of forbidden) {
    if (content.includes(token)) {
      violations.push(`${path}: activity kernel contains forbidden dependency "${token}"`);
    }
  }
}

function checkTransportOwnership(path, content) {
  if (path.startsWith("src/transport/")) {
    return;
  }
  for (const api of ["fetch(", "new WebSocket(", "new EventSource("]) {
    if (content.includes(api)) {
      violations.push(`${path}: protocol primitive "${api}" belongs in src/transport`);
    }
  }
}

function checkInlineStyles(path, content) {
  let index = 0;
  for (const match of content.matchAll(/\bcss\s*`([\s\S]*?)`/g)) {
    index += 1;
    checkDesignTokens(`${path} Lit css template ${index}`, match[1] ?? "");
  }
}

function checkFeatureImports(file, path, content) {
  const featureMatch = path.match(/^src\/features\/([^/]+)\//);
  if (featureMatch === null) {
    return;
  }
  const currentFeature = featureMatch[1];
  for (const match of content.matchAll(/from\s+["']([^"']+)["']/g)) {
    const specifier = match[1];
    if (specifier === undefined || !specifier.startsWith(".")) {
      continue;
    }
    const target = resolve(dirname(file), specifier);
    const targetPath = relative(sourceRoot, target).split(sep).join("/");
    const targetMatch = targetPath.match(/^features\/([^/]+)(?:\/(.*))?$/);
    if (targetMatch === null || targetMatch[1] === currentFeature) {
      continue;
    }
    if (targetMatch[2] !== undefined) {
      violations.push(`${path}: cross-feature imports must use the target feature index`);
    }
  }
}

function checkDesignTokens(path, content) {
  const lines = content.split(/\r?\n/);
  const excluded = new Set();
  for (const [index, line] of lines.entries()) {
    const marker = "design-literal-exception:";
    if (!line.includes(marker)) {
      continue;
    }
    const reason =
      line
        .split(marker)[1]
        ?.replace(/[*/#\s]+$/g, "")
        .trim() ?? "";
    if (reason === "") {
      violations.push(`${path}: design-literal exceptions require a rationale`);
      continue;
    }
    excluded.add(index);
    excluded.add(index + 1);
    if (index > 0 && lines[index - 1]?.includes(":")) {
      excluded.add(index - 1);
    }
  }
  const auditedContent = lines.filter((_line, index) => !excluded.has(index)).join("\n");
  const declarations = auditedContent.matchAll(
    /(?<property>-{0,2}[a-z][\w-]*)\s*:\s*(?<value>[^;{}]+?)\s*(?:;|(?=\}))/gi,
  );
  for (const match of declarations) {
    const property = match.groups?.property?.toLowerCase();
    const value = match.groups?.value?.trim();
    if (property === undefined || value === undefined || property.startsWith("--")) {
      continue;
    }
    const reason = rawDesignLiteral(property, value);
    if (reason !== undefined) {
      violations.push(`${path}: ${property} contains ${reason}`);
    }
  }
}

function rawDesignLiteral(property, value) {
  if (isColorProperty(property) && hasRawColor(value)) {
    return "a raw color outside the token layer";
  }
  if (property === "font-family" && !isGovernedValue(value)) {
    return "a raw font family outside the token layer";
  }
  if (["box-shadow", "text-shadow"].includes(property) && !isGovernedValue(value)) {
    return "a raw shadow outside the token layer";
  }
  if (property === "z-index" && hasNonzeroNumber(value)) {
    return "a raw layer value outside the token layer";
  }
  if (
    (property.startsWith("animation") || property.startsWith("transition")) &&
    /(?<![\w.-])(?:\d*\.)?\d+(?:ms|s)\b/i.test(value)
  ) {
    return "a raw motion duration outside the token layer";
  }
  if (isDimensionProperty(property) && RAW_DESIGN_UNIT.test(value)) {
    return "a raw design dimension outside the token layer";
  }
  return undefined;
}

function isColorProperty(property) {
  const direct = new Set([
    "accent-color",
    "background",
    "background-color",
    "border-color",
    "caret-color",
    "color",
    "column-rule-color",
    "fill",
    "outline",
    "outline-color",
    "stroke",
    "text-decoration",
    "text-decoration-color",
  ]);
  const borderShorthand =
    /^border(?:-(?:top|right|bottom|left|block(?:-(?:start|end))?|inline(?:-(?:start|end))?))?$/.test(
      property,
    );
  return direct.has(property) || borderShorthand || /(?:-color|-fill|-stroke)$/.test(property);
}

function hasRawColor(value) {
  if (/#[0-9a-f]{3,8}\b|\b(?:rgb|hsl|hwb|lab|lch|oklab|oklch|color(?:-mix)?)a?\s*\(/i.test(value)) {
    return true;
  }
  const safeWords = new Set([
    "auto",
    "currentcolor",
    "dashed",
    "dotted",
    "double",
    "groove",
    "hidden",
    "inherit",
    "initial",
    "inset",
    "none",
    "outset",
    "revert",
    "revert-layer",
    "ridge",
    "solid",
    "transparent",
    "unset",
  ]);
  const withoutTokens = value
    .replace(/var\([^)]*\)/gi, "")
    .replace(/\b(?:linear-gradient|radial-gradient|conic-gradient|url|image-set)\s*\(/gi, "(");
  return [...withoutTokens.toLowerCase().matchAll(/[a-z][a-z-]*/g)].some(
    (match) => match[0] !== undefined && !safeWords.has(match[0]),
  );
}

function isGovernedValue(value) {
  const normalized = value.trim().toLowerCase();
  return (
    normalized.startsWith("var(") ||
    ["inherit", "initial", "none", "revert", "revert-layer", "unset"].includes(normalized)
  );
}

function hasNonzeroNumber(value) {
  const normalized = value.trim().toLowerCase();
  if (
    normalized.startsWith("var(") ||
    ["auto", "inherit", "initial", "unset"].includes(normalized)
  ) {
    return false;
  }
  return [...normalized.matchAll(/-?(?:\d*\.)?\d+/g)].some(
    (match) => Number.parseFloat(match[0]) !== 0,
  );
}

function isDimensionProperty(property) {
  return [
    "border-",
    "bottom",
    "column-gap",
    "column-width",
    "flex-basis",
    "font-size",
    "gap",
    "height",
    "inset",
    "left",
    "letter-spacing",
    "margin",
    "max-height",
    "max-width",
    "min-height",
    "min-width",
    "outline-offset",
    "outline-width",
    "padding",
    "right",
    "row-gap",
    "top",
    "width",
  ].some((prefix) => property.startsWith(prefix));
}
