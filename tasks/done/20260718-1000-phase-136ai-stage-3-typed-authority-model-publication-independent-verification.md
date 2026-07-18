# Task Contract

## Task ID

20260718-1000-phase-136ai-stage-3-typed-authority-model-publication-independent-verification

## Title

Phase 136AI: Stage 3 Typed Authority Model Publication Independent Verification

## Status

done

## Mode

implementation

## Goal

Independently re-derive and verify PublicationAttempt and PublicationEvidence typed record models from Phase 136AH against frozen contracts and live executable schemas; bounded repair of independently reproduced Blocking defects only.

## Allowed Files

- tests/test_cltr_authority_136ai_publication_independent.py
- src/pcae/cltr/authority/publication.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_PUBLICATION_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-metadata-repairs.log
- .pcae/phase-reports/**

## Forbidden Files

- src/pcae/cltr/authority/recovery.py
- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/compatibility_quarantine.py


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

- Both publication record contracts independently re-derived from frozen contracts and live schemas, not from 136AH tests/fixtures/prose
- No later record-family model introduced; no publication execution, CAS execution, evidence verification, provider access, or reference resolution introduced
- No unresolved Blocking finding remains

## Acceptance Checks

- New independent test module passes
- 136AH/136AG/136AF/136AE/136AD/136AC/136AB/136AA/136Z focused suites pass with no new failures
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-18T10:00:01.909210+02:00
