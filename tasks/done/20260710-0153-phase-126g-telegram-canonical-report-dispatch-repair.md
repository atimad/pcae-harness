# Task Contract

## Task ID

20260710-0153-phase-126g-telegram-canonical-report-dispatch-repair

## Title

Phase 126G Telegram Canonical Report Dispatch Repair

## Status

done

## Mode

implementation

## Goal

Repair the notification dispatch pipeline so Telegram faithfully delivers canonical phase reports instead of a reduced generated summary. Root cause: (1) phase_report_to_notification_event() omits test_results/governance_results from event metadata even though TelegramSink._build_summary() reads them, silently dropping verification evidence; (2) Telegram document delivery trusts a static latest.md file path that can desync from the trust-checked report object rather than deriving content directly from it; (3) summary text truncation is silent with no marker, violating the required fallback contract; (4) pcae phase-report create cannot accept commits/governance_results/test_results/no_go_confirmations, forcing unsafe manual JSON editing. Repair only these verified defects.

## Allowed Files

- src/pcae/core/notifications.py
- src/pcae/commands/phase_reports.py
- src/pcae/cli.py
- tests/test_telegram_notifications.py
- tests/test_notifications.py
- tests/test_phase_reports.py
- docs/PHASE_126G_TELEGRAM_CANONICAL_REPORT_DISPATCH_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-0153-phase-126g-telegram-canonical-report-dispatch-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- cli
- core
- tests
- docs
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

- phase_report_to_notification_event includes test_results/governance_results in metadata so TelegramSink summary reflects real verification evidence
- Telegram document delivery derives content directly from the trusted PhaseReport object (report.render_markdown()), not a possibly-stale sibling file
- Summary truncation is never silent; a clear TRUNCATED marker is used when the compact summary exceeds the message limit
- pcae phase-report create accepts commits/governance-result/test-result/no-go-confirmation flags so a complete, trust-passing report can be produced through the governed CLI without hand-editing JSON
- Existing and new notification/report tests pass; fast_green passes
- No Dependency Knowledge Graph, Repository Intelligence, Historical Memory, execution, runtime plugin, Decision Evaluation, Advisory, or schema file modified
- Runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T01:53:12.933391+02:00
