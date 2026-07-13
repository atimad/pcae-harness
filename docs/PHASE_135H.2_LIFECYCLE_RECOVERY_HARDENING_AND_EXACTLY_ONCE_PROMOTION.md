# Phase 135H.2 — Lifecycle Recovery Hardening and Exactly-Once Promotion

## Executive summary

Phase 135H.2 independently reproduced the lifecycle weakness recorded by
135H.1 and repaired it at the production entry-point and transaction
boundaries. The defect was not in `promote_artifact()` and not in the shared
finalization transaction. It was a caller-owned fallback in `pcae phase-report
create`: when `validate_finalization_gate()` returned false, the command
skipped `run_finalization_transaction()` and directly called the same closure
that wrote the timestamped report, updated `latest.md`/`latest.json`, and then
attempted notification. Notification correctly rejected an incomplete report,
but promotion had already occurred.

The same authority leak existed in two adjacent forms: `pcae task finish`
called `finalize_phase_report()` without passing its failed gate when it fell
outside the transaction, and `pcae phase complete --allow-partial-report`
removed the gate before writing. All three now preserve the same invariant:

> A candidate that has not passed the full finalization gate can be persisted
> only as noncanonical quarantine evidence. It can never call the promotion or
> dispatch adapter.

Gate-passing candidates still use the shared finalization transaction. The
transaction now durably records `promotion_and_dispatch: in_progress`
immediately before entering its irreversible adapter. If the process stops in
that uncertainty window, automatic replay returns
`promotion_outcome_unconfirmed` and never invokes the adapter again. This
changes recovery from “retry and hope the side effect did not happen” to
“observe and reconcile; never duplicate an irreversible effect.”

The phase also adds `pcae phase-report reconcile --phase-id ...`, a public,
read-only reconciliation surface. It requires the promoted report digest and
finalization snapshot to agree with the marker and completed checkpoint, and
requires the checkpoint-bound receipt to exist, identify the same phase, and
be finalized. A marker alone never produces `reconciled`. The command performs
no promotion, dispatch, marker write, checkpoint write, or receipt synthesis.

PFN-001, PFR-001, and CLTR-001 are unchanged. No CLTR production authority was
introduced. Runtime remains `Observed`, maximum capability remains `observe`,
and execution remains unavailable.

## Inputs and independent method

The implementation and verdict were re-derived from:

- Phase 135H's production integration/authority-retirement plan;
- Phase 135H.1's primary artifact inventory and recovery transcript;
- PFN-001 in `docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`;
- PFR-001 in `docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_CONTRACT.md`;
- Track 134's architecture, final integration, transaction-span repair,
  independent verification, marker, receipt, and delivery models;
- Track 135's CLTR authority, state, ordering, retry, marker, and receipt
  invariants;
- current production source for report construction, trust application,
  finalization-gate validation, promotion, notification certification,
  marker persistence, transaction checkpointing, receipt persistence,
  task-finish integration, and paused-task lookup;
- the two retained 135H report generations, the sole 135H marker, completed
  checkpoint, finalized receipt, and canonical latest pointers.

No predecessor conclusion was accepted until the current source path and
hermetic reproduction agreed with it.

## 1. Recovery lifecycle reconstruction

### Ordinary completion

The intended ordinary path is:

`candidate assembled -> canonical/trust assessment -> finalization gate ->`
`transition validation -> notification certification -> transaction checkpoint`
`-> pre-promotion evidence/extraction/view/render certification ->`
`promotion intent persisted -> promotion -> notification -> marker -> receipt`
`-> completed checkpoint`.

Promotion authority begins only after the candidate is complete, the gate is
finalizable, the repository transition is accepted, and the mandatory
pre-promotion transaction stages finish. Notification authority is separately
certified and cannot make an untrusted candidate promotable.

### Failed completion

A failure before certification is `FAILED_PRE_CERT`-equivalent: the candidate
may be retained as an audit attempt, but no canonical path, notification,
marker, or receipt is permitted. A failure after promotion intent is durably
recorded but before its outcome can be confirmed is
`promotion_outcome_unconfirmed`: it is not safe to retry promotion or delivery.
Only observation and reconciliation are allowed.

### Rejected completion

