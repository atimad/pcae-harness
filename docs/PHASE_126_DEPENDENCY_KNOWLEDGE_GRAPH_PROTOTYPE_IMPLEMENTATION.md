# Phase 126E - Dependency Knowledge Graph Prototype

## 1. Purpose

Phase 126E implements the first deterministic, read-only Dependency
Knowledge Graph Builder exactly as defined by the 126A architecture,
126B contract, 126C verification, and 126D implementation plan. This
is the first phase in Track 126 to touch `src/pcae/` source code.

The implementation remains strictly observational: no graph traversal,
no semantic reasoning, no probabilistic relationships, no execution
capability, and no runtime behavior change.

## 2. Implementation Summary

Added `src/pcae/repository_intelligence/dependency_graph/` (new
package):

- `graph_builder.py` — deterministic node/edge/claim construction from
  an existing Repository Knowledge Snapshot, consumed exclusively
  through the Track 121 Query Layer.
- `graph_validation.py` — independent, fail-closed re-validation of
  the assembled graph (126D pipeline stage 10).
- `persistence.py` — write-only persistence, reusing Track 124's
  `serialize_deterministic_json`.
- `graph_generator.py` — top-level orchestration (the package's sole
  external entry point), mirroring `snapshot_generator.py`'s shape.

Wired a governed CLI command,
`pcae repository-intelligence dependency-graph generate`, consistent
with the existing `snapshot generate` / `query` / `change-impact`
commands (`src/pcae/commands/repository_intelligence.py`,
`src/pcae/cli.py`).

Added `tests/test_phase_126e_dependency_knowledge_graph_prototype.py`
(38 tests).

## 3. Graph Builder Summary

The builder follows 126D's twelve-stage pipeline exactly:

1. **Input validation** — `load_snapshot()` (Track 121's own Query
   Layer loader) validates the source artifact's shape and executable
   schema version before any extraction begins.
2. **Repository Intelligence loading** — entity identifiers are
   discovered from the validated snapshot, then each entity is
   individually re-fetched via `execute_query(..., QueryRequest(
   category="entity_lookup", target=entity_id))`, exactly mirroring
   Track 123's own per-target Query Layer consumption pattern.
   Snapshot-level limitations and boundary material are fetched via
   `limitation_lookup`/`boundary_lookup` queries.
3. **Entity extraction** — each RKS `entity_type` is translated to a
   DKG `node_type` via the frozen mapping table (126B §4.3, 126D
   §5.1); one node is also synthesized once per graph for the
   repository root itself.
4. **Relationship extraction** — one `related_to` (containment) edge
   is declared from the repository root to every other node, per 126B
   §5.2's `contains` -> `related_to` mapping. No other edge type is
   produced, because the current Track 120 generator does not declare
   any relationship beyond top-level path existence (126D §5.2's
   critical finding, now confirmed against real generated output).
5. **Graph construction** — nodes, edges, and `dependency_claims`
   (one `node_existence` claim per node, one `edge_existence` claim
   per edge) are assembled with the frozen identifier scheme (126D
   §7): `node_id = f"node:{entity_path}"`,
   `edge_id = f"edge:{edge_type}:{source}->{target}"`.
6. **Metadata attachment** — `graph_metadata` is populated including
   `graph_kind: "dependency"`, `graph_directionality: "directed"`, and
   `graph_completeness_state: "partial"` (resolving 126C Finding 3
   exactly as 126D §12 required — never `complete_claimed_by_source`
   for v1 output).
7. **Provenance attachment** — every node/edge/claim carries
   `source_attribution` traced to the specific RKS entity it was
   derived from.
8. **Limitation propagation** — inherited RKS `snapshot_limitations`
   are propagated unchanged and merged with two graph-specific
   limitations: the v1 containment-precision limitation (126B §5.2)
   and the "no imports/depends_on edges yet" limitation (126D §5.2),
   plus a symmetric "no class/function nodes" limitation (126B §4.3).
