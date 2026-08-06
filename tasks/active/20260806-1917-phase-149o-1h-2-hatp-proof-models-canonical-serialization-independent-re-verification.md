# Task Contract

## Task ID

20260806-1917-phase-149o-1h-2-hatp-proof-models-canonical-serialization-independent-re-verification

## Title

Phase 149O.1H.2: HATP Proof Models + Canonical Serialization Independent Re-Verification

## Status

active

## Mode

implementation

## Goal

Independently re-verify the 149O.1H.1 repair of B-149O.1H-1 and B-149O.1H-2 against src/pcae/core/human_approval_trusted_provenance.py; verification-only, no production source changes.

## Allowed Files

- tests/test_phase_149o_1h_2_hatp_proof_models_canonical_serialization_independent_reverification.py
- docs/PHASE_149O_1H_2_HATP_PROOF_MODELS_CANONICAL_SERIALIZATION_INDEPENDENT_REVERIFICATION.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/**
- docs/contracts/**


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

- B-149O.1H-1 and B-149O.1H-2 independently re-verified from scratch against current production source
- No production source under src/pcae/ modified

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_phase_149o_1h_2_hatp_proof_models_canonical_serialization_independent_reverification.py -q passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T19:17:42.567133+02:00
