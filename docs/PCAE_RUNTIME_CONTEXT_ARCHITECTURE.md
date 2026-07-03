# PCAE Runtime Context Architecture

**Frozen by**: Phase 112A | **Status**: architecture/design only — no
Runtime Context implementation, persistence implementation, database,
serialization, runtime execution, plugin loading, plugin
instantiation, plugin invocation, dependency injection, shell
mediation, backend invocation, adapter invocation, execution
enablement, execution capability, Permission Broker enforcement, audit
persistence, rollback execution, emergency stop, Telegram inbound,
REST endpoint, web UI, daemon, background worker, or automatic apply
is performed by this document or this phase.

## Purpose

Design how PCAE models the current operational state of the Runtime,
while preserving the complete non-executing guarantees established
through 111R. 110A froze the Runtime's static architecture; 110B–110F
froze and built the Registry's metadata layer; 111A–111D froze and
built the Introspection layer that reads that metadata. None of these
nine phases described *what the Runtime is currently doing* — a
specific session's active task, a specific phase's current intent,
whether that intent has been approved, what the broker decided, what
evidence exists. That missing layer is Runtime Context, designed (not
implemented) here. It is also the layer 111B's own deferral of
`SessionInfo`/`TaskInfo`/`PhaseInfo` was waiting on (111B §1: "Each of
those three domains already has a full, working, filesystem-backed
precedent... a materially different scope... left to a future phase")
and the layer 111R's review named as the central open design question
before any further Runtime work (111R Finding R-5).

This document builds on, and changes none of:

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A) — the Runtime, the
  seven-stage pipeline, the nine Runtime Services (which name Session/
  Task/Phase/Identity/Configuration as concepts the Runtime exposes,
  without designing their live shape), and the eight-state Runtime
  State Model (`Intent → Observed → ... → Rollback Ready`), which
  describes an *intent's* pipeline progression, not a *context
  object's* own lifecycle (§4 below is a distinct vocabulary).
