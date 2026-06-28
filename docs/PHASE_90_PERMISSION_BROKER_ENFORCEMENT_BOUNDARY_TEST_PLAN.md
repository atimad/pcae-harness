# Phase 90C — Permission Broker Enforcement Boundary Test Plan

```
phase_name    = phase_90c_permission_broker_enforcement_boundary_test_plan
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 91A — Permission Broker Simulation Prototype
```

## 1. Purpose and Scope

### 1.1 Purpose

Define a comprehensive test plan for the permission broker enforcement boundary designed in Phase 90A. This plan defines what tests must exist before any enforcement implementation begins, specifies test categories with expected outcomes, defines fixture strategies, and establishes no-go conditions that block enforcement implementation.

### 1.2 Scope

In scope (test planning only):

- Broker input model test coverage (task contract state, command class, human approval, accepted risk, readiness state)
- Broker output model test coverage (allow, deny, human_review, more_evidence, hard_block, reason codes, audit payload)
- Hard-block invariant tests proving non-overridability
- Human review and accepted-risk boundary tests
- Fail-closed behavior tests
- Audit evidence verification tests
- Fixture strategy (isolated repos, live smoke, task contract states, approval/risk fixtures)
- CLI test strategy for broker inspection commands
- Roadmap relationship and no-go conditions

Out of scope:

- Implementing enforcement, blocking, shell interception, shell wrappers
- Modifying shell configuration
- Executing command text, invoking backends, sending prompts
- Capturing outputs, performing intake/adoption
- Granting real authorization
- Writing broker source code or test implementation
- Changing existing source or test behavior
- Starting Phase 91A

### 1.3 Non-Goals

90C must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, authorization, any source changes, or any test implementation.

## 2. Starting Point

### 2.1 Design Foundation

| Phase | Deliverable | Key Outcomes |
|-------|------------|-------------|
| **90A** | Permission Broker Enforcement Boundary Design | 24 broker decisions, input/output model, hard-block model, layer responsibilities, fail-closed behavior, no-go conditions |
| **89J** | Enforcement Readiness Gate Checklist | 69 gates across 8 dimensions, go/no-go matrix |
| **89K** | Enforcement Readiness Test Plan and Fixture Design | ~304 tests, 13 fixture types, 25 test categories |
| **89N** | Enforcement Readiness Evidence Bundle and Gate Status Reporter | 69-gate registry, 20 satisfied, 47 unsatisfied |

### 2.2 Broker Decision Vocabulary (from 90A)

The broker produces one of 24 decisions:

```
allow_preflight_only
deny
requires_human_review
requires_more_evidence
blocked_by_scope
blocked_by_backend_policy
blocked_by_mutation_policy
blocked_by_commit_policy
blocked_by_push_policy
blocked_by_lifecycle_state
blocked_by_task_contract
blocked_by_risk
blocked_by_must_never_repeat
blocked_by_failed_check
blocked_by_failed_health
blocked_by_failed_doctor
blocked_by_failed_tests
blocked_by_push_check
blocked_by_raw_git_push
blocked_by_force_push
blocked_by_shell_gate
blocked_by_test_run_lock
blocked_by_conflicting_evidence
unknown
```

### 2.3 Hard-Block Decisions (from 90A §20)

Hard blocks are non-overridable by any actor (88V §16 permanent invariant):

- `blocked_by_force_push`
- `blocked_by_destructive_filesystem`
- `blocked_by_policy_forbidden_file`
- `blocked_by_history_rewrite`
- `blocked_by_raw_git_push`
- `blocked_by_raw_git_commit`
- `blocked_by_shell_gate`
- `blocked_by_conflicting_evidence`
- `blocked_by_scope`
- `blocked_by_task_contract`
- `blocked_by_failed_health`
- `blocked_by_failed_check`
- `blocked_by_failed_doctor`
- `blocked_by_failed_tests`
- `blocked_by_push_check`
- `blocked_by_test_run_lock`
- `deny`

### 2.4 Current Test Baseline

| Suite | Result |
|-------|--------|
| Fast-green | 3221/3221 passed |
| Quick tier | 8768/8768 passed |
| Full suite | 9530/9530 passed, 0 failures |

## 3. Broker Input Model Test Coverage

### 3.1 Input Categories

The broker accepts inputs across five categories (90A §18). Each category requires dedicated test coverage.

### 3.2 Task Contract State Tests

