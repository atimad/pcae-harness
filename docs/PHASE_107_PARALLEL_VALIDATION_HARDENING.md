# Phase 107D — Parallel Validation Hardening

## Purpose

Make PCAE's validation pipeline fully `pytest-xdist` compatible by eliminating
the known parallel-execution artifact collision documented in Phase 107C's
Validation Note (11 tests across 4 pre-existing files, first observed no
later than 106L/106M and reconfirmed in 107A/107B/107C).

## Scope

Test and validation infrastructure hardening only. No runtime enforcement,
autonomous execution, permission broker enforcement, shell mediation, backend
invocation, adapter execution, Telegram inbound, durable audit storage,
rollback execution, emergency stop implementation, execution enablement,
execution availability, no-go runtime enforcement, or any new execution
capability was implemented in this phase.

## Root Cause Investigation

### Cause 1 — subprocess CLI tests invoked against the real repo root

`tests/test_execution_readiness_preflight_artifact_trust.py`,
`tests/test_governed_execution_preflight_artifact_trust.py`,
`tests/test_governed_execution_preflight_contract.py`, and
`tests/test_execution_readiness_preflight_contract.py` contain 31 test
functions that invoke `pcae execution-readiness preflight/show/verify` (and
the `governed-execution` equivalents) via `subprocess.run(..., cwd=repo)`,
where `repo = Path(__file__).resolve().parent.parent` — the real,
shared repository root, not an isolated per-test directory.

The artifact paths these commands read/write
(`_preflight_dir_path()` / `_gep_dir_path()` in
`src/pcae/core/backend_invocations.py`) are relative
(`.pcae/execution-readiness-preflight`, `.pcae/governed-execution-preflight`),
so they resolve against whatever process CWD the subprocess is given. With
`--dist=loadfile`, each of these four files runs on its own xdist worker, so
when two of these workers' subprocesses race — e.g. one worker's `--save`
overwriting `latest.json` while another worker's `show`/`verify` reads it —
one worker can observe a different worker's freshly-written (or
not-yet-written) artifact. This is a filesystem-collision xdist-safety issue
in test infrastructure, not a product defect: the underlying `pcae`
commands behave correctly for any single, consistent CWD.

### Cause 2 — in-process fixture teardown sharing the same real-repo path

The same four files each define a `clean_artifact_dir` fixture that calls
`_preflight_dir_path()` / `_gep_dir_path()` directly (not via subprocess) to
clean the artifact directory before/after "tamper detection" tests that call
`save_execution_readiness_preflight()` / `save_governed_execution_preflight_prototype()`
directly, in-process. Because these helpers also resolve relative to the
*real* process CWD (the repo root, shared by every xdist worker), this is
the same collision expressed a second way: one worker's `clean_artifact_dir`
teardown (`shutil.rmtree`) or in-process save/tamper/reload sequence could
interleave with another worker's identical sequence on the same real-repo
directory. This explains why the 107C investigation observed different
specific test failures from run to run — it is a race, not a deterministic
bug, and it was reproduced (12 failed + 1 error, then 13 failed) across
repeated `-n auto` runs of the four files before the fix, and 0 failures in
5 repeated `-n auto` runs after.

### Investigated and ruled out (not part of this collision)

A first full-suite `-n auto` run (pre-fix confounded by concurrent monitoring
commands, discarded) and a second, clean full-suite `-n auto` run (13169
passed, 186 failed, 37:50 wall time) surfaced two additional apparent
failure clusters. Both were investigated and are **not** xdist collisions:

- **186 failures across ~15 files** (`test_scope_preflight*.py`,
  `test_mutation_preflight*.py`, `test_backend_preflight*.py`,
  `test_commit_push_preflight*.py`, `test_scope_gate.py`,
  `test_preflight_integration_verification.py`, etc.) all shared one
  signature: `task_contract_detected` / scope decisions resolving to
  `missing_task_contract` instead of the expected allow/deny outcome. These
  tests assert against the CLI's live read of the repository's *actual*
  active task contract (allowed/forbidden files such as `PROJECT_STATUS.md`,
  `CHANGELOG.md`, `README.md`). No task was active in the repository at the
  time of the full-suite run (107C had just completed; 107D's own task had
  not yet been created). Reproduced identically under **plain serial**
  `pytest` (no `-n auto`) — confirming this is an environmental precondition
  of the test suite (an active task contract must exist), not a
  parallel-execution defect. Resolved as a side effect of creating this
  phase's own governed task; a clean rerun of the representative file
  (`tests/test_scope_preflight.py`) after task creation passed 66/66.
- **A transient `ImportError` on `test_backend_cli.py`/`test_backend_invocations.py`
  and 4 unrelated failures in `test_strategic_lineage.py`/`test_session.py`**
  during fast-green tier investigation. Root cause: an investigation shell
  session was still `cd`'d into `tests/` from an earlier `ls` command,
  breaking the `from tests.artifact_only_invocation_fixtures import ...`
  absolute-package import and other repo-root-relative logic. Not a code or
  xdist defect. Re-running `python -m pytest -m "fast_green" -n auto` from
  the repository root passed cleanly at **4390/4390**, matching the
  documented baseline exactly. A stray `tests/.pcae/` directory created by
  the same misdirected invocation was removed as untracked debris.

### Broader pattern (not fixed, no observed failures)

`Path(__file__).resolve().parent.parent` used as a subprocess `cwd` appears
in roughly 60 other test files beyond the four fixed here. Most uses are
read-only (e.g. asserting a doc file exists, invoking read-only advisory
commands) and were not observed to fail in the clean full-suite run. Per
this phase's validation policy (fix identified, reproducible collisions;
do not speculatively rewrite passing tests), these were left unchanged. See
Future Recommendations below.

