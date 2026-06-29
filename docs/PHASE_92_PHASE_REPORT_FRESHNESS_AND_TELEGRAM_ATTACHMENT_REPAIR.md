# Phase 92D.3 — Phase Report Freshness and Telegram Attachment Repair

```
phase_name    = phase_92d_3_phase_report_freshness_and_telegram_attachment_repair
phase_version = 1.0
phase_status  = completed
implementation_status = corrective_repair
recommended_next_phase = 93C — Shell Gate Audit Evidence Model
```

## 1. Purpose

Fix PCAE phase completion reporting so Telegram sends the current phase's completed report, not a stale previous `latest.md`. Ensure the governed phase completion path writes a current phase report before notification dispatch, and that the notification uses the exact report artifact generated for the current phase.

## 2. Root Cause

Three contributing factors:

1. **Sparse report metadata**: `_finalize_report_and_notify()` in `phase.py` called `finalize_phase_report()` with only `phase_id`, `phase_name`, `status`, and `summary`. All other fields (`files_changed`, `commits`, `pushed_status`, `tests_run`) defaulted to zero/empty → rendered as "not captured" in the Markdown report.

2. **Stale phase name parsing**: `_derive_phase_name()` captured the trailing " — completed" suffix from the summary text, producing names like "Telegram Payload Compatibility Repair — completed" instead of clean phase names.

3. **latest.md attachment path**: `finalize_phase_report()` attached `paths["latest_markdown"]` (the `latest.md` symlink) for notification delivery. While `write_phase_report` does update `latest.md` before the notification dispatch runs, using the timestamped path is more explicit and auditable.

## 3. Repairs

### 3.1 Enriched Report Metadata

`_finalize_report_and_notify()` now gathers:
- `commits`: last 5 commit hashes from `git log --oneline`
- `files_changed`: count of files in `git diff --name-only origin/main..HEAD`
- `pushed_status`: "pushed" or "not_pushed" from `git log origin/main..HEAD`
- `origin_main_head_count`: from `git rev-list --count origin/main..HEAD`

These are passed to `finalize_phase_report()` so the generated report contains accurate metadata instead of "not captured".

### 3.2 Cleaned Phase Name

`_derive_phase_name()` now strips trailing status markers (` — completed`, ` — failed`, etc.) from the parsed phase name.

### 3.3 Timestamped Report Path for Attachment

`finalize_phase_report()` now uses `paths["markdown"]` (the timestamped path, e.g., `20260629-062236-92D.2.md`) for notification attachment instead of `paths["latest_markdown"]`. This guarantees the attached document is unambiguously the current phase report.

### 3.4 Improved Human Output

`pcae notify send-report --latest` now displays:
```
Telegram send-report
  Phase:   92D.2 — Telegram Payload Compatibility Repair
  Status:  completed
  Report:  .pcae/phase-reports/latest.md
  [OK] Telegram: summary sent, document sent
```

## 4. Summary vs Full Attachment

- **Telegram short message** (`sendMessage`): `[SEVERITY] Phase STATUS: Name\n\nSummary` — truncated at 3500 chars
- **Telegram document attachment** (`sendDocument`): Full `latest.md` Markdown — includes phase ID, name, status, files changed, tests, commits, push status, governance results, no-go confirmations, and recommended next phase

## 5. No-Go Conditions

- No Telegram polling, webhooks, or inbound command reception
- No `/run`, `/commit`, `/push`, or remote shell from Telegram
- No shell interception or wrappers
- No backend invocation
- No enforcement
- No test weakening, xfail, or skip

## 6. Test Coverage

| Test | Category |
|------|----------|
| `test_write_updates_latest_md` | latest.md freshness |
| `test_write_updates_latest_json` | latest.json freshness |
| `test_latest_overwritten_by_newer_phase` | Overwrite behavior |
| `test_read_latest_report_returns_latest` | read_latest_report |
| `test_timestamped_artifact_created` | Timestamped artifact |
| `test_notification_uses_timestamped_path` | Attachment path |
| `test_latest_md_matches_timestamped` | Content parity |
| `test_notification_uses_current_phase_id` | Phase ID correctness |

8 new tests added to existing 37 phase report tests = 45 total.

---

*Phase 92D.3 is a corrective repair for phase report freshness and Telegram attachment. No Telegram polling, inbound commands, remote shell, /run, command execution, shell interception, wrappers, backend invocation, or enforcement was implemented. Recommended next phase: 93C — Shell Gate Audit Evidence Model.*
