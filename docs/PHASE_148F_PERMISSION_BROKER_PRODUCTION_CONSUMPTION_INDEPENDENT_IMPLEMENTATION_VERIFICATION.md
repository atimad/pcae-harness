# Phase 148F — Permission Broker Production Consumption Independent Implementation Verification

## 1. Purpose and Methodology

Phase 148E implemented PBPC-001 v1.2 production consumption for `pcae
push`. This phase (148F) independently re-derives and verifies that
implementation against the frozen contracts (PBPC-001 v1.2, PBPA-001
v1.0) and empirical testing, **without trusting** 148E's phase report,
implementation document, test suite, in-code comments, claimed
dispatch-site count, claimed request shape, or claimed
non-bypassability.

Methodology: (1) reconstruct the exact production diff directly from
Git between the pre-148E baseline (`21a35087`) and 148E's final commit
(`5b015852`); (2) independently search the entire `src/pcae` tree —
not just `push.py` — for every mechanism capable of dispatching a real
`git push`; (3) read `run_push()` and `_run_push_staged_file_aware()`
line-by-line; (4) read the Permission Broker Foundation
(`permission_broker_foundation.py`) directly for POL-004/POL-005/
registry/decision-composition semantics; (5) write and run an
independently-authored adversarial test suite
(`tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py`,
11 tests, deliberately different coverage from 148E's suite); (6) run
the full existing regression battery. No production code, contract, or
POL-001..012 semantics were modified. Runtime posture was inspected
before and after and remains unchanged.

## 2. Initial Inspection (Read-Only)

```
git status --short              -> clean at phase start (task-lifecycle files only after bootstrap transition)
origin/main..HEAD                -> 0 commits
pcae health                      -> healthy
pcae check                       -> passed
pcae status coherence            -> coherent
pcae doctor task-memory          -> clean
pcae push check                  -> nothing_to_push
pcae runtime inspect             -> Observed / observe / unavailable
pcae notify status               -> Telegram configured, enabled
pcae phase-report show --latest  -> 148E, completed, complete
pcae phase-report reconcile 148E -> reconciled (read-only, no mutation)
```

148E's latest phase report (148E, status=completed, commits
`1f39ff38`/`5b015852`, pushed, origin/main..HEAD=0) was confirmed
against `pcae phase-report reconcile --phase-id 148E`, itself a
read-only operation.

## 3. Production Diff Reconstruction

Pre-148E baseline independently confirmed as `21a35087` (`1f39ff38`'s
direct parent). Full diff `21a35087..5b015852`:

```
CHANGELOG.md                                                       |  28 ++
PROJECT_STATUS.md                                                  |  40 ++
docs/PHASE_148E_..._IMPLEMENTATION.md                              | 501 +++
src/pcae/commands/push.py                                          | 166 +++++++
tasks/DONE.md                                                      |   1 +
tasks/completed/...148e-...implementation.md                       |  84 ++++
tasks/done/...idle-awaiting-next-governed-phase-post-148d.md       |   2 +-
tests/test_permission_broker_observation_verification.py           |   7 +-
tests/test_permission_broker_push_production_consumption.py        | 470 +++
tests/test_permission_broker_verification_compatibility.py         |  31 +-
tests/test_staged_file_aware_push.py                                |  13 +
```

`git diff --name-only 21a35087..5b015852 -- src/` returns exactly one
file: `src/pcae/commands/push.py`. **Sole-production-file claim
independently CONFIRMED.**

Hunk classification (`src/pcae/commands/push.py`, +166/-0):

| Hunk | Class |
|---|---|
| `PushPermissionResult` dataclass | ADAPTER |
| `_evaluate_push_permission()` | ADAPTER |
| `_permission_denial_details()` | DIAGNOSTIC |
| `_print_permission_denial()` | DIAGNOSTIC |
| `run_push()` insertion (Decision Consumption Point + gate) | ORDINARY_PATH_CONSUMPTION |
| `_run_push_staged_file_aware()` insertion (Decision Consumption Point + gate) | STAGED_PATH_CONSUMPTION |

No `BROKER_IMPORT` as a standalone hunk (the import is local, inside
`_evaluate_push_permission`, classified as part of ADAPTER). No
`REQUEST_CONSTRUCTION` hunk separate from ADAPTER (constructed inline
in the adapter). No `FAIL_CLOSED_HANDLING` hunk separate from ADAPTER
(the `try/except` and `isinstance` guard are part of the adapter body).
**No UNRELATED production hunk found.**

Independently confirmed empty diffs for:
`src/pcae/core/permission_broker_foundation.py`,
`src/pcae/core/permission_broker.py` — both byte-identical to
pre-148E.

## 4. Repository-Wide Git-Push Dispatch Inventory

Independent AST-based search of `src/pcae/**/*.py` for
`subprocess.run(["git", "push", ...])`-shaped calls (not a trusted
count) found **five** real dispatch sites total, not two:

| # | File | Line | Reachable from `pcae push`? | Broker-gated? |
|---|---|---|---|---|
| 1 | `src/pcae/commands/push.py` | 590 (`["git","push"]`) | Yes — `run_push()` | Yes (148E) |
| 2 | `src/pcae/commands/push.py` | 771 (`["git","push","origin","main"]`) | Yes — `_run_push_staged_file_aware()` | Yes (148E) |
| 3 | `src/pcae/core/agent.py` | 4732 (`_run_git_push`, Phase 42E "Controlled Push") | No — reachable only via `pcae agent ...` (`push_file_changes`, `src/pcae/commands/agent.py:2329`) | No (pre-existing, out of Chapter 148 MVP scope) |
| 4 | `src/pcae/commands/phase.py` | 19563 (`_build_backend_created_output_adoption_push_execution`) | No — reachable only via `pcae phase backend-created-output-adoption-push-execution --execute` | No (pre-existing, out of scope) |
| 5 | `src/pcae/commands/phase.py` | 20295 (`_build_final_verification_tooling_push_decision`) | No — reachable only via `pcae phase final-verification-tooling-push-decision --execute-push` (requires `--approve-keep`/`--approved-by`/`--reason`) | No (pre-existing, out of scope; gated by its own explicit-approval flags, not by PBPC) |

`pcae push`'s CLI subparser (`src/pcae/cli.py`) dispatches exclusively
to `run_push`, which calls only itself or
`_run_push_staged_file_aware`. `push.py` contains no reference to
`core.agent`, `push_file_changes`,
`_build_backend_created_output_adoption_push_execution`, or
`_build_final_verification_tooling_push_decision` (independently
grepped).

**Result: reachable-through-`pcae-push` real dispatches = 2. Reachable
ungated dispatches = 0.** Sites 3–5 are real, pre-existing (unchanged
by the 148E diff), separate CLI verbs, not reachable through `pcae
push`, and therefore outside PBPC-001's stated MVP scope (Section 3,
"exactly one production consumer: `pcae push`"). This matches 148D/148E's
scope claim exactly but is now independently re-derived rather than
assumed — see Finding F-148F-2 (Section 15) for why this is recorded as
an Observation rather than silently omitted.

All eight other `subprocess.run` calls inside `push.py` itself
(diff/rev-parse/log/merge-base/diff-tree/rev-list) were individually
inspected; none invoke `git push`.

## 5. Ordinary Path Control Flow (`run_push()`)

Traced line-by-line (`src/pcae/commands/push.py:509–623`):

1. `readiness = assess_push_readiness(root)` — mechanical.
2. `if not readiness.ready:` → return (0 or 1) — **no broker
   construction, no dispatch.**
3. `if dry_run:` → return 0 — **no broker construction, no dispatch**
   (confirms PBPC-REQ-015: dry-run never requests permission for a
   dispatch it never performs).
4. Decision Consumption Point: `_evaluate_push_permission(...)` called
   exactly once.
5. `if not permission_result.authorized:` → print denial, return 1 —
   **zero dispatch.**
6. Only past this point: banner print, then the sole
   `subprocess.run(["git", "push"], ...)` call.
7. On `CalledProcessError`: print/return 1 (git-level failure, not a
   permission bypass — the push attempt itself failed).
8. On success: reconciliation, return 0.

No branch after step 4 skips to step 6 without passing through step 5.
**No bypass found.**

## 6. Staged-File-Aware Control Flow (`_run_push_staged_file_aware()`)

Traced line-by-line (`src/pcae/commands/push.py:626–815`). Early
returns, in order, all strictly before the Decision Consumption Point:
phase-report-trust failure, phase-report-identity failure,
nothing-to-push, protected-file-in-unpushed-commits, force-push-required,
dry-run. Decision Consumption Point at line 747–767, identical shared
adapter, called exactly once. Only past an `authorized` check does
control reach the sole `subprocess.run(["git", "push", "origin",
"main"], ...)` at line 771. Post-dispatch: protected-staged-file
preservation check (diagnostic only, cannot un-dispatch). **No branch,
fallback, or error-recovery path found that dispatches before or
without `authorized=True`.**

Independently verified empirically
(`test_staged_file_aware_force_push_block_not_overridden_by_allow`):
with a genuine forced `ALLOW` decision, the pre-existing force-push
mechanical check still blocks the push, and the Permission Broker is
never even constructed for that attempt (`broker_constructed.count ==
0`) — mechanical validity and permission remain correctly separated.

## 7. Shared Adapter

`_evaluate_push_permission` exists exactly once (single `def`, grepped
repository-wide). No duplicate adapter, no alternate request
constructor, no inline broker call elsewhere in `push.py`. Both call
sites pass the same fixed fields and only vary `task_id` (from
`find_latest_active_task`) and `requested_resource` (branch-specific
string). **Confirmed: one shared production adapter, as required.**

