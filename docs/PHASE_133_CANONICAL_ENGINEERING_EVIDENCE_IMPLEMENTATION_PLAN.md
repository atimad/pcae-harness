# Phase 133G — Canonical Engineering Evidence & Derived Evidence Views Implementation Plan

## 1. Purpose and Planning Verdict

This phase converts the verified 133D–133F architecture and contract into
the definitive implementation plan. It introduces no executable schema,
source code, test code, report-generation change, notification change, or
runtime behavior.

The implementation shall use five independently owned stages:

```text
Engineering Activity
        ↓ capture
Canonical Engineering Evidence
        ↓ projection
Derived Evidence Views
        ↓ rendering
Rendered Artifacts
        ↓ delivery
Delivery Adapters
```

Canonical Engineering Evidence is the only authoritative engineering
record. Views decide content; renderers decide presentation; adapters decide
transport mechanics. Telegram is the first planned adapter, never an
authority or a content architecture.

## 2. Binding Inputs and Constraints

Implementation is governed by:

- 133D's authority, lifecycle, evidence-category, determinism, and
  Repository Intelligence separation architecture;
- 133E's Purpose, Authority, Derived Evidence, Integrity, Lifecycle,
  Determinism, Non-Strengthening, Non-Omission, Governance, Versioning, and
  Quality contracts;
- 133F's independent verification, especially preservation of uncertainty
  and limitations and the current thin-report Non-Omission acceptance case;
- PFR-001's thirteen mandatory sections and informational-completeness bar;
- PFN-001's finalization, trust, idempotency, delivery, and operator-
  visibility obligations.

The plan does not amend any of those contracts.

## 3. Current-State Analysis

### 3.1 Completion flow

`pcae phase complete` currently resolves identity and completion metadata,
constructs a trial `PhaseReport`, applies two trust models plus the repository
transition validator, reconciles push state, certifies notification
eligibility, calls `finalize_phase_report()`, writes canonical latest report
artifacts, and optionally dispatches notification sinks. Report creation and
delivery therefore occur in one finalization path, but there is no preceding
authoritative engineering-evidence object.

### 3.2 Report generation and persistence

`src/pcae/core/phase_reports.py` uses one mutable `PhaseReport` object for
captured facts, trust fields, canonical-report compatibility state,
notification outcome, architecture status, and Markdown/JSON rendering.
`write_phase_report()` persists rendered report artifacts; the report itself
is treated as canonical even though 133D–133F now define it as a derived view.
The current `canonical_report_content` bridge loads separately authored prose
rather than deriving all content from one normalized evidence record.

### 3.3 Notification, rendering, and delivery

`phase_report_to_notification_event()` selects the summary as message content
and embeds selected report metadata plus rendered Markdown. `TelegramSink`
then constructs a mobile summary, applies message-length handling, sends a
message, and sends or falls back from a document. Thus view selection,
presentation, segmentation, and transport are distributed across report and
notification code rather than owned by distinct layers.

### 3.4 Evidence creation, loss, and transport coupling

Evidence is currently assembled from task contracts, completion metadata,
git inspection, governance checks, test results, project memory, and manually
authored completion prose. It is lost when rich facts are compressed into the
single `summary`, when data has no `PhaseReport` field, and when the thin
report omits six PFR-001 sections as first-class content. Summaries are
independently authored in project status, changelog, report summary, and
notification presentation. Telegram-specific content construction and
truncation live inside the sink. These are migration targets, not defects to
repair in this planning phase.

## 4. Target Component Boundaries

| Component | Owns | Must not own |
|---|---|---|
| Evidence capture | Observed facts and source references | View selection, prose, transport |
| Normalizer/canonicalizer | Stable ordering, normalized values, equivalence | Inference, summarization, presentation |
| Evidence validator | Integrity and canonical-record completeness | PFR audience policy or channel limits |
| Evidence store | Draft/final lifecycle, immutable finalized record, corrections | Rendering and dispatch |
| View generator | Audience/content selection and disclosed filtering | Formatting and transport |
| Derived Correctness validator | Faithful-projection proof and diagnostics | Repairing or rewriting evidence |
| Renderer | Format transformation of an already complete view | Content selection or silent omission |
| Delivery adapter | Channel conversion, segmentation, retry, result capture | Summarization or finding changes |
| Finalization orchestrator | Ordered coordination and failure policy | Duplicated validation rules |

Each public boundary accepts the preceding layer's validated artifact and
returns a new immutable result. No layer reaches around another layer to read
an alternate authority.

