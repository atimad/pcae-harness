# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R — Durable Telegram Notification Acceptance Receipts + Phase-Completion Notification Auditability Repair

## Scope

Product repair, not verification. Repairs a genuine PCAE notification-
lifecycle observability defect exposed by a read-only audit of the
completed configured-agent-identity IV (`...1.1R.1`)'s Telegram
dispatch: real Telegram Bot API responses (`ok`, `message_id`) were
collapsed into an in-process boolean and discarded, leaving no durable
post-hoc proof of API acceptance. No F-5 continuation, no host
mutation, no re-dispatch of the affected historical IV report.

## Lineage

- Notification-repair phase-entry SHA (`N_ENTRY`) = `9c88f1a3`
- The prior full-repository sweep (40587 passed / 979 failed / 117
  errors) was produced against this same `src/pcae` state
  (byte-unchanged from `67d542ef` through `N_ENTRY`) and remains
  frozen, separate, unattributed evidence — not touched, classified,
  or repaired by this phase.

## Architecture adjudication

An "External Delivery Receipt Model" (Phase 134E.7) and its companion
delivery-pipeline adapter registry (Phase 134E.6) already exist in
this codebase, but both are explicitly documented as not-yet-active
lifecycle authority — nothing in the real notification path calls
into them, and their only registered adapters are synthetic
(`recording_v1`) or no-op (`null_v1`); wiring a real external Telegram
adapter into that architecture is explicitly reserved for a separate,
not-yet-implemented "Final Lifecycle Integration" phase (134E.10).
Reusing it here would have meant implementing that separate,
much-larger integration as an unrelated expansion of this narrowly-
scoped repair. This repair therefore adds the smallest new,
purpose-built receipt persistence directly alongside `TelegramSink`,
consistent with that architecture's vocabulary (attempt identity,
durable pre-attempt state, explicit outcome classification) without
adopting its adapter/pipeline machinery. No frozen contract governs
`notification_result`'s or the phase-report schema's shape, and
`notification_result` is explicitly excluded from the certified report
content hash (`compute_report_digest()`'s own documented exclusion) —
confirming additive fields here required no contract adjudication.

## Repair

`src/pcae/core/notifications.py`:

- A closed receipt-status vocabulary: `PREPARED`, `API_ACCEPTED`,
  `API_REJECTED`, `TRANSPORT_FAILED`, `OUTCOME_UNCERTAIN`.
- `TelegramSink.send()` now persists a durable `PREPARED` receipt
  *before* each network call (summary and document independently),
  then a final classified receipt afterward, atomically written
  (tmp-file + `os.replace`) to `.pcae/notification-receipts/<event_id>/
  <receipt_id>.json` (overridable via `PCAE_NOTIFICATION_RECEIPTS_DIR`,
  matching the existing `PCAE_NOTIFY_OUTPUT_DIR` convention).
- `_api_call_form`/`_api_call_multipart` now capture the real HTTP
  status and a failure-kind tag (`api_rejected` / `http_error` /
  `transport_failed`) alongside Telegram's parsed JSON, without
  changing their existing return-shape contract for callers that
  only read `ok`/`error`.
- `_classify_telegram_result()` applies strict validated-response
  semantics: `ok: true` without a valid integer `message_id` is
  `OUTCOME_UNCERTAIN`, never blindly accepted as `API_ACCEPTED`.
- Receipts never persist the bot token, the raw API URL, or Telegram
  chat/user profile data — only a stable, non-reversible destination
  alias (`sha256("telegram-chat:" + chat_id)[:12]`).
- A receipt-persistence failure (e.g. disk unavailable) cannot crash
  the sink (`NotificationSink.send()` must never raise); it is
  surfaced via `NotificationResult.metadata`/`.error` and a best-effort
  plain-text `PERSISTENCE-FAILURES.log` fallback, never silently
  reclassified as a safe, resendable state.
- `NotificationResult.success`'s existing contract —
  `msg_result["ok"] and doc_result.get("ok", False)` — is byte-
  unchanged; the receipt model is strictly additive evidence, never a
  redefinition of that boolean.
- Exactly one attempt per operation; no retry loop exists, so no
  duplicate-send risk is introduced by this repair.

`src/pcae/core/phase_reports.py`:

- A new `_telegram_receipts_summary()` helper pulls the per-operation
  receipt references (status, message_id, receipt_id, for summary and
  document independently) out of `NotificationResult.metadata` into
  the persisted `report.notification_result["telegram_receipts"]` —
  additive at all four call sites that build that dict, `[]` when no
  telegram sink was used or dispatch was skipped/pending. Historical
  reports without this key remain fully readable
  (`.get("telegram_receipts", [])` pattern; nothing crashes on
  absence).

`tests/conftest.py`:

- A new autouse `_isolate_notification_receipts_dir` fixture points
  `PCAE_NOTIFICATION_RECEIPTS_DIR` at a per-test `tmp_path` by default,
  matching the existing `_isolate_external_notifications` fixture's
  purpose — an ordinary unit test that constructs `TelegramSink` with
  an explicit fake `_opener` (as this repo's existing
  `test_telegram_notifications.py` suite already does, by design, to
  exercise the sink deterministically) would otherwise write real
  receipt files into this repository's own working tree as a side
  effect of merely running the test suite. Individual tests may still
  override the same env var to assert on receipt content.

## Verdict

**DURABLE TELEGRAM ACCEPTANCE RECEIPT / PHASE-NOTIFICATION
AUDITABILITY REPAIR: IMPLEMENTED — FRESH INDEPENDENT VERIFICATION
REQUIRED.**

Not independently verified in this phase. No re-dispatch of the
missing configured-agent IV report performed.

## Historical case

`...1.1R.1`'s original Telegram dispatch remains historically
unchanged: its persisted `notification_result` keeps the legacy
in-process `success: true` boolean and no `telegram_receipts` (this
repair began after that dispatch). Durable Telegram acceptance
receipt for that specific dispatch: **ABSENT.** Original external
outcome: **NOT INDEPENDENTLY AUDITABLE FROM DURABLE PCAE EVIDENCE** —
neither confirmed delivered nor confirmed failed. No receipt was
fabricated for it (confirmed by fresh-suite test scanning
`.pcae/notification-receipts/` for that phase_id).

## Regression

Fresh 41-case suite: 41 passed. Full notification/phase-report/
finalization consumer sweep (43 files + fresh suite): 1438 passed, 2
pre-existing unrelated failures deselected (independently reproduced
byte-identical against a fixed `N_ENTRY` baseline worktree —
`test_duplicate_terminal_delivery_mixed_evidence_134e81.py`, report-
coherence issue-count assertions unrelated to notifications). Four
initially-attributable failures (`test_delivery_pipeline_134e6.py`,
`test_delivery_receipt_134e7.py` — blunt substring/grep scope-fence
guards tripped by this repair's own explanatory comment literally
naming the dormant modules it deliberately did not wire into) were
resolved by rewording that comment, not by touching any test file —
zero `def test_` renamed/removed, zero test files modified besides the
one new `conftest.py` fixture.

## Contracts / dependencies

`docs/contracts/` and `pyproject.toml`: byte-unchanged since `N_ENTRY`.

## Production diff scope

`src/pcae/core/notifications.py`, `src/pcae/core/phase_reports.py`,
`tests/conftest.py` (test-isolation fixture only) — no other
production file changed.

## Host / F-5 / N-16-5

No host mutation, no protected-root/PPA action, no YubiKey/FIDO2/human
approval interaction. F-5 continuation technical prerequisite remains
**READY (not begun)**; F-5 continuation **execution** remains **HOLD
pending post-completion full-suite triage** (40587/979/117, frozen,
separate). N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.
Runtime remains `not_implemented / Observed / observe / unavailable`,
zero plugins/capabilities, first governed runtime effect absent.

## Recommended next (not begun)

Independent Verification of Durable Telegram Acceptance Receipts and
Phase-Completion Notification Auditability.
