# Phase 120A - Repository Intelligence Read-Only Prototype Architecture

## 1. Purpose

Phase 120A opens Track 120 by defining the architecture for a future
read-only Repository Intelligence prototype: a system that may, in
later phases, produce schema-conforming Repository Intelligence
artifacts from the verified 119 executable schema line, without
execution, mutation, Advisory authority, Decision Evaluation
replacement, runtime behavior change, or repository-state authority.

This document answers: "How should PCAE architecture support a future
read-only Repository Intelligence prototype that generates
schema-conforming artifacts without execution, mutation, Advisory
authority, Decision Evaluation replacement, runtime behavior change, or
repository-state authority?"

120A is architecture only. It does not build the prototype, does not
create generated Repository Intelligence artifacts, and does not
implement any of the stages it describes. It defines architecture,
boundaries, stages, contracts, inputs, outputs, invariants, and the
future phase sequence for the read-only prototype track.

## 2. Background

Phase 118 (118A-118E, 118R) defined the Repository Intelligence
concepts: Repository Knowledge as the foundational deterministic layer,
with Historical Memory, the Dependency Knowledge Graph, Change Impact
Analysis, and Advisory Reasoning Expansion all explicitly built to
"emerge from" or "consume" Repository Knowledge rather than stand as
independent subsystems. 118R recommended freezing Repository
Intelligence as one coherent contract, since all later layers specialize
the same base primitives.

Phase 119 (119A-119AC) froze the Repository Intelligence contract at
three levels of increasing precision — conceptual contract (119A/119B),
conceptual schema (119C/119D), artifact contract (119E/119F) — then
implemented, verified, and finally reviewed a complete, executable
JSON Schema Draft 2020-12 schema line (119G-119AC): twelve shared
components and eight artifact-family schemas. 119AC's cross-schema
final review confirmed the complete line is internally coherent,
contract-aligned, source-attributed, uncertainty-preserving,
boundary-preserving, read-only, and non-authoritative, with no schema
or shared-component corrections required, and concluded the line is
ready to inform 120A.

120 begins the read-only prototype layer: the layer that will, in
future phases, actually produce artifacts shaped by the 119 schemas.
Throughout 118, 119, and now 120A, the PCAE runtime execution boundary
has not changed: runtime state remains `Observed`, maximum plugin
capability remains `observe`, and execution remains unavailable. 120A
does not change this, and no phase in the 120 read-only prototype
sequence may change it until a separate, explicitly scoped execution
architecture phase is proposed and approved (Section 24).

## 3. Scope

120A is architecture only:

- Defines the layered architecture, stages, input/output models,
  persistence architecture (conceptual, non-final), verification
  architecture, and governance architecture for the future read-only
  prototype.
- Defines read-only guarantees, source attribution architecture,
  Evidence boundary architecture, uncertainty/unknown handling,
  limitation/disclaimer architecture, and boundary disclosure
  architecture that any future generator must satisfy.
- Defines failure and no-go conditions for future generator phases.
- Defines the 120 phase roadmap (120B-120F) and optionally later
  tracks (121+).
- Documents and classifies known inherited tooling/reporting issues
  carried forward from 119.
- Recommends 120B as the next phase.

120A does not:

- Implement a generator, extractor, repository scanner, or graph
  builder.
- Produce any generated Repository Intelligence artifact.
- Perform repository scanning or extraction of any kind.
- Implement a validator or validation library.
- Implement a CLI command.
- Implement Python models, Pydantic models, or dataclasses.
- Implement an automated test suite.
- Change runtime behavior, Advisory behavior, or Decision Evaluation
  behavior.
- Introduce execution.

## 4. Non-Goals

