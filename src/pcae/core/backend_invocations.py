"""Backend registry and invocation request model — Phase 94B.

Data models for governed backend invocation. No backend execution,
no subprocess, no network calls.  Simulation/validation only.
"""

from __future__ import annotations

import json as _json
import os as _os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path as _PathType
from typing import Any

SCHEMA_VERSION = "1.0"

# ── Backend types ─────────────────────────────────────────────────────────

BACKEND_TYPE_CLI = "cli"
BACKEND_TYPE_API = "api"
BACKEND_TYPE_SDK = "sdk"
BACKEND_TYPE_MCP = "mcp"
BACKEND_TYPE_MOCK = "mock"

VALID_BACKEND_TYPES: frozenset[str] = frozenset({
    BACKEND_TYPE_CLI, BACKEND_TYPE_API, BACKEND_TYPE_SDK,
    BACKEND_TYPE_MCP, BACKEND_TYPE_MOCK,
})

# ── Invocation modes ──────────────────────────────────────────────────────

INVOCATION_MODE_ARTIFACT_ONLY = "artifact_only"
INVOCATION_MODE_INTERACTIVE = "interactive"
INVOCATION_MODE_BATCH = "batch"
INVOCATION_MODE_DRY_RUN = "dry_run"

VALID_INVOCATION_MODES: frozenset[str] = frozenset({
    INVOCATION_MODE_ARTIFACT_ONLY, INVOCATION_MODE_INTERACTIVE,
    INVOCATION_MODE_BATCH, INVOCATION_MODE_DRY_RUN,
})

# ── Risk levels ───────────────────────────────────────────────────────────

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

VALID_RISK_LEVELS: frozenset[str] = frozenset({
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
})

# ── Approval states ───────────────────────────────────────────────────────

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_DENIED = "denied"
APPROVAL_EXPIRED = "expired"

VALID_APPROVAL_STATES: frozenset[str] = frozenset({
    APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_DENIED, APPROVAL_EXPIRED,
})

# ── Readiness states ──────────────────────────────────────────────────────

READINESS_READY = "ready"
READINESS_BLOCKED = "blocked"
READINESS_NEEDS_HUMAN_REVIEW = "needs_human_review"
READINESS_MISSING_EVIDENCE = "missing_evidence"

# ── Task types ────────────────────────────────────────────────────────────

TASK_PLANNING = "planning"
TASK_IMPLEMENTATION = "implementation"
TASK_REVIEW = "review"
TASK_DOCUMENTATION = "documentation"


# ═══════════════════════════════════════════════════════════════════════════
# Backend definition
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class BackendDefinition:
    """Metadata describing a configured AI backend.  No execution capability."""

    backend_id: str = ""
    backend_type: str = BACKEND_TYPE_CLI
    display_name: str = ""
    invocation_mode: str = INVOCATION_MODE_ARTIFACT_ONLY
    allowed_task_types: list[str] = field(default_factory=list)
    risk_level: str = RISK_MEDIUM
    requires_human_approval: bool = True
    supports_prompt_capture: bool = True
    supports_output_capture: bool = True
    supports_dry_run: bool = False
    supports_artifact_only_mode: bool = True
    environment_requirements: list[str] = field(default_factory=list)
    secret_requirements: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.backend_id:
            issues.append("backend_id is required")
        if self.backend_type not in VALID_BACKEND_TYPES:
            issues.append(f"invalid backend_type: {self.backend_type!r}")
        if self.invocation_mode not in VALID_INVOCATION_MODES:
            issues.append(f"invalid invocation_mode: {self.invocation_mode!r}")
        if self.risk_level not in VALID_RISK_LEVELS:
            issues.append(f"invalid risk_level: {self.risk_level!r}")
        if self.risk_level == RISK_CRITICAL:
            # Critical risk always requires human approval
            if not self.requires_human_approval:
                issues.append("critical risk must require human approval")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "display_name": self.display_name,
            "invocation_mode": self.invocation_mode,
            "allowed_task_types": self.allowed_task_types,
            "risk_level": self.risk_level,
            "requires_human_approval": self.requires_human_approval,
            "supports_prompt_capture": self.supports_prompt_capture,
            "supports_output_capture": self.supports_output_capture,
            "supports_dry_run": self.supports_dry_run,
            "supports_artifact_only_mode": self.supports_artifact_only_mode,
            "environment_requirements": self.environment_requirements,
            "secret_requirements": self.secret_requirements,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendDefinition":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


# ═══════════════════════════════════════════════════════════════════════════
# Invocation request
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class InvocationRequest:
    """A governed backend invocation request.  No execution — metadata only."""

    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    execution_mode: str = INVOCATION_MODE_DRY_RUN
    approval_state: str = APPROVAL_PENDING
    broker_decision: str = ""
    shell_gate_preflight: dict[str, Any] = field(default_factory=dict)
    audit_context: dict[str, Any] = field(default_factory=dict)
    no_execution_by_default: bool = True
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.request_id:
            issues.append("request_id is required")
        if not self.backend_id:
            issues.append("backend_id is required")
        if self.execution_mode not in VALID_INVOCATION_MODES:
            issues.append(f"invalid execution_mode: {self.execution_mode!r}")
        if self.approval_state not in VALID_APPROVAL_STATES:
            issues.append(f"invalid approval_state: {self.approval_state!r}")
        if not self.no_execution_by_default:
            issues.append("no_execution_by_default must be True")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "allowed_files": self.allowed_files,
            "forbidden_files": self.forbidden_files,
            "expected_outputs": self.expected_outputs,
            "execution_mode": self.execution_mode,
            "approval_state": self.approval_state,
            "broker_decision": self.broker_decision,
            "shell_gate_preflight": self.shell_gate_preflight,
            "audit_context": self.audit_context,
            "no_execution_by_default": self.no_execution_by_default,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InvocationRequest":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


# ═══════════════════════════════════════════════════════════════════════════
# Readiness check
# ═══════════════════════════════════════════════════════════════════════════


def check_invocation_readiness(
    request: InvocationRequest,
    registry: dict[str, BackendDefinition] | None = None,
) -> dict[str, Any]:
    """Check whether an invocation request is ready to proceed.

    Returns readiness result with status, missing evidence, hard blocks, warnings.
    Never executes.  Fail-closed: unknown backend, mode, or risk → blocked.
    """
    if registry is None:
        registry = get_default_registry()

    missing_evidence: list[str] = []
    hard_blocks: list[str] = []
    warnings: list[str] = []

    # 1. Validate request
    req_issues = request.validate()
    if req_issues:
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": req_issues,
            "warnings": [],
        }

    # 2. No execution invariant
    if not request.no_execution_by_default:
        hard_blocks.append("no_execution_by_default must be True")
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": hard_blocks,
            "warnings": [],
        }

    # 3. Backend existence — fail closed
    backend = registry.get(request.backend_id)
    if backend is None:
        hard_blocks.append(f"unknown backend: {request.backend_id!r}")
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": hard_blocks,
            "warnings": [],
        }

    # 4. Unknown risk level — fail closed
    if backend.risk_level not in VALID_RISK_LEVELS:
        hard_blocks.append(f"unknown risk level: {backend.risk_level!r}")
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": hard_blocks,
            "warnings": [],
        }

    # 5. Critical risk — hard block (never autonomous)
    if backend.risk_level == RISK_CRITICAL:
        hard_blocks.append("critical risk backend invocation is permanently blocked")
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": hard_blocks,
            "warnings": [],
        }

    # 6. Missing prompt artifact
    if not request.prompt_artifact_path:
        missing_evidence.append("prompt_artifact_path")

    # 7. Missing allowed/forbidden files
    if not request.allowed_files and not request.forbidden_files:
        warnings.append("no file scope defined (allowed_files/forbidden_files)")

    # 8. Human approval for high-risk backends
    if backend.risk_level == RISK_HIGH and request.approval_state != APPROVAL_APPROVED:
        return {
            "backend_invocation_ready": False,
            "status": READINESS_NEEDS_HUMAN_REVIEW,
            "missing_evidence": missing_evidence,
            "hard_blocks": [],
            "warnings": warnings,
        }

    # 9. Approval denied/expired
    if request.approval_state in (APPROVAL_DENIED, APPROVAL_EXPIRED):
        hard_blocks.append(f"approval state is {request.approval_state!r}")
        return {
            "backend_invocation_ready": False,
            "status": READINESS_BLOCKED,
            "missing_evidence": [],
            "hard_blocks": hard_blocks,
            "warnings": [],
        }

    # 10. Missing evidence
    if missing_evidence:
        return {
            "backend_invocation_ready": False,
            "status": READINESS_MISSING_EVIDENCE,
            "missing_evidence": missing_evidence,
            "hard_blocks": [],
            "warnings": warnings,
        }

    return {
        "backend_invocation_ready": True,
        "status": READINESS_READY,
        "missing_evidence": [],
        "hard_blocks": [],
        "warnings": warnings,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Default registry
# ═══════════════════════════════════════════════════════════════════════════


def get_default_registry() -> dict[str, BackendDefinition]:
    """Return the built-in backend registry.  Metadata only — no execution."""
    return {
        "claude": BackendDefinition(
            backend_id="claude",
            backend_type=BACKEND_TYPE_CLI,
            display_name="Claude (Anthropic)",
            invocation_mode=INVOCATION_MODE_ARTIFACT_ONLY,
            allowed_task_types=[TASK_PLANNING, TASK_IMPLEMENTATION, TASK_REVIEW],
            risk_level=RISK_MEDIUM,
            requires_human_approval=True,
            supports_prompt_capture=True,
            supports_output_capture=True,
            supports_dry_run=False,
            supports_artifact_only_mode=True,
            environment_requirements=["ANTHROPIC_API_KEY"],
            secret_requirements=["ANTHROPIC_API_KEY"],
        ),
        "claude-deepseek": BackendDefinition(
            backend_id="claude-deepseek",
            backend_type=BACKEND_TYPE_CLI,
            display_name="Claude-DeepSeek",
            invocation_mode=INVOCATION_MODE_ARTIFACT_ONLY,
            allowed_task_types=[TASK_PLANNING, TASK_IMPLEMENTATION],
            risk_level=RISK_MEDIUM,
            requires_human_approval=True,
            supports_prompt_capture=True,
            supports_output_capture=True,
            supports_dry_run=False,
            supports_artifact_only_mode=True,
            environment_requirements=["DEEPSEEK_API_KEY"],
            secret_requirements=["DEEPSEEK_API_KEY"],
        ),
        "codex": BackendDefinition(
            backend_id="codex",
            backend_type=BACKEND_TYPE_CLI,
            display_name="OpenAI Codex",
            invocation_mode=INVOCATION_MODE_ARTIFACT_ONLY,
            allowed_task_types=[TASK_IMPLEMENTATION, TASK_REVIEW],
            risk_level=RISK_MEDIUM,
            requires_human_approval=True,
            supports_prompt_capture=True,
            supports_output_capture=True,
            supports_dry_run=False,
            supports_artifact_only_mode=True,
            environment_requirements=["OPENAI_API_KEY"],
            secret_requirements=["OPENAI_API_KEY"],
        ),
        "qwen": BackendDefinition(
            backend_id="qwen",
            backend_type=BACKEND_TYPE_API,
            display_name="Qwen (Alibaba)",
            invocation_mode=INVOCATION_MODE_ARTIFACT_ONLY,
            allowed_task_types=[TASK_PLANNING, TASK_DOCUMENTATION],
            risk_level=RISK_MEDIUM,
            requires_human_approval=True,
            supports_prompt_capture=True,
            supports_output_capture=True,
            supports_dry_run=False,
            supports_artifact_only_mode=True,
            environment_requirements=["QWEN_API_KEY"],
            secret_requirements=["QWEN_API_KEY"],
        ),
        "mock": BackendDefinition(
            backend_id="mock",
            backend_type=BACKEND_TYPE_MOCK,
            display_name="Mock Backend (Testing)",
            invocation_mode=INVOCATION_MODE_DRY_RUN,
            allowed_task_types=[TASK_PLANNING, TASK_IMPLEMENTATION, TASK_REVIEW, TASK_DOCUMENTATION],
            risk_level=RISK_LOW,
            requires_human_approval=False,
            supports_prompt_capture=True,
            supports_output_capture=True,
            supports_dry_run=True,
            supports_artifact_only_mode=True,
            environment_requirements=[],
            secret_requirements=[],
        ),
    }


# ── Make a new request (helper) ───────────────────────────────────────────

def make_invocation_request(
    *,
    backend_id: str,
    phase_id: str = "",
    task_id: str = "",
    prompt_hash: str = "",
    prompt_artifact_path: str = "",
    allowed_files: list[str] | None = None,
    forbidden_files: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    execution_mode: str = INVOCATION_MODE_DRY_RUN,
    approval_state: str = APPROVAL_PENDING,
    **kwargs: Any,
) -> InvocationRequest:
    """Create a validated invocation request. Raises ValueError on invalid."""
    custom_request_id = kwargs.pop("request_id", None)
    req = InvocationRequest(
        request_id=custom_request_id or f"be-{uuid.uuid4().hex[:12]}",
        phase_id=phase_id,
        task_id=task_id,
        backend_id=backend_id,
        prompt_hash=prompt_hash,
        prompt_artifact_path=prompt_artifact_path,
        allowed_files=list(allowed_files or []),
        forbidden_files=list(forbidden_files or []),
        expected_outputs=list(expected_outputs or []),
        execution_mode=execution_mode,
        approval_state=approval_state,
        **kwargs,
    )
    issues = req.validate()
    if issues:
        raise ValueError(f"Invalid invocation request: {'; '.join(issues)}")
    return req


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94C — Prompt artifact capture
# ═══════════════════════════════════════════════════════════════════════════

_BACKEND_INVOCATION_DIR = ".pcae/backend-invocations"

# Re-use existing redaction from shell_gate for prompt text
_SECRET_ENV_VAR_NAMES: frozenset[str] = frozenset({
    "TOKEN", "API_KEY", "SECRET", "PASSWORD", "PASSWD", "PASS",
    "AUTH", "CREDENTIAL", "KEY", "PRIVATE_KEY", "ACCESS_KEY",
    "SECRET_KEY", "BEARER", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY", "QWEN_API_KEY", "GITHUB_TOKEN",
})
_SECRET_FLAG_PATTERNS: tuple[str, ...] = (
    "--token", "--api-key", "--secret", "--password", "--passwd",
    "--access-key", "--secret-key", "--private-key",
)


def _redact_prompt_text(text: str) -> tuple[str, bool]:
    """Redact secrets from prompt text. Returns (redacted, applied)."""
    import re
    redacted = text
    did_redact = False
    for var_name in _SECRET_ENV_VAR_NAMES:
        pattern = re.compile(rf'\b({var_name})=(\S+)', re.IGNORECASE)
        if pattern.search(redacted):
            redacted = pattern.sub(r'\1=[REDACTED]', redacted)
            did_redact = True
    for flag in _SECRET_FLAG_PATTERNS:
        pattern = re.compile(rf'({flag})\s+([^\s-][^\s]*)', re.IGNORECASE)
        if pattern.search(redacted):
            redacted = pattern.sub(r'\1 [REDACTED]', redacted)
            did_redact = True
    bearer = re.compile(r'(Authorization:\s*Bearer\s+)(\S+)', re.IGNORECASE)
    if bearer.search(redacted):
        redacted = bearer.sub(r'\1[REDACTED]', redacted)
        did_redact = True
    return redacted, did_redact


@dataclass
class PromptArtifact:
    """A captured, redacted prompt artifact for backend invocation."""

    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    prompt_preview: str = ""
    prompt_size_bytes: int = 0
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    created_at_utc: str = ""
    redaction_applied: bool = False
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "prompt_preview": self.prompt_preview,
            "prompt_size_bytes": self.prompt_size_bytes,
            "allowed_files": self.allowed_files,
            "forbidden_files": self.forbidden_files,
            "expected_outputs": self.expected_outputs,
            "created_at_utc": self.created_at_utc,
            "redaction_applied": self.redaction_applied,
            "schema_version": self.schema_version,
        }


def _ensure_invocation_dir() -> Path:
    import os
    from pathlib import Path as _Path
    d = _Path(_BACKEND_INVOCATION_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def capture_backend_prompt_artifact(
    request: InvocationRequest,
    prompt_text: str,
    *,
    invocation_dir: str | None = None,
) -> dict[str, Any]:
    """Capture a prompt artifact for a backend invocation request.

    Redacts secrets, computes SHA-256 hash, writes timestamped artifact
    and updates latest-prompt.md + latest.json.

    Never invokes a backend, never runs subprocess, never calls network.
    Returns capture result dict.
    """
    import hashlib
    import json as _json
    import os
    from datetime import datetime, timezone
    from pathlib import Path as _Path

    dir_path = _Path(invocation_dir) if invocation_dir else _ensure_invocation_dir()
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")

    # 1. Redact and hash
    redacted_text, redaction_applied = _redact_prompt_text(prompt_text)
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()
    prompt_size = len(redacted_text.encode())

    # 2. Write timestamped prompt
    prompt_filename = f"{ts}-{request.request_id}-prompt.md"
    prompt_path = dir_path / prompt_filename
    prompt_path.write_text(redacted_text)

    # 3. Build artifact metadata
    artifact = PromptArtifact(
        request_id=request.request_id,
        phase_id=request.phase_id,
        task_id=request.task_id,
        backend_id=request.backend_id,
        prompt_hash=prompt_hash,
        prompt_artifact_path=str(prompt_path),
        prompt_preview=redacted_text[:200] if len(redacted_text) > 200 else redacted_text,
        prompt_size_bytes=prompt_size,
        allowed_files=request.allowed_files,
        forbidden_files=request.forbidden_files,
        expected_outputs=request.expected_outputs,
        created_at_utc=now.isoformat(),
        redaction_applied=redaction_applied,
    )

    # 4. Write timestamped metadata JSON
    meta_filename = f"{ts}-{request.request_id}.json"
    meta_path = dir_path / meta_filename
    meta_path.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))

    # 5. Update latest pointers
    latest_prompt = dir_path / "latest-prompt.md"
    latest_json = dir_path / "latest.json"
    latest_prompt.write_text(redacted_text)

    # Atomically update latest.json
    latest_tmp = dir_path / ".latest.tmp"
    latest_tmp.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))
    os.replace(str(latest_tmp), str(latest_json))

    # Update request with prompt data
    request.prompt_hash = prompt_hash
    request.prompt_artifact_path = str(prompt_path)

    return {
        "status": "captured",
        "request_id": request.request_id,
        "prompt_hash": prompt_hash,
        "prompt_path": str(prompt_path),
        "latest_prompt_path": str(latest_prompt),
        "latest_meta_path": str(latest_json),
        "redaction_applied": redaction_applied,
        "prompt_size_bytes": prompt_size,
        "artifact": artifact,
    }


def read_latest_prompt(invocation_dir: str | None = None) -> dict | None:
    """Read the latest prompt artifact metadata. Returns None if absent."""
    import json as _json
    from pathlib import Path as _Path
    dir_path = _Path(invocation_dir) if invocation_dir else _Path(_BACKEND_INVOCATION_DIR)
    latest = dir_path / "latest.json"
    if not latest.exists():
        return None
    try:
        return _json.loads(latest.read_text())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94D — Output artifact capture
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class OutputArtifact:
    """A captured, redacted, quarantined backend output artifact."""

    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    output_hash: str = ""
    output_artifact_path: str = ""
    output_preview: str = ""
    output_size_bytes: int = 0
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    created_at_utc: str = ""
    redaction_applied: bool = False
    quarantined: bool = True
    applied_to_repo: bool = False
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "output_hash": self.output_hash,
            "output_artifact_path": self.output_artifact_path,
            "output_preview": self.output_preview,
            "output_size_bytes": self.output_size_bytes,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "created_at_utc": self.created_at_utc,
            "redaction_applied": self.redaction_applied,
            "quarantined": self.quarantined,
            "applied_to_repo": self.applied_to_repo,
            "schema_version": self.schema_version,
        }


def capture_backend_output_artifact(
    request: InvocationRequest,
    output_text: str,
    *,
    invocation_dir: str | None = None,
) -> dict[str, Any]:
    """Capture a backend output artifact.

    Redacts secrets, computes SHA-256 hash, writes timestamped artifact
    and updates latest-output.md + latest.json.  Output is ALWAYS
    quarantined (quarantined=True, applied_to_repo=False).

    Never invokes a backend, never runs subprocess, never calls network.
    Never applies output to source files, commits, or pushes.
    """
    import hashlib
    import json as _json
    import os
    from datetime import datetime, timezone
    from pathlib import Path as _Path

    dir_path = _Path(invocation_dir) if invocation_dir else _ensure_invocation_dir()
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")

    # 1. Redact and hash
    redacted_text, redaction_applied = _redact_prompt_text(output_text)
    output_hash = hashlib.sha256(output_text.encode()).hexdigest()
    output_size = len(redacted_text.encode())

    # 2. Write timestamped output
    output_filename = f"{ts}-{request.request_id}-output.md"
    output_path = dir_path / output_filename
    output_path.write_text(redacted_text)

    # 3. Build artifact metadata
    artifact = OutputArtifact(
        request_id=request.request_id,
        phase_id=request.phase_id,
        task_id=request.task_id,
        backend_id=request.backend_id,
        output_hash=output_hash,
        output_artifact_path=str(output_path),
        output_preview=redacted_text[:200] if len(redacted_text) > 200 else redacted_text,
        output_size_bytes=output_size,
        prompt_hash=request.prompt_hash,
        prompt_artifact_path=request.prompt_artifact_path,
        created_at_utc=now.isoformat(),
        redaction_applied=redaction_applied,
        quarantined=True,
        applied_to_repo=False,
    )

    # 4. Write metadata JSON
    meta_filename = f"{ts}-{request.request_id}.json"
    meta_path = dir_path / meta_filename
    meta_path.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))

    # 5. Update latest pointers
    latest_output = dir_path / "latest-output.md"
    latest_json = dir_path / "latest.json"
    latest_output.write_text(redacted_text)
    latest_tmp = dir_path / ".latest.tmp"
    latest_tmp.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))
    os.replace(str(latest_tmp), str(latest_json))

    return {
        "status": "captured",
        "request_id": request.request_id,
        "output_hash": output_hash,
        "output_path": str(output_path),
        "latest_output_path": str(latest_output),
        "latest_meta_path": str(latest_json),
        "redaction_applied": redaction_applied,
        "output_size_bytes": output_size,
        "quarantined": True,
        "applied_to_repo": False,
        "artifact": artifact,
    }


def read_latest_output(invocation_dir: str | None = None) -> dict | None:
    """Read the latest output artifact metadata. Returns None if absent."""
    import json as _json
    from pathlib import Path as _Path
    dir_path = _Path(invocation_dir) if invocation_dir else _Path(_BACKEND_INVOCATION_DIR)
    latest = dir_path / "latest.json"
    if not latest.exists():
        return None
    try:
        return _json.loads(latest.read_text())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94F — Mock backend invocation prototype
# ═══════════════════════════════════════════════════════════════════════════

_MOCK_OUTPUT_MARKER = "MOCK BACKEND OUTPUT — no real backend invoked"


def _generate_mock_output(prompt_text: str, request_id: str, backend_id: str) -> str:
    """Generate deterministic, safe mock backend output. In-process only."""
    import hashlib
    seed = hashlib.sha256(f"{request_id}:{prompt_text}".encode()).hexdigest()
    return (
        f"{_MOCK_OUTPUT_MARKER}\n\n"
        f"Request: {request_id}\n"
        f"Backend: {backend_id}\n"
        f"Prompt hash: {hashlib.sha256(prompt_text.encode()).hexdigest()}\n"
        f"Seed: {seed[:16]}\n\n"
        f"## Mock Response\n\n"
        f"This is a deterministic mock backend response.\n"
        f"The prompt was {len(prompt_text)} characters.\n"
        f"No real AI backend, subprocess, network, or shell was invoked.\n"
    )


