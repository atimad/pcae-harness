# Task Contract

## Task ID

20260828-2028-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-7-b1-b7-n1-n2-production-authority-repair-implementation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7: B1/B7/N1/N2 Production Authority Repair Implementation

## Status

done

## Mode

implementation

## Goal

Implement the frozen Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7 structural repairs for B1, B7, N1, N2 and HPAC Step 4, preserving hard NON-REAL rejection and leaving Gate 5/Gate 9/PB/runtime enablement out of scope.

## Allowed Files

- src/pcae/core/runtime_authority.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/hpac_verifier.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_7_B1_B7_N1_N2_PRODUCTION_AUTHORITY_REPAIR_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-*.json
- tests/**

## Forbidden Files

- src/pcae/core/runtime_invocation_approval_store.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- src/pcae/core/permission_broker_foundation.py
- docs/contracts/**

## Allowed Zones

- core
- tests
- docs
- tasks
- config

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
- No source behavior changes outside the three explicitly allowed production modules
- No execution authorization
- No raw Git commit or push outside the governed PCAE lifecycle
- No rollback
- No Gate 5/Gate 9 coordinator wiring, Permission Broker integration, real FIDO2/UI, provider-adapter modification, or runtime enablement

## Acceptance Criteria

- B1 projections are principal-derived, provenance-registered, and content-bound; copied or mutated projections fail closed.
- B7 dispatch request construction rereads the durable identity registry and rejects unregistered, stale, or tampered identities.
- N1 validation accepts only an approval ID resolved from the canonical approval store; caller-supplied approval objects fail closed.
- N2 approval creation consumes a freshly reverified verifier-authenticated human principal and never accepts caller-manufactured authority strings.
- HPAC Step 4 independently recomputes the canonical challenge digest before trust is emitted.
- NON-REAL identities are rejected at approval creation and validation; no runtime execution path is enabled.
- Gate 9, Permission Broker policy, approval-store structure, contracts, and provider adapters remain unchanged.

## Acceptance Checks

- python -m pytest -q tests/test_runtime_authority_production_repair_3w1r2b1r1117.py tests/test_hpac_verifier.py tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py tests/test_hpac_verifier_repair_independent_verification_3w1r2b1r1115a21.py
- python -m pytest -q tests/test_runtime_invocation_approval_store.py
- pcae health
- pcae status coherence
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T20:28:54.413565+02:00
