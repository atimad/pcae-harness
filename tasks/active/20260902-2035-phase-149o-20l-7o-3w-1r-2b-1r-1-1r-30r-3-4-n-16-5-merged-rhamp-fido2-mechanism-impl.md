# Task Contract

## Task ID

20260902-2035-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-3-4-n-16-5-merged-rhamp-fido2-mechanism-impl

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4: N-16-5 merged RHAMP FIDO2 mechanism impl

## Status

active

## Mode

documentation

## Goal

Implement the merged RHAMP-REQ-156 .1R.30 bundle: RHAMP-FIDO2-CREDENTIAL/1.0 sidecar store, RHAMP-COUNTER-STATE/1.0 counter store, native CTAP2 makeCredential/getAssertion with deterministic CI seam, FIDO2HumanAuthenticator for hpac.fido2.uv_presence.v2, PAWA-authorized enrollment + first-credential bootstrap ceremony, hpac_verifier real-assertion branch + _ELIGIBLE_MECHANISM_IDS widening, 41-code terminal_reason_code mapping, standalone scripts/hpac_principal_admin.py, fresh test suite + >=55 negative matrix, guard reconciliation, fixed-SHA A/B, docs, governed finalization. RHAMP-001 v1.0 / HPAC-PAWA-001 v1.1 / HPAC-001 v2.1 byte-unchanged. No protected presentation, no require_real_assurance Gate 5/9 wiring, no N-16-6/7, no Slice C, no first external effect, runtime unchanged.

## Allowed Files

- src/pcae/**
- tests/**
- scripts/**
- docs/**
- PROJECT_STATUS.md
- CHANGELOG.md
- AGENTS.md
- pyproject.toml
- tasks/**
- .pcae/**

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-02T20:35:17.532792+02:00
