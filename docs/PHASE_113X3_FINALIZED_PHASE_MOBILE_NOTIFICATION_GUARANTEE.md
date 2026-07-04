# Phase 113X.3 — Finalized Phase Mobile Notification Guarantee

## Purpose

Governance repair phase, closing a problem that Phase 113X.2's own
completion directly exposed: a finalized, pushed phase produced no
Telegram notification at all, because a separate, unrelated bug forced
its report to be marked `partial`, and Phase 105D deliberately never
sends a *normal* "Phase COMPLETED" notification for a partial report.
For this project, Telegram delivery is a core mobile-operator awareness
channel, not optional decoration — a finalized phase must never simply
go silent.

No Advisory Runtime changes. No execution capability. No Runtime
Snapshot behavior changes. No Telegram inbound, REST, web UI, or plugin
changes. Governance/notification repair only.

## Root Cause (two distinct bugs)

**Bug 1 — naive lexicographic phase-ID ordering.** Both
`commands/phase.py`'s "metadata freshness guard" and
`_check_canonical_metadata_consistency()`'s "backward-pointing
recommended next phase" check compared phase IDs with `next_num[:2] ==
current[:2] and next_num < current` (string comparison). `"113D" <
"113X.2"` is `True` as strings (`'D' < 'X'`), so recommending `113D`
from `113X.2` — a valid transition off the `113X` exceptional
governance-repair branch back to the lettered mainline — was flagged
as "pointing backward." This forced 113X.2's own completion through
`--allow-partial-report`, leaving its `report_completeness` as
`partial`.

**Bug 2 — no notification guarantee for a finalized-but-partial
report.** Once a report is `partial`, `pcae phase complete` cleared
`PCAE_NOTIFY_ENABLED` before calling `finalize_phase_report()`,
suppressing *all* notification — even though the report's canonical
`latest.md`/`latest.json` had still been written (via
`--allow-partial-report`). The operator received no signal whatsoever
that a phase had finalized and pushed.

## Scope

- `src/pcae/core/phase_reports.py` — `is_phase_id_backward()` and
  `_parse_phase_id_shape()` (branch-aware phase-ID comparison);
  `NOTIFICATION_OUTCOME_*` constants and `_classify_notification_outcome()`;
  `finalize_phase_report()` gains `report_is_complete:`/`report_incomplete_reason:`
  parameters and decides the notification *kind* itself
- `src/pcae/commands/phase.py` — uses `is_phase_id_backward()` instead
  of naive string comparison; removes the `PCAE_NOTIFY_ENABLED`-clearing
  suppression hack, passing `report_is_complete`/`report_incomplete_reason`
  instead; updated dispatch-result printing
- `src/pcae/core/notifications.py` — new
  `phase_report_to_partial_warning_notification_event()`
- `tests/test_finalization_notification_guarantee.py` — 17 new tests
- `tests/test_phase_report_trust_hard_fail.py` — one pre-existing test
  updated (it asserted the exact old-and-now-intentionally-changed
  "always silent for partial" behavior)
- `docs/PHASE_113X3_FINALIZED_PHASE_MOBILE_NOTIFICATION_GUARANTEE.md` — this document

## Implementation Summary

### 1. Branch-aware phase-ID comparison

`_parse_phase_id_shape(phase_id)` parses an ID into `(series, branch,
subphase)` — e.g. `"113X.2"` → `("113", "X", (2,))`. `is_phase_id_
backward(next_id, current_id)` returns `True` only when both IDs share
the same series and are both on the mainline or both on the `"X"`
exceptional branch, and `next_id` is a genuinely earlier `(branch,
subphase)` position. IDs on different kinds of branch (mainline vs.
`"X"`) are treated as **not comparable** — never flagged backward —
rather than guessed at with string comparison. Both pre-existing
call sites (`commands/phase.py`'s freshness guard,
`_check_canonical_metadata_consistency()`'s check #6) now share this
one helper instead of duplicating the (buggy) logic.

### 2. Notification outcome model

Four explicit outcomes (`NOTIFICATION_OUTCOME_ATTEMPTED` / `_SENT` /
`_SKIPPED_WITH_REASON` / `_FAILED_WITH_REASON`), classified by
`_classify_notification_outcome()` and always recorded on `finalize_
phase_report()`'s return value (`notification_outcome`, `notification_
reason`, `notification_kind`) and on `report.notification_result`. "Was
the operator told, and if not, why" is always answerable without
reading console output.

### 3. `finalize_phase_report(..., report_is_complete, report_incomplete_reason)`

- `report_is_complete=None` (default — every caller that doesn't pass
  it, notably `pcae task finish --commit`) preserves the exact prior
  behavior: always the normal "Phase COMPLETED" event, gated only by
  `PCAE_NOTIFY_ENABLED`/sinks, completely unaffected by this phase.
- `report_is_complete=True` (passed by `pcae phase complete` when trust
  is complete) → normal event, unchanged.
- `report_is_complete=False` (passed by `pcae phase complete` when
  trust is incomplete, including the finalized-but-partial-via-
  `--allow-partial-report` case) → `phase_report_to_partial_warning_
  notification_event()`: a distinctly different event — title
  `"PHASE FINALIZED BUT REPORT PARTIAL — mobile operator attention
  required"`, forced `SEVERITY_WARNING`, includes `report_incomplete_
  reason` — dispatched to whatever sinks are configured. Never the
  normal event; 105D's rule that partial reports are not sent as
  normal final reports is preserved by construction (a different
  event, not a suppressed one).
- Blocked/quarantined reports (113X.1) are **unchanged**: still fully
  silent, since canonical `latest.*` were never written for them. This
  keeps 113X.1's "do not weaken quarantine semantics" guarantee intact;
  the mandatory guarantee below applies only when canonical artifacts
  are actually updated.

### 4. `commands/phase.py` integration

The `PCAE_NOTIFY_ENABLED`-clearing suppression hack and the now-dead
`_notification_skip_reason()` helper are removed entirely. `dispatch_
allowed` (unchanged) is passed straight through as `report_is_complete`,
with a `report_incomplete_reason` built from `trust_result.summary`/
`missing_fields`. Console output now prints `(PARTIAL WARNING — mobile
operator attention required)` alongside the dispatch line whenever
`notification_kind == "partial_warning"`.

## Design Decisions

1. **The guarantee is scoped to canonical-artifact-updating
   finalizations**, matching the brief's own wording ("if PCAE
   finalizes a phase and updates canonical final report artifacts").
   Blocked/quarantined reports (113X.1) never update `latest.*`, so
   they remain outside the mandatory guarantee — optional per the
   brief, and left silent here to avoid weakening quarantine semantics
   and to avoid touching a large existing "quarantine = silent" test
   suite for a nice-to-have.
2. **`pcae task finish --commit`'s notification path is untouched.**
   Per 113X.1/113X.2 precedent, that path is documented and tested as
   warning-only visibility, a different concern from `pcae phase
   complete`'s authoritative finalization.
3. **One shared branch-aware helper, not two independent fixes.** Both
   pre-existing "backward-pointing" checks now call `is_phase_id_
   backward()` rather than each keeping its own (buggy) comparison.
4. **`report_is_complete=None` defaults to unconditional "complete"
   kind, not a `report.report_completeness`-derived guess** — verified
   directly: deriving it from `report.report_completeness` would have
   silently reclassified plenty of legacy/bare `finalize_phase_report()`
   calls (whose minimal `PhaseReport`s are `partial` by the 92D.5
   schema's own reckoning) as `partial_warning`, when the pre-113X.3
   code never looked at that field for this decision at all.

## Safety Invariants

- No Advisory Runtime changes
- No execution capability introduced or changed
- No Runtime Snapshot behavior changes
- No Telegram inbound, REST, web UI, or plugin changes
- Runtime state remains Observed
- Maximum plugin capability remains `observe`
- Execution availability remains unavailable
- 113X.1 quarantine semantics unchanged (blocked reports remain fully silent, never overwrite `latest.*`)
- 113X.2 identity-conflict enforcement unchanged

## Known Pre-Existing, Out-of-Scope Issues (not caused by this phase)

Reconfirmed unrelated to this phase's changes:

- `tests/test_rc_audit_findings_repair.py::TestAsymmetryReproduction::test_both_paths_agree_on_complete_report`
  and `tests/test_bootstrap_todo_consistency.py::test_recommended_next_phase_matches_real_project_status`
  / `::test_real_todo_not_flagged_stale_against_real_project_status` —
  already documented in 113X.1/113X.2 (tests hardcoded against literal,
  ever-advancing real repo state).
- `tests/test_project_state.py::test_project_state_no_repository_files_created`
  — failed once under the full `-n auto` run, passed cleanly in
  isolation; consistent with this codebase's own previously-documented
  xdist parallel-worker races on shared repository/filesystem state
  (e.g. the 107C combined-regression note). Not caused by this phase's
  changes — nothing here touches `project-state`.

## Test Coverage

17 tests in `tests/test_finalization_notification_guarantee.py`, plus
one updated pre-existing test:

| Group | Tests | Focus |
|---|---|---|
| Notification outcome model (direct) | 4 | `finalize_phase_report()`'s return value across complete/partial/disabled/legacy-caller cases |
| Branch-aware phase-ID ordering | 3 | `113D` from `113X.2` not backward; genuine mainline regression still caught; end-to-end `pcae phase complete` stays `complete` |
| Complete report still notifies normally | 1 | Normal event, no partial-warning label |
| Partial-but-finalized sends warning | 3 | Clearly labeled, distinct event/title/severity, reason included |
| Skip/failure recorded with reason | 2 | Notify-disabled and sink-failure cases |
| Quarantine behavior intact | 1 | Blocked reports remain silent and unwritten |
| Identity-conflict blocker intact | 1 | 113X.2 behavior unchanged |
| Latest never overwritten by blocked | 1 | 113X.1 behavior unchanged |
| Deterministic, no network calls | 1 | Filesystem sink only |

## Validation

- `python -m pytest tests/test_finalization_notification_guarantee.py -n auto -q`
- `python -m pytest tests/test_finalization_gate_enforcement.py tests/test_canonical_phase_identity_repair.py tests/test_phase_reports.py tests/test_phase_report_trust_hard_fail.py -n auto -q`
- `python -m pytest -n auto -q` (full suite)
- `python -m pytest -m fast_green -n auto -q`
- `pcae health && pcae check && pcae doctor task-memory && pcae push check`

## Recommended Next Phase

No new phase is required by this repair. All three 113X forensic/
follow-on findings (Finding 1 in 113X.1, Finding 3 in 113X.2, the
notification-silence gap discovered during 113X.2's own completion) are
closed. Return to normal PCAE roadmap development at **113D — Advisory
Runtime Verification & Compatibility**.
