# Phase 93C — Shell Gate Audit Evidence Model

```
phase_name    = phase_93c_shell_gate_audit_evidence_model
phase_version = 1.0
phase_status  = completed
implementation_status = simulation_only
recommended_next_phase = TBD
```

## 1. Purpose

Add a simulation-only audit evidence model to the narrow shell gate so each `pcae shell-gate check --command "<command>" [--json]` decision produces structured, redacted, durable audit evidence without executing, intercepting, blocking, or enforcing commands.

## 2. Audit Evidence Schema

Every shell-gate check result includes an `audit_evidence` object:

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | str | Unique event identifier (`sg-<uuid12>`) |
| `event_type` | str | `shell_gate.allow`, `shell_gate.deny`, `shell_gate.human_review`, `shell_gate.more_evidence` |
| `timestamp_utc` | str | ISO 8601 timestamp |
| `command_hash` | str | SHA-256 hex of the original (unredacted) command |
| `redacted_command` | str | Command with secrets replaced by `[REDACTED]` |
| `redaction_applied` | bool | True if any secret patterns were detected and redacted |
| `command_class` | str | Broker command class |
| `command_category` | str | Shell gate classifier category |
| `action_type` | str | Broker action type |
| `decision` | str | allow / deny / human_review / more_evidence |
| `hard_block` | bool | Non-overridable block (88V §16) |
| `reason_code` | str | Primary machine-readable reason |
| `reason_codes` | list[str] | All reason codes |
| `required_evidence` | list[str] | Evidence items needed |
| `message_summary` | str | First 200 chars of broker message |
| `broker_event_id` | str\|null | Cross-reference to broker audit payload |
| `broker_message_hash` | str\|null | SHA-256 prefix of broker message |
| `simulation_only` | bool | Always true |
| `no_execution` | bool | Always true |
| `no_enforcement` | bool | Always true |
| `source` | str | `"shell_gate"` |
| `schema_version` | str | `"1.0"` |

## 3. Redaction Model

### 3.1 Detected Patterns

- **Environment variables**: `TOKEN=value`, `API_KEY=value`, `PASSWORD=value`, `SECRET=value`, `BEARER=value`, and 15+ other known secret var names
- **Flag values**: `--token <value>`, `--password <value>`, `--api-key <value>`, `--secret <value>`, etc.
- **Bearer tokens**: `Authorization: Bearer <token>`

### 3.2 Redaction Behavior

- The original command is used for classification and hashing (integrity preserved)
- The `command_hash` is SHA-256 of the original unredacted command
- The `redacted_command` replaces secret values with `[REDACTED]`
- The top-level `command_text` field is also redacted
- If the entire command is secret-bearing, the command text becomes `<redacted_command>`

### 3.3 Examples

```
Input:  OPENAI_API_KEY=sk-abc123 curl api.example.com
Output: OPENAI_API_KEY=[REDACTED] curl api.example.com
        redaction_applied: true

Input:  api-client --token ghp_secret123 call-api
Output: api-client --token [REDACTED] call-api
        redaction_applied: true

Input:  git push --force
Output: git push --force
        redaction_applied: false
```

## 4. Command Hash Behavior

- SHA-256 of the original (unredacted) command text
- Same command always produces the same hash
- Different commands always produce different hashes (except collisions)
- Hash is verifiable but non-reversible (does not leak original command)

## 5. Relationship to Permission Broker Audit Payload

The shell gate audit evidence extends the broker's `audit_payload`:
- `broker_event_id` cross-references the broker's `event_id`
- `broker_message_hash` cross-references the broker's message
- Shell gate audit sits above broker audit in the evidence chain

## 6. Simulation-Only Boundary

The audit evidence is simulation-only:
- Not written to disk
- Not persisted
- Not part of an audit chain
- `simulation_only`, `no_execution`, `no_enforcement` always true
- Exists to demonstrate what future enforcement audit records would contain

## 7. Non-Goals

- No disk-based audit storage
- No audit chain integrity (checksum chains)
- No persistent audit database
- No shell interception, wrappers, or command mediation
- No backend invocation or command execution
- No Telegram inbound control, remote shell, /run
- No enforcement or real blocking

## 8. CLI Behavior

### 8.1 JSON Output

```json
{
  "audit_evidence": {
    "audit_id": "sg-a1b2c3d4e5f6",
    "event_type": "shell_gate.deny",
    "command_hash": "3075ad321adde596...",
    "redacted_command": "git push --force",
    "decision": "deny",
    "hard_block": true,
    "simulation_only": true,
    ...
  }
}
```

### 8.2 Text Output

```
Shell gate check (simulation only — Phase 93C)
  Command:            'git push --force'
  ...
  Audit ID:           sg-a1b2c3d4e5f6
  Command hash:       3075ad321adde596...
```

## 9. Examples

### Allow decision
```json
{"audit_evidence": {"event_type": "shell_gate.allow", "decision": "allow", "hard_block": false}}
```

### Deny hard-block
```json
{"audit_evidence": {"event_type": "shell_gate.deny", "decision": "deny", "hard_block": true, "reason_code": "blocked_by_force_push"}}
```

### Unknown fail-closed
```json
{"audit_evidence": {"event_type": "shell_gate.deny", "decision": "deny", "hard_block": true, "command_class": "unknown"}}
```

## 10. No-Go Conditions

- No shell interception, wrappers, or command mediation
- No backend invocation or command execution
- No Telegram inbound control, remote shell, /run
- No enforcement or real blocking
- No secret leakage in audit output
- No test weakening, xfail, or skip

## 11. Test Coverage

| Category | Tests |
|----------|-------|
| Audit evidence exists (allow/deny/unknown) | 3 |
| Required fields | 6 |
| Command hash (present, stable, different) | 3 |
| Command redaction (API key, password, token) | 6 |
| Audit invariants | 6 |
| 93B compatibility | 3 |
| CLI JSON audit | 4 |
| CLI text audit | 3 |
| **Total new** | **32** |

122 total shell gate tests (90 original + 32 new).

---

*Phase 93C implements the simulation-only shell gate audit evidence model. 32 new tests pass. No shell interception, wrappers, command mediation, backend invocation, Telegram inbound control, remote shell, /run, enforcement, or command execution path was implemented.*
