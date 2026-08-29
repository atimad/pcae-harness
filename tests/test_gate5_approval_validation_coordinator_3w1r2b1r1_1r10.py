"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.10 — Gate-5 Approval-Validation
Coordinator Integration Implementation.

Focused defensive tests for the new ``runtime_dispatch_gate5`` coordinator.
Constructed from the primary contracts (RDGO-001 v3.0 §6, RIHAC-001 v2.0
§16, HPAC-001 v2.0 HPAC-REQ-054/097, PBRD-001 v2.0, POL-005) and current
production source, not from a report or test names.

The deterministic HPAC mechanism is permanently NON-REAL: no production
assurance mechanism exists. There is therefore **no legitimate positive
Gate-5 success** to construct without real FIDO2/UI, and this suite does
not manufacture one (`.1R.9` §41). Every case is rejection-only or
structural, up to and including the Option-A NON-REAL hard stop, which the
coordinator inherits from ``validate_approval`` and never re-implements.
"""

from __future__ import annotations

import ast
import copy
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import hpac_verifier
from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core.hpac_lifecycle import HPACLifecycleStore, STATE_PROOF_VERIFIED_AND_BOUND
from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore

from _rdw3w_helpers import always_unconsumed, construct_test_only_deterministic_approval, matching_context
from test_hpac_verifier import NOW, _Rig

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY_BASELINE = "1810c8d8d1d10ad5dc3cb0743dc0c20c71180ca5"
NON_REAL_STOP = "non_real_authenticated_principal_cannot_validate_production_approval"


# ─────────────────────────────────────────────────────────────────────────
# Shared fixture: a canonical persisted approval whose deterministic HPAC
# chain verifies structurally at NON-REAL assurance.
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


def _run(rig, principal, approval, store, context, **overrides):
    kwargs = dict(
        approval_store=store,
        authenticated_principal=principal,
        context=context,
        consumption_lookup=always_unconsumed,
        lifecycle_store=rig.lifecycle_store,
    )
    kwargs.update(overrides)
    return gate5.run_gate5(overrides.get("approval_id", approval.approval_id), **{
        k: v for k, v in kwargs.items() if k != "approval_id"
    })


def _approval_bytes(store, approval_id):
    return store.load(approval_id).to_dict()


def _consumption_paths(root: Path):
    return list(root.rglob("consumption.json"))


# ═══════════════════════════════════════════════════════════════════════
# 1. Layered battery runs and stops at the inherited NON-REAL boundary
# ═══════════════════════════════════════════════════════════════════════
def test_canonical_authority_runs_full_battery_and_stops_at_non_real(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons == (NON_REAL_STOP,)
    assert not gate5.is_gate5_result(result)


def test_non_real_rejection_yields_no_result_and_consumes_nothing(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    before = _approval_bytes(store, approval.approval_id)
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None and reasons == (NON_REAL_STOP,)
    assert _approval_bytes(store, approval.approval_id) == before
    assert _consumption_paths(tmp_path) == []


def test_non_real_path_produces_no_gate9_and_no_pb_decision(tmp_path):
    # The coordinator module imports nothing that can evaluate PB policy or
    # write a Gate-9 consumption record, and the NON-REAL path never even
    # reaches a projection.
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    _run(rig, principal, approval, store, context)
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py").read_text()
    assert "permission_broker" not in src
    assert "runtime_invocation_authority_consumption" not in src
    assert "consumption.json" in src  # only named in a prohibition comment
    assert _consumption_paths(tmp_path) == []


# ═══════════════════════════════════════════════════════════════════════
# 2. HPAC-REQ-097 sequence-3 confirmation (coordinator ownership)
# ═══════════════════════════════════════════════════════════════════════
def test_sequence3_event_is_present_after_reverification_but_grants_no_result(tmp_path):
    # IF-1: the verifier's HPAC-REQ-054 step 10 creates PROOF_VERIFIED_AND_BOUND
    # while it reverifies the principal (assurance-independent). The
    # coordinator still returns fail-closed at NON-REAL: a persisted
    # lifecycle event is not authority (HPAC-REQ-097 / §40.2).
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    _run(rig, principal, approval, store, context)
    event = rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    assert event is not None
    assert event.record.state == STATE_PROOF_VERIFIED_AND_BOUND
    assert event.record.binding["approval_id"] == approval.approval_id
    assert event.record.binding["invocation_id"] == context.invocation_id


def test_resolve_gate5_binding_event_is_none_before_binding(tmp_path):
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "b" * 32)
    # chain is at PROOF_VERIFIED, not yet bound
    assert rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id) is None
    assert rig.lifecycle_store.resolve_gate5_binding_event("hap-" + "0" * 32) is None


def test_resolve_gate5_binding_event_creates_and_consumes_nothing(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    _run(rig, principal, approval, store, context)
    before = sorted(p.name for p in (rig.lifecycle_store._dir(rig.proof_id)).iterdir())
    rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    after = sorted(p.name for p in (rig.lifecycle_store._dir(rig.proof_id)).iterdir())
    assert before == after
    assert _consumption_paths(tmp_path) == []


# ═══════════════════════════════════════════════════════════════════════
# 3. Provenance: caller-produced / forged / copied principals
# ═══════════════════════════════════════════════════════════════════════
def test_forged_authenticated_principal_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    forged = object.__new__(hpac_verifier.AuthenticatedHumanPrincipal)
    for slot in hpac_verifier.AuthenticatedHumanPrincipal.__slots__:
        try:
            setattr(forged, slot, getattr(principal, slot))
        except AttributeError:
            pass
    result, reasons = _run(rig, principal, approval, store, context,
                           authenticated_principal=forged)
    assert result is None
    assert reasons == ("authenticated_principal_not_verifier_issued",)


def test_copied_principal_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    with pytest.raises(TypeError):
        copy.deepcopy(principal)  # __reduce__ raises
    result, reasons = _run(rig, principal, approval, store, context,
                           authenticated_principal=None)
    assert result is None
    assert reasons == ("authenticated_principal_not_verifier_issued",)


def test_lost_registry_membership_simulated_restart_fails_closed(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    hpac_verifier._AUTHENTIC_PRINCIPAL_REGISTRY.discard(principal)
    hpac_verifier._AUTHENTIC_PRINCIPAL_CONTEXTS.pop(principal, None)
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons == ("authenticated_principal_not_verifier_issued",)


# ═══════════════════════════════════════════════════════════════════════
# 4. Canonical approval resolution (N1 discipline, inherited)
# ═══════════════════════════════════════════════════════════════════════
def test_missing_canonical_approval_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context,
                           approval_id="ria-" + "9" * 32)
    assert result is None
    assert reasons == ("no_valid_approval:missing_or_unresolvable",)


def test_caller_supplied_approval_object_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context,
                           approval_id=approval)
    assert result is None
    assert reasons == ("noncanonical_approval_reference:caller_supplied_object",)


def test_lookalike_approval_store_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)

    class _FakeStore:
        def load(self, _id):
            return approval

    result, reasons = _run(rig, principal, approval, store, context,
                           approval_store=_FakeStore())
    assert result is None
    assert reasons == ("canonical_approval_store_required",)


# ═══════════════════════════════════════════════════════════════════════
# 5. Substitution / stale-state / mismatch (fail closed)
# ═══════════════════════════════════════════════════════════════════════
def test_invocation_substitution_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    import dataclasses
    other_context = dataclasses.replace(context, invocation_id="inv-" + "c" * 32)
    result, reasons = _run(rig, principal, approval, store, other_context)
    assert result is None
    assert reasons == ("subject_mismatch:invocation_id",)


def test_expired_approval_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    import dataclasses
    expired_ctx = dataclasses.replace(context, current_time="2026-08-28T00:05:00Z")
    result, reasons = _run(rig, principal, approval, store, expired_ctx)
    assert result is None
    assert reasons == ("expired",)


@pytest.mark.parametrize("what", ["principal", "credential"])
def test_revocation_after_authentication_fails_closed(tmp_path, what):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    if what == "principal":
        rig.registry.revoke_principal(admin, principal_id=rig.principal_id,
                                      revoked_at="2026-08-28T00:02:30Z")
    else:
        rig.registry.revoke_credential(admin, credential_id=rig.credential_id,
                                       revoked_at="2026-08-28T00:02:30Z")
    result, reasons = _run(rig, principal, approval, store, context)
    assert result is None
    assert reasons[0].startswith("authenticated_principal_reverification_failed")


def test_substituted_self_consistent_challenge_never_yields_a_principal(tmp_path):
    # HPAC-REQ-054 Step 4: a self-consistent substituted challenge is
    # rejected during verification, so no verifier-issued principal exists
    # and the coordinator fails closed on provenance.
    import dataclasses
    rig = _Rig(tmp_path / "hpac", invocation_id="inv-" + "d" * 32)
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
    changed = dataclasses.replace(changed, challenge_digest=hpac_verifier.canonical_digest(body))
    with pytest.raises(hpac_verifier.HPACVerificationError):
        rig.verify(challenge=changed)


def test_wrong_lifecycle_store_type_is_rejected(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    result, reasons = _run(rig, principal, approval, store, context,
                           lifecycle_store=object())
    assert result is None
    assert reasons == ("gate5_canonical_lifecycle_store_required",)


# ═══════════════════════════════════════════════════════════════════════
# 6. Repeatability — Gate 5 consumes nothing
# ═══════════════════════════════════════════════════════════════════════
def test_repeated_gate5_consumes_nothing(tmp_path):
    rig, principal, approval, store, context = _canonical_authority(tmp_path)
    before = _approval_bytes(store, approval.approval_id)
    first = _run(rig, principal, approval, store, context)
    second = _run(rig, principal, approval, store, context)
    assert first == second == (None, (NON_REAL_STOP,))
    assert _approval_bytes(store, approval.approval_id) == before
    assert _consumption_paths(tmp_path) == []
    # sequence-3 remains a single same-binding event (idempotent)
    events = rig.lifecycle_store.resolve_chain(rig.proof_id)
    assert [e.state for e in events][-1] == STATE_PROOF_VERIFIED_AND_BOUND
    assert sum(1 for e in events if e.state == STATE_PROOF_VERIFIED_AND_BOUND) == 1


# ═══════════════════════════════════════════════════════════════════════
# 7. Gate5Result type discipline (ephemeral, non-transferable)
# ═══════════════════════════════════════════════════════════════════════
def test_gate5_result_cannot_be_caller_constructed():
    with pytest.raises(TypeError):
        gate5.Gate5Result(
            projection=None, sequence3_event_digest="x", proof_id="p",
            approval_id="a", invocation_id="i", advisory_reasons=(),
            validated_at="t", _seal=object(),
        )


def test_gate5_result_cannot_be_subclassed():
    with pytest.raises(TypeError):
        type("Evil", (gate5.Gate5Result,), {})


def test_is_gate5_result_rejects_forgeries_and_copies():
    fake = object.__new__(gate5.Gate5Result)
    assert gate5.is_gate5_result(fake) is False
    assert gate5.is_gate5_result(None) is False
    assert gate5.is_gate5_result("x") is False


def test_gate5_result_is_non_serializable():
    fake = object.__new__(gate5.Gate5Result)
    with pytest.raises(TypeError):
        pickle.dumps(fake)


# ═══════════════════════════════════════════════════════════════════════
# 8. Isolation / no-external-effect / regression attribution
# ═══════════════════════════════════════════════════════════════════════
_FORBIDDEN_IMPORT_ROOTS = {
    "subprocess", "socket", "requests", "httpx", "urllib", "http",
    "fido2", "webauthn", "ctap", "smartcard", "usb", "serial", "ssl",
    "asyncio", "multiprocessing", "ctypes",
}


def test_new_coordinator_module_imports_nothing_effectful():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS


def test_test_only_fixture_not_importable_by_production():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            names = [a.name for a in node.names]
            assert "_rdw3w_helpers" not in mod and "_rdw3w_helpers" not in names
            assert not any("test" in (n or "").lower() for n in names + [mod])


# ─────────────────────────────────────────────────────────────────────────
# Phase-aware production-scope invariant (converted from a point-in-time
# frozen-diff assertion, Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.2 / V-13-1).
#
# The original assertion pinned "exactly / at most these three files changed
# since the .1R.10 entry SHA". That is deterministically stale the moment
# any *authorized* later phase in the same runtime-dispatch-gate chain adds
# its own coordinator file (.1R.12 added runtime_dispatch_permission.py;
# .1R.13.2 adds runtime_dispatch_gate7.py). Rather than permanently freeze a
# red diff or delete the assertion, it is converted to an invariant: the
# production surface touched since the .1R.10 baseline must be a SUBSET of
# the known, individually-authorized Gate-5..7 runtime-dispatch-chain
# surface, and NO file outside that authorized set may have changed. An
# unauthorized production-file expansion still fails this test.
# ─────────────────────────────────────────────────────────────────────────
_AUTHORIZED_RUNTIME_DISPATCH_CHAIN_SURFACE = {
    # Gate 5 (.1R.10) — new coordinator + its two read-only accessors
    "src/pcae/core/runtime_dispatch_gate5.py",
    "src/pcae/core/runtime_authority.py",
    "src/pcae/core/hpac_lifecycle.py",
    # Gate 6 (.1R.12) — coordinator appended to the trusted builder module
    "src/pcae/core/runtime_dispatch_permission.py",
    # Gate 7 (.1R.13.2) — new coordinator module
    "src/pcae/core/runtime_dispatch_gate7.py",
}


def test_only_expected_production_files_changed_since_baseline():
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    unexpected = changed - _AUTHORIZED_RUNTIME_DISPATCH_CHAIN_SURFACE
    assert unexpected == set(), (
        "unauthorized production-file expansion since the .1R.10 baseline: "
        f"{sorted(unexpected)}"
    )


def test_contracts_and_pol005_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
    ):
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == "", f"{rel} changed since baseline"
    pbf_src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    assert 'policy_id = "POL-005"' in pbf_src or '"POL-005"' in pbf_src


def test_runtime_state_remains_unavailable():
    from pcae.core import runtime_introspection as ri
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_runtime_authority_hook_is_read_only_and_gated():
    # trusted_projection_gate5_binding returns None for anything not a
    # registry-provenanced projection.
    assert authority.trusted_projection_gate5_binding(None) is None
    assert authority.trusted_projection_gate5_binding("x") is None
    fake = object.__new__(authority.ValidatedAuthorityProjection)
    assert authority.trusted_projection_gate5_binding(fake) is None
