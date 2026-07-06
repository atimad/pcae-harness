# Task Contract

## Task ID

20260706-1909-115p-advisory-repository-skills-architecture

## Title

115P: Advisory Repository Skills Architecture

## Status

active

## Mode

implementation

## Goal

Design Advisory Repository Skills as model-backed, evidence-only Repository Skills: freeze the advisory pipeline (Prompt Builder -> Current Model -> Raw Response -> Normalizer -> Evidence Builder -> EvidenceCollection), the model boundary, default same-model mode, future split-model mode (documented only), safety rules, failure behavior, and first pilot scope. Architecture/design only -- no Advisory Repository Skill, model call, or backend integration implemented.

## Allowed Files

- docs/PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md
- docs/PHASE_115P_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md
- tests/test_phase_115p_advisory_repository_skills_architecture.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1909-115p-advisory-repository-skills-architecture.md

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

- Advisory Repository Skills architecture defined; same-model advisory default documented; split-model config deferred; model output normalization boundary defined; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115p_advisory_repository_skills_architecture.py tests/test_phase_115h_repository_skills_architecture.py tests/test_phase_115i_repository_skills_contract_freeze.py tests/test_phase_115l_repository_skills_integration_design.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T19:09:42.372961+02:00
