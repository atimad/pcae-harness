# Task Contract

## Task ID

20260717-1913-phase-136ab-stage-3-typed-authority-model-authority-core-implementation

## Title

Phase 136AB: Stage 3 Typed Authority Model Authority Core Implementation

## Status

done

## Mode

implementation

## Goal

Implement AuthorityEpoch and AuthorityState typed models (Typed Model Implementation Group 2) per the frozen 136Y plan, shared 136Z/136AA core, and the two executable schemas. Descriptive, immutable, schema-backed representations only -- no authority resolution, no runtime integration.

## Allowed Files

- src/pcae/cltr/authority/authority_core.py
- src/pcae/cltr/authority/__init__.py
- tests/test_cltr_authority_136ab_authority_core.py
- tests/test_cltr_authority_136z_shared_core.py
- tests/test_cltr_authority_136aa_shared_core_independent.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORITY_CORE_IMPLEMENTATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

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

- Exactly two record-family models implemented: AuthorityEpoch, AuthorityState (Group 2 only)
- Every field independently mapped from the executable schemas; no field copied solely from 136Y prose
- Record type / schema family constants strictly enforced; no alias, no case normalization
- Absent vs null preserved distinctly per field; ABSENT sentinel used exactly where the schema permits omission
- Enums strict (fail-closed); no coercion, no case-folding, no unknown-value acceptance
- Identifier and digest families preserved via distinct wrapper types; no cross-family substitution
- References (predecessor_epoch, active_authority_epoch, publication_evidence_reference) never resolved, dereferenced, or existence-checked
- CasExpectation not used by either model (neither schema embeds it); no CAS evaluation
- Both models frozen and recursively immutable; lossless round trip
- No later record-family models, no semantic validators, no repositories, no persistence, no authority resolver, no production runtime import
- No side effects (no filesystem/network/subprocess/env/digest-computation) during construction or serialization
- Schema-to-model conformance tests automated for both families
- Packaging: both models importable from wheel/sdist outside checkout
- Narrowing of 136Z/136AA scope guards (module-inventory/no-record-family-model/packaging tests) is bounded to authorizing exactly AuthorityEpoch/AuthorityState; every other later-group record-model name and module remains forbidden by those same guards

## Acceptance Checks

- python -m pytest tests/test_cltr_authority_136ab_authority_core.py -v
- python -m pytest tests/test_cltr_authority_136z_shared_core.py tests/test_cltr_authority_136aa_shared_core_independent.py -v
- python -m pytest -k cltr_cutover -n auto
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T19:13:28.614110+02:00
