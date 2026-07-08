# Phase 120D - Repository Knowledge Snapshot Prototype Plan

## 1. Prototype Objective

This document is the definitive implementation plan for the first
Repository Intelligence prototype: a deterministic, read-only
Repository Knowledge Snapshot generator. It defines exactly how Phase
120E will implement that generator while preserving every
architectural boundary (120A), contractual rule (120B), and
independently verified consistency finding (120C) established so far
in Track 120.

**This phase does not implement the generator.** 120D produces a plan
only. No code, model, dataclass, validator, CLI, fixture, or test
exists as a result of this document.

## 2. Scope

The prototype planned here shall generate only:

- **Repository Knowledge Snapshot**
  (`schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`)

No other Repository Intelligence artifact family (Contract Conformance
Record, Historical Memory Snapshot, Dependency Knowledge Graph
Snapshot, Change Impact Report, Advisory Intelligence Context Package,
Query Result, Repository Intelligence Package) is included in this
plan or in Phase 120E, per the restriction frozen in 120B Section 3
and re-confirmed by 120C Section 4 (Scope Verification).

## 3. Implementation Boundaries (Reaffirmed)

Every boundary below is inherited unchanged from 120A/120B, verified
sound by 120C, and binding on 120E:

- **Read-only** — 120E may never modify repository files outside its
  own governed output write (120B §7).
- **Deterministic** — identical repository inputs (same commit) must
  produce identical snapshot structure, excluding approved
  non-substantive metadata (120B §6).
- **Observe-only** — 120E operates entirely within the existing
  `Observed` / `observe` / execution-unavailable runtime posture
  (120B §2). Confirmed unchanged at time of this plan via `pcae
  runtime inspect`: runtime state `Observed`, maximum plugin
  capability `observe`, execution capability `unavailable`, zero
  registered runtime plugins.
- **No execution** — 120E may never execute repository code or shell
  commands beyond PCAE's existing governed commands (120B §7).
- **No repository mutation** — 120E may never modify `src/`, `tests/`,
  or any tracked file outside its own governed persistence write
  (120B §7).
- **No runtime mutation** — 120E may never modify runtime state or
  install a runtime plugin (120B §7, §16).
- **No AI inference** — 120E may never rely on AI inference, sampling,
  or non-reproducible heuristic scoring to produce snapshot content
  (120B §6).
- **No network access** — 120E may never read from external services
  or network sources (120B §4).
- **No Advisory integration** — 120E may never invoke, configure, or
  mutate Advisory Runtime or any Advisory subsystem (120B §7).
- **No Decision Evaluation integration** — 120E may never replace,
  bypass, or substitute for Decision Evaluation (120B §7).

## 4. Planned Implementation Inputs

Conceptual repository sources Phase 120E will consume, drawn from the
allowed input list frozen in 120B §4:

- repository documentation (`docs/*.md`, `README.md`, `AGENTS.md`,
  `schemas/repository_intelligence/README.md`)
- governed lifecycle artifacts (`.pcae/phase-reports/**`,
  `.pcae/phase-completion-report.md`,
  `.pcae/phase-completion-metadata.json`, task contracts in
  `tasks/active/` and `tasks/done/`)
- tracked repository metadata (git commit history, tags, commit
  metadata; `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/TODO.md`,
  `tasks/DONE.md`)
- verified Repository Intelligence schemas
  (`schemas/repository_intelligence/**/*.schema.json`, frozen by 119)
- tracked source and test file structure (paths, module/package
  layout under `src/pcae/` and `tests/`) as architectural entities,
  read without executing any of the code they contain

No parsing algorithm is defined here. This section names the input
surface only; how each source is read is left to 120E's own
implementation, subject to the boundaries in Section 3.

## 5. Planned Extraction Pipeline (Logical, No Implementation)

The eleven-stage logical pipeline 120E will follow:

1. **Repository source discovery** — enumerate which allowed input
   sources (Section 4) are present in the repository at the commit
   being snapshotted.
2. **Source eligibility evaluation** — for each discovered source,
   confirm it is on the allowed list (120B §4) and reject anything
   that is not, rather than silently including it.
3. **Attribution assignment** — associate each eligible source with a
   deterministic Source Attribution Record locator (Section 7) before
   any fact is extracted from it.
4. **Repository knowledge extraction** — apply only deterministic,
   non-inferential extraction methods to attributed sources to
   produce candidate architectural entities, capabilities, subsystems,
   relationships, and claims.
