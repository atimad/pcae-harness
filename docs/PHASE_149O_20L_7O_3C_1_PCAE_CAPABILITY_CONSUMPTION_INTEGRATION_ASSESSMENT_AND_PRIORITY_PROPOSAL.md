# Phase 149O.20L.7O.3C.1 — PCAE Capability Consumption Integration Assessment and Priority Proposal

**Status:** COMPLETE
**Phase type:** READ-ONLY EVIDENCE-DRIVEN ASSESSMENT. No production source, CLI, contract, schema, or packaging-configuration file was modified in this phase. No integration was implemented. No priority was selected unilaterally.
**Phase-entry commit:** `594f2760` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope:** `~/repos/pcae-deepseek-research` (not inspected). Article track: **STOPPED** (not read, not modified, not published).
**Canonical authority used:** `PROJECT_STATUS.md` (no conflict with `tasks/TODO.md` encountered).

## 1. Objective

Phases 3A-3C established that many PCAE capabilities are implemented, verified, packaged, CLI-exposed, and documented. That is not the same as being *consumed* — i.e. automatically invoked by PCAE's own production workflows at the point they are required. Phase 3D (public v0.3.2 release) was **stopped before publication** to allow this stronger question to be asked first:

> Identify mature PCAE capabilities that exist but are not yet consumed automatically by PCAE production workflows, determine what exact connection is missing for each, and present a prioritized integration proposal for human selection.

This phase builds a complete Capability Consumption Graph, classifies every mature capability's consumption state, and proposes (but does not select) integration priorities. **No integration was implemented in this phase. No priority was selected unilaterally — human selection is required before any implementation phase begins.**

## 2. Stopped 3D state

Phase `149O.20L.7O.3D — PCAE v0.3.2 Public Release` is **STOPPED**. Publication did not occur. No irreversible release action occurred: no v0.3.2 tag (local or remote), no GitHub Release, no artifact upload, no PyPI publication.

Reverified this phase:

```
HEAD == origin/main == 594f2760
origin/main..HEAD = 0
working tree clean, nothing staged
git diff 8bb8c882..HEAD -- src/pcae pyproject.toml  => empty (no production/build-system change)
git diff --name-status 8bb8c882..HEAD => only .pcae/phase-completion-metadata.json,
    .pcae/phase-completion-report.md, CHANGELOG.md, tasks/DONE.md, tasks/active|done/* (lifecycle bookkeeping only)
git tag --sort=-creatordate => v0.3.1, v0.3.0, v0.3.0-rc1, v0.2.0, v0.1.0-rc1 (no v0.3.2)
git rev-parse v0.3.1^{commit} => 5d7edef9c34ee266a9c5b51940ee4f1848375d22 (unchanged)
git tag -l 'v0.3.2' => (empty)
git ls-remote --tags origin 'refs/tags/v0.3.2' => (empty)
pcae health => healthy
pcae check => passed
pcae status coherence => coherent
pcae doctor task-memory => warnings only (129+ pre-existing, unrelated tasks/DONE.md sync-debt entries predating this phase)
pcae push check => nothing_to_push
pcae runtime inspect => Runtime status: not_implemented; Runtime state: Observed;
    Execution capability: unavailable; Maximum plugin capability: observe;
    Permission Broker status: execution_unavailable; Governance posture: non-executing
pcae notify status => Telegram configured, enabled, ready
```

Confirmed: repository clean, `origin/main..HEAD` = 0, no v0.3.2 release exists anywhere, v0.3.1 unchanged, runtime posture unchanged (Observed/observe/unavailable). 3C/3D history was not rewritten. The current `HEAD` differs from the frozen release-candidate commit `8bb8c882baa3c7f9fa8b1241c2b6908e253d40ae` only by lifecycle/reporting bookkeeping — no production source or build-system change.

The current v0.3.2 release candidate is treated as **SUPERSEDED / ON HOLD PENDING CAPABILITY-CONSUMPTION INTEGRATION DECISION.**

## 3. Artifact reproducibility finding (carried forward, not resolved)

3D found that the exact artifact bytes frozen by 3C no longer reproduce. Two independent fresh clones pinned to `8bb8c882baa3c7f9fa8b1241c2b6908e253d40ae` produced byte-identical artifacts to *each other* but not to 3C's originally recorded hashes:

| Artifact | Size | SHA-256 (clean-clone rebuild) |
|---|---|---|
| `pcae_harness-0.3.2-py3-none-any.whl` | 2,339,194 bytes | `c3e714b2aa430138baab5cd506256afdae74e76a1590e23159635d97054a8e60` |
| `pcae_harness-0.3.2.tar.gz` | 2,055,376 bytes | `b03cbd2090d401e09cd2cfe931eaac76b7c85d80129ebac44d4e12c45caad125` |

Likely cause: `pyproject.toml`'s `[build-system]` declares `requires = ["hatchling"]` with **no version pin**; the stopped 3D rebuild resolved `hatchling 1.32.0` (`Generator: hatchling 1.32.0` in the wheel). This was **not repaired in 3C.1** — no build-system dependency was modified, no release hash was updated, no publication was resumed, per explicit instruction.

**Carried forward as:** RELEASE-ARTIFACT REPRODUCIBILITY / PROVENANCE GAP — PUBLICATION BLOCKED UNTIL RE-VERIFIED AFTER THE NEXT INTEGRATION BATCH. The eventual release-hardening phase must assess: pinning `hatchling`, locking build dependencies, `SOURCE_DATE_EPOCH` strategy, and other reproducible-build controls — none of which were modified here.

## 4. Consumption maturity model

```
1. IMPLEMENTED
2. VERIFIED
3. PACKAGED
4. CLI/API EXPOSED
5. PRODUCTION-CONSUMED
6. AUTOMATICALLY ORCHESTRATED
7. END-TO-END INDEPENDENTLY VERIFIED
8. RELEASED
```

A capability may legitimately ship at a lower level if intentionally diagnostic/manual — this assessment makes that explicit per capability rather than assuming CLI exposure implies production consumption, or that consumption implies authority, or that orchestration implies autonomous decision authority.

## 5. Definitions used throughout

**Production-consumed** requires all of: (1) another PCAE production workflow directly invokes the production service/API/component when required; (2) the user does not need to manually execute an internal command sequence to connect it; (3) data/evidence flows through the production call graph automatically; (4) failures propagate through the calling workflow; (5) authority boundaries remain intact; (6) the consumer does not shell out to PCAE's own CLI as the integration mechanism unless a frozen architecture explicitly requires it. Preferred shape: `production workflow → production service/API → capability`, not `production workflow → subprocess("pcae ...")`.

**Automatically orchestrated** means PCAE detects when a capability is required, invokes/resumes it, passes context/evidence, and stops/continues on result — asking the human only where human authority is contractually required. Automating orchestration must never automate human authority: `PCAE orchestrates. Human authorizes where required. Capability provides governed result/evidence.`

## 6. Methodology

Five parallel read-only research passes were run against current `HEAD` source (grep import/call-site evidence, direct file reads, live read-only CLI invocations only — no mutation, no execution activation). The complete 3A capability universe (16 major areas) was re-evaluated for consumption state, not restricted to the four capabilities 3B/3C selected for documentation exposure. 3B/3C evidence was used to understand packaged surfaces/side effects/authority semantics but CLI-smoke success was never treated as proof of internal production consumption. No broad test suite was run; targeted grep/read evidence and safe read-only CLI calls were used throughout (§17 lists exact commands run).

## 7. Capability universe and production consumer graph

