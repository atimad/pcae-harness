# Phase 105C — Task Finish Report Trust / Telegram Notification Integration

## Purpose

Close the lifecycle mismatch discovered after 105B: `pcae phase complete`
creates rich phase-completion reports and dispatches outbound Telegram
notifications (via `finalize_phase_report()`), but the project's actual
day-to-day phase-closing convention — `pcae commit implementation` followed
by `pcae task finish --commit` — never calls that code path. As a result,
no report was ever created and no Telegram message was ever sent when
phases were closed the way they actually are closed in practice. 105C makes
`pcae task finish --commit` do this automatically.

## Scope

- When `pcae task finish --commit` runs and `.pcae/phase-completion-metadata.json`
  exists, automatically finalize the phase-completion report, run the
  105A/105B report-trust validator against it, and dispatch outbound
  notifications when configured.
- Surface trust/notification/repair status in both human and JSON
  `pcae task finish` output.
- Add a simple idempotency guard so the same phase/commit isn't
  double-dispatched.

## Non-goals

105C does not implement runtime enforcement, execution, backend invocation,
adapter execution, shell mediation, Telegram inbound/polling, rollback
execution, or apply/commit/push authorization beyond what `pcae task finish
--commit` already governs. It does not add an execution enablement flag or
toggle. It does not make trust failures block task completion — that is
explicitly deferred to 105D. All authorization flags remain False;
`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`, and
`design_only` remain True where applicable.

## Relationship to 105A / 105B

- 105A (`core/phase_report_trust.py`): pure `validate_phase_report_trust()` /
  `select_active_phase_report()` — unchanged.
- 105B (`commands/phase_reports.py`, `cli.py`): `pcae phase-report trust`,
  `show --trust`, and a warning-only advisory line inside `pcae phase
  complete`'s existing 95M.1 gate flow — unchanged.
- 105C reuses both directly: it calls `finalize_phase_report()` (the same
  function `pcae phase complete` uses) to build/write the report, then runs
  the *same* `validate_phase_report_trust()` (via
  `adapt_report_for_trust_check()`) against the resulting report — so `pcae
  task finish --commit` and `pcae phase complete` agree on what "complete"
  means, by construction, not by convention.

## Root cause of missed automatic Telegram dispatch

`finalize_phase_report()` — the only function that builds a report with
governance/test results *and* dispatches notifications — is called from
exactly one place: `commands/phase.py::run_phase_complete` (`pcae phase
complete`). Every phase closure in this repository's actual history (104x,
105A, 105B) instead used `pcae commit implementation` + `pcae task finish
--commit`, which only moves the task contract file and creates a git commit
— it never touched `finalize_phase_report()`. So the Telegram pipeline was
correct and working (confirmed by a manual `pcae notify send-report
--latest` after 105B), but nothing in the actual workflow ever called it.

## Current lifecycle flow (before 105C)

```
pcae commit implementation --path ... --message "..."   (git commit only)
pcae task finish --staged-file-aware --commit "..."      (moves task file,
                                                            commits, done —
                                                            no report, no
                                                            notification)
```

```
pcae phase complete --summary "..."   (releases agent lock, records
                                        phase_completed provenance,
                                        finalize_phase_report(): builds
                                        report, runs 95M.1 gate, advisory
                                        105B trust line, dispatches
                                        Telegram if configured)
```

These are two independent, non-overlapping code paths. `pcae phase complete`
was never removed or changed by 105C — see "pcae phase complete
relationship" below.

## New task-finish integration behavior

`run_task_finish()` (`commands/task.py`), when invoked with `--commit`, now
calls `_finalize_task_report_and_notify(commit_hash)` after the commit
succeeds:

1. Read `.pcae/phase-completion-metadata.json`. If absent → print
   `Report finalization: skipped (no .pcae/phase-completion-metadata.json
   found ...)` and return normally (task finish is never blocked or crashed
   by a missing/invalid metadata file — malformed JSON produces the same
   kind of clear skip message).
2. Extract governance results, test results, files/tests counts, commits,
   push state, no-go confirmations, and recommended next phase from the
   metadata — the same extraction logic `pcae phase complete` uses,
   independently implemented here since task finish has no `--summary`
   argument to derive `phase_id`/`phase_name` from (metadata must carry
   `phase_id` and, ideally, `summary`; when `summary` is absent, a plain
   `"Phase {phase_id} completed via pcae task finish."` placeholder is used
   — this is intentionally a generic filler, not fabricated content).
3. Call `finalize_phase_report()` (unchanged, shared with `pcae phase
   complete`) to build and write the report.
4. Validate the **written report** (not the raw metadata) with
   `validate_phase_report_trust()` — the raw metadata is often, by design,
   missing fields like `commits` (only derived at finalize time from the
   git commit hash), so validating it directly would misreport a good
   report as invalid.
5. Dispatch notifications exactly as `finalize_phase_report()` already does
   (env-gated: `PCAE_NOTIFY_ENABLED`, `PCAE_NOTIFY_SINKS`).

## Trust validation behavior

Trust status is always computed and surfaced when metadata exists,
regardless of whether notifications are configured — `Report trust:
complete|partial|invalid` and `Repair required: yes|no` are printed
unconditionally. This mirrors 105B's advisory line in `pcae phase complete`
and uses the identical validator.

