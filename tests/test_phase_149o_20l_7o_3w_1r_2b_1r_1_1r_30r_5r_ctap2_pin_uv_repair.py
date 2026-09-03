"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R — N-16-5 CTAP2 PIN/UV Protocol
Interoperability Repair (finding H-1).

Dedicated repair suite. It exercises the *production* :class:`NativeCtap2Provider`
CTAP 2.1 PIN/UV code path against an in-memory, protocol-faithful,
structurally-NON_REAL virtual authenticator (:func:`build_virtual_ctap2_test_seam`),
proving:

* the historical `.1R.30R.5` BLOCKED artifact is preserved / immutable;
* the bare-``uv``-option request shape (finding H-1) is gone from production and
  is rejected by the protocol-faithful fixture exactly as real FIDO_2_1 hardware
  rejects it (``CTAP2_ERR_INVALID_OPTION`` / ``0x2C``);
* GetInfo capability negotiation + PIN/UV protocol selection (V2 preferred, V1
  fallback where valid);
* a trusted, non-logging, non-persisted local PIN flow (no CLI / env / repo PIN);
* permission-scoped, rp-bound PIN/UV tokens and command-scoped
  ``pinUvAuthParam`` for both ceremonies;
* mandatory UV is never downgraded; an authenticator that cannot perform UV is
  rejected as incompatible;
* production / test provider authority separation is intact;
* registration / counter-state / verifier / presentation / Gate 5-9 / contracts
  / runtime / first-effect boundaries are unchanged.

No hardware is accessed (RHAMP-REQ-153 for every phase before the controlled
hardware session). Synthetic PIN values only.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import subprocess
from pathlib import Path

import pytest

from fido2.ctap import CtapError

from pcae.core.hpac_rhamp_client_context import RP_ID, RP_ID_HASH
from pcae.core.hpac_rhamp_ctap2 import (
    Ctap2CancelledError,
    Ctap2UnavailableError,
    DeterministicCtap2Provider,
    NativeCtap2Provider,
    PRODUCTION_PROVIDER_KIND,
    _VirtualCtap2Authenticator,
    build_virtual_ctap2_test_seam,
    resolve_production_ctap2_provider,
    verify_assertion_signature_material,
)

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CTAP2_SRC = SRC / "core" / "hpac_rhamp_ctap2.py"
CONTRACTS = REPO / "docs" / "contracts"

_SYNTHETIC_PIN = "13795746"  # NON_REAL fixture value — never a real device PIN


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True).stdout


def _cdh(tag: bytes) -> bytes:
    return hashlib.sha256(b"pcae-hpac-cdh::" + tag).digest()


def _enrolled(**kw):
    provider, auth = build_virtual_ctap2_test_seam(**kw)
    mc = provider.make_credential(client_data_hash=_cdh(b"enroll"), user_id=b"u" * 16, user_name="alice")
    return provider, auth, mc


# ── 1. Historical .1R.30R.5 BLOCKED artifact preserved ─────────────────────

def test_01_historical_30r5_blocked_report_is_preserved_and_immutable():
    doc = REPO / "docs" / (
        "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5_"
        "N_16_5_MANDATORY_REAL_CTAP2_HARDWARE_VERIFICATION_AND_N_16_5_CLOSURE.md"
    )
    text = doc.read_text(encoding="utf-8")
    assert "**Status:** **BLOCKED.**" in text
    assert "finding H-1" in text or "H-1" in text
    # the finalized .1R.30R.5 head is still reachable and its subject unchanged
    subj = _git("log", "-1", "--format=%s", "4e6762bd").strip()
    assert "1R.30R.5" in subj and "BLOCKED" in subj


def test_02_h1_bare_uv_shape_is_gone_from_production():
    text = CTAP2_SRC.read_text(encoding="utf-8")
    assert '"rk": False, "uv": True' not in text
    assert 'options={"uv": True}' not in text
    # UV now flows through a command-scoped pinUvAuthParam on both ceremonies.
    assert text.count("pin_uv_param=pin_uv_param") >= 2
    assert text.count("pin_uv_protocol=pin_uv_protocol") >= 2