## 5. Canonical Engineering Evidence Implementation Plan

### 5.1 Lifecycle

Implement 133E's eight stages explicitly: activity, capture, normalization,
validation, canonical creation, derived generation, historical persistence,
and consumption. Operationally, use a mutable draft only through validation;
finalization atomically creates exactly one immutable canonical record per
phase before any view generation begins.

### 5.2 Persistence and identity

Persist canonical records in a dedicated evidence location separate from
`.pcae/phase-reports`. Identity is the governed phase identity, not free text.
Persistence must be atomic, collision-aware, locally durable, and capable of
distinguishing draft, finalized, and correction records. The later executable-
model phase will choose exact paths and schema.

### 5.3 Capture and normalization

Capture adapters shall consume existing authoritative inputs without parsing
claims from summaries: task/lifecycle identity, structured completion
metadata, git facts, governance results, test results, architectural boundary
statements, technical-debt classifications, findings, decisions, runtime
state, and repository state. Normalization establishes stable ordering,
canonical representations, explicit absent/unknown/not-applicable states,
source attribution, uncertainty, limitations, and approved timestamps.

### 5.4 Validation and canonicalization

Validation must cover all eleven frozen evidence categories, internal
consistency, identity, source traceability, classifications, uncertainty,
limitations, ordering, timestamp policy, and prohibited inference. A record
may finalize only after deterministic canonicalization and validation pass.
Equivalent normalized inputs must produce byte-equivalent canonical content
modulo approved timestamps.

### 5.5 Immutability and correction

Final records are read-only. Correction never overwrites history: a governed
correction artifact references the original record, states reason, authority,
changed evidence, and supersession relationship, and produces a new effective
version with an audit trail. Views identify the exact effective canonical
record/version used. Correction design is required before mutation support is
enabled; direct edits fail closed.

## 6. Derived Evidence View Architecture

Define one view protocol and independent deterministic generators. Every view
contains a canonical-record reference, view type/version, ordered content,
provenance links, disclosed selection/filter policy, preserved uncertainty and
limitations, and validation result.

Initial generators:

- **Phase Report View:** all thirteen PFR-001 sections, phase-class aware.
- **Operator Report View:** rich operational account described in Section 7.
- **Changelog View:** user/workflow-visible changes with explicit filtering.
- **Milestone View:** phase aggregation without making the aggregation
  authoritative.
- **Release View:** release-relevant evidence with disclosed selection rules.

New view types register alongside these generators and consume the stable
canonical interface. They must not add fields or behavior to Canonical
Engineering Evidence merely to satisfy presentation preferences; genuinely
missing engineering facts belong in evidence-model evolution through the
governed versioning process.

## 7. Operator Report View

The Operator Report is a sibling of the Phase Report View, not a Telegram
payload and not a summary of the Phase Report. Its ordered content must answer:

1. what happened and the major result;
2. decisions and architectural significance;
3. defects/findings and their classifications;
4. repairs and implementation changes;
5. verification evidence and tests;
6. technical debt reviewed, repaired, deferred, or newly found;
7. what changed and explicitly what did not change;
8. repository and runtime state;
9. governance/delivery readiness and limitations;
10. recommended next phase.

It shall retain the engineering density of the repository's rich governed
completion documents while using stable headings, concise lead summaries,
ordered findings, and traceability references. Content absence is explicit
(`none`, `not applicable`, `unknown with reason`), never represented by a
missing section. Mobile-friendliness is a rendering concern and may not weaken
this content contract.

## 8. Rendering Layer

Renderers accept only validated derived views and produce typed rendered
artifacts for Markdown, plain text, HTML, JSON, and future formats. Rendering
is deterministic, side-effect free, and unaware of Telegram or any delivery
configuration.

Every renderer must preserve view ordering, finding classification,
uncertainty, limitations, traceability, and disclosed omissions. Unsupported
content fails closed or emits an explicit loss diagnostic; it may never be
silently dropped. Renderer validation compares the rendered artifact's content
manifest to the source view manifest. Formatting differences are allowed;
semantic differences are not.

## 9. Delivery Adapter Architecture

Adapters receive a validated rendered artifact plus delivery envelope and
return a structured outcome. They may perform channel escaping, segmentation,
message/document choice, channel-limit conversion, retry/backoff, idempotency,
and transport error classification. They may not choose engineering content,
summarize, reorder semantic units, alter findings, strengthen conclusions, or
omit material evidence.

