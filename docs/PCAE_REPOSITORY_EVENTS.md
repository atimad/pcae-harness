# PCAE Repository Events

## Purpose

Phase 114B's forensic verification (`docs/PHASE_114B1_REPOSITORY_EVENTS_NOTIFICATION_POLICY.md`)
established that the notification certification implemented in Phase 114B
was correct, but exposed an architectural gap: when the Repository
Transition Validator correctly quarantines or rejects a transition,
nothing tells the operator that containment worked. Containment without
observability is silent success indistinguishable from silent failure.

This phase closes that gap architecturally, not mechanically. It freezes
Repository Events as a first-class Repository State Kernel primitive and
defines the Notification Policy that decides which events become
externally visible. No dispatch behavior changes. No validator behavior
changes. No promotion behavior changes.

## The Four Repository State Kernel Primitives

The Repository State Kernel is described in terms of exactly four
primitives. Every existing and future subsystem is a consumer or producer
of one or more of them -- no subsystem invents a separate lifecycle
concept.

| Primitive | Answers | Frozen by |
| --- | --- | --- |
| Repository State | What exists right now | 113T/113U (`RepositoryState`) |
| Repository Transition | What change is proposed | 113T/113U (`ProposedTransition`, `TransitionKind`) |
| Repository Artifact | What durable evidence/state was recorded | 114A (`ArtifactState`, `promote_artifact`) |
| Repository Event | What certified outcome was announced | 114B.1 (this phase) |

- **Repository State** describes what exists: the structural snapshot a
  transition is evaluated against (`RepositoryState` in
  `src/pcae/core/repository_transition_validator.py`).
- **Repository Transition** describes a proposed change: a
  `ProposedTransition` of some `TransitionKind`, evaluated by
  `validate_transition(...)` into one of four verdicts (Accept, Reject,
  Quarantine, Requires Human Review).
- **Repository Artifact** records durable evidence/state: the promoted or
  quarantined output of a transition (`ArtifactState`,
  `promote_artifact(...)`/`quarantine_artifact(...)` in
  `src/pcae/core/canonical_artifact_promotion.py`).
- **Repository Event** announces a certified outcome: this phase's
  addition. An event is produced once a transition has been evaluated (and,
  where applicable, an artifact promoted or quarantined) -- it never
  precedes that evaluation and never substitutes for it.

Existing and future subsystems map onto these four primitives rather than
defining their own vocabulary:

- Repository Transition Validator operates on Repository State +
  Repository Transition.
- Canonical Artifact Promotion operates on Repository Artifact.
- Notification Policy (`docs/PCAE_NOTIFICATION_POLICY.md`) consumes
  Repository Event.
- Push Authorization (114C, not yet implemented) will consume Repository
  State, Repository Artifact, and Repository Event.
- Future REST, Dashboard, Web UI, Audit, Monitoring, and plugins consume
  Repository Events -- never lifecycle commands directly.

## Repository Event Definition

A Repository Event is emitted by the Repository State Kernel, once, for
every completed repository transition evaluation. "Completed" means
`validate_transition(...)` returned a verdict -- Accept, Reject,
Quarantine, or Requires Human Review are all completions; none of them are
exempt from producing an event.

Repository Events never decide anything. They describe what already
happened to repository state; they do not gate, authorize, or reverse it.
A Repository Event is emitted regardless of whether the transition was
accepted or refused -- refusal is itself a certified outcome worth
describing.

Lifecycle commands never notify directly. Models never notify. Agents
never notify. Only the Repository State Kernel emits Repository Events;
only Notification Policy decides which of those events leave the
repository.

## Repository Event Taxonomy

The following ten event types are frozen as the minimum taxonomy. Future
phases may extend it; no future phase may remove or redefine one of these.

| Event | Produced when |
| --- | --- |
| `TransitionAccepted` | `validate_transition(...)` returns Accept |
| `TransitionRejected` | `validate_transition(...)` returns Reject |
| `TransitionQuarantined` | `validate_transition(...)` returns Quarantine |
| `TransitionRequiresHumanReview` | `validate_transition(...)` returns Requires Human Review |
| `CanonicalPromotionSucceeded` | `promote_artifact(...)` promotes Certified to Canonical |
| `CanonicalPromotionRejected` | promotion is refused (source state not Certified, or promotion fails closed) |
| `NotificationDelivered` | a Notification Policy-visible event was dispatched and every sink succeeded |
| `NotificationFailed` | a Notification Policy-visible event was dispatched and at least one sink failed |
| `NotificationSkipped` | a Notification Policy-visible event was not dispatched (disabled, transport unavailable, already dispatched) |
| `RetryScheduled` | a failed or skipped notification remains eligible for a future retry attempt |

## Event Lifecycle

```
Repository Transition
       |
       v
   Validation
       |
       v
   Promotion
       |
       v
 Repository Event
       |
       v
Notification Policy
       |
       v
    Consumers
```

Validation and Promotion are the existing 113U/114A pipeline stages,
unchanged by this phase. Repository Event is a new stage that observes
their outcome. Notification Policy (`docs/PCAE_NOTIFICATION_POLICY.md`)
is the first consumer of Repository Events; Consumers are anything that
subscribes to Notification Policy's visible subset.

## Model Independence

A Repository Event must never contain:

- model identity
- backend identity
- agent identity
- vendor-specific behavior

This mirrors the Repository Transition Validator's own frozen constraint
(113T Non-Goals; 113S Section 9): the validator evaluates repository
state, never "which model/human proposed this." Repository Events inherit
that constraint by construction -- an event describes what happened to
repository state, not who caused it to happen. A Repository Event answers
"what was the certified outcome," never "who or what proposed it."

## Relationship to Containment

Phase 114B's forensic verification confirmed that quarantine/rejection
correctly prevents an invalid transition from being promoted or notified
-- containment worked. What was missing was a channel for the operator to
learn that containment worked, distinct from being told a transition
succeeded. Repository Events make every containment outcome
(`TransitionRejected`, `TransitionQuarantined`,
`TransitionRequiresHumanReview`) a first-class, describable fact rather
than an implicit silence. Whether that fact is externally surfaced is
Notification Policy's decision (`docs/PCAE_NOTIFICATION_POLICY.md`), not
this document's.

## Non-Goals

This phase does not:

- implement an `Event` dataclass, emitter, or event bus
- change `validate_transition(...)`, `promote_artifact(...)`,
  `quarantine_artifact(...)`, or `certify_notification_transition(...)`
- change any lifecycle command's runtime behavior
- change what Telegram/filesystem dispatch actually does
- add REST, Dashboard, Web UI, or Permission Broker integration
- grant any execution capability

It freezes the concept and taxonomy a future implementation phase must
conform to.

## Compatibility Boundaries

This phase does not modify:

- Repository Transition Validator (`src/pcae/core/repository_transition_validator.py`)
- Repository Transition Validator integration (`src/pcae/core/repository_transition_integration.py`)
- Notification Certification (`src/pcae/core/notification_certification.py`)
- Canonical Artifact Promotion (`src/pcae/core/canonical_artifact_promotion.py`)
- notification sinks or dispatch (`src/pcae/core/notifications.py`)
- `pcae phase complete` / `pcae task finish --commit` runtime behavior
- `pcae push check`
- Permission Broker
- REST, Web UI, Dashboard
- Telegram inbound

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.
