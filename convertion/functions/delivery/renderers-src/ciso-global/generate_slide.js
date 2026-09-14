#!/usr/bin/env node
/* Global CISO Report — 9-slide PPTX renderer (requirement d).
 * Usage: node generate_slide.js <data.json> <out.pptx>
 * Input: ciso_global_deck.schema.json contract (verified + approved).
 * Brand: Euronext InfoSec house style — teal RGB(0,141,127), Verdana,
 * risk bands High>=7.0 red / Medium>=4.0 amber / Low green.
 */
"use strict";
const fs = require("fs");
const PptxGenJS = require("pptxgenjs");

const [, , dataPath, outPath] = process.argv;
const d = JSON.parse(fs.readFileSync(dataPath, "utf8"));

const TEAL = "008D7F", DARK = "1A1A1A", GREY = "555555";
const BAND = { red: "B00020", amber: "C99A06", green: "2E7D32" };
const scoreColor = (s) => (s >= 7.0 ? BAND.red : s >= 4.0 ? BAND.amber : BAND.green);
const F = { fontFace: "Verdana" };

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

function slide(title) {
  const s = pptx.addSlide();
  s.addShape("rect", { x: 0, y: 0, w: 13.33, h: 0.75, fill: { color: TEAL } });
  s.addText(title, { x: 0.3, y: 0.05, w: 10.5, h: 0.65, ...F, fontSize: 20, bold: true, color: "FFFFFF" });
  s.addText(d.meta.classification || "Euronext Internal — CISO",
    { x: 10.6, y: 0.2, w: 2.6, h: 0.4, ...F, fontSize: 8, color: "FFFFFF", align: "right" });
  return s;
}
function tbl(s, rows, opts) {
  s.addTable(rows, Object.assign({ x: 0.3, y: 1.0, w: 12.7, ...F, fontSize: 11,
    border: { type: "solid", color: "CCCCCC", pt: 0.5 }, color: DARK,
    fill: { color: "FFFFFF" }, autoPage: true }, opts));
}
const HDR = { bold: true, color: "FFFFFF", fill: { color: TEAL } };

// 1 — Cover
{
  const s = pptx.addSlide();
  s.background = { color: TEAL };
  s.addText("InfoSec Assessment", { x: 0.8, y: 2.0, w: 11.7, h: 0.8, ...F, fontSize: 30, color: "FFFFFF" });
  s.addText(`${d.meta.supplier} / ${d.meta.service}`,
    { x: 0.8, y: 2.9, w: 11.7, h: 1.0, ...F, fontSize: 40, bold: true, color: "FFFFFF" });
  s.addText([
    { text: `Assessment: ${d.meta.assessment_id}  (${d.meta.assessment_date})\n`, options: {} },
    { text: `Report date: ${d.meta.report_date}   Criticality: ${d.meta.criticality || "TO CONFIRM"}\n`, options: {} },
    { text: d.meta.classification || "Euronext Internal — CISO", options: { bold: true } },
  ], { x: 0.8, y: 4.3, w: 11.7, h: 1.5, ...F, fontSize: 14, color: "FFFFFF" });
}

// 2 — Service & supplier identification
{
  const s = slide("Service & Supplier Identification");
  tbl(s, [
    [{ text: "ENX Contract Owner", options: HDR }, { text: `${d.contract_owner.name} — ${d.contract_owner.entity}${d.contract_owner.role ? " (" + d.contract_owner.role + ")" : ""}` }],
    [{ text: "Identification source", options: HDR }, { text: d.contract_owner.source || "OneTrust assessment" }],
    [{ text: "Supplier legal entity", options: HDR }, { text: d.supplier_description.profile.split(".")[0] }],
    [{ text: "Criticality", options: HDR }, { text: d.meta.criticality || "TO CONFIRM" }],
    [{ text: "Assessment scope", options: HDR }, { text: d.service_description.summary }],
  ], { colW: [3.2, 9.5] });
}

