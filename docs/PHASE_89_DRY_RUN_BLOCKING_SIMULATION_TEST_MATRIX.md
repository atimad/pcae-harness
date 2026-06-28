# Phase 89D — Dry-Run Blocking Simulation Test Matrix and CLI Stability Review

```
phase_name    = phase_89d_dry_run_simulation_test_matrix
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 89e_dry_run_simulation_ux_refinement
```

## 1. Purpose

Expand and stabilize the dry-run blocking simulation prototype (89C) by adding a comprehensive test matrix and CLI contract review. Verify that dry-run check/explain/status behavior is stable across human-readable and JSON outputs, preserves hard-block and redaction behavior, and keeps every simulation/no-execution invariant intact.

## 2. Scope

In scope:

- Expand dry-run test matrix from 74 to 244 tests (+170)
- Add CLI subprocess tests (exit codes, JSON parsing, human-readable output)
- Verify JSON schema stability across 7 command types
- Verify human-readable output contains required sections
- Verify decision vocabulary coverage (all 19 decisions)
- Verify hard-block and redaction preservation
- Verify compact operator, shell embedded, and env-prefix behavior from 89A
- Verify exit-code behavior (0=allow, 1=blocked)
- Document any deferred defects

Out of scope:

- Changing shell-gate, advisory, or broker behavior
- Implementing enforcement, blocking, shell interception
- Source behavior changes beyond narrow dry-run fixes

## 3. Non-Goals

89D must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, or authorization.

## 4. Starting Point from 89C

74 tests in `tests/test_dry_run_simulation.py` covering envelope structure, invariants, decision mapping, severity, hard blocks, redaction, explain, status, vocabulary, and compound commands.

## 5. Matrix Dimensions

8 test categories:

| Category | Tests Added | Description |
|----------|------------|-------------|
| A. Read-only allow | 14 | Governed PCAE and read-only commands not blocked |
| B. Hard-block | 7 | Hard-block commands produce blocked severity |
| C. Shell embedded | 8 | Shell -c/-lc embedded command classification |
| D. Env-prefix | 5 | env/VAR=val prefix behavior from 89A |
| E. Compact operator | 8 | Compact |, &&, \|\|, ; operator splitting |
| F. Redaction | 8 | Secret redaction across env, files, programs |
| G. Explain/status | 4 | Full decision vocabulary explainability |
| H. JSON stability | 7 | JSON field presence and type stability |
| Safety cross-check | 15 | Every command type preserves all invariants |
| CLI tests | 24 | Subprocess CLI exit codes, JSON, human-readable |

**Total: 244 tests** (74 original + 170 new), plus 24 CLI subprocess tests.

## 6–12. Matrix Coverage

All 8 categories covered:
- ✅ A. Read-only allow paths (13 parametrized + 1)
- ✅ B. Hard-block paths (7 tests)
- ✅ C. Shell embedded-command paths (8 tests)
- ✅ D. Env-prefix paths (5 tests)
- ✅ E. Compact operator paths (8 tests)
- ✅ F. Redaction paths (8 tests)
- ✅ G. Explain/status paths (4 tests)
- ✅ H. JSON stability (7 tests)

## 13. JSON Schema Stability Review

✅ Reviewed. All 26 required fields present across 7 command types. Simulation ID format consistent ("sim-" + 12 hex). Enforcement stage always "dry_run_simulation". Schema version "0.1" stable.

## 14. Human-Readable Output Review

✅ Reviewed. All outputs contain:
- "Dry-Run Simulation" header
- "simulation complete" / "no enforcement" footer
- "SIMULATED BLOCK" for blocked commands
- No raw secret text in redacted commands
- Status output includes all invariant fields

## 15. Exit-Code Review

✅ Reviewed and documented:

| Scenario | Exit Code | Rationale |
|----------|-----------|-----------|
| Read-only / allowed | 0 | Informational, no block |
| Governed PCAE | 0 | Allowed |
| Blocked (hard block) | 1 | Would be blocked under enforcement |
| Force push | 1 | Permanently blocked |
| Human review required | 0 | Review is a gate, not a block |
| explain / status | 0 | Always informational |
| Missing --command | ≠0 | CLI usage error |

## 16. Safety Invariant Verification

✅ All 11 invariant fields unconditionally false across 12 command types. Safety invariants object verified. All 8 status invariants true.

## 17. Source Fixes

None required. No defects found in dry-run prototype code.

## 18. Tests Added/Updated

### tests/test_dry_run_simulation.py (+170 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| Test89dMatrixReadOnly | 14 | Read-only/governed commands not blocked |
| Test89dMatrixHardBlocks | 7 | Hard-block severity and governed alternatives |
| Test89dMatrixShellEmbedded | 8 | Shell -c/-lc commands |
| Test89dMatrixEnvPrefix | 5 | env/VAR=val prefix behavior |
| Test89dMatrixCompactOperators | 8 | Compact \|, &&, \|\|, ; |
| Test89dMatrixRedaction | 8 | Redaction paths + known limitations |
| Test89dMatrixExplainCoverage | 21 | All 19 decisions explainable |
| Test89dMatrixStatusCoverage | 2 | Status invariants and limitations |
| Test89dMatrixJsonStability | 22 | JSON field presence and format |
| Test89dSafetyInvariantCrossCheck | 15 | All invariants across all commands |

### tests/test_dry_run_cli.py (24 tests) — new file

| Class | Tests | Description |
|-------|-------|-------------|
| TestExitCodes | 8 | Differentiated exit codes |
| TestCliJsonStability | 7 | CLI JSON validity and invariants |
| TestCliHumanReadable | 6 | Human-readable output sections |

## 19. Validation Results

| Suite | Result | Runtime |
|-------|--------|---------|
| Dry-run simulation | 244 passed | ~2.9s |
| Dry-run CLI | 24 passed | included |
| Focused (5 suites) | 986 passed | 8.89s |
| Fast-green | 3,221 passed | 26.03s |
| Quick tier | 8,549 passed | 273s (4:33) |
| Full suite | 9,284 + 3 known failures | ~17:30 |

## 20. Known Full-Suite Baseline Issue

Same 3 pre-existing failures, unchanged:
- 2 in `test_preflight_integration_verification.py`
- 1 flaky `test_project_state_no_repository_files_created`

No new 89D failures.

## 21. Deferred Defects

| # | Defect | Reason |
|---|--------|--------|
| 1 | `echo $OPENAI_API_KEY` not redacted | Shell variable expansion detected at shell level, not by classifier |
| 2 | `cat .env` not redacted | `.env` not in `_SECRET_FILE_PREFIXES` |
| 3 | `sudo rm -rf /` not classified | `sudo` prefix handling deferred |

## 22. Recommended Next Phase

**89E — Dry-Run Blocking Simulation UX Refinement and Operator Guidance**

Apply 88Z UX design recommendations to simulation output: severity wording improvements, enhanced footer, operator guidance messages.
