# Phase 106B — Release-Critical Warning / Fast-Green Triage

## Purpose

Triage the 3 fast-green failures carried as "known pre-existing" since
before Phase 105A, and confirm no other release-critical warnings exist,
before PCAE v0.1 release hardening continues.

## Scope

- Reproduce each of the three known fast-green failures individually.
- Identify exact root cause, ownership, and whether each is a real defect,
  an obsolete test, or an environment-sensitive test.
- Repair what is safely repairable; classify explicitly whatever is not.
- Confirm `pcae doctor task-memory` remains clean.
- Update `docs/RELEASE_SCOPE_V0_1.md`'s validation baseline and blocker
  classification to reflect the triage outcome.

## Non-goals

106B does not implement runtime enforcement, autonomous execution, real
backend invocation, adapter execution, shell mediation, Telegram inbound,
rollback execution, or apply/commit/push authorization beyond the existing
governed lifecycle. It does not add an execution enablement flag or
toggle. It does not perform a broad architectural refactor — the fixes
below are narrowly scoped to the actual defects found. v0.1 remains
non-executing by design; v0.2 remains the autonomy target.

## Relationship to v0.1 Release Scope (106A)

106A's `docs/RELEASE_SCOPE_V0_1.md` listed the 3 fast-green failures as a
"must document before v0.1" item, explicitly deferring their disposition
to this phase ("106B should re-triage the fast-green failures specifically
and decide fix-vs-document-permanently"). 106B resolves that deferral.

## Current Validation Baseline (before this phase's fixes)

Fast-green: 4387/4390, 3 pre-existing failures — `Test94UPreflightArtifact`,
`Test94UPreflightArtifactCLI`, `TestBackendShow`. `pcae_doctor_task_memory`:
clean.

## Fast-Green Failure Inventory

| Test | File | Reproducible in isolation? |
|---|---|---|
| `Test94UPreflightArtifact::test_verify_valid_artifact` | `tests/test_backend_invocations.py` | Yes, deterministically |
| `Test94UPreflightArtifactCLI::test_verify_latest_after_save` | `tests/test_backend_invocations.py` | Yes, deterministically |
| `TestBackendShow::test_show_missing_artifacts` | `tests/test_backend_cli.py` | Yes, deterministically — but see root cause below |

## Per-Failure Investigation

### `Test94UPreflightArtifact::test_verify_valid_artifact` and `Test94UPreflightArtifactCLI::test_verify_latest_after_save`

**Symptom:** `verify_backend_adapter_preflight_artifact()` reports
`"unknown preflight status: 'ready'"` for an artifact whose status is
literally `PREFLIGHT_READY = "ready"` — the only status
`validate_backend_adapter_preflight()` can actually produce for a healthy
mock backend.

**Root cause:** `src/pcae/core/backend_invocations.py` (a ~10,400-line
file accumulated across dozens of phases) defined **two different,
unrelated module-level constants both named `VALID_PREFLIGHT_STATUSES`**:
one near line 3346 (Phase 94U-era, covering `BackendAdapterPreflightResult`
/ `BackendAdapterPreflightArtifact`, includes `"ready"`), and a second,
completely different one near line 7838 (a later phase's execution-
readiness-preflight feature, does not include `"ready"`). Since Python
executes module top-level code sequentially and both call sites reference
the name as a plain module global (not an import alias), the *second*
definition silently overwrote the first in the module namespace by the
time any test ran. `verify_backend_adapter_preflight_artifact()` and
`BackendAdapterPreflightResult.validate()` — both written for the *first*
feature — ended up validating against the *second*, unrelated status set.

This is a genuine defect: the 94U preflight-artifact feature has been
checking the wrong status set since whichever later phase introduced the
second `VALID_PREFLIGHT_STATUSES`, and the two fast-green failures are a
direct, deterministic consequence.

**Fix:** Renamed the first (94U) constant to
`VALID_ADAPTER_PREFLIGHT_STATUSES` and updated its two internal call sites
(`BackendAdapterPreflightResult.validate()` and
`verify_backend_adapter_preflight_artifact()`). The second, later
`VALID_PREFLIGHT_STATUSES` and its own call site/tests
(`tests/test_execution_readiness_preflight*.py`) are untouched — they were
already correct and already passing.

**Status:** **Fixed.**

### `TestBackendShow::test_show_missing_artifacts`

**Symptom:** `pcae backend show --latest` (run with `cwd=REPO_ROOT`, i.e.
against this actual working repository, not an isolated directory) returns
exit 0 and prints a real artifact, when the test expects "no artifacts"
(exit != 0).

**Root cause:** `.pcae/backend-invocations/` is gitignored and, in this
specific long-lived local working tree, has accumulated **4,760+ real
files** from years of legitimate local dogfooding of `pcae backend *`
commands across many earlier phases (94-something onward). The test's
assumption — "no backend invocation has ever happened in this repo" — was
true only briefly, right after the feature was first implemented, and has
not held for a long time. This is not a product defect:
`pcae backend show --latest` correctly shows the latest artifact when one
exists, which is the correct, intended behavior for an end user. It was
confirmed empirically: temporarily moving `.pcae/backend-invocations/`
aside and re-running the test in isolation made it pass immediately; the
directory was restored unchanged immediately after (no data was deleted).

**Fix:** Rather than delete real accumulated local history (which would be
irreversible and is not this phase's job), the test itself was changed to
run in an isolated `tmp_path` cwd instead of `cwd=REPO_ROOT` — it no longer
depends on this repository's own accumulated dogfooding state, and will
now pass identically on a fresh clone, in CI, or in this long-lived local
checkout. No other test in `tests/test_backend_cli.py` was changed; the
shared `_run()` helper (which several other, unrelated tests correctly
rely on `cwd=REPO_ROOT` for) is untouched.

**Status:** **Fixed** (test-fixture-mismatch repair category).

## Task-Memory Warning Status

`pcae doctor task-memory` → **clean. No inconsistencies detected.**
Re-verified after the fixes above and again before phase completion.

## Release Blocker Classification (final, post-repair)

| Item | Pre-106B classification | Post-106B status |
|---|---|---|
| `Test94UPreflightArtifact::test_verify_valid_artifact` | Must document before v0.1 | **Fixed** — no longer a blocker of any kind |
| `Test94UPreflightArtifactCLI::test_verify_latest_after_save` | Must document before v0.1 | **Fixed** — no longer a blocker of any kind |
| `TestBackendShow::test_show_missing_artifacts` | Must document before v0.1 | **Fixed** — no longer a blocker of any kind |
| `pcae_doctor_task_memory` | Not a blocker (clean) | Remains not a blocker (clean) |

No new release-blocking warnings were discovered during this triage.

## Repair Decisions

1. Renamed `VALID_PREFLIGHT_STATUSES` (94U-era) to
   `VALID_ADAPTER_PREFLIGHT_STATUSES` in `src/pcae/core/backend_invocations.py`,
   updating its 2 internal call sites. The unrelated, later
   `VALID_PREFLIGHT_STATUSES` definition and its call site/tests are
   unchanged.
2. Isolated `TestBackendShow::test_show_missing_artifacts` to a `tmp_path`
   cwd in `tests/test_backend_cli.py`, removing its dependency on this
   repository's own accumulated local `.pcae/backend-invocations/` history.

No safety checks were weakened. No tests were deleted or had their
assertions loosened — both were fixed to make their original, correct
assertions actually hold.

## Known Non-Blocking Limitation Decisions

None required — all three failures were repairable and have been repaired.
Fast-green is fully green (4390/4390) as of this phase.

## Release Disposition

**Fast-green is fully green: 4390/4390.** All three previously-known
failures are fixed, not merely documented. `pcae_doctor_task_memory` is
clean. No other release-critical warnings were found. v0.1 golden-workflow
stabilization (106C) may proceed without any known fast-green disposition
caveat.

## Recommended Next Phase

106C — Golden Workflow Stabilization. With fast-green fully green and
task-memory clean, stabilize and document the exact v0.1 production
workflow (the golden workflow from 106A) end-to-end.
