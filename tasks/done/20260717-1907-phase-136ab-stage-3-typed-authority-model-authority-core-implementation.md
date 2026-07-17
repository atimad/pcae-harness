# Task Contract

## Task ID

20260717-1907-phase-136ab-stage-3-typed-authority-model-authority-core-implementation

## Title

Phase 136AB: Stage 3 Typed Authority Model Authority Core Implementation

## Status

done

## Mode

implementation

## Goal

Implement AuthorityEpoch and AuthorityState typed models (Typed Model Implementation Group 2) per the frozen 136Y plan, shared 136Z/136AA core, and the two executable schemas. Descriptive, immutable, schema-backed representations only -- no authority resolution, no runtime integration.

## Allowed Files

- tests/test_cltr_authority_136z_shared_core.py
- tests/test_cltr_authority_136aa_shared_core_independent.py

## Forbidden Files

- src/pcae/cltr/authority/request_readiness.py
- src/pcae/cltr/authority/authorization_candidate.py
- src/pcae/cltr/authority/publication.py
- src/pcae/cltr/authority/recovery.py
- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/compatibility_quarantine.py
- src/pcae/cltr/models.py
- src/pcae/cltr/digest.py
- src/pcae/cltr/canonicalization.py
- src/pcae/cltr/enums.py
- src/pcae/schema_resources/**


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

- Narrowing of 136Z/136AA scope guards (module-inventory/no-record-family-model/packaging tests) is bounded to authorizing exactly AuthorityEpoch/AuthorityState; every other later-group record-model name and module remains forbidden by those same guards

## Acceptance Checks

- python -m pytest tests/test_cltr_authority_136ab_authority_core.py -v
- python -m pytest tests/test_cltr_authority_136z_shared_core.py tests/test_cltr_authority_136aa_shared_core_independent.py -v
- python -m pytest -k cltr_cutover -n auto
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T19:07:39.707617+02:00
