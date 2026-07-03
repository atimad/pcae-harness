# Phase 112A — Runtime Context Architecture

## Purpose

Design how PCAE models the current operational state of the Runtime
while preserving the complete non-executing guarantees established
through 111R. This is architecture/design only — no Runtime Context
implementation, persistence implementation, or execution capability
exists after this phase, only its frozen design.

## Scope

- `docs/PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md` — the architecture: Runtime
  Context defined, the Persistent/Session Context split, a twelve-object
  model (design only), a six-stage Context Lifecycle (a third, distinct
  lifecycle vocabulary alongside 110A §8 and 110B §4), frozen ownership,
  the Context relationship chain (with cardinality findings grounded in
  this session's own real operational evidence), a per-concept
  Persistence Model directly answering 111R's recommendation condition,
  and seven frozen Context invariants.
- `docs/PHASE_112_RUNTIME_CONTEXT_ARCHITECTURE.md` — this document.
- `tests/test_runtime_context_architecture.py` — documentation-
  verification tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. `docs/ROADMAP.md` was evaluated for an update; see §8 below.

## 1. Runtime Context Architecture Summary

Runtime Context is frozen as the Runtime's dynamic operational model —
what is happening now, as distinct from what is architecturally
possible (110A), what exists (110B–111D), or what can be observed about
static state (111A/111B). It describes; it never executes — the same
"surfaces, never decides" discipline 110C §5 (Registry) and 111A §1
(Introspection) already established, applied a third time. This
document is the design 110C §8's own "Dynamic runtime... a future
phase, not implemented here" was deferring to, and the design 111B's
deferred `SessionInfo`/`TaskInfo`/`PhaseInfo` needs before it can be
completed. Core principle extended with this phase's own addition:
**Context precedes execution** — a future execution-capability phase
must be able to name the exact session/task/phase/intent/approval/
decision an action belongs to before that action could ever be
authorized.

## 2. Persistent vs Session Context Summary

Two categories frozen, generalizing 110C §8's static/dynamic split:
**Persistent Context** (Runtime identity, Registry, plugin/capability
metadata, Runtime version, contracts — scoped to the whole Runtime,
forever) and **Session Context** (Session, Task, Phase, Intent,
Approval state, Broker decision, Evidence, Observation state — scoped
to one unit of work). Explicitly clarified: this is a distinction about
*conceptual scope*, not about whether data is physically persisted to
disk today — Session/Task/Phase are Session Context by scope, yet all
three already have real, working, filesystem-backed persistence
predating this arc.

## 3. Context Object Model Summary

Twelve objects frozen, design only: `RuntimeContext`, `RuntimeSession`,
`TaskContext`, `PhaseContext`, `IntentContext`, `ApprovalContext`,
`BrokerDecisionContext`, `EvidenceContext`, `ObservationContext`, and
three explicitly future/stub objects — `ExecutionContext`,
`AuditContext`, `RollbackContext`. `ExecutionContext` exists
conceptually; its current, only meaningful state is
`execution_unavailable` — named now so a future phase has a vocabulary
to design against, exactly as 110A §8 named `Executed` without making
it reachable.

## 4. Lifecycle Summary

Six stages frozen for a Context object's own existence — `Created`,
`Initialized`, `Observed`, `Updated`, `Completed`, `Archived` — a
distinct vocabulary from both 110A §8's Runtime State Model (an
*intent's* pipeline progression) and 110B §4's Plugin Lifecycle (a
*plugin's* existence). Future execution states (`Executing`/`Executed`/
`RolledBack`) are explicitly not added to this generic model; they
remain the domain of 110A §8 and the future `ExecutionContext`/
`AuditContext`/`RollbackContext` objects specifically.

## 5. Ownership Summary

Runtime owns Context lifecycle, current context, and context
transitions. Registry owns metadata (unchanged). Plugins own capability
implementation (unchanged). The Broker owns policy decisions
(unchanged). Context never owns execution, approval decisions, or
policy evaluation. This is the third instance, across this arc, of the
same "surfaces facts, never decides" discipline (110C §5, 111A §1, and
now this document) — the repetition is the reason nine consecutive
phases (110A–111D) have stayed safely non-executing.

## 6. Relationship Summary

Chain frozen: Session → Task → Phase → Intent → Approval → Broker
Decision → Evidence → (future) Execution. Two evidence-grounded
findings recorded rather than assumed: (1) **Task:Phase cardinality is
many-to-one**, not the naive one-to-many a top-down diagram might
suggest — verified directly against this session's own operational
pattern (every 110–111 series phase was served by one-or-more tasks,
never the reverse); (2) an **ordering tension between Approval and
Broker Decision** is named, not resolved — 110A §5's frozen "Decision
Pipeline → Approval" interface implies the Broker's decision precedes
Approval, the opposite of this chain's literal presentation order; left
as an explicit open question for 112B (contract freeze).

## 7. Persistence Model Summary

Direct answer to 111R's recommendation condition — per-concept, not
uniform: Session/Task/Phase should (and already do) persist. **Intent**
recommended session-only until Evidence exists to make its persistence
accountable (fail-closed reasoning). **Approval** and **Evidence**:
should eventually persist once implemented; nothing exists to persist
yet (a "not applicable" answer, distinct from "in-memory only").
**Broker decision** and **Observation state**: deliberately
session-only/ephemeral, as a *continuation* of 109B–109D's already-
frozen "consult and discard" safety property, not a new choice —
persisting broker decisions would require its own dedicated future
phase with an explicit safety re-analysis, out of 112A's scope
entirely. What must never persist (secrets, credentials, tokens, raw
untyped manifest content) is inherited unchanged from 111A §8 and
110E/110F/111C's manifest-exclusion precedent.

## 8. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This phase
adds one new principle (Context precedes execution) and one new
object model, consistent in kind with every prior phase-scoped
principle addition (Discoverable always, 110C; Metadata precedes
behavior, 110E; Visibility precedes authority, 111A) — none of which
required a roadmap change, since the roadmap's standing ordering text
already covers this vision at a coarser grain. **No change to
`docs/ROADMAP.md` was needed or made**, matching every prior
110/111-series phase's own evaluation outcome.

## Execution Integration Status

Unchanged from 111R — this phase adds no new command-path integration,
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
  limited to two documentation files, one test file, and standard
  status-tracking files.
- **Why the Context design itself cannot silently become an
  implementation:** every concept in this document (objects, lifecycle,
  ownership, relationships, persistence model) is prose-only — no code,
  no schema, no data structure any runtime could load or execute.
- **Why naming tensions honestly (Task:Phase cardinality, Approval/
  Broker Decision ordering) is itself a safety property:** silently
  picking an answer to either open question here, without the
  dedicated design attention a contract-freeze phase gives it, would
  risk baking an unexamined assumption into a future implementation —
  this document's discipline of naming, not resolving, both tensions
  is deliberate, not an oversight.
- **Why the persistence model cannot be mistaken for an implementation
  commitment:** every recommendation in §7 is phrased as "should
  eventually," "not yet," or "deliberately ephemeral" — none claims
  anything persists as a result of this phase, and the Broker-decision/
  Observation-state entries explicitly state persisting them is out of
  this phase's scope entirely, not merely deferred.

## Limitations

- This phase designs the Context *shape*; it does not validate that
  shape against a prototype implementation, since none exists (112B,
  contract freeze, is the recommended next phase, mirroring the
  110C→110D and 111A→111B pattern of design-then-contract-then-
  prototype).
- Two open questions are named, not resolved, and are explicitly
  112B's to resolve: the Task:Phase cardinality invariant's apparent
  contradiction with this session's own real operational pattern, and
  the Approval/Broker Decision ordering tension against 110A §5's
  frozen interface table.
- The persistence model (§7) is architecture-only — it recommends what
  *should* eventually persist and what must never persist, but designs
  no storage mechanism, schema, or format for any of it.

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

**112B — Runtime Context Contract Freeze.**
