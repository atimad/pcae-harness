# Phase 120B - Repository Intelligence Prototype Contract Freeze

## 1. Purpose

This document freezes the canonical contract governing the first
Repository Intelligence read-only prototype. It is the normative
specification that all later Track 120 implementation work (120D-120F
and beyond) must conform to. It does not implement anything; it fixes
the rules implementation must obey.

**Relationship to Phase 119 executable schemas.** Phase 119 froze,
implemented, verified, and finally reviewed (119AC) a complete JSON
Schema Draft 2020-12 schema line: twelve shared components and eight
artifact-family schemas under `schemas/repository_intelligence/`. This
contract does not alter, extend, or reinterpret those schemas. It
freezes the rules under which a future prototype may produce artifacts
that conform to them.

**Relationship to Phase 120A architecture.** Phase 120A defined the
read-only prototype architecture: nine conceptual stages, eight
architectural layers, conceptual input/output models, read-only
guarantees, and boundary architecture, all documented in
`docs/PHASE_120_REPOSITORY_INTELLIGENCE_READ_ONLY_PROTOTYPE_ARCHITECTURE.md`.
This contract freezes that architecture into binding, normative rules.
Where 120A described an option or a range of possibilities (for
example, the three candidate persistence locations), this contract
either selects among them or explicitly defers the selection to a
later phase — it does not silently narrow 120A's architecture without
saying so.

**Contract scope.** This contract governs exactly one prototype: the
first Repository Intelligence read-only prototype, whose sole
implementation target is the Repository Knowledge Snapshot artifact
family (Section 3). It does not govern any other artifact family, any
later Track 120 phase's own contract, or any Advisory, Decision
Evaluation, Evidence, or Repository State subsystem.

**Contract authority.** This contract is binding on 120D (Repository
Knowledge Snapshot Prototype Plan), 120E (Repository Knowledge
Snapshot Prototype: Read-Only Generator), and 120F (Repository
Knowledge Snapshot Prototype Verification). No later phase in this
sequence may implement behavior that this contract forbids, and no
later phase may treat a requirement of this contract as optional.
Deviation requires a new, explicitly scoped contract-amendment phase,
not a silent reinterpretation inside an implementation phase.

**Implementation independence.** This contract is implementation-
independent: it does not specify a programming language, a library, a
file format beyond "schema-conformant JSON," or a specific code
structure. 120D is free to choose implementation details, subject to
every rule this contract freezes.

## 2. Prototype Objective

Freeze the objective: deterministic generation of read-only Repository
Intelligence artifacts, conforming to the frozen 119 schema line,
without introducing any new runtime capability. The prototype must
operate entirely within the existing `Observed` / `observe` /
execution-unavailable runtime posture. Nothing in this contract
authorizes, implies, or schedules an increase in runtime capability.

## 3. First Prototype Target

The initial prototype shall generate only:

- **Repository Knowledge Snapshot**
  (`schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`,
  implemented in 119O)

No other artifact family (Contract Conformance Record, Historical
Memory Snapshot, Dependency Knowledge Graph Snapshot, Change Impact
Report, Advisory Intelligence Context Package, Query Result, or
Repository Intelligence Package) is included in the first
implementation. This restriction is binding on 120D-120F; extending
the prototype to any other family requires a new, separately scoped
contract phase.

## 4. Prototype Inputs

Conceptually allowed inputs for the first prototype, frozen from 120A
Section 7:

- the repository working tree (committed files)
- repository metadata (git commit history, tags, commit metadata)
- tracked documentation (`docs/*.md`, `README.md`, `AGENTS.md`)
- tracked repository artifacts (`schemas/**`, `tasks/**`,
  `PROJECT_STATUS.md`, `CHANGELOG.md`)
- governed lifecycle metadata (`.pcae/phase-reports/**`,
  `.pcae/phase-completion-report.md`,
  `.pcae/phase-completion-metadata.json`, task contracts in
  `tasks/active/` and `tasks/done/`)
- previously verified Repository Intelligence schemas
  (`schemas/repository_intelligence/**/*.schema.json`, frozen by 119)

Explicitly excluded:

- external services
- AI inference
- network sources
- runtime state mutation
- execution outputs (no input may be derived from running repository
  code)

