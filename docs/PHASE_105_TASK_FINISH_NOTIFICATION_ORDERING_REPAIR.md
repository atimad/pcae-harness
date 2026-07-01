# Phase 105C.1 — Task Finish Report Notification Ordering / Completeness Repair

## Purpose

Repair a real defect in Phase 105C's task-finish Telegram integration:
automatic dispatch fired before final push state (`pushed_status`,
`origin_main_head`, `governance_results.pcae_push_check`) was known, so the
Telegram message sent for 105C's own completion was a **partial** report —
even though prose at the time claimed the repo was "pushed and clean."

## Scope

- Gate `pcae task finish --commit`'s Telegram dispatch on the report
  actually being push-state complete, not just 105A/105B-schema "complete."
- Never send a partial report labeled as a final trusted handoff; prefer
  skipping dispatch over sending something misleading.
- Repair the idempotency marker so a skipped/partial attempt never blocks a
  later, genuinely complete send.
- Document (not silently rewrite) that 105C's own Telegram send was
  pre-final/partial.

## Non-goals

105C.1 does not implement runtime enforcement, execution, backend
invocation, adapter execution, shell mediation, Telegram inbound/polling,
rollback execution, or apply/commit/push authorization beyond what already
governs `pcae task finish --commit`. It does not add an execution enablement
flag or toggle. Telegram remains outbound-only. All authorization flags
remain False; `simulation_only`, `no_execution`, `evidence_only`,
`non_authorizing`, and `design_only` remain True where applicable.

## Original 105C intent

`pcae task finish --commit` should finalize the phase-completion report
(via the same `finalize_phase_report()` `pcae phase complete` uses),
trust-validate it with the 105A/105B validator, and dispatch outbound
Telegram notification when `PCAE_NOTIFY_ENABLED`/sinks are configured —
warning-only, never blocking task finish.

## Observed 105C Telegram problem

When 105C's own task was closed, the Telegram document actually sent
reflected:

```
report_completeness: partial
missing trust fields: pushed_status, origin_main_head, governance_results.pcae_push_check
pushed_status: not_pushed
origin/main..HEAD: 8
pcae_push_check: pending final commit
```

This happened *before* `pcae push` ran. The repo was later pushed and
clean, and prose describing the session correctly said so — but the
Telegram artifact that had already gone out did not reflect that; it
reflected the state at the moment `pcae task finish --commit` ran.

## Root cause

`_finalize_task_report_and_notify()` (105C) computed a 105A/105B trust
result and printed it as an *advisory* line, but never used it to gate
*dispatch* — dispatch happened whenever `PCAE_NOTIFY_ENABLED` and sinks
were configured, independent of trust status. Compounding this, the
105A/105B trust schema (`validate_phase_report_trust`) does not check push
state *semantically*: `pushed_status="not_pushed"` is a valid non-empty,
non-placeholder string, so the 105A/105B validator reported the 105C report
as `complete` even while the OLD (95M.1) schema's `report.report_completeness`
correctly reported `partial` with exactly the three fields above missing.
Nothing connected that correct, stricter signal to the dispatch decision.

## Final push-state fields that were missing

