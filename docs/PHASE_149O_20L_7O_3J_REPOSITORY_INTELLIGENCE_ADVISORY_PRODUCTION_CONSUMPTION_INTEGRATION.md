# Phase 149O.20L.7O.3J — Repository Intelligence → Advisory Production Consumption Integration

**Status:** COMPLETE
**Phase type:** BOUNDED SOURCE-MODIFYING INTEGRATION. One production file changed. No architecture redesign, no new authority semantics, no execution enablement.
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## Objective

Move the existing, already-built-and-tested Repository Intelligence (RI)-backed Advisory-context bridge (`advisory/context/advisory_context_builder.py::build_advisory_context()`) from `implemented → tested → CLI-consumed` to `production-consumed → automatically orchestrated by the real Advisory path`, per the human's Plan A / Candidate C selection from 149O.20L.7O.3I. Informational/contextual only: Repository Intelligence context never becomes authority.

## v0.4.1 baseline

Verified at phase entry (re-derived, not trusted from memory):

```
git status --short                        => (empty, clean)
git rev-list --count origin/main..HEAD    => 0
git rev-parse HEAD == git rev-parse origin/main => 3537ad15cd59bc048d800d4cc7131752769500bf
git rev-parse v0.4.1^{commit}             => 9869cb65d890b70d8649ddd4216ffda4e7d98df5
pcae health                               => healthy
pcae check                                => passed
pcae status coherence                     => coherent
pcae doctor task-memory                   => warnings only (pre-existing tasks/DONE.md sync-debt, unrelated)
pcae push check                           => nothing_to_push
pcae runtime inspect                      => Observed / observe / unavailable
pcae notify status                        => Telegram configured, enabled, ready
pcae phase-report show --latest           => Phase 149O.20L.7O.3I, status completed, report complete
```

## 3I selection

Human selected **Plan A — Candidate C only** (Repository Intelligence → Advisory production consumption), narrow first cut, no automatic snapshot regeneration in this cut. Candidate A (rollback readiness) and Candidate B (runtime preflight) explicitly deferred, not touched this phase.

## Pre-integration Advisory graph

Re-derived directly from source, not trusted from 3I's prose:

- **Real production Advisory entry point:** `pcae advisory check` (`commands/advisory.py::run_advisory_check`) → `core/advisory.py::build_advisory()`.
- `build_advisory()` imported only `pcae.core.permission_broker` — zero references to Repository Intelligence or `pcae.advisory.context` anywhere.
- `build_advisory()` inputs: `repo_root, requested_command, requested_action, requested_files, health_passed, check_passed, human_review_present, human_approval_present, accepted_risk_present`. Output: a flat JSON-serializable dict (`would_*` decision fields, broker/shell-gate evidence, operator messaging, always-`False` `performed_flags`).
- `core/current_acting_model_advisory_provider.py` (Phase 115S "AdvisoryProvider" concept) confirmed to be an **entirely different, unrelated Advisory concept** — stateless, not wired into any production command, used only by tests/prototype helpers. Not the real production path; not touched.

## RI context-builder graph

