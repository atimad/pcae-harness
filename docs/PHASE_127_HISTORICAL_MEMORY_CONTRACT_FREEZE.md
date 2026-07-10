# Phase 127B - Historical Memory Contract Freeze

## 1. Purpose

Phase 127B freezes the canonical contract for PCAE's Historical Memory:
deterministic temporal repository evidence, operationalizing the
architecture 127A defined into binding, normative requirements.

Historical Memory records repository evolution. It never interprets
history. It never predicts history. It never reasons.

The contract governs structure and behavior, not implementation. It is
binding for:

- 127C - Historical Memory Contract Verification;
- 127D - Historical Memory Plan;
- 127E - Historical Memory Implementation;
- 127F - Historical Memory Verification.

127B is documentation only. It creates no generator, no timeline
engine, no repository scanning, no Query Layer changes, no consumer
changes, **no schema modification**, no source code, no test code, and
no runtime behavior change.

## 2. Contract Authority

This document is the canonical Track 127 Historical Memory contract
unless explicitly superseded by a future governed contract-amendment
phase. It operates inside, and does not amend, the 125B Next
Architecture Direction Contract (still binding per 125B §7's
requirement that any Repository Intelligence extension follow its own
architecture → contract → verification → plan → implementation →
verification sequence) and inside the already-frozen 119Q
`historical_memory_snapshot.schema.json` (unchanged by this contract).

Later Track 127 phases may verify, plan, and implement only inside
this contract's constraints. No later phase may silently reinterpret
this contract as authorizing capability expansion, runtime behavior
change, execution capability, or a schema change without its own
separate, explicitly scoped governed contract-amendment phase.

## 3. Scope

The contract applies to:

- Historical Memory snapshots;
- historical timelines;
- historical events;
- historical transitions;
- historical provenance;
- historical context;
- historical evidence.

No new capability is introduced. The contract does not itself
construct, persist, query, or reason over historical content — those
remain implementation concerns for 127D-127E, bounded by this
contract.

Historical Memory shall not:

- infer unrecorded history;
- perform reasoning;
- predict future or past events beyond declared evidence;
- make decisions;
- execute actions;
- replace Repository Intelligence, Repository State, Evidence, or
  Decision Evaluation.

## 4. Historical Responsibilities

Historical Memory shall preserve, without modification of historical
facts:

- **Chronological ordering** — events and claims ordered by their own
  declared time reference, never by discovery or generation order.
- **Repository evolution** — the declared sequence of phases, releases,
  and artifact changes that produced the repository's current state.
- **Engineering continuity** — the record of how engineering work
  (phases, decisions, repairs, hardening) proceeded over time.
- **Architectural continuity** — the record of how architecture,
  contracts, and capabilities were defined, reviewed, frozen, and
  verified.
- **Implementation continuity** — the record of how schemas,
  prototypes, and integrations were implemented and verified.
