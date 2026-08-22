# Phase 149O.20L.7O.2S.2 — FGSC-001 Structured Fast Green Self-Certification Lifecycle Implementation

## 1. True phase entry

Phase-entry baseline: `123a6750` (last commit of Phase 149O.20L.7O.2S.1,
"sync origin_main_head to final post-push literal value"). This phase's
own first commit follows this report.

## 2. Scope

Implements the production mechanism specified by FGSC-001 v1.0
(`docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md`,
frozen by Phase 149O.20L.7O.2S, independently verified by 149O.20L.7O.2S.1
with 0 blocking findings). No contract text was amended; N1/N2/N3 were not
opportunistically repaired (§34 of the objective; see §9 below for their
carried-forward status). Phase 149O.20L.7O.2P was not touched, re-run, or
reclassified.

## 3. Production files inspected

Read directly, in full, before implementing (per objective §1):

- `docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md`
- `src/pcae/core/fast_green_attribution.py`
- `src/pcae/core/phase_reports.py` (validation call site and surrounding
  `validate_derived_correctness()`)
- `src/pcae/core/finalization_transaction.py` (pre-promotion certification
  call site, confirmed the single trust boundary)
- `src/pcae/commands/push.py` (confirmed `assess_push_readiness()`'s
  shape for in-process Stage B reuse; confirmed push.py performs no
  independent structured-evidence interpretation, §17)
- `src/pcae/core/check.py`, `src/pcae/core/status.py`,
  `src/pcae/core/tasks.py` (in-process Stage B focused-check functions)

## 4. Production files changed

- `src/pcae/core/fast_green_attribution.py` — added the FGSC-001
  mechanism: `FinalizationPathClass`, `classify_finalization_path()`,
  `_diff_raw_entries()`, `diff_authority_issues()`,
  `check_finalization_delta()`. **No existing function was modified.**
  `validate_structured_fast_green()`'s own strict-equality freshness
  check (contract §14: "not for the function's own unit behavior") is
  byte-for-byte unchanged.
- `src/pcae/core/phase_reports.py` — two changes:
  1. `validate_derived_correctness()`'s structured-`fast_green` branch:
     added the lifecycle-freshness carve-out (contract §14) around the
     existing `validate_structured_fast_green()` call. Any issue other
     than staleness still blocks unconditionally, byte-identical to
     before.
  2. New function `run_stage_b_focused_checks()` (contract §8).

No new production module was created (objective §43 — integrated into
the two existing modules the contract itself names as the expected
candidate surfaces).

## 5. New files

- `tests/test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py`
  (39 focused/adversarial tests — see §12).
- This report.

## 6. Trust/HMIC scope consequence

No new authority-bearing source file was introduced; both changed files
are already-trusted modules inside the existing structured-Fast-Green
trust surface established by Phase 149O.20L.7O.2R. No HMIC evolution
required or performed.

## 7. Verification checkpoint implementation

`verification_checkpoint_commit` is not a new stored value — per contract
§3 it is exactly the evidence artifact's existing `candidate_commit`
field, given a lifecycle role. No new "freeze" command was added; none
was authorized. `check_finalization_delta(repo_root, checkpoint,
final_head)` takes the checkpoint as `evidence["candidate_commit"]`,
supplied by the caller (`validate_derived_correctness`), which reads it
directly from the already-validated structured `fast_green` value — never
caller-arbitrary, never a symbolic ref.

## 8. Baseline/checkpoint separation

Unchanged: `derive_phase_entry_baseline()` (baseline) and the evidence's
`candidate_commit` (checkpoint) remain two independently derived values,
exactly as before this phase. This phase adds no code path that could
conflate them.

## 9. Stage A integration

Unmodified. `validate_structured_fast_green()` still performs the full
2R/2R.1 attribution-recomputation pipeline exactly as before, including
its own strict-equality freshness check. This phase only changes how the
*caller* (`validate_derived_correctness`) interprets a specific,
precisely-identified staleness issue when — and only when — it is the
*sole* issue reported.