5. **Knowledge normalization** — normalize extracted candidates into a
   consistent internal shape (e.g. consistent entity identifiers,
   consistent path formatting) without altering their substantive
   meaning or attribution.
6. **Repository Knowledge Snapshot assembly** — assemble normalized
   candidates into the shape of a Repository Knowledge Snapshot:
   `snapshot_identity`, `snapshot_subject`, `snapshot_scope`,
   `architectural_entities`, `capabilities`, `subsystems`,
   `knowledge_relationships`, `knowledge_claims`, `knowledge_sources`.
7. **Schema alignment** — align the assembled structure against the
   frozen `repository_knowledge_snapshot.schema.json` shape, including
   every required field named in Section 6 below.
8. **Limitation capture** — record what could not be determined
   (`unknowns`, `snapshot_limitations`, per-record `limitations`
   arrays) rather than omitting or guessing (Section 8).
9. **Boundary attachment** — attach `boundary_disclosures`,
   `disclaimers`, and the `repository_knowledge_snapshot_disclaimer`
   const so the artifact cannot be misread as authoritative
   (Section 9).
10. **Persistence** — write the completed, boundary-attached artifact
    to its planned output location (Section 10) under governed commit
    discipline.
11. **Human review** — a person, not Advisory, not Decision
    Evaluation, not an autonomous agent, decides whether the persisted
    snapshot is fit to be treated as current Repository Intelligence
    input for some other purpose.

This numbering reflects the eleven-step version of the ten conceptual
stages 120B §12 froze (120B's stage 1 "Source inventory" is split here
into stages 1-2 "source discovery" and "source eligibility
evaluation," and 120B's stage 3 "Deterministic extraction" is split
into stages 4-5 "extraction" and "normalization," for planning
precision). No stage's responsibility, ordering, or boundary changes
from what 120B froze; this is an implementation-planning elaboration,
not a contract amendment. No implementation detail (algorithm, data
structure, library) is specified for any stage.

## 6. Component Plan

Conceptual implementation components expected in 120E. No code is
specified for any of them.

### 6.1 Source Inventory Component

- **Responsibility**: enumerate allowed input sources present at the
  snapshotted commit (pipeline stages 1-2).
- **Inputs**: the allowed input list (Section 4), the repository
  working tree at a fixed commit.
- **Outputs**: a list of eligible source locations, each associated
  with a locator type from the frozen vocabulary (`file_path`,
  `commit_sha`, `phase_id`, etc.).
- **Boundaries**: read-only; must reject any source not on the allowed
  list rather than silently extending scope.

### 6.2 Attribution Component

- **Responsibility**: assign a deterministic Source Attribution Record
  to every eligible source before extraction proceeds (pipeline
  stage 3).
- **Inputs**: the eligible source list from 6.1.
- **Outputs**: source-attribution-tagged sources, using the frozen
  locator vocabulary from `source_attribution_record.schema.json`.
- **Boundaries**: deterministic; a source with no attributable locator
  must not proceed to extraction.

### 6.3 Extraction Component

- **Responsibility**: apply deterministic, non-inferential extraction
  methods to attributed sources to produce candidate knowledge
  (pipeline stage 4).
- **Inputs**: attribution-tagged sources from 6.2.
- **Outputs**: candidate architectural entities, capabilities,
  subsystems, relationships, and claims, each still carrying its
  source attribution.
- **Boundaries**: no AI inference; no execution of repository code;
  no network access; must fail closed rather than guess when a source
  cannot be deterministically parsed.

### 6.4 Normalization Component

- **Responsibility**: normalize candidate knowledge into a consistent
  internal shape without altering substantive meaning (pipeline
  stage 5).
- **Inputs**: candidate knowledge from 6.3.
- **Outputs**: normalized candidate knowledge, still fully attributed.
- **Boundaries**: must not discard attribution or uncertainty state
  during normalization; must not resolve conflicts (conflicts are
  preserved per Section 8, not normalized away).

### 6.5 Assembly Component

- **Responsibility**: assemble normalized knowledge into the
  Repository Knowledge Snapshot shape (pipeline stage 6).
- **Inputs**: normalized knowledge from 6.4.
- **Outputs**: an assembled, not-yet-schema-checked snapshot structure
  covering `snapshot_identity`, `snapshot_subject`, `snapshot_scope`,
  `architectural_entities`, `capabilities`, `subsystems`,
  `knowledge_relationships`, `knowledge_claims`, `knowledge_sources`.
- **Boundaries**: exactly one snapshot per generation run (120B §5);
  no other output artifact type.

