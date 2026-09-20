# Phase 150C Complete — Lifecycle Filename-Length Hardening Verified

Canonical Phase ID: `150C`

Alias: **PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R**

Status: **COMPLETE — LIFECYCLE FILENAME-LENGTH HARDENING VERIFIED.** Infrastructure-only repair; no HPAC/PAWA/PPA/Model E/foundation/PB/runtime file touched; no contract change.

CPIPC: a fresh short top-level phase number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), sibling to `150A` (blocked) and `150B` (completed). Fresh governed phase with its own identity, entry baseline, implementation commits, tests, Fast Green attribution, and completion lifecycle -- does not reinterpret or retroactively verify the original blocked 150A attempt.

Predecessor: N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR (150B) — **COMPLETE — STALE FAST GREEN HISTORICAL ASSERTIONS REPAIRED / TRUST GATE CLEAN.**

## What this phase did

Rooted at `origin/main` == `2be6fe01` (150B's own pushed final commit), in an isolated worktree/branch. Verified absent from ancestry, before mutation and before push: held source-conformance IV (`6c7f5cf4`, `2b8ad2aa`) and original blocked 150A commits (`72cdba16`, `d0b2a75a`). Neither touched, cherry-picked, merged, or published.

Independently reproduced the exact defect live against current `origin/main`: `write_quarantined_report()` in `src/pcae/core/phase_reports.py` embeds a canonical phase ID directly into a filename component. For 150B's own real rejected `.1`-extended candidate identity, the resulting `.blocked.md`/`.blocked.json` basenames are 258/260 UTF-8 bytes -- over the 255-byte portable filesystem component limit -- reproducing `OSError: [Errno 63] File name too long`.

Added `src/pcae/core/filename_safety.py` (new): `bounded_filename_component(raw, *, extension, max_bytes=255)` -- deterministic (not host-derived), UTF-8-byte-safe (never splits a code point), collision-resistant (SHA-256-derived 16-hex-char digest suffix over the full untruncated input), extension-preserving, and byte-for-byte backward compatible with every existing short filename. Routed `phase_reports.write_phase_report()`, `phase_reports.write_quarantined_report()`, and `tasks.create_task_contract()` through it.

Audited writer/reader symmetry across the full lifecycle: phase-report readers (promotion, notification dispatch, `read_latest_report`) resolve via the writer's returned path or the fixed short `latest.md`/`latest.json` names, never by reconstructing a filename from the phase ID -- no reader change needed. Task close/finish (`close_active_task`, used by `pcae task close`/`complete`/`finish`) renames the actually-discovered active-task file (found via `glob("*.md")`), never reconstructs a path from `task_id` -- no reader change needed either. Documented (not fixed, per this phase's narrow scope) a narrower, pre-existing gap: the diagnostic `pcae doctor task-memory --repair` helpers do reconstruct `tasks/{status}/{task_id}.md` from a bare task ID extracted from a diagnostic message, which would not resolve for an overlong task whose file was written under a bounded name -- a distinct, secondary self-repair path, not the primary create/close/finish lifecycle this phase's mandate covers.

Independently reviewed the original blocked 150A attempt's own production diff (`git show 72cdba16`) as read-only reference material: materially the same algorithm (same digest scheme, same 255-byte constant, same call sites). This phase's implementation was authored fresh and independently re-verified, not cherry-picked; convergence on the same design is corroborating evidence the model is sound.

Added a fresh 39-test suite (`tests/test_n16_5_f_5_tb_pcae_lifecycle_filename_length_hardening_r.py`) covering: short/exact-limit/one-byte-over boundaries, the real historically-blocked ID becoming safe, a UTF-8 Unicode byte-length matrix (Serbian Latin+combining, accented Latin, Cyrillic, CJK, emoji, stacked combining marks, mixed scripts), UTF-8-safe truncation never splitting a code point, determinism, shared-prefix collision resistance, distinct-digest-suffix proof, extension preservation, path-traversal safety of the real production composition, quarantine + promoted report writer/reader round trips with full phase-ID content-fidelity, a direct proof the old unbounded basename still overflows (the fix is not vacuous), full task create->lookup->finish->done round trip with a 500+ character title with full identity/title retained in content, historical short report/task names unaffected, 150B's two originally-repaired stale assertions re-run and confirmed still green, held/blocked-commit ancestry absence, and production-diff confinement.

While validating this phase's own Fast Green attribution, discovered two *additional* attributable failures: `tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py::test_this_phase_changed_zero_production_or_contract_files` and `::test_no_production_source_or_contract_changes_repo_wide` -- 150B's own fresh suite carried the identical current-HEAD-bound disease 150B itself was created to repair, in its own new tests. Repaired both using the identical Model FG-E pattern (rebound to 150B's own pinned final/pushed commit `2be6fe01` instead of `HEAD`) -- not excluded, not skipped, not xfail'd.

Self-hosting acceptance (exercised directly, section 20): a synthetic phase identity (243 bytes, longer than the real historically-blocked one, 223 bytes) and a derived task title -- task create, lookup (full title/ID recovered), close/move to done, phase-report promoted write, and phase-report quarantine write all succeeded, zero `ENAMETOOLONG`, full canonical identity recovered from every written artifact's content.

Files changed: `src/pcae/core/filename_safety.py` (new), `src/pcae/core/phase_reports.py`, `src/pcae/core/tasks.py`, `tests/test_n16_5_f_5_tb_pcae_lifecycle_filename_length_hardening_r.py` (new), `tests/test_n16_5_f_5_tb_fast_green_stale_assertion_repair.py`, `docs/PHASE_N16_5_F_5_TB_PCAE_LIFECYCLE_FILENAME_LENGTH_HARDENING_R.md` (new), `PROJECT_STATUS.md`, plus task-lifecycle bookkeeping. Zero `docs/contracts/**` changes; zero HPAC helper protocol/store-adapter/operations changes.

Governed Fast Green attribution (`pcae phase fast-green-attribution`, method `baseline_vs_candidate_isolated_worktree`): baseline `2be6fe01690d7ee81e854f6f8374a4086f318a9b` (origin/main, 150B's own pushed final commit), candidate `4dcd4c0ec4f5f547ede89957816bd7ce0c1a73be` (this phase's own checkpoint commit). One candidate-only failure surfaced, `tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record` -- the identical long-known-flaky node the predecessor and 150B phases both had to classify the same way. Adjudicated via `--rerun-node` (not a manual override). Final run: **`attributable_failures: []`.**

Regression suites: full `report|task|bootstrap|session_reporting|transition_valid` keyword sweep 20 failed / 2676 passed / 7 skipped, identical failure set (by name) to a `git stash -u`-isolated pre-edit baseline (20 failed / 2667 passed / 7 skipped) -- zero new failures. Targeted suite (`test_phase_reports*.py` + `test_task*.py` + both 150B stale-assertion-repair test files): 384/384 passed. `pcae check` passed.

## Disposition

**COMPLETE — LIFECYCLE FILENAME-LENGTH HARDENING VERIFIED.** Not claimed: N-16-5 closure, or that 150A itself is retroactively verified. No contract change, no foundation repair, no helper-admission implementation, no live host mutation. N-16-5 remains **NOT CLOSED**; N-16-6/N-16-7 untouched; runtime remains Observed / observe / unavailable.

Recommended next (not begun): reconcile/resume the held `N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV` (`6c7f5cf4`, `2b8ad2aa`), now that the filename-length limitation that motivated holding it no longer applies to a `.1`-style successor identity.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as historical governance evidence from a predecessor phase; not retroactively authorized, amended, erased, or normalized by this phase.
