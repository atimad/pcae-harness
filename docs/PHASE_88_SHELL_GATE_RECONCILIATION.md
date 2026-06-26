# Phase 88O — Shell Gate Design Reconciliation

## 1. Purpose

Reconcile the Phase 87 shell gate architecture (`docs/PHASE_87_SHELL_GATE_ARCHITECTURE.md`)
with the concrete Phase 88 and Phase 88N preflight layer, permission broker reconciliation,
fast-green validation architecture, and policy-forbidden consistency work. Define how a future
shell gate should reason about shell commands, filesystem mutation, git operations, test
execution, raw push, backend invocation, PCAE lifecycle state, and scope classification —
without implementing any of these behaviors here.

This phase is **design reconciliation only**.

## 2. Scope

Phase 88O delivers:

- This design reconciliation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No source implementation changes. No new CLI commands. No new tests. No storage.
No backend invocations. No prompt sending. No capture, intake, adoption, or mutation.

## 3. Non-Goals

- Implementing the shell gate.
- Implementing shell command interception.
- Implementing shell wrappers or modifying shell configs.
- Implementing the permission broker.
- Adding persistent storage, cache, or `.pcae` state files.
- Modifying source files (`src/**`).
- Modifying test files (`tests/**`).
- Backend invocation, prompt sending, output capture, intake, adoption.
- Raw git push or force push.
- Implementing Phase 88O.1, 88P, or any phase beyond 88O.

## 4. Artifact Identity

```
shell_gate_reconciliation_name=phase_88_shell_gate_reconciliation
shell_gate_reconciliation_version=0.1
shell_gate_reconciliation_status=draft_documented
implementation_status=not_started
recommended_next_phase=88O.1_scope_match_consistency_or_88P_shell_gate_prototype
```

## 5. Starting Point from 87I and 88A–88N.6

### Phase 87 shell gate architecture (87I)

Phase 87I defined the shell gate architecture before any enforcement existed:

| Phase | Contribution |
|-------|-------------|
| 87C | 15 dry-run gate evaluators |
| 87D–87G | Scope, backend, mutation/adoption, commit/push gate evaluations |
| 87H | Permission broker architecture |
| 87I | Shell gate architecture (command taxonomy, decision model, threat model) |

All gates were dry-run only. No enforcement. No authorization.

### Phase 88 preflight layer (88A–88M)

| Phase | Contribution |
|-------|-------------|
| 88A | First enforced gate boundary (design/planning) |
| 88B | Scope preflight enforcement |
| 88C | Backend invocation preflight enforcement |
| 88D | Mutation/adoption preflight enforcement |
| 88E | Commit/push preflight enforcement |
| 88L/88L.1 | Task state reconciliation and finish robustness |
| 88M | Full preflight integration verification (57 tests) |
| 88N | Permission broker design reconciliation |
| 88N.1 | Task-finish tracked-file robustness |
| 88N.2 | Full-suite runtime optimization; `pcae doctor test-run` |
| 88N.3 | Scope preflight baseline repair |
| 88N.4 | Full-suite bottleneck elimination |
| 88N.5 | Fast-green validation architecture (1,792 tests / ~22s) |
| 88N.6 | Preflight policy-forbidden consistency repair |

The five explicit preflights (`scope_preflight`, `backend_preflight`,
`mutation_preflight`, `commit_preflight`, `push_preflight`) are implemented, tested,
and integration-verified. Policy-forbidden files (`README.md`,
`docs/REAL_CAPTURED_TASKS.md`, `docs/LINKEDIN_ARTICLE_DRAFT.md`) are consistently
enforced across all four scope evaluation entry points. The fast-green development gate
is established at ~22s. Full-suite baseline: 7,736 passed / 0 failed.

## 6. What is the Shell Gate?

The shell gate is a **future mediation layer** that observes proposed shell commands
before execution, classifies them by risk, applies PCAE governance policy, and
either allows, blocks, or routes them to human review — based on task contract scope,
active preflight evidence, health/check state, and PCAE lifecycle position.

