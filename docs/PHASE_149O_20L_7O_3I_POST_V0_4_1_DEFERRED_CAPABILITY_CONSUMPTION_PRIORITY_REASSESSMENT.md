# Phase 149O.20L.7O.3I — Post-v0.4.1 Deferred Capability Consumption Priority Reassessment

**Status:** COMPLETE
**Phase type:** READ-ONLY STRATEGIC REASSESSMENT. No production source, CLI, contract, schema, or packaging-configuration file was modified. No integration was implemented. No priority was selected unilaterally.
**Phase-entry commit:** `7b9741cf308ecdf699b865876c7db15be2360cf9` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## 1. Objective

Phase 149O.20L.7O.3H.1 publicly released PCAE v0.4.1 (the independently verified rollback default-path Permission Broker integration). This phase re-derives, from current source (not from prior phase summaries), the priority order of the three deferred mature capability-consumption candidates first identified in 149O.20L.7O.3E and re-touched in 149O.20L.7O.3G:

1. rollback readiness/evidence auto-generation and internal consumption ("Candidate A");
2. runtime preflight disclosure / capability-aware orchestration ("Candidate B");
3. Repository Intelligence + Advisory-context consumption ("Candidate C").

The governing question: **which remaining mature capability should PCAE consume automatically next to increase usefulness and autonomy without weakening governance or prematurely enabling execution?** This phase produces a ranked proposal for human selection. It does not implement, select, or authorize any integration.

## 2. v0.4.1 baseline

Verified at phase entry:

```
git status --short                        => (empty, clean)
git status --branch --short               => ## main...origin/main
git rev-list --count origin/main..HEAD    => 0
git rev-parse HEAD                        => 7b9741cf308ecdf699b865876c7db15be2360cf9
git rev-parse origin/main                 => 7b9741cf308ecdf699b865876c7db15be2360cf9
git rev-parse v0.4.1^{commit}             => 9869cb65d890b70d8649ddd4216ffda4e7d98df5
git rev-parse v0.4.0^{commit}             => ea3f731ef50ea16985fd4a0562f0c091bb8109b2
pcae health                               => healthy
pcae check                                => passed
pcae status coherence                     => coherent
pcae doctor task-memory                   => warnings only (pre-existing tasks/DONE.md sync-debt entries predating this phase, unrelated)
pcae push check                           => nothing_to_push
pcae runtime inspect                      => Observed / observe / unavailable (unchanged)
source ~/.config/pcae/telegram.env        => succeeded (exit 0)
pcae notify status                        => Telegram configured, enabled, ready
pcae phase-report show --latest           => Phase 149O.20L.7O.3H.1, status completed, report complete
```

`git diff --name-status v0.4.1..HEAD -- src/pcae/` returns **zero files** — confirmed via direct re-run this phase. Every commit between the `v0.4.1` tag (`9869cb65`) and phase-entry HEAD (`7b9741cf`) is lifecycle/documentation bookkeeping (task open/close, phase-completion metadata/report sync, PROJECT_STATUS.md/CHANGELOG.md updates) from `149O.20L.7O.3H`/`3H.1`. This means: **no production behavior has changed since v0.4.1 shipped**, and every classification made by `149O.20L.7O.3E`/`3G` for the three candidates in this phase's scope is evaluated against source that is provably unchanged since those phases — this reassessment independently re-derives (not merely re-cites) each classification against current HEAD.

## 3. Current connected consumption graph (post-v0.4.1)

Re-confirmed by direct source read this phase (`src/pcae/commands/governance_auto_publication.py`, `src/pcae/commands/phase.py`, `src/pcae/core/mutation_permission.py`, `src/pcae/core/agent.py:94338-94376`):

```
Governed lifecycle path:
pcae phase complete
  → auto_publish_confirmed_session()          [commands/governance_auto_publication.py]
      → SessionApplicationService.find_session_by_subject_ref()  [deterministic lookup]
      → (only if SessionState == Confirmed)
          → publish_with_permission_gate()     [commands/publication_permission_gate.py]
              → mutation_permission.evaluate_publication_permission()  [Permission Broker]
                  → ALLOW → PublicationCoordinator.execute() → CHGR created (idempotent)
                  → DENY → no CHGR, phase-complete proceeds unaffected (informational only)

Rollback path:
pcae rollback --per-id X [--dry-run]
  → PER/ECP lookup, eligibility, divergence checks
  → dry_run? → readiness/evidence preview returned, zero mutation, zero broker call
  → RER created; divergence blocking? → return
  → HATP_MANDATORY? → evaluate_for_real_effect()   [pre-existing gate]
  → else → mutation_permission.evaluate_rollback_permission()  [agent.py:94356 — RELEASED in 149O.20L.7O.3F/3F.1]
       → ALLOW → restore/remove loop → execution record (RER)
       → DENY/failure → aborted_permission_denied, zero mutation
```

Treated as already-connected per the governing brief and independently re-confirmed, not re-integrated this phase: Interactive Workflow auto-detect/route; human decision pause/resume; CHGR downstream automatic consumption; Publication Execution Ownership auto-invocation; Permission Broker coverage for publication; Permission Broker coverage for rollback default dispatch; push Permission Broker consumption (`commands/push.py::_evaluate_push_permission`).

## 4. Consumption maturity model

Applied per candidate below (§5-7): IMPLEMENTED → VERIFIED → EXPOSED → PRODUCTION-CONSUMED → AUTO-ORCHESTRATED → INDEPENDENTLY E2E VERIFIED → RELEASED. `implemented` is never equated with `consumed`; `exposed` is never equated with `orchestrated` — each sub-capability below is classified individually rather than as one blended candidate-level label.

## 5. Rollback readiness/evidence assessment (Candidate A)

