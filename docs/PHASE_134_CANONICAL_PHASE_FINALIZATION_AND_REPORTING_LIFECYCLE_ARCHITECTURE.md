# Phase 134A — Canonical Phase Finalization & Reporting Lifecycle Architecture

## 1. Purpose

This phase defines the future authoritative architecture for the complete PCAE
phase-finalization lifecycle: from the moment engineering work stops through
evidence capture, canonicalization, derived reporting, rendering, delivery,
operator confirmation, repository validation, and official governed phase
completion.

The existing lifecycle is functionally correct and contains strong, proven
mechanisms. Its weakness is not absence of governance, but distribution of
authority and ordering across task completion, phase completion, push
reconciliation, report sidecars, promotion, and notification paths. This
architecture unifies those responsibilities conceptually before executable
Canonical Engineering Evidence is introduced.

This is architecture only. No implementation, schema, code, test, report,
notification, runtime, or execution behavior changes.

## 2. Architectural Direction

The authoritative lifecycle is:

```text
Engineering Activity
        ↓
Engineering Completion Boundary
        ↓
Engineering Evidence Capture
        ↓
Canonical Engineering Evidence Finalization
        ↓
Derived Evidence View Generation
        ↓
Rendering
        ↓
Repository and Governance Validation
        ↓
Delivery Certification
        ↓
Delivery Adapters
        ↓
Operator Delivery Confirmation
        ↓
Governed Phase Completion
```

The sequence is evidence-first and transport-independent. Official completion
is a terminal lifecycle state, not an early command-side effect. No stage may
claim the authority of another, and no alternative path may bypass a required
stage.

## 3. Current-State Re-Derivation

The current source implements the lifecycle through several cooperating
mechanisms:

- `pcae task finish` and `pcae phase complete` are separate orchestration
  entry points;
- canonical phase identity is resolved in fixed precedence order from active
  task, completion metadata, active lifecycle text, then explicit CLI identity;
- `.pcae/phase-completion-metadata.json` carries structured completion facts,
  while `.pcae/phase-completion-report.md` carries canonical companion prose;
- live git state reconciles stale declared push state;
- the Repository Transition Validator certifies lifecycle transitions;
- phase-report trust and finalization gates validate report completeness;
- canonical artifact promotion alone updates `latest.*`;
- notification certification evaluates canonical/trusted/push-clean/
  configured/not-already-dispatched conditions;
- dispatch markers provide logical idempotency;
- the governed push path reruns post-push reconciliation because task closure
  necessarily creates an unpushed commit before final push.

These mechanisms remain valid inputs to 134D planning. The target architecture
does not discard them. It removes conceptual ambiguity about which stage owns
each decision and when completion becomes official.

## 4. Architectural Responsibilities by Stage

### 4.1 Engineering Activity

Owns the governed work: investigation, decisions, implementation or
documentation, tests, checks, and repository changes. It produces observable
facts but is not itself a report or evidence artifact.

It must not declare itself complete, author transport payloads, or promote
canonical artifacts.

### 4.2 Engineering Completion Boundary

Closes the mutation window for the phase's intended work and establishes the
candidate finalization scope: phase identity, task lineage, intended files,
commits, validations, explicit non-changes, and recommended next phase.

Crossing this boundary means “engineering work is ready for evidence
finalization,” not “the phase is officially complete.” Any subsequent repair
is a separately governed finalization repair and becomes additional evidence.

### 4.3 Engineering Evidence Capture

Captures phase facts from their authoritative sources. It preserves source
attribution, uncertainty, limitations, observed absence, timing, and phase
ownership without summarizing or interpreting them.

Required evidence:

- canonical phase/task identity and lineage;
- engineering actions, decisions, findings, repairs, and explicit non-actions;
- architectural and implementation impact;
- verification and test evidence;
- governance results;
- technical-debt disposition and notable engineering knowledge;
- repository state and phase-owned commits;
- runtime state and execution availability;
- recommended next phase and no-go confirmations.

Optional evidence includes non-authoritative supporting diagnostics,
screenshots, external references, extended logs, timing details beyond approved
timestamps, and supplemental artifacts. Optional evidence is explicitly marked
and can never substitute for required evidence.

Capture begins during engineering activity, closes at canonical evidence
finalization, and may reopen only through a governed correction lifecycle.

### 4.4 Canonical Engineering Evidence Finalization

Track 133 is authoritative for this stage. Exactly one validated, immutable
Canonical Engineering Evidence record represents what happened in the phase.
This stage normalizes, validates, canonicalizes, and finalizes evidence. It does
not summarize, render, dispatch, infer, or become a reporting layer.

