# Phase 88N.3 Scope Preflight Review Full-Suite Baseline Repair

## 1. Purpose

Repair 2 pre-existing failures in `tests/test_scope_preflight_review.py` to restore a
green full-suite baseline before shell-gate design work begins. The failures were
confirmed pre-existing on the 88N.1 baseline and not regressions from 88N.2.

## 2. Scope

Phase 88N.3 delivers:

- A narrow implementation change to `src/pcae/core/scope_preflight.py`:
  `_SPF_POLICY_FORBIDDEN_FILES` constant and merge into `_evaluate_preflight`.
- This documentation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No new CLI commands. No new config. No schema changes. No storage. No test changes
(tests were already correctly asserting the intended behavior).

## 3. Non-Goals

- Permission broker implementation.
- Shell gate implementation (88O, deferred).
- Changes to any other preflight module (backend, mutation, commit, push).
- Changes to `tests/test_scope_preflight_review.py` — tests correctly state the
  intended policy; the implementation was wrong.
- Addition of global forbidden files beyond the three PCAE policy-protected documents.

## 4. Failure Identification

### 4.1 Pre-existing on 88N.1 and 88N.2 Baselines

The 2 failures appeared in the 88N.2 full-suite run (7,717 passed, 2 failures). They
were confirmed not introduced by 88N.2 — both 88N.1 and 88N.2 task contracts omitted
`docs/LINKEDIN_ARTICLE_DRAFT.md` from their forbidden file lists.

### 4.2 Failing Tests

| Test | Expected | Got |
|------|----------|-----|
| `test_forbidden_exact_match_linkedin` | `blocked_by_scope`, file in `matched_forbidden_files` | `requires_more_evidence` |
| `test_multi_file_two_allowed_one_forbidden` | `deny_preflight` or `blocked_by_scope` | `requires_human_review` |

Both failures involve `docs/LINKEDIN_ARTICLE_DRAFT.md` as the requested file.

## 5. Root Cause

### 5.1 Scope Preflight is Purely Task-Contract-Driven

`_evaluate_preflight` in `src/pcae/core/scope_preflight.py` sources allowed and
forbidden patterns exclusively from the active task contract:

```python
allowed_patterns = task_contract["allowed_files"]
forbidden_patterns = task_contract["forbidden_files"]
```

When a file is not listed in either, it is classified as "unknown."

### 5.2 Missing Policy File in 88N.1 and 88N.2 Task Contracts

Both the 88N.1 and 88N.2 task contracts explicitly forbade `README.md` and
`docs/REAL_CAPTURED_TASKS.md`, but omitted `docs/LINKEDIN_ARTICLE_DRAFT.md`:

**88N.1 Forbidden Files:**
- `README.md`
- `src/pcae/core/**`
- `docs/REAL_CAPTURED_TASKS.md`
- `.pcae/**`

**88N.2 Forbidden Files:**
- `README.md`
- `docs/REAL_CAPTURED_TASKS.md`
- `.pcae/**`

With `docs/LINKEDIN_ARTICLE_DRAFT.md` absent from the forbidden list:

- `test_forbidden_exact_match_linkedin`: action `docs_mutation`, only unknown files →
  `requires_more_evidence`. Test asserts `blocked_by_scope`. **FAIL.**
- `test_multi_file_two_allowed_one_forbidden`: `PROJECT_STATUS.md` (allowed) +
  `CHANGELOG.md` (allowed) + `docs/LINKEDIN_ARTICLE_DRAFT.md` (unknown) →
  `requires_human_review`. Test asserts `deny_preflight` or `blocked_by_scope`. **FAIL.**

### 5.3 Why README.md and docs/REAL_CAPTURED_TASKS.md Tests Passed

Both files were consistently present in the 88N.1 and 88N.2 task forbidden lists, so
their tests always had a concrete task-provided forbidden pattern to match against. The
inconsistency was specific to `docs/LINKEDIN_ARTICLE_DRAFT.md`.

## 6. Fix

### 6.1 Policy-Protected Files Constant

Added to `src/pcae/core/scope_preflight.py`:

