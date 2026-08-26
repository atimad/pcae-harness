# Task Contract

## Task ID

20260826-1341-phase-149o-20l-7o-3m-1-independent-end-to-end-rollback-readiness-evidence-consumption-verification

## Title

Phase 149O.20L.7O.3M.1: Independent End-to-End Rollback Readiness / Evidence Consumption Verification

## Status

active

## Mode

verification

## Goal

Independently verify pre- and post-3M rollback evidence preparation, consumption, authority isolation, freshness, persistence, CLI visibility, and regression safety without trusting 3M evidence or modifying production source.

## Allowed Files

- docs/PHASE_149O_20L_7O_3M_1_INDEPENDENT_END_TO_END_ROLLBACK_READINESS_EVIDENCE_CONSUMPTION_VERIFICATION.md
- tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*

## Forbidden Files

- src/pcae/**

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- Independently establish whether real pre-3M rollback computed and consumed file_plan and divergence_check without prior dry-run
- Verify evidence visibility is non-authoritative and preserves Permission Broker, HATP, human-trigger, effect, and runtime semantics
- Adjudicate readiness-contract need and promotion-time persistence from current and pre-3M evidence
- Zero Blocking findings or stop and recommend the smallest repair phase

## Acceptance Checks

- pcae health
- pcae check
- pcae status coherence
- python -m pytest tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py -q
- python -c "import json; d=json.load(open('.pcae/fast-green-attribution/77695d008f999ff48649a98c165dec885372ff20fab1aea111cc4571a2117651.json')); assert d['candidate_commit']=='42207c243c5386ba51ad24628e41e1c5356cd8c1'; assert not d['attributable_failures']"
- python -c "import subprocess; s=subprocess.check_output(['pcae','runtime','inspect'], text=True); assert 'Runtime state:             Observed' in s; assert 'Execution capability:      unavailable' in s; assert 'Maximum plugin capability: observe' in s"
- python -c "import json; d=json.load(open('.pcae/phase-completion-metadata.json')); assert d['validation_results']['focused_rollback_regressions'].startswith('188 passed'); assert d['validation_results']['shared_regressions'].startswith('601 passed')"

The governed push and the final `origin/main..HEAD == 0` assertion occur after
task closure because push-readiness report identity requires this task to be
the latest completed phase task.

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-26T13:41:03.997780+02:00
