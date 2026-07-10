# Phase 128A — Historical Memory Chapter Review & Hardening Architecture

## Status

Complete.

## Track 128 Purpose

Track 128 reviews and hardens the complete Historical Memory subsystem
produced by Track 127 (127A-127F) before PCAE introduces additional
Historical Memory capabilities. This mirrors Track 124's role for
Repository Intelligence (Tracks 119-123) directly — Track 124 hardened
the prototype pipeline before extension; Track 128 does the same for
Historical Memory.

The purpose is to improve consistency, maintainability, determinism,
governance compatibility, and extensibility of the existing Historical
Memory implementation.

Track 128 does not introduce new Historical Memory capabilities. It
reviews and hardens what already exists. No new Historical Memory
capabilities are introduced.

## Scope

Track 128 reviews the existing Track 127 implementation as one
architectural system. Unlike Track 124 (which reviewed four sibling
components — Repository Knowledge Snapshot, Query Layer, Advisory
Context Builder, Change Impact Builder — as one pipeline), Historical
Memory is a single builder with several internal stages; the review
therefore examines that builder's internal consistency and its
external relationships with the five other completed Repository
Intelligence artifact families, rather than inter-component boundaries
within Track 127 itself.

Applies to the complete Track 127 implementation, including:

- Historical Memory Builder (`historical_builder.py`);
- Timeline generation (chronological ordering, `historical_window`,
  `historical_period`);
- Event generation (`historical_event`, `event_type` classification);
- Transition generation (`repair_hardening_record`,
  `decision_history_record`, `supersession_correction_record`);
- Evidence mapping (`source_attribution`, `verification_state`,
  `limitations` propagation);
- Temporal reconstruction (`git_source.py`'s commit/task-contract
  resolution);
- Serialization (`persistence.py`'s reuse of
  `serialize_deterministic_json`);
- CLI integration (`pcae repository-intelligence historical-memory
  generate`).

## Review Objectives

Track 128 should identify opportunities to improve, without expanding
functionality:

- implementation consistency;
- terminology consistency;
- evidence consistency;
- limitation propagation consistency;
- boundary disclosure consistency;
- serialization consistency;
- deterministic behavior;
- interface consistency;
- documentation consistency;
- governance consistency;
- testing consistency.

No functionality expansion. The review classifies opportunities before
any future implementation; it must not treat every inconsistency as a
defect requiring immediate repair — some may be acceptable prototype
divergence, future hardening, or lifecycle/tooling debt, exactly as
124A established for Repository Intelligence.

## Complete Historical Memory Pipeline Review

The complete Track 127 pipeline now consists of:

1. **Frozen conceptual model** — 119Q's already-frozen
   `historical_memory_snapshot.schema.json` defines the artifact
   shape and schema compatibility expectations (mirrors 119's role for
   Track 124).
2. **Architecture, contract, verification, plan** — 127A-127D define
   what Historical Memory is, freeze its binding contract,
   independently verify that contract, and plan the bounded
   implementation.
3. **Historical Memory Builder** — 127E produces the first
   deterministic, read-only Historical Memory artifact family,
   consuming git-tracked `tasks/done/*.md` task contracts, git commit
   history, and an existing Repository Knowledge Snapshot (via the
   Track 121 Query Layer, for structural cross-reference only).
4. **Verification** — 127F independently verified 127E against the
   full evidence chain and found (and fixed) two genuine defects: stale
   `git log --follow` derivation-method claims baked into generated
   artifact content, and incomplete ordering-validation coverage for
   two of six sortable collections.

Track 128 reviews this pipeline as a system of contracts:

- Repository Knowledge Snapshot (Track 120) and git/task-contract
  history are Historical Memory's only inputs; the builder never
  regenerates either.
- The Track 121 Query Layer is Historical Memory's exclusive access
  path into Repository Intelligence content specifically; git/task-
  contract discovery is a *separate*, equally bounded access path,
  since task contracts are governance artifacts, not Repository
  Intelligence content (127D §5.1's own scoping — confirmed again in
  this review, Architecture category below).
- Historical Memory is additive to, and does not redefine, Tracks
  119-126.
- Runtime remains observe-only and execution unavailable.