The shell gate:

- Classifies every proposed shell command into a command category.
- Assigns a risk class to that category.
- Consults the active task contract, preflight evidence, and PCAE health state.
- Returns a decision with reason codes and audit evidence.
- Blocks or routes commands that exceed their classification threshold.
- Records decisions for audit purposes.
- Never executes commands itself.

## 7. What the Shell Gate Is Not

The shell gate is not:

- A command executor. It observes and classifies; it does not run commands.
- The permission broker. The broker decides policy in principle; the gate controls
  shell execution in practice. Both layers are needed.
- A replacement for the five explicit preflights. Those commands remain the
  pre-execution evidence layer. The gate consumes their output; it does not replace them.
- A replacement for task contracts. Task contracts remain authoritative for scope,
  allowed files, and forbidden files. The gate enforces them but does not define them.
- A replacement for `pcae health`, `pcae check`, `pcae doctor`, or `pcae push check`.
  The gate must not weaken any of those requirements.
- A replacement for human review. Human approval is evidence; the gate can route to
  it but must never treat it as automatic bypass.
- Persistent storage. The 88O design does not implement storage.

## 8. Relationship to Permission Broker

| Dimension | Permission Broker | Shell Gate |
|-----------|------------------|------------|
| Primary role | Decides whether an action is allowed in principle | Controls whether a shell command may execute |
| Input | Proposed action + gate evidence + task contract + human approval | Proposed shell command + broker decision + preflight evidence |
| Output | Allow/deny/review decision with reason codes | Execution decision with command class + risk class |
| Layer | Policy mediation | Execution mediation |
| Enforcement | Policy-level | Command-level |
| Dependency | Consumes preflight evidence | May consume broker decision |

The broker without the shell gate cannot prevent unsafe shell execution. The shell gate
without the broker lacks full governance context. Both are needed for complete mediated
execution. Neither replaces the other.

The shell gate must not treat broker absence as allow. A missing broker decision
produces `requires_more_evidence` or `blocked_by_missing_broker`, not allow.

## 9. Relationship to Explicit Preflight Commands

| Preflight | Command | Shell Gate Role |
|-----------|---------|-----------------|
| Scope preflight | `pcae scope-preflight` | Gate consumes scope evidence; scope denial is a blocking input |
| Backend preflight | `pcae backend-preflight` | Gate consumes backend evidence; denial blocks backend commands |
| Mutation/adoption preflight | `pcae mutation-preflight` | Gate consumes mutation evidence; denial blocks source/docs mutation |
| Commit preflight | `pcae commit-preflight` | Gate consumes commit evidence; denial blocks raw git commit |
| Push preflight | `pcae push-preflight` | Gate consumes push evidence; denial blocks raw git push |

Preflight outputs are evidence inputs to the shell gate decision, not authorization by
themselves. A preflight result of `requires_human_review` does not mean the gate should
allow the command — it means the gate should surface human review as a requirement.

The shell gate must not treat a preflight `allow` as full shell execution permission
without also checking task contract scope, health/check state, and command category.

## 10. Relationship to Task Contracts

Task contracts define:
- Allowed files (scope boundary)
- Forbidden files (explicit denials)
- Allowed zones (scope zones)
- Forbidden zones (scope zone denials)
- Mode (design, implementation, etc.)

The shell gate enforces task contract boundaries:
- Commands that write files outside the allowed-file set are blocked by scope.
- Commands that write to forbidden files are blocked by forbidden-file policy.
- Commands that mutate forbidden zones are blocked by zone policy.
- Policy-forbidden files (`_SPF_POLICY_FORBIDDEN_FILES`) are hard blocks regardless of
  task contract content — they must not be writable even if a task contract omits them.

The shell gate does not modify task contracts. Task contracts remain the authoritative
scope definition. The gate reads and enforces; it does not define.

## 11. How Shell Gate Treats No Active Task

When no task contract is active, the shell gate applies a conservative no-task policy:

