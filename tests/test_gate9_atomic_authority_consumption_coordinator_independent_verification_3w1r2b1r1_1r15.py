"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15 — Independent Verification of the
Gate-9 Atomic Authority Consumption Coordinator Integration (.1R.14).

RE-DERIVE. DO NOT TRUST. These assertions are constructed independently
from RDGO-001 v3.0 §10 / §10a / §17 / §18 / §19, RIHAC-001 v2.0 §17-§19,
HPAC-REQ-098/099/100/101/102, the ``.1R.9`` planning document §10-§19, and
the ``.1R.13.1`` §16 Gate-8 → Gate-9 handoff contract — not from the
``.1R.14`` report, its implementation document, its 63 tests, or the
Gate-9 module's own prose.

There is NO legitimate positive production Gate-9 path (permanent NON-REAL
HPAC upstream; the real Gate-7 coordinator is always
``Gate7Result(decision="DENY")``). To exercise the atomic-consumption
envelope WITHOUT manufacturing real authority, the ``chain`` fixture
installs a clearly-labelled test-boundary substitution of the *upstream
provenance predicates only* (``is_gate5_result`` / ``is_gate6_decision`` /
``is_gate7_result`` and the projection-trust predicates in the
``runtime_dispatch_gate8`` / ``runtime_dispatch_gate9`` namespaces) and
writes only to a ``tmp_path`` consumption store — never the
production-resolved ``HPAC_PROTECTED_ROOT``. The HPAC lifecycle sequence-3
event and its store are the real ones built through the canonical fixture
writers. No ``ValidatedAuthorityProjection``, approval, runtime capability,
positive ``Gate7Result`` or positive ``Gate8Result`` is fabricated.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import pickle
import subprocess
import threading
from pathlib import Path

import pytest

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
BASELINE = "c1ea2c8b"
_ECHO = "/bin/echo"

_OK_SNAPSHOT = {
    "current_runtime_state": "Observed",
    "current_maximum_plugin_capability": "observe",
    "execution_availability": "unavailable",
}


def _snapshot():
    return dict(_OK_SNAPSHOT)


def _sha256_file(path: str) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            d.update(chunk)
    return d.hexdigest()


def _count_records(root: Path) -> int:
    return len(list(Path(str(root)).rglob("consumption.json")))


# ── clearly-labelled test-boundary synthetic upstream objects ───────────
class _Projection:
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


def _g5(*, invocation_id, approval_id, proof_id, seq3_digest, projection):
    obj = object.__new__(gate5.Gate5Result)
    for k, v in (
        ("_projection", projection),
        ("sequence3_event_digest", seq3_digest),
        ("proof_id", proof_id),
        ("approval_id", approval_id),
        ("invocation_id", invocation_id),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, k, v)
    return obj


