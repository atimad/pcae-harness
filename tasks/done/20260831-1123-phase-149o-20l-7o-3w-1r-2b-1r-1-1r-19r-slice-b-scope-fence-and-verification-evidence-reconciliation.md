# Task Contract

## Task ID

20260831-1123-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-19r-slice-b-scope-fence-and-verification-evidence-reconciliation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19R: Slice-B Scope-Fence and Verification-Evidence Reconciliation

## Status

done

## Mode

implementation

## Goal

Repair governance/evidence, stale guard-maintenance, and N-20-4 error-normalization defects from .1R.20: widen 3 HPAC Layer-1/2 consumer-inventory guards by exactly the 2 authorized Slice-B importers (no wildcard); recover 2 consequential meta-guards; provenance-preserving .1R.19 erratum + corrected A/B; narrow begin_effect_attempt loser-error normalization (N-20-4); repaired-tree fixed-SHA A/B 0/0. No contract change, no Slice C, no execution enablement.

## Allowed Files

- src/pcae/core/runtime_dispatch_attempt_lifecycle.py
- tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py
- tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py
- tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py
- tests/test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py
- tests/test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py
- tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19_DISPATCH_ATTEMPT_DURABLE_LIFECYCLE_IDEMPOTENCY_AND_3S_2_1_PREREQUISITE_REPAIRS.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_19R_SLICE_B_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/**

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-31T11:23:23.888452+02:00
