# Phase 89H — Enforcement Readiness Audit and Rollback Model Design

```
phase_name    = phase_89h_enforcement_audit_and_rollback_model
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89i_enforcement_approval_and_accepted_risk_policy
```

## 1. Purpose

Design the audit event model, rollback evidence model, recovery paths, and integrity requirements that must exist before any future enforcement prototype can block commands. Enforcement without audit is unaccountable; enforcement without rollback is irreversible. This phase defines both.

## 2. Scope

In scope (design only):

- Audit event taxonomy and schemas
- Rollback artifact schema and creation workflow
- Evidence chain requirements for enforcement decisions
- Integrity and tamper-evidence requirements
- Retention and rotation policies
- Recovery workflow (enforcement → disabled)
- Rollback workflow (enforcement → simulation)
- Failure modes for audit and rollback
- Tests required before implementation

Out of scope: Implementation, enforcement, blocking, shell interception, wrappers.

## 3. Non-Goals

89H must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, authorization, or any source/test changes.

## 4. Starting Point from 89G

89G identified 34 threats, including:
- T26: Missing audit record for enforcement action
- T27: Audit log tampering
- T28: Inability to rollback enforcement
- T29: Rollback leaves system in inconsistent state
- F9–F11: Audit write failure, disk full, raw secrets in audit

89G defined 10 safety claims including:
- SC-4: PCAE must preserve audit evidence
- SC-5: PCAE must preserve rollback ability

89G defined must-not-proceed conditions:
- MNP-3: No audit model implemented
- MNP-4: No rollback model implemented

89H designs the audit and rollback models that satisfy these requirements.

## 5. Audit Goals

1. **Non-repudiation:** Every enforcement decision must produce an auditable, tamper-evident record.
2. **Traceability:** Every enforcement action must be traceable to the evidence that produced it.
3. **Integrity:** Audit records must be tamper-evident. Modification or deletion must be detectable.
4. **Redaction:** Audit records must never contain raw secret text.
5. **Availability:** Audit records must be available for review without disrupting operations.
6. **Retention:** Audit records must be retained for a defined period with clear rotation policy.

## 6. Audit Event Taxonomy

### 6.1 Event Types

| Event Type | Trigger | Severity |
|-----------|---------|----------|
| `enforcement.decision` | PCAE evaluates a command under enforcement | Info |
| `enforcement.blocked` | Command was blocked by enforcement | Warning |
| `enforcement.allowed` | Command was allowed by enforcement | Info |
| `enforcement.gated_review` | Command requires human review | Info |
| `enforcement.denied` | Command was permanently denied | Critical |
| `enforcement.bypass_detected` | Operator bypassed enforcement | Critical |
| `enforcement.error` | Enforcement encountered an internal error | Error |
| `approval.granted` | Human approval was granted for an action | Warning |
| `approval.expired` | Human approval expired | Info |
| `approval.revoked` | Human approval was revoked | Warning |
| `risk.accepted` | Operator accepted a risk | Warning |
| `risk.expired` | Accepted risk expired | Info |
| `rollback.created` | Rollback artifact was created | Info |
| `rollback.restored` | Rollback was executed | Critical |
| `enforcement.disabled` | Enforcement was disabled | Critical |
| `enforcement.enabled` | Enforcement was enabled | Critical |

