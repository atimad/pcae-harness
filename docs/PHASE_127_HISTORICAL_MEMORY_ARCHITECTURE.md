# Phase 127A - Historical Memory Architecture

## 1. Purpose

Phase 127A defines the canonical architecture for Historical Memory:
PCAE's temporal layer describing how and why the repository evolved
over time, complementing the point-in-time description Repository
Intelligence already provides.

Repository Intelligence and Historical Memory answer two different
questions:

- **Repository Intelligence answers: "What exists right now?"**
  Track 120's Repository Knowledge Snapshot enumerates architectural
  entities, capabilities, subsystems, and contracts as a flat,
  source-attributed record of the repository at one point in time.
  Track 126's Dependency Knowledge Graph answers a related but
  distinct question — "how are those things structurally related?" —
  also at one point in time.
- **Historical Memory answers: "How and why did the repository get
  here?"** It represents declared, source-attributed historical
  events, phase and release lineage, decisions, repairs, hardening,
  supersessions, and corrections — a temporal record, not a
  point-in-time one.

This is architecture only. It defines what Historical Memory is, what
it may and may not do, and how future phases (127B contract freeze,
127C contract verification, 127D plan, 127E implementation, 127F
verification — mirroring the exact Track 126 phase sequence) must
build it, without building any of it here. It creates no generator, no
timeline engine, no repository scanning, no Query Layer changes, no
consumer changes, **no schema modification**, no source code, no test
code, and no execution capability.

## 2. Grounding: A Historical Memory Schema Is Already Frozen

Unlike Track 126's starting point, this phase does not begin from a
blank conceptual slate. Phase 119Q already froze
`schemas/repository_intelligence/artifacts/historical_memory_snapshot.schema.json`
— the third artifact-family schema, and the second content-bearing one
after Repository Knowledge Snapshot, predating even the Dependency
Knowledge Graph Snapshot schema (119S). The schema's own README entry
(`schemas/repository_intelligence/README.md`) states its rationale
directly: "It follows Repository Knowledge Snapshot because Historical
Memory describes how repository architecture, contracts, capabilities,
releases, repairs, hardening, and decisions evolved over time."

127A's task is therefore not to invent a conceptual model from
scratch, but to **adopt the already-frozen 119Q schema as the
authoritative conceptual model**, exactly as 126A adopted the 119S/119T
node/edge taxonomy for the Dependency Knowledge Graph rather than
inventing a parallel one. No 119Q field, enum, or structure is added,
renamed, or reinterpreted by this phase.

The 119Q schema itself explicitly declares — in its own `description`
field — what it does not do: "it does not perform historical
extraction, git history analysis, repository scanning, timeline
generation, or lifecycle validation." It is a declared shape, not a
generator; 127A's job (and the phases after it) is to define how a
real generator would responsibly and honestly populate that shape.

## 3. Scope

Historical Memory provides deterministic historical evidence
describing repository evolution across snapshots. It preserves
engineering continuity.

- It never invents history. Every historical claim requires source
  attribution.
- It does not perform reasoning, prediction, or interpretation.
- It does not make decisions.
- It does not execute actions.
- It does not replace Repository Intelligence artifacts — it is a
  third, complementary artifact family (after Repository Knowledge
  Snapshot and, chronologically in the schema numbering, before
  Dependency Knowledge Graph), not a redefinition of either.
- It does not replace Repository State, Evidence, or Decision
  Evaluation — the 119Q disclaimer const string states this directly
  (Section 11).

This document does not implement: a Historical Memory builder; a
timeline engine; historical event extraction; git history analysis;
repository scanning; storage; source code; test code; schema changes;
or any change to runtime behavior.

## 4. Core Objectives

Historical Memory shall enable future PCAE components to understand,
without introducing reasoning:

- **Architectural evolution** — how architecture, contracts, and
  capabilities changed over time (via `historical_event` records of
  type `architecture_defined`, `architecture_reviewed`,
  `contract_frozen`, `contract_verified`, and `phase_lineage_record`
  entries).
