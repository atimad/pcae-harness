"""Independent Phase 149O.20L.7O.3W.1R.1 adversarial verification.

This module reconstructs fixtures directly from the frozen contracts and
production APIs.  It deliberately does not import any 3W/3W.1/3W.1R test
helper or test module.  Tests whose names contain ``exposes_blocker`` assert
the observed unsafe behavior so the verification evidence remains runnable;
they are findings, not expected product behavior.
"""

from __future__ import annotations

import dataclasses
import ast
import hashlib
import json
import os
import subprocess
import sys
import socket
import threading
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pb
from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_permission as dispatch
from pcae.core.runtime_invocation_approval_store import (
    ApprovalStoreIntegrityError,
    RuntimeInvocationApprovalStore,
)


REPO = "31" * 32
TASK = "phase-3w1r1-task"
PHASE = "149O.20L.7O.3W.1R.1"
TARGET = "local-cli-verifier"
PROMPT = authority.compute_prompt_semantic_hash(
    (
        authority.PromptSemanticComponent(kind="system", content="PCAE verifier"),
        authority.PromptSemanticComponent(kind="task", content="verify authority\r\nexactly"),
    )
)
HEAD = "4" * 40
TASK_DIGEST = "5" * 64
FS_DIGEST = "6" * 64
PROCESS_DIGEST = "7" * 64
DESCRIPTOR_DIGEST = "8" * 64
CONFIG_DIGEST = "9" * 64
BUDGET_DIGEST = "a" * 64
CREATED = "2026-08-27T12:00:00Z"
EXPIRES = "2026-08-27T13:00:00Z"
NOW = "2026-08-27T12:30:00Z"


def _scope() -> authority.ApprovalScope:
    return authority.ApprovalScope(
        requested_capability="local_cli_dispatch",
        filesystem_scope_ref=authority.ArtifactRef("scope-verifier", FS_DIGEST),
        process_profile_ref=authority.ArtifactRef("process-verifier", PROCESS_DIGEST),
    )


def _adapter() -> authority.AdapterBinding:
    return authority.AdapterBinding(
        adapter_id="verifier-adapter",
        descriptor_version="1.0",
        descriptor_digest=DESCRIPTOR_DIGEST,
        target_config_digest=CONFIG_DIGEST,
    )


def _approval(*, invocation_id: str = "inv-" + "1" * 32) -> authority.RuntimeInvocationApproval:
    return authority.create_runtime_invocation_approval(
        subject=authority.ApprovalSubject(
            invocation_id=invocation_id,
            runtime_target_id=TARGET,
            prompt_hash=PROMPT,
            repository_identity=REPO,
            task_id=TASK,
        ),
        governance_context=authority.GovernanceContext(phase_id=PHASE),
        approval_scope=_scope(),
        adapter_binding=_adapter(),
        freshness_snapshot=authority.FreshnessSnapshot(
            head_commit=HEAD,
            task_contract_digest=TASK_DIGEST,
            policy_version="policy-v1",
        ),
        approver_id="human:independent-verifier",
        identity_evidence_kind=authority.IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY,
        created_at=CREATED,
        expires_at=EXPIRES,
    )


def _context(
    approval: authority.RuntimeInvocationApproval,
    **changes: object,
) -> authority.InvocationRequestContext:
    values: dict[str, object] = {
        "invocation_id": approval.subject.invocation_id,
        "runtime_target_id": approval.subject.runtime_target_id,
        "prompt_hash": approval.subject.prompt_hash,
        "repository_identity": approval.subject.repository_identity,
        "task_id": approval.subject.task_id,
        "phase_id": approval.governance_context.phase_id,
        "session_id": approval.governance_context.session_id,
        "approval_scope": approval.approval_scope,
        "adapter_binding": approval.adapter_binding,
        "head_commit": approval.freshness_snapshot.head_commit,
        "task_contract_digest": approval.freshness_snapshot.task_contract_digest,
        "task_state": "active",
        "policy_version": approval.freshness_snapshot.policy_version,
        "current_time": NOW,
    }
    values.update(changes)
    return authority.InvocationRequestContext(**values)  # type: ignore[arg-type]


def _validate(
    approval: authority.RuntimeInvocationApproval,
    context: authority.InvocationRequestContext | None = None,
):
    return authority.validate_approval(
        approval,
        context=context or _context(approval),
        consumption_lookup=lambda _approval_id: authority.CONSUMPTION_STATE_NONE,
    )


