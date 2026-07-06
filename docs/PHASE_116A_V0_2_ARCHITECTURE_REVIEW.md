# Phase 116A — v0.2 Architecture Review & Consolidation

## Status

Complete.

This was a review and consolidation phase only. No runtime capability,
execution path, authorization behavior, Permission Broker behavior,
Repository Skill, Advisory Provider, Evidence Provider, Decision
Evaluation behavior, Repository Transition Validator behavior, lifecycle
command behavior, Notification Policy behavior, Telegram inbound path,
REST endpoint, Dashboard, Web UI, or model integration was implemented.

## Purpose

Phase 116A performed the first complete architectural review of the
v0.2 platform after the Advisory subsystem hardening completed in 115Z.
The review checked internal consistency, responsibility boundaries,
extension points, naming, wire diagrams, implementation-vs-contract
alignment, and remaining architectural debt before deciding whether the
v0.2 architecture is ready to freeze.

## Overall Assessment

**Architecture requires minor consolidation.**

The v0.2 architecture is internally coherent and does not require
significant redesign. The major subsystems now form a single
state/evidence/decision/promotion/notification architecture with clear
authority boundaries:

- Runtime remains an observation-only coordination architecture.
- Repository State Kernel owns the four primitives: State, Transition,
  Artifact, and Event.
- Repository Transition Validator is the only transition verdict
  authority.
- Evidence Providers and Repository Skills produce evidence only.
- Decision Evaluation centralizes invariant evaluation and
  explanations.
- Advisory Providers and Advisory Repository Skills produce
  model-labelled evidence only, behind Prompt Builder, Normalizer, and
  Evidence Builder boundaries.
- Notification Certification is the single notification-dispatch
  eligibility authority for lifecycle-driven outbound notifications.

No hidden execution authority was found. `pcae runtime inspect --json`
reported `execution_availability: "unavailable"`, current runtime state
`Observed`, and maximum plugin capability `observe`.

The reason this review does not declare the architecture ready to freeze
immediately is limited, known consolidation work: overlapping
phase-identity/finalization checks, duplicate report-completeness and
recommended-next-phase enforcement, two independent `RepositoryState`
construction call sites, and the conceptual Repository Event layer not
yet materialized as a runtime type. These are minor consolidation items,
not architectural contradictions.

Recommended next phase: **116B — v0.2 Architecture Consolidation**.

## Subsystem Review

| Subsystem | Assessment | Notes |
| --- | --- | --- |
| Runtime | Consistent; freezeable after minor consolidation elsewhere | `PCAE_RUNTIME_ARCHITECTURE.md`, Runtime Registry, Introspection, Context, and Snapshot contracts all keep execution unavailable and the current ceiling at `Observed`. Runtime plugins are defined as contracts/categories, not loading or execution capability. |
| Governance | Consistent | Health/check/push/task-memory/handoff/session commands remain governance and verification surfaces, not execution authority. Agent identity is used for lock/session coordination only, not for Repository Decisions. |
| Repository State Kernel | Consistent, with minor consolidation debt | Four primitives remain complete. Repository Decision correctly remains `TransitionResult`, not a fifth primitive. Known overlap in identity/finalization checks should be consolidated before freeze. |
| Repository Transition Validator | Consistent | `validate_transition(...)` remains the only transition verdict authority. It consumes repository facts and invariants, not model identity or prose. |
| Evidence Framework | Consistent | Evidence is evaluation-scoped, structured, labelled by category/confidence/freshness/determinism, and not a kernel primitive. Raw evidence persistence remains future work. |
| Decision Evaluation | Consistent | Decision Evaluation consumes `EvidenceCollection`, evaluates invariants, and emits structured explanations. Providers and skills do not decide or vote. |
| Repository Skills | Consistent and extensible | The skill contract correctly positions skills as evidence producers. Deterministic and advisory skills share one `EvidenceCollection` path. Stage 4 migration, where providers become fully internal to skills, remains future work. |
| Advisory Providers | Consistent and extensible | `AdvisoryProvider` remains swappable behind one `invoke(request) -> RawAdvisoryResponse` boundary. Same-model default is documented and second-provider implementation is intentionally deferred. |
| Advisory Context Package | Consistent | The package has 15 required sections, four trust classes, prompt-injection separation, size budgets, redaction summary, provenance, artifact references, and one allowed question. It is implemented but not wired into the live advisory pipeline. |
| Reporting | Consistent, with minor consolidation debt | Canonical report promotion is gated through certified/canonical artifact handling. Older finalization-gate checks still overlap with newer structural invariants. |
| Notifications | Consistent | Notification Policy describes event visibility; Notification Certification is the lifecycle dispatch eligibility authority. Manual `pcae notify send-report` and `pcae notify test` remain explicit human-invoked exceptions, not hidden lifecycle paths. |
| Phase lifecycle | Consistent | `pcae phase complete` and `pcae task finish --commit` both route phase-report promotion and notification eligibility through shared validator/certification flows. No lifecycle command gained execution or authorization capability. |

