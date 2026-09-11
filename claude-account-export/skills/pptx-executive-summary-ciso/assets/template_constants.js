/**
 * template_constants.js — Euronext TPRM Brand Template
 * Single source of truth for ALL colours, layout, typography.
 * Import in every slide/template script:
 *   const { C, L, DOMAINS, sh } = require('./template_constants');
 */
const C = {
  brandDark:"0A2926",brandDeep:"0D3D3A",brandMid:"0E6B68",brandBright:"12B5AF",brandPale:"E8F6F5",brandPaleMid:"C4E8E6",
  red:"B83228",redDark:"8B1E16",redPale:"FCECEA",
  amber:"C97A00",amberDark:"8B5200",amberPale:"FEF3E2",
  green:"1A6B3C",greenPale:"E6F5EE",
  blue:"1A4F8A",blueDark:"122E57",bluePale:"EBF3FC",
  white:"FFFFFF",offWhite:"F8FAFA",bg:"ECF2F2",cardBg:"FFFFFF",
  border:"C8DCDB",borderLight:"E4EEEE",dark:"0D1F1E",body:"2A3B3A",muted:"5A706E",
  domB1:"1B3A6B",domB2:"1E5799",domB3:"2471A3",domB4:"2980B9",domB5:"3498DB",
};
const L = {
  W:10,H:5.625,HDR_H:0.88,FTR_Y:5.24,TOP:0.95,BOT:5.22,GAP:0.03,
  LX:0.13,LW:5.44,RX:5.70,RW:4.17,
};
const DOMAINS = [
  {key:"Cybersecurity",col:C.domB1},{key:"Data Management",col:C.domB2},
  {key:"IT",col:C.domB3},{key:"Business Continuity",col:C.domB4},{key:"Third-Parties",col:C.domB5},
];
const sh = (op=0.08)=>({type:"outer",color:"000000",opacity:op,blur:7,offset:3,angle:135});
module.exports={C,L,DOMAINS,sh};
