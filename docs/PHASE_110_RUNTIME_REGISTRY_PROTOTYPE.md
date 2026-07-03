# Phase 110E — Runtime Registry Prototype (Observation-Only)

## Purpose

Implement the first passive Runtime Registry prototype: a plugin
metadata store that proves the Runtime can own, query, and validate
plugin metadata while preserving PCAE's complete non-executing
guarantees. **This is a passive metadata registry. No plugin loading.
No plugin instantiation. No plugin invocation. No execution.** Every
public method either reads or writes a plain, inert data record; none
of them imports, calls, or executes anything the stored metadata
describes.

This phase adds its own frozen addition to the roadmap ordering,
alongside 110C's "Discoverable always":

```
Metadata precedes behavior.
```

A plugin's existence is knowable, queryable, and validatable entirely
independent of any capability to run it. This prototype proves that
claim concretely — for the first time in the 110-series, this phase
adds real, testable code, and that code implements only the metadata
half.

## Scope

- `src/pcae/core/runtime_registry.py` — the implementation: frozen
  vocabularies restated from 110B/110C/110D, `PluginDescriptor` (an
  inert data record), `RuntimeRegistry` (a passive in-memory metadata
  store), `validate_descriptor()`, and three result/report data
  classes (`RegistrationResult`, `RegistrySnapshot`,
  `RegistryValidationReport`).
- `tests/test_runtime_registry_prototype.py` — 110 tests: functional
  coverage of every objective plus module-isolation tests (AST-based
  import allowlist, forbidden-call source scan) mirroring 108A's
  isolation guarantee for `permission_broker_foundation.py`.
- `docs/PHASE_110_RUNTIME_REGISTRY_PROTOTYPE.md` — this document.

