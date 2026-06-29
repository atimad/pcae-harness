# Phase 93D — Shell Gate Audit Persistence Design

```
phase_name    = phase_93d_shell_gate_audit_persistence_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 93E — Shell Gate Audit Persistence Implementation
```

## 1. Purpose and Scope

### 1.1 Purpose

Design how shell-gate audit evidence (Phase 93C) should be persisted as durable audit artifacts. Phase 93C produces structured audit evidence in memory for every `pcae shell-gate check` decision. This phase defines where, how, and with what integrity guarantees that evidence should be written to disk.

### 1.2 Why Audit Persistence Is Needed

- **Traceability**: Every shell-gate decision should leave a durable, non-repudiable record
- **Auditability**: Future phases can inspect historical decisions for debugging, compliance, and governance review
- **Phase report integration**: Phase reports can summarize audit counts (e.g., "12 shell-gate checks blocked this phase")
- **Breach investigation**: If a governed command bypasses PCAE, audit records provide forensic evidence

### 1.3 Simulation Evidence vs Durable Persistence

| Phase 93C (Current) | Phase 93E+ (This Design) |
|---|---|
| Audit evidence in memory only | Audit evidence written to `.pcae/shell-gate-audit/` |
| No disk state | Durable JSON artifacts |
| No chain integrity | SHA-256 per-record hash; optional chain |
| No retention policy | Retention: 100 records max, 30 days default |

### 1.4 Persistence Must Not Imply Enforcement

Writing audit records is a **read-only side effect** of simulation. It does not:
- Block, allow, or gate real shell commands
- Modify shell behavior
- Authorize execution
- Grant or deny any permission

The shell gate remains simulation-only. Audit persistence adds a durable record of what the simulation decided — nothing more.

## 2. Non-Goals

93D is design-only. The following are explicitly not designed or implemented:

- Shell interception, wrappers, or command mediation
- Command execution through PCAE
- Real enforcement or command blocking
- Backend invocation
- Telegram inbound control, remote shell, /run
- Audit-chain cryptographic verification (deferred to future phase)
- Automatic audit log rotation/cleanup (deferred)

## 3. Persistence Artifact Model

### 3.1 Directory Layout

```
.pcae/shell-gate-audit/
  latest.json                          ← always points to most recent record
  20260629-091200-sg-a1b2c3d4e5f6.json ← timestamped individual records
  20260629-091215-sg-f6e5d4c3b2a1.json
```

### 3.2 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Format | Individual JSON files | Aligns with `.pcae/phase-reports/` pattern |
| Naming | `<YYYYMMDD-HHMMSS>-<audit_id>.json` | Sortable, unique, human-readable |
| Latest pointer | `latest.json` | Fast lookup, matches phase-reports convention |
| Retention | 100 max files, 30-day age limit | Matches existing PCAE retention patterns |
| Versioning | `schema_version` in each record | Forward compatibility |

### 3.3 Why Not JSONL

JSONL (one JSON object per line, appended to a single file) was considered but rejected for v1:
- Individual files are easier to inspect, rotate, and test independently
- Matches existing `.pcae/phase-reports/` convention
- JSONL append requires file locking for concurrent access

## 4. Audit Record Schema

Each persisted record extends the 93C audit_evidence with persistence-specific fields:

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | str | Unique `sg-<uuid12>` |
| `schema_version` | str | `"1.0"` |
| `timestamp_utc` | str | ISO 8601 |
| `phase_id` | str\|null | Active phase ID at time of check |
| `task_id` | str\|null | Active task contract ID |
| `command_hash` | str | SHA-256 of original command |
| `redacted_command` | str | Command with secrets → `[REDACTED]` |
| `redaction_applied` | bool | True if secrets were detected |
| `command_class` | str | Broker command class |
| `command_category` | str | Shell gate classifier category |
| `action_type` | str | Broker action type |
| `decision` | str | allow / deny / human_review / more_evidence |
| `hard_block` | bool | Non-overridable (88V §16) |
| `reason_code` | str | Primary reason |
| `reason_codes` | list[str] | All reason codes |
| `required_evidence` | list[str] | Missing evidence items |
| `message_summary` | str | First 200 chars of broker message |
| `broker_event_id` | str\|null | Cross-reference to broker audit |
| `broker_message_hash` | str\|null | SHA-256 prefix of broker message |
| `simulation_only` | bool | Always true |
| `no_execution` | bool | Always true |
| `no_enforcement` | bool | Always true |
| `source` | str | `"shell_gate"` |
| `persisted_at` | str | ISO 8601 write timestamp |
| `record_digest` | str | SHA-256 of the record (excluding digest field itself) |

## 5. Redaction and Privacy

### 5.1 Persisted Content

- **Redacted command only** — raw command text never persisted
- **Command hash** — SHA-256 for integrity verification without exposing original
- **No raw secrets** — API keys, tokens, passwords replaced with `[REDACTED]`
- **No token/chat ID** — Telegram credentials never appear in audit records

### 5.2 Secret Handling

The existing `_redact_command_text()` from Phase 93C handles:
- Environment variable patterns (`TOKEN=`, `API_KEY=`)
- Flag patterns (`--token`, `--password`)
- Bearer token patterns

What is persisted is the **already redacted** output from `check_shell_gate()` — no additional redaction pass is needed at persistence time.

## 6. Integrity Model

### 6.1 Per-Record Hashing

Each audit record includes a `record_digest`: SHA-256 of the record JSON with the `record_digest` field set to `""`. This provides:
- Tamper detection: modifying any field changes the digest
- Integrity verification: `pcae shell-gate audit verify` can recompute and compare

### 6.2 Optional Chain Hashing (Future)