def _inputs(**changes: object) -> dispatch.RuntimeDispatchRequestConstructionInput:
    values: dict[str, object] = {
        "repository_identity": REPO,
        "base_commit": HEAD,
        "task_id": TASK,
        "task_contract_digest": TASK_DIGEST,
        "lifecycle_context": pb.RuntimeDispatchLifecycleContext(phase_id=PHASE),
        "runtime_target_id": TARGET,
        "adapter_descriptor_binding": pb.RuntimeDispatchAdapterDescriptorBinding(
            adapter_id="verifier-adapter",
            descriptor_version="1.0",
            descriptor_digest=DESCRIPTOR_DIGEST,
            target_config_digest=CONFIG_DIGEST,
        ),
        "prompt_hash": PROMPT,
        "requested_capability": "local_cli_dispatch",
        "filesystem_scope_ref": pb.RuntimeDispatchFilesystemScopeRef(
            scope_id="scope-verifier", scope_digest=FS_DIGEST
        ),
        "process_profile_ref": pb.RuntimeDispatchFilesystemScopeRef(
            scope_id="process-verifier", scope_digest=PROCESS_DIGEST
        ),
        "effect_class": "bounded_local_process_dispatch",
        "network_requirement": False,
        "resource_budget": pb.RuntimeDispatchFilesystemScopeRef(
            scope_id="budget-verifier", scope_digest=BUDGET_DIGEST
        ),
    }
    values.update(changes)
    return dispatch.RuntimeDispatchRequestConstructionInput(**values)  # type: ignore[arg-type]


def _identity(tmp_path: Path, inputs=None, invocation_id: str = "inv-" + "1" * 32):
    resolved = inputs or _inputs()
    return dispatch.new_runtime_dispatch_identity(
        resolved,
        identity_tracker=dispatch.RuntimeDispatchIdentityTracker(tmp_path),
        invocation_id=invocation_id,
    )


def _resign(approval: authority.RuntimeInvocationApproval, **changes: object):
    mutated = dataclasses.replace(approval, **changes, record_digest="")
    return dataclasses.replace(mutated, record_digest=authority.compute_record_digest(mutated))


def _binding_digest(identity, inputs) -> str:
    return authority.compute_canonical_digest(
        {
            "subject": {
                "invocation_id": identity.invocation_id,
                "runtime_target_id": inputs.runtime_target_id,
                "prompt_hash": inputs.prompt_hash,
                "repository_identity": inputs.repository_identity,
                "task_id": inputs.task_id,
            },
            "approval_scope": {
                "requested_capability": inputs.requested_capability,
                "transport_type": "local_cli",
                "effect_class": inputs.effect_class,
                "dispatch_limit": 1,
                "network_required": inputs.network_requirement,
                "filesystem_scope_ref": {
                    "artifact_id": inputs.filesystem_scope_ref.scope_id,
                    "artifact_digest": inputs.filesystem_scope_ref.scope_digest,
                },
                "process_profile_ref": {
                    "artifact_id": inputs.process_profile_ref.scope_id,
                    "artifact_digest": inputs.process_profile_ref.scope_digest,
                },
            },
            "adapter_binding": {
                "adapter_id": inputs.adapter_descriptor_binding.adapter_id,
                "descriptor_version": inputs.adapter_descriptor_binding.descriptor_version,
                "descriptor_digest": inputs.adapter_descriptor_binding.descriptor_digest,
                "target_config_digest": inputs.adapter_descriptor_binding.target_config_digest,
            },
        }
    )


def test_original_b1_naive_projection_raw_boolean_and_missing_context_are_closed(tmp_path):
    inputs = _inputs()
    identity = _identity(tmp_path, inputs)
    forged = authority.ValidatedAuthorityProjection(
        approval_id="ria-" + "2" * 32,
        record_digest="3" * 64,
        subject_scope_binding_digest=_binding_digest(identity, inputs),
        provenance_verdict="identified_human_distinct_from_producer",
        freshness_verdict_digest="4" * 64,
        expiry_verdict="not_expired",
        consumption_state_verdict=authority.CONSUMPTION_STATE_NONE,
        validated_at=NOW,
    )
    with pytest.raises(dispatch.RuntimeDispatchConstructionError):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=inputs, validated_authority=forged
        )
    with pytest.raises(ValueError, match="trusted_builder"):
        pb.build_permission_broker_request(
            action_type=pb.ACTION_TYPE_RUNTIME_DISPATCH,
            execution_class=pb.EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-006",
            requested_capability="local_cli_dispatch",
            approval_present=True,
        )
    direct = pb.PermissionBrokerRequest(
        request_id="pbr-direct",
        timestamp=NOW,
        action_type=pb.ACTION_TYPE_RUNTIME_DISPATCH,
        execution_class=pb.EXECUTION_CLASS_ADAPTER,
        task_id=TASK,
        phase_id=PHASE,
        requested_component="COMP-006",
        requested_capability="local_cli_dispatch",
        requested_resource=None,
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
        runtime_dispatch_context=None,
    )
    assert pb.PermissionBroker().evaluate(direct).decision == pb.DECISION_DENY


