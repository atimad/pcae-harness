# Phase 89K — Enforcement Readiness Test Plan and Fixture Design

```
phase_name    = phase_89k_enforcement_readiness_test_plan_and_fixture_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89l_enforcement_audit_rollback_prototype  (requires operator approval)
```

## 1. Purpose

Create a detailed enforcement-readiness test plan and fixture design before any enforcement architecture or prototype. Transform the 89G–89J threat model, audit/rollback model, approval/risk model, and go/no-go checklist into a concrete validation plan: test categories, fixtures, expected outcomes, required evidence, and minimum acceptance thresholds.

This is a **design/test-planning document**. No implementation is performed in 89K.

## 2. Scope

In scope (design only):

- Map 89G safety claims to required test categories
- Map 89H audit/rollback schemas to test requirements
- Map 89I approval/risk policy to test requirements
- Map 89J go/no-go gates to test categories
- Define fixture taxonomy (13 fixture types)
- Define command fixtures for all 25 test categories
- Define task-contract, repository-state, audit-event, rollback-artifact, approval/risk, secret/redaction, bypass-attempt, failure-mode, cross-platform shell, and Telegram/mobile-control fixtures
- Define expected outcomes and assertions per test category
- Define minimum pass thresholds per category
- Define test execution tiers
- Define data isolation and cleanup rules
- Define required evidence artifacts
- Document unsatisfied gates after 89K
- Recommend the next phase

Out of scope:

- Implementing enforcement, blocking, shell interception, wrappers
- Installing shell wrappers or modifying shell configuration
- Executing requested command text, invoking backends, sending prompts
- Capturing outputs, performing intake/adoption
- Granting real authorization
- Persisting advisory/broker/shell-gate/dry-run/enforcement state
- Adding persistent cache
- Changing advisory, shell-gate, permission-broker, dry-run, audit, approval, or lifecycle behavior
- Creating enforcement implementation files
- Raw git commit, raw git push, force push

## 3. Non-Goals

89K must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, authorization, or any source/test changes.

## 4. Starting Point from 89G–89J

| Phase | Deliverable | Key Outcomes |
|-------|------------|-------------|
| 89G | Threat Model & Safety Case | 34 threats, 10 safety claims, 20 controls, 10 must-not-proceed |
| 89H | Audit & Rollback Model | 16 event types, 5 schemas, chain integrity, ~60 tests |
| 89I | Approval & Risk Policy | 7 principles, 5 roles, 4 risk levels, hard-block non-overridable, ~43 tests |
| 89J | Gate Checklist | 69 gates, 8 dimensions, go/no-go matrix, 4 of 69 satisfied |

89K consolidates the test requirements from all four phases into a single, actionable test plan with concrete fixtures.

### 4.1 Current Test Baseline

| Suite | Tests | Result |
|-------|-------|--------|
| Dry-run simulation | 244 | All passing |
| Dry-run CLI | 24 | All passing |
| Fast-green | 3,221 | All passing |
| Full suite | 9,311 | Zero failures |

## 5. Relationship to 89J Readiness Gates

89J identified 69 gates across 8 dimensions. 89K defines the test plan that will satisfy the test-dimension gates (T1–T15) and provides fixture designs that will be used to verify implementation (I1–I11), audit (A1–A8), rollback (R1–R5), operator approval (O1–O7), secret-protection (S1–S5), and bypass-detection (B1–B5) gates.

### 5.1 Gate-to-Test-Category Mapping

| 89J Gate | Category | 89K Test Category |
|----------|----------|-------------------|
| T1 | Audit write/read | Category 5: Audit event creation tests |
| T2 | Audit chain integrity | Category 6: Audit integrity/tamper-evidence tests |
| T3 | Audit redaction | Category 9: Secret redaction and leakage tests |
| T4 | Rollback create/restore | Category 7–8: Rollback artifact + recovery tests |
| T5 | Approval grant/expire/revoke | Category 3–4: Accepted-risk + operator approval tests |
| T6 | Hard-block refusal | Category 1: Hard-block invariant tests |
| T7 | Enforcement decision equivalence | Category 1: Hard-block invariant tests |
| T8 | Block enforcement verification | Category 1: Hard-block invariant tests |
| T9 | Allow enforcement verification | Category 1: Hard-block invariant tests |
| T10 | Bypass detection | Category 12: Compact operator bypass tests |
| T11 | Emergency disable | Category 19: Failure-mode/fail-closed tests |
| T12 | Cross-platform shell | Category 20: Cross-platform shell compatibility tests |
| T13 | Threat model adversarial | Category 10–12: Command parser + bypass tests |
| T14 | Safety invariants | ✅ Already satisfied (244 simulation tests) |
| T15 | Full suite green | ✅ Already satisfied (9,311 tests) |

## 6. Safety-Claim-to-Test Mapping

Each 89G safety claim maps to specific test categories and fixtures:

| Safety Claim | Test Categories | Fixture Types | Minimum Tests |
|-------------|----------------|---------------|---------------|
| **SC-1**: PCAE must not execute unapproved commands | 1, 17 | command, backend, failure_mode | 30 |
| **SC-2**: Hard blocks must not be overridable | 1, 3, 4 | command, approval, accepted_risk | 20 |
| **SC-3**: Must not confuse advisory/dry-run with real authorization | 1, 17 | command, audit_event | 10 |
| **SC-4**: Must preserve audit evidence | 5, 6 | audit_event, failure_mode | 15 |
| **SC-5**: Must preserve rollback ability | 7, 8 | rollback_artifact, repo_state | 16 |
| **SC-6**: Must protect secrets in all output paths | 9 | secret, command, audit_event | 20 |
| **SC-7**: Must fail closed when evidence is missing | 19 | failure_mode, command | 15 |
| **SC-8**: Must detect or prevent known bypass paths | 10–16, 25 | command, shell, bypass, task_contract | 35 |
| **SC-9**: Must keep operator-visible wording unambiguous | 1, 2, 3, 4 | command, approval | 10 |
| **SC-10**: Must not move to enforcement without explicit authorization | 2, 4, 19 | approval, command, task_contract | 10 |

**Total minimum tests mapped from safety claims:** ~181 (some tests satisfy multiple claims)

## 7. Audit-Model-to-Test Mapping

89H defined 16 audit event types, 5 schemas, and ~60 required tests. 89K maps each:

| 89H Requirement | Test Category | Fixture Types | Minimum Tests |
|----------------|---------------|---------------|---------------|
| Audit event creation (all 16 event types) | 5 | audit_event | 16 |
| Audit event schema validation | 5 | audit_event, json_schema | 10 |
| Audit chain integrity (checksum chaining) | 6 | audit_event | 8 |
| Tamper detection (modification, deletion, insertion) | 6 | audit_event | 8 |
| Audit redaction (no raw secrets) | 5, 9 | audit_event, secret | 8 |
| Retention/rotation (10MB files, 100 max) | 5 | audit_event | 5 |
| Recovery workflow (disable → degrade → re-enable) | 19 | audit_event, failure_mode | 6 |
| Rollback artifact creation | 7 | rollback_artifact | 8 |

