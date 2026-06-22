# Real Captured Task Governance Path

**Policy Controlled Autonomous Execution**

*Version 1.0 — Phase 77J*

---

## 1. Overview

A **real captured task** is a governed, documentation-only task whose output is
captured from a locked backend runtime invoked under PCAE's full governance
gate chain. Unlike fixture-based or no-op captured pipelines, a real captured
task invokes an actual backend process, captures its stdout and stderr, and
classifies the outcome — all without mutating the repository, committing, or
pushing.

The governance path documented here was established by the PCAE Phase 77 series
(77A–77J) and serves as the authoritative reference for all future real
captured tasks. It defines the artifact chain, the blocking gates, and the
recovery path when backends time out.

**This is a documentation-only governance path.** The task output is
documentation files (e.g., `docs/`, `CHANGELOG.md`). Source code, test files,
and backend invocations are governed but not the subject of the task.

---

## 2. Governance Principles

Every phase in the captured task governance path adheres to these principles:

- **Governance before invocation.** No backend is called, no artifact is
  persisted, and no classification is produced until every upstream gate is
  satisfied.
- **Human approval is authoritative.** Backend capture requires an explicit,
  recorded human approval artifact (Phase 77D) bound to a specific package
  digest. No approval, no capture.
- **Evidence before action.** Each phase's output is a structured JSON
  artifact. The next phase reads its predecessor's artifact and refuses to
  proceed if it is missing, ineligible, or structurally invalid.
- **Mutation is forbidden.** Every phase in this path sets
  `apply_performed=False`, `files_modified=False`, `commits_created=0`,
  `push_performed=False`, and `execution_allowed=False`. These are structural
  invariants, not configuration.
- **Failure is classified, not ignored.** When a backend capture fails, the
  failure is classified into one of five outcome categories (Phase 77G). Each
  category has a defined next action.
- **Retry is governed, not automatic.** A timeout failure enters a governed
  retry path (77H → 77I → 77J) with explicit policy, preflight, and execution
  phases. There is no automatic retry loop.

---

## 3. The Governance Path

The captured task governance path is a strict 10-phase sequence. Each phase
produces a structured artifact that gates the next. No phase can be skipped.

```
77A Readiness Gate
  → 77B Contract Preparation
    → 77C Package Dry-Run
      → 77D Package Approval
        → 77E Backend Capture Preflight
          → 77F Backend Capture
            → 77G Result Intake (Classification)
              ├─ captured → output intake (77K)
              ├─ timeout_failure → 77H Timeout Policy
              │                      → 77I Retry Preflight
              │                        → 77J Governed Retry
              │                          → 77K Output Intake
              ├─ backend_failure → (future backend failure policy)
              ├─ repo_mutation_detected → emergency review
              └─ dry_run_only → run --execute first
```

### 3.1 Phase 77A — Readiness Gate

**Command:** `pcae phase real-captured-task-readiness-gate`

**Artifact:** `.pcae/real-captured-task-readiness-gates/latest.json`

**Purpose:** Assess whether PCAE is ready to move from the completed
fixture/no-op captured-output pipeline to a real captured task pipeline.

**Gates checked:**
1. Lifecycle final summary exists and is closed
2. Git working tree is clean
3. Real execution is confirmed disabled
4. Runner execution is confirmed unavailable (refuses invocation)
5. Phase audit has no warnings
6. An active agent lock exists

**Statuses:** `ready_for_real_task_preparation` | `blocked_lifecycle_not_closed` | `blocked_dirty_tree` | `blocked_execution_not_disabled` | `blocked_runner_execution_available` | `blocked_audit` | `blocked_agent_lock`

**Does not invoke a backend. Does not create a task contract.**

---

### 3.2 Phase 77B — Contract Preparation

**Command:** `pcae phase real-captured-task-contract-prepare`

**Artifact:** `.pcae/real-captured-task-contracts/latest.json`

**Purpose:** Prepare a task contract defining the governance boundaries for a
real captured task. The contract declares the task ID, goal, allowed files,
forbidden actions, and acceptance criteria.

**Predecessor:** 77A readiness gate must report `ready_for_real_task_preparation`.

**Contract contents for REAL-CAPTURED-TASK-001 (reference):**

