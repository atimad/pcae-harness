# Phase 110C — Runtime Service Registry & Plugin Discovery Architecture

## Purpose

Design the PCAE Runtime Service Registry and Plugin Discovery
architecture: how the Runtime discovers, resolves, validates, and
reasons about plugins without directly coupling to concrete
implementations. This is architecture/design only — no registry
implementation, plugin loading, or discovery execution exists after
this phase, only its frozen design.

## Scope

- `docs/PCAE_RUNTIME_SERVICE_REGISTRY.md` — the Registry's definition
  and position, service discovery model (8 facets), the plugin manifest
  concept (15 fields, no implementation), capability resolution flow (5
  steps), Registry responsibilities and non-responsibilities, plugin
  responsibility boundaries, the Infrastructure/Capability plugin class
  distinction, and the static/dynamic runtime model.
- `docs/PHASE_110_RUNTIME_SERVICE_REGISTRY_ARCHITECTURE.md` — this
  document.
- `tests/test_runtime_service_registry_architecture.py` —
  documentation-verification tests; no runtime code exists to
  unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. No registry implementation, plugin loading, or dependency
injection framework is added. `docs/ROADMAP.md` was evaluated for an
update and found to already state the relevant long-term vision (110B)
completely — no change was needed or made.

## 1. Service Registry Summary

The Registry is the canonical resolution layer between the Runtime and
every plugin instance, generalizing two existing narrow precedents
(`PolicyRegistry`, 108B; `INTEGRATION_REGISTRY`, 109C) that neither do
compatibility checking nor capability-based lookup today. It is not a
pipeline stage — it is a cross-cutting resolution service, architecturally
parallel to the Session/Task/Phase Runtime Services (110A §4). The core
principle — **Runtime orchestrates. Registry resolves. Plugins
implement.** — is extended with this phase's own addition:
**Discoverable always**, a standing property holding across every plugin
lifecycle state (110B §4), not a fifth sequential stage after
"Executable last."

## 2. Service Discovery Summary

Eight discovery facets are frozen: plugin identity, plugin type,
capability declarations, version compatibility, health status,
lifecycle state, security posture, current implementation status. Each
facet has a direct precedent in 110B's contract model or an existing
non-pluggable subsystem (e.g. `pcae hooks status` for health reporting).
Discovery is read-only — the Registry surfaces what a plugin's own hooks
report; it never computes or influences any facet itself.

## 3. Plugin Manifest Summary

A future (unimplemented) manifest concept is frozen with fifteen
fields: Plugin ID, Plugin name, Plugin type, Version, Compatible runtime
version, Capabilities provided, Capabilities required, Dependencies,
Lifecycle hooks, Configuration schema, Security boundaries, Evidence
requirements, Approval requirements, Audit expectations, Current status.
Thirteen of fifteen map directly onto an existing 110B contract field;
only "Plugin name" and "Capabilities required"/"Dependencies" are new,
introduced because manifest-level discovery needs an explicit dependency
graph a single-plugin contract did not need to express. No schema, file
format, parser, or loader is implemented.

## 4. Capability Resolution Summary

A five-step flow is frozen, each step with a single owner: (1) an intent
arrives at the Runtime; (2) the Runtime translates the need into a
capability identifier (illustrative example: `test.execution` /
`command.test` — no grammar is frozen); (3) the Registry resolves every
compatible, healthy, `available`-lifecycle-state candidate, never
picking a winner itself; (4) the Runtime selects one candidate
"according to policy" (mechanism not defined by this phase); (5) the
plugin implements the capability within its category contract's allowed
responsibilities. No resolution algorithm or selection-policy mechanism
is implemented.

## 5. Responsibility Boundary Summary

**Registry owns:** registration metadata, discovery, compatibility
checks, capability lookup, plugin health visibility, lifecycle
visibility, dependency metadata, current availability. **Registry does
not own:** orchestration, policy decisions, approval decisions,
execution, audit persistence, rollback execution — mirroring 108B's
`PolicyRegistry`/`_compose()` split (evaluate vs. decide) generalized to
the plugin-infrastructure layer.

