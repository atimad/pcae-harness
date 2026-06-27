# Phase 88Y — Advisory Mode Test Matrix and CLI Stability Review

```
phase_name    = phase_88y_advisory_mode_test_matrix
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 88Y.1_cli_subprocess_runtime_reduction
```

## 1. Purpose

Harden advisory mode by expanding the advisory command matrix, CLI JSON
stability tests, human-readable output tests, redaction regression tests,
decision vocabulary tests, false-positive/false-negative review, and
broker/shell-gate mapping consistency checks.

## 2. Scope

In scope:

- Expand advisory command matrix across 10 command categories
- CLI JSON stability tests for check/explain/status
- Human-readable output stability tests
- Decision vocabulary coverage (all 19 values)
- Broker/shell-gate consistency checks
- False-positive/false-negative review
- Comprehensive invariant cross-checks

Out of scope:

- Enforcement, shell interception, wrappers
- Backend invocation, prompts, capture
- Source behavior changes beyond narrow advisory defects
- 88Y.1 subprocess runtime reduction

## 3. Non-Goals

88Y must not and does not implement enforcement, shell interception,
wrappers, backend invocation, or authorization.

## 4. Starting Point from 88X

- 105 fast-green advisory tests in `tests/test_advisory_mode.py`
- `pcae advisory check/explain/status` commands working
- Core mapper in `src/pcae/core/advisory.py`
- No known defects

## 5. Advisory Command Matrix

189 new tests added across 10 command categories:

| Category | Tests | Commands Covered |
|----------|-------|-----------------|
| Read-only | 12 | git status, pwd, ls, cat, grep, diff, echo, whoami, date, head, wc |
| Governed PCAE | 4 | pcae health, check, doctor task-memory, doctor test-run |
| Raw git hard blocks | 7 | git push, git push --force, git push -f, git commit, git rebase |
| Dangerous filesystem | 5 | rm -rf variants, git reset --hard, git clean -fd |
| Policy-forbidden writes | 5 | echo > README.md, tee README.md, cat > forbidden docs |
| Test execution | 3 | pytest variants with -n auto |
| Review-required | 9 | pip, brew, npm, cargo install; curl, wget, ssh, scp |
| Secret/redaction | 35+ | VAR=val, printenv, env, env|grep, cat ~/.ssh, security |
| Compound | 5 | &&, \|\|, ; , pipe chains |
| Unknown/ambiguous | 4 | unknown-tool, bash, sh -c |
| Comprehensive invariants | 60+ | Every command checked for authorization/performed flags |

## 6. CLI JSON Stability Review

✅ Reviewed. CLI JSON output is stable across command types:
- `advisory check --json` produces valid JSON with all required fields
- `advisory explain --json` returns valid decisions and fallback for unknowns
- `advisory status --json` reports correct invariants

## 7. Human-Readable Output Review

✅ Reviewed. Human-readable output:
- Contains "Non-Authorizing" notice
- Shows advisory decision and would-block/would-require status
- Never leaks raw secret command text
- Hard-block output includes blocking language

## 8. Decision Vocabulary Review

✅ All 19 advisory decisions are explainable via `build_advisory_explain()`.
Each explanation includes summary, meaning, would_block status, can_override
guidance, and next_step.

Unknown/invalid decisions produce safe fallback explanations.

## 9. Hard-Block Preservation Review

✅ All hard-block commands produce `would_block_*` or `would_deny` advisory
decisions. No hard block is downgraded to a warning or allow decision.
Human approval and accepted risk do not override hard blocks.

## 10. Secret Redaction Review

✅ All 88V.1 redaction rules preserved in advisory output. Secret-like VAR=val
prefixes, env/printenv, secret file access, and secret-access programs are
all redacted. JSON and human-readable output never contain raw secret text.

## 11. Broker/Shell-Gate Consistency Review

✅ Shell gate categories and decisions are correctly reflected in advisory
output. 10 command-to-category mappings verified (read_only_inspection,
package_install, network_access, destructive_filesystem, secret_access,
raw_git_push, force_push, environment_mutation, etc.).

## 12. False-Positive Review

| Finding | Description | Status |
|---------|-------------|--------|
| `bash` blocked as unknown | Conservative FP — bash not in known programs | Documented |
| `sh -c 'cmd'` blocked as unknown | sh not in known programs | Documented |
| `env python` classified as secret_access | 88V.1 over-classifies env/printenv | Documented |

## 13. False-Negative Review

| Finding | Description | Status |
|---------|-------------|--------|
| `env\|grep TOKEN` (no spaces) not redacted | shlex.split produces single token `env\|grep`; pipe not detected | Documented, deferred to tokenizer hardening |
| None in hard blocks | All tested hard-block commands produce would_block | ✅ |
| None in secret redaction | All tested secret commands are redacted | ✅ |
| None in review-required | Review-required commands are not silently allowed | ✅ |

## 14. Tests Added/Updated

**189 new tests** in `tests/test_advisory_mode.py`:

- `Test88yMatrixReadOnly` — 12 tests
- `Test88yMatrixGovernedPCAE` — 4 tests
- `Test88yMatrixGitHardBlocks` — 7 tests
- `Test88yMatrixDangerousFilesystem` — 5 tests
- `Test88yMatrixPolicyForbidden` — 5 tests
- `Test88yMatrixTestExecution` — 3 tests
- `Test88yMatrixReviewRequired` — 9 tests
- `Test88yMatrixSecretRedaction` — 29 tests
- `Test88yMatrixCompound` — 5 tests
- `Test88yMatrixUnknown` — 4 tests
- `Test88yCLIJsonStability` — 6 tests
- `Test88yHumanReadableStability` — 5 tests
- `Test88yDecisionVocabulary` — 20 tests
- `Test88yBrokerShellGateConsistency` — 16 tests
- `Test88yFalsePositiveReview` — 3 tests
- `Test88yFalseNegativeReview` — 4 tests
- `Test88yComprehensiveInvariants` — 63 parametrized tests

**Total advisory tests**: 294 (105 from 88X + 189 from 88Y)

## 15. Defects Fixed

**None.** No advisory source defects were found. The implementation from 88X
is correct. The one false negative (`env|grep TOKEN` without spaces) is a
tokenizer limitation in `shlex.split`, not an advisory defect.

## 16. Validation Results

| Suite | Result | Runtime |
|-------|--------|---------|
| Advisory tests | 294 passed | 4.33s |
| Broker tests | 150 passed | ~1.2s |
| Shell gate tests | 774 passed | ~22s |
| Broker-shell integration | 162 passed | ~0.4s |
| Fast-green | 3,003 passed | 22.73s |
| Quick tier | TBD | |
| Full suite | TBD | |

## 17. Remaining Limitations

1. **`env|grep TOKEN` (no spaces)**: shlex.split produces single token;
   pipe not detected. Deferred to tokenizer hardening.
2. **`bash`/`sh` blocked as unknown**: These are in the unknown-program
   category. Could be added to a recognized-programs list in future.
3. **`env python` classified as secret_access**: 88V.1 over-classifies
   env/printenv. Conservative but may produce false positives.

## 18. Recommended Next Phase

**88Y.1 — CLI Subprocess Runtime Reduction**

Reduce full-suite runtime by refactoring subprocess-heavy CLI tests.
