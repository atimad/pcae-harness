# Phase 111A — Runtime Introspection Architecture

## Purpose

Design how PCAE exposes Runtime, Registry, Plugin, Capability, Session,
and Health information through a safe, read-only introspection model.
This is architecture/design only — no introspection implementation, CLI
command, or execution capability exists after this phase, only its
frozen design.

## Scope

- `docs/PCAE_RUNTIME_INTROSPECTION.md` — the architecture: introspection
  defined as the Runtime's read-only visibility layer, fifteen frozen
  domains, a four-tier visibility model, eleven introspection objects
  (design only), the Runtime Health Model (eight facets), the Runtime
  Status Model (restating 110A §8, not a new vocabulary), an
  eight-operation Introspection API (design only), and frozen
  visibility rules (may-expose / must-never-expose).
- `docs/PHASE_111_RUNTIME_INTROSPECTION_ARCHITECTURE.md` — this
  document.
- `tests/test_runtime_introspection_architecture.py` —
  documentation-verification tests; no runtime code exists to
  unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. No introspection implementation, CLI command, REST endpoint, or
web UI is added. `docs/ROADMAP.md` was evaluated for an update and
found to need no change; see §7 below.

## 1. Introspection Definition Summary

Runtime Introspection is frozen as the Runtime's read-only visibility
layer: a bounded set of query operations reporting what the Runtime
currently knows, without ever changing what it *is*. It is not a
pipeline stage and not a state-holding Runtime Service — it is a
cross-cutting reporting layer generalizing three existing narrow
precedents (`pcae health`, `pcae governance audit`, and 110E/110F's
`RuntimeRegistry.registry_health()`/`.validate_consistency()`), none of
which this phase modifies. The core principle — Runtime orchestrates,
Registry resolves, Plugins implement, Metadata precedes behavior — is
extended with this phase's own addition: **Visibility precedes
authority** — no future authorization/approval/execution-capability
phase may skip past a frozen introspection layer.

## 2. Domains Summary

Fifteen canonical introspection domains are frozen: Runtime, Registry,
Plugins, Capabilities, Policy, Observation, Session, Task, Phase,
Identity, Configuration, Health, Version, Governance, Future Execution.
Seven (Registry, Observation, Session, Task, Phase, Health, Governance)
already have a real, working, read-only precedent in this codebase
today; the remaining eight are wholly or partially conceptual pending
future architecture phases this document does not schedule. Future
Execution is named as **permanently the least-visible domain** until an
explicit, not-yet-scheduled future phase changes that.

## 3. Health Model Summary

Eight Runtime Health facets are frozen, generalizing `pcae health`'s
existing shape: runtime health, registry health, plugin metadata
health, manifest validity, contract compatibility, observation
coverage, execution availability, approval availability. Four of eight
(registry health, plugin metadata health, manifest validity,
observation coverage) already have a directly-implemented precedent
today (110E/110F, 109C); the remaining four are conceptual or
trivially-fixed (execution availability is always `False` by
definition, since `implementation_status` is unconditionally
`"execution_unavailable"`, 108A). **Current expected aggregate state,
without exception: Healthy, Execution unavailable** — a structural
ceiling, not a snapshot that could drift without a corresponding
architecture phase.

## 4. Status Model Summary

The "Runtime Status Model" is 110A §8's already-frozen eight-state
Runtime State Model, restated verbatim — this document deliberately
does not invent a second, competing vocabulary (the brief's own
"Approval"/"Executing"/"Auditing" phrasing is treated as informal
shorthand for `Approved`/`Executed`/`Audited`, not a new state set).
**Current state, without exception: `Observed`** — the same ceiling
110A §8 already froze, unmodified.

## 5. Visibility Model Summary

A four-tier classification is frozen for every fact any domain could
report: **Visible** (exposable today, no gating — e.g. Registry plugin
count, Session ID), **Hidden** (conceptual, not exposed because the
underlying domain has no live implementation yet — e.g. Configuration
Runtime Service values), **Requires future authorization** (could
become visible only after an explicit, not-yet-designed future gate —
e.g. audit evidence contents, once an Audit Plugin exists), and
**Permanently unavailable** (structurally cannot be exposed under any
future authorization, because exposure would itself leak execution
capability — e.g. execution handles, credentials). Four tiers, not two,
specifically to avoid conflating "not implemented yet" with
"permanently forbidden."

