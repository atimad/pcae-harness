# Phase 92D.7 — Telegram Handoff Message Precision Tightening

```
phase_name    = phase_92d_7_telegram_handoff_message_precision_tightening
phase_version = 1.0
phase_status  = completed
recommended_next_phase = 93D — Shell Gate Audit Persistence Design
```

## 1. Why Precision Matters

Telegram phase reports are now the primary remote handoff artifact. Ambiguous commit labeling (all commits shown as phase commits), cluttered format, and duplicated sections reduce trust and increase the risk of misreading.

## 2. Telegram Text Contract

The Telegram `sendMessage` text follows this structure:

```
PCAE Phase 92D.7 ✅
Telegram Handoff Message Precision Tightening
Trust: complete ✅

Files changed: 6
Tests added: 2
Tests: Report + notification: 149/149 (passed); Broker + shell gate: 387/387 (passed)
Governance: pcae health healthy, pcae check passed, pcae push check nothing_to_push

Phase commit: 3b61d31
Recent commits: b4c71ad6, e49b4a74
Push: pushed, origin/main..HEAD 0
Notification: sent via telegram
No-go: No Telegram polling, inbound commands, remote shell, /run, enforcement...
Next: 93D

Full report attached.
```

### Precision guarantees:
- **Trust state near top** — immediately visible if review is needed
- **Phase commit distinct** — only the actual phase commit labeled as such
- **Recent commits separate** — clearly labeled, excludes phase commit
- **Compact validation** — single-line tests and governance for mobile readability
- **No long summary body** — full details in Markdown attachment

## 3. Commit Labeling

| Before | After |
|--------|-------|
| `Phase commit: abc` (first of undifferentiated list) | `Phase commit: abc` (explicitly first) |
| `Recent commits: abc def ghi` (includes phase commit) | `Recent commits: def, ghi` (excludes phase commit) |
| No fallback for missing phase commit | `Phase commit: not captured` |

## 4. Trust State Placement

Trust state moved near top, right after header:
- `Trust: complete ✅`
- `Trust: partial ⚠️  Missing: files_changed, tests_run`
- `Trust: incomplete ❌ Manual review required`

## 5. No-Go Conditions

- No Telegram polling, inbound commands, remote shell, /run
- No enforcement, shell interception, wrappers, backend invocation
- No fabrication of missing data

---

*Phase 92D.7 tightens Telegram handoff message precision. 0 new tests, 2 test fixes. No Telegram polling, inbound commands, remote shell, /run, command execution, shell interception, wrappers, backend invocation, or enforcement was implemented.*
