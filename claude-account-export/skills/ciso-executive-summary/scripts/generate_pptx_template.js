const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const VENDOR = "TINEXTA CYBER SPA";
const ASSESSMENT = "TINEXTA CYBER_TPRM_2025_Backlog";
const IMG_DIR = "/home/claude/pptx_sections";
const OUT = "/home/claude/TinextaCyber_CISO_TPRM_Governance.pptx";

// Euronext brand constants
const TEAL = "007D71";
const TEAL_DARK = "003530";
const WHITE = "FFFFFF";
const BLACK = "0F172A";
const GRAY = "64748B";
const AMBER = "D97706";
const GOLD = "DAA520";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Euronext NV — Information Security Assurance";
pres.title = `G.CISO TPRM Governance Meeting Report — ${VENDOR}`;

// Helper: add Euronext footer to content slides
function addFooter(slide, slideNum, subtitle) {
  // Euronext logo text (bottom-left)
  slide.addText("EURONEXT", {
    x: 0.5, y: 6.9, w: 2, h: 0.4,
    fontSize: 14, fontFace: "Arial", bold: true, color: TEAL
  });
  // Subtitle (bottom-center)
  slide.addText(subtitle || "TPRM Executive Summary", {
    x: 3, y: 7.05, w: 6, h: 0.3,
    fontSize: 8, fontFace: "Calibri", color: GRAY, align: "center"
  });
  // PRIVATE label
  slide.addText("PRIVATE", {
    x: 5.5, y: 7.2, w: 2, h: 0.2,
    fontSize: 8, fontFace: "Calibri", color: GOLD, align: "center"
  });
  // Slide number
  slide.addText(`| ${slideNum}`, {
    x: 12.3, y: 7.05, w: 0.8, h: 0.3,
    fontSize: 9, fontFace: "Calibri", color: TEAL, align: "right"
  });
}

// Helper: add teal accent bar (slide header)
function addAccentBar(slide) {
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0.05, w: 0.08, h: 0.95,
    fill: { color: TEAL }
  });
}

// ═══════════════════════════════════════
// SLIDE 1: Title Slide
// ═══════════════════════════════════════
const s1 = pres.addSlide();
// Teal gradient background
s1.addShape(pres.ShapeType.rect, {
  x: 0, y: 0, w: 13.33, h: 7.5,
  fill: { color: TEAL_DARK }
});
// Decorative lighter rectangles
s1.addShape(pres.ShapeType.rect, {
  x: 0, y: 0, w: 5, h: 7.5,
  fill: { color: TEAL, transparency: 60 }
});
// Title
s1.addText("Current TP Risks above risk\nappetite", {
  x: 0.8, y: 2.5, w: 6, h: 2.5,
  fontSize: 40, fontFace: "Arial", bold: true, color: WHITE,
  lineSpacingMultiple: 1.2
});
// Euronext footer
s1.addText("EURONEXT", {
  x: 0.8, y: 6.2, w: 3, h: 0.5,
  fontSize: 16, fontFace: "Arial", bold: true, color: WHITE
});

// ═══════════════════════════════════════
// SLIDE 2: Assessment Summary Table
// ═══════════════════════════════════════
const s2 = pres.addSlide();
addAccentBar(s2);
s2.addText(`Assessments with Infosec Risk Score Medium`, {
  x: 0.3, y: 0.15, w: 12, h: 0.8,
  fontSize: 28, fontFace: "Arial", bold: true, color: BLACK
});
s2.addText(`${VENDOR}`, {
  x: 0.5, y: 1.1, w: 10, h: 0.4,
  fontSize: 16, fontFace: "Calibri", color: BLACK
});
// Summary table
const tableRows = [
  [
    { text: "Vendor / Service", options: { fill: TEAL, color: WHITE, bold: true, fontSize: 11 } },
    { text: "Service Description", options: { fill: TEAL, color: WHITE, bold: true, fontSize: 11 } },
    { text: "Company", options: { fill: TEAL, color: WHITE, bold: true, fontSize: 11 } },
    { text: "Infosec Risk Score", options: { fill: TEAL, color: WHITE, bold: true, fontSize: 11 } },
    { text: "Service Criticality", options: { fill: TEAL, color: WHITE, bold: true, fontSize: 11 } }
  ],
  [
    { text: "TINEXTA CYBER SPA / InfoCert (ICT)", options: { fontSize: 10 } },
    { text: "Digital trust solutions — digital signatures, electronic ID, secure digital storage. EU compliance.", options: { fontSize: 10 } },
    { text: "Euronext NV", options: { fontSize: 10 } },
    { text: "Medium", options: { fontSize: 10, bold: true, color: AMBER } },
    { text: "Not critical", options: { fontSize: 10 } }
  ]
];
s2.addTable(tableRows, {
  x: 0.5, y: 1.7, w: 12.3,
  border: { pt: 0.5, color: "CCCCCC" },
  colW: [2.5, 4.5, 1.8, 1.8, 1.7],
  rowH: [0.4, 0.5],
  fontFace: "Calibri",
  autoPage: false
});
// Key findings bullets
s2.addText([
  { text: "•  TINEXTA CYBER SPA (InfoCert) holds valid ISO 27001 and ISO 20000-1 certifications. All vendor-side controls (CIS 16.14, ISO 5.22) are Implemented. Residual risks remain Medium, concentrated in the Third-Parties domain, and are actively being treated through pending Euronext Supply Chain RM agreements.", options: { breakLine: true, fontSize: 11, bullet: false } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "•  No agreement or contract found in TPOPS at assessment date. Registered in CMDB as InfoCert.", options: { breakLine: true, fontSize: 11 } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "•  At this stage, all identified mitigation controls depend on Euronext internal teams (Security, Compliance, Risk & BCM agreements); therefore, no additional actions are required from the Supplier or the Contract Owner.", options: { fontSize: 11 } }
], {
  x: 0.5, y: 2.8, w: 12.3, h: 3,
  fontFace: "Calibri", color: BLACK, valign: "top",
  paraSpaceAfter: 6
});
addFooter(s2, 2, "Assessments: Infosec Risk Score above Medium");

