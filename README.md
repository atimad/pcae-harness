# PCAE — Policy Controlled Autonomous Execution

PCAE is a governance-first framework for controlled AI-assisted engineering. It is a cross-platform Python CLI injected into Git repositories to make AI coding agent execution safe, resumable, auditable, and human-authoritative.

For the project vision and long-term direction, see [VISION.md](VISION.md). For the authoritative governance reference, see the [Governance Handbook](docs/governance/GOVERNANCE_HANDBOOK.md). For a detailed technical description of the architecture, governance model, and design philosophy, see the [PCAE Architecture White Paper](docs/whitepaper/PCAE_WHITEPAPER.md).

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

PCAE is currently in the **controlled scaffolding phase** of the read-only invocation track.

| Capability | Status |
|---|---|
| Runtime execution | **Disabled** — `execution_allowed=False` for all runtimes |
| Prompt execution | **Disabled** — no prompt is submitted in any current phase |
| Write execution | **Disabled** — write execution requires a separately governed gate not yet implemented |
| Human review | **Required** — `human_review_required=True` for all invocation-related commands |

No PCAE command currently invokes a runtime, submits a prompt, or modifies repository files as part of agent execution. All invocation-related commands are scaffolds that evaluate readiness and report blockers.

## Roadmap Snapshot

| Track | Status |
|---|---|
| Documentation program | Active — architecture, commands, glossary, and governance docs generated and validated |
| Controlled read-only invocation | Active — Phase 48H complete; invocation evidence model implemented |
| Multi-agent read-only pilot | Planned — agent orchestration and capability matrix in place; pilot scaffolds ready |
| Controlled write pilot | Planned — rollback governance and change governance scaffolds complete; write gate not yet implemented |
| Autonomous engineering | Future — depends on evidence and review infrastructure passing human review requirements |

## Contributing

Contributions must preserve PCAE's governance guarantees. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, contribution workflow, governance requirements, testing standards, and pull request expectations.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