| ID | Scenario | Input State | Expected Broker Decision |
|----|----------|------------|--------------------------|
| INP-TC-001 | Active task, in-scope file, read action | task=active, file=PROJECT_STATUS.md, action=read | `allow_preflight_only` |
| INP-TC-002 | Active task, in-scope file, source_mutation | task=active, file=src/pcae/core/example.py, action=source_mutation | `allow_preflight_only` |
| INP-TC-003 | Active task, out-of-scope file | task=active, file=README.md, action=source_mutation | `blocked_by_scope` |
| INP-TC-004 | Active task, forbidden file | task=active, file=README.md (policy-forbidden), action=source_mutation | `blocked_by_scope` |
| INP-TC-005 | No active task, mutating action | task=None, action=source_mutation | `blocked_by_task_contract` |
| INP-TC-006 | No active task, read action | task=None, action=read | `requires_more_evidence` or `blocked_by_task_contract` |
| INP-TC-007 | Corrupted task contract JSON | task=invalid JSON | `blocked_by_conflicting_evidence` |
| INP-TC-008 | Missing task contract file | task=file not found | `blocked_by_task_contract` |
| INP-TC-009 | Task with enforcement_mode=advisory | task=advisory mode | Advisory classification, no real blocking |
| INP-TC-010 | Task with strict enforcement_mode | task=strict mode | Enforcement classification applied |

### 3.3 Command/Action Class Tests

| ID | Scenario | Input State | Expected Broker Decision |
|----|----------|------------|--------------------------|
| INP-CMD-001 | Read-only git status | command=`git status` | `allow_preflight_only` |
| INP-CMD-002 | Raw git push | command=`git push origin main` | `blocked_by_raw_git_push` |
| INP-CMD-003 | Force push | command=`git push --force` | `blocked_by_force_push` |
| INP-CMD-004 | Destructive filesystem | command=`rm -rf .` | `blocked_by_shell_gate` |
| INP-CMD-005 | Backend invocation | command=`claude "write code"` | `requires_human_review` |
| INP-CMD-006 | Governed lifecycle | command=`pcae health` | `allow_preflight_only` |
| INP-CMD-007 | Shell-embedded block | command=`bash -c "git push"` | `blocked_by_raw_git_push` |
| INP-CMD-008 | Compact operator bypass | command=`git status&&git push` | `blocked_by_raw_git_push` |
| INP-CMD-009 | Secret in env prefix | command=`env OPENAI_API_KEY=sk-test cmd` | `requires_human_review` (secret detected, redacted) |
| INP-CMD-010 | Unknown command | command=unparseable | `requires_more_evidence` or `blocked_by_shell_gate` |

### 3.4 Human Approval State Tests

| ID | Scenario | Input State | Expected Broker Decision |
|----|----------|------------|--------------------------|
| INP-AP-001 | Human review required, approval present, valid scope | human_review_present=true, human_approval_present=true, action=backend_invocation | `allow_preflight_only` (approval is not authorization) |
| INP-AP-002 | Human review required, no approval present | human_review_present=false, human_approval_present=false, action=backend_invocation | `requires_human_review` |
| INP-AP-003 | Hard block present, approval present | hard_block=true, human_approval_present=true | Hard block decision unchanged — approval refused |
| INP-AP-004 | Expired approval | human_approval_present=true, approval_expired=true | `requires_human_review` (expired not honored) |
| INP-AP-005 | Revoked approval | human_approval_present=true, approval_revoked=true | `requires_human_review` (revoked not honored) |
| INP-AP-006 | Wrong-scope approval | human_approval_present=true, scope=mismatch | `requires_human_review` (scope mismatch) |
| INP-AP-007 | Approval from wrong role | human_approval_present=true, role=insufficient | `requires_human_review` |

### 3.5 Accepted Risk State Tests

| ID | Scenario | Input State | Expected Broker Decision |
|----|----------|------------|--------------------------|
| INP-AR-001 | Low risk accepted, uncertain command | accepted_risk_present=true, risk_level=low | `allow_preflight_only` |
| INP-AR-002 | Medium risk accepted, in-scope write | accepted_risk_present=true, risk_level=medium | `allow_preflight_only` |
| INP-AR-003 | Hard block present, risk accepted | hard_block=true, accepted_risk_present=true | Hard block decision unchanged — risk refused |
| INP-AR-004 | Critical risk attempted | accepted_risk_present=true, risk_level=critical | `blocked_by_risk` (critical risk cannot be accepted) |
| INP-AR-005 | Expired accepted risk | accepted_risk_present=true, risk_expired=true | `requires_human_review` (expired not honored) |
| INP-AR-006 | No risk description | accepted_risk_present=true, description="" | Risk refused (description mandatory per 89I §10) |

### 3.6 Readiness and Repo State Tests