- **Implementation evolution** — how implementations, prototypes, and
  hardening evolved (via `schema_implemented`, `schema_verified`,
  `prototype_added`, `integration_recorded`, `hardening_completed`,
  `repair_completed` event types, and `repair_hardening_record`
  entries).
- **Repository evolution** — the sequence of phases and releases that
  produced the repository's current state (via `phase_lineage_record`
  and `release_lineage_record` entries, and `release_published` event
  type).
- **Engineering decisions** — recorded decisions and their outcomes
  (via `decision_history_record` entries and the `decision_recorded`
  event type).
- **Evidence chains** — the source attribution and optional Evidence
  links behind every historical claim (via `source_attribution` and
  `evidence_links` on every record type, and the top-level
  `historical_sources` array).
- **Historical relationships** — declared structural relationships
  between historical entities (via `historical_relationship` records:
  e.g. a phase `froze_contract`, a release `included_in_release`,  a
  correction `supersedes` or `corrects` a prior record).
- **Chronological context** — the declared time window and ordering a
  historical claim belongs to (via `historical_period`/
  `historical_time_reference` and the top-level `historical_window`).

Historical Memory shall remain evidence only. It answers "what was
declared to have happened, and on what evidence" — never "what should
happen next" or "why was this the right decision."

## 5. Conceptual Model

Resolving the brief's requested conceptual objects onto the
already-frozen 119Q `$defs`, adopted unchanged:

### 5.1 Historical Snapshot

Maps to `snapshot_identity` (`snapshot_id`, `snapshot_subject`,
`snapshot_scope`, `historical_window`, `snapshot_created_at_utc`,
version fields) plus the top-level envelope. One Historical Memory
Snapshot artifact represents one bounded, source-attributed view of
repository history as of its own generation time — analogous to how a
Repository Knowledge Snapshot represents one bounded view of current
repository state. A Historical Memory Snapshot is not itself "the
repository's history" in totality; it is a declared, honestly-scoped
claim about what history could be established from available sources
at generation time.

### 5.2 Historical Event

Maps directly to `historical_event`: a single, source-attributed,
dated occurrence (`event_id`, `event_type`, `event_subject`,
`event_time`, `event_summary`, `event_status`, `source_attribution`,
`verification_state`, `limitations`, optional `evidence_links` and
`related_events`). `event_type` is a closed, already-frozen enum of
21 values (`phase_started`, `phase_completed`, `architecture_defined`,
`architecture_reviewed`, `contract_frozen`, `contract_verified`,
`schema_implemented`, `schema_verified`, `prototype_added`,
`integration_recorded`, `hardening_completed`, `repair_completed`,
`release_published`, `governance_check_completed`, `report_generated`,
`metadata_promoted`, `notification_sent`, `decision_recorded`,
`supersession_recorded`, `correction_recorded`, `unknown`) — 127A
adopts this enum unchanged; no future phase may add, rename, or
reinterpret a value without a governed schema-amendment phase.

### 5.3 Historical Timeline

Not a single dedicated `$def` — represented conceptually by the
combination of `historical_window` (the snapshot's own declared
period, via `historical_period`), the `historical_time_reference`
shape (`time_reference_type`: `timestamp_utc`, `date`, `date_range`,
`phase`, `release`, `commit`, or `unknown`), and the ordered set of
`historical_events`/`phase_lineage`/`release_lineage` records a
generator assembles. A "timeline" in Historical Memory is therefore a
**declared ordering of already-dated records**, not a computed or
inferred sequence — Section 8 (Temporal Model) makes this explicit.

### 5.4 Historical Relationship

Maps directly to `historical_relationship`: a declared, directed (or
`bidirectional`/`unknown`-directioned) association between two
historical references (`relationship_id`, `relationship_type`,
`source_reference`, `target_reference`, `direction`,
`source_attribution`, `verification_state`, `limitations`).
`relationship_type` is a closed, already-frozen enum of 12 values
(`introduced_by`, `changed_by`, `froze_contract`, `verified_by`,
`repaired_by`, `hardened_by`, `supersedes`, `corrects`,
`included_in_release`, `documents`, `related_to`, `unknown`) — adopted
unchanged, mirroring exactly how 126B froze the Dependency Knowledge
Graph's `edge_type` enum as binding without reinterpretation.