An input source not on the allowed list may not be read by the
prototype without a contract amendment.

## 5. Prototype Outputs

The conceptual output model is frozen as:

- exactly one Repository Knowledge Snapshot artifact per generation run
- schema-conformant only (must validate against
  `repository_knowledge_snapshot.schema.json` and every shared
  component it references)
- deterministic (Section 6)
- read-only (Section 7)
- fully attributable (Section 8)
- bounded by explicit limitations (Section 11)

No other output artifact, file, log, or side-effect is authorized by
this contract for the first prototype.

## 6. Determinism Contract

Identical repository inputs must produce an identical Repository
Knowledge Snapshot structure, excluding approved metadata fields where
non-determinism is explicitly permitted (for example, a
`generated_at` timestamp field, if the schema envelope includes one,
or a `generation_run_id`). Approved exceptions must be limited to
metadata fields that do not affect the substantive content of the
snapshot (claims, source attributions, uncertainty states,
limitations). The prototype must never rely on probabilistic
reasoning, sampling, heuristic scoring with non-reproducible tie-
breaking, or any AI inference to produce snapshot content. Two runs
against the same repository state (same commit) must be
byte-for-byte identical except for approved metadata fields.

## 7. Read-Only Guarantees

The prototype shall never:

- modify repository files (`src/`, `tests/`, `docs/`, or any tracked
  file) outside its own governed output write, which itself must
  follow the existing PCAE governed lifecycle (Section 15)
- modify runtime state
- execute repository code
- execute shell commands beyond what PCAE's existing governed commands
  already perform
- invoke AI providers
- invoke external APIs
- mutate Repository State
- mutate Evidence
- mutate Advisory
- replace Decision Evaluation

Any prototype behavior that would violate one of these guarantees is a
contract violation, not an implementation detail to be resolved later.

## 8. Source Attribution Contract

- Every extracted fact must identify its source, using the frozen
  locator vocabulary from the 119 Artifact Contract (`file_path`,
  `file_path_line`, `file_path_symbol`, `file_path_section`,
  `phase_id`, `phase_report_id`, `task_id`, `commit_sha`, `tag`,
  `release_id`, `evidence_id`, `decision_id`,
  `contract_document_section`, `canonical_report_id`) via a Source
  Attribution Record.
- Attribution must remain deterministic: the same fact extracted from
  the same source must always produce the same attribution record
  shape and content.
- Missing attribution on a content-bearing claim is a contract
  failure. A fact that cannot be attributed must not be asserted; it
  must be represented as `unknown` or omitted from the snapshot
  entirely, never asserted without a source.

## 9. Evidence Boundary

Repository Intelligence is not Evidence. A Repository Knowledge
Snapshot produced under this contract may later support the Evidence
subsystem (for example, by being referenced from an Evidence Link
Record elsewhere), but it must never replace Evidence, assert Evidence
truth, or be treated as self-certifying proof of anything. Any
Evidence Link Record the prototype includes must use the shared
`evidence_link_record.schema.json` component and, where no genuine
Evidence link exists, must use `evidence_type: evidence_gap_marker`
rather than omit the field or fabricate a link.

## 10. Uncertainty Contract

The prototype must explicitly represent, rather than infer or paper
over:

- unknown information — represented as `unknown` using the shared
  `uncertainty_verification_state.schema.json` vocabulary
- incomplete information — represented via the artifact's
  `unknowns_gaps` array and/or `partially_verified` state
- conflicting information — represented via `conflicting` state and,
  where applicable, a `conflict_supersession_record`, which must
  preserve prior claims rather than silently discard them
- unverifiable information — represented as `unverifiable` or
  `unverified` state, never silently promoted to `verified`

The prototype must never perform a prohibited uncertainty collapse
(for example, converting `unknown` to `known` without new,
deterministic source attribution, or dropping a `conflicting` marker
to present a single clean answer).

## 11. Limitation Contract

Generated artifacts must be accompanied, when appropriate, by:

- limitation records (`limitation_record.schema.json`) — wherever the
  prototype's own extraction method, source coverage, or determinism
  has bounds
- disclaimer records (`disclaimer.schema.json` plus the
  `repository_knowledge_snapshot_disclaimer` const) — emitted verbatim
  as frozen by the 119 schema, never paraphrased
