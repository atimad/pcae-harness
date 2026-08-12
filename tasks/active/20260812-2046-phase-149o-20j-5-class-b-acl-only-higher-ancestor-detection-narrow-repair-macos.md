# Task Contract

## Task ID

20260812-2046-phase-149o-20j-5-class-b-acl-only-higher-ancestor-detection-narrow-repair-macos

## Title

Phase 149O.20J.5: Class-B ACL-Only Higher-Ancestor Detection Narrow Repair (macOS)

## Status

active

## Mode

implementation

## Goal

Repair B-149O.20J.4-1: _acl_grants_agent_write_macos fails to recognize real macOS canonical directory-replacement ACL rights (add_file/add_subdirectory/delete_child/delete), causing _ancestor_chain_safe to incorrectly classify an ACL-writable higher ancestor as safe

## Allowed Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- tests/test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_detection_macos_narrow_repair.py
- tests/test_phase_149o_20j_4_class_b_full_ancestor_chain_verification_repair_independent_verification.py
- docs/PHASE_149O_20J_5_CLASS_B_ACL_ONLY_HIGHER_ANCESTOR_DETECTION_NARROW_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260812-1827-idle-awaiting-next-governed-phase-post-149o-20j-3.md
- tasks/done/20260812-1827-idle-awaiting-next-governed-phase-post-149o-20j-3.md
- tasks/active/20260812-2046-phase-149o-20j-5-class-b-acl-only-higher-ancestor-detection-narrow-repair-macos.md
- tasks/done/20260812-2046-phase-149o-20j-5-class-b-acl-only-higher-ancestor-detection-narrow-repair-macos.md
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

2026-08-12T20:46:19.932249+02:00
