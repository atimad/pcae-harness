"""
Shared builders for Phase 149O.20L.7O.3W test files (not itself a test
module -- no `test_` prefix, never collected by pytest).

Centralizes the trusted-fixture construction used across
`test_runtime_authority_model.py`, `test_runtime_authority_validation.py`,
`test_runtime_invocation_approval_store.py`,
`test_runtime_dispatch_permission.py`,
`test_runtime_dispatch_attempt_idempotency.py`,
`test_runtime_dispatch_no_external_effect.py`,
`test_runtime_dispatch_regression_dry_path.py`, and
`test_runtime_dispatch_regression_pb_actions.py`, so every test file
starts from the same known-good baseline and diverges explicitly.
"""

from __future__ import annotations

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core.runtime_invocation import new_invocation_id

REPO_A = "a" * 64
REPO_B = "b1" * 32
TASK_A = "task-a"
TASK_B = "task-b"
TARGET_A = "local-cli-fixture-1"
TARGET_B = "local-cli-fixture-2"
PHASE_ID = "149O.20L.7O.3W"
FS_SCOPE_DIGEST = "b" * 64
PROC_PROFILE_DIGEST = "c" * 64
ADAPTER_ID = "fixture-adapter"
DESCRIPTOR_VERSION = "1.0"
DESCRIPTOR_DIGEST = "d" * 64
TARGET_CONFIG_DIGEST = "e" * 64
HEAD_COMMIT_A = "f" * 40
HEAD_COMMIT_B = "1" * 40
TASK_CONTRACT_DIGEST_A = "2" * 64
TASK_CONTRACT_DIGEST_B = "3" * 64
POLICY_VERSION_A = "pv-1"
POLICY_VERSION_B = "pv-2"
CREATED_AT = "2026-08-27T00:00:00Z"
EXPIRES_AT = "2026-08-27T01:00:00Z"
NOW_FRESH = "2026-08-27T00:30:00Z"
NOW_EXPIRED = "2026-08-27T02:00:00Z"


def prompt_hash(text: str = "Do the thing.") -> str:
    return ra.compute_prompt_semantic_hash(
        [
            ra.PromptSemanticComponent(kind="system", content="You are PCAE."),
            ra.PromptSemanticComponent(kind="task", content=text),
        ]
    )


def build_approval(
    *,
    invocation_id: str | None = None,
    runtime_target_id: str = TARGET_A,
    prompt: str = "Do the thing.",
    repository_identity: str = REPO_A,
    task_id: str = TASK_A,
    phase_id: str = PHASE_ID,
    session_id: str | None = None,
    head_commit: str = HEAD_COMMIT_A,
    task_contract_digest: str = TASK_CONTRACT_DIGEST_A,
    policy_version: str = POLICY_VERSION_A,
    created_at: str = CREATED_AT,
    expires_at: str = EXPIRES_AT,
    approver_id: str = "atila-madai",
) -> ra.RuntimeInvocationApproval:
    subject = ra.ApprovalSubject(
        invocation_id=invocation_id or new_invocation_id(),
        runtime_target_id=runtime_target_id,
        prompt_hash=prompt_hash(prompt),
        repository_identity=repository_identity,
        task_id=task_id,
    )
    gov = ra.GovernanceContext(phase_id=phase_id, session_id=session_id)
    scope = ra.ApprovalScope(
        requested_capability="local_cli_dispatch",
        filesystem_scope_ref=ra.ArtifactRef(artifact_id="fs-scope-1", artifact_digest=FS_SCOPE_DIGEST),
        process_profile_ref=ra.ArtifactRef(
            artifact_id="proc-profile-1", artifact_digest=PROC_PROFILE_DIGEST
        ),
    )
    adapter = ra.AdapterBinding(
        adapter_id=ADAPTER_ID,
        descriptor_version=DESCRIPTOR_VERSION,
        descriptor_digest=DESCRIPTOR_DIGEST,
        target_config_digest=TARGET_CONFIG_DIGEST,
    )
    freshness = ra.FreshnessSnapshot(
        head_commit=head_commit,
        task_contract_digest=task_contract_digest,
        policy_version=policy_version,
    )
    return ra.create_runtime_invocation_approval(
        subject=subject,
        governance_context=gov,
        approval_scope=scope,
        adapter_binding=adapter,
        freshness_snapshot=freshness,
        approver_id=approver_id,
        identity_evidence_kind=ra.IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY,
        created_at=created_at,
        expires_at=expires_at,
    )


