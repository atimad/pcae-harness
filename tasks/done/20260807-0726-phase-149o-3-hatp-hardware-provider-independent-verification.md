# Task Contract

## Task ID

20260807-0726-phase-149o-3-hatp-hardware-provider-independent-verification

## Title

Phase 149O.3: HATP Hardware Provider Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify (verification-only, no production code change) Phase 149O.2's HATP Wave-5 hardware-provider surface: reconstruct the Wave-5 production diff and requirement ownership from primary sources, adversarially attack FIDO2 protocol/payload binding, user-presence semantics, the new hardware credential registry's protected authority boundary, provider-factory containment, evidence-schema strictness, optional-dependency behavior, and the Wave-4 operational-readiness hard ceiling; classify every security property as proven-by-software-test / provider-semantic / requires-real-hardware; issue findings and a Wave-5 verdict without repairing anything.

## Allowed Files

- tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py
- docs/PHASE_149O_3_HATP_HARDWARE_PROVIDER_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260807-0726-phase-149o-3-hatp-hardware-provider-independent-verification.md
- tasks/done/20260807-0643-idle-awaiting-next-governed-phase-post-149o-2.md
- tasks/DONE.md

## Forbidden Files

- TBD


## Allowed Zones

- tests
- docs
- tasks
- config

## Forbidden Zones

- core
- package

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- Wave-5 production diff independently reconstructed from the 149O.1J baseline; UNRELATED hunks = 0
- Every Wave-5 security property classified A (proven by software test) / B (provider-semantic, not physically exercised) / C (requires real hardware, unverified)
- docs/PHASE_149O_3_HATP_HARDWARE_PROVIDER_INDEPENDENT_VERIFICATION.md records all required verdicts and findings
- No production file under src/pcae/ and no file under docs/contracts/ is modified by Phase 149O.3

## Acceptance Checks

- python -m pytest tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py -q
- python -m pytest tests/test_phase_149o_2_hatp_hardware_provider_implementation.py tests/test_hatp_verification_engine.py tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py -q
- git diff --name-only 89bebdc0..HEAD -- src/pcae/ docs/contracts/ must show no Phase 149O.3 change

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-07T07:26:53.992732+02:00
