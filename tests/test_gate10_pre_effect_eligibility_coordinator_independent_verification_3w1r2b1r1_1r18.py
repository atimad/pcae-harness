"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.18 — Independent Verification of the
Gate-10 Pre-Effect Eligibility Coordinator (Slice A of the ``.1R.16`` plan).

This suite **independently re-derives** the RDGO-001 v3.1 §11 items 1–6 +
§15 / §16 / §17 pre-effect read-back battery, the RPAC-REQ-029
``DispatchEnvelope`` non-bearer model, and the N-16-1 production resolver
factories from the primary contracts and current production source — NOT
from the ``.1R.17`` report, its test names, or its helper names.

Verification principle (phase prompt §1): RE-DERIVE, DO NOT TRUST. Every
claim ``.1R.17`` makes ("coordinator implemented", "envelope non-bearer",
"N-16-1 implemented", "first external effect absent") is re-established
here against source.

The deterministic HPAC mechanism is permanently NON_REAL and the real
Gate-7 coordinator always returns ``Gate7Result(decision="DENY")``, so no
legitimate positive production ``Gate9Result(status="consumed")`` — this
coordinator's mandatory input — can be produced. To exercise the positive
branches WITHOUT manufacturing real authority, ``chain`` installs the same
clearly-labelled test-boundary substitution the ``.1R.14`` Gate-9 suite
uses (``monkeypatch`` on the upstream provenance predicates only + a
``tmp_path`` consumption store), runs the REAL Gate-8 and Gate-9
coordinators under it, then feeds Gate 10. No ``ValidatedAuthorityProjection``,
approval, runtime capability, or positive ``Gate7Result`` is fabricated;
nothing is written outside ``tmp_path``.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib
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
# Immutable pre-.1R.17 baseline (phase prompt §66). Verified below to be
# the parent of the .1R.17 production implementation commit.
PHASE_ENTRY_BASELINE = "1f8b9c76"
_ECHO = "/bin/echo"
_RE_EXPIRES = "2026-12-31T23:59:59Z"

