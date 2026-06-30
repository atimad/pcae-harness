"""Deterministic evidence-chain fixtures for artifact-only invocation dry-run tests.

Phase 95M — Fixture builders that produce complete and broken evidence chains
without real backend execution. All paths use explicit test-safe values.
No subprocess, no network, no live inspection.
"""

from __future__ import annotations

from pcae.core.backend_invocations import (
    ArtifactOnlyInvocationCommandBoundary,
    ArtifactOnlyInvocationCommandBoundaryAssessment,
    validate_artifact_only_invocation_command_boundary,
    COMMAND_MODE_PLAN,
    COMMAND_MODE_DRY_RUN,
    COMMAND_MODE_EXECUTE_RESERVED,
    DECISION_ALLOW_DRY_RUN,
    DECISION_DENY,
    DECISION_HARD_BLOCK,
    DECISION_MISSING_EVIDENCE,
)

# ── Canonical fixture IDs ──────────────────────────────────────────────────

FIXTURE_PHASE_ID = "95M"
FIXTURE_TASK_ID = "artifact-only-fixture-chain"
FIXTURE_BACKEND_ID = "mock"
FIXTURE_ADAPTER_ID = "mock"
FIXTURE_BOUNDARY_ID = "cb-fixture-valid"

# ── Canonical valid fixture chain ───────────────────────────────────────────


def build_valid_boundary(**overrides) -> ArtifactOnlyInvocationCommandBoundary:
    """Build a canonical valid command boundary for artifact-only dry-run.

    All artifacts are internally consistent: same backend, same adapter,
    matching digests across the chain.  No execution flags are enabled.
    """
    kwargs = {
        "boundary_id": FIXTURE_BOUNDARY_ID,
        "phase_id": FIXTURE_PHASE_ID,
        "task_id": FIXTURE_TASK_ID,
        "backend_id": FIXTURE_BACKEND_ID,
        "adapter_id": FIXTURE_ADAPTER_ID,
        "prompt_artifact_path": "/fixture/prompt.md",
        "prompt_artifact_digest": "sha256:aaa111",
        "preflight_artifact_path": "/fixture/preflight.json",
        "preflight_artifact_digest": "sha256:bbb222",
        "runtime_evidence_path": "/fixture/runtime.json",
        "runtime_evidence_digest": "sha256:ccc333",
        "approval_artifact_path": "/fixture/approval.json",
        "approval_artifact_digest": "sha256:ddd444",
        "invocation_plan_path": "/fixture/plan.json",
        "invocation_plan_digest": "sha256:eee555",
        "broker_decision_id": "bd-fixture",
        "broker_decision": DECISION_ALLOW_DRY_RUN,
        "shell_gate_decision_id": "sg-fixture",
        "shell_gate_decision": DECISION_ALLOW_DRY_RUN,
        "output_quarantine_path": "/fixture/quarantine",
        "audit_path": "/fixture/audit",
        "timeout_seconds": 120,
        "redaction_policy_id": "rp-fixture",
        "operator_approval_reference": "approval-fixture-001",
        "command_mode": COMMAND_MODE_DRY_RUN,
    }
    kwargs.update(overrides)
    b = ArtifactOnlyInvocationCommandBoundary(**kwargs)
    b.record_digest = b.compute_digest()
    return b


# ── Broken fixture variants ─────────────────────────────────────────────────


def build_missing_prompt() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(prompt_artifact_path="", prompt_artifact_digest="")


def build_tampered_prompt_digest() -> ArtifactOnlyInvocationCommandBoundary:
    # Empty digest triggers hard-block (cross-artifact binding is a
    # future concern; model checks only presence, not cross-referencing)
    return build_valid_boundary(prompt_artifact_digest="")


def build_backend_mismatch() -> ArtifactOnlyInvocationCommandBoundary:
    # Empty backend triggers hard-block (not cross-artifact mismatch
    # which requires loading actual artifacts)
    return build_valid_boundary(backend_id="")