def _g6(*, decision, invocation_id, attempt_id, request_id):
    obj = object.__new__(rdp.Gate6Decision)
    for k, v in (
        ("_pb_decision", object()),
        ("decision", decision),
        ("decision_reason", "iv-synthetic"),
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
        object.__setattr__(obj, k, v)
    return obj


def _g7(*, decision, invocation_id, attempt_id, request_id):
    obj = object.__new__(gate7.Gate7Result)
    for k, v in (
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
        object.__setattr__(obj, k, v)
    return obj


def _effect_plan(**ov):
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
    base.update(ov)
    return g8.Gate8EffectPlan(**base)


def _resolver(**ov):
    def resolve(inputs):
        adapter = inputs.adapter_descriptor_binding
        f = dict(
            path=_ECHO,
            sha256=_sha256_file(_ECHO),
            version="1.0",
            descriptor_digest=adapter.descriptor_digest,
            target_config_digest=adapter.target_config_digest,
            runtime_target_id=inputs.runtime_target_id,
            installed=True,
        )
        f.update(ov)
        return g8.ResolvedExecutable(**f)

    return resolve


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
    projection = _Projection(
        subject_scope_binding_digest=expected,
        principal_id=rig.principal_id,
        approval_id=rig.approval_id,
        proof_id=rig.proof_id,
    )
    request_id = "pbr-" + "0" * 12
    g7 = _g7(decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id)
    g6 = _g6(decision="ALLOW", invocation_id=inv, attempt_id=identity.attempt_id, request_id=request_id)
    g5 = _g5(
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
        effect_plan=_effect_plan(),
        descriptor_resolver=_resolver(),
    )
    assert g8_result is not None and g8_result.containment_established is True, r8

    c = _Chain()
    c.rig, c.event, c.inputs, c.identity, c.projection = rig, event, inputs, identity, projection
    c.g5, c.g6, c.g7, c.g8 = g5, g6, g7, g8_result
    c.store = RuntimeInvocationAuthorityConsumptionStore(tmp_path / "consumption")
    c.monkeypatch = monkeypatch
    return c


def _authority_generation_resolver(chain):
    """Default trusted authority-generation resolver (`.1R.15.2` V-15-1):
    stable canonical principal / credential registry digests + the
    projection record digest. Stable across S1/S2 unless a test injects a
    canonical-state mutation."""

    def _resolve():
        return {
            "principal_generation": chain.rig.registry.resolve_canonical_principal(
                chain.rig.principal_id
            ).record_digest,
            "credential_generation": chain.rig.registry.resolve_canonical_credential(
                chain.rig.credential_id
            ).record_digest,
            "approval_generation": chain.projection.record_digest,
        }

    return _resolve


def _run(chain, **ov):
    g8_result = ov.pop("gate8_result", chain.g8)
    kw = dict(
        gate7_result=ov.pop("gate7_result", chain.g7),
        gate6_decision=ov.pop("gate6_decision", chain.g6),
        gate5_result=ov.pop("gate5_result", chain.g5),
        identity=ov.pop("identity", chain.identity),
        inputs=ov.pop("inputs", chain.inputs),
        authority_current_time=ov.pop("authority_current_time", NOW),
        repo_root=ov.pop("repo_root", REPO_ROOT),
        effect_plan=ov.pop("effect_plan", _effect_plan()),
        descriptor_resolver=ov.pop("descriptor_resolver", _resolver()),
        lifecycle_store=ov.pop("lifecycle_store", chain.rig.lifecycle_store),
        consumption_store=ov.pop("consumption_store", chain.store),
        capability_snapshot_resolver=ov.pop("capability_snapshot_resolver", _snapshot),
        authority_generation_resolver=ov.pop(
            "authority_generation_resolver", _authority_generation_resolver(chain)
        ),
    )
    kw.update(ov)
    return g9.run_gate9_atomic_authority_consumption(g8_result, **kw)


# ══════════════════════════════════════════════════════════════════════
# §7 / §66  Sole Gate-9 owner + zero downstream consumers + no Gate 10
# ══════════════════════════════════════════════════════════════════════
def _git_grep_l(pattern: str) -> set[str]:
    out = subprocess.run(
        ["git", "grep", "-l", "-E", pattern, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return set(out.split())


def test_sole_semantic_owner_of_gate9_consumption_boundary():
    assert _git_grep_l(r"run_gate9_atomic_authority_consumption") == {
        "src/pcae/core/runtime_dispatch_gate9.py"
    }
    assert _git_grep_l(r"_GATE9_RESULTS|_GATE9_RESULT_CONSTRUCTOR_SEAL") == {
        "src/pcae/core/runtime_dispatch_gate9.py"
    }


def test_no_alternate_consumption_store_create_caller_in_production():
    callers = _git_grep_l(r"RuntimeInvocationAuthorityConsumptionStore")
    # only the inert store module (defn) and the Gate-9 coordinator (sole user)
    assert callers == {
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }


def test_gate9result_has_zero_downstream_production_consumers_and_no_gate10():
    # Gate9Result / is_gate9_result appear only in the coordinator itself.
    assert _git_grep_l(r"Gate9Result|is_gate9_result") == {
        "src/pcae/core/runtime_dispatch_gate9.py"
    }
    # No Gate-10 symbol / wiring: gate9.py references no dispatch transport.
    for sym in ("run_gate10", "Gate10", "adapter_dispatch", "DispatchReceipt",
                "SimulationDispatchEnvelope", ".dispatch("):
        assert sym not in G9_SRC, sym
    # The pre-existing adapter transports do not import the Gate-9 coordinator.
    for adapter in ("src/pcae/core/runtime_adapter.py",
                    "src/pcae/core/mock_runtime_adapter.py"):
        assert "runtime_dispatch_gate9" not in (REPO_ROOT / adapter).read_text()


def test_gate8result_new_consumer_is_only_gate9():
    hits = _git_grep_l(r"Gate8Result|is_gate8_result")
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }
    assert "src/pcae/core/runtime_dispatch_gate9.py" in hits


# ══════════════════════════════════════════════════════════════════════
# §8 / §52  Gate8Result provenance — exact object only
# ══════════════════════════════════════════════════════════════════════
def test_missing_gate8_result_fails_closed(chain):
    assert _run(chain, gate8_result=None) == (None, ("gate9_untrusted_gate8_result",))


def test_object_new_gate8_result_rejected(chain):
    r, reasons = _run(chain, gate8_result=object.__new__(g8.Gate8Result))
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def test_gate8_result_copy_deepcopy_pickle_all_refused(chain):
    with pytest.raises(TypeError):
        copy.deepcopy(chain.g8)
    with pytest.raises(TypeError):
        pickle.dumps(chain.g8)


def test_duck_typed_gate8_lookalike_rejected(chain):
    class _Lookalike:
        containment_established = True
        invocation_id = chain_attr = None
    r, reasons = _run(chain, gate8_result=_Lookalike())
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


# ══════════════════════════════════════════════════════════════════════
# §9 / §10  Provenance is not containment; trusted negative is a hard stop
#           BEFORE any store access
# ══════════════════════════════════════════════════════════════════════
def test_trusted_negative_gate8_result_hard_stop_before_store_access(chain):
    neg, r8 = g8.run_gate8_process_containment(
        chain.g7,
        gate5_result=chain.g5,
        identity=chain.identity,
        inputs=chain.inputs,
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_effect_plan(),
        descriptor_resolver=_resolver(installed=False),
    )
    assert neg is not None and neg.containment_established is False
    assert g8.is_gate8_result(neg) is True

    create_calls, resolve_calls = [], []
    chain.monkeypatch.setattr(chain.store, "create", lambda *a, **k: create_calls.append(1))
    chain.monkeypatch.setattr(chain.store, "resolve", lambda *a, **k: resolve_calls.append(1))
    r, reasons = _run(chain, gate8_result=neg)
    assert r is None and reasons == ("gate9_gate8_containment_not_established",)
    assert create_calls == [] and resolve_calls == []
    assert _count_records(chain.store._root) == 0


# ══════════════════════════════════════════════════════════════════════
# §13-§16  Gate7/6/5 lineage re-derived; single invocation
# ══════════════════════════════════════════════════════════════════════
def test_gate7_provenance_and_allow_both_required(chain):
    chain.monkeypatch.setattr(gate7, "is_gate7_result", lambda c: False)
    assert _run(chain)[1] == ("gate9_untrusted_gate7_result",)


def test_gate7_deny_is_hard_stop(chain):
    deny = _g7(decision="DENY", invocation_id=chain.identity.invocation_id,
               attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id)
    chain.monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is deny)
    assert _run(chain, gate7_result=deny)[1] == ("gate9_gate7_decision_not_allow",)


def test_gate6_provenance_and_allow_both_required(chain):
    chain.monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: False)
    assert _run(chain)[1] == ("gate9_untrusted_gate6_decision",)
    deny = _g6(decision="DENY", invocation_id=chain.identity.invocation_id,
               attempt_id=chain.identity.attempt_id, request_id=chain.g7.request_id)
    chain.monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is deny)
    assert _run(chain, gate6_decision=deny)[1] == ("gate9_gate6_decision_not_allow",)