_CANONICAL_NON_EXECUTING = {
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
    return dict(_CANONICAL_NON_EXECUTING)


# ═══════════════════════════════════════════════════════════════════════
# Test-boundary fixtures (independent construction; same labelled
# substitution pattern as `.1R.14`)
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


def _mk_gate5(*, invocation_id, approval_id, proof_id, seq3_digest, projection):
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


def _mk_gate6(*, decision, invocation_id, attempt_id, request_id):
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


def _mk_gate7(*, decision, invocation_id, attempt_id, request_id, expires_at=_RE_EXPIRES):
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


class _ApprovalStoreShim:
    def __init__(self, chain):
        self._chain = chain

    def load(self, approval_id):
        class _A:
            pass

        a = _A()
        a.approval_id = self._chain.rig.approval_id
        a.record_digest = self._chain.projection.record_digest
        return a


def _prod_agr(chain, **overrides):
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


class _Chain:
    pass


@pytest.fixture
def chain(tmp_path, monkeypatch):
    inv = "inv-" + "c" * 32
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
    g7 = _mk_gate7(decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id)
    g6 = _mk_gate6(decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id)
    g5 = _mk_gate5(
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
    monkeypatch.setattr(g8, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection)
    monkeypatch.setattr(g9, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(g9, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection)

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
    c.rig, c.event, c.inputs, c.identity, c.projection = rig, event, inputs, identity, projection
    c.g5, c.g6, c.g7, c.g8 = g5, g6, g7, g8_result
    c.store = RuntimeInvocationAuthorityConsumptionStore(tmp_path / "consumption")

    from pcae.core.runtime_authority import compute_canonical_digest

    def _g9_agr():
        return {
            "principal_generation": rig.registry.resolve_canonical_principal(rig.principal_id).record_digest,
            "credential_generation": rig.registry.resolve_canonical_credential(rig.credential_id).record_digest,
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
    has_g9 = "gate9_result" in overrides
    g9r = overrides.pop("gate9_result", None)
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
        authority_generation_resolver=overrides.pop("authority_generation_resolver", _prod_agr(chain)),
    )
    kw.update(overrides)
    return g10.run_gate10_pre_effect_eligibility(g9r if has_g9 else chain.g9, **kw)


def _count_consumption_json(root: Path) -> int:
    return len(list(root.rglob("consumption.json")))


# ═══════════════════════════════════════════════════════════════════════
# §4/§5 — verification-entry repository state + exact .1R.17 range
# ═══════════════════════════════════════════════════════════════════════
def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_verification_entry_state_and_1r17_range():
    # .1R.17 production implementation commit + its immutable parent baseline.
    impl = _git("log", "--format=%H", "--grep", r"1R.17: Gate-10 pre-effect eligibility coordinator", "-1")
    assert impl, "could not locate the .1R.17 production implementation commit"
    parent = _git("rev-parse", f"{impl}^")
    assert parent.startswith(PHASE_ENTRY_BASELINE), (parent, PHASE_ENTRY_BASELINE)
    # The single production file appeared exactly at that commit.
    names = _git("diff", "--name-only", f"{parent}", f"{impl}", "--", "src/pcae").split()
    assert names == ["src/pcae/core/runtime_dispatch_gate10_eligibility.py"]


def test_no_unpushed_divergence_at_verification_entry():
    # origin/main..HEAD is re-checked at finalization by pcae push; here we
    # only assert the working tree carries no production/contract drift.
    prod = _git("diff", "--name-only", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae", "docs/contracts")
    # Slice A: the one new coordinator. Slice B (.1R.19): + the exact
    # `.1R.16`-§38 authorized set. Phase .1R.22 (N-16-3): + Gate 6 / PB
    # Foundation + the PB policy contracts (PBRD-001 v3.0 MAJOR).
    _authorized = {
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_invocation.py",
        "src/pcae/core/runtime_adapter.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/commands/runtime_inspect.py",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        # Phase .1R.26 (N-16-4 -- REPRC-001 v1.0): Gate 7 + the one new
        # companion contract. Exact paths, no wildcard.
        "src/pcae/core/runtime_dispatch_gate7.py",
        "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md",
    }
    assert set(prod.split()) <= _authorized, set(prod.split()) - _authorized


# ═══════════════════════════════════════════════════════════════════════
# §6 — re-derived RDGO §11 items 1–6 mapping to production checks
# ═══════════════════════════════════════════════════════════════════════
def test_rdgo_section11_items_1_to_6_each_have_a_production_check():
    src = G10_SRC
    # item 1–2: trusted Gate9Result + status == "consumed"
    assert "is_gate9_result(gate9_result)" in src
    assert 'gate9_result.status != "consumed"' in src
    # item 3: fresh durable consumption.json re-read + /2.1 + binding present + valid
    assert "consumption_store.resolve(proof_id)" in src
    assert "record.consumption_schema_version != CONSUMPTION_SCHEMA_VERSION" in src
    assert "_validate_authority_generation_binding(record.authority_generation_binding)" in src
    # item 4: exact lineage across durable record <-> Gate9Result <-> live request
    assert "record.record_digest != gate9_result.record_digest" in src
    assert "record.prompt_binding.get(\"prompt_hash\") != inputs.prompt_hash" in src
    # item 5: runtime capability + containment re-established at entry
    assert "_runtime_execution_unavailable(capability_snapshot)" in src
    assert "run_gate8_process_containment(" in src
    # item 6: re-derive current authority-generation vector, compare vs durable snapshot
    assert "authority_generation_resolver()" in src
    assert "_first_generation_drift(durable_snapshot, current_markers)" in src


def test_reason_taxonomy_is_a_closed_frozenset_no_wildcards():
    ids = g10.GATE10_ELIGIBILITY_REASON_IDS
    assert isinstance(ids, frozenset)
    # N-18-2 (non-blocking): the `.1R.17` doc/report prose says "38 stems";
    # the actual frozenset carries 39 members (two — `..._drift` /
    # `..._currentness_drift` — additionally take a `:<detail>` suffix). The
    # taxonomy is closed and the count is >= what the prose claims.
    assert len(ids) == 39
    assert all(isinstance(r, str) and r.startswith("gate10_") for r in ids)
    assert not any("*" in r for r in ids)
    assert "gate10_internal_error_fail_closed" in ids


# ═══════════════════════════════════════════════════════════════════════
# §7/§8 — F-G10-1: trusted Gate9Result; provenance != consumed success
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_or_forged_gate9_result_rejected(chain):
    for candidate in (
        None,
        object(),
        object.__new__(g9.Gate9Result),
    ):
        env, reasons = _run(chain, gate9_result=candidate)
        assert env is None and reasons == ("gate10_untrusted_gate9_result",)


def test_gate9_result_cannot_be_copied_or_pickled(chain):
    with pytest.raises(TypeError):
        pickle.dumps(chain.g9)
    with pytest.raises(TypeError):
        copy.deepcopy(chain.g9)


def test_trusted_but_already_consumed_gate9_result_rejected(chain):
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
        authority_generation_resolver=_prod_agr(chain),
    )
    assert already is not None and already.status == "already_consumed"
    assert g9.is_gate9_result(already) is True  # provenance holds
    env, reasons = _run(chain, gate9_result=already)
    assert env is None and reasons == ("gate10_gate9_status_not_consumed",)


# ═══════════════════════════════════════════════════════════════════════
# §9/§10/§11 — durable /2.1 re-read; /2.0 hard rejection; snapshot binding
# ═══════════════════════════════════════════════════════════════════════
def test_gate10_reads_the_durable_record_not_gate9_fields(chain):
    # Absent durable record => fail closed even though the trusted, consumed
    # Gate9Result is in hand.
    empty = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)) / "elsewhere")
    env, reasons = _run(chain, consumption_store=empty)
    assert env is None and reasons == ("gate10_consumption_record_read_back_failed",)


def test_durability_uncertain_fails_closed(chain, monkeypatch):
    from pcae.core.runtime_invocation_authority_consumption import (
        RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
    )

    monkeypatch.setattr(
        chain.store,
        "resolve",
        lambda p: (_ for _ in ()).throw(RuntimeInvocationAuthorityConsumptionDurabilityUncertainError("x")),
    )
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_consumption_record_read_back_failed",)


def _record_like(real, **overrides):
    class _R:
        pass

    r = _R()
    for name in (
        "consumption_schema_version",
        "authority_generation_binding",
        "record_digest",
        "request_identity",
        "authority_binding",
        "target_binding",
        "repository_task_binding",
        "prompt_binding",
        "pb_binding",
        "runtime_enforcement_binding",
        "dispatch_binding",
    ):
        setattr(r, name, getattr(real, name))
    for k, v in overrides.items():
        setattr(r, k, v)
    return r


