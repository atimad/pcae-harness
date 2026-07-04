# PCAE Advisory Runtime Architecture

**Frozen by**: Phase 113A | **Status**: architecture/design only — no
advisory execution, runtime execution, command authorization, command
denial, Permission Broker enforcement, plugin loading, plugin
instantiation, plugin invocation, dependency injection, shell
mediation, backend invocation, adapter invocation, execution
enablement, execution capability, automatic apply, audit persistence,
rollback execution, Telegram inbound, REST server, web UI, daemon, or
background workers is performed by this document or this phase.

## Purpose

112A–112F built the Runtime's complete read-only picture: what the
Runtime can do (110A), what plugins and capabilities exist
(110B–111D), what is currently happening (112A–112D, Runtime Context),
and the single canonical model composing all of it (112E–112F, Runtime
Snapshot). Every one of those phases answered a question about *what
is true*. This phase, and the new subsystem it designs, asks a
different question for the first time in this arc: **given what is
true, what should a human consider doing about it** — without ever
doing it, deciding it, or authorizing it. That subsystem is the
**Advisory Runtime**: analytical only, consuming Runtime Snapshot,
producing Advisory Results, and stopping there.

This document builds on, and changes none of: `docs/PCAE_RUNTIME_ARCHITECTURE.md`
(110A), `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B, including its
ten frozen plugin categories, unchanged and un-extended by this
phase), `docs/PCAE_RUNTIME_CONTEXT_CONTRACT.md` (112B), and
`docs/PCAE_RUNTIME_SNAPSHOT_CONTRACT.md` (112F, whose §6 already named
"Advisory Runtime" as a future consumer reading Runtime Snapshot as
read-only input — this document is that future phase).

**Not to be confused with IRG Challenge.** This codebase already has
an unrelated, pre-existing "advisory" concept —
`build_irg_challenge_context()`'s Independent Review Governance
Challenge (`_IRG_STRATEGIC_REVIEW_REGISTRY`), surfaced today as the
"IRG (advisory): ..." line in `pcae session bootstrap`. IRG Challenge
reviews *strategic/roadmap decisions* (has this project drifted from
its own stated direction) and is scoped to phase/roadmap governance.
Advisory Runtime reviews *Runtime Snapshot* (is the Runtime's current
operational state healthy, consistent, ready) and is scoped to runtime
operations. The two are architecturally unrelated subsystems that
happen to share the word "advisory" — this document does not extend,
modify, or depend on IRG Challenge in any way, and neither should be
read as a precedent constraining the other's design.

## New Principle

```
Recommendation precedes authorization.
```

Restated from this phase's own architectural principles list, frozen
here as a citable, testable addition alongside "Context precedes
execution" (112A) and "Identity precedes state" (112B): a future
authorization mechanism (whenever it exists) must be able to point to
the recommendation that preceded it — Advisory Runtime is the
subsystem that produces that recommendation, before any authorization
mechanism exists to consume it. This is a strict ordering constraint,
not a design suggestion: no future phase may wire a command straight
from "Runtime Snapshot" to "authorized" without an Advisory Result
sitting in between, exactly as "Context precedes execution" forbids
skipping straight from intent to execution without Context recording
what the action was for.

## 1. Advisory Runtime Subsystem Definition

**Purpose.** The Advisory Runtime reads one Runtime Snapshot and
produces zero-or-more Advisory Results — structured, read-only
recommendations about the Runtime's current operational state. It
never executes, never authorizes, never mutates Runtime Context, and
never mutates Runtime Snapshot (§8).

**Responsibilities:**

- Read exactly one Runtime Snapshot per analysis pass (§2, Stage 1).
- Apply zero-or-more Analysis routines to that snapshot (§2, Stage 2).
- Compose zero-or-more Recommendations from analysis findings (§2,
  Stage 3).
- Emit each Recommendation as a frozen Advisory Result record (§2,
  Stage 4; §3).
- Make every emitted Advisory Result available to Presentation,
  unchanged (§2, Stage 5; §7).

**Architectural boundaries — what Advisory Runtime is not:**

- It is not a Decision Pipeline stage (110A §2) — it does not evaluate
  policy, does not produce a `PermissionBrokerDecision`, and is never
  consulted by `PermissionBroker.evaluate()`.
- It is not an Execution Adapter (110B §2.5) — it has no path to a
  shell, a backend, or any adapter.
- It is not IRG Challenge (Purpose, above) — a different subsystem,
  reviewing a different kind of state, for a different purpose.
- It is not a Context mutator — `RuntimeContext`/`RuntimeSnapshot`
  remain, respectively, 112C's and 112E's exclusive write surfaces (in
  practice: neither has one yet; Advisory Runtime does not become
  one either).

**Where it sits.** Between Runtime Snapshot (112E/112F, already
frozen, already the canonical read model) and Presentation (§7, not
yet built for advisory output specifically). Advisory Runtime is a new
consumer of Runtime Snapshot — the second consumer this arc has now
named after the CLI (111C/112E) — not a modification to Runtime
Snapshot itself.

## 2. Advisory Pipeline (Frozen)

Five stages, strictly one-directional, no execution path at any stage:

```
Runtime Snapshot
  |
  v
