# PCAE — Project Vision

## 1. Vision Statement

PCAE (Policy Controlled Autonomous Execution) is becoming a governance-first
platform for controlled AI-assisted software evolution.

Its purpose is to make AI coding agents safe to use in production engineering
contexts — not by limiting their capability, but by surrounding their
execution with the approval gates, audit trails, rollback plans, and evidence
chains that responsible engineering requires.

The long-term vision is a platform where AI agents can assist with every phase
of software evolution — from roadmap generation to code authorship to
deployment — while every consequential action remains subject to human
authorization, every step is traceable, and no change is irreversible without
a pre-declared rollback path.

---

## 2. The Problem

AI coding agents can generate code at a pace that outstrips a team's ability
to review, approve, and recover from the changes they produce.

The core risks are architectural, not incidental:

**Uncontrolled execution.** Most agent invocations are unbounded. The agent
may read any file, modify any file, and attempt any shell operation within the
repository. Task-level scoping — constraining the agent to the files and
operations relevant to the current work item — is typically absent.

**Missing approval gates.** Agents execute when invoked, regardless of whether
the change has been reviewed, whether a rollback plan exists, or whether the
runtime has been evaluated for trust. There is no structural enforcement of
the approval step.

**Missing audit trails.** Without a linked chain connecting the original
request, the authorization decision, the preflight state, the captured output,
the review, and the final repository state, there is no reliable basis for
post-hoc review or incident response.

**Rollback as afterthought.** Rollback strategies are improvised after
something goes wrong rather than declared and validated before execution
begins. This inverts the correct order of operations.

**Unverified runtime trust.** Different AI runtimes have different sandboxing
guarantees, output behaviors, and trust levels. These differences are rarely
evaluated systematically before an agent is invoked.

**Human authority eroding by default.** The tooling that surrounds most
agent deployments provides no structural enforcement of human authority.
Humans remain nominally in control, but the architecture does not enforce it.

These are not edge cases or misconfigurations. They are the default state of
AI agent deployment today. PCAE is built to change that default.

---

## 3. The PCAE Approach

PCAE is built on five operating principles that apply at every phase of
development:

**Governance before autonomy.** No agent capability is introduced until the
governance infrastructure that contains it is in place. Execution gates are
built before execution is enabled. Evidence infrastructure is validated before
evidence is required.

**Evidence before execution.** An invocation is not eligible to run until
authorization, preflight, audit, capture, and review records all exist and
are linked. A missing record is a blocking condition, not a warning.

**Read-only before write.** Every new execution capability begins in read-only
mode. Write execution is a separately governed capability that requires its own
authorization gate. No write capability is introduced without first
demonstrating that the corresponding read-only path is sound.

**Human approval before irreversible action.** No commit, push, rollback, or
other irreversible operation occurs without explicit human sign-off. These
actions are never triggered automatically by agents, regardless of the outcome
of any automated check.

**Audit trails for every important decision.** Every invocation attempt, every
governance check, every authorization decision, and every review produces a
structured, machine-readable record. Records are linked into a complete
evidence chain. The chain cannot be partial: every upstream gate must be
satisfied before the downstream record can exist.

---

## 4. What PCAE Is Becoming

**A governed execution framework.** The core of PCAE is an 8-step execution
gate chain: task contract, authorization, preflight, runtime contract,
audit record, output capture, result review, and evidence record. Each gate
must pass before the next gate opens. No gate can be skipped.

**A prompt governance system.** Prompts submitted to AI agents are not
freeform inputs. They are governed artifacts: generated from templates,
rendered with verified parameters, validated against policy, and approved
before submission. Prompt governance ensures that what the agent is asked to
do reflects a human-approved plan.

**A runtime governance layer.** Not every AI runtime is equally trustworthy
or equally sandboxed. PCAE evaluates each configured runtime for trust level,
sandbox compliance, and contract adherence before any invocation is eligible.
Runtime trust is not assumed; it is assessed.

**A multi-agent orchestration platform.** Engineering work often requires
more than one agent, more than one capability, and more than one pass.
PCAE governs multi-agent workflows: agent selection is policy-declared and
capability-matched, handoffs are governed by session continuity, and
orchestration recommendations are advisory — the human user remains
authoritative.

**An autonomous engineering control plane.** The long-term target is a
platform capable of governing the full autonomous engineering loop: roadmap
generation, prompt authorship, execution, review, and commit — all subject
to human approval gates at every consequential step. This is a future state.
The current implementation builds the infrastructure that makes it safe to
reach.

---

## 5. Long-Term Direction

The roadmap advances in deliberate phases. Each phase demonstrates governance
soundness before the next phase introduces new execution capability. No phase
skips a gate.

