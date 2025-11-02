import { createEventStream } from "../src/hub/eventStreamer.js";

const stream = createEventStream();
stream.on("event", (evt) => console.log("📡 live:", evt.type, evt.origin.id));

stream.start();

setTimeout(() => {
  console.log("⏹ stopping stream...");
  stream.stop();
}, 10000);
