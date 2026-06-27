# Phase 88X.2 — Validation Runtime Budget and Test Tier Rebalancing

```
phase_name    = phase_88x2_validation_runtime_budget_and_test_tier_rebalancing
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 88Y_advisory_mode_test_matrix_and_cli_stability_review
```

## 1. Purpose

Profile validation runtime across all three test tiers, identify bottlenecks,
document tier policy, and make safe optimizations. Fast-green and quick tier
are already within target budgets; the full suite bottleneck is documented
with recommendations for follow-up optimization.

## 2. Scope

In scope:

- Profile fast-green, quick tier, and full suite runtimes
- Identify top slowest tests and files
- Document tier marker policy
- Identify marker hygiene issues
- Document full-suite active-task interference risk (88X.1 finding)
- Optional changed-test accelerator evaluation
- Make safe marker/fixture adjustments

Out of scope:

- Deleting, skipping, or xfailing tests
- Weakening assertions
- Changing production source behavior
- Implementing new validation commands
- 88Y advisory expansion

## 3. Non-Goals

88X.2 must not and does not:

- Delete, skip, or xfail tests
- Weaken assertions
- Change production source behavior
- Make new dependencies mandatory
- Implement 88Y or any enforcement features

## 4. Baseline Runtimes

| Tier | Tests | Runtime | Target | Status |
|------|-------|---------|--------|--------|
| Fast-green | 2,814 | 24.18s | ≤30s | ✅ Within target |
| Quick tier | 8,063 | 2:26 | ≤3min | ✅ Within target |
| Full suite | 8,800 | 33:00 | ≤25min (≤30min acceptable) | ❌ 3min over acceptable |

## 5. Runtime Bottlenecks Found

### Fast-Green (24.18s)

No significant bottlenecks. The slowest fast-green tests take ~2s each
(artifact index, memory snapshot, context retention). These are file-I/O
tests that read governance state — essential coverage.

### Quick Tier (2:26)

No significant bottlenecks. The 5,249 non-fast-green quick-tier tests run
in ~2 minutes. The slowest quick-tier tests take ~1.5s each.

### Full Suite (33:00)

**Bottleneck: 737 slow/integration/phase_closure tests.**

These tests spawn subprocesses (`subprocess.run` calling `pcae` CLI commands).
Each subprocess invocation incurs:
- Python interpreter startup: ~0.1-0.3s
- Module import: ~0.5-1s
- CLI argument parsing: ~0.1s
- Actual test logic (string matching): ~0.1s
- Total per subprocess: ~1-2s minimum

The top slowest tests take significantly longer because they:
- Run multiple subprocesses per test
- Include phase-closure validation with many CLI calls
- Perform sequential operations

**Top 5 slowest test files (from 88X.1 baseline):**

| File | Slowest Test | Duration |
|------|-------------|----------|
| `test_phase87_integration.py` | `test_no_repository_mutation` | 338s |
| `test_phase87_integration.py` | `test_gate_dry_run_deterministic` | 304s |
| `test_scope_preflight.py` | `test_existing_intelligence_commands_still_work` | 172s |
| `test_scope_matching_consistency.py` | `test_cli_both_agree_readme_is_forbidden` | 172s |
| `test_phase85_integration.py` | `test_all_commands_emit_valid_json` | 171s |

**Phase-closure test files** (3 files, ~25 slow tests, taking ~10+ minutes total):
- `test_phase87_integration.py`
- `test_phase85_integration.py`
- `test_lifecycle_regression.py`

These are high-value governance integration tests. They cannot be removed or
weakened without compromising coverage.

**Subprocess-heavy test files** (~40 files, ~700 slow/integration tests):
- Gate tests (`test_*_gate.py`)
- Preflight tests (`test_*_preflight*.py`)
- Integration tests (`test_*_integration.py`)
- CLI tests (`test_scope_matching_consistency.py`)

## 6. Fast-Green Marker Policy

### Current

Fast-green marker (`pytest.mark.fast_green`) is applied at either the file
level (`pytestmark = pytest.mark.fast_green`) or the test level. Tests
marked `fast_green`:

- Must not spawn subprocesses (except for a few CLI smoke tests)
- Must not perform file I/O beyond reading governance state
- Must run in <1s each (ideally <0.1s)
- Must cover high-signal governance invariants

### Marker Hygiene Issue

