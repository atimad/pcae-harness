# Task Contract

## Task ID

20260815-1338-phase-149o-20l-7d-7-class-b-verifier-narrow-source-repair-for-hbdc-req-022-030-035

## Title

Phase 149O.20L.7D.7: Class-B Verifier Narrow Source Repair for HBDC-REQ-022/030/035

## Status

done

## Mode

implementation

## Goal

Repair the shared distribution-metadata lookup defect (HBDC-REQ-022/035) and the overbroad symlink writability classification (HBDC-REQ-030 false positive) diagnosed by 149O.20L.7D.6, on the Mac dev repository only. No Dell mutation, no redeployment, no Action-9/CHGR/DeploymentBinding/certify/activate.

## Allowed Files

- src/pcae/core/hatp_class_b_conformance.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_topology_verifier.py
- tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py
- tests/test_phase_149o_20l_7d_7_class_b_verifier_narrow_source_repair.py
- docs/PHASE_149O_20L_7D_7_CLASS_B_VERIFIER_NARROW_SOURCE_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


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

2026-08-15T13:38:15.951354+02:00
