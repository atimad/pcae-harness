# PCAE Runtime Introspection Architecture

**Frozen by**: Phase 111A | **Status**: architecture/design only — no
introspection implementation, CLI introspection command, REST endpoint,
web UI, plugin loading, plugin instantiation, plugin invocation,
dependency injection, runtime execution, command authorization,
command denial, shell mediation, backend invocation, adapter
invocation, execution enablement, execution capability, Permission
Broker enforcement, audit persistence, rollback execution, emergency
stop, Telegram inbound, daemon, background workers, or automatic apply
is performed by this document or this phase.

## Purpose

Design how PCAE exposes Runtime, Registry, Plugin, Capability, Session,
and Health information through a safe, read-only introspection model.
110A froze the Runtime's architecture; 110B froze plugin contracts;
110C froze the Service Registry's architecture; 110D froze the
Registry's API/resolution contract; 110E built the first passive,
metadata-only Registry implementation; 110F verified it. None of those
six phases described *how an outside observer would ask the Runtime
what it currently knows* — that missing layer is Runtime Introspection,
designed (not implemented) here.

This document builds on, and changes none of:

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A) — the Runtime, the
  seven-stage pipeline, the ten plugin categories, the nine Runtime
  Services, the eleven principles, and the eight-state Runtime State
  Model.