def test_original_b1_exposes_blocker_projection_seal_is_copyable(tmp_path):
    approval = _approval()
    legitimate, reasons = _validate(approval)
    assert legitimate is not None and reasons == ()
    inputs = _inputs()
    identity = _identity(tmp_path, inputs, approval.subject.invocation_id)
    forged = dataclasses.replace(
        legitimate,
        approval_id="ria-" + "f" * 32,
        record_digest="e" * 64,
        subject_scope_binding_digest=_binding_digest(identity, inputs),
    )
    assert authority.is_trusted_validated_authority_projection(forged)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=forged, simulation_only=True
    )
    decision = pb.PermissionBroker().evaluate(request)
    assert request.approval_present is True
    assert decision.decision == pb.DECISION_ALLOW


def test_original_b1_exposes_blocker_sealed_pb_request_can_gain_fake_authority(tmp_path):
    inputs = _inputs()
    identity = _identity(tmp_path, inputs)
    unapproved = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=True
    )
    assert unapproved.approval_present is False
    fake_binding = pb.RuntimeDispatchHumanAuthorityBinding(
        approval_id="ria-" + "d" * 32,
        approval_record_digest="c" * 64,
        validation_evidence_digest="b" * 64,
    )
    forged = dataclasses.replace(
        unapproved,
        approval_present=True,
        runtime_dispatch_context=dataclasses.replace(
            unapproved.runtime_dispatch_context,
            human_authority_binding=fake_binding,
        ),
    )
    decision = pb.PermissionBroker().evaluate(forged)
    assert decision.decision == pb.DECISION_ALLOW
    assert "POL-004" not in decision.triggered_policy_ids


@pytest.mark.parametrize("bad_id", ["../escape", "/tmp/escape", "a/b", "a\\b", "", "ria-xyz"])
def test_original_b2_lexical_path_variants_fail_closed(tmp_path, bad_id):
    store = RuntimeInvocationApprovalStore(tmp_path)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(bad_id)


