# Phase 149O.20L.7O.3E — Post-v0.4 Deferred Capability Consumption Priority Reassessment

**Status:** COMPLETE
**Phase type:** READ-ONLY STRATEGIC REASSESSMENT. No production source, CLI, contract, schema, or packaging-configuration file was modified. No integration was implemented. No priority was selected unilaterally.
**Phase-entry commit:** `5908a052` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.

## 1. Objective

Phase 149O.20L.7O.3D published PCAE v0.4.0, the first release built on a genuinely *connected* governance-consumption graph (Plan B+ from Phase 3C.1, implemented in 3C.2, independently verified in 3C.3/3C.3.1/3C.3.2, release-hardened in 3C.4). This phase answers the follow-on strategic question:

> Now that PCAE itself consumes the Plan B+ governance path, what is the highest-value remaining missing consumption edge that can be connected next without weakening authority boundaries or prematurely enabling execution?

This is a re-derivation, not a repeat of 3C.1: every one of the six candidates was re-checked against current (post-v0.4.0) source, not assumed unchanged.

## 2. v0.4.0 baseline

Verified at phase entry:

```
git status --short              => (empty, clean)
git status --branch --short     => ## main...origin/main
git rev-list --count origin/main..HEAD => 0
git rev-parse HEAD               => 5908a052f94af4b01af41ba4995fd0fd036cbb22
git rev-parse origin/main        => 5908a052f94af4b01af41ba4995fd0fd036cbb22
git rev-parse v0.4.0^{commit}    => ea3f731ef50ea16985fd4a0562f0c091bb8109b2
git rev-parse v0.3.1^{commit}    => 5d7edef9c34ee266a9c5b51940ee4f1848375d22
pcae health                      => healthy
pcae check                       => passed
pcae status coherence            => coherent
pcae doctor task-memory          => warnings only (pre-existing tasks/DONE.md sync-debt entries, unrelated to this phase)
pcae push check                  => nothing_to_push
pcae runtime inspect             => Observed / observe / unavailable (unchanged)
pcae notify status                => Telegram configured, enabled, ready
pcae phase-report show --latest  => Phase 149O.20L.7O.3D, status completed, report complete
```

