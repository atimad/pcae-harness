# Phase 92D.8.1 — Canonical Report Metadata Consistency Guard

## Why

92D.8 introduced canonical final-report artifacts, but PCAE could mark a report complete even when `.pcae/phase-completion-report.md` and `.pcae/phase-completion-metadata.json` disagreed (e.g., stale validation totals from prior phase).

## Compared Fields

- Validation/test result totals (e.g., "Fast-green: 100/100" vs "149/149")
- Phase commit hash presence in canonical report
- Pushed status

## Mismatch Severity

| Type | Trust Impact |
|------|-------------|
| Validation total mismatch | Downgrade to partial ⚠️ |
| Phase commit not in canonical | Warning added |
| All consistent | Remains complete ✅ |

## Report Consistency Section

Markdown reports now include a "Report Consistency" section showing canonical/metadata presence and mismatch status.

## Telegram Behavior

Compact text shows trust state with warnings. Full report attached.

## No-Go

No Telegram polling, inbound, remote shell, /run, enforcement, shell interception, wrappers, backend invocation.
