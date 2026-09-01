"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 — N-16-4 Real Positive Single-Attempt
Runtime Enforcement Gate Implementation.

Defensive matrix + REPRC-001 v1.0 contract-production equivalence map for the
**positive** ``Gate7Result`` (``decision == "ALLOW"``), written from the
primary sources (REPRC-001 v1.0
``docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md``, the
``.1R.25`` trust-boundary freeze, RDGO-001 v3.1 §8, and current production
source) — not from a report or from test names.

The production positive Gate-7 path is unreachable (REPRC-001 §18): the
N-16-5 human-authority wall, the N-16-6 admission wall, and the current
Runtime Enforcement no-go posture each independently block it. To exercise
the positive branch WITHOUT enabling execution or manufacturing real human
authority, a small number of tests install a **clearly labelled, in-memory,
documented test-only substitution** (REPRC-001 §17) of
``runtime_dispatch_gate7.resolve_runtime_enforcement_posture`` (returning a
posture with ``execution_available is True`` and an empty
``matched_no_go_ids``) together with the existing test-boundary provenance
substitutions. The substitution is restored on teardown, is reachable from
no production call site, calls no adapter, alters no runtime capability, and
touches no network / credential / hardware / FIDO2 / WebAuthn / CTAP
surface. In every such test the real ``resolve_runtime_enforcement_posture``
still returns ``execution_available is False``.
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
from pcae.core import runtime_introspection as ri

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY = "28b8b2b70dcd4642dc45d4a3961a5218402c3c7c"  # .1R.25 finalize head == .1R.26 entry
NOW = "2026-08-29T00:30:00Z"
LATER_WITHIN_TTL = "2026-08-29T00:32:00Z"
LATER_PAST_TTL = "2026-08-29T00:40:00Z"
G7_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
REPRC = (REPO_ROOT / "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md").read_text()


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


def _synthetic_gate6_decision(*, decision="ALLOW", invocation_id, attempt_id,
                              request_id="pbr-" + "0" * 12) -> rdp.Gate6Decision:
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
        ("request_id", request_id),
        ("causing_policy_ids", ()),
        ("matched_no_go_ids", ()),
        ("requires_human", decision == "HUMAN_REVIEW"),
        ("simulation_only", False),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _allow_posture() -> g7.RuntimeEnforcementPosture:
    """REPRC-001 §17 documented test-only substitute: an available posture
    with an empty per-decision no-go set. Never produced by the real
    resolve_runtime_enforcement_posture (which reads frozen constants)."""
    return g7.RuntimeEnforcementPosture(
        runtime_status="not_implemented",
        runtime_state="Observed",
        execution_availability="available",
        maximum_plugin_capability="observe",
        governance_posture="non-executing",
        permission_broker_status="execution_unavailable",
        authorization_flags={},
        safety_flags={},
        matched_no_go_ids=(),
    )


@pytest.fixture(autouse=True)
def _isolate_gate7_result_registry():
    """The synthetic-seam tests below add real ``ALLOW`` ``Gate7Result``
    objects to the process-local ``_GATE7_RESULTS`` registry. Restore it
    exactly after every test so no other suite in the same pytest process
    observes a positive result it did not create (e.g. the ``.1R.13.3``
    ``test_no_production_path_adds_a_positive_gate7result`` invariant)."""
    snapshot = set(g7._GATE7_RESULTS)
    yield
    g7._GATE7_RESULTS.clear()
    g7._GATE7_RESULTS.update(snapshot)


@pytest.fixture
def bound():
    inp = dispatch_inputs()
    ident = new_dispatch_identity(inp)
    return ident, inp


def _substitute_provenance(monkeypatch, *, g6_ok=True, g5_ok=True, proj_ok=True):
    monkeypatch.setattr(rdp, "is_gate6_decision",
                        lambda o: g6_ok and isinstance(o, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result",
                        lambda o: g5_ok and isinstance(o, gate5.Gate5Result))
    if proj_ok:
        monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
        monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: True)


def _drive(monkeypatch, bound, *, decision="ALLOW", posture=True, now=NOW,
           g6_ok=True, g5_ok=True, proj_ok=True, g5_inv=None, g6_inv=None,
           g6_att=None, binding_digest=None, request_id="pbr-" + "0" * 12,
           inputs_override=None):
    ident, inp = bound
    if inputs_override is not None:
        inp = inputs_override
    _substitute_provenance(monkeypatch, g6_ok=g6_ok, g5_ok=g5_ok, proj_ok=proj_ok)
    if posture:
        monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture", _allow_posture)
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
        request_id=request_id,
    )
    return g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=now
    )