**Rollback path reconstruction** (`src/pcae/core/agent.py`, function `build_rollback_execution`, sole production caller `commands/agent.py:16264`):

| Component | Level reached | Evidence |
|---|---|---|
| Rollback readiness (a pre-computed "is a rollback for this promotion currently safe" artifact) | **NOT IMPLEMENTED** | No file/class/function named "readiness" tied to rollback exists anywhere in `src/pcae`; only unrelated historical design/pilot CLI subcommands (`write-rollback-verification`, `live-write-readiness`, `rollback-execution-pilot`) share the word. |
| Rollback evidence (dry-run preview) | **PRODUCTION-CONSUMED, human-triggered only** | `build_rollback_execution(root, per_id, dry_run=True, ...)` (`agent.py:94095`) is a real, safe, zero-mutation path (`agent.py:94195-94208`); exposed via `pcae rollback --dry-run`. `build_rollback_execution(` has exactly one caller in all of `src/pcae` — the CLI dispatch. |
| HATP/AG5 rollback approval evidence (`rollback_approval_evidence.py`) — a *different*, authority-scoped concept | PRODUCTION-CONSUMED, gated behind `HATP_MANDATORY` (currently inactive/deferred) | `agent.py:94279-94321`, `core/rollback_approval_evidence.py:1517`. |
| Permission Broker gate, default (non-HATP) path | **RELEASED** (v0.4.1, `149O.20L.7O.3F`) | `agent.py:94338-94376` — `mutation_permission.evaluate_rollback_permission`, independently E2E-verified in `3F.1`. |
| Permission Broker gate, HATP_MANDATORY path | RELEASED (pre-existing) | `agent.py:94266-94336`. |
| Dispatch (file restore/remove) | RELEASED | `agent.py:94378-94429`. |
| Execution record (RER) | RELEASED | `store_rollback_execution_record`; inspectable via `pcae rollback-execution show/list`. |
| Recovery/retry | PRODUCTION-CONSUMED, manual only | `pcae rollback-execution mark-interrupted` — bookkeeping only, no automatic retry/resume logic found. |

**Current manual choreography:** (1) operator must already hold a `per_id` from a prior `pcae promote` with `rollback_payload_available=True`; (2) operator manually runs `pcae rollback --per-id X --dry-run` to preview; (3) operator manually re-runs without `--dry-run` (plus `--hatp-evidence-id` under `HATP_MANDATORY`) to dispatch. No step auto-derives or persists readiness/evidence ahead of time; every dry-run recomputes from scratch and nothing from it is stored.

**Current internal consumption:** none. The rollback path does not consume readiness/evidence automatically anywhere.

**Missing edge (exact):** `PER completion (pcae promote) → automatic dry-run rollback-readiness derivation → persisted readiness/evidence artifact`. `build_rollback_execution(..., dry_run=True)` is the exact safe primitive already needed; the missing piece is a producer-side automatic call at promotion-completion time, plus a small persistence/schema for the resulting artifact.

### 6. Rollback readiness safety

| Property | Yes/No | Evidence |
|---|---|---|
| Non-effectful | Yes | Dry-run branch (`agent.py:94195-94208`) performs zero filesystem writes, zero RER persistence. |
| Deterministic | Yes | `file_plan` derived strictly from `PER.file_results` where `outcome="success"`; divergence check is a pure comparison against current repo state. |
| Idempotent | Yes | Re-running dry-run recomputes the same output for unchanged repo state; no accumulating side effect. |
| Local | Yes | Filesystem/git-state only, no network. |
| Authority-neutral | Yes, if implemented carefully | Every dry-run branch already carries `execution_allowed: False`. A new persisted readiness artifact would need an explicit non-authority disclaimer field (no such field exists today because no readiness concept exists yet) to avoid being misread as a go/no-go signal — i.e. `ready == authorized` and `evidence exists == rollback permitted` must be explicitly guarded against in the new artifact's design, not merely assumed absent. |

### 7. Rollback readiness freshness

No freshness/staleness semantics exist today because no readiness artifact exists to be stale. A directly reusable precedent exists in the sibling HATP approval-evidence subsystem: `RollbackApprovalValidationResult` enum (`VALID, MISSING, INVALID, STALE, REVOKED, UNAUTHORIZED_APPROVER, WRONG_SCOPE, SUPERSEDED`) and `RepositoryStateBinding(head_commit_sha, branch)` (`core/rollback_approval_evidence.py:169-181, 327-333`). This is real, tested design precedent in the exact same domain — not something to invent from scratch — but it is typed specifically to HATP approval decisions, not generic dry-run snapshots, so a new readiness artifact still needs its own binding/staleness contract. Missing artifact / conflicting artifact / changed repository state / changed PER / changed rollback plan: none of these currently have defined handling for a readiness artifact, because none exists; any implementation must define this explicitly (raises effort, per §9).

### 8. Rollback readiness reuse

The `RollbackApprovalBinding` pattern (`_compute_content_digest`, `RepositoryStateBinding` identity, explicit `revoke_rollback_approval_binding`) is a directly reusable architectural template for binding a new readiness artifact's identity to `(per_id, ecp_id, head_commit_sha)` rather than any heuristic "latest readiness" selection. This requires a **new schema** — `schema_resources/rollback_approval/` currently contains only `rollback_approval_binding.schema.json` and `rollback_approval_revocation.schema.json`, both approval-specific, not reusable as-is for a readiness/evidence artifact.

### 9. Rollback readiness user value

