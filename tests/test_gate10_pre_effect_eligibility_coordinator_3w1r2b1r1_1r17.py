"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.17 — Gate-10 Pre-Effect Eligibility
and Dispatch-Envelope Coordinator Implementation (Slice A).

Focused defensive tests for
``runtime_dispatch_gate10_eligibility.run_gate10_pre_effect_eligibility``
(the non-effecting front half of RDGO-001 v3.1 §11 Gate 10),
``DispatchEnvelope``, ``is_dispatch_envelope``, and the N-16-1 production
resolver factories. Constructed from the primary contracts (RDGO-001 v3.1
§11 items 1–6 / §15 / §16 / §17 / §19, RPAC-REQ-029/030, HPAC-001 v2.1 §41,
the ``.1R.16`` Gate-10 planning document F-G10-1..F-G10-18 and §34's
34-case defensive matrix) and current production source — not from a report
or test names.

The deterministic HPAC mechanism is permanently NON_REAL and the real
Gate-7 coordinator always returns ``Gate7Result(decision="DENY")``, so
**there is no legitimate positive production Gate-9 path** and therefore no
valid ``Gate9Result(status="consumed")`` — this coordinator's mandatory
input — can be produced in production. To exercise the eligibility battery
and the envelope mint WITHOUT manufacturing real authority, the ``chain``
fixture installs the SAME clearly-labelled test-boundary substitution the
``.1R.14`` Gate-9 suite uses (``monkeypatch`` on the upstream provenance
predicates only + a ``tmp_path`` consumption store), runs the real Gate-8
and Gate-9 coordinators under it to produce a genuine consumed
``consumption.json`` + ``Gate9Result``, then feeds Gate 10. It manufactures
no ``ValidatedAuthorityProjection``, no approval, no runtime capability, no
positive ``Gate7Result``, and writes only under ``tmp_path``.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate7 as gate7
from pcae.core import runtime_dispatch_gate8 as g8
from pcae.core import runtime_dispatch_gate9 as g9
from pcae.core import runtime_dispatch_gate10_eligibility as g10
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionStore,
)

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity
from test_hpac_verifier import NOW, _Rig

REPO_ROOT = Path(__file__).resolve().parents[1]
G10_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10_eligibility.py"
G10_SRC = G10_PATH.read_text()
G9_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py"
PHASE_ENTRY_BASELINE = "1f8b9c76"
_ECHO = "/bin/echo"
_RE_EXPIRES = "2026-12-31T23:59:59Z"

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
# Test-boundary fixtures — identical labelled substitution to the `.1R.14`
# Gate-9 suite; no real authority, no real runtime capability, no positive
# Gate7Result, tmp_path consumption store.
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


def _synthetic_gate7_result(*, decision, invocation_id, attempt_id, request_id, expires_at=_RE_EXPIRES):
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
        ("expires_at", expires_at),
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


def _g10_authority_generation_resolver(chain, **overrides):
    """Trusted five-marker Gate-10 resolver, built through the production
    N-16-1 factory over the rig's real principal/credential/approval and
    lifecycle/consumption stores."""

    resolver = g10.build_gate10_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=_ApprovalStoreShim(chain),
        approval_id=chain.rig.approval_id,
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    if not overrides:
        return resolver

    def _resolve():
        markers = dict(resolver())
        markers.update(overrides)
        return markers

    return _resolve


class _ApprovalStoreShim:
    """Minimal ``approval_store`` for
    ``build_production_authority_generation_resolver`` — returns an object
    with a stable ``approval_id`` / ``record_digest`` (the projection's), so
    ``approval_generation`` matches what Gate 9 committed."""

    def __init__(self, chain):
        self._chain = chain

    def load(self, approval_id):
        class _A:
            pass

        a = _A()
        a.approval_id = self._chain.rig.approval_id
        a.record_digest = self._chain.projection.record_digest
        return a


class _Chain:
    pass


