# PCAE Runtime Snapshot

**Frozen by**: Phase 112E | **Status**: observation-only integration —
no runtime execution, plugin loading, plugin instantiation, plugin
invocation, dependency injection, shell mediation, backend invocation,
adapter invocation, execution enablement, execution capability,
Permission Broker enforcement, audit persistence, rollback execution,
emergency stop, Telegram inbound, REST server, web UI, daemon,
background worker, or automatic apply is introduced by this document or
this phase.

## Purpose

Every prior 110/111/112-series phase built one layer of the Runtime's
read-only picture: what the Runtime can *do* (110A), what plugins and
capabilities *exist* (110B–111D), and what is *currently happening*
(112A–112D, Runtime Context). Until this phase, `pcae runtime inspect`
(111C) assembled its own view of the first two layers directly inside
the CLI command, and knew nothing at all about the third — Runtime
Context existed as a prototype (112C) with no consumer. This phase
introduces **Runtime Snapshot**: the single, canonical, read-only
composition of all of it, and makes `pcae runtime inspect` render that
one model instead of assembling its own.

## New Principle

```
Runtime Snapshot is the canonical read model.
```

Every prior principle in this arc answered "what can the Runtime do"
(110A), "what can the Runtime know" (110B–111D), or "what is the
Runtime doing" (112A–112D). This principle answers a different
question: **when something outside the Runtime asks "what is true right
now," there is exactly one model it should be given** — not a bespoke
assembly re-derived by whichever consumer happens to be asking. A CLI
command, a future REST endpoint, a future Telegram bot, a future
dashboard, and a future AI agent context pack should all render the
same Runtime Snapshot, never each independently re-deriving their own
partial view of the same underlying facts.

## 1. Runtime Snapshot, Defined

**Definition.** `RuntimeSnapshot` (`src/pcae/core/runtime_snapshot.py`)
is a single, immutable (frozen dataclass) composition of:

