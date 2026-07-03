# PCAE Runtime Context Contract

**Frozen by**: Phase 112B | **Status**: contract/freeze only — no Runtime
Context implementation, persistence implementation, serialization,
database, runtime execution, plugin loading, plugin instantiation,
plugin invocation, dependency injection, shell mediation, backend
invocation, adapter invocation, execution enablement, execution
capability, Permission Broker enforcement, audit persistence, rollback
execution, emergency stop, Telegram inbound, REST endpoint, web UI,
daemon, background worker, or automatic apply is performed by this
document or this phase.

## Purpose

Phase 112A designed Runtime Context — the Runtime's dynamic operational
model — as twelve objects (a field sketch, not a schema), a six-stage
lifecycle, ownership rules, a relationship chain, and a per-concept
persistence model. It deliberately left two questions open rather than
guessing: the apparent contradiction between its own Task:Phase
cardinality evidence and its own Task:Phase invariant wording, and the
ordering of Approval against Broker Decision in the relationship chain.
This document is the contract freeze 112A named as its own recommended
next phase: the exact, immutable contract for every one of the twelve
Context objects — identity, state, ownership, persistence, relationship,
and invariant — frozen *before* any Runtime Context implementation
begins, and the two deferred findings resolved deliberately, not by
default.

This document changes no source file. It builds on, and changes none
of, `docs/PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md` (112A) or any earlier
110/111-series document; where this document's resolutions differ from
112A's presentation (§6, §8 below), the difference is named explicitly
as a resolution, not a silent contradiction.

## New Principle: Identity Precedes State

The core principle, restated from 112A with this phase's own addition:

```
Runtime orchestrates.
Registry resolves.
Plugins implement.
Metadata precedes behavior.
Visibility precedes authority.
Context precedes execution.
Identity precedes state.
```

**Rationale.** §3 below freezes a state contract for every Context
object — initial state, valid transitions, terminal states, invalid
transitions. None of that is meaningful without first knowing *which*
object is transitioning: a state transition is a fact about a
specific, identified thing, not a free-floating event. §2 (Identity
Contracts) therefore must be, and is, frozen before §3 (State
Contracts) in this document's own ordering — a Context object is
`Created` (112A §4's first lifecycle stage) precisely by being
assigned an identity; no object may be `Initialized`, `Observed`,
`Updated`, `Completed`, or `Archived` before it has one. This is the
same kind of standing ordering constraint "Context precedes execution"
(112A) already names for a different pair of concepts, applied here to
identity and state specifically.

## 1. Contract Freeze Overview

The complete contract for every one of 112A's twelve Runtime Context
objects is frozen across §2–§7 below. No object gains, loses, or
changes shape relative to 112A §3 — this document adds identity,
state, ownership, persistence, relationship, and invariant precision
to objects 112A already named; it does not introduce a thirteenth
object or remove any of the twelve.

| # | Object | Identity (§2) | State ceiling today (§3) | Owner (§4) | Persistence bucket (§5) |
|---|---|---|---|---|---|
| 1 | `RuntimeContext` | none (root aggregate) | `Initialized` | Runtime | Session-only |
| 2 | `RuntimeSession` | `session_id` | `Archived` (real precedent) | Runtime | Persistent |
| 3 | `TaskContext` | `task_id` | `Archived` (real precedent) | Runtime | Persistent |
| 4 | `PhaseContext` | `phase_id` | `Archived` (real precedent) | Runtime | Persistent |
| 5 | `IntentContext` | `intent_id` | `Updated` | Runtime | Session-only |
| 6 | `ApprovalContext` | `approval_id` | `Created` (stub — `COMP-003` not implemented) | Runtime | Future persistence |
| 7 | `BrokerDecisionContext` | `decision_id` | `Created` (produced-and-discarded) | Runtime | Never persist |
| 8 | `EvidenceContext` | `evidence_id` | `Created` (stub — `COMP-007` not implemented) | Runtime | Future persistence |
| 9 | `ObservationContext` | `observation_id` | `Updated` | Runtime | Session-only |
| 10 | `ExecutionContext` *(future)* | `execution_id` | `Created` (stub — `execution_unavailable`) | Runtime | Never persist (today) |
| 11 | `AuditContext` *(future)* | `audit_id` | `Created` (stub) | Runtime | Future persistence |
| 12 | `RollbackContext` *(future)* | `rollback_id` | `Created` (stub) | Runtime | Future persistence |

Every cell above is expanded, with rationale and citations, in the
sections that follow. No cell is a new design decision — each is a
freeze of what 112A already implied, or a deliberate, named resolution
of a question 112A left open (§8).

## 2. Identity Contracts

Twelve identifiers are frozen, one per object, following the exact
naming 112A §3's objective list already anticipated (`session_id`
through `rollback_id`). `RuntimeContext` is the one exception, named
below.

