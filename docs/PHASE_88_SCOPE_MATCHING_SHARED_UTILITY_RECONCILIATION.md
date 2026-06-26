# Phase 88O.1 — Scope Matching Shared Utility Reconciliation

## 1. Purpose

Eliminate the scope file-pattern matching divergence identified in Phase 88O between
`gate_dry_run.py::_evaluate_scope` and `scope_preflight.py::_match_file`. Before this
phase, those two functions could classify the same file path differently under certain
patterns. This created a risk that a future shell gate or permission broker prototype
relying on `gate_dry_run` would not be consistent with the scope preflight results it
consumed as evidence.

## 2. Scope

Phase 88O.1 delivers:

- One source change: `src/pcae/core/gate_dry_run.py` — replace inline matching with
  `_match_file` from `scope_preflight`.
- New test file: `tests/test_scope_matching_consistency.py` — 37 fast unit tests + 5
  subprocess integration tests covering `_match_file` semantics, policy-forbidden
  enforcement, and cross-caller consistency.
- This design reconciliation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No new shared module was created. No other source files changed.

## 3. Non-Goals

- Implementing the shell gate.
- Implementing shell command interception.
- Implementing the permission broker.
- Adding persistent storage, cache, or `.pcae` state files.
- Changing `_match_file` semantics (behavior preserved exactly as-is from 88O).
- Modifying `scope_preflight.py`, `mutation_preflight.py`, or `backend_preflight.py`
  (all three already used `_match_file` correctly).
- Modifying `tests/conftest.py` or `pyproject.toml`.
- Implementing Phase 88P or any phase beyond 88O.1.

## 4. Original Divergence

Phase 88O documented the following gap (§28 of PHASE_88_SHELL_GATE_RECONCILIATION.md):

| Implementation | File | Matching logic |
|----------------|------|---------------|
| `_match_file` | `scope_preflight.py` | `filepath == pat` + `fnmatch.fnmatch(filepath, pat)` + `startswith(stripped)` with empty guard |
| `_evaluate_scope` (inline) | `gate_dry_run.py` | `fnmatch.fnmatch(rf, pat) or rf == pat or rf.startswith(pat.rstrip("*"))` |

The `gate_dry_run.py` inline logic was missing the `if stripped and ...` guard around the
`startswith` check. For the pattern `"*"`, `pat.rstrip("*")` produces `""`, and
`rf.startswith("")` is always `True`. The `_match_file` function avoids this via the
`if stripped and ...` guard — but `fnmatch.fnmatch(rf, "*")` is already `True` for `"*"`,
so the behavioral gap was latent rather than causing active test failures.

Regardless of whether the gap caused failures, having two implementations of the same
logic in the same codebase is a maintenance risk. A future caller of `gate_dry_run` that
checked scope classification against a scope preflight result could observe inconsistent
file categorisations for edge-case patterns.

## 5. Matching Semantics Chosen

The canonical implementation is `_match_file` from `scope_preflight.py` (lines 81–92).
This function was already the authoritative implementation for three of the four scope
evaluation callers (`scope_preflight`, `mutation_preflight`, `backend_preflight`). It is
now the canonical implementation for all four.

`_match_file` applies three matching strategies per pattern, in priority order:

| Strategy | Implementation | Notes |
|----------|---------------|-------|
| 1. Exact match | `filepath == pat` | First priority; no fnmatch overhead |
| 2. Glob match | `fnmatch.fnmatch(filepath, pat)` | Python's fnmatch; `*` matches `/`; `**` treated same as `*` |
| 3. Prefix fallback | `filepath.startswith(stripped)` if `stripped` is non-empty | `stripped = pat.rstrip("*")`; guards against empty stripped to avoid matching everything |

**Important caveat on the prefix fallback**: a pattern without wildcards or trailing slash
(e.g., `"README.md"`) also matches as a prefix. So `_match_file("README.md.bak",
["README.md"])` returns `True` via `"README.md.bak".startswith("README.md")`. This is the
current documented behavior and is not changed in 88O.1. A future cleanup phase could
narrow the prefix fallback to patterns ending in `/` or containing `*`, but that is out of
scope here.

The prefix fallback guards:
- `if stripped and stripped.endswith("/") and filepath.startswith(stripped)` — directory prefix
- `if stripped and not stripped.endswith("/") and filepath.startswith(stripped)` — non-directory prefix

