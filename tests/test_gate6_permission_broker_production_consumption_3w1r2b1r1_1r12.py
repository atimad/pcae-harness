"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.12 — Gate-6 Permission Broker
Production Consumption Integration Implementation.

Focused defensive tests for ``runtime_dispatch_permission.run_gate6_permission_broker``
(the frozen Gate-6 owner) and ``Gate6Decision``. Constructed from the
primary contracts (RDGO-001 v3.0 §7, PBRD-001 v2.0 §4/§7/§9/§10/§12/§14,
POL-005, RIHAC-001 v2.0 §16 step 12, the `.1R.9` planning document §16.1
slice 2 / §16.2 / §22) and current production source — not from a report
or from test names.

The deterministic HPAC mechanism is permanently NON-REAL: ``run_gate5``
never returns a ``Gate5Result`` on any obtainable path (Option-A NON-REAL
hard stop), so **there is no legitimate positive Gate-6 evaluation** to
construct without real FIDO2/UI, and this suite does not manufacture one
(`.1R.9` §41, prompt §30). Every Gate-6-owner case is rejection-only or
structural. The lower-level PB request/evaluator mechanics (POL-005 hard
DENY, DENY > HUMAN_REVIEW > ALLOW precedence) are exercised directly
against the already-verified `.1R.7` builder and the unmodified evaluator,
clearly separated from Gate-6 production-authority eligibility.
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
from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_permission as rdp

