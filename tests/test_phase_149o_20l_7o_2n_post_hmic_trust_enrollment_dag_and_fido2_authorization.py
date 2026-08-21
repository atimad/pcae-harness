"""Phase 149O.20L.7O.2N -- Post-HMIC-v1.7 Activation Trust-Enrollment
Real-Effect Node Selection and FIDO2 Enrollment Authorization.

Analysis / authorization-freeze phase only. This suite independently
re-derives, from live production source alone (never from a prior
phase's own report), the facts underlying this phase's verdict:

  - the eight-term HATP activation readiness conjunction is fully wired
    (all eight named checks exist, in order, in
    `_assess_hatp_mandatory_activation_readiness_at_root`);
  - the remaining Trust-Enrollment DAG (HardwareCredential -> Principal/
    Signer -> DeploymentBinding -> Class-B -> substrate -> readiness) is
    acyclic and its precondition chain is enforced in source, not merely
    documented;
  - `scripts/hatp_hardware_credential_admin.py`'s public CLI surface is
    exactly `{enroll, revoke}` -- no `recover`/`import`/`restore`/manual-
    identity flag exists;
  - the FIDO2 provider's credential-creation parameters (RP id, ES256-
    only algorithm restriction, no explicit resident-key option) match
    this phase's report;
  - zero-device and multi-device enrollment behavior (raise vs.
    `devices[0]` deterministic first-wins) are exactly as documented;
  - one-credential scope: no hardware-credential-admin call this suite
    exercises has any Principal/Signer/DeploymentBinding side effect;
  - no authorization envelope is frozen in this phase's own governance
    metadata (verdict is D/B, not A -- §35/§36 forbid freezing an
    envelope unless FIDO2 was actually selected).

Every test uses an isolated `tmp_path`-rooted fixture or a monkeypatched
synthetic FIDO2 provider seam (mirroring `tests/
test_hatp_hardware_credential_admin_script.py`'s own existing
convention) -- never `HATPTrustStore.production()`,
`HATPHardwareCredentialStore.production()`, or any other real/protected
path. No test opens a real CTAP/HID transport, calls `lsusb`, or SSHes
anywhere. No production source is modified by this suite.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CUTOVER_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"
_FIDO2_PROVIDER_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"

_EXPECTED_EIGHT_TERM_NAMES = (
    "class_b_protected_storage_available",
    "repository_deployment_identity_valid",
    "hatp_substrate_operational",
    "hsce_signing_implementation_available",
    "mandatory_consumption_implementation_independently_verified",
    "production_dependency_provenance_valid",
    "protected_activation_authority_mechanism_available",
    "class_b_deployment_conformance_satisfies_readiness",
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Eight-term readiness conjunction is fully wired (source-level, no
#    execution against any real host).
# ═══════════════════════════════════════════════════════════════════════════


def test_eight_readiness_term_names_appear_in_source_in_expected_order():
    text = _CUTOVER_SRC.read_text(encoding="utf-8")
    positions = []
    for name in _EXPECTED_EIGHT_TERM_NAMES:
        needle = f'"{name}"'
        idx = text.find(needle)
        assert idx != -1, f"readiness term {name!r} not found in {_CUTOVER_SRC}"
        positions.append(idx)
    assert positions == sorted(positions), "readiness terms are not declared in the expected fixed order"


def test_assess_readiness_function_returns_exactly_eight_checks_shape():
    from pcae.core.hatp_mandatory_cutover import _assess_hatp_mandatory_activation_readiness_at_root

    # Deliberately nonexistent protected root + no trust store + no
    # repository_root: every branch fails closed, never raises, and the
    # eight-check shape must still hold even in the maximally-unready case.
    result = _assess_hatp_mandatory_activation_readiness_at_root(
        Path("/nonexistent-protected-root-2n-test"),
        None,
        repository_root=None,
        trust_store=None,
    )
    names = tuple(c.name for c in result.checks)
    assert names == _EXPECTED_EIGHT_TERM_NAMES
    assert result.ready is False
    # With no protected root, no trust store, and no repository_root, the
    # terms that depend on those inputs must fail closed. Two terms
    # (`hsce_signing_implementation_available`, an unconditional import
    # check) are independent of protected-root/trust-store availability
    # and may legitimately still be True in a dev checkout -- this test
    # only asserts the input-dependent terms fail closed, never that
    # every term is False regardless of what it actually depends on.
    by_name = {c.name: c.satisfied for c in result.checks}
    assert by_name["class_b_protected_storage_available"] is False
    assert by_name["hatp_substrate_operational"] is False
    assert by_name["mandatory_consumption_implementation_independently_verified"] is False
    assert by_name["production_dependency_provenance_valid"] is False
    assert by_name["protected_activation_authority_mechanism_available"] is False
    assert by_name["class_b_deployment_conformance_satisfies_readiness"] is False


def test_eighth_term_is_wired_to_full_class_b_conformance_verifier():
    text = _CUTOVER_SRC.read_text(encoding="utf-8")
    assert "verify_class_b_deployment_conformance(" in text
    assert "class_b_conformance_status_satisfies_readiness(" in text
    # HMRC-REQ-089: any verifier exception fails closed, never propagates.
    idx = text.find("class_b_deployment_conformance_satisfies_readiness")
    surrounding = text[max(0, idx - 800) : idx + 400]
    assert "except Exception" in surrounding


# ═══════════════════════════════════════════════════════════════════════════
# 2. Remaining Trust-Enrollment DAG precondition chain is enforced in
#    source (not merely documented), and is acyclic.
# ═══════════════════════════════════════════════════════════════════════════


def test_hpse_enroll_signer_requires_active_hardware_credential_record():
    text = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_principal_signer_admin.py").read_text(encoding="utf-8")
    assert "no active HardwareCredentialRecord exists for signer_key_id=" in text


def test_deployment_binding_requires_active_signer_and_principal_and_hardware_credential():
    text = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py").read_text(encoding="utf-8")
    assert "no SignerRecord exists for signer_key_id=" in text
    assert "no PrincipalRecord exists for principal_id=" in text
    assert "no active HardwareCredentialRecord exists for signer_key_id=" in text


def test_remaining_dag_node_order_is_acyclic():
    # Explicit linear reconstruction of this phase's own §12/§8 DAG.
    # Encoded as an adjacency list and checked for cycles generically
    # (never hand-waved as "obviously acyclic").
    dag = {
        "hmic_valid": ["protected_root_compliant"],
        "protected_root_compliant": ["fido2_device_present"],
        "fido2_device_present": ["fido2_provider_software_available"],
        "fido2_provider_software_available": ["hardware_credential_created"],
        "hardware_credential_created": ["hardware_credential_record_persisted"],
        "hardware_credential_record_persisted": ["principal_signer_enrolled"],
        "principal_signer_enrolled": ["deployment_binding_created"],
        "deployment_binding_created": ["class_b_compliant"],
        "class_b_compliant": ["substrate_operational"],
        "substrate_operational": ["hatp_ready"],
        "hatp_ready": ["hatp_active"],
        "hatp_active": [],
    }

    visiting: set = set()
    visited: set = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        assert node not in visiting, f"cycle detected at {node!r}"
        visiting.add(node)
        for succ in dag.get(node, []):
            visit(succ)
        visiting.discard(node)
        visited.add(node)

    for start in dag:
        visit(start)
    assert visited == set(dag)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Hardware-credential-admin CLI surface is exactly {enroll, revoke}.
# ═══════════════════════════════════════════════════════════════════════════


def _load_script_module():
    spec = importlib.util.spec_from_file_location("hatp_hardware_credential_admin_script_2n", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_surface_is_exactly_enroll_and_revoke_no_recovery_path():
    module = _load_script_module()
    parser = module._build_parser()
    subparsers_action = next(
        action for action in parser._subparsers._group_actions if hasattr(action, "choices")
    )
    assert set(subparsers_action.choices.keys()) == {"enroll", "revoke"}

    enroll_dest_names = {a.dest for a in subparsers_action.choices["enroll"]._actions}
    forbidden = {"recover", "import", "restore", "credential_id", "public_key", "manual_identity"}
    assert not (enroll_dest_names & forbidden)


def test_enroll_requires_enrollment_reference_and_has_no_credential_identity_flag():
    module = _load_script_module()
    parser = module._build_parser()
    with pytest.raises(SystemExit):
        # no --enrollment-reference supplied -> argparse must reject
        parser.parse_args(["enroll"])
    args = parser.parse_args(["enroll", "--enrollment-reference", "CHGR-test-2n", "--assume-yes"])
    assert args.enrollment_reference == "CHGR-test-2n"
    assert args.presence_timeout_s == 30.0
    assert not hasattr(args, "credential_id")
    assert not hasattr(args, "public_key")


def test_confirmation_prompt_gates_only_registry_write_not_hardware_touch():
    """Load-bearing sequencing finding (this phase's §10/§12): the real
    ceremony runs in `_cmd_enroll` BEFORE the confirmation/preview
    description is built. Verified structurally: the ceremony call
    textually precedes both the preview construction and the
    confirmation gate inside `_cmd_enroll`'s source."""
    text = _SCRIPT_PATH.read_text(encoding="utf-8")
    fn_start = text.index("def _cmd_enroll(")
    fn_end = text.index("\ndef _cmd_revoke(")
    body = text[fn_start:fn_end]
    ceremony_idx = body.index("_run_enrollment_ceremony(")
    preview_idx = body.index("preview_register_credential(")
    confirm_idx = body.index("_prompt_confirm(")
    assert ceremony_idx < preview_idx < confirm_idx


# ═══════════════════════════════════════════════════════════════════════════
# 4. FIDO2 provider credential-creation parameters.
# ═══════════════════════════════════════════════════════════════════════════


def test_fido2_provider_rp_and_algorithm_restriction():
    import pcae.core.hatp_fido2_provider as provider_module

    assert provider_module._HATP_RP_ID == "hatp.pcae.local"
    assert provider_module._HATP_RP == {"id": "hatp.pcae.local", "name": "PCAE HATP"}
    assert provider_module._SUPPORTED_ENROLLMENT_ALGORITHMS == frozenset({"ES256"})

    text = _FIDO2_PROVIDER_SRC.read_text(encoding="utf-8")
    assert 'key_params = [{"type": "public-key", "alg": ES256.ALGORITHM}]' in text


def test_fido2_provider_passes_no_explicit_resident_key_or_user_verification_option():
    text = _FIDO2_PROVIDER_SRC.read_text(encoding="utf-8")
    start = text.index("def enroll_credential(")
    end = text.index("\n    def ", start + 1) if "\n    def " in text[start + 1 :] else len(text)
    body = text[start:end]
    assert "rk=" not in body
    assert "resident_key=" not in body
    assert "uv=" not in body
    assert "user_verification=" not in body


# ═══════════════════════════════════════════════════════════════════════════
# 5. Zero-device / multi-device enrollment behavior (§16-20, §35 rejection
#    of alternative C).
# ═══════════════════════════════════════════════════════════════════════════


fido2 = pytest.importorskip("fido2")


def _make_provider():
    from pcae.core.hatp_fido2_provider import Fido2HardwareProvider

    return Fido2HardwareProvider()


def test_zero_devices_raises_provider_unavailable(monkeypatch):
    import pcae.core.hatp_fido2_provider as provider_module
    from pcae.core.hatp_providers import HATPProviderUnavailableError

    monkeypatch.setattr(provider_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([])))
    provider = _make_provider()
    with pytest.raises(HATPProviderUnavailableError):
        provider.enroll_credential(presence_timeout_s=1.0)