134A does not redesign its model, lifecycle, persistence, correction,
determinism, or Derived Correctness contracts.

### 4.5 Derived Evidence View Generation

Track 133 remains authoritative for derived views. Phase Report, Operator
Report, changelog, milestone, release, and future views are deterministic,
faithful projections of the finalized canonical record. Content selection and
disclosed filtering belong here; delivery-channel behavior does not.

All required views for a phase must be generated and pass Derived Correctness
before rendering begins. A view failure blocks or durably fails finalization
according to the future 134B contract; it never silently produces a thinner
substitute.

### 4.6 Rendering

Rendering transforms a validated view into Markdown, plain text, JSON, HTML,
or another presentation format. It changes presentation only. It cannot select
engineering content, strengthen conclusions, obscure uncertainty, drop
limitations, reorder semantic content outside the view policy, or call a
transport.

Rendered artifacts carry canonical-record identity, view identity/version,
format/version, digest, ordering, completeness, and traceability manifests.

### 4.7 Repository and Governance Validation

Validates the final repository and governance facts used for completion:
working-tree cleanliness, phase-owned commits, upstream relation, task memory,
policy health, lifecycle identity, report trust, runtime posture, and required
artifact existence. Live repository state is authoritative over stale declared
state whenever determinable.

This stage certifies state; it does not create evidence facts retroactively,
render reports, or deliver messages. A post-push validation result is a required
input to delivery certification and official completion.

### 4.8 Delivery Certification

Determines whether each required rendered artifact may be delivered. It checks
canonical/view/render trust, repository-final state, configured required
destinations, idempotency identity, prior delivery outcome, and applicable
PFN-001 policy. Certification neither transports nor changes content.

### 4.9 Delivery Adapters

Adapters own channel-specific escaping, segmentation, message/document choice,
retry mechanics, rate limits, and transport calls. Telegram is the first
adapter. Email, Slack, Teams, Discord, dashboard, push, API, and future
transports are peers.

Adapters never gain engineering authority, choose evidence, summarize views,
alter findings, or report success after silent truncation.

### 4.10 Operator Delivery Confirmation

Produces an append-only delivery receipt for every required logical delivery.
A receipt links canonical record, derived view, rendered artifact digest,
adapter/destination class, ordered attempts, segment outcomes, timestamps,
final disposition, and acknowledgement when the transport supports it.

Delivery confirmation has four terminal/continuing outcomes:

- **success** — every required unit accepted by the transport and a durable
  receipt persisted;
- **retryable failure** — policy permits another ordered attempt and completion
  remains pending;
- **durable failure** — retry policy is exhausted or failure is permanent;
  failure evidence and unsent units are durably persisted;
- **acknowledged** — optional stronger confirmation that a channel/operator
  acknowledged receipt; it never replaces transport success unless a future
  explicit policy requires acknowledgement.

Attempts are ordered and idempotent. Exactly-once is logical, not a claim that
an external network performs exactly-once physical transmission.

### 4.11 Governed Phase Completion

Official completion is recorded only after:

1. canonical engineering evidence is finalized;
2. every required derived view is generated and validated;
3. every required rendering is complete and validated;
4. repository and governance state are certified final;
5. required deliveries either succeed or reach a policy-approved durable
   failure with complete failure evidence;
6. delivery receipts are persisted;
7. one completion transition is atomically recorded.

A durable delivery failure may permit official completion only when PFN-001 and
the future 134B contract explicitly define that failure disposition as terminal
and operator-visible through a governed recovery surface. It can never be
silently treated as success.

## 5. Canonical Authority Model

Every concern has exactly one authority:

| Concern | Canonical authority | Derived/read-only consumers |
|---|---|---|
| Phase identity | Governed phase lifecycle record bound to the active/completing task lineage | Evidence, reports, validators, adapters |
| Engineering evidence | Finalized Canonical Engineering Evidence record (Track 133) | All derived views and audits |
| Repository state | Live VCS state for the governed repository and configured upstream | Evidence capture, validation, reports |
| Governance state | Validated PCAE governance/task/session/policy state | Evidence and completion decision |
| Runtime state | Runtime Registry/Introspection result | Evidence and reports |
| Report content | Appropriate validated Derived Evidence View; PFR-001 governs Phase Report content | Renderers and delivery |
| Rendered representation | Validated renderer output bound to a view digest | Delivery adapters |
| Notification status | Append-only delivery receipt ledger | PFN status, reports, audits |
| Completion status | Single governed phase lifecycle transition record | Project status, handoff, history |
| Repository knowledge | Repository Intelligence authoritative artifacts | Evidence may reference, never absorb authority |

