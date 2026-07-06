# PCAE Notification Policy

## Purpose

Repository Events (`docs/PCAE_REPOSITORY_EVENTS.md`) are neutral: every
completed repository transition produces exactly one, regardless of
outcome. Notification Policy is the layer that decides which of those
events are worth telling a human about, and how urgently. Repository
Events do not decide this themselves -- deciding is Notification Policy's
one job.

This phase defines the policy only. It does not implement an event bus,
an emitter, or any dispatch behavior. `certify_notification_transition(...)`
(Phase 114B) remains the current, unchanged mechanism that actually gates
Telegram/filesystem dispatch; this document describes the policy a future
implementation phase must route through Repository Events to satisfy.

Phase 116B explicitly freezes Repository Event as policy/taxonomy only for
v0.2. No v0.2 component may treat Repository Event as an implemented
runtime object, emitter, event bus, or consumer subscription API. A future
runtime Event type requires its own contract phase.

## Policy Principle

Notification Policy decides which Repository Events are externally
visible. Repository Events themselves remain neutral -- an event's
existence never implies it was, or should be, dispatched anywhere.

The governing rule, established directly from the 114B forensic finding:
**containment must not be silent when operator attention is required.**
A transition that was correctly rejected or quarantined is a successful
outcome of the Repository Transition Validator, but if the operator has no
way to learn it happened, PCAE's own correctness is unobservable from
outside the repository.

## Visibility Rules

| Event | External visibility | Rationale |
| --- | --- | --- |
| `TransitionAccepted` | Visible (existing 114B behavior) | Operator expects confirmation of forward progress |
| `TransitionRejected` | **Visible** | Containment succeeded; operator must know a transition was refused and why |
| `TransitionQuarantined` | **Visible** | Containment succeeded; operator must know a transition was held back and why |
| `TransitionRequiresHumanReview` | **Visible** | By definition requires a human; silence defeats the purpose |
| `CanonicalPromotionSucceeded` | Visible (folds into `TransitionAccepted` visibility) | Confirms durable state changed |
| `CanonicalPromotionRejected` | **Visible** | Distinct failure mode from validator rejection; still containment succeeding |
| `NotificationDelivered` | Not itself re-notified | A delivered notification does not need a notification about itself |
| `NotificationFailed` | **Visible via an alternate channel** | A failed dispatch must not be the only failure that is silent -- see Non-Circularity below |
| `NotificationSkipped` | Visible only when the skip reason itself requires attention (e.g. transport misconfigured), not for routine idempotent skips | Distinguishes "nothing to report" from "something is wrong" |
| `RetryScheduled` | Not independently visible | Informational; folds into the event it retries |

The three rows in **bold** are the direct answer to the gap 114B's
forensic verification found: rejected, quarantined, and human-review
outcomes are not optional-visibility events. They are exactly as visible
as acceptance, because containment succeeding is news the operator needs
as much as forward progress succeeding.

## Non-Circularity

`NotificationFailed` cannot be resolved by scheduling another Telegram
notification about the failure -- if the transport is what failed, notifying
through the same transport cannot be the answer. Notification Policy
requires that `NotificationFailed` be observable through a channel that
does not depend on the failed transport succeeding: at minimum, the
existing `notification_outcome`/`notification_reason` fields already
written to the phase report and printed to the command's own stdout
(Phase 113X.3, unchanged by this phase) satisfy this today. A future
implementation may add additional non-Telegram channels; it may not make
`NotificationFailed` depend solely on the transport that just failed.

## Severity, Not Just Visibility

Visibility alone does not convey urgency. Notification Policy additionally
assigns an intended severity to each visible event, for a future
implementation to carry through to however it renders a notification:

| Event | Intended severity |
| --- | --- |
| `TransitionAccepted` | informational |
| `TransitionRejected` | warning |
| `TransitionQuarantined` | warning |
| `TransitionRequiresHumanReview` | action-required |
| `CanonicalPromotionRejected` | warning |
| `NotificationFailed` | action-required |
| `NotificationSkipped` (attention-worthy cases only) | warning |

This phase freezes the severity *intent*; it does not implement rendering,
formatting, or a severity field on any runtime type.

## Future Consumer Model

In the future consumer model, additional consumers subscribe to
Repository Events (filtered through Notification Policy's visibility
rules), not to lifecycle commands directly:

- **Telegram** -- the existing sink (`src/pcae/core/notifications.py`),
  unchanged by this phase; a future implementation routes its input
  through Notification Policy-visible events instead of being called
  directly from `finalize_phase_report(...)`.
- **REST** -- not implemented; would expose visible events as a
  read-only feed.
- **Dashboard / Web UI** -- not implemented; would render visible events
  for human review, including the rejected/quarantined/human-review
  events current tooling only prints to a terminal.
- **Audit** -- would persist every Repository Event (not just the visible
  subset) as an immutable record, independent of whether it was ever
  externally notified.
- **Monitoring** -- would alert on `NotificationFailed` and
  `TransitionRequiresHumanReview` specifically, as the two
  action-required rows above.
- **Future plugins** -- register as consumers of Repository Events
  through the existing Runtime Plugin Contract
  (`docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md`), never by modifying the
  Repository Transition Validator.

Every consumer in this list is additive and future-facing: none of them
requires a change to `validate_transition(...)`,
`promote_artifact(...)`, or `certify_notification_transition(...)`.
That is the point of the Repository Event vocabulary -- later consumers
should subscribe to one event stream rather than inventing call sites
into lifecycle commands. In v0.2, that stream remains policy only.

## Non-Goals

This phase does not:

- implement a policy engine, config schema, or severity field on any
  runtime type
- change what `certify_notification_transition(...)` actually gates today
- add a REST, Dashboard, Web UI, Audit, or Monitoring consumer
- change Telegram sink behavior
- grant any execution capability

## Compatibility Boundaries

This phase does not modify:

- Notification Certification (`src/pcae/core/notification_certification.py`)
- Repository Transition Validator
- Canonical Artifact Promotion
- notification sinks or dispatch
- `pcae phase complete` / `pcae task finish --commit` runtime behavior
- `pcae push check`
- Permission Broker
- REST, Web UI, Dashboard
- Telegram inbound

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.
