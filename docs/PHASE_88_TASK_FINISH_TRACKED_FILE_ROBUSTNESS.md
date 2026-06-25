# Phase 88N.1 Task Finish Tracked-File Robustness

## 1. Purpose

Fix `pcae task finish` so it handles untracked active task files safely. Before this
fix, if the active task contract file in `tasks/active/` had never been committed to
git, `pcae task finish --commit` would move the file to `tasks/done/` and then fail
trying to stage the old active path — because git had no record of a file to delete
there. This left the repository in a partial finish state that required manual recovery.

## 2. Scope

Phase 88N.1 delivers:

- A one-line logic change in `src/pcae/commands/task.py` (`run_task_finish`).
- 8 regression tests added to `tests/test_staged_file_aware_task_finish.py`.
- This documentation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No new CLI commands. No new config. No schema changes. No storage.

## 3. Non-Goals

- Permission broker implementation.
- Shell gate implementation.
- Full-suite optimization or test-run locking (reserved for 88N.2).
- Broad task lifecycle refactor.
- Changes to `finish_active_task` in `src/pcae/core/tasks.py`.
- Any change to the non-`--staged-file-aware` path of task finish.
- Any change to the `--commit` without `--staged-file-aware` path (that path already
  blocks on pre-existing changes before reaching the pathspec step).

## 4. 88M Failure Sequence

During Phase 88M completion, the following sequence produced the bug:

1. The 88M task contract was created in `tasks/active/` but never committed to git.
2. `pcae task finish --staged-file-aware --skip-checks --commit "..."` was called.
3. `finish_active_task` moved the task file: `tasks/active/...88m....md` →
   `tasks/done/...88m....md`.
4. The commit path built `paths_to_stage` including the OLD active path:
   `tasks/active/...88m....md`.
5. `git add -- tasks/active/...88m....md` failed:
   ```
   fatal: pathspec 'tasks/active/...88m....md' did not match any files
   ```
   The file no longer existed at that path, and git had no tracked record of it.
6. No commit was created.
7. The repository entered a partial finish state:
   - `tasks/active/` was empty (file moved to done).
   - `tasks/done/...88m....md` existed (untracked).
   - `tasks/DONE.md` was modified in working tree (not staged).
   - No active task existed.
8. The pre-commit hook correctly blocked raw recovery commits because `pcae check`
   found no active task.
9. Manual recovery required: restore active task file, restore status field, resync
   session, commit task contract via `pcae commit implementation`, then rerun
   `pcae task finish`.

## 5. Root Cause

In `src/pcae/commands/task.py`, `run_task_finish` builds `paths_to_stage` unconditionally
starting with the old active task path:

```python
paths_to_stage = [str(active_task_path)]   # tasks/active/...md (already moved)
```

When `git add -- tasks/active/...md` is then called and the file was never tracked,
git treats the path as a missing file with no tracked history, producing:

```
fatal: pathspec 'tasks/active/...md' did not match any files
```

If the file WAS tracked (the normal case), `git add` stages the deletion correctly.

## 6. Corrected Behavior

Before moving the task file, check whether it is tracked in git using
`git ls-files --error-unmatch`:

```python
_ls_check = subprocess.run(
    ["git", "ls-files", "--error-unmatch", str(active_task_path)],
    cwd=root.path,
    capture_output=True,
)
_active_task_was_tracked = _ls_check.returncode == 0
```

Then build `paths_to_stage` conditionally:

```python
paths_to_stage = [str(active_task_path)] if _active_task_was_tracked else []
```

The remaining paths (new `tasks/done/...md`, `tasks/DONE.md`, session file) are still
added from `result.updated_files` and `result.completed_task.destination_path`, which
are always present regardless of tracking status.

## 7. Tracked Active Task Behavior

Unchanged. When the active task file was previously committed:

- `git ls-files --error-unmatch` returns 0 → `_active_task_was_tracked = True`.
- `paths_to_stage` starts with the old active path.
- `git add -- tasks/active/...md` stages the deletion (correct behavior).
- Commit includes the deletion of the old path.
- Behavior is identical to before the fix.

