#!/usr/bin/env node
/**
 * generate_slide.js — Euronext TPRM Executive Summary Slide Generator
 * Data-driven from tprm_data.json + radar PNG.
 * All brand values imported from template_constants.js.
 *
 * Usage:
 *   node generate_slide.js --data <json> --radar <png> --out <pptx>
 */
"use strict";
const pptxgen = require("pptxgenjs");
const fs      = require("fs");
const path    = require("path");
const { C, L, DOMAINS, sh } = require(path.join(__dirname,"../assets/template_constants.js"));

// ── CLI ────────────────────────────────────────────────────────────────────────
const a={};process.argv.slice(2).forEach((v,i,arr)=>{if(v.startsWith("--"))a[v.slice(2)]=arr[i+1];});
const DATA  = a.data  || "/home/claude/tprm_data.json";
const RADAR = a.radar || "/home/claude/radar_chart.png";
const OUT   = a.out   || "/home/claude/TPRM_ExecSummary.pptx";
const d     = JSON.parse(fs.readFileSync(DATA,"utf8"));

// ── HELPERS ────────────────────────────────────────────────────────────────────
const mkSh = (op=0.08)=>sh(op);
const scoreColor=s=>s>=5.5?C.red:s>=4.0?C.amber:C.green;
const scoreBg   =s=>s>=5.5?C.redPale:s>=4.0?C.amberPale:C.greenPale;
const scoreDark =s=>s>=5.5?C.redDark:s>=4.0?C.amberDark:C.green;

function card(sl,pres,x,y,w,h,{accent,accentW=0.055,fill=C.cardBg}={}){
  sl.addShape(pres.shapes.RECTANGLE,{x,y,w,h,fill:{color:fill},line:{color:C.border,width:0.6},shadow:mkSh()});
  if(accent) sl.addShape(pres.shapes.RECTANGLE,{x,y,w:accentW,h,fill:{color:accent},line:{color:accent}});
}
function secHeader(sl,pres,x,y,w,aw,text,textC,stripC){
  const h=0.27;
  sl.addShape(pres.shapes.RECTANGLE,{x:x+aw,y,w:w-aw,h,fill:{color:stripC},line:{color:stripC}});
  sl.addText(text,{x:x+aw+0.10,y:y+0.01,w:w-aw-0.14,h:h-0.02,fontSize:9.5,bold:true,color:textC,fontFace:"Calibri",charSpacing:0.3,margin:0});
}

function riskKpi(risk){
  if(risk==="High")  return{bg:C.redPale,  border:C.red,  hdr:C.red,  txt:C.red};
  if(risk==="Medium")return{bg:C.amberPale,border:C.amber,hdr:C.amber,txt:C.amber};
  return               {bg:C.greenPale,border:C.green,hdr:C.green,txt:C.green};
}

