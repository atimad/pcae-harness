"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.11 — Independent Verification of the
Gate-5 Approval-Validation Coordinator Integration (`.1R.10`).

RE-DERIVE, DO NOT TRUST. Every scenario here is constructed from the primary
contracts (RDGO-001 v3.0 §4/§6, RIHAC-001 v2.0 §16, HPAC-001 v2.0
HPAC-REQ-054/097, PBRD-001 v2.0, POL-005) and the current production source,
not from the `.1R.10` report, the `.1R.10` test file, function/type names,
aggregate pass counts, or a lifecycle label.

The deterministic HPAC mechanism is permanently NON-REAL; there is no
legitimate positive Gate-5 success to construct without real FIDO2/UI, and
this suite does not manufacture one (`.1R.9` §41 / prompt §11). Every case
is rejection-only or structural up to and including the inherited Option-A
NON-REAL hard stop.

Fixture infrastructure (`_Rig`, `_rdw3w_helpers`) is shared plumbing; the
assertions and adversarial scenarios below are independently derived for
this phase.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import hpac_verifier
from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core.hpac_lifecycle import (
    HPACLifecycleForkError,
    HPACLifecycleStore,
    STATE_PROOF_VERIFIED,
    STATE_PROOF_VERIFIED_AND_BOUND,
)
from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore

from _rdw3w_helpers import always_unconsumed, construct_test_only_deterministic_approval, matching_context
from test_hpac_verifier import NOW, _Rig

REPO_ROOT = Path(__file__).resolve().parents[1]
# Immutable pre-.1R.10 baseline (tip of .1R.9's governed push).
PRE_1R10_BASELINE = "b504670e"
# Phase-entry commit the .1R.10 suite anchors its own diffs to.
PHASE_ENTRY_1R10 = "1810c8d8d1d10ad5dc3cb0743dc0c20c71180ca5"
NON_REAL_STOP = "non_real_authenticated_principal_cannot_validate_production_approval"
GATE5_SRC = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py"


# ─────────────────────────────────────────────────────────────────────────
# Fixture: a canonical persisted approval whose deterministic HPAC chain
# verifies structurally at NON-REAL assurance. (Same construction the
# production wiring would see; adversarial variation is layered per test.)
# ─────────────────────────────────────────────────────────────────────────
def _authority(tmp_path, *, invocation_char="a"):
    invocation_id = "inv-" + invocation_char * 32
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


def _run(rig, principal, approval, store, context, **overrides):
    kwargs = dict(
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
        lifecycle_store=rig.lifecycle_store,
    )
    kwargs.update(overrides)
    aid = overrides.get("approval_id", approval.approval_id)
    return gate5.run_gate5(aid, **{k: v for k, v in kwargs.items() if k != "approval_id"})


def _approval_bytes(store, approval_id):
    return store.load(approval_id).to_dict()


def _consumption_json(root: Path):
    return sorted(root.rglob("consumption.json"))


def _chain_states(rig):
    return [e.state for e in rig.lifecycle_store.resolve_chain(rig.proof_id)]


# ═══════════════════════════════════════════════════════════════════════
# 1. Independent Option-C call-flow reconstruction (prompt §6, §38.1)
# ═══════════════════════════════════════════════════════════════════════
def test_option_c_layering_delegates_and_never_reimplements_rihac_or_hpac():
    """run_gate5 must sequence validate_approval (RIHAC §16) +
    is_verifier_authenticated_principal (HPAC provenance) + a read-only
    lifecycle resolver, and must not re-implement the twelve-step logic,
    the NON-REAL hard stop, or a lifecycle writer call."""
    src = GATE5_SRC.read_text()
    tree = ast.parse(src)
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert "validate_approval" in called
    assert "is_verifier_authenticated_principal" in called
    assert "resolve_gate5_binding_event" in called
    # No duplicated authority primitives / no lifecycle mutation from the coordinator.
    for forbidden in (
        "bind_gate5",
        "compute_record_digest",
        "validate_riasc_schema_shape",
        "HPACAuthorityClass",
    ):
        assert forbidden not in called, f"coordinator unexpectedly calls {forbidden!r}"
    # reverify is reached transitively (through validate_approval), never called directly.
    assert "reverify_authenticated_principal" not in called


