# Task Contract

## Task ID

20260706-1925-115q-advisory-repository-skills-contract-freeze

## Title

115Q: Advisory Repository Skills Contract Freeze

## Status

active

## Mode

implementation

## Goal

Freeze the backend-agnostic contract for Advisory Repository Skills before any implementation: the AdvisoryRepositorySkill interface, the AdvisoryProvider/AdvisoryRequest/RawAdvisoryResponse/NormalizedAdvisoryResponse abstraction, default same-model mode, deferred split-model mode, prompt/response/evidence boundaries, failure contract, safety rules, and a narrow first pilot scope. Contract/design only -- no Advisory Repository Skill, Advisory Provider, or model call implemented.

## Allowed Files

- docs/PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md
- docs/PHASE_115Q_ADVISORY_REPOSITORY_SKILLS_CONTRACT_FREEZE.md
- tests/test_phase_115q_advisory_repository_skills_contract_freeze.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1925-115q-advisory-repository-skills-contract-freeze.md

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

- Advisory Repository Skills contract frozen; Advisory Provider abstraction frozen; prompt/response/evidence boundaries frozen; same-model default documented; split-model future mode deferred; first pilot scope frozen; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115q_advisory_repository_skills_contract_freeze.py tests/test_phase_115h_repository_skills_architecture.py tests/test_phase_115i_repository_skills_contract_freeze.py tests/test_phase_115p_advisory_repository_skills_architecture.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T19:25:28.169698+02:00