- `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B) — plugin contracts,
  capability taxonomy, and the eight-state Plugin Lifecycle model,
  which describes a *plugin's* existence, not a context object's.
- `docs/PCAE_RUNTIME_SERVICE_REGISTRY.md` (110C) §8 — the static/
  dynamic runtime split this document's §2 directly generalizes (110C
  §8 named "session, task, phase, intent, approval, broker decision,
  execution state" as "Dynamic runtime... explicitly a future phase,
  not implemented here." This document is that future phase's design.)
- `docs/PCAE_RUNTIME_INTROSPECTION.md` (111A) and
  `src/pcae/core/runtime_introspection.py` (111B) — the read-only
  visibility layer this document's Context objects would, in a future
  phase, become new Introspection objects/domains for (completing
  111B's deferred `SessionInfo`/`TaskInfo`/`PhaseInfo`).
- `docs/PCAE_RUNTIME_ARCHITECTURE_REVIEW.md` (111R) — this document is
  the direct answer to that review's §11 recommendation condition: an
  explicit, per-concept Persistence Model decision, not a uniform
  default (§7 below).

## Core Architectural Principle

```
Runtime orchestrates.
Registry resolves.
Plugins implement.
Metadata precedes behavior.
Visibility precedes authority.
```

Extended with this phase's own addition:

```
Context precedes execution.
```

Every prior 110/111-series phase asked "what can the Runtime *do*"
(110A), "what can the Runtime *know*" (110B–110F), or "what can the
Runtime *show*" (111A–111D). This phase asks a fourth question: "what
is the Runtime *currently doing*" — and answers it before any future
phase asks "what may the Runtime be *authorized* to do." A future
execution-capability phase must be able to name the exact session,
task, phase, intent, approval, and broker decision an action belongs
to *before* that action could ever be authorized — not as an
afterthought bolted onto an execution mechanism, but as a
precondition designed first. "Context precedes execution" names that
ordering as a standing constraint, extending "Visibility precedes
authority" (111A) from *read visibility* to *contextual accountability*:
visibility answers "can a human see what the Runtime knows"; context
answers "can the Runtime itself say what a specific action was *for*."

## 1. Runtime Context, Defined

**Definition.** Runtime Context is the Runtime's dynamic operational
model: the set of objects describing what is happening now, as opposed
to what is architecturally possible (110A), what plugins and
capabilities exist (110B–111D), or what can be observed about that
static state (111A/111B). Context is inherently time-varying — it is
created, changes, and eventually completes or archives (§4) — unlike
the largely static Registry/Contract material every prior phase in
this arc has modeled.

**Context describes; it never executes.** Restated as the sharpest
possible boundary: no Context object, and no operation this document
names, may invoke a plugin, evaluate a policy, grant an approval, or
run a command. This is the same "surfaces, never decides/executes"
discipline 110C §5 already established for the Registry and 111A §1
established for Introspection, applied a third time to a third layer.
A `TaskContext` recording that a task is `Updated` does not cause
anything to update — it is *told* that an update already happened, by
the Runtime (§5), and its only job is to hold that fact so it can
later be read.

**Relationship to Introspection.** Context objects are not
Introspection objects, but every Context object this document designs
is intended to become the backing shape for a corresponding
Introspection object in a future phase — most directly, `TaskContext`/
`PhaseContext`/a session-scoped context object are the design 111B's
deferred `TaskInfo`/`PhaseInfo`/`SessionInfo` needs before it can be
implemented. Context is the *state*; Introspection is the *read path*
onto that state. This document does not design that read path (a
future phase's responsibility) — only the state it would read.

**Current implementation status: not implemented.** No Context module,
class, or object exists in `src/pcae/` as a result of this phase. This
document is the design a future implementation phase (112B, contract
freeze, then a 112C-style prototype) would build against — the same
two-step pattern 110C→110D→110E and 111A→111B already followed twice.

## 2. Persistent vs Session Context

Two categories are frozen, directly generalizing the static/dynamic
split 110C §8 already named without designing:

| | **Persistent Context** | **Session Context** |
|---|---|---|
| **Scope** | The whole Runtime, for its entire operating life | One unit of work — one session, task, phase, intent, etc. |
| **Examples** | Runtime identity, Registry, Plugin metadata, Capability metadata, Runtime version, Contracts | Session, Task, Phase, Intent, Approval state, Broker decision, Evidence, Observation state |
| **Precedent** | 110C §8's "Static runtime" | 110C §8's "Dynamic runtime" |
| **Answers** | "What does this Runtime know how to do, forever?" | "What is this Runtime doing right now, for this specific piece of work?" |

**Why separate.** Persistent Context is what every other concept in the
110–111 series has already modeled (the Registry, 110E/110F; plugin
contracts, 110B) — it does not reset, does not belong to any one
session, and is consumed by anything asking "what is this Runtime
capable of." Session Context is scoped, transient by nature, and
consumed by anything asking "what is currently happening" — exactly
the question 111R Finding R-4 found `pcae runtime inspect` structurally
cannot answer today, because nothing in this category has been
designed until now.

**Important clarification — scope, not disk persistence.** "Persistent
vs Session" is a distinction about *conceptual scope*, not about
whether the underlying data is physically written to disk today.
Session, Task, and Phase are each categorized as Session Context
(§2 above, per the objective's own example list) — yet each already has
real, working, filesystem-backed persistence today (`pcae session
bootstrap`, task contract files, phase-completion-metadata.json),
predating this entire arc. Their Session Context classification
reflects that they are *scoped to one unit of work*, not that they are
unwritten to disk. §7 below addresses actual persistence recommendations
per concept, separately from this scope classification.

## 3. Runtime Context Object Model (Design Only — No Implementation)

Twelve objects are frozen as the shapes a future implementation phase
would build. Each is a design-time field sketch, not a class,
dataclass, or any concrete Python construct — no object below exists in
`src/pcae/` as a result of this phase, mirroring exactly how 111A §4
froze eleven Introspection objects and 110C §3 froze a fifteen-field
manifest concept without implementing either.

| # | Object | Represents | Field sketch (illustrative) | Category |
|---|---|---|---|---|
| 1 | `RuntimeContext` | The top-level aggregate a Runtime instance would hold | reference to the currently active `RuntimeSession` (if any); references to Persistent Context (Registry, Runtime version) | Root — spans both categories |
| 2 | `RuntimeSession` | One working session | session ID, start time, continuity status, active identity | Session Context |
| 3 | `TaskContext` | One active or historical task | task ID, title, allowed files/zones, status, lifecycle state (§4), owning `RuntimeSession` | Session Context |
| 4 | `PhaseContext` | One governed phase | phase ID, title, completion status, owning relationship to one-or-more `TaskContext` (§6 cardinality note) | Session Context |
| 5 | `IntentContext` | One proposed action (110A §8's `Intent` state, given a concrete shape) | intent ID, description, originating source, timestamp, owning `PhaseContext` | Session Context |
| 6 | `ApprovalContext` | One intent's human-approval status | approval status (conceptual: pending/granted/denied), owning `IntentContext` — **not implemented anywhere** (`COMP-003` Human Approval Gate, 107B, still not implemented) | Session Context |
| 7 | `BrokerDecisionContext` | One Permission Broker decision, contextualized | wraps a `PermissionBrokerDecision` (108A, unmodified) with its owning `IntentContext` | Session Context |
| 8 | `EvidenceContext` | One evidence record (110A's Evidence Pipeline, `COMP-007`) | evidence shape, owning `BrokerDecisionContext` — **not implemented anywhere** (Audit Boundary, 107B, still not implemented) | Session Context |
| 9 | `ObservationContext` | Aggregate observation-integration state | which of the four `INT-NNN` entries (109C) have been consulted, and when, for the current session | Session Context |
| 10 | `ExecutionContext` *(future)* | What would eventually model `Executable`/`Executed` (110A §8) | today, frozen with exactly one meaningful field: status = `execution_unavailable` | Session Context, future |
| 11 | `AuditContext` *(future)* | What would eventually model `Audited` (110A §8) | today, frozen as a stub — no field beyond a not-implemented marker | Session Context, future |
| 12 | `RollbackContext` *(future)* | What would eventually model `Rollback Ready` (110A §8) | today, frozen as a stub — no field beyond a not-implemented marker | Session Context, future |

**`ExecutionContext` exists conceptually; its current state is
`execution_unavailable`.** Naming this object now — as a frozen stub,
never a live capability — gives a future phase a vocabulary to design
against, exactly as 110A §8 named `Executed` as a state without making
it reachable, and exactly as 110B §3 named `execute` as a capability
class no plugin may currently declare. `AuditContext` and
`RollbackContext` are named for the same reason and are equally inert.

**No implementation.** No field list above is a frozen schema — a
future implementation phase chooses the concrete representation
(dataclass, TypedDict, JSON Schema), exactly as 110C §3's manifest
concept and 111A §4's Introspection objects were each frozen as field
lists first, implemented (with concrete Python types) only in the
phase after their contract was frozen (110D→110E, 111A→111B).

## 4. Lifecycle (Design Only)

Six lifecycle stages are frozen for a Context object's own existence —
**a distinct vocabulary from both** 110A §8's Runtime State Model
(which describes an *intent's* progression through the seven-stage
pipeline) **and** 110B §4's Plugin Lifecycle (which describes a
*plugin's* existence). Three lifecycle vocabularies now exist in this
codebase, each intentionally scoped to a different kind of subject —
not competing, and not to be conflated, mirroring the discipline 111A
§6 already applied when it deliberately restated 110A §8 verbatim
rather than inventing a fourth.

| Stage | Meaning |
|---|---|
| `Created` | The context object has been allocated and assigned an identity (e.g. an ID), but is not yet populated with real data. |
| `Initialized` | Required fields are populated; the object is ready to be read. |
| `Observed` | The object has been read via Introspection at least once — the point of contact between Context (this document) and the Introspection layer (111A/111B) that would eventually expose it. |
| `Updated` | One or more of the object's fields have changed since `Initialized` (e.g. a `TaskContext`'s status changing). |
| `Completed` | The unit of work the object represents has finished (e.g. a task finished, a phase completed). |
| `Archived` | The object is retained for historical reference but is no longer current or active. |

**Future execution states remain explicitly out of scope.** No
`Executing`/`Executed`/`RolledBack` stage is added to this six-stage
model — those remain the domain of 110A §8's own Runtime State Model
and, once implemented, the future `ExecutionContext`/`AuditContext`/
`RollbackContext` objects specifically (§3), not a generic property
every Context object gains.

## 5. Ownership (Frozen)

**The Runtime owns:**

- Context lifecycle (§4 — the Runtime is what would, in a future
  phase, transition a Context object between stages; no Context object
  transitions itself)
- Current context (which `RuntimeSession`/`TaskContext`/etc. is
  presently active)
- Context transitions (the act of moving from one lifecycle stage to
  the next)

**The Registry owns:** Metadata (110C §5, unchanged — Context never
duplicates or re-derives Registry state; a `TaskContext` referencing a
plugin would reference the Registry's own `PluginDescriptor`, never
copy it).

**Plugins own:** Capability implementation (110B §1, unchanged).

**The Broker owns:** Policy decisions (108A–108D, unchanged —
`BrokerDecisionContext`, §3 object 7, *wraps* a decision the broker
already produced; it does not produce, re-derive, or second-guess one).

**Context never owns:**

- Execution (the same guarantee §1 already states as an absolute)
- Approval decisions (`ApprovalContext` records that an approval
  outcome exists once one does; it is never itself the mechanism that
  decides one — that remains `COMP-003`'s job, not implemented anywhere)
- Policy evaluation (identical reasoning, for the Broker's job)

This ownership split is the third instance, in this arc, of the same
"surfaces facts, does not decide what to do with them" discipline —
110C §5 established it for the Registry, 111A §1 established it for
Introspection, and this section establishes it a third time for
Context. The repetition is deliberate: it is the single design
discipline that has kept every layer in this arc safely non-executing
across nine consecutive phases (110A–111D), reconfirmed with
increasingly rigorous tooling each time (111R §10).

## 6. Context Relationships

The canonical relationship chain, as a containment/ownership hierarchy
(not necessarily a strict temporal sequence — see the note on Approval/
Broker Decision ordering below):

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
Approval
  |
  v
Broker Decision
  |
  v
Evidence
  |
  v
(future) Execution
```

