import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

export interface ProjectInstance {
  projectId: string;
  instanceId: string;
  name?: string;
  owner?: string;
  env?: string;
  rag?: { corpusDir?: string; indexDir?: string };
  tools?: string[];
  endpoints?: Record<string, string>;
  health?: { url?: string };
  discoveredAt: string;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..", "..");
const PROJECTS_DIR = path.join(ROOT, "projects");
const SNAP_DIR = path.join(ROOT, "snapshots", "hub");
const REGISTRY_PATH = path.join(SNAP_DIR, "project-registry.json");

function ensureDir(p: string) {
  fs.mkdirSync(p, { recursive: true });
}

export function refreshProjects(): ProjectInstance[] {
  ensureDir(PROJECTS_DIR);
  ensureDir(SNAP_DIR);

  const dirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  const entries: ProjectInstance[] = [];
  for (const d of dirs) {
    const f = path.join(PROJECTS_DIR, d, "project.json");
    if (!fs.existsSync(f)) continue;
    const proj = JSON.parse(fs.readFileSync(f, "utf8"));
    proj.discoveredAt = new Date().toISOString();
    entries.push(proj);
  }

  const out = { generatedAt: new Date().toISOString(), projects: entries };
  fs.writeFileSync(REGISTRY_PATH, JSON.stringify(out, null, 2));
  console.log(`Refreshed ${entries.length} project instances`);
  return entries;
}

export function readProjects(): { generatedAt: string; projects: ProjectInstance[] } {
  if (!fs.existsSync(REGISTRY_PATH))
    return { generatedAt: new Date(0).toISOString(), projects: [] };
  return JSON.parse(fs.readFileSync(REGISTRY_PATH, "utf8"));
}

if (process.argv.includes("--refresh")) refreshProjects();
