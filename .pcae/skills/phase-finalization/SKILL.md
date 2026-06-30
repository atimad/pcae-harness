# Skill

## Skill ID

phase-finalization

## Skill Name

Phase Finalization and Report Authoring

## Skill Type

workflow

## Skill Version

1.0.1

## Skill Status

active

## Human Review Required

true

## Purpose

Guide the operator through writing complete `.pcae/phase-completion-metadata.json` before running `pcae phase complete`. Ensure all mandatory trust fields, governance evidence, test evidence, and no-go confirmations are present. Reports must not be marked complete unless all required keys are populated.

## Required Top-Level Trust Fields

- `phase_id`
- `phase_name`
- `status`
- `files_changed`
- `tests_run`
- `commits`
- `pushed`
- `origin_main_head`
- `summary`
- `governance_results`
- `test_results`
- `notification_dispatch`
- `no_go_confirmations`
- `recommended_next_phase`
- `report_consistency`

## Required Governance Keys

- `pcae_health`
- `pcae_check`
- `pcae_doctor_task_memory`
- `pcae_push_check`
- `telegram_runtime`

## Required Test Evidence

- `report_notification_tests`
- `bootstrap_session_reporting_tests`
- `fast_green`
- Backend/model/CLI tests if the phase touched source or tests
- Known pre-existing failure classification where applicable

## Required No-Go Confirmations

Must include at minimum:
- no real backend invocation
- no adapter execution
- no subprocess execution
- no network call
- no shell interception
- no Telegram inbound
- no enforcement
- no automatic apply
- no apply execution
- no commit/push authorization
- no real AI backend calls
- next phase not started

## Forbidden Final Report Patterns

The agent MUST NOT produce final reports with:

- `Files changed: not captured` — always capture actual count
- `Tests run: not captured` — always capture actual count or state `0 (review-only)`
- empty `governance_results` dict
- empty `test_results` dict
- abbreviated no-go text such as "No real backend invocation or execution."
- `complete ✅` with missing dotted trust fields in `missing_trust_fields`
- stale previous phase IDs anywhere in metadata
- `recommended_next_phase` that points backward or to itself
- `recommended_next_phase` that skips a corrective hardening phase
- summary that says "Next: 95H.1" but structured says "95I" (mismatch)
- Telegram report not re-sent after report repair

If any of these forbidden patterns appear, the agent MUST stop and repair the report before proceeding.

## Final Report Preflight Checklist

Before `pcae phase complete`, the agent MUST run and verify:

```
pcae phase-report show --latest
cat .pcae/phase-completion-metadata.json
pcae health
pcae check
pcae doctor task-memory
pcae push check
source ~/.config/pcae/telegram.env
pcae notify status
```

After `pcae phase complete`, the agent MUST:

```
pcae phase-report show --latest
pcae notify send-report --latest
```

Verify that:
- Report shows `complete ✅` with no `missing_trust_fields`
- Governance Results has all 5 keys populated
- Test Results has all applicable suites
- No-Go Confirmations has 12+ separate items each starting with "No "
- Recommended Next Phase points forward
- Commits are actual phase-specific hashes, not stale
- origin/main..HEAD is 0
- Telegram was sent and confirmed

## Agent-Specific Rules

- The agent MUST NOT use placeholder text such as "not captured."
- The agent MUST NOT mark a report complete if `files_changed`/`tests_run` are unknown.
- If validation results are missing, the agent MUST rerun or explicitly capture them before finalization.
- The agent MUST verify `.pcae/phase-completion-metadata.json` before `pcae phase complete`.
- The agent MUST verify `pcae phase-report show --latest` after completion.
- The agent MUST compare summary and structured metadata for consistency.
- The agent MUST verify no stale phase IDs, stale commits, stale test totals, or stale recommended next phase.
- The agent MUST list all required no-go confirmations as explicit separate sentences each starting with "No ".
- Documentation-only/review-only phases still require governance and regression evidence.
- If the report is partial, the agent MUST stop and repair the report before proceeding.
- Next-phase recommendation MUST point to the immediate governed phase, not skip corrective hardening.

## Completeness Rules

- Report must be **partial** if any required trust field is missing.
- Report must be **partial** if required governance keys are missing.
- Report must be **partial** if required test evidence is missing, unless explicitly exempted with a documented phase-specific reason.
- Report must be **inconsistent** if summary next phase differs from structured recommended next phase.
- Report must be **inconsistent** if stale phase data appears.
- Report must be **inconsistent** if pushed/origin data contradicts git state.
- Final Telegram report must be generated only after metadata freshness and completeness checks.
- No-go confirmations must be explicit and complete for safety-sensitive phases.
- Documentation-only phases still require design-safe regressions and governance evidence.
- **Skill-only is not trusted; CLI completeness enforcement is the source of truth.**

## Workflow

1. Verify phase_id matches the completing phase — never reuse stale metadata.
2. Run all required validation suites before writing metadata.
3. Write `.pcae/phase-completion-metadata.json` with all mandatory trust fields.
4. Verify `governance_results` dict has all 5 required keys.
5. Verify `test_results` dict has all applicable test suites.
6. Verify `no_go_confirmed` dict has all required confirmations.
7. Verify `recommended_next_phase` points forward, not backward.
8. Verify `notification_dispatch_result` is present.
9. Run `pcae phase complete`.
10. Verify `pcae phase-report show --latest` shows complete and consistent.
11. Resend Telegram if report was partial: `pcae notify send-report --latest`.
12. Verify forbidden patterns are absent.
