# Task Contract

## Task ID

20260807-0611-phase-149o-2-hatp-hardware-provider-human-presence-implementation-wave-5

## Title

Phase 149O.2: HATP Hardware Provider + Human-Presence Implementation (Wave 5)

## Status

active

## Mode

implementation

## Goal

Implement a real HATP_HARDWARE_PROVIDER_V1-conformant hardware provider layer (FIDO2 primary, PIV documented fallback) implementing the existing Wave-4 HATPProofVerifierProvider interface, without deriving approval_present, wiring RAE/PB/agent, or flipping HATP operational readiness.

## Allowed Files

- src/pcae/core/hatp_providers.py
- src/pcae/core/hatp_fido2_provider.py
- src/pcae/core/hatp_piv_provider.py
- src/pcae/core/hatp_hardware_credentials.py
- pyproject.toml
- tests/conftest.py
- tests/test_phase_149o_2_hatp_hardware_provider_implementation.py
- tests/test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py
- tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py
- docs/PHASE_149O_2_HATP_HARDWARE_PROVIDER_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260807-0611-phase-149o-2-hatp-hardware-provider-human-presence-implementation-wave-5.md
- tasks/done/20260807-0544-idle-awaiting-next-governed-phase-post-149o-1j.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml

## Allowed Zones

- core
- tests
- docs
- package
- tasks
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-07T06:11:39.452836+02:00