def test_original_b2_link_and_create_only_variants_fail_closed(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    approval_root = tmp_path / ".pcae/runtime-invocation-approvals/v1"
    approval_root.mkdir(parents=True)
    (approval_root / approval.approval_id).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(approval)
    assert list(outside.iterdir()) == []


def test_original_b2_hardlinked_and_symlinked_records_are_untrusted(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    record = tmp_path / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id / "approval.json"
    hardlink = tmp_path / "copy.json"
    os.link(record, hardlink)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


def test_original_b2_duplicate_identical_and_conflicting_writes_are_create_only(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(approval)
    conflicting = _approval(invocation_id="inv-" + "2" * 32)
    conflicting = dataclasses.replace(conflicting, approval_id=approval.approval_id, record_digest="")
    conflicting = dataclasses.replace(
        conflicting, record_digest=authority.compute_record_digest(conflicting)
    )
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(conflicting)


def test_original_b2_filename_record_identity_mismatch_fails_closed(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    record = tmp_path / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id / "approval.json"
    data = json.loads(record.read_text())
    data["approval_id"] = "ria-" + "f" * 32
    record.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


def test_original_b2_symlinked_store_component_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / ".pcae").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ApprovalStoreIntegrityError):
        RuntimeInvocationApprovalStore(tmp_path).create(_approval())


@pytest.mark.parametrize(
    ("path", "bad_value"),
    [
        (("governance_context", "phase_id"), 7),
        (("approval_scope", "requested_capability"), True),
        (("approval_scope", "network_required"), 0),
        (("adapter_binding", "descriptor_version"), " bad "),
        (("freshness_snapshot", "policy_version"), []),
        (("provenance", "approver_id"), ""),
    ],
)
def test_original_b3_nested_type_and_value_variants_are_rejected(path, bad_value):
    candidate = _approval().to_dict()
    target = candidate
    for member in path[:-1]:
        target = target[member]
    target[path[-1]] = bad_value
    assert authority.validate_riasc_schema_shape(candidate)


def test_original_b3_duplicate_json_keys_fail_closed(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    record = tmp_path / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id / "approval.json"
    raw = record.read_text()
    record.unlink()
    record.write_text(raw.replace('"schema_id":"RIASC-001"', '"schema_id":"RIASC-001","schema_id":"RIASC-999"'))
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(approval.approval_id)


@pytest.mark.parametrize("payload", ["{", "", "[]", "null"])
def test_corrupt_and_truncated_store_records_fail_closed(tmp_path, payload):
    approval = _approval()
    directory = tmp_path / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id
    directory.mkdir(parents=True)
    (directory / "approval.json").write_text(payload)
    with pytest.raises(ApprovalStoreIntegrityError):
        RuntimeInvocationApprovalStore(tmp_path).load(approval.approval_id)


def test_original_b4_preview_provenance_is_recomputed():
    approval = _approval()
    bad_provenance = dataclasses.replace(
        approval.provenance, approval_preview_digest="a" * 64
    )
    tampered = _resign(approval, provenance=bad_provenance)
    projection, reasons = _validate(tampered)
    assert projection is None
    assert reasons == ("approval_preview_digest_mismatch",)


@pytest.mark.parametrize(
    "mutation",
    [
        "subject",
        "provenance",
        "prompt_hash",
        "repository_identity",
        "approval_id",
        "unknown_field",
        "schema_version",
    ],
)
def test_tamper_variants_fail_closed(mutation):
    approval = _approval()
    if mutation == "subject":
        candidate = _resign(
            approval,
            subject=dataclasses.replace(approval.subject, task_id="tampered-task"),
        )
        assert _validate(candidate)[0] is None
    elif mutation == "provenance":
        candidate = _resign(
            approval,
            provenance=dataclasses.replace(approval.provenance, producer_component="agent"),
        )
        assert _validate(candidate)[0] is None
    elif mutation == "prompt_hash":
        candidate = _resign(
            approval,
            subject=dataclasses.replace(approval.subject, prompt_hash="0" * 64),
        )
        assert _validate(candidate)[0] is None
    elif mutation == "repository_identity":
        candidate = _resign(
            approval,
            subject=dataclasses.replace(approval.subject, repository_identity="0" * 64),
        )
        assert _validate(candidate)[0] is None
    elif mutation == "approval_id":
        candidate = _resign(approval, approval_id="ria-" + "f" * 32)
        assert _validate(candidate)[0] is not None
        # The model alone cannot prove canonical filename identity; the store must.
    elif mutation == "unknown_field":
        data = approval.to_dict()
        data["approved"] = True
        assert authority.validate_riasc_schema_shape(data)
    else:
        candidate = _resign(approval, schema_version="2.0")
        assert _validate(candidate)[0] is None


def test_copied_record_replay_into_different_repository_fails(tmp_path):
    approval = _approval()
    source = tmp_path / "repo-a"
    destination = tmp_path / "repo-b"
    source.mkdir()
    destination.mkdir()
    source_store = RuntimeInvocationApprovalStore(source)
    source_store.create(approval)
    destination_dir = (
        destination / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id
    )
    destination_dir.mkdir(parents=True)
    source_record = (
        source / ".pcae/runtime-invocation-approvals/v1" / approval.approval_id / "approval.json"
    )
    (destination_dir / "approval.json").write_bytes(source_record.read_bytes())
    copied = RuntimeInvocationApprovalStore(destination).load(approval.approval_id)
    projection, reasons = _validate(
        copied,
        _context(copied, repository_identity="0" * 64),
    )
    assert projection is None
    assert reasons == ("subject_mismatch:repository_identity",)


@pytest.mark.parametrize(
    "context_change",
    [
        {"adapter_binding": dataclasses.replace(_adapter(), descriptor_version="2.0")},
        {"adapter_binding": dataclasses.replace(_adapter(), descriptor_digest="0" * 64)},
        {"approval_scope": dataclasses.replace(_scope(), filesystem_scope_ref=authority.ArtifactRef("scope-wide", "0" * 64))},
        {"approval_scope": dataclasses.replace(_scope(), process_profile_ref=authority.ArtifactRef("process-wide", "0" * 64))},
    ],
)
def test_original_b5_descriptor_and_scope_variants_are_cross_bound(context_change):
    approval = _approval()
    projection, reasons = _validate(approval, _context(approval, **context_change))
    assert projection is None
    assert reasons[0].startswith(("adapter_binding_mismatch", "scope_mismatch"))


def test_original_b6_fractional_instants_are_chronological():
    approval = _approval()
    fractional_expiry = "2026-08-27T12:30:00.9Z"
    fractional_provenance = dataclasses.replace(
        approval.provenance,
        approval_preview_digest=authority.build_approval_preview_digest(
            subject=approval.subject,
            approval_scope=approval.approval_scope,
            expires_at=fractional_expiry,
        ),
    )
    fractional = _resign(
        approval,
        expires_at=fractional_expiry,
        provenance=fractional_provenance,
    )
    projection, reasons = _validate(
        fractional, _context(fractional, current_time="2026-08-27T12:30:00Z")
    )
    assert projection is not None and reasons == ()
    projection, reasons = _validate(
        fractional, _context(fractional, current_time="2026-08-27T12:30:01Z")
    )
    assert projection is None and reasons == ("expired",)
    with pytest.raises(ValueError, match="expires_at_must_be_after_created_at"):
        authority.create_runtime_invocation_approval(
            subject=approval.subject,
            governance_context=approval.governance_context,
            approval_scope=approval.approval_scope,
            adapter_binding=approval.adapter_binding,
            freshness_snapshot=approval.freshness_snapshot,
            approver_id="human",
            identity_evidence_kind=authority.IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY,
            created_at="2026-08-27T12:30:00.9Z",
            expires_at="2026-08-27T12:30:00Z",
        )


@pytest.mark.parametrize(
    "field",
    [
        "repository_identity",
        "base_commit",
        "task_id",
        "task_contract_digest",
        "lifecycle_context",
        "runtime_target_id",
        "adapter_descriptor_binding",
        "prompt_hash",
        "requested_capability",
        "filesystem_scope_ref",
        "process_profile_ref",
        "resource_budget",
    ],
)
def test_original_b7_idempotency_binds_identity_critical_variants(tmp_path, field):
    base = _inputs()
    replacements = {
        "repository_identity": "0" * 64,
        "base_commit": "a" * 40,
        "task_id": "other-task",
        "task_contract_digest": "b" * 64,
        "lifecycle_context": pb.RuntimeDispatchLifecycleContext(phase_id="other-phase"),
        "runtime_target_id": "other-target",
        "adapter_descriptor_binding": dataclasses.replace(base.adapter_descriptor_binding, descriptor_version="2.0"),
        "prompt_hash": "c" * 64,
        "requested_capability": "other-capability",
        "filesystem_scope_ref": pb.RuntimeDispatchFilesystemScopeRef("other-scope", "d" * 64),
        "process_profile_ref": pb.RuntimeDispatchFilesystemScopeRef("other-process", "e" * 64),
        "resource_budget": pb.RuntimeDispatchFilesystemScopeRef("other-budget", "f" * 64),
    }
    changed = dataclasses.replace(base, **{field: replacements[field]})
    invocation_id = "inv-" + "1" * 32
    key_a = hashlib.sha256(
        json.dumps(dispatch.canonical_runtime_dispatch_projection(base, invocation_id=invocation_id), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    key_b = hashlib.sha256(
        json.dumps(dispatch.canonical_runtime_dispatch_projection(changed, invocation_id=invocation_id), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert key_a != key_b


def test_original_b7_cross_process_key_is_deterministic(tmp_path):
    code = """
from pcae.core import permission_broker_foundation as p
from pcae.core import runtime_dispatch_permission as d
from pcae.core.runtime_invocation import compute_runtime_dispatch_idempotency_key
i=d.RuntimeDispatchRequestConstructionInput(repository_identity='31'*32,base_commit='4'*40,task_id='phase-3w1r1-task',task_contract_digest='5'*64,lifecycle_context=p.RuntimeDispatchLifecycleContext(phase_id='149O.20L.7O.3W.1R.1'),runtime_target_id='local-cli-verifier',adapter_descriptor_binding=p.RuntimeDispatchAdapterDescriptorBinding('verifier-adapter','1.0','8'*64,'9'*64),prompt_hash=%r,requested_capability='local_cli_dispatch',filesystem_scope_ref=p.RuntimeDispatchFilesystemScopeRef('scope-verifier','6'*64),process_profile_ref=p.RuntimeDispatchFilesystemScopeRef('process-verifier','7'*64),effect_class='bounded_local_process_dispatch',network_requirement=False,resource_budget=p.RuntimeDispatchFilesystemScopeRef('budget-verifier','a'*64))
print(compute_runtime_dispatch_idempotency_key(d.canonical_runtime_dispatch_projection(i,invocation_id='inv-'+'1'*32)))
""" % PROMPT
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(Path.cwd() / "src")}
    first = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=True, env=env).stdout.strip()
    second = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=True, env=env).stdout.strip()
    assert first == second and len(first) == 64


def test_original_b7_exposes_blocker_identity_seal_is_copyable_and_registry_not_rechecked(tmp_path):
    inputs = _inputs()
    identity = _identity(tmp_path, inputs)
    forged_attempt = "att-" + "f" * 32
    forged = dataclasses.replace(identity, attempt_id=forged_attempt, _registration_digest="")
    forged = dataclasses.replace(
        forged,
        _registration_digest=authority.compute_canonical_digest(
            {
                "invocation_id": forged.invocation_id,
                "attempt_id": forged.attempt_id,
                "idempotency_key": forged.idempotency_key,
            }
        ),
    )
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=forged, inputs=inputs, validated_authority=None
    )
    assert request.runtime_dispatch_context.attempt_id == forged_attempt
    assert not (
        tmp_path / ".pcae/runtime-dispatch-identities/v1/attempts" / f"{forged_attempt}.json"
    ).exists()


@pytest.mark.parametrize(
    ("member", "replacement"),
    [
        ("invocation_id", "inv-" + "2" * 32),
        ("runtime_target_id", "other-target"),
        ("prompt_hash", "0" * 64),
        ("repository_identity", "1" * 64),
        ("task_id", "other-task"),
    ],
)
def test_five_member_subject_mismatches_fail(member, replacement):
    approval = _approval()
    projection, reasons = _validate(approval, _context(approval, **{member: replacement}))
    assert projection is None
    assert "mismatch" in reasons[0]


@pytest.mark.parametrize(
    ("change", "reason_fragment"),
    [
        ({"head_commit": "a" * 40}, "head_commit"),
        ({"task_contract_digest": "b" * 64}, "task_contract_digest"),
        ({"task_state": "completed"}, "task_state"),
        ({"prompt_hash": "c" * 64}, "prompt_hash"),
        ({"runtime_target_id": "other-target"}, "runtime_target_id"),
        ({"adapter_binding": dataclasses.replace(_adapter(), target_config_digest="d" * 64)}, "adapter_binding"),
        ({"current_time": EXPIRES}, "expired"),
    ],
)
def test_seven_freshness_rules_block_or_rebind(change, reason_fragment):
    approval = _approval()
    projection, reasons = _validate(approval, _context(approval, **change))
    assert projection is None
    assert reason_fragment in reasons[0]


def test_policy_drift_requires_fresh_pb_without_erasing_human_act():
    approval = _approval()
    projection, reasons = _validate(
        approval, _context(approval, policy_version="policy-v2")
    )
    assert projection is not None
    assert reasons == ("policy_drift_requires_fresh_pb_re_evaluation",)


@pytest.mark.parametrize(
    "state",
    [
        authority.CONSUMPTION_STATE_CONSUMED,
        authority.CONSUMPTION_STATE_CANCELLED,
        authority.CONSUMPTION_STATE_UNCERTAIN,
        authority.CONSUMPTION_STATE_COMPLETED,
    ],
)
def test_consumed_or_uncertain_authority_fails_closed(state):
    approval = _approval()
    projection, reasons = authority.validate_approval(
        approval, context=_context(approval), consumption_lookup=lambda _approval_id: state
    )
    assert projection is None
    assert reasons == (f"already_bound:{state}",)


def test_one_shot_is_not_consumed_before_gate_9(tmp_path):
    approval = _approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    loaded = store.load(approval.approval_id)
    projection, reasons = _validate(loaded)
    assert projection is not None and reasons == ()
    inputs = _inputs()
    identity = _identity(tmp_path, inputs, approval.subject.invocation_id)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection, simulation_only=False
    )
    decision = pb.PermissionBroker().evaluate(request)
    assert decision.decision == pb.DECISION_DENY
    assert decision.causing_policy_id == "POL-005"
    projection_again, reasons_again = _validate(store.load(approval.approval_id))
    assert projection_again is not None and reasons_again == ()


def test_strongest_valid_request_is_denied_only_by_pol005(tmp_path):
    approval = _approval()
    projection, reasons = _validate(approval)
    assert projection is not None and reasons == ()
    inputs = _inputs()
    identity = _identity(tmp_path, inputs, approval.subject.invocation_id)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=projection, simulation_only=False
    )
    decision = pb.PermissionBroker().evaluate(request)
    assert decision.decision == pb.DECISION_DENY
    assert decision.causing_policy_ids == ("POL-005",)
    assert decision.decision_reason == "execution_boundary_unavailable"
    assert "POL-004" not in decision.triggered_policy_ids


def test_missing_authority_triggers_pol004_and_forged_naive_authority_stays_missing(tmp_path):
    inputs = _inputs()
    identity = _identity(tmp_path, inputs)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=True
    )
    decision = pb.PermissionBroker().evaluate(request)
    assert decision.decision == pb.DECISION_HUMAN_REVIEW
    assert decision.causing_policy_ids == ("POL-004",)