| ID | Scenario | Input State | Expected Broker Decision |
|----|----------|------------|--------------------------|
| INP-RS-001 | Health failed | health_passed=false | `blocked_by_failed_health` |
| INP-RS-002 | Check failed | check_passed=false | `blocked_by_failed_check` |
| INP-RS-003 | Doctor failed | doctor_passed=false | `blocked_by_failed_doctor` |
| INP-RS-004 | Tests failed | tests_passed=false | `blocked_by_failed_tests` |
| INP-RS-005 | Push check failed, push action | push_check_passed=false, action=push | `blocked_by_push_check` |
| INP-RS-006 | Test run lock active | test_run_clear=false | `blocked_by_test_run_lock` |
| INP-RS-007 | Enforcement readiness false | enforcement_ready=false | Advisory: enforcement not ready. Broker decision unchanged |
| INP-RS-008 | Enforcement unauthorized | enforcement_authorized=false | Advisory: enforcement not authorized |
| INP-RS-009 | Dirty worktree, mutating action | working_tree=dirty, action=commit | Requires attention; broker evaluates regardless |

## 4. Broker Output Model Test Coverage

### 4.1 Decision Output Tests

| ID | Scenario | Expected Decision | Expected Properties |
|----|----------|------------------|-------------------|
| OUT-DEC-001 | All checks pass, read action | `allow_preflight_only` | hard_block_present=false, authorization_granted=false |
| OUT-DEC-002 | Unconditional deny | `deny` | hard_block_present=true, overridable=false |
| OUT-DEC-003 | Requires human review | `requires_human_review` | hard_block_present=false, human_approval_relevant=true |
| OUT-DEC-004 | Missing evidence | `requires_more_evidence` | missing_evidence list non-empty |
| OUT-DEC-005 | Force push blocked | `blocked_by_force_push` | hard_block_present=true, overridable=false, permanent=true |
| OUT-DEC-006 | Raw git push blocked | `blocked_by_raw_git_push` | hard_block_present=true, governed_alternative="pcae push" |
| OUT-DEC-007 | Scope violation | `blocked_by_scope` | hard_block_present=true |
| OUT-DEC-008 | No task contract | `blocked_by_task_contract` | hard_block_present=true |
| OUT-DEC-009 | Contradictory evidence | `blocked_by_conflicting_evidence` | hard_block_present=true, warnings list non-empty |
| OUT-DEC-010 | Shell gate block | `blocked_by_shell_gate` | hard_block_present=true |

### 4.2 Hard Block Output Properties

Every output with `hard_block_present=true` must have:

| Property | Expected Value |
|----------|---------------|
| `hard_block_present` | `true` |
| `overridable` | `false` |
| `overridden` | `false` |
| `overridden_by` | `null` |
| `permanent` | `true` |
| `human_approval_would_change_outcome` | `false` |
| `accepted_risk_relevant` | `false` |

### 4.3 Reason Codes

| ID | Scenario | Expected Reason Codes |
|----|----------|----------------------|
| OUT-RC-001 | Shell gate block | Includes `shell_gate_decision:<sg_decision>` |
| OUT-RC-002 | Contradiction detected | Includes `contradictory_shell_gate_evidence` |
| OUT-RC-003 | Health failed | Includes `health_check_failed` |
| OUT-RC-004 | Missing active task | Includes `no_active_task_contract` |
| OUT-RC-005 | Scope denial | Includes `scope_preflight_decision:<decision>` |
| OUT-RC-006 | Missing evidence | Includes `missing_evidence_items` |
| OUT-RC-007 | Human review required | Includes `shell_gate_requires_human_review` or `action_requires_human_review` |
| OUT-RC-008 | All evidence passes | Includes `all_provided_evidence_passes` |

### 4.4 Audit Payload Tests

| ID | Scenario | Required Audit Fields |
|----|----------|----------------------|
| OUT-AUD-001 | Blocked command | event_type=`enforcement.blocked`, decision, hard_block, outcome, operator, command hash, timestamp |
| OUT-AUD-002 | Allowed command | event_type=`enforcement.allowed`, authorization_granted=false |
| OUT-AUD-003 | Human review gated | event_type=`enforcement.gated_review`, human_review_required=true |
| OUT-AUD-004 | Denied command | event_type=`enforcement.denied`, permanent=true |
| OUT-AUD-005 | Hard block | hard_block.reason, hard_block.source, hard_block.overridable=false |

## 5. Hard-Block Invariant Tests

### 5.1 Core Invariant

**88V §16 permanent invariant:** No human, no approval, no accepted risk, no operator override can bypass a hard block.

