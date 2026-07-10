# Phase 126G - Telegram Canonical Report Dispatch Repair

## Status

Complete.

## Purpose

During 126F's finalization, the Telegram notification delivered for the
completed phase report was observed to carry only a short, reduced
generated summary — showing `Report completeness: partial`, `Commits:
not captured`, and omitting verification evidence — even though the
canonical report itself was complete. This phase investigates the
complete notification pipeline (canonical report generation, trust
evaluation, notification formatting, Telegram sink, final dispatch),
identifies the precise root causes, and repairs them. It is not part
of Dependency Knowledge Graph, Repository Intelligence, Historical
Memory, or execution planning. No schema file was touched.

## Root Cause Analysis

Four independently verified, distinct defects were found across the
pipeline, each reproduced directly (not inferred from symptoms alone)
before any repair:

### Defect 1 — Event metadata silently dropped governance/test evidence

`phase_report_to_notification_event()` (`src/pcae/core/notifications.py`)
never included `test_results` or `governance_results` in the
`NotificationEvent.metadata` dict it built, even though
`TelegramSink._build_summary()` explicitly reads exactly those two
metadata keys to render its "Tests:"/"Governance:" lines. Reproduced
directly: constructing a `PhaseReport` with both fields fully
populated and calling the real event builder showed
`"test_results" in event.metadata` and `"governance_results" in
event.metadata` both `False` — the Tests/Governance lines silently
never rendered, for any report, regardless of how complete the
underlying canonical data was. This matches "greatly reduced
verification evidence" and "canonical report content not preserved"
directly.

### Defect 2 — Document delivery could diverge from the trusted report object

Telegram document delivery (`TelegramSink.send()`) read
`event.artifact_paths[0]` — a raw file path on disk (typically
`.pcae/phase-reports/latest.md`) — and sent whatever bytes happened to
be there at send time. Nothing guaranteed that file stayed in sync
with the specific `PhaseReport` object the trust gate had just
validated. This is not a hypothetical: it is exactly what happened
during 126F's own finalization, when `.pcae/phase-reports/latest.json`
was corrected to `report_completeness: complete` with full evidence,
but the sibling `latest.md` file was never regenerated from the
corrected object — so a Telegram document send at that point would
have delivered the stale, partial markdown regardless of what the JSON
(and the trust gate) actually said.

### Defect 3 — Silent summary truncation

When the compact Telegram summary text exceeded `max_message_chars`,
it was silently cut with a bare `"..."` suffix — no indication to the
reader that content was missing, violating the Fallback Contract's
explicit "silent truncation is forbidden" rule.

### Defect 4 — `pcae phase-report create` could not populate trust-critical fields

The CLI handler for `pcae phase-report create` never wired
`commits`, `governance_results`, `test_results`, or
`explicit_no_go_confirmations` from arguments into `make_phase_report()`
— even though the underlying `PhaseReport`/`make_phase_report()` already
fully supported all four as constructor fields. This forced any
operator who needed a genuinely complete, trust-passing report to
hand-edit the JSON/Markdown artifacts directly, bypassing
`write_phase_report()`'s atomic json+markdown generation — precisely
the unsafe workaround that produced Defect 2's desync during 126F.
Additionally, the CLI never called `report.apply_trust_assessment()`
before writing, so `report_completeness` was persisted as a permanent
empty string regardless of what was supplied, even though
`pcae phase-report trust` (a separate, independent trust-check code
path) could correctly assess the same data on demand.

## Repaired Components

All four defects were repaired with minimal, targeted changes; no
unrelated notification infrastructure was redesigned.

1. **`src/pcae/core/notifications.py`** —
   `phase_report_to_notification_event()` and
   `phase_report_to_partial_warning_notification_event()` now include
   `test_results`, `governance_results`, a compact `report_consistency`
   summary, and `canonical_report_markdown` (the exact
   `report.render_markdown()` output) in event metadata.
2. **`src/pcae/core/notifications.py`** —
   `TelegramSink.send()` now prefers `event.metadata["canonical_report_
   markdown"]` (sent via a new `_send_document_bytes()` helper) over a
   raw `artifact_paths` file, so document delivery can never diverge
   from the trusted report object. Falls back to the existing
   path-based behavior when the embedded content is absent (e.g. other
   event types), preserving compatibility.
