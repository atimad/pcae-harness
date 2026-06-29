# Phase 94A — Governed Backend Invocation Design

```
phase_name    = phase_94a_governed_backend_invocation_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 94B — Governed Backend Invocation Prototype
```

## 1. Purpose and Scope

### 1.1 Purpose

Design how PCAE should eventually invoke AI backends (Claude, Claude-DeepSeek, Codex, Qwen, etc.) under governance. This defines the abstraction, lifecycle, safety boundaries, and integration points — without implementing execution.

### 1.2 Why Governed Backend Invocation Is Needed

- **Runtime permission ≠ PCAE governance**: Claude's permission prompts control tool access; PCAE governs which tasks, files, and actions are authorized
- **Evidence before invocation**: Every backend call must be traceable to a task contract, broker decision, and audit record
- **Output quarantine**: Backend outputs must be captured, reviewed, and explicitly adopted before affecting the repository
- **One governance surface**: The same permission broker, shell gate, and hard-block registry that govern shell commands must govern backend invocations

### 1.3 Key Distinctions

| Concept | Shell Gate | Backend Invocation |
|---------|-----------|-------------------|
| What is mediated | Raw shell commands | AI backend API/CLI calls |
| Classification | Command text parsing | Backend type + prompt analysis |
| Safety concern | Destructive fs, force push | Autonomous repo mutation, prompt injection |
| Output | Simulation decision | Captured artifact (quarantined) |
| Human review | For high-risk commands | For all mutations, always |

## 2. Non-Goals

94A is design-only. The following are explicitly not designed or implemented:

- Backend invocation implementation (no Claude/DeepSeek/Codex/Qwen execution)
- Shell wrappers, shell interception, or command execution through PCAE
- Telegram inbound control, remote shell, /run
- Enforcement implementation
- Autonomous repo mutation
- Multi-agent orchestration
- Prompt sending, output capture, or intake/adoption

## 3. Backend Abstraction Model

Each supported backend is described by a registry entry:

| Field | Type | Description |
|-------|------|-------------|
| `backend_id` | str | Unique identifier (`claude`, `claude-deepseek`, `codex`, `qwen`) |
| `backend_type` | str | `cli`, `api`, `sdk`, `mcp` |
| `display_name` | str | Human-readable name |
| `command_or_adapter` | str | CLI binary name or adapter module |
| `invocation_mode` | str | `artifact_only`, `interactive`, `batch` |
| `allowed_task_types` | list[str] | `planning`, `implementation`, `review`, `documentation` |
| `risk_level` | str | `low`, `medium`, `high`, `critical` |
| `requires_human_approval` | bool | Always true for mutating actions |
| `supports_prompt_capture` | bool | Whether prompts can be saved as artifacts |
| `supports_output_capture` | bool | Whether outputs can be captured |
| `supports_dry_run` | bool | Whether the backend supports simulation |
| `supports_artifact_only_mode` | bool | Whether output-only mode is available |
| `environment_requirements` | list[str] | Required env vars (e.g., `ANTHROPIC_API_KEY`) |
| `secret_requirements` | list[str] | Secret names needed (values never stored) |
| `schema_version` | str | `"1.0"` |

## 4. Invocation Request Model

Each governed backend invocation is described by a request:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | str | Unique `be-<uuid12>` |
| `phase_id` | str | Active phase ID |
| `task_id` | str | Active task contract ID |
| `backend_id` | str | Which backend to use |
| `prompt_hash` | str | SHA-256 of the prompt text |
| `prompt_artifact_path` | str | Path to persisted prompt artifact |
| `allowed_files` | list[str] | Files the backend may read/write |
| `forbidden_files` | list[str] | Files the backend must not touch |
| `expected_outputs` | list[str] | Expected output types (`markdown`, `code`, `diff`) |
| `execution_mode` | str | `dry_run`, `artifact_only`, `interactive` |
| `approval_state` | str | `pending`, `approved`, `denied`, `expired` |
| `broker_decision` | str | Broker decision (allow/deny/human_review/more_evidence) |
| `shell_gate_preflight` | dict | Shell gate classification of the invocation command |
| `audit_context` | dict | Audit evidence for this request |
| `no_execution_by_default` | bool | Always true until explicitly authorized |
| `schema_version` | str | `"1.0"` |