// ═══════════════════════════════════════
// SLIDE 3: TPRM Executive Summary (image)
// ═══════════════════════════════════════
const s3 = pres.addSlide();
addAccentBar(s3);
s3.addText(`${VENDOR} - TPRM Executive Summary`, {
  x: 0.3, y: 0.15, w: 12, h: 0.8,
  fontSize: 28, fontFace: "Arial", bold: true, color: BLACK
});
s3.addImage({
  path: `${IMG_DIR}/s3_exec_summary.png`,
  x: 0.15, y: 1.0, w: 13.0, h: 6.0,
  sizing: { type: "contain", w: 13.0, h: 6.0 }
});
addFooter(s3, 3);

// ═══════════════════════════════════════
// SLIDE 4: Open Risks (image)
// ═══════════════════════════════════════
const s4 = pres.addSlide();
addAccentBar(s4);
s4.addText(`${VENDOR} – Open Risks`, {
  x: 0.3, y: 0.15, w: 12, h: 0.8,
  fontSize: 28, fontFace: "Arial", bold: true, color: BLACK
});
s4.addImage({
  path: `${IMG_DIR}/s4_open_risks.png`,
  x: 0.15, y: 1.0, w: 13.0, h: 5.2,
  sizing: { type: "contain", w: 13.0, h: 5.2 }
});
addFooter(s4, 4);

// ═══════════════════════════════════════
// SLIDE 5: Mitigation Controls (image)
// ═══════════════════════════════════════
const s5 = pres.addSlide();
addAccentBar(s5);
s5.addText(`${VENDOR} – Mitigation Controls`, {
  x: 0.3, y: 0.15, w: 12, h: 0.8,
  fontSize: 28, fontFace: "Arial", bold: true, color: BLACK
});
s5.addImage({
  path: `${IMG_DIR}/s5_controls_perimeter.png`,
  x: 0.15, y: 1.0, w: 13.0, h: 5.8,
  sizing: { type: "contain", w: 13.0, h: 5.8 }
});
addFooter(s5, 5);

// ═══════════════════════════════════════
// SLIDE 6: TPRM continuation - Findings + Actions (image)
// ═══════════════════════════════════════
const s6 = pres.addSlide();
addAccentBar(s6);
s6.addText(`${VENDOR} - TPRM Executive Summary`, {
  x: 0.3, y: 0.05, w: 10, h: 0.7,
  fontSize: 28, fontFace: "Arial", bold: true, color: BLACK
});
s6.addText("(continuation)", {
  x: 10.3, y: 0.22, w: 2.5, h: 0.5,
  fontSize: 14, fontFace: "Calibri", color: GRAY
});
s6.addImage({
  path: `${IMG_DIR}/s6_findings_actions.png`,
  x: 0.15, y: 0.9, w: 13.0, h: 5.5,
  sizing: { type: "contain", w: 13.0, h: 5.5 }
});
addFooter(s6, 6);

// ═══════════════════════════════════════
// SLIDE 7: Euronext Closing
// ═══════════════════════════════════════
const s7 = pres.addSlide();
s7.addShape(pres.ShapeType.rect, {
  x: 0, y: 6.8, w: 13.33, h: 0.7,
  fill: { color: TEAL }
});
s7.addText("EURONEXT", {
  x: 4.5, y: 3.0, w: 4.3, h: 1,
  fontSize: 36, fontFace: "Arial", bold: true, color: TEAL, align: "center"
});

// ═══════════════════════════════════════
// SLIDE 8: Disclaimer
// ═══════════════════════════════════════
const s8 = pres.addSlide();
s8.addText("This publication is for information purposes only and is not a recommendation to engage in investment activities. This publication is provided \"as is\" without representation or warranty of any kind. Whilst all reasonable care has been taken to ensure the accuracy of the content, Euronext does not guarantee its accuracy or completeness.", {
  x: 0.5, y: 2, w: 12.3, h: 3,
  fontSize: 8, fontFace: "Calibri", color: GRAY, align: "justify"
});
s8.addText("EURONEXT", {
  x: 0.5, y: 6.9, w: 2, h: 0.4,
  fontSize: 14, fontFace: "Arial", bold: true, color: TEAL
});

// WRITE
pres.writeFile({ fileName: OUT }).then(() => {
  console.log(`✅ PPTX saved → ${OUT}`);
}).catch(err => {
  console.error("Error:", err);
});