## Boundary Review

### Single Responsibility

The architecture assigns one primary responsibility per major layer:

- Runtime: future sequencing and state visibility.
- Permission Broker: evaluate-only policy decision for future execution,
  still execution-unavailable.
- Repository State Kernel: define canonical repository primitives.
- Repository Transition Validator: validate proposed repository
  transitions.
- Decision Evaluation: evaluate evidence against invariants and explain.
- Evidence Providers: collect evidence.
- Repository Skills: orchestrate/enrich evidence.
- Advisory Providers: produce untrusted raw advisory output.
- Normalizer/Evidence Builder: convert valid advisory output into
  ordinary evidence.
- Artifact Promotion: promote only certified artifacts.
- Notification Certification: decide whether a lifecycle notification may
  dispatch.
- Notification sinks: deliver after certification; they do not certify.

No subsystem was found owning another subsystem's authority.

### Overlapping Ownership

Four overlaps remain:

1. Phase identity is checked by `validate_phase_identity`,
   `identity_conflict`, and structural invariants.
2. Report completeness is checked by both the structural invariant path
   and the legacy finalization gate.
3. Recommended-next-phase presence is checked by both structural
   invariants and the legacy finalization gate.
4. Push state is derived centrally by reconciliation helpers but still
   consumed by multiple downstream checks.

These overlaps are consistent in conclusion, but they are duplicated
ownership and should be consolidated before v0.2 freeze.

### Duplicated Abstractions

No duplicate top-level architecture was found. The review explicitly
confirmed that:

- Repository Decision is not a new primitive; it is `TransitionResult`.
- Evidence is not a kernel primitive; it remains evaluation-scoped.
- Advisory Runtime, Advisory Repository Skills, and the older Phase 88X
  advisory mode are separate historical scopes, not competing authority
  paths.
- Runtime plugin contracts are extension categories, not another
  execution implementation.

### Circular Dependencies

The reviewed dependency direction is coherent:

- Evidence defines shared evidence objects.
- Evidence Providers depend on Evidence.
- Repository Skills depend on Evidence Providers and Evidence.
- Advisory Repository Skills depend on Repository Skills and Evidence.
- Decision Evaluation depends on Evidence only.
- Repository Transition Validator depends on Decision Evaluation output
  and Evidence, not on providers or skills.
- Notification Certification depends on the Validator.

No required architectural cycle was found. The Advisory Context Package
implementation remains especially isolated: it has no internal `pcae`
imports.

### Hidden Authority

No hidden authority was found. Specifically:

- No Repository Skill or Advisory Repository Skill decides, authorizes,
  mutates, promotes, pushes, commits, finalizes, notifies, or executes.
- No Evidence Provider decides, authorizes, mutates, promotes, notifies,
  or executes.
- No Advisory Provider returns trusted PCAE objects directly.
- No Notification sink decides lifecycle eligibility.
- No model identity changes validator behavior.

