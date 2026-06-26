# Phase 88S — Broker + Shell Gate Integration Design

```
broker_shell_gate_integration_design_name    = phase_88_broker_shell_gate_integration_design
broker_shell_gate_integration_design_version = 0.1
broker_shell_gate_integration_design_status  = draft_documented
implementation_status                        = not_started
recommended_next_phase                       = 88T_broker_shell_gate_integration_prototype
```

## 1. Purpose

Define how the permission broker prototype (`src/pcae/core/permission_broker.py`, Phase 88R)
should consume and interpret read-only shell-gate evidence (`src/pcae/core/shell_gate.py`,
Phases 88P/88Q) in a future integration prototype phase (88T). This document specifies
integration boundaries, evidence fields, decision mapping, category mapping, hard-block
propagation, audit requirements, active-task behavior, malformed evidence handling, and
safety invariants.

This is a design document. Nothing is implemented here.

## 2. Scope

In scope (design only):
- Evidence flow from shell gate into broker
- Shell-gate decision → broker decision mapping (26 → 24)
- Shell-gate category → broker decision implications (24 categories)
- Hard-block propagation rules
- Non-hard-block shell-gate decision handling
- Missing/malformed evidence behavior
- Conflicting evidence detection
- Human approval and accepted-risk limits
- Active-task and no-active-task behavior
- Audit model for integrated output
- Security requirements
- Implementation sequence for 88T

Out of scope:
- Implementing any of the above
- Modifying `src/pcae/core/permission_broker.py`
- Modifying `src/pcae/core/shell_gate.py`
- Shell interception or shell wrapper installation
- Shell configuration modification
- Backend invocation
- Prompt sending, output capture, intake, adoption
- Granting execution authorization
- Writing persistent broker/shell-gate state or cache
- Phase 88T task contract

## 3. Non-Goals

This design must not:
- Change broker decision priority as defined in 88R without explicit justification
- Weaken no-active-task blocking
- Allow shell-gate evidence to bypass human-review gates
- Allow accepted-risk or human-approval to override unconditional hard blocks
- Introduce execution authorization in any form
- Require broker to execute classified commands to verify classification

## 4. Starting Point

### 4.1 Shell Gate Evidence (88P/88Q)

`build_shell_gate(repo_root, command_text)` → `build_shell_gate_envelope` returns:

```
schema_version       : "0.1"
generated_at         : ISO timestamp
source_command       : "pcae shell-gate check"
repository_root      : path
gate: {
  gate_type          : "shell_gate_prototype"
  command_text       : str
  command_category   : one of 24 SGP_CATEGORIES
  decision           : one of 26 SGP_DECISIONS
  reason_codes       : list[str]
  hard_block_present : bool
  active_task_detected: bool
  requires_active_task: bool
  requires_preflight : bool
  requires_human_review: bool
  requires_more_evidence: bool
  test_run_preflight_required: bool
  test_run_clear_to_run: bool | null
  policy_forbidden_file_detected: bool
  raw_git_push_detected: bool
  force_push_detected : bool
  destructive_filesystem_detected: bool
  backend_invocation_detected: bool
  secret_access_detected: bool
  environment_mutation_detected: bool
  detected_flags      : dict[str, bool]  (all 21 flags)
  safety_notes        : dict[str, bool]  (all performed flags false)
}
```

`_classify_command(command_text)` returns the raw classification:
```
{
  command_category : str
  reason_codes     : list[str]
  detected_flags   : dict[str, bool]
}
```

`_decide(category, detected_flags, active_task_detected, test_run_clear)` returns:
```
(decision: str, reason_codes: list[str])
```

### 4.2 Current Broker Shell-Gate Consumption (88R)

The 88R broker already calls `_classify_command` and `_decide` internally and consumes
shell-gate results via `_SG_HARD_BLOCK_TO_BROKER`. Current hard-block mapping:

```python
_SG_HARD_BLOCK_TO_BROKER = {
    "blocked_by_raw_git_commit":         "blocked_by_shell_gate",
    "blocked_by_raw_git_push":           "blocked_by_raw_git_push",
    "blocked_by_force_push":             "blocked_by_force_push",
    "blocked_by_history_rewrite":        "blocked_by_shell_gate",
    "blocked_by_destructive_filesystem": "blocked_by_shell_gate",
    "blocked_by_policy_forbidden_file":  "blocked_by_shell_gate",
    "blocked_by_backend_policy":         "blocked_by_backend_policy",
    "blocked_by_prompt_policy":          "blocked_by_shell_gate",
    "blocked_by_adoption_policy":        "blocked_by_shell_gate",
    "blocked_by_test_run_lock":          "blocked_by_test_run_lock",
    "blocked_by_unknown_command":        "blocked_by_shell_gate",
    "deny":                              "deny",
}
```

Non-hard-block shell-gate decisions (`requires_human_review`, `requires_preflight`,
`requires_active_task`, `requires_more_evidence`) are partially handled in step 6 of
`_broker_decide` but not yet fully mapped or validated against the shell-gate field model.

### 4.3 Gaps Identified

The following gaps exist between 88R and full integration (to be closed in 88T):

