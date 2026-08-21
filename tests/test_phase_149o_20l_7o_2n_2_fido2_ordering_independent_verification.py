"""Phase 149O.20L.7O.2N.2 — Independent Verification of the Phase
149O.20L.7O.2N.1 repair of Blocking finding B-149O.20L.7O.2N-1
(`scripts/hatp_hardware_credential_admin.py::_cmd_enroll` ran the real
FIDO2 `makeCredential` ceremony before governance confirmation was
checked).

This suite is authored independently of Phase 149O.20L.7O.2N.1's own
`tests/test_hatp_hardware_credential_admin_script.py` additions: it does
not import, call, or otherwise reuse that suite's fixtures or
assertions. It re-derives the required behavior directly from the
current script source and re-instruments the call path from scratch.

Every synthetic provider/writer/registry seam here is fabricated in
this file. No real FIDO2/PIV hardware, no Dell host, no production
credential store is touched anywhere in this module.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import List

import pytest

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core.hatp_fido2_provider import EnrolledFido2Credential
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStoreError
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, HATPProviderDeviceError

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"

_CRED_ID = "cc" * 16
_PUBKEY = "dd" * 20


def _load_module():
    spec = importlib.util.spec_from_file_location("hatp_hw_admin_2n2_iv", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    root = tmp_path / "store"
    root.mkdir()
    return root


@pytest.fixture()
def mod(monkeypatch: pytest.MonkeyPatch, store: Path):
    m = _load_module()

    def _bound_register(*args, **kwargs):
        kwargs.setdefault("_store_root", store)
        return hw_admin.register_credential(*args, **kwargs)

    def _bound_preview_revoke(*args, **kwargs):
        kwargs.setdefault("_store_root", store)
        return hw_admin.preview_revoke_credential(*args, **kwargs)

    def _bound_revoke(*args, **kwargs):
        kwargs.setdefault("_store_root", store)
        return hw_admin.revoke_credential(*args, **kwargs)

    monkeypatch.setattr(m, "register_credential", _bound_register)
    monkeypatch.setattr(m, "preview_revoke_credential", _bound_preview_revoke)
    monkeypatch.setattr(m, "revoke_credential", _bound_revoke)
    return m


def _log_ceremony(monkeypatch: pytest.MonkeyPatch, module, events: List[str], *, fail: Exception | None = None):
    def _ceremony(*, presence_timeout_s: float):
        events.append("provider_ceremony")
        if fail is not None:
            raise fail
        return EnrolledFido2Credential(
            credential_id_hex=_CRED_ID,
            algorithm="ES256",
            public_key_hex=_PUBKEY,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
        )

    monkeypatch.setattr(module, "_run_enrollment_ceremony", _ceremony)


def _log_confirm(monkeypatch: pytest.MonkeyPatch, module, events: List[str], *, accept: bool):
    def _confirm(description: str) -> bool:
        events.append("confirmation_checked")
        return accept

    monkeypatch.setattr(module, "_prompt_confirm", _confirm)


def _log_register(monkeypatch: pytest.MonkeyPatch, module, events: List[str]):
    original = module.register_credential

    def _wrapped(*args, **kwargs):
        events.append("register_credential")
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "register_credential", _wrapped)


# ── §8/§10: successful path event order ─────────────────────────────


def test_successful_enroll_confirms_before_provider_before_writer(mod, monkeypatch, tmp_path):
    events: List[str] = []
    _log_confirm(monkeypatch, mod, events, accept=True)
    _log_ceremony(monkeypatch, mod, events)
    _log_register(monkeypatch, mod, events)

    code = mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-A"])

    assert code == 0
    assert events == ["confirmation_checked", "provider_ceremony", "register_credential"]


# ── §8/§9: declined confirmation — zero provider/writer effect ─────


def test_declined_confirmation_zero_provider_zero_writer_calls(mod, monkeypatch, tmp_path):
    events: List[str] = []
    _log_confirm(monkeypatch, mod, events, accept=False)
    _log_ceremony(monkeypatch, mod, events)
    _log_register(monkeypatch, mod, events)

    code = mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-B"])

    assert code == 1
    assert events == ["confirmation_checked"]
    assert not any(e == "provider_ceremony" for e in events)
    assert not any(e == "register_credential" for e in events)


def test_assume_yes_skips_prompt_but_still_confirms_before_provider(mod, monkeypatch, tmp_path):
    events: List[str] = []
    # _prompt_confirm must never even be invoked when --assume-yes is set.

    def _fail_if_called(_description: str) -> bool:
        raise AssertionError("_prompt_confirm must not be called under --assume-yes")

    monkeypatch.setattr(mod, "_prompt_confirm", _fail_if_called)
    _log_ceremony(monkeypatch, mod, events)
    _log_register(monkeypatch, mod, events)

    code = mod.main(
        ["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-C", "--assume-yes"]
    )

    assert code == 0
    assert events == ["provider_ceremony", "register_credential"]


# ── §14/§15: --preview is hardware-free and truthful ────────────────


def test_preview_never_touches_provider_or_writer(mod, monkeypatch, tmp_path, capsys):
    events: List[str] = []
    _log_ceremony(monkeypatch, mod, events)
    _log_register(monkeypatch, mod, events)

    def _fail_if_called(_description: str) -> bool:
        raise AssertionError("_prompt_confirm must not be called for --preview")

    monkeypatch.setattr(mod, "_prompt_confirm", _fail_if_called)

    code = mod.main(
        ["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-D", "--preview"]
    )

    assert code == 0
    assert events == []
    out = capsys.readouterr().out
    assert "has NOT run yet" in out
    assert _CRED_ID not in out
    assert _PUBKEY not in out
    assert "signer_key_id" not in out
    assert "public_key" not in out


def test_prospective_description_contains_no_fabricated_identity(mod, tmp_path):
    desc = mod._describe_prospective_enrollment(
        repository_root=tmp_path, enrollment_reference="CHGR-E", presence_timeout_s=30.0
    )
    assert "credential_id" not in desc
    assert "signer_key_id" not in desc
    assert "public_key" not in desc
    assert str(tmp_path) in desc
    assert "CHGR-E" in desc


# ── §22: provider failure after confirmation ─────────────────────────


def test_provider_failure_after_confirmation_no_record_no_false_success(mod, monkeypatch, store, tmp_path):
    events: List[str] = []
    _log_confirm(monkeypatch, mod, events, accept=True)
    _log_ceremony(monkeypatch, mod, events, fail=HATPProviderDeviceError("no device"))

    code = mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-F"])

    assert code == 1
    assert events == ["confirmation_checked", "provider_ceremony"]
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_CRED_ID) is None


# ── §23: user-presence timeout after confirmation ────────────────────


def test_user_presence_timeout_after_confirmation_clean_failure(mod, monkeypatch, store, tmp_path):
    events: List[str] = []
    _log_confirm(monkeypatch, mod, events, accept=True)
    _log_ceremony(monkeypatch, mod, events, fail=HATPProviderDeviceError("presence timeout"))

    code = mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-G"])

    assert code == 1
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_CRED_ID) is None
    # exactly one ceremony attempt -- no automatic retry of the hardware step itself
    assert events.count("provider_ceremony") == 1


# ── §11/§12: exactly one ceremony under forced write retry, same evidence ──


def test_persistence_retry_reuses_identical_evidence_one_ceremony_only(mod, monkeypatch, store, tmp_path):
    events: List[str] = []
    _log_confirm(monkeypatch, mod, events, accept=True)
    _log_ceremony(monkeypatch, mod, events)

    attempts = {"n": 0}
    original_register = mod.register_credential

    def _flaky_register(*args, **kwargs):
        attempts["n"] += 1
        events.append(f"register_attempt_{attempts['n']}")
        if attempts["n"] < 3:
            raise HATPHardwareCredentialStoreError("transient")
        return original_register(*args, **kwargs)

    monkeypatch.setattr(mod, "register_credential", _flaky_register)

    code = mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-H"])

    assert code == 0
    assert events.count("provider_ceremony") == 1
    assert attempts["n"] == 3
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_CRED_ID)
    assert record is not None
    assert record.signer_key_id == _CRED_ID


# ── §25: no caller-supplied credential identity anywhere on enroll ──


def test_enroll_parser_has_no_identity_override_flags(mod):
    enroll = mod._build_parser()._subparsers._group_actions[0].choices["enroll"]
    dests = {a.dest for a in enroll._actions}
    for forbidden in ("credential_id", "public_key", "public_key_hex", "signer_key_id"):
        assert forbidden not in dests


# ── §26: no recover/import/restore path exists anywhere in this script ──


def test_no_recover_import_restore_subcommand_or_flag(mod):
    sub = mod._build_parser()._subparsers._group_actions[0]
    assert set(sub.choices.keys()) == {"enroll", "revoke"}
    for name, subparser in sub.choices.items():
        dests = {a.dest for a in subparser._actions}
        for forbidden in ("recover", "restore", "import_", "from_file", "from_json", "stdin_evidence"):
            assert forbidden not in dests


# ── §27: revoke non-regression, no FIDO2 ceremony on revoke ──────────


def test_revoke_never_calls_provider_ceremony(mod, monkeypatch, store, tmp_path):
    events: List[str] = []
    _log_ceremony(monkeypatch, mod, events)
    _log_confirm(monkeypatch, mod, events, accept=True)

    # Nothing exists to revoke; expect a clean not-found failure, still zero ceremony calls.
    code = mod.main(
        ["revoke", "--repository-root", str(tmp_path), "--signer-key-id", _CRED_ID, "--enrollment-reference", "CHGR-I"]
    )

    assert code == 1
    assert "provider_ceremony" not in events


def test_revoke_declined_confirmation_no_write(mod, monkeypatch, store, tmp_path):
    events: List[str] = []
    # First register a real credential via the confirmed path so revoke has a target.
    _log_confirm(monkeypatch, mod, events, accept=True)
    _log_ceremony(monkeypatch, mod, events)
    mod.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-J"])

    monkeypatch.setattr(mod, "_prompt_confirm", lambda _d: False)
    code = mod.main(
        ["revoke", "--repository-root", str(tmp_path), "--signer-key-id", _CRED_ID, "--enrollment-reference", "CHGR-K"]
    )
    assert code == 1
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_CRED_ID)
    assert record is not None and record.status == "active"


# ── §32: vulnerable-checkpoint ordering, re-derived on this HEAD's git history ──


def test_vulnerable_checkpoint_ran_ceremony_before_confirmation():
    """Independently re-derives the pre-repair defect from git history
    rather than trusting 2N.1's own claim of `cbcbcc0c`."""
    import subprocess

    parent = subprocess.run(
        ["git", "rev-parse", "9e5981067fc5ba16638a5fe066d66ebcb4e68489^"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    vulnerable_source = subprocess.run(
        ["git", "show", f"{parent}:scripts/hatp_hardware_credential_admin.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    def_start = vulnerable_source.index("def _cmd_enroll")
    body = vulnerable_source[def_start : def_start + 900]
    ceremony_pos = body.index("_run_enrollment_ceremony")
    confirm_pos = body.index("_prompt_confirm") if "_prompt_confirm" in body else body.index("confirmed =")
    assert ceremony_pos < confirm_pos, "vulnerable checkpoint must call the ceremony before confirmation"
