# Phase 110F — Runtime Registry Verification & Compatibility

## Purpose

Verify and harden the passive Runtime Registry prototype (110E,
`src/pcae/core/runtime_registry.py`): prove it remains metadata-only,
non-executing, compatible with the 109A-109D observation integrations
and the 110A-110D runtime/plugin/registry architecture and contracts,
fails safe under every malformed/duplicate/unknown input, and exposes
enough read-only metadata for future introspection. **This is
verification/hardening only** — one narrow hardening fix is included
(§6 below); no new registry capability, plugin loading, instantiation,
invocation, or execution capability is added.

## Scope

- `src/pcae/core/runtime_registry.py` — one hardening change: see §6.
- `tests/test_runtime_registry_verification.py` — 68 new tests, the
  dedicated 110F verification suite, organized by objective:
  metadata-only boundary, hardening proof, contract compatibility,
  resolution semantics, fail-safe behavior, introspection readiness,
  and execution-unavailable reconfirmation.
- `tests/test_runtime_registry_prototype.py` — one-line update to the
  module-isolation stdlib allowlist (`types` added, for `MappingProxyType`).
- `docs/PHASE_110_RUNTIME_REGISTRY_VERIFICATION.md` — this document.

No CLI file, shell/backend/Telegram module, or any file outside the
above is touched. `docs/ROADMAP.md` was evaluated for an update; see
§8 below.

## 1. Metadata-Only Boundary Verification

Directly verified, beyond 110E's original coverage:

- Every `PluginDescriptor` field's declared type is plain data (`str`,
  `tuple[str, ...]`, `Mapping`) — none is `Callable`, a class, or a
  module-reference type (checked by inspecting
  `PluginDescriptor.__dataclass_fields__` directly, not just by
  reading the source).
- No field name on either class suggests a module/import-path/handler
  concept (`module`, `module_path`, `import_path`, `class_path`,
  `entry_point`, `callable`, `handler` all absent).
- A fresh `RuntimeRegistry` instance's own `__dict__` contains exactly
  one attribute (`_plugins`), and it is a plain `dict` — inspected on a
  live instance, not assumed from source.
- Every value ever stored in that dict is a `PluginDescriptor` and is
  not callable — checked after a real registration, not just by type
  annotation.
- No method name on `RuntimeRegistry` matches any load/instantiate/
  invoke vocabulary (`load*`, `instantiate*`, `invoke*`, `call_plugin`,
  `run_plugin`, `execute_plugin`, `dispatch`, etc.) — a `dir()`-based
  sweep, not a hand-picked list of methods to check.
- `find_capability()` results are `PluginDescriptor` instances, never
  callable, and `list_capabilities()` results are always plain `str`.

## 2. Contract Compatibility Verification

