# PCAE Governance Handbook

**Policy Controlled Autonomous Execution**

*Version 1.0 — Phase 48X.6*

---

## 1. Introduction

PCAE is a governance-first framework. Governance is not a layer added on top
of the engineering workflow — it is the foundation from which every execution
capability is built. No runtime is invoked, no prompt is submitted, and no
file is modified by an agent until the governance infrastructure that controls
that action is in place and validated.

**Why governance exists.**

AI coding agents can produce consequential changes to real repositories: file
edits, commits, pushed branches, triggered CI pipelines. Without structural
controls, these changes can occur without explicit approval, without an audit
trail, and without a pre-declared path to recovery. PCAE exists to provide
those controls — not as guidelines for human engineers to follow, but as
machine-enforceable gates that block execution when preconditions are unmet.

The difference between a governance checklist and a governance gate is that
the gate cannot be skipped.

**Relationship to the PCAE vision.**

The governance model described in this handbook is the operational
implementation of the principles stated in [VISION.md](../../VISION.md):
governance before autonomy, evidence before execution, read-only before write,
human approval before irreversible action, and audit trails for every
important decision. Every section of this handbook maps to at least one of
those principles.

---

## 2. Governance Layers

PCAE governs AI-assisted engineering across eight domains. Each domain is
responsible for a distinct class of risk and produces structured artifacts
that gate the next domain downstream.

**Change Governance** controls which files an agent may modify and under what
task contract. Change scope is declared before work begins. Operations outside
the declared scope are forbidden, not merely discouraged. Architecture zone
dependency rules enforce that source changes respect the declared layer
hierarchy.

**Rollback Governance** requires that rollback strategies be declared and
validated before any write execution begins. A write invocation is not
eligible until a rollback artifact exists, is structurally valid, and has been
reviewed. Recovery is planned, not improvised.

**Prompt Governance** treats prompts as governed artifacts. Prompts are
generated from templates, rendered with verified parameters, validated against
policy, and approved before submission. The governed prompt lifecycle runs
from roadmap proposal through approval, canonical prompt authorship,
agent-specific adaptation, review, and human authorization.

**Execution Governance** owns the 8-step gate chain that every invocation must
traverse. Each step must pass before the next gate opens. No step can be
skipped or deferred. The chain is: invocation request, authorization
artifact, authorization validity, authorization expiry, runtime contract
enforcement, preflight validation, output capture readiness, and human
approval presence.

**Runtime Governance** evaluates each configured runtime target for trust
level, sandbox compliance, contract adherence, and execution history before
any invocation is eligible. Trust is assessed, not assumed. A runtime that
does not meet the trust bar is not eligible for invocation regardless of
whether all other gates pass.

**Multi-Agent Governance** orchestrates agent selection, capability matching,
and handoff sequencing across multi-agent workflows. Agent selection is
policy-declared using the `[orchestration]` and `[agents.*]` sections of
`.pcae/policy.toml`. Recommendations are advisory — the human user remains
authoritative. Session continuity is verified at every handoff.

**Audit Governance** produces structured, machine-readable records for every
invocation attempt regardless of outcome. Audit records link the invocation
request, the authorization enforcement result, the runtime contract
enforcement result, the preflight result, the result capture record, and the
human approval artifact.

**Evidence Governance** extends audit records into complete evidence chains.
An evidence record is the terminal artifact of a fully governed invocation: it
cannot exist unless every preceding gate was satisfied. In the current phase,
all evidence records carry `evidence_status=not_executed` because no runtime
has been invoked. This is the correct and expected state.

---

## 3. Human Authority Model

**Human approval requirements.** No execution proceeds without a traceable
human approval artifact. Human approval is a discrete, recorded decision — not
implied by the presence of a task contract, not implied by the passage of a
preflight check, and not triggered automatically by any governance pipeline
step. Every approval is explicit, documented, and linked to the invocation
record.

**Authorization requirements.** Before any invocation is eligible, an
`ExecutionAuthorizationArtifact` must exist and pass four checks: structural
validity, non-expiry, linkage to a valid invocation request, and explicit
human approval. Authorization is not a checkbox — it is a versioned, timestamped
artifact with a defined expiry window.

