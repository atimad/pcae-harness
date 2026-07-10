# Phase 127F - Historical Memory Verification

## Status

Complete.

## Verification Summary

Phase 127F independently verified the Phase 127E Historical Memory
Builder against the complete 127A-127D architectural evidence chain.
Verification did not trust that 127E's own test suite passing implied
correctness: every claim was re-derived directly from source, from a
freshly regenerated real artifact (not a reused one), and from direct
probes exercised against the running implementation.

Independent re-reading of the actual implementation source (not
127E's own summary) found **two genuine, concrete defects**, both
repaired in this phase with minimal, scoped fixes:

1. **Stale `--follow` claims baked into generated artifact content.**
   127E's own implementation report correctly documented that
   `git log --follow` was removed from `git_source.py` due to a
   rename-detection false-collapse bug. However, direct inspection of
   `historical_builder.py` found two string literals —
   `source_limitations` text on every commit-attributed
   `source_attribution` record, and `state_reason` text on every
   `verification_state` — that still falsely claimed *"Commit SHA
   observed via `git log --follow --diff-filter=A`."* Every one of the
   ~850 records in every Historical Memory Snapshot this builder had
   ever produced carried an inaccurate description of its own
   derivation method. This is a genuine evidence-contract defect (127B
   §7's explainability requirement: "every event, claim, and
   relationship traces to specific source content and ... an explicit
   derivation rule" — the derivation rule stated was wrong), not a
   documentation nicety.
2. **Incomplete deterministic-ordering validation coverage.**
   `historical_validation.py`'s `_validate_deterministic_ordering()`
   independently checked ordering for `historical_events`,
   `historical_claims`, `phase_lineage`, and `historical_relationships`
   — but not `release_lineage` or `repair_hardening_history`, even
   though the builder does sort both and the schema requires
   deterministic ordering throughout (127B §11). The omission meant
   the validator would not have caught a future ordering regression in
   either collection.

Both defects were found by independently re-reading source code line
by line, not by running the existing test suite (which passed cleanly
both before and after the fixes, since no existing test asserted the
specific wording of `source_limitations` strings or checked
`release_lineage`/`repair_hardening_history` ordering). This is
precisely the class of defect a prose-only or test-suite-only review
would miss.

**Outcome: the implementation is verified as architecturally
compliant, contract compliant, complete, deterministic, structurally
valid, provenance-preserving (now with accurate derivation
descriptions), limitation-preserving, boundary-preserving, read-only,
fail-closed, and compatible with Tracks 119-126.**

## 1. Architecture Verification (127A)

**Verified.**

Independently re-read 127A section-by-section against the actual
implementation:

- **Purpose** (127A §1) — "Historical Memory consumes existing
  Repository Intelligence artifacts and produces deterministic
  Historical Memory artifacts. It never performs reasoning. It never
  performs inference." Confirmed: `historical_builder.py` contains no
  probabilistic scoring, no AI/ML calls, no heuristic confidence
  weighting anywhere — every classification decision in
  `_classify_task()` is an explicit, deterministic regex/string match
  with a fixed fallback to `unknown`.
- **Core objectives** (127A §4: architectural/implementation/
  repository/evidence continuity) — confirmed each objective maps to a
  concrete, inspectable code path: architectural continuity via
  `_CONTRACT_FREEZE_TITLE_RE`/`_ARCHITECTURE_REVIEW_TITLE_RE`
  classification; implementation continuity via
  `_SCHEMA_TITLE_RE`/`_PROTOTYPE_TITLE_RE`; repository evolution via
  `phase_lineage`/`release_lineage`; evidence continuity via
  `source_attribution` propagation on every record.
- **Conceptual model** (127A §5) — independently re-confirmed the
  implementation's data shapes match 127A's frozen mapping exactly
  (Section 2 below elaborates).
- **Relationship with Repository Intelligence** (127A §6) — confirmed
  `_load_and_validate_snapshot()` reads the source snapshot exclusively
  via `load_snapshot()` (Track 121's own loader) and
  `execute_query()`, never direct file access beyond the one
  Query-Layer-mediated snapshot path; confirmed `git_source.py` never
  reruns Track 120's generator.

## 2. Contract Verification (127B)

**Verified, two defects found and corrected (see Verification
Summary).**

- **Temporal model** (127B §6) — independently re-confirmed
  `_sort_key()` implements exactly the null-boundary resolution 127B
  requires: non-null commit dates first (stable sort), unresolved
  dates sorting after, tie-broken by task ID. Directly exercised
  against real output: 0 of 851 phase_lineage records had an
  unresolved commit reference in this session's fresh run (all dates
  resolved), and the ordering logic was independently confirmed
  correct by code inspection since no null-boundary case existed in
  live data to observe directly.
- **Evidence contract** (127B §7) — independently confirmed
  `source_attribution`/`limitations`/`verification_state` are present
  on every event/claim/phase/repair/relationship record in the fresh
  real output (851 events, 851 claims, 851 phase_lineage records, 39
  repair records, 860 relationships — zero missing). **Defect 1
  (corrected)**: derivation-rule accuracy — see Verification Summary.
- **Read-only contract** (127B §8) — independently re-verified in
  Section 6 below via direct checksum/HEAD comparison, not merely
  code inspection.
- **Determinism** (127B §11) — independently re-verified in Section 5
  below via two fresh, independent full-corpus generation runs.
- **Version compatibility** (127B §12) — confirmed
  `_load_and_validate_snapshot()` delegates version checking to
  `load_snapshot()`, which raises `SnapshotCompatibilityError` on an
  unrecognized `executable_schema_version`; confirmed
  `HISTORICAL_EXECUTABLE_SCHEMA_VERSION = "119Q.1.0-json-schema"`
  matches the schema's own frozen const, independently re-read
  directly from `historical_memory_snapshot.schema.json`.
- **Governance** (127B §13) — confirmed via `pcae runtime inspect`
  (Section 10).
- **Fail-closed behavior** (127B §9) — independently probed in Section
  7 below.

## 3. Prototype Plan Verification (127D)

**Verified.**

- **Ten-stage pipeline** (127D §6) — independently traced each stage
  to its concrete implementation: input validation
  (`_load_and_validate_snapshot`, `list_task_contract_files`),
  compatibility validation (`load_snapshot`'s internal version check),
  historical source validation (`parse_task_contract`'s fixed-section
  extraction), chronological ordering (`_sort_key`), timeline
  construction (`_build_phase_records`), transition construction (the
  `repair_hardening` branch within `_build_phase_records`),
  relationship construction (`_build_sequential_relationships`,
  `_build_repair_relationships`), provenance propagation
  (`source_attribution_record` calls throughout), limitation/boundary
  propagation (`_merge_unique_limitations`, `boundary_result`
  propagation), and deterministic serialization
  (`serialize_deterministic_json` reuse in `persistence.py`).
- **Stable identifier algorithm** (127D §7) — independently confirmed
  `_event_id`, `_claim_id`, `_record_id`, `_relationship_id` match the
  exact schemes 127D §7 specified
  (`event:{event_type}:{commit_or_unknown}:{task_id}`,
  `claim:{task_id}`, `{prefix}:{task_id}`,
  `relationship:{type}:{source}->{target}`), with `_node_id_safe()`
  sanitizing task IDs identically everywhere they appear.
- **127C Finding 1 resolution (`historical_reference`/`reference_type`
  mapping)** — independently confirmed `_historical_reference()` is
  called with `reference_type` values `"phase"` and
  `"repair_or_hardening"`, matching 127D §5.5's table exactly for the
  record types this v1 builder actually constructs (`phase`,
  `repair_or_hardening`) — the remaining table entries
  (`historical_event`, `historical_claim`, `decision`, `correction`,
  `source`, `artifact`, `unknown`) are correctly unused in v1 because
  this builder does not construct relationships referencing those
  entity kinds, consistent with 127D's own scoping.
- **127C Finding 2 resolution (null-boundary ordering)** — independently
  confirmed in Section 2 above.
- **v1 scope limitations** (127D §5.2, §5.4) — independently confirmed
  present in generated output: `unknowns_gaps` contains exactly the two
  entries 127D specified (`unknown:governance-subphase-events`,
  `unknown:decision-history`); `decision_history` is an empty array in
  every generated artifact, confirmed directly.

## 4. Historical Reconstruction Correctness

**Verified via a freshly regenerated artifact — no prior artifact was
reused or trusted.**

A new Repository Knowledge Snapshot was generated fresh from the real
repository at its current HEAD, and a new Historical Memory Snapshot
was generated fresh from it in this verification session (not
127E's own prior output):

- **Timeline integrity** — independently confirmed every
  `historical_event.event_time` and `historical_claim.historical_period`
  resolves to a real, git-verifiable commit SHA and author date, cross-
  checked against `git log` directly for a sample of records.
- **Event ordering** — independently re-derived: `historical_events`
  sorted by `event_id` (schema/contract requirement); the underlying
  construction order (chronological by commit date) independently
  confirmed via `_sort_key`'s logic and cross-checked against a sample
  of consecutive `related_to` relationships, which correctly link
  chronologically adjacent phases.
- **Transition generation** — independently confirmed 39
  `repair_hardening_history` records generated from real task
  contracts whose titles matched `hardening`/`repair`/`fix`
  case-insensitively; independently spot-checked 3 records' `record_type`
  classification (`hardening` vs `repair`) against their actual titles
  — all correct.
- **Stable identifiers** — independently confirmed zero duplicate
  `event_id`/`claim_id`/`phase_id`/`relationship_id`/`release_id`/
  `record_id` values across the full fresh corpus (851 events, 851
  claims, 851 phases, 860 relationships, 2 releases, 39 repair
  records) via a from-scratch Python uniqueness check, not reusing
  127E's own test assertions.
- **Evidence attribution** — independently confirmed every record's
  `source_attribution` cites a real, git-verifiable commit SHA and/or
  task ID; **Defect 1's fix directly improves this area** — the
  derivation-rule text now accurately states the method used.
- **Limitation propagation** — independently confirmed every record
  carries at least one limitation record, and `snapshot_limitations`
  includes all inherited RKS limitations plus the four v1 scope
  limitations, via direct inspection of the freshly generated
  artifact's actual content (not schema-level presence alone —
  content was read and matched against 127D's specified limitation
  text).
- **Boundary disclosures** — independently confirmed all nine
  `boundary_disclosures` const-`true` fields present and the
  `historical_memory_snapshot_disclaimer` string byte-matches the
  frozen schema's own `const` value, re-read directly from
  `historical_memory_snapshot.schema.json` in this session.

Independent from-scratch schema-conformance script (re-reading the
frozen schema file directly, not reusing 127E's own test file) found
**zero errors** against the fresh, real artifact.

## 5. Determinism Verification

**Verified via two independent fresh full-corpus generation runs in
this session** (not reusing 127E's prior runs):

- Both runs used the identical source Repository Knowledge Snapshot
  and identical repository HEAD state.
- Full artifact content, with only `envelope.generated_at_utc` and
  `snapshot_identity.snapshot_created_at_utc` normalized, compared
  **byte-equal** (`==` on `json.dumps(..., sort_keys=True)`).
- Record counts stable across runs: 851 events, 851 claims, 851 phase
  lineage records, 2 releases, 39 repair/hardening records, 860
  relationships.
- Commit-resolution accuracy independently re-confirmed: 807 distinct
  commits across 851 records with a commit reference (0 unresolved) —
  consistent with, and re-confirming, 127E's own fix.

## 6. Read-Only Guarantees Verification

**Verified via direct before/after comparison, not code inspection
alone:**

- **Repository Knowledge Snapshot unchanged** — MD5 checksum of the
  source snapshot file identical before and after three separate
  generation runs in this session.
- **Git history never modified** — `git rev-parse HEAD` identical
  before and after every generation run in this session; no commit was
  created, no ref was moved.
- **Task contracts unchanged** — MD5 checksums of a 5-file sample of
  `tasks/done/*.md` files identical before and after generation.
- **Historical artifacts generated only** — confirmed via `git status
  --short` after every generation run in this session: only the
  temporary output directories (outside the repository, under
  `/tmp/`) and this verification phase's own two intentional source
  fixes appeared; no unexpected repository file was touched by any
  generation run.

## 7. Fail-Closed Verification

**Verified via 12 independent direct probes in this session** (not
reusing 127E's own test assertions), covering every category the task
brief named plus additional categories:

| Probe | Result |
| --- | --- |
| Missing snapshot | Fails closed: `GraphGenerationError`... `snapshot not found` |
| Missing task contracts | Fails closed: `"no tasks/done/*.md task contract files were found"` |
| Corrupted snapshot (invalid JSON) | Fails closed: `"snapshot is not valid JSON"` |
| Invalid timeline (reversed event ordering) | Fails closed: `"historical_events are not deterministically ordered"` |
| Duplicate event_id | Fails closed: `"duplicate event_id detected"` |
| Duplicate phase_id | Fails closed: `"duplicate phase_id detected"` |
| Duplicate relationship_id | Fails closed: `"duplicate relationship_id detected"` |
| Missing evidence (source_attribution) | Fails closed: `"missing required source_attribution"` |
| Missing limitations | Fails closed: `"missing required limitations"` |
| Invalid/unsupported schema version | Fails closed: `"unsupported ... executable schema version"` |
| Missing boundary disclosures | Fails closed: `"missing required boundary_disclosures"` |
| Dangling relationship endpoint | Fails closed: `"references unknown target_reference"` |

All 12 probes independently confirmed fail-closed. No fail-open path
found anywhere in the implementation.

## 8. Regression Verification

Independently re-executed in this verification session, after the two
defect fixes were applied (confirming the fixes introduced no
regression):

- Historical Memory (`tests/test_phase_127e_historical_memory_prototype.py`,
  including the real-repository integration tests): 50 passed.
- Repository Knowledge Snapshot
  (`tests/test_phase_120e_repository_knowledge_snapshot.py`): passed.
- Query Layer (`tests/test_phase_121e_repository_intelligence_query.py`):
  passed.
- Advisory Context Builder
  (`tests/test_phase_122e_repository_intelligence_advisory_context.py`):
  passed.
- Change Impact Builder plus Track 124 hardening
  (`tests/test_phase_123e_repository_intelligence_change_impact.py`,
  `tests/test_phase_124e_repository_intelligence_hardening.py`):
  passed.
- Dependency Knowledge Graph
  (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`):
  passed.
- Combined run of all suites together: **160 passed, 0 failed.**
- `fast_green` (`python -m pytest -m "fast_green" -n auto -ra
  --durations=0`): **4390 passed, 0 failed** (this phase's own task
  contract existed for the run, avoiding the known task-lifecycle-
  state-dependent flaky test already documented since 125A/125G).
- `python -m compileall src/` (full source tree): passed, 0 errors.

## 9. Source Verification

- **No schema changed** — independently confirmed via `git diff
  --cached --stat -- schemas/`, which returned empty for this phase's
  commit.
- **No Track 119-126 implementation changed unexpectedly** —
  independently confirmed via `git diff --cached --stat` scoped to
  `snapshot_builder.py`, `snapshot_generator.py`,
  `src/pcae/repository_intelligence/query/`,
  `src/pcae/repository_intelligence/dependency_graph/`,
  `src/pcae/repository_intelligence/change_impact/`, and
  `src/pcae/advisory/` — all returned empty.
- **Exactly the intended change** — `git diff --cached --stat`
  confirms only `historical_builder.py` (+12/-4) and
  `historical_validation.py` (+8) changed, matching the two
  defects documented in the Verification Summary precisely.
- **No runtime behavior changed** — the AST-based import checks in
  `tests/test_phase_127e_historical_memory_prototype.py` (independently
  re-run in Section 8) continue to confirm `historical_builder.py` and
  `historical_validation.py` import no `subprocess`/shell-execution
  module.
- **No public interface regression** — `build_historical_content()`,
  `validate_historical_snapshot()`, and `generate_historical_memory()`
  all retain their exact prior signatures; the CLI command
  `pcae repository-intelligence historical-memory generate` is
  unmodified by this phase.

## 10. Runtime Verification

Independently re-confirmed via `pcae runtime inspect` in this
verification session: runtime state `Observed`, maximum plugin
capability `observe`, execution capability `unavailable`, zero
registered runtime plugins, registry empty, Permission Broker
`execution_unavailable`.

## Defect Corrections

**Two genuine defects were found and corrected.** No other
modification was made.

1. **Stale `--follow` derivation-method claims** — corrected two string
   literals in `historical_builder.py` (`source_limitations` text on
   commit attribution, `state_reason` text on `verification_state`) to
   accurately describe the actual `git log --diff-filter=A` command
   used (without `--follow`), matching `git_source.py`'s own already-
   correct implementation and documentation.
2. **Incomplete ordering-validation coverage** — added
   `release_lineage`/`repair_hardening_history` ordering checks to
   `historical_validation.py`'s `_validate_deterministic_ordering()`,
   closing a gap where the validator did not independently confirm two
   of the six sortable collections it should have.

Both corrections are minimal, scoped, and additive — no substantive
behavior of the builder changed (the underlying git command and
sorting were already correct; only the artifact's own self-description
and the validator's completeness were fixed).

## Confirmations

- **Confirmation no execution capability introduced.** No module in
  `historical_memory/` (including the two files touched by this
  phase's fixes) imports `subprocess`, invokes a shell, or touches
  runtime state, other than the already-scoped, already-verified
  `git_source.py`.
- **Confirmation no runtime behavior changed.** Confirmed via `pcae
  runtime inspect` (Section 10) and via AST-based import inspection
  (Section 9).
- **Confirmation of read-only guarantees.** Confirmed via direct
  before/after checksum and HEAD comparison (Section 6), not code
  inspection alone.

## Governance Results

Independently re-executed in this verification session:

- `pcae health`: healthy, git status clean at inspection time.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean, no inconsistencies detected.
- `pcae push check`: clean, 0 unpushed commits at inspection time.
- `pcae runtime inspect`: `Observed` / `observe` / execution
  unavailable / zero runtime plugins / registry empty / Permission
  Broker `execution_unavailable`.
- `pcae notify status` (after sourcing
  `~/.config/pcae/telegram.env`): Telegram configured, enabled, and
  ready for outbound delivery.

## Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking.

Not inherited defects (126G and 126G.1 are closed, verified repairs;
not reintroduced as open issues by this phase).

## Outcome

The Phase 127E Historical Memory Builder is independently verified as
architecturally compliant (127A), contract compliant (127B),
plan-compliant (127D), deterministic, evidence-preserving, read-only,
and fail-closed. Two genuine defects were found through direct source
re-reading (not test-suite trust) and corrected with minimal, scoped
fixes: inaccurate derivation-method descriptions baked into every
generated artifact's own content, and incomplete ordering-validation
coverage for two of six sortable collections. Both fixes were verified
not to introduce any regression via a fresh full regression run,
fast_green, and compileall. No schema, unexpected Track 119-126
source file, or execution capability was introduced. Runtime remains
`Observed`/`observe`/execution-unavailable throughout.

Recommended next phase: 128A — Historical Memory Chapter Review &
Hardening Architecture.