## Extension Point Review

| Extension point | Completeness | Extensibility assessment |
| --- | --- | --- |
| Repository Skills | Complete enough for v0.2 architecture | Manifest, determinism, capability classes, failure behavior, safety prohibitions, composition, and merge semantics are documented and prototyped. Remaining Stage 4 provider encapsulation is a future migration, not a contract gap. |
| Advisory Providers | Complete enough for v0.2 architecture | Provider/request/raw/normalized abstractions, same-model default, split-model future mode, Normalizer, Evidence Builder, failure behavior, and swappable backend diagram are complete. Future providers can be added without Decision Evaluation or Validator redesign. |
| Evidence Providers | Complete enough for v0.2 architecture | Four deterministic providers exist, and the contract keeps providers evidence-only. Additional providers can add categories without changing Decision Evaluation authority. |
| Runtime Plugins | Contract-complete, implementation-deferred | Ten categories and capability taxonomy are documented. The registry reports zero registered plugins and execution remains undeclarable/unavailable. This is acceptable for v0.2 because runtime plugin loading is explicitly deferred. |

## Naming Consistency

Terminology is consistent across the reviewed docs, contracts, and code:

- `Repository State`, `Repository Transition`, `Repository Artifact`,
  and `Repository Event` are the four kernel primitives.
- `Repository Decision` is a named computation/result, not a primitive.
- `TransitionResult` and the four verdicts (`ACCEPT`, `REJECT`,
  `QUARANTINE`, `REQUIRES_HUMAN_REVIEW`) are consistently used as the
  validator outcome.
- `Evidence`, `EvidenceCollection`, `EvidenceProvider`, and
  `RepositorySkill` are consistently evidence-producing concepts.
- `AdvisoryProvider`, `AdvisoryRequest`, `RawAdvisoryResponse`, and
  `NormalizedAdvisoryResponse` are consistently advisory-only model
  boundary concepts.
- The single pilot advisory question remains exactly
  `"Is the repository state internally consistent?"`.
- Runtime state remains `Observed`, execution availability remains
  `unavailable`, and maximum plugin capability remains `observe`.

One naming caveat remains: `Repository Event` is used consistently as a
kernel primitive/policy vocabulary, but it is not yet a runtime type.
That is documented and intentionally deferred.

## Wire Diagram Review

The reviewed Mermaid and text diagrams accurately reflect the current
architecture:

- `PCAE_REPOSITORY_STATE_KERNEL.md` shows the lifecycle from actor to
  Transition, Validator, Decision, Artifact Promotion, State, Event,
  Notification Policy, and Consumers. The diagram honestly marks
  Repository Event as policy/taxonomy rather than a runtime type.
- `PCAE_DECISION_FRAMEWORK.md` correctly shows Evidence Providers
  feeding Evidence, Decision Framework, Validator, Transition Result,
  Artifact, Event, Notification Policy, and Consumers.
- `PCAE_REPOSITORY_SKILLS_ARCHITECTURE.md` correctly inserts Repository
  Skills before Evidence Collection while preserving the single
  Decision Evaluation path.
- `PCAE_REPOSITORY_SKILLS_INTEGRATION_ARCHITECTURE.md` correctly shows
  deterministic and advisory skills as parallel implementations under
  Repository Skills.
- `PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md` and
  `PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md` correctly show Prompt
  Builder, Advisory Provider, Raw Response, Normalizer, Evidence Builder,
  Evidence Collection, Decision Evaluation, and Validator.
- `GOVERNANCE_LIFECYCLE_DIAGRAM.md` correctly marks governed execution
  as future and not started.

No wire diagram claims implemented execution, authorization, REST,
Dashboard, Web UI, Telegram inbound, or model integration.

## Architectural Debt Classification

### Must Fix Before v0.2

None found.

No issue found in this review requires significant redesign or blocks
continued v0.2 consolidation. Execution remains unavailable and no
authority leakage was found.

