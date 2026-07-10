# Phase 134B.2 Complete — External Delivery Isolation Independent Verification

## 1. Phase Identity

- **Phase ID:** `134B.2`
- **Status:** completed
- **Phase class:** dedicated adversarial verification
- **Report completeness:** complete
- **Runtime:** Observed; maximum capability `observe`; execution unavailable

## 2. Executive Summary

Phase 134B.2 independently re-derived, from source and fresh adversarial
probes, whether Phase 134B.1's isolation repair held at a channel-agnostic
architectural boundary rather than trusting 134B.1's report. It did not: a
second real dispatch call site (`pcae notify send-report`) bypassed
134B.1's boundary entirely. A single, minimal, shared authorization gate now
closes that gap and applies automatically to any future delivery adapter.

## 3. Architectural Findings

Isolation was a five-name environment-variable deny-list
(`tests/conftest.py`) plus one call site's (`finalize_phase_report()`)
master-switch check on `PCAE_NOTIFY_ENABLED`. Sink construction was a
hardcoded `if/elif` name chain, not an adapter registry. A second real
dispatch call site, `run_notify_send_report()` (the `pcae notify
send-report` CLI), constructed `TelegramSink()` directly and never read
`PCAE_NOTIFY_ENABLED` — gated only by that one adapter's own internal
`is_enabled()` check. Protection of that call site under ordinary tests was
coincidental: it worked only because `TelegramSink`'s three env-var names
happened to be in the sanitizer's literal list.

## 4. Implementation Findings

`src/pcae/core/notifications.py`'s `dispatch()` — the one function every
real and future call site already shares — now requires
`PCAE_NOTIFY_ENABLED` to be truthy before invoking any sink that is not on
an explicit local/no-network allowlist (`NoopSink`, `StdoutSink`,
`FilesystemSink`, `MockSink`). Unlisted sinks, including ones that do not
exist yet, are fail-closed by default. No new environment variables, no
sanitizer-list extension, and no per-call-site duplication were required.
`tests/test_telegram_notifications.py::test_telegram_sink_in_dispatcher`
was updated to set `PCAE_NOTIFY_ENABLED=1` since it deliberately exercises
an enabled `TelegramSink` through the dispatcher.

## 5. Verification Findings

Ten fresh adversarial tests
(`tests/test_external_delivery_isolation_134b2_verification.py`) prove: the
sanitizer allowlist is name-specific, not concept-generic; a synthetic
future adapter is blocked by `dispatch()` automatically with no new code;
`run_notify_send_report()` previously reached a live Telegram transport
call while `PCAE_NOTIFY_ENABLED` was unset (reproduced, then fixed);
message and document delivery already shared one gate; no retry loop
exists to escape isolation; the subprocess-env sanitizer strips only its
five known names; `TelegramSink` reads environment fresh per construction
with no caching; and a synthetic `send-report` invocation cannot write the
real notification-dispatch idempotency marker.

## 6. Technical Debt Review

Recorded transport-neutrally, none BLOCKING: (1) no durable per-attempt
external-delivery receipt ledger across all sinks — carried to Track 134
134D–134F; (2) the governed live-integration opt-in
(`PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1`) suppresses env stripping but does
not supply independent test-only credentials — requires two deliberate
operator actions, not an accidental-escape risk; (3) synthetic payloads are
not visibly marked at the isolation-layer level; (4) no pytest marker
scopes live-integration tests for collection-time exclusion.

## 7. Notable Engineering Knowledge

A test-suite environment sanitizer that enumerates known variable names by
hand is not the same thing as an architectural authorization boundary — it
protects exactly the call sites and adapters a human happened to name. The
correct boundary lives at the one function every caller already shares
(`dispatch()`), gated by an allowlist of known-safe sink types so unlisted
(including future) sinks fail closed by construction, not by enumeration.

## 8. Governance Results

- `pcae check`: passed.
- task memory: clean.
- governed commit/push commands only (`pcae commit implementation`, `pcae
  push`, `pcae task new`/`finish`).
- Telegram remains configured for the one genuine completion delivery.
- Runtime remains Observed; execution unavailable.

## 9. Test Results

- Focused external-delivery isolation regressions: 207 passed (134B.1 +
  telegram + phase_reports + 134B.2 verification).
- Related notification/gate/certification/permission-broker suites: 165
  passed.
- Fast-green: 4389 passed, 1 pre-existing unrelated failure
  (`test_pytest_dry_run_not_blocked`, reproduced identically on the
  pre-repair baseline commit `ca81238a`).
- `compileall`: passed.

## 10. No-Go Confirmation

No 134C, notification/PFN-001 redesign, Canonical Engineering Evidence,
Evidence Extraction, Derived Evidence Views, generic Delivery Adapter
architecture, Operator Report View, Track 134 lifecycle architecture,
Repository Intelligence, stale-metadata/Architecture-Status repair beyond
this phase's own, schema, runtime, or execution work occurred. No raw git
commit/push, `--no-verify`, or force push was used.

## 11. Architectural Boundary Confirmation

PFN-001 remains mandatory and unchanged. Exactly-once certification and
marker behavior are untouched. `pcae phase complete` / `pcae task finish
--commit` behavior is unchanged (already gated correctly). `pcae notify
send-report` now additionally requires `PCAE_NOTIFY_ENABLED=1` — not a
regression for the operator's real environment, which already sets it
alongside `PCAE_TELEGRAM_ENABLED`.

## 12. Track Progress

134B.2 is a dedicated adversarial-verification phase inserted after
134B.1's repair. It closes a real architectural gap 134B.1 left open
without advancing the 134C verification or 134D–134F implementation
sequence.

## 13. Next Phase

Recommended: **134C — Canonical Phase Finalization & Reporting Lifecycle
Contract Verification**. Phase 134C has not begun.