Identity conflict, incomplete trust, failed derived correctness, stale
successor, insufficient No-Go evidence, or any other finalization blocker
produces a rejected/quarantined attempt. The attempt receives a unique
microsecond-and-digest-bound filename under
`.pcae/phase-reports/quarantine/`. It never becomes `latest`, never enters the
finalization transaction, and never reaches notification certification as an
executable delivery transition.

### Recovered completion

Recovery is a new attempt over repaired inputs, not permission to relax the
gate. A fully certified recovery enters the same transaction as ordinary
completion. An identical completed transaction resumes as a no-op. An attempt
whose irreversible adapter may already have started stops as unconfirmed and
must be inspected. A rejected recovery remains quarantine evidence and cannot
be resumed into promotion; repaired evidence creates a new candidate.

### Lifecycle state inventory

| State | Durable representation | Canonical? | Retry rule |
|---|---|---:|---|
| candidate | in-memory `PhaseReport` | no | may be validated |
| rejected | quarantine Markdown/JSON with blockers | no | new attempt only |
| certified | complete trial report plus passing gate | no | transaction may start |
| pre-promotion in progress | transaction checkpoint | no | deterministic resume before irreversible intent |
| pre-promotion failed | failed checkpoint | no | new attempt after repair |
| promotion intent persisted | checkpoint step `promotion_and_dispatch=in_progress` | not inferable | never automatic replay |
| promoted | timestamped generation plus canonical pointers | yes | notification may proceed; promotion never repeats |
| notified | successful dispatch plus marker | yes | never redispatch ordinary completion |
| receipt finalized | immutable receipt bound through checkpoint | yes | no-op inspection/resume |
| completed | completed checkpoint | yes | exact replay returns existing result |

## 2. Promotion authority

Promotion is permitted only when all of the following are true:

1. canonical identity resolves without conflict;
2. `_apply_canonical_and_trust()` classifies the candidate complete;
3. `validate_finalization_gate()` returns `finalizable: true`;
4. repository transition validation accepts the requested lifecycle change;
5. notification payload certification finds no prior-payload conflict;
6. the shared transaction accepts the report digest and finalization snapshot;
7. evidence capture, extraction, both views, and both renderings finish before
   the irreversible adapter is entered.

The authority source is the conjunction of the accepted repository transition,
the passing gate, and the shared transaction state. `write_phase_report()` is
only the mechanical promotion adapter. Notification eligibility, an operator
recovery command, `--allow-partial-report`, a task title, or a marker is not
promotion authority.

The escape occurred in `run_phase_report_create()`'s former `else` branch:

`gate false -> _promote_and_dispatch() -> write_phase_report() -> dispatch check`.

Trust evaluation and gate certification ran before the branch and correctly
said no. Promotion timing nevertheless preceded the notification helper's
second completeness check. The authority leak was therefore caller ordering,
not a missing validation rule.

## 3. Recovery authority

Recovery ownership belongs to the explicitly invoked governed recovery
command, but its authority is limited to constructing a candidate and asking
the same production gate and transaction to evaluate it.

- Inputs: explicit phase identity and report facts, live repository/lifecycle
  projection, trust evidence, commit attribution, tests, governance results,
  No-Go confirmations, push state, and successor.
- Outputs: either quarantine evidence, a transaction result, or an idempotent
  already-dispatched/payload-conflict result.
- Checkpoints: the shared finalization checkpoint is created only for a
  complete, gate-passing report.
- Termination: rejected, pre-promotion failed, promotion outcome unconfirmed,
  promotion/dispatch failed, completed, or exact replay of completed.

Recovery cannot manufacture identity from a paused task. It cannot turn a
marker into a new delivery. It cannot synthesize a successful receipt from an
unconfirmed report. It cannot bypass the transaction to obtain a canonical
write.

## 4. Exactly-once promotion

The repaired rules are:

| Candidate classification | Versioned canonical generation | `latest.*` | Adapter invocation |
|---|---:|---:|---:|
| rejected | never | never | never |
| partial/incomplete | never | never | never |
| failed pre-certification | never | never | never |
| complete and certified | once | once | once |
| completed exact replay | unchanged | unchanged | zero |
| prior adapter outcome unconfirmed | unchanged/observed only | unchanged/observed only | zero |

