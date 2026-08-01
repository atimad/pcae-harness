# Phase 148A: Next Strategic Capability Architecture

**Mode:** Strategic Architecture / Roadmap Reassessment (architecture-only; no
implementation).
**Baseline:** canonical repository state after Phase 147R (Authority
Evaluation Chapter Certification Closure — CERTIFIED WITH RETAINED
OBSERVATIONS).
**Primary status source:** `PROJECT_STATUS.md`.

---

## 1. Executive Summary

Chapter 147 closed the Authority Evaluation chapter. Across the entire
140–147 arc, one fact was reconfirmed on every single phase without
exception: PCAE's runtime remains `Observed / observe / unavailable`, and
**no PCAE command path consumes a permission or enforcement decision before
mutating anything** — except `pcae commit` and `pcae push`, which already
perform real git mutation today through their own bespoke, broker-independent
readiness checks.

This phase selects **Chapter 148: Permission Broker Production Consumption —
Governed Command-Path Integration** as the next strategic capability. Its
purpose is to make an already-designed, already-frozen, already-tested
decision layer (`src/pcae/core/permission_broker_foundation.py`) into the
**first real, non-bypassable enforcement point** in PCAE, by routing the
existing git commit/push mutation paths through it — without granting any
new execution capability, without touching runtime state, and without
reopening Chapter 147.

This is deliberately a *consolidation* chapter, not an *expansion* chapter.
It closes the gap between "PCAE can compute a permission decision" and "PCAE
enforces a permission decision," using capability PCAE already possesses
(git commit/push), before any later chapter is asked to extend enforcement to
capability PCAE does not yet possess (shell execution, generic file
mutation, plugin dispatch).

**Verdict:** NEXT STRATEGIC CAPABILITY ARCHITECTURE COMPLETE.
**Recommended next phase:** 148B — Permission Broker Production Consumption
Contract Freeze.

---

## 2. Scope

In scope: analysis, candidate generation, evaluation, and architecture
definition for Chapter 148. Production of this document and any
architecture-bookkeeping artifacts it references.

Out of scope (see §39 / §36): any change to `src/pcae/**`, any new CLI
command, any runtime state change, any change to Permission Broker or
Runtime Enforcement *behavior*, any new plugin, any contract amendment, any
reopening of Chapter 147.

---

## 3. Assessment Method

Three independent research passes were run against canonical project state:

1. **Roadmap/capability-gap research** — `PROJECT_STATUS.md` (current phase
   section and the full 140–147 chapter arc), `docs/ROADMAP.md`,
   `docs/V0_2_AUTONOMY_ROADMAP.md`, `.pcae/strategic-lineage.json`,
   `docs/architecture/04-runtime-governance.md`,
   `docs/architecture/05-future-autonomous-flow.md`, `tasks/TODO.md`.
2. **Source-architecture research** — `src/pcae/core/permission_broker.py`,
   `src/pcae/core/permission_broker_foundation.py`,
   `src/pcae/core/backend_invocations.py` (Runtime Enforcement Decision
   Engine/Coordinator, Governed Execution Attempt Boundary),
   `src/pcae/core/runtime_registry.py`, `src/pcae/core/shell_gate.py`,
   `src/pcae/core/mutation_preflight.py`, `src/pcae/core/writer.py`,
   `src/pcae/commands/commit.py`, `src/pcae/commands/push.py`.
3. **Authority Evaluation boundary and contract-landscape research** —
   `src/pcae/authority_evaluation/`, `src/pcae/aesic/`, `docs/contracts/*`,
   `docs/PHASE_147*`, `docs/certification/PHASE_147R_*`,
   IWC-001/IWPC-001/PEC-001/CHGR-001/AESIC-001 contract text.

Live CLI commands were run directly against the repository as ground truth:
`pcae session bootstrap --agent-id claude-local --sync-lock`, `pcae check`,
`pcae health`, `pcae doctor task-memory`, `pcae runtime inspect`,
`pcae push check`. All findings below are reconciled against both the
static documentation record and this live runtime output.

---

## 4. Canonical Project Baseline

- `PROJECT_STATUS.md` Current Phase: **147R**, completed, report: complete.
  Verdict: "AUTHORITY EVALUATION CHAPTER CERTIFICATION CLOSED — CERTIFIED
  WITH RETAINED OBSERVATIONS." Recommended next phase named in that document:
  **148A — Next Strategic Capability Architecture — not authorized by this
  document.**
- `pcae runtime inspect` (live, this session): `Runtime status:
  not_implemented`, `Runtime state: Observed`, `Execution capability:
  unavailable`, `Maximum plugin capability: observe`, `Registry status:
  empty`, `Plugin count: 0`, `Permission Broker status:
  execution_unavailable`, `Governance posture: non-executing`.
- `pcae health` / `pcae check` / `pcae doctor task-memory`: healthy, passed,
  clean. `pcae push check`: nothing to push, working tree clean.
- No unexpected active governed phase exists; the active task
  (`20260801-1306-idle-awaiting-next-governed-phase-post-147r`) is the
  expected post-147R idle placeholder.

Per instruction, `PROJECT_STATUS.md` is treated as authoritative over
`tasks/TODO.md` throughout this analysis; no conflict between the two was
found on strategic direction.

---

## 5. Completed Capability Map

Classified as: **architected / contract-frozen / implemented / independently
verified / production-wired / operationally certified / intentionally
deferred / structurally absent.**

### Governance

| Capability | Status |
|---|---|
| Request intake / task-phase lifecycle | production-wired, operationally certified |
| Readiness (`pcae session bootstrap` blocked/ready signal) | production-wired |
| Confirmation (Decision Session state machine, IWC-001) | contract-frozen, implemented, production-wired, certified |
| Authority Evaluation (AEM/AESIC-001) | contract-frozen, implemented, independently verified, production-wired, **operationally certified (147R)** |
| Permission brokering (decision computation) | contract-frozen (two parallel implementations), implemented, tested — **not production-wired** (zero real call sites) |
| Canonical reporting (phase-report/finalization) | production-wired, operationally certified, with one retained recurring finding (metadata sequencing) already repaired at 145H.3R.1 |
| Publication (PEC-001 → CHGR-001) | contract-frozen, implemented, independently verified, production-wired, certified |
| Human governance records (CHGR) | contract-frozen (v1.3, schema-envelope-complete since 146N), production-wired |