### 5.2 Hard-Block Override Refusal Tests

Each hard block category must be tested against ALL override attempts:

| ID | Hard Block | Override Attempt | Expected Result |
|----|-----------|-----------------|----------------|
| HB-001 | `blocked_by_force_push` | Human approval present | Block stands; approval refused |
| HB-002 | `blocked_by_force_push` | Accepted risk present | Block stands; risk refused |
| HB-003 | `blocked_by_force_push` | Operator override flag | Block stands; override refused |
| HB-004 | `blocked_by_raw_git_push` | Human approval present | Block stands |
| HB-005 | `blocked_by_raw_git_push` | Accepted risk present | Block stands |
| HB-006 | `blocked_by_destructive_filesystem` | Human approval present | Block stands |
| HB-007 | `blocked_by_destructive_filesystem` | Accepted risk present | Block stands |
| HB-008 | `blocked_by_policy_forbidden_file` | Human approval present | Block stands |
| HB-009 | `blocked_by_policy_forbidden_file` | Within task scope | Block stands (policy-forbidden is independent of task scope) |
| HB-010 | `blocked_by_conflicting_evidence` | Human approval present | Block stands |
| HB-011 | `blocked_by_failed_health` | Accepted risk present | Block stands |
| HB-012 | `blocked_by_failed_check` | Accepted risk present | Block stands |
| HB-013 | `blocked_by_scope` | Operator "I know this file" | Block stands |

### 5.3 Hard-Block Non-Overridability Code-Path Tests

Every code path that applies human approval or accepted risk must verify:

| ID | Code Path | Verification |
|----|----------|-------------|
| HB-CP-001 | Enforcement executor: before applying approval | Checks `hard_block_present`; refuses if true |
| HB-CP-002 | Enforcement executor: before applying accepted risk | Checks `hard_block_present`; refuses if true |
| HB-CP-003 | Approval validator: `classify_approval()` | Returns `hard_block_non_overridable` when hard block present |
| HB-CP-004 | Risk validator: `classify_accepted_risk()` | Returns `hard_block_non_overridable` when hard block present |
| HB-CP-005 | Broker: `_check_sg_contradiction()` | Detects `human_approval_alongside_sg_hard_block` |
| HB-CP-006 | Broker: `_check_sg_contradiction()` | Detects `accepted_risk_alongside_sg_hard_block` |

### 5.4 Required Hard-Block Categories

Every category from 90A §20 must have dedicated non-override tests:

| Category | Minimum Tests | Key Assertions |
|----------|--------------|----------------|
| Raw git commit | 3 | `blocked_by_shell_gate`, hard_block, overridable=false |
| Raw git push | 3 | `blocked_by_raw_git_push`, governed_alternative="pcae push" |
| Force push | 5 | `blocked_by_force_push`, permanent=true, all override attempts refused |
| --no-verify bypass | 2 | `blocked_by_raw_git_commit` or `blocked_by_raw_git_push` |
| Out-of-scope mutation | 3 | `blocked_by_scope` |
| Forbidden file mutation | 4 | `blocked_by_scope` (policy-forbidden), independent of task scope |
| Unauthorized backend invocation | 3 | `blocked_by_backend_policy` or `requires_human_review` |
| Shell interception disabled | 2 | `blocked_by_shell_gate` (future — when shell gate enforces) |
| Missing active task (when required) | 3 | `blocked_by_task_contract` |
| Dirty lifecycle mismatch | 2 | `blocked_by_lifecycle_state` |
| Enforcement readiness false | 2 | Advisory: enforcement not ready; broker decision unchanged |
| Enforcement unauthorized | 2 | Advisory: enforcement not authorized |
| Command class unknown | 2 | `requires_more_evidence` or `blocked_by_shell_gate` |

**Total hard-block category tests: ~36**

## 6. Human Review and Accepted-Risk Tests

### 6.1 Human Review Boundary

Human review may permit progress only when ALL of these conditions hold:

1. The action is NOT a hard block
2. Required evidence exists (health, check, task contract)
3. Approval is scoped to the specific command/action
4. Approval is fresh (not expired)
5. Approval is auditable (record created)
6. Accepted risk is bounded and does not override policy

### 6.2 Human Review Tests