**Total minimum tests mapped from audit model:** ~69

## 8. Rollback-Model-to-Test Mapping

89H defined rollback artifact schema, recovery workflow, and failure modes:

| 89H Requirement | Test Category | Fixture Types | Minimum Tests |
|----------------|---------------|---------------|---------------|
| Pre-mutation snapshot creation | 7 | rollback_artifact, repo_state | 4 |
| Rollback artifact checksum validation | 7 | rollback_artifact | 3 |
| Rollback restore (files restored correctly) | 8 | rollback_artifact, repo_state | 8 |
| Git reflog fallback (artifact corrupted) | 8 | rollback_artifact, failure_mode | 3 |
| Rollback reversibility (re-apply after restore) | 8 | rollback_artifact | 2 |
| Concurrent mutation conflict | 8, 19 | rollback_artifact, failure_mode | 2 |
| Rollback list/restore CLI | 7, 8 | rollback_artifact | 4 |

**Total minimum tests mapped from rollback model:** ~26

## 9. Approval-Policy-to-Test Mapping

89I defined 7 principles, 5 roles, 4 risk levels:

| 89I Requirement | Test Category | Fixture Types | Minimum Tests |
|----------------|---------------|---------------|---------------|
| Approval grant (correct scope, expiry, audit) | 3, 4 | approval | 8 |
| Approval expiration (expired not honored) | 3 | approval | 5 |
| Approval revocation (revoked not honored) | 3 | approval | 5 |
| Hard-block refusal (approval cannot override) | 1, 4 | approval, command | 8 |
| Accepted-risk levels (correct gating) | 3 | accepted_risk | 6 |
| Human review vs authorization distinction | 2, 4 | approval | 4 |
| Multi-party approval (deferred Stage 4+) | — | — | 0 |
| Misuse prevention (expiry, revocation, race) | 3, 4, 19 | approval, accepted_risk | 6 |

**Total minimum tests mapped from approval policy:** ~42

## 10. Fixture Taxonomy

### 10.1 Fixture Type Definitions

| # | Fixture Type | Description | Format | Storage |
|---|-------------|-------------|--------|---------|
| 1 | `command_fixture` | A command text string with expected classification, decision, and outcome | JSON | `tests/fixtures/commands/` |
| 2 | `task_contract_fixture` | A synthetic task contract with scope, allowed/forbidden files, enforcement mode | JSON | `tests/fixtures/task_contracts/` |
| 3 | `repo_state_fixture` | A git repository in a known state (clean, dirty, specific commit, specific branch) | Shell script + git bundle | `tests/fixtures/repo_states/` |
| 4 | `audit_event_fixture` | A synthetic audit event record (valid, tampered, corrupted, or chain-broken) | JSONL | `tests/fixtures/audit_events/` |
| 5 | `rollback_artifact_fixture` | A synthetic rollback artifact with known pre/post state | JSON | `tests/fixtures/rollback_artifacts/` |
| 6 | `approval_fixture` | A synthetic approval record (active, expired, revoked) | JSON | `tests/fixtures/approvals/` |
| 7 | `accepted_risk_fixture` | A synthetic accepted-risk record (low/medium/high/critical) | JSON | `tests/fixtures/accepted_risks/` |
| 8 | `secret_fixture` | A command text containing known secret patterns (API keys, tokens, env vars) | Text | `tests/fixtures/secrets/` |
| 9 | `shell_fixture` | A shell invocation pattern (bash -c, sh -c, zsh -c, eval, source) | Text | `tests/fixtures/shells/` |
| 10 | `backend_fixture` | A synthetic backend invocation command (claude, codex, kimi, deepseek) | Text | `tests/fixtures/backends/` |
| 11 | `failure_mode_fixture` | A scenario that triggers a specific failure (disk full, chain break, corruption) | JSON | `tests/fixtures/failure_modes/` |
| 12 | `telegram_command_fixture` | A simulated Telegram-originated command with user ID and auth context | JSON | `tests/fixtures/telegram/` |
| 13 | `json_schema_fixture` | A JSON schema version for compatibility testing | JSON Schema | `tests/fixtures/json_schemas/` |

### 10.2 Fixture Naming Convention

```
{fixture_type}/{category}_{scenario_id}_{description}.{ext}

Examples:
  commands/hardblock_HB001_force_push.json
  task_contracts/scope_TC001_in_scope_write.json
  repo_states/clean_RS001_default_branch.sh
  audit_events/valid_AE001_enforcement_blocked.jsonl
  rollback_artifacts/valid_RA001_single_file.json
  approvals/active_AP001_single_command.json
  secrets/redact_SC001_openai_api_key.txt
  shells/embedded_SH001_bash_c_git_push.txt
  backends/invoke_BE001_claude_agent.txt
  failure_modes/disrupt_FM001_disk_full.json
  telegram/cmd_TG001_authorized_user.json
  json_schemas/v01_JS001_current_schema.json
```

### 10.3 Fixture Creation Rules

1. **No real secrets.** All secret fixtures use synthetic tokens (e.g., `sk-test-1234`, `OPENAI_API_KEY=test-key`).
2. **No real repository mutation.** Repo-state fixtures are created in temporary directories.
3. **Deterministic.** Same fixture always produces the same expected outcome.
4. **Self-contained.** Each fixture includes all metadata needed to validate the test.
5. **Versioned.** Each fixture declares a `fixture_schema_version`.
6. **Isolated.** No fixture references another fixture's path; all references are by ID.

## 11. Command Fixtures

### 11.1 Hard-Block Command Fixtures

```json
{
  "fixture_id": "cmd_HB001",
  "fixture_type": "command_fixture",
  "fixture_schema_version": "0.1",
  "category": "hard_block",
  "command_text": "git push origin main",
  "expected": {
    "classification": "raw_git_push",
    "shell_gate_category": "raw_git_push",
    "broker_decision": "blocked_by_raw_git_push",
    "simulation_decision": "would_block_by_raw_git_push",
    "severity": "blocked",
    "hard_block": true,
    "overridable": false,
    "governed_alternative": "pcae push"
  }
}
```

### 11.2 Complete Command Fixture Catalog

| ID | Command | Expected Decision | Hard Block |
|----|---------|------------------|------------|
| cmd_HB001 | `git push origin main` | blocked_by_raw_git_push | Yes |
| cmd_HB002 | `git push --force origin main` | blocked_by_force_push | Yes |
| cmd_HB003 | `git push -f` | blocked_by_force_push | Yes |
| cmd_HB004 | `git commit -m "x"` | blocked_by_raw_git_commit | Yes |
| cmd_HB005 | `git commit --no-verify -m "x"` | blocked_by_raw_git_commit | Yes |
| cmd_HB006 | `git reset --hard HEAD~5` | blocked_by_history_rewrite | Yes |
| cmd_HB007 | `git update-index --skip-worktree README.md` | blocked_by_shell_gate | Yes |
| cmd_HB008 | `rm -rf .` | blocked_by_destructive_filesystem | Yes |
| cmd_HB009 | `rm -rf /` | blocked_by_destructive_filesystem | Yes |
| cmd_HB010 | `rm -rf --no-preserve-root /` | blocked_by_destructive_filesystem | Yes |
| cmd_HB011 | `python -c "open('README.md','w').write('x')"` | blocked_by_policy_forbidden_file | Yes |
| cmd_HB012 | `git push --force --lease origin main` | blocked_by_force_push | Yes |

