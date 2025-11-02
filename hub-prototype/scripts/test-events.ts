import { mockBus } from "../src/hub/mockBus.js";

mockBus.emit({ type: "project", id: "veria" }, "startup", { msg: "booted" });
mockBus.emit({ type: "tool", id: "graph-service" }, "connected", { status: "ok" });

mockBus.subscribe((e) => console.log("🔁 replay:", e.type, e.origin.id));
mockBus.replay({ type: "project", id: "veria" });