| ID | Scenario | Expected Outcome |
|----|----------|-----------------|
| HR-001 | Backend invocation, valid approval, in-scope files | `allow_preflight_only` (approval present, still not authorization) |
| HR-002 | Backend invocation, no approval | `requires_human_review` |
| HR-003 | Backend invocation, expired approval | `requires_human_review` |
| HR-004 | Backend invocation, revoked approval | `requires_human_review` |
| HR-005 | Backend invocation, wrong-scope approval | `requires_human_review` |
| HR-006 | Adoption, valid reviewer approval | `allow_preflight_only` |
| HR-007 | Adoption, self-approval (insufficient role) | `requires_human_review` |
| HR-008 | Push, valid reviewer approval | `allow_preflight_only` |
| HR-009 | Push, approval present but hard block also present | Hard block stands; approval refused |
| HR-010 | Commit, valid task-owner approval | `allow_preflight_only` |

### 6.3 Accepted-Risk Tests

| ID | Scenario | Expected Outcome |
|----|----------|-----------------|
| AR-001 | Low risk, uncertain command, self-acknowledgment | `allow_preflight_only` |
| AR-002 | Medium risk, in-scope write, active task | `allow_preflight_only` |
| AR-003 | High risk, backend invocation, reviewer approval + acknowledgment | `allow_preflight_only` |
| AR-004 | Critical risk attempted (force push) | Refused — critical risk cannot be accepted |
| AR-005 | Hard block present, any risk level | Hard block stands; risk refused |
| AR-006 | Expired risk acceptance | Risk not honored; re-gate required |
| AR-007 | No risk description provided | Risk refused (description mandatory) |
| AR-008 | Scope mismatch: risk for different command | Risk not honored |
| AR-009 | Accepted risk revoked before action | Risk not honored |
| AR-010 | Multiple overlapping risks: most specific applied | Most specific risk applied |

## 7. Fail-Closed Behavior Tests

### 7.1 Fail-Closed Principle

**Any failure, uncertainty, missing evidence, contradiction, or error must result in blocking the command — never allowing it.**

### 7.2 Fail-Closed Scenarios

| ID | Failure Mode | Expected Decision | Expected Behavior |
|----|-------------|------------------|-------------------|
| FC-001 | Task contract cannot be parsed (invalid JSON) | `blocked_by_conflicting_evidence` | Block; log audit event; report corruption |
| FC-002 | Task contract file missing (expected but absent) | `blocked_by_task_contract` | Block; log audit event |
| FC-003 | Readiness state cannot be read | `requires_more_evidence` or `blocked_by_conflicting_evidence` | Block; report missing evidence |
| FC-004 | Repo state cannot be inspected (no git repo) | `requires_more_evidence` | Block; report missing evidence |
| FC-005 | Broker input incomplete (missing required fields) | `requires_more_evidence` | Block; list missing fields |
| FC-006 | Audit writer fails (disk full) | Enforcement degrades to simulation | All commands evaluated but not blocked; audit failure logged |
| FC-007 | Audit chain broken (tampered record) | Enforcement degrades to simulation | Operator notified; chain repair required |
| FC-008 | Command/action class unknown | `requires_more_evidence` or `blocked_by_unknown_command` | Block; request clarification |
| FC-009 | Policy version missing or incompatible | `blocked_by_conflicting_evidence` | Block; report version mismatch |
| FC-010 | Shell gate classification error (exception) | `blocked_by_shell_gate` | Block; log error |
| FC-011 | Scope preflight error (exception) | `blocked_by_scope` | Block; log error |
| FC-012 | Contradiction detected in evidence | `blocked_by_conflicting_evidence` | Block; report contradictions |
| FC-013 | Shell gate evidence version mismatch | `blocked_by_conflicting_evidence` | Block; report version mismatch |
| FC-014 | Performed/authorization flag unexpectedly true | `blocked_by_conflicting_evidence` | Block; invariant violation |
| FC-015 | Secret access with unredacted command text | `blocked_by_conflicting_evidence` | Block; redaction failure |

### 7.3 Degraded Mode Tests

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| FC-DG-001 | Audit chain broken → degraded | Enforcement mode becomes `degraded`; all commands simulation-only |
| FC-DG-002 | Audit write failure → degraded | Same; audit failure logged |
| FC-DG-003 | Degraded → disable → re-enable | Operator can disable degraded enforcement; re-enable requires repair |
| FC-DG-004 | Degraded mode produces audit events | Best-effort audit events for degradation itself |

## 8. Audit Evidence Tests

### 8.1 Required Audit Events

Every broker decision must produce an auditable record. The audit event must be produced BEFORE any enforcement action is applied.

### 8.2 Audit Evidence Per Decision

