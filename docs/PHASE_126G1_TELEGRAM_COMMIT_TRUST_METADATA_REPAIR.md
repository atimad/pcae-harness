# Phase 126G.1 - Telegram Commit Trust Metadata Repair

## Status

Complete.

## Purpose

Phase 126G restored canonical Telegram report delivery (governance
results, test results, no-go confirmations, and summary all now
propagate correctly). One trust warning remained on every report
produced through `pcae phase-report create`, regardless of how many
commits were supplied:

```
## Missing Trust Fields

- ⚠️ commits.phase_owned not verified — no phase_commits in metadata
```

This phase traces the complete commit metadata lifecycle and repairs
only this remaining gap. It is not part of Historical Memory,
Repository Intelligence, Dependency Knowledge Graph, or execution
planning. No schema file was touched.

## Commit Metadata Lifecycle Trace

Traced end to end, as required:

1. **Phase finalization** — an operator (or the internal `finalize_
   phase_report()` pipeline) supplies commit hashes for the phase.
2. **Phase metadata generation** — `pcae phase-report create` builds a
   `PhaseReport` via `make_phase_report()`, which already accepted
   `commits` as a flat list (`report.commits`) — confirmed working
   correctly since 126G.
3. **Phase report generation** — `write_phase_report()` persists the
   report, including whatever is in `report.metadata` (a *separate*
   free-form dict field from `report.commits`).
4. **Report trust validation** — `PhaseReport.assess_completeness()`
   (`src/pcae/core/phase_reports.py:206-210`) runs a dedicated
   commit-ownership check: when `self.commits` is non-empty and
   `self.files_changed > 0`, it requires `self.metadata.get(
   "phase_commits")` **or** `self.metadata.get("commit_attribution")`
   to be truthy, or it appends the `"commits.phase_owned not
   verified"` warning to `trust_warnings`.
5. **Notification event creation** — `phase_report_to_notification_
   event()` (126G) already forwards `report.trust_warnings` and
   `report.commits` into event metadata unchanged.
6. **Telegram dispatch** — `TelegramSink` renders whatever the report
   carries; unaffected by this phase.

## Root Cause

Step 4 is where the gap lives, but the actual defect is one step
earlier: `run_phase_report_create()` (the CLI handler 126G added)
populated `report.commits` directly from `--commit` flags but never
declared `report.metadata["commit_attribution"]` — the exact field
`assess_completeness()`'s ownership check requires. The internal
`finalize_phase_report()` pipeline already follows this convention
correctly (`report.metadata["commit_attribution"] = kwargs[
"commit_attribution"]`, `src/pcae/core/phase_reports.py:1980-1981`);
the CLI path 126G added simply never wired it, so every report created
through `pcae phase-report create --commit ...` triggered the warning
unconditionally, regardless of how many commits were supplied or how
explicitly the operator declared them.

`assess_completeness()` itself required no change — it is functioning
exactly as designed. Once a caller correctly declares
`metadata["commit_attribution"]`, the check already passes.

## Repaired Component

**`src/pcae/commands/phase_reports.py`** — `run_phase_report_create()`
now sets `report.metadata["commit_attribution"] = ", ".join(commits)`
whenever `--commit` was explicitly supplied, immediately after
constructing the report and before calling `apply_trust_assessment()`
(ordering matters: the assessment reads `self.metadata` at call time).
This is a truthful declaration, not a suppression — the operator
explicitly supplied these commit hashes as this phase's own commits
via the same command that sets `report.commits`, exactly mirroring how
the internal pipeline already treats its own `commit_attribution`
kwarg. When no `--commit` flags are supplied, `commit_attribution` is
correctly left unset, and the underlying check behaves exactly as
before — commits stay listed as a missing field (a stronger, more
specific signal than the ownership warning, which only applies once
commits are present at all).