| Field | Value |
|-------|-------|
| `task_id` | `REAL-CAPTURED-TASK-001` |
| `task_type` | `documentation_only` |
| `task_goal` | Create `docs/REAL_CAPTURED_TASKS.md` documenting the governance path |
| `allowed_files` | `docs/REAL_CAPTURED_TASKS.md` |
| `forbidden` | No backend invocation, no source modification, no commit, no push |

**Statuses:** `prepared` | `blocked_readiness_not_ready` | `blocked_dirty_tree` | `blocked_execution_not_disabled` | `blocked_runner_execution_available` | `blocked_audit` | `blocked_agent_lock`

---

### 3.3 Phase 77C — Package Dry-Run

**Command:** `pcae phase real-captured-task-package-dry-run`

**Artifact:** `.pcae/real-captured-task-package-dry-runs/latest.json`

**Purpose:** Create a dry-run prompt envelope for the captured task without
invoking any backend. The envelope carries `NOT SEND-AUTHORIZED` markers and
a SHA-256 digest of the package contents.

**Predecessor:** 77B contract must report `prepared`.

**Key fields:**
- `envelope`: The full prompt envelope with `NOT SEND-AUTHORIZED` markers
- `package_digest`: SHA-256 digest of the envelope content
- `backend_target`: The locked backend target (e.g., `claude-deepseek`)
- `status`: `ready` | `blocked_*`

**Does not invoke a backend.** The envelope exists only as an artifact for
human review before approval.

---

### 3.4 Phase 77D — Package Approval

**Command:** `pcae phase real-captured-task-package-approval --approve --approved-by "<name>" --reason "<reason>"`

**Artifact:** `.pcae/real-captured-task-package-approvals/latest.json`

**Purpose:** Record an explicit human approval of the package, bound to the
package digest produced in 77C.

**Predecessor:** 77C dry-run must report `ready`.

**Key fields:**
- `package_digest`: Must match the 77C dry-run digest
- `approved_by`: Human identifier (e.g., `Atila Madai`)
- `approval_reason`: Free-text reason for approval
- `human_approved`: `true` when explicitly approved

**Statuses:** `approved` | `ready_for_approval_request` | `blocked_*`

**Without approval, 77E preflight will refuse to proceed.** Approval is a
discrete, recorded human decision — not implied by the existence of a dry-run.

---

### 3.5 Phase 77E — Backend Capture Preflight

**Command:** `pcae phase real-captured-task-backend-capture-preflight`

**Artifact:** `.pcae/real-captured-task-backend-capture-preflights/latest.json`

**Purpose:** Validate all conditions before a backend capture is eligible.
This is the final gate before the backend is actually invoked.

**Predecessors:** 77D approval (`human_approved=true`), 77C dry-run (digest
verification).

**Gates checked:**
1. 77D approval exists and `human_approved=true`
2. Package digest matches between 77C dry-run and 77D approval
3. Locked backend is in the approved target list
4. Active agent lock exists
5. Phase audit has no warnings
6. Git working tree is clean
7. Real execution is confirmed disabled

**Statuses:** `ready_for_backend_capture` | `blocked_*`

**Does not invoke a backend.** Preflight is the last read-only gate.

---

### 3.6 Phase 77F — Backend Capture

**Command:** `pcae phase real-captured-task-backend-capture --execute`

**Artifact:** `.pcae/real-captured-task-backend-captures/latest.json`
**Raw output:** `.pcae/real-captured-task-backend-captures/latest.stdout.txt`
**Raw stderr:** `.pcae/real-captured-task-backend-captures/latest.stderr.txt`

**Purpose:** Invoke the locked backend with the approved prompt envelope,
capture its output, and guard against repository mutation.

**Predecessor:** 77E preflight must report `ready_for_backend_capture`.

**Execution behavior:**

1. The `NOT SEND-AUTHORIZED` markers from the 77C dry-run envelope are
   stripped and replaced with governed execution markers.
2. The locked backend is invoked via subprocess with a 120-second timeout.
3. stdout and stderr are captured and persisted to `latest.stdout.txt` and
   `latest.stderr.txt`.
4. A mutation guard runs `git status --porcelain` before and after invocation.
   Only changes under `.pcae/real-captured-task-backend-captures/` and
   `.pcae/agent-locks/` are permitted. Any other change is a mutation violation.