### Knowledge and Reasoning

| Capability | Status |
|---|---|
| Repository intelligence | implemented, production-wired |
| Historical memory / provenance timeline | implemented, production-wired (3,182+ events) |
| Dependency graph / architecture history | implemented |
| Cross-artifact knowledge | implemented |
| Advisory reasoning (IRG challenge) | implemented, production-wired, advisory-only by design |
| Change impact / explainability | implemented, partially production-wired |

### Execution

| Capability | Status |
|---|---|
| Execution attempt boundary (`GovernedExecutionAttemptBoundary`) | contract-frozen (Phase 99), implemented as a design-only dataclass, **structurally absent as a real gate** |
| Runtime enforcement (Decision Engine + Coordinator) | contract-frozen (Phases 101–104), implemented as design-only dataclasses, **structurally absent as a real gate** |
| Runtime/plugin model | architected, contract-frozen; registry is real code but is instantiated fresh per CLI call with no persistence — **structurally empty by construction** |
| Tool invocation | structurally absent |
| File modification (governed) | preflight model exists (`mutation_preflight.py`, design-only); a real, ungated filesystem writer exists (`writer.py`) for scaffolding only, not governed mutation |
| Command execution (shell/subprocess) | classifier exists (`shell_gate.py`) but **intercepts nothing** — no real command is ever piped through it before running |
| Environment mutation | structurally absent |
| Commit | **already real and production-wired** (`pcae commit`), governed by its own self-contained staged-file-conflict logic, not by either Permission Broker |
| Push | **already real and production-wired** (`pcae push`), governed by its own multi-source readiness assessment (health, check, task memory, phase-report trust, lifecycle-review policy), not by either Permission Broker |
| Rollback | design-only (`enforcement_rollback.py` family); BR-005 governed promote/rollback exists as a separate, capability-complete, narrower mutation path (see §22) |

### Orchestration

| Capability | Status |
|---|---|
| Single-agent lifecycle | production-wired, operationally certified |
| Multi-agent coordination (design) | architected, contract-frozen; no live multi-agent execution |
| Handoff | production-wired |
| Retries / recovery (design) | architected, largely design-only |
| Conflict resolution (design) | architected, design-only |
| Capability allocation | structurally absent (no capability-elevation mechanism exists at all) |

---

## 6. Remaining Autonomy Gaps

Reconstructing the intended end-to-end path (§7 below) against the map in
§5, the gaps cluster into exactly two kinds:

1. **Decision-without-enforcement**: Permission Broker and Runtime
   Enforcement are contract-frozen, implemented, and unit-tested, but
   *nothing calls them from a real command path*. This is not a missing
   design — it is a missing wire. `git grep` confirms zero call sites for
   `permission_broker_foundation.PermissionBroker`,
   `evaluate_permission_broker`, `RuntimeEnforcementDecision`, or
   `RuntimeEnforcementCoordinator` outside their own command/test modules.
2. **Capability-without-boundary**: `pcae commit` and `pcae push` already
   execute real, root-repository-mutating git operations today, gated by
   ad hoc, per-command readiness logic that has no relationship to either
   Permission Broker implementation and no relationship to the shell gate
   classifier. This is a working capability with a *bypassable* governance
   layer — two independent gates for the two highest-consequence mutating
   operations in the project, neither of which is the canonical decision
   point Permission Broker was designed to be.

