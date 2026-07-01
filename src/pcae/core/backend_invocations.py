"""Backend registry and invocation request model — Phase 94B.

Data models for governed backend invocation. No backend execution,
no subprocess, no network calls.  Simulation/validation only.
"""

from __future__ import annotations

import hashlib
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
    lp = _boundary_dir() / "assessments" / "latest-assessment.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyInvocationCommandBoundaryAssessment.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95O — Artifact-only invocation evidence chain bundle model
# ═══════════════════════════════════════════════════════════════════════════

_BUNDLE_SCHEMA_VERSION = "1.0"
_BUNDLE_DIR = ".pcae/evidence-chain-bundles"

BUNDLE_READY = "ready_for_dry_run_bundle"
BUNDLE_HARD_BLOCK = "hard_block"
BUNDLE_MISSING_ARTIFACTS = "missing_artifacts"
BUNDLE_MISMATCH = "mismatch"
BUNDLE_TAMPERED = "tampered"
BUNDLE_UNSUPPORTED_EXECUTE = "unsupported_execute"


@dataclass
class ArtifactOnlyInvocationEvidenceChainBundle:
    """Deterministic bundle grouping all evidence artifacts into one verifiable object.

    Model/validation only. No execution, no CLI, no orchestration.
    """

    bundle_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    adapter_id: str = ""
    command_mode: str = COMMAND_MODE_DRY_RUN
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
    broker_decision_digest: str = ""
    broker_decision: str = ""
    shell_gate_decision_id: str = ""
    shell_gate_decision_digest: str = ""
    shell_gate_decision: str = ""
    command_boundary_path: str = ""
    command_boundary_digest: str = ""
    command_boundary_assessment_path: str = ""
    command_boundary_assessment_digest: str = ""
    output_quarantine_path: str = ""
    audit_path: str = ""
    timeout_seconds: int = 0
    redaction_policy_id: str = ""
    operator_approval_reference: str = ""
    dry_run_only: bool = True
    execution_allowed: bool = False
    execute_supported: bool = False
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
    schema_version: str = _BUNDLE_SCHEMA_VERSION
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
    def from_dict(cls, data: dict) -> "ArtifactOnlyInvocationEvidenceChainBundle":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ArtifactOnlyInvocationEvidenceChainBundleAssessment:
    """Validation assessment for an evidence chain bundle."""

    assessment_id: str = ""
    bundle_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    ready: bool = False
    decision: str = ""
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_artifacts: list[str] = field(default_factory=list)
    mismatch_reasons: list[str] = field(default_factory=list)
    tamper_reasons: list[str] = field(default_factory=list)
    failure_classifications: list[str] = field(default_factory=list)
    evidence_chain_ready: bool = False
    command_boundary_ready: bool = False
    broker_shell_gate_ready: bool = False
    output_quarantine_ready: bool = False
    audit_ready: bool = False
    timeout_ready: bool = False
    redaction_ready: bool = False
    dry_run_only: bool = True
    execution_allowed: bool = False
    execute_supported: bool = False
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
    schema_version: str = _BUNDLE_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_artifacts"] = list(self.missing_artifacts)
        d["mismatch_reasons"] = list(self.mismatch_reasons)
        d["tamper_reasons"] = list(self.tamper_reasons)
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
    def from_dict(cls, data: dict) -> "ArtifactOnlyInvocationEvidenceChainBundleAssessment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def validate_artifact_only_invocation_evidence_chain_bundle(
    bundle: ArtifactOnlyInvocationEvidenceChainBundle,
) -> ArtifactOnlyInvocationEvidenceChainBundleAssessment:
    """Validate an evidence chain bundle against all 95O rules.

    Model-only — never executes, never invokes backends.
    """
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    assessment_id = f"eba-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    warnings_list: list[str] = []
    missing: list[str] = []
    mismatches: list[str] = []
    tampered: list[str] = []
    failures: list[str] = []

    if not bundle.bundle_id:
        hard_blocks.append("bundle_id_missing")
    if not bundle.phase_id:
        hard_blocks.append("phase_id_missing")
    if not bundle.task_id:
        hard_blocks.append("task_id_missing")
    if not bundle.backend_id:
        hard_blocks.append("backend_id_missing")
    if not bundle.adapter_id:
        hard_blocks.append("adapter_id_missing")

    # Artifact paths and digests
    _bundle_artifacts = [
        ("prompt_artifact", bundle.prompt_artifact_path, bundle.prompt_artifact_digest),
        ("preflight_artifact", bundle.preflight_artifact_path, bundle.preflight_artifact_digest),
        ("runtime_evidence", bundle.runtime_evidence_path, bundle.runtime_evidence_digest),
        ("approval_artifact", bundle.approval_artifact_path, bundle.approval_artifact_digest),
        ("invocation_plan", bundle.invocation_plan_path, bundle.invocation_plan_digest),
    ]
    for name, path, digest in _bundle_artifacts:
        if not path:
            hard_blocks.append(f"{name}_path_missing")
        if not digest:
            hard_blocks.append(f"{name}_digest_missing")

    # Broker/shell-gate
    if not bundle.broker_decision_id:
        hard_blocks.append("broker_decision_id_missing")
    if not bundle.broker_decision:
        hard_blocks.append("broker_decision_missing")
    elif bundle.broker_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hard_blocks.append(f"broker_decision:{bundle.broker_decision}")

    if not bundle.shell_gate_decision_id:
        hard_blocks.append("shell_gate_decision_id_missing")
    if not bundle.shell_gate_decision:
        hard_blocks.append("shell_gate_decision_missing")
    elif bundle.shell_gate_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hard_blocks.append(f"shell_gate_decision:{bundle.shell_gate_decision}")

    # Command boundary
    if not bundle.command_boundary_path:
        hard_blocks.append("command_boundary_path_missing")
    if not bundle.command_boundary_digest:
        hard_blocks.append("command_boundary_digest_missing")
    if not bundle.command_boundary_assessment_path:
        hard_blocks.append("command_boundary_assessment_path_missing")
    if not bundle.command_boundary_assessment_digest:
        hard_blocks.append("command_boundary_assessment_digest_missing")

    # Paths
    if not bundle.output_quarantine_path:
        hard_blocks.append("output_quarantine_path_missing")
    if not bundle.audit_path:
        hard_blocks.append("audit_path_missing")
    if bundle.timeout_seconds <= 0:
        hard_blocks.append("timeout_missing_or_invalid")
    if not bundle.redaction_policy_id:
        hard_blocks.append("redaction_policy_id_missing")
    if not bundle.operator_approval_reference:
        hard_blocks.append("operator_approval_reference_missing")

    # Command mode
    if bundle.command_mode not in VALID_COMMAND_MODES:
        hard_blocks.append(f"unknown_command_mode:{bundle.command_mode}")
    if bundle.command_mode == COMMAND_MODE_EXECUTE_RESERVED:
        hard_blocks.append("execute_reserved_not_supported")
    if bundle.execution_allowed:
        hard_blocks.append("execution_allowed=True")
    if bundle.execute_supported:
        hard_blocks.append("execute_supported=True")
    if not bundle.dry_run_only:
        hard_blocks.append("dry_run_only=False")

    # Safety flags
    _safety = [
        ("no_real_backend_invoked", bundle.no_real_backend_invoked),
        ("no_adapter_executed", bundle.no_adapter_executed),
        ("no_subprocess", bundle.no_subprocess),
        ("no_network", bundle.no_network),
        ("no_repo_mutation", bundle.no_repo_mutation),
        ("no_apply", bundle.no_apply),
        ("no_patch_parsing", bundle.no_patch_parsing),
        ("no_commit_push_authorization", bundle.no_commit_push_authorization),
        ("no_telegram_inbound", bundle.no_telegram_inbound),
    ]
    for name, flag in _safety:
        if not flag:
            hard_blocks.append(f"{name}=False")

    # Determine outcome
    if hard_blocks:
        if any("execute" in hb for hb in hard_blocks):
            decision = BUNDLE_UNSUPPORTED_EXECUTE
        else:
            decision = BUNDLE_HARD_BLOCK
        ready = False
    elif missing:
        decision = BUNDLE_MISSING_ARTIFACTS
        ready = False
    elif mismatches:
        decision = BUNDLE_MISMATCH
        ready = False
    elif tampered:
        decision = BUNDLE_TAMPERED
        ready = False
    else:
        decision = BUNDLE_READY
        ready = True

    for hb in hard_blocks:
        failures.append(hb)
    for m in missing:
        failures.append(f"missing:{m}")

    return ArtifactOnlyInvocationEvidenceChainBundleAssessment(
        assessment_id=assessment_id,
        bundle_id=bundle.bundle_id,
        phase_id=bundle.phase_id,
        task_id=bundle.task_id,
        ready=ready, decision=decision,
        hard_blocks=hard_blocks, warnings=warnings_list,
        missing_artifacts=missing, mismatch_reasons=mismatches, tamper_reasons=tampered,
        failure_classifications=failures,
        evidence_chain_ready=(bool(bundle.prompt_artifact_path) and bool(bundle.prompt_artifact_digest) and bool(bundle.preflight_artifact_path) and bool(bundle.preflight_artifact_digest) and bool(bundle.runtime_evidence_path) and bool(bundle.runtime_evidence_digest) and bool(bundle.approval_artifact_path) and bool(bundle.approval_artifact_digest) and bool(bundle.invocation_plan_path) and bool(bundle.invocation_plan_digest)),
        command_boundary_ready=(bool(bundle.command_boundary_path) and bool(bundle.command_boundary_digest) and bool(bundle.command_boundary_assessment_path) and bool(bundle.command_boundary_assessment_digest)),
        broker_shell_gate_ready=(bool(bundle.broker_decision) and bundle.broker_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE) and bool(bundle.shell_gate_decision) and bundle.shell_gate_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE)),
        output_quarantine_ready=bool(bundle.output_quarantine_path),
        audit_ready=bool(bundle.audit_path),
        timeout_ready=bundle.timeout_seconds > 0,
        redaction_ready=bool(bundle.redaction_policy_id),
        execution_allowed=False, execute_supported=False, dry_run_only=True,
        no_real_backend_invoked=True, no_adapter_executed=True,
        no_subprocess=True, no_network=True, no_repo_mutation=True,
        no_apply=True, no_patch_parsing=True,
        no_commit_push_authorization=True, no_telegram_inbound=True,
        schema_version=_BUNDLE_SCHEMA_VERSION, created_at_utc=now,
    )


def _bundle_dir() -> Path:
    from pathlib import Path as _P
    return _P(_BUNDLE_DIR)


def persist_evidence_chain_bundle(bundle: ArtifactOnlyInvocationEvidenceChainBundle) -> dict:
    import os
    d = _bundle_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    if not bundle.record_digest:
        bundle.record_digest = bundle.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{bundle.bundle_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(bundle.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(bundle.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "record_digest": bundle.record_digest}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_evidence_chain_bundle(bundle: ArtifactOnlyInvocationEvidenceChainBundle) -> dict:
    issues: list[str] = []
    if not bundle.bundle_id:
        issues.append("missing bundle_id")
    if not bundle.record_digest:
        issues.append("missing record_digest")
    if bundle.record_digest and bundle.compute_digest() != bundle.record_digest:
        issues.append("record_digest_mismatch")
    return {"valid": len(issues) == 0, "issues": issues}


def load_latest_evidence_chain_bundle() -> ArtifactOnlyInvocationEvidenceChainBundle | None:
    lp = _bundle_dir() / "latest.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyInvocationEvidenceChainBundle.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


def persist_evidence_chain_bundle_assessment(assessment: ArtifactOnlyInvocationEvidenceChainBundleAssessment) -> dict:
    import os
    d = _bundle_dir() / "assessments"
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


def verify_evidence_chain_bundle_assessment(assessment: ArtifactOnlyInvocationEvidenceChainBundleAssessment) -> dict:
    issues: list[str] = []
    if not assessment.assessment_id:
        issues.append("missing assessment_id")
    if not assessment.record_digest:
        issues.append("missing record_digest")
    if assessment.record_digest and assessment.compute_digest() != assessment.record_digest:
        issues.append("record_digest_mismatch")
    if assessment.execution_allowed:
        issues.append("execution_allowed must be False")
    return {"valid": len(issues) == 0, "issues": issues}


def load_latest_evidence_chain_bundle_assessment() -> ArtifactOnlyInvocationEvidenceChainBundleAssessment | None:
    lp = _bundle_dir() / "assessments" / "latest-assessment.json"
    if not lp.exists():
        return None
    try:
        data = _json.loads(lp.read_text())
        return ArtifactOnlyInvocationEvidenceChainBundleAssessment.from_dict(data) if isinstance(data, dict) and data else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95S — Artifact-only dry-run orchestration model
# ═══════════════════════════════════════════════════════════════════════════

_ORCH_SCHEMA_VERSION = "1.0"
_ORCH_DIR = ".pcae/orchestration-plans"

ORCH_READY = "ready_for_dry_run_orchestration"
ORCH_HARD_BLOCK = "hard_block"
ORCH_MISSING_INPUTS = "missing_inputs"
ORCH_MISMATCH = "mismatch"
ORCH_TAMPERED = "tampered"
ORCH_UNSUPPORTED_EXECUTE = "unsupported_execute"

# ── Ordered step names ────────────────────────────────────────────────────

ORCH_STEP_NAMES: tuple[str, ...] = (
    "load_bundle",
    "verify_bundle_digest",
    "validate_bundle",
    "load_boundary_assessment",
    "verify_boundary_assessment",
    "aggregate_broker_shell_gate",
    "verify_output_quarantine",
    "verify_audit_path",
    "verify_timeout",
    "verify_redaction_policy",
    "verify_no_execution_flags",
    "produce_dry_run_summary",
)


@dataclass
class ArtifactOnlyDryRunOrchestrationStep:
    """A single step in an orchestration plan."""

    step_id: str = ""
    step_name: str = ""
    step_order: int = 0
    required: bool = True
    input_refs: list[str] = field(default_factory=list)
    expected_decision: str = ""
    hard_block_on_failure: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["input_refs"] = list(self.input_refs)
        return d


@dataclass
class ArtifactOnlyDryRunOrchestrationStepResult:
    """Result of executing a single orchestration step (model-only)."""

    step_id: str = ""
    step_name: str = ""
    step_order: int = 0
    decision: str = ""
    ready: bool = False
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    mismatch_reasons: list[str] = field(default_factory=list)
    failure_classifications: list[str] = field(default_factory=list)
    no_execution_confirmed: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_inputs"] = list(self.missing_inputs)
        d["mismatch_reasons"] = list(self.mismatch_reasons)
        d["failure_classifications"] = list(self.failure_classifications)
        return d


@dataclass
class ArtifactOnlyDryRunOrchestrationPlan:
    """Orchestration plan: sequences existing dry-run steps and references
    bundle/boundary/demo artifacts. Model/validation only — no execution.
    """

    orchestration_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    adapter_id: str = ""
    bundle_id: str = ""
    bundle_path: str = ""
    bundle_digest: str = ""
    bundle_assessment_id: str = ""
    bundle_assessment_path: str = ""
    bundle_assessment_digest: str = ""
    command_boundary_id: str = ""
    command_boundary_assessment_id: str = ""
    demo_id: str = ""
    demo_assessment_id: str = ""
    ordered_steps: list[ArtifactOnlyDryRunOrchestrationStep] = field(default_factory=list)
    expected_decision: str = ORCH_READY
    output_quarantine_path: str = ""
    audit_path: str = ""
    timeout_seconds: int = 0
    redaction_policy_id: str = ""
    dry_run_only: bool = True
    execution_allowed: bool = False
    execute_supported: bool = False
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
    schema_version: str = _ORCH_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__
             if f != "ordered_steps"}
        d["ordered_steps"] = [s.to_dict() for s in self.ordered_steps]
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactOnlyDryRunOrchestrationPlan":
        steps_data = data.pop("ordered_steps", []) or []
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "ordered_steps"})
        plan.ordered_steps = [ArtifactOnlyDryRunOrchestrationStep(**{k2: v2 for k2, v2 in s.items() if k2 in ArtifactOnlyDryRunOrchestrationStep.__dataclass_fields__}) for s in steps_data if isinstance(s, dict)]
        return plan


@dataclass
class ArtifactOnlyDryRunOrchestrationAssessment:
    """Assessment for an orchestration plan. Aggregates step results."""

    assessment_id: str = ""
    orchestration_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    ready: bool = False
    decision: str = ""
    step_results: list[ArtifactOnlyDryRunOrchestrationStepResult] = field(default_factory=list)
    cumulative_hard_blocks: list[str] = field(default_factory=list)
    cumulative_warnings: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    mismatch_reasons: list[str] = field(default_factory=list)
    failure_classifications: list[str] = field(default_factory=list)
    evidence_chain_ready: bool = False
    bundle_ready: bool = False
    command_boundary_ready: bool = False
    broker_shell_gate_ready: bool = False
    output_quarantine_ready: bool = False
    audit_ready: bool = False
    timeout_ready: bool = False
    redaction_ready: bool = False
    dry_run_summary_ready: bool = False
    dry_run_only: bool = True
    execution_allowed: bool = False
    execute_supported: bool = False
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
    schema_version: str = _ORCH_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__
             if f != "step_results"}
        d["step_results"] = [s.to_dict() for s in self.step_results]
        d["cumulative_hard_blocks"] = list(self.cumulative_hard_blocks)
        d["cumulative_warnings"] = list(self.cumulative_warnings)
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
    def from_dict(cls, data: dict) -> "ArtifactOnlyDryRunOrchestrationAssessment":
        sr_data = data.pop("step_results", []) or []
        a = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "step_results"})
        a.step_results = [ArtifactOnlyDryRunOrchestrationStepResult(**{k2: v2 for k2, v2 in s.items() if k2 in ArtifactOnlyDryRunOrchestrationStepResult.__dataclass_fields__}) for s in sr_data if isinstance(s, dict)]
        return a