This phase explicitly does not implement: generated artifacts;
generator code; a source scanner; a repository scanner; an extractor;
a graph builder; graph traversal; a query engine; a package builder; a
validator; a validation library; a schema verification CLI; a CLI of
any kind; Python models; Pydantic models; dataclasses; an automated
test suite; a runtime plugin; runtime behavior change; Advisory
behavior change; Advisory Runtime change; Advisory integration; Decision
Evaluation behavior change or replacement; Evidence subsystem behavior
change; Repository Skills behavior change; execution; shell mediation;
Permission Broker changes; lifecycle redesign; lifecycle bug repair
unless explicitly scoped; REST; Dashboard; Web UI; Telegram inbound;
provider selection; multi-model orchestration; autonomous coding;
model capability expansion; automatic patch generation; automatic
refactoring; repository mutation outside allowed docs/status files;
runtime plugin changes; Repository State changes; source code changes;
test code changes; repository intelligence extraction; repository
knowledge extraction; historical memory extraction; git history
analysis; timeline generation; dependency extraction; dependency
scanning; diff analysis; impact analysis; impact prediction;
blast-radius computation; dependency graph construction; graph query
engine; query execution; query result generation; query ranking;
package generation; package validation; package registry; package
integrity computation; Advisory Intelligence Context generation;
Advisory Context Package generation; and any fixtures or sample
artifacts.

## 5. Prototype Architecture Overview

The future read-only prototype is defined here as a staged
architecture. In 120A these are architectural stages only — none is
implemented, and no code, fixture, or sample artifact exists for any of
them as a result of this phase.

1. **Source inventory stage** — conceptually identifies which governed,
   already-committed repository materials a future generator may read
   (Section 7).
2. **Source attribution stage** — conceptually ties every future
   generated claim to one or more Source Attribution Records, reusing
   the frozen locator vocabulary from the 119 Artifact Contract
   (`file_path`, `file_path_line`, `file_path_symbol`,
   `file_path_section`, `phase_id`, `phase_report_id`, `task_id`,
   `commit_sha`, `tag`, `release_id`, `evidence_id`, `decision_id`,
   `contract_document_section`, `canonical_report_id`).
3. **Deterministic extraction planning stage** — conceptually plans
   which deterministic, non-inferential methods a future generator may
   use to read source material (e.g. parsing structured files, reading
   known governance artifacts, inspecting git history/commit metadata,
   matching exact document references) without performing any
   extraction now.
4. **Artifact assembly stage** — conceptually assembles source-attributed
   claims into the shape of one target artifact family (Section 9).
5. **Schema-shape alignment stage** — conceptually aligns the assembled
   structure against the frozen 119 schema for the target family
   (`envelope`, `boundary_disclosures`, `disclaimers`, and the
   family-specific fields).
6. **Limitation/unknown capture stage** — conceptually records what the
   generator could not determine, using the shared uncertainty/
   verification-state vocabulary rather than omitting or guessing.
7. **Boundary/disclaimer attachment stage** — conceptually attaches the
   required boundary disclosure and disclaimer constants so the
   artifact cannot be misread as authoritative.
8. **Output persistence stage** — conceptually writes the artifact to a
   proposed (not final) location under governed, non-authoritative
   status (Section 16).
9. **Verification/reporting stage** — conceptually verifies the produced
   artifact against the frozen schema and boundary rules, and reports
   the result through the existing governed phase-report/notification
   pipeline, not a new reporting subsystem.

## 6. Architectural Layers

- **Schema Contract Layer** — the frozen 119 schema line
  (`schemas/repository_intelligence/{shared,artifacts}/`). Read-only
  reference for all later layers; not modified by 120A or any prototype
  phase without a governed contract-freeze phase.
- **Source Observation Layer** — the conceptual boundary through which a
  future generator may read governed repository material (Section 7).
  Read-only by construction: no layer above it may write back into
  observed sources.
- **Attribution Layer** — ties every claim produced by the Artifact
  Assembly Layer to Source Attribution Records and, where applicable,
  Evidence Link Records; enforces the "no unattributed claim" invariant
  established in the 119 Artifact Contract.
- **Artifact Assembly Layer** — conceptually assembles attributed claims
  into a shape matching one 119 artifact-family schema; the only layer
  that produces artifact-shaped structure.
- **Boundary/Disclaimer Layer** — attaches `boundary_disclosures` and
  `disclaimers` (from the shared components) to every assembled
  artifact; a future generator cannot emit an artifact that skips this
  layer.
- **Persistence Layer** — conceptually responsible for writing produced
  artifacts to a proposed, non-final location (Section 16), under the
  same governed-commit discipline as every other PCAE artifact.
