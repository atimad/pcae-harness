# Phase 128B.1 - Notification Dispatch Reliability Repair

## 1. Context

Phase 126G repaired canonical Telegram report *content fidelity*
(missing test/governance results, document-delivery staleness, silent
truncation). Phase 126G.1 repaired one remaining commit-trust-metadata
gap. Neither touched *whether* dispatch happens.

During Phase 128B, the canonical report was successfully generated and
independently confirmed trust-complete (`pcae phase-report trust`
reported `Status: complete`), but no Telegram notification was
received. This is a governance tooling repair only. It is not part of
Historical Memory, Repository Intelligence, or any runtime capability.

## 2. Root-Cause Analysis

### 2.1 The three dispatch-adjacent code paths

1. **`pcae phase complete`** (`src/pcae/commands/phase.py:48`
   `run_phase_complete` -> `_finalize_report_and_notify` at line 82) —
   the only entrypoint that was ever wired to dispatch. It:
   - builds a trial report and computes `dispatch_allowed =
     trust_result.complete`;
   - calls `certify_notification_transition()`
     (`src/pcae/core/notification_certification.py:93`) — the single
     shared authority for "should this NOTIFY transition be allowed",
     backed by the Repository Transition Validator's
     `TransitionKind.NOTIFY` invariant;
   - calls `finalize_phase_report()`
     (`src/pcae/core/phase_reports.py:1882`), which writes the report
     and, if `PCAE_NOTIFY_ENABLED` is truthy, builds sinks and calls
     `dispatch()` (`src/pcae/core/notifications.py:298`);
   - on a successful send, calls
     `write_notification_dispatch_marker()`
     (`src/pcae/core/phase_reports.py:714`) — the idempotency marker at
     `.pcae/phase-reports/.last-notified.json`.

2. **`pcae phase-report create`**
   (`src/pcae/commands/phase_reports.py`, `run_phase_report_create`)
   — the documented recovery command used when `pcae phase complete`
   is rejected by the repository transition validator (exactly what
   happened in 128B: stale `.pcae/phase-completion-metadata.json`
   still referencing phase `126E` triggered a
   `phase_identity_consistency` violation). Before this repair, this
   function called only `make_phase_report()`, `report.
   apply_trust_assessment()`, and `write_phase_report()` — it never
   called `certify_notification_transition()`, `dispatch()`, or
   `write_notification_dispatch_marker()` under any circumstances. The
   module's own docstring said so explicitly: *"No automatic hooks, no
   Telegram, no notification dispatch."* This is the confirmed root
   cause of the missing 128B notification: the report that actually
   got created and trusted was created entirely through a path with no
   dispatch wiring at all.

3. **`pcae notify send-report --latest`**
   (`src/pcae/commands/notifications.py`, `run_notify_send_report`) —
   a second, independent manual recovery command (named directly by
   the `phase-finalization` skill's own hint text as a fallback). It
   already had its own pre-existing 95M.1 finalization gate
   (`validate_finalization_gate`), but called `dispatch()` directly
   with **no idempotency check before sending and no marker write
   after** — an independent, pre-existing gap that matters for this
   repair because a repaired `phase-report create` and this command
   could otherwise both dispatch the same trusted report.

### 2.2 Why 126G/126G.1 did not already cover this

Both prior repairs' own "Compatibility Confirmation" sections confirm
they touched only `src/pcae/commands/phase_reports.py` (CLI argument
wiring for governance/test/commit/no-go fields) and
`src/pcae/core/notifications.py` (event/message formatting) — never
`finalize_phase_report()`, `dispatch()`, or the certification/marker
mechanism as consumed by `run_phase_report_create()`. The gap is
original to `run_phase_report_create()`'s design (a deliberately
dispatch-free manual command, per its own docstring), not a
regression introduced by either prior phase.

### 2.3 `phase-finalization` skill

`pcae skill invoke phase-finalization <id>` (`src/pcae/core/agent.py`)
previews target existence/type only. Its own returned
`notification_dispatch_note` states it explicitly: *"This command
previews target existence/type only. It never sends, gates, or
reflects Telegram dispatch."* Confirmed uninvolved in dispatch; not
modified by this repair.

