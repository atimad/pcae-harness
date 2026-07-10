# Phase 127D - Historical Memory Prototype Plan

## 1. Purpose

Phase 127D defines the definitive implementation plan for the first
deterministic, read-only Historical Memory Builder, bounded by the
127B contract and independently verified in 127C.

The builder shall consume existing Repository Intelligence artifacts
and the repository's own already-governed provenance record, and shall
produce a deterministic Historical Memory Snapshot artifact conforming
to the already-frozen 119Q schema.

This phase is documentation only. It implements no historical
extraction, modifies no runtime behavior, and creates no source code,
test code, or schema change. 127E implements the plan defined here;
127D performs none of it.

Historical Memory consumes existing Repository Intelligence artifacts
and produces deterministic Historical Memory artifacts. It never
performs reasoning. It never performs inference.

## 2. Grounding This Plan in Real Repository Data

Unlike 127A/127B/127C, which reasoned about the 119Q schema
conceptually, 127D grounds every mapping decision below in the actual,
currently-available data sources this repository has — read directly
for this plan, mirroring 126D's own grounding discipline for the
Dependency Knowledge Graph.

### 2.1 Repository Knowledge Snapshot has no lineage

Direct inspection of the most recent Repository Knowledge Snapshot
(`.pcae/repository-intelligence/latest.json`) confirms its envelope
carries exactly one `repository_context.repository_commit` value per
snapshot and its `architectural_entities` are a flat, structural list
with no temporal or lineage fields whatsoever. This confirms 127A's
own framing precisely: Repository Knowledge Snapshot answers "what
exists at this one commit," never "how did it get here." **Historical
Memory's temporal content cannot be derived from Repository Knowledge
Snapshot content itself** — it must come from a genuinely different
source.

### 2.2 `.pcae/phase-reports/` is not a durable source

Direct inspection confirms `.pcae/phase-reports/` (the canonical
`latest.json`/`latest.md` phase-report artifacts every recent phase in
this repository has produced) is listed in `.pcae/.gitignore` and is
therefore **never committed** — it exists only in the local working
tree of whichever agent most recently ran a phase, and does not
survive a fresh clone. A Historical Memory Builder that treated this
directory as its primary historical source would produce different,
non-reproducible output depending on which machine/session generated
it — directly violating 127B §11's determinism contract. **This
directory must not be a required input** for any deterministic
`historical_event`/`phase_lineage_record` the builder constructs; it
may be consulted opportunistically when present (as a richer, optional
elaboration source), but the builder's baseline chronology must not
depend on it existing.

### 2.3 Task contracts are the reliable, git-tracked historical source

Direct inspection confirms `tasks/done/` contains 854 committed,
git-tracked Markdown task-contract files, each with a consistent,
already-structured shape: `## Task ID`, `## Title`, `## Status`,
`## Mode`, `## Goal`, `## Created Timestamp`, plus `## Allowed Files`,
`## Acceptance Criteria`, and other sections. Every phase this
repository has completed since task-contract governance began has left
exactly one such file. This is the single most reliable, deterministic,
durable source of "what engineering work happened and in what order"
this repository actually has.

**Grounding fact**: a task contract's own body has no completion
timestamp — only `## Created Timestamp` (when the contract was
opened). The actual completion time is not embedded in the file; it is
implicit in the git commit that moved the file from `tasks/active/` to
`tasks/done/`. A deterministic builder must therefore correlate each
`tasks/done/*.md` file with the git commit(s) that introduced it (via
`git log --follow --diff-filter=A -- tasks/done/<file>`), not read a
nonexistent "completed at" field from the file's own content.

### 2.4 Git log is the deterministic backbone

Git commit history (`git log`) is the one source that is always
present, always deterministic for a fixed commit range, and already
carries exactly the fields `historical_time_reference`
(`time_reference_type: commit`) and `source_locator`
(`locator_type: commit_sha`) already anticipate. Direct inspection of
`shared/source_attribution_record.schema.json`'s `source_locator`
`$def` confirms its `locator_type` enum already includes `commit_sha`,
`task_id`, `phase_id`, `phase_report_id`, `tag`, `release_id` —
**this enum was clearly designed anticipating exactly this
task-contract-plus-commit provenance model**, not invented by this
plan. Likewise, `shared/phase_context.schema.json`'s own
`task_id` field is the direct, already-frozen attachment point for a
task contract's own `Task ID`.

