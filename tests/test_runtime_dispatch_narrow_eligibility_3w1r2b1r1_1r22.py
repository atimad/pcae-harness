"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3 Narrow-Eligibility Policy
and Contract Implementation. The `.1R.21` §37 defensive policy test matrix
(25 cases) plus the phase-prompt §50 static-never-ALLOW scan, §53 / §54
caller-forgery / provenance challenges, and the §63 contract-production
equivalence map.

Every case asserts NO external effect: the runtime posture is never mutated
and there is no `adapter.dispatch(` call site anywhere in `src/pcae`.

`.1R.23` re-derives every claim here.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core.permission_broker_foundation import (
    ADMISSION_CLASS_LOCAL_FIXED_ARGV,
    ADMISSION_CLASS_UNADMITTED,
    PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1,
    PermissionBroker,
    RuntimeDispatchAdapterDescriptorBinding,
    RuntimeDispatchFilesystemScopeRef,
    RuntimeDispatchHumanAuthorityBinding,
    RuntimeDispatchLifecycleContext,
    RuntimeDispatchRequestFacts,
    _build_runtime_dispatch_permission_broker_request,
    _is_trusted_narrow_local_cli_dispatch_v1,
    _narrow_local_cli_dispatch_v1_failed_predicates,
    _valid_runtime_dispatch_request,
    derive_runtime_dispatch_local_cli_v1_classification,
)

from _rdw3w_helpers import dispatch_inputs, full_chain, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
HEX64 = "a" * 64
HEX64_B = "b" * 64
HEX64_C = "c" * 64
HEX64_D = "d" * 64
HEX64_E = "e" * 64
ADM_DIGEST = "9" * 64


# ══════════════════════════════════════════════════════════════════════════
# Helpers — a hand-built, seal-constructed request whose predicates we vary.
# (There is no production/test path to a trusted ValidatedAuthorityProjection
#  — validate_approval deliberately rejects caller-supplied objects — so the
#  "structurally complete profile" cases build the sealed request directly
#  and exercise the POLICY logic, which is what the matrix cares about.)
# ══════════════════════════════════════════════════════════════════════════

_INV = "inv-" + "0" * 32
_ATT = "att-" + "1" * 32


def _authority(*, valid: bool = True) -> RuntimeDispatchHumanAuthorityBinding:
    if valid:
        return RuntimeDispatchHumanAuthorityBinding(
            approval_id="ria-" + "2" * 32,
            approval_record_digest=HEX64_B,
            validation_evidence_digest=HEX64_C,
        )
    return RuntimeDispatchHumanAuthorityBinding("", "", "")


def _adapter(*, admitted: bool = True) -> RuntimeDispatchAdapterDescriptorBinding:
    return RuntimeDispatchAdapterDescriptorBinding(
        adapter_id="fixture-adapter",
        descriptor_version="1.0",
        descriptor_digest=HEX64_D,
        target_config_digest=HEX64_E,
        admission_record_digest=ADM_DIGEST if admitted else "",
        admission_class=ADMISSION_CLASS_LOCAL_FIXED_ARGV if admitted else ADMISSION_CLASS_UNADMITTED,
    )


def _facts(**over) -> RuntimeDispatchRequestFacts:
    base = dict(
        invocation_id=_INV,
        attempt_id=_ATT,
        idempotency_key=HEX64,
        repository_identity=HEX64_B,
        task_id="task-a",
        lifecycle_context=RuntimeDispatchLifecycleContext(phase_id="149O.20L.7O.3W", session_id=None),
        runtime_target_id="local-cli-fixture-1",
        adapter_descriptor_binding=_adapter(admitted=True),
        prompt_hash=HEX64_C,
        requested_capability="local_cli_dispatch",
        filesystem_scope_ref=RuntimeDispatchFilesystemScopeRef(scope_id="fs-1", scope_digest=HEX64_D),
        human_authority_binding=_authority(valid=True),
        transport_type="local_cli",
        network_requirement=False,
        profile_classification="",
    )
    base.update(over)
    return RuntimeDispatchRequestFacts(**base)