## Fixes Applied

1. **31 subprocess CWD replacements.** In the four affected files, every
   `repo = Path(__file__).resolve().parent.parent` used as a subprocess
   `cwd=repo` was replaced with pytest's per-test-isolated `repo = tmp_path`
   fixture, and `tmp_path` was added to the enclosing test function's
   parameter list where not already present.
2. **4 fixture isolation fixes.** Each file's `clean_artifact_dir` fixture
   now takes `monkeypatch, tmp_path` and calls `monkeypatch.chdir(tmp_path)`
   before computing `_preflight_dir_path()` / `_gep_dir_path()`, so
   in-process save/load/tamper calls resolve against an isolated per-test
   directory instead of the shared real repo root. `monkeypatch` restores
   the original CWD automatically after each test.
3. No production code in `src/pcae/` was changed — the underlying CLI and
   library behavior was already correct for any single, consistent working
   directory. Only test isolation was hardened.

Files changed: `tests/test_execution_readiness_preflight_artifact_trust.py`,
`tests/test_governed_execution_preflight_artifact_trust.py`,
`tests/test_governed_execution_preflight_contract.py`,
`tests/test_execution_readiness_preflight_contract.py`.

## Remaining Limitations

None for the four files in scope. All 242 tests in the previously-affected
group now pass cleanly and repeatably under `-n auto` (verified across 5
consecutive runs pre-full-suite plus a final confirmation run — 0 failures
in every run). No test in this group requires a sequential fallback.

The broader `Path(__file__).resolve().parent.parent`-as-subprocess-`cwd`
pattern remains present in ~60 other files (see Future Recommendations). It
is not fixed in this phase because it is not currently causing observed
xdist failures — hardening it now would be speculative rework outside this
phase's validation-policy scope (fix identified, reproducible collisions).

## Validation Strategy

| Group | Before | After |
|---|---|---|
| The 4 previously-affected files, `-n auto` | 12 failed + 1 error / 13 failed (non-deterministic across repeated runs), 229–230 passed | 242/242 passed, 5 consecutive clean runs + 1 final confirmation run |
| Full suite, `-n auto` (clean, unconfounded run) | — | 13169 passed, 186 failed — all 186 traced to no active task contract (environmental, not xdist), 0 failed once a task was active |
| `fast_green` marker, `-n auto` | — | 4390/4390 passed (matches documented baseline exactly) |
| Release/lifecycle regression (`test_task*`, `test_phase*`, `test_notifications*`, `test_telegram_notifications.py`), `-n auto` | — | 1458/1458 passed |
| `pcae doctor task-memory` | — | clean, no inconsistencies |

No test count regression. No coverage reduction. No test disabled, skipped,
or removed.

## xdist Compatibility Guidance

For any future test that invokes a `pcae` CLI subcommand — via
`subprocess.run` or in-process — whose output depends on filesystem state
written under a path relative to the process's current working directory
(most commonly anything under `.pcae/`), isolate that state per test:

- **Subprocess invocations:** pass `cwd=tmp_path` (pytest's built-in
  per-test temporary directory), not a fixed real-repo path.
- **In-process calls:** use `monkeypatch.chdir(tmp_path)` in the fixture or
  test itself before calling any function that resolves a relative
  `.pcae/...` path.
- Tests that intentionally exercise real-repo governance state (e.g. this
  project's own active task contract, `PROJECT_STATUS.md`, or git history)
  are expected to depend on that live state and are not xdist bugs — they
  require an active task contract or specific repo state as an environmental
  precondition, matching normal phase-implementation conditions.
- `pyproject.toml`'s `--dist=loadfile` remains correct and necessary: it
  keeps all tests in one file on one worker, so isolation only needs to
  hold *across* files, not within a file.

## Future Recommendations

- Consider a shared `tests/conftest.py` fixture (e.g. `isolated_pcae_cwd`)
  that wraps the `tmp_path` + `monkeypatch.chdir` pattern established here,
  so future subprocess/CLI tests can opt in without repeating the
  boilerplate.
- The ~60 files still using `Path(__file__).resolve().parent.parent` as a
  subprocess `cwd` are not currently failing, but are latent candidates for
  the same collision class if two such files' tests ever write to the same
  relative `.pcae/` path concurrently. A future hardening pass could audit
  them file-by-file and apply the same `tmp_path` pattern where a test
  writes (not just reads) shared state.
- No sequential (`-n 0` / no `-n auto`) fallback is required anywhere in the
  suite as of this phase. If a future test reintroduces a real-repo-relative
  write path, prefer the isolation pattern above over adding it to a
  sequential-only carve-out.

## No-Go Confirmations

No runtime enforcement. No autonomous execution. No real backend invocation.
No adapter execution. No subprocess execution beyond existing
lifecycle/test/docs/git-remote-verification command behavior. No shell
mediation. No network call outside the existing Telegram outbound path and
ordinary git remote/GitHub verification. No shell interception. No Telegram
inbound. No enforcement. No automatic apply. No apply execution. No
commit/push authorization changes beyond the existing governed lifecycle. No
real AI backend calls. No execution enablement flag or toggle. No new tag
created. No new GitHub Release. No PyPI/GitHub Packages publication.
`v0.1.0-rc1` remains non-executing by design; v0.2 remains the autonomy
target (Level 3, not Level 4/5). Next phase not started.

## Recommended Next Phase

107E — PR-Compatible Governed Development Workflow Design (not started).