No other file needed to change. Canonical report generation
(`make_phase_report()`, `write_phase_report()`,
`PhaseReport.render_markdown()`), report formatting, governance/test/
no-go metadata handling, and notification formatting
(`phase_report_to_notification_event()`, `TelegramSink`) are all
untouched.

## Commit Metadata Pipeline Verification

Directly verified via fresh CLI invocations (not only the test suite):

- **Commits supplied via `--commit`** — `pcae phase-report create
  --commit abc12345 --commit def67890 ...` now produces a report with
  `report.metadata["commit_attribution"] == "abc12345, def67890"` and
  zero `phase_owned`-related entries in `trust_warnings`. Confirmed the
  rendered Markdown no longer contains a "Missing Trust Fields"
  section at all when every other trust field is also supplied.
- **No commits supplied** — confirmed `commit_attribution` correctly
  absent from `report.metadata`, and `"commits"` (not the ownership
  warning) correctly appears in `missing_trust_fields` — the original,
  unmodified `assess_completeness()` behavior for this case.
- **Commits present without CLI-declared attribution** (constructing a
  `PhaseReport` directly, bypassing the CLI, as any other caller might)
  — confirmed the `"commits.phase_owned not verified"` warning still
  fires exactly as before this phase. The underlying check was not
  weakened; only the CLI's own honest declaration was added.

## Trust Verification Results

- A report built entirely through `pcae phase-report create` with all
  required governance/test keys plus `--commit` flags now reaches
  `report_completeness: complete` with `trust_warnings == []` —
  previously it reached `complete` (since 126G) but still carried the
  stray ownership warning in the "Missing Trust Fields" section even
  though completeness itself was already `complete` (the warning is
  additive, not completeness-blocking, per the original 95I.1 design
  comment — this phase eliminates the false warning, not a false
  completeness downgrade).
- `pcae phase-report trust` (the independent, on-demand trust checker)
  is unaffected by this change — it reads the persisted report and was
  already correctly reporting `complete` before this fix; this phase's
  fix instead ensures `report.trust_warnings` (the list rendered
  directly into the canonical Markdown's "Missing Trust Fields"
  section) stops carrying a stale warning for data that was, in fact,
  already correctly attributed by the CLI's own arguments.

## Regression Verification

- `tests/test_phase_reports.py` (including 4 new tests in
  `TestPhase126G1CommitTrustMetadataRepair`): passed.
- `tests/test_telegram_notifications.py`, `tests/test_notifications.py`:
  passed, unchanged.
- `tests/test_task_finish_notification_ordering.py`,
  `tests/test_phase_report_trust_hard_fail.py`,
  `tests/test_task_finish_report_trust_notification.py`,
  `tests/test_finalization_notification_guarantee.py`: passed,
  unchanged.
- Combined notification/report/finalization suite: 297 passed (up
  from 126G's 293 — 4 new tests added).
- `fast_green` (`python -m pytest -m "fast_green" -n auto -ra
  --durations=0`): 4390 passed — unchanged from 126G's own fast_green
  count, since `tests/test_phase_reports.py` is not in this
  repository's `FAST_GREEN_MODULES` list (confirmed by direct
  `--collect-only` inspection), consistent with 126G's own finding for
  `tests/test_telegram_notifications.py`.

## Canonical Report / Notification Unchanged Confirmation

Confirmed via `git diff --stat` for this phase's own commit: only
`src/pcae/commands/phase_reports.py` (source) and
`tests/test_phase_reports.py` (tests) changed. Specifically unchanged:

- `make_phase_report()`, `write_phase_report()`,
  `PhaseReport.render_markdown()`, `PhaseReport.to_dict()` — canonical
  report generation and formatting, byte-identical behavior for any
  report whose commit attribution was already correctly declared.
- `phase_report_to_notification_event()`,
  `phase_report_to_partial_warning_notification_event()`,
  `TelegramSink` (all of `src/pcae/core/notifications.py`) —
  notification formatting and Telegram dispatch, completely untouched.