The transaction's new persisted-intent barrier closes the crash ambiguity that
remained after 134E.10.1. Before the adapter call, the checkpoint is written as
`in_progress`. A retry that sees that state stops. This guarantees at-most-once
adapter entry. Eventual completion is obtained by reconciliation, never by
blind replay.

The original 135H audit history still contains two timestamped promoted
generations: the historical partial candidate and the later trust-complete
candidate. Removing or relabeling the partial would violate the explicit
audit-preservation non-goal. There remains exactly one current canonical 135H
report and one delivered logical completion. Post-135H.2 regression scenarios
prove a rejected attempt creates zero promoted generations and the subsequent
successful recovery creates exactly one. The historic 135H count is disclosed,
not rewritten.

## 5. Audit preservation

| Classification | Meaning | Storage/visibility | May become canonical in place? |
|---|---|---|---:|
| evidence | facts about an attempt | checkpoint, quarantine, tests, logs | no |
| canonical | current trusted report selected by canonical pointers | normal generation plus `latest.*` | already canonical |
| promoted | certified generation written through promotion adapter | normal phase-report generation | no second ordinary promotion |
| historical | prior artifact retained for chronology | normal or quarantine history | no |
| abandoned | attempt intentionally not continued | quarantine/failed checkpoint with reason | no |
| superseded | later governed correction exists | retained original plus explicit later evidence | no mutation |
| rejected | gate/identity/trust did not authorize promotion | quarantine with blockers | never |

`write_quarantined_report()` now uses microseconds and a digest prefix in the
filename. Rapid or identical retries cannot silently overwrite an earlier
attempt. The artifact embeds its blockers and explicitly states that it is not
canonical or trusted.

## 6. Recovery state machine

| Operation | Precondition | Result | Forbidden effect |
|---|---|---|---|
| retry before irreversible intent | same candidate; pre-promotion not complete | safe re-evaluation | promotion before certification |
| replay completed | matching digest + snapshot + completed checkpoint | existing result | callback invocation |
| resume certified | gate complete; no irreversible intent | continue transaction | bypass transaction |
| rejection | gate false or report incomplete | quarantine + nonzero recovery result | canonical write/dispatch |
| abandonment | operator stops rejected/failed attempt | retained evidence | deletion/relabeling |
| supersession | later separately governed correction | explicit new evidence | in-place mutation |
| successful recovery | repaired candidate passes all gates | one promotion and governed delivery | second ordinary completion |
| uncertain promotion outcome | persisted adapter intent without completed step | fail closed, inspect/reconcile | automatic promotion or dispatch replay |

## 7. Marker–receipt relationship

The current production marker remains the ordinary-notification idempotency
derivative. The receipt remains the immutable delivery-model record. The
checkpoint binds both to the same report digest and finalization snapshot.
None replaces the others.

`pcae phase-report reconcile --phase-id PHASE` evaluates:

1. a normal promoted report generation exists and is trust-complete;
2. its computed digest and finalization snapshot match the notification marker;
3. the checkpoint identifies the same phase, digest, and snapshot;
4. the checkpoint is completed;
5. its receipt path exists;
6. the receipt identifies the same phase and is finalized.

Results are `reconciled`, `delivery_recorded_bookkeeping_incomplete`,
`promotion_outcome_unconfirmed`, `not_delivered`, or `conflict`. The command is
read-only by construction and reports `mutation_performed: false` and
`redispatch_performed: false`. This is the deterministic public inspection
model required before any future mutating reconciliation is authorized. It
does not elevate the marker to CLTR authority.

Inspection of the real 135H state returns `reconciled`: matching digest
`bc6f811b...`, snapshot `f544e5e5...`, one completed checkpoint, and one
finalized receipt, with no mutation or redispatch.

## 8. Paused task discovery

`find_latest_active_task()` returns the newest file under `tasks/active`
regardless of the contract's embedded status. That behavior is retained for
general task inspection and backward compatibility. Recovery notification
certification no longer uses it. It now calls
`find_latest_active_task_with_status(..., "active")`.

- Identity source: explicit recovery phase ID and report identity.
- Lifecycle source: current PROJECT_STATUS/lifecycle projection.
- Recovery task source: only a contract whose embedded status is `active`.