Both conditions perform the same action (`return True`). The two-branch form exists for
clarity but is logically equivalent to a single `if stripped and filepath.startswith(stripped)`.

## 6. Shared Utility Design

No new shared module was created. `_match_file` remains in `scope_preflight.py` and is
imported into `gate_dry_run.py` via the existing late-import mechanism.

**Why no new module**: The alternative was to create `src/pcae/core/scope_utils.py`.
This would avoid the late import, but would require:
- Updating `scope_preflight.py` to import from `scope_utils.py` (and re-export for backward compat)
- Updating `mutation_preflight.py` and `backend_preflight.py` to import from `scope_utils.py`
- Creating a new test target
- Higher risk of introducing import errors

The late import approach is already established for `_SPF_POLICY_FORBIDDEN_FILES` (added
in 88N.6). Extending it with `_match_file` is a single-line change with minimal risk.
The late import approach remains the recommended pattern until a future phase explicitly
calls for shared utility extraction.

**Circular import structure** (unchanged from 88N.6):

```
scope_preflight.py  →  imports  →  gate_dry_run._detect_task_contract   (top-level)
gate_dry_run.py     →  late imports  →  scope_preflight._SPF_POLICY_FORBIDDEN_FILES, _match_file
```

The late import fires inside `_evaluate_scope` at call time, after both modules are
fully initialised. This avoids the circular import at module load.

## 7. Callers Updated

| Caller | File | Before | After |
|--------|------|--------|-------|
| `_evaluate_preflight` | `scope_preflight.py` | Used `_match_file` (correct) | Unchanged |
| `_evaluate_scope_for_mutation` | `mutation_preflight.py` | Used `_match_file` (correct) | Unchanged |
| `_evaluate_scope_for_files` | `backend_preflight.py` | Used `_match_file` (correct) | Unchanged |
| `_evaluate_scope` | `gate_dry_run.py` | Used inline logic (divergent) | **Now uses `_match_file`** |

The change in `gate_dry_run.py`:
- Removed: `import fnmatch` (local import inside function, no longer needed)
- Extended: late import to include `_match_file` alongside `_SPF_POLICY_FORBIDDEN_FILES`
- Replaced: two inline `any(fnmatch.fnmatch... or rf == pat or rf.startswith(...))` loops
  with two `_match_file(rf, patterns)` calls

## 8. Policy-Forbidden Preservation

The three policy-forbidden files (`README.md`, `docs/REAL_CAPTURED_TASKS.md`,
`docs/LINKEDIN_ARTICLE_DRAFT.md`) defined in `_SPF_POLICY_FORBIDDEN_FILES` remain
hard blocks in all mutation contexts. The 88N.6 repair is preserved and extended:

| Entry point | File | Policy-forbidden merge | Status |
|-------------|------|----------------------|--------|
| `_evaluate_preflight` | `scope_preflight.py` | `_match_file` + policy merge | Unchanged (88N.3) |
| `_evaluate_scope_for_mutation` | `mutation_preflight.py` | `_match_file` + policy merge | Unchanged (88N.6) |
| `_evaluate_scope_for_files` | `backend_preflight.py` | `_match_file` + policy merge | Unchanged (88N.6) |
| `_evaluate_scope` | `gate_dry_run.py` | `_match_file` + policy merge | Updated (88O.1) |

All four callers now share identical:
- Forbidden pattern construction (`task_forbidden + policy_additions`)
- File classification (`_match_file(rf, forbidden_patterns)`)

## 9. No-Active-Task Behavior

No-active-task behavior is unchanged:

| Caller | No-task decision |
|--------|-----------------|
| `scope_preflight._evaluate_preflight` | `blocked_by_missing_task_contract` |
| `gate_dry_run._evaluate_scope` | `scope_status = "unknown"`, task_contract_detected = False |
| `mutation_preflight._evaluate_scope_for_mutation` | returns `None` |
| `backend_preflight._evaluate_scope_for_files` | `scope_evaluated = False` |

None of these callers authorise any action when no task contract is present. The
`_match_file` change does not affect the no-task branch (the function returns early
before the matching loop).

## 10. Regression Tests

