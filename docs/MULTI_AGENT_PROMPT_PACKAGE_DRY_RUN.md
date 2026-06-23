# Multi-Agent Prompt Package Dry-Run

## Purpose

Prepare draft prompt packages for the approved multi-agent route in MULTI-AGENT-DRY-RUN-001, including planner and documentation-reviewer prompt drafts, handoff expectations, output requirements, safety constraints, and capture requirements. This is a dry-run only — no prompts are sent, no backends are invoked, no task execution occurs.

## Scope

Draft prompt package creation for one approved route only. Both prompts are documentation artifacts describing what would be sent in a future governed invocation phase. No prompt is sent, no agent is invoked, no output is produced.

## Non-Goals

- Sending prompts to any backend.
- Invoking any agent or subagent.
- Task execution by any agent.
- Repository mutation by any agent.
- Output capture from any agent.
- Output intake or classification.
- Adoption of any agent output.
- Commit or push authorization.
- Source code or test changes.
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

## Approved Contract ID

| Field | Value |
|-------|-------|
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| contract_source | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |
| routing_approval_source | `docs/MULTI_AGENT_ROUTING_APPROVAL.md` |
| task_type | documentation_review |
| risk_level | medium |
| contract_status | draft |
| routing_authorized | true |
| backend_invocation_authorized | false |
| prompts_authorized | false |
| execution_authorized | false |

## Approved Route

| Role | Assigned To | Prompt Drafted |
|------|-------------|----------------|
| planner | claude-local | yes (below) |
| documentation_reviewer | claude-deepseek | yes (below) |
| adoption_reviewer | human/operator | N/A (no prompt needed) |
| commit_reviewer | human/operator | N/A (no prompt needed) |
| push_reviewer | human/operator | N/A (no prompt needed) |

## Prompt Package Status

| Field | Value |
|-------|-------|
| prompt_package_id | MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 |
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| status | draft_not_sent |
| prompts_sent | false |
| backends_invoked | false |

---

## Planner Prompt Draft

**Target agent:** claude-local
**Role:** planner
**Invocation mode:** future governed invocation with `--print` flag (stdout capture only)

### Draft Prompt Text

```
NOT SEND-AUTHORIZED — DRY-RUN ARTIFACT ONLY

You are acting as a PLANNER for a governed multi-agent documentation review
under PCAE contract MULTI-AGENT-DRY-RUN-001.

Your role: Plan the documentation review of PCAE's multi-agent capability
documentation (Phases 82A through 83D).

Task type: documentation_review
Risk level: medium
Your agent identity: claude-local (planner)
Reviewer identity: claude-deepseek (documentation_reviewer, separate agent)

You are reviewing these documents for consistency, clarity, and governance-boundary
accuracy:

- docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md (82A)
- docs/AGENT_IDENTITY_CAPABILITY_PROBE.md (82B)
- docs/SUBAGENT_DISCOVERY_CONTRACT.md (82C)
- docs/SUBAGENT_SAFETY_PROFILE.md (82D)
- docs/AGENT_ROUTING_DRY_RUN.md (82E)
- docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md (82F)
- docs/MULTI_AGENT_TASK_CONTRACT.md (83A)
- docs/AGENT_ASSIGNMENT_APPROVAL.md (83B)
- docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md (83C)
- docs/MULTI_AGENT_ROUTING_APPROVAL.md (83D)

INSTRUCTIONS:

1. Produce a planning summary that identifies:
   - The review scope (which documents, what to check).
   - Review focus areas (consistency, clarity, governance accuracy,
     cross-document references, terminology alignment).
   - Documentation risk notes (any areas where documents may contradict
     each other or leave governance boundaries ambiguous).
   - Handoff notes for the documentation reviewer (what to prioritize,
     what to look for, what the planner identified as highest concern).

2. Your output must be:
   - Markdown text only.
   - Structured with clear headings.
   - Suitable for handoff to the documentation reviewer.

3. You must NOT:
   - Edit any files.
   - Run any shell commands.
   - Generate patches or diffs.
   - Suggest commits or pushes.
   - Modify the repository in any way.
   - Auto-apply anything.
   - Access files outside the listed documents.

4. You must explicitly state:
   - Any limitations you encountered.
   - Any areas you could not fully assess.
   - Any assumptions you made.

REQUIRED OUTPUT SECTIONS:

- Planning Summary
- Review Focus Areas
- Documentation Risk Notes
- Handoff Notes for Documentation Reviewer
- Limitations

NOT SEND-AUTHORIZED — DRY-RUN ARTIFACT ONLY
```

