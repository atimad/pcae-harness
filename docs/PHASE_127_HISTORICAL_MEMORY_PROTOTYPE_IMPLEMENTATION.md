# Phase 127E - Historical Memory Prototype

## 1. Purpose

Phase 127E implements the first deterministic, read-only Historical
Memory Builder exactly as defined by the 127A architecture, 127B
contract, 127C verification, and 127D implementation plan. This is
the first phase in Track 127 to touch `src/pcae/` source code.

The implementation remains strictly evidence-only: no historical
reasoning, no inference, no recommendations, no execution capability,
and no runtime behavior change.

## 2. Implementation Summary

Added `src/pcae/repository_intelligence/historical_memory/` (new
package):

- `git_source.py` — the only module in this package permitted to
  invoke `git` as a subprocess (mirroring exactly the precedent
  `source_inventory.py` already established for Track 120). Provides
  read-only git commit resolution, task-contract-file discovery and
  parsing, and tag enumeration.
- `historical_builder.py` — deterministic event/timeline/transition/
  relationship/context construction from task contracts, git history,
  and an existing Repository Knowledge Snapshot, consumed exclusively
  through the Track 121 Query Layer for structural cross-reference.
  Never imports `subprocess`.
- `historical_validation.py` — independent, fail-closed re-validation
  of the assembled snapshot (127D pipeline stage 10, folded into
  construction per 127D §6's own design note).
- `persistence.py` — write-only persistence, reusing Track 124's
  `serialize_deterministic_json`.
- `historical_generator.py` — top-level orchestration (the package's
  sole external entry point), mirroring `graph_generator.py`'s shape.

Wired a governed CLI command,
`pcae repository-intelligence historical-memory generate`, consistent
with the existing `snapshot generate` / `dependency-graph generate`
commands (`src/pcae/commands/repository_intelligence.py`,
`src/pcae/cli.py`).

Added `tests/test_phase_127e_historical_memory_prototype.py` (50
tests: 48 fast, synthetic-repository tests plus 2 `@pytest.mark.slow`
real-repository integration tests).

## 3. Historical Memory Builder Summary

The builder follows 127D's ten-stage pipeline:

1. **Input validation** — confirms the source Repository Knowledge
   Snapshot loads and is schema-valid; confirms `tasks/done/` exists
   and contains at least one task contract.
2. **Compatibility validation** — the source snapshot's
   `executable_schema_version` is validated by the Track 121 Query
   Layer's own `load_snapshot()`.
3. **Historical source validation** — every `tasks/done/*.md` file is
   deterministically parsed (`## Task ID`/`## Title`/`## Status`/
   `## Mode`/`## Goal`/`## Created Timestamp` sections extracted by
   fixed regex, never interpreted); a task contract missing its own
   `## Task ID` is omitted, never fabricated.
4. **Chronological ordering** — each task's introducing commit is
   resolved via `git log --diff-filter=A` against its exact
   `tasks/done/` path; records sort by commit author date (stable
   sort), with unresolvable dates sorting after all resolved ones
   (127D §5.3's resolution of 127C Finding 2), tie-broken by task ID.
5. **Timeline construction** — one `historical_event` and one
   `phase_lineage_record` per task contract; `event_type` classified
   deterministically from `## Title`/`## Mode` content per 127D §5.2's
   frozen mapping table, falling back to `unknown` — never guessed —
   where no rule matches.
6. **Transition construction** — `repair_hardening_record` entries for
   title-matched repair/hardening tasks; zero `decision_history_record`
   entries in v1 (127D §5.4's documented limitation).
7. **Relationship construction** — one `related_to` relationship per
   chronologically adjacent phase pair (a pure function of the
   established ordering), plus `repaired_by`/`hardened_by`
   relationships where a repair/hardening record's own goal text names
   exactly one other known phase code (127D §5.5, resolving 127C
   Finding 1's `historical_reference`/`reference_type` naming gap).
8. **Provenance propagation** — every record's `source_attribution`
   cites the specific task ID and/or commit SHA it was derived from.
9. **Limitation/boundary propagation** — inherited RKS
   `snapshot_limitations` merged with four explicit v1 scope
   limitations (no sub-phase governance events, no decision records,
   no phase-lineage traversal, task-classification coverage bounded by
   source-data consistency); `boundary_disclosures`/`disclaimers`
   propagated from the Query Layer's `boundary_lookup` result.
10. **Deterministic serialization** — Track 124's
    `serialize_deterministic_json` (sorted keys, stable indent modes).

## 4. Historical Evidence Model Summary

### 4.1 Confirmed Against Real Generated Output

Running the builder against this repository's own real git history and
`tasks/done/` content (850 task contract files at the time of this
implementation) produced:

- **850 historical events** and **850 phase_lineage_records** — one
  pair per task contract.
- **event_type distribution**: 497 `unknown` (task contracts that do
  not follow the `"Phase <ID> ..."` title convention — the majority of
  this repository's historical corpus, confirmed during 127D planning:
  only ~20 of several hundred files follow that convention), 220
  `integration_recorded`, 27 `contract_frozen`, 21 `hardening_completed`,
  21 `prototype_added`, 21 `schema_implemented`, 18 `repair_completed`,
  10 `architecture_defined`, 10 `contract_verified`, 5
  `architecture_reviewed`. This distribution is an honest reflection
  of real source-data consistency, not a builder defect — 127D
  explicitly anticipated this.
- **859 historical_relationships**: 849 `related_to` (chronological
  adjacency) plus 9 `repaired_by` and 1 `hardened_by` (deterministically
  resolved from unambiguous phase-code references in repair/hardening
  goal text).
- **2 release_lineage_records**, one per existing git tag
  (`v0.1.0-rc1`, `v0.2.0`).
- **39 repair_hardening_history records**, **0 decision_history
  records** (127D §5.4's documented v1 limitation), **0
  supersession_correction_history records** in this run (no task
  contract's goal text contained an unambiguous supersession/correction
  reference at generation time).

### 4.2 A Genuine Defect Found and Fixed During Implementation

Independent verification of the first generation run found only 237
distinct commits across 850 task contracts with a resolved commit
reference — far fewer than expected. Root cause: `git log --follow`
(the initial implementation) uses git's content-similarity rename
heuristic, which falsely treated unrelated task contract files as
renames of one another because they share heavy templated boilerplate
(identical `## Task ID`/`## Title`/`## Status`/... section headers).
This silently collapsed distinct task contracts onto the same
introducing commit.

**Fix**: removed `--follow` from `git_source.resolve_task_introduction()`.
Plain `git log --diff-filter=A` against the file's exact
`tasks/done/` path correctly resolves the commit that added it there —
which, since this repository's governed task-finish flow adds the file
at its `tasks/done/` path directly rather than using `git mv` from
`tasks/active/`, is also the semantically correct "task completed"
commit, not merely an implementation detail. Re-running after the fix
produced 806 distinct commits across 850 records (the remaining
overlap is legitimate: some governed phases commit multiple
`tasks/done/` files in a single commit) — confirmed by direct
inspection, not assumed.

## 5. Validation Summary

`historical_validation.validate_historical_snapshot()` independently
re-checks, and fails closed on:

- unique `event_id`, `claim_id`, `phase_id`, `relationship_id` values;
- every relationship's `source_reference`/`target_reference` resolves
  to a real constructed record;
- every `event_type` is a member of the frozen 21-value enum;
- every `relationship_type` is a member of the frozen 12-value enum;
- deterministic ordering (events/claims/phases/relationships sorted by
  identifier);
- `source_attribution` presence on every event/claim/phase/repair/
  relationship record;
- `limitations` presence on every record, plus snapshot-level
  `snapshot_limitations`;
- `boundary_disclosures`/`disclaimers`/disclaimer-const presence.

This validation stage does not trust the builder's own construction —
exercised by dedicated negative tests (duplicate identifiers, invalid
event/relationship types, dangling relationship endpoints).

## 6. Serialization Summary

Persistence reuses Track 124's `serialize_deterministic_json` directly
(no parallel serialization logic introduced), per 127D §6 stage 10.
Verified: two independent generation runs against the same source
snapshot and repository state produce byte-identical output except
`envelope.generated_at_utc` and `snapshot_identity.snapshot_created_
at_utc` — confirmed both on synthetic test fixtures and on this
repository's own real, full 850-task-contract corpus.

## 7. Persistence Summary

Writes only, to `.pcae/repository-intelligence/historical-memory/`
(`latest.json`, overwritten each run, plus a timestamped file under
`snapshots/`, one per run) — a location distinct from Track 120's own
`repository-intelligence/` snapshot directory and Track 126's own
`dependency-graph/` directory. Persistence never reads back or
mutates the source snapshot or `tasks/done/*.md` files; verified by
dedicated regression tests confirming byte-identical checksums
before/after generation, including against this repository's real
`tasks/done/` content.

## 8. Regression Results

Independently re-executed in this implementation session:

- Repository Knowledge Snapshot
  (`tests/test_phase_120e_repository_knowledge_snapshot.py`): passed.
- Query Layer
  (`tests/test_phase_121e_repository_intelligence_query.py`): passed.
- Advisory Context Builder
  (`tests/test_phase_122e_repository_intelligence_advisory_context.py`):
  passed.
- Change Impact Builder plus 124E hardening tests
  (`tests/test_phase_123e_repository_intelligence_change_impact.py`,
  `tests/test_phase_124e_repository_intelligence_hardening.py`):
  passed.
- Dependency Knowledge Graph
  (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`):
  passed.
- New Historical Memory tests
  (`tests/test_phase_127e_historical_memory_prototype.py`): 50 passed.
- Combined run of all six suites together: 160 passed.
- `python -m compileall src/` (full source tree): passed, 0 errors.
- `fast_green` (`python -m pytest -m "fast_green" -n auto -ra
  --durations=0`): 4390 passed, 0 failed (task contract existed for
  this run, matching the same task-lifecycle-state-dependent pattern
  already documented in 125A/125G/126E/126F).

## 9. Deterministic Generation Results

Independently verified via direct Python invocation (not just test
assertions): two calls to `generate_historical_memory()` against the
identical source snapshot and identical repository state (both the
synthetic test fixture and this repository's real, full corpus)
produced snapshots whose full content, with only the two approved
timestamp fields normalized, compared byte-equal (`==`) as parsed
JSON. Event, claim, phase-lineage, and relationship counts were stable
across runs.

## 10. Compatibility Confirmation

No file under `schemas/`,
`src/pcae/repository_intelligence/snapshot_builder.py`,
`src/pcae/repository_intelligence/snapshot_generator.py`,
`src/pcae/repository_intelligence/persistence.py`,
`src/pcae/repository_intelligence/query/`,
`src/pcae/repository_intelligence/dependency_graph/`,
`src/pcae/advisory/context/`, or
`src/pcae/repository_intelligence/change_impact/` was modified by this
phase — confirmed via `git status`/`git diff` scoping before commit.
The new `historical_memory` package is purely additive.

- **Track 119 executable schemas** — unmodified; the builder consumes
  and produces the already-frozen `historical_memory_snapshot.schema.json`
  (119Q, `119Q.1.0-json-schema`) without any schema change.
- **Track 120 Repository Knowledge Snapshot** — unmodified; consumed
  exclusively through the Track 121 Query Layer for structural
  cross-reference only, never as a temporal source (127D §2.1).
- **Track 121 Query Layer** — unmodified; the builder's only access
  path into Repository Intelligence content.
- **Track 122 Advisory Context Builder** — unmodified; not consumed by
  this builder.
- **Track 123 Change Impact Builder** — unmodified; not consumed by
  this builder.
- **Track 126 Dependency Knowledge Graph** — unmodified; not consumed
  by this builder in v1 (127D §5.1 scoped this as optional; not
  exercised in this prototype).

## 11. Confirmations

- **No historical reasoning implemented.** No module in
  `historical_memory/` walks, paths, or recursively explores the
  assembled snapshot beyond the fixed, rule-based construction
  described in Section 3; a dedicated test
  (`test_no_reasoning_module_exists`) confirms no `historical_reasoning`
  module exists.
- **No inference implemented.** Every event/claim/relationship is a
  direct, traceable translation of already-declared task-contract
  content or git history via fixed rules (Section 3, stages 5-7); a
  dedicated test confirms non-convention-titled tasks are classified
  `unknown`, never guessed (`test_non_convention_title_classified_
  unknown_not_guessed`).
- **No recommendations implemented.** No module produces a
  recommendation, priority, or suggested action of any kind.
- **No timeline engine implemented.** A dedicated test
  (`test_no_timeline_engine_module_exists`) confirms no
  `timeline_engine` module exists.
- **No runtime behavior changed.** `historical_builder.py` and
  `historical_validation.py` import no `subprocess`/shell-execution
  module, confirmed by dedicated AST-based import inspection tests
  (following this codebase's established AST-over-substring-check
  convention). `git_source.py` is the sole, explicitly-scoped module
  permitted to invoke `git` as a subprocess, mirroring the precedent
  `source_inventory.py` already established for Track 120.
- **Execution remains unavailable.** Independently re-confirmed via
  `pcae runtime inspect` (Section 13 below).

## 12. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking.

Not inherited defects (126G and 126G.1 are closed, verified repairs;
not reintroduced as open issues by this phase).

## 13. Governance Results

- `pcae health`: healthy, git status clean at inspection time.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean, no inconsistencies detected.
- `pcae push check`: clean.
- `pcae runtime inspect`: `Observed` / `observe` / execution
  unavailable / zero runtime plugins / registry empty / Permission
  Broker `execution_unavailable`.
- `pcae notify status` (after sourcing
  `~/.config/pcae/telegram.env`): Telegram configured, enabled, and
  ready for outbound delivery.

## 14. Strict Non-Goals Confirmation

This phase does not implement: historical reasoning; causal reasoning;
recommendations; Decision Evaluation; predictive history; execution
planning; execution capability; AI interpretation; graph traversal;
runtime plugins. No schema file was changed.

## 15. Deferred Capabilities

Explicitly deferred, unchanged from 127B/127D: historical reasoning;
causal reasoning; timeline interpretation; recommendations; Decision
Evaluation; execution planning; execution capability; AI
interpretation; predictive history; graph traversal.

## 16. Conclusion

Phase 127E implements the first deterministic, read-only Historical
Memory Builder exactly as scoped by 127A-127D, verified end-to-end
against this repository's own real git history and 850 real task
contracts (not synthetic fixtures alone), and confirmed
byte-deterministic across repeated runs. A genuine defect discovered
during implementation verification — `git log --follow`'s content-
similarity rename heuristic falsely collapsing distinct task contracts
onto the same commit due to shared template boilerplate — was
identified, root-caused, and fixed before this phase's own
finalization, improving commit-resolution accuracy from 237 to 806
distinct commits across 850 records. Both 127C findings (the
`historical_reference`/`reference_type` naming gap and the
null-boundary time-reference ordering rule) were resolved exactly as
127D specified. No reasoning, inference, recommendation, or execution
capability was introduced. Runtime remains
`Observed`/`observe`/execution-unavailable.

Recommended next phase: 127F — Historical Memory Verification.
