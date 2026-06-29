# Phase 94R — Backend Real Adapter Design

```
phase_name    = phase_94r_backend_real_adapter_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 94S — Real Backend Adapter Contract Model
```

## 1. Purpose and Scope

### 1.1 Purpose

Design the real backend adapter architecture for PCAE. This phase defines how future real adapters for Claude, Claude-DeepSeek, Codex, Qwen, and other backends must integrate with PCAE governance — artifact capture, audit, trust/readiness, review/apply governance, and Telegram reporting — without implementing any adapter execution.

### 1.2 Why Real Adapter Design Is Needed

The mock backend lifecycle (94Q) exercises the full governance chain with deterministic in-process output. Real backends introduce fundamentally different risks:
- **Subprocess execution**: CLI backends (`claude`, `codex`) require spawning child processes
- **Network calls**: API backends require outbound HTTPS with credentials in headers
- **Secret exposure**: Real credentials (API keys, tokens) must transit through the invocation path without leaking into artifacts, logs, or process tables
- **Timeout and failure**: Real backends can hang, crash, return partial output, or exceed rate limits
- **Output unpredictability**: Real output may contain malicious content, secrets echoed by the backend, or structured data requiring parsing

PCAE must keep every adapter behind the same governance boundaries that the mock lifecycle respects. The adapter design must define the contract before any execution path is built.

### 1.3 Key Distinctions

| Concept | Mock Backend (94F/94Q) | Real Adapter (94R design) |
|---------|------------------------|---------------------------|
| Output generation | In-process deterministic text | External subprocess/API/network call |
| Execution risk | Zero — pure computation | Subprocess, network, credential, timeout, parsing |
| Governance gates | Exercised as simulation | Must be enforced before and after invocation |
| Secret handling | None needed | Env presence check, value never stored |
| Failure modes | Never fails | Timeout, crash, auth error, rate limit, partial output |
| Authorization | Preflight only | Explicit human approval per invocation |

## 2. Non-Goals

Design-only. The following are explicitly not implemented:

- Real adapter implementation (no Claude/DeepSeek/Codex/Qwen execution)
- Backend invocation (no subprocess, no CLI call, no API call, no SDK call, no MCP session)
- Subprocess execution, network calls, shell wrappers, shell interception
- Command mediation, Telegram inbound control, remote shell, /run
- Enforcement implementation, autonomous mutation, automatic apply
- Apply execution, patch parsing for mutation, source file mutation
- Automatic tests, automatic `pcae check`, commit/push authorization
- Real AI backend calls of any kind

## 3. Adapter Abstraction

### 3.1 BackendAdapter Contract

Design a Python Protocol that every real adapter must satisfy. The adapter sits between PCAE governance and the real backend execution mechanism:

```python
class BackendAdapter(Protocol):
    """Contract for every real backend adapter.

    Governance (readiness, capture, audit, review, approval) is the
    CALLER's responsibility — not the adapter's.  The adapter handles
    the execution bridge only.
    """

    backend_type: str          # cli | api | sdk | mcp
    display_name: str
    invocation_mode: str       # artifact_only | interactive | batch
    supports_artifact_only: bool
    supports_streaming: bool
    supports_timeout: bool
    supports_session_reuse: bool
    requires_secrets: bool
    required_env_keys: list[str]
    safety_capabilities: dict[str, bool]

    def preflight(
        self,
        definition: BackendDefinition,
    ) -> dict[str, Any]: ...

    def build_invocation_plan(
        self,
        request: InvocationRequest,
        definition: BackendDefinition,
        prompt_text: str,
    ) -> dict[str, Any]: ...

    def invoke_artifact_only(
        self,
        request: InvocationRequest,
        definition: BackendDefinition,
        prompt_text: str,
    ) -> dict[str, Any]: ...

    def capture_output(
        self,
        raw_output: str,
        request: InvocationRequest,
    ) -> dict[str, Any]: ...

    def classify_failure(
        self,
        result: dict[str, Any],
    ) -> str: ...

    def redact_runtime_metadata(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any]: ...
```

### 3.2 Contract Field Semantics

