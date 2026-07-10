# Phase 128F - Historical Memory Review & Hardening Verification

## 1. Method

This phase independently re-verifies 128E's implementation. It does
not trust 128E's implementation, comments, documentation, previous
tests, or previous reports. Every check below was re-derived directly
from: a git-diff re-read of the actual committed change, freshly
generated Historical Memory artifacts (not reused from any prior
phase's scratch output), the frozen 119Q schema and its shared
`$defs`, checksums taken before/after generation, and direct CLI
probing.

**This verification found one genuine, pre-existing defect** (Section
3) that no prior phase (127E, 127F, 128A-128E) had caught, despite
each independently claiming "zero schema errors." It was repaired
under this phase's explicit repair authorization, and the complete
verification was re-run against the repaired code (Sections 4-11 all
reflect the post-repair state; Section 3 documents the pre-repair
finding and the repair itself).

## 2. Verification of Both 128E Hardening Items

Re-read `git show a29c1478 -- .../historical_builder.py` directly
(not 128E's own documentation summarizing it):

- **Identifier-order clarification comment exists**: confirmed, 11
  lines, immediately above `"historical_events": sorted(events,
  key=lambda e: e["event_id"]),`. Independently confirmed the comment
  text contains all four required statements: (1) "Chronological
  ordering is already performed earlier, during construction"; (2)
  "This final, separate sort is intentionally identifier-based"; (3)
  "it exists to guarantee deterministic, stable, diffable
  serialization"; (4) "not to express historical/chronological
  ordering. Do not read this as chronological ordering."
- **Executable logic unchanged**: independently re-derived via
  programmatic diff analysis (not visual inspection alone) - every
  `+` line in the 128E commit's diff for `historical_builder.py`
  begins with `#` after stripping leading whitespace; 0 lines were
  removed. 11 added, 0 removed, 0 non-comment additions.
- **`historical_generator.py` explicitly documented**: confirmed
  present in `docs/PHASE_128_HISTORICAL_MEMORY_REVIEW_HARDENING_
  IMPLEMENTATION.md` (128E's own document), naming the module by name
  alongside the other four package files.
- **Frozen contracts remain unchanged**: `git log --oneline f62fa1d3..
  -- docs/PHASE_127_HISTORICAL_MEMORY_CONTRACT_FREEZE.md docs/PHASE_
  128_HISTORICAL_MEMORY_REVIEW_HARDENING_CONTRACT_FREEZE.md schemas/
  repository_intelligence/artifacts/historical_memory_snapshot.schema
  .json` returns zero commits - confirmed no commit since 128B's own
  freeze (inclusive) touches 127B, 128B, or the 119Q schema file.

**Verdict: CONFIRMED.** Both 128E items are exactly what 128D planned.

## 3. Independent Schema Verification - Defect Found and Repaired

No `jsonschema` library is available in this environment (confirmed:
`ModuleNotFoundError` in both system Python and the project's own
`.venv`), consistent with `tests/test_phase_127e_historical_memory_
prototype.py`'s own `TestSchemaRequiredFieldConformance` note. Rather
than trust that class's existing (partial) coverage, this phase wrote
an independent, dependency-free recursive JSON Schema structural
validator (`$ref`/`$defs`/cross-file-`$ref`/`required`/`type`/`enum`/
`items`/`const`/`minItems`) and validated a freshly generated artifact
against the actual frozen `historical_memory_snapshot.schema.json`
file directly - not against any prior phase's claim about it.

**Result on the pre-repair artifact: 903 schema violations**, all
one of exactly three distinct patterns:

1. `historical_claims[N].claim_type: 'phase_summary' not in enum
   [...]` (859 occurrences - every single generated claim). The
   frozen 119Q `claim_type` enum (`evolution`, `lineage`,
   `introduction`, `modification`, `repair`, `hardening`, `release`,
   `decision`, `supersession`, `correction`, `unknown`) has never
   included `"phase_summary"`.
2. `repair_hardening_history[N].phase_reference: expected type
   ['object'], got str` (42 occurrences - every repair/hardening
   record). The frozen schema's `phase_reference` field is a
   `source_locator` object (`{locator_type, locator_value}`), not a
   plain string.
3. `unknowns_gaps[N].affected_period: expected type ['object'], got
   str` (2 occurrences). The frozen schema's `affected_period` field
   is a `historical_period` object, not a plain string.

**Why the existing implementation was insufficient**: `git log -S`
traced all three defects to `1bfbd69d` (Phase 127E: Historical Memory
Prototype) - pre-existing since the original implementation, not
introduced by 128E (128E's own diff is comment-only; Section 2
independently re-confirms this). Every subsequent phase (127F, 128A,
128B, 128C, 128D, 128E) that claimed "zero schema errors" or
equivalent was correct only relative to `TestSchemaRequiredFieldConformance`'s
actual coverage, which checks top-level required fields, `historical_
event` required fields, and `phase_lineage_record` required fields -
**never** `historical_claim`'s `claim_type` enum, `repair_hardening_
record`'s `phase_reference` type, or `unknown_gap`'s `affected_period`
type. No prior phase's "12 fail-closed categories" or "no taxonomy
gap" verification exercised these three specific field/type
combinations either - both were correct claims about what they
actually checked, but neither checked full recursive schema
conformance, which is exactly the gap this phase's from-scratch
validator was written to close.

**Repair** (`src/pcae/repository_intelligence/historical_memory/
historical_builder.py`, three call sites, all comment-documented at
the change site):

1. `claim_type: "phase_summary"` -> `claim_type: "evolution"` (the
   closest frozen enum value for a claim describing a phase reaching
   completion status; matches 127A/127B's own "Historical Memory
   records repository evolution" framing).
2. `phase_reference: task_id` -> `phase_reference: source_locator
   ("task_id", task_id)`, reusing the existing `pcae.repository_
   intelligence.attribution.source_locator()` helper already used
   throughout the file for identical shapes elsewhere - not a new
   helper, not hand-rolled. The one consuming call site
   (`_build_repair_relationships`, comparing `record["phase_
   reference"]` against a task ID) was updated in the same commit to
   read `["locator_value"]`, preserving identical comparison behavior.
3. `affected_period: "graph-wide"` (two occurrences) -> a new
   `_graph_wide_period()` helper returning a proper `historical_
   period`-shaped object (`period_start`/`period_end` honestly `None`,
   matching the schema's own `["string","null"]` type - not a
   fabricated timestamp).

**Diff scope**: `git diff --stat` shows 43 insertions, 5 deletions,
entirely within `historical_builder.py` - one file, five precisely
targeted edits, each with an inline comment explaining what was wrong
and why. No schema file, test file, or other source file changed. No
`claim_type`/`phase_reference`/`affected_period` literal string
appears anywhere in `tests/**`, so zero test-code changes were
required.

**Result on the repaired artifact: 0 schema violations** (re-run of
the identical independent validator against a newly generated
artifact from the repaired code).

**Existing test suite re-run against the repair**: `tests/test_phase_
127e_historical_memory_prototype.py`, all 50 tests - pass, unchanged.

## 4. Fresh Artifact Generation

Generated a fresh Repository Knowledge Snapshot from the current
repository at commit `68df1c7a` (the pre-128F HEAD) via `pcae
repository-intelligence snapshot generate`, then a fresh Historical
Memory Snapshot from that fresh RKS snapshot via `pcae repository-
intelligence historical-memory generate` - neither artifact reused
from any prior phase's scratch output. Result (repaired code): 859
`historical_events`, 859 `historical_claims`, 859 `phase_lineage`
records, 2 `release_lineage` records, 42 `repair_hardening_history`
records, 870 `historical_relationships`, 1676 `historical_sources`, 2
`unknowns_gaps`.

## 5. Independent Deterministic Verification

Generated two independent Historical Memory artifacts from the same
fresh RKS snapshot input, both against the repaired code, in two
separate process invocations. Compared programmatically (recursive
dict diff, not visual inspection).

**Result: byte-identical**, 0 unexpected differences; the only 2
differences found are exactly the two already-approved
non-load-bearing timestamp fields (`envelope.generated_at_utc`,
`snapshot_identity.snapshot_created_at_utc`). Re-ran the identical
comparison against the pre-repair code as well (before applying
Section 3's fix), confirming determinism held before the repair too -
the repair fixed schema conformance, not determinism, which was never
in question.

## 6. Independent Schema Verification

Section 3. **0 schema violations** against the frozen 119Q schema
(including all cross-file `$ref`s into `schemas/repository_
intelligence/shared/*.schema.json`) for the repaired artifact.

## 7. Independent Read-Only Verification

Checksummed, immediately before and immediately after a fresh
generation run (repaired code):

- **git HEAD**: `68df1c7a...` unchanged (`git rev-parse HEAD`
  identical before/after).
- **`tasks/done/*.md`**: SHA-256 of the concatenated, sorted
  per-file SHA-256 list identical before/after (488757eb...).
- **Repository Knowledge Snapshot directory**: `.pcae/repository-
  intelligence/snapshots/` listing checksum identical before/after.
- **Dependency Knowledge Graph**: directory `.pcae/repository-
  intelligence/dependency-graph/` confirmed absent both before and
  after (Historical Memory does not consume or create DKG content -
  128C already confirmed this; re-confirmed here directly).
- **`historical_builder.py` itself**: SHA-256 identical before/after
  a generation run (confirms the generator does not self-modify its
  own source, an orthogonal but relevant read-only check).

**Verdict: CONFIRMED.** No mutation of the repository, git history,
Repository Knowledge Snapshot, Dependency Knowledge Graph, or task
contracts.

## 8. Independent Serialization Verification

- **Compatibility preserved**: `executable_schema_version` remains
  `119Q.1.0-json-schema` in the repaired artifact (schema file
  untouched, Section 2).
- **Identifier ordering unchanged**: independently re-verified for
  all six sortable collections (`historical_events`, `historical_
  claims`, `phase_lineage`, `release_lineage`, `repair_hardening_
  history`, `historical_relationships`) that each collection's own
  identifier field is in ascending sorted order in the repaired
  artifact - matching exactly what 128E's new comment (Section 2)
  describes.
- **No output format change**: JSON remains compact (no pretty-print
  indentation) via `serialize_deterministic_json`, matching prior
  behavior; top-level key set unchanged from the pre-128E/pre-repair
  artifact shape (only three field *values*' types/contents changed,
  per Section 3's repair - the schema-defined shape those fields
  should have always had).

**Verdict: CONFIRMED.**

## 9. Independent Temporal Verification

- **Chronological processing preserved**: `_sort_key`
  (`historical_builder.py`, unchanged by both 128E and this phase's
  repair - confirmed via diff, Section 2) still governs construction
  order.
- **Persisted ordering intentionally identifier-based**: Section 8.
- **No inferred chronology introduced**: the repair (Section 3) did
  not touch any date/time field - `period_start`/`period_end` in the
  new `_graph_wide_period()` helper are honestly `None`, never a
  fabricated or inferred timestamp, matching the schema's own
  `["string","null"]` type contract.

**Verdict: CONFIRMED.**

## 10. Independent Evidence Verification

On the repaired, freshly generated artifact: 0 of 859
`historical_claims` are missing `source_attribution`; 0 are missing
`limitations`; `boundary_disclosures`, `disclaimers`, and `snapshot_
limitations` are all present at the top level. Attribution content
itself (which specific task-contract/commit citation each record
carries) is unchanged by the repair - only the `claim_type`/`phase_
reference`/`affected_period` field *types*/*values* changed; no
`source_attribution` construction code was touched (confirmed via
diff, Section 2/3).

**Verdict: CONFIRMED.** Attribution, evidence, limitation propagation,
and boundary disclosure are all preserved.

## 11. Fail-Closed Verification

Re-ran the existing 12 fail-closed test categories (`TestFailClosedBehavior`,
9 tests; `TestValidation`'s 3 fail-closed-relevant tests) directly
against the repaired code: **14 passed** (12 fail-closed categories +
2 baseline valid-input-passes tests), 0 failed. Additionally, independently
probed a fail-closed condition not covered by re-running existing
tests: invoked `pcae repository-intelligence historical-memory
generate --snapshot <corrupted-json>` directly against a hand-crafted
invalid input file (`{"not": "a valid snapshot"}`) - result: `Error:
snapshot_identity is missing or invalid`, exit code 1. Confirms
fail-closed behavior holds under direct CLI probing, not merely
inside the existing test harness.

**Verdict: CONFIRMED.**

## 12. Regression Results

Full regression suites re-run against the repaired code (334 tests):

- **Historical Memory** (`tests/test_phase_127e_historical_memory_prototype.py`)
  - 50 passed.
- **Dependency Knowledge Graph** (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`)
  - passed, confirming continued independence.
- **Change Impact** (`tests/test_phase_123e_repository_intelligence_change_impact.py`,
  `tests/test_phase_124e_repository_intelligence_hardening.py`) - passed.
- **Advisory Context** (`tests/test_advisory_context_package.py`,
  `tests/test_advisory_context_package_verification_115y.py`,
  `tests/test_phase_115w_advisory_context_package_contract.py`) -
  passed.
- **Query Layer** (`tests/test_phase_121e_repository_intelligence_query.py`)
  - passed.
- **Repository Knowledge Snapshot** (`tests/test_phase_120e_repository_knowledge_snapshot.py`)
  - passed.

**Result: 334 passed, 0 failed** (76.97s).

## 13. fast_green Results

`python3 -m pytest -m "fast_green" -n auto` re-run against the
repaired code: **4390 passed, 0 failed** (70.69s).

## 14. compileall Results

`python3 -m compileall -q src/` re-run against the repaired code:
**clean, exit code 0**.

## 15. Governance Validation

`pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
check` / `pcae runtime inspect` / `pcae notify status` all re-run
after the repair. Runtime posture unchanged throughout this entire
phase: `Observed` / `observe` / execution `unavailable`, zero
registered runtime plugins, Permission Broker `execution_unavailable`.

## 16. Confirmations

- **No runtime behavior changed.** Every command run by this phase
  (schema validation, artifact generation, checksum comparison, CLI
  fail-closed probing, regression/fast_green/compileall) is read-only
  or writes only to scratch/output directories outside the governed
  repository state; the one source repair (Section 3) is a data-value
  correction inside an existing, already-governed generator function,
  not a runtime-capability change.
- **Execution remains unavailable.** Confirmed via `pcae runtime
  inspect` (Section 15).
- **Historical Memory hardening complete.** Both 128E items verified
  correct (Section 2); the one genuine pre-existing defect this
  phase's independent verification uncovered (Section 3) is repaired
  and the complete verification was re-run clean against the repair
  (Sections 4-15). No further known defects remain in scope for this
  hardening chapter.

## 17. Conclusion

128F independently re-verified 128E's two approved hardening items
(both confirmed exactly as planned) and, per this phase's own
"do not trust previous tests" mandate, wrote and ran an independent
recursive schema validator against a freshly generated artifact rather
than trusting any prior phase's "zero schema errors" claim. This
independent check found a genuine, pre-existing defect (three related
schema-conformance violations, present since Phase 127E, never
detected by any prior phase's narrower test coverage) and repaired it
with three minimal, precisely targeted, comment-documented changes,
then re-ran the complete verification (determinism, schema, read-only,
serialization, temporal, evidence, fail-closed, regression, fast_green,
compileall, governance) clean against the repair.

Historical Memory remains deterministic, read-only, and observe-only.
The Historical Memory hardening chapter (128A-128F) is complete.

Recommended next phase: 129A - Historical Memory Chapter Review & Next
Direction Architecture.