```
CURRENT
human performs several preparation commands
→ (after a promotion, if something breaks) cold-starts
  `pcae rollback --per-id X --dry-run` to first understand
  what a rollback would even look like
→ then invokes rollback for real

TARGET
pcae promote completes
→ PCAE auto-generates dry-run rollback readiness/evidence,
  persisted alongside the PER/ECP record
→ human decision to actually roll back remains theirs alone
→ if later needed, human finds pre-staged evidence instead
  of starting cold
```

Manual steps eliminated: the cold-start `--dry-run` invocation itself, performed only if/when a rollback later becomes necessary. Value is real but conditional — it only pays off if a promotion later actually needs reversing, which this repository's own history shows is rare.

### 10. Rollback readiness effort/risk

- **Implementation effort: S-M** — the compute primitive already exists and is safe; new work is (a) an automatic call site at promotion-completion, (b) a new small persistence/schema for the readiness artifact, (c) a freshness/binding contract modeled on (not copied from) `RollbackApprovalBinding`.
- **Authority risk: LOW** — no execution-capability change, no Permission Broker policy change, dry-run only, `execution_allowed=False` preserved throughout.
- **E2E testability: 4/5** — dry-run generation, staleness, missing/conflicting artifact, and restart/resume are all independently testable without touching real rollback execution.
- **User value: 3/5** — real but conditional on rollback events, which are rare in this repository's own history.

## 11. Runtime preflight assessment (Candidate B)

| Component | Level reached | Evidence |
|---|---|---|
| Runtime Registry (`RuntimeRegistry`) | IMPLEMENTED, VERIFIED | `core/runtime_registry.py` — constructed fresh/empty per call; "in-memory only, no persistence exists" per its own docstring. |
| Runtime Context (`RuntimeContext` + related objects) | IMPLEMENTED only | `core/runtime_context.py` — pure inert dataclasses; module docstring states no CLI command, persistence mechanism, or serialization format exists for any object. |
| Runtime Introspection (`get_*()` functions) | IMPLEMENTED, EXPOSED | Consumed by `runtime_snapshot.build_runtime_snapshot()`. |
| Runtime Snapshot (`build_runtime_snapshot`) | EXPOSED + PRODUCTION-CONSUMED (partial, internal, static-facts-only) | Exposed via `pcae runtime inspect` (`commands/runtime_inspect.py`); **also** auto-consumed internally in three real production paths (below). |
| Advisory Runtime / Advisory Providers consuming `RuntimeSnapshot` (`core/advisory_runtime.py`) | IMPLEMENTED only, **orphaned** | Zero call sites anywhere outside its own file — the module most resembling "capability-aware orchestration" exists but is unwired. |
| `RuntimeEvidenceProvider` (Evidence Framework) | PRODUCTION-CONSUMED | `core/evidence_providers.py:365-451` auto-builds a snapshot, emits 3 Evidence records. |

**Real internal (non-CLI) production consumers found:**
- `core/context.py:767-789` — `pcae session bootstrap` auto-embeds `runtime_snapshot_metadata` via `preview_runtime_snapshot()` into every session record.
- `core/phase_reports.py:3299-3315` — `pcae phase complete`'s canonical report generation auto-derives `current_runtime_state`/`current_maximum_capability`/`execution_availability` from `build_runtime_snapshot()`.
- `core/finalization_transaction.py:1105-1123` — finalization also folds in `runtime_introspection` output.

So three real production workflows already auto-consume runtime truth — but only the frozen static facts (`Observed`/`observe`/`unavailable`), never the registry's plugin/capability contents, because the registry is architecturally always empty by invariant (`pcae runtime inspect`: `Registry status: empty`, `Plugin count: 0`).

## 12. Runtime preflight current gap

Users must still manually run `pcae runtime inspect` before understanding capability availability for anything **beyond** the three already-automatic static-fact consumers above (session bootstrap, phase reports, finalization). No production workflow branches its own logic on registry/plugin contents — every consumer either reports facts unconditionally or is CLI-triggered inspection. No `if capability_required: check_registry(); decide_path()` pattern exists anywhere.

## 13. Runtime preflight target

Because the registry is architecturally always empty (0 plugins, an invariant, not a bug), any new preflight branch today can only ever resolve to "no capability available" — the only meaningful addition is **truthful structured refusal disclosure**, not real capability-aware routing among options (nothing exists yet to route among). This is confirmed independently by both `149O.20L.7O.3E`'s prior finding and this phase's fresh re-derivation. No execution enablement, backend invocation, or automatic fallback is proposed or would be appropriate.

## 14. Runtime disclosure semantics

`available != authorized`, `configured != callable`, `registered != executable`, `Permission Broker ALLOW != runtime capability` are not stated as one named frozen invariant in `docs/PCAE_RUNTIME_ARCHITECTURE.md`/`PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md`, but are enforced structurally: `BrokerDecisionContext` in `runtime_context.py` never imports `permission_broker_foundation` and never calls `PermissionBroker.evaluate()` (only wraps the shape of a decision); `runtime_inspect.py`'s own docstring states it never calls `PermissionBroker.evaluate()`. The separation is real, import-level enforced, just not centrally documented as a single named principle.

## 15. Runtime preflight consumers

Real current production-workflow consumers (not vague "all commands could use it" claims):

- `pcae session bootstrap` (`core/context.py`) — needs runtime truth to embed an accurate session-time snapshot; today it already gets this automatically; no gap.
- `pcae phase complete` canonical report (`core/phase_reports.py`) — needs it for the report's "Current Runtime State" section; today it already gets this automatically; no gap.
- Finalization (`core/finalization_transaction.py`) — needs it for finalization evidence; today it already gets this automatically; no gap.
- No further real production workflow was found that both (a) needs runtime/capability truth and (b) does not already have it. `core/advisory_runtime.py` is the one module shaped to consume it for orchestration but has zero call sites — it is unwired infrastructure, not a workflow with an unmet need.

