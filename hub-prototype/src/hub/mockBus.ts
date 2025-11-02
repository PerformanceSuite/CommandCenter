import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";

const ROOT = path.resolve(process.cwd(), "..");
const SNAP_DIR = path.join(ROOT, "snapshots", "hub");
const EVENTS_PATH = path.join(SNAP_DIR, "events.log");

export type EventOrigin = { type: "tool" | "project"; id: string };

export interface HubEvent {
  id: string;
  correlationId: string;
  origin: EventOrigin;
  timestamp: string;
  type: string;
  payload: any;
}

export class MockBus {
  private subs: ((e: HubEvent) => void)[] = [];
  constructor() { fs.mkdirSync(SNAP_DIR, { recursive: true }); }

  emit(origin: EventOrigin, type: string, payload: any, correlationId?: string) {
    const evt: HubEvent = {
      id: randomUUID(),
      correlationId: correlationId || randomUUID(),
      origin,
      timestamp: new Date().toISOString(),
      type,
      payload,
    };
    fs.appendFileSync(EVENTS_PATH, JSON.stringify(evt) + "\n");
    this.subs.forEach(fn => fn(evt));
  }

  subscribe(cb: (e: HubEvent) => void) { this.subs.push(cb); }

  replay(filter?: Partial<EventOrigin>) {
    if (!fs.existsSync(EVENTS_PATH)) return;
    const content = fs.readFileSync(EVENTS_PATH, "utf8").trim();
    if (!content) return;
    for (const line of content.split("\n")) {
      const evt = JSON.parse(line) as HubEvent;
      if (!filter || (filter.type === evt.origin.type && filter.id === evt.origin.id)) {
        this.subs.forEach(fn => fn(evt));
      }
    }
  }
}

export const mockBus = new MockBus();
