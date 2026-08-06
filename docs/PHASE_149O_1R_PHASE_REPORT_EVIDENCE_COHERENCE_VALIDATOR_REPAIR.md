# Phase 149O.1R — Phase Report Evidence-Coherence Validator + Suppression Plumbing Repair

**Phase ID:** 149O.1R
**Mode:** cross-cutting phase-report trust implementation repair (production + tests)
**Predecessor:** 149O.1H.1R (HATP Repair Phase Evidence-Coherence / Canonical Report Trust Repair — completed, verdict `NOT REPAIRED`, root-caused the failure to two report-generation defects rather than an evidence problem)
**Date:** 2026-08-06
**Runtime boundary:** unchanged (Observed / observe / unavailable)

## 1. Why a Two-Component Bootstrap ID

`149O.1R` was deliberately chosen as a two-component ID (series `149O`, subphase `1R`) because the *pre-repair* coherence validator can already parse and match two-component identities correctly — only three-or-more-component IDs (`149O.1H.1`, `149O.1H.1R`) triggered the extraction bug. Choosing a deeper nested ID for this repair phase itself would have made the repair phase's own canonical report subject to the exact defect it exists to fix, before the fix could be promoted — a circular bootstrap dependency. This is bootstrap engineering, not a semantic shortcut: `149O.1R` still identifies this phase's place in the same `149O` trust-repair lineage.

## 2. Local Commit State at Start

Five local commits were inherited from 149O.1H.1R, unpushed:

```
e3bd1fa1 Phase 149O.1H.1R: HATP Repair Phase Evidence-Coherence / Canonical Report Trust Repair
cad1fca9 Phase 149O.1H.1R: record commit hash in phase-completion metadata
8d2c10e9 Phase 149O.1H.1R: record task-lifecycle transition (move phase task to done, open idle placeholder)
231e7e2e Phase 149O.1H.1R: hand-sync canonical phase-completion report title/phase-id
59932a9f Phase 149O.1H.1R: sync idle placeholder allowed-file scope
```