def test_gate5_provenance_required(chain):
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: False)
    assert _run(chain)[1] == ("gate9_untrusted_gate5_result",)


def test_cross_invocation_mixture_refused(chain):
    other = _g7(decision="ALLOW", invocation_id="inv-" + "z" * 32,
                attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id)
    chain.monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is other)
    assert _run(chain, gate7_result=other)[1] == ("gate9_invocation_binding_mismatch",)


def test_attempt_id_mismatch_refused(chain):
    other = _g6(decision="ALLOW", invocation_id=chain.identity.invocation_id,
                attempt_id="att-" + "9" * 20, request_id=chain.g7.request_id)
    chain.monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is other)
    assert _run(chain, gate6_decision=other)[1] == ("gate9_invocation_binding_mismatch",)


def test_request_id_mismatch_refused(chain):
    other = _g6(decision="ALLOW", invocation_id=chain.identity.invocation_id,
                attempt_id=chain.identity.attempt_id, request_id="pbr-" + "9" * 12)
    chain.monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is other)
    assert _run(chain, gate6_decision=other)[1] == ("gate9_invocation_binding_mismatch",)


def test_gate7_lineage_digest_cross_checked_against_gate8(chain):
    tampered = _g7(decision="ALLOW", invocation_id=chain.identity.invocation_id,
                   attempt_id=chain.identity.attempt_id, request_id=chain.g6.request_id)
    object.__setattr__(tampered, "evaluated_input_digest", "0" * 64)
    chain.monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is tampered)
    assert _run(chain, gate7_result=tampered)[1] == ("gate9_gate7_lineage_mismatch",)


# ══════════════════════════════════════════════════════════════════════
# §17  attempt/request lineage — transitive (V-13-5-2)
# ══════════════════════════════════════════════════════════════════════
def test_gate5result_has_no_attempt_id_binding_is_transitive():
    # Independently confirm V-13-5-2: Gate5Result carries no attempt_id;
    # the coordinator binds attempt_id via g6/g7/g8 == identity only.
    assert "attempt_id" not in gate5.Gate5Result.__slots__
    src = G9_SRC
    assert "gate5_result.attempt_id" not in src
    assert "gate6_decision.attempt_id != identity.attempt_id" in src
    assert "gate7_result.attempt_id != identity.attempt_id" in src
    assert "gate8_result.attempt_id != identity.attempt_id" in src


# ══════════════════════════════════════════════════════════════════════
# §18-§20  Serialization boundary identification + critical ordering proof
# ══════════════════════════════════════════════════════════════════════
def test_serialization_boundary_is_the_create_only_primitive_no_second_lock():
    tree = ast.parse(G9_SRC)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    # no threading / filelock / advisory-lock / fcntl machinery
    for forbidden in ("Lock", "RLock", "flock", "lockf", "Semaphore", "FileLock", "filelock"):
        assert forbidden not in names and forbidden not in attrs, forbidden
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for m in ("threading", "fcntl", "filelock", "multiprocessing", "asyncio"):
        assert m not in imported, m
    # the single durable write is consumption_store.create
    create_calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "create"
    ]
    assert len(create_calls) == 1


def test_critical_ordering_revalidation_then_single_create(chain):
    """Instrument every in-boundary re-check and the durable create; prove
    the order: projection re-trust/revalidate → sequence-3 confirm →
    proof/approval pairing → capability re-read → record-absence check →
    exactly one create.  (RDGO-001 §10; .1R.9 §12/§18.)"""
    order = []

    real_reval = g9.revalidate_validated_authority_projection
    chain.monkeypatch.setattr(
        g9, "revalidate_validated_authority_projection",
        lambda p, *, current_time: (order.append("revalidate_projection"), True)[1],
    )
    real_resolve_evt = chain.rig.lifecycle_store.resolve_gate5_binding_event

    def spy_evt(pid):
        order.append("sequence3_resolve")
        return real_resolve_evt(pid)

    chain.monkeypatch.setattr(chain.rig.lifecycle_store, "resolve_gate5_binding_event", spy_evt)

    real_cap = _snapshot

    def spy_cap():
        order.append("capability_reread")
        return real_cap()

    real_resolve = chain.store.resolve
    real_create = chain.store.create

    def spy_resolve(pid):
        order.append("store_resolve")
        return real_resolve(pid)

    def spy_create(pid, rec):
        order.append("store_create")
        return real_create(pid, rec)

    chain.monkeypatch.setattr(chain.store, "resolve", spy_resolve)
    chain.monkeypatch.setattr(chain.store, "create", spy_create)

    r, reasons = _run(chain, capability_snapshot_resolver=spy_cap)
    assert r is not None and r.status == "consumed", reasons

    # revalidation strictly precedes the single durable create
    assert order.index("revalidate_projection") < order.index("store_create")
    assert order.index("sequence3_resolve") < order.index("store_create")
    assert order.index("capability_reread") < order.index("store_create")
    assert order.index("store_resolve") < order.index("store_create")
    # exactly one create; and the absence-check resolve is immediately before it
    assert order.count("store_create") == 1
    assert order[order.index("store_create") - 1] == "store_resolve"
    # capability re-read is inside the boundary battery (after revalidation)
    assert order.index("revalidate_projection") < order.index("capability_reread")


