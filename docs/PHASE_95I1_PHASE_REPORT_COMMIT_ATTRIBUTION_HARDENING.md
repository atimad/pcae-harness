# Phase 95I.1 — Phase Report Commit Attribution Hardening

```
phase_name = phase_95i1_phase_report_commit_attribution_hardening
phase_status = completed | implementation_status = completed
recommended_next_phase = 95J — Artifact-Only Invocation Command Boundary Design
```

## 1. Purpose

Hardened PCAE phase report commit attribution so reports no longer list stale prior-phase commits as current-phase commits. The root cause was a truthiness bug: `phase_commits: []` in metadata (explicitly empty, meaning "no commits for this phase") was treated as falsy, causing `_gather_commits()` to fall back to `git log -5` and inject commits from prior phases. Additionally, the `COMPLETENESS_COMPLETE` return path in `assess_completeness()` discarded accumulated trust warnings.

## 2. Root Cause

### Bug 1: `src/pcae/commands/phase.py:148-154`

```python
commits = _gather_commits()      # git log -5
if phase_commits_meta:           # [] is falsy → falls through
    ...
```

When metadata declares `"phase_commits": []` (no phase-owned commits), the empty list is falsy in Python, causing a fallback to `_gather_commits()` which shows the last 5 commits from HEAD — regardless of which phase they belong to.

### Bug 2: `src/pcae/core/phase_reports.py` — return path

```python
return COMPLETENESS_COMPLETE, [], []  # discards warnings
```

The complete return path hard-coded empty warnings list, discarding any trust warnings accumulated during assessment.

### Impact on Telegram

Telegram (`notifications.py:577-582`) reads `report.commits` from the PhaseReport metadata at `notifications.py:385`. The stale commit list flowed to Telegram, which labeled the first stale commit as "Phase commit."

## 3. Fixes

### Fix 1: `src/pcae/commands/phase.py` — Check key presence, not truthiness

```python
if "phase_commits" in meta:
    # Explicit declaration is authoritative (even empty list)
    phase_commits_meta = meta.get("phase_commits", [])
    meta_hashes = [c.get("hash", "")[:8] for c in phase_commits_meta if c.get("hash")]
    commits = meta_hashes  # explicitly empty → no commits
    commit_attribution = "phase_owned" if meta_hashes else "none"
else:
    commits = _gather_commits()  # backward compat fallback only when key absent
```

### Fix 2: `src/pcae/core/phase_reports.py` — Commit ownership validation

Added commit ownership trust warning in `assess_completeness()`: when `files_changed > 0` and commits are present but metadata has no `phase_commits` or `commit_attribution`, warn `commits.phase_owned not verified`.

### Fix 3: `src/pcae/core/phase_reports.py` — Preserve warnings on complete

Changed `return COMPLETENESS_COMPLETE, [], []` to `return COMPLETENESS_COMPLETE, [], warnings`.

## 4. Commit Attribution Data Flow (After Fix)

```
1. Metadata has "phase_commits": [] → commits=[] → report shows "not captured"
2. Metadata has "phase_commits": [{"hash": "abc"}] → commits=["abc"] → phase-owned
3. Metadata has NO "phase_commits" key → fallback to git log -5 → backward compat
   BUT: trust warning "commits.phase_owned not verified" appears
```

## 5. Files Changed

| File | Change |
|------|--------|
| `src/pcae/commands/phase.py` | Fix 1: `"phase_commits" in meta` check; `commit_attribution` pass-through |
| `src/pcae/core/phase_reports.py` | Fix 2+3: commit ownership warning; preserve warnings on COMPLETE |
| `tests/test_phase_reports.py` | 7 new tests (Test95I1CommitAttributionHardening class) |
| `docs/PHASE_95I1_PHASE_REPORT_COMMIT_ATTRIBUTION_HARDENING.md` | This document |

## 6. Tests (7 new)

| Test | Purpose |
|------|---------|
| `test_explicit_empty_phase_commits_not_overridden` | Empty phase_commits produces empty commits |
| `test_phase_owned_commits_preserved` | Phase-owned commits kept, report complete |
| `test_missing_phase_commits_key_backward_compat` | No key → warning, not blocking |
| `test_stale_commits_from_fallback_make_report_partial` | Stale commits trigger trust warning |
| `test_commit_attribution_explicit_allows_files_changed` | commit_attribution suppresses warning |
| `test_phase_commits_present_no_phase_owned_warning` | Explicit phase_commits → no warning |
| `test_multipart_phase_id_with_phase_commits` | Multipart IDs (95H.1) work correctly |

## 7. Repaired 95I Report

After the fix, the 95I report with `"phase_commits": []` in metadata will:
- Show `Commits: not captured` instead of listing stale hashes
- Mark report as partial with `commits` in missing trust fields
- NOT label a prior-phase commit as "Phase commit" in Telegram
- Include a trust warning if no `commit_attribution` is provided

## 8. No-Go Confirmations

- No real backend invocation was implemented.
- No adapter execution was implemented.
- No subprocess execution was implemented.
- No network call was implemented.
- No shell interception was implemented.
- No Telegram inbound was implemented.
- No enforcement was implemented.
- No automatic apply was implemented.
- No apply execution was implemented.
- No commit/push authorization was implemented.
- No real AI backend calls were implemented.
- 95J not started.

## 9. Recommended Next Phase

**95J — Artifact-Only Invocation Command Boundary Design**
