# Phase 149O.18B Complete — HATP Mandatory Evidence Consumption Adapter

**Phase ID:** 149O.18B
**Mode:** implementation (bounded — Wave B of the 149O.17 plan; one new production module only)
**Predecessor:** 149O.18A (HATP Mandatory Cutover State Foundation — completed, VERDICT: HATP MANDATORY CUTOVER STATE FOUNDATION: IMPLEMENTED — READY FOR 149O.18B)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** HATP MANDATORY EVIDENCE CONSUMPTION ADAPTER: IMPLEMENTED — READY FOR 149O.18C
**Commits:** fe18eb0d, 5e62c17b, e2a2f184
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18B_HATP_MANDATORY_EVIDENCE_CONSUMPTION_ADAPTER.md`) is
the canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.18A complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001` and the 149O.17
implementation plan in full (§9.2's Wave B module design, §10.1's
`simulation_only` provenance discipline), then read the exact production
signatures of `hatp_evidence_store.py`, `hatp_signed_evidence.py`,
`hatp_ag_authority.py`, `human_approval_trusted_provenance.py`,
`rollback_approval_evidence.py`, and `permission_broker_foundation.py`
directly from source.

Added the sole new production module
`src/pcae/core/hatp_rollback_consumption.py`: an immutable
`HATPRollbackConsumptionRequest(evidence_id, operation_context)` whose
site (AG3/AG5) is structurally determined by which of the two existing
RAE context types is supplied; the canonical 7-step consumption chain
(`HATPEvidenceStore.load` → `resolve_rollback_approval_evidence_with_
hatp`, reused entirely unmodified → `build_permission_broker_request` →
`PermissionBroker().evaluate()`); and a typed, non-persistent
`HATPRollbackConsumptionResult(evidence_id, hatp_status, pb_decision,
reasons)` — exactly HMRC-REQ-075's four fields, `approval_present` never
exposed.

Resolved a design question the 149O.17 plan left implicit:
`HATPEvidenceStore` and `RollbackApprovalEvidenceStore` are two
independently-keyed stores, so the caller's single HSCE `evidence_id`
cannot double as the RAE Binding lookup key (that would be circular —
the HSCE ID is itself a digest that depends on the proof's `binding_id`
field). The loaded proof's own `binding_id` field — which already points
at the RAE Binding it self-asserts to attest to — is used as the RAE
lookup key instead; `verify_hatp_proof`'s existing, unmodified identity
check independently re-derives and cross-checks the expected
`binding_id` against whichever RAE Binding is actually resolved, so this
is never a caller-controllable pointer.

Implemented two production entrypoints differing only in a hardcoded
`simulation_only` (`evaluate_for_real_effect`=`False`,
`evaluate_for_advisory`=`True`), signature exactly `(request, root)` on
both, no provider/trust-store/approval-present override anywhere (F-2
closure). `hatp_ag_authority.py` and `hatp_mandatory_cutover.py` remain
completely unmodified; the new module imports neither, nor `agent.py`,
`commands/agent.py`, or `cli.py` (AST-confirmed).

Authored 69 new tests (34 unit + 35 phase-specific), both added to Fast
Green. Confirmed the full valid HATP/RAE chain (genuine proof, genuine
matching Binding) reaches `hatp_status=VALID` but PB still denies because
substrate readiness is never operational on this deployment — matching
149O.4/149O.5's own finding, now reproduced one layer up through this
adapter. Proved the ALLOW-path wiring itself via a deterministic,
non-production-reachable engine substitution (never a production
`allow=True` parameter). Confirmed `evaluate_for_real_effect`'s truthful
`simulation_only=False` request deterministically resolves PB `DENY`
under current POL-005, unweakened. Ran a full HMRC/HATP/rollback/PB
regression sweep; via a `git stash`-based A/B baseline comparison,
independently attributed every resulting failure to either a
pre-existing, unrelated cause, or a necessary, well-understood
consequence of this phase's required production module now existing
(historical snapshot assertions in eight older phase-verification
files). No AG3/AG5/rollback/Permission-Broker behavioral regression
found. Fast Green with the 11 necessarily-invalidated snapshot
assertions and 1 pre-existing-unrelated interpreter-version test
deselected: **5270 passed, 0 failed, 2 skipped** (raw undeselected: 5270
passed, 12 failed, 2 skipped).

No AG3/AG5 effect-boundary integration, no CLI plumbing, no cutover-mode
dependency, no legacy-authority change, no Permission Broker change, and
no rollback effect performed. HMRC-001 v1.0 and all six upstream
contracts remain byte-unchanged; `hatp_mandatory_cutover.py` (149O.18A)
remains byte-unchanged. B-149O-1..4 remain INDEPENDENTLY VERIFIED AT
HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. HATP
production remains NOT READY. Runtime remains `Observed/observe/
unavailable`.

**Recommended next phase:** 149O.18C — AG3 Mandatory Consumption
Integration.
