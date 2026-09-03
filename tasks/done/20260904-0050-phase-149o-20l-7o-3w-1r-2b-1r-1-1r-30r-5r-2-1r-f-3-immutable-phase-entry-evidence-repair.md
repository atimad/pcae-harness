# Task Contract

## Task ID

20260904-0050-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-f-3-immutable-phase-entry-evidence-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R — F-3 Immutable Phase-Entry Evidence Repair

## Status

done

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

## Completion Evidence

- `A = E = 0250e5f7`, implementation `a85abff6`, `I = 361114d6`,
  `V = R0 = 57edf6a9`, all independently derived from Git topology.
- F-3 repaired with exact `a85abff6^ == 0250e5f7` immutable evidence; test
  name and sibling assertions retained.
- Predecessor suite 71/0; fresh repair suite 45/0; combined 116/0 from actual
  committed successor HEAD `c2ccf6d6`.
- Historical `.30R.5R.2.1` remains byte-unchanged and 85/0 at historical V;
  current 84/1 only at its preserved obsolete F-3 demonstration node.
- Presentation/non-regression sweep 552/0; historical guard sweep 428/0 after
  one unrelated transient concurrency node passed isolated and complete rerun.
- Production, scripts, dependencies, contracts, and H-1/H-2/F-2 source bytes
  unchanged; runtime/effect boundary unchanged; no hardware/real ceremony.
- F-3 REPAIRED; N-16-5 NOT CLOSED; successor `.30R.5R.2.1R.1` recommended,
  not begun.

## Created Timestamp

2026-09-04T00:50:40.360669+02:00
