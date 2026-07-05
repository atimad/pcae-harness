# Phase 113Z — Repository Transition Validator Task Finish Integration

## Status

Completed.

This implementation phase integrates the Repository Transition Validator into
exactly one additional lifecycle path:

- `pcae task finish --commit`

No push-check integration, notification-dispatch enforcement, execution
runtime, authorization, Permission Broker enforcement, plugin execution,
Telegram inbound path, REST API, Web UI, or Dashboard behavior was added.

## Integration Scope

`pcae task finish --commit` now performs a mandatory Repository Transition
Validator check before canonical phase-report promotion. The command still
finishes and commits the governed task closure through the existing task
lifecycle path, but `latest.md` and `latest.json` are unreachable unless the
validator accepts the phase-report transition.

The integration repairs the 113S/113T asymmetry: task finish can no longer
write or promote canonical phase-report artifacts through a path that bypasses
the validator already required by `pcae phase complete`.

## Shared Validation Path

Phase 113Z moves the phase-report validator adapter into
`src/pcae/core/repository_transition_integration.py` so both lifecycle paths
use one canonical validation helper:

- `pcae phase complete` requests `ProposedTransition(kind=complete_phase)`
- `pcae task finish --commit` requests `ProposedTransition(kind=finish_task)`

Both paths build the same validator input family:

1. canonical phase identity from `resolve_canonical_phase_identity(...)`
2. `RepositoryState`
3. `ProposedTransition`
4. `ExpectedTargetState(artifact_state=canonical)`
5. `validate_transition(...)`

No canonical `latest.*` artifact is written before the validator verdict is
known.

## Canonical Identity

Task finish preserves the completed task title as the active-task identity
source before the task file moves to `tasks/done/`. That title is passed into
the same canonical identity resolver used by phase complete.

Stale `.pcae/phase-completion-metadata.json` is not trusted as canonical when
it disagrees with the resolved phase identity. The validator sees metadata as
an independent source and rejects identity or metadata mismatch instead of
letting stale metadata overwrite `latest.md` or `latest.json`.

## Verdict Behavior

### Accept

Accepted task-finish transitions continue through the existing report
finalization flow. Valid metadata still produces canonical phase-report
artifacts, and existing successful task-finish behavior remains compatible.

Diagnostics include:

- `Repository transition validator: Transition accepted`
- `Verdict: accept`

### Reject

Rejected task-finish transitions stop before canonical report promotion.

Effects:

- no `latest.md` write or overwrite
- no `latest.json` write or overwrite
- no notification dispatch
- deterministic non-zero task-finish exit code after the task closure commit
- invariant identifiers included in output and JSON

Reject covers identity mismatch, metadata mismatch, missing
`recommended_next_phase`, missing report evidence, and execution availability
claims other than `unavailable`.

### Quarantine

Partial report evidence maps to quarantine.

Effects:

- quarantine artifacts are written under `.pcae/phase-reports/quarantine/`
- `latest.md` is unchanged
- `latest.json` is unchanged
- no notification dispatch
- deterministic non-zero task-finish exit code after the task closure commit

This changes the older warning-only task-finish behavior: partial final-push
state no longer writes a canonical latest report merely for visibility. It is
visible only as quarantine until repaired.

### Requires Human Review

Metadata that explicitly requires human review blocks promotion.

Effects:

- no canonical report
- no quarantine artifact from this branch
- no notification dispatch
- deterministic non-zero task-finish exit code after the task closure commit

## Compatibility Guarantees

The accepted path preserves the existing task-finish UX and report writer.
JSON output remains parseable; validator details appear under
`repository_transition_validator` when the validator blocks promotion.

The integration does not modify:

- `pcae push check`
- notification command behavior
- notification sink implementation
- Runtime Snapshot
- Runtime Inspect
- Advisory Runtime
- Permission Broker
- execution availability

## Regression Scenarios Covered

Focused tests verify:

- task finish invokes the Repository Transition Validator
- accepted task finish writes canonical latest reports
- missing `recommended_next_phase` rejects and leaves latest unchanged
- stale phase-completion metadata cannot overwrite latest
- phase identity mismatch is rejected
- partial reports quarantine and never promote
- human review blocks promotion
- execution availability violations reject
- task finish and phase complete use the same shared transition adapter
- notification and push-check command modules are not integrated

Current validator invariants do not implement live commit-lineage validation.
The 113Z test suite documents that `commit_lineage` remains outside
`STRUCTURAL_INVARIANTS`; full stale-commit enforcement remains future work for
a live-I/O adapter phase.

## Future Remaining Integration Points

Recommended next phase:

- 114A — Report Promotion & Quarantine Hardening

Still remaining after 113Z:

- report promotion/quarantine hardening
- notification enforcement
- push/check integration
- cross-agent verification
- model containment drill

## No-Go Confirmation

No notification-dispatch enforcement. No push-check integration. No execution
runtime. No authorization. No Permission Broker enforcement. No plugins. No
Telegram inbound. No REST. No Web UI. No Dashboard. No tags. No releases. No
package publication.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused task/phase validator integration and task-finish report suites: `60 passed`
- repository-transition/task/report focused group: `713 passed`
- governance/autonomy/runtime/advisory/plugin group: `3830 passed`
- release/lifecycle regression: `1571 passed`
- fast_green: `4390 passed`
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: nothing_to_push, health/check passed
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 113Z`: resolved, target status completed