// 3 — ENX entities
{
  const s = slide("ENX Companies Using / Impacted by the Service");
  const rows = [[
    { text: "Euronext entity", options: HDR }, { text: "Usage", options: HDR }, { text: "Data types involved", options: HDR }]];
  d.enx_entities.forEach(e => rows.push([{ text: e.entity }, { text: e.usage }, { text: e.data_types || "—" }]));
  tbl(s, rows, { colW: [4.5, 2.2, 6.0] });
}

// 4 — Service description
{
  const s = slide("Service Description");
  tbl(s, [
    [{ text: "Service", options: HDR }, { text: d.service_description.summary }],
    [{ text: "Delivery model", options: HDR }, { text: d.service_description.delivery_model }],
    [{ text: "Data processed", options: HDR }, { text: d.service_description.data_processed || "—" }],
    [{ text: "Connectivity to Euronext", options: HDR }, { text: d.service_description.connectivity || "—" }],
  ], { colW: [3.2, 9.5] });
}

// 5 — Supplier description
{
  const s = slide("Supplier Description");
  tbl(s, [
    [{ text: "Profile", options: HDR }, { text: d.supplier_description.profile }],
    [{ text: "Certifications (as claimed)", options: HDR }, { text: (d.supplier_description.certifications || []).join(", ") || "None stated" }],
    [{ text: "Sub-outsourcing", options: HDR }, { text: d.supplier_description.sub_outsourcing || "None stated" }],
  ], { colW: [3.2, 9.5] });
}

// 6 — Executive risk & controls resume
{
  const s = slide("Executive Risk & Controls Resume");
  s.addText(d.risk_resume.posture_bullets.map(b => ({ text: b, options: { bullet: true } })),
    { x: 0.3, y: 0.95, w: 7.2, h: 3.0, ...F, fontSize: 13, color: DARK });
  const rc = d.risk_resume.risk_counts || {};
  [["High", rc.high, BAND.red], ["Medium", rc.medium, BAND.amber], ["Low", rc.low, BAND.green]]
    .forEach(([lbl, n, c], i) => {
      s.addShape("rect", { x: 7.9 + i * 1.75, y: 1.0, w: 1.6, h: 1.2, fill: { color: c } });
      s.addText(`${n ?? 0}\n${lbl}`, { x: 7.9 + i * 1.75, y: 1.0, w: 1.6, h: 1.2, ...F, fontSize: 14, bold: true, color: "FFFFFF", align: "center" });
    });
  const rows = [[{ text: "Domain", options: HDR }, { text: "Implemented", options: HDR }, { text: "Partial", options: HDR }, { text: "Missing", options: HDR }]];
  (d.risk_resume.controls_status || []).forEach(c =>
    rows.push([{ text: c.domain }, { text: String(c.implemented) }, { text: String(c.partial) }, { text: String(c.missing) }]));
  tbl(s, rows, { y: 4.1, fontSize: 10, colW: [5.5, 2.4, 2.4, 2.4] });
}

