# Phase 88N.6 — Preflight Policy-Forbidden Consistency Repair

## 1. Purpose

Restore the full-suite green baseline by ensuring that PCAE's three policy-forbidden governance
files (`README.md`, `docs/REAL_CAPTURED_TASKS.md`, `docs/LINKEDIN_ARTICLE_DRAFT.md`) are
consistently enforced as forbidden by all scope evaluation functions — not only by the dedicated
scope preflight, but also by mutation preflight, backend preflight, and the gate dry-run.

## 2. Scope

Three source files changed:

- `src/pcae/core/mutation_preflight.py` — `_evaluate_scope_for_mutation`
- `src/pcae/core/backend_preflight.py` — `_evaluate_scope_for_files`
- `src/pcae/core/gate_dry_run.py` — `_evaluate_scope`

No test files changed. No test assertions weakened. No tests deleted.

## 3. Non-Goals

- No permission broker implementation.
- No shell gate implementation.
- No shell interception.
- No backend invocation.
- No prompts, capture, intake, or adoption.
- No modification to `src/pcae/core/scope_preflight.py` — it was already correct.
- No change to `_SPF_POLICY_FORBIDDEN_FILES` content.
- No change to the fast-green architecture from Phase 88N.5.
- Phase 88O not started.

## 4. Failure Summary

Full suite after Phase 88N.5: **7,726 passed, 10 failed**.

The 10 failing tests, all in subprocess-heavy (`slow`, `integration`) test files:

| Test | File |
|------|------|
| `test_docs_mutation_forbidden` | `test_mutation_preflight_review.py` |
| `test_source_mutation_forbidden` | `test_mutation_preflight_review.py` |
| `test_forbidden_file_blocks` | `test_mutation_preflight_review.py` |
| `test_multi_file_forbidden` | `test_mutation_preflight_review.py` |
| `test_forbidden_file_blocked` | `test_mutation_preflight.py` |
| `test_scope_denied_blocks` | `test_backend_preflight_review.py` |
| `test_forbidden_file_blocks` | `test_backend_preflight_review.py` |
| `test_multi_file_forbidden_blocks` | `test_backend_preflight_review.py` |
| `test_file_forbidden_scope_blocks` | `test_backend_preflight.py` |
| `test_source_mutation_forbidden_file` | `test_scope_gate.py` |

All 10 tests check that policy-forbidden files (`README.md`, `docs/REAL_CAPTURED_TASKS.md`,
`docs/LINKEDIN_ARTICLE_DRAFT.md`) produce `blocked_by_scope` or `out_of_scope` decisions from
their respective preflight/gate commands. All 10 were receiving `requires_human_review` or
`unknown` instead.

## 5. Baseline Inconsistency Analysis

The Phase 88N.4 full-suite baseline ("7,719 passed, 0 failures") was measured while the **88N.4
task was still active**. The 88N.4 task contract explicitly listed `README.md`,
`docs/REAL_CAPTURED_TASKS.md`, and `docs/LINKEDIN_ARTICLE_DRAFT.md` in its `## Forbidden Files`
section. Because the three scope evaluation functions consumed `task_contract["forbidden_files"]`
directly, these files appeared in the computed forbidden list — not because of policy enforcement,
but because the 88N.4 task contract happened to enumerate them.

The Phase 88N.5 task contract did not enumerate those files as forbidden (it only had `src/**` and
`.githooks/**`). When the 88N.5 full suite ran with that task active, the three policy-forbidden
files fell through as `unknown/partial` in the scope evaluation, producing `requires_human_review`
instead of `blocked_by_scope`.

**88N.4 baseline worktree verification**: running the same 10 failing tests against the d93bda54
worktree (without an active task) produced 66 failures — confirming that without an active task
that explicitly lists those files as forbidden, the tests fail at the 88N.4 source too. The "0
failures" baseline was task-state-dependent, not a property of the source.

## 6. Root Cause

Three scope evaluation functions did not include `_SPF_POLICY_FORBIDDEN_FILES` in their forbidden
pattern sets. Only `src/pcae/core/scope_preflight.py`'s `_evaluate_preflight` correctly merged the
constant. The other three functions read exclusively from `task_contract["forbidden_files"]`:

**`mutation_preflight.py` — `_evaluate_scope_for_mutation` (before)**:
```python
forbidden_patterns = task_contract["forbidden_files"]
```

**`backend_preflight.py` — `_evaluate_scope_for_files` (before)**:
```python
forbidden_patterns = task_contract["forbidden_files"]
```

**`gate_dry_run.py` — `_evaluate_scope` (before)**:
```python
forbidden_patterns = task_contract["forbidden_files"]
```

This meant: if a task contract did not explicitly list a policy-forbidden file, that file was not
forbidden from the perspective of those three evaluation functions.

