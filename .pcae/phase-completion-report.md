# Phase 149G Complete — Repository-Wide Mutation Permission Coverage Wave 1 Independent Verification

**Phase ID:** 149G
**Mode:** Independent implementation verification (no production repair,
no contract amendment, no rollback implementation)
**Predecessor:** 149F (Repository-Wide Mutation Permission Coverage Wave
1 Implementation — completed, verdict WAVE 1 IMPLEMENTED — READY FOR
INDEPENDENT VERIFICATION)
**Date:** 2026-08-04
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149G_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_WAVE_1_INDEPENDENT_VERIFICATION.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149G independently verifies Phase 149F's Wave-1 implementation
without trusting 149F's own summary, tests, comments, or mutation
inventory assertions. Reconstructed the exact production diff
(`git diff 5392a7cd..c3e72b04 -- src/pcae/`): exactly three files —
new `src/pcae/core/mutation_permission.py`, plus hunks in
`src/pcae/core/agent.py` and `src/pcae/commands/phase.py` — all mapped
to the six declared Wave-1 sites, zero unrelated hunks. Reconfirmed
`push.py`, `task.py`, `permission_broker_foundation.py`,
`permission_broker.py`, and `docs/contracts/**` byte-unchanged.

Read `mutation_permission.py` from scratch, independent of 149F's prose.
Built an independently-authored adversarial test suite
(`tests/test_phase_149g_rwmpc_wave1_independent_verification.py`, 34
tests, deliberately not importing 149F's own test fixtures) using real
scratch git repositories and a local bare remote: broker
construction/evaluation failure, malformed results, real DENY/
HUMAN_REVIEW, AG1 staged-tree/HEAD/task-id freshness drift and
observation-failure fail-closed behavior, AG2 real push against a bare
remote plus freshness drift, PH2/PH3 exactly-once-evaluation and
no-direct-fallback AST-based control-flow proofs, AG4 first-write-
ordering (permission/freshness strictly before the apply loop's first
write/unlink) and EPR/ECP/approved_paths drift, rollback (AG3/AG5) still
routes to HUMAN_REVIEW via POL-004, TK1-3 confirmed behaviorally
unchanged (`task.py` byte-identical). Independently reconstructed the
13-site mutation inventory via grep/AST scan of `src/pcae/**` — no 14th
site found; `test_repository_wide_mutation_inventory_guard.py`
independently re-confirmed genuinely AST-semantic (5/5 passed).

**Two non-blocking findings recorded, not silently accepted:**
(F1) `mutation_permission.py`'s docstring claims to be the sole
non-`pcae push` `PermissionBrokerRequest` constructor, but a third,
pre-existing (Phase 109), provably inert observation-only caller exists
in `command_path_observation.py` — already correctly classified as
`pre_existing_observational` by 149F's own consumer-scope-inventory
test; the docstring phrasing is imprecise, not a functional gap.
(F2) AG2/PH2/PH3's alternate-push freshness check cannot detect a
concurrent external push to the remote (no `git fetch` before
re-observing "unpushed count") — empirically verified that the real
safety net for this race is git's own non-fast-forward rejection at the
transport layer, not Wave-1's freshness check; zero corrupt mutation
reaches the remote either way.

Full regression suite re-run identical to the 149F baseline:
`test_agent.py` 4236 passed, lifecycle/phase group 954 passed, Fast
Green 4391 passed. Chapter-148 regression 79 passed; PBPA 140 passed;
runtime 236 passed. One pre-existing (since 149F, not a 149G regression)
stale test assertion identified (F3, `test_phase_149d_...
test_src_pcae_untouched_by_phase_149d`) and CLTR's 5 wheel-build failures
confirmed as a sandbox environment limitation (`python -m build`
unavailable), not a code regression.

**Verdict: VERIFIED WITH NON-BLOCKING FINDINGS — RWMPC WAVE 1
IMPLEMENTATION CONFORMS.**

Zero `src/pcae/**` changes and zero `docs/contracts/**` changes by this
phase (`git diff --name-only <pre-149G>..HEAD -- src/pcae/` and
`-- docs/contracts/` both empty). RWMPC-001 remains v1.0, PBPC-001
remains v1.2, PBPA-001 remains v1.0, all unamended. Runtime reconfirmed
Observed/observe/unavailable before and after.

Chapter 149 remains **not complete**: AG3/AG5 rollback approval
architecture and TK1-3 re-affirmation remain outstanding. Recommended
next phase: **149H — Rollback Approval Evidence Architecture**. See
`docs/PHASE_149G_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_WAVE_1_INDEPENDENT_VERIFICATION.md`
for full detail.
