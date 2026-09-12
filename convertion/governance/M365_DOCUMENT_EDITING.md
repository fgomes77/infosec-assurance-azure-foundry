# Editing Office Documents on M365 — What "Edit" Means Here

The claude.ai environment had a `google-workspace` skill that edited Docs,
Sheets and Slides **in place**. There is no equivalent on this platform, and
that is a decision rather than a gap: Graph is read-only for every agent
(`../scripts/attach_integrations.py` strips non-GET), and an in-place edit is
a write to a system of record, which belongs behind the approval gate.

This file is the governance text `../integrations/CONNECTOR_DECISIONS.md`
points at for the `google-workspace` row.

## 1. The rule

**Agents never edit an Office file in place.** An "edit" is:

1. **Read the current version** from SharePoint (read-only Graph, the agent's
   own tools) — never edit a file you have not just read, or you will silently
   revert someone else's change.
2. **Regenerate the whole file** with the **same file name** in the **same**
   `Reports/<Supplier>/<Service>/` folder, through `functions/delivery`
   (`POST /api/render` → `POST /api/upload`, `conflictBehavior: replace`). The
   link stays stable and SharePoint keeps the previous content as a **version**.
3. **`output-verifier` PASS**, then **human approval** (`HUMAN_APPROVAL.md`
   Layer 3).
4. **Verify after upload**: `GET` the item back, compare size and hash against
   what was sent, and record the resulting **version number** in the pipeline
   outcome. An upload that is not read back is not evidence.

**Never trash, never delete.** A superseded deliverable is a *previous
version*, not a deleted file. Deletion is a separate, separately approved act
(`../operations/RETENTION_AND_CLEANUP.md`).

## 2. Cell-level round-trips (OneTrust Form B)

One case genuinely needs cell-level surgery rather than regeneration: the
approved Form B answers must go back into **the user's own OneTrust
round-trip import workbook**, at the exact question rows OneTrust emitted.
Regenerating that workbook would destroy the ids OneTrust matches on.

It is served by the **`form-b-fill` renderer**, not by a Graph workbook write:
the original export is passed to `POST /api/render` as the `{input}` file
(`inputFileId` | `inputDriveId`+`inputItemId` | `inputContentBase64`), the
renderer runs the byte-verified
`claude-account-export/skills/onetrust-form-b/scripts/fill_form_b.py`
unchanged, and the filled workbook comes back as the rendered artefact. The
script fails on any `VALIDATION WARNING` or unmatched question id, so a
mismatched workbook is rejected rather than half-filled.

Two consequences worth stating plainly:

- **There is no `/api/update_xlsx` and no Graph workbook write.** An earlier
  draft of this decision proposed one; it is not needed, and not having it
  keeps the delivery Function's write surface at exactly one operation
  (upload), which is what makes the Layer-1 claim easy to audit.
- **Write-back into OneTrust itself stays manual**, in the OneTrust UI, by a
  human. Enterprise access is read-only (`DATA_PROTECTION_GUARDRAILS.md` §2);
  the platform produces the workbook, a person uploads it.

## 3. Which app does what

| Operation | Where | Note |
|---|---|---|
| Generate / regenerate a document | delivery Function `POST /api/render` | the renderers in `functions/delivery/renderers/` |
| Format conversion, thumbnails, `accept_changes`, formula recalculation | office-tools Function (`/api/convert`, `/api/thumbnail`, `/api/accept_changes`, `/api/recalc`, `/api/validate`) | called by the delivery Function or the pipeline — **never** by an agent |
| OCR / layout of a scanned PDF | delivery Function `POST /api/extract_pdf` | Document Intelligence is reachable only from the delivery app |
| Upload / replace in SharePoint | delivery Function `POST /api/upload` | the single technical write path, after the gate |

## 4. Why not in-place editing at all

An in-place edit has no natural review artefact: there is no "before" to show
the approver except the file itself, and by the time it is shown the change has
happened. Regeneration gives the approver a complete candidate document and
leaves the current version untouched until they say yes. It also means a
rejected change costs nothing — nothing was written.

Controls: ISO 27001:2022 A.5.33 (protection of records), A.8.32 (change
management), A.8.15 (logging — the version history *is* the log);
EU AI Act Art. 14 (the approval is the human oversight act);
ISO 42001 A.6.2.4–A.6.2.5.
