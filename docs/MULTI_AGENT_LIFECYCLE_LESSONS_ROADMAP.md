# Multi-Agent Lifecycle Lessons / Roadmap Update

## Purpose

Summarize what the 83A–83L governed multi-agent lifecycle proved, what friction remains, what risks were exposed, and what hardening phases should come next.

## Scope

Documentation-only retrospective and forward roadmap. No implementation, no backend invocation, no adoption.

## Non-Goals

- Backend invocation or prompt sending.
- Source code or test changes.
- CLI command implementation.
- Lifecycle runner implementation.
- Adoption of any content.
- Modification of existing lifecycle artifacts.

---

## Lifecycle Summary

PCAE completed its first end-to-end governed multi-agent lifecycle across 12 phases (83A–83L) using contract MULTI-AGENT-DRY-RUN-001 and prompt package MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001.

| Metric | Value |
|--------|-------|
| Total phases | 12 (83A–83L) |
| Foundation artifacts (82A–82F) | 6 |
| Lifecycle artifacts (83A–83K) | 11 |
| Verification artifact (83L) | 1 |
| Total artifacts | 18 |
| Agents invoked | 2 (claude-local, claude-deepseek) |
| Agents blocked | 4 (claude-kimi, codex, subagents, unknown) |
| Backend invocations | 2 (one per agent, 83G only) |
| Findings produced | 11 (7 planner + reviewer additions) |
| Adoption candidates executed | 3 |
| Items deferred | 4 |
| Items rejected | 4 |
| Target files modified | 2 |
| Total lines changed | 4 (2 changed + 2 added) |
| Source/test/README changes | 0 |
| Governance violations | 0 |

---

## What the 83A–83L Lifecycle Proved

### 1. Multi-Agent Task Contract Modeling Works

PCAE can define formal multi-agent contracts with role assignments, allowed/forbidden operations, file scope, handoff points, and approval boundaries. The contract model (83A) was instantiated as a dry-run (83C) and carried through the full lifecycle without semantic drift.

### 2. Governed Agent Assignment and Routing Works

Agent assignments can be approved (83B) and routing can be authorized (83D) as separate governance steps, preventing any agent from being invoked without explicit approval of both *who* does *what* and *how* they are reached.

### 3. Prompt Package Dry-Run Works

Prompt packages can be prepared, reviewed, and validated (83E) before any backend is invoked, giving the operator a chance to inspect and approve the exact text that will be sent.

### 4. Prompt/Invocation Approval as a Separate Gate Works

Separating prompt/invocation approval (83F) from the prompt package itself creates a clear authorization boundary: the prompt exists but cannot be sent until explicitly approved.

### 5. Real Multi-Agent Prompt Send/Capture Works

PCAE successfully sent approved prompts to two distinct backends (claude-local and claude-deepseek) in 83G, captured stdout/stderr with metadata (lines, bytes, SHA256), and verified no repository mutation via pre/post git status comparison. The `--print` mode invocation kept agents read-only.

### 6. Multi-Agent Output Intake/Classification Works

Captured outputs can be systematically intaked (83H) with prompt adherence checks (14/14), safety checks (12/12), contract fit checks (8/8), and cross-output consistency checks (4/4). The intake process classifies outputs before any adoption consideration.

### 7. Multi-Agent Handoff Works

The planner output was successfully included as handoff context in the reviewer prompt (83G). The reviewer explicitly referenced and confirmed the planner's findings, demonstrating that the two-agent pipeline produces coherent, complementary analysis.

### 8. Adoption Review/Approval/Execution Separation Works

The three-step adoption pipeline (review 83I → approval 83J → execution 83K) preserves human decision authority at each stage. The review identifies candidates, the approval binds them to exact scopes, and the execution applies only what was approved. No backend output was adopted without explicit human governance.

### 9. Boundary Discipline Is Maintainable

Across 12 phases, all governance boundaries were preserved: no unauthorized invocations, no raw push, no force push, role separation maintained, single-adoption-path maintained, and no-auto invariants maintained. The progressive authorization model (one flag at a time) prevented scope creep.

### 10. Lifecycle Verification Closes the Loop

The final verification (83L) confirmed all artifacts, all boundaries, and all authorization flags, providing a formal closure point for the lifecycle.

---

## What Remains Manual

| Area | Current State | Automation Opportunity |
|------|--------------|----------------------|
| Prompt extraction from dry-run artifacts | Manual copy from markdown | Schema-driven prompt package format |
| Prompt sending | Manual `claude --print` invocation | PCAE command with approval gate |
| stdout/stderr capture | Manual redirect to /tmp files | PCAE-managed capture directory |
| Capture metadata (lines, bytes, SHA256) | Manual shell commands | Automated capture metadata |
| Output intake classification | Manual document creation | Schema-driven intake checklist |
| Adoption candidate identification | Manual review of intake findings | Structured candidate schema |
| Adoption approval binding | Manual artifact creation | Schema-driven approval record |
| Adoption execution | Manual file edits | PCAE-guided edit with scope check |
| Lifecycle state tracking | Phase-by-phase documents | Lifecycle state machine |
| Deferred item tracking | Carried forward in text | Structured deferred item tracker |