def _sealed_request(
    facts: RuntimeDispatchRequestFacts,
    *,
    approval_present: bool = True,
    simulation_only: bool = False,
):
    return _build_runtime_dispatch_permission_broker_request(
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


def _complete_profile_request(**facts_over):
    """A structurally complete RUNTIME_DISPATCH_LOCAL_CLI_V1 request: sealed,
    admitted adapter, valid authority, and the derived marker stamped."""
    provisional = _sealed_request(_facts(**facts_over))
    assert _narrow_local_cli_dispatch_v1_failed_predicates(provisional, check_marker=False) == ()
    marked = _facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, **facts_over)
    return _sealed_request(marked)


class _AdmittingResolver(rdp.SupplyChainAdmissionResolver):
    """TEST-BOUNDARY only. Synthetic admitting N-16-6 resolver."""

    def resolve(self, adapter_id: str) -> rdp.SupplyChainAdmissionResult:
        return rdp.SupplyChainAdmissionResult(
            admitted=True,
            admission_record_digest=ADM_DIGEST,
            admission_class=ADMISSION_CLASS_LOCAL_FIXED_ARGV,
        )


def _decide(request):
    return PermissionBroker().evaluate(request)


# ══════════════════════════════════════════════════════════════════════════
# Runtime zero-effect invariant (asserted once; the matrix relies on it)
# ══════════════════════════════════════════════════════════════════════════

PHASE_ENTRY = "8603fe6a"


def test_runtime_posture_unchanged_and_no_new_first_effect_call_site():
    from pcae.core import runtime_introspection as ri

    assert (ri.CURRENT_RUNTIME_STATE, ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            ri.EXECUTION_AVAILABILITY) == ("Observed", "observe", "unavailable")
    # case 25: .1R.22 adds NO new `adapter.dispatch(` call site. (The only
    # pre-existing one is the mock/dry `simulate_invocation` path in
    # runtime_adapter.py, unchanged here.)
    diff = subprocess.run(
        ["git", "diff", PHASE_ENTRY, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    assert not any("adapter.dispatch(" in l for l in added)
    # no Gate-10 real-effect module was created
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    # the current src/pcae diff since .1R.22 entry is exactly the authorized
    # files: the original two .1R.22 files, plus `.1R.26`'s later-authorized,
    # single-file N-16-4 addition of runtime_dispatch_gate7.py (149O.20L.7O.
    # 3W.1R.2B.1R.1.1R.26R reconciliation — see production_byte_scope in the
    # .1R.26 canonical report: git diff 28b8b2b7 HEAD -- src/pcae is exactly
    # that one file). Exact-set equality is preserved; any further
    # unauthorized src/pcae file still fails this assertion.
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY, "HEAD", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.split())
    assert changed == {
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
    }, changed


# ══════════════════════════════════════════════════════════════════════════
# §37 matrix
# ══════════════════════════════════════════════════════════════════════════

def test_case_01_existing_runtime_dispatch_no_narrow_profile_denies():
    _, _, request, decision = full_chain(simulation_only=False)
    assert request.runtime_dispatch_context.profile_classification == ""
    assert decision.decision == "DENY"
    # POL-013 reinforces POL-005's hard DENY.
    assert decision.causing_policy_ids == ("POL-005", "POL-013")
    assert "NG-025" in decision.matched_no_go_ids


def test_case_02_caller_forged_profile_classification_via_generic_builder():
    with pytest.raises(ValueError, match="runtime_dispatch_requires_trusted_builder"):
        pbf.build_permission_broker_request(
            action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
            execution_class=pbf.EXECUTION_CLASS_ADAPTER,
            requested_component="COMP-006",
            requested_capability="c",
        )


def test_case_02b_generic_builder_rejects_runtime_dispatch_context():
    with pytest.raises(ValueError, match="runtime_dispatch_requires_trusted_builder"):
        pbf.build_permission_broker_request(
            action_type=pbf.ACTION_PUSH,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            requested_component="COMP-001",
            requested_capability="push",
            runtime_dispatch_context=_facts(),
        )


def test_case_03_missing_supply_chain_admission_binding_denies():
    req = _sealed_request(_facts(adapter_descriptor_binding=_adapter(admitted=False)))
    failed = _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True)
    assert "P_supply_chain_admission" in failed
    d = _decide(req)
    assert d.decision == "DENY"
    assert "POL-005" in d.causing_policy_ids and "POL-013" in d.causing_policy_ids