## 6. Introspection API Summary

Eight design-only, no-implementation operations are frozen:
`GetRuntime()`, `GetRegistry()`, `GetPlugins()`, `GetCapabilities()`,
`GetHealth()`, `GetGovernance()`, `GetState()`, `GetVersion()`. Each
returns one of eleven frozen introspection objects (`RuntimeInfo`,
`RegistryInfo`, `PluginInfo`, `CapabilityInfo`, `HealthInfo`,
`VersionInfo`, `GovernanceInfo`, `RuntimeStateInfo`, `SessionInfo`,
`TaskInfo`, `PhaseInfo`) — field lists only, no schema, dataclass, or
implementation chosen. `RegistryInfo`/`PluginInfo` map directly onto
already-implemented 110E/110F shapes (`RegistrySnapshot`/
`PluginDescriptor`); `SessionInfo`/`TaskInfo`/`PhaseInfo` map directly
onto already-implemented `pcae session`/`task`/`phase` JSON output.

## 7. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. Neither
"Discoverable always" (110C) nor "Metadata precedes behavior" (110E)
appears in `docs/ROADMAP.md` today — both prior phases found the
roadmap's standing ordering text already sufficient at its coarser
grain and made no change. This phase's own addition, "Visibility
precedes authority," is the same kind of phase-scoped principle
addition, not a change to long-term vision or phase ordering. **No
change to `docs/ROADMAP.md` was needed or made**, matching 110C's/
110D's/110E's/110F's own evaluation outcome.

## Execution Integration Status

Unchanged from 110F — this phase adds no new command-path integration,
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
  limited to documentation, one test file, and standard status-tracking
  files.
- **Why the introspection design itself cannot silently become an
  implementation:** every concept in this document (domains, objects,
  API, health/status models) is prose-only — no code, no schema, no
  class, no data structure any runtime could load or execute.
- **Why the visibility rules (§8 of the architecture document) cannot
  be silently weakened:** every "must never expose" item is either a
  direct restatement of an already-frozen 110B §6 security boundary or
  a direct consequence of nothing currently existing to expose
  (execution handles, plugin instances) — no new prohibition is
  invented, and none can be relaxed without contradicting material
  frozen in an earlier, still-binding phase.
- **Why the Runtime Status Model cannot drift from 110A §8:** this
  document explicitly restates it verbatim rather than defining a
  second vocabulary, closing off the specific risk of two
  divergently-named state models for the same concept coexisting in
  this codebase.

## Limitations

- This phase designs the introspection *shape*; it does not validate
  that shape against a prototype implementation, since none exists
  (111B is the recommended next phase for a first, observation-only
  prototype).
- Seven of fifteen domains (§2) and several introspection objects (§4
  of the architecture document) remain wholly or partially conceptual,
  pending future architecture phases (a Configuration Runtime Service,
  an Identity Plugin, a live Runtime entry point) this document does
  not schedule.
- The four-tier visibility model (§3 of the architecture document)
  names "Requires future authorization" as a reserved category without
  designing the authorization mechanism itself — a deliberate, explicit
  open question for a future phase, not a gap in this one.

## No-Go Confirmations

No runtime introspection implementation. No CLI introspection command.
No REST endpoint. No web UI. No plugin loading. No plugin
instantiation. No plugin invocation. No dependency injection. No
runtime execution. No command authorization. No command denial. No
shell mediation. No backend invocation. No adapter invocation. No
execution enablement. No execution capability. No Permission Broker
enforcement. No audit persistence. No rollback execution. No emergency
stop. No Telegram inbound. No daemon. No background workers. No
automatic apply. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed`. Current maximum plugin
capability remains `observe`. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**111B — Runtime Introspection Prototype (Observation-Only).**
