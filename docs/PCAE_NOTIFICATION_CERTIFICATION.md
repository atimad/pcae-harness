# PCAE Notification Certification

## Purpose

Notification certification is the governance step that decides whether an
external notification may be dispatched at all. Phase 114B wires the
Repository Transition Validator's `TransitionKind.NOTIFY` and
`notification_eligible()` -- both frozen since 113T/113U, but never called
from a real dispatch path until now -- into `pcae phase complete` and
`pcae task finish --commit`, the only two places a Telegram/filesystem
notification is ever sent.

Notifications are repository events, not command events, not model events,
not agent events. Exactly one certified repository transition may produce
exactly one external notification.

No lifecycle command may decide independently whether to notify. Both
callers now ask the same question, of the same function, backed by the same
validator invariant:

Transition Accepted -> Artifact Certified -> Artifact Canonical -> Notification Eligible

## Certification API

The reusable implementation lives in
`src/pcae/core/notification_certification.py`.

Primary API:

- `certify_notification_transition(...)` -- the single notification
  authority. Builds a `RepositoryState` with `artifact_state=Canonical`
  (the promotion this call follows is guaranteed, not assumed -- see
  below), constructs a `ProposedTransition(kind=TransitionKind.NOTIFY,
  ...)`, and calls `validate_transition(...)`. Returns a
  `NotificationCertification`.
- `notification_transport_status()` -- reads the same
  `PCAE_NOTIFY_ENABLED` / `PCAE_NOTIFY_SINKS` environment contract
  `finalize_phase_report()` uses for the actual dispatch attempt, so
  certification and dispatch never see a different picture of "is
  notification configured."

`certify_notification_transition(...)` is called only after the caller's
own `COMPLETE_PHASE` / `FINISH_TASK` transition already reached ACCEPT --
promotion to Canonical is therefore guaranteed by the time certification
runs, not a fabricated assumption.

## Eligibility

`NotificationCertification.eligible` is `True` only when all of the
following hold, evaluated by the validator's existing
`notification_eligibility` invariant:

- the artifact is finalized (Certified or Canonical)
- the artifact is Certified
- push is clean (`origin_main_head_count == 0`)
- notification has not already been dispatched for this phase + commit
- transport is enabled and configured (`PCAE_NOTIFY_ENABLED` plus at least
  one configured sink)

When ineligible, `NotificationCertification.outcome` names exactly one of:

| Outcome | Meaning |
| --- | --- |
| `eligible` | dispatch may proceed |
| `already_dispatched` | this phase + commit was already notified |
| `disabled` | `PCAE_NOTIFY_ENABLED` is not set |
| `transport_unavailable` | no notification sinks are configured |
| `not_certified` | some other invariant blocked the transition (e.g. push not clean, execution availability) |

`certify_notification_transition(...)` never contacts a transport. Whether
a specific configured sink (e.g. Telegram) can actually be reached is still
decided, exactly as before, by that sink's own `send()` at dispatch time --
surfaced as a dispatch failure, not a certification-time rejection.

## Idempotency

Idempotency is unchanged in mechanism and now enforced through one gate
instead of two ad hoc ones. The Phase 113V.N marker file
(`.pcae/phase-reports/.last-notified.json`, read by
`phase_already_notified(...)`, written by
`write_notification_dispatch_marker(...)` only after a dispatch attempt
actually succeeds) still records "phase_id + commit already dispatched."
`certify_notification_transition(...)` reads that marker into
`RepositoryState.notification_already_dispatched` before asking the
validator, so:

- retrying a lifecycle completion for the same phase + commit certifies
  `already_dispatched` and dispatch is skipped -- no duplicate send
- a genuinely new commit for the same phase (e.g. a report-repair
  follow-up) is not a duplicate -- the marker match requires a commit
  prefix match, so a different commit certifies eligible again
- a failed dispatch attempt never writes the marker, so retrying it is
  always certified eligible again -- retries are safe by construction,
  never producing a duplicate successful delivery

## Single Notification Authority

Before 114B, `pcae phase complete` and `pcae task finish --commit` each
built their own ad hoc "was this already dispatched" condition directly on
the marker file, with slightly different shapes (one gated only on the
marker, the other also folded in an unrelated trust-completeness check).
Both now call `certify_notification_transition(...)` and act on its
`eligible` field before invoking `finalize_phase_report(...)` -- the same
function, the same inputs, the same outcome vocabulary, for both callers.

## Failure Handling

Notification failure never invalidates canonical repository state.
`finalize_phase_report(...)` writes `latest.md` / `latest.json` before any
dispatch is attempted; a certified-but-failed dispatch (e.g. Telegram
misconfigured) leaves the canonical report exactly as written. The
idempotency marker is written only on success, so a failed attempt is
always safe to retry.

## Compatibility Boundaries

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

Successful Telegram/filesystem dispatch behavior is unchanged: a
transition that was already eligible before 114B remains eligible after
it. What changes is that push-not-clean, already-dispatched, and
transport-unavailable states -- previously handled inconsistently or not
at all on some paths -- are now uniformly certified before dispatch is
attempted.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.