**Plugins own:** declared capability implementation, local health
signal, lifecycle hooks, bounded inputs/outputs, evidence emission where
applicable. **Plugins do not own:** global orchestration,
self-authorization, bypassing the Permission Broker, bypassing approval,
bypassing audit, discovering/calling each other directly. Every
plugin-facing prohibition either restates an already-frozen 110B
security boundary or follows directly from the Registry being the sole
discovery path.

**Infrastructure plugins** (Identity, Storage, Notification, Audit,
Context) provide services other plugins depend on but do not decide,
approve, or execute anything intent-specific. **Capability plugins**
(Intent Source, Policy, Decision, Approval, Execution Adapter)
participate directly in a specific intent's pipeline journey. The
distinction matters for discovery cardinality (one Infrastructure
instance vs. multiple Capability candidates), failure blast radius (an
unavailable Infrastructure plugin silently degrades every dependent
Capability plugin), security posture emphasis (Infrastructure carries
boundaries 5–7; Capability carries boundaries 3–4, 8–10), and long-term
vision framing (the roadmap's intent-source/execution-target plugin
populations are both Capability-class).

## 6. Static/Dynamic Runtime Summary

**Static runtime** (designed by this document): architecture, contracts,
registry, plugin metadata, compatibility. **Dynamic runtime** (explicitly
NOT designed by this document, deferred to a future phase): session,
task, phase, intent, approval, broker decision, execution state. This
phase deliberately stops at the static boundary to avoid designing
dynamic behavior around a still-unvalidated static structure — mirroring
110A's own frozen-architecture-vs-undesigned-entry-point split and 110B's
frozen-contract-vs-no-live-instance split.

## Execution Integration Status

Unchanged from 110B — this phase adds no new command-path integration,
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
- **Why the Registry design itself cannot silently become an
  implementation:** every concept in this document (Registry, manifest,
  resolution flow) is prose-only — no code, no schema, no data
  structure any runtime could load or execute. The capability-resolution
  example flow (§4) is explicitly marked illustrative, not a frozen
  grammar or algorithm.
- **Why the Infrastructure/Capability split does not grant new
  authority:** it is a classification of the *same* ten already-frozen
  110B plugin categories — no eleventh category, no new capability
  class, and no change to any existing category's contract.
- **Why stopping at the static/dynamic boundary is itself a safety
  property:** designing dynamic runtime behavior (live session/task/
  approval/decision/execution state flowing through a Registry) before
  the static structure is validated would risk baking in assumptions a
  future phase would then have to unwind — this phase's scope discipline
  is deliberate, not an oversight.

## Limitations

- This phase designs the Registry's *shape*; it does not validate that
  shape against a prototype implementation, since none exists.
- The capability-identifier grammar (§4) and selection-policy mechanism
  (§4, step 4) are named as open questions a future phase must resolve
  deliberately, not pre-decided here.
- The manifest concept (§3) is not yet expressed as a concrete schema —
  a future phase choosing JSON Schema vs. a Python dataclass vs. TOML
  is an implementation decision this document does not make.

## No-Go Confirmations

No plugin registry implementation. No plugin loading. No plugin
discovery execution. No dependency injection framework. No runtime
execution. No command authorization. No command denial. No
behavior-changing integration. No shell mediation. No subprocess
mediation. No backend invocation. No adapter invocation. No execution
enablement. No execution capability. No Permission Broker enforcement.
No audit persistence. No rollback execution. No emergency stop. No
Telegram inbound. No REST server. No web server. No daemon. No
background workers. No automatic apply. No command execution.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision. Current maximum runtime state
remains `Observed`. Current maximum plugin capability remains `observe`.
No dynamic runtime context implemented. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/GitHub
Packages publication.

## Recommended Next Phase

**110D — Runtime Registry Contract Freeze.**