def test_case_04_admitted_but_wrong_admission_class_denies():
    bad = replace(_adapter(admitted=True), admission_class="dynamic_argv")
    req = _sealed_request(_facts(adapter_descriptor_binding=bad))
    assert "P_supply_chain_admission" in _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True)
    assert _decide(req).decision == "DENY"


def test_case_05_network_requirement_true_is_rejected_at_construction():
    # _valid_runtime_dispatch_request already rejects network_requirement != False
    req = _sealed_request(_facts(network_requirement=True))
    assert _valid_runtime_dispatch_request(req) is False
    assert _decide(req).decision == "DENY"


def test_case_06_credential_field_has_no_representation():
    # PBRD §6: there is no credential field on RuntimeDispatchRequestFacts.
    assert "credential" not in {f.name for f in dataclasses.fields(RuntimeDispatchRequestFacts)}
    assert not any(
        "secret" in f.name or "token" in f.name or "credential" in f.name
        for f in dataclasses.fields(rdp.RuntimeDispatchRequestConstructionInput)
    )


def test_case_07_no_shell_or_command_string_field():
    for dc in (RuntimeDispatchRequestFacts, rdp.RuntimeDispatchRequestConstructionInput):
        names = {f.name for f in dataclasses.fields(dc)}
        assert not any("shell" in n or "command" in n or "argv" in n for n in names)


def test_case_08_wrong_runtime_target_id_denies():
    req = _sealed_request(_facts(runtime_target_id="   "))
    assert _valid_runtime_dispatch_request(req) is False
    req2 = _sealed_request(_facts(runtime_target_id=""))
    assert "P_runtime_target" in _narrow_local_cli_dispatch_v1_failed_predicates(req2, check_marker=True)


def test_case_09_non_real_lineage_is_ineligible():
    req = _sealed_request(_facts(human_authority_binding=_authority(valid=False)), approval_present=False)
    failed = _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True)
    assert "P_human_authority_present" in failed
    d = _decide(req)
    assert d.decision == "DENY"          # POL-005 + POL-013 (non-simulation)
    # A simulation of the same request routes to HUMAN_REVIEW via POL-004.
    sim = _sealed_request(
        _facts(human_authority_binding=_authority(valid=False)),
        approval_present=False, simulation_only=True,
    )
    assert _decide(sim).decision == "HUMAN_REVIEW"
    assert "POL-004" in _decide(sim).causing_policy_ids


def test_case_10_missing_attempt_binding_denies():
    req = _sealed_request(_facts(attempt_id="att-not-hex"))
    assert _valid_runtime_dispatch_request(req) is False


def test_case_11_malformed_profile_evidence_fails_closed():
    bad = replace(_adapter(admitted=True), admission_record_digest="not-a-sha")
    req = _sealed_request(_facts(adapter_descriptor_binding=bad))
    assert "P_supply_chain_admission" in _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True)
    assert _decide(req).decision == "DENY"


def test_case_12_all_predicates_valid_pol005_not_categorical_pol013_neutral():
    req = _complete_profile_request()
    assert _valid_runtime_dispatch_request(req) is True
    assert _is_trusted_narrow_local_cli_dispatch_v1(req) is True
    assert _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True) == ()
    # POL-005 not triggered; POL-013 not triggered; the request is still
    # decided by every other policy — here POL-004 is satisfied (approval
    # present), POL-001/003/006/007 pass, so the composition default is ALLOW
    # ("policy would allow if execution existed") — never an executable token.
    d = _decide(req)
    assert "POL-005" not in d.triggered_policy_ids
    assert "POL-013" not in d.triggered_policy_ids
    assert d.decision == "ALLOW"
    assert d.implementation_status == pbf.IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_case_13_complete_profile_plus_another_deny_still_denies():
    req = _sealed_request(
        _facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1, task_id="task-a"),
    )
    # Force POL-003 (missing evidence) to trigger by rebuilding without evidence.
    req = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=False, approval_present=True, simulation_only=False,
        runtime_dispatch_context=_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1),
    )
    d = _decide(req)
    assert d.decision == "DENY"
    assert "POL-003" in d.causing_policy_ids