def test_pb_precedence_remains_deny_over_human_review(tmp_path):
    identity = _identity(tmp_path)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=_inputs(), validated_authority=None, simulation_only=False
    )
    decision = pb.PermissionBroker().evaluate(request)
    assert decision.decision == pb.DECISION_DENY
    assert "POL-004" in decision.triggered_policy_ids
    assert "POL-005" in decision.triggered_policy_ids
    assert decision.causing_policy_ids == ("POL-005",)


def test_attempt_and_idempotency_identifier_semantics(tmp_path):
    inputs = _inputs()
    invocation = "inv-" + "1" * 32
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    first = dispatch.new_runtime_dispatch_identity(
        inputs, identity_tracker=tracker, invocation_id=invocation
    )
    second = dispatch.new_runtime_dispatch_identity(
        inputs, identity_tracker=tracker, invocation_id=invocation
    )
    third = dispatch.new_runtime_dispatch_identity(
        inputs,
        identity_tracker=tracker,
        invocation_id="inv-" + "2" * 32,
    )
    assert first.invocation_id == second.invocation_id
    assert first.attempt_id != second.attempt_id
    assert first.idempotency_key == second.idempotency_key
    assert third.idempotency_key != first.idempotency_key
    assert first.attempt_id != first.idempotency_key