**Escalation paths.** When a governance gate reports a blocking condition,
the blocking reason is surfaced in structured output with explicit human
decision requirements. The human engineer decides whether to resolve the
blocker, defer the invocation, or abandon it. No gate resolves its own
blocker automatically.

**Authority boundaries.** Human authority is authoritative for every
execution, approval, and rollback decision. Agent recommendations, readiness
assessments, and advisory outputs do not override human judgment. PCAE does
not and will not provide a mechanism to delegate final authority to an agent.

---

## 4. Change Governance

**Modification controls.** The active task contract (stored in
`tasks/active/`) declares the set of allowed files, override-protected files,
and forbidden files for the current work item. `pcae check` enforces that
every source change falls within the declared scope. Changes to files outside
the allowed set are reported as violations with CI-safe non-zero exit codes.

**Review requirements.** Architecture zone dependency rules enforce layer
separation between core, commands, CLI, tests, and configuration zones.
`pcae check` reports zone violations alongside scope violations. Both classes
of violation must be resolved before a contribution is eligible for commit.

**Commit governance.** Commits are human-initiated operations. No PCAE
command triggers a commit automatically. Every governed commit must be
preceded by a passing `pcae check` and a passing test suite. Committing
without these checks is a governance violation.

**Push governance.** Push operations are human-initiated and require explicit
sign-off. No PCAE command triggers a push automatically. Push governance is a
planned capability (Phase 50A and beyond); the current implementation enforces
the precondition (no automatic push) without yet providing a formal push
authorization gate.

---

## 5. Rollback Governance

**Rollback planning.** Every write execution requires a pre-declared rollback
artifact. The rollback plan specifies the mechanism (git reset, file restore,
snapshot restore), the trigger conditions, and the responsible party. Rollback
planning is a precondition for write eligibility, not a response to failure.

**Rollback validation.** The rollback artifact is validated for structural
completeness before the write gate opens. An incomplete or missing rollback
artifact is a blocking condition. `pcae check` enforces that rollback
artifacts exist when write-phase task contracts are active.

**Rollback approval.** Rollback execution is a human-initiated action.
Automatic rollback — triggered by a governance check, a pipeline result, or
an agent output — is not part of the PCAE execution model. The human engineer
authorizes both the original write and any subsequent rollback.

**Rollback execution constraints.** In the current phase, write execution is
disabled (`execution_allowed=False` for all runtimes). Rollback execution
constraints are scaffolded and validated but not yet exercised against a live
write. The rollback governance design is validated before write execution is
introduced, which is the correct sequencing.

---

## 6. Prompt Governance

**Roadmap approval.** The governed prompt lifecycle begins with a
roadmap proposal. Proposals are reviewed against the active task contract and
governance policy. Approved proposals advance to canonical prompt authorship.
Unapproved proposals do not advance.

**Canonical prompts.** A canonical prompt is a parameterized, policy-validated
prompt template linked to an approved roadmap item. Canonical prompts are
the authoritative source of what an agent is asked to do. They are versioned,
linked to the authorizing human approval, and stored as governed artifacts.

**Agent-specific prompts.** Canonical prompts are adapted for specific agent
targets using `pcae prompt-render`. The rendering process substitutes
validated parameters, enforces policy constraints, and produces the final
prompt artifact that is submitted to the agent. Rendering is not execution:
it produces a governed artifact for human review before any submission.

**Prompt review.** Every rendered prompt artifact is subject to human review
before submission. Review confirms that the rendered output matches the
canonical prompt intent and that no rendering artifact introduces scope
creep or policy violations.

**Prompt authorization.** Prompt submission requires an authorization artifact
linked to the rendered prompt. Submission without authorization is a blocking
condition enforced by the execution governance gate chain.

---

## 7. Execution Governance

**Execution readiness.** Execution readiness is evaluated with
`pcae readonly-runtime-pilot`, which runs an 8-step lifecycle readiness gate
across all configured runtimes. A runtime must pass all 8 gates to be
considered eligible for invocation. In the current phase, all runtimes fail
at multiple gates; readiness is reported and blockers are surfaced without
any invocation occurring.

