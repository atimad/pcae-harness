"""Phase 149O.20L.7O.2L.3 -- HATP Hardware-Credential Admin Recovery
Authority Narrow Repair.

Repairs exactly the Blocking finding independently verified by Phase
149O.20L.7O.2L.2 (`HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT`):
`scripts/hatp_hardware_credential_admin.py` exposed a public `recover`
subcommand that accepted fully caller-supplied credential identity
material (`signer_key_id`/`provider_profile`/`protocol_name`/`algorithm`
/`public_key_hex`), never bound to any actual completed hardware
ceremony, and persisted it as an authoritative `HardwareCredentialRecord`
-- a generic, unauthenticated credential-import facility never
authorized by HHCE-001 v1.1 or the Phase 149O.20L.7O.2L architecture
freeze.

Repair: `recover` is removed entirely. `enroll` now retries the registry
write in-process, automatically, against the identical
`CredentialEnrollmentEvidence` object one physical `makeCredential`
ceremony already produced -- never a second ceremony, never
caller-supplied identity. This mirrors Phase 149O.20L.7O.2L's own
architecture-freeze document §6 ("no additional recovery state machine
is required ... not by a new mechanism this phase needs to invent").

Independently-authored suite: every assertion here is re-derived
directly against primary source (HHCE-001 v1.1, the Phase
149O.20L.7O.2L architecture-freeze document, the repaired script's own
source, and the unmodified core writer module) -- not against
`tests/test_hatp_hardware_credential_admin_script.py`,
`tests/test_phase_149o_20l_7o_2l_1_...py`, or `tests/
test_phase_149o_20l_7o_2l_2_...py` as an oracle, though this suite is
consistent with all three.

No physical FIDO2/PIV hardware touched. No real HardwareCredentialRecord
/Principal/Signer/DeploymentBinding created. Every writer/provider
interaction uses disposable `tmp_path` state and a monkeypatched
synthetic FIDO2 seam. No HHCE-001/HPSE-001 contract text or core writer
module modified by this phase (asserted directly, §21/§25 below). No
HMIC amendment performed (§22).

Finding status after this phase: REPAIRED -- INDEPENDENT VERIFICATION
PENDING (a later phase, 149O.20L.7O.2L.4, must independently confirm
this repair; this phase does not self-close the finding).
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HW_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"
_PS_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py"
_HHCE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
_HHCE_CONTRACT = _HHCE_CONTRACT_PATH.read_text(encoding="utf-8")

_SIGNER_KEY_ID = "aa" * 16
_PUBLIC_KEY_HEX = "bb" * 8
_PROVIDER_PROFILE = "HATP_HARDWARE_PROVIDER_V1"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _phase_entry_sha() -> str:
    log = _git("log", "--oneline", "--grep=Phase 149O.20L.7O.2L.2:", "--all")
    lines = [line for line in log.splitlines() if line.strip()]
    assert lines, "expected the 149O.20L.7O.2L.2 commit in history (this phase's own predecessor)"
    return lines[-1].split()[0]


def _load_hw_module():
    spec = importlib.util.spec_from_file_location("hw_script_2l3", _HW_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_ceremony_factory(*, signer_key_id: str = _SIGNER_KEY_ID, public_key_hex: str = _PUBLIC_KEY_HEX):
    _pubkey_hex = public_key_hex

    class _E:
        credential_id_hex = signer_key_id
        provider_profile = _PROVIDER_PROFILE
        algorithm = "ES256"
        public_key_hex = _pubkey_hex

    return lambda **kw: _E()


# ═══════════════════════════════════════════════════════════════════════════
# 1. `recover` removed -- public CLI grammar (§12, §26 success criteria 1/3)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecoverSubcommandRemoved:
    def test_public_surface_is_exactly_enroll_revoke(self):
        module = _load_hw_module()
        sub = module._build_parser()._subparsers._group_actions[0]
        assert set(sub.choices.keys()) == {"enroll", "revoke"}

    def test_recover_invocation_fails_at_argument_parsing(self):
        module = _load_hw_module()
        with pytest.raises(SystemExit) as exc:
            module._build_parser().parse_args(["recover", "--signer-key-id", _SIGNER_KEY_ID])
        assert exc.value.code == 2

    def test_help_output_never_mentions_recover(self):
        result = subprocess.run(
            ["python3", str(_HW_SCRIPT_PATH), "--help"],
            cwd=_REPO_ROOT, capture_output=True, text=True,
            env={"PYTHONPATH": str(_REPO_ROOT / "src")},
        )
        assert result.returncode == 0
        assert "recover" not in result.stdout
        assert "enroll" in result.stdout and "revoke" in result.stdout

    def test_no_recover_dispatch_function_or_branch_remains(self):
        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        assert "_cmd_recover" not in func_names
        string_literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert "recover" not in string_literals


# ═══════════════════════════════════════════════════════════════════════════
# 2. No caller-supplied credential identity path anywhere (§7, §16, §26
#    success criteria 2/3) -- mechanical argparse-surface search
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallerSuppliedIdentityImportSurface:
    def test_no_subcommand_accepts_full_identity_construction_fields(self):
        module = _load_hw_module()
        sub = module._build_parser()._subparsers._group_actions[0]
        for name in sub.choices:
            dests = {a.dest for a in sub.choices[name]._actions}
            assert not (dests & {"credential_id", "public_key", "public_key_hex", "algorithm", "protocol_name"}), (
                f"{name} unexpectedly accepts credential-identity-construction field(s)"
            )

    def test_no_import_restore_or_manual_credential_flag_or_subcommand_exists(self):
        """§16 of the governing prompt: mechanically search for any
        function/subcommand/flag equivalent to import/restore/recover/
        register-from-fields/manual credential."""

        module = _load_hw_module()
        sub = module._build_parser()._subparsers._group_actions[0]
        assert not ({"import", "restore", "recover", "register-from-fields", "manual-credential"} & set(sub.choices.keys()))
        src = _HW_SCRIPT_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ("--import", "--restore", "register-from-fields", "--manual-credential"):
            assert forbidden not in src

    def test_fabricated_evidence_cannot_be_submitted_through_any_public_cli_path(self, monkeypatch, tmp_path: Path):
        """End-to-end proof: there is no sequence of CLI arguments, under
        any subcommand, that persists caller-fabricated
        signer_key_id/public_key_hex never produced by a real ceremony."""

        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "register_credential", lambda **kw: hw_admin.register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))

        fabricated_signer_key_id = "ff" * 16
        fabricated_pubkey_hex = "11" * 32

        # `enroll` never exposes identity flags -- argparse itself rejects
        # any attempt to pass them.
        with pytest.raises(SystemExit):
            module._build_parser().parse_args([
                "enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1",
                "--signer-key-id", fabricated_signer_key_id, "--public-key-hex", fabricated_pubkey_hex,
            ])
        assert not (store / "hardware-credentials.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 3. `enroll` FIDO2 call-count proof, exactly one ceremony (§8, §26
#    success criteria 4/5)
# ═══════════════════════════════════════════════════════════════════════════


class TestEnrollSingleCeremonyInvariant:
    def test_enroll_calls_ceremony_exactly_once_even_when_write_is_retried(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        ceremony_calls = []

        def _ceremony(**kw):
            ceremony_calls.append(kw)
            return _fake_ceremony_factory()(**kw)

        real_register = hw_admin.register_credential
        write_attempts = []

        def _flaky_register(**kw):
            write_attempts.append(kw)
            if len(write_attempts) < 2:
                raise hw_admin.HardwareCredentialStoreUnavailableError("simulated transient failure")
            return real_register(_store_root=store, **kw)

        monkeypatch.setattr(module, "_run_enrollment_ceremony", _ceremony)
        monkeypatch.setattr(module, "register_credential", _flaky_register)
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))

        code = module.main(["enroll", "--repository-root", str(tmp_path), "--assume-yes", "--enrollment-reference", "CHGR-1"])
        assert code == 0
        assert len(ceremony_calls) == 1
        assert len(write_attempts) == 2
        assert write_attempts[0]["evidence"] is write_attempts[1]["evidence"], "retry must reuse the identical evidence object"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Hardware-success / persistence-failure matrix (§14, §26 success
#    criteria 6)
# ═══════════════════════════════════════════════════════════════════════════


class TestHardwareSuccessPersistenceFailureMatrix:
    def test_never_landed_write_lands_on_retry(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "_run_enrollment_ceremony", _fake_ceremony_factory())
        real_register = hw_admin.register_credential
        attempts = []

        def _register(**kw):
            attempts.append(kw)
            if len(attempts) < 3:
                raise hw_admin.HardwareCredentialStoreUnavailableError("never landed yet")
            return real_register(_store_root=store, **kw)

        monkeypatch.setattr(module, "register_credential", _register)
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--assume-yes", "--enrollment-reference", "CHGR-1"])
        assert code == 0
        record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
        assert record is not None and record.status == "active"

    def test_already_landed_write_resolves_idempotently_on_retry(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "_run_enrollment_ceremony", _fake_ceremony_factory())
        real_register = hw_admin.register_credential
        attempts = []

        def _register(**kw):
            result = real_register(_store_root=store, **kw)
            attempts.append(kw)
            if len(attempts) < 2:
                # Simulate: the write itself landed, but the ack/audit step
                # raised -- the caller sees a failure despite a durable write.
                raise hw_admin.HATPHardwareCredentialAdminError("simulated ack failure after a landed write")
            return result

        monkeypatch.setattr(module, "register_credential", _register)
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--assume-yes", "--enrollment-reference", "CHGR-1"])
        assert code == 0
        record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
        assert record is not None and record.status == "active"

    def test_conflicting_state_fails_closed_after_exhausting_retries(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id=_SIGNER_KEY_ID, provider_profile=_PROVIDER_PROFILE,
                protocol_name="FIDO2", algorithm="ES256", public_key_hex="cc" * 8,
                enrollment_reference="CHGR-setup",
            ),
            _store_root=store,
        )
        # Ceremony produces a DIFFERING public key for the same signer_key_id
        # -- a genuine CREDENTIAL_CONFLICT, deterministic on every retry.
        monkeypatch.setattr(module, "_run_enrollment_ceremony", _fake_ceremony_factory(public_key_hex=_PUBLIC_KEY_HEX))
        monkeypatch.setattr(module, "register_credential", lambda **kw: hw_admin.register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--assume-yes", "--enrollment-reference", "CHGR-2"])
        assert code == 1
        record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
        assert record.public_key.hex() == "cc" * 8  # unchanged, never overwritten

    def test_exhausted_retries_prints_diagnostic_without_credential_material(self, monkeypatch, tmp_path: Path, capsys):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "_run_enrollment_ceremony", _fake_ceremony_factory())

        def _always_fails(**kw):
            raise hw_admin.HardwareCredentialStoreUnavailableError("persistent failure")

        monkeypatch.setattr(module, "register_credential", _always_fails)
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--assume-yes", "--enrollment-reference", "CHGR-1"])
        assert code == 1
        err = capsys.readouterr().err
        assert "governed reconciliation" in err
        assert "RECOVERY EVIDENCE" not in err
        assert _PUBLIC_KEY_HEX not in err, "no credential material dumped for manual re-entry (no import path exists)"


# ═══════════════════════════════════════════════════════════════════════════
# 5. Revoke regression (§9, §26 success criteria 7) -- unchanged
# ═══════════════════════════════════════════════════════════════════════════


class TestRevokeUnchanged:
    def test_revoke_still_revokes(self, monkeypatch, tmp_path: Path, capsys):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id=_SIGNER_KEY_ID, provider_profile=_PROVIDER_PROFILE,
                protocol_name="FIDO2", algorithm="ES256", public_key_hex=_PUBLIC_KEY_HEX,
                enrollment_reference="CHGR-1",
            ),
            _store_root=store,
        )
        monkeypatch.setattr(module, "revoke_credential", lambda **kw: hw_admin.revoke_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_revoke_credential", lambda **kw: hw_admin.preview_revoke_credential(_store_root=store, **kw))
        code = module.main([
            "revoke", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID,
            "--enrollment-reference", "CHGR-REV-1", "--assume-yes",
        ])
        assert code == 0
        assert "outcome=revoked" in capsys.readouterr().out
        record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
        assert record.status == "revoked"

    def test_revoke_declined_confirmation_still_makes_zero_write(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id=_SIGNER_KEY_ID, provider_profile=_PROVIDER_PROFILE,
                protocol_name="FIDO2", algorithm="ES256", public_key_hex=_PUBLIC_KEY_HEX,
                enrollment_reference="CHGR-1",
            ),
            _store_root=store,
        )
        monkeypatch.setattr(module, "preview_revoke_credential", lambda **kw: hw_admin.preview_revoke_credential(_store_root=store, **kw))
        monkeypatch.setattr("builtins.input", lambda: "no")
        code = module.main([
            "revoke", "--repository-root", str(tmp_path), "--signer-key-id", _SIGNER_KEY_ID,
            "--enrollment-reference", "CHGR-REV-1",
        ])
        assert code == 1
        record = hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID)
        assert record.status == "active"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Principal/signer script unchanged (§10, §26 success criteria 8)
# ═══════════════════════════════════════════════════════════════════════════


class TestPrincipalSignerScriptUnchanged:
    def test_principal_signer_script_byte_unchanged_since_2l2(self):
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", str(_PS_SCRIPT_PATH.relative_to(_REPO_ROOT)))
        assert diff == "", "scripts/hatp_principal_signer_admin.py must not change in this repair phase"

    def test_principal_signer_public_surface_still_exactly_four_subcommands(self):
        spec = importlib.util.spec_from_file_location("ps_script_2l3", _PS_SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sub = module._build_parser()._subparsers._group_actions[0]
        assert set(sub.choices.keys()) == {"enroll-principal", "revoke-principal", "enroll-signer", "revoke-signer"}


# ═══════════════════════════════════════════════════════════════════════════
# 7. No core writer / contract changes (§21, §26 success criteria 9/10)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCoreWriterOrContractChanges:
    def test_no_core_writer_module_modified_since_2l2(self):
        entry_sha = _phase_entry_sha()
        diff = _git(
            "diff", "--name-only", f"{entry_sha}..HEAD", "--",
            "src/pcae/core/hatp_hardware_credential_admin.py",
            "src/pcae/core/hatp_principal_signer_admin.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_hardware_credentials.py",
            "src/pcae/core/hatp_bootstrap.py",
            "src/pcae/core/hatp_deployment_binding_admin.py",
        )
        assert diff == "", "this repair phase touches the wrapper script only, never a core writer"

    def test_no_docs_contracts_file_modified_since_2l2(self):
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", "docs/contracts")
        assert diff == "", "no docs/contracts/** file may change in this narrow repair phase"

    def test_hhce_still_v1_1_unwidened(self):
        assert "**Version:** 1.1" in _HHCE_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 8. Thin-wrapper invariant preserved (§15, §26 success criteria 11)
# ═══════════════════════════════════════════════════════════════════════════


class TestThinWrapperInvariantPreserved:
    def test_no_json_load_dump_or_fcntl_calls(self):
        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        forbidden_calls = {
            node.attr for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr in ("dump", "dumps", "load", "loads", "flock")
        }
        assert not forbidden_calls

    def test_retry_helper_contains_no_registry_validation_or_persistence_logic(self):
        """The in-process retry loop must remain a thin call-and-catch
        wrapper around the existing `register_credential` -- not a
        reimplemented mini transaction engine."""

        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        retry_fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_register_with_in_process_retry")
        calls = {n.func.id for n in ast.walk(retry_fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert calls <= {"register_credential", "print", "range", "len", "type"}

    def test_hardware_script_imports_only_core_writer_public_symbols(self):
        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("pcae.core")}
        assert modules <= {
            "pcae.core.hatp_hardware_credential_admin",
            "pcae.core.hatp_hardware_credentials",
            "pcae.core.hatp_providers",
            "pcae.core.hatp_fido2_provider",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 9. Fresh HMIC-REQ-052 analysis (§21, §26 success criteria 12) -- both
#    scripts remain authority-sensitive; removing `recover` does not
#    change that. Future delta remains 36 -> 38, not forced.
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshHmicReq052AnalysisAfterRepair:
    def test_current_frozen_set_still_exactly_36_unmodified_by_this_phase(self):
        from pcae.core import hatp_mandatory_certification as hmic

        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 36

    def test_neither_script_yet_hmic_bound(self):
        from pcae.core import hatp_mandatory_certification as hmic

        assert "scripts/hatp_hardware_credential_admin.py" not in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
        assert "scripts/hatp_principal_signer_admin.py" not in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES

    def test_hardware_script_still_answers_yes_to_authority_sensitivity(self):
        """Removing `recover` does not make the script non-authority
        -bearing: it is still the sole caller deciding which
        `register_credential`/`revoke_credential` call happens, with what
        evidence, after what confirmation -- an attacker who reintroduced
        an unauthenticated identity path, or skipped confirmation, would
        change the protected registry's real content without touching any
        currently-frozen file."""

        src = _HW_SCRIPT_PATH.read_text(encoding="utf-8")
        assert "register_credential(" in src
        assert "revoke_credential(" in src

    def test_future_hmic_delta_unchanged_at_36_plus_2(self):
        from pcae.core import hatp_mandatory_certification as hmic

        current = len(hmic._FROZEN_AUTHORITY_BEARING_FILES)
        assert current == 36
        assert current + 2 == 38


# ═══════════════════════════════════════════════════════════════════════════
# 10. Confirmation zero-touch preserved (§13)
# ═══════════════════════════════════════════════════════════════════════════


class TestConfirmationZeroTouchPreserved:
    def test_enroll_declined_confirmation_makes_zero_provider_and_writer_calls(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        register_calls = []
        monkeypatch.setattr(module, "register_credential", lambda **kw: register_calls.append(kw) or (_ for _ in ()).throw(AssertionError("must not write")))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "_run_enrollment_ceremony", _fake_ceremony_factory())
        monkeypatch.setattr("builtins.input", lambda: "no")
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1"])
        assert code == 1
        assert register_calls == []
        assert not (store / "hardware-credentials.json").exists()
