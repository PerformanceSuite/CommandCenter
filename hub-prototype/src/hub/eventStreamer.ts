import fs from "fs";
import { EventEmitter } from "events";
import path from "path";
import { HubEvent } from "./mockBus.js";

const ROOT = path.resolve(process.cwd(), "..");
const EVENTS_PATH = path.join(ROOT, "snapshots", "hub", "events.log");

export function createEventStream() {
  const emitter = new EventEmitter();
  let lastSize = 0;
  let watcher: fs.FSWatcher | null = null;

  function start() {
    if (!fs.existsSync(EVENTS_PATH)) {
      fs.mkdirSync(path.dirname(EVENTS_PATH), { recursive: true });
      fs.writeFileSync(EVENTS_PATH, "");
    }
    lastSize = fs.statSync(EVENTS_PATH).size;

    watcher = fs.watch(EVENTS_PATH, () => {
      const size = fs.statSync(EVENTS_PATH).size;
      if (size > lastSize) {
        const stream = fs.createReadStream(EVENTS_PATH, {
          start: lastSize,
          end: size,
          encoding: "utf8",
        });
        stream.on("data", (chunk) => {
          chunk.split("\n").forEach((line) => {
            const s = line.trim();
            if (s) {
              try {
                const evt: HubEvent = JSON.parse(s);
                emitter.emit("event", evt);
              } catch { /* swallow */ }
            }
          });
        });
        lastSize = size;
      }
    });
  }

  function stop() {
    if (watcher) watcher.close();
  }

  return { start, stop, on: emitter.on.bind(emitter) };
}

export function replayRange(sinceISO: string) {
  if (!fs.existsSync(EVENTS_PATH)) return;
  const since = new Date(sinceISO).getTime();
  const txt = fs.readFileSync(EVENTS_PATH, "utf8").trim();
  if (!txt) return;
  for (const line of txt.split("\n")) {
    const evt = JSON.parse(line) as HubEvent;
    if (new Date(evt.timestamp).getTime() >= since) {
      console.log("⏮ replay:", evt.type, evt.origin.id);
    }
  }
}