`scope_preflight.py`'s `_evaluate_preflight` (the dedicated preflight command) had already
received this fix in Phase 88N.3. The mutation, backend, and gate evaluation functions were missed.

## 7. Repair Performed

Each of the three functions was updated to merge `_SPF_POLICY_FORBIDDEN_FILES` into the
forbidden patterns using the same deduplication pattern used by `scope_preflight.py`:

```python
task_forbidden = list(task_contract["forbidden_files"])
policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
forbidden_patterns = task_forbidden + policy_additions
```

**`mutation_preflight.py`**: `_SPF_POLICY_FORBIDDEN_FILES` added to the existing import from
`scope_preflight` (`_match_file`). No circular import risk — `mutation_preflight` already imports
from `scope_preflight`.

**`backend_preflight.py`**: Same approach. `_SPF_POLICY_FORBIDDEN_FILES` added to the existing
import from `scope_preflight`. No circular import risk.

**`gate_dry_run.py`**: `scope_preflight.py` imports `_detect_task_contract` from `gate_dry_run`.
Adding a top-level import in the reverse direction would create a circular import. Used a **late
import** (inside the `_evaluate_scope` function body) to avoid the circular dependency at module
load time:

```python
def _evaluate_scope(...):
    from pcae.core.scope_preflight import _SPF_POLICY_FORBIDDEN_FILES  # late import avoids circular dep
    task_forbidden = list(task_contract["forbidden_files"])
    policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
    forbidden_patterns = task_forbidden + policy_additions
    ...
```

Late imports in function bodies are safe in Python — both modules are fully initialized by the time
any function is called.

## 8. Scope / Mutation / Backend Preflight Consistency

After the repair, all four scope evaluation entry points enforce `_SPF_POLICY_FORBIDDEN_FILES`
consistently:

| Entry point | File | Policy-forbidden merge |
|-------------|------|------------------------|
| `_evaluate_preflight` | `scope_preflight.py` | Top-level (Phase 88N.3) |
| `_evaluate_scope_for_mutation` | `mutation_preflight.py` | Top-level import (88N.6) |
| `_evaluate_scope_for_files` | `backend_preflight.py` | Top-level import (88N.6) |
| `_evaluate_scope` | `gate_dry_run.py` | Late import (88N.6) |

## 9. Safety Behavior Preserved

The repair makes scope enforcement **more conservative** (more files blocked), not less:
- Policy-forbidden files that were previously `requires_human_review` are now `blocked_by_scope`.
- Files not in `_SPF_POLICY_FORBIDDEN_FILES` are unaffected.
- No file that was previously `blocked_by_scope` becomes allowed.
- No authorization flag changes (all remain `false`).
- No permission broker logic introduced.
- No shell gate logic introduced.

## 10. Fast-Green Preservation

Phase 88N.5 fast-green architecture is unchanged:
- `tests/conftest.py` unmodified.
- `tests/test_88n5_fast_green_validation.py` unmodified.
- `pyproject.toml` fast_green marker unmodified.
- All 17 fast-green validation tests continue to pass.
- Fast-green tier: 1,792 tests, 21.72s (confirmed post-repair).

## 11. Validation Results

**Targeted failing tests (181 tests total across 5 files)**:
- `test_mutation_preflight_review.py` — all pass
- `test_backend_preflight_review.py` — all pass
- `test_scope_gate.py` — all pass
- `test_backend_preflight.py` — all pass
- `test_mutation_preflight.py` — all pass
- Result: **181 passed, 0 failed** in 8:00

**Fast-green validation tests**:
- `tests/test_88n5_fast_green_validation.py` — 17 passed in 1.39s
- Fast-green tier (`-m "fast_green" -n auto`) — 1,792 passed in 21.72s

**Quick tier** (`-m "not slow and not phase_closure" -n auto`):
- **7,029 passed in 2:22**

**Full suite** (`-n auto`):
- See full-suite log at `/tmp/pcae-full-suite-88n6.log`

## 12. Remaining Limitations

- `_SPF_POLICY_FORBIDDEN_FILES` is defined in `scope_preflight.py` and imported via late import
  into `gate_dry_run.py`. If a future refactor moves the constant, both import sites must be
  updated.
- Policy-forbidden file enforcement applies only when a task contract is present. When no task
  is active, all four functions return `blocked_by_missing_task_contract` (scope/mutation/backend)
  or `unknown` (gate dry-run) — they do not enforce policy-forbidden files without a task.
- The duplicate `fnmatch` logic in `gate_dry_run.py`'s `_evaluate_scope` (different from
  `_match_file` in `scope_preflight.py`) is a known divergence not addressed in this phase.

## 13. Recommended Next Phase

**88O — Shell Gate Design Reconciliation**