@pytest.fixture
def chain(tmp_path, monkeypatch):
    inv = "inv-" + "a" * 32
    rig = _Rig(tmp_path / "hpac", invocation_id=inv)
    rig.verify()
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

    def _g9_authority_generation_resolver():
        return {
            "principal_generation": rig.registry.resolve_canonical_principal(
                rig.principal_id
            ).record_digest,
            "credential_generation": rig.registry.resolve_canonical_credential(
                rig.credential_id
            ).record_digest,
            "approval_generation": projection.record_digest,
        }

    # Wrong: gate9 uses its own three-marker factory shape. Build a real
    # consumed Gate9Result the same way the `.1R.14` suite does.
    from pcae.core.runtime_authority import compute_canonical_digest

    def _g9_agr():
        return {
            "principal_generation": rig.registry.resolve_canonical_principal(
                rig.principal_id
            ).record_digest,
            "credential_generation": rig.registry.resolve_canonical_credential(
                rig.credential_id
            ).record_digest,
            "approval_generation": compute_canonical_digest(
                {
                    "approval_id": rig.approval_id,
                    "approval_record_digest": projection.record_digest,
                    "revocation_artifact_digest": None,
                }
            ),
        }

    g9_result, g9_reasons = g9.run_gate9_atomic_authority_consumption(
        g8_result,
        gate7_result=g7,
        gate6_decision=g6,
        gate5_result=g5,
        identity=identity,
        inputs=inputs,
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(),
        lifecycle_store=rig.lifecycle_store,
        consumption_store=c.store,
        capability_snapshot_resolver=_snapshot,
        authority_generation_resolver=_g9_agr,
    )
    assert g9_result is not None and g9_result.status == "consumed", g9_reasons
    c.g9 = g9_result
    c.record = c.store.resolve(rig.proof_id)
    assert c.record is not None
    return c


def _run(chain, **overrides):
    _has_g9 = "gate9_result" in overrides
    _g9 = overrides.pop("gate9_result", None)
    kw = dict(
        gate8_result=overrides.pop("gate8_result", chain.g8),
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
        authority_generation_resolver=overrides.pop(
            "authority_generation_resolver", _g10_authority_generation_resolver(chain)
        ),
    )
    kw.update(overrides)
    return g10.run_gate10_pre_effect_eligibility(_g9 if _has_g9 else chain.g9, **kw)


def _count_consumption_json(root: Path):
    return len(list(root.rglob("consumption.json")))


# ═══════════════════════════════════════════════════════════════════════
# 26-27. The stable synthetic eligibility path mints exactly one envelope
# ═══════════════════════════════════════════════════════════════════════
def test_stable_synthetic_eligibility_mints_one_envelope(chain):
    before = _count_consumption_json(Path(str(chain.store._root)))
    env, advisory = _run(chain)
    assert env is not None and g10.is_dispatch_envelope(env) is True
    assert advisory == ()
    # F-G10-8: consumed authority is byte-unchanged; NO new durable write.
    assert _count_consumption_json(Path(str(chain.store._root))) == before
    assert chain.store.resolve(chain.rig.proof_id).record_digest == chain.record.record_digest


def test_dispatch_envelope_exact_contract_fields(chain):
    env, _ = _run(chain)
    assert env.envelope_schema_version == "RPAC-DISPATCH-ENVELOPE/1.0"
    assert env.invocation_id == chain.identity.invocation_id
    assert env.attempt_id == chain.identity.attempt_id
    assert env.idempotency_key == chain.identity.idempotency_key
    assert env.proof_id == chain.rig.proof_id
    assert env.approval_id == chain.rig.approval_id
    # RPAC-REQ-029: immutable request identity, fresh target-status digest,
    # approval digest, PB decision digest(s), RE decision digest, durable
    # record reference, expiration.
    assert env.consumption_record_digest == chain.record.record_digest
    assert env.durable_record_reference == f"proofs/v2/{chain.rig.proof_id}/consumption.json"
    assert env.pb_decision_digest == chain.record.pb_binding["decision_digest"]
    assert env.re_decision_digest == chain.record.runtime_enforcement_binding["decision_digest"]
    assert env.approval_digest == chain.record.authority_binding["approval_digest"]
    assert env.executable_identity_digest == chain.record.target_binding["executable_identity_digest"]
    assert env.containment_evidence_digest == chain.g8.containment_evidence_digest
    assert env.effect_plan_digest == chain.g8.effect_plan_digest
    assert env.expires_at == chain.record.runtime_enforcement_binding["expires_at"]
    assert env.runtime_capability_snapshot_digest
    assert env.target_status_digest
    assert env.contract_versions["rdgo"] == "RDGO-001/3.1"
    assert isinstance(env.envelope_digest, str) and len(env.envelope_digest) == 64


