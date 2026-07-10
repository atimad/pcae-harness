# Phase 129A - Historical Memory Chapter Review & Next Direction Architecture

## 1. Purpose

Tracks 127 (Historical Memory) and 128 (its hardening chapter) are
complete. This phase performs a chapter-level architectural review of
that completed work and reassesses PCAE's next architectural
direction against the canonical 125G Execution Planning Readiness
Assessment, now that two of 125G's named prerequisite gaps
(Dependency Knowledge Graph, Historical Memory) have moved from
schema-only to fully implemented, independently verified, and
hardened.

This phase is architecture and review only. It implements nothing,
changes no schema, no source code, no test code, and no runtime
behavior. It selects no next chapter - it recommends one, for a future
governed decision phase to accept or reject.

## 2. Historical Memory Chapter Review (Tracks 127-128)

### 2.1 Lifecycle summary

| Phase | Role | Outcome |
| --- | --- | --- |
| 127A | Architecture | Defined Historical Memory's conceptual model against the already-frozen 119Q schema; found zero taxonomy gaps. |
| 127B | Contract Freeze | Froze the binding Historical Memory contract (determinism, evidence, temporal, read-only, serialization, failure, governance, versioning). |
| 127C | Contract Verification | Independently re-derived every 127B claim from the 119Q schema file directly; confirmed no gap. |
| 127D | Prototype Plan | Defined the bounded implementation plan, including the identifier-stability algorithm and the (subsequently corrected, 127F) `git log --follow` derivation approach. |
| 127E | Prototype (Implementation) | Delivered the first real, deterministic, read-only Historical Memory Builder (`historical_builder.py`, `historical_validation.py`, `persistence.py`, `git_source.py`, `historical_generator.py`) plus governed CLI integration. |
| 127F | Verification | Independently found and fixed two genuine defects (stale `git log --follow` derivation-method strings; incomplete ordering-validation coverage for 2 of 6 collections) by re-reading source directly rather than trusting 127E's own passing tests. |
| 128A | Hardening Architecture | Reviewed the complete 127A-127F pipeline across eleven categories; found two non-blocking documentation-debt items (persistence subdirectory naming; unscoped optional DKG CLI input). |
| 128B | Hardening Contract Freeze | Froze the hardening-chapter contract, restating 127B unchanged. |
| 128B.1 | Notification Dispatch Reliability Repair | Governance tooling repair (not Historical Memory itself): fixed `pcae phase-report create`'s missing notification dispatch, discovered during 128B's own finalization. |
| 128B.2 | Phase Finalization Notification Contract | Governance documentation (not Historical Memory itself): defined PFN-001, elevating notification from implementation detail to lifecycle invariant. |
| 128C | Hardening Contract Verification | Independently re-derived every 128B claim from 128A, 127B, and real source; found two non-blocking documentation-precision findings (temporal-ordering wording; `historical_generator.py` scope-list naming). |
| 128D | Hardening Implementation Plan | Scoped 128E to exactly two narrow, non-behavioral changes resolving 128C's two findings. |
| 128E | Hardening Implementation | Implemented both approved items: an 11-line clarifying comment (0 executable-code lines changed) and forward-only scope documentation. |
| 128F | Hardening Verification | Independently re-verified 128E; wrote and ran an independent recursive schema validator against a freshly generated artifact (not trusting any prior "zero schema errors" claim) and found a genuine, pre-existing (127E-origin) schema-conformance defect - 903 violations across three field/type mismatches - repaired it with three minimal changes, and re-ran the complete verification clean. |

### 2.2 What this lifecycle demonstrates

Every layer of PCAE's own verification discipline was exercised and
held: 127C independently re-derived 127B rather than trusting it;
127F found real defects 127E's own tests missed; 128C independently
re-derived 128B; 128F found a real, more consequential defect that
127F, 128A, 128B, 128C, 128D, and 128E all missed, because each
relied on the same partial test coverage. The chapter's own internal
correction record (two 127F fixes, two 128C findings resolved by
128E, one 128F-discovered-and-repaired schema-conformance defect) is
itself evidence that PCAE's "do not trust prior claims, re-derive
from source" verification discipline works - each layer caught what
the layer before it missed, and no defect survived past the layer
built to catch it.

### 2.3 Final verified state

Historical Memory is now: implemented, independently verified,
hardened, schema-conformant (0 violations against the frozen 119Q
schema, confirmed via independent recursive validation), deterministic
(byte-identical output for equivalent input, repeatedly re-confirmed
across 127E, 127F, and 128F), read-only (zero mutation of repository,
git history, Repository Knowledge Snapshot, Dependency Knowledge
Graph, or task contracts - checksum-verified in 128F), fail-closed (12
independently re-enumerated fail-closed categories, all passing, plus
a direct CLI probe in 128F), and compatible with the completed
Repository Intelligence stack (Tracks 119-124, 126).

## 3. Architectural Achievements

Capabilities now available, each grounded in the specific component
that provides it:

- **Deterministic temporal reconstruction** - `git_source.py` +
  `historical_builder.py`'s `_sort_key`, resolving commit-derived
  chronology from real git plumbing, never inferred.
- **Historical snapshots** - the complete, schema-conformant
  `historical_memory_snapshot` artifact family (119Q), persisted via
  `persistence.py`.