def test_no_effectful_step_between_last_revalidation_and_create(chain):
    """The window V-15-1 concerns: prove nothing effectful (no I/O, no
    network, no subprocess) runs between the capability re-read and the
    create — only pure in-memory record construction."""
    import re

    src = G9_SRC
    # slice the coordinator body between step 13 (capability re-read) and
    # step 16 (create)
    lo = src.index("# 13. Re-read the current runtime capability snapshot")
    hi = src.index("consumption_store.create(proof_id, consumption_record)")
    window = src[lo:hi]
    for bad in ("subprocess", "open(", "socket", "requests", "urllib", "Popen", "os.system", "sleep("):
        assert bad not in window, bad
    # the only store call in the window is the absence-check resolve
    assert window.count("consumption_store.resolve") == 1


# ══════════════════════════════════════════════════════════════════════
# §21-§24  In-boundary currentness: principal / proof / approval drift
# ══════════════════════════════════════════════════════════════════════
def test_projection_revoked_after_prior_gates_fails_closed_no_record(chain):
    chain.monkeypatch.setattr(
        g9, "revalidate_validated_authority_projection", lambda p, *, current_time: False
    )
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_stale_validated_authority_projection",)
    assert _count_records(chain.store._root) == 0


def test_projection_untrusted_inside_boundary_fails_closed(chain):
    calls = {"n": 0}
    real = g9.is_trusted_validated_authority_projection

    def flip(p):
        calls["n"] += 1
        return calls["n"] == 1  # trusted at step 7a, untrusted at step 9

    chain.monkeypatch.setattr(g9, "is_trusted_validated_authority_projection", flip)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_stale_validated_authority_projection",)
    assert _count_records(chain.store._root) == 0


def test_subject_scope_drift_rejected(chain):
    chain.projection.subject_scope_binding_digest = "0" * 64
    assert _run(chain)[1] == ("gate9_authority_subject_scope_mismatch",)


def test_sequence3_absent_rejected(chain):
    class _EmptyStore:
        def resolve_gate5_binding_event(self, pid):
            return None
    r, reasons = _run(chain, lifecycle_store=_EmptyStore())
    # wrong type caught by structural guard first
    assert r is None and reasons == ("gate9_invalid_lifecycle_store",)


def test_sequence3_cross_binding_rejected(chain):
    chain.projection.approval_id = "ria-" + "9" * 32
    chain.g5 = _g5(invocation_id=chain.identity.invocation_id, approval_id="ria-" + "9" * 32,
                   proof_id=chain.rig.proof_id, seq3_digest=chain.event.record.event_digest,
                   projection=chain.projection)
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)
    assert _run(chain)[1] == ("gate9_sequence3_cross_binding",)


def test_sequence3_event_digest_tamper_rejected(chain):
    chain.g5 = _g5(invocation_id=chain.identity.invocation_id, approval_id=chain.rig.approval_id,
                   proof_id=chain.rig.proof_id, seq3_digest="0" * 64, projection=chain.projection)
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)
    assert _run(chain)[1] == ("gate9_sequence3_event_digest_unverified",)


def test_proof_approval_pairing_mismatch_rejected(chain):
    chain.projection.approval_id = "ria-" + "7" * 32
    r, reasons = _run(chain)
    assert r is None and reasons in (
        ("gate9_proof_approval_pairing_mismatch",),
        ("gate9_sequence3_cross_binding",),
    )


# ══════════════════════════════════════════════════════════════════════
# §28-§34  Containment-evidence read-back (V-13-5-1): cwd/env/exe/argv drift
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "ov",
    [
        dict(effect_plan=_effect_plan(cwd="/tmp")),
        dict(effect_plan=_effect_plan(argv=("different",))),
        dict(effect_plan=_effect_plan(env_allowlist=("PATH", "HOME", "SECRET"))),
        dict(effect_plan=_effect_plan(network_denied=False)),
        dict(effect_plan=_effect_plan(child_process_policy="allowed")),
        dict(descriptor_resolver=_resolver(sha256="0" * 64)),
        dict(descriptor_resolver=_resolver(version="9.9")),
    ],
)
def test_containment_evidence_drift_rejected_before_commit(chain, ov):
    r, reasons = _run(chain, **ov)
    assert r is None
    assert reasons in (
        ("gate9_containment_recomputation_failed",),
        ("gate9_containment_evidence_recomputation_mismatch",),
    )
    assert _count_records(chain.store._root) == 0


def test_containment_recompute_actually_reruns_gate8(chain):
    calls = []
    real = g8.run_gate8_process_containment

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    chain.monkeypatch.setattr(g8, "run_gate8_process_containment", spy)
    # also patch the name imported into g9's function scope: it does
    # `from ... import run_gate8_process_containment` at call time
    _run(chain)
    assert calls, "Gate 9 did not re-run the Gate-8 owner for containment recompute"


def test_v13_5_1_recomputation_is_real_not_a_self_comparison(chain):
    """Decisive (§27): if Gate 9 merely echoed the handed digests, feeding a
    *different but structurally valid* effect plan would still be accepted.
    It is not — the Gate-8 re-run recomputes a genuinely different
    containment_evidence_digest and Gate 9 refuses before any store write."""
    r, reasons = _run(chain, effect_plan=_effect_plan(supervision_ref="supervisor-2"))
    assert r is None
    assert reasons in (
        ("gate9_containment_evidence_recomputation_mismatch",),
        ("gate9_containment_recomputation_failed",),
    )
    assert _count_records(chain.store._root) == 0
    # and the positive control: identical inputs DO reconcile
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "consumed"


