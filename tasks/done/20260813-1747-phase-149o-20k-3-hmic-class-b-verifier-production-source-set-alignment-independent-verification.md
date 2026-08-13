# Task Contract

## Task ID

20260813-1747-phase-149o-20k-3-hmic-class-b-verifier-production-source-set-alignment-independent-verification

## Title

Phase 149O.20K.3: HMIC Class-B Verifier Production Source-Set Alignment Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify Phase 149O.20K.2's production alignment of live HMIC to HMIC-001 v1.3 Class-B verifier source-scope target (28-file set); no production or contract modification

## Allowed Files

- docs/PHASE_149O_20K_3_HMIC_CLASS_B_VERIFIER_PRODUCTION_SOURCE_SET_ALIGNMENT_INDEPENDENT_VERIFICATION.md
- tests/test_phase_149o_20k_3_hmic_class_b_verifier_production_source_set_alignment_independent_verification.py
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

- Independent reconstruction of K.2's production alignment completed without trusting K.2's report/tests
- No production source or contract modification made
- CBV-S1 adjudicated at HMIC contract + production source-identity boundary only if all criteria independently verified; CBV-S10 remains OPEN

## Acceptance Checks

- pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T17:47:09.698795+02:00
