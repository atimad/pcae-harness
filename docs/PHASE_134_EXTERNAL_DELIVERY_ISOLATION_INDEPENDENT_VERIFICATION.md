# Phase 134B.2 — External Delivery Isolation Independent Verification

## 1. Scope and Verification Philosophy

Phase 134B.1 reported a repair for an operator-notification flood: ordinary
pytest execution inherited live Telegram configuration from the invoking
shell. This phase does not trust that report. It independently re-derives,
from source and fresh adversarial probes, whether the repair holds at the
correct architectural boundary: **channel-agnostic external-delivery
authorization enforced before adapter selection**, not a Telegram-specific
patch that happens to work today.

No claim in this document rests on 134B.1's report, its documentation, its
tests, or variable/function naming. Every finding below is backed by a
source citation and/or a fresh, runnable test in
`tests/test_external_delivery_isolation_134b2_verification.py`.

## 2. Actual Repair Architecture (as it existed before this phase)

Source inspection of every file touched by 134B.1 plus the full notification
call graph found:

- `tests/conftest.py` — an autouse fixture (`_isolate_external_notifications`)
  that deletes five literal environment-variable names
  (`PCAE_NOTIFY_ENABLED`, `PCAE_NOTIFY_SINKS`, `PCAE_TELEGRAM_ENABLED`,
  `PCAE_TELEGRAM_BOT_TOKEN`, `PCAE_TELEGRAM_CHAT_ID`) before every ordinary
  test, unless `PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1` is set.
- `pcae.core.phase_reports.finalize_phase_report()` — reads
  `PCAE_NOTIFY_ENABLED`, then `PCAE_NOTIFY_SINKS`, then constructs concrete
  sinks via a hardcoded `if/elif` chain (`name == "telegram"` →
  `TelegramSink()`, etc.) — **not** an adapter registry.
- `pcae.commands.notifications.run_notify_send_report()` (the `pcae notify
  send-report` CLI, reachable via `python -m pcae notify send-report`) — a
  **second, independent** real dispatch call site. It constructs
  `TelegramSink()` directly and calls `dispatch()`, gated only by
  `TelegramSink.is_enabled()`'s own internal read of
  `PCAE_TELEGRAM_ENABLED`/token/chat-id. It never reads
  `PCAE_NOTIFY_ENABLED` or `PCAE_NOTIFY_SINKS` at all.
- `pcae.core.notifications.dispatch()` — the one function both call sites
  (and `run_notify_test`) share. Before this phase it performed **no**
  authorization check; it sent to whatever sinks it was given.

134B.1's own "Investigation Methodology" (§2 of its report) lists tracing
`finalize_phase_report()` sink construction, but does not mention
`run_notify_send_report()`'s independent, unconditional `TelegramSink()`
construction — despite that path being exercised by pre-existing tests
(`test_cli_send_report_with_latest`, `test_cli_send_report_json`) and being a
real, documented CLI command.

## 3. Core Architectural Challenge — Answers

1. **Is isolation enforced before adapter selection?** Only on one of two
   real call sites (`finalize_phase_report`). The other
   (`run_notify_send_report`) selected `TelegramSink` unconditionally with no
   prior authorization check of any kind.
2. **Does it govern a generic concept, or Telegram specifically?** Before
   repair: Telegram specifically, via five named variables and a hardcoded
   name chain. No generic "external delivery" concept existed in code.
