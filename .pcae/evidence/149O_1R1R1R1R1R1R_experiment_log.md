# Experiment log — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R

Predecessor phase (`...1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R`) finalized with
`CONTAMINATION ROOT CAUSE: UNRESOLVED` after consuming only 2 of its
authorized 30 targeted pytest invocations (~2 of 60 minutes). Per this
phase's Phase-Completion Recovery Rule, this phase inherits the
**unused** completion envelope rather than a fresh reset:

- **Inherited budget:** 28 additional targeted pytest invocations / 58
  additional minutes, whichever is reached first.
- **Predecessor preserved byte-for-byte**; not reopened, not rewritten.

C0 = `2bf5fe403f1b996990a59e44edf1aadab14a16ef`. Environment unchanged from
predecessor: `.venv/bin/python` = Python 3.9.6, pytest 8.4.2,
pytest-xdist 3.8.0, `pytest-randomly` not installed, `PYTHONHASHSEED`
unset, `pyproject.toml` `[tool.pytest.ini_options]` unchanged
(`testpaths = ["tests"]`, `pythonpath = ["src"]`,
`addopts = "--dist=loadfile"`; note `--dist=loadfile` has no effect
without `-n`, and none of this phase's invocations passed `-n`, so every
run below is genuinely single-process).

## Reconstructed predecessor experiment inventory (read-only; no budget consumed)

1. Invocation #1 (predecessor): full-suite `--collect-only` identity
   watch, 41791 tests collected in 5.10s, 0/44612 log lines show
   `CHANGED=True` for `id(HPACStoreAuthority)` → **CONTAMINATION STAGE IS
   NOT COLLECTION/IMPORT.**
2. Invocation #2 (predecessor): 22-file multiprocessing/ProcessPoolExecutor
   cluster + victim, single process, 88.19s → `15 failed, 1348 passed`;
   all 15 failures are the pre-existing HISTORICAL-MOVING-AUTHORITY
   fixed-SHA-diff defect (0 reference the victim); victim's own 125 tests
   clean. **FALSIFIED.**
3. Predecessor's static narrowing: unfiltered `tests/` grep for any
   `del sys.modules[...]`/`.pop(...)`/`sys.modules[...] = ...` → only
   private/synthetic keys, cleaned up in `finally`; zero canonical
   `pcae`-prefixed key ever deleted/reassigned. Zero `importlib.reload(`
   call sites in `src/pcae`.

## New static narrowing this phase (no pytest invocation consumed)

- Re-verified, file-by-file, **every** `importlib.reload(` call site in
  the entire `tests/` tree (a broader, distinct search from the
  predecessor's `sys.modules` key search — this checks the *call
  mechanism* directly, not just key deletion/reassignment). 21 call
  sites across ~20 files were enumerated and each target inspected:
  - 15 CLTR-authority (`136a*`) files — already covered by the
    predecessor's "15 CLTR-authority test files + victim" composition
    (falsified there).
  - `test_cltr_rehearsal_135u_independent_verification.py` reloads
    `pcae.core.runtime_introspection` — unrelated module.
  - `test_hatp_cli.py` reloads `pcae.commands.hatp` (aliased `hatp_cli`)
    — unrelated module.
  - `test_phase_149o_20l_7k_hmic_frozen_source_scope_amendment_for_deploymentbinding_producer.py`
    reloads `pcae.core.hatp_mandatory_certification` — unrelated module.
  - `test_schema_runtime_boundaries.py` reloads `pcae.core.schema_runtime`
    — unrelated module.
  - `test_hpac_verifier_repair_independent_verification_3w1r2b1r1115a21.py`
    reloads `pcae.core.hpac_verifier`, but **exclusively inside a
    `subprocess.run([sys.executable, "-c", ...])` child process** — the
    test file's own docstring explicitly documents this as deliberate
    avoidance of exactly this class of in-process test-isolation hazard.
    Confirmed via source read: the `importlib.reload(hv)` line is inside
    the `script = "..."` string passed to `subprocess.run`, never
    executed in the pytest worker process itself.
  - **None** of the reload targets is `pcae.core.hpac_foundation`,
    `pcae.core.human_principal_registry`, or any module that re-exports/
    rebinds `HPACStoreAuthority`. This is new evidence beyond the
    predecessor's key-deletion search: it independently rules out the
    `importlib.reload()` *call* mechanism specifically (as opposed to
    manual `sys.modules` surgery), codebase-wide, for the two classes at
    issue.