def run_mock_backend_invocation(
    request: InvocationRequest,
    prompt_text: str,
    *,
    invocation_dir: str | None = None,
) -> dict[str, Any]:
    """Run in-process mock backend invocation lifecycle. No external calls."""
    reg = get_default_registry()

    if request.backend_id != "mock":
        return {
            "status": "blocked",
            "error": f"only 'mock' backend supported, got {request.backend_id!r}",
            "no_real_backend_invoked": True, "no_subprocess": True, "no_network": True,
        }

    readiness = check_invocation_readiness(request, reg)
    if readiness["status"] == READINESS_BLOCKED:
        return {
            "status": "blocked",
            "error": f"blocked: {'; '.join(readiness['hard_blocks'])}",
            "no_real_backend_invoked": True, "no_subprocess": True, "no_network": True,
        }

    if not request.no_execution_by_default:
        return {
            "status": "blocked",
            "error": "no_execution_by_default must be True",
            "no_real_backend_invoked": True,
        }

    prompt_result = capture_backend_prompt_artifact(request, prompt_text, invocation_dir=invocation_dir)
    mock_output = _generate_mock_output(prompt_text, request.request_id, request.backend_id)
    output_result = capture_backend_output_artifact(request, mock_output, invocation_dir=invocation_dir)

    return {
        "status": "completed",
        "request_id": request.request_id,
        "backend_id": request.backend_id,
        "readiness_status": readiness["status"],
        "prompt_hash": prompt_result["prompt_hash"],
        "prompt_path": prompt_result["prompt_path"],
        "output_hash": output_result["output_hash"],
        "output_path": output_result["output_path"],
        "quarantined": output_result["quarantined"],
        "applied_to_repo": output_result["applied_to_repo"],
        "no_real_backend_invoked": True,
        "no_subprocess": True,
        "no_network": True,
        "schema_version": SCHEMA_VERSION,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94G — Backend invocation audit trail
# ═══════════════════════════════════════════════════════════════════════════

_BACKEND_AUDIT_DIR = ".pcae/backend-invocations/audit"


def _audit_dir_path() -> Path:
    from pathlib import Path as _P
    return _P(_BACKEND_AUDIT_DIR)


def persist_backend_audit(
    event_type: str,
    request: InvocationRequest,
    *,
    readiness: dict[str, Any] | None = None,
    prompt_result: dict[str, Any] | None = None,
    output_result: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a redacted backend invocation audit record.

    Writes to .pcae/backend-invocations/audit/ with SHA-256 record digest.
    Never invokes backends, never fails into execution.
    """
    import hashlib
    import json as _json
    import os
    from datetime import datetime, timezone

    audit_id = f"ba-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")

    audit_dir = _audit_dir_path()
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    # Build redacted audit record
    record: dict[str, Any] = {
        "audit_id": audit_id,
        "timestamp_utc": now.isoformat(),
        "event_type": event_type,
        "request_id": request.request_id,
        "phase_id": request.phase_id,
        "task_id": request.task_id,
        "backend_id": request.backend_id,
        "execution_mode": request.execution_mode,
        "approval_state": request.approval_state,
        "readiness_status": readiness.get("status", "") if readiness else "",
        "hard_blocks": readiness.get("hard_blocks", []) if readiness else [],
        "missing_evidence": readiness.get("missing_evidence", []) if readiness else [],
        "warnings": readiness.get("warnings", []) if readiness else [],
        "prompt_hash": prompt_result.get("prompt_hash", "") if prompt_result else request.prompt_hash,
        "prompt_artifact_path": prompt_result.get("prompt_path", "") if prompt_result else request.prompt_artifact_path,
        "output_hash": output_result.get("output_hash", "") if output_result else "",
        "output_artifact_path": output_result.get("output_path", "") if output_result else "",
        "quarantined": output_result.get("quarantined", True) if output_result else True,
        "applied_to_repo": output_result.get("applied_to_repo", False) if output_result else False,
        "no_real_backend_invoked": True,
        "no_subprocess": True,
        "no_network": True,
        "no_execution": True,
        "no_enforcement": True,
        "source": "backend_invocation",
        "schema_version": SCHEMA_VERSION,
    }
    if extra:
        record.update(extra)

    # Compute digest (excluding record_digest)
    digest_input = _json.dumps(record, sort_keys=True, default=str)
    record_digest = hashlib.sha256(digest_input.encode()).hexdigest()
    record["record_digest"] = record_digest

    try:
        file_path = audit_dir / f"{ts}-{audit_id}.json"
        latest_path = audit_dir / "latest.json"
        file_path.write_text(_json.dumps(record, indent=2, sort_keys=True))
        tmp = audit_dir / ".latest.tmp"
        tmp.write_text(_json.dumps(record, indent=2, sort_keys=True))
        os.replace(str(tmp), str(latest_path))
        return {
            "status": "written",
            "audit_id": audit_id,
            "path": str(file_path),
            "latest_path": str(latest_path),
            "record_digest": record_digest,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def read_latest_backend_audit() -> dict | None:
    """Read latest backend audit record."""
    import json as _json
    p = _audit_dir_path() / "latest.json"
    if not p.exists():
        return None
    try:
        return _json.loads(p.read_text())
    except Exception:
        return None


def verify_backend_audit() -> dict:
    """Verify backend audit record integrity."""
    import json as _json
    import hashlib
    audit_dir = _audit_dir_path()
    result = {"total": 0, "valid": 0, "tampered": 0, "details": []}
    if not audit_dir.exists():
        return result
    for f in sorted(audit_dir.glob("*.json")):
        if f.name in ("latest.json", ".latest.tmp"):
            continue
        result["total"] += 1
        try:
            data = _json.loads(f.read_text())
            stored = data.pop("record_digest", None)
            if not stored:
                result["missing"] = result.get("missing", 0) + 1
                continue
            inp = _json.dumps(data, sort_keys=True, default=str)
            if hashlib.sha256(inp.encode()).hexdigest() == stored:
                result["valid"] += 1
            else:
                result["tampered"] += 1
                result["details"].append({"file": str(f), "status": "tampered"})
        except Exception:
            result["tampered"] += 1
    return result


def list_backend_audit(limit: int = 10) -> list[dict]:
    """List recent backend audit records."""
    import json as _json
    audit_dir = _audit_dir_path()
    records = []
    if not audit_dir.exists():
        return records
    for f in sorted(audit_dir.glob("*.json"), reverse=True):
        if f.name in ("latest.json", ".latest.tmp"):
            continue
        try:
            data = _json.loads(f.read_text())
            records.append({
                "file": f.name, "audit_id": data.get("audit_id", ""),
                "event_type": data.get("event_type", ""),
                "backend_id": data.get("backend_id", ""),
                "readiness_status": data.get("readiness_status", ""),
                "timestamp_utc": data.get("timestamp_utc", ""),
            })
            if len(records) >= limit:
                break
        except Exception:
            pass
    return records


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94H — Trust/readiness gate
# ═══════════════════════════════════════════════════════════════════════════

TRUST_COMPLETE = "complete"
TRUST_PARTIAL = "partial"
TRUST_INCOMPLETE = "incomplete"
TRUST_UNTRUSTED = "untrusted"

ASSESSMENT_READY = "ready"
ASSESSMENT_BLOCKED = "blocked"
ASSESSMENT_MISSING = "missing_evidence"
ASSESSMENT_REVIEW = "needs_human_review"
ASSESSMENT_INCOMPLETE = "incomplete"


def assess_backend_invocation_trust(
    request: InvocationRequest | None = None,
    *,
    readiness: dict[str, Any] | None = None,
    prompt_meta: dict[str, Any] | None = None,
    output_meta: dict[str, Any] | None = None,
    audit_meta: dict[str, Any] | None = None,
    audit_verified: bool = False,
) -> dict[str, Any]:
    """Assess backend invocation lifecycle trust. Fail-closed."""
    import uuid as _uuid
    assessment_id = f"as-{_uuid.uuid4().hex[:12]}"
    checks: dict[str, bool] = {}
    missing: list[str] = []
    hard_blocks: list[str] = []
    warnings: list[str] = []

    req_id = request.request_id if request else ""
    phase_id = request.phase_id if request else ""
    backend_id = request.backend_id if request else ""

    if request and not request.no_execution_by_default:
        hard_blocks.append("no_execution_by_default=False")

    prompt_present = bool(prompt_meta and prompt_meta.get("prompt_hash"))
    checks["prompt_artifact_present"] = prompt_present
    if not prompt_present:
        missing.append("prompt_artifact")

    output_present = bool(output_meta and output_meta.get("output_hash"))
    checks["output_artifact_present"] = output_present
    if not output_present and prompt_present:
        missing.append("output_artifact")

    if output_meta:
        quarantined = output_meta.get("quarantined", True)
        applied = output_meta.get("applied_to_repo", False)
        checks["output_quarantined"] = quarantined
        checks["applied_to_repo"] = applied
        if not quarantined:
            hard_blocks.append("output_not_quarantined")
        if applied:
            hard_blocks.append("output_applied_to_repo")

    audit_present = bool(audit_meta)
    checks["audit_record_present"] = audit_present
    checks["audit_record_verified"] = audit_verified
    if not audit_present:
        missing.append("audit_record")
    elif not audit_verified:
        warnings.append("audit_not_verified")

    checks["no_real_backend_invoked"] = True
    checks["no_subprocess"] = True
    checks["no_network"] = True
    checks["no_execution"] = True
    checks["no_enforcement"] = True

    if hard_blocks:
        status = ASSESSMENT_BLOCKED
        trust = TRUST_UNTRUSTED
    elif missing:
        status = ASSESSMENT_MISSING
        trust = TRUST_PARTIAL
    elif warnings:
        status = ASSESSMENT_READY
        trust = TRUST_PARTIAL
    else:
        status = ASSESSMENT_READY
        trust = TRUST_COMPLETE

    return {
        "assessment_id": assessment_id, "request_id": req_id,
        "phase_id": phase_id, "backend_id": backend_id,
        "status": status, "trust_level": trust,
        "backend_invocation_ready": status == ASSESSMENT_READY,
        "checks": checks, "missing_evidence": missing,
        "hard_blocks": hard_blocks, "warnings": warnings,
        "no_real_backend_invoked": True, "no_subprocess": True,
        "no_network": True, "no_execution": True, "no_enforcement": True,
        "recommended_action": (
            "blocked" if hard_blocks else
            "gather_evidence" if missing else
            "manual_review" if warnings else "proceed"
        ),
        "schema_version": SCHEMA_VERSION,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94J — Backend review state model
# ═══════════════════════════════════════════════════════════════════════════

REVIEW_CAPTURED = "captured"
REVIEW_QUARANTINED = "quarantined"
REVIEW_PENDING = "review_pending"
REVIEW_REVIEWED = "reviewed"
REVIEW_APPROVED = "approved_for_apply"
REVIEW_REJECTED = "rejected"

VALID_REVIEW_STATES: frozenset[str] = frozenset({
    REVIEW_CAPTURED, REVIEW_QUARANTINED, REVIEW_PENDING,
    REVIEW_REVIEWED, REVIEW_APPROVED, REVIEW_REJECTED,
})

_REVIEWS_DIR = ".pcae/backend-reviews"


@dataclass
class ReviewArtifact:
    review_id: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    output_hash: str = ""
    output_artifact_path: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    audit_id: str = ""
    trust_assessment_id: str = ""
    review_state: str = REVIEW_QUARANTINED
    operator: str = ""
    decision: str = ""
    decision_reason: str = ""
    created_at_utc: str = ""
    approved_for_apply: bool = False
    rejected: bool = False
    apply_ready: bool = False
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues = []
        if not self.request_id:
            issues.append("request_id required")
        if not self.output_hash:
            issues.append("output_hash required")
        if self.review_state not in VALID_REVIEW_STATES:
            issues.append(f"invalid review_state: {self.review_state!r}")
        if self.approved_for_apply and self.hard_blocks:
            issues.append("cannot approve with hard blocks")
        if self.apply_ready:
            issues.append("apply_ready not supported in 94J")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id, "request_id": self.request_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "backend_id": self.backend_id, "output_hash": self.output_hash,
            "output_artifact_path": self.output_artifact_path,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "audit_id": self.audit_id,
            "trust_assessment_id": self.trust_assessment_id,
            "review_state": self.review_state, "operator": self.operator,
            "decision": self.decision, "decision_reason": self.decision_reason,
            "created_at_utc": self.created_at_utc,
            "approved_for_apply": self.approved_for_apply,
            "rejected": self.rejected, "apply_ready": self.apply_ready,
            "hard_blocks": self.hard_blocks,
            "missing_evidence": self.missing_evidence,
            "warnings": self.warnings, "schema_version": self.schema_version,
        }


@dataclass
class ApprovalArtifact:
    approval_id: str = ""
    review_id: str = ""
    request_id: str = ""
    output_hash: str = ""
    operator: str = ""
    reason: str = ""
    approved_at_utc: str = ""
    expires_at_utc: str = ""
    hard_blocks_present: bool = False
    accepted_risk: bool = False
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues = []
        if not self.output_hash:
            issues.append("output_hash required")
        if not self.operator:
            issues.append("operator required")
        if self.hard_blocks_present:
            issues.append("approval invalid: hard blocks present")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id, "review_id": self.review_id,
            "request_id": self.request_id, "output_hash": self.output_hash,
            "operator": self.operator, "reason": self.reason,
            "approved_at_utc": self.approved_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "hard_blocks_present": self.hard_blocks_present,
            "accepted_risk": self.accepted_risk,
            "schema_version": self.schema_version,
        }


@dataclass
class RejectionArtifact:
    rejection_id: str = ""
    review_id: str = ""
    request_id: str = ""
    output_hash: str = ""
    operator: str = ""
    reason: str = ""
    rejected_at_utc: str = ""
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues = []
        if not self.output_hash:
            issues.append("output_hash required")
        if not self.operator:
            issues.append("operator required")
        if not self.reason:
            issues.append("reason required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "rejection_id": self.rejection_id,
            "review_id": self.review_id,
            "request_id": self.request_id,
            "output_hash": self.output_hash,
            "operator": self.operator,
            "reason": self.reason,
            "rejected_at_utc": self.rejected_at_utc,
            "schema_version": self.schema_version,
        }


def _reviews_dir() -> Path:
    from pathlib import Path as _P
    return _P(_REVIEWS_DIR)


def create_review_artifact(request_id: str, output_hash: str, *, backend_id: str = "", **kwargs: Any) -> ReviewArtifact:
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    review = ReviewArtifact(
        review_id=f"rv-{uuid.uuid4().hex[:12]}", request_id=request_id,
        output_hash=output_hash, backend_id=backend_id, created_at_utc=now,
        approved_for_apply=False, rejected=False, apply_ready=False,
        review_state=REVIEW_QUARANTINED,
        **{k: v for k, v in kwargs.items() if k in ReviewArtifact.__dataclass_fields__},
    )
    issues = review.validate()
    if issues:
        raise ValueError(f"Invalid review: {'; '.join(issues)}")
    return review


def approve_review(review: ReviewArtifact, operator: str, reason: str) -> ApprovalArtifact:
    if review.rejected or review.review_state == REVIEW_REJECTED:
        raise ValueError("Cannot approve: review is already rejected")
    if review.hard_blocks:
        raise ValueError("Cannot approve: hard blocks present")
    if not review.output_hash:
        raise ValueError("Missing output_hash")
    import uuid
    now = datetime.now(timezone.utc)
    approval = ApprovalArtifact(
        approval_id=f"ap-{uuid.uuid4().hex[:12]}", review_id=review.review_id,
        request_id=review.request_id, output_hash=review.output_hash,
        operator=operator, reason=reason, approved_at_utc=now.isoformat(),
    )
    issues = approval.validate()
    if issues:
        raise ValueError(f"Invalid approval: {'; '.join(issues)}")
    review.review_state = REVIEW_APPROVED
    review.approved_for_apply = True
    review.operator = operator
    review.decision = "approved"
    review.decision_reason = reason
    return approval


def reject_review(review: ReviewArtifact, operator: str, reason: str) -> RejectionArtifact:
    import uuid
    now = datetime.now(timezone.utc)
    rejection = RejectionArtifact(
        rejection_id=f"rj-{uuid.uuid4().hex[:12]}", review_id=review.review_id,
        request_id=review.request_id, output_hash=review.output_hash,
        operator=operator, reason=reason, rejected_at_utc=now.isoformat(),
    )
    review.review_state = REVIEW_REJECTED
    review.rejected = True
    review.operator = operator
    review.decision = "rejected"
    review.decision_reason = reason
    return rejection


def persist_review(review: ReviewArtifact) -> dict:
    import json as _json, os
    d = _reviews_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{review.review_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(review.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(review.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "latest_path": str(lp)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def read_latest_review() -> ReviewArtifact | None:
    import json as _json
    lp = _reviews_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ReviewArtifact(**{k: v for k, v in data.items() if k in ReviewArtifact.__dataclass_fields__})
    except Exception:
        return None


def persist_approval(approval: ApprovalArtifact, review: ReviewArtifact) -> dict:
    """Persist an approval artifact to .pcae/backend-reviews/.

    Writes timestamped approval JSON and updates latest.json with the
    updated review state.  Never executes apply, mutates source files,
    or authorizes commit/push.
    """
    import json as _json, os
    d = _reviews_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        ap = d / f"{ts}-{approval.approval_id}.json"
        ap.write_text(_json.dumps(approval.to_dict(), indent=2, sort_keys=True))
        # Update latest.json with the reviewed/approved review state
        lp = d / "latest.json"
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(review.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {
            "status": "written",
            "approval_path": str(ap),
            "latest_path": str(lp),
            "approval_id": approval.approval_id,
            "review_state": review.review_state,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def persist_rejection(rejection: RejectionArtifact, review: ReviewArtifact) -> dict:
    """Persist a rejection artifact to .pcae/backend-reviews/.

    Writes timestamped rejection JSON and updates latest.json with the
    rejected review state.  Never mutates source files or authorizes anything.
    """
    import json as _json, os
    d = _reviews_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        rp = d / f"{ts}-{rejection.rejection_id}.json"
        rp.write_text(_json.dumps(rejection.to_dict(), indent=2, sort_keys=True))
        lp = d / "latest.json"
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(review.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {
            "status": "written",
            "rejection_path": str(rp),
            "latest_path": str(lp),
            "rejection_id": rejection.rejection_id,
            "review_state": review.review_state,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94K — Apply plan model
# ═══════════════════════════════════════════════════════════════════════════

OP_CREATE = "create_file"
OP_MODIFY = "modify_file"
OP_DELETE = "delete_file"
OP_RENAME = "rename_file"
OP_MANUAL = "manual_instruction"
OP_UNKNOWN = "unknown"

VALID_OPERATIONS: frozenset[str] = frozenset({
    OP_CREATE, OP_MODIFY, OP_DELETE, OP_RENAME, OP_MANUAL, OP_UNKNOWN,
})
HIGH_RISK_OPS: frozenset[str] = frozenset({OP_DELETE, OP_RENAME, OP_UNKNOWN})

_APPLY_PLANS_DIR = ".pcae/backend-apply-plans"


@dataclass
class ApplyOperation:
    operation_id: str = ""
    operation_type: str = OP_MANUAL
    target_path: str = ""
    source_artifact_path: str = ""
    content_hash: str = ""
    risk_level: str = RISK_MEDIUM
    allowed_by_task_scope: bool = False
    forbidden: bool = False
    requires_manual_review: bool = True
    notes: str = ""
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues = []
        if self.operation_type not in VALID_OPERATIONS:
            issues.append(f"invalid operation_type: {self.operation_type!r}")
        if not self.target_path and self.operation_type not in (OP_MANUAL, OP_UNKNOWN):
            issues.append("target_path required for file operations")
        if self.operation_type in HIGH_RISK_OPS:
            # High-risk ops are valid but must be hard-blocked at plan level
            pass
        return issues

    def path_hard_blocks(self, *, forbidden_files: list[str] | None = None) -> list[str]:
        """Return hard-block reasons for this operation's target path.

        Separate from validate() so callers can collect hard blocks without
        raising.  Path safety is enforced via hard blocks, not ValidationErrors.
        """
        if self.operation_type in (OP_MANUAL, OP_UNKNOWN):
            return []
        return validate_operation_path(self.target_path, forbidden_files=forbidden_files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id, "operation_type": self.operation_type,
            "target_path": self.target_path, "source_artifact_path": self.source_artifact_path,
            "content_hash": self.content_hash, "risk_level": self.risk_level,
            "allowed_by_task_scope": self.allowed_by_task_scope,
            "forbidden": self.forbidden, "requires_manual_review": self.requires_manual_review,
            "notes": self.notes, "schema_version": self.schema_version,
        }


@dataclass
class RollbackRequirement:
    rollback_required: bool = True
    rollback_plan_id: str = ""
    rollback_evidence_required: bool = True
    affected_files: list[str] = field(default_factory=list)
    pre_apply_snapshot_required: bool = True
    manual_recovery_notes: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_required": self.rollback_required,
            "rollback_plan_id": self.rollback_plan_id,
            "rollback_evidence_required": self.rollback_evidence_required,
            "affected_files": self.affected_files,
            "pre_apply_snapshot_required": self.pre_apply_snapshot_required,
            "manual_recovery_notes": self.manual_recovery_notes,
            "schema_version": self.schema_version,
        }


@dataclass
class ApplyPlan:
    apply_plan_id: str = ""
    review_id: str = ""
    approval_id: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    output_hash: str = ""
    output_artifact_path: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    proposed_files: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    operations: list[ApplyOperation] = field(default_factory=list)
    risk_level: str = RISK_MEDIUM
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rollback_required: bool = True
    rollback_plan_id: str = ""
    tests_to_run: list[str] = field(default_factory=list)
    check_required: bool = True
    apply_ready: bool = False
    created_at_utc: str = ""
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues = []
        if not self.output_hash:
            issues.append("output_hash required")
        if not self.review_id:
            issues.append("review_id required")
        if self.apply_ready and self.hard_blocks:
            issues.append("cannot be apply_ready with hard blocks")
        for i, op in enumerate(self.operations):
            op_issues = op.validate()
            for oi in op_issues:
                issues.append(f"operation[{i}]: {oi}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_plan_id": self.apply_plan_id, "review_id": self.review_id,
            "approval_id": self.approval_id, "request_id": self.request_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "backend_id": self.backend_id, "output_hash": self.output_hash,
            "output_artifact_path": self.output_artifact_path,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "proposed_files": self.proposed_files,
            "allowed_files": self.allowed_files,
            "forbidden_files": self.forbidden_files,
            "operations": [op.to_dict() for op in self.operations],
            "risk_level": self.risk_level, "hard_blocks": self.hard_blocks,
            "missing_evidence": self.missing_evidence, "warnings": self.warnings,
            "rollback_required": self.rollback_required,
            "rollback_plan_id": self.rollback_plan_id,
            "tests_to_run": self.tests_to_run, "check_required": self.check_required,
            "apply_ready": self.apply_ready, "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }


def _apply_plans_dir() -> Path:
    from pathlib import Path as _P
    return _P(_APPLY_PLANS_DIR)


def create_apply_plan(
    review: ReviewArtifact,
    approval: ApprovalArtifact | None = None,
    *,
    operations: list[ApplyOperation] | None = None,
    allowed_files: list[str] | None = None,
    forbidden_files: list[str] | None = None,
    **kwargs: Any,
) -> ApplyPlan:
    """Create apply plan. Safe defaults. No execution."""
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    ops = list(operations or [])
    hard_blocks: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    if not approval:
        missing.append("approval")
    if not review.rollback_required if hasattr(review, 'rollback_required') else True:
        missing.append("rollback_plan")

    proposed = [op.target_path for op in ops if op.target_path]
    for f in proposed:
        if forbidden_files and f in forbidden_files:
            hard_blocks.append(f"forbidden_file:{f}")

    seen_paths: dict[str, str] = {}
    for op in ops:
        # Path safety hard blocks (absolute, traversal, forbidden)
        for pb in op.path_hard_blocks(forbidden_files=list(forbidden_files) if forbidden_files else None):
            if pb not in hard_blocks:
                hard_blocks.append(pb)
        if op.operation_type in HIGH_RISK_OPS:
            hard_blocks.append(f"high_risk_op:{op.operation_type}:{op.target_path}")
        if op.forbidden:
            hard_blocks.append(f"forbidden_op:{op.operation_type}:{op.target_path}")
        # Duplicate / conflicting operation detection
        p = op.target_path
        if p and op.operation_type not in (OP_MANUAL, OP_UNKNOWN):
            if p in seen_paths:
                prev = seen_paths[p]
                if prev != op.operation_type:
                    hard_blocks.append(f"conflicting_operations:{p}:{prev}+{op.operation_type}")
                else:
                    warnings.append(f"duplicate_operation:{p}:{op.operation_type}")
            else:
                seen_paths[p] = op.operation_type

    if not ops:
        missing.append("operations")

    plan = ApplyPlan(
        apply_plan_id=f"pl-{_uuid.uuid4().hex[:12]}",
        review_id=review.review_id,
        approval_id=approval.approval_id if approval else "",
        request_id=review.request_id, phase_id=review.phase_id,
        task_id=review.task_id, backend_id=review.backend_id,
        output_hash=review.output_hash,
        output_artifact_path=review.output_artifact_path,
        prompt_hash=review.prompt_hash,
        prompt_artifact_path=review.prompt_artifact_path,
        proposed_files=proposed,
        allowed_files=list(allowed_files or []),
        forbidden_files=list(forbidden_files or []),
        operations=ops, hard_blocks=hard_blocks,
        missing_evidence=missing, warnings=warnings,
        apply_ready=False, rollback_required=True, check_required=True,
        created_at_utc=now,
        **{k: v for k, v in kwargs.items() if k in ApplyPlan.__dataclass_fields__},
    )
    issues = plan.validate()
    if issues:
        raise ValueError(f"Invalid apply plan: {'; '.join(issues)}")
    return plan


def validate_apply_plan(plan: ApplyPlan) -> dict[str, Any]:
    """Validate apply plan readiness. Fail-closed."""
    hard_blocks = list(plan.hard_blocks)
    missing = list(plan.missing_evidence)
    warnings = list(plan.warnings)

    if not plan.review_id:
        missing.append("review_id")
    if not plan.approval_id:
        missing.append("approval_id")
    if not plan.output_hash:
        hard_blocks.append("output_hash_missing")
    if plan.forbidden_files:
        for f in plan.proposed_files:
            if f in plan.forbidden_files:
                hard_blocks.append(f"forbidden:{f}")
    if not plan.operations:
        missing.append("operations")
    if not plan.rollback_plan_id and plan.rollback_required:
        missing.append("rollback_plan_id")
    if not plan.tests_to_run and plan.check_required:
        missing.append("tests_to_run")

    ready = len(hard_blocks) == 0 and len(missing) == 0
    return {
        "apply_ready": ready,
        "status": "ready" if ready else "blocked" if hard_blocks else "missing_evidence",
        "hard_blocks": hard_blocks,
        "missing_evidence": missing,
        "warnings": warnings,
    }


def persist_apply_plan(plan: ApplyPlan) -> dict:
    """Persist apply plan artifact."""
    import json as _json, os
    d = _apply_plans_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{plan.apply_plan_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "latest_path": str(lp)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94L — Apply readiness validator
# ═══════════════════════════════════════════════════════════════════════════

READINESS_INCOMPLETE = "incomplete"
READINESS_UNTRUSTED = "untrusted"

_APPLY_READINESS_DIR = ".pcae/backend-apply-readiness"
_APPLY_READINESS_SCHEMA_VERSION = "1.0"

# Actions — strictly read-only / manual-package, never "execute apply"
ACTION_MANUAL_APPLY_PACKAGE_READY = "manual_apply_package_ready"
ACTION_CREATE_MANUAL_APPLY_PACKAGE = "create_manual_apply_package"
ACTION_BLOCKED_HARD = "blocked_hard"
ACTION_GATHER_EVIDENCE = "gather_evidence"
ACTION_NEEDS_HUMAN_REVIEW = "needs_human_review"
ACTION_UNTRUSTED = "untrusted"


@dataclass
class BackendApplyReadinessAssessment:
    """Fail-closed readiness assessment for a backend apply plan.

    Evaluates an apply plan against review, approval, output, and trust
    evidence.  Never executes apply, never mutates files, never invokes
    backends, never runs subprocess, never calls network.

    Safe defaults: apply_ready=False, all checks start False, hard_blocks
    dominate, human approval cannot override hard blocks, accepted risk
    cannot override hard blocks.
    """

    assessment_id: str = ""
    apply_plan_id: str = ""
    review_id: str = ""
    approval_id: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    status: str = READINESS_INCOMPLETE
    apply_ready: bool = False
    trust_level: str = TRUST_UNTRUSTED
    output_hash_verified: bool = False
    approval_bound_to_output_hash: bool = False
    review_state_valid: bool = False
    output_quarantined: bool = False
    output_not_applied: bool = False
    allowed_files_present: bool = False
    forbidden_files_present: bool = False
    operations_valid: bool = False
    rollback_ready: bool = False
    tests_defined: bool = False
    check_required: bool = True
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_action: str = ACTION_GATHER_EVIDENCE
    created_at_utc: str = ""
    schema_version: str = _APPLY_READINESS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "apply_plan_id": self.apply_plan_id,
            "review_id": self.review_id,
            "approval_id": self.approval_id,
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "status": self.status,
            "apply_ready": self.apply_ready,
            "trust_level": self.trust_level,
            "output_hash_verified": self.output_hash_verified,
            "approval_bound_to_output_hash": self.approval_bound_to_output_hash,
            "review_state_valid": self.review_state_valid,
            "output_quarantined": self.output_quarantined,
            "output_not_applied": self.output_not_applied,
            "allowed_files_present": self.allowed_files_present,
            "forbidden_files_present": self.forbidden_files_present,
            "operations_valid": self.operations_valid,
            "rollback_ready": self.rollback_ready,
            "tests_defined": self.tests_defined,
            "check_required": self.check_required,
            "hard_blocks": list(self.hard_blocks),
            "missing_evidence": list(self.missing_evidence),
            "warnings": list(self.warnings),
            "recommended_action": self.recommended_action,
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendApplyReadinessAssessment":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


def _apply_readiness_dir() -> Path:
    from pathlib import Path as _P
    return _P(_APPLY_READINESS_DIR)


def validate_backend_apply_readiness(
    plan: ApplyPlan | None = None,
    *,
    review: ReviewArtifact | None = None,
    approval: ApprovalArtifact | None = None,
    output_meta: dict[str, Any] | None = None,
    trust_assessment: dict[str, Any] | None = None,
) -> BackendApplyReadinessAssessment:
    """Validate backend apply readiness.  Fail-closed — blocks on uncertainty.

    Evaluates an apply plan against review, approval, output hash binding,
    quarantine, allowed/forbidden files, operation validity, rollback
    readiness, and test/check requirements.

    Hard blocks cannot be overridden by human approval or accepted risk.
    Commit/push authorization is never granted.

    Returns BackendApplyReadinessAssessment with apply_ready=True only when
    all evidence is complete and no hard blocks exist.

    Never executes apply, mutates files, invokes backends, runs subprocess,
    or calls network.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    assessment_id = f"ra-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    # ── Fail-closed: missing plan ────────────────────────────────────────
    if plan is None:
        return BackendApplyReadinessAssessment(
            assessment_id=assessment_id,
            status=READINESS_BLOCKED,
            apply_ready=False,
            trust_level=TRUST_UNTRUSTED,
            hard_blocks=["apply_plan_missing"],
            missing_evidence=["apply_plan"],
            recommended_action=ACTION_BLOCKED_HARD,
            created_at_utc=now,
        )

    # ── Extract plan context ─────────────────────────────────────────────
    plan_id = plan.apply_plan_id
    plan_review_id = plan.review_id
    plan_approval_id = plan.approval_id
    plan_output_hash = plan.output_hash
    plan_phase_id = plan.phase_id
    plan_task_id = plan.task_id
    plan_backend_id = plan.backend_id
    plan_request_id = plan.request_id

    # ── 1. Review evidence ───────────────────────────────────────────────
    review_present = review is not None
    review_id = review.review_id if review else ""
    if not review_present and not plan_review_id:
        missing.append("review_artifact")
    elif review is not None:
        if review.review_id != plan_review_id:
            hard_blocks.append("review_id_mismatch")
        if review.review_state not in (REVIEW_APPROVED, REVIEW_REVIEWED):
            missing.append("review_not_approved_or_reviewed")
    elif plan_review_id:
        missing.append("review_artifact_not_provided")

    # ── 2. Approval evidence ─────────────────────────────────────────────
    approval_present = approval is not None
    approval_id = approval.approval_id if approval else ""
    if not approval_present and not plan_approval_id:
        missing.append("approval_artifact")
    elif approval is not None:
        if plan_approval_id and approval.approval_id != plan_approval_id:
            hard_blocks.append("approval_id_mismatch")
        # Hash binding: approval must bind to the exact output_hash
        if approval.output_hash and plan_output_hash and approval.output_hash != plan_output_hash:
            hard_blocks.append("approval_output_hash_mismatch")
        if approval.hard_blocks_present:
            hard_blocks.append("approval_has_hard_blocks")
    elif plan_approval_id:
        missing.append("approval_artifact_not_provided")

    # ── 3. Output hash verification ──────────────────────────────────────
    if not plan_output_hash:
        hard_blocks.append("output_hash_missing")
    elif output_meta is not None:
        stored_hash = output_meta.get("output_hash", "")
        if stored_hash and stored_hash != plan_output_hash:
            hard_blocks.append("output_hash_mismatch")
        # Quarantine check
        quarantined = output_meta.get("quarantined", True)
        applied = output_meta.get("applied_to_repo", False)
        if not quarantined:
            hard_blocks.append("output_not_quarantined")
        if applied:
            hard_blocks.append("output_already_applied")

    # ── 4. Trust assessment integration ──────────────────────────────────
    if trust_assessment is not None:
        trust_status = trust_assessment.get("status", "")
        trust_level = trust_assessment.get("trust_level", TRUST_UNTRUSTED)
        trust_hard_blocks = trust_assessment.get("hard_blocks", [])
        if trust_hard_blocks:
            hard_blocks.extend(f"trust:{b}" for b in trust_hard_blocks)
        if trust_status == ASSESSMENT_BLOCKED:
            hard_blocks.append("trust_assessment_blocked")
        elif trust_level == TRUST_UNTRUSTED:
            hard_blocks.append("trust_level_untrusted")
    else:
        missing.append("trust_assessment")

    # ── 5. File scope validation ─────────────────────────────────────────
    proposed = list(plan.proposed_files)
    allowed = list(plan.allowed_files)
    forbidden = list(plan.forbidden_files)

    if forbidden:
        for f in proposed:
            if f in forbidden:
                hard_blocks.append(f"forbidden_file:{f}")
    if proposed and not allowed:
        warnings.append("allowed_files_not_defined")

    # ── 6. Operation validation ──────────────────────────────────────────
    operations = list(plan.operations)
    if not operations:
        missing.append("operations")
    else:
        for op in operations:
            op_type = op.operation_type
            target = op.target_path
            if op.forbidden:
                hard_blocks.append(f"forbidden_op:{op_type}:{target}")
            if op_type in HIGH_RISK_OPS:
                # delete/rename/unknown → hard block unless explicitly gated
                hard_blocks.append(f"high_risk_op:{op_type}:{target}")
            if op_type == OP_UNKNOWN:
                hard_blocks.append(f"unknown_operation:{target}")
            if op_type in (OP_DELETE, OP_RENAME):
                hard_blocks.append(f"destructive_op:{op_type}:{target}")

    # ── 7. Rollback readiness ────────────────────────────────────────────
    if plan.rollback_required and not plan.rollback_plan_id:
        missing.append("rollback_plan_id")
    if plan.rollback_required:
        warnings.append("rollback_required")

    # ── 8. Tests/check requirements ──────────────────────────────────────
    if plan.check_required and not plan.tests_to_run:
        missing.append("tests_to_run")
    if plan.check_required:
        warnings.append("check_required_before_apply")

    # ── 9. Hard blocks from plan ─────────────────────────────────────────
    for hb in plan.hard_blocks:
        if hb not in hard_blocks:
            hard_blocks.append(hb)

    # ── 10. Missing evidence from plan ───────────────────────────────────
    for me in plan.missing_evidence:
        if me not in missing:
            missing.append(me)

    # ── Determine status ─────────────────────────────────────────────────
    output_hash_ok = (
        bool(plan_output_hash)
        and not any("output_hash" in hb for hb in hard_blocks)
    )
    approval_bound = (
        approval is not None
        and bool(approval.output_hash)
        and approval.output_hash == plan_output_hash
        and not any("approval" in hb for hb in hard_blocks)
    )
    review_valid = (
        review is not None
        and review.review_state in (REVIEW_APPROVED, REVIEW_REVIEWED)
        and not review.rejected
        and not any("review" in hb for hb in hard_blocks)
    )
    output_quarantined = (
        output_meta is not None
        and output_meta.get("quarantined", True)
        and not output_meta.get("applied_to_repo", False)
    )
    output_not_applied = (
        output_meta is None
        or not output_meta.get("applied_to_repo", False)
    )
    allowed_ok = not any("forbidden_file" in hb for hb in hard_blocks)
    ops_ok = not any(
        "forbidden_op" in hb or "high_risk_op" in hb
        or "unknown_operation" in hb or "destructive_op" in hb
        for hb in hard_blocks
    )
    rollback_ok = "rollback_plan_id" not in missing
    tests_ok = "tests_to_run" not in missing

    if hard_blocks:
        status = READINESS_BLOCKED
        trust = TRUST_UNTRUSTED
        action = ACTION_BLOCKED_HARD
    elif missing:
        status = READINESS_MISSING_EVIDENCE
        trust = TRUST_PARTIAL
        action = ACTION_GATHER_EVIDENCE
    elif "trust_level_untrusted" in missing:
        status = READINESS_UNTRUSTED
        trust = TRUST_UNTRUSTED
        action = ACTION_UNTRUSTED
    else:
        status = READINESS_READY
        trust = TRUST_COMPLETE
        action = ACTION_MANUAL_APPLY_PACKAGE_READY

    return BackendApplyReadinessAssessment(
        assessment_id=assessment_id,
        apply_plan_id=plan_id,
        review_id=review_id,
        approval_id=approval_id,
        request_id=plan_request_id,
        phase_id=plan_phase_id,
        task_id=plan_task_id,
        backend_id=plan_backend_id,
        status=status,
        apply_ready=(status == READINESS_READY),
        trust_level=trust,
        output_hash_verified=output_hash_ok,
        approval_bound_to_output_hash=approval_bound,
        review_state_valid=review_valid,
        output_quarantined=output_quarantined,
        output_not_applied=output_not_applied,
        allowed_files_present=allowed_ok,
        forbidden_files_present=bool(plan.forbidden_files),
        operations_valid=ops_ok,
        rollback_ready=rollback_ok,
        tests_defined=tests_ok,
        check_required=plan.check_required,
        hard_blocks=hard_blocks,
        missing_evidence=missing,
        warnings=warnings,
        recommended_action=action,
        created_at_utc=now,
    )


def persist_apply_readiness(assessment: BackendApplyReadinessAssessment) -> dict:
    """Persist a readiness assessment artifact.

    Writes to .pcae/backend-apply-readiness/ with timestamped file and
    updates latest.json pointer.  Never executes apply, never mutates files.
    """
    import json as _json, os
    d = _apply_readiness_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{assessment.assessment_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "latest_path": str(lp)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def read_latest_apply_readiness() -> BackendApplyReadinessAssessment | None:
    """Read the latest apply readiness assessment. Returns None if absent."""
    import json as _json
    lp = _apply_readiness_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return BackendApplyReadinessAssessment.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94N — Apply plan read helpers
# ═══════════════════════════════════════════════════════════════════════════

def read_latest_apply_plan() -> ApplyPlan | None:
    """Read the latest apply plan. Returns None if absent."""
    import json as _json
    lp = _apply_plans_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        plan = ApplyPlan(**{k: v for k, v in data.items()
                             if k in ApplyPlan.__dataclass_fields__})
        # Deserialize operations list
        ops_raw = data.get("operations", [])
        ops = []
        for od in ops_raw:
            if isinstance(od, dict):
                ops.append(ApplyOperation(**{k: v for k, v in od.items()
                                              if k in ApplyOperation.__dataclass_fields__}))
        plan.operations = ops
        return plan
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94O — Backend Manual Apply Package
# ═══════════════════════════════════════════════════════════════════════════

_MANUAL_APPLY_PACKAGES_DIR = ".pcae/backend-manual-apply-packages"

_MANUAL_APPLY_SCHEMA_VERSION = "1.0"


@dataclass
class BackendManualApplyPackage:
    """Human-readable evidence bundle for manual apply decision.

    Bundles apply-plan, readiness assessment, review, approval, audit,
    and operator instructions into a single artifact.  Safe defaults:
    no_execution_performed=True, apply_ready mirrors validator output
    but does not imply execution.  Never authorises commit, push, or
    backend invocation.
    """

    package_id: str = ""
    apply_plan_id: str = ""
    readiness_assessment_id: str = ""
    review_id: str = ""
    approval_id: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    output_hash: str = ""
    output_artifact_path: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    audit_id: str = ""
    trust_assessment_id: str = ""
    review_state: str = ""
    readiness_status: str = ""
    apply_ready: bool = False
    proposed_files: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rollback_required: bool = True
    rollback_plan_id: str = ""
    rollback_instructions: str = ""
    tests_to_run: list[str] = field(default_factory=list)
    checks_to_run: list[str] = field(default_factory=list)
    manual_apply_instructions: str = ""
    operator_notes: str = ""
    no_execution_performed: bool = True
    created_at_utc: str = ""
    schema_version: str = _MANUAL_APPLY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "apply_plan_id": self.apply_plan_id,
            "readiness_assessment_id": self.readiness_assessment_id,
            "review_id": self.review_id,
            "approval_id": self.approval_id,
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "output_hash": self.output_hash,
            "output_artifact_path": self.output_artifact_path,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "audit_id": self.audit_id,
            "trust_assessment_id": self.trust_assessment_id,
            "review_state": self.review_state,
            "readiness_status": self.readiness_status,
            "apply_ready": self.apply_ready,
            "proposed_files": list(self.proposed_files),
            "allowed_files": list(self.allowed_files),
            "forbidden_files": list(self.forbidden_files),
            "operations": list(self.operations),
            "hard_blocks": list(self.hard_blocks),
            "missing_evidence": list(self.missing_evidence),
            "warnings": list(self.warnings),
            "rollback_required": self.rollback_required,
            "rollback_plan_id": self.rollback_plan_id,
            "rollback_instructions": self.rollback_instructions,
            "tests_to_run": list(self.tests_to_run),
            "checks_to_run": list(self.checks_to_run),
            "manual_apply_instructions": self.manual_apply_instructions,
            "operator_notes": self.operator_notes,
            "no_execution_performed": self.no_execution_performed,
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendManualApplyPackage":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})

    def render_markdown(self) -> str:
        """Render a human-readable Markdown summary of the package."""
        lines: list[str] = []
        lines.append(f"# Backend Manual Apply Package — {self.package_id}")
        lines.append("")
        lines.append("**This package is for manual human review only.**")
        lines.append("No files were modified by this package generation.")
        lines.append("No apply execution was performed.")
        lines.append("No backend was invoked.")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Package ID:           `{self.package_id}`")
        lines.append(f"- Apply plan ID:        `{self.apply_plan_id}`")
        lines.append(f"- Review ID:            `{self.review_id}`")
        lines.append(f"- Approval ID:          `{self.approval_id}`")
        lines.append(f"- Request ID:           `{self.request_id}`")
        lines.append(f"- Phase ID:             `{self.phase_id}`")
        lines.append(f"- Output hash:          `{self.output_hash}`")
        lines.append(f"- Readiness status:     **{self.readiness_status}**")
        lines.append(f"- Apply ready:          **{self.apply_ready}**")
        lines.append(f"- Rollback required:    {self.rollback_required}")
        lines.append(f"- Created:              {self.created_at_utc}")
        lines.append("")
        if self.hard_blocks:
            lines.append("## Hard Blocks (non-overridable)")
            lines.append("")
            for b in self.hard_blocks:
                lines.append(f"- ❌ `{b}`")
            lines.append("")
        if self.missing_evidence:
            lines.append("## Missing Evidence")
            lines.append("")
            for m in self.missing_evidence:
                lines.append(f"- ⚠️  `{m}`")
            lines.append("")
        if self.warnings:
            lines.append("## Warnings")
            lines.append("")
            for w in self.warnings:
                lines.append(f"- ℹ️  `{w}`")
            lines.append("")
        if self.proposed_files:
            lines.append("## Proposed Files")
            lines.append("")
            for f in self.proposed_files:
                lines.append(f"- `{f}`")
            lines.append("")
        if self.operations:
            lines.append("## Operations (descriptive metadata only)")
            lines.append("")
            for op in self.operations:
                lines.append(f"- `{op}`")
            lines.append("")
        lines.append("## Rollback Requirements")
        lines.append("")
        lines.append(f"- Rollback required: {self.rollback_required}")
        if self.rollback_plan_id:
            lines.append(f"- Rollback plan ID: `{self.rollback_plan_id}`")
        if self.rollback_instructions:
            lines.append("")
            lines.append("**Rollback instructions:**")
            lines.append("")
            lines.append(self.rollback_instructions)
        lines.append("")
        if self.tests_to_run:
            lines.append("## Tests to Run Manually")
            lines.append("")
            lines.append("⚠️  Run these tests **manually** after applying changes:")
            lines.append("")
            for t in self.tests_to_run:
                lines.append(f"- `{t}`")
            lines.append("")
        if self.checks_to_run:
            lines.append("## Checks to Run Manually")
            lines.append("")
            lines.append("⚠️  Run these checks **manually** after applying changes:")
            lines.append("")
            for c in self.checks_to_run:
                lines.append(f"- `{c}`")
            lines.append("")
        if self.manual_apply_instructions:
            lines.append("## Manual Apply Instructions")
            lines.append("")
            lines.append("⚠️  These instructions are **advisory only**.")
            lines.append("A human operator must review and execute them manually.")
            lines.append("")
            lines.append(self.manual_apply_instructions)
            lines.append("")
        if self.operator_notes:
            lines.append("## Operator Notes")
            lines.append("")
            lines.append(self.operator_notes)
            lines.append("")
        lines.append("## No-Execution Confirmation")
        lines.append("")
        lines.append(f"- `no_execution_performed`: **{self.no_execution_performed}**")
        lines.append("- No files were modified by this package generation.")
        lines.append("- No apply was executed.")
        lines.append("- No commit or push was authorized.")
        lines.append("- No backend was invoked.")
        lines.append("- No tests or checks were run automatically.")
        lines.append(f"- Schema version: {self.schema_version}")
        lines.append("")
        return "\n".join(lines)


def _manual_apply_packages_dir() -> Path:
    from pathlib import Path as _P
    return _P(_MANUAL_APPLY_PACKAGES_DIR)


def create_backend_manual_apply_package(
    plan: "ApplyPlan | None" = None,
    assessment: "BackendApplyReadinessAssessment | None" = None,
    *,
    review: "ReviewArtifact | None" = None,
    approval: "ApprovalArtifact | None" = None,
    operator_notes: str = "",
    rollback_instructions: str = "",
    manual_apply_instructions: str = "",
    **kwargs: Any,
) -> "BackendManualApplyPackage":
    """Create a BackendManualApplyPackage from evidence artifacts.

    Bundles apply plan + readiness assessment + review/approval metadata
    into a human-readable package for manual operator action.

    Never executes operations, never parses patches, never mutates files,
    never invokes backends, never runs tests or pcae check, never commits
    or pushes, never authorises commit/push.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()

    # Extract fields from plan
    apply_plan_id = plan.apply_plan_id if plan else ""
    request_id = plan.request_id if plan else ""
    phase_id = plan.phase_id if plan else ""
    task_id = plan.task_id if plan else ""
    backend_id = plan.backend_id if plan else ""
    output_hash = plan.output_hash if plan else ""
    output_artifact_path = plan.output_artifact_path if plan else ""
    prompt_hash = plan.prompt_hash if plan else ""
    prompt_artifact_path = plan.prompt_artifact_path if plan else ""
    proposed_files = list(plan.proposed_files) if plan else []
    allowed_files = list(plan.allowed_files) if plan else []
    forbidden_files = list(plan.forbidden_files) if plan else []
    rollback_required = plan.rollback_required if plan else True
    rollback_plan_id = plan.rollback_plan_id if plan else ""
    tests_to_run = list(plan.tests_to_run) if plan else []
    checks_to_run = []  # populate from plan.check_required advisory text
    if plan and plan.check_required:
        checks_to_run.append("pcae check (run manually after applying)")
    hard_blocks = list(plan.hard_blocks) if plan else []
    missing_evidence = list(plan.missing_evidence) if plan else []
    warnings = list(plan.warnings) if plan else []

    # Render operations as descriptive strings
    operations: list[str] = []
    if plan:
        for op in plan.operations:
            operations.append(f"{op.operation_type}:{op.target_path}")

    # Extract fields from review/approval
    review_id = ""
    approval_id = ""
    review_state = ""
    if plan:
        review_id = plan.review_id
        approval_id = plan.approval_id
    if review:
        review_id = review.review_id
        review_state = review.review_state
    if approval:
        approval_id = approval.approval_id

    # Extract fields from readiness assessment
    readiness_assessment_id = ""
    readiness_status = "incomplete"
    apply_ready = False
    if assessment:
        readiness_assessment_id = assessment.assessment_id
        readiness_status = assessment.status
        apply_ready = assessment.apply_ready
        # Merge in assessment hard blocks / missing / warnings (deduplicated)
        for b in assessment.hard_blocks:
            if b not in hard_blocks:
                hard_blocks.append(b)
        for m in assessment.missing_evidence:
            if m not in missing_evidence:
                missing_evidence.append(m)
        for w in assessment.warnings:
            if w not in warnings:
                warnings.append(w)

    # Build default manual apply instructions when not provided
    if not manual_apply_instructions:
        if apply_ready and not hard_blocks:
            manual_apply_instructions = (
                "Readiness check passed. A human operator may now:\n"
                "1. Review the proposed files and operations listed above.\n"
                "2. Apply changes manually using your preferred editor or tool.\n"
                "3. Run the tests listed in 'Tests to Run Manually'.\n"
                "4. Run the checks listed in 'Checks to Run Manually'.\n"
                "5. Commit changes using 'pcae commit implementation' (governed).\n"
                "6. Push using 'pcae push' (governed).\n"
                "No automatic apply was performed by package generation."
            )
        elif hard_blocks:
            manual_apply_instructions = (
                "Hard blocks are present. Apply is NOT permitted.\n"
                "Resolve all hard blocks before proceeding:\n"
                + "\n".join(f"  - {b}" for b in hard_blocks)
            )
        else:
            manual_apply_instructions = (
                "Missing evidence prevents apply readiness.\n"
                "Gather the missing evidence before proceeding:\n"
                + "\n".join(f"  - {m}" for m in missing_evidence)
            )

    pkg = BackendManualApplyPackage(
        package_id=f"pkg-{_uuid.uuid4().hex[:12]}",
        apply_plan_id=apply_plan_id,
        readiness_assessment_id=readiness_assessment_id,
        review_id=review_id,
        approval_id=approval_id,
        request_id=request_id,
        phase_id=phase_id,
        task_id=task_id,
        backend_id=backend_id,
        output_hash=output_hash,
        output_artifact_path=output_artifact_path,
        prompt_hash=prompt_hash,
        prompt_artifact_path=prompt_artifact_path,
        review_state=review_state,
        readiness_status=readiness_status,
        apply_ready=apply_ready,
        proposed_files=proposed_files,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        operations=operations,
        hard_blocks=hard_blocks,
        missing_evidence=missing_evidence,
        warnings=warnings,
        rollback_required=rollback_required,
        rollback_plan_id=rollback_plan_id,
        rollback_instructions=rollback_instructions,
        tests_to_run=tests_to_run,
        checks_to_run=checks_to_run,
        manual_apply_instructions=manual_apply_instructions,
        operator_notes=operator_notes,
        no_execution_performed=True,
        created_at_utc=now,
        **{k: v for k, v in kwargs.items()
           if k in BackendManualApplyPackage.__dataclass_fields__},
    )
    return pkg


def persist_manual_apply_package(pkg: BackendManualApplyPackage) -> dict:
    """Persist a manual apply package as JSON + Markdown.

    Writes to .pcae/backend-manual-apply-packages/ with timestamped
    filenames and updates latest.json and latest.md pointers.
    Never executes apply, never mutates source files.
    """
    import json as _json
    import os
    d = _manual_apply_packages_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        json_fp = d / f"{ts}-{pkg.package_id}.json"
        md_fp = d / f"{ts}-{pkg.package_id}.md"
        lp_json = d / "latest.json"
        lp_md = d / "latest.md"

        json_fp.write_text(_json.dumps(pkg.to_dict(), indent=2, sort_keys=True))
        md_fp.write_text(pkg.render_markdown())

        tmp_j = d / ".latest-j.tmp"
        tmp_j.write_text(_json.dumps(pkg.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp_j), str(lp_json))

        tmp_m = d / ".latest-m.tmp"
        tmp_m.write_text(pkg.render_markdown())
        os.replace(str(tmp_m), str(lp_md))

        return {
            "status": "written",
            "json_path": str(json_fp),
            "md_path": str(md_fp),
            "latest_json": str(lp_json),
            "latest_md": str(lp_md),
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def read_latest_manual_apply_package() -> "BackendManualApplyPackage | None":
    """Read the latest manual apply package. Returns None if absent."""
    import json as _json
    lp = _manual_apply_packages_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return BackendManualApplyPackage.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94P — Backend apply governance hardening
# ═══════════════════════════════════════════════════════════════════════════

# Path safety constants
_FORBIDDEN_PATH_PATTERNS: frozenset[str] = frozenset({
    ".env", ".git", ".pcae/session.json", ".pcae/agent-lock.json",
    ".pcae/architecture-history.json", ".pcae/provenance-history.json",
})


def validate_operation_path(
    path: str,
    *,
    forbidden_files: list[str] | None = None,
    forbidden_patterns: frozenset[str] | None = None,
) -> list[str]:
    """Validate an operation target path for safety.

    Returns a list of hard-block reason strings.  Empty list means safe.

    Checks:
    - empty path
    - absolute path (starts with / or drive letter on Windows)
    - parent traversal (.. in any component)
    - matches known forbidden file patterns
    - matches provided forbidden_files list

    Never executes, mutates, or invokes anything.
    """
    blocks: list[str] = []
    if not path or not path.strip():
        blocks.append("empty_target_path")
        return blocks
    # Absolute path check
    if _os.path.isabs(path):
        blocks.append(f"absolute_path:{path}")
    # Parent traversal
    parts = path.replace("\\", "/").split("/")
    if ".." in parts:
        blocks.append(f"parent_traversal_path:{path}")
    # Forbidden patterns
    pats = forbidden_patterns if forbidden_patterns is not None else _FORBIDDEN_PATH_PATTERNS
    for pat in pats:
        if path == pat or path.endswith("/" + pat):
            blocks.append(f"forbidden_path_pattern:{path}")
            break
    # Caller-supplied forbidden list
    if forbidden_files and path in forbidden_files:
        if not any("forbidden_file:" in b for b in blocks):
            blocks.append(f"forbidden_file:{path}")
    return blocks


def validate_operations_list(
    operations: list["ApplyOperation"],
    *,
    forbidden_files: list[str] | None = None,
) -> dict[str, Any]:
    """Validate a list of ApplyOperations for path safety and duplicates.

    Returns dict with keys:
    - hard_blocks: list of hard-block strings
    - warnings: list of warning strings
    - valid: bool

    Checks:
    - each target path via validate_operation_path()
    - duplicate target paths (same path, same or different op type)
    - conflicting operations (e.g. create + modify same target)

    Never executes or mutates anything.
    """
    hard_blocks: list[str] = []
    warnings: list[str] = []
    seen_paths: dict[str, str] = {}  # path -> first operation_type

    for i, op in enumerate(operations):
        path = op.target_path
        op_type = op.operation_type

        # Path-level validation for file operations
        if op_type not in (OP_MANUAL, OP_UNKNOWN):
            path_blocks = validate_operation_path(path, forbidden_files=forbidden_files)
            for pb in path_blocks:
                hard_blocks.append(f"operation[{i}]:{pb}")

        # Duplicate / conflict detection
        if path and path in seen_paths:
            prev_type = seen_paths[path]
            if prev_type != op_type:
                hard_blocks.append(f"conflicting_operations:{path}:{prev_type}+{op_type}")
            else:
                warnings.append(f"duplicate_operation:{path}:{op_type}")
        elif path:
            seen_paths[path] = op_type

        # Destructive ops
        if op_type in (OP_DELETE, OP_RENAME):
            hard_blocks.append(f"destructive_op:{op_type}:{path}")

        # Unknown operation
        if op_type == OP_UNKNOWN:
            hard_blocks.append(f"unknown_operation:{path}")

    return {
        "valid": len(hard_blocks) == 0,
        "hard_blocks": hard_blocks,
        "warnings": warnings,
    }


def validate_hash_chain(
    *,
    review: "ReviewArtifact | None" = None,
    approval: "ApprovalArtifact | None" = None,
    plan: "ApplyPlan | None" = None,
    assessment: "BackendApplyReadinessAssessment | None" = None,
    package: "BackendManualApplyPackage | None" = None,
) -> dict[str, Any]:
    """Validate output_hash and request_id chain across all evidence artifacts.

    Hash and request mismatches are hard blocks. Human approval cannot override.
    Accepted risk cannot override.

    Returns dict with keys:
    - valid: bool
    - hard_blocks: list of hard-block strings

    Never executes, mutates, or invokes anything.
    """
    hard_blocks: list[str] = []

    def _nonempty(a: str, b: str) -> bool:
        return bool(a) and bool(b)

    # review ↔ approval
    if review and approval:
        if _nonempty(review.output_hash, approval.output_hash):
            if review.output_hash != approval.output_hash:
                hard_blocks.append("review_approval_output_hash_mismatch")
        if _nonempty(review.request_id, approval.request_id):
            if review.request_id != approval.request_id:
                hard_blocks.append("review_approval_request_id_mismatch")

    # review ↔ plan
    if review and plan:
        if _nonempty(review.output_hash, plan.output_hash):
            if review.output_hash != plan.output_hash:
                hard_blocks.append("review_plan_output_hash_mismatch")
        if _nonempty(review.request_id, plan.request_id):
            if review.request_id != plan.request_id:
                hard_blocks.append("review_plan_request_id_mismatch")

    # approval ↔ plan
    if approval and plan:
        if _nonempty(approval.output_hash, plan.output_hash):
            if approval.output_hash != plan.output_hash:
                hard_blocks.append("approval_plan_output_hash_mismatch")

    # plan ↔ assessment
    if plan and assessment:
        if _nonempty(plan.apply_plan_id, assessment.apply_plan_id):
            if plan.apply_plan_id != assessment.apply_plan_id:
                hard_blocks.append("plan_assessment_id_mismatch")
        if _nonempty(plan.output_hash, assessment.request_id):
            pass  # different fields, no cross-check here
        # request_id cross-check
        if _nonempty(plan.request_id, assessment.request_id):
            if plan.request_id != assessment.request_id:
                hard_blocks.append("plan_assessment_request_id_mismatch")

    # plan ↔ package
    if plan and package:
        if _nonempty(plan.output_hash, package.output_hash):
            if plan.output_hash != package.output_hash:
                hard_blocks.append("plan_package_output_hash_mismatch")
        if _nonempty(plan.request_id, package.request_id):
            if plan.request_id != package.request_id:
                hard_blocks.append("plan_package_request_id_mismatch")
        if _nonempty(plan.apply_plan_id, package.apply_plan_id):
            if plan.apply_plan_id != package.apply_plan_id:
                hard_blocks.append("plan_package_apply_plan_id_mismatch")

    # assessment ↔ package
    if assessment and package:
        if _nonempty(assessment.assessment_id, package.readiness_assessment_id):
            if assessment.assessment_id != package.readiness_assessment_id:
                hard_blocks.append("assessment_package_id_mismatch")

    return {
        "valid": len(hard_blocks) == 0,
        "hard_blocks": hard_blocks,
    }


def validate_artifact_freshness(
    artifact: "dict[str, Any] | None",
    *,
    expected_output_hash: str = "",
    expected_request_id: str = "",
    expected_phase_id: str = "",
    artifact_label: str = "artifact",
) -> dict[str, Any]:
    """Validate that a loaded artifact dict is consistent and internally coherent.

    Returns dict with:
    - valid: bool
    - hard_blocks: list of hard-block strings
    - missing_evidence: list of missing field strings

    Checks:
    - artifact is not None
    - artifact is a non-empty dict
    - output_hash matches expected if provided
    - request_id matches expected if provided
    - phase_id matches expected if provided

    Never executes or mutates anything. Fail-closed on None/empty.
    """
    hard_blocks: list[str] = []
    missing: list[str] = []

    if artifact is None:
        hard_blocks.append(f"{artifact_label}_missing")
        return {"valid": False, "hard_blocks": hard_blocks, "missing_evidence": missing}

    if not isinstance(artifact, dict) or not artifact:
        hard_blocks.append(f"{artifact_label}_malformed")
        return {"valid": False, "hard_blocks": hard_blocks, "missing_evidence": missing}

    if expected_output_hash:
        stored = artifact.get("output_hash", "")
        if not stored:
            missing.append(f"{artifact_label}_output_hash_missing")
        elif stored != expected_output_hash:
            hard_blocks.append(f"{artifact_label}_output_hash_mismatch")

    if expected_request_id:
        stored = artifact.get("request_id", "")
        if not stored:
            missing.append(f"{artifact_label}_request_id_missing")
        elif stored != expected_request_id:
            hard_blocks.append(f"{artifact_label}_request_id_mismatch")

    if expected_phase_id:
        stored = artifact.get("phase_id", "")
        if stored and stored != expected_phase_id:
            hard_blocks.append(f"{artifact_label}_phase_id_mismatch")

    return {
        "valid": len(hard_blocks) == 0 and len(missing) == 0,
        "hard_blocks": hard_blocks,
        "missing_evidence": missing,
    }


def read_artifact_json_safe(path: "_PathType | str") -> "dict[str, Any] | None":
    """Read a JSON artifact file, returning None on any error.

    Returns None if:
    - path does not exist
    - file is not valid JSON
    - file content is not a dict

    Never raises, never mutates.
    """
    import json as _j
    try:
        p = _PathType(path)
        if not p.exists():
            return None
        data = _j.loads(p.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q — Backend lifecycle end-to-end mock demo
# ═══════════════════════════════════════════════════════════════════════════

_LIFECYCLE_DEMOS_DIR = ".pcae/backend-lifecycle-demos"
_LIFECYCLE_DEMO_SCHEMA_VERSION = "1.0"

# ── Demo lifecycle statuses ──────────────────────────────────────────────

DEMO_COMPLETED = "completed"
DEMO_BLOCKED = "blocked"
DEMO_PARTIAL = "partial"
DEMO_FAILED = "failed"

VALID_DEMO_STATUSES: frozenset[str] = frozenset({
    DEMO_COMPLETED, DEMO_BLOCKED, DEMO_PARTIAL, DEMO_FAILED,
})


@dataclass
class BackendLifecycleDemo:
    """End-to-end mock lifecycle demo summary artifact.

    Exercises the full governed backend flow — plan, prompt capture,
    mock output capture, audit, trust/readiness, review, approval,
    apply plan, apply readiness — without real backend invocation,
    without apply execution, without file mutation.

    All safety invariants are preserved:
    - no_real_backend_invoked = True
    - no_apply_execution = True
    - no_file_mutation = True
    - no_subprocess = True
    - no_network = True
    - no_shell_interception = True
    - output remains quarantined
    """

    demo_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    request_id: str = ""
    prompt_artifact_path: str = ""
    prompt_hash: str = ""
    output_artifact_path: str = ""
    output_hash: str = ""
    audit_id: str = ""
    trust_assessment_id: str = ""
    review_id: str = ""
    approval_id: str = ""
    rejection_id: str = ""
    apply_plan_id: str = ""
    apply_readiness_assessment_id: str = ""
    lifecycle_status: str = DEMO_PARTIAL
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    no_real_backend_invoked: bool = True
    no_apply_execution: bool = True
    no_file_mutation: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    no_shell_interception: bool = True
    created_at_utc: str = ""
    schema_version: str = _LIFECYCLE_DEMO_SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.demo_id:
            issues.append("demo_id is required")
        if self.lifecycle_status not in VALID_DEMO_STATUSES:
            issues.append(f"invalid lifecycle_status: {self.lifecycle_status!r}")
        if not self.no_real_backend_invoked:
            issues.append("no_real_backend_invoked must be True")
        if not self.no_apply_execution:
            issues.append("no_apply_execution must be True")
        if not self.no_file_mutation:
            issues.append("no_file_mutation must be True")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "demo_id": self.demo_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "backend_id": self.backend_id,
            "request_id": self.request_id,
            "prompt_artifact_path": self.prompt_artifact_path,
            "prompt_hash": self.prompt_hash,
            "output_artifact_path": self.output_artifact_path,
            "output_hash": self.output_hash,
            "audit_id": self.audit_id,
            "trust_assessment_id": self.trust_assessment_id,
            "review_id": self.review_id,
            "approval_id": self.approval_id,
            "rejection_id": self.rejection_id,
            "apply_plan_id": self.apply_plan_id,
            "apply_readiness_assessment_id": self.apply_readiness_assessment_id,
            "lifecycle_status": self.lifecycle_status,
            "hard_blocks": list(self.hard_blocks),
            "missing_evidence": list(self.missing_evidence),
            "warnings": list(self.warnings),
            "no_real_backend_invoked": self.no_real_backend_invoked,
            "no_apply_execution": self.no_apply_execution,
            "no_file_mutation": self.no_file_mutation,
            "no_subprocess": self.no_subprocess,
            "no_network": self.no_network,
            "no_shell_interception": self.no_shell_interception,
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendLifecycleDemo":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


def _lifecycle_demos_dir() -> Path:
    from pathlib import Path as _P
    return _P(_LIFECYCLE_DEMOS_DIR)


def run_mock_lifecycle_demo(
    *,
    phase_id: str = "94Q",
    task_id: str = "",
    backend_id: str = "mock",
    prompt_text: str = "",
    forbidden_path_check: bool = False,
    **kwargs: Any,
) -> tuple["BackendLifecycleDemo", dict[str, Any]]:
    """Run a complete end-to-end mock backend lifecycle demo.

    Exercises the full governed backend flow in sequence:
    1. backend plan (InvocationRequest + readiness check)
    2. prompt artifact capture
    3. mock backend output capture
    4. backend invocation audit
    5. trust/readiness assessment
    6. review artifact creation
    7. approval artifact creation
    8. apply plan creation
    9. apply readiness validation
    10. demo summary artifact

    All steps use mock backend only. No real backend invocation.
    No apply execution. No file mutation. No subprocess. No network.
    No shell interception.

    The forbidden_path_check flag, when True, causes the demo to exercise
    a negative-path scenario (blocked lifecycle). When False, the demo
    follows the happy path.

    Returns (BackendLifecycleDemo, step_details_dict).
    """
    import hashlib
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()

    demo_id = f"demo-{_uuid.uuid4().hex[:12]}"
    if not task_id:
        task_id = f"task-{_uuid.uuid4().hex[:12]}"

    steps: dict[str, Any] = {}
    hard_blocks: list[str] = []
    missing_evidence: list[str] = []
    warnings_list: list[str] = []

    prompt = prompt_text or (
        f"Mock lifecycle demo prompt for phase {phase_id}. "
        f"This is a safe, deterministic mock prompt for end-to-end testing."
    )

    # ── Step 1: backend plan ─────────────────────────────────────────────
    request = make_invocation_request(
        backend_id=backend_id,
        phase_id=phase_id,
        task_id=task_id,
        prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
        execution_mode=INVOCATION_MODE_DRY_RUN,
        allowed_files=["docs/demo-output.md"],
    )
    reg = get_default_registry()
    plan_readiness = check_invocation_readiness(request, reg)
    steps["plan"] = {
        "request_id": request.request_id,
        "backend_id": request.backend_id,
        "readiness_status": plan_readiness["status"],
    }
    if plan_readiness["status"] == READINESS_BLOCKED:
        hard_blocks.extend(plan_readiness.get("hard_blocks", []))

    # ── Step 2+3: mock backend invocation (prompt + output capture) ──────
    mock_result = run_mock_backend_invocation(request, prompt)
    steps["mock_invocation"] = mock_result

    if mock_result.get("status") != "completed":
        hard_blocks.append(f"mock_invocation_{mock_result.get('status', 'failed')}")

    prompt_hash_val = mock_result.get("prompt_hash", "")
    prompt_path = mock_result.get("prompt_path", "")
    output_hash_val = mock_result.get("output_hash", "")
    output_path = mock_result.get("output_path", "")

    # ── Step 4: backend invocation audit ─────────────────────────────────
    audit_result = persist_backend_audit(
        event_type="mock_lifecycle_demo",
        request=request,
        readiness=plan_readiness,
        prompt_result={
            "prompt_hash": prompt_hash_val,
            "prompt_path": prompt_path,
            "redacted": True,
        },
        output_result={
            "output_hash": output_hash_val,
            "output_path": output_path,
            "quarantined": True,
            "applied_to_repo": False,
        },
        extra={
            "mock_result_status": mock_result.get("status", ""),
            "no_real_backend_invoked": True,
            "no_subprocess": True,
            "no_network": True,
        },
    )
    steps["audit"] = audit_result
    audit_id_val = audit_result.get("audit_id", "")

    # ── Step 5: trust/readiness assessment ────────────────────────────────
    trust_result = assess_backend_invocation_trust(
        request=request,
        readiness=plan_readiness,
        prompt_meta={"prompt_hash": prompt_hash_val, "prompt_path": prompt_path},
        output_meta={"output_hash": output_hash_val, "output_path": output_path,
                     "quarantined": True, "applied_to_repo": False},
        audit_meta=audit_result,
        audit_verified=True,
    )
    steps["trust"] = trust_result
    trust_id = trust_result.get("assessment_id", "")
    if trust_result.get("hard_blocks"):
        hard_blocks.extend(f"trust:{b}" for b in trust_result["hard_blocks"])
    if trust_result.get("missing_evidence"):
        missing_evidence.extend(trust_result["missing_evidence"])

    # ── Step 6: review artifact creation ─────────────────────────────────
    review = create_review_artifact(
        request_id=request.request_id,
        output_hash=output_hash_val,
        backend_id=backend_id,
        phase_id=phase_id,
        task_id=task_id,
        prompt_hash=prompt_hash_val,
        prompt_artifact_path=prompt_path,
        output_artifact_path=output_path,
        audit_id=audit_id_val,
        trust_assessment_id=trust_id,
    )
    persist_review(review)
    steps["review"] = {"review_id": review.review_id, "review_state": review.review_state}

    # ── Step 7: approval (happy path) or rejection (negative path) ────────
    approval = None
    rejection_id = ""
    if forbidden_path_check:
        # Negative path: add a forbidden operation → hard blocks prevent approval
        review.hard_blocks.append("forbidden_path_pattern:.env")
        review.review_state = REVIEW_QUARANTINED
        try:
            approve_review(review, "demo-operator", "attempted approval with hard blocks")
        except ValueError:
            pass  # Expected — hard blocks prevent approval
        rejection = reject_review(review, "demo-operator", "Hard blocks present: forbidden path")
        persist_rejection(rejection, review)
        rejection_id = rejection.rejection_id
        steps["approval"] = {"status": "rejected", "rejection_id": rejection_id,
                             "reason": "forbidden_path_check"}
    else:
        # Happy path: approve
        approval = approve_review(review, "demo-operator", "Mock demo approval — safe")
        persist_approval(approval, review)
        steps["approval"] = {"approval_id": approval.approval_id,
                             "status": "approved"}

    # ── Step 8: apply plan creation ──────────────────────────────────────
    if forbidden_path_check:
        ops_for_plan = [
            ApplyOperation(
                operation_id=f"op-{_uuid.uuid4().hex[:8]}",
                operation_type=OP_CREATE,
                target_path=".env",  # forbidden
                risk_level=RISK_HIGH,
                forbidden=True,
            ),
        ]
    else:
        ops_for_plan = [
            ApplyOperation(
                operation_id=f"op-{_uuid.uuid4().hex[:8]}",
                operation_type=OP_CREATE,
                target_path="docs/demo-output.md",
                risk_level=RISK_LOW,
                allowed_by_task_scope=True,
            ),
        ]

    apply_plan = create_apply_plan(
        review=review,
        approval=approval,
        operations=ops_for_plan,
        allowed_files=["docs/demo-output.md"],
        forbidden_files=[".env"] if forbidden_path_check else [],
    )
    persist_apply_plan(apply_plan)
    steps["apply_plan"] = {
        "apply_plan_id": apply_plan.apply_plan_id,
        "hard_blocks": apply_plan.hard_blocks,
        "apply_ready": apply_plan.apply_ready,
    }
    if apply_plan.hard_blocks:
        hard_blocks.extend(apply_plan.hard_blocks)

    # ── Step 9: apply readiness validation ───────────────────────────────
    readiness_assessment = validate_backend_apply_readiness(
        plan=apply_plan,
        review=review,
        approval=approval,
        output_meta={
            "output_hash": output_hash_val,
            "output_path": output_path,
            "quarantined": True,
            "applied_to_repo": False,
        },
        trust_assessment=trust_result,
    )
    persist_apply_readiness(readiness_assessment)
    steps["apply_readiness"] = {
        "assessment_id": readiness_assessment.assessment_id,
        "status": readiness_assessment.status,
        "apply_ready": readiness_assessment.apply_ready,
        "hard_blocks": readiness_assessment.hard_blocks,
    }
    if readiness_assessment.hard_blocks:
        for hb in readiness_assessment.hard_blocks:
            if hb not in hard_blocks:
                hard_blocks.append(hb)
    if readiness_assessment.missing_evidence:
        for me in readiness_assessment.missing_evidence:
            if me not in missing_evidence:
                missing_evidence.append(me)
    if readiness_assessment.warnings:
        for w in readiness_assessment.warnings:
            if w not in warnings_list:
                warnings_list.append(w)

    # ── Determine lifecycle status ───────────────────────────────────────
    if hard_blocks:
        lifecycle_status = DEMO_BLOCKED
    elif missing_evidence:
        lifecycle_status = DEMO_PARTIAL
    elif warnings_list:
        lifecycle_status = DEMO_COMPLETED
    else:
        lifecycle_status = DEMO_COMPLETED

    # ── Step 10: demo summary artifact ───────────────────────────────────
    demo = BackendLifecycleDemo(
        demo_id=demo_id,
        phase_id=phase_id,
        task_id=task_id,
        backend_id=backend_id,
        request_id=request.request_id,
        prompt_artifact_path=prompt_path,
        prompt_hash=prompt_hash_val,
        output_artifact_path=output_path,
        output_hash=output_hash_val,
        audit_id=audit_id_val,
        trust_assessment_id=trust_id,
        review_id=review.review_id,
        approval_id=approval.approval_id if approval else "",
        rejection_id=rejection_id,
        apply_plan_id=apply_plan.apply_plan_id,
        apply_readiness_assessment_id=readiness_assessment.assessment_id,
        lifecycle_status=lifecycle_status,
        hard_blocks=hard_blocks,
        missing_evidence=missing_evidence,
        warnings=warnings_list,
        no_real_backend_invoked=True,
        no_apply_execution=True,
        no_file_mutation=True,
        no_subprocess=True,
        no_network=True,
        no_shell_interception=True,
        created_at_utc=now,
        **{k: v for k, v in kwargs.items()
           if k in BackendLifecycleDemo.__dataclass_fields__},
    )

    steps["lifecycle_status"] = lifecycle_status
    steps["demo"] = demo.to_dict()

    return demo, steps


def persist_lifecycle_demo(demo: BackendLifecycleDemo) -> dict:
    """Persist a lifecycle demo summary artifact.

    Writes to .pcae/backend-lifecycle-demos/ with timestamped filename
    and updates latest.json pointer.  Never executes apply, never mutates
    source files, never invokes backends.
    """
    import json as _json
    import os
    d = _lifecycle_demos_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{demo.demo_id}.json"
        lp = d / "latest.json"

        fp.write_text(_json.dumps(demo.to_dict(), indent=2, sort_keys=True))

        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(demo.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))

        return {
            "status": "written",
            "path": str(fp),
            "latest_path": str(lp),
            "demo_id": demo.demo_id,
            "lifecycle_status": demo.lifecycle_status,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def read_latest_lifecycle_demo() -> BackendLifecycleDemo | None:
    """Read the latest lifecycle demo. Returns None if absent or malformed."""
    import json as _json
    lp = _lifecycle_demos_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        if not isinstance(data, dict) or not data:
            return None
        return BackendLifecycleDemo.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94S — Real backend adapter contract model
# ═══════════════════════════════════════════════════════════════════════════

_ADAPTER_SCHEMA_VERSION = "1.0"

# ── Backend types for adapters ──────────────────────────────────────────

ADAPTER_BACKEND_MOCK = "mock"
ADAPTER_BACKEND_CLAUDE_CLI = "claude_cli"
ADAPTER_BACKEND_CLAUDE_DEEPSEEK_CLI = "claude_deepseek_cli"
ADAPTER_BACKEND_CODEX = "codex"
ADAPTER_BACKEND_QWEN = "qwen"
ADAPTER_BACKEND_CUSTOM = "custom"

VALID_ADAPTER_BACKEND_TYPES: frozenset[str] = frozenset({
    ADAPTER_BACKEND_MOCK, ADAPTER_BACKEND_CLAUDE_CLI,
    ADAPTER_BACKEND_CLAUDE_DEEPSEEK_CLI, ADAPTER_BACKEND_CODEX,
    ADAPTER_BACKEND_QWEN, ADAPTER_BACKEND_CUSTOM,
})

# ── Adapter invocation modes ────────────────────────────────────────────

ADAPTER_MODE_MOCK_ONLY = "mock_only"
ADAPTER_MODE_PREFLIGHT_ONLY = "preflight_only"
ADAPTER_MODE_ARTIFACT_ONLY = "artifact_only"
ADAPTER_MODE_DISABLED = "disabled"
ADAPTER_MODE_FUTURE_REAL = "future_real"

VALID_ADAPTER_MODES: frozenset[str] = frozenset({
    ADAPTER_MODE_MOCK_ONLY, ADAPTER_MODE_PREFLIGHT_ONLY,
    ADAPTER_MODE_ARTIFACT_ONLY, ADAPTER_MODE_DISABLED,
    ADAPTER_MODE_FUTURE_REAL,
})

REAL_ADAPTER_DEFAULT_MODE = ADAPTER_MODE_PREFLIGHT_ONLY

# ── Preflight statuses ──────────────────────────────────────────────────

PREFLIGHT_READY = "ready"
PREFLIGHT_BLOCKED = "blocked"
PREFLIGHT_MISSING_EVIDENCE = "missing_evidence"
PREFLIGHT_DISABLED = "disabled"
PREFLIGHT_UNSUPPORTED = "unsupported"
PREFLIGHT_NEEDS_HUMAN_REVIEW = "needs_human_review"

VALID_PREFLIGHT_STATUSES: frozenset[str] = frozenset({
    PREFLIGHT_READY, PREFLIGHT_BLOCKED, PREFLIGHT_MISSING_EVIDENCE,
    PREFLIGHT_DISABLED, PREFLIGHT_UNSUPPORTED, PREFLIGHT_NEEDS_HUMAN_REVIEW,
})

# ── Failure categories ──────────────────────────────────────────────────

FAILURE_NOT_INVOKED = "not_invoked"
FAILURE_DISABLED = "disabled"
FAILURE_MISSING_ENV = "missing_env"
FAILURE_BYPASS_PERMISSIONS = "bypass_permissions"
FAILURE_TIMEOUT = "timeout"
FAILURE_BACKEND_UNAVAILABLE = "backend_unavailable"
FAILURE_AUTH_FAILURE = "auth_failure"
FAILURE_RATE_LIMITED = "rate_limited"
FAILURE_OUTPUT_MISSING = "output_missing"
FAILURE_OUTPUT_MALFORMED = "output_malformed"
FAILURE_INTERRUPTED = "interrupted"
FAILURE_UNKNOWN = "unknown"

VALID_FAILURE_CATEGORIES: frozenset[str] = frozenset({
    FAILURE_NOT_INVOKED, FAILURE_DISABLED, FAILURE_MISSING_ENV,
    FAILURE_BYPASS_PERMISSIONS, FAILURE_TIMEOUT, FAILURE_BACKEND_UNAVAILABLE,
    FAILURE_AUTH_FAILURE, FAILURE_RATE_LIMITED, FAILURE_OUTPUT_MISSING,
    FAILURE_OUTPUT_MALFORMED, FAILURE_INTERRUPTED, FAILURE_UNKNOWN,
})


@dataclass
class BackendAdapterSafetyProfile:
    """Safety capability profile for a backend adapter.

    Conservative defaults: all safety requirements enabled.
    No default may imply executable real invocation.
    """

    requires_human_approval: bool = True
    requires_permission_broker: bool = True
    requires_shell_gate: bool = True
    requires_prompt_artifact: bool = True
    requires_output_quarantine: bool = True
    requires_audit: bool = True
    requires_timeout: bool = True
    requires_secret_redaction: bool = True
    requires_bypass_detection: bool = True
    supports_no_apply_guarantee: bool = True
    schema_version: str = _ADAPTER_SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.requires_human_approval:
            issues.append("requires_human_approval must be True for real adapters")
        if not self.requires_output_quarantine:
            issues.append("requires_output_quarantine must be True")
        if not self.requires_secret_redaction:
            issues.append("requires_secret_redaction must be True")
        if not self.supports_no_apply_guarantee:
            issues.append("supports_no_apply_guarantee must be True")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "requires_human_approval": self.requires_human_approval,
            "requires_permission_broker": self.requires_permission_broker,
            "requires_shell_gate": self.requires_shell_gate,
            "requires_prompt_artifact": self.requires_prompt_artifact,
            "requires_output_quarantine": self.requires_output_quarantine,
            "requires_audit": self.requires_audit,
            "requires_timeout": self.requires_timeout,
            "requires_secret_redaction": self.requires_secret_redaction,
            "requires_bypass_detection": self.requires_bypass_detection,
            "supports_no_apply_guarantee": self.supports_no_apply_guarantee,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendAdapterSafetyProfile":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


@dataclass
class BackendAdapterContract:
    """Serializable adapter contract for a backend.

    Describes what a backend adapter supports and requires.
    Real adapters default to preflight-only — no model default
    may imply executable real invocation.
    """

    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ADAPTER_BACKEND_MOCK
    display_name: str = ""
    invocation_mode: str = REAL_ADAPTER_DEFAULT_MODE
    supports_artifact_only: bool = False
    supports_streaming: bool = False
    supports_timeout: bool = False
    supports_session_reuse: bool = False
    requires_secrets: bool = False
    required_env_keys: list[str] = field(default_factory=list)
    safety_capabilities: BackendAdapterSafetyProfile = field(
        default_factory=BackendAdapterSafetyProfile
    )
    schema_version: str = _ADAPTER_SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.adapter_id:
            issues.append("adapter_id is required")
        if not self.backend_id:
            issues.append("backend_id is required")
        if self.backend_type not in VALID_ADAPTER_BACKEND_TYPES:
            issues.append(f"invalid backend_type: {self.backend_type!r}")
        if self.invocation_mode not in VALID_ADAPTER_MODES:
            issues.append(f"invalid invocation_mode: {self.invocation_mode!r}")
        if self.backend_type != ADAPTER_BACKEND_MOCK:
            if self.invocation_mode == ADAPTER_MODE_MOCK_ONLY:
                issues.append(f"real backend {self.backend_type!r} cannot use mock_only mode")
            if self.invocation_mode == ADAPTER_MODE_FUTURE_REAL:
                if not self.supports_timeout:
                    issues.append("future_real mode requires supports_timeout")
                if not self.requires_secrets:
                    issues.append("future_real mode requires requires_secrets")
        safety_issues = self.safety_capabilities.validate()
        for si in safety_issues:
            issues.append(f"safety: {si}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "display_name": self.display_name,
            "invocation_mode": self.invocation_mode,
            "supports_artifact_only": self.supports_artifact_only,
            "supports_streaming": self.supports_streaming,
            "supports_timeout": self.supports_timeout,
            "supports_session_reuse": self.supports_session_reuse,
            "requires_secrets": self.requires_secrets,
            "required_env_keys": list(self.required_env_keys),
            "safety_capabilities": self.safety_capabilities.to_dict(),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendAdapterContract":
        safety_data = data.get("safety_capabilities", {})
        safety = BackendAdapterSafetyProfile.from_dict(
            safety_data if isinstance(safety_data, dict) else {}
        )
        kwargs = {k: v for k, v in data.items()
                  if k in cls.__dataclass_fields__ and k != "safety_capabilities"}
        kwargs["safety_capabilities"] = safety
        return cls(**kwargs)


@dataclass
class BackendAdapterPreflightResult:
    """Result of adapter preflight validation.

    Reports environment readiness, safety conditions, and blocking issues.
    Never prints secret values. Never invokes real backends.
    Always fail-closed on uncertainty.
    """

    preflight_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ADAPTER_BACKEND_MOCK
    status: str = PREFLIGHT_BLOCKED
    ready: bool = False
    missing_env_keys: list[str] = field(default_factory=list)
    present_env_keys_redacted: list[str] = field(default_factory=list)
    unsafe_conditions: list[str] = field(default_factory=list)
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
    requires_broker: bool = True
    requires_shell_gate: bool = True
    bypass_permissions_detected: bool = False
    secrets_redacted: bool = True
    no_real_backend_invoked: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    created_at_utc: str = ""
    schema_version: str = _ADAPTER_SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.preflight_id:
            issues.append("preflight_id is required")
        if self.status not in VALID_PREFLIGHT_STATUSES:
            issues.append(f"invalid status: {self.status!r}")
        if self.bypass_permissions_detected:
            issues.append("bypass_permissions_detected: invocation not safe")
        if not self.secrets_redacted:
            issues.append("secrets_redacted must be True")
        if not self.no_real_backend_invoked:
            issues.append("no_real_backend_invoked must be True")
        if not self.no_subprocess:
            issues.append("no_subprocess must be True")
        if not self.no_network:
            issues.append("no_network must be True")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "preflight_id": self.preflight_id,
            "adapter_id": self.adapter_id,
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "status": self.status,
            "ready": self.ready,
            "missing_env_keys": list(self.missing_env_keys),
            "present_env_keys_redacted": list(self.present_env_keys_redacted),
            "unsafe_conditions": list(self.unsafe_conditions),
            "hard_blocks": list(self.hard_blocks),
            "warnings": list(self.warnings),
            "requires_human_approval": self.requires_human_approval,
            "requires_broker": self.requires_broker,
            "requires_shell_gate": self.requires_shell_gate,
            "bypass_permissions_detected": self.bypass_permissions_detected,
            "secrets_redacted": self.secrets_redacted,
            "no_real_backend_invoked": self.no_real_backend_invoked,
            "no_subprocess": self.no_subprocess,
            "no_network": self.no_network,
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendAdapterPreflightResult":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


@dataclass
class BackendAdapterInvocationPlan:
    """Future-only invocation plan artifact.

    Describes what WOULD be invoked. Never executes anything.
    executable=False is the hard default.
    """

    invocation_plan_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    request_id: str = ""
    phase_id: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    invocation_mode: str = REAL_ADAPTER_DEFAULT_MODE
    requires_human_approval: bool = True
    requires_broker_decision: bool = True
    requires_shell_gate_preflight: bool = True
    timeout_seconds: int = 120
    output_capture_required: bool = True
    audit_required: bool = True
    quarantine_required: bool = True
    hard_blocks: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    executable: bool = False
    schema_version: str = _ADAPTER_SCHEMA_VERSION

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.invocation_plan_id:
            issues.append("invocation_plan_id is required")
        if self.executable:
            issues.append("executable must be False in this phase")
        if self.invocation_mode not in VALID_ADAPTER_MODES:
            issues.append(f"invalid invocation_mode: {self.invocation_mode!r}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "invocation_plan_id": self.invocation_plan_id,
            "adapter_id": self.adapter_id,
            "backend_id": self.backend_id,
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "invocation_mode": self.invocation_mode,
            "requires_human_approval": self.requires_human_approval,
            "requires_broker_decision": self.requires_broker_decision,
            "requires_shell_gate_preflight": self.requires_shell_gate_preflight,
            "timeout_seconds": self.timeout_seconds,
            "output_capture_required": self.output_capture_required,
            "audit_required": self.audit_required,
            "quarantine_required": self.quarantine_required,
            "hard_blocks": list(self.hard_blocks),
            "missing_evidence": list(self.missing_evidence),
            "warnings": list(self.warnings),
            "executable": self.executable,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackendAdapterInvocationPlan":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


# ── Validation helpers ──────────────────────────────────────────────────


def validate_backend_adapter_contract(contract: BackendAdapterContract) -> dict[str, Any]:
    """Validate a backend adapter contract. Pure model validation.

    Returns dict with valid, hard_blocks, warnings.
    Never executes, never invokes backends.
    """
    issues = contract.validate()
    hard_blocks: list[str] = []
    warnings_list: list[str] = []

    if contract.backend_type not in VALID_ADAPTER_BACKEND_TYPES:
        hard_blocks.append(f"unknown_backend_type:{contract.backend_type}")
    if contract.invocation_mode not in VALID_ADAPTER_MODES:
        hard_blocks.append(f"unsupported_invocation_mode:{contract.invocation_mode}")
    if contract.backend_type != ADAPTER_BACKEND_MOCK:
        if contract.invocation_mode == ADAPTER_MODE_MOCK_ONLY:
            hard_blocks.append("real_backend_cannot_use_mock_only")
        if contract.invocation_mode == ADAPTER_MODE_FUTURE_REAL:
            if not contract.supports_timeout:
                hard_blocks.append("future_real_requires_timeout")
            if not contract.supports_artifact_only:
                warnings_list.append("future_real_adapter_without_artifact_only")

    # ── Phase 94W: safety capability hard-blocks for real adapters ──────
    if contract.backend_type != ADAPTER_BACKEND_MOCK:
        sp = contract.safety_capabilities
        if not sp.requires_human_approval:
            hard_blocks.append("real_adapter_requires_human_approval")
        if not sp.requires_audit:
            hard_blocks.append("real_adapter_requires_audit")
        if not sp.requires_timeout:
            hard_blocks.append("real_adapter_requires_timeout")
        if not sp.requires_secret_redaction and contract.requires_secrets:
            hard_blocks.append("real_adapter_with_secrets_requires_redaction")
        if not sp.requires_output_quarantine:
            hard_blocks.append("real_adapter_requires_output_quarantine")
        if not sp.supports_no_apply_guarantee:
            hard_blocks.append("real_adapter_requires_no_apply_guarantee")

    # ── Phase 94W: duplicate env key detection ──────────────────────────
    seen_keys: set[str] = set()
    for k in contract.required_env_keys:
        if k in seen_keys:
            warnings_list.append(f"duplicate_env_key:{k}")
        seen_keys.add(k)

    for i in issues:
        # Safety profile requirements are relaxed for mock adapters
        is_safety_issue = "safety:" in i
        if is_safety_issue and contract.backend_type == ADAPTER_BACKEND_MOCK:
            continue  # mock adapters may have relaxed safety defaults
        if any(x in i.lower() for x in ("must be true", "required", "cannot use", "requires_")):
            hard_blocks.append(i)
        else:
            warnings_list.append(i)

    return {
        "valid": len(hard_blocks) == 0,
        "hard_blocks": hard_blocks,
        "warnings": warnings_list,
    }


def validate_backend_adapter_preflight(
    contract: BackendAdapterContract,
    *,
    env_available: dict[str, bool] | None = None,
    bypass_detected: bool = False,
) -> BackendAdapterPreflightResult:
    """Run adapter preflight validation. Pure model — no subprocess, no network.

    Checks environment requirements, safety profile, and mode constraints.
    Never prints secret values. Reports presence/absence only.
    Always fail-closed.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    preflight_id = f"apf-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    missing_env: list[str] = []
    present_env: list[str] = []
    unsafe: list[str] = []

    # ── Backend type validation ────────────────────────────────────────
    if contract.backend_type not in VALID_ADAPTER_BACKEND_TYPES:
        return BackendAdapterPreflightResult(
            preflight_id=preflight_id,
            adapter_id=contract.adapter_id,
            backend_id=contract.backend_id,
            backend_type=contract.backend_type,
            status=PREFLIGHT_BLOCKED,
            ready=False,
            hard_blocks=[f"unknown_backend_type:{contract.backend_type}"],
            unsafe_conditions=[f"unknown_backend_type:{contract.backend_type}"],
            requires_human_approval=contract.safety_capabilities.requires_human_approval,
            requires_broker=contract.safety_capabilities.requires_permission_broker,
            requires_shell_gate=contract.safety_capabilities.requires_shell_gate,
            no_real_backend_invoked=True,
            no_subprocess=True,
            no_network=True,
            created_at_utc=now,
        )

    # ── Mode validation ────────────────────────────────────────────────
    mode = contract.invocation_mode
    if mode not in VALID_ADAPTER_MODES:
        hard_blocks.append(f"unsupported_invocation_mode:{mode}")
        unsafe.append(f"unsupported_invocation_mode:{mode}")

    if mode == ADAPTER_MODE_DISABLED:
        return BackendAdapterPreflightResult(
            preflight_id=preflight_id,
            adapter_id=contract.adapter_id,
            backend_id=contract.backend_id,
            backend_type=contract.backend_type,
            status=PREFLIGHT_DISABLED,
            ready=False,
            hard_blocks=hard_blocks,
            unsafe_conditions=unsafe,
            requires_human_approval=contract.safety_capabilities.requires_human_approval,
            requires_broker=contract.safety_capabilities.requires_permission_broker,
            requires_shell_gate=contract.safety_capabilities.requires_shell_gate,
            no_real_backend_invoked=True,
            no_subprocess=True,
            no_network=True,
            created_at_utc=now,
        )

    if contract.backend_type != ADAPTER_BACKEND_MOCK and mode == ADAPTER_MODE_MOCK_ONLY:
        hard_blocks.append("real_backend_cannot_use_mock_only")
        unsafe.append("real_backend_cannot_use_mock_only")

    # ── Bypass permissions detection ───────────────────────────────────
    if bypass_detected:
        hard_blocks.append("bypass_permissions_detected")
        unsafe.append("bypass_permissions_detected")

    # ── Environment validation ─────────────────────────────────────────
    if env_available is not None:
        for key_name, is_present in sorted(env_available.items()):
            if is_present:
                present_env.append(key_name)
            else:
                missing_env.append(key_name)

    required = list(contract.required_env_keys)
    if required:
        for rk in required:
            if rk not in present_env and rk not in missing_env:
                env_val = _os.environ.get(rk, "")
                if env_val:
                    present_env.append(rk)
                else:
                    missing_env.append(rk)

    if missing_env:
        hard_blocks.append("missing_required_env")
        unsafe.append(f"missing_env:{','.join(sorted(missing_env))}")

    # ── Determine status ───────────────────────────────────────────────
    if hard_blocks:
        status = PREFLIGHT_BLOCKED
        ready = False
    elif missing_env:
        status = PREFLIGHT_MISSING_EVIDENCE
        ready = False
    elif unsafe:
        status = PREFLIGHT_NEEDS_HUMAN_REVIEW
        ready = False
    elif mode in (ADAPTER_MODE_MOCK_ONLY, ADAPTER_MODE_PREFLIGHT_ONLY, ADAPTER_MODE_ARTIFACT_ONLY):
        status = PREFLIGHT_READY
        ready = True
    else:
        status = PREFLIGHT_READY
        ready = True

    return BackendAdapterPreflightResult(
        preflight_id=preflight_id,
        adapter_id=contract.adapter_id,
        backend_id=contract.backend_id,
        backend_type=contract.backend_type,
        status=status,
        ready=ready,
        missing_env_keys=sorted(set(missing_env)),
        present_env_keys_redacted=sorted(set(present_env)),
        unsafe_conditions=sorted(set(unsafe)),
        hard_blocks=hard_blocks,
        warnings=warnings_list,
        requires_human_approval=contract.safety_capabilities.requires_human_approval,
        requires_broker=contract.safety_capabilities.requires_permission_broker,
        requires_shell_gate=contract.safety_capabilities.requires_shell_gate,
        bypass_permissions_detected=bypass_detected,
        secrets_redacted=True,
        no_real_backend_invoked=True,
        no_subprocess=True,
        no_network=True,
        created_at_utc=now,
    )


def create_backend_adapter_invocation_plan(
    contract: BackendAdapterContract,
    *,
    request_id: str = "",
    phase_id: str = "",
    prompt_hash: str = "",
    prompt_artifact_path: str = "",
    **kwargs: Any,
) -> BackendAdapterInvocationPlan:
    """Create a future-only invocation plan. Never executes anything.

    executable=False is the hard default.
    """
    import uuid as _uuid
    plan_id = f"aip-{_uuid.uuid4().hex[:12]}"

    plan = BackendAdapterInvocationPlan(
        invocation_plan_id=plan_id,
        adapter_id=contract.adapter_id,
        backend_id=contract.backend_id,
        request_id=request_id,
        phase_id=phase_id,
        prompt_hash=prompt_hash,
        prompt_artifact_path=prompt_artifact_path,
        invocation_mode=contract.invocation_mode,
        requires_human_approval=contract.safety_capabilities.requires_human_approval,
        requires_broker_decision=contract.safety_capabilities.requires_permission_broker,
        requires_shell_gate_preflight=contract.safety_capabilities.requires_shell_gate,
        timeout_seconds=120 if contract.supports_timeout else 0,
        output_capture_required=contract.supports_artifact_only,
        audit_required=contract.safety_capabilities.requires_audit,
        quarantine_required=contract.safety_capabilities.requires_output_quarantine,
        executable=False,
        **{k: v for k, v in kwargs.items()
           if k in BackendAdapterInvocationPlan.__dataclass_fields__},
    )
    issues = plan.validate()
    if issues:
        raise ValueError(f"Invalid invocation plan: {'; '.join(issues)}")
    return plan


def classify_backend_adapter_failure(
    *,
    preflight: BackendAdapterPreflightResult | None = None,
    timeout_occurred: bool = False,
    exit_code: int = 0,
    output_present: bool = True,
    output_valid: bool = True,
    backend_responded: bool = True,
) -> str:
    """Classify a backend adapter failure into standard categories.

    Pure classification — no execution, no subprocess, no network.
    """
    # Preflight-level failures
    if preflight is not None:
        if preflight.status == PREFLIGHT_DISABLED:
            return FAILURE_DISABLED
        if preflight.bypass_permissions_detected:
            return FAILURE_BYPASS_PERMISSIONS
        if preflight.missing_env_keys:
            return FAILURE_MISSING_ENV

    # Runtime-level failures
    if timeout_occurred:
        return FAILURE_TIMEOUT
    if not backend_responded:
        return FAILURE_BACKEND_UNAVAILABLE
    if exit_code != 0:
        if exit_code in (401, 403):
            return FAILURE_AUTH_FAILURE
        if exit_code == 429:
            return FAILURE_RATE_LIMITED
        return FAILURE_UNKNOWN

    # Output-level failures (only checked when backend responded and exit was clean)
    if not output_present and not output_valid:
        return FAILURE_OUTPUT_MISSING
    if not output_present:
        return FAILURE_OUTPUT_MISSING
    if not output_valid:
        return FAILURE_OUTPUT_MALFORMED

    return FAILURE_NOT_INVOKED


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94V — Adapter-specific contract factories
# ═══════════════════════════════════════════════════════════════════════════


def _build_no_go_conditions(
    *,
    backend_type: str,
    requires_env: bool,
    requires_bypass: bool,
) -> list[str]:
    """Build a backend-specific no-go condition list."""
    conditions: list[str] = [
        "unknown_adapter",
        "unsupported_invocation_mode",
        "broker_hard_block",
        "shell_gate_deny",
        "human_approval_missing",
        "prompt_artifact_missing",
        "output_capture_unavailable",
        "audit_path_unavailable",
    ]
    if requires_env:
        conditions.append("required_env_missing")
    if requires_bypass:
        conditions.append("bypass_permissions_detected")
    if backend_type != ADAPTER_BACKEND_MOCK:
        conditions.extend([
            "timeout_missing",
            "real_backend_unsafe_mode",
        ])
    return sorted(set(conditions))


def _build_failure_mapping() -> dict[str, str]:
    """Build a standard failure-to-category mapping."""
    return {
        "disabled": FAILURE_DISABLED,
        "missing_env": FAILURE_MISSING_ENV,
        "bypass_permissions": FAILURE_BYPASS_PERMISSIONS,
        "timeout": FAILURE_TIMEOUT,
        "backend_unavailable": FAILURE_BACKEND_UNAVAILABLE,
        "auth_failure": FAILURE_AUTH_FAILURE,
        "rate_limited": FAILURE_RATE_LIMITED,
        "output_missing": FAILURE_OUTPUT_MISSING,
        "output_malformed": FAILURE_OUTPUT_MALFORMED,
        "interrupted": FAILURE_INTERRUPTED,
        "unknown": FAILURE_UNKNOWN,
        "not_invoked": FAILURE_NOT_INVOKED,
    }


def create_mock_adapter_contract() -> BackendAdapterContract:
    """Mock backend adapter — safe, no secrets, mock_only."""
    return BackendAdapterContract(
        adapter_id="adapter-mock",
        backend_id="mock",
        backend_type=ADAPTER_BACKEND_MOCK,
        display_name="Mock Backend Adapter",
        invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        supports_artifact_only=True,
        supports_timeout=False,
        requires_secrets=False,
        required_env_keys=[],
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=False,
            requires_permission_broker=False,
            requires_shell_gate=False,
            requires_bypass_detection=False,
        ),
    )


def create_claude_cli_adapter_contract() -> BackendAdapterContract:
    """Claude CLI adapter — preflight_only, bypass detection, env required."""
    return BackendAdapterContract(
        adapter_id="adapter-claude-cli",
        backend_id="claude",
        backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
        display_name="Claude CLI Adapter",
        invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
        supports_artifact_only=True,
        supports_timeout=True,
        requires_secrets=True,
        required_env_keys=["ANTHROPIC_API_KEY"],
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=True,
            requires_permission_broker=True,
            requires_shell_gate=True,
            requires_bypass_detection=True,
            requires_timeout=True,
            requires_secret_redaction=True,
            requires_audit=True,
            requires_output_quarantine=True,
        ),
    )


def create_claude_deepseek_cli_adapter_contract() -> BackendAdapterContract:
    """Claude-DeepSeek CLI adapter — preflight_only, bypass detection."""
    return BackendAdapterContract(
        adapter_id="adapter-claude-deepseek-cli",
        backend_id="claude-deepseek",
        backend_type=ADAPTER_BACKEND_CLAUDE_DEEPSEEK_CLI,
        display_name="Claude-DeepSeek CLI Adapter",
        invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
        supports_artifact_only=True,
        supports_timeout=True,
        requires_secrets=True,
        required_env_keys=["DEEPSEEK_API_KEY"],
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=True,
            requires_permission_broker=True,
            requires_shell_gate=True,
            requires_bypass_detection=True,
            requires_timeout=True,
            requires_secret_redaction=True,
            requires_audit=True,
            requires_output_quarantine=True,
        ),
    )