# ═══════════════════════════════════════════════════════════════════════
# 28-33. DispatchEnvelope model: non-authoritative, identity-only,
# non-serializable, non-subclassable, provenance != effect
# ═══════════════════════════════════════════════════════════════════════
def test_dispatch_envelope_not_caller_constructable():
    with pytest.raises(TypeError):
        g10.DispatchEnvelope(_seal=object())


def test_dispatch_envelope_non_serializable_and_non_transferable(chain):
    env, _ = _run(chain)
    with pytest.raises(TypeError):
        pickle.dumps(env)
    with pytest.raises(TypeError):
        copy.deepcopy(env)


def test_dispatch_envelope_structural_copy_is_non_authoritative(chain):
    env, _ = _run(chain)
    # copy.copy of a __slots__ object with a custom __setattr__ guard: either
    # it raises, or it produces an object that is NOT a registry member.
    try:
        clone = copy.copy(env)
    except Exception:
        return
    assert g10.is_dispatch_envelope(clone) is False


def test_dispatch_envelope_identity_equality_only(chain):
    env1, _ = _run(chain)
    env2, _ = _run(chain)  # a second mint over the same durable record
    assert env1 == env1 and env1 != env2 and hash(env1) == id(env1)


def test_dispatch_envelope_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g10.DispatchEnvelope,), {})


def test_dispatch_envelope_is_immutable(chain):
    env, _ = _run(chain)
    with pytest.raises(AttributeError):
        env.invocation_id = "tampered"


def test_dispatch_envelope_provenance_does_not_imply_effect_permission(chain):
    env, _ = _run(chain)
    # provenance predicate is separate from any notion of "effect authorized"
    assert g10.is_dispatch_envelope(env) is True
    assert g10.is_dispatch_envelope(object.__new__(g10.DispatchEnvelope)) is False
    assert g10.is_dispatch_envelope(None) is False
    assert g10.is_dispatch_envelope(env.to_reference_document()) is False


# ═══════════════════════════════════════════════════════════════════════
# 1-3. Trusted Gate9Result required; status == "consumed"; forgeries
# ═══════════════════════════════════════════════════════════════════════
def test_trusted_gate9_result_required(chain):
    env, reasons = _run(chain, gate9_result=None)
    assert env is None and reasons == ("gate10_untrusted_gate9_result",)


def test_object_new_gate9_result_rejected(chain):
    env, reasons = _run(chain, gate9_result=object.__new__(g9.Gate9Result))
    assert env is None and reasons == ("gate10_untrusted_gate9_result",)


def test_copied_pickled_gate9_result_rejected(chain):
    with pytest.raises(TypeError):
        pickle.dumps(chain.g9)
    with pytest.raises(TypeError):
        copy.deepcopy(chain.g9)


def test_consumed_status_required_not_already_consumed(chain):
    # a second real Gate-9 call on the same proof → already_consumed
    already, _ = g9.run_gate9_atomic_authority_consumption(
        chain.g8,
        gate7_result=chain.g7,
        gate6_decision=chain.g6,
        gate5_result=chain.g5,
        identity=chain.identity,
        inputs=chain.inputs,
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        capability_snapshot_resolver=_snapshot,
        authority_generation_resolver=_g10_authority_generation_resolver(chain),
    )
    assert already is not None and already.status == "already_consumed"
    assert g9.is_gate9_result(already) is True  # provenance holds
    env, reasons = _run(chain, gate9_result=already)
    assert env is None and reasons == ("gate10_gate9_status_not_consumed",)


# ═══════════════════════════════════════════════════════════════════════
# 4-6. Durable consumption.json re-read; /2.0 & snapshot-absent rejection
# ═══════════════════════════════════════════════════════════════════════
def test_durable_record_absent_fails_closed(chain):
    empty_store = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)) / "other")
    env, reasons = _run(chain, consumption_store=empty_store)
    assert env is None and reasons == ("gate10_consumption_record_read_back_failed",)


def test_durability_uncertain_record_fails_closed(chain, monkeypatch):
    from pcae.core.runtime_invocation_authority_consumption import (
        RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
    )

    def boom(proof_id):
        raise RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("corrupt")

    monkeypatch.setattr(chain.store, "resolve", boom)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_consumption_record_read_back_failed",)


