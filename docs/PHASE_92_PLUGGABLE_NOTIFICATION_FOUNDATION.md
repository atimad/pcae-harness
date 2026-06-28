# Phase 92B — Pluggable Notification Foundation

```
phase_name    = phase_92b_pluggable_notification_foundation
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 92C — Telegram Outbound Phase Report Delivery
```

## 1. Purpose

Implement a generic, pluggable notification foundation for PCAE Production v1. Create a reusable event/sink/dispatcher model that can later support Telegram, email, Slack, and other delivery channels without modifying core notification logic.

## 2. Scope

In scope:

- `NotificationEvent` dataclass with 8 fields
- `NotificationResult` dataclass with 7 fields
- `NotificationSink` Protocol
- 4 sinks: noop, stdout/text, filesystem, mock
- `dispatch()` with multi-sink, fail-continue behavior
- `phase_report_to_notification_event()` helper (92A integration)
- CLI: `pcae notify status`, `pcae notify test`
- 34 tests

Out of scope: Telegram, external network, automatic hooks, enforcement.

## 3. Event Model

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | str | Unique `ntf-<uuid12>` |
| `event_type` | str | phase_report_created, phase_completed, phase_failed, manual_test |
| `title` | str | Human-readable title |
| `message` | str | Notification body |
| `severity` | str | info, warning, error, critical |
| `created_at` | str | ISO 8601 timestamp |
| `artifact_paths` | list[str] | Related artifact paths |
| `metadata` | dict | Phase ID, operator, etc. |

## 4. Sink Model

### Protocol

```python
class NotificationSink(Protocol):
    def send(self, event: NotificationEvent) -> NotificationResult: ...
```

### Initial Sinks

| Sink | Behavior | Side Effects |
|------|----------|-------------|
| **NoopSink** | Returns success | None |
| **StdoutSink** | Renders formatted text | Optional stdout |
| **FilesystemSink** | Writes event JSON to directory | Local disk only |
| **MockSink** | Records events in memory | None (test only) |

## 5. Dispatcher

`dispatch(event, sinks)`:
1. Validates the event
2. Attempts delivery to each sink
3. One sink failure does not prevent others
4. Returns per-sink results
5. Never raises for normal sink failures

## 6. Phase Report Integration

`phase_report_to_notification_event(report, artifact_paths)` converts a PhaseReport (92A) into a NotificationEvent. This is a pure function — it does not send anything. Prepares for 92C Telegram delivery.

## 7. CLI

```
pcae notify status [--json]
pcae notify test --sink noop|stdout|filesystem|mock [--output-dir <path>] [--json]
```

## 8. Relationship to 92A / 92C / 92D

- **92A**: Creates phase report artifacts. 92B converts them to notification events.
- **92C**: Will add a Telegram sink that implements the NotificationSink protocol. No changes to 92B core needed.
- **92D**: Will add automatic trigger on `pcae phase complete`. No changes to 92B core needed.

## 9. Why Telegram Is Deferred

92B defines the **sink interface** and **dispatcher**. Telegram delivery (92C) will implement a `TelegramSink` that conforms to the `NotificationSink` protocol. This separation ensures:
- Core notification logic is independent of delivery channel
- New sinks can be added without modifying core
- Testing does not require Telegram API access

## 10. Why Automatic Finalization Is Deferred to 92D

Manual notification testing must be stable before automation. 92D will hook `pcae phase complete` to trigger `write_phase_report()` + `dispatch()`.

## 11. No-Go Conditions

- No Telegram implementation
- No external network calls
- No automatic phase-finalization hooks
- No shell interception or wrappers
- No backend invocation
- No enforcement

---

*Phase 92B implements the pluggable notification foundation. 34 tests pass. No Telegram, external network delivery, automatic hooks, enforcement, shell interception, wrappers, backend invocation, or command execution path was implemented. Recommended next phase: 92C — Telegram Outbound Phase Report Delivery.*