## Notification dispatch behavior

- `PCAE_NOTIFY_ENABLED` unset/falsy → `Report notification: skipped`,
  reason `PCAE_NOTIFY_ENABLED is not set to 1/true/yes`.
- Enabled but no sink configured/succeeds → `Report notification: skipped`
  (reason: sinks not fully configured) or `failed` (a sink was attempted
  and did not succeed) as appropriate — task finish's own exit code and
  completion are never affected either way.
- Enabled and configured (e.g. `PCAE_NOTIFY_SINKS=telegram` with Telegram
  env vars present) → `Report notification: sent`, same summary+document
  dispatch as `pcae notify send-report --latest`.

## Telegram outbound-only boundary

`Telegram: outbound-only` is printed unconditionally alongside the
notification line. No inbound handling, polling, or command processing is
implemented or reachable from this integration — dispatch goes through the
existing `TelegramSink.send()` path only (`sendMessage` + `sendDocument`),
unchanged from 105B/92B.

## Warning-only vs hard-fail

105C is warning-only, matching 105B: a `partial`/`invalid` trust result
never blocks `pcae task finish --commit` (exit code 0), never auto-repairs
the report, and never silently upgrades a partial report to complete.
Hard-fail enforcement (making an incomplete report block finalization) is
explicitly deferred to **105D**.

## Idempotency / duplicate-send behavior

`PhaseReport.notification_result` is **not** a reliable duplicate-send
signal: `finalize_phase_report()` writes the report artifact to disk
*before* attempting dispatch, so the persisted `latest.json` never reflects
the actual dispatch outcome (a pre-existing characteristic of that function,
unrelated to 105C, left as-is since fixing it is out of this phase's scope).
Instead, 105C writes a small dedicated marker,
`.pcae/phase-reports/.last-notified.json` (`{"phase_id", "commit"}`), only
after a *successful* dispatch. Before dispatching, if the marker's
`phase_id` and `commit` (prefix-tolerant) match the current finalization,
the send is skipped with `status: "skipped_duplicate"` and the trust result
is still reported (computed from the existing written report). This is a
best-effort guard for the realistic duplicate scenario — running both `pcae
phase complete` and `pcae task finish --commit` for the same metadata — not
a durable notification ledger; it is intentionally small per the phase's
"do not overbuild" guidance.

## `pcae phase complete` relationship

Unchanged. `pcae phase complete` remains available as a lower-level,
manual finalization command (it additionally releases the agent lock and
records `phase_completed` provenance, which `pcae task finish` does not do).
**`pcae task finish --commit` is now the preferred, self-sufficient
phase-closing workflow** for day-to-day use; `pcae phase complete` remains
useful for manual/ad hoc report finalization or resending, and both paths
share the exact same `finalize_phase_report()` and
`validate_phase_report_trust()` calls, so they cannot disagree on trust
status.

## CLI / task finish UX

Human output (only when `--commit` was used) adds, after existing task
finish output:

```
Report trust: complete
Repair required: no
Report notification: sent
Telegram: outbound-only
```

JSON output (`--json`) adds: `report_trust` (the full
`PhaseReportTrustResult.to_dict()`), `repair_required`, `notification_dispatch`
(`status`, `reason`, `sinks`), `telegram_runtime` (`"outbound-only"`),
`report_path`, `metadata_path`. All existing JSON fields are unchanged and
tested (see `tests/test_task.py`).

## No-execution guards

`_finalize_task_report_and_notify()` contains no `subprocess`, `os.system`,
direct network calls (`requests.`/`urllib`/`socket.`), or Telegram
inbound/polling code. The only network path reachable from it is the
pre-existing `TelegramSink.send()` outbound call, gated by
`PCAE_NOTIFY_ENABLED`/`PCAE_NOTIFY_SINKS`. `pcae task finish --commit`'s
existing git operations (add/commit) are unchanged and pre-existing.

## Residual risks

1. `finalize_phase_report()` writes the report before dispatch, so
   `PhaseReport.notification_result` on disk is always stale/empty — 105C
   works around this with its own marker file rather than fixing the
   underlying function, to avoid touching shared, already-tested code
   outside this phase's scope.
2. `.pcae/phase-completion-metadata.json` has no `status`/`summary` fields
   in most historical phases (those were always supplied via `pcae phase
   complete --summary`); task finish now defaults `status="completed"` and
   a generic `summary` placeholder when absent. Authors should start
   including `summary` directly in the metadata file for higher-fidelity
   reports going forward.
3. The idempotency marker is a single-slot file (last dispatch only), not a
   history; a second, unrelated phase's dispatch overwrites it. This is
   sufficient for the realistic same-phase duplicate case this phase
   targets, not a general notification ledger.
4. Hard-fail finalization (blocking `pcae task finish --commit` on an
   incomplete report) remains deferred to 105D, per phase intent.

## Recommended next phase

105D — Phase Report Trust Gate Hard-Fail / Push-Check Integration. Should
decide whether/how incomplete reports become lifecycle-blocking in
finalization and push-check paths, now that both `pcae phase complete` and
`pcae task finish --commit` produce trust-validated reports consistently.
