# Multi-Agent Prompt/Invocation Approval

## Purpose

Approve future prompt sending and backend invocation for the prepared prompt package MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 under contract MULTI-AGENT-DRY-RUN-001. This approval authorizes a future phase to send the exact approved prompts to the exact approved backends and capture their output. This approval does not send prompts, invoke backends, execute tasks, authorize adoption, commit, or push.

## Scope

Prompt/invocation approval only for two specific prompt drafts targeting two specific, distinct, proven backends for a documentation-review task. All later governance boundaries (execution, output intake, adoption, commit, push) are preserved.

## Non-Goals

- Sending prompts to any backend.
- Invoking any agent or subagent.
- Task execution by any agent.
- Repository mutation by any agent.
- Output capture or intake.
- Adoption of any agent output.
- Commit or push authorization.
- Source code or test changes.
- Subagent invocation or discovery probing.
- Prompt modification beyond the approved package.
- Implementation of prompt sender or CLI commands.

## Input Artifacts

| Artifact | Phase | Path |
|----------|-------|------|
| Agent Capability Registry Design | 82A | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` |
| Agent Identity Capability Probe | 82B | `docs/AGENT_IDENTITY_CAPABILITY_PROBE.md` |
| Subagent Discovery Contract | 82C | `docs/SUBAGENT_DISCOVERY_CONTRACT.md` |
| Subagent Safety Profile | 82D | `docs/SUBAGENT_SAFETY_PROFILE.md` |
| Agent Routing Dry-Run | 82E | `docs/AGENT_ROUTING_DRY_RUN.md` |
| Multi-Agent Task Split Dry-Run | 82F | `docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md` |
| Multi-Agent Task Contract Design | 83A | `docs/MULTI_AGENT_TASK_CONTRACT.md` |
| Agent Assignment Approval | 83B | `docs/AGENT_ASSIGNMENT_APPROVAL.md` |
| Multi-Agent Contract Instance Dry-Run | 83C | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |
| Multi-Agent Routing Approval | 83D | `docs/MULTI_AGENT_ROUTING_APPROVAL.md` |
| Multi-Agent Prompt Package Dry-Run | 83E | `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` |

## Approved Contract ID

| Field | Value |
|-------|-------|
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| contract_source | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |
| task_type | documentation_review |
| risk_level | medium |
| contract_status | draft |
| routing_approval_source | `docs/MULTI_AGENT_ROUTING_APPROVAL.md` |
| routing_authorized | true |

## Approved Prompt Package ID

| Field | Value |
|-------|-------|
| prompt_package_id | MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 |
| prompt_package_source | `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` |
| prompt_package_status | draft_not_sent |
| prompt_package_validation | 20/20 checks passed |

## Approved Future Invocation Route

| Role | Agent | Backend Command | Invocation Mode | Prompt Source |
|------|-------|----------------|-----------------|---------------|
| planner | claude-local | `claude` | `--print` (stdout capture) | Planner Prompt Draft (83E) |
| documentation_reviewer | claude-deepseek | `claude-deepseek` | `--print` (stdout capture) | Documentation-Reviewer Prompt Draft (83E) |
| adoption_reviewer | human/operator | N/A | N/A | N/A |
| commit_reviewer | human/operator | N/A | N/A | N/A |
| push_reviewer | human/operator | N/A | N/A | N/A |

## Approved Prompts

### Planner Prompt (claude-local)

The planner prompt draft documented in `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` under "Planner Prompt Draft" is approved for future sending to claude-local via `claude --print`.

Approved prompt properties:
- Requests planning summary, review focus areas, documentation risk notes, handoff notes, and limitations.
- Requests markdown-only output.
- Explicitly forbids file edits, shell commands, patches, commits, pushes, and repo mutation.
- Scoped to 10 documentation files (82A through 83D).
- Contains NOT SEND-AUTHORIZED markers that must be removed at governed send time.

### Documentation-Reviewer Prompt (claude-deepseek)

The documentation-reviewer prompt draft documented in `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` under "Documentation-Reviewer Prompt Draft" is approved for future sending to claude-deepseek via `claude-deepseek --print`.

Approved prompt properties:
- Requests consistency findings, governance boundary findings, clarity findings, suggested improvements, adoption review notes, and limitations.
- Requests markdown-only output.
- Explicitly forbids file edits, shell commands, patches, commits, pushes, and repo mutation.
- Scoped to the same 10 documentation files.
- Contains NOT SEND-AUTHORIZED markers that must be removed at governed send time.
- Depends on planner output (handoff H1); reviewer cannot be invoked before planner completes and planner output passes intake review.

## Forbidden Prompt Changes

The following changes to the approved prompts are forbidden without a new approval phase:

- Adding new prompts for additional agents.
- Changing the target agent for either prompt.
- Adding requests for file edits, shell commands, patches, commits, or pushes.
- Adding context files outside the approved 10 documents.
- Removing safety constraints from either prompt.
- Changing invocation mode from `--print` to interactive or file-writing mode.
- Any modification that would expand the scope beyond documentation review.

## Blocked Agents

| Agent | Status | Reason |
|-------|--------|--------|
| claude-kimi | blocked | Missing from PATH (82B probe) |
| codex | blocked | Available but unverified for PCAE governance (82B probe) |
| subagents | blocked | Discovery not performed (82C contract defined, probes not executed) |
| unknown agents | disabled | Disabled by default per registry policy (82A/82D) |

No blocked agent may receive prompts, be invoked, or produce output under this approval.

## Invocation Approval Checks

| # | Check | Result |
|---|-------|--------|
| 1 | Contract ID is MULTI-AGENT-DRY-RUN-001 | PASS |
| 2 | Prompt package ID is MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 | PASS |
| 3 | Prompt package status is draft_not_sent | PASS |
| 4 | Prompt package validation passed 20/20 checks | PASS |
| 5 | Routing is authorized (83D) | PASS |
| 6 | Backend invocation is not yet performed | PASS |
| 7 | Prompts have not yet been sent | PASS |
| 8 | Planner prompt is bound to claude-local | PASS |
| 9 | Documentation-reviewer prompt is bound to claude-deepseek | PASS |
| 10 | Planner and reviewer are distinct agents | PASS |
| 11 | Human/operator owns adoption/commit/push review | PASS |
| 12 | claude-kimi remains blocked (missing) | PASS |
| 13 | codex remains blocked (unverified) | PASS |
| 14 | subagents remain blocked (discovery pending) | PASS |
| 15 | unknown agents remain disabled | PASS |
| 16 | No prompt asks for source changes | PASS |
| 17 | No prompt asks for test changes | PASS |
| 18 | No prompt asks for shell execution | PASS |
| 19 | No prompt asks for repo mutation | PASS |
| 20 | No prompt asks for adoption, commit, or push | PASS |
| 21 | Future invocation requires prompt capture | PASS |
| 22 | Future invocation requires mutation guard | PASS |
| 23 | Future output requires output capture | PASS |
| 24 | Future output requires output intake before adoption | PASS |
| 25 | Adoption/commit/push remain separately governed | PASS |

**Validation: 25/25 checks passed.**

## Prompt Capture Requirements

For any future invocation under this approval:

1. The exact prompt text sent must be captured and logged before sending.
2. The NOT SEND-AUTHORIZED markers must be removed at governed send time only.
3. No unlogged prompts are permitted.
4. Prompt content must be verified to match the approved draft (with markers removed).
5. Prompt capture applies to both planner and documentation-reviewer invocations.

## Mutation Guard Requirements

For any future invocation under this approval:

1. Pre-invocation git status must be captured.
2. Post-invocation git status must be compared.
3. Unexpected mutations trigger quarantine and block all further processing.
4. Mutation guard is required for both planner and documentation-reviewer invocations.
5. Agents must be invoked with `--print` flag to minimize mutation risk.

## Output Capture Requirements

For any future invocation under this approval:

1. All stdout and stderr must be captured to files.
2. Return code must be recorded.
3. Capture must include byte count, line count, and SHA256 hash.
4. Captured output is not applied, adopted, or staged — it is held for intake.

## Output Intake Requirements

For any future agent output under this approval:

1. All output must go through intake classification before any use.
2. Intake must verify output matches expected sections.
3. Content safety scan is required (no secrets, no bypass instructions, no force-push).
4. No auto-apply of any agent output.
5. Output must be reviewed by a human before any adoption consideration.

## Human Review Requirements

| Review Point | Required | Who |
|-------------|----------|-----|
| Prompt verification before send | yes | human/operator |
| Planner output review | yes | human/operator |
| Handoff review (H1) | yes | human/operator |
| Documentation-reviewer output review | yes | human/operator |
| Adoption review (H2) | yes | human/operator |
| Commit review (H3) | yes | human/operator |
| Push review (H4) | yes | human/operator |

## Adoption / Commit / Push Boundaries

| Boundary | Required | Who | Authorized in 83F |
|----------|----------|-----|-------------------|
| Adoption review | yes | human/operator | no |
| Adoption approval | yes | human/operator | no |
| Adoption execution | yes | human/operator | no |
| Commit approval | yes | human/operator | no |
| Commit execution | yes | governed PCAE | no |
| Push approval | yes | human/operator | no |
| Push execution | yes | governed pcae push | no |

No adoption, commit, or push boundary is weakened or bypassed by this prompt/invocation approval.

## Authorization Flags

| Flag | Value |
|------|-------|
| prompt_invocation_approval_created | true |
| routing_authorized | true |
| backend_invocation_authorized | true |
| prompts_authorized | true |
| subagent_invocation_authorized | false |
| prompts_sent | false |
| backend_invocation_performed | false |
| execution_authorized | false |
| repo_mutation_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

### What backend_invocation_authorized=true and prompts_authorized=true Mean

- A future phase may send the exact approved prompts to the exact approved backends (claude-local and claude-deepseek).
- The future phase must use `--print` mode, capture all output, run mutation guard, and hold output for intake.
- The planner invocation must complete and its output must pass intake before the documentation-reviewer is invoked.

### What backend_invocation_authorized=true and prompts_authorized=true Do NOT Mean

- Phase 83F itself does not send prompts or invoke backends.
- No prompt modification is authorized without a new approval phase.
- No additional agents may be invoked.
- execution_authorized=false remains — agents may not execute tasks that modify the repository.
- repo_mutation_authorized=false remains — no repository changes by agents are permitted.
- adoption_authorized=false remains — no agent output may be adopted into the repository.
- commit_authorized=false and push_authorized=false remain — no commits or pushes are authorized beyond normal phase commits.

## Approval Outcome

| Field | Value |
|-------|-------|
| multi_agent_prompt_invocation_approval_status | approved |
| approval_outcome | approved_for_future_prompt_sending_only |

## Blockers / Warnings

**Blockers:** none for this prompt/invocation approval.

**Warnings:**
- This approval authorizes future prompt sending only; no prompts have been sent.
- The planner must be invoked before the documentation reviewer (handoff H1 dependency).
- Planner output must pass intake review before being included in the reviewer prompt.
- claude-kimi, codex, subagents, and unknown agents remain blocked from all invocation.
- Adoption, commit, and push remain unauthorized and require their own future approval phases.
- Any modification to the approved prompts requires a new approval phase.

## Safety Conclusion

- This is a prompt/invocation approval artifact only.
- Routing was previously approved (83D) and a prompt package was prepared (83E).
- No prompts were sent in Phase 83F.
- No backend or subagent was invoked in Phase 83F.
- No task execution occurred.
- No repository mutation occurred by any agent.
- No output was captured or adopted.
- No adoption, commit, or push is authorized.
- Future prompt sending requires mutation guard, prompt capture, output capture, and output intake.
- Future adoption/commit/push remain separately governed.

## Recommended Next Phase

**83G — Multi-Agent Prompt Send / Capture**

83G should send the approved planner prompt to claude-local, capture its output, run mutation guard, and hold output for intake. If planner output passes intake, 83G or a subsequent phase should send the approved documentation-reviewer prompt to claude-deepseek with the planner output as handoff context, capture its output, and hold for intake. No adoption, commit, or push in 83G.
