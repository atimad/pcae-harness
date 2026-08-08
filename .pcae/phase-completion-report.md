# Phase 149O.15 Complete — HATP Mandatory Production Consumption Contract Freeze

**Phase ID:** 149O.15
**Mode:** documentation (contract-freeze-only — no production, existing-contract, or CLI change; implements nothing)
**Predecessor:** 149O.14 (HATP AG3/AG5 Mandatory Production Consumption Architecture — completed, pushed, ARCHITECTURE SELECTED, recommended this contract-freeze phase next)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** HMRC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION (not VERIFIED)
**Commits:** e1c3653c, 945af762, 4638fac0
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full documents
(`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` and
`docs/PHASE_149O_15_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_FREEZE.md`)
are the canonical artifacts of this phase. Froze a new, standalone
contract — **HMRC-001 v1.0** (HATP Mandatory Rollback Consumption
Contract) — governing mandatory AG3/AG5 HATP evidence consumption:
explicit `--hatp-evidence-id <evidence_id>` (identical flag name on
both `pcae remote rollback execute` and `pcae rollback --per-id`);
canonical `HATPEvidenceStore.load(evidence_id)` →
`HATPSignedEvidenceEnvelope`, reused unmodified; fresh consumption-time
verification on every attempt via the existing, unmodified
`resolve_rollback_approval_evidence_with_hatp` conjunction, with no
caching of verification/approval/PB-decision state anywhere; Permission
Broker remaining the sole permission-decision owner. Resolved, rather
than deferred, the central open question 149O.14 left unsettled:
whether a PB `ALLOW` obtained under today's architecture's fixed
`simulation_only=True` request can authorize a real rollback effect.
It cannot — PBPC-001 already establishes a truthful
`simulation_only=False` request deterministically resolves `DENY`
given today's `execution_unavailable` posture (`COMP-002`/`COMP-008`
`not_implemented`) — frozen as a new invariant, **MC-14, the
Effect-Truthful PB Requirement**: a real effect requires a truthfully
non-simulated, `ALLOW`-resolving PB decision, which today's
architecture cannot produce, so `HATP_MANDATORY` does not by itself
guarantee rollback availability — an explicit, accepted, frozen
consequence. Also froze: a closed, fail-closed enumeration of every
evidence/verification failure mode with no post-cutover legacy
fallback under any of them; exact old-hook disposition
(`hatp_evidence_id` retained/canonical; `hatp_proof`/`hatp_evidence`
deprecated/internal-only, forbidden as production caller input on the
mandatory path); a closed list of forbidden caller-supplied inputs
(approval booleans, PB decisions, mode overrides); the three-state
`LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY` cutover model, no
direct skip, no reverse transition for ordinary principals, Class-B
Protected Activation Authority only; a new admin-owned Cutover Record
design under the existing Class-B protected HATP trust root (never
agent-writable `.pcae/`), closed v1 schema, and an explicit
monotonicity mechanism (a separate write-once deployment-baseline
marker) so record deletion/corruption can never silently downgrade a
previously-activated deployment; exact legacy-command/
`rollback_approval_state` disposition across all three modes with an
explicit no-dual-authority guarantee; preservation of every existing
AG3/AG5 structural precondition as distinct from human-approval
authority; the exact AG3 (inside `execute_rollback`, immediately
before `_run_git_revert`) and AG5 (inside `build_rollback_execution`,
immediately before the first real file mutation) mandatory-gate
placement, covering direct function calls, not merely the CLI;
MC-1..MC-14 security invariants (13 carried forward from 149O.14 plus
the new MC-14); and the full 45-scenario attack matrix, reconciled
exactly against the 149O.14 architecture document (independently
re-counted, no reduction, no addition), each now citing the specific
`HMRC-REQ` clause producing its expected result. Also removed, as
task-lifecycle hygiene, a pre-existing stale duplicate active-task file
left over from the 149O.6 era, flagged by `pcae doctor task-memory`.
New 37-test contract-verification file (all independently re-run and
passing) confirms the contract's own frozen identity/counts/
self-consistency and, independently of the contract's own prose,
re-verifies the underlying current-state production facts it depends
on — AG3/AG5 call graphs, inert Wave-7 hooks, zero-kwarg real callers,
`HATPEvidenceStore.load`'s explicit-ID-only shape, `hatp_ag_authority`'s
unconditional `simulation_only=True`, and `ExecutionDisabledRule`/
POL-005's exact trigger condition. Zero production source or
pre-existing contract files touched (`git diff --name-only --
src/pcae/` empty; `git diff --stat` empty for each of HSCE-001,
HATP-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001 — independently
confirmed). `149O.12B-Obs-PY39-1` (Python 3.9/3.10 timestamp defect):
does not block 149O.16 (independent contract verification); schedule
its repair before the first mandatory-consumption *implementation*
phase that follows 149O.16. B-149O-1..4 remain INDEPENDENTLY VERIFIED
AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED,
not closed by this phase. HATP production remains NOT READY. Runtime
remains Observed / observe / unavailable. Recommended next phase:
149O.16 — HATP Mandatory Production Consumption Contract Independent
Verification (no implementation before 149O.16 completes).
