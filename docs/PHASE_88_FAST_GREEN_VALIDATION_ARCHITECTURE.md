# Phase 88N.5 — Fast Green Validation Architecture

## 1. Purpose

Define a practical 1–2 minute normal development validation gate for PCAE. The prior
full-suite runtime (23:20 after 88N.4 optimization) and even the quick tier (~2:29) are
too slow to serve as the default gate for every governed phase iteration. This phase
creates a `fast_green` tier that provides high-signal governance confidence in seconds,
without weakening full-suite coverage.

## 2. Scope

- Add `fast_green` pytest marker declaration to `pyproject.toml`.
- Add `tests/conftest.py` with `pytest_collection_modifyitems` hook that auto-marks
  tests in selected modules as `fast_green`.
- Add `tests/test_88n5_fast_green_validation.py` — structural self-verification tests.
- Document tier model, selection criteria, and policy in this artifact.
- Update `PROJECT_STATUS.md` and `CHANGELOG.md`.

## 3. Non-Goals

- No source code changes (`src/` is unchanged).
- No test assertion weakening.
- No test deletion.
- No skip/xfail for speed.
- No `pcae validation fast-green` CLI command (the existing `pytest -m "fast_green"`
  invocation is sufficient; a CLI wrapper would add maintenance surface without
  governance value at this stage).
- No permission broker implementation.
- No shell gate implementation.
- No backend invocation.
- No prompts/capture/intake/adoption.

## 4. Baseline Problem

| Tier | Invocation | Runtime (88N.4 baseline) |
|------|-----------|--------------------------|
| Quick | `python -m pytest -m "not slow and not phase_closure" -n auto` | ~2:29 |
| Full | `python -m pytest -n auto` | ~23:20 |

A 2:29 quick tier is the fastest previously-documented normal gate. For typical governed
phases that change a narrow slice of PCAE governance logic, waiting 2.5 minutes per
validation cycle slows iteration and discourages running tests after every small fix.

## 5. Why Full Suite Remains But Cannot Be the Normal Gate

The full suite takes 23:20 on an M-series MacBook Pro. That is appropriate for:
- Release-quality validation
- Broad refactors touching shared code
- Governance-infrastructure changes
- CI baseline runs

It is not appropriate as the every-commit gate for narrow governance changes.

## 6. Validation Tier Model

| Tier | Marker/Filter | Approx. Tests | Approx. Runtime | Normal use |
|------|--------------|---------------|-----------------|-----------|
| targeted | `python -m pytest -k <phase_id>` | varies | seconds | Changed file smoke check |
| **fast-green** | `python -m pytest -m "fast_green" -n auto -ra --durations=50` | **~1,791** | **~22 s** | **Normal development gate** |
| quick | `python -m pytest -m "not slow and not phase_closure" -n auto` | ~7,012 | ~2:29 | Broader confidence, pre-push |
| full | `python -m pytest -n auto` | 7,719 | ~23:20 | Deep validation, release gating |
| nightly/exhaustive | (future) | all + extended | hours | Scheduled / manual |

## 7. Implementation Approach

Fast-green is implemented via a `tests/conftest.py` hook
(`pytest_collection_modifyitems`) that automatically applies `@pytest.mark.fast_green`
to all tests whose module name appears in `FAST_GREEN_MODULES`. No existing test files
are modified; no test functions receive a new decorator.

```python
# tests/conftest.py (excerpt)
FAST_GREEN_MODULES: frozenset[str] = frozenset({
    "test_check", "test_health", "test_hook_bypass_policy", ...
})

def pytest_collection_modifyitems(config, items):
    fast_green = pytest.mark.fast_green
    for item in items:
        module_name = item.module.__name__.split(".")[-1]
        if module_name in FAST_GREEN_MODULES:
            item.add_marker(fast_green)
```

## 8. Fast-Green Invocation

```
python -m pytest -m "fast_green" -n auto -ra --durations=50
```

For battery-conscious or low-core machines:

```
python -m pytest -m "fast_green" -n 4 -ra --durations=50
```

## 9. Fast-Green Selection Criteria

A test module is included in `fast_green` if ALL of the following hold:

1. It does **not** carry `@pytest.mark.slow` or `@pytest.mark.integration` — no
   per-test subprocess spawning.
2. It does **not** use module-scoped subprocess fixtures that require a cold pcae
   process startup per xdist worker (governance-info commands).
3. It does **not** contain capsys-bound tests that serialise under `xdist` and
   dominate runtime when multiplied by worker count.
4. Its primary purpose is to verify PCAE governance invariants, safety rules, task
   lifecycle logic, command structure, or architectural boundaries.
5. Including it does not push the fast-green wall-clock time past 60 seconds on
   typical developer hardware.

## 10. Included Categories

| Category | Modules | Rationale |
|----------|---------|-----------|
| Core governance check | test_check | Scope/task boundary enforcement |
| Health reporting | test_health | Overall health gate logic |
| Bypass prevention | test_hook_bypass_policy | Must-never-bypass safety |
| Hook wiring | test_hooks | Pre-commit hook installation |
| Policy validation | test_policy | Repo policy file parsing |
| CI integration | test_ci | CI workflow checks |
| Test-run preflight (88N.2) | test_doctor_test_run | Subprocess conflict detection |
| Task lifecycle | test_task | Contract create/update/finish/close |
| Session continuity | test_session | Agent-session handoff invariants |
| Task memory | test_task_memory_reconciliation | Memory drift detection |
| Lifecycle FSM | test_lifecycle_state_machine | State transition correctness |
| Lifecycle gates | test_lifecycle_gate_approval | Gate approval logic |
| Lifecycle dry-run | test_lifecycle_gate_runner_dry_run | Gate runner dry-run |
| Lifecycle next/status/summary | test_lifecycle_next_command, test_lifecycle_status_command, test_lifecycle_summary_command | Lifecycle command surface |
| Project structure | test_init, test_inspect, test_docs, test_repo | Repo layout validation |
| Architecture zones | test_architecture | Zone boundary enforcement |
| Strategic lineage | test_strategic_lineage | Strategic decision traceability |
| Provenance | test_provenance | Phase-to-commit lineage |
| Governance artefacts | test_artifact_index, test_artifact_metadata_consistency, test_memory_snapshot | Read-only artefact checks |
| Status / context / orchestration | test_status, test_context, test_orchestration | Output model correctness |
| Utility smoke | test_analytics, test_import, test_daemon, test_fleet, test_pipeline, test_export, test_review | Command surface smoke |
| 88N.5 self-verification | test_88n5_fast_green_validation | Tier structural integrity |

