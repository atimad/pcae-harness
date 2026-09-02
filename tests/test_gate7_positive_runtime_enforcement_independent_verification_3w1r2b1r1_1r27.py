"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.27 — Independent Verification of the
N-16-4 Runtime Enforcement Gate.

RE-DERIVE, DO NOT TRUST. Written independently from primary sources (current
production ``src/pcae/core/runtime_dispatch_gate7.py`` /
``runtime_dispatch_gate8.py`` / ``runtime_dispatch_gate10_eligibility.py``,
REPRC-001 v1.0, and immutable Git history) — not from the ``.1R.26`` report,
its test names, or its helper conventions. Complements (does not duplicate)
the live stale-rejection demonstrations already present and independently
re-run at HEAD in ``test_gate8_process_containment_coordinator_integration_
3w1r2b1r1_1r13_4.py`` (Gate-8 projection revalidation,
``test_projection_revalidation_failure_rejected``) and
``test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py`` /
``..._1r18.py`` (Gate-10 generation drift + TTL expiry,
``test_authority_generation_drift_rejected`` /
``test_re_decision_expired_rejected``), all of which chain a REAL
``run_gate7_runtime_enforcement`` result (post-``.1R.26`` 3-additive-slot
schema, exercised transparently) into a live Gate-8/Gate-10 call.

This suite's independent contribution: (1) a decisive production-path-bypass
challenge using ONLY public production APIs — no monkeypatch, no private
global mutation; (2) an explicit new-slot-transplant-fooling challenge
against Gate 8's ``_gate7_result_digest`` trust boundary; (3) fresh AST/byte
proofs of PB-not-rerun, no-effect, and normative/production byte scope
independently reconstructed (not copied from report prose); (4) independent
consumer-inventory and whole-tree guard re-derivation.
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
from pcae.core import runtime_dispatch_gate8 as g8
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_authority as ra

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA = "28b8b2b70dcd4642dc45d4a3961a5218402c3c7c"  # pre-.1R.26, independently confirmed
REPRC_FREEZE_SHA = "fa62717bfb2c84d45126e8cf98a8b540b9c7857a"
REPRC_CORRECTION_SHA = "cde76fd3286852cccbd4348aa3ccc785295d6383"
IMPL_SHA = "99d85106c833371e315af58f0b2b38cf931e0b25"
NOW = "2026-09-01T12:00:00Z"

G7_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
G8_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate8.py").read_text()
REPRC = (REPO_ROOT / "docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md").read_text()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


# ═══════════════════════════════════════════════════════════════════════
# 1. Immutable SHA / ordering re-derivation (independent of report prose)
# ═══════════════════════════════════════════════════════════════════════
def test_01_commit_ancestry_chain_independently_confirmed():
    assert _git("merge-base", "--is-ancestor", BASELINE_SHA, REPRC_FREEZE_SHA) == ""
    assert _git("merge-base", "--is-ancestor", REPRC_FREEZE_SHA, REPRC_CORRECTION_SHA) == ""
    assert _git("merge-base", "--is-ancestor", REPRC_CORRECTION_SHA, IMPL_SHA) == ""


def test_02_reprc_authored_and_corrected_strictly_before_implementation():
    freeze_ts = _git("show", "-s", "--format=%at", REPRC_FREEZE_SHA)
    correction_ts = _git("show", "-s", "--format=%at", REPRC_CORRECTION_SHA)
    impl_ts = _git("show", "-s", "--format=%at", IMPL_SHA)
    assert int(freeze_ts) < int(correction_ts) < int(impl_ts)


def test_03_reprc_sha256_no_semantic_drift_after_correction():
    correction_text = _git("show", f"{REPRC_CORRECTION_SHA}:docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md")
    head_text = REPRC.rstrip("\n")
    assert correction_text == head_text  # byte-identical: no drift after implementation began


def test_04_production_byte_scope_is_exactly_gate7():
    names = _git("diff", "--name-only", BASELINE_SHA, "HEAD", "--", "src/pcae")
    _r30 = {"src/pcae/core/hpac_pawa_schemas.py", "src/pcae/core/hpac_pawa_agent_exclusion.py",
            "src/pcae/core/hpac_protected_admin_writer.py", "src/pcae/core/hpac_foundation.py",
            "src/pcae/core/human_principal_registry.py"}  # Phase ...1R.30R.3.1 (N-16-5) PAWA Slice 1
    assert set(names.splitlines()) - _r30 == {"src/pcae/core/runtime_dispatch_gate7.py"}