def validate_artifact_only_dry_run_orchestration_plan(
    plan: ArtifactOnlyDryRunOrchestrationPlan,
) -> ArtifactOnlyDryRunOrchestrationAssessment:
    """Validate an orchestration plan. Model-only — never executes."""
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    aid = f"oa-{_uuid.uuid4().hex[:12]}"

    hard_blocks: list[str] = []
    missing: list[str] = []
    step_results: list[ArtifactOnlyDryRunOrchestrationStepResult] = []

    if not plan.orchestration_id:
        hard_blocks.append("orchestration_id_missing")
    if not plan.phase_id:
        hard_blocks.append("phase_id_missing")
    if not plan.task_id:
        hard_blocks.append("task_id_missing")

    # Bundle references
    if not plan.bundle_path:
        hard_blocks.append("bundle_path_missing")
    if not plan.bundle_digest:
        hard_blocks.append("bundle_digest_missing")
    if not plan.bundle_assessment_path:
        hard_blocks.append("bundle_assessment_path_missing")
    if not plan.bundle_assessment_digest:
        hard_blocks.append("bundle_assessment_digest_missing")

    # Paths
    if not plan.output_quarantine_path:
        hard_blocks.append("output_quarantine_path_missing")
    if not plan.audit_path:
        hard_blocks.append("audit_path_missing")
    if plan.timeout_seconds <= 0:
        hard_blocks.append("timeout_missing_or_invalid")
    if not plan.redaction_policy_id:
        hard_blocks.append("redaction_policy_id_missing")

    # Safety flags
    _orch_safety = [
        ("dry_run_only", plan.dry_run_only),
        ("execution_allowed must be False", not plan.execution_allowed),
        ("execute_supported must be False", not plan.execute_supported),
        ("no_real_backend_invoked", plan.no_real_backend_invoked),
        ("no_adapter_executed", plan.no_adapter_executed),
        ("no_subprocess", plan.no_subprocess),
        ("no_network", plan.no_network),
        ("no_repo_mutation", plan.no_repo_mutation),
        ("no_apply", plan.no_apply),
        ("no_patch_parsing", plan.no_patch_parsing),
        ("no_commit_push_authorization", plan.no_commit_push_authorization),
        ("no_telegram_inbound", plan.no_telegram_inbound),
    ]
    for name, flag in _orch_safety:
        if not flag:
            hard_blocks.append(f"{name}=False" if flag is False else f"{name}=True")

    # Ordered steps
    if not plan.ordered_steps:
        hard_blocks.append("ordered_steps_missing")
    else:
        seen_orders: set[int] = set()
        seen_names: set[str] = set()
        for step in plan.ordered_steps:
            if not step.step_name or step.step_name not in ORCH_STEP_NAMES:
                hard_blocks.append(f"unknown_step:{step.step_name}")
            if step.step_order in seen_orders:
                hard_blocks.append(f"duplicate_step_order:{step.step_order}")
            seen_orders.add(step.step_order)
            if step.step_name in seen_names:
                hard_blocks.append(f"duplicate_step_name:{step.step_name}")
            seen_names.add(step.step_name)
            # Build step result
            sr = ArtifactOnlyDryRunOrchestrationStepResult(
                step_id=step.step_id, step_name=step.step_name,
                step_order=step.step_order, ready=True,
                decision="ready", no_execution_confirmed=True,
            )
            if not step.step_id:
                sr.hard_blocks.append("step_id_missing")
            step_results.append(sr)
        # Check required steps present
        for req_name in ORCH_STEP_NAMES:
            if req_name not in seen_names:
                hard_blocks.append(f"missing_required_step:{req_name}")
        # Check order is sequential
        if seen_orders and max(seen_orders) != len(plan.ordered_steps) - 1:
            hard_blocks.append("steps_not_sequential")

    # Determine outcome
    all_hard_blocks = list(hard_blocks)
    if any("execute" in hb.lower() for hb in all_hard_blocks):
        decision = ORCH_UNSUPPORTED_EXECUTE
    elif hard_blocks:
        decision = ORCH_HARD_BLOCK
    elif missing:
        decision = ORCH_MISSING_INPUTS
    else:
        decision = ORCH_READY

    failures = list(all_hard_blocks)
    for m in missing:
        failures.append(f"missing:{m}")

    return ArtifactOnlyDryRunOrchestrationAssessment(
        assessment_id=aid, orchestration_id=plan.orchestration_id,
        phase_id=plan.phase_id, task_id=plan.task_id,
        ready=(decision == ORCH_READY), decision=decision,
        step_results=step_results,
        cumulative_hard_blocks=all_hard_blocks,
        missing_inputs=missing,
        failure_classifications=failures,
        evidence_chain_ready=bool(plan.bundle_path and plan.bundle_digest),
        bundle_ready=bool(plan.bundle_path and plan.bundle_assessment_path),
        command_boundary_ready=bool(plan.command_boundary_id),
        broker_shell_gate_ready=True,
        output_quarantine_ready=bool(plan.output_quarantine_path),
        audit_ready=bool(plan.audit_path),
        timeout_ready=plan.timeout_seconds > 0,
        redaction_ready=bool(plan.redaction_policy_id),
        dry_run_summary_ready=(decision == ORCH_READY),
        dry_run_only=True, execution_allowed=False, execute_supported=False,
        no_real_backend_invoked=True, no_adapter_executed=True,
        no_subprocess=True, no_network=True, no_repo_mutation=True,
        no_apply=True, no_patch_parsing=True,
        no_commit_push_authorization=True, no_telegram_inbound=True,
        created_at_utc=now,
    )


def _orch_dir() -> Path:
    from pathlib import Path as _P
    return _P(_ORCH_DIR)


def persist_orchestration_plan(plan: ArtifactOnlyDryRunOrchestrationPlan) -> dict:
    import os
    d = _orch_dir()
    try: d.mkdir(parents=True, exist_ok=True)
    except Exception as exc: return {"status": "failed", "error": str(exc)}
    if not plan.record_digest: plan.record_digest = plan.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{plan.orchestration_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_orchestration_plan(plan: ArtifactOnlyDryRunOrchestrationPlan) -> dict:
    issues: list[str] = []
    if not plan.orchestration_id: issues.append("missing orchestration_id")
    if not plan.record_digest: issues.append("missing record_digest")
    if plan.record_digest and plan.compute_digest() != plan.record_digest:
        issues.append("record_digest_mismatch")
    return {"valid": len(issues) == 0, "issues": issues}


def persist_orchestration_assessment(assessment: ArtifactOnlyDryRunOrchestrationAssessment) -> dict:
    import os
    d = _orch_dir() / "assessments"
    try: d.mkdir(parents=True, exist_ok=True)
    except Exception as exc: return {"status": "failed", "error": str(exc)}
    if not assessment.record_digest: assessment.record_digest = assessment.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{assessment.assessment_id}.json"
        lp = d / "latest-assessment.json"
        fp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest-assessment.tmp"
        tmp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def verify_orchestration_assessment(assessment: ArtifactOnlyDryRunOrchestrationAssessment) -> dict:
    issues: list[str] = []
    if not assessment.assessment_id: issues.append("missing assessment_id")
    if not assessment.record_digest: issues.append("missing record_digest")
    if assessment.record_digest and assessment.compute_digest() != assessment.record_digest:
        issues.append("record_digest_mismatch")
    if assessment.execution_allowed: issues.append("execution_allowed must be False")
    return {"valid": len(issues) == 0, "issues": issues}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 96B — Execution-adjacent plan model
# ═══════════════════════════════════════════════════════════════════════════

_EA_SCHEMA_VERSION = "1.0"
_EA_DIR = ".pcae/execution-adjacent-plans"

EA_READY = "ready_for_execution_adjacent_dry_run"
EA_HARD_BLOCK = "hard_block"
EA_MISSING_FIELDS = "missing_fields"
EA_MISMATCH = "mismatch"
EA_TAMPERED = "tampered"
EA_UNSUPPORTED_EXECUTION = "unsupported_execution"
EA_UNSAFE_CAPABILITY = "unsafe_capability_requested"


@dataclass
class ExecutionAdjacentPlan:
    """Non-executing execution-adjacent plan. Models intent without execution."""

    plan_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    backend_id: str = ""
    adapter_id: str = ""
    orchestration_id: str = ""
    command_identity_id: str = ""
    command_name: str = ""
    command_path: str = ""
    command_digest: str = ""
    command_args: list[str] = field(default_factory=list)
    command_env_digest: str = ""
    working_directory: str = ""
    timeout_policy_id: str = ""
    timeout_seconds: int = 0
    kill_policy_id: str = ""
    output_quarantine_id: str = ""
    output_quarantine_path: str = ""
    audit_record_id: str = ""
    audit_path: str = ""
    rollback_linkage_id: str = ""
    approval_artifact_id: str = ""
    approval_actor_id: str = ""
    broker_decision_id: str = ""
    broker_decision: str = ""
    shell_gate_decision_id: str = ""
    shell_gate_decision: str = ""
    repo_state_id: str = ""
    repo_clean: bool = True
    origin_main_head_count: int = 0
    task_scope_status: str = "in_scope"
    dry_run_only: bool = True
    execution_allowed: bool = False
    subprocess_allowed: bool = False
    shell_allowed: bool = False
    network_allowed: bool = False
    backend_invocation_allowed: bool = False
    adapter_execution_allowed: bool = False
    auto_apply_allowed: bool = False
    patch_parsing_allowed: bool = False
    commit_push_authorization_allowed: bool = False
    telegram_inbound_allowed: bool = False
    live_runtime_inspection_allowed: bool = False
    command_discovery_allowed: bool = False
    created_at_utc: str = ""
    schema_version: str = _EA_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["command_args"] = list(self.command_args)
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionAdjacentPlan":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ExecutionAdjacentPlanAssessment:
    """Validation assessment for an execution-adjacent plan."""

    assessment_id: str = ""
    plan_id: str = ""
    phase_id: str = ""
    task_id: str = ""
    ready: bool = False
    decision: str = ""
    hard_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    mismatch_reasons: list[str] = field(default_factory=list)
    tamper_reasons: list[str] = field(default_factory=list)
    failure_classifications: list[str] = field(default_factory=list)
    command_identity_ready: bool = False
    timeout_policy_ready: bool = False
    output_quarantine_ready: bool = False
    audit_ready: bool = False
    rollback_linkage_ready: bool = False
    approval_ready: bool = False
    broker_ready: bool = False
    shell_gate_ready: bool = False
    repo_state_ready: bool = False
    task_scope_ready: bool = False
    dry_run_only: bool = True
    execution_allowed: bool = False
    subprocess_allowed: bool = False
    shell_allowed: bool = False
    network_allowed: bool = False
    backend_invocation_allowed: bool = False
    adapter_execution_allowed: bool = False
    auto_apply_allowed: bool = False
    patch_parsing_allowed: bool = False
    commit_push_authorization_allowed: bool = False
    telegram_inbound_allowed: bool = False
    live_runtime_inspection_allowed: bool = False
    command_discovery_allowed: bool = False
    created_at_utc: str = ""
    schema_version: str = _EA_SCHEMA_VERSION
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["hard_blocks"] = list(self.hard_blocks)
        d["warnings"] = list(self.warnings)
        d["missing_fields"] = list(self.missing_fields)
        d["mismatch_reasons"] = list(self.mismatch_reasons)
        d["tamper_reasons"] = list(self.tamper_reasons)
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
    def from_dict(cls, data: dict) -> "ExecutionAdjacentPlanAssessment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def validate_execution_adjacent_plan(
    plan: ExecutionAdjacentPlan,
) -> ExecutionAdjacentPlanAssessment:
    """Validate execution-adjacent plan. Model-only — never executes."""
    import uuid as _uuid
    now = datetime.now(timezone.utc).isoformat()
    aid = f"ea-{_uuid.uuid4().hex[:12]}"
    hb: list[str] = []
    missing: list[str] = []

    if not plan.plan_id: hb.append("plan_id_missing")
    if not plan.phase_id: hb.append("phase_id_missing")
    if not plan.task_id: hb.append("task_id_missing")
    if not plan.backend_id: hb.append("backend_id_missing")
    if not plan.adapter_id: hb.append("adapter_id_missing")

    # Command identity
    if not plan.command_name: hb.append("command_name_missing")
    if not plan.command_path: hb.append("command_path_missing")
    if not plan.command_digest: hb.append("command_digest_missing")
    if not plan.command_env_digest: hb.append("command_env_digest_missing")
    if not plan.working_directory: hb.append("working_directory_missing")

    # Policies/paths
    if not plan.timeout_policy_id: hb.append("timeout_policy_id_missing")
    if plan.timeout_seconds <= 0: hb.append("timeout_seconds_missing_or_invalid")
    if not plan.kill_policy_id: hb.append("kill_policy_id_missing")
    if not plan.output_quarantine_id: hb.append("output_quarantine_id_missing")
    if not plan.output_quarantine_path: hb.append("output_quarantine_path_missing")
    if not plan.audit_record_id: hb.append("audit_record_id_missing")
    if not plan.audit_path: hb.append("audit_path_missing")
    if not plan.rollback_linkage_id: hb.append("rollback_linkage_id_missing")
    if not plan.approval_artifact_id: hb.append("approval_artifact_id_missing")
    if not plan.approval_actor_id: hb.append("approval_actor_id_missing")

    # Broker/shell-gate
    if not plan.broker_decision_id: hb.append("broker_decision_id_missing")
    if not plan.broker_decision: hb.append("broker_decision_missing")
    elif plan.broker_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hb.append(f"broker_decision:{plan.broker_decision}")
    if not plan.shell_gate_decision_id: hb.append("shell_gate_decision_id_missing")
    if not plan.shell_gate_decision: hb.append("shell_gate_decision_missing")
    elif plan.shell_gate_decision in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE):
        hb.append(f"shell_gate_decision:{plan.shell_gate_decision}")

    # Repo/task
    if not plan.repo_clean: hb.append("repo_clean=False")
    if plan.origin_main_head_count != 0: hb.append("origin_main_head_count!=0")
    if plan.task_scope_status != "in_scope": hb.append(f"task_scope_status:{plan.task_scope_status}")

    # Dry-run
    if not plan.dry_run_only: hb.append("dry_run_only=False")

    # Capability flags — all must be False
    _cap_flags = [
        ("execution_allowed", plan.execution_allowed),
        ("subprocess_allowed", plan.subprocess_allowed),
        ("shell_allowed", plan.shell_allowed),
        ("network_allowed", plan.network_allowed),
        ("backend_invocation_allowed", plan.backend_invocation_allowed),
        ("adapter_execution_allowed", plan.adapter_execution_allowed),
        ("auto_apply_allowed", plan.auto_apply_allowed),
        ("patch_parsing_allowed", plan.patch_parsing_allowed),
        ("commit_push_authorization_allowed", plan.commit_push_authorization_allowed),
        ("telegram_inbound_allowed", plan.telegram_inbound_allowed),
        ("live_runtime_inspection_allowed", plan.live_runtime_inspection_allowed),
        ("command_discovery_allowed", plan.command_discovery_allowed),
    ]
    for name, flag in _cap_flags:
        if flag:
            hb.append(f"{name}=True")

    failures = list(hb)
    for m in missing: failures.append(f"missing:{m}")
    if any("execution_allowed" in f or "subprocess_allowed" in f for f in hb):
        decision = EA_UNSAFE_CAPABILITY
    elif hb: decision = EA_HARD_BLOCK
    elif missing: decision = EA_MISSING_FIELDS
    else: decision = EA_READY

    return ExecutionAdjacentPlanAssessment(
        assessment_id=aid, plan_id=plan.plan_id, phase_id=plan.phase_id, task_id=plan.task_id,
        ready=(decision == EA_READY), decision=decision,
        hard_blocks=hb, missing_fields=missing, failure_classifications=failures,
        command_identity_ready=bool(plan.command_name and plan.command_path and plan.command_digest),
        timeout_policy_ready=bool(plan.timeout_policy_id and plan.timeout_seconds > 0),
        output_quarantine_ready=bool(plan.output_quarantine_id and plan.output_quarantine_path),
        audit_ready=bool(plan.audit_record_id and plan.audit_path),
        rollback_linkage_ready=bool(plan.rollback_linkage_id),
        approval_ready=bool(plan.approval_artifact_id and plan.approval_actor_id),
        broker_ready=(bool(plan.broker_decision) and plan.broker_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE)),
        shell_gate_ready=(bool(plan.shell_gate_decision) and plan.shell_gate_decision not in (DECISION_DENY, DECISION_HARD_BLOCK, DECISION_MISSING_EVIDENCE)),
        repo_state_ready=plan.repo_clean and plan.origin_main_head_count == 0,
        task_scope_ready=(plan.task_scope_status == "in_scope"),
        dry_run_only=True, execution_allowed=False, subprocess_allowed=False,
        shell_allowed=False, network_allowed=False, backend_invocation_allowed=False,
        adapter_execution_allowed=False, auto_apply_allowed=False, patch_parsing_allowed=False,
        commit_push_authorization_allowed=False, telegram_inbound_allowed=False,
        live_runtime_inspection_allowed=False, command_discovery_allowed=False,
        created_at_utc=now,
    )


def _ea_dir() -> Path:
    from pathlib import Path as _P
    return _P(_EA_DIR)


def persist_execution_adjacent_plan(plan: ExecutionAdjacentPlan) -> dict:
    import os
    d = _ea_dir()
    try: d.mkdir(parents=True, exist_ok=True)
    except Exception as exc: return {"status": "failed", "error": str(exc)}
    if not plan.record_digest: plan.record_digest = plan.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{plan.plan_id}.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(plan.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp)}
    except Exception as exc: return {"status": "failed", "error": str(exc)}


def verify_execution_adjacent_plan(plan: ExecutionAdjacentPlan) -> dict:
    issues: list[str] = []
    if not plan.plan_id: issues.append("missing plan_id")
    if not plan.record_digest: issues.append("missing record_digest")
    if plan.record_digest and plan.compute_digest() != plan.record_digest: issues.append("record_digest_mismatch")
    return {"valid": len(issues) == 0, "issues": issues}


def persist_execution_adjacent_assessment(assessment: ExecutionAdjacentPlanAssessment) -> dict:
    import os
    d = _ea_dir() / "assessments"
    try: d.mkdir(parents=True, exist_ok=True)
    except Exception as exc: return {"status": "failed", "error": str(exc)}
    if not assessment.record_digest: assessment.record_digest = assessment.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-{assessment.assessment_id}.json"
        lp = d / "latest-assessment.json"
        fp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest-assessment.tmp"
        tmp.write_text(_json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp)}
    except Exception as exc: return {"status": "failed", "error": str(exc)}


def verify_execution_adjacent_assessment(assessment: ExecutionAdjacentPlanAssessment) -> dict:
    issues: list[str] = []
    if not assessment.assessment_id: issues.append("missing assessment_id")
    if not assessment.record_digest: issues.append("missing record_digest")
    if assessment.record_digest and assessment.compute_digest() != assessment.record_digest: issues.append("record_digest_mismatch")
    if assessment.execution_allowed: issues.append("execution_allowed must be False")
    return {"valid": len(issues) == 0, "issues": issues}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 96H — Execution-unavailable boundary proof
# ═══════════════════════════════════════════════════════════════════════════

_BP_SCHEMA_VERSION = "1.0"
_BP_DIR = ".pcae/execution-boundary-proof"


@dataclass
class ExecutionBoundaryProof:
    """Machine-readable proof that execution is unavailable.

    Evidence artifact only — does not authorize anything.
    """

    phase_id: str = ""
    schema_version: str = _BP_SCHEMA_VERSION
    generated_at_utc: str = ""
    connected_chain_artifacts_checked: bool = True
    execution_available: bool = False
    backend_invocation_available: bool = False
    adapter_execution_available: bool = False
    subprocess_execution_available: bool = False
    shell_execution_available: bool = False
    network_call_available: bool = False
    telegram_inbound_available: bool = False
    telegram_polling_available: bool = False
    remote_shell_available: bool = False
    run_command_available: bool = False
    enforcement_available: bool = False
    automatic_apply_available: bool = False
    apply_execution_available: bool = False
    patch_parsing_available: bool = False
    commit_authorization_available: bool = False
    push_authorization_available: bool = False
    real_ai_backend_calls_available: bool = False
    executable_artifact_invocation_available: bool = False
    execution_enablement_flag_present: bool = False
    execution_availability_toggle_present: bool = False
    proof_status: str = "execution_unavailable"
    proof_checks: list[str] = field(default_factory=list)
    no_execution: bool = True
    simulation_only: bool = True
    record_digest: str = ""

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["proof_checks"] = list(self.proof_checks)
        if not include_digest:
            d.pop("record_digest", None)
        return d

    def compute_digest(self) -> str:
        import hashlib
        d = self.to_dict(include_digest=False)
        canonical = _json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionBoundaryProof":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_execution_boundary_proof() -> ExecutionBoundaryProof:
    """Generate a deterministic proof that execution is unavailable."""
    now = datetime.now(timezone.utc).isoformat()
    checks = [
        "no_subprocess_import_in_connected_path",
        "no_shell_execution_in_connected_path",
        "no_network_call_in_connected_path",
        "no_backend_invocation_in_connected_path",
        "no_adapter_execution_in_connected_path",
        "no_telegram_inbound_in_connected_path",
        "no_apply_execution_in_connected_path",
        "no_patch_parsing_in_connected_path",
        "no_commit_authorization_in_connected_path",
        "no_push_authorization_in_connected_path",
        "all_execution_capability_flags_false",
        "execute_command_unavailable",
        "dry_run_only_mode_active",
        "finalization_gate_active",
        "connected_chain_non_executing",
    ]
    proof = ExecutionBoundaryProof(
        phase_id="96H", generated_at_utc=now,
        proof_checks=checks,
        proof_status="execution_unavailable",
    )
    proof.record_digest = proof.compute_digest()
    return proof