**Statuses:** `captured` | `dry_run_ready` | `failed_backend_timeout` | `failed_backend_invocation` | `failed_repo_mutation_detected`

**Safety invariants enforced:**
- `apply_performed`: `false`
- `files_modified`: `false`
- `commits_created`: `0`
- `push_performed`: `false`
- `execution_allowed`: `false`

**Flags:**
- `--dry-run`: Validate without invoking the backend
- `--execute`: Perform the actual backend invocation

---

### 3.7 Phase 77G — Result Intake (Classification)

**Command:** `pcae phase real-backend-capture-result-intake`

**Artifact:** `.pcae/real-backend-capture-result-intakes/latest.json`

**Purpose:** Classify the outcome of the 77F backend capture into one of five
categories. This is the **fork point** in the governance path.

**Predecessor:** 77F backend capture must have produced an output artifact.

**Capture outcome categories:**

| Outcome | Meaning | Next Action |
|---------|---------|-------------|
| `captured` | Backend responded with output within timeout | Proceed to output intake (77K) |
| `timeout_failure` | Backend did not respond within the 120s timeout | Enter governed retry path (77H) |
| `backend_failure` | Backend invoked but returned non-zero exit code | Future backend failure policy (not yet built) |
| `repo_mutation_detected` | Backend invocation caused unexpected repo changes | Emergency review required |
| `dry_run_only` | 77F was run with `--dry-run`, no actual invocation | Run with `--execute` first |

**Detection logic:**
- `timeout_failure`: stderr contains "timeout" OR return code is `-1`
- `backend_failure`: return code is non-zero and not timeout-related
- `repo_mutation_detected`: mutation guard flagged unapproved file changes
- `dry_run_only`: 77F status is `dry_run_ready`
- `captured`: none of the above

**Key fields:**
- `capture_outcome`: One of the five categories above
- `output_intake_ready`: `true` when outcome is `captured`
- `retry_policy_needed`: `true` when outcome is `timeout_failure`
- `emergency_review_required`: `true` when outcome is `repo_mutation_detected`

---

### 3.8 The Timeout/Retry Path (77H → 77I → 77J)

When 77G classifies the capture outcome as `timeout_failure`, the task enters
the governed retry path. This path has three phases:

```
77G timeout_failure → 77H Timeout Policy → 77I Retry Preflight → 77J Governed Retry → 77K Output Intake
```

#### Phase 77H — Timeout Policy

**Command:** `pcae phase backend-capture-timeout-policy`

**Artifact:** `.pcae/backend-capture-timeout-policies/latest.json`

**Purpose:** Create a governed retry policy for timeout failures. The policy
defines the retry timeout, maximum attempts, and eligibility conditions.

**Predecessor:** 77G intake must report `timeout_failure`.

**Policy defaults (Phase 77H):**

| Parameter | Value |
|-----------|-------|
| `retry_timeout_seconds` | 300 |
| `max_additional_attempts` | 1 |
| `retry_allowed_now` | `false` |
| `automatic_retry_allowed` | `false` |
| `backend_retry_preflight_allowed_in_future_phase` | `true` |

**Statuses:** `prepared` | `blocked_not_timeout_failure` | `blocked_*`

**Key principle:** The policy never authorizes automatic retry. Retry always
requires a separate preflight (77I) and explicit governed execution (77J).

#### Phase 77I — Retry Preflight

**Command:** `pcae phase backend-capture-retry-preflight`

**Artifact:** `.pcae/backend-capture-retry-preflights/latest.json`

**Purpose:** Validate all retry eligibility conditions under the 77H timeout
policy before performing the governed retry.

**Predecessors:** 77H timeout policy (`prepared`), 77G intake
(`timeout_failure`).

**Gates checked:**
1. 77H timeout policy exists and is `prepared`
2. 77G capture outcome is `timeout_failure`
3. Retry has not already been performed (no existing retry artifact)
4. Emergency review is not required
5. Git working tree is clean
6. Phase audit has no warnings
7. Real execution is confirmed disabled
8. Runner execution is confirmed unavailable
9. Active agent lock exists
10. Locked backend is in the approved target list

**Statuses:** `ready_for_retry` | `blocked_*`

#### Phase 77J — Governed Retry

**Command:** `pcae phase backend-capture-governed-retry --execute`

