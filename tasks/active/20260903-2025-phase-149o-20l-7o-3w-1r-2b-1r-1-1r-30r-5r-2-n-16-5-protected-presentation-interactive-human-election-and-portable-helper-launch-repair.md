# Task Contract

## Task ID

20260903-2025-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-n-16-5-protected-presentation-interactive-human-election-and-portable-helper-launch-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2 — N-16-5 Protected-Presentation Interactive Human Election and Portable Helper Launch Repair

## Status

active

## Mode

implementation

## Goal

Repair H-2's missing trusted local explicit APPROVE/REJECT election and F-2's
non-portable held-byte helper launch; precisely reconcile the carried
historical guards; preserve every frozen authority/runtime/effect boundary;
and leave N-16-5 NOT CLOSED pending fresh independent verification and final
presentation-bound certification.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/protected_presentation_helper.py
- src/pcae/core/protected_presentation.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_2_protected_presentation_real_assurance_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py
- tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py
- tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_multi_write_completion_integrity_repair.py
- tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N_16_5_PROTECTED_PRESENTATION_INTERACTIVE_HUMAN_ELECTION_AND_PORTABLE_HELPER_LAUNCH_REPAIR.md
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

advisory

## Forbidden Changes

- No normative contract modification
- No production change outside the protected-presentation helper and launcher
- No CTAP2, verifier, Gate 5, Gate 9, PAWA, PPA, PB, policy, runtime, adapter,
  plugin, N-16-6, N-16-7, or Slice C implementation
- No first runtime external effect or execution enablement
- No raw git commit/push, hook bypass, force push, or history rewrite
- No same-phase N-16-5 closure; fresh independent verification/certification is required

## Acceptance Criteria

- Production APPROVE originates only from one explicit human election on a
  trusted local terminal distinct from the protocol channel; explicit REJECT
  is preserved and no-TTY/EOF/invalid/interruption fail closed.
- The frozen canonical displayed bytes and request/response/evidence bindings
  remain exact and terminal-control spoofing remains neutralized.
- The intended pinned helper bytes execute portably on macOS/Python 3.9 while
  held-fd integrity/currentness, fixed interpreter/argv, no-shell/no-PATH, and
  no-generic-process-authority invariants remain intact.
- Carried historical point-in-time guards are reconciled precisely without
  removed/renamed/skipped/xfailed tests, wildcard/fnmatch broadening, or
  weakened process/effect checks.
- H-2 and F-2 are repaired, all attributable suites are green, runtime remains
  Observed/observe/unavailable with zero plugins/capabilities, and N-16-5
  remains NOT CLOSED pending a fresh successor IV/certification phase.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -q tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py passes
- relevant presentation/RHAMP/FIDO2/Gate suites pass without xdist
- pcae runtime inspect preserves not_implemented/Observed/observe/unavailable

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-03T20:25:27.696486+02:00