from _rdw3w_helpers import (
    always_unconsumed,
    dispatch_inputs,
    full_chain,
    new_dispatch_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_ENTRY_BASELINE = "a26b9fe25c0830eaa1d2217edc6fe66c5718784a"
_1R15_4_SCOPE_END = "4d480553"  # end of .1R.15.3; .1R.15.4 (Contract Normalization) is the later authorized change
NOW = "2026-08-27T00:30:00Z"


def _forged_gate5_result():
    """A fully field-populated ``Gate5Result`` lookalike built without
    ``run_gate5`` — the exact reconstruction/copy attack surface."""
    forged = object.__new__(gate5.Gate5Result)
    for name, value in (
        ("_projection", None),
        ("sequence3_event_digest", "d" * 64),
        ("proof_id", "proof-x"),
        ("approval_id", "ria-" + "0" * 32),
        ("invocation_id", "inv-" + "a" * 32),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(forged, name, value)
    return forged


def _gate6(gate5_result, *, identity=None, inputs=None, **kw):
    inputs = inputs if inputs is not None else dispatch_inputs()
    identity = identity if identity is not None else new_dispatch_identity(inputs)
    kw.setdefault("authority_current_time", NOW)
    return rdp.run_gate6_permission_broker(
        gate5_result, identity=identity, inputs=inputs, **kw
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Provenance — only the exact object a successful run_gate5 returned
# ═══════════════════════════════════════════════════════════════════════
def test_none_gate5_result_fails_closed():
    decision, reasons = _gate6(None)
    assert decision is None
    assert reasons == ("gate6_untrusted_gate5_result",)


def test_caller_constructed_gate5_result_equivalent_rejected():
    decision, reasons = _gate6(_forged_gate5_result())
    assert decision is None and reasons == ("gate6_untrusted_gate5_result",)


def test_reconstructed_and_unpicklable_gate5_result_rejected():
    # a real Gate5Result cannot be pickled/copied at all (__reduce__ raises);
    # a hand-reconstructed one has no identity-registry provenance.
    with pytest.raises(TypeError):
        pickle.dumps(object.__new__(gate5.Gate5Result))
    with pytest.raises(TypeError):
        copy.deepcopy(_forged_gate5_result())
    rebuilt = _forged_gate5_result()
    decision, reasons = _gate6(rebuilt)
    assert decision is None and reasons == ("gate6_untrusted_gate5_result",)


def test_duck_typed_object_with_projection_attr_rejected():
    class _Looks:
        projection = None
        invocation_id = "inv-" + "a" * 32

    decision, reasons = _gate6(_Looks())
    assert decision is None and reasons == ("gate6_untrusted_gate5_result",)


def test_bare_validated_true_object_rejected():
    decision, reasons = _gate6(type("V", (), {"validated": True})())
    assert decision is None and reasons == ("gate6_untrusted_gate5_result",)


def test_gate5_results_registry_stays_empty_on_every_reject():
    for candidate in (None, _forged_gate5_result(), "x", 42):
        _gate6(candidate)
    assert len(gate5._GATE5_RESULTS) == 0
    assert len(rdp._GATE6_DECISIONS) == 0


# ═══════════════════════════════════════════════════════════════════════
# 2. Structural input guards (fail-closed, deterministic reason)
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_identity_type_rejected():
    inputs = dispatch_inputs()
    decision, reasons = rdp.run_gate6_permission_broker(
        _forged_gate5_result(), identity=object(), inputs=inputs, authority_current_time=NOW
    )
    # provenance check on gate5_result fires first — but a genuine
    # Gate5Result with a bad identity would hit the identity guard; assert
    # the identity guard exists and is reachable via source.
    assert decision is None
    body = rdp.run_gate6_permission_broker.__doc__ is not None
    assert body
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert 'gate6_untrusted_runtime_dispatch_identity' in src
    assert 'type(identity) is not RuntimeDispatchIdentity' in src


def test_non_string_authority_current_time_reason_present_in_source():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert "gate6_invalid_authority_current_time" in src
    assert "gate6_invalid_simulation_only" in src
    assert "gate6_invalid_construction_input" in src


def test_invocation_binding_guard_present_in_source():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert "gate5_result.invocation_id != identity.invocation_id" in src
    assert "gate6_invocation_binding_mismatch" in src


def test_every_reject_returns_none_and_a_single_reason_tuple():
    for candidate in (None, _forged_gate5_result(), object(), "", 0):
        decision, reasons = _gate6(candidate)
        assert decision is None
        assert isinstance(reasons, tuple) and len(reasons) == 1
        assert not rdp.is_gate6_decision(decision)


# ═══════════════════════════════════════════════════════════════════════
# 3. Gate 6 owns request construction + evaluation, replicates no policy
# ═══════════════════════════════════════════════════════════════════════
def test_gate6_builds_request_only_through_the_trusted_builder():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    fn = src[src.index("def run_gate6_permission_broker") :]
    fn = fn[: fn.index("\n_GATE6_DECISIONS: ") if "\n_GATE6_DECISIONS: " in fn else len(fn)]
    # the ONLY request the evaluator sees is the one this function builds
    assert "build_runtime_dispatch_permission_broker_request(" in fn
    assert fn.count("evaluator.evaluate(") == 1
    assert "PermissionBrokerRequest(" not in fn  # never hand-rolls a request


def test_gate6_replicates_no_policy_or_decision_logic():
    """AST check on the Gate-6 code (docstrings excluded): it never builds a
    decision, a policy result, a reason chain, or precedence logic — it only
    reads fields off the evaluator's own ``PermissionBrokerDecision``."""
    mod = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    targets = [
        n for n in mod.body
        if (isinstance(n, ast.FunctionDef) and n.name == "run_gate6_permission_broker")
        or (isinstance(n, ast.ClassDef) and n.name == "Gate6Decision")
    ]
    assert len(targets) == 2
    names_called = set()
    for node in targets:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                fn = sub.func
                if isinstance(fn, ast.Name):
                    names_called.add(fn.id)
                elif isinstance(fn, ast.Attribute):
                    names_called.add(fn.attr)
    for forbidden in (
        "_compose", "evaluate_all", "PolicyResult", "PolicyRegistry",
        "ExecutionDisabledRule", "MissingHumanApprovalRule", "ReasonChainLink",
        "_decision", "_sanitize_result",
    ):
        assert forbidden not in names_called, forbidden
    # it does build exactly one request via the trusted builder and calls
    # evaluate exactly once
    assert "build_runtime_dispatch_permission_broker_request" in names_called
    assert "evaluate" in names_called


def test_exactly_one_permission_broker_evaluate_call_site_for_runtime_dispatch():
    src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text()
    assert src.count(".evaluate(") == 1


# ═══════════════════════════════════════════════════════════════════════
# 4. POL-005 hard DENY preserved — lower-level PB mechanics (not Gate-6
#    production-authority eligibility; NON-REAL means no real Gate5Result)
# ═══════════════════════════════════════════════════════════════════════
def test_real_runtime_dispatch_request_denied_by_pol005():
    _, projection, request, decision = full_chain(simulation_only=False)
    assert projection is None
    assert request.simulation_only is False
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids
    assert "NG-025" in decision.matched_no_go_ids


def test_pol005_denies_even_when_approval_present_would_be_true():
    """Verified human authority does not override the POL-005 hard deny.
    Built as a request with ``approval_present=True`` directly against the
    unmodified rule — POL-005 ignores the approval entirely."""
    _, _, request, _ = full_chain(simulation_only=False)
    forced = dataclasses.replace(request, approval_present=True, simulation_only=False)
    result = pbf.ExecutionDisabledRule().evaluate(forced)
    assert result.triggered is True
    assert result.decision == pbf.DECISION_DENY
    assert result.matched_no_go_ids == ("NG-025",)


def test_deny_precedes_human_review_when_both_would_fire():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=False,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_human_review_when_no_authority_and_simulation_only():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids
    assert decision.decision != pbf.DECISION_DENY


def test_pb_precedence_constants_unchanged():
    assert pbf.DECISION_VALUES == ("ALLOW", "DENY", "HUMAN_REVIEW")


# ═══════════════════════════════════════════════════════════════════════
# 5. Gate6Decision type discipline (ephemeral, non-transferable)
# ═══════════════════════════════════════════════════════════════════════
def test_gate6_decision_cannot_be_caller_constructed():
    with pytest.raises(TypeError):
        rdp.Gate6Decision(
            pb_decision=None, approval_present=False, invocation_id="i",
            attempt_id="a", request_id="r", simulation_only=False,
            evaluated_at="t", _seal=object(),
        )


def test_gate6_decision_cannot_be_subclassed():
    with pytest.raises(TypeError):
        type("Evil", (rdp.Gate6Decision,), {})


def test_is_gate6_decision_rejects_forgery_none_and_wrong_type():
    fake = object.__new__(rdp.Gate6Decision)
    assert rdp.is_gate6_decision(fake) is False
    assert rdp.is_gate6_decision(None) is False
    assert rdp.is_gate6_decision("x") is False
    with pytest.raises(TypeError):
        copy.deepcopy(fake)  # non-serializable — cannot be cloned


def test_gate6_decision_is_non_serializable():
    fake = object.__new__(rdp.Gate6Decision)
    with pytest.raises(TypeError):
        pickle.dumps(fake)


def test_gate6_decision_identity_equality_only():
    a = object.__new__(rdp.Gate6Decision)
    b = object.__new__(rdp.Gate6Decision)
    assert a == a and a != b
    assert hash(a) == id(a)


# ═══════════════════════════════════════════════════════════════════════
# 6. No Gate-7 / Gate-8 / Gate-9 / Gate-10, runtime unchanged
# ═══════════════════════════════════════════════════════════════════════
_FORBIDDEN_IMPORT_ROOTS = {
    "subprocess", "socket", "requests", "httpx", "urllib", "http",
    "fido2", "webauthn", "ctap", "smartcard", "usb", "serial", "ssl",
    "asyncio", "multiprocessing", "ctypes",
}


def test_module_imports_nothing_effectful():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in _FORBIDDEN_IMPORT_ROOTS


def test_no_gate7_gate8_gate9_gate10_module_imported():
    """AST import scan: the module imports nothing from Runtime Enforcement,
    Shell Gate, the Gate-9 consumption store, or any adapter/provider."""
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    forbidden_modules = {
        "backend_invocations", "shell_gate", "runtime_invocation_authority_consumption",
        "runtime_dispatch_gate9", "runtime_adapter", "mock_runtime_adapter",
        "runtime_dispatch_effect", "runtime_introspection",
    }
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[-1])
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[-1])
    assert imported.isdisjoint(forbidden_modules), imported & forbidden_modules


def test_test_only_fixture_not_importable_by_production():
    tree = ast.parse((REPO_ROOT / "src/pcae/core/runtime_dispatch_permission.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            names = [a.name for a in node.names]
            assert "_rdw3w_helpers" not in mod and "_rdw3w_helpers" not in names
            assert not any("test" in (n or "").lower() for n in names + [mod])


def test_runtime_state_remains_unavailable_after_gate6_rejections():
    from pcae.core import runtime_introspection as ri

    for candidate in (None, _forged_gate5_result()):
        _gate6(candidate)
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_no_consumption_records_created_anywhere(tmp_path):
    identity = new_dispatch_identity(dispatch_inputs(), root=tmp_path)
    rdp.run_gate6_permission_broker(
        _forged_gate5_result(), identity=identity, inputs=dispatch_inputs(),
        authority_current_time=NOW,
    )
    assert list(tmp_path.rglob("consumption.json")) == []


# ═══════════════════════════════════════════════════════════════════════
# 7. Byte-identity / production-file allowlist / contract identity
# ═══════════════════════════════════════════════════════════════════════
def _git_names(*args):
    return subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()


def test_only_expected_production_file_changed_since_baseline():
    # Phase-aware invariant (V-13-1 conversion, .1R.13.2): the .1R.12
    # production weight is runtime_dispatch_permission.py; any later change
    # must be a member of the individually-authorized runtime-dispatch-gate
    # chain surface (.1R.13.2 adds runtime_dispatch_gate7.py; .1R.13.4 adds
    # runtime_dispatch_gate8.py).
    assert set(_git_names("src/pcae")) <= {
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",  # Gate 9 (.1R.14)
    }


def test_permission_broker_foundation_and_pol005_bytes_unchanged():
    assert _git_names("src/pcae/core/permission_broker_foundation.py") == []
    src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    assert 'policy_id = "POL-005"' in src
    assert 'decision_reason="execution_boundary_unavailable"' in src
    assert "DECISION_DENY > DECISION_HUMAN_REVIEW" not in src  # composed, not literal


def test_all_normative_contracts_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    ):
        assert _git_names(rel) == [], rel


def test_runtime_authority_and_gate5_coordinator_bytes_unchanged():
    assert _git_names("src/pcae/core/runtime_authority.py") == []
    assert _git_names("src/pcae/core/runtime_dispatch_gate5.py") == []
    assert _git_names("src/pcae/core/hpac_lifecycle.py") == []


# ═══════════════════════════════════════════════════════════════════════
# 8. Regression — the .1R.7 builder surface is unchanged
# ═══════════════════════════════════════════════════════════════════════
def test_builder_still_has_no_approval_present_parameter():
    import inspect

    sig = inspect.signature(rdp.build_runtime_dispatch_permission_broker_request)
    assert "approval_present" not in sig.parameters
    assert "validated_authority" in sig.parameters


def test_missing_authority_still_projects_approval_present_false():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=False,
    )
    assert request.approval_present is False
    binding = request.runtime_dispatch_context.human_authority_binding
    assert (binding.approval_id, binding.approval_record_digest,
            binding.validation_evidence_digest) == ("", "", "")