**Cardinality, per link, stated where evidence exists:**

- **Session : Task** — one Session has zero-or-more Tasks over its
  lifetime; at most one Task is *active* at any given moment (the real,
  already-enforced agent-lock invariant this codebase's `pcae task`
  already implements today).
- **Task : Phase** — **many Tasks to one Phase**, verified directly
  against this session's own operational pattern: every phase in the
  110–111 series (110A through 111R) was implemented via one-or-more
  governed tasks scoped to that phase's work (typically an
  implementation task, then a separate metadata-sync task) — never a
  single task spanning multiple phases. This is the *opposite*
  cardinality from a naive reading of the diagram above (which could
  suggest one Task containing many Phases); it is stated explicitly
  here because it is evidence-grounded, not assumed.
- **Phase : Intent** — one Phase's work is composed of one-or-more
  Intents; each Intent belongs to exactly one Phase.
- **Intent : Approval** — conceptually one:one (each intent that
  requires approval would have exactly one approval outcome) — though
  today this is purely conceptual, since `COMP-003` does not exist.
- **Approval : Broker Decision — ordering tension, named not resolved.**
  This document presents the chain in the order given (Approval, then
  Broker Decision), but notes directly: 110A §5's already-frozen Runtime
  Interfaces table names `Decision Pipeline → Approval` as one of eight
  interfaces — implying the Broker's decision is consulted *before*,
  not after, an Approval outcome, within the seven-stage pipeline's own
  sequencing. This document does not silently pick a side. **This is an
  open question for 112B (contract freeze) to resolve deliberately**,
  not a gap in this phase — naming a tension honestly is more useful
  than papering over it with an assumed answer.
