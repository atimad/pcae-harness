# Phase 128C - Historical Memory Review & Hardening Contract Verification

## 1. Method

This phase does not trust 128B (Historical Memory Review & Hardening
Contract Freeze) because it exists. Every requirement below was
re-derived directly from: the 128A architecture document, the 128B
contract's own text, the real Track 127 Historical Memory source
(`src/pcae/repository_intelligence/historical_memory/*.py`), the
frozen 119Q/119O/119S JSON schemas, the historical_memory CLI wiring
in `src/pcae/cli.py`, and the existing Track 127 test suite
(`tests/test_phase_127e_historical_memory_prototype.py`,
`tests/test_phase_127f_*`). Where 128B's prose was found to precisely
match source, the verdict is CONFIRMED. Where it was found to be
imprecise or incomplete, the verdict is a documented finding
(Section 15) - not repaired here, per this phase's documentation-only
scope.

No implementation, schema, or runtime behavior changed while
performing this verification. All commands run were read-only
(`grep`, direct file reads, `python3 -c` schema inspection).

## 2. Architecture Verification (128A)

Re-read `docs/PHASE_128_HISTORICAL_MEMORY_REVIEW_HARDENING_ARCHITECTURE.md`
directly rather than relying on 128B's summary of it. Confirmed:

- 128A's stated purpose ("reviews and hardens what already exists...
  no new Historical Memory capabilities are introduced") is carried
  into 128B §1 unchanged in substance.
- 128A's eleven review categories (Architecture, Contracts,
  Determinism, Interfaces, Artifact Consistency, Validation,
  Persistence, Serialization, CLI Consistency, Documentation, Testing,
  Governance) map onto 128B's twelve hardening-responsibility
  categories (128B §4) with one addition not present in 128A's own
  category list: "persistence consistency" is named explicitly as its
  own category in 128B §4, where 128A folded persistence-naming
  observations under "Artifact Consistency" and "Persistence" review
  categories rather than a single named "persistence consistency"
  responsibility. This is additive precision, not drift - 128B's
  broader category list is a superset, not a contradiction, of 128A's.
- 128A's two technical-debt findings (persistence subdirectory naming;
  optional DKG CLI input scope) are the same two findings 128B §13
  carries forward. Verified word-for-word consistent in substance
  across both documents.

**Verdict: CONFIRMED.** 128B is a faithful, non-drifting
operationalization of 128A's architecture.

## 3. Contract Verification (128B Structure)

128B's own contract authority (§2) claims it "operates inside, and
does not amend" the 125B Next Architecture Direction Contract and the
127B Historical Memory Contract. Independently re-read 127B in full:
confirmed 128B §§6-13 (Determinism, Evidence, Temporal, Read-Only,
Serialization, Failure, Governance, Documentation Findings) each
explicitly restate a specific 127B section (127B §11, §7, §6, §8, -,
§9, §13 respectively) rather than introducing new normative content.
No section of 128B was found to silently add a requirement 127B did
not already establish, and no section was found to silently drop a
127B requirement.

