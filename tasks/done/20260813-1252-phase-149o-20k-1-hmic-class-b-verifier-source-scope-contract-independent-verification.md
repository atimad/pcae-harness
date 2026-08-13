# Task Contract

## Task ID

20260813-1252-phase-149o-20k-1-hmic-class-b-verifier-source-scope-contract-independent-verification

## Title

Phase 149O.20K.1: HMIC Class-B Verifier Source-Scope Contract Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify Phase 149O.20K's HMIC-001 v1.2->v1.3 Class-B verifier source-scope contract evolution; no production or contract modification

## Allowed Files

- docs/PHASE_149O_20K_1_HMIC_CLASS_B_VERIFIER_SOURCE_SCOPE_CONTRACT_INDEPENDENT_VERIFICATION.md
- tests/test_phase_149o_20k_1_hmic_class_b_verifier_source_scope_contract_independent_verification.py
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/hatp_mandatory_certification.py
- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Independent reconstruction of HMIC v1.2->v1.3 amendment completed without trusting 149O.20K's narrative
- No production source or contract modification made
- CBV-S1 and CBV-S10 remain OPEN

## Acceptance Checks

- pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T12:52:20.732897+02:00
