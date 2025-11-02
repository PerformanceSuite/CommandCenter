import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { refreshRegistry, readRegistry } from "./registry.js";
import { refreshProjects, readProjects } from "./projects.js";

// Fix for ESM (__dirname not defined)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = path.resolve(__dirname, "..", "..");
const SNAP_DIR = path.join(ROOT, "snapshots", "hub");
const EVENTS_PATH = path.join(SNAP_DIR, "events.log");

function usage() {
  console.log(`
Usage:
  pnpm hub:list              - list registered tools
  pnpm hub:open <id>         - show endpoint info
  pnpm hub:events            - tail live Mesh-Bus feed
  pnpm hub:projects          - list registered project instances
  pnpm hub:projects:refresh  - rescan projects directory
`);
}

// -------------------------
// Tools registry commands
// -------------------------

function listTools() {
  const reg = readRegistry();
  if (!reg.tools?.length) {
    console.log("No tools registered. Run: pnpm hub:refresh");
    return;
  }
  console.log(JSON.stringify(reg.tools, null, 2));
}

function openTool(id: string) {
  const reg = readRegistry();
  const found = reg.tools.find((t: any) => t.id === id);
  if (!found) {
    console.error(`Tool '${id}' not found.`);
    process.exit(1);
  }
  console.log(JSON.stringify(found, null, 2));
}

function tailEvents() {
  console.log(`Tailing events from ${EVENTS_PATH}`);
  fs.watchFile(EVENTS_PATH, { interval: 1000 }, () => {
    const data = fs.readFileSync(EVENTS_PATH, "utf8");
    const lines = data.trim().split("\n").slice(-10);
    console.clear();
    console.log(lines.join("\n"));
  });
}

// -------------------------
// Project registry commands
// -------------------------

function listProjects() {
  const reg = readProjects();
  if (!reg.projects.length) {
    console.log("No projects found. Run: pnpm hub:projects:refresh");
    return;
  }
  for (const p of reg.projects) {
    console.log(`${p.instanceId} (${p.projectId}) env=${p.env} tools=[${(p.tools || []).join(",")}]`);
  }
}

function refreshAllProjects() {
  const out = refreshProjects();
  console.log(`Refreshed ${out.length} project instances`);
}

// -------------------------
// Command router
// -------------------------

const cmd = process.argv[2];
if (!cmd) {
  usage();
  process.exit(0);
}

switch (cmd) {
  case "list":
    listTools();
    break;
  case "open":
    openTool(process.argv[3]);
    break;
  case "events":
    tailEvents();
    break;
  case "projects":
    listProjects();
    break;
  case "projects:refresh":
    refreshAllProjects();
    break;
  default:
    usage();
    break;
}