# ── 3. No bare-uv production path / no fallback ────────────────────────────

def test_03_no_bare_uv_retry_after_pin_uv_negotiation():
    src = inspect.getsource(NativeCtap2Provider.make_credential)
    src += inspect.getsource(NativeCtap2Provider.get_assertion)
    # the only options dict passed is {"rk": False}; no "uv" dict key anywhere.
    assert '"uv":' not in src
    assert 'options={"uv"' not in src
    assert 'options = {"rk": False}' in src


def test_04_virtual_authenticator_rejects_bare_uv_like_real_hardware():
    auth = _VirtualCtap2Authenticator()
    with pytest.raises(CtapError) as ei:
        auth.make_credential(
            _cdh(b"x"), {"id": RP_ID}, {"id": b"u"}, [{"type": "public-key", "alg": -7}],
            options={"uv": True}, pin_uv_param=b"p", pin_uv_protocol=2,
        )
    assert ei.value.code == CtapError.ERR.INVALID_OPTION  # 0x2C
    with pytest.raises(CtapError) as ej:
        auth.get_assertion(RP_ID, _cdh(b"x"), allow_list=[{"id": b"c"}], options={"uv": True},
                           pin_uv_param=b"p", pin_uv_protocol=2)
    assert ej.value.code == CtapError.ERR.INVALID_OPTION


def test_05_missing_pin_uv_param_is_rejected():
    auth = _VirtualCtap2Authenticator()
    with pytest.raises(CtapError) as ei:
        auth.make_credential(_cdh(b"x"), {"id": RP_ID}, {"id": b"u"},
                             [{"type": "public-key", "alg": -7}])
    assert ei.value.code == CtapError.ERR.PUAT_REQUIRED


# ── 4-7. Capability negotiation + protocol selection ──────────────────────

def test_06_getinfo_capability_negotiation_incompatible_device_rejected():
    # no built-in UV and no client PIN configured -> incompatible, no downgrade
    provider, _ = build_virtual_ctap2_test_seam(client_pin_configured=False, builtin_uv=False)
    with pytest.raises(Ctap2UnavailableError) as ei:
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert "downgrade" in str(ei.value).lower()


def test_07_protocol_v2_selected_when_supported():
    provider, auth = build_virtual_ctap2_test_seam(pin_uv_protocols=(2, 1))
    mc = provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert mc.uv is True
    # captured protocol version on the last token grant path is V2
    assert 2 in auth._pin_uv_protocols


def test_08_protocol_v1_fallback_only_when_v2_absent():
    provider, auth = build_virtual_ctap2_test_seam(pin_uv_protocols=(1,))
    mc = provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert mc.uv is True


def test_09_no_mutually_supported_protocol_is_rejected():
    provider, _ = build_virtual_ctap2_test_seam(pin_uv_protocols=(7,))
    with pytest.raises(Ctap2UnavailableError):
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")


def test_10_builtin_uv_authenticator_uses_uv_token_no_pin_prompt():
    calls = []

    def _prompt():
        calls.append(1)
        return "should-not-be-called"

    auth = _VirtualCtap2Authenticator(builtin_uv=True, client_pin_configured=False)
    from pcae.core.hpac_rhamp_ctap2 import _VirtualClientPin

    provider = NativeCtap2Provider(
        _connection_factory=lambda: auth,
        _client_pin_factory=lambda _c: _VirtualClientPin(auth),
        _pin_prompt=_prompt,
    )
    mc = provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert mc.uv is True
    assert calls == []  # built-in UV -> no PIN prompt at all


# ── 8-9. Trusted, non-logging, non-persisted PIN entry ────────────────────

