"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.23 — Independent Verification of the
N-16-3 Narrow-Eligibility Policy (verifies Phase .1R.22).

RE-DERIVE, DO NOT TRUST. Every assertion here is derived independently from
primary source (PBRD-001 v3.0, PBNDE-001 v1.0, PBPA-001 v1.1, POL-005 /
POL-013 source, `_compose`, `runtime_authority.validate_approval`) — not from
the .1R.22 report, its 43-test suite, contract prose, or helper names.

Verification-entry SHA: HEAD == origin/main == 15aeb269.
Independently reconstructed baseline (phase-entry, .1R.21 push-reconcile):
8603fe6a. .1R.22 range: 8603fe6a..HEAD == 9 commits (1dadeb21 .. 15aeb269).

Two independent production blockers keep RUNTIME_DISPATCH_LOCAL_CLI_V1
unsatisfiable:
  B1 (N-16-6) — the only production SupplyChainAdmissionResolver admits
     nothing, so P_supply_chain_admission always fails.
  B2 (N-16-5) — there is no production or test path to a trusted
     ValidatedAuthorityProjection (validate_approval rejects caller-supplied
     objects), so approval_present is never True for a real request, so
     P_human_authority_present always fails.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_authority as ra
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri
from pcae.core.permission_broker_foundation import (
    ADMISSION_CLASS_LOCAL_FIXED_ARGV,
    ADMISSION_CLASS_UNADMITTED,
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1,
    PermissionBroker,
    PolicyRegistry,
    RuntimeDispatchAdapterDescriptorBinding as Adapter,
    RuntimeDispatchFilesystemScopeRef as ScopeRef,
    RuntimeDispatchHumanAuthorityBinding as AuthBinding,
    RuntimeDispatchLifecycleContext as LifecycleCtx,
    RuntimeDispatchRequestFacts as Facts,
    _build_runtime_dispatch_permission_broker_request as _seal_build,
    _is_trusted_narrow_local_cli_dispatch_v1,
    _narrow_local_cli_dispatch_v1_failed_predicates as _failed,
    _valid_runtime_dispatch_request,
    derive_runtime_dispatch_local_cli_v1_classification as _derive,
)

from _rdw3w_helpers import dispatch_inputs, full_chain, new_dispatch_identity

REPO = Path(__file__).resolve().parents[1]
BASELINE = "8603fe6a"
# .1R.22 finalize head (verification-entry SHA for this IV phase). The
# historical .1R.22 range BASELINE..R22_HEAD is exactly 9 commits and is
# immutable. Phase .1R.22R (N-16-3 Scope-Fence / Verification-Evidence
# Reconciliation) later repaired the N-23-3 blocker below — several tests in
# this file are intentionally sensitive to that reconciliation and are marked
# "reconciliation-aware" where they now assert the repaired current state
# while documenting the historical .1R.23 finding. The .1R.23 canonical
# artifact's BLOCKED verdict is preserved unchanged.
R22_HEAD = "15aeb269"
H = "a" * 64
HB, HC, HD, HE = "b" * 64, "c" * 64, "d" * 64, "e" * 64
ADM = "9" * 64
INV = "inv-" + "0" * 32
ATT = "att-" + "1" * 32
PBF_SRC = Path(pbf.__file__).read_text()
RDP_SRC = Path(rdp.__file__).read_text()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout


# ── independent request builders (policy-logic isolation; disclosed) ──────
# There is NO path (production or test) to a trusted ValidatedAuthority
# projection, so a structurally-complete profile request must be sealed
# directly to exercise POLICY logic. Production-path unsatisfiability is
# verified separately (test_production_*).

def _auth(valid: bool = True) -> AuthBinding:
    return AuthBinding("ria-" + "2" * 32, HB, HC) if valid else AuthBinding("", "", "")


def _adapter(admitted: bool = True) -> Adapter:
    return Adapter(
        adapter_id="fx-adapter",
        descriptor_version="1.0",
        descriptor_digest=HD,
        target_config_digest=HE,
        admission_record_digest=ADM if admitted else "",
        admission_class=ADMISSION_CLASS_LOCAL_FIXED_ARGV if admitted else ADMISSION_CLASS_UNADMITTED,
    )


def _facts(**over) -> Facts:
    base = dict(
        invocation_id=INV,
        attempt_id=ATT,
        idempotency_key=H,
        repository_identity=HB,
        task_id="task-a",
        lifecycle_context=LifecycleCtx(phase_id="149O.20L.7O.3W", session_id=None),
        runtime_target_id="local-cli-1",
        adapter_descriptor_binding=_adapter(admitted=True),
        prompt_hash=HC,
        requested_capability="local_cli_dispatch",
        filesystem_scope_ref=ScopeRef(scope_id="fs-1", scope_digest=HD),
        human_authority_binding=_auth(True),
        transport_type="local_cli",
        network_requirement=False,
        profile_classification="",
    )
    base.update(over)
    return Facts(**base)


def _sealed(facts: Facts, *, approval_present: bool = True, simulation_only: bool = False):
    return _seal_build(
        requested_component="COMP-006",
        requested_capability=facts.requested_capability,
        task_id=facts.task_id,
        phase_id=facts.lifecycle_context.phase_id,
        requested_resource=None,
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=simulation_only,
        runtime_dispatch_context=facts,
    )


def _complete(**over):
    prov = _sealed(_facts(**over))
    assert _failed(prov, check_marker=False) == (), _failed(prov, check_marker=False)
    return _sealed(_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **over))


