import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import type { ToolManifest, ToolRegistryEntry } from '../types/index.d.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = path.resolve(__dirname, '..', '..');
const TOOLS_DIR = path.join(ROOT, 'tools');
const SNAP_DIR = path.join(ROOT, 'snapshots', 'hub');
const REGISTRY_PATH = path.join(SNAP_DIR, 'tool-registry.json');
const AUDIT_BASE = path.join(SNAP_DIR, 'audit');
const EVENTS_BASE = path.join(SNAP_DIR, 'events');

function ensureDir(p: string) { fs.mkdirSync(p, { recursive: true }); }

function auditLog(message: string) {
  const now = new Date();
  const y = String(now.getFullYear());
  const m = String(now.getMonth()+1).padStart(2,'0');
  const d = String(now.getDate()).padStart(2,'0');
  const dir = path.join(AUDIT_BASE, y, m, d);
  ensureDir(dir);
  fs.appendFileSync(path.join(dir, 'hub.log'), `[${now.toISOString()}] ${message}\n`);
}

export function refreshRegistry(): ToolRegistryEntry[] {
  ensureDir(SNAP_DIR);
  ensureDir(AUDIT_BASE);
  ensureDir(EVENTS_BASE);

  let tools: string[] = [];
  try {
    tools = fs.readdirSync(TOOLS_DIR, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
  } catch {}

  const entries: ToolRegistryEntry[] = [];
  for (const tool of tools) {
    const manifestPath = path.join(TOOLS_DIR, tool, 'manifest.json');
    if (!fs.existsSync(manifestPath)) continue;
    const manifest: ToolManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const entry: ToolRegistryEntry = {
      id: manifest.id || tool,
      version: manifest.version,
      categories: manifest.category || [],
      ports: manifest.ports || {},
      healthUrl: manifest.health?.url,
      endpoints: manifest.endpoints || {},
      discoveredAt: new Date().toISOString()
    };
    entries.push(entry);
  }
  fs.writeFileSync(REGISTRY_PATH, JSON.stringify({ generatedAt: new Date().toISOString(), tools: entries }, null, 2));
  auditLog(`registry.refresh count=${entries.length}`);
  return entries;
}

export function readRegistry(): { generatedAt: string; tools: ToolRegistryEntry[] } {
  if (!fs.existsSync(REGISTRY_PATH)) return { generatedAt: new Date(0).toISOString(), tools: [] };
  const raw = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  return raw;
}

if (process.argv.includes('--refresh')) {
  const out = refreshRegistry();
  console.log(JSON.stringify(out, null, 2));
}
