# Task Contract

## Task ID

20260805-0345-phase-149o-1-rae-trusted-provenance-root-hardening

## Title

Phase 149O.1: RAE Trusted Provenance Root Hardening

## Status

done

## Mode

validation

## Goal

Determine whether a trusted, independently-grounded provenance root exists
anywhere in current PCAE architecture that can distinguish legitimate RAE
Binding/Decision creation from arbitrary same-capability filesystem
reconstruction. Implement bounded hardening only if such a root is found;
otherwise stop and report the required trust-model architecture rather than
adding another forgeable sidecar.

## Allowed Files

- docs/PHASE_149O_1_RAE_TRUSTED_PROVENANCE_ROOT_HARDENING.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/permission_broker_foundation.py
- src/pcae/core/permission_broker.py
- src/pcae/core/agent.py
- src/pcae/commands/agent.py
- src/pcae/core/mutation_permission.py
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

- No AG3/AG5 Permission Broker integration.
- No rollback execution behavior change.
- No RAE-001/RWMPC-001/PBPC-001/PBPA-001/CHGR-001 contract amendment.

## Acceptance Criteria

- Four B-149O findings independently reproduced.
- Explicit threat model and trust-capability matrix documented.
- Existing trust/provenance mechanisms inventoried (CHGR, PublicationCoordinator,
  session identity, agent lock, Telegram, IWC) with independence assessed.
- Root selected (A/B/C/D) and justified; no implementation before selection.
- Root-provenance verdict recorded.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-05T03:45:00+00:00