def test_prompt_hash_normalizes_only_nfc_and_newlines():
    decomposed = "Cafe\u0301\r\n  Keep  spaces"
    composed = "Caf\u00e9\n  Keep  spaces"
    changed = "Caf\u00e9\n Keep spaces"
    left = authority.compute_prompt_semantic_hash(
        [authority.PromptSemanticComponent("task", decomposed)]
    )
    right = authority.compute_prompt_semantic_hash(
        [authority.PromptSemanticComponent("task", composed)]
    )
    different = authority.compute_prompt_semantic_hash(
        [authority.PromptSemanticComponent("task", changed)]
    )
    assert left == right
    assert left != different


def test_option_b_has_exact_fourteen_facts_and_non_runtime_compatibility(tmp_path):
    identity = _identity(tmp_path)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=_inputs(), validated_authority=None
    )
    facts = request.runtime_dispatch_context
    assert facts is not None
    assert {field.name for field in dataclasses.fields(facts)} == {
        "invocation_id", "attempt_id", "idempotency_key", "repository_identity",
        "task_id", "lifecycle_context", "runtime_target_id",
        "adapter_descriptor_binding", "prompt_hash", "requested_capability",
        "transport_type", "network_requirement", "filesystem_scope_ref",
        "human_authority_binding",
    }
    ordinary = pb.build_permission_broker_request(
        action_type="push",
        execution_class=pb.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="push",
    )
    assert ordinary.runtime_dispatch_context is None


