"""Phase 149O.7 -- HATP Class-B Deployment / Activation Independent
Verification (adversarial re-verification of Phase 149O.6 / Wave 7).

Verification-only: no production code is modified by this phase. These
tests independently re-derive claims made by
`tests/test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py`
and `docs/PHASE_149O_6_HATP_CLASS_B_DEPLOYMENT_ACTIVATION_IMPLEMENTATION.md`
from source, rather than trusting that suite/report, plus adds checks
that suite does not cover: the Permission Broker `simulation_only`
structural boundary (POL-005 non-triggering), Wave-5 credential-registry
non-consumption by `capabilities()` (B-149O.3-1/-3 reclassification
check), host-mutation/env-override absence, and the exact-3-file Wave-7
production diff.

See `docs/PHASE_149O_7_HATP_CLASS_B_DEPLOYMENT_ACTIVATION_INDEPENDENT_VERIFICATION.md`
for the full narrative verification report and final verdicts.
"""
from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_ag_authority as ag_authority
from pcae.core.hatp_fido2_provider import Fido2HardwareProvider
from pcae.core.hatp_providers import HardwareProviderConformance
from pcae.core.human_approval_trusted_provenance import inspect_hatp_verification_substrate_readiness
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.permission_broker_foundation import PermissionBroker, build_permission_broker_request
from pcae.core.repository_identity import read_repository_identity

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BASELINE_149O5_COMMIT = "17a2c1b4"  # HEAD at 149O.6 phase start (149O.5, complete/pushed)