def create_codex_adapter_contract() -> BackendAdapterContract:
    """Codex adapter — preflight_only, env declaration, non-executable."""
    return BackendAdapterContract(
        adapter_id="adapter-codex",
        backend_id="codex",
        backend_type=ADAPTER_BACKEND_CODEX,
        display_name="Codex Adapter",
        invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
        supports_artifact_only=False,
        supports_timeout=True,
        requires_secrets=True,
        required_env_keys=["OPENAI_API_KEY"],
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=True,
            requires_permission_broker=True,
            requires_shell_gate=True,
            requires_bypass_detection=False,
            requires_timeout=True,
            requires_audit=True,
            requires_secret_redaction=True,
            requires_output_quarantine=True,
        ),
    )


def create_qwen_adapter_contract() -> BackendAdapterContract:
    """Qwen adapter — preflight_only, env declaration, non-executable."""
    return BackendAdapterContract(
        adapter_id="adapter-qwen",
        backend_id="qwen",
        backend_type=ADAPTER_BACKEND_QWEN,
        display_name="Qwen Adapter",
        invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
        supports_artifact_only=False,
        supports_timeout=True,
        requires_secrets=True,
        required_env_keys=["QWEN_API_KEY"],
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=True,
            requires_permission_broker=True,
            requires_shell_gate=True,
            requires_bypass_detection=False,
            requires_timeout=True,
            requires_audit=True,
            requires_secret_redaction=True,
            requires_output_quarantine=True,
        ),
    )