A chained hash (each record includes `previous_digest`) would provide append-only integrity. This is deferred to a future phase after basic persistence is stable.

### 6.3 Out of Scope for v1

- Cryptographic signatures (Ed25519, GPG)
- Merkle tree construction
- External audit verification tools
- Automatic integrity monitoring

## 7. Relationship to Permission Broker Audit Payload

| Layer | Scope | Persisted |
|-------|-------|-----------|
| **Shell gate audit** | Command classification, shell-gate decision | Yes (this design) |
| **Broker audit** | Broker decision, hard-block status | Cross-referenced via `broker_event_id` |
| **Phase report** | Phase completion summary | Separate (`.pcae/phase-reports/`) |

The shell gate audit is the **outer context** — what command was proposed, how it was classified, and what the shell gate decided. The broker audit is the **decision context** — embedded within the shell gate record via `broker_event_id` and `broker_message_hash`. They do not conflict; the shell gate audit wraps the broker decision.

## 8. Relationship to Phase Reports and Telegram

- **Phase reports** may summarize audit counts (e.g., "Shell-gate checks: 15 blocked, 42 allowed")
- **Telegram** should NOT include raw audit details (too verbose, potential secret exposure)
- **Full audit artifacts** are local/durable in `.pcae/shell-gate-audit/`
- **Notification** of audit events is deferred — Telegram already reports phase completion

## 9. CLI Design for Future Implementation

Design the following commands (do not implement in 93D):

### 9.1 `pcae shell-gate audit show --latest [--json]`

Shows the most recent audit record.

```
$ pcae shell-gate audit show --latest
Shell gate audit — latest
  Audit ID:      sg-a1b2c3d4e5f6
  Timestamp:     2026-06-29T09:12:00Z
  Command:       git push --force
  Decision:      deny
  Hard block:    True
  Reason:        blocked_by_force_push
  Phase:         93D
```

### 9.2 `pcae shell-gate audit list [--json] [--limit N]`

Lists recent audit records.

```
$ pcae shell-gate audit list --limit 5
20260629-091200  deny    blocked_by_force_push          git push --force
20260629-091100  allow   allow_preflight_only           git status
```

### 9.3 `pcae shell-gate audit verify [--json]`

Verifies integrity of all audit records.

```
$ pcae shell-gate audit verify
12 records checked, 0 integrity failures
```

## 10. Failure and Degraded-Mode Behavior

| Failure | Behavior |
|---------|----------|
| Audit directory cannot be created | Shell-gate check proceeds; audit persistence skipped; warning returned |
| Write permission denied | Shell-gate check proceeds; audit persistence skipped; error logged |
| Disk full | Shell-gate check proceeds; audit persistence skipped; error logged |
| Record digest mismatch on verify | Record marked as tampered; operator notified |
| `latest.json` corrupted | Rebuild from timestamped files |

**Key invariant**: Audit persistence failure is non-fatal to shell-gate check. The simulation decision is always produced and returned. Persistence is a best-effort side effect.

## 11. Test Strategy for Future Implementation

| # | Category | Planned Tests |
|---|----------|--------------|
| 1 | Record write | Write record, verify file exists with correct fields |
| 2 | Latest pointer | `latest.json` points to most recent record |
| 3 | Timestamped naming | Filename format `<timestamp>-<audit_id>.json` |
| 4 | Redaction | Redacted commands in persisted records |
| 5 | Hash stability | Same command → same `command_hash` and `record_digest` |
| 6 | Tamper detection | Modified record detected by `audit verify` |
| 7 | No execution | Shell-gate check never executes commands |
| 8 | Failure behavior | Missing dir / permission denied → non-fatal |
| 9 | CLI show | `audit show --latest` produces correct output |
| 10 | CLI list | `audit list --limit N` returns correct count |
| 11 | CLI verify | `audit verify` reports integrity status |
| 12 | Broker cross-reference | `broker_event_id` present in record |
| 13 | Phase/task context | `phase_id` and `task_id` captured when available |
| 14 | Retention | Old records pruned when exceeding max count/age |

**Estimated new tests: ~40**

## 12. Go/No-Go Criteria for Future Implementation

| # | Criterion |
|---|-----------|
| G1 | 93D design document reviewed and approved |
| G2 | Shell-gate audit evidence model (93C) stable |
| G3 | All existing shell-gate tests pass (122/122) |
| G4 | Fast-green baseline clean |
| G5 | Active task contract for implementation phase |
| G6 | Operator explicitly authorizes implementation |
| G7 | No enforcement, interception, or execution path exists |
| G8 | Audit directory `.pcae/shell-gate-audit/` added to `.pcae/.gitignore` |

## 13. Open Questions

| # | Question | Current Thinking |
|---|----------|-----------------|
| 1 | Always-on or opt-in? | Initially opt-in via `PCAE_SHELL_GATE_AUDIT=1` env var; become always-on after stabilization |
| 2 | JSONL vs individual files? | Individual JSON files (matches phase-reports convention) |
| 3 | Retention policy? | 100 max files, 30-day age limit (matches existing patterns) |
| 4 | Should audit artifacts be committed? | No — `.pcae/shell-gate-audit/` added to `.pcae/.gitignore` |
| 5 | Concurrent check safety? | Individual files with unique names; `latest.json` updated atomically via write-to-temp-then-rename |
| 6 | Audit across phases? | `phase_id` in each record enables cross-phase audit aggregation |

---

*Phase 93D is a design-only phase. No audit persistence, shell interception, wrappers, command mediation, backend invocation, Telegram inbound control, remote shell, /run, enforcement, or command execution path was designed or implemented. The design defines what future implementation will build.*
