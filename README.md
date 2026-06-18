# PCAE — Policy Controlled Autonomous Execution

PCAE is a governance harness for AI-assisted software development: a cross-platform Python CLI injected into Git repositories to make AI coding agent activity safe, resumable, auditable, and human-authoritative. It does not make agents trustworthy by assumption — it makes their work governable by requiring evidence at every step and refusing to proceed when that evidence is missing.

For installation instructions, see [docs/INSTALLATION.md](docs/INSTALLATION.md). For the project vision and long-term direction, see [VISION.md](VISION.md). For the authoritative architecture reference, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For the governance handbook, see the [Governance Handbook](docs/governance/GOVERNANCE_HANDBOOK.md). For test execution profiles, see the [Test Execution Guide](docs/testing/TEST_EXECUTION.md). For the BR-005 execution governance retrospective, see [docs/RETROSPECTIVE_BR005.md](docs/RETROSPECTIVE_BR005.md). For a detailed technical description of the architecture, governance model, and design philosophy, see the [PCAE Architecture White Paper](docs/whitepaper/PCAE_WHITEPAPER.md).

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

### Completed

| Track | Status |
|---|---|
| Documentation program | Complete — architecture, commands, glossary, and governance docs generated and validated |
| Controlled read-only invocation | Complete — Phase 48H; full evidence model implemented |
| Multi-agent governance | Complete — Phase 49A–49Q; governance state, invariants, drift detection, lock governance |
| Controlled write governance | Complete — Phase 50A–50K; full 11-step write governance chain |
| Controlled execution orchestration | Complete — Phase 51A–51K; full 11-step execution orchestration chain |
| Recovery planning | Complete — Phase 52A–52E; task, session, governance, lock, and corruption recovery |
| Runtime hardening | Complete — Phase 52F–52I; contract, sandbox, timeout, output integrity |
| Concurrency and multi-agent coordination | Complete — Phase 52J–52M; concurrency safety, parallel coordination, state consistency, conflict resolution |
| Chaos engineering and resilience | Complete — Phase 52N–52Q; chaos testing, failure injection, corruption simulation, recovery validation |
| Multi-runtime governance | Complete — Phase 55A–64H; runtime registry, trust, selection, arbitration, audit, quarantine, orchestration readiness |
| Capability and roadmap intelligence | Complete — Phase 64B Series; capability inventory, roadmap/prompt/skill intelligence |
| Strategic governance and independent review | Complete — Phase 65A–68D; strategic lineage, IRG challenge |
| **Execution governance activation (BR-005)** | **Complete — Phase 69A–69O; full approval → authorization → audit → activation → sandboxing → change capture → promotion → rollback chain** |

### Next

There is no currently active successor phase. Phase 69O remains the formally active phase in the authoritative roadmap registry (`_CRI_KNOWN_PHASES` requires exactly one active phase) pending an explicit, human-approved phase activation decision — this is intentional governance behavior, not an oversight (see [Phase Activation Governance](docs/ARCHITECTURE.md#current-limitations) in the architecture doc and the open item in [tasks/TODO.md](tasks/TODO.md)).

## Contributing

Contributions must preserve PCAE's governance guarantees. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, contribution workflow, governance requirements, testing standards, and pull request expectations.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
