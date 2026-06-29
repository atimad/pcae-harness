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
    req = InvocationRequest(
        request_id=f"be-{uuid.uuid4().hex[:12]}",
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
