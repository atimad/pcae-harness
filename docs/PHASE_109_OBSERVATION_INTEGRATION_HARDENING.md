# Phase 109C — Observation Integration Hardening & Multi-Path Expansion

## Purpose

Harden and generalize the observation-only integration pattern
established by 109B (`pcae health`) across a small number of additional
read-only lifecycle command paths, and introduce a canonical Integration
ID registry so future phases can enumerate "which command paths
currently observe the broker, and what is each one's status"
programmatically instead of re-deriving it from source inspection. This
phase widens observation coverage; it does not change what observation
*is* — the discard-the-decision contract from 109B is preserved exactly.

## Scope

Three additional command paths, each integrated in observation mode
only, plus the Integration ID registry:

- `src/pcae/core/command_path_observation.py` — adds
  `IntegrationRegistryEntry`, `INTEGRATION_REGISTRY`, `INTEGRATION_IDS`,
  and `get_integration()`. `observe()` itself is unmodified.
- `src/pcae/commands/check.py` — adds the `observe()` call to
  `run_check()` (INT-002).
- `src/pcae/commands/task.py` — adds the `observe()` call to
  `run_doctor_task_memory()` (INT-003).
- `src/pcae/commands/push.py` — adds the `observe()` call to
  `run_push_check()` only (INT-004). `run_push()` — the real, mutating
  push command — is deliberately untouched.
- `tests/test_permission_broker_observation_hardening.py` — new focused
  test suite (47 tests).

No other command path is touched. `commit`, `push` (the real push, not
push check), `shell`, `subprocess`, and every other execution-related
command remain outside observation scope, exactly as the brief required.
No runtime execution, shell mediation, subprocess mediation, backend
invocation, adapter invocation, execution enablement, execution
capability, Permission Broker enforcement, audit persistence, rollback
execution, emergency stop, Telegram inbound, automatic apply, command
execution, command blocking, command authorization, or behavior change
of any kind is implemented.

## Chosen Commands

| Integration ID | Command | Why chosen |
|---|---|---|
| INT-001 | `pcae health` | Established in 109B; unchanged here, listed for completeness. |
| INT-002 | `pcae check` | PCAE's own governance/scope gate — read-only, runs on virtually every workflow step, so exercising observation here gives the widest real-world coverage of any single addition. |
| INT-003 | `pcae doctor task-memory` | A diagnostic command with both a read-only mode and a `--fix` (self-repair) mode; chosen specifically to prove observation behaves identically across both invocation styles without needing to distinguish between them. |
| INT-004 | `pcae push check` | The read-only readiness assessment sibling of `pcae push`. Chosen precisely because it sits right next to a real mutating command, to prove the integration can be scoped to the safe half of a command pair without spilling into the other half. |

## Integration ID Registry

`src/pcae/core/command_path_observation.py` now exposes a canonical,
stable registry:

```python
INTEGRATION_REGISTRY: tuple[IntegrationRegistryEntry, ...] = (
    IntegrationRegistryEntry(integration_id="INT-001", command="pcae health", ...),
    IntegrationRegistryEntry(integration_id="INT-002", command="pcae check", ...),
    IntegrationRegistryEntry(integration_id="INT-003", command="pcae doctor task-memory", ...),
    IntegrationRegistryEntry(integration_id="INT-004", command="pcae push check", ...),
)
```

Each entry is a frozen dataclass recording `integration_id`, `command`,
`integration_type` (`"observation-only"` for all four), `observation_status`
(`"active"` for all four), `implementation_status`
(`"observation_only"` for all four), and a `future_evolution` note. IDs
are bookkeeping only — they carry no runtime behavior, are never read by
`observe()`, and are never consulted by any integrated command.
`get_integration(integration_id)` looks up a single entry by ID and
returns `None` for anything unregistered (e.g. `INT-999`).

## Observation-Only Architecture (unchanged from 109B)

```
Broker consulted
  |
  v
Decision produced
  |
  v
Decision discarded
  |
  v
Existing command continues unchanged
```

Every new call site follows the identical shape 109B established in
`health.py`: the command computes its result exactly as before, then
calls `observe(...)` as a bare expression inside a local
`try`/`except Exception: pass`, and finally proceeds using only values
computed before the observation call. `observe()` itself
(`command_path_observation.py`, unmodified since 109B) already wraps its
own body in `try`/`except Exception: return None` — every new call site
adds a second, redundant guard at the point of use, matching 109B's
defense-in-depth posture rather than trusting a single guard.

- **`run_check()`** (`check.py`): calls `observe()` with
  `requested_capability="pcae_check"` and `task_id=result.active_task_id`,
  immediately after `run_checks()` computes `result` and before any
  output is printed or the exit code is chosen.
- **`run_doctor_task_memory()`** (`task.py`): calls `observe()` with
  `requested_capability="pcae_doctor_task_memory"` once, before branching
  on `fix`/`dry_run`, so both the diagnostic and `--fix` invocation modes
  are observed identically without the call site distinguishing between
  them.
- **`run_push_check()`** (`push.py`): calls `observe()` with
  `requested_capability="pcae_push_check"`, before `_print_readiness()`
  is invoked. `run_push()` has no `observe()` call anywhere in its
  source — verified directly by a test that inspects
  `inspect.getsource(push_module.run_push)` for the literal substring
  `"observe("`.

All four calls use `action_type="read"`, `execution_class="none"`,
`requested_component="COMP-001"`, `evidence_available=True`,
`approval_present=True` — the same read-only justification 109B used for
`pcae health`, since none of these three commands mutate repository
state either.