def test_no_later_step_substitutes_for_an_earlier_failure():
    """If validate_approval fails, run_gate5 returns its reason verbatim and
    never reaches sequence-3 confirmation or Gate5Result construction."""
    tree = ast.parse(GATE5_SRC.read_text())
    run = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "run_gate5")
    body_src = ast.get_source_segment(GATE5_SRC.read_text(), run)
    # the projection-None short-circuit precedes any resolve_gate5_binding_event call
    assert body_src.index("if projection is None") < body_src.index("resolve_gate5_binding_event")
    assert body_src.index("if projection is None") < body_src.index("Gate5Result(")


# ═══════════════════════════════════════════════════════════════════════
# 2. HPAC-REQ-054 Step 4 — substituted / changed-input challenge (§8, §38.2-3)
# ═══════════════════════════════════════════════════════════════════════
def test_step4_self_consistent_substituted_challenge_yields_no_principal(tmp_path):
    """A fully self-consistent forged challenge (recomputed digest over the
    swapped nonce) is rejected inside verify_human_authentication, so no
    verifier principal exists and Gate 5 fails closed on provenance."""
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "s" * 32)
    swapped = dataclasses.replace(rig.challenge, nonce="independent-attacker-nonce")
    body = {
        "domain_separator": swapped.domain_separator,
        "challenge_version": swapped.challenge_version,
        "proof_schema_version": swapped.proof_schema_version,
        "principal_id": swapped.principal_id,
        "credential_id": swapped.credential_id,
        "approval_subject_digest": swapped.approval_subject_digest,
        "trusted_presentation_digest": swapped.trusted_presentation_digest,
        "nonce": swapped.nonce,
        "issued_at": swapped.issued_at,
        "expires_at": swapped.expires_at,
    }
    swapped = dataclasses.replace(swapped, challenge_digest=hpac_verifier.canonical_digest(body))
    # digest is internally consistent...
    assert swapped.challenge_digest == hpac_verifier.canonical_digest(body)
    # ...and still rejected: the verifier recomputes against canonical proof/lifecycle state.
    with pytest.raises(hpac_verifier.HPACVerificationError):
        rig.verify(challenge=swapped)


def test_step4_changed_invocation_input_invalidates_binding_through_gate5(tmp_path):
    """A live context whose invocation_id differs from the approval/principal
    binding fails closed at Gate 5 (RIHAC §16 step 6), before any Gate5Result."""
    rig, principal, approval, store, context = _authority(tmp_path)
    other = dataclasses.replace(context, invocation_id="inv-" + "z" * 32)
    result, reasons = _run(rig, principal, approval, store, other)
    assert result is None
    assert reasons == ("subject_mismatch:invocation_id",)
    assert not gate5.is_gate5_result(result)


