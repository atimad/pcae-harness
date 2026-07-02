# PCAE — Policy Controlled Autonomous Execution

PCAE is a governance harness for AI-assisted software engineering. It does not make AI agents trustworthy by assumption — it makes their work governable by requiring evidence at every step and refusing to proceed when that evidence is missing.

PCAE is a work-in-progress engineering experiment. It is **not production ready**. It does not claim to solve autonomous coding. The goal is governed autonomy — giving AI agents increasing capability while maintaining auditability, scope discipline, and human authority at every boundary.

**Status:** `v0.1.0-rc1` tagged and pushed — a governed, **non-executing** AI coding lifecycle harness. 12,900+ tests passing (fast-green gate: 4390/4390 fully green). Governed lifecycle tooling, read-only project intelligence, dry-run action gate evaluation, and broker/shell-gate architecture documented. Enforced preflight gates and live broker/shell-gate mediation are not yet implemented — v0.1 does not execute code, invoke a real AI backend, or mediate a shell on an agent's behalf. See [docs/RELEASE_SCOPE_V0_1.md](docs/RELEASE_SCOPE_V0_1.md) for the frozen v0.1 scope, [docs/V0_1_GOLDEN_WORKFLOW.md](docs/V0_1_GOLDEN_WORKFLOW.md) for the supported operator workflow, and [docs/RELEASE_HANDOFF_V0_1_RC1.md](docs/RELEASE_HANDOFF_V0_1_RC1.md) for the release-candidate handoff. Governed autonomy (real backend invocation, runtime enforcement) is the **v0.2** target — not yet implemented.

