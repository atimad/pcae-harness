# PCAE Repository Transition Validator — Integration Design

**Status:** Design only. No lifecycle integration is implemented by this
document.
**Phase:** 113W.
**Extends:** 113S architecture, 113T contract, 113U prototype, 113V
verification, and 113V.N notification finalization repair.

## 1. Containment Target

The target state is:

1. A model, human operator, scheduler, or future automation proposes a
   repository transition.
2. PCAE constructs the authoritative `RepositoryState` from live repository
   sources.
3. PCAE constructs a `ProposedTransition` and `ExpectedTargetState`.
4. The Repository Transition Validator returns exactly one verdict:
   `accept`, `reject`, `quarantine`, or `requires_human_review`.
5. Valid transitions proceed through one canonical promotion path.
6. Invalid transitions are rejected, quarantined, or held for human review.
7. No invalid repository state becomes canonical.

This is the containment rule for DeepSeek and every other inconsistent
agent: the agent may propose text, code, metadata, reports, and transition
intent, but it cannot certify its own state. Repository state is
authoritative; PCAE validates before canonical mutation.

## 2. Non-Goals

This phase does not implement validator integration. It does not modify
`pcae phase complete`, `pcae task finish --commit`, report writing,
notification dispatch, push checks, or any lifecycle command behavior.

It also does not modify Advisory Runtime, Runtime Snapshot, Runtime Context,
Runtime Registry, Runtime Inspect, Permission Broker enforcement, execution,
authorization, plugins, Telegram inbound, REST, Web UI, or Dashboard.
Execution capability remains unavailable, runtime state remains Observed, and
maximum plugin capability remains `observe`.

## 3. Integration Points

Future integration must cover every path that can affect canonical lifecycle
state:

- `pcae phase complete`
- `pcae task finish --commit`
- report generation
- report promotion
- phase-completion metadata
- `pcae push check`
- `pcae notify send-report`
- phase-finalization skill
- future automation and scheduler paths
- future agent-driven workflows

No command owns canonical state. Each command becomes a transition request
that calls one shared validation and promotion pipeline.

## 3.1 116B Consolidation Ownership

Phase 116B clarifies the intended ownership model without changing
current lifecycle behavior:

- `RepositoryState` construction is one policy, even where current code
  has two construction call sites. A future helper should live with the
  Repository Transition Validator/integration layer and be used by both
  `validate_phase_report_transition(...)` and
  `certify_notification_transition(...)`.
- Lifecycle commands remain front ends that request transitions. They do
  not own phase identity, report completeness, recommended-next-phase
  enforcement, canonical promotion eligibility, notification
  eligibility, or execution-unavailability policy.
- Structural invariants are the long-term home for phase identity,
  metadata consistency, report completeness, and recommended-next-phase
  enforcement. The finalization gate remains a v0.2 compatibility/trust
  gate until its unique governance-key and test-result-key checks are
  migrated into first-class invariants.
- Repository Event remains policy/taxonomy only for v0.2. Notification
  certification observes transition outcomes and dispatch eligibility; it
  does not materialize an event stream or own an event runtime type.

## 4. Transition Flow Matrix

### 4.1 `pcae phase complete`

Current behavior: resolves phase identity, reads phase-completion metadata,
generates a phase report, writes `latest.json`/`latest.md`, evaluates report
trust, updates project memory, and may dispatch notification depending on
transport state and idempotency.

Proposed validated behavior: build `RepositoryState` from git state, active
task, phase identity, metadata, report draft, test results, project status,
push state, notification marker, runtime state, and execution availability.
Submit `ProposedTransition(kind=complete_phase)` plus nested
`report_generation`, `report_promotion`, `status_update`, and optional
`notify` transitions to one validator path.

Required inputs: active task contract, canonical phase identity,
`.pcae/phase-completion-metadata.json`, draft report, computed report trust,
test results, commit list, `PROJECT_STATUS.md`, git status, push status,
notification marker, notification transport status, runtime inspect result,
and execution availability.

