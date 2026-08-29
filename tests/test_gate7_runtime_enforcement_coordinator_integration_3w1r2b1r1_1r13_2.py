"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.2 — Gate-7 Runtime Enforcement
Coordinator Integration Implementation.

Focused defensive tests for
``runtime_dispatch_gate7.run_gate7_runtime_enforcement`` (the frozen Gate-7
owner), ``Gate7Result``, ``is_gate7_result``, and
``resolve_runtime_enforcement_posture``. Constructed from the primary
contracts (RDGO-001 v3.0 §8 / §10 item 7 / §15 / §19, PBRD-001 v2.0 §14,
POL-005, the ``runtime_enforcement_safety_authorization`` design-only no-go
vocabulary, the ``.1R.13.1`` planning document §4 / §6 / §7 / §8 / §9 / §10
/ §13 / §24) and current production source — not from a report or from test
names.

The deterministic HPAC mechanism is permanently NON-REAL: ``run_gate5``
never returns a ``Gate5Result`` on any obtainable path, so
``run_gate6_permission_broker`` never returns a ``Gate6Decision``. **There
is no legitimate positive Gate-7 evaluation** to construct without real
FIDO2/UI, and this suite manufactures none. Every production-path case is
rejection-only or a negative ``Gate7Result``.

To drive the Gate-7 envelope (steps 2→7) at runtime WITHOUT manufacturing
real human authority, a small number of tests install a **test-boundary
substitution** for the provenance predicates only (``monkeypatch`` on
``runtime_dispatch_permission.is_gate6_decision`` /
``runtime_dispatch_gate5.is_gate5_result`` and, where the freshness
re-resolution is not under test, the projection-trust predicates in the
``runtime_dispatch_gate7`` namespace). This substitutes exactly the gates a
real FIDO2/UI ceremony + a real PB ALLOW would satisfy; it manufactures no
``ValidatedAuthorityProjection``, no approval, and no runtime capability. In
every such test the current runtime posture is the real one
(``Observed / observe / unavailable``), so the Gate-7 decision is still
``DENY`` — exactly as the plan states. This mirrors the ``.1R.13``
verification suite's accepted boundary.
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
from pcae.core import runtime_dispatch_gate7 as g7
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY_BASELINE = "698fabd9182fe90a74a0fef96cc978409fd8e1b0"
NOW = "2026-08-29T00:30:00Z"


# ═══════════════════════════════════════════════════════════════════════
# Test-boundary fixtures — clearly labelled; no real authority, no
# real runtime capability (see module docstring).
# ═══════════════════════════════════════════════════════════════════════
class _SyntheticProjection:
    """A non-authority stand-in for ``ValidatedAuthorityProjection`` used
    only where the freshness re-resolution is itself substituted. Carries
    just the two fields Gate 7 reads directly."""

    def __init__(self, *, subject_scope_binding_digest: str):
        self.subject_scope_binding_digest = subject_scope_binding_digest
        self.freshness_verdict_digest = "f" * 64

    def evidence_digest(self) -> str:
        return "e" * 64