Sidecars, command summaries, project-memory prose, Telegram messages,
changelog entries, and `latest.*` pointers are projections or indexes. None is
an independent authority.

## 6. Lifecycle State Model

The conceptual state machine is:

```text
Active
  → Engineering Ready
  → Evidence Draft
  → Evidence Finalized
  → Views Validated
  → Renderings Validated
  → Repository Certified
  → Delivery Certified
  → Delivery Pending
  → Delivery Terminal (Succeeded | Durably Failed)
  → Completed
```

Failure before `Evidence Finalized` returns to a governed draft/correction
state. Failure after finalization never mutates canonical evidence; it creates
new validation, rendering, delivery, or correction artifacts. `Completed` is
terminal except for an explicitly governed correction that preserves the
original transition and its history.

## 7. Lifecycle Invariants

1. **Single phase identity:** every stage uses one bound identity; no parsing
   from free-text summaries and no competing precedence at consumption time.
2. **Single engineering record:** exactly one effective finalized canonical
   record per phase, with append-only governed correction history.
3. **Deterministic lifecycle:** equivalent inputs and state produce equivalent
   artifacts, decisions, and ordering modulo approved timestamps and external
   transport response data.
4. **Exactly-once logical completion:** one phase identity can acquire one
   effective completion transition; retries observe it rather than duplicate it.
5. **Exactly-once logical operator report:** one canonical/view/render identity
   maps to one logical required delivery; physical retries share that identity.
6. **Evidence before views:** no derived view precedes finalized canonical
   evidence.
7. **Views before rendering:** no renderer selects or reconstructs content.
8. **Rendering before delivery:** no adapter authors presentation content.
9. **Repository-final before completion:** live final repository state is
   certified after the final governed commit and push.
10. **No silent omission:** evidence, views, renderings, segments, failures, and
    retries preserve completeness or explicitly disclose exclusions/loss.
11. **No strengthening or reinterpretation:** downstream layers preserve
    uncertainty, limitations, classifications, and authority.
12. **No duplicate promotion:** canonical indexes are updated through one
    certified promotion path.
13. **No duplicate completion:** task closure, report promotion, notification,
    and phase completion cannot independently claim official completion.
14. **No authority leakage:** sidecars, views, renderings, adapters, receipts,
    and consumers never become engineering authorities.
15. **Transport independence:** evidence, views, rendering, validation, and
    completion policy do not depend on Telegram or any adapter implementation.
16. **Failure visibility:** a required delivery or promotion failure is durable,
    classified, traceable, and never converted into success by omission.
17. **Historical preservation:** existing completed phases and reports are not
    rewritten to simulate the future lifecycle.

## 8. Ordering, Retry, and Acknowledgement Architecture

The finalization orchestrator assigns one lifecycle transaction identity and
persists each accepted stage transition. Retrying resumes from the last durable
state; it does not rerun already accepted logical stages without checking their
artifact identities and digests.

Delivery order follows the view/render manifest. Multi-part messages use stable
part numbers and total counts. A retry targets only units not durably confirmed
unless the adapter requires replay; replay retains the same logical delivery
identity and is recorded explicitly.

Transport acknowledgement means acceptance by the transport API. Operator
acknowledgement, when available, is a separate optional receipt event. PCAE
does not infer human receipt from transport success.

## 9. Report Promotion and Completion Architecture

Promotion updates the canonical report index only from a certified rendered
Phase Report artifact. It occurs after evidence/view/render validation and
before delivery certification, but it does not itself mark the phase complete.
Quarantined or rejected artifacts never replace canonical `latest.*`.

Completion is recorded after terminal delivery disposition and final
repository certification. The architecture eliminates the current conceptual
cycle in which task closure creates the final commit, push is needed for trust,
and post-push reconciliation must rerun report promotion. 134D must plan an
ordered transaction that preserves commit/push truth without prematurely
closing the phase; 134A does not choose its executable mechanism.

## 10. Known Technical Debt Classification