`git tag v0.4.0` resolves to `ea3f731e` ("149O.20L.7O.3C.4: Connected Capability Release Scope, Version, and Reproducible-Build Hardening") — the frozen release commit. HEAD is 10 commits ahead of the tag, all lifecycle bookkeeping (3D's publication act itself, PROJECT_STATUS.md/CHANGELOG.md updates, task-lifecycle open/close, phase-completion metadata/report writes) — confirmed via `git log --oneline` and `git diff --name-status ea3f731e..HEAD` touching only `docs/RELEASE_NOTES_V0_4_0.md`, `.pcae/*`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/*` — no `src/pcae` change between the tag and current HEAD. Runtime unchanged throughout. This confirms a clean, stable v0.4.0 baseline for reassessment.

## 3. Current connected-consumption graph (post-v0.4.0)

Reconstructed from source at current HEAD (`src/pcae/commands/phase.py:46,109`, `src/pcae/commands/governance_auto_publication.py`, `src/pcae/commands/publication_permission_gate.py`, `src/pcae/core/mutation_permission.py:546`):

```
pcae phase complete
  → run_phase_complete() [commands/phase.py]
      → auto_publish_confirmed_session(context, subject_ref=active_task_id, operator_id=agent_lock.agent_id)
          [commands/governance_auto_publication.py]
          → SessionApplicationService.find_session_by_subject_ref()
              [deterministic, non-heuristic session lookup]
          → (only if SessionState == Confirmed)
              → publish_with_permission_gate()  [commands/publication_permission_gate.py]
                  → mutation_permission.evaluate_publication_permission()  [Permission Broker, POL-001]
                      → ALLOW → PublicationApplicationService.hand_off()
                          → PublicationCoordinator.execute()
                              → CHGR created/already-published (idempotent, record_id returned)
                      → DENY → no CHGR, phase-complete proceeds unaffected (informational only)
      → complete_phase() [unchanged, byte-identical for the ~30+ prior phases with no bound session]
```

This is the frozen v0.4.0 baseline architecture. It is real, wired, non-CLI-shelling (verified: no `subprocess("pcae ...")` in the call chain), and preserves the human `Confirmed`-state boundary exactly. All six candidates below are assessed as **additions onto this graph**, not replacements of it.

## 4. Prior assessment changes since 3C.1

| Area | 3C.1 finding | Current state | Changed? |
|---|---|---|---|
| Interactive Workflow/CHGR routing | CLI-only, UC | Production-consumed via `auto_publish_confirmed_session`, wired to `pcae phase complete` | **YES — now AC** |
| Publication Execution Ownership auto-invocation | CLI-only | Same wiring as above | **YES — now AC** |
| Permission Broker — publication gap | UC | Closed (`evaluate_publication_permission`, `publish_with_permission_gate`) | **YES — now AC** |
| Permission Broker — rollback gap | UC | Still unwired — `build_rollback_execution`'s default path has zero broker call (`agent.py:16264`, re-grepped this phase, no `mutation_permission`/`permission_broker` hit) | NO — unchanged |
| CHGR downstream automatic consumption | UC | The one wired consumer (`pcae phase complete`) receives `record_id` automatically; no *other* production workflow reads a CHGR as input | PARTIALLY — a first automatic consumer now exists, but only as a byproduct of publication, not as a general "read an existing CHGR as evidence" capability |
| Repository Intelligence internal consumption | Rated S-M/Low by 3C.1; RE-EXAMINED and DEFERRED by 3C.2 (§8) after direct re-reading showed the target consumer (`push.py`'s freshness/report logic) is not display-only | Unchanged — RI still has zero production consumers outside `cli.py` (re-grepped this phase: `grep -rl "repository_intelligence" src/pcae --include="*.py"` outside `repository_intelligence/`, `advisory/`, `commands/` → only `cli.py`) | NO new consumer; the *reason* for deferral is now grounded in 3C.2, not merely an untested prediction |
| Runtime/plugin introspection — reporting/evidence | PC | Unchanged (`phase_reports.py`, `evidence_providers.py` still the only consumers, still reporting-only) | NO |
| Runtime/plugin introspection — preflight gating | UC | Unchanged — no `*preflight*.py` module imports `runtime_registry`/`runtime_snapshot`/`runtime_introspection` (re-grepped this phase, zero hits) | NO |
| Advisory core (status/check) | NC by design (broker-only decision-vocabulary mapper) | Unchanged — `core/advisory.py` imports only `pcae.core.permission_broker` | NO |
| Advisory-Context (RI-backed) | UC | Unchanged — `advisory_context_builder.py` remains the sole RI-consuming module, itself only called from `commands/advisory_context.py` (CLI) | NO |
| Rollback readiness/evidence auto-generation | UC | Unchanged — `build_rollback_execution` has exactly one caller, the CLI dispatch (`agent.py:16264`) | NO |
| Runtime Enforcement Decision Engine/Coordinator | TB | Unchanged — `RuntimeEnforcementCoordinator`/`RuntimeEnforcementDecision` exist only as design-only definitions in `backend_invocations.py` (lines ~9887, ~10323), zero consumers | NO |

**New consumer seam created by Plan B+ (v0.4.0):** `commands/governance_auto_publication.py` is now a real, precedent-setting "production workflow auto-detects + routes to an existing service, preserving the human boundary" pattern. This is the single most important architectural fact for this reassessment: it is now proof, not merely a proposal, that the "production service, not CLI shell-out" integration shape works end-to-end, survived independent verification (3C.3 series), and shipped. Every candidate below is evaluated against whether it can reuse this exact shape.

## 5. Repository Intelligence internal consumption

**Why 3C.2 deferred it (re-derived, not copied):** 3C.1 assumed `push.py`'s `git log`/`git diff` subprocess calls (then ~lines 321-346) were display-only text a service call could mechanically replace. 3C.2 (§8) re-read the same code at its own HEAD and found `_staged_file_snapshot`, `_files_in_unpushed_range`, `_unpushed_commit_lines` feed the actual push-permission freshness-comparison and report-generation *logic*, not just display text — swapping the data source would require re-plumbing consumer shape/semantics throughout `push.py`, not a drop-in substitution.

Re-verified this phase at current HEAD (`commands/push.py`): the same functions and call sites are present, unchanged in shape. The 3C.2 finding still holds.

**Current RI production architecture** (unchanged since 3C.1/3C.2, re-confirmed via source read):

- Repository Intelligence Service (`repository_intelligence/service.py` family) — unified query facade over the sub-capabilities below.
- Query layer (`repository_intelligence/query/query_engine.py`) — read-only query execution over a snapshot.
- Knowledge snapshot (`snapshot_loader.py`) — requires an explicit path; **no auto-discovery or staleness detection** of a snapshot exists anywhere.
- Change impact (`repository_intelligence/change_impact/`) — structured, attributed change analysis; unused by `push.py`/`phase.py`.
- Historical memory (`repository_intelligence/historical_memory/`) — unused by `push.py`/`phase.py`.
- Dependency graph (`repository_intelligence/dependency_graph/`) — no production consumer.
- Unified query (`repository_intelligence/unified_query/`) — no production consumer.
- Advisory context interface (`advisory/context/advisory_context_builder.py`) — the one *internal* RI consumer, itself only reachable from `commands/advisory_context.py` (CLI), never from `core/advisory.py`'s actual decision engine.

**Current potential consumers after v0.4.0:** the same two identified by 3C.1 — `push.py`/`phase.py` change-context gathering, and `core/advisory.py`'s decision engine (via the existing `advisory_context_builder` bridge). No new consumer seam was created for RI by Plan B+; `governance_auto_publication.py` does not touch repository content/history analysis at all.

**Answers to the mandatory questions:**

- *Does the new connected lifecycle provide a clean context-consumption seam?* No. `auto_publish_confirmed_session` is a session-state router, not a context aggregator; it has no natural point to attach RI-derived evidence, and CHGR evidence composition happens upstream of it (in `EvidenceCoordinator`, not in the new module).
- *Can RI enrich a workflow without becoming authority?* Yes in principle — RI's own CLI help text and 3C.1's precedent both establish it as explicitly non-authoritative, read-only. This has not changed.
- *Is automatic snapshot generation required?* Yes, and this remains unbuilt. `snapshot_loader.load_snapshot(path)` still requires an explicit path; there is no "detect stale/missing snapshot and regenerate" trigger anywhere. Any real consumption integration must design this first, which was not previously counted as part of the "S-M effort" 3C.1 estimate — a second reason the original estimate undercounted effort, beyond the `push.py` semantics issue 3C.2 found.
- *What freshness semantics would be needed?* A snapshot generated once and read repeatedly would drift from the live repo across a long-running phase. This needs an explicit policy (e.g. "regenerate if repo HEAD differs from snapshot's recorded HEAD") not designed anywhere today.
- *Would missing/stale RI be fail-soft or fail-closed?* Must be fail-soft (RI is informational, and none of push/phase logic depends on it today) — but this needs to be an explicit, tested behavior, not an assumption, since `push.py`'s freshness-comparison logic (per 3C.2's finding) is exactly the kind of place a silent RI failure could produce a subtly wrong comparison if wired incorrectly.
- *Is a new contract required?* Not necessarily a frozen contract-file change, but a new internal interface (a stable, freshness-aware "get change context" function signature that `push.py`/`phase.py` can call, decoupled from `push.py`'s current inline freshness logic) is required — this is real design work, not zero-contract wiring.
- *Does integration still require broad Advisory/context work?* No — the RI→push/phase wiring and the RI→Advisory wiring are two separable integrations; only the latter touches Advisory. RI→push/phase can proceed independently.

**Classification:** Effort **M** (re-classified up from 3C.1's S-M, per the two additional factors above: real `push.py` semantics re-plumbing, plus the previously-uncounted snapshot-freshness design work). Authority risk **LOW** (read-only, informational; RI remains explicitly non-authoritative). Not implemented.

## 6. Runtime/plugin capability-aware orchestration

**Current runtime registry/introspection consumers** (re-confirmed this phase, `grep -rl "runtime_registry\|RuntimeRegistry" src/pcae`): `cli.py` (CLI wiring), `core/runtime_context.py`, `core/runtime_introspection.py`, `core/runtime_snapshot.py`, `core/phase_reports.py` (reporting), `core/evidence_providers.py` (evidence enrichment), `core/agent.py` (an unrelated Phase 61A design-document generator, confirmed distinct from the real registry per 3C.1's own note, re-verified this phase — not a real consumer), `core/evidence.py`, `commands/runtime_inspect.py` and `commands/agent.py` (both CLI wiring).

**Does PCAE automatically query capability availability/plugins/runtime mode/execution availability when a workflow requires a capability?** No. Every consumer found is either (a) CLI-triggered inspection (`pcae runtime inspect`) or (b) passive reporting/evidence enrichment that runs unconditionally on every phase report/evidence collection, never gated on "does this specific workflow step need a capability." No production module contains the pattern `if capability_required: check_registry(); decide_path()`.

**Distinguishing the two states:** `pcae runtime inspect` (human can inspect) is fully built and CLI-exposed. "PCAE consumes runtime capability state internally" (the candidate flow: `PCAE workflow requests capability → canonical runtime registry/context → availability resolved → workflow chooses safe supported path or fails truthfully`) does not exist anywhere. The closest analogue — `phase_reports.py`/`evidence_providers.py` — always succeeds informationally; neither ever branches workflow behavior based on the result.

**Current status: diagnostic-only today**, with a small partially-consumed subset (reporting/evidence enrichment, unchanged PC classification from 3C.1). The candidate flow above is a real, coherent next orchestration layer, but since the runtime registry is architecturally always empty (0 plugins, an invariant, not a bug — confirmed via `pcae runtime inspect`'s `Plugin count: 0`, `Registry status: empty`), any workflow branching on it today would deterministically always resolve to "no capability available" — i.e. the only meaningful behavior such a preflight check could add right now is **truthful, structured refusal disclosure** (e.g., "this workflow step requires plugin capability X; none registered; declining rather than proceeding degraded"), not actual capability-aware routing among multiple options (there is nothing to route among yet). This must not be read as a step toward enabling execution.

**Classification:** Effort **S** for the narrow "preflight discloses registry emptiness truthfully" version (reuses `registry_health()`/`list_plugins()`, already-built pure metadata queries); the broader "workflow resolves among multiple available capabilities" version is **not currently buildable** (nothing to resolve among — the registry is architecturally empty), so it is out of scope, not merely deferred. Authority risk **LOW** (informational; explicitly must not enable execution).

## 7. Remaining Permission Broker coverage

Production mutation/effect matrix, freshly re-verified against current HEAD:

| Effect | Current permission boundary | Permission Broker consumed? | Bypass path? | Authority significance |
|---|---|---|---|---|
| `pcae push` | `commands/push.py::_evaluate_push_permission()` | YES | None found | HIGH (root-mutating, remote-visible) |
| `pcae commit` (via `core/agent.py` dispatch) | `agent.py:4710` `mutation_permission.evaluate_commit_permission` | YES | `commands/commit.py` primitive itself has no broker call — but it is only reachable through the governed `agent.py` dispatch in production use; not a live bypass | HIGH |
| `pcae promote` | `agent.py:~93726` `mutation_permission.evaluate_promotion_permission` | YES | None found | HIGH |
| Alternate push path | `agent.py:~4862` `mutation_permission.evaluate_alternate_push_permission` | YES | None found | HIGH |
| `pcae phase complete` (commit dispatch) | `commands/phase.py:~18479` `mutation_permission.evaluate_commit_permission` | YES | None found | HIGH |
| **Publication (`governance-record publish`, and this phase's own automatic path)** | `commands/publication_permission_gate.py::publish_with_permission_gate` → `mutation_permission.evaluate_publication_permission` | **YES — landed in 3C.2/v0.4.0** | Carried-forward finding (unchanged, re-confirmed this phase): `core/rollback_approval_evidence.py:980::create_rollback_approval_decision()` calls `PublicationCoordinator.execute()` directly, bypassing the gate — but this function still has **zero production callers** (re-grepped this phase), so it is dead code, not a live bypass | MODERATE (governance-document creation) |
| **`pcae rollback` default path** (`agent.py::build_rollback_execution`, sole caller `agent.py:16264`) | None — re-confirmed this phase, zero `mutation_permission`/`permission_broker` references in the default dispatch | **NO** | N/A — simply unguarded | HIGH (root-mutating recovery action) |
| `pcae task transition`/`task new` | None | NO (by design — lower-risk surface, `tasks/` files only) | N/A | LOW (acceptable-by-design, not a gap) |

**What remains:** exactly one open gap — the **rollback default path**. This is the same gap 3C.1 identified and 3C.2 explicitly deferred (governing brief for 3C.2 excluded it "unless a strict prerequisite — none was found"). No new gap was found in this reassessment; no policy was invented.

**Ranked by real-world governance value:** the rollback gap is now the *only* remaining Permission Broker gap in the entire production mutation surface — every other root-mutating command (push, commit, promotion, alternate-push, publication) is now broker-gated. Closing it would complete Permission Broker coverage across 100% of root-mutating commands, a clean, well-defined, testable finish line.

## 8. Advisory context consumption

**Current Advisory inputs, re-verified this phase:** `core/advisory.py` imports only `pcae.core.permission_broker`; it is a pure static-dict mapper (`_BROKER_TO_ADVISORY`) from broker decision output to advisory vocabulary. It does not import RI, runtime context, authority state, historical memory, or change impact. Unchanged since 3C.1.

**Service accepts context vs. production callers populate it automatically:** `advisory/context/advisory_context_builder.py` *can* accept RI-backed context (it imports `repository_intelligence.query.query_engine`/`snapshot_loader`), but its only production caller is `commands/advisory_context.py` — a CLI entry point a human must invoke explicitly. `core/advisory.py`'s actual `pcae advisory status/check` decision path never calls the builder. So: Advisory-as-a-service accepts context; **no production caller populates it automatically** into the path a human actually runs by default (`advisory status/check`).

**Is Advisory under-consuming already-built intelligence?** Yes — `advisory_context_builder` is fully built, tested, and RI-backed, but sits unused by the main decision engine. This is the same UC classification 3C.1 gave, re-confirmed unchanged.

**Narrow consumption integration:** wiring `advisory_context_builder`'s output into `core/advisory.py`'s existing static-dict mapping (as additional, clearly-labeled informational context alongside the broker-derived vocabulary, not replacing it) is a bounded, single-direction integration — smaller in scope than the full RI→push/phase wiring in §5, since it reuses an already-RI-integrated builder rather than requiring new snapshot-freshness design work from scratch. However, it inherits the same underlying "snapshot must exist and be reasonably fresh" problem identified in §5 — `advisory_context_builder` calls `snapshot_loader.load_snapshot(path)` with the same explicit-path-only limitation.

**Classification:** Effort **S-M** (reuses an already-RI-wired builder; smaller than §5's raw RI wiring, but shares its freshness-design gap). Authority risk **LOW** (Advisory stays structurally non-authoritative — `core/advisory.py`'s output never gates or grants, confirmed unchanged this phase).

## 9. Rollback readiness/evidence integration

**Separation, confirmed from source:**
- *Rollback readiness* — no current production concept; nothing computes "is a rollback for this promotion currently safe/possible" ahead of time.
- *Rollback evidence* — `build_rollback_execution` can run in `--dry-run` mode (existing, safe, read-only) and produce evidence output, but only when a human explicitly invokes it.
- *Rollback planning* — same function, same human-only trigger.
- *Rollback execution* — the same function's non-dry-run mode; this phase does not touch it, per the No-Go list.

**Could PCAE automatically prepare/read rollback readiness/evidence before an effectful governed operation without enabling rollback execution?** Yes, architecturally — `build_rollback_execution(..., dry_run=True)` is already the exact safe, read-only code path needed; no new execution surface would be created. Re-confirmed this phase: `build_rollback_execution`'s dry-run branch performs no mutation.

**Appropriate consumer/trigger/persistence/human boundary:**
- Consumer: promotion-completion path (`pcae promote`, the only command that creates a state a rollback would ever need to reverse).
- Trigger: promotion-completion hook, informational, non-blocking (same non-blocking pattern `auto_publish_confirmed_session` already established for phase-complete).
- Persistence: alongside the promotion record (ECP/PER), a new stored dry-run rollback-readiness artifact.
- Human boundary: unchanged — real rollback execution remains 100% human-initiated via explicit CLI `--per-id`, without `--dry-run`.
- Usefulness: real but conditional — it only pays off *if* a promotion later actually needs rolling back, which is not the common case in this repo's own history (no evidence of a rollback event was found in the phases reviewed this session).
- Authority risk: **LOW** (dry-run only, no execution implication, no new authority).

**"If it only becomes useful with real execution, lower its priority":** this candidate does *not* require execution capability to be useful — its value is fully realized under the current `Observed/observe/unavailable` runtime posture, since it only pre-stages evidence for a human-invoked dry-run/real rollback later. It is not held back by the runtime-execution trust boundary. Its lower ranking (see §17) instead comes from lower expected utility (rollback events are rare) relative to its effort, not from an authority blocker.

## 10. Runtime Enforcement consumption

**Current consumers, re-confirmed this phase:** `grep -rn "RuntimeEnforcementCoordinator|RuntimeEnforcementDecision" src/pcae` returns only the two definition sites in `core/backend_invocations.py` (~9887, ~10323), both explicitly commented "design-only, non-executing, non-authorizing." Zero consumers anywhere — unchanged from 3C.1, unchanged from 3A.

**Does any production operation already invoke them?** No.

**Does the current `Observed/observe/unavailable` posture make consumption meaningful?** No safe consumption path exists: the engine's entire purpose (per its own design-only header) is to gate an *execution attempt boundary* (COMP-002) that does not exist in this codebase. There is no boundary for it to attach preflight/governance evidence to, because there is no execution attempt to precede. Wiring it in today would mean either (a) inventing a fake boundary to attach it to, which would misrepresent the runtime's actual non-executing posture, or (b) doing nothing meaningful — neither is a real integration.

**Ranked by actual product benefit now:** lowest of the six candidates. It is architecturally important *for a future execution-capable PCAE*, but connecting it today would not make PCAE more useful in its current non-executing form — it is not an "already-built intelligence PCAE fails to use," it is "infrastructure with no current consumer" per the phase brief's own low-value criterion (§12 of the governing brief). Confirmed **TB** (blocked pending an execution boundary, out of scope), not merely low-priority.

## 11. Cross-capability composition

Investigated, not assumed:

```
Repository Intelligence → Advisory
```
Real composition: §8's Advisory-Context wiring already reuses RI via `advisory_context_builder`. If §5 (RI→push/phase) is ever done first, it should establish the snapshot-freshness/fail-soft pattern that §8 can then directly reuse rather than re-deriving it — a genuine "do §5 first, §8 benefits" ordering, not a hard dependency (§8 does not require §5 to land first, since `advisory_context_builder` already exists independently).

```
Runtime introspection → capability-aware lifecycle preflight
```
Real but currently low-value composition, per §6: the registry is architecturally always empty, so a preflight check today can only produce truthful "unavailable" disclosure, not real capability-aware routing. Composing this with anything else (e.g. gating publication or promotion on capability availability) would be a new authority relationship this phase does not propose.

```
Rollback readiness → Permission Broker / publication preparation
```
Investigated: no natural composition found. Rollback readiness (§9) is scoped to promotion; the Permission Broker rollback gap (§7) is scoped to the rollback *execution* dispatch. They touch the same subsystem (`agent.py::build_rollback_execution`) but are separable — closing the broker gap does not require readiness auto-generation, and vice versa (matches 3C.1's own dependency-graph finding, re-confirmed).

```
Runtime Enforcement → future execution attempt boundary
```
Confirmed no current composition is possible (§10) — there is no boundary to compose with yet.

**Conclusion:** the one genuine "two candidates compose, one alone has little value" case investigated (RI↔Advisory) is a soft ordering preference, not a hard bundling requirement. No pair of the six candidates *requires* joint delivery to be useful individually.

## 12. User-orchestration reduction

**Repository Intelligence → push/phase:**
```
CURRENT
human
→ runs `pcae repository-intelligence query`/`change-impact` manually
→ interprets result
→ manually cross-references it against `pcae push`/`pcae phase complete` output

TARGET
pcae push / pcae phase complete
→ obtains RI change-context automatically (fail-soft if snapshot missing/stale)
→ preserves "RI is non-authoritative, informational" disclosure
→ folds it into the existing report/evidence payload
```

**Runtime/plugin orchestration (preflight disclosure):**
```
CURRENT
human
→ runs `pcae runtime inspect` separately
→ manually checks whether a workflow step's capability requirement is satisfied

TARGET
workflow preflight
→ discloses registry state (0 plugins, execution unavailable) truthfully as part of its own precondition report
→ human sees this without a separate manual inspect call
```

**Permission Broker — rollback gap:**
```
CURRENT
human
→ invokes `pcae rollback --per-id X` trusting no independent machine-checked authorization gate exists on this specific path (unlike push/commit/promotion/publication)

TARGET
pcae rollback
→ evaluated by the same Permission Broker POL-001 invariant every other root-mutating command already has
→ human experience unchanged when authorized; a denial (e.g. no active task) now fails closed exactly like every other mutating command, instead of being silently ungated
```

**Advisory-Context wiring:**
```
CURRENT
human
→ runs `pcae advisory-context build` separately
→ manually cross-references it against `pcae advisory status/check`'s own output

TARGET
pcae advisory status/check
→ obtains RI-backed context automatically, folded in as additional disclosed informational input
```

**Rollback readiness/evidence:**
```
CURRENT
human
→ (after a promotion, if something breaks) cold-starts `pcae rollback --per-id X --dry-run` to first understand what a rollback would even look like

TARGET
pcae promote
→ auto-generates dry-run rollback readiness/evidence at promotion time
→ human, if a rollback is later needed, finds pre-staged evidence instead of starting cold
```

**Runtime Enforcement:** no orchestration-reduction story exists today — there is no manual command sequence this would shorten, because the engine has no current entry point for a human to use manually either.

None of the above removes a legitimate human authorization step; each removes manual PCAE-internal command choreography or cold-start information-gathering.

## 13. Authority-risk analysis

| Candidate | Risk | Basis |
|---|---|---|
| Repository Intelligence → push/phase | LOW | Read-only, informational; RI explicitly non-authoritative |
| Runtime/plugin orchestration (preflight disclosure) | LOW | Informational only; registry is architecturally empty, nothing to gate on |
| Permission Broker — rollback gap | MODERATE | Real mutation-adjacent gate on a root-mutating command; must not weaken existing dry-run-by-default safety |
| Advisory-Context → Advisory core wiring | LOW | Advisory stays structurally non-authoritative; additive informational input only |
| Rollback readiness/evidence auto-generation | LOW | Dry-run only, no execution implication |
| Runtime Enforcement consumption | BLOCKED | No execution attempt boundary exists to gate; would require new architecture (COMP-002), out of scope |

## 14. Effort analysis

| Candidate | Effort | Basis |
|---|---|---|
| Repository Intelligence → push/phase | M | Real `push.py` semantics re-plumbing (§5) + unbuilt snapshot-freshness design (revised up from 3C.1's S-M) |
| Runtime/plugin orchestration (preflight disclosure) | S | Reuses existing `registry_health()`/`list_plugins()` pure metadata queries; no new contract |
| Permission Broker — rollback gap | S-M | Same adapter pattern as the three existing broker adapters (commit/promotion/publication); must preserve dry-run-by-default safety, so needs care, not new architecture |
| Advisory-Context → Advisory core wiring | S-M | Reuses an already-RI-wired builder; smaller than raw RI wiring but shares its freshness-design gap |
| Rollback readiness/evidence auto-generation | S-M | Reuses existing dry-run-safe `build_rollback_execution`; new persistence/trigger only |
| Runtime Enforcement consumption | L (and currently not buildable safely) | Would require building the execution boundary first — explicitly out of scope |

## 15. E2E verification designs

**Repository Intelligence → push/phase change-context wiring**
Highest-level entry point: `pcae push` / `pcae phase complete`. Trigger: any invocation. Capability invoked: `repository_intelligence.change_impact`/`historical_memory` builders (with a new freshness/fail-soft wrapper). Data/evidence: repo path, commit range, snapshot freshness state. Human boundary: none (read-only). Result consumed downstream: push/phase report/evidence payload gains RI-attributed context. Restart/resume: safe — read-only, regenerable every invocation. Idempotency: deterministic given the same repo state. Failure case: RI/snapshot unavailable or stale → fail-soft to existing raw-subprocess behavior, does not block push/phase. No-bypass assertion: the raw-subprocess fallback must remain a disclosed fallback, not become a silent default once RI is wired. Authority assertion: RI output stays disclosed as non-authoritative. Runtime assertion: `pcae runtime inspect` unchanged before/after.

**Runtime/plugin orchestration (preflight disclosure)**
Entry point: any preflight-gated command (`push`, `commit`, `promotion`, `publication` dispatch). Trigger: preflight run. Capability invoked: `registry_health()`/`list_plugins()`. Data: none beyond existing preflight context. Human boundary: none. Result: registry-state fields added to the preflight's own evidence/precondition report. Downstream consumer: the existing preflight decision output (unchanged decision logic; richer disclosure only). Restart/resume: pure read, safe every call. Idempotency: trivially idempotent. Failure case: registry read fails → preflight proceeds with existing behavior, degraded disclosure only. No-bypass assertion: cannot become a new gate without a separate, explicit authority decision. Authority assertion: no new authority introduced. Runtime assertion: `Registry status: empty`/`Plugin count: 0` must still read correctly (proves the disclosure is truthful, not fabricated).

**Permission Broker — rollback default-path gap closure**
Entry point: `pcae rollback --per-id X` (both dry-run and real). Trigger: invocation. Capability invoked: a new `mutation_permission.evaluate_rollback_permission()` adapter (mirroring the three existing adapters). Data: rollback target descriptor, active task id. Human boundary: unchanged — rollback remains explicitly human-initiated via `--per-id`; the broker adds a machine-checked gate, not a new human step. Result: ALLOW/DENY. Downstream: rollback proceeds or fails closed. Restart/resume: broker re-checked fresh every attempt, no stale caching (matches the publication-gate precedent). Idempotency: unaffected. Failure case: DENY → no rollback mutation occurs (dry-run mode must remain unaffected by DENY, since dry-run performs no mutation — this distinction must be tested explicitly). No-bypass assertion: `build_rollback_execution`'s one production caller (`agent.py:16264`) must be the only path reaching the mutating branch; the dead `create_rollback_approval_decision` path (§7, carried-forward finding) must be re-confirmed still dead or fixed in the same phase. Authority assertion: broker decision does not replace the existing human `--per-id` requirement. Runtime assertion: unchanged.

**Advisory-Context → Advisory core wiring**
Entry point: `pcae advisory status/check`. Trigger: invocation. Capability invoked: `advisory_context_builder` (existing, RI-backed). Data: repo state via RI snapshot. Human boundary: none (informational). Result: additional disclosed context alongside the existing broker-derived advisory vocabulary. Downstream: `pcae advisory status/check`'s own output, clearly labeled as separate from the authoritative broker-derived verdict. Restart/resume: safe, regenerable. Idempotency: deterministic given repo state. Failure case: RI/snapshot unavailable → fail-soft, advisory output unchanged from today's behavior. No-bypass assertion: the broker-derived advisory verdict must remain the sole authoritative field; RI-context addition must not be readable as a verdict. Authority assertion: `core/advisory.py` output remains structurally non-authoritative (never gates/grants). Runtime assertion: unaffected.

**Rollback readiness/evidence auto-generation**
Entry point: `pcae promote`. Trigger: promotion completion. Capability invoked: `build_rollback_execution(..., dry_run=True)` (existing, safe). Data: the just-completed PER/ECP identifiers. Human boundary: none (dry-run, read-only). Result: rollback-readiness artifact stored alongside the promotion record. Downstream: any future human-initiated `pcae rollback --per-id ...` finds pre-staged evidence. Restart/resume: safe to regenerate. Idempotency: regenerable without side effect. Failure case: generation fails → promotion still completes normally, absence of evidence disclosed, not fatal. No-bypass assertion: real rollback execution still requires an explicit human `pcae rollback` invocation without `--dry-run`; auto-generation never executes a rollback. Authority assertion: unchanged — rollback execution remains human-gated. Runtime assertion: unchanged.

**Runtime Enforcement consumption:** no E2E design proposed — no safe consumption path exists without first building the execution attempt boundary, which is out of scope (§10, §25).

## 16. Dependency graph

```
Repository Intelligence → push/phase wiring          : independent
Runtime/plugin preflight disclosure                    : independent
Permission Broker → rollback-gap closure                : independent (pairs naturally with,
                                                          but does not require, rollback
                                                          readiness/evidence auto-generation)
Advisory-Context → Advisory core wiring                : independent; benefits from the RI
                                                          wiring pattern if RI lands first
                                                          (soft ordering preference, not a
                                                          hard dependency — advisory_context_builder
                                                          already exists and works standalone)
Rollback readiness/evidence auto-generation             : independent (dry-run only)
Runtime Enforcement consumption                          : only useful after an execution attempt
                                                          boundary (COMP-002) exists — no such
                                                          boundary exists today; out of scope
                                                          until that architecture is built
```

No dependency in this set crosses a human-approval boundary — all sequencing above is engineering ordering, not authority ordering.

## 17. Priority ranking — Matrix C

Scored 1-5 (5=best) for value/maturity/consumption-benefit/E2E-testability/differentiation; effort and authority-risk scored 1=easiest/safest.

| Candidate | User value | Current maturity | Consumption benefit | Effort | Authority risk | E2E testability | Strategic differentiation | Rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Permission Broker — rollback gap closure | 4 | 4 | 4 | 2 (S-M) | 3 (MODERATE) | 4 | 4 | 1 |
| Runtime/plugin orchestration (preflight disclosure) | 2 | 5 | 2 | 1 (S) | 1 (LOW) | 3 | 2 | 2 |
| Rollback readiness/evidence auto-generation | 3 | 4 | 3 | 2 (S-M) | 1 (LOW) | 3 | 3 | 3 |
| Repository Intelligence → push/phase | 4 | 4 | 4 | 3 (M) | 1 (LOW) | 4 | 4 | 4 |
| Advisory-Context → Advisory core wiring | 3 | 4 | 3 | 2 (S-M) | 1 (LOW) | 3 | 3 | 5 |
| Runtime Enforcement consumption | 1 | 2 | 1 | 4 (L, blocked) | 5 (BLOCKED) | 1 | 1 | 6 |

**Re-ranking rationale, explicitly not reproducing 3C.1's provisional order:** 3C.1 ranked Repository Intelligence #1 before Plan B+ landed, when the "governance core" gap (Interactive Workflow/CHGR) was still the largest open item — RI's LOW risk made it attractive as a *first, safe* integration to prove the pattern. That pattern is now proven (§4, §12) via Plan B+ itself. With the governance-core gap closed, this reassessment finds the **remaining Permission Broker rollback gap** now ranks highest: it is the last piece needed to complete 100% broker coverage across all root-mutating commands (a clean, bounded, high-differentiation finish line — §7), it directly reuses a proven adapter pattern (§4/§14), and unlike RI it does not carry a newly-discovered effort under-count (§5). RI is re-ranked to #4, not because its value dropped, but because its effort was revised upward (§5, §14) and its authority risk, while LOW, delivers less differentiated governance value than closing the last broker gap.

## 18. Plan A — Fastest meaningful consumption gain

**Capabilities:** Runtime/plugin preflight disclosure + Rollback readiness/evidence auto-generation.
**Missing edges:** `registry_health()`/`list_plugins()` call inside existing preflight modules; new dry-run-triggered persistence at promotion completion.
**Expected files/components:** `core/*preflight*.py` (new registry-state disclosure fields); a new small module (or extension to `agent.py::build_rollback_execution` call sites) invoked from the promotion-completion path, plus a new evidence-storage location alongside PER/ECP records.
**Effort:** S + S-M (aggregate S-M).
**Authority risk:** LOW (both).
**E2E strategy:** Per §15, both individually; one small batch-level End-to-End Capability Consumption Verification phase, matching the 3C.3-precedent requirement.
**Likely release magnitude:** patch-scale (`v0.4.1`) — both are informational/evidence-only, no new user-visible behavior change beyond richer reports.

## 19. Plan B — Highest governance/autonomy value

**Capabilities:** Permission Broker — rollback default-path gap closure.
**Missing edge:** a fourth `mutation_permission` adapter (`evaluate_rollback_permission`) plus its call site in `agent.py::build_rollback_execution`'s default dispatch, mirroring the publication-gate precedent exactly (§4, §7).
**Expected files/components:** `src/pcae/core/mutation_permission.py` (new adapter); `src/pcae/commands/agent.py` (call site, dry-run-safety-preserving); possibly a small new `commands`-zone gate module if the same architecture-policy boundary issue 3C.2 hit (§5a of 3C.2) recurs for this call site — must be checked fresh, not assumed.
**Effort:** S-M.
**Authority risk:** MODERATE (real mutation-adjacent gate on a root-mutating command; requires care to preserve dry-run-by-default safety and not introduce a new blocking failure mode for the common dry-run case).
**E2E strategy:** Per §15 — must explicitly test dry-run-mode is unaffected by DENY, non-bypassability via the carried-forward dead-code path, and no weakening of the existing default-deny-safe posture.
**Likely release magnitude:** this closes the last Permission Broker coverage gap across all root-mutating commands — a genuine milestone, but scoped to one command's gating logic; likely still `v0.4.1` unless bundled with other work, in which case `v0.5.0` becomes plausible (see §20).

## 20. Plan C — Broader connected-intelligence step

**Capabilities:** Repository Intelligence → push/phase change-context wiring + Advisory-Context → Advisory core wiring (composed per §11/§16's soft-ordering preference — RI wiring first establishes the snapshot-freshness/fail-soft pattern Advisory-Context reuses).
**Missing edges:** (1) a new freshness-aware "get change context" interface `push.py`/`phase.py` can call, replacing/augmenting the inline `git log`/`git diff` subprocess logic without changing its consumer shape (per 3C.2's finding, §5); (2) auto-snapshot-generation/staleness policy (currently entirely absent); (3) wiring `advisory_context_builder`'s existing RI-backed output into `core/advisory.py`'s decision-vocabulary mapper as additional disclosed context.
**Expected files/components:** `src/pcae/commands/push.py`, `src/pcae/commands/phase.py` (or a new intermediate `commands`-zone module, following the 3C.2 architecture-policy precedent, since `commands` is the zone permitted to depend on both `core` and `repository_intelligence`); `src/pcae/repository_intelligence/snapshot_loader.py` (new freshness/auto-regeneration logic); `src/pcae/core/advisory.py` (additive context field).
**Effort:** M (aggregate — this is genuinely the largest of the three plans, per §5/§14's revised-up effort finding).
**Authority risk:** LOW (both candidates).
**E2E strategy:** One batch-level End-to-End Capability Consumption Verification phase per the 3C.3 precedent, with explicit fail-soft/staleness-handling test coverage (a new requirement category beyond what 3C.3 needed, since Plan B+ had no snapshot-freshness concept at all).
**Likely release magnitude:** `v0.5.0` — this composes two capabilities and introduces new internal architecture (snapshot freshness policy) not present in v0.4.0, materially larger in scope than a patch.

## 21. Recommended plan

**Recommendation: Priority Plan B** (Permission Broker rollback-gap closure), as the next single phase to execute if/when the human authorizes implementation.

Rationale: it completes 100% Permission Broker coverage across every root-mutating production command — the cleanest, most differentiated, most bounded governance milestone available right now; it directly reuses the exact adapter pattern that shipped and was independently verified in v0.4.0 (§4), minimizing net-new architectural risk; and unlike Repository Intelligence (§5), its effort estimate has not been revised upward by fresh re-derivation — it remains S-M as originally assessed. Plan A (runtime preflight disclosure + rollback readiness/evidence) remains a reasonable lower-stakes alternative if the human prefers to stay strictly at LOW authority risk for the next phase; it is not mutually exclusive with Plan B and could be sequenced either before or after it. Plan C is presented as the more strategically complete "connected intelligence" step but should not be the very next phase, given its effort was found to be larger than previously assessed (§5, §14) and its two capabilities are more naturally sequenced after Plan A/B establish smaller wins first.

```text
HUMAN PRIORITY SELECTION REQUIRED
```

## 22. Human decision required

Exact options for the human to choose among:

- Integrate Plan B alone (Permission Broker rollback-gap closure) — recommended as the next single phase.
- Integrate Plan A alone (runtime preflight disclosure + rollback readiness/evidence auto-generation) — lowest-risk, fastest.
- Integrate Plan A + Plan B together as one batch.
- Integrate Plan C (Repository Intelligence + Advisory-Context) as the next phase instead.
- Integrate a custom subset not enumerated above (any of the five viable candidates in §17, individually or combined, per their independent dependency-graph entries in §16).
- Defer all integration and take no further action this cycle.
- Runtime Enforcement consumption is **not** offered as a selectable option — it remains trust-blocked (§10, §25) pending an execution-attempt-boundary architecture decision out of this phase's scope.

## 23. Release implications

Per §18-20's per-plan estimates: Plan A alone is patch-scale (**v0.4.1**-plausible — informational/evidence-only, no new user-visible command behavior beyond richer reports). Plan B alone is likely also **v0.4.1**-scale on its own (one command's gating logic, following the exact pattern that already shipped in v0.4.0), though if bundled with Plan A or other work in the same release cycle, a **v0.5.0** framing becomes defensible given the cumulative "Permission Broker coverage now complete" narrative. Plan C is **v0.5.0**-scale on its own — it introduces genuinely new internal architecture (snapshot freshness/auto-regeneration policy) not present in v0.4.0, a materially larger scope than a patch. This assessment does not select a version; the eventual release-hardening phase makes that determination once the human's selected batch is actually implemented and its true final scope is known.

## 24. Already-consumed capabilities

**NO FURTHER CONSUMPTION WORK REQUIRED CURRENTLY:**

- Permission Broker — push / commit / promotion / alternate-push / **publication** (publication newly joined this list via v0.4.0, §4)
- Interactive Workflow/CHGR auto-detect + route (newly AC via v0.4.0)
- Publication Execution Ownership auto-invocation (same wiring as above, newly AC via v0.4.0)
- Decision Evaluation / Repository Transition Validator explanation-enrichment
- Authority Evaluation service via aesic → interactive_workflow
- Reporting/finalization chain (trust → certify → promote → notify)
- Telegram outbound
- Intake → validate → promote

## 25. Trust-blocked capabilities

Kept outside immediate scope; re-confirmed unchanged this phase, no evidence found that any prerequisite changed:

- HATP activation / HATP Trust-Enrollment / `HATP_MANDATORY` — re-confirmed via `core/hatp_mandatory_cutover.py`; no production/CLI/agent-reachable activation path exists.
- HMIC / Class-B positive-authority consumption — same HATP prerequisite, unchanged.
- CLTR cutover (Typed Authority Model production consumption / `authority_cutover` flag) — re-confirmed via `pcae cltr migration status`-equivalent source read: `production_authority: legacy` remains the governing state; TAMPC-001's frozen contract explicitly forbids production-module import.
- Unrestricted runtime execution — `pcae runtime inspect` unchanged: Observed/observe/unavailable throughout this phase.
- Telegram inbound — not reopened, not investigated for change (no evidence any prerequisite changed).
- Backend/model execution — `backend_invocations.py` consumers re-confirmed reporting/CLI-only; no invocation call sites found (`_invoke_backend` etc. absent).
- Runtime Enforcement Decision Engine consumption — re-confirmed §10, TB, no execution attempt boundary exists.

None of these were reopened; none were found to have a changed prerequisite.

## 26. Governance documentation observation

The 3D phase report (per the phase-entry context provided for this reassessment) noted a lifecycle bookkeeping commit used direct `git commit` per an established repository convention. This phase did not repair or investigate the underlying mechanism — per the governing brief's explicit instruction not to. A repository-wide check of whether this exception is explicitly documented in governance contracts (`.pcae/policy.toml`, `docs/contracts/*`) was not performed as part of this read-only strategic phase (out of scope of the six-candidate reassessment); absent explicit contract text found and cited, this is recorded as:

```text
NON-BLOCKING GOVERNANCE DOCUMENTATION GAP
```

for later clarification. This observation did not influence any capability's priority ranking in §17.

## 27. Final recommendation

Recommend **Plan B** (Permission Broker rollback-gap closure) as the next phase, contingent on explicit human priority selection per §21/§22. Plan A remains available as a lower-risk alternative or companion batch. Plan C remains available as the larger "connected intelligence" step but is not recommended as the immediate next phase given its revised-up effort estimate. Runtime Enforcement consumption is excluded from all plans (trust-blocked, §10/§25). No implementation occurred in this phase.

## 28. Testing strategy and tests actually run

This was a read-only strategic reassessment. No broad test suite (`pytest -m fast_green`) was run merely to rank capabilities, per the governing brief's explicit instruction. Evidence was gathered via: targeted `grep -rn`/`grep -rl` searches across `src/pcae/` re-verifying every file:line citation this phase relies on against current HEAD (not trusting 3C.1/3C.2's citations as still-accurate without re-checking); direct reads of `commands/phase.py`, `commands/governance_auto_publication.py`, `commands/publication_permission_gate.py`, `core/mutation_permission.py`, `core/advisory.py`, `core/backend_invocations.py`; and the following safe, side-effect-free CLI invocations: `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report show --latest`, plus read-only `git status`/`git log`/`git rev-parse`/`git tag`/`git diff --name-status` invocations. No production source, contract, schema, CLI implementation, or packaging configuration was modified.

## 29. Governance results

- `pcae health`: healthy
- `pcae check`: passed
- `pcae status coherence`: coherent
- `pcae doctor task-memory`: warnings only (pre-existing, unrelated `tasks/DONE.md` sync-debt entries predating this phase)
- `pcae push check`: nothing_to_push (pre-finalization baseline; re-verified at close)
- `pcae runtime inspect`: unchanged (Observed / observe / unavailable)
- Telegram: configured, enabled, ready
- Runtime: **Observed / observe / unavailable**, unchanged throughout this phase
- Article: **STOPPED** — not read, not modified, not reassessed
- `~/repos/pcae-deepseek-research`: not inspected
- No production source, CLI, contract, schema, or packaging-configuration file was modified in this phase
- No PyPI publication, tag, or GitHub Release action occurred
- No hardware provisioning, credential creation, trust-root creation, or authority cutover occurred or was proposed for action
- No integration was implemented; no priority was selected unilaterally

## 30. Summary

```text
POST-v0.4 CAPABILITY CONSUMPTION REASSESSMENT:
COMPLETE

PUBLIC BASELINE:
v0.4.0

RUNTIME:
Observed / observe / unavailable

TOP CANDIDATES:
1. Permission Broker rollback default-path gap closure
2. Runtime/plugin orchestration (preflight disclosure)
3. Rollback readiness/evidence auto-generation

PLAN A:
Runtime preflight disclosure + rollback readiness/evidence
auto-generation. S-M effort, LOW risk. Likely v0.4.1.

PLAN B:
Permission Broker rollback-gap closure -- completes 100% broker
coverage across all root-mutating commands. S-M effort, MODERATE
risk. Likely v0.4.1 (v0.5.0 if bundled with other work).

PLAN C:
Repository Intelligence -> push/phase wiring + Advisory-Context ->
Advisory core wiring. M effort (revised up from 3C.1), LOW risk.
Likely v0.5.0.

RECOMMENDED:
Plan B

IMPLEMENTATION:
NOT STARTED

HUMAN PRIORITY SELECTION:
REQUIRED

ARTICLE:
STOPPED
```