def create_custom_adapter_contract(
    *,
    backend_id: str = "custom",
    display_name: str = "Custom Adapter",
    required_env_keys: list[str] | None = None,
) -> BackendAdapterContract:
    """Custom adapter — disabled by default, requires explicit configuration."""
    return BackendAdapterContract(
        adapter_id=f"adapter-{backend_id}",
        backend_id=backend_id,
        backend_type=ADAPTER_BACKEND_CUSTOM,
        display_name=display_name,
        invocation_mode=ADAPTER_MODE_DISABLED,
        supports_artifact_only=False,
        supports_timeout=False,
        requires_secrets=bool(required_env_keys),
        required_env_keys=list(required_env_keys or []),
        safety_capabilities=BackendAdapterSafetyProfile(
            requires_human_approval=True,
            requires_permission_broker=True,
            requires_shell_gate=True,
            requires_bypass_detection=True,
            requires_timeout=True,
            requires_audit=True,
            requires_secret_redaction=True,
            requires_output_quarantine=True,
        ),
    )


def get_adapter_no_go_conditions(contract: BackendAdapterContract) -> list[str]:
    """Return the backend-specific no-go condition list for a contract."""
    return _build_no_go_conditions(
        backend_type=contract.backend_type,
        requires_env=bool(contract.required_env_keys),
        requires_bypass=contract.safety_capabilities.requires_bypass_detection,
    )