Adapter body independently inspected: constructs a request via
`build_permission_broker_request`, constructs/uses a `PermissionBroker`,
calls `.evaluate()`, returns a frozen `PushPermissionResult`. No `git`
invocation, no `subprocess`, no filesystem write, no task/lifecycle
state mutation, no agent invocation, no Runtime Enforcement call.
**Confirmed non-mutating.**

## 8. Canonical Request Shape and Field Provenance

Independently re-read from the adapter body (not from 148E's tests):

| Field | Value | Provenance | PBPC requirement | Truthful? |
|---|---|---|---|---|
| `action_type` | `ACTION_PUSH` ("push") | Foundation constant | PBPC-REQ-033 | Yes |
| `execution_class` | `EXECUTION_CLASS_MUTATION` ("mutation") | Foundation constant, hardcoded | PBPC-REQ-034 | Yes |
| `requested_component` | `"COMP-001"` | string literal | PBPC-REQ-035 | Yes (traces to Phase 109/COMP-001 registry entry, confirmed via `get_component`/`ComponentRegistryEntry`) |
| `requested_capability` | `"pcae_push"` | string literal | PBPC-REQ-046 | Yes, exact frozen vocabulary string |
| `task_id` | `active_task_for_permission.task_id if ... else None` | `find_latest_active_task(root)` | PBPC-REQ-042/044 | Yes — no fabricated fallback (see Section 9) |
| `requested_resource` | `f"refs/heads/{readiness.branch}"` (ordinary) / `"refs/heads/main"` (staged) | live readiness/constant | PBPC-REQ-047 (optional) | Yes |
| `evidence_available` | `True` | hardcoded | (structural field) | Yes, request itself is the evidence |
| `approval_present` | `False` | hardcoded literal | PBPC-REQ-046 | Yes (Section 13) |
| `simulation_only` | `True` | hardcoded literal | PBPC-REQ-036 | Yes (Section 14) |

No `execution_class`, `approval_present`, `simulation_only`, or
policy-selection value is derived from CLI arguments, environment, or
config. Independently confirmed by inspecting the `push` argparse
subparser block in `src/pcae/cli.py`
(`test_cli_push_parser_exposes_no_permission_override_flags`): no such
flags exist on `pcae push`.

## 9. `task_id` Provenance

`find_latest_active_task` (`src/pcae/core/tasks.py:801`) returns the
most recent file in `tasks/active/*.md`, or `None` if the directory is
empty/missing. `push.py` uses `active_task_for_permission.task_id if
active_task_for_permission else None` — **no fabricated fallback ID.**
When absent, `POL-001` (`MissingActiveTaskRule`) correctly denies
(`DENY`, not `ALLOW`) — independently confirmed pre-existing behavior,
unweakened by 148E.

## 10. `requested_component` / `requested_capability`

`"COMP-001"` is a member of the Foundation's `COMPONENT_IDS` registry
(checked by `UnknownComponentRule`/POL-007); the literal is not an
arbitrary implementation choice but the frozen component identity for
this domain, consistent with prior Permission Broker phases (108–109).
`"pcae_push"` matches the capability string exactly as required; no
case variation or alternate spelling exists elsewhere in the adapter.

## 11. `execution_class`

Hardcoded to `EXECUTION_CLASS_MUTATION`. Independently searched
`push.py` and the `pcae push` CLI wiring for any override surface
(CLI flag, environment variable, config file read) — **none found.**
Caller override paths = 0.

## 12. `approval_present`

Hardcoded `False`, literal in the adapter call. Independently searched
for any code path that could set it from IWC confirmation, task status,
AESIC, environment, or a CLI option — **none found** (`push.py`
contains zero references to IWC/interactive-workflow/AESIC/
authority_evaluation terms; grep-confirmed, Section 14).

## 13. `simulation_only`

Hardcoded `True` for the canonical PBPC push evaluation, with no
production call path passing `False`. Independently re-verified via
`ExecutionDisabledRule`/POL-005 (Section 14 below): a request built with
`simulation_only=False` and otherwise identical to the canonical push
request receives `DECISION_DENY` with `POL-005` in
`causing_policy_ids` — proving the adapter's fixed `True` is
load-bearing, not incidental.

## 14. POL-005 Independent Control

Independently constructed (not reusing 148E's test) a
`PermissionBrokerRequest` with `simulation_only=False`, otherwise
identical to the canonical push shape, evaluated against the live,
unmodified `PermissionBroker()`:

```
decision.decision == DECISION_DENY
"POL-005" in decision.causing_policy_ids
```

**Confirmed.** The production adapter is not relying on any weakened
POL-005 semantics — it is `simulation_only=True` that avoids this DENY,
by design (COMP-002 execution boundary not yet implemented).

## 15. POL-004 Independent Verification

Independently re-read `MissingHumanApprovalRule` (POL-004) directly
from `permission_broker_foundation.py`:
`applicable_execution_classes = {shell, backend, adapter, rollback}` —
`mutation` and `none` are excluded. For `pcae push`'s canonical
`execution_class=mutation` request with `approval_present=False`,
POL-004 is **not applicable** (`"POL-004" in
decision.non_applicable_policy_ids`), independently reproduced. This is
a general scoping rule (Phase 148C.6, PBPA-REQ-063/064) applied
uniformly, not a push-specific carve-out. Separately, requests built
with `execution_class` values inside POL-004's applicable set
(`shell`/`backend`/`adapter`/`rollback`) and `approval_present=False`
correctly receive `HUMAN_REVIEW` — **no policy weakening found.**

## 16. Broker Construction and Registry Integrity

`_evaluate_push_permission` calls
`permission_broker_foundation.PermissionBroker()` with no arguments in
both production call sites — the canonical `DEFAULT_POLICY_RULES` via
`PolicyRegistry()`'s default. The adapter's `broker:
PermissionBroker | None = None` keyword parameter is a test-injection
seam only; `push.py`'s own production call sites never pass it.
`PolicyRegistry.__init__` independently re-read: it validates, at
construction time, that the rule-ID set exactly matches
`POLICY_IDS_CANONICAL` (`POL-001`..`POL-012`) and raises on a missing
or duplicate ID — a registry cannot silently be partial. No CLI flag,
environment variable, or config read anywhere in `push.py` or the
`pcae push` argparse wiring can select an alternate registry, exclude
policies, or inject a custom rule set. Repository-wide search for
`exclude_policies`, `selected_policy_ids`, `skip_policy`,
`policy_profile` (or equivalents) introduced by 148E: **none found.**

## 17. Decision Consumption

`_evaluate_push_permission` computes `authorized = decision.decision ==
permission_broker_foundation.DECISION_ALLOW` only after an `isinstance`
check confirms `decision` is a real `PermissionBrokerDecision`
instance — not merely a value equal to the string `"ALLOW"`. Independently
attacked with a **duck-typed fake** (`_FakeAllowDecision`, a plain
class exposing `.decision == "ALLOW"` but not an instance of
`PermissionBrokerDecision`) on both dispatch paths: rejected, zero
dispatch, in both cases
(`test_ordinary_path_rejects_duck_typed_fake_allow`,
`test_staged_file_aware_rejects_duck_typed_fake_allow`) — broader than
148E's own invalid-result test, which used only a plain string. A bare
`None` and a plain string were also independently confirmed to be
rejected via the `isinstance` guard.

## 18. Fail-Closed Attack Battery (Independently Reproduced)

| Attack | Ordinary path | Staged path | Result |
|---|---|---|---|
| Invalid/malformed result (plain object, non-`PermissionBrokerDecision`) | ✅ tested (148E + 148F duck-typed variant) | ✅ tested (148F) | zero dispatch |
| `DENY` | ✅ (148E `test_ordinary_path_non_bypassable_for_every_non_allow_outcome`) | ✅ (148E) | zero dispatch |
| `HUMAN_REVIEW` | ✅ (148E, same test, parametrized) | ✅ (148E) | zero dispatch |
| `evaluate()` raises | ✅ (148E) | ✅ (148E) | zero dispatch |
| **Broker construction raises** (`PermissionBroker.__init__`) | ✅ tested (148F, new) | ✅ tested (148F, new) | zero dispatch, **but see Finding F-148F-1** |
| Mechanical failure before broker | ✅ (148E `test_staged_file_aware_mechanical_checks_still_block_before_broker`; 148F force-push variant with genuine forced ALLOW) | ✅ | zero dispatch, broker not even constructed |

All fail-closed paths independently confirmed to produce **zero `git
push` dispatch**, with one caveat documented as Finding F-148F-1 below
(construction failure is not diagnostically graceful, though it still
does not dispatch).

## 19. Exactly-Once Evaluation and Dispatch; Stale-Decision Non-Reuse

- Exactly-once evaluation: independently re-confirmed (148E's tests;
  148F's construction-failure and duck-typed tests count evaluation/
  construction calls where relevant).
- Exactly-once dispatch on `ALLOW`: independently re-confirmed via
  148E's real-local-bare-remote tests (unmodified by 148F, re-run as
  part of the regression battery, Section 21) — one `git push` per
  successful attempt, both paths.
- Stale decision reuse, forward direction (`ALLOW` then `DENY`): 148E's
  `test_ordinary_path_no_stale_decision_reuse` independently re-run,
  passes.
- Stale decision reuse, **reverse direction** (`DENY` then genuine
  `ALLOW`): **148F-authored**
  `test_ordinary_path_denial_is_not_cached_across_attempts` —
  independently proves no stale *denial* is cached either; the second,
  independently-legitimate attempt re-evaluates and dispatches exactly
  once. 148E's suite did not test this direction.
- In-process reuse: inspected `_evaluate_push_permission` and
  `PushPermissionResult` for module-level globals, caches, or mutable
  default arguments that could retain a decision across invocations —
  **none found**; every call constructs a fresh request and (absent
  injection) a fresh `PermissionBroker()`.

## 20. Force-Push and Protected-Staged-File Semantics

Both mechanical protections (`force_push_required`,
`protected_file_in_unpushed_commits`) independently confirmed to
execute strictly before the Decision Consumption Point in
`_run_push_staged_file_aware` (Section 6). 148F additionally
empirically confirmed (Section 6) that a **genuine, forced `ALLOW`**
does not override the force-push mechanical block — permission and
mechanical validity remain correctly separate authorities, as PBPC-001
requires.

## 21. Phase-Report Trust/Identity Checks

Both gates (`_assess_phase_report_trust`, `_detect_phase_report_gap`)
independently confirmed to execute before the Decision Consumption
Point in the staged-file-aware path (Section 6) and are unmodified by
the 148E diff. No PBPC `ALLOW` bypasses them.

## 22. HARD_BLOCK_REGISTRY Recount

Independently imported `HARD_BLOCK_REGISTRY` from
`src/pcae/core/permission_broker.py` (a module confirmed byte-identical
pre/post-148E): **12 entries**, reason codes independently enumerated
and matched against the expected set
(`test_hard_block_registry_count_and_identity_unchanged`, 148F). No
entries added, removed, or modified by 148E.

## 23. Permission vs. Mechanical Ownership

No competing "broker ALLOW + legacy permission DENY" dual-authority
condition found: `push.py`'s own mechanical checks (readiness,
phase-report trust/identity, protected-file, force-push) are structural
preconditions that occur strictly before the broker is even consulted,
not a second permission judgment running in parallel with it. The
Permission Broker is the sole normative *permission* authority for the
push action; mechanical checks remain a separate, pre-existing
*readiness* layer, exactly as PBPC-001 Section 11 (Ownership Model)
specifies.

