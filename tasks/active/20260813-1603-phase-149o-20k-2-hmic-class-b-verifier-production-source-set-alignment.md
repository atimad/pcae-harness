# Task Contract

## Task ID

20260813-1603-phase-149o-20k-2-hmic-class-b-verifier-production-source-set-alignment

## Title

Phase 149O.20K.2: HMIC Class-B Verifier Production Source-Set Alignment

## Status

active

## Mode

implementation

## Goal

Align live production HMIC (_FROZEN_AUTHORITY_BEARING_FILES) from 25 to the independently verified 28-file HMIC-001 v1.3 target; bind three Class-B verifier modules into HMIC identity; no readiness integration, no Class-B provisioning, no CBV-S1 closure

## Allowed Files

- src/pcae/core/hatp_mandatory_certification.py
- tests/test_phase_149o_20k_2_hmic_class_b_verifier_production_source_set_alignment.py
- docs/PHASE_149O_20K_2_HMIC_CLASS_B_VERIFIER_PRODUCTION_SOURCE_SET_ALIGNMENT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
- src/pcae/core/hatp_mandatory_cutover.py
- src/pcae/core/permission_broker.py
- src/pcae/core/permission_broker_foundation.py
- scripts/hatp_certification_admin.py

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

- Production _FROZEN_AUTHORITY_BEARING_FILES exactly equals the independently-verified 28-file HMIC-001 v1.3 target
- Existing 25 files preserved as a strict subset; delta is exactly the three Class-B verifier modules
- Each of the three new files is independently proven digest-sensitive; missing-file fails closed
- Zero production consumers of the Class-B verifier island; no import/semantic cycle introduced
- CBV-S1 not closed; CBV-S10 untouched; no readiness/provisioning/certification/PB change

## Acceptance Checks

- pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T16:03:12.710049+02:00