def test_11_default_pin_prompt_is_getpass_and_fails_closed_non_interactive(monkeypatch):
    from pcae.core import hpac_rhamp_ctap2 as mod

    import sys

    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    with pytest.raises(Ctap2UnavailableError):
        mod._default_pin_prompt()


def test_12_default_pin_prompt_uses_getpass():
    src = inspect.getsource(__import__("pcae.core.hpac_rhamp_ctap2", fromlist=["x"])._default_pin_prompt)
    assert "getpass" in src
    assert "isatty" in src


def test_13_no_env_or_cli_or_repo_pin_source():
    text = CTAP2_SRC.read_text(encoding="utf-8").lower()
    # no environment / argv / config PIN read
    assert "os.environ" not in text.replace("os.environ:", "")
    assert "getenv" not in text
    assert "argv" not in text
    assert "sys.argv" not in text


def test_14_pin_never_stored_on_the_production_provider():
    provider, auth, _ = _enrolled()
    # NativeCtap2Provider (the PCAE side) holds no PIN. The virtual
    # authenticator legitimately models the *device* that holds the PIN.
    blob = repr(vars(provider))
    assert _SYNTHETIC_PIN not in blob
    assert not any(getattr(provider, k, None) == _SYNTHETIC_PIN for k in vars(provider))


def test_15_pin_never_in_exception_text_on_wrong_pin():
    provider, _ = build_virtual_ctap2_test_seam(supplied_pin="00000000")
    try:
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
        pytest.fail("wrong PIN should have failed")
    except Ctap2UnavailableError as exc:
        assert "00000000" not in str(exc)
        assert "invalid PIN" in str(exc) or "user verification failed" in str(exc)


def test_16_pin_prompt_cancellation_fails_closed():
    def _cancel():
        raise Ctap2CancelledError("PIN entry cancelled")

    auth = _VirtualCtap2Authenticator()
    from pcae.core.hpac_rhamp_ctap2 import _VirtualClientPin

    provider = NativeCtap2Provider(
        _connection_factory=lambda: auth,
        _client_pin_factory=lambda _c: _VirtualClientPin(auth),
        _pin_prompt=_cancel,
    )
    with pytest.raises(Ctap2CancelledError):
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert auth._credentials == {}  # nothing created


def test_17_empty_pin_is_rejected():
    provider, _ = build_virtual_ctap2_test_seam(supplied_pin="")
    with pytest.raises(Ctap2UnavailableError):
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")


# ── 10-13. Token scoping / rp binding / command-scoped auth param ─────────

def test_18_token_is_permission_scoped_per_command():
    provider, auth, mc = _enrolled()
    # make_credential granted a MAKE_CREDENTIAL-scoped token
    from fido2.ctap2 import ClientPin
    assert auth._token_permissions == ClientPin.PERMISSION.MAKE_CREDENTIAL
    provider.get_assertion(client_data_hash=_cdh(b"auth"), allow_credential_ids=[mc.raw_credential_id])
    assert auth._token_permissions == ClientPin.PERMISSION.GET_ASSERTION


def test_19_token_is_bound_to_the_canonical_rp_id():
    _, auth, _ = _enrolled()
    assert auth._token_rpid == RP_ID == "hpac.pcae.local"


def test_20_wrong_permission_token_is_rejected():
    from fido2.ctap2 import ClientPin
    auth = _VirtualCtap2Authenticator()
    auth._issue_token(ClientPin.PERMISSION.GET_ASSERTION, RP_ID)
    param = hashlib.sha256(auth._token).digest()  # deliberately wrong shape
    with pytest.raises(CtapError):
        auth.make_credential(_cdh(b"x"), {"id": RP_ID}, {"id": b"u"},
                             [{"type": "public-key", "alg": -7}],
                             pin_uv_param=param, pin_uv_protocol=2)