### 5.5 Historical Evidence

Not a distinct record type — an already-established, repeated
pattern: every `historical_event`, `historical_claim`,
`phase_lineage_record`, `release_lineage_record`,
`decision_history_record`, `repair_hardening_record`,
`supersession_correction_record`, and `historical_relationship`
requires its own `source_attribution` (`minItems: 1`, confirmed by
direct schema inspection) and `verification_state`, with optional
`evidence_links` connecting a claim to an Evidence Link Record —
exactly the same provenance discipline every other Repository
Intelligence artifact family already holds since Track 119, preserving
the established boundary that Evidence links are bridge/candidate
records, never accepted Evidence themselves.

### 5.6 Historical Transition

Represented by three distinct, already-frozen record types, each
covering a different kind of transition — 127A does not collapse them
into one, since the schema itself does not:

- **`decision_history_record`** — a recorded engineering decision and
  its outcome (`decision_id`, `decision_subject`, `decision_type`,
  `decision_summary`, `decision_source`, `recorded_outcome`).
- **`repair_hardening_record`** — a recorded repair or hardening
  action (`record_type`, `issue_or_boundary_addressed`,
  `correction_or_hardening_summary`, `affected_artifact_or_subsystem`).
- **`supersession_correction_record`** — a recorded supersession or
  correction (`superseded_reference`, `superseding_reference`,
  `supersession_reason`, `preserved_history` — this last field is
  itself a governance-critical requirement: Section 9 elaborates).

### 5.7 Historical Context

Maps to `historical_claim` (`claim_id`, `claim_type`, `claim_subject`,
`claim_statement`, optional `structured_value`, `historical_period`,
`source_attribution`, `verification_state`, `limitations`, optional
`conflict_or_supersession_records` and `related_claims`) — a
source-attributed statement scoped to a specific historical period,
distinct from a bare `historical_event` in that a claim may synthesize
or characterize a period rather than record a single dated occurrence.

### 5.8 Taxonomy Completeness

Every conceptual object the task brief named (Historical Snapshot,
Event, Timeline, Relationship, Evidence, Transition, Context) has a
direct, already-frozen mapping. Unlike 126A's discovery of genuine
taxonomy gaps in the Dependency Knowledge Graph's adopted enum (class/
function nodes, containment edges), no equivalent gap was found here —
119Q's schema authors already anticipated this conceptual surface in
full. This is a **finding**, not an assumption: 127A independently
re-read every `$defs` entry in the schema file directly (not from the
README's prose summary alone) to confirm this completeness before
stating it.

## 6. Relationship with Repository Intelligence

**Repository Intelligence remains the source of observed facts.
Historical Memory derives temporal claims from Repository Intelligence
and from the repository's own governed provenance record (phase
reports, task contracts, commit history, canonical metadata) — never
by direct git history parsing outside a Query Layer boundary, never by
independent interpretation.**

Historical Memory consumes existing Repository Intelligence. It never
regenerates Repository Intelligence. This mirrors exactly the
relationship Track 126 already established with Track 120/121: a
consumer, never a source; deterministic, never inferential.

### 6.1 Track 119 — Executable Schemas

Historical Memory's schema (`historical_memory_snapshot.schema.json`)
is already frozen by 119Q. This contract authorizes no schema change.
A future generator must produce output conforming to this schema
exactly as written.

### 6.2 Track 120 — Repository Knowledge Snapshot

Historical Memory's primary input is Repository Knowledge Snapshot
content, reached exclusively through the Track 121 Query Layer —
never by direct file access, never by repository scanning, never by
rerunning the Track 120 generator. `phase_lineage_record`'s
`phase_context`/`metadata_reference` fields and `release_lineage_
record`'s `release_context` fields are the natural attachment points
for RKS-derived entity/attribution content, analogous to how 126D
found RKS `entity_type` needed translation into DKG `node_type`; a
future 127D-equivalent plan phase must perform the same grounding
exercise here (Section 14).