Three files have file-level `fast_green` AND test-level `slow`/`integration`
markers simultaneously:

| File | Slow tests | Integration tests |
|------|-----------|-------------------|
| `test_broker_shell_gate_edge_cases.py` | 12 | 12 |
| `test_broker_shell_gate_integration.py` | 3 | 0 |
| `test_permission_broker.py` | 1 | ~8 |

These 16+ tests have BOTH `fast_green` (from file-level marker) AND `slow`
(from test-level marker). They are subprocess-based CLI tests that run in
`-m "fast_green"` because the file-level marker takes precedence.

These tests are fast enough (1-2s each) that they don't significantly impact
fast-green runtime (currently 24s). However, this is a marker hygiene issue
that should be addressed in a future cleanup phase.

### Policy (Documented)

- `fast_green`: High-signal governance invariants. No subprocess calls
  (except documented CLI smoke tests). Target ≤30s.
- `slow`: Tests that spawn subprocesses or take >1s each. Excluded from
  quick tier.
- `integration`: CLI integration tests that spawn `pcae` subprocesses.
  Typically also `slow`.
- `phase_closure`: Heavyweight phase-closure validation tests. Longest
  runtime tier.

## 7. Quick-Tier Policy

Quick tier: `-m "not slow and not phase_closure"` selects all tests that
are neither `slow` nor `phase_closure`. This includes:
- All `fast_green` tests
- All unmarked tests (no slow/integration/phase_closure marker)

Target: ≤3 minutes. Current: 2:26. ✅

## 8. Full-Suite Policy

Full suite: `-m ""` (no marker filter, all tests). This runs every test
in the project, including slow integration tests and phase-closure validation.

Target: ≤25 minutes (≤30 minutes acceptable). Current: 33:00. ❌

The 3-minute overage is driven by the 737 slow/integration/phase_closure
tests that spawn subprocesses. These tests are essential for CLI integration
coverage and cannot be removed.

### Recommended Full-Suite Commands

```bash
# Full governance suite (all tests):
pcae doctor test-run --json
python -m pytest -n auto -ra --durations=200

# Quick validation (skip slow):
python -m pytest -m "not slow and not phase_closure" -n auto

# Fast gate (high-signal invariants only):
python -m pytest -m "fast_green" -n auto -ra --durations=100
```

## 9. Security-Critical Fast-Green Coverage

The following invariants are covered by fast-green tests:

| Invariant | Test Location | Status |
|-----------|--------------|--------|
| Raw git push hard block | `test_broker_shell_gate_edge_cases.py`, `test_advisory_mode.py` | ✅ |
| Force push hard block | `test_broker_shell_gate_edge_cases.py`, `test_advisory_mode.py` | ✅ |
| Policy-forbidden file mutation | `test_broker_shell_gate_edge_cases.py` | ✅ |
| Secret redaction | `test_broker_shell_gate_edge_cases.py`, `test_advisory_mode.py` | ✅ |
| broker.requested_command redaction | `test_broker_shell_gate_edge_cases.py` | ✅ |
| Deny maps fail-closed | `test_broker_shell_gate_edge_cases.py` | ✅ |
| authorization_granted=false | Multiple files | ✅ |
| execution_authorized=false | Multiple files | ✅ |
| command_executed=false | Multiple files | ✅ |
| Performed flags false | Multiple files | ✅ |
| Hard blocks not overridden by human approval | `test_advisory_mode.py`, edge cases | ✅ |
| Hard blocks not overridden by accepted risk | `test_advisory_mode.py`, edge cases | ✅ |
| Advisory check JSON smoke | `test_advisory_mode.py` | ✅ |

All security-critical coverage is preserved in fast-green. No changes needed.

## 10. Tests Moved Between Tiers

**No tests were moved.** The current tier assignments are appropriate:

- Fast-green tests cover invariants that must be validated frequently
- Quick-tier tests cover broader behavior without slow subprocess overhead
- Slow/integration tests cover CLI integration and end-to-end behavior
- Phase-closure tests cover phase-completion validation

Moving slow tests to faster tiers would add subprocess overhead to the fast
tiers. Moving fast tests to slow tiers would reduce fast-green coverage
below acceptable levels for governance validation.

## 11. Fixture/Setup Optimizations

