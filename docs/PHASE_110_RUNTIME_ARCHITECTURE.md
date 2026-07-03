# Phase 110A — PCAE Runtime Architecture & Plugin Model

## Purpose

Elevate PCAE from a collection of independently-frozen governance
components into a single, modular runtime architecture: the canonical
runtime, plugin model, component lifecycle, interfaces, and data flow
that all future execution capabilities will use. This is an
architecture/freeze phase only — no execution capability is introduced,
and no source code under `src/pcae/` is touched.

## Scope

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` — the runtime itself, the
  seven-stage pipeline, nine runtime services, eight interface
  contracts, eleven principles, a capability matrix, and the
  eight-state lifecycle model.
- `docs/PCAE_PLUGIN_MODEL.md` — the ten canonical plugin categories,
  each fully specified (purpose, responsibilities, lifecycle, inputs,
  outputs, current status, future implementation phase).
- `tests/test_runtime_architecture.py` — 100% documentation-verification
  tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. No plugin loading mechanism, dependency injection framework, or
any other implementation is added.

## 1. Runtime Architecture Summary

The PCAE Runtime is defined as the central coordination layer: it
sequences intents through a fixed, non-skippable pipeline, enforces
contracts between pipeline stages, tracks state-model transitions, and
delegates every substantive decision to a plugin or pipeline stage —
never containing policy or execution logic itself. It explicitly is not
a daemon, server, or background process; it is a coordination pattern a
future phase would give a concrete (per-command) entry point, mirroring
how `observe()` (109B) is invoked per-command today rather than as a
long-running process.

**Runtime Pipeline (seven stages, frozen):**

```
Intent Source -> Runtime -> Intent Pipeline -> Decision Pipeline
  -> Execution Adapter -> Evidence Pipeline -> Notification Pipeline
```

Every stage maps onto an existing frozen component where one exists
(Decision Pipeline wraps the unmodified `COMP-001` Permission Broker;
Execution Adapter corresponds to `COMP-004`/`005`/`006`; Evidence
Pipeline corresponds to `COMP-007`) and is marked `not_implemented`
where none exists yet. Notification Pipeline is the only stage with a
real, working, exercised implementation today (`pcae notify`, Telegram
outbound).

**Runtime Services (nine, frozen):** Session, Task, Phase, Identity,
Configuration, Plugin Registry, Policy Registry, Integration Registry,
Audit Registry. Three (Session, Task, Phase) already have working
standalone implementations being named as services rather than
redesigned. Two (Policy Registry, Integration Registry) have narrower,
already-implemented precedents (108B, 109C) a future Runtime-level
registry would generalize. Four (Identity, unified Configuration,
Plugin Registry, Audit Registry) do not exist in any form today.

**Runtime Interfaces (eight contracts, frozen):** every adjacent pair in
the pipeline — Intent Sources→Runtime, Runtime→Broker, Broker→Decision
Pipeline, Decision Pipeline→Approval, Approval→Execution Adapter,
Execution Adapter→Audit, Audit→Notification, Notification→Storage — is
specified as a contract (what must be true of the handoff), not as
code.

## 2. Plugin Model Summary

Ten canonical plugin categories are frozen, each fully specified in
`docs/PCAE_PLUGIN_MODEL.md`: Intent Source Plugin, Policy Plugin,
Decision Plugin, Approval Plugin, Execution Adapter Plugin, Audit
Plugin, Notification Plugin, Storage Plugin, Identity Plugin, Context
Plugin. Three categories (Policy, Decision, Notification) have real but
non-pluggable precedents already implemented (`PolicyRule`,
`PermissionBroker`, `pcae notify`'s sink set respectively). The
remaining seven have no implementation, though two (Storage, Context)
have informal precedents (`.pcae/` filesystem storage, `pcae session
bootstrap`). **No plugin loading mechanism, discovery mechanism, or
dependency injection framework is implemented by this phase** — every
category definition stops at "purpose, responsibilities, lifecycle,
inputs, outputs, current status, future implementation phase," exactly
as required.

## 3. Runtime Pipeline Summary

See §1 above for the frozen seven-stage sequence. Every stage is
mandatory and ordered — an intent may not skip from Intent Source
directly to Execution Adapter, exactly as INV-001/INV-002 (107B) already
forbid skipping the execution lifecycle's named states. The pipeline and
the state model (§5 below) are two views of the same frozen sequence.

## 4. Runtime Principles

Eleven principles are frozen: Modular, Pluggable, Connected, Observable,
Automatable, Governed, Fail-closed, Least privilege, Human-controlled,
Deterministic, Testable. Each is defined in
`docs/PCAE_RUNTIME_ARCHITECTURE.md` §6 with a direct tie to an existing
frozen guarantee (e.g. Fail-closed ties directly to `_compose()`'s
existing empty-registry behavior, 108C; Human-controlled ties directly
to INV-003, 107B) — no principle is asserted without grounding in
something already true of the codebase.

## 5. Runtime State Model Summary

Eight states, frozen:

```
Intent -> Observed -> Advisory -> Approved -> Executable -> Executed
  -> Audited -> Rollback Ready
