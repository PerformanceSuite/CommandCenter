import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const ROOT = path.resolve(process.cwd(), '..');
    const base = path.join(ROOT, 'snapshots', 'hub', 'events');
    const days = fs.readdirSync(base).filter(f => /\d{8}/.test(f)).sort().reverse();
    const items: any[] = [];
    if (days[0]) {
      const dayDir = path.join(base, days[0]);
      const files = fs.readdirSync(dayDir).filter(f => f.endsWith('.jsonl')).sort().reverse();
      if (files[0]) {
        const fp = path.join(dayDir, files[0]);
        const lines = fs.readFileSync(fp, 'utf8').split('\n').filter(Boolean).slice(-100);
        for (const line of lines) items.push(JSON.parse(line));
      }
    }
    return NextResponse.json({ items });
  } catch {
    return NextResponse.json({ items: [] });
  }
}