| Command Category | No-Task Decision |
|-----------------|-----------------|
| `read_only_inspection` | `allow_read_only` (no mutation, no secret access) |
| `test_execution` | `requires_active_task` (test runs should be task-scoped) |
| `pcae_governed_lifecycle` | `allow_governed` (health, check, doctor are always safe) |
| `source_mutation` | `blocked_by_missing_task` |
| `docs_mutation` | `blocked_by_missing_task` |
| `filesystem_write` | `blocked_by_missing_task` |
| `raw_git_commit` | `blocked_by_missing_task` + `blocked_by_raw_git_commit` |
| `raw_git_push` | `blocked_by_missing_task` + `blocked_by_raw_git_push` |
| `force_push` | `blocked_by_force_push` (always, regardless of task state) |
| `backend_invocation` | `blocked_by_missing_task` |
| `prompt_send` | `blocked_by_missing_task` |
| `intake_adoption` | `blocked_by_missing_task` |
| `destructive_filesystem` | `blocked_by_missing_task` |
| `unknown` | `blocked_by_unknown_command` |

No active task must not be treated as an implicit allow for any mutating or
invocation command. Missing task is a governance gap, not a permission.

The existing preflight behavior where `no active task → blocked_by_missing_task_contract`
(scope/mutation/backend) or `unknown` (gate dry-run) confirms this boundary and the
shell gate must honor it.

## 12. Command Classification Taxonomy

The following taxonomy defines all command categories the shell gate must recognize.
Categories map directly to risk classes and default decision rules.

| Category | Examples | Risk Class |
|----------|----------|------------|
| `read_only_inspection` | `git status`, `git log`, `git diff`, `ls`, `cat`, `find`, `grep`, `pcae artifact-index`, `pcae project-state` | `low` |
| `test_execution` | `python -m pytest`, `pytest`, `python -m pytest -m fast_green`, `python -m pytest -n auto` | `medium` |
| `pcae_governed_lifecycle` | `pcae health`, `pcae check`, `pcae doctor`, `pcae task`, `pcae session`, `pcae push check` | `medium` |
| `pcae_governed_commit` | `pcae task finish --commit`, `pcae commit` | `high` |
| `pcae_governed_push` | `pcae push` | `high` |
| `raw_git_commit` | `git commit` (any form without pcae wrapper) | `high` |
| `raw_git_push` | `git push` (any form without pcae wrapper) | `critical` |
| `force_push` | `git push --force`, `git push -f`, `git push --force-with-lease` | `critical` |
| `git_history_rewrite` | `git rebase -i`, `git reset --hard`, `git commit --amend` (published), `git filter-branch` | `critical` |
| `destructive_filesystem` | `rm -rf`, `rm -f`, `git clean -f`, `git checkout --` | `high` |
| `filesystem_write` | Shell redirection (`>`, `>>`), `cp`, `mv`, `tee`, `write` | `high` |
| `source_mutation` | Any write to `src/**` | `high` |
| `test_mutation` | Any write to `tests/**` | `high` |
| `docs_mutation` | Any write to `docs/**` | `medium` |
| `policy_forbidden_file_mutation` | Any write to `README.md`, `docs/REAL_CAPTURED_TASKS.md`, `docs/LINKEDIN_ARTICLE_DRAFT.md` | `critical` |
| `backend_invocation` | `claude`, `codex`, `claude-deepseek`, subagent CLI commands | `critical` |
| `prompt_send` | Any command that pipes or sends a prompt to a backend | `critical` |
| `output_capture` | Commands that capture backend output to files | `high` |
| `intake_adoption` | `pcae intake`, `pcae adopt`, adoption-related commands | `critical` |
| `package_install` | `pip install`, `pip install -r`, `npm install`, `brew install` | `high` |
| `network_access` | `curl`, `wget`, `http`, `ssh`, direct API calls | `high` |
| `secret_access` | Reading from `.env`, environment variables containing secrets | `high` |
| `environment_mutation` | `export`, `unset`, modifying `.env` files, changing shell state | `high` |
| `unknown` | Any command not classified above | `unknown` |