- **Evidence continuity** — every historical claim's supporting
  evidence remains attached and unweakened across regenerations;
  corrections and supersessions preserve, never erase, what was
  previously recorded (119Q's `supersession_correction_record
  .preserved_history` field is the schema-level guarantee for this).
- **Provenance continuity** — every record's source attribution
  remains traceable to the specific source content it was derived
  from, never generalized or dropped across regenerations.

Historical Memory shall never rewrite what a prior snapshot declared —
regeneration extends the historical record with newly observable
events; it does not retroactively edit prior claims (Section 8.3).

## 5. Frozen Conceptual Model

The following mapping, established in 127A §5 by direct inspection of
the already-frozen 119Q schema's `$defs`, is re-frozen here as binding
for 127C-127F. No future phase may add, rename, reinterpret, or
collapse any of the following without a separate, governed
schema-amendment phase:

| Conceptual object | Frozen 119Q mapping |
| --- | --- |
| Historical Snapshot | `snapshot_identity` + top-level envelope |
| Historical Event | `historical_event` (closed `event_type` enum, 21 values) |
| Historical Timeline | `historical_window`/`historical_period` + ordered `historical_events`/`phase_lineage`/`release_lineage` arrays — **not** a dedicated `$def`; a declared ordering, never computed or inferred |
| Historical Relationship | `historical_relationship` (closed `relationship_type` enum, 12 values) |
| Historical Evidence | the repeated `source_attribution`/`evidence_links`/`verification_state`/`limitations` pattern on every record type — not a distinct record |
| Historical Transition | three distinct record types: `decision_history_record`, `repair_hardening_record`, `supersession_correction_record` |
| Historical Context | `historical_claim` |

The closed `event_type` enum (`phase_started`, `phase_completed`,
`architecture_defined`, `architecture_reviewed`, `contract_frozen`,
`contract_verified`, `schema_implemented`, `schema_verified`,
`prototype_added`, `integration_recorded`, `hardening_completed`,
`repair_completed`, `release_published`, `governance_check_completed`,
`report_generated`, `metadata_promoted`, `notification_sent`,
`decision_recorded`, `supersession_recorded`, `correction_recorded`,
`unknown`) and the closed `relationship_type` enum (`introduced_by`,
`changed_by`, `froze_contract`, `verified_by`, `repaired_by`,
`hardened_by`, `supersedes`, `corrects`, `included_in_release`,
`documents`, `related_to`, `unknown`) are both re-frozen here exactly
as 127A §5.2/§5.4 quoted them from the schema file — binding for
127C-127F.

**No taxonomy gap exists.** Unlike 126B, which had to resolve genuine
gaps 126A identified between the Dependency Knowledge Graph's frozen
enum and its fuller conceptual node/edge list, 127A found the entire
requested conceptual surface already fully represented in 119Q. 127B
therefore performs no gap-resolution work — there is none to perform.
127C must independently re-verify this "no gap" finding against the
schema file directly, not merely re-cite 127A's conclusion (mirroring
126C's own independent-re-derivation discipline).

## 6. Temporal Contract

Historical ordering shall be deterministic. Historical relationships
shall be reproducible. Equivalent repository history shall always
produce equivalent Historical Memory.

- **Deterministic ordering** — every `historical_event` carries an
  `event_time`; every `historical_claim` is scoped to a
  `historical_period`. A future generator must order events, claims,
  and lineage records by their own declared time reference (stable
  sort; ties broken by identifier), never by discovery, file-scan, or
  ambient ordering.
- **Reproducible relationships** — a `historical_relationship`'s
  existence and `direction` must be a pure function of explicit,
  declared source content; two independent runs against the same
  source snapshot(s) must produce the identical relationship set.
- **Snapshot lineage as data, not traversal** — `phase_lineage_record`'s
  `predecessor_phase_ids`/`successor_phase_ids` are declared fields, not
  values a generator computes by graph traversal. A future generator
  reads already-explicit lineage from governed phase-completion
  metadata and existing Repository Intelligence content; it does not
  infer lineage from timing proximity or heuristic matching.
- **Regeneration extends, never retroactively edits** — because
  Historical Memory's subject matter (past events) does not itself
  change retroactively, a new Historical Memory Snapshot must extend
  the historical record with newly observable events, never silently
  rewrite, delete, or reinterpret a prior snapshot's own claims. A
  correction is represented as a new `supersession_correction_record`
  referencing the superseded claim, with `preserved_history` intact
  (Section 4) — never as an in-place edit.

## 7. Evidence Contract

Historical Memory preserves, without reinterpretation:

- **Attribution** — every event, claim, lineage record, decision
  record, repair/hardening record, supersession/correction record, and
  relationship requires `source_attribution` (schema-required,
  `minItems: 1` where declared by 119Q) citing the specific source
  content it was derived from — never a generic "the repository" or
  "history" citation.
- **Provenance** — attribution must name a specific governed artifact
  (a phase report, a task contract, a commit reference, existing
  Repository Knowledge Snapshot content), matching the specificity
  standard 126B §7 already required for Dependency Knowledge Graph
  edges.
- **Limitations** — every record and the snapshot as a whole require
  at least one limitation record (`snapshot_limitations`,
  schema-required), preventing false completeness at any level of the
  artifact.
- **Boundary disclosures** — every Historical Memory artifact carries
  `boundary_disclosures` (the shared component: `read_only`,
  `no_execution`, `non_decision`, `advisory_non_authority`,
  `decision_evaluation_required`, `no_repository_mutation`,
  `no_lifecycle_mutation`, `no_evidence_replacement`,
  `no_repository_state_replacement`) and the frozen
  `historical_memory_snapshot_disclaimer` const string, unchanged.
- **No reinterpretation** — no future phase may reinterpret attribution
  as proof of historical truth, merge records in a way that loses
  per-record provenance, or convert a historical evidence gap into
  evidence support. This restates 126B §7's rule for the temporal
  layer.

## 8. Read-Only Contract

Historical Memory shall never mutate:

- **Repository Knowledge Snapshot** — read only, via the Track 121
  Query Layer; never modified, never regenerated by Historical Memory.
- **Dependency Knowledge Graph** — read only if and when a future
  cross-artifact reference is separately authorized (Section 5's
  table; not authorized by this contract); never modified or
  traversed.
- **Advisory Context** — never generated, modified, or consumed by any
  capability this contract authorizes.
- **Change Impact reports** — never generated, modified, or consumed
  by any capability this contract authorizes.
- **Repository state** — no repository scanning beyond what an
  already-approved Repository Intelligence generation performs; no
  file writes to source content; no lifecycle mutation.

Observe-only operation: a future Historical Memory generator reads
existing governed artifacts and produces a new, distinct artifact,
matching `boundary_disclosures`' const-`true` declarations exactly.

## 9. Failure Contract

Historical Memory shall fail closed whenever:

- **required evidence is missing** — a candidate historical event,
  claim, lineage record, or relationship lacking clear source support
  must be omitted (with a corresponding `unknown_gap` record — 119Q's
  own dedicated shape) or represented with an honestly
  `unknown`/`unverified` `verification_state` — never silently
  promoted into a confident-looking record;
- **provenance is incomplete** — missing or generic `source_
  attribution` blocks record creation entirely;
- **attribution is incomplete** — attribution that does not cite
  specific source content is treated as missing, not partially
  present;
- **chronology cannot be established** — an event or claim without a
  determinable `historical_time_reference`/`historical_period` must
  not be assigned a fabricated or estimated time; it fails closed
  (omitted or marked `unknown`);
- **required limitations are unavailable** — a record or snapshot
  lacking at least one limitation record fails closed;
- **required boundary disclosures are unavailable** — a snapshot
  lacking `boundary_disclosures`/`disclaimers` material fails closed.

A detected historical conflict (e.g. two sources disagreeing about
when an event occurred) must be represented honestly — via a
`conflicting` `verification_state` or a `conflict_or_supersession_
records` entry — never silently resolved by picking one source over
another without disclosure.

**No fail-open behavior.** This restates 125B §11's Failure Contract
and 126B §12's Failure Contract for the temporal layer. No future
phase this contract binds (127C-127F) may introduce a fail-open path.

## 10. Cross-Track Compatibility

The Historical Memory contract shall remain compatible with:

- **Track 119 executable schemas** — the already-frozen
  `historical_memory_snapshot.schema.json` (119Q,
  `119Q.1.0-json-schema`) without modification; this contract
  authorizes no schema change.
- **Track 120 Repository Knowledge Snapshot** — Historical Memory's
  primary input, reached exclusively through the Track 121 Query
  Layer; not modified by this contract or by any phase it binds.
- **Track 121 Query Layer** — Historical Memory's only access path
  into Repository Intelligence content; not modified by this
  contract. A future `historical_memory_query` category (already
  anticipated by 119Y's `query_type` enum, confirmed unimplemented in
  `SUPPORTED_QUERY_CATEGORIES` per 127A §6.3) remains unscoped and
  unauthorized here.
- **Track 122 Advisory Context** — not modified by this contract;
  Advisory's eventual consumption of Historical Memory content (119W's
  `historical_memory_package` package-type value already anticipates
  this) remains unscoped and unauthorized by this phase.
- **Track 123 Change Impact** — not modified by this contract; Change
  Impact's eventual consumption of Historical Memory content (per the
  Change Impact Report schema's own README rationale) remains unscoped
  and unauthorized by this phase.
- **Track 126 Dependency Knowledge Graph** — not modified by this
  contract; sibling, complementary artifact family. Any future
  cross-reference between a `historical_relationship` and a Dependency
  Knowledge Graph `node_id` remains unscoped and unauthorized by this
  phase (127A §6.6).

Compatibility means Historical Memory is additive to this existing
stack. It does not redefine any Track 119-126 contract, artifact
family, schema authority, Query Layer authority, Advisory authority,
Change Impact authority, Dependency Knowledge Graph authority, or
runtime authority.

## 11. Determinism Contract

Equivalent repository history shall always produce equivalent
Historical Memory artifacts. Serialization shall remain deterministic.

- Given the same set of source inputs (Repository Knowledge Snapshot
  content, governed phase-completion metadata, commit history at a
  fixed point), a future Historical Memory generator must produce the
  same `historical_events`, `historical_claims`, lineage records,
  relationships, and identifiers on every run.
- No historical claim, event, or relationship may be created by
  inference, heuristic guessing, probabilistic scoring, or AI-based
  interpretation. Every record must trace to an explicit, deterministic
  extraction rule applied to explicit source content — no third path
  exists under which a record could be created without deterministic
  support (mirroring 126C's own independent confirmation of this
  property for the Dependency Knowledge Graph contract).
- Ordering of events/claims/records within a serialized artifact must
  be deterministic (stable sort by declared time reference, then by
  identifier), consistent with the serialization discipline Track 124
  already hardened and Track 126 already reused
  (`serialize_deterministic_json`) — a future 127D plan should
  explicitly adopt this same shared helper rather than reintroducing
  parallel serialization logic, per the reuse precedent 126C Finding 2
  established and 126D/126E already applied.
- **Stable identifiers** — `event_id`, `claim_id`, `relationship_id`,
  and every other record's own identifier field must each be a
  deterministic function of their underlying source content, never an
  incidental generation-order artifact (e.g. `"event-1"`,
  `"event-2"`), stable across repeated generation from the same
  inputs, and unique within a single snapshot. This contract does not
  prescribe a specific identifier algorithm — that is a 127D planning
  decision — but any algorithm 127D selects must satisfy this
  determinism/stability/uniqueness standard, mirroring 126B §4.4's
  binding requirement for node/edge identifiers exactly.

## 12. Versioning Contract

Historical Memory shall consume only compatible Repository Intelligence
schema versions. Version incompatibility shall fail closed.

- The Historical Memory executable schema version is already frozen as
  `119Q.1.0-json-schema`; this contract does not change it. A future
  generator must reject an unsupported schema/version combination
  rather than guess compatibility, matching the version-compatibility
  discipline every Track 119-126 consumer already holds.
- Every Historical Memory artifact must record its own
  `snapshot_identity`, distinct from (but able to reference) the
  Repository Knowledge Snapshot(s) and any other artifacts it was
  derived from, so a Historical Memory Snapshot can never be
  interpreted independently of its source artifacts' own versions and
  limitations.
- A source Repository Knowledge Snapshot (or other consumed artifact)
  whose `executable_schema_version` the generator does not recognize
  must cause generation to fail closed — refusing to produce output
  rather than guessing compatibility.
- Regeneration, not incremental mutation, is the frozen model: a
  Historical Memory Snapshot is regenerated fresh, extending the
  historical record (Section 6), when the underlying repository/history
  changes. No patch/diff-based mutation model is authorized by this
  contract.

## 13. Governance Contract

Historical Memory shall remain, binding for every phase this contract
governs:

- **Observe-only** — unchanged; Section 8.
- **Deterministic** — Section 11.
- **Reproducible** — Section 6, Section 11.
- **Auditable** — every phase produces a complete, metadata-consistent
  canonical phase report; every Historical Memory artifact is
  independently inspectable.
- **Explainable** — every event, claim, and relationship traces to
  specific source content and, where a transformation was required, an
  explicit derivation rule; Section 7.
- **Execution unavailable** — runtime state remains `Observed`,
  maximum plugin capability remains `observe`, execution capability
  remains `unavailable`; no phase this contract binds (127C-127F) may
  change this boundary.

## 14. Deferred Capabilities

Explicitly deferred, not authorized by this contract:

- historical reasoning;
- timeline reasoning;
- causal inference;
- predictive analysis;
- recommendations;
- Decision Evaluation (integration);
- execution planning;
- execution capability;
- AI interpretation;
- graph traversal;
- Historical Memory Builder (generator);
- schemas (119Q remains frozen; no new value or field);
- storage implementation;
- timeline engine;
- repository scanning;
- runtime plugins.

Any future work in these areas requires its own separate, explicitly
scoped governed architecture and contract path outside this contract's
authorization. This contract also does not itself authorize any schema
change — Section 5's frozen conceptual model operates entirely within
the already-frozen 119Q schema and introduces no new value.

## 15. Technical Debt Classification

This phase classifies inherited technical debt only. It repairs none
of it.

- **Lifecycle/tooling debt**: 119Q report-generation-ordering defect;
  119AB phase-id comparison bug; recurring
  `pending_final_telegram_delivery` reporting detail.

**Not inherited defects — do not reintroduce**: 126G (Telegram
Canonical Report Dispatch Repair) and 126G.1 (Telegram Commit Trust
Metadata Repair) already resolved the notification-pipeline
content-fidelity gap (missing governance/test evidence, document
staleness risk, silent truncation) and the commit-trust-metadata gap
(`commits.phase_owned not verified`) each targeted. Both are closed,
verified repairs — neither is carried forward here, and no future
phase in this sequence may reintroduce either as if unresolved.

## 16. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this contract freeze.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this contract freeze.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.

## 17. Strict Non-Goals

This phase does not implement: Historical Memory Builder; generators;
schemas; storage; timeline engine; repository scanning; graph
traversal; reasoning; recommendations; execution planning; execution
capability; runtime plugins; source code; or test code.

## 18. Governance Compatibility

This contract is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- implementation remains deferred to a future explicit plan and
  implementation path;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 19. Relationship to Future Phases

- **127C - Historical Memory Contract Verification**: independently
  re-derive every enum, const string, and required-field claim in this
  contract directly from the frozen 119Q schema file (not from this
  contract's own quoted text), and independently re-confirm the "no
  taxonomy gap" finding, before verifying the contract complete,
  internally consistent, and implementation-ready.
- **127D - Historical Memory Plan**: define the bounded implementation
  plan inside this contract, including a concrete identifier algorithm
  (Section 11) and grounding every mapping decision in the actual
  behavior of the real Track 120/121 generator and Query Layer, per
  126D's own precedent for grounding conceptual claims against real
  system behavior.
- **127E - Historical Memory Implementation**: implement only the
  bounded generator authorized by 127B-127D.
- **127F - Historical Memory Verification**: independently verify
  127E's implementation against this contract and the 127D plan.

No 127C work begins in this phase.

## 20. Acceptance

127B is complete when this contract is frozen, project memory reflects
127B completion, runtime remains `Observed` / `observe` / execution
unavailable, no implementation has occurred, and the recommended next
phase is 127C - Historical Memory Contract Verification.
