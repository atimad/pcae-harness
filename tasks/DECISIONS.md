# Decisions

## Accepted

- Treat Phase 119E as artifact-contract-freeze-only: freeze the initial
  Repository Intelligence artifact contract for all twelve conceptual
  schema families defined in 119C and reviewed in 119D, incorporating the
  six minor clarifications identified by 119D (canonical field names with
  required/optional/conditional classification, embedded-vs-referenced
  cross-cutting convention, package materialization order, Contract
  Conformance Record non-decision wording, source locator vocabulary, and
  artifact reference vocabulary). Freeze the common artifact envelope,
  per-family contracts, mandatory invariants, source attribution contract,
  evidence link contract, uncertainty/verification contract,
  conflict/supersession contract, derivation disclosure contract,
  versioning/snapshot contract, forbidden claims, conformance model,
  compatibility matrix, and future constraints. Do not create executable
  schemas, JSON Schema, Pydantic models, dataclasses, validators, contract
  verifiers, CLIs, automated tests, Repository Intelligence extraction,
  Repository Knowledge extraction, Historical Memory extraction, Change
  Impact Analysis engines, Dependency Knowledge Graph construction, graph
  query engines, Advisory behavior changes, Advisory Runtime changes,
  Advisory Context Package changes, Evidence subsystem changes, Repository
  Skills changes, Decision Evaluation changes, source code, tests, runtime
  behavior, execution, authorization, enforcement, lifecycle behavior,
  Permission Broker behavior, Repository State behavior, Repository
  Transition Validator behavior, Notification Policy behavior, REST,
  Dashboard, Web UI, provider orchestration, autonomous coding, model
  capability expansion, automatic patch generation, automatic
  refactoring, repository mutation, or Telegram inbound capability.
- Treat Phase 119D as conceptual-schema-review-only: review the 119C
  conceptual schema architecture against the 119A contract and 119B
  verification expectations, assess coherence, completeness,
  boundaries, implementation leakage, and artifact-contract-freeze
  readiness, and recommend whether to proceed to artifact contract
  freeze. Do not freeze artifact contracts, create executable schemas,
  JSON Schema, Pydantic models, dataclasses, validators, contract
  verifiers, CLIs, automated tests, extraction, graph construction,
  impact analysis, Advisory behavior changes, runtime behavior changes,
  source/test changes, execution, enforcement, lifecycle redesign,
  Permission Broker changes, repository mutation, provider
  orchestration, autonomous coding, automatic patch generation,
  automatic refactoring, or Telegram inbound capability.
- Treat Phase 119C as conceptual-schema-architecture-only: define
  implementation-independent conceptual artifact families for future
  Repository Intelligence work, including common envelope, knowledge,
  historical, graph, impact, advisory context, source attribution,
  evidence link, uncertainty/verification, conflict/supersession, query
  result, and conformance record shapes. 119C may include
  non-normative conceptual examples but must not implement executable
  schemas, JSON Schema, Pydantic models, dataclasses, validators,
  contract verifiers, CLIs, automated tests, extraction, graph
  construction, impact analysis, Advisory behavior changes, runtime
  behavior changes, source/test changes, execution, enforcement,
  lifecycle redesign, Permission Broker changes, repository mutation,
  provider orchestration, autonomous coding, automatic patch generation,
  automatic refactoring, or Telegram inbound capability.
- Treat Phase 119B as a contract-verification-documentation-only phase:
  verify that the frozen Repository Intelligence contract from 119A is
  internally consistent, testable, future-enforceable, and ready to
  constrain conceptual schema architecture / prototype planning. 119B
  may define conceptual verification checks, invariant matrices,
  non-conformance examples, contract-preserving examples, and a future
  conformance checklist. It must not implement a verifier, CLI,
  automated tests, Repository Intelligence extraction, Repository
  Knowledge extraction, Historical Memory extraction, Change Impact
  Analysis engine, Dependency Knowledge Graph construction, graph query
  engine, Advisory behavior changes, Evidence subsystem changes,
  Repository Skills changes, Decision Evaluation changes, runtime
  behavior changes, source code changes, test code changes, execution,
  shell mediation, Permission Broker changes, lifecycle redesign,
  repository mutation, provider orchestration, autonomous coding,
  automatic patch generation, automatic refactoring, or Telegram inbound
  capability.