### 6.6 Schema Alignment Component

- **Responsibility**: align the assembled structure against the frozen
  schema shape, including every field the schema requires (pipeline
  stage 7).
- **Inputs**: the assembled snapshot from 6.5, the frozen
  `repository_knowledge_snapshot.schema.json`.
- **Outputs**: a schema-shaped snapshot (not yet boundary-attached or
  persisted).
- **Boundaries**: must fail closed (Section 11) if the assembled
  structure cannot be aligned to the schema without fabricating a
  required field.

### 6.7 Limitation/Unknown Capture Component

- **Responsibility**: populate `unknowns`, `snapshot_limitations`, and
  every per-record `limitations` array honestly (pipeline stage 8).
- **Inputs**: gaps and bounds surfaced by every prior component.
- **Outputs**: a snapshot with complete, honest limitation and unknown
  content.
- **Boundaries**: must never leave an applicable limitation or unknown
  unpopulated to imply false completeness (120B §11, §10).

### 6.8 Boundary Attachment Component

- **Responsibility**: attach `boundary_disclosures`, `disclaimers`, and
  the `repository_knowledge_snapshot_disclaimer` const verbatim
  (pipeline stage 9).
- **Inputs**: the schema-shaped, limitation-populated snapshot.
- **Outputs**: a complete, boundary-attached snapshot ready for
  persistence.
- **Boundaries**: all nine boundary-disclosure fields and all five
  shared disclaimer consts plus the family-specific const must be
  present, verbatim, unmodified (120B §11; confirmed exact against the
  schema files in 120C §3.1).

### 6.9 Persistence Component

- **Responsibility**: write the completed snapshot to its planned
  output location under governed commit discipline (pipeline
  stage 10).
- **Inputs**: the complete, boundary-attached snapshot from 6.8.
- **Outputs**: a persisted snapshot file at the location chosen in
  Section 10.
- **Boundaries**: must occur only through the existing PCAE governed
  lifecycle (task contract, staged-file-aware commit, `pcae task
  finish`, `pcae phase complete`); never an ungoverned write followed
  by a raw `git commit`/`git push` (120B §13).

### 6.10 Verification/Reporting Component