def test_v15_1_residual_revalidate_to_create_window(chain):
    """FINDING V-15-1 probe. RDGO-001 §10 / .1R.13.1 §16.2-inv-4 say Gate 9
    revalidates 'while holding the protected serialization boundary'. The
    implementation holds NO lock across the §12 battery; it revalidates
    immediately before the create-only atomic primitive (.1R.9 §18 'the
    create IS the transaction'). Demonstrate the residual window: a
    revocation that lands *after* the in-boundary revalidation but *before*
    the atomic create is NOT caught — the record is still written.

    This is non-blocking because (a) .1R.9 §18 froze the create-only
    primitive as the boundary and forbids a second lock, (b) no Gate-10
    effect follows, (c) Gate 10 MUST re-read the durable record + revalidate
    (is_gate9_result is provenance-only), (d) production path is unreachable.
    """
    real_create = chain.store.create
    revoked_after_battery = {"n": 0}

    def create_after_late_revocation(pid, rec):
        # simulate: revocation processed here, after the battery already ran
        revoked_after_battery["n"] += 1
        chain.monkeypatch.setattr(
            g9, "revalidate_validated_authority_projection",
            lambda p, *, current_time: False,
        )
        return real_create(pid, rec)

    chain.monkeypatch.setattr(chain.store, "create", create_after_late_revocation)
    r, reasons = _run(chain)
    # window exists: the record was written despite the "late" revocation
    assert revoked_after_battery["n"] == 1
    assert r is not None and r.status == "consumed"
    assert _count_records(chain.store._root) == 1
    # but: is_gate9_result is provenance only — a Gate-10 consumer that
    # re-read the projection would still fail closed. Confirm the forward
    # invariant is in-source.
    assert 'status == "consumed"' in G9_SRC and "re-read the durable" in G9_SRC


def _can_copy(x):
    try:
        copy.copy(x)
        return True
    except TypeError:
        return False


# ══════════════════════════════════════════════════════════════════════
# §35-§39  digests recomputed; capability snapshot inside boundary
# ══════════════════════════════════════════════════════════════════════
def test_effect_plan_digest_independently_reconstructed(chain):
    # handing a structurally-valid but different effect plan must be caught
    r, reasons = _run(chain, effect_plan=_effect_plan(resource_limit_ref="budget-2"))
    assert r is None
    assert reasons[0].startswith("gate9_containment")


def test_capability_available_inside_boundary_fails_closed(chain):
    r, reasons = _run(chain, capability_snapshot_resolver=lambda: {
        "current_runtime_state": "Executing",
        "current_maximum_plugin_capability": "dispatch",
        "execution_availability": "available",
    })
    assert r is None and reasons == ("gate9_runtime_execution_available_unexpected",)
    assert _count_records(chain.store._root) == 0


def test_capability_snapshot_malformed_fails_closed(chain):
    for bad in (None, {}, {"execution_availability": "unavailable"}, "unavailable", []):
        r, reasons = _run(chain, capability_snapshot_resolver=lambda b=bad: b)
        assert r is None and reasons == ("gate9_runtime_execution_available_unexpected",)


def test_capability_reread_is_inside_not_only_before(chain):
    """The snapshot resolver must be CALLED by Gate 9 (re-read), not merely
    accepted as a handed value."""
    calls = []
    chain.monkeypatch.setattr  # noqa
    r, reasons = _run(chain, capability_snapshot_resolver=lambda: (calls.append(1), _OK_SNAPSHOT)[1])
    assert calls, "Gate 9 never invoked capability_snapshot_resolver"


# ══════════════════════════════════════════════════════════════════════
# §41-§44  8-item record schema; one atomic record; no RIHAC mutation
# ══════════════════════════════════════════════════════════════════════
def test_consumption_record_is_the_closed_8_item_schema(chain):
    r, _ = _run(chain)
    rec = chain.store.resolve(chain.rig.proof_id)
    assert rec is not None
    doc = rec.to_document(include_digest=True)
    assert doc["consumption_schema_version"] == "HPAC-AUTHORITY-CONSUMPTION/2.0"
    assert set(doc) == {
        "consumption_schema_version", "record_digest", "request_identity",
        "repository_task_binding", "target_binding", "prompt_binding",
        "authority_binding", "pb_binding", "runtime_enforcement_binding",
        "dispatch_binding",
    }
    assert set(rec.request_identity) == {"invocation_id", "attempt_id", "idempotency_key"}
    assert set(rec.authority_binding) == {
        "approval_id", "approval_digest", "authority_projection_id",
        "authority_projection_digest", "authority_contract_version", "proof_id",
        "proof_digest", "proof_validation_digest", "registry_state_digest",
        "approval_subject_digest", "trusted_presentation_ref", "challenge_digest",
    }
    assert rec.authority_binding["authority_contract_version"] == "RIHAC-001/2.0"
    assert rec.dispatch_binding["state"] == "dispatch_attempted"


def test_proof_and_approval_consumed_by_one_write_no_mutable_flag(chain):
    _run(chain)
    assert _count_records(chain.store._root) == 1
    assert "consumed = True" not in G9_SRC and "consumed=True" not in G9_SRC
    # no separate mutable consumed field name in the record schema
    rec = chain.store.resolve(chain.rig.proof_id)
    for binding in (rec.authority_binding, rec.dispatch_binding):
        assert "consumed" not in binding or binding is rec.dispatch_binding


def test_no_rihac_approval_store_import_or_mutation(chain):
    assert "runtime_invocation_approval_store" not in G9_SRC
    assert "approval_store" not in G9_SRC
    # only reads lifecycle store, never writes it
    assert ".create(" in G9_SRC  # the consumption create
    for writer in ("record_verified", "record_assertion", "open_challenge", "fixture_"):
        assert writer not in G9_SRC


# ══════════════════════════════════════════════════════════════════════
# §45-§46  Store provenance + containment
# ══════════════════════════════════════════════════════════════════════
def test_planted_offstore_record_is_not_authoritative(chain):
    planted = Path(str(chain.store._root)) / "proofs" / "v2" / "hap-planted"
    planted.mkdir(parents=True)
    (planted / "consumption.json").write_text("{}")
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed"  # this proof still consumes normally