**Execution authorization.** The `ExecutionAuthorizationArtifact` is the
formal record that a human has approved an invocation. It must exist, be
structurally valid, be unexpired, and carry an explicit human approval field
set to `True`. Authorization is evaluated by
`pcae invocation-authorization-enforcement` before any invocation is eligible.

**Preflight validation.** The `ReadOnlyInvocationPreflight` record evaluates
sandbox conditions, timeout contracts, and output capture readiness
immediately before invocation. A preflight failure is a blocking condition.
In the current phase, `execution_allowed=False` in all preflight records.

**Execution pilots.** The controlled read-only invocation pilot
(`pcae readonly-runtime-pilot`) is the first execution-eligible surface in
the lifecycle. It evaluates the complete 8-step gate chain and reports
readiness without performing any invocation. Pilot execution — running an
actual runtime call — requires the invocation execution gate (Phase 49A) to
be implemented and all 8 gates to pass.

---

## 8. Runtime Governance

**Runtime contracts.** Each runtime target (codex-local, claude-local,
kimi-local) is governed by a runtime contract covering six areas:
invocation, output capture, writable scope, read-only scope, sandbox
isolation, and timeout enforcement. The contract specifies what the runtime
must do and what PCAE must verify before invoking it.

**Contract verification.** Runtime contract enforcement is evaluated with
`pcae runtime-contract-enforcement`. The enforcement check evaluates each
contract area and reports whether it is verified, partially verified, or
unverified. A runtime with unverified blocking contract areas is not eligible
for invocation.

**Runtime trust.** Trust levels are assigned by `pcae runtime-trust` based on
the runtime's contract verification status, sandbox confidence, timeout
confidence, output capture confidence, writable confidence, execution history,
and governance alignment. Three trust levels are defined:

- `trusted`: All contracts verified and live execution history confirms
  governance alignment.
- `partially_trusted`: Some contracts verified but gaps remain; no live
  execution history or unverified contract areas present.
- `untrusted`: Contracts unverified or installation unconfirmed; cannot be
  assigned execution authorization.

**Current runtime trust state (Phase 48X.6):**

| Runtime | Trust Level | Key Blockers |
|---|---|---|
| codex-local | `partially_trusted` | sandbox contract unverified, timeout contract unverified, no live execution history |
| claude-local | `partially_trusted` | sandbox contract unverified, timeout contract unverified, no live execution history |
| kimi-local | `untrusted` | installation not confirmed, all 6 contract areas unverified |

All three runtimes have `human_review_required=True` and
`execution_allowed=False`. No runtime is eligible for invocation in the
current phase.

**Runtime readiness.** Runtime readiness is a composite signal combining
trust level, contract enforcement status, preflight result, and the
authorization gate chain. A runtime must be at minimum `partially_trusted`
and must pass all 8 authorization gate chain steps to be considered eligible.
In the current phase, no runtime satisfies this composite requirement.

---

## 9. Audit and Evidence

**Audit trail.** Every invocation attempt — whether blocked or allowed —
produces an `InvocationAuditRecord`. The record links: the invocation request,
the authorization enforcement result, the runtime contract enforcement result,
the preflight result, the result capture record, and the human approval
artifact. Audit records are structured, machine-readable, and immutable once
written.

**Result capture.** Governed output capture (`InvocationResultCapture`)
specifies how the runtime's stdout, stderr, and metadata are captured,
structured, and persisted for review. Output capture configuration must be
verified as part of the preflight check before any invocation proceeds.
Unstructured or uncaptured output is a blocking preflight condition.

**Result review.** Captured output is reviewed through a formal workflow
(`pcae invocation-result-review`) before results are considered accepted.
Review covers per-stream quality assessment (stdout, stderr, metadata) and
a quality framework evaluation. Review status is recorded in the
`InvocationResultReviewRecord` and linked to the evidence record.

**Evidence model.** The `InvocationEvidenceRecord` is the terminal artifact
of a fully governed invocation. It extends the audit record with: the prompt
reference, the result review record, and a single `evidence_status` field
reflecting the completeness of the entire chain. The evidence chain integrity
guarantee is: no evidence record can exist unless every upstream gate was
satisfied. In the current phase, all evidence records carry
`evidence_status=not_executed` — the correct state before any runtime has
been invoked.