def matching_context(
    approval: ra.RuntimeInvocationApproval,
    *,
    current_time: str = NOW_FRESH,
    requested_capability: str = "local_cli_dispatch",
) -> ra.InvocationRequestContext:
    """Build an `InvocationRequestContext` that exactly matches `approval`'s
    subject/scope/freshness -- the caller then mutates individual fields to
    construct adversarial mismatch cases."""
    return ra.InvocationRequestContext(
        invocation_id=approval.subject.invocation_id,
        runtime_target_id=approval.subject.runtime_target_id,
        prompt_hash=approval.subject.prompt_hash,
        repository_identity=approval.subject.repository_identity,
        task_id=approval.subject.task_id,
        phase_id=approval.governance_context.phase_id,
        session_id=approval.governance_context.session_id,
        requested_capability=requested_capability,
        adapter_id=approval.adapter_binding.adapter_id,
        descriptor_version=approval.adapter_binding.descriptor_version,
        descriptor_digest=approval.adapter_binding.descriptor_digest,
        target_config_digest=approval.adapter_binding.target_config_digest,
        head_commit=approval.freshness_snapshot.head_commit,
        task_contract_digest=approval.freshness_snapshot.task_contract_digest,
        task_state=approval.freshness_snapshot.task_state,
        policy_version=approval.freshness_snapshot.policy_version,
        current_time=current_time,
    )


def always_unconsumed(_approval_id: str) -> str:
    return ra.CONSUMPTION_STATE_NONE


def dispatch_inputs(
    *,
    repository_identity: str = REPO_A,
    task_id: str = TASK_A,
    phase_id: str = PHASE_ID,
    session_id: str | None = None,
    runtime_target_id: str = TARGET_A,
    prompt: str = "Do the thing.",
    requested_capability: str = "local_cli_dispatch",
) -> rdp.RuntimeDispatchRequestConstructionInput:
    return rdp.RuntimeDispatchRequestConstructionInput(
        repository_identity=repository_identity,
        task_id=task_id,
        lifecycle_context=pbf.RuntimeDispatchLifecycleContext(
            phase_id=phase_id, session_id=session_id
        ),
        runtime_target_id=runtime_target_id,
        adapter_descriptor_binding=pbf.RuntimeDispatchAdapterDescriptorBinding(
            adapter_id=ADAPTER_ID,
            descriptor_version=DESCRIPTOR_VERSION,
            descriptor_digest=DESCRIPTOR_DIGEST,
            target_config_digest=TARGET_CONFIG_DIGEST,
        ),
        prompt_hash=prompt_hash(prompt),
        requested_capability=requested_capability,
        filesystem_scope_ref=pbf.RuntimeDispatchFilesystemScopeRef(
            scope_id="fs-scope-1", scope_digest=FS_SCOPE_DIGEST
        ),
    )


def full_chain(
    *, simulation_only: bool = True, tracker: rdp.RuntimeDispatchIdentityTracker | None = None
):
    """End-to-end: approval -> validation -> PB request -> decision, all
    matching. Returns (approval, projection, request, decision)."""
    approval = build_approval()
    ctx = matching_context(approval)
    projection, reasons = ra.validate_approval(
        approval, context=ctx, consumption_lookup=always_unconsumed
    )
    assert projection is not None and reasons == ()
    inputs = dispatch_inputs()
    identity = rdp.new_runtime_dispatch_identity(inputs, invocation_id=approval.subject.invocation_id)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=inputs,
        validated_authority=projection,
        simulation_only=simulation_only,
        identity_tracker=tracker,
    )
    broker = pbf.PermissionBroker()
    decision = broker.evaluate(request)
    return approval, projection, request, decision
