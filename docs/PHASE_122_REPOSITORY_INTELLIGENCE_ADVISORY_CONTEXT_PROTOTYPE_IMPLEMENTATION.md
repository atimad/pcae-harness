# Phase 122E - Repository Intelligence Advisory Context Prototype

## 1. Purpose

Phase 122E implements the first Repository Intelligence Advisory
Context Builder prototype. The builder deterministically assembles a
bounded, source-attributed Repository Intelligence context package for
a declared advisory purpose, consuming Repository Intelligence
exclusively through the existing Track 121 read-only Query Layer.

The builder is a context assembler only. It performs no reasoning, no
relevance ranking beyond declared query scope, and no decision making.
It is implemented within the boundaries frozen by 122B, verified by
122C, and planned by 122D.

## 2. Implementation Overview

Implemented a narrow package under `src/pcae/advisory/context/`:

- `context_request.py`: `AdvisoryContextRequest`, a bounded,
  declared-purpose request that translates unchanged into an existing
  Track 121 `QueryRequest` — no new query category, no query language.
- `context_validation.py`: `AdvisoryContextValidationError` and
  fail-closed validation for the context request, the Query Layer
  result shape, attribution presence, and boundary disclosure
  presence.
- `advisory_context_builder.py`: `AdvisoryContextBuilderError` and
  `build_advisory_context()`, the pipeline entry point that invokes
  the existing Track 121 `execute_query` and assembles the context
  package.
- `context_package.py`: `RepositoryIntelligenceContextPackage`, the
  deterministic, serializable context package container, and the
  package-level `NON_AUTHORITY_DISCLAIMER` constant.
- `context_serializer.py`: `serialize_context_package()`, deterministic
  JSON formatting.
- `__init__.py`: package exports.

Added the minimal CLI surface, nested under the existing `pcae
advisory` command group (Phase 88X) rather than a new top-level
command:

```text
pcae advisory context build --snapshot PATH
  (--entity NAME | --capability NAME | --contract NAME)
  [--purpose TEXT] [--output PATH] [--json|--pretty]
```

No reasoning command, recommendation command, or execution command was
introduced. `src/pcae/commands/advisory_context.py` implements the CLI
handler; `src/pcae/cli.py` wires `advisory context build` under the
existing `advisory_subparsers` group.

Reused, without duplication:

- `pcae.repository_intelligence.query.query_engine.execute_query` —
  the sole Repository Intelligence access path;
- `pcae.repository_intelligence.query.query_request.QueryRequest` and
  its `SUPPORTED_QUERY_CATEGORIES` — the six existing supported
  categories, imported and re-exported as
  `SUPPORTED_CONTEXT_CATEGORIES`, never redefined;
- `pcae.repository_intelligence.query.snapshot_loader` /
  `query_result` error types, caught and re-raised as
  `AdvisoryContextBuilderError` at the consumption boundary, never
  reimplemented.

No new Repository Intelligence logic, snapshot loader, query engine, or
query category was added. `src/pcae/repository_intelligence/**` was not
modified by this phase.

### 2.1 Naming Note: Distinct from the Frozen 115W `AdvisoryContextPackage`

`RepositoryIntelligenceContextPackage` (this phase) is a deliberately
different name from `pcae.core.advisory_context_package.AdvisoryContextPackage`
(115W, frozen, unmodified). The two are structurally and
architecturally independent: this phase decides no placement of its
output into any of the 115W type's 15 frozen sections, and does not
wire into any Advisory Provider, Repository Skill, Decision Evaluation,
or lifecycle command (122B S8, 122C S17-18, 122D S7/S16). That
placement decision remains deferred to a future, explicit
115W-contract amendment or extension phase.

## 3. Advisory Context Builder Architecture

`build_advisory_context(snapshot_path, request)` is the single pipeline
entry point. It is a plain function over dataclasses, not a class
hierarchy, matching the 122D plan's "responsibilities only" component
shapes:

1. Validate the `AdvisoryContextRequest` (`context_validation.validate_context_request`).
2. Translate the request into an existing `QueryRequest`
   (`AdvisoryContextRequest.to_query_request`).
3. Invoke `execute_query(snapshot_path, query_request)` — the existing
   Track 121 entry point, unmodified.
4. Validate the returned `QueryResult` shape defensively
   (`context_validation.validate_query_result`).
5. Select records, applying an optional deterministic `max_records`
   bound (a prefix of the Query Layer's own already-sorted records —
   no new ordering logic).
6. Verify attribution is present for content-bearing categories
   (`context_validation.ensure_attribution_present`).
7. Verify boundary disclosure material is present
   (`context_validation.ensure_boundary_disclosure_present`).
8. Assemble a `RepositoryIntelligenceContextPackage` with the
   attribution bundle, limitation bundle, boundary disclosure bundle
   (plus a package-level `NON_AUTHORITY_DISCLAIMER`), and context
   metadata.

Every fail-closed condition raises `AdvisoryContextBuilderError`, a
single exception type at the consumption boundary that wraps both
underlying Query Layer failures (`QueryExecutionError`,
`SnapshotCompatibilityError`, `SnapshotLoadError`) and
Advisory-context-layer validation failures
(`AdvisoryContextValidationError`), without repairing, guessing, or
working around the underlying cause.

## 4. Context Assembly Pipeline

The implemented pipeline follows the 122D plan's nine stages:

1. **Advisory request intake**: the CLI or a caller constructs an
   `AdvisoryContextRequest` with a declared `advisory_purpose`,
   category, optional target, and optional `max_records` bound.
2. **Repository Intelligence query preparation**:
   `AdvisoryContextRequest.to_query_request()` translates the request
   into an existing `QueryRequest`, using only the Query Layer's six
   existing supported categories.
3. **Read-only Query Layer invocation**: `execute_query` is called
   unchanged against an existing Repository Knowledge Snapshot
   artifact.
4. **Context selection**: the Query Result's already-sorted records are
   truncated to `max_records` if provided — no additional inference or
   relevance ranking.
5. **Attribution preservation**: the Query Result's `attribution` tuple
   is carried forward unchanged into `attribution_bundle`.
6. **Limitation propagation**: the Query Result's `limitations` tuple
   is carried forward unchanged into `limitation_bundle`; a single
   additive `context_bound` limitation is appended only when
   `max_records` truncation actually occurred.
7. **Boundary disclosure propagation**: the Query Result's
   `boundary_disclosures` and `disclaimers` are carried forward
   unchanged into `boundary_disclosure_bundle`, alongside the
   package-level `non_authority_disclaimer`.
8. **Advisory context package assembly**: `RepositoryIntelligenceContextPackage`
   is constructed from the above, plus `context_metadata` (advisory
   purpose, the originating query request, source artifact identity,
   result status, unknowns, selected record count, and an assembly
   timestamp).
9. **Advisory delivery**: `serialize_context_package()` produces
   deterministic JSON; the CLI prints it to stdout and/or an
   `--output` file. Delivery confers no authority.

## 5. Query Layer Integration

The builder's only Repository Intelligence access path is
`pcae.repository_intelligence.query.query_engine.execute_query`,
called with an unmodified `QueryRequest`. The builder:

- never reads a Repository Knowledge Snapshot artifact file directly;
- never reruns the Track 120 snapshot generator;
- never scans repository source, test, doc, or schema files;
- never inspects git history;
- introduces no new query category — `SUPPORTED_CONTEXT_CATEGORIES` is
  imported directly from `query_request.SUPPORTED_QUERY_CATEGORIES`,
  never redefined or extended.

`src/pcae/repository_intelligence/query/` was not modified by this
phase.

## 6. Context Package Description

`RepositoryIntelligenceContextPackage` contains exactly the five
elements the 122B/122D contracts and plans require:

- `selected_repository_intelligence`: the deterministic record subset
  chosen by context selection (a tuple of dicts, unmodified from the
  Query Result's own record shape).
- `attribution_bundle`: the Query Result's attribution, carried
  forward unchanged.
- `limitation_bundle`: the Query Result's limitations, plus any
  additive `context_bound` limitation.
- `boundary_disclosure_bundle`: `boundary_disclosures`, `disclaimers`,
  and `non_authority_disclaimer`.
- `context_metadata`: `advisory_purpose`, `query_request` (category and
  target), `source_artifact`, `result_status`, `unknowns`,
  `record_count`, and `assembly_timestamp`.

`to_dict()` additionally reports a `determinism` block stating the
package's own reproducibility rule, mirroring `QueryResult.to_dict()`'s
existing pattern. No reasoning output, recommendation, or decision
field is present anywhere in the package (verified by
`test_context_package_contains_no_reasoning_or_recommendation_fields`).

## 7. Attribution Behavior

Every Repository Intelligence element included in the context package
preserves provenance:

- `attribution_bundle` is the Query Result's own attribution, carried
  forward unchanged;
- `ensure_attribution_present` fails closed
  (`AdvisoryContextValidationError` → `AdvisoryContextBuilderError`) if
  any content-bearing category (`entity_lookup`, `capability_lookup`,
  `architectural_contract_lookup`, `attribution_lookup`) selects
  records but the Query Result returned no attribution for them;
- `limitation_lookup` and `boundary_lookup` are exempted from this
  check, mirroring the Query Layer's own `_collect_attribution`
  exemption for non-content-bearing categories.

Missing attribution on a content-bearing record remains a context
assembly failure, exactly as required.

## 8. Limitation Propagation

Every limitation present in the Query Result propagates unchanged into
`limitation_bundle`. The builder never drops or narrows an inherited
limitation. It may add exactly one additive `context_bound` limitation
when `max_records` truncates the selected record set — this addition
never replaces or narrows an inherited limitation, it only discloses
the truncation itself.

## 9. Boundary Disclosure Propagation

Every boundary disclosure and disclaimer present in the Query Result
propagates unchanged into `boundary_disclosure_bundle`.
`ensure_boundary_disclosure_present` fails closed if a Query Result
carries neither `boundary_disclosures` nor `disclaimers` at all — a
condition that should never occur against any genuine Track 120/121
artifact, since the Query Layer itself always attaches snapshot-level
boundary material regardless of query category or result status. Every
package additionally carries a package-level `non_authority_disclaimer`
restating that it is not Evidence, not Repository State, and not a
Decision Evaluation output.

## 10. Deterministic Guarantees

Equivalent Query Layer results plus an equivalent Advisory context
request produce an equivalent logical Advisory context package.

The implementation uses:

- the Query Layer's own deterministic record ordering, truncated
  deterministically (a fixed-length prefix) rather than re-sorted;
- deterministic attribution and limitation ordering, inherited
  unchanged from the Query Result;
- stable JSON formatting with sorted keys.

It uses no randomness, probabilistic ranking, AI inference, semantic
summarization, filesystem-order-dependent results, network calls, or
hidden mutable caches.

**Assembly timestamp note:** `context_metadata.assembly_timestamp` is a
declared wall-clock value, matching the 122D plan's "assembly
timestamp" metadata element. It is explicitly excluded from the
package's *logical* equality guarantee — reproducibility (122B S14)
requires that "a context package assembled twice from the same
Repository Knowledge Snapshot and the same advisory request must be
logically identical," not byte-identical. Focused tests verify logical
equality by comparing `to_dict()` output with `assembly_timestamp`
excluded.

## 11. Read-Only Guarantees

The implementation never:

- modifies Repository Intelligence, including Repository Knowledge
  Snapshot artifacts;
- invokes Repository Intelligence generation;
- rescans repository contents;
- executes repository code;
- invokes shell commands;
- invokes subprocesses;
- invokes AI providers;
- invokes external APIs;
- mutates runtime state;
- mutates Repository State;
- mutates Evidence;
- performs Advisory reasoning;
- performs Decision Evaluation.

Focused tests verify the queried snapshot file hash is unchanged before
and after context assembly.

## 12. Unknown and Fail-Closed Handling

The builder fails closed for:

- invalid context request (unsupported category, empty
  `advisory_purpose`, missing required target, non-positive
  `max_records`);
- invalid Query Layer result (missing required result fields or
  missing source artifact schema-version metadata);
- missing attribution on a content-bearing selected record;
- missing boundary disclosure material;
- unsupported Repository Intelligence schema version (propagated from
  the Query Layer's own `SnapshotCompatibilityError`);
- corrupted Repository Intelligence response (propagated from the
  Query Layer's own `SnapshotLoadError`);
- missing Repository Intelligence snapshot (propagated from the Query
  Layer's own `SnapshotLoadError`).

An `unknown` result status (e.g. an unmatched entity/capability target)
is represented explicitly in `context_metadata` (`result_status`,
`unknowns`) rather than treated as a failure — this mirrors the Query
Layer's own bounded-unknown handling; no inference is used to fill
missing data.

## 13. Verification

Added 21 focused tests in
`tests/test_phase_122e_repository_intelligence_advisory_context.py`
covering:

- deterministic entity context assembly with attribution, limitation,
  and boundary preservation;
- capability context missing-data unknown handling;
- limitation/boundary lookup categories never requiring attribution;
- repeated deterministic execution (logical equality excluding
  `assembly_timestamp`);
- deterministic JSON serialization (compact and pretty);
- invalid context request rejection (unsupported category, empty
  purpose, missing target, non-positive `max_records`);
- unsupported category rejection at the builder level;
- missing snapshot rejection;
- corrupted Repository Intelligence rejection;
- unsupported schema version rejection;
- missing attribution rejection;
- missing boundary disclosure rejection;
- `max_records` bound with disclosed `context_bound` limitation;
- read-only snapshot-file preservation;
- absence of reasoning/recommendation/decision fields;
- CLI JSON output, missing-snapshot failure, and `--output` file
  writing.

Also ran as regression:

- `tests/test_phase_121e_repository_intelligence_query.py` (15 tests,
  unaffected — Query Layer untouched);
- `tests/test_phase_120e_repository_knowledge_snapshot.py` (14 tests,
  unaffected — Repository Knowledge Snapshot generator untouched);
- full `fast_green` suite: 4390/4390 passed.

## 14. Future Extension Points

Future phases may extend Advisory context assembly only through
governed contract/plan work. Deferred capabilities, unchanged from
122D S16:

- Historical Memory consumption;
- Dependency Knowledge Graph consumption;
- Change Impact consumption;
- Advisory Intelligence Context Package consumption;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- execution planning;
- execution capability;
- `AdvisoryContextPackage` (115W) section placement decision;
- context package persistence;
- any query category beyond the Query Layer's existing six;
- Advisory runtime integration or wiring into any existing Advisory
  Provider, Repository Skill, Decision Evaluation, or lifecycle
  command.

## 15. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking inherited
  tooling/reporting issue.
- 119AB phase-id comparison bug: non-blocking inherited
  tooling/reporting issue.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking inherited reporting detail.

## 16. Acceptance

122E is complete when the Advisory Context Builder prototype is
implemented, focused tests and Query Layer/Repository Knowledge
Snapshot regression tests pass, deterministic context assembly is
verified, attribution/limitation/boundary preservation is verified,
fail-closed behavior is verified, `fast_green` passes, runtime remains
`Observed` / `observe` / execution unavailable, no Advisory reasoning
or Decision Evaluation integration occurs, and the recommended next
phase is 122F - Repository Intelligence Advisory Consumption
Verification.