| Object | Identifier | Uniqueness | Immutability | Lifetime | Ownership (who assigns) |
|---|---|---|---|---|---|
| `RuntimeContext` | *(none)* | N/A — not independently identified; the root aggregate is scoped to, and addressed through, whichever `RuntimeSession` it currently references (112A §3, object 1). | N/A | One per running Runtime instance/process. | Runtime |
| `RuntimeSession` | `session_id` | Unique per session; the real precedent (`.pcae/session.json`, predating this arc) identifies a session by its `timestamp` field today — no explicit `session_id` field exists yet in the real file. A future implementation may adopt the timestamp itself as `session_id`, or mint a distinct value; this document freezes only that the identifier must be unique *per session*, not the concrete format. | Immutable once assigned — a session's identity never changes mid-session, including across handoffs (a handoff changes the active agent, not the session identity). | From `RuntimeSession` creation (`pcae session bootstrap`) until session end. | Runtime |
| `TaskContext` | `task_id` | Globally unique by construction — the real, already-working precedent is the `YYYYMMDD-HHMM-<slug>` task ID this codebase's own task contracts already use (e.g. `20260703-2059-phase-112a-runtime-context-architecture`, `tasks/done/`), unique by timestamp + content-derived slug. | Immutable once assigned — a task is never renamed or re-identified across `pause`/`resume`/`complete`. | From `pcae task new` until the task contract is archived (moved to `tasks/done/`) — the task contract file itself is retained indefinitely after that, per real precedent. | Runtime |
| `PhaseContext` | `phase_id` | Unique per phase — the real precedent is the bare phase identifier already used throughout this codebase (`"112A"`, `"111R"`, in `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`), unique because the roadmap never reuses a phase ID. | Immutable once assigned. | From the phase's first task's creation until the phase's completion metadata is archived — which, per real precedent, is never (phase history is retained permanently in `PROJECT_STATUS.md`/`CHANGELOG.md`/`tasks/DONE.md`). | Runtime |
| `IntentContext` | `intent_id` | Unique per proposed action, scoped to the owning `PhaseContext` (112A §3, object 5). | Immutable once assigned. | From the moment an Intent Source produces a well-formed intent (110A §5's frozen "Intent Sources → Runtime" interface) until the intent's owning `PhaseContext` archives. | Runtime |
| `ApprovalContext` | `approval_id` | Conceptually one per `IntentContext` requiring approval (112A §6's "conceptually one:one" cardinality) — not implemented anywhere today, since `COMP-003` does not exist. | Immutable once assigned. | From creation until its owning Intent's context archives. | Runtime (would wrap `COMP-003`'s outcome, once implemented; never self-assigned) |
| `BrokerDecisionContext` | `decision_id` | One per Decision Pipeline consultation (110A §2's Decision Pipeline stage) — scoped to a single `IntentContext`. | Immutable — a `PermissionBrokerDecision` (108A), once produced, does not change; this is a direct restatement of the Broker's own already-frozen evaluate-only, no-side-effects contract (108A–108D), not a new rule. | For exactly the duration of one Decision Pipeline consultation — today, that duration is a single expression evaluation, per 109D's "bare, never-assigned expression" pattern; the identifier's real lifetime is not longer than any object that wraps it. | Runtime (wraps a decision the Broker, `COMP-001`, already produced — Runtime never mints the decision itself, only the wrapping identity) |
| `EvidenceContext` | `evidence_id` | One-or-more per `BrokerDecisionContext`, conceptually (112A §6) — not implemented anywhere today, since `COMP-007` (Audit Boundary) does not exist. | Immutable once assigned — an evidence record's identity, once created, is permanent, consistent with the append-only precedent this codebase already uses elsewhere for accountable history (`.pcae/strategic-lineage.json`). | From creation, permanently — evidence is never re-identified or reused. | Runtime (would wrap `COMP-007`'s output, once implemented) |
| `ObservationContext` | `observation_id` | One per `RuntimeSession` — an aggregate, not a per-consultation record (112A §3, object 9: "which of the four `INT-NNN` entries... have been consulted... for the current session"). | Immutable identity; the object's *contents* update as more `INT-NNN` entries are consulted (§3), but its identity does not change. | For the duration of one `RuntimeSession`. | Runtime |
| `ExecutionContext` *(future)* | `execution_id` | Would be one per attempted execution, once execution exists. | Immutable once assigned (once implemented). | Today: N/A — the object is a frozen stub with exactly one meaningful field (`status = execution_unavailable`, 112A §3); no `execution_id` is ever minted while execution remains unavailable. | Runtime |
| `AuditContext` *(future)* | `audit_id` | Would be one per audited outcome, once implemented. | Immutable once assigned (once implemented). | Today: N/A — frozen stub, no field beyond a not-implemented marker (112A §3). | Runtime |
| `RollbackContext` *(future)* | `rollback_id` | Would be one per verified rollback path, once implemented. | Immutable once assigned (once implemented). | Today: N/A — frozen stub, no field beyond a not-implemented marker (112A §3). | Runtime |

**No identifier is generated, minted, or validated by this document.**
Every "uniqueness" cell above states a *requirement* a future
implementation phase must satisfy (or, where real precedent already
exists — `TaskContext`, `PhaseContext` — a requirement it already
does), not a concrete algorithm this document implements.

## 3. State Contracts

Every Context object shares one generic state machine — 112A §4's
six-stage lifecycle (`Created → Initialized → Observed → Updated →
Completed → Archived`) — frozen once here as the canonical transition
table, rather than restated twelve times. Object-specific *ceilings*
(the highest stage a given object can reach given what exists in this
codebase today) are frozen separately, immediately below.

### 3.1 Canonical transition table (applies to all twelve objects)

| From | Valid transitions to | Rationale |
|---|---|---|
| `Created` | `Initialized` | The only valid next stage — an object must be populated before it can be read (112A §4). |
| `Initialized` | `Observed`, `Updated` | Once populated, the object may be read (`Observed`) or changed (`Updated`) — either may happen first; neither is required before the other. |
| `Observed` | `Updated`, `Completed` | An observed object may later change, or the unit of work it represents may finish. |
| `Updated` | `Observed`, `Updated`, `Completed` | An updated object may be re-observed, updated again (the self-loop covers repeated field changes — e.g. a `TaskContext`'s status changing more than once), or complete. |
| `Completed` | `Archived` | The only valid next stage once the underlying unit of work has finished. |
| `Archived` | *(none — terminal)* | No object resumes activity after archival; this is the one unconditionally terminal stage. |

**Terminal states.** `Archived` is the only unconditionally terminal
stage. `Completed` is a resting stage, not a terminal one, for objects
whose persistence bucket (§5) is `Persistent` or `Future persistence`
— those are expected to reach `Archived` eventually. For objects whose
persistence bucket is `Session-only` or `Never persist` (`Intent`,
`Observation`, `Broker Decision`, and the three future stubs while
`execution_unavailable` holds), the object's real lifecycle ends by
**discard at session end**, not by transitioning through `Completed` →
`Archived` — discard is not itself a seventh lifecycle stage (112A §4
already fixed the vocabulary at six stages; this document does not
reopen it), it is simply the absence of any further transition once
the owning `RuntimeSession` ends.

**Invalid transitions (apply to all twelve objects, unconditionally):**

- Any transition that **skips a stage** (`Created` → anything but
  `Initialized`; `Initialized` → `Completed` or `Archived` directly;
  any stage → `Archived` except from `Completed`).
- Any transition **backward** (`Archived` → anything; `Completed` →
  `Observed`/`Updated`/`Initialized`/`Created`; `Observed`/`Updated` →
  `Initialized`/`Created`).
- Any transition **into or through `Executing`/`Executed`/
  `RolledBack`** — these remain, unconditionally, 110A §8's Runtime
  State Model vocabulary and the future `ExecutionContext`/
  `AuditContext`/`RollbackContext` objects' own eventual domain (112A
  §4's "Future execution states remain explicitly out of scope"),
  never a state any of the twelve objects' own six-stage lifecycle may
  enter. This is restated here as an *invalid transition*, not merely
  an absent one, because it is the transition an execution-capability
  implementation phase might otherwise be tempted to add directly to
  this lifecycle rather than to the Runtime State Model where it
  belongs.

### 3.2 Per-object ceilings (today)

| Object | Initial state | Reachable ceiling today | Why the ceiling |
|---|---|---|---|
| `RuntimeContext` | `Created` | `Initialized` | The root aggregate is populated with references (current session, Registry) but is never itself "observed," "updated," "completed," or "archived" as a unit — those lifecycle events belong to the objects it references, not to the aggregate itself. |
| `RuntimeSession` | `Created` | `Archived` | Real precedent: `.pcae/session.json` already models a session's full lifecycle including its end. |
| `TaskContext` | `Created` | `Archived` | Real precedent: `tasks/active/` → `tasks/done/` is exactly `Completed` → `Archived` already, today. |
| `PhaseContext` | `Created` | `Archived` | Real precedent: `.pcae/phase-completion-metadata.json` plus permanent retention in `PROJECT_STATUS.md`/`tasks/DONE.md`. |
| `IntentContext` | `Created` | `Updated` | Nothing today advances an intent past `Observed`/`Updated` (110A §8: current maximum runtime state is `Observed`) — `Completed` would require the intent's unit of work to finish, which requires execution capability that does not exist. |
| `ApprovalContext` | `Created` | `Created` | `COMP-003` does not exist; nothing populates this object's required fields, so it cannot advance to `Initialized`. |
| `BrokerDecisionContext` | `Created` | `Created` | Produced and discarded within a single expression (109D) — never held long enough to be populated as a persistent object, let alone observed or updated as one. |
| `EvidenceContext` | `Created` | `Created` | `COMP-007` does not exist. |
| `ObservationContext` | `Created` | `Updated` | The four `INT-NNN` integrations are real and already consulted every session — this object's aggregate state genuinely changes as each is consulted, but the session itself never "completes" as a unit of work in the way a task or phase does. |
| `ExecutionContext` *(future)* | `Created` | `Created` | Frozen stub; `status = execution_unavailable` is the object's only field, and that field's value never changes while execution remains unavailable. |
| `AuditContext` *(future)* | `Created` | `Created` | Frozen stub; no field beyond a not-implemented marker. |
| `RollbackContext` *(future)* | `Created` | `Created` | Frozen stub; no field beyond a not-implemented marker. |

## 4. Ownership Contracts

112A §5 froze ownership at the category level (Runtime owns lifecycle/
current-context/transitions; Registry owns metadata; Plugins own
capability implementation; the Broker owns policy decisions; Context
never owns execution, approval decisions, or policy evaluation). This
section freezes the same split per object, per action.

| Object | Creates | Owns | Updates | Archives | Observes |
|---|---|---|---|---|---|
| `RuntimeContext` | Runtime (at Runtime startup) | Runtime | Runtime | N/A — lives with the process, never independently archived | Introspection layer *(future)* |
| `RuntimeSession` | Runtime (`pcae session bootstrap`) | Runtime | Runtime | Runtime (session end) | Introspection *(future `SessionInfo`, 111B's deferral)* |
| `TaskContext` | Runtime (`pcae task new`) | Runtime | Runtime (`pcae task update`/`pause`/`resume`) | Runtime (`pcae task complete`/`finish`) | Introspection *(future `TaskInfo`)* |
| `PhaseContext` | Runtime | Runtime | Runtime | Runtime (`pcae phase complete`) | Introspection *(future `PhaseInfo`)* |
| `IntentContext` | Runtime (on receiving a well-formed intent, 110A §5) | Runtime | Runtime (as the intent moves through the pipeline) | Runtime | Introspection *(future)* |
| `ApprovalContext` | Runtime — *wrapping* `COMP-003`'s eventual outcome; never self-created | Runtime | Runtime, recording an outcome `COMP-003` (not implemented) would produce — never the object deciding for itself (112A §5: "Context never owns... Approval decisions") | Runtime | Introspection *(future)* |
| `BrokerDecisionContext` | Runtime — *wrapping* a `PermissionBrokerDecision` the Broker (`COMP-001`, 108A) already produced | Runtime | N/A — immutable once wrapped (§2) | N/A — never persisted, discarded at end of consultation | Introspection *(future, for the single consultation's duration only)* |
| `EvidenceContext` | Runtime — *wrapping* `COMP-007`'s eventual output | Runtime | N/A — append-only once created (§2) | Runtime | Introspection *(future)* |
| `ObservationContext` | Runtime (first `INT-NNN` consultation of the session) | Runtime | Runtime (each subsequent `INT-NNN` consultation) | N/A — never persisted, discarded at session end | Introspection *(future)* |
| `ExecutionContext` *(future)* | Runtime (stub only, today) | Runtime | N/A today — frozen at `execution_unavailable` | N/A | Introspection *(future)* |
| `AuditContext` *(future)* | Runtime (stub only, today) | Runtime | N/A today | N/A | Introspection *(future)* |
| `RollbackContext` *(future)* | Runtime (stub only, today) | Runtime | N/A today | N/A | Introspection *(future)* |

**No row above grants any Plugin, Broker, or Registry a create/update/
archive action over any Context object.** This is deliberate and
restates 112A §5's ownership split precisely: the Broker *produces* a
decision (its own, unchanged job, 108A–108D) but never creates or owns
the `BrokerDecisionContext` object that wraps it; a Plugin *implements*
a capability (110B §1, unchanged) but never creates or owns any
Context object referencing it.

## 5. Persistence Contracts

This section refines 112A §7's per-concept Persistence Model into the
four buckets this contract freeze requires — **Persistent**,
**Session-only**, **Future persistence**, **Never persist** — for all
twelve objects (112A §7 covered eight concepts; the four not previously
covered — `RuntimeContext`, `RuntimeSession` as its own object row,
`ObservationContext`'s object row, and the three future stubs — are
completed here).

| Object | Bucket | Rationale |
|---|---|---|
| `RuntimeContext` | Session-only | The root aggregate is scoped to the current Runtime instance/session; it is never itself written to disk — only the persistent things it *references* (Registry, Runtime version) are persistent, and those are already covered by 110C/110E, unchanged. |
| `RuntimeSession` | Persistent | Already does — `.pcae/session.json` (112A §7, unchanged). |
| `TaskContext` | Persistent | Already does — task contract files (112A §7, unchanged). |
| `PhaseContext` | Persistent | Already does — `.pcae/phase-completion-metadata.json` and phase reports (112A §7, unchanged). |
| `IntentContext` | Session-only | 112A §7, unchanged: no durable audit/evidence mechanism exists yet to make stored intent history accountable; fail-closed choice is to stay ephemeral until Evidence exists. |
| `ApprovalContext` | Future persistence | 112A §7, unchanged: should eventually persist once `COMP-003` exists; nothing to persist today — a "not applicable yet" answer, not "in-memory only." |
| `BrokerDecisionContext` | Never persist | **Sharpened from 112A's "session-only/ephemeral" wording.** 112A used "session-only" loosely for both Broker Decision and Observation state; this contract freeze distinguishes them precisely: `ObservationContext` is genuinely held in memory for the session's duration (§3 shows it reaching `Updated`, its contents changing as the session progresses), while a `BrokerDecisionContext` is never held at all beyond a single expression evaluation (109D's "bare, never-assigned expression" pattern, §2's lifetime column) — it is discarded immediately, not retained for the session. "Never persist" is the more precise bucket; persisting it durably remains, as 112A stated, out of scope entirely, requiring its own dedicated future phase with an explicit safety re-analysis. |
| `EvidenceContext` | Future persistence | 112A §7, unchanged: should eventually persist once `COMP-007` exists; nothing to persist today. |
| `ObservationContext` | Session-only | Genuinely held in memory for the current session (§3: reaches `Updated` as more `INT-NNN` entries are consulted) but never written to disk — mirrors 109B–109D's "consult and discard" safety property for the underlying integrations themselves, unchanged. |
| `ExecutionContext` *(future)* | Never persist (today) | Frozen stub; `status = execution_unavailable` is not a fact requiring durable storage. **Once execution capability exists** (a future, separately-authorized phase), the in-flight execution state this object would model is expected to remain Session-only/transient — the durable record of an execution attempt is `EvidenceContext`/`AuditContext`'s job, not `ExecutionContext`'s; this document does not decide that a future phase must follow this expectation, only names it as the current design intent, consistent with §6's relationship chain routing Execution → (future) Audit, not the reverse. |
| `AuditContext` *(future)* | Future persistence | Once `COMP-007`/an Audit Boundary exists, an audited outcome is exactly the kind of fact needing a durable, accountable record — the same reasoning 112A already gave for Approval and Evidence. Nothing to persist today; frozen stub. |
| `RollbackContext` *(future)* | Future persistence | Once a Rollback Boundary (`COMP-008`) exists, a verified rollback path is likewise a fact needing durable review evidence. Nothing to persist today; frozen stub. |

**What must never persist**, restated unchanged from 112A §7 (itself
unchanged from 111A §8 and 110E/110F/111C's manifest-exclusion
precedent): secret material, credentials, tokens, and raw untyped
`manifest` content, regardless of which object above would otherwise
carry it. This rule is a field-level constraint that applies inside
every bucket above, including `Persistent` — persisting a `TaskContext`
does not mean persisting secrets a task might reference.

## 6. Relationship Contracts

**Resolved chain** (see §8.2 for the full resolution rationale):

```
Session
  |
  v
Task
  |
  v
Phase
  |
  v
Intent
  |
  v
Broker Decision
  |
  v
Approval
  |
  v
Evidence
  |
  v
(future) Execution
  |
  v
(future) Audit
  |
  v
(future) Rollback
```

This reorders 112A §6's presentation — which placed Approval before
Broker Decision and named, without resolving, the tension against
110A §5's frozen "Decision Pipeline → Approval" interface — to match
that already-frozen interface exactly (§8.2). The chain is also
extended two links past 112A's own scope boundary (Evidence → future
Execution), naming the two remaining future stubs' position in the
chain: Execution → future Audit → future Rollback, directly mirroring
110A §8's own state sequence (`Executed → Audited → Rollback Ready`).

**Cardinality, per link:**

- **Session : Task** — one Session has zero-or-more Tasks over its
  lifetime; at most one Task is *active* at any given moment (112A §6,
  unchanged — the real, already-enforced agent-lock invariant).
- **Task : Phase** — many-to-one over a Phase's full lifetime (112A
  §6's evidence-grounded finding, unchanged); **at most one Task is
  *active* for a given Phase at any given moment** (§7's resolution of
  the invariant tension, §8.1).
- **Phase : Intent** — one Phase's work is composed of one-or-more
  Intents; each Intent belongs to exactly one Phase (112A §6,
  unchanged).
- **Intent : Broker Decision** — one Decision Pipeline consultation per
  Intent, conceptually one:one (110A §2's Decision Pipeline stage
  consulted once per intent) — not implemented as a standalone,
  reachable stage today (110A §2, unchanged); every real consultation
  today is one of the four `INT-NNN` observation integrations,
  themselves 1:1 with the read-only command invocation that triggered
  them.
- **Broker Decision : Approval** — conceptually one:one for any
  decision requiring approval (a `HUMAN_REVIEW` decision, or per
  INV-003 any executable `ALLOW` — 110A §5's frozen interface,
  unchanged); zero Approval outcomes exist for a decision that requires
  none. Not implemented anywhere today, since `COMP-003` does not
  exist.
- **Approval : Evidence** — one-or-more Evidence records per approved
  (or denied) Intent's eventual outcome, conceptually (112A §6's
  "Broker Decision : Evidence" cardinality carried forward one link,
  since Evidence now follows Approval in the resolved chain, §8.2) —
  not implemented anywhere today.
- **Evidence → (future) Execution** — named as the eventual next link
  (112A §6, unchanged); the state model this link would reference
  (110A §8) is already frozen and requires no redesign here.
- **(future) Execution → (future) Audit** — directly mirrors 110A §8's
  `Executed → Audited` sequence; an executed action is expected to
  produce exactly one audited outcome (110A §5's frozen "Execution
  Adapter → Audit" interface: "every execution attempt... must produce
  exactly one evidence record").
- **(future) Audit → (future) Rollback** — directly mirrors 110A §8's
  `Audited → Rollback Ready` sequence; an audited outcome is expected
  to have, at most, one associated verified rollback path.

## 7. Invariant Contracts

Nine invariants are frozen — 112A §8's seven, with the Task:Phase
invariant **resolved** (not merely restated) and two invariants added
(one resolving §8.2's ordering tension, one freezing `Identity
precedes state`, this document's own principle addition).

1. **Exactly one active Runtime Context** — unchanged from 112A §8.
2. **Task belongs to one Session** — unchanged from 112A §8.
3. **At most one Task is active per Phase at any given moment**
   (**resolved**, replacing 112A §8's "Phase belongs to one Task" —
   see §8.1 below for the full resolution).
4. **Intent belongs to one Phase** — unchanged from 112A §8.
5. **Broker Decision precedes Approval** (**new**, resolving §8.2's
   named ordering tension — see §8.2 below).
6. **Execution unavailable** — unchanged, unconditional, restated from
   every prior phase in this arc.
7. **Observation always available** — unchanged from 112A §8; no
   Context object may gate or disable observation.
8. **No Context object may itself execute, approve, or evaluate
   policy** — unchanged from 112A §8 (itself §5's ownership split,
   restated as a testable invariant).
9. **Identity is immutable and precedes state** (**new** — freezes
   this document's own principle addition as a citable, testable
   invariant): every Context object's identifier (§2), once assigned,
   never changes for that object's lifetime, and no object may be
   `Initialized`, `Observed`, `Updated`, `Completed`, or `Archived`
   (§3) before its identity is assigned. `Created` (112A §4's first
   lifecycle stage) *is* the act of assigning identity — the two are
   not sequential steps within `Created`, they are the same event.

## 8. Resolution of Deferred Findings

112A named two questions explicitly rather than silently picking an
answer, and named both as this phase's responsibility to resolve
(112A §6, §8, Limitations). Both are resolved here, deliberately, with
the evidence each resolution rests on.

### 8.1 Task:Phase cardinality vs. the "Phase belongs to one Task" invariant

**The tension, as 112A left it.** 112A §6 found, against this session's
own real operational evidence, that Task:Phase cardinality is
many-to-one — every phase in the 110–111 series was served by
one-or-more governed tasks (typically an implementation task, then a
separate metadata-sync task), never the reverse. Yet 112A §8's own
invariant list stated "Phase belongs to one Task," whose literal
reading is the opposite cardinality (one Task per Phase, i.e. a Phase
cannot outlive or span more than one Task) — a direct contradiction
112A named but declined to resolve unilaterally.

**Resolution.** The invariant is restated as: **at most one Task is
*active* for a given Phase at any given moment** (§7, invariant 3) —
not a claim about a Phase's total lifetime Task count, but a claim
about concurrent ownership at any single instant. This resolves the
contradiction because the two claims are about different axes
entirely: §6's finding is about *cumulative* cardinality over a Phase's
full lifetime (how many Tasks, in total, ever served this Phase — many,
per the evidence); the invariant is about *concurrent* cardinality at
any one instant (how many Tasks are active for this Phase *right now*
— at most one). Both are true simultaneously, and this session's own
real evidence already demonstrates it: the already-enforced agent-lock
invariant (112A §6's Session:Task cardinality note; this codebase's own
`pcae task` behavior — `pcae health`'s "Agent lock" field) guarantees
at most one active task platform-wide, which trivially implies at most
one active task per phase at any moment, while `tasks/DONE.md`'s own
history shows many completed tasks accumulating against the same phase
ID over that phase's lifetime. The resolution is therefore not a new
design decision — it is naming which of two already-true, already-
evidenced facts the word "belongs" in the original invariant should
have referred to, and stating it unambiguously so no future
implementation phase has to guess.

### 8.2 Approval vs. Broker Decision ordering

**The tension, as 112A left it.** 112A §6 presented its relationship
chain in the order Approval, then Broker Decision, while noting
directly that 110A §5's already-frozen Runtime Interfaces table names
"Decision Pipeline → Approval" as one of eight interfaces — implying
the Broker's decision is consulted *before*, not after, an Approval
outcome. 112A declined to silently pick a side, naming this
explicitly as an open question for 112B.

**Resolution.** The chain is reordered to **Intent → Broker Decision →
Approval → Evidence** (§6 above), matching 110A §5 and §8 exactly, for
two independent, mutually-reinforcing pieces of already-frozen
evidence:

1. **110A §5's Runtime Interfaces table** states the contract in this
   exact direction: "Decision Pipeline → Approval | A decision of
   `HUMAN_REVIEW` or (per INV-003) any executable `ALLOW` must reach an
   explicit human approval step before proceeding." The interface
   named is Decision-Pipeline-*to*-Approval, not the reverse — the
   Broker's decision is the input that determines *whether* an
   Approval step is even required, which is only coherent if the
   decision is known first.
2. **110A §8's Runtime State Model** places the same ordering in its
   own frozen state sequence: `Observed` ("The Permission Broker has
   been consulted and produced a decision") occurs three states before
   `Approved` ("An explicit human approval has been recorded for this
   specific intent"), with `Advisory` between them. An intent cannot
   reach `Approved` without first passing through `Observed` — the
   broker consultation is structurally prior, in the one runtime state
   sequence this entire arc has already frozen and never revisited.

Both citations independently agree, and neither has been touched or
reinterpreted by this document — 112B's resolution is to make 112A's
own presentation consistent with architecture this codebase already
froze in 110A, not to invent a new ordering. 112A's presentation was
not wrong about the objects themselves (Approval and Broker Decision
are both still Context objects 5–7 and 6–7 respectively per §1's
table), only about the order it listed them in the chain diagram; this
resolution corrects that ordering, and §6's cardinality note above
(Broker Decision : Approval, one:one for decisions requiring approval)
follows directly from it.

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
maximum runtime state remains `Observed` (110A §8, unchanged). Current
maximum plugin capability remains `observe` (110B §3, unchanged).
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**112C — Runtime Context Prototype (Observation-Only).**
