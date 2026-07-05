# PCAE Repository Transition Validator — Integration Contract

**Status:** Integration contract frozen. Architecture/contract only — no
implementation.
**Phase:** 113X.
**Extends:** 113S architecture, 113T validator contract, 113U prototype,
113V verification, and 113W integration design.

## 0. Contract Principle

Repository lifecycle commands are transition-request front ends. They do not
own canonical state. The Repository Transition Validator is the mandatory
gateway that certifies whether a requested repository transition may become
canonical.

Frozen rule:

> Model proposes. Repository Transition Validator validates. Only certified
> transitions become canonical.

This is the Model Containment Layer (MCL). It is model-agnostic and applies to
Claude, DeepSeek, Codex, GLM, Qwen, Gemini, humans, future models, future REST,
future schedulers, future automation, and future execution runtimes.

## 1. Lifecycle Integration Contract

Every lifecycle integration point below must become a transition request. No
integration point may directly certify or promote canonical state.

| Integration point | Contracted transition role |
|---|---|
| `pcae phase complete` | Requests `complete_phase`, `report_generation`, `report_promotion`, `status_update`, and downstream `notify` transitions. |
| `pcae task finish --commit` | Requests `finish_task`, `commit`, and any phase-report side-effect through the same report transitions as `phase complete`. |
| report generation | Produces Draft artifacts only; it never writes canonical `latest.*`. |
| report promotion | Requests Draft/Certified to Canonical promotion; only the validator may certify it. |
| canonical `latest.*` | Written only after an Accept verdict and certification. |
| phase metadata | Input to `RepositoryState`; never a standalone authority. |
| notification dispatch | Downstream of certification; no certification means no notification. |
| `pcae push check` | Requests push-readiness validation over Certified/Canonical state. |
| future automation | Must submit the same transition requests as human-invoked commands. |
| future REST | Must be an API front end to the same transition contract, not a second lifecycle engine. |
| future scheduler | May trigger proposals but may not certify them. |
| future execution runtime | May produce evidence/proposals only; execution does not bypass certification. |

## 2. Mandatory Validator Entry Points

### 2.1 `pcae phase complete`

Before validator: resolve canonical phase identity, read active task, read
phase metadata, collect commits, collect validation/test evidence, build Draft
report, read push state, read notification state, read runtime/execution state.

Validator: submit `ProposedTransition(kind=complete_phase)` with nested
`report_generation`, `report_promotion`, `status_update`, and optional
`notify` proposals.

After validator: on Accept, promote Certified report to Canonical/latest,
update phase/project status, then evaluate downstream notification. On Reject,
Quarantine, or Requires Human Review, do not update canonical status or
latest artifacts.

Allowed state changes: Draft artifact creation; Certified to Canonical
promotion after Accept; project memory update after certification; notification
marker update after successful downstream notification.

Forbidden state changes: direct latest overwrite, direct status update,
direct notification dispatch before certification, alternate metadata reader,
or any lifecycle mutation after a non-Accept verdict.

### 2.2 `pcae task finish --commit`

Before validator: read active task, staged/unstaged scope, candidate commit,
phase identity if phase side effects are present, metadata, report draft,
push state, and notification marker.

Validator: submit `finish_task` and `commit` proposals; any report side effect
must submit the shared `report_generation`/`report_promotion` proposals.

After validator: on Accept, create governed commit and move task contract. If
phase report side effects are accepted, they use the same canonical promotion
path as `pcae phase complete`.

Allowed state changes: task contract move, governed commit, shared report
promotion after certification.

Forbidden state changes: independent latest writes, metadata-only report
promotion, notification dispatch from uncertified reports, or hidden task
closure after Reject/Quarantine/Human Review.

### 2.3 Report generation

Before validator: gather phase identity, metadata, commits, test results,
governance results, architecture status, recommended next phase, and no-go
confirmations.

Validator: submit `report_generation` with `ExpectedTargetState` describing a
Draft report.

After validator: Draft may be retained for promotion validation only.

Allowed state changes: Draft artifact materialization.
Forbidden state changes: canonical promotion, latest overwrite, notification,
or project-status update.

