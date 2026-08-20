"""Focused/adversarial tests for `scripts/hatp_hardware_credential_admin.py`
(Phase 149O.20L.7O.2L.1) — the standalone Protected Admin CLI wrapping
`pcae.core.hatp_hardware_credential_admin`'s writer functions and
`Fido2HardwareProvider.enroll_credential()`'s ceremony.

The script owns exactly: administrative input parsing -> protected
confirmation boundary -> call the existing core writer -> render a
deterministic result. This suite proves the wrapper adds no
reimplemented record parsing/validation/locking/persistence/duplicate-
detection/revocation logic of its own, and that the `enroll`/`recover`
recovery split (governing prompt §9/§10/§27) behaves as designed.

Every test injects a disposable `tmp_path` hardware-credential-store
root by monkeypatching the script module's own imported call targets
(the script's public CLI intentionally has no `--store-root`/
`--output-file` override, HHCE-REQ-021/governing prompt §21) — never
`HATPHardwareCredentialStore.production()`. `_run_enrollment_ceremony`
is monkeypatched to a synthetic FIDO2 ceremony seam; no test touches
real hardware or any production/protected path.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

fido2 = pytest.importorskip("fido2")

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core.hatp_fido2_provider import EnrolledFido2Credential
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, HATPProviderDeviceError, HATPProviderUnavailableError

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"

_SIGNER_KEY_ID = "aa" * 16
_PUBLIC_KEY_HEX = "bb" * 20


def _load_script_module():
    spec = importlib.util.spec_from_file_location("hatp_hardware_credential_admin_script", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bind_store(func, store_root: Path):
    def wrapper(*args, **kwargs):
        kwargs.setdefault("_store_root", store_root)
        return func(*args, **kwargs)

    return wrapper


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    root = tmp_path / "hwstore"
    root.mkdir()
    return root


@pytest.fixture()
def script(monkeypatch: pytest.MonkeyPatch, store: Path):
    module = _load_script_module()
    monkeypatch.setattr(module, "register_credential", _bind_store(hw_admin.register_credential, store))
    monkeypatch.setattr(module, "revoke_credential", _bind_store(hw_admin.revoke_credential, store))
    monkeypatch.setattr(module, "preview_register_credential", _bind_store(hw_admin.preview_register_credential, store))
    monkeypatch.setattr(module, "preview_revoke_credential", _bind_store(hw_admin.preview_revoke_credential, store))
    return module


def _fake_ceremony(monkeypatch: pytest.MonkeyPatch, module, *, credential_id_hex: str = _SIGNER_KEY_ID):
    def _ceremony(*, presence_timeout_s: float):
        return EnrolledFido2Credential(
            credential_id_hex=credential_id_hex,
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
        )

    monkeypatch.setattr(module, "_run_enrollment_ceremony", _ceremony)


# ═══════════════════════════════════════════════════════════════════════════
# --help / argument validation
# ═══════════════════════════════════════════════════════════════════════════


def test_top_level_help_exits_zero(script, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args(["--help"])
    assert exc.value.code == 0


@pytest.mark.parametrize("ceremony", ["enroll", "recover", "revoke"])
def test_subcommand_help_exits_zero(script, ceremony: str) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args([ceremony, "--help"])
    assert exc.value.code == 0


def test_no_subcommand_is_required(script) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args([])
    assert exc.value.code != 0


def test_enroll_missing_enrollment_reference_fails_argparse(script) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args(["enroll", "--repository-root", "."])
    assert exc.value.code == 2


def test_recover_missing_required_fields_fails_argparse(script) -> None:
    with pytest.raises(SystemExit):
        script._build_parser().parse_args(["recover", "--signer-key-id", _SIGNER_KEY_ID])


def test_recover_rejects_unsupported_protocol_name(script) -> None:
    with pytest.raises(SystemExit):
        script._build_parser().parse_args(
            [
                "recover",
                "--signer-key-id", _SIGNER_KEY_ID,
                "--provider-profile", HATP_HARDWARE_PROVIDER_V1,
                "--protocol-name", "BOGUS",
                "--algorithm", "ES256",
                "--public-key-hex", _PUBLIC_KEY_HEX,
                "--enrollment-reference", "CHGR-1",
            ]
        )


def test_no_credential_id_or_public_key_flag_on_enroll(script) -> None:
    """Governing prompt §10/§11: normal enrollment never accepts
    caller-supplied credential identity."""

    enroll_actions = {a.dest for a in script._build_parser()._subparsers._group_actions[0].choices["enroll"]._actions}
    assert "credential_id" not in enroll_actions
    assert "public_key" not in enroll_actions
    assert "public_key_hex" not in enroll_actions


# ═══════════════════════════════════════════════════════════════════════════
# enroll: synthetic FIDO2 success, declined confirmation, --preview
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_declined_confirmation_never_writes(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    _fake_ceremony(monkeypatch, script)
    monkeypatch.setattr("builtins.input", lambda: "no")
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1"])
    assert code == 1
    err = capsys.readouterr().err
    assert "ABORTED" in err
    assert "RECOVERY EVIDENCE" in err
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


def test_enroll_preview_never_writes(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    _fake_ceremony(monkeypatch, script)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--preview"])
    assert code == 0
    out = capsys.readouterr().out
    assert "would_register" in out
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


def test_enroll_success_with_assume_yes_registers_credential(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    _fake_ceremony(monkeypatch, script)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    assert code == 0
    out = capsys.readouterr().out
    assert "outcome=registered" in out
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record is not None
    assert record.status == "active"
    # no secret material printed
    assert "private" not in out.lower()


def test_enroll_confirmed_via_prompt_registers_credential(script, monkeypatch, store: Path, tmp_path: Path) -> None:
    _fake_ceremony(monkeypatch, script)
    monkeypatch.setattr("builtins.input", lambda: "yes")
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1"])
    assert code == 0
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is not None


def test_enroll_no_device_raises_unavailable_and_never_writes(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    def _raise_unavailable(*, presence_timeout_s: float):
        raise HATPProviderUnavailableError("no FIDO2 CTAP2 HID device detected")

    monkeypatch.setattr(script, "_run_enrollment_ceremony", _raise_unavailable)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    assert code == 1
    assert "HATPProviderUnavailableError" in capsys.readouterr().err
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


# ═══════════════════════════════════════════════════════════════════════════
# enroll: hardware success + persistence failure -> RECOVERY EVIDENCE,
# then safe retry via `recover` using identical evidence (governing
# prompt §9).
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_persistence_failure_prints_recovery_evidence(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    _fake_ceremony(monkeypatch, script)

    def _boom(*, repository_root, evidence):
        raise hw_admin.HardwareCredentialStoreUnavailableError("simulated persistence failure")

    monkeypatch.setattr(script, "register_credential", _boom)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    assert code == 1
    err = capsys.readouterr().err
    assert "RECOVERY EVIDENCE" in err
    assert f"--signer-key-id {_SIGNER_KEY_ID}" in err
    assert f"--public-key-hex {_PUBLIC_KEY_HEX}" in err
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


def test_recover_with_identical_evidence_after_simulated_failure_is_safe(script, tmp_path: Path, store: Path) -> None:
    """The core writer's own `_candidate_equal` idempotency (HHCE-REQ-016)
    makes a `recover` retry with identical evidence safe whether or not
    the original write actually landed."""

    # Simulate the original `enroll` having actually durably succeeded
    # (the case where persistence failed only in the audit step, or the
    # operator is unsure) by registering once directly first.
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=_SIGNER_KEY_ID,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            enrollment_reference="CHGR-1",
        ),
        _store_root=store,
    )

    code = script.main(
        [
            "recover",
            "--repository-root", str(tmp_path),
            "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1,
            "--protocol-name", "FIDO2",
            "--algorithm", "ES256",
            "--public-key-hex", _PUBLIC_KEY_HEX,
            "--enrollment-reference", "CHGR-1-retry",
            "--assume-yes",
        ]
    )
    assert code == 0
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record is not None
    assert record.status == "active"


def test_recover_from_scratch_when_original_write_never_landed(script, tmp_path: Path, store: Path) -> None:
    code = script.main(
        [
            "recover",
            "--repository-root", str(tmp_path),
            "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1,
            "--protocol-name", "FIDO2",
            "--algorithm", "ES256",
            "--public-key-hex", _PUBLIC_KEY_HEX,
            "--enrollment-reference", "CHGR-1",
            "--assume-yes",
        ]
    )
    assert code == 0
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is not None


def test_recover_with_conflicting_evidence_fails_closed_no_duplicate(script, tmp_path: Path, store: Path) -> None:
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=_SIGNER_KEY_ID,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            enrollment_reference="CHGR-1",
        ),
        _store_root=store,
    )
    code = script.main(
        [
            "recover",
            "--repository-root", str(tmp_path),
            "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1,
            "--protocol-name", "FIDO2",
            "--algorithm", "ES256",
            "--public-key-hex", "cc" * 20,  # differs -> conflict
            "--enrollment-reference", "CHGR-2",
            "--assume-yes",
        ]
    )
    assert code == 1
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record.public_key.hex() == _PUBLIC_KEY_HEX  # unchanged, never overwritten


def test_two_enroll_ceremonies_never_silently_collapse_into_one_record(script, monkeypatch, store: Path, tmp_path: Path) -> None:
    """No second credential creation where recovery evidence exists for
    the first: two genuinely distinct ceremonies produce two distinct
    records."""

    _fake_ceremony(monkeypatch, script, credential_id_hex=_SIGNER_KEY_ID)
    code1 = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    assert code1 == 0

    _fake_ceremony(monkeypatch, script, credential_id_hex="dd" * 16)
    code2 = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-2", "--assume-yes"])
    assert code2 == 0

    hwstore = hw_admin.HATPHardwareCredentialStore(_test_only_root=store)
    assert hwstore.lookup_credential(_SIGNER_KEY_ID) is not None
    assert hwstore.lookup_credential("dd" * 16) is not None


# ═══════════════════════════════════════════════════════════════════════════
# revoke
# ═══════════════════════════════════════════════════════════════════════════


def test_revoke_declined_confirmation_never_writes(script, monkeypatch, store: Path, tmp_path: Path) -> None:
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=_SIGNER_KEY_ID,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            enrollment_reference="CHGR-1",
        ),
        _store_root=store,
    )
    monkeypatch.setattr("builtins.input", lambda: "no")
    code = script.main(["revoke", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID, "--enrollment-reference", "CHGR-REV-1"])
    assert code == 1
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record.status == "active"


def test_revoke_nonexistent_fails_closed(script, tmp_path: Path) -> None:
    code = script.main(
        ["revoke", "--repository-root", str(tmp_path), "--signer-key-id", "does-not-exist", "--enrollment-reference", "CHGR-1", "--assume-yes"]
    )
    assert code == 1


def test_revoke_success(script, tmp_path: Path, store: Path, capsys) -> None:
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=_SIGNER_KEY_ID,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            enrollment_reference="CHGR-1",
        ),
        _store_root=store,
    )
    code = script.main(
        ["revoke", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID, "--enrollment-reference", "CHGR-REV-1", "--assume-yes"]
    )
    assert code == 0
    assert "outcome=revoked" in capsys.readouterr().out
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record.status == "revoked"


def test_revoke_preview_never_writes(script, tmp_path: Path, store: Path, capsys) -> None:
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=_SIGNER_KEY_ID,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex=_PUBLIC_KEY_HEX,
            enrollment_reference="CHGR-1",
        ),
        _store_root=store,
    )
    code = script.main(
        ["revoke", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID, "--enrollment-reference", "CHGR-REV-1", "--preview"]
    )
    assert code == 0
    assert "would_revoke" in capsys.readouterr().out
    record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
    assert record.status == "active"


# ═══════════════════════════════════════════════════════════════════════════
# Malformed store
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_against_malformed_store_fails_closed(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    (store / "hardware-credentials.json").write_text("not json", encoding="utf-8")
    _fake_ceremony(monkeypatch, script)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    assert code == 1
    assert "Malformed" in capsys.readouterr().err


# ═══════════════════════════════════════════════════════════════════════════
# No secret output, no unrelated protected write, authority negatives
# ═══════════════════════════════════════════════════════════════════════════


def test_no_secret_material_ever_printed(script, monkeypatch, store: Path, tmp_path: Path, capsys) -> None:
    _fake_ceremony(monkeypatch, script)
    script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1", "--assume-yes"])
    combined = "".join(capsys.readouterr())
    for banned in ("private_key", "PIN", "bearer", "secret", "password", "token"):
        assert banned.lower() not in combined.lower() or banned == "token" and "enrollment_reference" not in combined  # sanity guard only


def test_script_has_no_pin_or_password_cli_flags(script) -> None:
    for name in ("enroll", "recover", "revoke"):
        actions = script._build_parser()._subparsers._group_actions[0].choices[name]._actions
        dests = {a.dest for a in actions}
        assert not (dests & {"pin", "password", "private_key", "token"})


def test_script_never_creates_deployment_binding_or_touches_hmic() -> None:
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    assert "DeploymentBinding" not in source
    assert "create_deployment_binding" not in source
    assert "hmic" not in source.lower()


def test_script_is_not_importable_from_agent_reachable_modules() -> None:
    cli_src = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "hatp_hardware_credential_admin" not in cli_src


def test_script_never_accepts_output_file_or_store_root_override(script) -> None:
    for name in ("enroll", "recover", "revoke"):
        actions = script._build_parser()._subparsers._group_actions[0].choices[name]._actions
        dests = {a.dest for a in actions}
        assert "output_file" not in dests
        assert "store_root" not in dests
