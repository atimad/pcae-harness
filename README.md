# PCAE — Policy Controlled Autonomous Execution

PCAE is a governance-first framework for controlled AI-assisted engineering. It is a cross-platform Python CLI injected into Git repositories to make AI coding agent execution safe, resumable, auditable, and human-authoritative.

For the project vision and long-term direction, see [VISION.md](VISION.md). For the authoritative governance reference, see the [Governance Handbook](docs/governance/GOVERNANCE_HANDBOOK.md). For test execution profiles and parallel validation guidance, see the [Test Execution Guide](docs/testing/TEST_EXECUTION.md). For a detailed technical description of the architecture, governance model, and design philosophy, see the [PCAE Architecture White Paper](docs/whitepaper/PCAE_WHITEPAPER.md).

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

- **Human approval remains authoritative.** No execution proceeds without explicit human sign-off.
- **Read-only before write.** Invocation starts with read-only pilots; write execution requires a separately governed gate.
- **Evidence before execution.** Authorization, preflight, audit, capture, and review records must exist before any invocation is eligible.
- **Audit everything.** Every invocation attempt produces a structured audit trail regardless of outcome.
- **Rollback must be planned.** Rollback strategies are declared and validated before any write execution begins.
- **Runtime trust must be verified.** Runtime contract enforcement is evaluated independently for each runtime target.
- **No automatic commit, push, or rollback.** These operations require human confirmation and are never triggered automatically by agents.

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

The implementation is organized into six architecture layers:

| Layer | Phases | Description |
|---|---|---|
| **Governance Layer** | 1–49 | Task contracts, policy checks, orchestration, session continuity |
| **Execution Layer** | 50A–51K | Write authorization and execution orchestration chains |
| **Recovery Layer** | 52A–52E | Task, session, governance, lock, and corruption recovery planning |
| **Runtime Hardening Layer** | 52F–52I | Contract hardening, sandbox isolation, timeout governance, output integrity |
| **Concurrency Layer** | 52J–52M | Concurrency safety, parallel coordination, state consistency, conflict resolution |
| **Resilience Layer** | 52N–52Q | Chaos testing, failure injection planning, corruption simulation, recovery validation |

## Current Capabilities

### Task and Policy Governance
- **Task contracts** constrain which files an agent may touch, which operations are forbidden, and what the session goal is.
- **Policy checks** (`pcae check`) validate that every source change is accompanied by documentation updates and that architecture zone rules are respected.
- **Session continuity** verifies that the active task matches the current working state on every check.

### Change and Rollback Governance
- **Controlled modification design** models the full lifecycle of a governed write: pre-modification snapshot, targeted change, verification, and rollback trigger.
- **Controlled commit, push, and rollback governance** produces structured scaffolds defining the approval and rollback plan before any mutation occurs.

### Prompt Governance
- **Prompt generation and rendering** (`pcae prompt-render`) produces governed, parameterized prompts for agent invocation, with preflight validation before submission.

### Execution Readiness and Pilot Scaffolds
- **Controlled read-only invocation scaffold** (`pcae readonly-invocation`) defines the request, preflight, and result models for a sandboxed read-only agent run.
- **Controlled read-only runtime invocation pilot** (`pcae readonly-runtime-pilot`) evaluates an 8-step lifecycle readiness gate across all configured runtimes.
- **Invocation audit trail** (`pcae invocation-audit`) scaffolds the audit record linked to every invocation attempt.
- **Invocation result review** (`pcae invocation-result-review`) scaffolds the review workflow for captured invocation output.
- **Invocation evidence model** (`pcae invocation-evidence`) links all upstream artifacts — request, authorization, audit, capture, and review — into a single evidence record.

### Runtime Governance
- **Runtime trust assessment** (`pcae runtime-trust`) evaluates each configured runtime for trust level, sandbox compliance, and contract verification.
- **Runtime contract enforcement** (`pcae runtime-contract-enforcement`) evaluates blocking enforcement checks before any invocation is eligible.
- **Invocation authorization enforcement** (`pcae invocation-authorization-enforcement`) evaluates an 8-step authorization chain covering authorization artifacts, preflight state, contract enforcement, and human approval.

### Controlled Write Governance (50A–50K)
- **Write authorization chain** (`pcae write-authorization` through `pcae write-recommendation`) implements the complete 10-step governed write lifecycle: authorization, review, decision, lifecycle, planning, readiness, evidence, audit, rollback verification, governance audit, and recommendation.
- All write-related commands are advisory and read-only. No write execution occurs. `authorization_allowed=False` and `execution_allowed=False` for all commands.

### Controlled Execution Orchestration (51A–51K)
- **Execution orchestration chain** (`pcae execution-request` through `pcae execution-recommendation`) implements the complete 11-step governed execution lifecycle: request, review, decision, lifecycle, plan, readiness assessment, evidence, audit, rollback verification, governance audit, and recommendation.
- All execution-related commands are advisory and read-only. No execution occurs. `execution_allowed=False` for all commands.

