# Phase 134B.1 — External Notification Investigation & Isolation Repair

## 1. Incident Summary

After Phase 134B finalization, the operator received substantially more
external notifications than the one logical phase completion should produce.
Investigation confirms an automated-test isolation defect: pytest was launched
from a shell that had sourced the production Telegram environment, and ordinary
in-process report tests inherited live notification enablement, sink selection,
bot token, and chat ID. Any test calling the real `finalize_phase_report()`
without locally overriding those variables could select the live Telegram
adapter.

The repair isolates external notification environment for every ordinary test
and inherited subprocess. Production notification behavior is unchanged.

## 2. Investigation Methodology

The investigation traced:

- `pcae task finish`, governed push post-push reconciliation, and `pcae phase
  complete`;
- identity resolution, report trust, transition validation, promotion, and
  notification certification;
- `finalize_phase_report()` environment resolution and sink construction;
- notification event construction, Telegram message and document calls,
  failure fallback, and dispatch marker behavior;
- CLI and subprocess environment inheritance;
- pytest configuration and notification/report/finalization tests;
- local notification event files, canonical reports, quarantine artifacts,
  and `.last-notified.json`.

No hypothesis was accepted without source or artifact evidence. Reproduction
used isolated/non-live execution; the investigation did not intentionally send
another external test notification.

## 3. Evidence Collected

### 3.1 Production completion path

The 134B governed push performed one accepted post-push completion transition,
one eligible notification dispatch, and wrote `.last-notified.json` for phase
`134B` and commit `a19e9740`. The following explicit `pcae phase complete`
observed `already_dispatched` and skipped. This confirms no duplicate logical
134B completion and no independent second production dispatch.

Telegram's adapter sends two physical channel artifacts for one logical
delivery: a `sendMessage` summary and a `sendDocument` full report. That is
intentional delivery completeness, not duplicate logical completion.

### 3.2 Synthetic activity during the incident window

Eight durable filesystem notification events were created between
20:35:58–20:36:30 UTC while the focused reporting suite ran. Their synthetic
titles/identities were:

| Title | Phase identity |
|---|---|
| Fresh Test | 92D.8.2 |
| NonFatal Test | 92D.4-t2 |
| Consistent Test | 92D.8.1 |
| Canonical Test | 92D.8 |
| Commit Test | 92D.8.1 |
| Mismatch Test | 92D.8.1 |
| Test Phase | 126G1-T |
| NonFatal Test | 92D.4-t2 |

Every artifact path points to pytest/temporary directories and every title is
defined by report tests, proving synthetic test activity was processed through
real production event construction.

These eight files are not a complete ledger of external Telegram attempts:
the filesystem sink records only executions selecting that sink, while the
Telegram sink persists no per-attempt local receipt. Therefore the exact number
of external messages cannot be reconstructed from repository evidence alone.
The external channel history is the only source capable of supplying that
count, and it was not provided to this session. Inventing a number would violate
the evidence standard. Repository evidence establishes **at least eight
synthetic notification events in the incident window**, plus one legitimate
134B logical delivery; it does not establish a complete external count.

### 3.3 Configuration and subprocess chain

`finalize_phase_report()` reads `PCAE_NOTIFY_ENABLED`, then reads
`PCAE_NOTIFY_SINKS`, and constructs `TelegramSink()` when `telegram` is present.
`TelegramSink` reads token, chat ID, and enabled state directly from the same
process environment. Pytest inherits the invoking shell environment. Python
subprocesses inherit it again unless a test supplies a replacement `env`.

No configuration cache exists in this chain. The problem is direct environment
inheritance, not caching.

### 3.4 Test behavior

Many tests call the real `finalize_phase_report()` while assuming notification
is disabled unless that test explicitly enables it. That assumption is false
when pytest starts after `source ~/.config/pcae/telegram.env`. A few tests
explicitly select `noop` or `filesystem`; those are isolated. Tests that do not
override the inherited variables can reach Telegram.

The broad suite also contains subprocess-based CLI tests. Before repair, child
processes inherited the live parent environment. This made per-test monkeypatch
discipline insufficient as a system-wide safety boundary.

### 3.5 Retry, replay, and receipts

- `TelegramSink.send()` contains no automatic retry loop.
- No repository evidence shows replay of the 134B logical delivery.
- The idempotency marker correctly prevented the explicit second completion
  path from dispatching.
