"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.8 — Independent Verification of the
B1/B7/N1/N2 Production Authority Repair Implementation (.1R.7).

RE-DERIVE, DO NOT TRUST.  These cases were constructed from the primary
contracts (RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0,
RDGO-001 v3.0, RPAC-001 v1.0, POL-005) and from current production source
(``runtime_authority.py``, ``runtime_dispatch_permission.py``,
``hpac_verifier.py``), not from ``.1R.7``'s own report or test names.

The deterministic HPAC mechanism is permanently NON-REAL: no production
assurance mechanism exists.  Every positive case therefore verifies
structural / provenance plumbing only, up to the Option-A NON-REAL hard
stop.  No case asserts that a deterministic authentication can become real
production authority.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hpac_verifier
from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_permission as dispatch
from pcae.core.hpac_foundation import HPACAuthorityClass
from pcae.core.hpac_verifier import HPACVerificationError
from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore

from _rdw3w_helpers import (
    always_unconsumed,
    construct_test_only_deterministic_approval,
    dispatch_inputs,
    matching_context,
)
from test_hpac_verifier import NOW, _Rig

REPO_ROOT = Path(__file__).resolve().parents[1]
PRE_1R7_BASELINE = "b85e903c62f386f3c5a45747ded5ff7682b77267"


# ─────────────────────────────────────────────────────────────────────────
# Shared fixture: a canonical, persisted approval whose HPAC chain verifies
# structurally at NON-REAL assurance.
# ─────────────────────────────────────────────────────────────────────────
def _canonical_authority(tmp_path):
    invocation_id = "inv-" + "a" * 32
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


def _creation_kwargs(approval):
    return {
        "subject": approval.subject,
        "governance_context": approval.governance_context,
        "approval_scope": approval.approval_scope,
        "adapter_binding": approval.adapter_binding,
        "freshness_snapshot": approval.freshness_snapshot,
        "created_at": approval.created_at,
        "expires_at": approval.expires_at,
    }


def _emit_registered_projection(**overrides):
    """Independently reproduce what ``validate_approval`` would register on
    success, since the NON-REAL hard stop makes the real emission path
    unreachable.  This exercises the B1 predicate, not an authority claim."""
    fields = dict(
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
        mechanism_id="mech",
        mechanism_assurance="production",
        invocation_id="inv-" + "7" * 32,
    )
    fields.update(overrides)
    projection = authority.ValidatedAuthorityProjection(**fields)
    object.__setattr__(
        projection, "_content_binding_digest", projection.evidence_digest()
    )
    authority._VALIDATED_AUTHORITY_CONTEXTS[projection] = object()
    return projection


# ═══════════════════════════════════════════════════════════════════════
# B1 — trusted authority projection is not a transferable bearer token
# ═══════════════════════════════════════════════════════════════════════
def test_b1_pre_repair_seal_field_is_gone_from_source():
    """The pre-repair defect was an identity-only ``_validator_seal``
    compared against one module-level sentinel.  Re-derive from source
    that the sentinel no longer exists and the field is gone."""
    src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    assert "_VALIDATED_AUTHORITY_SEAL" not in src
    assert "_validator_seal" not in src
    assert "_VALIDATED_AUTHORITY_CONTEXTS" in src
    assert "_content_binding_digest" in src


