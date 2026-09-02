# Task Contract

## Task ID

20260902-2237-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-3-6-n-16-5-pawa-multi-write-completion-one-operation-integrity-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6: N-16-5 PAWA Multi-Write Completion One-Operation Integrity Repair

## Status

active

## Mode

implementation

## Goal

Repair only `HPACStoreAuthority.complete_multi_write` so canonical
process-local issuance lifecycle ACTIVE -> CONSUMED is atomic and permits at
most one successful completion, while preserving the historical `.30R.3.5`
BLOCKED verdict and every already-verified RHAMP/FIDO2/runtime boundary.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_6_N_16_5_PAWA_MULTI_WRITE_COMPLETION_ONE_OPERATION_INTEGRITY_REPAIR.md
- src/pcae/core/hpac_foundation.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_multi_write_completion_integrity_repair.py

## Forbidden Files

- docs/contracts/**
- src/pcae/core/hpac_protected_admin_writer.py
- src/pcae/core/hpac_rhamp_enrollment.py
- src/pcae/core/human_principal_registry.py
- src/pcae/core/human_authenticator_fido2.py
- src/pcae/core/hpac_verifier.py
- src/pcae/core/runtime_dispatch_gate5.py
- src/pcae/core/runtime_dispatch_gate9.py
- src/pcae/core/approval_presentation.py
- src/pcae/core/approval_presentation_deterministic.py


## Allowed Zones


## Forbidden Zones


## Allowed Dependencies


## Forbidden Dependencies


## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside the narrow `complete_multi_write`
  lifecycle repair
- No execution authorization
- No rollback
- No raw git commit/push, hook bypass, force push, or history rewrite;
  governed PCAE commit/push lifecycle only
- No new `HPACWriterCapability` field or issuance-registry structure
- No new PAWA or RHAMP failure code

## Acceptance Criteria

- Historical `.30R.3.4` defect independently reproduced before editing
- Exactly one concurrent completion succeeds for a canonical ACTIVE issuance
- Second/re-entrant completion fails with existing `capability_stale`
- Canonical registry state dominates mutable object-local `_spent`
- Invalid/non-issued/wrong-scope calls fail without corrupting valid authority
- Ordinary one-write and bounded multi-write component behavior is unchanged
- Historical `.30R.3.5` blocking nodes pass unchanged on the repaired tree
- RHAMP enrollment and affected PAWA/FIDO2 suites have no unexplained repair-only regression
- Contracts and forbidden production surfaces remain byte-identical to R0
- Runtime remains Observed/observe/unavailable; first external effect absent
- N-16-5 remains NOT CLOSED and a fresh successor IV is derived

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes
- Dedicated `.30R.3.6`, `.30R.3.5`, `.30R.3.4`, and PAWA integrity suites pass
- Fixed-SHA A/R affected-scope attribution has zero unexplained R-only failures
- No-test-weakening audit passes
- origin/main..HEAD = 0 after governed push and phase completion succeeds

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-02T22:37:12.663640+02:00
