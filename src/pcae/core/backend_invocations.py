"""Backend registry and invocation request model — Phase 94B.

Data models for governed backend invocation. No backend execution,
no subprocess, no network calls.  Simulation/validation only.
"""

from __future__ import annotations

import json as _json
import uuid
from dataclasses import dataclass, field
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