def test_b1_pre_repair_copyable_seal_reconstructed_from_fixed_baseline():
    """At the immutable pre-.1R.7 baseline, a copied projection kept its
    seal for free via dataclasses.replace (compare=False field)."""
    old = subprocess.run(
        ["git", "show", f"{PRE_1R7_BASELINE}:src/pcae/core/runtime_authority.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert "_VALIDATED_AUTHORITY_SEAL = object()" in old
    assert "value._validator_seal is _VALIDATED_AUTHORITY_SEAL" in old
    # compare=False => dataclasses.replace copies it verbatim onto any content.
    assert "field(default=None, repr=False, compare=False)" in old


def test_b1_copied_projection_is_rejected():
    original = _emit_registered_projection()
    try:
        assert authority.is_trusted_validated_authority_projection(original) is True
        for clone in (copy.copy(original), copy.deepcopy(original),
                      dataclasses.replace(original)):
            assert authority.is_trusted_validated_authority_projection(clone) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b1_field_mutation_breaks_the_recomputed_content_binding():
    original = _emit_registered_projection()
    try:
        object.__setattr__(original, "approval_id", "ria-" + "9" * 32)
        assert authority.is_trusted_validated_authority_projection(original) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b1_reregistered_transfer_to_a_different_invocation_is_rejected():
    original = _emit_registered_projection()
    try:
        moved = dataclasses.replace(
            original, invocation_id="inv-" + "0" * 32, _content_binding_digest=""
        )
        object.__setattr__(moved, "_content_binding_digest", moved.evidence_digest())
        # Recomputed binding is now self-consistent, but the object was never
        # registered by validate_approval.
        assert authority.is_trusted_validated_authority_projection(moved) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(original, None)


def test_b1_hand_built_lookalike_without_registry_membership_is_rejected():
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
        mechanism_id="mech",
        mechanism_assurance="production",
        invocation_id="inv-" + "7" * 32,
    )
    object.__setattr__(
        projection, "_content_binding_digest", projection.evidence_digest()
    )
    # Exact fields, exact digest, but not in the exact-object registry.
    assert authority.is_trusted_validated_authority_projection(projection) is False


def test_b1_dispatch_binding_rejects_untrusted_projection():
    inputs = dispatch_inputs()
    identity = _make_identity(inputs)
    lookalike = authority.ValidatedAuthorityProjection(
        approval_id="ria-" + "1" * 32,
        record_digest="2" * 64,
        subject_scope_binding_digest="3" * 64,
        provenance_verdict="principal_derived",
        freshness_verdict_digest="4" * 64,
        expiry_verdict="not_expired",
        consumption_state_verdict=authority.CONSUMPTION_STATE_NONE,
        validated_at=NOW,
    )
    with pytest.raises(dispatch.RuntimeDispatchConstructionError,
                       match="untrusted_validated_authority_projection"):
        dispatch.project_human_authority_binding(
            lookalike, identity=identity, inputs=inputs, current_time=NOW
        )


# ═══════════════════════════════════════════════════════════════════════
# B7 — dispatch identity is revalidated against the durable registry
# ═══════════════════════════════════════════════════════════════════════
def _make_identity(inputs, root: Path | None = None):
    tracker = dispatch.RuntimeDispatchIdentityTracker(root or Path(_tmpdir()))
    return dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker), tracker


_TMPDIRS = []


def _tmpdir():
    import tempfile
    d = str(Path(tempfile.mkdtemp()).resolve())
    _TMPDIRS.append(d)
    return d


