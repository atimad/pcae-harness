# Phase 111C — Runtime Inspect CLI

## Purpose

Add the first official Runtime CLI inspection command, `pcae runtime
inspect`, exposing 111B's observation-only Runtime Introspection model
as a safe, read-only operational snapshot. **This phase exposes
read-only runtime introspection through CLI only** — no runtime
behavior change, no plugin loading/instantiation/invocation, no
Permission Broker evaluation, no execution capability.

## Scope

- `src/pcae/commands/runtime_inspect.py` — the command implementation:
  snapshot assembly (`_build_snapshot()`), human-readable formatting
  (`_format_human()`), and the CLI handler (`run_runtime_inspect()`).
- `src/pcae/cli.py` — one new import line and one new subparser
  (`runtime inspect`, sibling to the existing `runtime snapshot`
  subcommand) with `--json` and `--verbose` flags.
- `tests/test_runtime_inspect_cli.py` — 46 tests covering command
  existence, human/JSON/verbose output content, safety behavior, and
  compatibility with 109C/110E/110F/111B.
- `docs/PHASE_111_RUNTIME_INSPECT_CLI.md` — this document.

No file under `src/pcae/core/runtime_introspection.py` (111B) is
touched — this phase adds a display layer on top of it, unmodified.
`docs/ROADMAP.md` was evaluated for an update; see §7 below.

## 1. CLI Implementation Summary

`pcae runtime inspect` is a new sibling subcommand under the existing
`runtime` command group (alongside the pre-existing `runtime snapshot`
family). The handler, `run_runtime_inspect()`, constructs exactly one
fresh, empty `RuntimeRegistry()` per invocation — there is no
persisted or process-shared registry anywhere in this codebase today
(110E's own documented limitation: "in-memory only for this phase") —
and calls every one of 111B's eight `get_*()` introspection functions
against it, then formats the combined result as either human-readable
text (default) or JSON (`--json`). `--verbose` adds four additional
sections to the human-readable output without changing what data is
computed. An empty registry (zero plugins, zero declared capabilities)
is therefore the honest, correct report every single invocation
produces — not a bug, not a placeholder, and documented explicitly in
both the module docstring and this document.

## 2. Human Output Summary

Default (non-verbose) output is eleven labeled lines, not a raw
`dict`/`repr()` dump: Runtime status, Runtime state, Execution
capability, Maximum plugin capability, Registry status, Plugin count,
Capability count, Observation integrations (count), Permission Broker
status, Governance posture, and Runtime principles (count + names).
`--verbose` adds four further sections: full plugin metadata (or `(none
registered)`), all ten capability classes with their declaring plugins
and an `[undeclarable]` marker for `execute`/`enforce`, the four
`INT-NNN` observation integration entries (109C, read directly from
`command_path_observation.INTEGRATION_REGISTRY`), and a "Current
limitations" section naming the registry's in-memory-only nature, the
three deferred 111B objects, and the absence of any plugin loading/
instantiation/invocation capability anywhere in this codebase.

## 3. JSON Output Summary

`pcae runtime inspect --json` prints one JSON object with eight
top-level keys — `runtime`, `registry`, `plugins`, `capabilities`,
`health`, `governance`, `state`, `version` — each a direct
serialization of the corresponding 111B introspection object's fields.
Output is stable and deterministic across invocations (no timestamps,
no random ordering, no wall-clock-dependent field) — verified directly
by a test asserting two consecutive invocations produce byte-identical
output. `PluginDescriptor.manifest` (an open, untyped field per
110E/110F) is **deliberately excluded** from every plugin entry in
`plugins` — confirmed directly by a test that registers a plugin with a
manifest containing an obviously-sensitive-looking key and asserts it
never appears anywhere in the serialized snapshot.

## 4. Verbose Output

Implemented, not deferred — `--verbose` was straightforward given
111B's `get_plugins()`/`get_capabilities()` already return everything
needed. It affects only human-readable formatting; `--json --verbose`
together still produce the same valid, unaffected JSON output
`--json` alone would (tested directly).

## 5. Safety Verification

Directly proven, by dedicated tests:

- **Does not mutate:** `_build_snapshot()` called twice against the
  same `RuntimeRegistry` produces identical results, and the
  registry's own `registry_health()` is unchanged before/after.
- **Does not call `PermissionBroker.evaluate()`:** an AST-based test
  walks every `ast.Call` node in the command module's source and
  confirms no call resolves to `PermissionBroker` or `evaluate` — a
  precise check, not a fragile substring search (the module's own
  docstring legitimately *names* `PermissionBroker.evaluate()` in
  prose to explain what this command deliberately never does, which a
  naive substring check would false-positive on).
- **Does not load/instantiate/invoke a plugin:** confirmed absent from
  source (`load_plugin(`, `instantiate_plugin(`, `invoke_plugin(`,
  `register_metadata(`), and confirmed live — the JSON output's
  `plugins` array is always empty and `registered_plugin_count` is
  always `0`.
- **No network calls, no subprocess, no file writes:** confirmed
  absent from source (`subprocess.`, `socket.`, `requests.`,
  `urllib.`, `os.system(`, `open(`, `shutil.`, etc.).
- **No secrets/credentials/environment variables:** confirmed absent
  from source (`os.environ`, `os.getenv`) and confirmed absent from
  live JSON output (a case-insensitive scan for `token`, `secret`,
  `credential`, `password`, `api_key`).
- **Module import isolation:** an AST-based allowlist restricts
  `runtime_inspect.py` to `__future__`, `argparse`, `json`, and three
  already-frozen, already-non-executing internal modules
  (`pcae.core.command_path_observation`, `pcae.core.runtime_introspection`,
  `pcae.core.runtime_registry`) — no `permission_broker`, `shell_gate`,
  `subprocess`, `backend_invocations`, `notifications`, `telegram`, or
  `importlib` dependency anywhere.

## 6. Compatibility Verification

- `runtime_introspection.py` (111B) is unmodified — confirmed both by
  this phase's task contract (which does not list it as an allowed
  file) and by a test asserting every `get_*()` function still exists
  with its original, minimal signature.