1. **No schema version check** — broker does not verify `sg_evidence["schema_version"]`
2. **No malformed-evidence detection** — broker does not check for impossible states (e.g., any performed flag true, conflicting decision/category, unknown category with allow decision)
3. **Non-hard-block decisions partially mapped** — `requires_human_review` from sg drives human-review gate (step 7) but `requires_preflight` and `requires_active_task` only reach `missing_evidence` list (step 6), without distinct broker reason codes
4. **`blocked_by_missing_task` not in `_SG_HARD_BLOCK_TO_BROKER`** — currently falls through to step 6 missing evidence; should be a hard block when no task present
5. **Category-level broker mapping undefined** — broker knows decision but not category; category provides richer audit/reason information
6. **Command text in shell-gate evidence is raw** — if command contains secret arguments (passwords, API keys), storing it verbatim in broker output poses redaction risk
7. **Contradiction detection absent** — broker does not detect when shell gate says `allow_read_only` but broker action is `source_mutation`, or when category is `unknown` but decision is `allow_read_only`
8. **`accepted_risk_present` not mapped to shell-gate evidence** — accepted risk currently applies to broker-level actions only; no definition of how it interacts with shell-gate blocks

## 5. Evidence Flow Design

### 5.1 Shell-Gate Evidence Fields the Broker Should Consume

When `requested_command` is present, the broker must collect shell-gate evidence and
consume the following fields. Fields prefixed `sg.` refer to the shell gate output.

**Required consumption:**
```
sg.schema_version                    — validate == "0.1"; reject if missing/wrong
sg.command_category                  — map to broker reason codes and audit
sg.decision                          — map to broker decision (see §6)
sg.reason_codes                      — pass through to broker reason_codes
sg.hard_block_present                — if True, broker hard_block_present must be True
sg.requires_active_task              — if True and no task → hard block
sg.requires_preflight                — if True and scope evidence absent → missing evidence
sg.requires_human_review             — if True → broker requires human_review_present
sg.requires_more_evidence            — if True → broker missing_evidence += item
sg.test_run_preflight_required       — if True → broker records test_run evidence
sg.test_run_clear_to_run             — if False → blocked_by_test_run_lock
sg.policy_forbidden_file_detected    — must be reflected in hard_block_present=True
sg.raw_git_push_detected             — must be reflected in hard_block_present=True
sg.force_push_detected               — must be reflected in hard_block_present=True
sg.destructive_filesystem_detected   — must be reflected in hard_block_present=True
sg.backend_invocation_detected       — broker notes; requires human review
sg.secret_access_detected            — broker notes; command text must not be stored raw
sg.environment_mutation_detected     — broker notes; requires preflight
```

**All detected_flags must be inspected individually** — broker must not rely solely on
the top-level decision when a more specific flag signals a hard block.

**Fields the broker must NOT trust blindly:**
- `sg.detected_flags["command_executed"]` — shell gate never executes; if True, evidence is malformed
- `sg.detected_flags["*_performed"]` — shell gate never performs actions; any True value is malformed
- `sg.decision = "allow_read_only"` when `sg.command_category` is a mutating category (contradiction)
- Any allow decision (`allow_*`) when `sg.hard_block_present = True` (contradiction)
- `sg.schema_version` missing or not matching expected

### 5.2 Fields the Broker Must Not Consume From Shell Gate

The broker must not propagate the following from shell gate output into broker authorization:
- `sg.gate["authorization_granted"]` — shell gate never grants authorization; any True is malformed
- `sg.gate["execution_authorized"]` — same
- Raw command text when `sg.secret_access_detected = True` — redact or hash

### 5.3 Evidence Sources Record

The integrated broker envelope should include shell-gate evidence as a named source:
```
"pcae shell-gate classifier (internal)"  — already present in 88R
```

In 88T, add:
```
"pcae shell-gate category:{command_category}"  — include category in evidence source label
```

## 6. Decision Mapping: Shell-Gate Decision → Broker Decision

The following table defines the required mapping from shell-gate decisions (26 values)
to broker decisions (24 values). Priority column indicates where in `_broker_decide` the
mapping fires.

| Shell Gate Decision               | Broker Decision                  | Priority | Hard Block |
|-----------------------------------|----------------------------------|----------|------------|
| `blocked_by_force_push`           | `blocked_by_force_push`          | 1 (SG)   | Yes        |
| `blocked_by_raw_git_push`         | `blocked_by_raw_git_push`        | 1 (SG)   | Yes        |
| `blocked_by_raw_git_commit`       | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `blocked_by_history_rewrite`      | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `blocked_by_destructive_filesystem` | `blocked_by_shell_gate`        | 1 (SG)   | Yes        |
| `blocked_by_policy_forbidden_file`| `blocked_by_scope`               | 1 (SG)   | Yes        |
| `blocked_by_backend_policy`       | `blocked_by_backend_policy`      | 1 (SG)   | Yes        |
| `blocked_by_prompt_policy`        | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `blocked_by_adoption_policy`      | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `blocked_by_test_run_lock`        | `blocked_by_test_run_lock`       | 1 (SG)   | Yes        |
| `blocked_by_unknown_command`      | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `blocked_by_missing_task`         | `blocked_by_task_contract`       | 1 (SG)   | Yes        |
| `blocked_by_scope`                | `blocked_by_scope`               | 1 (SG)   | Yes        |
| `blocked_by_failed_health`        | `blocked_by_failed_health`       | 2        | Yes        |
| `blocked_by_failed_check`         | `blocked_by_failed_check`        | 2        | Yes        |
| `blocked_by_failed_doctor`        | `blocked_by_failed_doctor`       | 2        | Yes        |
| `blocked_by_push_check`           | `blocked_by_push_check`          | 2        | Yes        |
| `deny`                            | `deny`                           | 1 (SG)   | Yes        |
| `unknown`                         | `blocked_by_shell_gate`          | 1 (SG)   | Yes        |
| `requires_human_review`           | `requires_human_review`          | 7        | No         |
| `requires_preflight`              | `requires_more_evidence`         | 6        | No         |
| `requires_active_task`            | `blocked_by_task_contract`       | 4 / 1(SG)| Yes        |
| `requires_more_evidence`          | `requires_more_evidence`         | 6        | No         |
| `allow_read_only`                 | `allow_preflight_only`           | 8        | No         |
| `allow_governed`                  | `allow_preflight_only`           | 8        | No         |
| `allow_test_execution`            | `allow_preflight_only`           | 8        | No         |