## 16. Runtime preflight value/risk

- **Implementation effort: S** — reuses existing pure metadata queries (`registry_health()`/`list_plugins()`); no new contract required for the narrow "disclose registry emptiness truthfully" version.
- **Authority risk: LOW** — informational only, no new authority path.
- **User value: 2/5** — the three genuine internal consumers already exist; no unmet real workflow need was found while the registry remains architecturally empty.
- **E2E testability: 3/5.**
- **Strategic value:** low while execution remains unavailable — confirmed independently by two separate phases (`3E`, this one). Lower priority, per the governing brief's own instruction, since no meaningful current workflow needs runtime state beyond what is already automatically consumed.

## 17. RI/Advisory assessment (Candidate C)

| Sub-capability | Level reached | Evidence |
|---|---|---|
| RI Service (`repository_intelligence/service/service_engine.py::run_service`) | EXPOSED | 9-stage documented lifecycle; exposed via `pcae repository-intelligence service` CLI only. |
| Query layer (`query/query_engine.py::execute_query`) | PRODUCTION-CONSUMED | Only non-CLI caller is `advisory/context/advisory_context_builder.py`. |
| Snapshot loader (`query/snapshot_loader.py::load_snapshot`) | EXPOSED | Requires explicit path; no auto-discovery or staleness detection exists in source. |
| Dependency graph (`dependency_graph/`) | EXPOSED | CLI-only; zero non-CLI importers. |
| Historical memory (`historical_memory/`) | EXPOSED | CLI-only; zero non-CLI importers. |
| Change impact (`change_impact/`) | EXPOSED | CLI-only; zero non-CLI importers. |
| Unified query (`unified_query/`) | EXPOSED | CLI-only, and internally reused by the RI Service engine; no external production consumer besides Service itself. |
| Advisory context builder (`advisory/context/advisory_context_builder.py`) | PRODUCTION-CONSUMED, but only from a CLI command | Sole caller is `commands/advisory_context.py` (`run_advisory_context_build`) — human-invoked, **not** wired into `core/advisory.py`'s actual decision engine. |
| Advisory core decision engine (`core/advisory.py`) | Does not consume RI at all, by design | Imports only `pcae.core.permission_broker`; RI-blind. |

**Precise consumption graph:**

```
RI sub-capabilities (snapshot / dependency-graph / historical-memory / change-impact / unified-query)
  → manual CLI only, each with its own `pcae repository-intelligence <subcommand>`
  → RI Service (facade over unified_query, still CLI-only entry `pcae repository-intelligence service`)

RI Query Engine → execute_query()
  → advisory_context_builder.build_advisory_context()   [the ONE non-CLI consumer in the codebase]
  → but build_advisory_context() itself has exactly ONE caller: commands/advisory_context.py (a CLI command)

core/advisory.py (real, default advisory decision engine)
  → permission_broker only — never touches RI
```

Net effect: zero automatic/internal production consumption exists anywhere in the RI/Advisory subsystem today. Every RI path terminates at a human-invoked CLI command, including the one Advisory-context bridge that already exists.

## 18. RI → Advisory missing edge

**Bounded, not broad.** The wiring shape already exists and works: `Advisory invocation → RI query engine → structured context package (with provenance/limitations already enforced) → Advisory processing`. `AdvisoryContextRequest`/`RepositoryIntelligenceContextPackage` are already well-formed dataclasses suitable for programmatic (non-CLI) construction. The only missing piece is a call from `core/advisory.py`'s actual decision path (or `core/current_acting_model_advisory_provider.py`) into `build_advisory_context()`, replacing/supplementing the current CLI-only trigger. This matches, and narrows, `149O.20L.7O.3E`'s prior finding — no broad new context architecture is required for a first, bounded integration.

## 19. RI freshness and artifact generation

`.pcae/repository-intelligence/latest.json` and `.pcae/repository-intelligence/snapshots/` exist on disk (a snapshot has been manually generated at some point). `snapshot_loader.load_snapshot(path)` requires an explicit path — no auto-discovery of "latest" and no age/staleness check exists in source. Failure mode is **fail-closed today**: `SnapshotLoadError`/`SnapshotCompatibilityError` propagate up through `AdvisoryContextBuilderError` rather than being swallowed. If automatic snapshot regeneration/consumption were wired into Advisory's default decision path, this fail-closed behavior would need to become fail-soft for that specific call (Advisory must continue functioning, with the absence of RI context explicitly disclosed, rather than Advisory itself failing because RI context was unavailable) — new staleness semantics do not exist today and would need to be designed; this raises effort somewhat but does not change the boundedness of the edge itself.

## 20. RI authority isolation

Clean separation confirmed by source: zero references to `permission_broker`/`PermissionBroker` anywhere in `src/pcae/repository_intelligence` or `src/pcae/advisory`. `advisory_context_builder.py` explicitly carries a `NON_AUTHORITY_DISCLAIMER` constant and enforces `ensure_boundary_disclosure_present`/`ensure_limitation_present` before returning a context package — non-authority framing is structurally enforced, not merely documented. No conflation risk found: `RI context != authority`, `RI evidence != permission`, `RI recommendation != execution approval`, `Advisory != Permission Broker` all hold in current source.

## 21. RI + Advisory value

Today, a human must run `pcae advisory-context build` separately and manually cross-reference it against `pcae advisory status/check`'s own output — the two never converge automatically. Wiring the existing bridge into the default decision path would give `pcae advisory status/check` richer, automatically-acquired repository context (change impact, historical memory, dependency relationships already surfaced by RI) folded in as clearly-labeled, non-authoritative additional context, without any claim of improved model reasoning quality — the improvement is architectural (automatic acquisition, less manual cross-referencing) not a claim about output quality.