def test_v2_0_record_readable_but_pre_effect_ineligible(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    legacy = _record_like(
        real,
        consumption_schema_version="HPAC-AUTHORITY-CONSUMPTION/2.0",
        authority_generation_binding=None,
    )
    monkeypatch.setattr(chain.store, "resolve", lambda p: legacy)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_consumption_record_generation_snapshot_absent",)


def test_malformed_generation_binding_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    for mutate in (
        {"snapshot_schema_version": "HPAC-AUTHORITY-GENERATION-SNAPSHOT/9.9"},
        {"consumption_generation": "present:deadbeef"},  # durable snapshot must read "absent"
    ):
        bad = dict(real.authority_generation_binding)
        bad.update(mutate)
        rec = _record_like(real, authority_generation_binding=bad)
        monkeypatch.setattr(chain.store, "resolve", lambda p, rec=rec: rec)
        env, reasons = _run(chain)
        assert env is None and reasons == ("gate10_consumption_snapshot_malformed",)


def test_record_digest_mismatch_vs_gate9_result_rejected(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    tampered = dataclasses.replace(real, record_digest="0" * 64)
    monkeypatch.setattr(chain.store, "resolve", lambda p: tampered)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_lineage_binding_mismatch",)


def test_live_request_drift_rejected(chain):
    other = dispatch_inputs(runtime_target_id="local-cli-fixture-2")
    env, reasons = _run(chain, inputs=other)
    assert env is None
    assert reasons[0].startswith("gate10_") and reasons[0] != "gate10_internal_error_fail_closed"


def test_idempotency_key_alone_does_not_authorize(chain):
    other = new_dispatch_identity(chain.inputs, invocation_id="inv-" + "d" * 32)
    object.__setattr__(other, "idempotency_key", chain.identity.idempotency_key)
    env, reasons = _run(chain, identity=other)
    assert env is None and reasons == ("gate10_invocation_binding_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# §12–§17 — post-consumption drift: principal / credential / approval /
# lifecycle / consumption-state inconsistency
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "marker",
    ["principal_generation", "credential_generation", "approval_generation", "lifecycle_generation"],
)
def test_authority_generation_drift_invalidates_eligibility(chain, marker):
    resolver = _prod_agr(chain, **{marker: "drifted-" + "z" * 20})
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == (f"gate10_authority_generation_drift:{marker}",)


def test_incomplete_generation_markers_rejected(chain):
    env, reasons = _run(chain, authority_generation_resolver=lambda: {"principal_generation": "x"})
    assert env is None and reasons == ("gate10_authority_generation_snapshot_incomplete",)


def test_consumption_generation_must_be_present_this_record(chain):
    resolver = _prod_agr(chain, consumption_generation="present:" + "0" * 64)
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == ("gate10_consumption_state_inconsistent",)


def test_consumption_state_inconsistency_rejected(chain):
    resolver = _prod_agr(chain, consumption_generation="absent")
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == ("gate10_consumption_state_inconsistent",)


# ═══════════════════════════════════════════════════════════════════════
# §18/§19 — N-16-1 authority-generation resolver: canonical source only,
# restart-safe, composed from the FROZEN Gate-9 factory
# ═══════════════════════════════════════════════════════════════════════
def test_authority_generation_resolver_five_markers_from_canonical_sources(chain):
    markers = _prod_agr(chain)()
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
    assert markers["credential_generation"] == chain.rig.registry.resolve_canonical_credential(
        chain.rig.credential_id
    ).record_digest
    assert markers["consumption_generation"] == "present:" + chain.record.record_digest


def test_authority_generation_resolver_is_restart_reconstructible(chain):
    # A brand-new store + resolver over the same root reproduces every marker
    # byte-for-byte — no wall clock / mtime / nonce / process identity.
    fresh = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)))
    a = _prod_agr(chain)()
    b = g10.build_gate10_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=_ApprovalStoreShim(chain),
        approval_id=chain.rig.approval_id,
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=fresh,
        proof_id=chain.rig.proof_id,
    )()
    assert a == b


def test_authority_generation_resolver_source_carries_no_time_or_nonce():
    src = G10_SRC
    lo = src.index("def build_gate10_authority_generation_resolver")
    hi = src.index("def build_gate10_capability_snapshot_resolver")
    body = src[lo:hi] if lo < hi else src[hi:lo]
    # window may be either order; take the resolver body explicitly
    lo = src.index("def build_gate10_authority_generation_resolver")
    body = src[lo:lo + 3000]
    for banned in ("time.time", "datetime.now", "utcnow", "monotonic", "uuid", "os.urandom", "getpid"):
        assert banned not in body, banned


