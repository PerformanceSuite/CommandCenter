import fs from "fs";
import path from "path";

const HUB_PKG = path.join(process.cwd(), "hub", "package.json");
if (!fs.existsSync(HUB_PKG)) {
  console.error("❌ hub/package.json not found. Run from hub-prototype root.");
  process.exit(1);
}

const raw = fs.readFileSync(HUB_PKG, "utf8");
const pkg = JSON.parse(raw);

pkg.scripts = pkg.scripts || {};

const desired: Record<string,string> = {
  "verify": "bash ../scripts/verify-snapshots.sh",
  "test-events": "tsx ../scripts/test-events.ts",
  "stream-demo": "tsx ../scripts/stream-demo.ts",
  "replay-demo": "tsx ../scripts/replay-demo.ts"
};

let changed = false;
for (const [k, v] of Object.entries(desired)) {
  const key = `hub:${k}`;
  if (pkg.scripts[key] !== v) {
    pkg.scripts[key] = v;
    changed = true;
  }
}

if (changed) {
  fs.writeFileSync(HUB_PKG, JSON.stringify(pkg, null, 2) + "\n", "utf8");
  console.log("✅ Updated hub/package.json with Phase2-3 scripts.");
} else {
  console.log("ℹ️ Scripts already present. No changes made.");
}