def test_b7_pre_repair_had_no_dispatch_time_registry_reread():
    old = subprocess.run(
        ["git", "show", f"{PRE_1R7_BASELINE}:src/pcae/core/runtime_dispatch_permission.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert "def revalidate(self" not in old
    now = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert "def revalidate(self" in now
    assert "_identity_tracker.revalidate(identity)" in now


def test_b7_valid_registry_passes_reread(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None
    )
    assert request.approval_present is False
    assert request.runtime_dispatch_context.attempt_id == identity.attempt_id


def test_b7_registry_record_deleted_after_mint_fails_closed(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    root = tmp_path / ".pcae" / "runtime-dispatch-identities" / "v1"
    (root / "invocations" / f"{identity.invocation_id}.json").unlink()
    with pytest.raises(dispatch.RuntimeDispatchConstructionError,
                       match="identity_store_record_missing|identity_registry_mismatch"):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=inputs, validated_authority=None
        )


def test_b7_registry_record_content_changed_after_mint_fails_closed(tmp_path):
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    rec = tmp_path / ".pcae" / "runtime-dispatch-identities" / "v1" / "invocations" / f"{identity.invocation_id}.json"
    rec.write_text('{"invocation_id":"inv-tampered","idempotency_key":"x"}')
    with pytest.raises(dispatch.RuntimeDispatchConstructionError,
                       match="identity_registry_mismatch|identity_record"):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=identity, inputs=inputs, validated_authority=None
        )


def test_b7_identity_from_a_different_tracker_is_rejected(tmp_path):
    inputs = dispatch_inputs()
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    t1 = dispatch.RuntimeDispatchIdentityTracker(tmp_path / "a")
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=t1)
    # Rebind a foreign tracker onto the frozen identity.
    t2 = dispatch.RuntimeDispatchIdentityTracker(tmp_path / "b")
    forged = dataclasses.replace(identity, _identity_tracker=t2)
    with pytest.raises(dispatch.RuntimeDispatchConstructionError):
        dispatch.build_runtime_dispatch_permission_broker_request(
            identity=forged, inputs=inputs, validated_authority=None
        )


# ═══════════════════════════════════════════════════════════════════════
# B7 / HPAC-REQ-054 Step 4 — independent challenge digest recomputation
# ═══════════════════════════════════════════════════════════════════════
def test_step4_is_implemented_as_independent_recomputation_not_agreement(tmp_path):
    src = (REPO_ROOT / "src/pcae/core/hpac_verifier.py").read_text()
    assert "recomputed_challenge_digest = canonical_digest(challenge_body)" in src
    assert "independently recomputed challenge state" in src
    # Step-4 field set mirrors HPAC-REQ-049 / open_challenge_canonical.
    for field in ("domain_separator", "challenge_version", "proof_schema_version",
                  "principal_id", "credential_id", "approval_subject_digest",
                  "trusted_presentation_digest", "nonce", "issued_at", "expires_at"):
        assert f'"{field}": challenge.{field}' in src


def test_step4_caller_supplied_challenge_value_alone_is_not_trusted(tmp_path):
    rig = _Rig(tmp_path)
    tampered = dataclasses.replace(rig.challenge, nonce="attacker-nonce")
    with pytest.raises(HPACVerificationError, match="independently recomputed"):
        rig.verify(challenge=tampered)


def test_step4_self_consistent_substituted_challenge_still_rejected(tmp_path):
    rig = _Rig(tmp_path)
    changed = dataclasses.replace(rig.challenge, nonce="attacker-nonce")
    body = {
        "domain_separator": changed.domain_separator,
        "challenge_version": changed.challenge_version,
        "proof_schema_version": changed.proof_schema_version,
        "principal_id": changed.principal_id,
        "credential_id": changed.credential_id,
        "approval_subject_digest": changed.approval_subject_digest,
        "trusted_presentation_digest": changed.trusted_presentation_digest,
        "nonce": changed.nonce,
        "issued_at": changed.issued_at,
        "expires_at": changed.expires_at,
    }
    changed = dataclasses.replace(
        changed, challenge_digest=hpac_verifier.canonical_digest(body)
    )
    with pytest.raises(HPACVerificationError, match="canonical proof"):
        rig.verify(challenge=changed)


def test_step4_challenge_from_another_invocation_is_rejected(tmp_path):
    rig_a = _Rig(tmp_path / "a", invocation_id="iv-a")
    rig_b = _Rig(tmp_path / "b", invocation_id="iv-b")
    with pytest.raises(HPACVerificationError):
        rig_a.verify(challenge=rig_b.challenge)


def test_step4_changed_invocation_parameter_changes_recomputed_digest(tmp_path):
    rig = _Rig(tmp_path)
    d1 = hpac_verifier.canonical_digest({
        "domain_separator": rig.challenge.domain_separator,
        "challenge_version": rig.challenge.challenge_version,
        "proof_schema_version": rig.challenge.proof_schema_version,
        "principal_id": rig.challenge.principal_id,
        "credential_id": rig.challenge.credential_id,
        "approval_subject_digest": rig.challenge.approval_subject_digest,
        "trusted_presentation_digest": rig.challenge.trusted_presentation_digest,
        "nonce": rig.challenge.nonce,
        "issued_at": rig.challenge.issued_at,
        "expires_at": rig.challenge.expires_at,
    })
    d2 = hpac_verifier.canonical_digest({
        "domain_separator": rig.challenge.domain_separator,
        "challenge_version": rig.challenge.challenge_version,
        "proof_schema_version": rig.challenge.proof_schema_version,
        "principal_id": rig.challenge.principal_id,
        "credential_id": rig.challenge.credential_id,
        "approval_subject_digest": "different-subject-digest",
        "trusted_presentation_digest": rig.challenge.trusted_presentation_digest,
        "nonce": rig.challenge.nonce,
        "issued_at": rig.challenge.issued_at,
        "expires_at": rig.challenge.expires_at,
    })
    assert d1 != d2


# ═══════════════════════════════════════════════════════════════════════
# N1 — approval authority requires canonical-store resolution
# ═══════════════════════════════════════════════════════════════════════
def test_n1_validate_approval_no_longer_accepts_an_approval_object_signature():
    old = subprocess.run(
        ["git", "show", f"{PRE_1R7_BASELINE}:src/pcae/core/runtime_authority.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert "def validate_approval(\n    approval: RuntimeInvocationApproval | None," in old
    now = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    assert "def validate_approval(\n    approval_id: object," in now


def test_n1_external_wellformed_approval_object_is_rejected(tmp_path):
    _, principal, approval, store, context = _canonical_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval,  # a fully valid object, but a caller object
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("noncanonical_approval_reference:caller_supplied_object",)


def test_n1_duck_typed_lookalike_store_is_rejected(tmp_path):
    _, principal, approval, real_store, context = _canonical_authority(tmp_path)

    class FakeStore:
        def load(self, approval_id):
            return real_store.load(approval_id)

    projection, reasons = authority.validate_approval(
        approval.approval_id,
        approval_store=FakeStore(),
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("canonical_approval_store_required",)


def test_n1_noncanonical_approval_id_is_rejected(tmp_path):
    _, principal, _, store, context = _canonical_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        "not-a-valid-ria-id",
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons == ("noncanonical_approval_id",)


def test_n1_unresolvable_canonical_id_is_rejected(tmp_path):
    _, principal, _, store, context = _canonical_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        "ria-" + "b" * 32,
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("no_valid_approval")


def test_n1_canonical_id_path_reaches_hpac_stage_then_non_real_stop(tmp_path):
    """Structural success up to — and stopping at — the NON-REAL boundary."""
    _, principal, approval, store, context = _canonical_authority(tmp_path)
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


def test_n1_validation_does_not_mutate_the_canonical_record(tmp_path):
    _, principal, approval, store, context = _canonical_authority(tmp_path)
    rec = (tmp_path / ".pcae" / "runtime-invocation-approvals" / "v1"
           / approval.approval_id / "approval.json")
    before = rec.read_bytes()
    authority.validate_approval(
        approval.approval_id, approval_store=store,
        authenticated_principal=principal, context=context,
        consumption_lookup=always_unconsumed,
    )
    assert rec.read_bytes() == before
    assert not (tmp_path / ".pcae" / "runtime-invocation-authority-consumption").exists()


# ═══════════════════════════════════════════════════════════════════════
# N2 — human provenance is verifier-owned, never caller text
# ═══════════════════════════════════════════════════════════════════════
def test_n2_pre_repair_accepted_freeform_approver_id_string():
    old = subprocess.run(
        ["git", "show", f"{PRE_1R7_BASELINE}:src/pcae/core/runtime_authority.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert "    approver_id: str,\n    identity_evidence_kind: str,\n" in old


def test_n2_caller_supplied_approver_id_raises(tmp_path):
    _, _, approval, _, _ = _canonical_authority(tmp_path)
    with pytest.raises(TypeError, match="cannot establish human authority"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval),
            approver_id="ceo@example.com",
            identity_evidence_kind=authority.IDENTITY_EVIDENCE_OS_AUTHENTICATED_USER,
        )


def test_n2_forged_principal_shape_is_not_verifier_provenance(tmp_path):
    _, principal, approval, _, _ = _canonical_authority(tmp_path)
    forged = object.__new__(type(principal))
    for slot in type(principal).__slots__:
        setattr(forged, slot, getattr(principal, slot))
    assert hpac_verifier.is_verifier_authenticated_principal(forged) is False
    with pytest.raises(ValueError, match="not_verifier_issued"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval), authenticated_principal=forged
        )


def test_n2_copy_and_deepcopy_of_principal_are_not_verifier_provenance(tmp_path):
    _, principal, _, _, _ = _canonical_authority(tmp_path)
    # Stronger than "copy is not registered": the verifier result refuses to
    # be copied or serialized at all (HPAC-REQ-058), so a copy-based forgery
    # cannot even be constructed.
    with pytest.raises(TypeError):
        copy.copy(principal)
    with pytest.raises(TypeError):
        copy.deepcopy(principal)
    import pickle
    with pytest.raises(TypeError):
        pickle.dumps(principal)


def test_n2_legitimate_verifier_principal_is_recognized_but_still_non_real(tmp_path):
    _, principal, approval, _, _ = _canonical_authority(tmp_path)
    # Provenance recognized:
    assert hpac_verifier.is_verifier_authenticated_principal(principal) is True
    # ...yet real production authority still refused because assurance is NON_REAL:
    with pytest.raises(ValueError, match="non_real_authenticated_principal"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval), authenticated_principal=principal
        )


def test_n2_principal_derived_binding_requires_matching_invocation(tmp_path):
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "c" * 32)
    principal = rig.verify()
    other = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id,
        invocation_id="inv-" + "d" * 32,
        approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z",
        expires_at="2026-08-28T00:04:30Z",
    )
    with pytest.raises(ValueError, match="invocation_mismatch"):
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(other), authenticated_principal=principal
        )


# ═══════════════════════════════════════════════════════════════════════
# Option-A — deterministic NON-REAL hard stop at the authority boundary
# ═══════════════════════════════════════════════════════════════════════
def test_optiona_no_fixture_store_can_be_constructed_at_production_assurance():
    """The central safety property: no deterministically-writable HPAC
    store can carry PRODUCTION authority_class, so verify_human_authentication
    can never emit a PRODUCTION principal."""
    from pcae.core.hpac_foundation import HPACStoreAuthority
    fixture = HPACStoreAuthority.fixture(Path(_tmpdir()))
    assert fixture.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert fixture.is_real_runtime_eligible is False
    # A fixture authority can only ever mint a FIXTURE_NON_REAL writer.
    writer = fixture.writer("genesis")
    assert writer.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    # The production authority cannot even initialise its root on this host
    # (protected-root resolution / boundary validation fails closed).
    with pytest.raises(Exception):
        auth = HPACStoreAuthority.production()
        auth._ensure_root(create=False)


def test_optiona_hard_stop_present_in_both_creation_and_validation():
    src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    assert src.count("HPACAuthorityClass.PRODUCTION") >= 2
    assert "non_real_authenticated_principal_cannot_create_production_approval" in src
    assert "non_real_authenticated_principal_cannot_validate_production_approval" in src


def test_optiona_no_deterministic_real_authority_path_exists_in_repo(tmp_path):
    """Behavioural: across several deterministic rig configurations, a
    verifier-issued, registry-passing principal is ALWAYS FIXTURE_NON_REAL,
    and require_real_assurance=True hard-rejects it."""
    for i, inv in enumerate(("inv-" + "1" * 32, "inv-" + "2" * 32, "inv-" + "3" * 32)):
        rig = _Rig(tmp_path / f"r{i}", invocation_id=inv)
        principal = rig.verify()
        assert hpac_verifier.is_verifier_authenticated_principal(principal) is True
        assert principal.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
        assert principal.is_real_runtime_eligible is False
        with pytest.raises(HPACVerificationError, match="FIXTURE_NON_REAL|real-runtime assurance"):
            rig.verify(require_real_assurance=True)


def test_optiona_full_strength_deterministic_chain_is_still_rejected(tmp_path):
    """Strongest available deterministic path — canonical principal,
    credential, presentation, proof, lifecycle, UP=UV=true, verifier
    provenance valid, canonical approval, exact invocation binding — and
    real authority creation still fails specifically on assurance."""
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "e" * 32)
    principal = rig.verify()
    assert principal.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id, invocation_id="inv-" + "e" * 32,
        approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z", expires_at="2026-08-28T00:04:30Z",
    )
    with pytest.raises(ValueError) as exc:
        authority.create_runtime_invocation_approval(
            **_creation_kwargs(approval), authenticated_principal=principal
        )
    assert "non_real_authenticated_principal_cannot_create_production_approval" in str(exc.value)


