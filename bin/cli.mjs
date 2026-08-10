#!/usr/bin/env node
/**
 * theainews-skills CLI — install Codex skills from this repository.
 *
 * Usage:
 *   npx -y github:fire3/theainews-skills list
 *   npx -y github:fire3/theainews-skills install [skill...] [--dest <dir>] [--force]
 *
 * With no skill names, `install` installs every skill in skills/.
 */

import { cp, mkdir, readdir, stat } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS_DIR = path.join(ROOT, "skills");

function defaultDest() {
  return process.env.CODEX_HOME
    ? path.join(process.env.CODEX_HOME, "skills")
    : path.join(os.homedir(), ".codex", "skills");
}

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

async function listSkills() {
  const entries = await readdir(SKILLS_DIR, { withFileTypes: true });
  const skills = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (await exists(path.join(SKILLS_DIR, entry.name, "SKILL.md"))) {
      skills.push(entry.name);
    }
  }
  return skills.sort();
}

async function install(names, dest, force) {
  const available = await listSkills();
  if (names.length === 0) names = [...available];

  const missing = names.filter((n) => !available.includes(n));
  if (missing.length > 0) {
    console.error(
      `Unknown skill(s): ${missing.join(", ")}\nAvailable: ${available.join(", ") || "(none)"}`
    );
    process.exitCode = 1;
    return;
  }

  await mkdir(dest, { recursive: true });
  for (const name of names) {
    const target = path.join(dest, name);
    if ((await exists(target)) && !force) {
      console.error(`Already installed: ${target} (use --force to overwrite)`);
      process.exitCode = 1;
      continue;
    }
    await cp(path.join(SKILLS_DIR, name), target, { recursive: true, force: true });
    console.log(`Installed ${name} -> ${target}`);
  }
}

function usage() {
  console.log(`theainews-skills — Codex skill installer

Usage:
  theainews-skills list
  theainews-skills install [skill...] [--dest <dir>] [--force]

Examples:
  theainews-skills list
  theainews-skills install theainews-cover-image
  theainews-skills install --force

Options:
  --dest <dir>  Install into <dir> (default: $CODEX_HOME/skills or ~/.codex/skills)
  --force       Overwrite an existing skill directory
  -h, --help    Show this help`);
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
  usage();
} else {
  const cmd = args[0];
  const rest = args.slice(1);
  const destIdx = rest.indexOf("--dest");
  const dest = destIdx >= 0 ? rest[destIdx + 1] : defaultDest();
  const clean = destIdx >= 0 ? rest.filter((_, i) => i !== destIdx && i !== destIdx + 1) : rest;
  const force = clean.includes("--force");
  const names = clean.filter((a) => a !== "--force");

  if (cmd === "list") {
    const skills = await listSkills();
    console.log(skills.length ? skills.join("\n") : "(no skills)");
  } else if (cmd === "install") {
    if (destIdx >= 0 && !rest[destIdx + 1]) {
      console.error("--dest requires a directory path");
      process.exitCode = 1;
    } else {
      await install(names, dest, force);
    }
  } else {
    console.error(`Unknown command: ${cmd}`);
    usage();
    process.exitCode = 1;
  }
}
