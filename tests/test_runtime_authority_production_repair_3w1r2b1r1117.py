"""Phase .1R.7 defensive verification for B1/B7/N1/N2 and HPAC Step 4.

The deterministic fixture remains explicitly NON-REAL.  Positive tests in
this module prove structural registration/revalidation only; none asserts
that a deterministic authentication can become production authority.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
from pathlib import Path
import subprocess

import pytest

from pcae.core import hpac_verifier
from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_permission as dispatch
from pcae.core.hpac_verifier import HPACVerificationError
from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore
from pcae.core.hpac_lifecycle import STATE_REVOKED

from _rdw3w_helpers import (
    always_unconsumed,
    construct_test_only_deterministic_approval,
    dispatch_inputs,
    matching_context,
)
from test_hpac_verifier import NOW, _Rig


def _fixture_authority(tmp_path: Path):
    invocation_id = "inv-" + "7" * 32
    rig = _Rig(tmp_path / "hpac", invocation_id=invocation_id)
    principal = rig.verify()
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id,
        invocation_id=invocation_id,
        approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z",
        expires_at="2026-08-28T00:04:30Z",
    )
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    context = matching_context(approval, current_time=NOW)
    return rig, principal, approval, store, context


def _creation_kwargs(approval: authority.RuntimeInvocationApproval) -> dict:
    return {
        "subject": approval.subject,
        "governance_context": approval.governance_context,
        "approval_scope": approval.approval_scope,
        "adapter_binding": approval.adapter_binding,
        "freshness_snapshot": approval.freshness_snapshot,
        "created_at": approval.created_at,
        "expires_at": approval.expires_at,
    }


def test_step4_rejects_challenge_state_whose_digest_was_not_recomputed(tmp_path):
    rig = _Rig(tmp_path)
    tampered = dataclasses.replace(rig.challenge, nonce="caller-substituted-nonce")
    with pytest.raises(HPACVerificationError, match="independently recomputed"):
        rig.verify(challenge=tampered)


def test_step4_rejects_self_consistent_challenge_substituted_against_proof(tmp_path):
    rig = _Rig(tmp_path)
    changed = dataclasses.replace(rig.challenge, nonce="caller-substituted-nonce")
    body = {
        name: getattr(changed, name)
        for name in (
            "domain_separator",
            "challenge_version",
            "proof_schema_version",
            "principal_id",
            "credential_id",
            "approval_subject_digest",
            "trusted_presentation_digest",
            "nonce",
            "issued_at",
            "expires_at",
        )
    }
    changed = dataclasses.replace(
        changed, challenge_digest=hpac_verifier.canonical_digest(body)
    )
    with pytest.raises(HPACVerificationError, match="canonical proof"):
        rig.verify(challenge=changed)


def test_n1_rejects_caller_constructed_approval_object_before_shape_trust(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("noncanonical_approval_reference:caller_supplied_object",)


def test_n1_rejects_copied_canonical_approval_object_as_independent_authority(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    copied = copy.copy(approval)
    projection, reasons = authority.validate_approval(
        copied,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("noncanonical_approval_reference:caller_supplied_object",)


def test_n1_rejects_noncanonical_approval_id(tmp_path):
    _, principal, _, store, context = _fixture_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        "../approval.json",
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("noncanonical_approval_id",)


def test_n1_requires_the_concrete_canonical_store(tmp_path):
    _, principal, approval, _, context = _fixture_authority(tmp_path)

    class CallerStore:
        def load(self, _approval_id):
            return approval

    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=CallerStore(),
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("canonical_approval_store_required",)


def test_n1_validation_actually_rereads_store_and_does_not_mutate_it(tmp_path, monkeypatch):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    approval_path = (
        tmp_path
        / ".pcae"
        / "runtime-invocation-approvals"
        / "v1"
        / approval.approval_id
        / "approval.json"
    )
    before = approval_path.read_bytes()
    original_load = store.load
    calls = []

    def observed_load(approval_id):
        calls.append(approval_id)
        return original_load(approval_id)

    monkeypatch.setattr(store, "load", observed_load)
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("non_real_authenticated_principal_cannot_validate_production_approval",)
    assert calls == [approval.approval_id]
    assert approval_path.read_bytes() == before


def test_n2_caller_strings_are_explicitly_rejected(tmp_path):
    _, _, approval, _, _ = _fixture_authority(tmp_path)
    with pytest.raises(TypeError, match="caller-supplied approver_id"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval),
            approver_id="human-looking-string",
            identity_evidence_kind=authority.IDENTITY_EVIDENCE_OS_AUTHENTICATED_USER,
        )


def test_n2_copied_principal_shape_is_not_verifier_provenance(tmp_path):
    _, principal, approval, _, _ = _fixture_authority(tmp_path)
    copied = object.__new__(type(principal))
    for slot in type(principal).__slots__:
        setattr(copied, slot, getattr(principal, slot))
    with pytest.raises(ValueError, match="not_verifier_issued"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval), authenticated_principal=copied
        )


def test_non_real_principal_cannot_create_production_approval(tmp_path):
    _, principal, approval, _, _ = _fixture_authority(tmp_path)
    with pytest.raises(ValueError, match="non_real_authenticated_principal"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval), authenticated_principal=principal
        )


def test_non_real_principal_cannot_validate_production_approval(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("non_real_authenticated_principal_cannot_validate_production_approval",)


def test_invocation_substitution_fails_closed(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    context = dataclasses.replace(context, invocation_id="inv-" + "8" * 32)
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("subject_mismatch:invocation_id",)


def test_lost_process_local_principal_registry_rejects_stale_result(tmp_path):
    _, principal, approval, _, _ = _fixture_authority(tmp_path)
    hpac_verifier._AUTHENTIC_PRINCIPAL_REGISTRY.discard(principal)
    try:
        with pytest.raises(ValueError, match="not_verifier_issued"):
            authority.create_runtime_invocation_approval(
                **_creation_kwargs(approval), authenticated_principal=principal
            )
    finally:
        hpac_verifier._AUTHENTIC_PRINCIPAL_REGISTRY.add(principal)


def test_revoked_credential_is_detected_by_fresh_reverification(tmp_path):
    rig, principal, approval, store, context = _fixture_authority(tmp_path)
    rig.registry.revoke_credential(
        rig.registry.fixture_admin_writer(),
        credential_id=rig.credential_id,
        revoked_at="2026-08-28T00:02:30Z",
    )
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed:")


def test_revoked_principal_is_detected_by_fresh_reverification(tmp_path):
    rig, principal, approval, store, context = _fixture_authority(tmp_path)
    rig.registry.revoke_principal(
        rig.registry.fixture_admin_writer(),
        principal_id=rig.principal_id,
        revoked_at="2026-08-28T00:02:30Z",
    )
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed:")


def test_expired_proof_challenge_is_detected_by_fresh_reverification(tmp_path):
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "9" * 32)
    principal = rig.verify()
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id,
        invocation_id=rig.invocation_id,
        approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z",
        expires_at="2026-08-28T00:10:00Z",
    )
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    context = matching_context(approval, current_time="2026-08-28T00:06:00Z")
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed:")


def test_expired_approval_is_rejected_after_current_hpac_reverification(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    context = dataclasses.replace(context, current_time="2026-08-28T00:04:31Z")
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("expired",)


def test_changed_presentation_state_is_detected_by_fresh_reverification(tmp_path):
    rig, principal, approval, store, context = _fixture_authority(tmp_path)
    path = rig.presentation_store._path(principal.presentation_id)
    path.write_text("{}", encoding="utf-8")
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed:")


def test_changed_lifecycle_state_is_detected_by_fresh_reverification(tmp_path):
    rig, principal, approval, store, context = _fixture_authority(tmp_path)
    rig.lifecycle_store.terminate_canonical(
        rig.lifecycle_store.fixture_terminal_writer(rig.proof_id),
        proof_id=rig.proof_id,
        state=STATE_REVOKED,
        reason_code="test-revocation",
        occurred_at="2026-08-28T00:02:30Z",
    )
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed:")


def test_replayed_approval_consumption_state_is_rejected(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=lambda _approval_id: authority.CONSUMPTION_STATE_CONSUMED,
    )
    assert projection is None
    assert reasons == ("already_bound:dispatch_attempted",)


def test_same_binding_proof_reverification_is_idempotent_and_not_consumption(tmp_path):
    rig, principal, approval, store, context = _fixture_authority(tmp_path)
    before = tuple(
        resolved.record.event_digest
        for resolved in rig.lifecycle_store.resolve_canonical_chain(rig.proof_id)
    )
    for _ in range(2):
        projection, reasons = authority.validate_approval(
            approval.approval_id,
            approval_store=store,
            authenticated_principal=principal,
            context=context,
            consumption_lookup=always_unconsumed,
        )
        assert projection is None
        assert reasons == (
            "non_real_authenticated_principal_cannot_validate_production_approval",
        )
    after = tuple(
        resolved.record.event_digest
        for resolved in rig.lifecycle_store.resolve_canonical_chain(rig.proof_id)
    )
    assert after == before
    assert not (tmp_path / ".pcae" / "runtime-invocation-authority-consumption").exists()


def _registered_test_projection():
    projection = authority.ValidatedAuthorityProjection(
        approval_id="ria-" + "1" * 32,
        record_digest="2" * 64,
        subject_scope_binding_digest="3" * 64,
        provenance_verdict="principal_derived",
        freshness_verdict_digest="4" * 64,
        expiry_verdict="not_expired",
        consumption_state_verdict=authority.CONSUMPTION_STATE_NONE,
        validated_at=NOW,
        principal_id="hp-" + "5" * 32,
        proof_id="hap-" + "6" * 32,
        mechanism_id="test-mechanism",
        mechanism_assurance="production",
        invocation_id="inv-" + "7" * 32,
    )
    object.__setattr__(projection, "_content_binding_digest", projection.evidence_digest())
    # Same-process private insertion is test scaffolding only. Production
    # validation is the sole legitimate writer of this registry.
    authority._VALIDATED_AUTHORITY_CONTEXTS[projection] = object()
    return projection


def test_b1_copied_projection_cannot_transfer_registry_provenance():
    original = _registered_test_projection()
    try:
        copied = copy.copy(original)
        assert authority.is_trusted_validated_authority_projection(original) is True
        assert authority.is_trusted_validated_authority_projection(copied) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b1_same_object_content_mutation_breaks_recomputed_binding():
    original = _registered_test_projection()
    try:
        object.__setattr__(original, "approval_id", "ria-" + "f" * 32)
        assert authority.is_trusted_validated_authority_projection(original) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b1_projection_cannot_transfer_to_another_invocation():
    original = _registered_test_projection()
    try:
        transferred = dataclasses.replace(
            original,
            invocation_id="inv-" + "8" * 32,
            _content_binding_digest="",
        )
        object.__setattr__(
            transferred, "_content_binding_digest", transferred.evidence_digest()
        )
        assert authority.is_trusted_validated_authority_projection(transferred) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b7_dispatch_builder_rereads_valid_registry(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None
    )
    assert request.runtime_dispatch_context.attempt_id == identity.attempt_id


def test_b7_unregistered_replaced_identity_fails_at_registry_reread(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    changed = dataclasses.replace(identity, attempt_id="att-" + "a" * 32)
    changed = dataclasses.replace(
        changed, _registration_digest=dispatch._identity_registration_digest(changed)
    )
    with pytest.raises(dispatch.RuntimeDispatchConstructionError, match="record_missing"):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=changed, inputs=inputs, validated_authority=None
        )


def test_b7_registry_deletion_between_mint_and_build_fails_closed(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    attempt_path = (
        tmp_path
        / dispatch.RuntimeDispatchIdentityTracker.STORE_ROOT
        / "attempts"
        / f"{identity.attempt_id}.json"
    )
    attempt_path.unlink()
    with pytest.raises(dispatch.RuntimeDispatchConstructionError, match="record_missing"):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=inputs, validated_authority=None
        )


def test_b7_registry_content_change_between_mint_and_build_fails_closed(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    attempt_path = (
        tmp_path
        / dispatch.RuntimeDispatchIdentityTracker.STORE_ROOT
        / "attempts"
        / f"{identity.attempt_id}.json"
    )
    attempt_path.write_text("{}", encoding="utf-8")
    with pytest.raises(dispatch.RuntimeDispatchConstructionError, match="registry_mismatch"):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=inputs, validated_authority=None
        )


def test_upstream_non_real_rejection_yields_no_pb_authority_and_runtime_stays_denied(tmp_path):
    _, principal, approval, store, context = _fixture_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("non_real_authenticated_principal_cannot_validate_production_approval",)
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(
        inputs, identity_tracker=tracker, invocation_id=approval.subject.invocation_id
    )
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity,
        inputs=inputs,
        validated_authority=projection,
        simulation_only=False,
    )
    from pcae.core.permission_broker_foundation import PermissionBroker

    decision = PermissionBroker().evaluate(request)
    assert request.approval_present is False
    assert decision.decision == "DENY"
    assert "POL-005" in decision.causing_policy_ids


def test_test_only_fixture_is_not_imported_by_production_modules():
    source_root = Path(__file__).resolve().parents[1] / "src" / "pcae"
    offenders = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "_rdw3w_helpers":
                offenders.append(str(path))
            if isinstance(node, ast.Import):
                offenders.extend(
                    str(path) for alias in node.names if alias.name == "_rdw3w_helpers"
                )
    assert offenders == []


def test_production_file_allowlist_matches_frozen_phase_matrix():
    repo = Path(__file__).resolve().parents[1]
    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "b85e903c62f386f3c5a45747ded5ff7682b77267",
            "--",
            "src/pcae",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.11 re-baseline (`.1R.9` §29):
    # `.1R.10` added the authorized Gate-5 approval-validation coordinator
    # (`runtime_dispatch_gate5.py`) plus read-only hooks in
    # `runtime_authority.py` (+21) and `hpac_lifecycle.py` (+27) -- `.1R.9`
    # §6.2 row 23 / §16.1 slice 1. `.1R.11` independently confirmed the
    # slice touches exactly these five files and introduces no PB / Gate-9 /
    # runtime path.
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.2 (V-13-1): converted from a
    # point-in-time equality assertion to a phase-aware invariant. Each
    # additional file below was added by its own individually human-
    # authorized runtime-dispatch-gate-chain phase (Gate 7 -> .1R.13.2 adds
    # runtime_dispatch_gate7.py). An unauthorized production-file expansion
    # still fails this test.
    _authorized_surface = {
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/hpac_lifecycle.py",
        "src/pcae/core/runtime_dispatch_gate7.py",  # Gate 7 (.1R.13.2)
        "src/pcae/core/runtime_dispatch_gate8.py",  # Gate 8 (.1R.13.4)
        "src/pcae/core/runtime_dispatch_gate9.py",  # Gate 9 (.1R.14)
    }
    unexpected = set(changed) - _authorized_surface
    assert unexpected == set(), f"unauthorized production-file expansion: {sorted(unexpected)}"


@pytest.mark.parametrize(
    ("relative_path", "expected_sha256"),
    [
        (
            "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
            "38d98e9b6bfee3d1097628b73f7fdcd70ca932a9dfda9007e764c0e9e90a04d0",
        ),
        (
            "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
            "a47869ba315a55b829982d03989c755aa753af9fef52667d7775ead31a95f608",
        ),
        (
            "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
            "24fd6fac04ea174d5387c4c945f5055896b77c466c149cd8d13dd3353db0567b",
        ),
        (
            "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
            "e0799d464af603b4be559c6be4607d2519635eea933ffd1cdde0e02d0e77ffef",
        ),
        (
            "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
            "24e1eefaedf4c63bc221e6460fecf3c055b88d9d7ba230a76d3ec113f511f5ab",
        ),
        (
            "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
            "395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89",
        ),
        (
            "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            "6daf404b608fd410a8e8c4551f06e76268e49abe056c96db49c1ecca99db02b2",
        ),
        (
            "src/pcae/core/permission_broker_foundation.py",
            "2eb7c1068736c10018482f6787ae9cbd7cf4cf8ceaeeac728e18b75dec2639d1",
        ),
    ],
)
def test_contract_and_pol005_bytes_remain_identical(relative_path, expected_sha256):
    path = Path(__file__).resolve().parents[1] / relative_path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256


def test_consumer_inventory_is_bounded_and_gate9_stays_unwired():
    repo = Path(__file__).resolve().parents[1]
    src_root = repo / "src" / "pcae"
    hpac_consumers = set()
    projection_consumers = set()
    gate9_consumers = set()
    for path in src_root.rglob("*.py"):
        if path.name == "hpac_verifier.py":
            continue
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(repo))
        if "hpac_verifier" in text:
            hpac_consumers.add(relative)
        if "ValidatedAuthorityProjection" in text and path.name != "runtime_authority.py":
            projection_consumers.add(relative)
        if (
            "runtime_invocation_authority_consumption" in text
            and path.name != "runtime_invocation_authority_consumption.py"
        ):
            gate9_consumers.add(relative)
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.11 re-baseline: `.1R.10`'s
    # authorized Gate-5 coordinator consumes the `hpac_verifier` public
    # predicate and `ValidatedAuthorityProjection` (via the gated
    # `trusted_projection_gate5_binding` accessor) only. `gate9_consumers`
    # stays empty -- no Gate-9 atomic-consumption wiring
    # (`.1R.11`-verified; Gate 9 frozen per `.1R.9`).
    assert hpac_consumers == {
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
    }
    # .1R.13.2 / .1R.13.4 (V-13-1): Gate 7 (runtime_dispatch_gate7.py) and
    # Gate 8 (runtime_dispatch_gate8.py) re-trust the Gate-5
    # ValidatedAuthorityProjection at their own point of use (RDGO-001 §8
    # item 3 / §9; plan §29). Phase-aware invariant: projection consumers
    # must be a SUBSET of the individually-authorized
    # runtime-dispatch-gate-chain modules; gate9 consumers stay empty.
    assert projection_consumers <= {
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unexpected ValidatedAuthorityProjection consumer: {sorted(projection_consumers)}"
    # .1R.14 (V-13-1): the Gate-9 atomic-consumption coordinator is the
    # single authorized consumer of the inert Gate-9 store
    # (`runtime_invocation_authority_consumption`) — the explicitly
    # human-authorized `.1R.9` §16.1 slice 3 / `.1R.13.1` §16 handoff.
    # Phase-aware subset invariant: any OTHER importer still fails.
    assert gate9_consumers <= {"src/pcae/core/runtime_dispatch_gate9.py"}, (
        f"unexpected Gate-9 store consumer: {sorted(gate9_consumers)}"
    )


def test_repaired_production_modules_have_no_effect_or_real_ceremony_imports():
    repo = Path(__file__).resolve().parents[1]
    paths = [
        repo / "src/pcae/core/hpac_verifier.py",
        repo / "src/pcae/core/runtime_authority.py",
        repo / "src/pcae/core/runtime_dispatch_permission.py",
    ]
    forbidden_import_roots = {
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "fido2",
        "webauthn",
        "ctap",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported.isdisjoint(forbidden_import_roots)