# ═══════════════════════════════════════════════════════════════════════
# Freshness / revocation — fresh reverification at the consumption point
# ═══════════════════════════════════════════════════════════════════════
def _revoke(rig, what):
    admin = rig.registry.fixture_admin_writer()
    if what == "principal":
        rig.registry.revoke_principal(admin, principal_id=rig.principal_id,
                                      revoked_at="2026-08-28T00:02:30Z")
    else:
        rig.registry.revoke_credential(admin, credential_id=rig.credential_id,
                                       revoked_at="2026-08-28T00:02:30Z")


@pytest.mark.parametrize("what", ["principal", "credential"])
def test_freshness_revocation_between_auth_and_consumption_fails_closed(tmp_path, what):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    _revoke(rig, what)
    projection, reasons = authority.validate_approval(
        approval.approval_id, approval_store=store,
        authenticated_principal=principal, context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed")


def test_freshness_lost_registry_membership_simulated_restart_fails_closed(tmp_path):
    _, principal, approval, store, context = _canonical_authority(tmp_path)
    hpac_verifier._AUTHENTIC_PRINCIPAL_REGISTRY.discard(principal)
    hpac_verifier._AUTHENTIC_PRINCIPAL_CONTEXTS.pop(principal, None)
    try:
        projection, reasons = authority.validate_approval(
            approval.approval_id, approval_store=store,
            authenticated_principal=principal, context=context,
            consumption_lookup=always_unconsumed,
        )
        assert projection is None
        assert reasons == ("authenticated_principal_not_verifier_issued",)
    finally:
        pass  # deliberately not restored: principal is now permanently stale


def test_freshness_replayed_consumption_state_is_rejected(tmp_path):
    _, principal, approval, store, context = _canonical_authority(tmp_path)
    projection, reasons = authority.validate_approval(
        approval.approval_id, approval_store=store,
        authenticated_principal=principal, context=context,
        consumption_lookup=lambda _id: "consumed",
    )
    assert projection is None
    assert reasons[0].startswith(("unrecognized_consumption_state", "consumption"))


# ═══════════════════════════════════════════════════════════════════════
# Approval intent stays separate from authentication
# ═══════════════════════════════════════════════════════════════════════
def test_authentication_success_alone_does_not_imply_approval_authority(tmp_path):
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "f" * 32)
    principal = rig.verify()  # authentication OK (NON-REAL)
    store = RuntimeInvocationApprovalStore(tmp_path)  # no approval persisted
    context = matching_context(
        construct_test_only_deterministic_approval(
            approval_id=rig.approval_id, invocation_id="inv-" + "f" * 32,
            approver_id=rig.principal_id,
            created_at="2026-08-28T00:02:00Z", expires_at="2026-08-28T00:04:30Z",
        ),
        current_time=NOW,
    )
    projection, reasons = authority.validate_approval(
        rig.approval_id, approval_store=store,
        authenticated_principal=principal, context=context,
        consumption_lookup=always_unconsumed,
    )
    assert projection is None
    assert reasons[0].startswith("no_valid_approval")


