# Phase 92D.4 — Finalization Notification Dispatch Visibility and Runtime Env Loading

```
phase_name    = phase_92d_4_finalization_notification_dispatch_visibility
phase_version = 1.0
phase_status  = completed
implementation_status = corrective_repair
recommended_next_phase = 93C — Shell Gate Audit Evidence Model
```

## 1. Purpose

Fix three operational gaps in PCAE notification dispatch:

1. **Notification dispatch visibility**: `pcae phase complete` output did not clearly report whether notification dispatch was sent, skipped, or failed.
2. **Stale status text**: `pcae notify status` showed "Telegram is available but disabled unless configured" even when Telegram was configured and enabled.
3. **Misleading `Files changed: 0`**: After push, `origin/main..HEAD` is empty, causing `_gather_files_changed()` to return 0, which rendered as "Files changed: 0" instead of "not captured".

## 2. Root Causes

### 2.1 Sparse Notification Output

`_finalize_report_and_notify()` printed only:
```
Notifications: skipped (disabled — set PCAE_NOTIFY_ENABLED=1)
```
or a simple per-sink status line. No summary of sent/skipped/failed, no reason for skip, no report path.

### 2.2 Hardcoded Status Text

`run_notify_status()` always printed the same 3-line footer regardless of actual Telegram/notify configuration state.

### 2.3 Empty Diff Range After Push

`_gather_files_changed()` used `git diff --name-only origin/main..HEAD` which returns 0 files when all commits are pushed. The render logic showed `files_changed > 0 or self.commits` → "Files changed: 0" which is misleading.

## 3. Repairs

### 3.1 Notification Dispatch Visibility

`_finalize_report_and_notify()` now prints:
```
Notification dispatch: sent
  Sinks attempted:  telegram
  Report sent:      .pcae/phase-reports/20260629-063810-92D.3.md
  [telegram]: OK — Telegram: summary sent, document sent
```

Or when skipped:
```
Notification dispatch: skipped
  Reason: PCAE_NOTIFY_ENABLED is not set to 1/true/yes
```

Errors are redacted (token and chat ID replaced with `[REDACTED_TOKEN]` / `[REDACTED_CHAT_ID]`).

### 3.2 Context-Sensitive Status Text

`pcae notify status` now prints context-sensitive guidance:

- **Configured + Enabled**: "✅ Telegram is configured, enabled, and ready for outbound delivery."
- **Configured but Disabled**: "Telegram is configured but disabled (PCAE_TELEGRAM_ENABLED not set)."
- **Enabled but Unconfigured**: "Notifications are enabled but Telegram is not configured."
- **Neither**: Original fallback text.

### 3.3 Files Changed "not captured"

- `_gather_files_changed()` now returns `-1` when `origin/main..HEAD` is empty (pushed)
- `render_markdown()` now only shows a number when `files_changed > 0` (positively measured), never `files_changed > 0 or self.commits`
- Result: "Files changed: not captured" instead of misleading "Files changed: 0"

## 4. No-Go Conditions

- No Telegram polling, webhooks, or inbound command reception
- No `/run`, `/commit`, `/push`, or remote shell from Telegram
- No shell interception or wrappers
- No backend invocation
- No enforcement
- No token or chat ID leakage in output
- No test weakening, xfail, or skip

## 5. Test Coverage

| Test | Category |
|------|----------|
| `test_files_changed_zero_shows_not_captured` | files_changed rendering |
| `test_files_changed_positive_shows_number` | files_changed rendering |
| `test_files_changed_zero_no_commits_shows_not_captured` | files_changed rendering |
| `test_notification_skipped_when_disabled` | Skip metadata |
| `test_notification_failure_non_fatal` | Non-fatal failure |
| `test_notification_result_includes_paths` | Path metadata |
| `test_status_shows_ready_when_configured_and_enabled` | Status text |
| `test_status_shows_configured_but_disabled_when_tg_disabled` | Status text |
| `test_status_shows_unconfigured_when_missing_token` | Status text |
| `test_status_json_includes_correct_state` | JSON status |
| `test_no_token_leaked_in_status` | Secret redaction |

11 new tests (129 total report+notification).

---

*Phase 92D.4 is a corrective repair for notification dispatch visibility and status text accuracy. No Telegram polling, inbound commands, remote shell, /run, command execution, shell interception, wrappers, backend invocation, or enforcement was implemented. Recommended next phase: 93C — Shell Gate Audit Evidence Model.*