// ── BUILD ──────────────────────────────────────────────────────────────────────
async function build(){
  const pres=new pptxgen();
  pres.layout="LAYOUT_16x9";
  pres.title=`${d.vendor} — TPRM Executive Summary`;
  const sl=pres.addSlide();
  sl.background={color:C.bg};

  const {LX,LW,RX,RW,HDR_H,FTR_Y,TOP,BOT,GAP}=L;

  /* ── HEADER ── */
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:0,w:10,h:HDR_H,fill:{color:C.brandPale},line:{color:C.brandPale}});
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:0,w:0.22,h:HDR_H,fill:{color:C.brandBright},line:{color:C.brandBright}});
  sl.addShape(pres.shapes.RECTANGLE,{x:0.22,y:0,w:0.035,h:HDR_H,fill:{color:C.brandMid},line:{color:C.brandMid}});
  sl.addShape(pres.shapes.LINE,{x:0,y:HDR_H,w:10,h:0,line:{color:C.brandBright,width:1.8}});
  sl.addText(`${d.vendor} — Security Risks`,{x:0.36,y:0.09,w:5.2,h:0.44,fontSize:22,bold:true,color:C.brandDark,fontFace:"Calibri",margin:0});
  sl.addText(`Executive Summary  ·  TPRM Risk Assessment  ·  ${d.report_date}`,{x:0.36,y:0.55,w:5.4,h:0.21,fontSize:8,color:C.brandMid,fontFace:"Calibri",charSpacing:1.2,margin:0});

  // KPIs
  const rk=riskKpi(d.overall_risk);
  for(const[xOff,label,hdr,bg,border,txt,fs]of[
    [6.16,"OVERALL RISK",rk.hdr,rk.bg,rk.border,rk.txt,18],
    [8.02,"CRITICALITY", C.brandMid,C.brandPale,C.brandMid,C.brandMid,13],
  ]){
    sl.addShape(pres.shapes.RECTANGLE,{x:xOff,y:0.09,w:1.74,h:0.71,fill:{color:bg},line:{color:border,width:1.5}});
    sl.addShape(pres.shapes.RECTANGLE,{x:xOff,y:0.09,w:1.74,h:0.20,fill:{color:hdr},line:{color:hdr}});
    sl.addText(label,{x:xOff,y:0.09,w:1.74,h:0.20,fontSize:6,bold:true,color:C.white,align:"center",fontFace:"Calibri",charSpacing:2,margin:0});
    sl.addText(xOff<7?d.overall_risk:d.criticality,{x:xOff,y:0.28,w:1.74,h:0.47,fontSize:fs,bold:true,color:txt,align:"center",fontFace:"Calibri",margin:0});
  }

  /* ── SERVICE BANNER ── */
  const SVC_Y=TOP,SVC_H=0.42;
  card(sl,pres,LX,SVC_Y,LW,SVC_H,{accent:C.brandBright});
  const certs=(d.certifications||[]).join(", ")||"None";
  sl.addText([
    {text:"Service & Deployment  ",options:{bold:true,color:C.brandDeep,fontSize:9}},
    {text:d.service_desc,options:{color:C.body,fontSize:8.5}},
    {text:"   DORA: ",options:{color:C.body,fontSize:8.5}},
    {text:d.dora_scope?"Yes ✔":"No ✗",options:{bold:true,color:d.dora_scope?C.green:C.amber,fontSize:8.5}},
    {text:`   Certs: ${certs}`,options:{color:C.muted,fontSize:8}},
  ],{x:LX+0.13,y:SVC_Y,w:LW-0.17,h:SVC_H,fontFace:"Calibri",valign:"middle",margin:0});

  /* ── TOP 3 RISKS ── */
  const RSK_Y=SVC_Y+SVC_H+GAP,RSK_H=1.82;
  card(sl,pres,LX,RSK_Y,LW,RSK_H,{accent:C.red});
  secHeader(sl,pres,LX,RSK_Y,LW,0.055,"▲   TOP 3 EURONEXT IMPACT RISKS",C.red,C.redPale);
  const panelW=1.72;
  (d.top_risks||[]).slice(0,3).forEach((r,i)=>{
    const ROW_H=0.40,ry=RSK_Y+0.29+i*(ROW_H+0.04);
    if(i%2===1) sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.055,y:ry,w:LW-0.055,h:ROW_H,fill:{color:C.offWhite},line:{color:C.offWhite}});
    sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.055,y:ry,w:panelW,h:ROW_H,fill:{color:scoreBg(r.score)},line:{color:scoreBg(r.score)}});
    sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.055,y:ry,w:0.04,h:ROW_H,fill:{color:scoreColor(r.score)},line:{color:scoreColor(r.score)}});
    sl.addShape(pres.shapes.LINE,{x:LX+0.055+panelW,y:ry,w:0,h:ROW_H,line:{color:C.border,width:0.6}});
    sl.addText("RESIDUAL RISK SCORE",{x:LX+0.11,y:ry+0.03,w:panelW-0.07,h:0.14,fontSize:6,bold:true,color:scoreDark(r.score),fontFace:"Calibri",charSpacing:1.2,align:"center",margin:0});
    sl.addText(`${Number(r.score).toFixed(1)}`,{x:LX+0.11,y:ry+0.14,w:panelW-0.07,h:0.24,fontSize:20,bold:true,color:scoreColor(r.score),fontFace:"Calibri",align:"center",margin:0});
    const tx=LX+0.055+panelW+0.10,tw=LW-0.055-panelW-0.14;
    sl.addText(r.title,{x:tx,y:ry+0.02,w:tw,h:0.21,fontSize:9.5,bold:true,color:C.dark,fontFace:"Calibri",valign:"middle",margin:0});
    if(r.detail) sl.addText((r.detail||"").substring(0,80),{x:tx,y:ry+0.22,w:tw,h:0.16,fontSize:7.2,color:C.muted,italic:true,fontFace:"Calibri",margin:0});
  });

  // Full register strip
  const regY=RSK_Y+RSK_H-0.20;
  sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.055,y:regY,w:LW-0.055,h:0.20,fill:{color:"EFF5F4"},line:{color:"EFF5F4"}});
  sl.addShape(pres.shapes.LINE,{x:LX+0.055,y:regY,w:LW-0.055,h:0,line:{color:C.border,width:0.5}});
  const regParts=[{text:`Full Register (${(d.full_register||[]).length} risks — In Treatment):  `,options:{bold:true,color:C.muted}}];
  (d.full_register||[]).forEach((r,i)=>{
    regParts.push({text:`${r.id} `,options:{bold:true,color:scoreColor(r.score)}});
    regParts.push({text:`${r.label} ${r.score}${i<d.full_register.length-1?"  ·  ":""}`,options:{color:C.body}});
  });
  sl.addText(regParts,{x:LX+0.13,y:regY+0.02,w:LW-0.18,h:0.16,fontSize:6.8,fontFace:"Calibri",margin:0});

  /* ── MITIGATION CONTROLS ── */
  const MIT_Y=RSK_Y+RSK_H+GAP,MIT_H=0.92;
  card(sl,pres,LX,MIT_Y,LW,MIT_H,{accent:C.brandMid});
  secHeader(sl,pres,LX,MIT_Y,LW,0.055,"✦   TOP 3 MITIGATION CONTROLS",C.brandDeep,C.brandPale);
  (d.mitigations||[]).slice(0,3).forEach((ctrl,i)=>{
    const cy=MIT_Y+0.30+i*0.20;
    sl.addShape(pres.shapes.OVAL,{x:LX+0.12,y:cy+0.02,w:0.20,h:0.20,fill:{color:C.brandMid},line:{color:C.brandMid}});
    sl.addText(String(i+1),{x:LX+0.12,y:cy+0.02,w:0.20,h:0.20,fontSize:8,bold:true,color:C.white,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    const pend=(ctrl.status||"Pending")==="Pending";
    sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.37,y:cy+0.03,w:0.60,h:0.17,fill:{color:pend?C.redPale:C.greenPale},line:{color:pend?C.red:C.green,width:0.75}});
    sl.addText(pend?"⏳  Pending":"✔  Done",{x:LX+0.37,y:cy+0.03,w:0.60,h:0.17,fontSize:6.5,bold:true,color:pend?C.red:C.green,align:"center",fontFace:"Calibri",margin:0});
    sl.addText([{text:ctrl.label+"  ",options:{bold:true,color:C.dark}},{text:"—  "+ctrl.detail,options:{color:C.muted}}],
      {x:LX+1.02,y:cy,w:LW-1.10,h:0.23,fontSize:7.8,fontFace:"Calibri",valign:"middle",margin:0});
  });

  /* ── KEY FINDINGS ── */
  const KF_Y=MIT_Y+MIT_H+GAP,KF_H=BOT-KF_Y;
  card(sl,pres,LX,KF_Y,LW,KF_H,{accent:C.blue,fill:C.bluePale});
  sl.addShape(pres.shapes.RECTANGLE,{x:LX+0.055,y:KF_Y,w:LW-0.055,h:0.25,fill:{color:"D2E5F6"},line:{color:"D2E5F6"}});
  sl.addText("💡   KEY FINDINGS & RECOMMENDATIONS",{x:LX+0.14,y:KF_Y+0.01,w:LW-0.18,h:0.23,fontSize:9.5,bold:true,color:C.blue,fontFace:"Calibri",charSpacing:0.2,margin:0});
  (d.findings||[]).slice(0,3).forEach((f,i)=>{
    const fy=KF_Y+0.28+i*0.22;
    sl.addShape(pres.shapes.OVAL,{x:LX+0.13,y:fy+0.02,w:0.18,h:0.18,fill:{color:C.blue},line:{color:C.blue}});
    sl.addText(String(i+1),{x:LX+0.13,y:fy+0.02,w:0.18,h:0.18,fontSize:7.5,bold:true,color:C.white,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    const parts=[];
    f.replace(/\*\*(.+?)\*\*/g,(_,b)=>`|||B|||${b}|||E|||`).split("|||").forEach(seg=>{
      if(seg==="B"||seg==="E") return;
      const isBold=seg.startsWith("B|||");
      const text=isBold?seg.slice(4):seg; if(!text) return;
      const col=text==="Pending"?C.red:text==="Implemented"?C.green:C.blue;
      parts.push({text,options:{bold:isBold,color:isBold?col:C.body}});
    });
    sl.addText(parts.length?parts:[{text:f,options:{color:C.body}}],
      {x:LX+0.37,y:fy,w:LW-0.44,h:0.22,fontSize:7.8,fontFace:"Calibri",valign:"middle",margin:0});
  });

  /* ── RIGHT: RADAR PANEL ── */
  const RAD_Y=TOP,RAD_H=2.34;
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:RAD_Y,w:RW,h:RAD_H,fill:{color:C.cardBg},line:{color:C.border,width:0.6},shadow:mkSh(0.09)});
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:RAD_Y,w:RW,h:0.29,fill:{color:C.brandDeep},line:{color:C.brandDeep}});
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:RAD_Y,w:0.055,h:0.29,fill:{color:C.brandBright},line:{color:C.brandBright}});
  sl.addText("SECURITY RISK ASSESSMENT",{x:RX+0.10,y:RAD_Y+0.03,w:RW-0.14,h:0.22,fontSize:7.8,bold:true,color:C.white,align:"center",fontFace:"Calibri",charSpacing:1.8,margin:0});
  sl.addText("Residual risk per domain  ·  Scale 0–10  ·  🔴 High ≥7  🟡 Medium 4–7  🟢 Low ≤4",{x:RX+0.06,y:RAD_Y+0.30,w:RW-0.12,h:0.13,fontSize:6.0,color:C.muted,align:"center",fontFace:"Calibri",margin:0});
  // Radar image — fills full card height below subtitle
  sl.addImage({path:RADAR,x:RX+0.02,y:RAD_Y+0.44,w:RW-0.04,h:RAD_H-0.46});

  /* ── RIGHT: PERIMETER TABLE ── */
  const TBL_Y=RAD_Y+RAD_H+GAP,TBL_H=BOT-TBL_Y;
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:TBL_Y,w:RW,h:TBL_H,fill:{color:C.cardBg},line:{color:C.border,width:0.6},shadow:mkSh(0.09)});
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:TBL_Y,w:RW,h:0.28,fill:{color:C.brandDeep},line:{color:C.brandDeep}});
  sl.addShape(pres.shapes.RECTANGLE,{x:RX,y:TBL_Y,w:0.055,h:0.28,fill:{color:C.brandBright},line:{color:C.brandBright}});
  sl.addText("EURONEXT PERIMETER  ·  ATTACK SURFACE MAP",{x:RX+0.10,y:TBL_Y+0.03,w:RW-0.14,h:0.21,fontSize:7.5,bold:true,color:C.white,align:"center",fontFace:"Calibri",charSpacing:0.8,margin:0});

  const TX=RX+0.055,CW0=1.44,CW1=1.26,CW2=1.38;
  const CH_Y=TBL_Y+0.29,CH_H=0.26;
  sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0,y:CH_Y,w:CW1,h:CH_H,fill:{color:C.brandPale},line:{color:C.brandPaleMid,width:0.6}});
  sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0+CW1,y:CH_Y,w:CW2,h:CH_H,fill:{color:C.bluePale},line:{color:"BCCDE8",width:0.6}});
  sl.addText("🏢  Internal",{x:TX+CW0,y:CH_Y,w:CW1,h:CH_H,fontSize:7.8,bold:true,color:C.brandDeep,align:"center",fontFace:"Calibri",margin:0});
  sl.addText("🌐  External",{x:TX+CW0+CW1,y:CH_Y,w:CW2,h:CH_H,fontSize:7.8,bold:true,color:C.blue,align:"center",fontFace:"Calibri",margin:0});

  const ROW_H=(TBL_H-CH_H-0.29)/DOMAINS.length;
  DOMAINS.forEach((dom,i)=>{
    const ry=CH_Y+CH_H+i*ROW_H,alt=i%2===1;
    const p=(d.perimeter||{})[dom.key]||{internal:{text:"✔ Mitigated",alert:false},external:{text:"✔ Mitigated",alert:false}};
    sl.addShape(pres.shapes.RECTANGLE,{x:TX,y:ry,w:CW0,h:ROW_H,fill:{color:dom.col},line:{color:dom.col,width:0}});
    sl.addText(dom.key,{x:TX,y:ry,w:CW0,h:ROW_H,fontSize:7.5,bold:true,color:C.white,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    const iBg=p.internal.alert?C.amberPale:alt?"F6FEFD":"FAFFFE";
    sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0,y:ry,w:CW1,h:ROW_H,fill:{color:iBg},line:{color:C.borderLight,width:0.5}});
    sl.addText(p.internal.text,{x:TX+CW0+0.04,y:ry,w:CW1-0.06,h:ROW_H,fontSize:p.internal.alert?7:7.5,bold:p.internal.alert,color:p.internal.alert?C.amber:C.green,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
    sl.addShape(pres.shapes.RECTANGLE,{x:TX+CW0+CW1,y:ry,w:CW2,h:ROW_H,fill:{color:alt?"F4F7FD":"F8FAFF"},line:{color:C.borderLight,width:0.5}});
    sl.addText(p.external.text,{x:TX+CW0+CW1+0.04,y:ry,w:CW2-0.06,h:ROW_H,fontSize:7.5,bold:p.external.alert,color:p.external.alert?C.amber:C.green,align:"center",valign:"middle",fontFace:"Calibri",margin:0});
  });

  /* ── FOOTER ── */
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:FTR_Y,w:10,h:5.625-FTR_Y,fill:{color:C.brandPale},line:{color:C.brandPale}});
  sl.addShape(pres.shapes.LINE,{x:0,y:FTR_Y,w:10,h:0,line:{color:C.brandBright,width:1.8}});
  sl.addShape(pres.shapes.RECTANGLE,{x:0,y:FTR_Y,w:0.22,h:5.625-FTR_Y,fill:{color:C.brandBright},line:{color:C.brandBright}});
  sl.addText("EURONEXT",{x:0.32,y:FTR_Y+0.06,w:1.30,h:0.24,fontSize:8.5,bold:true,color:C.brandDark,fontFace:"Calibri",charSpacing:2.5,margin:0});
  sl.addText("*TPRM risk evaluation reflects Residual risk in present reporting week",{x:1.76,y:FTR_Y+0.07,w:7.0,h:0.22,fontSize:6.8,color:C.brandMid,fontFace:"Calibri",align:"center",margin:0});
  sl.addText("| 1",{x:9.60,y:FTR_Y+0.07,w:0.36,h:0.22,fontSize:8,color:C.muted,fontFace:"Calibri",align:"right",margin:0});

  await pres.writeFile({fileName:OUT});
  console.log(`✅  ${OUT}`);
}
build().catch(e=>{console.error(e);process.exit(1);});