- Treat Phase 119A as the contract-freeze-only phase for Track B
  Repository Intelligence: freeze the initial Repository Intelligence
  contract derived from 118A through 118R, including purpose, scope,
  component boundaries, shared primitive families, source attribution,
  determinism, uncertainty/conflict/supersession, versioning/snapshot,
  verification, conceptual query/report expectations, read-only
  boundary, Advisory non-authority, Decision Evaluation boundary,
  execution boundary, contract invariants, compatibility matrix, future
  phase constraints, and the minor clarifications identified by 118R.
  Do not implement extraction, graph construction, impact analysis,
  advisory behavior, schemas as executable models, runtime behavior,
  source changes, test changes, execution, enforcement, lifecycle
  redesign, Permission Broker changes, provider orchestration,
  autonomous coding, automatic patch generation, automatic refactoring,
  repository mutation, or Telegram inbound capability in 119A.
- Treat Phase 118R as the architecture-review-only closure of the
  initial Track B architecture set: 118A through 118E form one coherent
  Repository Intelligence architecture, with Repository Knowledge as the
  foundation, Historical Memory as temporal layer, Dependency Knowledge
  Graph as relationship layer, Change Impact Analysis as read-only
  change-scoped reasoning, and Advisory Reasoning Expansion as a
  non-authoritative consumer. The architecture is ready for contract
  freeze with minor clarifications around shared primitive names, source
  references, evidence links, uncertainty states, snapshot identity,
  dependency-vs-impact relationship views, and Advisory Context Package
  integration. Do not introduce implementation, extraction, graph
  construction, advisory behavior changes, contract freeze, execution,
  lifecycle redesign, or authority changes in 118R.
- Treat Phase 118E as the architecture-only Advisory Reasoning
  Expansion phase for Track B Repository Intelligence: expanded
  Advisory may consume Repository Knowledge, Historical Memory, Change
  Impact Analysis, Dependency Knowledge Graph context, Evidence,
  Repository Skills, Advisory Repository Skills, Advisory Context
  Packages, and canonical lifecycle artifacts to produce better
  explanations, recommendations, uncertainty statements, evidence-gap
  summaries, reasoning traces, and handoff context. Advisory may become
  more informed but must not become more powerful. It must not decide,
  authorize, execute, enforce, broker permissions, mutate lifecycle or
  repository state, orchestrate providers, implement advisory behavior,
  change Advisory Context Packages, implement a reasoning engine, build
  graphs, run impact analysis, extract Repository Knowledge or
  Historical Memory, generate patches, refactor automatically, or bypass
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118D as the architecture-only Dependency Knowledge Graph
  phase for Track B Repository Intelligence: the Dependency Knowledge
  Graph is a deterministic, source-attributed, inspectable, versioned,
  read-only relationship layer inside Repository Knowledge that
  represents repository entities as graph nodes, repository-derived
  relationships as typed directional edges, and dependency assertions as
  source-backed claims. It may support Change Impact Analysis,
  Historical Memory, architectural contract mapping, Advisory context,
  repository intelligence reports, subsystem lineage inspection, and
  traceability. It must not become graph construction, a graph database,
  a graph CLI, a graph query engine, graph visualization, runtime
  orchestration, execution planning, command routing, permission
  brokering, enforcement, autonomous planning, lifecycle mutation,
  repository mutation, hidden model inference, test execution,
  automatic patch generation, automatic refactoring, or a bypass around
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118C as the architecture-only Change Impact Analysis
  phase for Track B Repository Intelligence: Change Impact Analysis is
  deterministic, source-attributed, inspectable reasoning over
  Repository Knowledge and Historical Memory to identify what may be
  affected by a proposed or observed repository change. It may define
  impact subjects, entities, surfaces, relationships, paths, claims,
  sources, evidence links, scope, blast radius, queries, and reports;
  may produce evidence candidates; and may strengthen Advisory through
  bounded impact context. It must not become model prediction,
  autonomous planning, a decision maker, an enforcement layer, a
  Permission Broker, a lifecycle authority, an execution mechanism, a
  repository mutator, a dependency graph implementation, an impact
  extraction engine, an impact database, an impact CLI, a test runner,
  automatic patch generation, automatic refactoring, or a bypass around
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118B as the architecture-only Historical Memory phase for
  Track B Repository Intelligence: Historical Memory is a deterministic,
  source-attributed, inspectable, versioned, read-only temporal layer
  inside Repository Knowledge that describes how repository
  architecture, capabilities, contracts, decisions, repairs, hardening,
  releases, and subsystems evolved over time. It may expose historical
  subjects, events, claims, sources, lineage, snapshots, query results,
  and evidence links; may produce evidence candidates; and may
  strengthen Advisory through bounded historical context. It must not
  become generic model/conversation memory, decide, authorize, execute,
  enforce, mutate repository state, rewrite history, promote artifacts,
  send notifications, replace governance, or bypass Decision Evaluation
  / the Repository Transition Validator.