**Notes on specific mappings:**

- `blocked_by_policy_forbidden_file` → `blocked_by_scope` (not `blocked_by_shell_gate`): The
  policy-forbidden file block originates from the same policy source as the scope preflight
  forbidden-file list. Using `blocked_by_scope` keeps the audit trail consistent. The current
  88R mapping uses `blocked_by_shell_gate`; the 88T implementation should evaluate changing
  this to `blocked_by_scope` for consistency with the scope preflight integration.

- `blocked_by_missing_task` → `blocked_by_task_contract` (hard block): In 88R this falls through
  to step 6 missing evidence. In 88T it should be promoted to step 1 (SG hard block) so it fires
  before the broker's own task-contract check at step 4. This avoids double-checking and provides
  richer reason codes.

- `requires_active_task` → `blocked_by_task_contract` when no task detected: When shell gate says
  the command requires an active task and the broker detects no active task, this is effectively
  `blocked_by_task_contract` and must be a hard block. When a task IS present, the constraint is
  satisfied and the decision degrades to the next applicable level.

- `allow_read_only` / `allow_governed` / `allow_test_execution` → `allow_preflight_only`: Shell
  gate allow decisions never grant execution authorization. The broker must consistently map all
  allow shell-gate decisions to `allow_preflight_only`, never to a more permissive value. There
  is no broker decision more permissive than `allow_preflight_only` in the current prototype.

- `unknown` → `blocked_by_shell_gate`: Conservative default. Unknown shell-gate decisions must
  never be treated as allowing anything.

## 7. Category Mapping: Shell-Gate Category → Broker Implications

The following table maps all 24 shell-gate categories to their broker implications. The
"Broker Hard Block?" column indicates whether the category implies `hard_block_present=True`.

| Category                       | Broker Implication                                      | Hard Block |
|-------------------------------|----------------------------------------------------------|------------|
| `read_only_inspection`         | `allow_preflight_only`; `execution_authorized=False`    | No         |
| `test_execution`               | Conditional: test-run lock → block; no task → block; else allow_preflight_only | Conditional |
| `pcae_governed_lifecycle`      | `allow_preflight_only`; governed path acknowledged      | No         |
| `pcae_governed_commit`         | `allow_preflight_only`; governed path acknowledged      | No         |
| `pcae_governed_push`           | `allow_preflight_only`; governed path acknowledged      | No         |
| `raw_git_commit`               | `blocked_by_shell_gate`; hard block                     | Yes        |
| `raw_git_push`                 | `blocked_by_raw_git_push`; hard block                   | Yes        |
| `force_push`                   | `blocked_by_force_push`; hard block                     | Yes        |
| `git_history_rewrite`          | `blocked_by_shell_gate`; hard block                     | Yes        |
| `destructive_filesystem`       | `blocked_by_shell_gate`; hard block                     | Yes        |
| `filesystem_write`             | requires_preflight if task present; blocked_by_task_contract if no task | Conditional |
| `source_mutation`              | requires_preflight + scope; blocked_by_task_contract if no task | Conditional |
| `test_mutation`                | requires_preflight + scope; blocked_by_task_contract if no task | Conditional |
| `docs_mutation`                | requires_preflight + scope; blocked_by_task_contract if no task | Conditional |
| `policy_forbidden_file_mutation` | `blocked_by_scope`; hard block                        | Yes        |
| `backend_invocation`           | requires_human_review; requires backend preflight       | No         |
| `prompt_send`                  | `blocked_by_shell_gate`; hard block (shell gate blocks prompts) | Yes  |
| `output_capture`               | requires_human_review; capture preflight required       | No         |
| `intake_adoption`              | requires_human_review; adoption preflight required      | No         |
| `package_install`              | requires_human_review                                   | No         |
| `network_access`               | requires_human_review                                   | No         |
| `secret_access`                | requires_human_review; command text MUST be redacted    | No         |
| `environment_mutation`         | requires_human_review; preflight required               | No         |
| `unknown`                      | `blocked_by_shell_gate`; hard block; conservative deny  | Yes        |

**Category-specific notes:**

- `test_execution` hard-block path: If `expensive_test_execution_detected=True` and
  `test_run_clear_to_run=False`, the broker decision is `blocked_by_test_run_lock`
  (hard block). If task is absent, decision is `blocked_by_task_contract`. If both
  task present and test run clear, decision is `allow_preflight_only`.

- `secret_access` handling: Broker must not store `sg.command_text` verbatim when
  `sg.secret_access_detected=True`. Store `"[redacted: secret_access_detected]"` or
  a SHA-256 hash of the command text with a `hashed_command_text` field.

- `policy_forbidden_file_mutation` maps to `blocked_by_scope` (not `blocked_by_shell_gate`)
  for audit consistency with scope preflight. See decision mapping note in §6.

- `pcae_governed_*` categories: Shell gate already knows these are the safe paths. Broker
  must still require active task for mutating governed commands (e.g., `pcae commit` is
  still a mutating action requiring task contract even though shell gate allows it).

