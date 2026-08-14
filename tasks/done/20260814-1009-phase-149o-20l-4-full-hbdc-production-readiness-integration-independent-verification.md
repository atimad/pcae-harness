# Task Contract

## Task ID

20260814-1009-phase-149o-20l-4-full-hbdc-production-readiness-integration-independent-verification

## Title

Phase 149O.20L.4: Full-HBDC Production Readiness Integration Independent Verification

## Status

done

## Mode

validation

## Goal

Independently verify Phase 149O.20L.3's production implementation of HMRC-001 v1.1's eighth mandatory Full-HBDC Class-B readiness prerequisite, trusting nothing from L.3's report or tests. Adjudicate L.3's cbv_s1_regression_reconfirmed contradiction against live HMIC frozen-scope source. Verification-only: no production, contract, or Class-B verifier change.

## Allowed Files

- tests/test_phase_149o_20l_4_full_hbdc_production_readiness_integration_independent_verification.py
- tasks/active/*.md
- tasks/done/*.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- src/pcae/core/hatp_mandatory_cutover.py
- src/pcae/core/hatp_mandatory_certification.py


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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-14T10:09:56.602946+02:00