Expected target: completed phase, certified report, updated
`PROJECT_STATUS.md`, latest artifacts promoted only after certification, and
notification eligibility evaluated after canonical promotion.

Invariants: phase identity consistency, active task consistency, commit
lineage, metadata consistency, report completeness, report trust,
architecture status consistency, recommended-next-phase consistency, test
result consistency, push state consistency, notification eligibility, single
final notification, no execution availability, and single canonical
transition authority.

Accepted outcome: project memory and latest artifacts update through the
single promotion path; notification is considered only after certification.
Reject outcome: no canonical artifact or project-memory update is written;
diagnostics name each blocking invariant; exit code is non-zero.
Quarantine outcome: the draft report is retained under quarantine with
diagnostics; `latest.*` and project memory remain unchanged; exit code is
non-zero.
Human-review outcome: no canonical state changes; a review record or explicit
operator instruction is required before retry; exit code is non-zero.

### 4.2 `pcae task finish --commit`

Current behavior: validates task state, stages allowed files, creates a
governed commit, moves the task contract, updates memory, and may finalize a
phase report and notification using phase-completion metadata.

Proposed validated behavior: task finishing remains a governed task
transition. Any report side effect is expressed as the same
`report_generation`/`report_promotion` transition used by `pcae phase
complete`; it never writes latest artifacts independently.

Required inputs: active task contract, staged/unstaged file scope, git commit
candidate, phase identity, metadata, draft report, test evidence, report trust,
notification marker, and push state.

Expected target: done task contract, governed commit, one certified canonical
report if phase finalization is in scope, and no duplicate notification.

Invariants: allowed file scope, active task consistency, commit lineage,
phase identity consistency, metadata consistency, report trust, canonical
promotion eligibility, and notification idempotency.

Accepted outcome: task closes and commit is created through governed
lifecycle; any report promotion routes through the shared promotion path.
Reject outcome: task remains active or recoverable; no commit or latest
artifact is created; exit code is non-zero.
Quarantine outcome: task closure may be blocked while generated report
evidence is retained for inspection; latest artifacts remain unchanged.
Human-review outcome: task closure/commit is paused until explicit operator
approval resolves the ambiguity.

### 4.3 Report Generation

Current behavior: report content is assembled from metadata, validation
results, git commits, and project status by existing report helpers.

Proposed validated behavior: report generation produces a Draft artifact only.
Drafts are not canonical and are never sent externally.

Required inputs: phase identity, metadata, commits, test results, architecture
status, recommended next phase, current project status, and validation output.

Expected target: Draft report with structured fields complete enough for
validation.

Invariants: report completeness, metadata consistency, commit lineage, test
result consistency, architecture status consistency, and
recommended-next-phase presence.

Accepted outcome: Draft may advance to promotion validation.
Reject outcome: no artifact is retained unless diagnostics require it.
Quarantine outcome: malformed or suspicious draft is retained under
quarantine, never `latest`.
Human-review outcome: draft is held with explicit ambiguity diagnostics.

### 4.4 Report Promotion

Current behavior: more than one command path can create or refresh latest
artifacts, though 113V.N repaired notification idempotency across current
paths.

Proposed validated behavior: one shared promotion function is the only writer
of `.pcae/phase-reports/latest.json` and `.pcae/phase-reports/latest.md`.
Only a Certified report may become Canonical.

Required inputs: Draft report, validation verdict, existing latest artifacts,
quarantine history, phase identity, metadata, report trust, and push state.

Expected target: Certified report promoted to Canonical/latest or noncanonical
blocked/quarantined state.

Invariants: canonical promotion eligibility, single canonical transition
authority, single identity source, report trust, no canonical artifact
promotion when blocked, and notification certification.

Accepted outcome: latest artifacts are written atomically by the single
promotion path.
Reject outcome: latest artifacts are untouched; no partial overwrite.
Quarantine outcome: artifact is stored in quarantine and never promoted.
Human-review outcome: latest artifacts are untouched pending explicit
approval.