## 8. Decision Priority for Integrated Broker

The following priority order is a design recommendation for 88T `_broker_decide`. It refines
the 88R priority chain. Explicit test coverage is required before implementing.

```
Priority 1 — Shell gate hard blocks (checked before all evidence)
  1a. Force push detected (force_push_detected flag)
  1b. Raw git push detected (raw_git_push_detected flag)
  1c. Shell gate decision in hard-block map (SG_HARD_BLOCK_TO_BROKER)
      Includes: raw_git_commit, history_rewrite, destructive_filesystem,
                policy_forbidden_file, backend_policy, prompt_policy,
                adoption_policy, test_run_lock, unknown_command, deny
  1d. Shell gate requires_active_task when no task detected → blocked_by_task_contract

Priority 2 — Malformed/contradictory evidence (checked immediately after SG hard blocks)
  2a. Shell gate schema_version missing or wrong → blocked_by_conflicting_evidence
  2b. Shell gate performed flag true (command_executed, authorization_granted, etc.)
      → blocked_by_conflicting_evidence (hard block)
  2c. Shell gate allow decision but hard_block_present=True
      → blocked_by_conflicting_evidence
  2d. Shell gate unknown category + allow decision → blocked_by_shell_gate

Priority 3 — Explicit evidence failures (health, check, doctor, tests, push-check)
  Same as 88R step 2.

Priority 4 — Test run lock (when expensive test detected by broker independent check)
  Same as 88R step 3.

Priority 5 — No active task for mutating actions
  Same as 88R step 4.

Priority 6 — Scope preflight denial
  Same as 88R step 5.

Priority 7 — Missing evidence collection
  Shell gate requires_preflight → missing_evidence += "scope_preflight_for_command"
  Shell gate requires_human_review → missing_evidence += "human_review_for_command"
  Shell gate requires_more_evidence → missing_evidence += "additional_sg_evidence"
  Shell gate requires_active_task (when task present) → no additional block
  Standard mutating action evidence (health, check, push_check)
  → requires_more_evidence if any missing

Priority 8 — Human review gate
  Shell gate decision == requires_human_review → requires human_review_present
  Action in human-review-required set (push, commit, adoption, rollback, storage_write,
    backend_invocation) → requires human_review_present
  Shell gate category in (backend_invocation, secret_access, environment_mutation,
    package_install, network_access, output_capture, intake_adoption) → requires
    human_review_present

Priority 9 — Allow preflight only
  All prior checks pass → allow_preflight_only
  (Not execution authorization. Not command execution. Not mutation.)
```

This priority order is a **design recommendation only**. It must be validated with unit tests
covering each priority level and boundary transition in 88T before implementation is considered
complete.

## 9. Hard-Block Propagation Rules

Hard blocks are defined by `BPE_HARD_BLOCK_DECISIONS` in the broker. The following rules
govern propagation from shell-gate evidence:

### 9.1 Raw Git Push / Force Push

```
sg.decision == "blocked_by_raw_git_push"   → broker.decision = "blocked_by_raw_git_push"
sg.decision == "blocked_by_force_push"     → broker.decision = "blocked_by_force_push"
sg.detected_flags["raw_git_push_detected"] == True → same as decision-level block
sg.detected_flags["force_push_detected"]   == True → same as decision-level block
```

Rules:
- Raw git push and force push are **unconditional hard blocks**
- Neither `human_approval_present=True` nor `accepted_risk_present=True` may override these
- Both flags (`raw_git_push_detected`, `force_push_detected`) are checked independently of
  the decision field — if either flag is True, the corresponding hard block fires regardless
  of decision string
- `broker.hard_block_present` must be `True`
- All performed/authorization flags remain `False`

### 9.2 Destructive Filesystem

```
sg.decision == "blocked_by_destructive_filesystem"
sg.detected_flags["destructive_filesystem_detected"] == True
→ broker.decision = "blocked_by_shell_gate"
→ broker.hard_block_present = True
```

Rules:
- Unconditional hard block (same as raw git push)
- Human approval does not override
- Accepted risk does not override
- Reason codes must include `"shell_gate_category:destructive_filesystem"`

### 9.3 Policy-Forbidden File Mutation

```
sg.decision == "blocked_by_policy_forbidden_file"
sg.detected_flags["policy_forbidden_file_detected"] == True
→ broker.decision = "blocked_by_scope"   (recommended; see §6 note)
→ broker.hard_block_present = True
```

Rules:
- Policy-forbidden files (`README.md`, `docs/REAL_CAPTURED_TASKS.md`,
  `docs/LINKEDIN_ARTICLE_DRAFT.md`) are unconditional hard blocks at the scope boundary
- Shell gate detects this from command-level analysis (redirection, tee targets)
- Scope preflight detects this from file-level analysis
- Both are independent hard blocks; either alone is sufficient to block
- Human approval does not override
- Accepted risk does not override

### 9.4 Test Run Lock Propagation

```
sg.decision == "blocked_by_test_run_lock"
sg.test_run_clear_to_run == False
→ broker.decision = "blocked_by_test_run_lock"
→ broker.hard_block_present = True
```

Rules:
- Test run lock fires when `expensive_test_execution_detected=True` and
  `test_run_clear_to_run=False` (concurrent test process detected)
- Lock must be checked both at the shell-gate level (via `_call_doctor_test_run` in shell
  gate) and at the broker level (via `_call_doctor_test_run` in broker for commands that
  reach the broker directly without first passing through the shell gate CLI)