Analysis
  |
  v
Recommendation
  |
  v
Advisory Result
  |
  v
Presentation
```

| Stage | Input | Output | Responsibility | Forbidden |
|---|---|---|---|---|
| **Runtime Snapshot** | (none — the frozen 112E/112F model) | A `RuntimeSnapshot` instance | Supplies the one, canonical, already-frozen read model every later stage analyzes. | Advisory Runtime may not construct its own competing snapshot, and may not read any source Runtime Snapshot itself doesn't already compose (112F §2). |
| **Analysis** | One `RuntimeSnapshot` | Zero-or-more analysis findings (architecture only — no concrete finding type is frozen by this phase) | Inspects Runtime Snapshot's domains (`runtime`/`registry`/`plugins`/`capabilities`/`health`/`governance`/`state`/`version`/`context`) for conditions worth recommending on. | Never mutates the snapshot it reads (112F §3's "no mutable internal references" extends here: Analysis must treat its input as read-only); never calls any Runtime Snapshot field's *absence* as a license to invent data — an unpopulated `context.active_phase` (always `null` today, 112E) means "nothing to analyze here," never a fabricated finding. |
| **Recommendation** | Analysis findings | A candidate recommendation (architecture only) | Composes one-or-more findings into one proposed course of action for a human to consider. | Never composes a recommendation that *is* an action — "consider running `pcae check`" is a recommendation; running `pcae check` is not this stage's job under any circumstance. |
| **Advisory Result** | A candidate recommendation | One frozen `AdvisoryResult` record (§3) | Freezes the recommendation into the canonical, immutable, transport-agnostic record every Presentation consumer reads. | Never varies shape per consumer — the same `AdvisoryResult` record must be identical whether CLI, Telegram, REST, dashboard, or an AI agent eventually reads it (§7). |
| **Presentation** | One-or-more `AdvisoryResult` records | Human-readable text, JSON, or any future consumer-specific rendering | Renders `AdvisoryResult` records for a specific consumer, exactly as `_format_human()`/`snapshot_to_dict()` (112E) render `RuntimeSnapshot` today. | Never a source of new findings — Presentation only formats what Advisory Result already froze; it may not re-analyze Runtime Snapshot itself (that would bypass Analysis/Recommendation, violating the pipeline's own one-directional shape). |

**No execution path.** No stage above may invoke a plugin, evaluate a
policy, call a shell, call an adapter, or call
`PermissionBroker.evaluate()` — restated as an absolute in §8, not
merely implied by the table.

## 3. Advisory Result (Frozen Model, Architecture Only)

A canonical `AdvisoryResult` concept is frozen — a field sketch, not a
class, dataclass, or concrete Python construct, mirroring exactly how
112A §3 froze twelve Context objects and 111A §4 froze eleven
Introspection objects before any implementation phase gave them a
concrete type:

| Field | Meaning | Precedent this field's shape follows |
|---|---|---|
| `advisory_id` | A stable, never-reused identifier for this specific Advisory Result. | Mirrors `COMP-NNN`/`INT-NNN`/`ISP-NNN`-style frozen ID discipline (107B/109C/110B) — never renumbered once assigned. |
| `category` | Which of §4's advisory categories this result belongs to. | An open, extensible taxonomy (§4), deliberately unlike 110B's ten *closed* plugin categories — named and justified in §4. |
| `severity` | How significant this finding is: `info`, `advisory`, `warning`, or `critical` — a new, frozen four-level vocabulary, deliberately distinct from `dry_run.py`'s `simulation_severity` (`info`/`caution`/`blocked`), since Advisory Runtime never blocks anything (§8) and reusing "blocked" wording here would misrepresent that. | New vocabulary, frozen by this phase specifically because reusing an enforcement-flavored vocabulary would be inaccurate. |
| `confidence` | How well-grounded this finding is: `unknown`, `observed`, `validated`, or `proven`. | Reuses this codebase's own existing, already-frozen confidence vocabulary verbatim (`_CAP_CONF_UNKNOWN`/`_CAP_CONF_OBSERVED`/`_CAP_CONF_VALIDATED`/`_CAP_CONF_PROVEN`, capability-discovery confidence levels, `src/pcae/core/agent.py`) rather than inventing a competing one. |
| `rationale` | Free-text explanation of why this recommendation was produced. | — |
| `evidence_references` | A tuple of pointers into the specific Runtime Snapshot fields that produced this finding (e.g. `"health.plugin_count"`, `"context.session_id"`) — dot-path strings into the frozen 112F schema, not a copy of the underlying value. | Mirrors 112B §2's identity-reference discipline (a `BrokerDecisionContext` references a decision, never copies it) — evidence is traceable back to its source, never duplicated. |
| `recommended_action` | Free-text description of what a human might consider doing. Never an executable command, never a shell string, never a callable. | Directly enforces "Recommendation precedes authorization" — this field is where the ordering constraint is most concretely visible: text a human reads and decides on, not a trigger. |
| `affected_runtime_objects` | A tuple of identifiers (`task_id`, `plugin_id`, `session_id`, etc.) naming which already-identified Runtime/Context/Registry objects this result concerns. | Reuses 112B §2's own frozen identity formats verbatim — never a new identifier scheme. |
| `timestamp` | ISO 8601 timestamp of when this Advisory Result was produced. | Matches `.pcae/session.json`'s own real `timestamp` field convention (112E's `build_runtime_context_from_repo()` precedent). |

**No implementation.** No field above is a frozen schema in the sense
112B froze one for Runtime Context — a future contract-freeze phase
(113B, this phase's own recommended next phase) chooses the concrete
representation, exactly as 112A's twelve objects were frozen as field
lists first and given a concrete shape only in 112B/112C.

## 4. Advisory Categories (Frozen List, Open Taxonomy)

Eight categories frozen, matching this phase's own brief exactly:

| Category | Concerned with |
|---|---|
| Runtime Health | `health` domain conditions (110A/111B `HealthInfo`) |
| Governance | `governance` domain conditions (`GovernanceInfo`, broker/observation status) |
| Context Consistency | `context` domain conditions (112C/112E `RuntimeContext` — e.g. a session with no active task for an unusually long time) |
| Registry | `registry` domain conditions (110E/110F `RegistrySnapshot`) |
| Plugin Compatibility | `plugins`/`capabilities` domain conditions (110B/111B `PluginInfo`/`CapabilityInfo`) |
| Configuration | Policy/config-shaped conditions (110A §4's Configuration Runtime Service) |
| Operational Readiness | Cross-domain conditions spanning more than one Runtime Snapshot domain at once |
| *(Future extensibility)* | Reserved — not a real category, a placeholder acknowledging more will be added |

**Deliberately an open taxonomy — unlike 110B's closed ten-category
plugin taxonomy.** 110B §2 froze plugin categories as closed and
exhaustive ("cross-category plugins are not permitted"), because a
plugin category is a security-relevant contract boundary (110B §6).
An advisory category is not a security boundary — it is a
classification label on an analytical finding, and closing it would
force every future kind of insight into an ill-fitting existing label.
This document therefore freezes the eight categories above as the
*initial* set, explicitly extensible by a future phase without
requiring a contract-breaking change (mirroring 112F §3's own
"additive-only changes" rule for Runtime Snapshot's schema, applied
here to the category enum instead of a JSON key set).

## 5. Runtime Integration (Objective 5)

**Advisory Runtime consumes Runtime Snapshot, and nothing else.** It
must not depend directly on the CLI, Telegram, REST, or any other
transport — those are Presentation-layer concerns (§7), strictly
downstream of Advisory Result, never an input to Analysis or
Recommendation. Concretely, this means a future implementation's
Analysis stage takes a `RuntimeSnapshot` object (112E's own
`build_runtime_snapshot()` return type) as its only input — never a
CLI `argparse.Namespace`, never a Telegram update object, never an
HTTP request.

**Why this matters architecturally.** It is the same discipline
`runtime_snapshot.py` (112E) already applies to `runtime_introspection.py`
(111B) and `runtime_context.py` (112C): a layer composes the layer
beneath it and exposes a clean interface upward, never reaching
sideways into a sibling transport layer. Advisory Runtime sits exactly
one layer above Runtime Snapshot and exactly one layer below
Presentation — the same "layering, never reaching sideways" pattern
already established twice (112E's own `build_runtime_context_from_repo()`
bridges Context into Snapshot without either depending on the CLI;
Advisory Runtime bridges Snapshot into Advisory Result without
depending on any Presentation consumer).

## 6. Plugin Integration (Objective 6 — Named Gap, Not Resolved)

**Honest finding: no existing plugin category fits.** 110B §2 froze
exactly ten plugin categories (Intent Source, Policy, Decision,
Approval, Execution Adapter, Audit, Notification, Storage, Identity,
Context). None of them describes "read Runtime Snapshot, produce an
analytical recommendation" — Policy Plugin (110B §2.2) is the closest
in spirit, but its allowed responsibility is narrowly "evaluate one
normalized intent against one policy concern" as direct input to the
Decision Pipeline, a pre-execution authorization concern, not a
post-hoc analytical one; reusing it would misrepresent both.

**Resolution: named, not decided.** This document does not add an
eleventh plugin category. Extending 110B's closed taxonomy is out of
this phase's own scope (an architecture phase for Advisory Runtime,
not a revision to Plugin Contracts). If a future phase decides
Advisory Recommendations should be extensible via registered plugins
— rather than built entirely into Advisory Runtime's own Analysis
stage — the natural extension point would be a new, eleventh plugin
category, distinct from all ten already frozen, contributing findings
into the Analysis stage (§2) without ever itself producing an
`AdvisoryResult` directly (Advisory Result composition remains
Advisory Runtime's own job, per §2's Recommendation → Advisory Result
stages). This is named here explicitly, mirroring 111R/112A/112B's own
discipline of naming a tension rather than silently resolving it
outside the proper phase's scope — a future phase, not this one,
decides whether and how to build it.

**No plugin loading.** Nothing in this document, and nothing a future
Advisory Runtime implementation may do under this architecture,
loads, instantiates, or invokes any plugin — today or as a result of
this phase.

## 7. Presentation Layer (Objective 7)

Advisory Result records are rendered, unchanged, by whichever consumer
needs them — the same "one model, many renderers" discipline 112F §1/§6
already froze for Runtime Snapshot, extended here to Advisory Result:

- **CLI** — a future `pcae runtime advisory` (or similar) command would
  render `AdvisoryResult` records the same way `pcae runtime inspect`
  renders `RuntimeSnapshot` today (111C/112E's own `_format_human()`/
  JSON-output precedent).
- **Telegram** — a future outbound-only notification could send a
  formatted Advisory Result via the existing `pcae notify` sinks —
  Telegram inbound remains, unconditionally, out of scope for this
  entire arc.
- **REST** — a future read-only endpoint would serve Advisory Result
  records as JSON, unchanged, subject to the same security rules §8
  and 112F §7 already froze.
- **Dashboard** — a future web UI would render the same records; no
  new schema, no new backend logic.
- **AI agents** — a future bootstrap/context-pack integration could
  fold current Advisory Results into `pcae session bootstrap --compact`'s
  own prompt, alongside Runtime Snapshot (112F §6) and IRG Challenge's
  own, separate advisory line — three independent advisory-shaped
  inputs an agent could read side by side, never merged into one.

No implementation is added for any of the five consumers above.

## 8. Safety Rules (Frozen, Absolute)

The Advisory Runtime, unconditionally, in this architecture and in
every future implementation built against it:

- **Never executes.** No stage (§2) may run a command, invoke a
  plugin, or call a shell.
- **Never authorizes.** No `AdvisoryResult` may be read by any future
  mechanism as an authorization — "Recommendation precedes
  authorization" names the ordering; it does not grant the
  recommendation itself any authority.
- **Never mutates Runtime Context.** Analysis (§2) reads a
  `RuntimeSnapshot`'s `context` field; it never calls `observe_context()`
  (112C) or constructs a new `RuntimeContext` that could be mistaken
  for a live update.
- **Never mutates Runtime Snapshot.** Analysis treats its input
  `RuntimeSnapshot` as fully read-only, exactly as 112F §3's "no
  mutable internal references" rule already requires of every
  consumer.
- **Never invokes Permission Broker.** No stage imports
  `permission_broker_foundation` or calls
  `PermissionBroker.evaluate()` — the same isolation guarantee
  `runtime_context.py` (112C) and `runtime_snapshot.py` (112E) already
  hold, extended here a third time.
- **Never invokes shell.** No stage imports `subprocess`, `os.system`,
  or any shell-adjacent module.
- **Never invokes adapters.** No stage has any reference to an
  Execution Adapter Plugin (110B §2.5) or any other plugin instance.

## No-Go Confirmations

No advisory execution. No runtime execution. No command authorization.
No command denial. No Permission Broker enforcement. No plugin
loading. No plugin instantiation. No plugin invocation. No dependency
injection. No shell mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No
automatic apply. No audit persistence. No rollback execution. No
Telegram inbound. No REST server. No web UI. No daemon. No background
workers. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed` (110A §8, unchanged). Current
maximum plugin capability remains `observe` (110B §3, unchanged).
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the
autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new
tag. No new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**113B — Advisory Runtime Contract Freeze.**