def _synthetic_gate5_result(*, invocation_id: str, projection) -> gate5.Gate5Result:
    obj = object.__new__(gate5.Gate5Result)
    for name, value in (
        ("_projection", projection),
        ("sequence3_event_digest", "d" * 64),
        ("proof_id", "proof-x"),
        ("approval_id", "ria-" + "0" * 32),
        ("invocation_id", invocation_id),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _forged_gate5_result():
    return _synthetic_gate5_result(invocation_id="inv-" + "a" * 32, projection=None)


class _FakePBDecision:
    decision = "ALLOW"
    decision_reason = "would-allow"
    causing_policy_ids = ()
    matched_no_go_ids = ()
    requires_human = False
    simulation_only = False
    implementation_status = "execution_unavailable"


def _synthetic_gate6_decision(
    *, decision: str, invocation_id: str, attempt_id: str
) -> rdp.Gate6Decision:
    obj = object.__new__(rdp.Gate6Decision)
    pb = _FakePBDecision()
    pb.decision = decision
    for name, value in (
        ("_pb_decision", pb),
        ("decision", decision),
        ("decision_reason", "synthetic"),
        ("approval_present", True),
        ("invocation_id", invocation_id),
        ("attempt_id", attempt_id),
        ("request_id", "pbr-" + "0" * 12),
        ("causing_policy_ids", ()),
        ("matched_no_go_ids", ()),
        ("requires_human", decision == "HUMAN_REVIEW"),
        ("simulation_only", False),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


@pytest.fixture
def chain(monkeypatch):
    """A trusted (substituted-provenance) Gate-6 ALLOW + Gate-5 result bound
    to one real identity/inputs. Projection trust + revalidation are also
    substituted (not under test in the cases that use this fixture)."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    expected = rdp._expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    projection = _SyntheticProjection(subject_scope_binding_digest=expected)
    g6 = _synthetic_gate6_decision(
        decision="ALLOW",
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
    )
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)

    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g7, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection
    )
    return dict(inputs=inputs, identity=identity, g6=g6, g5=g5, projection=projection)


def _run(chain, **overrides):
    g6 = overrides.pop("gate6_decision", chain["g6"])
    kw = dict(
        gate5_result=chain["g5"],
        identity=chain["identity"],
        inputs=chain["inputs"],
        authority_current_time=NOW,
    )
    kw.update(overrides)
    return g7.run_gate7_runtime_enforcement(g6, **kw)


# ═══════════════════════════════════════════════════════════════════════
# 1. Gate6Decision provenance — only the exact registry object
# ═══════════════════════════════════════════════════════════════════════
def test_none_gate6_decision_fails_closed():
    r, reasons = g7.run_gate7_runtime_enforcement(
        None, gate5_result=None, identity=object(), inputs=object(), authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_caller_constructed_gate6_decision_rejected():
    forged = object.__new__(rdp.Gate6Decision)
    for n in rdp.Gate6Decision.__slots__:
        try:
            object.__setattr__(forged, n, "ALLOW" if n == "decision" else None)
        except AttributeError:
            pass
    r, reasons = g7.run_gate7_runtime_enforcement(
        forged,
        gate5_result=None,
        identity=object(),
        inputs=object(),
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_reconstructed_copied_serialized_gate6_decision_rejected():
    with pytest.raises(TypeError):
        pickle.dumps(object.__new__(rdp.Gate6Decision))
    fake = object.__new__(rdp.Gate6Decision)
    object.__setattr__(fake, "decision", "ALLOW")
    with pytest.raises(TypeError):
        copy.deepcopy(fake)


def test_bare_decision_allow_object_rejected():
    r, reasons = g7.run_gate7_runtime_enforcement(
        type("D", (), {"decision": "ALLOW"})(),
        gate5_result=None,
        identity=object(),
        inputs=object(),
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_registries_stay_empty_on_every_reject():
    before7 = len(g7._GATE7_RESULTS)
    for c in (None, object(), "x", 7, type("D", (), {"decision": "ALLOW"})()):
        g7.run_gate7_runtime_enforcement(
            c, gate5_result=None, identity=object(), inputs=object(), authority_current_time=NOW
        )
    assert len(g7._GATE7_RESULTS) == before7


# ═══════════════════════════════════════════════════════════════════════
# 2. Gate-6 decision semantics — DENY / HUMAN_REVIEW rejected BEFORE
#    any runtime-enforcement evaluation; only literal "ALLOW" continues
# ═══════════════════════════════════════════════════════════════════════
def test_pb_deny_rejected_before_re_evaluation(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    g6 = _synthetic_gate6_decision(
        decision="DENY", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=object(), identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None
    assert reasons == ("gate7_pb_decision_not_allow:DENY",)
    assert not g7.is_gate7_result(r)


def test_pb_human_review_never_becomes_allow(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    g6 = _synthetic_gate6_decision(
        decision="HUMAN_REVIEW",
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=object(), identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None
    assert reasons == ("gate7_pb_decision_not_allow:HUMAN_REVIEW",)


def test_unknown_pb_decision_value_fails_closed(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    g6 = _synthetic_gate6_decision(
        decision="MAYBE", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=object(), identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_pb_decision_not_allow:MAYBE",)


def test_pol005_deny_cannot_reach_gate7_success(monkeypatch):
    """A POL-005 hard DENY (the real production Gate-6 result today) makes
    ``decision != "ALLOW"`` by exact equality; Gate 7 short-circuits with no
    ``Gate7Result``. Gate 7 never inspects *why* PB denied."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    g6 = _synthetic_gate6_decision(
        decision="DENY", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    g6._pb_decision.causing_policy_ids = ("POL-005",)
    g6._pb_decision.matched_no_go_ids = ("NG-025",)
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=object(), identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_pb_decision_not_allow:DENY",)


# ═══════════════════════════════════════════════════════════════════════
# 3. Gate-5 provenance + exact invocation lineage
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_gate5_result_fails_closed(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    g6 = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6,
        gate5_result=_forged_gate5_result(),
        identity=identity,
        inputs=inputs,
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_untrusted_gate5_result",)


def test_invocation_substitution_rejected(chain, monkeypatch):
    other_inputs = dispatch_inputs(task_id="task-b")
    other_identity = new_dispatch_identity(other_inputs)
    r, reasons = g7.run_gate7_runtime_enforcement(
        chain["g6"],
        gate5_result=chain["g5"],
        identity=other_identity,
        inputs=chain["inputs"],
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_attempt_id_substitution_rejected(chain, monkeypatch):
    bad_g6 = _synthetic_gate6_decision(
        decision="ALLOW",
        invocation_id=chain["identity"].invocation_id,
        attempt_id="att-" + "9" * 32,
    )
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is bad_g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        bad_g6,
        gate5_result=chain["g5"],
        identity=chain["identity"],
        inputs=chain["inputs"],
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 4. Freshness re-resolution at Gate 7's own point of use
# ═══════════════════════════════════════════════════════════════════════
def test_stale_projection_rejected(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    expected = rdp._expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    projection = _SyntheticProjection(subject_scope_binding_digest=expected)
    g6 = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    # trust passes, revalidation FAILS (revoked/expired/policy-drifted)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g7, "revalidate_validated_authority_projection", lambda p, *, current_time: False
    )
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_stale_validated_authority_projection",)


def test_untrusted_projection_rejected(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    projection = _SyntheticProjection(subject_scope_binding_digest="z" * 64)
    g6 = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda p: False)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_stale_validated_authority_projection",)


def test_subject_scope_binding_mismatch_rejected(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    projection = _SyntheticProjection(subject_scope_binding_digest="0" * 64)  # wrong
    g6 = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=identity.invocation_id, attempt_id=identity.attempt_id
    )
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g7, "revalidate_validated_authority_projection", lambda p, *, current_time: True
    )
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=identity, inputs=inputs, authority_current_time=NOW
    )
    assert r is None and reasons == ("gate7_authority_subject_scope_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 5. Structural input guards
# ═══════════════════════════════════════════════════════════════════════
def test_invalid_authority_current_time_rejected(chain):
    r, reasons = g7.run_gate7_runtime_enforcement(
        chain["g6"],
        gate5_result=chain["g5"],
        identity=chain["identity"],
        inputs=chain["inputs"],
        authority_current_time=42,
    )
    assert r is None and reasons == ("gate7_invalid_authority_current_time",)


def test_invalid_identity_type_rejected(monkeypatch):
    g6 = _synthetic_gate6_decision(decision="ALLOW", invocation_id="inv-x", attempt_id="att-x")
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6,
        gate5_result=object(),
        identity=object(),
        inputs=dispatch_inputs(),
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_invalid_identity",)


def test_invalid_construction_input_rejected(monkeypatch):
    g6 = _synthetic_gate6_decision(decision="ALLOW", invocation_id="inv-x", attempt_id="att-x")
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda c: c is g6)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6,
        gate5_result=object(),
        identity=new_dispatch_identity(dispatch_inputs()),
        inputs=object(),
        authority_current_time=NOW,
    )
    assert r is None and reasons == ("gate7_invalid_construction_input",)


# ═══════════════════════════════════════════════════════════════════════
# 6. Runtime posture — current Observed / observe / unavailable ALWAYS
#    yields a negative Gate7Result (RE-NOGO-002 + safety no-gos)
# ═══════════════════════════════════════════════════════════════════════
def test_current_posture_yields_negative_gate7_result(chain):
    r, reasons = _run(chain)
    assert g7.is_gate7_result(r)
    assert r.decision == "DENY"
    assert "RE-NOGO-002" in r.matched_no_go_ids
    assert "RE-NOGO-001" in r.matched_no_go_ids
    assert "RE-NOGO-010" in r.matched_no_go_ids
    assert "RE-NOGO-011" in r.matched_no_go_ids
    assert reasons == ("gate7_runtime_execution_unavailable",)
    assert "gate7_runtime_execution_unavailable" in r.causing_reason_ids
    assert any(c.startswith("gate7_safety_no_go:RE-NOGO-002") for c in r.causing_reason_ids)


def test_negative_result_carries_bound_digests(chain):
    r, _ = _run(chain)
    assert r.invocation_id == chain["identity"].invocation_id
    assert r.attempt_id == chain["identity"].attempt_id
    assert r.request_id == chain["g6"].request_id
    for d in (
        r.pb_decision_digest,
        r.authority_freshness_digest,
        r.evaluated_input_digest,
        r.runtime_posture_digest,
    ):
        assert isinstance(d, str) and len(d) == 64
    assert r.expires_at == NOW and r.evaluated_at == NOW


def test_posture_resolved_internally_not_from_caller(chain):
    """There is no request parameter that carries posture; the coordinator
    reads ``runtime_introspection`` itself."""
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    tree = ast.parse(src)
    fn = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "run_gate7_runtime_enforcement"
    )
    params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    assert params == {
        "gate6_decision", "gate5_result", "identity", "inputs", "authority_current_time",
    }