**Unknown commands must never be treated as safe.** An unrecognized command class
always produces `blocked_by_unknown_command` or `requires_human_review`, never allow.

## 13. Decision Model

The shell gate produces exactly one decision per evaluated command. The following
decision values are defined:

| Decision | Meaning | Permits Execution |
|----------|---------|-------------------|
| `allow_read_only` | Read-only inspection; no mutation risk | yes (future) |
| `allow_governed` | PCAE-governed lifecycle command | yes (future) |
| `allow_test_execution` | Test execution with test-run preflight passed | yes (future) |
| `requires_active_task` | Command requires active task contract | no |
| `requires_preflight` | Relevant preflight command must pass first | no |
| `requires_human_review` | Human must explicitly approve | no (until approved) |
| `requires_more_evidence` | Evidence is missing or incomplete | no |
| `blocked_by_missing_task` | No active task contract | no |
| `blocked_by_scope` | Command writes files outside task scope | no |
| `blocked_by_policy_forbidden_file` | Command targets a policy-forbidden file | no |
| `blocked_by_raw_git_commit` | Raw `git commit` without pcae wrapper | no |
| `blocked_by_raw_git_push` | Raw `git push` without pcae wrapper | no |
| `blocked_by_force_push` | Force push (`--force` / `-f`) | no |
| `blocked_by_history_rewrite` | Destructive history rewrite | no |
| `blocked_by_destructive_filesystem` | Destructive filesystem command | no |
| `blocked_by_backend_policy` | Backend invocation without preflight + authorization | no |
| `blocked_by_prompt_policy` | Prompt send without preflight + authorization | no |
| `blocked_by_adoption_policy` | Intake/adoption without preflight + authorization | no |
| `blocked_by_test_run_lock` | Overlapping pytest process detected | no |
| `blocked_by_failed_health` | `pcae health` not healthy | no |
| `blocked_by_failed_check` | `pcae check` not passed | no |
| `blocked_by_failed_doctor` | `pcae doctor` reports inconsistency | no |
| `blocked_by_push_check` | `pcae push check` not passed | no |
| `blocked_by_unknown_command` | Command class could not be classified | no |
| `deny` | Explicit denial (catch-all) | no |
| `unknown` | Decision could not be determined; treated as deny | no |

`unknown` must never be treated as `allow_read_only`, `allow_governed`, or
`allow_test_execution`. Unknown decisions are treated as deny.

## 14. Policy: Raw Git Commit

Raw `git commit` (any form that bypasses the pcae-governed commit workflow) should
be blocked when the PCAE governed commit path is available.

Rationale: `pcae task finish --commit` runs the pre-commit hook which enforces
the active-task requirement, health checks, and governance invariants. Bypassing it
via raw `git commit` can produce ungoverned commits that the audit trail does not
record correctly.

Decision: `blocked_by_raw_git_commit`

Exception handling: If the operator explicitly requires raw git commit for a
well-documented reason (e.g., recovery from a broken hook), the shell gate must
surface `requires_human_review` with full reason codes rather than silently allowing.

Hook bypass (`--no-verify`) is a separate, always-blocked category. See §16.

## 15. Policy: Raw Git Push and Force Push

Raw `git push` and force push are must-never-repeat controls inherited from Phase 87:

| Command | Decision | Override |
|---------|----------|---------|
| `git push` (raw, any remote/branch) | `blocked_by_raw_git_push` | Never; must route through `pcae push` |
| `git push --force` | `blocked_by_force_push` | Never |
| `git push -f` | `blocked_by_force_push` | Never |
| `git push --force-with-lease` | `blocked_by_force_push` | Never |
| `git push --mirror` | `blocked_by_force_push` | Never |

The shell gate must not convert a human override into permission for force push.
Even if a human approves, the gate must return `blocked_by_force_push` and surface
the override request for operator-level escalation outside the gate.

## 16. Policy: Destructive Filesystem Commands