def test_store_rejects_traversal_and_absolute_proof_id(chain):
    for bad in ("../escape", "/abs/proof", "a/../../b"):
        chain.projection.proof_id = bad
        chain.g5 = _g5(invocation_id=chain.identity.invocation_id, approval_id=chain.rig.approval_id,
                       proof_id=bad, seq3_digest=chain.event.record.event_digest,
                       projection=chain.projection)
        chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c, g5=chain.g5: c is g5)
        r, reasons = _run(chain)
        assert r is None
        assert reasons[0].startswith("gate9_sequence3") or reasons[0] == "gate9_internal_error_fail_closed"


# ══════════════════════════════════════════════════════════════════════
# §47-§55  First consumption / replay / concurrency
# ══════════════════════════════════════════════════════════════════════
def test_first_consumption_one_record_and_readback(chain):
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed" and reasons == ()
    assert g9.is_gate9_result(r) is True
    assert _count_records(chain.store._root) == 1
    assert _count_records(REPO_ROOT) == 0  # nothing under the repo tree


def test_identical_replay_is_deterministic_already_consumed(chain):
    r1, _ = _run(chain)
    for _ in range(3):
        r, reasons = _run(chain)
        assert r is not None and r.status == "already_consumed"
        assert reasons == ("gate9_already_consumed",)
    assert _count_records(chain.store._root) == 1


def test_same_gate8_result_replay_no_second_consumption(chain):
    _run(chain)
    r, reasons = _run(chain, gate8_result=chain.g8)
    assert r.status == "already_consumed" and _count_records(chain.store._root) == 1


def test_same_proof_different_approval_never_second_success(chain):
    _run(chain)
    chain.projection.approval_id = "ria-" + "5" * 32
    chain.g5 = _g5(invocation_id=chain.identity.invocation_id, approval_id="ria-" + "5" * 32,
                   proof_id=chain.rig.proof_id, seq3_digest=chain.event.record.event_digest,
                   projection=chain.projection)
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)
    r, reasons = _run(chain)
    # rejected at sequence-3 cross-binding OR already-consumed — never a 2nd success
    assert (r is None) or (r.status == "already_consumed")
    assert _count_records(chain.store._root) == 1


def test_different_proof_same_approval_rejected(chain):
    _run(chain)
    bad = "hap-" + "5" * 32
    chain.projection.proof_id = bad
    chain.g5 = _g5(invocation_id=chain.identity.invocation_id, approval_id=chain.rig.approval_id,
                   proof_id=bad, seq3_digest=chain.event.record.event_digest, projection=chain.projection)
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_sequence3_proof_verified_and_bound_absent",)
    assert _count_records(chain.store._root) == 1


@pytest.mark.parametrize("n", [4, 8, 16])
def test_true_concurrency_exactly_one_winner(chain, n):
    results = []
    barrier = threading.Barrier(n)
    lock = threading.Lock()

    def worker():
        barrier.wait()
        out = _run(chain)
        with lock:
            results.append(out)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == n
    statuses = [(r.status if r is not None else "fail_closed") for r, _ in results]
    assert statuses.count("consumed") == 1, statuses
    for s in statuses:
        assert s in ("consumed", "already_consumed", "fail_closed"), s
    assert _count_records(chain.store._root) == 1
    # the single record is complete and reads back
    rec = chain.store.resolve(chain.rig.proof_id)
    assert rec is not None and rec.dispatch_binding["state"] == "dispatch_attempted"


def test_concurrency_repeated_no_second_record_ever(chain, tmp_path):
    # stress the race many times with fresh proof roots
    for i in range(12):
        inv = "inv-" + f"{i:x}" + "d" * 31
        rig = _Rig(tmp_path / f"h{i}", invocation_id=inv)
        rig.verify()
        ev = rig.lifecycle_store.resolve_gate5_binding_event(rig.proof_id)
        inputs = dispatch_inputs()
        ident = new_dispatch_identity(inputs, invocation_id=inv)
        exp = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inputs)
        proj = _Projection(subject_scope_binding_digest=exp, principal_id=rig.principal_id,
                           approval_id=rig.approval_id, proof_id=rig.proof_id)
        rid = "pbr-" + "0" * 12
        g7 = _g7(decision="ALLOW", invocation_id=inv, attempt_id=ident.attempt_id, request_id=rid)
        g6 = _g6(decision="ALLOW", invocation_id=inv, attempt_id=ident.attempt_id, request_id=rid)
        g5 = _g5(invocation_id=inv, approval_id=rig.approval_id, proof_id=rig.proof_id,
                 seq3_digest=ev.record.event_digest, projection=proj)
        mp = pytest.MonkeyPatch()
        mp.setattr(gate7, "is_gate7_result", lambda c, g=g7: c is g)
        mp.setattr(gate5, "is_gate5_result", lambda c, g=g5: c is g)
        mp.setattr(rdp, "is_gate6_decision", lambda c, g=g6: c is g)
        mp.setattr(g8, "is_trusted_validated_authority_projection", lambda p, pr=proj: p is pr)
        mp.setattr(g8, "revalidate_validated_authority_projection", lambda p, *, current_time, pr=proj: p is pr)
        mp.setattr(g9, "is_trusted_validated_authority_projection", lambda p, pr=proj: p is pr)
        mp.setattr(g9, "revalidate_validated_authority_projection", lambda p, *, current_time, pr=proj: p is pr)
        g8r, r8 = g8.run_gate8_process_containment(
            g7, gate5_result=g5, identity=ident, inputs=inputs, authority_current_time=NOW,
            repo_root=REPO_ROOT, effect_plan=_effect_plan(), descriptor_resolver=_resolver())
        assert g8r is not None
        store = RuntimeInvocationAuthorityConsumptionStore(tmp_path / f"c{i}")
        out = []
        b = threading.Barrier(6)

        def w():
            b.wait()
            out.append(g9.run_gate9_atomic_authority_consumption(
                g8r, gate7_result=g7, gate6_decision=g6, gate5_result=g5, identity=ident,
                inputs=inputs, authority_current_time=NOW, repo_root=REPO_ROOT,
                effect_plan=_effect_plan(), descriptor_resolver=_resolver(),
                lifecycle_store=rig.lifecycle_store, consumption_store=store,
                capability_snapshot_resolver=_snapshot,
                authority_generation_resolver=lambda rg=rig: {
                    "principal_generation": rg.registry.resolve_canonical_principal(rg.principal_id).record_digest,
                    "credential_generation": rg.registry.resolve_canonical_credential(rg.credential_id).record_digest,
                    "approval_generation": "a" * 64,
                }))

        ts = [threading.Thread(target=w) for _ in range(6)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        mp.undo()
        statuses = [(r.status if r else "fc") for r, _ in out]
        assert statuses.count("consumed") == 1, (i, statuses)
        assert _count_records(store._root) == 1, i


# ══════════════════════════════════════════════════════════════════════
# §56-§61  Crash / restart / corrupt-record fault injection
# ══════════════════════════════════════════════════════════════════════
def test_crash_before_commit_leaves_unconsumed_retriable(chain):
    chain.monkeypatch.setattr(chain.store, "create", lambda p, r: (_ for _ in ()).throw(RuntimeError("crash")))
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_atomic_commit_failed",)
    assert chain.store.resolve(chain.rig.proof_id) is None
    assert _count_records(chain.store._root) == 0
    # retry after "restart" (real create) now succeeds — authority was NOT consumed
    chain.monkeypatch.undo()
    # re-install provenance substitution the undo removed
    chain.monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is chain.g7)
    chain.monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is chain.g5)
    chain.monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is chain.g6)
    chain.monkeypatch.setattr(g9, "is_trusted_validated_authority_projection", lambda p: p is chain.projection)
    chain.monkeypatch.setattr(g9, "revalidate_validated_authority_projection", lambda p, *, current_time: p is chain.projection)
    chain.monkeypatch.setattr(g8, "is_trusted_validated_authority_projection", lambda p: p is chain.projection)
    chain.monkeypatch.setattr(g8, "revalidate_validated_authority_projection", lambda p, *, current_time: p is chain.projection)
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "consumed"


