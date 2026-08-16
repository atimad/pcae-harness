# Task Contract

## Task ID

20260816-2305-phase-149o-20l-7l-3-attack-matrix-rows-33-34-36-37-and-ast-guard-multiline-import-narrow-repair

## Title

Phase 149O.20L.7L.3: Attack-Matrix Rows 33/34/36/37 and AST-Guard Multiline-Import Narrow Repair

## Status

done

## Mode

documentation

## Goal

Repair F-7L-5 (attack-matrix rows 33/34/36/37 stale current-state claims) and F-7L-7 (AST-guard from-package-import-submodule blind spot), same-version, contract-text-and-test-only, per 149O.20L.7L.2's recommended next phase

## Allowed Files

- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py
- tests/test_phase_149o_20l_7l_2_hmic_consumer_status_and_dependency_header_repair_independent_verification.py
- tests/test_phase_149o_20l_7l_3_attack_matrix_and_ast_guard_narrow_repair.py
- tests/test_phase_149o_19_5e_1_hmic_v1_1_validator_admin_identity_contract_evolution.py
- tests/test_phase_149o_20d_hmic_v1_2_hbdc_bound_contract_identity_evolution.py
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

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-16T23:05:56.687053+02:00