### 6.3 Track 121 — Repository Intelligence Query Layer

The Query Result schema (119Y) already anticipates a
`historical_memory_query` value in its own closed `query_type` enum
(`$defs/query_type`, confirmed by direct schema inspection), alongside
the five other artifact-family query categories. **This category is
not implemented**
— the Track 121 Query Layer's actual `SUPPORTED_QUERY_CATEGORIES`
(confirmed by direct source inspection of
`src/pcae/repository_intelligence/query/query_request.py`) currently
supports only `entity_lookup`, `capability_lookup`,
`architectural_contract_lookup`, `attribution_lookup`,
`limitation_lookup`, and `boundary_lookup` — none of which is
Historical-Memory-specific. This mirrors exactly 126A's own finding
for the Dependency Knowledge Graph's anticipated-but-unimplemented
query categories. No Query Layer code changes occur in this phase; a
future `historical_memory_query` category remains anticipated, not
authorized, by 127A.

### 6.4 Track 122 — Advisory Context Builder

The Advisory Intelligence Context Package schema (119W) already
anticipates Historical Memory Snapshot as one of the four
content-bearing artifact families it packages
(`repository_intelligence_package.schema.json`'s
`historical_memory_package` package-type enum value, confirmed by
direct schema inspection). Advisory may eventually consume Historical
Memory content exactly as it already consumes Repository Knowledge
Snapshot content today: through a bounded Query Layer request, with
attribution, limitations, and boundary disclosures preserved unchanged
into the assembled Advisory context package. **No Advisory reasoning
is implemented, implied, or authorized by this phase.** Track 122's
Advisory Context Builder itself is not modified.

### 6.5 Track 123 — Change Impact

The Change Impact Report schema's own README rationale (Section 2)
states directly: "Change Impact Analysis reasons over Repository
Knowledge, Historical Memory, and the Dependency Knowledge Graph to
describe what may be affected by a change." A future Change Impact
Builder revision could ask Historical Memory "has this entity been
repaired/hardened/superseded before, and by what" to enrich impact
context with temporal precedent. **No impact reasoning is implemented
in this phase.** Track 123's Change Impact Builder itself is not
modified.

### 6.6 Track 126 — Dependency Knowledge Graph