- **Responsibility**: verify the persisted snapshot against the
  120F verification agenda (Section 11) before it is considered
  anything more than a draft (pipeline stage 11's precondition).
- **Inputs**: the persisted snapshot, the frozen schema.
- **Outputs**: a verification result (pass/fail per check).
- **Boundaries**: no validator library is implemented by this
  component in 120E; verification tooling implementation itself is
  120F's responsibility (120C §16, Out of scope for 120D/120E).

## 7. Source Attribution Plan

Attribution is attached at the earliest possible pipeline stage
(stage 3, before extraction) and carried through every subsequent
stage without being dropped:

- Every source discovered in stage 1-2 receives a locator using the
  frozen vocabulary (`file_path`, `file_path_line`, `file_path_symbol`,
  `file_path_section`, `phase_id`, `phase_report_id`, `task_id`,
  `commit_sha`, `tag`, `release_id`, `contract_document_section`,
  `canonical_report_id`; `evidence_id`/`decision_id` apply only where
  a fact is itself sourced from an Evidence or Decision Evaluation
  record referenced by governed lifecycle metadata).
- Extraction (6.3) and normalization (6.4) must both preserve the
  attribution attached in stage 3 without weakening or generalizing
  it (for example, normalization may not collapse a `file_path_line`
  locator to a coarser `file_path` locator).
- Assembly (6.5) places each extracted claim's attribution into the
  schema's `source_attribution` field on the corresponding `$def`
  (`architectural_entity`, `capability_summary`, `subsystem_summary`,
  `knowledge_relationship`, `knowledge_claim`, `command_surface`,
  `contract_reference`, `documentation_reference`, `ownership_marker`
  — every one of which requires `source_attribution` per the schema's
  own `$defs`).
- A fact that cannot be traced back to an eligible, attributed source
  by the end of stage 6 (Assembly) must not appear in the snapshot at
  all — this is enforced by the Failure Plan (Section 11), not left as
  a best-effort cleanup step.

## 8. Unknown Handling Plan

- **Missing information**: represented as `unknown` in the relevant
  record's `verification_state`/`uncertainty_state`, and reflected in
  the snapshot-level `unknowns` array (the schema's actual required
  field name; see 120C Section 6's clarification that this field is
  `unknowns`, not `unknowns_gaps`, for this specific schema).
- **Conflicting information**: represented via `conflicting`
  verification/uncertainty state; where two sources disagree, both
  claims are retained with their respective attributions rather than
  one silently overwriting the other, consistent with 120B §10's
  prohibition on collapsing `conflicting` state.
- **Incomplete information**: represented via `partially_verified`
  state and/or an explicit `unknowns` entry describing what portion is
  missing.
- **Unverifiable information**: represented as `unverified` state,
  never silently promoted to `verified` without a new, deterministic
  attribution.

No inference is permitted at any point in this handling: 120E must
represent what it could determine and what it could not, and must
never fill an unknown with a plausible guess.

## 9. Limitation Plan

- **Limitation records** (`limitation_record.schema.json`): attached
  per-record (via each `$def`'s own `limitations` array — confirmed
  present as a required field on `architectural_entity`,
  `capability_summary`, `subsystem_summary`, `knowledge_relationship`,
  `knowledge_claim`, `command_surface`, and `documentation_reference`
  in the frozen schema) wherever the extraction method or source
  coverage has bounds, and at the snapshot level via
  `snapshot_limitations`.
- **Disclaimer records** (`disclaimer.schema.json`): the five shared
  disclaimer consts plus the `repository_knowledge_snapshot_disclaimer`
  const, emitted verbatim as frozen by the 119 schema (120B §11,
  confirmed exact in 120C §3.1).
- **Boundary disclosures** (`boundary_disclosure.schema.json`): all
  nine const-`true` fields, attached in the Boundary Attachment
  Component (6.8), present and unmodified.

## 10. Persistence Plan

120B §13 delegated the final output-location decision to this phase.
120D selects, as the planned (not yet implemented) output location:

**`.pcae/repository-intelligence/`**

Rationale for this choice among 120A's three candidates
(`.pcae/repository-intelligence/`, `artifacts/repository-intelligence/`,
`reports/repository-intelligence/`):

- `.pcae/` is already the established home for governed, canonical,
  lifecycle-produced artifacts in this repository (phase reports,
  completion metadata, session state), so placing generated Repository
  Intelligence artifacts alongside them keeps all governed-lifecycle
  output under one root, consistent with existing repository
  conventions.
- `artifacts/repository-intelligence/` was rejected because
  `artifacts/` does not yet exist as a top-level directory in this
  repository and would introduce a new top-level convention purely for
  this one prototype, which is a heavier footprint than necessary for
  a single-family, single-artifact-per-run generator.
- `reports/repository-intelligence/` was rejected for the same reason
  as above, and additionally risks conflating generated Repository
  Intelligence artifacts with PCAE's own `.pcae/phase-reports/`
  concept, which already uses "report" to mean something more
  specific (a phase-completion report).

This is a conceptual persistence model only — no directory is created,
no file is written, and no storage class or implementation mechanism
is specified as a result of this plan. 120E is responsible for
implementing the actual write, subject to 120B §13's requirement that
persistence occur only through the existing PCAE governed lifecycle.

## 11. Verification Plan (for Phase 120F)

Phase 120F will verify, without this plan implementing any validator:

- **Schema conformance**: the persisted snapshot parses as valid JSON
  and matches every `required` field and `$def` shape in
  `repository_knowledge_snapshot.schema.json` and its referenced
  shared components.
- **Attribution completeness**: every content-bearing record (every
  `architectural_entity`, `capability_summary`, `subsystem_summary`,
  `knowledge_relationship`, `knowledge_claim`, `command_surface`,
  `contract_reference`, `documentation_reference`, `ownership_marker`
  present in the snapshot) carries a `source_attribution` field with a
  valid locator.
- **Deterministic behavior**: re-running 120E's generator against the
  same commit reproduces byte-for-byte identical output except
  approved non-substantive metadata fields (120B §6's determinism
  test).
- **Boundary preservation**: all nine `boundary_disclosures` fields and
  all six disclaimer consts (five shared plus the family-specific
  const) are present and match the frozen schema constants exactly.
- **Limitation handling**: `unknowns` and `snapshot_limitations` are
  populated wherever the generator's own coverage has bounds, and no
  per-record `limitations` array is left empty where a genuine
  limitation exists.
- **Governance compliance**: the snapshot was persisted only through
  the governed PCAE lifecycle (task contract, staged-file-aware
  commit, `pcae task finish`, `pcae phase complete`), with
  `origin/main..HEAD` returned to 0 at the end of the generating phase.

No validator, validation library, or verification CLI is implemented
in 120D or 120E. 120F is the phase responsible for implementing
however this checklist is executed.

## 12. Failure Plan (Fail-Closed)

120E must halt, not degrade or approximate, when it encounters:

- **Missing required sources**: a source the schema requires content
  for is not reachable through an allowed input (Section 4) — 120E
  must not fabricate the missing content.
- **Attribution failures**: a candidate fact cannot be given a
  deterministic Source Attribution Record (Section 7) — the fact must
  be dropped or represented as `unknown`, never asserted unattributed.
- **Schema incompatibility**: the assembled structure cannot be
  aligned to `repository_knowledge_snapshot.schema.json` without
  omitting a required field or violating `additionalProperties: false`
  — 120E must halt rather than emit a non-conformant artifact.
- **Invalid snapshot construction**: any internal inconsistency (for
  example, a `knowledge_relationship` referencing an
  `architectural_entity` id that does not exist in the same snapshot)
  is detected during assembly — 120E must halt rather than persist an
  internally inconsistent snapshot.
- **Boundary violations**: any condition that would require violating
  one of Section 3's implementation boundaries to continue (for
  example, needing to execute code to extract a fact) — 120E must halt
  rather than cross the boundary.