- **Verification Layer** — conceptually responsible for checking a
  produced artifact against its schema and boundary rules before it can
  be treated as anything more than a draft; reuses PCAE's existing
  governed phase-report and check pipeline rather than introducing a
  new one.
- **Human Review Layer** — the layer at which a person (not Advisory, not
  Decision Evaluation, not an autonomous agent) decides whether a
  produced artifact is fit to be treated as current Repository
  Intelligence input for some other purpose; this layer's approval
  authority is out of scope for 120A to define in detail and is
  explicitly reserved for later phases (Section 20).

## 7. Input Model (Conceptual)

Future allowable inputs, conceptually, for a read-only generator:

- committed repository files (source, tests, docs)
- phase documents (`docs/PHASE_*.md`)
- status files (`PROJECT_STATUS.md`, `CHANGELOG.md`)
- task memory (`tasks/TODO.md`, `tasks/DONE.md`, `tasks/active/`,
  `tasks/done/`)
- schema files (`schemas/repository_intelligence/**/*.schema.json`)
- canonical phase reports (`.pcae/phase-reports/**`,
  `.pcae/phase-completion-report.md`,
  `.pcae/phase-completion-metadata.json`)
- governance outputs (`pcae check`, `pcae health`, `pcae doctor`
  results as already recorded in canonical artifacts, not re-run as
  part of generation)
- git history and commit metadata, read via standard, deterministic
  git inspection (no shell mediation beyond what PCAE's existing
  governed commands already perform)

120A does not read or process any of these beyond the architecture
review already performed for this document and by the 119 line. No
input is parsed, extracted, or transformed as a result of 120A.

## 8. Output Model (Conceptual)

Future output artifacts, conceptually, one per 119 artifact family:

- Repository Knowledge Snapshot artifact (first target, Section 9)
- later: Historical Memory Snapshot artifact
- later: Dependency Knowledge Graph Snapshot artifact
- later: Change Impact Report artifact
- later: Advisory Intelligence Context Package artifact
- later: Query Result artifact
- later: Repository Intelligence Package artifact
- Contract Conformance Record remains structural/self-descriptive
  rather than a generation target in the same sense as the other seven

120A creates no generated output artifact, fixture, or sample of any
kind. The output model above is a target list for future phases, not a
deliverable of this phase.

## 9. First Prototype Target: Repository Knowledge Snapshot

The first future prototype target is the **Repository Knowledge
Snapshot** artifact
(`schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`,
implemented in 119O). This choice is grounded directly in Phase 118A's
Repository Knowledge Architecture and in the schema-implementation
order confirmed coherent in 119AC (Section 24 of the 119AC final
review):

- It is the first content-bearing Repository Intelligence artifact
  family; Contract Conformance Record (119M) is structural, not a
  generation target of the same kind.
