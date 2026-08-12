# Task Contract

## Task ID

20260812-2330-phase-149o-20j-7-class-b-writesecurity-chown-acl-right-reclassification-narrow-repair

## Title

Phase 149O.20J.7: Class-B writesecurity/chown ACL-Right Reclassification Narrow Repair

## Status

done

## Mode

implementation

## Goal

Repair the known-safe-vocabulary gap in B-149O.20J.4-1 independently identified by 149O.20J.6: reclassify writesecurity and chown from _MACOS_ACL_KNOWN_SAFE_RIGHTS to write-capable in hatp_class_b_topology_verifier.py, with real-ACL evidence and a bounded audit of the remaining known-safe vocabulary

## Allowed Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- tests/test_phase_149o_20j_7_class_b_writesecurity_chown_acl_right_reclassification_narrow_repair.py
- tests/test_phase_149o_20j_6_class_b_acl_only_higher_ancestor_detection_repair_independent_verification.py
- docs/PHASE_149O_20J_7_CLASS_B_WRITESECURITY_CHOWN_ACL_RIGHT_RECLASSIFICATION_NARROW_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/*.md
- tasks/done/*.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- src/pcae/core/hatp_bootstrap.py
- src/pcae/core/repository_identity.py
- src/pcae/core/hatp_mandatory_certification.py
- src/pcae/core/hatp_mandatory_cutover.py
- scripts/hatp_certification_admin.py
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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-12T23:30:55.866230+02:00