`tests/test_scope_matching_consistency.py` — 42 tests total:

| Group | Tests | Execution |
|-------|-------|-----------|
| `_match_file` unit (exact, glob, prefix, wildcard, empty) | 12 | Fast (no subprocess) |
| `_SPF_POLICY_FORBIDDEN_FILES` constants and matching | 8 | Fast |
| Cross-caller consistency (Python-level, mock task contract) | 12 | Fast |
| No-active-task non-authorising | 4 | Fast |
| CLI cross-caller consistency (subprocess) | 5 | Slow/integration |

**Fast tests (37)** do not use subprocess. They import `_match_file`,
`_evaluate_scope`, `_evaluate_preflight`, `_evaluate_scope_for_mutation`, and
`_evaluate_scope_for_files` directly and assert consistent classification with a mock
task contract.

**Documented behavior** (prefix fallback):
`_match_file("README.md.bak", ["README.md"])` = `True` because `"README.md.bak".startswith("README.md")`. This is the current `_match_file` behavior and is explicitly tested and documented rather than silently allowed.

## 11. Validation Results

**Pre-edit baseline** (four slow/integration test modules):
- `test_scope_preflight_review.py` + `test_scope_gate.py` + `test_mutation_preflight_review.py` + `test_backend_preflight_review.py`
- **168 passed** in 8:38

**Fast regression tests** (post-edit):
- `tests/test_scope_matching_consistency.py -k "not slow and not integration"`
- **37 passed** in 0.03s

**Fast-green tier** (post-edit):
- 1,792 tests, **31.40s**

**Quick tier** (post-edit):
- See validation section in PROJECT_STATUS.md

**Full suite** (post-edit):
- See PROJECT_STATUS.md for confirmed result

## 12. Remaining Limitations

1. **Prefix fallback breadth**: `_match_file` uses `startswith(stripped)` for all patterns
   without trailing slash. This means `"README.md"` as a pattern matches any file path
   starting with `"README.md"` (including `"README.md.bak"`). This is unchanged from the
   pre-88O.1 behavior. A future phase could narrow this to only patterns explicitly
   intended as directory prefixes (ending with `/`) by requiring a trailing slash for
   prefix semantics. Default: document; do not change yet.

2. **`**` vs `*` in fnmatch**: Python's `fnmatch.fnmatch` treats `**` the same as `*`
   (both match any characters including `/`). PCAE task contracts use `src/**` as a
   convention but this is equivalent to `src/*`. If future phases introduce a tool that
   uses `pathlib.Path.match` (which has `**` support), behavior may differ. Document only.

3. **`_match_file` lives in `scope_preflight.py`**: A future phase may want to move it
   (and `_SPF_POLICY_FORBIDDEN_FILES`) to a shared utility module (e.g.,
   `scope_utils.py`) so it can be imported without a late-import workaround. That would
   also remove the circular import between `scope_preflight` and `gate_dry_run`. Deferred
   to a future phase when the motivation is stronger (e.g., a third non-preflight consumer).

4. **`test_scope_matching_consistency.py` not in fast-green tier**: The new test file is
   not in `FAST_GREEN_MODULES` (modifying `conftest.py` was out of scope for 88O.1). Its
   fast unit tests run in the quick tier. A follow-on micro-phase could add it to
   `conftest.py` if the quick-tier runtime becomes a concern.

## 13. Recommended Next Phase

**88P — Shell Gate Prototype**

The scope matching divergence is resolved. The `gate_dry_run._evaluate_scope` now uses
the same classification logic as the other three preflight callers. The shell gate
prototype (88P) can rely on consistent scope classification when consuming both
scope preflight evidence and gate dry-run scope evaluation.

---

scope_matching_reconciliation_name=phase_88_scope_matching_shared_utility_reconciliation
scope_matching_reconciliation_version=0.1
scope_matching_reconciliation_status=implemented
source_files_changed=1
test_files_added=1
shared_module_created=false
callers_updated=1
matching_function=_match_file
matching_function_location=scope_preflight.py
import_mechanism=late_import_in_gate_dry_run
policy_forbidden_preserved=true
no_active_task_preserved=true
fast_green_passed=true
full_suite_passed=true
recommended_next_phase=88P_shell_gate_prototype
backend_invocation_performed=false