- `runtime_registry.py` (110E/110F) remains metadata-only — confirmed
  by inspecting a fresh `RuntimeRegistry`'s own `__dict__` after this
  command's snapshot assembly runs against it (still exactly one
  attribute, `_plugins`).
- `command_path_observation.py` (109C) still has exactly four `INT-NNN`
  entries — reconfirmed directly.
- Permission Broker decisions remain `execution_unavailable` — a live
  `PermissionBroker().evaluate()` call (unrelated to this command,
  exercising 108A directly) reconfirms this independent of anything
  this phase added.
- Existing lifecycle commands (`pcae health`, `pcae check`) still run
  to completion and still produce their own expected output — verified
  directly. (Their specific exit codes are not asserted, since those
  legitimately depend on unrelated live governance/doc-sync state this
  phase has no bearing on, not on this phase's own correctness.)

## 7. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This
phase adds one CLI command exposing already-frozen (111A) and
already-implemented (111B) material; it introduces no new principle
and no change to the roadmap's long-term vision or phase ordering. **No
change to `docs/ROADMAP.md` was needed or made**, matching every prior
110/111-series phase's own evaluation outcome.

## Execution Integration Status

Unchanged from 111B — this phase adds a CLI command but no
command-path *observation* integration (this command is a display
command, not one of the four `INT-NNN`-observed paths), no execution
capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Non-Goals (This Phase)

- No REST endpoint, web UI, daemon, or background worker.
- No persistence — the registry this command inspects is always
  freshly constructed and always empty; a future phase adding durable
  registry storage would change what this command reports, but this
  phase does not add that storage.
- No `SessionInfo`/`TaskInfo`/`PhaseInfo` exposure (111B's own
  deferral, unchanged here).
- No `--verbose` gating, filtering, or pagination — the current
  verbose output is complete and unconditional; a future phase could
  add finer-grained flags if the output ever grows unwieldy.
- No command-path observation integration for `pcae runtime inspect`
  itself — it was not added to `INTEGRATION_REGISTRY` (109C), since
  doing so is out of this phase's scope and not requested by the brief.

## No-Go Confirmations

No runtime behavior changes. No plugin loading. No plugin
instantiation. No plugin invocation. No dependency injection. No
runtime execution. No command authorization. No command denial. No
behavior-changing integration. No shell mediation. No backend
invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No REST endpoint. No web UI. No daemon. No background worker.
No automatic apply. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision (this
phase's own command never constructs or evaluates a broker). Current
maximum runtime state remains `Observed` (110A §8, unchanged). Current
maximum plugin capability remains `observe` (110B §3, unchanged).
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**111D — Runtime Inspect CLI Verification & Compatibility.**
