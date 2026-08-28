"""Phase 149O.20L.7O.3W.1R seven-finding closure regressions."""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core.runtime_invocation_approval_store import (
    ApprovalStoreIntegrityError,
    RuntimeInvocationApprovalStore,
    STORE_ROOT,
)

from _rdw3w_helpers import (
    always_unconsumed,
    build_approval,
    dispatch_inputs,
    matching_context,
    new_dispatch_identity,
)


def _projection(item: ra.RuntimeInvocationApproval) -> ra.ValidatedAuthorityProjection:
    projection, reasons = ra.validate_approval(
        item, context=matching_context(item), consumption_lookup=always_unconsumed
    )
    assert projection is not None and reasons == ()
    return projection


def _redigest(
    item: ra.RuntimeInvocationApproval, **changes: object
) -> ra.RuntimeInvocationApproval:
    changed = dataclasses.replace(item, record_digest="", **changes)
    return dataclasses.replace(changed, record_digest=ra.compute_record_digest(changed))


def test_finding_1_forged_projection_and_raw_pb_shortcuts_fail_closed():
    item = build_approval()
    bound_inputs = dispatch_inputs()
    identity = new_dispatch_identity(
        bound_inputs, invocation_id=item.subject.invocation_id
    )
    forged = ra.ValidatedAuthorityProjection(
        approval_id=item.approval_id,
        record_digest=item.record_digest,
        subject_scope_binding_digest="a" * 64,
        provenance_verdict="identified_human_distinct_from_producer",
        freshness_verdict_digest="b" * 64,
        expiry_verdict="not_expired",
        consumption_state_verdict=ra.CONSUMPTION_STATE_NONE,
        validated_at="2026-08-27T00:30:00Z",
    )
    with pytest.raises(rdp.RuntimeDispatchConstructionError, match="untrusted"):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=bound_inputs, validated_authority=forged
        )

    direct = pbf.PermissionBrokerRequest(
        request_id="pbr-forged",
        timestamp="2026-08-27T00:30:00+00:00",
        action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
        execution_class=pbf.EXECUTION_CLASS_ADAPTER,
        task_id="task-a",
        phase_id="149O.20L.7O.3W",
        requested_component="COMP-006",
        requested_capability="local_cli_dispatch",
        requested_resource=None,
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
        runtime_dispatch_context=None,
    )
    decision = pbf.PermissionBroker().evaluate(direct)
    assert decision.decision == pbf.DECISION_DENY
    assert decision.decision_reason == "invalid_runtime_dispatch_request"


@pytest.mark.parametrize("attack", ["approval_dir_symlink", "tmp_symlink", "tmp_hardlink"])
def test_finding_2_store_link_attacks_cannot_escape_or_overwrite(
    tmp_path: Path, attack: str
):
    item = build_approval()
    store = RuntimeInvocationApprovalStore(tmp_path)
    approval_dir = tmp_path / STORE_ROOT / item.approval_id
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    approval_dir.parent.mkdir(parents=True)
    if attack == "approval_dir_symlink":
        approval_dir.symlink_to(outside, target_is_directory=True)
    else:
        approval_dir.mkdir()
        temporary = approval_dir / "approval.json.tmp"
        if attack == "tmp_symlink":
            temporary.symlink_to(sentinel)
        else:
            os.link(sentinel, temporary)
    with pytest.raises(ApprovalStoreIntegrityError):
        store.create(item)
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    assert not (outside / "approval.json").exists()


@pytest.mark.parametrize(
    ("path", "bad"),
    [
        (("governance_context", "phase_id"), []),
        (("approval_scope", "dispatch_limit"), True),
        (("adapter_binding", "descriptor_version"), 1),
        (("freshness_snapshot", "policy_version"), {}),
        (("provenance", "approver_id"), []),
    ],
)
def test_finding_3_nested_schema_types_fail_closed(path: tuple[str, ...], bad: object):
    raw = build_approval().to_dict()
    cursor = raw
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = bad
    assert ra.validate_riasc_schema_shape(raw)


def test_finding_3_duplicate_json_keys_fail_closed(tmp_path: Path):
    item = build_approval()
    raw = json.dumps(item.to_dict(), sort_keys=True, separators=(",", ":"))
    marker = f'"approval_id":"{item.approval_id}"'
    raw = raw.replace(marker, f'"approval_id":"ria-{"f" * 32}",{marker}', 1)
    target = tmp_path / STORE_ROOT / item.approval_id / "approval.json"
    target.parent.mkdir(parents=True)
    target.write_text(raw, encoding="utf-8")
    with pytest.raises(ApprovalStoreIntegrityError):
        RuntimeInvocationApprovalStore(tmp_path).load(item.approval_id)


