# Task Contract

## Task ID

20260812-0704-phase-149o-20g-hmic-v1-2-hbdc-25-file-5-contract-production-identity-alignment-independent-verification

## Title

Phase 149O.20G: HMIC v1.2 HBDC 25-File / 5-Contract Production Identity Alignment Independent Verification

## Status

active

## Mode

read_mostly

## Goal

Independently verify production exactly implements HMIC v1.2 verified 25/5 HBDC identity model; adjudicate B-149O.20D-1 and HBDC-BINDING-GATE at implementation-verification boundary; zero src/pcae or scripts modification

## Allowed Files

- tests/test_phase_149o_20g_hmic_v1_2_hbdc_25_file_5_contract_production_identity_alignment_independent_verification.py
- docs/PHASE_149O_20G_HMIC_V1_2_HBDC_25_FILE_5_CONTRACT_PRODUCTION_IDENTITY_ALIGNMENT_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/done/20260812-0525-idle-awaiting-next-governed-phase-post-149o-20f.md
- tasks/active/20260812-0704-phase-149o-20g-hmic-v1-2-hbdc-25-file-5-contract-production-identity-alignment-independent-verification.md

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- core
- commands
- cltr
- cli
- schema_runtime
- governance
- interactive_workflow
- authority_evaluation
- aesic
- scripts

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Independent dual-equality (25/25 files, 5/5 contract members) verified from primary sources
- HBDC dual binding (content + version/ID) independently reimplemented and confirmed
- Zero src/pcae/** or scripts/** modification

## Acceptance Checks

- pytest tests/test_phase_149o_20g_hmic_v1_2_hbdc_25_file_5_contract_production_identity_alignment_independent_verification.py

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-12T07:04:04.055563+02:00