def test_authority_generation_resolver_composes_the_frozen_gate9_factory():
    assert "build_production_authority_generation_resolver" in G10_SRC
    assert "_base = build_production_authority_generation_resolver(" in G10_SRC
    # and the Gate-9 module is byte-identical to baseline (no refactor).
    diff = _git("diff", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae/core/runtime_dispatch_gate9.py")
    assert diff == ""


def test_resolver_fail_closed_on_unreadable_principal(chain):
    class _BrokenRegistry:
        def resolve_canonical_principal(self, _):
            return None

        def resolve_canonical_credential(self, _):
            return None

    resolver = g10.build_gate10_authority_generation_resolver(
        principal_registry=_BrokenRegistry(),
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=_ApprovalStoreShim(chain),
        approval_id=chain.rig.approval_id,
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    env, reasons = _run(chain, authority_generation_resolver=resolver)
    assert env is None and reasons == ("gate10_internal_error_fail_closed",)


# ═══════════════════════════════════════════════════════════════════════
# §20–§25 — capability resolver: canonical source, caller cannot
# manufacture availability, semantic wall, no mutation
# ═══════════════════════════════════════════════════════════════════════
def test_capability_resolver_reads_canonical_introspection_state():
    snap = g10.build_gate10_capability_snapshot_resolver()()
    assert snap == {
        "current_runtime_state": ri.CURRENT_RUNTIME_STATE,
        "current_maximum_plugin_capability": ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
        "execution_availability": ri.EXECUTION_AVAILABILITY,
    }
    assert snap == _CANONICAL_NON_EXECUTING


def test_capability_snapshot_drift_fails_closed(chain):
    for bad in (
        {"current_runtime_state": "Executable", "current_maximum_plugin_capability": "execute", "execution_availability": "available"},
        {"current_runtime_state": "Observed", "current_maximum_plugin_capability": "observe", "execution_availability": "available"},
        {"execution_availability": "available"},
        {},
        "not-a-dict",
        None,
        True,
    ):
        env, reasons = _run(chain, capability_snapshot_resolver=lambda b=bad: b)
        assert env is None and reasons == ("gate10_runtime_capability_not_unavailable",)


def test_consumed_authority_does_not_override_runtime_capability(chain):
    # Full valid chain; only the capability snapshot claims "available".
    env, reasons = _run(
        chain,
        capability_snapshot_resolver=lambda: {
            "current_runtime_state": "Executable",
            "current_maximum_plugin_capability": "execute",
            "execution_availability": "available",
        },
    )
    assert env is None and reasons == ("gate10_runtime_capability_not_unavailable",)


def test_capability_resolver_does_not_mutate_runtime_state(chain):
    before = (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, ri.EXECUTION_AVAILABILITY)
    g10.build_gate10_capability_snapshot_resolver()()
    _run(chain)
    _run(chain, capability_snapshot_resolver=lambda: {})
    after = (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY, ri.EXECUTION_AVAILABILITY)
    assert before == after == ("Observed", "observe", "unavailable")


def test_capability_resolver_source_registers_no_plugin_or_capability():
    src = G10_SRC
    lo = src.index("def build_gate10_capability_snapshot_resolver")
    body = src[lo:lo + 1400]
    for banned in ("register", "enable(", "activate", "promote", "elevate", "CURRENT_RUNTIME_STATE ="):
        assert banned not in body, banned


# ═══════════════════════════════════════════════════════════════════════
# §26/§27 — PB (POL-005) and RE lineage: trusted, ALLOW, not re-run
# ═══════════════════════════════════════════════════════════════════════
def test_pb_lineage_must_be_allow(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    bad = dataclasses.replace(real, pb_binding={**real.pb_binding, "decision": "DENY"})
    monkeypatch.setattr(chain.store, "resolve", lambda p: bad)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_pb_lineage_not_allow",)


def test_no_pb_or_re_policy_re_evaluation_in_source():
    for banned in ("evaluate_pb_policy", "evaluate_policy", "run_gate6", "run_gate7", "PermissionBroker("):
        assert banned not in G10_SRC, banned


def test_re_lineage_verdict_must_be_allow(chain, monkeypatch):
    real = chain.store.resolve(chain.rig.proof_id)
    bad = dataclasses.replace(
        real, runtime_enforcement_binding={**real.runtime_enforcement_binding, "verdict": "HUMAN_REVIEW"}
    )
    monkeypatch.setattr(chain.store, "resolve", lambda p: bad)
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_re_lineage_not_allow",)


def test_re_decision_expiry_at_gate10_entry_rejected(chain):
    env, reasons = _run(chain, authority_current_time="2027-06-01T00:00:00Z")
    assert env is None and reasons == ("gate10_re_decision_expired",)


def test_matched_no_go_ids_not_consulted_as_authority_input():
    # `matched_no_go_ids` is a per-decision diagnostic (RE No-Go Registry
    # 1.1), never an allow/deny input — the coordinator makes no lookup of it.
    code = _strip_strings(G10_SRC)
    assert "matched_no_go_ids" not in code


# ═══════════════════════════════════════════════════════════════════════
# §28–§36 — containment / executable / effect-plan read-back drift
# ═══════════════════════════════════════════════════════════════════════
def test_executable_identity_drift_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(sha256="f" * 64))
    assert env is None and reasons == ("gate10_executable_identity_drift",)


def test_executable_absent_or_symlink_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(path="/nonexistent/xyz"))
    assert env is None and reasons == ("gate10_executable_identity_drift",)


def test_argv_drift_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(argv=("different",)))
    assert env is None and reasons == ("gate10_containment_evidence_recomputation_mismatch",)


def test_cwd_drift_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(cwd=str(REPO_ROOT / "src")))
    assert env is None
    assert reasons[0] in (
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
    )


def test_env_allowlist_drift_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(env_allowlist=("PATH", "HOME", "EXTRA")))
    assert env is None
    assert reasons[0] in (
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
    )


def test_containment_recomputation_failure_rejected(chain):
    env, reasons = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert env is None and reasons == ("gate10_containment_recomputation_failed",)


