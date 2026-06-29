# Phase 92D.5 — Telegram Phase Report Trust Contract

```
phase_name    = phase_92d_5_telegram_phase_report_trust_contract
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = TBD
```

## 1. Purpose

Make Telegram phase reports trustworthy enough to use as the primary remote handoff artifact. The Telegram text must be concise, structured, and based on verified phase-report fields. If critical metadata is missing, stale, or ambiguous, Telegram must clearly warn that the report is partial/incomplete and manual review is required.

## 2. Report Completeness States

| State | Icon | Meaning |
|-------|------|---------|
| `complete` | ✅ | All trust-critical and non-fatal fields captured and consistent |
| `partial` | ⚠️ | Critical fields OK but some non-fatal fields missing (e.g. files_changed, tests_run) |
| `incomplete` | ❌ | Critical fields missing/contradictory — remote handoff unsafe, manual review required |

## 3. Trust-Critical Fields

For a completed phase, these fields determine completeness:

**Fatal** (incomplete if missing): `phase_id`, `phase_name`, `status`

**Non-fatal** (partial if missing): `files_changed`, `tests_run`, `commits`, `pushed_status`, `test_results`, `governance_results`

## 4. Telegram Text Summary Contract

The Telegram sendMessage text is now concise and structured:

```
PCAE Phase 93C completed
Report: partial ⚠️ (missing: files_changed, tests_run)
Name: Shell Gate Audit Evidence Model

Validation:
  Shell gate: 122/122
  Broker: 265/265
  Report+notification: 129/129
  Fast-green: 3272/3272
  health: healthy

Phase commit: e49b4a74
Recent commits: e49b4a74 0973b4bf 4885d6c5
Pushed: pushed
origin/main..HEAD: 0

Notification: sent via telegram
No-go: no execution, no interception, no enforcement
Next: TBD

Full report attached.
```

### Key properties:
- Concise (under 800 chars for typical phases)
- Includes completeness state with missing fields
- Distinguishes "Phase commit" from "Recent commits"
- Includes validation result lines extracted from summary
- Includes notification dispatch status
- Includes pushed status and origin count
- States "Full report attached" — detailed report is in the document

## 5. Markdown Attachment Contract

The attached `.md` document is the full phase report including:
- Phase ID, name, status
- Report completeness state
- Missing trust fields (if any)
- Full summary
- Files changed / tests run
- Test results / governance results
- Commits (all available)
- Pushed status / origin count
- No-go confirmations
- Recommended next phase
- Notification dispatch result (dispatched, sinks, success)
- Schema version

## 6. Stale-Report Protection

Before sending, the notification metadata includes `report_phase_id` and `report_phase_name` to cross-reference with the event's phase_id. If a mismatch is detected, the Telegram text includes a warning:
```
⚠️ STALE REPORT: event phase=93C, report phase=92D.4
```

Notification failure remains non-fatal to phase completion.

## 7. Phase Commit vs Recent Commits

The Telegram text separates:
- **Phase commit**: The first (most recent) commit hash
- **Recent commits**: All available commit hashes (up to the stored list)

If commits cannot be determined, shows: `Phase commits: not captured`

## 8. No-Go Conditions

- No Telegram polling, webhooks, or inbound command reception
- No `/run`, `/commit`, `/push`, or remote shell from Telegram
- No shell interception or wrappers
- No backend invocation
- No enforcement
- No token or chat ID leakage
- No real network calls in tests

## 9. Test Coverage

| Category | Tests |
|----------|-------|
| Report completeness (complete/partial/incomplete) | 8 |
| Telegram text format (phase_id, completeness, commits, notification) | 7 |
| **Total new** | **15** |

144 total report+notification tests (129 old + 15 new).

---

*Phase 92D.5 implements the Telegram phase report trust contract. 15 new tests pass. No Telegram polling, inbound commands, remote shell, /run, command execution, shell interception, wrappers, backend invocation, or enforcement was implemented.*