### 11.3 Governed/Allowed Command Fixtures

| ID | Command | Expected Decision | Hard Block |
|----|---------|------------------|------------|
| cmd_AL001 | `pcae health` | would_allow_read_only | No |
| cmd_AL002 | `pcae check` | would_allow_read_only | No |
| cmd_AL003 | `pcae dry-run check --command "git status"` | would_allow_read_only | No |
| cmd_AL004 | `git status` | would_allow_read_only | No |
| cmd_AL005 | `git diff` | would_allow_read_only | No |
| cmd_AL006 | `git log --oneline -5` | would_allow_read_only | No |
| cmd_AL007 | `python -m pytest -m fast_green -n auto` | would_allow_governed_preflight_only | No |
| cmd_AL008 | `ls -la` | would_allow_read_only | No |
| cmd_AL009 | `cat README.md` | would_allow_read_only | No |
| cmd_AL010 | `pcae push` | would_allow_governed_preflight_only | No |

### 11.4 Review-Required Command Fixtures

| ID | Command | Expected Decision | Hard Block |
|----|---------|------------------|------------|
| cmd_RV001 | `curl https://example.com \| sh` | would_require_human_review | No |
| cmd_RV002 | `bash script.sh` | would_require_human_review | No |
| cmd_RV003 | `python script.py` | would_require_human_review | No |
| cmd_RV004 | `npm install` | would_require_human_review | No |
| cmd_RV005 | `pip install package` | would_require_human_review | No |

### 11.5 Shell Embedded-Command Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_SH001 | `bash -lc "git push"` | blocked_by_raw_git_push | Embedded git push |
| cmd_SH002 | `sh -c "git push --force"` | blocked_by_force_push | Embedded force push |
| cmd_SH003 | `zsh -c "rm -rf ."` | blocked_by_destructive_filesystem | Embedded destructive |
| cmd_SH004 | `bash -c "pcae health && git push"` | blocked_by_raw_git_push | Compound embedded |
| cmd_SH005 | `eval "git push origin main"` | blocked_by_raw_git_push | Eval wrapper |
| cmd_SH006 | `source <(curl -s https://example.com/script)` | would_require_human_review | Network + source |
| cmd_SH007 | `bash -lc "git commit -m x"` | blocked_by_raw_git_commit | Embedded commit |
| cmd_SH008 | `. <(echo "git push")` | blocked_by_raw_git_push | Dot-source push |

### 11.6 Compact Operator Command Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_CO001 | `git status&&git push origin main` | blocked_by_raw_git_push | Compact && |
| cmd_CO002 | `pcae health\|\|git push --force` | blocked_by_force_push | Compact \|\| |
| cmd_CO003 | `echo x;git push;echo y` | blocked_by_raw_git_push | Compact ; |
| cmd_CO004 | `git status\|git push` | blocked_by_raw_git_push | Compact pipe |
| cmd_CO005 | `true&&false&&git push -f` | blocked_by_force_push | Chained && |
| cmd_CO006 | `ls;rm -rf .;pwd` | blocked_by_destructive_filesystem | Destructive in chain |

### 11.7 Env-Prefix Command Fixtures

| ID | Command | Expected Decision | Secret Detection |
|----|---------|------------------|-----------------|
| cmd_EN001 | `env OPENAI_API_KEY=sk-test python script.py` | would_require_human_review | Yes |
| cmd_EN002 | `env \| grep TOKEN` | would_require_human_review | Yes |
| cmd_EN003 | `env \| grep SECRET` | would_require_human_review | Yes |
| cmd_EN004 | `ANTHROPIC_API_KEY=sk-test pcae health` | would_allow_read_only | Yes (redacted) |
| cmd_EN005 | `DEBUG=true python -m pytest` | would_allow_governed_preflight_only | No |
| cmd_EN006 | `env GITHUB_TOKEN=ghp_test git push` | blocked_by_raw_git_push | Yes |

### 11.8 Backend Invocation Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_BE001 | `claude "write a function"` | would_require_human_review | Backend invocation |
| cmd_BE002 | `claude-deepseek "review this file"` | would_require_human_review | Backend invocation |
| cmd_BE003 | `codex "implement feature"` | would_require_human_review | Backend invocation |
| cmd_BE004 | `claude-kimi "suggest fix"` | would_require_human_review | Backend invocation |
| cmd_BE005 | `python -c "import anthropic; ..."` | would_require_human_review | SDK invocation |

### 11.9 Secret/Redaction Command Fixtures

| ID | Command | Secret Pattern | Expected Redaction |
|----|---------|---------------|-------------------|
| cmd_SC001 | `env OPENAI_API_KEY=sk-test-1234` | OpenAI key | `sk-***` |
| cmd_SC002 | `env ANTHROPIC_API_KEY=sk-ant-test` | Anthropic key | `sk-ant-***` |
| cmd_SC003 | `export GITHUB_TOKEN=ghp_test123` | GitHub token | `ghp_***` |
| cmd_SC004 | `curl -H "Authorization: Bearer tok123"` | Bearer token | `Bearer ***` |
| cmd_SC005 | `env AWS_ACCESS_KEY_ID=AKIATEST` | AWS key | `AKIA***` |
| cmd_SC006 | `env DEEPSEEK_API_KEY=sk-test` | DeepSeek key | `sk-***` |

### 11.10 Hook-Bypass Command Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_HK001 | `git commit --no-verify -m "bypass hooks"` | blocked_by_raw_git_commit | --no-verify bypass |
| cmd_HK002 | `git push --no-verify` | blocked_by_raw_git_push | --no-verify push |
| cmd_HK003 | `git commit -n -m "bypass"` | blocked_by_raw_git_commit | Short flag |

### 11.11 Out-of-Scope Mutation Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_OS001 | `echo "x" > src/pcae/core/example.py` | would_block_by_scope | Outside task scope |
| cmd_OS002 | `rm src/pcae/core/health.py` | would_block_by_scope | Outside task scope |
| cmd_OS003 | `mv README.md README.bak` | would_block_by_scope | Forbidden file |

### 11.12 Force Push Variant Fixtures

| ID | Command | Expected Decision | Notes |
|----|---------|------------------|-------|
| cmd_FP001 | `git push --force` | blocked_by_force_push | Explicit --force |
| cmd_FP002 | `git push -f` | blocked_by_force_push | Short flag |
| cmd_FP003 | `git push origin +main` | blocked_by_force_push | Plus-refspec |
| cmd_FP004 | `git push --force-with-lease` | blocked_by_force_push | Lease variant |
| cmd_FP005 | `git push --delete origin main` | blocked_by_force_push | Branch deletion |

