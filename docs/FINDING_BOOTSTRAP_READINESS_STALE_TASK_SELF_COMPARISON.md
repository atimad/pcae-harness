# Finding — `pcae session bootstrap` Stale-Active-Task Check Compares the Latest Phase Report to Itself

**Status:** Open — queued for a future governed phase. Not yet repaired.

**Discovered:** 2026-07-20, during Phase 137J → 137K task-transition bootstrap.

## What

`_classify_bootstrap_readiness()` in `src/pcae/commands/session.py` is meant
to detect when the *active task* still refers to a phase that has already
been completed and reported. Instead, the check compares the latest
completed phase report to itself, so it fires unconditionally — regardless
of what the active task actually is — any time `latest_report.status ==
"completed"`.

```python
# src/pcae/commands/session.py, inside _classify_bootstrap_readiness()
if report_status == "completed" and report_phase:
    # Check if active task phase is already completed
    if _phase_is_completed(report_phase, latest_report):
        # Active task belongs to a completed phase → stale
        blocked.append(f"Active task appears stale (phase {report_phase} is completed)")
```

`_phase_is_completed(phase_id, latest_report)` extracts `latest_report["phase_id"]`
again internally and compares it against `phase_id`:

```python
def _phase_is_completed(phase_id: str, latest_report: dict | None) -> bool:
    ...
    report_phase = latest_report.get("phase_id", "")
    report_status = latest_report.get("status", "")
    if not report_phase or report_status != "completed":
        return False
    report_base = _extract_phase_number(report_phase)
    task_base = _extract_phase_number(phase_id)
    return task_base == report_base or report_phase.startswith(task_base)
```

The call site passes `report_phase` (i.e. `latest_report["phase_id"]`) as the
`phase_id` argument instead of the *active task's* phase. That makes
`task_base == report_base` trivially true every time, since both are derived
from the same string. The intended comparison — "does the active task's
phase match/precede the just-completed phase report's phase?" — is never
actually performed.

## Impact

- `pcae session bootstrap` reports `Readiness: blocked` with
  `"Active task appears stale (phase <X> is completed)"` on every bootstrap
  run following any completed phase report, even immediately after a fresh,
  correctly-matching active task has been opened via `pcae task transition`.
- Confirmed reproduced on 2026-07-20: after closing the stale idle task and
  opening task `20260720-1208-phase-137k-...` (title matches the recommended
  next phase, 137K), bootstrap still reported the task as stale referencing
  completed phase 137J.
- Severity: cosmetic/diagnostic only. It does not block real work — no
  command refuses to run because of it — but it makes `Readiness: blocked`
  permanently uninformative, masking genuine staleness signals an operator
  or agent should actually act on.

## Proposed Fix

Pass the **active task's** phase identifier into `_phase_is_completed`,
not the report's own phase, e.g.:

```python
if report_status == "completed" and report_phase:
    if task_id and _phase_is_completed(task_id, latest_report):
        blocked.append(f"Active task appears stale (phase {report_phase} is completed)")
```

`task_id` (or an extracted phase token from `active_task["id"]`/`title`) is
already in scope a few lines above (`task_id = active_task.get("id", "")`).
`_extract_phase_number()` already tolerates arbitrary leading text before the
phase token via its regex, so passing the full task id/title should work
without further changes to `_extract_phase_number`.

Recommended repair scope:

1. Fix the call site to compare the active task's phase against the latest
   completed report's phase, not the report against itself.
2. Add a regression test asserting that a freshly-transitioned active task
   whose title/id matches the recommended next phase does **not** trigger
   the stale-task blocked message, while an active task whose phase matches
   an older, already-completed report still does.
3. Re-verify the existing "Active task may not match recommended next"
   warning path is unaffected (it already correctly reads `task_title`
   separately and was not misfiring in the 2026-07-20 reproduction).

This is a small, isolated, single-file diagnostic fix with no contract or
lifecycle surface — suitable as a short bounded phase, or as a rider on a
nearby governance/session-reporting phase.
