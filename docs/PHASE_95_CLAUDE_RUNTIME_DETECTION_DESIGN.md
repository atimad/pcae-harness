# Phase 95B — Claude/Claude-DeepSeek Runtime Detection Design

```
phase_name    = phase_95b_claude_runtime_detection_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 95C — Claude Runtime Evidence Model
```

## 1. Purpose

Design the runtime detection boundary for Claude CLI and Claude-DeepSeek CLI. Define how PCAE will detect runtime identity, command path, authentication mode, bypass-permissions state, session safety, and environment evidence before any real invocation is allowed. This phase is design-only — no runtime execution.

### Why Runtime Detection Is Needed

Two read-only subagents confirmed:
- **All bypass detection today is model-only** — accepts `bypass_detected: bool` as input, never computes it
- **No command path resolution exists** — shell gate recognizes `"claude"` as a command string but has no PATH lookup, binary fingerprinting, or identity collapse detection
- **Five bypass-detection readiness gates (B1-B5 from 89J) remain unsatisfied**
- **Claude and Claude-DeepSeek could resolve to the same binary** (symlink/hardlink identity collapse) — no detection exists

## 2. Non-Goals

Design-only. Explicitly NOT implemented:
- Real backend invocation, adapter execution, subprocess execution
- Shell command execution, network calls, shell wrappers
- Live Claude/Claude-DeepSeek process inspection
- `which`, `claude --version`, or any subprocess call
- Secret value reading, auth inference by API call
- Enforcement, autonomous mutation, automatic apply
- Commit/push authorization

## 3. Detection Scope

### 3.1 Runtime Detection Profiles

| Profile | backend_id | backend_type | Command Names | Required Env | Bypass Detection |
|---------|-----------|-------------|---------------|-------------|-----------------|
| Claude | claude | claude_cli | ["claude"] | ANTHROPIC_API_KEY | Required |
| Claude-DeepSeek | claude-deepseek | claude_deepseek_cli | ["claude-deepseek"] | DEEPSEEK_API_KEY | Required |
| Custom | (configured) | custom | (configured) | (configured) | Required |

### 3.2 Evidence Sources (Stat-Only, No Execution)

| Source | Method | Risk |
|--------|--------|------|
| Binary path resolution | `shutil.which()` — pure Python PATH lookup | Zero — no fork/exec |
| Binary fingerprint | `os.stat()` — inode, device, mode | Zero — stat syscall only |
| Shebang detection | `open()` first line — script vs binary | Zero — file read |
| Config file inspection | `open()` ~/.claude.json, ~/.claude/settings.json | Zero — file read |
| Environment scan | `os.environ.get()` — key presence only | Zero — env var read |
| Bypass env detection | Check for known bypass env var names | Zero — env var name check |

None of these sources require executing any backend binary.

## 4. Runtime Evidence Model (Future Data Model Sketch)

```python
@dataclass
class BackendRuntimeIdentity:
    """Stat-only runtime identity evidence. Never executes backends."""
    identity_id: str              # "bri-<uuid12>"
    claimed_backend_id: str       # "claude" or "claude-deepseek"
    adapter_id: str               # matching adapter contract
    binary_path: str | None       # resolved from shutil.which()
    binary_exists: bool           # whether binary was found on PATH
    binary_inode: int | None      # for identity collapse detection
    binary_device: int | None     # for identity collapse detection
    binary_is_script: bool | None # True if starts with #!
    identity_collapsed: bool      # True if claude==claude-deepseek same binary
    collapsed_with: list[str]     # backend_ids sharing the same binary
    env_keys_present_redacted: list[str]  # env key names present (never values)
    env_keys_missing: list[str]   # required env keys not found
    config_model: str | None      # model from config file
    config_endpoint: str | None   # endpoint URL from config file
    bypass_env_detected: list[str]   # bypass-indicating env vars found
    bypass_config_detected: list[str] # bypass-indicating config keys found
    bypass_permissions_active: bool   # aggregate bypass state
    session_isolation_mode: str   # "stateless" (v1 default)
    identity_confidence: str      # "high" | "medium" | "low" | "conflict"
    hard_blocks: list[str]
    warnings: list[str]
    missing_evidence: list[str]
    detected_at_utc: str
    evidence_source: str          # "stat_only" (no execution)
    schema_version: str
    record_digest: str
```

## 5. Bypass-Permissions Boundary

### 5.1 Fail-Closed Rules

| Condition | Decision |
|-----------|----------|
| `bypass_env_detected` non-empty | Hard block |
| `bypass_config_detected` non-empty | Hard block |
| `bypass_permissions_active=True` | Hard block |
| `bypass_permissions_active` unknown | Missing evidence → blocked |
| Bypass evidence source unavailable | Missing evidence → blocked |

### 5.2 Non-Overridability

