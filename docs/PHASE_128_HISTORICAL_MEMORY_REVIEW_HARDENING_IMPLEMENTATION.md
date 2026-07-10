# Phase 128E - Historical Memory Review & Hardening Implementation

## 1. Purpose

Implements exactly the two bounded, non-behavioral hardening items
128D approved. Nothing else. No functional behavior change, no
schema change, no public API change, no serialization change.

## 2. Implementation Scope

The Historical Memory implementation scope, for hardening-chapter
purposes (128A-128F), consists of the following five modules under
`src/pcae/repository_intelligence/historical_memory/`:

- `git_source.py` - the sole module permitted to invoke `git`
  (subprocess-based, read-only plumbing).
- `historical_builder.py` - constructs historical events, claims,
  lineage, transitions, and relationships from task-contract and git
  source data.
- **`historical_generator.py`** - the package's own documented
  external entry point ("the only intended external entry point into
  the historical_memory package", per its own module docstring),
  wiring together `historical_builder`, `historical_validation`, and
  `persistence`. Named explicitly here to close 128C's Finding 2: 128B
  §3's scope list did not separately name this module, though its
  role was always implicitly covered by that list's "CLI
  integration"/"Serialization" items. This document is the forward
  fix - 128B's own frozen text is not reopened (128B §2's own
  amendment-authority rule; see Section 4 below).
- `historical_validation.py` - validates a constructed snapshot
  (identifier uniqueness, deterministic ordering, provenance/
  limitation/boundary completeness, relationship-endpoint integrity)
  before persistence.
- `persistence.py` - the sole module permitted to write the generated
  artifact, reusing `serialize_deterministic_json` unchanged.

No module was added, removed, or renamed. This section documents
existing scope precisely; it does not expand it.

## 3. Implemented Change 1 - Ordering Clarification Comment

**File**: `src/pcae/repository_intelligence/historical_memory/historical_builder.py`

**Change**: one comment block (11 lines) added immediately above the
`"historical_events": sorted(events, key=lambda e: e["event_id"]),`
line inside `build_historical_content`'s return-dict construction,
where every persisted collection (`historical_events`,
`historical_claims`, `phase_lineage`, `release_lineage`,
`repair_hardening_history`, `historical_relationships`) is sorted by
its own record's identifier field immediately before being placed into
the snapshot.

**What the comment states** (resolving 128C's Finding 1 exactly as
128D Section 2.1 specified):

- chronological processing is already performed earlier, during
  construction (`_sort_key`, used to order task-derived records
  before events/claims/etc. are built from them) - this is a distinct,
  earlier stage from the sort documented here;
- the persisted artifact ordering documented here is intentionally
  identifier-based, not time-based;
- identifier ordering exists specifically to guarantee deterministic,
  stable, diffable serialization - matching exactly what
  `historical_validation.py`'s `_validate_deterministic_ordering`
  independently checks;
- this is explicitly **not** chronological ordering, and must not be
  read as such.

**Verification the change is comment-only**: `git diff` for this file
shows exactly 11 added lines, every one beginning with `#` (a Python
comment), zero lines removed, zero non-comment lines added. No sort
key, no comparison function, no field name, and no code path changed.

## 4. Implemented Change 2 - Scope Documentation

**File**: this document (`docs/PHASE_128_HISTORICAL_MEMORY_REVIEW
_HARDENING_IMPLEMENTATION.md`), Section 2 above.

Resolves 128C's Finding 2 by explicitly naming `historical_generator
.py` within the Historical Memory implementation scope, going forward,
without modifying 128B's own frozen text. 128B §2 states: "No later
phase may silently reinterpret this contract as authorizing capability
expansion... without its own separate, explicitly scoped governed
contract-amendment phase." This document does not reinterpret or edit
128B's text - it is a new, separate, explicitly scoped document (128E,
exactly as 128D Section 4 planned) that supplies the missing naming
completeness for every future reader from this point forward. 128B's
own scope list (§3) remains unedited and historically accurate to what
it said at the time it was frozen.

No historical contract was amended. No architectural intent was
altered.

## 5. Confirmation: Comment/Documentation Only

The complete diff for this phase touches:

- `src/pcae/repository_intelligence/historical_memory/historical_builder.py`
  - 11 comment lines added, 0 removed, 0 executable-code lines
  changed;
- this document (new file);
- `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, and this
  phase's own task contract (standard governed-lifecycle bookkeeping
  files, unrelated to Historical Memory implementation).

No file under `schemas/**` changed. No file under `tests/**` changed.
No public function signature, CLI option, or serialized field changed.

## 6. Acceptance Criteria Demonstration

Each criterion 128D Section 5 required, demonstrated directly:

- **Zero functional behavior change** - `git diff` on
  `historical_builder.py` (Section 3) shows comment-only lines; no
  other source file changed.
- **Deterministic output unchanged** - Section 7's byte-comparison
  demonstrates this directly against real repository data.
- **Serialization unchanged** - `serialize_deterministic_json` reuse
  in `persistence.py` untouched; `executable_schema_version` remains
  `119Q.1.0-json-schema` (schema file untouched, confirmed via `git
  diff --stat` showing no `schemas/**` entry).
- **Evidence unchanged** - `source_attribution` construction logic
  (`historical_builder.py:344-381`) is untouched code; Section 7's
  byte comparison confirms identical attribution content in generated
  output.
- **Attribution unchanged** - same basis as evidence, above.
- **Temporal semantics unchanged** - both the processing-order
  `_sort_key` function and the persisted-order identifier sorts are
  byte-for-byte unchanged code; the new comment describes existing
  behavior, it does not alter it.
