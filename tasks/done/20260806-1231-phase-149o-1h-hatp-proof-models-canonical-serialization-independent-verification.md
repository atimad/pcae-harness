# Task Contract

## Task ID

20260806-1231-phase-149o-1h-hatp-proof-models-canonical-serialization-independent-verification

## Title

Phase 149O.1H: HATP Proof Models + Canonical Serialization Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify Wave-3 HATP proof models and canonical serialization; report BLOCKING/NON-BLOCKING findings without repairing them

## Allowed Files

- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_149O_1H_HATP_PROOF_MODELS_CANONICAL_SERIALIZATION_INDEPENDENT_VERIFICATION.md
- tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/*.md
- tasks/done/*.md

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

- Wave-3 production diff independently reconstructed and classified
- HATP-001 requirement span independently re-derived, not accepted from report
- Adversarial attack matrix executed: closed-schema, duplicate-key, version, timestamp, Unicode, construction, immutability
- Independent golden vectors computed without reusing implementation's own canonicalizer
- New independent test file created and passing
- All required regression suites run with actual results reported
- Zero production code and zero contract text modified

## Acceptance Checks

- python -m pytest tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py -q
- python -m pytest tests/test_hatp_proof_models.py tests/test_hatp_canonical_serialization.py tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T12:31:09.490661+02:00