def test_generation_snapshot_absent_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)

    class _Legacy:
        consumption_schema_version = "HPAC-AUTHORITY-CONSUMPTION/2.0"
        authority_generation_binding = None
        record_digest = real.record_digest
        request_identity = real.request_identity
        authority_binding = real.authority_binding
        target_binding = real.target_binding
        repository_task_binding = real.repository_task_binding
        prompt_binding = real.prompt_binding
        pb_binding = real.pb_binding
        runtime_enforcement_binding = real.runtime_enforcement_binding
        dispatch_binding = real.dispatch_binding

    monkeypatch.setattr(chain.store, "resolve", lambda p: _Legacy())
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_consumption_record_generation_snapshot_absent",)


def test_malformed_generation_snapshot_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    bad = dict(real.authority_generation_binding)
    bad["snapshot_schema_version"] = "HPAC-AUTHORITY-GENERATION-SNAPSHOT/9.9"

    class _Bad:
        consumption_schema_version = "HPAC-AUTHORITY-CONSUMPTION/2.1"
        authority_generation_binding = bad
        record_digest = real.record_digest
        request_identity = real.request_identity
        authority_binding = real.authority_binding
        target_binding = real.target_binding
        repository_task_binding = real.repository_task_binding
        prompt_binding = real.prompt_binding
        pb_binding = real.pb_binding
        runtime_enforcement_binding = real.runtime_enforcement_binding
        dispatch_binding = real.dispatch_binding

    monkeypatch.setattr(chain.store, "resolve", lambda p: _Bad())
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_consumption_snapshot_malformed",)


# ═══════════════════════════════════════════════════════════════════════
# lineage binding: digest / ids must match durable record AND live request
# ═══════════════════════════════════════════════════════════════════════
def test_record_digest_mismatch_vs_gate9_result_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    monkeypatch.setattr(
        real, "record_digest", "0" * 64, raising=False
    ) if False else None
    # simpler: wrap resolve to return a record whose digest differs
    import dataclasses

    tampered = dataclasses.replace(real, record_digest="0" * 64)
    monkeypatch.setattr(chain.store, "resolve", lambda p: tampered)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_lineage_binding_mismatch",)


def test_live_request_target_drift_rejected(chain):
    other = dispatch_inputs(runtime_target_id="local-cli-fixture-2")
    env, reasons = _run(chain, inputs=other)
    assert env is None
    assert reasons[0] in (
        "gate10_invocation_binding_mismatch",
        "gate10_request_currentness_drift" ,
        "gate10_lineage_binding_mismatch",
    ) or reasons[0].startswith("gate10_request_currentness_drift")


def test_idempotency_key_alone_does_not_authorize(chain):
    # A fresh identity that reuses only the idempotency_key but has a new
    # attempt_id/invocation_id → invocation binding mismatch, no envelope.
    other = new_dispatch_identity(chain.inputs, invocation_id="inv-" + "b" * 32)
    object.__setattr__(other, "idempotency_key", chain.identity.idempotency_key)
    env, reasons = _run(chain, identity=other)
    assert env is None and reasons == ("gate10_invocation_binding_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 7-10 / 13. Authority-generation drift (principal/credential/approval/
# lifecycle); consumption-state inconsistency
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "marker",
    ["principal_generation", "credential_generation", "approval_generation", "lifecycle_generation"],
)
def test_authority_generation_drift_rejected(chain, marker):
    resolver = _g10_authority_generation_resolver(chain, **{marker: "drifted-" + "z" * 16})
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == (f"gate10_authority_generation_drift:{marker}",)


def test_incomplete_generation_markers_rejected(chain):
    env, reasons = _run(chain, authority_generation_resolver=lambda: {"principal_generation": "x"})
    assert env is None and reasons == ("gate10_authority_generation_snapshot_incomplete",)


def test_consumption_state_inconsistency_rejected(chain):
    resolver = _g10_authority_generation_resolver(chain, consumption_generation="present:deadbeef")
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == ("gate10_consumption_state_inconsistent",)


def test_production_generation_resolver_derives_from_canonical_sources(chain):
    resolver = _g10_authority_generation_resolver(chain)
    markers = resolver()
    assert set(markers) == {
        "principal_generation",
        "credential_generation",
        "approval_generation",
        "lifecycle_generation",
        "consumption_generation",
    }
    assert markers["principal_generation"] == chain.rig.registry.resolve_canonical_principal(
        chain.rig.principal_id
    ).record_digest
    assert markers["consumption_generation"] == "present:" + chain.record.record_digest


def test_capability_resolver_reads_canonical_introspection_state():
    snap = g10.build_gate10_capability_snapshot_resolver()()
    assert snap == {
        "current_runtime_state": ri.CURRENT_RUNTIME_STATE,
        "current_maximum_plugin_capability": ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        "execution_availability": ri.EXECUTION_AVAILABILITY,
    }