- Treat Phase 118A as the architecture-only start of Track B
  Repository Intelligence: define Repository Knowledge as a deterministic,
  read-only, source-attributed architectural understanding layer that is
  distinct from Repository State, Evidence, Advisory Context, Repository
  Skills, and Decision Evaluation. Repository Knowledge may describe
  entities, relationships, claims, sources, snapshots, and evidence links;
  may produce evidence candidates; and may strengthen Advisory through
  bounded context selection. It must not decide, authorize, execute,
  enforce, mutate repository state, promote artifacts, send notifications,
  replace governance, or bypass Decision Evaluation / the Repository
  Transition Validator.
- Treat Phase 117E.1 as an additive corrective governance phase, not a
  history rewrite: 117E remains part of the audit trail as release
  preparation / release-attempt history, while 117E.1 verifies the real
  external publication state and publishes only the missing v0.2.0 Git
  tag and GitHub Release. Do not amend or delete historical 117E
  records. No feature, runtime behavior, architecture, execution,
  lifecycle behavior, production source, or test behavior change is
  authorized by this repair.
- Treat Phase 117E as release-only: publish the official `v0.2.0` Git
  tag and GitHub Release using the 117D release notes, update release
  metadata/status, and do not add features, change runtime behavior,
  change architecture, implement execution, modify lifecycle behavior,
  publish to PyPI, or publish packages. Package metadata may be updated
  to `0.2.0` as release metadata; this is not runtime behavior.
- Treat Phase 117D as release preparation only. Draft v0.2.0 release
  notes and refresh release-facing README/install/demo messaging to
  match the frozen v0.2 posture, but do not publish a release, create a
  tag, push a GitHub Release, publish packages, add features, change
  runtime behavior, implement execution, change architecture, or change
  lifecycle behavior. The release message must state that PCAE is
  non-executing by design, runtime state is `Observed`, execution is
  unavailable, advisory evidence does not authorize action, and PCAE is
  not an autonomous coding agent.
- Treat Phase 117C as verification-only with a narrow test-repair
  exception for proven 117B baseline regressions: real-repository
  TODO/bootstrap checks must derive the expected current recommendation
  from authoritative `PROJECT_STATUS.md` rather than hard-code a phase
  id, and 88M preflight decision assertions must use a stable fixture
  task contract rather than the real repository's active task scope. No
  production source, runtime behavior, architecture, lifecycle behavior,
  or release-preparation change is authorized by this verification.
- Treat Phase 117B as test-maintenance only: update stale/legacy test
  expectations documented by 116C/116D to match frozen v0.2 behavior
  without changing production source or weakening safety coverage.
  `PROJECT_STATUS.md` remains authoritative over `tasks/TODO.md`; real
  TODO/bootstrap tests should derive the current recommended phase from
  that source instead of hard-coding a historical phase id. Incomplete
  task-finish report promotion is expected to be quarantined by the
  Repository Transition Validator with notification dispatch skipped.
  The 88M preflight standalone issue remains classified as a
  real-repository fixture-state concern unless it reproduces with an
  active task and proves a product defect.
- Treat Phase 116C as verification-only: Phase 116B introduced no
  runtime/source regression because it changed no `src/` or `tests/`
  files. Six full-suite failures are pre-existing stale expectations.
  One full-suite failure is an intentional changed expectation caused by
  116B's roadmap scratch correction from stale 113Y-era wording to the
  116A/116B/116C v0.2 architecture-freeze track. No 116B
  architecture/runtime repair is required; stale tests may be addressed
  by a future focused test-maintenance phase before freeze if desired.