| Field | Source | Unchanged since |
|---|---|---|
| `runtime` | `RuntimeInfo` | 111B |
| `registry` | `RegistryInfo` | 111B (= 110E/110F's `RegistrySnapshot`) |
| `plugins` | `tuple[PluginInfo, ...]` | 111B (= 110E/110F's `PluginDescriptor`) |
| `capabilities` | `tuple[CapabilityInfo, ...]` | 111B |
| `health` | `HealthInfo` | 111B |
| `governance` | `GovernanceInfo` | 111B |
| `state` | `RuntimeStateInfo` | 111B |
| `version` | `VersionInfo` | 111B |
| `context` | `RuntimeContext \| None` | 112C, newly consumed here |

**Runtime Snapshot composes; it never re-derives.** Every field above
is either a direct delegation to a `pcae.core.runtime_introspection`
`get_*()` function 111B already froze (unchanged, no new logic), or a
`RuntimeContext` built by `build_runtime_context_from_repo()` (below).
No field on `RuntimeSnapshot` independently recomputes a value another
layer already owns — this is the same "surfaces facts, never decides"
discipline 110C §5 (Registry), 111A §1 (Introspection), and 112A §1
(Context) already established, applied a fourth time to the
composition layer itself.

## 2. Composition (Objective 2)

`build_runtime_snapshot(root, registry) -> RuntimeSnapshot` assembles
every field in one pass:

```
runtime      = get_runtime()                 # 111B, unchanged
registry     = get_registry(registry)        # 111B, unchanged
plugins      = get_plugins(registry)          # 111B, unchanged
capabilities = get_capabilities(registry)     # 111B, unchanged
health       = get_health(registry)           # 111B, unchanged
governance   = get_governance()               # 111B, unchanged
state        = get_state()                    # 111B, unchanged
version      = get_version(registry)          # 111B, unchanged
context      = build_runtime_context_from_repo(root)   # 112E, new
```

No duplication: `RuntimeSnapshot` does not redefine `plugin_count`
(already `health.plugin_count`), does not redefine `session_id`
(already `context.session.session_id`), and does not flatten any
composed object's fields into its own — it holds references, exactly
as 112C's own `RuntimeContext` holds references to `TaskContext`/
`ObservationContext` rather than flattening them.

## 3. Runtime Context Integration (Objective 4)

`build_runtime_context_from_repo(root)` is the one genuinely new piece
of logic this phase introduces: a read-only bridge between 112C's pure,
isolated `RuntimeContext` object model (which itself performs no I/O —
that isolation guarantee, verified by 112C/112D's own tests, is
unchanged and unrepeated here) and the real, already-governed repo
state every other PCAE command already reads.

It reads exactly two already-existing sources, through the exact same
helper functions `pcae session bootstrap` itself uses — no new I/O
capability, no new file format, no new parsing logic:

- `.pcae/session.json`, via `pcae.core.session.read_session_snapshot()`
  — supplies `session_id` (the session's own `timestamp` field, since,
  as 112B §2 already noted honestly, no explicit `session_id` field
  exists in the real file yet).
- `tasks/active/`, via `pcae.core.tasks.find_latest_active_task()` —
  supplies the active `TaskContext`, if one exists.

Populated, per 112E's objective 4:

| Concept | Populated? | Why |
|---|---|---|
| Runtime Session | Yes | Real `.pcae/session.json` state |
| Active Task | Yes, if one exists | Real `tasks/active/` state |
| Observation State | Yes, always | The four `INT-NNN` integrations are always consultable (112B §8's "Observation always available" invariant) — populated even when no task is active |
| Active Phase | No — always `null` | No real, governed phase-context source exists anywhere in this codebase |
| Intent | No — always `null` | `Intent Pipeline` remains not implemented (110A §2) |
| Approval | No — always `null` | `COMP-003` (Human Approval Gate) remains unimplemented |
| Broker Decision | No — always `null` | Would require wrapping a live `PermissionBrokerDecision`; this module never calls `PermissionBroker.evaluate()` |
| Evidence | No — always `null` | `COMP-007` (Audit Boundary) remains unimplemented |

The five `null` rows are reported explicitly, by name, in both JSON and
human-readable output — never silently omitted — so a consumer can see
exactly what Runtime Context will eventually report without mistaking
today's honest absence for a missing feature.

## 4. Relationship to Runtime Inspect (Objective 3)

`pcae runtime inspect` (111C) no longer assembles its own snapshot.
`commands/runtime_inspect.py`'s `_build_snapshot(registry)` — kept
under its original 111C name and single-argument signature for
backward compatibility with every existing call site — is now a
three-line delegation:

```python
def _build_snapshot(registry: RuntimeRegistry) -> dict:
    root = HarnessPath.cwd()
    snapshot = build_runtime_snapshot(root, registry)
    return snapshot_to_dict(snapshot)
```

All composition logic lives in `runtime_snapshot.py`; the CLI's own
job is limited to constructing a `RuntimeRegistry`, resolving the repo
root, and formatting the result — exactly the "avoid bespoke assembly
logic inside the CLI" objective 3 asked for.

## 5. Observation-Only Guarantees (Objective 5)

- **No broker evaluation.** `runtime_snapshot.py` imports nothing from
  `permission_broker_foundation`; `GovernanceInfo.broker_implementation_status`
  is read from an already-frozen constant, exactly as 111B does.
- **No execution.** No field, function, or code path in this module
  can run a command, invoke a plugin, or change Runtime state.
- **No plugin loading.** `runtime_snapshot.py` never imports a plugin-
  loading module and never calls `register_metadata()`.
- **No shell / backend invocation.** No `subprocess`, no
  `backend_invocations`, no network module anywhere in its import list.
- **No behavior change.** `build_runtime_context_from_repo()` performs
  reads only (`read_session_snapshot`, `find_latest_active_task`) —
  confirmed directly: constructing a full `RuntimeSnapshot` against a
  populated temporary repo leaves every file byte-for-byte unchanged.

## 6. Backward Compatibility (Objective 6)

`pcae runtime inspect`, `pcae runtime inspect --json`, and `pcae
runtime inspect --verbose` all continue to work exactly as 111C/111D
left them. The JSON schema gains exactly one new, additive top-level
key — `context` — every other key, and every existing key's own
section shape, is byte-for-byte unchanged (reconfirmed directly against
111D's own `STABLE_TOP_LEVEL_KEYS`/`STABLE_SECTION_KEYS` frozen
contract tests, deliberately updated to include the new key, not
silently loosened). The human-readable default output is completely
unchanged; the new "Runtime Context (112E):" section appears only in
`--verbose` output, alongside the existing verbose-only sections
(Plugin metadata, Capability declarations, Observation integrations,
Current limitations).

## 7. Current Limitations

- Active Phase, Intent, Approval, Broker Decision, and Evidence remain
  entirely unpopulated — honestly, not as a bug, since none has a real
  governed backing source anywhere in this codebase yet.
- `session_id` is derived from `.pcae/session.json`'s `timestamp`
  field, not a dedicated `session_id` field — 112B §2 already named
  this as the real file's current shape, not invented here.
- The "exactly one active Runtime Context" and "at most one active Task
  per Phase" invariants (112B §7) remain represented structurally
  (112C/112D) but unenforced by this integration.
- No REST endpoint, Telegram integration, web UI, or dashboard consumes
  `RuntimeSnapshot` yet — all are named below as intended future
  consumers, not implemented by this phase.

## 8. Future Consumers

`RuntimeSnapshot` is designed to be the single model every future
observation surface renders, not a CLI-specific structure:

- **CLI** (`pcae runtime inspect`) — implemented, this phase.
- **REST endpoint** — a future, explicitly out-of-scope phase (this
  phase's hard boundary forbids introducing one) would serve
  `snapshot_to_dict()`'s own JSON shape directly.
- **Telegram** — a future bot command could render the same
  human-readable formatting `_format_human()` already produces.
- **Dashboard** — a future web UI would consume the same JSON shape,
  unchanged.
- **AI agents** — a future bootstrap/context-pack phase could fold
  `RuntimeSnapshot` into the same compact context pack
  `pcae session bootstrap --compact` already assembles
  (`pcae.core.context.build_context_pack`), giving an agent one
  consistent view of "what is the Runtime doing" alongside the
  existing "what phase are we on" view.

## No-Go Confirmations

No runtime execution. No plugin loading. No plugin instantiation. No
plugin invocation. No dependency injection. No shell mediation. No
backend invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No REST server. No web UI. No daemon. No background worker.
No automatic apply. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed`. Current maximum plugin
capability remains `observe`. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**112F — Runtime Snapshot Contract Freeze.**