- Human approval **cannot** override bypass hard block
- Accepted risk **cannot** override bypass hard block
- Telegram **cannot** override bypass hard block
- Broker must treat bypass as hard-blocking for real invocation
- Shell gate must deny if bypass evidence is missing or unsafe
- Four independent enforcement points already exist in the codebase (94W, 94Y, 94Z, 95A)

### 5.3 Known Bypass Indicators (Future Detection)

| Type | Examples |
|------|----------|
| Env vars | `CLAUDE_CODE_SKIP_PERMISSION_CHECKS`, `ANTHROPIC_DISABLE_PERMISSIONS` |
| Config keys | `bypass_permissions: true` in settings.json |
| CLI flags | `--no-check`, `--skip-permissions` |
| Shell state | `set +o` / `shopt` indicating relaxed error handling |

Detection is stat-only — env var name presence, config key presence, no process inspection.

## 6. Command Identity Boundary

### 6.1 What Future Implementation May Inspect Safely

- Configured command path from explicit PCAE config
- Wrapper path and hash from predeclared config/artifact
- Expected backend ID from adapter contract
- Expected invocation mode from adapter contract
- Declared environment key names only (never values)
- Config file model/endpoint fields (never auth tokens)
- Binary existence via `shutil.which()` (no execution)
- Binary fingerprint via `os.stat()` (inode, device only)

### 6.2 What Must Not Be Done

- Execute `claude`, `claude-deepseek`, or any backend binary
- Run `which`, `claude --version`, or any subprocess
- Read secret values from env or config
- Infer auth by attempting an API call
- Inspect live Claude sessions or process state
- Auto-discover arbitrary shell commands

## 7. Shell-Gate and Broker Integration

Runtime detection evidence feeds into the existing governance chain:

```
BackendRuntimeIdentity
  → adapter contract validation (94S/94W)
  → preflight artifact (94U)
  → approval artifact (94Y)
  → invocation plan artifact (94Z)
  → dry-run assessment (95A)
  → permission broker hard-block check
  → shell gate dry-run boundary
  → audit trail
  → output quarantine
```

### 7.1 Broker Integration

- `bypass_permissions_active=True` → hard block `blocked_by_real_invocation_bypass`
- `identity_confidence=conflict` → missing evidence
- `binary_exists=False` → hard block `backend_binary_not_found`
- `identity_collapsed=True` → warning (not hard block — operator must confirm which backend)

### 7.2 Shell-Gate Integration

- Runtime identity evidence feeds shell gate preflight
- Command class: `backend_invocation` (existing)
- Shell gate does NOT execute the backend — only classifies

## 8. Failure Categories

| Category | Trigger |
|----------|---------|
| `runtime_unknown` | No identity evidence available |
| `command_identity_missing` | Binary not found on PATH |
| `command_identity_mismatch` | Binary path doesn't match expected backend |
| `identity_collapsed` | Two backends share same binary |
| `auth_evidence_missing` | Required env keys not present |
| `bypass_state_unknown` | Cannot determine bypass state |
| `bypass_enabled` | Bypass indicators detected |
| `timeout_missing` | Timeout not configured |
| `output_capture_unavailable` | Quarantine path missing |
| `audit_path_missing` | Audit path not configured |
| `quarantine_path_missing` | Output quarantine path missing |
| `shell_gate_missing` | Shell gate evidence absent |
| `broker_denied` | Permission broker hard block |
| `detection_artifact_tampered` | Digest verification failed |
| `unsupported_runtime` | Backend not in recognized list |

## 9. Go/No-Go Criteria for Implementation (95C)

| # | Criterion | Status |
|---|-----------|--------|
| G1 | Config-only evidence model approved | Design complete (this phase) |
| G2 | No live command execution required | Guaranteed — stat-only |
| G3 | Explicit operator configuration available | Deferred to 95C |
| G4 | Redaction tested | Deferred to 95C |
| G5 | Broker hard-blocks defined for bypass | Design complete |
| G6 | Shell-gate dry-run evidence defined | Design complete |
| G7 | Timeout/audit/quarantine fields required | Already in plan model (94Z) |
| G8 | Failure classification tests planned | ~25 tests planned |
| G9 | All existing tests pass | 527 model / 188 CLI |
| G10 | No execution path created | Verified — design-only |

## 10. Recommended Next Phase

**95C — Claude Runtime Evidence Model**

Implement the `BackendRuntimeIdentity` dataclass and `detect_backend_runtime_identity()` function as a pure stat-only model. No subprocess, no network, no execution. Implement the identity detection logic using `shutil.which()` + `os.stat()` + config file reading. Add ~25 tests.

Do NOT implement real backend invocation.

---
*Phase 95B is design-only. No backend invocation, adapter execution, subprocess, network, or shell commands were performed. Two read-only subagents provided architecture and safety review.*
