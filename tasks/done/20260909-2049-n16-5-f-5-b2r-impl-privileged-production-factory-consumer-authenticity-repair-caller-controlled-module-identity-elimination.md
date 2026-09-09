# Task Contract

## Task ID

20260909-2049-n16-5-f-5-b2r-impl-privileged-production-factory-consumer-authenticity-repair-caller-controlled-module-identity-elimination

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R (N16-5-F-5-B2R-IMPL): Privileged Production Factory Consumer-Authenticity Repair -- Caller-Controlled Module-Identity Elimination

## Status

done

## Mode

implementation

## Goal

Repair the shared caller-controlled consumer-recognition primitive (_detect_caller_module) so it derives identity from real import-time provenance instead of forgeable frame.f_globals['__name__'], atomically across all four privileged factories; add regression coverage; verify clean-installed wheel boundary; leave HPAC-PAWA-001 v1.3 byte-unchanged.

## Allowed Files

- src/pcae/core/hpac_protected_admin_writer.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_n16_5_f5b1_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_impl.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b2.py
- tests/test_phase_n16_5_f5b2_impl_consumer_authenticity.py
- tests/test_phase_n16_5_f5b2_iv_adversarial.py
- tests/test_phase_n16_5_f5b2r_impl_repair.py
- PROJECT_STATUS.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_N16_5_F5B2R_IMPL.md
- tasks/done/20260909-1950-idle-awaiting-explicit-authorization-for-the-name-forgery-repair-phase-post-n16-5-f-5-b2-iv-n16-5-f-5-b2-not-verified-blocked-n-16-5-not-closed.md
- tasks/active/20260909-2049-n16-5-f-5-b2r-impl-privileged-production-factory-consumer-authenticity-repair-caller-controlled-module-identity-elimination.md
- tasks/done/20260909-2049-n16-5-f-5-b2r-impl-privileged-production-factory-consumer-authenticity-repair-caller-controlled-module-identity-elimination.md
- .pcae/phase-completion-metadata.json
- .pcae/session.json

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

- Four-factory atomicity: production_writer, certification_writer, recognized_certification_read_authority, mint_protected_presentation_evidence_writer all use the repaired recognition mechanism
- Caller-controlled __name__/exec()-globals forgery denied for all four factories (regression-locked)
- sys.modules poisoning and code-object-substitution attacks denied
- Legitimate consumers still succeed via genuine import provenance
- Clean-installed wheel boundary verified
- HPAC-PAWA-001 contract byte-unchanged
- No live production/HPAC/PPA/FIDO2 mutation; no real certification ceremony

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-09T20:49:38.848598+02:00