**Artifact:** `.pcae/backend-capture-governed-retries/latest.json`
**Raw output:** `.pcae/backend-capture-governed-retries/latest.stdout.txt`
**Raw stderr:** `.pcae/backend-capture-governed-retries/latest.stderr.txt`

**Purpose:** Perform exactly one governed retry of the backend capture with
the 300-second timeout defined in the 77H policy.

**Predecessor:** 77I retry preflight must report `ready_for_retry`.

**Execution behavior:**

1. Follows the same pattern as 77F: strips markers, invokes backend via
   subprocess, captures stdout/stderr, runs mutation guard.
2. Uses the **300-second** timeout from the 77H policy (not the 120-second
   default from 77F).
3. Reports `failed_backend_timeout` if the retry also times out (distinct
   from 77F's `failed_backend_timeout` — this is the retry artifact's status).

**Statuses:** `captured` | `dry_run_ready` | `failed_backend_timeout` | `failed_backend_invocation` | `failed_repo_mutation_detected`

**On success (`captured`):** Proceed to 77K output intake.
**On timeout (`failed_backend_timeout`):** The policy allows only 1 additional
attempt. If the retry also times out, human investigation is required.

**Safety invariants:** Same as 77F — no apply, no file modification, no
commit, no push, no execution authorization.

---

## 4. The Fork at Phase 77G (Capture Outcome Branching)

Phase 77G is the single fork point in the governance path. Understanding the
branching logic is essential for operating future captured tasks:

```
77F Backend Capture
  ↓
77G Result Intake
  ↓
  ├─ capture_outcome = "captured"
  │    → output_intake_ready = true
  │    → Next: 77K Real Captured Backend Output Intake
  │
  ├─ capture_outcome = "timeout_failure"
  │    → retry_policy_needed = true
  │    → Next: 77H → 77I → 77J (governed retry path)
  │    → After retry: 77K
  │
  ├─ capture_outcome = "backend_failure"
  │    → Next: Future backend failure policy (not yet built)
  │    → For now: human investigation
  │
  ├─ capture_outcome = "repo_mutation_detected"
  │    → emergency_review_required = true
  │    → Next: Human emergency review before any further action
  │
  └─ capture_outcome = "dry_run_only"
       → Next: Re-run 77F with --execute
```

**No branch is automatic.** Every fork requires an explicit human decision
to proceed to the next phase. The governance path recommends next actions but
never auto-advances.

---

## 5. Safety Invariants

Every phase artifact in the governance path includes the following invariants.
They are structural, not configurable:

| Invariant | Value | Enforced By |
|-----------|-------|-------------|
| `apply_performed` | `false` | All phases |
| `files_modified` | `false` | All phases |
| `commits_created` | `0` | All phases |
| `push_performed` | `false` | All phases |
| `execution_authorized` | `false` | All phases |
| `real_captured_task_execution_allowed` | `false` | All phases |
| `output_application_allowed` | `false` | All phases |
| `backend_invocation_allowed_now` | `false` | Phases 77A–77E, 77G–77I |
| `backend_capture_allowed_now` | `false` | Phases 77A–77E, 77G–77I |

These invariants mean:
- **No phase in this path mutates the repository.** The only files created
  are governance artifacts under `.pcae/`.
- **No phase commits or pushes.** `git commit` and `git push` remain
  exclusively human actions.
- **No phase applies captured output to the repository.** The captured output
  is stored for human review, not automatic application.

---

## 6. Artifact Directory Map

All governance artifacts are stored under `.pcae/`. Each phase has its own
subdirectory with a `latest.json` artifact and a `.gitignore` that excludes
all contents from version control.

| Phase | Artifact Directory | Key Files |
|-------|-------------------|-----------|
| 77A | `.pcae/real-captured-task-readiness-gates/` | `latest.json` |
| 77B | `.pcae/real-captured-task-contracts/` | `latest.json` |
| 77C | `.pcae/real-captured-task-package-dry-runs/` | `latest.json` |
| 77D | `.pcae/real-captured-task-package-approvals/` | `latest.json` |
| 77E | `.pcae/real-captured-task-backend-capture-preflights/` | `latest.json` |
| 77F | `.pcae/real-captured-task-backend-captures/` | `latest.json`, `latest.stdout.txt`, `latest.stderr.txt` |
| 77G | `.pcae/real-backend-capture-result-intakes/` | `latest.json` |
| 77H | `.pcae/backend-capture-timeout-policies/` | `latest.json` |
| 77I | `.pcae/backend-capture-retry-preflights/` | `latest.json` |
| 77J | `.pcae/backend-capture-governed-retries/` | `latest.json`, `latest.stdout.txt`, `latest.stderr.txt` |