- `advisory/context/advisory_context_builder.py::build_advisory_context(snapshot_path, request)` — already fully built and tested. Calls `repository_intelligence.query.query_engine.execute_query()` exclusively; never re-scans the repository, never re-runs the snapshot generator.
- `AdvisoryContextRequest(category, advisory_purpose, target, max_records)` — `category` must be one of `entity_lookup / capability_lookup / architectural_contract_lookup / attribution_lookup / limitation_lookup / boundary_lookup` (identical to the Query Layer's own six categories; introduces no new category). `entity_lookup` matches on `entity_id`/`entity_name`/`entity_path` — a repository-relative file path is an existing, valid lookup target, not an invented one.
- **Sole caller prior to this phase:** `commands/advisory_context.py::run_advisory_context_build` (the manual `pcae advisory context build` CLI command), which required an explicit `--snapshot` path and an explicit `--entity`/`--capability`/`--contract` target.
- Canonical snapshot location already established by the existing write pipeline: `repository_intelligence/persistence.py::DEFAULT_OUTPUT_SUBDIR = "repository-intelligence"`, writing `<repo_root>/.pcae/repository-intelligence/latest.json` (overwritten each generation run) plus a `snapshots/<timestamp>.json` per run. This phase reads `latest.json` at that literal, pipeline-defined path — not a directory scan/"most recent file" heuristic.
- `snapshot_loader.load_snapshot()` fails closed (`SnapshotLoadError`/`SnapshotCompatibilityError`) for missing file, invalid JSON, or incompatible `executable_schema_version`; these already propagate through `AdvisoryContextBuilderError`.

## Exact missing edge

`core/advisory.py::build_advisory()` → `build_advisory_context()`. No CLI shell-out, no subprocess, no text parsing of CLI output — a direct, in-process Python function call, exactly the preferred shape per the governing brief.

## Architectural ownership

`core/advisory.py` (Advisory core) owns context composition; RI is coupled there, not to any model/provider module. `core/current_acting_model_advisory_provider.py` was not modified and is not part of this integration — confirmed unrelated per the pre-integration graph above.

## Context contract

No new Advisory input contract was invented. `build_advisory()`'s existing `requested_files: list[str] | None` parameter is reused as the `entity_lookup` target (first requested file) when present; `boundary_lookup` (which requires no target and always resolves, per `query_engine.py`) is used as the fallback when no files are supplied — a pre-existing, always-available query category, not an invented one. The Advisory output dict gains exactly one new, additive key, `repository_intelligence_context`; no existing key was renamed, removed, or changed in meaning.

## Automatic acquisition behavior

**READ-ONLY QUERY.** `_gather_repository_intelligence_context()` only reads `.pcae/repository-intelligence/latest.json` (if present) via the existing `execute_query`/`load_snapshot` path and calls `git rev-parse HEAD` (read-only) for the staleness comparison below. It writes nothing, generates no snapshot, invokes no change-impact/historical-memory/dependency-graph subsystem, and creates no new `.pcae/` artifact. This is a **narrower** acquisition mode than the RI Service's own 9-stage pipeline — it consumes only the Query Layer, exactly as `build_advisory_context()` always has.

## Missing/stale/invalid behavior

- **Missing snapshot:** `available: False`, `unavailable_reason: "no_repository_intelligence_snapshot_found"`. Advisory's broker-derived verdict is unaffected (verified by test; see below).
- **Invalid/corrupt snapshot (malformed JSON, incompatible schema version):** `AdvisoryContextBuilderError` is caught (not propagated); `available: False`, `unavailable_reason: "repository_intelligence_context_build_failed"`, `unavailable_detail` carries the underlying message. This is a **deliberate fail-soft divergence** from `build_advisory_context()`'s own fail-closed default for its CLI caller, scoped to this one call path only — the CLI's own fail-closed behavior (`commands/advisory_context.py`) is untouched.
- **Stale snapshot:** the snapshot's own already-recorded provenance field (`envelope.repository_context.repository_commit`, exposed via `source_artifact.repository_commit`) is compared against the current `git rev-parse HEAD` (reusing the existing `repository_intelligence.historical_memory.git_source.git_head_commit_sha()` read-only helper — no new subprocess call site was introduced). On divergence, a `possibly_stale_snapshot` limitation entry is appended to the existing `limitation_bundle`, using the same free-form `{limitation_type, limitation_description}` shape the Query Layer and Advisory-context builder already use elsewhere (e.g. `context_bound`, `missing_data`, `scope_limitation`). No new freshness *policy* was invented — no TTL, no automatic regeneration, no blocking behavior — only a factual disclosure derived from data the snapshot already carries.

## Side effects

None beyond one `git rev-parse HEAD` read. No file is written, no snapshot is regenerated, no `.pcae/` state is mutated.

## Provenance

`source_artifact` (`artifact_id`, `snapshot_id`, `executable_schema_version`, `repository_commit`) and the full `attribution_bundle`/`limitation_bundle`/`boundary_disclosure_bundle` produced by `build_advisory_context()` are passed through unflattened (`RepositoryIntelligenceContextPackage.to_dict()`), with the staleness limitation appended using the same structured shape. Nothing is collapsed into anonymous text.

## Identity/repository isolation

The snapshot path is derived from the same `repo_root` passed into `build_advisory()` — the identical value that already anchors every other part of the advisory envelope (`repository_root` field, permission-broker evaluation). No global/ambient snapshot location is consulted. Verified by test: a `repo_root` with no snapshot never reads another repository's snapshot.

## Authority non-flow

Verified by test (`test_repository_intelligence_presence_never_changes_broker_or_advisory_decision`): identical evidence inputs produce identical `broker_decision`/`advisory_decision`/`would_*`/`hard_block_present`/`authorization_granted`/`execution_authorized` whether or not Repository Intelligence context is present. `repository_intelligence_context` is inserted into the return dict *after* `advisory_decision`/`broker_decision`/all `would_*` fields are already fully computed from `build_permission_broker()`'s output alone — RI data cannot causally influence those fields since they are computed first and read from broker output exclusively.

## Permission Broker isolation

Static re-confirmation (test `test_no_permission_broker_coupling_in_repository_intelligence_or_advisory_context_modules`): zero occurrences of `permission_broker`/`PermissionBroker` anywhere under `src/pcae/repository_intelligence/` or `src/pcae/advisory/context/` — unchanged from 3I's finding. `mutation_permission.py`/`permission_broker.py` were not modified and were re-confirmed to contain no reference to `repository_intelligence`/`advisory` context modules.

## Provider/model boundary

No model/provider module (`current_acting_model_advisory_provider.py` or otherwise) was touched. No LLM call, no OpenRouter call, no network dependency was added.

## CLI compatibility

`pcae advisory context build` (the manual diagnostic CLI) is byte-unmodified and independently re-verified working end-to-end this phase (see Tests). `pcae advisory check` now additionally emits `repository_intelligence_context`; all pre-existing fields/behavior are unchanged (verified by the full pre-existing `test_advisory_mode.py` suite passing unmodified).

## Post-integration graph

```
pcae advisory check (real production entry point)
  → core/advisory.py::build_advisory()
      → build_permission_broker()  [unchanged — sole authority source]
      → _gather_repository_intelligence_context()  [NEW, additive, read-only]
          → build_advisory_context()  [existing bridge, now with two callers]
              → execute_query() → RI Query Engine → latest.json snapshot
      → returns {..., repository_intelligence_context}

pcae advisory context build (manual CLI, unchanged)
  → build_advisory_context()  [same canonical implementation, second caller]
```

Both the CLI and the real Advisory production path now consume the identical, single `build_advisory_context()` implementation — the service-boundary requirement (§6) is met without any extraction, since the function was already a plain, reusable, non-CLI-coupled function.

## Manual choreography eliminated

Before this phase, `pcae advisory check`/`status` never acquired RI context; a human had to separately run `pcae advisory context build --snapshot ... --entity/--capability/--contract ...` and manually cross-reference the two outputs. After this phase, `pcae advisory check` acquires RI context automatically whenever a snapshot is present, with no CLI prerequisite (verified end-to-end by `test_cli_advisory_check_reflects_automatic_repository_intelligence_context`, which invokes only `pcae advisory check` as a subprocess and asserts `repository_intelligence_context` is present in its own output). The manual command remains available and unmodified for diagnostic/control use.

## Tests

New file: `tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py` — 18 tests, all `fast_green`-marked, all passing:

- Automatic consumption without manual CLI prerequisite (2 tests)
- Correct entity-lookup identity binding from `requested_files` (1)
- Missing RI state → fail-soft, broker decision unaffected (1)
- Invalid/corrupt snapshot → fail-soft, not raised (1)
- Incompatible schema version → fail-soft, not raised (1)
- Stale snapshot → disclosed as limitation (1); matching-commit snapshot → not flagged stale (1)
- Cross-repository isolation — wrong repo's snapshot never consumed (1); canonical `latest.json` path is not a directory-scan heuristic (1)
- Deterministic repeated consumption (1)
- Authority non-flow — RI presence never changes broker/advisory decision (1); no authority-shaped field synthesized (1)
- Static Permission Broker isolation re-confirmation (1)
- Static no-self-CLI-subprocess check on `core/advisory.py` (1)
- CLI regression — manual `advisory context build` still functions (1); `advisory check` reflects automatic RI context end-to-end via subprocess (1)
- Runtime boundary — advisory check never activates execution (1)

## Regressions

- **Advisory regression:** `tests/test_advisory_mode.py` (166+ tests) — all pass unmodified.
- **RI regression:** `tests/test_phase_122e_repository_intelligence_advisory_context.py`, `tests/test_advisory_context_package.py`, and the full `advisory`/`repository_intelligence` test corpus (2848 tests across 22 files) — all pass except 7 pre-existing failures independently reproduced against the unmodified pre-3J baseline via `git stash` (see below) — confirmed unrelated to this phase.
- **Permission Broker/rollback/push regression:** no source overlap — `mutation_permission.py`, `permission_broker.py`, `commands/push.py`, rollback dispatch paths were not modified and were statically re-confirmed to contain no reference to the new integration.

### Pre-existing-failure re-confirmation methodology

7 failures observed in a broad `advisory|repository_intelligence|permission_broker|mutation_permission` sweep (`test_no_new_directory_added_for_advisory` ×2, `test_permission_broker_consumer_scope_inventory`, `test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`, `test_no_permission_broker_request_construction_uses_approval_present_true`, `test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`, `test_rae_permission_broker_and_agent_do_not_reference_wave5`) were re-run against the exact pre-3J working tree via `git stash push -u` / `git stash pop` and failed **identically** — confirmed pre-existing, not attributable to this phase.

## Fast Green

- **Baseline** (pre-3J working tree, via `git stash`): `336 failed, 8731 passed, 5 skipped, 9 errors` (146s, `-n auto`).
- **Current** (post-3J): `352 failed, 8733 passed, 5 skipped, 9 errors` (138s, `-n auto`).
- **Node-ID diff:** exactly 16 new FAILED node IDs, 0 resolved. All 16 are of the literal form "no `src/pcae` file was touched/dirty since a fixed historical phase-entry commit" (e.g. `test_git_status_touches_no_src_pcae_or_contract_file`, `test_no_src_pcae_files_dirty_in_working_tree`, `test_only_expected_production_files_changed`) — pre-existing, structural self-referential tripwires (documented technical debt from prior phases: any legitimate `src/pcae/` source change necessarily trips every historical phase's own "nothing changed since my phase" freeze assertion). This phase is explicitly source-modifying, so tripping these was expected and is not a functional regression in RI/Advisory/Permission-Broker behavior.
- Arithmetic reconciliation: `8731 (baseline passed) − 16 (flipped pass→fail) + 18 (this phase's new tests) = 8733` — fully accounted for.
- **Attributable regressions: 0.**

## Runtime

`pcae runtime inspect` before and after: `Observed / observe / unavailable` — byte-identical, unchanged.

## Deferred Candidate A/B

Not implemented this phase, per the human's Plan A selection: rollback readiness/evidence auto-generation (Candidate A) and runtime preflight capability-aware routing (Candidate B) remain exactly as characterized in 149O.20L.7O.3I.

## Independent verification requirement

This phase does not self-certify. See Recommended next phase below.

## Final verdict

```text
REPOSITORY INTELLIGENCE → ADVISORY PRODUCTION CONSUMPTION:
IMPLEMENTED

REAL ADVISORY PATH:
AUTO-CONSUMES EXISTING RI CONTEXT BUILDER

MANUAL ADVISORY-CONTEXT CLI PREREQUISITE:
REMOVED

RI PROVENANCE:
PRESERVED

RI LIMITATIONS:
PRESERVED

RI AUTHORITY:
NONE / UNCHANGED

PERMISSION BROKER:
NOT INFLUENCED BY RI CONTEXT

MODEL/NETWORK EXPANSION:
NONE

RUNTIME:
Observed / observe / unavailable

ATTRIBUTABLE REGRESSIONS:
0

INDEPENDENT END-TO-END VERIFICATION:
MANDATORY NEXT
```

## Recommended next phase

**149O.20L.7O.3J.1 — Independent End-to-End Repository Intelligence / Advisory Consumption Verification.** Not begun. Must independently reconstruct the pre/post production call graph, prove the real Advisory path invokes the RI context builder without a manual CLI prerequisite, verify correct repo/task/snapshot binding, test missing/stale/corrupt RI, verify provenance/limitations, verify authority non-flow, verify Permission Broker isolation, verify no model/network/runtime expansion, attempt cross-repo context leakage, rerun Advisory/RI regressions, and adjudicate all findings.

Do not begin 3J.1 automatically. Stop after 3J.