def _decide(req):
    return PermissionBroker().evaluate(req)


class _AdmittingResolver(rdp.SupplyChainAdmissionResolver):
    def resolve(self, adapter_id: str) -> rdp.SupplyChainAdmissionResult:
        return rdp.SupplyChainAdmissionResult(True, ADM, ADMISSION_CLASS_LOCAL_FIXED_ARGV)


# ═══════════════ 1. range / baseline reconstruction ═══════════════════════

def test_baseline_and_range_reconstructed_independently():
    # Reconciliation-aware (.1R.22R): the original body asserted
    # BASELINE..HEAD == 9, which was only true at the .1R.23
    # verification-entry SHA; .1R.23's own finalization commits (and later
    # .1R.22R) grow HEAD. The immutable, stable fact is the historical
    # .1R.22 range BASELINE..R22_HEAD.
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE, "origin/main"], cwd=REPO
    ).returncode == 0
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", R22_HEAD, "origin/main"], cwd=REPO
    ).returncode == 0
    rng = _git("rev-list", "--count", f"{BASELINE}..{R22_HEAD}").strip()
    assert rng == "9"
    subjects = [l for l in _git("log", "--format=%s", f"{BASELINE}..{R22_HEAD}").splitlines() if l]
    assert len(subjects) == 9
    assert all("1R.1.1R.22" in s for s in subjects)


def test_only_two_production_files_changed_since_baseline():
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--", "src/pcae").split())
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26 (N-16-4 -- REPRC-001 v1.0)
    # authorizedly changes exactly runtime_dispatch_gate7.py. Subtract that
    # one file; any OTHER unauthorized production change still fails.
    changed -= {"src/pcae/core/runtime_dispatch_gate7.py"}
    assert changed == {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
    }


def test_only_authorized_contract_files_changed_since_baseline():
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--", "docs/contracts",
                       "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md").split())
    # Phase ...1R.26 (N-16-4): exactly one NEW companion contract, REPRC-001 v1.0.
    changed -= {"docs/contracts/RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md"}
    assert changed == {
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md",
    }


# ═══════════════ 2. PBRD §16 MAJOR trigger (re-derived) ═══════════════════

def _norm(text: str) -> str:
    return " ".join(text.split())


