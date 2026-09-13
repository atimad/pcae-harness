# Task Contract

## Task ID

20260913-1725-n16-5-f-5-tb-real-helper-store-launcher-impl-canonical-store-wiring-linux-one-shot-launcher-2-of-5-ops-wired-3-blocked-by-req-033-writer-seal-exclusivity

## Title

N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL: canonical-store wiring + Linux one-shot launcher (2 of 5 ops wired; 3 blocked by REQ-033 writer-seal exclusivity)

## Status

done

## Mode

implementation

## Goal

Wire HPAC-PAWA-HELPER/1.0's certification_read/ceremony_entry to real canonical stores, implement the Linux one-shot launcher + entrypoint, run the required adversarial matrix; report the REQ-033 writer-capability blocker for admin_mutation/certification_write/presentation_evidence_write honestly rather than routing around it.

## Allowed Files

- src/pcae/core/hpac_pawa_helper_operations.py
- src/pcae/core/hpac_pawa_helper_entrypoint.py
- src/pcae/core/hpac_pawa_helper_launcher.py
- src/pcae/core/hpac_pawa_helper_store_adapter.py
- tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py
- tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py
- tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py
- tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py
- tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- docs/PHASE_N16_5_F_5_TB_REAL_HELPER_STORE_LAUNCHER_IMPL.md
- tasks/active/20260913-1725-n16-5-f-5-tb-real-helper-store-launcher-impl-canonical-store-wiring-linux-one-shot-launcher-2-of-5-ops-wired-3-blocked-by-req-033-writer-seal-exclusivity.md
- tasks/done/20260913-1532-idle-post-n16-5-f-5-tb-admin-mutation-packaging-decision-complete-helper-store-wiring-linux-first-launcher-next-not-begun-n-16-5-not-closed.md
- .pcae/fast-green-attribution/ed28bd8c5f89e82b802e60559b30b75bc339da7dfa5ea11762863b438dfbec7d.json
- .pcae/fast-green-attribution/00dd8566502c030691d62a2ac401b69738b416396ddcd52d1a2c0ccd2f090e33.json

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

2026-09-13T17:25:09.429041+02:00
