# Phase 113W — Repository Transition Validator Integration Design

**Status:** Complete. Architecture/design only — no implementation.

## Purpose

Phase 113W designs how the Repository Transition Validator will eventually
integrate with PCAE lifecycle commands so inconsistent agents can propose
work but cannot make invalid repository state canonical.

The durable design is
`docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION.md`.

## Containment Target

The target state is: model proposes, PCAE validates, valid transitions
proceed, invalid transitions reject/quarantine/require human review, and no
invalid state becomes canonical. DeepSeek, other models, human operators,
future schedulers, and future automation all submit transition proposals to
the same validator path.

## Integration Point Summary

The design covers `pcae phase complete`, `pcae task finish --commit`, report
generation, report promotion, phase-completion metadata, `pcae push check`,
`pcae notify send-report`, the phase-finalization skill, future automation
and scheduler paths, and future agent-driven workflows.

Each integration point is specified with current behavior, proposed validated
behavior, required `RepositoryState` inputs, `ProposedTransition`,
`ExpectedTargetState`, invariants, and accept/reject/quarantine/human-review
outcomes.

## Canonical Promotion Summary

The design requires one future promotion path for `latest.json`,
`latest.md`, phase-completion metadata consumption, and notification event
eligibility. A Draft report can become Certified only after an Accept verdict;
only Certified can become Canonical/latest; notifications can reference only a
Certified/Canonical report. No alternate promotion path is allowed.

## Failure Behavior Summary

Reject writes no canonical artifact, updates no project memory, sends no
notification, exits non-zero, and prints invariant diagnostics. Quarantine
retains the suspect artifact for inspection but never promotes it. Human
review blocks canonical mutation until explicit operator resolution. Accept
proceeds through the single promotion path.

## DeepSeek Containment Scenarios

The design explicitly covers stale commits in report, wrong phase ID, missing
recommended next phase, bad test-results structure, duplicate Telegram
reports, silent missing Telegram report, stale phase-completion metadata,
report from wrong phase, Architecture Status overclaim, and push with
untrusted report.

## Implementation Order

Recommended order:

1. `pcae phase complete`
2. report promotion/latest artifacts
3. `pcae task finish --commit`
4. notification dispatch
5. `pcae push check`
6. cross-agent verification

This order is confirmed because phase completion is the authoritative
lifecycle boundary; report promotion is the shared canonical write surface;
task finish is the second existing path identified by 113S/113T; notification
must wait for central certification; push check consumes certified state; and
cross-agent verification should exercise integrated paths after they exist.

## No-Go Confirmation

No validator integration implemented. No lifecycle command behavior changed.
No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime Registry,
Runtime Inspect, Permission Broker enforcement, execution, authorization,
plugin, Telegram inbound, REST, Web UI, or Dashboard changes. Execution
capability remains unavailable. Execution capability remains unavailable,
runtime state remains Observed, and maximum plugin capability remains
`observe`.

## Tests

Added `tests/test_repository_transition_validator_integration_design.py`.
These are architecture/design documentation-completeness tests only. They do
not test or imply implementation.

Validation run:

- Focused design tests: `57 passed`.
- Affected bootstrap/report-trust regression files:
  `tests/test_bootstrap_todo_consistency.py`,
  `tests/test_rc_audit_findings_repair.py`, and the 113W design tests:
  `93 passed`.
- Governance/autonomy group:
  `tests/test_*runtime* tests/test_*contract* tests/test_*autonomy* tests/test_*plugin* tests/test_*advisory*`
  under `-n auto`: `3784 passed`.
- Release/lifecycle regression:
  `tests/test_task*.py tests/test_*task* tests/test_*phase* tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py`
  under `-n auto`: `1552 passed`.
- Fast-green: `4390 passed`.
- Full suite: `16703 passed`.

During full-suite validation, stale real-repo expectations from Phase 112B.1
were updated to track the current `PROJECT_STATUS.md` recommendation (`113X`)
and `tasks/TODO.md` next marker. The Phase 106H synthetic report-trust fixture
now derives the current project phase ID from `PROJECT_STATUS.md`, preserving
the test's intent under the strengthened phase-identity gate.

## Recommended Next Phase

113X — Repository Transition Validator Integration Contract.
