# Phase 114C — Push Authorization & Post-Push Reconciliation

## Status

Completed.

## Root Cause

Phase 114B's independent forensic verification found a live defect: a
genuinely pushed repository (confirmed by `pcae push check`:
`origin/main..HEAD` = 0) was quarantined by `pcae phase complete`, which
printed `pushed_status is 'not_pushed'` and `origin/main..HEAD is 6, not
0`. The cause was mechanical, not a validator bug:
`_finalize_report_and_notify` (`pcae phase complete`) and
`_finalize_task_report_and_notify` (`pcae task finish --commit`) read
`pushed_status`/`origin_main_head_count` from the declared, static
`.pcae/phase-completion-metadata.json` file, not from live git state.

`pcae phase complete`'s prior fallback (`meta.get("pushed_status", "") or
_gather_pushed_status()`) only ever consulted live git when the metadata
field was *absent* -- a present-but-stale value (e.g. `"not_pushed"`,
itself a non-empty, truthy string) always won, skipping live derivation
entirely. `pcae task finish --commit` was worse: it never attempted live
derivation at all, trusting metadata unconditionally.

## Live Push-State Authority

`src/pcae/core/push_state_reconciliation.py` makes live git state the
authority for current push state whenever it can be determined.
`compute_live_push_state()` checks whether `origin/main` resolves at all
(`git rev-parse --verify --quiet origin/main`) before trusting a
`git rev-list --count origin/main..HEAD` result -- this distinguishes
"confirmed clean" from "could not be checked," which a bare `0`/`""`
fallback cannot. Isolated repositories with no real `origin` remote (every
other fixture in this test suite, and any environment without a
configured remote) fall back to declared metadata exactly as every
finalization path did before this phase -- live authority only applies
when it is genuinely determinable.

## Reconciliation Behavior

`reconcile_push_state(metadata, live=None)` returns a
`ReconciledPushState` with a single `pushed_status`/`origin_main_head_count`
pair that both `pcae phase complete` and `pcae task finish --commit` now
use everywhere they previously read those two fields straight from
metadata. When live state is determinable, it always wins, regardless of
what metadata declares -- including when metadata optimistically claims
`"pushed"` while live state shows unpushed commits (Acceptance Criterion:
"live unpushed state still blocks when appropriate"). When live state is
not determinable, declared metadata is used exactly as before.

## Stale Metadata Handling

Every reconciliation call classifies whether declared metadata disagreed
with live state (`metadata_push_state_stale`). Both lifecycle commands
print the discrepancy unconditionally when detected -- never a silent
substitution:

```
Push state reconciliation: stale metadata detected
  metadata_push_state_stale: true
  metadata_pushed_status: 'not_pushed'
  metadata_origin_main_head_count: 7
  live_origin_main_head_count: 0
  reconciled_push_state: pushed
```

`ReconciledPushState.to_diagnostics()` exposes the same shape
programmatically for any future JSON-output caller.

## Finalization Behavior

`validate_finalization_gate(...)` and `certify_notification_transition(...)`
are unchanged -- both already accepted `pushed_status`/
`origin_main_head_count` as parameters from their callers. The fix is
entirely in what `pcae phase complete`/`pcae task finish --commit` pass
in: reconciled values, not raw metadata reads. `pcae phase complete` no
longer quarantines solely because metadata says `not_pushed` when live git
proves `origin/main..HEAD = 0`; it still quarantines correctly when live
git genuinely shows unpushed commits, even if metadata claims otherwise.

## Notification Eligibility After Reconciliation

`certify_notification_transition(...)` receives `origin_main_head_count`
from the caller, which is now the reconciled value. Its own
`notification_eligible()` push-clean check therefore reflects live state:
if Telegram is configured/enabled and the reconciled state is
certified/canonical/push-clean/not-already-dispatched, dispatch is
eligible -- closing the exact gap the 114B/114B.1 forensic verification
found (a real push could never actually result in a real notification,
because finalization never got past the stale-metadata quarantine).

## Push Authorization Integration

`pcae push check`/`pcae push` are unchanged -- this phase does not modify
the push path itself, does not implement raw git push, and does not add
new push authorization. Live push state is derived independently by
`compute_live_push_state()`, using the same `origin/main..HEAD` semantics
`pcae push check` already reports, so the two stay consistent by
construction without one calling the other.

## Repository Event Alignment

Per Phase 114B.1's frozen taxonomy, the expected event relation this
reconciliation participates in is:

```
PushSucceeded
     |
     v
PushStateReconciled
     |
     v
CanonicalReportCertified
     |
     v
NotificationEligible
```

No event bus or `Event` type is implemented in this phase (114B.1's own
non-goal, unchanged). `push_state_reconciliation.py` is the concrete
mechanism a future event-emitting implementation would call at the
`PushStateReconciled` step; today it is invoked as a plain function inside
the two finalization commands.

## Compatibility Boundaries

This phase does not modify:

- Repository Transition Validator
- Notification Certification's own eligibility logic
- Canonical Artifact Promotion
- notification sinks or dispatch
- `pcae push` / `pcae push check`
- Permission Broker
- execution runtime, authorization, plugins
- Telegram inbound, REST, Web UI, Dashboard

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Remaining Future Work

- A future phase could route `PushSucceeded`/`PushStateReconciled` through
  an actual Repository Event emission once 114B.1's event bus is
  implemented.
- `pcae push` itself could call `compute_live_push_state()` post-push to
  proactively refresh `.pcae/phase-completion-metadata.json`'s declared
  fields, rather than leaving that refresh to happen implicitly the next
  time a finalization command runs. This phase deliberately does not do
  this (Objective 2 forbids "manually edit metadata as the fix" and this
  phase's scope is finalization-time reconciliation, not proactive
  metadata rewriting).
- `compute_live_push_state()` currently only checks `origin/main`
  specifically (matching every existing push-state check in this
  codebase); a future phase could generalize it to the actual configured
  upstream branch.

## Validation

Validation completed:

- focused push/reconciliation/report/notification tests: see final report
- phase lifecycle tests: see final report
- governance/autonomy tests: see final report
- release/lifecycle regression: see final report
- fast_green: see final report
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: see final report
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 114C`: resolved, target status completed

## Recommended Next Phase

114D — Cross-Agent Verification Command
