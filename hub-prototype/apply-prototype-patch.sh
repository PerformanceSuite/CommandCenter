#!/usr/bin/env bash
set -e

echo "🔧 Applying Project Registry + MRKTZR integration patch to hub-prototype..."

# --- Paths ---
ROOT="$(pwd)"
HUB_SRC="$ROOT/hub/src"
HUB_CONSOLE="$ROOT/hub-console"

# --------------------------------------------------------------------
# 1. Create new projects.ts file
# --------------------------------------------------------------------
cat > "$HUB_SRC/projects.ts" <<'TS'
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
TS

# --------------------------------------------------------------------
# 2. Patch index.ts to include project registry RPC methods
# --------------------------------------------------------------------
echo "🧩 Patching hub/src/index.ts ..."
grep -q "projects.refresh" "$HUB_SRC/index.ts" || \
cat >> "$HUB_SRC/index.ts" <<'PATCH'

/* --- Added Project Registry support --- */
import { refreshProjects, readProjects } from "./projects.js";
/* --- end import --- */

// Extend RPC handler
// (Append inside the same handler as other registry methods)
fastify.post('/rpc', async (req, reply) => {
  const body = req.body as any;
  const { id, method, params } = body || {};
  try {
    if (method === 'projects.refresh') {
      const out = refreshProjects();
      return { jsonrpc: '2.0', id, result: { count: out.length } };
    }
    if (method === 'projects.read') {
      return { jsonrpc: '2.0', id, result: readProjects() };
    }
  } catch (err: any) {
    return { jsonrpc: '2.0', id, error: { code: -32000, message: err?.message || 'Internal error' } };
  }
});
PATCH

# --------------------------------------------------------------------
# 3. Patch cli.ts to add projects commands
# --------------------------------------------------------------------
echo "🧩 Patching hub/src/cli.ts ..."
grep -q "projects" "$HUB_SRC/cli.ts" || \
cat >> "$HUB_SRC/cli.ts" <<'PATCH'

import { refreshProjects, readProjects } from "./projects.js";

async function listProjects() {
  const reg = readProjects();
  if (!reg.projects.length) {
    console.log("No projects found. Run: pnpm hub:projects:refresh");
    return;
  }
  for (const p of reg.projects) {
    console.log(`${p.instanceId} (${p.projectId}) env=${p.env} tools=[${(p.tools||[]).join(",")}]`);
  }
}

const cmd = process.argv[2];
if (cmd === "projects") listProjects();
else if (cmd === "projects:refresh") refreshProjects();
PATCH

# --------------------------------------------------------------------
# 4. Add new API route in console
# --------------------------------------------------------------------
echo "🧩 Creating hub-console/app/api/projects/route.ts ..."
mkdir -p "$HUB_CONSOLE/app/api/projects"
cat > "$HUB_CONSOLE/app/api/projects/route.ts" <<'TS'
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const ROOT = path.resolve(process.cwd(), "..");
    const p = path.join(ROOT, "snapshots", "hub", "project-registry.json");
    const data = JSON.parse(fs.readFileSync(p, "utf8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ projects: [] });
  }
}
TS

# --------------------------------------------------------------------
# 5. Patch UI page.tsx to show projects
# --------------------------------------------------------------------
echo "🧩 Patching hub-console/app/page.tsx ..."
grep -q "Project Instances" "$HUB_CONSOLE/app/page.tsx" || \
cat >> "$HUB_CONSOLE/app/page.tsx" <<'PATCH'

const projects = await fetchJSON('/api/projects');

<section>
  <h2 className="text-xl font-medium mb-2">Project Instances</h2>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
    {(projects.projects || []).map((p: any) => (
      <div key={p.instanceId} className="rounded-2xl p-4 bg-neutral-900 border border-neutral-800">
        <div className="font-semibold">{p.name || p.instanceId}</div>
        <div className="text-xs text-neutral-400">{p.projectId} • env={p.env}</div>
        <div className="text-xs text-neutral-400 mt-1">
          tools: {(p.tools||[]).join(", ")}
        </div>
      </div>
    ))}
  </div>
</section>
PATCH

# --------------------------------------------------------------------
# 6. Create example MRKTZR + project scaffolding
# --------------------------------------------------------------------
echo "🧩 Creating MRKTZR tool and example projects ..."
mkdir -p tools/mrktzr projects/veria-dev projects/mrktzr-cpa-demo

cat > tools/mrktzr/manifest.json <<'JSON'
{
  "id": "mrktzr",
  "name": "MRKTZR (Integrated)",
  "version": "0.1.0",
  "category": ["intel", "outreach"],
  "ports": { "api": 8181 },
  "health": { "url": "http://127.0.0.1:8181/health" },
  "endpoints": { "api": "http://127.0.0.1:8181" }
}
JSON

cat > projects/veria-dev/project.json <<'JSON'
{
  "projectId": "veria",
  "instanceId": "veria-dev",
  "name": "Veria (Dev)",
  "owner": "commandcenter",
  "env": "dev",
  "rag": { "corpusDir": "../../Projects/Veria/docs", "indexDir": "rag/index" },
  "tools": ["veria"],
  "endpoints": { "api": "http://127.0.0.1:8082" },
  "health": { "url": "http://127.0.0.1:8082/health" },
  "discoveredAt": ""
}
JSON

cat > projects/mrktzr-cpa-demo/project.json <<'JSON'
{
  "projectId": "mrktzr",
  "instanceId": "mrktzr-cpa-demo",
  "name": "MRKTZR (CPA Demo)",
  "owner": "commandcenter",
  "env": "demo",
  "rag": { "corpusDir": "../../Projects/MRKTZR/docs", "indexDir": "rag/index" },
  "tools": ["mrktzr"],
  "endpoints": {},
  "discoveredAt": ""
}
JSON

echo "✅ Patch applied successfully!"
echo ""
echo "Next steps:"
echo "1️⃣  pnpm hub:refresh"
echo "2️⃣  pnpm hub:projects:refresh"
echo "3️⃣  pnpm hub:projects"
echo "Then open the console (pnpm console:dev) and you should see both Tools and Project Instances listed."