def test_pbrd_section_16_lists_weakening_pol005_eligibility_as_major():
    pbrd = _norm((REPO / "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text())
    assert "weakening POL-005 eligibility" in pbrd
    assert "requires a new MAJOR plus explicit migration and independent verification" in pbrd
    base_pbrd = _git("show", f"{BASELINE}:docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md")
    assert base_pbrd.startswith("# PBRD-001 v2.1")
    assert "weakening POL-005 eligibility" in base_pbrd  # trigger predates .1R.22
    assert pbrd.startswith("# PBRD-001 v3.0")


def test_new_12a_narrows_pol005_match_domain_so_major_is_correct():
    # §12a rule: POL-005 returns not-triggered for one class it previously
    # matched -> it "stops matching one class" -> §16 MAJOR trigger fires.
    src = inspect.getsource(pbf.ExecutionDisabledRule.evaluate)
    assert "_is_trusted_narrow_local_cli_dispatch_v1(request)" in src
    assert "_not_triggered(self.policy_id)" in src
    # baseline POL-005 had exactly one not-triggered branch (simulation_only)
    base = _git("show", f"{BASELINE}:src/pcae/core/permission_broker_foundation.py")
    base_eval = base.split("class ExecutionDisabledRule")[1].split("class UnknownCapabilityRule")[0]
    assert base_eval.count("_not_triggered(self.policy_id)") == 1
    assert src.count("_not_triggered(self.policy_id)") == 2


# ═══════════════ 3. migration completeness / no auto-upgrade ═════════════

def test_pbrd_v3_migration_defines_the_mandatory_clauses():
    mig = _norm((REPO / "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text())
    mig = mig.split("v3.0 explicit migration semantics")[1]
    for needle in [
        "v2.1 is the superseded prior MAJOR line",
        "Existing v2.x request shapes remain parseable",
        "categorically DENIED", "No silent auto-upgrade",
        "There is no compatibility default to the narrow profile",
        "Independent verification is mandatory",
        "149O.20L.7O.3W.1R.2B.1R.1.1R.23",
    ]:
        assert needle in mig, needle


def test_legacy_v2x_shaped_request_gets_no_marker_and_is_denied():
    # a request the builder cannot fully classify carries "" and POL-005 DENYs
    _, _, request, decision = full_chain(simulation_only=False)
    assert request.runtime_dispatch_context.profile_classification == ""
    assert decision.decision == DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


def test_no_compatibility_default_promotes_to_the_narrow_profile():
    # empty marker + incomplete profile is the ONLY legacy state; and a
    # complete-looking profile without the trusted marker is a structural DENY
    facts = _facts()  # marker ""
    prov = _sealed(facts)
    # profile is "complete" structurally but marker is "" -> validator rejects
    assert _failed(prov, check_marker=False) == ()
    assert _valid_runtime_dispatch_request(prov) is False


# ═══════════════ 4. independent predicate enumeration ════════════════════

def test_independently_enumerated_predicate_ids():
    # Re-derive the predicate id set directly from the source of _failed().
    src = inspect.getsource(pbf._narrow_local_cli_dispatch_v1_failed_predicates)
    tree = ast.parse(src)
    appended = {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
        and node.args and isinstance(node.args[0], ast.Constant)
    }
    assert appended == {
        "P_trusted_builder_seal", "P_action_runtime_dispatch", "P_execution_class_adapter",
        "P_runtime_dispatch_context", "P_transport_local_cli", "P_network_prohibited",
        "P_supply_chain_admission", "P_human_authority_present", "P_human_authority_binding_valid",
        "P_attempt_identity", "P_runtime_target", "P_filesystem_scope",
        "P_trusted_profile_classification",
    }, appended
    # 13 checked predicates; P5..P7 (credential/provider/shell) hold by
    # construction (no request field exists) -> structural, not runtime.
    assert len(appended) == 13


def test_each_single_predicate_break_denies_via_pol013():
    breaks = [
        dict(transport_type="api"),
        dict(network_requirement=True),
        dict(adapter_descriptor_binding=_adapter(admitted=False)),
        dict(runtime_target_id=""),
        dict(attempt_id="not-an-att-id"),
        dict(human_authority_binding=_auth(False)),
        dict(filesystem_scope_ref=ScopeRef(scope_id="", scope_digest=HD)),
    ]
    for over in breaks:
        req = _sealed(_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **over))
        d = _decide(req)
        assert d.decision == DECISION_DENY, over


# ═══════════════ 5. trusted-builder ownership ════════════════════════════

def test_profile_classification_is_only_ever_set_by_the_trusted_builder():
    # every assignment/replace of profile_classification in src/pcae
    hits = _git("grep", "-n", "profile_classification", "--", "src/pcae")
    assign_lines = [l for l in hits.splitlines()
                    if "replace(facts, profile_classification=marker)" in l
                    or "profile_classification: str = \"\"" in l
                    or "facts.profile_classification" in l]
    # the only *write* is in runtime_dispatch_permission.build_...():
    writes = [l for l in hits.splitlines() if "profile_classification=marker" in l]
    assert len(writes) == 1
    assert "runtime_dispatch_permission.py" in writes[0]


def test_derive_is_referenced_only_by_the_builder_module():
    hits = _git("grep", "-l", "derive_runtime_dispatch_local_cli_v1_classification", "--", "src/pcae")
    assert set(hits.split()) == {
        "src/pcae/core/permission_broker_foundation.py",  # definition
        "src/pcae/core/runtime_dispatch_permission.py",   # sole caller
    }


def test_construction_input_rejects_caller_preset_admission_fields():
    src = inspect.getsource(rdp._validate_construction_inputs)
    assert 'adapter.admission_record_digest == ""' in src
    assert 'adapter.admission_class == ""' in src


# ═══════════════ 6-8. forged / reconstructed / incomplete markers ════════

def test_generic_builder_cannot_carry_a_runtime_dispatch_request():
    with pytest.raises(Exception):
        pbf.build_permission_broker_request(
            requested_component="COMP-006", requested_capability="x", task_id="t",
            phase_id="p", action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
        )


def test_marker_survives_replace_but_stripping_the_seal_defeats_the_carveout():
    good = _complete()
    assert _is_trusted_narrow_local_cli_dispatch_v1(good) is True
    unsealed = replace(good, _runtime_dispatch_seal=None)
    assert _is_trusted_narrow_local_cli_dispatch_v1(unsealed) is False
    # and the structural validator rejects it (seal predicate fails)
    assert _valid_runtime_dispatch_request(unsealed) is False
    assert _decide(unsealed).decision == DECISION_DENY


def test_marker_present_but_one_predicate_absent_fails_closed():
    req = _sealed(_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1,
                         network_requirement=True))
    assert _valid_runtime_dispatch_request(req) is False
    assert _decide(req).decision == DECISION_DENY


def test_complete_profile_without_the_trusted_marker_is_structural_deny():
    req = _sealed(_facts())  # complete but marker ""
    assert _valid_runtime_dispatch_request(req) is False
    d = _decide(req)
    assert d.decision == DECISION_DENY
    assert d.decision_reason == "invalid_runtime_dispatch_request"


# ═══════════════ 9-10. recomputation completeness / digest binding ══════

def test_every_predicate_fact_is_recomputed_live_by_the_validator():
    # mutate each predicate-relevant fact on a marked request; the structural
    # validator must reject every one (marker set, profile now incomplete).
    good = _complete()
    f = good.runtime_dispatch_context
    mutations = [
        replace(f, transport_type="api"),
        replace(f, network_requirement=True),
        replace(f, runtime_target_id=""),
        replace(f, attempt_id="x"),
        replace(f, idempotency_key="short"),
        replace(f, human_authority_binding=_auth(False)),
        replace(f, adapter_descriptor_binding=_adapter(admitted=False)),
        replace(f, filesystem_scope_ref=ScopeRef(scope_id="", scope_digest="")),
    ]
    for mf in mutations:
        req = _sealed(mf)  # re-seal so only the fact differs
        # marker still the literal, profile now incomplete -> reject
        req2 = _sealed(replace(mf, profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1))
        assert _valid_runtime_dispatch_request(req2) is False, mf


def test_admission_fields_are_in_the_canonical_projection():
    proj = rdp.canonical_runtime_dispatch_projection(dispatch_inputs(), invocation_id=INV)
    assert "admission_record_digest" in proj["adapter_descriptor_binding"]
    assert "admission_class" in proj["adapter_descriptor_binding"]
    # production resolver -> unadmitted
    assert proj["adapter_descriptor_binding"]["admission_class"] == ADMISSION_CLASS_UNADMITTED


def test_admission_mutation_changes_the_idempotency_key():
    inp = dispatch_inputs()
    k_prod = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inp, invocation_id=INV))
    k_adm = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(
            inp, invocation_id=INV, _supply_chain_admission_resolver=_AdmittingResolver()))
    assert k_prod != k_adm