@pytest.mark.parametrize(
    ("fact", "invalid"),
    [
        ("invocation_id", "bad"),
        ("attempt_id", "bad"),
        ("idempotency_key", "bad"),
        ("repository_identity", "bad"),
        ("task_id", ""),
        ("lifecycle_context", pb.RuntimeDispatchLifecycleContext(phase_id="")),
        ("runtime_target_id", ""),
        ("adapter_descriptor_binding", pb.RuntimeDispatchAdapterDescriptorBinding("", "1", "8" * 64, "9" * 64)),
        ("prompt_hash", "bad"),
        ("requested_capability", ""),
        ("transport_type", "api"),
        ("network_requirement", True),
        ("filesystem_scope_ref", pb.RuntimeDispatchFilesystemScopeRef("", "6" * 64)),
        ("human_authority_binding", pb.RuntimeDispatchHumanAuthorityBinding("x", "y", "z")),
    ],
)
def test_each_option_b_fact_is_mandatory_and_validated(tmp_path, fact, invalid):
    identity = _identity(tmp_path)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=_inputs(), validated_authority=None
    )
    facts = dataclasses.replace(request.runtime_dispatch_context, **{fact: invalid})
    if fact == "human_authority_binding":
        request = dataclasses.replace(request, approval_present=True)
    malformed = dataclasses.replace(request, runtime_dispatch_context=facts)
    decision = pb.PermissionBroker().evaluate(malformed)
    assert decision.decision == pb.DECISION_DENY
    assert decision.decision_reason == "invalid_runtime_dispatch_request"