- Test-generated phase identities are distinct and therefore legitimately
  bypass 134B's phase/commit idempotency key; they are separate synthetic
  logical events, not retries.
- Durable records accurately show the last genuine phase/commit dispatch but do
  not record every Telegram attempt. That receipt gap is existing Track 134
  debt, not expanded in this repair.

## 4. Verified Root Causes

### Primary: test/environment isolation defect

Ordinary pytest execution inherited live external delivery configuration.
There was no test-session boundary clearing live notification enablement,
adapter selection, credentials, and destination. Real production notification
functions therefore behaved correctly for the environment they received but
were invoked by synthetic tests against the operator channel.

### Contributing: subprocess isolation defect

CLI subprocesses inherit the parent's environment by default. Without a
test-wide parent isolation boundary, every child begins with live configuration
even when its test is not intended as live integration.

### Contributing observability limitation

The repository has one last-notified marker and selected filesystem events, but
no durable per-attempt Telegram receipt ledger. It cannot reconstruct the exact
external count after the fact. This did not cause dispatch, but limited incident
accounting.

### Explicitly not causes

- no duplicate logical 134B completion;
- no Telegram automatic retry;
- no notification replay;
- no configuration cache;
- no second independent production finalization mechanism;
- no PFN-001 defect;
- no report-promotion/notification decoupling in the accepted 134B path.

## 5. Minimal Implementation Repair

`tests/conftest.py` now applies an autouse external-notification isolation
fixture. Unless explicitly opted in, it removes:

- `PCAE_NOTIFY_ENABLED`;
- `PCAE_NOTIFY_SINKS`;
- `PCAE_TELEGRAM_ENABLED`;
- `PCAE_TELEGRAM_BOT_TOKEN`;
- `PCAE_TELEGRAM_CHAT_ID`.

The boundary runs before every ordinary test. In-process production calls see
notifications disabled, and subprocesses inherit the already-isolated parent
environment. Individual tests remain free to configure noop/filesystem or fake
Telegram values after the fixture runs.

Governed live integration testing remains possible only through the deliberate
`PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1` opt-in. This makes live delivery an
explicit test authorization rather than an ambient shell accident.

No production source, sink selection, adapter, orchestration, PFN-001 rule,
idempotency behavior, or lifecycle behavior changed.

## 6. Focused Regression Coverage

`tests/test_external_notification_isolation_134b1.py` verifies:

- ordinary tests contain no live notification configuration;
- child processes inherit isolation rather than operator credentials;
- a fully populated pre-existing live environment is removed;
- explicit governed live-integration opt-in preserves configuration.

Running the new tests plus `tests/test_phase_reports.py` from a shell with the
real Telegram environment sourced passed 150/150. The local notification file
count increased by one only because an existing test deliberately selects the
filesystem sink; no test retained the live Telegram variables.

## 7. Compatibility Assessment

- **Production notification:** unchanged; governed commands outside pytest read
  the same environment and deliver exactly as before.
- **PFN-001:** preserved; genuine terminal completion still requires exactly
  one trusted logical delivery or durable failure.
- **Exactly-once logical completion:** preserved; marker/certification logic is
  untouched.
- **Explicit live testing:** preserved behind named opt-in.
- **Future Track 134:** compatible with transport-independent adapters and
  future receipt work; no lifecycle architecture was implemented early.
- **Runtime:** remains Observed, maximum capability observe, execution
  unavailable.

## 8. Remaining Technical Debt

- A durable per-attempt delivery receipt ledger is still required to reconstruct
  exact external delivery counts; this belongs to 134D–134F.
- The filesystem sink's default repository-local output means tests that
  intentionally select it may leave ignored diagnostic files. This is not an
  external-delivery risk and is not repaired here.
- Existing tests use mixed manual environment restoration and monkeypatch
  styles. The autouse boundary contains the external risk; stylistic
  consolidation is unrelated work.
- Physical message-plus-document delivery remains two channel artifacts for one
  logical report, by design.

## 9. Governance and Scope Confirmation

This repair changes only pytest isolation and focused tests. It does not begin
134C, redesign notification/PFN-001, implement Canonical Engineering Evidence,
Operator Report View, or Track 134 lifecycle architecture, modify Repository
Intelligence, or introduce execution capability.

## 10. Recommended Next Phase

**134C — Canonical Phase Finalization & Reporting Lifecycle Contract
Verification.** No 134C work began in this repair phase.
