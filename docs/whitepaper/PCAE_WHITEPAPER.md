# PCAE Architecture White Paper

**Policy Controlled Autonomous Execution**

*Version 1.0 — Phase 48X.2*

---

## 1. Executive Summary

PCAE (Policy Controlled Autonomous Execution) is a governance-first framework for controlled AI-assisted software engineering. It wraps AI coding agent execution in a structured chain of authorization, preflight, audit, capture, review, and evidence gates — none of which an agent can bypass.

The current implementation is a cross-platform Python CLI injected into Git repositories. It enforces task contracts, validates governance artifacts, orchestrates multi-agent workflows, and scaffolds the full invocation lifecycle for future controlled read-only and write execution. Runtime execution is explicitly disabled in the current phase; every invocation-related command produces a structured scaffold that evaluates readiness and reports what must still be resolved before execution can be considered.

PCAE is designed for engineering teams that want to adopt AI coding agents responsibly — with full auditability, human-authoritative approval, and governed rollback — rather than accepting the risk of unconstrained agent autonomy.

For the project vision, long-term direction, and core principles, see [VISION.md](../../VISION.md).

---

## 2. Problem Statement

AI coding agents are increasingly capable of producing real changes to real repositories: file edits, commits, pushed branches, triggered CI pipelines. The engineering industry has adopted these capabilities faster than it has built the governance infrastructure to support them safely.

Current agent deployments commonly lack:

- **Explicit authorization gates.** Agents execute when invoked, regardless of whether the change has been approved or even reviewed.
- **Pre-execution preflight checks.** No systematic verification that sandbox conditions, timeout contracts, and output capture are in place before the agent runs.
- **Structured audit trails.** Without a linked chain of request, authorization, execution, and result records, there is no reliable basis for post-hoc review or incident response.
- **Planned rollback.** When an agent-driven change produces an unacceptable state, recovery depends on ad hoc git operations rather than a pre-declared rollback plan.
- **Runtime trust verification.** Different AI runtimes have different sandboxing guarantees, output behaviors, and trust levels. These differences are rarely evaluated systematically.
- **Human authority preservation.** The human engineer remains the ultimate decision-maker, but current tooling provides no structural enforcement of that authority.

The absence of these controls does not merely create operational risk — it creates a category of failure where an AI agent makes a consequential change, no human approved it, no audit trail exists, and rollback requires manual forensics.

---

## 3. Why Existing Agent Systems Are Risky

The risk in current AI coding agent systems is not primarily a question of model capability. It is a question of execution architecture.

**No concept of authorization scope.** Most agent invocations are unbounded: the agent may read any file, modify any file, and attempt any shell command within the repo. Task-level scoping — constraining the agent to the files and operations relevant to the current work item — is absent.

**No execution contract.** Nothing in the typical agent invocation specifies what output must be captured, what timeout applies, what sandbox mode is expected, or what constitutes a valid result. These are all implicit, and implicit contracts cannot be enforced.

**No evidence chain.** An agent that modifies ten files and pushes a commit leaves behind only a commit message. The link between the original task, the authorization decision, the preflight state, the captured output, the review, and the final repository state exists only in informal documentation, if at all.

**Rollback is afterthought.** Rollback strategies are invented after something goes wrong, rather than declared and validated before execution begins. This inverts the correct order of operations.

**Trust is assumed, not verified.** The assumption that a particular AI runtime is safe to invoke in a particular context is rarely verified against explicit criteria.

PCAE is designed to address each of these gaps systematically, through architecture rather than process.

---

## 4. PCAE Design Philosophy

PCAE is built on six design commitments:

**1. Governance is structural, not advisory.**
PCAE does not produce guidelines for human engineers to follow. It produces machine-enforceable gates that block execution when preconditions are unmet. The difference between a governance checklist and a governance gate is that the gate cannot be skipped.

**2. Humans remain authoritative.**
No PCAE command approves, commits, pushes, or rolls back without explicit human confirmation. The framework surfaces information, evaluates readiness, and proposes actions — but it does not take consequential actions autonomously.

**3. Evidence precedes execution.**
Every execution attempt must be backed by a complete chain of structured artifacts: invocation request, authorization result, runtime contract enforcement result, preflight result, audit record, capture path, and review record. Execution is not eligible until all upstream evidence gates are satisfied.

