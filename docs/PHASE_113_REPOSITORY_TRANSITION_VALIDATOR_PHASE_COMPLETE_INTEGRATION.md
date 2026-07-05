# Phase 113Y — Repository Transition Validator Phase Completion Integration

## Status

Completed.

This is the first implementation phase for the Repository State Kernel /
Model Containment Layer. It integrates the Repository Transition Validator
into exactly one lifecycle command:

- `pcae phase complete`

No other lifecycle command was integrated.

## Integration Scope

`pcae phase complete` now performs a mandatory Repository Transition
Validator check before canonical phase-report promotion. The integration is
inside `src/pcae/commands/phase.py`, after phase identity, metadata, trial
report, finalization gate, and trust state are computed, and before
`finalize_phase_report()` can write timestamped report artifacts or
`latest.md` / `latest.json`.

The integration does not modify:

- `pcae task finish --commit`
- `pcae push check`
- notification dispatch internals
- Runtime Snapshot
- Runtime Inspect
- Advisory Runtime
- Permission Broker
- execution capability
- REST, Web UI, Dashboard, or Telegram inbound

## Validator Call Sequence

The phase-complete path now follows this sequence:

1. Resolve canonical phase identity using the existing identity resolver.
2. Load `.pcae/phase-completion-metadata.json`.
3. Build the trial `PhaseReport`.
4. Apply canonical/trust assessment to the trial report.
5. Build `RepositoryState`.
6. Build `ProposedTransition(kind=complete_phase)`.
7. Build `ExpectedTargetState(artifact_state=canonical)`.
8. Invoke `validate_transition(...)`.
9. Continue to canonical promotion only when the verdict is `accept`.

No canonical `latest.*` artifact is written before the validator verdict is
known.

## Verdict Behavior

### Accept

The command continues through the existing report finalization path.
Observable lifecycle behavior remains compatible for valid phase completions:
the same report writer owns the final write, notifications remain downstream
of the existing report path, and the normal success exit code is preserved.

Diagnostic output includes:

- `Repository transition validator: Transition validated`
- `Verdict: accept`

### Reject

The command stops before canonical report generation.

Effects:

- no canonical report is created
- `latest.md` is not written or overwritten
- `latest.json` is not written or overwritten
- no notification dispatch path is entered
- command exits non-zero

Diagnostics include:

- `Repository transition validator: Transition rejected`
- the validator verdict
- violated invariant identifiers and reasons

### Quarantine

The command writes quarantine artifacts only, using the existing quarantined
phase-report format under `.pcae/phase-reports/quarantine/`.

Effects:

- quarantine markdown is written
- quarantine JSON is written
- `latest.md` is not written or overwritten
- `latest.json` is not written or overwritten
- no notification dispatch path is entered
- command exits non-zero

Diagnostics include:

- `Repository transition validator: Transition quarantined`
- violated invariant identifiers and reasons
- quarantine artifact paths

### Requires Human Review

The command stops before canonical report generation when phase-completion
metadata explicitly requests human review.

Effects:

- no canonical report is created
- no quarantine artifact is written by this branch
- `latest.md` is not written or overwritten
- `latest.json` is not written or overwritten
- no notification dispatch path is entered
- command exits non-zero

Diagnostics include:

- `Repository transition validator: Human review required`
- `human_review_required`

## Canonical Promotion Summary

`pcae phase complete` no longer directly owns the decision to make a phase
completion canonical. It requests a `complete_phase` transition. The
Repository Transition Validator certifies whether the transition may proceed.
Only after an `accept` verdict does the existing report finalization path
write canonical `latest.*` artifacts.

The existing report writer still performs the physical file write. The new
authority boundary is that the write is unreachable unless the transition is
accepted first.

## Failure Mapping

The first phase-complete integration maps the required failure classes
deterministically:

| Failure class | Validator outcome |
| --- | --- |
| phase identity mismatch | `reject` |
| metadata mismatch | `reject` |
| missing `recommended_next_phase` | `reject` |
| complete missing report evidence | `reject` |
| partial report completeness | `quarantine` |
| explicit human-review metadata flag | `requires_human_review` |
| execution availability other than `unavailable` | `reject` |

Invariant identifiers are printed in diagnostics so inconsistent agents can
propose work, but cannot silently make invalid repository state canonical.

## Compatibility Guarantees

Accepted phase completions continue through the existing lifecycle flow.

The integration preserves:

- existing CLI command shape
- existing final report writer
- existing notification implementation
- existing governance/trust checks after acceptance
- existing Runtime Snapshot behavior
- existing Runtime Inspect behavior
- existing Advisory Runtime behavior
- existing Permission Broker posture
- execution unavailable posture

The only intended behavior change is that invalid phase-complete transitions
are stopped before canonical promotion.

## Future Integration Work

Next phase:

- 113Z — Repository Transition Validator Integration: Task Finish

Future phases remain:

- 114A — Report promotion/quarantine hardening
- 114B — Notification enforcement
- 114C — Push/check integration
- 114D — Cross-agent verification
- 114E — Model containment drill

## Validation

Validation completed:

- focused phase-complete integration: `8 passed`
- focused integration plus legacy phase-complete fixtures: `16 passed`
- report/finalization regression slice: `194 passed`
- phase lifecycle suite: `894 passed`
- governance/autonomy suite: `3830 passed`
- release/lifecycle regression: `1560 passed`
- fast_green: `4390 passed`

Full governance and release validation is recorded in the canonical phase
completion report.

## No-Go Confirmation

No task-finish integration. No report-promotion integration outside the
phase-complete path. No push integration. No notification-dispatch
enforcement. No Runtime Snapshot change. No Runtime Inspect change. No
Advisory Runtime change. No Permission Broker enforcement. No execution
capability. No REST. No Web UI. No Dashboard. No Telegram inbound. No tag.
No release. No package publication.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.
