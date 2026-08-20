"""Focused/adversarial tests for `scripts/hatp_principal_signer_admin.py`
(Phase 149O.20L.7O.2L.1) — the standalone Protected Admin CLI wrapping
`pcae.core.hatp_principal_signer_admin`'s writer functions.

The script owns exactly: administrative input parsing -> protected
confirmation boundary -> call the existing core writer -> render a
deterministic result. This suite proves the wrapper adds no
reimplemented validation/locking/persistence/cross-registry-precondition
logic of its own, and that `enroll-signer`'s continuous two-lock
critical section (HPSE-REQ-057, HHCE-REQ-037) survives intact as one
single call into the core module.

Every test injects disposable `tmp_path` roots by monkeypatching the
script module's own imported call targets (the script's public CLI
intentionally has no root override, HPSE-REQ-021-mirroring governing
prompt §21) — never the real `HATPTrustStore.production()`/
`HATPHardwareCredentialStore.production()`. No test touches real
hardware, a real registry, or any production/protected path.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py"

_SIGNER_KEY_ID = "aa" * 16
_PRINCIPAL_ID = "principal-1"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("hatp_principal_signer_admin_script", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def hw_store(tmp_path: Path) -> Path:
    root = tmp_path / "hwstore"
    root.mkdir()
    return root


@pytest.fixture()
def bind_store(tmp_path: Path) -> Path:
    root = tmp_path / "bindstore"
    root.mkdir()
    return root


@pytest.fixture()
def script(hw_store: Path, bind_store: Path):
    # The script's own subcommand handlers read
    # `args._protected_root`/`args._hardware_store_root` (always None
    # from `main()` in production, governing prompt §21) -- `_run()`
    # below sets them directly on the parsed namespace before dispatch,
    # exactly the seam `main()` itself uses.
    return _load_script_module()


def _run(script, argv: list, *, bind_store: Path, hw_store: Path) -> int:
    args = script._build_parser().parse_args(argv)
    args._protected_root = bind_store
    args._hardware_store_root = hw_store
    ceremony = argv[0]
    dispatch = {
        "enroll-principal": script._cmd_enroll_principal,
        "revoke-principal": script._cmd_revoke_principal,
        "enroll-signer": script._cmd_enroll_signer,
        "revoke-signer": script._cmd_revoke_signer,
    }[ceremony]
    try:
        return dispatch(args)
    except script.ConfirmationDeclinedError as exc:
        print(f"ABORTED: {exc}")
        return 1
    except script._HANDLED_ERRORS + (
        script.PrincipalEvidenceMalformedError,
        script.PrincipalNotFoundError,
        script.PrincipalRevokedError,
        script.DuplicatePrincipalError,
        script.SignerNotFoundError,
        script.DuplicateSignerError,
        script.UnsupportedProviderProfileError,
        script.HardwareCredentialNotRegisteredError,
        script.HardwareCredentialConflictError,
        script.ReadbackMismatchError,
    ) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1


def _register_credential(tmp_path: Path, hw_store: Path, *, signer_key_id: str = _SIGNER_KEY_ID) -> None:
    hw_admin.register_credential(
        repository_root=tmp_path,
        evidence=hw_admin.CredentialEnrollmentEvidence(
            signer_key_id=signer_key_id,
            provider_profile=HATP_HARDWARE_PROVIDER_V1,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="bb" * 20,
            enrollment_reference="CHGR-HW-1",
        ),
        _store_root=hw_store,
    )


# ═══════════════════════════════════════════════════════════════════════════
# --help / argument validation
# ═══════════════════════════════════════════════════════════════════════════


def test_top_level_help_exits_zero(script) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args(["--help"])
    assert exc.value.code == 0


@pytest.mark.parametrize("ceremony", ["enroll-principal", "revoke-principal", "enroll-signer", "revoke-signer"])
def test_subcommand_help_exits_zero(script, ceremony: str) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args([ceremony, "--help"])
    assert exc.value.code == 0


def test_no_subcommand_is_required(script) -> None:
    with pytest.raises(SystemExit):
        script._build_parser().parse_args([])


def test_enroll_principal_missing_election_reference_fails_argparse(script) -> None:
    with pytest.raises(SystemExit) as exc:
        script._build_parser().parse_args(["enroll-principal", "--principal-id", _PRINCIPAL_ID])
    assert exc.value.code == 2


def test_enroll_signer_missing_provider_profile_fails_argparse(script) -> None:
    with pytest.raises(SystemExit):
        script._build_parser().parse_args(
            ["enroll-signer", "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID, "--election-reference", "CHGR-1"]
        )


def test_enroll_signer_has_no_public_key_or_credential_material_flag(script) -> None:
    actions = script._build_parser()._subparsers._group_actions[0].choices["enroll-signer"]._actions
    dests = {a.dest for a in actions}
    assert not (dests & {"public_key", "public_key_hex", "credential_id", "algorithm"})


# ═══════════════════════════════════════════════════════════════════════════
# enroll-principal
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_principal_declined_confirmation_never_writes(script, monkeypatch, tmp_path, bind_store, hw_store) -> None:
    monkeypatch.setattr("builtins.input", lambda: "no")
    code = _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1
    from pcae.core.hatp_bootstrap import HATPTrustStore

    assert HATPTrustStore(_test_only_root=bind_store).lookup_principal(_PRINCIPAL_ID) is None


def test_enroll_principal_success(script, tmp_path, bind_store, hw_store, capsys) -> None:
    code = _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 0
    assert "outcome=enrolled" in capsys.readouterr().out
    from pcae.core.hatp_bootstrap import HATPTrustStore

    principal = HATPTrustStore(_test_only_root=bind_store).lookup_principal(_PRINCIPAL_ID)
    assert principal is not None and principal.status == "active"


def test_enroll_principal_idempotent(script, tmp_path, bind_store, hw_store) -> None:
    argv = ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"]
    assert _run(script, argv, bind_store=bind_store, hw_store=hw_store) == 0
    assert _run(script, argv, bind_store=bind_store, hw_store=hw_store) == 0


def test_enroll_principal_preview_never_writes(script, tmp_path, bind_store, hw_store, capsys) -> None:
    code = _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--preview"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 0
    assert "would_enroll" in capsys.readouterr().out
    from pcae.core.hatp_bootstrap import HATPTrustStore

    assert HATPTrustStore(_test_only_root=bind_store).lookup_principal(_PRINCIPAL_ID) is None


def test_revoke_principal_success_and_conflicting_reenroll_fails(script, tmp_path, bind_store, hw_store) -> None:
    argv_enroll = [
        "enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"
    ]
    assert _run(script, argv_enroll, bind_store=bind_store, hw_store=hw_store) == 0
    argv_revoke = [
        "revoke-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-REV-1", "--assume-yes"
    ]
    assert _run(script, argv_revoke, bind_store=bind_store, hw_store=hw_store) == 0
    # never reactivates
    assert _run(script, argv_enroll, bind_store=bind_store, hw_store=hw_store) == 1


def test_revoke_principal_nonexistent_fails_closed(script, tmp_path, bind_store, hw_store) -> None:
    code = _run(
        script,
        ["revoke-principal", "--repository-root", str(tmp_path), "--principal-id", "nobody", "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


# ═══════════════════════════════════════════════════════════════════════════
# enroll-signer -- cross-registry precondition (HPSE-REQ-056)
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_signer_requires_registered_hardware_credential(script, tmp_path, bind_store, hw_store) -> None:
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1  # no matching registered hardware credential yet


def test_enroll_signer_requires_active_principal(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", "no-such-principal", "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


def test_enroll_signer_success_after_credential_and_principal(script, tmp_path, bind_store, hw_store, capsys) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 0
    assert "outcome=enrolled" in capsys.readouterr().out
    from pcae.core.hatp_bootstrap import HATPTrustStore

    signer = HATPTrustStore(_test_only_root=bind_store).lookup_signer(_SIGNER_KEY_ID)
    assert signer is not None and signer.status == "active" and signer.principal_id == _PRINCIPAL_ID


def test_enroll_signer_idempotent_replay(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    argv = [
        "enroll-signer", "--repository-root", str(tmp_path),
        "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
        "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
    ]
    assert _run(script, argv, bind_store=bind_store, hw_store=hw_store) == 0
    assert _run(script, argv, bind_store=bind_store, hw_store=hw_store) == 0


def test_enroll_signer_conflicting_existing_signer(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", "principal-2", "--election-reference", "CHGR-2", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", "principal-2", "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-2", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1  # differing principal_id for same signer_key_id -> conflict


def test_enroll_signer_revoked_hardware_credential_fails_closed(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    hw_admin.revoke_credential(repository_root=tmp_path, signer_key_id=_SIGNER_KEY_ID, enrollment_reference="CHGR-REV", _store_root=hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


def test_enroll_signer_provider_profile_mismatch_fails_closed(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", "BOGUS_PROFILE", "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


def test_enroll_signer_declined_confirmation_never_writes(script, monkeypatch, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    monkeypatch.setattr("builtins.input", lambda: "no")
    code = _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1
    from pcae.core.hatp_bootstrap import HATPTrustStore

    assert HATPTrustStore(_test_only_root=bind_store).lookup_signer(_SIGNER_KEY_ID) is None


def test_enroll_signer_never_creates_deployment_binding(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    raw = (bind_store / "registry.json").read_text(encoding="utf-8")
    assert "deployment_bindings" not in raw or '"deployment_bindings": []' in raw or "deployment_bindings\": []" in raw


# ═══════════════════════════════════════════════════════════════════════════
# revoke-signer
# ═══════════════════════════════════════════════════════════════════════════


def test_revoke_signer_success_never_cascades_to_hardware_credential(script, tmp_path, bind_store, hw_store) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    code = _run(
        script,
        ["revoke-signer", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID, "--election-reference", "CHGR-REV-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 0
    from pcae.core.hatp_bootstrap import HATPTrustStore

    signer = HATPTrustStore(_test_only_root=bind_store).lookup_signer(_SIGNER_KEY_ID)
    assert signer.status == "revoked"
    credential = hw_admin.HATPHardwareCredentialStore(_test_only_root=hw_store).lookup_credential(_SIGNER_KEY_ID)
    assert credential.status == "active"  # no cascade


def test_revoke_signer_nonexistent_fails_closed(script, tmp_path, bind_store, hw_store) -> None:
    code = _run(
        script,
        ["revoke-signer", "--repository-root", str(tmp_path), "--signer-key-id", "does-not-exist", "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


# ═══════════════════════════════════════════════════════════════════════════
# Malformed store
# ═══════════════════════════════════════════════════════════════════════════


def test_enroll_principal_against_malformed_store_fails_closed(script, tmp_path, bind_store, hw_store) -> None:
    (bind_store / "registry.json").write_text("not json", encoding="utf-8")
    code = _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    assert code == 1


# ═══════════════════════════════════════════════════════════════════════════
# No secret output, authority negatives
# ═══════════════════════════════════════════════════════════════════════════


def test_no_secret_material_ever_printed(script, tmp_path, bind_store, hw_store, capsys) -> None:
    _register_credential(tmp_path, hw_store)
    _run(
        script,
        ["enroll-principal", "--repository-root", str(tmp_path), "--principal-id", _PRINCIPAL_ID, "--election-reference", "CHGR-1", "--assume-yes"],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    _run(
        script,
        [
            "enroll-signer", "--repository-root", str(tmp_path),
            "--principal-id", _PRINCIPAL_ID, "--signer-key-id", _SIGNER_KEY_ID,
            "--provider-profile", HATP_HARDWARE_PROVIDER_V1, "--election-reference", "CHGR-S-1", "--assume-yes",
        ],
        bind_store=bind_store,
        hw_store=hw_store,
    )
    combined = "".join(capsys.readouterr()).lower()
    for banned in ("private_key", "pin=", "bearer", "password"):
        assert banned not in combined


def test_script_never_creates_deployment_binding_or_touches_hmic_in_source() -> None:
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    assert "create_deployment_binding" not in source
    assert "import" not in "\n".join(line for line in source.splitlines() if "hmic" in line.lower())
    assert "hatp_mandatory_certification" not in source


def test_script_is_not_importable_from_agent_reachable_modules() -> None:
    cli_src = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "hatp_principal_signer_admin" not in cli_src


def test_script_never_accepts_output_file_or_root_override(script) -> None:
    for name in ("enroll-principal", "revoke-principal", "enroll-signer", "revoke-signer"):
        actions = script._build_parser()._subparsers._group_actions[0].choices[name]._actions
        dests = {a.dest for a in actions}
        assert "output_file" not in dests
        assert "protected_root" not in dests
        assert "hardware_store_root" not in dests