- `pushed_status` (was `"not_pushed"` — a valid string, not a disallowed
  placeholder, so the 105A/105B schema didn't flag it)
- `origin_main_head` (i.e. `origin_main_head_count > 0`; only the OLD
  schema checks this at all)
- `governance_results.pcae_push_check` (was `"pending final commit"`,
  again not a disallowed placeholder string)

## Why sending before final push is unsafe for a "final trusted handoff"

A Telegram document is, by design, the durable, external artifact a human
reads to know a phase is *done*. If it's sent before push state is final,
it can describe files/commits that are still local-only, claim a push
state that hasn't happened yet, or otherwise go stale the moment `pcae
push` runs afterward — exactly what happened here. For PCAE v0.1, an
automatic "final" notification must describe the actual final state, not a
snapshot mid-closure.

## Chosen repair behavior

Added `_apply_push_state_gate(trust_result, report)` in `commands/task.py`:
folds the OLD schema's push-related missing fields
(`pushed_status`, `origin_main_head`, `governance_results.pcae_push_check`)
into the 105A/105B `PhaseReportTrustResult` used for the dispatch decision,
downgrading `complete` to `False` whenever any are pending. Before
attempting dispatch, `_finalize_task_report_and_notify()` now builds a
**trial** report (via `make_phase_report()` + the same internal
`_apply_canonical_and_trust()` `finalize_phase_report()` uses — no I/O, no
dispatch) purely to compute this gated trust result *before* deciding
whether to allow dispatch:

- **Trust-gated complete** → proceed exactly as 105C did: finalize (write)
  the report and dispatch normally if configured. Marker updated on
  success.
- **Trust-gated partial/incomplete** (including "push state pending") →
  still finalize/write the report (visible, not hidden — `pcae phase-report
  show --latest` always shows the true current state), but the real
  dispatch call has `PCAE_NOTIFY_ENABLED` temporarily suppressed for that
  one call so **no sink is invoked, Telegram or otherwise**. Result status
  is `skipped_incomplete`. The idempotency marker is **not** written, so a
  later, genuinely complete finalization (e.g. after `pcae push`, metadata
  updated) can still send.

This is "prefer skip over partial send," per the repair brief: a partial
report is never dispatched as final, labeled or not.

### Was a post-push dispatch route added? (Option A vs B)

Option B was chosen: `pcae task finish --commit` remains warning-only /
pre-final validation, now correctly gated. A dedicated post-push dispatch
command is **not** added in 105C.1 — `pcae notify send-report --latest` /
`pcae phase-report trust` already let an operator (or a future 105D
finalization step) validate-then-send once push state is final, and adding
a new command for that now would be overbuilding ahead of 105D's actual
push-check integration design. This is documented as the 105D scope.

## Idempotency marker behavior

`.pcae/phase-reports/.last-notified.json` is now written **only** when a
dispatch attempt both ran (trust-gated complete) and succeeded — never for
a `skipped_incomplete` result. This means: a partial attempt never
poisons a later complete send for the same phase/commit, but a genuinely
already-sent complete report still correctly blocks a duplicate resend
(`skipped_duplicate`), unchanged from 105C.

## 105C canonical report repair/supersession status

The 105C report that was actually sent via Telegram is **not** rewritten —
that would falsify what was actually dispatched. Instead:

- This document records, verbatim, that the original 105C Telegram send was
  pre-final/partial (see "Observed 105C Telegram problem" above).
- 105C.1's own phase-completion metadata/report (created for *this* phase)
  is the first canonical report produced under the repaired ordering
  policy, and is push-state complete at the time it is dispatched (after
  `pcae push`), demonstrating the fix.
- No history is force-rewritten; no prior Telegram message is retracted
  (Telegram has no deletion/edit path in this outbound-only integration).

## Residual risks

1. The push-state gate relies on the metadata author providing accurate
   `pushed_status`/`origin_main_head_count`/`pcae_push_check` values before
   `pcae task finish --commit` runs; if metadata is written before `pcae
   push` completes (as in 105C), the correct outcome is now "skip," but the
   operator must still re-run `pcae task finish` or a future post-push path
   to actually get a complete dispatch. 105C.1 does not automate that
   re-run.
2. `.pcae/phase-reports/.last-notified.json` remains a single-slot marker
   (last dispatch only), not a full ledger — unchanged limitation from
   105C, documented there and still true here.
3. Hard-fail finalization (blocking `pcae task finish --commit` itself on
   an incomplete report, as opposed to just suppressing notification) is
   still deferred to **105D**, which should also decide how push-check
   integrates into that hard gate.

## Recommended next phase

105D — Phase Report Trust Gate Hard-Fail / Push-Check Integration. Should
build on this repair's push-state-aware trust gating to decide whether
incomplete reports (including push-pending ones) become lifecycle-blocking,
not just notification-suppressing.