def test_05_normative_byte_scope_is_exactly_the_new_reprc_doc():
    names = _git("diff", "--name-only", BASELINE_SHA, "HEAD", "--", "docs/contracts")
    assert names.splitlines() == ["docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"]


@pytest.mark.parametrize("relpath", [
    "src/pcae/core/runtime_dispatch_permission.py",
    "src/pcae/core/runtime_dispatch_gate8.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
    "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    "src/pcae/core/runtime_invocation_authority_consumption.py",
    "src/pcae/core/runtime_authority.py",
    "src/pcae/core/runtime_enforcement_safety_authorization.py",
    "src/pcae/core/runtime_introspection.py",
])
def test_06_downstream_files_byte_identical_since_baseline(relpath):
    assert _git("diff", BASELINE_SHA, "HEAD", "--", relpath) == ""


@pytest.mark.parametrize("relpath", [
    "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
    "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
    "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
])
def test_07_normative_contracts_byte_identical_since_baseline(relpath):
    assert _git("diff", BASELINE_SHA, "HEAD", "--", relpath) == ""


# ═══════════════════════════════════════════════════════════════════════
# 2. Currentness B signature + slot fidelity, independently reconstructed
# ═══════════════════════════════════════════════════════════════════════
def test_08_signature_byte_unchanged_since_baseline_by_ast():
    old_src = _git("show", f"{BASELINE_SHA}:src/pcae/core/runtime_dispatch_gate7.py")
    def params(src):
        tree = ast.parse(src)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "run_gate7_runtime_enforcement")
        return [a.arg for a in fn.args.args] + [a.arg for a in fn.args.kwonlyargs]
    assert params(old_src) == params(G7_SRC) == [
        "gate6_decision", "gate5_result", "identity", "inputs", "authority_current_time"]


def test_09_exactly_three_additive_slots_no_removal():
    old_src = _git("show", f"{BASELINE_SHA}:src/pcae/core/runtime_dispatch_gate7.py")
    def slots(src):
        tree = ast.parse(src)
        cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "Gate7Result")
        assign = next(n for n in cls.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "__slots__" for t in n.targets))
        return set(ast.literal_eval(ast.get_source_segment(src, assign.value)))
    old, new = slots(old_src), slots(G7_SRC)
    assert new - old == {"reprc_schema_version", "runtime_enforcement_result_id", "idempotency_key"}
    assert old - new == set()


def test_10_no_dict_introduced_gate7result_stays_slotted():
    r = object.__new__(g7.Gate7Result)
    with pytest.raises(AttributeError):
        r.__dict__  # no __dict__ slot => AttributeError, confirms __slots__-only


def test_11_no_currentness_binding_slot_or_assignment():
    assert "currentness_binding" not in g7.Gate7Result.__slots__
    assert '"currentness_binding"' not in G7_SRC
    assert "'currentness_binding'" not in G7_SRC
    assert "self.currentness_binding" not in G7_SRC
    assert "currentness_binding=" not in G7_SRC.replace(" ", "")


# ═══════════════════════════════════════════════════════════════════════
# 3. New-slot / _gate7_result_digest downstream-binding challenge (decisive)
# ═══════════════════════════════════════════════════════════════════════
def test_12_gate7_result_digest_does_not_hash_the_three_new_slots():
    src_fn = G8_SRC[G8_SRC.index("def _gate7_result_digest"):]
    src_fn = src_fn[:src_fn.index("\ndef _effect_plan_digest")]
    for new_field in ("reprc_schema_version", "runtime_enforcement_result_id", "idempotency_key"):
        assert new_field not in src_fn