### 2.4 Duplicate-prevention mechanism

`dispatch()` itself (`src/pcae/core/notifications.py:298`) has no
idempotency logic — it unconditionally sends to every sink given.
Idempotency lives one layer up: the shared marker file
`.pcae/phase-reports/.last-notified.json`
(`read_notification_dispatch_marker` /
`phase_already_notified(phase_id, commit_hash)` /
`write_notification_dispatch_marker(phase_id, commit_hash)`,
`src/pcae/core/phase_reports.py:672-726`), checked inside
`certify_notification_transition()`. Before this repair, only
`pcae phase complete`'s flow ever consulted or wrote it — neither
`pcae phase-report create` nor `pcae notify send-report --latest`
touched it at all.

## 3. Repair

Minimal, targeted, additive only. No architecture redesign, no report
format change, no report content change, no trust-assessment change,
no Repository Intelligence change, no Historical Memory change.

### 3.1 `run_phase_report_create()` (`src/pcae/commands/phase_reports.py`)

After the existing `write_phase_report()` call, a new helper
`_dispatch_manual_report_notification(report, paths)` is invoked:

- **Skips dispatch entirely** when `report.report_completeness !=
  "complete"` — an untrusted/partial report is never dispatched, same
  rule `pcae phase complete` already enforces.
- **Certifies** via the same shared
  `certify_notification_transition()` used by `pcae phase complete`,
  with `source_transition_kind=TransitionKind.REPORT_GENERATION`
  (a distinct, semantically accurate value from `COMPLETE_PHASE`;
  `source_transition` is recorded as payload metadata only and does
  not itself change the validator's gating logic — confirmed by
  reading `_check_notification_eligibility()` in
  `repository_transition_validator.py`, which branches only on
  `transition.kind != TransitionKind.NOTIFY`, never on the nested
  `source_transition` value).
- **Deliberately passes `metadata={}`** to certification rather than
  re-reading `.pcae/phase-completion-metadata.json` — this manual
  command exists specifically as a recovery path for when that file's
  stale content already caused `pcae phase complete` to be rejected;
  re-checking the same stale file here would simply reproduce the same
  rejection. The operator's explicit `--phase-id` (and the rest of the
  explicit CLI-supplied report fields) is the intended identity source
  for this path, exactly mirroring why this command exists at all.
  Push-cleanliness (`origin_main_head_count`), already-dispatched
  status, transport configuration, and the no-execution-availability
  invariant are still independently, honestly re-checked from real
  inputs.
- **Dispatches** using the same env-driven sink construction
  (`PCAE_NOTIFY_ENABLED`, `PCAE_NOTIFY_SINKS`, `PCAE_NOTIFY_OUTPUT_DIR`)
  and the same `phase_report_to_notification_event()` used by the
  primary path, so Telegram content is identical in shape.
- **Writes the shared idempotency marker** only after a fully
  successful dispatch, exactly mirroring
  `commands/phase.py`'s own `write_notification_dispatch_marker()`
  call site.
- **Reports outcome** (`sent` / `failed` / `skipped` /
  `already_dispatched` / certification-outcome value) in both the
  human-readable and `--json` command output, so a failure is always
  observable rather than silent.

### 3.2 `run_notify_send_report()` (`src/pcae/commands/notifications.py`)

Before dispatching, now checks `phase_already_notified(report.
phase_id, commit_hash)` against the same shared marker; if already
dispatched, prints/returns a clearly labeled idempotent-skip instead of
re-sending. After a fully successful dispatch, calls
`write_notification_dispatch_marker()`. The pre-existing 95M.1
finalization gate (`validate_finalization_gate`) is unchanged — this
repair only closes the idempotency gap, not the gate's own content
requirements.

### 3.3 What was explicitly not changed

- `finalize_phase_report()`, `dispatch()`, `TelegramSink`,
  `certify_notification_transition()`, and the marker file format are
  all unchanged.
- No report schema, report rendering, or trust-assessment logic
  changed.
- No Repository Intelligence (`src/pcae/repository_intelligence/**`),
  Dependency Knowledge Graph, or Historical Memory file changed.
