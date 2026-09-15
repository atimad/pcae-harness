# Task Contract

## Task ID

20260915-1736-n16-5-f-5-tb-helper-writer-authority-contract-iv-fresh-independent-verification-of-hpac-pawa-helper-001-v2-0-model-d-writer-authority-contract

## Title

N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV: fresh independent verification of HPAC-PAWA-HELPER-001 v2.0 Model D writer-authority contract

## Status

active

## Mode

verification

## Goal

Independently verify (not merely re-read) whether the frozen Model D writer-authority architecture is genuinely narrow and mechanically enforced, or remains a broad legacy-equivalent capability with descriptive-only scoping. No production implementation.

## Allowed Files

- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/4d8bff8474279f51d920426d99f70c51c9a0ef7f8e56c8d93cc55aff5ee8b4e0.json
- .pcae/fast-green-attribution/c13319dba939e1fdb7a8916581cbafa018fb139eea4ebff76ed741a6a53ed218.json
- docs/N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV_EVIDENCE.md
- docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV.md
- tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py
- tasks/done/20260915-1356-idle-post-n16-5-f-5-tb-helper-writer-authority-contract-arch-complete-n16-5-f-5-tb-helper-writer-authority-contract-iv-recommended-next-not-begun-n-16-5-not-closed.md
- tasks/active/20260915-1736-n16-5-f-5-tb-helper-writer-authority-contract-iv-fresh-independent-verification-of-hpac-pawa-helper-001-v2-0-model-d-writer-authority-contract.md
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/core/hpac_foundation.py
- src/pcae/core/hpac_protected_admin_writer.py
- src/pcae/core/hpac_pawa_schemas.py
- src/pcae/core/hpac_pawa_agent_exclusion.py
- src/pcae/core/hpac_pawa_helper_store_adapter.py


## Allowed Zones

- tasks
- docs
- tests
- config

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

- Independent CPIPC-derived phase ID validated (is_valid, same_series, same_branch, compare=less, equals=False, zero collisions)
- Model D reconstructed independently from contract text and source facts, not predecessor prose
- Explicit VERIFIED/NOT VERIFIED verdict issued per subsystem, and an overall verdict
- Zero production source (src/pcae/**) changes
- Fresh IV tests + predecessor 39-test regression + helper-boundary regression all run directly by the primary operator
- Governed fast-green-attribution run directly, 0 attributable regressions, against final pushed HEAD

## Acceptance Checks

- pytest tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py -q
- pytest tests/test_hpac_pawa_helper_writer_authority_contract_v2.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-15T17:36:56.449702+02:00
