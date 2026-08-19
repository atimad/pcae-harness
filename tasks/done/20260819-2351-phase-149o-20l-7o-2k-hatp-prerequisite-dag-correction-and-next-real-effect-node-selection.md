# Task Contract

## Task ID

20260819-2351-phase-149o-20l-7o-2k-hatp-prerequisite-dag-correction-and-next-real-effect-node-selection

## Title

Phase 149O.20L.7O.2K: HATP Prerequisite DAG Correction and Next Real-Effect Node Selection

## Status

done

## Mode

analysis

## Goal

Correct 149O.20L.7O.2I's stale prerequisite DAG per 149O.20L.7O.2J primary evidence, independently select exactly one next real-effect node (HMIC certification vs FIDO2 hardware-credential enrollment), and freeze a narrow authorization envelope for it. Analysis/authorization only; no real-effect action performed.

## Allowed Files

- docs/PHASE_149O_20L_7O_2K_HATP_PREREQUISITE_DAG_CORRECTION_AND_NEXT_REAL_EFFECT_NODE_SELECTION.md
- tests/test_phase_149o_20l_7o_2k_hatp_prerequisite_dag_correction_and_next_real_effect_node_selection.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
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

- Corrected DAG document produced citing 2J primary evidence
- Exactly one next real-effect node selected (or verdict C/D if neither ready), no real-effect action performed
- Focused phase-local tests pass; fast_green shows zero attributable regressions

## Acceptance Checks

- pytest tests/test_phase_149o_20l_7o_2k_hatp_prerequisite_dag_correction_and_next_real_effect_node_selection.py

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T23:51:34.907582+02:00