def _bp_dir() -> Path:
    from pathlib import Path as _P
    return _P(_BP_DIR)


def persist_execution_boundary_proof(proof: ExecutionBoundaryProof) -> dict:
    import os
    d = _bp_dir()
    try: d.mkdir(parents=True, exist_ok=True)
    except Exception as exc: return {"status": "failed", "error": str(exc)}
    if not proof.record_digest: proof.record_digest = proof.compute_digest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    try:
        fp = d / f"{ts}-96H.json"
        lp = d / "latest.json"
        fp.write_text(_json.dumps(proof.to_dict(), indent=2, sort_keys=True))
        tmp = d / ".latest.tmp"
        tmp.write_text(_json.dumps(proof.to_dict(), indent=2, sort_keys=True))
        os.replace(str(tmp), str(lp))
        return {"status": "written", "path": str(fp), "latest": str(lp)}
    except Exception as exc: return {"status": "failed", "error": str(exc)}


def load_latest_execution_boundary_proof() -> ExecutionBoundaryProof | None:
    lp = _bp_dir() / "latest.json"
    if not lp.exists(): return None
    try:
        return ExecutionBoundaryProof.from_dict(_json.loads(lp.read_text()))
    except Exception: return None


def verify_execution_boundary_proof(proof: ExecutionBoundaryProof) -> dict:
    issues: list[str] = []
    if not proof.record_digest: issues.append("missing record_digest")
    elif proof.record_digest != proof.compute_digest(): issues.append("record_digest_mismatch")
    if proof.execution_available: issues.append("execution_available must be False")
    if proof.backend_invocation_available: issues.append("backend_invocation_available must be False")
    if proof.subprocess_execution_available: issues.append("subprocess_execution_available must be False")
    if proof.shell_execution_available: issues.append("shell_execution_available must be False")
    if proof.network_call_available: issues.append("network_call_available must be False")
    if proof.telegram_inbound_available: issues.append("telegram_inbound_available must be False")
    if proof.apply_execution_available: issues.append("apply_execution_available must be False")
    if proof.commit_authorization_available: issues.append("commit_authorization_available must be False")
    if proof.push_authorization_available: issues.append("push_authorization_available must be False")
    if not proof.no_execution: issues.append("no_execution must be True")
    return {"valid": len(issues) == 0, "issues": issues}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 97A — Execution readiness model constants
# ═══════════════════════════════════════════════════════════════════════════

READINESS_UNAVAILABLE = "unavailable"
READINESS_NOT_READY = "not_ready"
READINESS_EVIDENCE_INCOMPLETE = "evidence_incomplete"
READINESS_APPROVAL_REQUIRED = "approval_required"
READINESS_BLOCKED = "blocked"
READINESS_READY_FOR_HUMAN_REVIEW = "ready_for_human_review"
READINESS_READY_FOR_PREFLIGHT_ONLY = "ready_for_preflight_only"
EXECUTION_READY_FUTURE_ONLY = "execution_ready"  # not available, not implemented

VALID_READINESS_STATUSES: frozenset[str] = frozenset({
    READINESS_UNAVAILABLE, READINESS_NOT_READY, READINESS_EVIDENCE_INCOMPLETE,
    READINESS_APPROVAL_REQUIRED, READINESS_BLOCKED,
    READINESS_READY_FOR_HUMAN_REVIEW, READINESS_READY_FOR_PREFLIGHT_ONLY,
})

READINESS_AUTHORIZED_STATUSES: frozenset[str] = frozenset()  # empty — none authorize execution

EXECUTION_UNAVAILABLE_STATUSES: frozenset[str] = frozenset({
    EXECUTION_READY_FUTURE_ONLY,
})