# ═══════════════════════════════════════════════════════════════════════
# 15 / 17 / 20. Runtime capability hard stop; valid authority cannot
# override unavailable; post-Gate-9 projection revalidation
# ═══════════════════════════════════════════════════════════════════════
def test_runtime_capability_not_unavailable_rejected(chain):
    for bad in (
        {"current_runtime_state": "Executable", "current_maximum_plugin_capability": "execute", "execution_availability": "available"},
        {"current_runtime_state": "Observed", "current_maximum_plugin_capability": "observe", "execution_availability": "available"},
        {},
        "not-a-dict",
    ):
        env, reasons = _run(chain, capability_snapshot_resolver=lambda b=bad: b)
        assert env is None and reasons == ("gate10_runtime_capability_not_unavailable",)


def test_valid_human_authority_cannot_override_unavailable_capability(chain):
    # everything else valid; only the capability snapshot says "available"
    env, reasons = _run(
        chain,
        capability_snapshot_resolver=lambda: {
            "current_runtime_state": "Executable",
            "current_maximum_plugin_capability": "execute",
            "execution_availability": "available",
        },
    )
    assert env is None and reasons == ("gate10_runtime_capability_not_unavailable",)


def test_post_gate9_projection_revocation_rejected(chain, monkeypatch):
    proj = chain.projection
    monkeypatch.setattr(g10, "is_trusted_validated_authority_projection", lambda p: p is proj)
    monkeypatch.setattr(
        g10, "revalidate_validated_authority_projection", lambda p, *, current_time: False
    )
    env, reasons = _run(chain, validated_authority_projection=proj)
    assert env is None and reasons == ("gate10_stale_validated_authority_projection",)


def test_untrusted_projection_rejected(chain, monkeypatch):
    monkeypatch.setattr(g10, "is_trusted_validated_authority_projection", lambda p: False)
    env, reasons = _run(chain, validated_authority_projection=object())
    assert env is None and reasons == ("gate10_stale_validated_authority_projection",)


# ═══════════════════════════════════════════════════════════════════════
# 17-18. PB lineage / RE lineage / RE expiry
# ═══════════════════════════════════════════════════════════════════════
def test_pb_lineage_not_allow_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    import dataclasses

    bad = dataclasses.replace(real, pb_binding={**real.pb_binding, "decision": "DENY"})
    monkeypatch.setattr(chain.store, "resolve", lambda p: bad)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_pb_lineage_not_allow",)


def test_re_lineage_not_allow_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    import dataclasses

    bad = dataclasses.replace(
        real,
        runtime_enforcement_binding={**real.runtime_enforcement_binding, "verdict": "HUMAN_REVIEW"},
    )
    monkeypatch.setattr(chain.store, "resolve", lambda p: bad)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_re_lineage_not_allow",)


def test_re_decision_expired_rejected(chain):
    # authority_current_time now AFTER the RE decision's expires_at
    env, reasons = _run(chain, authority_current_time="2027-01-01T00:00:00Z")
    assert env is None and reasons == ("gate10_re_decision_expired",)


# ═══════════════════════════════════════════════════════════════════════
# 11-12 / 14 / 16 / 33. Containment / effect-plan / executable drift;
# credential-requiring plan rejected
# ═══════════════════════════════════════════════════════════════════════
def test_effect_plan_digest_drift_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(argv=("different",)))
    assert env is None and reasons == ("gate10_containment_evidence_recomputation_mismatch",)


def test_cwd_drift_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(cwd=str(REPO_ROOT / "src")))
    assert env is None
    assert reasons[0] in (
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
    )


def test_executable_identity_drift_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(sha256="f" * 64))
    assert env is None and reasons == ("gate10_executable_identity_drift",)


def test_executable_absent_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(path="/nonexistent/xyz"))
    assert env is None and reasons == ("gate10_executable_identity_drift",)


def test_credentials_required_effect_plan_rejected(chain):
    # containment recomputation catches this first (gate8 denies credentials),
    # but either way there is no envelope.
    env, reasons = _run(chain, effect_plan=_good_effect_plan(credentials_required=True))
    assert env is None
    assert reasons[0] in (
        "gate10_effect_plan_requires_credentials",
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
    )


def test_containment_recomputation_failure_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert env is None and reasons == ("gate10_containment_recomputation_failed",)


