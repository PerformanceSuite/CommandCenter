import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..', '..');
const EVENTS_BASE = path.join(ROOT, 'snapshots', 'hub', 'events');

function ensureDir(p: string) { fs.mkdirSync(p, { recursive: true }); }

export class MockBus extends EventEmitter {
  private dayDir: string;
  private filePath: string;
  private count = 0;

  constructor() {
    super();
    const now = new Date();
    const ymd = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}`;
    this.dayDir = path.join(EVENTS_BASE, ymd);
    ensureDir(this.dayDir);
    const hh = String(now.getHours()).padStart(2,'0');
    this.filePath = path.join(this.dayDir, `${hh}.events.jsonl`);
  }

  publish(topic: string, payload: unknown) {
    if (!topic.startsWith('tools.')) throw new Error('Topic must start with tools.');
    const evt = { ts: new Date().toISOString(), topic, payload };
    fs.appendFileSync(this.filePath, JSON.stringify(evt) + '\n');
    this.count++;
    this.emit('event', evt);
  }

  stats() {
    return { events: this.count };
  }
}