# ═══════════════════════════════════════════════════════════════════════
# RIHAC projection provenance is process-local, not serializable
# ═══════════════════════════════════════════════════════════════════════
def test_projection_registry_is_process_local_and_not_serializable():
    src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    # In-process dict keyed by exact object identity, module-level, never
    # persisted (no open()/write of the registry anywhere in the module).
    assert "_VALIDATED_AUTHORITY_CONTEXTS: dict[" in src
    proj = _emit_registered_projection()
    try:
        restored = copy.deepcopy(proj)  # "serialize + restore" analogue
        assert authority.is_trusted_validated_authority_projection(restored) is False
    finally:
        authority._VALIDATED_AUTHORITY_CONTEXTS.pop(proj, None)


# ═══════════════════════════════════════════════════════════════════════
# Isolation — no Gate-5/9/10, PB, POL-005, or runtime leakage
# ═══════════════════════════════════════════════════════════════════════
def test_isolation_only_three_production_files_changed_since_baseline():
    changed = subprocess.run(
        ["git", "diff", "--name-only", PRE_1R7_BASELINE, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.11 re-baseline (`.1R.9` §29 /
    # prompt §29): `.1R.10` added the authorized Gate-5 approval-validation
    # coordinator (`runtime_dispatch_gate5.py`, new) plus a +21-line
    # read-only accessor in `runtime_authority.py` and a +27-line read-only
    # resolver in `hpac_lifecycle.py` (`.1R.9` §6.2 row 23 / §16.1 slice 1).
    # `.1R.11` independently re-derived that this is the exact authorized
    # slice, introduces no PB / Gate-9 / runtime path, and leaves the
    # NON-REAL hard stop and every B1/B7/N1/N2/F1 property intact.
    assert set(changed) == {
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/hpac_lifecycle.py",
    }


def test_isolation_no_gate_coordinator_or_gate9_consumption_wiring():
    src_root = REPO_ROOT / "src" / "pcae"
    gate9_callers, projection_consumers, hpac_consumers = set(), set(), set()
    for path in src_root.rglob("*.py"):
        rel = str(path.relative_to(REPO_ROOT))
        text = path.read_text(encoding="utf-8")
        if path.name != "runtime_invocation_authority_consumption.py" and \
           path.name != "hpac_verifier.py" and \
           "import" in text and "runtime_invocation_authority_consumption" in text:
            # only count real imports
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)) and \
                   "runtime_invocation_authority_consumption" in ast.dump(node):
                    gate9_callers.add(rel)
        if path.name not in ("runtime_authority.py",) and "ValidatedAuthorityProjection" in text:
            projection_consumers.add(rel)
        if path.name != "hpac_verifier.py" and "hpac_verifier" in text:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)) and "hpac_verifier" in ast.dump(node):
                    hpac_consumers.add(rel)
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.11 re-baseline: `.1R.10` added the
    # authorized Gate-5 coordinator. It reads `ValidatedAuthorityProjection`
    # only through `runtime_authority.trusted_projection_gate5_binding`
    # (gated on `is_trusted_validated_authority_projection`) and imports the
    # `hpac_verifier` public predicate `is_verifier_authenticated_principal`
    # only. `gate9_callers` stays empty -- the coordinator calls no Gate-9
    # atomic-consumption primitive (`.1R.11`-verified; `.1R.12`+ is the PB
    # slice, Gate 9 remains frozen).
    assert gate9_callers == set()
    assert projection_consumers == {
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
    }
    assert hpac_consumers == {
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
    }


