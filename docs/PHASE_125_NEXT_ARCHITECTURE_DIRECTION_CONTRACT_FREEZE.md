# Phase 125B - Next Architecture Direction Contract Freeze

## 1. Purpose

Phase 125B freezes the canonical decision contract for evaluating
PCAE's next architectural direction following the completed Repository
Intelligence chapter (Tracks 119-124).

This contract governs **architectural decision making only**. It does
not select the next implementation track. Phase 125A evaluated six
candidate directions and recommended Dependency Knowledge Graph as a
suggested first evaluation candidate for future work; that remains a
recommendation, not a decision, and this contract does not convert it
into one. Selecting an implementation path remains explicitly out of
scope for this document and for every phase this document binds.

This contract is binding for:

- 125C - Next Architecture Direction Contract Verification;
- 125D - Next Architecture Direction Plan;
- 125E - Next Architecture Direction (implementation-track phase,
  scope to be defined once a direction is selected under this
  contract's process);
- 125F - Next Architecture Direction Verification.

125B is documentation only. It creates no source code, no test code,
no schema, no generator, no query capability, no consumer, no runtime
plugin, and no execution capability. It implements no candidate
direction named in Section 4.

## 2. Contract Authority

This document is the canonical Track 125 next-direction decision
contract unless explicitly superseded by a future governed
contract-amendment phase.

Later Track 125 phases may verify, plan, and — if and when a direction
is formally selected through the process this contract defines —
implement only inside this contract's constraints. No later phase may
silently reinterpret this contract as authorizing capability expansion,
runtime behavior change, execution capability, or selection of an
implementation path without completing the decision sequence in
Section 6.

## 3. Scope

This contract governs **evaluation and selection process**, not
outcome. It applies to:

- how candidate architectural directions are evaluated;
- what evaluation principles a candidate must be assessed against;
- what must be true before an implementation path may be selected;
- how Repository Intelligence must be preserved during evaluation;
- what remains deferred regardless of which direction is eventually
  selected.

This contract does not itself select Historical Memory, Dependency
Knowledge Graph, Repository Intelligence expansion, Decision
Evaluation support, Execution Planning, Permission Broker evolution, or
any other candidate. No phase bound by this contract may treat mere
candidate listing (Section 4) as selection.

## 4. Candidate Architecture Domains

The following candidate directions are recognized as under evaluation.
Listing a candidate here does not constitute selecting it; a candidate
becomes selected only when a future governed phase completes the
decision sequence in Section 6 and explicitly records the selection.

### 4.1 Historical Memory

Candidate evaluation criteria: schema readiness (119Q/119R already
frozen and verified); source-boundary risk (git/lifecycle history is a
broader, more heterogeneous source surface than Track 120's snapshot
sources); generator-pattern reuse potential (Track 120 pattern
applicability); temporal-context value to existing consumers (Change
Impact, Advisory Context).

### 4.2 Dependency Knowledge Graph

Candidate evaluation criteria: schema readiness (119S/119T already
frozen and verified); graph-construction/traversal boundary discipline
required to avoid drifting toward inference or prediction; direct
gap-closure value for Change Impact's existing flat entity model;
consistency with the graph schema's existing disclaimer that no
traversal or construction occurs by PCAE tooling.

### 4.3 Repository Intelligence Expansion (richer artifact families)

Candidate evaluation criteria: marginal capability gain versus
architectural risk for persisting Advisory Intelligence Context
Package, Query Result, or Repository Intelligence Package as
first-class artifacts; existence of a concrete downstream consumer need
(e.g. cross-session context reuse) rather than persistence for its own
sake.

### 4.4 Decision Evaluation Support

Candidate evaluation criteria: governance sensitivity (highest among
listed candidates, since it is the first candidate that reaches a
decision-authoritative subsystem, even indirectly); existing
contract-level hook (`decision_evaluation_handoff` field in the
Advisory Intelligence Context Package schema); preservation of the
invariant that Repository Intelligence never itself becomes
decision-authoritative regardless of how many consumers sit between it
and Decision Evaluation.

### 4.5 Execution Planning

Candidate evaluation criteria: current architectural fit is low, since
no completed chapter produces output shaped for execution planning and
PCAE's runtime remains execution-unavailable by repeatedly-reconfirmed
design; risk of conflating the Repository Intelligence read-only
boundary with the runtime's execution-unavailable boundary if pursued
as a Repository Intelligence extension rather than its own governed
chapter.

### 4.6 Permission Broker Evolution

Candidate evaluation criteria: current architectural fit is low and
largely orthogonal to Repository Intelligence; any evolution belongs to
a runtime/governance chapter, not a Repository Intelligence chapter;
evaluating it further inside this contract would blur chapter
boundaries.

### 4.7 Other Future Architectural Chapters

This contract does not close the candidate set to Sections 4.1-4.6. A
future phase bound by this contract may introduce and evaluate an
additional candidate not listed here, provided it is evaluated against
the same Section 5 principles and follows the same Section 6 decision
sequence before any implementation path is selected.

## 5. Evaluation Principles

Every candidate direction, including any introduced later under
Section 4.7, shall be evaluated against all of the following
principles before selection:

- **Governance compatibility** — the candidate must fit within existing
  PCAE governed lifecycle, commit, push, report, and notification
  discipline without requiring ungoverned shortcuts.
- **Determinism** — the candidate must be capable of producing
  equivalent logical output for equivalent input, with no randomness,
  AI inference, or ambient state dependence required by its core
  design.
- **Explainability** — the candidate must be capable of tracing its
  output back to governed sources in a way a human or downstream
  consumer can inspect.
- **Auditability** — the candidate must be capable of producing
  reproducible, inspectable records of what it did and why.
- **Maintainability** — the candidate must fit the existing shared
  patterns (generator, Query Layer, sibling-consumer) established by
  Tracks 120-124 without requiring a parallel, incompatible
  architecture.
- **Reproducibility** — the candidate's outputs must be reproducible
  from the same governed inputs across repeated runs.
- **Architectural cohesion** — the candidate must relate coherently to
  the completed Repository Intelligence chapter and to PCAE's broader
  architecture, not stand as an isolated, uncoordinated addition.
- **Safety** — the candidate must not expand authority, decision
  power, or execution capability beyond what is explicitly and
  separately authorized through its own governed contract-freeze phase.
- **Observe-first philosophy** — the candidate must be evaluable and,
  if selected, initially implementable without requiring the runtime
  execution boundary to change.

A candidate that cannot be evaluated against all nine principles is not
ready for selection under this contract, regardless of how compelling
its architectural fit appears.

## 6. Decision Constraints

This contract prohibits selecting an implementation path before all of
the following have been completed, in order, for the candidate under
consideration:

1. **Architecture** — a governed architecture phase defining the
   candidate's scope, boundaries, invariants, and relationship to
   Repository Intelligence and to PCAE's broader architecture.
2. **Contract** — a governed contract-freeze phase defining the
   candidate's normative, binding requirements.
3. **Verification** — a governed contract-verification phase
   independently confirming the frozen contract is internally
   consistent, testable, and ready to constrain planning.

Only after all three steps are complete for a specific candidate may a
future phase select that candidate as an implementation path — and even
then, selection is a separate, explicit decision recorded in that
phase's own documentation, not an automatic consequence of completing
the three steps.

No phase bound by this contract (125C, 125D, 125E, 125F) may skip
architecture, skip contract freeze, skip verification, or treat
candidate evaluation (Section 4) as equivalent to completing this
three-step sequence.

## 7. Preserve Repository Intelligence

Repository Intelligence (Tracks 119-124) shall remain stable during
future architectural evaluation:

- No phase bound by this contract may modify a Track 119 schema, the
  Track 120 generator, the Track 121 Query Layer, the Track 122
  Advisory Context Builder, or the Track 123 Change Impact Builder
  without its own separate, explicitly scoped governed contract-freeze
  phase.
- Repository Intelligence's existing public interfaces, CLI surface,
  deterministic outputs, attribution behavior, limitation propagation,
  and boundary disclosures remain frozen as verified in 124F and
  reviewed in 125A.
- A future candidate direction (e.g. Dependency Knowledge Graph,
  Historical Memory) that extends Repository Intelligence with a new
  artifact family or generator does so as an **addition**, following
  the same architecture -> contract -> verification -> plan ->
  implementation -> verification sequence Tracks 120-124 already
  proved, not as a modification of what those tracks already froze.

## 8. Execution Boundary

Execution shall remain unavailable. Observe-only runtime remains
mandatory for every phase bound by this contract.

- Runtime state remains `Observed`.
- Maximum plugin capability remains `observe`.
- Execution capability remains `unavailable`.
- Permission Broker status remains `execution_unavailable`.
- No phase bound by this contract (125C-125F) may change this boundary.
  Any future proposal to change it requires its own separate,
  explicitly scoped governed architecture and contract path — it is
  not something this contract, or any candidate evaluated under it,
  authorizes.

## 9. Governance Contract

Every phase bound by this contract shall preserve:

- **deterministic engineering** — no phase introduces randomness,
  probabilistic behavior, or unexplained non-reproducibility into
  either the evaluation process or any candidate's eventual design;
- **fail-closed philosophy** — invalid, unsupported, or ambiguous
  evaluation inputs must not produce a default selection or silent
  candidate promotion;
- **attribution** — evaluation conclusions must cite the governed
  sources (125A, this contract, prior track documents) they rely on;
- **limitation propagation** — known limitations of a candidate
  direction identified during evaluation must be carried forward into
  later phases (125C-125F), not dropped;
- **boundary disclosures** — every evaluation and decision document
  must continue to distinguish architectural evaluation from
  implementation authorization, exactly as Repository Intelligence
  distinguished itself from Repository State, Evidence, Advisory
  reasoning, and execution authority;
- **reproducibility** — evaluation criteria and conclusions must be
  re-derivable by a future reviewer from the same governed sources;
- **auditability** — every phase bound by this contract must produce a
  complete, metadata-consistent canonical phase report.

## 10. Compatibility Contract

Future chapters shall remain compatible with the completed Repository
Intelligence subsystem unless explicitly superseded through a governed
lifecycle:

- A future candidate implementation must consume Repository
  Intelligence through the existing Track 121 Query Layer boundary,
  following the Track 122/123 sibling-consumer pattern, unless a
  separate governed phase explicitly redesigns that boundary.
- A future candidate implementation must not silently redefine
  Repository Intelligence terminology (Repository Knowledge Snapshot,
  Query Result, attribution bundle, limitation bundle, boundary
  disclosure bundle, unknown/unavailable/incomplete/conflicting) that
  has held consistently across Tracks 119-124.
- Compatibility does not mean the next chapter is limited to
  Repository Intelligence's exact current shape — new artifact
  families, new query categories, and new consumers are all
  architecturally anticipated (125A Section 6) — but any change to
  already-frozen Track 119-124 contracts requires its own explicit
  supersession decision, not an incidental side effect of building the
  next chapter.

## 11. Deferred Capabilities

Explicitly deferred, regardless of which candidate direction is
eventually selected:

- execution capability;
- autonomous decision making;
- Decision Evaluation authority;
- runtime mutation;
- autonomous repository modification;
- execution planning implementation.

Any future work in these areas requires its own separate, explicitly
scoped governed architecture and contract path outside this contract's
authorization.

## 12. Technical Debt Classification

This phase classifies inherited technical debt only. It repairs none
of it.

Carried forward from 125A's own classification (itself carried forward
from Track 124):