- **Read-only guarantees unchanged** - no new file write, no new git
  mutation, no new subprocess call; the existing AST-based
  no-subprocess-import tests (`test_builder_module_has_no_execution_
  related_imports`, `test_validation_module_has_no_execution_related_
  imports`) re-run unchanged in Section 8 and still pass, confirming
  no import was added.
- **CLI compatibility unchanged** - `src/pcae/cli.py` was not touched
  by this phase (confirmed via `git diff --stat`); `historical-memory
  generate`'s `--snapshot`/`--output`/`--pretty`/`--json` option
  surface is unchanged.
- **Governance compatibility unchanged** - Section 9.

## 7. Deterministic Output Verification (Real Data)

Generated a real Historical Memory snapshot from the actual repository
state twice against the same real Repository Knowledge Snapshot input
(`.pcae/repository-intelligence/snapshots/20260708T231402432259Z.json`)
- once against the pre-change code (comment removed via `git stash`),
once against the post-change code (comment restored via `git stash
pop`, diff re-confirmed as the same 11 comment-only lines) - and
compared output programmatically (Python dict equality after stripping
only the two approved timestamp fields).

Result: **byte-identical** except the two already-approved
non-load-bearing timestamp fields (`envelope.generated_at_utc`,
`snapshot_identity.snapshot_created_at_utc`). Both runs produced 858
`historical_events`, 858 `historical_claims`, 858 `phase_lineage`
records, 2 `release_lineage` records, 41 `repair_hardening_history`
records, and 869 `historical_relationships`, from the identical
repository commit (`0eedb51d`). Every `historical_event`,
`historical_claim`, `phase_lineage`, `release_lineage`,
`repair_hardening_history`, and `historical_relationship` record -
including every `source_attribution`, `verification_state`, and
`limitations` field - is identical between the two runs, confirming
the comment addition has zero effect on generated output.

## 8. Regression Results

Full regression suites run against the post-change code (334 tests,
all passing):

- **Historical Memory** (`tests/test_phase_127e_historical_memory_prototype.py`)
  - pass, identical to baseline.
- **Dependency Knowledge Graph** (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`)
  - pass, confirming continued independence from Historical Memory.
- **Change Impact** (`tests/test_phase_123e_repository_intelligence_change_impact.py`,
  `tests/test_phase_124e_repository_intelligence_hardening.py`) - pass,
  confirming continued independence.
- **Advisory Context** (`tests/test_advisory_context_package.py`,
  `tests/test_advisory_context_package_verification_115y.py`,
  `tests/test_phase_115w_advisory_context_package_contract.py`) -
  pass, confirming continued independence.
- **Query Layer** (`tests/test_phase_121e_repository_intelligence_query.py`)
  - pass, confirming the comment-only change did not alter Historical
  Memory's `execute_query()`/`load_snapshot()` usage.
- **Repository Knowledge Snapshot** (`tests/test_phase_120e_repository_knowledge_snapshot.py`)
  - pass, confirming Historical Memory's upstream input path is
  untouched.

Command: `python3 -m pytest tests/test_phase_127e_historical_memory_prototype.py
tests/test_phase_126e_dependency_knowledge_graph_prototype.py
tests/test_phase_123e_repository_intelligence_change_impact.py
tests/test_phase_124e_repository_intelligence_hardening.py
tests/test_advisory_context_package.py
tests/test_advisory_context_package_verification_115y.py
tests/test_phase_115w_advisory_context_package_contract.py
tests/test_phase_121e_repository_intelligence_query.py
tests/test_phase_120e_repository_knowledge_snapshot.py -q`

Result: **334 passed, 0 failed** (77.07s).

## 9. fast_green / compileall / Governance Validation

- `fast_green` (`python3 -m pytest -m "fast_green" -n auto`) - **4390
  passed, 0 failed** (70.75s), full suite re-run against the
  post-change tree.
- `compileall` (`python3 -m compileall -q src/`) - **clean, exit code
  0**, confirming no syntax error was introduced by the comment
  addition.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae
  push check` / `pcae runtime inspect` / `pcae notify status` - all
  re-run after the change; runtime posture (`Observed`/`observe`/
  execution-`unavailable`, zero registered runtime plugins) confirmed
  unchanged.

## 10. Strict Non-Goals Confirmed

Not introduced by this phase: historical reasoning; causal reasoning;
inference; recommendations; Decision Evaluation; graph traversal;
execution planning; execution capability; runtime plugins; schema
changes; public API changes; serialization changes. Confirmed by the
diff itself (Section 5) - there is no code path in an 11-line comment
addition and one new documentation file capable of introducing any of
the above.

## 11. Relationship to 128F

128F - Historical Memory Review & Hardening Verification - must
independently re-verify every claim in this document, not merely
re-run and trust this phase's own reported results, per 128D Section
7's verification-strategy requirement: independently re-read the
actual diff, independently regenerate a real snapshot before trusting
any byte-identical claim, independently re-run every regression suite
and governance check named in Section 8-9.

## 12. Acceptance

128E is complete when both approved changes (Sections 3-4) are made
exactly as 128D scoped them, every acceptance criterion (Section 6) is
demonstrated with concrete evidence (Sections 7-9), all regressions
and fast_green/compileall pass, governance validation confirms
unchanged posture, no implementation beyond the two approved items
occurred, runtime remains `Observed`/`observe`/execution-unavailable,
and the recommended next phase is 128F - Historical Memory Review &
Hardening Verification.