def get_current_execution_readiness() -> dict[str, Any]:
    """Return the current execution readiness state.

    Always returns unavailable — execution is not ready.
    Evidence-only, non-authorizing.
    """
    return {
        "readiness_status": READINESS_BLOCKED,
        "execution_available": False,
        "execution_authorized": False,
        "apply_authorized": False,
        "commit_authorized": False,
        "push_authorized": False,
        "simulation_only": True,
        "no_execution": True,
        "missing_evidence": [
            "governed_backend_invocation_contract",
            "adapter_invocation_boundary",
            "human_approval_gate",
            "audit_rollback_readiness",
            "execution_preflight_prototype",
        ],
        "no_go_conditions": [
            "execution_readiness_model_not_implemented",
            "backend_invocation_never_implemented",
            "subprocess_mediation_never_implemented",
            "shell_mediation_never_implemented",
        ],
        "message": "Execution is unavailable. Readiness model is design-only."
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 97B — Governed backend invocation contract constants
# ═══════════════════════════════════════════════════════════════════════════

INVOCATION_DENIED_MISSING_READINESS = "denied_missing_readiness"
INVOCATION_DENIED_MISSING_APPROVAL = "denied_missing_approval"
INVOCATION_DENIED_INVALID_BACKEND = "denied_invalid_backend_identity"
INVOCATION_DENIED_INVALID_ADAPTER = "denied_invalid_adapter_identity"
INVOCATION_DENIED_SCOPE = "denied_scope_violation"
INVOCATION_DENIED_VERIFICATION = "denied_artifact_verification_failed"
INVOCATION_DENIED_NO_ROLLBACK = "denied_no_rollback_readiness"
INVOCATION_DENIED_NO_AUDIT = "denied_no_audit_readiness"
INVOCATION_DENIED_EXECUTION_UNAVAILABLE = "denied_execution_unavailable"
INVOCATION_DENIED_BYPASS = "denied_bypass_permissions"
INVOCATION_DENIED_UNKNOWN_SCHEMA = "denied_unknown_schema"
INVOCATION_DENIED_CONFLICTING_FLAGS = "denied_conflicting_safety_flags"

VALID_INVOCATION_DENIAL_REASONS: frozenset[str] = frozenset({
    INVOCATION_DENIED_MISSING_READINESS, INVOCATION_DENIED_MISSING_APPROVAL,
    INVOCATION_DENIED_INVALID_BACKEND, INVOCATION_DENIED_INVALID_ADAPTER,
    INVOCATION_DENIED_SCOPE, INVOCATION_DENIED_VERIFICATION,
    INVOCATION_DENIED_NO_ROLLBACK, INVOCATION_DENIED_NO_AUDIT,
    INVOCATION_DENIED_EXECUTION_UNAVAILABLE, INVOCATION_DENIED_BYPASS,
    INVOCATION_DENIED_UNKNOWN_SCHEMA, INVOCATION_DENIED_CONFLICTING_FLAGS,
})


def get_backend_invocation_readiness() -> dict[str, Any]:
    """Return current backend invocation readiness.

    Always denied — backend invocation is never authorized.
    Evidence-only, non-authorizing.
    """
    return {
        "backend_invocation_authorized": False,
        "adapter_execution_authorized": False,
        "mutation_authorized": False,
        "apply_authorized": False,
        "commit_authorized": False,
        "push_authorized": False,
        "execution_authorized": False,
        "simulation_only": True,
        "no_execution": True,
        "denial_reasons": [
            INVOCATION_DENIED_EXECUTION_UNAVAILABLE,
            INVOCATION_DENIED_MISSING_READINESS,
            INVOCATION_DENIED_MISSING_APPROVAL,
        ],
        "message": "Backend invocation is never authorized. Contract design only."
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 97C — Adapter invocation boundary constants
# ═══════════════════════════════════════════════════════════════════════════

ADAPTER_DENIED_MISSING_IDENTITY = "denied_missing_adapter_identity"
ADAPTER_DENIED_INVALID_IDENTITY = "denied_invalid_adapter_identity"
ADAPTER_DENIED_MISSING_CAPABILITY = "denied_missing_capability_declaration"
ADAPTER_DENIED_CAPABILITY_MISMATCH = "denied_capability_mismatch"
ADAPTER_DENIED_FORBIDDEN_OP = "denied_forbidden_operation"
ADAPTER_DENIED_NETWORK_REQUESTED = "denied_network_requested"
ADAPTER_DENIED_SUBPROCESS_REQUESTED = "denied_subprocess_requested"
ADAPTER_DENIED_SHELL_REQUESTED = "denied_shell_requested"
ADAPTER_DENIED_MUTATION_REQUESTED = "denied_mutation_requested"
ADAPTER_DENIED_APPLY_REQUESTED = "denied_apply_requested"
ADAPTER_DENIED_COMMIT_REQUESTED = "denied_commit_requested"
ADAPTER_DENIED_PUSH_REQUESTED = "denied_push_requested"
ADAPTER_DENIED_TELEGRAM_INBOUND = "denied_telegram_inbound_requested"
ADAPTER_DENIED_SECRET_DETECTED = "denied_secret_material_detected"


def get_adapter_invocation_boundary() -> dict[str, Any]:
    """Return current adapter invocation boundary status.

    Always denied — adapter execution is never authorized.
    Evidence-only, non-authorizing.
    """
    return {
        "adapter_execution_authorized": False,
        "backend_invocation_authorized": False,
        "network_authorized": False,
        "subprocess_authorized": False,
        "shell_authorized": False,
        "mutation_authorized": False,
        "apply_authorized": False,
        "commit_authorized": False,
        "push_authorized": False,
        "execution_authorized": False,
        "simulation_only": True,
        "no_execution": True,
        "denial_reasons": [
            ADAPTER_DENIED_MISSING_IDENTITY,
            ADAPTER_DENIED_MISSING_CAPABILITY,
            ADAPTER_DENIED_SUBPROCESS_REQUESTED,
            ADAPTER_DENIED_SHELL_REQUESTED,
            ADAPTER_DENIED_NETWORK_REQUESTED,
        ],
        "message": "Adapter execution is never authorized. Boundary design only."
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 97E — Execution audit / rollback readiness constants
# ═══════════════════════════════════════════════════════════════════════════

AUDIT_DENIED_MISSING_READINESS = "denied_missing_audit_readiness"
AUDIT_DENIED_MISSING_ROLLBACK = "denied_missing_rollback_readiness"
AUDIT_DENIED_MISSING_SNAPSHOT = "denied_missing_pre_execution_snapshot"
AUDIT_DENIED_MISSING_OUTPUT_POLICY = "denied_missing_output_capture_policy"
AUDIT_DENIED_MISSING_REDACTION = "denied_missing_redaction_policy"
AUDIT_DENIED_ROLLBACK_INCOMPLETE = "denied_rollback_plan_incomplete"
AUDIT_DENIED_STORAGE_UNAVAILABLE = "denied_audit_storage_unavailable"

ABORT_BEFORE_BACKEND = "aborted_before_backend_invocation"
ABORT_BEFORE_ADAPTER = "aborted_before_adapter_execution"
ABORT_BEFORE_OUTPUT = "aborted_before_output_capture"
ABORT_BEFORE_APPLY = "aborted_before_apply"


def get_audit_rollback_readiness() -> dict[str, Any]:
    """Return current audit/rollback readiness.

    Always not ready — audit/rollback readiness is design-only.
    Evidence-only, non-authorizing.
    """
    return {
        "audit_ready": False,
        "rollback_ready": False,
        "rollback_execution_available": False,
        "rollback_authorized": False,
        "mutation_authorized": False,
        "apply_authorized": False,
        "commit_authorized": False,
        "push_authorized": False,
        "execution_authorized": False,
        "simulation_only": True,
        "no_execution": True,
        "denial_reasons": [
            AUDIT_DENIED_MISSING_READINESS,
            AUDIT_DENIED_MISSING_ROLLBACK,
            AUDIT_DENIED_MISSING_SNAPSHOT,
        ],
        "message": "Audit and rollback readiness are design-only. No execution."
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 97F — Execution readiness preflight dry-run
# ═══════════════════════════════════════════════════════════════════════════

_PREFLIGHT_SCHEMA_VERSION = "1.0"

# ── Preflight statuses ──────────────────────────────────────────────────

PREFLIGHT_UNAVAILABLE = "unavailable"
PREFLIGHT_NOT_READY = "not_ready"
PREFLIGHT_BLOCKED = "blocked"
PREFLIGHT_EVIDENCE_INCOMPLETE = "evidence_incomplete"
PREFLIGHT_APPROVAL_REQUIRED = "approval_required"
PREFLIGHT_AUDIT_REQUIRED = "audit_required"
PREFLIGHT_ROLLBACK_REQUIRED = "rollback_required"
PREFLIGHT_FAILED_VERIFICATION = "failed_verification"
PREFLIGHT_READY_FOR_HUMAN_REVIEW = "ready_for_human_review"
PREFLIGHT_READY_FOR_PREFLIGHT_ONLY = "ready_for_preflight_only"

# Future-only — never available, never implemented
PREFLIGHT_EXECUTION_READY_FUTURE_ONLY = "execution_ready"
PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY = "execute_now"
PREFLIGHT_INVOKE_NOW_FUTURE_ONLY = "invoke_now"
PREFLIGHT_APPLY_NOW_FUTURE_ONLY = "apply_now"
PREFLIGHT_COMMIT_NOW_FUTURE_ONLY = "commit_now"
PREFLIGHT_PUSH_NOW_FUTURE_ONLY = "push_now"

VALID_PREFLIGHT_STATUSES: frozenset[str] = frozenset({
    PREFLIGHT_UNAVAILABLE,
    PREFLIGHT_NOT_READY,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_EVIDENCE_INCOMPLETE,
    PREFLIGHT_APPROVAL_REQUIRED,
    PREFLIGHT_AUDIT_REQUIRED,
    PREFLIGHT_ROLLBACK_REQUIRED,
    PREFLIGHT_FAILED_VERIFICATION,
    PREFLIGHT_READY_FOR_HUMAN_REVIEW,
    PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
})

# Statuses that are available for current use (non-future)
CURRENT_PREFLIGHT_STATUSES: frozenset[str] = frozenset({
    PREFLIGHT_UNAVAILABLE,
    PREFLIGHT_NOT_READY,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_EVIDENCE_INCOMPLETE,
    PREFLIGHT_APPROVAL_REQUIRED,
    PREFLIGHT_AUDIT_REQUIRED,
    PREFLIGHT_ROLLBACK_REQUIRED,
    PREFLIGHT_FAILED_VERIFICATION,
    PREFLIGHT_READY_FOR_HUMAN_REVIEW,
    PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
})

# Statuses that are NEVER authorized — execution is never available
UNAVAILABLE_PREFLIGHT_STATUSES: frozenset[str] = frozenset({
    PREFLIGHT_EXECUTION_READY_FUTURE_ONLY,
    PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
    PREFLIGHT_INVOKE_NOW_FUTURE_ONLY,
    PREFLIGHT_APPLY_NOW_FUTURE_ONLY,
    PREFLIGHT_COMMIT_NOW_FUTURE_ONLY,
    PREFLIGHT_PUSH_NOW_FUTURE_ONLY,
})

# ── Evidence ref categories ─────────────────────────────────────────────

EVIDENCE_READINESS_MODEL = "readiness_model"
EVIDENCE_BACKEND_CONTRACT = "backend_invocation_contract"
EVIDENCE_ADAPTER_BOUNDARY = "adapter_invocation_boundary"
EVIDENCE_HUMAN_APPROVAL_GATE = "human_approval_gate"
EVIDENCE_AUDIT_READINESS = "audit_readiness"
EVIDENCE_ROLLBACK_READINESS = "rollback_readiness"
EVIDENCE_ARTIFACT_VERIFICATION = "artifact_verification"
EVIDENCE_EXECUTION_BOUNDARY_PROOF = "execution_boundary_proof"
EVIDENCE_PHASE_FINALIZATION = "phase_finalization_context"
EVIDENCE_ACTIVE_TASK = "active_task_contract"

ALL_EVIDENCE_CATEGORIES: frozenset[str] = frozenset({
    EVIDENCE_READINESS_MODEL,
    EVIDENCE_BACKEND_CONTRACT,
    EVIDENCE_ADAPTER_BOUNDARY,
    EVIDENCE_HUMAN_APPROVAL_GATE,
    EVIDENCE_AUDIT_READINESS,
    EVIDENCE_ROLLBACK_READINESS,
    EVIDENCE_ARTIFACT_VERIFICATION,
    EVIDENCE_EXECUTION_BOUNDARY_PROOF,
    EVIDENCE_PHASE_FINALIZATION,
    EVIDENCE_ACTIVE_TASK,
})

# ── No-go condition constants ───────────────────────────────────────────

NOGO_MISSING_READINESS = "missing_execution_readiness"
NOGO_MISSING_BACKEND_CONTRACT = "missing_backend_invocation_contract"
NOGO_MISSING_ADAPTER_BOUNDARY = "missing_adapter_boundary"
NOGO_MISSING_APPROVAL = "missing_human_approval"
NOGO_EXPIRED_APPROVAL = "expired_or_revoked_approval"
NOGO_MISSING_AUDIT = "missing_audit_readiness"
NOGO_MISSING_ROLLBACK = "missing_rollback_readiness"
NOGO_FAILED_VERIFICATION = "failed_artifact_verification"
NOGO_MISSING_BOUNDARY_PROOF = "missing_execution_boundary_proof"
NOGO_STALE_POINTER = "stale_latest_pointer"
NOGO_UNKNOWN_SCHEMA = "unknown_schema_version"
NOGO_CONFLICTING_FLAGS = "conflicting_safety_flags"
NOGO_FORBIDDEN_PATH = "forbidden_path_or_scope"
NOGO_SECRET_DETECTED = "secret_material_detected"
NOGO_NETWORK_REQUESTED = "network_requested"
NOGO_SUBPROCESS_REQUESTED = "subprocess_requested"
NOGO_SHELL_REQUESTED = "shell_requested"
NOGO_TELEGRAM_INBOUND = "telegram_inbound_requested"
NOGO_APPLY_REQUESTED = "apply_requested_without_governance"
NOGO_ROLLBACK_EXEC_REQUESTED = "rollback_execution_requested"
NOGO_COMMIT_PUSH_REQUESTED = "commit_or_push_requested"
NOGO_RAW_GIT = "raw_git_path_detected"
NOGO_NO_VERIFY = "no_verify_attempt"
NOGO_FORCE_PUSH = "force_push_attempt"
NOGO_BYPASS_PERMISSIONS = "bypass_permissions_detected"

VALID_NOGO_CONDITIONS: frozenset[str] = frozenset({
    NOGO_MISSING_READINESS,
    NOGO_MISSING_BACKEND_CONTRACT,
    NOGO_MISSING_ADAPTER_BOUNDARY,
    NOGO_MISSING_APPROVAL,
    NOGO_EXPIRED_APPROVAL,
    NOGO_MISSING_AUDIT,
    NOGO_MISSING_ROLLBACK,
    NOGO_FAILED_VERIFICATION,
    NOGO_MISSING_BOUNDARY_PROOF,
    NOGO_STALE_POINTER,
    NOGO_UNKNOWN_SCHEMA,
    NOGO_CONFLICTING_FLAGS,
    NOGO_FORBIDDEN_PATH,
    NOGO_SECRET_DETECTED,
    NOGO_NETWORK_REQUESTED,
    NOGO_SUBPROCESS_REQUESTED,
    NOGO_SHELL_REQUESTED,
    NOGO_TELEGRAM_INBOUND,
    NOGO_APPLY_REQUESTED,
    NOGO_ROLLBACK_EXEC_REQUESTED,
    NOGO_COMMIT_PUSH_REQUESTED,
    NOGO_RAW_GIT,
    NOGO_NO_VERIFY,
    NOGO_FORCE_PUSH,
    NOGO_BYPASS_PERMISSIONS,
    # Upstream conditions from 97A readiness model (passthrough)
    "execution_readiness_model_not_implemented",
    "backend_invocation_never_implemented",
    "subprocess_mediation_never_implemented",
    "shell_mediation_never_implemented",
})

# ── Artifact paths ──────────────────────────────────────────────────────

_PREFLIGHT_ARTIFACT_DIR = ".pcae/execution-readiness-preflight"
_PREFLIGHT_LATEST = "latest.json"


def _preflight_dir_path() -> Path:
    from pathlib import Path as _P
    return _P(_PREFLIGHT_ARTIFACT_DIR)


def _preflight_latest_path() -> Path:
    return _preflight_dir_path() / _PREFLIGHT_LATEST


def _preflight_timestamped_path(ts: str) -> Path:
    return _preflight_dir_path() / f"{ts}.json"


# ═══════════════════════════════════════════════════════════════════════════
# ExecutionReadinessPreflight — main preflight result dataclass
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ExecutionReadinessPreflight:
    """Integrated readiness preflight combining 97A–97E evidence.

    Deterministic, evidence-only, non-executing, non-authorizing.
    All authorization flags are always False in the current system.
    """

    schema_version: str = _PREFLIGHT_SCHEMA_VERSION
    preflight_id: str = ""
    phase_id: str = "97F"
    task_id: str = ""
    generated_at_utc: str = ""

    # ── Core statuses ──────────────────────────────────────────────────
    readiness_status: str = READINESS_BLOCKED
    preflight_status: str = PREFLIGHT_BLOCKED
    evidence_status: str = READINESS_EVIDENCE_INCOMPLETE

    # ── Domain statuses ─────────────────────────────────────────────────
    backend_invocation_contract_status: str = PREFLIGHT_NOT_READY
    adapter_boundary_status: str = PREFLIGHT_NOT_READY
    approval_status: str = PREFLIGHT_APPROVAL_REQUIRED
    audit_readiness_status: str = PREFLIGHT_AUDIT_REQUIRED
    rollback_readiness_status: str = PREFLIGHT_ROLLBACK_REQUIRED
    artifact_verification_status: str = PREFLIGHT_FAILED_VERIFICATION
    execution_boundary_proof_status: str = PREFLIGHT_NOT_READY

    # ── Aggregated results ─────────────────────────────────────────────
    no_go_conditions: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # ── Evidence references ─────────────────────────────────────────────
    evidence_refs: list[str] = field(default_factory=list)
    approval_refs: list[str] = field(default_factory=list)
    audit_refs: list[str] = field(default_factory=list)
    rollback_refs: list[str] = field(default_factory=list)
    proof_refs: list[str] = field(default_factory=list)

    # ── Authorization summary — all False in current system ────────────
    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    # ── Safety invariants ──────────────────────────────────────────────
    simulation_only: bool = True
    no_execution: bool = True

    # ── Digest ─────────────────────────────────────────────────────────
    digest: str = ""

    def validate(self) -> list[str]:
        """Validate preflight invariants. Fail-closed."""
        issues: list[str] = []
        if self.schema_version != _PREFLIGHT_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.preflight_status not in VALID_PREFLIGHT_STATUSES:
            issues.append(f"invalid preflight_status: {self.preflight_status!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.backend_invocation_authorized:
            issues.append("backend_invocation_authorized must be False")
        if self.adapter_execution_authorized:
            issues.append("adapter_execution_authorized must be False")
        if self.network_authorized:
            issues.append("network_authorized must be False")
        if self.subprocess_authorized:
            issues.append("subprocess_authorized must be False")
        if self.shell_authorized:
            issues.append("shell_authorized must be False")
        if self.mutation_authorized:
            issues.append("mutation_authorized must be False")
        if self.apply_authorized:
            issues.append("apply_authorized must be False")
        if self.rollback_authorized:
            issues.append("rollback_authorized must be False")
        if self.commit_authorized:
            issues.append("commit_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        for cond in self.no_go_conditions:
            if cond not in VALID_NOGO_CONDITIONS:
                issues.append(f"unknown no_go_condition: {cond!r}")
        # Future-only statuses must never appear as current status
        if self.preflight_status in UNAVAILABLE_PREFLIGHT_STATUSES:
            issues.append(
                f"preflight_status {self.preflight_status!r} is future-only and unavailable"
            )
        return issues

    def compute_digest(self) -> str:
        """Compute SHA-256 digest over all fields except digest itself."""
        payload = _canonical_preflight_dict(self)
        payload.pop("digest", None)
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "preflight_id": self.preflight_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "readiness_status": self.readiness_status,
            "preflight_status": self.preflight_status,
            "evidence_status": self.evidence_status,
            "backend_invocation_contract_status": self.backend_invocation_contract_status,
            "adapter_boundary_status": self.adapter_boundary_status,
            "approval_status": self.approval_status,
            "audit_readiness_status": self.audit_readiness_status,
            "rollback_readiness_status": self.rollback_readiness_status,
            "artifact_verification_status": self.artifact_verification_status,
            "execution_boundary_proof_status": self.execution_boundary_proof_status,
            "no_go_conditions": sorted(self.no_go_conditions),
            "missing_evidence": sorted(self.missing_evidence),
            "failed_checks": sorted(self.failed_checks),
            "warnings": sorted(self.warnings),
            "evidence_refs": self.evidence_refs,
            "approval_refs": self.approval_refs,
            "audit_refs": self.audit_refs,
            "rollback_refs": self.rollback_refs,
            "proof_refs": self.proof_refs,
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "digest": self.digest,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionReadinessPreflight":
        auth = data.get("authorization_summary", {})
        return cls(
            schema_version=data.get("schema_version", _PREFLIGHT_SCHEMA_VERSION),
            preflight_id=data.get("preflight_id", ""),
            phase_id=data.get("phase_id", "97F"),
            task_id=data.get("task_id", ""),
            generated_at_utc=data.get("generated_at_utc", ""),
            readiness_status=data.get("readiness_status", READINESS_BLOCKED),
            preflight_status=data.get("preflight_status", PREFLIGHT_BLOCKED),
            evidence_status=data.get("evidence_status", READINESS_EVIDENCE_INCOMPLETE),
            backend_invocation_contract_status=data.get(
                "backend_invocation_contract_status", PREFLIGHT_NOT_READY
            ),
            adapter_boundary_status=data.get(
                "adapter_boundary_status", PREFLIGHT_NOT_READY
            ),
            approval_status=data.get("approval_status", PREFLIGHT_APPROVAL_REQUIRED),
            audit_readiness_status=data.get(
                "audit_readiness_status", PREFLIGHT_AUDIT_REQUIRED
            ),
            rollback_readiness_status=data.get(
                "rollback_readiness_status", PREFLIGHT_ROLLBACK_REQUIRED
            ),
            artifact_verification_status=data.get(
                "artifact_verification_status", PREFLIGHT_FAILED_VERIFICATION
            ),
            execution_boundary_proof_status=data.get(
                "execution_boundary_proof_status", PREFLIGHT_NOT_READY
            ),
            no_go_conditions=data.get("no_go_conditions", []),
            missing_evidence=data.get("missing_evidence", []),
            failed_checks=data.get("failed_checks", []),
            warnings=data.get("warnings", []),
            evidence_refs=data.get("evidence_refs", []),
            approval_refs=data.get("approval_refs", []),
            audit_refs=data.get("audit_refs", []),
            rollback_refs=data.get("rollback_refs", []),
            proof_refs=data.get("proof_refs", []),
            execution_available=auth.get("execution_available", False),
            execution_authorized=auth.get("execution_authorized", False),
            backend_invocation_authorized=auth.get("backend_invocation_authorized", False),
            adapter_execution_authorized=auth.get("adapter_execution_authorized", False),
            network_authorized=auth.get("network_authorized", False),
            subprocess_authorized=auth.get("subprocess_authorized", False),
            shell_authorized=auth.get("shell_authorized", False),
            mutation_authorized=auth.get("mutation_authorized", False),
            apply_authorized=auth.get("apply_authorized", False),
            rollback_authorized=auth.get("rollback_authorized", False),
            commit_authorized=auth.get("commit_authorized", False),
            push_authorized=auth.get("push_authorized", False),
            simulation_only=data.get("simulation_only", True),
            no_execution=data.get("no_execution", True),
            digest=data.get("digest", ""),
        )


def _canonical_preflight_dict(preflight: ExecutionReadinessPreflight) -> dict[str, Any]:
    """Return a canonical dict representation for digest computation."""
    return {
        "schema_version": preflight.schema_version,
        "preflight_id": preflight.preflight_id,
        "phase_id": preflight.phase_id,
        "task_id": preflight.task_id,
        "generated_at_utc": preflight.generated_at_utc,
        "readiness_status": preflight.readiness_status,
        "preflight_status": preflight.preflight_status,
        "evidence_status": preflight.evidence_status,
        "backend_invocation_contract_status": preflight.backend_invocation_contract_status,
        "adapter_boundary_status": preflight.adapter_boundary_status,
        "approval_status": preflight.approval_status,
        "audit_readiness_status": preflight.audit_readiness_status,
        "rollback_readiness_status": preflight.rollback_readiness_status,
        "artifact_verification_status": preflight.artifact_verification_status,
        "execution_boundary_proof_status": preflight.execution_boundary_proof_status,
        "no_go_conditions": sorted(preflight.no_go_conditions),
        "missing_evidence": sorted(preflight.missing_evidence),
        "failed_checks": sorted(preflight.failed_checks),
        "warnings": sorted(preflight.warnings),
        "evidence_refs": sorted(preflight.evidence_refs),
        "approval_refs": sorted(preflight.approval_refs),
        "audit_refs": sorted(preflight.audit_refs),
        "rollback_refs": sorted(preflight.rollback_refs),
        "proof_refs": sorted(preflight.proof_refs),
        "authorization_summary": {
            "execution_available": preflight.execution_available,
            "execution_authorized": preflight.execution_authorized,
            "backend_invocation_authorized": preflight.backend_invocation_authorized,
            "adapter_execution_authorized": preflight.adapter_execution_authorized,
            "network_authorized": preflight.network_authorized,
            "subprocess_authorized": preflight.subprocess_authorized,
            "shell_authorized": preflight.shell_authorized,
            "mutation_authorized": preflight.mutation_authorized,
            "apply_authorized": preflight.apply_authorized,
            "rollback_authorized": preflight.rollback_authorized,
            "commit_authorized": preflight.commit_authorized,
            "push_authorized": preflight.push_authorized,
        },
        "simulation_only": preflight.simulation_only,
        "no_execution": preflight.no_execution,
        "digest": preflight.digest,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Preflight builder — aggregates 97A–97E evidence
# ═══════════════════════════════════════════════════════════════════════════


_UNSET = object()


def build_execution_readiness_preflight(
    *,
    task_id: str = "",
    phase_id: str = "97F",
    readiness_data: dict[str, Any] | None = _UNSET,
    backend_data: dict[str, Any] | None = _UNSET,
    adapter_data: dict[str, Any] | None = _UNSET,
    approval_data: dict[str, Any] | None = _UNSET,
    audit_data: dict[str, Any] | None = _UNSET,
    custom_evidence: dict[str, Any] | None = None,
    active_task_contract: str | None = None,
    phase_finalization_present: bool = False,
) -> ExecutionReadinessPreflight:
    """Build an integrated execution readiness preflight combining 97A–97E evidence.

    Deterministic, evidence-only, non-executing, non-authorizing.
    Fails closed: any missing required evidence → blocked with no-go conditions.

    Args:
        task_id: Active task ID for contextualization.
        phase_id: Phase performing the preflight (default: 97F).
        readiness_data: From get_current_execution_readiness() (97A).
        backend_data: From get_backend_invocation_readiness() (97B).
        adapter_data: From get_adapter_invocation_boundary() (97C).
        approval_data: Approval gate status dict (97D).
        audit_data: From get_audit_rollback_readiness() (97E).
        custom_evidence: Optional additional evidence for extensibility.
        active_task_contract: Path to active task contract file.
        phase_finalization_present: Whether .pcae/phase-completion-metadata.json exists.

    Returns:
        ExecutionReadinessPreflight with aggregated evidence, no-go conditions,
        and fail-closed authorization flags.
    """
    import uuid
    now = datetime.now(timezone.utc)
    preflight_id = f"erp-{uuid.uuid4().hex[:12]}"
    generated_at = now.isoformat()

    # ── Gather evidence from 97A–97E models ─────────────────────────────
    # _UNSET sentinel → use default getter.  Explicit None → evidence missing.
    if readiness_data is _UNSET:
        readiness_data = get_current_execution_readiness()
    if backend_data is _UNSET:
        backend_data = get_backend_invocation_readiness()
    if adapter_data is _UNSET:
        adapter_data = get_adapter_invocation_boundary()
    if audit_data is _UNSET:
        audit_data = get_audit_rollback_readiness()
    # approval_data defaults to None (missing evidence) when not provided
    if approval_data is _UNSET:
        approval_data = None

    # ── Build evidence presence map ─────────────────────────────────────
    evidence_present: dict[str, bool] = {}
    missing_evidence: list[str] = []
    evidence_refs: list[str] = []

    # 97A — readiness model
    if readiness_data:
        evidence_present[EVIDENCE_READINESS_MODEL] = True
        evidence_refs.append("model:execution_readiness_97a")
    else:
        evidence_present[EVIDENCE_READINESS_MODEL] = False
        missing_evidence.append(EVIDENCE_READINESS_MODEL)

    # 97B — backend invocation contract
    if backend_data:
        evidence_present[EVIDENCE_BACKEND_CONTRACT] = True
        evidence_refs.append("model:backend_invocation_contract_97b")
    else:
        evidence_present[EVIDENCE_BACKEND_CONTRACT] = False
        missing_evidence.append(EVIDENCE_BACKEND_CONTRACT)

    # 97C — adapter invocation boundary
    if adapter_data:
        evidence_present[EVIDENCE_ADAPTER_BOUNDARY] = True
        evidence_refs.append("model:adapter_invocation_boundary_97c")
    else:
        evidence_present[EVIDENCE_ADAPTER_BOUNDARY] = False
        missing_evidence.append(EVIDENCE_ADAPTER_BOUNDARY)

    # 97D — human approval gate
    if approval_data:
        evidence_present[EVIDENCE_HUMAN_APPROVAL_GATE] = True
        evidence_refs.append("model:human_approval_gate_97d")
    else:
        evidence_present[EVIDENCE_HUMAN_APPROVAL_GATE] = False
        missing_evidence.append(EVIDENCE_HUMAN_APPROVAL_GATE)

    # 97E — audit/rollback readiness
    if audit_data:
        evidence_present[EVIDENCE_AUDIT_READINESS] = True
        evidence_present[EVIDENCE_ROLLBACK_READINESS] = True
        evidence_refs.append("model:audit_rollback_readiness_97e")
    else:
        evidence_present[EVIDENCE_AUDIT_READINESS] = False
        evidence_present[EVIDENCE_ROLLBACK_READINESS] = False
        missing_evidence.append(EVIDENCE_AUDIT_READINESS)
        missing_evidence.append(EVIDENCE_ROLLBACK_READINESS)

    # Active task contract
    if active_task_contract:
        evidence_present[EVIDENCE_ACTIVE_TASK] = True
        evidence_refs.append(f"file:{active_task_contract}")
    else:
        evidence_present[EVIDENCE_ACTIVE_TASK] = False
        missing_evidence.append(EVIDENCE_ACTIVE_TASK)

    # Phase finalization context
    if phase_finalization_present:
        evidence_present[EVIDENCE_PHASE_FINALIZATION] = True
        evidence_refs.append("file:.pcae/phase-completion-metadata.json")
    else:
        evidence_present[EVIDENCE_PHASE_FINALIZATION] = False
        missing_evidence.append(EVIDENCE_PHASE_FINALIZATION)

    # ── Determine evidence status ───────────────────────────────────────
    if not any(evidence_present.values()):
        evidence_status = READINESS_EVIDENCE_INCOMPLETE
    elif all(evidence_present.values()):
        evidence_status = "complete"
    else:
        evidence_status = READINESS_EVIDENCE_INCOMPLETE

    # ── Aggregate no-go conditions ──────────────────────────────────────
    no_go: list[str] = []

    # From 97A readiness
    if readiness_data:
        no_go.extend(readiness_data.get("no_go_conditions", []))
    if not evidence_present.get(EVIDENCE_READINESS_MODEL, False):
        no_go.append(NOGO_MISSING_READINESS)

    # From 97B backend contract
    if not evidence_present.get(EVIDENCE_BACKEND_CONTRACT, False):
        no_go.append(NOGO_MISSING_BACKEND_CONTRACT)

    # From 97C adapter boundary
    if not evidence_present.get(EVIDENCE_ADAPTER_BOUNDARY, False):
        no_go.append(NOGO_MISSING_ADAPTER_BOUNDARY)

    # From 97D approval gate
    if not evidence_present.get(EVIDENCE_HUMAN_APPROVAL_GATE, False):
        no_go.append(NOGO_MISSING_APPROVAL)
    elif approval_data:
        approval_decision = approval_data.get("decision", "")
        if approval_decision in ("expired", "revoked"):
            no_go.append(NOGO_EXPIRED_APPROVAL)

    # From 97E audit/rollback
    if not evidence_present.get(EVIDENCE_AUDIT_READINESS, False):
        no_go.append(NOGO_MISSING_AUDIT)
    if not evidence_present.get(EVIDENCE_ROLLBACK_READINESS, False):
        no_go.append(NOGO_MISSING_ROLLBACK)

    # No artifact verification yet
    no_go.append(NOGO_FAILED_VERIFICATION)

    # No execution boundary proof yet
    no_go.append(NOGO_MISSING_BOUNDARY_PROOF)

    # Deduplicate
    no_go = sorted(set(no_go))

    # ── Aggregate failed checks ─────────────────────────────────────────
    failed_checks: list[str] = []
    if not evidence_present.get(EVIDENCE_READINESS_MODEL, False):
        failed_checks.append("check:readiness_model_missing")
    if not evidence_present.get(EVIDENCE_BACKEND_CONTRACT, False):
        failed_checks.append("check:backend_invocation_contract_missing")
    if not evidence_present.get(EVIDENCE_ADAPTER_BOUNDARY, False):
        failed_checks.append("check:adapter_boundary_missing")
    if not evidence_present.get(EVIDENCE_HUMAN_APPROVAL_GATE, False):
        failed_checks.append("check:human_approval_gate_missing")
    if not evidence_present.get(EVIDENCE_AUDIT_READINESS, False):
        failed_checks.append("check:audit_readiness_missing")
    if not evidence_present.get(EVIDENCE_ROLLBACK_READINESS, False):
        failed_checks.append("check:rollback_readiness_missing")
    if not evidence_present.get(EVIDENCE_ACTIVE_TASK, False):
        failed_checks.append("check:active_task_contract_missing")
    if not evidence_present.get(EVIDENCE_PHASE_FINALIZATION, False):
        failed_checks.append("check:phase_finalization_context_missing")

    # ── Determine domain statuses ───────────────────────────────────────
    backend_status = (
        PREFLIGHT_BLOCKED
        if NOGO_MISSING_BACKEND_CONTRACT in no_go
        else PREFLIGHT_NOT_READY
    )
    adapter_status = (
        PREFLIGHT_BLOCKED
        if NOGO_MISSING_ADAPTER_BOUNDARY in no_go
        else PREFLIGHT_NOT_READY
    )
    approval_domain_status = (
        PREFLIGHT_APPROVAL_REQUIRED
        if NOGO_MISSING_APPROVAL in no_go or NOGO_EXPIRED_APPROVAL in no_go
        else PREFLIGHT_NOT_READY
    )
    audit_domain_status = (
        PREFLIGHT_AUDIT_REQUIRED
        if NOGO_MISSING_AUDIT in no_go
        else PREFLIGHT_NOT_READY
    )
    rollback_domain_status = (
        PREFLIGHT_ROLLBACK_REQUIRED
        if NOGO_MISSING_ROLLBACK in no_go
        else PREFLIGHT_NOT_READY
    )
    verification_status = (
        PREFLIGHT_FAILED_VERIFICATION
        if NOGO_FAILED_VERIFICATION in no_go
        else PREFLIGHT_NOT_READY
    )
    proof_status = (
        PREFLIGHT_NOT_READY
        if NOGO_MISSING_BOUNDARY_PROOF in no_go
        else PREFLIGHT_NOT_READY
    )

    # ── Determine readiness status from 97A ────────────────────────────
    readiness_status = readiness_data.get(
        "readiness_status", READINESS_BLOCKED
    ) if readiness_data else READINESS_BLOCKED

    # ── Determine overall preflight status (fail-closed) ───────────────
    if no_go:
        # Determine the most severe status from no-go conditions
        if NOGO_FAILED_VERIFICATION in no_go:
            preflight_status = PREFLIGHT_FAILED_VERIFICATION
        elif NOGO_MISSING_READINESS in no_go:
            preflight_status = PREFLIGHT_EVIDENCE_INCOMPLETE
        elif NOGO_MISSING_BACKEND_CONTRACT in no_go or NOGO_MISSING_ADAPTER_BOUNDARY in no_go:
            preflight_status = PREFLIGHT_BLOCKED
        elif NOGO_MISSING_APPROVAL in no_go or NOGO_EXPIRED_APPROVAL in no_go:
            preflight_status = PREFLIGHT_APPROVAL_REQUIRED
        elif NOGO_MISSING_AUDIT in no_go:
            preflight_status = PREFLIGHT_AUDIT_REQUIRED
        elif NOGO_MISSING_ROLLBACK in no_go:
            preflight_status = PREFLIGHT_ROLLBACK_REQUIRED
        else:
            preflight_status = PREFLIGHT_BLOCKED
    elif missing_evidence:
        preflight_status = PREFLIGHT_EVIDENCE_INCOMPLETE
    elif evidence_status == READINESS_EVIDENCE_INCOMPLETE:
        preflight_status = PREFLIGHT_EVIDENCE_INCOMPLETE
    elif approval_data and approval_data.get(
        "decision", ""
    ) in ("approved",):
        preflight_status = PREFLIGHT_READY_FOR_HUMAN_REVIEW
    else:
        preflight_status = PREFLIGHT_READY_FOR_PREFLIGHT_ONLY

    # ── Collect warnings ───────────────────────────────────────────────
    warnings_list: list[str] = []
    if missing_evidence:
        warnings_list.append(
            f"missing_evidence: {', '.join(sorted(missing_evidence))}"
        )
    if no_go:
        warnings_list.append(f"no_go_conditions: {len(no_go)} active")
    warnings_list.append("execution_remains_unavailable")
    warnings_list.append("preflight_is_evidence_only_non_authorizing")

    # ── Build preflight ────────────────────────────────────────────────
    preflight = ExecutionReadinessPreflight(
        schema_version=_PREFLIGHT_SCHEMA_VERSION,
        preflight_id=preflight_id,
        phase_id=phase_id,
        task_id=task_id,
        generated_at_utc=generated_at,
        readiness_status=readiness_status,
        preflight_status=preflight_status,
        evidence_status=evidence_status,
        backend_invocation_contract_status=backend_status,
        adapter_boundary_status=adapter_status,
        approval_status=approval_domain_status,
        audit_readiness_status=audit_domain_status,
        rollback_readiness_status=rollback_domain_status,
        artifact_verification_status=verification_status,
        execution_boundary_proof_status=proof_status,
        no_go_conditions=sorted(no_go),
        missing_evidence=sorted(missing_evidence),
        failed_checks=sorted(failed_checks),
        warnings=sorted(warnings_list),
        evidence_refs=sorted(evidence_refs),
        approval_refs=sorted(approval_data.get("refs", [])) if approval_data else [],
        audit_refs=sorted(audit_data.get("denial_reasons", [])) if audit_data else [],
        rollback_refs=sorted(audit_data.get("denial_reasons", [])) if audit_data else [],
        proof_refs=[],
        # All authorization flags remain False
        execution_available=False,
        execution_authorized=False,
        backend_invocation_authorized=False,
        adapter_execution_authorized=False,
        network_authorized=False,
        subprocess_authorized=False,
        shell_authorized=False,
        mutation_authorized=False,
        apply_authorized=False,
        rollback_authorized=False,
        commit_authorized=False,
        push_authorized=False,
        simulation_only=True,
        no_execution=True,
    )
    preflight.digest = preflight.compute_digest()
    return preflight


# ═══════════════════════════════════════════════════════════════════════════
# Preflight persistence and verification
# ═══════════════════════════════════════════════════════════════════════════


def save_execution_readiness_preflight(
    preflight: ExecutionReadinessPreflight,
) -> Path:
    """Save preflight to .pcae/execution-readiness-preflight/.

    Writes both latest.json and a timestamped copy.
    Never executes, never invokes backends, never mutates source.
    """
    dir_path = _preflight_dir_path()
    dir_path.mkdir(parents=True, exist_ok=True)

    # Recompute digest before saving
    preflight.digest = preflight.compute_digest()
    payload = preflight.to_dict()

    canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)

    # Write timestamped copy
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    ts_path = _preflight_timestamped_path(ts)
    ts_path.write_text(canonical, encoding="utf-8")

    # Write latest
    latest_path = _preflight_latest_path()
    latest_path.write_text(canonical, encoding="utf-8")

    return ts_path


def load_latest_execution_readiness_preflight() -> ExecutionReadinessPreflight | None:
    """Load the latest preflight artifact.

    Returns None if no artifact exists.
    Never executes, never invokes backends, never mutates source.
    """
    latest_path = _preflight_latest_path()
    if not latest_path.exists():
        return None
    try:
        raw = latest_path.read_text(encoding="utf-8")
        data = _json.loads(raw)
        return ExecutionReadinessPreflight.from_dict(data)
    except (_json.JSONDecodeError, KeyError, TypeError):
        return None


def verify_execution_readiness_preflight(
    preflight: ExecutionReadinessPreflight | None = None,
    *,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    """Verify a preflight artifact.

    Checks schema version, digest, safety flags, authorization flags,
    no-go conditions, missing evidence, and fail-closed invariants.

    Returns dict with valid=False for any verified issue.
    Never executes, never invokes backends, never mutates source.
    """
    issues: list[str] = []

    if preflight is None:
        return {
            "valid": False,
            "issues": ["no_preflight_artifact_found"],
            "preflight_present": False,
        }

    # Schema version check
    if preflight.schema_version != _PREFLIGHT_SCHEMA_VERSION:
        issues.append(
            f"unknown schema_version: {preflight.schema_version!r} "
            f"(expected {_PREFLIGHT_SCHEMA_VERSION!r})"
        )

    # Digest check
    if expected_digest is not None:
        if preflight.digest != expected_digest:
            issues.append("digest_mismatch: tampered or stale artifact")
    elif preflight.digest:
        computed = preflight.compute_digest()
        if computed != preflight.digest:
            issues.append("digest_mismatch: computed_digest_differs_from_stored")

    # Validate invariants
    validate_issues = preflight.validate()
    issues.extend(validate_issues)

    # Check safety flags
    if not preflight.simulation_only:
        issues.append("simulation_only must be True")
    if not preflight.no_execution:
        issues.append("no_execution must be True")

    # Check authorization flags
    auth_checks = [
        ("execution_available", preflight.execution_available),
        ("execution_authorized", preflight.execution_authorized),
        ("backend_invocation_authorized", preflight.backend_invocation_authorized),
        ("adapter_execution_authorized", preflight.adapter_execution_authorized),
        ("network_authorized", preflight.network_authorized),
        ("subprocess_authorized", preflight.subprocess_authorized),
        ("shell_authorized", preflight.shell_authorized),
        ("mutation_authorized", preflight.mutation_authorized),
        ("apply_authorized", preflight.apply_authorized),
        ("rollback_authorized", preflight.rollback_authorized),
        ("commit_authorized", preflight.commit_authorized),
        ("push_authorized", preflight.push_authorized),
    ]
    for flag_name, flag_value in auth_checks:
        if flag_value:
            issues.append(f"{flag_name} must be False")

    # Check preflight status is not future-only
    if preflight.preflight_status in UNAVAILABLE_PREFLIGHT_STATUSES:
        issues.append(
            f"preflight_status {preflight.preflight_status!r} is future-only and unavailable"
        )

    # Contradictory status check
    if preflight.preflight_status == PREFLIGHT_READY_FOR_PREFLIGHT_ONLY:
        if preflight.no_go_conditions:
            issues.append(
                "contradictory: ready_for_preflight_only with active no_go_conditions"
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "preflight_present": True,
        "preflight_id": preflight.preflight_id,
        "digest": preflight.digest,
        "preflight_status": preflight.preflight_status,
        "no_execution_confirmed": preflight.no_execution and not preflight.execution_available,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 98A — First governed execution preflight prototype
# ═══════════════════════════════════════════════════════════════════════════

_GEP_SCHEMA_VERSION = "1.0"

# ── Prototype statuses ─────────────────────────────────────────────────

GEP_UNAVAILABLE = "unavailable"
GEP_BLOCKED = "blocked"
GEP_EVIDENCE_INCOMPLETE = "evidence_incomplete"
GEP_APPROVAL_REQUIRED = "approval_required"
GEP_AUDIT_REQUIRED = "audit_required"
GEP_ROLLBACK_REQUIRED = "rollback_required"
GEP_VERIFICATION_FAILED = "verification_failed"
GEP_READY_FOR_PREFLIGHT_REVIEW = "ready_for_preflight_review"
GEP_PREFLIGHT_ONLY = "preflight_only"

VALID_GEP_STATUSES: frozenset[str] = frozenset({
    GEP_UNAVAILABLE, GEP_BLOCKED, GEP_EVIDENCE_INCOMPLETE,
    GEP_APPROVAL_REQUIRED, GEP_AUDIT_REQUIRED, GEP_ROLLBACK_REQUIRED,
    GEP_VERIFICATION_FAILED, GEP_READY_FOR_PREFLIGHT_REVIEW, GEP_PREFLIGHT_ONLY,
})

# ── Prototype decisions ────────────────────────────────────────────────

GEP_DECISION_DENY = "deny"
GEP_DECISION_BLOCK = "block"
GEP_DECISION_REQUIRE_EVIDENCE = "require_evidence"
GEP_DECISION_REQUIRE_APPROVAL = "require_approval"
GEP_DECISION_REQUIRE_AUDIT_READINESS = "require_audit_readiness"
GEP_DECISION_REQUIRE_ROLLBACK_READINESS = "require_rollback_readiness"
GEP_DECISION_REQUIRE_VERIFICATION = "require_verification"
GEP_DECISION_READY_FOR_REVIEW_ONLY = "ready_for_review_only"

VALID_GEP_DECISIONS: frozenset[str] = frozenset({
    GEP_DECISION_DENY, GEP_DECISION_BLOCK, GEP_DECISION_REQUIRE_EVIDENCE,
    GEP_DECISION_REQUIRE_APPROVAL, GEP_DECISION_REQUIRE_AUDIT_READINESS,
    GEP_DECISION_REQUIRE_ROLLBACK_READINESS, GEP_DECISION_REQUIRE_VERIFICATION,
    GEP_DECISION_READY_FOR_REVIEW_ONLY,
})

# ── Future-only / unavailable decisions ────────────────────────────────

GEP_DECISION_EXECUTE_FUTURE = "execute"
GEP_DECISION_RUN_FUTURE = "run"
GEP_DECISION_INVOKE_FUTURE = "invoke"
GEP_DECISION_APPLY_FUTURE = "apply"
GEP_DECISION_COMMIT_FUTURE = "commit"
GEP_DECISION_PUSH_FUTURE = "push"
GEP_DECISION_EXECUTION_READY_FUTURE = "execution_ready"
GEP_DECISION_INVOCATION_AUTHORIZED_FUTURE = "invocation_authorized"

UNAVAILABLE_GEP_DECISIONS: frozenset[str] = frozenset({
    GEP_DECISION_EXECUTE_FUTURE, GEP_DECISION_RUN_FUTURE,
    GEP_DECISION_INVOKE_FUTURE, GEP_DECISION_APPLY_FUTURE,
    GEP_DECISION_COMMIT_FUTURE, GEP_DECISION_PUSH_FUTURE,
    GEP_DECISION_EXECUTION_READY_FUTURE, GEP_DECISION_INVOCATION_AUTHORIZED_FUTURE,
})

# ── Artifact paths ──────────────────────────────────────────────────────

_GEP_ARTIFACT_DIR = ".pcae/governed-execution-preflight"
_GEP_LATEST = "latest.json"


def _gep_dir_path() -> Path:
    from pathlib import Path as _P
    return _P(_GEP_ARTIFACT_DIR)


def _gep_latest_path() -> Path:
    return _gep_dir_path() / _GEP_LATEST


def _gep_timestamped_path(ts: str) -> Path:
    return _gep_dir_path() / f"{ts}.json"


# ═══════════════════════════════════════════════════════════════════════════
# GovernedExecutionPreflightPrototype — main prototype dataclass
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class GovernedExecutionPreflightPrototype:
    """Non-executing governed execution preflight prototype.

    Consumes a Phase 97 ExecutionReadinessPreflight and produces a richer
    future-execution preflight decision artifact. Fails closed.
    All authorization flags remain False in the current system.
    """

    schema_version: str = _GEP_SCHEMA_VERSION
    prototype_id: str = ""
    phase_id: str = "98A"
    task_id: str = ""
    generated_at_utc: str = ""

    # ── Source preflight reference ──────────────────────────────────────
    source_preflight_ref: str = ""
    source_preflight_digest: str = ""
    source_preflight_status: str = ""
    source_readiness_status: str = ""
    source_no_go_conditions: list[str] = field(default_factory=list)
    source_missing_evidence: list[str] = field(default_factory=list)
    source_failed_checks: list[str] = field(default_factory=list)
    consumed_evidence_refs: list[str] = field(default_factory=list)

    # ── Prerequisite summaries ──────────────────────────────────────────
    prerequisite_summary: str = ""
    approval_summary: str = ""
    audit_summary: str = ""
    rollback_summary: str = ""
    backend_contract_summary: str = ""
    adapter_boundary_summary: str = ""
    artifact_verification_summary: str = ""
    execution_boundary_summary: str = ""

    # ── Prototype decision ──────────────────────────────────────────────
    prototype_status: str = GEP_BLOCKED
    decision: str = GEP_DECISION_BLOCK
    decision_reasons: list[str] = field(default_factory=list)
    no_go_conditions: list[str] = field(default_factory=list)
    missing_prerequisites: list[str] = field(default_factory=list)
    failed_prerequisites: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # ── Authorization summary — all False in current system ────────────
    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    # ── Safety invariants ──────────────────────────────────────────────
    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True

    # ── Digest ─────────────────────────────────────────────────────────
    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _GEP_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.prototype_status not in VALID_GEP_STATUSES:
            issues.append(f"invalid prototype_status: {self.prototype_status!r}")
        if self.decision not in VALID_GEP_DECISIONS:
            issues.append(f"invalid decision: {self.decision!r}")
        if self.decision in UNAVAILABLE_GEP_DECISIONS:
            issues.append(f"decision {self.decision!r} is future-only and unavailable")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.backend_invocation_authorized:
            issues.append("backend_invocation_authorized must be False")
        if self.adapter_execution_authorized:
            issues.append("adapter_execution_authorized must be False")
        if self.network_authorized:
            issues.append("network_authorized must be False")
        if self.subprocess_authorized:
            issues.append("subprocess_authorized must be False")
        if self.shell_authorized:
            issues.append("shell_authorized must be False")
        if self.mutation_authorized:
            issues.append("mutation_authorized must be False")
        if self.apply_authorized:
            issues.append("apply_authorized must be False")
        if self.rollback_authorized:
            issues.append("rollback_authorized must be False")
        if self.commit_authorized:
            issues.append("commit_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.evidence_only:
            issues.append("evidence_only must be True")
        if not self.non_authorizing:
            issues.append("non_authorizing must be True")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "prototype_id": self.prototype_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_preflight_ref": self.source_preflight_ref,
            "source_preflight_digest": self.source_preflight_digest,
            "source_preflight_status": self.source_preflight_status,
            "source_readiness_status": self.source_readiness_status,
            "source_no_go_conditions": sorted(self.source_no_go_conditions),
            "source_missing_evidence": sorted(self.source_missing_evidence),
            "source_failed_checks": sorted(self.source_failed_checks),
            "consumed_evidence_refs": sorted(self.consumed_evidence_refs),
            "prerequisite_summary": self.prerequisite_summary,
            "approval_summary": self.approval_summary,
            "audit_summary": self.audit_summary,
            "rollback_summary": self.rollback_summary,
            "backend_contract_summary": self.backend_contract_summary,
            "adapter_boundary_summary": self.adapter_boundary_summary,
            "artifact_verification_summary": self.artifact_verification_summary,
            "execution_boundary_summary": self.execution_boundary_summary,
            "prototype_status": self.prototype_status,
            "decision": self.decision,
            "decision_reasons": sorted(self.decision_reasons),
            "no_go_conditions": sorted(self.no_go_conditions),
            "missing_prerequisites": sorted(self.missing_prerequisites),
            "failed_prerequisites": sorted(self.failed_prerequisites),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prototype_id": self.prototype_id,
            "phase_id": self.phase_id,
            "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_preflight_ref": self.source_preflight_ref,
            "source_preflight_digest": self.source_preflight_digest,
            "source_preflight_status": self.source_preflight_status,
            "source_readiness_status": self.source_readiness_status,
            "source_no_go_conditions": sorted(self.source_no_go_conditions),
            "source_missing_evidence": sorted(self.source_missing_evidence),
            "source_failed_checks": sorted(self.source_failed_checks),
            "consumed_evidence_refs": sorted(self.consumed_evidence_refs),
            "prerequisite_summary": self.prerequisite_summary,
            "approval_summary": self.approval_summary,
            "audit_summary": self.audit_summary,
            "rollback_summary": self.rollback_summary,
            "backend_contract_summary": self.backend_contract_summary,
            "adapter_boundary_summary": self.adapter_boundary_summary,
            "artifact_verification_summary": self.artifact_verification_summary,
            "execution_boundary_summary": self.execution_boundary_summary,
            "prototype_status": self.prototype_status,
            "decision": self.decision,
            "decision_reasons": sorted(self.decision_reasons),
            "no_go_conditions": sorted(self.no_go_conditions),
            "missing_prerequisites": sorted(self.missing_prerequisites),
            "failed_prerequisites": sorted(self.failed_prerequisites),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GovernedExecutionPreflightPrototype":
        auth = data.get("authorization_summary", {})
        return cls(
            schema_version=data.get("schema_version", _GEP_SCHEMA_VERSION),
            prototype_id=data.get("prototype_id", ""),
            phase_id=data.get("phase_id", "98A"),
            task_id=data.get("task_id", ""),
            generated_at_utc=data.get("generated_at_utc", ""),
            source_preflight_ref=data.get("source_preflight_ref", ""),
            source_preflight_digest=data.get("source_preflight_digest", ""),
            source_preflight_status=data.get("source_preflight_status", ""),
            source_readiness_status=data.get("source_readiness_status", ""),
            source_no_go_conditions=data.get("source_no_go_conditions", []),
            source_missing_evidence=data.get("source_missing_evidence", []),
            source_failed_checks=data.get("source_failed_checks", []),
            consumed_evidence_refs=data.get("consumed_evidence_refs", []),
            prerequisite_summary=data.get("prerequisite_summary", ""),
            approval_summary=data.get("approval_summary", ""),
            audit_summary=data.get("audit_summary", ""),
            rollback_summary=data.get("rollback_summary", ""),
            backend_contract_summary=data.get("backend_contract_summary", ""),
            adapter_boundary_summary=data.get("adapter_boundary_summary", ""),
            artifact_verification_summary=data.get("artifact_verification_summary", ""),
            execution_boundary_summary=data.get("execution_boundary_summary", ""),
            prototype_status=data.get("prototype_status", GEP_BLOCKED),
            decision=data.get("decision", GEP_DECISION_BLOCK),
            decision_reasons=data.get("decision_reasons", []),
            no_go_conditions=data.get("no_go_conditions", []),
            missing_prerequisites=data.get("missing_prerequisites", []),
            failed_prerequisites=data.get("failed_prerequisites", []),
            warnings=data.get("warnings", []),
            execution_available=auth.get("execution_available", False),
            execution_authorized=auth.get("execution_authorized", False),
            backend_invocation_authorized=auth.get("backend_invocation_authorized", False),
            adapter_execution_authorized=auth.get("adapter_execution_authorized", False),
            network_authorized=auth.get("network_authorized", False),
            subprocess_authorized=auth.get("subprocess_authorized", False),
            shell_authorized=auth.get("shell_authorized", False),
            mutation_authorized=auth.get("mutation_authorized", False),
            apply_authorized=auth.get("apply_authorized", False),
            rollback_authorized=auth.get("rollback_authorized", False),
            commit_authorized=auth.get("commit_authorized", False),
            push_authorized=auth.get("push_authorized", False),
            simulation_only=data.get("simulation_only", True),
            no_execution=data.get("no_execution", True),
            evidence_only=data.get("evidence_only", True),
            non_authorizing=data.get("non_authorizing", True),
            digest=data.get("digest", ""),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Prototype builder — consumes Phase 97 preflight
# ═══════════════════════════════════════════════════════════════════════════


def build_governed_execution_preflight_prototype(
    *,
    source_preflight: ExecutionReadinessPreflight | None = None,
    task_id: str = "",
    phase_id: str = "98A",
    load_latest: bool = True,
) -> GovernedExecutionPreflightPrototype:
    """Build a governed execution preflight prototype consuming a 97F preflight.

    Non-executing, non-authorizing, fail-closed.
    """
    import uuid
    now = datetime.now(timezone.utc)
    prototype_id = f"gep-{uuid.uuid4().hex[:12]}"
    generated_at = now.isoformat()

    # Load source preflight if needed
    if source_preflight is None and load_latest:
        source_preflight = load_latest_execution_readiness_preflight()

    # ── Handle missing/invalid source ──────────────────────────────────
    if source_preflight is None:
        proto = GovernedExecutionPreflightPrototype(
            schema_version=_GEP_SCHEMA_VERSION,
            prototype_id=prototype_id,
            phase_id=phase_id,
            task_id=task_id,
            generated_at_utc=generated_at,
            prototype_status=GEP_UNAVAILABLE,
            decision=GEP_DECISION_BLOCK,
            decision_reasons=["source_preflight_missing"],
            missing_prerequisites=["source_preflight"],
            warnings=["No Phase 97 preflight artifact found. Run: pcae execution-readiness preflight --save"],
            simulation_only=True, no_execution=True,
            evidence_only=True, non_authorizing=True,
        )
        proto.digest = proto.compute_digest()
        return proto

    # Validate source preflight
    source_issues = source_preflight.validate()
    source_verification = verify_execution_readiness_preflight(source_preflight)

    # ── Consume source evidence ─────────────────────────────────────────
    prototype = GovernedExecutionPreflightPrototype(
        schema_version=_GEP_SCHEMA_VERSION,
        prototype_id=prototype_id,
        phase_id=phase_id,
        task_id=task_id,
        generated_at_utc=generated_at,
        source_preflight_ref=source_preflight.preflight_id,
        source_preflight_digest=source_preflight.digest,
        source_preflight_status=source_preflight.preflight_status,
        source_readiness_status=source_preflight.readiness_status,
        source_no_go_conditions=list(source_preflight.no_go_conditions),
        source_missing_evidence=list(source_preflight.missing_evidence),
        source_failed_checks=list(source_preflight.failed_checks),
        consumed_evidence_refs=list(source_preflight.evidence_refs),
    )

    # ── Check source safety invariants ──────────────────────────────────
    blocker_reasons: list[str] = []

    # Source validation
    if source_issues:
        blocker_reasons.append(f"source_validation_failed: {'; '.join(source_issues[:3])}")
    if not source_verification.get("valid", False):
        blocker_reasons.append("source_verification_failed")

    # Source no-go conditions
    if source_preflight.no_go_conditions:
        blocker_reasons.append(
            f"source_has_{len(source_preflight.no_go_conditions)}_no_go_conditions"
        )
        prototype.no_go_conditions = list(source_preflight.no_go_conditions)

    # Source authorization check
    auth = source_preflight.to_dict().get("authorization_summary", {})
    for flag_name, flag_value in auth.items():
        if flag_value:
            blocker_reasons.append(f"source_{flag_name}_is_true")
            break

    # Source safety check
    if not source_preflight.no_execution:
        blocker_reasons.append("source_no_execution_is_false")
    if not source_preflight.simulation_only:
        blocker_reasons.append("source_simulation_only_is_false")
    if source_preflight.execution_available:
        blocker_reasons.append("source_execution_available_is_true")

    # ── Prerequisite evaluation ─────────────────────────────────────────
    missing_prereqs: list[str] = []
    failed_prereqs: list[str] = []

    # Evidence
    if source_preflight.missing_evidence:
        missing_prereqs.append(
            f"missing_evidence: {', '.join(source_preflight.missing_evidence[:5])}"
        )

    # Approval
    if source_preflight.approval_status in (PREFLIGHT_APPROVAL_REQUIRED, PREFLIGHT_BLOCKED):
        missing_prereqs.append("human_approval_required")
        prototype.approval_summary = "approval_required"
    else:
        prototype.approval_summary = source_preflight.approval_status

    # Audit
    if source_preflight.audit_readiness_status in (PREFLIGHT_AUDIT_REQUIRED, PREFLIGHT_BLOCKED):
        missing_prereqs.append("audit_readiness_required")
        prototype.audit_summary = "audit_required"
    else:
        prototype.audit_summary = source_preflight.audit_readiness_status

    # Rollback
    if source_preflight.rollback_readiness_status in (PREFLIGHT_ROLLBACK_REQUIRED, PREFLIGHT_BLOCKED):
        missing_prereqs.append("rollback_readiness_required")
        prototype.rollback_summary = "rollback_required"
    else:
        prototype.rollback_summary = source_preflight.rollback_readiness_status

    # Failed checks
    if source_preflight.failed_checks:
        failed_prereqs.extend(source_preflight.failed_checks[:5])

    # ── Determine prototype status and decision ─────────────────────────
    if blocker_reasons:
        prototype.prototype_status = GEP_BLOCKED
        prototype.decision = GEP_DECISION_BLOCK
    elif source_verification.get("valid") and source_issues:
        prototype.prototype_status = GEP_VERIFICATION_FAILED
        prototype.decision = GEP_DECISION_REQUIRE_VERIFICATION
    elif source_preflight.missing_evidence:
        prototype.prototype_status = GEP_EVIDENCE_INCOMPLETE
        prototype.decision = GEP_DECISION_REQUIRE_EVIDENCE
    elif source_preflight.approval_status in (PREFLIGHT_APPROVAL_REQUIRED,):
        prototype.prototype_status = GEP_APPROVAL_REQUIRED
        prototype.decision = GEP_DECISION_REQUIRE_APPROVAL
    elif source_preflight.audit_readiness_status in (PREFLIGHT_AUDIT_REQUIRED,):
        prototype.prototype_status = GEP_AUDIT_REQUIRED
        prototype.decision = GEP_DECISION_REQUIRE_AUDIT_READINESS
    elif source_preflight.rollback_readiness_status in (PREFLIGHT_ROLLBACK_REQUIRED,):
        prototype.prototype_status = GEP_ROLLBACK_REQUIRED
        prototype.decision = GEP_DECISION_REQUIRE_ROLLBACK_READINESS
    elif source_preflight.artifact_verification_status == PREFLIGHT_FAILED_VERIFICATION:
        prototype.prototype_status = GEP_VERIFICATION_FAILED
        prototype.decision = GEP_DECISION_REQUIRE_VERIFICATION
    elif missing_prereqs:
        prototype.prototype_status = GEP_EVIDENCE_INCOMPLETE
        prototype.decision = GEP_DECISION_REQUIRE_EVIDENCE
    else:
        prototype.prototype_status = GEP_READY_FOR_PREFLIGHT_REVIEW
        prototype.decision = GEP_DECISION_READY_FOR_REVIEW_ONLY

    # ── Fill in remaining fields ────────────────────────────────────────
    prototype.decision_reasons = blocker_reasons
    prototype.missing_prerequisites = sorted(missing_prereqs)
    prototype.failed_prerequisites = sorted(failed_prereqs)
    prototype.prerequisite_summary = (
        f"{len(missing_prereqs)} missing, {len(failed_prereqs)} failed"
    )
    prototype.backend_contract_summary = source_preflight.backend_invocation_contract_status
    prototype.adapter_boundary_summary = source_preflight.adapter_boundary_status
    prototype.artifact_verification_summary = source_preflight.artifact_verification_status
    prototype.execution_boundary_summary = source_preflight.execution_boundary_proof_status

    # Safety invariants
    prototype.simulation_only = True
    prototype.no_execution = True
    prototype.evidence_only = True
    prototype.non_authorizing = True

    # Warnings
    warnings_list: list[str] = [
        "execution_remains_unavailable",
        "prototype_is_evidence_only_and_non_authorizing",
    ]
    if blocker_reasons:
        warnings_list.append(f"blocked: {'; '.join(blocker_reasons[:3])}")
    if missing_prereqs:
        warnings_list.append(f"missing_prerequisites: {len(missing_prereqs)}")
    prototype.warnings = sorted(warnings_list)

    prototype.digest = prototype.compute_digest()
    return prototype


# ═══════════════════════════════════════════════════════════════════════════
# Prototype persistence and verification
# ═══════════════════════════════════════════════════════════════════════════


def save_governed_execution_preflight_prototype(
    prototype: GovernedExecutionPreflightPrototype,
) -> Path:
    dir_path = _gep_dir_path()
    dir_path.mkdir(parents=True, exist_ok=True)
    prototype.digest = prototype.compute_digest()
    payload = prototype.to_dict()
    canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    ts_path = _gep_timestamped_path(ts)
    ts_path.write_text(canonical, encoding="utf-8")
    latest_path = _gep_latest_path()
    latest_path.write_text(canonical, encoding="utf-8")
    return ts_path


def load_latest_governed_execution_preflight_prototype() -> GovernedExecutionPreflightPrototype | None:
    latest_path = _gep_latest_path()
    if not latest_path.exists():
        return None
    try:
        raw = latest_path.read_text(encoding="utf-8")
        data = _json.loads(raw)
        return GovernedExecutionPreflightPrototype.from_dict(data)
    except (_json.JSONDecodeError, KeyError, TypeError):
        return None


def verify_governed_execution_preflight_prototype(
    prototype: GovernedExecutionPreflightPrototype | None = None,
    *,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    if prototype is None:
        return {
            "valid": False,
            "issues": ["no_prototype_artifact_found"],
            "prototype_present": False,
        }
    if prototype.schema_version != _GEP_SCHEMA_VERSION:
        issues.append(f"unknown schema_version: {prototype.schema_version!r}")
    if expected_digest is not None:
        if prototype.digest != expected_digest:
            issues.append("digest_mismatch")
    elif prototype.digest:
        computed = prototype.compute_digest()
        if computed != prototype.digest:
            issues.append("digest_mismatch: computed_differs_from_stored")
    validate_issues = prototype.validate()
    issues.extend(validate_issues)
    if not prototype.simulation_only:
        issues.append("simulation_only must be True")
    if not prototype.no_execution:
        issues.append("no_execution must be True")
    if not prototype.evidence_only:
        issues.append("evidence_only must be True")
    if not prototype.non_authorizing:
        issues.append("non_authorizing must be True")
    auth_checks = [
        ("execution_available", prototype.execution_available),
        ("execution_authorized", prototype.execution_authorized),
        ("push_authorized", prototype.push_authorized),
    ]
    for flag_name, flag_value in auth_checks:
        if flag_value:
            issues.append(f"{flag_name} must be False")
    if prototype.decision in UNAVAILABLE_GEP_DECISIONS:
        issues.append(f"decision {prototype.decision!r} is future-only")
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "prototype_present": True,
        "prototype_id": prototype.prototype_id,
        "digest": prototype.digest,
        "prototype_status": prototype.prototype_status,
        "decision": prototype.decision,
        "no_execution_confirmed": prototype.no_execution and not prototype.execution_available,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 99A — Governed execution attempt boundary design
# ═══════════════════════════════════════════════════════════════════════════

_GEA_SCHEMA_VERSION = "1.0"

# ── Attempt states ─────────────────────────────────────────────────────
GEA_UNAVAILABLE = "unavailable"
GEA_NOT_REQUESTED = "not_requested"
GEA_REQUEST_DRAFTED = "request_drafted"
GEA_PREFLIGHT_REQUIRED = "preflight_required"
GEA_PREFLIGHT_FAILED = "preflight_failed"
GEA_APPROVAL_REQUIRED = "approval_required"
GEA_AUDIT_REQUIRED = "audit_required"
GEA_ROLLBACK_REQUIRED = "rollback_required"
GEA_DENIED = "denied"
GEA_ABORTED_BEFORE_EXECUTION = "aborted_before_execution"
GEA_BLOCKED_BY_NO_GO = "blocked_by_no_go"
GEA_BLOCKED_BY_MISSING_EVIDENCE = "blocked_by_missing_evidence"
GEA_BLOCKED_BY_FAILED_VERIFICATION = "blocked_by_failed_verification"
GEA_READY_FOR_DESIGN_REVIEW_ONLY = "ready_for_design_review_only"

# Future-only — never available
GEA_EXECUTING_FUTURE = "executing"
GEA_EXECUTED_FUTURE = "executed"
GEA_RUNNING_FUTURE = "running"
GEA_INVOKED_FUTURE = "invoked"
GEA_APPLIED_FUTURE = "applied"
GEA_COMMITTED_FUTURE = "committed"
GEA_PUSHED_FUTURE = "pushed"
GEA_SUCCESS_FUTURE = "success"
GEA_EXECUTION_COMPLETE_FUTURE = "execution_complete"

VALID_GEA_STATES: frozenset[str] = frozenset({
    GEA_UNAVAILABLE, GEA_NOT_REQUESTED, GEA_REQUEST_DRAFTED,
    GEA_PREFLIGHT_REQUIRED, GEA_PREFLIGHT_FAILED,
    GEA_APPROVAL_REQUIRED, GEA_AUDIT_REQUIRED, GEA_ROLLBACK_REQUIRED,
    GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
    GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
    GEA_BLOCKED_BY_FAILED_VERIFICATION, GEA_READY_FOR_DESIGN_REVIEW_ONLY,
})

UNAVAILABLE_GEA_STATES: frozenset[str] = frozenset({
    GEA_EXECUTING_FUTURE, GEA_EXECUTED_FUTURE, GEA_RUNNING_FUTURE,
    GEA_INVOKED_FUTURE, GEA_APPLIED_FUTURE, GEA_COMMITTED_FUTURE,
    GEA_PUSHED_FUTURE, GEA_SUCCESS_FUTURE, GEA_EXECUTION_COMPLETE_FUTURE,
})

# ── Denial reasons ─────────────────────────────────────────────────────
GEA_DENIED_MISSING_PHASE97 = "denied_missing_phase97_preflight"
GEA_DENIED_INVALID_PHASE97 = "denied_invalid_phase97_preflight"
GEA_DENIED_MISSING_PHASE98 = "denied_missing_phase98_preflight"
GEA_DENIED_INVALID_PHASE98 = "denied_invalid_phase98_preflight"
GEA_DENIED_NO_GO_PRESENT = "denied_no_go_present"
GEA_DENIED_MISSING_APPROVAL = "denied_missing_human_approval"
GEA_DENIED_APPROVAL_EXPIRED = "denied_approval_expired"
GEA_DENIED_APPROVAL_REVOKED = "denied_approval_revoked"
GEA_DENIED_MISSING_AUDIT = "denied_missing_audit_readiness"
GEA_DENIED_MISSING_ROLLBACK = "denied_missing_rollback_readiness"
GEA_DENIED_FAILED_VERIFICATION = "denied_failed_artifact_verification"
GEA_DENIED_FAILED_REF_VALIDATION = "denied_failed_reference_validation"
GEA_DENIED_UNKNOWN_SCHEMA = "denied_unknown_schema"
GEA_DENIED_CONFLICTING_FLAGS = "denied_conflicting_safety_flags"
GEA_DENIED_UNSAFE_AUTH_FLAG = "denied_unsafe_authorization_flag"
GEA_DENIED_BACKEND_REQUESTED = "denied_requested_backend_invocation"
GEA_DENIED_ADAPTER_REQUESTED = "denied_requested_adapter_execution"
GEA_DENIED_SUBPROCESS_REQUESTED = "denied_requested_subprocess"
GEA_DENIED_SHELL_REQUESTED = "denied_requested_shell"
GEA_DENIED_NETWORK_REQUESTED = "denied_requested_network"
GEA_DENIED_TELEGRAM_INBOUND = "denied_requested_telegram_inbound"
GEA_DENIED_APPLY_REQUESTED = "denied_requested_apply"
GEA_DENIED_ROLLBACK_EXEC_REQUESTED = "denied_requested_rollback_execution"
GEA_DENIED_COMMIT_PUSH_REQUESTED = "denied_requested_commit_push"
GEA_DENIED_BYPASS_PERMISSIONS = "denied_bypass_permissions"
GEA_DENIED_SECRET_DETECTED = "denied_secret_material_detected"

VALID_GEA_DENIAL_REASONS: frozenset[str] = frozenset({
    GEA_DENIED_MISSING_PHASE97, GEA_DENIED_INVALID_PHASE97,
    GEA_DENIED_MISSING_PHASE98, GEA_DENIED_INVALID_PHASE98,
    GEA_DENIED_NO_GO_PRESENT, GEA_DENIED_MISSING_APPROVAL,
    GEA_DENIED_APPROVAL_EXPIRED, GEA_DENIED_APPROVAL_REVOKED,
    GEA_DENIED_MISSING_AUDIT, GEA_DENIED_MISSING_ROLLBACK,
    GEA_DENIED_FAILED_VERIFICATION, GEA_DENIED_FAILED_REF_VALIDATION,
    GEA_DENIED_UNKNOWN_SCHEMA, GEA_DENIED_CONFLICTING_FLAGS,
    GEA_DENIED_UNSAFE_AUTH_FLAG,
    GEA_DENIED_BACKEND_REQUESTED, GEA_DENIED_ADAPTER_REQUESTED,
    GEA_DENIED_SUBPROCESS_REQUESTED, GEA_DENIED_SHELL_REQUESTED,
    GEA_DENIED_NETWORK_REQUESTED, GEA_DENIED_TELEGRAM_INBOUND,
    GEA_DENIED_APPLY_REQUESTED, GEA_DENIED_ROLLBACK_EXEC_REQUESTED,
    GEA_DENIED_COMMIT_PUSH_REQUESTED,
    GEA_DENIED_BYPASS_PERMISSIONS, GEA_DENIED_SECRET_DETECTED,
})


# ═══════════════════════════════════════════════════════════════════════════
# GovernedExecutionAttemptBoundary — design-only, non-executing
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class GovernedExecutionAttemptBoundary:
    """Design-only model for a future governed execution attempt boundary.

    Non-executing, non-authorizing, evidence-only. No attempt is possible
    in the current system — this is a design artifact for future phases.
    """

    schema_version: str = _GEA_SCHEMA_VERSION
    attempt_boundary_id: str = ""
    phase_id: str = "99A"
    task_id: str = ""
    generated_at_utc: str = ""

    attempt_state: str = GEA_UNAVAILABLE
    attempt_decision: str = GEA_DENIED

    phase97_preflight_ref: str = ""
    phase97_preflight_digest: str = ""
    phase98_preflight_ref: str = ""
    phase98_preflight_digest: str = ""

    approval_ref: str = ""
    audit_readiness_ref: str = ""
    rollback_readiness_ref: str = ""
    backend_contract_ref: str = ""
    adapter_boundary_ref: str = ""
    artifact_verification_ref: str = ""
    no_go_review_ref: str = ""
    execution_boundary_proof_ref: str = ""

    hard_no_go_conditions: list[str] = field(default_factory=list)
    missing_prerequisites: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)
    abort_reasons: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True
    design_only: bool = True

    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _GEA_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.attempt_state not in VALID_GEA_STATES:
            issues.append(f"invalid attempt_state: {self.attempt_state!r}")
        if self.attempt_state in UNAVAILABLE_GEA_STATES:
            issues.append(f"attempt_state {self.attempt_state!r} is future-only")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.design_only:
            issues.append("design_only must be True")
        for reason in self.denial_reasons:
            if reason not in VALID_GEA_DENIAL_REASONS:
                issues.append(f"unknown denial_reason: {reason!r}")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "attempt_boundary_id": self.attempt_boundary_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "attempt_state": self.attempt_state,
            "attempt_decision": self.attempt_decision,
            "phase97_preflight_ref": self.phase97_preflight_ref,
            "phase97_preflight_digest": self.phase97_preflight_digest,
            "phase98_preflight_ref": self.phase98_preflight_ref,
            "phase98_preflight_digest": self.phase98_preflight_digest,
            "denial_reasons": sorted(self.denial_reasons),
            "abort_reasons": sorted(self.abort_reasons),
            "hard_no_go_conditions": sorted(self.hard_no_go_conditions),
            "missing_prerequisites": sorted(self.missing_prerequisites),
            "failed_checks": sorted(self.failed_checks),
            "warnings": sorted(self.warnings),
            "evidence_refs": sorted(self.evidence_refs),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_boundary_id": self.attempt_boundary_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "attempt_state": self.attempt_state,
            "attempt_decision": self.attempt_decision,
            "phase97_preflight_ref": self.phase97_preflight_ref,
            "phase97_preflight_digest": self.phase97_preflight_digest,
            "phase98_preflight_ref": self.phase98_preflight_ref,
            "phase98_preflight_digest": self.phase98_preflight_digest,
            "approval_ref": self.approval_ref,
            "audit_readiness_ref": self.audit_readiness_ref,
            "rollback_readiness_ref": self.rollback_readiness_ref,
            "backend_contract_ref": self.backend_contract_ref,
            "adapter_boundary_ref": self.adapter_boundary_ref,
            "artifact_verification_ref": self.artifact_verification_ref,
            "no_go_review_ref": self.no_go_review_ref,
            "execution_boundary_proof_ref": self.execution_boundary_proof_ref,
            "hard_no_go_conditions": sorted(self.hard_no_go_conditions),
            "missing_prerequisites": sorted(self.missing_prerequisites),
            "failed_checks": sorted(self.failed_checks),
            "denial_reasons": sorted(self.denial_reasons),
            "abort_reasons": sorted(self.abort_reasons),
            "evidence_refs": sorted(self.evidence_refs),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
            "digest": self.digest,
        }


# ═══════════════════════════════════════════════════════════════════════════
# NoGoEnforcementEvidence — design-only, non-executing, non-authorizing
# Phase 100B — Execution Boundary No-Go Enforcement Model
# ═══════════════════════════════════════════════════════════════════════════

_NGE_SCHEMA_VERSION = "1.0"

# ── No-go categories (17) ────────────────────────────────────────────────
NGE_CATEGORY_ARTIFACT_TRUST = "artifact_trust"
NGE_CATEGORY_PREREQUISITE = "prerequisite"
NGE_CATEGORY_AUTHORIZATION_FLAG = "authorization_flag"
NGE_CATEGORY_SAFETY_FLAG = "safety_flag"
NGE_CATEGORY_APPROVAL = "approval"
NGE_CATEGORY_AUDIT = "audit"
NGE_CATEGORY_ROLLBACK = "rollback"
NGE_CATEGORY_BACKEND_ADAPTER = "backend_adapter"
NGE_CATEGORY_SHELL_SUBPROCESS_NETWORK = "shell_subprocess_network"
NGE_CATEGORY_MUTATION_APPLY = "mutation_apply"
NGE_CATEGORY_COMMIT_PUSH = "commit_push"
NGE_CATEGORY_REPORT_NOTIFICATION = "report_notification"
NGE_CATEGORY_OPERATOR_RUNTIME_MODE = "operator_runtime_mode"
NGE_CATEGORY_SECRET_EXPOSURE = "secret_exposure"
NGE_CATEGORY_COMPATIBILITY_SCHEMA = "compatibility_schema"
NGE_CATEGORY_STALE_REPLAY = "stale_replay"
NGE_CATEGORY_UNKNOWN_UNSUPPORTED = "unknown_unsupported"

VALID_NGE_CATEGORIES: frozenset[str] = frozenset({
    NGE_CATEGORY_ARTIFACT_TRUST, NGE_CATEGORY_PREREQUISITE,
    NGE_CATEGORY_AUTHORIZATION_FLAG, NGE_CATEGORY_SAFETY_FLAG,
    NGE_CATEGORY_APPROVAL, NGE_CATEGORY_AUDIT, NGE_CATEGORY_ROLLBACK,
    NGE_CATEGORY_BACKEND_ADAPTER, NGE_CATEGORY_SHELL_SUBPROCESS_NETWORK,
    NGE_CATEGORY_MUTATION_APPLY, NGE_CATEGORY_COMMIT_PUSH,
    NGE_CATEGORY_REPORT_NOTIFICATION, NGE_CATEGORY_OPERATOR_RUNTIME_MODE,
    NGE_CATEGORY_SECRET_EXPOSURE, NGE_CATEGORY_COMPATIBILITY_SCHEMA,
    NGE_CATEGORY_STALE_REPLAY, NGE_CATEGORY_UNKNOWN_UNSUPPORTED,
})

# ── Severities (6) ───────────────────────────────────────────────────────
NGE_SEVERITY_CRITICAL_BLOCKER = "critical_blocker"
NGE_SEVERITY_HARD_BLOCKER = "hard_blocker"
NGE_SEVERITY_MISSING_PREREQUISITE = "missing_prerequisite"
NGE_SEVERITY_TRUST_FAILURE = "trust_failure"
NGE_SEVERITY_UNSUPPORTED_REQUEST = "unsupported_request"
NGE_SEVERITY_REPORTING_FAILURE = "reporting_failure"

VALID_NGE_SEVERITIES: frozenset[str] = frozenset({
    NGE_SEVERITY_CRITICAL_BLOCKER, NGE_SEVERITY_HARD_BLOCKER,
    NGE_SEVERITY_MISSING_PREREQUISITE, NGE_SEVERITY_TRUST_FAILURE,
    NGE_SEVERITY_UNSUPPORTED_REQUEST, NGE_SEVERITY_REPORTING_FAILURE,
})

# ── Evaluation statuses ──────────────────────────────────────────────────
NGE_STATUS_DENIED = "denied"
NGE_STATUS_BLOCKED = "blocked"
NGE_STATUS_EVIDENCE_INCOMPLETE = "evidence_incomplete"

VALID_NGE_STATUSES: frozenset[str] = frozenset({
    NGE_STATUS_DENIED, NGE_STATUS_BLOCKED, NGE_STATUS_EVIDENCE_INCOMPLETE,
})

# ── Evaluation decisions ─────────────────────────────────────────────────
NGE_DECISION_BLOCKED = "blocked"
NGE_DECISION_DENY = "deny"

VALID_NGE_DECISIONS: frozenset[str] = frozenset({
    NGE_DECISION_BLOCKED, NGE_DECISION_DENY,
})

# ── 30 no-go condition identifiers (from 100A gap analysis) ──────────────
NGE_MISSING_PHASE97_PREFLIGHT = "MISSING_PHASE97_PREFLIGHT"
NGE_MISSING_PHASE98_PREFLIGHT = "MISSING_PHASE98_PREFLIGHT"
NGE_MISSING_PHASE99_ATTEMPT = "MISSING_PHASE99_ATTEMPT"
NGE_ARTIFACT_TAMPERED = "ARTIFACT_TAMPERED"
NGE_UNKNOWN_SCHEMA = "UNKNOWN_SCHEMA"
NGE_STALE_ARTIFACT = "STALE_ARTIFACT"
NGE_AUTH_FLAG_TRUE = "AUTH_FLAG_TRUE"
NGE_NO_EXECUTION_FALSE = "NO_EXECUTION_FALSE"
NGE_SIMULATION_ONLY_FALSE = "SIMULATION_ONLY_FALSE"
NGE_EVIDENCE_ONLY_FALSE = "EVIDENCE_ONLY_FALSE"
NGE_NON_AUTHORIZING_FALSE = "NON_AUTHORIZING_FALSE"
NGE_MISSING_APPROVAL_ENFORCEMENT = "MISSING_APPROVAL_ENFORCEMENT"
NGE_MISSING_AUDIT_PERSISTENCE = "MISSING_AUDIT_PERSISTENCE"
NGE_MISSING_ROLLBACK_PLAN = "MISSING_ROLLBACK_PLAN"
NGE_MISSING_DENIAL_ENFORCEMENT = "MISSING_DENIAL_ENFORCEMENT"
NGE_MISSING_BACKEND_ALLOWLIST = "MISSING_BACKEND_ALLOWLIST"
NGE_MISSING_ADAPTER_ALLOWLIST = "MISSING_ADAPTER_ALLOWLIST"
NGE_MISSING_SHELL_BOUNDARY = "MISSING_SHELL_BOUNDARY"
NGE_MISSING_OUTPUT_CAPTURE = "MISSING_OUTPUT_CAPTURE"
NGE_MISSING_SECRET_REDACTION = "MISSING_SECRET_REDACTION"
NGE_MISSING_TIMEOUT_ABORT = "MISSING_TIMEOUT_ABORT"
NGE_MISSING_REPORT_COMPLETENESS = "MISSING_REPORT_COMPLETENESS"
NGE_MISSING_NOTIFICATION_VISIBILITY = "MISSING_NOTIFICATION_VISIBILITY"
NGE_BYPASS_PERMISSIONS = "BYPASS_PERMISSIONS"
NGE_RAW_GIT_OR_FORCE = "RAW_GIT_OR_FORCE"
NGE_TELEGRAM_INBOUND = "TELEGRAM_INBOUND"
NGE_AUTOMATIC_APPLY = "AUTOMATIC_APPLY"
NGE_ROLLBACK_WITHOUT_GOVERNANCE = "ROLLBACK_WITHOUT_GOVERNANCE"
NGE_PREMATURE_BACKEND_INVOCATION = "PREMATURE_BACKEND_INVOCATION"
NGE_EVIDENCE_AS_AUTHORIZATION = "EVIDENCE_AS_AUTHORIZATION"

VALID_NGE_CONDITIONS: frozenset[str] = frozenset({
    NGE_MISSING_PHASE97_PREFLIGHT, NGE_MISSING_PHASE98_PREFLIGHT,
    NGE_MISSING_PHASE99_ATTEMPT, NGE_ARTIFACT_TAMPERED,
    NGE_UNKNOWN_SCHEMA, NGE_STALE_ARTIFACT, NGE_AUTH_FLAG_TRUE,
    NGE_NO_EXECUTION_FALSE, NGE_SIMULATION_ONLY_FALSE,
    NGE_EVIDENCE_ONLY_FALSE, NGE_NON_AUTHORIZING_FALSE,
    NGE_MISSING_APPROVAL_ENFORCEMENT, NGE_MISSING_AUDIT_PERSISTENCE,
    NGE_MISSING_ROLLBACK_PLAN, NGE_MISSING_DENIAL_ENFORCEMENT,
    NGE_MISSING_BACKEND_ALLOWLIST, NGE_MISSING_ADAPTER_ALLOWLIST,
    NGE_MISSING_SHELL_BOUNDARY, NGE_MISSING_OUTPUT_CAPTURE,
    NGE_MISSING_SECRET_REDACTION, NGE_MISSING_TIMEOUT_ABORT,
    NGE_MISSING_REPORT_COMPLETENESS, NGE_MISSING_NOTIFICATION_VISIBILITY,
    NGE_BYPASS_PERMISSIONS, NGE_RAW_GIT_OR_FORCE,
    NGE_TELEGRAM_INBOUND, NGE_AUTOMATIC_APPLY,
    NGE_ROLLBACK_WITHOUT_GOVERNANCE, NGE_PREMATURE_BACKEND_INVOCATION,
    NGE_EVIDENCE_AS_AUTHORIZATION,
})


@dataclass
class NoGoEnforcementEvidence:
    """Design-only model for no-go enforcement evidence.

    Non-executing, non-authorizing, evidence-only. Defines how hard no-go
    conditions block any future execution-capable boundary. No runtime
    enforcement exists. No execution is enabled.
    """

    schema_version: str = _NGE_SCHEMA_VERSION
    no_go_evaluation_id: str = ""
    phase_id: str = "100B"
    task_id: str = ""
    generated_at_utc: str = ""

    evaluation_status: str = NGE_STATUS_DENIED
    evaluation_decision: str = NGE_DECISION_BLOCKED

    source_gap_analysis_ref: str = ""
    phase97_preflight_ref: str = ""
    phase98_preflight_ref: str = ""
    phase99_attempt_boundary_ref: str = ""

    checked_no_go_conditions: list[str] = field(default_factory=list)
    triggered_no_go_conditions: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)
    override_attempts: list[str] = field(default_factory=list)
    unknown_conditions: list[str] = field(default_factory=list)
    unsupported_requests: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # All 12 auth flags — must remain False
    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    # All 5 safety flags — must remain True
    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True
    design_only: bool = True

    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _NGE_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.evaluation_status not in VALID_NGE_STATUSES:
            issues.append(f"invalid evaluation_status: {self.evaluation_status!r}")
        if self.evaluation_decision not in VALID_NGE_DECISIONS:
            issues.append(f"invalid evaluation_decision: {self.evaluation_decision!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.design_only:
            issues.append("design_only must be True")
        for condition in self.triggered_no_go_conditions:
            if condition not in VALID_NGE_CONDITIONS:
                issues.append(f"unknown no-go condition: {condition!r}")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "no_go_evaluation_id": self.no_go_evaluation_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "evaluation_status": self.evaluation_status,
            "evaluation_decision": self.evaluation_decision,
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "checked_no_go_conditions": sorted(self.checked_no_go_conditions),
            "missing_evidence": sorted(self.missing_evidence),
            "failed_checks": sorted(self.failed_checks),
            "denial_reasons": sorted(self.denial_reasons),
            "unknown_conditions": sorted(self.unknown_conditions),
            "unsupported_requests": sorted(self.unsupported_requests),
            "warnings": sorted(self.warnings),
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "no_go_evaluation_id": self.no_go_evaluation_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "evaluation_status": self.evaluation_status,
            "evaluation_decision": self.evaluation_decision,
            "source_gap_analysis_ref": self.source_gap_analysis_ref,
            "phase97_preflight_ref": self.phase97_preflight_ref,
            "phase98_preflight_ref": self.phase98_preflight_ref,
            "phase99_attempt_boundary_ref": self.phase99_attempt_boundary_ref,
            "checked_no_go_conditions": sorted(self.checked_no_go_conditions),
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "missing_evidence": sorted(self.missing_evidence),
            "failed_checks": sorted(self.failed_checks),
            "denial_reasons": sorted(self.denial_reasons),
            "override_attempts": sorted(self.override_attempts),
            "unknown_conditions": sorted(self.unknown_conditions),
            "unsupported_requests": sorted(self.unsupported_requests),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
            "digest": self.digest,
        }


# ═══════════════════════════════════════════════════════════════════════════
# RuntimeEnforcementCoordinator — design-only, non-executing, non-authorizing
# Phase 103A — Runtime Enforcement Coordinator Contract Design
# ═══════════════════════════════════════════════════════════════════════════

_REC_SCHEMA_VERSION = "1.0"

REC_STATUS_UNAVAILABLE = "unavailable"
REC_STATUS_NOT_STARTED = "not_started"
REC_STATUS_INPUT_COLLECTION_FAILED = "input_collection_failed"
REC_STATUS_EVIDENCE_BUNDLE_UNAVAILABLE = "evidence_bundle_unavailable"
REC_STATUS_DECISION_UNAVAILABLE = "decision_unavailable"
REC_STATUS_PREREQUISITES_FAILED = "prerequisites_failed"
REC_STATUS_BLOCKED = "blocked"
REC_STATUS_DENIED = "denied"
REC_STATUS_FAIL_CLOSED = "fail_closed"
REC_STATUS_DESIGN_REVIEW = "ready_for_design_review_only"

VALID_REC_STATUSES: frozenset[str] = frozenset({
    REC_STATUS_UNAVAILABLE, REC_STATUS_NOT_STARTED,
    REC_STATUS_INPUT_COLLECTION_FAILED, REC_STATUS_EVIDENCE_BUNDLE_UNAVAILABLE,
    REC_STATUS_DECISION_UNAVAILABLE, REC_STATUS_PREREQUISITES_FAILED,
    REC_STATUS_BLOCKED, REC_STATUS_DENIED, REC_STATUS_FAIL_CLOSED,
    REC_STATUS_DESIGN_REVIEW,
})

REC_RESULT_DENIED = "denied"
REC_RESULT_FAIL_CLOSED = "fail_closed"
REC_RESULT_BLOCKED_MISSING_BUNDLE = "blocked_by_missing_evidence_bundle"
REC_RESULT_BLOCKED_MISSING_DECISION = "blocked_by_missing_decision"
REC_RESULT_BLOCKED_BUNDLE_VERIFICATION = "blocked_by_failed_bundle_verification"
REC_RESULT_BLOCKED_DECISION_VERIFICATION = "blocked_by_failed_decision_verification"
REC_RESULT_BLOCKED_NO_GO = "blocked_by_no_go"
REC_RESULT_BLOCKED_APPROVAL = "blocked_by_missing_approval"
REC_RESULT_BLOCKED_AUDIT = "blocked_by_missing_audit"
REC_RESULT_BLOCKED_ROLLBACK = "blocked_by_missing_rollback"
REC_RESULT_BLOCKED_REPORT_TRUST = "blocked_by_report_trust_failure"
REC_RESULT_BLOCKED_NOTIFICATION_TRUST = "blocked_by_notification_trust_failure"
REC_RESULT_BLOCKED_UNSUPPORTED_SURFACE = "blocked_by_unsupported_surface"
REC_RESULT_BLOCKED_FUTURE_ONLY = "blocked_by_future_only_step"
REC_RESULT_EVIDENCE_ONLY = "evidence_only"
REC_RESULT_DESIGN_REVIEW = "design_review_only"

VALID_REC_RESULTS: frozenset[str] = frozenset({
    REC_RESULT_DENIED, REC_RESULT_FAIL_CLOSED,
    REC_RESULT_BLOCKED_MISSING_BUNDLE, REC_RESULT_BLOCKED_MISSING_DECISION,
    REC_RESULT_BLOCKED_BUNDLE_VERIFICATION, REC_RESULT_BLOCKED_DECISION_VERIFICATION,
    REC_RESULT_BLOCKED_NO_GO, REC_RESULT_BLOCKED_APPROVAL,
    REC_RESULT_BLOCKED_AUDIT, REC_RESULT_BLOCKED_ROLLBACK,
    REC_RESULT_BLOCKED_REPORT_TRUST, REC_RESULT_BLOCKED_NOTIFICATION_TRUST,
    REC_RESULT_BLOCKED_UNSUPPORTED_SURFACE, REC_RESULT_BLOCKED_FUTURE_ONLY,
    REC_RESULT_EVIDENCE_ONLY, REC_RESULT_DESIGN_REVIEW,
})

REC_STEP_LOAD_BUNDLE = "load_evidence_bundle"
REC_STEP_VERIFY_BUNDLE = "verify_bundle_digest"
REC_STEP_LOAD_DECISION = "load_decision_artifact"
REC_STEP_VERIFY_DECISION = "verify_decision_digest"
REC_STEP_COMPARE_BINDING = "compare_bundle_decision_binding"
REC_STEP_EVAL_NO_GO = "evaluate_no_go"
REC_STEP_EVAL_APPROVAL = "evaluate_approval"
REC_STEP_EVAL_AUDIT = "evaluate_audit"
REC_STEP_EVAL_ROLLBACK = "evaluate_rollback"
REC_STEP_EVAL_REPORT_TRUST = "evaluate_report_trust"
REC_STEP_EVAL_NOTIFICATION_TRUST = "evaluate_notification_trust"
REC_STEP_EVAL_SCOPE = "evaluate_scope_binding"
REC_STEP_EVAL_IDENTITY = "evaluate_identity_binding"
REC_STEP_EVAL_SURFACE = "evaluate_requested_surface"
REC_STEP_DENY_UNSUPPORTED = "deny_unsupported_surface"
REC_STEP_PRODUCE = "produce_coordinator_artifact"

ALL_REC_STEPS: tuple[str, ...] = (
    REC_STEP_LOAD_BUNDLE, REC_STEP_VERIFY_BUNDLE, REC_STEP_LOAD_DECISION,
    REC_STEP_VERIFY_DECISION, REC_STEP_COMPARE_BINDING, REC_STEP_EVAL_NO_GO,
    REC_STEP_EVAL_APPROVAL, REC_STEP_EVAL_AUDIT, REC_STEP_EVAL_ROLLBACK,
    REC_STEP_EVAL_REPORT_TRUST, REC_STEP_EVAL_NOTIFICATION_TRUST,
    REC_STEP_EVAL_SCOPE, REC_STEP_EVAL_IDENTITY, REC_STEP_EVAL_SURFACE,
    REC_STEP_DENY_UNSUPPORTED, REC_STEP_PRODUCE,
)


@dataclass
class RuntimeEnforcementCoordinator:
    """Design-only model for a future runtime enforcement coordinator.

    Non-executing, non-authorizing, evidence-only. Orchestrates loading
    evidence bundles and decision artifacts, evaluating prerequisites,
    and producing a coordinator artifact. Does not enforce.
    """

    schema_version: str = _REC_SCHEMA_VERSION
    coordinator_id: str = ""
    phase_id: str = "103A"
    task_id: str = ""
    generated_at_utc: str = ""

    source_evidence_bundle_ref: str = ""
    source_evidence_bundle_digest: str = ""
    source_decision_ref: str = ""
    source_decision_digest: str = ""

    coordinator_status: str = REC_STATUS_NOT_STARTED
    coordinator_result: str = REC_RESULT_DENIED
    coordinator_reason: str = ""

    requested_surface: list[str] = field(default_factory=list)
    evaluated_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    stale_inputs: list[str] = field(default_factory=list)
    tampered_inputs: list[str] = field(default_factory=list)
    contradictory_inputs: list[str] = field(default_factory=list)
    triggered_no_go_conditions: list[str] = field(default_factory=list)
    denied_steps: list[str] = field(default_factory=list)
    blocked_steps: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)
    future_only_steps: list[str] = field(default_factory=list)
    unsupported_requests: list[str] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)
    fail_closed_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True
    design_only: bool = True

    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _REC_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.coordinator_status not in VALID_REC_STATUSES:
            issues.append(f"invalid coordinator_status: {self.coordinator_status!r}")
        if self.coordinator_result not in VALID_REC_RESULTS:
            issues.append(f"invalid coordinator_result: {self.coordinator_result!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.design_only:
            issues.append("design_only must be True")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "coordinator_id": self.coordinator_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_evidence_bundle_ref": self.source_evidence_bundle_ref,
            "source_evidence_bundle_digest": self.source_evidence_bundle_digest,
            "source_decision_ref": self.source_decision_ref,
            "source_decision_digest": self.source_decision_digest,
            "coordinator_status": self.coordinator_status,
            "coordinator_result": self.coordinator_result,
            "coordinator_reason": self.coordinator_reason,
            "requested_surface": sorted(self.requested_surface),
            "evaluated_inputs": sorted(self.evaluated_inputs),
            "missing_inputs": sorted(self.missing_inputs),
            "stale_inputs": sorted(self.stale_inputs),
            "tampered_inputs": sorted(self.tampered_inputs),
            "contradictory_inputs": sorted(self.contradictory_inputs),
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "denied_steps": sorted(self.denied_steps),
            "blocked_steps": sorted(self.blocked_steps),
            "skipped_steps": sorted(self.skipped_steps),
            "future_only_steps": sorted(self.future_only_steps),
            "unsupported_requests": sorted(self.unsupported_requests),
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "warnings": sorted(self.warnings),
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "coordinator_id": self.coordinator_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_evidence_bundle_ref": self.source_evidence_bundle_ref,
            "source_evidence_bundle_digest": self.source_evidence_bundle_digest,
            "source_decision_ref": self.source_decision_ref,
            "source_decision_digest": self.source_decision_digest,
            "coordinator_status": self.coordinator_status,
            "coordinator_result": self.coordinator_result,
            "coordinator_reason": self.coordinator_reason,
            "requested_surface": sorted(self.requested_surface),
            "evaluated_inputs": sorted(self.evaluated_inputs),
            "missing_inputs": sorted(self.missing_inputs),
            "stale_inputs": sorted(self.stale_inputs),
            "tampered_inputs": sorted(self.tampered_inputs),
            "contradictory_inputs": sorted(self.contradictory_inputs),
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "denied_steps": sorted(self.denied_steps),
            "blocked_steps": sorted(self.blocked_steps),
            "skipped_steps": sorted(self.skipped_steps),
            "future_only_steps": sorted(self.future_only_steps),
            "unsupported_requests": sorted(self.unsupported_requests),
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
            "digest": self.digest,
        }


# ═══════════════════════════════════════════════════════════════════════════
# RuntimeEnforcementEvidenceBundle — design-only, non-executing
# Phase 101B — Runtime Enforcement Evidence Bundle Contract Design
# ═══════════════════════════════════════════════════════════════════════════

_REEB_SCHEMA_VERSION = "1.0"

REEB_STATUS_UNAVAILABLE = "unavailable"
REEB_STATUS_NOT_COLLECTED = "not_collected"
REEB_STATUS_INCOMPLETE = "incomplete"
REEB_STATUS_COLLECTED = "collected"
REEB_STATUS_INVALID = "invalid"
REEB_STATUS_BLOCKED_BY_NO_GO = "blocked_by_no_go"
REEB_STATUS_BLOCKED_BY_MISSING = "blocked_by_missing_required_evidence"
REEB_STATUS_BLOCKED_BY_VERIFICATION = "blocked_by_failed_verification"
REEB_STATUS_READY_FOR_DESIGN_REVIEW = "ready_for_design_review_only"

VALID_REEB_STATUSES: frozenset[str] = frozenset({
    REEB_STATUS_UNAVAILABLE, REEB_STATUS_NOT_COLLECTED, REEB_STATUS_INCOMPLETE,
    REEB_STATUS_COLLECTED, REEB_STATUS_INVALID,
    REEB_STATUS_BLOCKED_BY_NO_GO, REEB_STATUS_BLOCKED_BY_MISSING,
    REEB_STATUS_BLOCKED_BY_VERIFICATION, REEB_STATUS_READY_FOR_DESIGN_REVIEW,
})

REEB_DECISION_DENIED = "denied"
REEB_DECISION_FAIL_CLOSED = "fail_closed"
REEB_DECISION_BLOCKED = "blocked"
REEB_DECISION_EVIDENCE_ONLY = "evidence_only"
REEB_DECISION_DESIGN_REVIEW = "design_review_only"

VALID_REEB_DECISIONS: frozenset[str] = frozenset({
    REEB_DECISION_DENIED, REEB_DECISION_FAIL_CLOSED, REEB_DECISION_BLOCKED,
    REEB_DECISION_EVIDENCE_ONLY, REEB_DECISION_DESIGN_REVIEW,
})


@dataclass
class RuntimeEnforcementEvidenceBundle:
    """Design-only model for a future runtime enforcement evidence bundle.

    Non-executing, non-authorizing, evidence-only. Collects references, digests,
    and trust statuses from the PCAE evidence stack. Does not enforce.
    """

    schema_version: str = _REEB_SCHEMA_VERSION
    evidence_bundle_id: str = ""
    phase_id: str = "101B"
    task_id: str = ""
    generated_at_utc: str = ""

    bundle_status: str = REEB_STATUS_NOT_COLLECTED
    bundle_decision: str = REEB_DECISION_DENIED

    required_evidence: list[str] = field(default_factory=list)
    missing_required_evidence: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    evidence_digests: list[str] = field(default_factory=list)

    no_go_evidence_ref: str = ""
    no_go_evidence_digest: str = ""
    no_go_conditions: list[str] = field(default_factory=list)
    approval_ref: str = ""
    audit_readiness_ref: str = ""
    rollback_readiness_ref: str = ""
    report_trust_ref: str = ""
    notification_trust_ref: str = ""
    denial_reasons: list[str] = field(default_factory=list)
    fail_closed_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True
    design_only: bool = True

    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _REEB_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.bundle_status not in VALID_REEB_STATUSES:
            issues.append(f"invalid bundle_status: {self.bundle_status!r}")
        if self.bundle_decision not in VALID_REEB_DECISIONS:
            issues.append(f"invalid bundle_decision: {self.bundle_decision!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.design_only:
            issues.append("design_only must be True")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "evidence_bundle_id": self.evidence_bundle_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "bundle_status": self.bundle_status,
            "bundle_decision": self.bundle_decision,
            "required_evidence": sorted(self.required_evidence),
            "missing_required_evidence": sorted(self.missing_required_evidence),
            "evidence_refs": sorted(self.evidence_refs),
            "evidence_digests": sorted(self.evidence_digests),
            "no_go_conditions": sorted(self.no_go_conditions),
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "warnings": sorted(self.warnings),
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_bundle_id": self.evidence_bundle_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "bundle_status": self.bundle_status,
            "bundle_decision": self.bundle_decision,
            "required_evidence": sorted(self.required_evidence),
            "missing_required_evidence": sorted(self.missing_required_evidence),
            "evidence_refs": sorted(self.evidence_refs),
            "evidence_digests": sorted(self.evidence_digests),
            "no_go_evidence_ref": self.no_go_evidence_ref,
            "no_go_evidence_digest": self.no_go_evidence_digest,
            "no_go_conditions": sorted(self.no_go_conditions),
            "approval_ref": self.approval_ref,
            "audit_readiness_ref": self.audit_readiness_ref,
            "rollback_readiness_ref": self.rollback_readiness_ref,
            "report_trust_ref": self.report_trust_ref,
            "notification_trust_ref": self.notification_trust_ref,
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
            "digest": self.digest,
        }


# ═══════════════════════════════════════════════════════════════════════════
# RuntimeEnforcementDecision — design-only, non-executing, non-authorizing
# Phase 102A — Runtime Enforcement Decision Engine Contract Design
# ═══════════════════════════════════════════════════════════════════════════

_RED_SCHEMA_VERSION = "1.0"

RED_STATUS_UNAVAILABLE = "unavailable"
RED_STATUS_NOT_EVALUATED = "not_evaluated"
RED_STATUS_INCOMPLETE = "incomplete"
RED_STATUS_EVALUATED = "evaluated"
RED_STATUS_INVALID = "invalid"
RED_STATUS_BLOCKED = "blocked"
RED_STATUS_DENIED = "denied"
RED_STATUS_FAIL_CLOSED = "fail_closed"
RED_STATUS_DESIGN_REVIEW = "ready_for_design_review_only"

VALID_RED_STATUSES: frozenset[str] = frozenset({
    RED_STATUS_UNAVAILABLE, RED_STATUS_NOT_EVALUATED, RED_STATUS_INCOMPLETE,
    RED_STATUS_EVALUATED, RED_STATUS_INVALID, RED_STATUS_BLOCKED,
    RED_STATUS_DENIED, RED_STATUS_FAIL_CLOSED, RED_STATUS_DESIGN_REVIEW,
})

RED_RESULT_DENIED = "denied"
RED_RESULT_FAIL_CLOSED = "fail_closed"
RED_RESULT_BLOCKED_MISSING_EVIDENCE = "blocked_by_missing_evidence"
RED_RESULT_BLOCKED_VERIFICATION = "blocked_by_failed_verification"
RED_RESULT_BLOCKED_NO_GO = "blocked_by_no_go"
RED_RESULT_BLOCKED_APPROVAL = "blocked_by_missing_approval"
RED_RESULT_BLOCKED_AUDIT = "blocked_by_missing_audit"
RED_RESULT_BLOCKED_ROLLBACK = "blocked_by_missing_rollback"
RED_RESULT_BLOCKED_REPORT_TRUST = "blocked_by_report_trust_failure"
RED_RESULT_BLOCKED_NOTIFICATION_TRUST = "blocked_by_notification_trust_failure"
RED_RESULT_EVIDENCE_ONLY = "evidence_only"
RED_RESULT_DESIGN_REVIEW = "design_review_only"

VALID_RED_RESULTS: frozenset[str] = frozenset({
    RED_RESULT_DENIED, RED_RESULT_FAIL_CLOSED,
    RED_RESULT_BLOCKED_MISSING_EVIDENCE, RED_RESULT_BLOCKED_VERIFICATION,
    RED_RESULT_BLOCKED_NO_GO, RED_RESULT_BLOCKED_APPROVAL,
    RED_RESULT_BLOCKED_AUDIT, RED_RESULT_BLOCKED_ROLLBACK,
    RED_RESULT_BLOCKED_REPORT_TRUST, RED_RESULT_BLOCKED_NOTIFICATION_TRUST,
    RED_RESULT_EVIDENCE_ONLY, RED_RESULT_DESIGN_REVIEW,
})


@dataclass
class RuntimeEnforcementDecision:
    """Design-only model for a future runtime enforcement decision.

    Non-executing, non-authorizing, evidence-only. Evaluates an evidence bundle
    and produces a decision artifact. Does not enforce.
    """

    schema_version: str = _RED_SCHEMA_VERSION
    decision_engine_id: str = ""
    phase_id: str = "102A"
    task_id: str = ""
    generated_at_utc: str = ""

    source_bundle_ref: str = ""
    source_bundle_digest: str = ""
    decision_status: str = RED_STATUS_NOT_EVALUATED
    decision_result: str = RED_RESULT_DENIED
    decision_reason: str = ""

    evaluated_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    stale_inputs: list[str] = field(default_factory=list)
    tampered_inputs: list[str] = field(default_factory=list)
    contradictory_inputs: list[str] = field(default_factory=list)
    triggered_no_go_conditions: list[str] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)
    fail_closed_reasons: list[str] = field(default_factory=list)
    future_only_decisions: list[str] = field(default_factory=list)
    unsupported_requests: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    execution_available: bool = False
    execution_authorized: bool = False
    backend_invocation_authorized: bool = False
    adapter_execution_authorized: bool = False
    network_authorized: bool = False
    subprocess_authorized: bool = False
    shell_authorized: bool = False
    mutation_authorized: bool = False
    apply_authorized: bool = False
    rollback_authorized: bool = False
    commit_authorized: bool = False
    push_authorized: bool = False

    simulation_only: bool = True
    no_execution: bool = True
    evidence_only: bool = True
    non_authorizing: bool = True
    design_only: bool = True

    digest: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema_version != _RED_SCHEMA_VERSION:
            issues.append(f"unknown schema_version: {self.schema_version!r}")
        if self.decision_status not in VALID_RED_STATUSES:
            issues.append(f"invalid decision_status: {self.decision_status!r}")
        if self.decision_result not in VALID_RED_RESULTS:
            issues.append(f"invalid decision_result: {self.decision_result!r}")
        if self.execution_available:
            issues.append("execution_available must be False")
        if self.execution_authorized:
            issues.append("execution_authorized must be False")
        if self.push_authorized:
            issues.append("push_authorized must be False")
        if not self.simulation_only:
            issues.append("simulation_only must be True")
        if not self.no_execution:
            issues.append("no_execution must be True")
        if not self.design_only:
            issues.append("design_only must be True")
        return issues

    def compute_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "decision_engine_id": self.decision_engine_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_bundle_ref": self.source_bundle_ref,
            "source_bundle_digest": self.source_bundle_digest,
            "decision_status": self.decision_status,
            "decision_result": self.decision_result,
            "decision_reason": self.decision_reason,
            "evaluated_inputs": sorted(self.evaluated_inputs),
            "missing_inputs": sorted(self.missing_inputs),
            "stale_inputs": sorted(self.stale_inputs),
            "tampered_inputs": sorted(self.tampered_inputs),
            "contradictory_inputs": sorted(self.contradictory_inputs),
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "future_only_decisions": sorted(self.future_only_decisions),
            "unsupported_requests": sorted(self.unsupported_requests),
            "warnings": sorted(self.warnings),
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
        }
        canonical = _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_engine_id": self.decision_engine_id,
            "phase_id": self.phase_id, "task_id": self.task_id,
            "generated_at_utc": self.generated_at_utc,
            "source_bundle_ref": self.source_bundle_ref,
            "source_bundle_digest": self.source_bundle_digest,
            "decision_status": self.decision_status,
            "decision_result": self.decision_result,
            "decision_reason": self.decision_reason,
            "evaluated_inputs": sorted(self.evaluated_inputs),
            "missing_inputs": sorted(self.missing_inputs),
            "stale_inputs": sorted(self.stale_inputs),
            "tampered_inputs": sorted(self.tampered_inputs),
            "contradictory_inputs": sorted(self.contradictory_inputs),
            "triggered_no_go_conditions": sorted(self.triggered_no_go_conditions),
            "denial_reasons": sorted(self.denial_reasons),
            "fail_closed_reasons": sorted(self.fail_closed_reasons),
            "future_only_decisions": sorted(self.future_only_decisions),
            "unsupported_requests": sorted(self.unsupported_requests),
            "warnings": sorted(self.warnings),
            "authorization_summary": {
                "execution_available": self.execution_available,
                "execution_authorized": self.execution_authorized,
                "backend_invocation_authorized": self.backend_invocation_authorized,
                "adapter_execution_authorized": self.adapter_execution_authorized,
                "network_authorized": self.network_authorized,
                "subprocess_authorized": self.subprocess_authorized,
                "shell_authorized": self.shell_authorized,
                "mutation_authorized": self.mutation_authorized,
                "apply_authorized": self.apply_authorized,
                "rollback_authorized": self.rollback_authorized,
                "commit_authorized": self.commit_authorized,
                "push_authorized": self.push_authorized,
            },
            "simulation_only": self.simulation_only,
            "no_execution": self.no_execution,
            "evidence_only": self.evidence_only,
            "non_authorizing": self.non_authorizing,
            "design_only": self.design_only,
            "digest": self.digest,
        }
