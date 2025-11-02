#!/usr/bin/env node
// Lightweight orchestrator: walks tools/* and, if a Daggerfile exists, print planned build.
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const toolsDir = path.join(ROOT, 'tools');
let tools = [];
try {
  tools = fs.readdirSync(toolsDir, { withFileTypes: true }).filter(d => d.isDirectory()).map(d => d.name);
} catch {}
for (const t of tools) {
  const daggerfile = path.join(toolsDir, t, 'Daggerfile');
  if (fs.existsSync(daggerfile)) {
    console.log(`[dagger] would build ${t} using ${daggerfile}`);
  } else {
    console.log(`[dagger] skip ${t} (no Daggerfile)`);
  }
}
process.exit(0);
