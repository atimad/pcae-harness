# Phase 149O.20L.7O.3A — Existing Capability Confirmation, Integration Gap, and Quick-Release Audit

**Status:** COMPLETE
**Phase type:** READ-ONLY AUDIT + PRODUCT GAP ANALYSIS. No production source, CLI, contract, or packaging-configuration change was made in this phase.
**Phase-entry commit:** `d2d406c3` (HEAD at phase start; `git log origin/main..HEAD` = 0, working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope:** `~/repos/pcae-deepseek-research` (not inspected).
**Canonical authority used:** `PROJECT_STATUS.md` (no conflict with `tasks/TODO.md` was encountered requiring adjudication).

## 1. Baseline confirmation

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (in sync) |
| `git log origin/main..HEAD` | 0 commits |
| Latest tag | `v0.3.1` (v0.3.0, v0.3.0-rc1, v0.2.0, v0.1.0-rc1 also present, all intact) |
| `pcae health` | healthy; git status clean; session continuity verified |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings only — 129 pre-existing `tasks/DONE.md` sync-debt entries, all predating this phase, repository-maintainer-only, not touched by this audit |
| `pcae push check` | nothing_to_push |
| `pcae runtime inspect` | `Runtime status: not_implemented`, `Runtime state: Observed`, `Execution capability: unavailable`, `Maximum plugin capability: observe`, `Permission Broker status: execution_unavailable`, `Governance posture: non-executing`, 0 registered plugins |
| Telegram | configured, enabled, ready for outbound delivery (`pcae notify status`) |
| `pcae phase-report show --latest` | Phase 149O.20L.7O.2Z.1, COMPLETE, recommended next phase pre-3A was the (out-of-scope-here) article-reassessment discussion phase |

No active governed phase existed before this session started 3A. PyPI remains unpublished. Article track untouched (not read, not modified).

## 2. Methodology

Five parallel read-only research passes were run against current `HEAD` source, live CLI output, and existing tests (no new tests written; no broad suite run). Historical phase docs and `PROJECT_STATUS.md`/`CHANGELOG.md` were used as secondary evidence only — every classification below is grounded in current source file/function citations and/or live command output captured during this phase, not phase titles or historical claims. Where current source contradicted a historical "complete"/"certified" claim, current source won.

Classification scheme (unchanged from phase brief): **A** Released, **B** Release-ready, **C** Integration gap, **D** Verification gap, **E** Authority/trust gap, **F** Prototype/contract only, **G** Deferred/substantial new work.

## 3. Product surface reconstruction

`src/pcae/commands/` contains 62 command modules registered in `src/pcae/cli.py` (852 `add_parser`/`set_defaults(func` sites). `pyproject.toml` packages `src/pcae` wholesale (`packages = ["src/pcae"]`); nothing in the six capability-area module directories examined (`repository_intelligence/`, `advisory/`, `authority_evaluation/`, `hatp/`, `cltr/`, `interactive_workflow/`) is excluded from the wheel/sdist, and none carry non-`.py` resource files needing separate `package_data` declarations. A real, separate packaging gap exists for the top-level `schemas/` directory (sibling to `src/`, not under `src/pcae`), self-disclosed in `CHANGELOG.md` under Phase 136E as `PREREQUISITE-136E-1` ("current wheel/sdist packaging scope does not include `schemas/`") — carried forward as known debt, not fixed here.

The runtime posture is uniformly non-executing across every subsystem inspected: `pcae runtime inspect --json` marks `execute`/`enforce` capabilities `undeclarable: true`; `pcae backend execution-boundary proof --json` returns a signed proof with `execution_available: false`, `subprocess_execution_available: false`, `real_ai_backend_calls_available: false`. This is an architectural invariant the project treats as a stable non-regression, not a defect.

## 4. Capability classifications by area

### 4.1 Permission Broker — **B** (release-ready; effectively already released in v0.3.1's own mutation paths, but the broker's own foundation module self-labels every decision `implementation_status="execution_unavailable"`)

`src/pcae/core/permission_broker_foundation.py` is the frozen single policy decision point (Phase 108A). Real, non-bypassable consumption exists: `push.py::_evaluate_push_permission()`/`run_push()` (line ~643-648) hard-gates the real `git push` dispatch on `permission_result.authorized`, with a freshness re-check immediately before dispatch. `src/pcae/core/mutation_permission.py` (Phase 149F) extends this to commit/promotion/alternate-push sites consumed from `src/pcae/core/agent.py` (lines ~4706-4991) and `src/pcae/commands/phase.py` (lines ~18475-20386), both of which `return`/block on an unauthorized result. `mutation_permission.py`, `push.py`'s gate, and `permission_broker_foundation.py` are byte-identical between `v0.3.1` and current `HEAD` (`git diff v0.3.1..HEAD` empty on these paths) — this is genuinely in the released product. 126 test files reference the broker, including dedicated production-consumption suites (`tests/test_permission_broker_push_production_consumption.py`, `tests/test_mutation_permission_commit_integration.py`, `tests/test_mutation_permission_push_routing_integration.py`).

**Exact remaining gap:** `src/pcae/commands/commit.py` (the low-level staged-commit primitive) and the preflight-only modules (`commit_push_preflight.py`, `mutation_preflight.py`, `scope_preflight.py`, `backend_preflight.py`) still self-declare `"permission_broker_not_implemented": True` and never call the broker directly — governance is enforced one layer up (in `agent.py`/`phase.py`), not inside the primitive. AG3/AG5 (rollback) and TK1-3 (task-finish) mutation sites are explicitly noted in the Phase 149F commit message as untouched.

### 4.2 Runtime Enforcement — **F** (prototype/contract only)

`RuntimeEnforcementCoordinator`/`RuntimeEnforcementDecision` (`src/pcae/core/backend_invocations.py`, ~lines 9968/10369) carry section headers literally reading "design-only, non-executing, non-authorizing." `grep` confirms zero consumers anywhere outside that one file; no CLI subcommand exposes them. **Exact remaining gap:** no caller anywhere, and no execution boundary (`COMP-002`, per the Permission Broker's own component registry) exists for it to gate — this is unbuilt architecture, not a wiring gap.

### 4.3 Shell Gate — **F** for enforcement, **D** for the underlying classification/audit layer

`run_shell_gate_check()` docstring: "Never executes. Simulation-only." Sole entry point is the explicit CLI (`pcae shell-gate check`); nothing pipes real shell invocations through it before execution. It does produce a large, real, tamper-checkable audit trail: `.pcae/shell-gate-audit/` holds **200,988 files, ~785 MB** — genuine evidence of self-classification runs, not of intercepted real commands. **Exact remaining gap:** no pre-exec hook/wrapper exists anywhere in the repo; turning classification into enforcement needs the same missing execution boundary as 4.2. The 785 MB audit corpus is flagged as operational debt (§8), not remediated.

### 4.4 HATP / hardware-backed trust — **F/E** for anything authority-facing; narrow **C** for the already-wired-but-unreachable rollback-evidence consumption path

Extensive real source exists (20+ core modules, `pcae hatp sign` CLI) and `build_rollback_execution` in `agent.py` has a genuine optional HATP-evidence consumption path (`agent.py` ~94100-94125) — real integration, not a stub. But it only engages when a deployment's cutover mode is `HATP_MANDATORY`, and `hatp_mandatory_cutover.py`'s own docstring states there is **no production-, CLI-, or agent-reachable path that can activate `HATP_MANDATORY`** — a human with direct filesystem access to the protected root must do it out-of-band. The most recent HMIC activation phase doc (`docs/PHASE_149O_20L_7O_2N_5_...md`) headlines "HATP STILL NOT READY/NOT ACTIVE, NO REAL FIDO2 HARDWARE EFFECT" — Trust-Enrollment artifacts (`HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`) are entirely absent on the one test host (`hac-dell`) that has any real HMIC certification at all. `docs/PHASE_149O_20L_7O_2Z_1_PUBLIC_RELEASE.md` explicitly lists "HATP/FIDO2/WebAuthn or Dell deployment work" as not performed for v0.3.1; `README.md`/`CHANGELOG.md` have zero HATP/HMIC mentions; the `hatp-hardware` extra is opt-in, not a base dependency.

**Exact remaining gap:** real Trust-Enrollment ceremony + full Class-B provisioning + `HATP_MANDATORY` activation, none reachable through any governed path today by design. This is a hard-stop area under §38 of the phase brief (hardware provisioning, trust-root creation, HMIC activation). The `pcae hatp sign` CLI surface and `hatp_class_b_conformance.verify_class_b_deployment_conformance`/`assess_hatp_mandatory_activation_readiness` read functions are inert/diagnostic-safe without real credentials, but are not recommended for headline release marketing (§4.5 covers why).

### 4.5 Class-B verifier — **D** as read-only diagnostic, **C** as an authority/readiness consumer

`hatp_class_b_conformance.py` is real and is consumed as one readiness term inside `assess_hatp_mandatory_activation_readiness`, but that consumer is itself production-unreachable (4.4). The only live read on the actual test host returned `INDETERMINATE` and was explicitly disclaimed by its own phase doc as "not an authoritative Class-B verdict" (non-canonical SSH-as-root context). No dedicated CLI subcommand exposes Class-B conformance standalone (`pcae hatp --help` shows only `sign`). **Exact remaining gap:** no standalone CLI exposure, and no canonical-context authoritative result has ever been produced. Per phase-brief §15, no positive-authority integration is proposed here.

### 4.6 Rollback — **A** (released) for the core PER-rollback path; the HATP-gated extension inherits 4.4's E/F status and is correctly optional/inert

`pcae rollback --per-id PER_ID [--hatp-evidence-id EVIDENCE_ID] [--dry-run] [--json]` is real: `--dry-run` performs zero mutation; without it, `run_rollback`→`build_rollback_execution` really reverts a PER's writes using the originating ECP's before-content/hashes, producing a Rollback Execution Record. `README.md` documents this as one of only two commands in PCAE's history that mutate the root repository (with `pcae promote`), both gated on prior human-reviewed evidence. Unchanged across v0.1.0-rc1 through v0.3.1. Already released — not a candidate for the next release batch, but worth noting as confirmation that the release story already includes a solid governed-mutation example.

### 4.7 Repository Intelligence — mixed: **B** for the RKS/Query/Advisory-Context/Change-Impact core, **C** for Dependency Graph / Historical Memory / Cross-Artifact Integration, **F** for Unified Query and the "Repository Intelligence Service"

`pcae repository-intelligence {snapshot,query,change-impact,dependency-graph,historical-memory,cross-artifact-integration,unified-query,service}` is fully CLI-registered and was exercised live during this audit:
- `snapshot generate` produced a real artifact (20 architectural entities, 2 subsystems, 5 knowledge claims, 27 sources, 4 declared unknowns), backed by `tests/test_phase_120e_repository_knowledge_snapshot.py` (14 tests).
- `query` returned real deterministic JSON with attribution/limitations/boundary disclosures (`tests/test_phase_121e_...py`, 15 tests).
- `advisory context build` layers on the query engine (`tests/test_phase_122e_...py`, 22 tests).
- `change-impact` is real and tested (`tests/test_phase_123e_...py` + `124e` hardening, 21 tests combined).
- `dependency-graph generate` executed live (21 nodes, 20 edges, 41 dependency claims, `completeness_state: "partial"`) but is self-labeled "prototype" in its own test filename (`tests/test_phase_126e_dependency_knowledge_graph_prototype.py`, 38 tests).
- `historical-memory generate` genuinely walks this repo's 5,493-commit git history and `tasks/done/`; also self-labeled "prototype" (`tests/test_phase_127e_..._prototype.py`, 50 tests).
- `cross-artifact-integration` connects change-impact↔dependency-graph via stable IDs, CLI help text says "read-only, no execution, no traversal, no reasoning" (31 tests, "prototype" in filename).
- `unified-query` and `service` CLI help text literally self-declare "prototype" (Phase 131E/132E); `service --kind` even admits "composite requests are not exposed via this CLI surface in this prototype; use the Python API directly."

**Cross-cutting integration-gap finding:** `grep -rl "repository_intelligence\."` outside `repository_intelligence/`, `advisory/`, and `commands/` returns only `cli.py` (argparse wiring). **No other PCAE subsystem — governance decisions, execution pathway, promotion/rollback — reads any Repository Intelligence artifact.** The entire capability family is real, deeply tested (200+ tests across the pipeline), CLI-exposed, and byte-unchanged since v0.3.1, but is invisible to users because it is not documented as a supported release feature (not in `README.md`'s golden path, not headlined in `CHANGELOG.md`'s v0.3.1 notes) and has zero producer→consumer wiring into the rest of the system.

### 4.8 Advisory — **F/E** for the core check machinery (structurally, permanently non-authoritative by design), **B** for the Advisory-Context sub-feature (shared with 4.7)

`pcae advisory status`/`pcae advisory check` are real, working, read-only evaluators (`src/pcae/core/advisory.py`) — verified live (`pcae advisory check --command "git status" --json` returns a genuine structured decision). But the command's own JSON self-declares `"implementation_status": "prototype"`, `"phase": "88X"`, and hard-codes `performed_flags_always_false: true` — this is architected to never become authoritative without a distinct trust/authorization prerequisite, a ceiling the project's own 138A-141G "Advisory Governance" chapter (26 phases) deliberately held at "Stage 3, Advisory use." Not a quick-release integration target; already usable as-is for its intended read-only purpose.

### 4.9 Plugin/runtime architecture and runtime introspection — **F** (contract/metadata-only, but complete and honestly self-scoped)

No plugin loader exists anywhere (`grep` for `plugin.py`/`plugins/` under `src/pcae` finds nothing beyond metadata modules). `src/pcae/core/runtime_registry.py`'s own docstring: "owns plugin metadata only — it never loads, imports, instantiates, invokes, or executes a plugin... Current implementation status: execution unavailable." `pcae runtime {snapshot,inspect}` is real and was exercised live: `registered_plugin_count: 0`, `registry_status: "empty"`, all 10 declared capabilities (`observe`/`advise`/`approve`/`deny`/`enforce`/`execute`/`audit`/`notify`/`store`/`rollback_prepare`) have empty `declaring_plugin_ids`, `lifecycle_stage: "Observed"` (max of a 7-stage ladder). This is consistent across dozens of CHANGELOG entries treated as an invariant non-regression, not a bug. Test coverage: `tests/test_runtime_registry_prototype.py`, `test_runtime_registry_contract.py`, `test_runtime_introspection_prototype.py` (74 tests), `test_runtime_introspection_architecture.py` (53 tests).

**Exact remaining gap:** `pcae runtime inspect`/`snapshot` already form a coherent, demonstrable, honestly-labeled "what does the runtime currently know about itself" capability — this is releasable as a transparency/introspection feature exactly as-is, with zero execution-capability change, because it only ever reports the (always-true) absence of loaded plugins. Going from 0→N actual plugins requires new architecture (loader, sandbox, capability enforcement) and is correctly out of scope (G-level) for any quick release.

### 4.10 Canonical lifecycle / CLTR — **G** (deferred/substantial new work)

`grep -n "cltr" src/pcae/commands/{task,phase,commit,push}.py` returns zero matches. `pcae cltr migration status --json` self-reports, verbatim: `"authoritative": false, "authority_cutover": false, "production_authority": "legacy", "migration_stage": "shadow_observation"`. Task/phase/commit/push lifecycle is still driven entirely by the legacy `tasks/active|done` directory convention, not CLTR. This is exactly the kind of authority-cutover work the phase brief warns is unlikely to be quick-release-ready, and current evidence (the tool's own status output) confirms the migration has not started, not merely stalled partway. **Not a candidate.**

### 4.11 Human governance / interactive workflow / CHGR — **A** (released), with a discoverability caveat

`pcae decision-session {create,evidence,select,clarify,preview,confirm,status,readiness,cancel}` and `pcae governance-record {inspect,verify,template,publish}` are real, filesystem-backed (`FilesystemSessionRepository`, `FilesystemPendingReadinessStore`), byte-identical to `v0.3.1`, documented with full CLI syntax in `docs/COMMANDS.md`, and have been used dozens of times in this project's own `CHANGELOG.md` history to authorize real repository actions — proven in continuous real use, not just isolated tests. `docs/PHASE_145H5_...md` records a 390-test chapter-scoped regression pass and a "READY FOR ... CERTIFICATION" verdict.

**Exact remaining gap:** none in implementation/verification/integration — this is already shipped and load-bearing. The gap is pure discoverability: `README.md` and `docs/QUICKSTART_V0_3.md` only mention the `pcae intake` golden path; `decision-session`/`governance-record` appear only in the secondary `docs/COMMANDS.md` reference. A capability this mature, sitting outside the primary onboarding story, is a strong candidate for the next release's documentation/exposure work even though its code is unchanged.

### 4.12 Authority Evaluation — **A/B** for the service substrate (already production-consumed), **C** for the standalone inspector CLI

`src/pcae/authority_evaluation/` is consumed by `aesic/*`, `interactive_workflow/*`, `governance/publication/record.py`, and directly wired into `decision_session.py`'s `SessionCoordinator` — i.e., live in the path every governance decision goes through. 8 distinct `tests/test_phase_147*.py` files span implementation, independent verification, integration, and persistence-hardening cycles. Unchanged since `v0.3.1`. But `pcae authority inspect` (`src/pcae/commands/authority_inspect.py`) — a separate, self-declared "representation-only, non-authoritative" record viewer — has **zero mentions in `docs/COMMANDS.md`** and much thinner dedicated test coverage (2 files) than the service it inspects (8 files).

**Exact remaining gap:** the standalone `pcae authority inspect` command boundary is undocumented and under-tested relative to its sibling capability; the service itself needs nothing further.

### 4.13 Telegram / notifications — **A** (released)

`pcae notify {status,test,send-report}` is real, configured in this environment (verified live), outbound-only by explicit design (`telegram_inbound_available: false` per `pcae backend execution-boundary proof`), and genuinely wired into `pcae phase complete`'s finalization transaction (`phase.py::_finalize_report_and_notify()` → `certify_notification_transition()`), with idempotency markers shared across `phase complete`, `phase-report create`, and `notify send-report`. 170 test files reference notifications; unchanged since v0.3.1. No remaining gap; the absence of inbound control is a deliberate, hard-stopped design boundary (§38), not a defect.

### 4.14 Audit / evidence persistence — **A** (released) for the user-facing capability, with disclosed operational debt

`pcae shell-gate audit {show,list,verify}` and `pcae phase-report {show,trust,consistency,reconcile}` already form a complete, wired, read-only "show me the audit trail" surface — `phase-report reconcile` explicitly cross-checks promoted-report/marker/checkpoint/receipt agreement. This is already integrated and exposed, not "one small step away." Operational debt noted (not remediated): `.pcae/shell-gate-audit/` is 785 MB / 200,988 files; `.pcae/phase-audits/` holds 98 more snapshots; `CHANGELOG.md`'s Phase 145G entry documents a prior CI race caused by a corrupted/tampered record in this same directory.

### 4.15 Backend/provider adapters — **F** for execution capability across every provider (by architecture, proven via a signed execution-boundary proof, not merely unconfigured); registration/identity depth varies

`pcae runtime inspect --json` marks `execute`/`enforce` `undeclarable: true`; `pcae backend execution-boundary proof --json` returns `execution_available: false`, `real_ai_backend_calls_available: false`, `simulation_only: true`. Capability matrix (from `pcae agents adapters --json` / `pcae backend list --json`):

| Provider | Registered | Locally detected | Execution code | Classification |
|---|---|---|---|---|
| Claude | yes | yes (CLI v2.1.243) | none | D (identity solid, execution n/a by design) |
| Codex | yes | yes (CLI v0.149.1) | none | D |
| Codex-Ox | yes (identity only) | unknown | none | D |
| Kimi | yes | yes (CLI v0.6.0) | none | D |
| DeepSeek | partial (`claude-deepseek` in backend list; agent-adapter side "undeclared") | null | none | C/G |
| Gemini / Grok / Perplexity | declared placeholders | null | none | G — "Adapter not yet declared" |
| Manual/noop (`pcae-native`) | yes | n/a | mock only | D |

`agents adapters --json` self-disclaims: "Adapter reporting is advisory; no agent runtime is modified." Not a quick-release candidate — closing the F gap would mean real execution activation, hard-stopped by §38.

### 4.16 Packaging gaps — trivial for the six named capability-area modules; a real, already self-disclosed gap in `./schemas/`

See §3. No action taken.

## 5. Matrix A — Capability State

| Capability | Implementation | Verification | Integration | Authority | Packaging | User surface | Released | Class |
|---|---|---|---|---|---|---|---|---|
| Permission Broker (push/commit/promotion gating) | complete | strong (126 test files) | non-bypassable at agent.py/phase.py/push.py | non-authoritative by design (execution_unavailable label) | clean | CLI + internal | yes (v0.3.1) | B |
| Runtime Enforcement Coordinator | complete (design) | none (no consumer) | none | n/a | clean | none | no | F |
| Shell Gate (classification/audit) | complete | strong | CLI-only, no interception hook | n/a | clean | CLI | yes (as simulation tool) | F/D |
| HATP core + rollback-evidence path | extensive | partial (one test host) | real but production-unreachable | E (no trust root/enrollment) | clean, hardware extra opt-in | none documented | no | F/E/C |
| Class-B verifier | complete | one indeterminate live read | internal-only consumer | E | clean | none | no | D/C |
| Rollback (PER) | complete | strong | wired, README-documented | released authority | clean | CLI | yes (v0.1.0-rc1+) | A |
| Repository Intelligence — RKS/Query/Advisory-Context/Change-Impact | complete | strong (~70 tests) | CLI-only, zero external consumers | n/a (read-only) | clean | CLI | shipped, undocumented | B |
| Repository Intelligence — Dependency Graph/Historical Memory/Cross-Artifact | complete | strong (~119 tests) | CLI-only, self-labeled prototype | n/a | clean | CLI | shipped, undocumented | C |
| Repository Intelligence — Unified Query/Service | complete | strong (93 tests) | CLI-only, self-declared prototype | n/a | clean | CLI (partial) | shipped, undocumented | F |
| Advisory (check/status) | complete | strong | wired to shell-gate/broker | E (structurally non-authoritative) | clean | CLI | shipped | F/E |
| Runtime/plugin registry + introspection | complete (metadata layer) | strong (127+ tests) | self-contained, honestly scoped | n/a | clean | CLI | shipped, undocumented | F |
| CLTR (canonical lifecycle) | partial (shadow only) | n/a | none — legacy authority still in force | n/a | clean | CLI (read-only) | shipped as read-only tool | G |
| Interactive Workflow / CHGR | complete | strong (390-test chapter run) | fully wired, real filesystem persistence | released authority | clean | CLI, docs/COMMANDS.md only | yes (v0.3.1) | A |
| Authority Evaluation service | complete | strong (8 test files) | wired into aesic/decision-session | released authority | clean | internal + `authority inspect` CLI | yes (v0.3.1) | A/B |
| `pcae authority inspect` (standalone) | complete | thin (2 test files) | isolated, undocumented | non-authoritative by design | clean | CLI, undocumented | technically yes, invisible | C |
| Telegram/notifications | complete | strong (170 test files) | wired into `phase complete` | n/a | clean | CLI | yes (v0.3.1) | A |
| Audit/evidence persistence (shell-gate audit, phase-report reconcile) | complete | strong | wired | n/a | clean | CLI | yes (v0.3.1) | A |
| Backend/provider adapters (execution) | none by design | n/a | n/a | E (execution boundary absent) | clean | CLI (identity only) | identity yes, execution no | F/G |

## 6. Matrix B — Gap

| Capability | Exact remaining gap | Source/consumer boundary | Est. effort | Authority risk | Release value |
|---|---|---|---|---|---|
| Repository Intelligence (B-rated core) | Not documented in README/QUICKSTART/CHANGELOG headline; no other subsystem consumes it | `cli.py` is the only external caller of `repository_intelligence.*` | low (docs only) | none | high |
| Runtime/plugin introspection | Not documented/marketed as a supported transparency feature | none needed — self-contained | low (docs only) | none | medium-high |
| Interactive Workflow/CHGR | Absent from README/QUICKSTART primary onboarding | none needed — already wired | low (docs only) | none | high |
| `pcae authority inspect` | Undocumented in docs/COMMANDS.md, thin dedicated tests | `authority_inspect.py` → `authority_evaluation` package | low (docs + optional test addition) | none | low-medium |
| Permission Broker | `commit.py` primitive and 4 preflight modules don't call the broker directly (enforced one layer up instead) | `commands/commit.py`, `commit_push_preflight.py`, `mutation_preflight.py`, `scope_preflight.py`, `backend_preflight.py` | moderate (real integration work, not docs) | low | low (already effectively released) |
| Dependency Graph / Historical Memory / Cross-Artifact | Self-labeled "prototype," zero external consumers | `repository_intelligence/{dependency_graph,historical_memory,cross_artifact_integration}` → no consumer outside CLI/tests | moderate | none | medium |
| Class-B verifier | No standalone CLI exposure; only one, disclaimed, non-canonical live read exists | `hatp_class_b_conformance.py` → no CLI command | moderate | low-medium (do not propose positive authority) | low |
| HATP Trust-Enrollment/activation | No production-reachable activation path anywhere; requires real hardware ceremony | `hatp_mandatory_cutover.py` → no reachable caller | substantial | high (hard-stopped by §38) | n/a — excluded |
| CLTR authority cutover | `task.py`/`phase.py`/`commit.py`/`push.py` don't consume CLTR state at all | none — cutover unstarted | substantial | high (authority migration) | n/a — excluded |
| Backend execution | No execution boundary exists for any provider | none — architectural | substantial | high (hard-stopped by §38) | n/a — excluded |

## 7. Matrix C — Candidate Ranking

Scored 1–5 (5 = best/highest) per §25 axes; effort/verification-effort/authority-risk/packaging-complexity scored so that 1 = best (lowest).

| Candidate | User value | Maturity | Verification confidence | Integration effort | Authority risk | Packaging complexity | Release differentiation | Recommendation |
|---|---|---|---|---|---|---|---|---|
| Repository Intelligence exposure (RKS/Query/Advisory-Context/Change-Impact) | 5 | 5 | 5 | 1 | 1 | 1 | 5 | INTEGRATE NOW (doc/expose) |
| Runtime/plugin introspection exposure | 4 | 5 | 5 | 1 | 1 | 1 | 4 | EXPOSE/PACKAGE NOW |
| Interactive Workflow / CHGR discoverability | 4 | 5 | 5 | 1 | 1 | 1 | 3 | EXPOSE/PACKAGE NOW |
| `pcae authority inspect` documentation | 2 | 4 | 3 | 1 | 1 | 1 | 2 | EXPOSE/PACKAGE NOW (bundle-in) |
| Permission Broker primitive-level closure (commit.py/preflight modules) | 3 | 4 | 4 | 3 | 2 | 1 | 2 | DEFER (real integration work, marginal value since mutation paths are already gated one layer up) |
| Repository Intelligence Dependency-Graph/Historical-Memory productization | 3 | 4 | 4 | 3 | 1 | 2 | 3 | DEFER (self-labeled prototype; needs a real consumer, not just docs) |
| Class-B verifier standalone CLI | 1 | 3 | 2 | 3 | 4 | 2 | 1 | HOLD — TRUST GAP |

## 8. Selected quick-release batch (2–4)

1. **Repository Intelligence exposure** (RKS + Query + Advisory-Context + Change-Impact) — EXPOSE/PACKAGE NOW.
2. **Runtime/plugin introspection exposure** (`pcae runtime inspect`/`snapshot`) — EXPOSE/PACKAGE NOW.
3. **Interactive Workflow / CHGR discoverability** — EXPOSE/PACKAGE NOW.
4. **`pcae authority inspect` documentation** — EXPOSE/PACKAGE NOW, bundled as a small addendum to (3)'s documentation pass rather than a standalone theme.

All four share the same profile: already built, already tested, already shipped in `v0.3.1`'s installed code, zero execution-capability change, zero new trust surface, and the only real remaining work is bounded verification of exact CLI syntax plus documentation/README/CHANGELOG exposure. This satisfies §26's preferred-candidate shape exactly ("already built + mostly verified + one missing integration edge + clear CLI/user workflow + no runtime-capability elevation").

### Rejected/deferred for this batch

- Permission Broker primitive-level closure — real code change, not documentation; already effectively released at the layer that matters (commit/push/promotion dispatch); DEFER.
- Repository Intelligence Dependency-Graph/Historical-Memory/Cross-Artifact/Unified-Query/Service — self-labeled prototypes needing a real external consumer to graduate past C/F; DEFER to a future integration-focused phase.
- Class-B verifier standalone exposure — low user value, non-trivial authority-adjacency risk, HOLD — TRUST GAP.
- HATP Trust-Enrollment/activation, CLTR authority cutover, backend execution activation — all hard-stopped by §38 (hardware provisioning, trust-root creation, authority cutover, execution activation). DEFER.

## 9. Release coherence and theme

**Recommended next-release theme:** *Make PCAE's existing read-only intelligence and governance-transparency layer — Repository Intelligence, runtime/plugin introspection, and the interactive human-governance workflow — visible and documented as supported product capabilities, with zero change to execution posture or authority state.*

This theme was derived from the candidates, not chosen first: all four selected items are read-only, already-shipped, already-tested CLI surfaces whose only defect is that they are undocumented or buried, and all reinforce PCAE's non-executing governance posture rather than expanding it.

## 10. Version recommendation

**v0.3.2.** The batch adds no new commands, no new behavior, and no new dependencies — it promotes existing, unchanged, already-installed capability into documented/supported status (README/QUICKSTART/COMMANDS/CHANGELOG updates, plus possibly removing internal "prototype" self-labels from the four selected surfaces' CLI help text in a bounded follow-up phase). This is release-hardening/documentation scope, consistent with the project's own precedent for patch-level bumps, not a `v0.4.0`-scale feature addition.

## 11. Minimum follow-up phase sequence

1. **3B — Verify + expose.** Confirm exact current CLI syntax/output for all four selected capabilities against the versions cited in this document (no drift since audit), then write the README/QUICKSTART/docs/COMMANDS.md/CHANGELOG documentation additions that surface them as supported workflows. Decide, within phase, whether removing "prototype" self-labels from CLI help text for the four selected surfaces is in scope (bounded doc-string-level change only, no behavior change) or deferred.
2. **3C — Release hardening / RC.** Full regression run, clean-install verification of the documented workflows from the built wheel/sdist, no source changes expected beyond what 3B produced.
3. **3D — Public v0.3.2 release.** Tag, GitHub Release, verification — following the same governed publication procedure used for v0.3.1.

No architecture, contract, or authority phase is recommended. The audit found no meaningful near-complete capability requiring new contracts to ship.

## 12. Runtime, article, and hard-stop confirmations

- Runtime: **Observed / observe / unavailable** — reconfirmed unchanged via `pcae runtime inspect` during this phase.
- Article: **STOPPED** — not read, not modified, not reassessed.
- `~/repos/pcae-deepseek-research`: not inspected.
- No production source, CLI, contract, schema, or packaging-configuration file was modified in this phase.
- No PyPI publication, tag, or GitHub Release action occurred.
- No hardware provisioning, credential creation, trust-root creation, or authority cutover occurred or was proposed for action.

## 13. Governance results (this phase)

- `pcae health`: healthy
- `pcae check`: passed
- `pcae status coherence`: coherent
- `pcae doctor task-memory`: warnings (129 pre-existing, unrelated, unchanged)
- `pcae push check`: nothing_to_push (pre-finalization baseline; re-verified at close per governed procedure)
- `pcae runtime inspect`: unchanged (`Observed`/`observe`/`unavailable`)
- Telegram: configured, ready
- Tests run this phase: none new; existing-test evidence was gathered via targeted `grep`/live CLI invocation rather than a broad suite run, per §34's focused-verification instruction. Live, side-effect-free CLI invocations exercised during evidence-gathering: `pcae repository-intelligence {snapshot generate, query, dependency-graph generate, historical-memory generate}`, `pcae advisory {status, context build, check}`, `pcae runtime {inspect, snapshot}`, `pcae hatp --help`, `pcae rollback --help`, `pcae decision-session --help`, `pcae governance-record --help`, `pcae authority --help`, `pcae notify status`, `pcae backend execution-boundary proof --json`, `pcae agents adapters --json`, `pcae backend list --json`.

## 14. Summary

```
CAPABILITY AUDIT:
COMPLETE
HIGH-VALUE NEAR-COMPLETE CAPABILITIES:
Repository Intelligence (RKS/Query/Advisory-Context/Change-Impact),
Runtime/Plugin Introspection, Interactive Workflow/CHGR,
pcae authority inspect (bundled)
PRIMARY GAP TYPE:
Documentation / product-surface exposure (not integration, not
verification, not packaging)
AUTHORITY-RISK PROFILE:
LOW / BOUNDED
RECOMMENDED NEXT-RELEASE THEME:
Expose PCAE's existing read-only intelligence and governance-
transparency layer as a documented, supported product capability
RECOMMENDED VERSION:
v0.3.2
MINIMUM REMAINING PHASES:
3B (verify + expose) -> 3C (release hardening/RC) -> 3D (public release)
RUNTIME:
Observed / observe / unavailable
ARTICLE:
STOPPED
```