**4. Read-only before write.**
The invocation track is sequenced deliberately: read-only invocation pilots must demonstrate governance soundness before write execution is introduced. Write execution requires a separately governed gate with explicit rollback planning.

**5. Audit everything.**
Every invocation attempt — including blocked attempts — produces a structured audit record. The audit trail is complete regardless of whether execution succeeded or was blocked.

**6. Rollback must be planned.**
Rollback strategies are declared, validated, and linked to the change plan before any write execution begins. Rollback is not a recovery option; it is a precondition.

---

## 5. Governance-First Architecture

PCAE organizes its governance logic into seven domains, each responsible for a distinct layer of the execution lifecycle:

```
┌──────────────────────────────────────────────────────────────────┐
│                         PCAE Governance                          │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│   Change     │   Rollback   │    Prompt    │     Execution      │
│  Governance  │  Governance  │  Governance  │    Governance      │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│             Runtime Governance  │  Multi-Agent Governance       │
├─────────────────────────────────┴───────────────────────────────┤
│                  Audit, Evidence, and Trust                      │
└──────────────────────────────────────────────────────────────────┘
```

Each domain produces structured, machine-readable artifacts. Each domain's output gates the next domain's input. No domain executes without its upstream domain having produced a valid artifact.

See [01-governance-stack.md](../architecture/01-governance-stack.md) for an interactive Mermaid diagram of the governance stack.

---

## 6. Change Governance

Change governance controls what files an agent may touch, in what scope, and under what task contract.

**Task contracts** (`tasks/active/*.md`) define:
- The allowed file scope for the current work item
- Forbidden files and forbidden operations
- Override-protected files that require explicit elevation
- The enforcement mode (advisory vs. strict)
- Acceptance checks that must pass before the task is considered complete

**Policy checks** (`pcae check`) enforce task contracts on every source change:
- Validates that architecture zone rules are respected
- Requires documentation files to be updated alongside source changes
- Verifies session continuity (active task matches working state)
- Reports violations and warnings in human or JSON form

Change governance is the outermost gate. A task that violates its contract cannot produce a valid authorization for execution.

---

## 7. Rollback Governance

Rollback governance ensures that a recovery plan exists and is validated before any write execution begins.

The rollback governance domain models the full write lifecycle:

1. **Pre-modification snapshot** — the repository state before the change is captured.
2. **Targeted change** — the agent's modification, constrained to the task scope.
3. **Verification** — the post-change state is verified against acceptance criteria.
4. **Rollback trigger** — if verification fails, the rollback plan is invoked.

Rollback artifacts define:
- The rollback strategy (git revert, reset, or custom)
- The verification criteria that trigger rollback
- The human approval required before rollback executes
- The audit record linking the rollback to the original change

Write execution is not eligible until rollback artifacts are present and valid. This inverts the typical failure mode where rollback is improvised after a bad deployment.

---

## 8. Prompt Governance

Prompt governance controls how prompts are constructed, validated, and delivered to AI runtimes.

**Prompt generation** produces parameterized, governance-aware prompts from structured task and context inputs. Prompts are not ad hoc strings — they are typed artifacts with declared inputs, scope constraints, and expected output formats.

**Prompt rendering** (`pcae prompt-render`) applies the current task context, policy state, and governance artifacts to produce a concrete prompt ready for submission. The rendered prompt includes:
- Task scope constraints
- Forbidden operations (derived from the task contract)
- Expected output format
- Timeout and sandbox parameters

**Prompt preflight** validates the rendered prompt before submission:
- Verifies that the prompt does not request forbidden operations
- Confirms that authorization and contract enforcement artifacts are present
- Blocks submission if any upstream gate is unresolved

No prompt is submitted without a valid preflight result.

See [03-prompt-governance.md](../architecture/03-prompt-governance.md) for the prompt governance flow diagram.

---

## 9. Execution Governance

Execution governance is the core gate chain that determines whether an invocation is eligible to proceed.

**The invocation lifecycle** progresses through eight sequential gates:

| Step | Gate | Input Artifact |
|------|------|----------------|
| 1 | Request created | `ReadOnlyInvocationRequest` |
| 2 | Authorization enforcement checked | `InvocationAuthorizationEnforcementResult` |
| 3 | Runtime contract enforcement checked | `RuntimeContractEnforcementResult` |
| 4 | Preflight checked | `ReadOnlyInvocationPreflight` |
| 5 | Audit trail checked | `InvocationAuditRecord` |
| 6 | Result capture path checked | `InvocationResultCapture` |
| 7 | Human approval checked | `human_approval_artifact` |
| 8 | Pilot result produced | `ReadOnlyRuntimePilotResult` |

Every gate is blocking. A failure at any step halts the chain and produces a structured blocker report. `execution_allowed` remains `False` until all eight gates pass — and currently, none do, because the governance infrastructure is still being built out.

**Key execution governance commands:**

- `pcae readonly-invocation` — scaffold and evaluate the invocation request and preflight
- `pcae invocation-authorization-enforcement` — evaluate the 8-step authorization chain
- `pcae runtime-contract-enforcement` — evaluate runtime-specific contract compliance
- `pcae readonly-runtime-pilot` — evaluate the full 8-step lifecycle readiness
- `pcae invocation-audit` — scaffold the audit record for this invocation attempt
- `pcae invocation-result-review` — scaffold the result review workflow
- `pcae invocation-evidence` — link all upstream artifacts into a single evidence record

See [02-execution-lifecycle.md](../architecture/02-execution-lifecycle.md) for the full gate chain diagram.

---

## 10. Runtime Governance

Runtime governance verifies that the target AI runtime is safe to invoke before any invocation is attempted.

**Trust assessment** (`pcae runtime-trust`) evaluates each configured runtime against explicit trust criteria:
- Is the runtime sandboxed?
- Is the runtime's output deterministic and capturable?
- Does the runtime operate within the declared timeout contract?
- Is the runtime's invocation mode consistent with the request?

**Contract enforcement** (`pcae runtime-contract-enforcement`) evaluates seven blocking checks:

| Check | Description |
|-------|-------------|
| `runtime_contract_exists` | A contract artifact exists for this runtime |
| `runtime_trust_acceptable` | The runtime's trust level meets the minimum threshold |
| `sandbox_contract_verified` | Sandbox conditions are confirmed |
| `timeout_contract_verified` | Timeout parameters are confirmed |
| `output_capture_contract_verified` | Output capture path is ready |
| `invocation_mode_matches_request` | The runtime's invocation mode matches the request type |
| `writable_execution_blocked` | Write execution is explicitly blocked (current phase) |

All three currently configured runtimes (codex-local, claude-local, kimi-local) are blocked by contract enforcement in the current phase. This is expected and intentional: the scaffolding must be complete and validated before any runtime is cleared for invocation.

See [04-runtime-governance.md](../architecture/04-runtime-governance.md) for the runtime governance flow diagram.

---

## 11. Multi-Agent Governance

Multi-agent governance orchestrates the selection, sequencing, and handoff of AI agents across complex engineering workflows.

**Agent orchestration** (`pcae orchestration`) provides:
- **Capability matrix** — a structured inventory of what each agent can and cannot do
- **Agent selection** — matches task types to agents based on the capability matrix
- **Handoff sequencing** — defines the order in which agents hand off to each other and what context is transferred

**Policy-governed routing** ensures that agent selection is driven by the current governance policy, not by ad hoc assignment. The orchestration policy defines:
- Which agent types are authorized for which task types
- Capability constraints (e.g., an agent authorized for read-only tasks cannot be selected for write tasks)
- Handoff protocols (what state the receiving agent requires before it can begin)

**Vendor neutrality** is a design goal. PCAE does not assume a fixed agent roster. The policy configuration supports Claude, Codex, Kimi, DeepSeek, and other agents without implying fixed work-type ownership.

---

## 12. Audit, Evidence, and Trust

The audit, evidence, and trust layer produces the structured records that make every invocation attempt reviewable, attributable, and defensible.

**Audit records** (`InvocationAuditRecord`) link:
- The invocation request
- The authorization enforcement result
- The runtime contract enforcement result
- The preflight result
- The result capture record
- The human approval artifact

**Evidence records** (`InvocationEvidenceRecord`) extend audit records to include:
- The prompt reference
- The result review record
- A single `evidence_status` field reflecting the completeness of the entire chain

**Review records** (`InvocationResultReviewRecord`) capture the human review of captured invocation output, including per-stream review status (stdout, stderr, metadata) and quality framework results.