### 4.5 Phase-Completion Metadata

Current behavior: metadata is read by lifecycle paths and has historically
been a source of stale phase/commit/test-result defects when reused across
phases.

Proposed validated behavior: metadata is an input to transition validation,
not a canonical authority by itself. A single reader loads it once for a
transition and compares it against active task, phase identity, commits, test
results, and recommended next phase.

Required inputs: metadata JSON, active task contract, resolved phase identity,
git commits, test evidence, and project status.

Expected target: metadata either matches the transition and can contribute to
the draft, or is rejected/quarantined as stale or inconsistent.

Invariants: phase identity consistency, metadata consistency, commit lineage,
test result consistency, recommended-next-phase consistency, and report
completeness.

Accepted outcome: metadata participates in Draft report construction.
Reject outcome: metadata is ignored for canonical writes; command fails with a
specific stale/inconsistent metadata diagnostic.
Quarantine outcome: suspicious metadata-linked draft is retained for review.
Human-review outcome: ambiguous metadata requires operator choice before
retry.

### 4.6 `pcae push check`

Current behavior: evaluates push readiness and phase report trust before
publication.

Proposed validated behavior: push is a `push` transition over current
repository state. It must confirm that the latest report is Certified,
Canonical, trusted, current for the commits being pushed, and not produced by
an alternate promotion path.

Required inputs: `origin/main..HEAD`, latest report JSON/MD, report trust,
project status, task state, git status, and notification state.

Expected target: push-ready state only when canonical artifacts are trusted and
consistent with commits.

Invariants: push state consistency, report trust, commit lineage, phase
identity consistency, no canonical promotion when blocked, and notification
eligibility where applicable.

Accepted outcome: push check passes.
Reject outcome: push check fails with invariant diagnostics.
Quarantine outcome: untrusted report is marked noncanonical for operator
inspection without pushing.
Human-review outcome: push remains blocked until an operator resolves the
reported ambiguity.

### 4.7 `pcae notify send-report`

Current behavior: manual resend can send the latest report and is deliberately
not idempotency-blocked by 113V.N.

Proposed validated behavior: manual resend remains explicit, but notification
content must still reference a Certified, Canonical, trusted latest report.
The command proposes a `notify` transition with a manual-resend flag.

Required inputs: latest report, report trust, push state, notification marker,
transport status, and operator intent.

Expected target: external notification referencing only canonical certified
state.

Invariants: notification certification, notification eligibility,
transport-enabled status, report trust, and single final notification except
where a distinct manual-resend transition is explicitly approved.

Accepted outcome: send proceeds and records dispatch evidence.
Reject outcome: no send; diagnostic explains the failed certification or
transport invariant.
Quarantine outcome: report is retained but not sent when trust is suspicious.
Human-review outcome: resend pauses if it would resemble a duplicate final
notification without clear operator intent.

### 4.8 Phase-Finalization Skill

Current behavior: `pcae skill invoke phase-finalization` is a read-only target
preview and does not dispatch Telegram or finalize reports.

Proposed validated behavior: keep it read-only. If it later becomes a guided
finalization workflow, it must produce transition proposals only and call the
same lifecycle validation path as direct commands.

Required inputs: target phase ID, live report lookup, project status, metadata,
and skill invocation intent.

Expected target: no canonical mutation for preview mode; future workflow mode
must delegate to `complete_phase` validation.

Invariants: target resolution, phase identity consistency, no command bypass,
and no execution availability.

Accepted outcome: preview succeeds or future workflow delegates to validated
transition.
Reject outcome: invalid target or unsupported mutation path fails without
state changes.
Quarantine outcome: not applicable to current read-only preview; future
workflow may quarantine generated drafts.
Human-review outcome: ambiguous target or phase state requires explicit
operator choice.

### 4.9 Future Automation, Scheduler, and Agent-Driven Workflows

Current behavior: no automation path is allowed to mutate canonical lifecycle
state outside existing commands.

