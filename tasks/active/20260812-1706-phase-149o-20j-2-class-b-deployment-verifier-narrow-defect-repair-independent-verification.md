# Task Contract

## Task ID

20260812-1706-phase-149o-20j-2-class-b-deployment-verifier-narrow-defect-repair-independent-verification

## Title

Phase 149O.20J.2: Class-B Deployment Verifier Narrow Defect Repair Independent Verification

## Status

active

## Mode

validation

## Goal

Independently verify 149O.20J.1's three narrow defect repairs (J-1 .pth executable-import, J-2 effective-GID, J-3 trusted-Git ACL) from primary source without modifying production source, contracts, or scripts.

## Allowed Files

- tests/test_phase_149o_20j_2_class_b_deployment_verifier_narrow_defect_repair_independent_verification.py
- docs/PHASE_149O_20J_2_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- src/pcae/core/hatp_bootstrap.py
- src/pcae/core/repository_identity.py
- src/pcae/core/hatp_mandatory_certification.py
- src/pcae/core/hatp_mandatory_cutover.py
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

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-12T17:06:11.224891+02:00
