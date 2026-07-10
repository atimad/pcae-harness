# Phase 128D - Historical Memory Review & Hardening Implementation Plan

## 1. Purpose

This phase produces the definitive, bounded implementation plan for
128E. It defines *what* 128E may change and *why*, precisely enough
that 128E requires no further scoping judgment calls of its own. This
phase performs no implementation itself: no schema, source, or test
file is touched by 128D.

128C found the Historical Memory hardening chapter (128A-128C) to be
internally consistent and source-accurate, with exactly two
non-blocking documentation-precision findings. 128D's entire purpose
is narrower than "harden Historical Memory broadly" - it is to plan
the smallest correct implementation that resolves those two specific
findings, plus define the review pipeline that confirms nothing else
needs to change (128C already confirmed every other category; 128E
must not treat that confirmation as an invitation to look for more
work).

## 2. Implementation Strategy

128E's implementation surface is **deliberately minimal**, bounded to
exactly two source-level changes, both comment/docstring-only, zero
behavioral effect:

1. **Finding 1 resolution** - a clarifying code comment at the final
   array-assembly site in `historical_builder.py`
   (`build_historical_snapshot`'s return dict construction, currently
   lines ~912-921), explicitly distinguishing the two-stage ordering
   Historical Memory actually uses:
   - **Processing order** (the existing, already-correctly-commented
     `_sort_key` function, lines ~332-340): chronological, by
     `commit_author_date_utc`, null-boundary records last, tie-broken
     by `task_id`. This governs the order records are *built* in, not
     the order they are *persisted* in.
   - **Persisted/validated order** (currently uncommented): every
     output collection (`historical_events`, `historical_claims`,
     `phase_lineage`, `release_lineage`, `repair_hardening_history`,
     `historical_relationships`) is sorted by its own record's
     identifier field immediately before being written into the
     snapshot dict - lexicographic string order, not time order. This
     is the order `historical_validation.py`'s
     `_validate_deterministic_ordering` actually checks and enforces.

   128E adds one comment block immediately above the six `sorted(...,
   key=lambda ...)` calls, stating plainly that persisted-array order
   is identifier-based (not time-based), that this is intentional
   (stable, diffable, byte-reproducible output independent of any
   record's own timestamp field), and cross-referencing this plan and
   128C's Finding 1 by phase ID. **No sort key, no comparison
   function, no field, and no output byte changes.** This is a
   comment-only addition; `git diff` against this change touches only
   comment lines.

2. **Finding 2 resolution** - `historical_generator.py`'s own module
   docstring already accurately self-describes its role ("the only
   intended external entry point into the historical_memory
   package") and requires no change. The gap 128C found was in 128B
   §3's scope *list*, which is a already-frozen prior contract outside
   128D-128F's amendment authority (128B §2: "no later phase may
   silently reinterpret this contract... without its own separate,
   explicitly scoped governed contract-amendment phase"). 128E does
   not reopen 128B's own text. Instead, Finding 2 is resolved entirely
   within Track 128's own forward documentation: 128E's own
   implementation report (and any future Track 128 document that
   restates hardening scope) explicitly names all five package files
   -  `git_source.py`, `historical_builder.py`,
   `historical_generator.py`, `historical_validation.py`,
   `persistence.py` - by name, closing the naming gap going forward
   without editing frozen prior text. **No source file changes; a
   pure forward-documentation-completeness fix.**

No other Historical Memory source file, schema, or test is touched.
128C's twelve verification categories reached CONFIRMED for
everything except these two wording-precision items - 128E's pipeline
(Section 3) re-walks those categories only to *confirm* nothing
regressed while these two narrow changes were made, not to search for
new work.

## 3. Implementation Pipeline

Ten steps, in sequence, each gated on the previous step's success:

1. **Terminology refinement** - draft the exact clarifying comment
   text for Finding 1 (Section 2.1); confirm it uses the same
   vocabulary as 127B/128B/128C ("processing order",
   "persisted/validated order", "declared time reference",
   "identifier") so the comment reads as a precision addition, not a
   competing description.
2. **Documentation refinement** - confirm 128E's own implementation
   report will explicitly name all five package files (Finding 2,
   Section 2.2); no other document is edited.
3. **Implementation consistency review** - re-confirm (not
   re-discover) that `persistence.py` still owns all writing,
   `historical_builder.py` never writes, and the Query Layer remains
   the exclusive Repository Intelligence access path - restates
   128C §6/§10, expected to reach the identical CONFIRMED verdict
   since no behavioral code changed.
4. **Persistence review** - re-confirm `DEFAULT_OUTPUT_SUBDIR` values
   for RKS/DKG/Historical Memory are unchanged (the `graphs/`-vs-
   `snapshots/` finding remains carried-forward debt, Section 7, not
   touched by 128E).
5. **Serialization review** - re-confirm `serialize_deterministic_json`
   reuse is unchanged and that the comment addition (Section 2.1)
   does not alter serialized byte output - verified by a direct
   before/after byte comparison of a real generated snapshot in 128E's
   own validation.
6. **Deterministic behavior review** - re-run the existing determinism
   regression tests (`test_equivalent_snapshot_produces_equivalent_
   graph`-equivalent Historical Memory tests, and the two-independent-
   run byte-equality checks 127E/127F already established) to confirm
   byte-identical output before and after the comment addition.
7. **CLI consistency review** - re-confirm `historical-memory
   generate`'s option surface (`--snapshot`, `--output`, `--pretty`,
   `--json`) is unchanged; 128E adds no CLI option (Finding 2's
   resolution is documentation-only, not the DKG-cross-reference CLI
   expansion 128A/128B/128C all separately classified as unscoped
   debt, Section 7).
8. **Regression validation** - Section 5.
9. **Governance validation** - `pcae health`, `pcae check`, `pcae
   doctor task-memory`, `pcae push check`, `pcae runtime inspect`
   after the change, confirming observe-only/execution-unavailable
   posture is unchanged (a comment-only change cannot itself affect
   runtime posture, but this step re-confirms it rather than assuming
   it).
10. **Verification readiness** - confirm every 128F verification
    objective (Section 6) has a concrete, checkable artifact to
    verify against (the specific comment diff, the specific
    documentation-naming addition, and the regression/governance
    results from steps 5-9) before 128E is declared complete.

## 4. Resolution Plan for 128C's Two Findings

Restated from Section 2 for direct traceability:

| Finding | Resolution mechanism | Behavior change | Files touched |
| --- | --- | --- | --- |
| 1 - temporal vs. persisted ordering wording | One clarifying comment block above the six final-array `sorted()` calls in `historical_builder.py` | None (comment-only) | `historical_builder.py` |
| 2 - `historical_generator.py` scope naming | 128E's own implementation report explicitly names all five package files | None (documentation-only) | 128E's own report; no source file |

Both resolutions are terminology/documentation precision fixes only,
matching 128B §4's "terminology consistency"/"documentation
consistency" hardening-responsibility categories exactly - neither
expands functionality, neither is a schema change, and neither alters
what any generated artifact contains.

**Explicitly out of scope for 128E**: amending 127B §6's or 128B §8's
own contract text. Both remain frozen governance artifacts; a future,
separately scoped contract-amendment phase - not 128E - would be the
correct vehicle if their prose itself is ever judged to need
rewording. 128E resolves the *practical* confusion the imprecise
wording could cause (a future reader misreading the contract as
requiring literal chronological persisted order) by adding the missing
clarity at the point closest to where a future reader would actually
look - the code itself - without touching the frozen contract prose.

## 5. Acceptance Criteria for 128E

128E is acceptable only if every one of the following holds, each
independently checkable:

- **No functional behavior change** - `git diff` for 128E's commit
  touches only comment lines in `historical_builder.py` and 128E's
  own documentation; zero lines of executable code change.
- **Deterministic output preserved** - a freshly generated Historical
  Memory snapshot from the same real repository state, taken
  immediately before and immediately after 128E's change, is
  byte-identical except the two already-approved non-load-bearing
  timestamp fields (`envelope.generated_at_utc`,
  `snapshot_identity.snapshot_created_at_utc`).
- **Evidence preserved** - every record's `source_attribution` is
  byte-identical before/after (a direct consequence of zero code
  change, verified rather than assumed).
- **Attribution preserved** - same as above.
- **Temporal semantics preserved** - the processing-order sort
  (`_sort_key`) and persisted-order sort (identifier-based) both
  produce identical output before/after; the new comment describes
  existing behavior, it does not redefine it.
- **Read-only guarantees preserved** - no new file write, no new git
  mutation path, no new subprocess call introduced (verified via the
  same AST-based no-subprocess-import tests 127E already established,
  re-run unchanged).
- **Serialization compatibility preserved** - `executable_schema_
  version` remains `119Q.1.0-json-schema`; `serialize_deterministic_
  json` reuse unchanged; output byte-for-byte identical (Section 3
  step 5).
- **CLI compatibility preserved** - `historical-memory generate`'s
  option surface is unchanged; no new flag, no removed flag, no
  changed default.
- **Governance compatibility preserved** - `pcae health`/`check`/
  `doctor task-memory`/`push check`/`runtime inspect` all pass
  identically before and after; runtime remains `Observed`/`observe`/
  execution-`unavailable` throughout.

Any 128E change that fails even one of these criteria is out of
128E's authorized scope and must be reverted, not merged as
"hardening."

## 6. Regression Strategy

128E must run, and 128F must independently re-verify, regression
suites against every subsystem Historical Memory has a real or
potential boundary with:

- **Historical Memory** (Track 127) - the full existing prototype
  test suite (`tests/test_phase_127e_historical_memory_prototype.py`,
  50 tests) plus any 127F-added regression coverage - must pass
  unchanged (same pass count, same test names, same assertions
  satisfied).
- **Dependency Knowledge Graph** (Track 126) - Historical Memory does
  not consume DKG in the current implementation (128C §10, §13
  re-confirmed this), so DKG's own test suite is a pure regression
  check (confirms 128E did not accidentally introduce a DKG
  dependency) rather than a functional-interaction check.
- **Change Impact** (Track 123) - not a Historical Memory consumer or
  producer relationship today; regression run confirms continued
  independence.
- **Advisory Context** (Track 122) - same as Change Impact.
- **Query Layer** (Track 121) - Historical Memory's exclusive
  Repository Intelligence access path; its own test suite plus
  Historical Memory's Query-Layer-integration tests must pass
  unchanged, confirming the comment-only change did not alter how
  `execute_query()`/`load_snapshot()` are called.
- **Repository Knowledge Snapshot** (Track 120) - Historical Memory's
  upstream input; RKS's own test suite is a regression check
  confirming 128E touched nothing under
  `src/pcae/repository_intelligence/persistence.py` or
  `source_inventory.py`.

Expected result for every suite above: identical pass/fail outcome to
the pre-128E baseline. Any new failure anywhere in this list is
grounds to reject 128E's change regardless of how narrowly scoped it
appeared.

## 7. Verification Strategy for 128F

128F must independently re-verify, not merely re-run and trust green
output:

- **Implementation correctness** - re-read the actual diff (expected:
  comment-only in `historical_builder.py`) and confirm no non-comment
  line changed; independently confirm the new comment text accurately
  describes the real sort behavior (not merely that it was copied from
  this plan without verification).
- **Deterministic equivalence** - independently regenerate a real
  Historical Memory snapshot from real repository data before
  trusting any "byte-identical" claim 128E makes; do not accept 128E's
  own comparison without re-deriving it, mirroring 127F's own
  discipline of never trusting a prior phase's self-reported
  correctness.
- **Serialization compatibility** - independently confirm
  `executable_schema_version` and the persisted directory layout are
  unchanged.
- **Read-only verification** - independently re-run (or re-derive) the
  no-subprocess-outside-`git_source.py` AST checks and confirm no new
  write path was introduced.
- **Governance verification** - independently re-run `pcae health`/
  `check`/`doctor task-memory`/`push check`/`runtime inspect` and
  confirm the same posture 128D/128E claim.
- **Regression verification** - independently re-run every suite named
  in Section 6, not merely trust 128E's own reported pass counts.

128F's own recommended-next-phase output (expected: a track-closing or
128F-terminal recommendation, since 128E/128F together would close the
two 128C findings with nothing else outstanding) is out of this
document's scope to predict - that determination belongs to 128F
itself, based on what it actually finds.