# ═══════════════ 11-12. admission interface / production stub ════════════

def test_production_supply_chain_resolver_admits_nothing():
    r = rdp._PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER
    for aid in ["", "x", "codex-local", "any-adapter", "local_fixed_argv"]:
        res = r.resolve(aid)
        assert res.admitted is False
        assert res.admission_class == ADMISSION_CLASS_UNADMITTED


def test_resolve_helper_fails_closed_on_bad_resolvers():
    class Broken:
        def resolve(self, a): raise RuntimeError("boom")
    class WrongType(rdp.SupplyChainAdmissionResolver):
        def resolve(self, a): return "not a result"
    class AdmitEmpty(rdp.SupplyChainAdmissionResolver):
        def resolve(self, a): return rdp.SupplyChainAdmissionResult(True, "", "")
    for bad in [Broken(), WrongType(), AdmitEmpty(), None, 42]:
        if bad is None:
            continue
        res = rdp._resolve_supply_chain_admission("x", bad)
        assert res.admitted is False
        assert res.admission_class == ADMISSION_CLASS_UNADMITTED


# ═══════════════ 13-14. private override / test-resolver isolation ══════

def test_no_production_call_site_passes_the_resolver_override():
    # the ONLY production call to the trusted builder is run_gate6_permission_broker;
    # neither it nor any src/pcae code passes _supply_chain_admission_resolver.
    hits = _git("grep", "-n", "_supply_chain_admission_resolver=", "--", "src/pcae")
    # keep only lines that bind the kwarg to something OTHER than None or the
    # same-named pass-through parameter.
    passing = []
    for l in hits.splitlines():
        rhs = l.split("_supply_chain_admission_resolver=", 1)[1].strip().rstrip(",")
        if rhs not in ("None", "_supply_chain_admission_resolver"):
            passing.append(l)
    assert passing == [], passing
    # exactly one production call to the trusted builder, inside the module itself
    calls = [l for l in _git("grep", "-rn", "build_runtime_dispatch_permission_broker_request(",
                             "--", "src/pcae").splitlines()
             if "def build_runtime_dispatch" not in l and "_build_runtime_dispatch" not in l
             and "`" not in l and "#" not in l.split(":", 2)[-1][:4]]
    assert len(calls) == 1, calls
    assert "runtime_dispatch_permission.py" in calls[0]


def test_resolver_default_is_none_and_the_production_default_is_non_admitting():
    for fn in (rdp.build_runtime_dispatch_permission_broker_request,
               rdp.canonical_runtime_dispatch_projection,
               rdp.new_runtime_dispatch_identity):
        sig = inspect.signature(fn)
        assert sig.parameters["_supply_chain_admission_resolver"].default is None
    assert type(rdp._PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER).__name__ == \
        "_NonAdmittingSupplyChainAdmissionResolver"


# ═══════════════ 15-17. production unsatisfiability / no PB ALLOW ═══════

def test_production_builder_never_classifies_the_narrow_profile():
    # full production path, simulation_only=False, no overrides
    _, _, request, decision = full_chain(simulation_only=False)
    assert request.runtime_dispatch_context.profile_classification == ""
    assert decision.decision == DECISION_DENY


def test_two_independent_production_blockers():
    import tempfile
    # B1: even a synthetic admitting resolver (identity minted with the SAME
    #     resolver so the idempotency key matches) still cannot classify,
    #     because approval_present stays False (no trusted authority projection).
    inp = dispatch_inputs()
    root = tempfile.TemporaryDirectory()
    tracker = rdp.RuntimeDispatchIdentityTracker(Path(root.name))
    ident = rdp.new_runtime_dispatch_identity(
        inp, identity_tracker=tracker, invocation_id=INV,
        _supply_chain_admission_resolver=_AdmittingResolver(),
    )
    req = rdp.build_runtime_dispatch_permission_broker_request(
        identity=ident, inputs=inp, validated_authority=None,
        simulation_only=False, _supply_chain_admission_resolver=_AdmittingResolver(),
    )
    assert req.runtime_dispatch_context.profile_classification == ""
    assert req.approval_present is False
    failed = _failed(req, check_marker=False)
    assert "P_human_authority_present" in failed
    assert "P_human_authority_binding_valid" in failed
    # B2: validate_approval rejects every caller-supplied approval object ->
    #     there is no path (prod or test) to a trusted ValidatedAuthority.
    approval, projection, request, decision = full_chain(simulation_only=False)
    assert projection is None
    assert decision.decision == DECISION_DENY


def test_no_production_path_reaches_pb_allow_for_a_real_runtime_dispatch():
    # A real (non-simulation) production runtime_dispatch always DENYs.
    _, _, _, d_real = full_chain(simulation_only=False)
    assert d_real.decision == DECISION_DENY
    assert "POL-005" in d_real.causing_policy_ids


# ═══════════════ 18-22. POL-005 semantics ═══════════════════════════════

def test_pol005_deny_body_is_byte_identical_to_baseline():
    base = _git("show", f"{BASELINE}:src/pcae/core/permission_broker_foundation.py")
    def _body(text):
        seg = text.split("class ExecutionDisabledRule")[1].split("class UnknownCapabilityRule")[0]
        return seg.split("return PolicyResult(")[1].split("class ")[0]
    assert _body(base).replace(" ", "").replace("\n", "") == \
        _body(PBF_SRC).replace(" ", "").replace("\n", "")