| Command | Decision |
|---------|---------|
| `rm -rf <path>` | `blocked_by_destructive_filesystem` unless narrowly pre-authorized |
| `rm -f <file>` | `requires_human_review` for governed paths; `blocked_by_scope` for task-forbidden paths |
| `git clean -f` | `blocked_by_destructive_filesystem` |
| `git clean -fd` | `blocked_by_destructive_filesystem` |
| `git checkout -- <file>` | `requires_human_review` (discards uncommitted changes) |
| `git reset --hard` | `blocked_by_history_rewrite` |

Default is deny. Narrow authorization requires:
1. Active task contract.
2. File not in forbidden set or policy-forbidden set.
3. Explicit human review approval recorded.

## 17. Policy: Shell Redirection and File Writes

Shell redirection that writes to files is classified as `filesystem_write` or the
more specific category if the target path is a source, test, docs, or policy-forbidden
file.

| Redirection | Examples | Decision |
|-------------|----------|---------|
| Write to `src/**` | `cmd > src/pcae/core/foo.py` | `blocked_by_scope` (unless in task allowed-files + preflight passed) |
| Write to `tests/**` | `cmd > tests/test_foo.py` | `blocked_by_scope` (unless in task allowed-files) |
| Write to policy-forbidden file | `cmd > README.md` | `blocked_by_policy_forbidden_file` |
| Write to task-allowed doc | `cmd > docs/PHASE_88_FOO.md` | `requires_preflight` |
| Write to arbitrary path | `cmd > /tmp/foo` | `requires_active_task` + scope check |
| Append to any governed file | `cmd >> docs/CHANGELOG.md` | `requires_preflight` |

Shell redirection must be classified as a file write, not read-only inspection.
A command that appears read-only but uses `>` or `>>` is a mutation command.

## 18. Policy: Package Installation and Environment Mutation

Package installation changes the runtime environment and may affect test outcomes,
dependency resolution, and reproducibility.

| Command | Decision |
|---------|---------|
| `pip install <pkg>` | `requires_human_review` |
| `pip install -r requirements.txt` | `requires_human_review` |
| `npm install` | `requires_human_review` |
| `brew install <pkg>` | `requires_human_review` |
| `export VAR=value` (in shell session) | `requires_active_task` for governed variables |
| Writing to `.env` files | `requires_human_review` |
| `unset VAR` | `requires_active_task` if VAR is governance-related |

Package installation is always `requires_human_review` because it mutates the
environment outside the task contract scope model. It may require additional
validation beyond fast-green.

## 19. Policy: Backend, Network, and API Commands

| Command Class | Examples | Decision |
|--------------|----------|---------|
| `backend_invocation` | `claude`, `codex`, `claude-deepseek` | `requires_preflight` + `requires_human_review` |
| `prompt_send` | Piping text to a backend CLI | `blocked_by_prompt_policy` without task + backend preflight |
| `network_access` | `curl`, `wget`, direct API calls | `requires_active_task` + `requires_human_review` |
| `output_capture` | Redirecting backend output to files | `requires_preflight` (scope + backend) |
| `intake_adoption` | `pcae intake`, `pcae adopt` | `blocked_by_adoption_policy` without full governance chain |

Backend invocation is a critical-risk category. It requires:
1. Active task contract.
2. Backend preflight passed (`pcae backend-preflight`).
3. Scope preflight passed for any files that will be written.
4. Explicit human review approval.

The shell gate must not treat backend preflight alone as authorization to invoke a
backend. Backend preflight confirms that invocation is *not blocked by known policy* —
it does not grant execution permission.

## 20. Policy: Prompt/Capture/Intake/Adoption Commands

These categories remain gated by the existing governance chain established in 88C–88M:

| Stage | Gate | Shell Gate Role |
|-------|------|-----------------|
| Prompt send | Backend preflight + human review | Blocks without preflight evidence |
| Output capture | Scope preflight | Blocks out-of-scope capture targets |
| Intake | Mutation preflight + scope preflight | Blocks unapproved intake targets |
| Adoption | Mutation preflight + scope preflight + human review | Hard block without full chain |