---

## 10. Current Safety State

As of Phase 48X.6, PCAE is in the controlled scaffolding phase of the
read-only invocation track. The following safety invariants are enforced
by architecture and are not configurable:

| Capability | Status | Mechanism |
|---|---|---|
| Runtime execution | **Disabled** | `execution_allowed=False` for all runtimes in all invocation commands |
| Prompt execution | **Disabled** | No PCAE command submits a prompt to any runtime |
| Write execution | **Disabled** | Write execution gate (Phase 50A) not yet implemented |
| Human review | **Required** | `human_review_required=True` for all invocation-related commands |
| Auto-commit | **Disabled** | No PCAE command triggers `git commit` automatically |
| Auto-push | **Disabled** | No PCAE command triggers `git push` automatically |

These are not warnings or recommendations — they are structural invariants.
No PCAE command, flag, or policy configuration overrides them in the current
phase.

**Invocation-related commands are scaffolds.** `pcae readonly-invocation`,
`pcae readonly-runtime-pilot`, `pcae invocation-audit`,
`pcae invocation-result-review`, `pcae invocation-evidence`, and
`pcae invocation-authorization-enforcement` all produce structured scaffolds
that evaluate readiness and surface blockers. None of them invoke a runtime,
submit a prompt, or modify repository files.

---

## 11. Governance Maturity

**Overall maturity.** The governance infrastructure is complete at the
scaffolding level. All eight governance domains have defined models,
CLI commands, and test coverage. No domain is missing its structural
foundation. Runtime execution is the next capability to be enabled, and it
requires the invocation execution gate (Phase 49A) to be implemented and
validated first.

**Major completed milestones:**

- Task contracts and policy checks (`pcae check`) — change governance enforced
- Architecture zone dependency enforcement — layer separation validated
- Rollback design, dry-run validation, and write pilot scaffold — rollback
  governance foundation complete
- Prompt generation, rendering, and preflight — prompt governance scaffolded
- 8-step invocation lifecycle — execution governance gate chain complete
- Runtime contract enforcement and trust assessment — runtime governance
  operational
- Multi-agent registry, orchestration policy, capability matrix, and advisory
  selection — multi-agent governance operational
- Invocation audit record, result capture, result review, evidence model —
  audit and evidence governance scaffolded
- Architecture Decision Records, architecture memory, and governance audit —
  architecture governance operational
- Session bootstrap, continuity packs, runtime snapshots — session governance
  operational
- Documentation program (commands, architecture, glossary, white paper,
  architecture diagrams, contributor guide, project vision) — complete

**Remaining milestones:**

- Phase 49A: Invocation execution gate — clear `execution_allowed` when all
  8 lifecycle gates pass; first live runtime invocation
- Phase 48X.T: Parallel test execution standardization — enforce
  `pytest-xdist` and parallel-safe test isolation across CI
- Phase 50A: Controlled write authorization — introduce write execution with
  rollback planning as a precondition
- Phase 51A: Goal-based planning — governed roadmap and prompt generation

---

## 12. Future Roadmap

The roadmap advances in deliberate phases. Each phase demonstrates governance
soundness before the next phase introduces new execution capability.

| Phase | Track | Description |
|---|---|---|
| 48X.T | Test infrastructure | Parallel Test Execution Standardization — standardize `pytest-xdist` across CI; enforce parallel-safe test isolation; foundation for faster governed CI |
| 49A | Execution gate | Multi-Agent Read-Only Pilot — implement the invocation execution gate that conditionally clears `execution_allowed`; first live governed read-only runtime invocation |
| 50A | Write authorization | Controlled Write Authorization — introduce write execution with explicit rollback planning as a precondition; no write without a validated rollback artifact |
| 51A | Planning | Goal-Based Planning — governed roadmap and prompt generation; proposals are artifacts subject to human approval before execution |

The sequencing is deliberate. No phase skips a gate. Evidence of governance
soundness at each phase is the precondition for the next phase beginning.

---

## 13. License

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

See the [LICENSE](../../LICENSE) file for the full license text.