- Governance-results, test-results, and no-go-confirmation handling —
  untouched; only the commit-attribution declaration was added.

## Compatibility Confirmation

No Dependency Knowledge Graph, Repository Intelligence, Historical
Memory, execution planning, execution capability, runtime plugin,
Advisory, Decision Evaluation, or schema file was modified — confirmed
via `git diff --stat` scoped to this phase's commit, touching only
`src/pcae/commands/phase_reports.py` and `tests/test_phase_reports.py`.

## Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail, non-blocking.
- `tasks/active/` directory-collapse false-positive in `pcae
  check`/`pcae health` for a newly created, still-untracked task
  contract file: governance-tooling detail, non-blocking (resolved for
  this session by staging the file before continuing).
- The recurring `pending_final_telegram_delivery` reporting detail
  (dispatch-ordering/timing, distinct from content fidelity) remains
  carried forward unchanged, as noted by 126G.
- Two parallel, not-fully-reconciled trust-assessment implementations
  still coexist (`PhaseReport.assess_completeness()` vs.
  `pcae.core.phase_report_trust.validate_phase_report_trust()`, used
  by `pcae phase-report trust`) — noted by 126G, not addressed here;
  out of this phase's narrow commit-trust-metadata scope.

**Resolved by this phase**: the specific `commits.phase_owned not
verified — no phase_commits in metadata` warning is now correctly
absent whenever `pcae phase-report create --commit ...` is used to
declare commit ownership, while remaining correctly present whenever
commit ownership genuinely cannot be attributed.

## Confirmations

- **Canonical report generation unchanged.** Confirmed via diff scope
  above — zero lines changed in `PhaseReport`, `make_phase_report()`,
  or `write_phase_report()`.
- **Notification unchanged except the repaired trust field.** Zero
  lines changed in `src/pcae/core/notifications.py`; the only
  observable difference in a dispatched notification is the presence
  or absence of the now-correctly-resolved `phase_owned` warning
  inside `trust_warnings`, which 126G already wired into event
  metadata unchanged.
- **Missing Trust Fields warning resolved when applicable.** Confirmed
  directly: a report built with `--commit` flags plus all required
  governance/test keys renders zero "Missing Trust Fields" section.
- **No runtime behavior changed.** No module touched by this phase
  imports `subprocess`, invokes a shell, or touches runtime state.
- **Execution remains unavailable.** Confirmed via `pcae runtime
  inspect`: `Observed` / `observe` / execution unavailable / zero
  runtime plugins / registry empty / Permission Broker
  `execution_unavailable`.

## Governance Results

- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean.
- `pcae push check`: clean.
- `pcae runtime inspect`: `Observed` / `observe` / execution
  unavailable / zero runtime plugins.
- `pcae notify status` (after sourcing
  `~/.config/pcae/telegram.env`): Telegram configured, enabled, ready.

## Conclusion

Phase 126G.1 traced the complete commit metadata lifecycle from phase
finalization through Telegram dispatch and found the final remaining
trust gap 126G left behind: `pcae phase-report create` declared
commits on the report but never declared their ownership attribution,
the specific field `assess_completeness()`'s commit-ownership check
requires. A single, minimal, targeted fix — declaring `metadata[
"commit_attribution"]` from the same `--commit` flags already
supplied — resolves the warning honestly whenever commit ownership is
genuinely declared, while leaving the check's behavior completely
unchanged (and therefore still correctly warning) whenever it is not.
No canonical report generation, formatting, governance/test/no-go
metadata, or notification formatting was touched. No Dependency
Knowledge Graph, Repository Intelligence, Historical Memory,
execution, runtime plugin, Advisory, Decision Evaluation, or schema
file was modified. Runtime remains
`Observed`/`observe`/execution-unavailable throughout.

Recommended next phase: 127A — Historical Memory Architecture.