## 5. Invocation Lifecycle

```
1. Prepare prompt artifact        → .pcae/backend-invocations/<id>-prompt.md
2. Validate task contract          → scope, allowed files, task state
3. Broker preflight                → evaluate_permission_broker()
4. Shell-gate classification       → pcae shell-gate check equivalent
5. Human review (if needed)         → approval record, audit event
6. Backend invocation (if authorized) → CLI/API call
7. Capture output                  → .pcae/backend-invocations/<id>-output.md
8. Produce output artifact         → structured output + audit
9. Review/apply separately         → human reviews output before adoption
10. Audit and report               → phase report includes invocation summary
11. No direct commit/push          → backend output is never auto-committed
```

**Key invariant**: Backend output is **never** automatically committed, pushed, or applied. Every output must pass through human review before affecting the repository.

## 6. Relationship to Permission Broker

- Every backend invocation must pass through `evaluate_permission_broker()`
- The broker evaluates: task contract scope, backend risk level, approval state, enforcement readiness
- Hard blocks (88V §16) are non-overridable by any actor
- Human approval cannot override hard blocks
- Accepted risk cannot override hard blocks
- Unknown backend or unknown invocation mode → `deny` (fail-closed)

## 7. Relationship to Shell Gate

- Backend invocation commands (e.g., `claude "write code"`) are already classified as `backend_invocation` by the shell gate
- The broker maps `backend_invocation` → `requires_human_review` (not hard block, but gated)
- Future: raw backend shell invocation should be mediated through `pcae shell-gate check`
- No shell gate enforcement is implemented in 94A

## 8. Relationship to Phase Reports and Telegram

- Phase reports may summarize: "3 backend invocations this phase, 2 approved, 1 denied"
- Telegram may include compact invocation status: "Backend: Claude-DeepSeek, 2 invocations"
- Telegram must NOT send prompts, secrets, raw outputs, or unredacted backend responses
- Full invocation artifacts are local in `.pcae/backend-invocations/`
- Telegram remains outbound-only

## 9. Prompt and Output Artifact Model

### 9.1 Directory Layout

```
.pcae/backend-invocations/
  latest.json
  latest-prompt.md
  latest-output.md
  YYYYMMDD-HHMMSS-<request-id>.json
  YYYYMMDD-HHMMSS-<request-id>-prompt.md
  YYYYMMDD-HHMMSS-<request-id>-output.md
```

### 9.2 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Format | Individual JSON + Markdown files | Matches `.pcae/phase-reports/` and `.pcae/shell-gate-audit/` pattern |
| Prompt storage | Separate `.md` file | Human-readable, diffable |
| Output storage | Separate `.md` file | Quarantined until reviewed |
| Latest pointer | `latest.json` + `latest-prompt.md` + `latest-output.md` | Fast lookup |
| Schema versioning | `schema_version` in each record | Forward compatibility |

## 10. Secret and Environment Handling

- Secrets **never committed** to the repository
- Secrets loaded from **local environment only** (env vars, `.env` files, OS keychain)
- Backend env status reports `present`/`missing` only — never the value
- No token, API key, or chat ID leakage in artifacts, reports, or Telegram
- Canonical final reports reference backend usage but never include credentials
- Existing secret redaction patterns (93C) extend to prompt/output capture

## 11. Risk Model

| Risk Level | Description | Examples | Max Autonomy |
|------------|-------------|----------|-------------|
| `low` | Read-only planning, documentation | "Summarize this file" | Artifact-only dry-run |
| `medium` | Code proposal, test generation | "Write a test for X" | Artifact-only, human reviews output |
| `high` | Code mutation, apply-to-repo | "Implement feature Y" | Requires human approval per invocation |
| `critical` | Commit, push, backend invocation of another backend | "Commit and push changes" | **Never autonomous** — hard block |