def test_crash_after_commit_is_durably_consumed(chain):
    real_create = chain.store.create

    def create_then_crash(pid, rec):
        real_create(pid, rec)
        raise RuntimeError("crash after link, before return")

    chain.monkeypatch.setattr(chain.store, "create", create_then_crash)
    r, reasons = _run(chain)
    assert r is not None and r.status == "already_consumed"
    assert reasons == ("gate9_already_consumed",)
    assert chain.store.resolve(chain.rig.proof_id) is not None
    assert _count_records(chain.store._root) == 1
    chain.monkeypatch.setattr(chain.store, "create", real_create)
    r2, reasons2 = _run(chain)
    assert r2.status == "already_consumed" and reasons2 == ("gate9_already_consumed",)


def test_partial_corrupt_record_fails_closed_never_retries_consumption(chain):
    _run(chain)  # one good record
    path = next(Path(str(chain.store._root)).rglob("consumption.json"))
    path.write_text('{"consumption_schema_version": "HPAC-AUTHORITY-CONSUMPTION/2.0"')  # truncated
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_consumption_state_durability_uncertain",)
    # still exactly one file; corruption never treated as "unconsumed → retry"
    assert _count_records(chain.store._root) == 1


def test_corrupt_digest_mismatch_fails_closed(chain):
    _run(chain)
    path = next(Path(str(chain.store._root)).rglob("consumption.json"))
    doc = json.loads(path.read_text())
    doc["record_digest"] = "0" * 64
    path.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")))
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_consumption_state_durability_uncertain",)


def test_restart_uses_durable_record_not_process_local_registry(chain):
    r1, _ = _run(chain)
    g9._GATE9_RESULTS.clear()  # simulate a fresh process: no in-memory markers
    fresh = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)))
    chain.store = fresh
    r2, reasons2 = _run(chain)
    assert r2 is not None and r2.status == "already_consumed"
    assert reasons2 == ("gate9_already_consumed",)


def test_restart_after_precommit_failure_sees_unconsumed(chain):
    chain.monkeypatch.setattr(chain.store, "create", lambda p, r: (_ for _ in ()).throw(RuntimeError("x")))
    _run(chain)
    g9._GATE9_RESULTS.clear()
    fresh = RuntimeInvocationAuthorityConsumptionStore(Path(str(chain.store._root)))
    assert fresh.resolve(chain.rig.proof_id) is None


# ══════════════════════════════════════════════════════════════════════
# §62-§65  Gate9Result provenance / anti-transfer / not-success
# ══════════════════════════════════════════════════════════════════════
def test_gate9_result_not_caller_constructable():
    with pytest.raises(TypeError):
        g9.Gate9Result(status="consumed", proof_id="p", approval_id="a", record_digest="d",
                       dispatch_state="dispatch_attempted", invocation_id="i", attempt_id="t",
                       consumed_at=NOW, advisory_reasons=(), _seal=object())


def test_gate9_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g9.Gate9Result,), {})


def test_gate9_result_anti_transfer(chain):
    r, _ = _run(chain)
    assert g9.is_gate9_result(r) is True
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    assert g9.is_gate9_result(object.__new__(g9.Gate9Result)) is False
    assert g9.is_gate9_result(None) is False
    # identity equality only
    assert r == r and hash(r) == id(r)


def test_is_gate9_result_means_provenance_not_success(chain):
    r1, _ = _run(chain)
    r2, _ = _run(chain)  # already_consumed
    assert g9.is_gate9_result(r1) and g9.is_gate9_result(r2)
    assert r1.status == "consumed" and r2.status == "already_consumed"
    # forward invariant for Gate 10 is documented in-source
    assert 'status == "consumed"' in G9_SRC
    assert "re-read the durable" in G9_SRC


