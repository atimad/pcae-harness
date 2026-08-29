"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13 — Independent Verification of the
Gate-6 Permission Broker Production Consumption Integration (.1R.12).

RE-DERIVE. DO NOT TRUST. These tests were written from the primary
contracts (RDGO-001 v3.0 §7, PBRD-001 v2.0 §4 fact 14 / §5 / §7 / §9 / §10 /
§12 / §15, POL-005 in ``permission_broker_foundation.ExecutionDisabledRule``,
RIHAC-001 v2.0 §16 step 12) and current production source — never from the
.1R.12 report, the .1R.12 tests, or function/type names.

Two coverage gaps in the .1R.12 suite are closed here:

1. the .1R.12 suite proves the step-2 invocation-binding guard, the
   trusted-builder call, and the single-``evaluate`` call site only by
   source-substring / AST assertions, because on every obtainable path
   ``is_gate5_result`` is ``False`` (the permanent NON-REAL hard stop) and
   ``run_gate6_permission_broker`` returns at step 1;
2. no test drives the Gate-6 envelope (steps 2→5) at runtime.

To close them WITHOUT manufacturing real human authority, a small number of
tests below install a **test-boundary substitution** for the
``run_gate5``-provenance predicate only (``monkeypatch`` on
``runtime_dispatch_gate5.is_gate5_result``). This substitutes the provenance
gate that a real FIDO2/UI ceremony would satisfy; it manufactures no
``ValidatedAuthorityProjection`` and no approval. In every such test the
referenced projection is ``None`` or a non-registry lookalike, so
``approval_present`` stays ``False``, ``project_human_authority_binding``
returns the empty binding, and **no ``ALLOW`` is ever produced** — the
evaluator returns POL-005 ``DENY`` (real request) or POL-004
``HUMAN_REVIEW`` (simulation). Positive production Gate-6 authority remains
unreachable, exactly as .1R.12 states.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_permission as rdp

from _rdw3w_helpers import dispatch_inputs, full_chain, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The .1R.13 verification-entry commit (HEAD when this phase began): the
#: last .1R.12 finalization commit. .1R.13 introduces no ``src/`` change, so
#: this is also the regression-attribution baseline.
PHASE_1R13_ENTRY = "e04ca7af2dad7276205ab4150669f472ca49cca0"

#: The pre-.1R.12 baseline (parent of the first .1R.12 commit): the exact
#: fixed SHA against which the .1R.12 production diff is one file.
PRE_1R12_BASELINE = "70d1e454"

