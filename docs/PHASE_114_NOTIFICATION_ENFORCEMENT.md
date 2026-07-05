# Phase 114B — Notification Enforcement & Idempotency

## Status

Completed.

Phase 114B integrates notification dispatch into the Repository State
Kernel so external notifications become certified consequences of
canonical repository state. It closes the last gap in the 113U/113Y/113Z
lineage: the Repository Transition Validator's `TransitionKind.NOTIFY` and
`notification_eligible()` existed and were fully unit-tested, but nothing
on the real dispatch path ever constructed a `NOTIFY` transition or asked
the validator.

## Certification Summary

Added `src/pcae/core/notification_certification.py`, a reusable
certification module with:

- `NotificationCertificationOutcome` (`eligible`, `already_dispatched`,
  `disabled`, `transport_unavailable`, `not_certified`)
- `NotificationCertification` (eligibility result, outcome, reasons,
  transition verdict)
- `certify_notification_transition(...)` -- the single notification
  authority
- `notification_transport_status()` -- one shared read of the
  `PCAE_NOTIFY_ENABLED` / `PCAE_NOTIFY_SINKS` environment contract

## Eligibility Summary

A `NOTIFY` transition is certified eligible only when the artifact is
Certified and Canonical, push is clean, notification is enabled, transport
is configured, and this phase + commit has not already been dispatched.
All five conditions are evaluated by the validator's existing
`notification_eligibility` invariant -- unchanged since 113T, now actually
consulted.

## Idempotency Summary

Idempotency is unchanged in mechanism (the Phase 113V.N marker file) and
now enforced through one function instead of two independently-shaped ad
hoc checks. `pcae phase complete` and `pcae task finish --commit` both
call `certify_notification_transition(...)` before invoking
`finalize_phase_report(...)`. Duplicate notifications for the same phase +
commit are impossible; a new commit for the same phase is correctly
treated as not-yet-dispatched.

## Retry Summary

A failed dispatch attempt never writes the idempotency marker (unchanged
from 113V.N), so retrying it is always certified eligible again. Retrying
a crashed or interrupted lifecycle completion for the same already-
dispatched phase + commit is always certified `already_dispatched` and
skipped -- retries are deterministic and safe by construction in both
directions.

## Failure Behavior

Notification failure never invalidates canonical repository state.
`finalize_phase_report(...)` writes `latest.md` / `latest.json` before any
dispatch is attempted, regardless of certification outcome or dispatch
success. A certified-but-failed dispatch (e.g. Telegram misconfigured)
leaves the canonical report exactly as written and is observable through
the existing `notification_outcome`/`notification_reason` fields, plus a
new `Notification certification: <outcome>` diagnostic line printed
before the dispatch result on the `pcae phase complete` path.

## Compatibility Summary

This phase does not modify:

- `TelegramSink`, `dispatch()`, or any other sink implementation
- `finalize_phase_report()`'s own sink construction or dispatch attempt
- the Phase 113X.3 complete/partial-warning notification kind distinction
- `pcae push check`
- Runtime Snapshot
- Runtime Inspect
- Permission Broker
- execution runtime
- authorization
- plugins
- Telegram inbound
- REST
- Web UI
- Dashboard

A transition that was already eligible before 114B remains eligible after
it, and successful Telegram/filesystem dispatch behavior is byte-for-byte
unchanged. What changes is that push-not-clean, already-dispatched, and
transport-unavailable states are now uniformly certified before dispatch
is attempted, instead of being handled inconsistently (or, for push-not-
clean on the `pcae phase complete` path, not at all) across the two
callers.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused notification certification tests: `17 passed`
  (`tests/test_notification_certification_idempotency.py`)
- report/transition/promotion compatibility group: `328 passed`
  (repository transition validator, task-finish integration, canonical
  artifact promotion, task-finish notification ordering, 113V.N repair,
  phase report trust hard-fail, task-finish report trust notification,
  finalization gate enforcement, finalization notification guarantee,
  phase reports, notification certification)
- fast_green: see final report
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: nothing_to_push
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 114B`: resolved, target status completed

## Recommended Next Phase

114C — Push Authorization & Repository Trust Integration
