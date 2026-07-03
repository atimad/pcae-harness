# PCAE Runtime Architecture

**Frozen by**: Phase 110A | **Status**: architecture/freeze only — no
runtime execution, command authorization, command denial, shell
mediation, subprocess mediation, backend invocation, adapter invocation,
execution enablement, execution capability, Permission Broker
enforcement, audit persistence, rollback execution, emergency stop,
Telegram inbound, REST server, web server, daemon, background workers,
automatic apply, command execution, plugin loading implementation, or
dependency injection framework is performed by this document or this
phase.

## Purpose

Elevate PCAE from a collection of independently-frozen governance
components (the Permission Broker of 108A–108D, the observation
integrations of 109B–109D, the Autonomy Contract of 107B, the No-Go
Gates of 107C) into a single, named, modular runtime architecture: the
canonical coordination layer that every future execution capability will
plug into. This document freezes intent and shape — the runtime, its
pipeline, its services, and its interfaces — exactly as `docs/V0_2_AUTONOMY_CONTRACT.md`
(107B) froze invariants and components, and as
`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (109A) froze
the command-path integration flow. It grants no execution capability and
connects nothing. Every status claim below is either "already true
today" (the components enumerated in 107B, the broker of 108A–108D, the
four observation integrations of 109B–109D) or "not implemented"
(the runtime itself, and everything the runtime would coordinate).

This document builds on, and changes none of:

- `docs/V0_2_AUTONOMY_CONTRACT.md` (107B) — ten invariants (INV-001..010),
  twelve named components (ten with `COMP-NNN` IDs), the canonical
  execution lifecycle (`PLANNED → READY → AWAITING_HUMAN_APPROVAL →
  AUTHORIZED → EXECUTING → {COMPLETED|FAILED|ABORTED}`).
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (107C) — 25 frozen
  no-go gates (NG-001..025).
- `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (109A) — the
  eight-stage command-path integration flow and eleven command
  categories.
- `src/pcae/core/permission_broker_foundation.py` (108A–108D) — the
  evaluate-only Permission Broker, unmodified.
- `src/pcae/core/command_path_observation.py` (109B–109D) — the four
  observation-only integrations (INT-001..004) and their registry.

The runtime described here is a **superset architectural frame** around
these existing, frozen pieces — it does not replace, rename, or
renumber any of them. `COMP-001` remains the Permission Broker.
`INT-001`..`INT-004` remain the four observation integrations. This
document adds a coordination layer *above* them, and a plugin surface
*around* them, neither of which exists in code today.

## 1. The PCAE Runtime

**Definition.** The PCAE Runtime is the central coordination layer that
receives intents, routes them through a fixed pipeline of governance and
(eventually) execution stages, and returns a result — while itself
containing no policy logic, no execution logic, and no plugin-specific
logic. It is an orchestrator, exactly as `PermissionBroker` (108B) is an
orchestrator over `PolicyRule`s rather than a policy author: the Runtime
delegates every substantive decision to a pipeline stage or a plugin,
and its own responsibility is limited to sequencing, contract
enforcement between stages, and state-transition bookkeeping.

**Responsibilities:**

1. **Sequencing.** Drive every intent through the seven pipeline stages
   (§2) in a fixed, non-skippable order — no stage may be bypassed, no
   stage may run out of order, exactly as INV-001/INV-002 (107B) already
   require for the execution lifecycle.
2. **Contract enforcement between stages.** Validate that each stage's
   output satisfies the next stage's input contract (§5) before handing
   it forward; reject (fail-closed) malformed handoffs rather than
   passing them through.
3. **State-transition bookkeeping.** Record which state (§8) an intent
   currently occupies and enforce that transitions only ever move
   forward through the state model, never skip, never reverse without an
   explicit rollback path.
4. **Plugin coordination, not plugin logic.** Invoke registered plugins
   (§3) at the appropriate pipeline stage; the Runtime does not itself
   decide policy, does not itself execute, and does not itself notify —
   it calls the plugin whose category owns that responsibility.