- **Lifecycle/tooling debt**: 119Q report-generation-ordering defect;
  119AB phase-id comparison bug; recurring
  `pending_final_telegram_delivery` reporting detail.
- **Repository hosting policy reporting detail**: GitHub main-branch
  PR-rule bypass notification.
- **Notification environment detail**: missing `PCAE_NOTIFY_ENABLED`
  during governed push environment.

No new technical debt category is introduced by this contract.

## 13. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this contract freeze.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this contract freeze.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail, non-blocking for governed PCAE push when
  `pcae push` succeeds.
- Missing `PCAE_NOTIFY_ENABLED` during governed push environment:
  notification environment detail, non-blocking when Telegram status
  and explicit report delivery are verified after sourcing the
  environment.

## 14. Strict Non-Goals

This phase does not implement:

- any new architectural chapter;
- Historical Memory;
- Dependency Knowledge Graph;
- Repository Intelligence expansion;
- Decision Evaluation;
- execution planning;
- execution capability;
- runtime plugins;
- source code;
- test code;
- schema changes.

This phase does not select an implementation path among the candidates
listed in Section 4. Selection remains gated by the Section 6 decision
sequence and belongs to a future phase that has completed that
sequence for a specific candidate.

## 15. Relationship to Future Phases

- **125C - Next Architecture Direction Contract Verification**:
  independently verify this contract before planning candidate
  evaluation work.
- **125D - Next Architecture Direction Plan**: define the bounded plan
  for how candidate evaluation (not selection) proceeds inside this
  contract, and/or how the Section 6 decision sequence will be applied
  to a specific candidate if 125C/125D determine one is ready to enter
  that sequence.
- **125E - Next Architecture Direction**: scope to be defined by 125D;
  may not select or implement a candidate unless the Section 6
  decision sequence has been completed for it.
- **125F - Next Architecture Direction Verification**: independently
  verify whatever 125E produces against this contract and the 125D
  plan.

No 125C work begins in this phase.

## 16. Governance Compatibility

This contract is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- candidate evaluation is scoped through governed phases only;
- implementation selection is explicitly gated behind the Section 6
  decision sequence;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 17. Acceptance

125B is complete when this decision contract is frozen, project memory
reflects 125B completion, runtime remains `Observed` / `observe` /
execution unavailable, no implementation has occurred, no
implementation path has been selected, and the recommended next phase
is 125C - Next Architecture Direction Contract Verification.
