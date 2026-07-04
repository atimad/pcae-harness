# PCAE Runtime Snapshot Contract

**Frozen by**: Phase 112F | **Status**: contract/freeze only — no
runtime behavior changes, no advisory decision behavior, no command
authorization, no command denial, no Permission Broker enforcement, no
plugin loading, no plugin instantiation, no plugin invocation, no
dependency injection, no shell mediation, no backend invocation, no
adapter invocation, no execution enablement, no execution capability,
no audit persistence, no rollback execution, no emergency stop, no
Telegram inbound, no REST server, no web UI, no daemon, no background
worker, no automatic apply is performed by this document or this
phase.

## Purpose

112E introduced Runtime Snapshot and made `pcae runtime inspect` render
it, but froze no contract for it — nothing yet said which keys are
guaranteed stable, how a future consumer should react to an unknown
key, what "additive" means precisely, or what Runtime Snapshot must
never expose. Before any Advisory Runtime work begins (113A), this
document freezes that contract: Runtime Snapshot as PCAE's stable,
canonical, read-only interface — for humans, the CLI, and every future
consumer named in §6 — with an explicit schema, compatibility rules,
versioning rules, and security rules. This document changes no source
file; every schema domain and key named below is transcribed directly
from the real, already-shipped 112E implementation
(`src/pcae/core/runtime_snapshot.py`,
`src/pcae/commands/runtime_inspect.py`), not invented.

## 1. Runtime Snapshot as Canonical Read-Only Interface

**Frozen scope.** Runtime Snapshot is PCAE's single, canonical,
read-only operational interface — the one model every consumer of
"what is the Runtime doing right now" renders, rather than each
independently re-deriving its own partial view (112E's own principle,
restated here as a frozen contract rather than a design intent):

- **Humans** — via `pcae runtime inspect`'s human-readable output.
- **CLI** — the only implemented consumer today (111C/112E).
- **Future AI agents** — a future context-pack phase could fold
  Runtime Snapshot into `pcae session bootstrap --compact`'s own
  compact prompt, giving an agent one consistent view of "what is the
  Runtime doing" alongside the existing "what phase are we on" view.
- **Future Telegram integration** — a future bot command could render
  the same human-readable formatting `_format_human()` already
  produces, or the JSON shape directly.
- **Future REST API** — a future endpoint would serve
  `snapshot_to_dict()`'s own JSON shape, unchanged, not a bespoke
  re-derivation.
- **Future dashboard/UI** — would consume the same JSON shape.
- **Future automation** — any future governed automation that needs
  "what is currently true about the Runtime" reads Runtime Snapshot,
  never re-implements its own assembly (112E objective 3's "avoid
  bespoke assembly logic," generalized here to every future consumer,
  not just the CLI).

**What this contract does not do.** It does not build any of the six
future consumers above — none is implemented by this phase, and this
phase's hard boundary explicitly forbids introducing a REST server, a
web UI, a daemon, or Telegram inbound. It freezes the interface those
future phases must target, before any of them exist.

## 2. Snapshot Schema (Objective 2)

**Required top-level domains, frozen exactly as 112E already
implemented them** (`snapshot_to_dict()`,
`src/pcae/core/runtime_snapshot.py`):

| Domain | Required | Shape | Source |
|---|---|---|---|
| `runtime` | Yes | object | `RuntimeInfo` (111B) |
| `registry` | Yes | object | `RegistryInfo` (111B / 110E-110F `RegistrySnapshot`) |
| `plugins` | Yes | array of objects | `tuple[PluginInfo, ...]` (111B / 110E-110F `PluginDescriptor`) |
| `capabilities` | Yes | array of objects | `tuple[CapabilityInfo, ...]` (111B) |
| `health` | Yes | object | `HealthInfo` (111B) |
| `governance` | Yes | object | `GovernanceInfo` (111B) |
| `state` | Yes | object | `RuntimeStateInfo` (111B) |
| `version` | Yes | object | `VersionInfo` (111B) |
| `context` | Yes (value may be `null`) | object or `null` | `RuntimeContext \| None` (112C/112E) |

