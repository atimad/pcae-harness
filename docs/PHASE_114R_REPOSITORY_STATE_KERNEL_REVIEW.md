# Phase 114R — Repository State Kernel Review

## Status

Completed. Architecture review only: no runtime implementation, no
lifecycle changes.

## Purpose

The first complete architectural review of the Repository State Kernel
after Phase 114E's successful containment drill. Full design record:
`docs/PCAE_REPOSITORY_STATE_KERNEL.md`.

## Objective 1 — Kernel Completeness

The four primitives (Repository State, Repository Transition, Repository
Artifact, Repository Event) are frozen as **complete**. No additional
first-class primitive emerged from this review. Agent Lock and Task
Contract are real, distinct concepts but are session-coordination
concerns that sit alongside the kernel, not state-outcome primitives
within it (see full design doc, Model Independence Audit).

## Objective 2 — Repository Decision

**Conclusion: not promoted to a fifth primitive.** It already exists as
`TransitionResult`, the frozen four-verdict output of
`validate_transition(...)`. The brief's proposed chain (Transition ->
Validation -> Decision -> Artifact Promotion) is exactly what the code
already does; this review formalizes the vocabulary rather than
introducing a new type. Full reasoning in the design doc's "Repository
Decision" section.

## Objective 3 — Invariant Taxonomy

Reviewed every invariant across 113X–114E. Two independent enforcement
systems exist: the Repository Transition Validator's 7 structural
invariants (113T/113U) and the older finalization gate (95M.1 → 105A/
105B/105D → 113X.1/113X.2). Found:

- **No missing invariants** and **no contradictions** -- every drilled
  scenario (114E) was caught by at least one system, and no case was
  found where the two systems reached opposite conclusions.
- **Real duplication**: `recommended_next_phase` presence (checked
  twice), report completeness (checked twice, different strictness),
  push state (checked in three places, now all fed by 114C's single live
  authority), and -- the largest finding -- **phase identity has three
  overlapping validation mechanisms** (`validate_phase_identity` 113B.2,
  the `identity_conflict` hook 113X.2, and the structural invariants
  113T/113U).

Full taxonomy table and recommendation in the design doc.

## Objective 4 — Containment Across Models

**Containment does not depend on model capability.** Direct grep of all
seven kernel modules (`repository_transition_validator.py`,
`canonical_artifact_promotion.py`, `notification_certification.py`,
`push_state_reconciliation.py`, `handoff_verification.py`,
`post_push_canonicalization.py`, `repository_transition_integration.py`)
for `model_id`/`agent_id`/`backend_id`/`vendor` returned **zero matches**.
`RepositoryState` has no identity field by construction (113T/113S).
Containment for Claude, DeepSeek, Codex, GLM, humans, and future models is
identical because the mechanism has no way to distinguish them -- proven
concretely by 114E's drill, which reproduced every scenario as bare
repository state with no simulated actor at all.

## Objective 5 — Observability

Every significant transition outcome is observable via command stdout
(unconditional, 113X.1/113X.3), the canonical report's structured
fields, the 113V.N/114B dispatch marker, or `pcae agent verify-handoff`
(114D) independently re-deriving state. One intentional exception:
`pcae notify send-report --latest`/`pcae notify test` are manual,
human-invoked commands that bypass certification by design (a different
authority than automatic lifecycle dispatch). No other silent path was
found.

## Objective 6 — Authority

Exactly one authority per concern, listed and verified by direct code
inspection in the design doc's Kernel Authorities table. One honest
exception found: `RepositoryState` construction has two call sites
(`validate_phase_report_transition` for `COMPLETE_PHASE`/`FINISH_TASK`,
`certify_notification_transition` for `NOTIFY`), kept consistent by
convention/comment rather than a shared constructor -- flagged as a
follow-up candidate, not a defect (114E found no case of actual drift
between them).

## Objective 7 — Lifecycle Connectivity

Traced the complete lifecycle from Model/Human/Automation through
Repository Transition, the Validator, Decision, Promotion, State, Event,
Notification Policy, to Consumers. No disconnected path was found. The
one honest gap: Repository Event is a frozen taxonomy and policy (114B.1),
not yet a runtime type or emitter -- the "event" step today is implicit in
what `certify_notification_transition(...)` observes, not a distinct
object passed between stages.

## Objective 8 — Model Independence

Confirmed clean: zero identity-field coupling in any kernel module. The
only `agent_id` usage near the lifecycle path is agent-lock session
bookkeeping, which never reaches a kernel decision function. No
remaining coupling found.

## Objective 9 — Canonical Wire Diagram

Produced in `docs/PCAE_REPOSITORY_STATE_KERNEL.md` (Mermaid
`flowchart TD`), superseding 114B.1's diagram by making the Decision
point's four verdicts explicit and showing Reject/Quarantine/Requires-
Human-Review reaching Notification Policy directly (114B.1's own
visibility rule, not previously drawn).

## Objective 10 — Architecture Assessment

**Fundamental**: the four primitives, the four Decision verdicts, model
independence, live-state authority over declared state, and quarantine/
reject never being silent. **Implementation detail**: `RepositoryState`'s
exact fields, `verify-handoff`'s specific check set, which sinks
Notification Policy currently wires, the finalization gate's required-key
lists. **Should never be duplicated again**: phase-identity consistency
checking (three mechanisms already exist; do not add a fourth) and
push-state derivation (one function family, `reconcile_push_state`/
`compute_live_push_state`, already correctly reused by five consumers).

## Objective 11 — Future Roadmap

**Containment is complete** for the drift patterns drilled in 114E, with
no kernel-primitive gap, no model-dependent containment logic, and no
silent path found. Recommended direction: transition toward
explainability and autonomous reasoning, building on the now-formalized
Repository Decision vocabulary. Two non-blocking follow-ups carried
forward (not required before 115A): consolidate the three phase-identity
mechanisms; give `RepositoryState` one shared constructor.

## Compatibility Boundaries

This phase does not modify: the Repository Transition Validator,
Notification Certification, Canonical Artifact Promotion, Push-State
Reconciliation, Post-Push Canonicalization, `pcae agent verify-handoff`,
`pcae push`/`pcae push check`, Permission Broker, execution runtime,
authorization, plugins, Telegram inbound, REST, Web UI, or Dashboard.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused architecture/documentation tests: see final report
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 114R`: resolved, target status completed

## Recommended Next Phase

115A — Repository Decision & Explainability Architecture