### Planner Prompt Constraints

| Constraint | Value |
|-----------|-------|
| Output format | markdown only |
| File edits requested | none |
| Shell commands requested | none |
| Patches requested | none |
| Commits/pushes requested | none |
| Repo mutation requested | none |
| Invocation mode | `--print` (stdout only) |

---

## Documentation-Reviewer Prompt Draft

**Target agent:** claude-deepseek
**Role:** documentation_reviewer
**Invocation mode:** future governed invocation with `--print` flag (stdout capture only)
**Dependency:** receives planner output (handoff H1) before invocation

### Draft Prompt Text

```
NOT SEND-AUTHORIZED — DRY-RUN ARTIFACT ONLY

You are acting as a DOCUMENTATION REVIEWER for a governed multi-agent
documentation review under PCAE contract MULTI-AGENT-DRY-RUN-001.

Your role: Review PCAE's multi-agent capability documentation for consistency,
clarity, and governance-boundary accuracy.

Task type: documentation_review
Risk level: medium
Your agent identity: claude-deepseek (documentation_reviewer)
Planner identity: claude-local (planner, separate agent)

The planner (claude-local) has provided planning notes and review priorities.
Those notes are included below under PLANNER HANDOFF.

You are reviewing these documents:

- docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md (82A)
- docs/AGENT_IDENTITY_CAPABILITY_PROBE.md (82B)
- docs/SUBAGENT_DISCOVERY_CONTRACT.md (82C)
- docs/SUBAGENT_SAFETY_PROFILE.md (82D)
- docs/AGENT_ROUTING_DRY_RUN.md (82E)
- docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md (82F)
- docs/MULTI_AGENT_TASK_CONTRACT.md (83A)
- docs/AGENT_ASSIGNMENT_APPROVAL.md (83B)
- docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md (83C)
- docs/MULTI_AGENT_ROUTING_APPROVAL.md (83D)

PLANNER HANDOFF:
[Planner output would be inserted here after governed capture and intake]

INSTRUCTIONS:

1. Review the listed documents and produce findings in these areas:
   - Documentation consistency: Do documents reference each other correctly?
     Are phase numbers, artifact names, and cross-references accurate?
   - Governance boundary accuracy: Do all documents correctly state what is
     and is not authorized at each phase? Are authorization flags consistent
     across documents?
   - Clarity: Are documents clear about scope, non-goals, and safety
     constraints? Are there ambiguous statements?
   - Suggested improvements: Specific, actionable suggestions for improving
     documentation quality.
   - Adoption review notes: Summary of findings suitable for the human
     adoption reviewer to assess whether improvements should be adopted.

2. Your output must be:
   - Markdown text only.
   - Structured with clear headings.
   - Suitable for human adoption review.

3. You must NOT:
   - Edit any files.
   - Run any shell commands.
   - Generate patches or diffs.
   - Suggest commits or pushes.
   - Modify the repository in any way.
   - Auto-apply anything.
   - Access files outside the listed documents.

4. You must explicitly state:
   - Any limitations you encountered.
   - Any areas you could not fully assess.
   - Any assumptions you made.

REQUIRED OUTPUT SECTIONS:

- Documentation Consistency Findings
- Governance Boundary Findings
- Clarity Findings
- Suggested Improvements
- Adoption Review Notes
- Limitations

NOT SEND-AUTHORIZED — DRY-RUN ARTIFACT ONLY
```

### Documentation-Reviewer Prompt Constraints

| Constraint | Value |
|-----------|-------|
| Output format | markdown only |
| File edits requested | none |
| Shell commands requested | none |
| Patches requested | none |
| Commits/pushes requested | none |
| Repo mutation requested | none |
| Invocation mode | `--print` (stdout only) |
| Dependency | planner output (handoff H1) |

