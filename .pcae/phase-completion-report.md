# Phase 146D — CHGR-001 Sec.26 Authority-Basis Requiredness Resolution

**Status:** Complete (contract/schema amendment only; no production code,
runtime, Publication Coordinator, or Interactive Workflow change; no
execution capability added; no certification of Chapter 146).
**Mode:** Contract Amendment.
**Predecessor:** Phase 146C — CHGR-001 Schema-Envelope Contract
Independent Verification (verdict: NOT VERIFIED).
**Question answered:** per explicit human authorization, grounded in
Phase 146C's own Blocking finding — determine the architectural root
cause of the CHGR-REQ-199/CHGR-REQ-204/schema contradiction and produce
the minimum necessary amendment.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Pushed:** pending_push (commits `6794c0f5`, `d0ac6c78`, `abb97ef2`,
`7291b455` are local to `main`; push authorized by the human and
in progress as part of this phase's own completion).

This phase did not assume the schema was wrong, and did not assume
CHGR-REQ-199 was wrong. Every claim below was independently re-derived
from primary sources: CHGR-001 §11/§12/§22, the Phase 143E schema's own
description, PEC-REQ-115 (Phase 144F), CHGR-REQ-096/097 (Phase 143B),
IWPC-001 §31 C-1's disclosed deferral, and `record.py`'s own existing
disclosure text.

---

## 1. Bootstrap

`git status --short`: clean at phase start. `git branch --show-current`:
`main`. `git rev-list --count origin/main..HEAD`: 0 at phase start.
`pcae session bootstrap --agent-id claude-local`: lock already held,
health healthy, check passed. Latest completed phase: 146C (completed,
report: complete). Recommended next phase per bootstrap: 146D (explicit
human authorization was supplied separately in the phase prompt, not
inferred from the recommendation). `pcae task transition` closed the
post-146C idle placeholder and opened this phase's own task. `pcae
check`/`pcae health`/`pcae doctor task-memory`: passed/healthy/clean.
`pcae runtime inspect`: `Observed`/`observe`/`unavailable`. `pcae push
check`: clean, 0 unpushed commits, nothing to push (prior to this
phase's own commits).

## 2. Root-cause reconstruction and candidate evaluation

Directly read CHGR-001 §11 (Authority Contract), §12 (Assurance
Contract), §22 (Amendment Contract), CHGR-REQ-090–097/180–188; PEC-REQ-115
(`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`); IWPC-001 §29/§31
(the C-1 deferral, independently re-confirmed Non-Blocking/Observation,
disclosed, out of scope); `human_governance_record.schema.json`'s own
top-of-file description (Phase 143E, unchanged: "explicitly named
'claimed', never 'verified'"); and `record.py`'s own `_KNOWN_LIMITATIONS`
disclosure text (unmodified, read only).

Five candidates evaluated against this evidence:

- **(A) CHGR-REQ-199 incorrect — rejected.** Would contradict
  CHGR-REQ-097/the Authority Contract's "never silently resolved in the
  record's favor" rule.
- **(B) The frozen schema's requiredness incorrect — accepted.** The
  `required` array was frozen (143E) before PEC-REQ-115 (144F) or
  CHGR-REQ-199/204 (146B) established the field's conditional
  construction rule — a sequencing artifact, matching the schema's own
  existing optional-field convention (`rationale`, `conditions`,
  `governing_references`).
- **(C) Build the authority model first — rejected as disproportionate.**
  Explicitly out of scope per IWPC-001 §31 C-1's own disclosed deferral
  and CHGR-001 §26.3(b); a categorically larger undertaking than a
  minimum-necessary amendment.
- **(D) A canonical non-fabricated sentinel value already exists —
  rejected as the direct repair.** No such string convention exists;
  inventing one risks the exact fabrication CHGR-REQ-097 forbids. The
  nearest real precedent (`governance_record_provenance.schema.json`'s
  `repository_provenance.available: false` wrapper) is informative only —
  retrofitting the field's type is disproportionate to what
  `required`-array removal already achieves.
- **(E) None found beyond (B).**

Full evaluation in
`docs/PHASE_146D_CHGR001_SEC26_AUTHORITY_BASIS_REQUIREDNESS_RESOLUTION.md`
§3.

## 3. Amendment

`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §28
(v1.2) adds:

- **CHGR-REQ-207** — `authority_basis_claimed` removed from
  `human_governance_record.schema.json`'s `required` array; becomes
  optional, like `rationale`/`conditions`/`governing_references`.
- **CHGR-REQ-208** — the CHGR-REQ-204/205 fail-closed gate additionally
  enforces CHGR-REQ-199's existing `limitations`-array disclosure
  obligation.
- **CHGR-REQ-209** — no requirement in §1–§26 (CHGR-REQ-001–206) is
  narrowed, superseded, or reworded.

Implementing files: `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`
(`required` array 18→17 entries; one property description extended);
`src/pcae/schema_resources/chgr/manifest.json` (human_governance_record
entry: `schema_version` 1.0→1.1, `file_digest` recomputed to
`1a59e2931c4e4b6c654f25823f0dc6d533e13bd015eb8bfe70e36bd878cdce58`).

**Drafting self-check, disclosed.** An initial draft also bumped the
schema file's local `contract_version` const to `CHGR-001/1.2`. Loading
the amended schema showed this is unsatisfiable: `contract_version` is
defined once in the shared `envelope.schema.json`'s `chgr_envelope`
definition and composed via `allOf` into every `records/*.schema.json`
file; a conflicting local const makes the schema unsatisfiable by any
value. Reverted before inclusion; `contract_version` remains
`CHGR-001/1.0`, matching §26.3(c)'s own precedent for the same underlying
reason. Full detail in the contract's own §28.6.1.

## 4. Verification

`src/pcae/schema_runtime/manifest.py:load_and_verify_manifest` run live
against the amended schema/manifest: **passed**, 12 entries shape-valid
and digest-matched. `required`-array diff: exactly one entry removed,
none added/reordered, every other required field/const/`$ref` unchanged.
A construction that omits `authority_basis_claimed` and discloses the
omission in `limitations` now validates against the amended schema —
CHGR-REQ-204 no longer refuses every Publication attempt permanently.
Full detail in
`docs/PHASE_146D_CHGR001_SEC26_AUTHORITY_BASIS_REQUIREDNESS_RESOLUTION.md`
§7.

## 5. Compatibility and regression review

Independently reconfirmed compatible with PEC-001 v1.1, IWC-001 v1.2,
IWPC-001 v1.4, TAMC-001/TAMPC-001 (unmodified); the three sibling record
schemas and all `shared/*.schema.json` files unmodified. No authority
leakage, no fabricated authority, no lifecycle regression, no schema
ambiguity, no identity ambiguity, no compatibility regression, no
weakening of validation (CHGR-REQ-204/205 strengthened, not weakened, by
CHGR-REQ-208). Full detail in the contract's own §28.4/§28.5/§28.7.

## 6. Governance validation

```
pcae check              -> passed
pcae health              -> healthy
pcae doctor task-memory  -> clean
pcae runtime inspect     -> Observed / observe / unavailable (unchanged)
pcae push check          -> pending_push (4 local commits; push authorized this phase)
```

No architecture-policy file (`.pcae/policy.toml`) was touched. No
strategic-lineage file (`.pcae/strategic-lineage.json`) was touched. No
sibling schema file or shared `$defs` file under
`src/pcae/schema_resources/chgr/**` was touched. No production `src/`
file outside the one named schema resource was modified.

## 7. Regression evidence

`fast_green` marker suite re-run fresh this phase: **4391 passed, 0
failed** — identical to Phase 146A's/146B's/146C's own baseline. Targeted
CHGR/publication sweep (`tests/test_chgr_schema_family.py`,
`tests/test_chgr_packaging.py`, `tests/test_chgr_authority_boundary.py`,
`tests/test_chgr_143f_independent_verification.py`, plus
`-k "chgr or publication or 146"`): 896 passed, 1 skipped, 4 failed — all
four independently confirmed pre-existing, environment-only
(`python -m build`: `No module named build`) failures, identical on
unmodified `main` HEAD via `git stash` before/after comparison, none
touching any file this phase changed.

## 8. No-go boundary — confirmations

No Publication Coordinator code (`src/pcae/governance/publication/**`)
was modified. No Interactive Workflow code
(`src/pcae/interactive_workflow/**`) was modified. No runtime file was
modified. No lifecycle sequencing was modified. No execution capability
was added. No authority ownership was changed. No implementation
planning was begun. No implementation of the CHGR-REQ-194–209
construction rules was begun or performed. No certification of Chapter
146 was performed. No sibling schema file was modified. No shared
`$defs` file was modified. No CLI command was added or changed. No
`.pcae/policy.toml` edit was made. No `.pcae/strategic-lineage.json` edit
was made. No test file under `tests/` was modified.

## 9. Final verdict

**AMENDMENT COMPLETE.** The Blocking contractual inconsistency Phase 146C
independently found (§4 of its own report) is resolved: CHGR-REQ-207
removes the schema-level contradiction, CHGR-REQ-208 closes the
disclosure-enforcement gap, and CHGR-REQ-209 confirms no prior
requirement is narrowed. One drafting error was independently caught and
disclosed, not hidden (§3 above).

## 10. Recommended next phase

**146E — CHGR-001 Authority-Basis Amendment Independent Verification** (a
recommendation, not an authorization). A future phase should
independently re-derive CHGR-REQ-207–209 from the amended contract and
schema/manifest files, mirroring Phase 146C's own role for the v1.1
revision, before any implementation phase is authorized.

## 11. Files changed

- `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` — new
  §28 (v1.2 revision) and §29 (post-revision next phase).
- `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`
  — `required` array and one property description amended.
- `src/pcae/schema_resources/chgr/manifest.json` — one entry's
  `schema_version`/`file_digest` updated.
- `docs/PHASE_146D_CHGR001_SEC26_AUTHORITY_BASIS_REQUIREDNESS_RESOLUTION.md`
  (this phase's full report, new).
- `PROJECT_STATUS.md` — Current Phase section updated, prior content
  demoted to "Phase 146C Complete".
- `CHANGELOG.md`, `tasks/DONE.md`, `tasks/done/20260728-1844-...md`
  (post-146C idle-placeholder closure), `tasks/active/20260728-1909-...md`
  → `tasks/done/...` (this phase's own task contract, closed),
  `tasks/active/20260728-1914-...md` (post-146D idle placeholder).
- `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`
  — this file.

No file under `src/pcae/governance/publication/**`,
`src/pcae/interactive_workflow/**`, `tests/`, or any sibling/shared
schema resource under `src/pcae/schema_resources/chgr/**` was modified.