5. **Service ownership boundary.** Own or delegate to the nine runtime
   services (§4), and expose them consistently to every plugin so that,
   for example, a Notification Plugin and an Audit Plugin see the same
   Session/Task/Phase context for a given intent.
6. **Fail-closed by construction.** Exactly as `PermissionBroker.evaluate()`
   (108A) fails closed on a malformed request and `_compose()` (108C)
   fails closed on an empty policy registry, the Runtime fails closed on
   any stage that cannot produce a valid output — an intent that cannot
   be sequenced correctly never silently proceeds.

**What the Runtime explicitly is not:** it is not a scheduler, not a
daemon, not a server, not a background process, and not itself an
execution mechanism. It has no persistent process of its own in this
phase's design — it is a coordination *pattern* that a future
implementation phase would give a concrete entry point (e.g. invoked
per-command, exactly as `observe()` is invoked per-command today), not a
new long-running system. This mirrors 109A's treatment of "Command
Boundary" as a pattern rather than a standing component where
appropriate — here, by contrast, the Runtime *is* significant enough to
warrant a first-class architectural identity, precisely because it is
the thing every plugin and every pipeline stage will be defined in terms
of.

**Current implementation status: not implemented.** No file, class, or
function named "Runtime" exists in `src/pcae/` today. This document
defines what such an implementation would need to satisfy; it does not
create it.

## 2. The Runtime Pipeline

The canonical, frozen seven-stage pipeline every intent flows through,
once a Runtime exists to drive it:

```
Intent Source
  |
  v
Runtime
  |
  v
Intent Pipeline
  |
  v
Decision Pipeline
  |
  v
Execution Adapter
  |
  v
Evidence Pipeline
  |
  v
Notification Pipeline
```

| Stage | Role | Owns | Current status |
|---|---|---|---|
| **Intent Source** | Where a proposed action originates — a human, an AI agent, a governed CLI command, a future scheduled trigger. | Producing a well-formed intent; nothing else. | Partially present informally: every governed CLI command today (`pcae commit`, `pcae push`, etc.) is *ad hoc* an intent source, but no formal `Intent Source Plugin` contract exists yet. |
| **Runtime** | The coordination layer (§1). Receives the intent, opens a state-model entry (§8) at `Intent`, and begins sequencing. | Sequencing, contract enforcement, state bookkeeping. | Not implemented. |
| **Intent Pipeline** | Normalizes and validates the raw intent into a canonical, structured request — analogous to how `build_permission_broker_request()` (108A) already normalizes broker inputs, but generalized beyond the broker to any future pipeline consumer. | Structural validation, normalization, canonicalization. | Not implemented as a standalone stage; `build_permission_broker_request()` is a narrow, broker-specific precedent for the *shape* this stage would take. |
| **Decision Pipeline** | Consults the Permission Broker (`COMP-001`, unmodified) and any registered Policy/Decision plugins (§3) to produce a decision. This is the stage the four existing observation integrations (INT-001..004) already touch today — in observation mode, the decision is produced and discarded; a Decision Pipeline stage is what a future phase would need to formalize before a decision could ever be *read* by anything downstream. | Policy evaluation, decision composition (`_compose()`, 108C, unmodified), decision recording. | The Permission Broker itself is foundation-implemented (108A–108D). The Decision Pipeline *stage* — the thing that would sit around the broker and make its output available to later stages — is not implemented. |
| **Execution Adapter** | The single mediated boundary through which an authorized intent would actually run — corresponds to `COMP-004`/`COMP-005`/`COMP-006` (Shell/Backend/Adapter Boundary, 107B) collectively. | Mediated execution, never direct. | Not implemented. No code path in this codebase executes agent-authored commands or invokes a real backend. |
| **Evidence Pipeline** | Captures what happened — inputs, decision, outcome — into a durable, structured record. Corresponds to `COMP-007` (Audit Boundary, 107B). | Evidence capture, audit-record construction. | Not implemented. No audit persistence exists for any real action today. |
| **Notification Pipeline** | Surfaces the outcome to a human or system — the only stage with a real, working implementation precedent today (`pcae notify`, `COMP-009` Telegram outbound, exercised at the end of every phase in this session). | Outbound delivery, formatting, sink selection. | **Partially implemented** — outbound-only notification (Telegram, stdout, filesystem, mock sinks) already exists and is exercised every phase via `pcae phase complete`. Inbound remains explicitly out of scope (No-Go: "No Telegram inbound"). |

