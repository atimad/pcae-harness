# Experiment log — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R

B0 = `346a409853b2ac7f6ac9efa90c77d03068f64705`. Environment: `.venv/bin/python`
= Python 3.9.6, pytest 8.4.2, pytest-xdist 3.8.0 (unchanged from predecessor).
`pytest-randomly` confirmed **not installed** (`pip show pytest-randomly` →
not found) — collection/execution order is deterministic (default
alphabetical-by-file), not the source of any apparent nondeterminism.
`PYTHONHASHSEED` unset (default). `pyproject.toml`
`[tool.pytest.ini_options]` unchanged since D0/B0: `testpaths = ["tests"]`,
`pythonpath = ["src"]`, `addopts = "--dist=loadfile"`.

Budget: maximum 30 pytest invocations OR 60 minutes, whichever first.
Static/source inspection (grep, `git show`, code reading) does not consume
this budget.

## Prior-phase candidates already falsified (not repeated)

1. The 15 `importlib.reload`-using CLTR-authority test files + victim, single
   process → victim fully clean; unrelated wheel/sdist cluster failures only.
   **FALSIFIED** (predecessor phase).
2. The full 55-file RHAMP/PAWA/CLTR-authority "clean-in-isolation" thematic
   cluster (incl. victim) → `2148 passed, 1 skipped`. **FALSIFIED**
   (predecessor phase).
3. Full 571-file alphabetical prefix minus slow/integration/phase_closure
   markers → aborted at ~7% after ~10-11 min; extrapolated 2.5+ hours to
   complete. **INFEASIBLE within any single bounded phase budget**
   (predecessor phase).

## New static/source narrowing (this phase; no pytest invocation consumed)

- Broadened predecessor's targeted grep (which searched only for
  `reload`/`sys.modules` mutation *naming* `hpac_foundation`,
  `HPACStoreAuthority`, `human_principal_registry`, or
  `hpac_protected_admin_writer`) to an **unfiltered** search of
  `del sys.modules[...]` / `sys.modules.pop(...)` / `sys.modules[...] = ...`
  across the entire `tests/` tree for **any** key at all. Result: every hit
  targets a private, uniquely-generated, or otherwise non-canonical
  `sys.modules` key (e.g. `hatp_bootstrap_isolated_<uuid>`,
  `_historical_topology_snapshot`, `hist_blob_149o_20j6`), each cleaned up
  in a `finally`/`pop(..., None)`. **Zero** test file anywhere in the suite
  deletes or reassigns a canonical `pcae`/`pcae.core`/`pcae.core.*`
  `sys.modules` key. This closes off "some test file reloads/re-registers
  a `pcae`-prefixed module" as a candidate mechanism entirely — not just
  for the four originally-named modules, but for the `pcae` package as a
  whole.
- Confirmed **zero** `importlib.reload(` call sites anywhere in `src/pcae`
  (production code never reloads itself). Two `importlib.import_module`/
  `__import__` call sites exist in `src/pcae` (`hatp_mandatory_cutover.py`,
  `commands/phase.py`); neither targets `hpac_foundation` or a dependent,
  and both are ordinary cached imports (no reload semantics).
- Confirmed `HPACStoreAuthority` (`src/pcae/core/hpac_foundation.py:514`) is
  an ordinary class with no metaclass, no `ABCMeta`/`register()`, and no
  `__instancecheck__` override — ruling out a virtual-subclass /
  `ABCMeta`-cache-invalidation explanation for the `isinstance` divergence.
- Confirmed no second, spoofed class definition anywhere sets
  `__module__`/`__qualname__` to mimic `pcae.core.hpac_foundation.
  HPACStoreAuthority` (grepped for `class.*HPACStoreAuthority`,
  `__qualname__.*HPACStoreAuthority`, `__module__.*hpac_foundation` outside
  the canonical definition and its docstring cross-references).