- boundary disclosures (`boundary_disclosure.schema.json`) — all nine
  const-`true` declarations (`read_only`, `no_execution`,
  `non_decision`, `advisory_non_authority`,
  `decision_evaluation_required`, `no_repository_mutation`,
  `no_lifecycle_mutation`, `no_evidence_replacement`,
  `no_repository_state_replacement`) must be present and unmodified
- uncertainty records — per Section 10, attached to every relevant
  claim, not just summarized at the artifact level

A generator that cannot honestly satisfy every one of these when
appropriate must not produce an artifact (see Section 14, Failure
Contract).

## 12. Prototype Stages (Conceptual)

The following stages are frozen as the conceptual shape the future
generator must follow. This contract freezes their existence, order,
and responsibility boundaries; it does not specify implementation.

1. **Source inventory** — enumerate which allowed inputs (Section 4)
   are present and in scope for this run.
2. **Source attribution** — associate each candidate fact with a
   deterministic Source Attribution Record before it may be used.
3. **Deterministic extraction** — apply only deterministic,
   non-inferential extraction methods to produce candidate claims from
   attributed sources.
4. **Artifact assembly** — assemble extracted, attributed claims into
   the shape of a Repository Knowledge Snapshot.
5. **Schema-shape alignment** — align the assembled structure against
   the frozen `repository_knowledge_snapshot.schema.json` shape.
6. **Unknown/limitation capture** — record what could not be
   determined, using the Section 10-11 vocabulary, rather than
   omitting or guessing.
7. **Boundary attachment** — attach the required boundary disclosures
   and disclaimers (Section 11) so the artifact cannot be misread as
   authoritative.
8. **Persistence** — write the artifact to its (not-yet-finalized,
   Section 13) output location under governed commit discipline.
9. **Verification** — verify the produced artifact against its schema
   and the boundary rules before treating it as anything more than a
   draft.
10. **Human review** — a person, not Advisory, not Decision
    Evaluation, not an autonomous agent, decides whether a produced
    artifact is fit to be treated as current Repository Intelligence
    input for some other purpose.

No implementation details are specified for any stage. 120D is
responsible for planning how each stage is realized, within the
boundaries this contract freezes.

## 13. Persistence Contract (Conceptual Only)

This contract freezes only the conceptual persistence expectations. It
does not specify storage implementation, file format details beyond
schema-conformant JSON, or a final output path.

120A proposed three candidate output locations without choosing among
them: `.pcae/repository-intelligence/`,
`artifacts/repository-intelligence/`, and
`reports/repository-intelligence/`. This contract does not select one.
The final output location must be decided in 120D (Repository
Knowledge Snapshot Prototype Plan), which is the phase this contract
delegates that decision to. Whatever location 120D selects, persistence
must occur only through the existing PCAE governed lifecycle (governed
task contracts, staged-file-aware commits, `pcae task finish`, `pcae
phase complete`) — a generator may never write output through an
ungoverned file write followed by a raw `git commit`/`git push`.

## 14. Verification Contract (No Validators Implemented)

This contract freezes conceptual verification expectations without
introducing validators. A future generated Repository Knowledge
Snapshot must be verifiable, at minimum, for:

- schema parse (valid JSON, matching the declared schema shape)
- schema conformance, once a conformant JSON Schema validator exists
  in a later phase (none exists yet; this contract does not create one)
- source attribution completeness (Section 8)
- unknown/limitation presence (Section 10-11)
- boundary/disclaimer presence and correctness (Section 11)
- determinism (Section 6) — re-running generation against unchanged
  input must reproduce the same substantive content

Verification remains architectural in this phase. No validator,
validation library, or verification CLI is implemented by 120B, and
none may be implemented before 120D plans how verification will occur
in 120F.

## 15. Failure Contract (Fail-Closed)

The prototype must be fail-closed. It must refuse to produce a
non-conformant artifact — producing nothing is always preferable to
producing an artifact that violates this contract. The prototype must
halt, not degrade or approximate, when it encounters:

- missing required sources (a source the schema requires is not
  reachable through an allowed input)
- attribution failures (a candidate fact cannot be given a
  deterministic Source Attribution Record)