### 2.4 Report promotion and canonical `latest.*`

Before validator: read Draft report, current latest artifacts, quarantine
history, phase identity, report trust, metadata, commit lineage, and push
state.

Validator: submit `report_promotion` with `ExpectedTargetState` =
Certified/Canonical report.

After validator: Accept certifies and promotes to `latest.json`/`latest.md`;
Quarantine stores the artifact outside latest; Reject blocks promotion; Human
Review pauses promotion.

Allowed state changes: atomic `latest.*` write after Accept.
Forbidden state changes: partial latest overwrite, non-Certified promotion,
second writer, or command-owned certification.

### 2.5 Phase metadata

Before validator: read `.pcae/phase-completion-metadata.json` exactly once for
the transition and compare it with active task, phase identity, commits, tests,
and recommended next phase.

Validator: metadata is part of `RepositoryState`; it is not a transition
authority.

After validator: metadata may contribute to a Draft only if consistent.

Allowed state changes: none from metadata alone.
Forbidden state changes: metadata-driven latest promotion, stale metadata
reuse, partial metadata patching as certification, or metadata as identity
fallback outside the single identity chain.

### 2.6 Notification dispatch

Before validator: read Certified/Canonical report, notification marker,
transport configuration, push state, and operator intent for manual resend.

Validator: submit `notify` after certification.

After validator: send only after Accept and write idempotency marker only after
successful dispatch.

Allowed state changes: external notification and dispatch marker after
certified Accept.
Forbidden state changes: notification before certification, duplicate final
notification, notification for Draft/Blocked/Quarantined reports, silent skip
when eligibility was true.

### 2.7 `pcae push check`

Before validator: read git status, `origin/main..HEAD`, latest report,
project status, task state, report trust, notification state, and runtime
state.

Validator: submit `push` readiness proposal.

After validator: Accept reports ready; non-Accept blocks push readiness.

Allowed state changes: none; this remains read-only.
Forbidden state changes: push authorization based on untrusted report,
promotion during push check, or any mutation from read-only check.

### 2.8 Future automation, REST, scheduler, and execution runtime

Before validator: normalize the external trigger into the same
`ProposedTransition` shape as CLI commands and read the same `RepositoryState`.

Validator: submit the equivalent command transition. Agent identity is audit
metadata only and cannot affect certification.

After validator: route through the same Accept/Reject/Quarantine/Human Review
outcomes.

Allowed state changes: only those allowed for the equivalent CLI transition.
Forbidden state changes: alternate REST lifecycle engine, scheduler-owned
certification, runtime-owned certification, model-owned certification, or
identity-based bypass.

## 3. Canonical Authority

Frozen:

- No lifecycle command owns canonical state.
- Commands request transitions.
- The Repository Transition Validator certifies transitions.
- Only Certified artifacts may become Canonical/latest.
- `latest.json`, `latest.md`, project status, phase metadata consumption, push
  readiness, and notification eligibility must all derive from the certified
  transition result.
- There is one canonical promotion path and one certification authority.

## 4. Model Containment Layer Contract

The Model Containment Layer is frozen as:

1. Models never modify canonical state.
2. Models propose transitions.
3. The validator certifies transitions.
4. Repository changes only after certification.
5. Agent identity never influences certification.

The same contract applies to Claude, DeepSeek, Codex, GLM, Qwen, Gemini,
human operators, future automation, future REST, future schedulers, and future
execution runtimes. Identity may be recorded for audit, attribution, and
review, but not for verdict selection.

## 5. Transition Pipeline

The frozen pipeline is:

1. **Proposal** — command/model/operator creates a `ProposedTransition`.
2. **Validation** — PCAE constructs authoritative `RepositoryState` and
   `ExpectedTargetState`, then calls the validator.
3. **Certification** — only an Accept verdict can certify the target state.
4. **Promotion** — Certified artifacts may be promoted to Canonical/latest.
5. **Notification** — notifications are downstream of certification.
6. **Completion** — lifecycle/task/project memory advances after certified
   promotion.