Segmentation operates on renderer-declared boundaries. Every segment carries
artifact identity, ordered part number/count, and canonical/view traceability.
If complete delivery is impossible, the adapter reports partial/failed with
the exact unsent segments; it never reports success after truncation.

The first adapter wraps existing Telegram transport behavior behind this
contract. Email, Slack, Teams, Discord, dashboard, push, and API adapters can
then be added without changing evidence, view generation, or rendering.

## 10. PFR-001 Generation and Informational Completeness

The Phase Report generator maps canonical evidence deterministically into all
thirteen mandatory sections in PFR order: Phase Identity, Executive Summary,
Architectural Findings, Implementation Findings, Verification Findings,
Technical Debt Review, Notable Engineering Knowledge, Governance Results,
Test Results, No-Go Confirmation, Architectural Boundary Confirmation, Track
Progress, and Next Phase.

Validation replaces today's metadata-presence model with two cumulative gates:

- **structural completeness:** every mandatory section exists in order;
- **informational completeness:** each section meets its PFR-001 minimum for
  the phase class, uses explicit none/not-applicable statements where allowed,
  includes required evidence and classifications, and rejects generic
  completion prose as sufficient content.

Existing identity, push, governance, trust, and notification gates remain
requirements and are composed with, not discarded by, the new content gate.

## 11. Derived Correctness Validation

Implement one reusable validator for every view and rendered artifact. A view
generation result includes a projection manifest mapping every output semantic
unit to canonical evidence identifiers and recording every excluded unit with
its disclosed filter reason.

Validation checks:

- no output claim lacks canonical support (no invention);
- canonical meaning and classification are unchanged (no reinterpretation);
- certainty is never increased (no strengthening);
- every excluded material item is disclosed (no silent omission);
- uncertainty and limitations remain attached to affected claims;
- ordering is deterministic and prescribed by view policy;
- traceability resolves to the exact canonical record/version;
- repeated generation/rendering is byte-equivalent modulo approved timestamps.

Failure is diagnostic and fail-closed. The validator never edits output to
make it pass. View-specific policies may add stricter rules but may not weaken
the shared invariant.

## 12. PFN-001 Finalization Integration

PFN-001 continues to govern delivery. The final ordered transaction is:

```text
capture → normalize → validate → finalize canonical evidence
        → generate views → validate projections
        → render → validate renderings
        → certify delivery → adapter dispatch → persist delivery outcome
```

No view or delivery begins before canonical finalization. Rendering completes
before adapter execution. Existing trust, transition, push-state,
notification-certification, idempotency, partial-warning, and explicit failure
behavior remain intact.

Because canonical evidence is immutable, delivery outcome is linked back by a
separate append-only delivery receipt referencing canonical record ID/version,
view ID/version, rendered-artifact digest, adapter, attempts, segment outcomes,
and final disposition. It is not written into or allowed to mutate the
finalized evidence record. This resolves the apparent tension between
"link back" and immutability.

## 13. Repository Intelligence Independence

Repository Intelligence remains authoritative only for "what is true about
the repository?" Canonical Engineering Evidence remains authoritative only
for "what happened during engineering?" Evidence capture may record a
source-attributed Repository Intelligence artifact reference or snapshot
digest used during a phase, but it does not absorb that artifact's authority.
Repository Intelligence does not derive engineering actions, and evidence
generation does not scan or regenerate Repository Intelligence. Cross-links
are references, never ownership transfer or a merged schema.

## 14. Migration Strategy

Migration is additive and gated:

1. introduce the canonical model/store behind no production finalization;
2. dual-capture current inputs and compare without changing current outputs;
3. generate shadow Phase Report and Operator Report views;
4. validate shadow outputs against current artifacts and PFR/Derived
   Correctness requirements;
5. introduce side-effect-free renderers and shadow rendered artifacts;
6. wrap Telegram transport as an adapter while current dispatch remains the
   active path;
7. switch finalization ordering only after independent verification and
   explicit activation approval;
8. retain rollback to the pre-switch path until equivalence, completeness,
   idempotency, and failure semantics are proven.

Historical reports remain historically valid and byte-unchanged. They are
marked as legacy derived artifacts with no fabricated canonical ancestor. No
backfill, retroactive canonicalization, or rewriting is permitted. Migration
begins with the first explicitly activated phase.

## 15. Smallest Governed Implementation Roadmap