The shell gate must never authorize intake/adoption without the complete governance
chain. Adoption without explicit human review and both preflights is
`blocked_by_adoption_policy`.

## 21. Policy: Test Execution and Test-Run Preflight

Test execution is `medium`-risk but requires coordination to avoid overlapping runs.

### Test-run preflight requirement

Before any expensive xdist test execution, the shell gate should require test-run
preflight (`pcae doctor test-run --json`) to confirm `clear_to_run=true`.

| Condition | Decision |
|-----------|---------|
| `clear_to_run=true`, fast-green tier | `allow_test_execution` |
| `clear_to_run=true`, quick/full tier | `allow_test_execution` |
| `clear_to_run=false` (active pytest process) | `blocked_by_test_run_lock` |
| No active task, any tier | `requires_active_task` |

The shell gate must not kill conflicting pytest processes automatically. If
`clear_to_run=false`, the gate blocks and surfaces the active process count.
Process termination requires explicit human review.

### Tier-aware validation policy

The shell gate integrates with the three validation tiers defined in Phase 88N.5:

| Tier | Invocation | Shell Gate Policy |
|------|-----------|------------------|
| targeted | `python -m pytest -k <phase_id>` | Low-risk change smoke; no test-run preflight required |
| fast-green | `python -m pytest -m "fast_green" -n auto` | Normal development gate; prefer over quick/full |
| quick | `python -m pytest -m "not slow and not phase_closure" -n auto` | Pre-push confidence; no test-run preflight required |
| full | `python -m pytest -n auto` | Requires `pcae doctor test-run --json` first |

The shell gate does not require full-suite validation for every phase. The tier
selection is driven by change risk:

- Targeted + fast-green: low/medium-risk changes (single command path, no shared infrastructure)
- Quick tier: broader confidence, pre-push, when fast-green passes but broader coverage wanted
- Full suite: shared governance source changes, test-infrastructure changes, release gating

## 22. Policy: Full-Suite and Fast-Green Integration

The shell gate recognizes the validation tier model and must not downgrade it.

Specifically:
- The gate must not block a fast-green run when `clear_to_run=true`.
- The gate must not substitute fast-green for a full-suite run when full suite is required.
- Full suite is required for: changes to `src/pcae/core/`, test infrastructure
  (`conftest.py`, `pyproject.toml` markers, fixtures), `.githooks/`, and
  shared governance files.
- Fast-green is sufficient for: design-only phases (like 88O), narrow single-command
  changes, and documentation updates.
- The shell gate must preserve the fast-green / quick / full tier model; it must not
  collapse it to a single required tier.

## 23. Policy: Policy-Forbidden Files

The three policy-forbidden files (`README.md`, `docs/REAL_CAPTURED_TASKS.md`,
`docs/LINKEDIN_ARTICLE_DRAFT.md`) defined in `_SPF_POLICY_FORBIDDEN_FILES` are
hard blocks in all mutation contexts.

| Context | Decision |
|---------|---------|
| Any command that writes to a policy-forbidden file | `blocked_by_policy_forbidden_file` |
| Task contract that lists a policy-forbidden file as allowed | Gate overrides: still `blocked_by_policy_forbidden_file` |
| Backend output captured to a policy-forbidden file | `blocked_by_policy_forbidden_file` |
| Shell redirection writing to a policy-forbidden file | `blocked_by_policy_forbidden_file` |

Policy-forbidden file enforcement must be independent of task contract content.
A task contract that omits a policy-forbidden file from its forbidden-file list does not
make that file writable. The 88N.6 baseline inconsistency — where the 88N.4 task
happened to list those files and masked the gap — must not recur at the shell gate level.

The shell gate must enforce policy-forbidden files as absolute hard blocks, not as
a default that task contracts can override.

## 24. Policy: Human Approval and Accepted Risk

Human approval is **evidence**, not bypass.