| Field / Method | Purpose | Safety Constraint |
|---------------|---------|-------------------|
| `backend_type` | Discriminates dispatch (cli/api/sdk/mcp) | Must match BackendDefinition.backend_type |
| `required_env_keys` | List of env var names needed | Values never stored; presence/absence only |
| `preflight()` | Validate env, check backend availability, detect bypass-permissions | Must fail-closed; never prints secrets |
| `build_invocation_plan()` | Construct the concrete invocation command/request | Must not include raw secrets in returned metadata |
| `invoke_artifact_only()` | Execute the backend call | Mandatory timeout; must not mutate source files; must not commit/push |
| `capture_output()` | Redact and structure raw output | Applies redaction before storage; quarantined by default |
| `classify_failure()` | Map failure to standard taxonomy | Distinguishes timeout, auth_error, rate_limit, partial, malformed |
| `redact_runtime_metadata()` | Strip secrets from timing/command/exit metadata | Must run before any metadata is persisted |

### 3.3 Adapter Registry Design

Extend `BackendDefinition` with an `adapter_module` field to bind backend IDs to adapter implementations:

| Field | Type | Description |
|-------|------|-------------|
| `adapter_module` | str | Python module path for the adapter (e.g., `pcae.adapters.claude`) |

Future `get_default_registry()` returns `BackendDefinition` objects with `adapter_module` populated. The adapter is loaded only at invocation time, never at import. Unknown or missing adapter modules fail-closed.

## 4. Backend-Specific Adapter Notes

### 4.1 Mock Backend

- Already implemented (94F). Remains the reference for governance chain integration.
- No subprocess, no network, deterministic output.
- Serves as the testDouble for all adapter contract tests.

### 4.2 Claude CLI

| Concern | Design |
|---------|--------|
| Bypass-permissions detection | Adapter preflight must check Claude is NOT in bypass-permissions mode (Shift+Tab state). If bypass is on, invocation is blocked with a clear message. |
| Session isolation | Adapter must not reuse a running Claude session. Each invocation is stateless/single-shot (v1). |
| Prompt input strategy | Prompt delivered via stdin or temp file, never as CLI argument (prevents process-table leakage). |
| Output capture strategy | Full stdout captured. Stderr separated for diagnostics. SHA-256 hashed. |
| Timeout handling | Configurable timeout enforced by adapter wrapper. Partial output preserved on timeout. |
| Environment/secrets | `ANTHROPIC_API_KEY` presence checked; value never stored. |
| Terminal restart behavior | Adapter does not depend on terminal state beyond env vars. |
| No auto-apply | Output captured and quarantined. Never auto-applied. |

### 4.3 Claude-DeepSeek CLI

- Same design as Claude CLI with `backend_id = "claude-deepseek"`.
- Environment: `DEEPSEEK_API_KEY` (or equivalent).
- Otherwise identical governance boundaries.

### 4.4 Codex

- CLI-based adapter (`codex exec`). Same governance as Claude CLI.
- Environment: OpenAI-compatible key.
- Output may be structured (JSON). Adapter must capture raw text; parsing is downstream.

### 4.5 Qwen

- CLI or API adapter. Same governance boundaries.
- Environment: Qwen-specific credentials.

### 4.6 Future Custom Backends

- Must implement the `BackendAdapter` Protocol.
- Must be registered in the adapter registry with `adapter_module`.
- Must pass the same governance preflight (env, bypass, health, broker, shell-gate).
- Must never bypass hard blocks, human review, or output quarantine.

## 5. Invocation Lifecycle for Real Adapters

Future real invocation lifecycle (design only):

```
 1. Request creation          — make_invocation_request()
 2. Prompt artifact capture   — capture_backend_prompt_artifact()
 3. Adapter preflight          — adapter.preflight() — env check, bypass detection
 4. Permission broker eval     — evaluate_permission_broker() — hard blocks, human review
 5. Shell gate preflight       — check_shell_gate() — command classification
 6. Human approval (if req)    — ApprovalArtifact, hash-bound, expiring
 7. Artifact-only invocation   — adapter.invoke_artifact_only() — THE REAL CALL
 8. Output capture             — capture_backend_output_artifact() — redact, hash, quarantine
 9. Audit record               — persist_backend_audit() — tamper-evident digest
10. Trust/readiness assessment — assess_backend_invocation_trust()
11. Review state               — ReviewArtifact
12. Approval/Rejection         — approve_review() / reject_review()
13. Apply plan                 — create_apply_plan()
14. Apply readiness            — validate_backend_apply_readiness()
15. Manual apply package       — create_backend_manual_apply_package()
16. Commit/Push                — SEPARATE governed steps, never automatic
```