**Verdict: CONFIRMED.** 128B is structurally sound: every normative
clause traces to either 127B (Historical Memory's own binding
contract) or 128A (this hardening chapter's own architecture) - never
free-floating new authority.

## 4. Scope Verification

Re-derived from the real package contents, not from 128B's own list.
Files under `src/pcae/repository_intelligence/historical_memory/`:
`__init__.py`, `git_source.py`, `historical_builder.py`,
`historical_generator.py`, `historical_validation.py`,
`persistence.py`.

| 128B scope item | Real source mapping |
| --- | --- |
| Historical Memory Builder | `historical_builder.py` (939 lines) |
| Timeline generation | `historical_window`/`historical_period` construction + the chronological sort in `historical_builder.py` |
| Event generation | `historical_event` record construction, `historical_builder.py` |
| Transition generation | `decision_history_record`/`repair_hardening_record`/`supersession_correction_record` construction, `historical_builder.py` |
| Evidence mapping | `source_attribution_record(...)` call sites, `historical_builder.py:344-628` |
| Temporal reconstruction | `git_source.py` (247 lines) |
| Serialization | `persistence.py` (`write_historical_snapshot`, reuses `serialize_deterministic_json`) |
| CLI integration | `src/pcae/cli.py:4675-4716` (`historical-memory generate` subcommand: `--snapshot`, `--output`, `--pretty`, `--json`) |
| Validation | `historical_validation.py` (260 lines) |
| Persistence | `persistence.py` |
| Documentation | 127A-127F + 128A-128C themselves |

**One scope-completeness observation**: `historical_generator.py` (82
lines, its own docstring: "the only intended external entry point into
the historical_memory package") is not named as its own line item in
128B §3's scope list. It is not omitted from coverage in substance -
its orchestration role is implicitly covered by the "CLI integration"
and "Serialization" items it wires together - but a reader unfamiliar
with the package could momentarily miss that this module exists.
Documented as Finding 2 (Section 15) - a naming-completeness
precision gap, not a coverage gap; no real subsystem escapes 128B's
governance.

**Verdict: CONFIRMED**, with Finding 2 noted for precision (not a
blocking omission - every real file and function is governed by some
128B scope item).

## 5. Hardening Responsibility Verification

128B §4 permits improvement only in implementation, terminology,
persistence, evidence, limitation-propagation, boundary-disclosure,
serialization, deterministic-behavior, interface, documentation,
governance, and testing consistency, and explicitly states "Hardening
shall not expand functionality." Cross-checked against 128A's own
"Hardening Architecture" section (which independently arrived at
eleven, not twelve, named categories - the difference being 128B's
explicit "persistence consistency" line, already addressed in Section
2 above) and 124A's precedent (the equivalent Repository Intelligence
hardening chapter, which established the same "consistency
improvement only, no functionality expansion" boundary for a sibling
subsystem). No category in 128B's list, individually or combined,
authorizes a new record type, new CLI capability, new consumer
integration, or new artifact family - each named category is a
quality-of-existing-implementation concern only.

**Verdict: CONFIRMED.** The permitted-categories list is exhaustive of
consistency-only concerns and contains no functional-expansion path.

## 6. Cross-Track Compatibility Verification

Re-derived directly from current source, not from 128A/128B's prior
findings, for every track 128B names:

- **Track 119** (executable schemas) - `historical_memory_snapshot
  .schema.json`'s `executable_schema_version` const is
  `"119Q.1.0-json-schema"` (schema file, `snapshot_identity`
  properties). RKS's is `"119O.1.0-json-schema"`; DKG's is
  `"119S.1.0-json-schema"`. All three exactly match 128B's claimed
  strings. Not modified by Track 128 (confirmed via `git log
  --oneline -- schemas/` showing no Track 128 commit touches any
  schema file).
- **Track 120** (Repository Knowledge Snapshot) - Historical Memory's
  only Repository Intelligence input, reached exclusively via the
  Track 121 Query Layer (confirmed: `historical_builder.py` imports
  `execute_query`/`load_snapshot` from the query-layer module, never a
  raw RKS file read).
- **Track 121** (Query Layer) - confirmed exclusive access path for
  Repository Intelligence content specifically; task-contract/git
  history discovery is a separate, non-Query-Layer path via
  `git_source.py`, exactly as 127D §5.1 scoped and 128A's Architecture
  category re-confirmed. Re-confirmed again here directly: no
  `historical_memory_query` category exists in
  `SUPPORTED_QUERY_CATEGORIES` (grep confirms absence).
- **Track 122** (Advisory Context) - not modified by Track 128; no
  Advisory module imports anything from `historical_memory`
  (confirmed via grep for `historical_memory` imports outside the
  package itself and outside test files: zero hits in
  `src/pcae/repository_intelligence/advisory*` or similar).
- **Track 123** (Change Impact) - same result; zero cross-imports.
- **Track 126** (Dependency Knowledge Graph) - not modified by Track
  128 (`git log` shows no Track 128 commit under
  `src/pcae/repository_intelligence/dependency_graph/`). DKG's
  `DEFAULT_OUTPUT_SUBDIR` is `"repository-intelligence/dependency
  -graph"`, writing to a `graphs/` subdirectory - confirmed still true
  by direct current-source read (`persistence.py:20,36` in the
  `dependency_graph` package), not merely historically true.
- **Track 127** (Historical Memory itself) - 127A-127F's own
  documents are unmodified by Track 128 (only new 128-series documents
  were added; `git log --oneline -- docs/PHASE_127*` shows no commit
  after 127F's own completion touches any 127-series file).

**Verdict: CONFIRMED, no contract drift.** Every cross-track claim in
128B §5 was independently re-verified against current source, not
merely re-cited from 128A.

## 7. Determinism Verification

Re-derived the actual sort/serialization code, not 128B's description
of it.

- `persistence.py` imports and calls `serialize_deterministic_json`
  (`from pcae.repository_intelligence.serialization import
  serialize_deterministic_json`; called in `write_historical_snapshot`)
  - confirmed identical helper reuse to Track 124/126, as 128B §10
  claims.
- Processing-order sort (`historical_builder.py:332-340`): stable sort
  by `(has_commit_date, commit_author_date_utc, task_id)` - matches
  the "chronological, null-boundary-after, id-tiebreak" description in
  128A's Determinism category.
- Final persisted-array sort (`historical_builder.py:912-921`): every
  output collection (`historical_events`, `historical_claims`,
  `phase_lineage`, `release_lineage`, `repair_hardening_history`,
  `historical_relationships`) is sorted by its own record's
  identifier field (`event_id`, `claim_id`, etc.) - lexicographic
  string order, not by declared time reference.
- `historical_validation.py`'s `_validate_deterministic_ordering`
  (lines 193-215) independently confirms this: it validates
  ID-lexicographic order for all six collections, not chronological
  order.

Both orderings are individually fully deterministic (same input always
produces the same output, byte-for-byte, as 127F's own two-independent
-run verification already confirmed and this phase does not
re-execute). **However**: 127B §6's "Deterministic ordering" clause
("order events, claims, and lineage records by their own declared time
reference... ties broken by identifier"), restated unchanged by 128B
§8, describes the *persisted* output as time-ordered with an
identifier tiebreak. The real, validated, enforced property is
identifier-ordered outright - chronological order governs only an
internal processing stage, never the final persisted array order.
This is a wording-precision gap in the underlying 127B contract text
(carried forward, not introduced, by 128B), not a functional defect -
determinism itself is fully intact under either description. Documented
as Finding 1 (Section 15).

**Verdict: CONFIRMED for the determinism property itself (equivalent
input -> equivalent output, no entropy). Finding 1 (non-blocking
documentation-precision gap) noted for the specific ordering-key
wording.**

## 8. Evidence Verification

`historical_builder.py:344-381` builds `source_attribution` from real
derived content: `source_id=f"source:task-contract:{...}"` for every
task-contract-derived record, with an added commit-based attribution
(`source:commit:{introduction.commit_sha}`) when a resolvable
introduction commit exists. This attribution list is attached to every
event (424, 442, 469, 485), decision record (515), repair/hardening
record (572), and relationship (628) - confirmed by direct line
inspection, not by trusting 128A/128B's summary. No placeholder or
generic ("the repository") attribution string was found anywhere in
the builder.

**Verdict: CONFIRMED.** Evidence and attribution are preserved exactly
as 127B §7/128B §7 require; no inferred evidence exists anywhere in
the builder (every attribution traces to a real task-contract path or
git commit SHA already resolved by `git_source.py`).

## 9. Temporal Verification

- **Deterministic ordering**: Section 7 above (Finding 1 notwithstanding,
  fully deterministic).
- **No inferred chronology**: `git_source.py` resolves
  `commit_author_date_utc` from real `git log` plumbing output only
  (`git_source.py`'s subprocess call, the sole subprocess use in the
  package); when no introduction commit is resolvable,
  `historical_builder.py`'s sort key treats the record as a
  null-boundary case (sorted after, never assigned a fabricated date)
  - confirmed by direct reading of the `_sort_key` function (Section 7).
- **No historical reasoning**: confirmed absent - Section 12 below.

**Verdict: CONFIRMED.**

## 10. Read-Only Verification

- **Repository/git history**: `git_source.py`'s only subprocess
  invocation is `subprocess.run(["git", *args], ...)` (read-only git
  plumbing: `log`, `show`, etc. - no `commit`, `push`, `checkout
  --force`, or any mutating git subcommand appears anywhere in the
  package, confirmed by grep for `"git",` argument lists).
- **Repository Knowledge Snapshot**: read-only via Query Layer
  (Section 6).
- **Dependency Knowledge Graph**: not consumed at all in the current
  implementation (confirmed: no import of any `dependency_graph`
  module anywhere in `historical_memory/*.py`) - therefore trivially
  read-only (nothing to mutate because nothing is touched).
- **Task contracts**: read via `git_source.py`'s git-plumbing-based
  discovery of `tasks/done/*.md` content at specific historical
  commits (not live filesystem mutation) - confirmed no `open(...,
  "w")` or `Path.write_text` call exists anywhere in
  `historical_builder.py`, `historical_validation.py`, or
  `git_source.py` (only `persistence.py` writes, and only to its own
  output artifact path).
- **No subprocess outside `git_source.py`**: confirmed via grep -
  `historical_builder.py` and `historical_validation.py` import no
  `subprocess`. AST-based enforcement exists:
  `tests/test_phase_127e_historical_memory_prototype.py`'s
  `test_builder_module_has_no_execution_related_imports` and
  `test_validation_module_has_no_execution_related_imports` (lines
  694-734) parse each module with `ast.parse`/`ast.walk` and assert
  `{"subprocess", "os.system", "shell_gate"}` is absent from the
  import set.

**Verdict: CONFIRMED.** No mutation path exists for repository
contents, git history, Repository Knowledge Snapshot, Dependency
Knowledge Graph (not even read, let alone mutated), or task contracts.

## 11. Serialization Verification

`persistence.py` reuses `serialize_deterministic_json` unchanged
(Section 7); no parallel serialization logic exists in the package.
Compatibility: `executable_schema_version` remains
`"119Q.1.0-json-schema"` (Section 6), unmodified by Track 128; the
persisted artifact shape is unchanged from 127E/127F. The
`graphs/`-vs-`snapshots/` naming inconsistency (Section 6, DKG vs.
RKS/Historical Memory) remains a cosmetic, non-functional divergence -
re-confirmed still true by direct current-source read, not merely
historically true.

**Verdict: CONFIRMED.** Serialization compatibility is preserved; the
one named inconsistency is unchanged and correctly still classified as
non-blocking documentation debt (Section 14).

## 12. Failure Contract Verification

Independently enumerated (not merely re-counted from 128A/128B's
claimed "12") every fail-closed category actually tested:
`TestFailClosedBehavior` in
`tests/test_phase_127e_historical_memory_prototype.py` (lines 432-518)
contains exactly 9 tests: missing snapshot file, corrupted snapshot,
missing task history, incompatible schema version, corrupted
Repository Intelligence artifact, missing source attribution, missing
limitations, missing boundary disclosures, chronology violation.
`TestValidation` (lines 382-430) adds 3 more distinct fail-closed
categories not covered above: duplicate identifiers, invalid
event/relationship type, dangling relationship endpoint reference.
9 + 3 = **12**, independently re-derived and exactly matching 128A/128B's
claimed count - not merely trusted from their prose.

Deferred/reasoning-related deferred capabilities being explicitly
absent (Section 13 below) is itself part of what keeps this failure
surface closed: no code path exists that could silently promote an
ambiguous input into a confident-looking record via inference, since
no inference code exists at all.

**Verdict: CONFIRMED**, with the exact count (12) independently
re-derived rather than trusted.

## 13. Deferred Capabilities Verification

Grepped the full package plus the two governing test files for any
reasoning/inference/predictive/recommendation/LLM/graph-traversal
code (not merely documentation strings disclaiming them): zero hits.
The only matches found were disclosure strings *stating* these are
forbidden (e.g. `__init__.py`'s module docstring,
`historical_builder.py`'s `_NO_PHASE_LINEAGE_TRAVERSAL_LIMITATION`
constant - itself a disclosure record, not an implementation).
`ModuleNotFoundError`-raising tests (lines 678-692 of the prototype
test file) explicitly assert no `historical_reasoning` or
`timeline_engine` module exists anywhere in the package. No `import
openai`, `import anthropic`, network call, or `requests`/`urllib`
usage exists anywhere in the package (confirmed via the same import
grep used in Section 10).

**Verdict: CONFIRMED.** Every capability 128B §14 lists as deferred
remains, independently re-verified, completely unimplemented.

## 14. Technical Debt Verification

Re-confirmed both 128A findings, carried forward unrepaired by 128B
§13, remain correctly classified and still genuinely present (not
stale claims):

1. **Persistence subdirectory naming** - re-confirmed by direct,
   current-source inspection (Section 6): RKS and Historical Memory
   both write to `snapshots/`; DKG alone writes to `graphs/`. Still
   true, still unrepaired, still correctly classified as
   documentation debt (cosmetic - each family uses its own distinct
   `DEFAULT_OUTPUT_SUBDIR`, so no cross-family confusion results).
2. **Optional DKG CLI input scope** - re-confirmed by direct
   inspection of both the schema (`historical_relationship`'s
   `reference_type` enum includes `"artifact"`, confirming the
   data-model hook exists) and the CLI parser (`cli.py:4693-4716`
   has no `--dependency-graph` option) - still genuinely unexercised,
   still correctly classified as documentation debt, not a functional
   defect (an unused option is honest, not incomplete).

No implementation repair occurred for either finding in 128A, 128B,
or this phase (128C). Both remain open candidates for a future 128D
plan to explicitly judge.

**Verdict: CONFIRMED.** Both findings remain accurately classified and
genuinely unrepaired.

## 15. Documentation Defects Found

Two findings, both non-blocking, neither repaired in this phase (128C
is documentation-only and does not modify prior frozen contracts or
any implementation):

- **Finding 1 - Temporal contract wording precision gap.** 127B §6's
  "Deterministic ordering" clause (restated unchanged by 128B §8)
  describes persisted Historical Memory output as ordered "by their
  own declared time reference... ties broken by identifier." The real,
  tested, enforced property (Section 7/9 above) is that the final
  persisted arrays are ordered purely by each record's own identifier
  field; chronological ordering by declared time reference governs
  only an internal processing stage before the final identifier-based
  sort. This does not weaken determinism (identifier-ordering is
  itself fully deterministic and independently verified
  byte-reproducible) - it is a precision gap in how the contract
  describes *which* sort key the persisted artifact actually uses.
  Since 127B and 128B are both already-frozen contracts outside this
  verification phase's edit authority, this finding is recorded here
  for a future contract-amendment phase (potentially within 128D-128F,
  or a dedicated amendment) to resolve by clarifying the wording -
  not by changing the implementation, which is already correct and
  already the more useful of the two orderings for artifact
  reproducibility/diffability.
- **Finding 2 - Scope-list naming completeness gap.** 128B §3's scope
  list does not separately name `historical_generator.py` (the
  package's own documented external entry point) as its own line
  item, though its orchestration role is implicitly covered by the
  "CLI integration"/"Serialization" items it connects. No real
  subsystem escapes governance because of this - it is a readability
  precision gap only, worth a future 128D-128F phase folding in if the
  scope list is otherwise touched, not worth a dedicated
  contract-amendment phase on its own.

No inconsistency, omission (beyond Finding 2's minor naming gap),
ambiguity, incorrect cross-reference, governance drift, or terminology
drift was found anywhere else in 128A or 128B against the real,
current source.

## 16. Governance Compatibility

Re-confirmed via `pcae runtime inspect` in this session: runtime state
`Observed`, maximum plugin capability `observe`, execution capability
`unavailable`, Permission Broker status `execution_unavailable`, zero
registered runtime plugins. Reproducibility, auditability, and
explainability are preserved by construction - every claim in this
verification traces to a specific file:line citation, re-derivable by
any future reader without trusting this document's own prose either.

**Verdict: CONFIRMED.**

## 17. Confirmations

- **No implementation occurred.** This phase performed only read
  operations (file reads, `grep`, `git log`, `python3 -c` schema
  inspection). No file under `src/**` or `tests/**` was modified.
- **No runtime behavior changed.** No command executed by this phase
  had any side effect beyond reading.
- **Execution remains unavailable.** Confirmed via `pcae runtime
  inspect` (Section 16).

## 18. Conclusion

Every requirement in 128B (Historical Memory Review & Hardening
Contract Freeze) was independently re-derived from 128A's architecture,
127B's underlying Historical Memory contract, and the real Track 127
source/schema/test files - not merely re-cited from 128B's own text.
All twelve verification categories this phase was scoped to check
(Purpose, Scope, Hardening Responsibilities, Cross-Track Compatibility,
Determinism, Evidence, Temporal, Read-Only, Serialization, Failure,
Governance, Technical Debt, Deferred Capabilities) reach CONFIRMED,
with two non-blocking documentation-precision findings recorded
(Section 15) for a future phase to weigh - neither repaired here, and
neither changing this verification's overall conclusion that 128B is
internally consistent, source-accurate, and ready to bind 128D-128F.

No implementation occurred. No schema changed. No runtime behavior
changed. Runtime remains `Observed`/`observe`/execution-unavailable.

Recommended next phase: 128D - Historical Memory Review & Hardening
Implementation Plan.