- Hard block; does not override on human approval

### 9.5 Unknown Command

```
sg.decision == "blocked_by_unknown_command"
sg.command_category == "unknown"
→ broker.decision = "blocked_by_shell_gate"
→ broker.hard_block_present = True
```

Rules:
- Deny-by-default for unrecognized commands
- Broker must treat `unknown` category as equivalent to hard block
- Even if shell gate later adds a new category, broker must not assume it is safe without
  an explicit decision mapping update

## 10. Non-Hard-Block Decision Handling

### 10.1 `requires_human_review`

```
sg.decision == "requires_human_review"
→ if human_review_present:
    does not block; continues to next priority
  else:
    broker.decision = "requires_human_review"
    broker.hard_block_present = False
    broker.missing_evidence += "human_review_for_command"
```

Categories that trigger this path: `package_install`, `network_access`, `backend_invocation`,
`output_capture`, `intake_adoption`, `environment_mutation`, `secret_access`.

### 10.2 `requires_preflight`

```
sg.decision == "requires_preflight"
→ broker.missing_evidence += "scope_preflight_for_command"
→ if scope_preflight_envelope is None:
    broker.decision = "requires_more_evidence"
  else:
    scope preflight result takes effect via existing scope block (priority 6)
```

Categories: `filesystem_write`, `source_mutation`, `test_mutation`, `docs_mutation`.

### 10.3 `requires_active_task`

```
sg.decision == "requires_active_task"
→ if not active_task_detected:
    broker.decision = "blocked_by_task_contract"  (hard block, promoted to priority 1d)
  else:
    constraint satisfied; continue to next check
```

### 10.4 `requires_more_evidence`

```
sg.decision == "requires_more_evidence"
→ broker.missing_evidence += "additional_sg_evidence"
→ broker.decision = "requires_more_evidence" (unless stronger block applies)
```

### 10.5 `allow_read_only` / `allow_governed` / `allow_test_execution`

```
sg.decision in ("allow_read_only", "allow_governed", "allow_test_execution")
→ shell gate constraint satisfied for command
→ broker continues to remaining checks (task, scope, evidence, human review)
→ final broker decision cannot be stronger than "allow_preflight_only"
→ broker.execution_authorized = False  (invariant)
→ broker.authorization_granted = False (invariant)
```

**Critical**: Broker must never interpret shell-gate allow decisions as execution
authorization or as a bypass of higher-priority broker checks.

## 11. Active-Task / No-Active-Task Behavior

### 11.1 Active Task Present

When `active_task_detected=True`:
- Shell gate `requires_active_task` constraint is satisfied for that decision
- Broker task-contract check (priority 5) passes for mutating actions
- Scope preflight runs and evaluates against the active task's allowed/forbidden file lists
- Shell gate evidence is still fully evaluated; active task does not bypass SG hard blocks

### 11.2 No Active Task (Idle Repository)

When `active_task_detected=False`:
- Shell gate `requires_active_task` → `blocked_by_task_contract` (priority 1d)
- Shell gate `blocked_by_missing_task` → `blocked_by_task_contract` (priority 1)
- Broker task-contract check (priority 5) → `blocked_by_task_contract` for mutating actions
- **Read-only actions are not blocked by absent task** — `read_only_inspection` category with
  `allow_read_only` decision proceeds to `allow_preflight_only` without requiring a task
- Broker must fire task-contract block even if shell gate has already indicated it

The double check (shell gate + broker) is intentional redundancy for defense-in-depth.
Both layers must independently enforce the constraint.

## 12. Human Approval Limits

Human approval (`human_approval_present=True`) is a governance evidence flag. It means a
human has reviewed and approved the proposed action. It is **not a bypass mechanism**.

Human approval:
- **May satisfy** the `requires_human_review` gate for non-hard-block decisions
- **May satisfy** the `requires_human_review` gate for broker actions (push, commit,
  adoption, rollback, storage_write, backend_invocation)
- **May NOT override** any hard block in either shell gate or broker:
  - `blocked_by_force_push`
  - `blocked_by_raw_git_push`
  - `blocked_by_destructive_filesystem`
  - `blocked_by_policy_forbidden_file`/`blocked_by_scope`
  - `blocked_by_unknown_command`/`blocked_by_shell_gate`
  - `blocked_by_conflicting_evidence`
  - `blocked_by_task_contract`
  - Any `blocked_by_*` in `BPE_HARD_BLOCK_DECISIONS`
- **Does not grant execution authorization** (`execution_authorized` remains `False`)
- **Does not grant operation completion** (no performed flag becomes `True`)

## 13. Accepted-Risk Limits

Accepted risk (`accepted_risk_present=True`) is a governance evidence flag. It means the
requesting party has acknowledged the risk of the proposed action. It is **not mitigation**.

Accepted risk:
- **Is recorded in evidence** via `evidence_provided["accepted_risk_present"]`
- **Does not override** any hard block
- **Does not satisfy** the human review gate (human review and accepted risk are independent)
- **Does not grant** more permissive broker decisions
- **Must be logged** in the audit record as a noted risk acknowledgment
- In the integrated design, accepted risk should lower `missing_evidence` verbosity for
  certain categories (e.g., `network_access`) but must not change the decision if a hard
  block or human-review gate applies

## 14. Missing Shell-Gate Evidence

When `requested_command` is present but shell-gate evidence cannot be produced (e.g.,
`_classify_command` throws, or the shell gate module is unavailable), the broker must:

1. Record `shell_gate_evidence = None` with `sg_unavailable=True` in broker output
2. Add `"shell_gate_evidence"` to `missing_evidence`
3. Return `requires_more_evidence` (not `allow_preflight_only`) for any action with a
   requested command
4. Never assume the command is safe because shell-gate evidence is absent
5. Log a warning in `broker["warnings"]`

When `requested_command` is absent:
- Shell gate evidence is correctly `None`
- Broker proceeds without shell-gate evidence as in 88R

## 15. Conflicting Evidence Detection

The 88T broker must detect and block on the following contradictions. These indicate either
implementation bugs or tampered evidence and must result in `blocked_by_conflicting_evidence`
(hard block).

| Contradiction                                                          | Action                                |
|------------------------------------------------------------------------|---------------------------------------|
| `sg.schema_version` missing or != "0.1"                               | `blocked_by_conflicting_evidence`     |
| Any sg performed flag is `True` (command_executed, authorization_granted, etc.) | `blocked_by_conflicting_evidence` |
| `sg.hard_block_present=True` but `sg.decision` is an allow decision   | `blocked_by_conflicting_evidence`     |
| `sg.command_category == "unknown"` and `sg.decision` is allow         | `blocked_by_conflicting_evidence`     |
| `sg.force_push_detected=True` but `sg.decision != "blocked_by_force_push"` | `blocked_by_conflicting_evidence` |
| `sg.raw_git_push_detected=True` but `sg.decision` is allow            | `blocked_by_conflicting_evidence`     |
| Broker action is mutating but `sg.decision == "allow_read_only"`       | `blocked_by_conflicting_evidence`     |

When contradictions are detected:
- `broker.decision = "blocked_by_conflicting_evidence"`
- `broker.hard_block_present = True`
- `broker.reason_codes` includes `"contradictory_shell_gate_evidence"`
- Contradiction details recorded in `broker["warnings"]`
- No performed flag is set to True

Contradictions must be logged for audit even when other hard blocks apply first.

## 16. Performed Flags Invariant

All performed/authorization flags must remain unconditionally `False` in the integrated
broker. This invariant holds regardless of shell-gate decision, human approval, accepted
risk, task contract state, or any other evidence.

```
authorization_granted     = False  (invariant)
execution_authorized      = False  (invariant)
command_executed          = False  (invariant)
repo_mutation_performed   = False  (invariant)
backend_invocation_performed = False  (invariant)
prompt_sent               = False  (invariant)
capture_performed         = False  (invariant)
intake_performed          = False  (invariant)
adoption_performed        = False  (invariant)
commit_performed          = False  (invariant)
push_performed            = False  (invariant)
raw_git_push_performed    = False  (invariant)
force_push_performed      = False  (invariant)
storage_written           = False  (invariant)
```

Shell gate also maintains this invariant in its output. If any shell-gate performed flag is
`True`, the broker must treat this as a malformed-evidence contradiction (§15).

## 17. Audit Model

The integrated broker output envelope should include the following fields to support
governance audit requirements. Fields marked "(new in 88T)" are not present in 88R.

```
broker: {
  # Existing 88R fields (unchanged)
  broker_type              : "permission_broker_prototype"
  decision                 : str
  reason_codes             : list[str]
  hard_block_present       : bool
  active_task_detected     : bool
  task_contract_path       : str | null
  shell_gate_evidence      : dict | null
  scope_preflight_decision : str | null
  test_run_preflight_required: bool
  test_run_clear_to_run    : bool | null
  evidence_provided        : dict
  evidence_sources         : list[str]
  missing_evidence         : list[str]
  safety_notes             : dict[str, bool]
  # All 14 performed flags

  # Audit fields (new in 88T)
  shell_gate_schema_version  : str | null          (new) — from sg evidence
  shell_gate_command_category: str | null          (new) — category surface
  shell_gate_command_text_hash: str | null         (new) — SHA-256 of command; null if not secret
  shell_gate_command_text_redacted: bool           (new) — True if secret_access_detected
  shell_gate_decision        : str | null          (new) — sg decision, for audit traceability
  shell_gate_reason_codes    : list[str]           (new) — sg reason_codes, for audit
  shell_gate_hard_block_present: bool | null       (new) — sg hard_block_present value
  conflicting_evidence_detected: bool              (new) — True if §15 contradiction found
  conflicting_evidence_details : list[str]         (new) — which contradictions found
  hard_block_sources         : list[str]           (new) — which evidence sources triggered hard blocks
  human_review_sources       : list[str]           (new) — which evidence required human review
  accepted_risk_noted        : bool                (new) — mirrors accepted_risk_present
  broker_mapping_reason      : str | null          (new) — human-readable mapping justification
}
```

**Command text redaction policy** (new in 88T):
- When `sg.secret_access_detected=True`: set `shell_gate_command_text_redacted=True`,
  set `shell_gate_command_text_hash=sha256(command_text)`, do NOT store raw command text
- When `sg.secret_access_detected=False`: `shell_gate_command_text_redacted=False`,
  `shell_gate_command_text_hash=None`, raw command text may appear in `shell_gate_evidence`
  as in 88R

**Do not store raw command text containing secret arguments in persistent logs or storage.**

## 18. Security Requirements

### 18.1 Schema Version Validation

Before consuming any shell-gate evidence, the broker must check:
```python
if sg_evidence.get("schema_version") != "0.1":
    return "blocked_by_conflicting_evidence"
```

Unknown or future schema versions must not be trusted without explicit version-specific
handling. Treat missing schema version as a hard-block condition.

