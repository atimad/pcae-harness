# Phase 125D - Next Architecture Direction Evaluation Plan

## 1. Purpose

Phase 125D defines the structured evaluation process used to determine
PCAE's next architectural chapter, operating inside the canonical
decision contract frozen in 125B and independently verified in 125C.

This phase defines evaluation methodology only. It selects no
architectural direction, implements no candidate, changes no runtime
behavior, and modifies no source code, test code, or schema.

125D turns 125B's Section 5 evaluation principles and Section 6
decision constraints into an executable process: what order evaluation
work happens in, what each stage produces, what criteria and risk
categories apply, and how a future phase will independently verify the
evaluation was conducted objectively. 125D does not itself perform that
evaluation — it plans how 125E will.

## 2. Contract Basis

This plan operates inside, and does not amend, the 125B contract:

- `docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_CONTRACT_FREEZE.md`
  (125B) — defines candidate domains, nine evaluation principles, the
  three-step architecture -> contract -> verification decision
  sequence, Repository Intelligence preservation, execution boundary,
  governance/compatibility contracts, and deferred capabilities.
- `docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_CONTRACT_VERIFICATION.md`
  (125C) — independently confirmed the 125B contract is complete,
  decision-neutral, and implementation-ready with no defects requiring
  repair.

125D does not reinterpret, loosen, or extend either document. Every
evaluation criterion and pipeline stage defined here is a concrete
operationalization of a 125B requirement, not a new requirement.

## 3. Candidate Architecture Domains

125D evaluates the same candidate set 125B recognized, unchanged.
Listing a candidate here — again — does not constitute selecting it.

- **Historical Memory** — temporal Repository Intelligence layer;
  schema already frozen (119Q/119R).
- **Dependency Knowledge Graph** — structural relationship layer over
  Repository Knowledge; schema already frozen (119S/119T).
- **Repository Intelligence expansion** — persisting the remaining
  frozen-but-unimplemented Track 119 artifact families (Advisory
  Intelligence Context Package, Query Result, Repository Intelligence
  Package) as first-class artifacts.
- **Decision Evaluation support** — wiring Repository Intelligence
  and/or Advisory context into an actual Decision Evaluation consumer.
- **Execution Planning** — a future runtime capability chapter,
  currently low architectural fit per 125B §4.5.
- **Permission Broker evolution** — a future runtime/governance
  chapter, currently orthogonal to Repository Intelligence per 125B
  §4.6.
- **Other future architectural chapters** — 125B §4.7 keeps this set
  open; 125D's pipeline (Section 4) applies equally to any candidate
  introduced later, named or not named here.

No candidate in this list is more "in scope" for selection than any
other as a result of appearing in this plan. 125D's own strict
non-goals (Section 12) forbid this plan from selecting any of them.

## 4. Evaluation Pipeline

125E shall follow this eight-stage sequence when it performs candidate
evaluation. Each stage below is a **responsibility**, not a decision;
125D performs none of these stages itself.

### 4.1 Stage 1 — Candidate Identification

Responsibility: enumerate the candidate set from Section 3 (and any
Section 3-qualifying addition), confirm each candidate is a legitimate
architectural domain rather than an implementation detail, and record
the source document(s) that first proposed or scoped it (118, 119A,
125A).

Output: a candidate register — one entry per candidate, each citing its
originating governed source.

### 4.2 Stage 2 — Architectural Fit Assessment