Steps 1-9 are the invocation phase. Steps 10-16 are the post-invocation governance phase — they already exist and remain unchanged.

## 6. Permission Broker Integration

### 6.1 Classification

| Invocation Type | Broker Decision | Overridable? |
|----------------|-----------------|--------------|
| Mock invocation | `allow_preflight_only` | N/A — mock only |
| Dry-run preflight | `allow_preflight_only` | N/A — no execution |
| Real artifact-only | `requires_human_review` | Yes — by human approval |
| Real interactive | `requires_human_review` + additional gates | Yes — by human approval |
| Real batch | `requires_human_review` + additional gates | Yes — by human approval |
| Unknown backend | `deny` (hard block) | **No** |
| Bypass-permissions on | `deny` (hard block) | **No** |
| Missing secrets | `deny` (hard block) | **No** |

### 6.2 Hard-Block Invariants (Non-Overridable)

All existing hard blocks remain. Additionally for real adapters:
- `bypass_permissions_active` → hard block
- `unknown_backend` → hard block
- `unsupported_invocation_mode` → hard block
- `missing_required_env` → hard block
- `prompt_artifact_missing` → hard block
- `shell_gate_deny` → hard block

Human approval cannot override hard blocks. Accepted risk cannot override hard blocks.

## 7. Shell Gate Integration

### 7.1 Command Classification

Real adapter invocation commands are classified as `backend_invocation` (existing category). The shell gate:
- Detects backend programs (`claude`, `claude-deepseek`, `codex`, `openai`, `qwen`, etc.)
- Classifies at severity level 2
- Maps to broker `action_type=backend_invocation`
- Requires human review (not hard-blocked, but gated)

### 7.2 Subprocess Boundaries

Future real adapters may require subprocess execution ONLY through a governed path:
- Shell gate must classify the command before execution
- Permission broker must evaluate before execution
- No direct `subprocess.run()` from adapter internals without governance wrapping
- Command hash logged; command text redacted in audit
- Unsupported invocation modes blocked

## 8. Artifact Model

### 8.1 Future Artifact Paths

```
.pcae/backend-invocations/
  <ts>-<request_id>-prompt.md           # Prompt artifact (existing)
  <ts>-<request_id>-output.md           # Output artifact (existing)
  <ts>-<request_id>.json                # Combined metadata (existing)
  <ts>-<request_id>-preflight.json      # Adapter preflight result (new)
  <ts>-<request_id>-runtime.json        # Adapter runtime metadata (new)
  <ts>-<request_id>-stderr.txt          # Stderr capture if separate (new)
  audit/<ts>-<audit_id>.json            # Audit artifact (existing)
```

### 8.2 Runtime Metadata Fields (Design)

| Field | Type | Description |
|-------|------|-------------|
| `invocation_id` | str | Maps to request_id |
| `backend_id` | str | Which backend was invoked |
| `adapter_module` | str | Adapter used |
| `duration_seconds` | float | Wall-clock duration |
| `exit_code` | int | Subprocess exit code (CLI) or HTTP status (API) |
| `timeout_occurred` | bool | Whether timeout fired |
| `output_truncated` | bool | Whether output exceeded max size |
| `output_size_bytes` | int | Raw output size |
| `invocation_mode` | str | artifact_only / interactive / batch |
| `no_real_backend_invoked` | bool | Always False for real adapters |
| `secrets_accessed` | list[str] | Env var names checked (never values) |

Raw secrets must never appear in runtime metadata. The `redact_runtime_metadata()` method must run before persistence.

## 9. Secret and Environment Model

### 9.1 Principles

- Required env keys are checked for presence; values are never printed, logged, or stored.
- Token/API key/chat ID values are redacted from all artifacts.
- Adapter runtime metadata must not leak secrets.
- Terminal restart must reload runtime env where required.
- Prompt text must not be passed as CLI argument (process-table leak). Use stdin or temp file.