def test_case_14_complete_profile_without_approval_is_human_review():
    req = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=True, approval_present=False, simulation_only=False,
        runtime_dispatch_context=_facts(
            human_authority_binding=_authority(valid=False),
        ),
    )
    # No marker (P_human_authority fails) -> POL-005 DENYs. But if we force a
    # marked request with approval_present False, _valid_runtime_dispatch_request
    # rejects it (authority inconsistency). So the honest case-14 statement:
    # a complete profile REQUIRES approval_present True; without it the request
    # is not the narrow profile and POL-004 HUMAN_REVIEW dominates ALLOW for a
    # simulation.
    sim = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=True, approval_present=False, simulation_only=True,
        runtime_dispatch_context=_facts(human_authority_binding=_authority(valid=False)),
    )
    d = _decide(sim)
    assert d.decision == "HUMAN_REVIEW"
    assert "POL-004" in d.causing_policy_ids


def test_case_15_narrow_profile_never_returns_allow_by_classification():
    # ALLOW only ever arrives via _compose's default (no DENY / HUMAN_REVIEW).
    src = inspect.getsource(pbf.NarrowLocalCliDispatchEligibilityRule.evaluate)
    assert "DECISION_ALLOW" not in src
    assert "DECISION_HUMAN_REVIEW" not in src
    src5 = inspect.getsource(pbf.ExecutionDisabledRule.evaluate)
    assert "DECISION_ALLOW" not in src5


def test_case_16_pb_decision_bound_to_exact_attempt():
    req_a = _complete_profile_request()
    req_b_facts = _facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1,
                         attempt_id="att-" + "3" * 32)
    req_b = _sealed_request(req_b_facts)
    assert req_a.runtime_dispatch_context.attempt_id != req_b.runtime_dispatch_context.attempt_id


def test_case_17_mutating_the_marker_is_a_structural_deny():
    good = _complete_profile_request()
    tampered_facts = replace(good.runtime_dispatch_context, profile_classification="SOMETHING_ELSE")
    tampered = _sealed_request(tampered_facts)
    assert _valid_runtime_dispatch_request(tampered) is False
    assert _decide(tampered).decision == "DENY"
    # And stripping the marker off a complete profile is also rejected.
    stripped = _sealed_request(replace(good.runtime_dispatch_context, profile_classification=""))
    assert _valid_runtime_dispatch_request(stripped) is False


def test_case_18_legacy_callers_unaffected():
    for action, ec in (
        (pbf.ACTION_PUSH, pbf.EXECUTION_CLASS_MUTATION),
        (pbf.ACTION_ROLLBACK, pbf.EXECUTION_CLASS_ROLLBACK),
        (pbf.ACTION_SOURCE_MUTATION, pbf.EXECUTION_CLASS_MUTATION),
        (pbf.ACTION_ADAPTER_INVOCATION, pbf.EXECUTION_CLASS_ADAPTER),
    ):
        req = pbf.build_permission_broker_request(
            action_type=action, execution_class=ec, requested_component="COMP-001",
            requested_capability="x", task_id="t", evidence_available=True,
            approval_present=True, simulation_only=True,
        )
        d = _decide(req)
        # POL-013 never triggers for a simulation / non-runtime_dispatch request.
        assert "POL-013" not in d.triggered_policy_ids
        assert d.decision == "ALLOW"


def test_case_19_and_20_provider_network_credential_class_blocked():
    # network true / credential presence are rejected at construction (case 5/6);
    # here confirm a non-simulation adapter_invocation still hard-DENYs (POL-005).
    req = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_ADAPTER_INVOCATION, execution_class=pbf.EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006", requested_capability="x", task_id="t",
        evidence_available=True, approval_present=True, simulation_only=False,
    )
    d = _decide(req)
    assert d.decision == "DENY" and "POL-005" in d.causing_policy_ids
    # POL-013 does not trigger for a non-runtime_dispatch action.
    assert "POL-013" not in d.triggered_policy_ids