3. **Could a future adapter bypass the repair without touching isolation
   code?** Yes, provably: a synthetic adapter added to the same
   `if/elif` construction pattern, using its own env-var names, would not be
   in the sanitizer's literal list. See `test_sanitizer_allowlist_is_
   enumerated_by_name_not_by_concept` and `test_future_adapter_is_blocked_by_
   dispatch_without_any_new_code` (documents the pre-repair gap and proves
   the post-repair fix).
4. **Would a new adapter require updating a hard-coded sanitization list?**
   Yes, before repair. After repair: no — see §5.
5. **Does ordinary test execution select an isolated transport, or merely
   make Telegram config unavailable?** Before repair: the latter only
   (Telegram config unavailable; no substitute recording/null transport is
   selected). This is a documented, non-blocking, cosmetic gap relative to
   the ideal invariant, since making config unavailable was, for the one
   existing adapter, behaviorally equivalent to blocking it.
6. **Is the real transport blocked even if credentials reach the process
   through an unanticipated mechanism?** No, before repair —
   `test_notify_send_report_now_honors_the_master_notify_switch` (originally
   written to fail — i.e. to demonstrate the bypass — and confirmed failing
   pre-repair) proves credentials introduced after the isolation fixture ran
   reached a live `TelegramSink().send()` attempt. Fixed by the `dispatch()`
   gate (§5).
7. **Is authorization centralized or duplicated?** Duplicated across two
   production call sites with non-overlapping conditions, before repair.
   Centralized into `dispatch()` after repair.
8. **Are message and document delivery both protected?** Yes — both are
   issued from within one `TelegramSink.send()` call gated by one
   `is_enabled()` check (`test_message_and_document_delivery_share_a_single_
   enabled_check`). This was already correct and unaffected by the repair.
9. **Are retries/fallback protected?** N/A — `TelegramSink.send()` contains
   no retry loop (confirmed by source inspection,
   `test_no_retry_loop_exists_to_escape_isolation`). The one fallback
   message sent on document-attachment failure reuses the same, already-
   authorized `_send_message` path — no separate escape.
10. **Can direct concrete-adapter use bypass the shared boundary?** A test
    author can always construct `TelegramSink(enabled=True, ...)` directly
    with explicit fake or real credentials — this is deliberate test
    authorship, not ordinary/accidental execution, and is outside supported
    architecture the same way calling `urllib.request.urlopen` directly
    would be. What matters is that **ordinary application call sites**
    cannot reach a live adapter without authorization — true after repair
    for both known call sites, and true by construction for any future one
    that goes through `dispatch()`.
11. **Can import-time/cached configuration retain live state?** No —
    `TelegramSink.__init__` reads `os.environ` fresh on every construction;
    no module-level cache exists (`test_telegram_sink_reads_environment_at_
    construction_not_import`).
12. **Can subprocesses reconstruct live configuration from another source?**
    Not tested as bypassing PCAE_NOTIFY_ENABLED specifically, but the
    sanitizer's protection is proven to be exactly as wide as its five
    literal names and no wider
    (`test_subprocess_env_construction_strips_known_names_only`). Because
    the `dispatch()` gate is transport-independent, a subprocess that
    somehow acquires unenumerated adapter credentials is still blocked at
    dispatch time unless `PCAE_NOTIFY_ENABLED` is also true.
13. **Is live-test authorization explicit and test-specific?** Explicit
    (`PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1`), but not fully independent of
    production enablement: the opt-in only suppresses env stripping: it does
    not itself set `PCAE_NOTIFY_ENABLED` or supply distinct test-only
    credentials. See §6 debt item.
14. **Is a dedicated test destination required for live integration?** Not
    enforced in code; relies on operator discipline. Documented as debt,
    §6.
15. **Is synthetic content visibly identified?** No explicit "SYNTHETIC" /
    "TEST" marker is injected into event titles by the isolation layer
    itself; 134B.1's incident evidence table shows synthetic titles were
    only distinguishable by the test authors' own naming convention.
    Non-blocking — no delivery occurs for synthetic content under ordinary
    isolated execution, so mislabeling risk is contained.
16. **Can synthetic deliveries become genuine terminal lifecycle records?**
    Tested directly: `test_synthetic_send_report_cannot_write_the_real_
    dispatch_marker` proves a synthetic `send-report` invocation, even
    combined with the Probe-3 unanticipated-credential scenario, does not
    write `.last-notified.json`. True both before and after repair (blocked
    upstream of the marker write either by `TelegramSink.is_enabled()`
    pre-repair or by the `dispatch()` gate post-repair).
17. **Does the repair protect future adapters without hard-coding every
    channel?** No, before repair. Yes, after repair — see §5.

## 4. Channel-Agnostic Invariant — Verdict

**Before this phase: not satisfied.** The isolation boundary was a literal,
enumerated environment-variable deny-list plus one call site's specific
`PCAE_NOTIFY_ENABLED` check; a second real call site had no boundary at all.

**After this phase's repair: satisfied.** `dispatch()` — the single function
every notification-sending code path uses — now requires
`PCAE_NOTIFY_ENABLED` to be truthy before invoking any sink that is not on an
explicit local/no-network allowlist (`NoopSink`, `StdoutSink`,
`FilesystemSink`, `MockSink`). A sink not on that allowlist is fail-closed by
default — including one that does not exist yet — so a future adapter
inherits protection automatically without any change to the allowlist, the
sink-construction chain, or the test sanitizer.

## 5. Repair Applied

**File:** `src/pcae/core/notifications.py`

Added `_LOCAL_SAFE_SINK_TYPES` (the four known no-network sinks) and
`_requires_external_delivery_authorization()` / `_external_delivery_
authorized()`, then modified `dispatch()` to check, per sink, whether it
requires authorization and — if so — whether `PCAE_NOTIFY_ENABLED` is
truthy, before calling `sink.send()`. An unauthorized sink yields a
`NotificationResult(success=False, error="external_delivery_not_
authorized")` instead of being invoked.

This is the smallest responsible boundary: one function, no new environment
variables, no changes to `finalize_phase_report()`'s existing (already
correct) gate, no changes to `run_notify_send_report()`'s call site (it is
now protected transitively through `dispatch()`), and no redesign of the
notification subsystem or Track 134's future Delivery Adapter architecture.

