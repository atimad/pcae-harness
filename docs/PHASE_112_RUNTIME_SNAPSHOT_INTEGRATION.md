# Phase 112E — Runtime Snapshot & Runtime Inspect Context Integration

## Purpose

Integrate Runtime Context (112C/112D) into the Runtime Inspect
subsystem by introducing the canonical Runtime Snapshot model. Runtime
Snapshot becomes the Runtime's single read-only operational
representation; `pcae runtime inspect` renders it instead of assembling
its own view. Observation-only integration phase — no execution
capability.

## Scope

- `src/pcae/core/runtime_snapshot.py` — new module: `RuntimeSnapshot`
  (composes 111B's eight Introspection objects, unchanged, with 112C's
  `RuntimeContext`), `build_runtime_context_from_repo()` (read-only
  bridge from real repo state to a `RuntimeContext`),
  `build_runtime_snapshot()`, `snapshot_to_dict()`.
- `src/pcae/commands/runtime_inspect.py` — refactored: `_build_snapshot()`
  is now a three-line delegation to Runtime Snapshot (kept under its
  original 111C name/signature for backward compatibility); `_format_human()`
  gained one new verbose-only "Runtime Context (112E):" section.
- `docs/PCAE_RUNTIME_SNAPSHOT.md` — the architecture document.
- `docs/PHASE_112_RUNTIME_SNAPSHOT_INTEGRATION.md` — this document.
- `tests/test_runtime_snapshot.py` — 35 new tests.
- `tests/test_runtime_inspect_cli.py` / `tests/test_runtime_inspect_verification.py`
  — five pre-existing tests deliberately updated (§5 below), each with
  an explanatory comment, none silently loosened.

## 1. Runtime Snapshot Summary