def test_finding_4_preview_provenance_is_recomputed_and_bound():
    item = build_approval()
    tampered = _redigest(
        item,
        provenance=dataclasses.replace(
            item.provenance, approval_preview_digest="f" * 64
        ),
    )
    projection, reasons = ra.validate_approval(
        tampered, context=matching_context(tampered), consumption_lookup=always_unconsumed
    )
    assert projection is None
    assert reasons == ("approval_preview_digest_mismatch",)


def test_finding_5_descriptor_and_full_scope_are_cross_bound():
    item = build_approval()
    original = matching_context(item)
    changed_context = dataclasses.replace(
        original,
        adapter_binding=dataclasses.replace(
            original.adapter_binding, descriptor_version="2.0"
        ),
    )
    projection, reasons = ra.validate_approval(
        item, context=changed_context, consumption_lookup=always_unconsumed
    )
    assert projection is None
    assert reasons == ("adapter_binding_mismatch:adapter_binding",)

    valid, valid_reasons = ra.validate_approval(
        item, context=matching_context(item), consumption_lookup=always_unconsumed
    )
    assert valid is None
    assert valid_reasons == ("noncanonical_approval_reference:caller_supplied_object",)
    broader = dispatch_inputs(
        requested_capability=item.approval_scope.requested_capability
    )
    broader = dataclasses.replace(
        broader,
        filesystem_scope_ref=pbf.RuntimeDispatchFilesystemScopeRef(
            "broader", "f" * 64
        ),
    )
    identity = new_dispatch_identity(
        broader, invocation_id=item.subject.invocation_id
    )
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=broader, validated_authority=valid
    )
    assert request.approval_present is False


def test_finding_6_freshness_uses_chronological_instants():
    item = build_approval(expires_at="2026-08-27T00:30:00Z")
    projection, reasons = ra.validate_approval(
        item,
        context=matching_context(item, current_time="2026-08-27T00:30:00.9Z"),
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("expired",)
    with pytest.raises(ValueError, match="expires_at_must_be_after_created_at"):
        build_approval(
            created_at="2026-08-27T00:00:00.9Z",
            expires_at="2026-08-27T00:00:00Z",
        )


def test_finding_7_all_identity_facts_and_distinct_invocations_are_bound(tmp_path: Path):
    first_inputs = dispatch_inputs()
    first = new_dispatch_identity(first_inputs, root=tmp_path)
    second = new_dispatch_identity(first_inputs, root=tmp_path)
    assert first.invocation_id != second.invocation_id
    assert first.idempotency_key != second.idempotency_key
    projection = rdp.canonical_runtime_dispatch_projection(
        first_inputs, invocation_id=first.invocation_id
    )
    assert {
        "base_commit",
        "task_contract_digest",
        "process_profile_ref",
        "effect_class",
        "network_requirement",
        "resource_budget",
        "invocation_id",
    } <= projection.keys()


def test_finding_7_cross_process_retry_and_conflict_are_deterministic(tmp_path: Path):
    bound_inputs = dispatch_inputs()
    invocation_id = "inv-" + "9" * 32
    first = new_dispatch_identity(
        bound_inputs, root=tmp_path, invocation_id=invocation_id
    )
    code = """
import sys
from pathlib import Path
sys.path.insert(0, 'tests')
from _rdw3w_helpers import dispatch_inputs
from pcae.core import runtime_dispatch_permission as rdp
root = Path(sys.argv[1])
invocation_id = sys.argv[2]
changed = sys.argv[3] == 'changed'
inputs = dispatch_inputs(prompt='changed' if changed else 'Do the thing.')
try:
    identity = rdp.new_runtime_dispatch_identity(
        inputs,
        identity_tracker=rdp.RuntimeDispatchIdentityTracker(root),
        invocation_id=invocation_id,
    )
except rdp.RuntimeDispatchConstructionError:
    print('CONFLICT')
else:
    print(identity.idempotency_key)
"""
    same = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), invocation_id, "same"],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), invocation_id, "changed"],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert same.stdout.strip() == first.idempotency_key
    assert changed.stdout.strip() == "CONFLICT"


def test_finding_7_registered_identity_cannot_change_attempt_after_mint(tmp_path: Path):
    bound_inputs = dispatch_inputs()
    identity = new_dispatch_identity(bound_inputs, root=tmp_path)
    tampered = dataclasses.replace(identity, attempt_id="att-" + "f" * 32)
    with pytest.raises(rdp.RuntimeDispatchConstructionError, match="untrusted"):
        rdp.build_runtime_dispatch_permission_broker_request(
            identity=tampered, inputs=bound_inputs, validated_authority=None
        )