## 11. Excluded Categories

| Module(s) | Reason for Exclusion |
|-----------|---------------------|
| `test_agent` | 4,236 tests (~2:06); contains 23 capsys-bound capability-discovery tests (~4.5 s each) that cannot be effectively parallelised under xdist |
| `test_phase` | 886 tests (~25 s); exhaustive command-catalog coverage — important but not the daily development gate |
| `test_governance_timeline`, `test_decision_log`, `test_risk_register`, `test_project_state` | Despite having no `slow` marker, these use module-scoped subprocess fixtures that each spawn a pcae process per xdist worker; group total ~2:25 |
| All `slow` + `integration` files (707 tests) | Spawn a fresh pcae subprocess per test; structurally incompatible with a fast gate |
| `phase_closure` files | Heavyweight phase-closure validation; correct tier is full |

## 12. Runtime Target and Measured Result

| Target | Measured (M5 Pro, -n auto) |
|--------|---------------------------|
| 1–2 minutes | **22.19 s** (1,775 tests) |

The 22-second runtime significantly beats the 1-minute target, providing substantial
head room for future marker additions without risking tier inflation.

After adding `test_88n5_fast_green_validation.py` (17 tests), the tier grows to
~1,791 tests at approximately the same runtime.

## 13. When Fast-Green + Targeted Is Sufficient

Fast-green paired with targeted (`-k <phase_id>`) tests is the normal development gate
for low- and medium-risk governed changes. A change is low/medium-risk when it:

- Affects a single PCAE command or narrow logic path.
- Does not modify shared lifecycle, session, or governance infrastructure.
- Does not change test markers, test infrastructure, or pyproject.toml test config.
- Does not touch `.githooks/` or pre-commit hook logic.
- Does not affect subprocess-facing CLI contracts.

Suggested workflow:
```
# After each edit:
python -m pytest -k <phase_id> -n auto          # targeted (seconds)
python -m pytest -m "fast_green" -n auto -ra    # fast-green gate (22 s)
pcae check                                       # governance invariants
```

## 14. When Quick Tier Is Required

Use quick tier (`python -m pytest -m "not slow and not phase_closure" -n auto`) when:

- Fast-green passes but you want broader confidence before committing.
- Changes affect `test_agent`, `test_phase`, or governance-info modules excluded from
  fast-green.
- Changes affect the pyproject.toml test configuration.
- Pre-push verification on a significant change.
- Fast-green is newly failing and you want broader diagnostic context.

## 15. When Full Suite Is Required

Use full suite (`python -m pytest -n auto`) when:

- Changing shared lifecycle or governance source files in `src/pcae/core/`.
- Broad refactors touching multiple command families.
- Changing test infrastructure (conftest.py, pytest markers, fixtures).
- Release-quality validation before tagging.
- Fast-green or quick tier fails and the fix is not locally obvious.
- Explicitly requested by the operator.

**Always run `pcae doctor test-run --json` before a full-suite run** to detect
conflicting parallel pytest processes.

## 16. Test-Run Preflight Usage

Before any full-suite run:

```
pcae doctor test-run --json    # must return clear_to_run=true
python -m pytest -n auto -ra --durations=150
```

Fast-green and quick tier do not require the preflight check in normal usage — they
run in under 2:30. Use preflight defensively if another pytest process may be running.

## 17. Safety and Coverage Preservation

- **No tests deleted.** All 7,719 tests remain in the full suite.
- **No assertions weakened.** All existing test invariants are unchanged.
- **No skip/xfail for speed.** The fast_green marker is an additive label only.
- **No existing pytestmark modified.** The conftest.py hook adds markers at collection
  time; it does not remove or override any existing markers.
- **Full-suite baseline remains green.** 7,719 passed, 0 failures (88N.4 baseline).

## 18. Remaining Limitations

1. `test_agent.py` contains 23 capsys-bound capability-discovery tests (~4.5 s each)
   that remain outside fast-green. They are deferred per the 88N.4 bottleneck
   documentation. Isolating them with a `slow` marker is a candidate for a future
   narrow phase.

2. `test_governance_timeline`, `test_decision_log`, `test_risk_register`,
   `test_project_state` remain excluded from fast-green. Their module-scoped fixtures
   reduce per-test cost but each worker still pays one subprocess startup. A future
   phase could explore in-process mocking for the read-only governance commands to
   bring these into fast-green.

3. The fast-green set currently covers ~1,791 of 7,719 tests (23%). Higher coverage
   with no runtime penalty is achievable by bringing the four governance-info modules
   in-process.

## 19. Recommended Next Phase

**88O — Shell Gate Design Reconciliation**

88O reconciles the Phase 87 shell gate design with the explicit preflight layer built
in 88A–88N. The full-suite baseline is green and the fast-green development gate is
now established. 88O should be a design-only phase (no source or test changes
required); it delivers a `docs/` design artifact.