## 22. RI + Advisory effort/risk

- **Implementation effort: S** for the bounded first integration (wiring the caller-side of an already-built, already-tested bridge) — revised **down** from `3E`'s M/"v0.5.0-scale" characterization, which predated verification that `build_advisory_context()` is fully built and merely unwired to the default decision path. If automatic snapshot freshness/regeneration is included in scope, effort rises toward **M**, since that semantics does not exist yet.
- **Authority risk: LOW** — read-only, structurally non-authoritative, verified by import-level isolation from Permission Broker.
- **E2E testability: 4/5.**
- **User value: 4/5** — closes a genuine "PCAE already built this intelligence but does not use it by default" gap.
- **Strategic differentiation: 4/5.**
- The old "v0.5.0-scale" label is **not accurate** for this specific bounded edge; it remains a fair characterization only for a broader RI production-consumption program (wiring dependency-graph/historical-memory/change-impact into other workflows like `push.py`/`phase.py`), which is **not** what this narrow edge requires and is **not** proposed by this phase.

## 23. Missing edges (summary)

| Candidate | Exact missing production edge |
|---|---|
| A — rollback readiness/evidence | `pcae promote` completion → automatic `build_rollback_execution(dry_run=True)` call → persisted readiness/evidence artifact (new small schema, freshness/binding contract modeled on `RollbackApprovalBinding`). |
| B — runtime preflight | None with real current value beyond what is already auto-consumed (session bootstrap, phase reports, finalization); the only buildable addition is truthful "capability unavailable" disclosure text in preflight-gated commands, which changes no existing decision logic. |
| C — RI/Advisory | `core/advisory.py` (or `core/current_acting_model_advisory_provider.py`) decision path → call into existing `build_advisory_context()` bridge, with fail-soft handling for missing/stale snapshot. |

## 8. Manual choreography (cross-candidate)

- **A:** cold-start `pcae rollback --per-id X --dry-run` only after a promotion later needs reversing.
- **B:** run `pcae runtime inspect` separately for anything beyond the three already-automatic static-fact consumers.
- **C:** run `pcae advisory-context build` separately, then manually cross-reference its output against `pcae advisory status/check`.

## 9. Human-boundary analysis

None of the three candidates removes a legitimate human authorization step:

- **A:** real rollback execution remains 100% human-initiated via explicit `pcae rollback --per-id` without `--dry-run`; auto-generation only pre-stages informational evidence.
- **B:** disclosure only; no new gate, no new authority.
- **C:** Advisory's output remains structurally non-authoritative — it never gates or grants; automatic context acquisition changes what information is folded into an already-non-authoritative report, not who decides what.

## 10. Freshness/state analysis (cross-candidate)

- **A:** no freshness semantics exist today (no artifact exists to be stale); a reusable precedent (`RollbackApprovalBinding`) exists but is not directly reusable without a new artifact-specific contract.
- **B:** not applicable — the registry has no state to go stale; it is always empty by architectural invariant.
- **C:** snapshot staleness/auto-discovery does not exist; current failure mode is fail-closed; automatic consumption would need an explicit fail-soft policy for this one call path.

## 11. Authority-risk analysis

| Candidate | Risk | Basis |
|---|---|---|
| A — rollback readiness/evidence | LOW | Dry-run only, `execution_allowed: False` preserved; needs an explicit non-authority disclaimer in the new artifact's design. |
| B — runtime preflight | LOW | Purely informational; registry is architecturally empty, nothing to gate on. |
| C — RI/Advisory | LOW | Read-only, structurally isolated from Permission Broker by import boundary; needs fail-soft handling to avoid Advisory itself becoming fragile to RI unavailability. |

## 12. Effort analysis

| Candidate | Effort | Basis |
|---|---|---|
| A — rollback readiness/evidence | S-M | Safe primitive exists; new persistence/schema/freshness-binding contract required. |
| B — runtime preflight | S | Reuses existing pure metadata queries; no new contract for the narrow disclosure-only version. |
| C — RI/Advisory | S (M if freshness/regeneration is included) | Bridge already fully built and tested; only a caller-side wire is missing for the bounded first integration. |

## 13. Dependency graph

```
Candidate A (rollback readiness/evidence) : independent
Candidate B (runtime preflight)            : independent; does not benefit from or require A or C
Candidate C (RI/Advisory)                  : independent

No candidate requires another to be useful individually. A soft ordering
preference exists only within C itself: if C's freshness/fail-soft
handling is designed carefully, a hypothetical future broader RI→other-
workflow wiring (push.py/phase.py, explicitly out of scope for this
phase) could reuse that same fail-soft pattern -- this is not a
prerequisite relationship between A/B/C.
```

## 26. Consumption-gap matrix

| Candidate | Production owner | Current consumer | Missing consumer edge | Manual choreography | Human boundary | Effort | Risk |
|---|---|---|---|---|---|---|---|
| A — rollback readiness/evidence | `core/agent.py::build_rollback_execution` | CLI dispatch only (`commands/agent.py:16264`) | Auto-trigger at `pcae promote` completion + persistence | Cold-start `--dry-run` after the fact | Real rollback execution stays human-`--per-id`-gated | S-M | LOW |
| B — runtime preflight | `core/runtime_snapshot.py`, `core/runtime_registry.py` | 3 automatic internal consumers (session bootstrap, phase reports, finalization) + CLI inspect | None with unmet real value; only disclosure-text addition possible | `pcae runtime inspect` for anything beyond the 3 auto-consumers | No new gate proposed | S | LOW |
| C — RI/Advisory | `advisory/context/advisory_context_builder.py`, `repository_intelligence/query/query_engine.py` | CLI only (`commands/advisory_context.py`) | `core/advisory.py` decision path → `build_advisory_context()` call, with fail-soft snapshot handling | `pcae advisory-context build` run and cross-referenced manually | Advisory output stays non-authoritative | S (M if freshness included) | LOW |