- Treat Phase 116B as documentation-only v0.2 architecture consolidation:
  structural invariants are the long-term authority for phase identity,
  metadata consistency, report completeness, recommended-next-phase
  presence, canonical promotion eligibility, notification eligibility,
  and execution-unavailability checks; the legacy finalization gate
  remains a v0.2 compatibility/trust gate until its unique
  governance-key and test-result-key checks migrate into first-class
  invariants; shared `RepositoryState` construction is the required
  future implementation shape owned by the Repository Transition
  Validator/integration layer; and Repository Event is frozen as
  policy/taxonomy only for v0.2, not a runtime type, event bus, emitter,
  or consumer subscription API. No runtime behavior, lifecycle behavior,
  execution, authorization, Permission Broker behavior, Repository
  Skill, Advisory Provider, Evidence Provider, Decision Evaluation
  behavior, Repository Transition Validator behavior, Notification
  Policy behavior, Telegram inbound, REST, Dashboard, Web UI, event bus,
  or model integration is authorized by this phase.
- Treat Phase 116A as a review-only v0.2 architecture assessment:
  the architecture is internally coherent and does not require
  significant redesign, but it should be classified as requiring minor
  consolidation before freeze because phase-identity/finalization
  checks overlap, report-completeness/recommended-next-phase
  enforcement is duplicated, `RepositoryState` is constructed at two
  equivalent call sites, and Repository Event remains policy vocabulary
  rather than a runtime type. No runtime capability, execution,
  authorization, Permission Broker change, Repository Skill, Advisory
  Provider, Evidence Provider, Decision Evaluation change, Repository
  Transition Validator change, lifecycle command change, Notification
  Policy change, Telegram inbound, REST, Dashboard, Web UI, or model
  integration is authorized by this review.
- Treat Phase 115B as an architecture-only Evidence contract freeze:
  Evidence is evaluation-scoped, referenceable by explanations, and
  contractually structured, but it does not decide, mutate repository
  state, become a kernel primitive, persist by default, authorize
  canonical mutation, or give Evidence Providers any authority beyond
  producing labelled evidence for centralized evaluation.
- Treat Phase 115A as an architecture-only explainability framework
  phase: Repository Decision remains a centralized computation over
  repository state, proposed transition, evidence, and invariants;
  Evidence becomes a first-class architectural concept but not a kernel
  primitive; Repository Skills are future evidence-only providers that
  never decide, vote, mutate state, authorize transitions, promote
  artifacts, send notifications, bypass the validator, invoke runtime
  execution, or depend on model identity.
- Treat Phase 114A as phase-report promotion hardening only: introduce a
  reusable canonical artifact promotion state machine, route phase-report
  `latest.*` writes through Certified -> Canonical promotion, and keep
  rejected/quarantined artifacts terminal and non-canonical while leaving
  notification enforcement, push check, Runtime Snapshot, Runtime Inspect,
  Permission Broker, REST, Telegram inbound, and execution out of scope.
- Treat Phase 113Z as the second Repository State Kernel enforcement phase:
  `pcae task finish --commit` may finish and commit the governed task closure,
  but canonical phase-report promotion now requires Repository Transition
  Validator acceptance through the same shared phase-report transition adapter
  used by `pcae phase complete`. Partial report evidence quarantines instead
  of writing `latest.*`; notification and push-check commands remain out of
  scope.
- Treat Phase 113Y as the first Repository State Kernel enforcement phase:
  `pcae phase complete` must request a transition from the Repository
  Transition Validator before canonical `latest.*` promotion, while task
  finish, push/check, notification enforcement, Runtime Snapshot, Runtime
  Inspect, Advisory Runtime, Permission Broker, REST, and execution remain out
  of scope.
- Treat Phase 113X as a contract-freeze phase for future Repository Transition
  Validator lifecycle integration: commands remain transition-request front
  ends, the validator is the only certification authority, the Model
  Containment Layer is model-agnostic, and no lifecycle behavior changes until
  later implementation phases.
