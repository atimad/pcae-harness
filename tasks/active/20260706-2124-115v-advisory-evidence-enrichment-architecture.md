# Task Contract

## Task ID

20260706-2124-115v-advisory-evidence-enrichment-architecture

## Title

115V: Advisory Evidence Enrichment Architecture

## Status

active

## Mode

implementation

## Goal

Design how PCAE improves advisory quality by enriching the deterministic evidence supplied to Advisory Repository Skills: enrichment definition, eleven evidence categories, priority matrix, the future Advisory Context Package, safety boundaries, prompt-injection handling, evidence summarization rules, and a phased future roadmap (115W-115Z). Architecture/design only -- no new evidence provider, Repository Skill, or Advisory Provider runtime change implemented.

## Allowed Files

- docs/PCAE_ADVISORY_EVIDENCE_ENRICHMENT.md
- docs/PHASE_115V_ADVISORY_EVIDENCE_ENRICHMENT_ARCHITECTURE.md
- tests/test_phase_115v_advisory_evidence_enrichment_architecture.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2124-115v-advisory-evidence-enrichment-architecture.md

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

- Advisory Evidence Enrichment architecture defined; evidence quality strategy documented; advisory context package designed; prompt-injection boundary documented; evidence summarization rules documented; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115v_advisory_evidence_enrichment_architecture.py tests/test_phase_115u_advisory_provider_strategy_review.py tests/test_phase_115h_repository_skills_architecture.py tests/test_phase_115q_advisory_repository_skills_contract_freeze.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T21:24:40.813559+02:00