// 7 — Exposure diagram (internal | service | external)
{
  const s = slide("Euronext Risk Surface Exposure");
  s.addText("INTERNAL SURFACE", { x: 0.4, y: 0.95, w: 5.0, h: 0.4, ...F, fontSize: 12, bold: true, color: GREY });
  s.addText("EXTERNAL SURFACE", { x: 7.9, y: 0.95, w: 5.0, h: 0.4, ...F, fontSize: 12, bold: true, color: GREY, align: "right" });
  s.addShape("roundRect", { x: 5.6, y: 3.1, w: 2.1, h: 1.2, fill: { color: TEAL } });
  s.addText(d.meta.service, { x: 5.6, y: 3.1, w: 2.1, h: 1.2, ...F, fontSize: 11, bold: true, color: "FFFFFF", align: "center" });
  const draw = (nodes, xBox, xLineFrom, xLineTo) => nodes.slice(0, 6).forEach((n, i) => {
    const y = 1.4 + i * 0.95;
    // connector from the node's mid-height (y + 0.35) to the service box centre (y = 3.7);
    // pptxgenjs lines need a non-negative h, so flip vertically when the node sits below the box
    const yFrom = y + 0.35, yTo = 3.7;
    s.addShape("line", { x: xLineFrom, y: Math.min(yFrom, yTo), w: xLineTo - xLineFrom, h: Math.abs(yTo - yFrom),
      flipV: yFrom > yTo, line: { color: "AAAAAA", width: 1 } });
    s.addShape("roundRect", { x: xBox, y, w: 4.4, h: 0.7, fill: { color: "FFFFFF" }, line: { color: BAND[n.risk] || GREY, width: 2.5 } });
    s.addText(`${n.node}${n.note ? " — " + n.note : ""}`,
      { x: xBox + 0.1, y, w: 4.2, h: 0.7, ...F, fontSize: 9.5, color: DARK, align: "left", valign: "middle" });
    s.addShape("ellipse", { x: xBox + 4.05, y: y + 0.2, w: 0.28, h: 0.28, fill: { color: BAND[n.risk] || GREY } });
  });
  draw(d.exposure.internal, 0.4, 4.8, 5.6);
  draw(d.exposure.external, 8.5, 7.7, 8.5);
  s.addText("● red = High   ● amber = Medium   ● green = Low  (bands: High ≥7.0, Medium ≥4.0)",
    { x: 0.4, y: 7.05, w: 12.5, h: 0.35, ...F, fontSize: 9, color: GREY });
}

// 8 — ICT risk scores
{
  const s = slide("Overall ICT Risk Scores");
  const gauge = (label, val, x) => {
    s.addText(label, { x, y: 1.4, w: 5.0, h: 0.5, ...F, fontSize: 16, bold: true, color: DARK, align: "center" });
    s.addShape("rect", { x: x + 0.5, y: 2.2, w: 4.0, h: 0.6, fill: { color: "EEEEEE" } });
    s.addShape("rect", { x: x + 0.5, y: 2.2, w: Math.max(0.05, 4.0 * (val / 10)), h: 0.6, fill: { color: scoreColor(val) } });
    s.addText(val.toFixed(1) + " / 10", { x, y: 3.0, w: 5.0, h: 0.9, ...F, fontSize: 34, bold: true, color: scoreColor(val), align: "center" });
  };
  gauge("ICT Inherent Risk", d.scores.inherent, 1.1);
  gauge("ICT Residual Risk", d.scores.residual, 7.2);
  s.addText(`Risk reduction achieved by verified controls: ${(d.scores.inherent - d.scores.residual).toFixed(1)} points`,
    { x: 1.1, y: 4.4, w: 11.1, h: 0.5, ...F, fontSize: 13, color: DARK, align: "center" });
  if (d.scores.driver_note)
    s.addText(d.scores.driver_note, { x: 1.1, y: 5.1, w: 11.1, h: 1.2, ...F, fontSize: 12, italic: true, color: GREY, align: "center" });
}

// 9 — ENX controls & actions to the Contract Owner
{
  const s = slide("Euronext Controls & Actions — Owner: " + d.contract_owner.name);
  const rows = [[
    { text: "ID", options: HDR }, { text: "Euronext control / action", options: HDR },
    { text: "Priority", options: HDR }, { text: "Target", options: HDR }, { text: "Owner", options: HDR }]];
  d.enx_actions.forEach(a => rows.push([
    { text: a.id }, { text: a.action },
    { text: a.priority, options: { bold: true, color: a.priority === "High" ? BAND.red : a.priority === "Medium" ? BAND.amber : BAND.green } },
    { text: a.target_date || "TBD" }, { text: a.owner }]));
  tbl(s, rows, { fontSize: 10, colW: [0.9, 6.4, 1.4, 1.6, 2.4] });
  if (d.recommendation)
    s.addText(`Recommended decision: ${d.recommendation}`,
      { x: 0.3, y: 6.8, w: 12.7, h: 0.5, ...F, fontSize: 14, bold: true, color: TEAL });
}

pptx.writeFile({ fileName: outPath }).then(() => console.log("written", outPath));