(The governing prompt for this phase stated four commits; direct `git log`/`git rev-list --count origin/main..HEAD` inspection at the start of this phase found **five** — recorded here as observed, not silently corrected to match the prompt's count.)

`pcae push check` confirmed the block: `Phase report identity: failed — Canonical phase report identifies phase '149O.1H.1', but the latest completed phase task is Phase '149O.1H.1R'... run pcae phase complete... before pushing.` This is expected input to this repair, not a cleanliness failure requiring raw push. None of these five commits were rewritten, squashed, amended, or force-pushed by this phase.

## 3. 149O.1H.1R Investigation Summary (inherited, not re-litigated)

149O.1H.1R independently re-derived every checkable technical claim in 149O.1H.1's report from source/history/fresh tests and found them coherent, but could not repair the canonical report's `internal_evidence_coherence` trust field, and stopped with verdict `149O.1H.1 CANONICAL COMPLETION TRUST NOT REPAIRED`. It root-caused this to two defects in `src/pcae/core/phase_reports.py`'s `validate_internal_report_coherence()` and the metadata-to-object plumbing, and recommended exactly this bounded repair. This phase does not re-verify 149O.1H.1's Wave-3 technical claims — that is 149O.1H.2's job, deliberately out of scope here.

## 4. Defect 1 — Baseline Reproduction

Direct simulation against the actual promoted `149O.1H.1` report JSON (`.pcae/phase-reports/latest.json` at the start of this phase) confirmed the mechanism before any edit:

```
regex "(?<![A-Za-z0-9])\d+[A-Za-z]+(?:\.?\d+[A-Za-z]*)?(?![A-Za-z0-9])" against
"Phase 149O.1H.1 repairs B-149O.1H-1" -> ['149O.1H', '149O.1H']
```

The dotted-segment group `(?:\.?\d+[A-Za-z]*)?` occurs **at most once** (a bare `?`, not `*`), so a three-component ID can only ever be truncated to its first two components. `normalized_current_id` for `149O.1H.1` (`"149O1H1"`) could therefore never appear among the extracted `evidence_phase_ids`, regardless of wording.

## 5. Canonical Phase-ID Grammar

Derived from `src/pcae/core/phase_id.py` (CPIPC-001 v1.0, Phase 137R — the repository's sole existing phase-ID authority, not re-derived from scratch):

```
phase-id        = series , branch , { "." , subphase-segment } ;
series          = digit , { digit } ;
branch          = letter , { letter } ;
subphase-segment = numeric-segment | letter-segment ;
numeric-segment = digit , { digit } , [ letter , { letter } ] ;
letter-segment  = letter , { letter } ;
```

Subphase depth is explicitly unbounded (`{ "." , subphase-segment }`, a Kleene star). `149O.1H.1`, `149O.1H.1R`, `149O.1B.3`, `135H.2`, `145H.1R` are all valid under this grammar and all parse successfully via `phase_id.parse()`.

## 6. Repaired Extraction

`validate_internal_report_coherence()` (`src/pcae/core/phase_reports.py`) now uses a new helper, `_extract_evidence_phase_ids()`, built on a new boundary-anchored candidate regex whose dotted-segment group is unbounded (`(?:\.[0-9A-Za-z]+)*`, matching the module's own grammar depth) instead of single-occurrence. Acceptance of each candidate is never re-implemented — every candidate is handed to `phase_id.parse()` (the sole grammar authority, CPIPC-REQ-018), exactly as the module's own `phase_id.scan_tokens()` does for its own callers. Comparison against the current phase uses `phase_id.equals()` (exact structural identity) instead of a dot-stripped string, and `phase_id.same_series()` (already a first-class predicate, CPIPC-REQ-043) for the "related phase" classification — no new ad hoc string-comparison rule was introduced.

This module's own `_TOKEN_CANDIDATE_RE`/`scan_tokens()` was deliberately **not** reused directly for extraction: that scanner has no boundary anchors by design (appropriate for its own call sites, which operate on a single already-known field), and reusing it unmodified here would have reintroduced the embedded-substring risk in §8. The new extractor still delegates 100% of *acceptance* semantics to `phase_id.parse()` — only the boundary-anchored candidate span is locally defined, per the "one canonical parser" preference in the governing prompt (§6).

## 7. Prefix-Collision Attacks

Verified directly against the repaired function:

```
current=149O.1H,   evidence only names 149O.1H.1 -> STILL FLAGGED (not falsely satisfied)
current=149O.1H.1, evidence only names 149O.1H   -> STILL FLAGGED (not falsely satisfied)
```

Because comparison uses `phase_id.equals()` on fully-parsed structural identities, a shorter ID can never satisfy a longer current phase's own-evidence check, or vice versa — they are simply different, unrelated-by-equality `PhaseId` values.

## 8. Boundary-Safety Attacks

```
_EVIDENCE_PHASE_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[0-9]+[A-Za-z]+(?:\.[0-9A-Za-z]+)*(?![A-Za-z0-9])")
```

Tested: `x149O.1H.1`, `149O.1H.1xyz`, `foo149O.1H.1bar`, `abc149O.1H.1def` — none extract `149O.1H.1` as a standalone token; the alphanumeric boundary lookarounds correctly refuse to pull a candidate out of the middle of a longer alnum run. Negative-grammar strings (`149O..`, `149O.1H.`, `.149O`, `149O..1H`, `149O.1H..1`, `149O/1H/1`) never extract themselves whole as a single valid token (a shorter, independently valid prefix substring may still legitimately extract — e.g. `149O` out of `149O..` — which is correct grammar behavior, not a defect).

## 9. Defect 2 — Baseline Reproduction

Traced both production paths that construct a `PhaseReport`:

- **`pcae phase complete`** → `commands/phase.py`'s `_finalize_report_and_notify()` reads `.pcae/phase-completion-metadata.json` into `meta`, explicitly pulling out `files_changed`, `tests_added_or_updated`, `validation_results`, `governance_results`, `no_go_confirmation`, `commit_attribution`, `phase_commits`, `recommended_next_phase` — but never `test_evidence_classification`. Neither the pre-check `trial_report` nor the actual `finalize_phase_report(...)` call passed it anywhere.
- **`pcae phase-report create`** → `commands/phase_reports.py`'s `run_phase_report_create()` sets `report.metadata["commit_attribution"]` and `report.metadata["phase_id"]` explicitly, but had no CLI argument at all for `test_evidence_classification` (confirmed by enumerating every `pr_create_parser.add_argument` call in `src/pcae/cli.py`).
- `finalize_phase_report()` (`core/phase_reports.py`) itself only ever read `kwargs.get("commit_attribution")` and `kwargs.get("architecture_status_snapshot")` — no `test_evidence_classification` kwarg existed to read.

Both paths independently confirmed as dropping the field before it could reach `report.metadata`, matching 149O.1H.1R's finding exactly.

## 10. Classification Plumbing Repair

- `finalize_phase_report()` now accepts `test_evidence_classification` via its existing `**kwargs` and, when truthy, sets `report.metadata["test_evidence_classification"]` — same pattern as the pre-existing `commit_attribution` handling immediately above it.
- `commands/phase.py`'s `_finalize_report_and_notify()` now reads `test_evidence_classification = str(meta.get("test_evidence_classification", "") or "")` from canonical metadata, sets it on `trial_report.metadata` (so the pre-promotion gate check sees it too, not just the final promoted report), and forwards it into the `finalize_phase_report(...)` call.
- `src/pcae/cli.py` gained one new argument, `--test-evidence-classification`, on `pr_create_parser` (no other new flag).
- `commands/phase_reports.py`'s `run_phase_report_create()` reads `args.test_evidence_classification` and sets `report.metadata["test_evidence_classification"]` when supplied.

No `--skip-trust`/`--ignore-coherence`/`--force-report` or other generic bypass was added. The only new surface is a pass-through for the field the codebase already documented (Phase 134E.9) as the sole governed suppression mechanism.

## 11. Suppression-Abuse Attacks

- **Cannot manufacture missing current-phase evidence:** a report with zero `test_results` and the classification set produces `validate_internal_report_coherence() == []` trivially (nothing to be incoherent about) but `assess_completeness()` still correctly reports non-`complete` — completeness is a wholly separate check the classification field cannot touch.
- **Cannot hide contradictory production evidence:** the `phase_id` metadata-disagreement check (`report identity … disagrees with snapshot metadata …`) fires independently of `test_evidence_classification` — verified with a report carrying the classification set *and* a deliberately contradictory `metadata["phase_id"]`; the disagreement is still flagged.
- **Cannot hide wrong phase ownership:** unchanged — the classification only suppresses the "same-series citation with no exact self-match" pattern; it never fabricates an exact self-match, and every other independent check (metadata phase-identity agreement, source-revision agreement, commit attribution) is untouched by this repair.

## 12. 149O.1H.1 Re-Evaluation

Direct simulation, reconstructing a `PhaseReport` from the actual promoted `149O.1H.1` JSON with **no edits to its evidence text**:

```
issues (repaired validator, no classification set):        []
issues (repaired validator, with 'inherited_regression'):   []
```

The repaired regex alone (§6) is sufficient — `149O.1H.1`'s own evidence text already names itself exactly (e.g. "Phase 149O.1H.1 repairs B-149O.1H-1"), so once the extractor can see three-component IDs, the exact-match check passes without needing the classification suppression at all for this specific report. No evidence text was rewritten to achieve this.

## 13. 149O.1H.1R Re-Evaluation

The same generic function, given `149O.1H.1R`'s own evidence text (which genuinely cites itself, e.g. "Phase 149O.1H.1R investigated 149O.1H.1"), likewise returns no coherence issues. This is covered as a durable, generic parametrized test case (not a phase-specific carve-out) in `tests/test_phase_149o_1r_phase_report_evidence_coherence_validator_repair.py`.

## 14. Report-Trust Regression Suites

`tests/test_phase_reports.py`, `tests/test_phase_reports_cli.py`, `tests/test_phase_report_trust_hard_fail.py`, `tests/test_push_phase_report_identity_137f1.py`: **201 passed**, no regression.

Broader finalization/PFR/quarantine/promotion/task-finish suites (`test_cltr_authority_136ap/aq/at/au`, `test_cltr_cutover_136v/w`, `test_finalization_configuration_identity_cross_agent_134b3`, `test_finalization_gate_enforcement`, `test_finalization_notification_guarantee`, `test_finalization_transaction_134e10`, `test_mutation_permission_promotion_integration`, `test_phase_113v_n_notification_finalization_repair`, `test_phase_137i1_finalization_ordering_deadlock`, `test_phase_complete_completion_metadata_shape_136aw`, `test_phase_report_trust_automation_gap_closure_design`, `test_phase_report_trust_gate`, `test_phase_report_trust_gate_cli`, `test_phase_report_view_134e3`/`134e3v`, `test_phase_reports_134e1v_identity_repair`, `test_repository_transition_validator_phase_complete_integration`/`task_finish_integration`, `test_staged_file_aware_task_finish`, `test_task_finish_notification_ordering`/`permission_non_interference`/`report_trust_notification`): **1239 passed, 12 failed**. All 12 failures independently reproduced on a clean pre-repair baseline via `git stash push -u` (sdist/wheel packaging tests requiring a build step not run in this session, plus one pre-existing finalization test unrelated to phase ID extraction or classification) — confirmed pre-existing and unrelated, not attributable to this repair.

## 15. Self-Hosted 149O.1R Finalization

See the Final Report below for the exact `pcae phase complete` transcript and outcome.

## 16. Findings

- **B-149O.1R-1** (nested phase-ID extraction truncation) — repaired.
- **B-149O.1R-2** (`test_evidence_classification` dropped before validation) — repaired.

## 17. Repair Verdict

See Final Report.

## 18. Recommended Next Phase

If self-hosting and governed push both succeed: **149O.1H.2 — HATP Proof Models + Canonical Serialization Independent Re-Verification**, per PROJECT_STATUS.md's existing recommendation, now reachable because 149O.1H.1's canonical report can be honestly re-evaluated through the repaired trust gate. This phase's own report-trust regression suites (§14) are the existing repository convention's independent-verification gate for changes to `phase_reports.py`; no additional dedicated verification phase is introduced here, consistent with existing project practice (report-trust changes have historically shipped with their own regression suite rather than a separate verification phase, e.g. 105A-105D, 134E.9).