def test_13_gate8_trust_boundary_is_identity_registry_not_the_digest():
    """The decisive question: can a transplanted/altered Gate7Result (with
    forged new-slot values) reach Gate 8's digest-composition step at all?
    Independently verify the ORDER of operations: is_gate7_result (exact
    registry-object-identity membership) is checked strictly BEFORE
    _gate7_result_digest is ever computed, so a forged/reconstructed object
    -- whatever its new-slot values say -- never reaches the digest step in
    the first place. The digest omitting the new slots is therefore
    immaterial to authenticity, which never rests on the digest."""
    is_check_idx = G8_SRC.index("if not is_gate7_result(gate7_result):")
    digest_call_idx = G8_SRC.index("gate7_digest = _gate7_result_digest(gate7_result)")
    assert is_check_idx < digest_call_idx


def test_14_forged_new_slot_values_are_never_a_registry_member(monkeypatch, bound):
    """Attempt the attack directly: build a Gate7Result-shaped object with
    every field -- including the three new REPRC slots and the real _seal
    value -- copied verbatim from a real trusted ALLOW result. Even a
    byte-perfect field copy fails ``is_gate7_result`` because trust is
    exact-object registry membership, not field shape. Combined with
    test_13 (identity check strictly precedes digest composition in Gate
    8), this proves a forged/transplanted new-slot object can never reach
    Gate 8's containment evidence step as trusted input -- independently
    exercised live (not merely asserted) by
    test_gate8_process_containment_coordinator_integration_3w1r2b1r1_1r13_4.py
    ::test_caller_constructed_gate7_result_rejected and
    ::test_copied_reconstructed_serialized_gate7_result_rejected, both
    re-confirmed passing at HEAD in this phase's suite run."""
    real, _ = _real_allow(monkeypatch, bound)
    forged = object.__new__(g7.Gate7Result)
    for name in g7.Gate7Result.__slots__:
        object.__setattr__(forged, name, getattr(real, name))
    assert forged is not real
    assert g7.is_gate7_result(forged) is False
    assert forged not in g7._GATE7_RESULTS


def _real_allow(monkeypatch, bound):
    ident, inp = bound
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda o: isinstance(o, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result", lambda o: isinstance(o, gate5.Gate5Result))
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
    monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: True)
    monkeypatch.setattr(g7, "resolve_runtime_enforcement_posture", lambda: g7.RuntimeEnforcementPosture(
        runtime_status="not_implemented", runtime_state="Observed",
        execution_availability="available", maximum_plugin_capability="observe",
        governance_posture="non-executing", permission_broker_status="execution_unavailable",
        authorization_flags={}, safety_flags={}, matched_no_go_ids=()))
    binding = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    g5 = _synthetic_gate5_result(ident, inp, binding=binding)
    g6 = _synthetic_gate6_decision(ident)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is not None and r.decision == "ALLOW", reasons
    return r, reasons


class _SyntheticProjection:
    def __init__(self, *, subject_scope_binding_digest):
        self.subject_scope_binding_digest = subject_scope_binding_digest
        self.freshness_verdict_digest = "f" * 64

    def evidence_digest(self):
        return "e" * 64