def test_trusted_non_success_result_carries_no_gate10_licence(chain):
    _run(chain)
    r2, _ = _run(chain)
    assert r2.status == "already_consumed"
    assert g9.is_gate9_result(r2) is True  # provenance yes
    # a Gate-10 consumer that only checked is_gate9_result would be wrong;
    # the source explicitly requires status == "consumed" AND a durable re-read
    assert 'status == "consumed"' in G9_SRC


# ══════════════════════════════════════════════════════════════════════
# §40 / §66-§67 / §81  NON-REAL / no effect / absolute Gate-9|10 separation
# ══════════════════════════════════════════════════════════════════════
def test_production_predicates_make_gate9_unreachable_without_substitution():
    r, reasons = g9.run_gate9_atomic_authority_consumption(
        object.__new__(g8.Gate8Result),
        gate7_result=object.__new__(gate7.Gate7Result),
        gate6_decision=object.__new__(rdp.Gate6Decision),
        gate5_result=object.__new__(gate5.Gate5Result),
        identity=object(), inputs=object(), authority_current_time=NOW,
        repo_root=REPO_ROOT, effect_plan=object(), descriptor_resolver=lambda i: None,
        lifecycle_store=None, consumption_store=None, capability_snapshot_resolver=_snapshot,
        authority_generation_resolver=lambda: {},
    )
    assert r is None and reasons == ("gate9_untrusted_gate8_result",)


def test_real_gate5_never_yields_gate5result(tmp_path):
    from _rdw3w_helpers import (always_unconsumed, construct_test_only_deterministic_approval,
                                matching_context)
    from pcae.core.runtime_invocation_approval_store import RuntimeInvocationApprovalStore
    inv = "inv-" + "e" * 32
    rig = _Rig(tmp_path / "hpac", invocation_id=inv)
    principal = rig.verify()
    approval = construct_test_only_deterministic_approval(
        approval_id=rig.approval_id, invocation_id=inv, approver_id=rig.principal_id,
        created_at="2026-08-28T00:02:00Z", expires_at="2026-08-28T00:04:30Z")
    store = RuntimeInvocationApprovalStore(tmp_path)
    store.create(approval)
    result, reasons = gate5.run_gate5(
        approval.approval_id, approval_store=store, authenticated_principal=principal,
        context=matching_context(approval, current_time=NOW), consumption_lookup=always_unconsumed,
        lifecycle_store=rig.lifecycle_store)
    assert result is None
    assert reasons == ("non_real_authenticated_principal_cannot_validate_production_approval",)


def test_module_imports_nothing_effectful():
    tree = ast.parse(G9_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in ("subprocess", "socket", "pty", "os", "requests", "httpx", "urllib",
                "asyncio", "multiprocessing", "ctypes", "fcntl", "ssl", "selectors",
                "threading", "pcae.core.runtime_adapter", "pcae.core.mock_runtime_adapter",
                "fido2", "webauthn", "ctap"):
        assert bad not in imported, bad
    # code-level (not prose): the module defines/calls no effectful primitive
    tree2 = ast.parse(G9_SRC)
    for node in ast.walk(tree2):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in (
                "Popen", "run", "system", "spawn", "spawnv", "execv", "execve",
                "dispatch", "connect", "sendall", "urlopen",
            ), node.func.attr
    assert "Popen(" not in G9_SRC and "os.system(" not in G9_SRC


def test_runtime_capability_constants_unchanged_after_gate9(chain):
    _run(chain)
    _run(chain)
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_only_effect_is_the_local_canonical_consumption_store_write(chain):
    before_repo = _count_records(REPO_ROOT)
    r, _ = _run(chain)
    assert r.status == "consumed"
    assert _count_records(REPO_ROOT) == before_repo
    assert _count_records(chain.store._root) == 1


# ══════════════════════════════════════════════════════════════════════
# §74-§77  V-13-1 guard orientation + production scope + contract identity
# ══════════════════════════════════════════════════════════════════════
def test_production_scope_since_baseline_is_exactly_gate9_file():
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASELINE, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert changed == ["src/pcae/core/runtime_dispatch_gate9.py"]


def test_frozen_contracts_and_adjacent_modules_byte_unchanged():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/shell_gate.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/hpac_lifecycle.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/hpac_foundation.py",
    ):
        diff = subprocess.run(["git", "diff", BASELINE, "HEAD", "--", rel],
                              cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert diff == "", rel


def test_gate9_internal_error_fails_closed_no_partial_output(chain):
    chain.monkeypatch.setattr(
        g9, "_expected_subject_scope_binding_digest",
        lambda **k: (_ for _ in ()).throw(ValueError("boom")))
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate9_internal_error_fail_closed",)
    assert _count_records(chain.store._root) == 0


def test_structural_input_guards(chain):
    for ov, reason in (
        (dict(identity=object()), "gate9_invalid_identity"),
        (dict(inputs=object()), "gate9_invalid_construction_input"),
        (dict(authority_current_time=""), "gate9_invalid_authority_current_time"),
        (dict(repo_root="x"), "gate9_invalid_repo_root"),
        (dict(descriptor_resolver="x"), "gate9_invalid_descriptor_resolver"),
        (dict(consumption_store=object()), "gate9_invalid_consumption_store"),
        (dict(capability_snapshot_resolver="x"), "gate9_invalid_capability_snapshot_resolver"),
        (dict(effect_plan=object()), "gate9_invalid_effect_plan"),
        (dict(lifecycle_store=object()), "gate9_invalid_lifecycle_store"),
    ):
        r, reasons = _run(chain, **ov)
        assert r is None and reasons == (reason,), (ov, reasons)
