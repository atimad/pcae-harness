# Phase 149E Complete — Repository-Wide Mutation Permission Coverage Implementation Plan

**Phase ID:** 149E
**Mode:** Implementation planning only (zero `src/pcae/**` changes;
zero `docs/contracts/**` changes; no `POL-001..012` semantic change;
no `POL-013+`; no new Permission Broker consumer; no new runtime
capability)
**Predecessor:** 149D (Repository-Wide Mutation Permission Coverage
Contract Independent Verification — completed, verdict VERIFIED WITH
NON-BLOCKING FINDINGS, recommended 149E)
**Date:** 2026-08-03
**Status:** completed
**Pushed:** not_pushed (staged pre-push; promote via `pcae phase
complete` after `pcae push`)

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149E_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_IMPLEMENTATION_PLAN.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149E independently re-verifies RWMPC-001 v1.0's 13-site
inventory and every per-site disposition against current source (zero
drift since 149D) and produces an implementation-ready Wave-1 plan for
the six not-yet-wired `EXECUTION_CLASS_MUTATION` sites (AG1, AG2, AG4,
PH1, PH2, PH3; PU1/PU2 already certified under PBPC-001 v1.2).

**Architecture:** one new shared primitive module
`src/pcae/core/mutation_permission.py`, generalizing `push.py`'s
certified `_evaluate_push_permission`/`_PushDecisionSnapshot`/
`_validate_push_permission_freshness` pattern rather than inventing a
new one, plus three thin per-class adapters (commit, alternate-push,
source-mutation). Commit-class freshness binds to `(HEAD, git
write-tree staged-content identity, task_id)`; promotion-apply
freshness reuses the existing ECP/EPR/PER integrity model; alternate
push (AG2 directly broker-wired, PH2/PH3 routed into AG2's shared
dispatcher, not into `pcae push`'s own Chapter-148 machinery) requires
no refactor of `push.py`.

AG4's self-modification risk (`pcae promote` targeting `src/pcae/**`)
is deliberately left without a new mechanical hard block in Wave 1,
per RWMPC-REQ-019's explicit prohibition on over-gating via
misclassification — `BROKER_WIRE` coverage itself is RWMPC-001's
stated mitigation. Rollback (AG3, AG5) and task-finish (TK1-TK3) are
explicitly excluded, each with an individually recorded
re-affirmation criterion, not silently dropped.

**Verdict: IMPLEMENTATION PLAN COMPLETE — WAVE 1 READY.** Four
Observation-level findings recorded; zero Blocking findings.

Production diff: `git diff --name-only 674df97a..HEAD -- src/pcae/`
empty (this phase adds only documentation and status/planning
bookkeeping, no production changes). Existing-contract diff: `git diff
--name-only 674df97a..HEAD -- docs/contracts/` empty (RWMPC-001
remains v1.0, PBPC-001 remains v1.2, PBPA-001 remains v1.0, all
unamended). Runtime reconfirmed Observed/observe/unavailable before
and after. Recommended next phase: **149F — Repository-Wide Mutation
Permission Coverage Wave 1 Implementation** (scoped exactly to AG1,
AG2, AG4, PH1, PH2, PH3), to be followed by **149G — Wave-1
Independent Verification** before any Chapter 149 completion claim.
See
`docs/PHASE_149E_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_IMPLEMENTATION_PLAN.md`
for full detail.