Everything downstream of these two gaps (generic shell execution, file
mutation outside git, plugin dispatch, capability elevation) is
**structurally absent by explicit, repeatedly-reconfirmed design** — see
`docs/ROADMAP.md`: "The current maximum capability actually exercised by any
real PCAE code path is `observe` — nothing more," and
`src/pcae/core/runtime_registry.py`'s `UNDECLARABLE_CAPABILITIES =
frozenset({"enforce", "execute"})`, which makes it structurally impossible
for any plugin descriptor to even *declare* enforcement or execution
capability today, independent of any policy decision.

The first architectural gap preventing transition from observation/advisory
operation into safely governed execution is therefore **not** "runtime
capability is too low" — it is **"the one decision layer designed to gate
capability elevation has never been made authoritative over anything, not
even the mutating capability PCAE already has."** Building broader execution
before closing this gap would mean adding a third, fourth, and fifth
independent, ad hoc gate rather than extending the one gate meant to
generalize.

---

## 7. Candidate Chapter Options

Three or more candidates were generated and evaluated, spanning the
suggested classes:

- **A. Permission Broker Production Consumption — Governed Command-Path
  Integration.** Route the existing git commit/push mutation paths through
  `permission_broker_foundation.py` as the single, non-bypassable decision
  point, replacing their current bespoke gating. No new execution
  capability; centralizes and hardens capability PCAE already has.
- **B. Runtime Capability Elevation Architecture.** Design the mechanism by
  which runtime capability could move from `observe` toward a mutation
  tier (explicit request, ceiling, broker decision, scope, expiration,
  revocation, audit). Directly extends the roadmap's "Executable last"
  frontier.
- **C. Unified Confirmation/Authority/Permission/Capability State Lattice.**
  Produce the single canonical document that formally ties together the six
  states research confirmed are deliberately scattered across contracts
  today (Confirmed → record-Confirmed → Eligible → Authorized → Permitted →
  Capable → Executed), with explicit non-conflation rules.
- **D. Governed Filesystem/Command Mutation Boundary (generic shell/file
  execution).** Design a new execution-intent → plan → attempt → evidence
  model and wire it to a first real, narrowly-scoped subprocess/file-write
  capability.
- **E. Execution Evidence / Postcondition Verification Framework.** Design
  the canonical immutable evidence artifact for any future execution
  attempt, independent of which execution surface it eventually gates.

Candidates B, D, and E all presuppose that the enforcement point they would
gate already works reliably for *something* — none of them do yet. Candidate
C is valuable but is a pure documentation consolidation with no capability
delta; it does not, by itself, close any operational gap. Candidate A is the
only option that converts an existing, real, already-approved-for-production
capability (commit/push) into governed-by-design rather than
governed-by-convention, and in doing so builds and exercises the exact
integration pattern that B, D, and E would each separately need to invent.

---

## 8. Candidate Evaluation Matrix

Scored 1 (worst) – 5 (best) per criterion; not a weighted sum, used for
relative comparison only.

| Criterion | A: Broker Consumption | B: Capability Elevation | C: State Lattice Doc | D: Generic Mutation | E: Evidence Framework |
|---|---|---|---|---|---|
| Strategic value | 5 | 4 | 3 | 4 | 3 |
| Dependency readiness | 5 (broker already frozen/tested) | 2 (no elevation mechanism exists at all) | 5 | 2 (needs A first) | 2 (needs A first) |
| Architectural risk | 2 (low — touches 2 existing commands) | 5 (high — new capability class) | 1 (very low) | 4 (high) | 3 |
| Governance risk | 2 (low — decision layer already policy-complete, fail-closed) | 5 (high — new authority surface) | 1 | 4 | 2 |
| Implementation complexity | 2 (wiring, not new design) | 5 | 1 | 5 | 3 |
| Testability | 5 (two real commands, deterministic policies) | 2 | 4 | 2 | 3 |
| Reversibility | 5 (broker denial = command still runs old path is not needed; broker call is additive and can be feature-scoped) | 2 (elevation grants are hard to fully reverse) | 5 | 2 | 3 |
| Runtime safety | 5 (no runtime-state change) | 2 | 5 | 3 | 4 |
| Contract maturity | 5 (POL-001..012 already frozen) | 1 | 3 | 1 | 2 |
| Operational usefulness | 5 (closes a real, named, 4-phase-old gap) | 3 | 2 | 3 | 2 |
| Path toward full v0.2 autonomy | 5 (necessary prerequisite for B/D/E) | 4 | 2 | 4 | 3 |
| Scope isolation | 5 (git commit/push only) | 2 | 5 | 2 | 3 |
| Overlap with completed chapters | 5 (none — Permission Broker was frozen, never certified as consumed) | 4 | 3 (overlaps AESIC boundary language) | 4 | 4 |

**Candidate A dominates.** It has the only combination of high strategic
value, low risk, and high dependency readiness — every other candidate
either presupposes A's outcome (B, D, E) or delivers no capability change at
all (C). Candidate C's content (the state lattice) is retained as a
required *sub-deliverable inside* Chapter 148's later contract-freeze phase
(148B), rather than promoted to its own chapter, because it has no
independent operational payoff and Candidate A's contract work will need to
state these distinctions precisely regardless.

---

## 9. Selected Strategic Capability

**Chapter 148: Permission Broker Production Consumption — Governed
Command-Path Integration.**

---

## 10. Strategic Rationale

Four independent lines of evidence converge on this gap:

1. Phase 144H (2026, pre-Authority-Evaluation chapter) already identified
   Runtime/Permission Broker implementation as "the largest true gap," and
   ranked it below the Interactive Workflow/Publication unlock only because
   that unlock was lower-risk at the time — not because the gap itself was
   smaller.
2. `docs/V0_2_AUTONOMY_ROADMAP.md`'s 17 Hard No-Go Conditions for any
   execution capability are unanimously ungated today, and its "Required
   Execution Capabilities (Not Yet Implemented)" list opens with "permission
   broker enforcement (not just simulation)."
3. Independent source inspection confirms this is not a design gap but a
   *wiring* gap: `permission_broker_foundation.py`'s `POL-001..012` policy
   framework is frozen, composed fail-closed (`DENY > HUMAN_REVIEW >
   ALLOW`), and stamped with an `implementation_status` field precisely
   because the authors already anticipated this exact chapter.
4. Phase 147R itself, in closing Authority Evaluation, explicitly recommends
   148A and explicitly instructs that runtime capability be preserved unless
   *separately authorized* — meaning Chapter 148 must find value without
   touching runtime state. Candidate A is the only candidate that delivers
   real strategic value while satisfying that constraint outright, because
   it operates entirely on capability (git mutation) that already exists
   outside the runtime/plugin model.

---

## 11. Problem Statement

PCAE has computed permission decisions since Phase 108 and has performed
real git mutation since (at latest) the introduction of `pcae commit` and
`pcae push`. These two facts have never been connected. Every root-mutating
operation PCAE actually performs today is gated by logic local to that one
command, not by the shared decision layer built to generalize governance
across all present and future mutating operations. This leaves PCAE with (a)
a well-tested enforcement brain with no body, and (b) two working mutation
paths whose safety depends on each command's own bespoke correctness rather
than a single, auditable, fail-closed chokepoint. Chapter 148 closes this by
making Permission Broker Foundation the mandatory, non-bypassable decision
point that `pcae commit` and `pcae push` consult before performing their
existing (unchanged) git operations.

---

## 12. Existing-System Constraints

- `src/pcae/core/permission_broker_foundation.py` (Phase 108A–C) is the
  contract-frozen implementation to build on — not
  `src/pcae/core/permission_broker.py` (Phase 88R/91A/91C), which is an
  older, richer but non-fail-closed evidence aggregator with a different
  24-value decision vocabulary. Consolidating the two brokers, or choosing
  between them for the long term, is itself an open question deferred to
  148B (see §33).
- `PolicyRule`s `POL-001..012` compose via `_compose()` as
  `DENY > HUMAN_REVIEW > ALLOW`, fail-closed by construction. `POL-005`
  (`ExecutionDisabledRule`) unconditionally denies any non-simulation
  request because `COMP-002` (execution capability) is `not_implemented`.
  This rule as currently written would deny commit/push outright if
  invoked naively — 148B must define precisely how commit/push (real,
  already-authorized git mutation, not "execution" in the runtime-plugin
  sense) are represented to the broker so `POL-005` does not misclassify
  already-legitimate git operations as unavailable runtime execution.
- `git commit`/`git push` are **not** runtime-plugin capability; they are a
  pre-existing, chapter-independent capability class. Chapter 148 must not
  imply that git mutation is being "unlocked" — it already works. The
  change is *where the decision is made*, not *what is allowed*.

---

## 13. Runtime Reality

`Observed / observe / unavailable` means:

- **Execution is not disabled by a flag that could simply be flipped** — no
  runtime adapter, plugin loader, or process-shared registry exists at all.
  `RuntimeRegistry()` is constructed fresh per CLI invocation
  (`src/pcae/commands/runtime_inspect.py`), so "Plugin count: 0" is not a
  configuration state, it is the *only* state reachable by the current
  architecture.
- The capability model is complete as a *vocabulary* (`CAPABILITY_CLASSES`,
  10 values including `enforce`/`execute`) but incomplete as a *mechanism* —
  `UNDECLARABLE_CAPABILITIES = frozenset({"enforce", "execute"})` makes
  `enforce`/`execute` structurally impossible for any plugin to declare,
  independent of policy.
- Permission enforcement is incomplete in the specific sense this chapter
  addresses: decisions exist, consumption does not.
- Execution orchestration, mutation boundaries beyond git, and rollback
  tied to enforcement are all structurally absent — not merely unimplemented
  behind a flag, but never wired to any dispatch point.
- There is no trusted production adapter for any runtime (`codex-local`,
  `claude-local`, `kimi-local` are all `trust: low/untrusted`, `contract:
  blocked`, `execution: blocked` per `docs/architecture/04-runtime-governance.md`).
- **Runtime activation is not the next architectural gap.** Activating a
  runtime capability tier today would have nothing durable to attach to,
  because the one component designed to arbitrate capability
  (Permission Broker) is not yet consulted by anything. Chapter 148 makes
  that arbitration real first, on a domain (git) where the consequences of
  a design mistake are small and already-reversible by existing git
  tooling, before any chapter proposes widening what can be arbitrated.

---

## 14. Permission Broker Analysis

**Currently decides:** for a described request (task-contract state,
shell-gate classification, scope-preflight result, explicit
health/check/doctor/test flags), one of `ALLOW / DENY / HUMAN_REVIEW /
MORE_EVIDENCE` (foundation model) or one of 24 finer-grained outcomes
(legacy model), composed fail-closed against an 11-item
`HARD_BLOCK_REGISTRY` (raw git commit/push, force push, `--no-verify`,
destructive filesystem, unknown command class, out-of-scope paths,
policy-forbidden files, missing task, missing readiness, missing
authorization).

**Currently does not decide:** anything, in the sense that no caller outside
its own CLI/tests ever asks it to. Every `PermissionBrokerDecision` is
stamped `implementation_status="execution_unavailable"` — even an `ALLOW`
today means "policy would allow this if a consumer existed," not "this was
allowed."

**Production wiring:** none. `pcae permission-broker evaluate/status/
explain/check/hard-blocks` are standalone diagnostic commands.

**Execution-path consumption:** none — confirmed by exhaustive call-site
search.

**Capability elevation:** none exists in either broker implementation.

**Denial enforceability:** N/A today — nothing is denied because nothing is
asked.

**Durability/replayability:** none. Decisions are in-memory dataclasses,
never persisted. `src/pcae/core/enforcement_audit.py` exists as a
design-only module not consulted by either broker — this is a required
148B/148C dependency (see §24, §29).

**Bypassability:** trivially bypassable today, because the only two real
mutation paths (commit/push) never call it. Chapter 148's entire value
proposition is closing exactly this bypass for those two paths.

**Assessment:** Chapter 148 should **consume** Permission Broker Foundation,
not extend its policy surface. `POL-001..012` are sufficient to reason
about git commit/push; new policy rules, if any prove necessary during
148B, should be additive (`POL-013+`), never a modification of frozen
`POL-001..012` semantics.

---

## 15. Runtime Enforcement Analysis

The Runtime Enforcement Decision Engine (`RED-*`) and Coordinator (`REC-*`,
both in `src/pcae/core/backend_invocations.py`) are contract-complete
dataclasses whose authorization fields (`execution_authorized`,
`push_authorized`, `commit_authorized`) are forced `False` by construction
contract (`simulation_only=True`, `design_only=True`). They model *runtime
plugin* invocation authorization — a different, broader problem than "should
this git commit proceed," and their contracts (Phases 101–104) were
explicitly frozen against a not-yet-existing plugin registry.

- Contracts complete: yes, for the runtime-plugin domain.
- Implementations exist: yes, as non-functional dataclasses (design proof,
  not behavior).
- Real command/file mutation connected: no.
- Execution evidence: no persisted evidence exists; only the accumulated
  `.pcae/execution-boundary-proof/` and `.pcae/execution-adjacent-plans/`
  directories hold JSON artifacts from prior phases' dry-run/proof
  mechanisms — real files, but proof-of-design artifacts, not operational
  evidence of an enforced decision.
- Rollback/recovery tied to enforcement: no.
- Runtime state transitions modeled: yes, as vocabulary
  (`LIFECYCLE_STATES`, 8 values) — not yet exercised by any real
  transition.

**The exact point where real execution currently stops:** between "a
decision is computed" and "a decision is consumed by the code path that
would act on it." This is true for both the runtime-plugin domain (Runtime
Enforcement) and the git-mutation domain (Permission Broker). Chapter 148
closes this gap for the git-mutation domain first, because it is the only
one of the two domains with a real, already-existing action (commit/push)
on the other side of the gap to consume the decision.

---

## 16. Execution Boundary Analysis

Tracing the hypothetical governed operation for the chosen domain (`pcae
commit` / `pcae push`, standing in for "agent proposes shell command" since
these are today's only real mutating commands):

| Step | Architecture | Contract | Implementation | Production wiring | Independent verification |
|---|---|---|---|---|---|
| Agent proposes commit/push | n/a — human/agent invokes CLI directly | n/a | yes | yes | n/a |
| PCAE recognizes mutation intent | implicit (the CLI command itself) | no explicit "intent" contract | n/a | yes (by virtue of being the command) | n/a |
| Authority/permission evaluated | Permission Broker Foundation exists | POL-001..012 frozen | yes | **no** | n/a (never exercised in production) |
| Runtime capability checked | Runtime Registry vocabulary exists | frozen | yes (vocabulary only) | n/a — git mutation is not a runtime-plugin capability | n/a |
| Enforcement decision made | ad hoc, per-command (readiness checks in `commit.py`/`push.py`) | none — not a formal contract | yes | yes (but not via Permission Broker) | not independently verified against a shared contract |
| Command dispatched | real `subprocess.run` in `commit.py`/`push.py` | none | yes | yes | n/a |
| Output captured | yes (diff-tree verification, push banner) | none | yes | yes | n/a |
| Side effects assessed | partial (staged-file conflict detection, diff-tree match) | none | yes | yes | n/a |
| Success/failure determined | yes | none | yes | yes | n/a |
| Rollback considered | no | none | no | no | n/a |
| Evidence persisted | partial (provenance events, phase reports) | none specific to permission decisions | partial | partial | n/a |

**Chapter 148 boundary:** insert a real Permission Broker Foundation
evaluation between "PCAE recognizes mutation intent" and "enforcement
decision made," replacing the ad hoc per-command readiness logic's *sole
authority* with a broker decision that the existing readiness logic then
supplies as additional evidence to (not replaces outright — see §33 for why
existing readiness checks are retained as inputs, not discarded).

---

## 17. Authority and Confirmation Boundaries

Chapter 148 introduces no new authority or confirmation semantics and must
not create any. It sits entirely within the existing, already-frozen
`Permitted` layer of the state vocabulary identified in research (see §29):

`Confirmed` (IWC-001) → `record-Confirmed` (CHGR) → `Eligible/Ineligible/
Indeterminate` (AESIC) → `Authorized` (human phase authorization language) →
**`Permitted` (Permission Broker — this chapter's domain)** → `Capable`
(runtime registry) → `Executed` (not yet real for any generic capability).

Per `IWC-REQ-029`, no Decision Session state may be "visible to, consumable
by, or capable of triggering any runtime capability change" — Chapter 148
does not touch Decision Sessions and must not introduce any code path by
which a Permission Broker decision could be mistaken for, or substituted
for, Confirmation, Authority Evaluation, or Publication. Conversely, per the
Authority Evaluation boundary (`src/pcae/authority_evaluation/__init__.py`:
"never grants, blocks, or conditions Confirmation, Readiness, Authorization,
or Publication"), Chapter 148 must not consume Authority Evaluation output
as a gating input to Permission Broker decisions — Authority Evaluation
stays strictly downstream/orthogonal, consulted (if at all) only as
disclosure, per the existing `authority_evaluation.stage_1_omitted_on_confirm`
logging pattern already established in `decision_session.py`.

---

## 18. Core Architecture

**Chapter 148 name:** Permission Broker Production Consumption.

**Problem statement:** see §11.

**Purpose:** make Permission Broker Foundation the single, non-bypassable
decision point for `pcae commit` and `pcae push`.

**Ownership boundaries:** Permission Broker Foundation owns the ALLOW/DENY/
HUMAN_REVIEW/MORE_EVIDENCE decision and its rationale. `commit.py`/`push.py`
retain ownership of *how* to gather the evidence the broker needs (task
state, git state, health/check results) and of the git operation itself.
The broker does not perform git operations; the commands do not make policy
decisions independent of the broker once wired.

**Trust boundaries:** the broker trusts evidence supplied by the calling
command (task-contract state, git status) exactly as much as that command
already trusts it today — no new trust is introduced, no new external input
crosses a boundary.

**Core components:** `PermissionBroker` (existing), a new thin **Command
Evidence Adapter** (148B/148D-scoped, not built in this phase) that
translates `commit.py`/`push.py`'s already-gathered readiness data into the
`PermissionRequest` shape the broker expects, and a **Decision Consumption
Point** inserted into each command's control flow immediately before the
real `git commit`/`git push` invocation.

**Lifecycle:** Request → Evidence Adapter → Broker `.evaluate()` → Decision
→ {`ALLOW`: proceed to existing git invocation; `DENY`: command exits
non-zero with broker rationale, no git operation attempted; `HUMAN_REVIEW`:
command exits non-zero, directs to human review path (mechanism TBD in
148B); `MORE_EVIDENCE`: command exits non-zero, reports what evidence is
missing}.

**Data model:** reuse `PermissionRequest`/`PermissionBrokerDecision`
dataclasses as-is; no new fields authorized in this phase (148B may find new
fields necessary — see §16/§33 open question).

**Persistence model:** none exists today; §24/§29 identify this as a
required 148C-scoped addition (audit persistence), not built here.

**Failure model:** see §26.

**Replay model:** see §27.

**Security model:** see §28.

**Integration points:** `src/pcae/commands/commit.py`,
`src/pcae/commands/push.py`, `src/pcae/core/permission_broker_foundation.py`.

**Explicit non-goals:** see §36.

---

## 19. Architectural Components

| Component | Responsibility | Inputs | Outputs | Authority | Persistence | Dependencies | Forbidden responsibilities |
|---|---|---|---|---|---|---|---|
| `PermissionBroker` (existing, `permission_broker_foundation.py`) | Compose `POL-001..012` into one decision | `PermissionRequest` | `PermissionBrokerDecision` | decision only | none (148C-scoped gap) | none new | must not perform git operations, must not read files directly |
| Command Evidence Adapter (new, 148B/148D) | Translate command-local readiness state into `PermissionRequest` | task-contract state, git status, health/check results already gathered by `commit.py`/`push.py` | `PermissionRequest` | none — pure translation | none | `commit.py`/`push.py` internals | must not itself decide ALLOW/DENY |
| Decision Consumption Point (new, 148B/148D) | Call broker, branch on decision before git invocation | `PermissionBrokerDecision` | proceed/abort | enforces the broker's decision | logs decision (148C) | `PermissionBroker`, `commit.py`/`push.py` | must not silently continue past DENY/HUMAN_REVIEW |
| `commit.py` / `push.py` (existing) | Gather git/task/health evidence, perform real git operation if allowed | repository state | git commit/push result | unchanged — still owns the actual git invocation | unchanged (provenance events) | Decision Consumption Point | must not bypass the Consumption Point once wired |

---

## 20. Canonical Data Flow

```
Agent/Human invokes `pcae commit` or `pcae push`
    ↓