### Recovery Planning (52A–52E)
- **Task lifecycle hardening** (`pcae task-lifecycle-hardening`) detects stale, inconsistent, or ambiguous task state before it contaminates sessions or handoffs.
- **Session recovery** (`pcae session-recovery`) defines recovery planning for stale, missing, or orphaned session state.
- **Governance state recovery** (`pcae governance-state-recovery`) defines recovery planning for inconsistent or corrupted governance records.
- **Agent lock recovery** (`pcae agent-lock-recovery`) defines recovery planning for stale, conflicting, or orphaned agent lock state.
- **Corruption recovery** (`pcae corruption-recovery`) defines recovery planning for corrupted project state artifacts.
- All recovery commands are advisory. `recovery_allowed=False` and `human_review_required=True` for all commands.

### Runtime Hardening (52F–52I)
- **Runtime contract hardening** (`pcae runtime-contract-hardening`) validates runtime contracts for determinism, governability, and completeness.
- **Sandbox hardening** (`pcae sandbox-hardening`) validates sandbox isolation boundaries: filesystem, process, network, and environment.
- **Timeout hardening** (`pcae timeout-hardening`) validates timeout governance for bounded, recoverable, runaway-resistant execution.
- **Output integrity verification** (`pcae output-integrity-verification`) validates that future runtime outputs will be deterministic, attributable, complete, and tamper-resistant.

### Concurrency and Multi-Agent Coordination (52J–52M)
- **Concurrency safety** (`pcae concurrency-safety`) validates safety requirements for simultaneous agents, sessions, and governance workflows.
- **Parallel agent coordination** (`pcae parallel-agent-coordination`) validates coordination requirements for agents operating in parallel.
- **Multi-agent state consistency** (`pcae multi-agent-state-consistency`) validates consistency requirements for shared state across coordinated agents.
- **Conflict resolution engine** (`pcae conflict-resolution-engine`) defines conflict detection, severity classification, escalation, and advisory resolution planning for multi-agent workflows.

### Chaos Engineering and Resilience (52N–52Q)
- **Chaos testing** (`pcae chaos-testing`) defines chaos scenarios for governance, recovery, hardening, concurrency, and conflict-resolution workflows. Scenarios are defined but not executed.
- **Failure injection planning** (`pcae failure-injection`) defines controlled failure-injection scenarios for validating PCAE detection and recovery planning. No failures are injected.
- **Corruption simulation** (`pcae corruption-simulation`) defines controlled corruption scenarios for validating PCAE corruption detection and recovery planning. No files are corrupted.
- **Recovery validation** (`pcae recovery-validation`) validates that recovery plans, chaos scenarios, failure-injection scenarios, and corruption-simulation scenarios have complete, governed, human-reviewed recovery paths.

### Capability and Roadmap
- **Capability discovery** (`pcae orchestration capabilities`) exposes the current governed capability matrix for agent orchestration.
- **Roadmap evidence** (`pcae roadmap-evidence`) reports structured evidence of completed phases to keep roadmap and provenance coherent.
- **Governance audit** (`pcae governance audit`) validates all governance artifacts for drift and consistency.

## CLI Examples

```
# Check repo governance health
pcae health

# Validate source changes against governance policy
pcae check

# Inspect repo readiness in detail
pcae inspect

# Report roadmap evidence
pcae roadmap-evidence

# Render a governed prompt
pcae prompt-render

# Audit governance artifacts
pcae governance audit

# Assess runtime trust
pcae runtime-trust

# Report invocation evidence readiness
pcae invocation-evidence
```

## Current Safety Status

PCAE has completed governance scaffolding through Phase 52Q. The project is at the **Post-52Q Architecture Checkpoint**, with 4201 passing tests and governance infrastructure complete across all six architecture layers. Runtime integration has not yet begun.

| Capability | Status |
|---|---|
| Runtime execution | **Disabled** — `execution_allowed=False` for all runtimes |
| Prompt execution | **Disabled** — no prompt is submitted in any current phase |
| Write execution | **Disabled** — `authorization_allowed=False` and `execution_allowed=False` for all write commands |
| Failure injection | **Disabled** — `injection_allowed=False` for all failure injection commands |
| Corruption simulation | **Disabled** — `simulation_allowed=False` for all corruption simulation commands |
| Recovery execution | **Disabled** — `recovery_allowed=False` and `recovery_execution_allowed=False` for all recovery commands |
| Human review | **Required** — `human_review_required=True` for all invocation-related commands |

No PCAE command currently invokes a runtime, submits a prompt, or modifies repository files as part of agent execution. All invocation-related commands are scaffolds that evaluate readiness and report blockers.

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

### Next

| Phase | Track | Description |
|---|---|---|
| 54A | Runtime integration | Runtime Integration Readiness |
| 55A | Runtime integration | Controlled Read-Only Runtime Invocation |
| 56A | Runtime integration | Runtime Output Capture Persistence |
| 57A | Runtime integration | Human Review of Runtime Output |
| 58A | Multi-agent execution | Multi-Agent Read-Only Execution Pilot |
| 59A | Write execution | Controlled Write Dry-Run |
| 60A | Write execution | First Controlled Single-File Write Pilot |

## Contributing

Contributions must preserve PCAE's governance guarantees. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, contribution workflow, governance requirements, testing standards, and pull request expectations.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
