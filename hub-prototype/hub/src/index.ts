import Fastify from 'fastify';
import { MockBus } from './mockBus.js';
import { refreshRegistry, readRegistry } from './registry.js';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const fastify = Fastify({ logger: false });
const bus = new MockBus();
const PORT = 5055;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..', '..');
const AUDIT_BASE = path.join(ROOT, 'snapshots', 'hub', 'audit');

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

fastify.post('/rpc', async (req, reply) => {
  const body = req.body as any;
  const { id, method, params } = body || {};
  try {
    if (method === 'bus.publish') {
      const { topic, payload } = params || {};
      bus.publish(topic, payload);
      auditLog(`bus.publish topic=${topic}`);
      return { jsonrpc: '2.0', id, result: { ok: true } };
    }
    if (method === 'bus.health') {
      return { jsonrpc: '2.0', id, result: { ok: true, stats: bus.stats() } };
    }
    if (method === 'registry.refresh') {
      const out = refreshRegistry();
      return { jsonrpc: '2.0', id, result: { count: out.length } };
    }
    if (method === 'registry.read') {
      return { jsonrpc: '2.0', id, result: readRegistry() };
    }
    return { jsonrpc: '2.0', id, error: { code: -32601, message: 'Method not found' } };
  } catch (err: any) {
    return { jsonrpc: '2.0', id, error: { code: -32000, message: err?.message || 'Internal error' } };
  }
});

fastify.get('/health', async () => ({ ok: true, uptime: process.uptime(), stats: bus.stats() }));

fastify.listen({ port: PORT, host: '127.0.0.1' })
  .then(() => {
    auditLog(`hub.start port=${PORT}`);
    console.log(`[hub] JSON-RPC listening on http://127.0.0.1:${PORT}/rpc`);
  })
  .catch(err => { console.error(err); process.exit(1); });

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