Responsibility: assess each candidate against architectural cohesion
with the completed Repository Intelligence chapter and PCAE's broader
architecture (125B §5's "architectural cohesion" principle), including
whether an existing pattern (Track 120 generator, Track 121 Query
Layer, Track 122/123 sibling-consumer) already fits the candidate or
whether a new pattern would be required.

Output: a per-candidate architectural fit statement with explicit
citation to which existing pattern (if any) applies.

### 4.3 Stage 3 — Governance Compatibility Assessment

Responsibility: assess each candidate against 125B §5's governance
compatibility, determinism, explainability, and auditability
principles — whether the candidate can be evaluated, planned, and
(if ever selected) implemented entirely inside governed lifecycle,
commit, push, report, and notification discipline, with deterministic,
explainable, auditable behavior.

Output: a per-candidate governance compatibility statement, explicitly
flagging any candidate that cannot yet satisfy all four principles.

### 4.4 Stage 4 — Dependency Assessment

Responsibility: identify what each candidate depends on that already
exists (e.g. a frozen Track 119 schema, an existing Query Layer query
category, an existing consumer pattern) versus what it would require
that does not yet exist (e.g. a new schema, a new generator, a new
runtime capability). Cross-reference 125B §7 (Repository Intelligence
preservation) and §10 (compatibility contract) to confirm the
dependency path does not require modifying already-frozen Track
119-124 work without its own supersession decision.

Output: a per-candidate dependency map distinguishing "already
available" from "would require new governed work."

### 4.5 Stage 5 — Risk Assessment

Responsibility: assess each candidate against the five risk categories
defined in Section 6 below (technical, governance, maintenance,
migration, future compatibility).

Output: a per-candidate risk profile, one rating and rationale per risk
category.

### 4.6 Stage 6 — Readiness Assessment

Responsibility: determine, for each candidate, where it currently
stands relative to 125B §6's three-step decision sequence
(architecture -> contract -> verification) — none started, architecture
only, architecture + contract, or all three complete — since only a
candidate with all three complete may ever be selected.

Output: a per-candidate readiness marker against the three-step
sequence. No candidate is expected to have any step complete yet,
since no Section 6 sequence work has begun for any candidate as of
125D.

### 4.7 Stage 7 — Comparative Analysis

Responsibility: assemble the per-candidate outputs from Stages 2-6 into
a single comparison structure (e.g. a table) so a future reader can
see all candidates' fit, governance compatibility, dependencies, risk,
and readiness side by side, without the comparison itself asserting
which candidate is "best."

Output: a comparative analysis artifact. This stage produces a
side-by-side view, not a ranking or a recommendation.

### 4.8 Stage 8 — Recommendation Preparation

Responsibility: prepare the material a future governed phase would
need to propose entering the Section 6 decision sequence for a specific
candidate — citing the Stage 1-7 outputs — without itself proposing,
ranking, or selecting one. "Preparation" here means assembling
traceable evidence, not producing a verdict.

Output: a recommendation-preparation artifact that a future phase may
read, but that does not itself constitute a recommendation, ranking,
or selection. See Section 8 for the explicit boundary between
preparation and decision.

## 5. Evaluation Criteria

Every candidate evaluated under this plan's pipeline shall be assessed
against the following measurable criteria. These operationalize 125B
§5's nine evaluation principles and add implementation complexity and
future extensibility as 125D-specific planning criteria not already
named in 125B (both are compatible extensions of 125B §5's
"maintainability" and "architectural cohesion" principles, not new
authority).

| Criterion | What it measures | Source |
| --- | --- | --- |
| Governance compatibility | Fits governed lifecycle/commit/push/report/notification discipline without ungoverned shortcuts | 125B §5 |
| Architectural cohesion | Relates coherently to Repository Intelligence and PCAE's broader architecture | 125B §5 |
| Determinism | Capable of equivalent logical output for equivalent input, no randomness/AI inference required | 125B §5 |
| Explainability | Output traceable back to governed sources | 125B §5 |
| Auditability | Produces reproducible, inspectable records of what and why | 125B §5 |
| Reproducibility | Outputs reproducible from the same governed inputs across repeated runs | 125B §5 |
| Maintainability | Fits existing shared patterns (generator, Query Layer, sibling-consumer) without a parallel incompatible architecture | 125B §5 |
| Safety | Does not expand authority/decision power/execution capability beyond what its own contract-freeze phase would explicitly authorize | 125B §5 |
| Implementation complexity | Estimated scope of new governed work required (new schema? new generator? new consumer pattern? new runtime capability?) | 125D-specific, operationalizes 125B §5 maintainability |
| Future extensibility | Whether selecting this candidate forecloses or preserves the option to pursue other listed candidates later | 125D-specific, operationalizes 125B §5 architectural cohesion |

Observe-first philosophy (125B §5's ninth principle) is evaluated
separately in Section 7 (Execution Boundary) rather than folded into
this table, since it is a binary gate (the candidate must be evaluable
and initially implementable without requiring the execution boundary
to change) rather than a graded criterion.

## 6. Risk Assessment Methodology

125E shall assess every candidate against five risk categories:

- **Technical risk** — likelihood that the candidate's implementation
  (if ever selected) would introduce non-determinism, break an
  existing pattern, or require unproven techniques not already
  demonstrated by Tracks 120-124.
- **Governance risk** — likelihood that the candidate would strain
  governed lifecycle discipline, canonical reporting, or fail-closed
  behavior, or would require an ungoverned shortcut to implement.
- **Maintenance risk** — likelihood that the candidate would increase
  long-term maintenance burden disproportionately to its capability
  gain, or would require a parallel, incompatible architecture rather
  than extending existing shared patterns.
- **Migration risk** — likelihood that adopting the candidate would
  require changing already-frozen Track 119-124 contracts, interfaces,
  or terminology rather than adding to them (125B §7, §10).
- **Future compatibility risk** — likelihood that selecting the
  candidate now would foreclose, complicate, or conflict with pursuing
  a different candidate later.

Each risk category shall be rated with an explicit rationale citing
the governed sources (Track 119-124 documents, 125A, 125B, 125C) the
rating is based on — not an unexplained numeric score. This preserves
125B §9's attribution and reproducibility requirements.

## 7. Repository Intelligence Compatibility Strategy

Every candidate evaluated under this plan must preserve compatibility
with the completed Repository Intelligence subsystem (Tracks 119-124)
unless an explicit governed supersession is proposed:

- Stage 4 (Dependency Assessment) and the migration-risk rating in
  Stage 5 both explicitly check whether a candidate's dependency path
  would require modifying an already-frozen Track 119 schema, the
  Track 120 generator, the Track 121 Query Layer, or the Track 122/123
  consumers.
- A candidate whose evaluated dependency path requires such
  modification must have that requirement explicitly flagged in its
  Stage 4 output and its migration-risk rating, not silently absorbed
  into a lower-risk rating.
- Consistent with 125B §7, a candidate that would extend Repository
  Intelligence (e.g. Dependency Knowledge Graph, Historical Memory)
  is evaluated as proposing an **addition** via the same architecture
  -> contract -> verification -> plan -> implementation -> verification
  sequence Tracks 120-124 already proved — not as a modification of
  what those tracks already froze — unless the candidate's own future
  evaluation explicitly proposes supersession, which 125D does not do.

## 8. Execution Boundary

Execution remains unavailable. Observe-only runtime remains mandatory
for every phase this plan governs.

- Runtime state remains `Observed`.
- Maximum plugin capability remains `observe`.
- Execution capability remains `unavailable`.
- Permission Broker status remains `execution_unavailable`.
- Stage 3 (Governance Compatibility Assessment) and the evaluation
  criteria table (Section 5) both require every candidate to be
  evaluable, and — if ever selected — initially implementable, without
  requiring this boundary to change. A candidate that can only be
  meaningfully evaluated or implemented by first changing the
  execution boundary is not ready for the Section 6 decision sequence
  under this contract; any such candidate would require its own
  separate, explicitly scoped governed architecture and contract path
  outside this plan's and 125B's authorization (125B §8, §11).

## 9. Decision Preparation

This plan's Stage 8 (Recommendation Preparation) describes how future
evaluation work prepares — but does not make — PCAE's eventual
architectural recommendation:

- Preparation means assembling the Stage 1-7 outputs (candidate
  register, fit/governance/dependency/risk/readiness assessments,
  comparative analysis) into a form a future governed phase can read,
  cite, and act on.
- Preparation does not mean ranking candidates, declaring a "winner,"
  or proposing that a specific candidate enter the Section 6 decision
  sequence. Any such act is a decision, not preparation, and 125B §6
  requires it to be "a separate, explicit decision recorded in that
  phase's own documentation" — not something 125D's plan or 125E's
  evaluation work performs by default.
- The distinction matters because it keeps evaluation (assembling
  evidence) and decision (choosing a path) as separately governed,
  separately auditable acts, exactly as 125B's contract requires.
- A future phase that wishes to propose entering the Section 6
  sequence for a specific candidate does so as its own explicit,
  documented act, citing the Stage 8 preparation material as evidence
  — not as an automatic next step this plan authorizes in advance.

## 10. Verification Strategy

A future verification phase (bound by 125B, following the 121F/122F/
124F/125C pattern of re-deriving findings from source rather than
trusting an evaluation's own summary) shall confirm the evaluation
performed under this plan remained objective, reproducible, and
governance-compliant by checking:

- **Objectivity**: every candidate received all eight pipeline stages
  (Section 4), not a subset; no candidate's evaluation was skipped,
  abbreviated, or given materially less scrutiny than another without
  an explicitly documented reason.
- **Reproducibility**: every criterion rating (Section 5) and risk
  rating (Section 6) cites the specific governed source(s) it is based
  on, such that an independent reviewer could re-derive the same
  rating from the same sources.
- **Governance compliance**: the evaluation used only governed
  lifecycle/commit/push/report/notification commands; no raw git
  commit/push, force push, or `--no-verify` occurred; canonical phase
  reports remain complete and metadata-consistent.
- **Decision-neutrality**: the evaluation's Stage 8 output (Section 9)
  prepared evidence without selecting, ranking as a declared winner, or
  implicitly authorizing any candidate; no candidate was treated as
  already having entered the Section 6 decision sequence.
- **Repository Intelligence preservation**: no Track 119-124 file was
  modified by the evaluation itself (evaluation is a documentation
  activity, not an implementation activity).
- **Execution boundary preservation**: runtime state, maximum plugin
  capability, execution capability, and Permission Broker status all
  remained unchanged throughout the evaluation.

This verification strategy itself does not perform verification —
that is 125E's eventual output being checked by a later phase, not
work this plan (125D) performs.

## 11. Governance Contract

Every phase bound by this plan shall preserve, consistent with 125B §9:

- deterministic engineering;
- fail-closed philosophy;
- attribution;
- limitation propagation;
- boundary disclosures;
- reproducibility;
- auditability.

## 12. Deferred Capabilities

Explicitly deferred, regardless of which candidate is eventually
evaluated as ready or ultimately selected:

- execution capability;
- autonomous decision making;
- Decision Evaluation authority;
- runtime mutation;
- autonomous repository modification;
- execution planning implementation.

Any future work in these areas requires its own separate, explicitly
scoped governed architecture and contract path outside this plan's and
125B's authorization.

## 13. Technical Debt Classification

125D classifies no new technical debt. Inherited technical debt
(Section 14) is carried forward unchanged from 125A/125B/125C's own
classification. This phase repairs none of it.

## 14. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this evaluation plan.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this evaluation plan.
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

## 15. Strict Non-Goals

This phase does not:

- select a next architectural chapter;
- implement Historical Memory;
- implement Dependency Knowledge Graph;
- implement Repository Intelligence expansion;
- implement Decision Evaluation;
- implement Execution Planning;
- implement execution capability;
- modify runtime behavior;
- modify source code;
- modify test code;
- modify schemas.

125D plans evaluation methodology only. It performs no Stage 1-8
evaluation work itself — that is 125E's responsibility, executed
strictly inside this plan and the 125B contract.

## 16. Relationship to Future Phases

- **125E - Next Architecture Direction Evaluation**: executes the
  eight-stage pipeline (Section 4) against the candidate set (Section
  3) using the criteria (Section 5) and risk methodology (Section 6)
  defined here. 125E may not select a candidate; it may only produce
  Stage 1-8 outputs, including the Stage 8 recommendation-preparation
  artifact, which remains evidence, not a decision.
- **125F - Next Architecture Direction Decision Review**:
  independently verifies whatever 125E produces against this plan and
  the 125B contract, using the verification strategy in Section 10.
  125F may confirm the evaluation was objective, reproducible, and
  governance-compliant; it does not itself select a candidate either,
  unless a future phase beyond 125F explicitly proposes entering the
  125B §6 decision sequence for a specific candidate as its own
  separate act.

No 125E work begins in this phase.

## 17. Governance Compatibility

This plan is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- evaluation work is scoped through governed phases only;
- implementation selection remains explicitly gated behind the 125B §6
  decision sequence;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 18. Acceptance

125D is complete when this evaluation plan is documented, project
memory reflects 125D completion, runtime remains `Observed` /
`observe` / execution unavailable, no implementation has occurred, no
architectural direction has been selected, and the recommended next
phase is 125E - Next Architecture Direction Evaluation.