## Safety Case

- **Why the integration cannot execute anything:** identical to 109B's
  argument, unchanged because `observe()` itself is unmodified. The
  broker (108A–108D, unmodified) imports only `__future__`, `uuid`,
  `dataclasses`, `datetime` — re-verified directly by this phase's own
  AST-import test (`test_broker_foundation_module_still_stdlib_only`).
  `command_path_observation.py` was re-verified to introduce no
  `subprocess`, `shell_gate`, `backend_invocations`, or `notifications`
  import even after adding the registry
  (`test_command_path_observation_module_still_isolated`).
- **Why it cannot block anything:** for each of the three new call
  sites, a source-inspection test confirms the observation call's return
  value is never assigned to a name (`"= observe(" not in source`) — it
  is always a bare expression whose result is thrown away before the
  function's real control flow (branching, printing, `return`) is
  reached.
- **Why it cannot authorize anything:** the broker's `decision` field is
  not read at any of the three new call sites (verified by the same
  source-inspection tests, plus a direct check that no forbidden
  authorization-sounding token — `authorize`, `authorization_granted`,
  `execution_authorized`, `block_command`, `deny_command` — appears
  anywhere in the three integrated functions' source).
- **Why it cannot bypass governance:** `pcae check`'s own scope/policy
  enforcement, `pcae push check`'s own readiness computation, and
  `pcae doctor task-memory`'s own diagnostic/repair logic are all
  computed independently of `observe()` and before it is called;
  `test_check_scope_enforcement_unaffected_by_observation` and
  `test_push_check_readiness_logic_unaffected_by_observation` prove this
  directly by forcing the broker to return opposite decisions (`ALLOW`
  vs `DENY`) and asserting the command's real output and exit code do
  not change.
- **Why existing behavior is preserved:** proven directly, per command,
  by running it twice against the same repository state — once with
  `observe()` returning `None`, and again with it returning `ALLOW`,
  `DENY`, `HUMAN_REVIEW`, or raising an exception — and asserting
  captured stdout and exit code are byte-identical across every variant
  (`test_output_identical_regardless_of_decision`,
  `test_output_identical_when_observe_raises`,
  `test_check_json_output_identical_regardless_of_decision`).
- **Why INT-001 (`pcae health`) is unaffected:** `health.py` was not
  modified in this phase (not in this phase's task contract's allowed
  files) and 109B's own 22-test suite
  (`tests/test_permission_broker_command_path_prototype.py`) was re-run
  unmodified and still passes in full
  (`test_health_tests_still_pass`).

## Backward Compatibility

- **Command output unchanged:** `pcae check`, `pcae doctor task-memory`,
  and `pcae push check` produce byte-identical stdout across every
  broker-decision variant, including exceptions.
- **Exit codes unchanged:** same guarantee, verified directly for all
  three new commands.
- **Lifecycle unchanged:** `pcae task`/`pcae commit`/`pcae push` (the
  real push) are untouched except for the single, additive
  `run_push_check()` call site; no other function in any of the three
  modified modules was changed.
- **Governance unchanged:** `pcae check`'s scope enforcement and
  `pcae push check`'s readiness computation are demonstrated to be fully
  independent of the broker's decision (see safety case above). Branch
  protection and the 108E pre-push hook were not touched by this phase.
- **Broker isolation preserved:** `permission_broker_foundation.py` was
  not modified (not in this phase's allowed files); 108D's isolation
  test (`test_broker_not_imported_by_lifecycle_command_modules`, which
  greps `commit.py`/`push.py`/`task.py`/`phase.py` for the literal
  strings `"permission_broker_foundation"` and `"PermissionBroker("`)
  still passes, because the new call sites import `observe` from the
  `command_path_observation` indirection layer, never the broker module
  directly.
- **Previous observation path unchanged:** INT-001 (`pcae health`) was
  re-verified end-to-end — the broker is still consulted, and 109B's
  full test suite still passes unmodified.

## Execution Integration Status

| Field | Value |
|---|---|
| Observed command paths | **4** (`pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push check` — all observation-only) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |

## Limitations

- Observation coverage remains deliberately narrow — four Read-only /
  Repository-inspection command paths out of PCAE's full command
  surface. Git-lifecycle-mutating commands (`commit`, the real `push`),
  shell/subprocess-adjacent commands, and every execution-capable
  category from `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`
  (109A) remain entirely unobserved, by design.
- The Integration ID registry is static, hand-authored bookkeeping — it
  does not auto-discover call sites and would drift silently if a future
  phase added an `observe()` call without also adding a registry entry.
  No test in this phase enforces registry/call-site parity beyond the
  four IDs this phase itself introduced.
- As with 109B, there is still no mechanism to observe what `observe()`
  returned outside of a test — no logging, no metrics, no artifact. This
  remains an intentional, unaddressed gap carried forward from 109B, not
  a regression introduced here.

## Future Evolution

**109D — Observation Integration Verification & Compatibility**
(recommended next phase) would be the natural place to re-verify, under
a full regression pass, that all four observation-only integrations
established through 109B and 109C continue to hold their guarantees
without expanding coverage further — mirroring how 108D re-verified
108A–108C before 109A began new design work.

## No-Go Confirmations

No runtime execution. No shell mediation. No subprocess mediation. No
backend invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No automatic apply. No command execution. No command blocking.
No command authorization. No behavior change. `implementation_status`
remains unconditionally `"execution_unavailable"` on every decision.
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**109D — Observation Integration Verification & Compatibility.**
