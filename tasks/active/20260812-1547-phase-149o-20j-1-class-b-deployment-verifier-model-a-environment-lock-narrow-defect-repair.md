# Task Contract

## Task ID

20260812-1547-phase-149o-20j-1-class-b-deployment-verifier-model-a-environment-lock-narrow-defect-repair

## Title

Phase 149O.20J.1: Class-B Deployment Verifier / Model-A Environment-Lock Narrow Defect Repair

## Status

active

## Mode

implementation

## Goal

Repair exactly the 3 Blocking findings recorded by Phase 149O.20J (B-CBV-J-1 .pth tab-import bypass, B-CBV-J-2 getegid omission, B-CBV-J-3 trusted-Git ACL-blindness) in the two 149O.20I verifier modules, without HMIC scope evolution, Class-B provisioning, or readiness/certification/activation change

## Allowed Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- tests/test_phase_149o_20j_1_class_b_deployment_verifier_narrow_defect_repair.py
- docs/PHASE_149O_20J_1_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
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

- Exactly the 3 149O.20J Blocking findings repaired; no unrelated verifier redesign; verifier remains read-only, non-authoritative, and outside HMIC's frozen source scope

## Acceptance Checks

- pcae status coherence passes
- pcae health passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-12T15:47:39.244709+02:00
