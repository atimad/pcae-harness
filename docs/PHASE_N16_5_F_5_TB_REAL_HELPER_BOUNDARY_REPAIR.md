# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1

**Alias:** N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR
**Title:** Real Helper Boundary Repair — Same-File-Object Exec Inheritance + Canonical-Store Entrypoint Wiring
**Status:** COMPLETE

## 0. Governance / phase identity

**Predecessor Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1` (alias N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV).

**Predecessor final commit:** `5b1596b01a58f0c329af396036ea6b616a8e362d`. Predecessor terminal result **COMPLETE — NOT VERIFIED / BLOCKED**, independently re-confirmed from `PROJECT_STATUS.md` "## Current Phase", `.pcae/phase-completion-metadata.json` (`status: completed`), and `.pcae/phase-reports/latest.json` before any mutation, all agreeing with the phase-authorization prompt's own recap.

**Entry state:** branch `main`, HEAD == origin/main == `5b1596b0`, `origin/main..HEAD` = 0, tree clean, no conflicting active governed phase, agent lock available/acquired.

**CPIPC validation:** candidate `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1` independently derived via `pcae.core.phase_id` by the primary operator (not trusted from the authorization prompt's own precomputed text): exact one appended `.1` segment past the predecessor, `is_valid` True, `normalize(candidate) == candidate`, `same_series`/`same_branch` True vs. predecessor, `compare` = less, unique against `git log --all` at entry, no conflicting active governed phase.

**Predecessor defects independently reconstructed before repair** (both confirmed still present, unrepaired, by direct source read at phase entry — no later commit had touched either):
- `hpac_pawa_helper_os.py::execute_verified` still lacked `os.set_inheritable`.
- `hpac_pawa_helper_entrypoint.py::main()` still hardcoded `ProtectedStoreFoundation()`.

## 1. Delegated-worker disclosure

Per phase-authorization §62: DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED. A bounded delegated worker (isolated git worktree, no commit/push/finalization authority) performed initial source repair, test construction, and genuine-Linux verification on `hac-dell`. The primary operator independently re-verified every load-bearing claim before incorporating any of it — see §7 — and performed all commit/push/task-lifecycle/finalization steps itself.

## 2. Repair A — exec fd inheritance (`src/pcae/core/hpac_pawa_helper_os.py`)

**Root cause:** `verify_helper_executable` opens the candidate via a bare `os.open()`, which CPython (PEP 446) makes non-inheritable (`O_CLOEXEC`) by default. `execute_verified` then `execve()`s `/proc/self/fd/<fd>`. A directly-loaded ELF is unaffected (the kernel maps the image from the descriptor before the close takes effect), but the only realistic deployment shape — a shebang script, since it must run `hpac_pawa_helper_entrypoint.main()` — requires the kernel's `binfmt_script` handler to re-exec the *interpreter* with the original exec pathname as `argv[1]`; the interpreter's own re-open of that `/proc/self/fd/<fd>` path happens *after* the outer `execve` has already closed the O_CLOEXEC descriptor, failing `ENOENT`.

**Repair:** exactly one added statement — `os.set_inheritable(verified.fd, True)` — in the fork's child branch, immediately before `execve`, after all §6 provenance predicates have already been evaluated in the parent.

**Inheritance timing:** set only in the child, only immediately before exec — no window in the parent where an inheritable privileged descriptor exists.

**Exec-failure cleanup semantics:** unchanged — the child's `finally: os._exit(127)` terminates the whole process image on any `execve` failure, closing every descriptor it holds. No additional cleanup code was needed or added.

**Pathname-reopen disposition:** NONE INTRODUCED. The exec target remains the verified file *description* via `/proc/self/fd/<fd>`; no pathname is re-resolved.

**Script-shaped Linux positive result:** PASS — a realistic shebang script, opened/verified via the production `verify_helper_executable`, executed via the production `execute_verified`, ran successfully end-to-end on genuine Linux (`hac-dell`), independently re-confirmed by the primary operator.

**Replacement-after-open (directory-entry substitution) result:** PASS — unchanged, execution still resolves to the originally-verified object regardless of subsequent directory-entry mutation.

**Unrelated fd inheritance result:** PASS — regular-file, pipe, and socket descriptors opened before launch do not cross the exec boundary; only the one verified fd does (directly observed via `readlink` on the child's `/proc/self/fd/<fd>` in the delegated worker's test, independently re-run by the primary operator).

**Symlink/nonregular/digest regressions:** PASS — unchanged, all still rejected before exec.

## 3. Repair B — real entrypoint store profile (`src/pcae/core/hpac_pawa_helper_entrypoint.py`)

**Root cause:** `main()` unconditionally constructed `ProtectedStoreFoundation()` (NON_REAL), never the existing `RealCanonicalReadAdapter`.

**Design:** `resolve_store_profile(protected_root)` accepts the `real` profile **only** when the launcher-supplied bootstrap `protected_root` is byte-identical to the platform's single fixed canonical root returned by `pcae.core.hpac_foundation.resolve_hpac_protected_root()` — a function that "accepts no override input" by its own contract (independently confirmed by direct source read: `os.name`/`sys.platform` dispatch to two hardcoded constants, zero parameters). Any other root — missing, relative, differently spelled, a disposable test root, or an unsupported platform — raises and fails closed; `main()` maps that to a distinct nonzero exit code (`4`), never a `ProtectedStoreFoundation` fallback.

`build_helper_context(...)` then constructs the store: for the `real` profile, `RealCanonicalReadAdapter(HPACStoreAuthority.production())` — the exact adapter and authority-construction path the predecessor phase already introduced and wired for `certification_read`/`ceremony_entry`, reused verbatim, no second implementation. NON_REAL is reachable **only** through `build_helper_context`'s explicit, keyword-only, in-process `_test_only_store` parameter (default `None`), never from `main()`, the environment, argv, or a request field.

**Trusted profile source — independently re-verified by the primary operator against `src/pcae/core/hpac_foundation.py`, not merely trusted from the worker's report:**
- `resolve_hpac_protected_root()` (line 173): zero parameters, no env/override read, dispatches only on `os.name`/`sys.platform` to two hardcoded `Path` constants.
- `HPACStoreAuthority.production()` (line 614): `cls(resolve_hpac_protected_root(), HPACAuthorityClass.PRODUCTION, ...)` — takes no root argument at all.
- `_validate_production_boundary()` (line 639): `if not self._test_fixture_root and self.root != resolve_hpac_protected_root().absolute(): raise HPACAuthorityError("production HPAC authority cannot be redirected")` — an independent re-pin, not merely a constructor-time check.
- `_validate_production_boundary()` further re-runs the live `_effective_write_access` / `_ancestor_chain_safe` topology evaluation against the configured agent principal, and `_ensure_root` calls `_reject_symlink_components` on every path component.
- `_ensure_root` (line 663-667): for `HPACAuthorityClass.PRODUCTION`, a missing root is never auto-created — it raises `HPACAuthorityError("HPAC authority root is unavailable...")`. Independently confirmed live on `hac-dell`: `/etc/pcae/hpac/protected-root` does not exist there, so a `real`-profile construction attempt genuinely fails closed on that host rather than silently succeeding against nothing.

**Why request-injection has no effect:** `main()` builds the `HelperContext` before the one-shot socket is even connected; the request travels over the channel afterward and is parsed by a closed schema (`HelperRequest.from_mapping` rejects unknown fields) — structurally unreachable regardless of field name. Verified directly and via new regression tests (`profile`, `real`, `store_backend`, and arbitrary protected-root fields, both as top-level and nested inside `operation_params`).

**Why direct untrusted invocation cannot acquire REAL backing:** selecting `real` grants no privilege the invoking process does not already independently hold — the only accepted root value is the one fixed canonical root, so a hostile environment cannot redirect the real profile anywhere; the actual barrier remains the OS-level `0700` deployment-owner-only permissions plus the topology/symlink checks in `_validate_production_boundary`, which apply regardless of the profile-selection outcome.

**REAL failure → no fallback:** confirmed by code inspection and test — any exception during `build_helper_context`'s `real`-profile branch propagates to `main()`'s `except Exception: return EXIT_REAL_STORE_UNAVAILABLE`; `ProtectedStoreFoundation` is never constructed in `main()` at all (it is not even imported there any more).

**`certification_read` / `ceremony_entry` end-to-end result:** PASS — both genuinely reached `RealCanonicalReadAdapter` over a real (fixture-rooted, disposable-directory) `PRODUCTION`-class authority through an actually-launched, separate helper process on genuine Linux (independently re-run by the primary operator; see §7).

**Blocked write operations:** PASS — `admin_mutation`, `certification_write`, `presentation_evidence_write` remain fail-closed in the `real` profile (regression-tested; unchanged code path).

**REQ-033:** PASS — no helper module (`hpac_pawa_helper_os.py`, `hpac_pawa_helper_entrypoint.py`, `hpac_pawa_helper_launcher.py`, `hpac_pawa_helper_store_adapter.py`, `hpac_pawa_helper_operations.py`, `hpac_pawa_helper_protocol.py`) imports `hpac_protected_admin_writer` (independently grepped by the primary operator: only docstring mentions, zero import statements).

**Second-mint-path search:** none found; `build_helper_context` does not reference `_PRODUCTION_TEST_FIXTURE_SEAL` or any fixture constructor outside the explicit test seam.

**Launcher change:** NONE. `hpac_pawa_helper_launcher.py` is byte-unchanged — the design deliberately requires no new env var in its closed allowlist (independently confirmed via `git diff --stat` showing the file absent from the changed-file list).

## 4. Finding C — NOT repaired, out of narrow scope (disclosed, not silently dropped)

One predecessor-file test, `test_helper_substitution_after_verification_is_rejected`, fails both before and after this repair (independently reproduced by the primary operator on `hac-dell`). It exercises **in-place content mutation of the same inode** (truncate + rewrite the verified file's bytes at the same path), not directory-entry substitution. `/proc/self/fd`-anchored exec defends against directory-entry swaps (tested and passing) but not against in-place mutation of the already-open inode's content between verification and exec — genuinely out of reach of the same-file-object property as currently implemented, and outside this phase's two-defect scope (repairing it would require sealing the verified bytes into an independent copy, e.g. a `memfd`, which is a broader production redesign). Recommended for the fresh repair-IV successor's adjudication, not attempted here.

## 5. Production files changed

- `src/pcae/core/hpac_pawa_helper_os.py`
- `src/pcae/core/hpac_pawa_helper_entrypoint.py`

Test files changed/added:
- `tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` (one helper-script template updated — see §6)
- `tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py` (new, 60 tests)

No contract, schema, failure-vocabulary, dependency, or packaging file touched (independently confirmed: `git diff --stat` against `docs/contracts/*`, `pyproject.toml`, `hpac_protected_admin_writer.py` is empty).

## 6. Predecessor test-file template change (disclosed)

`_HELPER_SCRIPT_TEMPLATE` in `tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` previously invoked `main()` directly with a disposable-tmp-path `PAWA_HELPER_PROTECTED_ROOT` — exactly the redirectable-REAL assumption Repair B exists to forbid, so those two tests were red at baseline (caused by defect A, not this template). The updated template exercises the genuine production path (`build_helper_context` + `run_one_shot`) against the genuine `RealCanonicalReadAdapter` in a genuine subprocess; the only test-only substitution is the already-disclosed `_production_test_fixture` authority-seal seam, supplied through `build_helper_context`'s explicit `_test_only_store` parameter — never reachable from environment, argv, or request. Assertions themselves are unchanged.

## 7. Independent verification performed by the primary operator (not merely trusted from the delegated worker's report)

- Independently re-read both defect sites in current source at phase entry, before any repair.
- Independently derived and validated the CPIPC candidate via `pcae.core.phase_id` before task creation.
- Independently re-read `git diff HEAD` in the delegated worker's worktree, confirming exactly the 3 intentional file changes plus 1 new file, and that the diffstat matched the worker's own report.
- Independently re-read every changed line of `hpac_pawa_helper_os.py` and `hpac_pawa_helper_entrypoint.py` and confirmed the reasoning holds.
- Independently re-read `src/pcae/core/hpac_foundation.py` (`resolve_hpac_protected_root`, `HPACStoreAuthority.production`, `_validate_production_boundary`, `_ensure_root`) to confirm the trusted-profile-source argument, rather than trusting the worker's citation.
- Independently packaged the candidate source (git-archived HEAD plus the worker's uncommitted diff, applied via `git apply`) into a **fresh, separate disposable directory** on `hac-dell` (not the worker's own workspace), created a fresh venv, `pip install -e .`, and:
  - Ran `tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py` independently: **60 passed, 0 failed** — exact match to the worker's report.
  - Ran `test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` + `test_n16_5_f_5_tb_real_helper_store_launcher_iv.py` + `test_hpac_pawa_helper_protocol_foundation.py` + `test_n16_5_f_5_tb_replay_repair.py` together independently: **1 failed (Finding C, expected), 170 passed** — exact match (31+12+52+76=171 total).
  - Ran `test_n16_5_f_5_tb_helper_iv_r.py` independently: **12 failed, 123 passed, 2 skipped** — exact match; failures are a pre-existing hac-dell umask/group-writable artifact unrelated to this phase.
  - Set up a **separate, unmodified baseline** venv (same commit `5b1596b0`, no patch applied) on the same host and re-ran the same suites: **16 failed, 202 passed, 2 skipped** — confirming the exact 3-test delta (`test_genuine_separate_process_positive_integration`, `test_cross_process_replay_after_new_helper_process`, `test_hpac_pawa_helper_protocol_foundation::test_execute_verified_actually_runs_on_linux`) is what the repair fixes, and that Finding C (`test_helper_substitution_after_verification_is_rejected`) and the 12 iv_r failures are identical in both baseline and candidate — genuinely pre-existing, not introduced or masked.
  - Independently confirmed zero live-state mutation after all runs: `/etc/pcae` contains only the pre-existing root-owned `hatp/trust-store` (mtime unchanged, `Aug 15 08:55`), and `/etc/pcae/hpac/protected-root` does not exist on the host.
  - Deleted all disposable verification directories after use.
- Ran the full changed-suite set locally on macOS: **199 passed, 32 skipped, 0 failed** (Linux-only tests correctly skipped).
- Confirmed via `git diff --stat` that `docs/contracts/*`, `pyproject.toml`, and `hpac_protected_admin_writer.py` are byte-unchanged.
- Independently grepped all six helper modules for `hpac_protected_admin_writer` — zero import statements (REQ-033).

## 8. Broader regression tallies (exact)

| Suite | Baseline (Linux, `hac-dell`) | Candidate (Linux, `hac-dell`) |
|---|---|---|
| `test_n16_5_f_5_tb_real_helper_boundary_repair.py` | n/a (new) | 60 passed |
| `test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` | 3 failed, 28 passed | 1 failed (Finding C), 30 passed |
| `test_n16_5_f_5_tb_real_helper_store_launcher_iv.py` | 12 passed | 12 passed |
| `test_hpac_pawa_helper_protocol_foundation.py` | 1 failed, 51 passed | 52 passed |
| `test_n16_5_f_5_tb_replay_repair.py` | 76 passed | 76 passed |
| `test_n16_5_f_5_tb_helper_iv_r.py` | 12 failed, 123 passed, 2 skipped | 12 failed, 123 passed, 2 skipped |
| **Combined** | **16 failed, 290 passed, 2 skipped** | **13 failed, 353 passed, 2 skipped** |

macOS (all six files, local re-run by the primary operator plus the new file): 199 passed, 32 skipped, 0 failed.

## 9. Scope discipline confirmation

Caller migration: NONE. Packaging changes: NONE. Live helper install/register: NONE. Live protected-host writes: 0. Real FIDO2: NOT PERFORMED. Real presentation: NOT PERFORMED. Real certification: NOT PERFORMED. macOS status: unchanged, FAIL-CLOSED / NOT IMPLEMENTED (`UnsupportedPlatformProfile`, unmodified code path). Contract changes: NONE. Schema changes: NONE. Failure-vocabulary changes: NONE. Dependency changes: NONE. Runtime state: Observed / observe / unavailable (unchanged). Plugins/capabilities: 0/0 (unchanged). First governed runtime external effect: ABSENT / UNREACHABLE (unchanged). Writer-authority contract evolution: NOT BEGUN. No second writer mint path found.

## 10. Fresh repair-IV successor

**Recommended, derived, NOT begun:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1` (a valid direct `.1` child of this phase's own ID, independently derived and `is_valid` confirmed via `pcae.core.phase_id`), tentatively N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR-IV, which must independently re-run script-shaped same-file-object execution, descriptor inheritance/isolation, path substitution, peer credentials, transitive import/environment attacks, REAL entrypoint canonical-store selection, `certification_read`/`ceremony_entry` real-store, blocked writes, replay, no-authority-export, and no-generic-broker — and separately adjudicate Finding C and the `_HELPER_SCRIPT_TEMPLATE` change. **NOT BEGUN.**

## 11. Status matrix (per phase-authorization §59)

- Linux script-shaped same-file-object execution: **REPAIRED**
- Verified helper fd inheritance: **NARROW / EXEC-ONLY**
- Path substitution resistance: **PRESERVED**
- Unrelated fd isolation: **PRESERVED**
- REAL helper entrypoint: **CANONICAL-STORE ADAPTER WIRED**
- NON_REAL helper entrypoint: **DETERMINISTIC TEST-ONLY**
- `certification_read`: **END-TO-END REAL-STORE WIRED THROUGH GENUINE HELPER PROCESS**
- `ceremony_entry`: **END-TO-END REAL-STORE WIRED THROUGH GENUINE HELPER PROCESS**
- `admin_mutation`: **CORRECTLY BLOCKED BY WRITER-AUTHORITY CONTRACT**
- `certification_write`: **CORRECTLY BLOCKED BY WRITER-AUTHORITY CONTRACT**
- `presentation_evidence_write`: **CORRECTLY BLOCKED BY WRITER-AUTHORITY CONTRACT**
- Writer-authority contract evolution: **NOT BEGUN**
- Caller migration: **NOT BEGUN**
- Packaging/live deployment: **NOT BEGUN**
- macOS: **FAIL-CLOSED / NOT IMPLEMENTED**
- Boundary status: **REPAIRED / PENDING FRESH INDEPENDENT LINUX IV**
- F-5-B2: **BLOCKED PENDING FRESH IV + WRITER-AUTHORITY CONTRACT / MIGRATION / PLATFORM / PACKAGING / DEPLOYMENT SLICES**
- F-5: **CERTIFICATION BLOCKED**
- N-16-5: **NOT CLOSED**
- N-16-6: **OPEN / UNTOUCHED**
- N-16-7: **OPEN / UNTOUCHED — STRICTLY LAST**
- Runtime: **Observed / observe / unavailable**
- Plugins/capabilities: **0 / 0**
- First governed runtime external effect: **ABSENT / UNREACHABLE**

Recommended next: fresh independent Linux verification of this repair (§10). **NOT BEGUN.**

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
