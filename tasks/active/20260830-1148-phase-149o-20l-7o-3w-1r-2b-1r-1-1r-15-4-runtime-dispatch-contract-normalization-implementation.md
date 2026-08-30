# Task Contract

## Task ID

20260830-1148-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-15-4-runtime-dispatch-contract-normalization-implementation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4: Runtime-Dispatch Contract Normalization Implementation

## Status

active

## Mode

implementation

## Goal

Normalize the frozen runtime-dispatch contracts to the independently verified Gate 5->Gate 9 architecture and add the durable authority-generation-snapshot representation required before Gate-10 planning, per the .1R.15.1 planning blueprint (sections 7-20) and this phase's prompt.

Contract normalization: RDGO-001 v3.0 -> v3.1 (V-2 seq-3 ownership, V-3 RIASC digest wording, V-13-3-1 Gate-6/7 PB-policy ownership, V-13-5-1 Gate-8 three-layer containment model, V-15-1 create-only-linearization + zero-I/O generation-token recheck); PBRD-001 v2.0 -> v2.1 (V-4 human_authority_binding representation-equivalence clause); RIASC-001 v3.0 errata cross-reference note (V-3); HPAC-001 v2.0 -> v2.1 (durable generation-snapshot semantics; HPAC-AUTHORITY-CONSUMPTION/2.0 -> /2.1); RE No-Go Registry schema 1.0 -> 1.1 (per-decision / environmental-readiness / advisory classification of all 17 entries). Both .1R.15.1 MAJOR-candidate judgment calls adjudicated MINOR with primary-source justification.

Durable snapshot + production wiring: add the authority_generation_binding closed binding object to HPAC-AUTHORITY-CONSUMPTION/2.1; embed the S1 snapshot durably in the consumption record; keep S1/S2 write-path ordering unchanged; the snapshot is data (verification evidence), not a bearer token. N-15-3-2: wire a production authority_generation_resolver factory whose approval_generation folds the current approval-store resolvability/currentness (RIHAC-001 §14 -- no separate approval-revocation store exists in the frozen v2 model; approval revocation is transitively covered by principal/credential/lifecycle/expiry, and the resolver additionally commits the current resolved approval record digest + a forward hook for a future §14 append-only revocation artifact).

Phase-document errata: .1R.9 §13.5 (lock self-contradiction), .1R.13.1 §11.2/§13/§16.2, .1R.13.2 prose, .1R.14/.1R.15 wording superseded by V-15-1. Cross-reference sweep of the active contract set. Contract evolution manifest. Contract/durable-schema/resolver traceability tests. Gate-9 + Gate 5-8 regressions. Fixed-SHA A/B attribution (no xdist). Do not begin .1R.15.5. Do not plan or implement Gate 10. Do not enable execution; runtime stays not_implemented / Observed / observe / unavailable; POL-005 unchanged.

## Allowed Files

- docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md
- docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md
- docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md
- docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_9_GATE_5_GATE_9_PRODUCTION_AUTHORITY_COORDINATOR_INTEGRATION_PLANNING.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_1_GATE_7_RUNTIME_ENFORCEMENT_AND_GATE_8_SHELL_GATE_CONSUMPTION_INTEGRATION_PLANNING.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_2_GATE_7_RUNTIME_ENFORCEMENT_COORDINATOR_INTEGRATION_IMPLEMENTATION.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_14_GATE_9_ATOMIC_AUTHORITY_CONSUMPTION_COORDINATOR_INTEGRATION_IMPLEMENTATION.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_GATE9_ATOMIC_AUTHORITY_CONSUMPTION_COORDINATOR_INDEPENDENT_VERIFICATION.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_2_GATE_9_ATOMIC_CONSUMPTION_SERIALIZATION_SEMANTICS_REPAIR.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_3_INDEPENDENT_VERIFICATION_GATE_9_SERIALIZATION_SEMANTICS_REPAIR.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_4_RUNTIME_DISPATCH_CONTRACT_NORMALIZATION_IMPLEMENTATION.md
- src/pcae/core/runtime_dispatch_gate9.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- tests/**
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/**

## Forbidden Files

- src/pcae/core/runtime_dispatch_gate5.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/runtime_dispatch_gate7.py
- src/pcae/core/runtime_dispatch_gate8.py
- src/pcae/core/permission_broker_foundation.py

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
- No Gate 10 module, symbol, plan, or phase ID
- No second global lock or transaction mechanism
- No commit
- No push
- No rollback

## Acceptance Criteria

- RDGO-001 v3.1, PBRD-001 v2.1, HPAC-001 v2.1, RIASC-001 errata, RE No-Go Registry schema 1.1 published; no unplanned contract file changed
- HPAC-AUTHORITY-CONSUMPTION/2.1 durable authority_generation_binding implemented; S1/S2 write-path ordering unchanged
- N-15-3-2 production authority_generation_resolver completeness wired and tested
- Fixed-SHA A/B: CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0; UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0
- Runtime remains not_implemented / Observed / observe / unavailable; POL-005 unchanged; Gate 10 without a phase ID

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-30T11:48:29.353908+02:00