## 7. Enforcement Decision Event Schema

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "enforcement.blocked",
  "timestamp": "<ISO 8601>",
  "operator": {
    "user": "<username>",
    "agent_id": "<agent-id or null>",
    "session_id": "<session-id>"
  },
  "command": {
    "text_hash": "<sha256>",
    "text_redacted": "<redacted command or sentinel>",
    "category": "<shell_gate_category>",
    "action": "<requested_action>"
  },
  "decision": {
    "broker": "<broker_decision>",
    "shell_gate": "<sg_decision>",
    "simulation": "<would_* decision>",
    "severity": "<severity>",
    "hard_block": true
  },
  "outcome": {
    "action": "blocked",
    "enforced": true,
    "governed_alternative": "pcae push",
    "operator_bypassed": false
  },
  "repository": {
    "root": "<path>",
    "commit": "<HEAD sha>",
    "branch": "<branch>",
    "task_contract": "<task-id or null>"
  },
  "evidence": {
    "health_passed": true,
    "check_passed": true,
    "sources": ["shell_gate", "broker", "scope_preflight"]
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256 of event>"
  }
}
```

## 8. Command Attempt Event Schema

When an operator runs a command directly (bypassing PCAE governance), the bypass detection system produces:

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "enforcement.bypass_detected",
  "timestamp": "<ISO 8601>",
  "operator": {
    "user": "<username>",
    "shell_pid": 12345
  },
  "command": {
    "text_hash": "<sha256>",
    "text_redacted": "<redacted>",
    "detected_via": "shell_hook",
    "was_classified": true,
    "would_have_been": "blocked"
  },
  "outcome": {
    "action": "logged_only",
    "enforced": false,
    "note": "Bypass logged; enforcement was active but operator used direct shell"
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

## 9. Human Approval Event Schema

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "approval.granted",
  "timestamp": "<ISO 8601>",
  "approval": {
    "approved_by": "<username>",
    "approved_action": "<action description>",
    "approved_command_hash": "<sha256>",
    "scope": ["<file>", "..."],
    "expires_at": "<ISO 8601>",
    "revocable": true
  },
  "decision_context": {
    "original_decision": "would_require_human_review",
    "hard_block_present": false,
    "approval_changes_outcome": true
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

## 10. Accepted-Risk Event Schema

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "risk.accepted",
  "timestamp": "<ISO 8601>",
  "risk": {
    "accepted_by": "<username>",
    "risk_level": "medium",
    "risk_description": "<specific risk being accepted>",
    "scope": ["<action>", "<files>"],
    "expires_at": "<ISO 8601>",
    "hard_block_override": false,
    "hard_block_note": "Accepted risk never overrides hard blocks (88V §16)"
  },
  "decision_context": {
    "original_decision": "would_require_human_review",
    "hard_block_present": false
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

## 11. Hard-Block Event Schema

Hard blocks produce a distinct event type because they are non-overridable:

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "enforcement.blocked",
  "timestamp": "<ISO 8601>",
  "hard_block": {
    "reason": "blocked_by_force_push",
    "source": "shell_gate",
    "overridable": false,
    "overridden_by": null,
    "overridden": false,
    "permanent": true
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

## 12. Rollback Artifact Schema

### 12.1 Pre-Mutation Snapshot

Before any governed mutation, PCAE creates a rollback artifact:

```json
{
  "rollback_id": "rb-<uuid12>",
  "created_at": "<ISO 8601>",
  "mutation": {
    "type": "source_mutation",
    "action": "write",
    "files": ["src/pcae/core/example.py"],
    "expected_change": "Add enforcement module"
  },
  "pre_state": {
    "commit": "<HEAD sha before mutation>",
    "file_hashes": {
      "src/pcae/core/example.py": "<sha256>"
    },
    "working_tree_clean": true
  },
  "rollback_instructions": {
    "method": "git_checkout",
    "target": "<HEAD sha before mutation>",
    "files": ["src/pcae/core/example.py"]
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

### 12.2 Rollback Execution Record

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "rollback.restored",
  "timestamp": "<ISO 8601>",
  "rollback_id": "rb-<uuid12>",
  "restored_by": "<username>",
  "outcome": {
    "success": true,
    "files_restored": ["src/pcae/core/example.py"],
    "commit_after": "<HEAD sha after rollback>",
    "working_tree_clean": true
  },
  "integrity": {
    "schema_version": "0.1",
    "checksum": "<sha256>"
  }
}
```

## 13. Evidence Chain Requirements

### 13.1 Chain of Custody

Every enforcement decision must be traceable through:

```
command_text → shell_gate classification → broker decision
  → simulation decision → enforcement action → audit record
```

The audit record must reference:
- Shell gate reason codes
- Broker decision and reason codes
- Evidence sources consulted
- Any contradictions detected
- Whether human approval or accepted risk was present

### 13.2 Evidence Integrity

- Each audit record is checksummed (SHA-256)
- Checksums form a chain: each record includes the previous record's checksum
- Chain validation detects insertion, deletion, or modification
- Chain break → enforcement degraded to simulation-only until chain is repaired

## 14. Integrity/Tamper-Evidence Requirements

### 14.1 Per-Record Integrity

- Every audit record has a `checksum` field: SHA-256 of the record content (excluding the checksum field itself)
- Records are written atomically: either the full record is written or nothing is
- Partial writes are detectable and treated as corruption

### 14.2 Chain Integrity

- Each record includes `previous_checksum` referencing the prior record
- The first record in a log file has `previous_checksum: null`
- Chain validation: for each record N, verify `sha256(record_N) == record_N+1.previous_checksum`
- Chain break → enforcement degraded, operator notified

### 14.3 Tamper Detection

- Manual modification of any record changes its checksum
- Deletion of any record breaks the chain
- Insertion of a forged record breaks the chain (previous_checksum won't match)
- All three are detectable by chain validation

## 15. Retention/Rotation Requirements

### 15.1 Log Structure

```
.pcae/enforcement/
  audit-2026-06-28-001.jsonl    (max 10MB)
  audit-2026-06-28-002.jsonl    (max 10MB)
  audit-2026-06-29-001.jsonl    (max 10MB)
  rollbacks/
    rb-<uuid12>.json            (one per rollback artifact)
```

### 15.2 Rotation Policy

| Parameter | Value |
|-----------|-------|
| Max file size | 10 MB |
| Max total files | 100 |
| Max total size | 1 GB |
| Rotation trigger | File reaches 10MB |
| Oldest file deletion | When total exceeds 100 files or 1GB |
| Retention minimum | 30 days |

### 15.3 Cleanup

- `pcae enforcement audit prune --older-than 30d` — manual cleanup
- Automatic cleanup on rotation when limits exceeded
- Cleanup logged as audit event `enforcement.audit_pruned`

## 16. Recovery Workflow

### 16.1 Enforcement → Disabled

```
1. Operator detects enforcement issue
   (false block, performance problem, unexpected behavior)

2. Operator runs: pcae enforcement disable
   Requires: operator confirmation ("disable" must be typed)
   Produces: audit event enforcement.disabled
   Effect: enforcement reverts to simulation-only immediately

3. Operator verifies: pcae enforcement status
   Shows: enforcement_mode: disabled, since: <timestamp>

4. Operator continues working with simulation-only mode

5. Operator may re-enable: pcae enforcement enable
   Requires: operator confirmation
   Produces: audit event enforcement.enabled
```

### 16.2 Degraded Mode

If audit chain is broken or audit write fails:
- Enforcement automatically degrades to simulation-only
- Operator notified: "Enforcement degraded: audit integrity cannot be verified"
- All commands evaluated but not blocked
- Audit events still produced (best-effort) for the degradation itself

## 17. Rollback Workflow

### 17.1 Pre-Mutation Rollback Creation

```
1. Operator initiates governed mutation
   (pcae commit implementation, write, etc.)

2. PCAE creates rollback artifact BEFORE mutation
   - Snapshots current state of files to be modified
   - Records git HEAD commit
   - Creates rollback artifact in .pcae/enforcement/rollbacks/

3. PCAE performs mutation

4. If mutation succeeds: rollback artifact retained for 30 days
   If mutation fails: rollback artifact used to restore pre-state
```

### 17.2 Operator-Initiated Rollback

```
1. Operator wants to undo a governed mutation

2. Operator runs: pcae enforcement rollback list
   Shows: available rollback artifacts with timestamps and descriptions

3. Operator runs: pcae enforcement rollback restore <rollback_id>
   Requires: operator confirmation
   Produces: audit event rollback.restored
   Effect: files restored to pre-mutation state

4. Operator verifies: git status, git diff
```

## 18. Failure Modes

| # | Failure | Detection | Recovery |
|---|---------|-----------|----------|
| F1 | Audit write fails (disk full) | Write error, enforcement degrades | Free disk space, re-enable |
| F2 | Audit chain broken | Chain validation on read | Degrade to simulation, repair chain |
| F3 | Rollback artifact corrupted | Checksum verification on restore | Use git reflog as fallback |
| F4 | Rollback artifact missing | File not found | Use git reflog as fallback |
| F5 | Concurrent audit writes conflict | File lock, retry with backoff | Atomic write with lock |
| F6 | Audit log deleted by operator | Chain gap detected | Degrade enforcement, notify |
| F7 | Rollback to wrong state | Operator confirms rollback target | Second rollback to correct state |

## 19. Tests Required Before Implementation

| Category | Tests | Description |
|----------|-------|-------------|
| Audit write | 10 | Events written correctly, checksums valid |
| Audit read | 5 | Events readable, chain validatable |
| Audit chain integrity | 8 | Tamper detection, chain break detection |
| Audit redaction | 5 | No raw secrets in audit records |
| Rollback create | 8 | Artifact created before mutation |
| Rollback restore | 8 | Files restored correctly |
| Rollback integrity | 5 | Corrupted artifact detection, fallback |
| Recovery workflow | 6 | Disable/enable, degrade, status |
| Rotation | 5 | File rotation, limits, cleanup |
| **Total** | **~60** | |

## 20. Recommended Next Phase

**89I — Enforcement Operator Approval and Accepted-Risk Policy Design**