def get_adapter_failure_mapping(
    contract: BackendAdapterContract,  # noqa: ARG001 — reserved for future use
) -> dict[str, str]:
    """Return the standard failure classification mapping."""
    return _build_failure_mapping()


def get_default_adapter_registry() -> dict[str, BackendAdapterContract]:
    """Build the default adapter registry using specialized factories.

    All real adapters default to preflight-only or disabled.
    Only mock adapter is mock_only.
    """
    return {
        "mock": create_mock_adapter_contract(),
        "claude": create_claude_cli_adapter_contract(),
        "claude-deepseek": create_claude_deepseek_cli_adapter_contract(),
        "codex": create_codex_adapter_contract(),
        "qwen": create_qwen_adapter_contract(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94U — Backend adapter preflight artifacts
# ═══════════════════════════════════════════════════════════════════════════

_ADAPTER_PREFLIGHTS_DIR = ".pcae/backend-adapter-preflights"
_ADAPTER_PREFLIGHT_SCHEMA_VERSION = "1.0"


@dataclass
class BackendAdapterPreflightArtifact:
    """Persistent, redacted, verifiable preflight artifact.

    Embeds the preflight result with a deterministic digest for
    tamper-evident verification. Never contains secret values.
    """

    artifact_id: str = ""
    preflight_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    invocation_mode: str = ""
    status: str = ""
    ready: bool = False
    missing_env_keys: list[str] = field(default_factory=list)
    present_env_keys_redacted: list[str] = field(default_factory=list)
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsafe_conditions: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
    requires_broker: bool = True
    requires_shell_gate: bool = True
    no_real_backend_invoked: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    secrets_redacted: bool = True
    created_at_utc: str = ""
    source_command: str = ""
    record_digest: str = ""
    schema_version: str = _ADAPTER_PREFLIGHT_SCHEMA_VERSION

    @classmethod
    def from_preflight_result(
        cls,
        result: BackendAdapterPreflightResult,
        *,
        source_command: str = "",
    ) -> "BackendAdapterPreflightArtifact":
        import uuid as _uuid
        return cls(
            artifact_id=f"pfa-{_uuid.uuid4().hex[:12]}",
            preflight_id=result.preflight_id,
            adapter_id=result.adapter_id,
            backend_id=result.backend_id,
            backend_type=result.backend_type,
            status=result.status,
            ready=result.ready,
            missing_env_keys=list(result.missing_env_keys),
            present_env_keys_redacted=list(result.present_env_keys_redacted),
            hard_blocks=list(result.hard_blocks),
            warnings=list(result.warnings),
            unsafe_conditions=list(result.unsafe_conditions),
            requires_human_approval=result.requires_human_approval,
            requires_broker=result.requires_broker,
            requires_shell_gate=result.requires_shell_gate,
            no_real_backend_invoked=result.no_real_backend_invoked,
            no_subprocess=result.no_subprocess,
            no_network=result.no_network,
            secrets_redacted=result.secrets_redacted,
            created_at_utc=result.created_at_utc,
            source_command=source_command,
        )

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "preflight_id": self.preflight_id,
            "adapter_id": self.adapter_id,
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "invocation_mode": self.invocation_mode,
            "status": self.status,
            "ready": self.ready,
            "missing_env_keys": list(self.missing_env_keys),
            "present_env_keys_redacted": list(self.present_env_keys_redacted),
            "hard_blocks": list(self.hard_blocks),
            "warnings": list(self.warnings),
            "unsafe_conditions": list(self.unsafe_conditions),
            "requires_human_approval": self.requires_human_approval,
            "requires_broker": self.requires_broker,
            "requires_shell_gate": self.requires_shell_gate,
            "no_real_backend_invoked": self.no_real_backend_invoked,
            "no_subprocess": self.no_subprocess,
            "no_network": self.no_network,
            "secrets_redacted": self.secrets_redacted,
            "created_at_utc": self.created_at_utc,
            "source_command": self.source_command,
            "schema_version": self.schema_version,
        }
        if include_digest and self.record_digest:
            d["record_digest"] = self.record_digest
        return d

    def compute_digest(self) -> str:
        """Compute deterministic SHA-256 digest over sorted JSON fields.

        Excludes record_digest itself from the hash input.
        """
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "BackendAdapterPreflightArtifact":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


def _adapter_preflights_dir() -> Path:
    from pathlib import Path as _P
    return _P(_ADAPTER_PREFLIGHTS_DIR)


def persist_backend_adapter_preflight_artifact(
    artifact: BackendAdapterPreflightArtifact,
) -> dict:
    """Persist a preflight artifact with digest.

    Writes timestamped JSON, updates latest.json atomically.
    Never executes backends, never mutates source files.
    """
    import os
    d = _adapter_preflights_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    # Compute digest if not set
    if not artifact.record_digest:
        artifact.record_digest = artifact.compute_digest()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{artifact.backend_id}-{artifact.preflight_id}.json"
        lp = d / "latest.json"

        fp.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))

        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(artifact.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))

        return {
            "status": "written",
            "path": str(fp),
            "latest_path": str(lp),
            "artifact_id": artifact.artifact_id,
            "record_digest": artifact.record_digest,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_backend_adapter_preflight_artifact(
    artifact: BackendAdapterPreflightArtifact,
) -> dict:
    """Verify a preflight artifact's integrity.

    Checks: digest, required IDs, schema version, safety invariants.
    Fail-closed: any issue → valid=False.
    """
    issues: list[str] = []

    if not artifact.artifact_id:
        issues.append("missing artifact_id")
    if not artifact.preflight_id:
        issues.append("missing preflight_id")
    if not artifact.backend_id:
        issues.append("missing backend_id")
    if not artifact.record_digest:
        issues.append("missing record_digest")
    if artifact.schema_version != _ADAPTER_PREFLIGHT_SCHEMA_VERSION:
        issues.append(f"schema_version mismatch: {artifact.schema_version!r}")
    if not artifact.no_real_backend_invoked:
        issues.append("no_real_backend_invoked must be True")
    if not artifact.no_subprocess:
        issues.append("no_subprocess must be True")
    if not artifact.no_network:
        issues.append("no_network must be True")
    if not artifact.secrets_redacted:
        issues.append("secrets_redacted must be True")
    # ── Phase 94W: additional integrity checks ──────────────────────────
    if not artifact.adapter_id:
        issues.append("missing adapter_id")
    if not artifact.backend_type:
        issues.append("missing backend_type")
    if artifact.status not in VALID_PREFLIGHT_STATUSES and artifact.status:
        issues.append(f"unknown preflight status: {artifact.status!r}")
    if artifact.ready and artifact.hard_blocks:
        issues.append("ready=True with hard_blocks present")
    if artifact.invocation_mode == ADAPTER_MODE_FUTURE_REAL:
        issues.append("future_real mode not permitted in artifacts")
    if artifact.backend_id and artifact.adapter_id:
        # adapter_id should contain the backend_id for consistency
        pass  # informational, not a hard block

    if artifact.record_digest:
        computed = artifact.compute_digest()
        if computed != artifact.record_digest:
            issues.append("record_digest mismatch")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "artifact_id": artifact.artifact_id,
    }