- **Broker Decision : Evidence** — one-or-more Evidence records per
  Broker Decision, conceptually (a future Audit Boundary, `COMP-007`,
  could in principle record more than one evidence artifact per
  decision) — not implemented anywhere today.
- **Evidence → (future) Execution** — named as the eventual next link,
  explicitly out of 112A's own scope (112A models context, not
  execution) — the state model this future link would reference (110A
  §8) is already frozen and requires no redesign here.

## 7. Persistence Model (Architecture Only)

This section is this document's direct answer to 111R's §11
recommendation condition: an explicit, per-concept Persistence Model
decision for each of Intent, Approval, Broker decision, and Evidence —
not a single uniform default silently inherited from the Registry's own
in-memory-only choice (110E).

| Concept | Should eventually persist? | Rationale |
|---|---|---|
| **Session** | Yes — already does. | `.pcae/session.json` already exists, predating this arc. No change recommended; Context should reference, not replace, this existing mechanism. |
| **Task** | Yes — already does. | Task contract files (`tasks/active/`, `tasks/done/`) already exist. Same reasoning as Session. |
| **Phase** | Yes — already does. | `phase-completion-metadata.json` and phase reports already exist. Same reasoning. |
| **Intent** | **Session-only, not yet.** | No durable audit/evidence mechanism exists to review stored intent history (`COMP-007` not implemented). Persisting intents without a governance-reviewed record of what is stored would accumulate ungoverned historical data — the fail-closed choice is to keep Intent ephemeral until Evidence (below) exists to make its persistence accountable, not before. |
| **Approval** | **Should eventually persist, once implemented; nothing to persist today.** | An approval decision is exactly the kind of fact that needs a durable, accountable record (`COMP-003` + an audit trail) — but `COMP-003` does not exist, so there is no approval outcome anywhere to persist yet. This is a "not applicable yet" answer, not an "in-memory only" answer — the two are different and should not be conflated. |
| **Broker decision** | **Deliberately session-only/ephemeral — a continuation of an already-frozen choice, not a new one.** | 109B–109D already froze "the decision is produced and discarded" as a load-bearing safety property — their own safety cases rest specifically on isolation being structural (every `observe()` call is a bare, never-assigned expression, 109D). Persisting broker decisions durably would be a significant architectural change to that frozen guarantee, requiring its own dedicated future phase with an explicit safety re-analysis — **out of 112A's scope entirely**, not merely deferred. |
| **Evidence** | **Should eventually persist, once implemented; nothing to persist today.** | Persistence is the entire point of an evidence record (`COMP-007`, Audit Boundary) — but it does not exist, so there is nothing to persist yet. Same "not applicable yet" framing as Approval. |
| **Observation state** | **Session-only/ephemeral.** | Mirrors Broker Decision's reasoning directly — the four observation integrations (109B–109D) are explicitly "consult and discard," and their safety case rests on the same non-persistence property. |