3. **`src/pcae/core/notifications.py`** —
   `_build_summary()`'s truncation now appends an explicit
   `[TRUNCATED — full canonical report attached as document]` marker
   instead of a bare `"..."`, and a `Consistency:` line was added
   reflecting the new `report_consistency` metadata. On document
   attachment failure, `send()` now sends an additional, clearly marked
   `"⚠️ TRUNCATED — canonical report delivery incomplete"` follow-up
   message (Fallback Contract item 4) rather than leaving the failure
   silent on the mobile channel.
4. **`src/pcae/commands/phase_reports.py`** / **`src/pcae/cli.py`** —
   `pcae phase-report create` gained repeatable `--commit`,
   `--governance-result NAME=STATUS`, `--test-result NAME=STATUS`, and
   `--no-go-confirmation TEXT` flags, and now calls
   `report.apply_trust_assessment()` before writing, so a complete,
   trust-passing report can be produced through the governed CLI alone
   — closing the process gap that caused Defect 2's manual-edit
   workaround.

## Canonical Dispatch Contract Verification

Independently verified via direct invocation (not only via the test
suite) against a freshly constructed, fully-populated `PhaseReport`:

- **Phase metadata** — `phase_id`/`phase_name`/`phase_status` present;
  confirmed unchanged from prior behavior.
- **Summary** — `report.summary` still used as the notification
  message field; unchanged.
- **Governance results** — confirmed present in event metadata and
  rendered as a `Governance:` line in the Telegram summary
  (`pcae_check passed, pcae_health healthy, ...`).
- **Test results** — confirmed present in event metadata and rendered
  as a `Tests:` line.
- **No-go confirmations** — confirmed present in event metadata
  (full list); the summary shows a compact first-item preview (by
  design, to stay concise — the existing `test_text_concise_under_
  800_chars` trust-contract test was not changed), with the complete
  list preserved in the attached canonical document.
- **Report consistency** — new `Consistency:` line added, derived from
  the same `canonical_report_used`/`trust_warnings` fields
  `render_markdown()`'s own "Report Consistency" section already uses.
- **Recommended next phase** — confirmed present and rendered
  (`Next: ...`).
- **Commit hashes** — confirmed preserved whenever available
  (`Phase commit: ...` / `Recent commits: ...`); confirmed via a fresh
  `pcae phase-report create --commit ... --commit ...` invocation that
  the persisted report's `Commits:` field is no longer "not captured".
- **Report completeness accuracy** — confirmed a report built entirely
  through `pcae phase-report create` with the new flags now persists
  `report_completeness: complete` (previously always empty/unassessed
  through this command), matching what `pcae phase-report trust`
  independently computes for the same data.

## Fallback Behavior Verification

Directly probed each preferred-order fallback tier:

1. **Complete canonical report within limits** — confirmed the
   document payload sent to Telegram is byte-identical to
   `report.render_markdown()`, even when the sibling `artifact_paths`
   file does not exist on disk (proving delivery no longer depends on
   file presence/freshness).
2. **Deterministic splitting for oversized content** — the compact
   summary itself, when forced past `max_message_chars` (e.g. via a
   report with 50+ governance/test entries), truncates at a
   deterministic boundary with an explicit marker rather than
   arbitrary/silent loss; the full canonical content remains available
   via the always-attempted document channel regardless of summary
   length.
3. **Document attachment with executive summary** — this is the
   architecture's normal path (compact summary message +
   full-canonical-content document) and was already broadly correct;
   Defect 1/2 are what made it deliver incomplete content in practice.
4. **Clearly marked truncated notification when attachment is
   impossible** — confirmed: forcing a document-send failure now
   produces an additional `sendMessage` call whose text contains
   `TRUNCATED` and explicitly states delivery was incomplete, instead
   of only a Python-side result field.

Silent truncation is confirmed eliminated: every truncation path now
either delivers full content via the document channel or emits an
explicit `TRUNCATED` marker.

## Verification Matrix

Directly verified (via new tests in
`tests/test_telegram_notifications.py::TestPhase126GCanonicalDispatch`
plus ad hoc direct invocation in this session), covering every
scenario named in the task brief:

