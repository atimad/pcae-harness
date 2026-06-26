# Phase 88R.1 — Broker Test Task-Contract Decoupling

## 1. Purpose

Repair `tests/test_permission_broker.py` so tests that require active-task-present broker
behavior use an isolated temporary repository root instead of the live `REPO_ROOT`. This
eliminates a latent coupling between broker test outcomes and the repository's idle/active
state, restoring fast-green and quick-tier stability after `pcae task finish` returns the
repo to idle.

## 2. Scope

- **In scope**: `tests/test_permission_broker.py` (test design repair only)
- **In scope**: Documentation artifact
- **In scope**: `PROJECT_STATUS.md`, `CHANGELOG.md`, task lifecycle files
- **Out of scope**: `src/pcae/core/permission_broker.py` (no source behavior changes)
- **Out of scope**: `src/pcae/core/shell_gate.py`, any shell wrappers, backend invocations,
  prompt/capture/intake/adoption, `src/**` other than the above

## 3. Non-Goals

- Do not change broker decision priority
- Do not weaken no-active-task blocking
- Do not broaden permission broker authorization
- Do not start Phase 88S
- Do not implement Broker + Shell Gate integration
- Do not implement shell interception or install shell wrappers
- Do not modify shell configuration
- Do not invoke backends, send prompts, or capture outputs
- Do not raw git commit or raw git push

## 4. Root Cause

During Phase 88R, the 19 failing tests passed because `tasks/active/20260626-1706-88r-permission-broker-prototype.md`
was present in the repository. Tests called `_broker(...)` which internally called
`build_permission_broker(repo_root=REPO_ROOT, ...)`. The broker's `_detect_task_contract(REPO_ROOT)`
found the active task file and allowed the broker to proceed past the task-contract gate.

After `pcae task finish` moved the task to `tasks/done/`, `REPO_ROOT` returned to idle state
(no active task). On the next test run, `_detect_task_contract(REPO_ROOT)` returned `None`,
and the broker correctly applied its priority-4 rule:

```
if requested_action in BPE_MUTATING_ACTIONS and task_contract is None:
    return "blocked_by_task_contract"
```

The 19 tests expected downstream decisions (`allow_preflight_only`, `requires_more_evidence`,
`requires_human_review`, `blocked_by_scope`) that are only reachable after the task-contract
gate is passed. They received `blocked_by_task_contract` instead and failed.

## 5. Why Broker Behavior Was Correct

The broker correctly blocked all mutating actions when no active task was present. This is
the intended governance invariant: without an active task contract, no mutation, push, commit,
adoption, rollback, or storage-write action may proceed. The priority order documented in
`_broker_decide` is:

1. Shell gate hard blocks
2. Explicit evidence failures (health, check, doctor, tests, push-check)
3. Test run lock
4. **Missing active task for mutating actions** ← blocks before scope/evidence/human-review
5. Scope preflight denial
6. Missing evidence collection
7. Human review gate
8. `allow_preflight_only`

The broker returned the correct decision for an idle repository. No broker logic needed fixing.

## 6. Why Test Design Was Wrong

The tests for Groups A–D (allow_preflight_only, requires_more_evidence, requires_human_review,
blocked_by_scope) implicitly assumed that an active task would always be present in `REPO_ROOT`.
This assumption held during Phase 88R development (task was active) but broke as soon as the
phase completed and the repo returned to idle. The tests should have been written to supply
their own isolated task-active environment rather than inheriting live repo state.

## 7. Fixture Design

A `tmp_task_root` pytest fixture was added to `tests/test_permission_broker.py`:

```python
@pytest.fixture
def tmp_task_root(tmp_path: Path) -> Path:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True)
    (active_dir / "test-active-task.md").write_text(
        "## Allowed Files\n"
        "- src/**\n"
        "- tests/**\n"
        "- docs/**\n"
        "## Forbidden Files\n"
    )
    return tmp_path
```

Key design choices:
- Uses pytest's built-in `tmp_path` fixture for automatic isolation and cleanup per test
- Minimal task contract: only `## Allowed Files` and `## Forbidden Files` sections, matching
  what `_detect_task_contract` actually parses
- Allowed patterns cover all files used by failing tests (`src/x.py`, `tests/test_x.py`,
  `docs/HOWTO.md`)