**Every stage is mandatory and ordered.** An intent may not skip from
Intent Source directly to Execution Adapter, exactly as INV-001/INV-002
(107B) already forbid skipping lifecycle states. The pipeline is the
lifecycle (§8) given a processing shape rather than a state-name shape —
the two are two views of the same frozen sequence, cross-referenced in
§8.

## 3. Plugin Architecture

Ten canonical plugin categories are frozen. **No plugin loading
mechanism, plugin discovery mechanism, or dependency injection framework
is implemented by this phase** — these are category *definitions* only,
each specifying purpose, responsibilities, lifecycle, inputs, outputs,
current status, and future implementation phase. Full detail for each
category lives in the companion document, `docs/PCAE_PLUGIN_MODEL.md`;
this section gives the canonical list and how each category maps onto
the pipeline (§2).

| # | Plugin Category | Pipeline Stage(s) it Serves | Current Status |
|---|---|---|---|
| 1 | Intent Source Plugin | Intent Source | Not implemented (informal precedent: governed CLI commands) |
| 2 | Policy Plugin | Decision Pipeline | Foundation-implemented as `PolicyRule` (108B), not yet a general plugin category |
| 3 | Decision Plugin | Decision Pipeline | Foundation-implemented as `PermissionBroker` (108A), not yet a general plugin category |
| 4 | Approval Plugin | between Decision Pipeline and Execution Adapter | Not implemented (`COMP-003` Human Approval Gate is not implemented) |
| 5 | Execution Adapter Plugin | Execution Adapter | Not implemented |
| 6 | Audit Plugin | Evidence Pipeline | Not implemented |
| 7 | Notification Plugin | Notification Pipeline | Partially implemented (`pcae notify`, outbound-only) |
| 8 | Storage Plugin | cross-cutting (backs Evidence Pipeline, Runtime Services) | Not implemented as a plugin; ad hoc filesystem/JSON storage exists throughout `.pcae/` today |
| 9 | Identity Plugin | cross-cutting (backs Approval, Audit) | Not implemented |
| 10 | Context Plugin | cross-cutting (backs Intent Pipeline, Runtime Services) | Not implemented as a plugin; ad hoc context assembly exists in `pcae session bootstrap` today |

See `docs/PCAE_PLUGIN_MODEL.md` for the full definition of each category.

## 4. Runtime Services

Nine canonical services are frozen. Each is a piece of state or
capability the Runtime exposes consistently to every pipeline stage and
every plugin, so that (for example) an Audit Plugin and a Notification
Plugin observe the same Task/Phase context for a single intent.