### Recommended Before v0.2

1. **Consolidate overlapping phase-identity checks.**
   Three mechanisms currently cover related identity concerns. The
   structural invariants should become the single long-term authority.

2. **Consolidate duplicated finalization/report checks.**
   Report completeness and recommended-next-phase checks exist in both
   the structural invariant path and the legacy finalization gate. The
   unique finalization-gate checks should be migrated to first-class
   invariants, then duplicate checks retired.

3. **Introduce one shared `RepositoryState` construction helper.**
   `validate_phase_report_transition(...)` and
   `certify_notification_transition(...)` build similar
   `RepositoryState` objects independently. They agree today, but a
   shared constructor would make the authority structural rather than
   discipline-based.

4. **Materialize Repository Event as a type or explicitly freeze it as
   policy-only for v0.2.**
   The Event layer is a canonical primitive and notification-policy
   vocabulary, but not yet a runtime object. v0.2 should either create a
   minimal event representation or explicitly freeze the policy-only
   status.

### Future Enhancement

- Wire `AdvisoryContextPackage` into a future advisory pipeline.
- Add additional advisory questions such as documentation, report,
  architecture, code, or security review after separate contract phases.
- Add a second Advisory Provider only when independent-review benefit
  outweighs complexity/cost/reproducibility risks.
- Complete Repository Skills Stage 4 by making Evidence Providers fully
  internal implementation details behind skills.
- Add runtime plugin loading, REST, Dashboard, Web UI, inbound Telegram,
  audit persistence, rollback, emergency stop, or execution only under
  separately approved future phases.

### Intentionally Deferred

- Runtime execution and authorization.
- Permission Broker enforcement changes.
- Execution Adapter, Audit Plugin, Storage Plugin, Identity Plugin, and
  full Plugin Registry implementation.
- Notification Policy runtime event bus.
- Telegram inbound.
- REST, Dashboard, and Web UI.
- Model/backend integrations.
- Raw evidence persistence.
- Automatic redaction scanning inside `AdvisoryContextPackage` itself;
  the assembler remains responsible for redaction before package
  construction.

## Implementation Consistency

Prototype implementations remain consistent with frozen contracts:

- Runtime Registry/Introspection/Context/Snapshot report
  execution-unavailable posture and do not execute.
- Evidence and Evidence Providers implement the evaluation-scoped
  evidence contract.
- Decision Evaluation consumes Evidence only and centralizes invariant
  explanations.
- Repository Transition Validator remains the verdict authority and
  includes execution-unavailable invariant coverage.
- Repository Skills wrap deterministic providers and produce
  `EvidenceCollection`.
- Repository Skills integration helpers provide provider/skill evidence
  collection without changing lifecycle behavior.
- Advisory Repository Skills implement request/response normalization,
  failure handling, and evidence building without lifecycle authority.
- Current Acting Model Advisory Provider is a contained provider
  implementation, not a backend/model integration beyond the current
  acting model abstraction.
- Advisory Context Package implements bounded sections, trust classes,
  size budgets, redaction summary, provenance, artifact references, and
  JSON-compatible serialization while remaining unwired.
- Notification Certification gates lifecycle notification eligibility
  before dispatch and does not contact transports itself.

## Validation

Architecture/documentation verification only. Required governed
validation commands for the phase:

- `pcae health`
- `pcae check`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae agent verify-handoff`
- `pcae session bootstrap --compact --profile implementation`
- `pcae runtime inspect --json`
- `pcae notify status`
- `pcae skill invoke phase-finalization 116A`

## No-Go Confirmation

Phase 116A did not implement runtime capability, execution,
authorization, Permission Broker changes, Repository Skills, Advisory
Providers, Evidence Providers, Decision Evaluation changes, Repository
Transition Validator changes, lifecycle command changes, Notification
Policy changes, Telegram inbound, REST, Dashboard, Web UI, or model
integrations.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

116B — v0.2 Architecture Consolidation.