| Principle | Implication |
|-----------|-------------|
| Human approval is evidence | The gate records that a human approved; it does not remove blocking conditions |
| Human approval does not un-block must-never-repeat controls | Force push remains blocked even if a human approves |
| Accepted risk is not mitigation | A risk logged as `accepted` in the risk register does not make the underlying command safe |
| Human review required ≠ human review received | `requires_human_review` is a gate output, not a gate outcome |
| Override requires escalation | Must-never-repeat overrides require operator-level escalation outside the gate mechanism |

The gate must not convert human approval into automatic allow for blocked categories.
A human approving a force push at the gate level must produce a record with full reason
codes and the explicit override request — it does not change the `blocked_by_force_push`
decision.

## 25. Audit and Evidence Model

The shell gate produces decision records with:

| Field | Required | Notes |
|-------|----------|-------|
| `shell_gate_decision_id` | yes | Unique per decision |
| `decision` | yes | From §13 decision values |
| `reason_codes` | yes | One or more from §13 |
| `command_class` | yes | From §12 taxonomy |
| `risk_class` | yes | From §12 risk column |
| `human_review_required` | yes | Boolean |
| `execution_allowed` | yes | Boolean (false until implementation) |
| `evidence_artifacts` | recommended | Preflight outputs, task contract, health state consulted |
| `evidence_events` | recommended | Governance events consulted |
| `safety_notes` | recommended | Annotations for auditors |
| `audit_event_required` | yes | Boolean; true for any non-read-only decision |
| `generated_at` | yes | ISO 8601 |
| `schema_version` | yes | `"0.1"` |

Future audit events the gate should produce:

| Event | Trigger |
|-------|---------|
| `shell_gate_request_received` | Command evaluation requested |
| `shell_gate_command_classified` | Command classified |
| `shell_gate_decision_recorded` | Decision produced |
| `shell_gate_execution_denied` | Command denied |
| `shell_gate_human_review_required` | Routed to human review |
| `shell_gate_blocked_must_never_repeat` | Must-never-repeat control triggered |
| `shell_gate_test_run_lock_active` | Test-run lock prevented execution |
| `shell_gate_error` | Evaluation failure |

Evidence preservation is not optional. The shell gate must record what evidence it
consulted for each decision so that a future auditor can reconstruct why a command
was allowed or blocked.

## 26. Shell Gate Role Summary

The shell gate should:

- Observe proposed shell commands before execution.
- Classify command risk using the taxonomy in §12.
- Require active task where the command category demands it.
- Require relevant preflight evidence before mutation or invocation commands.
- Block raw git push and force push unconditionally.
- Block raw git commit when the governed `pcae task finish --commit` path is available.
- Block commands that write to policy-forbidden files.
- Block commands that bypass the PCAE lifecycle.
- Block backend, prompt, capture, intake, and adoption commands without explicit
  preflight evidence and task authorization.
- Block destructive filesystem commands unless narrowly authorized.
- Surface required human review with full reason codes.
- Surface missing evidence requirements.
- Preserve reason codes and audit details in every decision.
- Never convert human approval into bypass.
- Never execute commands itself.
- Never weaken `pcae health`, `pcae check`, `pcae doctor`, or `pcae push check`.

## 27. Shell Gate Non-Role Summary

The shell gate must not:

- Run commands.
- Invoke backends.
- Send prompts.
- Capture outputs.
- Apply adoption.
- Perform commits.
- Perform pushes.
- Replace the permission broker.
- Replace explicit preflight commands.
- Replace task contracts.
- Replace human review.
- Replace `pcae check`.
- Replace `pcae health`.
- Replace `pcae doctor`.
- Replace `pcae push check`.
- Grant permission by itself (permission requires the full governance chain).
- Write persistent storage in this design phase.
- Bypass policy-forbidden files.
- Bypass must-never-repeat controls.
- Treat unknown decisions as allow.
- Treat human approval as automatic bypass for blocked categories.

## 28. Known Scope Matching Divergence (88N.6 Risk)

**Risk**: `gate_dry_run.py::_evaluate_scope` uses inline fnmatch logic that diverges
from `scope_preflight.py::_match_file`. The two implementations classify the same
file differently for some patterns.