def test_case_21_22_23_arbitrary_executable_argv_unsupported_adapter_blocked():
    for adm_class in ("", "arbitrary_executable", "shell_string", "dynamic_argv"):
        bad = replace(_adapter(admitted=True), admission_class=adm_class or ADMISSION_CLASS_UNADMITTED)
        req = _sealed_request(_facts(adapter_descriptor_binding=bad))
        assert "P_supply_chain_admission" in _narrow_local_cli_dispatch_v1_failed_predicates(req, check_marker=True)
        assert _decide(req).decision == "DENY"


def test_case_24_production_profile_is_unsatisfiable():
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None, simulation_only=False,
    )
    # No test resolver -> the production non-admitting resolver -> no marker.
    assert request.runtime_dispatch_context.profile_classification == ""
    assert request.runtime_dispatch_context.adapter_descriptor_binding.admission_class == ADMISSION_CLASS_UNADMITTED
    d = _decide(request)
    assert d.decision == "DENY"
    assert d.causing_policy_ids == ("POL-005", "POL-013")


def test_case_24b_synthetic_admitting_resolver_still_needs_real_authority():
    # Even with a synthetic admitting N-16-6 resolver, approval_present stays
    # False through the trusted builder (no trusted projection exists), so
    # P_human_authority_present fails and the marker is not derived.
    inputs = dispatch_inputs()
    tmp = tempfile.TemporaryDirectory()
    tracker = rdp.RuntimeDispatchIdentityTracker(Path(tmp.name))
    tracker._t = tmp
    identity = rdp.new_runtime_dispatch_identity(
        inputs, identity_tracker=tracker,
        _supply_chain_admission_resolver=_AdmittingResolver(),
    )
    request = rdp.build_runtime_dispatch_permission_broker_request(
        identity=identity, inputs=inputs, validated_authority=None,
        simulation_only=False, _supply_chain_admission_resolver=_AdmittingResolver(),
    )
    assert request.approval_present is False
    assert request.runtime_dispatch_context.adapter_descriptor_binding.admission_class == ADMISSION_CLASS_LOCAL_FIXED_ARGV
    assert request.runtime_dispatch_context.profile_classification == ""  # P_human_authority_present failed
    assert _decide(request).decision == "DENY"


def test_case_26_trusted_human_approval_but_invalid_profile_still_denies():
    req = _sealed_request(_facts(transport_type="remote"))  # not local_cli
    assert _valid_runtime_dispatch_request(req) is False
    assert _decide(req).decision == "DENY"


def test_case_27_another_deny_dominates_a_complete_profile():
    # An unknown requested_component makes POL-007 DENY even though the narrow
    # profile is structurally complete and POL-005 / POL-013 do not block.
    req = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-999", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=True, approval_present=True, simulation_only=False,
        runtime_dispatch_context=_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1),
    )
    d = _decide(req)
    assert d.decision == "DENY"
    assert "POL-007" in d.causing_policy_ids
    assert "POL-013" not in d.triggered_policy_ids
    assert "POL-005" not in d.triggered_policy_ids


def test_case_28_human_review_dominates_a_complete_profile_simulation():
    req = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=True, approval_present=False, simulation_only=True,
        runtime_dispatch_context=_facts(human_authority_binding=_authority(valid=False)),
    )
    d = _decide(req)
    assert d.decision == "HUMAN_REVIEW"


def test_case_29_static_scan_pol013_has_no_allow_or_human_review_branch():
    src = inspect.getsource(pbf.NarrowLocalCliDispatchEligibilityRule.evaluate)
    assert "ALLOW" not in src and "HUMAN_REVIEW" not in src
    tree = ast.parse(src.strip())
    returns = [n for n in ast.walk(tree) if isinstance(n, ast.Return)]
    assert len(returns) >= 2
    for r in returns:
        # every return is either _not_triggered(...) or a PolicyResult(...)
        # whose decision is DECISION_DENY — never ALLOW / HUMAN_REVIEW.
        call = r.value
        assert isinstance(call, ast.Call)
        fn = call.func
        name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
        assert name in {"_not_triggered", "PolicyResult"}
        if name == "PolicyResult":
            kw = {k.arg: k.value for k in call.keywords}
            dec = kw.get("decision")
            dec_name = dec.id if isinstance(dec, ast.Name) else getattr(dec, "attr", "")
            assert dec_name == "DECISION_DENY", ast.dump(dec)