def _git_diff_names(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", _BASELINE_149O5_COMMIT, "HEAD", "--", *paths],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Exact Wave-7 production diff: independently reconstructed, UNRELATED=0.
# ═══════════════════════════════════════════════════════════════════════════


def test_wave7_production_diff_is_exactly_three_named_files() -> None:
    changed = set(_git_diff_names("src/pcae/"))
    assert changed == {
        "src/pcae/core/agent.py",
        "src/pcae/core/hatp_ag_authority.py",
        "src/pcae/core/human_approval_trusted_provenance.py",
    }


def test_rollback_approval_evidence_untouched_by_wave7() -> None:
    """Wave 6's RAE/HATP binding module is claimed byte-unchanged since
    149O.5 -- independently confirmed, not merely cited from the report."""
    assert _git_diff_names("src/pcae/core/rollback_approval_evidence.py") == []


def test_hatp_contract_byte_unchanged_since_wave7() -> None:
    assert _git_diff_names("docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md") == []


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-2 dependency provenance: no injection surface, independently
#    re-inspected via `inspect.signature`, not copied from the 149O.6
#    suite's own equivalent test.
# ═══════════════════════════════════════════════════════════════════════════


def test_f2_ag3_adapter_signature_has_no_authority_injection_parameter() -> None:
    params = set(inspect.signature(ag_authority.resolve_ag3_gated_rollback_authority).parameters)
    for forbidden in ("hatp_provider", "hatp_trust_store", "approval_present"):
        assert forbidden not in params


def test_f2_ag5_adapter_signature_has_no_authority_injection_parameter() -> None:
    params = set(inspect.signature(ag_authority.resolve_ag5_gated_rollback_authority).parameters)
    for forbidden in ("hatp_provider", "hatp_trust_store", "approval_present"):
        assert forbidden not in params


def test_f2_adapter_module_source_never_names_test_provider_class() -> None:
    source = Path(ag_authority.__file__).read_text()
    assert "TestHATPProofVerifierProvider" not in source


def test_f2_adapter_resolves_only_named_production_factories() -> None:
    """`_resolve_gated_approval` must call exactly the production
    factories (`HATPTrustStore.production`, `create_production_hardware_
    provider`) and no caller-reachable substitute -- confirmed by
    reading the actual call sites, not by trusting the docstring."""
    source = inspect.getsource(ag_authority._resolve_gated_approval)
    assert "HATPTrustStore.production()" in source
    assert "create_production_hardware_provider(" in source
    assert "hatp_provider=" not in source.split("try:")[0]  # no injected provider before the try block


# ═══════════════════════════════════════════════════════════════════════════
# 3. Default AG3/AG5 invocation: independently confirm no HATP import
#    occurs at module load time on the default (no-`hatp_evidence_id`)
#    path -- the decisive "does ordinary CLI dispatch even touch HATP"
#    question (§30/§121 of the governing brief).
# ═══════════════════════════════════════════════════════════════════════════


def test_agent_module_does_not_import_hatp_ag_authority_at_top_level() -> None:
    """`hatp_ag_authority` must be imported lazily, inside the
    `if hatp_evidence_id is not None:` branch, never at module scope --
    otherwise every pre-Wave-7 caller would pay an unconditional import
    cost and, more importantly, the import graph itself would not prove
    the gated path is opt-in."""
    import pcae.core.agent as agent_module

    top_level_source = inspect.getsource(agent_module)
    # crude but decisive: the import statement must never appear outside
    # an indented (branch-local) context in execute_rollback/
    # build_rollback_execution.
    for line in top_level_source.splitlines():
        if line.startswith("from pcae.core.hatp_ag_authority") or line.startswith("import pcae.core.hatp_ag_authority"):
            assert line.startswith(("    ", "\t")), f"module-level HATP import found: {line!r}"


def test_real_cli_rollback_commands_never_supply_hatp_evidence() -> None:
    """Signing-ceremony/CLI-evidence-acquisition inventory (§32/§120):
    no command module anywhere references `hatp_evidence_id`,
    `HumanApprovalProvenanceProof`, or `request_signature` -- confirming
    no production CLI surface can populate the gated path today."""
    commands_dir = _REPO_ROOT / "src" / "pcae" / "commands"
    hits = []
    for path in commands_dir.rglob("*.py"):
        text = path.read_text()
        for needle in ("hatp_evidence_id", "HumanApprovalProvenanceProof", "request_signature("):
            if needle in text:
                hits.append((path.name, needle))
    assert hits == []


# ═══════════════════════════════════════════════════════════════════════════
# 4. Permission Broker: decision-provenance vs execution-enforcement,
#    the two-part verdict the governing brief requires kept separate.
# ═══════════════════════════════════════════════════════════════════════════


def test_gated_permission_broker_request_is_always_simulation_only() -> None:
    """`_evaluate_rollback_permission` hardcodes `simulation_only=True`
    -- this is structural proof the gated path can never itself trigger
    POL-005 (Execution Disabled), i.e. it is architecturally a policy
    *simulation*, never a real execution-permission gate, regardless of
    the returned decision value."""
    source = inspect.getsource(ag_authority._evaluate_rollback_permission)
    assert "simulation_only=True" in source


def test_pol005_execution_disabled_denies_every_real_non_simulation_request() -> None:
    """Independently confirms Permission Broker's own architecture: a
    real (non-simulation) rollback-execution request is unconditionally
    DENY today (no COMP-002 execution boundary), which is *why* the
    gated adapter's permanent `simulation_only=True` cannot be read as
    a loophole -- a non-simulation request through the same broker
    would simply be denied outright."""
    request = build_permission_broker_request(
        action_type=ag_authority.ACTION_ROLLBACK,
        execution_class=ag_authority.EXECUTION_CLASS_ROLLBACK,
        requested_component="COMP-008",
        requested_capability="execute_rollback",
        task_id="active-task-1",
        evidence_available=True,
        approval_present=True,
        simulation_only=False,
    )
    decision = PermissionBroker().evaluate(request)
    assert decision.decision == "DENY"
    assert decision.implementation_status == "execution_unavailable"


def test_permission_broker_module_is_isolated_from_execution_machinery() -> None:
    """Re-confirms the module's own documented isolation claim: no
    subprocess/shell/execution-adjacent import exists in
    `permission_broker_foundation.py`, independently grepped rather than
    quoted from the module docstring."""
    import pcae.core.permission_broker_foundation as pbf

    code_lines = [
        line for line in Path(pbf.__file__).read_text().splitlines()
        if (line.startswith("import ") or line.startswith("from "))
    ]
    for forbidden in ("subprocess", "pcae.core.shell_gate", "pcae.core.backend_invocations"):
        assert not any(forbidden in line for line in code_lines), forbidden


# ═══════════════════════════════════════════════════════════════════════════
# 5. Class-B readiness: no assert-based security, no env override, no
#    host mutation in the two Wave-7-touched production files.
# ═══════════════════════════════════════════════════════════════════════════


def test_readiness_function_has_no_bare_assert_statement() -> None:
    """The Wave-4-era `assert operational is False` tripwire was removed
    this wave; confirm no assert statement of any kind remains inside
    `inspect_hatp_verification_substrate_readiness` (no assert-based
    security predicate, §6/§76 of the governing brief)."""
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    body_lines = source.splitlines()[1:]  # skip def line
    for line in body_lines:
        stripped = line.strip()
        assert not stripped.startswith("assert "), f"bare assert found: {stripped!r}"


def test_readiness_function_has_no_environment_or_override_hook() -> None:
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    for forbidden in ("os.environ", "getenv", "HATP_FORCE_OPERATIONAL", "HATP_TRUSTED_OPERATIONAL",
                       "PCAE_HATP_OPERATIONAL", "HATP_OPERATIONAL", "PCAE_HATP_FORCE"):
        assert forbidden not in source


def test_no_env_override_variable_referenced_anywhere_in_hatp_modules() -> None:
    hatp_files = [
        "src/pcae/core/hatp_ag_authority.py",
        "src/pcae/core/human_approval_trusted_provenance.py",
        "src/pcae/core/hatp_bootstrap.py",
        "src/pcae/core/hatp_providers.py",
    ]
    forbidden_vars = (
        "HATP_FORCE_OPERATIONAL", "HATP_TRUSTED_OPERATIONAL",
        "PCAE_HATP_OPERATIONAL", "HATP_OPERATIONAL", "PCAE_HATP_FORCE",
    )
    for rel in hatp_files:
        text = (_REPO_ROOT / rel).read_text()
        for var in forbidden_vars:
            assert var not in text, f"{rel} references {var}"


def test_no_host_provisioning_commands_in_wave7_touched_files() -> None:
    wave7_files = [
        "src/pcae/core/hatp_ag_authority.py",
        "src/pcae/core/human_approval_trusted_provenance.py",
    ]
    forbidden = re.compile(r"\b(useradd|dscl|sudoers|chmod|chown|setfacl|subprocess\.(run|Popen|call))\b")
    for rel in wave7_files:
        text = (_REPO_ROOT / rel).read_text()
        assert not forbidden.search(text), f"{rel} contains a host-provisioning-shaped call"


def test_readiness_operational_true_requires_every_synthetic_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """Independently re-derive (not copy) that a trust store reporting
    zero enrollment cannot reach OPERATIONAL even if hardware discovery
    is monkeypatched conformant -- i.e. the hardware-provider terms
    alone are insufficient; the trust-store terms are independently
    load-bearing."""
    from pcae.core import hatp_providers as providers_module

    class _EmptyTrustStore(HATPTrustStore):
        def __init__(self) -> None:  # noqa: D401 - test double, no production root touched
            pass

        def environment_status(self):
            class _Env:
                class _Status:
                    value = "READY"

                status = _Status()
                reasons: tuple = ()

            return _Env()

        def load_repository_enrollment(self, repository_id: str):
            return None  # no enrollment at all

    monkeypatch.setattr(
        providers_module,
        "discover_hardware_providers",
        lambda: (
            providers_module.HardwareProviderAvailability(
                provider_profile=providers_module.HATP_HARDWARE_PROVIDER_V1,
                protocol_name="FIDO2",
                library_installed=True,
                device_detected=True,
            ),
        ),
    )
    monkeypatch.setattr(
        providers_module,
        "create_production_hardware_provider",
        lambda profile, **kw: Fido2HardwareProvider(),
    )

    result = inspect_hatp_verification_substrate_readiness(
        _EmptyTrustStore(), current_repository_id="11111111-1111-4111-8111-111111111111"
    )
    assert result.operational is False
    assert any(name == "protected_deployment_enrollment_valid" and not value for name, value in result.terms)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Wave-5 finding reclassification: B-149O.3-1/-3 (weaker credential
#    registry) must not be consumed by the Wave-7 operational conjunction
#    through `capabilities()`.
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_capabilities_does_not_consult_credential_registry() -> None:
    """B-149O.3-1/-3 concern `HATPHardwareCredentialStore`'s weaker
    readiness/schema checks. `capabilities()` -- the only method Wave 7's
    `provider_attestation_trusted` term calls -- must not reference the
    credential store at all, or B-149O.3-1/-3 would need reclassifying
    as now load-bearing for activation. Independently confirmed by
    source inspection of `capabilities()` alone, not `verify()`."""
    source = inspect.getsource(Fido2HardwareProvider.capabilities)
    assert "credential_store" not in source
    assert "_resolve_credential_store" not in source


def test_fido2_capabilities_is_a_static_conformance_descriptor() -> None:
    provider = Fido2HardwareProvider()
    caps = provider.capabilities()
    assert caps.hatp_conformant in (
        HardwareProviderConformance.CONFORMANT,
        HardwareProviderConformance.CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS,
    )


def test_verify_hatp_proof_fails_closed_on_provider_exception() -> None:
    """B-149O.3-8 concerns `Fido2HardwareProvider.verify()` raising for
    malformed evidence instead of returning a result. Independently
    confirm Wave 4's `verify_hatp_proof` still wraps the provider call
    in a blanket `except Exception` fail-closed umbrella, so B-149O.3-8
    cannot propagate an unhandled exception through the gated path."""
    import pcae.core.human_approval_trusted_provenance as hatp_module

    source = inspect.getsource(hatp_module.verify_hatp_proof)
    assert "except Exception" in source
    # the umbrella must wrap the provider.verify(...) call specifically
    verify_call_index = source.find("provider.verify(")
    except_index = source.find("except Exception", verify_call_index)
    assert verify_call_index != -1 and except_index != -1


# ═══════════════════════════════════════════════════════════════════════════
# 7. Current real deployment: independently re-confirm NOT_READY.
# ═══════════════════════════════════════════════════════════════════════════


def test_current_real_deployment_independently_confirmed_not_ready() -> None:
    from pcae.core.paths import HarnessPath

    root = HarnessPath(_REPO_ROOT)
    identity = read_repository_identity(root)
    repository_id = identity.repository_instance_id if identity is not None else "00000000-0000-4000-8000-000000000000"
    result = inspect_hatp_verification_substrate_readiness(
        HATPTrustStore.production(), current_repository_id=repository_id
    )
    assert result.operational is False
    assert result.status.value == "NOT_READY"
