import fs from 'fs';
import path from 'path';

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'ai', 'recommendations.json');

function safeReadJSON(p: string, fallback: any) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return fallback; }
}

function main() {
  const registry = safeReadJSON(path.join(ROOT, 'snapshots', 'hub', 'tool-registry.json'), { tools: [] });
  const recs: any[] = [];
  for (const t of registry.tools || []) {
    const hasHealth = !!t.healthUrl;
    recs.push({
      tool: t.id,
      recommendation: hasHealth ? 'OK: health endpoint present' : 'Add health endpoint to manifest and tool',
      categories: t.categories || []
    });
  }
  fs.writeFileSync(OUT, JSON.stringify({ generatedAt: new Date().toISOString(), items: recs }, null, 2));
  console.log('wrote', OUT);
}
main();