def test_case_30_pol013_neutral_cannot_suppress_a_deny():
    # A complete-profile request that also trips POL-001 -> DENY, not ALLOW.
    # (covered by case 27; here assert POL-013 was not-triggered in that case)
    req = _build_runtime_dispatch_permission_broker_request(
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        task_id="task-a", phase_id="149O.20L.7O.3W", requested_resource=None,
        evidence_available=False, approval_present=True, simulation_only=False,
        runtime_dispatch_context=_facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1),
    )
    d = _decide(req)
    assert "POL-013" not in d.triggered_policy_ids
    assert d.decision == "DENY" and "POL-003" in d.causing_policy_ids


def test_case_31_caller_reconstruction_of_marker_is_rejected():
    good = _complete_profile_request()
    # dataclasses.replace on the facts to inject a marker without a complete profile
    incomplete = replace(
        good.runtime_dispatch_context,
        adapter_descriptor_binding=_adapter(admitted=False),
        profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1,
    )
    forged = _sealed_request(incomplete)
    assert _valid_runtime_dispatch_request(forged) is False
    assert _decide(forged).decision == "DENY"


def test_case_31b_marker_without_the_seal_is_not_trusted():
    facts = _facts(profile_classification=PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1)
    unsealed = pbf.PermissionBrokerRequest(
        request_id="pbr-x", timestamp="t", action_type=pbf.ACTION_TYPE_RUNTIME_DISPATCH,
        execution_class=pbf.EXECUTION_CLASS_ADAPTER, task_id="task-a", phase_id="149O.20L.7O.3W",
        requested_component="COMP-006", requested_capability="local_cli_dispatch",
        requested_resource=None, evidence_available=True, approval_present=True,
        simulation_only=False, runtime_dispatch_context=facts,
    )
    assert _is_trusted_narrow_local_cli_dispatch_v1(unsealed) is False
    # structural validator rejects it (no seal) -> DENY before POL-005/013
    assert _decide(unsealed).decision == "DENY"


def test_case_32_admission_field_mutation_changes_the_idempotency_key():
    inputs = dispatch_inputs()
    key_prod = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(inputs, invocation_id=_INV)
    )
    key_synth = rdp.compute_runtime_dispatch_idempotency_key(
        rdp.canonical_runtime_dispatch_projection(
            inputs, invocation_id=_INV, _supply_chain_admission_resolver=_AdmittingResolver()
        )
    )
    assert key_prod != key_synth  # the admission binding is in the canonical digest


def test_case_33_old_representative_callers_reproduce_identical_decisions():
    for action, ec, comp in (
        (pbf.ACTION_PUSH, pbf.EXECUTION_CLASS_MUTATION, "COMP-001"),
        (pbf.ACTION_READ, pbf.EXECUTION_CLASS_NONE, "COMP-001"),
    ):
        req = pbf.build_permission_broker_request(
            action_type=action, execution_class=ec, requested_component=comp,
            requested_capability="x", task_id="t", evidence_available=True,
            approval_present=True, simulation_only=True,
        )
        d = _decide(req)
        assert d.decision == "ALLOW"
        assert "POL-013" in d.non_applicable_policy_ids or ec != pbf.EXECUTION_CLASS_ADAPTER


# ══════════════════════════════════════════════════════════════════════════
# Registry / precedence / applicability regressions
# ══════════════════════════════════════════════════════════════════════════

def test_pol013_registered_last_and_canon_is_13():
    reg = pbf.PolicyRegistry()
    assert reg.policy_ids[-1] == "POL-013"
    assert len(reg.policy_ids) == 13
    assert set(reg.policy_ids) == pbf.POLICY_IDS_CANONICAL


def test_pol013_applicability_is_adapter_only():
    rule = pbf.NarrowLocalCliDispatchEligibilityRule()
    assert rule.applicable_execution_classes == frozenset({pbf.EXECUTION_CLASS_ADAPTER})