## Hardening Architecture

Hardening is an architectural review and consolidation process, not a
capability expansion process — restated from 124A, binding identically
here.

Track 128 hardening should proceed through these review categories.

### Architecture

Review component responsibilities, ownership boundaries, and
cross-track relationships.

Questions, with concrete observations from this review:

- Is the Track 121 Query Layer still the exclusive access boundary for
  Repository Intelligence content? **Confirmed**: `historical_builder.py`
  reaches Repository Knowledge Snapshot content exclusively through
  `execute_query()`/`load_snapshot()`; direct file reads occur only
  for task contracts and git history (via `git_source.py`), which
  127D §5.1 explicitly and correctly scoped as outside the Query Layer
  boundary — task contracts are governance artifacts, not Repository
  Intelligence content, so this is not a boundary violation. A future
  128B contract freeze should state this distinction explicitly and
  permanently, since a reader unfamiliar with 127D's reasoning could
  otherwise mistake it for an inconsistency.
- Are producer and consumer responsibilities clearly separated?
  **Confirmed**: Historical Memory is a consumer of Track 120 content
  and a producer of its own artifact family; it does not redefine
  Track 120's own producer role.
- Are Repository State, Evidence, Advisory output, Decision
  Evaluation, and Repository Intelligence still distinguished?
  **Confirmed**: `boundary_disclosures`/`disclaimers`/the frozen
  `historical_memory_snapshot_disclaimer` const string preserve this
  distinction unchanged, independently re-verified in 127F.
- Is `git_source.py`'s subprocess boundary still the sole permitted
  one? **Confirmed**: `historical_builder.py` and
  `historical_validation.py` import no `subprocess`, verified by
  dedicated AST-based tests; `git_source.py` remains the only module
  permitted to invoke `git`, mirroring `source_inventory.py`'s
  established Track 120 precedent exactly.

### Contracts

Review whether architecture documents, frozen contracts,
implementation plans, implementations, and verification reports align
across 127A-127F.

Questions:

- Are normative requirements stated once and referenced consistently?
  **Largely yes** — 127D explicitly incorporated and resolved both
  127C findings, and 127F's own two corrections were scoped narrowly
  to the implementation, not the contract; the contract itself needed
  no amendment.
- Are contract terms stable across phases? **Confirmed** — the frozen
  119Q conceptual model was never reinterpreted across 127A-127F.
- Are required failure modes identical where they should be identical?
  **Confirmed** — 127F independently probed 12 fail-closed scenarios,
  all consistent with 126B/127B's shared Failure Contract discipline.
- Are deferred capabilities clearly marked as deferred? **Confirmed**
  — 127B §14/127D §14 both name the same deferred-capability list,
  consistent with this phase's own Section "Deferred Capabilities"
  below.

### Determinism

Review deterministic behavior across artifact generation, timeline
construction, event/transition/relationship classification, and
serialization.

Questions:

- Are ordering rules explicit? **Confirmed**: stable sort by
  chronological commit date (null-boundary records sorting after,
  tie-broken by identifier — 127D §5.3/127C Finding 2's resolution),
  independently re-verified in 127F against real data.
- Are timestamps non-load-bearing where present? **Confirmed**:
  `envelope.generated_at_utc`/`snapshot_identity.snapshot_created_
  at_utc` are the only two approved non-substantive fields, matching
  every other Repository Intelligence artifact family since 120B §6.
- Are repeated equivalent inputs expected to produce equivalent
  logical outputs? **Confirmed**: byte-equal across independent runs,
  re-verified twice (127E, 127F) against the real repository's full
  task-contract corpus.
- Are random, probabilistic, heuristic, or AI-inferred behaviors
  absent? **Confirmed**: `_classify_task()`'s every branch is an
  explicit, deterministic regex/string match with a fixed `unknown`
  fallback — no scoring, no confidence weighting, no inference.

### Interfaces

Review public request/result models, CLI surfaces, and consumption
boundaries.

Questions, with concrete observations:

- Are request models consistently bounded? **Confirmed**: `pcae
  repository-intelligence historical-memory generate` accepts exactly
  `--snapshot`/`--output`/`--pretty`/`--json`, matching `dependency-
  graph generate`'s exact option surface.
- **Observation (interface/documentation consistency)**: 127D §5.1
  named an existing Dependency Knowledge Graph artifact as an
  *optional* input for structural cross-reference, but the CLI exposes
  no `--dependency-graph` (or similarly named) option, and 127E's own
  implementation report confirms Track 126 is "not exercised in this
  prototype." This is not a defect — the option was never scoped as
  required for v1, and omitting an unused flag is honest, not
  incomplete — but it is worth a future 128D plan explicitly deciding
  whether to add the option (functionality that already exists in the
  builder's own data model, `historical_relationship`'s `artifact`
  reference type, but has no CLI entry point) or to explicitly close
  the gap in documentation instead.
- Are unknown, unavailable, incomplete, and conflicting states handled
  consistently? **Confirmed**: `event_status`/`verification_state`
  vocabularies are the shared, already-frozen Track 119 vocabularies,
  unchanged.
- Are unsupported requests rejected or disclosed consistently?
  **Confirmed**: 127F's 12 fail-closed probes found no inconsistency.

### Artifact Consistency

Review artifact and package structure across Repository Knowledge
Snapshot, Dependency Knowledge Graph Snapshot, and Historical Memory
Snapshot.

Questions, with concrete observations:

- Are metadata fields aligned? **Confirmed**: `envelope`/
  `snapshot_identity` shapes are structurally identical across all
  three artifact families (shared `common_artifact_envelope.schema.json`).
- **Observation (terminology/documentation consistency)**: persistence
  subdirectory naming is *not* consistent across the three sibling
  artifact families — Repository Knowledge Snapshot and Historical
  Memory Snapshot both write timestamped files under a `snapshots/`
  subdirectory, but Dependency Knowledge Graph Snapshot writes under
  `graphs/` (confirmed by direct inspection of all three
  `persistence.py` modules' `DEFAULT_OUTPUT_SUBDIR`/directory-name
  constants). This is cosmetic, not functional — no cross-family
  artifact confusion results, since each lives under its own
  `DEFAULT_OUTPUT_SUBDIR` — but it is a genuine, concrete terminology
  inconsistency worth a future 128D plan deciding whether to
  standardize on one convention (e.g. renaming DKG's `graphs/` to
  `snapshots/` in a future, separately governed DKG-scoped change,
  since Track 128 itself must not modify Track 126 — Historical
  Memory's own hardening chapter cannot unilaterally rename another
  track's directory).
- Are schema/version references consistent? **Confirmed**: each
  family's own frozen `executable_schema_version` const
  (`119O.1.0-json-schema` for RKS, `119S.1.0-json-schema` for DKG,
  `119Q.1.0-json-schema` for Historical Memory) is correctly and
  distinctly cited in its own artifact.
- Are generated artifacts and assembled reports distinguishable?
  **Confirmed**: Historical Memory produces only a generated artifact
  family (no assembled report/package role, unlike Advisory Context or
  Change Impact).

### Validation

Review validation boundaries and fail-closed behavior.

Questions:

- Are invalid requests rejected before work begins? **Confirmed**:
  `_load_and_validate_snapshot()` runs before any extraction.
- Are missing attribution, limitations, and boundary disclosures
  handled consistently? **Confirmed**, independently re-verified in
  127F.
- **Observation (testing consistency, already resolved)**: 127F found
  `historical_validation.py`'s deterministic-ordering check
  independently covered only 4 of 6 sortable collections
  (`release_lineage`/`repair_hardening_history` were missing) — this
  gap was found and closed within Track 127 itself (127F), so it is
  not carried forward as open debt here; it is noted only as a
  worked example of exactly the kind of validation-completeness gap
  this review category should watch for in any future Track 127
  extension.
- Are unsupported schema versions rejected without fallback guessing?
  **Confirmed**: delegated to `load_snapshot()`'s existing
  `SnapshotCompatibilityError` path, reused unchanged.

### Persistence

Review which outputs are persisted, which are in-memory, and which are
CLI delivery products.

Questions:

- Is persistence explicitly owned by the correct layer?
  **Confirmed**: `persistence.py` owns writing; `historical_builder.py`
  never writes.
- Are generated artifacts separated from other artifact families?
  **Confirmed**, modulo the `graphs/`-vs-`snapshots/` naming
  observation above (Artifact Consistency category).
- Are latest/timestamped artifact conventions consistent where they
  exist? **Confirmed**: `latest.json` + one timestamped file per run,
  identical convention across RKS/DKG/Historical Memory.

### Serialization

Review JSON serialization, sorting, pretty-printing, metadata, and
machine-readable output conventions. Serialization consistency may
improve; compatibility must remain unchanged.

Questions:

- Are serialized outputs deterministic? **Confirmed**: `serialize_
  deterministic_json` reuse, unchanged from Track 124's own hardening.
- Are keys sorted consistently where JSON is emitted? **Confirmed**.
- Are pretty and compact modes consistent? **Confirmed**,
  independently re-verified by 127E's own byte-comparison test.
- Are output files written only on explicit user/generation request?
  **Confirmed**: no ambient or implicit persistence anywhere in the
  package.

### CLI Consistency

Review CLI naming, option names, error behavior, JSON/pretty/output
flags, and user-facing summaries.

Questions:

- Are Repository Intelligence commands grouped coherently? **Confirmed**:
  `pcae repository-intelligence historical-memory generate` sits
  alongside `snapshot generate`/`dependency-graph generate`/
  `change-impact`/`query` under the same subcommand group.
- Are `--snapshot`, `--json`, `--pretty`, and `--output` semantics
  consistent? **Confirmed** (Interfaces category above).
- Do errors fail closed with clear messages? **Confirmed**: every
  `HistoricalGenerationError` message is specific and actionable,
  independently re-read during 127F.
- Do CLIs avoid hidden generation, scanning, execution, or network
  access? **Confirmed**: bounded git plumbing only, no network calls
  anywhere in the package.

### Documentation

Review whether architecture, contracts, plans, implementations,
verification documents, changelog entries, and project status entries
remain aligned.

Questions:

- Do documents use the same names for the same concepts? **Largely
  yes** across 127A-127F; this review found no cross-document
  terminology drift beyond the two intra-implementation string-literal
  defects 127F already found and fixed (which were data-output
  strings, not documentation).
- Are known limitations and deferred capabilities carried forward?
  **Confirmed** — restated identically in this document's own
  "Deferred Capabilities" and "Known Inherited Issues" sections below.
- Are inherited lifecycle/tooling issues classified consistently?
  **Confirmed** (Technical Debt Classification below).
- Are next-phase recommendations coherent? **Confirmed** — each
  127A-127F document's "Recommended next phase" formed an unbroken
  chain, and this document's own chain continues it.

### Testing

Review test coverage for deterministic behavior, Query Layer
exclusivity, attribution preservation, limitation propagation, boundary
propagation, serialization, failure behavior, read-only behavior, and
regressions across sibling artifact families.

Questions:

- Are high-risk boundaries covered by focused tests? **Confirmed**:
  50 tests in `tests/test_phase_127e_historical_memory_prototype.py`
  cover determinism, identifier stability, timeline/transition
  correctness, provenance/limitation/boundary propagation, validation,
  fail-closed behavior, serialization determinism, persistence
  read-only guarantees, compatibility validation, schema conformance,
  and no-reasoning/no-execution confirmation.
- Are regression suites tied to cross-track dependencies?
  **Confirmed**: 127E/127F both ran Track 120-124/126 regressions
  alongside the new suite.
- Are failure tests symmetrical across sibling artifact families where
  contracts are symmetrical? **Largely yes** — Historical Memory's
  fail-closed test categories mirror DKG's own (missing source,
  corrupted source, incompatible version, duplicate identifiers,
  missing evidence/limitations/boundary), extended with
  Historical-Memory-specific categories (missing task history,
  chronology violation) that have no DKG analogue since DKG has no
  temporal dimension.
- Are tests verifying absence of authority fields and execution
  behavior? **Confirmed**: `test_no_reasoning_module_exists`,
  `test_no_timeline_engine_module_exists`, and the AST-based
  no-subprocess-import tests directly mirror DKG's own
  `test_no_graph_traversal_module_exists`/
  `test_no_query_module_exists` pattern.
- **Observation (testing consistency)**: the fast, synthetic-git-repo
  test fixtures (`_basic_repo`, `_make_synthetic_repo`) are unique to
  the Historical Memory test file — no equivalent lightweight fixture
  pattern exists in the DKG or RKS test files, since neither consumes
  git history directly. This is an expected, not a debt-worthy,
  asymmetry — it exists because Historical Memory is the only
  artifact family with a temporal/git-history dimension, not because
  of inconsistent test design.

### Governance

Review compatibility with PCAE governance and runtime boundaries.

Questions:

- Does every component preserve observe-only runtime posture?
  **Confirmed** via `pcae runtime inspect`, re-verified in this
  session (Governance Compatibility section below).
- Are lifecycle reports complete and metadata consistent? **Confirmed**
  — every 127A-127F canonical phase report reached
  `report_completeness: complete`.
- Are deterministic, auditable, explainable, reproducible outcomes
  preserved? **Confirmed** throughout this review.
- Does any command imply approval, recommendation, execution, or
  runtime authority? **Confirmed absent** — `historical-memory
  generate` only ever generates a descriptive, read-only artifact.

## Cross-Track Consistency Strategy

Historical Memory should remain consistent across terminology,
artifact structure, metadata, provenance, limitation propagation,
boundary disclosures, fail-closed behavior, and version compatibility
with:

- **Track 119 executable schemas** — the already-frozen
  `historical_memory_snapshot.schema.json` (`119Q.1.0-json-schema`);
  Track 128 authorizes no schema change.
- **Track 120 Repository Knowledge Snapshot** — Historical Memory's
  only Repository Intelligence input; not modified by Track 128.
- **Track 121 Query Layer** — Historical Memory's exclusive access
  path into Repository Intelligence content; not modified by Track
  128. Task-contract/git-history discovery remains a separate, equally
  bounded, non-Query-Layer path, per this review's Architecture
  category finding above.
- **Track 122 Advisory Context** — not modified; Historical Memory's
  eventual consumption by Advisory (127A §6.4) remains unscoped and
  unauthorized by Track 128.
- **Track 123 Change Impact** — not modified; the same unscoped/
  unauthorized status applies (127A §6.5).
- **Track 126 Dependency Knowledge Graph** — not modified; Historical
  Memory's optional structural cross-reference to Dependency Knowledge
  Graph content (127D §5.1) remains unexercised in v1, per the
  Interfaces category observation above.

Stable terminology should include Historical Memory Snapshot,
Historical Event, Historical Timeline, Historical Transition,
Historical Relationship, Historical Context, Historical Evidence,
phase lineage, release lineage, source attribution, verification
state, snapshot limitations, boundary disclosures, unknown, and
unverified.

Generated Repository Knowledge Snapshot, Dependency Knowledge Graph
Snapshot, and Historical Memory Snapshot artifacts must remain
distinguishable — confirmed unchanged; the one cosmetic subdirectory-
naming inconsistency noted above (Artifact Consistency category) does
not blur this distinction, since each family already writes to its own
distinct `DEFAULT_OUTPUT_SUBDIR`.

Metadata should consistently identify the input, source artifact,
schema/version, selected records, limitations, boundary disclosures,
and non-load-bearing values — confirmed consistent across all three
generated-artifact families.

Attribution/provenance must remain attached to every content-bearing
record — confirmed unchanged, and strengthened by 127F's own
derivation-accuracy fix.

Historical Memory limitations must propagate unchanged from Repository
Knowledge Snapshot; inherited limitations cannot be dropped, weakened,
replaced, or masked by additive Historical-Memory-specific
limitations — restated from 125B §7/126B §8/127B §7, binding
identically here.

Boundary disclosures and disclaimers must remain attached throughout —
confirmed unchanged.

Fail-closed behavior should remain consistent: invalid request,
unsupported schema/version, corrupted Repository Intelligence, missing
task history, missing attribution, missing limitation, missing
boundary disclosure, duplicate identifiers, and chronology violation
must not produce authoritative or silently incomplete output —
confirmed, 12/12 probes independently verified in 127F.

Version compatibility remains owned by the layer that consumes the
artifact or result. Track 128 must not silently add compatibility
fallbacks.

## Determinism Architecture

Equivalent repository state shall continue producing equivalent
Historical Memory. This restates 127B §11's Determinism Contract as
binding for Track 128's own review-and-hardening work: any future
128D-128E hardening change must preserve byte-equal output (modulo the
two approved timestamp fields) for equivalent git history, task
contract content, and source Repository Knowledge Snapshot input.
Hardening may improve *how* determinism is achieved (e.g. clarifying
an identifier scheme's own documentation) but must never change *what*
deterministic output equivalent input produces.

## Evidence Architecture

Evidence attribution shall remain unchanged. Historical events shall
never gain inferred evidence. This restates 127B §7's Evidence
Contract as binding for Track 128: hardening may correct an
attribution's own *description* (as 127F's Defect 1 fix did — the
underlying attribution was always evidence-based; only its
self-description was momentarily stale) but must never attach
evidence to a claim that lacked direct, deterministic source support
before hardening.

## Temporal Consistency Architecture

Timeline ordering shall remain deterministic. No inferred chronology.
This restates 127B §6's Temporal Contract as binding for Track 128:
hardening may improve *how clearly* the ordering rule is documented or
tested (as this review's Testing category names as an opportunity) but
must never introduce a heuristic, estimated, or inferred time reference
where the underlying source data does not already deterministically
establish one.

## Read-Only Architecture

Historical Memory shall never modify:

- the repository (source files, working tree content);
- git history (no commit, no ref move, no tag creation);
- Repository Knowledge Snapshot (read-only via the Query Layer);
- task contracts (`tasks/done/*.md`, read-only via `git_source.py`);
- Dependency Knowledge Graph (not consumed in v1; would remain
  read-only if and when a future phase wires the optional
  cross-reference).

This restates 127B §8's Read-Only Contract, independently re-verified
via direct checksum/HEAD comparison in 127F, as binding unchanged for
all Track 128 hardening work.

## Serialization Architecture

Serialization consistency may improve. Compatibility must remain
unchanged. A future 128D plan may, for example, decide whether to
standardize the `graphs/`-vs-`snapshots/` subdirectory-naming
inconsistency this review found (Artifact Consistency category) — but
any such change is scoped to documentation/consistency improvement
within Historical Memory's own persistence module, never a change to
Dependency Knowledge Graph's own directory (out of Track 128's scope
by definition; a change there would require its own separately
governed Track 126 phase), and never a change to the frozen
119Q/119O/119S schema versions or the `serialize_deterministic_json`
helper's own behavior.

## Failure Architecture

Hardening shall preserve fail-closed behavior. No fail-open behavior.
This restates 127B §9's Failure Contract as binding for Track 128
identically: every one of the 12 fail-closed categories 127F
independently verified must remain fail-closed after any future
128D-128E hardening change; hardening must never relax a failure
condition into a warning, a default value, or a silently degraded
artifact.

## Governance Contract

Track 128 hardening must preserve:

- observe-only runtime posture;
- execution-unavailable boundary;
- reproducibility;
- auditability;
- explainability;
- human-controlled governance.

Hardening must not make Historical Memory appear more complete,
authoritative, current, or actionable than its sources and limitations
support — restated from 124A's identical principle, binding
identically here. In particular, hardening must never reclassify a
`event_type: unknown` record (497 of 850+ real events, per 127E's own
confirmed corpus distribution) into a more specific type without new,
genuinely deterministic source support — doing so would be
functionality expansion (better classification coverage), explicitly
out of Track 128's scope, not hardening.

## Compatibility Contract

Track 128 shall remain fully compatible with all completed Repository
Intelligence tracks: 119 (executable schemas), 120 (Repository
Knowledge Snapshot), 121 (Query Layer), 122 (Advisory Context), 123
(Change Impact), and 126 (Dependency Knowledge Graph). No file under
any of these tracks may be modified by Track 128 without its own
separate, explicitly scoped governed phase outside this chapter's
authorization.

## Technical Debt Classification

Track 128 classifies debt before repair. No repairs occur during this
phase.

- **Documentation debt**: the `graphs/`-vs-`snapshots/` persistence
  subdirectory-naming inconsistency across DKG and Historical
  Memory/RKS (Artifact Consistency category); the unscoped-but-
  unexercised optional Dependency Knowledge Graph cross-reference
  input having no CLI entry point despite existing in the builder's
  own data model (Interfaces category).
- **Implementation debt**: none identified beyond what 127F already
  found and closed within Track 127 itself (the two defects fixed in
  127F are resolved, not open debt).
- **Testing debt**: none identified as genuinely missing; the
  synthetic-git-repo fixture asymmetry (Testing category) is an
  expected consequence of Historical Memory being the only artifact
  family with a temporal/git-history dimension, not a coverage gap.
- **Governance debt**: none identified — every 127A-127F canonical
  report reached full trust completeness.
- **Lifecycle/tooling debt**: carried forward unchanged (Section
  "Known Inherited Issues" below).

Known inherited lifecycle/tooling issues carried forward:

- 119Q report-generation-ordering defect;
- 119AB phase-id comparison bug;
- recurring `pending_final_telegram_delivery` reporting detail.

These issues are not repaired in 128A. Not inherited defects: 126G
(Telegram Canonical Report Dispatch Repair) and 126G.1 (Telegram
Commit Trust Metadata Repair) are closed, verified repairs and remain
excluded from this list, consistent with every 127A-127F document's
own treatment of them.

## Hardening Principles

Track 128 hardening must preserve:

- determinism;
- read-only behavior;
- auditability;
- reproducibility;
- explainability;
- fail-closed behavior;
- Query Layer exclusivity (for Repository Intelligence content
  specifically; task-contract/git-history discovery remains its own,
  separately bounded path, per this document's Architecture category);
- attribution preservation;
- limitation propagation;
- boundary disclosure propagation;
- observe-only runtime posture;
- execution-unavailable boundary;
- human-controlled governance.

Hardening must not make Historical Memory appear more complete,
authoritative, current, or actionable than its sources and limitations
support.

## Deferred Capabilities

Explicitly deferred, not authorized by this phase:

- historical reasoning;
- causal inference;
- predictive history;
- recommendations;
- Decision Evaluation;
- execution planning;
- execution capability;
- graph traversal;
- AI interpretation.

Also explicitly deferred, consistent with 124A's own equivalent list:

- new Historical Memory artifact families;
- Dependency Knowledge Graph expansion;
- Advisory reasoning;
- runtime plugins;
- AI provider integration;
- external API integration;
- repository scanning beyond what 127E already performs;
- new schemas during 128A.

## Track 128 Roadmap

- **128A — Review & Hardening Architecture**: define scope,
  categories, principles, debt classification, and roadmap (this
  document).
- **128B — Hardening Contract Freeze**: freeze the normative hardening
  contract.
- **128C — Hardening Contract Verification**: independently verify the
  frozen contract.
- **128D — Hardening Plan**: define the implementation plan for
  bounded hardening work (e.g. resolving the documentation-debt items
  Section "Technical Debt Classification" names, if judged worth
  resolving).
- **128E — Hardening Implementation**: implement approved hardening
  only within the frozen contract.
- **128F — Hardening Verification**: independently verify 128E.

## Strict Non-Goals

128A does not implement: historical reasoning; causal reasoning;
recommendations; Decision Evaluation; execution planning; execution
capability; runtime plugins; schema changes; source code; test code.

## Governance Compatibility

This architecture is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- review and hardening are scoped through governed phases;
- implementation is deferred to a future explicit implementation
  phase;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## Conclusion

Phase 128A defines Track 128 as a review-and-hardening track over the
existing Historical Memory implementation, mirroring Track 124's role
for Repository Intelligence directly. It establishes review
objectives, hardening categories, cross-track consistency strategy,
technical debt classification (two genuine, concrete, non-blocking
documentation-debt items found: persistence subdirectory naming
inconsistency, and an unscoped-but-unexercised optional CLI input),
hardening principles, deferred work, and the 128A-128F roadmap. No
implementation occurred. No schema changed. No runtime behavior
changed.

Recommended next phase: 128B — Historical Memory Review & Hardening
Contract Freeze.