`RuntimeSnapshot` (`src/pcae/core/runtime_snapshot.py`) composes
`runtime`/`registry`/`plugins`/`capabilities`/`health`/`governance`/
`state`/`version` (111B's own `get_*()` functions, called unchanged)
with a new `context: RuntimeContext | None` field. This phase's own new
principle, **"Runtime Snapshot is the canonical read model,"** names
the intent directly: every future consumer (CLI today; REST, Telegram,
dashboard, and AI agents named as future consumers, §8 of the
architecture doc) should render this one model, never independently
re-derive a partial view of the same facts.

## 2. Runtime Inspect Integration Summary

`commands/runtime_inspect.py`'s `_build_snapshot(registry)` — kept
under its exact original name and single-argument signature so every
pre-existing call site across `test_runtime_inspect_cli.py` (111C) and
`test_runtime_inspect_verification.py` (111D) continues to work
unmodified — is now:

```python
def _build_snapshot(registry: RuntimeRegistry) -> dict:
    root = HarnessPath.cwd()
    snapshot = build_runtime_snapshot(root, registry)
    return snapshot_to_dict(snapshot)
```

Three lines, no loop, no bespoke composition (confirmed directly: an
AST scan of this function finds zero `for`/`while` nodes — the same
"cost scales only with delegated calls" property 111D's own
performance-verification test already checked, now re-verified against
the refactored function). All actual assembly logic moved to
`runtime_snapshot.py`.

## 3. Runtime Context Integration Summary

`build_runtime_context_from_repo(root)` reads `.pcae/session.json`
(`pcae.core.session.read_session_snapshot`) and `tasks/active/`
(`pcae.core.tasks.find_latest_active_task`) — the same already-governed
helpers `pcae session bootstrap` itself uses — to construct a
best-effort `RuntimeContext`. Populated: `RuntimeSession` (`session_id`
from the real file's `timestamp` field), the active `TaskContext` (if
one exists), and `ObservationContext` (the four `INT-NNN` integrations,
always populated per 112B §8's "Observation always available"
invariant, regardless of whether a task is active). Never populated:
Active Phase, Intent, Approval, Broker Decision, Evidence — each has no
real, governed backing source anywhere in this codebase yet
(`COMP-003`/`COMP-007` remain unimplemented), and each is reported
explicitly as `null`/"not implemented anywhere," never silently
omitted.

## 4. Backward Compatibility Summary

`pcae runtime inspect`, `--json`, and `--verbose` all continue to work.
The JSON schema gains exactly one new, additive top-level key —
`context` — confirmed directly against 111D's own frozen
`STABLE_TOP_LEVEL_KEYS`/`STABLE_SECTION_KEYS` contract tests (updated
deliberately to include it, not loosened). Every pre-existing section
(`runtime`/`registry`/`plugins`/`capabilities`/`health`/`governance`/
`state`/`version`) is byte-for-byte unchanged in shape. The default
human-readable output is completely unchanged; the new "Runtime Context
(112E):" section appears only under `--verbose`.

## 5. Pre-Existing Test Updates (Deliberate, Not Silent)

Five tests, written in 111C/111D before Runtime Snapshot existed,
needed deliberate updates — each is exactly the kind of "documented
decision, not an accidental side effect" their own comments already
anticipated:

- `test_runtime_inspect_cli.py::test_module_imports_are_allowlisted`
  and `test_runtime_inspect_verification.py::test_module_import_allowlist_unchanged_from_111c`
  — the CLI's import allowlist updated: `pcae.core.runtime_introspection`
  removed (no longer imported directly), `pcae.core.paths` and
  `pcae.core.runtime_snapshot` added.
- `test_runtime_inspect_verification.py`'s `STABLE_TOP_LEVEL_KEYS` —
  `context` added, per that constant's own comment: "any change... must
  be a deliberate, documented decision."
- `test_json_is_always_a_flat_two_level_structure_for_scalars` —
  `context` excluded from the flatness constraint, since Runtime
  Context is, by 112A/112B/112C's own frozen design, genuinely
  hierarchical (session → tasks, session → observation); flattening it
  would misrepresent the composition model this phase exists to
  integrate.
- `test_compatible_with_111a_introspection_architecture_domains` —
  `context` excluded from the per-key doc-text check, since 111A's
  architecture document predates Runtime Context entirely and never
  mentions it; `docs/PCAE_RUNTIME_SNAPSHOT.md` is the document that key
  is meaningfully checked against instead.

No test was loosened beyond what the new, additive key required; all
101 tests across the two affected files (111C/111D) plus 35 new tests
(`tests/test_runtime_snapshot.py`) — 136 total — pass after the
updates.

## 6. Current Limitations

- Active Phase, Intent, Approval, Broker Decision, and Evidence remain
  unpopulated — no real, governed backing source exists anywhere in
  this codebase yet for any of them.
- `session_id` is derived from `.pcae/session.json`'s `timestamp`
  field, not a dedicated identifier — the real file's current shape,
  not invented by this phase.
- No REST endpoint, Telegram integration, web UI, or dashboard consumes
  `RuntimeSnapshot` yet.
- Runtime Context's own structural-but-unenforced invariants (112C/112D)
  are unchanged by this integration.

## Recommendation for Runtime Inspect Integration

Completed by this phase. **112F — Runtime Snapshot Contract Freeze** is
recommended next, mirroring the design→contract→prototype pattern this
arc has already followed for Registry (110C→110D→110E) and Context
(112A→112B→112C): freeze the exact contract for `RuntimeSnapshot`
itself (identity, composition rules, what "canonical" guarantees, and
what a future REST/Telegram/dashboard consumer may rely on) before any
of those future consumers are built against it.

## Execution Integration Status

Unchanged — this phase introduces no execution capability:

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

- **Why this phase cannot introduce execution capability:** neither
  new/modified file imports a plugin-loading, broker-evaluation, shell,
  subprocess, or network module (verified directly via AST import
  scans in `tests/test_runtime_snapshot.py`).
- **Why the new repo-state read is not a new I/O capability:**
  `build_runtime_context_from_repo()` calls the exact same
  `pcae.core.session.read_session_snapshot()`/
  `pcae.core.tasks.find_latest_active_task()` functions `pcae session
  bootstrap` already calls today — reading state this codebase already
  reads elsewhere, not a new capability.
- **Why backward compatibility is provable, not just claimed:** every
  pre-existing JSON section shape and the human-readable default output
  are covered by 111C/111D's own already-passing tests, re-run
  unmodified against the refactored code; the five updates needed were
  each to a test whose own subject matter (import allowlist, schema
  key set, doc-text cross-check) legitimately changed, not to a test
  checking unrelated behavior.

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