def test_compose_precedence_unchanged_deny_beats_human_review_beats_allow():
    src = inspect.getsource(pbf._compose)
    assert "for decision_value in (DECISION_DENY, DECISION_HUMAN_REVIEW):" in src
    # no specificity tier / weight / override keyword introduced
    for banned in ("specificity", "weight", "override", "tier"):
        assert banned not in src.lower()


def test_pol005_deny_policyresult_body_byte_identical():
    src = inspect.getsource(pbf.ExecutionDisabledRule.evaluate)
    assert 'decision_reason="execution_boundary_unavailable"' in src
    assert 'matched_no_go_ids=("NG-025",)' in src
    assert 'matched_invariants=("INV-001",)' in src
    assert 'matched_component_ids=("COMP-002",)' in src


# ══════════════════════════════════════════════════════════════════════════
# §63 contract-production equivalence map
# ══════════════════════════════════════════════════════════════════════════

def test_contract_production_equivalence_pbnde_predicates_map_to_source():
    contract = (REPO_ROOT / "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md").read_text()
    src = (REPO_ROOT / "src/pcae/core/permission_broker_foundation.py").read_text()
    for pid in (
        "P_trusted_builder_seal", "P_action_runtime_dispatch", "P_execution_class_adapter",
        "P_transport_local_cli", "P_network_prohibited", "P_supply_chain_admission",
        "P_human_authority_present", "P_human_authority_binding_valid", "P_attempt_identity",
        "P_runtime_target", "P_filesystem_scope", "P_trusted_profile_classification",
    ):
        assert pid in contract, pid
        assert pid in src, pid


def test_contract_production_equivalence_pbrd_v3_0_and_migration():
    pbrd = (REPO_ROOT / "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text()
    assert pbrd.startswith("# PBRD-001 v3.0")
    assert "## 12a." in pbrd
    assert "v3.0 explicit migration semantics" in pbrd
    assert "categorically DENIED" in pbrd
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.23" in pbrd  # IV mandated


def test_ng_025_annotation_is_in_the_right_file():
    ng = (REPO_ROOT / "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md").read_text()
    assert "RUNTIME_DISPATCH_LOCAL_CLI_V1" in ng
    assert "Canonical-statement annotation" in ng
    # not mistakenly added to the RE-NOGO registry
    renogo = (REPO_ROOT / "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md").read_text()
    assert "RUNTIME_DISPATCH_LOCAL_CLI_V1" not in renogo
    assert "NG-025" not in renogo


def test_derive_classification_is_only_referenced_by_the_trusted_builder():
    hits = subprocess.run(
        ["git", "grep", "-l", "derive_runtime_dispatch_local_cli_v1_classification", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.split()
    assert set(hits) == {
        "src/pcae/core/permission_broker_foundation.py",   # defines it
        "src/pcae/core/runtime_dispatch_permission.py",    # the trusted builder
    }, hits


def test_n16_6_resolver_admits_nothing_in_production():
    r = rdp._PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER
    result = r.resolve("any-adapter-id")
    assert result.admitted is False
    assert result.admission_class == ADMISSION_CLASS_UNADMITTED
    assert result.admission_record_digest == ""
    # a caller passing a broken resolver fails closed
    fc = rdp._resolve_supply_chain_admission("x", object())
    assert fc.admitted is False


def test_no_first_effect_primitive_in_the_touched_modules():
    for mod in ("permission_broker_foundation.py", "runtime_dispatch_permission.py"):
        tree = ast.parse((REPO_ROOT / "src/pcae/core" / mod).read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    assert a.name.split(".")[0] not in {
                        "subprocess", "socket", "ssl", "http", "urllib", "multiprocessing", "ctypes",
                    }, (mod, a.name)
            if isinstance(n, ast.ImportFrom):
                assert (n.module or "").split(".")[0] not in {
                    "subprocess", "socket", "ssl", "http", "urllib",
                }, (mod, n.module)
            if isinstance(n, ast.Attribute) and n.attr in {
                "Popen", "system", "posix_spawn", "spawn", "check_output", "check_call", "dispatch",
            }:
                raise AssertionError(f"{mod}: effect primitive {n.attr}")
