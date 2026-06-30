# Phase 95F.2 — Phase Report Authoring Skill and Completeness Enforcement
```
phase_name = phase_95f2_phase_report_authoring_skill_and_completeness_enforcement
phase_status = completed | implementation_status = completed
recommended_next_phase = 95G — Runtime Evidence Broker/Shell-Gate Integration
```

## 1. Purpose
Added `.pcae/skills/phase-finalization/SKILL.md` (7th skill). Strengthened `assess_completeness()` with key-level validation: 5 required governance keys, 3 required base test keys. Reports now partial if any key missing.

## 2. Skill
`.pcae/skills/phase-finalization/SKILL.md` — workflow type. Mandatory protocol: 15 trust fields, 5 governance keys, 3 base test keys + backend-specific. Skill-only insufficient; CLI enforcement is source of truth.

## 3. Completeness Enforcement
`_REQUIRED_GOVERNANCE_KEYS`: pcae_health, pcae_check, pcae_doctor_task_memory, pcae_push_check, telegram_runtime.
`_REQUIRED_BASE_TEST_RESULT_KEYS`: report_notification_tests, bootstrap_session_reporting_tests, fast_green.
Missing keys → dotted paths in `missing_trust_fields` → partial.

## 4. Files (5)
.pcae/skills/phase-finalization/SKILL.md, src/pcae/core/phase_reports.py, tests/test_phase_reports.py, docs, PROJECT_STATUS/CHANGELOG/tasks

## 5. Tests (11 new + 87 updated pre-existing, 98 total)
Test95F2CompletenessEnforcement: full complete, 6 missing-keys-are-partial, dotted paths, empty gov lists all, empty test lists all, skill file exists.