# ═══════════════════════════════════════════════════════════════════════
# 2 / 5-8 upstream lineage provenance + ALLOW
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_gate8_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(g8, "is_gate8_result", lambda c: False)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_untrusted_gate8_result",)


def test_negative_gate8_result_rejected(chain):
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
    env, reasons = _run(chain, gate8_result=neg)
    assert env is None and reasons == ("gate10_gate8_containment_not_established",)


def test_untrusted_gate7_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: False)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_untrusted_gate7_result",)


def test_gate7_decision_not_allow_rejected(chain, monkeypatch):
    deny = _synthetic_gate7_result(
        decision="DENY",
        invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id,
        request_id=chain.g6.request_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is deny)
    env, reasons = _run(chain, gate7_result=deny)
    assert env is None and reasons == ("gate10_gate7_decision_not_allow",)


def test_untrusted_gate5_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: False)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_untrusted_gate5_result",)


def test_invocation_binding_mismatch_rejected(chain):
    other = new_dispatch_identity(chain.inputs, invocation_id="inv-" + "9" * 32)
    env, reasons = _run(chain, identity=other)
    assert env is None and reasons == ("gate10_invocation_binding_mismatch",)


def test_gate7_lineage_mismatch_rejected(chain, monkeypatch):
    other7 = _synthetic_gate7_result(
        decision="ALLOW",
        invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id,
        request_id=chain.g6.request_id,
        expires_at="2026-11-30T00:00:00Z",
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c in (chain.g7, other7))
    env, reasons = _run(chain, gate7_result=other7)
    assert env is None and reasons == ("gate10_gate7_lineage_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 19 / 25 / restart / 21-22. NON_REAL unreachable; no effect; consumed
# authority stays consumed; restart re-runs battery from disk
# ═══════════════════════════════════════════════════════════════════════
def test_real_predicates_make_production_gate10_unreachable():
    # With NO provenance substitution, a hand-built Gate9Result is not a
    # registry member → fail closed at the first gate.
    env, reasons = g10.run_gate10_pre_effect_eligibility(
        object.__new__(g9.Gate9Result),
        gate8_result=object.__new__(g8.Gate8Result),
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
        authority_generation_resolver=lambda: {},
    )
    assert env is None and reasons == ("gate10_untrusted_gate9_result",)


def test_pre_effect_rejection_produces_no_effect_and_consumed_stays_consumed(chain):
    before_digest = chain.store.resolve(chain.rig.proof_id).record_digest
    before_files = _count_consumption_json(Path(str(chain.store._root)))
    env, reasons = _run(chain, capability_snapshot_resolver=lambda: {"execution_availability": "available"})
    assert env is None
    after = chain.store.resolve(chain.rig.proof_id)
    assert after is not None and after.record_digest == before_digest  # byte-unchanged
    assert _count_consumption_json(Path(str(chain.store._root))) == before_files


def test_restart_reads_durable_state_only(chain):
    # a "restart": brand-new store object over the same root; the coordinator
    # re-runs the whole battery from disk and still mints an envelope.
    fresh_store = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)))
    resolver = g10.build_gate10_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=_ApprovalStoreShim(chain),
        approval_id=chain.rig.approval_id,
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=fresh_store,
        proof_id=chain.rig.proof_id,
    )
    env, reasons = _run(chain, consumption_store=fresh_store, authority_generation_resolver=resolver)
    assert env is not None, reasons


def test_internal_error_fails_closed_with_no_partial_output(chain, monkeypatch):
    monkeypatch.setattr(g10, "_gate7_result_digest_unused", None, raising=False)
    monkeypatch.setattr(
        g10, "compute_canonical_digest", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom"))
    )
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_internal_error_fail_closed",)


# ═══════════════════════════════════════════════════════════════════════
# 30-31 / 43-44. Source-level no-effect scan; no adapter dispatch symbol;
# no runtime capability mutation
# ═══════════════════════════════════════════════════════════════════════
def test_module_imports_nothing_effectful():
    tree = ast.parse(G10_SRC)
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
        "pcae.core.shell_gate", "fido2", "webauthn", "ctap", "http", "http.client",
    ):
        assert bad not in imported, bad