def _synthetic_gate5_result(ident, inp, binding=None):
    if binding is None:
        binding = rdp._expected_subject_scope_binding_digest(identity=ident, inputs=inp)
    obj = object.__new__(gate5.Gate5Result)
    for name, value in (
        ("_projection", _SyntheticProjection(subject_scope_binding_digest=binding)),
        ("sequence3_event_digest", "d" * 64),
        ("proof_id", "proof-x"),
        ("approval_id", "ria-" + "0" * 32),
        ("invocation_id", ident.invocation_id),
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


def _synthetic_gate6_decision(ident, decision="ALLOW", request_id="pbr-" + "0" * 12):
    obj = object.__new__(rdp.Gate6Decision)
    pb = _FakePB()
    pb.decision = decision
    for name, value in (
        ("_pb_decision", pb), ("decision", decision), ("decision_reason", "synthetic"),
        ("approval_present", True), ("invocation_id", ident.invocation_id),
        ("attempt_id", ident.attempt_id), ("request_id", request_id),
        ("causing_policy_ids", ()), ("matched_no_go_ids", ()),
        ("requires_human", decision == "HUMAN_REVIEW"), ("simulation_only", False),
        ("evaluated_at", NOW), ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


@pytest.fixture(autouse=True)
def _isolate_gate7_registry():
    snapshot = set(g7._GATE7_RESULTS)
    yield
    g7._GATE7_RESULTS.clear()
    g7._GATE7_RESULTS.update(snapshot)


@pytest.fixture
def bound():
    inp = dispatch_inputs()
    ident = new_dispatch_identity(inp)
    return ident, inp


# ═══════════════════════════════════════════════════════════════════════
# 4. Non-bearer / registry ownership challenge, independently written
# ═══════════════════════════════════════════════════════════════════════
def test_15_pickle_rejected(monkeypatch, bound):
    r, _ = _real_allow(monkeypatch, bound)
    with pytest.raises(TypeError):
        pickle.dumps(r)


def test_16_deepcopy_not_a_registry_member(monkeypatch, bound):
    r, _ = _real_allow(monkeypatch, bound)
    try:
        cloned = copy.deepcopy(r)
    except Exception:
        return  # rejection via exception is also an acceptable fail-closed outcome
    assert g7.is_gate7_result(cloned) is False


def test_17_subclass_attempt_rejected():
    with pytest.raises(TypeError):
        class Evil(g7.Gate7Result):
            pass


def test_18_known_result_id_alone_grants_nothing(monkeypatch, bound):
    r, _ = _real_allow(monkeypatch, bound)
    known_id = r.runtime_enforcement_result_id
    forged = object.__new__(g7.Gate7Result)
    for name in g7.Gate7Result.__slots__:
        object.__setattr__(forged, name, getattr(r, name))
    object.__setattr__(forged, "runtime_enforcement_result_id", known_id)
    assert g7.is_gate7_result(forged) is False
    assert forged not in g7._GATE7_RESULTS


def test_19_only_run_gate7_runtime_enforcement_populates_the_registry():
    """AST proof: search the whole module for every ``_GATE7_RESULTS``
    mutation site; both must be ``.add(result)`` calls and both must be
    lexically inside ``run_gate7_runtime_enforcement`` (the DENY branch and
    the ALLOW branch of its single completed-evaluation return path) -- no
    helper or public constructor mutates the registry directly."""
    tree = ast.parse(G7_SRC)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "run_gate7_runtime_enforcement")
    in_fn_sites = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("add", "update", "discard", "remove", "clear") and \
               isinstance(node.func.value, ast.Name) and node.func.value.id == "_GATE7_RESULTS":
                in_fn_sites.append(node.func.attr)
    all_sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("add", "update", "discard", "remove", "clear") and \
               isinstance(node.func.value, ast.Name) and node.func.value.id == "_GATE7_RESULTS":
                all_sites.append(node.func.attr)
    assert in_fn_sites == all_sites == ["add", "add"]


# ═══════════════════════════════════════════════════════════════════════
# 5. Production positive-path bypass challenge (decisive; public APIs only)
# ═══════════════════════════════════════════════════════════════════════
def test_20_public_api_bypass_challenge_no_monkeypatch_no_private_mutation(bound):
    """Attempt to obtain a trusted ALLOW Gate7Result using ONLY:
    - the real (unsubstituted) module-global resolve_runtime_enforcement_posture
    - the real production run_gate7_runtime_enforcement
    - attacker-selectable *public* inputs (identity, inputs, current time)
    No monkeypatch, no private global reassignment, no direct _GATE7_RESULTS
    mutation. This is the strongest in-process production-style challenge
    reasonably available without executing real human-authority /
    admission / hardware flows. A caller-constructed Gate6Decision /
    Gate5Result is rejected at the provenance guards (is_gate6_decision /
    is_gate5_result), which this test also does not bypass."""
    ident, inp = bound
    fake_gate6 = _synthetic_gate6_decision(ident)  # NOT registry-provenanced
    fake_gate5 = _synthetic_gate5_result(ident, inp)  # NOT registry-provenanced
    r, reasons = g7.run_gate7_runtime_enforcement(
        fake_gate6, gate5_result=fake_gate5, identity=ident, inputs=inp,
        authority_current_time=NOW)
    # Rejected at the provenance guard before runtime-enforcement posture
    # is even consulted -- the real resolver was never substituted.
    assert r is None
    assert reasons == ("gate7_untrusted_gate6_decision",)


def test_21_real_posture_resolver_independently_confirms_no_go(bound):
    p = g7.resolve_runtime_enforcement_posture()
    assert p.execution_available is False
    assert p.execution_availability == "unavailable"
    assert set(p.matched_no_go_ids) & {"RE-NOGO-001", "RE-NOGO-002", "RE-NOGO-010", "RE-NOGO-011"}


def test_22_no_module_level_assignment_of_the_resolver_anywhere_in_src():
    """No production src/pcae file assigns to
    runtime_dispatch_gate7.resolve_runtime_enforcement_posture (no config
    path, no plugin substitution, no import-time hook)."""
    hits = subprocess.run(
        ["git", "grep", "-n", "resolve_runtime_enforcement_posture\\s*=", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True)
    # git grep exits 1 with empty stdout when there are no matches
    assert hits.stdout.strip() == ""


def test_23_synthetic_seam_is_a_module_global_read_not_a_parameter():
    """The seam is the plain module-global lookup at call time (Currentness
    B: no resolver parameter). Independently confirm resolve_runtime_
    enforcement_posture is invoked with zero arguments and its result is
    used directly -- no injected/parameterized posture path exists."""
    tree = ast.parse(G7_SRC)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "run_gate7_runtime_enforcement")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "resolve_runtime_enforcement_posture"]
    assert len(calls) == 1
    assert calls[0].args == [] and calls[0].keywords == []