| Scenario | Result |
| --- | --- |
| Complete canonical report | Governance/test/commit/consistency all present in event + summary |
| Partial report | Available evidence (commits, governance, test results) still preserved, not additionally dropped |
| Documentation-only phase (`tests_run=0`) | `test_results`/`governance_results` still populated and delivered when supplied |
| Implementation phase | Covered by the complete-report scenario above |
| Verification phase | Covered by the complete-report scenario above (126F's own shape) |
| Long report (80 governance + 80 test entries) | Summary truncates deterministically with explicit `TRUNCATED` marker; full content still in document |
| Short report | Delivered whole, no truncation marker present |
| Commit capture | `--commit` (repeatable) now reaches the persisted report and the notification |
| Governance capture | `--governance-result NAME=STATUS` (repeatable) now reaches the persisted report and the notification |
| Test result capture | `--test-result NAME=STATUS` (repeatable) now reaches the persisted report and the notification |

## Regression Verification

- `tests/test_telegram_notifications.py`: 47 passed (37 pre-existing +
  10 new Phase 126G tests). Two pre-existing tests
  (`test_truncation_ellipsis`, testing the old silent-`"..."`
  behavior) were updated to assert the new, correct `TRUNCATED` marker
  behavior instead — this is the exact defect 126G was scoped to fix,
  not an unrelated behavior change.
- `tests/test_notifications.py`: passed, unchanged.
- `tests/test_phase_reports.py`: passed, unchanged.
- `tests/test_task_finish_notification_ordering.py`,
  `tests/test_phase_report_trust_hard_fail.py`,
  `tests/test_task_finish_report_trust_notification.py`,
  `tests/test_finalization_notification_guarantee.py`: 87 passed,
  unchanged.
- Combined notification/report-related suite total: 293 passed.
- `fast_green` (`python -m pytest -m "fast_green" -n auto -ra
  --durations=0`): 4390 passed (existing suite) — this repository's
  fast_green marker set does not include the newly added
  `TestPhase126GCanonicalDispatch` class (it is not decorated
  `fast_green`), consistent with how other recently added test classes
  in this file are scoped; explicitly run separately above.

## Compatibility Confirmation

- **Canonical report generation unchanged** — `make_phase_report()`,
  `write_phase_report()`, `PhaseReport.render_markdown()`,
  `PhaseReport.assess_completeness()` were not modified. Only the CLI
  wiring in `run_phase_report_create()` was extended to pass through
  already-supported constructor fields and call the already-existing
  `apply_trust_assessment()` method.
- **No Dependency Knowledge Graph, Repository Intelligence, Historical
  Memory, execution planning, execution capability, runtime plugin,
  Decision Evaluation, Advisory, or schema file was modified** —
  confirmed via `git diff --stat` scoped to this phase's commits,
  touching only `src/pcae/core/notifications.py`,
  `src/pcae/commands/phase_reports.py`, `src/pcae/cli.py`, and
  `tests/test_telegram_notifications.py`.
- **No runtime behavior changed** — no module touched by this phase
  imports `subprocess`, invokes a shell, or touches runtime state.

## Known Inherited Issues

Carried forward, not repaired in this phase (out of scope — inherited
tooling debt, not notification dispatch):

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail, non-blocking.
- `tasks/active/` directory-collapse false-positive in `pcae
  check`/`pcae health` for a newly created, still-untracked task
  contract file: governance-tooling detail, non-blocking (resolved for
  this session by staging the file before continuing).

**Resolved by this phase**: the recurring `pending_final_telegram_
delivery` reporting detail is **not** fully resolved by this repair —
that detail refers to notification dispatch occurring after report
promotion in the finalization sequence (an ordering/timing detail,
Phase 113X/119Q-adjacent), which is a different, narrower concern than
the content-fidelity defects repaired here. It remains carried forward
unchanged; this phase's repair is scoped to content fidelity, not
dispatch ordering.

## Confirmations

- **No runtime behavior changed.** Confirmed via `pcae runtime
  inspect` in this session.
- **Execution remains unavailable.** `Observed` / `observe` / execution
  unavailable / zero runtime plugins / registry empty / Permission
  Broker `execution_unavailable`.
- **Canonical report generation unchanged.** Confirmed via diff scope
  above.
- **Telegram now preserves canonical report content.** Confirmed via
  direct reproduction of all four defects and their fixes above.

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

Phase 126G identified and repaired four distinct, independently
verified defects spanning notification formatting (missing governance/
test metadata), final dispatch (document-content staleness risk),
fallback behavior (silent truncation), and canonical report generation
tooling (CLI unable to populate trust-critical fields, forcing unsafe
manual edits). Telegram now faithfully delivers canonical phase report
content — governance results, test results, commits, report
consistency, and recommended next phase — derived directly from the
trusted report object rather than an independently generated,
possibly-stale summary. No unrelated notification infrastructure was
redesigned. No Dependency Knowledge Graph, Repository Intelligence,
Historical Memory, execution, runtime plugin, Decision Evaluation,
Advisory, or schema file was touched. Runtime remains
`Observed`/`observe`/execution-unavailable throughout.

Recommended next phase: 127A — Historical Memory Architecture.
