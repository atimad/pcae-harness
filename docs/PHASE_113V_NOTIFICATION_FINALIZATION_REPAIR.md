# Phase 113V.N — Phase Finalization Notification Repair

## Purpose

Governance/notification repair phase. 113S/113T/113U/113V each documented
the same observed symptom without repairing it: `pcae skill invoke
phase-finalization <phase-id>` returned `blocked`/`target_unresolved` for
a completed, trusted, pushed phase, and no Telegram final report appeared
to follow. This phase performs the forensic investigation the prior
phases deferred, identifies the two real (and different) defects behind
that symptom, and repairs both.

No Repository Transition Validator integration (113W is explicitly out of
scope). No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime
Registry, Runtime Inspect, or Permission Broker changes. No execution,
authorization, plugin, Telegram-inbound, REST, Web UI, or Dashboard
changes. Execution capability remains unavailable.

## Forensic Findings

**Finding 1 — `pcae skill invoke phase-finalization <phase-id>` is not
part of the real notification path at all.** It is Phase 64B.5's generic
"Skill Invocation Targeting" preview (`build_skill_invocation_targeting()`
in `src/pcae/core/agent.py`) — a read-only tool that answers "does this
target exist and what type is it," shared across every skill
(`phase-implementation`, `phase-validation`, `capability-analysis`, ...).
It never imports `notifications.py`, never constructs a `TelegramSink`,
and never reads `PCAE_NOTIFY_ENABLED`. The actual dispatch path is
`finalize_phase_report()` (`core/phase_reports.py`), called from `pcae
phase complete` and `pcae task finish --commit`.

**Finding 2 — the frozen roadmap registry, not "special" phase-ID
shapes, is why resolution failed.** `_sit_resolve_phase_target()`
resolved phase targets by exact match against `_CRI_KNOWN_PHASES`, a
hard-coded tuple last extended around Phase 69P/64B.6E (76 entries).
Confirmed live: **`pcae skill invoke phase-finalization 113D`** — an
entirely ordinary, non-"special" phase ID — returned the identical
`target_type_unresolved` failure as `113T`/`113U`/`113V`. The registry
fails *every* phase after ~69P, regardless of ID shape; "special" IDs
were never the actual variable.

**Finding 3 (the real functional gap) — `pcae phase complete` had no
notification-dispatch idempotency guard.** `pcae task finish --commit`
(`src/pcae/commands/task.py`) already carried a private marker-file
workaround (`.pcae/phase-reports/.last-notified.json`), with an explicit
comment recording *why*: `finalize_phase_report()` writes the report
artifact before attempting dispatch, so `PhaseReport.notification_result`
can never itself answer "was this already sent" at the moment dispatch
is being decided. `pcae phase complete` — the authoritative finalization
path — never had this guard. Re-running it for the same phase_id +
commit could dispatch a duplicate Telegram final report. This is the one
concrete "asymmetry" the two prior phases' own titles ("notification
asymmetry") pointed at without naming precisely.

**Confirmed NOT a defect:** the trust/eligibility gate itself
(`validate_finalization_gate()` + `compute_final_trust()`) already
correctly handles arbitrary phase-ID strings — it derives identity from
`.pcae/phase-completion-metadata.json`, never from a fixed registry — and
`finalize_phase_report()` already reports a clear, specific skip reason
("PCAE_NOTIFY_ENABLED is not set to 1/true/yes") whenever notifications
are disabled. Whether 113T/113U/113V actually had `PCAE_NOTIFY_ENABLED=1`
set at completion time cannot be reconstructed retroactively; what is
certain is that the skill-invoke symptom those phases observed was
*never causally connected* to real dispatch, which is itself the
confusion this phase closes.

## Repair Summary

