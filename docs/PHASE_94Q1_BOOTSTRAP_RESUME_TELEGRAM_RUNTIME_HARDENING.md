# Phase 94Q.1 — Bootstrap Resume and Telegram Runtime Hardening

```
phase_name    = phase_94q1_bootstrap_resume_telegram_runtime_hardening
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94R — Backend Real Adapter Design
```

## 1. Purpose

Harden PCAE session bootstrap/resume behavior so it does not incorrectly report readiness when active task state, latest phase state, handoff state, transition state, pcae health/check, or Telegram runtime readiness are stale or inconsistent.

## 2. Observed Problem

From the 94Q Telegram report, several stale-state issues were visible:

- `pcae_health`: unhealthy — active task 94P, pending transition to 94Q
- `pcae_check`: failed — task scope mismatch before transition
- Earlier bootstrap resumed stale active task 94P even though 94P was completed
- Earlier bootstrap displayed old handoff from 94L
- Telegram runtime env had to be manually loaded after terminal restart
- Push mode showed "not ready (nothing_to_push)" — contradictory wording

This confirmed bootstrap/resume readiness was too permissive and stale-state detection was insufficient.

## 3. Non-Goals

This phase is bootstrap/session/reporting/runtime hardening only. It does NOT:
- Implement 94R (Backend Real Adapter Design)
- Change backend lifecycle demo functionality
- Implement real backend invocation, apply execution, patch parsing, file mutation
- Implement subprocess, network, shell interception, Telegram inbound
- Implement enforcement, autonomous mutation, automatic apply

## 4. Readiness Classification

New multi-factor readiness classification replaces the single-factor `ready = check_passed`:

| Status | Meaning |
|--------|---------|
| `ready` | All factors aligned: health healthy, check passed, no stale state, report complete, push clean, Telegram loaded |
| `ready_with_warnings` | Non-blocking issues present: stale handoff, task memory warnings, Telegram not loaded, unpushed commits |
| `needs_attention` | Reserved for future use |
| `blocked` | Hard blocks: unhealthy, check failed, stale active task, partial/incomplete report |

## 5. Factors Evaluated

| Factor | Blocking? | Check |
|--------|-----------|-------|
| pcae health | Yes (if unhealthy) | `build_health_data()` |
| pcae check | Yes (if failed) | `run_checks()` |
| Stale active task | Yes (if phase is completed) | Compares active task with latest phase report |
| Partial report | Yes | `report_completeness == "partial"` |
| Incomplete report | Yes | `report_completeness == "incomplete"` |
| Stale handoff | No (warning) | Handoff `created_at` < report `completed_at` |
| Unpushed commits | No (warning) | `origin/main..HEAD > 0` |
| Task memory warnings | No (warning) | Active task files > 1 |
| Telegram not loaded | No (warning) | `PCAE_TELEGRAM_BOT_TOKEN` env missing |
| Mismatched active task | No (warning) | Active task phase ≠ recommended next |

## 6. Push Wording Fix

Before: `Push: not ready (nothing_to_push)` — contradictory ("not ready" + "nothing to push")

After: `Push: clean (nothing_to_push)` — clear and accurate

Distinguishes:
- `clean (nothing_to_push)` — 0 unpushed commits
- `needs_push (N unpushed)` — commits ahead of origin/main
- `ready` — active task, can push

## 7. Telegram Runtime Handling

Bootstrap now checks Telegram runtime env vars without printing secrets:

- Detects whether `PCAE_TELEGRAM_BOT_TOKEN` + `PCAE_TELEGRAM_CHAT_ID` are set
- Reports status: `loaded` or `not_loaded`
- When not loaded, shows explicit action: `source ~/.config/pcae/telegram.env && pcae notify status`
- Never prints token, chat ID, or any secret values

## 8. Bootstrap Output Changes

New bootstrap text output includes:

```
Latest completed phase: 94Q (completed, report: complete)
Recommended next phase: 94Q.1 — Bootstrap Resume and Telegram Runtime Hardening
Readiness: ready_with_warnings / blocked
  - <issue line>
Push: clean (nothing_to_push)
Telegram runtime: loaded / not_loaded (action: ...)
```

New JSON fields: `readiness`, `readiness_issues`, `latest_phase_report`, `push_check`, `telegram_runtime`, `task_memory_warnings`, `active_task_count`

## 9. Files Changed

- `src/pcae/commands/session.py` — Added `_read_latest_phase_report()`, `_load_push_check()`, `_count_active_tasks()`, `_check_telegram_runtime()`, `_extract_phase_number()`, `_phase_is_completed()`, `_classify_bootstrap_readiness()`, `_format_push_status()`. Modified `run_session_bootstrap()` to use multi-factor readiness.
- `tests/test_session.py` — Added 30 tests (5 classes: Test94Q1ReadinessClassification, Test94Q1TelegramRuntime, Test94Q1Helpers, Test94Q1BootstrapOutput). Updated 6 pre-existing tests for new output format.

## 10. Test Coverage

**30 new tests:**

- `Test94Q1ReadinessClassification` (11 tests): healthy ready, unhealthy blocks, check failed blocks, stale active task blocks, partial report blocks, incomplete report blocks, stale handoff warning, TG not loaded warning, task memory warning, unpushed warning, multiple issues
- `Test94Q1TelegramRuntime` (4 tests): no env → not_loaded, token present → loaded, token but disabled, no secrets in result
- `Test94Q1Helpers` (9 tests): extract_phase_number, phase_is_completed variants, format_push_status variants
- `Test94Q1BootstrapOutput` (6 tests): JSON includes new fields, no secrets in TG runtime, no shell execution, no Telegram inbound, no network, multi-part phase ID

## 11. No-Go Confirmations

| Item | Status |
|------|--------|
| Real backend invocation | NOT implemented ✅ |
| Apply execution | NOT implemented ✅ |
| Patch parsing for mutation | NOT implemented ✅ |
| Source file mutation | NOT implemented ✅ |
| Subprocess execution (beyond git rev-list) | NOT implemented ✅ |
| Network calls | NOT implemented ✅ |
| Shell interception/wrappers | NOT implemented ✅ |
| Telegram inbound commands | NOT implemented ✅ |
| Remote shell / /run | NOT implemented ✅ |
| Enforcement | NOT implemented ✅ |
| Autonomous mutation | NOT implemented ✅ |
| Automatic apply | NOT implemented ✅ |
| 94R implementation | NOT started ✅ |

## 12. Deferred Work

| Item | Target Phase |
|------|-------------|
| Real backend adapter design | 94R |
| Real backend invocation preflight | TBD |
| Task memory auto-cleanup | Future |
| Approval expiry check | TBD |

---

*Phase 94Q.1 is a corrective bootstrap/session/reporting/runtime hardening phase. No real backend invocation, apply execution, patch parsing, file mutation, subprocess, network, shell interception, enforcement, or autonomous mutation was implemented.*