| Service | Owns | Relationship |
|---|---|---|
| **Session** | The current working session's identity, continuity state, and agent-lock status. | Already implemented today (`pcae session bootstrap`, `pcae.core.session`) as a standalone command surface; this phase names it as a Runtime Service the future Runtime would expose rather than a caller re-deriving it per pipeline stage. |
| **Task** | The active task contract: scope, allowed files/zones, lifecycle state. | Already implemented today (`pcae task`, `pcae.core.tasks`); named here as a Runtime Service for the same reason. |
| **Phase** | The current governed phase's identity and completion metadata. | Already implemented today (`pcae phase`, `.pcae/phase-completion-metadata.json`); named here as a Runtime Service. |
| **Identity** | Who (human or agent) originated a given intent. | Not implemented as a distinct service; today's commands assume a single implicit local operator. |
| **Configuration** | Runtime-wide and plugin-specific configuration (e.g. which sinks are enabled, per `pcae notify status`). | Partially implemented today via environment variables (`PCAE_NOTIFY_ENABLED`, `PCAE_NOTIFY_SINKS`) and `.config/pcae/`; not yet unified under a single Configuration service. |
| **Plugin Registry** | Which plugins are registered, per category, and their current status. | Not implemented. `docs/PCAE_PLUGIN_MODEL.md`'s ten-category table is the frozen *shape* such a registry would eventually hold — not the registry itself. |
| **Policy Registry** | The registered `PolicyRule`s a Decision Pipeline would consult. | Already implemented today as `pcae.core.permission_broker_foundation.PolicyRegistry` (108B) — narrower in scope than a future Runtime-level Policy Registry, since it only serves the Permission Broker today, not a general Policy Plugin category. |
| **Integration Registry** | Which command paths currently observe (or, in the future, integrate with) the Runtime. | Already implemented today as `pcae.core.command_path_observation.INTEGRATION_REGISTRY` (109C) — the four INT-NNN entries. This is the direct precedent the future Plugin Registry and any per-category registry would generalize. |
| **Audit Registry** | Which evidence records exist, for which intents. | Not implemented. No audit persistence exists for any real action today (consistent with the No-Go list above). |

**Ownership note:** three of the nine services (Session, Task, Phase)
already have working, standalone implementations that predate this
architecture and are not being redesigned by this phase — they are
being *named* as services a future Runtime would expose consistently,
rather than each pipeline stage or plugin re-deriving session/task/phase
context independently. Two more (Policy Registry, Integration Registry)
have narrower, already-implemented precedents (108B, 109C respectively)
that a future Runtime-level registry would need to generalize without
breaking. The remaining four (Identity, Configuration unification,
Plugin Registry, Audit Registry) are not implemented in any form today.

## 5. Runtime Interfaces

Contracts, not implementations, between each adjacent pair in the
pipeline (§2). Each interface below is described in terms of what must
be true of the handoff, not how it would be coded.