Cross-checked directly against the **live text** of the relevant docs
(not against this phase's own memory of what they say):

- All ten `PLUGIN_CATEGORIES` appear as `"<Category> Plugin"` headings
  in `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B).
- All eight `LIFECYCLE_STATES` and all ten `CAPABILITY_CLASSES` appear,
  backtick-quoted, in the same 110B document.
- All three `IMPLEMENTATION_STATUSES` appear, backtick-quoted, in the
  same document.
- The five 110D canonical API operation names this prototype claims to
  implement (`RegisterPlugin()`, `ListPlugins()`,
  `DiscoverCapabilities()`, `ListCapabilityProviders()`,
  `GetPluginMetadata()`) are confirmed present in both
  `docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md`'s live text and this
  module's own docstring — not just asserted by the module about
  itself.
- `docs/PCAE_RUNTIME_ARCHITECTURE.md`'s `Observed` runtime state is
  still present in its Runtime State Model section (110A §8).
- The 109C `INTEGRATION_REGISTRY` (`pcae.core.command_path_observation`)
  is confirmed unchanged: exactly four entries, IDs exactly
  `{INT-001, INT-002, INT-003, INT-004}` — this phase touches no
  command path and must not (and does not) alter it.
- `PermissionBroker().evaluate()` (108A) still returns
  `implementation_status == "execution_unavailable"` for a benign
  request, confirming this phase's addition has no observable effect
  on broker behavior.
- `runtime_registry.py` is confirmed, via AST-based import inspection
  (not substring search — see the note in §7), to import nothing
  containing `permission_broker`, `subprocess`, `shell_gate`,
  `backend_invocations`, `notifications`, `importlib`, or `socket`
  anywhere in its `import`/`from ... import` statements.
- No `INT-NNN` string or `observe()` call (the `command_path_observation`
  helper) appears anywhere in `runtime_registry.py` — confirming no new
  command-path integration was added.

## 3. Resolution Semantics Verification

Re-tested and extended beyond 110E's original coverage, in particular
around states 110E's suite did not exercise:

- Registered-capability lookup succeeds; missing-capability lookup
  returns `()`, never an error.
- Duplicate `plugin_id` is rejected outright (not merged, not
  overwritten) — the original registration's data is confirmed
  preserved.
- Duplicate capability *within one descriptor's own tuple* is
  rejected.
- Invalid descriptors (bad type/lifecycle/version) never raise.
- A manifest declaring a conflicting `version` is rejected
  (`manifest_version_mismatch`).
- **New this phase:** every one of the three `HEALTH_STATES`
  (`healthy`/`unhealthy`/`unknown`) and all eight `LIFECYCLE_STATES`
  (including `disabled`/`failed`/`retired`) are confirmed
  *registerable* — health/lifecycle are inert caller-supplied data,
  not a gate on registration.
- **New this phase:** `find_capability()` is confirmed to *not* filter
  by health or lifecycle state — an `unhealthy`/`failed` plugin's
  declared capability is still surfaced, since filtering would be
  `ResolveCapability()` behavior (110D §4), explicitly out of scope.
  This is a deliberate design confirmation, not a gap: 110E's docs
  already named this scope boundary; this phase makes it a directly
  tested, citable guarantee.
- The current maximum capability actually exercisable through this
  registry is reconfirmed `observe`-and-below only: attempting to
  register `execute` or `enforce` under any plugin ID fails, and after
  every such attempt `list_capabilities()` is confirmed empty.

## 4. Fail-Safe Behavior Verification

- An invalid descriptor never appears in `list_plugins()`.
- A sweep of seven distinct malformed-field descriptors (empty
  `plugin_id`, empty `plugin_type`, empty `lifecycle_state`, empty
  `health_state`, `implementation_status="implemented"`, empty
  `version`, an unknown capability) all reject via a returned result,
  never a raised exception — mirroring 108C's `_sanitize_result()`
  fail-closed-without-crashing pattern.
- **"No provider means no provider, not fallback execution":** an
  unresolved capability returns `()`, confirmed non-`None` and
  non-default.
- **"Multiple providers remain metadata candidates only":** two
  plugins declaring the same capability both appear in
  `find_capability()`'s result, and `RuntimeRegistry` is confirmed to
  have no `select_candidate`/`resolve_capability`/`choose_provider`
  method that could pick a winner.
- **"Registry unavailable cannot imply execution":** the closest this
  metadata-only prototype can represent "unavailable" is an empty,
  freshly constructed registry — confirmed to return `()`/empty for
  every query and expose no method whose behavior depends on
  population state.
- **"Unknown capability cannot imply execution":** four different
  unknown-capability strings (including an empty string and an
  uppercase variant) all return `()`.
- **"No descriptor can declare or enable execute/enforce capability in
  this phase":** re-confirmed both at the `validate_descriptor()` level
  and via `UNDECLARABLE_CAPABILITIES == frozenset({"execute", "enforce"})`.
- A systematic single-field-corruption sweep (eight distinct
  corruptions of an otherwise-valid descriptor, one field at a time)
  confirms every corruption rejects — fail-safe direction is always
  toward rejection, never silent correction or acceptance with a
  defaulted value.

## 5. Introspection Readiness Verification

Confirmed the registry exposes every metadata surface 110E objective 5
and this phase's objective 5 require, without a CLI:

- Registered plugin count and full capability list, via
  `registry_health()`.
- Full plugin metadata (`plugin_id`, `plugin_type`, `version`, etc.),
  via `get_plugin_metadata()`.
- Health and lifecycle status, via the same method — both fields are
  directly readable on the returned descriptor.
- Validation status, via both `registry_health().metadata_validity` and
  `validate_consistency().consistent`.
- **Confirmed no CLI was added:** neither `argparse` nor `add_parser`
  appears anywhere in `runtime_registry.py` — this phase's task
  contract does not include `cli.py`, and the source itself carries no
  trace of command-line wiring.

## 6. Hardening: Manifest Immutability

One genuine hardening finding, within the "verification/hardening
only" boundary this phase permits. `@dataclass(frozen=True)` on
`PluginDescriptor` prevents *reassigning* `descriptor.manifest`, but
before this phase, the `dict` object that field pointed at remained
independently mutable and was the *same object* a caller's own
manifest reference pointed at — an aliasing gap. A caller could
construct a descriptor, register it, then mutate their original
manifest dict and silently change what the registry reports having
stored, undermining the "metadata is inert, immutable data" claim this
whole module rests on.

**Fix:** `PluginDescriptor.__post_init__` now converts `manifest` into
a `MappingProxyType` wrapping a shallow copy of whatever was passed in
(`object.__setattr__` is used to set it, the one sanctioned way to
initialize a field post-construction on a frozen dataclass). This
closes the gap in both directions: `descriptor.manifest[...] = ...`
now raises `TypeError`, and mutating the caller's original dict after
construction has no effect on the stored descriptor — both proven
directly by dedicated tests, including one that registers a descriptor
and then confirms a post-registration mutation of the original dict
does not alter what `get_plugin_metadata()` returns.

This is a shallow copy, not a deep copy: a manifest value that is
itself a mutable container (e.g. a list) is not independently frozen.
This is a deliberate, documented limitation (§9) rather than an
oversight — a deep copy could fail on non-copyable objects (the
adversarial "manifest smuggles in a callable" test in §1 depends on
being able to store an arbitrary object unmodified), and 110D's
compatibility-dimension concerns are about scalar field agreement
(`plugin_id`/`plugin_type`/`version`), not nested-structure integrity.

The `types` module (for `MappingProxyType`) is now part of this
module's stdlib import allowlist, updated in
`tests/test_runtime_registry_prototype.py`'s isolation test alongside
this change.

## 7. A Testing Gotcha Found and Fixed During This Phase

An early draft of two isolation tests in this phase's own suite
(`test_runtime_registry_module_never_imports_permission_broker`,
`test_runtime_registry_module_has_no_new_execution_adjacent_imports`)
used a naive `"permission_broker" not in text` / `"subprocess" not in
text` substring check against the module's raw source. Both false-
positived: `runtime_registry.py`'s own docstring *names* these
forbidden dependencies to explain that it has none of them (the same
prose pattern 108A's module docstring uses). Fixed by switching both
tests to AST-based import inspection (`ast.parse` + walking
`Import`/`ImportFrom` nodes), the same technique 110E's own isolation
suite already used correctly — checking actual import statements, not
raw text, avoids false positives from documentation prose. Noted here
as a reusable lesson for any future phase writing this style of
isolation test.

## 8. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This
phase adds no new principle, no new plugin category, and no change to
the roadmap's long-term vision or phase ordering — it is a
verification/hardening phase confirming an existing implementation's
guarantees, not introducing new architecture. **No change to
`docs/ROADMAP.md` was needed or made**, matching 110C's/110D's/110E's
own evaluation outcome.

## Execution Integration Status

Unchanged from 110E:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Remaining Limitations

- Manifest immutability (§6) is shallow, not deep — nested mutable
  values inside a manifest are not independently frozen. Deliberate,
  not an oversight (see §6 for rationale).
- This phase verifies the *existing* prototype's guarantees; it does
  not add new Registry API operations, CLI introspection, persistence,
  or resolution/selection behavior. Those remain out of scope for the
  reasons 110D/110E already documented (Runtime-side behavior, not
  metadata).
- Compatibility verification is textual/structural (cross-checking
  live doc text and live module behavior) — it does not, and cannot,
  verify compatibility against a Runtime implementation, since none
  exists yet.

## No-Go Confirmations

No plugin loading. No plugin instantiation. No plugin invocation. No
callable references. No module references. No import path references.
No dependency injection. No runtime execution. No command
authorization. No command denial. No behavior-changing integration. No
shell mediation. No subprocess mediation. No backend invocation. No
adapter invocation. No execution enablement. No execution capability.
No Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST server. No
web server. No daemon. No background workers. No automatic apply. No
command execution. No runtime context implementation.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision (reconfirmed directly by this
phase's own test, §2). Current maximum runtime state remains `Observed`
(110A §8, unchanged). Current maximum plugin capability remains
`observe` (110B §3, unchanged). `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**111A — Runtime Introspection Architecture.**
