#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { createEventStream } from "./eventStreamer.js";

const ROOT = path.resolve(process.cwd(), "..");
const EVENTS_PATH = path.join(ROOT, "snapshots", "hub", "events.log");

function parseArgs(argv: string[]) {
  const args: Record<string,string|boolean> = {};
  for (let i=0; i<argv.length; i++) {
    const a = argv[i];
    if (a === "--project" || a === "--tool") {
      args[a.slice(2)] = argv[i+1];
      i++;
    } else if (a === "--replay-only") {
      args.replayOnly = true;
    }
  }
  return args;
}

function filterLine(line: string, args: Record<string,string|boolean>) {
  try {
    const evt = JSON.parse(line);
    if (args.project && evt.origin?.type === "project" && evt.origin?.id === args.project) return true;
    if (args.tool && evt.origin?.type === "tool" && evt.origin?.id === args.tool) return true;
    if (!args.project && !args.tool) return true;
  } catch {}
  return false;
}

function replayExisting(args: Record<string,string|boolean>) {
  if (!fs.existsSync(EVENTS_PATH)) {
    console.error(`No events log at ${EVENTS_PATH}`);
    return;
  }
  const txt = fs.readFileSync(EVENTS_PATH, "utf8");
  if (!txt.trim()) return;
  txt.split("\n").forEach(l => {
    const s = l.trim();
    if (s && filterLine(s, args)) console.log(s);
  });
}

function tail(args: Record<string,string|boolean>) {
  const stream = createEventStream();
  stream.on("event", (evt: any) => {
    if (!args.project && !args.tool) {
      console.log(JSON.stringify(evt));
      return;
    }
    if (args.project && evt.origin?.type === "project" && evt.origin?.id === args.project) {
      console.log(JSON.stringify(evt));
    }
    if (args.tool && evt.origin?.type === "tool" && evt.origin?.id === args.tool) {
      console.log(JSON.stringify(evt));
    }
  });
  stream.start();
}

function main() {
  const cmd = process.argv[2] || "events";
  const args = parseArgs(process.argv.slice(3));

  if (cmd === "events") {
    console.log(`Tailing events from ${EVENTS_PATH}`);
    replayExisting(args);
    if (!args.replayOnly) {
      tail(args);
    }
  } else {
    console.error(`Unknown command: ${cmd}`);
    process.exit(1);
  }
}

main();