## 8. Untracked Active Task Behavior

After the fix. When the active task file was never committed:

- `git ls-files --error-unmatch` returns non-zero → `_active_task_was_tracked = False`.
- `paths_to_stage` starts empty (old active path omitted).
- `result.updated_files` provides: `tasks/done/...md`, `tasks/DONE.md`, session file.
- `result.completed_task.destination_path` provides the new done path (deduplicated).
- `git add` stages only the new files — no attempt to stage a non-existent path.
- Commit includes: new `tasks/done/...md`, `tasks/DONE.md`, session file.
- Task finishes cleanly without pathspec error.
- Working tree is clean after commit.
- `tasks/active/` task file is gone (moved by `finish_active_task`, never tracked).

## 9. Regression Tests

Eight tests added to `tests/test_staged_file_aware_task_finish.py`:

| Test | Covers |
|------|--------|
| `test_untracked_task_sfa_finish_succeeds` | finish returns `finished=True, committed=True` |
| `test_untracked_task_sfa_finish_moves_to_done` | task file ends in `tasks/done/`, not `tasks/active/` |
| `test_untracked_task_sfa_finish_updates_done_md` | `tasks/DONE.md` has exactly 1 entry for the task |
| `test_untracked_task_sfa_finish_creates_commit` | a new git commit is created |
| `test_untracked_task_sfa_finish_no_staged_remainder` | no staged files remain after finish |
| `test_untracked_task_sfa_finish_no_pathspec_error` | exit code 0, no `CalledProcessError` |
| `test_tracked_task_sfa_finish_still_works` | tracked-file behavior preserved |
| `test_untracked_task_finish_no_duplicate_done_entry` | `tasks/DONE.md` has exactly 1 entry (not duplicated) |

Helper added: `_create_untracked_active_task` — creates a task contract without staging
or committing the task file, reproducing the 88M failure precondition.

## 10. Safety Boundary

The fix is strictly within the commit-path staging logic of `run_task_finish`. It does not:

- Change `finish_active_task` (the core task state machine).
- Change the `--commit` without `--staged-file-aware` path.
- Change the `--staged-file-aware` conflict-detection logic.
- Change the `git commit --no-verify` call.
- Broaden the task lifecycle semantics.
- Introduce new commands, config, or storage.
- Affect the permission broker, shell gate, or any other subsystem.

## 11. Remaining Limitations

- The fix only applies to the `--staged-file-aware` path. The non-SFA `--commit` path
  blocks on pre-existing changes (which include the untracked task file) before
  reaching the staging step — so it fails earlier and differently. That path is
  unaffected by this fix and unaffected by the 88M failure mode.
- No change to `pcae task finish recover`, which handles a different scenario
  (already-moved task file with no active task).
- Full-suite runtime optimization and test-run lock are not addressed here (88N.2).

## 12. Recommended Next Phase

**88N.2 — Full Suite Runtime Optimization and Test-Run Lock**

The Phase 88 series revealed that full-suite runs are slow (>7,000 tests) and that
overlapping full-suite runs contaminate results. 88N.2 should address:

- Full-suite runtime profiling and subprocess-heavy hotspot identification.
- Slow integration test categorization.
- Single foreground full-suite validation policy.
- Test-run lock or preflight to prevent concurrent `pytest -n auto` runs.
- Clear distinction between quick, governance, integration, and full tiers.
- Reliable green validation with less wall-clock time.

---

task_finish_robustness_name=phase_88_task_finish_tracked_file_robustness
task_finish_robustness_version=0.1
task_finish_robustness_status=implemented
implementation_status=complete
root_cause=untracked_active_task_file_staged_as_deletion_after_move
fix_location=src/pcae/commands/task.py:run_task_finish
fix_type=pre_move_tracking_check
regression_tests=8
recommended_next_phase=88N.2_full_suite_runtime_optimization_and_test_run_lock
backend_invocation_performed=false
source_mutation_authorized=true_for_task_finish_bugfix_only
test_mutation_authorized=true_for_regression_tests_only
execution_authorized=false