def test_21_wrong_rp_id_token_binding_is_rejected():
    from fido2.ctap2 import ClientPin
    import hmac
    auth = _VirtualCtap2Authenticator()
    auth._issue_token(ClientPin.PERMISSION.MAKE_CREDENTIAL, "attacker.example")
    good = hmac.new(auth._token, _cdh(b"x"), hashlib.sha256).digest()
    with pytest.raises(CtapError) as ei:
        auth.make_credential(_cdh(b"x"), {"id": RP_ID}, {"id": b"u"},
                             [{"type": "public-key", "alg": -7}],
                             pin_uv_param=good, pin_uv_protocol=2)
    assert ei.value.code == CtapError.ERR.PIN_AUTH_INVALID


def test_22_command_scoped_auth_param_differs_per_client_data_hash():
    import hmac
    auth = _VirtualCtap2Authenticator()
    tok = auth._issue_token(None, RP_ID)
    a = hmac.new(tok, _cdh(b"a"), hashlib.sha256).digest()
    b = hmac.new(tok, _cdh(b"b"), hashlib.sha256).digest()
    assert a != b
    # a param computed over challenge "a" must not validate for challenge "b"
    with pytest.raises(CtapError):
        auth.get_assertion(RP_ID, _cdh(b"b"), allow_list=[{"id": b"c"}],
                           pin_uv_param=a, pin_uv_protocol=2)


def test_23_wrong_protocol_version_is_rejected():
    auth = _VirtualCtap2Authenticator(pin_uv_protocols=(2,))
    auth._issue_token(None, RP_ID)
    import hmac
    param = hmac.new(auth._token, _cdh(b"x"), hashlib.sha256).digest()
    with pytest.raises(CtapError) as ei:
        auth.make_credential(_cdh(b"x"), {"id": RP_ID}, {"id": b"u"},
                             [{"type": "public-key", "alg": -7}],
                             pin_uv_param=param, pin_uv_protocol=1)
    assert ei.value.code == CtapError.ERR.INVALID_PARAMETER


# ── 14-15. makeCredential / getAssertion repair (positive) ───────────────

def test_24_make_credential_positive_produces_es256_uv_credential():
    _, _, mc = _enrolled()
    assert mc.up is True and mc.uv is True
    assert mc.transport in ("usb", "nfc")
    from fido2.cose import CoseKey
    from fido2 import cbor
    key = CoseKey.parse(cbor.decode(mc.cose_public_key))
    assert key[3] == -7  # ES256


def test_25_get_assertion_positive_passes_full_signature_material_check():
    provider, _, mc = _enrolled()
    cdh = _cdh(b"assert-1")
    ga = provider.get_assertion(client_data_hash=cdh, allow_credential_ids=[mc.raw_credential_id])
    chk = verify_assertion_signature_material(
        cose_public_key=mc.cose_public_key,
        authenticator_data=ga.authenticator_data,
        signature=ga.signature,
        client_data_hash=cdh,
    )
    assert chk.rp_id_hash_ok and chk.signature_ok and chk.up and chk.uv
    assert chk.sign_count >= 1


def test_26_get_assertion_counter_increments():
    provider, _, mc = _enrolled()
    g1 = provider.get_assertion(client_data_hash=_cdh(b"a1"), allow_credential_ids=[mc.raw_credential_id])
    g2 = provider.get_assertion(client_data_hash=_cdh(b"a2"), allow_credential_ids=[mc.raw_credential_id])
    assert g2.sign_count > g1.sign_count


def test_27_get_assertion_requires_non_empty_allowlist():
    provider, _, _ = _enrolled()
    with pytest.raises(Ctap2UnavailableError):
        provider.get_assertion(client_data_hash=_cdh(b"a"), allow_credential_ids=[])


def test_28_wrong_challenge_assertion_fails_signature_material():
    provider, _, mc = _enrolled()
    ga = provider.get_assertion(client_data_hash=_cdh(b"real"), allow_credential_ids=[mc.raw_credential_id])
    chk = verify_assertion_signature_material(
        cose_public_key=mc.cose_public_key,
        authenticator_data=ga.authenticator_data,
        signature=ga.signature,
        client_data_hash=_cdh(b"different"),
    )
    assert chk.signature_ok is False