---

## Handoff Model

| Handoff | From | To | Artifact | Approval | Status |
|---------|------|----|----------|----------|--------|
| H1 | planner (claude-local) | documentation_reviewer (claude-deepseek) | Planning summary + handoff notes | Required | not_executed |
| H2 | documentation_reviewer (claude-deepseek) | adoption_reviewer (human/operator) | Review findings | Required | not_executed |
| H3 | adoption_reviewer (human/operator) | commit_reviewer (human/operator) | Adoption decision | Required | not_executed |
| H4 | commit_reviewer (human/operator) | push_reviewer (human/operator) | Commit confirmation | Required | not_executed |

No handoff has been executed. All handoffs are documented for future governed phases.

## Expected Planner Output

| Section | Description |
|---------|-------------|
| planning_summary | Scope and structure of the documentation review |
| review_focus_areas | What aspects to prioritize (consistency, clarity, governance accuracy) |
| documentation_risk_notes | Areas where documents may contradict or leave boundaries ambiguous |
| handoff_notes_for_documentation_reviewer | Priorities and concerns for the reviewer |
| limitations | What the planner could not fully assess |

## Expected Documentation-Reviewer Output

| Section | Description |
|---------|-------------|
| documentation_consistency_findings | Cross-reference accuracy, phase number correctness |
| governance_boundary_findings | Authorization flag consistency, scope statement accuracy |
| clarity_findings | Ambiguous statements, unclear non-goals |
| suggested_improvements | Specific, actionable improvement suggestions |
| adoption_review_notes | Summary suitable for human adoption reviewer |
| limitations | What the reviewer could not fully assess |

## Forbidden Outputs

The following outputs are forbidden from both planner and documentation-reviewer:

| Forbidden Output | Reason |
|-----------------|--------|
| Patches or diffs | Agents may not produce direct file modifications |
| Direct file edits | Agents may not modify the repository |
| Shell commands | Agents may not execute shell commands |
| Commit messages for execution | Agents may not commit |
| Push instructions | Agents may not push |
| Secret requests | No secret or credential access |
| Policy bypass instructions | No governance bypass |
| Hook bypass instructions | No hook bypass |
| Force-push instructions | Force push is unconditionally forbidden |

## File / Context Scope

### Allowed Future Context Files

- `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md`
- `docs/AGENT_IDENTITY_CAPABILITY_PROBE.md`
- `docs/SUBAGENT_DISCOVERY_CONTRACT.md`
- `docs/SUBAGENT_SAFETY_PROFILE.md`
- `docs/AGENT_ROUTING_DRY_RUN.md`
- `docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md`
- `docs/MULTI_AGENT_TASK_CONTRACT.md`
- `docs/AGENT_ASSIGNMENT_APPROVAL.md`
- `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md`
- `docs/MULTI_AGENT_ROUTING_APPROVAL.md`

### Forbidden Future Context / Files

- `src/**`
- `tests/**`
- `.pcae/**`
- `.githooks/**`
- `docs/REAL_CAPTURED_TASKS.md`
- `pyproject.toml`

## Prompt Capture Requirements

For any future invocation under this prompt package:

1. The exact prompt text sent must be captured and logged before sending.
2. No unlogged prompts are permitted.
3. Prompt content must be reviewed for scope compliance before sending.
4. The captured prompt must match the draft in this artifact (or a reviewed revision).
5. Prompt capture applies to both planner and documentation-reviewer invocations.

## Mutation Guard Requirements

For any future invocation under this prompt package:

1. Pre-invocation git status must be captured.
2. Post-invocation git status must be compared.
3. Unexpected mutations trigger quarantine and block adoption.
4. Mutation guard is required for both planner and documentation-reviewer invocations.
5. Agents are invoked with `--print` flag to minimize mutation risk.

## Output Capture Requirements

For any future invocation under this prompt package:

1. All stdout and stderr must be captured to files.
2. Return code must be recorded.
3. Capture must include byte count, line count, and SHA256 hash.
4. Captured output is not applied, adopted, or staged — it is held for intake.

## Output Intake Requirements

For any future agent output under this prompt package:

1. All output must go through intake classification.
2. Intake must verify output matches expected sections.
3. Content safety scan is required (no secrets, no bypass instructions, no force-push).
4. No auto-apply of any agent output.
5. Output must be reviewed by a human before any adoption consideration.

## Human Review Requirements

| Review Point | Required | Who |
|-------------|----------|-----|
| Prompt review before send | yes | human/operator |
| Planner output review | yes | human/operator |
| Handoff review (H1) | yes | human/operator |
| Documentation-reviewer output review | yes | human/operator |
| Adoption review (H2) | yes | human/operator |
| Commit review (H3) | yes | human/operator |
| Push review (H4) | yes | human/operator |

## Adoption / Commit / Push Boundaries

| Boundary | Required | Who | Authorized in 83E |
|----------|----------|-----|-------------------|
| Adoption review | yes | human/operator | no |
| Adoption approval | yes | human/operator | no |
| Adoption execution | yes | human/operator | no |
| Commit approval | yes | human/operator | no |
| Commit execution | yes | governed PCAE | no |
| Push approval | yes | human/operator | no |
| Push execution | yes | governed pcae push | no |

No adoption, commit, or push boundary is weakened or bypassed by this prompt package.

## Validation Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | Contract ID is MULTI-AGENT-DRY-RUN-001 | PASS |
| 2 | Routing approval exists (83D) | PASS |
| 3 | Routing is authorized | PASS |
| 4 | Backend invocation is not authorized | PASS |
| 5 | Prompts are not authorized to be sent | PASS |
| 6 | Execution is not authorized | PASS |
| 7 | Planner prompt is bound to claude-local | PASS |
| 8 | Documentation-reviewer prompt is bound to claude-deepseek | PASS |
| 9 | Planner and reviewer are distinct agents | PASS |
| 10 | Human/operator remains adoption/commit/push reviewer | PASS |
| 11 | No prompt asks for source changes | PASS |
| 12 | No prompt asks for test changes | PASS |
| 13 | No prompt asks for shell execution | PASS |
| 14 | No prompt asks for repo mutation | PASS |
| 15 | No prompt asks for patch generation | PASS |
| 16 | No prompt asks for adoption, commit, or push | PASS |
| 17 | Prompt package is marked draft_not_sent | PASS |
| 18 | Future prompt sending requires separate approval | PASS |
| 19 | Future output requires capture and intake | PASS |
| 20 | Future adoption/commit/push remain separately governed | PASS |

**Validation: 20/20 checks passed.**

## Authorization Flags

| Flag | Value |
|------|-------|
| prompt_package_created | true |
| routing_authorized | true |
| backend_invocation_authorized | false |
| subagent_invocation_authorized | false |
| prompts_authorized | false |
| prompts_sent | false |
| execution_authorized | false |
| repo_mutation_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

## Blockers / Warnings

**Blockers:** none for this prompt package dry-run.

**Warnings:**
- Prompt package is draft_not_sent and does not authorize sending.
- Future prompt sending requires a separate prompt/invocation approval phase.
- Planner output must be captured and reviewed before it can be handed off to the documentation reviewer.
- Documentation-reviewer prompt depends on planner output (handoff H1); the reviewer cannot be invoked before the planner completes.
- claude-kimi, codex, subagents, and unknown agents remain blocked from all routing.

## Dry-Run Outcome

| Field | Value |
|-------|-------|
| multi_agent_prompt_package_dry_run_status | created |
| prompt_package_status | draft_not_sent |
| validation_result | valid_prompt_package_not_authorized_for_send |

## Safety Conclusion

- This is a draft prompt package only.
- Routing was previously approved (83D) but prompt sending was not authorized.
- No prompts were sent in Phase 83E.
- No backend or subagent was invoked.
- No task execution occurred.
- No repository mutation occurred by any agent.
- No adoption, commit, or push is authorized.
- Future prompt sending requires a separate prompt/invocation approval phase.

## Recommended Next Phase

**83F — Multi-Agent Prompt/Invocation Approval**

83F should approve whether the prompt package may be sent to the approved agents, establishing the invocation approval boundary, but should still avoid execution unless explicitly scoped.