**Artifact format:** All `latest.json` artifacts are structured JSON with
`sort_keys=True` and `indent=2`. Every artifact includes:
- A timestamp (`created_at` or equivalent)
- References to predecessor artifacts (paths or IDs)
- A status field that downstream phases gate on
- Safety invariants
- A `recommended_next_phase` field

---

## 7. CLI Command Reference

### Primary Commands

```bash
# 77A — Readiness Gate
pcae phase real-captured-task-readiness-gate [--json] [--save]
pcae phase real-captured-task-readiness-gate-show [--json]

# 77B — Contract Preparation
pcae phase real-captured-task-contract-prepare [--json] [--save]
pcae phase real-captured-task-contract-prepare-show [--json]

# 77C — Package Dry-Run
pcae phase real-captured-task-package-dry-run [--json] [--save]
pcae phase real-captured-task-package-dry-run-show [--json]

# 77D — Package Approval
pcae phase real-captured-task-package-approval --approve --approved-by "<name>" --reason "<reason>" [--json] [--save]
pcae phase real-captured-task-package-approval-show [--json]

# 77E — Backend Capture Preflight
pcae phase real-captured-task-backend-capture-preflight [--json] [--save]
pcae phase real-captured-task-backend-capture-preflight-show [--json]

# 77F — Backend Capture
pcae phase real-captured-task-backend-capture [--dry-run | --execute] [--json] [--save]
pcae phase real-captured-task-backend-capture-show [--json]

# 77G — Result Intake
pcae phase real-backend-capture-result-intake [--json] [--save]
pcae phase real-backend-capture-result-intake-show [--json]

# 77H — Timeout Policy
pcae phase backend-capture-timeout-policy [--json] [--save]
pcae phase backend-capture-timeout-policy-show [--json]

# 77I — Retry Preflight
pcae phase backend-capture-retry-preflight [--json] [--save]
pcae phase backend-capture-retry-preflight-show [--json]

# 77J — Governed Retry
pcae phase backend-capture-governed-retry [--dry-run | --execute] [--json] [--save]
pcae phase backend-capture-governed-retry-show [--json]
```

### Return Codes

- `0`: Success — phase gate passed, artifact is in ready/approved/prepared state
- `1`: Blocked — one or more gates failed, artifact reports blocked status

### Common Flags

- `--json`: Machine-readable JSON output to stdout
- `--save`: Persist the artifact to its `.pcae/` directory
- `--dry-run`: (77F, 77J) Validate without invoking the backend
- `--execute`: (77F, 77J) Perform the actual backend invocation

---

## 8. Setting Up a Future Real Captured Task

To create a new real captured task (e.g., `REAL-CAPTURED-TASK-002`), follow
this sequence. Each step must complete successfully before the next begins.

### Prerequisites

- PCAE is in clean healthy idle state (`pcae health` passes, no active task)
- Git working tree is clean
- Real execution is disabled
- An agent lock is acquired (`pcae agent acquire`)

### Step-by-Step

1. **77A — Run the readiness gate.**
   ```bash
   pcae phase real-captured-task-readiness-gate --json --save
   ```
   Confirm `readiness_status` is `ready_for_real_task_preparation`.

2. **77B — Prepare the task contract.**
   The contract defines the new task's goal, allowed files, and forbidden
   actions. Update the contract preparation logic (in `src/pcae/commands/phase.py`,
   `_build_real_captured_task_contract`) to produce the new task's contract,
   or create the contract manually following the REAL-CAPTURED-TASK-001
   template.

3. **77C — Create the package dry-run.**
   ```bash
   pcae phase real-captured-task-package-dry-run --json --save
   ```
   Record the `package_digest` — it will be required for approval.

4. **77D — Approve the package.**
   ```bash
   pcae phase real-captured-task-package-approval \
     --approve \
     --approved-by "Your Name" \
     --reason "Reason for approval" \
     --json --save
   ```
   This is the explicit human approval gate. Without it, 77E will block.

