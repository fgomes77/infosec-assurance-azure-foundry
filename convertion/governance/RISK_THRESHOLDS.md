# Risk Thresholds — Scale-Aware Reference (single source for the platform)

Two different, both correct, scales coexist in the exported skills. They
are NOT interchangeable and no agent, verifier rule or template label may
apply one scale's bands to the other's scores. Persona principle 3
("apply the team's established thresholds exactly; never invent
alternative scales") means: use the scale that belongs to the deliverable
type below. Source of truth is the byte-verified skill content in
`../../claude-account-export/skills/`; this file only indexes it.

## 1. Scales by deliverable / agent

| Scale | Bands | Deliverables / agents on this scale | Source (verbatim skill) |
|---|---|---|---|
| **OneTrust residual score 1–25** (likelihood × impact) | `>12` HIGH (red `#DC2626`) · `>4 ≤12` MEDIUM (amber `#D97706`) · `≤4` LOW (teal `#007D71`) | `ciso-reporting` (HTML dashboard, A3 PDF, 8-slide PPTX), `ciso-executive-summary` (Strategic Risk Intelligence Dashboard HTML), `dpia` (InfoSec TPA report — control status only, no re-scoring), `ciso-global-report` when fed OneTrust scores | `ciso-reporting/SKILL.md` "Thresholds (OneTrust 1–25 scale)" and SSOT §1; `ciso-executive-summary/SKILL.md` threshold table |
| **TPRM 10-scale** (inherent / residual, one decimal) | classification High `≥7.0` · Medium `≥4.0 <7.0` · Low `<4.0`; slide/gauge colour red `≥5.5` · amber `≥4.0` · green `<4.0` | `tprm-slide-generator`, `pptx-executive-summary-ciso`, `ciso-global-report` gauges and exposure map (`functions/delivery/renderers-src/ciso-global/generate_slide.js`: `scoreColor` High ≥7.0 red / Medium ≥4.0 amber) | `tprm-slide-generator/SKILL.md` and `pptx-executive-summary-ciso/SKILL.md` classification table |
| **TPSRCA 1–25 risk + 0–100 maturity** | Risk score: 20–25 Critical · 15–19 High · 10–14 Medium · 1–9 Low. Framework %: <50 Critical · 50–69 High · 70–79 Medium · 80–100 Low. Composite: <60 · 60–69 · 70–79 · 80–100. Confidence: <50 · 50–69 · 70–84 · 85–100 | `tpsrca-assessment-engine` | `tpsrca-assessment-engine/SKILL.md` "Rating Thresholds" (SSOT §2) |
| **DeepSearch confidence / posture** | as defined per section in the protocol (no cross-mapping to the scales above) | `deepsearch-protocol`, `ai-deepsearch-osint-gathering-report` | respective `SKILL.md` §Confidence Scoring |

Invariants that hold on every scale: residual ≤ inherent; a score and its
colour band must agree; a threshold change is a **methodology change**
and goes through the template-manager approval workflow
(`HUMAN_APPROVAL.md` Layer 3), never through an agent's judgement.

## 2. Where the platform must stay scale-aware

| Component | Required behaviour |
|---|---|
| `agents/persona_system_prompt.md` principle 3 | Must cite this file instead of hard-coding the 10-scale bands (shared delta recorded in the workflow output). |
| `agents/verifier_instructions.md` rule 2 | Consistency check keyed by deliverable type using §1 above; a correct `ciso-reporting` draft with residual 12 = MEDIUM must PASS. |
| `templates/registry.json` → `ciso-executive-summary-html`.style.thresholds | `">12 HIGH, >4 MEDIUM, <=4 LOW (OneTrust 1-25)"` — the current `High>=7.0 Medium>=4.0` label is the wrong scale for that template. |
| `agents/ciso-global-report_instructions.md` | State which scale each input carries; never re-map OneTrust 1–25 residuals onto the 0–10 gauges without the documented conversion the team approves (none exists today → "TO CONFIRM"). |
| `operations/evaluation` comparison set | Known-good claude.ai outputs are the fidelity oracle; the verifier's thresholds are derived from them, not the other way round. |

## 3. Verification

```bash
grep -n "1–25\|>12" ../../claude-account-export/skills/ciso-reporting/SKILL.md      # OneTrust scale, unchanged
grep -n "≥ 7.0" ../../claude-account-export/skills/tprm-slide-generator/SKILL.md     # 10-scale, unchanged
grep -n "thresholds" ../templates/registry.json                                     # label must name the scale
```