Command gathers existing readiness evidence (unchanged logic)
    ↓
Command Evidence Adapter builds PermissionRequest
    ↓
PermissionBroker.evaluate()  →  PermissionBrokerDecision
    ↓
Decision Consumption Point
    ├── ALLOW  ──────────────→ existing git commit/push invocation (unchanged)
    ├── DENY  ───────────────→ abort, no git operation, rationale surfaced
    ├── HUMAN_REVIEW ────────→ abort, human-review path (mechanism: 148B)
    └── MORE_EVIDENCE ───────→ abort, missing-evidence report
    ↓
(148C-scoped) decision persisted as audit evidence
```

---

## 21. State Model

Minimal states, matching the existing decision vocabulary rather than
inventing new ones:

`proposed` (command invoked) → `evaluated` (broker returned a decision) →
`permitted` | `denied` | `review_required` | `evidence_required` →
`executed` (git operation ran; only reachable from `permitted`) |
`aborted` (reachable from `denied`/`review_required`/`evidence_required`).

Ownership: `commit.py`/`push.py` own `proposed`→`evaluated` transition (by
calling the broker); `PermissionBroker` owns which of the four
post-`evaluated` states is reached; `commit.py`/`push.py` own the
`permitted`→`executed` transition (unchanged git invocation) and all
`→aborted` transitions.

No `human_review` resolution mechanism is designed in this phase — 148B
must decide whether `HUMAN_REVIEW` today simply means "abort, rerun after a
human changes something out-of-band" (simplest, consistent with current
`pcae` command idioms) versus a new interactive gate (larger scope,
deferred unless 148B analysis shows it necessary).

---

## 22. Data Model

No new persistent data model is authorized in this phase. The existing
`PermissionRequest`/`PermissionBrokerDecision` dataclasses are reused
unchanged. 148B must determine whether `PermissionRequest` needs new fields
to represent git-commit/push-specific evidence (e.g., staged-file scope,
branch, unpushed-commit count) that the current shape does not carry — this
is flagged as an open question (§33), not resolved here, per the
architecture-only mandate.

---

## 23. Persistence

None exists today for permission decisions (confirmed: in-memory only, no
audit store consulted by either broker). This chapter's MVP (§35) can
function without new persistence — the existing provenance-event stream
already records `pcae commit`/`pcae push` outcomes, and a broker `DENY` that
aborts a command produces the same "nothing happened" state persistence
already handles correctly today. Durable, replayable, per-decision audit
records (distinct from provenance events) are identified as a 148C-scoped
enhancement, consuming the existing but currently-unconsulted
`src/pcae/core/enforcement_audit.py` design, not required for 148A/148B/148D
to deliver value.

---

## 24. Replay and Restart

Because the broker call sits entirely within a single synchronous CLI
invocation of `pcae commit`/`pcae push` — request, evaluation, and
git-dispatch all happen in one process, one command — the existing restart
semantics of those commands are unaffected:

- **Request before decision, process crash:** no git mutation attempted; safe.
- **Decision before execution, process crash:** decision is discarded
  (not yet persisted); rerunning the command re-evaluates from scratch —
  identical to today's behavior when `commit.py`/`push.py` crash before
  their existing git invocation.
- **Execution dispatch before result persistence:** unchanged from today's
  git-level atomicity (a `git commit`/`git push` either completes or it
  doesn't; PCAE does not currently persist a separate "dispatch record"
  distinct from the git object itself).
- **Restart after success/failure, duplicate retry:** unchanged — rerunning
  `pcae commit` on a clean tree is already a no-op today (nothing to
  commit); rerunning `pcae push` when already pushed already reports
  "nothing to push" (confirmed live: `pcae push check` → `Mode:
  nothing_to_push`). Adding a broker evaluation ahead of these idempotent
  operations does not change this.

No new replay hazard is introduced because no new asynchronous or
multi-step dispatch is introduced. This property is exactly why Candidate A
is lower-risk than Candidates B/D, which would require replay semantics for
genuinely new, potentially long-running or multi-step operations.

---

## 25. Failure Ownership

| Failure | Owner |
|---|---|
| Invalid/malformed request to broker | Command Evidence Adapter (must not construct an invalid `PermissionRequest`) |
| Permission denial | `PermissionBroker` (sole authority) |
| Broker itself raises/crashes | Decision Consumption Point treats as fail-closed DENY (deny-by-default per §13/§28) |
| Git command failure (post-ALLOW) | `commit.py`/`push.py`, unchanged from today |
| Postcondition failure (diff-tree mismatch, push not reflected) | `commit.py`/`push.py`, unchanged from today |
| Audit persistence failure (148C-scoped, future) | not owned by this phase; must not block the underlying git operation once ALLOW is already granted, to avoid a new denial-of-service surface — flagged for 148C |

No dual ownership is introduced: the broker owns exactly one thing (the
decision), the commands own everything they already own today
(evidence-gathering and git dispatch).

---

## 26. Rollback and Recovery

Rollback of the *decision* is not meaningful (a decision is not a mutation).
Rollback of the underlying git operation is unchanged from today: `pcae
commit` failures leave the working tree as git itself leaves it; `pcae
push` failures leave the remote unchanged (git push is atomic per-ref at
the remote). Chapter 148 introduces no new non-reversible operation and
therefore requires no new rollback mechanism to be "solved before production
execution is authorized" — the production capability (commit/push) was
already authorized and already shipping before this chapter.

---

## 27. Security Threat Model

| Threat | Addressed by Chapter 148? |
|---|---|
| Prompt-induced dangerous git operation (e.g., force-push, `--no-verify`) | **Yes** — `HARD_BLOCK_REGISTRY` already covers force push and `--no-verify`; this chapter is what finally makes that registry apply to real commit/push calls |
| Authority confusion (broker decision mistaken for Confirmation/Authorization) | Addressed architecturally by §17's strict layering; enforced by code review in 148D, not by this document alone |
| Permission bypass | **Directly addressed** — this chapter's entire purpose is closing the current bypass |
| Capability escalation | Not applicable — no new capability is granted |
| Shell injection / path traversal / symlink race | Out of scope — `commit.py`/`push.py` do not take untrusted path input beyond what they already validate; unchanged |
| Environment poisoning / plugin substitution / command substitution | Not applicable — no plugin dispatch involved |
| Replay attack / duplicate execution | Addressed by §24 — no new hazard introduced |
| Stale authorization | Deferred — the broker's `PermissionRequest` freshness (e.g., does a stale task-contract snapshot produce a stale ALLOW?) is a 148B analysis item |
| Concurrent conflicting operations | Out of scope — unchanged from today's single-agent-lock model |
| Rollback manipulation / audit deletion | Deferred to 148C (no audit persistence exists yet to manipulate) |
| Confused deputy | Addressed — the broker, not the command, is the deputy making the decision; the command cannot claim broker authority it wasn't granted |
| Agent identity spoofing | Out of scope — unchanged from today's existing agent-lock identity model |

Threats explicitly deferred (stale authorization freshness, audit
manipulation, concurrent conflicts) are deferred because they require
capability (persistence, multi-agent execution) this chapter does not add —
consistent with §36's non-goals.

---

## 28. Trust Boundaries

- **LLM/agent → PCAE lifecycle:** unchanged — the agent invokes `pcae
  commit`/`pcae push` as a CLI, same as today.
- **PCAE lifecycle → Permission Broker:** new trust relationship this
  chapter establishes — the lifecycle commands must trust the broker's
  decision as authoritative once wired (this is the whole point).
- **Permission Broker → runtime enforcement / OS:** none — the broker
  never touches the OS directly, only returns a decision.
- **PCAE lifecycle → git / repository:** unchanged, still the sole
  mutation surface, unchanged code path once ALLOW is granted.
- **PCAE lifecycle → network/remote (push):** unchanged.
- **PCAE lifecycle → human operator:** unchanged for ALLOW/DENY; a new,
  currently-undefined touchpoint for HUMAN_REVIEW is flagged for 148B.

No untrusted data newly crosses any boundary — the broker consumes the same
evidence the commands already gather from trusted, local repository state.

---

## 29. Contract Compatibility

- **Execution attempt boundary contracts (Phase 99):** not extended or
  amended; git commit/push are not "execution" in the
  `GovernedExecutionAttemptBoundary` sense (that contract concerns backend/
  runtime invocation) — 148B must state this distinction explicitly to
  avoid confusion.
- **Permission Broker contracts (Phase 108A–C, POL-001..012):** **consumed**,
  not amended. Any new policy needs (§14) are additive (`POL-013+`).
- **Runtime enforcement contracts (Phases 101–104):** unaffected — this
  chapter operates entirely outside the runtime-plugin domain those
  contracts govern.
- **Runtime/plugin contracts:** unaffected.
- **IWC-001/IWPC-001 (Confirmation, Decision Sessions):** unaffected;
  `IWC-REQ-029` explicitly forbids Decision Session state from gating
  runtime capability, and Chapter 148 does not touch Decision Sessions at
  all.
- **PEC-001/CHGR-001 (Publication):** unaffected.
- **AESIC-001 (Authority Evaluation):** unaffected; not consumed, not
  reopened.
- **Phase-report/finalization lifecycle:** unaffected — `pcae commit`/`pcae
  push` remain the same commands other lifecycle tooling already calls;
  their external contract (CLI surface, exit codes for success) is
  preserved. New DENY/HUMAN_REVIEW/MORE_EVIDENCE exit paths are additive,
  not breaking, provided 148D preserves existing exit-code conventions for
  the ALLOW path.

**Preference:** this chapter requires no amendment to any certified
contract. A new, standalone contract (148B: Permission Broker Production
Consumption Contract) is preferred over touching any existing frozen
contract, consistent with "prefer additive new contracts over destabilizing
certified contracts."

---

## 30. Operational Considerations

`pcae commit`/`pcae push` are invoked by existing lifecycle tooling
(finalization, phase completion) as well as directly by agents/humans. 148D
implementation must preserve current success-path behavior byte-for-byte
for the common case (an already-permitted commit/push continues to work
exactly as today) to avoid regressing the 4391-test `fast_green` baseline or
any lifecycle automation that shells out to these commands.

---

## 31. Minimum Safe MVP

The smallest slice that provides real strategic value: **governed
consumption of Permission Broker Foundation by `pcae push` only**, gating
solely the `HARD_BLOCK_REGISTRY` conditions already defined (force push,
raw/unreviewed push, `--no-verify`-equivalent bypass) — not `pcae commit`,
and not any new policy surface. `pcae push` is preferred as the MVP target
over `pcae commit` because it is the higher-consequence, less-frequent
operation (remote-visible, harder to locally undo) and because its existing
`assess_push_readiness()` already gathers most of the evidence a
`PermissionRequest` needs, minimizing new Evidence Adapter surface. This
satisfies "governed deterministic tool operation" from the suggested MVP
classes without building "full autonomous shell access," and it directly
answers the roadmap's standing observation that Permission Broker is
"capability-complete but consumed nowhere" using the single highest-value,
lowest-risk consumer available today.

`pcae commit` consumption, any `POL-013+` additions, and the HUMAN_REVIEW
resolution mechanism are explicitly follow-on scope (148D+), not part of
the MVP.

---

## 32. Explicit Non-Goals

Chapter 148 explicitly excludes:

- Arbitrary network access, arbitrary root/system mutation, package
  installation, secret management, remote deployment, production
  environment mutation, unrestricted shell, multi-host execution,
  cross-repository mutation — none of these are anywhere near this
  chapter's scope.
- Automatic capability elevation — no runtime capability changes.
- Autonomous push (in the sense of PCAE deciding *to* push without a
  human/agent invoking the command) — this chapter only decides whether an
  *already-invoked* push is permitted, never initiates one.
- Generic shell/subprocess execution, generic file mutation outside git,
  plugin dispatch, capability elevation lifecycle — all deferred to
  hypothetical later chapters, contingent on this chapter's outcome.
- Consolidating or removing the legacy `permission_broker.py` — a design
  question for 148B, not decided here.
- Any Human-Review interactive resolution mechanism beyond "abort and
  report" — deferred to 148B.

---

## 33. Risks and Open Questions

- **Broker consolidation:** two Permission Broker implementations exist.
  148B must decide whether the legacy `permission_broker.py` is formally
  deprecated, or whether both remain for different purposes (e.g. legacy as
  richer diagnostic evidence, foundation as the enforcement authority).
- **`PermissionRequest` shape sufficiency:** does the existing dataclass
  carry enough fields to represent commit/push evidence precisely, or does
  148B need to define additive fields?
  - **`POL-005` (`ExecutionDisabledRule`) misclassification risk:** as
  written, this rule denies "any non-simulation request" because runtime
  execution capability is `not_implemented`. 148B must define how the
  Evidence Adapter marks git commit/push requests so this rule does not
  incorrectly deny already-legitimate, already-shipping git mutation
  meant for a different capability domain than "runtime execution."
- **HUMAN_REVIEW resolution mechanism:** undefined; simplest option
  (abort-and-rerun-after-human-intervenes-out-of-band) is likely sufficient
  for MVP but should be confirmed in 148B rather than assumed here.
- **Audit persistence timing:** whether 148C (persistence) must land before
  148D (implementation) ships, or can follow it, is a sequencing choice for
  148B — this document does not mandate an order beyond "persistence is not
  required for MVP value" (§23).

No Blocking architectural contradiction was found. These are open questions
for the *next* phase to resolve, not defects in this architecture.

---

## 34. Proposed Chapter 148 Phase Sequence

- **148A** — Next Strategic Capability Architecture (this document).
- **148B** — Permission Broker Production Consumption Contract Freeze:
  resolve §33's open questions, define the `PermissionRequest`
  representation for git commit/push evidence, define the HUMAN_REVIEW
  resolution mechanism, define the broker-consolidation decision, formally
  incorporate the §17 state-lattice distinctions (Candidate C's content) as
  contract language rather than a separate chapter.
- **148C** — Contract-adjacent audit persistence design (consume
  `enforcement_audit.py`, define durable/replayable decision records) —
  may run in parallel with or precede 148D per 148B's sequencing decision.
- **148D** — Independent Contract Verification.
- **148E** — Implementation (MVP: `pcae push` consumption only, per §31).
- **148F** — Independent Implementation Verification.
- **148G** — Production Wiring / extension to `pcae commit`.
- **148H** — Independent Production Verification.
- **148I** — Operational Readiness / Chapter Certification.

This sequence is proposed, not authorized; only 148B is recommended for
authorization by this document (§42).

---

## 35. Overall Architecture Verdict

**NEXT STRATEGIC CAPABILITY ARCHITECTURE COMPLETE.**

Selected Chapter 148 capability: **Permission Broker Production
Consumption — Governed Command-Path Integration**, targeting `pcae commit`
and `pcae push` as its first real consumers, with `pcae push` alone as the
Minimum Safe MVP.

---

## 36. Recommended Next Phase

**148B — Permission Broker Production Consumption Contract Freeze.**

148B shall convert this architecture into a normative contract: freeze
responsibilities (Broker decides, commands dispatch), freeze the
`PermissionRequest`/`PermissionBrokerDecision` interface (including any
additive fields resolved from §33), freeze lifecycle semantics (§20/§21),
freeze persistence and replay semantics (§23/§24 — explicitly stating audit
persistence is deferred, not silently omitted), freeze failure ownership
(§25), freeze security boundaries (§27/§28), and define verification
requirements for 148D. 148B shall explicitly preserve runtime state
(`Observed / observe / unavailable`) unless later implementation is
separately authorized, and shall explicitly preserve every Chapter 147
Authority Evaluation boundary (§17) without amendment.

This recommendation is not authorization.

---

## 37. Validation

Run at bootstrap (§1) and reconfirmed before this document was finalized:

```
pcae session bootstrap --agent-id claude-local --sync-lock   → healthy, check passed
pcae check                                                    → passed
pcae health                                                   → healthy
pcae doctor task-memory                                       → clean
pcae runtime inspect                                          → Observed / observe / unavailable (unchanged)
pcae push check                                                → clean, nothing_to_push
```

No `src/pcae/**` files were modified. No new CLI commands, plugins,
contracts, or schemas were added or amended. No commits were created
containing production implementation. This document is the sole artifact
produced by this phase; `python -m pytest -m fast_green` was not re-run
since no production or test file changed (per the phase's own validation
instructions, focused regression runs are optional when no such files
change).

Runtime confirmed unchanged: **Observed / observe / unavailable.**