| ID | Decision | Required Audit Fields |
|----|----------|----------------------|
| AUD-001 | `allow_preflight_only` | event_type=`enforcement.allowed`, authorization_granted=false, execution_authorized=false |
| AUD-002 | `deny` | event_type=`enforcement.denied`, permanent=true, overridable=false |
| AUD-003 | `blocked_by_force_push` (hard block) | event_type=`enforcement.blocked`, hard_block.reason, hard_block.source, hard_block.overridable=false, hard_block.permanent=true |
| AUD-004 | `blocked_by_raw_git_push` (hard block) | event_type=`enforcement.blocked`, governed_alternative="pcae push" |
| AUD-005 | `requires_human_review` | event_type=`enforcement.gated_review`, human_review_required=true |
| AUD-006 | `requires_more_evidence` | event_type=`enforcement.decision`, missing_evidence list non-empty |
| AUD-007 | `blocked_by_conflicting_evidence` | event_type=`enforcement.blocked`, contradictions listed |
| AUD-008 | Human approval granted | event_type=`approval.granted`, approved_by, scope, expires_at |
| AUD-009 | Accepted risk | event_type=`risk.accepted`, risk_level, risk_description, hard_block_override=false |
| AUD-010 | Enforcement disabled | event_type=`enforcement.disabled`, operator, timestamp |

### 8.3 Audit Integrity Tests

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| AUD-INT-001 | Audit record checksum valid | SHA-256 of record matches `integrity.checksum` |
| AUD-INT-002 | Chain integrity: next record references previous | `record_N+1.previous_checksum == sha256(record_N)` |
| AUD-INT-003 | Tamper detection: modified record | Checksum mismatch → chain break detected |
| AUD-INT-004 | Tamper detection: deleted record | Chain gap → break detected |
| AUD-INT-005 | Tamper detection: inserted forged record | Chain break → break detected |
| AUD-INT-006 | Redaction: no raw secrets in audit | All `text_redacted` fields contain redacted or hash-only content |
| AUD-INT-007 | Redaction: command text redacted | `command.text_redacted` field exists and is not raw command text |
| AUD-INT-008 | Audit log rotation | New file created when current reaches 10MB |

## 9. Fixture Strategy

### 9.1 Fixture Types (from 89K §10)

| # | Fixture Type | Purpose | Storage |
|---|-------------|---------|---------|
| 1 | `command_fixture` | Command text with expected classification and decision | `tests/fixtures/commands/` |
| 2 | `task_contract_fixture` | Synthetic task contract with scope, allowed/forbidden files | `tests/fixtures/task_contracts/` |
| 3 | `repo_state_fixture` | Git repository in known state (clean, dirty, specific branch) | `tests/fixtures/repo_states/` |
| 4 | `audit_event_fixture` | Synthetic audit event (valid, tampered, chain-broken) | `tests/fixtures/audit_events/` |
| 5 | `approval_fixture` | Synthetic approval record (active, expired, revoked) | `tests/fixtures/approvals/` |
| 6 | `accepted_risk_fixture` | Synthetic accepted-risk record (low/medium/high/critical) | `tests/fixtures/accepted_risks/` |
| 7 | `readiness_fixture` | Enforcement readiness state (ready, not ready, degraded) | `tests/fixtures/readiness/` |

### 9.2 Fixture Catalog for Broker Tests

#### Isolated Repo Fixtures

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-ISO-001 | Clean main, idle | Default healthy state, no active task |
| FIX-ISO-002 | Clean main, active task | Active task present with proper scope |
| FIX-ISO-003 | Dirty worktree | Uncommitted changes present |
| FIX-ISO-004 | Detached HEAD | HEAD at specific commit |
| FIX-ISO-005 | Feature branch | On feature branch, diverged from main |
| FIX-ISO-006 | Behind origin/main | Local behind remote |
| FIX-ISO-007 | Ahead of origin/main | Unpushed commits |
| FIX-ISO-008 | No .pcae directory | Uninitialized repository |
| FIX-ISO-009 | Corrupt .pcae state | Missing or invalid governance artifacts |
| FIX-ISO-010 | Merge conflict | Unresolved merge conflict |

#### Live REPO_ROOT Smoke Checks

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-LIVE-001 | Current repo, idle state | Smoke test against actual PCAE repo |
| FIX-LIVE-002 | Current repo, active task | Smoke test with real task contract |

#### Task Contract Fixtures

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-TC-001 | Valid task, in-scope write | Allowed files match tested files |
| FIX-TC-002 | Valid task, out-of-scope write | Tested file not in allowed list |
| FIX-TC-003 | Valid task, forbidden file | Tested file in forbidden list |
| FIX-TC-004 | No active task | tasks/active/ empty |
| FIX-TC-005 | Corrupted task JSON | Invalid JSON in task file |
| FIX-TC-006 | Missing task file | Task file referenced but absent |
| FIX-TC-007 | Task with enforcement_mode=advisory | Advisory mode task |
| FIX-TC-008 | Task with enforcement_mode=strict | Strict enforcement task |