def _allow(monkeypatch, bound, **kw):
    r, reasons = _drive(monkeypatch, bound, **kw)
    assert r is not None, reasons
    return r, reasons


# ═══════════════════════════════════════════════════════════════════════
# A. Positive branch reachable ONLY through the synthetic seam (matrix 1, 2)
# ═══════════════════════════════════════════════════════════════════════
def test_01_synthetic_allow_is_reachable_and_trusted(monkeypatch, bound):
    r, reasons = _allow(monkeypatch, bound)
    assert r.decision == "ALLOW"
    assert g7.is_gate7_result(r) is True
    assert reasons == ()
    assert r.matched_no_go_ids == ()


def test_02_production_positive_is_unreachable_real_posture(monkeypatch, bound):
    # real resolve_runtime_enforcement_posture, only provenance substituted
    r, reasons = _drive(monkeypatch, bound, posture=False)
    assert r.decision == "DENY"
    assert reasons == ("gate7_runtime_execution_unavailable",)
    assert not any(x.decision == "ALLOW" for x in g7._GATE7_RESULTS
                   if x.invocation_id == bound[0].invocation_id)


def test_03_real_posture_resolver_still_reports_unavailable():
    p = g7.resolve_runtime_enforcement_posture()
    assert p.execution_available is False
    assert p.execution_availability == "unavailable"
    assert set(p.matched_no_go_ids) >= {"RE-NOGO-001", "RE-NOGO-002",
                                        "RE-NOGO-010", "RE-NOGO-011"}


def test_04_positive_branch_still_pragma_no_cover_in_source():
    lines = G7_SRC.splitlines()
    idx = next(i for i, l in enumerate(lines) if l.strip() == 'decision="ALLOW",')
    window = "\n".join(lines[max(0, idx - 4):idx + 1])
    assert "pragma: no cover" in window
    assert "unreachable in production" in window


# ═══════════════════════════════════════════════════════════════════════
# B. reprc_schema_version + result identity (matrix 46, 47; REPRC §1, §3)
# ═══════════════════════════════════════════════════════════════════════
def test_05_reprc_schema_version_on_every_result(monkeypatch, bound):
    r_allow, _ = _allow(monkeypatch, bound)
    r_deny, _ = _drive(monkeypatch, bound, posture=False)
    assert r_allow.reprc_schema_version == "REPRC-001/1.0" == g7.REPRC_SCHEMA_VERSION
    assert r_deny.reprc_schema_version == "REPRC-001/1.0"


def test_06_result_id_is_deterministic_for_same_bound_inputs(monkeypatch, bound):
    r1, _ = _allow(monkeypatch, bound)
    r2, _ = _allow(monkeypatch, bound)
    assert r1 is not r2
    assert r1.runtime_enforcement_result_id == r2.runtime_enforcement_result_id
    assert len(r1.runtime_enforcement_result_id) == 64


def test_07_result_id_changes_when_a_security_field_changes(monkeypatch, bound):
    r_ref, _ = _allow(monkeypatch, bound)
    other = dispatch_inputs()
    ident2 = new_dispatch_identity(other)
    r_other, _ = _allow(monkeypatch, (ident2, other))
    assert r_ref.runtime_enforcement_result_id != r_other.runtime_enforcement_result_id