7. **Rollback eligibility** — rollback may be evaluated only from certified
   transition evidence; rollback readiness is not execution permission.

Reject, Quarantine, and Requires Human Review are terminal for canonical
mutation until a new proposal or explicit human-reviewed retry is submitted.

## 6. Integration Invariants

| Lifecycle command | Required RepositoryState | Required ProposedTransition | Required ExpectedTargetState | Required invariants | Verdict mapping |
|---|---|---|---|---|---|
| `pcae phase complete` | active task, phase identity, metadata, commits, tests, governance, draft report, push state, notification state, runtime/execution state | `complete_phase` + `report_generation` + `report_promotion` + `status_update` + optional `notify` | completed phase, Certified/Canonical report, updated status, eligible notification | phase identity, metadata, commit lineage, report completeness/trust, test consistency, architecture status, recommended next phase, push state, notification eligibility, no execution availability, single authority | Accept promotes; Reject blocks; Quarantine stores draft; Human Review pauses |
| `pcae task finish --commit` | active task, file scope, candidate commit, phase side-effect state if present | `finish_task` + `commit` + shared report transitions if needed | done task, governed commit, optional Certified report | active task, allowed scope, commit lineage, phase identity, metadata, report trust, notification idempotency | Accept closes/commits; others block or pause |
| report generation | identity, metadata, commits, tests, governance, architecture status | `report_generation` | Draft report | report completeness, metadata consistency, test consistency, commit lineage | Accept creates Draft; others block/hold/quarantine |
| report promotion / `latest.*` | Draft, current latest, trust, quarantine history, push state | `report_promotion` | Certified/Canonical report | canonical promotion eligibility, single authority, report trust, no blocked promotion | Accept writes latest; others never overwrite latest |
| phase metadata | metadata file plus identity/task/commit/test cross-check state | metadata input to parent transition | consistent metadata contribution | metadata consistency, identity consistency, commit lineage, recommended next phase | Accept uses metadata; others ignore/quarantine/hold |
| notification dispatch | Certified report, marker, push state, transport config | `notify` | sent notification + marker | notification certification, eligibility, idempotency, transport enabled | Accept sends once; others do not send |
| `pcae push check` | git status, origin delta, latest report, trust, status, task, runtime | `push` | push-ready read-only result | push state, report trust, phase identity, commit lineage | Accept ready; others not ready |
| future automation/REST/scheduler/runtime | equivalent command state plus trigger audit metadata | equivalent command transition | equivalent command target | equivalent command invariants plus no identity bypass | same four verdict meanings |

## 7. Command Compatibility

Future integration must preserve:

- existing CLI UX and command names
- existing report formats and report paths
- existing governance health/check semantics
- existing Runtime Snapshot behavior
- existing Runtime Inspect output
- existing Advisory Runtime behavior

Integration may add diagnostics and fail-closed blockers where the frozen
contract requires them, but it must not silently change successful clean-path
outputs without a dedicated implementation phase and tests.

## 8. Notification Integration

Frozen:

- Notification is downstream of certification.
- No certification means no notification.
- Certification occurs once for a transition.
- Final notification occurs once for a certified phase.
- A notification may reference only a Certified/Canonical report.
- Manual resend is a distinct operator-requested `notify` transition and must
  still validate report certification.

## 9. Future Enforcement Order

Frozen roadmap:

1. 113Y — Repository Transition Validator Integration: Phase Completion
2. 113Z — Repository Transition Validator Integration: Task Finish
3. 114A — Report Promotion / Quarantine Hardening
4. 114B — Notification Enforcement
5. 114C — Push/Check Integration
6. 114D — Cross-Agent Verification
7. 114E — Model Containment Drill

## 10. No-Go

This phase does not implement integration. It does not modify lifecycle
command behavior, report promotion behavior, notification dispatch behavior,
push behavior, Runtime Snapshot, Runtime Inspect, Advisory Runtime, Permission
Broker enforcement, execution, authorization, plugins, Telegram inbound, REST,
Web UI, Dashboard, tags, releases, or package publication.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## 11. Next Phase

113Y — Repository Transition Validator Integration: Phase Completion.