def test_no_adapter_dispatch_or_effect_primitive_in_source():
    """AST scan (phase prompt §43): no effect-primitive *call* and no
    effect-primitive *name reference* anywhere in code — string literals
    (docstrings) that merely NAME the forbidden concepts are ignored."""
    tree = ast.parse(G10_SRC)
    banned_attr = {
        "dispatch", "Popen", "spawn", "spawnv", "posix_spawn", "execv", "execve",
        "execvp", "execl", "system", "popen", "call", "check_output", "check_call",
        "connect", "sendall", "urlopen", "getpass", "getuser",
    }
    banned_name = {
        "subprocess", "socket", "pty", "ctypes", "ssl", "fido2", "webauthn",
        "DispatchReceipt", "RuntimeAdapter", "MockDryRuntimeAdapter",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in banned_attr, node.func.attr
        if isinstance(node, ast.Name):
            assert node.id not in banned_name, node.id
        if isinstance(node, ast.Attribute):
            assert node.attr not in banned_name, node.attr
    assert "run_gate10_pre_effect_eligibility" in G10_SRC


def test_runtime_zero_effect_monkeypatched_boundaries(chain, monkeypatch):
    import os
    import subprocess as sp

    for mod, name in ((os, "system"), (os, "posix_spawn"), (sp, "Popen"), (sp, "run")):
        if hasattr(mod, name):
            monkeypatch.setattr(
                mod, name, lambda *a, **k: pytest.fail(f"{name} called by Gate-10 eligibility")
            )
    env, _ = _run(chain)
    assert env is not None
    # negative path too
    _run(chain, capability_snapshot_resolver=lambda: {})


def test_runtime_state_unchanged_after_gate10_runs(chain):
    _run(chain)
    _run(chain, capability_snapshot_resolver=lambda: {})
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_current_runtime_negative_path_with_production_resolvers(chain):
    # production capability resolver → canonical Observed/observe/unavailable
    # → the battery still proceeds and mints an envelope (the "no effect"
    # property is structural: this module has NO adapter.dispatch() call
    # site). No positive PRODUCTION path exists because a real Gate9Result
    # cannot be produced (tested above).
    env, reasons = _run(chain, capability_snapshot_resolver=g10.build_gate10_capability_snapshot_resolver())
    assert env is not None, reasons


# ═══════════════════════════════════════════════════════════════════════
# 47-48. Envelope has zero effect-bearing consumers; no first-effect site
# ═══════════════════════════════════════════════════════════════════════
def test_dispatch_envelope_has_zero_downstream_production_consumers():
    hits = set(subprocess.run(
        ["git", "grep", "--untracked", "-l", "-E",
         r"is_dispatch_envelope|run_gate10_pre_effect_eligibility|_DISPATCH_ENVELOPES|build_gate10_",
         "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True).stdout.split())
    assert hits == {"src/pcae/core/runtime_dispatch_gate10_eligibility.py"}


def test_no_first_effect_call_site_in_eligibility_module():
    # The eligibility module contains no ``adapter.dispatch(`` / ``.dispatch(envelope)``
    # / ``posix_spawn(`` CODE (docstring prose that names the concept is
    # fine — proven by the AST scan test). Strip comments and check no code
    # line performs a dispatch.
    tree = ast.parse(G10_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", getattr(fn, "id", ""))
            assert name != "dispatch", "eligibility module must have no dispatch() call"
    # and no posix_spawn / Popen even as a bare reference
    assert "posix_spawn" not in ast.dump(tree)


def test_no_gate10_first_effect_module_exists():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()


# ═══════════════════════════════════════════════════════════════════════
# 35-36 / 49-52 / 54. Gate 5-9 unchanged; production scope
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_module_bytes_unchanged_since_baseline():
    diff = subprocess.run(
        ["git", "diff", PHASE_ENTRY_BASELINE, "--", "src/pcae/core/runtime_dispatch_gate9.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    assert diff == ""


#: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B) is authorized by
#: `.1R.16` §36.2 / §38 to modify exactly these earlier-phase modules
#: (the two 3S.2.1 MUST-FIX repairs + the item-9 runtime-inspect
#: discoverability repair) and to add one new non-authoritative mirror
#: module. The Slice-A coordinator itself (`runtime_dispatch_gate10_eligibility.py`)
#: stays byte-unchanged; Gate 5-9 stay byte-unchanged; no contract changes.
_SLICE_B_AUTHORIZED_SINCE_BASELINE = {
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",  # Slice A (this suite's own new file)
    "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",   # Slice B — new, non-authoritative, non-effecting
    "src/pcae/core/runtime_invocation.py",                   # Slice B — 3S.2.1 MUST-FIX #2 (store path containment)
    "src/pcae/core/runtime_adapter.py",                      # Slice B — 3S.2.1 MUST-FIX #1 (malformed-result fail-closed)
    "src/pcae/core/runtime_introspection.py",                # Slice B — 3S.2.1 item-9 (runtime-inspect discoverability, observational)
    "src/pcae/commands/runtime_inspect.py",  # Slice B (.1R.19) -- 3S.2.1 item-9 runtime-inspect CLI section (observational)
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
    # narrow-eligibility policy + POL-013). Exact filenames, no wildcard.
    "src/pcae/core/permission_broker_foundation.py",         # POL-005 §12a carve-out + POL-013
    "src/pcae/core/runtime_dispatch_permission.py",          # Gate 6 -- N-16-3 profile derivation + N-16-6 admission stub
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0). Gate 7
    # is the sole authorized production surface for the positive-result
    # schema/identity/TTL/immutability. Exact filename, no wildcard.
    "src/pcae/core/runtime_dispatch_gate7.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (N-16-5 -- HPAC-PAWA-001
    # v1.1 Slice 1 production protected-admin writer anchor). Exact
    # filenames, no wildcard. The non-agent-importable admin-writer fence
    # (guard-tested off every agent/runtime/Gate path) plus a seal-guarded
    # PRODUCTION mint primitive and PRODUCTION subject-scoped writer
    # consumption -- no Gate-10 / DispatchEnvelope / effect wiring.
    "src/pcae/core/hpac_pawa_schemas.py",
    "src/pcae/core/hpac_pawa_agent_exclusion.py",
    "src/pcae/core/hpac_protected_admin_writer.py",
    "src/pcae/core/hpac_foundation.py",
    "src/pcae/core/human_principal_registry.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (N-16-5 -- merged RHAMP
    # `.1R.30` bundle). Exact filenames, no wildcard.
    "src/pcae/core/hpac_verifier.py",
    "src/pcae/core/hpac_rhamp_terminal_reasons.py",
    "src/pcae/core/hpac_rhamp_client_context.py",
    "src/pcae/core/hpac_rhamp_credential_sidecar.py",
    "src/pcae/core/hpac_rhamp_counter_state.py",
    "src/pcae/core/hpac_rhamp_ctap2.py",
    "src/pcae/core/human_authenticator_fido2.py",
    "src/pcae/core/hpac_rhamp_assertion_verify.py",
    "src/pcae/core/hpac_rhamp_enrollment.py",
}

#: Contracts a later authorized phase may change (exact paths, no wildcard).
#: Phase ...1R.22: PBRD-001 -> v3.0 (MAJOR).
_R122_AUTHORIZED_CONTRACT_CHANGES = {
    "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
    # Phase ...1R.26 (N-16-4): the one NEW companion contract REPRC-001 v1.0.
    "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md",
}


def test_earlier_gates_and_contracts_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/shell_gate.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_registry.py",
    ):
        if (
            rel in _SLICE_B_AUTHORIZED_SINCE_BASELINE
            or rel in _R122_AUTHORIZED_CONTRACT_CHANGES
        ):
            continue
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert diff == "", f"{rel} changed since baseline"


def test_production_scope_since_baseline_is_the_single_new_file():
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True).stdout.split())
    # Slice A alone: exactly the one new coordinator file. Slice B (.1R.19)
    # additionally admits the exact `.1R.16`-§38-authorized set below — an
    # unauthorized production-file expansion still fails this subset check.
    assert changed <= _SLICE_B_AUTHORIZED_SINCE_BASELINE, sorted(
        changed - _SLICE_B_AUTHORIZED_SINCE_BASELINE
    )


def test_f7_boundary_stated_verbatim():
    assert "same-account autonomous-agent assumption" in G10_SRC
    assert "same-process Python code execution" in G10_SRC
    assert "threat model NOT broadened" in G10_SRC


def test_no_capability_elevation_or_state_mutation_in_source():
    tree = ast.parse(G10_SRC)
    for node in ast.walk(tree):
        # no assignment to a runtime_introspection capability constant
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute):
                    assert tgt.attr not in (
                        "CURRENT_RUNTIME_STATE",
                        "CURRENT_MAXIMUM_PLUGIN_CAPABILITY",
                        "EXECUTION_AVAILABILITY",
                    )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("register", "enable", "activate", "promote", "elevate")
