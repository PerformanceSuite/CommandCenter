import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const ROOT = path.resolve(process.cwd(), "..");
    const p = path.join(ROOT, "snapshots", "hub", "project-registry.json");
    const data = JSON.parse(fs.readFileSync(p, "utf8"));
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ projects: [] });
  }
}