**Correction against the brief's suggested list, per this document's
own "use the actual 112E implementation as source of truth"
instruction:** the brief's suggested domain list named "principles or
maturity" as a possible tenth top-level domain. The real
implementation does not have one — `principles` is, and remains, a
field *inside* `runtime` (`runtime.principles`, eleven frozen Runtime
Principles, 110A §6), not an independent top-level domain. No
"maturity" domain exists anywhere in 112E. This document freezes the
schema as it actually is (nine domains), not as the brief speculated it
might be — inventing a tenth domain here would be exactly the kind of
undocumented schema change §3 below forbids.

**Frozen per-domain shape** (field sets, transcribed from
`snapshot_to_dict()`):

- `runtime`: `pipeline_stages`, `principles`, `runtime_services`.
- `registry`: `registered_plugin_count`, `registered_capability_count`,
  `registry_status`, `metadata_validity`, `plugin_ids`, `capabilities`.
- `plugins[]`: `plugin_id`, `plugin_type`, `version`, `capabilities`,
  `lifecycle_state`, `health_state`, `implementation_status`.
  `manifest` is permanently excluded (§7).
- `capabilities[]`: `capability`, `declaring_plugin_ids`, `undeclarable`.
- `health`: `runtime_status`, `registry_status`, `plugin_count`,
  `capability_count`, `metadata_validity`, `execution_availability`,
  `current_runtime_state`, `current_maximum_plugin_capability`.
- `governance`: `non_executing_posture`, `broker_implementation_status`,
  `observed_command_paths`, `execution_capability`.
- `state`: `current_state`, `state_model`.
- `version`: `release_version`, `plugin_versions`.
- `context`: `session_id`, `lifecycle_stage`, `active_tasks`,
  `active_phase`, `intent`, `approval`, `broker_decision`, `evidence`,
  `observation`. May be `null` (no session state observed).

## 3. JSON Compatibility Rules (Objective 3)

Frozen, unconditionally, for every future change to Runtime Snapshot's
JSON output:

1. **Stable top-level keys.** The nine keys in §2's table are stable.
   None may be removed or renamed without a schema major version bump
   (§4).
2. **Additive-only changes within the same schema major version.** A
   new top-level key, or a new field within an existing domain, may be
   added within the same major version — exactly as 112E itself added
   `context` as a new, additive top-level key without bumping anything,
   since no version field existed yet (§4 resolves this going forward).
3. **Removal or rename requires a schema major version bump.** Removing
   a key, renaming a key, or changing an existing field's *meaning*
   (not just adding a sibling field) is a breaking change and requires
   the major version (§4) to increment.
4. **Consumers must ignore unknown keys.** Every future consumer named
   in §1 must be written to tolerate additional top-level keys or
   additional per-domain fields appearing in a later, compatible
   schema version — never to fail closed on an unrecognized key.
   (Failing closed on a *missing required* key remains correct and
   expected; this rule is specifically about *extra*, unrecognized
   keys.)
5. **No secrets or credentials** (§7).
6. **No execution handles** (§7).
7. **No mutable internal references** (§7) — every value in the
   snapshot must be a plain, JSON-serializable scalar, list, or dict;
   never a live reference to a `RuntimeRegistry`'s internal state, a
   `PluginDescriptor.manifest`, or any object a caller could mutate to
   affect the Runtime.

## 4. Snapshot Versioning (Objective 4)

**Decision: no `snapshot_schema_version` field is added by this
phase.** This is a contract/freeze phase — its hard boundary is "no
runtime behavior changes," and 112B, 112D, and every prior pure
contract-freeze phase in this arc touched no file under `src/pcae/`.
Adding a field to the real JSON output, however small, is a behavior
change to a shipped, backward-compatibility-tested interface (112E's
own `STABLE_TOP_LEVEL_KEYS` test), and belongs to a future
*implementation* phase that can carry its own governed task contract,
tests, and backward-compatibility verification — not folded silently
into a freeze phase's own scope. This is a deliberate decision, named
explicitly (matching this arc's established discipline of naming a
choice rather than silently picking one), not an oversight: the
alternative — implementing the field now — was considered and rejected
specifically because a freeze phase changing shipped behavior would
contradict its own hard boundary.