## 24. No New Policy Meaning

`permission_broker_foundation.py` and `permission_broker.py` diffs both
independently confirmed empty (`git diff 21a35087..5b015852`). POL-001
through POL-012 evaluator bodies unread-modified. No `POL-013+` added
(`POLICY_IDS_CANONICAL` still `POL-001`..`POL-012`, independently
recounted in Section 22's registry-construction validation).

## 25. Old Invariant-Test Repair Classification

148E narrowed two Phase 108D/109D-era tests
(`test_permission_broker_observation_verification.py`,
`test_permission_broker_verification_compatibility.py`) that previously
asserted `push.py` never imports the broker at all. Independently
diffed both files (Section 3): the narrowing removes exactly `push.py`
from the "never imports broker" assertion list, keeps
`commit.py`/`task.py`/`phase.py` under the original, unmodified
assertion, and adds a new positive guard
(`test_broker_wiring_remains_scoped_to_push_only`) asserting `push.py`
does still import the broker (preventing silent *removal* of the
wiring going forward, though not silent *expansion* to a sixth module —
see Section 26). **Classification: CORRECTLY_NARROWED.** The repair is
proportionate to the one explicitly authorized exception PBPC-001
grants and does not weaken the assertion for any other module.

## 26. New Scope Guard

`test_broker_wiring_remains_scoped_to_push_only` (148E) only asserts
that `push.py` still imports the broker — it does not, by itself,
positively re-assert that `commit.py`/`task.py`/`phase.py` remain
unwired (that assertion lives in the separately-parametrized test
retained from 108D/109D, `LIFECYCLE_COMMAND_MODULES_UNWIRED`, Section
25). Both together provide the intended guard. 148F independently
re-derived this from production source directly
(`test_permission_broker_consumer_scope_inventory`, Section 27) rather
than trusting the test file's own framing.

## 27. Production Consumer Inventory

Independent repository-wide search of `src/pcae/**/*.py` for
`permission_broker_foundation` imports or `PermissionBroker(`
construction:

| File | Classification |
|---|---|
| `src/pcae/commands/push.py` | AUTHORIZED_148E_PUSH_CONSUMER |
| `src/pcae/core/permission_broker_foundation.py` | (the module itself) |
| `src/pcae/core/runtime_context.py` | PRE_EXISTING_OBSERVATIONAL |
| `src/pcae/core/command_path_observation.py` | PRE_EXISTING_OBSERVATIONAL (Phase 109C, `push check`-only, decision discarded, PBPC-REQ-015) |
| `src/pcae/core/runtime_introspection.py` | PRE_EXISTING_OBSERVATIONAL |
| `src/pcae/core/runtime_registry.py` | PRE_EXISTING_OBSERVATIONAL |

No `UNEXPECTED_NEW_CONSUMER` found. `commit.py`/`task.py`/`phase.py`
independently confirmed to contain zero references to
`permission_broker_foundation` or `PermissionBroker(`
(`test_permission_broker_consumer_scope_inventory`, 148F).

## 28. Command Scope

Confirmed: PBPC production enforcement was not added to `pcae commit`,
`pcae task`, or `pcae phase` (Section 27). Chapter 148 MVP remains
`pcae push` only.

## 29. IWC Independence

`push.py` independently grepped for `iwc`, `interactive_workflow`,
`confirmation` (case-insensitive): **zero matches.** No permission
dependency on Interactive Workflow Confirmation.

## 30. AESIC Independence

`push.py` independently grepped for `aesic`, `authority_evaluation`
(case-insensitive): **zero matches.** No permission dependency on
Authority Evaluation/AESIC.

## 31. Runtime Enforcement Independence

`push.py` independently grepped for `runtime_enforcement`
(case-insensitive): **zero matches.** No new Runtime Enforcement calls
or imports. Runtime Enforcement regression suites (Section 34) pass
unchanged.

## 32. Runtime Capability State

`pcae runtime inspect` run before and after this phase's verification
work: **State: Observed, Maximum Capability: observe, Execution
Availability: unavailable** — unchanged in both directions. PBPC wiring
governs an already-existing mutation command; it does not elevate
runtime capability.

## 33. Durable Artifact Check

Independently searched for new files or artifact writers representing
broker decisions introduced by 148E: **none found.** `PushPermissionResult`
is an in-memory, per-call `dataclass`, never serialized to disk by the
adapter. The PBPC decision remains consumed strictly in-process.

## 34. Diagnostic Safety and Exit Codes

`_permission_denial_details`/`_print_permission_denial` expose only
`decision.decision`, `decision.decision_reason`, and
`decision.causing_policy_ids` — no internal broker state, no secret
material. `BROKER_FAILURE` is diagnostically distinguishable from
`DENY`/`HUMAN_REVIEW` (a distinct `"permission_decision"` label).
Exit-code behavior, independently captured:

| Outcome | Exit code | Diagnostic quality |
|---|---|---|
| `ALLOW` (successful push) | 0 | n/a |
| `DENY` | 1 | clean, distinguishable message |
| `HUMAN_REVIEW` | 1 | clean, distinguishable message |
| `evaluate()` exception | 1 | clean, labeled `BROKER_FAILURE` |
| invalid/malformed decision object | 1 | clean, labeled `BROKER_FAILURE` (`invalid_broker_result`) |
| **`PermissionBroker()` construction exception** | **uncaught Python exception (non-zero, but not the clean `1`/`BROKER_FAILURE` path)** | **ungraceful — see Finding F-148F-1** |
| mechanical failure (e.g. force-push-required) | 1 | pre-existing, unrelated to PBPC, unchanged |
| `--dry-run` | 0 | n/a, no broker call made |

## 35. Findings

### F-148F-1 (NON-BLOCKING) — `PermissionBroker()` construction failure is not fail-closed *gracefully*

In `_evaluate_push_permission`
(`src/pcae/commands/push.py:449–450`), the line
`broker_instance = broker if broker is not None else
permission_broker_foundation.PermissionBroker()` sits **outside** the
subsequent `try:` block, which wraps only `broker_instance.evaluate(request)`.
A `PermissionBroker.__init__`/registry-construction failure therefore
propagates as an **unhandled exception out of `pcae.cli.main()`
itself**, independently reproduced
(`test_ordinary_path_broker_construction_failure_does_not_dispatch`,
`test_staged_file_aware_broker_construction_failure_does_not_dispatch`),
rather than the clean `"Push blocked: Permission Broker evaluation
failed (...)"` / exit-code-1 diagnostic the `evaluate()`-failure path
produces.

**Severity assessment:** the core security invariant (`git push`
dispatched ⇒ fresh valid `ALLOW`) is **not violated** — the process
crashes strictly before reaching the `subprocess.run(["git", "push"],
...)` line, so zero dispatch occurs either way, in both call sites.
This is a diagnostics/failure-ownership gap (PBPC-001 Section 19),
not a bypass. Under today's canonical `DEFAULT_POLICY_RULES`,
`PolicyRegistry()` construction cannot actually fail (it always
receives a complete, non-duplicate, hardcoded rule tuple), so this gap
is not presently triggerable by any external caller — it would require
a future code change (e.g. a corrupted registry, or a future dynamic
registry-selection feature) to become reachable. Classified
**NON-BLOCKING**. Recommend a bounded repair (widen the adapter's
`try:` to also cover broker construction) in a future 148F.x-scoped
phase; **148F does not implement this repair** (out of scope per the
"No Production Repair Rule").

### F-148F-2 (OBSERVATION) — Three pre-existing, unrelated `git push` dispatch mechanisms exist outside `pcae push`

`src/pcae/core/agent.py` (`_run_git_push`, Phase 42E "Controlled Push",
reachable via `pcae agent ...`) and `src/pcae/commands/phase.py`
(`_build_backend_created_output_adoption_push_execution` /
`_build_final_verification_tooling_push_decision`, reachable via two
distinct, older, one-off `pcae phase ...` subcommands, each gated by
their own explicit `--approve-keep`/`--approved-by`/`--reason` or
`--execute` flags) each perform a real `git push` and are **not**
gated by the Permission Broker. All three predate Phase 148E (confirmed
unmodified by the 148E diff, Section 3) and are **not reachable through
the `pcae push` CLI verb** (Section 4) — PBPC-001's stated MVP scope is
explicitly `pcae push` only (Section 3, "SHALL NOT apply to ... arbitrary
Git operations outside `pcae push`"), so this is not a contract
violation. Classified **OBSERVATION**, not Blocking: recorded so a
future phase considering broader Permission Broker coverage (beyond
Chapter 148's `pcae push` MVP) has an accurate, independently-verified
starting inventory rather than rediscovering these paths from scratch.

### F-148F-3 (NON-BLOCKING) — PBPC-REQ-059/060/061 (Final Pre-Dispatch Validation / re-observation) is not implemented

PBPC-001 v1.2 Section 17 (`PBPC-REQ-059`–`061`) states: "Immediately
before each dispatch site ... a future implementation SHALL re-observe:
local HEAD revision, local branch, unpushed-commit count, and active
task ID ... A mismatch ... SHALL constitute a material mismatch ...
the existing `ALLOW` decision SHALL be treated as invalid." This is
reinforced as a required demonstration for "a future implementation,
once built" by `PBPC-REQ-091`. Independently confirmed: neither
`_evaluate_push_permission` nor either dispatch site performs any such
re-observation or mismatch check between the broker's `ALLOW` and the
subsequent `subprocess.run(["git", "push", ...])` call — the
`ALLOW`-derived `PushPermissionResult` is consumed once, immediately,
with no re-check of HEAD/branch/unpushed-count/task-ID against the
values bound into the original request.

**Severity assessment:** the gap between decision and dispatch is a
handful of synchronous Python statements (a `print()` on the ordinary
path, nothing on the staged path) with no intervening I/O that a
single-threaded, single-agent-locked CLI invocation would itself
introduce (concurrent-process races are separately, explicitly
out-of-scope per PBPC-REQ-055). No exploit was constructed or attempted
against this gap (doing so would require an external, concurrent actor
mutating local Git state mid-invocation, which 148F's scope and time
budget did not extend to). This is a genuine, traceable contract
non-conformance — not something 148E's phase report acknowledges —
but with low practical severity under the current single-agent
execution model. Classified **NON-BLOCKING**. Recommend a bounded
148F.x-scoped repair phase to implement Section 17's re-observation
step (or, alternatively, a contract amendment narrowing Section 17's
applicability if a future phase determines re-observation is
unnecessary under the single-agent-lock model — that determination is
explicitly **not** made by 148F, which does not amend PBPC-001).

No other Blocking, Non-Blocking, or Observation findings were
identified.

## 36. Regression Results

| Suite | Result |
|---|---|
| `test_permission_broker_push_production_consumption.py` + `test_push.py` + `test_staged_file_aware_push.py` + `test_commit_push_gate.py` + `test_push_phase_report_identity_137f1.py` + `test_post_push_canonicalization.py` + `test_push_state_reconciliation.py` + 148F's own new suite | 143 passed |
| `test_commit_push_preflight.py` + `test_commit_push_preflight_review.py` (additional push suites discovered by independent search) | 74 passed |
| Permission Broker Foundation/applicability/composition/rule-framework + 148C.7/148C.8 verification suites | 333 passed |
| `test_permission_broker.py` + CLI + command-path design/prototype + observation hardening/verification + verification-compatibility | 551 passed |
| Runtime context/architecture/contract/verification + introspection + snapshot + contract | 903 passed |
| 148F's own independent suite (standalone run) | 11 passed |
| `python -m pytest -m fast_green -n auto -q` | **4391 passed, 0 failed** — unchanged from 148D/148E's reported baseline |

No suppressed or skipped failures. No test was modified or removed by
148F (148F only added one new file:
`tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py`,
which is `slow`/`integration`-marked and therefore not part of the
`fast_green` count above, consistent with that count remaining
unchanged from 148E's own reported baseline).

## 37. Production Source and Contract Boundary (148F itself)

```
git diff --name-only HEAD -- src/pcae/            -> (empty)
git diff --name-only HEAD -- docs/contracts/      -> (empty)
```

148F changed zero files under `src/pcae/**` and zero files under
`docs/contracts/**`. PBPC-001 remains v1.2. PBPA-001 remains v1.0.

## 38. Verification Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — PBPC-001 v1.2 PRODUCTION CONSUMPTION CONFORMS**

Every real `git push` dispatch reachable through `pcae push` is
independently confirmed to be non-bypassably gated by a fresh,
canonical, PBPC-001 v1.2-conformant Permission Broker evaluation whose
result must be a genuine `ALLOW`; `DENY`, `HUMAN_REVIEW`, broker
evaluation failure, and malformed/duck-typed results are all
independently confirmed to produce zero dispatch on both paths. Two
NON-BLOCKING findings (F-148F-1, F-148F-3) and one OBSERVATION
(F-148F-2) were identified; none are Blocking.

## 39. Chapter 148 Readiness Assessment

| Obligation | Status |
|---|---|
| PBPC contract complete | ✅ v1.2, frozen |
| PBPA complete | ✅ v1.0, frozen |
| B-1 closed | ✅ CLOSED (independently re-confirmed: `POL-004` non-applicable to `execution_class=mutation`, not applicability=ALLOW; `approval_present` remains `False`, never the cause) |
| Implementation complete | ✅ (148E, both dispatch sites) |
| Independent verification complete | ✅ (this phase, 148F) |
| Both push paths gated | ✅ |
| No outstanding Blocking findings | ✅ (two Non-Blocking, one Observation, both/all recommended for a future bounded repair, not Blocking to Chapter 148) |
| Runtime unchanged | ✅ Observed / observe / unavailable |
| No deferred Chapter-148-specific implementation debt | ⚠️ Two Non-Blocking findings (F-148F-1, F-148F-3) exist and should be tracked, but are assessed as not Chapter-148-closure-blocking given their severity analysis above |

Prompt Generation (Phase 45F, `partially_ready`) is explicitly **not**
a Chapter 148 obligation and remains deferred (Section 40).

**Assessment: Chapter 148 is ready to proceed toward its next
readiness/certification step**, provided the next phase either (a)
opens a bounded repair phase for F-148F-1/F-148F-3 first, or (b)
explicitly records both as accepted, tracked technical debt as part of
Chapter 148's closure. **148F does not itself decide between (a) and
(b)** — that decision belongs to the next phase, per this phase's scope
boundary ("Do not certify or close Chapter 148").

## 40. Prompt Generation — Deferred Strategic Observation (Preserved)

Prompt Generation / Prompt Creation (Phase 45F) remains
`partially_ready`: design/data-model exists, live prompt-generation
pipeline inactive, prompt dispatch inactive, agent invocation inactive.
Preserved as a **DEFERRED STRATEGIC OBSERVATION** for post-Chapter-148
reassessment, per prior phases' framing. Not implemented, redesigned,
or advanced by 148F. `generated ≠ approved ≠ dispatched ≠ executed`
preserved.

## 41. Recommended Next Phase

Given `VERIFIED WITH NON-BLOCKING FINDINGS` and zero Blocking findings,
the canonical next phase is a Chapter 148 readiness/operational
assessment step — consistent with this repository's established
pattern of following an independent-verification phase with a
readiness-assessment phase (e.g., 148C.7 → 148C.8; 148D → 148E).
Recommended:

**148G — Permission Broker Production Consumption Operational
Readiness / Chapter 148 Assessment**, which should explicitly resolve
Findings F-148F-1 and F-148F-3 (either via a bounded repair sub-phase,
or an explicit, recorded acceptance of them as tracked technical debt)
before any Chapter 148 certification/closure claim is made. Prompt
Generation (Phase 45F) remains the leading deferred candidate for
strategic capability reassessment **after** Chapter 148 reaches its
canonical closure point — not before, and not as part of 148F or 148G.

## 42. Explicit Confirmations

- PBPC-001 v1.2 production consumption was independently verified
  rather than trusted from Phase 148E.
- PBPA-001 v1.0 remains unchanged.
- 148C-B-1 remains CLOSED; no independent evidence in this phase
  disturbed that finding.
- No production code was modified by Phase 148F.
- Every real `git push` dispatch reachable through `pcae push` requires
  a fresh, valid Permission Broker `ALLOW`, independently verified.
- `DENY` cannot dispatch. `HUMAN_REVIEW` cannot dispatch. Broker
  `evaluate()` failure cannot dispatch. Broker *construction* failure
  cannot dispatch either, though its failure mode is ungraceful
  (F-148F-1).
- Malformed and duck-typed broker results cannot dispatch.
- No caller-selectable policy set exists.
- `execution_class` remains canonically `mutation`, with no caller
  override surface.
- `approval_present` remains `False`.
- `simulation_only` remains `True`.
- No POL-001..012 meaning was changed. POL-004 remains unweakened.
  POL-005 remains unweakened.
- Mechanical/structural push protections (force-push, protected-staged-
  file, phase-report trust/identity) remain enforced and are not
  overridable by a genuine broker `ALLOW`.
- Interactive Workflow Confirmation remains independent (zero
  references in `push.py`).
- Authority Evaluation / AESIC remains disclosure-only (zero references
  in `push.py`).
- No Runtime Enforcement behavior was changed (zero references in
  `push.py`; Runtime Enforcement regression: 903 passed).
- No durable Permission Broker decision artifact was added.
- Prompt Generation remains design-only / `partially_ready` and
  DEFERRED for post-Chapter-148 reassessment. No Prompt Generation,
  Prompt Dispatch, or agent invocation capability was implemented.
- Runtime remains Observed, maximum capability remains `observe`, and
  execution availability remains `unavailable`.