### 18.2 Malformed Evidence

The broker must not silently swallow malformed evidence. Any field that cannot be parsed
or validated to its expected type must be treated as missing (→ `requires_more_evidence`)
or contradictory (→ `blocked_by_conflicting_evidence`) depending on severity.

Type expectations:
- `sg.command_category`: must be in `SGP_CATEGORIES` tuple; if not → contradiction
- `sg.decision`: must be in `SGP_DECISIONS` tuple; if not → contradiction
- `sg.hard_block_present`: must be bool; if not → contradiction
- `sg.detected_flags`: must be dict with bool values; non-bool values → contradiction

### 18.3 Conservative Handling

When in doubt, block. The broker must never allow an action because evidence was absent,
unparseable, or ambiguous. Default to the most conservative applicable decision when
evidence is uncertain.

### 18.4 No Trust Amplification

Shell gate is a classifier. It classifies commands based on lexical analysis. It does not
execute commands and does not verify command semantics. The broker must not amplify trust
beyond what the classifier provides:
- `allow_read_only` from shell gate does not mean the command is actually safe to execute
- It means the classifier believes the command text matches a read-only pattern
- The broker must still evaluate task state, scope, health, human review independently

## 19. What Remains Out of Scope Until Enforcement Phases

The following topics are explicitly deferred beyond 88T:

1. **Shell interception** — installing hooks or wrappers that intercept shell commands at
   execution time; requires dedicated safety analysis and OS-specific implementation
2. **Real-time enforcement** — blocking shell commands at the OS/shell level; out of scope
   for prototype phases
3. **Persistent shell-gate storage** — writing gate decisions to `.pcae/` directories for
   later audit retrieval; deferred to audit persistence phases
4. **Multi-command analysis** — analyzing the relationship between multiple sequential
   shell commands (e.g., detecting that `git status` followed by `git push` violates policy)
5. **Shell variable expansion** — evaluating `$VAR` in command text; the classifier does
   lexical analysis only
6. **Subshell execution** — `$(cmd)` or `` `cmd` `` expansion analysis
7. **Alias resolution** — detecting aliased commands that resolve to blocked programs
8. **Authorization expiration** — shell-gate decisions that expire after a time window
9. **Multi-agent coordination** — ensuring broker decisions are consistent across concurrent
   agent instances
10. **Write execution governance** — using broker + shell gate output to actually authorize
    and audit write operations; requires phases beyond 88T

## 20. Minimum Tests for 88T Implementation

The 88T test suite must verify the following scenarios to satisfy acceptance criteria.
Tests must be in the fast-green tier. Tests must not use live REPO_ROOT for task-active
behavior (use `tmp_task_root` fixture from 88R.1).

**Hard-block propagation (minimum 8 tests):**
- Force push command → `blocked_by_force_push` regardless of human approval
- Raw git push command → `blocked_by_raw_git_push` regardless of human approval
- Destructive filesystem command → `blocked_by_shell_gate` hard block
- Policy-forbidden file redirection → `blocked_by_scope` hard block
- Unknown command → `blocked_by_shell_gate` hard block
- Test run lock → `blocked_by_test_run_lock` hard block
- Hard block overrides allow evidence (health=True, check=True, human_review=True)
- Hard block with no task: hard block still fires before task-contract check

**Non-hard-block shell-gate decisions (minimum 6 tests):**
- `requires_human_review` + `human_review_present=True` → `allow_preflight_only`
- `requires_human_review` + no human review → `requires_human_review`
- `requires_preflight` + scope evidence absent → `requires_more_evidence`
- `requires_preflight` + scope evidence present → scope result takes effect
- `requires_active_task` + task present → not blocked by this check
- `requires_active_task` + no task → `blocked_by_task_contract`

**Read-only command handling (minimum 3 tests):**
- `allow_read_only` → `allow_preflight_only`, never `execution_authorized`
- `allow_governed` → `allow_preflight_only`
- `allow_test_execution` + all evidence → `allow_preflight_only` only

**Malformed evidence (minimum 5 tests):**
- Missing schema_version → `blocked_by_conflicting_evidence`
- Wrong schema_version → `blocked_by_conflicting_evidence`
- Performed flag True in sg evidence → `blocked_by_conflicting_evidence`
- allow decision + hard_block_present=True in sg → `blocked_by_conflicting_evidence`
- Unknown category + allow decision → `blocked_by_conflicting_evidence`

**Performed-flag invariant (minimum 14 parametrized tests):**
- All 14 performed flags False for allow path
- All 14 performed flags False for hard-block path
- All 14 performed flags False for missing-evidence path
- All 14 performed flags False for human-review path
- (56 parametrized total, following 88R pattern)

**Secret-access redaction (minimum 2 tests):**
- `secret_access_detected=True` → command text redacted in output
- `secret_access_detected=False` → command text present in output

**Contradiction detection (minimum 4 tests):**
- Broker mutating action + sg decision `allow_read_only` → contradiction
- sg force_push_detected=True but decision is not blocked_by_force_push → contradiction
- sg raw_git_push_detected=True but decision is allow → contradiction
- Contradiction logged in warnings but all performed flags remain False

**Active-task / no-task boundary (minimum 4 tests):**
- Read-only command, no task → `allow_preflight_only` (task not required)
- Mutating command, no task → `blocked_by_task_contract`
- Mutating command, task present → proceeds to next check
- requires_active_task from sg, no task → blocked_by_task_contract

**Minimum total**: ~102 tests (following 88R/88Q pattern with parametrize). Actual count
may be higher after full gap analysis in 88T.

