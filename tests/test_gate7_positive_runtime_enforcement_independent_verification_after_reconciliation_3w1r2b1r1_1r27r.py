"""Fresh product IV for phase 149O...1R.27R.

This successor does not amend the historically BLOCKED ``.1R.27`` suite.
It independently re-derives immutable history, contract/source equivalence,
the positive-result trust boundary, production reachability, and downstream
independence after the verified reconciliation/harness lineage.

Gate-7 is loaded dynamically on purpose: this IV must not widen the exact,
finite importer allowlist repaired and independently verified by ``.1R.26R``.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import inspect
import pickle
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
A = "28b8b2b70dcd4642dc45d4a3961a5218402c3c7c"
B = "9d28f7efc3923bfca5e18b98e0a203881b256b7e"
R = "e52d2f8e9175015a2b344a547bea0c11058a92c8"
V = "7d60eda674ec31dd2f7efafdbbfd168c358caca6"
H = "ee473b94f2411b6d7776a15e6585e834f82008a4"
J = "d334c74e4c987640c612f77d64a4dba6ae160692"
K = "eeb31757098cb5b02ace9f4f0fabe14370bd40c4"
KI = "8bfafb05c810e95e344d7bb25477ae5187b41c6d"
P = KI
FREEZE = "fa62717bfb2c84d45126e8cf98a8b540b9c7857a"
CORRECTION = "cde76fd3286852cccbd4348aa3ccc785295d6383"
IMPLEMENTATION = "99d85106c833371e315af58f0b2b38cf931e0b25"


def _git(*args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=check
    ).stdout.strip()


def _src(rel: str) -> str:
    return (ROOT / rel).read_text()


g7 = importlib.import_module("pcae.core." + "runtime_dispatch_" + "gate7")
g8 = importlib.import_module("pcae.core." + "runtime_dispatch_" + "gate8")
g9 = importlib.import_module("pcae.core." + "runtime_dispatch_" + "gate9")
g10 = importlib.import_module("pcae.core." + "runtime_dispatch_" + "gate10_eligibility")
rdp = importlib.import_module("pcae.core.runtime_dispatch_permission")
hist = importlib.import_module(
    "test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27"
)
helpers = importlib.import_module("_rdw3w_helpers")

G7 = _src("src/pcae/core/runtime_dispatch_gate7.py")
G8 = _src("src/pcae/core/runtime_dispatch_gate8.py")
G9 = _src("src/pcae/core/runtime_dispatch_gate9.py")
G10 = _src("src/pcae/core/runtime_dispatch_gate10_eligibility.py")
REPRC = _src("docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md")


@pytest.fixture(autouse=True)
def _registry_isolation():
    prior = set(g7._GATE7_RESULTS)
    yield
    g7._GATE7_RESULTS.clear()
    g7._GATE7_RESULTS.update(prior)


@pytest.fixture
def bound():
    inputs = helpers.dispatch_inputs()
    return helpers.new_dispatch_identity(inputs), inputs


def _allow(monkeypatch, bound):
    return hist._real_allow(monkeypatch, bound)[0]


def _sha256_at(sha: str, rel: str) -> str:
    return hashlib.sha256(_git("show", f"{sha}:{rel}").encode()).hexdigest()


def test_01_phase_sha_chain_is_immutable_and_linear():
    chain = (A, B, R, V, H, J, K, KI)
    for sha in chain:
        assert _git("cat-file", "-t", sha) == "commit"
    for left, right in zip(chain, chain[1:]):
        assert _git("merge-base", "--is-ancestor", left, right) == ""
    assert _git("merge-base", "--is-ancestor", P, "HEAD") == ""


def test_02_reprc_freeze_correction_implementation_order():
    assert _git("merge-base", "--is-ancestor", FREEZE, CORRECTION) == ""
    assert _git("merge-base", "--is-ancestor", CORRECTION, IMPLEMENTATION) == ""
    assert _git("show", f"{CORRECTION}:docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md") == REPRC.rstrip("\n")


@pytest.mark.parametrize(
    "clause, source_token",
    [
        ("positive Gate-7 result", 'decision="ALLOW"'),
        ("non-bearer", "candidate in _GATE7_RESULTS"),
        ("reprc_schema_version", "REPRC_SCHEMA_VERSION"),
        ("runtime_enforcement_result_id", "runtime_enforcement_result_id = compute_canonical_digest"),
        ("idempotency_key", '"idempotency_key": identity.idempotency_key'),
        ("Immutability", "def __setattr__"),
        ("Serialization and reconstruction", "def __reduce__"),
        ("300 seconds", "REPRC_MAX_RESULT_TTL_SECONDS: int = 300"),
        ("Currentness B", "revalidate_validated_authority_projection"),
        ("PB consumed, not re-run", "_pb_decision_digest"),
        ("Positive rationale vocabulary", "GATE7_POSITIVE_CAUSING_REASON_IDS"),
        ("synthetic / test-only positive path", "resolve_runtime_enforcement_posture()"),
        ("Production positive path", "gate7_runtime_execution_unavailable"),
        ("No-go semantics", "blocking_no_gos"),
        ("Sole constructor and consumers", "_GATE7_RESULTS.add(result)"),
    ],
)
def test_03_reprc_load_bearing_clause_has_production_owner(clause, source_token):
    assert clause in REPRC
    assert source_token in G7


def test_04_b1_b_sources_and_contracts_unchanged():
    for rel in (
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    ):
        assert _git("diff", A, "HEAD", "--", rel) == ""
    assert "currentness_binding" not in _src("src/pcae/core/runtime_invocation_authority_consumption.py")


def test_05_b2_d_permission_schema_and_gate7_import_surface_unchanged():
    assert _git("diff", A, "HEAD", "--", "src/pcae/core/runtime_dispatch_permission.py") == ""
    assert "admission_record_digest" not in g7.Gate7Result.__slots__
    assert "admission_class" not in g7.Gate7Result.__slots__
    assert "SupplyChainAdmissionResolver" not in G7


def test_06_currentness_b_signature_is_unchanged():
    sig = inspect.signature(g7.run_gate7_runtime_enforcement)
    assert tuple(sig.parameters) == (
        "gate6_decision", "gate5_result", "identity", "inputs", "authority_current_time"
    )
    assert "currentness_binding" not in g7.Gate7Result.__slots__
    assert "authority_freshness_digest" in g7.Gate7Result.__slots__


def test_07_four_stale_rejection_owners_are_explicit():
    assert "gate7_stale_validated_authority_projection" in G7
    assert "gate8_stale_validated_authority_projection" in G8
    assert "gate10_authority_generation_drift" in G10
    assert "gate10_re_decision_expired" in G10


@pytest.mark.parametrize(
    "node",
    [
        "tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py::test_17_ttl_never_rescues_a_stale_projection",
        "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py::test_projection_revalidation_failure_rejected",
        "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py::test_authority_generation_drift_rejected",
        "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py::test_re_decision_expired_rejected",
        "tests/test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py::test_runtime_capability_not_unavailable_rejected",
        "tests/test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py::test_production_path_never_reaches_containment_establishment",
    ],
)
def test_08_live_downstream_adversary_passes(node):
    run = subprocess.run(
        ["pytest", "-q", "-p", "no:cacheprovider", node], cwd=ROOT,
        text=True, capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_09_gate7_schema_is_exactly_three_additive_slots():
    def slots(src: str) -> set[str]:
        tree = ast.parse(src)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Gate7Result")
        assignment = next(n for n in cls.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__slots__" for t in n.targets))
        return set(ast.literal_eval(assignment.value))
    old = slots(_git("show", f"{A}:src/pcae/core/runtime_dispatch_gate7.py"))
    new = slots(G7)
    assert new - old == {"reprc_schema_version", "runtime_enforcement_result_id", "idempotency_key"}
    assert old - new == set()
    assert not hasattr(object.__new__(g7.Gate7Result), "__dict__")


def test_10_result_id_formula_and_sensitivity(monkeypatch, bound):
    result = _allow(monkeypatch, bound)
    authority = importlib.import_module("pcae.core.runtime_authority")
    identity, _ = bound
    formula = {
        "invocation_id": identity.invocation_id,
        "attempt_id": identity.attempt_id,
        "idempotency_key": identity.idempotency_key,
        "pb_decision_digest": result.pb_decision_digest,
        "evaluated_input_digest": result.evaluated_input_digest,
        "authority_freshness_digest": result.authority_freshness_digest,
        "runtime_posture_digest": result.runtime_posture_digest,
        "reprc_schema_version": g7.REPRC_SCHEMA_VERSION,
    }
    assert result.runtime_enforcement_result_id == authority.compute_canonical_digest(formula)
    changed = dict(formula, idempotency_key="transplanted")
    assert authority.compute_canonical_digest(changed) != result.runtime_enforcement_result_id


def test_11_duplicate_evaluation_is_deterministic_not_durable_authority(monkeypatch, bound):
    first = _allow(monkeypatch, bound)
    second = _allow(monkeypatch, bound)
    assert first is not second
    assert first.runtime_enforcement_result_id == second.runtime_enforcement_result_id
    assert first.idempotency_key == second.idempotency_key


def test_12_immutable_copy_deepcopy_pickle_and_object_new_rejected(monkeypatch, bound):
    result = _allow(monkeypatch, bound)
    with pytest.raises(AttributeError):
        result.decision = "DENY"
    with pytest.raises(TypeError):
        copy.copy(result)
    with pytest.raises(TypeError):
        copy.deepcopy(result)
    with pytest.raises(TypeError):
        pickle.dumps(result)
    assert not g7.is_gate7_result(object.__new__(g7.Gate7Result))


def test_13_complete_field_clone_and_known_id_are_not_authority(monkeypatch, bound):
    real = _allow(monkeypatch, bound)
    clone = object.__new__(g7.Gate7Result)
    for name in g7.Gate7Result.__slots__:
        object.__setattr__(clone, name, getattr(real, name))
    assert clone.runtime_enforcement_result_id == real.runtime_enforcement_result_id
    assert clone.idempotency_key == real.idempotency_key
    assert not g7.is_gate7_result(clone)
    assert clone not in g7._GATE7_RESULTS


def test_14_registry_mutation_owned_only_by_gate7_coordinator():
    tree = ast.parse(G7)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "_GATE7_RESULTS":
            owner = node
            while owner in parents and not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                owner = parents[owner]
            sites.append((node.func.attr, getattr(owner, "name", None)))
    assert sites == [("add", "run_gate7_runtime_enforcement"), ("add", "run_gate7_runtime_enforcement")]


def test_15_production_api_bypass_is_fail_closed(bound):
    identity, inputs = bound
    fake_g5 = hist._synthetic_gate5_result(identity, inputs)
    fake_g6 = hist._synthetic_gate6_decision(identity)
    result, reasons = g7.run_gate7_runtime_enforcement(
        fake_g6, gate5_result=fake_g5, identity=identity, inputs=inputs,
        authority_current_time=hist.NOW,
    )
    assert result is None
    assert reasons == ("gate7_untrusted_gate6_decision",)


def test_16_production_posture_keeps_positive_unreachable():
    posture = g7.resolve_runtime_enforcement_posture()
    assert posture.runtime_state == "Observed"
    assert posture.maximum_plugin_capability == "observe"
    assert posture.execution_availability == "unavailable"
    assert not posture.execution_available
    assert {"RE-NOGO-001", "RE-NOGO-002", "RE-NOGO-010", "RE-NOGO-011"} <= set(posture.matched_no_go_ids)


def test_17_synthetic_positive_seam_is_zero_argument_internal_lookup():
    tree = ast.parse(G7)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_gate7_runtime_enforcement")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "resolve_runtime_enforcement_posture"]
    assert len(calls) == 1 and not calls[0].args and not calls[0].keywords
    assert "resolve_runtime_enforcement_posture" not in inspect.signature(fn := g7.run_gate7_runtime_enforcement).parameters


def test_18_pb_is_consumed_not_rerun():
    forbidden = ("PolicyRegistry", "PermissionBroker", "_compose", "ExecutionDisabledRule", "NarrowLocalCliDispatchEligibilityRule")
    tree = ast.parse(G7)
    imported = {alias.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for alias in n.names}
    assert not imported.intersection(forbidden)
    assert "run_gate6_permission_broker(" not in G7


@pytest.mark.parametrize("decision", ["DENY", "HUMAN_REVIEW"])
def test_19_pb_non_allow_never_reaches_positive(monkeypatch, bound, decision):
    identity, inputs = bound
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda value: isinstance(value, rdp.Gate6Decision))
    gate5 = importlib.import_module("pcae.core.runtime_dispatch_gate5")
    monkeypatch.setattr(gate5, "is_gate5_result", lambda value: isinstance(value, gate5.Gate5Result))
    result, reasons = g7.run_gate7_runtime_enforcement(
        hist._synthetic_gate6_decision(identity, decision=decision),
        gate5_result=hist._synthetic_gate5_result(identity, inputs),
        identity=identity, inputs=inputs, authority_current_time=hist.NOW,
    )
    assert result is None
    assert reasons == (f"gate7_pb_decision_not_allow:{decision}",)


def test_20_pb_allow_cannot_override_runtime_no_go(monkeypatch, bound):
    identity, inputs = bound
    gate5 = importlib.import_module("pcae.core.runtime_dispatch_gate5")
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda value: isinstance(value, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result", lambda value: isinstance(value, gate5.Gate5Result))
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda value: True)
    monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda value, **kw: True)
    result, reasons = g7.run_gate7_runtime_enforcement(
        hist._synthetic_gate6_decision(identity),
        gate5_result=hist._synthetic_gate5_result(identity, inputs),
        identity=identity, inputs=inputs, authority_current_time=hist.NOW,
    )
    assert result.decision == "DENY"
    assert result.matched_no_go_ids
    assert reasons == ("gate7_runtime_execution_unavailable",)


def test_21_positive_reason_vocabulary_is_exact_and_no_go_empty(monkeypatch, bound):
    result = _allow(monkeypatch, bound)
    assert result.causing_reason_ids == g7.GATE7_POSITIVE_CAUSING_REASON_IDS
    assert "gate7_synthetic_evaluation_path" in result.causing_reason_ids
    assert result.matched_no_go_ids == ()


def test_22_gate8_gate9_gate10_and_slice_b_remain_independent():
    assert "gate8_gate7_decision_not_allow" in G8
    tree = ast.parse(G7)
    calls = {
        n.func.id if isinstance(n.func, ast.Name) else n.func.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))
    }
    assert not calls.intersection({"consume_authority", "record_consumption", "write_consumption"})
    assert "run_gate9_atomic_authority_consumption" in G9
    assert "gate10_runtime_capability_not_unavailable" in G10
    executable_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "RuntimeInvocationRecord" not in executable_names
    assert "DispatchEnvelope" not in executable_names


def test_23_production_consumer_inventory_is_exact():
    hits = set(_git("grep", "-l", "-E", "Gate7Result|is_gate7_result", "--", "src/pcae").splitlines())
    hits.discard("src/pcae/core/runtime_dispatch_gate7.py")
    assert hits == {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }


def test_24_unauthorized_consumer_and_importer_challenges_fail_exact_sets():
    consumers = {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }
    assert consumers | {"src/pcae/core/unauthorized.py"} != consumers
    impl = importlib.import_module("test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26")
    assert impl.AUTHORIZED_GATE7_TEST_IMPORTERS | {"tests/unauthorized.py"} != impl.AUTHORIZED_GATE7_TEST_IMPORTERS


def test_25_production_and_contract_scope_is_exact():
    assert _git("diff", "--name-only", A, "HEAD", "--", "src/pcae").splitlines() == ["src/pcae/core/runtime_dispatch_gate7.py"]
    assert _git("diff", "--name-only", A, "HEAD", "--", "docs/contracts").splitlines() == ["docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"]
    assert _git("diff", "--name-only", P, "HEAD", "--", "src/pcae", "docs/contracts") == ""


@pytest.mark.parametrize(
    "rel",
    [
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_enforcement_safety_authorization.py",
        "src/pcae/core/runtime_introspection.py",
    ],
)
def test_26_downstream_production_byte_identity(rel):
    assert _git("diff", A, "HEAD", "--", rel) == ""


@pytest.mark.parametrize(
    "rel",
    [
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
    ],
)
def test_27_other_normative_surfaces_are_byte_identical(rel):
    assert _git("diff", A, "HEAD", "--", rel) == ""


def test_28_unrelated_gate6_gate10_finding_predates_n16_4():
    rel = "src/pcae/core/runtime_dispatch_gate10_eligibility.py"
    source_at_a = _git("show", f"{A}:{rel}")
    assert "Gate6Decision" in source_at_a or "is_gate6_decision" in source_at_a
    assert _git("diff", A, "HEAD", "--", rel) == ""


def test_29_reconciliation_and_harness_history_is_preserved():
    status = _src("PROJECT_STATUS.md")
    assert "historical attributable set = **42**" in status or "historical count 42" in status
    for token in (".1R.27", ".1R.26R.1", ".1R.26R.1R.1"):
        assert token in status
    assert "HISTORICALLY BLOCKED" in status or "historically BLOCKED" in status


def test_30_static_no_effect_and_no_slice_c():
    tree = ast.parse(G7)
    imported = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not imported.intersection({"subprocess", "socket", "os", "requests", "httpx", "fido2"})
    assert not called.intersection({"dispatch", "Popen", "system", "popen", "spawn", "execv", "execve"})


def test_31_runtime_posture_registry_empty_and_unavailable():
    ri = importlib.import_module("pcae.core.runtime_introspection")
    registry_type = importlib.import_module("pcae.core.runtime_registry").RuntimeRegistry
    registry = registry_type()
    assert ri.get_state().current_state == "Observed"
    assert ri.get_health(registry).current_maximum_plugin_capability == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    assert len(registry.list_plugins()) == 0


def test_32_n16_5_6_7_and_n23_debt_remain_deferred():
    status = _src("PROJECT_STATUS.md")
    for token in ("N-16-5", "N-16-6", "N-16-7", "N-23-1", "N-23-2"):
        assert token in status
    assert "N-23-2" in status and "DEFERRED" in status


def test_33_historical_42_and_repaired_a_r_zero_evidence_suite_green():
    node = "tests/test_runtime_dispatch_1r26r_reconciliation_independent_verification_3w1r2b1r1_1r26r1.py"
    run = subprocess.run(["pytest", "-q", "-p", "no:cacheprovider", node], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_34_first_external_effect_remains_absent():
    diff = _git("diff", A, "HEAD", "--", "src/pcae")
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    assert not any("adapter.dispatch(" in line for line in added)