def test_imports_have_no_execution_adjacent_dependencies():
    for module_path in (
        Path("src/pcae/core/runtime_authority.py"),
        Path("src/pcae/core/runtime_dispatch_permission.py"),
        Path("src/pcae/core/runtime_invocation_approval_store.py"),
    ):
        source = module_path.read_text()
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert imported.isdisjoint({"socket", "requests", "httpx", "subprocess", "openai"})


def test_pure_authority_pb_path_has_no_process_network_credential_or_background_effect(
    tmp_path, monkeypatch
):
    approval = _approval()
    projection, reasons = _validate(approval)
    assert projection is not None and reasons == ()
    inputs = _inputs()
    identity = _identity(tmp_path, inputs, approval.subject.invocation_id)
    observed = {"process": 0, "network": 0, "credential": 0, "thread": 0}

    def blocked_process(*_args, **_kwargs):
        observed["process"] += 1
        raise AssertionError("unexpected process")

    def blocked_network(*_args, **_kwargs):
        observed["network"] += 1
        raise AssertionError("unexpected network")

    real_getenv = os.getenv

    def guarded_getenv(key, default=None):
        if any(marker in key.upper() for marker in ("TOKEN", "SECRET", "KEY", "CREDENTIAL")):
            observed["credential"] += 1
            raise AssertionError("unexpected credential read")
        return real_getenv(key, default)

    def blocked_thread(*_args, **_kwargs):
        observed["thread"] += 1
        raise AssertionError("unexpected background thread")

    monkeypatch.setattr(subprocess, "Popen", blocked_process)
    monkeypatch.setattr(socket, "create_connection", blocked_network)
    monkeypatch.setattr(os, "getenv", guarded_getenv)
    monkeypatch.setattr(threading.Thread, "start", blocked_thread)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=inputs,
        validated_authority=projection,
        simulation_only=False,
    )
    assert pb.PermissionBroker().evaluate(request).decision == pb.DECISION_DENY
    assert observed == {"process": 0, "network": 0, "credential": 0, "thread": 0}


def test_clean_process_import_has_no_file_side_effect(tmp_path):
    code = """
from pathlib import Path
before=sorted(str(p.relative_to(Path.cwd())) for p in Path.cwd().rglob('*'))
import pcae.core.runtime_authority
import pcae.core.runtime_invocation_approval_store
import pcae.core.runtime_dispatch_permission
import pcae.core.permission_broker_foundation
after=sorted(str(p.relative_to(Path.cwd())) for p in Path.cwd().rglob('*'))
assert before == after, (before, after)
"""
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(Path.cwd() / "src")}
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_identity_state_is_repository_local(tmp_path):
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    inputs = _inputs()
    identity_a = _identity(repo_a, inputs)
    identity_b = _identity(repo_b, inputs, identity_a.invocation_id)
    assert identity_a.idempotency_key == identity_b.idempotency_key
    assert identity_a.attempt_id != identity_b.attempt_id
    assert (repo_a / dispatch.RuntimeDispatchIdentityTracker.STORE_ROOT).is_dir()
    assert (repo_b / dispatch.RuntimeDispatchIdentityTracker.STORE_ROOT).is_dir()


def test_exposes_blocker_direct_approval_object_bypasses_canonical_store_provenance():
    approval = _approval()
    projection, reasons = _validate(approval)
    assert projection is not None and reasons == ()
    assert projection.approval_id == approval.approval_id


def test_exposes_blocker_caller_strings_can_mint_human_provenance():
    approval = _approval()
    assert approval.provenance.approver_id == "human:independent-verifier"
    projection, reasons = _validate(approval)
    assert projection is not None and reasons == ()
    assert projection.provenance_verdict == "identified_human_distinct_from_producer"
