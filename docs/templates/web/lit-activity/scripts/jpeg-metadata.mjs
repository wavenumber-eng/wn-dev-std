import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import { extname, join } from "node:path";

const checkOnly = process.argv.includes("--check");
const targets = process.argv.slice(2).filter((value) => value !== "--check");
if (targets.length === 0) {
  throw new Error("pass at least one JPEG file or directory");
}

const files = [];
for (const target of targets) {
  const targetStat = await stat(target);
  if (targetStat.isDirectory()) {
    for (const name of await readdir(target)) {
      if ([".jpg", ".jpeg"].includes(extname(name).toLowerCase())) {
        files.push(join(target, name));
      }
    }
  } else {
    files.push(target);
  }
}

const offenders = [];
for (const path of files.sort()) {
  const input = await readFile(path);
  const { output, removed } = stripPrivateMetadata(input, path);
  if (removed === 0) {
    continue;
  }
  if (checkOnly) {
    offenders.push(`${path} contains ${removed} EXIF/XMP or Photoshop/IPTC segment(s)`);
  } else {
    await writeFile(path, output);
    process.stdout.write(`${path}: removed ${removed} private metadata segment(s)\n`);
  }
}

if (offenders.length > 0) {
  throw new Error(offenders.join("\n"));
}
if (checkOnly) {
  process.stdout.write(`JPEG metadata: ${files.length} file(s) clean\n`);
}

function stripPrivateMetadata(input, path) {
  if (input[0] !== 0xff || input[1] !== 0xd8) {
    throw new Error(`${path} is not a JPEG file`);
  }
  const chunks = [input.subarray(0, 2)];
  let offset = 2;
  let removed = 0;
  while (offset < input.length) {
    if (input[offset] !== 0xff) {
      throw new Error(`${path} has an invalid marker at byte ${offset}`);
    }
    const start = offset;
    while (input[offset] === 0xff) {
      offset += 1;
    }
    const marker = input[offset];
    offset += 1;
    if (marker === 0xda || marker === 0xd9) {
      chunks.push(input.subarray(start));
      offset = input.length;
      break;
    }
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) {
      chunks.push(input.subarray(start, offset));
      continue;
    }
    const length = input.readUInt16BE(offset);
    const end = offset + length;
    if (end > input.length) {
      throw new Error(`${path} has an invalid segment at byte ${start}`);
    }
    if (marker === 0xe1 || marker === 0xed) {
      removed += 1;
    } else {
      chunks.push(input.subarray(start, end));
    }
    offset = end;
  }
  return { output: Buffer.concat(chunks), removed };
}