**Trust chain integrity** is maintained by ensuring that no artifact in the chain can be produced without its upstream artifacts being present and valid. A complete evidence record is the terminal artifact of a fully governed invocation: it cannot exist unless every preceding gate was satisfied.

In the current phase, all evidence records have `evidence_status=not_executed` because no runtime has been invoked. This is the correct state. The evidence infrastructure is being validated before execution begins.

---

## 13. Current Maturity

As of Phase 48X.2, PCAE has completed the following governance infrastructure:

| Domain | Status | Key Artifacts |
|--------|--------|---------------|
| Change governance | Complete | Task contracts, policy checks, architecture zone enforcement |
| Rollback governance | Scaffolded | Rollback design, dry-run validation, write pilot scaffold |
| Prompt governance | Scaffolded | Prompt generation, rendering, preflight |
| Execution governance | Scaffolded | Full 8-step lifecycle, all gates blocking |
| Runtime governance | Scaffolded | Trust assessment, contract enforcement (all blocked) |
| Multi-agent governance | Active | Capability matrix, agent selection, orchestration policy |
| Audit and evidence | Scaffolded | Audit record, result review, evidence model (all not_executed) |

**Current safety invariants:**

- `execution_allowed=False` for all runtimes in all invocation-related commands
- `human_review_required=True` for all invocation-related commands
- No PCAE command invokes a runtime, submits a prompt, or modifies repository files as part of agent execution
- All blocked states are intentional and reflect the current phase boundary

---

## 14. Roadmap

| Track | Status | Description |
|-------|--------|-------------|
| Documentation program | Active | Architecture, commands, glossary, white paper, architecture diagrams generated and validated |
| Controlled read-only invocation | Active — Phase 48H complete | Full evidence model implemented; all gates scaffolded; execution still blocked |
| Parallel test execution | Complete — 48X.T | `pytest-xdist` standardized; three execution profiles documented (fast, battery, release); see [Test Execution Guide](../testing/TEST_EXECUTION.md) |
| Invocation execution gate | Planned — 49A | Implement the gate that conditionally clears `execution_allowed` when all 8 lifecycle gates pass |
| Multi-agent read-only pilot | Planned | Extend the pilot scaffold to multi-agent workflows; validate orchestration handoff |
| Controlled write pilot | Planned | Introduce write execution with explicit rollback planning as a precondition |
| Autonomous engineering | Future | Depends on evidence and review infrastructure passing sustained human review requirements |

The sequencing is deliberate. Each phase must demonstrate governance soundness before the next phase introduces new execution capability. No phase skips a gate.

See [05-future-autonomous-flow.md](../architecture/05-future-autonomous-flow.md) for the target autonomous engineering loop (future state).

---

## 15. Contributing

PCAE welcomes contributions that preserve its governance guarantees. The
[CONTRIBUTING.md](../../CONTRIBUTING.md) guide documents the full contribution
workflow, including development setup, governance requirements, testing
standards, and pull request expectations.

The governance bar for contributions is the same bar PCAE enforces in the
repos it governs: human approval remains authoritative, auditability is
required, rollback paths must exist, runtime trust must be assessed, and
evidence must precede execution. Contributions that weaken any of these
guarantees fall outside the accepted scope.

**Development setup.** Clone the repository, create a virtual environment,
install dependencies with `pip install -e ".[dev]"`, and verify with
`pcae health`, `pcae check`, and `python -m pytest -n auto`. All three
must pass before beginning work.

**Parallel test execution.** The preferred validation path is
`python -m pytest -n auto`, which distributes the test suite across available
CPU cores using `pytest-xdist`. This is the standard for CI and local
pre-commit validation. Tests must be written to be parallel-safe. For all
execution profiles (fast validation, battery mode, release verification) and
parallel safety requirements, see the
[Test Execution Guide](../testing/TEST_EXECUTION.md).

**Documentation.** Every behavior-visible change requires corresponding
updates to `CHANGELOG.md` and `PROJECT_STATUS.md` at minimum. Architecture
changes additionally require updates to the white paper, architecture
diagrams, and the [Governance Handbook](docs/governance/GOVERNANCE_HANDBOOK.md).

---

## 16. License

PCAE is licensed under the Apache License 2.0.

Copyright 2026 Atila Madai

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

See the [LICENSE](../../LICENSE) file for the full license text.
