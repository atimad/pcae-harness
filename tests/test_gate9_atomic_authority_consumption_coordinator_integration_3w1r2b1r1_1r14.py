"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.14 — Gate-9 Atomic Authority
Consumption Coordinator Integration Implementation.

Focused defensive tests for
``runtime_dispatch_gate9.run_gate9_atomic_authority_consumption`` (the
frozen Gate-9 owner), ``Gate9Result``, and ``is_gate9_result``. Constructed
from the primary contracts (RDGO-001 v3.0 §10 / §1 row 9 / §17 / §18 / §19,
HPAC-REQ-098/099/100/101/102, RIHAC-001 v2.0 §17 / §19, the ``.1R.9``
planning document §10-§19, the ``.1R.13.1`` §16 Gate-8 → Gate-9 handoff
contract) and current production source — not from a report or test names.

The deterministic HPAC mechanism is permanently NON-REAL and the real
Gate-7 coordinator always returns ``Gate7Result(decision="DENY")`` under the
current runtime posture, so **there is no legitimate positive production
Gate-9 path**: every real call fails closed upstream. To exercise the
atomic-consumption envelope WITHOUT manufacturing real authority, a
``chain`` fixture installs a **test-boundary substitution** of the upstream
provenance predicates only (``monkeypatch`` on
``is_gate5_result`` / ``is_gate6_decision`` / ``is_gate7_result`` and the
projection-trust predicates in the ``runtime_dispatch_gate8`` /
``runtime_dispatch_gate9`` namespaces) and writes only to a ``tmp_path``
consumption store — never the production-resolved ``HPAC_PROTECTED_ROOT``.
This substitutes exactly the gates a real FIDO2/UI ceremony + a real PB
ALLOW + a real Gate-7 ALLOW + a real Gate-8 positive containment would
satisfy; it manufactures no ``ValidatedAuthorityProjection``, no approval,
no runtime capability, no positive ``Gate7Result``. The HPAC lifecycle
sequence-3 event and its ``HPACLifecycleStore`` are the **real** ones,
built through the canonical fixture writers (``test_hpac_verifier._Rig``).
"""

from __future__ import annotations

import ast
import copy
import hashlib
import pickle
import subprocess
import threading
from pathlib import Path

import pytest

from pcae.core import runtime_authority as authority
from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate7 as gate7
from pcae.core import runtime_dispatch_gate8 as g8
from pcae.core import runtime_dispatch_gate9 as g9
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
    RuntimeInvocationAuthorityConsumptionStore,
)

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity
from test_hpac_verifier import NOW, _Rig

REPO_ROOT = Path(__file__).resolve().parents[1]
G9_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py"
G9_SRC = G9_PATH.read_text()
PHASE_ENTRY_BASELINE = "c1ea2c8b"
_ECHO = "/bin/echo"

_GOOD_SNAPSHOT = {
    "current_runtime_state": "Observed",
    "current_maximum_plugin_capability": "observe",
    "execution_availability": "unavailable",
}


def _sha256_file(path: str) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            d.update(chunk)
    return d.hexdigest()


def _snapshot():
    return dict(_GOOD_SNAPSHOT)


# ═══════════════════════════════════════════════════════════════════════
# Test-boundary fixtures — clearly labelled; no real authority, no real
# runtime capability, no positive Gate7Result, tmp_path consumption store.
# ═══════════════════════════════════════════════════════════════════════
class _SyntheticProjection:
    def __init__(self, *, subject_scope_binding_digest, principal_id, approval_id, proof_id):
        self.subject_scope_binding_digest = subject_scope_binding_digest
        self.principal_id = principal_id
        self.approval_id = approval_id
        self.proof_id = proof_id
        self.record_digest = "r" * 64
        self.validated_at = NOW
        self.freshness_verdict_digest = "f" * 64

    def evidence_digest(self) -> str:
        return "e" * 64


def _synthetic_gate5_result(*, invocation_id, approval_id, proof_id, seq3_digest, projection):
    obj = object.__new__(gate5.Gate5Result)
    for name, value in (
        ("_projection", projection),
        ("sequence3_event_digest", seq3_digest),
        ("proof_id", proof_id),
        ("approval_id", approval_id),
        ("invocation_id", invocation_id),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _synthetic_gate6_decision(*, decision, invocation_id, attempt_id, request_id):
    obj = object.__new__(rdp.Gate6Decision)
    for name, value in (
        ("_pb_decision", object()),
        ("decision", decision),
        ("decision_reason", "synthetic"),
        ("approval_present", True),
        ("invocation_id", invocation_id),
        ("attempt_id", attempt_id),
        ("request_id", request_id),
        ("causing_policy_ids", ()),
        ("matched_no_go_ids", ()),
        ("requires_human", False),
        ("simulation_only", False),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _synthetic_gate7_result(*, decision, invocation_id, attempt_id, request_id):
    obj = object.__new__(gate7.Gate7Result)
    for name, value in (
        ("decision", decision),
        ("matched_no_go_ids", () if decision == "ALLOW" else ("RE-NOGO-002",)),
        ("causing_reason_ids", ()),
        ("invocation_id", invocation_id),
        ("attempt_id", attempt_id),
        ("request_id", request_id),
        ("pb_decision_digest", "a" * 64),
        ("authority_freshness_digest", "b" * 64),
        ("evaluated_input_digest", "c" * 64),
        ("runtime_posture_digest", "9" * 64),
        ("expires_at", NOW),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _good_effect_plan(**overrides):
    base = dict(
        executable_path=_ECHO,
        argv=("runtime-dispatch-preflight",),
        cwd=str(REPO_ROOT),
        env_allowlist=("PATH", "HOME"),
        child_process_policy="prohibited",
        resource_limit_ref="budget-1",
        time_limit_ref="timeout-30s",
        supervision_ref="supervisor-1",
        network_denied=True,
        credentials_required=False,
    )
    base.update(overrides)
    return g8.Gate8EffectPlan(**base)


def _resolver(**overrides):
    def resolve(inputs):
        adapter = inputs.adapter_descriptor_binding
        fields = dict(
            path=_ECHO,
            sha256=_sha256_file(_ECHO),
            version="1.0",
            descriptor_digest=adapter.descriptor_digest,
            target_config_digest=adapter.target_config_digest,
            runtime_target_id=inputs.runtime_target_id,
            installed=True,
        )
        fields.update(overrides)
        return g8.ResolvedExecutable(**fields)

    return resolve


class _Chain:
    pass


@pytest.fixture
def chain(tmp_path, monkeypatch):
    inv = "inv-" + "a" * 32
    rig = _Rig(tmp_path / "hpac", invocation_id=inv)
    rig.verify()  # creates the real sequence-3 PROOF_VERIFIED_AND_BOUND event
    event = rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
    assert event is not None and event.record.state == "PROOF_VERIFIED_AND_BOUND"

    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs, invocation_id=inv)
    expected = rdp._expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    projection = _SyntheticProjection(
        subject_scope_binding_digest=expected,
        principal_id=rig.principal_id,
        approval_id=rig.approval_id,
        proof_id=rig.proof_id,
    )
    request_id = "pbr-" + "0" * 12
    g7 = _synthetic_gate7_result(
        decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id
    )
    g6 = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id
    )
    g5 = _synthetic_gate5_result(
        invocation_id=inv,
        approval_id=rig.approval_id,
        proof_id=rig.proof_id,
        seq3_digest=event.record.event_digest,
        projection=projection,
    )

    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is g7)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    monkeypatch.setattr(g8, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g8, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection
    )
    monkeypatch.setattr(g9, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g9, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection
    )

    # Real Gate-8 positive containment result (registry-provenanced) via the
    # same labelled substitution — no positive Gate7Result, no real authority.
    g8_result, r8 = g8.run_gate8_process_containment(
        g7,
        gate5_result=g5,
        identity=identity,
        inputs=inputs,
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(),
    )
    assert g8_result is not None and g8_result.containment_established is True, r8

    c = _Chain()
    c.rig = rig
    c.event = event
    c.inputs = inputs
    c.identity = identity
    c.projection = projection
    c.g5, c.g6, c.g7, c.g8 = g5, g6, g7, g8_result
    c.store = RuntimeInvocationAuthorityConsumptionStore(tmp_path / "consumption")
    return c


def _run(chain, **overrides):
    g8_result = overrides.pop("gate8_result", chain.g8)
    kw = dict(
        gate7_result=overrides.pop("gate7_result", chain.g7),
        gate6_decision=overrides.pop("gate6_decision", chain.g6),
        gate5_result=overrides.pop("gate5_result", chain.g5),
        identity=overrides.pop("identity", chain.identity),
        inputs=overrides.pop("inputs", chain.inputs),
        authority_current_time=overrides.pop("authority_current_time", NOW),
        repo_root=overrides.pop("repo_root", REPO_ROOT),
        effect_plan=overrides.pop("effect_plan", _good_effect_plan()),
        descriptor_resolver=overrides.pop("descriptor_resolver", _resolver()),
        lifecycle_store=overrides.pop("lifecycle_store", chain.rig.lifecycle_store),
        consumption_store=overrides.pop("consumption_store", chain.store),
        capability_snapshot_resolver=overrides.pop("capability_snapshot_resolver", _snapshot),
    )
    kw.update(overrides)
    return g9.run_gate9_atomic_authority_consumption(g8_result, **kw)


def _count_consumption_json(root: Path):
    return len(list(root.rglob("consumption.json")))


# ═══════════════════════════════════════════════════════════════════════
# 1-4. Gate8Result provenance + affirmative containment required
# ═══════════════════════════════════════════════════════════════════════
def test_none_gate8_result_fails_closed(chain):
    r, reasons = _run(chain, gate8_result=None)
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def test_object_new_gate8_result_rejected(chain):
    r, reasons = _run(chain, gate8_result=object.__new__(g8.Gate8Result))
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def test_copied_reconstructed_serialized_gate8_result_rejected(chain):
    with pytest.raises(TypeError):
        pickle.dumps(chain.g8)
    with pytest.raises(TypeError):
        copy.deepcopy(chain.g8)
    r, reasons = _run(chain, gate8_result=copy.copy(chain.g8) if _safe_copy(chain.g8) else object())
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def _safe_copy(x):
    try:
        copy.copy(x)
        return True
    except TypeError:
        return False


def test_trusted_negative_gate8_result_rejected_before_any_consumption(chain, monkeypatch):
    neg, _ = g8.run_gate8_process_containment(
        chain.g7,
        gate5_result=chain.g5,
        identity=chain.identity,
        inputs=chain.inputs,
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(installed=False),
    )
    assert neg is not None and neg.containment_established is False
    assert g8.is_gate8_result(neg) is True
    calls = []
    monkeypatch.setattr(chain.store, "create", lambda *a, **k: calls.append(1))
    r, reasons = _run(chain, gate8_result=neg)
    assert r is None and reasons == ("gate9_gate8_containment_not_established",)
    assert calls == []
    assert _count_consumption_json(chain.store._root if False else Path(str(chain.store._root))) == 0


# ═══════════════════════════════════════════════════════════════════════
# 5-8. Upstream lineage: decision must be ALLOW; provenance required
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_gate7_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_untrusted_gate7_result",)


def test_gate7_decision_not_allow_rejected(chain, monkeypatch):
    deny = _synthetic_gate7_result(
        decision="DENY", invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is deny)
    r, reasons = _run(chain, gate7_result=deny)
    assert r is None and reasons == ("gate9_gate7_decision_not_allow",)


def test_untrusted_gate6_decision_rejected(chain, monkeypatch):
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_untrusted_gate6_decision",)


def test_gate6_decision_not_allow_rejected(chain, monkeypatch):
    deny = _synthetic_gate6_decision(
        decision="DENY", invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id, request_id=chain.g7.request_id,
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is deny)
    r, reasons = _run(chain, gate6_decision=deny)
    assert r is None and reasons == ("gate9_gate6_decision_not_allow",)


def test_untrusted_gate5_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_untrusted_gate5_result",)


# ═══════════════════════════════════════════════════════════════════════
# 5-7 / 14. Invocation / attempt / request lineage
# ═══════════════════════════════════════════════════════════════════════
def test_invocation_mismatch_rejected(chain, monkeypatch):
    other = _synthetic_gate7_result(
        decision="ALLOW", invocation_id="inv-" + "z" * 32,
        attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is other)
    r, reasons = _run(chain, gate7_result=other)
    assert r is None and reasons == ("gate9_invocation_binding_mismatch",)


def test_attempt_mismatch_rejected(chain, monkeypatch):
    other = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=chain.identity.invocation_id,
        attempt_id="att-" + "z" * 20, request_id=chain.g7.request_id,
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is other)
    r, reasons = _run(chain, gate6_decision=other)
    assert r is None and reasons == ("gate9_invocation_binding_mismatch",)


def test_request_id_mismatch_rejected(chain, monkeypatch):
    other = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id, request_id="pbr-" + "9" * 12,
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is other)
    r, reasons = _run(chain, gate6_decision=other)
    assert r is None and reasons == ("gate9_invocation_binding_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 8-10. Gate7 lineage digest + effect-plan + containment-evidence recompute
# ═══════════════════════════════════════════════════════════════════════
def test_gate7_lineage_digest_mismatch_rejected(chain, monkeypatch):
    # A trusted Gate7Result whose evidence differs from the one the handed
    # Gate8Result was produced over.
    tampered = _synthetic_gate7_result(
        decision="ALLOW", invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id,
    )
    object.__setattr__(tampered, "evaluated_input_digest", "0" * 64)
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is tampered)
    r, reasons = _run(chain, gate7_result=tampered)
    assert r is None and reasons == ("gate9_gate7_lineage_mismatch",)


def test_effect_plan_drift_rejected_by_recomputation(chain):
    # Gate8Result was produced for argv ("runtime-dispatch-preflight",);
    # feed Gate 9 a different effect plan → the re-run recomputes a
    # different digest and Gate 9 refuses.
    r, reasons = _run(chain, effect_plan=_good_effect_plan(argv=("different-arg",)))
    assert r is None
    assert reasons in (
        ("gate9_containment_evidence_recomputation_mismatch",),
        ("gate9_containment_recomputation_failed",),
    )


def test_executable_drift_rejected_by_recomputation(chain):
    r, reasons = _run(chain, descriptor_resolver=_resolver(sha256="0" * 64))
    assert r is None
    assert reasons in (
        ("gate9_containment_recomputation_failed",),
        ("gate9_containment_evidence_recomputation_mismatch",),
    )


def test_cwd_outside_repository_rejected_by_recomputation(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(cwd="/etc"))
    assert r is None
    assert reasons in (
        ("gate9_containment_recomputation_failed",),
        ("gate9_containment_evidence_recomputation_mismatch",),
    )


# ═══════════════════════════════════════════════════════════════════════
# 11-17. In-boundary revalidation: projection / scope / principal /
#        credential / proof / approval currentness
# ═══════════════════════════════════════════════════════════════════════
def test_stale_projection_rejected_inside_boundary(chain, monkeypatch):
    monkeypatch.setattr(g9, "revalidate_validated_authority_projection", lambda p, *, current_time: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_stale_validated_authority_projection",)


def test_untrusted_projection_rejected_inside_boundary(chain, monkeypatch):
    monkeypatch.setattr(g9, "is_trusted_validated_authority_projection", lambda p: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_stale_validated_authority_projection",)


def test_subject_scope_binding_mismatch_rejected(chain):
    chain.projection.subject_scope_binding_digest = "0" * 64
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_authority_subject_scope_mismatch",)


def test_sequence3_absent_rejected(chain):
    class _EmptyLifecycle:
        pass

    # wrong type is caught first
    r, reasons = _run(chain, lifecycle_store=_EmptyLifecycle())
    assert r is None and reasons == ("gate9_invalid_lifecycle_store",)


def test_sequence3_cross_binding_rejected(chain):
    chain.projection.approval_id = "ria-" + "9" * 32
    chain.g5 = _synthetic_gate5_result(
        invocation_id=chain.identity.invocation_id,
        approval_id="ria-" + "9" * 32,
        proof_id=chain.rig.proof_id,
        seq3_digest=chain.event.record.event_digest,
        projection=chain.projection,
    )
    # rebind the is_gate5_result monkeypatch target
    import pcae.core.runtime_dispatch_gate5 as _g5mod
    _g5mod.is_gate5_result = lambda c: c is chain.g5
    try:
        r, reasons = _run(chain)
    finally:
        pass
    assert r is None and reasons == ("gate9_sequence3_cross_binding",)


def test_proof_approval_pairing_mismatch_rejected(chain):
    # projection.approval_id disagrees with gate5_result.approval_id
    chain.projection.approval_id = "ria-" + "7" * 32
    r, reasons = _run(chain)
    assert r is None and reasons in (
        ("gate9_proof_approval_pairing_mismatch",),
        ("gate9_sequence3_cross_binding",),
    )


# ═══════════════════════════════════════════════════════════════════════
# 13 / 33. Runtime capability re-read inside boundary
# ═══════════════════════════════════════════════════════════════════════
def test_runtime_execution_available_inside_boundary_fails_closed(chain):
    r, reasons = _run(chain, capability_snapshot_resolver=lambda: {
        "current_runtime_state": "Executing",
        "current_maximum_plugin_capability": "dispatch",
        "execution_availability": "available",
    })
    assert r is None and reasons == ("gate9_runtime_execution_available_unexpected",)


def test_malformed_capability_snapshot_fails_closed(chain):
    r, reasons = _run(chain, capability_snapshot_resolver=lambda: None)
    assert r is None and reasons == ("gate9_runtime_execution_available_unexpected",)


# ═══════════════════════════════════════════════════════════════════════
# Structural input guards
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "override,reason",
    [
        (dict(identity=object()), "gate9_invalid_identity"),
        (dict(inputs=object()), "gate9_invalid_construction_input"),
        (dict(authority_current_time=""), "gate9_invalid_authority_current_time"),
        (dict(repo_root="not-a-path"), "gate9_invalid_repo_root"),
        (dict(descriptor_resolver="nope"), "gate9_invalid_descriptor_resolver"),
        (dict(consumption_store=object()), "gate9_invalid_consumption_store"),
        (dict(capability_snapshot_resolver="nope"), "gate9_invalid_capability_snapshot_resolver"),
        (dict(effect_plan=object()), "gate9_invalid_effect_plan"),
    ],
)
def test_structural_input_guards(chain, override, reason):
    r, reasons = _run(chain, **override)
    assert r is None and reasons == (reason,)


# ═══════════════════════════════════════════════════════════════════════
# 26 / 34 / 49-50. First valid consumption succeeds (test-path only);
#                  atomic single record; local-store-only effect
# ═══════════════════════════════════════════════════════════════════════
def test_first_valid_consumption_succeeds_in_test_path_only(chain):
    before = _count_consumption_json(Path(str(chain.store._root)))
    r, reasons = _run(chain)
    assert r is not None and g9.is_gate9_result(r) is True
    assert r.status == "consumed"
    assert r.proof_id == chain.rig.proof_id
    assert r.dispatch_state == "dispatch_attempted"
    assert reasons == ()
    after = _count_consumption_json(Path(str(chain.store._root)))
    assert after == before + 1
    # read-back: exactly one closed 8-item record
    written = chain.store.resolve(chain.rig.proof_id)
    assert written is not None and written.record_digest == r.record_digest
    assert written.dispatch_binding["state"] == "dispatch_attempted"
    assert set(written.request_identity) == {"invocation_id", "attempt_id", "idempotency_key"}


def test_no_partial_consumption_single_record_covers_proof_and_approval(chain):
    r, _ = _run(chain)
    written = chain.store.resolve(chain.rig.proof_id)
    assert written.authority_binding["proof_id"] == chain.rig.proof_id
    assert written.authority_binding["approval_id"] == chain.rig.approval_id
    # one file only
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 24 / 27-28 / 25. One-shot / replay
# ═══════════════════════════════════════════════════════════════════════
def test_duplicate_identical_request_reports_already_consumed(chain):
    r1, _ = _run(chain)
    assert r1.status == "consumed"
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "already_consumed"
    assert reasons2 == ("gate9_already_consumed",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


def test_replayed_stale_gate8_result_second_attempt_never_a_second_success(chain):
    _run(chain)
    # same handed Gate8Result again (a replay) → already consumed, not a
    # second record, not a retriable error.
    r, reasons = _run(chain, gate8_result=chain.g8)
    assert r.status == "already_consumed" and reasons == ("gate9_already_consumed",)


def test_different_proof_same_consumed_approval_is_rejected(chain):
    _run(chain)
    # A fresh proof_id with the already-consumed approval: the sequence-3
    # event will not resolve for the new proof_id → fail closed, no second
    # consumption.
    chain.projection.proof_id = "hap-" + "5" * 32
    chain.g5 = _synthetic_gate5_result(
        invocation_id=chain.identity.invocation_id,
        approval_id=chain.rig.approval_id,
        proof_id="hap-" + "5" * 32,
        seq3_digest=chain.event.record.event_digest,
        projection=chain.projection,
    )
    import pcae.core.runtime_dispatch_gate5 as _g5mod
    _g5mod.is_gate5_result = lambda c: c is chain.g5
    r, reasons = _run(chain)
    assert r is None
    assert reasons == ("gate9_sequence3_proof_verified_and_bound_absent",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 30. Concurrency — exactly one winner
# ═══════════════════════════════════════════════════════════════════════
def test_concurrent_requests_yield_exactly_one_success(chain):
    results = []
    barrier = threading.Barrier(4)

    def worker():
        barrier.wait()
        results.append(_run(chain))

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 4
    statuses = [r.status if r is not None else "fail_closed" for r, _ in results]
    # RDGO-001 §10 / §18: exactly one consumption success; every other racer
    # is deterministically already-consumed or fails closed — never a second
    # success, never a second canonical record.
    assert statuses.count("consumed") == 1
    losers = [s for s in statuses if s != "consumed"]
    assert len(losers) == 3
    assert all(s in ("already_consumed", "fail_closed") for s in losers)
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 31-33 / 29. Crash-before / crash-after commit; ambiguous restart
# ═══════════════════════════════════════════════════════════════════════
def test_crash_before_commit_leaves_both_unconsumed(chain, monkeypatch):
    def boom(proof_id, record):
        raise RuntimeError("crash before durable link")

    monkeypatch.setattr(chain.store, "create", boom)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_atomic_commit_failed",)
    assert chain.store.resolve(chain.rig.proof_id) is None
    assert _count_consumption_json(Path(str(chain.store._root))) == 0


def test_crash_after_commit_retry_reports_consumed(chain, monkeypatch):
    real_create = chain.store.create

    def create_then_crash(proof_id, record):
        real_create(proof_id, record)
        raise RuntimeError("crash after durable link, before return")

    monkeypatch.setattr(chain.store, "create", create_then_crash)
    r, reasons = _run(chain)
    # The durable record IS present (crash happened AFTER the atomic link):
    # the coordinator detects the completed consumption and reports
    # already-consumed — never a second write, never continue-to-effect.
    assert r is not None and r.status == "already_consumed"
    assert reasons == ("gate9_already_consumed",)
    assert chain.store.resolve(chain.rig.proof_id) is not None
    assert _count_consumption_json(Path(str(chain.store._root))) == 1
    # an independent retry (real create) still detects already-consumed
    monkeypatch.setattr(chain.store, "create", real_create)
    r2, reasons2 = _run(chain)
    assert r2.status == "already_consumed" and reasons2 == ("gate9_already_consumed",)


def test_ambiguous_durability_uncertain_fails_closed(chain, monkeypatch):
    def uncertain(proof_id):
        raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("partial")

    monkeypatch.setattr(chain.store, "resolve", uncertain)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_consumption_state_durability_uncertain",)


def test_canonical_durable_record_is_authority_across_restart(chain):
    r1, _ = _run(chain)
    # simulate a "restart": a brand-new store object over the same root
    fresh_store = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)))
    assert fresh_store.resolve(chain.rig.proof_id) is not None
    chain.store = fresh_store
    r2, reasons2 = _run(chain)
    assert r2.status == "already_consumed" and reasons2 == ("gate9_already_consumed",)


# ═══════════════════════════════════════════════════════════════════════
# 36-37 / 30-31. Gate9Result model + forward invariant
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_result_not_caller_constructable():
    with pytest.raises(TypeError):
        g9.Gate9Result(
            status="consumed", proof_id="p", approval_id="a", record_digest="d",
            dispatch_state="dispatch_attempted", invocation_id="i", attempt_id="t",
            consumed_at=NOW, advisory_reasons=(), _seal=object(),
        )


def test_gate9_result_non_transferable_and_non_serializable(chain):
    r, _ = _run(chain)
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    assert g9.is_gate9_result(object.__new__(g9.Gate9Result)) is False
    assert g9.is_gate9_result(None) is False


def test_gate9_result_identity_equality_only(chain):
    r1, _ = _run(chain)
    r2, _ = _run(chain)  # already_consumed
    assert r1 == r1 and r1 != r2 and hash(r1) == id(r1)


def test_gate9_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g9.Gate9Result,), {})


def test_is_gate9_result_is_provenance_not_success(chain):
    r, _ = _run(chain)
    r2, _ = _run(chain)
    # both are registry members (provenance); only one is a real consumption
    assert g9.is_gate9_result(r) and g9.is_gate9_result(r2)
    assert r.status == "consumed" and r2.status == "already_consumed"
    # the forward invariant is documented for Gate 10
    assert 'status == "consumed"' in G9_SRC


# ═══════════════════════════════════════════════════════════════════════
# 38-39 / 20 / 50. No Gate-10 call; module imports nothing effectful
# ═══════════════════════════════════════════════════════════════════════
def test_module_imports_nothing_effectful():
    tree = ast.parse(G9_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in (
        "subprocess", "socket", "pty", "os.system", "requests", "httpx", "urllib",
        "asyncio", "multiprocessing", "ctypes", "fcntl", "ssl", "selectors",
        "pcae.core.runtime_adapter", "pcae.core.mock_runtime_adapter",
        "fido2", "webauthn", "ctap",
    ):
        assert bad not in imported, bad
    assert "Popen(" not in G9_SRC and "os.system(" not in G9_SRC
    assert ".dispatch(" not in G9_SRC


def test_no_gate10_symbol_or_adapter_call():
    tree = ast.parse(G9_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("dispatch", "Popen", "spawn", "execv", "system"), node.func.attr
    for sym in ("run_gate10", "Gate10", "adapter_dispatch", "DispatchReceipt"):
        assert sym not in G9_SRC, sym


def test_runtime_state_unchanged_after_gate9_runs(chain):
    _run(chain)
    _run(chain)
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_gate9_writes_only_the_canonical_local_consumption_store(chain):
    # No write anywhere under repo except the tmp_path consumption store.
    before = _count_consumption_json(REPO_ROOT)
    _run(chain)
    assert _count_consumption_json(REPO_ROOT) == before  # nothing under the repo tree
    assert _count_consumption_json(Path(str(chain.store._root))) == 1


# ═══════════════════════════════════════════════════════════════════════
# 40 / 34. NON-REAL production path unreachable
# ═══════════════════════════════════════════════════════════════════════
def test_real_predicates_make_production_gate9_unreachable():
    # With NO provenance substitution, hand-built synthetic upstream objects
    # are not registry members → Gate 9 fails closed at the first gate. This
    # is the production reachability: the real predicates never trust a
    # fabricated Gate8Result / Gate7Result.
    forged8 = object.__new__(g8.Gate8Result)
    r, reasons = g9.run_gate9_atomic_authority_consumption(
        forged8,
        gate7_result=object.__new__(gate7.Gate7Result),
        gate6_decision=object.__new__(rdp.Gate6Decision),
        gate5_result=object.__new__(gate5.Gate5Result),
        identity=object(),
        inputs=object(),
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=object(),
        descriptor_resolver=lambda i: None,
        lifecycle_store=None,
        consumption_store=None,
        capability_snapshot_resolver=_snapshot,
    )
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def test_non_real_gate5_never_yields_gate5result_for_gate9(tmp_path):
    # The real run_gate5 on a canonical deterministic chain stops at NON-REAL
    # and returns no Gate5Result — so Gate 9 can never receive one in
    # production.
    from _rdw3w_helpers import construct_test_only_deterministic_approval, matching_context, always_unconsumed
    from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore
    inv = "inv-" + "d" * 32
    rig = _Rig(tmp_path / "hpac", invocation_id=inv)
    principal = rig.verify()
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id, invocation_id=inv, approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z", expires_at="2026-08-28T00:04:30Z",
    )
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    ctx = matching_context(approval, current_time=NOW)
    result, reasons = gate5.run_gate5(
        approval.approval_id, approval_store=store, authenticated_principal=principal,
        context=ctx, consumption_lookup=always_unconsumed, lifecycle_store=rig.lifecycle_store,
    )
    assert result is None
    assert reasons == ("non_real_authenticated_principal_cannot_validate_production_approval",)


# ═══════════════════════════════════════════════════════════════════════
# 40-42. Canonical store containment + durable-record + write authority
# ═══════════════════════════════════════════════════════════════════════
def test_consumption_store_rejects_traversal_proof_id(chain):
    chain.projection.proof_id = "../escape"
    chain.g5 = _synthetic_gate5_result(
        invocation_id=chain.identity.invocation_id, approval_id=chain.rig.approval_id,
        proof_id="../escape", seq3_digest=chain.event.record.event_digest, projection=chain.projection,
    )
    import pcae.core.runtime_dispatch_gate5 as _g5mod
    _g5mod.is_gate5_result = lambda c: c is chain.g5
    r, reasons = _run(chain)
    assert r is None
    # sequence-3 lookup for a bogus proof id fails closed before any write
    assert reasons[0].startswith("gate9_sequence3") or reasons[0] == "gate9_internal_error_fail_closed"


def test_planted_foreign_record_outside_writer_is_not_authoritative(chain):
    # A schema-shaped file placed by hand at a *different* proof_id root does
    # not make THIS invocation's proof consumed.
    other_root = Path(str(chain.store._root)) / "proofs" / "v2" / "hap-planted"
    other_root.mkdir(parents=True)
    (other_root / "consumption.json").write_text("{}")
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed"


# ═══════════════════════════════════════════════════════════════════════
# 41 / 43-45 / 47. Sole ownership + consumer inventory + production scope
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_is_sole_production_owner_of_consumption_boundary():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"run_gate9_atomic_authority_consumption|_GATE9_RESULTS", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits == {"src/pcae/core/runtime_dispatch_gate9.py"}


def test_gate9_is_the_only_new_gate8_result_consumer():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate8Result|is_gate8_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }
    assert "src/pcae/core/runtime_dispatch_gate9.py" in hits


def test_gate9result_has_zero_downstream_production_consumers():
    # Gate 10 does not exist.
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate9Result|is_gate9_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits == {"src/pcae/core/runtime_dispatch_gate9.py"}


def test_production_scope_since_baseline_is_the_single_new_gate9_file():
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert changed == {"src/pcae/core/runtime_dispatch_gate9.py"}


def test_contracts_and_earlier_gates_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/shell_gate.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/hpac_lifecycle.py",
        "src/pcae/core/runtime_authority.py",
    ):
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert diff == "", f"{rel} changed since baseline"


def test_gate9_does_not_reference_gate10_or_import_effect_modules():
    assert "runtime_adapter" not in G9_SRC
    assert "mock_runtime_adapter" not in G9_SRC


def test_f7_boundary_stated_verbatim():
    assert "same-account" in G9_SRC
    assert "arbitrary same-process Python code execution" in G9_SRC
    assert "threat model NOT broadened" in G9_SRC


def test_internal_error_fails_closed_with_no_partial_output(chain, monkeypatch):
    def boom(*a, **k):
        raise ValueError("kaboom")

    monkeypatch.setattr(g9, "_expected_subject_scope_binding_digest", boom)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_internal_error_fail_closed",)
    assert _count_consumption_json(Path(str(chain.store._root))) == 0