| Resource | Link |
|----------|------|
| **v0.1 Release Scope** | [docs/RELEASE_SCOPE_V0_1.md](docs/RELEASE_SCOPE_V0_1.md) |
| **v0.1 Golden Workflow** | [docs/V0_1_GOLDEN_WORKFLOW.md](docs/V0_1_GOLDEN_WORKFLOW.md) |
| **v0.1 Release Handoff** | [docs/RELEASE_HANDOFF_V0_1_RC1.md](docs/RELEASE_HANDOFF_V0_1_RC1.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Installation | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| Demo Script | [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) |
| Lifecycle Diagrams | [docs/GOVERNANCE_LIFECYCLE_DIAGRAM.md](docs/GOVERNANCE_LIFECYCLE_DIAGRAM.md) |
| Vision | [VISION.md](VISION.md) |
| Governance Handbook | [docs/governance/GOVERNANCE_HANDBOOK.md](docs/governance/GOVERNANCE_HANDBOOK.md) |
| White Paper | [docs/whitepaper/PCAE_WHITEPAPER.md](docs/whitepaper/PCAE_WHITEPAPER.md) |

### Architecture Diagrams

| Diagram | Description |
|---------|-------------|
| [Governance Stack](docs/architecture/01-governance-stack.md) | The seven governance domains and their relationships |
| [Execution Lifecycle](docs/architecture/02-execution-lifecycle.md) | The 8-step gate chain every invocation must traverse |
| [Prompt Governance](docs/architecture/03-prompt-governance.md) | How prompts are generated, validated, and approved |
| [Runtime Governance](docs/architecture/04-runtime-governance.md) | How runtimes are evaluated for trust and contract compliance |
| [Future Autonomous Flow](docs/architecture/05-future-autonomous-flow.md) | The target autonomous engineering loop (future state) |

## Why PCAE Exists

AI coding agents can produce real changes to real repositories — commits, pushes, file modifications — without approval gates, audit trails, or rollback plans. A single unconstrained agent invocation can leave a codebase in an inconsistent state with no clear path back.

PCAE was built to address this directly:

- **Uncontrolled execution risk.** Agents that run without authorization checks can make destructive changes before any human has reviewed the plan.
- **Missing approval gates.** No mechanism prevents an agent from committing or pushing without explicit human sign-off.
- **Missing audit trails.** Without structured records linking requests, authorization, execution, and results, there is no basis for reviewing what happened or why.
- **Missing rollback governance.** Rollback strategies must be declared before execution, not improvised after.
- **Unverified runtime trust.** Not every AI runtime is equally trustworthy or sandboxed. Runtime contract enforcement must be evaluated before invocation.
- **Human authority.** Humans must remain the authoritative decision-makers for every execution, approval, and rollback action.

## Core Principles

- **Human approval remains authoritative.** No execution, promotion, or rollback proceeds without explicit human sign-off recorded in an artifact.
- **Read-only before write.** Invocation starts with read-only pilots; write execution requires a separately governed gate (`pcae promote`), and reversal requires its own (`pcae rollback`).
- **Evidence before execution.** Authorization, preflight, audit, capture, and review records must exist before any invocation or write is eligible.
- **Audit everything.** Every invocation attempt produces a structured audit trail regardless of outcome.
- **Rollback must be planned.** Rollback evidence (before-content and hashes) is captured at promotion time, not improvised after the fact.
- **Runtime trust must be verified.** Runtime contract enforcement is evaluated independently for each runtime target.
- **No automatic commit, push, or rollback.** These operations require human confirmation and are never triggered automatically by agents.

## Artifact Lifecycle

PCAE's execution governance is a chain of structured, append-only artifacts. Each one gates the next; only two commands in PCAE's entire history mutate the root repository, and both require prior human-reviewed evidence.

```
APA → ARA → EAR → ESA → ERR/ECR → ECP → EPR → PER → RER
```

| Artifact | Name | Role |
|---|---|---|
| **APA** | Approved Prompt Artifact | A human approves a specific prompt + agent pair before any invocation is considered. |
| **ARA** | Authorization Record | The approved, contract-validated invocation is explicitly authorized to proceed. |
| **EAR** | Execution Audit Record | An append-only audit entry is created for every invocation attempt, regardless of outcome. |
| **ESA** | Execution Snapshot Artifact | Git working-tree state is captured before and after the attempt. |
| **ERR** | Execution Result Record | The structured outcome of the invocation, classified by technical status and governance attention. |
| **ECR** | Execution Change Record | The file-level changes detected between two ESAs (paths, not content). |
| **ECP** | Execution Change Package | Full evidentiary capture of sandbox content — diffs, before/after content, SHA-256 hashes — taken just before the sandbox is destroyed. |
| **EPR** | Execution Promotion Review | A human's explicit content-level review of an ECP, with partial-path approval and a separate `promotion_authorized` flag. |
| **PER** | Promotion Execution Record | `pcae promote` writes reviewed content to root, gated on `EPR.promotion_authorized=True`. The first artifact where root mutation actually occurs. |
| **RER** | Rollback Execution Record | `pcae rollback` reverses a PER's writes using the originating ECP's before-content and hashes. The first artifact whose subject is reversing a root mutation. |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#artifact-model) for full field-level detail, store locations, and the execution/promotion/rollback lifecycles built on top of this chain.

## Architecture Overview

PCAE governs AI-assisted engineering across seven domains:

| Domain | Responsibility |
|---|---|
| **Change governance** | Controls what files agents may modify and under what task contract |
| **Rollback governance** | Validates and enforces rollback plans before write execution |
| **Prompt governance** | Generates, renders, and validates prompts before they are submitted |
| **Execution governance** | Authorizes, preflight-checks, and enforces contracts for each invocation |
| **Runtime governance** | Assesses runtime trust, contract compliance, and sandbox conditions |
| **Multi-agent governance** | Orchestrates agent selection, capability matching, and handoff sequencing |
| **Audit and evidence** | Links requests, authorization, audit records, captures, reviews, and evidence into a complete invocation chain |

Each domain produces structured, machine-readable artifacts that gate the next step. No step executes without its upstream gate passing.

The implementation is organized into the following architecture layers:

| Layer | Phases | Description |
|---|---|---|
| **Governance Layer** | 1–49 | Task contracts, policy checks, orchestration, session continuity |
| **Execution Layer** | 50A–51K | Write authorization and execution orchestration chains |
| **Recovery Layer** | 52A–52E | Task, session, governance, lock, and corruption recovery planning |
| **Runtime Hardening Layer** | 52F–52I | Contract hardening, sandbox isolation, timeout governance, output integrity |
| **Concurrency Layer** | 52J–52M | Concurrency safety, parallel coordination, state consistency, conflict resolution |
| **Resilience Layer** | 52N–52Q | Chaos testing, failure injection planning, corruption simulation, recovery validation |
| **Runtime Governance Layer** | 55A–64H | Runtime registry, trust modeling, multi-runtime selection, arbitration, audit, and orchestration |
| **Capability Intelligence Layer** | 64B Series | Capability inventory, roadmap/prompt/skill intelligence and recommendation hardening |
| **Strategic Governance Layer** | 65A–68D | Strategic decision lineage, independent review governance, IRG challenge |
| **Execution Governance Activation Layer** | 69A–69O | Approval, authorization, audit, activation, sandboxing, change capture, governed promotion, and governed rollback |

## Current Capabilities

### Task and Policy Governance
- **Task contracts** constrain which files an agent may touch, which operations are forbidden, and what the session goal is.
- **Policy checks** (`pcae check`) validate that every source change is accompanied by documentation updates and that architecture zone rules are respected.
- **Session continuity** verifies that the active task matches the current working state on every check.

### Prompt, Skill, and Capability Intelligence
- **Capability and roadmap intelligence** (`pcae capability list/show/dependencies`, `pcae roadmap current/tracks/evolution`) reports the authoritative capability and phase registries.
- **Prompt recommendation** (`pcae prompt next/phase/validate`) recommends governed prompts sourced from the roadmap and capability registries.
- **Skill system** (`pcae skill list/show/validate/invoke`) treats skills as first-class governed packages under `.pcae/skills`.

### Strategic Governance and Independent Review
- **Strategic decision lineage** (`pcae strategic-continuity show/history/validate`) is an append-only record of human strategic decisions and rationale, distinct from roadmap state and activation evidence.
- **Independent Review Governance (IRG) Challenge** (`pcae irg-challenge`) surfaces assumptions, blind spots, and uncertainty about strategic decisions for human attention — advisory only, never gating a command's outcome.
- **Write invocation approval gateway** (`pcae write-invocation-approval-gateway`) and **mapping review governance** (`pcae mapping-review-governance`) govern strategic-to-objective mapping decisions.

### Execution Governance Activation (BR-005, Phases 69A–69O)
- **Approval and authorization** (`pcae approval-store`, `pcae authorization-store`, `pcae invocation-contract-validation`, `pcae execution-pathway-integration`) record human approval and authorization before any invocation.
- **Audit and activation** (`pcae audit-record`, `pcae execution-activation`) create an append-only audit record and run the invocation inside an isolated sandbox (`git worktree` + `rsync` overlay).
- **Result governance and review** (`pcae execution-result-governance`, `pcae result-review`) classify outcomes and record human disposition.
- **Change capture and promotion review** (`pcae execution-change-package`, `pcae promotion-review`) capture full evidentiary content from the sandbox and record a human's promotion decision.
- **Governed promotion** (`pcae promote`) and **governed rollback** (`pcae rollback`) are the only two commands in PCAE's history that mutate the root repository — both gated on prior human-reviewed evidence, both idempotent, both refusing to proceed on divergence.

### Change and Rollback Governance (Design Scaffolds)
- **Controlled modification design** models the full lifecycle of a governed write: pre-modification snapshot, targeted change, verification, and rollback trigger.
- **Controlled commit, push, and rollback governance** produces structured scaffolds defining the approval and rollback plan before any mutation occurs.

### Runtime Governance
- **Runtime trust assessment** (`pcae runtime-trust`) evaluates each configured runtime for trust level, sandbox compliance, and contract verification.
- **Multi-runtime registry, selection, arbitration, and audit** (Phases 63A–63F) govern selection among multiple registered runtimes with full audit chain and quarantine on failure.
- **Orchestration readiness gate** (Phase 64F) evaluates approval/audit/recovery/quarantine readiness without authorizing execution.

### Controlled Write Governance (50A–50K) and Execution Orchestration (51A–51K)
- Full 10/11-step advisory chains (authorization, review, decision, lifecycle, planning, readiness, evidence, audit, rollback verification, governance audit, recommendation) that predate and inform the 69-series activation chain above. All commands remain advisory and read-only.

### Recovery, Hardening, Concurrency, and Resilience (52A–52Q)
- Task lifecycle hardening, session/governance/lock/corruption recovery planning, runtime contract/sandbox/timeout hardening, output integrity verification, concurrency safety, parallel agent coordination, multi-agent state consistency, conflict resolution, chaos testing, failure injection planning, corruption simulation, and recovery validation. All commands are advisory; none inject failures, corrupt files, or execute recovery automatically.

## Governed Lifecycle

PCAE provides a governed lifecycle for task-based development. Every phase follows the same pattern:

```bash
# 1. Create a task contract with structured scope
pcae task new "70L Lifecycle Consolidation" \
  --goal "Document the governed lifecycle" \
  --mode implementation \
  --allowed-file "docs/COMMANDS.md" \
  --allowed-file "README.md" \
  --enforcement-mode advisory \
  --acceptance-check "pcae health passes"

# 2. Implement, then commit normally
git add <files>
git commit -m "Implement Phase 70L lifecycle consolidation"

# 3. Finish the task and commit closure in one governed command
pcae task finish --commit "Complete Phase 70L lifecycle consolidation"

# 4. Push with governed readiness validation
pcae push
```

After task closure, the repo enters a **healthy idle** state — no active task, clean working tree, all checks pass. This is a valid resting state, not a governance failure.

Key lifecycle commands:

| Command | Purpose |
|---------|---------|
| `pcae task new` | Create a task contract with goal, scope, and acceptance criteria |
| `pcae task finish` | Validate, close task, update memory files, refresh session |
| `pcae task finish --commit` | Finish and commit closure in one step |
| `pcae push` | Validate readiness and push to tracking branch |
| `pcae push check` | Check push readiness without pushing |
| `pcae doctor task-memory` | Detect task-memory inconsistencies |
| `pcae doctor task-memory --fix` | Repair deterministic inconsistencies |
| `pcae health` | Check overall governance health |
| `pcae check` | Validate source changes against policy |

## Backend-Output Adoption Lifecycle Commands

PCAE includes read-only and approval-bound lifecycle commands for the `backend-output-adoption` lifecycle:

| Command | Purpose |
|---------|---------|
| `pcae lifecycle backend-output-adoption status` | Display the current lifecycle state, including phase, gate results, and authorization flags. |
| `pcae lifecycle backend-output-adoption next` | Show advisory next steps based on current state. Does not perform any action. |
| `pcae lifecycle backend-output-adoption run-gate --dry-run` | Evaluate gate criteria and report pass/fail without recording results or changing state. |
| `pcae lifecycle backend-output-adoption approve-gate` | Record gate approval. Approval is recorded as a governance decision only — it does not trigger execution. |
| `pcae lifecycle backend-output-adoption summary` | Generate a final summary report of the lifecycle process, including all recorded decisions and gate evaluations. |

Non-dry-run gate execution is not implemented. Approval is separate from execution, and `execution_authorized=false` remains the safety default. These commands are governance/advisory tooling, not autonomous execution.

## Multi-Agent Governance Design

PCAE is building governance for AI-assisted and multi-agent software work — not unrestricted autonomous execution. The multi-agent design stream (Phases 82A–84K) defines how PCAE should discover agents, approve routing, send governed prompts, capture output, classify findings, review adoption candidates, and track deferred work, all under explicit human authorization at every step.

The current multi-agent work is **design and governance documentation only**. No multi-agent runtime execution, schema parsing, or CLI automation has been implemented from these designs. All designs carry `implementation_status=not_started`.

### Completed Design Artifacts (84-Series)

| Phase | Artifact | Description |
|-------|----------|-------------|
| 84A | [Lifecycle Lessons / Roadmap](docs/MULTI_AGENT_LIFECYCLE_LESSONS_ROADMAP.md) | Retrospective and forward roadmap from the 83A–83L governed lifecycle |
| 84B | [Prompt Package Schema](docs/MULTI_AGENT_PROMPT_PACKAGE_SCHEMA.md) | Machine-readable schema for approved prompts, roles, agents, and safety constraints |
| 84C | [Capture Metadata Schema](docs/MULTI_AGENT_CAPTURE_METADATA_SCHEMA.md) | Schema for invocation captures: stdout/stderr hashes, timing, mutation guard |
| 84D | [Output Intake Schema](docs/MULTI_AGENT_OUTPUT_INTAKE_SCHEMA.md) | Schema for classifying captured outputs before adoption review |
| 84E | [Adoption Candidate Schema](docs/MULTI_AGENT_ADOPTION_CANDIDATE_SCHEMA.md) | Schema for candidates, deferred items, and rejected items |
| 84F | [Lifecycle State Machine](docs/MULTI_AGENT_LIFECYCLE_STATE_MACHINE.md) | 15-state lifecycle connecting schemas into a unified model |
| 84G | [Lifecycle Command Dry-Run](docs/MULTI_AGENT_LIFECYCLE_COMMAND_DRY_RUN.md) | Read-only command surface design for lifecycle inspection |
| 84H | [Backend Invocation Guard](docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md) | Pre-invocation guard design: identity, command, hash, timeout, mutation checks |
| 84I | [Capture Storage Policy](docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md) | Where prompts, captures, and evidence live; git-tracked vs non-git rules |
| 84J | [Deferred Item Tracker](docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md) | Tracking policy for deferred, blocked, rejected, and future implementation items |

For a fuller overview, see [docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md](docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md).

### Key Safety Boundaries

- **Approved agent identity.** Only registered, verified agents may be invoked. Blocked and unknown agents are refused.
- **Exact prompt and command authorization.** Prompt text is SHA256-hashed at approval; the guard blocks invocation on any mismatch.
- **Capture before intake.** Every invocation must capture stdout/stderr with hashes before any classification occurs.
- **Intake before adoption.** Captured output must pass intake classification before adoption review.
- **Adoption approval before execution.** Human approval is required before any backend-originated change enters the repo.
- **Governed commit and push.** Commits and pushes use governed PCAE paths, not raw git operations.
- **Raw output is not adopted by default.** Backend output is evidence, not approved content, until explicitly reviewed and approved.
- **Deferred items are tracked, not approved.** Recording a deferred item does not authorize its implementation.

### Why Recent Phases Did Not Add Tests

Phases 84A–84K were documentation and design-only: they produced governance design artifacts without modifying source code, tests, or CLI behavior. Test mutation was intentionally not authorized. Future implementation phases (schema parsers, guard validators, lifecycle commands) will reintroduce tests as part of their governed scope.

### Next Steps

The 84-series multi-agent governance design stream was reconciled in Phase 84L with a Phase 85 plan. Phase 85 designs (85A–85F) and Phase 86 implementation (86A–86I) are complete. See the **Read-Only Project Intelligence Stack** section below.

## Read-Only Project Intelligence Stack

Phases 86A–86I implemented a read-only project-intelligence stack that answers governance questions from committed evidence. Six commands are available:

| Command | Purpose |
|---------|---------|
| `pcae artifact-index --json` | Lists governance artifacts with type, path, status, and freshness |
| `pcae memory-snapshot --json` | Reports current project memory state: phase, lifecycle, roadmap |
| `pcae governance-timeline --json` | Extracts ordered governance events from commits and artifacts |
| `pcae decision-log --json` | Extracts decision records with scope and authorization flags |
| `pcae risk-register --json` | Extracts risk records: active, accepted, deferred, stale, must-never-repeat |
| `pcae project-state --json` | Integrates all five layers into a single project-state answer |

**Read-only and non-authorizing.** These commands report observed governance state from committed evidence. They do not grant permission, authorize execution, invoke agents, approve adoption, permit commits, or permit pushes. All outputs are JSON to stdout — no generated cache, no committed state files, no `.pcae` storage.

**Test coverage.** 183 tests across 86C–86I, including 38 integration tests validating cross-layer consistency, no-write behavior, and no authority inference. Full suite: `python -m pytest -n auto` — 7122 passed, 0 failures.

For the full summary, see [docs/PHASE_85_READ_ONLY_STACK_SUMMARY.md](docs/PHASE_85_READ_ONLY_STACK_SUMMARY.md).

## CLI Examples

```
# Check repo governance health
pcae health

# Validate source changes against governance policy
pcae check

# Inspect repo readiness in detail
pcae inspect

# Show the current roadmap phase and capability registry
pcae roadmap current
pcae capability list

# Promote reviewed sandbox content to root (human-authorized only)
pcae promote --epr-id <id> --dry-run
pcae promote --epr-id <id>

# Reverse a promotion using its captured evidence
pcae rollback --per-id <id> --dry-run
pcae rollback --per-id <id>

# Surface independent review challenge context for a strategic decision
pcae irg-challenge

# Assess runtime trust
pcae runtime-trust
```

## Capability Maturity

| Status | Count | Examples |
|---|---|---|
| **Implemented** | 77 of 79 capabilities | Task contracts, write/execution orchestration chains, recovery planning, runtime hardening, multi-runtime registry, capability/roadmap intelligence, skill system, strategic lineage, IRG challenge, full 69A–69O execution governance activation chain |
| **Dormant** | 1 | Controlled Runtime Execution Pilot (Phase 62A) — superseded in practice by the read-only runtime invocation governance it depends on; not removed, not currently exercised |
| **Superseded** | 1 | Invocation Pilot (Legacy, Phase 46A–46J) — replaced by the Multi-Runtime Registry (Phase 63A) |
| **Roadmap gaps** | 0 | No registered phase is missing an implementation |

Run `pcae capability-inventory` for the live, regenerated inventory (`docs/CAPABILITY_INVENTORY.md`).

## Current Safety Status

PCAE has completed BR-005 (Execution Governance Activation) through Phase 69O. The full chain from human approval to governed root promotion to governed rollback is implemented and tested.

| Capability | Status |
|---|---|
| Real AI runtime invocation | **Disabled** — `execution_allowed=False` for every command, including `pcae promote` and `pcae rollback` |
| Governed write to root | **Enabled, human-gated** — `pcae promote` writes only content already captured in an ECP and explicitly authorized in an EPR (`promotion_authorized=True`) |
| Governed rollback of a promotion | **Enabled, human-gated** — `pcae rollback` reverses only a specific PER's writes, gated on `rollback_payload_available=True` |
| Rollback-of-rollback | **Forbidden by construction** — no command accepts an `rer_id` as a rollback target |
| Git commit / push automation | **Disabled** — every governed path stops at a file-level write or reversal; commit and push remain human actions |
| Failure injection / corruption simulation | **Disabled** — `injection_allowed=False` / `simulation_allowed=False` for all such commands |
| Recovery execution | **Disabled** — `recovery_allowed=False` and `recovery_execution_allowed=False` for all recovery commands |
| Human review | **Required** — for every invocation, promotion, and rollback decision |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#current-limitations) for the full, current list of limitations and deferred capabilities, including the unresolved Phase Activation Governance gap (implementation approval does not imply activation, commit, or push approval).

## Roadmap Snapshot

See [docs/ROADMAP.md](docs/ROADMAP.md) for the canonical roadmap. This section summarizes the current state.

### Completed

| Arc | Phases | Status |
|-----|--------|--------|
| Governance foundation | 44A–69O | Complete — task contracts through execution governance activation |
| Multi-agent and intelligence | 82A–87J | Complete — agent discovery through governed action gates |
| Advisory and enforcement readiness | 88P–90B | Complete — shell gate, permission broker, advisory, dry-run simulation, enforcement readiness, full-suite green (9530/9530) |

### Production v1 Path (In Progress)

| Series | Phases | Focus |
|--------|--------|-------|
| **90** | 90A–90C | Enforcement boundary and test foundation |
| **91** | 91A–91C | Permission broker simulation prototype and CLI |
| **92** | 92A–92D | Phase reporting, notification foundation, Telegram outbound delivery |
| **93** | 93A–93B | Narrow shell gate design and prototype |
| **94** | 94A | Governed backend invocation design |
| **95–96** | 95A–96A | Documentation, install, demo, governance review |

**Recommended next phase:** 90C — Permission Broker Enforcement Boundary Test Plan (requires explicit operator approval).

### Future v2 / Pluggability

Notification adapters, backend adapters, policy modules, audit storage adapters, multi-agent orchestration plugins, mobile command gateway (post-broker/shell-gate maturity), external packaging.

### Limitations

- PCAE is **not production ready**
- Enforcement is **simulation-only** — no real blocking, no shell interception
- Permission broker and shell gate are **simulation prototypes, not enforcement engines**
- Dry-run/advisory output is **not authorization**
- No agent is given autonomous repo access
- Telegram is **outbound only** in Production v1 — no inbound commands, no remote shell

## Contributing

Contributions must preserve PCAE's governance guarantees. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, contribution workflow, governance requirements, testing standards, and pull request expectations.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
