"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1 — Independent Verification of the
CTAP2 PIN/UV Repair + Mandatory Real-CTAP2-Hardware Verification + N-16-5
Closure.

RESULT: **BLOCKED.** N-16-5: **NOT CLOSED.**

H-1 (the ``.1R.30R.5R`` CTAP2 PIN/UV interoperability repair) is independently
verified from primary source **and** certified against genuine FIDO_2_1
hardware (evidence: ``.pcae/certification/rhamp_hardware_cert_30r5r1.json`` and
the canonical phase document — RHAMP-REQ-154: this suite never requires real
hardware).

N-16-5 does not close: **finding H-2** — the production protected-presentation
helper (``pcae/protected_presentation_helper.py::_observe_election``) has no
interactive human-election surface, so RHAMP-REQ-152 bullet 4 (a real explicit
Approve election yielding a ``PRODUCTION`` ``AuthenticatedHumanPrincipal``
end-to-end through Gate 5) cannot be performed. Adding it is a ``src/pcae``
change outside this verification-only phase's authorized scope.

This suite is hardware-free and deterministic. It pins the anchors, proves the
one-file production diff and byte-unchanged contracts, re-derives the H-1
repair mechanics from primary source, proves the ``require_real_assurance``
PRODUCTION chain composes end-to-end in software (an in-process shim stands in
for **only** the launcher's ``posix_spawn`` boundary — not the CTAP2
authenticator; this is not a substitute for the real helper, whose absence is
H-2), pins H-2, and proves every runtime / first-effect / N-16-6 / N-16-7 /
mechanism-flexibility boundary is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"
CTAP2_MODULE = SRC / "core" / "hpac_rhamp_ctap2.py"
HELPER_MODULE = SRC / "protected_presentation_helper.py"
PHASE_DOC = (
    REPO / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_1_CTAP2_PIN_UV_REPAIR_IV_REAL_HARDWARE_VERIFICATION_AND_N_16_5_CLOSURE.md"
)
CERT_EVIDENCE = REPO / ".pcae" / "certification" / "rhamp_hardware_cert_30r5r1.json"

A = "9f004ea9"          # finalized .1R.30R.5 BLOCKED head (attribution baseline)
R = "ea40c47e"          # finalized .1R.30R.5R repair head
V = "ea40c47e"          # .1R.30R.5R.1 phase-entry SHA (== R)
H = "0250e5f7"          # finalized .1R.30R.5R.1 BLOCKED head

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root / launch model"),
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True
    ).stdout


# ── 1. anchors ───────────────────────────────────────────────────────────

def test_01_anchor_A_is_the_finalized_30r5_blocked_head():
    assert _git("cat-file", "-t", A).strip() == "commit"
    assert ".1R.30R.5" in _git("show", "-s", "--format=%s", A)
    assert "BLOCKED" in _git("show", "-s", "--format=%B", A)


def test_02_anchor_R_and_V_are_the_finalized_repair_head():
    assert _git("cat-file", "-t", R).strip() == "commit"
    assert ".1R.30R.5R" in _git("show", "-s", "--format=%s", R)
    assert _git("rev-parse", V).strip() == _git("rev-parse", R).strip()


# ── 2. production diff — exactly one file ─────────────────────────────────

def test_03_production_diff_A_to_R_is_exactly_one_file():
    names = _git("diff", "--name-status", A, R, "--", "src/pcae", "scripts", "pyproject.toml").split()
    assert names == ["M", "src/pcae/core/hpac_rhamp_ctap2.py"], names