## 8. Technical Debt Carried Forward

Only the same two items 128A found and 128B/128C already carried
forward, unrepaired, continue forward through 128D-128F:

1. **Persistence naming consistency** - Repository Knowledge Snapshot
   and Historical Memory Snapshot write to `snapshots/`; Dependency
   Knowledge Graph writes to `graphs/`. Cosmetic, non-functional,
   genuinely still present (128C re-confirmed against current
   source). **Not repaired by 128D or authorized for repair by
   128E** - any future standardization requires its own separately
   scoped decision (and, for the DKG side specifically, its own
   separately governed Track 126 phase, since Track 128 cannot
   unilaterally rename another track's directory).
2. **Explicit `historical_generator.py` scope** - resolved *forward*
   by 128E's own documentation (Section 4's Finding 2 resolution) but
   the underlying prior-document naming gap in 128B §3 itself remains
   unamended (128B is frozen; 128D-128F do not reopen it). Carried
   forward as a closed-going-forward, not retroactively-repaired,
   item.

No other technical debt is introduced, discovered, or carried forward
by this plan. 128E is not authorized to treat any other prior
observation (e.g. RKS's own independent, non-`serialize_
deterministic_json` local serializer, noted only as incidental context
during 128C's research and never part of any 128A/128B/128C finding)
as in-scope debt to repair - that was never a named finding of this
chapter and remains entirely out of 128D-128F's authorization.

## 9. Deferred Capabilities

Continue deferring, unauthorized by this plan or by 128E:

- historical reasoning;
- causal reasoning;
- predictive history;
- recommendations;
- Decision Evaluation;
- Dependency Knowledge Graph traversal;
- AI interpretation;
- execution planning;
- execution capability;
- new Historical Memory artifact families;
- new schemas;
- runtime plugins.

## 10. Governance Contract

128D and the 128E implementation it plans shall preserve:

- **observe-only runtime** - unchanged; a comment-only source change
  and a documentation-only report cannot themselves alter runtime
  posture, and Section 3 step 9 independently re-confirms this rather
  than assuming it;
- **execution unavailable** - unchanged;
- **reproducibility** - Section 5's byte-identical-output requirement
  is the direct reproducibility guarantee;
- **auditability** - every 128E change is independently diff-checkable
  (Section 7);
- **explainability** - the entire point of Finding 1's resolution is
  to make the real ordering behavior *more* explainable, not less.

## 11. Strict Non-Goals

This phase (128D) does not: implement hardening; modify Historical
Memory behavior; modify Repository Intelligence behavior; modify
schemas; modify source code; modify test code; introduce reasoning;
introduce inference; introduce execution; introduce runtime plugins.

128D produces a plan only. The plan itself authorizes 128E to make
exactly two narrow, non-behavioral changes (Section 2); it does not
itself make them.

## 12. Relationship to 128E and 128F

- **128E - Historical Memory Review & Hardening Implementation**:
  implements exactly Section 2's two items, following Section 3's
  pipeline, satisfying every Section 5 acceptance criterion, and
  running every Section 6 regression suite - no more, no less.
- **128F - Historical Memory Review & Hardening Verification**:
  independently re-verifies 128E per Section 7, not merely re-runs
  128E's own claimed results.

## 13. Acceptance

128D is complete when this implementation plan is frozen, both 128C
findings have an explicit, bounded, non-behavioral resolution plan,
the ten-step pipeline and every acceptance/regression/verification
requirement for 128E-128F are defined, technical debt and deferred
capabilities are correctly carried forward unrepaired, no
implementation has occurred, runtime remains
`Observed`/`observe`/execution-unavailable, and the recommended next
phase is 128E - Historical Memory Review & Hardening Implementation.