No CLI command is added by this phase. 110E's brief explicitly permits
this ("Need not expose a CLI if out of scope, but the underlying
runtime data structures should support introspection") — `list_plugins()`,
`get_plugin_metadata()`, `list_capabilities()`, `find_capability()`,
and `registry_health()` together satisfy the introspection requirement
without touching `cli.py`, keeping this phase's changed-file footprint
to exactly one new core module and its test file. `docs/ROADMAP.md` was
evaluated for an update; see §7 below.

## 1. Registry Implementation Summary

`RuntimeRegistry` (`src/pcae/core/runtime_registry.py`) is a plain
Python class wrapping one private `dict[str, PluginDescriptor]`. Every
public method is a synchronous, in-process read or write against that
dict — no I/O, no subprocess, no network, no dynamic import. It is the
first concrete implementation in the 110-series (110A–110D were all
design/contract phases touching no file under `src/pcae/`), and it
implements exactly the boundary those four phases froze: the Registry
resolves (here: stores and surfaces) metadata; it does not orchestrate,
decide, approve, or execute — because it holds no capability to do any
of those things.

## 2. Metadata Model Summary

`PluginDescriptor` is a frozen dataclass with eight fields, each
corresponding to a 110B/110C contract field: `plugin_id`, `plugin_type`,
`version` (110B §1 fields 1, 2, 11), `capabilities` (field 8),
`lifecycle_state` (110B §4), `health_state` (surfaces field 10 as inert
data), `implementation_status` (field 18), and an open `manifest`
mapping for any of 110C §3's remaining manifest fields. Five frozen
vocabularies gate valid values: `PLUGIN_CATEGORIES` (10, from 110A
§3/110B §2), `LIFECYCLE_STATES` (8, from 110B §4), `CAPABILITY_CLASSES`
(10, from 110B §3), `IMPLEMENTATION_STATUSES` (3 — `implemented` is
deliberately never a member), and `HEALTH_STATES` (3, new to this
phase — `healthy`/`unhealthy`/`unknown`, since 110B never froze a
health-state vocabulary, only that a Health Reporting hook must exist).
`UNDECLARABLE_CAPABILITIES` (`enforce`, `execute`) is enforced as a
hard validation rejection, not just a data-hygiene check — this is the
one rule that exists specifically to preserve the execution-unavailable
guarantee at the metadata layer.

## 3. Registry API Summary

Five of 110D §2's nine canonical Registry API operations are
implemented, metadata-only:

| 110D operation | This phase's implementation |
|---|---|
| `RegisterPlugin()` | `register_metadata()` — fails closed (never raises); rejects a duplicate `plugin_id` or any `validate_descriptor()` issue without storing anything. |
| `ListPlugins()` | `list_plugins()` — every registered descriptor, in registration order. |
| `DiscoverCapabilities()` / `ListCapabilityProviders()` | `list_capabilities()` (deduplicated, sorted) and `find_capability()` (all declared providers of one capability, unfiltered). |
| `GetPluginMetadata()` | `get_plugin_metadata()` — a single descriptor or `None`. |

Four operations are deliberately **not** implemented this phase:
`UnregisterPlugin()` (no lifecycle-driving removal behavior is added —
tested directly: `RuntimeRegistry` has no `unregister_metadata`/
`unregister_plugin` method), `ResolveCapability()` (110D §4's outcome
semantics — `Resolved`/`MultipleCandidates`/`NoProvider`/etc. — require
Runtime-side selection behavior, not metadata storage; `find_capability()`
implements only the unfiltered `ListCapabilityProviders()` view),
`GetPluginHealth()` as a live signal (a descriptor's `health_state` is
accepted as inert, caller-supplied data — this module never computes
or polls it), and `ValidateCompatibility()` as a gating check (version-
format and manifest-consistency issues are *reported*, via
`validate_descriptor()`, never used to block anything beyond
registration admission itself).

## 4. Introspection Summary

`list_plugins()`, `get_plugin_metadata()`, `list_capabilities()`,
`find_capability()`, and `registry_health()` together give full
read-only visibility into everything the registry holds, without a CLI
command. `registry_health()` returns a `RegistrySnapshot` — registered
plugin count, registered capability count, registry status
(`empty`/`populated`), an aggregate `metadata_validity` signal, and the
full plugin-ID/capability lists — satisfying 110E objective 5's
metadata-only runtime health requirement. No field on `RegistrySnapshot`
reflects behavioral health (no `behavioral_health`, `live_status`, or
`execution_status` field exists — verified directly by a dedicated
test).

## 5. Validation Summary

`validate_descriptor()` is a pure function checking: non-empty
`plugin_id`; `plugin_type` in the ten frozen categories; `lifecycle_state`
in the eight frozen states; `health_state` in the three frozen states;
`implementation_status` in the three permitted values (never
`implemented`); `version` matching `MAJOR.MINOR.PATCH`; no duplicate
entries within one descriptor's own `capabilities` tuple; every
capability drawn from the frozen taxonomy, with `enforce`/`execute`
hard-rejected; and manifest/descriptor field agreement (`plugin_id`,
`plugin_type`, `version`, when present in the manifest, must match the
descriptor). The same function backs both `register_metadata()` (a
pre-store, fail-closed admission gate — nothing invalid is ever stored)
and `RuntimeRegistry.validate_consistency()` (a post-store, read-only
re-scan producing a `RegistryValidationReport`), so admission and
audit can never drift out of sync with each other. In normal operation
every field of `RegistryValidationReport` is empty — `register_metadata()`
already refuses anything that would appear there — and dedicated tests
prove this directly by attempting duplicate/invalid registrations and
confirming both that they are rejected and that `validate_consistency()`
independently confirms the registry stayed clean. This mirrors the
read-only re-verification pattern `pcae governance audit` already
applies elsewhere in this codebase: trust the admission gate, but make
the invariant independently checkable rather than merely assumed.

## 6. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. The
roadmap's Long-Term Runtime Vision (110B) already states "Pluggable
first. Connected second. Automated third. Executable last," and 110C
already covers "Discoverable always" where applicable. This phase's new
addition, "Metadata precedes behavior," is stated in this document (§
above) and in `PROJECT_STATUS.md`/`CHANGELOG.md` as this phase's frozen
principle — it does not change the roadmap's long-term vision or phase
ordering, matching 110C's and 110D's own evaluation outcome. **No
change to `docs/ROADMAP.md` was needed or made.**

## Execution Integration Status

Unchanged from 110D — this phase adds a new core module but no new
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

- **Why this phase cannot introduce execution capability, despite being
  the first 110-series phase to touch `src/pcae/`:** `RuntimeRegistry`
  and `PluginDescriptor` hold no callable, module reference, class
  reference, or import path anywhere in their fields or methods — a
  `PluginDescriptor` is eight plain values and a dict; nothing about
  either type allows turning stored metadata into a running plugin.
  Verified directly: dedicated tests assert neither class defines any
  `load`/`instantiate`/`invoke`/`call`/`execute`/`run` method.
- **Why registering `execute`/`enforce` capability metadata cannot grant
  execution capability:** `validate_descriptor()` hard-rejects both at
  the metadata layer — a descriptor declaring either is never stored,
  proven directly by a test that attempts registration and confirms
  both `accepted is False` and `find_capability("execute") == ()`.
- **Why the module's own source cannot silently gain a shell/backend/
  network dependency:** an AST-based import allowlist test restricts
  `runtime_registry.py` to four standard-library modules (`__future__`,
  `re`, `dataclasses`, `typing`); separate source-text scans confirm no
  `subprocess`, `os.system`, `eval`, `exec`, `__import__`, file I/O
  (`open`, `Path`, `os.remove`/`os.rename`, `shutil`), or network call
  (`socket`, `requests`, `urllib`, `http.client`) appears anywhere in
  the file — mirroring 108A's isolation guarantee for
  `permission_broker_foundation.py`.
- **Why omitting `UnregisterPlugin()`/`ResolveCapability()`/live
  `GetPluginHealth()`/gating `ValidateCompatibility()` is itself a
  safety property, not a gap:** each of the four would require either
  lifecycle-driving behavior (removal), Runtime-side selection behavior
  (resolution outcomes), live computation (health polling), or a
  gating decision (compatibility enforcement) — all behavior, not
  metadata. Implementing any of them this phase would blur "Metadata
  precedes behavior" into "metadata *is* behavior." Their absence is
  tested directly (`hasattr` checks) so the boundary is enforced by the
  test suite, not merely by omission in the source.

## Limitations

- The registry is in-memory only; nothing is persisted to `.pcae/` or
  anywhere else. A future phase adding durable storage would be new
  behavior (and would naturally belong to a Storage Plugin, 110A §3),
  explicitly out of scope here.
- No CLI command (`pcae runtime plugins` or similar) is added. The
  brief permits this explicitly; a future phase may wire one against
  the introspection methods already implemented here without changing
  this module.
- `find_capability()` returns every declared provider regardless of
  `lifecycle_state` or `health_state` — it is 110D §2's unfiltered
  `ListCapabilityProviders()` view, not the filtered `ResolveCapability()`
  view. A future phase implementing real resolution semantics would
  need to add filtering logic on top of, not instead of, this method.

## No-Go Confirmations

No plugin loading. No plugin instantiation. No plugin invocation. No
dependency injection. No runtime execution. No command authorization.
No command denial. No behavior-changing integration. No shell
mediation. No subprocess mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No
Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST server. No
web server. No daemon. No background workers. No automatic apply. No
command execution. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision (this
phase does not touch `permission_broker_foundation.py`). Current
maximum runtime state remains `Observed` (110A §8, unchanged). Current
maximum plugin capability remains `observe` (110B §3, unchanged).
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110F — Runtime Registry Verification & Compatibility.**