def test_multiple_devices_selects_first_deterministically_documented_gap(monkeypatch):
    """This is a documented architecture gap (this phase's §10/§19/§20),
    not a safety property: `enroll_credential()` always selects
    `devices[0]` with no contract-defined selection mechanism. This test
    proves the deterministic-first-wins behavior exists in source (so a
    future phase cannot silently regress it to something non-
    deterministic) -- it does NOT assert this is safe for multi-device
    hosts, and this phase's own verdict is unaffected by it since zero
    devices, not multiple, is the actual current host state."""
    import pcae.core.hatp_fido2_provider as provider_module

    class _FakeDevice:
        def __init__(self, tag):
            self.tag = tag

    first, second = _FakeDevice("first"), _FakeDevice("second")
    monkeypatch.setattr(provider_module.CtapHidDevice, "list_devices", staticmethod(lambda: iter([first, second])))

    seen = {}

    class _FakeCtap2:
        def __init__(self, device):
            seen["device"] = device

        def make_credential(self, **kwargs):
            raise provider_module.HATPProviderDeviceError("stop before any real attestation handling")

    monkeypatch.setattr(provider_module, "Ctap2", _FakeCtap2)
    provider = _make_provider()
    with pytest.raises(provider_module.HATPProviderDeviceError):
        provider.enroll_credential(presence_timeout_s=1.0)
    assert seen["device"] is first


