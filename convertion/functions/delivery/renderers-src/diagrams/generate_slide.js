#!/usr/bin/env node
/**
 * generate_slide.js — Mermaid source -> SVG or PNG via @mermaid-js/mermaid-cli
 * Usage: node generate_slide.js <data.json> <out.svg|out.png>
 * data.json: { "mermaid": "...", "theme": "neutral", "background": "white", "width": 1400 }
 * Runs the bundled Chromium with --no-sandbox (container), no network access needed.
 */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const [dataPath, outPath] = process.argv.slice(2);
if (!dataPath || !outPath) { console.error("usage: render_mermaid.js <data.json> <out.svg|png>"); process.exit(2); }
const d = JSON.parse(fs.readFileSync(dataPath, "utf8"));
if (!d.mermaid || typeof d.mermaid !== "string") { console.error("data.mermaid missing"); process.exit(2); }

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mmd-"));
const src = path.join(tmp, "diagram.mmd");
fs.writeFileSync(src, d.mermaid, "utf8");
const cfg = path.join(tmp, "puppeteer.json");
fs.writeFileSync(cfg, JSON.stringify({ args: ["--no-sandbox", "--disable-setuid-sandbox"] }));
const mmdc = path.join(__dirname, "node_modules", ".bin", "mmdc");
const args = ["-i", src, "-o", outPath, "-t", d.theme || "neutral", "-b", d.background || "white",
              "-w", String(d.width || 1400), "-p", cfg];
execFileSync(mmdc, args, { stdio: "inherit" });
fs.rmSync(tmp, { recursive: true, force: true });
console.log("OK", outPath);