A paused task can remain physically under `tasks/active` without contaminating
recovery identity. A focused regression places a mismatching paused task there
and proves a correctly identified recovery still certifies, promotes, and
finalizes.

## 9. Terminal rejection recording

Every gate-failing manual recovery now writes a blocked Markdown and JSON pair
under quarantine and returns nonzero. Each record is:

- immutable by unique microsecond-and-digest identity;
- auditable through embedded phase identity, generated content, and blockers;
- noncanonical because it never touches normal timestamped paths or pointers;
- never promotable in place because quarantine is terminal in the artifact
  promotion state machine;
- available for investigation without being returned by canonical report
  readers.

The ordinary and task-finish paths use the same gate-aware
`finalize_phase_report()` quarantine mechanism. `--allow-partial-report` may
retain its historical command-success semantics, but it no longer removes the
promotion gate or causes notification.

## 10. Compatibility and authority boundary

- PFN-001: unchanged. Exactly-once ordinary notification remains governed by
  notification certification and the marker. The repair only prevents an
  untrusted artifact from being promoted before PFN-001 correctly suppresses
  delivery.
- PFR-001: unchanged. Report content, mandatory sections, and trust contract
  remain intact. The implementation enforces that incomplete PFR evidence
  cannot become canonical.
- CLTR-001: unchanged. No schema, canonical record, production CLTR write,
  read authority, cutover, or compatibility adapter was introduced.
- Artifact-promotion state machine: unchanged. `CERTIFIED -> CANONICAL` remains
  the only promoting transition; `REJECTED` and `QUARANTINED` remain terminal.
- Runtime: unchanged at Observed / observe / execution unavailable.

## Verification

### Reproduced paths

1. Original 135H failure: task closure preceded mixed-identity report
   rejection; transaction/promotion/notification did not begin.
2. Rejected recovery: incomplete/compound evidence fails the gate. Before the
   repair the fallback promoted it; after the repair it creates one quarantine
   attempt and zero normal generations, pointers, markers, checkpoints,
   receipts, or notification calls.
3. Successful recovery: a fully specified candidate passes the real gate,
   enters the transaction, produces one promoted generation, one marker, one
   checkpoint, one finalized receipt, and one notification. Replay is a no-op.
4. Crash-window recovery: a synthetic process stop after adapter entry leaves
   persisted `promotion_and_dispatch: in_progress`; a retry returns
   `promotion_outcome_unconfirmed` and the callback call count remains one.
5. Paused-task recovery: a stale paused task is ignored as an identity source.
6. Public reconciliation: matching report/marker/checkpoint/receipt returns
   `reconciled` without mutation or redispatch.

### Acceptance matrix

| Criterion | Result |
|---|---|
| Exactly one canonical promoted report in repaired successful recovery | PASS |
| Exactly one promoted generation in repaired successful recovery | PASS |
| Exactly one marker | PASS |
| Exactly one completed checkpoint | PASS |
| Exactly one finalized receipt | PASS |
| Exactly one ordinary notification | PASS |
| Rejected candidates never promoted | PASS |
| Rejected candidates remain auditable | PASS |
| Recovery deterministic across reject/replay/uncertain states | PASS |
| Fail-closed behavior preserved | PASS |

Focused lifecycle regression: 369 passed. A full-suite audit initially produced
19752 passes and 26 failures: 23 were obsolete assertions for the intentionally
removed partial-promotion behavior and all affected modules subsequently pass
in focused reruns (439 passed, plus a 101-test supplemental group). The three
remaining failures reproduce independently and predate 135H.2: two legacy tests
require the long-existing `src/pcae/advisory` directory not to exist, and one
legacy rendering test rejects the long-existing word `rendering` in a source
comment. Fast-green: 4391 passed with 105 known collection warnings.
`compileall`, health, check, task-memory, push-check, runtime inspection, and
real 135H read-only reconciliation pass.

## Verdict and next phase

**A — IMPLEMENTED AND VERIFIED.** The remaining 135H.1 promotion-authority
escape is closed. Exactly-once promotion is enforced by gate convergence,
transaction-only adapter entry, completed replay no-op, and uncertainty-stop
semantics. Rejected evidence remains durable and noncanonical.

Phase 135I was not started. The recommended next governed phase remains 135I —
Production CLTR Schema, Canonicalization, and Versioning Contract Freeze.