def load_latest_backend_adapter_preflight_artifact() -> (
    "BackendAdapterPreflightArtifact | None"
):
    """Load the latest preflight artifact. Returns None if absent/malformed."""
    lp = _adapter_preflights_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        if not isinstance(data, dict) or not data:
            return None
        return BackendAdapterPreflightArtifact.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Y — Real adapter invocation approval model
# ═══════════════════════════════════════════════════════════════════════════

_REAL_ADAPTER_APPROVALS_DIR = ".pcae/real-adapter-approvals"
_APPROVAL_SCHEMA_VERSION = "1.0"

# ── Decision constants ──────────────────────────────────────────────────

APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_EXPIRED = "expired"
APPROVAL_REVOKED = "revoked"

VALID_APPROVAL_DECISIONS: frozenset[str] = frozenset({
    APPROVAL_APPROVED, APPROVAL_REJECTED,
    APPROVAL_EXPIRED, APPROVAL_REVOKED,
})


@dataclass
class RealAdapterInvocationApproval:
    """Human approval for a real backend adapter invocation.

    Binds to exact adapter, backend, request, prompt, preflight artifact,
    invocation mode, risk level, and operator. Hard blocks make approval
    ineffective. Does NOT authorize apply, commit, or push.
    """

    approval_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    preflight_artifact_id: str = ""
    preflight_artifact_path: str = ""
    preflight_digest: str = ""
    invocation_mode: str = ""
    risk_level: str = RISK_MEDIUM
    operator: str = ""
    decision: str = ""
    decision_reason: str = ""
    approved_at_utc: str = ""
    expires_at_utc: str = ""
    hard_blocks_present: bool = False
    accepted_risk: bool = False
    approval_effective: bool = False
    schema_version: str = _APPROVAL_SCHEMA_VERSION
    record_digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.approval_id:
            issues.append("approval_id is required")
        if not self.operator:
            issues.append("operator is required")
        if not self.decision_reason:
            issues.append("decision_reason is required")
        if self.decision and self.decision not in VALID_APPROVAL_DECISIONS:
            issues.append(f"invalid decision: {self.decision!r}")
        if self.hard_blocks_present and self.approval_effective:
            issues.append("approval_effective must be False when hard_blocks_present")
        if self.decision == APPROVAL_APPROVED and self.hard_blocks_present:
            issues.append("cannot approve with hard blocks present")
        if self.accepted_risk and self.hard_blocks_present:
            issues.append("accepted_risk cannot override hard blocks")
        return issues

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "approval_id": self.approval_id,
            "adapter_id": self.adapter_id,
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "request_id": self.request_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "preflight_artifact_id": self.preflight_artifact_id,
            "preflight_artifact_path": self.preflight_artifact_path,
            "preflight_digest": self.preflight_digest,
            "invocation_mode": self.invocation_mode,
            "risk_level": self.risk_level,
            "operator": self.operator,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "approved_at_utc": self.approved_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "hard_blocks_present": self.hard_blocks_present,
            "accepted_risk": self.accepted_risk,
            "approval_effective": self.approval_effective,
            "schema_version": self.schema_version,
        }
        if include_digest and self.record_digest:
            d["record_digest"] = self.record_digest
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "RealAdapterInvocationApproval":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


def _real_adapter_approvals_dir() -> Path:
    from pathlib import Path as _P
    return _P(_REAL_ADAPTER_APPROVALS_DIR)