def test_re_nogo_vocabulary_is_consumed_not_redefined():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    assert "from pcae.core.runtime_enforcement_safety_authorization import" in src
    # no local RE-NOGO id string is minted (only referenced via the maps)
    assert '"RE-NOGO-0' not in src and "'RE-NOGO-0" not in src


def test_no_positive_production_gate7_success_today(chain):
    """Even with substituted provenance + substituted freshness, the real
    posture drives DENY. The positive branch is unreachable in production."""
    r, _ = _run(chain)
    assert r.decision == "DENY"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# 7. Gate7Result provenance / anti-transfer (shape != provenance)
# ═══════════════════════════════════════════════════════════════════════
def test_gate7_result_not_caller_constructable():
    with pytest.raises(TypeError):
        g7.Gate7Result(
            decision="ALLOW",
            matched_no_go_ids=(),
            causing_reason_ids=(),
            invocation_id="i",
            attempt_id="a",
            request_id="r",
            pb_decision_digest="x",
            authority_freshness_digest="x",
            evaluated_input_digest="x",
            runtime_posture_digest="x",
            expires_at=NOW,
            evaluated_at=NOW,
            _seal=object(),
        )


def test_gate7_result_non_transferable(chain):
    r, _ = _run(chain)
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    assert not g7.is_gate7_result(object.__new__(g7.Gate7Result))
    assert not g7.is_gate7_result(None)

    class _Looks:
        decision = "ALLOW"
        matched_no_go_ids = ()

    assert not g7.is_gate7_result(_Looks())