- Confirmed no duplicate physical copy of `hpac_foundation.py` or
  `human_principal_registry.py` exists in the working tree outside
  `src/pcae/core/` (the only other filesystem copies are inside
  `.claude/worktrees/agent-*` sibling git worktrees, which `testpaths =
  ["tests"]` does not collect and which no test file's `spec_from_file_
  location`/`git worktree add` usage imports in-process — the one test
  that builds a disposable pre-repair worktree
  (`test_phase_149o_20l_7o_3c_3_2_...`) invokes it exclusively via
  `subprocess.run(["pcae", ...])`, a genuinely separate OS process, never
  an in-process import).
- All `spec_from_file_location(name, path)` call sites in `tests/` (37
  files) pass a private/synthetic `name` (e.g. `"hw_script_2l3"`,
  `"hatp_certification_admin"`); none passes a canonical dotted `pcae.*`
  name, so none can silently replace the canonical cached module even
  without an explicit `sys.modules[name] = mod` assignment under the real
  key.

## Invocation #1 — full-suite collection-only identity watch

- **Command:** `PYTHONPATH="<scratch>:src" .venv/bin/python -m pytest
  --collect-only -q -p no:cacheprovider -p identity_watch_plugin tests/`
- **Hypothesis:** if the class-identity split occurs at import/collection
  time (any test module's own top-level imports transitively re-triggering
  a fresh `hpac_foundation` import), a disposable diagnostic pytest plugin
  recording `id(sys.modules["pcae.core.hpac_foundation"].
  HPACStoreAuthority)` after every collected item/file would show at least
  one `CHANGED=True` transition somewhere across the full suite.
- **Candidate set:** entire `tests/` tree (41791 tests collected).
- **Order:** default pytest collection order (alphabetical-by-file,
  unmodified).
- **Start/end:** single foreground invocation, wall-clock **5.10s**
  (`41791 tests collected in 5.10s`).
- **Exit code:** 0.
- **Outcome:** **0 of 44612 recorded log lines show `CHANGED=True`.** The
  class identity of `HPACStoreAuthority` never changes during collection
  of the *entire* 41791-test suite (first appears at log line 5796 once
  the module is first imported by an earlier test file, then remains
  `cls_id=41178078736` — spot-checked — through to the end of the log).
- **Evidence artifact:** disposable plugin
  `/private/tmp/claude-501/.../scratchpad/identity_watch_plugin.py`
  (not part of the repository; not additive to product/test files, per
  scope §"bounded temporary diagnostic instrumentation outside existing
  product/test files") + its output log (same scratch directory,
  not repository-durable — the finding itself, not the raw log, is what
  is canonicalized here).
- **Budget consumed:** 1 invocation; ~0.1 min wall-clock.
- **Conclusion:** **CONTAMINATION STAGE IS NOT COLLECTION/IMPORT.** This is
  new evidence beyond the predecessor phase, which left contamination
  stage entirely unaddressed. Combined with the exhaustive reload/
  sys.modules narrowing above, this means the trigger — whatever it is —
  must act during test **execution** (fixture setup, test body, or
  teardown) of some file(s) preceding the victim, since collection alone
  (which does execute every test module's top-level imports) never
  reproduces it.

## Invocation #2 — multiprocessing/ProcessPoolExecutor cluster + victim

- **Command:** `.venv/bin/python -m pytest -q -p no:cacheprovider <22
  files using multiprocessing/ProcessPoolExecutor, sorted> tests/
  test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
- **Hypothesis:** the Gate5-10/dispatch-attempt test files that spawn real
  child processes (via `multiprocessing`/`ProcessPoolExecutor`) are a
  previously-untested cluster (disjoint from both prior-phase compositions)
  whose subprocess spawn (macOS default `spawn` start method, which
  bootstraps a fresh interpreter and re-imports `pcae` fresh in the child)
  could plausibly leave parent-process state that later confuses class
  identity for objects that cross the process boundary.
- **Candidate set:** the 22 files matched by
  `grep -rl "multiprocessing\|ProcessPoolExecutor" tests/` + the victim
  (23 files total), collected/run in that order, single process, no xdist.
- **Order:** files passed in sorted alphabetical order on the command line,
  preserving normal pytest per-file collection order within that set.
- **Start/end:** single foreground invocation, wall-clock **88.19s**.
- **Exit code:** 1.
- **Outcome:** `15 failed, 1348 passed in 88.19s`. **Zero** failures
  reference `merged_rhamp_mechanism.py` (grepped explicitly — 0 hits). All
  15 failures are the pre-existing HISTORICAL-MOVING-AUTHORITY defect
  (fixed-SHA `git diff <old-SHA> HEAD -- src/pcae`/contract-identity
  assertions that necessarily break against current, moving HEAD — already
  classified by the predecessor phase, CAIR-triggered, non-blocking,
  unrelated to this contamination): `test_no_contract_file_changed`,
  `test_production_scope_since_baseline_is_the_single_new_file`,
  `test_no_unpushed_divergence_at_verification_entry`,
  `test_widened_guard_module_passes_at_head[...]` (×2),
  `test_production_scope_since_baseline_is_exactly_one_new_file`,
  `test_no_downstream_production_consumer_of_gate6_symbols`,
  `test_55_production_diff_since_phase_entry_is_only_gate7`,
  `test_56_normative_contract_diff_since_phase_entry_is_only_reprc`,
  `test_hbdc_001_byte_identical_since_7h_baseline`,
  `test_hatp_bootstrap_and_repository_identity_byte_identical_since_7h`,
  `test_producer_and_admin_script_untouched_by_this_phase`,
  `test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline`,
  `test_no_unplanned_contract_file_changed_since_task_open`,
  `test_runtime_posture_unchanged_and_no_new_first_effect_call_site`.
  The victim's own 125 tests are clean (among the 1348 passed).
- **Evidence artifact:** `/tmp/run2_mp_plus_victim.log` (not repository-
  durable; the finding, not the raw scratch log, is canonicalized here).
- **Budget consumed:** 1 invocation (2 total); ~1.5 min wall-clock (~1.6
  min total).
- **Conclusion: FALSIFIED.** The multiprocessing/ProcessPoolExecutor
  cluster does not reproduce the RHAMP class-identity signature.

## Budget accounting at stop

- **2 of 30 maximum pytest invocations used** (both completed to exit,
  neither left running — `ps aux | grep pytest` empty after each).
- **~2 minutes of ~60 minutes maximum wall-clock diagnostic time used.**
- Diagnostic experimentation was stopped **before** budget exhaustion
  because the two concrete, evidence-motivated remaining hypotheses this
  phase could construct from source inspection (import/collection-stage
  contamination; the multiprocessing/subprocess-spawn cluster) were both
  tested and falsified, the reload/sys.modules mechanism class was closed
  off entirely (broader than the predecessor's own closure of it), and no
  further specific, falsifiable, budget-feasible hypothesis could be
  constructed from available evidence without resuming the
  independently-confirmed-infeasible (predecessor phase) blind full-prefix
  bisection. Per this phase's own governing rule, stopping here with
  `CONTAMINATION ROOT CAUSE: UNRESOLVED` is the required, valid outcome
  rather than continuing to consume budget without a new hypothesis.
