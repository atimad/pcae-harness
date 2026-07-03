# Phase 112B — Runtime Context Contract Freeze

## Purpose

Freeze the canonical Runtime Context contracts 112A designed: the
exact immutable identities, state models, ownership, persistence
expectations, relationships, and invariants for every Runtime Context
object, before any Runtime Context implementation begins. Contract/
freeze only — no runtime behavior changes, no Runtime Context
implementation, no execution capability exists after this phase, only
its frozen contract.

## Scope

- `docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md` — the contract: a new
  principle (`Identity precedes state`), a contract-freeze overview
  cross-referencing all twelve 112A objects, per-object Identity
  Contracts (identifier, uniqueness, immutability, lifetime,
  ownership), a canonical six-stage State Contract shared by all
  twelve objects plus per-object reachable ceilings, per-object
  Ownership Contracts (creates/owns/updates/archives/observes),
  per-object Persistence Contracts refining 112A §7 into four buckets,
  a resolved Relationship Contract (Broker Decision reordered before
  Approval, extended to the two future stubs past Evidence), nine
  frozen invariants (112A's seven, one resolved, two added), and an
  explicit, evidence-cited resolution of both findings 112A deferred.
- `docs/PHASE_112_RUNTIME_CONTEXT_CONTRACT_FREEZE.md` — this document.
- `tests/test_runtime_context_contract.py` — documentation-verification
  tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. `docs/ROADMAP.md` was evaluated for an update; see §9 below.

## 1. Contract Freeze Overview Summary

The complete contract for every one of 112A's twelve Runtime Context
objects is frozen — no object is added, removed, or reshaped relative
to 112A §3. This document adds identity, state, ownership, persistence,
relationship, and invariant precision to objects 112A already named,
and resolves the two questions 112A explicitly deferred rather than
guessed at.

## 2. Identity Contract Summary

Twelve identifiers frozen (`session_id` through `rollback_id`, plus
`RuntimeContext`'s explicit non-identity, since it is a root aggregate
scoped to the active `RuntimeSession` rather than independently
identified). For each: uniqueness, immutability, lifetime, and
ownership are specified. Two real, already-working precedents ground
the format requirements without inventing new ones: `task_id`'s
`YYYYMMDD-HHMM-<slug>` format (`tasks/done/`) and `phase_id`'s bare
identifier format (`"112A"`, `PROJECT_STATUS.md`). `session_id` is
named honestly as not yet a concrete field in the real
`.pcae/session.json` (which identifies a session by `timestamp` today)
— the contract freezes the requirement, not a pre-existing format.

## 3. State Contract Summary

One canonical six-stage transition table (`Created → Initialized →
Observed → Updated → Completed → Archived`, 112A §4) is frozen for all
twelve objects, with explicit valid transitions, the terminal-state
rule (`Archived` unconditionally terminal; `Completed` a resting stage
for persistent/future-persistence objects, replaced by discard-at-
session-end for session-only/never-persist objects), and invalid
transitions (skips, backward moves, and any transition into
`Executing`/`Executed`/`RolledBack`, unconditionally forbidden). A
per-object ceiling table freezes the highest stage each object reaches
today: `Archived` for the three objects with real filesystem precedent
(`RuntimeSession`, `TaskContext`, `PhaseContext`); `Updated` for
`IntentContext` and `ObservationContext`; `Created` for every object
gated on an unimplemented component (`ApprovalContext`,
`BrokerDecisionContext`, `EvidenceContext`, and the three future
stubs); `Initialized` for the root `RuntimeContext` aggregate.

## 4. Ownership Contract Summary

Per-object creates/owns/updates/archives/observes table frozen,
directly extending 112A §5's category-level split. No row grants any
Plugin, Broker, or Registry a create/update/archive action over any
Context object — the Broker produces decisions (unchanged, 108A–108D)
but never creates or owns the `BrokerDecisionContext` wrapping one;
Plugins implement capabilities (unchanged, 110B §1) but never own any
Context object.

## 5. Persistence Contract Summary

112A §7's per-concept persistence model is refined into four buckets
(**Persistent**, **Session-only**, **Future persistence**, **Never
persist**) for all twelve objects. One deliberate sharpening is named
explicitly: 112A used "session-only/ephemeral" loosely for both Broker
Decision and Observation state; this document distinguishes them —
`ObservationContext` is genuinely held in memory for a session
(**Session-only**), while `BrokerDecisionContext` is discarded within a
single expression evaluation and never retained even for the session's
duration (**Never persist**), per 109D's already-frozen "bare,
never-assigned expression" pattern. The three future stubs are bucketed
by what they will eventually need once their underlying component
exists: `ExecutionContext` stays session-only/transient even once
implemented (the durable record is Evidence/Audit's job); `AuditContext`
and `RollbackContext` are **Future persistence**, for the same reason
112A already gave Approval and Evidence.

## 6. Relationship Contract Summary

Chain resolved to **Intent → Broker Decision → Approval → Evidence →
(future) Execution → (future) Audit → (future) Rollback**, reordering
112A's presentation to match 110A §5's frozen "Decision Pipeline →
Approval" interface and 110A §8's frozen state sequence exactly (§8.2).
Per-link cardinality restated and extended: Task:Phase is many-to-one
over a Phase's lifetime with at most one active Task per Phase at any
moment (resolving §8.1); Broker Decision:Approval is one:one for
decisions requiring approval; Execution→Audit and Audit→Rollback
directly mirror 110A §8's own `Executed → Audited → Rollback Ready`
sequence.

## 7. Invariant Contract Summary

Nine invariants frozen: 112A's seven, with "Phase belongs to one Task"
**resolved** into "at most one Task is active per Phase at any given
moment" (§8.1), plus two new invariants — "Broker Decision precedes
Approval" (resolving §8.2's ordering tension) and "Identity is
immutable and precedes state" (freezing this document's own new
principle as a testable invariant, restating that `Created` *is* the
act of identity assignment, not a step preceding it).

## 8. Resolution of Deferred Findings Summary

Both findings 112A named explicitly, rather than silently assumed, are
resolved here with cited evidence, not by default:

- **Task:Phase cardinality vs. the Task:Phase invariant** — resolved
  by recognizing the two claims describe different axes (cumulative
  lifetime cardinality, many-to-one, vs. concurrent-moment cardinality,
  at-most-one-active), both already true and already evidenced by this
  codebase's own agent-lock invariant and `tasks/DONE.md` history —
  not a new design decision, a naming of which axis the original
  invariant's word "belongs" referred to.
- **Approval vs. Broker Decision ordering** — resolved in favor of
  Broker Decision preceding Approval, citing 110A §5's frozen "Decision
  Pipeline → Approval" interface and 110A §8's frozen state sequence
  (`Observed` before `Approved`) — two independent, already-frozen
  citations that agree, neither reinterpreted by this document.

## 9. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content, as every
110/111/112-series phase before it has been. This phase adds one new
principle (`Identity precedes state`) and resolves two named findings;
it introduces no new object, no new capability, and no new roadmap
milestone — the roadmap's standing ordering text already covers this
vision at a coarser grain, matching 112A's own evaluation outcome.
**No change to `docs/ROADMAP.md` was needed or made.**

## Execution Integration Status

Unchanged from 112A — this phase adds no new command-path integration,
touches no source code, and introduces no execution capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Safety Case

- **Why this phase cannot introduce execution capability:** it touches
  no file under `src/pcae/` — its task contract's allowed files are
  limited to documentation files, one test file, and standard
  status-tracking files, mirroring 112A's own task contract exactly.
- **Why the contract freeze itself cannot silently become an
  implementation:** every table in this document (identity, state,
  ownership, persistence, relationship, invariant) is prose and
  markdown tables only — no code, no schema, no data structure any
  runtime could load or execute. Freezing a *contract* is freezing what
  a future implementation must satisfy, not satisfying it.
- **Why resolving two deferred findings here is itself a safety
  property, not scope creep:** 112A explicitly named both questions as
  112B's responsibility (112A §6, §8, Limitations) rather than leaving
  them silently unresolved for an implementation phase to guess at —
  resolving them now, with cited evidence, before any implementation
  exists, is exactly the discipline 112A's own deferral was designed to
  produce.
- **Why the persistence bucket refinement is a sharpening, not a
  reversal:** every object's bucket in §5 traces directly to 112A §7's
  own reasoning; the one refinement (splitting "session-only/ephemeral"
  into distinct Session-only and Never-persist buckets for Observation
  and Broker Decision respectively) is grounded in 109D's own
  already-frozen "bare, never-assigned expression" evidence, not a new
  assumption.

## Limitations

- This phase freezes the Context *contract*; it does not validate that
  contract against a prototype implementation, since none exists (112C,
  Runtime Context Prototype (Observation-Only), is the recommended next
  phase, mirroring the 110D→110E and 111A→111B pattern this arc has
  already followed twice: design, then contract, then prototype).
- No identifier generation algorithm, serialization format, or storage
  schema is designed here — §2's identity contracts state uniqueness/
  immutability/lifetime *requirements*, not concrete formats, except
  where real precedent (`task_id`, `phase_id`) already fixes one.
- The persistence contract (§5) remains architecture-only, per 112A's
  own scope boundary — it recommends which bucket each object belongs
  to, but designs no storage mechanism for any bucket.

## No-Go Confirmations

No Runtime Context implementation. No persistence implementation. No
database. No serialization. No runtime execution. No plugin loading.
No plugin instantiation. No plugin invocation. No dependency
injection. No shell mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No
Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST endpoint.
No web UI. No daemon. No background worker. No automatic apply.
`implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed`. Current maximum plugin
capability remains `observe`. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**112C — Runtime Context Prototype (Observation-Only).**