### 2.5 CHANGELOG.md / PROJECT_STATUS.md are attribution-only, never extraction inputs

Both files contain rich, dated prose describing what each phase did,
but their content is free text, not structured data. Reliably
extracting structured facts from prose would require interpretation —
explicitly forbidden by 127B §3/§11 ("Historical Memory shall not ...
perform reasoning"). **These files may be cited as human-readable
attribution locators (`locator_type: file_path`) alongside a
structured claim already derived from a task contract or commit, but
must never themselves be the sole or primary source a candidate
historical claim is extracted from.**

### 2.6 Summary of the real input hierarchy

| Source | Reliability | Role |
| --- | --- | --- |
| `git log` (commit hash, author date, message, file changes) | Always present, deterministic for a fixed commit range | Backbone: `historical_time_reference`, `commit_sha` locators |
| `tasks/done/*.md` task contracts | Committed, git-tracked, structurally consistent | Primary source for `phase_lineage_record`, `historical_event` (phase-shaped events) |
| Repository Knowledge Snapshot (Track 120) | Committed if regenerated; structural only | Entity existence cross-reference only; never a temporal source |
| Dependency Knowledge Graph (Track 126) | Committed if regenerated; structural only | Structural cross-reference for `historical_relationship` endpoints, where a node already exists |
| `.pcae/phase-reports/` | **Gitignored, not durable** | Optional, opportunistic elaboration only — never required |
| `CHANGELOG.md` / `PROJECT_STATUS.md` | Committed, but free text | Attribution locator only — never an extraction source |

## 3. Objective

Produce deterministic historical evidence describing repository
evolution over time. Historical Memory shall describe, without
interpretation:

- **Repository evolution** — the declared sequence of phases and
  releases that produced the repository's current state, derived from
  `tasks/done/*.md` correlated with the git commits that introduced
  each file.
- **Engineering continuity** — the record of how engineering work
  (phases, decisions, repairs, hardening) proceeded, one
  `historical_event`/`phase_lineage_record` per task contract.
- **Architectural continuity** — phases whose `## Title`/`## Mode`
  indicate architecture/contract work map to the corresponding
  `event_type` values (Section 5.2).
- **Implementation continuity** — phases whose `## Mode` is
  `implementation` map to `schema_implemented`/`prototype_added`/
  `integration_recorded`-shaped events (Section 5.2).
- **Evidence continuity** — every constructed record's
  `source_attribution` cites the specific task contract file and/or
  commit SHA it was derived from; nothing is asserted without one.

## 4. Prototype Scope

Implementation plans below cover: historical builder, historical
validation, historical persistence, historical metadata, provenance
propagation, limitation propagation, boundary propagation, and
deterministic output. None of these is implemented in this phase.

## 5. Historical Model

### 5.1 Inputs

The builder shall consume only:

- **git commit history** for a bounded, explicitly-specified commit
  range (e.g. all commits reachable from `HEAD`, or a caller-supplied
  range) — read via governed git plumbing, never by shelling out to an
  unbounded or ambient `git log` call without an explicit range;
- **`tasks/done/*.md` task contract files** — read directly as
  repository files (task contracts are governance artifacts, not
  Repository Intelligence content, so this is not a Query Layer
  boundary violation — precisely analogous to how Track 120's own
  generator reads repository files directly to build the Repository
  Knowledge Snapshot in the first place);
- **an existing Repository Knowledge Snapshot**, reached exclusively
  through the Track 121 Query Layer, for structural entity
  cross-reference only (Section 2.6) — never as a temporal source;
- **an existing Dependency Knowledge Graph artifact**, where present,
  for structural relationship cross-reference only, per 127B §10's
  "where required for structural references" scoping — never
  traversed, never regenerated, and entirely optional (a Historical
  Memory Snapshot must remain constructible with zero Dependency
  Knowledge Graph input, since the graph may not exist for a given
  repository state).

No repository scanning beyond what is already listed above. The
builder never parses file contents for symbols/imports (that remains
outside Track 120's own declared scope, per 126D's finding, and is not
this track's concern either), never reads `.pcae/phase-reports/` as a
required input (Section 2.2), and never independently reruns the
Track 120 generator.

### 5.2 Historical Event Mapping

Resolving the frozen `event_type` enum (127B §5, independently
re-verified in 127C) against real task-contract content, binding for
127E:

| Task contract signal | `event_type` |
| --- | --- |
| `## Mode: architecture` | `architecture_defined` |
| `## Mode: architecture` + title contains "Review" | `architecture_reviewed` |
| `## Mode: architecture` + title contains "Contract Freeze" | `contract_frozen` |
| `## Mode: verification` + title contains "Contract Verification" | `contract_verified` |
| `## Mode: implementation` + title contains "Schema" | `schema_implemented` |
| `## Mode: verification` + title contains "Schema" | `schema_verified` |
| `## Mode: implementation` + title contains "Prototype" | `prototype_added` |
| `## Mode: implementation` (general) | `integration_recorded` |
| `## Mode: implementation` + title contains "Hardening" | `hardening_completed` |
| `## Mode: implementation` + title contains "Repair" | `repair_completed` |
| Task file's own `git log` introduction commit is tagged as a release | `release_published` |
| Every `## Status: done` transition | `phase_completed` |
| Every task contract's own creation (`## Created Timestamp`) | `phase_started` |

**Critical v1 scope finding**: title/mode string matching is a
deterministic, explicit, rule-based classification — not inference —
but it is necessarily an approximate mapping bounded by how
consistently task-contract titles/modes have been written across 854
existing files. Where no rule matches, the builder must classify the
event as `event_type: unknown` (the frozen enum's own honest fallback)
rather than guess. This mirrors 126D §5.2's "near-zero non-containment
edges" finding: the mapping is correct and complete for the enum, but
real classification coverage depends on the consistency of the
underlying source data, which 127D does not control and does not
retroactively normalize.

`governance_check_completed`, `report_generated`, `metadata_promoted`,
and `notification_sent` event types have no reliable task-contract or
git-log signal in v1 (they describe sub-phase-granularity governance
actions this repository does not durably record outside the gitignored
`.pcae/phase-reports/`, per Section 2.2) — **v1 produces zero events of
these four types**, and this must be stated as an explicit limitation,
not silently omitted.

`decision_recorded`, `supersession_recorded`, `correction_recorded`
map to the three Historical Transition record types directly (Section
5.4), not to generic `historical_event` records — avoiding double
representation of the same fact as both an event and a transition
record.

### 5.3 Historical Timeline

Per 127B §5/127C's independent confirmation, the timeline is not a
distinct record — it is the ordered `historical_events` +
`phase_lineage` + `release_lineage` arrays, ordered by
`historical_time_reference`. Concretely: every constructed event's
`event_time.time_reference_type` is set to `commit`, with
`time_reference_value` set to the introducing commit's SHA and
`time_reference_source` citing the same commit via a `commit_sha`
locator — never a wall-clock timestamp guess, since git commit
identity is the only value the builder can establish deterministically
and non-ambiguously from the actual source data (a task contract's own
`## Created Timestamp` is operator-entered free text, not
independently verifiable, and is therefore cited as a *limitation*-
qualified supplementary data point, never as the authoritative
`time_reference_value`).

**Resolving 127C Finding 2 (null-boundary time references)**: a
`historical_period`/`historical_time_reference` with a genuinely
unknown boundary (e.g. an ongoing, not-yet-closed task contract with no
corresponding `tasks/done/` commit yet) shall have that boundary's
`time_reference_value`/`period_end` explicitly set to `null`
(schema-permitted) with `uncertainty_state.state_value: "unknown"` and
an explicit `state_reason` naming why. For deterministic ordering, the
builder sorts strictly by non-null time references first (stable sort,
ties broken by `event_id`); records carrying a `null` boundary sort
**after** all records with a fully-resolved time reference of the same
`time_reference_type`, and among themselves are ordered by `event_id`
(never by insertion/discovery order). This is a concrete, binding
resolution of 127C's finding, not a deferral of it — 127E must
implement exactly this rule.

### 5.4 Historical Transition

- **`decision_history_record`** — v1 produces zero decision records.
  This repository's governed decision points (e.g. 125F's Track 126
  selection) are recorded in prose within phase documents
  (`docs/PHASE_*.md`), not in any structured, task-contract-adjacent
  field a deterministic rule can extract without interpretation.
  Explicit limitation, not silently omitted (mirrors 126D's own
  "zero imports edges" honesty pattern).
- **`repair_hardening_record`** — populated deterministically for any
  task contract whose title contains "Repair", "Hardening", or "Fix"
  (case-insensitive, exact substring match — e.g. 126G, 126G.1, the
  126E metadata-fix tasks), with `issue_or_boundary_addressed` and
  `correction_or_hardening_summary` populated from the task contract's
  own `## Goal` field verbatim (cited, not paraphrased — paraphrasing
  would be reinterpretation, forbidden by 127B §7).
- **`supersession_correction_record`** — populated deterministically
  only where a task contract's own text contains an explicit,
  parseable reference to a specific prior phase ID it supersedes or
  corrects (e.g. this very document's own 127C→127B citation-correction
  pattern). Where no such explicit, unambiguous reference exists, no
  record is produced — never inferred from title similarity or timing
  proximity alone.

### 5.5 Historical Relationship

**Resolving 127C Finding 1 (`historical_reference`/`reference_type`
not explicitly named)**: every `historical_relationship`'s
`source_reference`/`target_reference` is a `historical_reference`
object (`reference_id`, `reference_type`, optional
`reference_locator`), independently re-confirmed by 127C as the
correct schema resolution. 127D fixes `reference_type` deterministically
per the entity being referenced:

| Referenced entity | `reference_type` |
| --- | --- |
| A `historical_event` this builder constructed | `historical_event` |
| A `historical_claim` this builder constructed | `historical_claim` |
| A `phase_lineage_record`'s own `phase_id` | `phase` |
| A `release_lineage_record`'s own `release_id` | `release` |
| A `decision_history_record`'s own `decision_id` | `decision` |
| A `repair_hardening_record`'s own `record_id` | `repair_or_hardening` |
| A `supersession_correction_record`'s own `record_id` | `correction` |
| A git commit, task contract file, or other raw source | `source` |
| A Repository Knowledge Snapshot / Dependency Knowledge Graph artifact reference | `artifact` |
| Unresolvable | `unknown` |

`relationship_type` values are populated only where the underlying
source data explicitly supports them: `froze_contract` for a task
contract whose title contains "Contract Freeze", `verified_by` linking
a verification-mode task contract to the phase it verified,
`hardened_by`/`repaired_by` linking a repair/hardening-mode task
contract to its subject, `included_in_release` only where a release
tag genuinely contains the relevant commit (git-verifiable, never
guessed). `related_to` is the deterministic fallback for a
structural association the builder can establish (e.g. two task
contracts touching the same file) that does not fit a more specific
type — never a catch-all for weak/unverified guesses.

### 5.6 Historical Context

`historical_claim` records are produced sparingly in v1: one per
`phase_lineage_record` synthesizing "phase `<id>` was completed with
mode `<mode>`, per task contract `<file>`" — a direct restatement of
already-established facts, not new synthesis. No claim is produced
that isn't a direct restatement of a fact already established by an
event or lineage record with its own attribution.

### 5.7 Historical Evidence

Every record's `source_attribution` cites, per Section 2's grounding:
a `commit_sha` locator (for the introducing commit), a `task_id`
locator (for the task contract), and/or a `file_path` locator (for the
task contract file's own path) — never a generic "the repository" or
"task contracts" citation. This directly satisfies 127B §7's
specificity requirement, independently re-confirmed by 127C.

## 6. Historical Construction Pipeline (Planned Stages)

127E shall implement the following ten stages, matching the task
brief's own enumeration exactly. Each is a planned responsibility;
127D performs none of them.

1. **Input validation** — confirm the specified commit range resolves
   to a valid git history; confirm `tasks/done/` exists and is
   readable; confirm any supplied Repository Knowledge Snapshot/
   Dependency Knowledge Graph reference resolves via the Query Layer
   before any extraction begins; fail closed (Section 9) on any
   invalid or missing required input.
2. **Compatibility validation** — confirm the source Repository
   Knowledge Snapshot's (and, where supplied, Dependency Knowledge
   Graph's) `executable_schema_version` is recognized; fail closed on
   an unsupported version (Section 10).
3. **Snapshot ordering** — enumerate `tasks/done/*.md` files, resolve
   each to its introducing commit via `git log --follow
   --diff-filter=A`, and establish a deterministic, commit-ordered
   sequence (chronological by commit, ties broken by task ID string
   order) as the backbone the remaining stages build from.
4. **Timeline construction** — apply Section 5.2's event mapping to
   each ordered task contract, producing `historical_events` and
   `phase_lineage_record`/`release_lineage_record` entries with
   time references resolved per Section 5.3 (including the null-
   boundary rule resolving 127C Finding 2).
5. **Historical transition construction** — apply Section 5.4's rules
   to produce `decision_history_record`/`repair_hardening_record`/
   `supersession_correction_record` entries, honestly empty where no
   rule matches.
6. **Historical relationship construction** — apply Section 5.5's
   rules (resolving 127C Finding 1) to produce `historical_relationship`
   entries between already-constructed records.
7. **Provenance propagation** — populate `source_attribution` on every
   record per Section 5.7, citing the specific commit/task-contract
   source each was derived from.
8. **Limitation propagation** — populate `snapshot_limitations` with
   the explicit v1 scope limitations named throughout Section 5
   (zero `governance_check_completed`/`report_generated`/
   `metadata_promoted`/`notification_sent` events; zero decision
   records; `.pcae/phase-reports/` not consulted as a required
   source; task-contract title/mode classification is rule-based and
   bounded by source-data consistency), plus any inherited RKS/DKG
   limitations where those artifacts were supplied.
9. **Boundary disclosure propagation** — populate `boundary_disclosures`
   and the frozen `historical_memory_snapshot_disclaimer` const
   string, unchanged.
10. **Historical artifact serialization** — reuse Track 124's
    `serialize_deterministic_json` directly (no parallel serialization
    logic), matching 126D §9's own precedent and 127B §11's explicit
    recommendation to do so.

Validation of the assembled artifact (analogous to 126D's own
dedicated validation stage) is folded into stages 3-9 above via each
stage's own fail-closed checks (Section 9), rather than a separate
eleventh stage — since, unlike the Dependency Knowledge Graph's
node/edge validation (which checks a graph structure assembled in one
pass), Historical Memory's records are constructed incrementally from
an already-ordered backbone (stage 3) where invalid states are
naturally caught by construction, not discovered after the fact. 127E
must still implement an explicit final structural check (unique
identifiers, no dangling `historical_reference`s, every required field
present) before persistence, mirroring 126E's own independent
re-validation discipline — this is implicit in "no implementation
occurred" here, not omitted from the plan.

## 7. Stable Identifier Algorithm

Mirroring 126B §4.4/126D §7's binding node/edge identifier discipline
exactly, applied to Historical Memory's record types:

- **`event_id`**: `f"event:{commit_sha}:{task_id}"` — deterministic (a
  pure function of the introducing commit and task ID), stable
  (identical across repeated generation from the same commit range),
  and unique (a given commit introduces a given task file at most
  once).
- **`claim_id`**: `f"claim:{phase_id}"` — one synthesized claim per
  phase lineage record (Section 5.6), deterministic and unique by
  construction.
- **`relationship_id`**: `f"relationship:{relationship_type}:{source_reference_id}->{target_reference_id}"`
  — deterministic, stable, and unique (no two relationships may share
  the same type and endpoint pair; where source data could otherwise
  produce a duplicate, the builder fails closed per Section 9 rather
  than silently deduplicating).
- **`phase_id`** (on `phase_lineage_record`): the task contract's own
  `## Task ID` value, used verbatim — already unique by construction
  of this repository's task-contract naming convention (independently
  confirmed: no two `tasks/done/*.md` files share a Task ID).
- **`release_id`** (on `release_lineage_record`): the git tag name,
  used verbatim, where a commit is tagged; v1 produces zero release
  records where no tags exist in the supplied commit range (explicit
  limitation, not fabrication).
- **`record_id`** (on transition records): `f"{record_type_prefix}:{task_id_or_commit_sha}"`
  (e.g. `f"repair:{task_id}"`), deterministic and unique by the same
  reasoning as `event_id`.

This plan does not prescribe implementation-level hashing beyond the
string-concatenation schemes above — 127E may adjust exact separator
characters, but must preserve the determinism/stability/uniqueness
properties this section requires.

## 8. Determinism

Equivalent historical inputs shall always produce equivalent Historical
Memory outputs. Ordering rules shall be deterministic.

- Given the same commit range and the same `tasks/done/` content, two
  independent builder runs must produce byte-identical output except
  approved non-substantive timestamp fields (`envelope.generated_at_utc`,
  `snapshot_identity.snapshot_created_at_utc`) — mirroring 120B §6's
  rule, already reused by every subsequent Repository Intelligence
  artifact family including 126E.
- No historical claim, event, or relationship may be created by
  inference, heuristic guessing, probabilistic scoring, or AI-based
  judgment anywhere in extraction — Section 5's rules are all explicit,
  deterministic string/structural matches against task-contract
  content and git history, never semantic interpretation of prose.
- Ordering is deterministic per Section 5.3's resolution of 127C
  Finding 2, and Section 6 stage 3's commit-then-task-ID tie-break
  rule.
- Identifiers are deterministic per Section 7.

## 9. Failure Strategy

The builder shall fail closed for:

- **Missing snapshots** — a specified Repository Knowledge Snapshot
  reference that does not resolve via the Query Layer aborts
  generation entirely (Section 6 stage 1).
- **Incompatible schema versions** — an unrecognized
  `executable_schema_version` on any supplied artifact aborts
  generation (Section 6 stage 2).
- **Missing provenance** — any candidate record lacking a resolvable
  commit SHA and/or task ID is omitted, never assigned a fabricated
  attribution.
- **Incomplete chronology** — Section 5.3's null-boundary rule
  (explicit `unknown` state, never a fabricated timestamp).
- **Missing limitation metadata** — any record or the snapshot as a
  whole lacking at least one limitation record aborts generation
  (schema `minItems: 1`, independently re-confirmed by 127C).
- **Missing boundary disclosures** — absent `boundary_disclosures`/
  `disclaimers` material aborts generation.
- **Corrupted Repository Intelligence artifacts** — a Query Layer
  result that does not satisfy `validate_query_result_shape` (the
  existing Track 124 shared helper, reused per Section 6 stage 10's
  serialization-reuse precedent) aborts generation.

No fail-open path exists anywhere in this plan. This directly
implements 127B §9's Failure Contract for the concrete v1 builder.

## 10. Version Compatibility Plan

- **Track 119 executable schemas** — the builder consumes and produces
  only the already-frozen `historical_memory_snapshot.schema.json`
  (`119Q.1.0-json-schema`, independently re-confirmed by 127C); no
  schema file is touched by this plan or by 127E.
- **Track 120 artifacts** — the builder validates the source Repository
  Knowledge Snapshot's `executable_schema_version` before any
  extraction; an unrecognized version fails closed (Section 9).
- **Track 121 query contracts** — the builder's only access path to
  Repository Intelligence content for cross-reference purposes; not
  modified by this plan. This plan does not scope a new
  `historical_memory_query` category (127B §10/127C's independent
  confirmation that this remains unimplemented and unauthorized here).
- **Track 126 graph contracts** — where a Dependency Knowledge Graph
  artifact is supplied, its `executable_schema_version` is validated
  identically; where absent, the builder proceeds without it (Section
  5.1) — Dependency Knowledge Graph input is optional, never required.

## 11. Verification Strategy (What 127F Shall Verify)

127F shall independently verify:

- **Deterministic output** — two independent builder runs against the
  same commit range and `tasks/done/` content produce byte-identical
  output except approved timestamps.
- **Chronology correctness** — every generated event's time reference
  independently traced back to a real git commit; null-boundary
  records independently confirmed sorted per Section 5.3's rule, not
  arbitrarily.
- **Provenance propagation** — every generated record's
  `source_attribution` independently traced back to a real task
  contract file and/or commit.
- **Limitation propagation** — the explicit v1 scope limitations named
  in Section 6 stage 8 independently confirmed present in generated
  output, not silently dropped.
- **Boundary propagation** — boundary disclosures and the frozen
  disclaimer const string independently confirmed present unchanged.
- **Compatibility validation** — independently probed against at least
  one unsupported-schema-version scenario per artifact type consumed.
- **Fail-closed behavior** — independently probed against at least one
  scenario per Section 9 failure category.
- **Regression preservation** — Tracks 120-124/126's existing
  regression suites remain unaffected; the builder is a new, additive
  module requiring no change to `snapshot_builder.py`, the Query
  Layer, or the Dependency Knowledge Graph builder.
- **Serialization determinism** — independently confirmed that
  `serialize_deterministic_json` reuse produces the same compact/
  pretty/sorted-key behavior as every other Repository Intelligence
  artifact family.
- **Read-only guarantees** — independently confirmed via a persistence-
  never-mutates-source probe (checksum-identical source task-contract
  directory and Repository Knowledge Snapshot before/after generation),
  mirroring 126E/126F's own `test_persistence_never_mutates_source_
  snapshot`-shaped regression test.

## 12. Acceptance Criteria for 127E

127E's implementation shall be accepted only when all of the following
are objectively true:

1. `src/pcae/repository_intelligence/historical_memory/` exists with a
   builder, independent validation module, persistence module (reusing
   `serialize_deterministic_json`), and top-level orchestration module,
   mirroring the Dependency Knowledge Graph package's own shape
   (`graph_builder.py`/`graph_validation.py`/`persistence.py`/
   `graph_generator.py` → analogous `historical_builder.py`/
   `historical_validation.py`/`persistence.py`/
   `historical_generator.py`).
2. A governed CLI command,
   `pcae repository-intelligence historical-memory generate`, is
   wired consistently with the existing `snapshot generate`/
   `dependency-graph generate` commands.
3. Running the builder against this repository's own real commit
   history and `tasks/done/` content produces a schema-valid
   `historical_memory_snapshot.schema.json` artifact with zero
   validation errors (verified against the actual schema file, not a
   fixture).
4. Two independent runs against the same commit range produce
   byte-identical output except the two approved timestamp fields.
5. Every event/claim/relationship's `source_attribution` independently
   traces to a real commit SHA and/or task ID present in this
   repository's actual git history and `tasks/done/` directory.
6. All eight Section 9 failure categories are exercised by dedicated
   negative tests, each confirming fail-closed behavior.
7. `snapshot_limitations` explicitly names every v1 scope limitation
   Section 5/6 identifies (zero `governance_check_completed`/etc.
   events; zero decision records; `.pcae/phase-reports/` not
   consulted; rule-based classification bounded by source-data
   consistency).
8. Tracks 120-124/126 regression suites and `fast_green` all pass
   unmodified.
9. No traversal, reasoning, or execution capability is introduced,
   confirmed by the same AST-based import-inspection and
   no-forbidden-module-exists test pattern 126E already established.

## 13. Compatibility

This plan remains compatible with, and modifies none of:

- **Track 119 schemas** — consumed and produced only as already
  frozen; no schema file touched by this plan or by 127E.
- **Track 120 Repository Knowledge Snapshot** — read-only cross
  reference via the Query Layer; not modified.
- **Track 121 Query Layer** — the builder's only Repository
  Intelligence access path; not modified. No new query category is
  scoped or authorized here.
- **Track 122 Advisory Context Builder** — not modified; not consumed
  by 127E's builder.
- **Track 123 Change Impact Builder** — not modified; not consumed by
  127E's builder. The artifact 127E produces is available for a
  future, separately governed Change Impact revision to consume
  (127A §6.5), but no such revision is scoped here.
- **Track 126 Dependency Knowledge Graph** — read-only, optional
  structural cross-reference; not modified, not traversed.

## 14. Deferred Capabilities

Explicitly deferred, not authorized by this plan:

- historical reasoning;
- causal reasoning;
- timeline interpretation;
- recommendations;
- Decision Evaluation (integration);
- execution planning;
- execution capability;
- AI interpretation;
- predictive history;
- graph traversal.

## 15. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this plan.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this plan.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.

Not inherited defects (126G and 126G.1 are closed, verified repairs;
not reintroduced as open issues by this phase).

## 16. Strict Non-Goals

This phase does not implement: Historical Memory Builder; schemas;
generators; storage; timeline engine; graph traversal; repository
scanning; reasoning; recommendations; execution planning; execution
capability; runtime plugins; source code; or test code.

## 17. Governance Compatibility

This plan is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- implementation remains deferred to 127E, following this explicit
  plan;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 18. Acceptance

127D is complete when this implementation plan is documented, project
memory reflects 127D completion, runtime remains `Observed`/`observe`/
execution unavailable, no implementation has occurred, and the
recommended next phase is 127E - Historical Memory Prototype.