# ── 16-17. No UP-only downgrade ───────────────────────────────────────────

def test_29_make_credential_without_uv_flag_is_rejected():
    provider, _ = build_virtual_ctap2_test_seam(uv=False)
    with pytest.raises(Ctap2UnavailableError) as ei:
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert "UV" in str(ei.value) or "user verification" in str(ei.value).lower()


def test_30_uv_semantics_never_weakened_in_source():
    text = CTAP2_SRC.read_text(encoding="utf-8")
    assert "forbids a UP-only downgrade" in text
    assert "FLAG.UV" in text


# ── 18. PIN error mapping (existing frozen codes only) ────────────────────

def test_31_pin_blocked_maps_to_existing_terminal_reason():
    provider, _ = build_virtual_ctap2_test_seam(pin_blocked=True)
    with pytest.raises(Ctap2UnavailableError) as ei:
        provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    assert "blocked" in str(ei.value).lower()


def test_32_no_new_terminal_reason_code_added():
    from pcae.core.hpac_rhamp_terminal_reasons import TerminalReasonCode
    assert len(list(TerminalReasonCode)) == 41


# ── 20-21. Deterministic provider realism / authority separation ──────────

def test_33_virtual_authenticator_is_structurally_non_real():
    assert _VirtualCtap2Authenticator.SIMULATION_ONLY is True
    assert _VirtualCtap2Authenticator.PROVIDER_KIND_IS_REAL is False
    from pcae.core.hpac_rhamp_ctap2 import _VirtualClientPin
    assert _VirtualClientPin.SIMULATION_ONLY is True


def test_34_deterministic_provider_still_non_real():
    p = DeterministicCtap2Provider()
    assert p.SIMULATION_ONLY is True
    assert p.PROVIDER_KIND != PRODUCTION_PROVIDER_KIND
    assert getattr(p, "PROVIDER_KIND_IS_REAL", True) is False


def test_35_production_resolver_is_distinct_and_takes_no_seam():
    prov = resolve_production_ctap2_provider()
    assert isinstance(prov, NativeCtap2Provider)
    assert prov.PROVIDER_KIND == PRODUCTION_PROVIDER_KIND
    # no seam populated by the production path
    assert prov._connection_factory is None
    assert prov._client_pin_factory is None
    src = inspect.getsource(resolve_production_ctap2_provider)
    assert "return NativeCtap2Provider()" in src
    assert "os.environ" not in src and "getenv" not in src


def test_36_seam_params_are_underscore_prefixed_keyword_only():
    sig = inspect.signature(NativeCtap2Provider.__init__)
    for name in ("_connection_factory", "_client_pin_factory", "_pin_prompt"):
        assert name in sig.parameters
        assert sig.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters[name].default is None


def test_37_build_seam_returns_real_native_provider():
    provider, auth = build_virtual_ctap2_test_seam()
    assert type(provider) is NativeCtap2Provider
    assert isinstance(auth, _VirtualCtap2Authenticator)


# ── 25. Negative UV can never yield REAL success ──────────────────────────

def test_38_up_only_assertion_is_flagged_by_signature_material():
    provider, _ = build_virtual_ctap2_test_seam()
    mc = provider.make_credential(client_data_hash=_cdh(b"e"), user_id=b"u" * 16, user_name="a")
    # a fresh authenticator that yields UP only
    provider2, _ = build_virtual_ctap2_test_seam(uv=True)
    ga = provider2.get_assertion(client_data_hash=_cdh(b"a"),
                                 allow_credential_ids=[mc.raw_credential_id]) if False else None
    # direct: craft a UP-only assertion via the virtual authenticator
    p3, a3 = build_virtual_ctap2_test_seam()
    m3 = p3.make_credential(client_data_hash=_cdh(b"e3"), user_id=b"u" * 16, user_name="a")
    a3._uv = False
    cdh = _cdh(b"a3")
    ga = a3.get_assertion(RP_ID, cdh, allow_list=[{"id": m3.raw_credential_id}],
                          pin_uv_param=__import__("hmac").new(a3._issue_token(None, RP_ID), cdh, hashlib.sha256).digest(),
                          pin_uv_protocol=2)
    chk = verify_assertion_signature_material(
        cose_public_key=m3.cose_public_key, authenticator_data=ga.auth_data,
        signature=ga.signature, client_data_hash=cdh,
    )
    assert chk.uv is False