5. **77E — Run the capture preflight.**
   ```bash
   pcae phase real-captured-task-backend-capture-preflight --json --save
   ```
   Confirm `backend_capture_preflight_status` is `ready_for_backend_capture`.

6. **77F — Execute the backend capture.**
   ```bash
   pcae phase real-captured-task-backend-capture --execute --json --save
   ```

7. **77G — Classify the capture outcome.**
   ```bash
   pcae phase real-backend-capture-result-intake --json --save
   ```

8. **Follow the fork.**
   - If `capture_outcome = "captured"`: proceed to output intake.
   - If `capture_outcome = "timeout_failure"`: enter the retry path (steps 9–11).
   - For other outcomes: follow the prescribed next action.

### If the Backend Times Out (Retry Path)

9. **77H — Create the timeout policy.**
   ```bash
   pcae phase backend-capture-timeout-policy --json --save
   ```

10. **77I — Run the retry preflight.**
    ```bash
    pcae phase backend-capture-retry-preflight --json --save
    ```
    Confirm `backend_retry_preflight_status` is `ready_for_retry`.

11. **77J — Execute the governed retry.**
    ```bash
    pcae phase backend-capture-governed-retry --execute --json --save
    ```

---

## 9. Governance Boundaries

### What This Path Authorizes

- Invocation of a **locked backend** (pre-approved, specific agent target)
  under governed conditions
- Capture of backend stdout and stderr as persisted artifacts
- Classification of capture outcomes
- A single governed retry attempt when the initial capture times out

### What This Path Does NOT Authorize

- **No automatic retry.** Retry requires explicit policy (77H), preflight
  (77I), and execution (77J) phases.
- **No unbounded retry.** The timeout policy allows exactly 1 additional
  attempt.
- **No repository mutation.** Every phase sets `apply_performed=false` and
  `files_modified=false`.
- **No commit or push.** These remain exclusively human actions outside the
  governance path.
- **No execution authorization.** Every phase sets `execution_allowed=false`
  and `execution_authorized=false`.
- **No output application.** Captured output is stored for human review, not
  automatically applied to the repository.
- **No backend switching.** The locked backend target is fixed in the contract
  and validated at preflight.
- **No multi-task execution.** Each real captured task traverses the governance
  path independently.

---

## 10. Relationship to PCAE Governance Model

The real captured task governance path is a specialization of PCAE's general
governance model (see [GOVERNANCE_HANDBOOK.md](governance/GOVERNANCE_HANDBOOK.md)).
It instantiates the following governance domains:

| Governance Domain | How It Applies |
|-------------------|----------------|
| **Change Governance** | The task contract (77B) declares allowed files and forbidden actions |
| **Execution Governance** | The gate chain (77A→77E) ensures no backend is invoked until all preconditions are met |
| **Audit Governance** | Every phase produces a structured, machine-readable artifact |
| **Evidence Governance** | The artifact chain (77A→77J) forms a complete evidence record of the captured task |
| **Human Authority** | Package approval (77D) requires explicit, recorded human approval |

The governance path does **not** exercise:
- **Rollback Governance** — no writes are performed, so no rollback is needed
- **Prompt Governance** — the prompt is an envelope, not a governed prompt artifact
- **Runtime Governance** — the backend is locked, not runtime-assessed
- **Multi-Agent Governance** — single backend, single invocation

---

## 11. Phase 77 Series Implementation History

| Phase | Commit | Description |
|-------|--------|-------------|
| 77A | (initial) | Real captured task readiness gate |
| 77B | (initial) | Real captured task contract preparation |
| 77C | (initial) | Real captured task package dry-run |
| 77D | (initial) | Real captured task package approval |
| 77E | (initial) | Real captured task backend capture preflight |
| 77F | (initial) | Real captured task backend capture |
| 77G | (initial) | Real backend capture result intake |
| 77H | `d159ff09` | Backend capture timeout policy |
| 77I | `e875ef4b` → `257b2f32` | Backend capture retry preflight |
| 77J | `4e5be39d` → `cd7205b1` | Backend capture governed retry |

---

## 12. License

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

See the [LICENSE](../LICENSE) file for the full license text.
