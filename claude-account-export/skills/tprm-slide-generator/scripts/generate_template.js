#!/usr/bin/env node
/**
 * generate_template.js  —  Creates the blank Euronext TPRM brand template PPTX
 * Produces a .pptx with the full chrome and labelled placeholder zones.
 * Share this with stakeholders to show the standard slide structure.
 */
const pptxgen = require("pptxgenjs");
const path    = require("path");
const { C, L: LAYOUT, sh, DOMAINS: DOMAIN_ORDER } = require(
  path.join(__dirname, "../assets/template_constants.js")
);
const { LX, LW, RX, RW, HDR_H, FTR_Y, TOP, BOT, GAP } = LAYOUT;

async function buildTemplate() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title  = "Euronext TPRM Executive Summary — Brand Template";

  const sl = pres.addSlide();
  sl.background = { color: C.bg };

  // ── HEADER ─────────────────────────────────────────────────────────────────
  sl.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:HDR_H,
    fill:{color:C.bannerBg}, line:{color:C.bannerBg} });
  sl.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:0.22, h:HDR_H,
    fill:{color:C.brandBright}, line:{color:C.brandBright} });
  sl.addShape(pres.shapes.RECTANGLE, { x:0.22, y:0, w:0.035, h:HDR_H,
    fill:{color:C.brandMid}, line:{color:C.brandMid} });
  sl.addShape(pres.shapes.LINE, { x:0, y:HDR_H, w:10, h:0,
    line:{color:C.brandBright, width:1.8} });

  sl.addText("[Vendor Name] — Security Risks", {
    x:0.36, y:0.09, w:5.2, h:0.44,
    fontSize:22, bold:true, color:C.brandDark, fontFace:"Calibri", margin:0 });
  sl.addText("Executive Summary  ·  TPRM Risk Assessment  ·  [Month Year]", {
    x:0.36, y:0.55, w:5.4, h:0.21,
    fontSize:8, color:C.brandMid, fontFace:"Calibri", charSpacing:1.2, margin:0 });

  // KPI placeholder boxes
  for (const [xOff, label, hdrCol, textCol, bgCol, borderCol] of [
    [6.16, "OVERALL RISK\n[Medium]", C.amber,   C.amber,   C.amberPale, C.amber],
    [8.02, "CRITICALITY\n[Not-Critical]", C.brandMid, C.brandMid, C.brandPale, C.brandMid],
  ]) {
    sl.addShape(pres.shapes.RECTANGLE, { x:xOff, y:0.09, w:1.74, h:0.71,
      fill:{color:bgCol}, line:{color:borderCol, width:1.5} });
    sl.addShape(pres.shapes.RECTANGLE, { x:xOff, y:0.09, w:1.74, h:0.20,
      fill:{color:hdrCol}, line:{color:hdrCol} });
    sl.addText(label.split("\n")[0], { x:xOff, y:0.09, w:1.74, h:0.20,
      fontSize:6, bold:true, color:C.white, align:"center",
      fontFace:"Calibri", charSpacing:2, margin:0 });
    sl.addText(label.split("\n")[1], { x:xOff, y:0.28, w:1.74, h:0.47,
      fontSize:16, bold:true, color:textCol, align:"center",
      fontFace:"Calibri", margin:0 });
  }

  // ── LEFT COLUMN PLACEHOLDERS ───────────────────────────────────────────────
  const placeholders = [
    { y: TOP,        h: 0.42, label: "Service & Deployment Banner",    ac: C.brandBright },
    { y: TOP+0.45,   h: 1.82, label: "Top 3 Impact Risks\n[Score Panel + Title × 3 rows]\n[Full Register strip at bottom]", ac: C.red },
    { y: TOP+2.30,   h: 0.92, label: "Top 3 Mitigation Controls\n[Numbered • Pending/Done badge • Label — Detail]", ac: C.brandMid },
    { y: TOP+3.25,   h: BOT-(TOP+3.25), label: "Key Findings & Recommendations\n[3 numbered findings]", ac: C.blue },
  ];
  placeholders.forEach(p => {
    sl.addShape(pres.shapes.RECTANGLE, { x:LX, y:p.y, w:LW, h:p.h,
      fill:{color:C.cardBg}, line:{color:C.border, width:0.6}, shadow:sh(0.07) });
    sl.addShape(pres.shapes.RECTANGLE, { x:LX, y:p.y, w:0.055, h:p.h,
      fill:{color:p.ac}, line:{color:p.ac} });
    sl.addShape(pres.shapes.RECTANGLE, { x:LX+0.055, y:p.y, w:LW-0.055, h:0.27,
      fill:{color:"F0F0F0"}, line:{color:"F0F0F0"} });
    sl.addText(p.label, { x:LX+0.14, y:p.y+0.01, w:LW-0.2, h:p.h-0.02,
      fontSize:8, bold:false, color:"999999", italic:true,
      fontFace:"Calibri", valign:"middle", margin:0 });
  });

  // ── RIGHT COLUMN PLACEHOLDERS ──────────────────────────────────────────────
  // Radar card
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TOP, w:RW, h:2.34,
    fill:{color:C.cardBg}, line:{color:C.border, width:0.6}, shadow:sh(0.08) });
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TOP, w:RW, h:0.29,
    fill:{color:C.brandDeep}, line:{color:C.brandDeep} });
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TOP, w:0.055, h:0.29,
    fill:{color:C.brandBright}, line:{color:C.brandBright} });
  sl.addText("SECURITY RISK ASSESSMENT", { x:RX+0.10, y:TOP+0.03, w:RW-0.14, h:0.22,
    fontSize:7.8, bold:true, color:C.white, align:"center",
    fontFace:"Calibri", charSpacing:1.8, margin:0 });
  sl.addShape(pres.shapes.RECTANGLE, { x:RX+0.3, y:TOP+0.50, w:RW-0.6, h:1.70,
    fill:{color:"F5F5F5"}, line:{color:"CCCCCC", width:0.5} });
  sl.addText("[ Radar Chart PNG\n5 domains · Cybersecurity, Data Mgmt, IT, BC, 3P\nInserted via generate_radar.py ]", {
    x:RX+0.30, y:TOP+0.50, w:RW-0.60, h:1.70,
    fontSize:8, color:"AAAAAA", italic:true, align:"center", valign:"middle",
    fontFace:"Calibri", margin:0 });

  // Perimeter table card
  const TBL_Y = TOP+2.37;
  const TBL_H = BOT-TBL_Y;
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TBL_Y, w:RW, h:TBL_H,
    fill:{color:C.cardBg}, line:{color:C.border, width:0.6}, shadow:sh(0.08) });
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TBL_Y, w:RW, h:0.28,
    fill:{color:C.brandDeep}, line:{color:C.brandDeep} });
  sl.addShape(pres.shapes.RECTANGLE, { x:RX, y:TBL_Y, w:0.055, h:0.28,
    fill:{color:C.brandBright}, line:{color:C.brandBright} });
  sl.addText("EURONEXT PERIMETER  ·  ATTACK SURFACE MAP", {
    x:RX+0.10, y:TBL_Y+0.03, w:RW-0.14, h:0.21,
    fontSize:7.5, bold:true, color:C.white, align:"center",
    fontFace:"Calibri", charSpacing:0.8, margin:0 });

  // Col headers
  const TX=RX+0.055, CW0=1.44, CW1=1.26, CW2=1.38;
  const CH_Y=TBL_Y+0.29, CH_H=0.26;
  sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0,y:CH_Y,w:CW1,h:CH_H,fill:{color:C.brandPale},line:{color:C.brandPaleMid,width:0.6}});
  sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0+CW1,y:CH_Y,w:CW2,h:CH_H,fill:{color:C.bluePale},line:{color:"BCCDE8",width:0.6}});
  sl.addText("🏢  Internal",{x:TX+CW0,y:CH_Y,w:CW1,h:CH_H,fontSize:7.8,bold:true,color:C.brandDeep,align:"center",fontFace:"Calibri",margin:0});
  sl.addText("🌐  External",{x:TX+CW0+CW1,y:CH_Y,w:CW2,h:CH_H,fontSize:7.8,bold:true,color:C.blue,align:"center",fontFace:"Calibri",margin:0});

  const ROW_H=(TBL_H-CH_H-0.29)/DOMAIN_ORDER.length;
  DOMAIN_ORDER.forEach((dom,i)=>{
    const ry=CH_Y+CH_H+i*ROW_H, alt=i%2===1;
    sl.addShape(pres.shapes.RECTANGLE,{x:TX,y:ry,w:CW0,h:ROW_H,fill:{color:dom.col},line:{color:dom.col,width:0}});
    sl.addText(dom.key,{x:TX,y:ry,w:CW0,h:ROW_H,fontSize:7.5,bold:true,color:C.white,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0,y:ry,w:CW1,h:ROW_H,fill:{color:alt?"F6FEFD":"FAFFFE"},line:{color:C.borderLight,width:0.5}});
    sl.addText("[ Internal status ]",{x:TX+CW0+0.04,y:ry,w:CW1-0.06,h:ROW_H,fontSize:7,color:"AAAAAA",italic:true,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0+CW1,y:ry,w:CW2,h:ROW_H,fill:{color:alt?"F4F7FD":"F8FAFF"},line:{color:C.borderLight,width:0.5}});
    sl.addText("[ External status ]",{x:TX+CW0+CW1+0.04,y:ry,w:CW2-0.06,h:ROW_H,fontSize:7,color:"AAAAAA",italic:true,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
  });

  // ── FOOTER ─────────────────────────────────────────────────────────────────
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:FTR_Y,w:10,h:5.625-FTR_Y,fill:{color:C.bannerBg},line:{color:C.bannerBg}});
  sl.addShape(pres.shapes.LINE,{x:0,y:FTR_Y,w:10,h:0,line:{color:C.brandBright,width:1.8}});
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:FTR_Y,w:0.22,h:5.625-FTR_Y,fill:{color:C.brandBright},line:{color:C.brandBright}});
  sl.addText("EURONEXT",{x:0.32,y:FTR_Y+0.06,w:1.30,h:0.24,fontSize:8.5,bold:true,color:C.brandDark,fontFace:"Calibri",charSpacing:2.5,margin:0});
  sl.addText("*TPRM risk evaluation reflects Residual risk in present reporting week",{x:1.76,y:FTR_Y+0.07,w:7.0,h:0.22,fontSize:6.8,color:C.brandMid,fontFace:"Calibri",align:"center",margin:0});
  sl.addText("| 1",{x:9.60,y:FTR_Y+0.07,w:0.36,h:0.22,fontSize:8,color:C.muted,fontFace:"Calibri",align:"right",margin:0});

  await pres.writeFile({ fileName: "/home/claude/TPRM_Brand_Template.pptx" });
  console.log("✅  TPRM_Brand_Template.pptx generated");
}

buildTemplate().catch(e => { console.error(e); process.exit(1); });