### 9.2 Redaction Gaps to Close (Future Implementation)

| Gap | Current State | Required |
|-----|--------------|----------|
| `PCAE_TELEGRAM_BOT_TOKEN` in backend redaction | Missing from `_SECRET_ENV_VAR_NAMES` in backend_invocations.py | Add to redaction set |
| Subprocess environment inheritance | Not controlled | Explicit allowlist from `environment_requirements` |
| Error body logging in API calls | Telegram sink logs raw error bodies | Strip credentials from error payloads |
| Adapter runtime metadata | Not designed | `redact_runtime_metadata()` before persistence |

## 10. Timeout and Failure Model

### 10.1 Timeout

- Every real adapter invocation must have a configurable hard timeout.
- Default: 120 seconds (matching EGA timeout). Overridable per backend.
- No indefinite execution. Timeout is a hard boundary.
- On timeout: partial output captured, status marked `timed_out`, no automatic retry.

### 10.2 Failure Taxonomy

| Failure | Behavior |
|---------|----------|
| Timeout | Partial output preserved; status `timed_out` |
| Non-zero exit | Full output captured; status `failed` |
| Partial output | Quarantined with `partial` marker; human review required |
| Missing output | Invocation result `incomplete`; blocked from apply |
| Malformed output | Quarantined with warning; adoption blocked |
| Backend unavailable | Preflight blocks invocation; clear error |
| Auth failure | Preflight detects missing/expired credentials; blocked |
| Rate limit | Invocation blocked; operator notified |
| Unknown failure | Fail-closed; all output quarantined |

### 10.3 Safe Degradation

Backend invocation failure is non-fatal to PCAE. The repository is never left in an inconsistent state. Output is quarantined until explicitly adopted.

## 11. Streaming and Output Model

### 11.1 Streaming (Future, v2+)

- Streaming is deferred to future phases. Production v1 is single-shot artifact-only.
- If streaming is added: final output must be fully captured before governance processing.
- Partial/interrupted streams marked `partial`; human review required.

### 11.2 Output Capture

- Maximum output size enforced (default: 64KB, matching EGA limit). Truncation recorded.
- Raw output quarantined by default.
- No automatic interpretation as patch, diff, or file operation.
- No automatic apply of any kind.

## 12. Human Approval Model

### 12.1 Requirements

- Real backend invocation requires explicit human approval before execution.
- Approval binds to: `backend_id`, `request_id`, `prompt_hash`, `risk_level`, `invocation_mode`.
- Approval recorded as `ApprovalArtifact` with hash binding.
- Approval expires (default: 1 hour for mutations).
- Approval is auditable and revocable.

### 12.2 What Approval Does NOT Authorize

- Approval does NOT authorize apply execution.
- Approval does NOT authorize commit or push.
- Approval does NOT override hard blocks.
- Approval does NOT bypass the permission broker or shell gate.
- Approval does NOT authorize autonomous or batch invocation without per-invocation review.

## 13. Telegram Behavior

### 13.1 Outbound Only

- Telegram reports adapter preflight/invocation status outbound only.
- No Telegram approval in Production v1.
- No Telegram command control of any kind.

### 13.2 Content Safety

- Summarize invocation status (backend, duration, status) — never raw output.
- Never include bot token, chat ID, API keys, or backend credentials.
- Never include raw prompt or full output text unless explicitly safe and operator-bounded.

## 14. Security and No-Go Conditions

### 14.1 No-Go Conditions for Real Invocation

Real backend invocation must be blocked when ANY of these are true:

| Condition | Block Type |
|-----------|-----------|
| Bypass permissions active | Hard block |
| Missing human approval | Hard block |
| Unknown backend | Hard block |
| Missing prompt artifact | Hard block |
| Unverified prompt hash | Hard block |
| Missing audit path | Hard block |
| Shell gate deny | Hard block |
| Broker hard block | Hard block |
| Required env missing | Hard block |
| Unsafe invocation mode | Hard block |
| Output capture unavailable | Hard block |
| Task scope unavailable | Hard block |
| `no_execution_by_default=False` | Hard block |
| Health unhealthy | Block (warning) |
| Check failed | Block (warning) |