Historical Memory and the Dependency Knowledge Graph are sibling,
complementary artifact families over the same Repository Knowledge
Snapshot foundation — one temporal, one structural. Per the schemas
README's own stated chronology, Historical Memory Snapshot (119Q)
predates Dependency Knowledge Graph Snapshot (119S) in the schema
numbering; Track 126 was, however, selected and implemented first
(125F's decision), establishing the proven six-phase governed sequence
(architecture → contract freeze → contract verification → plan →
prototype → verification) that 127A now begins repeating for
Historical Memory. A future Historical Memory generator's
`historical_relationship` records could reference Dependency Knowledge
Graph `node_id`s (e.g., "this entity was `hardened_by` the phase that
also produced this dependency edge"), but **no such cross-artifact
reference is designed, scoped, or authorized here.**

## 7. Temporal Model

- **Chronological ordering** — every `historical_event` carries an
  `event_time` (`historical_time_reference`); every `historical_claim`
  is scoped to a `historical_period`. A generator must order events
  and claims by their own declared time reference, never by discovery
  or file-scan order — matching the same "deterministic, not
  incidental" ordering discipline Track 124 already hardened for
  Repository Intelligence serialization generally.
- **Snapshot lineage** — `phase_lineage_record`'s
  `predecessor_phase_ids`/`successor_phase_ids` fields declare phase
  sequence explicitly, as data, not as inferred graph edges. A
  Historical Memory Snapshot does not itself compute lineage by
  traversal; it records lineage that is already explicit in governed
  phase-completion metadata (recommended-next-phase chains, task
  contract predecessors) or already-declared source content.
- **Repository evolution** — the combination of ordered
  `historical_events`, `phase_lineage`, and `release_lineage` arrays
  is the declared record of repository evolution. This is not a
  "living" or continuously-updated model — consistent with Section 12
  of the frozen schema's versioning discipline (Section 12 below),
  each Historical Memory Snapshot is a fresh, regenerated, bounded
  claim about history as understood at its own generation time.
- **Historical provenance** — every record's `source_attribution`
  establishes not just *that* a historical claim is made but *what it
  was derived from* — a governed phase report, a task contract, a
  commit reference, or existing Repository Knowledge Snapshot content.
  No historical claim may cite "history" or "the repository"
  generically; attribution must be as specific as the Track 119-126
  provenance discipline already requires elsewhere.
- **Evidence continuity** — `supersession_correction_record`'s
  `preserved_history` field is a structural guarantee, not optional
  narrative: when a historical record is superseded or corrected, the
  superseded content itself must remain represented (not deleted or
  silently replaced), consistent with 125B §7's "inherited limitations
  cannot be dropped, weakened, replaced, or masked" principle, restated
  here for historical continuity specifically — Historical Memory must
  never let a correction erase the record of what was previously
  believed true.

## 8. Determinism

Historical reconstruction shall remain deterministic. Equivalent
repository history shall produce equivalent historical artifacts.

- Given the same set of source inputs (Repository Knowledge Snapshot
  content, governed phase-completion metadata, commit history at a
  fixed point), a future Historical Memory generator must produce the
  same `historical_events`, `historical_claims`, lineage records, and
  identifiers on every run.
- No historical claim may be created by inference, heuristic guessing,
  probabilistic scoring, or AI-based interpretation of intent. Every
  event, claim, and relationship must trace to an explicit,
  deterministic extraction rule applied to explicit source content —
  the same discipline 126B §10 already froze for the Dependency
  Knowledge Graph, restated for the temporal layer.
- Ordering of events/claims/records within a serialized artifact must
  be deterministic (e.g. stable sort by declared time reference, then
  by identifier), consistent with the serialization discipline Track
  124 already hardened and Track 126 already reused
  (`serialize_deterministic_json`).
- Stable identifiers — `event_id`, `claim_id`, `relationship_id`,
  `record_id` must each be deterministic functions of their underlying
  source content, not incidental generation-order artifacts, mirroring
  126B §4.4/126D §7's node/edge identifier discipline exactly.

## 9. Evidence Contract

Historical Memory preserves, without reinterpretation:

- **Provenance** — every event, claim, lineage record, decision
  record, repair/hardening record, supersession/correction record, and
  relationship requires `source_attribution` (schema-required,
  `minItems: 1` where declared) citing the specific source content it
  was derived from.
- **Attribution** — attribution must be specific (a phase report, a
  task contract, a commit, existing Repository Intelligence content),
  never a generic "the repository" or "history" citation — the same
  standard 126B §7 already required for Dependency Knowledge Graph
  edges.
- **Limitations** — every record and the snapshot as a whole require
  at least one limitation record (`snapshot_limitations`,
  schema-required), preventing false completeness at any level of the
  artifact, exactly as every other Repository Intelligence artifact
  family already requires.
- **Boundary disclosures** — every Historical Memory artifact carries
  `boundary_disclosures` (the shared component: `read_only`,
  `no_execution`, `non_decision`, `advisory_non_authority`,
  `decision_evaluation_required`, `no_repository_mutation`,
  `no_lifecycle_mutation`, `no_evidence_replacement`,
  `no_repository_state_replacement`, independently re-confirmed by
  direct schema inspection) and the frozen
  `historical_memory_snapshot_disclaimer` const string, unchanged:
  *"This Historical Memory Snapshot describes declared repository
  history and lineage. It is not Repository State, does not decide
  lifecycle standing, does not prove historical truth or completeness,
  and does not authorize action or execution."*
- **No reinterpretation** — no future phase may reinterpret attribution
  as proof of historical truth, merge records in a way that loses
  per-record provenance, or convert a historical evidence gap into
  evidence support. This restates 126B §7's rule for the temporal
  layer specifically.

## 10. Read-Only Contract

Historical Memory never mutates:

- **The repository** — no repository scanning beyond what an
  already-approved Repository Intelligence generation performs; no
  file writes to source content.
- **Snapshots** — a Historical Memory Snapshot never modifies an
  existing Repository Knowledge Snapshot or Dependency Knowledge Graph
  Snapshot artifact; it only reads them (via the Query Layer) and
  writes its own, distinct artifact.
- **The graph** — no Dependency Knowledge Graph artifact is read,
  written, or traversed by this phase or by any capability it
  authorizes.
- **Advisory context** — no Advisory Context Package is generated,
  modified, or consumed by this phase.
- **Change reports** — no Change Impact Report is generated, modified,
  or consumed by this phase.

Observe-only operation: a future Historical Memory generator reads
existing governed artifacts and produces a new, distinct artifact; it
performs no repository mutation, no lifecycle mutation, no execution,
and no runtime state change — matching `boundary_disclosures`'
const-`true` declarations exactly.

## 11. Failure Model

**Historical Memory shall fail closed whenever required evidence
cannot be established. Historical Memory shall never invent history.**

- If available source content does not clearly support a candidate
  historical event, claim, lineage record, or relationship, a future
  generator must either omit it entirely (with a corresponding
  `unknown_gap` record — the schema's own dedicated shape for this,
  `unknown_id`/`unknown_subject`/`missing_evidence`/`affected_period`/
  `uncertainty_state`/`limitation`) or represent it with an honestly
  `unknown`/`unverified` `verification_state` — never silently promote
  an ambiguous or incomplete historical signal into a confident-looking
  record.
- Missing attribution, missing limitations, missing boundary
  disclosure material, unsupported schema versions, corrupted
  Repository Intelligence input, and invalid Query Layer results must
  all fail closed — the generator refuses to produce output rather
  than producing an under-evidenced artifact, matching the fail-closed
  discipline every Track 120-126 phase has already independently
  established.
- A detected historical conflict (e.g. two sources disagreeing about
  when an event occurred) must be represented honestly — via a
  `conflicting` `verification_state`, or a `conflict_or_supersession_
  records` entry (the shared component already referenced by
  `historical_claim`) — never silently resolved by picking one source
  over another without disclosure.
- No fail-open path may be introduced. This restates 125B §11's
  Failure Contract and 126B §12's Failure Contract for the temporal
  layer specifically.

## 12. Governance Compatibility

This architecture is compatible with PCAE governance:

- **Observe-only** — preserved; Section 10.
- **Deterministic** — preserved; Section 8.
- **Reproducible** — preserved; Section 8, Section 13 (Versioning).
- **Auditable** — every phase in the sequence this architecture opens
  must produce a complete, metadata-consistent canonical phase report,
  following the same discipline every Repository Intelligence phase
  has used.
- **Explainable** — every event, claim, and relationship traces to
  specific source content and (where present) an explicit derivation
  rule; Section 9.
- **Execution unavailable** — preserved; runtime state remains
  `Observed`, maximum plugin capability remains `observe`, execution
  capability remains `unavailable`, and no phase in the planned
  127A-F sequence changes this boundary, mirroring 126A §15's binding
  requirement.
- Raw git commit/push, force push, and `--no-verify` remain forbidden;
  this phase did not use them.
- Canonical reports remain complete and metadata-consistent.
- Human-controlled lifecycle authority remains unchanged.

## 13. Versioning Architecture

Conceptual versioning, mirroring Track 119's conventions already
established for every other artifact family (no storage implementation
occurs in this phase):

- **Schema/contract version** — Historical Memory's executable schema
  version is already frozen as `119Q.1.0-json-schema`
  (`snapshot_identity.executable_schema_version`'s own `const` value,
  independently confirmed via direct schema inspection, alongside
  `artifact_contract_version: "119E.1.0"` and
  `schema_concept_version: "119C.1.0-concept"` — both shared with every
  other Track 119 artifact family); a future 127B contract freeze must
  cite this version explicitly, not silently assume it.
- **Snapshot identity** — each generated Historical Memory Snapshot
  carries its own `snapshot_identity`/`snapshot_id`, distinct from (but
  potentially referencing) the Repository Knowledge Snapshot(s) and any
  other artifacts it was derived from.
- **Regeneration, not mutation** — consistent with every existing
  Repository Intelligence artifact family, a Historical Memory Snapshot
  is regenerated fresh when the underlying repository/history changes;
  no incremental/patch-based mutation model is proposed or assumed.
  Because Historical Memory's subject matter (past events) does not
  itself change retroactively, regeneration means *extending* the
  historical record with newly-observable events, not rewriting prior
  ones — Section 7's evidence-continuity requirement applies directly
  here.

## 14. Relationship to Future Chapters

Historical Memory enables, without itself introducing:

- **Richer Change Impact** — Section 6.5's temporal-precedent
  enrichment, once a real generator and Query Layer category exist.
- **Stronger Advisory Context** — Section 6.4's historically-aware
  context assembly, once wired.
- **Future Decision Evaluation** — historical decision records could
  eventually inform Decision Evaluation's evidence base as one more
  source among many; 115E's "Evidence never decides" principle remains
  untouched, and no Decision Evaluation change is introduced here.
- **Eventual Execution Planning** — 125G's readiness assessment
  identified both Dependency Knowledge Graph and Historical Memory
  maturity as concrete readiness gaps for a future Execution Planning
  chapter; Historical Memory's eventual maturity narrows that gap
  further alongside Track 126's. This phase introduces no execution
  planning, execution capability, or change to the
  execution-unavailable boundary.

None of these future integrations is designed, scoped, or authorized
by this phase.

## 15. Deferred Capabilities

Explicitly deferred, not implemented by this phase:

- Historical Memory Builder (generator);
- historical reasoning;
- predictive reasoning;
- recommendations;
- decision evaluation;
- execution planning;
- execution capability;
- AI interpretation;
- graph traversal;
- timeline inference beyond deterministic, source-attributed evidence;
- schema changes;
- storage implementation.

## 16. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this architecture phase.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this architecture phase.
- Recurring `pending_final_telegram_delivery` reporting detail
  (dispatch-ordering/timing, distinct from content fidelity):
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.

**Not inherited defects**: 126G (Telegram Canonical Report Dispatch
Repair) and 126G.1 (Telegram Commit Trust Metadata Repair) already
resolved the notification-pipeline content-fidelity and commit-trust
gaps they each targeted. Neither is carried forward as an open issue
here — both are closed, verified repairs, confirmed by their own
canonical reports and by live Telegram dispatch during their respective
finalizations.

## 17. Strict Non-Goals

This phase does not implement: a Historical Memory Builder; schemas
(119Q's schema is adopted unchanged, not modified); generators;
storage; a timeline engine; repository scanning; graph traversal;
reasoning; recommendations; execution planning; execution capability;
runtime plugins; source code; or test code.

## 18. Conclusion

Phase 127A defines Historical Memory as PCAE's temporal layer — a
third, complementary Repository Intelligence artifact family that
derives from, and remains subordinate to, Repository Intelligence and
the repository's own governed provenance record. Unlike Track 126's
starting point, this phase found the entire requested conceptual
surface (Historical Snapshot, Event, Timeline, Relationship, Evidence,
Transition, Context) already fully and honestly represented by the
already-frozen 119Q schema — no taxonomy gap requiring 127B resolution
was found, a materially different outcome from 126A's own discovery
process, independently confirmed by direct inspection of every `$defs`
entry rather than assumed from the schema's README summary. This
document adopts that schema as the binding conceptual model, and
defines temporal model, determinism, evidence contract, read-only
contract, failure model, versioning strategy, and Track 119-126
relationships — all without implementing any of it. No implementation
occurred. No runtime behavior changed. Execution remains unavailable.

Recommended next phase: 127B — Historical Memory Contract Freeze.