9. **Boundary disclosure propagation** — `boundary_disclosures` and
   `disclaimers` are propagated from the Query Layer's `boundary_
   lookup` result; the frozen `dependency_knowledge_graph_snapshot_
   disclaimer` const string is attached unchanged.
10. **Graph validation** — `graph_validation.validate_graph()`
    independently re-checks the assembled graph (Section 5 below).
11. **Deterministic serialization** — Track 124's
    `serialize_deterministic_json` (sorted keys, stable indent modes).
12. **Persistence** — `persistence.write_graph()`, writing to
    `.pcae/repository-intelligence/dependency-graph/` (distinct from
    the source snapshot's own `repository-intelligence/` directory).

## 4. Graph Model Summary

### 4.1 Node Mapping (Confirmed Against Real Generated Output)

Running the builder against a freshly generated Repository Knowledge
Snapshot from this repository produced 13 nodes: one synthesized
`repository` root, plus a 1:1 translation of every declared RKS
entity — `source_file` entities became `file` nodes, directory
entities (RKS's own `module` classification) remained `module` nodes,
and the fixed `tests`/`schemas/repository_intelligence` entities
became `test`/`schema` nodes respectively. This exactly matches 126D
§5.1's frozen mapping table with zero deviation.

### 4.2 Edge Mapping (Confirmed Against Real Generated Output)

The same run produced 12 edges, every one a `related_to`-typed
containment edge from the repository root to a non-root node. Zero
`depends_on`, `references`, `produces`, `consumes`, `verifies`, or
`documents` edges were produced — confirming 126D §5.2's critical
finding empirically, not just as a prediction: the current Track 120
generator's own declared scope ("does not parse file contents,
imports, or symbols") makes this the correct, honest v1 output, not a
builder defect.

### 4.3 Class/Function Nodes

Zero class or function nodes were produced or are producible by this
builder, consistent with 126B §4.3's explicit v1 scope exclusion.

## 5. Validation Summary

`graph_validation.validate_graph()` independently re-checks, and fails
closed on:

- unique `node_id` values;
- unique `edge_id` values;
- every edge's `source_node_id`/`target_node_id` resolves to a real
  node in the same graph;
- every `node_type` is a member of the frozen enum;
- every `edge_type` is a member of the frozen enum;
- deterministic ordering (nodes/edges sorted by identifier);
- `graph_metadata` required-field completeness;
- `source_attribution` presence on every node/edge/claim;
- `limitations` presence on every node/edge/claim, plus snapshot-level
  `snapshot_limitations`;
- `boundary_disclosures`/`disclaimers`/disclaimer-const presence.

This validation stage does not trust the builder's own construction —
it is a genuinely independent re-check against the same real, assembled
graph dict, exercised by dedicated negative tests (duplicate
identifiers, invalid categories, dangling edge endpoints).

## 6. Serialization Summary

Persistence reuses Track 124's `serialize_deterministic_json` directly
(no parallel serialization logic introduced), resolving 126C Finding 2
exactly as 126D §9 required. Verified: two independent generation runs
against the same source snapshot produce byte-identical output except
`envelope.generated_at_utc` and `snapshot_identity.snapshot_created_
at_utc` (the only approved non-substantive fields, mirroring 120B §6's
rule for Repository Knowledge Snapshot).

## 7. Persistence Summary

Writes only, to `.pcae/repository-intelligence/dependency-graph/`
(`latest.json`, overwritten each run, plus a timestamped file under
`graphs/`, one per run) — a location distinct from Track 120's own
`repository-intelligence/` snapshot directory, so the two artifact
families are never confused. Persistence never reads back or mutates
the source snapshot; verified by an explicit regression test
(`test_persistence_never_mutates_source_snapshot`).

## 8. Regression Results

Independently re-executed in this implementation session:

- Repository Knowledge Snapshot
  (`tests/test_phase_120e_repository_knowledge_snapshot.py`): 14
  passed.
- Query Layer
  (`tests/test_phase_121e_repository_intelligence_query.py`): 15
  passed.
- Advisory Context Builder
  (`tests/test_phase_122e_repository_intelligence_advisory_context.py`):
  22 passed.
- Change Impact Builder plus 124E hardening tests
  (`tests/test_phase_123e_repository_intelligence_change_impact.py`
  `tests/test_phase_124e_repository_intelligence_hardening.py`): 21
  passed.
- New Dependency Knowledge Graph tests
  (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`):
  38 passed.
