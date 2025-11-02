import { replayRange } from "../src/hub/eventStreamer.js";

// Replay events from the last minute
const since = new Date(Date.now() - 60_000).toISOString();
replayRange(since);