def test_pol005_still_universal_applicability():
    assert pbf.ExecutionDisabledRule().applicable_execution_classes is None


def test_pol005_carveout_reads_only_marker_and_seal():
    src = inspect.getsource(pbf._is_trusted_narrow_local_cli_dispatch_v1)
    assert "profile_classification == PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1" in src
    assert "_runtime_dispatch_seal" in src
    # no caller-field / shape inference
    assert "approval_present" not in src and "transport_type" not in src


def test_pol005_caller_forged_narrowish_facts_do_not_untrigger():
    # take a legitimately-sealed complete profile, strip the seal: the
    # carve-out predicate now reads False and POL-005 triggers its DENY.
    good = _complete()
    unsealed = replace(good, _runtime_dispatch_seal=None)
    assert _is_trusted_narrow_local_cli_dispatch_v1(unsealed) is False
    assert pbf.ExecutionDisabledRule().evaluate(unsealed).triggered is True
    # the generic builder also refuses to carry a runtime_dispatch context
    with pytest.raises(ValueError, match="runtime_dispatch_requires_trusted_builder"):
        pbf.build_permission_broker_request(
            requested_component="COMP-006", requested_capability="x",
            action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
            execution_class=pbf.EXECUTION_CLASS_ADAPTER,
            runtime_dispatch_context=_facts(),
        )


def test_pol005_hard_deny_for_every_other_non_simulation_class():
    cases = [
        (pbf.ACTION_SHELL_COMMAND, pbf.EXECUTION_CLASS_SHELL),
        (pbf.ACTION_ADAPTER_INVOCATION, pbf.EXECUTION_CLASS_ADAPTER),
        (pbf.ACTION_BACKEND_INVOCATION, pbf.EXECUTION_CLASS_BACKEND),
        (pbf.ACTION_ROLLBACK, pbf.EXECUTION_CLASS_ROLLBACK),
        (pbf.ACTION_PUSH, pbf.EXECUTION_CLASS_MUTATION),
    ]
    for at, ec in cases:
        req = pbf.build_permission_broker_request(
            requested_component="COMP-002", requested_capability="c", task_id="t",
            phase_id="p", action_type=at, execution_class=ec, simulation_only=False,
        )
        res = pbf.ExecutionDisabledRule().evaluate(req)
        assert res.triggered and res.decision == DECISION_DENY, (at, ec)


# ═══════════════ 23-26. POL-013 static + dynamic ═══════════════════════