**The versioning contract, frozen for the field a future phase will
add:**

- **Field name:** `snapshot_schema_version` (a new top-level key,
  additive per §3 rule 2).
- **Format:** a single integer major version, starting at `1` — the
  schema as of 112E/112F (nine domains, §2) is retroactively defined as
  schema version `1`. No minor/patch component: within-major-version
  changes are, by rule 2, always additive and never require a consumer
  to branch on anything finer than the major version.
- **Compatibility rule:** a consumer reading `snapshot_schema_version
  == 1` may rely on every key and shape frozen in §2 being present;
  any additional keys it doesn't recognize must be ignored (§3 rule 4).
- **Deprecation rule:** no domain or field is deprecated by this
  document. A future phase introducing a deprecation must name the
  deprecated field explicitly in this document's own future revision,
  state the version it will be removed in, and bump the major version
  only at actual removal, never at deprecation-announcement time.
- **Migration expectation:** a future major-version bump must ship
  alongside a migration note in this document naming exactly which
  keys changed meaning or were removed, mirroring how this document
  itself names 112E's own JSON shape as schema version 1's frozen
  baseline.
- **Future version bump rule:** only §3 rule 3's conditions (removal,
  rename, meaning change) may trigger a major version bump. Adding a
  key, adding a field, or populating a previously-always-`null` field
  with real data (e.g. `context.active_phase` once a real phase-context
  source exists) is never, by itself, a breaking change and never
  triggers a bump.

## 5. Human Output Compatibility (Objective 5)

- **JSON is the machine contract; human-readable output is stable but
  less strict.** Every rule in §3 applies to `--json` output
  unconditionally. The default (non-JSON, non-verbose) human-readable
  output is stable in *content* (the same eleven labelled fields 111C
  already froze: `Runtime status`, `Runtime state`, `Execution
  capability`, `Maximum plugin capability`, `Registry status`, `Plugin
  count`, `Capability count`, `Observation integrations`, `Permission
  Broker status`, `Governance posture`, `Runtime principles`) but not
  in exact formatting — spacing, wording, and section ordering may
  change without a schema version bump, since no consumer should be
  machine-parsing human-readable text.
- **Default output remains concise.** The default (non-verbose) output
  shows only the eleven fields above — no plugin list, no capability
  declarations, no Runtime Context detail, no limitations list. This
  is frozen: a future phase may not silently expand the default output
  with new sections; new detail belongs in `--verbose`.
- **Verbose output may expose more read-only metadata.** `--verbose`
  today additionally shows Plugin metadata, Capability declarations,
  Observation integrations, the Runtime Context section (112E), and
  Current limitations — all read-only, none executable. A future phase
  may add further verbose-only sections without a schema version bump,
  since verbose output was never claimed stable in exact shape, only
  in remaining read-only and non-executable.

## 6. Future Consumers (Objective 6, Detailed)

No implementation is added for any of these — each is named so a
future phase has a frozen target to build against, exactly as 112A
named `ExecutionContext` as a stub before any execution capability
existed:

- **CLI** — implemented (111C, integrated 112E). The reference
  consumer every other consumer's contract is checked against.
- **Telegram** — a future outbound-only extension (Telegram inbound
  remains, unconditionally, out of scope for this entire arc) could
  send `_format_human()`'s own text via the existing outbound
  notification sinks (`pcae notify`), or the JSON shape as an
  attachment — no new formatting logic, reusing what §5 already froze.
- **REST** — a future read-only endpoint would serve
  `snapshot_to_dict()`'s JSON directly, subject unconditionally to
  every rule in §3 and §7; this phase's hard boundary forbids
  introducing the endpoint itself.
- **Web UI / dashboard** — a future consumer of the same JSON shape;
  no new schema, no new backend logic, purely a rendering layer.
- **AI agents** — a future bootstrap/context-pack integration
  (`pcae.core.context.build_context_pack`) could fold Runtime Snapshot
  into the compact bootstrap prompt already assembled for
  `pcae session bootstrap --compact`, giving an agent one further
  domain of already-governed context.