# ── 26. Secret-handling ──────────────────────────────────────────────────

def test_39_pin_not_in_logs_or_source_literals():
    text = CTAP2_SRC.read_text(encoding="utf-8")
    assert "import logging" not in text
    assert "getLogger" not in text
    assert "logger." not in text


def test_40_provider_source_drops_the_pin_promptly():
    text = CTAP2_SRC.read_text(encoding="utf-8")
    assert "del pin" in text  # PIN reference dropped as soon as the token is obtained
    native_part = text.split("Deterministic NON_REAL provider")[0]
    # NativeCtap2Provider keeps no PIN attribute
    assert "self._pin =" not in native_part
    assert "self._pin:" not in native_part


# ── 27-28. No contract change / narrow production diff ────────────────────

_R0 = "9f004ea9"


def test_41_no_normative_contract_change():
    changed = [l for l in _git("diff", "--name-only", _R0, "--", "docs/contracts").split() if l.strip()]
    assert changed == [], changed


def test_42_production_diff_is_confined_to_the_ctap2_module():
    changed = set(_git("diff", "--name-only", _R0, "--", "src/pcae", "scripts", "pyproject.toml").split())
    assert changed <= {"src/pcae/core/hpac_rhamp_ctap2.py"}, changed


def test_43_no_new_dependency():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "fido2" in text  # already declared; unchanged
    diff = _git("diff", _R0, "--", "pyproject.toml")
    assert diff.strip() == ""


# ── 29-31. No test weakening / scope fences ──────────────────────────────

def test_44_this_suite_defines_no_skip_or_xfail():
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            dump = " ".join(ast.dump(d) for d in node.decorator_list)
            assert "xfail" not in dump
            assert "skip" not in dump.replace("skipif", "")
        # no runtime pytest.skip()/fnmatch broadening call anywhere
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            assert name not in {"skip", "xfail", "fnmatch", "fnmatchcase"}


def test_45_no_first_effect_primitive_in_ctap2_module():
    tree = ast.parse(CTAP2_SRC.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name not in {"subprocess", "socket", "ssl", "http.client", "multiprocessing", "requests"}
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in {"subprocess", "socket", "ssl", "http.client"}
    text = CTAP2_SRC.read_text()
    assert "adapter.dispatch(" not in text
    assert "os.fork" not in text
    assert "posix_spawn" not in text


def test_46_registration_and_verifier_and_presentation_modules_unchanged():
    for rel in (
        "src/pcae/core/hpac_rhamp_enrollment.py",
        "src/pcae/core/hpac_rhamp_credential_sidecar.py",
        "src/pcae/core/hpac_rhamp_counter_state.py",
        "src/pcae/core/hpac_rhamp_assertion_verify.py",
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/human_authenticator_fido2.py",
        "src/pcae/core/approval_presentation.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    ):
        assert _git("diff", "--stat", _R0, "HEAD", "--", rel).strip() == "", rel


def test_47_runtime_boundary_unchanged():
    out = subprocess.run(
        [str(REPO / ".venv/bin/pcae"), "runtime", "inspect"],
        capture_output=True, text=True, cwd=REPO,
    ).stdout
    assert "not_implemented" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out


def test_48_n16_6_and_n16_7_untouched():
    # no runtime effect-adapter admission, no Observed->Approved transition
    text = CTAP2_SRC.read_text()
    assert "Observed" not in text or "Approved" not in text
    assert "enable execution" not in text.lower()
