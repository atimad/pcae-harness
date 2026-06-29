# Phase 94I — Backend Review/Apply Governance Design

```
phase_name    = phase_94i_backend_review_apply_governance_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 94J — Backend Review State Model
```

## 1. Purpose

Design how PCAE should review, approve, reject, and safely apply quarantined backend output artifacts. Output capture (94D) ensures output is quarantined; trust assessment (94H) verifies lifecycle state. This phase defines the governance layer that controls **whether and how** output moves from quarantine to application.

### Key Distinctions

| State | Meaning |
|-------|---------|
| Captured | Output artifact exists, redacted, quarantined |
| Reviewed | Operator has examined output content |
| Approved | Operator has explicitly approved for application |
| Applied | Changes have been applied to the repository (future, gated) |

Output capture does NOT imply adoption. Trust assessment is necessary but NOT sufficient for application. Human approval is always required for mutation.

## 2. Non-Goals

Design-only. The following are explicitly not implemented:

- Review/apply commands, patch parsing, file mutation
- Backend invocation, subprocess, network calls
- Shell wrappers, interception, command mediation
- Telegram inbound, remote shell, /run
- Enforcement, autonomous mutation, automatic commit/push

## 3. Review State Model

| State | Description | Production v1? |
|-------|-------------|---------------|
| `captured` | Output artifact written, quarantined | ✅ Current (94D) |
| `quarantined` | Output isolated, not yet reviewed | ✅ Current (94D) |
| `review_pending` | Output awaiting operator review | Future |
| `reviewed` | Operator has examined output | Future |
| `approved_for_apply` | Operator approved; apply-ready check pending | Future |
| `rejected` | Operator rejected output | Future |
| `apply_ready` | All checks passed; can be applied | Future |
| `applied` | Changes applied to repo | Future (gated) |
| `apply_failed` | Apply attempted but failed | Future |
| `rolled_back` | Changes applied then rolled back | Future |

## 4. Apply Readiness Model

Before output can be applied, all of these must be true:

- Active task contract exists
- Output artifact exists and hash verified
- Output remains quarantined (not previously applied)
- Trust/readiness assessment is `complete` or `ready`
- Backend audit record is present and verified
- Allowed files known from task scope
- Forbidden files not in proposed change set
- Proposed change set extracted and validated
- No hard blocks present
- Human approval recorded (artifact with hash binding)
- Rollback plan prepared
- Required tests/checks identified
- Commit and push are separate, governed steps

## 5. Human Approval Model

- Human approval is **required** before any apply
- Approval cannot override hard blocks (88V §16)
- Accepted risk cannot override hard blocks
- Approval recorded as artifact: `approval_id`, `timestamp`, `operator`, `decision`, `reason`
- Approval binds to exact `output_hash` and `request_id`
- Approval expires (default: 1 hour for mutations)
- Approval is auditable and revocable

## 6. Review Artifact Model

```
.pcae/backend-reviews/
  latest.json
  YYYYMMDD-HHMMSS-<request-id>-review.json
  YYYYMMDD-HHMMSS-<request-id>-approval.json
  YYYYMMDD-HHMMSS-<request-id>-apply-plan.json
```

## 7. Proposed Change Extraction

Future work. PCAE may extract candidate changes from backend output as:
- Plain text proposal (operator interprets)
- Diff block (unified diff)
- File operation list (`file: operation: content`)
- Structured JSON patch
- Manual operator mapping

Extraction must be validated before any apply. No automatic parsing of arbitrary output into patches.

## 8. Apply Plan Model

| Field | Description |
|-------|------------|
| `apply_plan_id` | Unique identifier |
| `request_id` | Backend invocation request |
| `output_hash` | Hash of output being applied |
| `proposed_files` | Files to modify |
| `allowed_files` | From task scope |
| `forbidden_files` | Must not overlap proposed |
| `operations` | File-level operations |
| `risk_level` | low/medium/high/critical |
| `hard_blocks` | Any hard blocks detected |
| `approval_id` | Human approval reference |
| `rollback_plan_id` | Rollback plan reference |
| `tests_to_run` | Required test suite |
| `check_required` | Governance checks needed |
| `apply_ready` | All gates passed |

## 9. Relationship to Existing Governance

| System | Role in Review/Apply |
|--------|---------------------|
| Controlled file modification | Apply must respect task scope |
| Change review artifacts | Review state recorded as artifact |
| Approval gate | Human approval required |
| Controlled commit/push | Apply does NOT commit or push |
| Rollback governance | Rollback plan required before apply |
| Permission broker | Hard blocks prevent apply |
| Shell gate | Apply operations mediated through shell gate |
| Backend trust gate | Trust assessment must be complete |

## 10. Failure/Degraded-Mode

| Failure | Behavior |
|---------|----------|
| Missing output | Apply blocked |
| Tampered hash | Apply blocked, audit alerted |
| Missing audit | Apply blocked, evidence incomplete |
| Already applied | Apply blocked (idempotency guard) |
| No active task | Apply blocked |
| Forbidden file | Apply blocked |
| Missing rollback plan | Apply blocked |
| Missing approval | Apply blocked |
| Tests/check failure | Apply blocked until resolved |
| Partial apply | Rollback triggered |

## 11. Future CLI Design

```
pcae backend review show --latest
pcae backend review create --request <id>
pcae backend review approve --request <id> --output-hash <hash>
pcae backend review reject --request <id>
pcae backend apply plan --request <id>
pcae backend apply execute --plan <id>
```

## 12. Telegram Behavior

- Telegram may summarize review/apply status **outbound only**
- Telegram must NOT approve, reject, or apply
- Telegram must not include raw output unless safe
- Telegram remains outbound-only in Production v1

## 13. Test Strategy (~50 tests)

Review state transitions, approval hash binding, rejection flow, apply readiness with missing evidence, hard block dominance, forbidden files, tampered hash, rollback requirement, no auto-commit/push, Telegram safety.

## 14. Go/No-Go Criteria

- Trust/readiness gate stable
- Audit verification stable
- Output hash verified
- Task scope available
- Rollback model ready
- Human approval artifact design accepted
- No hard blocks
- All negative tests planned

## 15. Open Questions

| Q | Current Thinking |
|---|-----------------|
| v1: manual apply plans only? | Yes — operator maps output to files manually |
| Delay apply execute? | Yes — after rollback hardening |
| Structured output format first? | Not required for v1; plain text + operator mapping |
| Diff parsing strictness? | Conservative: only unified diff or explicit file:operation format |
| CLI-only or artifact-based approval? | Artifact-based; CLI is the interface |
| Local-only before Telegram? | Yes — review/apply is local-only until proven safe |

---

*Phase 94I is design-only. No review/apply implementation, patch parsing, file mutation, backend invocation, subprocess, network, shell interception, wrappers, enforcement, autonomous mutation, or command execution was designed or implemented.*