- **Audit/reporting** — a future phase could persist periodic Runtime
  Snapshots as an audit trail once `COMP-007` (Audit Boundary) exists —
  today, no snapshot is ever persisted (112E, unchanged; `context`
  itself explicitly excludes any `EvidenceContext`, per 112C/112D).
- **Advisory Runtime** (113A, this phase's own recommended next phase)
  — a future Decision Pipeline stage could read Runtime Snapshot as
  read-only input to an advisory recommendation, never write to it,
  and never let a recommendation appear to be an authorization (110A
  §6's "Human-controlled" principle, unchanged).

## 7. Security Rules (Objective 7)

Runtime Snapshot must never expose, in any output mode, any of the
following — frozen as an absolute, not a best-effort:

| Forbidden | Status today | Enforcement |
|---|---|---|
| Secrets | Never exposed | No field name or value sourced from any secret store; verified directly, `tests/test_runtime_snapshot.py`/`tests/test_runtime_inspect_cli.py`. |
| Tokens | Never exposed | Same. |
| Credentials | Never exposed | Same. |
| Environment variables | Never read | `runtime_snapshot.py`/`commands/runtime_inspect.py` contain no `os.environ`/`os.getenv` reference (verified). |
| Execution handles | Never exposed | No field is ever a callable, a subprocess handle, or a plugin instance — every value is a plain scalar/list/dict (§3 rule 7). |
| Plugin instances | Never exposed | `PluginInfo` is metadata only (110B §1); no live plugin object exists anywhere in this codebase to expose. |
| Callable references | Never exposed | Verified adversarially (111B/111C/112E): a `manifest` containing an exploding callable is confirmed never invoked and never serialized. |
| Module/import paths | Never exposed | No field carries a Python import path, file path, or module reference. |
| Mutable internal objects | Never exposed | `registry`'s section is confirmed, directly, to never contain the live `RuntimeRegistry._plugins` dict itself (111D). |
| Approval bypasses | N/A — nothing to bypass | `COMP-003` does not exist; `context.approval` is always `null`; no field could ever represent an approval outcome, real or bypassed. |

`manifest` (`PluginDescriptor`'s own open, untyped field, 110E) is
permanently excluded from every output mode — not merely "not yet
included" — since it is caller-supplied and could contain any of the
above.

## 8. Current Capability Limits (Objective 8)

Restated, unconditionally, as this document's own frozen baseline:

- **Runtime state remains `Observed`** (110A §8). `state.current_state`
  and `health.current_runtime_state` are both, unconditionally,
  `"Observed"`.
- **Maximum plugin capability remains `observe`** (110B §3).
  `health.current_maximum_plugin_capability` is unconditionally
  `"observe"`.
- **Execution capability remains unavailable.**
  `health.execution_availability` and `governance.execution_capability`
  are both, unconditionally, `"unavailable"`.
- **Advisory mode is not implemented.** No Decision Pipeline stage
  reads Runtime Snapshot today; `governance.broker_implementation_status`
  is unconditionally `"execution_unavailable"`.
- **Approval mode is not implemented.** `context.approval` is
  unconditionally `null`; `COMP-003` does not exist.
- **Enforcement is not implemented.** No field in Runtime Snapshot can
  cause a command to be authorized or denied; `pcae runtime inspect`
  remains, unconditionally, read-only.

## No-Go Confirmations

No runtime execution. No advisory decision behavior. No command
authorization. No command denial. No Permission Broker enforcement. No
plugin loading. No plugin instantiation. No plugin invocation. No
dependency injection. No shell mediation. No backend invocation. No
adapter invocation. No execution enablement. No execution capability.
No audit persistence. No rollback execution. No emergency stop. No
Telegram inbound. No REST server. No web UI. No daemon. No background
worker. No automatic apply. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision. Current maximum runtime state remains `Observed`. Current
maximum plugin capability remains `observe`. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/
GitHub Packages publication.

## Recommended Next Phase

**113A — Advisory Runtime Architecture.**
