# Task Contract

## Task ID

20260706-2007-115r-advisory-repository-skills-prototype

## Title

115R: Advisory Repository Skills Prototype

## Status

done

## Mode

implementation

## Goal

Implement the complete Advisory Repository Skills framework (AdvisoryRequest, RawAdvisoryResponse, NormalizedAdvisoryResponse, AdvisoryProvider interface, MockAdvisoryProvider, Prompt Builder, Response Normalizer, Evidence Builder, and the first Advisory Repository Skill) using a deterministic Mock Advisory Provider only. No real model invoked, no network, no execution. No Decision Evaluation/Validator/lifecycle changes.

## Allowed Files

- src/pcae/core/advisory_repository_skills.py
- tests/test_advisory_repository_skills_prototype_115r.py
- docs/PCAE_ADVISORY_REPOSITORY_SKILLS_PROTOTYPE.md
- docs/PHASE_115R_ADVISORY_REPOSITORY_SKILLS_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2007-115r-advisory-repository-skills-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- docs
- tests
- tasks

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

- Advisory framework implemented; Mock Advisory Provider implemented; AdvisoryRequest/Prompt Builder/Response Normalizer/Evidence Builder implemented; end-to-end advisory pipeline proven; deterministic failures handled; no real model invoked; no network access; no execution capability

## Acceptance Checks

- python -m pytest tests/test_advisory_repository_skills_prototype_115r.py tests/test_phase_115q_advisory_repository_skills_contract_freeze.py tests/test_repository_skills.py tests/test_repository_skills_integration_115m.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T20:07:34.303469+02:00