def test_gate7_result_identity_equality_only(chain):
    r1, _ = _run(chain)
    r2, _ = _run(chain)
    assert r1 is not r2
    assert r1 != r2
    assert hash(r1) == id(r1)


def test_gate7_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g7.Gate7Result,), {})


# ═══════════════════════════════════════════════════════════════════════
# 8. Consumes nothing / idempotent / no partial output
# ═══════════════════════════════════════════════════════════════════════
def test_repeated_run_consumes_nothing_and_is_deterministic(chain, tmp_path):
    consumption_before = list(REPO_ROOT.rglob("consumption.json"))
    r1, x1 = _run(chain)
    r2, x2 = _run(chain)
    assert x1 == x2 == ("gate7_runtime_execution_unavailable",)
    assert r1.decision == r2.decision == "DENY"
    assert r1 is not r2  # fresh result each call, never a cache
    assert r1.evaluated_input_digest == r2.evaluated_input_digest
    assert list(REPO_ROOT.rglob("consumption.json")) == consumption_before


def test_internal_error_fails_closed_with_no_partial_output(chain, monkeypatch):
    def _boom():
        raise RuntimeError("resolver exploded")

    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture", _boom)
    before = len(g7._GATE7_RESULTS)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate7_internal_error_fail_closed",)
    assert len(g7._GATE7_RESULTS) == before