#### Approval Fixtures

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-AP-001 | Active approval, single command | Valid, in-scope, fresh |
| FIX-AP-002 | Expired approval | expires_at in past |
| FIX-AP-003 | Revoked approval | revoked_at set |
| FIX-AP-004 | Wrong-scope approval | Scope doesn't match command |
| FIX-AP-005 | Self-approval, low risk | Valid for read-only uncertain commands |
| FIX-AP-006 | Reviewer approval, high risk | Valid for backend invocation |

#### Accepted-Risk Fixtures

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-AR-001 | Low risk, with description | Valid self-acknowledgment |
| FIX-AR-002 | Medium risk, in-scope | Valid with active task |
| FIX-AR-003 | High risk, with review | Valid with reviewer approval |
| FIX-AR-004 | Critical risk | Should be refused |
| FIX-AR-005 | No description | Should be refused |
| FIX-AR-006 | Expired risk | Should not be honored |

#### Readiness Fixtures

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-RDY-001 | Readiness false | enforcement_ready=false, enforcement_authorized=false |
| FIX-RDY-002 | All gates satisfied | enforcement_ready=true (future) |
| FIX-RDY-003 | Degraded state | Enforcement degraded due to audit failure |

#### Notification/Mobile Fixture (Future Input Source Only)

| ID | Fixture | Description |
|----|---------|-------------|
| FIX-NTF-001 | Telegram-originated command | Simulated Telegram command with user ID and auth context |
| FIX-NTF-002 | Unauthorized Telegram user | Unknown user ID |
| FIX-NTF-003 | Mobile command confirmation | Command with confirmation token |

These notification/mobile fixtures are defined for future planning only. They model the input shape of a Telegram-originated command without implementing Telegram, mobile delivery, or any inbound command gateway. They are not used in 90C or 91-series tests.

### 9.3 Fixture Creation Rules

1. **No real secrets.** All fixtures use synthetic tokens.
2. **No real repository mutation.** Repo-state fixtures use temp directories.
3. **Deterministic.** Same fixture always produces same expected outcome.
4. **Self-contained.** Each fixture includes all metadata for validation.
5. **Versioned.** Each fixture declares a `fixture_schema_version`.
6. **Isolated.** No fixture references another fixture's path; references are by ID.

## 10. CLI Test Strategy

### 10.1 Future Broker CLI Commands

When the permission broker is implemented (91A–91B), these CLI commands will need test coverage:

```
pcae broker check --command "<cmd>" [--json]
pcae broker check --command "<cmd>" --requested-action <action> --requested-file <file> [--json]
pcae broker explain --decision <decision> [--json]
pcae broker status [--json]
```

### 10.2 CLI Test Categories

| ID | Category | Tests | Description |
|----|----------|-------|-------------|
| CLI-001 | Command exists | 3 | `pcae broker check/explain/status` exit successfully |
| CLI-002 | Required flags | 2 | Missing --command gives helpful error |
| CLI-003 | JSON output | 6 | --json flag produces valid JSON with required fields |
| CLI-004 | Human-readable output | 3 | Plain text output contains decision, reason, recommendation |
| CLI-005 | Exit codes | 4 | 0=allow, 1=blocked, 2=error, other=unexpected |
| CLI-006 | Decision explanation | 24 | All 24 decisions explainable via `pcae broker explain` |
| CLI-007 | Status invariants | 2 | Status reports simulation-only, no enforcement |
| CLI-008 | Redaction in output | 3 | Secrets redacted in both human and JSON output |
| CLI-009 | Authorization wording | 2 | Output states non-authorization; "does NOT mean PCAE authorizes" |
| CLI-010 | Help text | 3 | `--help` shows all subcommands and flags |
| CLI-011 | JSON schema stability | 2 | JSON output has stable field names and types |

**Estimated CLI tests: ~54**

### 10.3 CLI Test Principles

- CLI tests validate the user interface, not the broker logic.
- Broker logic is tested by unit tests against `build_permission_broker()`.
- CLI tests use subprocess against live REPO_ROOT or isolated temp repos.
- Exit codes must be deterministic and documented.
- JSON output must include `schema_version`, `generated_at`, and all required fields.

## 11. Relationship to Roadmap

### 11.1 Canonical Roadmap

