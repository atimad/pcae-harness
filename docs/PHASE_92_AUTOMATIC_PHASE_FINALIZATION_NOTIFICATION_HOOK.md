# Phase 92D — Automatic Phase-Finalization Notification Hook

```
phase_name    = phase_92d_automatic_phase_finalization_notification_hook
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 93A — Narrow Shell Gate Design
```

## 1. Purpose

Integrate the 92A phase report artifact model and 92B/92C notification foundation into the governed `pcae phase complete` lifecycle. Phase reports are created automatically on phase finalization. Notification dispatch is opt-in and disabled by default.

## 2. Scope

In scope:

- Auto-create phase report artifacts on `pcae phase complete`
- Optional notification dispatch via `PCAE_NOTIFY_ENABLED`
- `finalize_phase_report()` reusable hook function
- 16 new tests

Out of scope: Telegram polling, inbound, automatic commit/push, enforcement.

## 3. Finalization Hook Behavior

On `pcae phase complete`:

1. Phase provenance is recorded (existing behavior)
2. Agent lock is released (existing behavior)
3. **NEW**: `finalize_phase_report()` is called:
   - Derives phase_id, phase_name, next_phase from the summary text
   - Creates `.pcae/phase-reports/latest.md` and `latest.json`
   - Creates timestamped artifacts
   - If `PCAE_NOTIFY_ENABLED=1`, dispatches to configured sinks
4. Results are printed to the operator

## 4. Report Artifact Generation

The generated report includes all fields that can be derived:
- phase_id, phase_name, status="completed"
- summary text
- recommended_next_phase (parsed from summary)
- explicit_no_go_confirmations (if provided)
- Optional: files_changed, tests_run, test_results, governance_results, commits, pushed_status, origin_main_head_count

## 5. Optional Notification Dispatch

Controlled by environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PCAE_NOTIFY_ENABLED` | (disabled) | Set to `1`/`true`/`yes` to enable |
| `PCAE_NOTIFY_SINKS` | `filesystem` | Comma-separated sink names: noop, filesystem, telegram |
| `PCAE_NOTIFY_OUTPUT_DIR` | `.pcae/notifications` | Filesystem sink output directory |

## 6. Disabled-by-Default Policy

Notifications are **disabled by default**. The operator must explicitly set `PCAE_NOTIFY_ENABLED=1` before any notification is dispatched. This prevents accidental external delivery during development.

## 7. Telegram Outbound-Only Behavior

Telegram notifications use the existing 92C `TelegramSink` with env var config (`PCAE_TELEGRAM_BOT_TOKEN`, `PCAE_TELEGRAM_CHAT_ID`, `PCAE_TELEGRAM_ENABLED`). No inbound commands. No polling.

## 8. Failure Semantics

- **Report creation failure**: Error is printed; phase finalization completes normally
- **Notification failure**: Individual sink failures are recorded; other sinks continue; phase finalization completes normally
- **Telegram disabled/unconfigured**: Skipped gracefully; no error

**Notification failure is always non-fatal to phase finalization.**

## 9. Manual Resend Path

If automatic notification fails, the operator can manually resend:

```
pcae notify send-report --latest
```

This reads the latest phase report from `.pcae/phase-reports/` and dispatches via Telegram.

## 10. Relationship to 92A / 92B / 92C

- **92A**: Creates the artifact model. 92D auto-creates artifacts on finalization.
- **92B**: Notification foundation. 92D dispatches via the same `dispatch()` function.
- **92C**: Telegram sink. 92D dispatches via `TelegramSink` when configured.

## 11. No-Go Conditions

- No Telegram polling, inbound commands, remote shell, /run
- No commit/push control from Telegram
- No shell interception, wrappers, backend invocation
- No enforcement

---

*Phase 92D integrates phase report creation and optional notification dispatch into the governed phase-finalization lifecycle. 16 new tests, 365 total regression tests pass. No Telegram polling, inbound commands, remote shell, /run, commit/push control, enforcement, shell interception, wrappers, backend invocation, or command execution path was implemented. Recommended next phase: 93A — Narrow Shell Gate Design.*
