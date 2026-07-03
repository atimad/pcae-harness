# Phase 111B — Runtime Introspection Prototype (Observation-Only)

## Purpose

Implement the first observation-only Runtime Introspection prototype:
in-process, read-only data structures/functions exposing Runtime,
Registry, Plugin, Capability, Health, Version, Governance, and
RuntimeState metadata, integrated with the passive Runtime Registry
(110E/110F). **This is in-process introspection data/model only** — no
CLI command, no plugin loading/instantiation/invocation, no execution
capability. `pcae runtime inspect` is explicitly deferred to 111C.

## Scope

- `src/pcae/core/runtime_introspection.py` — the implementation: eight
  frozen architecture-level constants restated from 110A, eight
  introspection objects (two realized as type aliases of existing
  110E/110F shapes, six new frozen dataclasses), and eight functions
  mirroring 111A §7's canonical API operation names 1:1.
- `tests/test_runtime_introspection_prototype.py` — 74 tests covering
  every objective: object existence, registry integration, health/
  status/governance snapshots, immutability, no-CLI confirmation,
  111A/110E/110F compatibility, and module isolation.
- `tests/test_runtime_introspection_architecture.py` — one guard test
  updated (`test_no_introspection_module_added_to_core`): as of 111A no
  implementation existed; 111B's `runtime_introspection.py` is the
  expected, intentional next step, so it is removed from that test's
  forbidden-filename set rather than left to perpetually fail.
- `docs/PHASE_111_RUNTIME_INTROSPECTION_PROTOTYPE.md` — this document.

No file under `src/pcae/cli.py` or `src/pcae/commands/` is touched —
confirmed both by the task contract's allowed files and by dedicated
tests. `docs/ROADMAP.md` was evaluated for an update; see §7 below.

## 1. Introspection Implementation Summary

`src/pcae/core/runtime_introspection.py` implements eight of 111A's
eleven frozen introspection objects. Two — `RegistryInfo` and
`PluginInfo` — are realized as direct type aliases of 110E/110F's own
`RegistrySnapshot`/`PluginDescriptor` (`RegistryInfo = RegistrySnapshot`,
`PluginInfo = PluginDescriptor`), not new duplicate dataclasses, since
111A §4 already named those exact existing shapes as what those two
objects map onto. The remaining six (`RuntimeInfo`, `CapabilityInfo`,
`HealthInfo`, `VersionInfo`, `GovernanceInfo`, `RuntimeStateInfo`) are
new frozen dataclasses, each grounded in an already-existing source
(architecture-level constants restated from 110A, live `RuntimeRegistry`
queries, or already-frozen governance constants) — none fabricates a
field with no real backing source.

**Deliberately deferred, not implemented this phase:** `SessionInfo`,
`TaskInfo`, `PhaseInfo`. This phase's own goal statement scopes
introspection to "runtime, registry, plugin, capability, health, state,
and governance metadata" — Session/Task/Phase are not named. Each of
those three domains already has a full, working, filesystem-backed
precedent (`pcae session bootstrap --json`, `pcae task show --json`,
`pcae phase report --json`) reading live `.pcae/` state — a materially
different scope (filesystem I/O, live session/lock state) from this
phase's in-process, `RuntimeRegistry`-backed model. Tests confirm
directly that `SessionInfo`/`TaskInfo`/`PhaseInfo` do not exist on the
module and that the deferral is documented in the module's own
docstring.

## 2. Registry Integration Summary

Every introspection function that needs live data takes a
`RuntimeRegistry` instance and reads it exclusively through its
already-frozen, already-verified public API (`registry_health()`,
`list_plugins()`, `list_capabilities()`, `find_capability()`) — no new
registry method is added, and no introspection function reaches into
`RuntimeRegistry._plugins` directly. `get_registry()` and `get_plugins()`
are proven, by direct equality tests, to produce *exactly* what
`registry.registry_health()`/`registry.list_plugins()` already produce
— no new computation is layered on top. `get_capabilities()` is the one
function that adds real logic: it enumerates the full ten-class frozen
capability taxonomy (110B §3), not only currently-declared capabilities,
pairing each with its declaring plugin IDs (via `find_capability()`)
and an `undeclarable` flag (`True` for exactly `execute`/`enforce`) —
tested directly to confirm those two capabilities can never have a
non-empty `declaring_plugin_ids`, since `register_metadata()` already
structurally prevents their registration (110E).

**Never loads, instantiates, invokes, or mutates.** A dedicated test
registers a plugin whose manifest smuggles in a callable "canary" that
raises `AssertionError` if ever called, then exercises every one of the
eight introspection functions against that registry — none raises,
proving none of them ever calls a manifest value. A separate test
confirms `register_metadata(` never appears anywhere in this module's
source. A before/after test confirms `registry.list_plugins()` is
identical before and after a full round of introspection calls.

## 3. Health/Status Snapshot Summary

`get_health()` composes `RuntimeRegistry.registry_health()` (110E/110F,
live) with this module's own static, frozen constants — `registry_status`,
`plugin_count`, `capability_count`, and `metadata_validity` come
straight from the registry snapshot; `execution_availability`
(`"unavailable"`), `current_runtime_state` (`"Observed"`), and
`current_maximum_plugin_capability` (`"observe"`) are frozen constants
this module reports but never computes or influences. `runtime_status`
honestly reports `"not_implemented"` rather than fabricating a
`"healthy"` claim about a Runtime that has no live instance to be
healthy or unhealthy about — a deliberate design choice, tested
directly.

