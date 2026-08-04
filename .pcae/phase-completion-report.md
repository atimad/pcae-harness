# Phase 149H Complete — Rollback Approval Evidence Architecture

**Phase ID:** 149H
**Mode:** Architecture-only (no implementation, no contract freeze, no
production source or contract changes)
**Predecessor:** 149G (Repository-Wide Mutation Permission Coverage Wave
1 Independent Verification — completed, verdict VERIFIED WITH
NON-BLOCKING FINDINGS — RWMPC WAVE 1 IMPLEMENTATION CONFORMS)
**Date:** 2026-08-04
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149H_ROLLBACK_APPROVAL_EVIDENCE_ARCHITECTURE.md`) is the
canonical artifact of this phase.

---

## Executive Summary

Phase 149H resolves RWMPC-001's own BLOCKING finding (RWMPC-REQ-027) that
rollback-class Permission Broker coverage (AG3, AG5) is not satisfiable
without a legitimate `approval_present=True` evidence source. Reconstructed
AG3 (`execute_rollback`: `job_id` + `original_commit_sha`, `git revert`)
and AG5 (`build_rollback_execution`: `per_id` + derived `ecp_id`, direct
file restore) semantics, reconfirmed 149D's finding that AG5 is a
standalone, explicitly-invoked command (not automatic failure restore),
and independently re-checked every existing approval-shaped legacy flag
(`--promotion-authorized`, `--reviewed-by`, `approve_rollback`,
`change_approval_state`, `--approve-keep`, `--approved-by`, `--reason`) —
all remain unauthenticated self-declaration or bare state-flag toggles,
matching prior classification.

Inventoried the Canonical Human Governance Record (CHGR-001 — self-declared
identity, no structural operation-reference field, no expiry, no
revocation writer, but rigorous Confirmation/Publication/replay-guard/
integrity machinery and an existing, unamended Decision Template extension
point), the Typed Authority Model's `human_authorization` family (136
series — structurally closer shape: operation-bound family-locked
references, mandatory expiry, revocation, single-use — but contractually
walled off from CHGR per CHGR-001 §19.1 / TAMC-REQ-024-036 and scoped to a
different subsystem), Interactive Workflow Confirmation (IWC-001 —
explicitly not approval per RWMPC-REQ-023), Publication Execution
Ownership (PEC-001 — adopts self-declared operator-id as sufficient for
v1.0, names a stronger Model 3 as a future option), and Authority
Evaluation/AESIC (disclosure-only, explicitly barred from
`approval_present` per RWMPC-REQ-023).

**Selected architecture:** reuse CHGR's existing, unamended trust
substrate (identity capture, Confirmation ritual, Publication atomicity,
replay guard, content integrity) via a new, unamended-CHGR-001-compatible
Rollback Approval Decision Template, plus a new dedicated Rollback
Approval Binding record (new schema/contract, not built this phase)
structurally modeled on `human_authorization`'s proven operation-bound/
expiring/revocable/single-use shape without composing with that family.
Defined the derived `approval_present` rule (validated evidence only,
never caller-set), operation/repository-state binding, freshness/
revocation/replay/single-use semantics, and a 14-item threat model;
confirmed RWMPC-001/PBPA-001/PBPC-001 all require no amendment to consume
this architecture.

Two STRATEGIC_GAP findings recorded honestly (no stronger-than-self-
declared identity substrate anywhere in this repository; no technical
privilege separation between agent and human CLI invocation) — both
pre-existing, repository-wide trust-ceiling facts inherited from
already-frozen contracts, not new blockers.

**Verdict: ROLLBACK APPROVAL EVIDENCE ARCHITECTURE DEFINED.**

**Rollback permission implementation: NOT YET READY** — architecture
definition alone is not implementation readiness.

Zero `src/pcae/**` changes and zero `docs/contracts/**` changes by this
phase (`git diff --name-only 83887d27..HEAD -- src/pcae/` and
`-- docs/contracts/` both empty). RWMPC-001 remains v1.0, PBPC-001
remains v1.2, PBPA-001 remains v1.0, all unamended. Runtime reconfirmed
Observed/observe/unavailable before and after.

Chapter 149 remains **not complete**: AG3/AG5 rollback implementation and
TK1-3 re-affirmation remain outstanding. Recommended next phase:
**149I — Rollback Approval Evidence Contract Freeze**. See
`docs/PHASE_149H_ROLLBACK_APPROVAL_EVIDENCE_ARCHITECTURE.md` for full
detail.