```

**Current maximum state reachable by any real PCAE command path today:
`Observed`.** The four existing observation integrations (INT-001..004,
109B–109D) reach exactly this state on every invocation and go no
further — the broker is consulted, a decision is produced, and it is
discarded. No command path reaches `Advisory` (decision retained and
surfaced) or beyond.

## Capability Matrix (excerpt — full table in `docs/PCAE_RUNTIME_ARCHITECTURE.md` §7)

| Capability | Current | Future | Phase | Status | Maturity |
|---|---|---|---|---|---|
| Observation | 4 read-only paths, discard-only | All 11 command categories, still discard-only | complete for read-only | implemented (observation-only) | Medium |
| Policy evaluation | Broker evaluate-only, discarded by callers | Decision Pipeline makes decisions available downstream | 110B+ | foundation_implemented | Medium |
| Human approval | None | Approval Plugin enforces INV-003 | 111A | not_implemented | Low |
| Execution | None | Execution Adapter mediates all real action | not scheduled | not_implemented | None |
| Notification (outbound) | Working (Telegram, stdout, filesystem, mock) | Generalized under plugin contract | not scheduled | partially_implemented | High |

## Execution Integration Status

Unchanged from 109D — this phase adds no new command-path integration,
touches no source code, and introduces no execution capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (`pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push check` — unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |

## Safety Case

- **Why this phase cannot introduce execution capability:** it touches
  no file under `src/pcae/` — its task contract's allowed files are
  limited to three documentation files, one test file, and standard
  status-tracking files. There is no code path by which a documentation
  phase could grant execution capability.
- **Why the architecture itself cannot silently become enforcement:**
  every component named in this phase's documents either already exists
  with a frozen, unmodified contract (Permission Broker, `COMP-001`..`010`,
  the four `INT-NNN` observation integrations) or is explicitly marked
  `not_implemented` with no code backing it. The Runtime, the Intent
  Pipeline, the Decision Pipeline (as a stage separate from the broker
  it wraps), the Execution Adapter, the Evidence Pipeline, and nine of
  the ten plugin categories are pure documentation as of this phase.
- **Why observation remains the ceiling:** the state model (§5)
  explicitly marks `Observed` as the current maximum reachable state,
  and the No-Go confirmations (below) restate, in the same form every
  prior phase has used, that no execution-adjacent capability was added.

## Limitations

- This phase defines architecture; it does not validate that the
  architecture is buildable without further design work. Several
  interface contracts (§5 of the Runtime Architecture document) note
  open questions a future phase must resolve deliberately (e.g. what
  "available" means for a decision reaching the Advisory state) rather
  than pre-deciding them here.
- The capability matrix and state model are internally consistent with
  each other and with 107B/109A, but neither has been validated against
  an actual prototype implementation — that is explicitly deferred to
  110B and beyond.
- Two plugin categories (Storage, Context) are described partly in terms
  of informal precedents (`.pcae/` filesystem usage, `pcae session
  bootstrap`) rather than a single canonical implementation; a future
  phase formalizing these categories will need to reconcile several
  existing ad hoc call sites, not just one.

## No-Go Confirmations

No runtime execution. No command authorization. No command denial. No
shell mediation. No subprocess mediation. No backend invocation. No
adapter invocation. No execution enablement. No execution capability. No
Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST server. No
web server. No daemon. No background workers. No automatic apply. No
command execution. No plugin loading implementation. No dependency
injection framework. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. `v0.1.0-rc1`
remains non-executing by design. v0.2 remains the autonomy target
(Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and branch
protection on `main` are unchanged. No new tag. No new GitHub Release.
No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110B — Runtime Plugin Contract Freeze.**
