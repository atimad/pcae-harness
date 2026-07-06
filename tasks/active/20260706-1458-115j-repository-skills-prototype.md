# Task Contract

## Task ID

20260706-1458-115j-repository-skills-prototype

## Title

115J: Repository Skills Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first Repository Skills framework prototype using only deterministic skills that wrap existing 115D Evidence Providers: RepositorySkill, RepositorySkillContext, RepositorySkillResult, RepositorySkillRegistry, RepositorySkillCapability, RepositorySkillManifest, plus GitRepositorySkill/RuntimeRepositorySkill/ReportRepositorySkill/MetadataRepositorySkill. No AI/SLM/LLM skills, no DeepSeek integration, no lifecycle integration, no Decision Evaluation integration, no Repository Transition Validator integration, no execution capability.

## Allowed Files

- src/pcae/core/repository_skills.py
- tests/test_repository_skills.py
- tests/test_phase_115h_repository_skills_architecture.py
- tests/test_phase_115i_repository_skills_contract_freeze.py
- docs/PHASE_115J_REPOSITORY_SKILLS_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1458-115j-repository-skills-prototype.md

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

- Repository Skills framework implemented; deterministic skills implemented; skills wrap Evidence Providers only; registry implemented; no AI skills; no lifecycle integration; no decision authority; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_repository_skills.py tests/test_evidence.py tests/test_evidence_collection.py tests/test_evidence_providers.py tests/test_evidence_serialization.py tests/test_evidence_validation.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T14:58:56.450790+02:00