## 27. Maturity matrix

| Candidate | Implemented | Verified | Exposed | Production-consumed | Auto-orchestrated | E2E verified | Released |
|---|---|---|---|---|---|---|---|
| A — rollback readiness (artifact) | No | — | — | — | — | — | — |
| A — rollback evidence (dry-run) | Yes | Yes | Yes | Yes (manual trigger) | No | No | No |
| A — rollback PB gate (default path) | Yes | Yes | Yes | Yes | Yes | Yes | **Yes (v0.4.1)** |
| B — runtime registry/snapshot | Yes | Yes | Yes | Yes (partial: 3 static-fact consumers) | No | No | No (infra only) |
| C — RI query engine | Yes | Yes | Yes | Yes (via Advisory-context builder) | No | No | No |
| C — Advisory-context builder | Yes | Yes | Yes | Yes (CLI-triggered only) | No | No | No |
| C — Advisory core decision engine | N/A (does not consume RI) | — | — | — | — | — | — |

## 28. Priority matrix

Scored 1-5 (5 = best) for user value/maturity/consumption benefit/E2E testability/differentiation; effort scored 1 = easiest; authority safety scored 5 = safest.

| Candidate | User value | Maturity | Consumption benefit | Effort | Authority safety | E2E testability | Differentiation |
|---|---:|---:|---:|---:|---:|---:|---:|
| C — RI/Advisory | 4 | 4 | 4 | 1 (S) | 5 (LOW) | 4 | 4 |
| A — rollback readiness/evidence | 3 | 4 | 3 | 2 (S-M) | 5 (LOW) | 4 | 3 |
| B — runtime preflight | 2 | 5 | 2 | 1 (S) | 5 (LOW) | 3 | 2 |

**Ranking: C > A > B.** This re-ranks `3E`'s original ordering (which had RI-adjacent work ranked lower due to an M/"v0.5.0-scale" effort estimate). The revision is grounded in this phase's independent re-derivation showing `build_advisory_context()` is a fully built, tested bridge whose only missing piece is a caller-side wire — not a re-guess. B remains lowest: its registry is architecturally empty and its three genuine real consumers already exist, so remaining potential value is limited to disclosure text with no unmet workflow need found.

## 15. E2E designs (summary; full designs in §31-33)

Full designs for all three candidates are provided in §31-33 below, matching the required structure per the governing brief.

## 31. Independent E2E design — rollback readiness (Candidate A)

- Highest-level entry: `pcae promote` (trigger for automatic generation) and `pcae rollback --per-id X` (both dry-run and real, for consumption).
- Automatic readiness/evidence generation: triggered non-blockingly at promotion completion; must be provably non-mutating (assert zero filesystem writes beyond the new artifact itself, zero RER creation).
- Human trigger: real rollback dispatch remains `pcae rollback --per-id X` without `--dry-run`; unaffected by whether readiness exists.
- Stale/missing evidence: test (a) readiness generated then repo state changes (HEAD moves) → must be detected stale, not silently reused; (b) readiness artifact missing entirely → rollback must fall back to computing fresh, exactly as today.
- Permission Broker: readiness generation must never itself call `mutation_permission`; only the existing rollback-dispatch gate call remains the sole broker touch point.
- ALLOW / DENY: both outcomes must be unaffected by whether pre-staged readiness existed — DENY must still occur identically with or without it.
- Restart: promotion process interrupted after readiness generation but before completion — no duplicate artifact on retry (idempotency check).
- No duplicate artifacts: re-running promotion (if ever legitimately possible) or re-triggering generation must not create a second artifact for the same `(per_id, ecp_id, head_commit_sha)` binding.
- Runtime unchanged: `pcae runtime inspect` before/after must be byte-identical.

## 32. Independent E2E design — runtime preflight (Candidate B)

- Workflow requiring capability truth: a preflight-gated command's own precondition report (e.g. `push`/`commit`/`promotion`/`publication` dispatch), extended with a new disclosure field.
- Automatic runtime/context lookup: `registry_health()`/`list_plugins()` called inside the preflight step itself, not left to a separate manual `pcae runtime inspect`.
- Unavailable case: registry empty (current, invariant) → disclosure must read "0 plugins registered; execution unavailable" truthfully, must not fabricate availability.
- Configured-but-not-executable case: not currently reachable (registry is always empty) — test must assert the disclosure code does not silently assume this state is reachable; if it can never occur today, the test documents that explicitly rather than faking it.
- Restart: pure read, safe on every invocation, no state to lose.
- No authority elevation: assert the new disclosure field cannot be read by any code path as a decision input to `mutation_permission`.
- No fallback execution: explicitly assert no code path attempts to invoke a backend/plugin merely because disclosure text was added.

## 33. Independent E2E design — RI/Advisory (Candidate C)