def create_real_adapter_invocation_approval(
    *,
    adapter_id: str,
    backend_id: str,
    backend_type: str,
    request_id: str = "",
    prompt_hash: str = "",
    prompt_artifact_path: str = "",
    preflight_artifact: BackendAdapterPreflightArtifact | None = None,
    invocation_mode: str = "",
    risk_level: str = RISK_MEDIUM,
    operator: str = "",
    decision: str = "",
    decision_reason: str = "",
    expires_at_utc: str = "",
    accepted_risk: bool = False,
    **kwargs: Any,
) -> "RealAdapterInvocationApproval":
    """Create a real adapter invocation approval with binding.

    Binds to the exact preflight artifact digest if provided.
    Hard blocks from preflight make approval ineffective.
    Never authorizes apply, commit, or push.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    approval_id = f"raa-{_uuid.uuid4().hex[:12]}"

    preflight_id = ""
    preflight_path = ""
    preflight_dig = ""
    hard_blocks: list[str] = []
    missing: list[str] = []
    approval_eff = False

    if preflight_artifact is not None:
        preflight_id = preflight_artifact.artifact_id
        preflight_dig = preflight_artifact.record_digest or preflight_artifact.compute_digest()
        hard_blocks = list(preflight_artifact.hard_blocks)
        # Preflight safety invariants must hold
        if not preflight_artifact.no_real_backend_invoked:
            hard_blocks.append("preflight:no_real_backend_invoked=False")
        if not preflight_artifact.no_subprocess:
            hard_blocks.append("preflight:no_subprocess=False")
        if not preflight_artifact.no_network:
            hard_blocks.append("preflight:no_network=False")
        if not preflight_artifact.secrets_redacted:
            hard_blocks.append("preflight:secrets_redacted=False")
    else:
        missing.append("preflight_artifact")

    if not prompt_hash:
        missing.append("prompt_hash")
    if not operator:
        missing.append("operator")
    if not decision_reason:
        missing.append("decision_reason")

    hard_blocks_present = len(hard_blocks) > 0

    # Determine approval_effective
    if decision == APPROVAL_APPROVED and not hard_blocks_present and not missing and not accepted_risk:
        approval_eff = True
    elif decision == APPROVAL_APPROVED and hard_blocks_present:
        approval_eff = False  # hard blocks dominate

    approval = RealAdapterInvocationApproval(
        approval_id=approval_id,
        adapter_id=adapter_id,
        backend_id=backend_id,
        backend_type=backend_type,
        request_id=request_id,
        prompt_hash=prompt_hash,
        prompt_artifact_path=prompt_artifact_path,
        preflight_artifact_id=preflight_id,
        preflight_digest=preflight_dig,
        invocation_mode=invocation_mode,
        risk_level=risk_level,
        operator=operator,
        decision=decision,
        decision_reason=decision_reason,
        approved_at_utc=now,
        expires_at_utc=expires_at_utc,
        hard_blocks_present=hard_blocks_present,
        accepted_risk=accepted_risk,
        approval_effective=approval_eff,
        **{k: v for k, v in kwargs.items()
           if k in RealAdapterInvocationApproval.__dataclass_fields__},
    )
    issues = approval.validate()
    if issues:
        raise ValueError(f"Invalid approval: {'; '.join(issues)}")
    return approval


def validate_real_adapter_invocation_approval(
    approval: RealAdapterInvocationApproval,
    *,
    preflight_artifact: BackendAdapterPreflightArtifact | None = None,
    contract: BackendAdapterContract | None = None,
) -> dict[str, Any]:
    """Validate an approval against binding evidence. Fail-closed."""
    hard_blocks: list[str] = []
    missing: list[str] = []
    warnings_list: list[str] = []

    issues = approval.validate()
    for i in issues:
        if "cannot" in i.lower() or "must" in i.lower():
            hard_blocks.append(i)
        else:
            missing.append(i)

    if not approval.prompt_hash:
        hard_blocks.append("prompt_hash_missing")
    if not approval.preflight_digest:
        hard_blocks.append("preflight_digest_missing")
    if approval.decision != APPROVAL_APPROVED:
        hard_blocks.append(f"decision_not_approved:{approval.decision}")

    # Check preflight artifact binding
    if preflight_artifact is not None:
        pf_digest = preflight_artifact.record_digest or preflight_artifact.compute_digest()
        if approval.preflight_digest and approval.preflight_digest != pf_digest:
            hard_blocks.append("preflight_digest_mismatch")
        if approval.preflight_artifact_id and approval.preflight_artifact_id != preflight_artifact.artifact_id:
            hard_blocks.append("preflight_artifact_id_mismatch")
        if approval.backend_id and approval.backend_id != preflight_artifact.backend_id:
            hard_blocks.append("backend_id_mismatch")

    # Check adapter contract binding
    if contract is not None:
        if approval.adapter_id and approval.adapter_id != contract.adapter_id:
            hard_blocks.append("adapter_id_mismatch")
        if approval.backend_id and approval.backend_id != contract.backend_id:
            hard_blocks.append("backend_contract_mismatch")
        if approval.invocation_mode and approval.invocation_mode != contract.invocation_mode:
            warnings_list.append("invocation_mode_mismatch")

    # Hard blocks dominate
    if approval.hard_blocks_present:
        hard_blocks.append("hard_blocks_present")
        if approval.accepted_risk:
            hard_blocks.append("accepted_risk_cannot_override_hard_blocks")

    valid = len(hard_blocks) == 0 and len(missing) == 0
    return {
        "valid": valid,
        "hard_blocks": hard_blocks,
        "missing_evidence": missing,
        "warnings": warnings_list,
        "approval_effective": approval.approval_effective and valid,
    }


def persist_real_adapter_invocation_approval(
    approval: RealAdapterInvocationApproval,
) -> dict:
    """Persist an approval artifact with digest. Atomic latest.json."""
    import os
    d = _real_adapter_approvals_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    if not approval.record_digest:
        approval.record_digest = approval.compute_digest()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{approval.approval_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(approval.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(approval.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {
            "status": "written", "path": str(fp), "latest_path": str(lp),
            "approval_id": approval.approval_id,
            "record_digest": approval.record_digest,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_real_adapter_invocation_approval(
    approval: RealAdapterInvocationApproval,
) -> dict:
    """Verify approval artifact integrity. Fail-closed."""
    issues_list: list[str] = []
    if not approval.approval_id:
        issues_list.append("missing approval_id")
    if not approval.record_digest:
        issues_list.append("missing record_digest")
    if approval.record_digest:
        computed = approval.compute_digest()
        if computed != approval.record_digest:
            issues_list.append("record_digest_mismatch")
    if approval.schema_version != _APPROVAL_SCHEMA_VERSION:
        issues_list.append(f"schema_version mismatch: {approval.schema_version!r}")
    if approval.hard_blocks_present and approval.approval_effective:
        issues_list.append("approval_effective=True with hard_blocks_present")
    if approval.decision == APPROVAL_APPROVED and not approval.approval_effective and not approval.hard_blocks_present:
        pass  # informative
    return {
        "valid": len(issues_list) == 0,
        "issues": issues_list,
        "approval_id": approval.approval_id,
    }


def load_latest_real_adapter_invocation_approval() -> (
    "RealAdapterInvocationApproval | None"
):
    """Load the latest approval. Returns None if absent/malformed."""
    lp = _real_adapter_approvals_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        if not isinstance(data, dict) or not data:
            return None
        return RealAdapterInvocationApproval.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Z — Real adapter invocation plan artifact
# ═══════════════════════════════════════════════════════════════════════════

_REAL_ADAPTER_PLANS_DIR = ".pcae/real-adapter-invocation-plans"
_PLAN_SCHEMA_VERSION = "1.0"


@dataclass
class RealAdapterInvocationPlan:
    """Future artifact-only real backend invocation plan.

    Binds adapter contract, invocation request, prompt, preflight, approval,
    output quarantine, audit, timeout, broker/shell-gate expectations.
    All execution flags default to False. Plan is model-only — never executes.
    """

    plan_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    prompt_hash: str = ""
    prompt_artifact_path: str = ""
    preflight_artifact_id: str = ""
    preflight_artifact_path: str = ""
    preflight_digest: str = ""
    approval_id: str = ""
    approval_artifact_path: str = ""
    approval_digest: str = ""
    invocation_mode: str = ""
    risk_level: str = RISK_MEDIUM
    operator: str = ""
    output_quarantine_path: str = ""
    audit_artifact_path: str = ""
    timeout_seconds: int = 0
    broker_required: bool = True
    broker_expected_decision: str = ""
    shell_gate_required: bool = True
    shell_gate_expected_decision: str = ""
    no_auto_apply: bool = True
    no_commit_authorization: bool = True
    no_push_authorization: bool = True
    real_backend_invocation_allowed: bool = False
    execution_ready: bool = False
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at_utc: str = ""
    expires_at_utc: str = ""
    schema_version: str = _PLAN_SCHEMA_VERSION
    record_digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.plan_id:
            issues.append("plan_id is required")
        if self.real_backend_invocation_allowed:
            issues.append("real_backend_invocation_allowed must be False")
        if self.execution_ready:
            issues.append("execution_ready must be False")
        if not self.no_auto_apply:
            issues.append("no_auto_apply must be True")
        if not self.no_commit_authorization:
            issues.append("no_commit_authorization must be True")
        if not self.no_push_authorization:
            issues.append("no_push_authorization must be True")
        return issues

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "plan_id": self.plan_id, "adapter_id": self.adapter_id,
            "backend_id": self.backend_id, "backend_type": self.backend_type,
            "request_id": self.request_id, "phase_id": self.phase_id,
            "task_id": self.task_id, "prompt_hash": self.prompt_hash,
            "prompt_artifact_path": self.prompt_artifact_path,
            "preflight_artifact_id": self.preflight_artifact_id,
            "preflight_artifact_path": self.preflight_artifact_path,
            "preflight_digest": self.preflight_digest,
            "approval_id": self.approval_id,
            "approval_artifact_path": self.approval_artifact_path,
            "approval_digest": self.approval_digest,
            "invocation_mode": self.invocation_mode,
            "risk_level": self.risk_level, "operator": self.operator,
            "output_quarantine_path": self.output_quarantine_path,
            "audit_artifact_path": self.audit_artifact_path,
            "timeout_seconds": self.timeout_seconds,
            "broker_required": self.broker_required,
            "broker_expected_decision": self.broker_expected_decision,
            "shell_gate_required": self.shell_gate_required,
            "shell_gate_expected_decision": self.shell_gate_expected_decision,
            "no_auto_apply": self.no_auto_apply,
            "no_commit_authorization": self.no_commit_authorization,
            "no_push_authorization": self.no_push_authorization,
            "real_backend_invocation_allowed": self.real_backend_invocation_allowed,
            "execution_ready": self.execution_ready,
            "hard_blocks": list(self.hard_blocks),
            "warnings": list(self.warnings),
            "created_at_utc": self.created_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "schema_version": self.schema_version,
        }
        if include_digest and self.record_digest:
            d["record_digest"] = self.record_digest
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "RealAdapterInvocationPlan":
        return cls(**{k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__})


def _real_adapter_plans_dir() -> Path:
    from pathlib import Path as _P
    return _P(_REAL_ADAPTER_PLANS_DIR)


def create_real_adapter_invocation_plan(
    *,
    adapter_id: str,
    backend_id: str,
    backend_type: str,
    request_id: str = "",
    phase_id: str = "",
    task_id: str = "",
    prompt_hash: str = "",
    prompt_artifact_path: str = "",
    preflight_artifact: BackendAdapterPreflightArtifact | None = None,
    approval_artifact: RealAdapterInvocationApproval | None = None,
    invocation_mode: str = "",
    risk_level: str = RISK_MEDIUM,
    operator: str = "",
    output_quarantine_path: str = "",
    audit_artifact_path: str = "",
    timeout_seconds: int = 120,
    **kwargs: Any,
) -> "RealAdapterInvocationPlan":
    """Create a future-only invocation plan. Never executes anything."""
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    plan_id = f"rip-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    pf_id = pf_digest = ""
    approval_id_val = approval_digest = ""

    # Validate preflight binding
    if preflight_artifact is not None:
        pf_id = preflight_artifact.artifact_id
        pf_digest = preflight_artifact.record_digest or preflight_artifact.compute_digest()
        if preflight_artifact.backend_id and preflight_artifact.backend_id != backend_id:
            hard_blocks.append("preflight_backend_mismatch")
        if preflight_artifact.hard_blocks:
            hard_blocks.extend(f"preflight:{hb}" for hb in preflight_artifact.hard_blocks)
    else:
        hard_blocks.append("preflight_artifact_missing")

    # Validate approval binding
    if approval_artifact is not None:
        approval_id_val = approval_artifact.approval_id
        approval_digest = approval_artifact.record_digest or approval_artifact.compute_digest()
        if not approval_artifact.approval_effective:
            hard_blocks.append("approval_not_effective")
        if approval_artifact.decision != APPROVAL_APPROVED:
            hard_blocks.append(f"approval_decision:{approval_artifact.decision}")
        if approval_artifact.backend_id and approval_artifact.backend_id != backend_id:
            hard_blocks.append("approval_backend_mismatch")
        if approval_artifact.preflight_digest and pf_digest and approval_artifact.preflight_digest != pf_digest:
            hard_blocks.append("approval_preflight_digest_mismatch")
    else:
        hard_blocks.append("approval_artifact_missing")

    if not prompt_hash:
        hard_blocks.append("prompt_hash_missing")
    if not prompt_artifact_path:
        hard_blocks.append("prompt_artifact_path_missing")
    if not output_quarantine_path:
        hard_blocks.append("output_quarantine_path_missing")
    if not audit_artifact_path:
        hard_blocks.append("audit_artifact_path_missing")
    if timeout_seconds <= 0:
        hard_blocks.append("timeout_missing_or_invalid")
    if not operator:
        hard_blocks.append("operator_missing")

    plan = RealAdapterInvocationPlan(
        plan_id=plan_id, adapter_id=adapter_id, backend_id=backend_id,
        backend_type=backend_type, request_id=request_id,
        phase_id=phase_id, task_id=task_id,
        prompt_hash=prompt_hash, prompt_artifact_path=prompt_artifact_path,
        preflight_artifact_id=pf_id, preflight_digest=pf_digest,
        approval_id=approval_id_val, approval_digest=approval_digest,
        invocation_mode=invocation_mode, risk_level=risk_level,
        operator=operator, output_quarantine_path=output_quarantine_path,
        audit_artifact_path=audit_artifact_path,
        timeout_seconds=timeout_seconds,
        hard_blocks=hard_blocks, warnings=warnings_list,
        created_at_utc=now,
        **{k: v for k, v in kwargs.items()
           if k in RealAdapterInvocationPlan.__dataclass_fields__},
    )
    issues = plan.validate()
    if issues:
        raise ValueError(f"Invalid plan: {'; '.join(issues)}")
    return plan


def validate_real_adapter_invocation_plan(
    plan: RealAdapterInvocationPlan,
) -> dict[str, Any]:
    """Validate plan binding evidence. Fail-closed."""
    hard_blocks = list(plan.hard_blocks)
    issues = plan.validate()
    for i in issues:
        hard_blocks.append(i)
    return {
        "valid": len(hard_blocks) == 0,
        "hard_blocks": hard_blocks,
        "warnings": list(plan.warnings),
    }


def persist_real_adapter_invocation_plan(plan: RealAdapterInvocationPlan) -> dict:
    import os
    d = _real_adapter_plans_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not plan.record_digest:
        plan.record_digest = plan.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{plan.plan_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": plan.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_real_adapter_invocation_plan(plan: RealAdapterInvocationPlan) -> dict:
    issues_list: list[str] = []
    if not plan.plan_id:
        issues_list.append("missing plan_id")
    if not plan.record_digest:
        issues_list.append("missing record_digest")
    if plan.record_digest:
        if plan.compute_digest() != plan.record_digest:
            issues_list.append("record_digest_mismatch")
    if plan.real_backend_invocation_allowed:
        issues_list.append("real_backend_invocation_allowed must be False")
    if plan.execution_ready:
        issues_list.append("execution_ready must be False")
    if not plan.no_auto_apply:
        issues_list.append("no_auto_apply must be True")
    return {"valid": len(issues_list) == 0, "issues": issues_list, "plan_id": plan.plan_id}


def load_latest_real_adapter_invocation_plan() -> RealAdapterInvocationPlan | None:
    lp = _real_adapter_plans_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        if not isinstance(data, dict) or not data:
            return None
        return RealAdapterInvocationPlan.from_dict(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95A — Artifact-only real invocation dry-run boundary
# ═══════════════════════════════════════════════════════════════════════════

_DRY_RUN_DIR = ".pcae/artifact-only-real-invocation-dry-runs"
_DRY_RUN_SCHEMA_VERSION = "1.0"


@dataclass
class ArtifactOnlyRealInvocationDryRunAssessment:
    """Dry-run readiness assessment for artifact-only real invocation.

    Evaluates the complete evidence chain without executing anything.
    All execution flags are hard-defaulted to False.
    """

    assessment_id: str = ""
    plan_id: str = ""
    adapter_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    request_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    prompt_hash: str = ""
    preflight_artifact_id: str = ""
    preflight_digest: str = ""
    approval_id: str = ""
    approval_digest: str = ""
    plan_digest: str = ""
    broker_required: bool = True
    broker_expected_decision: str = ""
    broker_dry_run_decision: str = ""
    shell_gate_required: bool = True
    shell_gate_expected_decision: str = ""
    shell_gate_dry_run_decision: str = ""
    output_quarantine_path: str = ""
    audit_artifact_path: str = ""
    timeout_seconds: int = 0
    execution_allowed: bool = False
    execution_ready: bool = False
    dry_run_only: bool = True
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    deny_reasons: list[str] = field(default_factory=list)
    evidence_chain_valid: bool = False
    no_real_backend_invoked: bool = True
    no_adapter_executed: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    no_auto_apply: bool = True
    no_commit_authorization: bool = True
    no_push_authorization: bool = True
    # ── Phase 95E: runtime evidence binding ───────────────────────────
    runtime_evidence_id: str = ""
    runtime_evidence_path: str = ""
    runtime_evidence_digest: str = ""
    runtime_profile: str = ""
    runtime_bypass_permissions_state: str = ""
    runtime_evidence_valid: bool = False
    runtime_evidence_source: str = ""
    runtime_failure_category: str = ""
    runtime_hard_blocks: list[str] = field(default_factory=list)
    # ── Phase 95G: broker/shell-gate runtime evidence decisions ────────
    runtime_broker_decision: str = ""
    runtime_broker_hard_blocks: list[str] = field(default_factory=list)
    runtime_shell_gate_decision: str = ""
    runtime_shell_gate_hard_blocks: list[str] = field(default_factory=list)
    runtime_broker_shell_gate_ready: bool = False
    created_at_utc: str = ""
    schema_version: str = _DRY_RUN_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_evidence"] = list(self.missing_evidence)
        d["deny_reasons"] = list(self.deny_reasons)
        d["runtime_hard_blocks"] = list(self.runtime_hard_blocks)
        d["runtime_broker_hard_blocks"] = list(self.runtime_broker_hard_blocks)
        d["runtime_shell_gate_hard_blocks"] = list(self.runtime_shell_gate_hard_blocks)
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactOnlyRealInvocationDryRunAssessment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _dry_run_dir() -> Path:
    from pathlib import Path as _P
    return _P(_DRY_RUN_DIR)


def evaluate_artifact_only_real_invocation_dry_run(
    *,
    plan: RealAdapterInvocationPlan | None = None,
    preflight_artifact: BackendAdapterPreflightArtifact | None = None,
    approval_artifact: RealAdapterInvocationApproval | None = None,
    contract: BackendAdapterContract | None = None,
    runtime_evidence: ClaudeRuntimeEvidence | None = None,
) -> ArtifactOnlyRealInvocationDryRunAssessment:
    """Evaluate evidence chain for artifact-only real invocation. Dry-run only.

    Never executes, never invokes backends, never spawns subprocess.
    Always returns execution_allowed=False, dry_run_only=True.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    assessment_id = f"dra-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    missing: list[str] = []
    deny: list[str] = []

    # ── Plan evidence ──────────────────────────────────────────────────
    if plan is None:
        hard_blocks.append("invocation_plan_missing")
    else:
        plan_result = verify_real_adapter_invocation_plan(plan)
        if not plan_result["valid"]:
            hard_blocks.extend(f"plan:{i}" for i in plan_result["issues"])
        if plan.real_backend_invocation_allowed:
            hard_blocks.append("plan:real_backend_invocation_allowed=True")
        if plan.execution_ready:
            hard_blocks.append("plan:execution_ready=True")
        if not plan.no_auto_apply:
            hard_blocks.append("plan:no_auto_apply=False")
        if not plan.no_commit_authorization:
            hard_blocks.append("plan:no_commit_authorization=False")
        if not plan.no_push_authorization:
            hard_blocks.append("plan:no_push_authorization=False")

    # ── Preflight evidence ─────────────────────────────────────────────
    if preflight_artifact is None:
        hard_blocks.append("preflight_artifact_missing")
    else:
        pf_result = verify_backend_adapter_preflight_artifact(preflight_artifact)
        if not pf_result["valid"]:
            hard_blocks.extend(f"preflight:{i}" for i in pf_result["issues"])

    # ── Approval evidence ──────────────────────────────────────────────
    if approval_artifact is None:
        hard_blocks.append("approval_artifact_missing")
    else:
        ap_result = verify_real_adapter_invocation_approval(approval_artifact)
        if not ap_result["valid"]:
            hard_blocks.extend(f"approval:{i}" for i in ap_result["issues"])
        if not approval_artifact.approval_effective:
            hard_blocks.append("approval_not_effective")
        if approval_artifact.decision != APPROVAL_APPROVED:
            hard_blocks.append(f"approval_decision:{approval_artifact.decision}")

    # ── Cross-artifact binding ─────────────────────────────────────────
    if plan is not None and preflight_artifact is not None:
        if plan.preflight_digest and preflight_artifact.record_digest:
            if plan.preflight_digest != preflight_artifact.record_digest:
                hard_blocks.append("plan_preflight_digest_mismatch")
    if plan is not None and approval_artifact is not None:
        if plan.approval_digest and approval_artifact.record_digest:
            if plan.approval_digest != approval_artifact.record_digest:
                hard_blocks.append("plan_approval_digest_mismatch")

    # ── Plan structural checks ─────────────────────────────────────────
    if plan is not None:
        if not plan.output_quarantine_path:
            missing.append("output_quarantine_path")
        if not plan.audit_artifact_path:
            missing.append("audit_artifact_path")
        if plan.timeout_seconds <= 0:
            hard_blocks.append("timeout_missing_or_invalid")

    # ── Runtime evidence validation (Phase 95E) ──────────────────────
    re_id = re_digest = re_profile = re_bypass = re_source = re_failure = ""
    re_valid = False
    re_hard_blocks: list[str] = []
    if runtime_evidence is not None:
        re_id = runtime_evidence.runtime_evidence_id
        re_digest = runtime_evidence.record_digest or runtime_evidence.compute_digest()
        re_profile = runtime_evidence.runtime_profile
        re_bypass = runtime_evidence.bypass_permissions_state
        re_source = runtime_evidence.evidence_source
        re_valid_result = validate_claude_runtime_evidence(runtime_evidence)
        re_valid = re_valid_result["valid"]
        re_hard_blocks = list(re_valid_result.get("hard_blocks", []))
        re_failure = runtime_evidence.failure_category or ""
        if not re_valid:
            hard_blocks.extend(f"runtime:{hb}" for hb in re_hard_blocks)
        # Cross-binding checks
        if plan is not None:
            if plan.backend_id and runtime_evidence.backend_id and plan.backend_id != runtime_evidence.backend_id:
                hard_blocks.append("runtime_backend_mismatch")
            if plan.adapter_id and runtime_evidence.adapter_id and plan.adapter_id != runtime_evidence.adapter_id:
                hard_blocks.append("runtime_adapter_mismatch")
            if plan.timeout_seconds and runtime_evidence.timeout_seconds and plan.timeout_seconds != runtime_evidence.timeout_seconds:
                hard_blocks.append("runtime_timeout_mismatch")
            if plan.audit_artifact_path and runtime_evidence.audit_path and plan.audit_artifact_path != runtime_evidence.audit_path:
                hard_blocks.append("runtime_audit_path_mismatch")
            if plan.output_quarantine_path and runtime_evidence.output_quarantine_path and plan.output_quarantine_path != runtime_evidence.output_quarantine_path:
                hard_blocks.append("runtime_quarantine_path_mismatch")
        if not runtime_evidence.no_real_backend_invoked:
            hard_blocks.append("runtime:no_real_backend_invoked=False")
        if not runtime_evidence.no_subprocess:
            hard_blocks.append("runtime:no_subprocess=False")
        if not runtime_evidence.no_network:
            hard_blocks.append("runtime:no_network=False")
        if not runtime_evidence.no_adapter_executed:
            hard_blocks.append("runtime:no_adapter_executed=False")
    else:
        hard_blocks.append("runtime_evidence_missing")
        re_failure = "runtime_evidence_missing"

    # ── Determine outcome ──────────────────────────────────────────────
    for hb in hard_blocks:
        deny.append(hb)
    for m in missing:
        deny.append(f"missing:{m}")

    evidence_valid = len(hard_blocks) == 0 and len(missing) == 0
    execution_allowed = False
    execution_ready = False

    return ArtifactOnlyRealInvocationDryRunAssessment(
        assessment_id=assessment_id,
        plan_id=plan.plan_id if plan else "",
        adapter_id=plan.adapter_id if plan else "",
        backend_id=plan.backend_id if plan else "",
        backend_type=plan.backend_type if plan else "",
        dry_run_only=True,
        execution_allowed=execution_allowed,
        execution_ready=execution_ready,
        hard_blocks=hard_blocks,
        warnings=warnings_list,
        missing_evidence=missing,
        deny_reasons=deny,
        evidence_chain_valid=evidence_valid,
        no_real_backend_invoked=True,
        no_adapter_executed=True,
        no_subprocess=True,
        no_network=True,
        no_auto_apply=True,
        no_commit_authorization=True,
        no_push_authorization=True,
        runtime_evidence_id=re_id,
        runtime_evidence_digest=re_digest,
        runtime_profile=re_profile,
        runtime_bypass_permissions_state=re_bypass,
        runtime_evidence_valid=re_valid,
        runtime_evidence_source=re_source,
        runtime_failure_category=re_failure,
        runtime_hard_blocks=re_hard_blocks,
        created_at_utc=now,
    )
    # ── Broker/shell-gate runtime evidence decisions (95G) ──────────────
    broker_dec = evaluate_runtime_evidence_broker_decision(
        plan=plan, runtime_evidence=runtime_evidence,
    )
    sg_dec = evaluate_runtime_evidence_shell_gate_decision(
        plan=plan, runtime_evidence=runtime_evidence,
    )
    assessment.runtime_broker_decision = broker_dec["decision"]
    assessment.runtime_broker_hard_blocks = broker_dec["hard_blocks"]
    assessment.runtime_shell_gate_decision = sg_dec["decision"]
    assessment.runtime_shell_gate_hard_blocks = sg_dec["hard_blocks"]
    assessment.runtime_broker_shell_gate_ready = (
        broker_dec["decision"] == DECISION_ALLOW_DRY_RUN
        and sg_dec["decision"] == DECISION_ALLOW_DRY_RUN
    )
    return assessment


def persist_artifact_only_real_invocation_dry_run_assessment(
    assessment: ArtifactOnlyRealInvocationDryRunAssessment,
) -> dict:
    import os
    d = _dry_run_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not assessment.record_digest:
        assessment.record_digest = assessment.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{assessment.assessment_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": assessment.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_artifact_only_real_invocation_dry_run_assessment(
    assessment: ArtifactOnlyRealInvocationDryRunAssessment,
) -> dict:
    issues_list: list[str] = []
    if not assessment.assessment_id:
        issues_list.append("missing assessment_id")
    if not assessment.record_digest:
        issues_list.append("missing record_digest")
    if assessment.record_digest and assessment.compute_digest() != assessment.record_digest:
        issues_list.append("record_digest_mismatch")
    if not assessment.dry_run_only:
        issues_list.append("dry_run_only must be True")
    if assessment.execution_allowed:
        issues_list.append("execution_allowed must be False")
    if not assessment.no_real_backend_invoked:
        issues_list.append("no_real_backend_invoked must be True")
    return {"valid": len(issues_list) == 0, "issues": issues_list}


def load_latest_artifact_only_real_invocation_dry_run_assessment() -> (
    "ArtifactOnlyRealInvocationDryRunAssessment | None"
):
    lp = _dry_run_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyRealInvocationDryRunAssessment.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════
# Phase 95C — Claude runtime evidence model
# ═══════════════════════════════════════════════════════════════════════

_RUNTIME_EVIDENCE_DIR = ".pcae/claude-runtime-evidence"
_RUNTIME_EVIDENCE_SCHEMA_VERSION = "1.0"

# ── Profiles ───────────────────────────────────────────────────────────
PROFILE_CLAUDE_CLI = "claude_cli"
PROFILE_CLAUDE_DEEPSEEK_CLI = "claude_deepseek_cli"
PROFILE_CUSTOM_CLAUDE_COMPATIBLE = "custom_claude_compatible"
VALID_RUNTIME_PROFILES = frozenset({PROFILE_CLAUDE_CLI, PROFILE_CLAUDE_DEEPSEEK_CLI, PROFILE_CUSTOM_CLAUDE_COMPATIBLE})

# ── Bypass states ──────────────────────────────────────────────────────
BYPASS_UNKNOWN = "unknown"
BYPASS_OFF = "off"
BYPASS_ON = "on"
BYPASS_NOT_APPLICABLE = "not_applicable"
VALID_BYPASS_STATES = frozenset({BYPASS_UNKNOWN, BYPASS_OFF, BYPASS_ON, BYPASS_NOT_APPLICABLE})

# ── Evidence sources ───────────────────────────────────────────────────
EVIDENCE_OPERATOR_DECLARED = "operator_declared"
EVIDENCE_PCAE_CONFIG = "pcae_config"
EVIDENCE_ARTIFACT_IMPORT = "artifact_import"
EVIDENCE_FUTURE_STAT_ONLY = "future_stat_only_detector"
EVIDENCE_UNKNOWN = "unknown"
VALID_EVIDENCE_SOURCES = frozenset({EVIDENCE_OPERATOR_DECLARED, EVIDENCE_PCAE_CONFIG, EVIDENCE_ARTIFACT_IMPORT, EVIDENCE_FUTURE_STAT_ONLY, EVIDENCE_UNKNOWN})


@dataclass
class ClaudeRuntimeEvidence:
    """Pure runtime evidence model for Claude/Claude-DeepSeek.

    Stat-only representation. Never inspects the live system.
    All execution flags default to safe values.
    """

    runtime_evidence_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    adapter_id: str = ""
    runtime_profile: str = ""
    command_identity: str = ""
    declared_command_path: str = ""
    declared_command_path_hash: str = ""
    wrapper_identity: str = ""
    wrapper_path: str = ""
    wrapper_path_hash: str = ""
    auth_mode: str = ""
    required_env_keys_present_redacted: list[str] = field(default_factory=list)
    required_env_keys_missing: list[str] = field(default_factory=list)
    bypass_permissions_state: str = BYPASS_UNKNOWN
    bypass_permissions_evidence: str = ""
    session_isolation_mode: str = "stateless"
    working_directory: str = ""
    timeout_seconds: int = 0
    output_capture_mode: str = ""
    audit_path: str = ""
    output_quarantine_path: str = ""
    shell_gate_required: bool = True
    shell_gate_expected_decision: str = ""
    broker_required: bool = True
    broker_expected_decision: str = ""
    detected_at_utc: str = ""
    evidence_source: str = EVIDENCE_OPERATOR_DECLARED
    confidence: str = "low"
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    failure_category: str = ""
    no_real_backend_invoked: bool = True
    no_adapter_executed: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    secrets_redacted: bool = True
    schema_version: str = _RUNTIME_EVIDENCE_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["required_env_keys_present_redacted"] = list(self.required_env_keys_present_redacted)
        d["required_env_keys_missing"] = list(self.required_env_keys_missing)
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_evidence"] = list(self.missing_evidence)
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ClaudeRuntimeEvidence":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _runtime_evidence_dir() -> Path:
    from pathlib import Path as _P
    return _P(_RUNTIME_EVIDENCE_DIR)


def validate_claude_runtime_evidence(evidence: ClaudeRuntimeEvidence) -> dict:
    """Validate runtime evidence. Fail-closed. Never inspects the live system."""
    hard_blocks: list[str] = []
    missing: list[str] = []

    if not evidence.runtime_evidence_id:
        missing.append("runtime_evidence_id")
    if not evidence.backend_id:
        hard_blocks.append("backend_id_missing")
    if evidence.runtime_profile not in VALID_RUNTIME_PROFILES:
        hard_blocks.append(f"unknown_runtime_profile:{evidence.runtime_profile}")
    if not evidence.command_identity:
        hard_blocks.append("command_identity_missing")
    if evidence.runtime_profile != PROFILE_CUSTOM_CLAUDE_COMPATIBLE:
        if not evidence.declared_command_path:
            hard_blocks.append("declared_command_path_missing")
    if evidence.bypass_permissions_state == BYPASS_UNKNOWN:
        hard_blocks.append("bypass_state_unknown")
    elif evidence.bypass_permissions_state == BYPASS_ON:
        hard_blocks.append("bypass_enabled")
    if evidence.evidence_source not in VALID_EVIDENCE_SOURCES:
        hard_blocks.append(f"unknown_evidence_source:{evidence.evidence_source}")
    if evidence.evidence_source == EVIDENCE_UNKNOWN:
        hard_blocks.append("evidence_source_unknown")
    if evidence.timeout_seconds <= 0:
        hard_blocks.append("timeout_missing_or_invalid")
    if not evidence.audit_path:
        hard_blocks.append("audit_path_missing")
    if not evidence.output_quarantine_path:
        hard_blocks.append("output_quarantine_path_missing")
    if not evidence.no_real_backend_invoked:
        hard_blocks.append("no_real_backend_invoked_must_be_true")
    if not evidence.no_adapter_executed:
        hard_blocks.append("no_adapter_executed_must_be_true")
    if not evidence.no_subprocess:
        hard_blocks.append("no_subprocess_must_be_true")
    if not evidence.no_network:
        hard_blocks.append("no_network_must_be_true")
    if not evidence.secrets_redacted:
        hard_blocks.append("secrets_redacted_must_be_true")
    if evidence.confidence == "high" and evidence.evidence_source == EVIDENCE_OPERATOR_DECLARED:
        pass  # allowed but should have explicit evidence
    return {
        "valid": len(hard_blocks) == 0 and len(missing) == 0,
        "hard_blocks": hard_blocks,
        "missing_evidence": missing,
    }


