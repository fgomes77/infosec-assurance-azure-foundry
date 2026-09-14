# `convertion/evaluation/` — pointer

The evaluation harness lives in **`../operations/evaluation/`**, next to the
operating documents that use it:

| Path | What |
|---|---|
| `../operations/evaluation/EVALUATION.md` | The loop, golden-set composition, metrics and floors, gates G0–G5, the monthly M1 procedure, and the platform-side continuous-evaluation / red-team hooks (§4b, finding C18) |
| `../operations/evaluation/golden-set.schema.json` | JSON Schema of a golden set |
| `../operations/evaluation/golden-set.example.json` | Starter set with offline fixtures |
| `../operations/evaluation/run_evals.py` | The runner (`--dry-run`, `--candidates`, live, `--model-override`, `--emit-plans`, `--redteam-report`) |
| `../ci/README.md` | Where gate **G0** runs on every PR |

The real golden set (`golden-set.json`, `EVAL_GOLDEN_SET_PATH` in
`setup/.env`) is **not** committed: its cases quote approved supplier
deliverables. It lives on the site under `Governance/ComparisonSet/`, and
reports are written to the git-ignored `build/evals/`.

`golden/` and `smoke/` here are empty placeholders from an earlier layout;
do not add a second golden set — extend the one above.
