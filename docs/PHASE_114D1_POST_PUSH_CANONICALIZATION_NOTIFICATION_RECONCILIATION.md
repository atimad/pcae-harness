# Phase 114D.1 — Post-Push Canonicalization & Notification Reconciliation

## Status

Completed.

## Origin

Phase 114D's own `pcae agent verify-handoff`, run immediately after 114D's
governed push, correctly reported **FAIL**: `.pcae/phase-completion-
metadata.json` declared `phase_id: 114D`, but the canonical report
(`.pcae/phase-reports/latest.json`) was still `114A`. The repository was
genuinely clean and pushed (`origin/main..HEAD` = 0) -- canonical
promotion simply never reran after the push that made it so.

Root cause: `pcae task finish --commit` always creates its own closure
commit (moving the task to `tasks/done/`, updating `tasks/DONE.md`) as
part of finishing. Finalization is evaluated *inside* that same command
invocation, at which point the just-created closure commit is inherently
one commit ahead of `origin/main` -- so the Repository Transition
Validator correctly quarantines it (113X/114C behavior, unchanged and
still correct: it must not promote an unpushed transition). Nothing,
until this phase, ever re-evaluated finalization *after* the follow-up
`pcae push` actually landed.

## Post-Push Reconciliation Behavior

`pcae push` (`src/pcae/commands/push.py`) now calls
`_reconcile_post_push(root)` in two places: after a real push succeeds,
and when readiness reports `nothing_to_push` (the repository was already
clean and pushed -- e.g. a second `pcae push` invocation, or the exact
scenario 114D's `verify-handoff` caught). Never on `--dry-run`.

`_reconcile_post_push` asks two pure, read-only questions from the new
`src/pcae/core/post_push_canonicalization.py`:

1. `reconciliation_pending(root)` -- does declared
   `.pcae/phase-completion-metadata.json` name a phase whose `phase_id`
   disagrees with (or is entirely absent from) the canonical report? If
   not, this returns immediately (`"not_pending"`), printing nothing --
   the common case, so `pcae push` stays quiet when there is nothing to
   reconcile.
2. `live_push_is_clean(root)` -- is the working tree clean *and* does
   Phase 114C's `compute_live_push_state()` confirm
   `origin/main..HEAD == 0`? If either is false, reconciliation is
   skipped and reported as such -- canonicalization never runs ahead of
   what has actually reached `origin/main` (Objective 6).

When both are satisfied, `pcae push` calls the existing
`_finalize_report_and_notify(...)` (`src/pcae/commands/phase.py`) --
the same function `pcae phase complete` uses, already carrying Phase
114C's live push-state reconciliation and Phase 114B's notification
certification/idempotency. **Nothing new was implemented for promotion or
dispatch decisions** -- this phase only decides *when* to re-invoke
finalization that already existed.

## Canonical Report Promotion

Because `_finalize_report_and_notify` is reused unmodified, promotion
behaves exactly as it does for `pcae phase complete`: a trial report is
built from `.pcae/phase-completion-metadata.json`, validated by the
Repository Transition Validator, and -- on ACCEPT -- `latest.json` /
`latest.md` are updated via Phase 114A's `promote_artifact(...)`. A stale
canonical report pointing at an old phase is overwritten with the correct
one.

## Notification Dispatch

Also inherited unmodified from `_finalize_report_and_notify`: if Telegram
is configured and enabled (`PCAE_NOTIFY_ENABLED=1`) and
`certify_notification_transition(...)` finds the reconciled state
eligible (certified, canonical, push-clean, not already dispatched), the
final notification dispatches. The Phase 113V.N marker file
(`.pcae/phase-reports/.last-notified.json`) is written only after a
successful dispatch, exactly as before.

## Idempotency

Re-running reconciliation (e.g. calling `pcae push` again immediately
after) is a no-op by construction, not by a new tracking flag:
`reconciliation_pending(...)` compares the canonical report's `phase_id`
against declared metadata directly. Once promotion succeeds, they agree,
and every subsequent call returns `not_pending` -- silently. Notification
idempotency is unchanged 113V.N/114B behavior: the dispatch marker,
written only on success, prevents a duplicate send regardless of how many
times reconciliation itself runs.

## Handoff Verification After Reconciliation

Once canonicalization completes, `pcae agent verify-handoff`'s
`report_metadata_phase_match` check (Phase 114D) passes -- the failure
this phase exists to fix. Any remaining output (e.g. a working tree
containing the newly-written, gitignored `.pcae/phase-reports/` artifacts,
or a `notification_marker`/`push_reconciliation` warning) is either
untracked (real repository convention: `.pcae/phase-reports/` is
gitignored) or an already-documented non-blocking warning -- not a new
failure class.

## Compatibility Boundaries

This phase does not modify:

- the Repository Transition Validator
- Notification Certification's eligibility logic
- Canonical Artifact Promotion
- `push_state_reconciliation.py` (114C) -- only imported and reused
- `_finalize_report_and_notify` itself (`pcae phase complete`'s own
  finalization function) -- only invoked, not changed
- notification sinks or dispatch
- Permission Broker
- execution runtime, authorization, plugins
- Telegram inbound, REST, Web UI, Dashboard

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused post-push reconciliation tests: see final report
- phase/report/push-state/notification tests: see final report
- governance/autonomy tests: see final report
- release/lifecycle regression: see final report
- fast_green: see final report
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: see final report
- `pcae agent verify-handoff --json`: see final report
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env

## Recommended Next Phase

114E — Model Containment Drill