**Test file updated:** `tests/test_telegram_notifications.py` —
`test_telegram_sink_in_dispatcher` now sets `PCAE_NOTIFY_ENABLED=1`, since it
deliberately constructs and enables a `TelegramSink` for dispatcher-wiring
verification and must now also supply the master authorization the new gate
requires.

## 6. Remaining Technical Debt (transport-neutral)

1. **No durable per-attempt external-delivery receipt ledger.** Carried over
   from 134B.1, restated transport-neutrally: no component distinguishes
   logical delivery from physical per-adapter attempts durably across all
   sinks. Does not cause a delivery-escape defect (dispatch results are
   returned and stored on the report per-call); classified as future
   Track 134 debt (134D–134F), not repaired here.
2. **Live-integration opt-in is not independent of production enablement.**
   `PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1` only suppresses env stripping; if
   an operator has already sourced production Telegram config, that
   production config — not a separate test-specific credential/destination
   — is what a live test would use. Requires two deliberate operator
   actions (source production config, then explicitly opt in), so it is not
   an accidental-escape risk, but it does not meet the letter of "production
   delivery enablement alone is insufficient." Recommend, for a future
   phase: a distinct `PCAE_TEST_TELEGRAM_*` credential/destination set for
   live integration, independent of the operator's production variables.
3. **Synthetic payloads are not visibly marked as synthetic** at the
   isolation-layer level (only by test-author naming convention, per
   134B.1's incident table). No delivery occurs under ordinary isolated
   execution, so this is cosmetic, not a delivery-escape risk.
4. **No pytest marker (e.g. `@pytest.mark.live_notification`) scopes live
   integration tests for collection-time exclusion** — the opt-in is a
   single process-wide environment variable, so setting it affects every
   test in that run, not just an intended one. Mitigated by requiring
   deliberate operator action; recommend a dedicated marker in a future
   phase.

None of these four items caused or permitted an external-delivery escape
under ordinary/ungoverned test execution; none is classified BLOCKING.

## 7. Fresh Adversarial Probe Results

All ten probes live in
`tests/test_external_delivery_isolation_134b2_verification.py` and pass
against the repaired tree:

| Probe | Result |
|---|---|
| Generic external adapter (non-Telegram) | Blocked by `dispatch()` gate unless authorized; unaffected by sanitizer |
| Future-adapter registration | No sanitizer/registry update needed; automatic |
| Direct concrete-adapter bypass (`send-report`) | Closed — now requires `PCAE_NOTIFY_ENABLED` |
| Message/document protection | Confirmed shared gate, pre-existing and correct |
| Retry/fallback | No retry loop exists; fallback message reuses authorized path |
| Subprocess (known vs. unknown var) | Known vars stripped; unknown var passes through untouched (expected — protection is now at `dispatch()`, not the sanitizer) |
| Import/cache | No caching; fresh env read per construction |
| Production compatibility | `finalize_phase_report`'s existing gate unaffected; verified via control probe |
| Synthetic → genuine marker pollution | Proven impossible under the tested scenario, before and after repair |

## 8. Test Results

Focused (134B.1 regressions + telegram + phase_reports + new 134B.2 file):

```
207 passed in 0.90s
```

Related notification/gate/certification/permission-broker suites:

```
165 passed in 9.41s
```

`python -m compileall -q src`: passed, no errors.

Full fast-green suite:

```
python -m pytest -m "fast_green" -n auto -ra --durations=100
4389 passed, 1 failed in 69.36s
```

The one failure, `tests/test_dry_run_simulation.py::Test89dMatrixReadOnly::
test_pytest_dry_run_not_blocked`, is a pre-existing, environment-state-
dependent failure (requires an active governed task) reproduced identically
on the pre-134B.2 baseline commit (`ca81238a`) with no code changes applied.
It is unrelated to notification/external-delivery isolation and out of
134B.2's scope.

## 9. Production Compatibility

- `pcae phase complete` / `pcae task finish --commit` (via
  `finalize_phase_report`): unchanged — already required
  `PCAE_NOTIFY_ENABLED`, and the operator's real environment (confirmed via
  `pcae notify status`) already sets it alongside `PCAE_TELEGRAM_ENABLED`.
- `pcae notify send-report --latest`: now additionally requires
  `PCAE_NOTIFY_ENABLED=1`. This is a deliberate, minimal behavior change
  that closes the verified gap; it is not a regression for the operator's
  actual configuration, which already sets both variables together.
- `pcae notify test --sink {noop,stdout,filesystem,mock}`: unaffected — all
  four are on the local/no-network allowlist.
- PFN-001 (exactly-once logical completion): unaffected — the
  idempotency marker and certification logic were not touched.

## 10. Governance and Scope Confirmation

This phase did not begin 134C, did not implement Canonical Engineering
Evidence, Evidence Extraction, Derived Evidence Views, a generic Delivery
Adapter architecture, an Operator Report View, PFN-001 redesign, or a full
notification-subsystem redesign. The repair is a single, narrow, shared
authorization check inside one existing function.