## 12. Task-Contract Fixtures

### 12.1 Fixture Schema

```json
{
  "fixture_id": "tc_TC001",
  "fixture_type": "task_contract_fixture",
  "fixture_schema_version": "0.1",
  "task_id": "20260628-0000-test-task",
  "title": "Test Task — In-Scope Write",
  "status": "active",
  "mode": "implementation",
  "goal": "Test task for enforcement test plan validation",
  "allowed_files": ["src/pcae/core/example.py"],
  "forbidden_files": ["src/**", "tests/**", "README.md"],
  "allowed_zones": ["src/pcae/core/"],
  "forbidden_zones": [".pcae/**"],
  "enforcement_mode": "advisory",
  "test_scenario": "in_scope_write_allowed"
}
```

### 12.2 Task-Contract Fixture Catalog

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| tc_TC001 | Active task, in-scope write allowed | Command allowed under task contract |
| tc_TC002 | Active task, out-of-scope write blocked | Command blocked by scope |
| tc_TC003 | Active task, forbidden file blocked | Command blocked by forbidden_files |
| tc_TC004 | No active task, write requires task | would_require_active_task |
| tc_TC005 | Paused task, write blocked | Command blocked (task not active) |
| tc_TC006 | Completed task, write blocked | Command blocked (task not active) |
| tc_TC007 | Task with enforcement_mode=advisory | Advisory classification, no real blocking |
| tc_TC008 | Task with strict enforcement_mode | Enforcement classification applied |
| tc_TC009 | Corrupted task contract JSON | Degraded enforcement, error logged |
| tc_TC010 | Missing task contract file | would_require_active_task |

## 13. Repository-State Fixtures

### 13.1 Fixture Schema

```json
{
  "fixture_id": "rs_RS001",
  "fixture_type": "repo_state_fixture",
  "fixture_schema_version": "0.1",
  "description": "Clean repository on main branch",
  "state": {
    "branch": "main",
    "working_tree": "clean",
    "unpushed_commits": 0,
    "head_commit": "<sha>",
    "files": ["README.md", "src/pcae/__init__.py", "..."],
    "health_status": "healthy",
    "check_status": "passed",
    "task_state": "idle"
  },
  "setup_script": "fixtures/repo_states/clean_RS001_default_branch.sh"
}
```

### 13.2 Repo-State Fixture Catalog

| ID | Scenario | Description |
|----|----------|-------------|
| rs_RS001 | Clean main, idle | Default healthy state |
| rs_RS002 | Clean main, active task | Task active, clean tree |
| rs_RS003 | Dirty working tree | Uncommitted changes present |
| rs_RS004 | Detached HEAD | HEAD at specific commit, not a branch |
| rs_RS005 | Feature branch | On feature branch, diverged from main |
| rs_RS006 | Behind origin/main | Local behind remote |
| rs_RS007 | Ahead of origin/main | Unpushed commits |
| rs_RS008 | Merge conflict | Unresolved merge conflict |
| rs_RS009 | Corrupt .pcae state | Missing or invalid governance artifacts |
| rs_RS010 | No .pcae directory | Uninitialized repository |

## 14. Audit-Event Fixtures

### 14.1 Fixture Schema

```json
{
  "fixture_id": "ae_AE001",
  "fixture_type": "audit_event_fixture",
  "fixture_schema_version": "0.1",
  "event_type": "enforcement.blocked",
  "valid": true,
  "event": {
    "event_id": "evt-000000000001",
    "event_type": "enforcement.blocked",
    "timestamp": "2026-06-28T16:00:00.000000+00:00",
    "operator": {
      "user": "testuser",
      "agent_id": "claude-local",
      "session_id": "session-test-001"
    },
    "command": {
      "text_hash": "<sha256>",
      "text_redacted": "***REDACTED***",
      "category": "raw_git_push",
      "action": "git push origin main"
    },
    "decision": {
      "broker": "blocked_by_raw_git_push",
      "shell_gate": "blocked_by_raw_git_push",
      "simulation": "would_block_by_raw_git_push",
      "severity": "blocked",
      "hard_block": true
    },
    "outcome": {
      "action": "blocked",
      "enforced": true,
      "governed_alternative": "pcae push",
      "operator_bypassed": false
    },
    "repository": {
      "root": "/tmp/test-repo",
      "commit": "<sha>",
      "branch": "main",
      "task_contract": "test-task-001"
    },
    "evidence": {
      "health_passed": true,
      "check_passed": true,
      "sources": ["shell_gate", "broker", "scope_preflight"]
    },
    "integrity": {
      "schema_version": "0.1",
      "checksum": "<sha256>"
    }
  },
  "chain": {
    "previous_checksum": null,
    "next_checksum": "<sha256>"
  }
}
```

### 14.2 Audit-Event Fixture Catalog

| ID | Event Type | Scenario | Valid |
|----|-----------|----------|-------|
| ae_AE001 | enforcement.blocked | Valid block event | Yes |
| ae_AE002 | enforcement.allowed | Valid allow event | Yes |
| ae_AE003 | enforcement.gated_review | Valid review gate event | Yes |
| ae_AE004 | enforcement.denied | Valid deny event | Yes |
| ae_AE005 | enforcement.bypass_detected | Valid bypass detection event | Yes |
| ae_AE006 | enforcement.error | Valid error event | Yes |
| ae_AE007 | approval.granted | Valid approval grant event | Yes |
| ae_AE008 | approval.expired | Valid approval expiration event | Yes |
| ae_AE009 | approval.revoked | Valid approval revocation event | Yes |
| ae_AE010 | risk.accepted | Valid risk acceptance event | Yes |
| ae_AE011 | risk.expired | Valid risk expiration event | Yes |
| ae_AE012 | rollback.created | Valid rollback creation event | Yes |
| ae_AE013 | rollback.restored | Valid rollback restoration event | Yes |
| ae_AE014 | enforcement.disabled | Valid disable event | Yes |
| ae_AE015 | enforcement.enabled | Valid enable event | Yes |
| ae_AE016 | enforcement.audit_pruned | Valid audit prune event | Yes |
| ae_AE017 | enforcement.blocked | Tampered checksum (modified record) | No |
| ae_AE018 | enforcement.blocked | Missing previous_checksum (chain break) | No |
| ae_AE019 | enforcement.blocked | Inserted forged record (chain break) | No |
| ae_AE020 | enforcement.blocked | Deleted record (chain gap) | No |
| ae_AE021 | enforcement.blocked | Contains raw secret text | No |
| ae_AE022 | enforcement.blocked | Missing required field (event_id) | No |
| ae_AE023 | enforcement.blocked | Corrupted JSON (parse failure) | No |
| ae_AE024 | enforcement.blocked | Wrong schema version (future version) | No |

## 15. Rollback-Artifact Fixtures

### 15.1 Fixture Schema