- **Historical events** - 21 frozen `event_type` values (verified
  exact enum count, unchanged since 127A), each requiring
  `source_attribution`.
- **Historical transitions** - three distinct record types
  (`decision_history_record`, `repair_hardening_record`,
  `supersession_correction_record`), each schema-conformant as of
  128F's repair.
- **Historical relationships** - 12 frozen `relationship_type` values
  (verified exact enum count), each with `source_reference`/
  `target_reference` endpoint validation.
- **Historical evidence** - mandatory `source_attribution` on every
  record, traced to a real task-contract path or commit SHA, never a
  generic citation (independently confirmed in 128C and again in
  128F: 0 of 859 claims missing attribution).
- **Stable identifiers** - deterministic, content-derived
  `event_id`/`claim_id`/`relationship_id`/etc., never
  generation-order artifacts (`"event-1"`, `"event-2"`).
- **Chronological processing** - construction-time ordering by
  declared commit date, now explicitly documented as distinct from
  persisted ordering (128E's clarification, 128F-confirmed accurate).
- **Deterministic persisted ordering** - identifier-lexicographic
  ordering for every output collection, independently re-verified
  byte-reproducible across three separate phases' own regeneration
  (127E, 127F, 128F).
- **Provenance preservation** - every record's attribution traces to
  specific, real source content; never weakened or genericized across
  regeneration.
- **Limitation propagation** - every record and the snapshot as a
  whole carry at least one limitation record; independently
  re-confirmed 0 missing in 128F's fresh artifact.
- **Boundary disclosure propagation** - `boundary_disclosures`,
  `disclaimers`, and the frozen `historical_memory_snapshot_disclaimer`
  const string present on every generated artifact.
- **Fail-closed validation** - 12 independently re-enumerated
  fail-closed categories (missing/corrupted source, incompatible
  version, duplicate identifiers, invalid type, dangling endpoint,
  missing attribution/limitations/boundary, missing task history,
  chronology violation), all verified in 128F.
- **Read-only operation** - zero mutation path for repository
  contents, git history, Repository Knowledge Snapshot, Dependency
  Knowledge Graph (not even read - confirmed absent as a dependency),
  or task contracts; checksum-verified before/after generation in
  128F.

## 4. Knowledge-Stack Maturity Assessment

Six components, now all implemented (a change from 125G, where two
were schema-only):

| Component | Role | Maturity |
| --- | --- | --- |
| Repository Knowledge Snapshot (Track 120) | **What exists** - the deterministic, source-attributed inventory of repository entities, capabilities, and contracts. | Mature; verified (120E/120F), hardened (124), unchanged since. |
| Query Layer (Track 121) | The single governed access path into Repository Knowledge Snapshot content. | Mature; 6 query categories (`entity_lookup`, `capability_lookup`, `architectural_contract_lookup`, `attribution_lookup`, `limitation_lookup`, `boundary_lookup`), unchanged since 121E - **still RKS-only**; no `dependency_graph_query` or `historical_memory_query` category exists (confirmed by direct source inspection of `SUPPORTED_QUERY_CATEGORIES`, Section 7.1). |
| Advisory Context (Track 122) | **How deterministic evidence is assembled** - a bounded, non-authoritative context-assembly path over Repository Intelligence content. | Mature; verified, hardened, zero open defects at last inspection. |
| Change Impact (Track 123) | **What may be affected by change** - deterministic, descriptive identification of entities a declared change affects. | Mature at the flat-entity-model level; **still does not consume the Dependency Knowledge Graph** despite DKG now existing (confirmed: zero cross-imports between `change_impact/` and `dependency_graph/`, Section 7.2) - the exact gap 125G §3.5 named as "not yet satisfied," still not yet satisfied. |
| Dependency Knowledge Graph (Track 126) | **How entities are structurally related** - real, deterministic, traversable (but not itself traversing - graph *data*, not graph *reasoning*) structural relationship data. | Now implemented, verified, hardened. Was 125G's single largest identified gap; now closed as a standalone artifact family. |
| Historical Memory (Track 127-128) | **How the repository evolved over time** - deterministic temporal reconstruction of phase/release/repair lineage. | Now implemented, independently verified, hardened, and (as of 128F) schema-conformant with zero known open defects. Was 125G's second identified gap; now closed. |

**Combined assessment**: the knowledge foundation's *individual*
artifact-family maturity is now uniformly high across all six
components - every one is implemented, deterministic, source-
attributed, limitation-propagating, boundary-disclosing, and (as of
128F's repair) schema-conformant. What remains immature is
*integration between* components: Change Impact does not yet
structurally consume DKG; neither DKG nor Historical Memory is
reachable through the unified Query Layer; Historical Memory's own
optional DKG cross-reference field exists in its data model but has
no CLI entry point and is unexercised (127D/128A/128B/128C/128D/128E
all independently confirmed this unchanged). The knowledge *stack* is
therefore six mature, independently-correct silos, not yet one
integrated knowledge fabric - a materially different maturity profile
than 125G described (where two silos were entirely missing), and the
concrete next-layer gap this review identifies (Section 9).

## 5. Schema-Conformance Lessons (128F)

### 5.1 What happened

128F wrote an independent, dependency-free recursive JSON Schema
validator (no `jsonschema` library is available anywhere in this
environment - confirmed absent from both system Python and the
project's own `.venv`) and ran it against a freshly generated
Historical Memory artifact. It found 903 violations across three
distinct field/type mismatches, all traced via `git log -S` to Phase
127E - the original implementation, never caught by 127E's own tests,
127F's independent verification, or any of 128A-128E's own review/
verification/planning work.

### 5.2 Why existing coverage did not catch it

`tests/test_phase_127e_historical_memory_prototype.py`'s
`TestSchemaRequiredFieldConformance` class - the *only* schema-
conformance test coverage that existed - checked exactly three things:
top-level required fields, `historical_event` required fields, and
`phase_lineage_record` required fields. It never checked
`historical_claim.claim_type`'s enum validity, `repair_hardening_
record.phase_reference`'s type, or `unknown_gap.affected_period`'s
type - three fields on three different record types that happened to
fall entirely outside that partial coverage's scope. Every subsequent
phase's "zero schema errors" or "no taxonomy gap" claim was accurate
*relative to what it actually checked* - none of those claims were
false, but none of them checked full recursive schema conformance
either.

### 5.3 The architectural lesson

**Existing tests and regressions did not prove complete executable-
schema conformance.** Required-field-presence checks and enum checks
for a hand-selected subset of fields are not equivalent to validating
every field's type/enum/required-ness against the schema's own full
`$defs` graph, including cross-file `$ref`s. A test suite can report
100% pass with a systemic conformance defect present in the majority
of generated records, as this repository's own history now
demonstrates concretely rather than hypothetically.

### 5.4 Evaluation (not implementation) of future requirements

This phase evaluates, without implementing, whether future phases
require:

- **Mandatory full-artifact schema validation** - evaluated as
  **warranted for consideration**. 128F's own dependency-free
  recursive validator (roughly 100 lines, no external dependency,
  handles `$ref`/cross-file `$ref`/`required`/`type`/`enum`/`items`/
  `const`/`minItems`) is a concrete, reusable existence proof that
  this is achievable without adding a new dependency to the project.
  A future phase could evaluate promoting an equivalent validator into
  a shared test/CI utility usable by every Repository Intelligence
  artifact family (RKS, DKG, Historical Memory, Advisory, Change
  Impact), not just Historical Memory.
- **Independent schema-validation probes** - evaluated as **already
  demonstrated valuable** by 128F's own result (a real, previously-
  undetected defect found). Whether this becomes a standing governed
  practice (e.g., a required step in every future artifact-family
  verification phase) versus a one-off is a decision for a future
  governance phase, not this one.
- **Explicit field/enum/type coverage** - evaluated as a **gap worth
  closing** in the existing `TestSchemaRequiredFieldConformance`
  pattern specifically (extending it to cover every field this
  schema's `$defs` define, not a hand-selected subset) - but doing so
  is a test-code change, explicitly out of this phase's scope.
- **Conformance verification beyond focused tests** - evaluated as
  the correct general principle underlying all three items above:
  focused, hand-written required-field tests are necessary but not
  sufficient; systemic, schema-driven validation catches what
  hand-selected coverage structurally cannot.

**This phase does not implement any of the above.** These are
findings for a future phase (potentially a dedicated schema-
conformance-hardening chapter, Section 10's Candidate G) to act on.

## 6. Execution Planning Readiness Reassessment

This section re-derives 125G's own checklist against current,
directly-inspected state - not merely restating 125G's conclusion.

### 6.1 What changed since 125G

125G's "Not Ready" determination rested on two unsatisfied mandatory
prerequisites: Dependency Knowledge Graph maturity (§3.2) and
Historical Memory maturity (§3.3), both then schema-only. Both are
now fully implemented, independently verified, and hardened (Sections
2-4 above). This is a materially different starting point than 125G
had.

### 6.2 Re-derived prerequisite status (125G Section 9 checklist, reassessed)

| Item | 125G status | Current status | Basis |
| --- | --- | --- | --- |
| Repository Intelligence mature | Satisfied | **Satisfied**, unchanged | Tracks 120-124, no regression found. |
| Dependency Knowledge Graph mature | Not yet - schema frozen, no generator | **Satisfied** | Track 126 implemented, verified, hardened. |
| Historical Memory mature | Not yet - schema frozen, no generator | **Satisfied** | Tracks 127-128 implemented, independently verified, hardened, schema-conformant (128F). |
| Advisory Context mature | Satisfied | **Satisfied**, unchanged | No track modified it since. |
| Change Impact mature | Partially - flat entity model pending DKG | **Still partially** - DKG now exists but Change Impact does not yet structurally consume it (Section 4, confirmed via direct import inspection) | The specific blocker 125G named is now technically resolvable but has not yet been resolved. |
| Runtime Registry mature | Satisfied at passive-metadata level | **Satisfied**, unchanged | `runtime_registry.py` (464 lines) byte-identical to 125G-era state (confirmed via `git log`), zero plugins registered by design. |
| Permission Broker mature | Satisfied at read-only decision-aggregator level; unproven against real execution | **Unchanged** | `permission_broker.py` (1163 lines) byte-identical to 125G-era state; still unproven against real execution. |
| Rollback mature | Satisfied at simulation-model level only | **Unchanged** | No track since 125G targeted `enforcement_rollback.py`. |
| Audit chain complete | Satisfied at simulation-model level only | **Unchanged** | No track since 125G targeted `enforcement_audit.py`. |
| Deterministic evidence verified | Satisfied | **Satisfied**, unchanged | `decision_evaluation.py` (593 lines) byte-identical to 125G-era state. |
| Cross-component verification complete | Partial - Repository Intelligence only, no integration across governance/runtime | **Still partial**, and now additionally: no cross-component verification exists across the six knowledge-stack artifact families *themselves* either (Section 4's "six silos" finding is new information 125G could not have had, since two of the six did not yet exist). | New finding, Section 4. |
| Governance verification complete | Satisfied in isolation; not re-verified as an integrated whole | **Unchanged** | No integration attempt occurred. |

### 6.3 New prerequisite dimension: knowledge-stack integration

125G's checklist did not and could not evaluate whether the six
knowledge-stack components integrate with each other, because two of
them did not exist. Now that all six exist, this review adds a
prerequisite dimension 125G's own checklist structure did not
anticipate:

| Item | Status | Basis |
| --- | --- | --- |
| Unified Query Layer access to DKG/Historical Memory | **Unsatisfied** | `SUPPORTED_QUERY_CATEGORIES` remains RKS-only (Section 7.1); DKG and Historical Memory are each reachable only via their own direct file-load path, not the governed Query Layer. |
| Change Impact structurally informed by DKG | **Unsatisfied** | Section 4; zero cross-imports. |
| Historical Memory's own DKG cross-reference wired | **Unsatisfied (by design, unscoped)** | 127D/128A-128E all confirmed the data-model hook exists but is deliberately unexercised; not a defect, an explicit scope boundary. |
| Full-artifact schema-conformance verification, standing practice | **Unsatisfied** | Section 5; 128F's approach is a one-off, not yet a governed standing requirement. |

### 6.4 Overall prerequisite status matrix

Classified per this phase's own required categories:

- **Satisfied**: Repository Intelligence maturity; Dependency
  Knowledge Graph maturity; Historical Memory maturity; Advisory
  Context maturity; Runtime Registry maturity (passive level);
  deterministic evidence chain (Decision Evaluation); fail-closed
  behavior across every inspected subsystem; boundary disclosure
  consistency; provenance/attribution consistency.
- **Partially satisfied**: Change Impact maturity (flat-model
  satisfied, structural-model via DKG not yet wired); cross-component
  verification (satisfied within each artifact family, not across
  the six-component knowledge stack or across knowledge+governance
  subsystems); Permission Broker/rollback/audit maturity (mature as
  models, unproven against real execution - unchanged from 125G).
- **Unsatisfied**: unified Query Layer access to DKG/Historical
  Memory; Change Impact-DKG structural integration; standing
  full-artifact schema-conformance verification practice; any real
  (non-simulation) exercise of permission/approval/rollback/audit
  subsystems.
- **Optional enhancement**: Historical Memory's DKG cross-reference
  wiring (explicitly scoped as optional since 127D); multi-hop/
  path-based DKG traversal (explicitly out of Track 126's initial
  scope); quantified Change Impact blast-radius scoring (explicitly
  out of Track 123's contract).

### 6.5 Planning architecture vs. execution authority

This review explicitly distinguishes four separable concepts, per
this phase's own instruction not to conflate them:

1. **Planning architecture** - a descriptive representation of a
   proposed change and its structural/temporal/impact context,
   authored using already-mature, read-only knowledge-stack content
   (RKS + DKG + Historical Memory + Change Impact + Advisory). This
   is, in principle, buildable today: it would consume only
   already-deterministic, already-verified, read-only data, and would
   itself perform no execution, exactly as Decision Evaluation
   consumes only Evidence and performs no execution.
2. **Plan evaluation** - assessing a planning representation against
   governance invariants (Decision Evaluation's six existing
   deterministic invariant families are a plausible consumer/pattern
   for this, per 125E §3.4's own finding that Decision Evaluation is
   "arguably a better-suited consumer of Repository Intelligence's
   own deterministic guarantees than a hypothetical non-deterministic
   subsystem would be").
3. **Execution authorization** - a governed decision granting
   permission for a specific, bounded action - requires Permission
   Broker, approval gate, and audit subsystems to move from
   simulation-model maturity to real-execution-proven maturity
   (Section 6.2's still-unproven items). Not satisfied today.
4. **Actual execution** - requires runtime execution capability,
   which remains, and must remain, `execution_unavailable` per every
   governance contract this repository has ever frozen, including
   PFN-001 (Section 8) and every prior runtime-boundary contract.
   Explicitly out of scope for any near-term chapter.

**Finding**: item 1 (planning architecture) is now more plausible than
125E's own assessment judged it to be, precisely because the knowledge
foundation 125E found entirely absent for this candidate ("no schema,
no Query Layer support, no consumer exists") is now substantially less
absent - Repository Intelligence, DKG, and Historical Memory
collectively provide exactly the kind of structural/temporal context a
planning representation would need to describe a proposed change
against. Items 2-4 remain gated on prerequisites this review confirms
are still unsatisfied (Section 6.4) or explicitly out of scope. A
future "Execution Planning Architecture" chapter, if selected, would
need to be scoped explicitly and narrowly to item 1 alone (a
descriptive planning representation, itself non-executing, consuming
only already-verified read-only knowledge-stack content) - conflating
it with items 2-4 would repeat exactly the boundary-blurring risk
125A §7.5 and 125E's own Execution Planning assessment warned against.

### 6.6 Readiness determination

Applying 125G §10's own three-outcome model (Not Ready / Conditionally
Ready / Ready) to the reassessed evidence:

**Determination: Conditionally Ready for a narrowly-scoped Execution
Planning *architecture* chapter (item 1, Section 6.5); Not Ready for
plan evaluation, execution authorization, or execution itself.**

This is a genuinely different determination than 125G's own blanket
"Not Ready," made possible specifically because 125G's two named
mandatory-prerequisite gaps are now closed. It is not a determination
that execution readiness generally has improved - permission,
approval, rollback, and audit subsystems remain exactly as unproven
against real execution as 125G found them (Section 6.2), and the
knowledge-stack integration gaps this review newly identifies
(Section 6.3) are real, unsatisfied prerequisites for anything beyond
a narrowly-scoped planning-architecture chapter.

## 7. Direct Re-Inspection Evidence

Concrete evidence this review's claims are grounded in, not asserted:

### 7.1 Query Layer category set (unchanged since 121E)

`src/pcae/repository_intelligence/query/query_request.py`'s
`SUPPORTED_QUERY_CATEGORIES`: `entity_lookup`, `capability_lookup`,
`architectural_contract_lookup`, `attribution_lookup`,
`limitation_lookup`, `boundary_lookup` - six categories, all RKS-
scoped, zero DKG or Historical Memory categories.

### 7.2 Change Impact / Dependency Knowledge Graph cross-imports

`grep -rl "dependency_graph\|DependencyGraph" src/pcae/repository_
intelligence/change_impact/` returns zero matches.

### 7.3 Governance/runtime subsystem line counts (byte-identical to 125G-era)

`src/pcae/core/decision_evaluation.py` (593 lines), `src/pcae/core/
permission_broker.py` (1163 lines), `src/pcae/core/runtime_
registry.py` (464 lines) - `git log --oneline` confirms zero commits
to any of these three files since before 125G, and line counts match
125G's own cited figures exactly.

## 8. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), restated here
as still globally binding, not amended:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. Confirmed still binding; every phase since 128B.2 (128C, 128D,
  128E, 128F) satisfied it, each via the `pcae phase-report create`
  recovery path (itself the subject of 128B.1's repair) after `pcae
  phase complete`/`pcae task finish --commit` were rejected by the
  same pre-existing stale `.pcae/phase-completion-metadata.json`
  (Section 9).
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited.
  This phase (129A) will itself satisfy PFN-001 identically, via the
  same recovery path, dispatching exactly one trusted notification for
  this phase's own canonical report.
- **No amendment.** This phase does not modify PFN-001's own contract
  text (`docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`),
  consistent with that document's own amendment-authority rule.

**PFN-001 remains globally applicable, unchanged, and satisfied.**

## 9. Known Inherited Issues (Re-Evaluated, Not Copied)

Re-derived directly from current state, not copied from any prior
phase's list:

- **119Q report-generation-ordering defect** - re-confirmed still
  present (no phase since has targeted it); lifecycle/tooling debt,
  non-blocking.
- **119AB phase-id comparison bug** - re-confirmed still present; same
  classification.
- **`.pcae/phase-completion-metadata.json` staleness** - re-confirmed
  as an active, recurring, concrete issue: every phase since at least
  128B has independently hit the identical `pcae phase complete`/
  `pcae task finish --commit` rejection (`Disagreeing phase identity
  sources: ['126E', '<current-phase>']`) because this file has not
  been refreshed since Phase 126E. This is a more precise
  re-statement of the older, vaguer "119AB phase-id comparison bug"
  entry some prior phases carried forward - re-evaluated here as its
  own concrete, recurring, still-unrepaired lifecycle/tooling debt
  item, not a stale copy-paste of an old bullet.
- **Recurring `pending_final_telegram_delivery` reporting detail** -
  re-confirmed still present as a *possible* transient state for a
  report generated before Telegram env is sourced; not observed as an
  active problem in any recent phase (128B.1 onward), since every
  recent phase sources `~/.config/pcae/telegram.env` before dispatch.
  Downgraded here from "recurring issue" to "latent, currently
  dormant" - re-evaluated, not blindly copied forward as still active.

**Explicitly not carried forward, because they are closed, verified
repairs, not open debt** (confirmed by direct check against each
repair's own scope):

- **126G / 126G.1** - Telegram canonical report dispatch and commit-
  trust-metadata repairs; both closed, both remain closed (no
  regression found in any phase since).
- **128B.1** - notification dispatch reliability repair; closed. The
  `.pcae/phase-completion-metadata.json` staleness issue above is
  explicitly a *different* defect than what 128B.1 repaired - 128B.1
  fixed the *dispatch path* being entirely absent from `pcae phase-
  report create`; the metadata staleness issue is a *separate*,
  still-open, upstream cause of why `pcae phase complete` itself keeps
  getting rejected in the first place. Conflating the two would be
  exactly the kind of stale-copy error this section is required to
  avoid.
- **128B.2** - PFN-001 governance contract; closed, confirmed still
  binding (Section 8).
- **128A/128B/128C/128D/128E/128F's own two-then-one findings** - all
  resolved within Track 128 itself (persistence naming remains
  carried-forward *debt*, not a defect requiring repair; the temporal-
  wording and scope-naming findings were resolved in 128E; the
  schema-conformance defect was repaired in 128F). None of these are
  re-opened or re-carried-forward as if unresolved.

**Genuine remaining tooling debt, carried forward unrepaired by this
phase**:

1. `.pcae/phase-completion-metadata.json` staleness (concrete,
   recurring, precisely re-stated above).
2. 119Q report-generation-ordering defect.
3. 119AB phase-id comparison bug.
4. Historical Memory / DKG / RKS persistence subdirectory naming
   inconsistency (`snapshots/` vs. `graphs/`) - still present, still
   cosmetic, still correctly classified as non-blocking documentation
   debt (128A-128F all independently re-confirmed this unchanged).

## 10. Candidate Next Directions

Evaluated against: architectural cohesion, prerequisite readiness,
governance compatibility, determinism, explainability, auditability,
reproducibility, safety, strategic value, implementation complexity,
and contribution toward eventual controlled execution.

### Candidate A - Decision Evaluation Support (Repository Intelligence integration)

Wire a bounded, explicitly-scoped subset of Decision Evaluation's six
existing invariant families to consume Repository Intelligence content
(via Advisory Context, preserving "Evidence never decides"). **Cohesion**:
high - builds on two already-mature subsystems. **Prerequisite
readiness**: high - both sides (Decision Evaluation, Advisory Context)
are unchanged-mature since 125G/125E. **Governance compatibility**:
high, if scoped to preserve non-authority exactly as Tracks 122/123
already demonstrate. **Determinism/explainability/auditability**: high
- Decision Evaluation's own design is already built for these.
**Safety**: high - no execution surface. **Strategic value**: high -
directly closes 125E's own identified integration gap. **Complexity**:
moderate-high (bounding new input without expanding authority is
delicate, per 125E's own finding). **Contribution to eventual
execution**: high - this is exactly the kind of deterministic,
evidence-only decision surface controlled execution would eventually
need.

### Candidate B - Repository Intelligence Query Expansion (DKG/Historical Memory query categories)

Extend the Query Layer's `SUPPORTED_QUERY_CATEGORIES` to cover DKG and
Historical Memory content, closing Section 6.3's "unsatisfied" unified-
access gap. **Cohesion**: high - a direct, narrow extension of an
existing, proven pattern (six categories already exist). **Prerequisite
readiness**: high - both DKG and Historical Memory are now mature,
schema-conformant sources. **Governance compatibility**: high - purely
additive, read-only. **Determinism/explainability/auditability**: high
- would inherit the Query Layer's existing guarantees. **Safety**: high.
**Strategic value**: high - this is the most direct way to convert
"six independently mature silos" (Section 4) into one integrated
knowledge fabric. **Complexity**: low-moderate - the pattern is proven
three times already (RKS's six categories); extending it to two more
artifact families is incremental, not novel. **Contribution to eventual
execution**: moderate - a unified query surface is infrastructure a
future planning architecture (Candidate F) would directly depend on.

### Candidate C - Cross-Artifact Knowledge Integration (Change Impact + DKG)

Wire Change Impact to structurally consume the Dependency Knowledge
Graph, closing the specific gap 125G §3.5 named as "not yet satisfied"
and Section 4/6.2 confirm remains unsatisfied today. **Cohesion**:
high - a named, expected next step for Track 123 since its own
contract. **Prerequisite readiness**: high - DKG now exists. **Governance
compatibility**: high - both sides already independently verified,
read-only. **Determinism/explainability/auditability**: high.
**Safety**: high. **Strategic value**: high - directly strengthens
Change Impact from "flat entity model" to "structurally-informed,"
the single most concretely-named limitation in 125G's entire
assessment. **Complexity**: moderate - requires Change Impact's own
consumer boundary to add a second Repository Intelligence input
without weakening its own non-authority/read-only guarantees.
**Contribution to eventual execution**: high - structurally-aware
blast-radius identification is a direct prerequisite for any future
planning representation's usefulness.

### Candidate D - Additional Schema-Conformance Hardening

Promote 128F's dependency-free recursive schema validator into a
shared, standing test/CI utility applied to every Repository
Intelligence artifact family (RKS, DKG, Historical Memory, Advisory,
Change Impact), closing Section 5.4's identified gap. **Cohesion**:
high - a direct generalization of a proven, working tool. **Prerequisite
readiness**: high - the validator already exists and already found a
real defect. **Governance compatibility**: high - pure verification
tooling, no behavioral surface. **Determinism/explainability/
auditability**: high - schema conformance is itself a determinism/
correctness property. **Safety**: high. **Strategic value**: moderate-
high - 128F's own result (903 real violations found in one artifact
family alone) suggests non-trivial probability of finding similar
latent defects in RKS/DKG/Advisory/Change Impact, none of which has
ever been checked this way. **Complexity**: low - the validator is
~100 lines, already written, dependency-free. **Contribution to
eventual execution**: moderate - trustworthy, schema-conformant
knowledge artifacts are a baseline prerequisite for anything consuming
them, including a future planning architecture.

### Candidate E - Permission Broker Evolution

Advance Permission Broker, approval gate, rollback, and audit
subsystems from simulation-model maturity toward real-execution-proven
maturity via a bounded, explicitly-scoped pilot. **Cohesion**: moderate
- orthogonal to the knowledge stack, adjacent to governance
infrastructure. **Prerequisite readiness**: moderate - the models
themselves are mature (Section 7.3, unchanged since 125G) but have
never been exercised against real execution, by design. **Governance
compatibility**: requires extreme care - this is the candidate closest
to the execution boundary among the "infrastructure-adjacent" options.
**Determinism/explainability/auditability**: high at the model level;
unproven at the real-exercise level. **Safety**: the central open
question - a "bounded pilot" is exactly the kind of step 125G §10's
"Conditionally Ready" outcome describes, but this review does not find
the knowledge-stack integration prerequisites (Section 6.3) satisfied
enough yet to recommend this as the *immediate* next step. **Strategic
value**: high long-term, low immediate (per 125E's own original
assessment, unchanged). **Complexity**: high. **Contribution to
eventual execution**: highest of any candidate, definitionally - but
premature relative to Candidates B/C's lower-risk, more immediately
actionable integration work.

### Candidate F - Execution Planning Architecture (narrowly scoped to planning representation only)

Per Section 6.5's explicit distinction: a descriptive planning
representation (not evaluation, not authorization, not execution),
consuming only already-mature, read-only knowledge-stack content.
**Cohesion**: moderate - would be a genuinely new chapter, but one now
groundable in real, mature knowledge-stack content in a way 125E found
entirely absent. **Prerequisite readiness**: **improved since 125E**,
per Section 6.5's finding - still gated on Candidates B/C's integration
work being more valuable to do first (a planning representation
without unified query access or DKG-informed impact data would be
weaker than one built after Candidates B/C). **Governance compatibility**:
requires the same extreme care 125E identified - must be scoped to
exclude items 2-4 of Section 6.5 explicitly and by name in its own
contract, not merely by convention. **Determinism/explainability/
auditability**: achievable if scoped correctly (a pure descriptive
representation can be exactly as deterministic/explainable as any
other Repository Intelligence artifact). **Safety**: the central risk
this review inherits directly from 125E - boundary-blurring risk is
real and must be the first thing any future contract for this
candidate addresses. **Strategic value**: high, if the knowledge
foundation is further integrated first (Candidates B/C). **Complexity**:
high - new chapter, no existing pattern to extend, unlike Candidates
A-D. **Contribution to eventual execution**: highest of any near-term-
plausible candidate (Candidate E is higher but is not near-term-
plausible per this review).

### Candidate G - Other Justified Candidates (Repository Intelligence expansion, richer artifact families)

Considered and not separately elaborated: 125E's own "Repository
Intelligence expansion (richer artifact families)" candidate remains
available but this review finds no new evidence changing 125E's own
assessment of it (low risk, high maintenance-burden-per-value
relative to Candidates B/C, which close named, concrete gaps rather
than adding speculative new artifact families).

## 11. Remaining Architectural Gaps

Consolidated from Sections 4, 5, 6, and 9:

- **Knowledge integration**: Query Layer does not yet cover DKG/
  Historical Memory (Candidate B); Change Impact does not yet consume
  DKG structurally (Candidate C); Historical Memory's own DKG
  cross-reference remains unwired (explicitly optional, not a gap
  requiring repair).
- **Decision Evaluation**: integration surface with Repository
  Intelligence remains entirely unbuilt (Candidate A); the subsystem
  itself is mature and unchanged.
- **Advisory interpretation**: Advisory Context remains bounded to
  context assembly, not interpretation/reasoning - no track has
  proposed expanding this, and this review does not identify a
  concrete need to.
- **Permission governance / approval governance / rollback guarantees
  / execution boundary enforcement**: all mature at the model/
  simulation level, all unchanged and unproven against real execution
  since 125G (Candidate E; Section 6.2).
- **Runtime capability governance**: unchanged since 125G; passive-
  metadata registry, zero plugins, by design.
- **Lifecycle/reporting tooling**: `.pcae/phase-completion-
  metadata.json` staleness is a genuine, recurring, currently-
  unrepaired gap (Section 9) - every phase since 128B has independently
  hit and worked around it via the `pcae phase-report create`
  recovery path.
- **Schema-conformance verification**: no standing practice exists
  beyond 128F's one-off application to Historical Memory alone
  (Candidate D); RKS, DKG, Advisory, and Change Impact have never been
  checked this way.

## 12. Maturity Assessment

Historical Memory and the broader knowledge layer, assessed against
each required dimension:

- **Determinism**: high across all six knowledge-stack components;
  independently re-verified multiple times for Historical Memory
  specifically (127E, 127F, 128F).
- **Completeness**: high within each artifact family's own declared
  scope; incomplete across the *integration* dimension (Section 11).
- **Provenance**: high; mandatory, verified source attribution
  throughout.
- **Schema conformance**: high for Historical Memory specifically, as
  of 128F's repair (0 violations, independently verified); **unknown**
  for RKS, DKG, Advisory, and Change Impact, since no equivalent
  independent recursive validation has ever been run against them
  (Section 5.4/Candidate D - this is a genuine open question this
  review surfaces, not a claim that defects definitely exist
  elsewhere, but also not a claim that they definitely don't).
- **Limitation propagation**: high; independently re-verified.
- **Boundary disclosures**: high; independently re-verified.
- **Maintainability**: high; every artifact family follows the same
  established generator/validator/persistence pattern, and Historical
  Memory's own hardening chapter (128A-128F) demonstrates the pattern
  scales to catching and fixing real defects without architectural
  disruption.
- **Reproducibility**: high; every governed phase produces a
  reproducible canonical report; every artifact family produces
  byte-reproducible output.
- **Auditability**: high for the knowledge stack itself; unchanged-
  moderate (model-level only) for governance/permission/audit
  subsystems (Section 6.2).
- **Explainability**: high; every record traces to specific source
  content or an explicit derivation rule.
- **Readiness for downstream consumers**: high for read-only,
  non-authoritative consumption (exactly what Advisory Context and
  Change Impact already demonstrate is safe); not yet evaluable for
  authoritative or execution-adjacent consumption, which remains
  correctly gated behind Section 6's still-unsatisfied prerequisites.

## 13. Recommended Roadmap

This review recommends, without beginning, the following high-level
sequence:

1. **Next chapter: Candidate C (Cross-Artifact Knowledge Integration -
   Change Impact + Dependency Knowledge Graph)** or **Candidate B
   (Query Layer expansion to DKG/Historical Memory)** - both are
   low-complexity, high-strategic-value, directly close named,
   concrete gaps this review and 125G both identify, and both move
   the knowledge stack from "six mature silos" toward "one integrated
   knowledge fabric" with minimal governance risk. Between the two,
   Candidate C has a slightly more concrete, longer-standing precedent
   (125G §3.5/§12 named it explicitly as the direct next step after
   DKG's own completion); Candidate B is architecturally prerequisite
   to Candidate F should that be pursued later. A future governed
   decision phase (mirroring 125E/125F's own process) should choose
   between them, informed by this review but not bound by it.
2. **Following that: Candidate A (Decision Evaluation Support) and/or
   Candidate D (Schema-Conformance Hardening)** - both remain
   high-value, moderate-complexity, and do not depend on Candidates
   B/C completing first (they could in principle proceed in parallel
   or in either order).
3. **Execution Planning remains deferred - but the reason has
   changed.** Per Section 6.6: this review does not conclude Execution
   Planning is deferred merely because execution is unavailable
   (execution-unavailable is a permanent, correct governance boundary,
   not a temporary blocker to reason from). It is deferred because
   (a) plan evaluation, execution authorization, and actual execution
   (Section 6.5 items 2-4) remain gated on Permission Broker/approval/
   rollback/audit subsystems that are unchanged since 125G and still
   unproven against real execution, and (b) even a narrowly-scoped
   planning-*architecture*-only chapter (item 1) would be
   better-grounded after Candidates B/C strengthen the knowledge
   foundation it would consume. **If a future decision phase judges
   the knowledge foundation sufficiently integrated without waiting
   for Candidates B/C, a narrowly-scoped Execution Planning
   Architecture chapter (Candidate F, item 1 only) is now eligible for
   selection** - this is a genuine change from 125E's own assessment,
   made possible by Tracks 126-128's completion, and this review
   explicitly does not recommend against it being selected next; it
   recommends Candidates B/C as *higher-value, lower-risk* precursors,
   not as mandatory gates.
4. **Ongoing, independent of chapter sequencing**: repair the
   `.pcae/phase-completion-metadata.json` staleness (Section 9) at the
   next convenient governance-tooling-repair phase, mirroring 128B.1's
   own precedent - this is not itself a candidate architectural
   chapter, but a recurring tooling-debt item every phase since 128B
   has had to work around.

## 14. Governance Compatibility

This review is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- no architectural chapter was selected or begun;
- no implementation occurred;
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- canonical reports remain complete and metadata-consistent;
- PFN-001 remains satisfied (Section 8);
- human-controlled lifecycle authority remains unchanged - this review
  recommends, it does not decide.

## 15. Strict Non-Goals

This phase does not implement: a new architectural chapter; Decision
Evaluation; Advisory reasoning; graph traversal; Historical Memory
expansion; Execution Planning; execution capability; runtime plugins;
schema changes; source code; test code.

## 16. Confirmations

- **No implementation occurred.** This phase produced only
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**

## 17. Conclusion

The Historical Memory hardening chapter (128A-128F) is complete, and
its own internal correction record - two 127F fixes, two findings
resolved in 128E, one substantial schema-conformance defect found and
repaired in 128F - is itself evidence that PCAE's layered
verification discipline functions as designed. The combined knowledge
stack (Repository Knowledge Snapshot, Query Layer, Advisory Context,
Change Impact, Dependency Knowledge Graph, Historical Memory) is now
uniformly mature at the individual-artifact-family level for the
first time in this repository's history, but remains six independent
silos rather than one integrated knowledge fabric - the concrete
architectural gap this review identifies as the highest-value near-
term target. Execution Planning readiness has genuinely improved
since 125G (both of its named mandatory gaps are now closed), but
remains gated on knowledge-integration work (Candidates B/C) and
unproven governance/permission subsystems (Candidate E) - not on
execution-unavailability itself, which is a permanent boundary, not a
temporary blocker. A narrowly-scoped Execution Planning Architecture
chapter (descriptive planning representation only, explicitly
excluding evaluation/authorization/execution) is now a genuinely
eligible future candidate, distinguished carefully from execution
authority, which remains and must remain unavailable.

Recommended next phase: a future governed decision phase (mirroring
125E/125F's process) selecting between **Candidate B (Repository
Intelligence Query Expansion)** and **Candidate C (Cross-Artifact
Knowledge Integration: Change Impact + Dependency Knowledge Graph)**
as the next architectural chapter.