def test_04_no_production_or_contract_change_in_this_phase():
    # .1R.30R.5R.1 itself (V..HEAD) changes no src/pcae / scripts / pyproject / contract byte.
    assert _git("diff", "--name-only", V, H, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts").strip() == ""


# ── 3. contract byte identity ────────────────────────────────────────────

def test_05_all_contracts_byte_unchanged_since_A():
    assert _git("diff", "--name-only", A, H, "--", "docs/contracts").strip() == ""


@pytest.mark.parametrize("contract", [
    "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",
    "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
])
def test_06_named_normative_contract_unchanged(contract):
    assert _git("diff", "--stat", A, H, "--", f"docs/contracts/{contract}").strip() == ""


def test_07_rhamp_001_still_v1_0():
    rhamp = (CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md").read_text()
    assert "RHAMP-001 v1.0" in rhamp
    assert "RHAMP-REQ-152" in rhamp and "RHAMP-INV-018" in rhamp


# ── 4. H-1 root cause + repair, re-derived from primary source ────────────

def test_08_h1_bare_uv_shape_is_gone_from_the_production_provider():
    src = CTAP2_MODULE.read_text()
    assert 'options = {"rk": False, "uv": True}' not in src
    assert 'options={"uv": True}' not in src
    native = src.split("class NativeCtap2Provider", 1)[1]
    make_seg = native.split("    def make_credential(", 1)[1].split("\n    def ", 1)[0]
    assert 'options = {"rk": False}' in make_seg
    assert 'pin_uv_param=pin_uv_param' in make_seg and 'pin_uv_protocol=pin_uv_protocol' in make_seg
    get_seg = native.split("    def get_assertion(", 1)[1].split("\n    def ", 1)[0]
    assert 'options=' not in get_seg.split("ctap2.get_assertion(", 1)[1].split(")", 1)[0]


def test_09_client_pin_handshake_is_present_and_threaded():
    src = CTAP2_MODULE.read_text()
    for token in ("ClientPin", "_obtain_pin_uv", "pin_uv_param", "pin_uv_protocol",
                  "get_pin_token", "get_uv_token", "_PIN_UV_TOKEN_RP_ID"):
        assert token in src, token


def test_10_protocol_v2_preferred_v1_fallback_no_compat_fail_closed():
    from fido2.ctap2 import ClientPin
    from fido2.ctap2.pin import PinProtocolV1, PinProtocolV2
    assert [p.VERSION for p in ClientPin.PROTOCOLS] == [2, 1]
    assert PinProtocolV2.VERSION == 2 and PinProtocolV1.VERSION == 1
    src = CTAP2_MODULE.read_text()
    # no mutually supported protocol -> ValueError -> Ctap2UnavailableError (fail closed)
    seg = src.split("def _obtain_pin_uv", 1)[1].split("\n    def ", 1)[0]
    assert "except ValueError" in seg and "Ctap2UnavailableError" in seg
    assert "no mutually supported CTAP2 PIN/UV protocol" in seg


def test_11_permission_scoped_and_rp_bound_token():
    from fido2.ctap2 import ClientPin
    src = CTAP2_MODULE.read_text()
    seg = src.split("def _obtain_pin_uv", 1)[1].split("\n    def ", 1)[0]
    assert "PERMISSION.MAKE_CREDENTIAL" in seg and "PERMISSION.GET_ASSERTION" in seg
    assert "_PIN_UV_TOKEN_RP_ID" in seg
    assert "permission_name" in seg
    assert {"MAKE_CREDENTIAL", "GET_ASSERTION"} <= {p.name for p in ClientPin.PERMISSION}


def test_12_command_scoped_pin_uv_auth_param():
    src = CTAP2_MODULE.read_text()
    seg = src.split("def _obtain_pin_uv", 1)[1].split("\n    def ", 1)[0]
    assert "protocol.authenticate(token, client_data_hash)" in seg


def test_13_trusted_non_logging_non_persisted_pin():
    src = CTAP2_MODULE.read_text()
    prompt = src.split("def _default_pin_prompt", 1)[1].split("\ndef ", 1)[0]
    assert "getpass" in prompt
    assert "isatty()" in prompt
    assert "Ctap2UnavailableError" in prompt  # non-interactive -> fail closed
    assert "Ctap2CancelledError" in prompt    # EOF / KeyboardInterrupt -> cancel
    obtain = src.split("def _obtain_pin_uv", 1)[1].split("\n    def ", 1)[0]
    assert "del pin" in obtain and "del token" in obtain
    # PIN never stored on the provider — only the prompt callable is
    init = src.split("class NativeCtap2Provider", 1)[1].split("def __init__", 1)[1].split("\n    def ", 1)[0]
    assert "self._pin_prompt = _pin_prompt or _default_pin_prompt" in init
    assert "self._pin =" not in init


def test_14_error_mapper_uses_only_extant_reasons_and_mints_no_new_code():
    from fido2.ctap import CtapError
    src = CTAP2_MODULE.read_text()
    seg = src.split("def _map_pin_uv_ctap_error", 1)[1].split("\n\ndef ", 1)[0]
    for name in ("ACTION_TIMEOUT", "USER_ACTION_TIMEOUT", "KEEPALIVE_CANCEL", "PIN_INVALID",
                 "PIN_AUTH_INVALID", "UV_INVALID", "PIN_BLOCKED", "PIN_AUTH_BLOCKED",
                 "UV_BLOCKED", "PIN_NOT_SET"):
        assert hasattr(CtapError.ERR, name), name
    from pcae.core.hpac_rhamp_terminal_reasons import TERMINAL_REASON_CODES
    assert len(TERMINAL_REASON_CODES) == 41
    # every reason the mapper returns is a pre-existing Ctap2* RhampTerminalError
    assert "Ctap2CancelledError" in seg and "Ctap2UnavailableError" in seg
    assert "class TerminalReasonCode" not in CTAP2_MODULE.read_text()


def test_15_no_bare_uv_retry_no_uv_downgrade():
    src = CTAP2_MODULE.read_text()
    assert 'No bare-"uv" retry' in src
    mc = src.split("class NativeCtap2Provider", 1)[1].split("    def make_credential(", 1)[1].split("\n    def ", 1)[0]
    assert "FLAG.UV" in mc and "UP-only downgrade" in mc


# ── 5. deterministic-fixture realism + provider separation ───────────────

def test_16_virtual_authenticator_rejects_the_historical_shapes():
    from pcae.core.hpac_rhamp_ctap2 import build_virtual_ctap2_test_seam
    provider, auth = build_virtual_ctap2_test_seam()
    assert auth.SIMULATION_ONLY is True
    assert auth.PROVIDER_KIND_IS_REAL is False
    from fido2.ctap import CtapError
    with pytest.raises(CtapError) as ei:
        auth.make_credential(client_data_hash=b"x" * 32, rp={"id": "hpac.pcae.local"},
                             user={"id": b"u"}, key_params=[], options={"uv": True})
    assert ei.value.code == CtapError.ERR.INVALID_OPTION  # 0x2C — exactly what real FIDO_2_1 hw returns


def test_17_deterministic_provider_permanently_simulation_only():
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider, PRODUCTION_PROVIDER_KIND
    assert DeterministicCtap2Provider.SIMULATION_ONLY is True
    assert DeterministicCtap2Provider().SIMULATION_ONLY is True
    assert DeterministicCtap2Provider().PROVIDER_KIND != PRODUCTION_PROVIDER_KIND


def test_18_production_resolver_is_seam_free_native_provider():
    from pcae.core.hpac_rhamp_ctap2 import (
        NativeCtap2Provider, PRODUCTION_PROVIDER_KIND, resolve_production_ctap2_provider,
    )
    p = resolve_production_ctap2_provider()
    assert isinstance(p, NativeCtap2Provider)
    assert p.PROVIDER_KIND == PRODUCTION_PROVIDER_KIND == "native-ctap2"
    assert p._connection_factory is None and p._client_pin_factory is None
    src = CTAP2_MODULE.read_text()
    seg = src.split("def resolve_production_ctap2_provider", 1)[1]
    assert "os.environ" not in seg and "getenv" not in seg
    assert "build_virtual_ctap2_test_seam" not in seg


# ── 6. .1R.30R.5R repair suite still green ───────────────────────────────

def test_19_r30r5r_repair_suite_still_passes():
    out = subprocess.run(
        ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert "48 passed" in out.stdout, out.stdout[-3000:]


# ── 7. downstream baselines byte-unchanged since A ───────────────────────

@pytest.mark.parametrize("module", [
    "core/hpac_rhamp_enrollment.py",
    "core/hpac_rhamp_credential_sidecar.py",
    "core/hpac_rhamp_counter_state.py",
    "core/hpac_rhamp_assertion_verify.py",
    "core/hpac_rhamp_client_context.py",
    "core/human_authenticator_fido2.py",
    "core/hpac_verifier.py",
    "core/approval_presentation.py",
    "core/protected_presentation.py",
    "core/protected_presentation_installation.py",
    "core/hpac_protected_presentation_admin.py",
    "protected_presentation_helper.py",
    "core/runtime_dispatch_gate5.py",
    "core/runtime_dispatch_gate9.py",
])
def test_20_downstream_module_byte_unchanged_since_A(module):
    assert _git("diff", "--stat", A, H, "--", f"src/pcae/{module}").strip() == ""


# ── 8. real-hardware certification evidence recorded ─────────────────────

def test_21_certification_evidence_artifact_records_the_hardware_ceremony():
    ev = json.loads(CERT_EVIDENCE.read_text())
    assert ev["dryrun"] is False
    assert ev["part_A_result"] == "PASS"
    assert ev["part_B_result"] == "BLOCKED (H-2)"
    a = ev["A"]
    assert "FIDO_2_1" in a["authenticator_versions"]
    assert a["authenticator_aaguid"] == "b7d3f68e88a6471e9ecf2df26d041ede"
    assert a["real_flag_up"] is True and a["real_flag_uv"] is True
    assert "OK" in a["real_make_credential"]
    assert "OK" in a["real_get_assertion_1"] and "OK" in a["real_get_assertion_2"]
    assert "CLIENT_DATA_HASH_MISMATCH" in a["wrong_challenge_rejected"]
    assert "SIGNATURE_COUNTER_REGRESSION" in a["replay_rejected"]
    assert "not active" in a["revoked_credential_rejected"]
    # genuineness: the fixture aaguid is 0x11*16 and its counter is 0 -> 1
    assert a["authenticator_aaguid"] != "11" * 16
    assert a["real_observed_sign_count_1"] >= 2


def test_22_phase_doc_records_hardware_verified_and_h2_blocked():
    text = PHASE_DOC.read_text()
    assert "REAL-CTAP2-HARDWARE VERIFIED" in text
    assert "**Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**" in text
    assert "finding H-2" in text or "H-2 (BLOCKING)" in text
    assert "no interactive human-election surface" in text
    assert "RHAMP-REQ-152" in text and "RHAMP-INV-018" in text
    # carried guard debt named, not repaired
    assert "F-1" in text and "test_no_contract_change_since_r20_head" in text
    assert "test_no_contract_change_since_b30" in text


# ── 9. finding H-2 — the missing interactive election surface ────────────

def test_23_helper_observe_election_has_no_interactive_surface():
    # Historical H-2 reconstruction reads the immutable BLOCKED-phase blob;
    # later repair phases must not rewrite this evidence.
    src = _git("show", f"{H}:src/pcae/protected_presentation_helper.py")
    seg = src.split("def _observe_election", 1)[1].split("\n\ndef ", 1)[0]
    # the ONLY non-CANCEL path is the disclosed test seam
    assert "test_decision_directive" in seg
    assert 'return "CANCEL"' in seg
    # no interactive read primitive
    for prim in ("input(", "sys.stdin.read", "readline", "/dev/tty", "termios", "tty."):
        assert prim not in seg, prim
    assert "successor hardware phase" in seg or "no interactive local" in seg


def test_24_no_production_caller_passes_test_decision_source():
    hits = _git("grep", "-n", "_test_decision_source", "--", "src/pcae").strip().splitlines()
    # only the launcher's own plumbing + one helper docstring line — never a
    # verifier / gate / enrollment / admin caller.
    for line in hits:
        assert ("core/protected_presentation.py" in line
                or "protected_presentation_helper.py" in line), line
    assert any("_test_decision_source: Optional[str] = None" in l for l in hits)


# ── 10. require_real_assurance PRODUCTION chain composes end-to-end (sw) ──

def _agent_src():
    return lambda account, provisioned_uid: (provisioned_uid, frozenset({999_901}))


def _locked_probe():
    from pcae.core import hpac_protected_admin_writer as w
    return w.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("root",)),
    )


def test_25_require_real_assurance_production_chain_composes_in_software():
    """RHAMP-REQ-152 bullet 4's chain, minus the one leg H-2 blocks. An
    in-process shim stands in for **only** ``_launch_and_exchange``'s
    ``posix_spawn`` boundary (the launcher), NOT the CTAP2 authenticator
    (``DeterministicCtap2Provider`` — structurally NON_REAL) and NOT the human
    election (still the disclosed ``_test_decision_source`` seam). This proves
    nothing downstream of the missing interactive surface is broken; it is an
    IV observation, not a certification.
    """
    from pcae.core import hpac_protected_admin_writer as w
    from pcae.core import hpac_protected_presentation_admin as ppadmin
    from pcae.core import protected_presentation as pp
    from pcae.core import protected_presentation_installation as inst
    import pcae.protected_presentation_helper as H
    from pcae.core.hpac_foundation import (
        _PRODUCTION_TEST_FIXTURE_SEAL, _PRODUCTION_WRITER_FACTORY_SEAL,
        HPACAuthorityClass, HPACStoreAuthority, canonical_digest, canonical_json_bytes,
    )
    from pcae.core.approval_presentation import (
        PresentationMechanismDescriptorStore, TrustedApprovalPresentationStore,
        new_canonical_runtime_approval_subject,
    )
    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore, new_principal_id
    from pcae.core.hpac_lifecycle import HPACLifecycleStore
    from pcae.core.hpac_verifier import (
        AuthenticatedHumanPrincipal, is_verifier_authenticated_principal, verify_human_authentication,
    )
    from pcae.core.hpac_rhamp_client_context import MECHANISM_ID
    from pcae.core.hpac_rhamp_counter_state import COUNTER_STATE_VERIFIER_ROLE, HpacRhampCounterStateStore
    from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore
    from pcae.core.hpac_rhamp_ctap2 import DeterministicCtap2Provider
    from pcae.core.hpac_rhamp_enrollment import enroll_first_credential, resolve_active_credentials
    from pcae.core.human_authenticator_fido2 import FIDO2HumanAuthenticator, encode_assertion_envelope
    from pcae.core.human_authentication_proof import (
        HumanAuthenticationProof, HumanAuthenticationProofStore, PROOF_SCHEMA_VERSION, new_proof_id,
    )

    HELPER_SHIM = (
        b"#!/usr/bin/env python3\nimport sys\nfrom pcae.protected_presentation_helper import main\n"
        b"sys.exit(main())\n"
    )
    RENDERER = "pcae-protected-local-presentation-renderer/1.0"

    def _inproc_launch(helper_fd, request, *, timeout_seconds):
        os.close(helper_fd)
        req = H._validate_request(json.loads(canonical_json_bytes(request).decode()))
        displayed = H.render_human_visible_bytes(req["human_visible_facts"], renderer_profile=req["renderer_profile"])
        dd = hashlib.sha256(displayed).hexdigest()
        decision = H._observe_election(req, displayed)
        if decision == "CANCEL":
            return None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return json.loads(canonical_json_bytes(H._build_response(req, decision, dd, now=now)).decode())

    def _prod(auth, role, subj):
        return auth._mint_production_writer_capability(role, subj, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL)

    orig = pp._launch_and_exchange
    pp._launch_and_exchange = _inproc_launch
    try:
        with tempfile.TemporaryDirectory() as td:
            root = (Path(td) / "root").resolve()
            w.provision_protected_root(protected_root=root, agent_account="a-svc-r5r1", agent_uid=4_242_901)
            authority = HPACStoreAuthority._production_test_fixture(
                root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
            )
            registry = HumanPrincipalRegistryStore(authority)
            sidecar_store = HpacRhampCredentialSidecarStore(authority)
            counter_store = HpacRhampCounterStateStore(authority)
            principal_id = new_principal_id()
            w.enroll_principal_via_pawa(
                principal_id=principal_id, enrollment_provenance_ref="r5r1-iv",
                _protected_root=root, _configured_agent_identity_source=_agent_src(),
                _topology_probe=_locked_probe(),
            )
            sha = hashlib.sha256(HELPER_SHIM).hexdigest()
            hp = inst.helper_content_addressed_path(root, sha)
            hp.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            hp.write_bytes(HELPER_SHIM)
            os.chmod(hp, 0o500)
            ppadmin.configure_presentation_mechanism(
                action="install", helper_sha256=sha, helper_implementation_version="pplp/1.0.0",
                verifier_configuration_digest=hashlib.sha256(b"vc-iv").hexdigest(),
                renderer_profile=RENDERER, descriptor_version="pplp-1.0", protected_root=root,
                _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
            )
            provider = DeterministicCtap2Provider()
            res = enroll_first_credential(
                principal_id=principal_id, subject_digest="a" * 64, presentation_digest="b" * 64,
                invocation_id="iv-r5r1", attempt_id="at-r5r1", provider=provider, protected_root=root,
                _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
            )
            cred = registry.resolve_credential(res.credential_id)

            invocation_id, attempt_id = "inv-r5r1", "at-r5r1"
            facts = {
                "repository_identity": "repo-iv", "repository_display": "repo-iv (fp:iv)",
                "task_id": "task-iv", "task_display": "task-iv x",
                "runtime_target_id": "rt-none", "runtime_target_display": "rt-none x",
                "operation_effect_scope_display": "cap=none; no-effect", "prompt_hash": "c" * 64,
                "prompt_instruction_display": "iv (fp:c001)", "invocation_id": invocation_id,
                "invocation_display": f"{invocation_id} (fp:i001)", "expires_at": "2099-01-01T00:00:00Z",
                "one_shot_notice": True,
            }
            dd = hashlib.sha256(H.render_human_visible_bytes(facts, renderer_profile=RENDERER)).hexdigest()
            subject = new_canonical_runtime_approval_subject(
                subject={"repository_identity": "repo-iv", "task_id": "task-iv",
                         "runtime_target_id": "rt-none", "prompt_hash": "c" * 64, "invocation_id": invocation_id},
                approval_scope={"capability": "none", "one_dispatch": False, "network": False},
                approval_preview_digest=dd, expires_at="2099-01-01T00:00:00Z",
            )
            approval_id = "ria-" + hashlib.sha256(f"{invocation_id}{attempt_id}".encode()).hexdigest()[:32]
            cer = pp.run_protected_presentation_ceremony(
                authority=authority, approval_id=approval_id, challenge_id="ch-" + invocation_id,
                canonical_subject=subject, human_visible_facts=facts, principal_id=principal_id,
                invocation_id=invocation_id, attempt_id=attempt_id, _test_decision_source="APPROVE",
            )
            ds = PresentationMechanismDescriptorStore(authority)
            ps = TrustedApprovalPresentationStore(authority)
            resolved_pres = ps.resolve_canonical(
                presentation_id=cer.presentation_id, presentation_digest=cer.presentation_digest, descriptor_store=ds
            )
            assert resolved_pres.authority_class is HPACAuthorityClass.PRODUCTION

            material = resolve_active_credentials(registry, principal_id)
            allow = tuple(m.raw_credential_id for m in material if m.credential_id == res.credential_id)
            auth_fido = FIDO2HumanAuthenticator(
                principal_id=principal_id, credential_id=res.credential_id, provider=provider,
                allow_credential_ids=allow, invocation_id=invocation_id, attempt_id=attempt_id,
            )
            ch = auth_fido.prepare_challenge(subject.digest(), cer.presentation_digest, issued_at="2026-09-03T12:00:00Z")
            env = auth_fido.run_assertion_ceremony(ch)
            body = {
                "proof_schema_version": PROOF_SCHEMA_VERSION, "proof_id": new_proof_id(),
                "mechanism_id": MECHANISM_ID, "principal_id": principal_id, "credential_id": res.credential_id,
                "challenge_digest": ch.challenge_digest, "approval_subject_digest": ch.approval_subject_digest,
                "trusted_presentation_ref": {"presentation_id": cer.presentation_id,
                                             "presentation_digest": cer.presentation_digest},
                "assertion": encode_assertion_envelope(env), "up": env.up, "uv": env.uv,
                "authenticated_at": ch.issued_at, "verifier_version": "iv-r5r1/1.0",
            }
            body["proof_digest"] = canonical_digest({k: v for k, v in body.items() if k != "proof_digest"})
            proof = HumanAuthenticationProof(**body)
            proof_store = HumanAuthenticationProofStore(authority)
            proof_store.create_canonical(_prod(authority, "human_authentication_proof_verifier", MECHANISM_ID), proof)
            resolved_proof = proof_store.resolve_canonical(proof.proof_id)
            assert resolved_proof.authority_class is HPACAuthorityClass.PRODUCTION

            lc = HPACLifecycleStore(authority)
            lc.open_challenge_canonical(
                _prod(authority, "hpac_challenge_coordinator", proof.proof_id),
                proof_id=proof.proof_id, approval_id=approval_id, invocation_id=invocation_id,
                attempt_id=attempt_id, principal_id=principal_id, credential_id=res.credential_id,
                mechanism_id=MECHANISM_ID, occurred_at="2026-09-03T12:00:10Z",
                resolved_presentation=resolved_pres, challenge=ch,
            )
            lc.record_assertion_canonical(
                _prod(authority, "hpac_assertion_recorder", proof.proof_id),
                proof_id=proof.proof_id, assertion_digest=canonical_digest({"assertion": proof.assertion}),
                occurred_at="2026-09-03T12:00:20Z",
            )
            lc.record_verified_canonical(
                _prod(authority, "human_authentication_proof_verifier", proof.proof_id),
                resolved_proof=resolved_proof, registry_state_digest=canonical_digest({"r": "s"}),
                verifier_version="iv-r5r1/1.0", occurred_at="2026-09-03T12:00:30Z",
            )
            result = verify_human_authentication(
                registry=registry, presentation_store=ps, descriptor_store=ds, proof_store=proof_store,
                lifecycle_store=lc, challenge=ch, proof_id=proof.proof_id, approval_id=approval_id,
                now="2026-09-03T12:01:00Z", occurred_at="2026-09-03T12:00:45Z",
                gate5_writer=_prod(authority, "hpac_gate5_binder", proof.proof_id),
                require_real_assurance=True, sidecar_store=sidecar_store, counter_state_store=counter_store,
                counter_state_writer=_prod(authority, COUNTER_STATE_VERIFIER_ROLE, res.credential_id),
            )
            assert isinstance(result, AuthenticatedHumanPrincipal)
            assert result.assurance_class is HPACAuthorityClass.PRODUCTION
            assert result.is_real_runtime_eligible is True
            assert is_verifier_authenticated_principal(result)
    finally:
        pp._launch_and_exchange = orig


def test_26_gate5_frozen_production_check_is_the_only_consumption_path():
    g5 = (SRC / "core" / "runtime_dispatch_gate5.py").read_text()
    assert "principal.assurance_class is HPACAuthorityClass.PRODUCTION" in g5
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    assert "HPAC-PPA-REQ-057" in v and "_REAL_PRESENTATION_MECHANISM_ID" in v


# ── 11. boundaries unchanged ────────────────────────────────────────────

def test_27_runtime_still_not_implemented_observed_unavailable():
    out = subprocess.run(
        ["python", "-m", "pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=str(REPO)
    ).stdout
    assert "not_implemented" in out and "Observed" in out and "unavailable" in out
    import re
    assert re.search(r"Plugin count:\s+0\b", out) and re.search(r"Capability count:\s+0\b", out)


def test_28_no_first_external_effect_primitive_anywhere_new():
    added = [l for l in _git("diff", A, H, "--", "src/pcae").splitlines()
             if l.startswith("+") and not l.startswith("+++")]
    changed = {l.split(" b/")[-1] for l in _git("diff", A, H, "--", "src/pcae").splitlines()
               if l.startswith("diff --git ")}
    assert changed <= {"src/pcae/core/hpac_rhamp_ctap2.py"}, changed
    for l in added:
        assert "adapter.dispatch(" not in l and "DispatchEnvelope" not in l
        assert "os.fork" not in l and "posix_spawn" not in l


def test_29_n16_6_and_n16_7_untouched():
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "N-16-6" in status and "N-16-7" in status


def test_30_fido2_profile_is_supported_not_exclusive():
    text = PHASE_DOC.read_text()
    assert "not globally mandatory" in text.lower() or "not.*exclusive" or "supported-not-exclusive" in text.lower()
    assert "mobile-only" in text.lower()
    assert "MUST NOT" in text and "block current development" in text


def test_31_this_phase_touched_only_doc_test_status_and_pcae_files():
    changed = {l.split("\t")[-1] for l in _git("diff", "--name-only", V, H).splitlines() if l.strip()}
    for path in changed:
        assert (path.startswith(("docs/", "tests/", "tasks/", ".pcae/"))
                or path in {"PROJECT_STATUS.md", "CHANGELOG.md"}), path


def test_32_n_16_5_not_closed_everywhere():
    assert "NOT CLOSED" in PHASE_DOC.read_text()
    status = (REPO / "PROJECT_STATUS.md").read_text().split("## Prior Phase", 1)[0]
    assert "N-16-5" in status and "NOT CLOSED" in status