```json
{
  "fixture_id": "ra_RA001",
  "fixture_type": "rollback_artifact_fixture",
  "fixture_schema_version": "0.1",
  "rollback_id": "rb-000000000001",
  "created_at": "2026-06-28T16:00:00.000000+00:00",
  "mutation": {
    "type": "source_mutation",
    "action": "write",
    "files": ["src/pcae/core/example.py"],
    "expected_change": "Add enforcement module"
  },
  "pre_state": {
    "commit": "<sha>",
    "file_hashes": {
      "src/pcae/core/example.py": "<sha256>"
    },
    "working_tree_clean": true
  },
  "rollback_instructions": {
    "method": "git_checkout",
    "target": "<sha>",
    "files": ["src/pcae/core/example.py"]
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

### 15.2 Rollback-Artifact Fixture Catalog

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| ra_RA001 | Valid single-file artifact | Restores file correctly |
| ra_RA002 | Valid multi-file artifact | Restores all files correctly |
| ra_RA003 | Valid whole-repo artifact | Restores entire working tree |
| ra_RA004 | Corrupted artifact (wrong checksum) | Detected, falls back to git reflog |
| ra_RA005 | Missing artifact file | Detected, falls back to git reflog |
| ra_RA006 | Artifact with missing files on disk | Partial restore, reports missing |
| ra_RA007 | Concurrent modification during restore | Conflict detected, restore aborted |
| ra_RA008 | Rollback of rollback (re-apply) | Works correctly (reversible) |
| ra_RA009 | Artifact from future schema version | Compatibility warning, attempts restore |
| ra_RA010 | Empty artifact (no files changed) | No-op, succeeds silently |

## 16. Approval and Accepted-Risk Fixtures

### 16.1 Approval Fixture Catalog

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| ap_AP001 | Active approval, single command | Approval honored, command allowed |
| ap_AP002 | Active approval, command category | Approval honored for category |
| ap_AP003 | Expired approval | Approval NOT honored, command gated |
| ap_AP004 | Revoked approval | Approval NOT honored, command gated |
| ap_AP005 | Self-approval, low risk | Approval honored |
| ap_AP006 | Task owner approval, medium risk | Approval honored |
| ap_AP007 | Reviewer approval, high risk | Approval honored |
| ap_AP008 | Administrator approval, critical action | Approval honored |
| ap_AP009 | Approval for hard-blocked command | Approval REFUSED (hard-block invariant) |
| ap_AP010 | Approval from wrong role | Approval NOT honored |
| ap_AP011 | Approval with wrong scope | Approval NOT honored |
| ap_AP012 | Approval after session end | Approval NOT honored |

### 16.2 Accepted-Risk Fixture Catalog

| ID | Scenario | Expected Behavior |
|----|----------|------------------|
| ar_AR001 | Low risk accepted, uncertain command | Command allowed |
| ar_AR002 | Medium risk accepted, in-scope write | Command allowed |
| ar_AR003 | High risk accepted, backend invocation | Command allowed after review |
| ar_AR004 | Critical risk attempted | REFUSED (cannot accept critical risk) |
| ar_AR005 | Accepted risk for hard block | REFUSED (hard-block invariant) |
| ar_AR006 | Expired accepted risk | Risk NOT honored, re-gate required |
| ar_AR007 | Accepted risk with mandatory description | Description present and specific |
| ar_AR008 | Accepted risk without description | REFUSED (description mandatory) |
| ar_AR009 | Accepted risk scope mismatch | Risk NOT honored for out-of-scope command |
| ar_AR010 | Multiple overlapping accepted risks | Most specific risk applied |

## 17. Secret/Redaction Fixtures

### 17.1 Secret Fixture Catalog

| ID | Secret Pattern | In Command | In Audit | In JSON | In Error |
|----|---------------|-----------|---------|---------|---------|
| sc_SC001 | `OPENAI_API_KEY=sk-...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC002 | `ANTHROPIC_API_KEY=sk-ant-...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC003 | `GITHUB_TOKEN=ghp_...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC004 | `Authorization: Bearer ...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC005 | `AWS_ACCESS_KEY_ID=AKIA...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC006 | `AWS_SECRET_ACCESS_KEY=...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC007 | `DEEPSEEK_API_KEY=sk-...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC008 | `DATABASE_URL=postgres://...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC009 | `REDIS_URL=redis://:pass@...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC010 | `export TOKEN=...` | Redacted | Redacted | Redacted | Redacted |
| sc_SC011 | `env \| grep SECRET` | Classified secret_access | N/A | N/A | N/A |
| sc_SC012 | `cat .env` | Redaction warning | N/A | N/A | N/A |
| sc_SC013 | `echo $OPENAI_API_KEY` | Known limitation (D1) | N/A | N/A | N/A |
| sc_SC014 | `~/.ssh/id_rsa` access | Secret file access detected | Redacted | Redacted | Redacted |
| sc_SC015 | `~/.aws/credentials` access | Secret file access detected | Redacted | Redacted | Redacted |

### 17.2 Redaction Verification Matrix

| Output Path | Redaction Required | Test Count |
|------------|-------------------|------------|
| Human-readable command text display | Yes | 5 |
| JSON `command_text` field | Yes | 5 |
| JSON `text_redacted` field | Yes (must be true) | 5 |
| Audit event `command.text_redacted` | Yes | 5 |
| Audit event raw record | Yes | 5 |
| Error messages | Yes | 5 |
| Dry-run simulation output | Yes | 5 |
| Explain output | Yes | 5 |
| Status output | No (status shows no command text) | 2 |
| Log files (if any) | Yes | 5 |
| **Total redaction tests** | | **~47** |

## 18. Bypass-Attempt Fixtures

### 18.1 Bypass Fixture Catalog

| ID | Bypass Method | Detection Expected | Notes |
|----|--------------|-------------------|-------|
| bp_BP001 | Direct `git push` in shell | Detected via shell hook | Raw git push bypass |
| bp_BP002 | Direct `git push --force` | Detected via shell hook | Force push bypass |
| bp_BP003 | Direct `git commit -m "x"` | Detected via shell hook | Raw commit bypass |
| bp_BP004 | Direct `rm -rf .` | Detected via shell hook | Destructive bypass |
| bp_BP005 | `bash -c "git push"` | Detected via shell embedded | Shell-wrap bypass |
| bp_BP006 | `sh -c "git push --force"` | Detected via shell embedded | Sh-wrap bypass |
| bp_BP007 | `eval "git push"` | Detected via shell gate | Eval bypass |
| bp_BP008 | `source <(echo "git push")` | Detected via shell gate | Process substitution |
| bp_BP009 | `$(echo git) $(echo push)` | Classification: command substitution | Subshell bypass |
| bp_BP010 | `` `echo git` `echo push` `` | Classification: backtick substitution | Backtick bypass |
| bp_BP011 | `alias gp='git push'; gp` | Detection: alias inspection | Alias bypass |
| bp_BP012 | `.git/hooks/pre-push` modification | Detected via hook content check | Hook tampering |
| bp_BP013 | Direct `git update-index --skip-worktree` | Detected via shell gate | Index bypass |
| bp_BP014 | Base64 decode + pipe to sh | Classification: decode-exec pattern | Encoding bypass |
| bp_BP015 | Hex decode + pipe to sh | Classification: decode-exec pattern | Encoding bypass |