- 118A already describes a read-only production model for Repository
  Knowledge specifically: source discovery, extractors producing
  source-attributed claims, normalization, conflict detection
  (preserving contradictions rather than resolving them), snapshot
  assembly, and inspection surfaces — with production explicitly
  required to be read-only ("Extractors may read repository files and
  git metadata. They may not rewrite docs, tests, source, task records,
  phase reports, or canonical artifacts.").
- It is safer than the graph, impact, query, or Advisory context
  artifacts: 118's own architecture states that Historical Memory, the
  Dependency Knowledge Graph, and Change Impact Analysis are all
  designed to "emerge from" or "consume" Repository Knowledge, and
  Advisory Reasoning Expansion explicitly does not own or extract
  Repository Knowledge. Building any of those first would require
  Repository Knowledge to already exist as a dependency.
- It supports an observe-before-reason progression: a Repository
  Knowledge Snapshot only records what is directly observable
  (files, structure, declared relationships) with source attribution,
  without requiring any reasoning, prediction, or graph traversal.
- It does not require execution: every accepted source type Phase 118A
  names (source files, tests, docs, phase reports,
  `.pcae/phase-completion-metadata.json`, changelog entries, task
  records) and every accepted extraction method (parsing structured
  files, reading known governance artifacts, inspecting git history,
  matching exact document references, parsing import relationships
  with deterministic tools, reading test names/paths) is achievable
  without running the repository's own code.

120A does not implement Repository Knowledge Snapshot generation. It
only designates it as the first target for 120D-120F.

## 10. Read-Only Guarantees

Any future prototype phase must preserve, at the architecture level:

- No file mutation outside governed docs/status updates performed
  through the existing PCAE governed lifecycle (task contracts,
  `pcae commit`, `pcae task finish`, `pcae phase complete`).
- No source modification (no generator may rewrite `src/` or `tests/`).
- No execution (no generator may run repository code, install
  dependencies, or invoke a shell to produce artifact content).
- No shell mediation beyond what PCAE's existing governed commands
  already perform.
- No package installation.
- No network dependency.
- No runtime plugin change (runtime state remains `Observed`, maximum
  capability remains `observe`).
- No Advisory behavior change.
- No Decision Evaluation replacement.
- No Evidence truth claim (a generator may reference Evidence via
  Evidence Link Records; it may never assert Evidence truth or
  sufficiency itself).
- No Repository State truth claim (a generator may reference Repository
  State via source attribution; it may never assert Repository State
  truth or authority itself).

## 11. Source Attribution Architecture

Every future generated claim must be tied to one or more Source
Attribution Records, reusing the shared
`source_attribution_record.schema.json` component and the locator
vocabulary frozen in the 119 Artifact Contract
(`file_path`, `file_path_line`, `file_path_symbol`,
`file_path_section`, `phase_id`, `phase_report_id`, `task_id`,
`commit_sha`, `tag`, `release_id`, `evidence_id`, `decision_id`,
`contract_document_section`, `canonical_report_id`). A claim without an
attributable source must be represented as `unknown` or `inferred`
rather than asserted as fact — this rule is already structurally
enforced by the 119 schemas (every content-bearing `$def` requires
`source_attribution`) and 120A carries it forward as a generation-time
invariant, not a new rule.

## 12. Evidence Boundary Architecture

A future generator may reference Evidence only through Evidence Link
Records (`evidence_link_record.schema.json`), which distinguish
candidate references from `accepted_by_evidence_subsystem` status. A
generator producing an artifact with no genuine Evidence link must
include an Evidence Link Record with `evidence_type:
evidence_gap_marker` rather than omit the field, consistent with the
119 Artifact Contract. A generator must never claim to replace,
bypass, or preempt the Evidence subsystem, and Evidence Link Records
remain references, never proof.

## 13. Uncertainty and Unknown Handling

Future artifacts must represent uncertainty using the frozen shared
`uncertainty_verification_state.schema.json` vocabulary: `known,
unknown, unverified, partially_verified, weak, possible, inferred,
advisory_only, decision_required, verified, invalid, stale,
superseded, conflicting`. A future generator must never perform a
"prohibited uncertainty collapse" (for example, converting `unknown`
to `known` without new source attribution, or silently dropping a
`conflicting` state to present a single clean answer). Every
artifact-family schema already requires an `unknowns_gaps` (or
`unknowns`) array at the artifact level in addition to per-record
uncertainty state; a future generator must populate this honestly
rather than leave it empty to imply completeness.

## 14. Limitation and Disclaimer Architecture

Future artifacts must consistently populate `limitation_record`
entries (`limitation_record.schema.json`) wherever a generator's own
method, source coverage, or determinism has bounds — for example,
"this extraction method could not resolve dynamic imports" or "this
snapshot covers only committed files, not working-tree changes." Every
artifact-family schema requires the shared `disclaimer.schema.json`
constants (`non_decision_disclaimer`, `no_execution_disclaimer`,
`advisory_non_authority_disclaimer`, `evidence_boundary_disclaimer`,
`repository_state_boundary_disclaimer`) plus a family-specific
`*_disclaimer` const; a future generator must emit these verbatim as
frozen by the 119 schema line, never paraphrase or omit them.

## 15. Boundary Disclosure Architecture

Every future generated artifact must preserve the nine const-`true`
declarations required by the shared `boundary_disclosure.schema.json`
component: `read_only`, `no_execution`, `non_decision`,
`advisory_non_authority`, `decision_evaluation_required`,
`no_repository_mutation`, `no_lifecycle_mutation`,
`no_evidence_replacement`, `no_repository_state_replacement`. A future
generator that could not honestly declare all nine must not produce an
artifact at all — it is not permitted to declare a boundary falsely to
satisfy schema validity.

## 16. Persistence Architecture (Conceptual, Non-Final)

A future generated artifact's output location has not been chosen.
Possible future locations, listed here only as options for 120B's
contract freeze to evaluate, not as a decision:

- `.pcae/repository-intelligence/`
- `artifacts/repository-intelligence/`
- `reports/repository-intelligence/`

No path is recommended by 120A. Whichever option (or another) is
selected must be decided explicitly in 120B (Repository Intelligence
Prototype Contract Freeze), not inferred from this architecture
document. No location is created, and no file is written to any of
these paths as a result of 120A.

## 17. Verification Architecture (No Validators Implemented)

Later phases (120D-120F and beyond) should verify future generated
artifacts against:

- schema parse (valid JSON, matching the 119 schema's declared shape)
- schema conformance, once a conformant JSON Schema validator exists
  (no such validator exists yet in the 119 or 120 line; 120A does not
  create one)
- source attribution completeness (every content-bearing claim has an
  attributable source or an explicit `unknown`/`inferred` marker)
- unknown/limitation presence checks (the artifact does not imply false
  completeness)
- boundary/disclaimer checks (all nine boundary disclosures and all
  required disclaimer constants are present and unmodified)
- no-authority checks (the artifact does not imply approval, execution
  permission, Advisory decision, or Decision Evaluation outcome)
- no-execution checks (the artifact's provenance does not indicate it
  was produced by running repository code)

120A does not implement any validator, validation library, or
verification CLI. These checks are architecture requirements for
120D-120F to design and, eventually, implement.

## 18. Governance Architecture

Future prototype phases must remain governed exactly as every phase in
the 118/119 line has been:

- governed phase lifecycle (task contracts via `pcae task new`, staged-
  file-aware commits via `pcae commit implementation`, `pcae task
  finish`, `pcae phase complete`)
- governed commit/push only; no raw `git commit`, no raw `git push`, no
  `--no-verify`, no force push
- `origin/main..HEAD` returned to 0 at the end of every phase
- runtime remains `Observed` / `observe` throughout; no phase in the
  120 read-only prototype sequence may change this without a separately
  scoped and approved execution-architecture phase (Section 24, and see
  the placeholder "125+" note in Section 20)

## 19. Failure and No-Go Conditions

A future prototype phase or generator must halt (no-go) if any of the
following would otherwise occur:

- missing source attribution on a content-bearing claim
- a generated artifact implies truth or completeness beyond what its
  sources support
- a generated artifact implies approval
- a generated artifact implies execution permission
- the generator attempts repository mutation (writing to `src/`,
  `tests/`, or any file outside its designated, governed output
  location)
- the generator changes source files
- the generator invokes Advisory
- the generator performs Decision Evaluation
- the generator performs graph traversal
- the generator performs impact analysis
- the generator executes commands
- the generator relies on runtime plugins beyond the existing
  `observe`-capability posture

## 20. Track 120 Phase Roadmap

Recommended sequence:

- **120A** — Repository Intelligence Read-Only Prototype Architecture
  (this phase)
- **120B** — Repository Intelligence Prototype Contract Freeze
- **120C** — Repository Intelligence Prototype Contract Verification
- **120D** — Repository Knowledge Snapshot Prototype Plan
- **120E** — Repository Knowledge Snapshot Prototype: Read-Only
  Generator
- **120F** — Repository Knowledge Snapshot Prototype Verification

Optional, not-yet-committed later phases, listed here only as a
tentative long-range shape and explicitly not activated by this
document:

- **121** — Repository Intelligence Query/Report Layer
- **122** — Advisory Context Consumption
- **123** — Change Impact Read-Only Prototype
- **124** — Prototype Review / Hardening
- **125+** — Execution Planning Architecture, only after the read-only
  knowledge layer matures, and only as its own explicitly scoped,
  separately approved architecture phase

No phase beyond 120B is activated by this document. Per
`tasks/TODO.md`'s own source-of-truth precedence rule, only the phase
explicitly named "Recommended next repo phase" in `PROJECT_STATUS.md`
is confirmed; everything listed above after 120B is a tentative
candidate sequence, not a committed queue.

## 21. Relationship to Phase 119

Phase 119 defines schema shape: twelve shared components and eight
artifact-family JSON Schema Draft 2020-12 schemas, frozen, implemented,
verified per-family, and finally reviewed as a coherent whole in 119AC.
Phase 120 defines the read-only prototype architecture for producing
artifacts that conform to those shapes. 120 does not alter, extend, or
reinterpret the 119 schemas; it treats them as the frozen, verified
vocabulary for any future generated artifact, exactly as 119AC's
readiness assessment (Section 35) recommended.

## 22. Relationship to Advisory

120 does not grant Advisory authority. A future generated Repository
Intelligence artifact may become an input that Advisory could someday
consume via the already-designed Advisory Intelligence Context Package
family (119W), but 120A does not implement, invoke, or modify Advisory
Runtime or any Advisory subsystem. Advisory consumption of Repository
Intelligence artifacts remains a separately scoped, not-yet-activated
future track (tentatively "122" in Section 20).

## 23. Relationship to Decision Evaluation

120 does not replace Decision Evaluation. Every 119 schema requires the
`decision_evaluation_required` boundary disclosure to be declared
`true`, and 120A carries that requirement forward unchanged: no future
generated artifact may assert that it has decided, authorized, or
substituted for a Decision Evaluation outcome.

## 24. Relationship to Execution

120 does not introduce execution. Runtime state remains `Observed`,
maximum plugin capability remains `observe`, and execution remains
unavailable throughout 120A and the entire 120B-120F sequence this
document defines. Any future move toward execution-backed generation
(for example, running a repository's own code to observe behavior)
would require its own explicitly scoped, separately approved
architecture phase — tentatively placed no earlier than "125+" in
Section 20 — and is not authorized, implied, or scheduled by this
document.

## 25. Known Inherited Issues

- **119Q report-generation-ordering defect**: the 119Q canonical report
  and metadata recorded `Commits: pending_` because the report was
  generated as part of the same commit it describes and could not
  self-reference its own resulting hash; 119R recovered the actual
  commit (`d804458fda2663d79577941f7c415a2a50fe1573`). **Classification
  for 120A: non-blocking for architecture.** It affects report-
  generation tooling, not schema content or prototype architecture, and
  does not affect anything 120A defines.
- **`is_phase_id_backward()` phase-id comparison bug** (documented in
  119AB, `src/pcae/core/phase_reports.py`): compares letter-suffix
  phase-id branches as plain strings, so `"AA" < "Z"` evaluates `True`,
  misclassifying same-series double-letter phase ids as backward.
  **Classification for 120A: non-blocking for architecture; should be
  tracked before generator implementation (120E) if the 120 series ever
  reaches a letter-length transition** (e.g. a hypothetical 120Z →
  120AA boundary). It does not affect 120A's own finalization since
  120A's id has no letter suffix following a same-series longer-branch
  id in this transition.
- **Repeated `report_notification_tests: pending_final_telegram_delivery`
  detail**: every phase-completion metadata file records this at
  canonical-report-generation time, because the report is generated
  before the final `pcae phase complete` call that actually dispatches
  the Telegram notification; every phase in the 119 line has
  independently confirmed the notification was in fact sent by
  re-running `pcae phase complete` with `PCAE_NOTIFY_ENABLED=1` after
  sourcing `~/.config/pcae/telegram.env`. **Classification for 120A:
  non-blocking, well-understood, and consistently handled**; it has
  never once indicated a missed notification.

None of the three known inherited issues blocks 120A or the 120B-120F
architecture defined here. All three should continue to be tracked as
lifecycle/report-generation tooling debt, separate from Repository
Intelligence schema or prototype-architecture work, and are candidates
for a future, explicitly scoped governance-repair phase — not for
repair inside the 120 read-only prototype track itself.

## 26. Recommended Next Phase

Recommended next phase:

`120B - Repository Intelligence Prototype Contract Freeze`

Reason: after defining the read-only prototype architecture, freeze
the prototype contract before planning or implementing any generator.
The contract must preserve the architecture boundaries defined here: no
execution, no mutation, no Advisory authority, no Decision Evaluation
replacement, no runtime behavior change, and no repository scanning
beyond explicitly contracted read-only observation in later phases.