| Implementation | File | Matching logic |
|----------------|------|---------------|
| `_match_file` | `scope_preflight.py` | `fnmatch.fnmatch(filepath, pat)` |
| `_evaluate_scope` (inline) | `gate_dry_run.py` | `fnmatch.fnmatch(rf, pat) or rf == pat or rf.startswith(pat.rstrip("*"))` |

The `gate_dry_run.py` variant adds two fallbacks (`rf == pat`, `rf.startswith(...)`)
that are absent from `_match_file`. This means a file that `scope_preflight` classifies
as out-of-scope may appear in-scope to `gate_dry_run`, or vice versa, for certain
wildcard patterns.

**Shell gate implication**: A future shell gate that relies on `gate_dry_run._evaluate_scope`
for scope classification will not be consistent with the scope preflight result. This
divergence must be resolved before the shell gate uses scope classification as a blocking
signal, or the gate must canonically use `_match_file` (or a shared utility) rather than
the inline logic.

**88O action**: Document only. Do not fix.

**Recommended corrective phase**: 88O.1 — Scope Matching Shared Utility Reconciliation.
That phase should extract a single canonical `_match_file` implementation into a shared
module and update all callers (`scope_preflight.py`, `gate_dry_run.py`) to use it.
88O.1 is not started here.

## 29. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88O.1** | Scope Matching Shared Utility Reconciliation — extract canonical `_match_file` to shared module; update `scope_preflight.py` and `gate_dry_run.py` callers |
| **88P** | Shell Gate Prototype — implement shell gate command classifier and decision engine; no shell interception |
| **88Q** | Shell Gate Test Matrix and False-Positive Review — validate decision model against real command corpus |
| **88R** | Permission Broker Prototype — implement broker decision engine consuming preflight outputs |
| **88S** | Broker + Shell Gate Integration Design — define how broker decisions flow into gate decisions |

Phase 88O.1 should precede 88P to ensure that the shell gate prototype is built on a
consistent scope matching implementation.

## 30. Safety Invariants

1. Shell gate is not implemented in 88O.
2. Shell gate does not execute commands in 88O.
3. Shell gate does not intercept commands in 88O.
4. Shell gate does not authorize in 88O.
5. Shell gate does not enforce in 88O.
6. Shell gate does not invoke backends in 88O.
7. Shell gate does not mutate repo source or tests in 88O.
8. Shell gate does not commit or push in 88O.
9. Shell gate does not write storage in 88O.
10. No permission broker implementation in 88O.
11. Future shell gate must deny by default.
12. Future shell gate must preserve evidence and reason codes.
13. Future shell gate must require broker decision (or explicit absence handling) for high-risk commands.
14. Future shell gate must not override must-never-repeat controls silently.
15. Future shell gate must enforce policy-forbidden files independently of task contract content.
16. Future shell gate must honor `clear_to_run=false` from `pcae doctor test-run`.
17. Future shell gate must not kill pytest processes automatically.

## 31. Recommended Next Phase

**88O.1 — Scope Matching Shared Utility Reconciliation**

Extract the canonical `_match_file` function into a shared utility module and update
`scope_preflight.py` and `gate_dry_run.py` to use it. This resolves the divergence
documented in §28 and ensures that the future shell gate prototype (88P) operates on
consistent scope classification.

Alternatively, if the operator determines that scope matching divergence is low-risk
for the current phase set, the next phase may proceed directly to:

**88P — Shell Gate Prototype**

---

shell_gate_reconciliation_name=phase_88_shell_gate_reconciliation
shell_gate_reconciliation_version=0.1
shell_gate_reconciliation_status=draft_documented
implementation_status=not_started
command_categories=23
decision_values=26
command_taxonomy_sections=12_14
threat_model_carried_from=phase_87_shell_gate_architecture
scope_matching_divergence_documented=yes
fast_green_integration_documented=yes
recommended_next_phase=88O.1_scope_match_consistency_or_88P_shell_gate_prototype
backend_invocation_performed=false
source_files_changed=false
test_files_changed=false