---

## What Remains Risky

### Risk: Prompt Modification Without Re-Approval

The current process relies on human discipline to send the exact approved prompt. There is no machine-enforced check that the sent prompt matches the approved package. A schema-driven prompt package with hash verification would close this gap.

### Risk: Capture Path Volatility

Captured outputs are stored in `/tmp`, which is volatile. If the machine reboots between capture and intake, outputs are lost. A PCAE-managed capture directory with persistence policy would mitigate this.

### Risk: Handoff Content Injection

The planner output is inserted into the reviewer prompt as raw text. A malicious or confused planner output could inject instructions that change the reviewer's behavior. Structured handoff with content boundaries would reduce this risk.

### Risk: Stale Agent Verification

Agent capability probes (82B) were performed at a point in time. Agent versions, availability, and behavior may change. There is no automated re-verification mechanism.

### Risk: Single-Session Lifecycle

The entire lifecycle ran in a small number of sessions. A long-running lifecycle spanning days or weeks would need session continuity guarantees that are not yet tested.

---

## Friction Observed

### 1. Phase Count

12 phases for a documentation review is governance-heavy. The approval/dry-run/approval pattern is correct for establishing trust but could be compressed for repeat workflows once the pattern is proven.

### 2. Artifact Volume

18 artifacts for one lifecycle creates a large documentation surface. Future lifecycles should consider consolidated artifacts where governance gates don't require separate documents.

### 3. Task File Management

Moving task files between `tasks/active/` and `tasks/completed/` required extra commits and occasional PCAE scope adjustments. A first-class task lifecycle command would reduce friction.

### 4. Prompt Package Extraction

Extracting prompts from markdown code blocks is error-prone. A structured prompt package format (JSON or YAML) would be more reliable.

### 5. NOT SEND-AUTHORIZED Markers

The markers served their purpose (preventing accidental send during dry-run) but required manual removal at send time. A prompt package schema could handle this transition automatically.

---

## Boundary Lessons

- **One authorization flag per phase** is the right granularity for establishing trust. It prevented scope creep and made each phase's authority clear.
- **Explicit "what this does NOT authorize" sections** are essential. They prevented misinterpretation of routing_authorized, prompts_authorized, and adoption_authorized.
- **Human/operator as adoption/commit/push reviewer** is non-negotiable. No agent should own these decisions.
- **Blocked agents must remain blocked** unless a governed discovery/verification phase clears them.

## Agent-Routing Lessons

- **Two-agent routing with handoff** worked well for documentation review. The planner/reviewer split produced complementary analysis.
- **Identity separation** (claude-local vs claude-deepseek) was maintained throughout. No identity confusion occurred.
- **`--print` mode** was effective at preventing repo mutation during invocation.

## Prompt-Package Lessons

- **Dry-run prompt packages** gave the operator a chance to review exact prompt text before approval.
- **Separate approval for the package vs. sending** created a useful checkpoint.
- **NOT SEND-AUTHORIZED markers** were effective but should be schema-managed.

## Capture/Intake Lessons

- **SHA256 hashing of captured output** provided tamper-evidence between capture and intake.
- **Mutation guard (pre/post git status)** detected no mutations — `--print` mode worked.
- **Cross-output consistency checks** confirmed the handoff pipeline worked as designed.

## Adoption Lessons

- **Three-step adoption (review → approval → execution)** prevented any accidental application of backend output.
- **Scope-binding in approval** (exact target file, exact change type, forbidden changes) was essential.
- **Human-authored final edits** (not raw backend paste) maintained documentation quality.
- **4 lines changed across 2 files** is a modest but real outcome. The governance overhead was high relative to the change size, which is expected for a first lifecycle.

## Commit/Push Lessons

- **Governed `pcae push`** worked throughout. No raw or force pushes.
- **Explicit file paths in `git add`** prevented accidental inclusion of sensitive files.
- **Implementation + completion commit pattern** was consistent across all phases.

---

## Deferred Items Carried Forward

| ID | Finding | Origin | Target | Status |
|----|---------|--------|--------|--------|
| DF-1 | Stale 83A future phases table | RISK-2 / C-2 | `docs/MULTI_AGENT_TASK_CONTRACT.md` | deferred — update after 83-series stabilizes |
| DF-2 | Dual capability models (82A vs 82C) relationship | RISK-6 / C-6 | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` or `docs/SUBAGENT_DISCOVERY_CONTRACT.md` | deferred — documentation consolidation phase |
| DF-3 | `blocked` risk taxonomy back-reference | RISK-5 / C-5 | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` | deferred — documentation consolidation phase |
| DF-4 | Authorization flag standardization | G-1 / S-7 | Multiple docs (83B, 83C, 83D) | deferred — documentation consolidation phase |

These items are informational improvements, not governance blockers.

---

## Recommended Roadmap: 84-Series

