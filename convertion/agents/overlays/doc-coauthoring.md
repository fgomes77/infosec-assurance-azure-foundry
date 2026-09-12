# doc-coauthoring — Foundry adaptation

(Appended after the SKILL.md body; environment mapping only. Deployed as an
adapted example skill for policies, procedures, DORA RoI write-ups and
assessment narratives.)

- **Stage 1 context sources:** Confluence, SharePoint, Jira and Jira
  Assets read-only tools replace Slack/Google Drive; quote the record you
  used. Web search only for public references.
- **Stage 2 drafting:** no artifacts — keep the working document in a
  `code_interpreter` file (`/mnt/data/outputs/<slug>.md`) and show the
  changed section in the thread after each edit.
- **Stage 3 reader testing:** replace sub-agents with the connected agent
  `output_verifier` (rule-based check) and, for a "fresh reader", a
  hand-off to `infosec_assurance_advisor` with ONLY the draft text and the
  reader questions.
- **Finalisation:** hand the approved markdown to the `docx` agent /
  `advisory-file-delivery` pipeline (DOCX under `Advisory/<Topic>/<Subtopic>/`
  or `Reports/<Supplier>/<Service>/`), after verifier PASS and approval.
- House style: `knowledge-packs/enx-writing-style.md`.
