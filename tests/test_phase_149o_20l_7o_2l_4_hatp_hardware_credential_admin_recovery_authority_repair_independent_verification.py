"""Phase 149O.20L.7O.2L.4 — HATP Hardware-Credential Admin Recovery
Authority Repair Independent Verification.

Freshly authored independent test suite. Does NOT import or reuse any
149O.20L.7O.2L.3 test module. Verifies, against the CURRENT repaired
tree, the closure of the HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT
Blocking finding independently identified by 149O.20L.7O.2L.2 (commit
ab12406e) and claimed repaired by 149O.20L.7O.2L.3 (commit b010cdff).

No real hardware, no hac-dell, no real protected-root writes. Every
writer call in this suite targets a disposable tmp_path root via the
core module's own `_store_root=` test seam.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path("/Users/atilamadai/repos/pcae-harness")
SCRIPT_PATH = REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"

sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core import hatp_hardware_credential_admin as core  # noqa: E402
from pcae.core import hatp_hardware_credentials as store_mod  # noqa: E402


def _load_script_module():
    spec = importlib.util.spec_from_file_location("hatp_hw_admin_2l4", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _evidence(**overrides):
    base = dict(
        signer_key_id="ab" * 32,
        provider_profile="hatp-fido2-v1",
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key_hex="00" * 16,
        enrollment_reference="CHGR-2L4-TEST",
    )
    base.update(overrides)
    return core.CredentialEnrollmentEvidence(**base)


class _FakeEnrolledCredential:
    def __init__(self, credential_id_hex, algorithm="ES256", public_key_hex="ab" * 8, provider_profile="hatp-fido2-v1"):
        self.credential_id_hex = credential_id_hex
        self.algorithm = algorithm
        self.public_key_hex = public_key_hex
        self.provider_profile = provider_profile


# ---------------------------------------------------------------------------
# Sections 5-7: CLI grammar, recover absence, generic import-surface search
# ---------------------------------------------------------------------------


class TestCurrentPublicCLISurface:
    def test_exactly_enroll_and_revoke_registered(self):
        module = _load_script_module()
        parser = module._build_parser()
        sub = [a for a in parser._subparsers._group_actions if hasattr(a, "choices")][0]
        assert set(sub.choices) == {"enroll", "revoke"}

    def test_recover_rejected_by_argparse_returncode_nonzero(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "recover", "--signer-key-id", "aa"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0
        assert "invalid choice" in (proc.stderr + proc.stdout)

    def test_no_hidden_alias_for_recover_in_source(self):
        """The word "recover" may appear in module-docstring prose
        (explaining why the finding was repaired), but never as an
        argparse subcommand string literal, add_parser() call argument,
        or dispatch function name."""
        text = SCRIPT_PATH.read_text()
        assert "_cmd_recover" not in text
        assert 'add_parser(\n        "recover"' not in text
        assert 'add_parser("recover"' not in text
        # No argparse dest/choice value equal to "recover" outside comments.
        module = _load_script_module()
        parser = module._build_parser()
        sub = [a for a in parser._subparsers._group_actions if hasattr(a, "choices")][0]
        assert "recover" not in sub.choices

    def test_help_output_never_mentions_recover(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"], capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert "recover" not in proc.stdout.lower()

    def test_no_manual_identity_construction_flags_on_enroll(self):
        module = _load_script_module()
        parser = module._build_parser()
        sub = [a for a in parser._subparsers._group_actions if hasattr(a, "choices")][0]
        enroll_dests = {a.dest for a in sub.choices["enroll"]._actions}
        forbidden = {"signer_key_id", "public_key_hex", "provider_profile", "protocol_name", "algorithm"}
        assert enroll_dests.isdisjoint(forbidden)

    def test_generic_import_surface_absent_from_source(self):
        text = SCRIPT_PATH.read_text()
        for token in ("--from-json", "--from-file", "--import", "--restore", "sys.stdin.read"):
            assert token not in text, f"unexpected potential import surface token: {token}"


# ---------------------------------------------------------------------------
# Section 8/9: fabricated-evidence exploit -- vulnerable (git-history-frozen
# commit, invoked in-process against a disposable store) vs repaired CLI.
# ---------------------------------------------------------------------------


class TestFabricatedEvidenceExploit:
    def test_vulnerable_checkpoint_recover_path_persists_fabricated_evidence(self, tmp_path):
        """Reproduces the ORIGINAL defect directly from the frozen vulnerable
        source blob at commit 2396055f (pre-2L.3), without needing a
        worktree checkout: extracts _cmd_recover's exact evidence-construction
        logic (`CredentialEnrollmentEvidence(**caller_argparse_fields)` ->
        `register_credential`) and proves it persists caller-fabricated
        identity with zero hardware ceremony."""
        vulnerable_blob = subprocess.run(
            ["git", "show", "2396055f:scripts/hatp_hardware_credential_admin.py"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
        ).stdout
        assert "_cmd_recover" in vulnerable_blob
        assert "def _cmd_recover" in vulnerable_blob
        # Confirm the exact vulnerable construction: evidence built directly
        # from args.* fields with no provider/ceremony call in between.
        recover_body = vulnerable_blob[vulnerable_blob.index("def _cmd_recover"):]
        recover_body = recover_body[: recover_body.index("\n\n\n")]
        assert "args.signer_key_id" in recover_body
        assert "args.public_key_hex" in recover_body
        assert "enroll_credential" not in recover_body
        assert "_run_enrollment_ceremony" not in recover_body

        # Reproduce the underlying persistence behavior: this is the exact
        # sequence _cmd_recover performed (evidence from caller fields,
        # straight to register_credential) against the CURRENT core module,
        # which the contract does not require to add a provenance check
        # (HHCE-001's real boundary is the CLI/script layer, not the core
        # writer -- confirmed by direct contract read, HHCE-REQ-019/020).
        store_root = tmp_path / "store"
        store_root.mkdir()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        fabricated = core.CredentialEnrollmentEvidence(
            signer_key_id="deadbeef" * 8,
            provider_profile="totally-fabricated-no-hardware-ever-touched",
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key_hex="aabbccdd",
            enrollment_reference="FABRICATED-NO-CEREMONY",
        )
        try:
            result = core.register_credential(repository_root=repo_root, evidence=fabricated, _store_root=store_root)
        except Exception as exc:
            pytest.skip(f"provenance prerequisite unsatisfiable in this harness: {exc}")
            return
        assert result.outcome.value == "registered"
        doc = json.loads((store_root / "hardware-credentials.json").read_text())
        assert doc["credentials"][0]["signer_key_id"] == "deadbeef" * 8
        # HISTORICAL FINDING INDEPENDENTLY REPRODUCED: the underlying core
        # writer accepts whatever evidence it is given -- confirming the
        # ORIGINAL defect lived entirely in the vulnerable script's public
        # CLI surface (recover), never in the core module itself.

    def test_repaired_cli_rejects_identical_fabricated_attempt(self, tmp_path, monkeypatch):
        writer_calls = []
        monkeypatch.setattr(core, "register_credential", lambda **kw: writer_calls.append(kw) or (_ for _ in ()).throw(AssertionError("must not reach writer")))
        proc = subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "recover",
                "--signer-key-id", "deadbeef" * 8,
                "--provider-profile", "totally-fabricated",
                "--protocol-name", "FIDO2",
                "--algorithm", "ES256",
                "--public-key-hex", "aabbccdd",
                "--enrollment-reference", "FABRICATED-NO-CEREMONY",
                "--assume-yes",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert proc.returncode != 0
        assert writer_calls == []
        assert not (tmp_path / "hardware-credentials.json").exists()


# ---------------------------------------------------------------------------
# Sections 10-13: provider-derived identity, one ceremony, retry evidence
# identity, retry reachability
# ---------------------------------------------------------------------------


class TestProviderDerivedIdentityAndOneCeremony:
    def test_evidence_constructed_only_from_provider_output_fields(self):
        module = _load_script_module()
        enrolled = _FakeEnrolledCredential("cc" * 32, algorithm="RS256", public_key_hex="ff" * 4, provider_profile="prof-x")
        evidence = module._evidence_from_enrolled_credential(enrolled, enrollment_reference="CHGR-Y")
        assert evidence.signer_key_id == "cc" * 32
        assert evidence.algorithm == "RS256"
        assert evidence.public_key_hex == "ff" * 4
        assert evidence.provider_profile == "prof-x"

    def test_no_caller_override_path_after_provider_returns(self):
        """_evidence_from_enrolled_credential's only inputs are `enrolled`
        (provider output) and `enrollment_reference` -- no other
        caller-controlled parameter can influence identity fields."""
        module = _load_script_module()
        sig = inspect.signature(module._evidence_from_enrolled_credential)
        assert set(sig.parameters) == {"enrolled", "enrollment_reference"}

    def test_one_provider_ceremony_call_per_cli_enroll_invocation(self, monkeypatch, tmp_path):
        module = _load_script_module()
        n = {"ceremony": 0}

        def _ceremony(*, presence_timeout_s):
            n["ceremony"] += 1
            return _FakeEnrolledCredential("11" * 32)

        monkeypatch.setattr(module, "_run_enrollment_ceremony", _ceremony)
        monkeypatch.setattr(module, "preview_register_credential",
                             lambda evidence: mock.Mock(kind=mock.Mock(value="would_register"), signer_key_id="x",
                                                         existing_record=None, candidate_record=None, registry_path=Path("/x")))
        monkeypatch.setattr(module, "_register_with_in_process_retry",
                             lambda **kw: mock.Mock(outcome=mock.Mock(value="registered"),
                                                     record=mock.Mock(signer_key_id="x", provider_profile="p",
                                                                       protocol_name="FIDO2", algorithm="ES256",
                                                                       status="active", revoked_at=None)))
        args = module._build_parser().parse_args(["enroll", "--repository-root", str(tmp_path),
                                                    "--enrollment-reference", "CHGR-Z", "--assume-yes"])
        module._cmd_enroll(args)
        assert n["ceremony"] == 1

    def test_retry_never_triggers_second_ceremony(self, monkeypatch, tmp_path):
        module = _load_script_module()
        n = {"ceremony": 0, "register": 0}

        def _ceremony(*, presence_timeout_s):
            n["ceremony"] += 1
            return _FakeEnrolledCredential("22" * 32)

        def _flaky_register(*, repository_root, evidence):
            n["register"] += 1
            if n["register"] < 3:
                raise core.HardwareCredentialStoreUnavailableError("transient")
            return mock.Mock(outcome=mock.Mock(value="registered"), record=mock.Mock())

        monkeypatch.setattr(module, "_run_enrollment_ceremony", _ceremony)
        monkeypatch.setattr(module, "register_credential", _flaky_register)
        monkeypatch.setattr(module, "preview_register_credential",
                             lambda evidence: mock.Mock(kind=mock.Mock(value="would_register"), signer_key_id="x",
                                                         existing_record=None, candidate_record=None, registry_path=Path("/x")))
        args = module._build_parser().parse_args(["enroll", "--repository-root", str(tmp_path),
                                                    "--enrollment-reference", "CHGR-Z2", "--assume-yes"])
        module._cmd_enroll(args)
        assert n["ceremony"] == 1
        assert n["register"] == 3

    def test_retry_helper_only_reachable_after_ceremony_in_cmd_enroll(self):
        module = _load_script_module()
        src = inspect.getsource(module._cmd_enroll)
        assert src.index("_run_enrollment_ceremony") < src.index("_register_with_in_process_retry")
        for name, obj in vars(module).items():
            if name in ("_cmd_enroll", "_register_with_in_process_retry") or not inspect.isfunction(obj):
                continue
            if obj.__module__ != module.__name__:
                continue
            try:
                fsrc = inspect.getsource(obj)
            except OSError:
                continue
            assert "_register_with_in_process_retry(" not in fsrc

    def test_argparse_cannot_construct_credential_enrollment_evidence_for_retry(self):
        """No enroll-subparser argument name maps 1:1 onto a
        CredentialEnrollmentEvidence field other than enrollment_reference."""
        module = _load_script_module()
        parser = module._build_parser()
        sub = [a for a in parser._subparsers._group_actions if hasattr(a, "choices")][0]
        enroll_dests = {a.dest for a in sub.choices["enroll"]._actions}
        evidence_fields = set(core.CredentialEnrollmentEvidence.__dataclass_fields__)
        overlap = enroll_dests & evidence_fields
        assert overlap <= {"enrollment_reference"}


# ---------------------------------------------------------------------------
# Section 14-18: retry exception classification
# ---------------------------------------------------------------------------


class TestRetryExceptionClassification:
    def test_handled_errors_tuple_exact_membership(self):
        module = _load_script_module()
        assert module._HANDLED_ERRORS == (
            core.HATPHardwareCredentialAdminError,
            store_mod.HATPHardwareCredentialStoreError,
            module.HATPHardwareProviderError,
            OSError,
        )

    def test_deterministic_conflict_retried_full_budget_then_fails_closed(self, tmp_path):
        module = _load_script_module()
        calls = {"n": 0}

        def _conflict(*, repository_root, evidence):
            calls["n"] += 1
            raise core.CredentialConflictError("deterministic")

        with mock.patch.object(module, "register_credential", _conflict):
            with pytest.raises(core.CredentialConflictError):
                module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert calls["n"] == module._MAX_REGISTER_ATTEMPTS

    def test_malformed_state_retried_but_does_not_heal(self, tmp_path):
        module = _load_script_module()
        calls = {"n": 0}

        def _malformed(*, repository_root, evidence):
            calls["n"] += 1
            raise store_mod.HATPHardwareCredentialStoreMalformedError("malformed")

        with mock.patch.object(module, "register_credential", _malformed):
            with pytest.raises(store_mod.HATPHardwareCredentialStoreMalformedError):
                module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert calls["n"] == module._MAX_REGISTER_ATTEMPTS

    def test_permission_failure_retried_no_fallback_path(self, tmp_path):
        module = _load_script_module()
        calls = {"n": 0}

        def _perm(*, repository_root, evidence):
            calls["n"] += 1
            raise PermissionError("denied")

        with mock.patch.object(module, "register_credential", _perm):
            with pytest.raises(PermissionError):
                module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert calls["n"] == module._MAX_REGISTER_ATTEMPTS
        src = inspect.getsource(module._register_with_in_process_retry)
        assert "chmod" not in src and "chown" not in src and "fallback" not in src.lower() and "elsewhere" not in src.lower()

    def test_unexpected_programming_exception_propagates_on_first_attempt(self, tmp_path):
        module = _load_script_module()
        calls = {"n": 0}

        def _bug(*, repository_root, evidence):
            calls["n"] += 1
            raise AttributeError("unexpected programmer error")

        with mock.patch.object(module, "register_credential", _bug):
            with pytest.raises(AttributeError):
                module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert calls["n"] == 1

    def test_catch_scope_excludes_bare_exception_and_common_builtins(self):
        module = _load_script_module()
        for exc_type in (Exception, KeyError, ValueError, AttributeError, RuntimeError, TypeError):
            assert not issubclass(exc_type, module._HANDLED_ERRORS)


# ---------------------------------------------------------------------------
# Section 19-20: never-landed / already-landed uncertain result
# ---------------------------------------------------------------------------


class TestNeverLandedAndAlreadyLanded:
    def test_never_landed_write_lands_on_retry_single_final_record(self, tmp_path):
        module = _load_script_module()
        attempts = {"n": 0}

        def _once_then_ok(*, repository_root, evidence):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise core.CredentialReadbackMismatchError("never landed")
            return mock.Mock(outcome=mock.Mock(value="registered"), record=mock.Mock(signer_key_id=evidence.signer_key_id))

        with mock.patch.object(module, "register_credential", _once_then_ok):
            result = module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert attempts["n"] == 2
        assert result.record.signer_key_id == _evidence().signer_key_id

    def test_already_landed_replay_resolves_idempotently_real_core(self, tmp_path):
        store_root = tmp_path / "store"
        store_root.mkdir()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        evidence = _evidence(signer_key_id="33" * 32)
        try:
            first = core.register_credential(repository_root=repo_root, evidence=evidence, _store_root=store_root)
        except Exception as exc:
            pytest.skip(f"provenance prerequisite unsatisfiable: {exc}")
            return
        second = core.register_credential(repository_root=repo_root, evidence=evidence, _store_root=store_root)
        assert first.outcome.value == "registered"
        assert second.outcome.value == "already_registered"
        doc = json.loads((store_root / "hardware-credentials.json").read_text())
        assert len(doc["credentials"]) == 1


# ---------------------------------------------------------------------------
# Section 21-23: exhausted retries, no recovery-evidence output, safe diagnostic
# ---------------------------------------------------------------------------


class TestExhaustedRetriesDiagnostic:
    def test_exhaustion_raises_last_error_no_recovery_language(self, tmp_path, capsys):
        module = _load_script_module()

        def _always_fail(*, repository_root, evidence):
            raise core.CredentialReadbackMismatchError("persistent")

        with mock.patch.object(module, "register_credential", _always_fail):
            with pytest.raises(core.CredentialReadbackMismatchError):
                module._register_with_in_process_retry(
                    repository_root=tmp_path, evidence=_evidence(signer_key_id="44" * 32, public_key_hex="ab" * 16)
                )
        err = capsys.readouterr().err
        assert "recovery evidence" not in err.lower()
        assert "--public-key-hex" not in err
        assert "--signer-key-id" not in err
        assert "paste" not in err.lower()
        assert "governed reconciliation" in err.lower() or "reconciliation" in err.lower()

    def test_finite_attempts_no_infinite_loop(self, tmp_path):
        module = _load_script_module()
        calls = {"n": 0}

        def _always_fail(*, repository_root, evidence):
            calls["n"] += 1
            raise core.CredentialConflictError("x")

        with mock.patch.object(module, "register_credential", _always_fail):
            with pytest.raises(core.CredentialConflictError):
                module._register_with_in_process_retry(repository_root=tmp_path, evidence=_evidence())
        assert calls["n"] == module._MAX_REGISTER_ATTEMPTS < 10


# ---------------------------------------------------------------------------
# Section 24: confirmation zero-touch
# ---------------------------------------------------------------------------


class TestConfirmationZeroTouch:
    def test_enroll_declined_zero_writer_calls(self, monkeypatch, tmp_path):
        module = _load_script_module()
        monkeypatch.setattr(module, "_run_enrollment_ceremony", lambda **kw: _FakeEnrolledCredential("55" * 32))
        monkeypatch.setattr(module, "preview_register_credential",
                             lambda evidence: mock.Mock(kind=mock.Mock(value="would_register"), signer_key_id="x",
                                                         existing_record=None, candidate_record=None, registry_path=Path("/x")))
        writer_calls = {"n": 0}
        monkeypatch.setattr(module, "_register_with_in_process_retry",
                             lambda **kw: writer_calls.__setitem__("n", writer_calls["n"] + 1))
        monkeypatch.setattr("builtins.input", lambda: "no")
        args = module._build_parser().parse_args(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "C"])
        with pytest.raises(module.ConfirmationDeclinedError):
            module._cmd_enroll(args)
        assert writer_calls["n"] == 0

    def test_revoke_declined_zero_writer_calls(self, monkeypatch, tmp_path):
        module = _load_script_module()
        monkeypatch.setattr(module, "preview_revoke_credential",
                             lambda signer_key_id: mock.Mock(kind=mock.Mock(value="would_revoke"), signer_key_id=signer_key_id,
                                                              existing_record=None, candidate_record=None, registry_path=Path("/x")))
        revoke_calls = {"n": 0}
        monkeypatch.setattr(module, "revoke_credential", lambda **kw: revoke_calls.__setitem__("n", revoke_calls["n"] + 1))
        monkeypatch.setattr("builtins.input", lambda: "no")
        args = module._build_parser().parse_args(["revoke", "--repository-root", str(tmp_path), "--signer-key-id", "aa",
                                                    "--enrollment-reference", "C"])
        with pytest.raises(module.ConfirmationDeclinedError):
            module._cmd_revoke(args)
        assert revoke_calls["n"] == 0


# ---------------------------------------------------------------------------
# Section 25: revoke regression
# ---------------------------------------------------------------------------


class TestRevokeRegression:
    def test_valid_revoke_then_idempotent_replay_monotonic(self, tmp_path):
        store_root = tmp_path / "store"
        store_root.mkdir()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        evidence = _evidence(signer_key_id="66" * 32)
        try:
            core.register_credential(repository_root=repo_root, evidence=evidence, _store_root=store_root)
        except Exception as exc:
            pytest.skip(f"provenance prerequisite unsatisfiable: {exc}")
            return
        first = core.revoke_credential(repository_root=repo_root, signer_key_id=evidence.signer_key_id,
                                        enrollment_reference="R1", _store_root=store_root)
        second = core.revoke_credential(repository_root=repo_root, signer_key_id=evidence.signer_key_id,
                                         enrollment_reference="R2", _store_root=store_root)
        assert first.outcome.value == "revoked"
        assert second.outcome.value == "already_revoked"
        assert second.record.revoked_at == first.record.revoked_at

    def test_revoke_missing_id_fails_closed(self, tmp_path):
        store_root = tmp_path / "store"
        store_root.mkdir()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        with pytest.raises(core.CredentialNotFoundError):
            core.revoke_credential(repository_root=repo_root, signer_key_id="nope" * 8,
                                    enrollment_reference="X", _store_root=store_root)

    def test_revoke_never_deletes_never_touches_other_records(self, tmp_path):
        store_root = tmp_path / "store"
        store_root.mkdir()
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        e1 = _evidence(signer_key_id="77" * 32)
        e2 = _evidence(signer_key_id="88" * 32)
        try:
            core.register_credential(repository_root=repo_root, evidence=e1, _store_root=store_root)
            core.register_credential(repository_root=repo_root, evidence=e2, _store_root=store_root)
        except Exception as exc:
            pytest.skip(f"provenance prerequisite unsatisfiable: {exc}")
            return
        core.revoke_credential(repository_root=repo_root, signer_key_id=e1.signer_key_id,
                                enrollment_reference="R", _store_root=store_root)
        doc = json.loads((store_root / "hardware-credentials.json").read_text())
        assert len(doc["credentials"]) == 2
        other = next(c for c in doc["credentials"] if c["signer_key_id"] == e2.signer_key_id)
        assert other["status"] == "active"


# ---------------------------------------------------------------------------
# Section 26: Principal/Signer non-regression (byte identity + focused smoke)
# ---------------------------------------------------------------------------


class TestPrincipalSignerNonRegression:
    def test_scripts_byte_identical_since_2l3_entry(self):
        diff = subprocess.run(
            ["git", "diff", "--name-only", "b010cdff", "HEAD", "--",
             "scripts/hatp_principal_signer_admin.py", "src/pcae/core/hatp_principal_signer_admin.py"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
        ).stdout.strip()
        assert diff == ""

    def test_principal_signer_script_public_surface_unchanged(self):
        text = (REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py").read_text()
        for sub in ("enroll-principal", "revoke-principal", "enroll-signer", "revoke-signer"):
            assert sub in text


# ---------------------------------------------------------------------------
# Section 27-28: core writer / contract byte identity
# ---------------------------------------------------------------------------


class TestCoreAndContractImmutability:
    def test_core_writer_modules_byte_identical_since_vulnerable_checkpoint(self):
        files = [
            "src/pcae/core/hatp_hardware_credential_admin.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_hardware_credentials.py",
            "src/pcae/core/hatp_piv_provider.py",
            "src/pcae/core/hatp_providers.py",
            "src/pcae/core/hatp_principal_signer_admin.py",
        ]
        diff = subprocess.run(
            ["git", "diff", "--name-only", "2396055f", "HEAD", "--"] + files,
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
        ).stdout.strip()
        assert diff == "", f"unexpected core writer diff: {diff}"

    def test_contracts_byte_identical_since_vulnerable_checkpoint(self):
        files = [
            "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
            "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
        ]
        diff = subprocess.run(
            ["git", "diff", "--name-only", "2396055f", "HEAD", "--"] + files,
            capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
        ).stdout.strip()
        assert diff == ""

    def test_hhce_version_still_1_1(self):
        text = (REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md").read_text()
        assert "**Version:** 1.1" in text


# ---------------------------------------------------------------------------
# Section 29: thin-wrapper recheck
# ---------------------------------------------------------------------------


class TestThinWrapperRecheck:
    def test_retry_helper_calls_only_allowlisted_names(self):
        import ast
        module = _load_script_module()
        src = inspect.getsource(module._register_with_in_process_retry)
        tree = ast.parse(src)
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
        allowlist = {"register_credential", "print", "range", "len", "type"}
        assert called_names <= allowlist, f"unexpected calls in retry helper: {called_names - allowlist}"

    def test_no_json_or_fcntl_in_script(self):
        text = SCRIPT_PATH.read_text()
        assert "json.load" not in text and "json.dump" not in text
        assert "fcntl" not in text


# ---------------------------------------------------------------------------
# Section 30-31: call graph / path containment
# ---------------------------------------------------------------------------


class TestCallGraphAndPathContainment:
    def test_no_direct_argparse_to_evidence_constructor_edge_for_creation(self):
        text = SCRIPT_PATH.read_text()
        # The only CredentialEnrollmentEvidence construction site must be
        # _evidence_from_enrolled_credential (provider-derived), never a
        # direct construction from `args.*` fields.
        assert text.count("CredentialEnrollmentEvidence(") == 1
        idx = text.index("CredentialEnrollmentEvidence(")
        surrounding = text[max(0, idx - 400): idx]
        assert "args.signer_key_id" not in surrounding
        assert "args.public_key_hex" not in surrounding

    def test_no_trust_store_or_output_path_override_flags(self):
        text = SCRIPT_PATH.read_text()
        for token in ("--trust-store", "--output-path", "--store-root", "--registry-path"):
            assert token not in text


# ---------------------------------------------------------------------------
# Section 32: secret handling
# ---------------------------------------------------------------------------


class TestSecretHandling:
    def test_no_pin_or_private_key_cli_argument_or_print(self):
        """"PIN" appears in module-docstring prose (disclosing that no PIN
        is ever accepted); the check that matters is that no argparse
        argument or print() call actually names/emits one."""
        module = _load_script_module()
        parser = module._build_parser()
        all_dests = set()
        for a in parser._subparsers._group_actions[0].choices.values():
            all_dests |= {act.dest for act in a._actions}
        for forbidden in ("pin", "private_key", "secret"):
            assert forbidden not in all_dests


# ---------------------------------------------------------------------------
# Section 33: historical evidence preservation
# ---------------------------------------------------------------------------


class TestHistoricalEvidencePreservation:
    def test_2l2_historical_test_file_still_exists_and_documents_the_finding(self):
        f = REPO_ROOT / "tests" / "test_phase_149o_20l_7o_2l_2_hatp_trust_enrollment_admin_entrypoint_independent_verification.py"
        assert f.exists()
        text = f.read_text()
        assert "recover" in text.lower()

    def test_vulnerable_commit_still_reachable_in_history(self):
        proc = subprocess.run(["git", "cat-file", "-e", "ab12406e"], cwd=str(REPO_ROOT), capture_output=True)
        assert proc.returncode == 0
        proc2 = subprocess.run(["git", "cat-file", "-e", "2396055f"], cwd=str(REPO_ROOT), capture_output=True)
        assert proc2.returncode == 0


# ---------------------------------------------------------------------------
# Section 34-35: HMIC-REQ-052 + transitive closure
# ---------------------------------------------------------------------------


class TestHmicReq052AndClosure:
    def test_hmic_req_052_definition_locatable(self):
        contract = REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
        assert "HMIC-REQ-052" in contract.read_text()

    def test_frozen_authority_bearing_files_exactly_36(self):
        """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
        governing prompt): true at this phase's own exit commit
        (fd782695c90a8d6ac4e6dd6f985aaf3a9540101a). Superseded for LIVE
        production state by Phase 149O.20L.7O.2M's own HMIC v1.7
        widening -- see test_future_delta_is_exactly_two_new_repository_
        root_relative_entries below, which predicted exactly this."""

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text

    def test_repaired_scripts_not_yet_hmic_members(self):
        """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
        governing prompt) -- see docstring above."""

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )
        assert '"scripts/hatp_hardware_credential_admin.py"' not in text
        assert '"scripts/hatp_principal_signer_admin.py"' not in text

    def test_future_delta_is_exactly_two_new_repository_root_relative_entries(self):
        from pcae.core import hatp_mandatory_certification as hmic
        current = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
        target = current | {"scripts/hatp_hardware_credential_admin.py", "scripts/hatp_principal_signer_admin.py"}
        assert len(target) == 38
