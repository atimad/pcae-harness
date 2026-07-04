# Phase 113X.1 — Finalization Gate Enforcement Repair

## Purpose

Governance repair phase, scoped to a single finding from the Phase 113X
(Cross-Agent Governance Verification) forensic audit: `validate_finalization_gate()`
correctly detects phase-identity and trust blockers, but
`finalize_phase_report()` wrote `latest.md`/`latest.json` unconditionally
regardless of the gate result. A blocked report could still become the
canonical "latest" artifact, with no persisted record of why it was
blocked, and neither `pcae push check` nor a future agent reading
`.pcae/phase-reports/latest.json` had any way to know the artifact had
been refused.

No Advisory Runtime changes. No execution capability. No Runtime
Snapshot behavior changes. Governance/report-lifecycle repair only.

## Root Cause

`finalize_phase_report()` (`src/pcae/core/phase_reports.py`) called
`write_phase_report()` unconditionally inside its try/except block. Its
callers (`_finalize_report_and_notify()` in `commands/phase.py`, and
`_finalize_task_report_and_notify()` in `commands/task.py`) both already
computed `gate = validate_finalization_gate(...)` beforehand and printed
`"BLOCKED by finalization gate"` when blockers existed — but neither
call site's `gate` result was ever passed into `finalize_phase_report()`,
so the write proceeded regardless. This was reproduced directly against
the repository's own `.pcae/phase-reports/latest.json` during the 113X
audit: `validate_phase_identity()` correctly flagged it as blocked
(`phase_id='113B'` vs. PROJECT_STATUS.md's then-current phase `'113C'`),
yet that exact file was sitting on disk as the canonical "latest" report.

## Scope

- `src/pcae/core/phase_reports.py` — `finalize_phase_report()` gains an
  optional `gate:` parameter; new `write_quarantined_report()` helper
- `src/pcae/commands/phase.py` — `_finalize_report_and_notify()` passes
  its already-computed `gate` through (except when `--allow-partial-report`
  is given — see Design Decisions)
- `tests/test_finalization_gate_enforcement.py` — 15 new tests
- `docs/PHASE_113X1_FINALIZATION_GATE_ENFORCEMENT_REPAIR.md` — this document

`src/pcae/commands/task.py`'s `_finalize_task_report_and_notify()`
(used by `pcae task finish --commit`) is deliberately **not** changed —
see Design Decisions §2.

## Implementation Summary

### 1. `finalize_phase_report(..., gate: dict | None = None)`

When the caller passes a `gate` result with `finalizable=False`, the
report is written to a quarantine path (`write_quarantined_report()`)
instead of `write_phase_report()`. `latest.md`/`latest.json` — and the
normal timestamped canonical filename — are never touched. The blocker
list is embedded directly in the quarantined artifact's JSON
(`finalization_blockers`) and Markdown (a `## Finalization Blockers`
section), so the artifact is self-describing even without the
accompanying console output.

`gate=None` (the default — used by every pre-existing caller/test that
doesn't pass it) preserves the prior unconditional-write behavior
exactly. This is what keeps existing valid-phase finalization and the
`tests/test_phase_reports.py` suite unchanged.

### 2. `write_quarantined_report(report, reports_dir, blockers)`

New function. Writes to `reports_dir / "quarantine" / "{ts}-{phase_id}.blocked.{md,json}"`.
Sets `report_completeness = "blocked"` in the persisted JSON. Never
writes `latest.*` or the normal timestamped filename.

### 3. `pcae phase complete` enforcement

`_finalize_report_and_notify()` now computes
`enforced_gate = None if allow_partial_report else gate` and passes
`gate=enforced_gate` to `finalize_phase_report()`. Console output on a
block now states plainly that `latest.md`/`latest.json` were **not**
written or overwritten, and prints the quarantine file paths. The
function's existing control flow (105D trust-gate print, notification
skip messaging, final `finalizable` return value) is otherwise
unchanged — it still falls through to `"Notification dispatch: skipped"`
exactly as before the repair.

## Design Decisions

1. **Quarantine, not silent failure.** A blocked report is still fully
   written — just not as `latest.*`. Nothing about the attempt
   disappears; it's demoted rather than discarded, per the phase's own
   instruction ("write only to a clearly non-canonical quarantine path").

2. **`pcae task finish --commit`'s report-finalization path is
   unchanged.** `_finalize_task_report_and_notify()` is documented as
   "warning-only: never raises, never blocks task finish," and its
   pre-existing, tested contract (`tests/test_task_finish_notification_ordering.py::TestReportTrustBehavior`)
   is to still write a `partial`/`incomplete` report for human
   visibility when final push state is merely pending (e.g.
   `pushed_status="not_pushed"` before a commit is pushed) — explicitly
   "no silent auto-repair," but also no disappearance behind quarantine.
   That is a different, legitimate class of "blocker" (transient,
   expected mid-workflow state) from 113X Finding 1's actual concern
   (a report whose *identity/claims are wrong*, discovered on the
   authoritative `pcae phase complete` path). Quarantine enforcement is
   scoped to `pcae phase complete`, the command Phase 105D already
   designed as the hard-fail authority.

3. **`--allow-partial-report` keeps its pre-existing override
   behavior.** This flag (Phase 105D) is an existing, tested, explicit
   human override that lets `pcae phase complete` proceed with a
   canonical write despite blockers (`tests/test_phase_report_trust_hard_fail.py::test_allow_partial_report_bypasses_hard_fail`).
   Changing that override's behavior is outside 113X.1's scope
   ("repair only the finalization enforcement gap"); the repair only
   closes the gap that existed when no override was given.

4. **`gate=None` default, not gate always computed internally.** The
   gate is still computed exactly once by each caller (unchanged), and
   passed through explicitly — avoiding a second, potentially-divergent
   gate computation inside `finalize_phase_report()` itself.

## Safety Invariants

- No Advisory Runtime changes
- No execution capability introduced or changed
- No authorization / Permission Broker changes
- No plugin, Telegram inbound, REST, or web UI changes
- Runtime state remains Observed
- Maximum plugin capability remains `observe`
- Execution availability remains unavailable

## Known Pre-Existing, Out-of-Scope Issue Found During Validation

`tests/test_rc_audit_findings_repair.py::TestAsymmetryReproduction::test_both_paths_agree_on_complete_report`
fails on a clean checkout of `5acd0499` — **before** any change in this
phase — because `validate_phase_identity()` reads the real
`PROJECT_STATUS.md` from the working directory rather than an isolated
fixture, and the synthetic report's `phase_id="999Z"` doesn't match
PROJECT_STATUS.md's real current phase. Confirmed via `git stash -u` on
top of `5acd0499` with no active task file present. This is a symptom of
the same phase-identity-source issue the 113X audit's Finding 3
identified (`_derive_phase_id()` and, here, `validate_phase_identity()`'s
direct filesystem read), not a regression introduced by 113X.1. It is
left for **Phase 113X.2 — Canonical Phase Identity Source Repair**.

## Test Coverage

15 tests in `tests/test_finalization_gate_enforcement.py`:

| Group | Tests | Focus |
|---|---|---|
| A — `finalize_phase_report()` gate enforcement | 6 | Blocked gate skips latest write, quarantine artifact has blockers, prior valid latest never clobbered, finalizable gate unaffected, `gate=None` preserves legacy behavior |
| A — `write_quarantined_report()` direct | 1 | Quarantine filenames never contain "latest" |
| B — `pcae phase complete` CLI enforcement | 6 | Identity-blocked completion doesn't overwrite a prior valid latest, non-zero exit, quarantine artifact written, no latest.* created, valid completion unaffected, `--allow-partial-report` keeps writing (unchanged), notification suppressed |
| C — push check / report trust | 1 | `read_latest_report()` still returns the last valid report, never a blocked one |

## Validation

- `python -m pytest tests/test_finalization_gate_enforcement.py -n auto -q`
- `python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_identity.py tests/test_phase_report_trust_hard_fail.py tests/test_phase_report_trust_gate_cli.py tests/test_rc_audit_findings_repair.py tests/test_task_finish_report_trust_notification.py tests/test_task_finish_notification_ordering.py -n auto -q`
- `python -m pytest -m fast_green -n auto -q`
- `pcae health && pcae check && pcae doctor task-memory && pcae push check`

## Recommended Next Phase

**113X.2 — Canonical Phase Identity Source Repair**