- `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B) — the eighteen-field
  contract model, the ten-class capability taxonomy, the eight-state
  plugin lifecycle model.
- `docs/PCAE_RUNTIME_SERVICE_REGISTRY.md` (110C) and
  `docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md` (110D) — the Registry's
  architecture and canonical API/resolution contract.
- `src/pcae/core/runtime_registry.py` (110E, verified 110F) — the first
  concrete, metadata-only `RuntimeRegistry`/`PluginDescriptor`
  implementation this document's design would, in a future phase,
  expose read-only views of.

## Core Architectural Principle

```
Runtime orchestrates.
Registry resolves.
Plugins implement.
Metadata precedes behavior.
```

Extended with this phase's own addition:

```
Visibility precedes authority.
```

Every prior 110-series phase asked "what can the Runtime *do*" (110A's
pipeline, 110C's resolution) or "what can the Runtime *know*" (110D's
contract vocabulary, 110E/110F's metadata store). This phase asks a
third, distinct question: "what can the Runtime *show*" — and answers
it before any phase asks "what can the Runtime *authorize*." A system
that can be observed, audited, and reasoned about by a human before it
can act is strictly safer than one designed the other way around.
"Visibility precedes authority" names that ordering as a standing
constraint: no future authorization, approval, or execution capability
phase may skip past introspection — the visibility layer this document
designs must exist, in frozen form, before any of those phases are
scheduled. This mirrors, at the observability layer, the same
discipline 110B's "Pluggable first... Executable last" ordering already
enforces at the plugin-capability layer.

## 1. Runtime Introspection, Defined

**Definition.** Runtime Introspection is the Runtime's read-only
visibility layer: a bounded set of query operations (§7) that report
what the Runtime currently knows about itself, the Registry, plugins,
capabilities, policy, observation, session/task/phase state,
identity, configuration, health, version, and governance — without
ever changing what any of those things *are*. Introspection **exposes
information; it never changes behavior.** No introspection query may
have a side effect on Runtime state, Registry state, plugin state, or
any file on disk beyond what a read already implies (e.g. opening a
file to read it).

**Position relative to the Runtime.** Introspection is not a pipeline
stage (110A §2) and not a Runtime Service (110A §4) in the sense of
Session/Task/Phase (which *hold* state) — it is a cross-cutting,
read-only reporting layer that sits *above* every existing Runtime
Service, Registry, and plugin category, querying their already-frozen
state without participating in orchestration, resolution, or
implementation. It is architecturally analogous to, and generalizes,
precedents that already exist narrowly today: `pcae health` (108E,
observation-only Permission Broker consultation baked in since 109B),
`pcae governance audit` (a read-only, cross-cutting re-verification
pass), and `RuntimeRegistry.registry_health()`/`.validate_consistency()`
(110E/110F, read-only registry introspection scoped to one module).
None of these three precedents is modified by this phase; this
document is the generalization a future implementation phase would
build against.

**What introspection must not become.** An introspection query that
started mutating state, granting access, or influencing a decision
would stop being introspection and start being either orchestration
(110A §1, Runtime's job) or authorization (a future, unscheduled
capability this phase explicitly does not design toward implementing).
Keeping "exposes, never changes" as introspection's sole verb is what
keeps "Visibility precedes authority" a genuine ordering constraint
rather than a slogan.

**Current implementation status: not implemented.** No introspection
module, API, or CLI command exists in `src/pcae/` as a result of this
phase. This document is the design a future implementation phase (111B,
recommended below) would build against.

## 2. Introspection Domains

Fifteen canonical domains are frozen. Each domain names *what kind of
question* introspection can answer about it, and names its current
grounding — either an already-implemented precedent this document
generalizes, or a purely conceptual 110-series design this document is
the first to make queryable even in principle.

| # | Domain | What it answers | Current grounding |
|---|---|---|---|
| 1 | **Runtime** | What is the Runtime, which pipeline stages exist, which principles apply? | 110A (architecture only — no live Runtime instance exists to query). |
| 2 | **Registry** | What plugins are registered, what capabilities are declared, is the store consistent? | `RuntimeRegistry` (110E/110F) — the one domain with a real, queryable implementation today, via `list_plugins()`/`registry_health()`/`validate_consistency()`. |
| 3 | **Plugins** | What plugin categories exist, what does a specific registered plugin's metadata say? | 110B (categories/contracts) + 110E/110F (`PluginDescriptor`, per-instance metadata). |
| 4 | **Capabilities** | Which capability classes exist, which are declared by which plugins, which remain undeclarable? | 110B §3 (ten-class taxonomy) + `RuntimeRegistry.list_capabilities()`/`find_capability()` (110E). |
| 5 | **Policy** | What policy rules exist, what did the last evaluation report? | `PolicyRegistry`/`PermissionBroker` (108A–108D) — narrower in scope than a future Runtime-level Policy Plugin category (110A §3), but already real and already read-only-queryable via `evaluate()`'s returned decision. |
| 6 | **Observation** | Which command paths are observation-integrated, what is their status? | `INTEGRATION_REGISTRY` (109C, `command_path_observation.py`) — four entries, `INT-001`..`INT-004`, already exactly this kind of read-only registry. |
| 7 | **Session** | What session is active, when did it start, what is its continuity state? | `pcae session bootstrap`/`pcae session end` — already implemented and already read-only-queryable via `--json`. |
| 8 | **Task** | What task is active, what are its allowed files, what is its status? | `pcae task show`/`pcae task list` — already implemented. |
| 9 | **Phase** | What phase is current, what was the last completed phase, what phase report exists? | `pcae phase report`/`PROJECT_STATUS.md` — already implemented (the phase-completion-metadata/phase-report machinery every 110-series phase already produces). |
| 10 | **Identity** | What identity concept applies to the current agent/session? | 110A §3 (Identity Plugin category, not implemented) — purely conceptual; `pcae session bootstrap --agent-id` is the closest existing precedent, narrower in scope. |
| 11 | **Configuration** | What configuration applies to the Runtime/a plugin? | 110A §4 (Configuration Runtime Service, not implemented) + `PluginDescriptor`'s eventual Configuration Model field (110B §1 field 9) — purely conceptual today. |
| 12 | **Health** | Is the Runtime/Registry/a plugin's metadata healthy? | `pcae health` (108E) + `RuntimeRegistry.registry_health()` (110E) — see §5 for the frozen Runtime Health Model this document adds on top. |
| 13 | **Version** | What version is the Runtime/a plugin/the contract model at? | `v0.1.0-rc1` (release-level) + 110B §5 (per-plugin semantic versioning rules, not yet exercised by any real instance) — partially grounded. |
| 14 | **Governance** | What is the current governance status (no-go gates, invariants, trust gate)? | `pcae governance audit`, `pcae check`, `pcae doctor task-memory`, `phase_report_trust.py` — already implemented and already the most mature read-only reporting surface in this codebase. |
| 15 | **Future Execution** | What would execution capability look like, if it existed? | 107B/107C (Autonomy Contract, No-Go Gates) — purely conceptual; **permanently the least-visible domain** (§3) until a future phase, not scheduled, explicitly changes that. |

Domains 2, 6, 7, 8, 9, 12, and 14 already have a real, working,
read-only precedent in this codebase today. Domains 1, 3, 4, 10, 11,
13, and 15 are wholly or partially conceptual — introspection for them
means exposing frozen *design*, not live state, until the phases that
would give them live state (a Registry implementation deep enough to
hold live plugin instances, a Configuration Runtime Service, etc.) are
themselves scheduled and completed. This document does not schedule
any of them.

## 3. Introspection Model — Four Visibility Tiers

Every fact any domain (§2) could report is classified into exactly one
of four tiers, frozen here as the canonical introspection model:

| Tier | Meaning | Representative examples |
|---|---|---|
| **Visible** | Exposable today, via a read-only query, with no gating. | Registry plugin count (110F), Registered capabilities (110E), Session ID, Task allowed-files, Phase completion metadata, `pcae health` status, No-go gate IDs (107C), plugin contract field values (110B). |
| **Hidden** | Exists conceptually but is not exposed by any introspection query today, by design (not because it is secret) — typically because the underlying domain itself has no live implementation yet. | Live plugin instance state (no plugin instance exists to have state), Configuration Runtime Service values (110A §4, not implemented), Identity Plugin resolution results (110A §3, not implemented). |
| **Requires future authorization** | Could become visible, but only after a future, unscheduled phase adds an explicit authorization/approval gate in front of it — this document does not design that gate, only reserves the category. | Full audit evidence contents (once an Audit Plugin exists, 110B §2.6), approval records (once an Approval Plugin exists, 110B §2.4), any field a future Identity Plugin marks sensitive. |
| **Permanently unavailable** | Structurally cannot be exposed by introspection under any future authorization, because exposing it would itself be, or directly enable, an execution-capability leak. | Execution handles, running process references, credential/secret material, a mechanism to bypass approval, a mechanism to control execution. Identical in kind to §8's "must never expose" list — this tier is that list's permanent-and-non-negotiable half. |

**Why four tiers, not two.** A simple visible/hidden split would not
distinguish "not implemented yet" (Hidden — an ordinary, expected,
temporary state every 110-series phase has passed through) from
"deliberately gated pending a future authorization design" (Requires
future authorization — a real design commitment about *how* something
would eventually become visible) from "can never be shown, full stop"
(Permanently unavailable — the same category of guarantee 110B §6's
security boundaries and 107C's No-Go Gates already provide elsewhere in
this codebase). Collapsing these into fewer tiers would either
overclaim (implying "Hidden" facts are permanently forbidden, when they
are merely not-yet-implemented) or underclaim (implying "Permanently
unavailable" facts might someday be shown, which they structurally
cannot be, per §8).

## 4. Introspection Objects (Design Only — No Implementation)

Eleven read-only objects are frozen as the shapes a future
introspection implementation would return. Each is a *design-time
field list*, not a class, dataclass, schema, or any other concrete
Python construct — no object below exists in `src/pcae/` as a result
of this phase.

| # | Object | Represents | Field sketch (illustrative, not exhaustive) | Grounding |
|---|---|---|---|---|
| 1 | `RuntimeInfo` | The Runtime itself | pipeline stage names (110A §2), principle names (110A §6), current runtime state (§6 below) | 110A, purely conceptual (no live Runtime instance) |
| 2 | `RegistryInfo` | The Registry's aggregate state | registered plugin count, registered capability count, registry status, metadata validity | Directly maps onto `RegistrySnapshot` (110E/110F, already implemented) |
| 3 | `PluginInfo` | One plugin's metadata | plugin id, plugin type, version, capabilities, lifecycle state, health state, implementation status | Directly maps onto `PluginDescriptor` (110E/110F, already implemented) |
| 4 | `CapabilityInfo` | One capability class | capability name, which plugins declare it, whether it is undeclarable | Maps onto 110B §3 taxonomy + `RuntimeRegistry.find_capability()` (110E) |
| 5 | `HealthInfo` | Aggregate health across every checkable domain | runtime health, registry health, plugin metadata health, manifest validity, contract compatibility, observation coverage, execution availability, approval availability (§5 below) | New this phase — generalizes `pcae health`'s existing shape |
| 6 | `VersionInfo` | Version state across Runtime/contract/plugin | release version (`v0.1.0-rc1`), contract model version (110B §5), per-plugin declared version | Partially grounded (release version is real; per-plugin versioning has no live instance yet) |
| 7 | `GovernanceInfo` | Current governance posture | no-go gate count/IDs (107C), invariant status (107B), trust gate status (`phase_report_trust.py`) | Directly maps onto existing `pcae governance audit`/`pcae check` output |
| 8 | `RuntimeStateInfo` | Current position in the Runtime State Model | current state name, reachable-today flag (§6 below) | Directly maps onto 110A §8's eight-state model, unmodified |
| 9 | `SessionInfo` | Active session | session ID, start time, continuity status | Directly maps onto existing `pcae session bootstrap --json` output |
| 10 | `TaskInfo` | Active task | task ID, title, allowed files, status | Directly maps onto existing `pcae task show --json` output |
| 11 | `PhaseInfo` | Current/last phase | phase ID, phase title, completion status, recommended next phase | Directly maps onto existing `PROJECT_STATUS.md`/phase-completion-metadata content |

**No implementation.** No field list above is a frozen schema — a
future implementation phase (111B) chooses the concrete representation
(dataclass, TypedDict, JSON Schema). This document freezes only *what
information* each object would carry and *which existing precedent* (if
any) it generalizes, exactly as 110C §3's plugin manifest concept froze
fifteen fields without choosing a schema.

## 5. Runtime Health Model (Design Only)

Eight health facets are frozen, generalizing `pcae health`'s existing
shape (108E, already implemented for a narrower scope) into the full
Runtime Introspection domain set:

| Facet | What it reports | Precedent |
|---|---|---|
| Runtime health | Whether the Runtime's own architecture-level invariants hold. | New — no live Runtime instance exists to check yet; conceptual until a future phase gives the Runtime a concrete entry point (110A's own stated limitation). |
| Registry health | `RegistrySnapshot.registry_status`/`.metadata_validity` (empty/populated, valid/invalid). | Directly implemented today: `RuntimeRegistry.registry_health()` (110E/110F). |
| Plugin metadata health | Per-plugin `validate_descriptor()` result, aggregated. | Directly implemented today: `RuntimeRegistry.validate_consistency()` (110E/110F). |
| Manifest validity | Whether a plugin's manifest (110C §3) is internally consistent (no `manifest_*_mismatch` issues). | Directly implemented today, as one component of `validate_descriptor()`'s issue set (110E). |
| Contract compatibility | Whether a plugin's declared version/type/capabilities satisfy 110B §5's rules and 110D §6's five compatibility dimensions. | Partially implemented (semver format check, 110E) + partially conceptual (110D §6's runtime/manifest/contract-version dimensions, not yet checkable without a live Runtime version to compare against). |
| Observation coverage | How many of the four `INTEGRATION_REGISTRY` command paths (109C) are actively observed. | Directly implemented today: `command_path_observation.INTEGRATION_REGISTRY` (109C), currently 4/4. |
| Execution availability | Whether execution capability exists. | Directly implemented today, trivially: always `False`/`"execution_unavailable"` (108A's `PermissionBrokerDecision.implementation_status`, unconditional). |
| Approval availability | Whether an Approval Plugin (110A §3, 110B §2.4) exists to record human approval. | Conceptual — `COMP-003` Human Approval Gate (107B) is not implemented; this facet would report `False`/`not_implemented` today, exactly as every other "not implemented" facet in this codebase does. |

**Current expected aggregate state, reported by every facet above,
without exception: `Healthy`, `Execution unavailable`.** No facet in
this table can report anything execution-related as available — this
is not a current snapshot that might change without a corresponding
architecture phase; it is a structural ceiling every "not implemented"
facet enforces by definition (an unimplemented Approval Plugin cannot
report "approval available" any more than an unimplemented Runtime can
report "Runtime unhealthy" — there is nothing yet to be healthy or
unhealthy about beyond what already has a real implementation).

## 6. Runtime Status Model (Design Only — Restates 110A §8, Not a New Model)

This document deliberately does **not** invent a second, competing
status vocabulary. The "Runtime Status Model" introspection would
report is 110A §8's already-frozen, eight-state Runtime State Model,
verbatim:

```
Intent -> Observed -> Advisory -> Approved -> Executable -> Executed -> Audited -> Rollback Ready
```

(This phase's own brief lists illustrative synonyms — "Approval" for
`Approved`, "Executing" for `Executed`, "Auditing" for `Audited` — informal
shorthand for the same states, not a second vocabulary. Introspection
reports the 110A §8 state names exactly, to avoid the confusion two
divergently-named state models for the same concept would create.)

**Current state, reported by `RuntimeStateInfo` (§4) without
exception: `Observed`.** Per 110A §8, this is still the maximum state
any real PCAE command path reaches today (the four `INTEGRATION_REGISTRY`
entries, 109B–109D) — introspection reporting anything past `Observed`
would be a false claim about capability this codebase does not have,
which is precisely the failure mode "Visibility precedes authority"
exists to prevent: visibility must be *accurate*, not merely present.

## 7. Introspection API (Design Only — No Implementation)

Eight read-only, no-argument (or minimally-parameterized) query
operations are frozen as the canonical Introspection API surface, each
returning one of §4's objects:

| # | Operation | Returns | Purpose |
|---|---|---|---|
| 1 | `GetRuntime()` | `RuntimeInfo` | The Runtime's own architecture-level facts (§2 domain 1). |
| 2 | `GetRegistry()` | `RegistryInfo` | The Registry's aggregate state (§2 domain 2). |
| 3 | `GetPlugins()` | `tuple[PluginInfo, ...]` | Every registered plugin's metadata (§2 domains 3–4). |
| 4 | `GetCapabilities()` | `tuple[CapabilityInfo, ...]` | Every capability class and its declaring plugins (§2 domain 4). |
| 5 | `GetHealth()` | `HealthInfo` | The full Runtime Health Model (§5). |
| 6 | `GetGovernance()` | `GovernanceInfo` | Current governance posture (§2 domain 14). |
| 7 | `GetState()` | `RuntimeStateInfo` | Current position in the Runtime State Model (§6). |
| 8 | `GetVersion()` | `VersionInfo` | Version state across Runtime/contract/plugin (§2 domain 13). |

**Design-only.** No signature (parameter types beyond what is implied
above, return types, error types), no interface definition, no
abstract base class, and no concrete function implementing any of the
eight operations is added by this phase — exactly as 110D §2 froze nine
Registry API operation *names and purposes* without implementing any of
them. `GetPlugins()`/`GetCapabilities()` deliberately return a
collection, mirroring `RuntimeRegistry.list_plugins()`/`.list_capabilities()`'s
already-implemented plural shape (110E); the other six return a single
aggregate object.

**Relationship to existing real commands.** `GetHealth()`,
`GetGovernance()`, `GetState()`, and `GetVersion()` each generalize a
command that already exists in some form today (`pcae health`, `pcae
governance audit`, `PROJECT_STATUS.md`'s phase-position text, `pcae
--version`/release tagging respectively) — this document names the
unified, cross-domain shape those existing narrow commands would
eventually compose into, without modifying any of them.

## 8. Visibility Rules (Frozen)

**The Runtime may expose:**

- Metadata (plugin descriptors, manifests, registration state — 110E/110F)
- Contracts (the eighteen-field plugin contract model, 110B §1)
- Health (§5's eight facets)
- Status (§6's Runtime State Model position)
- Capabilities (110B §3's taxonomy, and which plugins declare which)
- Version (release version, per-plugin declared version, contract model version)
- Compatibility (110D §6's five compatibility dimensions, as a report — never as a gate introspection itself performs)

**The Runtime must never expose:**

- Execution handles (no introspection query may return anything that
  could be used to invoke, control, or reference a running process —
  there are none today, and none may be exposed even conceptually)
- Plugin instances (only `PluginDescriptor`-shaped metadata, §4 object
  3, is exposable — never a live plugin object, since none exist and
  none may be referenced even if they someday do)
- Internal mutable state (introspection returns read-only *copies* or
  *reports*, never a live reference into `RuntimeRegistry._plugins` or
  any other internal store — mirroring 110F's own manifest-immutability
  hardening, applied at the introspection-object level this time)
- Secret material (tokens, keys, credentials — none of §4's objects has
  a field for any of these, by design, not by omission)
- Credentials (as above — Identity Plugin resolution results, §2 domain
  10, remain Hidden per §3's tier model specifically because a future
  Identity Plugin is the correct place to define what, if anything,
  about credentials is ever visible, not this document)
- Approval bypasses (no introspection query may double as, or reveal a
  path to, circumventing a future Approval Plugin — this is the
  introspection-layer restatement of 110B §6's "no bypass of human
  approval" security boundary)
- Execution control (no introspection query may accept a parameter that
  changes what the Runtime does next — every operation in §7 is a pure
  query; none is a command)

Every "must never expose" item above is either a direct restatement of
an already-frozen 110B §6 security boundary, a direct consequence of
§1's "exposes, never changes" definition, or (for execution handles/
plugin instances) a direct consequence of the fact that none currently
exist to expose. No new prohibition is invented by this section beyond
naming the introspection-layer consequences of rules 110A/110B/107B/107C
already established elsewhere.

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
maximum runtime state remains `Observed` (110A §8, unchanged). Current
maximum plugin capability remains `observe` (110B §3, unchanged).
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**111B — Runtime Introspection Prototype (Observation-Only).**