| Interface | From → To | Contract |
|---|---|---|
| Intent Sources → Runtime | Intent Source → Runtime | The source must produce a well-formed intent carrying at minimum: an identity (who/what proposed it), an action description, and a timestamp. The Runtime must reject (fail-closed) any intent missing these fields rather than guessing defaults — mirroring `PermissionBroker.evaluate()`'s existing rejection of a non-`PermissionBrokerRequest` object (108A). |
| Runtime → Broker | Runtime → Decision Pipeline (Permission Broker) | The Runtime must construct a valid `PermissionBrokerRequest` (already frozen, 108A) before calling `PermissionBroker.evaluate()`. The Broker's contract — evaluate-only, no side effects, fail-closed composition — is already frozen (108A–108D) and unchanged by this document. |
| Broker → Decision Pipeline | Permission Broker → Decision Pipeline (wrapping stage) | The Broker returns a `PermissionBrokerDecision` (already frozen). The Decision Pipeline stage's contract is to make this decision *available* to later stages for the first time — today, every consumer (INT-001..004) discards it immediately; a future phase formalizing this interface must decide, deliberately, what "available" means (logged? persisted? passed to Approval?) rather than defaulting to persistence. |
| Decision Pipeline → Approval | Decision Pipeline → Approval Plugin | A decision of `HUMAN_REVIEW` or (per INV-003, 107B) any executable `ALLOW` must reach an explicit human approval step before proceeding; the contract is that Approval never infers consent from silence, timeout, or absence of objection — this is already a frozen invariant (INV-003) that any future Approval Plugin must satisfy, not a new rule. |
| Approval → Execution Adapter | Approval Plugin → Execution Adapter Plugin | Only an intent that has reached `AUTHORIZED` (107B's lifecycle) may be handed to an Execution Adapter. The contract is a one-way gate: Execution Adapter must refuse any intent not carrying proof of prior authorization. |
| Execution Adapter → Audit | Execution Adapter Plugin → Audit Plugin | Every execution attempt — success or failure — must produce exactly one evidence record; the contract forbids "silent" execution outcomes, mirroring the No-Go list's "No audit persistence" being a currently-true gap this interface would need to close before execution could ever be enabled. |
| Audit → Notification | Audit Plugin → Notification Plugin | Evidence records may trigger a notification, but notification is never a substitute for the evidence record itself — the contract requires Audit to persist first, independent of whether any Notification Plugin is configured or reachable. |
| Notification → Storage | Notification Plugin → Storage Plugin | Notification delivery status (sent/failed/skipped) is itself a fact worth storing, using the same Storage Plugin category the Audit Plugin uses — not a bespoke notification-specific persistence mechanism. |

## 6. Runtime Principles

Eleven architectural principles are frozen. Every future runtime
implementation phase must be evaluated against all eleven; violating any
one is a design defect, not a style preference.

1. **Modular** — every pipeline stage and plugin category is
   independently definable and independently replaceable; no stage's
   internal logic depends on another stage's internals.
2. **Pluggable** — the ten plugin categories (§3) are the only extension
   points; new capability is added by implementing a plugin contract,
   never by modifying the Runtime's sequencing logic.
3. **Connected** — every plugin category is reachable from, and
   accountable to, the Runtime's single pipeline; there is no
   out-of-band path for a plugin to act without passing through it (this
   is the architectural reason the four observation integrations
   deliberately touch only read-only commands today, per 109B's design).
4. **Observable** — every stage transition and every plugin invocation
   must be inspectable (today: via tests and structural inspection; in
   the future: via the Evidence Pipeline) — nothing in the pipeline may
   be a black box even before execution is enabled.
5. **Automatable** — the pipeline's shape must not assume a human is
   present at every stage forever; Human Approval Gate (`COMP-003`) is a
   named, addressable stage precisely so that future automation can be
   reasoned about explicitly rather than assumed away.
6. **Governed** — every stage is subject to the frozen invariants
   (INV-001..010, 107B) and no-go gates (NG-001..025, 107C); the Runtime
   does not get a governance exemption for being "just coordination."
7. **Fail-closed** — identical to the Permission Broker's own design
   principle (108B/108C): anything unknown, unavailable, malformed, or
   unsupported at any stage resolves to the least-permissive outcome,
   never a silent pass-through.
8. **Least privilege** — a plugin only receives the inputs its category
   contract specifies (§3, §5); a Notification Plugin, for example, is
   never handed raw execution credentials because no notification
   contract calls for them.
9. **Human-controlled** — INV-003 (107B) is architecturally load-bearing
   here: no pipeline configuration may cause an intent to reach
   `AUTHORIZED` without an explicit, recorded human approval action.
10. **Deterministic** — for a given intent and a given set of plugin
    responses, the Runtime's sequencing and state transitions must be
    reproducible; only plugins may introduce non-determinism (e.g. a
    real AI backend's output), never the Runtime's own coordination
    logic.
11. **Testable** — every stage and every plugin contract must be
    exercisable in isolation, without a live human, a live backend, or
    network access — exactly as every broker and observation-integration
    test in this codebase runs fully offline today.

## 7. Runtime Capability Matrix

| Capability | Current capability | Future capability | Implementation phase | Current implementation status | Expected maturity |
|---|---|---|---|---|---|
| Intent normalization | None | Intent Pipeline validates and canonicalizes every intent | 110B+ | not_implemented | Low |
| Policy evaluation | `PermissionBroker.evaluate()` (evaluate-only, discarded by callers) | Decision Pipeline makes broker decisions available downstream | 110B+ (contract), later phase (enforcement) | foundation_implemented (broker only) | Medium |
| Observation | Four read-only command paths consult the broker and discard the result (INT-001..004) | All eleven command categories (109A) observed, still discard-only until enforcement is separately authorized | 109-series (complete for read-only); expansion not yet scheduled | implemented (observation-only, 4 paths) | Medium |
| Human approval | None | Approval Plugin enforces INV-003 before any `AUTHORIZED` transition | 111A (per `docs/V0_2_AUTONOMY_CONTRACT.md`'s own component status notes) | not_implemented | Low |
| Execution | None | Execution Adapter mediates all real action through Shell/Backend/Adapter Boundary (`COMP-004`/`005`/`006`) | not scheduled | not_implemented | None |
| Audit persistence | None | Evidence Pipeline produces one record per execution attempt | not scheduled | not_implemented | None |
| Notification (outbound) | Working today: Telegram, stdout, filesystem, mock sinks; exercised every phase via `pcae phase complete` | Notification Plugin generalizes today's sinks under the plugin contract | not scheduled | partially_implemented | High (for outbound only) |
| Notification (inbound) | None; explicitly out of scope | Not designed by this phase | not scheduled | not_implemented (explicit no-go) | None |
| Plugin registry | None | Tracks registered plugins per category, with status | 110B+ | not_implemented | Low |
| Rollback | None | Rollback Boundary (`COMP-008`) reverses a completed or failed execution | not scheduled | not_implemented | None |
| Emergency stop | None | Halts an in-flight execution, producing an `ABORTED` audit record | not scheduled | not_implemented | None |

## 8. Runtime State Model

The canonical, frozen lifecycle every intent passes through, as a
sequence of named states — the same sequence the pipeline (§2) expresses
as processing stages:

```
Intent
  |
  v
Observed
  |
  v
Advisory
  |
  v
Approved
  |
  v
Executable
  |
  v
Executed
  |
  v
Audited
  |
  v
Rollback Ready
```

| State | Meaning | Corresponds to (107B lifecycle) | Current status |
|---|---|---|---|
| `Intent` | A proposed action has been produced by an Intent Source; nothing has evaluated it yet. | `PLANNED` | Informally reachable today (any governed CLI invocation) |
| `Observed` | The Permission Broker has been consulted and produced a decision, but that decision has been (or would be) discarded by the caller. | between `PLANNED` and `READY` (not a named 107B state; this is the observation-only ceiling 109B introduced) | **Reachable today** — INT-001..004 reach exactly this state, every invocation, and go no further |
| `Advisory` | The decision is retained and surfaced to a human or system as advice, without any enforcement effect. | between `READY` and `AWAITING_HUMAN_APPROVAL` | Not implemented (this is the state 110A+ work is expected to design toward — see Recommended Next Phase) |
| `Approved` | An explicit human approval has been recorded for this specific intent. | `AWAITING_HUMAN_APPROVAL` → (approval recorded) | Not implemented |
| `Executable` | The approved intent has passed rollback-readiness and audit-artifact-creation checks and may now proceed. | `AUTHORIZED` | Not implemented |
| `Executed` | The action has run through the Execution Adapter. | `EXECUTING` → `COMPLETED`/`FAILED` | Not implemented |
| `Audited` | An evidence record exists for the outcome. | (implicit in `COMPLETED`/`FAILED`, formalized here as its own state) | Not implemented |
| `Rollback Ready` | A verified rollback path exists for the executed action, whether or not it is ever invoked. | (implicit in `COMPLETED`, formalized here as its own state) | Not implemented |

**Current maximum state reachable by any real PCAE command path today:
`Observed`.**

**Execution unavailable.** No intent, through any command path, plugin,
or pipeline stage described in this document, can reach `Approved`,
`Executable`, `Executed`, `Audited`, or `Rollback Ready` — those five
states, and the capabilities they describe, remain entirely
undesigned-for-implementation as of this phase, exactly as the No-Go
list at the top of this document requires.

## No-Go Confirmations

No runtime execution. No command authorization. No command denial. No
shell mediation. No subprocess mediation. No backend invocation. No
adapter invocation. No execution enablement. No execution capability. No
Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST server. No
web server. No daemon. No background workers. No automatic apply. No
command execution. No plugin loading implementation. No dependency
injection framework. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision (unchanged
since 108A). `v0.1.0-rc1` remains non-executing by design. v0.2 remains
the autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new tag.
No new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110B — Runtime Plugin Contract Freeze.**