- schema mismatch (the assembled structure does not match the frozen
  `repository_knowledge_snapshot.schema.json` shape)
- unknown mandatory fields (a field the schema requires `required` has
  no value the prototype can honestly populate, including the
  boundary disclosures and disclaimers of Section 11)
- boundary violations (any condition under Section 7's read-only
  guarantees would be violated by continuing)

## 16. Governance Contract

Every future prototype phase (120D-120F) must preserve:

- the observe-only boundary (runtime state `Observed`, maximum
  capability `observe`, execution unavailable)
- governed lifecycle compliance (task contracts, staged-file-aware
  commits, `pcae task finish`, `pcae phase complete`; no raw `git
  commit`, no raw `git push`, no `--no-verify`, no force push)
- repository cleanliness (`origin/main..HEAD` returned to 0 at the end
  of every phase)
- deterministic operation (Section 6)
- auditability (every generated artifact's provenance must be
  traceable to the inputs and extraction methods that produced it)
- reproducibility (Section 6 and Section 14's determinism check)

## 17. Explicit Non-Goals

This phase (120B) does not implement: a generator; a repository
scanner; an extraction engine; an artifact persistence implementation;
validators; a validation library; a schema verification CLI; a CLI of
any kind; Python models; dataclasses; Pydantic models; runtime
plugins; runtime behavior change; Advisory integration; a query
engine; graph traversal; execution planning; or execution capability.
It also does not implement any fixture, sample artifact, automated
test suite, source code change, or test code change.

## 18. Relationship to Future Phases

This contract governs and is binding on:

- **120C — Repository Intelligence Prototype Contract Verification**
  — independently verifies that this contract is internally
  consistent, unambiguous, and faithful to 119 and 120A before any
  planning or implementation begins.
- **120D — Repository Knowledge Snapshot Prototype Plan** — plans
  concrete implementation of the stages in Section 12 within this
  contract's boundaries, and makes the persistence-location decision
  deferred by Section 13.
- **120E — Repository Knowledge Snapshot Prototype: Read-Only
  Generator** — implements the generator planned in 120D, subject to
  every rule this contract freezes.
- **120F — Repository Knowledge Snapshot Prototype Verification** —
  verifies the 120E generator and its output against this contract.

No future implementation beyond this roadmap is authorized by this
document. Any track expansion (a second artifact family, a query
layer, Advisory consumption) requires its own new, separately scoped
contract phase.

## 19. Known Inherited Issues

Carried forward, unchanged in classification, from 119AC and 120A:

- **119Q report-generation-ordering defect**: the 119Q canonical
  report/metadata recorded `Commits: pending_` because the report was
  generated as part of the same commit it describes; 119R recovered
  the actual commit (`d804458fda2663d79577941f7c415a2a50fe1573`).
  **Classification: non-blocking for this contract.**
- **`is_phase_id_backward()` phase-id comparison bug**
  (`src/pcae/core/phase_reports.py`, documented in 119AB): compares
  letter-suffix phase-id branches as plain strings, misclassifying
  same-series double-letter phase ids as backward at certain
  transitions. **Classification: non-blocking for this contract;
  should still be tracked before a letter-length transition occurs
  within the 120 series** (e.g. a hypothetical 120Z → 120AA boundary,
  not relevant to 120B → 120C).
- **Recurring `report_notification_tests:
  pending_final_telegram_delivery` reporting detail**: every
  phase-completion metadata file records this at canonical-report-
  generation time because the report is generated before the final
  `pcae phase complete` call that dispatches the Telegram
  notification. **Classification: non-blocking, well-understood, and
  consistently handled.**

None of these three issues is repaired by this phase. Repair remains
explicitly out of scope for 120B, consistent with 119AC and 120A.

## 20. Recommended Next Phase

Recommended next phase:

`120C - Repository Intelligence Prototype Contract Verification`

Reason: before any planning or implementation of the read-only
generator begins, the frozen contract itself must be independently
verified for internal consistency, unambiguous wording, and fidelity
to Phase 119's schema line and Phase 120A's architecture — exactly as
every prior Track B contract (119A/119B, 119E/119F, 119H/119I) was
verified before implementation proceeded.