### 7.1 Interactive Workflow / CHGR

**Service layer (not CLI):** `src/pcae/interactive_workflow/session/coordinator.py::SessionCoordinator` (create/load/persist/validate; delegates sequencing to `orchestration/coordinator.py::WorkflowOrchestrator`), `evidence/coordinator.py::EvidenceCoordinator`, `clarification/controller.py`, `preview/builder.py::PreviewBuilder`, `confirmation/controller.py`, `interactive_workflow/application/publication_service.py`, `governance/publication/coordinator.py::PublicationCoordinator`.

A repo-wide grep for `SessionCoordinator`/`WorkflowOrchestrator`/`from pcae.interactive_workflow` outside `commands/`, `interactive_workflow/`, and `governance/` returns only: `aesic/service.py` (imports the `Session` **type** only, no coordinator call) and `core/rollback_approval_evidence.py` (imports `SessionState`/`PublicationReadinessPackage`/`generate_session_id` — types/id-generation only). **No production lifecycle module (`task.py`, `phase.py`, `push.py`, `commit.py`, `core/agent.py`'s main dispatch) imports or calls `SessionCoordinator`/`WorkflowOrchestrator`.** Session creation → evidence → select → preview → confirm is 100% human-typed CLI today; nothing in PCAE automatically detects "a human governance act is required" and routes to this system.

One real but **dead** exception: `core/rollback_approval_evidence.py::create_rollback_approval_decision()` (line 924) genuinely builds a `PublicationReadinessPackage` programmatically and drives `PublicationCoordinator.authorize()`/`.execute()` (~lines 947-979) — exactly the production-op-to-capability-service pattern the target state wants. But `create_rollback_approval_decision(` has **zero callers anywhere** in production code or CLI (confirmed by repo-wide grep); `agent.py`'s actual rollback dispatch never calls it. It is unconsumed dead code, not wired to anything real.

**CHGR downstream:** `governance-record inspect/verify` (CLI) are the only consumers found; no production workflow reads a CHGR artifact as automatic evidence/authority input.

**Classification:** Interactive Workflow/CHGR orchestration = **CLI** (real, wired, filesystem-persisted; routing into it is 100% manual). CHGR downstream consumption = **UC** (no automatic reader exists; the one programmatic-producer path is itself dead code).

```
CURRENT
PCAE operation (e.g. pcae push / pcae phase complete)
    X  no connection
Human
    ↓ manually types
pcae decision-session create/evidence/select/preview/confirm
    ↓
pcae governance-record publish

TARGET
PCAE operation
    ↓ detects human-governance-required condition
SessionCoordinator.create (existing service)
    ↓ evidence/select/preview assembled from operation context
Human confirmation boundary (unchanged — still human-typed confirm)
    ↓
PublicationCoordinator.authorize/execute → CHGR
    ↓
PCAE operation resumes/fails-closed on result
```

Effort: **M** (new detection/routing logic at the calling boundary; the target service layer already exists cleanly, no new contract). Authority risk: **MODERATE** (must preserve human confirm/select boundary).

### 7.2 CHGR downstream consumption

Covered above (§7.1). **UC.** Effort **M**, risk **LOW-MODERATE**.

### 7.3 Permission Broker

Command × broker matrix, source-verified:

| Command | Broker call | Evidence |
|---|---|---|
| `pcae push` | YES | `commands/push.py::_evaluate_push_permission()` (~478-518), `run_push` gates on `permission_result.authorized` (~643-648) |
| `pcae commit` (dispatch in `core/agent.py`) | YES | `agent.py:4710` `mutation_permission.evaluate_commit_permission(...)`, denial at 4714 |
| `pcae commit` (`commands/commit.py` primitive) | NO | zero broker/mutation_permission references (governed one layer up, at `agent.py:4710`) |
| `pcae promote` | YES | `agent.py:93726` `mutation_permission.evaluate_promotion_permission(...)`, denial 93730 |
| Alternate push path | YES | `agent.py:4862` `mutation_permission.evaluate_alternate_push_permission(...)` |
| `pcae phase complete` (commit dispatch) | YES | `commands/phase.py:18479` `mutation_permission.evaluate_commit_permission(...)` |
| `pcae task transition`/`task new` | NO | zero broker references in `task.py` (lower-risk surface: `tasks/` files only) |
| `pcae rollback` default path (`agent.py::build_rollback_execution`) | NO | no broker call in default dispatch (~94094-94130); only the optional HATP-evidence branch (94285) touches broker constants, and only when `--hatp-evidence-id` is explicitly supplied |
| CHGR publication (`PublicationCoordinator`) | NO | `governance/publication/coordinator.py` has no import of `permission_broker_foundation`/`mutation_permission` — publication executes entirely independent of the broker |

**Classification: PC (Partially Consumed).** Consumed correctly: push, commit (via agent.py dispatch), promotion, alternate-push. Real gaps: **rollback default path** (root-mutating, unguarded by the broker) and **CHGR/publication path** (the other root/external-effect-adjacent action, entirely outside broker scope). `commit.py` primitive and `task.py` bypasses are acceptable-by-design (governed one layer up / low-risk surface respectively), not counted as gaps needing closure.

Effort: publication gap **S** (one new broker-request call site, existing `PermissionBrokerRequest`/`ACTION_*` pattern); rollback gap **S-M** (same pattern, must not weaken existing dry-run-by-default safety). Risk: publication **LOW-MODERATE** (publication is already human-confirmed upstream; broker adds defense-in-depth); rollback **MODERATE** (touches real root-repo mutation).

### 7.4 Interactive publication / Publication Execution Ownership

`governance/publication/coordinator.py::PublicationCoordinator` is the actual external-effect boundary (`.authorize()`/`.execute()`). It does not call Permission Broker (confirmed §7.3). It does internally require `session_state=CONFIRMED` plus a built preview/confirmation via `PublicationReadinessPackage` — CHGR-readiness gating is real, just not broker-mediated. `PublicationCoordinator` is instantiated from exactly three places: `interactive_workflow/application/publication_service.py` (CLI-driven application service), `governance/publication/coordinator.py` (self), and the dead `core/rollback_approval_evidence.py` path (§7.1). **No non-CLI production path publishes a CHGR automatically.** Manual choreography today: 6+ manually-typed commands in exact sequence (create → evidence → select → preview → confirm → publish), no shortcut.

**Classification: CLI.** Effort **M** (service layer reusable; work is at the calling boundary). Risk **MODERATE** (must only auto-*initiate*, never auto-confirm).

### 7.5 Repository Intelligence (all sub-capabilities)

Whole-package check: `grep -rl "repository_intelligence" src/pcae --include="*.py"` outside `repository_intelligence/`, `advisory/`, `commands/` returns **only `cli.py`** (argparse wiring). This is uniform across every RI sub-capability — Repository Knowledge Snapshot, Query, Change-Impact, Dependency Knowledge Graph, Historical Memory, Cross-Artifact Integration, Unified Query, Repository Intelligence Service: **zero production consumers outside the CLI entry point.**

- Advisory: only the `advisory/context/` sub-feature imports RI (`advisory_context_builder.py:20,24` → `repository_intelligence.query.query_engine`/`snapshot_loader`). The *main* `pcae advisory status/check` decision engine (`core/advisory.py`) imports **only** `pcae.core.permission_broker` — zero RI import.
- Task planning/context construction: no consumption — `advisory_context_builder` is imported only by `commands/advisory_context.py` (CLI) and one internal RI cross-reference.
- Change-impact auto-invoked pre-push/pre-promote: **no**. `commands/push.py:321-346` and `phase.py` build ad hoc change context via raw `subprocess.run(["git","log"/"diff"...])` instead of calling RI's Change-Impact/Historical-Memory builders — exactly the job those builders already do, tested, deterministic, attributed, but unused.
- Governance/decision paths (permission_broker, authority_evaluation, decision_session): **zero** RI/advisory imports in `core/decision_evaluation.py` or `core/repository_transition_validator.py` (the real load-bearing engine imported by `phase.py`/`task.py`/`phase_reports.py`). RI's dependency-graph/historical-memory builders reference the *string* `"decision_evaluation_required": True` as self-declared output metadata — a cosmetic one-directional label, not a real call into `core.decision_evaluation`.
- Snapshot auto-discovery: **no** — `snapshot_loader.load_snapshot(path)` requires an explicit path; no auto-detection of staleness or auto-regeneration trigger exists outside manual `snapshot generate`.

**Classification: UC** uniformly across all RI sub-capabilities including Advisory-Context (which has one real internal consumer — the builder — but that builder itself has zero production callers, so it remains UC not PC).

```
CURRENT
push.py / phase.py change-context gathering
    X  no connection
    ↓ (instead) subprocess(["git","log"]) / subprocess(["git","diff"])

TARGET
push.py / phase.py change-context gathering
    ↓
repository_intelligence.change_impact.build_change_impact_report() /
repository_intelligence.historical_memory.generate_historical_memory()
    ↓ (no human boundary needed — read-only informational input)
structured, attributed evidence
    ↓
push.py / phase.py resumes with richer context
```

Effort: **M** (real service-to-service wiring, moderate coordination/testing, no new authority model). Risk: **LOW** (read-only, informational; RI is explicitly non-authoritative by its own CLI help text).

### 7.6 Advisory

`core/advisory.py` is a pure function over `pcae.core.permission_broker`'s decision output, mapped via a static dict (`_BROKER_TO_ADVISORY`) to advisory vocabulary. It imports no RI, runtime context, authority state, historical memory, or change impact — it "can accept" only what the broker already computes from CLI args/repo state at call time. **Classification: NC** for the core check/status machinery (a deliberately narrow decision-vocabulary mapper, not meant to be a context aggregator — not a gap). Advisory-Context is classified separately at §7.5 (**UC**).

### 7.7 Repository Decision / Explainability Framework

Phase 115A itself is explicitly architecture/contract-only with "zero changes to `repository_transition_integration.py`." The real implementation thread is `core/decision_evaluation.py` (115E-115G, "behavior-preserving explanation-enrichment integration"), which **is** genuinely imported by `repository_transition_validator.py`, `repository_skills.py`, `repository_skills_integration.py`, `advisory_repository_skills.py` — and `repository_transition_validator`/`repository_transition_integration` are in turn imported by `commands/phase.py`, `commands/task.py`, `commands/phase_reports.py`, `notification_certification.py`, `canonical_engineering_evidence.py`, `evidence.py`. This is a real, load-bearing production call graph already wired into phase/task finalization.

**Classification: AC.** No integration gap; nothing to recommend here.

### 7.8 Runtime/plugin introspection

Real internal (non-CLI) consumers exist:
- `core/phase_reports.py` (~3301-3310) builds a `RuntimeRegistry()`, calls `build_runtime_snapshot()`, writes `current_runtime_state`/`current_maximum_capability`/`execution_availability` into every phase report (graceful fallback on failure).
- `core/evidence_providers.py::RuntimeEvidenceProvider.collect()` (~365-410) builds a runtime snapshot and emits `Evidence` objects (`E-runtime-001/002`) into the CHGR evidence-collection stage.

Both are **read-only informational enrichment**, never a gate/precondition. Zero consumption in gating position: none of the four preflight modules (`commit_push_preflight.py`, `mutation_preflight.py`, `scope_preflight.py`, `backend_preflight.py`) import `runtime_registry`/`runtime_snapshot`/`runtime_introspection` at all.

**Classification: PC** (consumed for reporting/evidence enrichment; not consumed for preflight/gating). Missing edge: preflight modules could consult `runtime_registry.registry_health()`/`list_plugins()` to disclose "0 plugins registered, execution unavailable" as part of their own precondition report, but don't. Effort **S**, risk **LOW** (informational only, no execution implication).

### 7.9 Runtime registry / plugin capability resolution

`RuntimeRegistry` (`core/runtime_registry.py:320-409`) exposes only pure metadata queries (`list_plugins`, `list_capabilities`, `find_capability`, `get_plugin_metadata`, `registry_health`, `validate_consistency`) — no `resolve`/`get_capability`-style provider-selection method exists. The only caller of `find_capability`/`list_plugins` outside the registry module itself is `runtime_introspection.py`. No workflow does `request capability → registry resolves provider → checked → continue/fail`; since the registry is always empty (0 plugins, architectural invariant), such resolution would always fail. Backend/provider selection (§7.10) is hard-coded identity metadata, not registry-mediated. (Note: `agent.py`'s many `RuntimeRegistry*` hits are an unrelated Phase 61A design-document generator producing a static scaffolding dict, `execution_allowed: False` — not the real `core.runtime_registry.RuntimeRegistry` class; confirmed by reading context.)

**Classification: UC.** Effort N/A (would require plugin loader architecture — out of scope). Risk **BLOCKED/TB** for anything beyond metadata inspection.

### 7.10 Backend/provider subsystem

Consumers of `backend_invocations.py`: `runtime_introspection.py`, `runtime_registry.py`, `commands/backend.py`, `commands/agent.py` — all reporting/CLI-wiring. `permission_broker_foundation.py` only *mentions* `backend_invocations` in a docstring listing modules it deliberately does **not** import — confirming intentional non-coupling, not a wired relationship. `pcae agents adapters --json` confirms Claude/Codex/Codex-Ox/Kimi are pure registration/identity records (`adapter_type: cli/native`, `lifecycle_status: available`); no actual invocation call sites (`_invoke_backend`, adapter execution dispatch) exist in `agent.py`. Codex-Ox confirmed descriptive-identity-only.

**Classification: TB** (intentionally unconsumed — execution capability architecturally absent, not merely a configuration gap). No effort proposed; risk **BLOCKED** by design (hard-stopped, §38).

### 7.11 Runtime Enforcement Decision Engine

`grep -rn "RuntimeEnforcementCoordinator|RuntimeEnforcementDecision"` returns only the two definition sites in `backend_invocations.py` (lines 9968, 10369) plus their own "design-only, non-executing, non-authorizing" section-header comments — zero consumers anywhere at current HEAD, unchanged from 3A. It does not sit "behind" Permission Broker in any wired sense (confirmed via the docstring above). No safe dry-run/advisory-only consumption path exists today because no execution boundary (`COMP-002`) exists for it to gate — this is unbuilt architecture, not a wiring gap.

**Classification: TB.** Effort **L** (would require building the execution boundary first — out of scope). Risk **BLOCKED**. Do not propose execution activation.

### 7.12 Authority Evaluation / canonical authority resolver

Two architecturally distinct services, previously conflated by 3A's single "A/B" rating:

**`src/pcae/authority_evaluation/`** — a pure, disclosure-only `evaluate()` (no I/O, no side effects, "never determines legal authority, never grants/denies/authorizes anything"). Consumers (grep-verified): `src/pcae/aesic/{diagnostics,records,registry_filesystem,resolution,service}.py`, which is in turn consumed by `commands/aesic_status.py`, `commands/decision_session.py`, and **`interactive_workflow/application/session_service.py`** — the real production path into `SessionCoordinator`. `governance/publication/record.py` does not import `authority_evaluation`/`aesic` directly; it carries a passthrough `authority_evaluation_ref`/`citation_text` disclosure pair on the publication package (lines 262-273), consistent with "disclosure not permission." No duplicated ad-hoc authority-reconstruction logic found bypassing this path.

**Classification: AC.** Production-consumed correctly; no gap.

**`src/pcae/cltr/authority/`** (Stage 3 "Typed Authority Model", ~8,936 lines, 16 record-family models) — a **separate package** whose own `__init__.py` explicitly states no production runtime module (lifecycle, finalization, notification, marker/receipt creation, publication, recovery, authority selection, execution coordinator, permission broker, runtime decision engine) may import it. Grep-confirmed: zero production modules outside `src/pcae/cltr/authority/` itself import it. Its sole consumer is `cltr/authority_inspection.py`, itself explicitly "representation-only observation" behind `pcae authority inspect`.

**Classification: TB** — intentionally unconsumed by frozen architectural boundary (a TAMPC-001 contract), not a wiring gap.

### 7.13 `pcae authority inspect`

Confirmed a thin CLI frontend whose entire implementation lives in `authority_inspection.py` (the TB-classified typed model above). It reads only explicitly-supplied artifact bytes plus packaged schema resources — no repository discovery, no lifecycle mutation, no authority resolution.

**Classification: NC** (diagnostic/administrative frontend, not a capability needing its own consumer). The underlying resolver it inspects is the TB-classified typed authority model (§7.12), not the AC-classified `authority_evaluation` service — a correction to 3A's write-up, which slightly conflated the two.

### 7.14 CLTR / lifecycle state infrastructure

Live `pcae cltr migration status --json`: `authoritative: false, authority_cutover: false, production_authority: "legacy", migration_stage: "shadow_observation", shadow_enabled: false, dual_derivation_enabled: false, migration_evidence_only: true, transition_evidence_count: 0`. Beyond 3A: even the *shadow* observation/dual-derivation flags are currently **off** — there is presently no active internal shadow-write consumer populating comparison state, a step below what the stage name "shadow_observation" implies.

- **Cutover-authority portion** (the typed authority model, §7.12): **TB** — blocked on an explicit authority-cutover decision, hard-stopped.
- **Shadow/derivative infrastructure portion**: **UC** — exists, inert, zero current internal consumers populating it. Distinct from TB: enabling shadow observation would not itself grant authority (`migration_evidence_only: true` stays true) — it's unwired, not authority-blocked. Effort **M**, risk **MODERATE** (still touches lifecycle bookkeeping even if evidence-only).

### 7.15 Reporting / finalization

`commands/phase.py::run_phase_complete` → `_finalize_report_and_notify()` → report-trust validation → `certify_notification_transition()` → `blockers_are_push_state_only()` gate → `finalize_phase_report()` promotion+dispatch. One CLI call drives trust check → certification → promotion → notification automatically, with no manual intermediate steps.

**Classification: AC.** No further consumption work required.

### 7.16 Telegram outbound

Same automatic chain as §7.15 terminates in notification dispatch; idempotency (`PAYLOAD_CONFLICT`/`ALREADY_DISPATCHED`) is enforced centrally, not per-caller. No new callers since 3A.

**Classification: AC.** Do not propose inbound Telegram (hard-stopped).

### 7.17 Shell Gate

**Enforcement:** `run_shell_gate_check` has exactly one caller in production source — `cli.py:5372` (CLI dispatch table). No pre-exec hook/wrapper/interception point exists anywhere else.

**Classification (enforcement): TB** — no execution boundary exists to hook into; not a wiring gap, hard-stopped per §38 (no automatic shell enforcement proposed).

**Audit persistence:** `grep -rln "shell-gate-audit\|shell_gate_audit"` outside the shell-gate command/core modules returns only `cli.py` dispatch wiring. Explicitly checked `push.py`/`phase_reports.py` — zero mentions. No other workflow (push check, phase complete, governance-drift review) reads shell-gate audit records automatically; it is purely a diagnostic browser (`shell-gate audit show/list/verify`).

**Classification (audit persistence): UC**, low-value gap. A diagnostic audit browser legitimately need not have another consumer — but if PCAE ever wants "did governance-drift review show risky-command classifications" surfaced automatically (e.g. in `pcae health`), that is the missing edge. Effort **S**, risk **LOW**.

### 7.18 Rollback

`build_rollback_execution` has exactly one caller: `commands/agent.py:16264` — the `pcae rollback` CLI dispatch path, confirmed 100% human-initiated via `--per-id`. Zero references to "rollback" in `push.py`; no workflow auto-generates rollback readiness/evidence when a promotion or push occurs.

**Classification (rollback execution): CLI** — correct and appropriate as-is; no execution elevation is proposed. **Classification (rollback readiness/evidence generation, dry-run-safe): UC** — a real, in-scope, low-risk gap: nothing pre-stages rollback evidence at promotion time, so a human recovering from a broken promotion must know to manually invoke `pcae rollback --per-id ... --dry-run` cold. Effort **S-M**, risk **LOW** (dry-run only, no execution change).

```
CURRENT
promotion completes
    X  no connection
    ↓ human manually runs `pcae rollback --per-id X --dry-run` later if something breaks

TARGET
promotion completes
    ↓
rollback readiness/evidence auto-generated (dry-run, read-only)
    ↓
stored alongside promotion record
    ↓
human still explicitly invokes real rollback via CLI if ever needed
```

### 7.19 Intake / review / promotion

`commands/intake.py` is thin CLI plumbing over `pcae.core.intake.validate_and_ingest_intake_candidate`, which already performs validation + ECP construction + **promotion** inline in one call (result carries `promotion_executed`/`execution_allowed`/`idempotent_replay`). Intake → validate → promote is already **one automatic chain** triggered by a single CLI call, not three manual steps.

`review.py` (`run_lifecycle_review_create/show/list`) is a separate, manual, CLI-only surface with no import/call linkage from `intake.py` — a **genuine human decision boundary by design**: a lifecycle review is a human-authored judgment on already-promoted/executed work, correctly not auto-chained.

**Classification:** intake→promotion = **AC**. Lifecycle review = **NC** (intentional human boundary, not a consumption gap).

### 7.20 HATP / HMIC / Class-B

Re-confirmed unchanged from 3A via current source: `core/hatp_mandatory_cutover.py` still states no production/CLI/agent-reachable path can activate `HATP_MANDATORY`; the one optional HATP-evidence consumption path in `agent.py::build_rollback_execution` engages only when a deployment's cutover mode is already `HATP_MANDATORY`, which requires out-of-band human filesystem access to activate. Trust-Enrollment artifacts remain absent on the one test host. No new HATP/HMIC/Class-B evidence found since 3A.

**Classification: TB** for all authority-facing HATP/HMIC/Class-B consumption. Read-only diagnostic surfaces may remain NC/AC as informational only; no positive-authority consumption is proposed.

## 8. Human-boundary analysis

For every candidate below, the target state explicitly preserves a human decision point where one currently exists:

| Candidate | Human boundary preserved |
|---|---|
| Interactive Workflow/CHGR auto-detect+route | Human still explicitly confirms/selects; only *routing into* the session is automated |
| Publication auto-invocation | Human still explicitly confirms before `PublicationCoordinator.execute()` runs |
| Permission Broker rollback/publication gaps | No new human step added or removed — broker adds a machine-checked gate, not a human one |
| CHGR downstream consumption | Read-only evidence consumption; does not touch who authorizes |
| Repository Intelligence internal consumption | Read-only informational input; RI stays non-authoritative |
| Runtime introspection preflight gating | Informational disclosure only; no gating authority added |
| Rollback readiness/evidence auto-generation | Real rollback execution stays 100% human-initiated via explicit CLI `--per-id` |
| CLTR shadow infrastructure | Evidence-only; `production_authority` stays `legacy` |
| Advisory-Context → Advisory core wiring | Advisory stays structurally non-authoritative (`performed_flags_always_false`) |
| Shell-gate audit surfacing | Diagnostic surfacing only; enforcement remains untouched |

None of the proposed integrations remove a human authorization step. All of them remove *manual PCAE-internal command choreography* the human currently has to perform by hand to connect an already-authorized or already-non-authoritative capability.

## 9. Matrix A — Consumption State

| Capability | Implemented | Verified | Packaged | CLI/API | Production-consumed | Auto-orchestrated | E2E verified | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Permission Broker (push/commit/promotion) | yes | yes | yes | yes | yes | yes | yes (per-command tests) | AC |
| Permission Broker — rollback default path | yes | yes | yes | yes | no | no | no | UC |
| Permission Broker — CHGR publication path | yes | yes | yes | yes | no | no | no | UC |
| Interactive Workflow/CHGR orchestration (routing) | yes | yes | yes | yes | no | no | no | CLI |
| CHGR downstream consumption | yes | yes | yes | yes (viewer only) | no | no | no | UC |
| Publication Execution Ownership (auto-invocation) | yes | yes | yes | yes | no | no | no | CLI |
| Repository Intelligence (all sub-capabilities) | yes | yes | yes | yes | no | no | no | UC |
| Advisory-Context (RI-backed) | yes | yes | yes | yes | no | no | no | UC |
| Advisory core (status/check) | yes | yes | yes | yes | yes (broker only, by design) | yes | yes | NC |
| Decision Evaluation / Repository Transition Validator | yes | yes | yes | n/a (internal) | yes | yes | yes | AC |
| Authority Evaluation service (via aesic) | yes | yes | yes | n/a (internal) | yes | yes | yes | AC |
| `pcae authority inspect` command | yes | yes | yes | yes | n/a (diagnostic) | n/a | n/a | NC |
| Typed Authority Model (`cltr/authority/`) | yes | yes | yes | yes (inspect only) | no (by frozen contract) | no | no | TB |
| CLTR shadow/dual-derivation infra | yes | partial | yes | yes | no (flags off) | no | no | UC |
| CLTR authority cutover | no (shadow only) | n/a | yes | yes (read-only) | no | no | no | TB |
| Runtime/plugin introspection — reporting/evidence | yes | yes | yes | yes | yes | yes | yes | PC |
| Runtime/plugin introspection — preflight gating | yes | yes | yes | yes | no | no | no | UC |
| Runtime registry capability-resolution | yes (metadata only) | yes | yes | yes | no | no | no | UC |
| Runtime Enforcement Decision Engine | yes (design) | no | yes | no | no | no | no | TB |
| Backend/provider invocation (execution) | no (by design) | n/a | yes (identity) | yes (identity) | no | no | no | TB |
| HATP Trust-Enrollment / `HATP_MANDATORY` | yes | partial | yes (opt-in extra) | yes | no | no | no | TB |
| HMIC / Class-B positive-authority | yes | one indeterminate read | yes | no (no standalone CLI) | no | no | no | TB |
| Reporting/finalization chain | yes | yes | yes | yes | yes | yes | yes | AC |
| Telegram outbound | yes | yes | yes | yes | yes | yes | yes | AC |
| Shell Gate enforcement | yes (sim only) | yes | yes | yes | n/a (no boundary) | no | no | TB |
| Shell-gate audit persistence | yes | yes | yes | yes | no (diagnostic-only) | no | no | UC |
| Rollback execution (CLI dispatch) | yes | yes | yes | yes | yes (by design, human-gated) | n/a | yes | CLI |
| Rollback readiness/evidence auto-generation | yes (manual only) | yes | yes | yes | no | no | no | UC |
| Intake → validate → promote | yes | yes | yes | yes | yes | yes | yes | AC |
| Lifecycle review | yes | yes | yes | yes | n/a (human artifact) | n/a | n/a | NC |

**Totals (30 audited items):** AC = 6, PC = 1, CLI = 3, UC = 10, TB = 7, NC = 3.

## 10. Matrix B — Consumer Gap

| Capability | Production owner | Current consumer | Expected consumer | Manual choreography today | Missing edge | Human boundary retained? | Risk |
|---|---|---|---|---|---|---|---|
| Permission Broker — rollback | `permission_broker_foundation.py` | none (default path) | `agent.py::build_rollback_execution` | none needed — gap is invisible to human | broker-request call site in default rollback dispatch | yes | MODERATE |
| Permission Broker — publication | `permission_broker_foundation.py` | none | `governance/publication/coordinator.py` | none needed | broker-request call site in `PublicationCoordinator.execute()` | yes | LOW-MODERATE |
| Interactive Workflow/CHGR routing | `interactive_workflow/session/coordinator.py` | none (CLI only) | `phase.py`/`push.py`/`agent.py` at governance-required detection points | 6+ manually-typed commands | detection logic + `SessionCoordinator.create()` call at calling boundary | yes | MODERATE |
| CHGR downstream consumption | `governance/publication/record.py` | none | evidence/authority-consuming workflows | manual `governance-record inspect` | automatic CHGR discovery/read at consuming workflow | yes | LOW-MODERATE |
| Repository Intelligence | `repository_intelligence/*` | `cli.py` only | `push.py`/`phase.py` change-context gathering, `decision_evaluation.py` | manual `snapshot generate`/`query`/`change-impact` invocation | service call replacing raw `git log`/`git diff` subprocess use | yes (read-only, no boundary needed) | LOW |
| Advisory-Context | `advisory/context/advisory_context_builder.py` | `commands/advisory_context.py` only | `core/advisory.py` main check machinery | manual `advisory context build` | wiring RI-backed context into advisory's decision vocabulary | yes | LOW |
| Runtime introspection (preflight) | `core/runtime_registry.py` | `phase_reports.py`, `evidence_providers.py` (reporting only) | preflight modules (`backend_preflight.py` etc.) | manual `pcae runtime inspect` | `registry_health()`/`list_plugins()` call inside preflight | yes | LOW |
| Shell-gate audit persistence | `.pcae/shell-gate-audit/` store | none (diagnostic browser only) | `pcae health`/governance-drift review | manual `shell-gate audit show/list/verify` | summary-surfacing call in health/drift review | yes | LOW |
| Rollback readiness/evidence | `agent.py::build_rollback_execution` | none (default path) | promotion completion path | manual `pcae rollback --per-id --dry-run` after the fact | auto-generate dry-run evidence at promotion time | yes | LOW |
| CLTR shadow infra | `cltr/` migration module | none (flags off) | task/phase/commit/push lifecycle (observation only) | none (currently inert) | enable shadow-write population, evidence-only | yes | MODERATE |

## 11. Matrix C — Integration Priority

Scored 1-5 for value/maturity/verification/benefit/testability/release-value (5=best); effort and authority-risk scored 1=easiest/safest.

| Capability | User value | Maturity | Verification | Consumption benefit | Effort | Authority risk | E2E testability | Release value | Rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Repository Intelligence → push/phase change-context wiring | 5 | 5 | 5 | 5 | 2 (S-M) | 1 (LOW) | 4 | 5 | 1 |
| Permission Broker — CHGR publication gap closure | 3 | 4 | 4 | 4 | 1 (S) | 2 (LOW-MOD) | 4 | 2 | 2 |
| Runtime introspection → preflight gating disclosure | 3 | 5 | 5 | 3 | 1 (S) | 1 (LOW) | 3 | 2 | 3 |
| Rollback readiness/evidence auto-generation | 3 | 4 | 4 | 3 | 2 (S-M) | 1 (LOW) | 3 | 2 | 4 |
| Advisory-Context → Advisory core wiring | 3 | 4 | 4 | 3 | 2 (S-M) | 1 (LOW) | 3 | 3 | 5 |
| Shell-gate audit surfacing into `pcae health` | 2 | 4 | 3 | 2 | 1 (S) | 1 (LOW) | 2 | 1 | 6 |
| Interactive Workflow/CHGR auto-detect+route | 5 | 5 | 5 | 5 | 3 (M) | 3 (MODERATE) | 4 | 5 | 7 |
| Publication Execution Ownership auto-invocation | 4 | 5 | 5 | 4 | 3 (M) | 3 (MODERATE) | 4 | 4 | 8 |
| Permission Broker — rollback gap closure | 3 | 4 | 4 | 4 | 2 (S-M) | 3 (MODERATE) | 4 | 2 | 9 |
| CHGR downstream automatic consumption | 3 | 3 | 3 | 3 | 3 (M) | 2 (LOW-MOD) | 3 | 2 | 10 |
| CLTR shadow/dual-derivation infra | 2 | 3 | 2 | 2 | 3 (M) | 3 (MODERATE) | 2 | 1 | 11 |

Ranking method: candidates 1-6 are the S/M-effort, LOW-risk "fast" tier ranked by (value × benefit) / effort with risk as a tiebreaker; candidates 7-10 are the higher-value but M-effort/MODERATE-risk "governance-core" tier; candidate 11 is lowest priority (low release value, moderate risk, moderate effort — poor ROI relative to the rest).

## 12. Mandatory provisional candidates — final ranked answer

The phase brief's six seed candidates, evidence-ranked (source evidence, not assumed order):

1. **Repository Intelligence internal consumption** (§7.5) — UC, effort S-M, risk LOW, highest value/effort ratio. Top priority.
2. **Permission Broker production-consumption completeness** (§7.3) — PC with two concrete, small, LOW/MODERATE-risk gaps (publication, rollback).
3. **Runtime/plugin introspection/capability consumption** (§7.8-7.9) — PC (reporting) / UC (gating); the gating gap is S-effort, LOW-risk.
4. **Interactive Workflow / CHGR automatic consumption** (§7.1, §7.4) — highest strategic/governance value but M-effort and MODERATE authority risk; the flagship "governance core" candidate, not the cheapest one.
5. **Authority Evaluation / canonical authority service consumption** (§7.12) — **already AC**; no integration work required. The typed authority model it might be confused with is TB by frozen contract.
6. **Runtime Enforcement consumption** (§7.11) — TB; no safe consumption path exists without building a new execution boundary, which is out of scope. Not a near-term candidate.

## 13. Already-consumed exclusions — NO FURTHER CONSUMPTION WORK REQUIRED

Confirmed from source; excluded from the integration proposal:

- Permission Broker — push / commit / promotion / alternate-push (§7.3)
- Decision Evaluation / Repository Transition Validator explanation-enrichment (§7.7)
- Authority Evaluation service via aesic → interactive_workflow (§7.12)
- Reporting/finalization chain (trust → certify → promote → notify) (§7.15)
- Telegram outbound (§7.16)
- Intake → validate → promote (§7.19)

## 14. Trust-blocked exclusions — DO NOT SELECT FOR IMMEDIATE INTEGRATION

| Capability | Exact blocking prerequisite |
|---|---|
| Typed Authority Model (`cltr/authority/`) production consumption | Frozen architectural contract (TAMPC-001) explicitly forbids any production module import; requires a deliberate authority-cutover decision, out of scope here |
| CLTR authority cutover (`authority_cutover`/`authoritative` flags) | Same — explicit cutover decision required; currently `production_authority: legacy` |
| HATP Trust-Enrollment / `HATP_MANDATORY` activation | Real hardware Trust-Enrollment ceremony; only reachable via out-of-band human filesystem access, non-agent-reachable by design |
| HMIC / Class-B positive-authority consumption | Same HATP activation prerequisite; only one INDETERMINATE non-canonical live read has ever existed |
| Runtime Enforcement Decision Engine consumption | No execution boundary (`COMP-002`) exists anywhere for it to gate; would require new architecture |
| Backend/provider execution invocation | Execution capability architecturally absent (signed `execution_available: false` proof); hard-stopped |
| Shell Gate enforcement (interception) | No pre-exec hook/wrapper exists anywhere; same missing execution boundary as Runtime Enforcement |

None of these are proposed for integration in any plan below.

## 15. Cross-capability interaction assessment

Coherent composition batches found in the evidence:

```
Repository Intelligence (change-impact/historical-memory)
→ push.py / phase.py change-context gathering
→ (optionally, later) Advisory-Context / decision_evaluation enrichment
```

```
Permission Broker
→ CHGR publication path (defense-in-depth before)
→ Interactive Workflow/CHGR auto-detect+route (adds a new auto-triggered publication caller)
```

```
Runtime introspection (registry_health)
→ preflight modules (informational disclosure only)
```

```
Promotion completion
→ rollback readiness/evidence auto-generation (dry-run only)
→ (shares the broker-gap-closure pattern with rollback default-path gating)
```

Unrelated wiring to avoid: CLTR shadow infra does not naturally compose with any of the above (it is isolated lifecycle-bookkeeping observability) — including it only for "more integrations" would not create a coherent end-to-end improvement; it is listed as optional/lowest-priority, not bundled by default.

## 16. Integration dependency graph

```
Repository Intelligence → push/phase wiring         : independent
Runtime introspection → preflight gating            : independent
Permission Broker → publication-path gap closure    : SHOULD land before/with
Interactive Workflow/CHGR auto-detect+route          : depends on publication-path
                                                        gap closure landing first
                                                        (defense-in-depth before adding
                                                        a new auto-triggered publication caller)
Publication Execution Ownership auto-invocation      : same work as CHGR auto-detect+route
                                                        (not a separate dependency)
Permission Broker → rollback-path gap closure        : pairs naturally with, but does
                                                        not require, rollback readiness/
                                                        evidence auto-generation
Rollback readiness/evidence auto-generation          : independent (dry-run only)
CHGR downstream automatic consumption                : depends on CHGR auto-detect+route
                                                        landing first (no point consuming
                                                        what nothing yet produces
                                                        automatically) — though existing
                                                        manually-created CHGRs could be
                                                        consumed independently as a smaller
                                                        first step
Advisory-Context → Advisory core wiring              : independent; benefits from RI
                                                        wiring pattern established first
                                                        (same integration shape)
CLTR shadow/dual-derivation infra                    : fully independent, optional
```

No dependency requires crossing a human-approval boundary — all sequencing above is engineering ordering, not authority ordering.

## 17. E2E verification designs (for every recommended candidate)

**Repository Intelligence → push/phase change-context wiring**
Starting state: clean repo, RI snapshot absent or stale. Trigger: `pcae push` or `pcae phase complete`. Auto-invoked: `repository_intelligence.change_impact`/`historical_memory` builders. Data in: repo path, commit range. Human intervention: none (read-only). Result: structured, attributed change-context object. Downstream consumer: push/phase evidence/report payload. Expected final state: report contains RI-attributed change context instead of raw git-subprocess text; behavior otherwise unchanged. Retry/idempotency: safe to regenerate every invocation (read-only, deterministic). Failure case: RI unavailable/stale → falls back to existing raw-subprocess behavior, does not block push/phase. No-bypass assertion: the raw-subprocess path is only a fallback, not a silent default once RI is wired. Authority assertions: RI output is disclosed as non-authoritative, matches existing CLI help text.

**Permission Broker — CHGR publication-path gap closure**
Starting state: a `CONFIRMED` `PublicationReadinessPackage` exists. Trigger: `PublicationCoordinator.execute()`. Auto-invoked: `permission_broker_foundation.PermissionBroker` request/decision. Data in: publication action descriptor. Human intervention point: none new (human already confirmed upstream). Result: `authorized`/`denied` decision. Downstream consumer: `execute()` proceeds or fails closed. Expected final state: identical to today when authorized; publication blocked with a clear denial when not. Retry: broker re-checked fresh each publish attempt (no stale caching). Failure case: broker denial → publication does not occur, CHGR not created. Idempotency: unaffected (unchanged from current publication idempotency markers). No-bypass assertion: no alternate `execute()` path skips the broker call. Authority assertions: broker decision does not replace human confirmation, only adds a machine-checked gate after it.

**Runtime introspection → preflight gating disclosure**
Starting state: any preflight invocation (e.g. `backend_preflight.py`). Trigger: preflight run. Auto-invoked: `runtime_registry.registry_health()`/`list_plugins()`. Data in: none beyond existing preflight context. Human intervention: none. Result: runtime-state fields added to preflight's evidence dict. Downstream consumer: preflight's existing evidence/decision output. Expected final state: preflight decision logic unchanged; only disclosed evidence is richer. Retry/idempotency: pure read, safe on every call. Failure case: registry read fails → preflight proceeds with existing behavior, degraded disclosure only. No-bypass assertion: informational-only, cannot become a new gate without a separate explicit authority decision. Authority assertions: no new authority introduced.

**Rollback readiness/evidence auto-generation**
Starting state: a promotion has just completed. Trigger: promotion-completion hook. Auto-invoked: `build_rollback_execution(..., dry_run=True)` (existing dry-run-safe code path). Data in: the just-completed PER/ECP identifiers. Human intervention: none (dry-run, read-only). Result: rollback readiness/evidence artifact stored alongside the promotion record. Downstream consumer: any future human-initiated `pcae rollback --per-id ...` invocation, which now finds pre-staged evidence. Expected final state: promotion record gains an attached rollback-readiness artifact; no mutation occurs. Retry: safe to regenerate. Failure case: generation fails → promotion still completes normally, absence of evidence is disclosed, not fatal. No-bypass assertion: real rollback execution still requires an explicit human `pcae rollback` invocation without `--dry-run` — auto-generation never executes a rollback. Authority assertions: unchanged — rollback execution remains one of the two root-mutating, human-gated commands.

## 18. Batch-level End-to-End Capability Consumption Verification requirement

Whichever capabilities the human selects, they must **not** be considered complete on individual unit/integration verification alone. The eventual integration phase(s) must be followed by one independent phase — **End-to-End Capability Consumption Verification** — proving, for the entire selected batch:

- PCAE itself invokes the selected capabilities automatically (no operator-typed internal command choreography remains for the wired paths).
- Production services are called directly (no `subprocess("pcae ...")` self-shelling).
- Sequencing, state/evidence flow, and failure propagation are all correct.
- Retries/resumption are correct and idempotent; no duplicate governance artifacts are produced.
- Human authority remains explicit at every boundary identified in §8; no capability self-authorizes.
- No unauthorized fallback and no execution-capability elevation occurred anywhere in the batch.

This phase must run **before** any subsequent release-hardening phase.

## 19. Priority Plan A — Lowest Risk / Fastest

**Capabilities:** Repository Intelligence → push/phase change-context wiring; Permission Broker CHGR publication-path gap closure; Runtime introspection → preflight gating disclosure; Rollback readiness/evidence auto-generation.

**Benefits:** All four are S/S-M effort, LOW authority risk, no new authority model, no new human-facing behavior change (only richer disclosure or a machine-checked gate behind an already-human-confirmed action). Establishes the "production service, not CLI shell-out" wiring pattern the rest of the roadmap can reuse.

**Required integration phases:** One phase, or two small phases if the human prefers RI-wiring separated from the Permission-Broker/introspection/rollback trio.

**Required E2E verification:** One batch-level End-to-End Capability Consumption Verification phase per §18, scoped to these four.

**Expected release impact:** Plausibly still `v0.3.2`-scale (no new commands, no behavior change visible to users beyond richer reports/evidence and one new internal gate) — but see §20 for the version-decision caveat.

## 20. Priority Plan B — Highest Governance Value

**Capabilities:** Interactive Workflow/CHGR auto-detect+route; Publication Execution Ownership auto-invocation (same work); Permission Broker rollback-path gap closure; CHGR downstream automatic consumption.

**Benefits:** Closes the single biggest, most strategically visible gap identified in this assessment — PCAE's own most mature governance capability (CHGR) is currently 100% human-orchestrated even though its production service layer is clean and ready. Directly answers the objective that motivated stopping 3D.

**Required integration phases:** At least two — (1) detection/routing + publication auto-invocation, sequenced after Plan A's publication-permission-gap closure lands; (2) CHGR downstream automatic consumption, sequenced after (1).

**Required E2E verification:** One batch-level End-to-End Capability Consumption Verification phase per §18, scoped to this batch, with explicit "no-self-authorization" and "human confirmation still required" assertions given the MODERATE authority risk.

**Expected release impact:** Materially changes production call graphs (new auto-triggered publication paths) — likely `v0.4.0`, not a patch-level bump.

## 21. Priority Plan C — Broader Connected PCAE

**Capabilities:** Everything in Plan A + Plan B, plus Advisory-Context → Advisory core wiring, plus Shell-gate audit surfacing into `pcae health`. CLTR shadow infra explicitly **excluded by default** (lowest rank, poor ROI) but available as an optional add-on if the human wants full coverage of every non-TB candidate.

**Benefits:** The most complete realization of "PCAE consumes its own mature capabilities automatically" across governance, intelligence, and introspection layers in one coherent roadmap.

**Required integration phases:** The union of Plan A's and Plan B's phases, plus one small phase for Advisory-Context wiring and one for shell-gate audit surfacing (both independent, either order).

**Required E2E verification:** One batch-level verification phase per §18 covering the full set (or two, gated by sub-batch, if the human prefers incremental verification).

**Expected release impact:** `v0.4.0` at minimum, given the scope; the batch is materially larger than a documentation/hardening patch.

## 22. Matrix E — Proposed Plans

| Plan | Capabilities | Effort | Authority risk | Expected user improvement | Likely release version | Required phases |
|---|---|---|---|---|---|---|
| A — Lowest Risk/Fastest | RI wiring, PB publication-gap, runtime-introspection preflight, rollback evidence auto-gen | S-M (aggregate) | LOW | Richer evidence/reports, one new gate, no visible behavior change | v0.3.2-plausible | 1-2 integration + 1 E2E verification |
| B — Highest Governance Value | CHGR auto-detect+route, publication auto-invocation, PB rollback-gap, CHGR downstream consumption | M (aggregate) | MODERATE | PCAE self-triggers governance workflow instead of requiring 6+ manual commands | v0.4.0 | 2 integration + 1 E2E verification |
| C — Broader Connected PCAE | A + B + Advisory-Context wiring + shell-gate audit surfacing | M-L (aggregate) | LOW-MODERATE | Most complete self-consumption across governance/intelligence/introspection | v0.4.0 | 3-4 integration + 1-2 E2E verification |

## 23. Recommended plan

**Recommendation: Priority Plan A**, as the first phase to execute if/when the human authorizes implementation. Rationale: it proves the "production service, not CLI shell-out" integration pattern this whole roadmap depends on, at the lowest possible authority risk, before touching the higher-stakes CHGR auto-routing work in Plan B. Plan B remains the strategically most important follow-on and should be sequenced next regardless of whether Plan A or a different starting point is chosen. Plan C is presented as the complete picture, not a recommended single starting point — its scope is better executed as Plan A followed by Plan B followed by the two small remaining items, rather than as one large batch.

**This recommendation is not a decision.** Alternatives (Plan B first, Plan C in full, or any other evidence-derived subset) remain fully available.

## 24. Human decision required

> **Human selection required before implementation.** No integration was implemented in this phase, and no priority was selected unilaterally.

Exact options for the human to choose among:

- Integrate only Interactive Workflow/CHGR + Publication auto-invocation (the core of Plan B, standalone).
- Integrate Interactive Workflow/CHGR + Repository Intelligence (a custom cross-plan subset).
- Integrate the "governance core" set (Plan B in full).
- Integrate all S/M, LOW/LOW-MODERATE-risk candidates (Plan A in full).
- Integrate everything non-TB (Plan C in full, with or without CLTR shadow infra).
- Select a different evidence-derived combination not enumerated above.
- Defer all integration and resume 3D publication as-is (not recommended, given the strategic reassessment that stopped 3D, but remains the human's choice).

## 25. Release/version implications

The stopped v0.3.2 release candidate (`8bb8c882`) is **not preserved automatically**. Once any selected integration batch modifies production call graphs (Plan B or C), `v0.3.2` is very likely the wrong version label — this assessment recommends the eventual release-hardening phase evaluate `v0.4.0` for any batch beyond Plan A. Plan A alone could plausibly remain `v0.3.2`-scoped (no new commands, no new user-visible behavior), but this is a release-hardening-phase decision, not a decision made here. **Version decision comes after priority selection, not before.**

## 26. Deferred / trust-blocked capabilities

See §14 for the full table. Summary: Typed Authority Model / CLTR authority cutover, HATP Trust-Enrollment / `HATP_MANDATORY` activation, HMIC / Class-B positive-authority consumption, Runtime Enforcement Decision Engine consumption, Backend/provider execution invocation, Shell Gate enforcement. None are candidates for any of the three proposed plans.

## 27. Artifact reproducibility carry-forward

Restated from §3, unmodified in this phase:

```
Build system:
hatchling unpinned

Release artifact reproducibility:
not sufficiently frozen across independent sessions

Publication:
blocked pending future release-hardening re-verification
```

## 28. Exact minimum next phases

1. **Human priority decision** (not a PCAE phase — a decision by the user, per §24).
2. **Integration phase(s)** matching the selected plan (Plan A: 1-2 phases; Plan B: 2 phases; Plan C: 3-4 phases) — no source implementation occurred in 3C.1; this is the first phase where production source may change.
3. **End-to-End Capability Consumption Verification** (§18) — mandatory, independent, batch-level, before any release-hardening phase.
4. **Release-hardening / RC phase** — re-addresses the artifact-reproducibility gap (§27) and re-freezes a release candidate, informed by whatever version §25 determines is now correct.
5. **Public release phase** — only after all of the above, following the same governed publication procedure used for v0.3.1.

No architecture, contract, or authority-cutover phase is recommended by this assessment.

## 29. Testing strategy and tests actually run

This was a read-only assessment. No broad test suite was run. Evidence was gathered via: targeted `grep -rn`/`grep -rl` searches across `src/pcae/` for import/call-site evidence (avoiding reliance on grep-string-matching alone where aliasing/indirection mattered — e.g. distinguishing the real `core.runtime_registry.RuntimeRegistry` from an unrelated Phase 61A scaffolding function of a similar name); direct reads of the relevant production source files cited by file:line throughout §7; and the following safe, side-effect-free CLI invocations: `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report show --latest`, `pcae cltr migration status --json`, `pcae agents adapters --json`, `git status`/`git log`/`git diff`/`git tag`/`git ls-remote` (all read-only). No production source, contract, schema, CLI implementation, or packaging configuration was modified.

## 30. Governance results

- `pcae health`: healthy
- `pcae check`: passed
- `pcae status coherence`: coherent
- `pcae doctor task-memory`: warnings only (129+ pre-existing, unrelated `tasks/DONE.md` sync-debt entries predating this phase)
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

## 31. Summary

```
CAPABILITY CONSUMPTION ASSESSMENT:
COMPLETE

CAPABILITIES AUDITED: 30
  ALREADY CONSUMED (AC): 6
  PARTIALLY CONSUMED (PC): 1
  CLI-ONLY / HUMAN-ORCHESTRATED (CLI): 3
  UNCONSUMED INTERNAL (UC): 10
  TRUST-BLOCKED (TB): 7
  NOT A CONSUMABLE CAPABILITY (NC): 3

ALREADY CONSUMED:
Permission Broker (push/commit/promotion), Decision Evaluation /
Repository Transition Validator, Authority Evaluation service (via
aesic), Reporting/finalization chain, Telegram outbound,
Intake -> validate -> promote

PARTIALLY CONSUMED:
Runtime/plugin introspection (reporting/evidence yes, preflight
gating no)

CLI-ONLY / HUMAN-ORCHESTRATED:
Interactive Workflow/CHGR orchestration, Publication Execution
Ownership auto-invocation, Rollback execution (by design)

UNCONSUMED INTERNAL:
Repository Intelligence (all sub-capabilities), Advisory-Context,
Permission Broker rollback/publication gaps, CHGR downstream
consumption, Runtime introspection preflight gating, Runtime
registry capability-resolution, CLTR shadow infra, Shell-gate audit
persistence, Rollback readiness/evidence auto-generation

TRUST-BLOCKED:
Typed Authority Model / CLTR authority cutover, HATP Trust-
Enrollment / HATP_MANDATORY, HMIC/Class-B positive-authority,
Runtime Enforcement Decision Engine, Backend/provider execution,
Shell Gate enforcement

TOP INTEGRATION CANDIDATES:
1. Repository Intelligence internal consumption
2. Permission Broker production-consumption completeness
   (publication + rollback gaps)
3. Runtime/plugin introspection preflight gating
4. Interactive Workflow / CHGR automatic consumption (highest
   strategic value, higher effort/risk)

RECOMMENDED PRIORITY PLAN:
Plan A (Lowest Risk / Fastest), with Plan B recommended as the
next follow-on regardless of starting point

IMPLEMENTATION:
NOT STARTED

HUMAN PRIORITY DECISION:
REQUIRED

FUTURE INDEPENDENT END-TO-END CONSUMPTION VERIFICATION:
MANDATORY FOR ALL SELECTED CAPABILITIES

v0.3.2:
NOT RELEASED

3D:
STOPPED

ARTIFACT REPRODUCIBILITY:
NOT RESOLVED -- CARRIED FORWARD, PUBLICATION BLOCKED PENDING
RE-VERIFICATION AFTER NEXT INTEGRATION BATCH

RUNTIME:
Observed / observe / unavailable

ARTICLE:
STOPPED
```