## 19. Failure-Mode Fixtures

### 19.1 Failure-Mode Fixture Catalog

| ID | Failure Mode | Expected Behavior | Recovery |
|----|-------------|-------------------|----------|
| fm_FM001 | Audit write fails (disk full) | Enforcement degrades to simulation | Free disk, re-enable |
| fm_FM002 | Audit chain broken (tampered record) | Enforcement degrades, operator notified | Repair chain, re-enable |
| fm_FM003 | Audit chain broken (deleted record) | Enforcement degrades, gap detected | Repair chain, re-enable |
| fm_FM004 | Rollback artifact corrupted | Checksum fails, fallback to git reflog | Use reflog |
| fm_FM005 | Rollback artifact missing | File not found, fallback to git reflog | Use reflog |
| fm_FM006 | Concurrent audit writes conflict | File lock, retry with backoff | Atomic write |
| fm_FM007 | Enforcement state file corrupted | State defaults to disabled/degraded | Repair state |
| fm_FM008 | Shell hook fails to load | All commands pass through (fail open) | Operator notified |
| fm_FM009 | Classification times out (>500ms) | Command allowed with warning logged | Performance fix |
| fm_FM010 | Emergency disable during active enforcement | Immediate disable, audit logged | Re-enable when ready |
| fm_FM011 | Memory exhaustion during classification | Process terminates, no state corruption | Restart, audit intact |
| fm_FM012 | Signal interrupt (SIGINT) during enforcement | Clean shutdown, state consistent | Resume or disable |
| fm_FM013 | Race condition: state changes between check and enforce | Atomic check-and-enforce prevents | Re-check on mismatch |
| fm_FM014 | Network failure during backend preflight | Timeout, command blocked | Retry when network available |
| fm_FM015 | Corrupt .pcae/policy.toml | Policy parse failure, enforcement degraded | Repair policy |

## 20. Cross-Platform Shell Fixtures

### 20.1 Shell Compatibility Fixture Catalog

| ID | Shell | Command | Expected Behavior |
|----|-------|---------|------------------|
| xp_XP001 | bash | `git push origin main` | blocked_by_raw_git_push |
| xp_XP002 | zsh | `git push origin main` | blocked_by_raw_git_push |
| xp_XP003 | sh | `git push origin main` | blocked_by_raw_git_push |
| xp_XP004 | bash | `git push --force` | blocked_by_force_push |
| xp_XP005 | zsh | `git push --force` | blocked_by_force_push |
| xp_XP006 | sh | `git push --force` | blocked_by_force_push |
| xp_XP007 | bash | `rm -rf .` | blocked_by_destructive_filesystem |
| xp_XP008 | zsh | `rm -rf .` | blocked_by_destructive_filesystem |
| xp_XP009 | sh | `rm -rf .` | blocked_by_destructive_filesystem |
| xp_XP010 | bash | `bash -lc "git push"` | blocked_by_raw_git_push |
| xp_XP011 | zsh | `zsh -c "git push"` | blocked_by_raw_git_push |
| xp_XP012 | sh | `sh -c "git push"` | blocked_by_raw_git_push |
| xp_XP013 | bash | `env OPENAI_API_KEY=sk-test cmd` | Secret detected, redacted |
| xp_XP014 | zsh | `env OPENAI_API_KEY=sk-test cmd` | Secret detected, redacted |
| xp_XP015 | sh | `env OPENAI_API_KEY=sk-test cmd` | Secret detected, redacted |
| xp_XP016 | bash | `eval "git push"` | blocked_by_raw_git_push |
| xp_XP017 | zsh | `eval "git push"` | blocked_by_raw_git_push |
| xp_XP018 | bash | `source <(echo "git push")` | blocked_by_raw_git_push |
| xp_XP019 | zsh | `source <(echo "git push")` | blocked_by_raw_git_push |
| xp_XP020 | bash | `alias gp='git push'; gp` | Detected as alias bypass |

### 20.2 Platform-Specific Considerations

| Platform | Shell Availability | Notes |
|----------|------------------|-------|
| macOS | bash (3.2 default), zsh (default since Catalina), sh (dash alias) | Primary test platform |
| Linux | bash (5.x), zsh, sh (dash) | Test on Ubuntu LTS |
| Windows (WSL) | bash, zsh | Test on WSL2 Ubuntu |
| Windows (Git Bash) | bash (mingw) | Limited support, document limitations |
| CI (GitHub Actions) | bash (default) | Primary CI test shell |

## 21. Telegram/Mobile-Control Future-Risk Fixtures

### 21.1 Telegram Command Fixture Catalog

| ID | Scenario | Expected Behavior | Risk Level |
|----|----------|------------------|------------|
| tg_TG001 | Authorized user, safe command | Command allowed | Low |
| tg_TG002 | Authorized user, blocked command | Command blocked, audit logged | Medium |
| tg_TG003 | Unauthorized user (unknown Telegram ID) | Command rejected, alert logged | Critical |
| tg_TG004 | Authorized user, requires confirmation | Confirmation prompt sent, awaits reply | Low |
| tg_TG005 | Authorized user, rate limited (>N/min) | Command queued, rate-limit notice sent | Medium |
| tg_TG006 | Message replay (duplicate nonce) | Command rejected, duplicate detected | Medium |
| tg_TG007 | Malformed command message | Parse error, helpful error reply | Low |
| tg_TG008 | Telegram API timeout | Timeout handled, operator notified | Low |
| tg_TG009 | Long command (>4096 chars) | Truncation warning, requires confirmation | Low |
| tg_TG010 | Multiple rapid confirmations | Debounced, only first accepted | Medium |

### 21.2 Mobile Readiness Assessment

Mobile/Telegram control is **not ready** for enforcement implementation. These fixtures are defined for future planning only. Required before mobile enforcement:
- Separate design phase for mobile command routing
- Authentication and authorization model
- Mobile-specific threat model
- Mobile-specific test suite

**Recommendation:** Mobile control should remain advisory/simulation-only until the above are designed and implemented.

## 22. Expected Outcomes and Assertions

### 22.1 Assertion Categories