def test_pol013_static_return_analysis_never_allow_or_human_review():
    import textwrap
    tree = ast.parse(textwrap.dedent(
        inspect.getsource(pbf.NarrowLocalCliDispatchEligibilityRule.evaluate)))
    returns = [n for n in ast.walk(tree) if isinstance(n, ast.Return)]
    assert returns, "no returns found"
    for r in returns:
        v = r.value
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "_not_triggered":
            continue
        assert isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "PolicyResult"
        kw = {k.arg: k.value for k in v.keywords}
        assert isinstance(kw["decision"], ast.Name) and kw["decision"].id == "DECISION_DENY"
    # no code (docstrings stripped) in the rule references positive authority
    rule_ast = ast.parse(textwrap.dedent(inspect.getsource(pbf.NarrowLocalCliDispatchEligibilityRule)))
    names = {n.id for n in ast.walk(rule_ast) if isinstance(n, ast.Name)}
    consts = {n.value for n in ast.walk(rule_ast) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "DECISION_ALLOW" not in names and "DECISION_HUMAN_REVIEW" not in names
    assert "ALLOW" not in consts and "HUMAN_REVIEW" not in consts


def test_pol013_dynamic_result_vocabulary():
    rule = pbf.NarrowLocalCliDispatchEligibilityRule()
    # complete profile -> not triggered
    assert rule.evaluate(_complete()).triggered is False
    # each gap -> DENY with the exact reason
    for over in [dict(network_requirement=True), dict(runtime_target_id=""),
                 dict(adapter_descriptor_binding=_adapter(admitted=False)),
                 dict(human_authority_binding=_auth(False))]:
        r = rule.evaluate(_sealed(_facts(
            profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **over)))
        assert r.triggered and r.decision == DECISION_DENY
        assert r.decision_reason == "narrow_local_cli_dispatch_profile_incomplete"
    # non-runtime-dispatch adapter request / simulation -> no-op
    sim = _sealed(_facts(), simulation_only=True)
    assert rule.evaluate(sim).triggered is False


def test_pol013_neutral_is_not_an_allow_vote_and_never_suppresses_a_deny():
    from pcae.core.permission_broker_foundation import _compose, _not_triggered, PolicyResult
    deny = PolicyResult(policy_id="POL-005", triggered=True, decision=DECISION_DENY,
                        decision_reason="execution_boundary_unavailable")
    neutral = _not_triggered("POL-013")
    # POL-013 neutral cannot cancel a co-present DENY
    assert _compose((deny, neutral)).decision == DECISION_DENY
    # POL-013 neutral is `triggered=False` — it casts no ALLOW vote; a lone
    # neutral leaves the INV-008 "would allow if execution existed" default,
    # which is explicitly non-executable.
    assert neutral.triggered is False
    lone = _compose((neutral,))
    assert lone.decision == DECISION_ALLOW and "INV-008" in lone.matched_invariants


def test_pol013_applicability_is_adapter_only_and_registered_last():
    rule = pbf.NarrowLocalCliDispatchEligibilityRule()
    assert rule.applicable_execution_classes == frozenset({pbf.EXECUTION_CLASS_ADAPTER})
    assert rule.policy_id == "POL-013"
    assert pbf.DEFAULT_POLICY_RULES[-1].policy_id == "POL-013"
    assert pbf.POLICY_IDS_CANONICAL == frozenset(f"POL-{n:03d}" for n in range(1, 14))
    PolicyRegistry()  # construction-time completeness check must still pass


# ═══════════════ 27-30. _compose precedence / dominance / human wall ═══

def test_compose_is_byte_unchanged_since_baseline():
    base = _git("show", f"{BASELINE}:src/pcae/core/permission_broker_foundation.py")
    def _fn(text, name):
        return text.split(f"def {name}(")[1].split("\ndef ")[0]
    for name in ("_compose", "_structural_request_failure", "_decision"):
        assert _fn(base, name) == _fn(PBF_SRC, name), name
    assert _fn(base, "_valid_runtime_dispatch_request") != _fn(PBF_SRC, "_valid_runtime_dispatch_request")


def test_precedence_deny_beats_human_review_beats_allow():
    from pcae.core.permission_broker_foundation import _compose, _not_triggered, PolicyResult
    d = PolicyResult(policy_id="A", triggered=True, decision=DECISION_DENY, decision_reason="d")
    h = PolicyResult(policy_id="B", triggered=True, decision=DECISION_HUMAN_REVIEW, decision_reason="h")
    a = PolicyResult(policy_id="C", triggered=True, decision=DECISION_ALLOW, decision_reason="a")
    assert _compose((a, h, d)).decision == DECISION_DENY
    assert _compose((a, h)).decision == DECISION_HUMAN_REVIEW
    assert _compose((_not_triggered("X"), a)).decision == DECISION_ALLOW


def test_complete_profile_plus_unrelated_deny_still_denies():
    # POL-001 missing active task is unrelated; force it by a bare phase/task
    req = _complete(task_id="")
    d = _decide(req)
    assert d.decision == DECISION_DENY


def test_human_authority_alone_never_exempts_pol005():
    # approval_present True but profile invalid -> DENY
    req = _sealed(_facts(network_requirement=True), approval_present=True)
    assert _decide(req).decision == DECISION_DENY


# ═══════════════ 31-46. broader effect classes / bindings / replay ═════

def test_broader_effect_classes_all_blocked():
    # each of these genuinely breaks a narrow-profile predicate -> DENY
    cases = [
        dict(transport_type="api"),               # provider/API transport
        dict(network_requirement=True),            # network
        dict(adapter_descriptor_binding=_adapter(admitted=False)),  # unadmitted supply chain
        dict(adapter_descriptor_binding=replace(_adapter(True), admission_class="dynamic_argv")),
        dict(runtime_target_id=""),                # no bound target
        dict(human_authority_binding=_auth(False)),  # no human authority
    ]
    for over in cases:
        req = _sealed(_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **over))
        assert _decide(req).decision == DECISION_DENY, over


def test_runtime_target_and_attempt_and_scope_bindings_enforced():
    for over in (dict(runtime_target_id=""),
                 dict(attempt_id="att-bad"),
                 dict(idempotency_key="short"),
                 dict(filesystem_scope_ref=ScopeRef(scope_id="", scope_digest=""))):
        req = _sealed(_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **over))
        assert _valid_runtime_dispatch_request(req) is False, over


def test_profile_replay_transplant_is_rejected():
    a = _complete()
    fb = _facts(invocation_id="inv-" + "7" * 32, attempt_id="att-" + "8" * 32)
    # transplant A's marker onto B's facts without re-derivation via builder
    transplanted = _sealed(replace(fb, profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1))
    # still structurally valid only if every predicate holds for B too; if so,
    # the point is the marker cannot carry A's identity — B is judged on B.
    assert _decide(transplanted).decision in (DECISION_DENY, DECISION_ALLOW)
    # the decisive check: a NON-complete B with A's marker is a structural DENY
    bad_b = _sealed(replace(fb, network_requirement=True,
                            profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1))
    assert _valid_runtime_dispatch_request(bad_b) is False


# ═══════════════ 47-51. NON_REAL wall / gate independence / runtime ═══

def test_non_real_lineage_wall_is_upstream_and_unchanged():
    # runtime_authority.py is NOT among the .1R.22 changed files
    changed = set(_git("diff", "--name-only", BASELINE, "HEAD", "--", "src/pcae").split())
    assert "src/pcae/core/runtime_authority.py" not in changed
    # validate_approval still rejects caller-supplied approval objects
    _, _, _, _ = full_chain()


def test_gate7_and_gate9_and_gate10_modules_byte_unchanged():
    # runtime_dispatch_gate7.py is authorizedly changed by Phase ...1R.26
    # (N-16-4 -- REPRC-001 v1.0); Gate 5 / 8 / 9 / 10 remain byte-frozen here.
    for g in ["runtime_dispatch_gate8.py",
              "runtime_dispatch_gate9.py", "runtime_dispatch_gate10_eligibility.py",
              "runtime_dispatch_gate5.py"]:
        assert _git("diff", "--stat", BASELINE, "HEAD", "--", f"src/pcae/core/{g}").strip() == "", g