| Debt | Track 134 disposition | Rationale |
|---|---|---|
| Stale completion metadata | **Owned** | Competing/manual phase and trust facts conflict with single-authority lifecycle |
| Historical report-generation ordering | **Owned** | Directly concerns finalization transaction ordering |
| Report informational completeness | **Integrated dependency** | PFR-001/Track 133 own content rules; Track 134 owns when validation gates completion |
| Architecture status generation | **Owned at lifecycle boundary** | Status must consume canonical completion/repository truth, not independently infer phase state |
| Duplicate phase identity paths | **Owned** | One identity authority and binding event are core 134 invariants |
| Notification coupling to report/sink code | **Owned** | Delivery certification/adapters/receipts require separation |
| Report promotion sequencing | **Owned** | Promotion and completion ordering are core lifecycle responsibilities |
| Canonical state determination | **Owned** | One lifecycle state machine must replace command-local completion claims |
| Thin current report model | **Not repaired by 134A** | PFR-001/Track 133 implementation dependency; Track 134 only composes its gate |
| Manually maintained completion sidecars | **Owned migration debt** | May remain compatibility inputs temporarily, but cannot remain canonical authorities |
| Physical exactly-once external delivery | **Not solvable/claimed** | Architecture guarantees logical idempotency and recorded attempts only |

No debt is repaired in this phase. Historical artifacts remain valid.

## 11. Compatibility Assessment

### Runtime Governance

Compatible and unchanged. Finalization consumes validated governance/runtime
state and grants no execution authority. Runtime remains `Observed`, maximum
capability `observe`, execution unavailable.

### Repository Intelligence and Service

Compatible and independent. Repository Intelligence answers what is true about
the repository; evidence records what happened during engineering. Finalization
may reference Repository Intelligence artifacts but cannot create, mutate, or
supersede their knowledge authority. The Service remains a read-only consumer.

### Canonical Engineering Evidence

Track 133 is incorporated without redesign. 134A supplies the surrounding
phase-finalization lifecycle and official completion ordering, not a competing
evidence model.

### PFR-001

PFR-001 remains the Phase Report View content contract. Track 134 determines
when the validated PFR view is generated, rendered, promoted, and considered
sufficient for completion. It does not alter the thirteen sections.

### PFN-001

PFN-001 remains mandatory and governs finalization notification delivery.
Track 134 generalizes delivery certification, adapter execution, receipts,
retry, durable failure, and ordering while preserving PFN-001's no-silent-
omission, trust-before-dispatch, idempotency, and operator-visibility rules.

## 12. Governance and Failure Policy

All stage transitions are fail-closed, source-attributed, explainable, and
auditable. A validator produces classification and evidence, not authority to
repair. Human overrides, if a future contract permits them, are explicit
governed transitions with durable reasons and cannot fabricate delivery or
evidence success.

No network action occurs before delivery certification. No adapter failure
rolls back immutable canonical evidence. No completion failure erases already
persisted evidence, views, renderings, promotion diagnostics, or receipts.

## 13. Future Track 134 Roadmap

Repository inspection supports the proposed six-phase sequence:

- **134A — Architecture:** this document.
- **134B — Contract Freeze:** bind stages, authorities, state transitions,
  invariants, failure semantics, PFN/PFR integration, and non-goals.
- **134C — Independent Verification:** re-derive contract completeness and
  compatibility from source and prior contracts.
- **134D — Lifecycle Implementation Plan:** map the verified architecture onto
  current commands, sidecars, validators, promotion, push reconciliation,
  notification certification, and migration/rollback steps.
- **134E — Lifecycle Implementation:** implement only the verified plan with
  compatibility gates and shadow/migration behavior where required.
- **134F — Independent Verification:** verify the complete lifecycle,
  idempotency, failure/retry behavior, transport independence, canonical
  authorities, migration, PFN-001, and terminal repository state.

No additional architecture phase is necessary. 134B is the smallest safe next
step because implementation planning must be measured against a frozen and
independently verified lifecycle contract.

## 14. Non-Goals and Boundary Confirmation

Phase 134A does not:

- implement or modify lifecycle behavior;
- modify reporting or notification code;
- define an executable schema;
- implement Canonical Engineering Evidence or derived views;
- modify PFR-001 or PFN-001;
- modify Repository Intelligence or its Service;
- change phase identity, metadata, promotion, push, retry, or adapter code;
- introduce an event bus, execution planning, execution capability, runtime
  plugin, provider integration, or inbound operator control;
- rewrite historical reports or completion records;
- begin 134B.

## 15. Expected Final State and Recommended Next Phase

The authoritative lifecycle architecture, canonical authority model, stage
responsibilities, state model, invariants, delivery confirmation model, debt
classification, compatibility assessment, and roadmap are complete.

Recommended next phase: **134B — Canonical Phase Finalization & Reporting
Lifecycle Contract Freeze**.

No implementation occurred. Runtime remains `Observed`; maximum plugin
capability remains `observe`; execution remains unavailable.