- No runtime capability introduced; runtime remains `Observed`,
  `observe`, execution `unavailable`.

## 4. Dispatch Lifecycle Verification

Confirmed, both by direct source reading and by regression tests
(Section 5):

- Report write always precedes any dispatch attempt in both repaired
  paths (the report object and its written `paths` are the inputs to
  the notification helper, never the reverse).
- Dispatch is attempted only for a report already assessed
  `report_completeness == "complete"`.
- A dispatch failure never writes the idempotency marker, so a later
  retry (once the underlying transport issue is fixed) is not
  permanently blocked as "already sent".
- A disabled (`PCAE_NOTIFY_ENABLED` unset) run neither attempts
  dispatch nor writes the marker — matches `pcae phase complete`'s
  existing disabled-by-default behavior.

## 5. Regression Tests

Added `TestPhase128B1NotificationDispatchReliabilityRepair` in
`tests/test_phase_reports.py` (8 new tests, all passing):

- `test_untrusted_report_is_never_dispatched`
- `test_trusted_report_dispatches_exactly_once`
- `test_recovery_path_after_phase_complete_rejection_dispatches`
- `test_duplicate_dispatch_is_prevented`
- `test_dispatch_ordering_report_written_before_notification`
- `test_failed_dispatch_is_observable_and_not_marked_notified`
- `test_disabled_notify_env_skips_without_marking_notified`
- `test_notify_send_report_skips_duplicate_after_phase_report_create_dispatched`

All use `monkeypatch.chdir(tmp_path)` (the existing convention already
used by `test_notification_certification_idempotency.py` and
`test_finalization_notification_guarantee.py`) to isolate the shared
marker file and any lifecycle-file reads from the real repository
state, and `PCAE_NOTIFY_SINKS=noop` to exercise real dispatch mechanics
without a network call.

Full regression run: `tests/test_phase_reports.py`,
`tests/test_telegram_notifications.py`, `tests/test_notifications.py`,
`tests/test_notifications_cli.py`,
`tests/test_notification_certification_idempotency.py`,
`tests/test_finalization_notification_guarantee.py`,
`tests/test_task_finish_notification_ordering.py`,
`tests/test_task_finish_report_trust_notification.py`,
`tests/test_phase_113v_n_notification_finalization_repair.py` — 325
passed (317 pre-existing + 8 new), zero failures. `fast_green` — 4389
passed, 1 known pre-existing idle-state-dependent failure
(`test_dry_run_simulation.py::Test89dMatrixReadOnly::
test_pytest_dry_run_not_blocked`, which flips on active-task presence,
not code changes; re-verified clean with this phase's own active task
present).

## 6. Real Telegram Verification

Performed against the real repository with `PCAE_TELEGRAM_*` sourced
from `~/.config/pcae/telegram.env` and `PCAE_NOTIFY_ENABLED=1`,
`PCAE_NOTIFY_SINKS=telegram`:

- Ran `pcae phase-report create` with this phase's own governance/test/
  commit/no-go data (mirroring the exact 128B recovery scenario:
  explicit `--phase-id`, no reliance on
  `.pcae/phase-completion-metadata.json`).
- Confirmed `pcae phase-report trust` reported `Status: complete`
  before dispatch was attempted.
- Confirmed exactly one Telegram message was received, matching the
  canonical report's own content (governance results, test results,
  no-go confirmations, recommended next phase).
- Re-ran the identical command a second time and confirmed no second
  Telegram message was sent (`Notification dispatch: already_dispatched`).
- Confirmed the shared marker file
  `.pcae/phase-reports/.last-notified.json` was written with this
  phase's `phase_id` and commit prefix after the successful send.

## 7. Governance Compatibility

- observe-only runtime unchanged; execution remains unavailable
  (`pcae runtime inspect` re-confirmed);
- no schema, Repository Intelligence, Dependency Knowledge Graph, or
  Historical Memory file changed;
- no report format or report content change;
- governed lifecycle commands only — no raw `git commit`/`git push`,
  no force push, no `--no-verify`.

## 8. Recommended Next Phase

128C - Historical Memory Review & Hardening Contract Verification.