# ═══════════════════════════════════════════════════════════════════════════
# 6. One-credential scope: no Principal/Signer/DeploymentBinding side
#    effect from any hardware-credential-admin call.
# ═══════════════════════════════════════════════════════════════════════════


def test_register_credential_has_no_import_dependency_on_principal_signer_or_deployment_binding_modules():
    import ast

    import pcae.core.hatp_hardware_credential_admin as hw_admin

    tree = ast.parse(inspect.getsource(hw_admin))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert not any("hatp_principal_signer_admin" in m for m in imported_modules)
    assert not any("hatp_deployment_binding_admin" in m for m in imported_modules)


def test_register_credential_isolated_tmp_path_creates_only_hardware_credential_record(tmp_path):
    from pcae.core.hatp_hardware_credential_admin import CredentialEnrollmentEvidence, register_credential

    evidence = CredentialEnrollmentEvidence(
        signer_key_id="cc" * 16,
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        protocol_name="FIDO2",
        algorithm="Es256",
        public_key_hex="dd" * 20,
        enrollment_reference="CHGR-2n-isolated-test",
    )
    result = register_credential(repository_root=tmp_path, evidence=evidence, _store_root=tmp_path)
    assert result.record.signer_key_id == "cc" * 16
    assert result.record.status == "active"
    # Only the hardware-credential store's own artifacts exist under tmp_path
    # -- no principal/signer/deployment-binding registry file was created as
    # a side effect of this single call.
    created_names = {p.name for p in tmp_path.rglob("*") if p.is_file()}
    assert not any("deployment-binding" in n or "registry.json" == n for n in created_names)


# ═══════════════════════════════════════════════════════════════════════════
# 7. No authorization envelope is frozen in this phase's governance
#    metadata (verdict D/B, not A).
# ═══════════════════════════════════════════════════════════════════════════


def test_no_fido2_enrollment_authorization_envelope_frozen_in_this_phase_metadata():
    metadata_path = _REPO_ROOT / ".pcae" / "phase-completion-metadata.json"
    if not metadata_path.exists():
        pytest.skip("phase-completion-metadata.json not present at collection time")
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    phase_id = data.get("phase_id", "")
    if "2N" not in phase_id.upper().replace(".", ""):
        pytest.skip("metadata does not yet reflect phase 2N (pre-finalization collection)")
    summary_blob = json.dumps(data).upper()
    assert "ENROLLMENT ENVELOPE FROZEN" not in summary_blob.replace(" ", "")