# ═══════════════════════════════════════════════════════════════════════
# 9. Sole owner / no Gate-8 / no Gate-9 / no Gate-10 effect
# ═══════════════════════════════════════════════════════════════════════
_FORBIDDEN_IMPORT_ROOTS = {
    "subprocess", "socket", "requests", "httpx", "urllib", "http",
    "asyncio", "multiprocessing", "ctypes", "pty", "fcntl", "signal",
    "ssl", "selectors",
}


def test_module_imports_nothing_effectful():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root not in _FORBIDDEN_IMPORT_ROOTS
            assert "runtime_dispatch_gate8" not in node.module
            assert "runtime_dispatch_gate9" not in node.module
            assert "runtime_invocation_authority_consumption" not in node.module
            assert "shell_gate" not in node.module
            assert "runtime_adapter" not in node.module
            assert "backend_invocation" not in node.module


def test_no_gate8_gate9_gate10_symbol_referenced():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    for forbidden in (
        "run_gate8", "Gate8Result", "run_gate9", "Gate9Result",
        "dispatch_attempted", "import subprocess", "os.system(",
        "Popen(", ".dispatch(",
    ):
        assert forbidden not in src, forbidden


def test_gate7_is_sole_production_consumer_of_is_gate6_decision():
    """Only ``runtime_dispatch_gate7`` consumes ``is_gate6_decision`` /
    ``Gate6Decision`` as a production Gate-7 path (RDGO-001 §8; plan §29)."""
    hits = subprocess.run(
        ["git", "grep", "-l", "is_gate6_decision", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert set(hits) == {
        "src/pcae/core/runtime_dispatch_permission.py",  # defines it
        "src/pcae/core/runtime_dispatch_gate7.py",  # sole consumer
    }


def test_runtime_state_unchanged_after_gate7_runs(chain):
    _run(chain)
    _run(chain)
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    posture = g7.resolve_runtime_enforcement_posture()
    assert posture.execution_available is False
    assert posture.governance_posture == "non-executing"


# ═══════════════════════════════════════════════════════════════════════
# 10. Production-scope invariant + contract byte identity
# ═══════════════════════════════════════════════════════════════════════
def test_production_scope_since_baseline_is_the_single_new_gate7_file():
    changed = subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert set(changed) == {"src/pcae/core/runtime_dispatch_gate7.py"}


def test_contracts_and_pol005_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    ):
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == "", f"{rel} changed since baseline"
    pbf_diff = subprocess.run(
        ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--",
         "src/pcae/core/permission_broker_foundation.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert pbf_diff == ""


def test_gate5_gate6_coordinators_unchanged_since_baseline():
    for rel in (
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_enforcement_safety_authorization.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/policy.py",
    ):
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, "HEAD", "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == "", f"{rel} changed since baseline"