This test plan supports the Production v1 path defined in [docs/ROADMAP.md](../ROADMAP.md). Phase 90C is the final phase in the 90-series (enforcement boundary and test foundation). After 90C, the path proceeds to 91A (Permission Broker Simulation Prototype).

### 11.2 Production v1 Alignment

| 90C Deliverable | Supports Production v1 Goal |
|----------------|---------------------------|
| Broker input model tests | Validates that the broker correctly processes all input categories |
| Hard-block invariant tests | Proves that hard blocks cannot be overridden — core Production v1 safety guarantee |
| Fail-closed tests | Ensures broker fails safe in all error conditions |
| Audit evidence tests | Ensures every broker decision produces auditable records |
| CLI test strategy | Defines the user interface for broker inspection and decision explanation |
| Fixture strategy | Provides the test infrastructure for future implementation phases |

### 11.3 Telegram/Mobile Scope

Per the canonical roadmap: Telegram/mobile integration remains **outbound only** in Production v1. Notification/mobile fixtures in §9.2 are defined as future input source models only — they are not used in 90C or 91-series tests and do not imply inbound command support. Inbound commands will be considered only after broker and shell gate maturity (future v2+).

## 12. No-Go Conditions

### 12.1 Absolute Blocks on Broker Implementation (91A)

Broker implementation must not start if ANY of these is true:

| # | Condition | Rationale |
|---|-----------|-----------|
| **STOP-1** | Full suite is not green (zero failures) | Implementation must not regress existing behavior |
| **STOP-2** | Fast-green regresses | Fast-green is the pre-commit safety net |
| **STOP-3** | Any hard-block invariant is violated in existing simulation code | Hard-block non-overridability is a permanent safety invariant |
| **STOP-4** | Secret redaction can be bypassed in any output path | Secret leakage is unacceptable |
| **STOP-5** | No active task contract for 91A | Ungoverned implementation |
| **STOP-6** | Operator has not explicitly authorized 91A | Human authority is absolute |
| **STOP-7** | 90C test plan not completed and reviewed | Test plan is the blueprint; implementation without a plan is ungoverned |
| **STOP-8** | Enforcement readiness gates from 89J not tracked | Must know which gates 91A will satisfy |
| **STOP-9** | Existing broker safety invariants not verified | `safety_notes.*` all must be true |
| **STOP-10** | Existing simulation-only invariants not preserved | `no_execution=True`, `no_enforcement=True` |

### 12.2 Conditional Blocks

| # | Condition | Required Before Proceeding |
|---|-----------|--------------------------|
| **STOP-11** | Fixture infrastructure not in place | Create fixture directories and helper utilities |
| **STOP-12** | Test isolation not verified | Confirm tests don't interfere with each other or live repo state |
| **STOP-13** | Review not performed by at least one other operator | Independent review of test plan |

## 13. Test Count Summary

| Category | Minimum Tests |
|----------|--------------|
| Broker input model — task contract | 10 |
| Broker input model — command/action class | 10 |
| Broker input model — human approval | 7 |
| Broker input model — accepted risk | 6 |
| Broker input model — readiness/repo state | 9 |
| Broker output model — decisions | 10 |
| Broker output model — reason codes | 8 |
| Broker output model — audit payload | 5 |
| Hard-block invariant — non-override | 13 |
| Hard-block invariant — code paths | 6 |
| Hard-block categories | 36 |
| Human review boundary | 10 |
| Accepted-risk boundary | 10 |
| Fail-closed scenarios | 15 |
| Degraded mode | 4 |
| Audit evidence per decision | 10 |
| Audit integrity | 8 |
| CLI tests | 54 |
| **Total** | **~231** |

These tests are in addition to:
- Existing 244 simulation tests (89D)
- Existing 87 audit/rollback prototype tests (89L)
- Existing 62 approval prototype tests (89M)
- Existing 70 readiness reporter tests (89N)

## 14. Recommended Next Phase

**91A — Permission Broker Simulation Prototype** (requires explicit operator approval)

91A will implement the broker as a simulation-only decision aggregator based on the 90A boundary design and this 90C test plan. The prototype will:
1. Implement `build_permission_broker()` with structured input/output
2. Not block commands, intercept shell, or invoke backends
3. Preserve all simulation-only invariants
4. Be validated against this test plan

**Do not start 91A without explicit operator approval.**

---

*Phase 90C completes the 90-series enforcement boundary and test foundation trilogy (90A design, 90B baseline repair, 90C test plan). All three phases are design/test-planning only. No enforcement implementation has been performed. The repository remains at 9530/9530 passed, 0 failures. The 90C test plan defines ~231 broker-specific tests across 13 categories — to be implemented in 91A+.*
