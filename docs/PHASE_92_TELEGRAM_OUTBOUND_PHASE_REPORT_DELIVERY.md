# Phase 92C — Telegram Outbound Phase Report Delivery

```
phase_name    = phase_92c_telegram_outbound_phase_report_delivery
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 92D — Automatic Phase-Finalization Notification Hook
```

## 1. Purpose

Implement Telegram as an outbound notification sink for PCAE phase reports. Telegram is ONE sink in the 92B pluggable notification foundation — not a separate system. Manual command only; no inbound, no polling, no remote shell.

## 2. Scope

In scope:

- `TelegramSink` implementing `NotificationSink` protocol
- `sendMessage` (short summary) + `sendDocument` (full report file)
- Environment variable configuration only (PCAE_TELEGRAM_BOT_TOKEN, PCAE_TELEGRAM_CHAT_ID, PCAE_TELEGRAM_ENABLED)
- CLI: `pcae notify send-report [--latest] [--json]`
- 20 tests with mocked HTTP

Out of scope: Telegram polling, inbound commands, /run, remote shell, commit/push control, automatic hooks, enforcement.

## 3. Telegram as One Notification Sink

`TelegramSink` conforms to the `NotificationSink` protocol from 92B:

```python
sink = TelegramSink()
result = sink.send(event)  # → NotificationResult
```

It works with the existing `dispatch()` function:

```python
dispatch(event, [TelegramSink(), FilesystemSink(dir)])
```

## 4. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PCAE_TELEGRAM_BOT_TOKEN` | Yes | Telegram Bot API token |
| `PCAE_TELEGRAM_CHAT_ID` | Yes | Target chat ID |
| `PCAE_TELEGRAM_ENABLED` | No | Set to `1`/`true`/`yes` to enable. Disabled by default. |

Secrets must not be committed to the repository. No token or chat ID is stored in tracked config files.

## 5. Manual Send Command

```
pcae notify send-report [--latest] [--json]
```

Behavior:
1. Reads latest phase report from `.pcae/phase-reports/latest.json` (92A)
2. Converts to notification event via `phase_report_to_notification_event()` (92B)
3. Sends short summary via Telegram `sendMessage`
4. Sends `latest.md` as a document via Telegram `sendDocument`
5. Returns structured JSON with `--json`
6. Fails safely if not configured or disabled

## 6. Short Summary + Full Report Document

- **Summary**: `[SEVERITY] Phase STATUS: Name\n\nSummary text` — truncated at 3500 chars (configurable)
- **Document**: `latest.md` attached as a Telegram document with original filename

## 7. Relationship to 92A / 92B

- **92A**: Creates phase report artifacts. 92C reads `latest.json` and sends `latest.md`.
- **92B**: Notification foundation. 92C adds `TelegramSink` as a new sink implementation.
- **92D**: Will add automatic trigger on `pcae phase complete`.

## 8. Why Inbound Telegram Commands Are Not Implemented

Per the Production v1 roadmap: Telegram is **outbound only**. Inbound commands (polling, webhooks, /run, commit/push) require:
- Permission broker and shell gate maturity
- Operator authentication and command confirmation
- Full governance parity with CLI commands
- A separate design phase (future v2+)

## 9. Why Automatic Finalization Is Deferred to 92D

Manual send-report must be stable before automation. 92D will hook `pcae phase complete` to trigger `write_phase_report()` + `dispatch()`.

## 10. No-Go Conditions

- No Telegram polling, webhooks, or inbound command reception
- No `/run`, `/commit`, `/push`, or remote shell
- No automatic phase-finalization hook
- No shell interception or wrappers
- No backend invocation
- No enforcement

---

*Phase 92C implements Telegram as an outbound notification sink. 54 total notification tests pass. No Telegram polling, inbound commands, remote shell, /run, commit/push control, automatic finalization hook, enforcement, shell interception, wrappers, backend invocation, or command execution path was implemented. Recommended next phase: 92D — Automatic Phase-Finalization Notification Hook.*