- Advisory entry point: `pcae advisory status/check` (the actual default decision path, not the CLI `advisory-context build` command).
- Automatic RI context acquisition: `core/advisory.py` (or the acting-model provider) calls `build_advisory_context()` without requiring a separate human-invoked CLI step first.
- Fresh artifact: snapshot present and recent → context populated, disclosed as additional non-authoritative input alongside the broker-derived verdict.
- Missing artifact: no snapshot present → Advisory must still return its existing broker-derived verdict unaffected, with RI-context absence explicitly disclosed (fail-soft, not fail-closed, for this specific call path — a deliberate, tested divergence from `advisory_context_builder`'s current fail-closed default for its CLI caller).
- Stale artifact: snapshot exists but repo HEAD has since diverged → must be disclosed as stale, not silently presented as current.
- Provenance: every RI-derived field in the advisory output must carry its snapshot source/generation-time provenance, never presented as if computed live.
- No authority flow: assert `core/advisory.py`'s output still never gates or grants — the broker-derived verdict remains the sole authoritative field.
- Restart: safe to re-run; regenerates or reuses snapshot deterministically given the same on-disk artifact.
- Deterministic consumption: same snapshot + same query inputs → same context package, every time.

## 16. Plan A — Fastest meaningful next consumption

**Capability:** Candidate C alone (RI/Advisory context wiring), scoped narrowly to the caller-side wire only (no automatic snapshot regeneration in this first cut — missing/stale snapshot is disclosed and handled fail-soft, but generating a fresh one automatically is deferred).
**Missing edge:** `core/advisory.py` → `build_advisory_context()` call, per §18.
**Effort:** S. **Authority risk:** LOW.
**E2E strategy:** per §33, scoped to the fresh/missing/stale-disclosure cases; automatic regeneration explicitly out of this narrow cut's scope.
**Likely release magnitude:** patch-scale (`v0.4.2`-plausible) — informational-context-only, no new user-visible command syntax, no authority change.

Not forcing rollback readiness here: Candidate A scores lower on effort and marginally lower on differentiation than C in the priority matrix (§28); Candidate B scores lowest overall despite being equally cheap, since its remaining value is limited to disclosure text with no unmet workflow need found (§16 of this doc's own runtime-preflight analysis).

## 17. Plan B — Highest strategic product value

**Capability:** Candidate C (RI/Advisory context wiring) + Candidate A (rollback readiness/evidence auto-generation), together.
**Rationale:** both are LOW authority risk, both are independent (§13's dependency graph confirms neither requires the other), and together they materially increase PCAE's autonomous usefulness on two different axes — richer, automatically-acquired advisory reasoning context, and pre-staged rollback safety net — without touching execution capability or Permission Broker policy.
**Effort:** S (C) + S-M (A), aggregate S-M.
**Authority risk:** LOW (both).
**E2E strategy:** one batch-level End-to-End Capability Consumption Verification phase, per §31/§33, plus explicit confirmation the two integrations do not interact (they touch disjoint subsystems: `core/advisory.py` vs. `core/agent.py::build_rollback_execution`).
**Likely release magnitude:** `v0.4.2` if scoped tightly (both individually patch-level); a `v0.5.0` framing becomes defensible only if bundled with additional work beyond these two.

## 18. Plan C — Sequenced roadmap

```
Step 1: Candidate C (RI/Advisory context wiring, narrow cut per Plan A)
        -- cheapest, highest current value, bounded scope.
        Release boundary: v0.4.2-plausible on its own.

Step 2: Candidate A (rollback readiness/evidence auto-generation)
        -- independent of Step 1; reuses the fail-soft disclosure
        pattern Step 1 establishes as a design precedent (not a
        hard dependency).
        Release boundary: v0.4.2 (if bundled with Step 1) or a
        separate small patch release on its own.

Step 3: Candidate B (runtime preflight disclosure)
        -- lowest remaining value; revisit only if a real production
        workflow with an unmet runtime-truth need is later found, or
        if the runtime registry ever stops being architecturally
        empty (neither has occurred; this phase does not propose or
        anticipate either).
        Release boundary: not scheduled; deprioritized.
```

Explanation: C is sequenced first because it is now both the cheapest (S) and the highest-value candidate — a genuine finding of this reassessment, not an assumption carried from `3E`. A follows because it is independent and delivers real (if conditional) value at S-M effort. B is sequenced last because, unlike `3E`'s treatment of it as a "cheap first step," this phase's fresh re-derivation found its real remaining value is lower than previously estimated once the three already-automatic static-fact consumers are accounted for.

## 19. Recommended next capability

**Recommendation: Candidate C (Repository Intelligence + Advisory-context consumption), narrow first cut per Plan A (§16).**

Rationale: it is now the cheapest of the three candidates (Effort S, revised down from `3E`'s M/"v0.5.0-scale" label after fresh verification that the bridge is already fully built and tested), carries LOW authority risk with structurally-enforced non-authority isolation, and delivers the highest differentiated value — it closes a genuine "PCAE already built this intelligence but does not use it by default" gap, which is exactly the category of improvement this reassessment's governing question asks for. Candidate A remains a strong, low-risk companion (Plan B, §17) if the human prefers a slightly larger single batch. Candidate B is not recommended next — its remaining real value, once existing automatic static-fact consumption is accounted for, is the lowest of the three.

```text
HUMAN PRIORITY SELECTION REQUIRED
```

## 25. Human decision required

Exact options for the human to choose among:

- Integrate Plan A alone (Candidate C narrow cut) — recommended as the fastest, highest-value next step.
- Integrate Plan B (Candidate C + Candidate A together) as one batch — highest strategic value without execution activation.
- Integrate Candidate A alone.
- Integrate Candidate B alone (lowest priority per this reassessment, but not excluded).
- Integrate a custom subset/sequencing not enumerated above, per §18's dependency-independent structure.
- Defer all integration and take no further action this cycle.

## 20. Release implications

Per §16-18: Plan A (Candidate C narrow cut) alone is patch-scale (`v0.4.2`-plausible) — informational, no new user-visible command syntax, no authority change. Plan B (C + A) is also plausibly `v0.4.2`-scale if kept tightly scoped; a `v0.5.0` framing would require additional bundled work beyond these two. Candidate B alone, if ever selected, would also be patch-scale but is not the recommended next step. This assessment does not select or freeze a version; the eventual release-hardening phase makes that determination once an actual implementation's true final scope is known.

## 21. Already-connected governance confirmation

No new Permission Broker gap or production mutation bypass was found by any of the three independent candidate investigations this phase. Specifically re-confirmed: (a) Candidate A's rollback dispatch retains its sole, already-released Permission Broker gate (`agent.py:94356`), with no bypass path found; (b) Candidate B's runtime introspection paths make no authority claims and call no broker code; (c) Candidate C's RI/Advisory modules make zero calls into `permission_broker`/`PermissionBroker` anywhere in `src/pcae/repository_intelligence` or `src/pcae/advisory`. No governance gap requires interrupting this roadmap.

## 22. Deferred/trust-blocked systems

Not reassessed this phase, per the governing brief: HATP activation; HMIC/Class-B authority; CLTR cutover; backend/model execution; Telegram inbound; Dell deployment. No evidence was found or sought that any of these became a strict dependency of Candidates A/B/C; none is reopened.

## 23. Human decision required

See §25 above (mandatory-section-numbering duplicate per the governing brief's required-sections list, both entries refer to the same decision point).

## 24. Testing strategy and checks actually run

This was a read-only strategic reassessment; no broad Fast Green run was performed merely to rank candidates, per the governing brief's explicit instruction. Evidence was gathered via: the baseline CLI checks in §2 (all side-effect-free); `git diff --name-status v0.4.1..HEAD -- src/pcae/` (confirmed zero production changes since the release tag); direct reads of `docs/PHASE_149O_20L_7O_3E_...md` and `docs/PHASE_149O_20L_7O_3G_...md` (prior reassessment phases, used as a starting baseline, independently re-verified against current source rather than trusted as-is); and three independent, parallel source-reconstruction passes over `src/pcae/core/agent.py`, `src/pcae/core/rollback_approval_evidence.py`, `src/pcae/core/mutation_permission.py`, `src/pcae/core/runtime_registry.py`, `src/pcae/core/runtime_context.py`, `src/pcae/core/runtime_snapshot.py`, `src/pcae/core/advisory_runtime.py`, `src/pcae/core/evidence_providers.py`, `src/pcae/core/context.py`, `src/pcae/core/phase_reports.py`, `src/pcae/core/finalization_transaction.py`, `src/pcae/core/advisory.py`, `src/pcae/repository_intelligence/**`, `src/pcae/advisory/**`, `src/pcae/commands/advisory.py`, `src/pcae/commands/advisory_context.py`, `src/pcae/commands/repository_intelligence.py`, `src/pcae/commands/governance_auto_publication.py`, `src/pcae/commands/publication_permission_gate.py`, `src/pcae/schema_resources/rollback_approval/**`, each independently citing file:line/function evidence rather than trusting prior phase-report text. No production source, contract, schema, CLI implementation, or packaging configuration was modified.

## Governance results (pre-completion)

- `pcae health`: healthy
- `pcae check`: passed
- `pcae status coherence`: coherent
- `pcae doctor task-memory`: warnings only (pre-existing, unrelated `tasks/DONE.md` sync-debt entries predating this phase)
- `pcae push check`: nothing_to_push (pre-finalization baseline)
- `pcae runtime inspect`: Observed / observe / unavailable — unchanged
- Telegram: configured, enabled, ready
- No production source, CLI, contract, schema, or packaging-configuration file was modified this phase.
- No version-string change was made this phase.
- No build infrastructure was modified this phase.
- No Permission Broker policy was invented or altered this phase.
- No rollback authority was changed this phase.
- No runtime execution capability was enabled this phase.
- No HATP/HMIC/Class-B authority was touched this phase.
- No CLTR authority cutover occurred this phase.
- No backend/model execution was added this phase.
- No OpenRouter call occurred this phase.
- No Dell host was mutated this phase.
- No inspection of the private `~/repos/pcae-deepseek-research` repository occurred this phase.
- No reading, modification, or publication of the article occurred this phase — it remains STOPPED.
- No integration was implemented; no priority was selected unilaterally.

## Summary

```text
POST-v0.4.1 DEFERRED CAPABILITY REASSESSMENT:
COMPLETE

PUBLIC BASELINE:
v0.4.1

RUNTIME:
Observed / observe / unavailable

CANDIDATE A — ROLLBACK READINESS/EVIDENCE:
Readiness: NOT IMPLEMENTED. Evidence (dry-run): PRODUCTION-CONSUMED
(manual trigger only). Permission Broker gate: RELEASED (v0.4.1).
Missing edge: automatic generation at promotion completion. Effort
S-M, LOW risk.

CANDIDATE B — RUNTIME PREFLIGHT:
Registry/snapshot: IMPLEMENTED, EXPOSED, PRODUCTION-CONSUMED (partial
-- 3 automatic static-fact consumers: session bootstrap, phase
reports, finalization). No unmet real workflow need found; registry
architecturally empty. Effort S, LOW risk, lowest priority.

CANDIDATE C — RI/ADVISORY:
RI query engine + Advisory-context builder: PRODUCTION-CONSUMED via
CLI only. Advisory core decision engine: does not consume RI. Missing
edge: single caller-side wire into an already-built, already-tested
bridge. Effort S (revised down from prior M/v0.5.0-scale label),
LOW risk, highest priority.

TOP PRIORITY:
Candidate C (RI/Advisory context wiring, narrow first cut)

RECOMMENDED PLAN:
Plan A (Candidate C alone) as the fastest meaningful next step;
Plan B (Candidate C + Candidate A) as the highest-strategic-value
batch if the human prefers a larger single release.

IMPLEMENTATION:
NOT STARTED

HUMAN PRIORITY SELECTION:
REQUIRED

ARTICLE:
STOPPED
```

Stop after 3I. Do not begin implementation automatically.