## 12. Future CLI Design

Design possible future commands (do not implement):

```
pcae backend status [--json]
pcae backend list [--json]
pcae backend plan --backend <id> --task <task-id> [--dry-run]
pcae backend invoke --request <id> [--dry-run] [--artifact-only]
pcae backend show --latest [--json]
pcae backend review --request <id>
pcae backend apply --request <id> --files <paths>
pcae backend deny --request <id> --reason "..."
```

## 13. Failure and Degraded-Mode Behavior

| Failure | Behavior |
|---------|----------|
| Missing backend config | Invocation refused; error reported |
| Missing secrets | Invocation refused; "missing: ANTHROPIC_API_KEY" (no value) |
| Unknown backend | `deny` — fail-closed |
| Broker denial | Invocation blocked; reason reported |
| Shell-gate denial | Invocation blocked; reason reported |
| Backend timeout | Output capture partial; timeout recorded in audit |
| Output capture failure | Invocation result marked incomplete; human review required |
| Partial output | Quarantined; marked partial; human review required |
| Unsafe output detected | Quarantined with warning; adoption blocked |
| No active task | Invocation refused for mutating actions |

**Key invariant**: Backend invocation failure is non-fatal to PCAE. The repository is never left in an inconsistent state. Backend output is quarantined until explicitly adopted.

## 14. Test Strategy for Future Implementation

| # | Category | Planned Tests |
|---|----------|--------------|
| 1 | Backend registry | Valid backends load, unknown backends fail |
| 2 | Request model | Valid/invalid requests, required fields |
| 3 | Prompt artifact capture | Prompt written, redacted, hashed |
| 4 | Output artifact capture | Output written, quarantined |
| 5 | Broker denial | Backend invocation blocked by broker |
| 6 | Shell-gate denial | Backend invocation blocked by shell gate |
| 7 | Secret redaction | No tokens in artifacts or audit |
| 8 | No direct repo mutation | Backend output never auto-committed |
| 9 | No commit/push | Backend cannot commit or push |
| 10 | Telegram summary safety | No secrets in Telegram text |
| 11 | Failure handling | Each failure mode produces safe result |
| 12 | Human approval | Required for mutating actions |
| 13 | Hard-block invariant | Non-overridable for critical risk |
| 14 | Artifact-only mode | Dry-run produces artifacts only |
| 15 | CLI commands | Each future command has basic tests |

**Estimated new tests: ~60**

## 15. Go/No-Go Criteria

| # | Criterion |
|---|-----------|
| G1 | 94A design reviewed and approved |
| G2 | Permission broker (91A–91C) stable and tested |
| G3 | Shell gate (93B–93F) stable and tested |
| G4 | All existing tests pass (broker 265, shell gate 142) |
| G5 | Fast-green baseline clean |
| G6 | Active task contract for 94B |
| G7 | Operator explicitly authorizes implementation |
| G8 | No enforcement, interception, or autonomous execution path exists |
| G9 | Backend registry populated with at least one mock backend |
| G10 | Prompt/output artifact paths added to `.pcae/.gitignore` |

## 16. Open Questions

| # | Question | Current Thinking |
|---|----------|-----------------|
| 1 | First backend? | Mock backend for testing; Claude CLI as first real backend |
| 2 | v1 mode? | Artifact-only mode only — no direct repo mutation |
| 3 | Approval every time? | Yes for mutating actions; read-only planning may be pre-approved per task |
| 4 | Long-running sessions? | v1 supports single-shot invocation only; sessions deferred |
| 5 | Multi-agent orchestration? | Deferred to future phase after single-backend governance is proven |

---

*Phase 94A is a design-only phase. No backend invocation, shell interception, wrappers, command mediation, Telegram inbound control, remote shell, /run, enforcement, autonomous mutation, or command execution path was designed or implemented. The design defines what future implementation will build.*