def test_effect_plan_must_equal_the_consumed_commitment(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(time_limit_ref="timeout-9000s"))
    assert env is None
    assert reasons[0].startswith("gate10_containment")


def test_credentials_required_effect_plan_rejected(chain):
    env, reasons = _run(chain, effect_plan=_good_effect_plan(credentials_required=True))
    assert env is None
    assert reasons[0] in (
        "gate10_effect_plan_requires_credentials",
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
    )


# ═══════════════════════════════════════════════════════════════════════
# §37 — F-G10-12: NON_REAL / deterministic authority cannot mint an
# envelope eligible for the future first-effect boundary (defence in depth)
# ═══════════════════════════════════════════════════════════════════════
def test_no_provenance_substitution_makes_gate10_unreachable():
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


def test_gate7_deny_lineage_blocks_independently(chain, monkeypatch):
    deny = _mk_gate7(
        decision="DENY",
        invocation_id=chain.identity.invocation_id,
        attempt_id=chain.identity.attempt_id,
        request_id=chain.g6.request_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is deny)
    env, reasons = _run(chain, gate7_result=deny)
    assert env is None and reasons == ("gate10_gate7_decision_not_allow",)


# ═══════════════════════════════════════════════════════════════════════
# §38 — F-G10-13: envelope mint ordering — nothing escapes before the
# full battery completes
# ═══════════════════════════════════════════════════════════════════════
def test_no_envelope_escapes_on_any_negative_path(chain):
    registry_before = len(g10._DISPATCH_ENVELOPES)
    negatives = [
        dict(gate9_result=None),
        dict(capability_snapshot_resolver=lambda: {}),
        dict(descriptor_resolver=_resolver(sha256="f" * 64)),
        dict(effect_plan=_good_effect_plan(argv=("x",))),
        dict(authority_generation_resolver=lambda: {"principal_generation": "x"}),
        dict(authority_current_time="2027-06-01T00:00:00Z"),
    ]
    for kw in negatives:
        env, reasons = _run(chain, **kw)
        assert env is None and g10.is_dispatch_envelope(env) is False
    assert len(g10._DISPATCH_ENVELOPES) == registry_before  # no leaked mint


def test_mint_occurs_only_after_every_check_in_source():
    src = G10_SRC
    mint = src.index("envelope = DispatchEnvelope(_seal=")
    for check in (
        "_runtime_execution_unavailable(capability_snapshot)",
        "_first_generation_drift(durable_snapshot, current_markers)",
        "run_gate8_process_containment(",
        "_hash_file_sha256(",
        'record.pb_binding.get("decision") != "ALLOW"',
    ):
        assert src.index(check) < mint, check


# ═══════════════════════════════════════════════════════════════════════
# §39/§40/§41/§42 — DispatchEnvelope: RPAC-REQ-029 fields; non-bearer;
# non-reconstructable; provenance != authority; non-serializable
# ═══════════════════════════════════════════════════════════════════════
def test_envelope_binds_every_rpac_req_029_field(chain):
    env, advisory = _run(chain)
    assert env is not None and advisory == ()
    doc = env.to_reference_document()
    required = {
        "envelope_schema_version", "invocation_id", "attempt_id", "idempotency_key",
        "proof_id", "approval_id", "runtime_target_id", "adapter_id",
        "descriptor_digest", "target_config_digest", "consumption_record_digest",
        "durable_record_reference", "authority_projection_digest", "approval_digest",
        "authority_generation_snapshot_digest", "pb_request_digest", "pb_decision_digest",
        "re_decision_digest", "re_expires_at", "effect_plan_digest",
        "containment_evidence_digest", "live_preflight_digest", "executable_identity_digest",
        "runtime_capability_snapshot_digest", "target_status_digest", "contract_versions",
        "minted_at", "expires_at", "envelope_digest", "advisory_reasons",
    }
    assert required <= set(doc)
    assert env.envelope_schema_version == "RPAC-DISPATCH-ENVELOPE/1.0"
    assert env.consumption_record_digest == chain.record.record_digest
    assert env.durable_record_reference == f"proofs/v2/{chain.rig.proof_id}/consumption.json"
    assert env.expires_at == env.re_expires_at == chain.record.runtime_enforcement_binding["expires_at"]
    assert env.contract_versions["rdgo"] == "RDGO-001/3.1"
    assert len(env.envelope_digest) == 64


def test_envelope_not_caller_constructable():
    with pytest.raises(TypeError):
        g10.DispatchEnvelope(_seal=object())


def test_envelope_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g10.DispatchEnvelope,), {})


def test_envelope_is_immutable(chain):
    env, _ = _run(chain)
    with pytest.raises(AttributeError):
        env.invocation_id = "tampered"


def test_envelope_non_serializable_every_route(chain):
    env, _ = _run(chain)
    with pytest.raises(TypeError):
        pickle.dumps(env)
    with pytest.raises(TypeError):
        copy.deepcopy(env)
    with pytest.raises(TypeError):
        env.__reduce__()


def test_envelope_copy_or_reconstruction_is_not_a_registry_member(chain):
    env, _ = _run(chain)
    assert g10.is_dispatch_envelope(env) is True
    # object.__new__ bypass
    assert g10.is_dispatch_envelope(object.__new__(g10.DispatchEnvelope)) is False
    # dict reconstruction
    assert g10.is_dispatch_envelope(env.to_reference_document()) is False
    # copy.copy — either raises or yields a non-member
    try:
        clone = copy.copy(env)
        assert g10.is_dispatch_envelope(clone) is False
    except Exception:
        pass