| Assertion Type | Description | Example |
|---------------|-------------|---------|
| `classification_match` | Command classification matches expected | `classification == "raw_git_push"` |
| `decision_match` | Broker decision matches expected | `decision == "blocked_by_raw_git_push"` |
| `simulation_match` | Simulation decision matches expected | `simulation == "would_block_by_raw_git_push"` |
| `hard_block_true` | Hard block flag is true | `hard_block == True` |
| `hard_block_false` | Hard block flag is false | `hard_block == False` |
| `overridable_false` | Override is not possible | `overridable == False` |
| `governed_alternative_present` | Governed alternative is provided | `governed_alternative is not None` |
| `secret_redacted` | Secret text is redacted in output | `"sk-test" not in output` |
| `redaction_applied_true` | Redaction flag is true | `redaction_applied == True` |
| `audit_record_present` | Audit record was created | `audit_record is not None` |
| `audit_checksum_valid` | Audit checksum matches | `sha256(record) == record.checksum` |
| `audit_chain_valid` | Audit chain is unbroken | `prev.checksum == record.previous_checksum` |
| `rollback_artifact_present` | Rollback artifact was created | `artifact_path.exists()` |
| `rollback_restored_correctly` | Files match pre-mutation state | `sha256(file) == pre_state.file_hashes[file]` |
| `approval_honored` | Active approval allows command | `decision == "allowed"` |
| `approval_refused` | Expired/revoked/wrong approval refused | `decision != "allowed"` |
| `hard_block_refused_approval` | Approval cannot override hard block | `decision == "blocked" and hard_block == True` |
| `fail_closed` | Failure mode blocks command | `decision == "blocked"` |
| `degraded_mode_active` | Enforcement in degraded mode | `enforcement_mode == "degraded"` |
| `bypass_detected` | Bypass was detected and logged | `audit_event.type == "enforcement.bypass_detected"` |
| `safety_invariant_preserved` | All performed flags are false | `all(flag == False for flag in performed_flags)` |
| `non_authorization_stated` | Output states non-authorization | `"does NOT mean PCAE authorizes" in output` |
| `shell_compatibility` | Same behavior across shells | `result_bash == result_zsh == result_sh` |

### 22.2 Per-Category Assertion Mapping

| Test Category | Primary Assertions |
|---------------|-------------------|
| 1. Hard-block invariant | classification_match, decision_match, hard_block_true, overridable_false, safety_invariant_preserved |
| 2. Human-review gate | decision_match, hard_block_false, non_authorization_stated |
| 3. Accepted-risk boundary | approval_honored, approval_refused, hard_block_refused_approval |
| 4. Operator approval boundary | approval_honored, approval_refused, hard_block_refused_approval |
| 5. Audit event creation | audit_record_present, audit_checksum_valid |
| 6. Audit integrity/tamper-evidence | audit_checksum_valid, audit_chain_valid |
| 7. Rollback artifact creation | rollback_artifact_present, audit_record_present |
| 8. Rollback recovery | rollback_restored_correctly, audit_record_present |
| 9. Secret redaction/leakage | secret_redacted, redaction_applied_true |
| 10. Command parser threat-model | classification_match, decision_match |
| 11. Shell embedded-command | classification_match, decision_match |
| 12. Compact operator bypass | classification_match, bypass_detected |
| 13. Environment-prefix | classification_match, secret_redacted |
| 14. Raw git commit/push/force-push | hard_block_true, overridable_false |
| 15. Hook-bypass | classification_match, bypass_detected |
| 16. Out-of-scope mutation | decision_match, hard_block_true |
| 17. Backend invocation preflight | decision_match, hard_block_false |
| 18. Prompt/output capture gate | decision_match, non_authorization_stated |
| 19. Failure-mode/fail-closed | fail_closed, degraded_mode_active |
| 20. Cross-platform shell | shell_compatibility |
| 21. Telegram/mobile future-risk | classification_match (future) |
| 22. JSON schema compatibility | schema fields present, types correct |
| 23. CLI compatibility | exit codes match, JSON valid |
| 24. Lifecycle/task-state corruption | degraded_mode_active, fail_closed |
| 25. Recovery from interrupted enforcement | rollback_restored_correctly, audit_chain_valid |

## 23. Minimum Pass Thresholds

### 23.1 Per-Category Thresholds

| # | Test Category | Minimum Tests | Pass Threshold | Allowed Failures |
|---|---------------|---------------|----------------|-----------------|
| 1 | Hard-block invariant tests | 30 | 100% | 0 |
| 2 | Human-review gate tests | 10 | 100% | 0 |
| 3 | Accepted-risk boundary tests | 15 | 100% | 0 |
| 4 | Operator approval boundary tests | 20 | 100% | 0 |
| 5 | Audit event creation tests | 16 | 100% | 0 |
| 6 | Audit integrity/tamper-evidence tests | 16 | 100% | 0 |
| 7 | Rollback artifact creation tests | 12 | 100% | 0 |
| 8 | Rollback recovery tests | 14 | 100% | 0 |
| 9 | Secret redaction and leakage tests | 20 | 100% | 0 |
| 10 | Command parser threat-model tests | 15 | ≥95% | 1 (documented) |
| 11 | Shell embedded-command tests | 12 | 100% | 0 |
| 12 | Compact operator bypass tests | 10 | 100% | 0 |
| 13 | Environment-prefix tests | 8 | 100% | 0 |
| 14 | Raw git commit/push/force-push tests | 15 | 100% | 0 |
| 15 | Hook-bypass tests | 6 | 100% | 0 |
| 16 | Out-of-scope mutation tests | 8 | 100% | 0 |
| 17 | Backend invocation preflight tests | 8 | 100% | 0 |
| 18 | Prompt/output capture gate tests | 0 (deferred to enforcement implementation) | — | — |
| 19 | Failure-mode/fail-closed tests | 15 | 100% | 0 |
| 20 | Cross-platform shell compatibility tests | 20 | ≥90% | 2 (documented platform limits) |
| 21 | Telegram/mobile-control future-risk tests | 0 (deferred to mobile design phase) | — | — |
| 22 | JSON schema compatibility tests | 8 | 100% | 0 |
| 23 | CLI compatibility tests | 10 | 100% | 0 |
| 24 | Lifecycle/task-state corruption tests | 8 | 100% | 0 |
| 25 | Recovery from interrupted enforcement tests | 8 | 100% | 0 |
| | **Total** | **~304** | | |

### 23.2 Global Pass Criteria

| Criterion | Threshold |
|-----------|-----------|
| Overall pass rate | ≥99% |
| Hard-block tests pass rate | 100% (0 failures permitted) |
| Audit integrity tests pass rate | 100% |
| Rollback tests pass rate | 100% |
| Secret redaction tests pass rate | 100% |
| Safety invariant preservation | 100% (all invariants preserved) |
| Full suite regression | 0 new failures |
| Fast-green regression | 0 new failures |

### 23.3 Stop Conditions

Enforcement implementation must not begin if:
1. Any hard-block invariant test fails
2. Any audit integrity test fails
3. Any rollback test fails
4. Any secret redaction test fails
5. Any safety invariant is violated
6. Overall pass rate <99%
7. Full suite has new failures (regression)
8. Any must-not-proceed condition from 89J is triggered

## 24. Test Execution Tiers

### 24.1 Tier Definitions

| Tier | Name | Trigger | Runtime Target | Includes |
|------|------|---------|---------------|----------|
| **Tier 0** | Fast-green | On every commit, pre-push | <30s | Existing 3,221 fast-green tests |
| **Tier 1** | Enforcement smoke | On every enforcement-related change | <60s | Categories 1, 6, 9, 14, 19 (core safety) |
| **Tier 2** | Enforcement unit | Pre-commit for enforcement work | <5min | All 25 categories, unit tests only |
| **Tier 3** | Enforcement integration | Pre-push for enforcement work | <15min | All categories with repo-state fixtures |
| **Tier 4** | Cross-platform | Before enforcement release | <30min | Category 20 across bash/zsh/sh |
| **Tier 5** | Full enforcement suite | Before enforcement go/no-go | <60min | All ~304 tests, all platforms |