Proposed validated behavior: every future automation path creates the same
`ProposedTransition` objects as human-invoked commands and receives the same
four verdicts. Agent identity is not a validator input.

Required inputs: the same authoritative repository state required by the
equivalent command, plus an audit record of the proposer and trigger.

Expected target: identical to the equivalent direct command target.

Invariants: all invariants for the equivalent lifecycle command, plus no
alternate identity/promotion/metadata source.

Accepted outcome: validated state change through shared path.
Reject outcome: no canonical mutation.
Quarantine outcome: proposed artifact retained for review only.
Human-review outcome: automation stops and waits for explicit operator
approval.

## 5. Implementation Order

Recommended implementation order is confirmed:

1. `pcae phase complete`
2. report promotion/latest artifacts
3. `pcae task finish --commit`
4. notification dispatch
5. `pcae push check`
6. cross-agent verification

Evidence: `pcae phase complete` is the authoritative phase lifecycle
boundary and already has the richest identity/trust context. Report
promotion must follow immediately because it is the canonical write surface
shared by every path. `pcae task finish --commit` comes next because 113S and
113T identified it as the second existing writer and the source of the
two-path asymmetry. Notification dispatch must wait until canonical
certification is centralized, because notifications must reference only
Certified/Canonical reports. `pcae push check` then consumes the certified
state. Cross-agent verification comes last because it should exercise the
integrated paths rather than define them.

## 6. Single Canonical Promotion Path

Future PCAE must have one promotion path for:

- `.pcae/phase-reports/latest.json`
- `.pcae/phase-reports/latest.md`
- `.pcae/phase-completion-metadata.json` consumption during finalization
- notification event eligibility

The path is:

1. Read authoritative repository state once.
2. Generate a Draft report.
3. Validate Draft plus expected target state.
4. On `accept`, mark the report Certified.
5. Promote Certified to Canonical/latest through one writer.
6. Evaluate notification eligibility against the Certified/Canonical report.
7. Record dispatch idempotency after a successful send.

No command may write `latest.*`, consume metadata for canonical promotion, or
declare notification eligibility through a separate path.

## 7. Compatibility Constraints

Integration must preserve existing successful lifecycle flows. Each command
path should be integrated behind focused tests, with no broad behavior change
until that path is validated. The first integrated path may add diagnostics
and stricter blocking only where the invariant is already a documented
contract requirement. Existing clean phase-completion, task-finish,
notification, and push workflows must remain clean when their repository
state is consistent.

## 8. Failure Behavior

Reject means the command exits non-zero, writes no canonical artifact, updates
no project memory, sends no notification, and prints invariant-specific
diagnostics.

Quarantine means PCAE retains the suspect draft or evidence in a quarantine
location, exits non-zero, does not overwrite `latest.*`, does not update
canonical project memory, and sends no normal completion notification.

Requires human review means PCAE writes or references a review-required
diagnostic record, exits non-zero, performs no canonical mutation, and waits
for explicit operator approval or correction before retry.

Accept means the transition proceeds through the single canonical path and
records enough diagnostics to prove which invariants were satisfied.

Exit-code behavior must be stable: `accept` returns success; `reject`,
`quarantine`, and `requires_human_review` return failure for lifecycle
commands and push checks. Read-only preview commands may return success when
they report a non-mutating diagnostic, but they must not imply canonical
acceptance.

## 9. DeepSeek Containment Scenarios

PCAE must prevent these concrete failure classes:

- stale commits in a report
- wrong phase ID
- missing `recommended_next_phase`
- malformed or unstructured test results
- duplicate Telegram reports from repeated lifecycle commands
- silent missing Telegram report when a final report was eligible
- stale phase-completion metadata reused across phases
- report from the wrong phase
- Architecture Status overclaim
- push with an untrusted report

For each scenario, DeepSeek or another agent may still propose the content or
transition. PCAE must reject, quarantine, or require human review before any
invalid state becomes canonical.

## 10. Next Contract Phase

Recommended next phase: 113X — Repository Transition Validator Integration
Contract.