**Target resolution (`src/pcae/core/agent.py`).** `_sit_resolve_phase_target()`
and `_sit_infer_target_type()` now fall back, when a phase ID is not in
the frozen roadmap registry, to live repository state: the canonical
`latest.json` report, any historical timestamped report, a quarantined
report, in-flight `.pcae/phase-completion-metadata.json`, and
PROJECT_STATUS.md's "Current Phase" line — the same sources the real
finalization path already treats as authoritative. A new phase-ID
grammar (`_SIT_PHASE_ID_GRAMMAR_RE`,
`^\d+[A-Za-z]*(?:\.\d+)*(?:\.[A-Za-z]+)?$`) classifies any
phase-shaped ID as `target_type=phase` even when nothing resolves it, so
the resulting signal is a specific `target_unresolved` ("not found in the
roadmap registry, phase reports archive, phase-completion metadata, or
PROJECT_STATUS.md's current phase") rather than a generic
`target_type_unresolved`. A syntactically invalid ID (one that does not
match the grammar at all, reachable via explicit `--target-type phase`)
is reported as `invalid_phase_id_form` — a distinct signal, because the
remedy differs ("fix the ID's shape" vs. "check whether the phase
exists"). The result's `notification_dispatch_note` field (populated only
for `invoke_skill_id="phase-finalization"`) states explicitly that this
command previews target existence only and never gates or reflects
Telegram dispatch, pointing at `pcae notify status` / `pcae phase
complete` / `pcae notify send-report --latest` instead.

**Notification-dispatch idempotency (`src/pcae/core/phase_reports.py`,
`src/pcae/commands/phase.py`, `src/pcae/commands/task.py`).** The
marker-file logic `pcae task finish --commit` already had is generalized
into three shared functions: `read_notification_dispatch_marker()`,
`phase_already_notified(phase_id, commit_hash)`, and
`write_notification_dispatch_marker(phase_id, commit_hash)`. `task.py`'s
`_finalize_task_report_and_notify()` is refactored to call these instead
of its private inline copy (behavior unchanged). `pcae phase complete`'s
`_finalize_report_and_notify()` gains the same guard it previously
lacked: before dispatch it checks `phase_already_notified(phase_id,
commit)`; if true, `PCAE_NOTIFY_ENABLED` is transparently suppressed for
that call only, the report is still written normally, and the printed
outcome reads `Notification dispatch: skipped (idempotent — already
dispatched)` with an explicit reason naming the phase and commit — never
the generic "not enabled" message, so idempotent skips are never
confused with disabled notifications. After a real send succeeds, the
marker is written. A genuinely new commit for the same phase_id (e.g. a
report-repair follow-up) is correctly treated as not-yet-dispatched and
is still sent.

## Supported Phase ID Grammar

| Form | Example | Supported |
|---|---|---|
| Digits + optional letter branch | `113D` | Yes |
| Digits + multi-letter suffix | `113XR` | Yes |
| Dotted numeric sub-phase | `113X.2` | Yes |
| Dotted single-letter repair suffix | `113D.R`, `113V.N` | Yes |
| Anything not matching the above | `"not-a-phase!!"` | No — reported as `invalid_phase_id_form`, not silently accepted or conflated with "not found" |

Matching the grammar means the ID is recognized as phase-shaped; it does
not by itself mean the phase exists. A grammar-valid ID with no matching
report/metadata/PROJECT_STATUS.md entry still resolves as
`target_unresolved`, with a reason naming every source checked.

## Notification Eligibility Summary

Unchanged from the pre-existing (and already-correct) model, confirmed by
this phase's forensic review and regression tests:

- eligibility requires report trust completeness, clean push state
  (`origin/main..HEAD == 0`), and Telegram configured + enabled + ready
- a partial/incomplete report is never sent as a normal "Phase COMPLETED"
  notification (Phase 105D/113X.3); it either gets a clearly labeled
  WARNING event or is skipped with a specific reason
- a gate-blocked (quarantined) report is never eligible for any
  notification
- disabled notifications (`PCAE_NOTIFY_ENABLED` unset) are reported with
  that exact, specific reason — never as `target_unresolved` or any other
  unrelated failure mode

## Idempotency Summary

- shared marker: `.pcae/phase-reports/.last-notified.json`, `{phase_id,
  commit}` (8-char commit prefix)
- matched with a bidirectional commit-prefix comparison, mirroring the
  pre-existing `pcae task finish --commit` behavior this generalizes
- `pcae phase complete` and `pcae task finish --commit` both consult and
  update the same marker — the asymmetry (one path guarded, one not) is
  closed
- `pcae notify send-report --latest` (the fully manual resend command) is
  deliberately left unguarded: the phase-finalization skill's own
  documented workflow explicitly calls for resending Telegram after a
  report repair, which is a legitimate, human-invoked, intentional
  duplicate-in-appearance send, not an accidental one

## Tests

New: `tests/test_phase_113v_n_notification_finalization_repair.py` (18
tests) — normal/multi-letter/dotted/repair-suffix phase resolution via
live report lookup, quarantine-only phases resolving as `blocked` (not a
clean target), grammar-invalid IDs rejected distinctly from
not-found IDs, the `notification_dispatch_note` clarification, the
read-only preview's absence of dispatch side effects, the shared marker
helpers' round-trip and non-matching-commit behavior, and end-to-end
`pcae phase complete` idempotency (first call sends, second call for the
same phase+commit is a no-op with an explicit reason, a new commit for
the same phase still sends, and a missing `PCAE_NOTIFY_ENABLED` is
reported accurately and never as `target_unresolved`).

Unchanged and re-run clean: `tests/test_phase_reports.py`,
`tests/test_notifications.py`, `tests/test_telegram_notifications.py`,
`tests/test_phase.py`, `tests/test_task.py`,
`tests/test_task_finish_notification_ordering.py`,
`tests/test_task_finish_report_trust_notification.py`,
`tests/test_phase_report_trust_gate.py`,
`tests/test_phase_report_trust_gate_cli.py`,
`tests/test_phase_report_trust_hard_fail.py`,
`tests/test_phase_reports_cli.py`, and the full `test_agent.py`
skill-targeting suite.

## Remaining Limitations

- `_CRI_KNOWN_PHASES` itself is not extended or replaced; the live
  fallback added here means later phases no longer *need* it to resolve,
  but the registry's own track/predecessor/successor metadata is still
  frozen at ~69P for the callers that use it for that richer context
  (e.g. `build_prompt_rendering_skill()`'s phase-implementation prompt
  quality checks) — untouched here as out of scope for a notification
  repair.
- The idempotency marker is a single global file, not one per phase — by
  design (mirrors the pre-existing `task.py` behavior exactly), since
  only the single most recent phase+commit pair is ever relevant to "was
  this exact finalization already sent."
- `pcae notify send-report --latest` remains unguarded by design (see
  Idempotency Summary); an operator who runs it twice in a row for the
  same unchanged report will get two Telegram sends. This preserves the
  documented repair-resend workflow rather than silently blocking it.
- Whether 113T/113U/113V themselves actually had `PCAE_NOTIFY_ENABLED=1`
  set at completion time is not reconstructable from repository state
  alone; this phase repairs the mechanism and the false signal, not those
  phases' historical completion runs.

## Recommended Next Phase

113W — Repository Transition Validator Integration Design