**What must never persist.** Restated, unchanged, from 111A §8's
visibility rules and 110E/110F/111C's manifest-exclusion precedent:
secret material, credentials, tokens, and raw untyped `manifest`
content (110E) without the same redaction discipline already enforced
at the CLI output boundary (111C). Runtime Context inherits this rule
directly — no future Context persistence implementation may relax it.

## 8. Context Invariants (Frozen)

- **Exactly one active Runtime Context** — mirrors the already-enforced
  one-active-task-at-a-time agent-lock invariant, generalized to the
  full Context hierarchy.
- **Task belongs to one Session.**
- **Phase belongs to one Task** — presented as given by this phase's
  objectives; **note the direct tension with §6's evidence-grounded
  Task:Phase cardinality finding** (many Tasks serve one Phase in this
  session's own real operational practice, the reverse of what this
  invariant's literal wording states). This document does not resolve
  the tension unilaterally — that is explicitly 112B's (contract
  freeze) responsibility, named here so it is not lost between phases.
- **Intent belongs to one Phase.**
- **Execution unavailable** — restated, unconditional, unchanged from
  every prior phase in this arc.
- **Observation always available** — the four `INT-NNN` integrations
  (109C) remain unconditionally consultable regardless of Context
  state; no Context object may gate or disable observation.
- **No Context object may itself execute, approve, or evaluate policy**
  — §5's ownership split, restated as an invariant so it is directly
  citable and testable in a future implementation phase, not only
  implied by the responsibility table.

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

**112B — Runtime Context Contract Freeze.**