```python
# Files that PCAE policy always forbids, independent of the active task contract.
# These protect documents that agents must never modify regardless of task scope.
_SPF_POLICY_FORBIDDEN_FILES: tuple[str, ...] = (
    "README.md",
    "docs/REAL_CAPTURED_TASKS.md",
    "docs/LINKEDIN_ARTICLE_DRAFT.md",
)
```

All three files represent PCAE governance documents that no task should ever modify.
Including all three (not just the failing one) makes the policy explicit and prevents
the same class of omission in future task contracts from causing new test failures.

### 6.2 Merge at Evaluation Time

In `_evaluate_preflight`, after reading the task contract forbidden list:

```python
task_forbidden = list(task_contract["forbidden_files"])
policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
forbidden_patterns = task_forbidden + policy_additions
```

The policy additions are deduplicated against the task contract list to avoid redundant
entries in `forbidden_files` output. The effective `forbidden_patterns` is used for all
file matching and returned in the `forbidden_files` response field.

### 6.3 No Test Changes Required

The tests were already correctly asserting the intended PCAE policy. The implementation
was the source of the divergence. No test was weakened, deleted, or relaxed.

## 7. Validation

### 7.1 Targeted (Before Fix)

Without the fix and with the 88N.3 task active (which includes `docs/LINKEDIN_ARTICLE_DRAFT.md`
in its own forbidden list), all 63 tests pass. The fix makes the behavior consistent
regardless of whether the active task contract mentions the policy files.

### 7.2 Targeted (After Fix)

```
python -m pytest tests/test_scope_preflight_review.py -q
63 passed in 37.53s
```

### 7.3 Related Tests

```
python -m pytest tests -k "scope_preflight or preflight_scope" -q
133 passed, 7586 deselected in 76.14s
```

No regressions in adjacent preflight modules.

### 7.4 Quick Tier

```
python -m pytest -m "not slow and not phase_closure" -n auto -q
7012 passed in 275.35s (0:04:35)
```

### 7.5 Full Suite

```
python -m pytest -n auto -q
7719 passed in 1693.48s (0:28:13)
```

Full-suite baseline: **7,719 passed, 0 failures.**

Prior baseline (88N.2): 7,717 passed, 2 failures. The 2 failures are now fixed (+2 = 7,719).

## 8. Safety Boundary

The fix is contained to `src/pcae/core/scope_preflight.py`. It does not:

- Add or remove CLI commands.
- Change the scope preflight's JSON output schema.
- Modify how allowed files are evaluated.
- Affect the `blocked_by_missing_task_contract` path (no task present).
- Change the commit, push, backend, or mutation preflight modules.
- Introduce runtime storage, backend invocation, or shell interception.
- Implement the permission broker or shell gate.

Files that were already forbidden by a task contract remain forbidden. Files that were
already allowed remain allowed. The only behavioral change: three governance documents
are now always forbidden regardless of whether the active task contract explicitly lists
them.

## 9. Recommended Next Phase

**88O — Shell Gate Design Reconciliation**

Phase 88O was deferred from 88N.2 pending a green full-suite baseline. With the
baseline now restored (7,719 passed, 0 failures), 88O may proceed.

88O should reconcile the Phase 87 shell gate architecture with the concrete Phase 88
explicit preflight layer, define how a future shell gate interacts with scope preflight
results, and document the boundary between read-only preflight and execution control —
without implementing the gate.

---

scope_preflight_baseline_repair_name=phase_88n3_scope_preflight_baseline_repair
scope_preflight_baseline_repair_version=0.1
scope_preflight_baseline_repair_status=implemented
root_cause=docs_linkedin_article_draft_missing_from_task_contract_forbidden_list
fix_location=src/pcae/core/scope_preflight.py:_SPF_POLICY_FORBIDDEN_FILES
fix_type=policy_protected_files_constant
tests_repaired=2
full_suite_result=7719_passed_0_failures
recommended_next_phase=88O_shell_gate_design_reconciliation
backend_invocation_performed=false
source_mutation_authorized=true_for_scope_preflight_policy_fix_only
test_mutation_authorized=false
execution_authorized=false
