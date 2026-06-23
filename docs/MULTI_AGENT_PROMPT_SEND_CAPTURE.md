# Multi-Agent Prompt Send / Capture

## Purpose

Send the exact approved planner and documentation-reviewer prompts to the approved backends, capture stdout/stderr/return code/duration/hash, run mutation guard before and after each invocation, and hold captured outputs for future intake. No output is adopted, applied, staged, committed, or pushed.

## Scope

Governed prompt send and output capture only for two approved invocations under contract MULTI-AGENT-DRY-RUN-001. This is the first phase that actually invokes backends. Outputs are captured but not processed, classified, or adopted.

## Non-Goals

- Output intake or classification.
- Content safety scan of outputs.
- Adoption review.
- Repository modification based on backend output.
- Application of any suggestions.
- Commit or push authorization.
- Source code or test changes.
- Invocation of any non-approved agent.

## Input Artifacts

| Artifact | Phase | Path |
|----------|-------|------|
| Multi-Agent Contract Instance Dry-Run | 83C | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |
| Multi-Agent Routing Approval | 83D | `docs/MULTI_AGENT_ROUTING_APPROVAL.md` |
| Multi-Agent Prompt Package Dry-Run | 83E | `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` |
| Multi-Agent Prompt/Invocation Approval | 83F | `docs/MULTI_AGENT_PROMPT_INVOCATION_APPROVAL.md` |

## Approved Contract ID

| Field | Value |
|-------|-------|
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| task_type | documentation_review |

## Approved Prompt Package ID

| Field | Value |
|-------|-------|
| prompt_package_id | MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 |

## Approved Route

| Role | Agent | Backend Command | Invocation Mode |
|------|-------|----------------|-----------------|
| planner | claude-local | `claude` | `--print` |
| documentation_reviewer | claude-deepseek | `claude-deepseek` | `--print` |
| adoption_reviewer | human/operator | N/A | N/A |
| commit_reviewer | human/operator | N/A | N/A |
| push_reviewer | human/operator | N/A | N/A |

---

## Planner Invocation Metadata

| Field | Value |
|-------|-------|
| agent_id | claude-local |
| backend_command | `claude` |
| role | planner |
| prompt_source | Planner Prompt Draft from `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` |
| prompt_sent | true |
| invocation_mode | `--print` (stdout capture only) |
| return_code | 0 |
| timed_out | false |
| duration_seconds | 104 |
| stdout_path | `/tmp/pcae-83g-planner-stdout.txt` |
| stderr_path | `/tmp/pcae-83g-planner-stderr.txt` |
| stdout_line_count | 159 |
| stdout_byte_count | 11263 |
| stdout_sha256 | `7eea6c4c41c5f6eb24ce3d543ec6aaa2741c36a038167507ede4734c53dea492` |
| stderr_line_count | 1 |
| stderr_byte_count | 157 |
| stderr_sha256 | `e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0` |

### Planner Mutation Guard

| Check | Before | After | Match |
|-------|--------|-------|-------|
| git status --short | `?? tasks/active/83g-*` (untracked task file only) | `?? tasks/active/83g-*` (unchanged) | MATCH |
| git diff --name-only | (empty) | (empty) | MATCH |
| git diff --cached --name-only | (empty) | (empty) | MATCH |
| mutation_detected | false | — | — |

### Planner Output Summary

The planner produced a structured markdown planning summary with all 5 required sections:

- Planning Summary (review scope, 10-document inventory)
- Review Focus Areas (5 areas: cross-document consistency, governance boundary accuracy, terminology alignment, cross-document reference accuracy, clarity/completeness)
- Documentation Risk Notes (7 risk items: RISK-1 through RISK-7)
- Handoff Notes for Documentation Reviewer (priority order, what to look for, stable items)
- Limitations (5 stated limitations)

Key planner findings for intake review:
- RISK-1: `documentation_review` classified as `low` in 82E but `medium` in 83C/83D
- RISK-2: 83A future phases table is stale vs actual phases
- RISK-3: Typo "claude-deepseep" in 83B line 82
- RISK-4: 83C allowed files scope narrower than actual review set
- RISK-5: Risk taxonomy expansion (`blocked`) in 82D not back-referenced from 82A
- RISK-6: Dual capability models (82A vs 82C) without explicit relationship
- RISK-7: Mutation guard principle wording in 82D could be ambiguous

---

## Documentation-Reviewer Invocation Metadata

| Field | Value |
|-------|-------|
| agent_id | claude-deepseek |
| backend_command | `claude-deepseek` |
| role | documentation_reviewer |
| prompt_source | Documentation-Reviewer Prompt Draft from `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md` |
| prompt_sent | true |
| handoff_included | true (planner stdout inserted as PLANNER HANDOFF section) |
| invocation_mode | `--print` (stdout capture only) |
| return_code | 0 |
| timed_out | false |
| duration_seconds | 131 |
| stdout_path | `/tmp/pcae-83g-reviewer-stdout.txt` |
| stderr_path | `/tmp/pcae-83g-reviewer-stderr.txt` |
| stdout_line_count | 330 |
| stdout_byte_count | 20491 |
| stdout_sha256 | `f821b0e3771cc7763eb7725cdca6d10a8c2665766dea26f2862d1391aab064c3` |
| stderr_line_count | 1 |
| stderr_byte_count | 157 |
| stderr_sha256 | `e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0` |

### Reviewer Mutation Guard

