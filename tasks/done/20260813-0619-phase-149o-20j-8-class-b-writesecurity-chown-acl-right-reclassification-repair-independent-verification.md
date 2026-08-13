# Task Contract

## Task ID

20260813-0619-phase-149o-20j-8-class-b-writesecurity-chown-acl-right-reclassification-repair-independent-verification

## Title

Phase 149O.20J.8: Class-B writesecurity/chown ACL-Right Reclassification Repair Independent Verification

## Status

done

## Mode

validation

## Goal

Independently verify J.7's writesecurity/chown ACL-right reclassification repair for B-149O.20J.4-1; verification-only, no production source modification

## Allowed Files

- tests/test_phase_149o_20j_8_class_b_writesecurity_chown_acl_right_reclassification_repair_independent_verification.py
- docs/PHASE_149O_20J_8_CLASS_B_WRITESECURITY_CHOWN_ACL_RIGHT_RECLASSIFICATION_REPAIR_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/*.md
- tasks/done/*.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
- docs/contracts/HATP_MANDATORY_INTEGRATION_CONTRACT.md


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

- Independently re-derive HBDC authority criterion and full macOS ACL right inventory from primary sources, not from production code
- Independently adjudicate writesecurity and chown via real ACL fixtures, not mocked results
- Independently audit all remaining known-safe rights and inheritance-modifier combinations for masking defects
- Establish a fixed pre-J.7 baseline via isolated worktree for Fast Green and broad-sweep comparison
- No production source modification

## Acceptance Checks

- fresh independent J.8 test module passes
- fast_green fixed-baseline exact node-ID delta established

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T06:19:30.042771+02:00