- Treat Phase 113W as a design-only Repository Transition Validator integration phase: the human phase prompt supersedes the generated transition contract's overly narrow default scope, so 113W may edit integration design docs, documentation-completeness tests, and project memory, while continuing to forbid source behavior changes, lifecycle behavior changes, and raw git operations.
- Treat the Phase 88L task-state mismatch as legacy contract-format reconciliation, not a transition-engine defect: checkbox-based `## Status` content is visible to directory-based health reporting but is not the literal `active` status required by `pcae task transition`; close the completed legacy contract with `pcae task close`, create a separate structured 88L.1 reconciliation contract, and do not create or start 88M until reconciliation is complete.
- Treat Phase 69C agent approval as artifact-authoritative and strict: `gep-gate-006` must use `ApprovedPromptArtifact.approved_agents` as the only authoritative approval source; legacy 69B artifacts without `approved_agents` block with `reason=approved_agents_missing`; approval must not be inferred from runtime registration, installation status, contract presence, prompt approval alone, or recommended runtime.
- Treat Phase 69C as validation-only activation hardening: scope is limited to approved-agent validation (gep-gate-006), invocation-contract availability (gep-gate-007), codex-local contract verification, claude-local contract verification, and runtime contract registry consistency; execution_allowed remains False and no runtime invocation, prompt execution, or execution authorization is introduced.
- Treat IRG Challenge as awareness-only, not authority: it identifies assumptions, blind spots, inconsistencies, counterfactuals, and uncertainty that deserve human attention; it does not recommend approval or rejection, prescribe implementation, emit change lists, alter command outcomes, or create governance gates; automatic surfacing is limited to session bootstrap, phase handoff, and phase completion/control review; full detail is available only through `pcae irg-challenge` and `--json`; no persistence, acknowledgement, override, remediation, or workflow coupling is introduced by default.
- Treat strategic lineage supersession as reference-derived, not status-mutating: historical approved lineage records remain immutable append-only activation evidence even after branch current_phase advances; supersession is inferred from later `supersedes_lineage_id` references, and branch current_phase matching is enforced only for the current non-superseded active lineage record.
- Treat Phase 65J strategic continuity as governed decision lineage, not generic memory: `.pcae/strategic-lineage.json` is append-only authority only for human strategic decisions and rationale; roadmap state remains owned by `_CRI_KNOWN_PHASES`, activation evidence remains owned by provenance, and review findings remain owned by `_IRG_STRATEGIC_REVIEW_REGISTRY`; bootstrap and handoff summaries are derived and bounded; implementation approval does not imply activation approval, commit approval, or push approval; no command may create decisions, infer rationale, approve, activate phases, execute prompts, invoke runtimes, or authorize writes.
- Treat Phase Activation Governance as unresolved roadmap debt exposed by 65J: future governance must represent implementation approval, activation approval, commit approval, and push approval as separate human decisions; until that capability exists, phase activation requires explicit human language and must never be inferred from implementation approval.
- Treat Phase 65I strategic registry coherence as a severity-partitioned validation layer: authoritative registry contradictions (branch current_phase drift, invalid active-phase cardinality, unexplained CRI/CI divergence) are blocking defects that fail `pcae check`, while generated-doc drift remains non-mutating advisory drift surfaced by `pcae status coherence` and warning-only in `pcae check`/`pcae health`.
- Treat Phase 64F Orchestration Readiness Gate as a read-only future-dispatch eligibility layer over 64C orchestration entries, 64D coordination policy entries, and 64E audit records: it evaluates approval/audit/recovery/quarantine readiness and emits governed gate records and signals, but must not authorize execution, duplicate 64B generic readiness, or replace 64E audit structure.
- Treat the 64F phase transition as roadmap and prompt-governance advancement only: mark 64E completed, make 64F the active multi_runtime phase, move 65A behind 64F, and register 64F prompt profiles without introducing new runtime behavior before 64F implementation begins.
- Treat Phase 64E Orchestration Audit Model as a read-only governance layer over 64C orchestration entries and 64D coordination policy entries: it defines audit records, traceability checks, and review readiness, but must not duplicate dispatch logic, policy logic, or authorize execution.
- Treat capability projection as shared infrastructure: capability inventory and capability/roadmap intelligence must materialize their public capability records through one projection helper so IDs, fields, and command/report outputs stay stable while projection logic cannot drift independently.
- Treat Phase 64B.4A skill registry hardening as consolidation work, not a new parallel subsystem: skill discovery, metadata parsing, and registry alignment should reuse the shared intelligence infrastructure that already supports capability, roadmap, and prompt governance.
- Treat Phase 64B.4 skills as first-class governed packages stored under `.pcae/skills`: a skill is metadata plus reusable instructions/workflow references, not merely a rendered prompt, and skill invocation remains read-only with no runtime, orchestration, or write execution.
- Treat Phase 64B.3 prompt recommendations as registry-backed governance artifacts: `pcae prompt next`, `pcae prompt phase`, and `pcae prompt validate` must source phase alignment from the roadmap registry, capability alignment from the capability registry, block historical/completed/superseded/track-mismatch prompt recommendations, and remain read-only with no runtime or orchestration execution.
- Phase 62A (Controlled Runtime Execution Pilot) is the first PCAE phase where execution_allowed=True. Execution is conditionally permitted only when: runtime is shell-local, command is on the allowlist (pwd, ls, ls -la, git status, python --version, python3 --version), command is not on the denylist, no write or network operations are involved, the 30s timeout is enforced, the 100 KB output limit is enforced, and human_review_required=True. All other governance restrictions (no write execution, no network, no AI runtime invocation, no commit/push/rollback) remain in force.
- Use Python and `pathlib` for cross-platform filesystem behavior.
- Use Markdown files as the only persistence mechanism for the MVP.
- Defer databases, LLM calls, and vector search.
- Keep commands modular under `src/pcae/commands`.
- Keep `pcae inspect` read-only; reserve enforcement and repair behavior for future commands.
- Treat unvalidated sandbox isolation boundaries as advisory hardening signals that keep execution blocked; Phase 52G may recommend human-reviewed remediation but cannot apply remediation or authorize runtime execution.
- Treat Phase 52M conflict resolution as read-only classification and escalation: preserve conflicting evidence, recommend human-reviewed resolution paths, and keep automatic resolution and execution disabled.
- Keep Phase 61B runtime discovery strictly assessment-only: define discovery readiness requirements and report blockers, but do not probe the host, invoke runtimes, register runtimes, or authorize execution.
- Keep Phase 61C runtime capability inventory strictly assessment-only: classify capability status and trust level from governance inputs, but do not discover hosts, register runtimes, invoke runtimes, or authorize execution.
- Keep Phase 61D runtime trust modeling strictly assessment-only: classify trust signals and prerequisites from governance inputs, but do not assign trust automatically, discover hosts, register runtimes, invoke runtimes, or authorize execution.
- Keep Phase 61E task lifecycle governance strictly assessment-only: inspect active/done task, roadmap, and session alignment, recommend remediation when needed, but do not move tasks, rewrite session state, or mutate repository state automatically.
- Keep Phase 61F agent handoff modernization strictly assessment-only: inspect continuity requirements, summarize roadmap/runtime/governance posture, and recommend modernization when needed, but do not rewrite handoff artifacts, rewrite session state, or mutate repository state automatically.
- Keep Phase 61G roadmap continuity strictly assessment-only: validate roadmap/task/session/runtime/handoff alignment before runtime work, but do not rewrite roadmap files, rewrite session state, or mutate repository state automatically.
- Keep Phase 61H automated task transition limited to governance lifecycle automation: complete the current task, create the next task, refresh session continuity, update governance memory files, and validate coherence/health/check state, but do not invoke runtimes, execute prompts, authorize execution, commit, push, rollback, or change unrelated source behavior.
# Decisions

- Accepted: Treat Phase 117D as release preparation only. Draft v0.2.0
  release notes and refresh release-facing README/install/demo
  messaging to match the frozen v0.2 posture, but do not publish a
  release, create a tag, push a GitHub Release, publish packages, add
  features, change runtime behavior, implement execution, change
  architecture, or change lifecycle behavior. The release message must
  state that PCAE is non-executing by design, runtime state is
  `Observed`, execution is unavailable, advisory evidence does not
  authorize action, and PCAE is not an autonomous coding agent.