Producing nothing is always preferable to producing an artifact that
violates the 120B contract, consistent with 120B §15's fail-closed
requirement.

## 13. Governance Plan

Phase 120E will preserve:

- **Observe-only runtime**: runtime state remains `Observed`, maximum
  plugin capability remains `observe`; 120E introduces no runtime
  plugin and requests no capability increase.
- **Execution unavailable**: 120E's generator runs entirely through
  deterministic, non-executing extraction methods; it never invokes
  repository code, a shell beyond PCAE's existing governed commands,
  or an external process.
- **Deterministic generation**: per Section 5-7 and the determinism
  test in Section 11.
- **Reproducibility**: the same commit, run twice, produces the same
  substantive snapshot content (120B §6, §16).
- **Auditability**: every field in the persisted snapshot traces back
  through its `source_attribution` to a specific, allowed input source
  (Section 4, Section 7), and the generating phase's own governed
  commit history provides an independent audit trail.

120E must also follow the same commit/push discipline as every prior
phase in this track: governed task contracts, staged-file-aware
commits, `pcae task finish`, `pcae phase complete`; no raw `git
commit`/`git push`, no `--no-verify`, no force push;
`origin/main..HEAD` returned to 0 at the end of the phase.

## 14. Deliverables Expected from 120E

Listed as a target list only; none of these is created by 120D:

- a deterministic Repository Knowledge Snapshot generator implementing
  the eleven-stage pipeline (Section 5) via the ten components
  (Section 6)
- one generated, schema-conformant, boundary-attached Repository
  Knowledge Snapshot artifact, persisted at
  `.pcae/repository-intelligence/` (Section 10)
- an implementation document describing what was actually built
  (120E's own phase document, per the established Track B/120
  documentation pattern)
- no validator, CLI, Python package, or test suite is expected from
  120E itself unless 120E's own governed brief explicitly scopes one
  in — this plan does not presuppose that decision

## 15. Acceptance Criteria (for Phase 120E)

Phase 120E is complete only if:

1. Exactly one Repository Knowledge Snapshot artifact is generated per
   run, and no other artifact family is produced.
2. The generated artifact validates against
   `repository_knowledge_snapshot.schema.json` and every shared
   component it references (structurally, via the same scripted
   parse/`$ref`/`additionalProperties` checks used throughout 119 and
   120, since no conformant validator exists yet).
3. Every content-bearing record in the artifact carries a valid
   `source_attribution` locator.
4. Re-running the generator against the same commit produces
   byte-for-byte identical output except approved non-substantive
   metadata fields.
5. All nine `boundary_disclosures` fields and all six disclaimer
   consts are present, verbatim, and unmodified.
6. `unknowns` and `snapshot_limitations` are populated wherever the
   generator's actual coverage has bounds; no false-completeness
   implication is present.
7. No repository file outside the artifact's own governed persistence
   write was modified.
8. No execution, shell mediation beyond existing governed commands, AI
   provider invocation, external API call, or network access occurred.
9. No Advisory or Decision Evaluation subsystem was invoked, mutated,
   or replaced.
10. The artifact was persisted only through the governed PCAE
    lifecycle, with `origin/main..HEAD` returned to 0 at the end of the
    phase.
11. Repository health (`pcae health`, `pcae check`, `pcae doctor
    task-memory`, `pcae push check`) remained healthy/passed/clean
    throughout.