NOW = "2026-08-27T00:30:00Z"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════
def _git_names(*args, base=PRE_1R12_BASELINE, head="HEAD"):
    return subprocess.run(
        ["git", "diff", "--name-only", base, head, "--", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()


def _blob(rev, path):
    return subprocess.run(
        ["git", "rev-parse", f"{rev}:{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _forged_gate5_result(*, invocation_id="inv-" + "a" * 32, projection=None):
    """A fully field-populated ``Gate5Result`` lookalike built without
    ``run_gate5`` — no identity-registry provenance."""
    forged = object.__new__(gate5.Gate5Result)
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
        object.__setattr__(forged, name, value)
    return forged


def _accept_forged_gate5(monkeypatch, forged):
    """TEST-BOUNDARY ONLY: substitute the ``run_gate5`` provenance predicate
    so the Gate-6 envelope (steps 2→5) becomes reachable. Manufactures no
    authority — ``forged.projection`` is ``None`` / untrusted throughout."""
    monkeypatch.setattr(
        gate5, "is_gate5_result",
        lambda c: c is forged or (isinstance(c, gate5.Gate5Result) and c in gate5._GATE5_RESULTS),
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Sole Gate-6 owner — independent inventory
# ═══════════════════════════════════════════════════════════════════════
def test_run_gate6_is_the_only_production_caller_of_the_trusted_dispatch_builder():
    """Every production call site of ``build_runtime_dispatch_permission_broker_request``
    (the .1R.7 trusted builder) and of the seal-bearing
    ``_build_runtime_dispatch_permission_broker_request`` must be inside
    ``runtime_dispatch_permission.py`` and, for the public builder, inside
    ``run_gate6_permission_broker``."""
    hits = subprocess.run(
        ["git", "grep", "-n", "build_runtime_dispatch_permission_broker_request", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    call_sites = [
        h for h in hits
        if "build_runtime_dispatch_permission_broker_request(" in h
        and "def " not in h.split(":", 2)[2]
    ]
    for h in call_sites:
        assert h.split(":", 1)[0] == "src/pcae/core/runtime_dispatch_permission.py", h
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    after_gate6 = src[src.index("def run_gate6_permission_broker"):]
    assert "build_runtime_dispatch_permission_broker_request(" in after_gate6


def test_generic_builder_refuses_runtime_dispatch_requests():
    """No parallel authority path: the generic ``build_permission_broker_request``
    raises for a runtime_dispatch action or any runtime_dispatch context."""
    with pytest.raises(ValueError):
        pbf.build_permission_broker_request(
            action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
            execution_class=pbf.EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-006",
            requested_capability="local_cli_dispatch",
        )


def test_no_downstream_production_consumer_of_gate6_symbols():
    """RDGO-001 §7 / §8 / prompt §25 / .1R.13.1 §29: the ONLY authorized
    downstream production consumer of ``Gate6Decision`` / ``is_gate6_decision``
    is the Gate-7 coordinator (``runtime_dispatch_gate7``, added by the
    authorized .1R.13.2 phase). ``run_gate6_permission_broker`` still has no
    downstream production caller. Phase-aware invariant (V-13-1 conversion of
    a point-in-time equality assertion)."""
    hits = set(
        subprocess.run(
            ["git", "grep", "-l", "-E",
             r"run_gate6_permission_broker|Gate6Decision|is_gate6_decision", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    assert hits <= {
        "src/pcae/core/runtime_dispatch_permission.py",  # defines them
        "src/pcae/core/runtime_dispatch_gate7.py",  # sole authorized Gate-7 consumer
    }, f"unexpected Gate-6 symbol consumer: {sorted(hits - {'src/pcae/core/runtime_dispatch_permission.py', 'src/pcae/core/runtime_dispatch_gate7.py'})}"
    # the Gate-7 module consumes only the two provenance/type symbols, never
    # calls the Gate-6 coordinator entrypoint (it consumes the decision object)
    g7_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    g7_tree = ast.parse(g7_src)
    called = {
        n.func.id for n in ast.walk(g7_tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    } | {
        n.func.attr for n in ast.walk(g7_tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert "run_gate6_permission_broker" not in called


# ═══════════════════════════════════════════════════════════════════════
# 2. Gate5Result provenance boundary (behavioral, not source-grep)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("candidate_factory", [
    lambda: None,
    lambda: _forged_gate5_result(),
    lambda: object.__new__(gate5.Gate5Result),
    lambda: type("V", (), {"validated": True})(),
    lambda: type("L", (), {"projection": None, "invocation_id": "inv-" + "a" * 32})(),
    lambda: "ria-" + "0" * 32,
    lambda: 42,
])
def test_only_registry_member_gate5_result_is_trusted(candidate_factory):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    decision, reasons = rdp.run_gate6_permission_broker(
        candidate_factory(), identity=identity, inputs=inputs, authority_current_time=NOW,
    )
    assert decision is None
    assert reasons == ("gate6_untrusted_gate5_result",)
    assert len(rdp._GATE6_DECISIONS) == 0


def test_real_gate5_result_is_non_serializable_and_non_copyable():
    stub = object.__new__(gate5.Gate5Result)
    with pytest.raises(TypeError):
        pickle.dumps(stub)
    with pytest.raises(TypeError):
        copy.deepcopy(_forged_gate5_result())


def test_is_gate5_result_never_true_for_a_reconstruction():
    assert gate5.is_gate5_result(_forged_gate5_result()) is False
    assert gate5.is_gate5_result(object.__new__(gate5.Gate5Result)) is False


# ═══════════════════════════════════════════════════════════════════════
# 3. Exact invocation binding (runtime, via test-boundary provenance sub)
# ═══════════════════════════════════════════════════════════════════════
def test_invocation_binding_mismatch_is_rejected_at_runtime(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id="inv-" + "b" * 32)  # != identity
    _accept_forged_gate5(monkeypatch, forged)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
    )
    assert decision is None
    assert reasons == ("gate6_invocation_binding_mismatch",)
    assert len(rdp._GATE6_DECISIONS) == 0


def test_identity_type_guard_reached_when_provenance_substituted(monkeypatch):
    forged = _forged_gate5_result()
    _accept_forged_gate5(monkeypatch, forged)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=object(), inputs=dispatch_inputs(), authority_current_time=NOW,
    )
    assert decision is None
    assert reasons == ("gate6_untrusted_runtime_dispatch_identity",)


def test_bad_authority_current_time_and_simulation_flag_rejected(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)
    _accept_forged_gate5(monkeypatch, forged)
    d1, r1 = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time="   ",
    )
    assert d1 is None and r1 == ("gate6_invalid_authority_current_time",)
    d2, r2 = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        simulation_only="yes",  # type: ignore[arg-type]
    )
    assert d2 is None and r2 == ("gate6_invalid_simulation_only",)


# ═══════════════════════════════════════════════════════════════════════
# 4. Trusted-builder exclusivity / untrusted projection rejected
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_projection_on_gate5_result_fails_request_construction(monkeypatch):
    """Even past the provenance gate, a projection with no registry
    provenance is rejected inside the trusted builder (B1 discipline)."""
    fake_projection = object.__new__(ra.ValidatedAuthorityProjection)
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id, projection=fake_projection)
    _accept_forged_gate5(monkeypatch, forged)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
    )
    assert decision is None
    assert len(reasons) == 1
    assert reasons[0].startswith("gate6_request_construction_failed:")
    assert "untrusted_validated_authority_projection" in reasons[0]


def test_gate6_never_hand_rolls_a_permission_broker_request():
    mod = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    fn = next(n for n in ast.walk(mod)
              if isinstance(n, ast.FunctionDef) and n.name == "run_gate6_permission_broker")
    constructed = {
        s.func.id for s in ast.walk(fn)
        if isinstance(s, ast.Call) and isinstance(s.func, ast.Name)
    }
    assert "PermissionBrokerRequest" not in constructed
    assert "_build_runtime_dispatch_permission_broker_request" not in constructed
    assert "build_runtime_dispatch_permission_broker_request" in constructed


# ═══════════════════════════════════════════════════════════════════════
# 5. Canonical evaluator identity + exactly-one evaluation
# ═══════════════════════════════════════════════════════════════════════
def test_gate6_calls_the_unmodified_canonical_evaluator_exactly_once(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)  # projection=None
    _accept_forged_gate5(monkeypatch, forged)

    calls = []
    real_evaluate = pbf.PermissionBroker.evaluate

    def counting_evaluate(self, request):
        calls.append(request)
        return real_evaluate(self, request)

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", counting_evaluate)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        simulation_only=False,
    )
    assert len(calls) == 1
    assert calls[0].action_type == pbf.ACTION_TYPE_RUNTIME_DISPATCH
    assert reasons == ()
    assert decision is not None
    assert decision.decision == pbf.DECISION_DENY  # POL-005


def test_gate6_rejects_a_non_permission_broker_evaluator(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)
    _accept_forged_gate5(monkeypatch, forged)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        broker=object(),  # type: ignore[arg-type]
    )
    assert decision is None
    assert reasons == ("gate6_untrusted_permission_broker",)


# ═══════════════════════════════════════════════════════════════════════
# 6. DENY > HUMAN_REVIEW > ALLOW precedence (independent derivation)
# ═══════════════════════════════════════════════════════════════════════
def test_deny_precedes_human_review_real_non_simulation_request():
    _, projection, request, decision = full_chain(simulation_only=False)
    assert projection is None
    assert request.simulation_only is False
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_human_review_precedes_allow_when_only_approval_missing():
    _, _, request, decision = full_chain(simulation_only=True)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids
    assert decision.decision != pbf.DECISION_ALLOW


def test_compose_precedence_is_deny_then_human_review_then_allow():
    """Re-derive the ordering directly from ``_compose``."""
    src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    compose = src[src.index("def _compose("):]
    compose = compose[:compose.index("\ndef ")]
    assert "for decision_value in (DECISION_DENY, DECISION_HUMAN_REVIEW):" in compose
    # ALLOW only reached after both DENY and HUMAN_REVIEW find no match
    assert compose.index("DECISION_DENY, DECISION_HUMAN_REVIEW") < compose.index("DECISION_ALLOW")
    assert "not results" in compose  # empty -> fail closed to DENY


# ═══════════════════════════════════════════════════════════════════════
# 7. POL-005 dominance — not overridable by (would-be) human authority
# ═══════════════════════════════════════════════════════════════════════
def test_pol005_denies_every_non_simulation_request_bytewise_frozen():
    assert _git_names("src/pcae/core/permission_broker_foundation.py") == []
    src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    assert 'policy_id = "POL-005"' in src
    assert "if request.simulation_only:" in src
    assert 'decision_reason="execution_boundary_unavailable"' in src


def test_pol005_ignores_approval_present_true():
    _, _, request, _ = full_chain(simulation_only=False)
    forced = dataclasses.replace(request, approval_present=True, simulation_only=False)
    result = pbf.ExecutionDisabledRule().evaluate(forced)
    assert result.triggered is True
    assert result.decision == pbf.DECISION_DENY
    assert result.matched_no_go_ids == ("NG-025",)


def test_full_evaluation_denies_non_simulation_even_with_approval_present_forced():
    """Forcing ``approval_present=True`` onto a request whose 14 facts carry
    no ``human_authority_binding`` is itself rejected fail-closed by the
    unmodified structural validator (``invalid_runtime_dispatch_request``)
    BEFORE policy evaluation — a caller cannot smuggle a bare boolean past
    the binding/flag consistency check. Either way the outcome is DENY; a
    non-simulation request is never ALLOW."""
    _, _, request, _ = full_chain(simulation_only=False)
    forced = dataclasses.replace(request, approval_present=True, simulation_only=False)
    decision = pbf.PermissionBroker().evaluate(forced)
    assert decision.decision == pbf.DECISION_DENY
    assert decision.decision_reason in (
        "invalid_runtime_dispatch_request", "execution_boundary_unavailable",
    )


# ═══════════════════════════════════════════════════════════════════════
# 8. Gate6Decision semantics — ALLOW is not capability; DENY fails closed
# ═══════════════════════════════════════════════════════════════════════
def test_no_allow_reachable_without_a_trusted_authority_projection(monkeypatch):
    """With projection=None, simulation_only=True: HUMAN_REVIEW, never ALLOW."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)
    _accept_forged_gate5(monkeypatch, forged)
    decision, reasons = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        simulation_only=True,
    )
    assert decision is not None
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert decision.approval_present is False


def test_gate6_decision_from_envelope_is_registry_member_but_not_transferable(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)
    _accept_forged_gate5(monkeypatch, forged)
    decision, _ = rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        simulation_only=False,
    )
    assert rdp.is_gate6_decision(decision) is True
    # anti-transfer: cannot be pickled, deepcopied, or reconstructed
    with pytest.raises(TypeError):
        pickle.dumps(decision)
    with pytest.raises(TypeError):
        copy.deepcopy(decision)
    clone = object.__new__(rdp.Gate6Decision)
    assert rdp.is_gate6_decision(clone) is False
    assert decision != clone and decision == decision


def test_gate6_decision_cannot_be_caller_constructed_or_subclassed():
    with pytest.raises(TypeError):
        rdp.Gate6Decision(
            pb_decision=None, approval_present=False, invocation_id="i", attempt_id="a",
            request_id="r", simulation_only=False, evaluated_at="t", _seal=object(),
        )
    with pytest.raises(TypeError):
        type("Evil", (rdp.Gate6Decision,), {})


# ═══════════════════════════════════════════════════════════════════════
# 9. V-4 — PBRD-001 §4 fact 14 (7-field) vs production (3-field)
# ═══════════════════════════════════════════════════════════════════════
def test_pbrd_fact14_enumerates_exactly_seven_subfields():
    contract = (REPO_ROOT / "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text()
    row = next(l for l in contract.splitlines() if l.startswith("| 14 |"))
    for field in (
        "approval_id", "approval_digest", "authority_projection_id",
        "authority_projection_digest", "authority_contract_version",
        "proof_validation_digest", "request_binding_digest",
    ):
        assert field in row, field
    assert "RIHAC-001/2.0" in row


def test_production_binding_has_exactly_three_fields():
    fields = [f.name for f in dataclasses.fields(pbf.RuntimeDispatchHumanAuthorityBinding)]
    assert fields == ["approval_id", "approval_record_digest", "validation_evidence_digest"]


def test_validation_evidence_digest_commits_to_every_omitted_semantic():
    """The single 3-field ``validation_evidence_digest`` is ``evidence_digest()``
    over the full projection payload, which includes proof_id,
    subject_scope_binding_digest, the provenance/freshness/expiry verdicts,
    mechanism_assurance, invocation_id and schema_version — i.e. it
    cryptographically binds every semantic the 7-field enumeration names
    (projection identity/digest, proof validation, request binding,
    contract version). Any change to any of them changes the digest."""
    payload_src = (REPO_ROOT / "src/pcae/core/runtime_authority.py").read_text()
    binding = payload_src[payload_src.index("def _binding_payload"):]
    binding = binding[:binding.index("def evidence_digest")]
    for key in (
        "approval_id", "record_digest", "subject_scope_binding_digest",
        "provenance_verdict", "freshness_verdict_digest", "expiry_verdict",
        "consumption_state_verdict", "principal_id", "proof_id",
        "mechanism_id", "mechanism_assurance", "invocation_id", "schema_version",
    ):
        assert f'"{key}"' in binding, key


def test_v4_no_collision_two_distinct_authority_contexts_cannot_share_a_binding():
    """Construct two projection payloads differing only in an
    'omitted-from-3-field' semantic (proof_id) and confirm the resulting
    ``evidence_digest`` — hence ``validation_evidence_digest`` — differs."""
    base = dict(
        approval_id="ria-" + "0" * 32, record_digest="a" * 64,
        subject_scope_binding_digest="b" * 64, provenance_verdict="ok",
        freshness_verdict_digest="c" * 64, expiry_verdict="ok",
        consumption_state_verdict="none", validated_at=NOW, principal_id="hp-1",
        proof_id="proof-1", mechanism_id="m-1", mechanism_assurance="NON_REAL",
        invocation_id="inv-" + "a" * 32,
    )
    p1 = ra.ValidatedAuthorityProjection(**base)
    p2 = ra.ValidatedAuthorityProjection(**{**base, "proof_id": "proof-2"})
    assert p1.evidence_digest() != p2.evidence_digest()
    p3 = ra.ValidatedAuthorityProjection(**{**base, "subject_scope_binding_digest": "d" * 64})
    assert p1.evidence_digest() != p3.evidence_digest()


def test_request_binding_semantic_is_independently_re_enforced_pre_construction():
    """``request_binding_digest`` (7-field) has an operational analogue: the
    builder recomputes ``_expected_subject_scope_binding_digest(identity,
    inputs)`` and rejects a projection whose digest differs, and
    ``run_gate6`` separately rejects ``gate5_result.invocation_id !=
    identity.invocation_id``."""
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert "validated_authority.subject_scope_binding_digest != expected_binding" in src
    assert "validated_authority_subject_scope_mismatch" in src
    assert "gate5_result.invocation_id != identity.invocation_id" in src


# ═══════════════════════════════════════════════════════════════════════
# 10. V-2 / V-3 — no Gate-6 dependence on HPAC lifecycle sequence-3 wording
# ═══════════════════════════════════════════════════════════════════════
def test_gate6_path_never_touches_hpac_lifecycle_or_sequence3():
    mod = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    imported = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[-1])
    assert "hpac_lifecycle" not in imported
    assert "hpac_verifier" not in imported
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert "PROOF_VERIFIED_AND_BOUND" not in src
    assert "sequence3" not in src.lower()


# ═══════════════════════════════════════════════════════════════════════
# 11. Isolation — no Gate-7/8/9/10, runtime unchanged
# ═══════════════════════════════════════════════════════════════════════
_FORBIDDEN_IMPORT_ROOTS = {
    "subprocess", "socket", "requests", "httpx", "urllib", "http",
    "fido2", "webauthn", "ctap", "smartcard", "usb", "serial", "ssl",
    "asyncio", "multiprocessing", "ctypes",
}
_FORBIDDEN_MODULES = {
    "backend_invocations", "shell_gate", "runtime_invocation_authority_consumption",
    "runtime_dispatch_gate9", "runtime_adapter", "mock_runtime_adapter",
    "runtime_dispatch_effect", "runtime_introspection", "runtime_enforcement",
}


def test_module_imports_nothing_effectful_and_no_downstream_gate():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    imported_roots, imported_leaves = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported_roots.add(a.name.split(".")[0])
                imported_leaves.add(a.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
            imported_leaves.add(node.module.split(".")[-1])
            for a in node.names:
                imported_leaves.add(a.name)
    assert imported_roots.isdisjoint(_FORBIDDEN_IMPORT_ROOTS)
    assert imported_leaves.isdisjoint(_FORBIDDEN_MODULES), imported_leaves & _FORBIDDEN_MODULES


def test_no_consumption_json_and_runtime_constants_unchanged(tmp_path, monkeypatch):
    from pcae.core import runtime_introspection as ri

    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs, root=tmp_path)
    forged = _forged_gate5_result(invocation_id=identity.invocation_id)
    _accept_forged_gate5(monkeypatch, forged)
    rdp.run_gate6_permission_broker(
        forged, identity=identity, inputs=inputs, authority_current_time=NOW,
        simulation_only=False,
    )
    assert list(tmp_path.rglob("consumption.json")) == []
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# 12. Production-file scope + contract byte-identity (fixed SHA)
# ═══════════════════════════════════════════════════════════════════════
# Phase-aware production-scope invariant (converted from a point-in-time
# equality assertion, Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.2 / V-13-1).
# The .1R.12 production weight is still exactly runtime_dispatch_permission.py;
# any additional src/pcae change since PRE_1R12_BASELINE must be a member of
# the known, individually-authorized runtime-dispatch-gate-chain surface
# (.1R.13.2 adds runtime_dispatch_gate7.py). An unauthorized expansion fails.
_AUTHORIZED_POST_1R12_CHAIN_SURFACE = {
    "src/pcae/core/runtime_dispatch_permission.py",  # Gate 6 (.1R.12)
    "src/pcae/core/runtime_dispatch_gate7.py",  # Gate 7 (.1R.13.2)
    "src/pcae/core/runtime_dispatch_gate8.py",  # Gate 8 (.1R.13.4)
}


def test_1r12_production_diff_is_exactly_one_file():
    changed = set(_git_names("src/pcae"))
    assert "src/pcae/core/runtime_dispatch_permission.py" in changed
    unexpected = changed - _AUTHORIZED_POST_1R12_CHAIN_SURFACE
    assert unexpected == set(), f"unauthorized production-file expansion: {sorted(unexpected)}"


def test_no_contract_or_pb_foundation_change_since_pre_1r12():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/hpac_lifecycle.py",
    ):
        assert _git_names(rel) == [], rel


def test_contract_blob_hashes_identical_baseline_and_head():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
    ):
        assert _blob(PRE_1R12_BASELINE, rel) == _blob("HEAD", rel), rel


# ═══════════════════════════════════════════════════════════════════════
# 13. Regression attribution — the two known point-in-time scope guards
# ═══════════════════════════════════════════════════════════════════════
def test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable():
    """Two .1R.10 / .1R.11 suite tests assert 'only my planned files changed
    since my frozen phase-entry SHA'. .1R.12's legitimate single-file
    addition (runtime_dispatch_permission.py) trips both. They are:
      * present at the .1R.13 entry commit already,
      * caused solely by .1R.12's source addition (A/B: pass at the .1R.10
        entry, fail at HEAD),
      * non-functional (frozen-baseline hygiene assertions),
      * NOT re-triggered or worsened by .1R.13 (which adds no src/ file).
    This test pins that attribution so a future reader is not surprised."""
    # .1R.13 itself added no src file. The later authorized .1R.13.2 / .1R.13.4
    # phases add exactly runtime_dispatch_gate7.py (Gate 7) and
    # runtime_dispatch_gate8.py (Gate 8) — a phase-aware invariant, not an
    # unbounded expansion (V-13-1 conversion).
    assert set(_git_names("src/pcae", base=PHASE_1R13_ENTRY, head="HEAD")) <= {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
    }
    # the guarded tests still exist and still name a frozen past-phase SHA
    t10 = (REPO_ROOT / "tests/test_gate5_approval_validation_coordinator_3w1r2b1r1_1r10.py").read_text()
    t11 = (REPO_ROOT / "tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py").read_text()
    assert "test_only_expected_production_files_changed_since_baseline" in t10
    assert "test_production_scope_is_exactly_the_three_planned_files" in t11