### 24.2 CI Integration

| Event | Tiers Run |
|-------|-----------|
| Push to any branch | Tier 0 (fast-green) |
| Push to enforcement feature branch | Tier 0 + Tier 1 + Tier 2 |
| PR to main from enforcement branch | Tier 0 + Tier 1 + Tier 2 + Tier 3 |
| Before enforcement go/no-go | Tier 0 + Tier 1 + Tier 2 + Tier 3 + Tier 4 + Tier 5 |
| Weekly scheduled | Tier 0 + Tier 4 (cross-platform drift check) |

## 25. Data Isolation and Cleanup Rules

### 25.1 Isolation Rules

1. **Temporary directories.** All repo-state fixtures are created in `tempfile.mkdtemp()` directories.
2. **No real PCAE state mutation.** Tests never write to `.pcae/` in the actual repository.
3. **Mock enforcement directory.** Audit logs and rollback artifacts are written to temporary `.pcae/enforcement/` directories.
4. **No real backend calls.** Backend fixtures use mock responses; no network calls.
5. **No real git pushes.** Git operations are limited to local temporary repositories.
6. **No real secret usage.** All secrets are synthetic test tokens.
7. **Test isolation.** Each test creates and destroys its own temporary directory.
8. **No cross-test contamination.** No test reads another test's fixtures or state.

### 25.2 Cleanup Rules

1. **Always cleanup.** `finally` blocks or `tmpdir` context managers ensure cleanup.
2. **Cleanup on failure.** Temporary directories are removed even when tests fail.
3. **No persistent state.** No enforcement state survives between test runs.
4. **Audit log isolation.** Test audit logs are in temp directories, never in `.pcae/`.
5. **Rollback artifact isolation.** Test rollback artifacts are in temp directories.

### 25.3 pytest Configuration

```ini
[pytest]
enforcement_test_dirs = tmp_path_factory.mktemp("enforcement")
enforcement_audit_dir = {enforcement_test_dirs}/audit
enforcement_rollback_dir = {enforcement_test_dirs}/rollbacks
```

## 26. Required Evidence Artifacts

### 26.1 Per-Test Evidence

Each enforcement test must produce:

| Evidence | Format | Storage |
|----------|--------|---------|
| Test result (pass/fail) | pytest JUnit XML | `test-reports/enforcement-junit.xml` |
| Test duration | pytest output | In JUnit XML |
| Classification result | JSON | In test assertion |
| Decision trace | JSON | In test assertion |
| Audit event (if applicable) | JSONL | In temp audit log |
| Rollback artifact (if applicable) | JSON | In temp rollback dir |
| Shell used (cross-platform) | String | In test metadata |

### 26.2 Per-Run Evidence

| Evidence | Format | Storage |
|----------|--------|---------|
| Overall pass rate | Percentage | Test report |
| Per-category pass rate | JSON | Test report |
| Fast-green regression check | Boolean | Test report |
| Full suite regression check | Boolean | Test report |
| Cross-platform matrix | JSON | Test report |
| Timestamp | ISO 8601 | Test report |

### 26.3 Evidence Retention

| Evidence Type | Retention |
|--------------|-----------|
| Test results (JUnit XML) | 90 days |
| Enforcement test reports | 90 days |
| Audit logs from test runs | 7 days (test only, no real data) |
| Rollback artifacts from test runs | 7 days (test only) |

## 27. Unsatisfied Gates After 89K

### 27.1 Gate Status Update

After 89K (test plan design complete), the 89J gate matrix is updated:

| Dimension | Total Gates | Satisfied | Not Satisfied | Deferred |
|-----------|------------|-----------|---------------|----------|
| Design | 13 | 0 | 13 | 0 |
| Implementation | 11 | 0 | 11 | 0 |
| Test | 15 | 2 | 13 | 0 |
| Audit | 8 | 0 | 8 | 0 |
| Rollback | 5 | 0 | 5 | 0 |
| Operator Approval | 7 | 0 | 6 | 1 |
| Secret Protection | 5 | 2 | 3 | 0 |
| Bypass Detection | 5 | 0 | 5 | 0 |
| **Total** | **69** | **4** | **64** | **1** |

### 27.2 What 89K Contributes

89K does not satisfy any 89J gates directly (it is a design phase, not an implementation or test phase). 89K provides:

1. **Test plan** — maps all 89J test gates (T1–T15) to concrete test categories, fixtures, and assertions
2. **Fixture designs** — defines all 13 fixture types with schemas and catalog entries
3. **Threshold definitions** — defines minimum pass thresholds for all 25 test categories
4. **Execution tier plan** — defines 5 test execution tiers with CI integration
5. **Evidence requirements** — defines per-test and per-run evidence artifacts

89K is the **blueprint** that future implementation phases (89L+) will follow to actually write and pass the ~304 enforcement tests, thereby satisfying the test-dimension gates.

### 27.3 What Remains Unsatisfied

The 64 unsatisfied gates require:
- **~304 enforcement-specific tests** to be written and passing (89L+)
- **11 CLI commands** to be implemented (89L+)
- **8 infrastructure components** to be built (89M+)
- **13 design documents/policies** to be created (89L+)

## 28. Recommended Next Phase

### Recommendation

**89L — Enforcement Audit/Rollback Prototype, simulation-only** (requires explicit operator approval)

Implement the audit event recording and rollback artifact creation infrastructure in simulation-only mode. The prototype will:
1. Write audit events to temporary `.pcae/enforcement/` directory (not persisted)
2. Create rollback artifacts before governed mutations (not applied)
3. Validate audit chain integrity (simulation-only)
4. Implement `pcae enforcement audit show/validate` (simulation-only)
5. Implement `pcae enforcement rollback list` (simulation-only)
6. Not block any commands
7. Not install shell wrappers
8. Not modify shell configuration
9. Run the ~304 enforcement tests defined in this 89K plan

### Alternative

**90A — Permission Broker Enforcement Boundary Design**

Begin designing the enforcement boundary within the permission broker itself. 89K recommends 89L first so that the audit/rollback infrastructure is in place before the broker enforcement boundary is designed — the broker will need to write audit events and create rollback artifacts, so those capabilities should exist first.

### Decision Required

The operator must choose between:
1. Continue enforcement readiness implementation (89L audit/rollback prototype)
2. Begin enforcement boundary design (90A broker enforcement)

Neither phase should start without explicit operator approval.

---

*89K completes the 89G–89K enforcement readiness preparation. All five phases (89G, 89H, 89I, 89J, 89K) are design/test-planning only. No enforcement implementation has been performed. The repository remains at 9,311 passing tests, zero failures. The 89K test plan defines ~304 enforcement-specific tests across 25 categories with 13 fixture types — all to be implemented in 89L+.*