**Governed read-only runtime invocation (Phase 49A and beyond).** The
invocation execution gate conditionally clears `execution_allowed` when all
8 lifecycle gates pass. This is the first phase in which a runtime is actually
invoked — read-only, sandboxed, and preceded by a complete evidence record.

**Multi-agent read-only execution.** Extend the read-only pilot to multi-agent
workflows. Validate orchestration handoff under governance constraints. Confirm
that session continuity, capability matching, and advisory recommendations
behave correctly across agent boundaries.

**Controlled write execution.** Introduce write execution with explicit rollback
planning as a precondition. A write invocation requires a pre-declared rollback
artifact. The rollback path is validated before the write gate opens.

**Governed commit and push.** Commit and push operations become governed
actions: subject to task contract scope, human approval sign-off, and
structured audit records. No agent triggers a commit or push automatically.

**Autonomous roadmap and prompt generation.** PCAE generates governed
roadmap proposals and prompt artifacts autonomously, subject to human approval
before any generated artifact is used for execution. Generation is not
execution.

**Evidence-based software evolution.** The terminal state of the platform is
one in which every change to a governed repository is traceable to a complete
evidence record: the original request, the human authorization, the preflight
state, the runtime trust assessment, the captured output, the review, and
the final repository state. No change lacks provenance.

The roadmap also includes **48X.T Parallel Test Execution Standardization**:
standardize `pytest-xdist` across CI and enforce parallel-safe test isolation
as a foundation for faster governed CI.

---

## 6. Non-Goals

PCAE is explicit about what it is not and will not become:

**Not an unrestricted coding agent.** PCAE does not invoke AI runtimes
without authorization, preflight, and evidence gates in place. Unrestricted
execution is not a target capability.

**Not an auto-commit bot.** PCAE never triggers a `git commit` automatically.
Commits require human confirmation and are never a side effect of any
governed pipeline step.

**Not an auto-push bot.** PCAE never triggers a `git push` automatically.
Push operations require explicit human sign-off. They are not triggered by
governance health checks, pipeline completions, or agent outputs.

**Not a replacement for human judgment.** PCAE produces recommendations,
readiness assessments, and advisory outputs. None of these override human
authority. The human engineer is the authoritative decision-maker for every
execution, approval, and rollback action.

**Not a system that bypasses governance.** No PCAE command, flag, or
configuration option provides a path around the governance gate chain.
Advisory outputs are advisory; enforcement outputs are enforced. There is no
`--skip-governance` flag.

---

## 7. Core Principles

**Human authority.** The human engineer is the authoritative decision-maker.
All agent actions, recommendations, and governance outputs are advisory until
a human approves them. This is enforced by architecture, not by convention.

**Traceability.** Every important decision in a governed workflow is traceable
to a structured record. The record includes who authorized it, what preflight
state existed, what the runtime produced, and how the output was reviewed.

**Auditability.** Every invocation attempt produces a structured audit record
regardless of outcome. Audit records are linked into an evidence chain.
The chain is machine-readable and complete.

**Reversibility.** Rollback paths are declared and validated before any write
execution begins. Irreversible actions require explicit human authorization.
Recovery is planned, not improvised.

**Explicit authorization.** No execution proceeds without a traceable
authorization artifact. Authorization is not implied by the presence of a
task contract or the passage of a preflight check. It is a discrete, recorded
decision.

**Runtime trust.** Runtime trust is assessed before invocation, not assumed.
Each runtime target is evaluated for sandbox compliance, contract adherence,
and trust level. A runtime that does not meet the trust bar is not eligible
for invocation.

**Least privilege.** Agent scope is constrained to the files and operations
defined in the active task contract. Operations outside that scope are
forbidden, not just discouraged.

**No hidden automation.** PCAE does not perform consequential actions as side
effects of other operations. Background tasks, deferred writes, implicit
rollbacks, and auto-repair logic are not part of the platform's execution
model. Every consequential action is explicit and human-initiated.

---

## 8. License and Community

PCAE is licensed under the Apache License 2.0.

Copyright 2026 Atila Madai

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy
of the License at:

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

See the [LICENSE](LICENSE) file for the full license text.

**Open collaboration, enterprise-grade governance.** The Apache 2.0 license
makes PCAE suitable for both open-source and enterprise adoption. The
governance model is designed to scale from individual contributors to
multi-team engineering organizations.

**Contributors must preserve governance guarantees.** Every contribution to
PCAE is held to the same governance standards the platform enforces in the
repos it governs. Contributions that weaken human authority, remove audit
trails, introduce hidden automation, or bypass the evidence chain fall outside
the accepted scope. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full
contribution guide.