### 14.2 Invariants Preserved

All existing safety invariants remain:
- Hard blocks non-overridable (88V §16)
- Fail-closed on uncertainty
- Human authority absolute
- Output never auto-applied
- No autonomous commit/push
- Evidence before action

## 15. Test Strategy for Future Implementation

### 15.1 Planned Test Categories (~100 tests)

| # | Category | Tests |
|---|----------|-------|
| 1 | Adapter contract | Serialization round-trip, required fields, Protocol compliance |
| 2 | Preflight | Success, missing env, unknown backend, bypass-permissions detected |
| 3 | Env redaction | Missing env reported without values, secrets never in output |
| 4 | Invocation blocking | Unknown backend blocked, hard block honored, shell gate deny honored |
| 5 | Timeout | Timeout produces partial output, no retry, status timed_out |
| 6 | Partial output | Capture on crash/timeout, quarantine preserved |
| 7 | Secret safety | No secrets in artifacts, runtime metadata redacted |
| 8 | No auto-apply | Output captured, not applied; apply_ready requires separate step |
| 9 | No commit/push | Adapter output never committed or pushed |
| 10 | Telegram safety | Outbound-only summary, no raw output, no secrets |
| 11 | Real adapter disabled | Real adapter invocation blocked by default |
| 12 | Multi-backend | Each backend type tested with mock adapter |
| 13 | Failure taxonomy | Each failure mode produces correct classification |

## 16. Go/No-Go Criteria Before Implementation

Implementation of real adapter execution (94S+) must not start until:

| # | Criterion |
|---|-----------|
| G1 | 94R design reviewed and accepted |
| G2 | Adapter contract (Protocol) agreed and documented |
| G3 | Shell gate boundary for real adapter subprocess agreed |
| G4 | Permission broker classification for real invocation agreed |
| G5 | Secret handling and redaction gaps closed (see §9.2) |
| G6 | Timeout and output capture model agreed |
| G7 | Failure taxonomy accepted |
| G8 | No-go condition list (§14.1) accepted |
| G9 | Test strategy (§15) reviewed and tests planned |
| G10 | All existing tests pass (backend 538, broker 265, shell-gate 142, reports 162, fast-green ~3860) |
| G11 | Active task contract for 94S |
| G12 | Operator explicitly authorizes real adapter implementation |
| G13 | No enforcement, interception, or autonomous execution path exists |
| G14 | Bypass-permissions detection mechanism tested and verified |

## 17. Open Questions

| # | Question | Current Thinking |
|---|----------|-----------------|
| 1 | First real adapter? | Claude CLI (most mature tooling, best understood failure modes) |
| 2 | API vs CLI first? | CLI first (simpler subprocess model, leverages existing shell-gate detection) |
| 3 | Streaming in v1? | No — single-shot artifact-only only. Streaming deferred to v2+. |
| 4 | Session reuse? | No — each invocation is stateless in v1. Session reuse deferred. |
| 5 | Multi-backend parallelism? | Deferred. Single-backend invocation proven first. |
| 6 | Adapter plugin discovery? | Deferred to v2 pluggability track. v1: explicit registry. |
| 7 | Subprocess sandboxing? | Not in v1. Docker forbidden. Workspace isolation via git worktree where applicable. |
| 8 | Approval caching for repeated invocations? | No — per-invocation approval in v1. Caching deferred until trust model matures. |

## 18. Recommended Next Phase

**94S — Real Backend Adapter Contract Model**

Implement the `BackendAdapter` Protocol as a concrete Python Protocol class with serialization, validation, and registry integration. Purely structural — no execution. Tests verify the contract shape, not invocation behavior.

---
*Phase 94R is a design-only phase. No real backend invocation, adapter implementation, subprocess execution, network calls, shell wrappers, shell interception, command mediation, Telegram inbound control, remote shell, /run, enforcement, autonomous mutation, automatic apply, apply execution, patch parsing for mutation, source file mutation, automatic tests, automatic pcae check, commit/push authorization, or real AI backend calls were designed or implemented. The design defines what future implementation will build under governance.*