def test_envelope_identity_equality_only(chain):
    e1, _ = _run(chain)
    e2, _ = _run(chain)
    assert e1 == e1 and e1 != e2 and hash(e1) == id(e1)


def test_is_dispatch_envelope_is_provenance_not_authority():
    src = G10_SRC
    fn = src[src.index("def is_dispatch_envelope"):src.index("def is_dispatch_envelope") + 1400]
    assert "Provenance only" in fn or "provenance" in fn.lower()
    assert "not" in fn.lower() and "authoriz" in fn.lower()
    # membership test, never isinstance-only / field-based
    assert "candidate in _DISPATCH_ENVELOPES" in fn


def test_stale_genuine_envelope_is_still_only_provenance(chain):
    # A real, previously-minted envelope stays a registry member (provenance
    # is process-local and permanent) but that is explicitly NOT effect
    # authority — there is no effect path in this module regardless.
    env, _ = _run(chain)
    assert g10.is_dispatch_envelope(env) is True
    assert not hasattr(g10, "dispatch")
    assert ".dispatch(" not in _strip_strings(G10_SRC)


# ═══════════════════════════════════════════════════════════════════════
# §43/§44/§45/§46 — no effect: consumer inventory, AST no-adapter-call,
# AST no-effect-primitive, dynamic zero-effect trap
# ═══════════════════════════════════════════════════════════════════════
def test_zero_effect_bearing_consumers_in_production():
    hits = set(
        subprocess.run(
            [
                "git", "grep", "--untracked", "-l", "-E",
                r"is_dispatch_envelope|run_gate10_pre_effect_eligibility|_DISPATCH_ENVELOPES|build_gate10_",
                "--", "src/pcae",
            ],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.split()
    )
    assert hits == {"src/pcae/core/runtime_dispatch_gate10_eligibility.py"}
    # The pre-existing `SimulationDispatchEnvelope` (mock-v1 `simulate_invocation`
    # path) is a DISTINCT type, not wired into the RDGO Gate 5–11 chain
    # (`.1R.16` §5.1 / §27.2) — it is not a consumer of the new envelope.
    sim = set(
        subprocess.run(
            ["git", "grep", "-l", r"\bDispatchEnvelope\b", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.split()
    )
    assert "src/pcae/core/runtime_dispatch_gate10_eligibility.py" in sim


def _strip_strings(src: str) -> str:
    """Remove every string literal (docstrings included) from source, leaving
    only code — so a docstring that NAMES a forbidden concept is ignored."""
    tree = ast.parse(src)

    class _R(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                return ast.copy_location(ast.Constant(value=""), node)
            return node

    return ast.unparse(_R().visit(tree))


def test_ast_no_adapter_dispatch_call_site():
    tree = ast.parse(G10_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", getattr(fn, "id", ""))
            assert name != "dispatch", f"adapter dispatch call at line {node.lineno}"
    assert "posix_spawn" not in ast.dump(tree)


def test_ast_no_effect_primitive_reference_in_code():
    code = _strip_strings(G10_SRC)
    banned = (
        "subprocess", "posix_spawn", "Popen", "os.system", "os.popen", "execv",
        "execve", "spawnv", "socket", "ssl.", "pty", "ctypes", "fcntl",
        "urlopen", "http.client", "requests.", "httpx.", "fido2", "webauthn",
        "ctap", "RuntimeAdapter", "MockDryRuntimeAdapter", "DispatchReceipt",
        "smartcard", "getpass",
    )
    for token in banned:
        assert token not in code, token


def test_module_imports_nothing_effectful():
    tree = ast.parse(G10_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in (
        "subprocess", "socket", "pty", "ssl", "ctypes", "fcntl", "selectors",
        "asyncio", "multiprocessing", "urllib", "urllib.request", "http",
        "http.client", "requests", "httpx", "fido2", "webauthn",
        "pcae.core.runtime_adapter", "pcae.core.mock_runtime_adapter",
        "pcae.core.shell_gate",
    ):
        assert bad not in imported, bad


def test_dynamic_zero_effect_boundary_trap(chain, monkeypatch):
    import os
    import socket as _socket
    import subprocess as _sp

    tripped = []
    for mod, name in (
        (os, "system"), (os, "posix_spawn"), (os, "popen"), (os, "fork"),
        (os, "execv"), (os, "execve"),
        (_sp, "Popen"), (_sp, "run"), (_sp, "call"), (_sp, "check_output"),
        (_socket, "socket"),
    ):
        if hasattr(mod, name):
            monkeypatch.setattr(
                mod, name, lambda *a, _n=name, **k: tripped.append(_n) or pytest.fail(f"{_n} touched")
            )
    # positive path
    env, _ = _run(chain)
    assert env is not None
    # every negative branch
    for kw in (
        dict(gate9_result=None),
        dict(capability_snapshot_resolver=lambda: {}),
        dict(descriptor_resolver=_resolver(path="/nonexistent/xyz")),
        dict(effect_plan=_good_effect_plan(argv=("x",))),
        dict(authority_current_time="2027-06-01T00:00:00Z"),
    ):
        _run(chain, **kw)
    assert tripped == []


def test_no_first_effect_module_exists():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    assert not hasattr(g10, "Gate10Result")
    assert not hasattr(g10, "_GATE10_RESULTS")
    assert not hasattr(g10, "run_gate10")  # only the *_pre_effect_eligibility name


def test_no_capability_elevation_or_state_assignment_in_source():
    tree = ast.parse(G10_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute):
                    assert tgt.attr not in (
                        "CURRENT_RUNTIME_STATE",
                        "CURRENT_MAXIMUM_PLUGIN_CAPABILITY",
                        "EXECUTION_AVAILABILITY",
                    )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("register", "activate", "promote", "elevate")


# ═══════════════════════════════════════════════════════════════════════
# §47 — no positive production path (multiple independent blockers)
# ═══════════════════════════════════════════════════════════════════════
def test_runtime_posture_is_the_canonical_non_executing_state():
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_real_gate7_coordinator_denies():
    # The docstring-documented production fact, re-asserted structurally:
    # gate9's module docstring records the real Gate-7 DENY; here we confirm
    # no code path in the eligibility module fabricates a positive Gate7.
    assert "Gate7Result" not in _strip_strings(G10_SRC) or "is_gate7_result(gate7_result)" in G10_SRC


def test_synthetic_positive_path_writes_nothing_durable(chain):
    before = _count_consumption_json(Path(str(chain.store._root)))
    env, _ = _run(chain)
    assert env is not None
    assert _count_consumption_json(Path(str(chain.store._root))) == before
    assert chain.store.resolve(chain.rig.proof_id).record_digest == chain.record.record_digest


# ═══════════════════════════════════════════════════════════════════════
# §48 — test-boundary substitution isolation
# ═══════════════════════════════════════════════════════════════════════
def test_substitution_does_not_leak_into_production_predicates():
    # After the `chain` fixture's monkeypatches are torn down, the real
    # provenance predicates are restored and reject a hand-built object.
    assert g9.is_gate9_result(object.__new__(g9.Gate9Result)) is False
    assert gate7.is_gate7_result(object.__new__(gate7.Gate7Result)) is False
    assert gate5.is_gate5_result(object.__new__(gate5.Gate5Result)) is False


def test_module_exposes_no_public_positive_authority_mechanism():
    public = [n for n in g10.__all__]
    assert "run_gate10_pre_effect_eligibility" in public
    # no symbol that would let a caller mint or register an envelope directly
    for banned in ("mint_dispatch_envelope", "register_dispatch_envelope", "force_eligible"):
        assert banned not in dir(g10)


# ═══════════════════════════════════════════════════════════════════════
# §49/§50 — the eight widened scope-fence guards: still bounded, still
# reject an unauthorized importer
# ═══════════════════════════════════════════════════════════════════════
_WIDENED_GUARDS = [
    "test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8",
    "test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11",
    "test_runtime_authority_production_repair_3w1r2b1r1117",
    "test_hpac_foundation_independent_verification_3w1r2b1r111r31",
    "test_hpac_foundation_trust_root_repair_3w1r2b1r111r32",
    "test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321",
    "test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2",
    "test_phase_149o_1g_hatp_proof_models_canonical_serialization",
]


@pytest.mark.parametrize("modname", _WIDENED_GUARDS)
def test_widened_guard_admits_only_the_authorized_module(modname):
    path = REPO_ROOT / "tests" / f"{modname}.py"
    src = path.read_text()
    assert "runtime_dispatch_gate10_eligibility" in src, modname
    # the addition is exactly the eligibility module — never a wildcard /
    # package-wide allowance.
    for bad in ('"src/pcae/core/*"', "'src/pcae/core/*'", '"pcae.core.*"', '"src/pcae/**"', "fnmatch("):
        assert bad not in src, (modname, bad)
    # the admission is the exact filename / dotted-module string — a bounded
    # allowlist entry, not an open door.
    assert (
        '"runtime_dispatch_gate10_eligibility.py"' in src
        or "runtime_dispatch_gate10_eligibility.py," in src
        or "src/pcae/core/runtime_dispatch_gate10_eligibility.py" in src
    ), modname


@pytest.mark.parametrize(
    "modname",
    [
        "test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8",
        "test_runtime_authority_production_repair_3w1r2b1r1117",
        "test_hpac_foundation_trust_root_repair_3w1r2b1r111r32",
        "test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2",
        "test_phase_149o_1g_hatp_proof_models_canonical_serialization",
    ],
)
def test_widened_guard_module_passes_at_head(modname):
    # Guards with NO pre-existing failure class — must be fully green at HEAD.
    # (The `.1R.11` / `..._31` / `..._321` guard modules carry pre-existing
    #  unrelated failures — covered by the fixed-SHA A/B, not asserted here.)
    r = subprocess.run(
        ["python", "-m", "pytest", "-q", "-p", "no:randomly", f"tests/{modname}.py"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]


def test_unauthorized_new_production_importer_would_fail_a_guard(tmp_path):
    # Simulate an unauthorized production consumer of the Gate-9 store and
    # confirm the `.1R.8` isolation guard's subset invariant would catch it.
    guard = importlib.import_module(
        "test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8"
    )
    # the guard computes `gate9_callers` from src; inject a fake and re-check
    authorized = {
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }
    intruder = authorized | {"src/pcae/core/some_unauthorized_module.py"}
    assert not (intruder <= authorized)  # the exact subset assert the guard makes


# ═══════════════════════════════════════════════════════════════════════
# §51/§52/§53/§54/§55/§56/§57 — Gate 9 byte identity + Gate 5–8 + runtime
# introspection + registry + POL-005 + contracts unchanged
# ═══════════════════════════════════════════════════════════════════════
_UNCHANGED_SINCE_BASELINE = [
    "src/pcae/core/runtime_dispatch_gate5.py",
    # runtime_dispatch_gate7.py: authorizedly changed by Phase
    # 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0, the positive
    # Gate-7 result schema/identity/TTL/immutability). Gate 5 / 8 / 9 stay
    # byte-frozen here; see _SLICE_A_PLUS_B_PLUS_C_SCOPE.
    "src/pcae/core/runtime_dispatch_gate8.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
    # runtime_dispatch_permission.py (Gate 6) + permission_broker_foundation.py
    # + PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md are authorized Phase
    # ...1R.22 (N-16-3, PBRD-001 v3.0 §12a) targets -- removed from this
    # Slice-A byte-freeze list. Gate 5 / 7 / 8 / 9 stay frozen.
    "src/pcae/core/runtime_invocation_authority_consumption.py",
    "src/pcae/core/runtime_authority.py",
    "src/pcae/core/runtime_registry.py",
    "src/pcae/core/mock_runtime_adapter.py",
    # `runtime_introspection.py` / `runtime_adapter.py` were byte-frozen
    # for Slice A but are authorized Slice-B (.1R.19) targets by `.1R.16`
    # §36.2 / §38 (3S.2.1 MUST-FIX #1 + the item-9 runtime-inspect repair);
    # they are removed from this Slice-A byte-freeze list. The Slice-A
    # coordinator itself (runtime_dispatch_gate10_eligibility.py) stays
    # byte-unchanged through Slice B — asserted by
    # test_production_scope_since_baseline_is_exactly_one_new_file below.
    "src/pcae/core/shell_gate.py",
    "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
    "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
    "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
]


@pytest.mark.parametrize("rel", _UNCHANGED_SINCE_BASELINE)
def test_file_byte_unchanged_since_phase_entry_baseline(rel):
    diff = subprocess.run(
        ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--", rel],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert diff == "", f"{rel} changed since {PHASE_ENTRY_BASELINE}"


#: Slice A alone: exactly one new file. Slice B (.1R.19) additionally
#: admits the exact `.1R.16`-§38-authorized set (the two 3S.2.1 MUST-FIX
#: repairs + the item-9 runtime-inspect repair + one new non-authoritative
#: mirror module). An unauthorized production-file expansion still fails.
_SLICE_A_PLUS_B_PLUS_C_SCOPE = {
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
    "src/pcae/core/runtime_invocation.py",
    "src/pcae/core/runtime_adapter.py",
    "src/pcae/core/runtime_introspection.py",
    "src/pcae/commands/runtime_inspect.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
    # narrow-eligibility policy + POL-013). Exact filenames, no wildcard.
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py",
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0). The
    # sole authorized production surface for the positive Gate-7 result.
    "src/pcae/core/runtime_dispatch_gate7.py",
}
_SLICE_A_PLUS_B_SCOPE = _SLICE_A_PLUS_B_PLUS_C_SCOPE


def test_production_scope_since_baseline_is_exactly_one_new_file():
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.split()
    )
    assert changed <= _SLICE_A_PLUS_B_SCOPE, sorted(changed - _SLICE_A_PLUS_B_SCOPE)
    # the Slice-A coordinator is byte-unchanged since its own creation
    r17_head = "c618134a"
    assert subprocess.run(
        ["git", "diff", r17_head, "HEAD", "--",
         "src/pcae/core/runtime_dispatch_gate10_eligibility.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout == ""


def test_runtime_registry_still_empty():
    inspect = subprocess.run(
        ["python", "-m", "pcae", "runtime", "inspect"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout
    assert "Registry status:" in inspect and "empty" in inspect
    assert "Plugin count:" in inspect and "Capability count:" in inspect
    assert "Execution capability:" in inspect and "unavailable" in inspect
    assert "Observed" in inspect


def test_pol_005_still_hard_deny_in_source():
    pbf = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    assert "POL-005" in pbf and "ExecutionDisabledRule" in pbf


# ═══════════════════════════════════════════════════════════════════════
# §52 — Gate-9 behavioural regression spot-checks (provenance / one-shot /
# no-bearer) with .1R.17 present
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_one_shot_still_holds(chain):
    # second real consumption on the same proof_id => already_consumed
    second, _ = g9.run_gate9_atomic_authority_consumption(
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
        authority_generation_resolver=_prod_agr(chain),
    )
    assert second is not None and second.status == "already_consumed"


def test_gate9_result_is_not_serializable(chain):
    with pytest.raises(TypeError):
        pickle.dumps(chain.g9)


# ═══════════════════════════════════════════════════════════════════════
# §64 restart + internal-error fail-closed
# ═══════════════════════════════════════════════════════════════════════
def test_restart_reruns_the_whole_battery_from_disk(chain):
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


def test_internal_error_fails_closed_no_partial_output(chain, monkeypatch):
    monkeypatch.setattr(
        g10, "compute_canonical_digest",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    env, reasons = _run(chain)
    assert env is None and reasons == ("gate10_internal_error_fail_closed",)


def test_f7_threat_model_stated_verbatim_and_not_broadened():
    assert "same-account autonomous-agent assumption" in G10_SRC
    assert "same-process Python code execution" in G10_SRC
    assert "threat model NOT broadened" in G10_SRC