| Phase | Name | Description | Priority |
|-------|------|-------------|----------|
| 84B | Multi-Agent Prompt Package Schema | Define a machine-readable schema for prompt packages (agents, roles, prompts, expected outputs, forbidden actions) | HIGH — foundation for automation |
| 84C | Multi-Agent Capture Metadata Schema | Define a schema for capture results (stdout/stderr paths, hashes, line/byte counts, mutation guard results) | HIGH — pairs with 84B |
| 84D | Multi-Agent Output Intake Schema | Define a schema for intake classification (section checks, safety checks, contract fit, cross-output consistency) | MEDIUM |
| 84E | Multi-Agent Adoption Candidate Schema | Define a schema for adoption candidates (finding, target, scope, approval status, execution status) | MEDIUM |
| 84F | Multi-Agent Lifecycle State Machine | Design a state machine for the multi-agent lifecycle (contract → route → package → invoke → capture → intake → review → approve → execute → verify → close) | HIGH — unifies the 12-phase pattern |
| 84G | Multi-Agent Lifecycle Command Dry-Run | Dry-run a PCAE command interface for multi-agent lifecycle management (status, next, run-gate equivalents) | MEDIUM |
| 84H | Multi-Agent Backend Invocation Guard Hardening | Harden the prompt-to-send pipeline: hash verification that sent prompt matches approved package | HIGH — closes the prompt modification risk |
| 84I | Multi-Agent Prompt Capture Storage Policy | Define persistent capture storage (PCAE-managed directory, retention, cleanup) to replace volatile /tmp | MEDIUM |
| 84J | Multi-Agent Deferred Item Tracker | Resolve DF-1 through DF-4 and establish a tracking mechanism for future deferred items | LOW |
| 84K | Multi-Agent Lessons README Summary | Add a compact multi-agent capability summary to README.md (documentation-only) | LOW |

### Prioritized Next Phase

**84B — Multi-Agent Prompt Package Schema**

Rationale: A schema for prompt packages should come before automating sending/capture, because it gives PCAE a stable machine-readable boundary for approved prompts, roles, agents, expected outputs, and forbidden actions. Without a schema, automation would have to parse markdown artifacts, which is fragile.

---

## Safety Invariants to Preserve

These invariants must hold across all future multi-agent phases:

1. No backend invocation without explicit approval.
2. No prompt sending without explicit approval.
3. No subagent invocation without discovery and approval.
4. No repo mutation without approved target scope.
5. No adoption without intake/review/approval.
6. No commit without governed commit path.
7. No push without governed push path.
8. No force push.
9. No raw git push.
10. No hook bypass normalization.
11. Blocked agents remain blocked until governed verification.
12. Human/operator owns adoption/commit/push decisions.
13. No auto-routing agents.
14. No auto-sending prompts.
15. No auto-adopting backend output.
16. No auto-committing adopted content.
17. No auto-pushing adopted content.

---

## Automation Opportunities

| Opportunity | Risk Without | Current State | Prerequisite |
|-------------|-------------|---------------|-------------|
| Schema-driven prompt packages | Prompt modification without re-approval | Manual markdown extraction | 84B |
| PCAE-managed capture directory | Lost captures on reboot | /tmp volatile storage | 84I |
| Hash-verified prompt sending | Prompt tampering | Human discipline | 84H |
| Structured intake checklists | Inconsistent classification | Manual document creation | 84D |
| Lifecycle state machine | Phase tracking drift | Document-driven phases | 84F |
| Deferred item tracking | Forgotten deferrals | Carried in text | 84J |

---

## Explicit Non-Recommendations

PCAE should **not** yet:

1. **Auto-route agents** — routing decisions require human judgment about agent suitability and risk.
2. **Auto-send prompts without approval** — prompt content must be reviewed before sending.
3. **Auto-run subagents** — subagent discovery has not been performed; unknown subagent behavior is a risk.
4. **Auto-adopt backend output** — backend output is advisory, not authoritative. Human review is required.
5. **Auto-commit adopted content** — commits must be governed.
6. **Auto-push adopted content** — pushes must use governed `pcae push`.
7. **Treat backend output as authoritative** — backend findings are suggestions that require human judgment.
8. **Collapse review/approval/execution phases** — the separation exists to prevent accidental adoption. It may be streamlined but not eliminated.
9. **Implement a non-dry-run lifecycle runner for multi-agent work** — the single-agent lifecycle runner is proven but multi-agent orchestration needs more design work.
10. **Invoke codex or claude-kimi** — codex is unverified for PCAE governance; claude-kimi is unavailable.

---

## Final Recommendation

The 83A–83L lifecycle successfully proved that PCAE can govern multi-agent work end-to-end with zero governance violations. The next priority is moving from document-driven artifacts to schema-driven artifacts (84B–84E), then designing the lifecycle state machine (84F) that would enable command-line orchestration of the proven pattern.

The governance overhead is intentionally high for a first lifecycle. As schemas and tooling mature, the phase count per lifecycle should decrease while preserving the same safety invariants.
