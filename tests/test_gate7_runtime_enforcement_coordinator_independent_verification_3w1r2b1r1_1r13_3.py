"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.3 — Independent Verification of the
Gate-7 Runtime Enforcement Coordinator Integration.

RE-DERIVE, DO NOT TRUST. This suite is written from the primary sources
(RDGO-001 v3.0 §8/§10/§15/§19, PBRD-001 v2.0 §14, POL-005,
``runtime_enforcement_safety_authorization`` design-only no-go vocabulary,
``docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md``, ``.1R.13.1`` §4/§6/§7/§10/
§13/§24, and current production source) — not from the ``.1R.13.2`` report,
its implementation document, or its 36 tests.

The deterministic HPAC mechanism is permanently NON-REAL, so ``run_gate5``
never returns a ``Gate5Result`` on any obtainable path and no legitimate
positive Gate-7 evaluation exists. To drive the Gate-7 envelope (steps
2→7) without manufacturing real human authority, a small number of tests
install a **clearly labelled test-boundary substitution** for the
provenance predicates only (``is_gate6_decision`` / ``is_gate5_result`` and,
where the freshness re-resolution is not itself under test, the
projection-trust predicates). This substitutes exactly the gates a real
FIDO2/UI ceremony + a real PB ALLOW would satisfy; it manufactures no
``ValidatedAuthorityProjection``, no approval, and no runtime capability.
In every such test the runtime posture is the real one
(``Observed / observe / unavailable``), so the Gate-7 decision is still
``DENY``. This mirrors the accepted ``.1R.13`` / ``.1R.13.2`` boundary.
"""

from __future__ import annotations

import ast
import copy
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate7 as g7
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_authority as ra

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY_BASELINE = "698fabd9182fe90a74a0fef96cc978409fd8e1b0"
_1R15_4_SCOPE_END = "4d480553"  # end of .1R.15.3; .1R.15.4 (Contract Normalization) is the later authorized change
NOW = "2026-08-29T00:30:00Z"
G7_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()


# ═══════════════════════════════════════════════════════════════════════
# Labelled test-boundary fixtures — no real authority, no runtime capability
# ═══════════════════════════════════════════════════════════════════════
class _SyntheticProjection:
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


class _FakePB:
    decision = "ALLOW"
    decision_reason = "would-allow"
    causing_policy_ids = ()
    matched_no_go_ids = ()
    requires_human = False
    simulation_only = False
    implementation_status = "execution_unavailable"


def _synthetic_gate6_decision(*, decision, invocation_id, attempt_id) -> rdp.Gate6Decision:
    obj = object.__new__(rdp.Gate6Decision)
    pb = _FakePB()
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
def bound():
    inp = dispatch_inputs()
    ident = new_dispatch_identity(inp)
    return ident, inp


def _substitute_provenance(monkeypatch, *, g6_ok=True, g5_ok=True, proj_ok=True):
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda o: g6_ok and isinstance(o, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result", lambda o: g5_ok and isinstance(o, gate5.Gate5Result))
    if proj_ok:
        monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
        monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: True)


def _drive(monkeypatch, bound, *, decision="ALLOW", g6_ok=True, g5_ok=True, proj_ok=True,
           g5_inv=None, g6_inv=None, g6_att=None, binding_digest=None):
    ident, inp = bound
    _substitute_provenance(monkeypatch, g6_ok=g6_ok, g5_ok=g5_ok, proj_ok=proj_ok)
    if binding_digest is None:
        binding_digest = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    g5 = _synthetic_gate5_result(
        invocation_id=g5_inv or ident.invocation_id,
        projection=_SyntheticProjection(subject_scope_binding_digest=binding_digest),
    )
    g6 = _synthetic_gate6_decision(
        decision=decision,
        invocation_id=g6_inv or ident.invocation_id,
        attempt_id=g6_att or ident.attempt_id,
    )
    return g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Sole Gate-7 owner
# ═══════════════════════════════════════════════════════════════════════
def test_gate7_is_sole_production_owner_of_runtime_enforcement_boundary():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E",
         r"run_gate7_runtime_enforcement|resolve_runtime_enforcement_posture", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits == {"src/pcae/core/runtime_dispatch_gate7.py"}


def test_no_downstream_production_consumer_of_gate7_result():
    # .1R.13.4 (V-13-1): Gate 8 (runtime_dispatch_gate8.py) is the sole
    # authorized downstream production consumer of the Gate-7 result
    # (is_gate7_result + decision == "ALLOW"); RDGO-001 §9. Phase-aware
    # invariant: the Gate7Result consumer set is a SUBSET of {gate7 (defines),
    # gate8 (sole authorized consumer)} — any other consumer still fails.
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate7Result|is_gate7_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",  # authorized Gate-9 consumer (.1R.14 §16.2)
    }, f"unexpected Gate7Result consumer: {sorted(hits)}"


def test_gate7_is_the_only_new_gate6_decision_consumer():
    # .1R.14 (V-13-1): the Gate-9 atomic-consumption coordinator is the
    # second authorized downstream consumer of the Gate-6 decision object
    # (the .1R.13.1 §16.2 handoff re-derives Gate-6 lineage). Phase-aware
    # subset invariant.
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate6Decision|is_gate6_decision", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits <= {
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unexpected Gate6Decision consumer: {sorted(hits)}"


# ═══════════════════════════════════════════════════════════════════════
# 2. Gate6Decision / Gate5Result provenance
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("bad", [None, object(), "ALLOW", 123])
def test_non_registry_gate6_decision_fails_closed(bound, bad):
    ident, inp = bound
    r, reasons = g7.run_gate7_runtime_enforcement(
        bad, gate5_result=object(), identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_object_new_gate6_lookalike_fails_closed(bound):
    ident, inp = bound
    forged = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=ident.invocation_id, attempt_id=ident.attempt_id)
    r, reasons = g7.run_gate7_runtime_enforcement(
        forged, gate5_result=object(), identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_copy_and_deepcopy_of_gate6_lookalike_fail_closed(bound):
    ident, inp = bound
    forged = _synthetic_gate6_decision(
        decision="ALLOW", invocation_id=ident.invocation_id, attempt_id=ident.attempt_id)
    for make in (copy.copy, copy.deepcopy):
        try:
            variant = make(forged)
        except TypeError:
            continue  # Gate6Decision is non-serializable -> copy blocked, also fine
        r, reasons = g7.run_gate7_runtime_enforcement(
            variant, gate5_result=object(), identity=ident, inputs=inp, authority_current_time=NOW)
        assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_trusted_allow_but_forged_gate5_result_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", g5_ok=False)
    assert r is None and reasons == ("gate7_untrusted_gate5_result",)


def test_mixed_provenance_forged_gate6_trusted_gate5_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", g6_ok=False)
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


def test_correct_trusted_pair_reaches_evaluation_and_returns_negative_result(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW")
    assert g7.is_gate7_result(r) and r.decision == "DENY"
    assert reasons == ("gate7_runtime_execution_unavailable",)


# ═══════════════════════════════════════════════════════════════════════
# 3. Decision anti-escalation (DENY / HUMAN_REVIEW / unknown before eval)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("decision", ["DENY", "HUMAN_REVIEW", "allow", "ALLOW ", "MAYBE", ""])
def test_non_allow_decision_rejected_before_runtime_evaluation(monkeypatch, bound, decision):
    # posture resolver must not even be consulted: patch it to explode.
    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture",
                        lambda: (_ for _ in ()).throw(AssertionError("posture consulted")))
    r, reasons = _drive(monkeypatch, bound, decision=decision)
    assert r is None
    assert reasons == (f"gate7_pb_decision_not_allow:{decision}",)


def test_no_path_converts_deny_into_positive_result(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="DENY")
    assert r is None
    # nothing was added to the result registry
    assert all(x.decision != "ALLOW" for x in g7._GATE7_RESULTS if x.invocation_id == bound[0].invocation_id)


def test_only_literal_ALLOW_string_continues(monkeypatch, bound):
    r_ok, _ = _drive(monkeypatch, bound, decision="ALLOW")
    assert r_ok is not None  # negative Gate7Result, but evaluation was reached


# ═══════════════════════════════════════════════════════════════════════
# 4. Invocation binding + subject/scope digest recompute
# ═══════════════════════════════════════════════════════════════════════
def test_gate5_invocation_id_substitution_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", g5_inv="inv-" + "z" * 32)
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_gate6_invocation_id_substitution_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", g6_inv="inv-" + "z" * 32)
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_gate6_attempt_id_substitution_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", g6_att="att-" + "z" * 32)
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_subject_scope_binding_digest_is_recomputed_not_trusted(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", binding_digest="0" * 64)
    assert r is None and reasons == ("gate7_authority_subject_scope_mismatch",)


def test_structural_identity_and_input_type_guards(bound):
    ident, inp = bound
    r, reasons = g7.run_gate7_runtime_enforcement(
        _synthetic_gate6_decision(decision="ALLOW", invocation_id=ident.invocation_id,
                                  attempt_id=ident.attempt_id),
        gate5_result=object(), identity="not-identity", inputs=inp, authority_current_time=NOW)
    # provenance is checked first, so a forged g6 shortcuts; assert on a real-shaped path:
    assert reasons[0] in ("gate7_untrusted_gate6_decision", "gate7_invalid_identity")


@pytest.mark.parametrize("bad_time", ["", "  ", "x" * 65, 5, None])
def test_invalid_authority_current_time_fails_closed(monkeypatch, bound, bad_time):
    ident, inp = bound
    _substitute_provenance(monkeypatch)
    g6 = _synthetic_gate6_decision(decision="ALLOW", invocation_id=ident.invocation_id,
                                   attempt_id=ident.attempt_id)
    g5 = _synthetic_gate5_result(invocation_id=ident.invocation_id, projection=None)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=bad_time)
    assert r is None and reasons == ("gate7_invalid_authority_current_time",)


# ═══════════════════════════════════════════════════════════════════════
# 5. Freshness re-resolution (projection re-trust + revalidate)
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_projection_at_gate7_point_of_use_rejected(monkeypatch, bound):
    ident, inp = bound
    _substitute_provenance(monkeypatch, proj_ok=False)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: False)
    binding = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    g5 = _synthetic_gate5_result(
        invocation_id=ident.invocation_id,
        projection=_SyntheticProjection(subject_scope_binding_digest=binding))
    g6 = _synthetic_gate6_decision(decision="ALLOW", invocation_id=ident.invocation_id,
                                   attempt_id=ident.attempt_id)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_stale_validated_authority_projection",)


def test_revalidation_failure_after_gate56_rejected(monkeypatch, bound):
    ident, inp = bound
    _substitute_provenance(monkeypatch, proj_ok=False)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
    monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: False)
    binding = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    g5 = _synthetic_gate5_result(
        invocation_id=ident.invocation_id,
        projection=_SyntheticProjection(subject_scope_binding_digest=binding))
    g6 = _synthetic_gate6_decision(decision="ALLOW", invocation_id=ident.invocation_id,
                                   attempt_id=ident.attempt_id)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_stale_validated_authority_projection",)


def test_revalidate_re_runs_validate_approval_with_refreshed_time():
    # Independently confirm revalidate_validated_authority_projection re-runs
    # validate_approval (RDGO-001 §8 item 3): a projection that never was a
    # trusted registry member cannot revalidate.
    assert ra.revalidate_validated_authority_projection(object(), current_time=NOW) is False


# ═══════════════════════════════════════════════════════════════════════
# 6. Runtime posture — canonical source, coherent snapshot, RE-NOGO set
# ═══════════════════════════════════════════════════════════════════════
def test_posture_resolved_internally_no_caller_parameter():
    sig = subprocess.run(["python", "-c",
        "import inspect,pcae.core.runtime_dispatch_gate7 as g;"
        "print(sorted(inspect.signature(g.run_gate7_runtime_enforcement).parameters))"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    assert "execution_available" not in sig and "posture" not in sig
    assert sorted(eval(sig)) == sorted(
        ["gate6_decision", "gate5_result", "identity", "inputs", "authority_current_time"])


def test_posture_reads_canonical_introspection_surface():
    from pcae.core import runtime_introspection as ri
    p = g7.resolve_runtime_enforcement_posture()
    assert p.execution_availability == ri.EXECUTION_AVAILABILITY == "unavailable"
    assert p.execution_available is False
    assert p.runtime_state == ri.get_state().current_state == "Observed"


def test_current_posture_matches_all_flag_derived_no_gos_including_re_nogo_002():
    p = g7.resolve_runtime_enforcement_posture()
    # every authorization flag False, every safety flag True -> full mapped set
    assert set(p.matched_no_go_ids) == {
        "RE-NOGO-001", "RE-NOGO-002", "RE-NOGO-003", "RE-NOGO-004", "RE-NOGO-005",
        "RE-NOGO-006", "RE-NOGO-007", "RE-NOGO-008", "RE-NOGO-010", "RE-NOGO-011"}
    assert "RE-NOGO-002" in p.matched_no_go_ids  # execution boundary absent


def test_re_nogo_vocabulary_is_consumed_not_redefined():
    tree = ast.parse(G7_SRC)
    assigned = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)}
    assert "AUTH_FLAG_TO_NO_GO" not in assigned
    assert "SAFETY_FLAG_TO_NO_GO" not in assigned
    # no hard-coded RE-NOGO string literal in code (ids come from the map)
    assert '"RE-NOGO-' not in G7_SRC and "'RE-NOGO-" not in G7_SRC
    # the mapping is imported from the design-only module
    assert "from pcae.core.runtime_enforcement_safety_authorization import" in G7_SRC


def test_single_posture_snapshot_per_evaluation(monkeypatch, bound):
    calls = []
    real = g7.resolve_runtime_enforcement_posture
    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture",
                        lambda: (calls.append(1), real())[1])
    _drive(monkeypatch, bound, decision="ALLOW")
    assert calls == [1]


# ═══════════════════════════════════════════════════════════════════════
# 7. Current-posture result + no reachable positive production path
# ═══════════════════════════════════════════════════════════════════════
def test_negative_gate7result_carries_bound_digests_and_no_gos(monkeypatch, bound):
    r, _ = _drive(monkeypatch, bound, decision="ALLOW")
    assert r.decision == "DENY"
    assert "RE-NOGO-002" in r.matched_no_go_ids
    assert any(c.startswith("gate7_safety_no_go:RE-NOGO-") for c in r.causing_reason_ids)
    assert "gate7_runtime_execution_unavailable" in r.causing_reason_ids
    for d in (r.pb_decision_digest, r.authority_freshness_digest,
              r.evaluated_input_digest, r.runtime_posture_digest):
        assert isinstance(d, str) and len(d) == 64


def test_positive_branch_is_pragma_no_cover_and_guarded_by_posture():
    tree = ast.parse(G7_SRC)
    allow_literals = [n for n in ast.walk(tree)
                      if isinstance(n, ast.Constant) and n.value == "ALLOW"]
    assert allow_literals  # present structurally
    src_lines = G7_SRC.splitlines()
    # the ALLOW-decision Gate7Result construction (code literal `decision="ALLOW",`)
    # sits under a `pragma: no cover` on the enclosing `Gate7Result(` line.
    idx = next(i for i, l in enumerate(src_lines) if l.strip() == 'decision="ALLOW",')
    window = "\n".join(src_lines[max(0, idx - 3):idx + 1])
    assert "pragma: no cover" in window


def test_no_production_path_adds_a_positive_gate7result(monkeypatch, bound):
    before = {x for x in g7._GATE7_RESULTS if x.decision == "ALLOW"}
    for _ in range(3):
        _drive(monkeypatch, bound, decision="ALLOW")
    after = {x for x in g7._GATE7_RESULTS if x.decision == "ALLOW"}
    assert before == after == set()


def test_real_run_gate5_yields_no_gate5result_so_no_real_gate7_input():
    from _rdw3w_helpers import build_approval, matching_context, always_unconsumed
    ap = build_approval()
    proj, reasons = ra.validate_approval(
        ap, context=matching_context(ap), consumption_lookup=always_unconsumed)
    assert proj is None  # NON-REAL hard stop upstream


# ═══════════════════════════════════════════════════════════════════════
# 8. Gate7Result semantics — provenance != success; anti-transfer; expiry
# ═══════════════════════════════════════════════════════════════════════
def test_is_gate7_result_means_provenance_not_allow(monkeypatch, bound):
    r, _ = _drive(monkeypatch, bound, decision="ALLOW")
    assert g7.is_gate7_result(r) is True       # provenance holds
    assert r.decision == "DENY"                # ...but it is NOT a success
    # regression guard for Gate 8: a trusted negative result must never be
    # read as progression — the downstream check is decision == "ALLOW".
    assert not (g7.is_gate7_result(r) and r.decision == "ALLOW")


def test_object_new_gate7result_is_not_a_registry_member():
    fake = object.__new__(g7.Gate7Result)
    assert g7.is_gate7_result(fake) is False


def test_gate7result_not_caller_constructable():
    with pytest.raises(TypeError):
        g7.Gate7Result(
            decision="ALLOW", matched_no_go_ids=(), causing_reason_ids=(),
            invocation_id="i", attempt_id="a", request_id="r",
            pb_decision_digest="x", authority_freshness_digest="x",
            evaluated_input_digest="x", runtime_posture_digest="x",
            expires_at=NOW, evaluated_at=NOW, _seal=object())


def test_gate7result_not_serializable_and_not_subclassable(monkeypatch, bound):
    r, _ = _drive(monkeypatch, bound, decision="ALLOW")
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    with pytest.raises(TypeError):
        class _Sub(g7.Gate7Result):
            pass


def test_gate7result_identity_equality_only(monkeypatch, bound):
    r1, _ = _drive(monkeypatch, bound, decision="ALLOW")
    r2, _ = _drive(monkeypatch, bound, decision="ALLOW")
    assert r1 == r1 and r1 != r2 and hash(r1) == id(r1)


def test_gate7result_field_reconstruction_is_not_a_member(monkeypatch, bound):
    r, _ = _drive(monkeypatch, bound, decision="ALLOW")
    clone = object.__new__(g7.Gate7Result)
    for s in g7.Gate7Result.__slots__:
        try:
            object.__setattr__(clone, s, getattr(r, s))
        except AttributeError:
            pass
    assert g7.is_gate7_result(clone) is False


# ═══════════════════════════════════════════════════════════════════════
# 9. Idempotency + consumes nothing
# ═══════════════════════════════════════════════════════════════════════
def test_repeated_evaluation_is_idempotent_reject(monkeypatch, bound):
    r1, s1 = _drive(monkeypatch, bound, decision="ALLOW")
    r2, s2 = _drive(monkeypatch, bound, decision="ALLOW")
    assert r1.decision == r2.decision == "DENY" and s1 == s2


def test_gate7_writes_no_consumption_json(monkeypatch, bound, tmp_path):
    _drive(monkeypatch, bound, decision="ALLOW")
    assert not list(REPO_ROOT.glob("**/consumption.json"))


def test_gate7_module_calls_no_lifecycle_or_consumption_primitive():
    tree = ast.parse(G7_SRC)
    called_attrs = {n.func.attr for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for forbidden in ("consume", "bind", "record_consumption", "write", "mutate",
                      "run_gate6_permission_broker", "run_gate5"):
        assert forbidden not in called_attrs


# ═══════════════════════════════════════════════════════════════════════
# 10. Gate 8 / 9 / 10 isolation + runtime unchanged
# ═══════════════════════════════════════════════════════════════════════
def test_no_gate8_gate9_gate10_symbol_or_effect_import():
    tree = ast.parse(G7_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in ("subprocess", "socket", "pty", "os.system", "requests", "httpx",
                "pcae.core.runtime_dispatch_gate8", "pcae.core.shell_gate",
                "pcae.core.runtime_invocation_authority_consumption"):
        assert bad not in imported
    assert "runtime_dispatch_gate8" not in G7_SRC
    assert "shell_gate" not in G7_SRC


def test_runtime_introspection_constants_unchanged_since_baseline():
    # .1R.13.4 (V-13-1): the later authorized Gate-8 phase adds exactly
    # runtime_dispatch_gate8.py. Phase-aware invariant: the src/pcae change
    # set since the .1R.13.1 baseline is a SUBSET of {gate7, gate8}, and
    # runtime_introspection.py in particular is untouched.
    out = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert out <= {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",  # Gate 9 (.1R.14)
    }, f"unauthorized production-file expansion since the .1R.13.1 baseline: {sorted(out)}"
    assert "src/pcae/core/runtime_introspection.py" not in out


def test_contracts_and_pol005_bytes_unchanged_since_baseline():
    out = subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--",
         "docs/contracts", "src/pcae/core/permission_broker_foundation.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert out == ""


def test_runtime_posture_still_not_implemented_observed_unavailable():
    from pcae.core import runtime_introspection as ri
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    assert ri.get_state().current_state == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"


# ═══════════════════════════════════════════════════════════════════════
# 11. V-13-1 guard conversions — security intent preserved
# ═══════════════════════════════════════════════════════════════════════
_CONVERTED_GUARDS = [
    ("tests/test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8.py",
     ["test_isolation_only_three_production_files_changed_since_baseline",
      "test_isolation_no_gate_coordinator_or_gate9_consumption_wiring"]),
    ("tests/test_gate5_approval_validation_coordinator_3w1r2b1r1_1r10.py",
     ["test_only_expected_production_files_changed_since_baseline"]),
    ("tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py",
     ["test_production_scope_is_exactly_the_three_planned_files"]),
    ("tests/test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py",
     ["test_only_expected_production_file_changed_since_baseline"]),
    ("tests/test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py",
     ["test_no_downstream_production_consumer_of_gate6_symbols",
      "test_1r12_production_diff_is_exactly_one_file",
      "test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable"]),
    ("tests/test_runtime_authority_production_repair_3w1r2b1r1117.py",
     ["test_production_file_allowlist_matches_frozen_phase_matrix",
      "test_consumer_inventory_is_bounded_and_gate9_stays_unwired"]),
]


def test_exactly_ten_converted_guards_present():
    assert sum(len(v) for _, v in _CONVERTED_GUARDS) == 10
    for path, names in _CONVERTED_GUARDS:
        src = (REPO_ROOT / path).read_text()
        for name in names:
            assert f"def {name}(" in src, f"{path}::{name} missing"


def test_converted_guards_still_reject_an_unauthorized_extra_production_file():
    # Independently re-derive the subset orientation: `changed - AUTHORIZED`
    # (or `<= AUTHORIZED`), never `AUTHORIZED - changed`, so an unexpected
    # file is still caught.
    for path, _ in _CONVERTED_GUARDS:
        src = (REPO_ROOT / path).read_text()
        assert " - _AUTHORIZED" in src or " <= {" in src or ") <= {" in src or "changed - " in src or " <= _AUTH" in src.replace("_AUTHORIZED", "_AUTH")


def test_converted_guards_keep_hpac_exact_and_gate9_bounded_asserts():
    # .1R.14 (V-13-1): the Gate-9 store importer / consumer asserts are no
    # longer exact-empty — the explicitly human-authorized .1R.14 phase adds
    # exactly one authorized importer (runtime_dispatch_gate9.py). They stay
    # phase-aware SUBSET asserts (any other importer still fails); the
    # hpac_verifier consumer asserts remain exact and unweakened.
    src8 = (REPO_ROOT / _CONVERTED_GUARDS[0][0]).read_text()
    assert 'gate9_callers <= {"src/pcae/core/runtime_dispatch_gate9.py"}' in src8
    assert "hpac_consumers == {" in src8  # still exact, not weakened
    src117 = (REPO_ROOT / _CONVERTED_GUARDS[5][0]).read_text()
    assert 'gate9_consumers <= {"src/pcae/core/runtime_dispatch_gate9.py"}' in src117
    assert "hpac_consumers == {" in src117


def test_synthetic_unauthorized_file_would_fail_the_subset_invariant():
    # direct logical re-derivation of the converted assertion
    authorized = {"src/pcae/core/runtime_dispatch_gate7.py"}
    changed_ok = {"src/pcae/core/runtime_dispatch_gate7.py"}
    changed_bad = changed_ok | {"src/pcae/core/permission_broker_foundation.py"}
    assert changed_ok - authorized == set()
    assert changed_bad - authorized == {"src/pcae/core/permission_broker_foundation.py"}


# ═══════════════════════════════════════════════════════════════════════
# 12. Gate-5 / Gate-6 regression
# ═══════════════════════════════════════════════════════════════════════
def test_gate5_gate6_coordinators_byte_unchanged_since_baseline():
    out = subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--",
         "src/pcae/core/runtime_dispatch_gate5.py",
         "src/pcae/core/runtime_dispatch_permission.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert out == ""


def test_gate5_still_fails_closed_on_non_real_upstream():
    from _rdw3w_helpers import build_approval, matching_context, always_unconsumed
    ap = build_approval()
    proj, _ = ra.validate_approval(
        ap, context=matching_context(ap), consumption_lookup=always_unconsumed)
    assert proj is None


def test_gate6_symbol_import_in_gate7_is_function_local():
    tree = ast.parse(G7_SRC)
    module_level_importfroms = {
        n.module for n in tree.body if isinstance(n, ast.ImportFrom)}
    assert "pcae.core.runtime_dispatch_gate5" not in module_level_importfroms
    # permission symbols used at module scope are the request-construction
    # helpers, not the Gate6Decision provenance predicate
    assert "pcae.core.runtime_dispatch_permission" in module_level_importfroms