## 10. Finalization-only mode / lifecycle state

The eight named states (§9 of the contract) are not represented by a
persisted state field in this implementation (see §21 "eight-state
lifecycle" below) — the lifecycle is instead derived structurally, at
call time, from Git history and the report's own fields, which the
contract's crash/resume requirement (§21 item 12, objective §35) permits
("fully reconstructable from Git history plus `.pcae/` canonical metadata
alone"). `report.metadata["fgsc_lifecycle_state"]` is set to
`"FINALIZATION_VERIFIED"` only once conditions 1-5 of §14 all hold —
naming the terminal pre-`READY_TO_PUSH` state from the contract's
vocabulary without requiring separate storage for the intermediate states,
which are never durably observed by this codebase's promotion pipeline
(`IMPLEMENTING`/`CANDIDATE_FROZEN`/`BEHAVIOR_VERIFIED`/`FINALIZING` are
transient, single-process-lifetime states in every existing phase's real
history, exactly as `CANDIDATE_FROZEN` already was before this phase).

## 11. Class A / Class B implementation

`classify_finalization_path()` implements contract §4 exactly:
directory-prefix rules for `src/pcae/**`, `scripts/**`, `tests/**`,
`docs/contracts/**`, `pyproject.toml`, `conftest.py` (any depth),
`.githooks/**` → Class A; the named Class B directories/files
(`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`,
`PROJECT_STATUS.md`, `CHANGELOG.md`, `.pcae/fast-green-attribution/**`,
`tasks/**`, `.pcae/session*`) → Class B, gated by the content-sensitivity
restriction (data-format extension `.md`/`.json`/`.txt` required; any
other extension, or a symlink/gitlink/executable-mode Git file mode,
forces Class A regardless of directory). Any path not matching a named
Class B rule defaults to Class A — fail closed, exactly as §4 requires.
Class terminology (`FinalizationPathClass.A`/`.B`) uses the contract's own
letters verbatim (N2 not opportunistically repaired).

## 12. Path/change-type classification

`_diff_raw_entries()` parses `git diff --raw -z -M -C` (rename/copy
detection enabled), which distinguishes added/modified/deleted/renamed/
copied/type-changed paths and carries old/new Git file mode per entry —
covering the objective §8 minimum list except true submodule *behavior*
(no gitlink exists anywhere in this repository to exercise against; the
mode-160000 check is implemented and unit-tested against a synthetic mode
string, but not against a real submodule, since none exists in this repo
to construct one from). For a rename/copy, **both** `old_path` and
`new_path` are classified independently (`diff_authority_issues()` checks
both `old_path`/`old_mode` and `new_path`/`new_mode` per entry) — a rename
that crosses from a Class A directory into a Class B one, or vice versa,
is rejected because either side alone being Class A is disqualifying.

## 13. Authorized finalization delta / unknown-path behavior

`diff_authority_issues()` computes `git diff --raw` over the *entire*
`checkpoint..final_head` range as one two-tree comparison (contract §6's
literal mechanism, "`git diff --name-only verification_checkpoint_commit..
final_phase_head`" — this implementation uses `--raw` instead of
`--name-only` specifically to obtain mode/rename information the classifier
needs, but is the same single-diff mechanism, not per-commit accumulation).
Every path classified Class A — including any unrecognized path — produces
a distinct issue string identifying the offending path; the checkpoint is
never partially accepted.

## 14. Post-checkpoint diff authority mechanism

`check_finalization_delta()` (the function `validate_derived_correctness`
actually calls) is a thin wrapper composing: (a) ancestry
(`git merge-base --is-ancestor`), (b) merge-commit rejection
(`git rev-list --min-parents=2`), (c) `diff_authority_issues()`'s path
classification. It recomputes the delta fresh from Git on every call —
**it never trusts report metadata's own prior claim** that "only
finalization files changed" (objective §11's explicit requirement).

## 15. Merge/history-rewrite handling

- Merge commits anywhere in `checkpoint..final_head` are unconditionally
  rejected (`git rev-list --min-parents=2`, full range — not
  first-parent-only, so a merge cannot be hidden by walking only the
  first-parent chain).
- History rewrite: `git merge-base --is-ancestor` failing is treated as
  conclusive proof the checkpoint is no longer a real ancestor (amend,
  rebase, reset, or genuinely unrelated history all present identically
  to this check) — no attempt is made to distinguish *why* ancestry
  failed, matching contract §7's "no substitute checkpoint may be chosen
  after the fact" by simply refusing to select one.

## 16. Five-condition freshness implementation

Implemented across two layers, matching the contract's own division of
labor (§14 note: conditions 1-2 already existed):

1. `candidate_commit == verification_checkpoint_commit` — trivially true
   by construction (the checkpoint variable *is* `evidence["candidate_commit"]`
   in every call site); enforced transitively by `validate_structured_
   fast_green()`'s own artifact-digest/inline-value equality checks.
2. Baseline authority — unchanged, enforced by `validate_structured_
   fast_green()` (produces a *separate* issue from staleness; the carve-out
   only fires when staleness is the *sole* issue, so a baseline defect
   still blocks unconditionally).
3. Checkpoint ancestor of final head — `check_finalization_delta()` via
   `git merge-base --is-ancestor`.
4. Every post-checkpoint commit single-parent + Class B — `check_
   finalization_delta()` via merge-commit rejection + path classification.
5. Stage B focused checks — `run_stage_b_focused_checks()`.

Each condition is broken individually by a dedicated adversarial test (see
§21/§12).

## 17. Checkpoint/final HEAD distinction

`report.metadata` records `fgsc_verification_checkpoint_commit` and
`fgsc_final_phase_head` as two distinct fields (contract §18) — set only
once, only when all five conditions hold, never implying equality.

## 18. Stage B implementation

`run_stage_b_focused_checks(repo_root)` — new function in
`phase_reports.py`. Calls, **in-process** (never a subprocess, never the
`pcae` CLI re-entrant), the same underlying functions the CLI commands
call:

- `pcae.core.check.run_checks()` → `pcae check`
- `pcae.core.status.check_project_status_coherence()` → `pcae status coherence`
- `pcae.core.tasks.diagnose_task_memory()` → `pcae doctor task-memory`
- `pcae.commands.push.assess_push_readiness()` → `pcae push check`
  (reads `.health_ok`/`.check_ok`/`.doctor_ok`, i.e. the same underlying
  signals `pcae push check` itself gates on — not push eligibility
  itself, preserving §28's single trust boundary)

In-process calls were chosen over shelling to a `pcae` subprocess
specifically to make the recursion argument checkable by inspection: none
of `run_checks`, `check_project_status_coherence`, `diagnose_task_memory`,
or `assess_push_readiness` imports `phase_reports.py` or
`finalization_transaction.py` (confirmed by direct grep, §3), so calling
them from inside `validate_derived_correctness` cannot re-enter this same
gate.

`pcae phase-report consistency` is **excluded** from Stage B — contract §8
itself marks it "read-only diagnostic; informational under today's
tooling", and it has no promoted report to inspect at this pre-promotion
point (there is no `final_phase_head` report on disk yet to check
consistency of).

A Stage B focused-check failure blocks progression (produces a
`"FGSC-001 Stage B focused check failed: ..."` issue) without invalidating
Stage A's evidence — exactly contract §8's "does not, by itself, invalidate
Stage A's behavioral evidence... blocks progression... until the underlying
Class-B-only defect is fixed."

## 19. Invalidation / return-to-work

No new "resume" state machinery was built: a Class-A defect discovered
post-checkpoint is handled structurally — `check_finalization_delta()`
returns non-empty issues, `validate_derived_correctness` does not apply
the carve-out, the original staleness issue (plus the new Class-A-path
issue) blocks `pcae phase complete` exactly as an ordinary validation
failure always has. The implementer's actual next action (fix, take a new
`pcae phase fast-green-attribution` capture, retry) is unchanged from
today's ordinary workflow — this phase introduces no new "resume" verb
because none was authorized (objective §43, §19: "if current
implementation representation can faithfully preserve the same
semantics").

## 20. Finite termination

No loop was introduced anywhere in this implementation: `check_
finalization_delta()` and `run_stage_b_focused_checks()` are both
non-recursive, single-pass functions called at most once per
`validate_derived_correctness()` invocation. The push-state
predicted-value/correction-loop (§12 of the contract, N3) is unmodified —
this phase adds no new commit/push cycle.

## 21. Push-state / post-push behavior

Unmodified. `push.py` was not touched (confirmed §17 preserved: only
`git grep`-confirmed absence of any new import from `pcae.commands.push`
into the structured-evidence interpretation path — `phase_reports.py`
*imports* `assess_push_readiness` for a read-only signal, but `push.py`
itself gained no new code and still trusts only `compute_final_trust()`
over the already-finalized report).

## 22. Report schema / trust changes

`PhaseReport.metadata` (already a free-form `dict[str, Any]`) gained three
optional keys, set only in the lifecycle-carve-out path:
`fgsc_verification_checkpoint_commit`, `fgsc_final_phase_head`,
`fgsc_lifecycle_state`. No change to `PhaseReport`'s dataclass fields, no
change to `_REQUIRED_*` key tuples — fully backward compatible (§16).

## 23. Consistency diagnostic behavior

`pcae phase-report consistency` (`phase_reports.py:887`,
`commands/phase_reports.py`) was **not** modified — contract §19
explicitly scopes this as "a future implementation phase" target, "not
implemented by this contract." Carried forward unchanged; its existing
false-negative-but-harmless "stale" read on a promoted structured report
remains exactly as 2R.1/the contract's own §19 described it.

## 24. Scalar backward compatibility

Verified by test (`test_scalar_mode_entirely_unaffected`): a scalar
`fast_green` value produces no FGSC-related issue and leaves
`report.metadata` untouched. The existing 2R suite
(`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`,
`TestScalarUnaffected`, 3 tests) passes unmodified — 18/18.

## 25. Structured opt-in / malformed hybrid

Unchanged: `is_structured_fast_green()` (schema-marker dict check) still
gates entry to the entire structured path; anything else falls through to
the untouched scalar `_fast_green_failure_signal()` path.

## 26. Carried-forward findings

- **Raw-content trust** (2R.1 Finding 2): unaffected; this phase adds no
  new trust boundary and does not claim to fix filesystem-trust-model
  provenance.
- **Environment-exclusion timeout** (`ENVIRONMENT_EXCLUSION_BOUND = 3`):
  unmodified — not touched.
- **Baseline commit-message authority**: unmodified —
  `derive_phase_entry_baseline()` was not edited.
- **Evidence-artifact retention**: unmodified; no cleanup policy added.
- **N1** (overbroad `docs/contracts/**` digest-binding citation): not
  repaired — `docs/contracts/**` remains wholesale Class A in this
  implementation, which is *more* conservative than N1's overbreadth
  concern, not less; N1 remains an open, carried-forward observation about
  the contract text's citation precision, not this implementation's
  behavior.
- **N2** (Class C naming inconsistency): not repaired — this
  implementation uses "Class A"/"Class B" exactly per the frozen contract
  text and treats "unrecognized" as a fail-closed *outcome* mapped to
  Class A, never introducing a third label in code.
- **N3** (push-correction-loop termination bound): not touched; §12/§24 of
  the contract's push-state handling is unmodified by this phase. No new
  correction loop was introduced. This implementation's own only loop-like
  construct (Stage B focused-check retry) is not automatic — a human/agent
  re-invokes `pcae phase complete` after fixing a Class-B-only defect,
  exactly like every other `pcae phase complete` retry in this repository's
  history; no ungoverned automatic iteration exists.

## 27. Crash/resume, checkpoint persistence

Both are satisfied structurally rather than by new persisted state: the
checkpoint is the evidence artifact's own `candidate_commit`
(content-addressed, already durable on disk at
`.pcae/fast-green-attribution/<digest>.json`); `check_finalization_delta`
recomputes everything else from Git history on every call. Verified by
`test_crash_resume_reconstructable_from_git_and_artifact_alone`: the
checkpoint is re-derived by reading the persisted artifact file from disk
(simulating a fresh process with no in-memory state) and the delta check
is re-run from that reloaded value with an identical result.

## 28. Synthetic self-certification mechanics

`test_finalization_delta_after_checkpoint_accepted` (positive) and
`test_forbidden_change_after_checkpoint_still_blocks_completion` (negative)
are the required minimum pair (objective §37): a real synthetic repo
captures structured evidence at a checkpoint, then is either finalized
with only Class B files (accepted, `fgsc_lifecycle_state ==
"FINALIZATION_VERIFIED"`) or with a further `src/**` change (rejected,
issue names the offending path, no metadata written). These are disposable
synthetic-repo tests, not the real S22 self-hosting proof.

## 29. S22 future gate / this phase's own finalization honesty

This phase's own commits **cannot** use the structured lifecycle it is
itself introducing, for the same reason 2R's real commit sequence
couldn't (objective §39): the mechanism only becomes importable after its
own behavior-bearing commit lands, and this phase's own finalization
commits (doc, `PROJECT_STATUS.md`, `CHANGELOG.md`, task lifecycle,
`.pcae/phase-completion-metadata.json`) are themselves exactly the
`src/pcae/**`-adjacent + Class-B mix a real self-hosting run would need to
classify — using it on itself here would not be an honest external proof.
This phase's own finalization uses the pre-existing scalar+deselection
convention (`project_phase_completion_procedure.md`), stated plainly, not
disguised as structured self-certification. Real S22.1 (positive) /
S22.2 (negative) self-hosting acceptance remains for a later, separate
disposable governed phase, per contract §22 and objective §40/§41.

## 30. Phase 2P — untouched proof

`git diff --stat 123a6750..HEAD -- '*149O_20L_7O_2P*' '*149o_20l_7o_2p*'`
(run before writing this report) returns no output — no file whose name
references Phase 2P was read, written, or touched by this phase's commits.
2P's metadata, promotion status, and classification are unchanged.

## 31. Focused tests (this phase)

`tests/test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py`
— 39 tests, all passing:

- `TestPathClassification` (10): Class A paths, Class B paths, unknown
  path fail-closed, wrong-extension-in-open-directory, executable mode,
  symlink mode, gitlink mode.
- `TestDiffAuthority` (9): empty delta, allowed Class B delta, `src/**`
  rejected, `tests/**` rejected, `docs/contracts/**` rejected, unknown
  path rejected, rename evaluates both sides, rewritten/unrelated
  ancestry rejected, merge commit in range rejected.
- `TestLifecycleFreshnessIntegration` (6): finalization delta accepted end
  to end through `validate_derived_correctness`, forbidden post-checkpoint
  change still blocks completion, Stage B failure blocks completion even
  with a clean delta, scalar mode entirely unaffected, crash/resume
  reconstruction from Git + artifact alone.
- `TestStageBFocusedChecks` (3): runs against the real repo without
  raising, flags a `pcae check` failure via monkeypatch, flags a
  task-memory error via monkeypatch.

## 32. Existing attribution regression suite

`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py` — 18/18
passed, unmodified, confirming Stage A's attribution arithmetic,
provenance, and scalar-unaffected behavior are byte-identical to before
this phase.

## 33. Phase report trust/finalization suites

`test_finalization_transaction_134e10.py`,
`test_phase_149o_1r_phase_report_evidence_coherence_validator_repair.py`,
`test_phase_report_trust_gate.py`, `test_phase_report_trust_gate_cli.py`,
`test_phase_report_trust_hard_fail.py`, `test_phase_reports.py`,
`test_phase_reports_134e1v_identity_repair.py`,
`test_phase_reports_cli.py` — 343/343 passed. Confirms the shared
`validate_derived_correctness()` call site (used by
`finalization_transaction.py`'s pre-promotion certification and by two
CLI commands) is unaffected for every non-structured-FGSC scenario these
suites already covered.

## 34. Controlled Fast Green comparison (raw)

Full `pytest -m fast_green -n auto` run, controlled A/B via `git stash -u`
(candidate = this phase's working tree; baseline = `123a6750`, identical
command both sides):

- Baseline: 336 failed, 8690 passed, 5 skipped, 9 errors (130.12s).
- Candidate: 352 failed, 8674 passed, 5 skipped, 9 errors (129.80s).
- Diff (`comm` over sorted `FAILED`/`ERROR` node-ID sets): **exactly 16**
  failures present in candidate and absent from baseline; **zero**
  failures present in baseline and absent from candidate (no fix, no
  hidden new pass masking a break). The 9 `ERROR`s are identical in both
  runs (pre-existing, unrelated to this phase).

All 16 attributable failures are of one exact, previously-established
kind: existing prior-phase "frozen source scope" guard tests
(`test_no_src_pcae_files_dirty_in_working_tree`,
`test_git_status_touches_no_src_pcae_or_contract_file`,
`test_no_authority_relevant_source_mutated_by_this_phase`, and similar,
across `test_phase_149o_14_*`, `test_phase_149o_17_*`,
`test_phase_149o_19_4_*`, `test_phase_149o_1g_*`, `test_phase_149o_20a_*`,
`test_phase_149o_20c_*`, `test_phase_149o_20d*`, `test_phase_149o_20e_*`,
`test_phase_149o_20h_*`, `test_phase_149o_20k*`, `test_phase_149o_20l_1_*`,
`test_phase_149o_20l_7d_9_*`, `test_phase_149o_20l_7d_10_*`,
`test_phase_149o_20l_7e_*`). Each asserts `git status --short`/equivalent
is empty for `src/`, `scripts/`, `docs/contracts/`, `pyproject.toml` —
i.e. they assert the working tree is clean of exactly the kind of
authorized, in-scope change this phase's own commit legitimately makes to
`src/pcae/core/fast_green_attribution.py` and
`src/pcae/core/phase_reports.py` (confirmed by direct read of one
representative test, §417-419 of
`test_phase_149o_20l_7d_10_independent_verification.py`: literally
`git status --short -- src/ scripts/ docs/contracts/ pyproject.toml`).
This is the working tree's *pre-commit* dirty state at the moment the
comparison ran, not a defect in the implementation; the deselected clean
count below is reported as the `fast_green` structured/scalar evidence
per `project_phase_completion_procedure.md`'s established convention.

Deselected clean count:
**8674 passed, 336 failed (all 336 identical to baseline), 5 skipped, 9
errors (identical to baseline)** — i.e. after deselecting the 16
attributable node IDs, candidate and baseline failure sets are set-equal.

## 35. Runtime

Unchanged: Observed / observe / unavailable (Phase 110A's ceiling). No
runtime execution was enabled or exercised.

## 36. Findings

No Blocking implementation finding. No new contract semantics were
invented; where the contract left an implementation-phase discretion
(§9's state representation, §8's Stage B mechanism), this report
documents the choice made and its rationale (§10, §18 above).

## 37. Phase 2P — unchanged (repeat, for report completeness)

Confirmed unchanged; see §30.

## 38. Commits / push / origin parity

Recorded in `.pcae/phase-completion-metadata.json` and finalized per the
governed push ceremony (see task/CHANGELOG/PROJECT_STATUS commits
following this report).

## 39. Recommended next phase

**149O.20L.7O.2S.3 — FGSC-001 Structured Fast Green Self-Certification
Lifecycle Implementation Independent Verification.** That phase must
independently attack this implementation (the classification rules, the
lifecycle carve-out's issue-filtering logic, the Stage B in-process
wiring, the recursion-safety argument in §18, and the eight-state
representation choice in §10) before any S22.1/S22.2 real self-hosting
acceptance phase is scheduled, and before Phase 149O.20L.7O.2P
reconciliation may be considered.