`get_state()` returns `RuntimeStateInfo` restating 110A §8's eight-state
Runtime State Model verbatim (`Intent -> Observed -> Advisory ->
Approved -> Executable -> Executed -> Audited -> Rollback Ready`), with
`current_state` always `"Observed"` — proven by a direct doc-text
cross-check against `docs/PCAE_RUNTIME_ARCHITECTURE.md`, not just an
internal constant comparison.

## 4. Governance Snapshot Summary

`get_governance()` reads exactly two already-frozen, already-verified
sources: `permission_broker_foundation.IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE`
(108A, a plain string constant — never a live `PermissionBroker()`
construction or `.evaluate()` call, confirmed by a dedicated source-text
test) and `command_path_observation.INTEGRATION_REGISTRY`'s length
(109C, confirmed `4`). `non_executing_posture` is a static `True`;
`execution_capability` restates the same `"unavailable"` constant
`get_health()` uses, avoiding two independently-drifting sources of
truth for the same fact.

## 5. Read-Only / Immutability Guarantees

Every new dataclass (`RuntimeInfo`, `CapabilityInfo`, `HealthInfo`,
`VersionInfo`, `GovernanceInfo`, `RuntimeStateInfo`) is `frozen=True` —
confirmed directly by inspecting `__dataclass_params__.frozen` on each,
and by dedicated mutation-attempt tests that expect an exception.
`get_plugins()` returns 110F's already-hardened `PluginDescriptor`
instances, whose `manifest` field is a `MappingProxyType` snapshot
(110F) — a plugin returned by `get_plugins()` is immune to manifest
tampering by exactly the same guarantee 110F already proved, re-tested
here to confirm it transparently survives passing through this new
layer. A five-iteration repeated-call test confirms introspection
functions never accumulate state or drift between calls.

## 6. CLI Deferral (111C)

No `argparse` usage, no `add_parser` call, and no reference to
`runtime_introspection` or `runtime-inspect` appears anywhere in
`src/pcae/cli.py` — confirmed directly. This module's docstring states
the deferral explicitly: "planned for 111C (the `pcae runtime inspect`
command), not implemented here." No file under `src/pcae/commands/` was
added by this phase.

## 7. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This phase
implements 111A's already-frozen architecture; it introduces no new
principle, no new plugin category, and no change to the roadmap's
long-term vision or phase ordering. **No change to `docs/ROADMAP.md`
was needed or made**, matching every prior 110/111-series phase's own
evaluation outcome.

## Execution Integration Status

Unchanged from 111A — this phase adds a new core module but no new
command-path integration, no CLI wiring, and no execution capability:

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

- **Why this phase cannot introduce execution capability:** every
  introspection function either returns a static, frozen constant or
  reads an already-verified, non-executing source (`RuntimeRegistry`'s
  public API, `permission_broker_foundation`'s status constant,
  `command_path_observation`'s registry length) — none constructs a
  live `PermissionBroker`, none calls `observe()`, and none touches the
  filesystem, network, or a subprocess (all confirmed by dedicated
  source-text and AST-based import tests).
- **Why registry integration cannot silently become mutation:** every
  registry-reading function is proven, by direct equality assertions,
  to delegate to an already-frozen `RuntimeRegistry` method rather than
  reach into internal state; a before/after test and an
  adversarial-callable test both confirm no side effect occurs.
- **Why the read-only guarantee holds even for returned plugin data:**
  `PluginInfo` is a type alias of `PluginDescriptor`, inheriting 110F's
  manifest-immutability hardening automatically — this phase adds no
  new mutable-field risk, and a dedicated test confirms the hardening
  transparently applies to data returned through this new layer.
- **Why the CLI deferral is enforced, not just documented:** dedicated
  tests scan both this module's own source and `cli.py` for any
  `argparse`/`add_parser`/`runtime-inspect` trace — none exists.

## Limitations

- Three of 111A's eleven introspection objects (`SessionInfo`,
  `TaskInfo`, `PhaseInfo`) remain unimplemented, deliberately, for the
  reasons in §1 — a future phase would need to decide whether they
  belong in this module (reading `.pcae/` state directly) or in a
  thinner wrapper over the existing `pcae session`/`task`/`phase`
  commands.
- `get_capabilities()`'s `undeclarable` field is currently only ever
  `True` for `execute`/`enforce` — correct today, but if 110B §3's
  frozen ten-class taxonomy is ever extended by a future phase, this
  function's behavior (deriving `undeclarable` from
  `UNDECLARABLE_CAPABILITIES`, not a hardcoded pair) already
  generalizes correctly without modification.
- No CLI, REST, or web surface exists yet — 111C (recommended next
  phase) is scoped specifically to add `pcae runtime inspect` against
  this module's existing functions, without changing any of them.

## No-Go Confirmations

No CLI introspection command. No `pcae runtime inspect`. No REST
endpoint. No web UI. No daemon. No background worker. No plugin
loading. No plugin instantiation. No plugin invocation. No dependency
injection. No runtime execution. No command authorization. No command
denial. No behavior-changing integration. No shell mediation. No
backend invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No automatic apply. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision (this phase does not touch `permission_broker_foundation.py`
beyond reading one constant). Current maximum runtime state remains
`Observed` (110A §8, unchanged). Current maximum plugin capability
remains `observe` (110B §3, unchanged). `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/GitHub
Packages publication.

## Recommended Next Phase

**111C — Runtime Inspect CLI.**