def build_adapter_mismatch() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(adapter_id="")


def build_runtime_evidence_digest_mismatch() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(runtime_evidence_digest="")


def build_approval_ineffective() -> ArtifactOnlyInvocationCommandBoundary:
    # Approval is missing (empty path and digest)
    return build_valid_boundary(approval_artifact_path="", approval_artifact_digest="")


def build_invocation_plan_tampered() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(invocation_plan_digest="")


def build_broker_deny() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(broker_decision=DECISION_DENY)


def build_broker_hard_block() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(broker_decision=DECISION_HARD_BLOCK)


def build_shell_gate_deny() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(shell_gate_decision=DECISION_DENY)


def build_shell_gate_hard_block() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(shell_gate_decision=DECISION_HARD_BLOCK)


def build_missing_quarantine() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(output_quarantine_path="")


def build_missing_audit() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(audit_path="")


def build_missing_timeout() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(timeout_seconds=0)


def build_execute_reserved() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(command_mode=COMMAND_MODE_EXECUTE_RESERVED)


def build_execute_requested() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(execute_requested=True)


def build_no_subprocess_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_subprocess=False)


def build_no_network_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_network=False)


def build_no_repo_mutation_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_repo_mutation=False)


def build_no_apply_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_apply=False)


def build_no_patch_parsing_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_patch_parsing=False)


def build_no_commit_push_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_commit_push_authorization=False)


def build_no_telegram_inbound_false() -> ArtifactOnlyInvocationCommandBoundary:
    return build_valid_boundary(no_telegram_inbound=False)


# ── Broken fixture registry ─────────────────────────────────────────────────

BROKEN_FIXTURES: dict[str, tuple[callable, str]] = {
    "missing_prompt": (build_missing_prompt, "prompt_artifact_path_missing"),
    "tampered_prompt_digest": (build_tampered_prompt_digest, "prompt_artifact_digest_missing"),
    "backend_mismatch": (build_backend_mismatch, "backend_id_missing"),
    "adapter_mismatch": (build_adapter_mismatch, "adapter_id_missing"),
    "runtime_evidence_digest_mismatch": (build_runtime_evidence_digest_mismatch, "runtime_evidence_digest_missing"),
    "approval_ineffective": (build_approval_ineffective, "approval_artifact_path_missing"),
    "invocation_plan_tampered": (build_invocation_plan_tampered, "invocation_plan_digest_missing"),
    "broker_deny": (build_broker_deny, "broker_decision:deny"),
    "broker_hard_block": (build_broker_hard_block, "broker_decision:hard_block"),
    "shell_gate_deny": (build_shell_gate_deny, "shell_gate_decision:deny"),
    "shell_gate_hard_block": (build_shell_gate_hard_block, "shell_gate_decision:hard_block"),
    "missing_quarantine": (build_missing_quarantine, "output_quarantine_path_missing"),
    "missing_audit": (build_missing_audit, "audit_path_missing"),
    "missing_timeout": (build_missing_timeout, "timeout_missing_or_invalid"),
    "execute_reserved": (build_execute_reserved, "execute_reserved_not_supported"),
    "execute_requested": (build_execute_requested, "execute_requested=True"),
    "no_subprocess_false": (build_no_subprocess_false, "no_subprocess=False"),
    "no_network_false": (build_no_network_false, "no_network=False"),
    "no_repo_mutation_false": (build_no_repo_mutation_false, "no_repo_mutation=False"),
    "no_apply_false": (build_no_apply_false, "no_apply=False"),
    "no_patch_parsing_false": (build_no_patch_parsing_false, "no_patch_parsing=False"),
    "no_commit_push_false": (build_no_commit_push_false, "no_commit_push_authorization=False"),
    "no_telegram_inbound_false": (build_no_telegram_inbound_false, "no_telegram_inbound=False"),
}