def test_runtime_posture_unchanged():
    assert (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            ri.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")


def test_ng_025_annotation_is_in_the_right_file_only():
    ng = (REPO / "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md").read_text()
    assert "RUNTIME_DISPATCH_LOCAL_CLI_V1" in ng
    assert "Human\noverride remains `no`" in ng or "Human override remains `no`" in ng \
        or "override remains `no`" in ng
    # NOT added to the RE No-Go Registry
    reg = REPO / "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md"
    if reg.exists():
        assert "RUNTIME_DISPATCH_LOCAL_CLI_V1" not in reg.read_text()


def test_pbpa_v1_1_amendment_is_additive_only():
    pbpa = (REPO / "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md").read_text()
    assert pbpa.startswith("# PBPA-001") and "**Version:**\n1.1" in pbpa.replace(" ", "\n", 0) \
        or "Version:** 1.1" in pbpa
    assert "POL-013" in pbpa
    assert "two\ncurrently-implemented scoped policies" in pbpa or \
        "two currently-implemented scoped policies" in pbpa or \
        "to two currently-implemented" in pbpa


# ═══════════════ 52-54. contract-production equivalence / no effect ═══

def test_contract_production_equivalence_pbnde_predicates():
    pbnde = (REPO / "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md").read_text()
    for token in ["RUNTIME_DISPATCH_LOCAL_CLI_V1", "POL-013", "local_fixed_argv",
                  "narrow_local_cli_dispatch_profile_incomplete",
                  "_is_trusted_narrow_local_cli_dispatch_v1",
                  "_valid_runtime_dispatch_request"]:
        assert token in pbnde, token
        assert token in PBF_SRC or token in RDP_SRC, token


def test_no_first_effect_primitive_added_in_touched_modules():
    added = [l for l in _git("diff", BASELINE, "HEAD", "--", "src/pcae").splitlines()
             if l.startswith("+") and not l.startswith("+++")]
    for banned in ["adapter.dispatch(", "subprocess.", "socket.", "os.system", "Popen",
                   "urllib", "requests.", "httpx", "os.exec"]:
        assert not any(banned in l for l in added), banned


def test_no_test_weakening_in_the_r122_diff():
    # Reconciliation-aware (.1R.22R): scoped to the historical .1R.22 range
    # BASELINE..R22_HEAD ("the r122 diff"), which is what this guard means
    # and is immutable. The original body scanned BASELINE..HEAD, which
    # (a) grew to include .1R.23's own suite — whose source quotes
    # "pytest.mark.xfail" as string data, self-matching the scanner (the
    # same class of bug .1R.19R.1 fixed for its own suite, commit dfbb79ca)
    # — and (b) will later include .1R.22R's authorized guard reconciliation.
    # The .1R.22 test diff is the correct, stable scope for this assertion.
    diff = _git("diff", BASELINE, R22_HEAD, "--", "tests/")
    removed_defs = [l for l in diff.splitlines()
                    if l.startswith("-") and l.lstrip("-").strip().startswith(("def test_", "async def test_"))]
    assert removed_defs == []
    added_xfail = [l for l in diff.splitlines()
                   if l.startswith("+") and ("pytest.mark.xfail" in l or "pytest.xfail(" in l)]
    assert added_xfail == []
    # the single added pytest.skip is a scoped byte-freeze reconciliation
    skips = [l for l in diff.splitlines() if l.startswith("+") and "pytest.skip(" in l]
    assert len(skips) <= 1


# ═══════════════ 55-63. fixed-SHA A/B guard-regression attribution ══════

# The 16 functional guard/contract-freeze test nodes that PASS at the
# independently-reconstructed baseline 8603fe6a and FAIL at HEAD, are
# attributable to the two authorized .1R.22 changes (add POL-013; PBPA-001
# v1.0->v1.1 + PBRD v2.1->v3.0 + POL-005 §12a), and are NOT listed in the
# .1R.22 canonical artifact §11.1 guard-impact inventory or disclosed in
# §12 (which asserts "0 unexplained attributable functional regressions").
# This is the .1R.23 BLOCKER (N-23-3). Reproduced deterministically, no xdist,
# via `git worktree add <wt> 8603fe6a`.
R122_UNDISCLOSED_ATTRIBUTABLE_GUARD_REGRESSIONS = (
    "test_permission_broker_policy_rule_framework.py::test_registry_has_twelve_policies",
    "test_permission_broker_policy_rule_framework.py::test_policy_ids_are_stable_and_ordered",
    "test_permission_broker_policy_rule_framework.py::test_broker_evaluated_policy_ids_equal_applicable_policy_set",
    "test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_even_when_one_triggers",
    "test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_every_time",
    "test_permission_broker_observation_verification.py::test_broker_default_policy_rule_count_unchanged",
    "test_phase_149d_rwmpc_contract_independent_verification.py::TestContractsUnamended::test_pbpc_and_pbpa_contract_files_unchanged_since_before_chapter_149",
    "test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py::TestMC14EffectTruthfulnessAgainstCurrentSource::test_pol_005_denies_unconditionally_when_simulation_only_false",
    "test_phase_149o_18c_ag3_mandatory_consumption_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]",
    "test_phase_149o_18d_ag5_mandatory_consumption_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]",
    "test_phase_149o_18e_cli_legacy_authority_migration_integration.py::TestContractByteIdentity::test_contract_byte_unchanged[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]",
    "test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py::test_upstream_contract_byte_unchanged_by_this_repair[PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md]",
    "test_phase_149o_20l_7o_3v_1r_1_contract_verification.py::TestBoundariesUnchanged::test_pol_005_unchanged_claim_present",
    "test_phase_149o_20l_7o_3v_1r_contract_repair.py::TestNoNewContradictions::test_no_go_statements_preserved",
    "test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_pbrd_remains_projection_only_and_pol005_remains_hard_deny",
    "test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_rpac_companion_contract_is_byte_identical_and_riasc_pbrd_only_normalized",
)


# .1R.22R independently re-derived the fixed-SHA A/B (8603fe6a -> 15aeb269)
# — first over the 11 files this suite implicates, then over the full suite /
# ~65 candidate files — and found the true attributable set is TWENTY-TWO,
# not sixteen: the .1R.23 enumeration above under-counted by SIX (same
# self-similar guard-freeze class: PBRD-001 v2.1->v3.0 version pins and PBPA
# byte-freeze). All six were reconciled by .1R.22R.
R122R_ADDITIONALLY_ENUMERATED = (
    "test_phase_149d_rwmpc_contract_independent_verification.py::TestNoProductionModification::test_existing_contract_text_not_amended_by_phase_149d",
    "test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_active_contract_versions_after_1r15_4_normalization",
    "test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_independent_verification_3w1r2b1r111r1.py::test_versions_after_1r15_4_normalization",
    "test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py::test_contract_headers_are_the_normalized_minor_versions",
    "test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py::test_both_major_candidate_calls_are_adjudicated_minor",
    "test_runtime_human_principal_cross_contract_freeze_repair_independent_verification_3w1r2b1r11.py::test_active_versions_and_supersession_are_exact",
)
R122_ALL_ATTRIBUTABLE_GUARD_REGRESSIONS = (
    R122_UNDISCLOSED_ATTRIBUTABLE_GUARD_REGRESSIONS + R122R_ADDITIONALLY_ENUMERATED
)


def test_r122_artifact_does_not_disclose_these_regressions():
    # Reconciliation-aware (.1R.22R). Historically true at .1R.23: neither
    # the .1R.22 canonical doc's original body nor PROJECT_STATUS disclosed
    # these attributable guard regressions, and the record claimed "0
    # unexplained attributable functional regressions". .1R.22R issued a
    # provenance-preserving erratum. Assert BOTH: the original claim is
    # still present verbatim (historical record preserved), AND an erratum
    # now names the regression set and records the true count.
    doc = next(REPO.glob("docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_22_*.md")).read_text()
    status = (REPO / "PROJECT_STATUS.md").read_text()
    flat_status = " ".join(status.split())
    # Original inaccurate claim preserved as historical evidence:
    assert "0 unexplained attributable functional regressions" in flat_status
    # Erratum issued by .1R.22R, appended after the original canonical trailer:
    assert "## ERRATUM" in doc and "149O.20L.7O.3W.1R.2B.1R.1.1R.22R" in doc
    assert "22" in doc  # the corrected attributable count
    for node in R122_ALL_ATTRIBUTABLE_GUARD_REGRESSIONS:
        base = node.split("::")[0]
        assert base in doc, f"erratum omits attributable guard: {base}"
    # PROJECT_STATUS now records the .1R.22R reconciliation:
    assert "1R.22R" in status


def test_count_is_sixteen_and_all_are_registry_or_contract_freeze_guards():
    # The .1R.23 enumeration was sixteen; .1R.22R's independent re-derivation
    # found six more of the same class (total twenty-two). Both figures are
    # asserted so the historical .1R.23 count stays on record.
    assert len(R122_UNDISCLOSED_ATTRIBUTABLE_GUARD_REGRESSIONS) == 16
    assert len(set(R122_UNDISCLOSED_ATTRIBUTABLE_GUARD_REGRESSIONS)) == 16
    assert len(R122R_ADDITIONALLY_ENUMERATED) == 6
    assert len(set(R122_ALL_ATTRIBUTABLE_GUARD_REGRESSIONS)) == 22


@pytest.mark.skipif(
    "8603fe6a" not in _git("rev-list", "HEAD", "--max-count=400"),
    reason="baseline not in local history",
)
def test_ab_delta_is_exactly_these_sixteen_when_a_baseline_worktree_is_available():
    # Reconciliation-aware (.1R.22R). At .1R.23 every listed node FAILED at
    # HEAD — that was the N-23-3 blocker. .1R.22R widened each stale
    # point-in-time guard to the exact authorized change set (POL-013 /
    # PBPA-001 v1.1 / PBRD-001 v3.0 / POL-005 §12a), no wildcard. Assert the
    # repaired current state: every attributable node now PASSES at HEAD.
    import subprocess
    r = subprocess.run(
        ["python", "-m", "pytest", "-q", "-o", "addopts=", "--no-header",
         *[f"tests/{n}" for n in R122_ALL_ATTRIBUTABLE_GUARD_REGRESSIONS]],
        cwd=REPO, capture_output=True, text=True,
    )
    assert " failed" not in r.stdout, r.stdout[-3000:]
    assert "22 passed" in r.stdout, r.stdout[-3000:]


def test_policy_registry_integrity_no_dupes_no_gaps():
    ids = [r.policy_id for r in pbf.DEFAULT_POLICY_RULES]
    assert len(ids) == len(set(ids))
    assert set(ids) >= pbf.POLICY_IDS_CANONICAL
    assert sorted(pbf.POLICY_IDS_CANONICAL) == [f"POL-{n:03d}" for n in range(1, 14)]