## 16. Risks

- **Risk: extraction ambiguity for architectural entities.** Some
  repository structures (e.g. a file that is both a documentation
  reference and an architectural entity) may not map cleanly onto a
  single `$def`. **Mitigation**: 120E must resolve this via the
  fail-closed principle (Section 12) — if a source's category is
  ambiguous under deterministic rules, it is either represented in
  both applicable `$def`s (each independently attributed) or excluded
  with an `unknowns` entry, never force-fit into one category by
  guesswork.
- **Risk: determinism drift from git/filesystem ordering.** Directory
  listings and git log output are not always guaranteed to return
  results in a stable order across environments. **Mitigation**: 120E
  must explicitly sort every extracted collection (entities,
  capabilities, relationships, claims) by a stable key (e.g.
  `entity_id`, `claim_id`) before assembly, so output order does not
  depend on filesystem or git iteration order.
- **Risk: persistence location conflicts with the architecture zone
  system.** `.pcae/` is not one of PCAE's `DEFAULT_ARCHITECTURE_ZONES`
  (core, commands, cli, tests, docs, tasks, scripts, hooks, package,
  session, policy, config), so a generated snapshot file there would
  fall into the "unclassified" zone, the same situation the 119 schema
  files hit under `schemas/`. **Mitigation**: 120E's task contract
  should omit `--allowed-zone` (leaving `allowed_zones` empty) and use
  `--allowed-file` for the specific generated snapshot path instead,
  exactly as every 119 schema-implementation phase did — this is a
  known, already-solved governance pattern, not a new risk requiring
  new tooling.
- **Risk: schema evolution mismatch.** If a future phase revises
  `repository_knowledge_snapshot.schema.json` after 120D but before
  120E, this plan's field-name references (Section 6, Section 8-9)
  could go stale. **Mitigation**: 120E must re-verify the schema's
  current `required` fields and `$defs` at implementation time rather
  than trusting this plan's field names blindly, exactly as 120C
  Section 6 caught and corrected one such stale reference
  (`unknowns_gaps` vs `unknowns`) in 120B's own prose.
- **Risk: fail-closed behavior producing zero usable output.** If the
  repository state at generation time genuinely lacks attributable
  sources for a required field, a strictly fail-closed generator may
  refuse to produce any artifact at all. **Mitigation**: this is the
  contractually correct behavior (120B §15), not a defect to work
  around; 120F's verification plan should treat "the generator
  correctly refused to produce a non-conformant artifact" as a passing
  outcome for that scenario, not a failure of 120E.

## 17. Deferred Work

Explicitly deferred, not included in 120D, 120E, or any phase this
plan authorizes:

- query layer (tentatively "121" per 120A §20)
- Advisory consumption (tentatively "122" per 120A §20)
- change impact read-only prototype (tentatively "123" per 120A §20)
- graph traversal
- execution planning (tentatively "125+" per 120A §24, and only as its
  own separately scoped, separately approved architecture phase)
- execution capability of any kind

Extending the prototype to any other artifact family, or to any of the
deferred items above, requires a new, separately scoped contract
phase, per 120B §3 and §18.

## 18. Known Inherited Issues

Carried forward, unchanged in classification, from 119AC/120A/120B/120C:

- **119Q report-generation-ordering defect** (`Commits: pending_`,
  recovered commit `d804458fda2663d79577941f7c415a2a50fe1573`,
  documented in 119R). **Classification: non-blocking.**
- **`is_phase_id_backward()` phase-id comparison bug**
  (`src/pcae/core/phase_reports.py`, documented in 119AB).
  **Classification: non-blocking for 120D; should still be tracked
  before a letter-length transition occurs within the 120 series**
  (not relevant to the 120C → 120D or 120D → 120E transitions, both
  single-letter-to-single-letter).
- **Recurring `report_notification_tests:
  pending_final_telegram_delivery` reporting detail**. **Classification:
  non-blocking, well-understood, and consistently handled.**

None of these three issues is repaired by this phase. Repair remains
explicitly out of scope for 120D, consistent with 119AC, 120A, 120B,
and 120C.

## 19. Recommended Next Phase

Recommended next phase:

`120E - Repository Knowledge Snapshot Prototype: Read-Only Generator`

Reason: the implementation plan is now complete, including the
persistence-location decision this phase was responsible for making
(Section 10). 120E may now implement the generator planned here,
subject to every boundary reaffirmed in Section 3, every contractual
rule frozen in 120B, and every finding independently verified in 120C.