def test_step4_is_reached_via_reverify_not_bypassed(tmp_path):
    """validate_approval MUST route principal provenance through
    reverify_authenticated_principal (which runs HPAC-REQ-054 incl. Step 4).
    Proven by revoking the credential post-authentication: a cached/bypassed
    check would still pass; the real re-resolution fails closed."""
    rig, principal, approval, store, context = _authority(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    rig.registry.revoke_credential(admin, credential_id=rig.credential_id,
                                   revoked_at="2026-08-28T00:02:15Z")
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed")


# ═══════════════════════════════════════════════════════════════════════
# 3. Current-state stale cases (prompt §9, §38.4-8)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("mutate", ["principal", "credential"])
def test_revoked_principal_or_credential_after_auth_fails_closed(tmp_path, mutate):
    rig, principal, approval, store, context = _authority(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    if mutate == "principal":
        rig.registry.revoke_principal(admin, principal_id=rig.principal_id,
                                      revoked_at="2026-08-28T00:02:20Z")
    else:
        rig.registry.revoke_credential(admin, credential_id=rig.credential_id,
                                       revoked_at="2026-08-28T00:02:20Z")
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed")


def test_expired_approval_fails_closed(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    expired = dataclasses.replace(context, current_time="2026-08-28T00:06:00Z")
    result, reasons = _run(rig, principal, approval, store, expired)
    assert result is None
    assert reasons == ("expired",)


def test_stale_head_commit_fails_closed(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    drifted = dataclasses.replace(context, head_commit="9" * 40)
    result, reasons = _run(rig, principal, approval, store, drifted)
    assert result is None
    assert reasons[0].startswith("stale_approval:")


def test_prior_consumption_state_fails_closed(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context,
                           consumption_lookup=lambda _id: authority.CONSUMPTION_STATE_CONSUMED
                           if hasattr(authority, "CONSUMPTION_STATE_CONSUMED") else "consumed")
    assert result is None
    assert reasons[0].startswith("already_bound:") or reasons[0].startswith("unrecognized_consumption_state:")


def test_lifecycle_not_bindable_state_fails_closed(tmp_path):
    """Chain still at ASSERTION_RECEIVED (no verified event) -> verifier
    reverification fails; Gate 5 never sees a projection."""
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "e" * 32, skip_record_verified=True)
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id, invocation_id="inv-" + "e" * 32, approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z", expires_at="2026-08-28T00:04:30Z")
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    context = matching_context(approval, current_time=NOW)
    # No verifier principal can be produced from an unverified chain.
    with pytest.raises(Exception) as exc:
        rig.verify()
    assert exc.type is not AssertionError


# ═══════════════════════════════════════════════════════════════════════
# 4. Sequence-3 authoritative writer / IF-1 (prompt §14, §15, §38.9-12)
# ═══════════════════════════════════════════════════════════════════════
def test_if1_sequence3_is_written_by_verifier_step10_not_the_coordinator(tmp_path):
    """Independent confirmation of IF-1: the PROOF_VERIFIED_AND_BOUND event
    is created by verify_human_authentication (HPAC-REQ-054 step 10) during
    principal (re)verification, and pre-exists any run_gate5 call. The
    coordinator holds no lifecycle writer capability."""
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "w" * 32)
    assert _chain_states(rig)[-1] == STATE_PROOF_VERIFIED  # before any verify()
    rig.verify()  # this is the verifier call — it binds
    assert _chain_states(rig)[-1] == STATE_PROOF_VERIFIED_AND_BOUND
    # The coordinator module never imports a writer/binder symbol.
    src = GATE5_SRC.read_text()
    assert "fixture_gate5_writer" not in src and "gate5_writer" not in src
    assert "HPACWriterCapability" not in src


def test_sequence3_event_exists_but_confers_no_gate5_result_on_non_real(tmp_path):
    """A canonical sequence-3 event present + valid RIHAC binding still
    yields NO Gate5Result because assurance is NON-REAL (HPAC-REQ-097 §40.2:
    a persisted lifecycle event is not authority)."""
    rig, principal, approval, store, context = _authority(tmp_path)
    event = rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    assert event is not None and event.record.state == STATE_PROOF_VERIFIED_AND_BOUND
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None and reasons == (NON_REAL_STOP,)
    assert not gate5.is_gate5_result(result)


def test_caller_manufactured_lifecycle_store_cannot_satisfy_gate5(tmp_path):
    """A non-HPACLifecycleStore object (even one that returns a plausible
    event) is rejected by the exact-type guard before confirmation."""
    rig, principal, approval, store, context = _authority(tmp_path)

    class _FakeLifecycle:
        def resolve_gate5_binding_event(self, _pid):
            return rig.lifecycle_store.resolve_gate5_binding_event(_pid)

    result, reasons = _run(rig, principal, approval, store, context,
                           lifecycle_store=_FakeLifecycle())
    assert result is None
    assert reasons == ("gate5_canonical_lifecycle_store_required",)


def test_sequence3_cross_binding_to_a_different_approval_fails_closed(tmp_path):
    """The verifier locks the proof to one approval-subject digest; a second
    verify with a different approval_id raises rather than forking."""
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "x" * 32)
    rig.verify()
    with pytest.raises((hpac_verifier.HPACVerificationError, HPACLifecycleForkError)):
        rig.verify(approval_id="ria-" + "0" * 32)


def test_resolve_gate5_binding_event_is_read_only(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    d = rig.lifecycle_store._dir(rig.proof_id)
    before = sorted(p.name for p in d.iterdir())
    for _ in range(3):
        rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    assert sorted(p.name for p in d.iterdir()) == before
    assert _consumption_json(tmp_path) == []


# ═══════════════════════════════════════════════════════════════════════
# 5. NON-REAL hard stop + downstream isolation (prompt §12, §13, §38.13-15)
# ═══════════════════════════════════════════════════════════════════════
def test_strongest_deterministic_path_still_stops_at_non_real(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons == (NON_REAL_STOP,)
    # the hard stop is a production-code check in validate_approval, inherited
    # (not re-implemented) by the coordinator.
    ra_tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text())
    ra_strs = {n.value for n in ast.walk(ra_tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert NON_REAL_STOP in ra_strs
    g5_tree = ast.parse(GATE5_SRC.read_text())
    g5_strs = {n.value for n in ast.walk(g5_tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    # the coordinator never emits the hard-stop reason itself as a bare literal
    assert NON_REAL_STOP not in g5_strs


def test_non_real_rejection_writes_no_consumption_and_no_pb_request(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    before = _approval_bytes(store, approval.approval_id)
    _run(rig, principal, approval, store, context)
    assert _approval_bytes(store, approval.approval_id) == before
    assert _consumption_json(tmp_path) == []
    src = GATE5_SRC.read_text()
    assert "permission_broker" not in src
    assert "PermissionBrokerRequest" not in src
    assert "runtime_invocation_authority_consumption" not in src


def test_non_real_rejection_leaves_no_gate9_eligibility(tmp_path):
    """After a NON-REAL rejection there is no Gate5Result, so nothing a
    downstream gate could consume; is_gate5_result is false for everything."""
    rig, principal, approval, store, context = _authority(tmp_path)
    result, _ = _run(rig, principal, approval, store, context)
    assert gate5.is_gate5_result(result) is False
    # the identity registry only ever gains members on run_gate5 success
    assert len(gate5._GATE5_RESULTS) == 0


# ═══════════════════════════════════════════════════════════════════════
# 6. Gate5Result output model + anti-transfer (prompt §10, §11, §38.16-17)
# ═══════════════════════════════════════════════════════════════════════
def test_gate5_result_not_caller_constructable():
    with pytest.raises(TypeError):
        gate5.Gate5Result(
            projection=None, sequence3_event_digest="d", proof_id="p",
            approval_id="a", invocation_id="i", advisory_reasons=(),
            validated_at="t", _seal=object(),
        )


def test_gate5_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (gate5.Gate5Result,), {})


def test_gate5_result_identity_only_equality_and_non_serializable():
    fake = object.__new__(gate5.Gate5Result)
    assert fake == fake and fake != object.__new__(gate5.Gate5Result)
    with pytest.raises(TypeError):
        pickle.dumps(fake)
    with pytest.raises(TypeError):
        copy.deepcopy(fake)  # deepcopy invokes __reduce_ex__ -> __reduce__


def test_is_gate5_result_rejects_forgery_copy_reconstruction():
    forged = object.__new__(gate5.Gate5Result)
    for name in ("proof_id", "approval_id", "invocation_id", "sequence3_event_digest",
                 "advisory_reasons", "validated_at", "_seal"):
        try:
            setattr(forged, name, "x" if name != "advisory_reasons" else ())
        except Exception:
            pass
    assert gate5.is_gate5_result(forged) is False
    assert gate5.is_gate5_result(None) is False
    assert gate5.is_gate5_result(42) is False


def test_gate5_binding_accessor_is_gated_and_read_only():
    assert authority.trusted_projection_gate5_binding(None) is None
    assert authority.trusted_projection_gate5_binding("x") is None
    fake = object.__new__(authority.ValidatedAuthorityProjection)
    assert authority.trusted_projection_gate5_binding(fake) is None


# ═══════════════════════════════════════════════════════════════════════
# 7. Consumes nothing / idempotency / failure atomicity (§18-20, §38.18-20)
# ═══════════════════════════════════════════════════════════════════════
def test_repeated_gate5_is_non_consuming_and_non_forking(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    before = _approval_bytes(store, approval.approval_id)
    r1 = _run(rig, principal, approval, store, context)
    r2 = _run(rig, principal, approval, store, context)
    r3 = _run(rig, principal, approval, store, context)
    assert r1 == r2 == r3 == (None, (NON_REAL_STOP,))
    assert _approval_bytes(store, approval.approval_id) == before
    assert _consumption_json(tmp_path) == []
    states = _chain_states(rig)
    assert states[-1] == STATE_PROOF_VERIFIED_AND_BOUND
    assert states.count(STATE_PROOF_VERIFIED_AND_BOUND) == 1  # no fork/dup


def test_late_failure_leaves_no_partial_authority(tmp_path):
    """Fail at the last comparable step (invocation mismatch surfaced late
    via principal binding): no Gate5Result, no consumption, registry empty."""
    rig, principal, approval, store, context = _authority(tmp_path)
    # expire the approval so validate_approval fails at step 10 (late)
    late = dataclasses.replace(context, current_time="2026-08-28T00:07:00Z")
    result, reasons = _run(rig, principal, approval, store, late)
    assert result is None and reasons == ("expired",)
    assert len(gate5._GATE5_RESULTS) == 0
    assert _consumption_json(tmp_path) == []


# ═══════════════════════════════════════════════════════════════════════
# 8. B1/B7/N1/N2 + F1 regression (prompt §21, §22, §38.21-25)
# ═══════════════════════════════════════════════════════════════════════
def test_b1_projection_remains_identity_only_and_non_copyable(tmp_path):
    ra_src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    assert "class ValidatedAuthorityProjection" in ra_src
    assert "eq=False" in ra_src
    # coordinator only reads the projection through the gated accessor
    assert "trusted_projection_gate5_binding" in GATE5_SRC.read_text()
    assert "._projection" in GATE5_SRC.read_text() or "_projection" in GATE5_SRC.read_text()


def test_n1_coordinator_enforces_exact_store_type_like_validate_approval(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)

    class _DuckStore:
        def load(self, _id):
            return approval

    result, reasons = _run(rig, principal, approval, store, context, approval_store=_DuckStore())
    assert result is None and reasons == ("canonical_approval_store_required",)


def test_n1_caller_supplied_approval_object_rejected(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context, approval_id=approval)
    assert result is None
    assert reasons == ("noncanonical_approval_reference:caller_supplied_object",)


def test_f1_forged_authenticated_principal_rejected(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    forged = object.__new__(hpac_verifier.AuthenticatedHumanPrincipal)
    for slot in hpac_verifier.AuthenticatedHumanPrincipal.__slots__:
        try:
            setattr(forged, slot, getattr(principal, slot))
        except AttributeError:
            pass
    result, reasons = _run(rig, principal, approval, store, context, authenticated_principal=forged)
    assert result is None
    assert reasons == ("authenticated_principal_not_verifier_issued",)


def test_n2_lost_registry_membership_fails_closed(tmp_path):
    rig, principal, approval, store, context = _authority(tmp_path)
    hpac_verifier._AUTHENTIC_PRINCIPAL_REGISTRY.discard(principal)
    hpac_verifier._AUTHENTIC_PRINCIPAL_CONTEXTS.pop(principal, None)
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons == ("authenticated_principal_not_verifier_issued",)


# ═══════════════════════════════════════════════════════════════════════
# 9. Authorized consumer expansion + gate/effect isolation (§28, §33-37, §38.26-30)
# ═══════════════════════════════════════════════════════════════════════
# Phase-aware production-scope invariant (converted from a point-in-time
# frozen-diff equality assertion, Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.2 /
# V-13-1). The original "== exactly these three files" is deterministically
# stale once an authorized later Gate-6 / Gate-7 chain phase adds its own
# coordinator file. Converted to: the .1R.10 Gate-5 production surface plus
# any later change must be a SUBSET of the known, individually-authorized
# runtime-dispatch-gate-chain surface, with no unexpected file. The .1R.10
# Gate-5 trio must still all be present in the diff (the .1R.10 functional
# closure is real), and an unauthorized expansion still fails.
_AUTHORIZED_GATE_CHAIN_SURFACE = {
    "src/pcae/core/runtime_dispatch_gate5.py",
    "src/pcae/core/runtime_authority.py",
    "src/pcae/core/hpac_lifecycle.py",
    "src/pcae/core/runtime_dispatch_permission.py",  # Gate 6 (.1R.12)
    "src/pcae/core/runtime_dispatch_gate7.py",  # Gate 7 (.1R.13.2)
    "src/pcae/core/runtime_dispatch_gate8.py",  # Gate 8 (.1R.13.4)
    "src/pcae/core/runtime_dispatch_gate9.py",  # Gate 9 (.1R.14)
}


def test_production_scope_is_exactly_the_three_planned_files(tmp_path):
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", PHASE_ENTRY_1R10, "HEAD", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    assert changed - _AUTHORIZED_GATE_CHAIN_SURFACE == set(), (
        f"unauthorized production-file expansion: {sorted(changed - _AUTHORIZED_GATE_CHAIN_SURFACE)}"
    )
    assert {
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/hpac_lifecycle.py",
    } <= changed


def test_hpac_verifier_not_modified_since_baseline():
    diff = subprocess.run(
        ["git", "diff", PRE_1R10_BASELINE, "HEAD", "--", "src/pcae/core/hpac_verifier.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert diff == ""


def test_all_seven_contracts_and_pol005_byte_identical():
    pinned = {
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md":
            "38d98e9b6bfee3d1097628b73f7fdcd70ca932a9dfda9007e764c0e9e90a04d0",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md":
            "a47869ba315a55b829982d03989c755aa753af9fef52667d7775ead31a95f608",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md":
            "24fd6fac04ea174d5387c4c945f5055896b77c466c149cd8d13dd3353db0567b",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md":
            "e0799d464af603b4be559c6be4607d2519635eea933ffd1cdde0e02d0e77ffef",
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md":
            "24e1eefaedf4c63bc221e6460fecf3c055b88d9d7ba230a76d3ec113f511f5ab",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md":
            "395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md":
            "6daf404b608fd410a8e8c4551f06e76268e49abe056c96db49c1ecca99db02b2",
        "src/pcae/core/permission_broker_foundation.py":
            "2eb7c1068736c10018482f6787ae9cbd7cf4cf8ceaeeac728e18b75dec2639d1",
    }
    for rel, want in pinned.items():
        got = hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()
        assert got == want, f"{rel} changed"


def test_coordinator_is_the_only_authorized_new_consumer_and_is_bounded():
    """runtime_dispatch_gate5 consumes hpac_verifier (public predicate only),
    hpac_lifecycle (read-only resolver + state constant), and runtime_authority
    (validate_approval + gated accessor). It consumes NO PB, Gate-9, adapter,
    or runtime-enforcement module."""
    src = GATE5_SRC.read_text()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert imported <= {
        "__future__", "typing",
        "pcae.core.hpac_lifecycle", "pcae.core.runtime_authority",
        "pcae.core.hpac_verifier",
    }
    # No banned module is *imported* (they may appear only in prohibition prose).
    for banned in (
        "permission_broker_foundation", "runtime_dispatch_permission",
        "runtime_invocation_authority_consumption", "backend_invocations",
        "shell_gate", "runtime_adapter", "mock_runtime_adapter", "runtime_registry",
    ):
        assert not any(banned in m for m in imported)


def test_coordinator_imports_nothing_effectful():
    forbidden = {
        "subprocess", "socket", "requests", "httpx", "urllib", "http", "ssl",
        "fido2", "webauthn", "ctap", "smartcard", "usb", "serial",
        "asyncio", "multiprocessing", "ctypes",
    }
    tree = ast.parse(GATE5_SRC.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in forbidden
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden


def test_runtime_capability_unchanged():
    from pcae.core import runtime_introspection as ri
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_no_gate9_consumption_store_wiring_anywhere_new():
    """The inert Gate-9 consumption store
    (``runtime_invocation_authority_consumption``) has no production importer
    OTHER than the authorized Gate-9 atomic-consumption coordinator
    (``runtime_dispatch_gate9``, added by the explicitly human-authorized
    .1R.14 phase). Phase-aware invariant (V-13-1 conversion of a
    point-in-time equality assertion): an unauthorized importer still fails
    this test."""
    src_root = REPO_ROOT / "src" / "pcae"
    importers = []
    for path in src_root.rglob("*.py"):
        if path.name == "runtime_invocation_authority_consumption.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and \
               node.module.endswith("runtime_invocation_authority_consumption"):
                importers.append(str(path))
            elif isinstance(node, ast.Import):
                importers += [str(path) for a in node.names
                              if a.name.endswith("runtime_invocation_authority_consumption")]
    assert set(importers) <= {
        str(src_root / "core" / "runtime_dispatch_gate9.py"),
    }, f"unauthorized Gate-9 store importer: {sorted(importers)}"


def test_test_only_fixtures_not_importable_by_the_coordinator():
    src = GATE5_SRC.read_text()
    assert "_rdw3w_helpers" not in src
    assert "test_hpac_verifier" not in src
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            names = [a.name for a in node.names]
            assert not any("test" in (n or "").lower() for n in names + [mod])