## 21. Recommended Implementation Sequence

### Phase 88T — Broker + Shell Gate Integration Prototype

Goal: Implement the integration design in this document.

Scope:
1. Update `_SG_HARD_BLOCK_TO_BROKER` with `blocked_by_missing_task` and `blocked_by_scope`
   for `blocked_by_policy_forbidden_file`
2. Add schema version validation to broker shell-gate evidence consumption
3. Add contradiction detection (§15 table)
4. Promote `requires_active_task` to priority 1d (hard block when no task)
5. Add `requires_preflight` handling in step 7 (missing evidence + scope check)
6. Add `requires_human_review` gate for shell-gate categories (beyond current step 7)
7. Add redaction for secret-access command text
8. Add new audit fields (§17 "new in 88T" list)
9. Write minimum test suite (§20)
10. Validate fast-green and quick tiers pass
11. Create `docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_PROTOTYPE.md`
12. Update PROJECT_STATUS.md and CHANGELOG.md

Forbidden in 88T:
- Shell interception or shell wrapper installation
- Real-time enforcement
- Persistent shell-gate storage
- Execution authorization

### Phase 88U — Broker + Shell Gate Integration Validation

Goal: Comprehensive false-positive and false-negative review of the 88T integration.

Expected scope:
- Edge case test matrix for all 24 categories × active/no-active task
- Compound command integration tests (&&, ||, ;, pipe chains)
- False-positive review (legitimate operations incorrectly blocked)
- False-negative review (dangerous operations incorrectly allowed)
- CLI integration tests for combined broker+shell-gate output

### Phase 88V (provisional) — Broker Schema Hardening

Goal: Define versioned broker output schema, add field-level validation, and document
migration path for future schema versions.

## 22. Safety Invariants

The following invariants must hold throughout 88T implementation and all subsequent phases:

1. `authorization_granted = False` — unconditional, no exception
2. `execution_authorized = False` — unconditional, no exception
3. All other performed flags = False — unconditional, no exception
4. Shell-gate evidence does not grant execution authorization
5. Shell-gate allow decisions do not produce broker decisions more permissive than `allow_preflight_only`
6. Human approval does not override hard blocks
7. Accepted risk does not override hard blocks
8. Accepted risk does not satisfy human review gate
9. Unknown category → blocked, not allowed
10. Missing shell-gate evidence (when command present) → `requires_more_evidence`, not allow
11. Malformed shell-gate evidence → `blocked_by_conflicting_evidence`, not allow
12. Schema version mismatch → `blocked_by_conflicting_evidence`, not allow
13. No-task state blocks mutating actions even when shell gate allows
14. Force push and raw git push are never overridable, ever
15. Secret-bearing command text must not be stored verbatim in audit records
16. Broker does not invoke backends, send prompts, or capture outputs
17. Broker does not write persistent storage
18. Broker does not install shell wrappers
19. Contradiction between broker and shell-gate evidence escalates to hard block, not resolution
20. This design document is design-only; all described behaviors are not_started until 88T

## 23. Remaining Limitations (As of 88S)

1. Shell gate is lexical only — it does not evaluate variable expansion, aliases, or
   subshell execution; a malicious command could potentially evade classification
2. Compound command parsing handles `&&`, `||`, `;`, and pipes but not all possible shell
   constructs (backtick substitution, `eval`, POSIX `$(...)` in arguments)
3. No cryptographic signing of shell-gate evidence — broker cannot verify the evidence was
   produced by a trusted shell-gate instance
4. No expiration model — shell-gate evidence collected at T1 is not invalidated by state
   changes at T2
5. The broker and shell gate both call `_call_doctor_test_run` independently — in 88T this
   should be deduplicated to a single call
6. Category severity ordering in `_CATEGORY_SEVERITY` (shell_gate.py) is not yet formally
   tested against the integration decision mapping; test coverage required in 88T

## 24. Artifacts Referenced

| Artifact | Phase | Notes |
|---|---|---|
| `docs/PHASE_88_PERMISSION_BROKER_RECONCILIATION.md` | 88N | Broker design baseline |
| `docs/PHASE_88_SHELL_GATE_RECONCILIATION.md` | 88O | Shell gate design baseline |
| `docs/PHASE_88_SCOPE_MATCHING_SHARED_UTILITY_RECONCILIATION.md` | 88O.1 | Scope match shared util |
| `docs/PHASE_88_SHELL_GATE_PROTOTYPE.md` | 88P | Shell gate implementation |
| `docs/PHASE_88_SHELL_GATE_TEST_MATRIX.md` | 88Q | Gate test coverage |
| `docs/PHASE_88_PERMISSION_BROKER_PROTOTYPE.md` | 88R | Broker implementation |
| `docs/PHASE_88_BROKER_TEST_TASK_CONTRACT_DECOUPLING.md` | 88R.1 | Test isolation repair |
| `src/pcae/core/shell_gate.py` | 88P/88Q | 26 decisions, 24 categories, `_decide` function |
| `src/pcae/core/permission_broker.py` | 88R | 24 decisions, `_broker_decide` function |

## 25. Recommended Next Phase

**88T — Broker + Shell Gate Integration Prototype**

Implement this design document. Specifically:
- Update `_SG_HARD_BLOCK_TO_BROKER` with missing mappings
- Add schema validation and contradiction detection
- Add audit fields to broker output
- Add secret-access command redaction
- Write minimum 102 tests covering the scenarios in §20
- Validate all tiers pass
- No shell interception, no execution authorization