def persist_claude_runtime_evidence(evidence: ClaudeRuntimeEvidence) -> dict:
    import os
    d = _runtime_evidence_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not evidence.record_digest:
        evidence.record_digest = evidence.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{evidence.runtime_evidence_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(evidence.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(evidence.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": evidence.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_claude_runtime_evidence(evidence: ClaudeRuntimeEvidence) -> dict:
    issues_list: list[str] = []
    if not evidence.runtime_evidence_id:
        issues_list.append("missing runtime_evidence_id")
    if not evidence.record_digest:
        issues_list.append("missing record_digest")
    if evidence.record_digest and evidence.compute_digest() != evidence.record_digest:
        issues_list.append("record_digest_mismatch")
    if evidence.schema_version != _RUNTIME_EVIDENCE_SCHEMA_VERSION:
        issues_list.append(f"schema_version mismatch: {evidence.schema_version!r}")
    return {"valid": len(issues_list) == 0, "issues": issues_list}


def load_latest_claude_runtime_evidence() -> ClaudeRuntimeEvidence | None:
    lp = _runtime_evidence_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ClaudeRuntimeEvidence.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


# ── Phase 95D: secret detection helper ─────────────────────────────────

_SECRET_VALUE_PATTERNS: list[str] = [
    "sk-ant-", "sk-", "Bearer ", "API_KEY=", "TOKEN=", "PASSWORD=",
    "--api-key ", "--token ", "--password ",
]


def _scan_for_secrets(data: dict | list | str | Any) -> list[str]:
    """Recursively scan a JSON-serializable structure for secret-like values.

    Returns list of paths where secrets were found. Empty list = safe.
    Never prints the actual values.
    """
    findings: list[str] = []
    if isinstance(data, str):
        lower = data.lower()
        for pat in _SECRET_VALUE_PATTERNS:
            if pat.lower() in lower:
                findings.append(f"secret_pattern_detected")
                break
    elif isinstance(data, dict):
        for k, v in data.items():
            if any(p.lower() in k.lower() for p in ("token", "password", "api_key", "secret")):
                if isinstance(v, str) and len(v) > 8:
                    findings.append(f"secret_like_value_in_key:{k}")
            for f in _scan_for_secrets(v):
                findings.append(f"{k}.{f}" if "." not in f else f"{k}/{f}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            for f in _scan_for_secrets(item):
                findings.append(f"[{i}]{f}")
    return findings


def import_claude_runtime_evidence_from_json(json_path: str) -> tuple[
    "ClaudeRuntimeEvidence | None", dict
]:
    """Import runtime evidence from an explicit JSON file.

    Validates JSON shape, constructs ClaudeRuntimeEvidence, scans for
    secrets, validates model, computes digest. Returns (evidence, result).
    Never inspects live runtime, never executes commands, never calls network.
    """
    from pathlib import Path as _P
    p = _P(json_path)
    if not p.is_file():
        return None, {"status": "failed", "error": f"File not found: {json_path}"}

    try:
        raw_data = _json.loads(p.read_text())
    except Exception as exc:
        return None, {"status": "failed", "error": f"Malformed JSON: {exc}"}

    if not isinstance(raw_data, dict):
        return None, {"status": "failed", "error": "JSON root must be a dict"}

    # Scan for secrets before constructing model
    secret_findings = _scan_for_secrets(raw_data)
    if secret_findings:
        return None, {"status": "blocked", "error": "secret values detected in import",
                       "details": secret_findings[:3]}

    try:
        evidence = ClaudeRuntimeEvidence.from_dict(raw_data)
    except Exception as exc:
        return None, {"status": "failed", "error": f"Model construction failed: {exc}"}

    # Validate
    validation = validate_claude_runtime_evidence(evidence)
    if not validation["valid"]:
        return None, {"status": "blocked", "error": "validation failed",
                       "hard_blocks": validation["hard_blocks"],
                       "missing_evidence": validation["missing_evidence"]}

    # Compute digest
    evidence.record_digest = evidence.compute_digest()

    return evidence, {"status": "imported", "runtime_evidence_id": evidence.runtime_evidence_id}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95F — Stat-only runtime detector prototype
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ClaudeRuntimeDetectionConfig:
    """Explicit operator-provided config for stat-only detection.

    All paths must be explicit. No PATH lookup. No command auto-discovery.
    No subprocess. No shell. No network. No live session inspection.
    """

    config_id: str = ""
    backend_id: str = ""
    backend_type: str = ""
    adapter_id: str = ""
    runtime_profile: str = ""
    declared_command_path: str = ""
    wrapper_path: str = ""
    auth_mode: str = ""
    required_env_keys_present_redacted: list[str] = field(default_factory=list)
    required_env_keys_missing: list[str] = field(default_factory=list)
    bypass_permissions_state: str = BYPASS_UNKNOWN
    bypass_permissions_evidence: str = ""
    session_isolation_mode: str = "stateless"
    working_directory: str = ""
    timeout_seconds: int = 0
    output_capture_mode: str = ""
    audit_path: str = ""
    output_quarantine_path: str = ""
    shell_gate_required: bool = True
    shell_gate_expected_decision: str = ""
    broker_required: bool = True
    broker_expected_decision: str = ""
    evidence_source: str = EVIDENCE_OPERATOR_DECLARED
    schema_version: str = _RUNTIME_EVIDENCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["required_env_keys_present_redacted"] = list(self.required_env_keys_present_redacted)
        d["required_env_keys_missing"] = list(self.required_env_keys_missing)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ClaudeRuntimeDetectionConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def detect_claude_runtime_evidence_stat_only(
    config: ClaudeRuntimeDetectionConfig,
) -> ClaudeRuntimeEvidence:
    """Stat-only runtime evidence detector.

    Reads only explicit configured paths using Python filesystem APIs.
    Computes SHA-256 hashes of explicit files. Never executes, never
    uses subprocess/which/shell/network, never auto-discovers commands.
    """
    import hashlib
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    evidence_id = f"re-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    missing: list[str] = []
    command_hash = ""
    wrapper_hash = ""

    # Validate profile
    if config.runtime_profile not in VALID_RUNTIME_PROFILES:
        hard_blocks.append(f"unknown_runtime_profile:{config.runtime_profile}")

    # Stat-only filesystem inspection for explicit paths
    if config.runtime_profile != PROFILE_CUSTOM_CLAUDE_COMPATIBLE:
        cp = config.declared_command_path
        if not cp:
            hard_blocks.append("declared_command_path_missing")
        else:
            from pathlib import Path as _P
            pp = _P(cp)
            if not pp.exists():
                hard_blocks.append("command_path_not_found")
            elif pp.is_dir():
                hard_blocks.append("command_path_is_directory")
            elif not pp.is_file():
                hard_blocks.append("command_path_not_regular_file")
            else:
                try:
                    command_hash = hashlib.sha256(pp.read_bytes()).hexdigest()
                except Exception:
                    hard_blocks.append("command_path_unreadable")

    if config.wrapper_path:
        from pathlib import Path as _P
        wp = _P(config.wrapper_path)
        if not wp.exists():
            hard_blocks.append("wrapper_path_not_found")
        elif wp.is_dir():
            hard_blocks.append("wrapper_path_is_directory")
        elif not wp.is_file():
            hard_blocks.append("wrapper_path_not_regular_file")
        else:
            try:
                wrapper_hash = hashlib.sha256(wp.read_bytes()).hexdigest()
            except Exception:
                hard_blocks.append("wrapper_path_unreadable")

    # Bypass
    if config.bypass_permissions_state == BYPASS_UNKNOWN:
        hard_blocks.append("bypass_state_unknown")
    elif config.bypass_permissions_state == BYPASS_ON:
        hard_blocks.append("bypass_enabled")

    # Required fields
    if config.timeout_seconds <= 0:
        missing.append("timeout")
    if not config.audit_path:
        missing.append("audit_path")
    if not config.output_quarantine_path:
        missing.append("output_quarantine_path")

    return ClaudeRuntimeEvidence(
        runtime_evidence_id=evidence_id,
        backend_id=config.backend_id,
        backend_type=config.backend_type,
        adapter_id=config.adapter_id,
        runtime_profile=config.runtime_profile,
        command_identity=config.declared_command_path,
        declared_command_path=config.declared_command_path,
        declared_command_path_hash=command_hash,
        wrapper_path=config.wrapper_path,
        wrapper_path_hash=wrapper_hash,
        auth_mode=config.auth_mode,
        required_env_keys_present_redacted=list(config.required_env_keys_present_redacted),
        required_env_keys_missing=list(config.required_env_keys_missing),
        bypass_permissions_state=config.bypass_permissions_state,
        bypass_permissions_evidence=config.bypass_permissions_evidence,
        timeout_seconds=config.timeout_seconds,
        audit_path=config.audit_path,
        output_quarantine_path=config.output_quarantine_path,
        shell_gate_required=config.shell_gate_required,
        shell_gate_expected_decision=config.shell_gate_expected_decision,
        broker_required=config.broker_required,
        broker_expected_decision=config.broker_expected_decision,
        detected_at_utc=now,
        evidence_source=EVIDENCE_FUTURE_STAT_ONLY,
        confidence="medium" if not hard_blocks else "low",
        hard_blocks=hard_blocks,
        warnings=warnings_list,
        missing_evidence=missing,
        no_real_backend_invoked=True,
        no_adapter_executed=True,
        no_subprocess=True,
        no_network=True,
        secrets_redacted=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95G — Runtime evidence broker/shell-gate integration
# ═══════════════════════════════════════════════════════════════════════════

DECISION_ALLOW_DRY_RUN = "allow_dry_run"
DECISION_DENY = "deny"
DECISION_HARD_BLOCK = "hard_block"
DECISION_MISSING_EVIDENCE = "missing_evidence"


def evaluate_runtime_evidence_broker_decision(
    *,
    plan: RealAdapterInvocationPlan | None = None,
    runtime_evidence: ClaudeRuntimeEvidence | None = None,
) -> dict[str, Any]:
    """Dry-run broker decision for runtime evidence. Model-only, never executes."""
    hard_blocks: list[str] = []
    missing: list[str] = []

    if runtime_evidence is None:
        hard_blocks.append("runtime_evidence_missing")
    else:
        ver = validate_claude_runtime_evidence(runtime_evidence)
        if not ver["valid"]:
            hard_blocks.extend(f"runtime:{hb}" for hb in ver.get("hard_blocks", []))
        if runtime_evidence.bypass_permissions_state in (BYPASS_UNKNOWN, BYPASS_ON):
            hard_blocks.append(f"bypass_{runtime_evidence.bypass_permissions_state}")
        if runtime_evidence.runtime_profile not in VALID_RUNTIME_PROFILES:
            hard_blocks.append(f"unknown_profile:{runtime_evidence.runtime_profile}")
        if runtime_evidence.evidence_source == EVIDENCE_UNKNOWN:
            hard_blocks.append("evidence_source_unknown")
        if not runtime_evidence.no_real_backend_invoked:
            hard_blocks.append("no_real_backend_invoked=False")
        if not runtime_evidence.no_subprocess:
            hard_blocks.append("no_subprocess=False")
        if plan is not None and runtime_evidence is not None:
            if plan.backend_id and runtime_evidence.backend_id and plan.backend_id != runtime_evidence.backend_id:
                hard_blocks.append("broker_backend_mismatch")
            if plan.adapter_id and runtime_evidence.adapter_id and plan.adapter_id != runtime_evidence.adapter_id:
                hard_blocks.append("broker_adapter_mismatch")

    if hard_blocks:
        decision = DECISION_HARD_BLOCK
    elif missing:
        decision = DECISION_MISSING_EVIDENCE
    else:
        decision = DECISION_ALLOW_DRY_RUN

    return {"decision": decision, "hard_blocks": hard_blocks, "missing_evidence": missing,
            "allow_dry_run_only": True, "no_execution": True}


def evaluate_runtime_evidence_shell_gate_decision(
    *,
    plan: RealAdapterInvocationPlan | None = None,
    runtime_evidence: ClaudeRuntimeEvidence | None = None,
) -> dict[str, Any]:
    """Dry-run shell-gate decision for runtime evidence. Model-only, never executes."""
    hard_blocks: list[str] = []
    missing: list[str] = []

    if runtime_evidence is None:
        hard_blocks.append("runtime_evidence_missing")
    else:
        if not runtime_evidence.shell_gate_required:
            missing.append("shell_gate_required=False")
        if not runtime_evidence.shell_gate_expected_decision:
            missing.append("shell_gate_expected_decision_missing")
        if not runtime_evidence.declared_command_path and runtime_evidence.runtime_profile != "custom_claude_compatible":
            hard_blocks.append("command_path_missing")
        if not runtime_evidence.declared_command_path_hash and runtime_evidence.runtime_profile != "custom_claude_compatible":
            hard_blocks.append("command_path_hash_missing")
        if not runtime_evidence.no_subprocess:
            hard_blocks.append("no_subprocess=False")
        if not runtime_evidence.no_network:
            hard_blocks.append("no_network=False")
        if runtime_evidence.bypass_permissions_state in (BYPASS_UNKNOWN, BYPASS_ON):
            hard_blocks.append(f"bypass_{runtime_evidence.bypass_permissions_state}")

    if hard_blocks:
        decision = DECISION_HARD_BLOCK
    elif missing:
        decision = DECISION_MISSING_EVIDENCE
    else:
        decision = DECISION_ALLOW_DRY_RUN

    return {"decision": decision, "hard_blocks": hard_blocks, "missing_evidence": missing,
            "allow_dry_run_only": True, "no_execution": True}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95K — Artifact-only invocation command boundary model
# ═══════════════════════════════════════════════════════════════════════════

_BOUNDARY_SCHEMA_VERSION = "1.0"
_BOUNDARY_DIR = ".pcae/artifact-only-invocation-boundaries"

# ── Command modes ─────────────────────────────────────────────────────────

COMMAND_MODE_PLAN = "plan"
COMMAND_MODE_DRY_RUN = "dry_run"
COMMAND_MODE_EXECUTE_RESERVED = "execute_reserved"

VALID_COMMAND_MODES: frozenset[str] = frozenset({
    COMMAND_MODE_PLAN, COMMAND_MODE_DRY_RUN, COMMAND_MODE_EXECUTE_RESERVED,
})

# ── Boundary decisions ─────────────────────────────────────────────────────

BOUNDARY_READY_FOR_PLAN = "ready_for_plan"
BOUNDARY_READY_FOR_DRY_RUN = "ready_for_dry_run"
BOUNDARY_HARD_BLOCK = "hard_block"
BOUNDARY_UNSUPPORTED_EXECUTE = "unsupported_execute"
BOUNDARY_MISSING_INPUTS = "missing_inputs"
BOUNDARY_MISMATCH = "mismatch"


@dataclass
class ArtifactOnlyInvocationCommandBoundary:
    """Command boundary input model for artifact-only backend invocation.

    Translates the 95J design into deterministic Python data model.
    No execution capability — validation and planning only.
    """

    boundary_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    adapter_id: str = ""
    prompt_artifact_path: str = ""
    prompt_artifact_digest: str = ""
    preflight_artifact_path: str = ""
    preflight_artifact_digest: str = ""
    runtime_evidence_path: str = ""
    runtime_evidence_digest: str = ""
    approval_artifact_path: str = ""
    approval_artifact_digest: str = ""
    invocation_plan_path: str = ""
    invocation_plan_digest: str = ""
    broker_decision_id: str = ""
    broker_decision: str = ""
    shell_gate_decision_id: str = ""
    shell_gate_decision: str = ""
    output_quarantine_path: str = ""
    audit_path: str = ""
    timeout_seconds: int = 0
    redaction_policy_id: str = ""
    operator_approval_reference: str = ""
    command_mode: str = COMMAND_MODE_PLAN
    execute_requested: bool = False
    dry_run_only: bool = True
    no_real_backend_invoked: bool = True
    no_adapter_executed: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    no_repo_mutation: bool = True
    no_apply: bool = True
    no_patch_parsing: bool = True
    no_commit_push_authorization: bool = True
    no_telegram_inbound: bool = True
    created_at_utc: str = ""
    schema_version: str = _BOUNDARY_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactOnlyInvocationCommandBoundary":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ArtifactOnlyInvocationCommandBoundaryAssessment:
    """Validation assessment for a command boundary.

    Always returns execution_allowed=False.  Execute is unsupported in 95K.
    """

    assessment_id: str = ""
    boundary_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    command_mode: str = ""
    ready: bool = False
    decision: str = ""
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    mismatch_reasons: list[str] = field(default_factory=list)
    failure_classifications: list[str] = field(default_factory=list)
    execution_allowed: bool = False
    execute_supported: bool = False
    dry_run_only: bool = True
    broker_shell_gate_ready: bool = False
    output_quarantine_ready: bool = False
    audit_ready: bool = False
    timeout_ready: bool = False
    evidence_chain_ready: bool = False
    no_real_backend_invoked: bool = True
    no_adapter_executed: bool = True
    no_subprocess: bool = True
    no_network: bool = True
    no_repo_mutation: bool = True
    no_apply: bool = True
    no_patch_parsing: bool = True
    no_commit_push_authorization: bool = True
    no_telegram_inbound: bool = True
    created_at_utc: str = ""
    schema_version: str = _BOUNDARY_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_inputs"] = list(self.missing_inputs)
        d["mismatch_reasons"] = list(self.mismatch_reasons)
        d["failure_classifications"] = list(self.failure_classifications)
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactOnlyInvocationCommandBoundaryAssessment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def validate_artifact_only_invocation_command_boundary(
    boundary: ArtifactOnlyInvocationCommandBoundary,
) -> ArtifactOnlyInvocationCommandBoundaryAssessment:
    """Validate a command boundary against all 95K rules.

    Model-only validation — never executes, never invokes backends,
    never spawns subprocess.  Always returns execution_allowed=False.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    assessment_id = f"cba-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    missing: list[str] = []
    mismatches: list[str] = []
    failures: list[str] = []

    # ── Identity fields ──────────────────────────────────────────────────
    if not boundary.boundary_id:
        hard_blocks.append("boundary_id_missing")
    if not boundary.phase_id:
        hard_blocks.append("phase_id_missing")
    if not boundary.task_id:
        hard_blocks.append("task_id_missing")

    # ── Backend/adapter ───────────────────────────────────────────────────
    if not boundary.backend_id:
        hard_blocks.append("backend_id_missing")
    if not boundary.adapter_id:
        hard_blocks.append("adapter_id_missing")

    # ── Artifact paths and digests ────────────────────────────────────────
    _required_artifacts = [
        ("prompt_artifact", boundary.prompt_artifact_path, boundary.prompt_artifact_digest),
        ("preflight_artifact", boundary.preflight_artifact_path, boundary.preflight_artifact_digest),
        ("runtime_evidence", boundary.runtime_evidence_path, boundary.runtime_evidence_digest),
        ("approval_artifact", boundary.approval_artifact_path, boundary.approval_artifact_digest),
        ("invocation_plan", boundary.invocation_plan_path, boundary.invocation_plan_digest),
    ]
    for name, path, digest in _required_artifacts:
        if not path:
            hard_blocks.append(f"{name}_path_missing")
        if not digest:
            hard_blocks.append(f"{name}_digest_missing")

    # ── Broker / shell-gate decisions ─────────────────────────────────────
    if not boundary.broker_decision_id:
        hard_blocks.append("broker_decision_id_missing")
    if not boundary.broker_decision:
        hard_blocks.append("broker_decision_missing")
    elif boundary.broker_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hard_blocks.append(f"broker_decision:{boundary.broker_decision}")

    if not boundary.shell_gate_decision_id:
        hard_blocks.append("shell_gate_decision_id_missing")
    if not boundary.shell_gate_decision:
        hard_blocks.append("shell_gate_decision_missing")
    elif boundary.shell_gate_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hard_blocks.append(f"shell_gate_decision:{boundary.shell_gate_decision}")

    # ── Paths and timeout ─────────────────────────────────────────────────
    if not boundary.output_quarantine_path:
        hard_blocks.append("output_quarantine_path_missing")
    if not boundary.audit_path:
        hard_blocks.append("audit_path_missing")
    if boundary.timeout_seconds <= 0:
        hard_blocks.append("timeout_missing_or_invalid")
    if not boundary.redaction_policy_id:
        hard_blocks.append("redaction_policy_id_missing")
    if not boundary.operator_approval_reference:
        hard_blocks.append("operator_approval_reference_missing")

    # ── Command mode ──────────────────────────────────────────────────────
    if boundary.command_mode not in VALID_COMMAND_MODES:
        hard_blocks.append(f"unknown_command_mode:{boundary.command_mode}")
    if boundary.command_mode == COMMAND_MODE_EXECUTE_RESERVED:
        hard_blocks.append("execute_reserved_not_supported")
    if boundary.execute_requested:
        hard_blocks.append("execute_requested=True")
    if not boundary.dry_run_only:
        hard_blocks.append("dry_run_only=False")

    # ── Safety invariants ─────────────────────────────────────────────────
    _safety_checks = [
        ("no_real_backend_invoked", boundary.no_real_backend_invoked),
        ("no_adapter_executed", boundary.no_adapter_executed),
        ("no_subprocess", boundary.no_subprocess),
        ("no_network", boundary.no_network),
        ("no_repo_mutation", boundary.no_repo_mutation),
        ("no_apply", boundary.no_apply),
        ("no_patch_parsing", boundary.no_patch_parsing),
        ("no_commit_push_authorization", boundary.no_commit_push_authorization),
        ("no_telegram_inbound", boundary.no_telegram_inbound),
    ]
    for name, flag in _safety_checks:
        if not flag:
            hard_blocks.append(f"{name}=False")

    # ── Determine outcome ─────────────────────────────────────────────────
    if hard_blocks:
        if any("execute" in hb for hb in hard_blocks):
            decision = BOUNDARY_UNSUPPORTED_EXECUTE
        else:
            decision = BOUNDARY_HARD_BLOCK
        ready = False
    elif missing:
        decision = BOUNDARY_MISSING_INPUTS
        ready = False
    elif mismatches:
        decision = BOUNDARY_MISMATCH
        ready = False
    elif boundary.command_mode == COMMAND_MODE_PLAN:
        decision = BOUNDARY_READY_FOR_PLAN
        ready = True
    elif boundary.command_mode == COMMAND_MODE_DRY_RUN:
        decision = BOUNDARY_READY_FOR_DRY_RUN
        ready = True
    else:
        decision = BOUNDARY_HARD_BLOCK
        ready = False

    # Build failure classifications
    for hb in hard_blocks:
        failures.append(hb)
    for m in missing:
        failures.append(f"missing:{m}")

    return ArtifactOnlyInvocationCommandBoundaryAssessment(
        assessment_id=assessment_id,
        boundary_id=boundary.boundary_id,
        phase_id=boundary.phase_id,
        task_id=boundary.task_id,
        command_mode=boundary.command_mode,
        ready=ready,
        decision=decision,
        hard_blocks=hard_blocks,
        warnings=warnings_list,
        missing_inputs=missing,
        mismatch_reasons=mismatches,
        failure_classifications=failures,
        execution_allowed=False,
        execute_supported=False,
        dry_run_only=True,
        broker_shell_gate_ready=(
            boundary.broker_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE)
            and bool(boundary.broker_decision)
            and boundary.shell_gate_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE)
            and bool(boundary.shell_gate_decision)
        ),
        output_quarantine_ready=bool(boundary.output_quarantine_path),
        audit_ready=bool(boundary.audit_path),
        timeout_ready=boundary.timeout_seconds > 0,
        evidence_chain_ready=(
            bool(boundary.prompt_artifact_path) and bool(boundary.prompt_artifact_digest)
            and bool(boundary.preflight_artifact_path) and bool(boundary.preflight_artifact_digest)
            and bool(boundary.runtime_evidence_path) and bool(boundary.runtime_evidence_digest)
            and bool(boundary.approval_artifact_path) and bool(boundary.approval_artifact_digest)
            and bool(boundary.invocation_plan_path) and bool(boundary.invocation_plan_digest)
        ),
        no_real_backend_invoked=True,
        no_adapter_executed=True,
        no_subprocess=True,
        no_network=True,
        no_repo_mutation=True,
        no_apply=True,
        no_patch_parsing=True,
        no_commit_push_authorization=True,
        no_telegram_inbound=True,
        created_at_utc=now,
    )


def _boundary_dir() -> Path:
    from pathlib import Path as _P
    return _P(_BOUNDARY_DIR)


def persist_artifact_only_invocation_command_boundary(
    boundary: ArtifactOnlyInvocationCommandBoundary,
) -> dict:
    import os
    d = _boundary_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not boundary.record_digest:
        boundary.record_digest = boundary.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{boundary.boundary_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(boundary.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(boundary.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": boundary.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_artifact_only_invocation_command_boundary(
    boundary: ArtifactOnlyInvocationCommandBoundary,
) -> dict:
    issues_list: list[str] = []
    if not boundary.boundary_id:
        issues_list.append("missing boundary_id")
    if not boundary.record_digest:
        issues_list.append("missing record_digest")
    if boundary.record_digest and boundary.compute_digest() != boundary.record_digest:
        issues_list.append("record_digest_mismatch")
    if boundary.schema_version != _BOUNDARY_SCHEMA_VERSION:
        issues_list.append(f"schema_version mismatch: {boundary.schema_version!r}")
    return {"valid": len(issues_list) == 0, "issues": issues_list}


def load_latest_artifact_only_invocation_command_boundary() -> (
    "ArtifactOnlyInvocationCommandBoundary | None"
):
    lp = _boundary_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyInvocationCommandBoundary.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


def persist_artifact_only_invocation_command_boundary_assessment(
    assessment: ArtifactOnlyInvocationCommandBoundaryAssessment,
) -> dict:
    import os
    d = _boundary_dir() / "assessments"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not assessment.record_digest:
        assessment.record_digest = assessment.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{assessment.assessment_id}.json"
        lp = d / "latest-assessment.json"
        fp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest-assessment.tmp"
        tmp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": assessment.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_artifact_only_invocation_command_boundary_assessment(
    assessment: ArtifactOnlyInvocationCommandBoundaryAssessment,
) -> dict:
    issues_list: list[str] = []
    if not assessment.assessment_id:
        issues_list.append("missing assessment_id")
    if not assessment.record_digest:
        issues_list.append("missing record_digest")
    if assessment.record_digest and assessment.compute_digest() != assessment.record_digest:
        issues_list.append("record_digest_mismatch")
    if assessment.execution_allowed:
        issues_list.append("execution_allowed must be False")
    if assessment.execute_supported:
        issues_list.append("execute_supported must be False")
    return {"valid": len(issues_list) == 0, "issues": issues_list}


def load_latest_artifact_only_invocation_command_boundary_assessment() -> (
    "ArtifactOnlyInvocationCommandBoundaryAssessment | None"
):
    lp = _boundary_dir() / "latest-assessment.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyInvocationCommandBoundaryAssessment.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None