The suggested decomposition is refined to keep authority-bearing work ahead of
all presentation work:

| Phase | Scope | Exit condition |
|---|---|---|
| **133H** | Executable Canonical Engineering Evidence model, lifecycle states, deterministic normalization/canonicalization, validation, persistence, immutable finalization, correction envelope; no views or delivery | One authoritative record can be created and validated without changing active report/notify flow |
| **133I** | Independent verification of 133H | Authority, integrity, determinism, correction, and Repository Intelligence independence re-derived |
| **133J** | Derived View protocol, Phase Report View, Operator Report View, informational completeness, Derived Correctness validator | Both initial views deterministically and faithfully project canonical evidence |
| **133K** | Independent verification of 133J | PFR thirteen-section compliance and Operator Report completeness confirmed |
| **133L** | Rendering subsystem and render correctness for Markdown/plain text/JSON | Rendering is lossless, deterministic, and transport-independent |
| **133M** | Delivery Adapter framework, Telegram adapter, PFN-001 orchestration, receipts, segmentation, retry/idempotency, guarded migration | Telegram delivers the rich Operator Report without content ownership or silent truncation |
| **133N** | End-to-end independent verification and activation-readiness review | Full pipeline, rollback, compatibility, and unchanged authority boundaries proven |

Email/Slack/Teams/other adapters, Changelog/Milestone/Release generator
implementation, HTML, dashboards, APIs, historical backfill, and analytics are
deferred until the initial pipeline is independently verified. Their
interfaces are planned here; implementing them is not required to activate the
first complete path.

## 16. Acceptance and Verification Matrix

Future implementation is acceptable only when tests prove:

- exactly one finalized authoritative evidence record per governed phase;
- draft mutability and finalized immutability with governed correction only;
- deterministic canonicalization, view generation, and rendering;
- all eleven evidence categories are represented with explicit state;
- all thirteen PFR sections are structurally and informationally complete;
- Operator Report answers every Section 7 question with rich evidence;
- projection manifests prove no invention, reinterpretation,
  strengthening, or silent omission;
- uncertainty, limitations, traceability, and ordering survive every layer;
- adapters cannot access canonical evidence or select view content;
- Telegram segmentation delivers every segment or reports explicit failure;
- PFN-001 trust, ordering, certification, idempotency, and visibility remain;
- historical reports remain unchanged;
- Repository Intelligence authority remains independent;
- runtime remains `Observed`, maximum capability `observe`, and execution
  remains unavailable unless separately governed in a future track.

## 17. Risks and Mitigations

- **Big-bang finalization rewrite:** mitigate with shadow generation,
  independent verification, explicit activation, and rollback.
- **Schema optimized around PFR/Telegram:** model frozen evidence categories
  first; keep view and adapter fields out of the canonical model.
- **False completeness from non-empty prose:** use phase-class-aware semantic
  requirements and evidence references, not heading/field presence alone.
- **Projection validator becomes a second authority:** require manifests and
  comparison only; prohibit inference and automatic repair.
- **Adapter truncation masquerades as success:** segment manifests and
  per-segment receipts; fail closed on incomplete delivery.
- **Delivery receipt mutates evidence:** append-only linkage external to the
  immutable record.
- **Dual-write drift:** canonical input capture is shared; compare digests and
  surface divergence during shadow operation.

## 18. Technical Debt Disposition

This plan owns, but does not repair, the current thin canonical report,
metadata-only completeness, independently authored summaries, mixed
rendering/transport responsibilities, Telegram sink content selection, and
absence of an authoritative engineering record. The uncertainty/limitations
clarification from 133F is made an explicit implementation and validation
requirement. None is silently reclassified as resolved by planning.

## 19. Strict Non-Goals and Boundary Confirmation

Phase 133G does not implement an evidence model or schema, view generator,
renderer, adapter, validator, migration, Telegram behavior, or PFN-001 change.
It does not modify report-generation or notification source, tests, runtime,
Repository Intelligence, execution authority, plugin capability, or historical
artifacts. Planning documents and repository memory are the only intended
changes.

## 20. Recommended Next Phase

**133H — Canonical Engineering Evidence Executable Model Implementation.**

133H should implement only the authority-bearing foundation: lifecycle,
executable model, deterministic normalization/canonicalization, validation,
persistence, immutable finalization, and governed correction envelope. It must
remain disconnected from active report rendering and notification delivery.
This is the smallest safe next step because derived views cannot be correctly
implemented before their sole authority exists and is independently testable.
