# PCAE Runtime Registry Contract Freeze & Resolution Semantics

**Frozen by**: Phase 110D | **Status**: contract/freeze only — no
registry implementation, plugin loading, plugin discovery execution,
dependency injection framework, runtime execution, command
authorization, command denial, behavior-changing integration, shell
mediation, subprocess mediation, backend invocation, adapter invocation,
execution enablement, execution capability, Permission Broker
enforcement, audit persistence, rollback execution, emergency stop,
Telegram inbound, REST server, web server, daemon, background workers,
automatic apply, or command execution is performed by this document or
this phase.

## Purpose

Freeze the canonical Runtime Registry contract before any registry
implementation begins. 110C designed the Registry's *architecture* —
what it is, what it resolves, and where it sits. This document freezes
the Registry's *contract*: its canonical API surface, capability
namespace conventions, resolution outcome semantics, plugin selection
strategies, compatibility rules, lifecycle interaction model, and
failure behavior. A future implementation phase would build against
this contract; this document implements no part of it.

This document builds on, and changes none of:

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A) — the Runtime, the
  seven-stage pipeline, the ten plugin category names, the nine runtime
  services, the eleven principles, and the eight-state runtime state
  model.
- `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B) — the eighteen-field
  contract model, the ten category contracts, the ten-class capability
  taxonomy, the eight-state plugin lifecycle model, compatibility/
  versioning rules, and the ten security boundaries.
- `docs/PCAE_RUNTIME_SERVICE_REGISTRY.md` (110C) — the Registry's
  definition and position, the eight-facet service discovery model, the
  fifteen-field plugin manifest concept, the five-step capability
  resolution flow, Registry/plugin responsibility boundaries, the
  Infrastructure/Capability plugin class distinction, and the
  static/dynamic runtime model.
- `docs/ROADMAP.md`'s Long-Term Runtime Vision (110B) — "Pluggable
  first. Connected second. Automated third. Executable last."

## Core Architectural Principle (Unchanged)

```
Runtime orchestrates.
Registry resolves.
Plugins implement.
```

```
Pluggable first.
Connected second.
Automated third.
Executable last.
Discoverable always.
```

This document does not modify these principles. It freezes the
contract that keeps the Registry's "resolves" verb precise: what
operations it exposes, what a resolution outcome can mean, and what
must happen when resolution fails.

## 1. The Registry as Single Authoritative Service-Resolution Interface

The Registry is the Runtime's **only** service-resolution interface.
Restated from 110C §1, now frozen as contract:

- The Runtime interacts only with the Registry to locate a plugin
  instance — never with a plugin directly, never by hardcoded class or
  module path (110C §1, "What the Runtime must not know").
- Plugins never communicate directly with each other (110C §1, "What
  plugins must not know"; 110B §6, boundary "discovering/calling each
  other directly"). The Registry is the sole discovery path.
- The Registry never owns orchestration (110C §5, "does not own":
  Orchestration). It answers resolution questions; it does not sequence
  pipeline stages, decide policy, or execute anything.

This section adds no new rule — it names the existing 110A/110B/110C
constraints "the Registry is the single authoritative service-resolution
interface" as one composite, citable contract clause.

## 2. Canonical Registry API (Design Only — No Implementation)

Nine operations are frozen as the Registry's canonical API surface.
Each is a *design-time signature concept* — no function, class, method,
or interface implementing any of them exists in `src/pcae/` after this
phase.

| # | Operation | Purpose | Owner precedent |
|---|---|---|---|
| 1 | `RegisterPlugin()` | Admit a plugin instance's manifest (110C §3) into registration metadata (110C §5, "Registry owns: Registration metadata"). | New — no existing operation registers a plugin instance today. |
| 2 | `UnregisterPlugin()` | Remove a plugin instance's registration metadata, e.g. on `retired` lifecycle transition (110B §4). | New — symmetric counterpart to `RegisterPlugin()`. |
| 3 | `DiscoverCapabilities()` | Surface the capability declarations (110C §2, "Capability declarations" facet) a registered instance honestly claims. | 110C §2, discovery facet 3. |
| 4 | `ResolveCapability()` | Given a capability identifier, return every compatible, healthy, `available`-lifecycle candidate (110C §4, step 3). | 110C §4, capability resolution flow. |
| 5 | `ListPlugins()` | Enumerate all currently registered plugin instances, regardless of capability. | New — a coarser-grained sibling of `ResolveCapability()`. |
| 6 | `GetPluginMetadata()` | Return a single registered instance's full manifest (110C §3, fifteen fields). | 110C §3. |
| 7 | `GetPluginHealth()` | Surface (not compute) a single instance's current Health Reporting output (110C §2, "Health status" facet). | 110C §2, discovery facet 5; 110B §1, field 10. |
| 8 | `ValidateCompatibility()` | Evaluate one instance's version/manifest/contract compatibility against current Runtime/contract versions (§6 below). | 110B §5's compatibility rules, applied per-instance. |
| 9 | `ListCapabilityProviders()` | Enumerate every registered instance that declares a given capability, independent of current health/availability (broader than `ResolveCapability()`, which additionally filters by compatibility/health/lifecycle). | New — the "raw declaration" view `ResolveCapability()`'s filtered view is built on top of. |

**Design-only.** No signature (parameter types, return types, error
types), no interface definition, no abstract base class, no protocol,
and no concrete function implementing any of the nine operations is
added by this phase. The table above freezes *names and purposes*, not
executable contracts.

**Relationship between operations 4 and 9.** `ListCapabilityProviders()`
returns every instance that *declares* a capability (110C §2's
discovery facet, read-only). `ResolveCapability()` additionally applies
the compatibility, health, and lifecycle filters 110C §4 step 3 already
specified — it is `ListCapabilityProviders()` narrowed to currently
usable candidates. Both are frozen as distinct operations because a
future diagnostic or audit use case may need the unfiltered view (e.g.
"why isn't plugin X eligible" requires seeing it in the declared set
even when it is filtered out of the resolved set).

## 3. Capability Namespace Conventions (Design Only)

Capability identifiers follow a dotted `domain.action` convention. 110C
§4 step 2 named this need but froze no grammar; this document freezes
the naming *convention* (illustrative namespace list), still with no
identifier grammar (regex, parser, or validator) implemented.

| Namespace | Domain | Plugin category precedent (110A §3 / 110B §2) |
|---|---|---|
| `intent.receive` | Intent Source | Intent Source Plugin |
| `intent.plan` | Intent Source | Intent Source Plugin |
| `policy.evaluate` | Policy | Policy Plugin |
| `decision.observe` | Decision | Decision Plugin (`observe` capability class, 110B §3) |
| `decision.advise` | Decision | Decision Plugin (`advise` capability class, 110B §3) |
| `approval.request` | Approval | Approval Plugin |
| `approval.record` | Approval | Approval Plugin |
| `execution.shell` | Execution Adapter | Execution Adapter Plugin |
| `execution.git` | Execution Adapter | Execution Adapter Plugin |
| `execution.backend` | Execution Adapter | Execution Adapter Plugin |
| `execution.filesystem` | Execution Adapter | Execution Adapter Plugin |
| `audit.write` | Audit | Audit Plugin |
| `audit.verify` | Audit | Audit Plugin |
| `notification.send` | Notification | Notification Plugin |
| `storage.read` | Storage | Storage Plugin |
| `storage.write` | Storage | Storage Plugin |
| `identity.resolve` | Identity | Identity Plugin |
| `context.session` | Context | Context Plugin |
| `context.phase` | Context | Context Plugin |

**Design-only, illustrative.** These eighteen identifiers are examples
of the convention, not an exhaustive or enforced namespace registry. No
namespace validator, no capability-identifier parser, and no
enforcement of `domain.action` shape is implemented. A future phase may
add, rename, or extend namespaces without violating this document, as
long as the `domain.action` convention itself is preserved or a
successor convention is explicitly frozen in its place. Every namespace
above maps to one of the ten plugin categories already frozen in 110A
§3 / 110B §2 — no new plugin category is introduced by this document.

## 4. Resolution Semantics (Design Only)

`ResolveCapability()` (§2, operation 4) can conclude with exactly one of
nine frozen outcomes. Each outcome is documented; none is implemented.

| Outcome | Meaning | Runtime consequence |
|---|---|---|
| `Resolved` | Exactly one compatible, healthy, `available`-lifecycle candidate found. | Runtime may proceed to selection (§5) trivially — there is only one candidate. |
| `MultipleCandidates` | More than one compatible, healthy, `available`-lifecycle candidate found. | Runtime must apply a selection strategy (§5); the Registry never picks a winner (110C §4, step 3, unchanged). |
| `NoProvider` | No registered instance declares the requested capability at all (110C §2's "Capability declarations" facet is empty for this capability). | No execution (§11). |
| `Incompatible` | At least one candidate declares the capability, but none pass `ValidateCompatibility()` (§6). | No execution (§11) — behaves as `NoProvider` from the Runtime's perspective. |
| `Disabled` | A candidate exists and would otherwise be compatible, but its lifecycle state (110B §4) is `disabled`. | Treated as unavailable; excluded from the candidate set. |
| `Unavailable` | A candidate exists and would otherwise be eligible, but is transiently unreachable (110C §5's "Current availability," narrower than lifecycle `available`). | Treated as unavailable for this resolution attempt; may succeed on retry. |
| `HealthRejected` | A candidate exists but its Health Reporting output (110C §2, facet 5) indicates unhealthy. | Excluded from the candidate set; not an error, a filtered-out candidate. |
| `VersionRejected` | A candidate exists but fails `ValidateCompatibility()`'s version check specifically (§6, "plugin version" / "runtime version" mismatch). | Excluded from the candidate set; a named subtype of `Incompatible` kept distinct because version mismatches are the most common compatibility failure and benefit from a dedicated outcome for diagnostics. |
| `PolicyRejected` | A candidate exists, is compatible and healthy, but a policy (Policy Plugin, `policy.evaluate`) excludes it from this specific resolution. | Excluded from the candidate set; distinguishes "this plugin cannot work at all" (`Incompatible`/`HealthRejected`) from "this plugin could work but policy says no here" (`PolicyRejected`). |

**Design-only.** No enum, exception type, return-value structure, or
outcome-computation algorithm is implemented. The nine outcomes are
frozen as a documented vocabulary a future implementation must use
verbatim (or a superset of), not as executable code.

**Relationship to responsibility boundaries.** `PolicyRejected` does not
mean the Registry evaluates policy (110C §5, "does not own: Policy
decisions" is unchanged) — it means the Registry's resolution result
*reflects* a policy evaluation the Policy Plugin (or Runtime, consulting
the Policy Plugin) already performed and handed to the Registry as a
constraint on this resolution call. The Registry surfaces the outcome;
it does not decide the policy.

## 5. Plugin Selection Semantics (Design Only)

When `ResolveCapability()` returns `MultipleCandidates` (§4), the
Runtime — never the Registry (110C §4, step 4, unchanged) — selects one
candidate. Seven future selection strategies are named; none is
implemented, and none is chosen as a default by this document.

| Strategy | Selection rule |
|---|---|
| `HighestPriority` | Select the candidate with the highest declared priority value (priority field not yet defined by any prior phase — named here as a future manifest/configuration concept only). |
| `HighestVersion` | Select the candidate with the highest semantic version (110B §5). |
| `Healthiest` | Select the candidate whose Health Reporting output (110C §2, facet 5) indicates the strongest health signal among eligible candidates. |
| `PolicyPreferred` | Select the candidate a Policy Plugin evaluation (`policy.evaluate`, §3) names as preferred. |
| `UserPreferred` | Select the candidate matching an explicit human-configured preference (mechanism not defined by this phase). |
| `ManualSelection` | Defer to a human decision for this specific resolution instead of an automatic strategy. |
| `FirstCompatible` | Select the first candidate `ResolveCapability()` returns, in registration order. |

**Design-only.** No selection algorithm, no strategy interface, no
configuration mechanism for choosing a strategy, and no default
strategy is implemented or designated. Which strategy (or combination)
a future Runtime implementation uses is explicitly left open — this
document freezes the vocabulary of possible strategies, not a decision
among them.

## 6. Compatibility Rules (Design Only)

`ValidateCompatibility()` (§2, operation 8) evaluates compatibility
across five version dimensions, plus a migration-policy placeholder.
None of the five checks is implemented; this section documents what a
future implementation must evaluate.

| Dimension | What is compared | Precedent |
|---|---|---|
| Runtime version | The Runtime's own version against a plugin instance's declared "Compatible runtime version" (110C §3, manifest field 5). | 110B §5's compatibility rules, unmodified. |
| Plugin version | A plugin instance's own semantic version (110B §1, field 11; 110C §3, manifest field 4). | 110B §5. |
| Manifest version | The version of the manifest schema itself (110C §3 notes no manifest schema is yet implemented — this dimension is a placeholder for when one exists). | New — anticipates 110C §3's "future phase choosing JSON Schema vs. a Python dataclass vs. TOML." |
| Contract version | The version of the plugin category contract (110B) a plugin instance claims to satisfy. | 110B's eighteen-field contract model, unmodified. |
| Capability version | The version of a specific capability identifier's semantics (§3) a plugin instance implements, independent of the plugin's own overall version. | New — anticipates that a single capability namespace (e.g. `execution.shell`) could itself evolve semantics across versions independent of the plugin's release version. |

**Future migration policy.** How an incompatibility across any of the
five dimensions above should be *resolved* over time (e.g. deprecation
windows, forced-upgrade policies, compatibility shims) is explicitly
**not defined by this document** — named here as an open question a
future phase must address deliberately, mirroring 110C §8's explicit
static/dynamic boundary discipline.

**Design-only.** No version-comparison algorithm, no semantic-version
parser, and no compatibility matrix data structure is implemented.

## 7. Plugin Lifecycle Interaction (Observation Only)

The Registry **observes** the plugin lifecycle model 110B §4 already
froze (eight states); it never drives a transition. Six of the eight
110B lifecycle states are directly relevant to Registry-visible state
(the remaining two — `defined` and any pre-registration states — are
outside what a Registry can observe, since observation requires prior
registration):

| Lifecycle state (Registry-observed) | Registry's relationship to it |
|---|---|
| `Registered` | The Registry's own admission point (§2, `RegisterPlugin()`) — the first state the Registry itself can observe. |
| `Available` | Registry surfaces this as eligible for `ResolveCapability()` (§4, `Resolved`/`MultipleCandidates` outcomes). |
| `Unavailable` | Registry surfaces this as excluded from resolution (§4, `Unavailable` outcome). |
| `Disabled` | Registry surfaces this as excluded from resolution (§4, `Disabled` outcome). |
| `Deprecated` | Registry surfaces this in metadata (`GetPluginMetadata()`, §2) as a signal a future selection strategy (§5) may weigh, without the Registry itself excluding a deprecated-but-still-`available` instance. |
| `Removed` | The Registry's own eviction point (§2, `UnregisterPlugin()`). |

**Registry never executes lifecycle.** Restated as contract: the
Registry does not cause a plugin instance to transition between
lifecycle states (that is the plugin's own lifecycle hooks, 110B §1
field 7, and — for the two Registry-owned endpoints, `Registered` and
`Removed` — the explicit `RegisterPlugin()`/`UnregisterPlugin()` calls
a future Runtime or operator would invoke, not an autonomous decision
the Registry makes on its own). This is the same "surfaces, does not
drive" relationship 110C §5 already froze for lifecycle visibility in
general, now stated per-state.

## 8. Registry Responsibilities (Restated as Contract, Unchanged from 110C §5)

**The Registry owns:**

- Registration metadata
- Discovery
- Capability lookup
- Compatibility evaluation
- Plugin metadata
- Plugin health visibility
- Availability visibility

**The Registry does not own:**

- Execution
- Orchestration
- Approval
- Policy
- Audit persistence
- Rollback

This section restates 110C §5's Registry responsibility split verbatim
as a frozen contract clause (not a re-derivation) — no responsibility is
added, removed, or reworded from its 110C meaning; this document only
elevates it from architectural description to contract.

## 9. Runtime Responsibilities (Restated as Contract, Unchanged from 110A §1 / 110C §4)

**The Runtime owns:**

- Orchestration
- Workflow progression
- Policy invocation
- Approval invocation
- Plugin invocation
- State transitions
- Registry interaction

**The Runtime never owns:**

- Plugin metadata
- Capability storage
- Plugin discovery

This section is the Runtime-facing mirror of §8: the Runtime is the
sole caller of the Registry's API (§2) and the sole party that performs
selection (§5) among candidates the Registry returns — it never stores
or computes plugin metadata, capability declarations, or discovery
facets itself (that storage and computation belongs entirely to the
Registry, §8). Unchanged from 110A §1's "Runtime orchestrates" and 110C
§4's five-step flow.

## 10. Plugin Responsibilities (Restated as Contract, Unchanged from 110B §1/§6 / 110C §6)

**Plugins own:**

- Declared capabilities
- Bounded implementation
- Health reporting
- Manifest
- Version
- Local lifecycle

**Plugins never own:**

- Global orchestration
- Global discovery
- Authorization
- Approval bypass
- Registry modification

"Registry modification" here means a plugin instance may never call
`RegisterPlugin()`/`UnregisterPlugin()`/or any other Registry API
operation (§2) on another plugin's behalf, or alter another instance's
registration metadata — a plugin instance may only affect its *own*
registration state, and even that only through the lifecycle hooks
110B §1 field 7 already scoped to it. This is a direct restatement of
110C §6's "Plugins do not own: ... Discovering or calling each other
directly," made explicit for the Registry API surface specifically.

## 11. Failure Behavior (Design Only)

Registry-related failures must fail safely — toward *no execution*,
never toward an implicit default execution path. Four failure
scenarios are frozen:

| Failure scenario | Consequence |
|---|---|
| **No provider** (`ResolveCapability()` → `NoProvider`, §4) | No execution. The Runtime has no candidate to select from (§5) and must not fall back to any hardcoded or implicit plugin. |
| **Multiple providers** (`ResolveCapability()` → `MultipleCandidates`, §4) | No automatic execution. The Runtime must apply an explicit selection strategy (§5) before any plugin is invoked — ambiguity is never silently resolved by picking "the first one" unless `FirstCompatible` (§5) was the deliberately configured strategy. |
| **Registry unavailable** | Execution unavailable. If the Registry itself cannot be reached or queried, the Runtime has no resolution path at all — this is a stricter failure than any single plugin being unavailable (§4's `Unavailable` outcome), since it removes the Runtime's only resolution mechanism entirely. |
| **Manifest invalid** | Plugin unavailable. An instance whose manifest (110C §3) fails to parse, is missing required fields, or otherwise cannot be validated is treated as if it were not registered — it must not be resolved, listed as a viable candidate, or selected. |
| **Compatibility failure** (`ValidateCompatibility()` fails, §6) | Plugin unavailable. Mirrors the `Incompatible`/`VersionRejected` resolution outcomes (§4) — an incompatible instance is excluded, never invoked with a compatibility waiver. |

**Design-only.** No exception hierarchy, no error-handling code path,
and no fail-safe enforcement mechanism is implemented. This section
freezes the *required direction* of failure (always toward less
execution capability, never more) as a contract constraint a future
implementation must satisfy, not as executable error handling.

## No-Go Confirmations

No registry implementation. No plugin loading. No plugin discovery
execution. No dependency injection framework. No runtime execution. No
command authorization. No command denial. No behavior-changing
integration. No shell mediation. No subprocess mediation. No backend
invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No REST server. No web server. No daemon. No background
workers. No automatic apply. No command execution.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision. Current maximum runtime state
remains `Observed` (110A §8, unchanged). Current maximum plugin
capability remains `observe` (110B §3, unchanged). No dynamic runtime
context is implemented — this document extends only the static runtime
model (110C §8) with contract-level detail; the dynamic runtime remains
deferred to a future phase. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**110E — Runtime Registry Prototype (Observation-Only).** The prototype
should implement only passive registration and discovery of plugin
metadata. It must not instantiate plugins, invoke plugins, authorize
commands, or introduce any execution capability.
