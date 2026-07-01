# Phase 106H — v0.1 RC Audit Findings Repair

## Purpose

Repair the trust-gate asymmetry between `pcae task finish --commit` and
`pcae phase complete` that Phase 106G's post-RC audit found and
empirically reproduced, so both v0.1 completion paths enforce the same
final-completeness guarantee — without weakening either, adding execution
capability, or introducing a new completion command.

## Scope

A small, targeted code change to `core/phase_report_trust.py`,
`commands/task.py`, and `commands/phase.py`; two pre-existing test
fixtures updated to include a field (`commit_attribution`) that
production metadata has always set but that these older fixtures
predated; new regression tests proving the fix; documentation updates
recording the repair. No new completion command, no runtime behavior
beyond report-trust/dispatch decision logic.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/packaging/tag-verification command behavior; no
network calls outside the existing Telegram outbound path and ordinary
git remote verification; no shell interception; no Telegram
inbound/polling; no remote shell; no `/run`; no automatic apply/apply
execution/patch parsing; no commit/push authorization changes beyond the
existing governed lifecycle; no real AI backend calls; no executable
artifact-only invocation path; no execution enablement flag or toggle; no
cryptographic signing; no remote attestation; no database-backed audit
storage; no shell mediation; no rollback execution, file mutation
rollback, or automatic restore; no git reset/checkout/revert execution;
**no new tag created**; no v0.2 implementation started.

## 106G Finding Summary

Phase 106G's audit (`docs/PHASE_106_POST_RC_SYSTEM_INSPECTION_LIFECYCLE_CONNECTIVITY_AUDIT.md`)
found that `pcae task finish --commit`'s Telegram-dispatch trust gate used
only the 105A/105B schema plus push-state fields, while `pcae phase
complete`'s gate (since Phase 105D) additionally required the OLD (95M.1)
schema's full completeness check (`validate_finalization_gate`). This was
empirically reproduced, not inferred: a synthetic report with
`files_changed=0` (otherwise complete) was dispatched by `task finish
--commit` but correctly refused by `phase complete`.

## Exact Asymmetry Observed

Reproduced again at the start of this phase, using the actual functions
(not mocks), before any code change:

```
task.py dispatch_allowed (trial_trust.complete):        True
phase.py gate[finalizable]:                              False
phase.py trust_result.complete:                           True
phase.py dispatch_allowed (gate AND trust_result):        False
gate blockers: ['files_changed missing or zero',
  "no_go_confirmations too short (0 items, require 11+ ...)",
  "report completeness is 'partial', not complete",
  'missing trust fields: files_changed']
```

`task finish --commit` never called `validate_finalization_gate` at all;
`phase complete` called it and combined its result with the 105A/105B
schema via `gate["finalizable"] and trust_result.complete`. The two
functions (`commands/task.py::_finalize_task_report_and_notify` and
`commands/phase.py::_finalize_report_and_notify`) were independent
implementations that had diverged since the Phase 105D hard-fail fix was
applied only to `phase complete`.

## Root Cause

`_finalize_task_report_and_notify()` (added in 105C, gated by push-state
in 105C.1) was never updated when 105D introduced the OLD-schema
`validate_finalization_gate()` combination for `phase complete`'s
dispatch decision. The two finalize functions had no shared trust-gate
helper, so a fix to one did not propagate to the other — precisely the
kind of drift the two independently-evolved schemas were already known to
risk (documented since 105B/105C.1/105D/106A).

## Repair Decision

**`pcae task finish --commit` remains the preferred v0.1 golden-workflow
completion command** (unchanged — this decision was not in question).

**Both `task finish --commit` and `phase complete` now enforce the
identical combined trust gate** — the OLD (95M.1) schema's full
completeness check (`validate_finalization_gate`) **and** the 105A/105B
schema plus push-state fields (`validate_phase_report_trust` +
`apply_push_state_gate`) — via a new **shared helper**,
`apply_old_schema_gate()`, added to `core/phase_report_trust.py`
alongside the existing `apply_push_state_gate()` it mirrors. Neither
command was made weaker; `task finish --commit` was brought up to
`phase complete`'s existing (correct) standard, and `phase complete` was
refactored to use the same shared helper instead of its own inline
boolean combination, removing the risk of the two diverging again in the
future.