def test_isolation_repaired_modules_import_nothing_effectful():
    forbidden = {"subprocess", "socket", "requests", "httpx", "urllib",
                 "fido2", "webauthn", "ctap", "smartcard", "usb"}
    for name in ("hpac_verifier", "runtime_authority", "runtime_dispatch_permission"):
        tree = ast.parse((REPO_ROOT / f"src/pcae/core/{name}.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in forbidden
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden


def test_isolation_pol005_denies_any_execution_claim(tmp_path):
    from pcae.core.permission_broker_foundation import (
        PermissionBroker, ExecutionDisabledRule,
    )
    inputs = dispatch_inputs()
    tracker = dispatch.RuntimeDispatchIdentityTracker(tmp_path)
    identity = dispatch.new_runtime_dispatch_identity(inputs, identity_tracker=tracker)
    request = dispatch.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None,
        simulation_only=False,
    )
    decision = PermissionBroker().evaluate(request)
    assert decision.decision == "DENY"
    assert "POL-005" in decision.causing_policy_ids


def test_isolation_contract_and_pol005_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
    ):
        old = subprocess.run(
            ["git", "show", f"{PRE_1R7_BASELINE}:{rel}"],
            cwd=REPO_ROOT, capture_output=True, check=True,
        ).stdout
        cur = (REPO_ROOT / rel).read_bytes()
        assert hashlib.sha256(old).hexdigest() == hashlib.sha256(cur).hexdigest(), rel


def test_isolation_runtime_state_remains_unavailable():
    from pcae.core import runtime_introspection as ri
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    assert ri.IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_isolation_test_only_fixture_not_importable_by_production():
    src_root = REPO_ROOT / "src" / "pcae"
    for path in src_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "_rdw3w_helpers"
            if isinstance(node, ast.Import):
                assert all(a.name != "_rdw3w_helpers" for a in node.names)