- Searched for **name rebinding** (as opposed to attribute-patching) of
  `HPACStoreAuthority` anywhere in `tests/`/`src/`: found only
  `monkeypatch.setattr(HPACStoreAuthority, "complete_multi_write",
  counted)` (2 files, `.1R.30R.3.6` / `.1R.30R.3.6.1`) — this patches a
  **method attribute** on the existing class object (auto-restored by
  pytest's `monkeypatch` fixture at teardown) and does not rebind the
  class object itself; not a viable identity-divergence mechanism.
  Confirmed both production import sites
  (`hpac_protected_admin_writer.py:44`, `human_principal_registry.py:17`)
  import `HPACStoreAuthority` from the same canonical
  `pcae.core.hpac_foundation` via ordinary top-level
  `from ... import (...)` — no lazy/deferred/aliased import that could
  observe a different binding.

## Invocation #1 — new bounded adjacent-file composition (control)

- **Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_3r_decomposition_adjudication.py
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
- **Hypothesis:** the file immediately preceding the victim in normal
  alphabetical collection order (`...30r_3_3r_decomposition_adjudication.py`)
  is the cheapest, most evidence-neutral next composition to test before
  committing budget to wider ones.
- **Order:** normal alphabetical, single process.
- **Outcome:** `1 failed, 141 passed in 2.96s`. The 1 failure
  (`test_rhamp_001_byte_unchanged_since_baseline_a`) is the pre-existing
  fixed-baseline-vs-moving-HEAD contract-diff guard (same
  HISTORICAL-MOVING-AUTHORITY class as predecessor invocation #2's 15
  failures) — not the RHAMP class-identity signature. Victim's own tests
  all pass.
- **Conclusion: FALSIFIED** (as sole trigger). Confirms the contamination
  is not carried by merely the single immediately-preceding file.
- **Budget consumed:** 1 invocation; ~3s.

## Invocation #2 — execution-time (not collection-time) identity-watch, partial coverage

- **Command:** disposable pytest plugin
  `identity_exec_watch.py` (scratch, not in repository) recording, after
  every test's teardown, `id(sys.modules["pcae.core.hpac_foundation"]
  .HPACStoreAuthority)` and `id(sys.modules["pcae.core.
  human_principal_registry"].HumanPrincipalRegistryStore)`, aborting the
  instant either changes since first observed. `PYTHONPATH` prepended
  with the scratch dir; `-p identity_exec_watch`. Full `tests/` tree,
  normal alphabetical order, single process, no xdist, watchdog cap
  1200s (20 min, inside the remaining budget).
- **Hypothesis:** the predecessor only checked class identity during
  `--collect-only` (which executes every module's top-level imports but
  no test bodies/fixtures). This checks the same identity signal during
  actual **execution** (fixture setup, test bodies, teardown) — the
  contamination stage already established as TEST-EXECUTION — which the
  predecessor did not attempt.
- **Outcome:** watchdog terminated the run (SIGTERM) at the 1200s cap;
  reached **~14% of the suite** (≈80 of 571 files) with **zero identity
  changes observed** for either watched class. No crash, no
  `INTERNALERROR`, no `/tmp/identity_change_found.txt` written.
- **Extrapolation:** at the observed rate (~14%/20min single-process),
  full-suite coverage would require **~140 minutes** — this matches (and
  now empirically reconfirms, rather than merely estimates) the
  predecessor's own finding that a full 571-file single-process pass is
  infeasible inside any single bounded phase's diagnostic budget (the
  predecessor's own attempt aborted at ~7% after ~10-11 minutes with the
  same ~2.5-hour extrapolation).
- **Budget consumed:** 1 invocation; 20.0 minutes (two earlier `-p`
  loading misconfigurations that exited before collecting/running any
  test — a bad file-path plugin spec, then a `pytest_exit_now` hookimpl
  name colliding with pytest's hook-validation — are not counted as
  invocations; each exited in <1s before any test ran).
- **Evidence artifact:** `identity_exec_watch.py` (scratch, preserved
  alongside this log's originating session only; not additive to the
  repository, per this phase's scope for bounded temporary diagnostic
  instrumentation outside existing product/test files) +
  `/tmp/identity_exec_watch_run.log` (scratch, not repository-durable —
  the finding, not the raw log, is canonicalized here).

## Invocation #3 — clean-context PAWA/PPA/RHAMP/configured-agent band

- **Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_configured_agent_resolution_source_iv.py
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1_independent_verification_configured_agent_identity_threading_repair.py
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_configured_agent_identity_threading_repair.py
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py`
- **Outcome:** `7 failed, 258 passed, 3 skipped in 5.09s`. All 7 failures
  are the same pre-existing HISTORICAL-MOVING-AUTHORITY fixed-SHA/
  diff-scope guard class (`test_iv_entry_sha_is_current_head`,
  `test_host_protected_root_generation_and_helper_digest_unchanged`,
  `test_ppa_current_generation_and_installation_absent_on_host`,
  `test_production_diff_scope_bounded_to_topology_verifier`,
  `test_no_removed_or_skipped_tests_in_repair_diff`,
  `test_repair_diff_touches_only_expected_test_files`,
  `test_no_ppa_install_or_root_admin_functions_referenced_in_diff` — all
  compare against a fixed historical baseline SHA and necessarily diverge
  as HEAD moves forward with each subsequent phase's commits). **Zero**
  RHAMP class-identity signature. Configured-agent-identity threading
  repair and the RHAMP/PAWA/protected-presentation relevant band remain
  meaningful and preserved.
- **Budget consumed:** 1 invocation; ~5s.

## Invocation #4 — fresh phase-specific IV suite rerun (clean-context confirmation)

- **Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_contamination_isolation_iv.py`
- **Outcome:** `16 passed in 0.36s` — unchanged from predecessor.
- **Budget consumed:** 1 invocation; <1s.

## Budget accounting at stop

- **4 of 28 additional maximum pytest invocations used** (28 remaining
  after this phase's use; predecessor's own 2/30 remain separately
  accounted in its own report and are not re-spent here).
- **~20.1 of 58 additional maximum minutes used** (dominated by
  Invocation #2's 20-minute watchdog-capped execution-time trace).
- **Stop condition reached: B — CONCRETE TECHNICAL BLOCKER.** The single
  remaining evidence-supported diagnostic avenue capable of either
  producing a causal reproducer or conclusively extending the
  reload/sys.modules/monkeypatch closure to 100% dynamic coverage —
  continuing the execution-time identity trace to the end of the
  571-file suite, or reproducing the actual failure via a full-suite run
  to compare against the trace — requires, at the empirically observed
  single-process execution rate, **~140 minutes** of wall-clock pytest
  execution to complete a single pass. That structurally exceeds this
  phase's entire 58-minute diagnostic ceiling on its own (let alone
  leaving room for a second confirmatory pass, per this phase's own
  causal-proof requirement of a fresh-process repeat). This is not "more
  candidates remain" (the candidate list for the *reload/monkeypatch/
  duplicate-definition* mechanism class is now exhaustively closed, both
  statically over the whole codebase and dynamically over ~14% of real
  execution); it is a quantified, budget-driven infeasibility of the
  only remaining test capable of either confirming or refuting that
  mechanism class over its full domain, or of directly capturing the
  actual failure with instrumentation attached.
- Diagnostic experimentation stopped here per this phase's own governing
  rule: continuing to consume budget on a differently-sized slice of the
  *same* blind/broad execution-time trace, without a new falsifiable
  hypothesis narrower than "somewhere in the untested ~86% of the
  suite," would repeat the predecessor's own already-identified
  infeasible-full-prefix pattern rather than changing the method.