- Combined run of all five suites together: 110 passed.
- fast_green (`python -m pytest -m "fast_green" -n auto -ra
  --durations=0`): 4390 passed, 0 failed (an initial run before this
  phase's own task contract existed showed one unrelated,
  task-lifecycle-state-dependent failure —
  `test_dry_run_simulation.py::test_pytest_dry_run_not_blocked` —
  resolved once the task contract existed, matching the same pattern
  documented in 125A/125G; not a regression from this phase's changes).

## 9. Deterministic Generation Results

Independently verified via direct Python invocation (not just test
assertions): two calls to `generate_dependency_graph()` against the
identical source snapshot produced graphs whose full content, with
only the two approved timestamp fields normalized, compared byte-equal
(`==`) as parsed JSON. Node and edge counts were stable across runs.

## 10. Compatibility Confirmation

No file under `schemas/`, `src/pcae/repository_intelligence/
snapshot_builder.py`, `src/pcae/repository_intelligence/snapshot_
generator.py`, `src/pcae/repository_intelligence/persistence.py`,
`src/pcae/repository_intelligence/query/`, `src/pcae/advisory/context/`,
or `src/pcae/repository_intelligence/change_impact/` was modified by
this phase — confirmed via `git status`/`git diff` scoping before
commit. The new `dependency_graph` package is purely additive.

- **Track 119 executable schemas** — unmodified; the builder consumes
  and produces the already-frozen `dependency_knowledge_graph_
  snapshot.schema.json` (119S/119T) without any schema change.
- **Track 120 Repository Knowledge Snapshot** — unmodified; the
  builder's only input.
- **Track 121 Query Layer** — unmodified; the builder's only access
  path into Repository Intelligence content.
- **Track 122 Advisory Context Builder** — unmodified; not consumed
  by this builder.
- **Track 123 Change Impact Builder** — unmodified; not consumed by
  this builder.

## 11. Confirmations

- **No graph traversal implemented.** No module in
  `dependency_graph/` walks, paths, or recursively explores the
  assembled graph; a dedicated test
  (`test_no_graph_traversal_module_exists`) confirms no
  `graph_traversal` module exists.
- **No reasoning implemented.** Every node and edge is a direct
  translation of already-declared Repository Knowledge Snapshot
  content; no inference, heuristic, or probabilistic logic exists
  anywhere in `graph_builder.py`.
- **No runtime behavior changed.** No module under
  `dependency_graph/` imports `subprocess`, invokes a shell, or touches
  runtime state; confirmed by AST-based import inspection
  (`test_builder_module_has_no_execution_related_imports`), following
  this codebase's established AST-over-substring-check convention.
- **Execution remains unavailable.** Independently re-confirmed via
  `pcae runtime inspect` (Section 13 below).

## 12. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail, non-blocking.
- Missing `PCAE_NOTIFY_ENABLED` during governed push environment:
  notification environment detail, non-blocking (resolved for this
  session by sourcing `~/.config/pcae/telegram.env` before governance
  validation).

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

This phase does not implement: graph traversal; dependency reasoning;
graph queries; graph database; recommendations; Advisory reasoning;
Decision Evaluation; execution planning; execution capability; runtime
plugins; AI integration. No schema file was changed.

## 15. Deferred Capabilities

Explicitly deferred, unchanged from 126B/126D: graph traversal;
dependency reasoning; impact reasoning; Historical Memory integration;
Advisory reasoning; Decision Evaluation; graph database; execution
planning; execution capability; AI reasoning.

## 16. Conclusion

Phase 126E implements the first deterministic, read-only Dependency
Knowledge Graph Builder exactly as scoped by 126A-126D, verified
end-to-end against a freshly generated real Repository Knowledge
Snapshot from this repository (not synthetic fixtures alone), and
confirmed byte-deterministic across repeated runs. All three 126C
findings and 126D's critical grounding predictions (the entity_type/
node_type enum mismatch and the near-absence of non-containment edges)
were independently confirmed against real generated output. No
traversal, reasoning, or execution capability was introduced. Runtime
remains `Observed`/`observe`/execution-unavailable.

Recommended next phase: 126F — Dependency Knowledge Graph Verification.