`pcae phase complete` remains available as the documented, lower-level,
manual re-dispatch path for the post-push corrected-report case (per
Phase 106G's audit and the golden-workflow clarity note added there) — it
is not deprecated, since it still serves a real, non-redundant purpose
(re-dispatching a corrected report after `pcae push`, when `task finish
--commit` already ran pre-push and correctly deferred dispatch).

## Implementation Details

- **`core/phase_report_trust.py`**: added `apply_old_schema_gate(trust_result, gate)`
  — mutates a `PhaseReportTrustResult` in place, downgrading it to
  incomplete/partial when the OLD schema's `validate_finalization_gate()`
  found blockers, with each blocker recorded in `missing_fields` as
  `"old_schema_gate: <blocker text>"` for a clear, actionable message.
  No-op when the gate is already finalizable or absent — behaviorally
  identical to before in the already-passing case.
- **`commands/task.py::_finalize_task_report_and_notify`**: now calls
  `validate_finalization_gate(...)` (same arguments `phase complete`
  uses) for both (a) the trial-report check that decides
  `dispatch_allowed`, and (b) the post-finalize check used for the
  returned/printed `"trust"` status — then applies
  `apply_old_schema_gate()` to fold the gate into the existing
  105A/105B-plus-push-state trust result in both places.
- **`commands/phase.py::_finalize_report_and_notify`**: replaced the
  inline `dispatch_allowed = gate["finalizable"] and trust_result.complete`
  boolean with `apply_old_schema_gate(trust_result, gate); dispatch_allowed
  = trust_result.complete` — same shared helper, behaviorally identical
  outcome (verified: no existing `phase complete` test's expectations
  changed).
- **Two pre-existing test fixtures updated** (`tests/test_task_finish_report_trust_notification.py`,
  `tests/test_task_finish_notification_ordering.py`): added
  `"commit_attribution": "phase_owned"` to their shared `_write_metadata()`
  helper. This field was already required by the OLD schema's
  phase-owned-commits check (`validate_finalization_gate`) whenever
  `files_changed > 0` and `"phase_commits"` is absent from metadata — every
  real phase-completion metadata file in this project's history already
  sets it explicitly (confirmed by inspecting this project's own
  `.pcae/phase-completion-metadata.json` history); only these two
  synthetic test fixtures, written before `task finish` had this gate,
  omitted it. Adding it is a fixture correction, not a behavior weakening
  — `test_phase_report_trust_hard_fail.py`'s fixture (which exercises
  `phase complete`, already gated since 105D) already included this same
  field.

## Task Finish Behavior After Repair

`pcae task finish --commit` still never hard-fails the task-finish
command itself (task completion always succeeds regardless of report
trust — this is unchanged, by design, since task finish's job is
completing the *task*, not gating on report quality). What changed:
its **dispatch decision** (whether the report is trust-complete enough to
send Telegram as final) now requires the same full completeness standard
`phase complete` has always required. A report that would have
previously dispatched with e.g. `files_changed=0` now correctly shows
`Report notification: skipped_incomplete` with a `Missing fields:` line
listing the specific OLD-schema blocker(s).

## Phase Complete Behavior After Repair

`pcae phase complete --summary "..."` behavior is **unchanged from the
caller's perspective** — same hard-fail-by-default semantics, same
`--allow-partial-report` override, same printed output for every
previously-passing case (verified by the full existing `test_phase.py`/
`test_phase_report_trust_hard_fail.py` suites passing unchanged). The
only internal change is that its combination logic now flows through the
shared `apply_old_schema_gate()` helper instead of its own inline
boolean, for future-drift resistance.

## Report-Trust Hard-Fail Behavior

Unchanged in spirit, strengthened in coverage: `phase complete` still
hard-fails by default on incomplete/invalid trust
(`--allow-partial-report` remains the explicit, logged override); `task
finish --commit` still never hard-fails task completion, but its
Telegram-dispatch gate is no longer weaker than `phase complete`'s. No
command can mark or report final completion as trusted when required
report fields are missing under the OLD schema, the 105A/105B schema, or
push-state — all three are now consistently checked at both call sites.

## Telegram Outbound Behavior

Unchanged: outbound-only, no inbound handler anywhere in
`core/notifications.py`. Partial/incomplete reports remain suppressed
from dispatch in both commands (now consistently, per the repair above).
`.pcae/phase-reports/.last-notified.json` semantics are unchanged — still
written only by `task finish`'s successful-dispatch path, keyed on
`phase_id`+`commit`, unaffected by this repair (the marker's pre-existing
stale content from the corrected 106E dispatch, documented in 106G's
audit, is untouched here — no fabricated content was written, consistent
with 106G's decision not to hand-edit it).

## Golden Workflow Impact

No change needed to `docs/V0_1_GOLDEN_WORKFLOW.md` beyond what 106G
already added — the documented sequence (`task finish --commit` for the
golden workflow; `phase complete` for the post-push corrected re-dispatch)
remains accurate; it is now also *consistently enforced*, which is a
behind-the-scenes correctness improvement, not a workflow-shape change.

## Release Impact

Strictly positive: closes a real correctness gap in the exact guarantee
v0.1's release notes claim ("report-trust hard-fail gates"), with no
behavior change to any already-passing case. `v0.1.0-rc1`'s existing tag
and artifacts are unaffected (no new tag created in this phase).

## Residual Risks

1. `pcae push check`'s trust gate remains content-only (105D design
   decision, unaffected by this repair) and still does not incorporate
   the OLD schema's full check — a report could still show `Phase report
   trust: passed` in `push check` despite an OLD-schema-only defect.
   This is a smaller-severity, pre-existing, and separately-documented
   design choice (not part of 106G's flagged asymmetry, which was
   specifically about the *dispatch* gates); left unchanged in this
   phase to avoid overbuilding beyond the audited finding.
2. The `already_sent`/`skipped_duplicate` informational branch in
   `commands/task.py` still computes its displayed trust without the OLD
   schema fold-in — it does not gate any dispatch decision (a dispatch
   already happened), so this is cosmetic only.

## Recommended Next Phase

106I — v0.1 RC End-to-End Verification / Full Phase Check.