| Check | Before | After | Match |
|-------|--------|-------|-------|
| git status --short | `?? tasks/active/83g-*` (untracked task file only) | `?? tasks/active/83g-*` (unchanged) | MATCH |
| git diff --name-only | (empty) | (empty) | MATCH |
| git diff --cached --name-only | (empty) | (empty) | MATCH |
| mutation_detected | false | — | — |

### Reviewer Output Summary

The documentation reviewer produced a structured markdown review with all 6 required sections:

- Documentation Consistency Findings
- Governance Boundary Findings
- Clarity Findings
- Suggested Improvements
- Adoption Review Notes
- Limitations

Full content review of these outputs belongs to Phase 83H (intake).

---

## stdout/stderr Metadata Summary

| Invocation | stdout lines | stdout bytes | stdout SHA256 | stderr lines | stderr bytes |
|-----------|-------------|-------------|---------------|-------------|-------------|
| planner (claude-local) | 159 | 11263 | `7eea6c4c...dea492` | 1 | 157 |
| reviewer (claude-deepseek) | 330 | 20491 | `f821b0e3...064c3` | 1 | 157 |

## Output Hash Metadata

| Output | SHA256 |
|--------|--------|
| planner stdout | `7eea6c4c41c5f6eb24ce3d543ec6aaa2741c36a038167507ede4734c53dea492` |
| planner stderr | `e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0` |
| reviewer stdout | `f821b0e3771cc7763eb7725cdca6d10a8c2665766dea26f2862d1391aab064c3` |
| reviewer stderr | `e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0` |

## Mutation Guard Results

| Field | Value |
|-------|-------|
| pre_planner_mutation | none |
| post_planner_mutation | none |
| planner_mutation_detected | false |
| pre_reviewer_mutation | none |
| post_reviewer_mutation | none |
| reviewer_mutation_detected | false |
| any_mutation_detected | false |
| reviewer_invocation_skipped_due_to_mutation | false |

## Prompt Send Validation

| # | Check | Result |
|---|-------|--------|
| 1 | Planner prompt matches approved draft (markers removed) | PASS |
| 2 | Reviewer prompt matches approved draft (markers removed, handoff inserted) | PASS |
| 3 | Planner sent to claude-local via `claude --print` only | PASS |
| 4 | Reviewer sent to claude-deepseek via `claude-deepseek --print` only | PASS |
| 5 | No additional prompts sent | PASS |
| 6 | No prompt modifications beyond marker removal and handoff insertion | PASS |
| 7 | No claude-kimi invocation | PASS |
| 8 | No codex invocation | PASS |
| 9 | No subagent invocation | PASS |
| 10 | No unknown agent invocation | PASS |

## Capture Validation

| # | Check | Result |
|---|-------|--------|
| 1 | Planner return code captured (0) | PASS |
| 2 | Planner stdout captured (159 lines, 11263 bytes) | PASS |
| 3 | Planner stderr captured (1 line, 157 bytes) | PASS |
| 4 | Planner stdout SHA256 recorded | PASS |
| 5 | Planner duration recorded (104s) | PASS |
| 6 | Reviewer return code captured (0) | PASS |
| 7 | Reviewer stdout captured (330 lines, 20491 bytes) | PASS |
| 8 | Reviewer stderr captured (1 line, 157 bytes) | PASS |
| 9 | Reviewer stdout SHA256 recorded | PASS |
| 10 | Reviewer duration recorded (131s) | PASS |
| 11 | Mutation guard before/after planner: no mutation | PASS |
| 12 | Mutation guard before/after reviewer: no mutation | PASS |
| 13 | No backend output applied to repo | PASS |
| 14 | No backend output adopted | PASS |
| 15 | No backend output staged | PASS |

## Blockers / Warnings

**Blockers:** none.

**Warnings:**
- Captured outputs are held for future intake (83H). They have not been classified, safety-scanned, or reviewed.
- Planner identified 7 documentation risk items that need intake review.
- Reviewer output needs full content review in intake phase.
- Output files are stored at `/tmp/pcae-83g-*` outside the repository; they are not persisted in git.

## Authorization Flags

| Flag | Value |
|------|-------|
| routing_authorized | true |
| backend_invocation_authorized | true |
| prompts_authorized | true |
| prompts_sent | true |
| backend_invocation_performed | true |
| subagent_invocation_performed | false |
| execution_authorized | false |
| repo_mutation_authorized | false |
| repo_mutation_detected | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

## Capture Outcome

| Field | Value |
|-------|-------|
| multi_agent_prompt_send_capture_status | captured |
| capture_outcome | multi_agent_outputs_captured_no_mutation |
| planner_capture_status | captured |
| reviewer_capture_status | captured |
| total_invocations | 2 |
| successful_invocations | 2 |
| failed_invocations | 0 |
| mutation_events | 0 |

## Safety Conclusion

- Both approved prompts were sent to the exact approved backends.
- Both invocations used `--print` mode (stdout capture only).
- Both invocations completed successfully (return code 0).
- Mutation guard detected no repository changes before or after either invocation.
- No backend output was applied, adopted, staged, committed, or pushed.
- No additional agents, subagents, or backends were invoked.
- No source code, tests, or docs/REAL_CAPTURED_TASKS.md were modified.
- Captured outputs are held at `/tmp/pcae-83g-*` for future intake.

## Recommended Next Phase

**83H — Multi-Agent Output Intake**

83H should perform intake classification and content safety scan on both captured outputs, verify they match expected sections, and determine whether findings are suitable for future human adoption review. No adoption, commit, or push in 83H.
