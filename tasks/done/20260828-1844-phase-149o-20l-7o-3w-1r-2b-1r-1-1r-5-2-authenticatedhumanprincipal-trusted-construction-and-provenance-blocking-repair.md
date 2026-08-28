# Task Contract

## Task ID

20260828-1844-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-5-2-authenticatedhumanprincipal-trusted-construction-and-provenance-blocking-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2: AuthenticatedHumanPrincipal Trusted-Construction and Provenance Blocking Repair

## Status

done

## Mode

implementation

## Goal

Repair F1 (BLOCKING) from .1R.5.1: AuthenticatedHumanPrincipal trusted-construction seal bypassable via object.__new__. Establish verifier-owned identity-registry provenance boundary that survives direct construction, object.__new__, subclassing, copy/deepcopy, manual state/slot copying, reflection, and pickle. No B1/B7/N1/N2 repair, no PB/runtime integration, no real FIDO2/UI.

## Allowed Files

- src/pcae/core/hpac_verifier.py
- tests/test_hpac_verifier*.py
- tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_2_*
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/runtime_authority.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/runtime_invocation_approval_store.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- src/pcae/core/hpac_foundation.py
- src/pcae/core/hpac_lifecycle.py


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

- F1 repaired: object.__new__/subclass/copy/deepcopy/state-copy/reflection cannot establish verifier-authenticated authority
- Zero production consumers of hpac_verifier.py preserved
- No PB/runtime-authority/Gate-9 integration

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T18:44:49.439163+02:00
