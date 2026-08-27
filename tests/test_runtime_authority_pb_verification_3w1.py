"""Independent Phase 149O.20L.7O.3W.1 adversarial verification.

These tests intentionally reconstruct their own fixtures rather than import
Phase 3W's ``_rdw3w_helpers``.  Tests whose names contain
``demonstrates_blocking_gap`` assert the currently observed unsafe behavior;
they are evidence for a NOT VERIFIED verdict, not an endorsement of it.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core.runtime_invocation_approval_store import (
    ApprovalStoreIntegrityError,
    RuntimeInvocationApprovalStore,
    STORE_ROOT,
)


H_A = "a" * 64
H_B = "b" * 64
H_C = "c" * 64
HEAD_A = "1" * 40
HEAD_B = "2" * 40
CREATED = "2026-08-27T12:00:00Z"
EXPIRES = "2026-08-27T13:00:00Z"
NOW = "2026-08-27T12:30:00Z"


def subject(**changes: object) -> ra.ApprovalSubject:
    values: dict[str, object] = {
        "invocation_id": "inv-" + "1" * 32,
        "runtime_target_id": "fixture.local.v1",
        "prompt_hash": H_A,
        "repository_identity": H_B,
        "task_id": "task-3w1",
    }
    values.update(changes)
    return ra.ApprovalSubject(**values)  # type: ignore[arg-type]


def scope(**changes: object) -> ra.ApprovalScope:
    values: dict[str, object] = {
        "requested_capability": "bounded.execute",
        "filesystem_scope_ref": ra.ArtifactRef("fs-scope", H_A),
        "process_profile_ref": ra.ArtifactRef("process-profile", H_B),
    }
    values.update(changes)
    return ra.ApprovalScope(**values)  # type: ignore[arg-type]


def approval(**changes: object) -> ra.RuntimeInvocationApproval:
    values: dict[str, object] = {
        "subject": subject(),
        "governance_context": ra.GovernanceContext("149O.20L.7O.3W.1", "session-3w1"),
        "approval_scope": scope(),
        "adapter_binding": ra.AdapterBinding("adapter.fixture", "1.0", H_B, H_C),
        "freshness_snapshot": ra.FreshnessSnapshot(HEAD_A, H_C, "policy-v1"),
        "approver_id": "human:operator",
        "identity_evidence_kind": ra.IDENTITY_EVIDENCE_TYPED_CONFIRMATION_ONLY,
        "created_at": CREATED,
        "expires_at": EXPIRES,
    }
    values.update(changes)
    return ra.create_runtime_invocation_approval(**values)  # type: ignore[arg-type]


def context(item: ra.RuntimeInvocationApproval, **changes: object) -> ra.InvocationRequestContext:
    values: dict[str, object] = {
        "invocation_id": item.subject.invocation_id,
        "runtime_target_id": item.subject.runtime_target_id,
        "prompt_hash": item.subject.prompt_hash,
        "repository_identity": item.subject.repository_identity,
        "task_id": item.subject.task_id,
        "phase_id": item.governance_context.phase_id,
        "session_id": item.governance_context.session_id,
        "requested_capability": item.approval_scope.requested_capability,
        "adapter_id": item.adapter_binding.adapter_id,
        "descriptor_version": item.adapter_binding.descriptor_version,
        "descriptor_digest": item.adapter_binding.descriptor_digest,
        "target_config_digest": item.adapter_binding.target_config_digest,
        "head_commit": item.freshness_snapshot.head_commit,
        "task_contract_digest": item.freshness_snapshot.task_contract_digest,
        "task_state": "active",
        "policy_version": item.freshness_snapshot.policy_version,
        "current_time": NOW,
    }
    values.update(changes)
    return ra.InvocationRequestContext(**values)  # type: ignore[arg-type]


def inputs(item: ra.RuntimeInvocationApproval, **changes: object) -> rdp.RuntimeDispatchRequestConstructionInput:
    values: dict[str, object] = {
        "repository_identity": item.subject.repository_identity,
        "task_id": item.subject.task_id,
        "lifecycle_context": pbf.RuntimeDispatchLifecycleContext(
            item.governance_context.phase_id, item.governance_context.session_id
        ),
        "runtime_target_id": item.subject.runtime_target_id,
        "adapter_descriptor_binding": pbf.RuntimeDispatchAdapterDescriptorBinding(
            item.adapter_binding.adapter_id,
            item.adapter_binding.descriptor_version,
            item.adapter_binding.descriptor_digest,
            item.adapter_binding.target_config_digest,
        ),
        "prompt_hash": item.subject.prompt_hash,
        "requested_capability": item.approval_scope.requested_capability,
        "filesystem_scope_ref": pbf.RuntimeDispatchFilesystemScopeRef(
            item.approval_scope.filesystem_scope_ref.artifact_id,
            item.approval_scope.filesystem_scope_ref.artifact_digest,
        ),
    }
    values.update(changes)
    return rdp.RuntimeDispatchRequestConstructionInput(**values)  # type: ignore[arg-type]


def unconsumed(_: str) -> str:
    return ra.CONSUMPTION_STATE_NONE


def validate(item: ra.RuntimeInvocationApproval, **context_changes: object):
    return ra.validate_approval(
        item, context=context(item, **context_changes), consumption_lookup=unconsumed
    )


def redigest(
    item: ra.RuntimeInvocationApproval, **changes: object
) -> ra.RuntimeInvocationApproval:
    changed = dataclasses.replace(item, record_digest="", **changes)
    return dataclasses.replace(changed, record_digest=ra.compute_record_digest(changed))


def valid_projection(item: ra.RuntimeInvocationApproval) -> ra.ValidatedAuthorityProjection:
    projection, reasons = validate(item)
    assert projection is not None
    assert reasons == ()
    return projection


def build_request(item: ra.RuntimeInvocationApproval, *, simulation_only: bool):
    bound_inputs = inputs(item)
    identity = rdp.new_runtime_dispatch_identity(
        bound_inputs, invocation_id=item.subject.invocation_id
    )
    return rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=bound_inputs,
        validated_authority=valid_projection(item),
        simulation_only=simulation_only,
    )


def test_exact_riasc_top_level_and_subject_cardinalities():
    item = approval()
    assert set(item.to_dict()) == {
        "schema_id", "schema_version", "contract_version", "record_type",
        "approval_id", "record_digest", "created_at", "expires_at", "subject",
        "governance_context", "prompt_hash_profile", "approval_scope",
        "adapter_binding", "freshness_snapshot", "provenance", "attempt_limit",
    }
    assert len(item.to_dict()) == 16
    assert set(item.to_dict()["subject"]) == {
        "invocation_id", "runtime_target_id", "prompt_hash",
        "repository_identity", "task_id",
    }
    assert len(item.to_dict()["subject"]) == 5


@pytest.mark.parametrize("missing", sorted(ra._TOP_LEVEL_REQUIRED))
def test_every_missing_top_level_field_fails_shape(missing: str):
    raw = approval().to_dict()
    del raw[missing]
    assert any("missing_field" in issue for issue in ra.validate_riasc_schema_shape(raw))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("governance_context", "phase_id"), []),
        (("approval_scope", "requested_capability"), []),
        (("approval_scope", "filesystem_scope_ref", "artifact_id"), []),
        (("approval_scope", "filesystem_scope_ref", "artifact_digest"), "not-a-digest"),
        (("adapter_binding", "adapter_id"), []),
        (("adapter_binding", "descriptor_version"), []),
        (("freshness_snapshot", "policy_version"), []),
        (("provenance", "approver_id"), []),
    ],
)
def test_incomplete_schema_type_enforcement_demonstrates_blocking_gap(path, value):
    raw = approval().to_dict()
    cursor = raw
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    assert ra.validate_riasc_schema_shape(raw) == ()


@pytest.mark.parametrize(
    "shortcut",
    ["approved", "authorized", "permission", "ALLOW", "approval_present",
     "execution_available", "pb_allow"],
)
def test_authority_shortcut_fields_fail_closed(shortcut: str):
    raw = approval().to_dict()
    raw[shortcut] = True
    assert ra.validate_riasc_schema_shape(raw)


def test_unknown_nested_field_fails_closed():
    raw = approval().to_dict()
    raw["subject"]["future_authority"] = True
    assert "subject_unknown_field:future_authority" in ra.validate_riasc_schema_shape(raw)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("invocation_id", "inv-" + "2" * 32),
        ("runtime_target_id", "other.target"),
        ("prompt_hash", H_B),
        ("repository_identity", H_C),
        ("task_id", "other-task"),
    ],
)
def test_each_subject_member_mismatch_fails_closed(field: str, replacement: str):
    item = approval()
    projection, reasons = validate(item, **{field: replacement})
    assert projection is None
    assert any("mismatch" in reason for reason in reasons)


def test_preview_digest_is_not_verified_demonstrates_blocking_gap():
    item = approval()
    tampered_provenance = dataclasses.replace(
        item.provenance, approval_preview_digest="f" * 64
    )
    tampered = redigest(item, provenance=tampered_provenance)
    projection, reasons = validate(tampered)
    assert projection is not None
    assert reasons == ()


def test_descriptor_version_is_not_bound_demonstrates_blocking_gap():
    item = approval()
    projection, reasons = validate(item, descriptor_version="999.0")
    assert projection is not None
    assert reasons == ()


def test_filesystem_scope_is_not_cross_bound_demonstrates_blocking_gap():
    item = approval()
    projection = valid_projection(item)
    changed_inputs = inputs(
        item, filesystem_scope_ref=pbf.RuntimeDispatchFilesystemScopeRef("broader", H_C)
    )
    identity = rdp.new_runtime_dispatch_identity(
        changed_inputs, invocation_id=item.subject.invocation_id
    )
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=changed_inputs,
        validated_authority=projection,
        simulation_only=True,
    )
    assert request.approval_present is True
    assert request.runtime_dispatch_context.filesystem_scope_ref.scope_id == "broader"


@pytest.mark.parametrize(
    "bad_id",
    ["..", "../x", "ria/" + "1" * 32, "ria\\" + "1" * 32,
     "/absolute", "ria-" + "1" * 31, "ria-" + "1" * 33,
     "ria-" + "1" * 31 + "／", "ria-" + "1" * 31 + "∕"],
)
def test_store_rejects_noncanonical_or_pathlike_ids(tmp_path: Path, bad_id: str):
    store = RuntimeInvocationApprovalStore(tmp_path)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(bad_id)


def test_store_duplicate_create_fails_closed(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    store.create(item)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(item)


@pytest.mark.parametrize("content", ["{", "[]", "{}"])
def test_store_corrupt_json_or_wrong_schema_fails_closed(tmp_path: Path, content: str):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    target = tmp_path / STORE_ROOT / item.approval_id / "approval.json"
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(item.approval_id)


def test_store_filename_record_identity_mismatch_fails_closed(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    requested = approval()
    other = approval()
    target = tmp_path / STORE_ROOT / requested.approval_id / "approval.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(other.to_dict()), encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        store.load(requested.approval_id)


def test_duplicate_json_identity_is_accepted_demonstrates_blocking_gap(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    raw = json.dumps(item.to_dict(), sort_keys=True, separators=(",", ":"))
    marker = f'"approval_id":"{item.approval_id}"'
    conflict = 'ria-' + 'f' * 32
    raw = raw.replace(marker, f'"approval_id":"{conflict}",{marker}', 1)
    target = tmp_path / STORE_ROOT / item.approval_id / "approval.json"
    target.parent.mkdir(parents=True)
    target.write_text(raw, encoding="utf-8")
    assert store.load(item.approval_id) is not None


def test_approval_directory_symlink_escapes_store_demonstrates_blocking_gap(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    external = tmp_path / "outside"
    external.mkdir()
    link = tmp_path / STORE_ROOT / item.approval_id
    link.parent.mkdir(parents=True)
    link.symlink_to(external, target_is_directory=True)
    store.create(item)
    assert (external / "approval.json").exists()


def test_precreated_tmp_symlink_overwrites_external_file_demonstrates_blocking_gap(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    approval_dir = tmp_path / STORE_ROOT / item.approval_id
    approval_dir.mkdir(parents=True)
    external = tmp_path / "outside.txt"
    external.write_text("sentinel", encoding="utf-8")
    (approval_dir / "approval.json.tmp").symlink_to(external)
    store.create(item)
    assert external.read_text(encoding="utf-8") != "sentinel"


def test_precreated_tmp_hardlink_overwrites_external_file_demonstrates_blocking_gap(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    approval_dir = tmp_path / STORE_ROOT / item.approval_id
    approval_dir.mkdir(parents=True)
    external = tmp_path / "outside-hardlink.txt"
    external.write_text("sentinel", encoding="utf-8")
    os.link(external, approval_dir / "approval.json.tmp")
    store.create(item)
    assert external.read_text(encoding="utf-8") != "sentinel"


def test_rename_failure_leaves_no_final_artifact(tmp_path: Path, monkeypatch):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    original = Path.replace

    def fail_replace(self: Path, target: Path):
        if self.name == "approval.json.tmp":
            raise OSError("fault injected")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="fault injected"):
        store.create(item)
    assert not (tmp_path / STORE_ROOT / item.approval_id / "approval.json").exists()


def test_repo_task_target_prompt_and_head_replay_fail_closed():
    item = approval()
    mutations = {
        "repository_identity": H_C,
        "task_id": "task-b",
        "runtime_target_id": "target-b",
        "prompt_hash": H_B,
        "head_commit": HEAD_B,
    }
    for field, value in mutations.items():
        projection, _ = validate(item, **{field: value})
        assert projection is None, field


def test_all_seven_freshness_conditions_have_fail_closed_or_refresh_semantics():
    item = approval()
    failing = [
        {"head_commit": HEAD_B},
        {"task_contract_digest": H_A},
        {"task_state": "done"},
        {"prompt_hash": H_B},
        {"runtime_target_id": "target-b"},
        {"target_config_digest": H_A},
        {"current_time": EXPIRES},
    ]
    for mutation in failing:
        projection, _ = validate(item, **mutation)
        assert projection is None, mutation
    projection, reasons = validate(item, policy_version="policy-v2")
    assert projection is not None
    assert reasons == ("policy_drift_requires_fresh_pb_re_evaluation",)


def test_fractional_timestamp_comparison_accepts_expired_approval_demonstrates_blocking_gap():
    item = approval(expires_at="2026-08-27T12:30:00Z")
    projection, reasons = validate(item, current_time="2026-08-27T12:30:00.9Z")
    assert projection is not None
    assert reasons == ()


def test_creation_uses_lexical_time_order_demonstrates_blocking_gap():
    item = approval(
        created_at="2026-08-27T12:00:00.9Z",
        expires_at="2026-08-27T12:00:00Z",
    )
    assert (item.expires_at < item.created_at) is False  # lexical, but chronologically earlier


def test_validation_and_pol005_deny_do_not_consume_approval(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    store.create(item)
    before = (tmp_path / STORE_ROOT / item.approval_id / "approval.json").read_bytes()
    first = valid_projection(store.load(item.approval_id))  # type: ignore[arg-type]
    second = valid_projection(store.load(item.approval_id))  # type: ignore[arg-type]
    assert first == second
    request = build_request(item, simulation_only=False)
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids
    after = (tmp_path / STORE_ROOT / item.approval_id / "approval.json").read_bytes()
    assert after == before


def test_restart_load_preserves_identity_and_digest(tmp_path: Path):
    store = RuntimeInvocationApprovalStore(tmp_path)
    item = approval()
    store.create(item)
    code = (
        "import sys; from pathlib import Path; "
        "from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore; "
        "a=RuntimeInvocationApprovalStore(Path(sys.argv[1])).load(sys.argv[2]); "
        "print(a.approval_id, a.record_digest)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), item.approval_id],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == f"{item.approval_id} {item.record_digest}"


def test_attempt_id_format_uniqueness_and_identity_distinction():
    item = approval()
    bound_inputs = inputs(item)
    first = rdp.new_runtime_dispatch_identity(bound_inputs)
    second = rdp.new_runtime_dispatch_identity(bound_inputs)
    assert re.fullmatch(r"att-[0-9a-f]{32}", first.attempt_id)
    assert first.attempt_id != second.attempt_id
    assert first.invocation_id != first.attempt_id != first.idempotency_key


def test_idempotency_is_deterministic_across_processes():
    item = approval()
    projection = rdp.canonical_runtime_dispatch_projection(inputs(item))
    expected = rdp.compute_runtime_dispatch_idempotency_key(projection)
    code = (
        "import json,sys; from pcae.core.runtime_invocation import "
        "compute_runtime_dispatch_idempotency_key as f; print(f(json.loads(sys.argv[1])))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, json.dumps(projection, sort_keys=True)],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_identity", H_C),
        ("task_id", "task-b"),
        ("runtime_target_id", "target-b"),
        ("prompt_hash", H_B),
    ],
)
def test_idempotency_changes_for_represented_identity_fields(field: str, value: str):
    item = approval()
    first = inputs(item)
    second = inputs(item, **{field: value})
    assert rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(first)
    ) != rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(second)
    )


def test_idempotency_projection_omits_contract_fields_demonstrates_blocking_gap():
    field_names = {field.name for field in dataclasses.fields(rdp.RuntimeDispatchRequestConstructionInput)}
    assert {
        "base_commit", "task_contract_digest", "process_profile_ref",
        "approval_scope", "effect_class", "network_requirement", "resource_budget",
    }.isdisjoint(field_names)


def test_distinct_invocations_share_key_demonstrates_blocking_gap():
    item = approval()
    bound_inputs = inputs(item)
    first = rdp.new_runtime_dispatch_identity(bound_inputs)
    second = rdp.new_runtime_dispatch_identity(bound_inputs)
    assert first.invocation_id != second.invocation_id
    assert first.idempotency_key == second.idempotency_key


def test_runtime_context_is_optional_for_runtime_dispatch_demonstrates_blocking_gap():
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
        execution_class=pbf.EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006",
        requested_capability="bounded.execute",
        task_id="task-3w1",
        phase_id="149O.20L.7O.3W.1",
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
        runtime_dispatch_context=None,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_ALLOW
    assert request.runtime_dispatch_context is None


def test_public_projection_is_forgeable_demonstrates_blocking_gap():
    item = approval()
    forged = ra.ValidatedAuthorityProjection(
        approval_id="ria-" + "f" * 32,
        record_digest=H_A,
        subject_scope_binding_digest=H_B,
        provenance_verdict="identified_human_distinct_from_producer",
        freshness_verdict_digest=H_C,
        expiry_verdict="not_expired",
        consumption_state_verdict=ra.CONSUMPTION_STATE_NONE,
        validated_at=NOW,
    )
    bound_inputs = inputs(item)
    identity = rdp.new_runtime_dispatch_identity(bound_inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=bound_inputs,
        validated_authority=forged,
        simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert request.approval_present is True
    assert decision.decision == pbf.DECISION_ALLOW
    assert "POL-004" not in decision.triggered_policy_ids


def test_pol004_and_pol005_rule_specific_behavior_and_precedence():
    item = approval()
    bound_inputs = inputs(item)
    identity = rdp.new_runtime_dispatch_identity(bound_inputs)
    no_approval = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=bound_inputs,
        validated_authority=None,
        simulation_only=False,
    )
    decision = pbf.PermissionBroker().evaluate(no_approval)
    assert "POL-004" in decision.triggered_policy_ids
    assert "POL-005" in decision.triggered_policy_ids
    assert decision.decision == pbf.DECISION_DENY
    assert decision.causing_policy_ids == ("POL-005",)


def test_valid_approval_and_valid_real_request_still_denied_by_pol005():
    request = build_request(approval(), simulation_only=False)
    decision = pbf.PermissionBroker().evaluate(request)
    assert request.approval_present is True
    assert decision.decision == pbf.DECISION_DENY
    assert decision.causing_policy_ids == ("POL-005",)


def test_existing_action_remains_context_free_and_compatible():
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_PUSH,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="push",
        task_id="task-3w1",
        evidence_available=True,
        simulation_only=True,
    )
    assert request.runtime_dispatch_context is None
    assert pbf.PermissionBroker().evaluate(request).decision == pbf.DECISION_ALLOW


def test_new_modules_have_no_re_shell_process_network_or_provider_imports():
    modules = [ra, rdp, sys.modules[RuntimeInvocationApprovalStore.__module__]]
    forbidden = (
        "runtime_enforcement", "shell_gate", "subprocess", "socket", "requests",
        "httpx", "urllib", "openai", "anthropic", "credential",
    )
    for module in modules:
        source = inspect.getsource(module)
        imports = "\n".join(
            line for line in source.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        )
        assert not any(name in imports for name in forbidden)


def test_full_authority_pb_path_has_no_external_effect_calls(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: calls.append("subprocess.Popen"))
    monkeypatch.setattr(os, "system", lambda *a, **k: calls.append("os.system"))
    monkeypatch.setattr(socket, "socket", lambda *a, **k: calls.append("socket.socket"))
    monkeypatch.setattr(threading.Thread, "start", lambda *a, **k: calls.append("thread.start"))
    request = build_request(approval(), simulation_only=False)
    assert pbf.PermissionBroker().evaluate(request).decision == pbf.DECISION_DENY
    assert calls == []


def test_clean_process_imports_create_no_files(tmp_path: Path):
    before = set(tmp_path.rglob("*"))
    code = (
        "import pcae.core.runtime_authority; "
        "import pcae.core.runtime_invocation_approval_store; "
        "import pcae.core.runtime_dispatch_permission"
    )
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, check=True)
    assert set(tmp_path.rglob("*")) == before


def test_no_mutable_module_level_authority_cache_or_registry():
    for module in (ra, rdp):
        mutable = {
            name: value for name, value in vars(module).items()
            if not name.startswith("__") and isinstance(value, (dict, list, set))
        }
        assert mutable == {}