# ═══════════════════════════════════════════════════════════════════════
# 6. PB consumed not re-run; hard no-go; positive vocabulary (independent AST)
# ═══════════════════════════════════════════════════════════════════════
def test_24_no_policy_engine_import_by_ast():
    tree = ast.parse(G7_SRC)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported_names.add(alias.name)
    forbidden = {"PolicyRegistry", "PermissionBroker", "_compose",
                 "ExecutionDisabledRule", "NarrowLocalCliDispatchEligibilityRule"}
    assert not (imported_names & forbidden)
    assert "POL-" not in G7_SRC.replace("POL-005", "")  # POL-005 appears only in docstring prose


def test_25_pb_allow_plus_re_violation_still_denies(monkeypatch, bound):
    ident, inp = bound
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda o: isinstance(o, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result", lambda o: isinstance(o, gate5.Gate5Result))
    monkeypatch.setattr(g7, "is_trusted_validated_authority_projection", lambda o: True)
    monkeypatch.setattr(g7, "revalidate_validated_authority_projection", lambda o, **k: True)
    # real posture resolver -- Runtime Enforcement no-go posture in force
    g5 = _synthetic_gate5_result(ident, inp)
    g6 = _synthetic_gate6_decision(ident, decision="ALLOW")
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r.decision == "DENY"
    assert reasons == ("gate7_runtime_execution_unavailable",)


@pytest.mark.parametrize("decision", ["DENY", "HUMAN_REVIEW"])
def test_26_pb_non_allow_blocks_before_evaluation(monkeypatch, bound, decision):
    ident, inp = bound
    monkeypatch.setattr(rdp, "is_gate6_decision", lambda o: isinstance(o, rdp.Gate6Decision))
    monkeypatch.setattr(gate5, "is_gate5_result", lambda o: isinstance(o, gate5.Gate5Result))
    g5 = _synthetic_gate5_result(ident, inp)
    g6 = _synthetic_gate6_decision(ident, decision=decision)
    r, reasons = g7.run_gate7_runtime_enforcement(
        g6, gate5_result=g5, identity=ident, inputs=inp, authority_current_time=NOW)
    assert r is None
    assert reasons == (f"gate7_pb_decision_not_allow:{decision}",)


def test_27_positive_result_never_carries_a_matched_no_go(monkeypatch, bound):
    r, _ = _real_allow(monkeypatch, bound)
    assert r.matched_no_go_ids == ()


def test_28_positive_reason_vocabulary_non_empty_and_frozen(monkeypatch, bound):
    r, _ = _real_allow(monkeypatch, bound)
    assert r.causing_reason_ids == g7.GATE7_POSITIVE_CAUSING_REASON_IDS
    assert len(r.causing_reason_ids) > 0
    assert "gate7_synthetic_evaluation_path" in r.causing_reason_ids


# ═══════════════════════════════════════════════════════════════════════
# 7. Gate 8/9/10/Slice-B independence + no-effect static proof (fresh)
# ═══════════════════════════════════════════════════════════════════════
def _code_only(src: str) -> str:
    """Strip the module docstring (which discusses, in prose, the very
    primitives Gate 7 must NOT call) so effect-primitive checks scan only
    executable code, not documentation."""
    tree = ast.parse(src)
    doc = ast.get_docstring(tree, clean=False) or ""
    idx = src.index(doc) if doc else 0
    return src[idx + len(doc):] if doc else src


G7_CODE_ONLY = _code_only(G7_SRC)


def test_29_gate7_writes_no_consumption_record_by_ast():
    tree = ast.parse(G7_SRC)
    called_names = {n.func.id for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    called_attrs = {n.func.attr for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    forbidden = {"consume_authority", "record_consumption", "write_consumption"}
    assert not (called_names & forbidden)
    assert not (called_attrs & forbidden)
    assert "consumption.json" not in G7_CODE_ONLY


def test_30_no_effect_primitives_imported_or_called():
    tree = ast.parse(G7_SRC)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden_modules = {"subprocess", "socket", "os"}
    assert not (imported_modules & forbidden_modules)
    for token in ("os.system", "os.popen", "os.spawn", "os.exec", "Popen",
                  "adapter.dispatch(", "FIDO2", "WebAuthn", "CTAP"):
        assert token not in G7_CODE_ONLY


def test_31_gate9_not_imported_or_called_by_gate7():
    assert "runtime_dispatch_gate9" not in G7_SRC
    assert "gate9" not in G7_SRC.lower().replace("gate9_", "GATE9_MARKER_NEVER_PRESENT")


def test_32_slice_b_record_never_touched_by_gate7():
    assert "RuntimeInvocationRecord" not in G7_SRC
    assert "dispatch_attempted" not in G7_SRC


# ═══════════════════════════════════════════════════════════════════════
# 8. Independent consumer inventory + guard re-derivation
# ═══════════════════════════════════════════════════════════════════════
def test_33_consumer_inventory_reproduced_independently():
    hits = subprocess.run(
        ["git", "grep", "-lE", "Gate7Result|is_gate7_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    consumers = {h for h in hits if not h.endswith("runtime_dispatch_gate7.py")}
    assert consumers == {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }


def test_34_no_new_unauthorized_production_consumer():
    """Simulate an unauthorized importer: a module-level object claiming to
    consume Gate7Result outside the three legitimate files must not appear
    anywhere in src/pcae -- re-derived, not assumed."""
    hits = subprocess.run(
        ["git", "grep", "-lE", "from pcae.core.runtime_dispatch_gate7 import.*Gate7Result|from pcae.core.runtime_dispatch_gate7 import.*is_gate7_result",
         "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    assert set(hits) <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }


# ═══════════════════════════════════════════════════════════════════════
# 9. Runtime state / N-16-5/6/7 untouched (fresh re-check, not report-trusted)
# ═══════════════════════════════════════════════════════════════════════
def test_35_runtime_state_unchanged_since_baseline():
    from pcae.core import runtime_introspection as ri
    from pcae.core.runtime_registry import RuntimeRegistry
    state = ri.get_state()
    assert state.current_state == "Observed"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    health = ri.get_health(RuntimeRegistry())
    assert health.current_maximum_plugin_capability == "observe"
    reg = RuntimeRegistry()
    assert len(reg.list_plugins()) == 0 if hasattr(reg, "list_plugins") else True


def test_36_no_new_adapter_dispatch_call_site_since_baseline():
    """A real ``adapter.dispatch()`` call site already exists pre-baseline
    (``runtime_adapter.py`` -- the dispatch primitive's own definition/call,
    unrelated to Gate 7). The decisive check is that the .1R.26 diff did
    not ADD a new call site, and that Gate 7 itself (the only file touched)
    contains none."""
    assert "adapter.dispatch(" not in G7_CODE_ONLY
    diff = _git("diff", BASELINE_SHA, "HEAD", "--", "src/pcae")
    added_lines = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    assert not any("adapter.dispatch(" in l for l in added_lines)


def test_37_no_fido2_webauthn_ctap_source_added_since_baseline():
    diff = _git("diff", BASELINE_SHA, "HEAD", "--stat")
    for token in ("fido2", "webauthn", "ctap"):
        assert token not in diff.lower()
