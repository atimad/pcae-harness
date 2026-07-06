# Task Contract

## Task ID

20260706-1318-115h-repository-skills-architecture

## Title

115H: Repository Skills Architecture

## Status

done

## Mode

implementation

## Goal

Design Repository Skills as the governed extension mechanism for PCAE decision support: skill definition, skill classes, deterministic skill examples, advisory/AI skill boundary, DeepSeek future pilot boundary, skill lifecycle, manifest concept, safety boundary, updated wire diagram. Architecture/design only, no implementation, no execution, no lifecycle changes.

## Allowed Files

- docs/PCAE_REPOSITORY_SKILLS_ARCHITECTURE.md
- docs/PHASE_115H_REPOSITORY_SKILLS_ARCHITECTURE.md
- tests/test_phase_115h_repository_skills_architecture.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1318-115h-repository-skills-architecture.md

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

- Repository Skills architecture defined; skills produce evidence only; deterministic and advisory skill classes defined; DeepSeek future pilot boundary documented; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115h_repository_skills_architecture.py tests/test_phase_115a_decision_explainability_framework.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T13:18:54.235234+02:00