def test_08_result_id_binds_reprc_schema_version(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    from pcae.core.runtime_authority import compute_canonical_digest
    ident, inp = bound
    expected_inputs = {
        "invocation_id": ident.invocation_id,
        "attempt_id": ident.attempt_id,
        "idempotency_key": ident.idempotency_key,
        "pb_decision_digest": r.pb_decision_digest,
        "evaluated_input_digest": r.evaluated_input_digest,
        "authority_freshness_digest": r.authority_freshness_digest,
        "runtime_posture_digest": r.runtime_posture_digest,
        "reprc_schema_version": "REPRC-001/1.0",
    }
    assert r.runtime_enforcement_result_id == compute_canonical_digest(expected_inputs)
    bad = dict(expected_inputs, reprc_schema_version="REPRC-001/2.0")
    assert r.runtime_enforcement_result_id != compute_canonical_digest(bad)


def test_09_result_id_excludes_expires_at_and_evaluated_at(monkeypatch, bound):
    # the id formula is a pure function of the bound inputs; the wall-clock
    # (evaluated_at / expires_at) is not an ingredient (REPRC-001 §3).
    r_now, _ = _allow(monkeypatch, bound, now=NOW)
    r_later, _ = _allow(monkeypatch, bound, now=LATER_WITHIN_TTL)
    assert r_now.runtime_enforcement_result_id == r_later.runtime_enforcement_result_id
    assert r_now.evaluated_at != r_later.evaluated_at
    assert r_now.expires_at != r_later.expires_at


# ═══════════════════════════════════════════════════════════════════════
# C. idempotency_key slot (matrix 10, 17, 35; REPRC §3, §12)
# ═══════════════════════════════════════════════════════════════════════
def test_10_idempotency_key_promoted_to_explicit_slot(monkeypatch, bound):
    ident, _ = bound
    r, _ = _allow(monkeypatch, bound)
    assert r.idempotency_key == ident.idempotency_key
    assert "idempotency_key" in g7.Gate7Result.__slots__


def test_11_changed_idempotency_key_changes_evaluated_input_and_result_id(monkeypatch, bound):
    ident, inp = bound
    r_ref, _ = _allow(monkeypatch, bound)
    ident_mut = type(ident)(
        invocation_id=ident.invocation_id, attempt_id=ident.attempt_id,
        idempotency_key="idem-" + "9" * 40,
    ) if False else None
    # RuntimeDispatchIdentity is frozen/sealed — mutate via a fresh inputs set instead
    inp2 = dispatch_inputs(prompt="A different prompt entirely.")
    ident2 = new_dispatch_identity(inp2)
    r2, _ = _allow(monkeypatch, (ident2, inp2))
    assert ident2.idempotency_key != ident.idempotency_key
    assert r2.evaluated_input_digest != r_ref.evaluated_input_digest
    assert r2.runtime_enforcement_result_id != r_ref.runtime_enforcement_result_id


# ═══════════════════════════════════════════════════════════════════════
# D. TTL / expires_at (matrix 13, 14, 44; REPRC §7)
# ═══════════════════════════════════════════════════════════════════════
def test_12_allow_expires_at_is_evaluated_at_plus_300s(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    assert r.evaluated_at == NOW
    assert r.expires_at == "2026-08-29T00:35:00Z"
    assert r.expires_at > r.evaluated_at
    assert g7._result_expires_at(NOW) == r.expires_at


def test_13_deny_expires_at_equals_evaluated_at(monkeypatch, bound):
    r, _ = _drive(monkeypatch, bound, posture=False)
    assert r.decision == "DENY"
    assert r.expires_at == r.evaluated_at == NOW


def test_14_ttl_constant_is_frozen_at_300(monkeypatch, bound):
    assert g7.REPRC_MAX_RESULT_TTL_SECONDS == 300
    assert "REPRC_MAX_RESULT_TTL_SECONDS: int = 300" in G7_SRC


def test_15_fresh_positive_result_is_not_expired_at_gate10_within_ttl(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    # Gate 10 step 11: re_expires_at must be strictly after its own now.
    assert r.expires_at > LATER_WITHIN_TTL
    assert not (r.expires_at > LATER_PAST_TTL)  # past the 300s window -> expired


def test_16_malformed_authority_current_time_fails_closed_on_allow(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, now="not-a-timestamp-but-bounded")
    assert r is None and reasons == ("gate7_internal_error_fail_closed",)


def test_17_ttl_never_rescues_a_stale_projection(monkeypatch, bound):
    # within the TTL window, but the projection no longer revalidates
    ident, inp = bound
    _substitute_provenance(monkeypatch, proj_ok=False)
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
    monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: False)
    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture", _allow_posture)
    binding = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    g5 = _synthetic_gate5_result(invocation_id=ident.invocation_id,
                                 projection=_SyntheticProjection(subject_scope_binding_digest=binding))
    g6 = _synthetic_gate6_decision(invocation_id=ident.invocation_id, attempt_id=ident.attempt_id)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_stale_validated_authority_projection",)


# ═══════════════════════════════════════════════════════════════════════
# E. Currentness B — no signature change, no currentness_binding (matrix 47, 48)
# ═══════════════════════════════════════════════════════════════════════
def test_18_signature_unchanged_no_resolver_no_posture_param():
    tree = ast.parse(G7_SRC)
    fn = next(n for n in tree.body
             if isinstance(n, ast.FunctionDef) and n.name == "run_gate7_runtime_enforcement")
    params = [a.arg for a in fn.args.args] + [a.arg for a in fn.args.kwonlyargs]
    assert params == ["gate6_decision", "gate5_result", "identity", "inputs",
                      "authority_current_time"]
    assert "resolver" not in " ".join(params)
    assert "posture" not in " ".join(params)


def test_19_no_currentness_binding_slot():
    assert "currentness_binding" not in g7.Gate7Result.__slots__
    # not present as a slot string / digest key / assignment target
    assert '"currentness_binding"' not in G7_SRC
    assert "'currentness_binding'" not in G7_SRC
    assert "currentness_binding =" not in G7_SRC
    assert "self.currentness_binding" not in G7_SRC


def test_20_exactly_three_additive_slots_since_phase_entry():
    old_src = subprocess.run(
        ["git", "show", f"{PHASE_ENTRY}:src/pcae/core/runtime_dispatch_gate7.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    old_slots = set(ast.literal_eval(_slots_literal(old_src)))
    new_slots = set(g7.Gate7Result.__slots__)
    assert new_slots - old_slots == {
        "reprc_schema_version", "runtime_enforcement_result_id", "idempotency_key"}
    assert old_slots - new_slots == set()


def _slots_literal(src: str) -> str:
    tree = ast.parse(src)
    cls = next(n for n in ast.walk(tree)
              if isinstance(n, ast.ClassDef) and n.name == "Gate7Result")
    assign = next(n for n in cls.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "__slots__" for t in n.targets))
    return ast.get_source_segment(src, assign.value)


def test_21_named_stale_rejection_owners_locatable_in_source():
    ra_src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    g8_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate8.py").read_text()
    g10_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10_eligibility.py").read_text()
    # owner 1: Gate 7 creation-time projection revalidation
    assert "revalidate_validated_authority_projection" in G7_SRC
    assert "gate7_stale_validated_authority_projection" in G7_SRC
    # owner 2: Gate 8 independently re-trusts + revalidates the projection
    assert "revalidate_validated_authority_projection" in g8_src
    assert "gate8_stale_validated_authority_projection" in g8_src
    # owner 3/4: Gate 10 step 13 generation re-derivation + step 11 expiry
    assert "authority_generation_resolver" in g10_src
    assert "gate10_authority_generation_drift" in g10_src
    assert "gate10_re_decision_expired" in g10_src
    assert "revalidate_validated_authority_projection" in ra_src


# ═══════════════════════════════════════════════════════════════════════
# F. Non-bearer / immutability / serialization (matrix 23-27, 31, 45; REPRC §4-6)
# ═══════════════════════════════════════════════════════════════════════
def test_22_immutable_after_construction(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    with pytest.raises(AttributeError):
        r.decision = "DENY"
    with pytest.raises(AttributeError):
        r.runtime_enforcement_result_id = "x" * 64
    with pytest.raises(AttributeError):
        del r.expires_at


def test_23_not_caller_constructable_even_with_all_new_kwargs():
    with pytest.raises(TypeError):
        g7.Gate7Result(
            decision="ALLOW", matched_no_go_ids=(), causing_reason_ids=(),
            invocation_id="i", attempt_id="a", request_id="r",
            pb_decision_digest="x", authority_freshness_digest="x",
            evaluated_input_digest="x", runtime_posture_digest="x",
            expires_at=NOW, evaluated_at=NOW,
            reprc_schema_version="REPRC-001/1.0",
            runtime_enforcement_result_id="z" * 64, idempotency_key="k",
            _seal=object())


def test_24_object_new_and_reconstruction_not_a_member(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    assert g7.is_gate7_result(object.__new__(g7.Gate7Result)) is False
    clone = object.__new__(g7.Gate7Result)
    for s in g7.Gate7Result.__slots__:
        try:
            object.__setattr__(clone, s, getattr(r, s))
        except AttributeError:
            pass
    assert g7.is_gate7_result(clone) is False


def test_25_not_serializable(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    with pytest.raises(TypeError):
        copy.copy(r)


def test_26_known_result_id_alone_grants_nothing(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    known = r.runtime_enforcement_result_id

    class _Bearer:
        decision = "ALLOW"
        runtime_enforcement_result_id = known
        matched_no_go_ids = ()
    assert g7.is_gate7_result(_Bearer()) is False


def test_27_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g7.Gate7Result,), {})


def test_28_reprc_schema_version_must_match_on_construction():
    # even the sealed internal constructor rejects an unknown schema version
    with pytest.raises(TypeError):
        g7.Gate7Result(
            decision="ALLOW", matched_no_go_ids=(), causing_reason_ids=(),
            invocation_id="i", attempt_id="a", request_id="r",
            pb_decision_digest="x", authority_freshness_digest="x",
            evaluated_input_digest="x", runtime_posture_digest="x",
            expires_at=NOW, evaluated_at=NOW,
            reprc_schema_version="REPRC-001/9.9",
            runtime_enforcement_result_id="z" * 64, idempotency_key="k",
            _seal=g7._GATE7_RESULT_CONSTRUCTOR_SEAL)


# ═══════════════════════════════════════════════════════════════════════
# G. Restart / duplicate (matrix 26, 27; REPRC §15)
# ═══════════════════════════════════════════════════════════════════════
def test_29_result_from_previous_process_not_a_member(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    saved = g7._GATE7_RESULTS
    monkeypatch.setattr(g7, "_GATE7_RESULTS", set())
    try:
        assert g7.is_gate7_result(r) is False
    finally:
        monkeypatch.setattr(g7, "_GATE7_RESULTS", saved)


def test_30_duplicate_evaluation_is_idempotent(monkeypatch, bound):
    r1, s1 = _allow(monkeypatch, bound)
    r2, s2 = _allow(monkeypatch, bound)
    assert r1 is not r2 and r1 != r2
    assert r1.decision == r2.decision == "ALLOW"
    assert s1 == s2 == ()
    assert r1.evaluated_input_digest == r2.evaluated_input_digest
    assert r1.runtime_enforcement_result_id == r2.runtime_enforcement_result_id


def test_31_no_durable_gate7_store_written(monkeypatch, bound, tmp_path):
    before = list(REPO_ROOT.rglob("consumption.json"))
    _allow(monkeypatch, bound)
    assert list(REPO_ROOT.rglob("consumption.json")) == before


# ═══════════════════════════════════════════════════════════════════════
# H. PB consumed not re-run + anti-escalation (matrix 3-7, 40; REPRC §14)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("decision", ["DENY", "HUMAN_REVIEW", "allow", "ALLOW ", ""])
def test_32_non_allow_pb_decision_rejected_before_posture(monkeypatch, bound, decision):
    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture",
                        lambda: (_ for _ in ()).throw(AssertionError("posture consulted")))
    r, reasons = _drive(monkeypatch, bound, decision=decision, posture=False)
    assert r is None and reasons == (f"gate7_pb_decision_not_allow:{decision}",)


def test_33_pb_allow_plus_re_violation_is_deny(monkeypatch, bound):
    # trusted Gate6 ALLOW, but the (real) posture matches no-gos -> DENY
    r, reasons = _drive(monkeypatch, bound, decision="ALLOW", posture=False)
    assert r.decision == "DENY"
    assert r.matched_no_go_ids != ()


def test_34_gate7_imports_no_pb_policy_symbol():
    tree = ast.parse(G7_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
            for a in n.names:
                imported.add(a.name)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for banned in ("PolicyRegistry", "_compose", "PermissionBroker",
                   "NarrowLocalCliDispatchEligibilityRule", "ExecutionDisabledRule",
                   "permission_broker_foundation", "pcae.core.policy"):
        assert banned not in imported, banned
    assert "PolicyRegistry" not in G7_SRC
    assert "_compose(" not in G7_SRC


def test_35_forged_gate6_decision_rejected(monkeypatch, bound):
    ident, inp = bound
    forged = _synthetic_gate6_decision(invocation_id=ident.invocation_id,
                                       attempt_id=ident.attempt_id)
    r, reasons = g7.run_gate7_runtime_enforcement(
        forged, gate5_result=object(), identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None and reasons == ("gate7_untrusted_gate6_decision",)


# ═══════════════════════════════════════════════════════════════════════
# I. Lineage / replay matrix (matrix 15-21; REPRC §3.1, §12)
# ═══════════════════════════════════════════════════════════════════════
def test_36_changed_invocation_id_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, g5_inv="inv-" + "z" * 32)
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_37_changed_attempt_id_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, g6_att="att-" + "z" * 32)
    assert r is None and reasons == ("gate7_invocation_binding_mismatch",)


def test_38_changed_subject_scope_binding_rejected(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, binding_digest="0" * 64)
    assert r is None and reasons == ("gate7_authority_subject_scope_mismatch",)


def test_39_changed_runtime_target_changes_evaluated_input_digest(monkeypatch, bound):
    r_ref, _ = _allow(monkeypatch, bound)
    inp2 = dispatch_inputs(runtime_target_id="local-cli-fixture-2")
    ident2 = new_dispatch_identity(inp2)
    r2, _ = _allow(monkeypatch, (ident2, inp2))
    assert r2.evaluated_input_digest != r_ref.evaluated_input_digest


def test_40_network_requirement_true_is_ineligible(monkeypatch, bound):
    ident, inp = bound
    inp2 = type(inp).__call__ if False else None
    from dataclasses import replace as _replace
    bad = _replace(inp, network_requirement=True)
    r, reasons = _drive(monkeypatch, (ident, bad), inputs_override=bad)
    # network drift fails closed — either as a construction-fact violation
    # or as target ineligibility; both are the correct conservative outcome.
    assert r is None
    assert reasons[0] in (
        "gate7_runtime_target_ineligible",
        "gate7_request_currentness_drift:invalid_construction_input_facts",
    ), reasons


def test_41_changed_pb_decision_digest_changes_result_id(monkeypatch, bound):
    r_ref, _ = _allow(monkeypatch, bound)
    r_other, _ = _allow(monkeypatch, bound, request_id="pbr-" + "f" * 12)
    assert r_other.pb_decision_digest != r_ref.pb_decision_digest
    assert r_other.runtime_enforcement_result_id != r_ref.runtime_enforcement_result_id


# ═══════════════════════════════════════════════════════════════════════
# J. Downstream independence (matrix 28-32, 34, 35; REPRC §9-11, §18)
# ═══════════════════════════════════════════════════════════════════════
def test_42_gate8_still_required_negative_is_hard_stop():
    g8_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate8.py").read_text()
    assert "gate8_gate7_decision_not_allow" in g8_src
    assert 'decision == "ALLOW"' in g8_src or "decision != \"ALLOW\"" in g8_src


def test_43_gate9_is_sole_consumption_owner_gate7_writes_nothing():
    tree = ast.parse(G7_SRC)
    attrs = {n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for banned in ("consume", "bind", "record_consumption", "write", "mutate",
                   "run_gate9", "run_gate6_permission_broker", "run_gate5"):
        assert banned not in attrs
    # no filesystem writes of any kind
    assert "open(" not in G7_SRC and ".write(" not in G7_SRC
    assert "_write_consumption" not in G7_SRC


def test_44_gate10_capability_reread_independent_of_gate7():
    g10_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10_eligibility.py").read_text()
    assert "gate10_runtime_capability_not_unavailable" in g10_src


def test_45_n16_5_wall_real_validate_approval_yields_no_projection():
    from _rdw3w_helpers import build_approval, matching_context, always_unconsumed
    ap = build_approval()
    proj, _ = ra.validate_approval(ap, context=matching_context(ap),
                                   consumption_lookup=always_unconsumed)
    assert proj is None


def test_46_runtime_state_unchanged_after_positive_eval(monkeypatch, bound):
    _allow(monkeypatch, bound)
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    assert ri.get_state().current_state == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"


# ═══════════════════════════════════════════════════════════════════════
# K. Positive rationale vocabulary (matrix 43; REPRC §20)
# ═══════════════════════════════════════════════════════════════════════
def test_47_positive_result_carries_non_empty_reason_vocabulary(monkeypatch, bound):
    r, _ = _allow(monkeypatch, bound)
    assert r.causing_reason_ids == g7.GATE7_POSITIVE_CAUSING_REASON_IDS
    assert r.causing_reason_ids != ()
    assert "gate7_synthetic_evaluation_path" in r.causing_reason_ids
    assert "gate7_runtime_enforcement_satisfied" in r.causing_reason_ids


def test_48_negative_reason_set_unchanged(monkeypatch, bound):
    r, reasons = _drive(monkeypatch, bound, posture=False)
    assert reasons == ("gate7_runtime_execution_unavailable",)
    assert "gate7_runtime_execution_unavailable" in r.causing_reason_ids
    assert any(c.startswith("gate7_safety_no_go:RE-NOGO-") for c in r.causing_reason_ids)


# ═══════════════════════════════════════════════════════════════════════
# L. No-effect AST scans (matrix 36, 37; REPRC §17, §18)
# ═══════════════════════════════════════════════════════════════════════
def test_49_no_effect_primitive_call_syntax_in_module():
    # actual call / attribute syntax an effect would need — not prose in the
    # module's own prohibition list.
    for banned in ("adapter.dispatch(", ".dispatch(", "Popen(", "subprocess.",
                   "os.system(", "os.execv", "os.spawn", "socket.socket(",
                   "pty.spawn", ".connect(", "webauthn", "ctap2"):
        assert banned not in G7_SRC, banned


def test_50_module_imports_nothing_effectful():
    tree = ast.parse(G7_SRC)
    forbidden = {"subprocess", "socket", "requests", "httpx", "urllib", "http",
                 "asyncio", "multiprocessing", "ctypes", "pty", "fcntl", "signal",
                 "ssl", "selectors"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                assert a.name.split(".")[0] not in forbidden
        elif isinstance(n, ast.ImportFrom) and n.module:
            assert n.module.split(".")[0] not in forbidden
            for bad in ("runtime_dispatch_gate8", "runtime_dispatch_gate9",
                        "runtime_dispatch_gate10", "shell_gate",
                        "runtime_invocation_authority_consumption", "runtime_adapter"):
                assert bad not in n.module


# ═══════════════════════════════════════════════════════════════════════
# M. Consumer inventory guard (matrix 38, 39; REPRC §21)
# ═══════════════════════════════════════════════════════════════════════
AUTHORIZED_GATE7_CONSUMERS = {
    "src/pcae/core/runtime_dispatch_gate8.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
}
#: Exact, finite set of test files that *import* the Gate-7 module or its
#: symbols (real `import` statements, not path strings in scope-fence
#: comments). No wildcard, no fnmatch, no package prefix.
AUTHORIZED_GATE7_TEST_IMPORTERS = {
    "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py",
    "tests/test_gate7_runtime_enforcement_coordinator_integration_3w1r2b1r1_1r13_2.py",
    "tests/test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py",
    "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py",
    "tests/test_gate8_process_containment_coordinator_independent_verification_3w1r2b1r1_1r13_5.py",
    "tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py",
    "tests/test_gate9_atomic_authority_consumption_coordinator_independent_verification_3w1r2b1r1_1r15.py",
    "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py",
    "tests/test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py",
}


def test_51_production_gate7result_consumer_inventory_is_exact():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate7Result|is_gate7_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    hits.discard("src/pcae/core/runtime_dispatch_gate7.py")  # defines it
    assert hits == AUTHORIZED_GATE7_CONSUMERS, sorted(hits)


def test_52_unauthorized_extra_consumer_would_fail_the_exact_check():
    intruder = "src/pcae/core/some_new_module.py"
    simulated = set(AUTHORIZED_GATE7_CONSUMERS) | {intruder}
    assert simulated != AUTHORIZED_GATE7_CONSUMERS
    assert (simulated - AUTHORIZED_GATE7_CONSUMERS) == {intruder}


def test_53_test_importers_of_gate7_symbols_are_a_known_finite_set():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E",
         r"import +runtime_dispatch_gate7|runtime_dispatch_gate7 +import|"
         r"runtime_dispatch_gate7 +as |from +pcae\.core\.runtime_dispatch_gate7",
         "--", "tests"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    # this file is untracked until the phase's test commit; tolerate its
    # absence from `git grep` output pre-commit.
    self_rel = "tests/" + Path(__file__).name
    hits.discard(self_rel)
    known = AUTHORIZED_GATE7_TEST_IMPORTERS - {self_rel}
    unexpected = hits - known
    assert unexpected == set(), sorted(unexpected)
    missing = known - hits
    assert missing == set(), sorted(missing)
    # every allowlist entry is a concrete repo-relative path (exact, finite)
    for entry in AUTHORIZED_GATE7_TEST_IMPORTERS:
        assert entry.startswith("tests/") and entry.endswith(".py")
        assert set(entry) & set("*?[]") == set()


def test_54_consumer_allowlists_are_exact_and_finite():
    # every authorized entry is a literal repo-relative path; none is a glob
    for entry in (AUTHORIZED_GATE7_CONSUMERS | AUTHORIZED_GATE7_TEST_IMPORTERS):
        assert isinstance(entry, str)
        assert entry.endswith(".py")
        assert not (set(entry) & set("*?[]"))
    src = (REPO_ROOT / "tests" / Path(__file__).name).read_text()
    # the production consumer check is exact equality, not a subset relation
    assert "hits == AUTHORIZED_GATE7_CONSUMERS" in src
    assert len(AUTHORIZED_GATE7_CONSUMERS) == 3


# ═══════════════════════════════════════════════════════════════════════
# N. Scope fence — production/contract diff since phase entry (REPRC §21, .1R.25 §29)
# ═══════════════════════════════════════════════════════════════════════
def test_55_production_diff_since_phase_entry_is_only_gate7():
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert changed == {"src/pcae/core/runtime_dispatch_gate7.py"}, sorted(changed)


def test_56_normative_contract_diff_since_phase_entry_is_only_reprc():
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY, "HEAD", "--", "docs/contracts"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert changed == {"docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"}, sorted(changed)


@pytest.mark.parametrize("rel", [
    "src/pcae/core/runtime_dispatch_permission.py",
    "src/pcae/core/runtime_dispatch_gate8.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    "src/pcae/core/runtime_invocation_authority_consumption.py",
    "src/pcae/core/runtime_authority.py",
    "src/pcae/core/runtime_enforcement_safety_authorization.py",
    "src/pcae/core/runtime_introspection.py",
])
def test_57_downstream_and_sibling_modules_byte_unchanged(rel):
    diff = subprocess.run(["git", "diff", PHASE_ENTRY, "HEAD", "--", rel],
                          cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    assert diff == "", rel


@pytest.mark.parametrize("rel", [
    "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
    "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
    "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
    "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md",
])
def test_58_frozen_contracts_byte_unchanged_since_phase_entry(rel):
    diff = subprocess.run(["git", "diff", PHASE_ENTRY, "HEAD", "--", rel],
                          cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    assert diff == "", rel


def test_59_runtime_inspect_state_unchanged():
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# O. REPRC-001 v1.0 contract-production equivalence map (REPRC §22)
# ═══════════════════════════════════════════════════════════════════════
def test_60_reprc_contract_frozen_and_v1_0():
    assert REPRC.startswith("# REPRC-001 v1.0 — Runtime Enforcement Positive Result Contract")
    assert "**Version:** 1.0" in REPRC
    assert "**Status:** FROZEN" in REPRC


def test_61_reprc_equivalence_map():
    checks = {
        # REPRC clause -> (source text present in production or a sibling)
        "§1 schema literal": g7.REPRC_SCHEMA_VERSION == "REPRC-001/1.0",
        "§3 result id ingredients": all(
            k in G7_SRC for k in ("runtime_enforcement_result_id", "pb_decision_digest",
                                  "authority_freshness_digest", "runtime_posture_digest")),
        "§6 immutability guard": "Gate7Result is immutable" in G7_SRC,
        "§7 ttl 300": "REPRC_MAX_RESULT_TTL_SECONDS: int = 300" in G7_SRC,
        "§8 no signature change": "authority_generation_resolver" not in G7_SRC,
        "§8 currentness anchor": "authority_freshness_digest" in G7_SRC,
        "§13 no admission binding": "admission_record_digest" not in G7_SRC
                                    and "SupplyChainAdmissionResolver" not in G7_SRC,
        "§14 pb not re-run": "PolicyRegistry" not in G7_SRC and "_compose" not in G7_SRC,
        "§20 positive vocab": "gate7_runtime_enforcement_satisfied" in G7_SRC,
        "§21 sole constructor": "run_gate7_runtime_enforcement" in G7_SRC,
    }
    failed = [k for k, ok in checks.items() if not ok]
    assert failed == [], failed


def test_62_no_rdgo_or_hpac_or_pb_contract_file_in_the_diff():
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY, "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    for frozen in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
    ):
        assert frozen not in changed, frozen
    # the new contract carries no RDGO/HPAC version-header bump
    reprc = (REPO_ROOT / "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md").read_text()
    assert "RDGO-001 stays v3.1" in reprc
    assert "HPAC-001 stays v2.1" in reprc