**No fixture optimizations were made.** The slow tests primarily use
`subprocess.run` to call PCAE CLI commands. Each invocation is a fresh
process — there is no shared setup to cache at the fixture level.

Session-scoped fixtures are not applicable because:
- Each test calls a different CLI command with different arguments
- The CLI commands need a real filesystem (temp dirs are per-test)
- Parallel execution (pytest-xdist) distributes tests across workers

## 12. Subprocess Reductions

**No subprocess reductions were made.** Converting subprocess-based CLI
tests to direct function calls would require:
1. Refactoring CLI commands to separate core logic from argument parsing
2. Rewriting hundreds of tests

This is a significant refactoring effort that belongs in a dedicated
test-architecture improvement phase, not 88X.2.

## 13. Full-Suite Active-Task Interference Risk

**Finding from 88X.1**: Full-suite tests that subprocess against live
`REPO_ROOT` can be affected by an active task contract under `tasks/active/`.

During Phase 88X, the active task contract caused 185 preflight/scope/
backend tests to fail with `blocked_by_missing_task_contract` or unexpected
scope decisions. After the task was finished (`pcae task finish` moved the
contract to `tasks/done/`), all 8,800 tests passed.

**Recommendation**: Full-suite runs should be performed in idle state
(after `pcae task finish`). Alternatively, tests requiring task-active
behavior should use isolated temp task roots (as broker + shell gate
integration tests already do). A future test-hardening phase (88R.1 pattern)
should migrate all preflight/scope/backend tests to use `tmp_task_root`
fixtures.

**Avoidance**: The active-task interference only affects full-suite runs.
Fast-green and quick-tier tests either:
- Use direct function calls (not subprocess against REPO_ROOT)
- Use temp dir fixtures with explicit task contracts
- Test invariants independent of task state

## 14. Optional Changed-Test Accelerator Evaluation

Three accelerator options were evaluated:

### `pytest --lf` / `--ff` (last-failed / first-failed)
- **Utility**: High — reruns only previously failing tests
- **Risk**: Low — pytest built-in
- **Recommendation**: Already available. Document as optional local accelerator
  but not as governance evidence.

### `pytest-testmon` (changed-test selection)
- **Utility**: Medium — runs only tests affected by code changes
- **Risk**: Medium — requires database, adds dependency, can miss non-code
  changes (config, docs)
- **Recommendation**: Optional local accelerator only. Must not replace
  full-suite governance validation. Do not make mandatory.

### `pytest-ranking` (feedback-ordered execution)
- **Utility**: Low-Medium — runs fastest/failing tests first for earlier feedback
- **Risk**: Low — only changes ordering, not selection
- **Recommendation**: Optional. Low priority.

## 15. Final Runtimes

| Tier | Tests | Runtime | Target | Delta |
|------|-------|---------|--------|-------|
| Fast-green | 2,814 | 24.18s | ≤30s | -5.82s |
| Quick tier | 8,063 | 2:26 | ≤3min | -34s |
| Full suite | 8,800 | 33:00 | ≤30min | +3min |

All tier counts are unchanged from baseline (no marker changes made).

## 16. Remaining Bottlenecks

1. **Full suite subprocess overhead**: 737 slow/integration tests spend most
   of their runtime waiting for subprocess spawn + Python import. Without
   architectural changes (refactoring CLI to separate core logic from
   argument parsing), this overhead is unavoidable.

2. **Phase-closure tests**: `test_phase87_integration.py` and
   `test_phase85_integration.py` contain the slowest individual tests
   (up to 338s). These tests perform comprehensive governance validation
   that requires multiple subprocess calls.

3. **Marker hygiene**: 16+ tests have both `fast_green` and `slow` markers
   due to file-level marker inheritance. These don't significantly impact
   fast-green runtime but should be cleaned up in a future phase.

## 17. Recommended Next Phase

**88Y — Advisory Mode Test Matrix and CLI Stability Review**

Proceed with advisory mode test expansion as originally planned. The
validation tiers are documented, runtimes are profiled, and the full-suite
bottleneck is understood. No blocking issues remain for 88Y.

A dedicated test-architecture improvement phase should be scheduled after
88Y to:
1. Refactor subprocess-heavy tests to use direct function calls
2. Clean up marker hygiene (file-level vs test-level marker conflicts)
3. Migrate preflight/scope/backend tests to isolated task fixtures
4. Reduce full-suite runtime below 30 minutes
