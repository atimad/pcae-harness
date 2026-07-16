# Task Contract

## Task ID

20260716-1444-phase-136i-companion-executable-schema-shared-core-independent-verification

## Title

Phase 136I: Companion Executable Schema Shared Core Independent Verification

## Status

done

## Mode

implementation

## Goal

Independently verify and adversarially attack the Stage 3 Companion Executable Schema shared core implemented by 136H: re-derive the exact inventory, attack identifiers/digests/timestamps/enums/reason-codes/references/limitations, mutate manifest/schema copies to prove fail-closed tamper detection, attack the Mapping-contract repair with a second hostile Mapping, independently build and verify wheel/sdist packaging, and re-verify no-network/no-authority/no-execution boundaries. No authority-bearing record schema, typed model, semantic validator, or authority resolver/state/pointer.

## Allowed Files

- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- src/pcae/schema_resources/**
- src/pcae/schema_runtime/**
- docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/cltr/**
- schemas/**
- .pcae/cltr-authority/**


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

- TBD

## Acceptance Criteria

- Independent inventory re-derivation confirms 7 shared files, 33 defs, 8 enums, 24 reason codes, 7 manifest entries exactly
- No authority-bearing record schema, typed model, semantic validator, or authority resolver/state/pointer created
- Fresh wheel/sdist build verified with installed-wheel operation proven outside the repository
- Combined schema-runtime + 136H + 136I suite and Fast Green pass with zero regressions

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -m fast_green -n auto passes
- python -m pytest tests/test_schema_runtime_*.py tests/test_cltr_cutover_*.py -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T14:44:52.477061+02:00
