# Task Contract

## Task ID

20260904-0050-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-f-3-immutable-phase-entry-evidence-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R — F-3 Immutable Phase-Entry Evidence Repair

## Status

active

## Mode

implementation

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R — F-3 Immutable Phase-Entry Evidence Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_f3_immutable_phase_entry_evidence_repair.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_F3_IMMUTABLE_PHASE_ENTRY_EVIDENCE_REPAIR.md
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

- No production, script, dependency, or normative-contract change
- No modification to the `.30R.5R.2.1` IV suite or historical reports
- No test removal, rename-to-evade, skip, xfail, wildcard, or fnmatch broadening
- No real protected-presentation or FIDO2 ceremony
- No N-16-5 closure, N-16-6/N-16-7 work, runtime capability, or first effect
- Governed commit/push only; no raw commit/push or hook bypass

## Acceptance Criteria

- F-3 historical/live-HEAD conflation is repaired using immutable Git topology.
- The complete `.30R.5R.2` and unchanged `.30R.5R.2.1` suites pass.
- Production, contracts, dependencies, H-1/H-2/F-2 bytes, runtime, and effect
  boundaries remain unchanged.
- N-16-5 remains NOT CLOSED and the fresh IV/certification successor is
  recommended but not begun.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T00:50:40.360669+02:00
