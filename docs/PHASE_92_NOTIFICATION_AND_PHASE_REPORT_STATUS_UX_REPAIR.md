# Phase 92D.1 — Notification and Phase Report Status UX Repair

```
phase_name    = phase_92d1_notification_and_phase_report_status_ux_repair
phase_version = 1.0
phase_status  = completed
recommended_next_phase = 93A — Narrow Shell Gate Design
```

## 1. Scope

Corrective UX phase fixing two issues:
1. `pcae notify status` was stale (claiming "No Telegram" after 92C, "No automatic hooks" after 92D)
2. `pcae phase-report show --latest` was too sparse (misleading zeroes, missing detail)

## 2. notify status Before/After

**Before:** "No Telegram, no external network, no automatic hooks."

**After:** Shows accurate state:
- Telegram sink available (92C), disabled unless configured
- Auto finalization hook available (92D), dispatch disabled by default
- Token/chat ID presence (never values)
- Configured sinks from env
- External network possible only when Telegram enabled

## 3. phase-report show Before/After

**Before:** `Files changed: 0`, `Tests run: 0` — misleading zeroes when data was simply not captured.

**After:** `Files changed: not captured`, `Tests run: not captured` — clearly distinguishes unknown from zero.

Also shows commits, pushed status, origin/main..HEAD only when relevant.

## 4. Unknown-vs-Zero Semantics

| Field | Zero | Unknown |
|-------|------|---------|
| files_changed | "0" (known: no files changed) | "not captured" |
| tests_run | "0" (known: no tests run) | "not captured" |
| commits | (empty, hidden) | "not captured" |
| pushed_status | (shown as-is) | "not captured" |

## 5. Secret Redaction

`pcae notify status` shows token/chat ID presence only ("present"/"missing"), never prints actual values. No secret is ever included in phase report output.

## 6. No-Go Conditions

- No Telegram polling, inbound, remote shell, /run
- No enforcement, shell interception, wrappers, backend invocation

---

*Phase 92D.1 repairs operator-facing UX for notifications and phase reports. 100 related tests pass. Recommended next phase: 93A.*
