# Task Contract

## Task ID

20260806-0034-phase-149o-1f-1-hatp-production-trust-store-path-hardening

## Title

Phase 149O.1F.1: HATP Production Trust-Store Path Hardening

## Status

active

## Mode

implementation

## Goal

Repair Blocking finding B-149O.1F-1: HATPTrustStore.production() resolves via Path.home(), redirectable through the agent-controllable $HOME environment variable. Narrow repair of _default_production_trust_root() only.

## Allowed Files

- src/pcae/core/hatp_bootstrap.py
- tests/test_hatp_bootstrap_foundation.py
- tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py
- tests/test_phase_149o_1f_1_hatp_production_trust_store_path_hardening.py
- docs/PHASE_149O_1F_1_HATP_PRODUCTION_TRUST_STORE_PATH_HARDENING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- B-149O.1F-1 exploit reproduced pre-repair and shown blocked post-repair
- No src/pcae/** file other than hatp_bootstrap.py modified

## Acceptance Checks

- pcae check passes
- pcae health passes
- pcae status coherence passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T00:34:37.703238+02:00
