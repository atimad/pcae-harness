# Phase 109B — First Command-Path Integration Prototype (Observation-Only, Disabled by Default)

## Purpose

Implement the first Permission Broker command-path integration prototype
while preserving PCAE's current non-executing guarantees. This phase
establishes integration plumbing only: the broker may be consulted for
observation purposes, but its decision must never influence repository
behavior. It is the first phase in the 109-series to touch `src/pcae/`
production code since 108D — 109A (architecture design) touched none.

## Scope

Exactly one command path, integrated in observation mode only. Adds
`src/pcae/core/command_path_observation.py` (the `observe()` helper) and
modifies `src/pcae/commands/health.py` (the integration call site). Adds
`tests/test_permission_broker_command_path_prototype.py`. No other
command path is touched. No runtime execution, shell mediation,
subprocess mediation, backend invocation, adapter invocation, execution
enablement, execution capability, Permission Broker enforcement, audit
persistence, rollback execution, emergency stop, Telegram inbound,
automatic apply, command execution, command blocking, command
authorization, or behavior change of any kind is implemented.

## Chosen Command

**`pcae health`.** Selected because it is PCAE's most fundamental
read-only diagnostic command — no mutation, no side effects, a pure
function of `build_health_data()` + `is_healthy()` — and it falls
squarely in the "Read-only" category frozen by
`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (109A), whose
own table states broker involvement is "not required" for this
category's authorization purposes. Consulting the broker here anyway,
purely for observation, is the lowest-risk possible way to prove the
integration plumbing works before ever touching a category where the
broker's involvement matters.

## Observation-Only Architecture

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

`run_health()` (`src/pcae/commands/health.py`) computes `data` exactly as
before, then calls `pcae.core.command_path_observation.observe(...)`
with `action_type="read"`, `execution_class="none"`,
`requested_component="COMP-001"`, `requested_capability="pcae_health"`,
the active task ID if one exists, and `evidence_available=True`,
`approval_present=True` (this command needs neither in reality — these
values reflect that a read-only action always has what it needs, not a
claim that the broker's answer matters here). The call's return value is
never assigned to anything the function later reads; it is a bare
expression whose result is thrown away. Printing and the exit-code
computation (`return 0 if is_healthy(data) else 1`) are completely
unaffected — they were already computed from `data` before the
observation call and depend on nothing it returns.

`observe()` itself (`src/pcae/core/command_path_observation.py`) wraps
the entire broker interaction — request construction and
`PermissionBroker.evaluate()` — in a `try`/`except Exception: return
None`, so it can never raise. The call site in `health.py` wraps the
call again in its own `try`/`except Exception: pass`, so behavior
preservation holds even if a future change to `observe()` ever
reintroduced a way to raise — defense in depth, not reliance on a single
guard.

**No authorization. No denial. No execution.** The broker's decision —
`ALLOW`, `DENY`, or `HUMAN_REVIEW` — is produced exactly as it always is
(108A–108D, unmodified), and then discarded. Nothing reads
`decision.decision` to change control flow.

## Safety Case

- **Why the integration cannot execute anything:** `observe()` only
  constructs a `PermissionBrokerRequest` and calls
  `PermissionBroker.evaluate()`. The broker itself has zero execution
  capability by construction (108A's AST-import isolation tests, still
  unmodified and still passing against this phase's code) — it imports
  only `__future__`, `uuid`, `dataclasses`, `datetime`. `observe()`
  itself was verified to introduce no `subprocess`, `os`, `shell_gate`,
  `backend_invocations`, or `notifications` import. There is no code
  path in this integration that could execute anything even if it tried.
- **Why it cannot block anything:** `run_health()`'s return statement
  references `is_healthy(data)` only — verified directly by a test that
  inspects the function's source and confirms the line containing
  `return` and `is_healthy` never also contains `observe`. The
  observation call's result is never captured in a variable the return
  statement (or the print calls before it) could reference.
- **Why it cannot authorize anything:** the broker's decision was
  already established (108A–108D) to never constitute a real execution
  authorization even when a caller *does* read it —
  `implementation_status` is unconditionally `"execution_unavailable"`
  on every decision, `ALLOW` included. Here, the decision is not even
  read, so it is doubly incapable of authorizing anything.
- **Why it cannot bypass governance:** `pcae check`'s task-scope
  enforcement, `pcae push check`, GitHub branch protection (106M), and
  the 108E pre-push hook are all completely independent of this
  observation call — none of them consult or are affected by `observe()`
  or its result. This integration adds a call, not a dependency for any
  existing gate.
- **Why existing behavior is preserved:** proven directly by tests that
  run `pcae health` twice against the same repository state — once with
  `observe()` returning `None`, and again with it returning `ALLOW`,
  `DENY`, `HUMAN_REVIEW`, or raising an exception — and assert the
  captured stdout and exit code are byte-identical across every variant.

## Backward Compatibility

- **Command output unchanged:** `tests/test_health.py`'s 14 pre-existing
  tests are unmodified and pass unchanged against the integrated code.
- **Exit codes unchanged:** demonstrated directly — `main(["health"])`'s
  return value is identical regardless of what `observe()` returns,
  including when it raises.
- **Lifecycle unchanged:** `pcae task`/`pcae commit`/`pcae push` and
  every other governed lifecycle command are untouched by this phase;
  only `pcae health` was modified.
- **Governance unchanged:** `pcae check`, `pcae push check`, branch
  protection, and the pre-push hook all continue to operate exactly as
  before — none of them were modified, and none of them depend on this
  integration.
- **Broker isolation preserved:** `src/pcae/core/permission_broker_foundation.py`
  itself was not modified by this phase (not in this phase's task
  contract's allowed files); its own 108A–108D isolation and behavior
  tests (171 tests across four files) remain unmodified and pass
  unchanged.

## Execution Integration Status

*(This section's format is intended to be a canonical, reusable report
section — future phases that integrate additional command paths should
include an updated version of this same table in their own phase docs,
incrementing the counts as integration grows.)*

| Field | Value |
|---|---|
| Integrated command paths | **1** (`pcae health`, observation-only) |
| Connected boundaries | **0** (no `COMP-NNN` boundary beyond the Permission Broker itself is connected to anything) |
| Behavior-changing integrations | **0** |
| Execution-capable integrations | **0** |
| Current execution capability | **Execution unavailable** |

## Limitations

- This prototype proves the plumbing works for exactly one, deliberately
  trivial command category (Read-only). It says nothing about how
  observation would need to change for a category where the broker's
  answer should eventually matter (Git lifecycle, shell execution, etc.)
  — that is explicitly out of scope and deferred to a future hardening
  phase.
- The observation call happens on every `pcae health` invocation,
  including the many the existing test suite already performs — this
  was a deliberate choice to get real-world exercise of the integration
  "for free" across the whole suite, not an attempt to gather production
  telemetry (nothing is logged, persisted, or surfaced anywhere; see the
  safety case above).
- No mechanism exists yet to actually *observe* what `observe()` returned
  outside of a test — there is no logging, no metrics, no artifact. This
  is intentional for this prototype phase; a future phase would need to
  design that surface deliberately (and decide what, if anything, is
  safe to persist) rather than bolt it on incidentally here.

## Future Evolution

**109C — Command-Path Integration Hardening** (recommended next phase)
would be the natural place to: extend observation to additional
Read-only/Repository-inspection command paths (widening from 1 to
several integrated paths while keeping behavior-changing and
execution-capable integrations at 0); consider whether a structured,
safe way to record what the broker observed (without persisting
anything sensitive or creating a new audit-adjacent mechanism ahead of
`COMP-007`) is worth designing; and re-verify, as this phase did, that
zero behavior change holds after each addition.

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

**109C — Command-Path Integration Hardening.**