- `README.md` deliberately omitted from `## Forbidden Files` — it is already in the global
  `_SPF_POLICY_FORBIDDEN_FILES` tuple, so scope tests that rely on README.md being denied
  continue to work correctly via the global policy
- Fixture is module-local (not in `conftest.py`) since it is only used in this file

## 8. Tests Updated

19 test methods updated to receive `tmp_task_root` as a fixture parameter and pass
`root=tmp_task_root` to `_broker()` / `_pb()`:

**Group A — TestAllowPreflightOnly (5 tests):**
- `test_source_mutation_with_health_check`
- `test_test_mutation_with_health_check`
- `test_docs_mutation_with_health_check`
- `test_push_with_full_evidence_and_human_review`
- `test_commit_with_evidence_and_human_review`

**Group B — TestRequiresMoreEvidence (7 tests):**
- `test_source_mutation_missing_health`
- `test_source_mutation_missing_check`
- `test_push_missing_push_check`
- `test_missing_evidence_list_populated`
- `test_health_missing_in_evidence_list`
- `test_check_missing_in_evidence_list`
- `test_hard_block_present_is_false`

**Group C — TestRequiresHumanReview (6 tests):**
- `test_push_without_human_review`
- `test_commit_without_human_review`
- `test_adoption_without_human_review`
- `test_rollback_without_human_review`
- `test_storage_write_without_human_review`
- `test_hard_block_present_is_false`

**Group D — TestScopePreflight (1 test):**
- `test_policy_forbidden_file_blocked_by_scope`

Helper changes:
- `_pb()` gained an optional `root: Path = REPO_ROOT` parameter; `repo_root` now uses `root`
- `_broker()` passes `**kwargs` through unchanged, so `root=tmp_task_root` propagates

## 9. No-Active-Task Behavior Preserved

`TestBlockedByTaskContract` was not modified. Its three tests continue to use an explicit
`/tmp/pcae-88r-test-no-task` directory (an empty directory with no `tasks/active/` content)
and directly call `build_permission_broker(repo_root=tmp_root, ...)`. These tests remain the
authoritative verification that:
- All mutating actions return `blocked_by_task_contract` when no task is present
- `active_task_detected` is `False` in that case
- `hard_block_present` is `True`
- Read actions are not blocked

`TestEvidenceFailures.test_health_failure_priority_over_task_contract` also continues to use
the explicit no-task root to verify that health failure (priority 2) takes precedence over
the task-contract check (priority 4).

`TestShellGateHardBlocks.test_hard_block_takes_priority_over_no_task` similarly continues to
verify shell gate hard blocks (priority 1) take precedence over the task check (priority 4).

## 10. Task-Active Behavior Isolated

The 19 updated tests now use `tmp_task_root` (isolated per-test temp dir) rather than
`REPO_ROOT`. Each test receives a fresh temp directory with a minimal valid task contract.
Tests no longer depend on the live repository's active-task state. They pass equally whether
the repo is idle, mid-phase, or has any other task active.

## 11. Validation Results

**Targeted broker tests:**
```
150 passed in 1.23s
```

**Shell-gate regression:**
```
449 passed, 0 failed, 7921 deselected in 18.73s
```

**Fast-green:**
```
2384 passed in 23.31s
```

**Quick tier:**
See final phase report.

**Full suite:**
See final phase report.

## 12. Remaining Limitations

- `TestBlockedByTaskContract` uses a fixed path `/tmp/pcae-88r-test-no-task` rather than
  `tmp_path`. This is pre-existing behavior from 88R; it is not a regression and is out of
  scope for this repair phase. Could be improved in a future hygiene phase.
- Some tests in other classes (e.g., `TestPerformedFlagInvariants.test_flag_always_false_for_mutation`)
  still call `_broker("source_mutation", ...)` without `tmp_task_root`. These are intentionally
  left alone: they test that performed flags are False regardless of decision, and the decision
  (`blocked_by_task_contract` in idle state) does not affect flag correctness.

## 13. Recommended Next Phase

**88S — Broker + Shell Gate Integration Design**

Design the integration between the permission broker and the shell gate classifier, defining
how the broker's decision feeds back into the shell gate's allow/block behavior and how the
combined system presents a unified governance interface.
