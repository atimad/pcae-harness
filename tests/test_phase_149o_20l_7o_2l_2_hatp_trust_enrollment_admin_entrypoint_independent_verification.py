"""Phase 149O.20L.7O.2L.2 -- HATP Trust-Enrollment Standalone Protected
Admin Entry-Point Independent Verification.

Independently-authored verification suite. Does NOT reuse or extend
`tests/test_hatp_hardware_credential_admin_script.py`,
`tests/test_hatp_principal_signer_admin_script.py`, or
`tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py`
as an oracle -- every assertion here is re-derived directly against
primary source: HHCE-001 v1.1 / HPSE-001 v1.1 contract text (unchanged),
the phase 149O.20L.7O.2L architecture-freeze document (unchanged), the
two scripts' own actual source, and the unmodified core writer modules.

No physical FIDO2/PIV hardware touched. No real HardwareCredentialRecord/
Principal/Signer/DeploymentBinding created. Every writer/provider
interaction uses disposable `tmp_path` state and a monkeypatched
synthetic FIDO2 seam.

This suite documents a Blocking finding (see TestRecoverScopeAndProvenance
below): `recover` is not named by the phase 149O.20L.7O.2L architecture
freeze (which explicitly authorizes only register/revoke for the
hardware script, and explicitly states the recovery path is "retry
register_credential() with the identical evidence already held by the
caller" -- no new external-input mechanism), yet the implemented
`recover` subcommand accepts fully human-typed credential identity
material with no binding to any actual completed hardware ceremony and
persists it as an authoritative HardwareCredentialRecord.
"""
from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core import hatp_principal_signer_admin as ps_admin

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HW_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"
_PS_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py"
_HHCE_CONTRACT = (_REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md").read_text(encoding="utf-8")
_HPSE_CONTRACT = (_REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md").read_text(encoding="utf-8")
_2L_ARCH_DOC = (
    _REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2L_POST_HMIC_ACTIVATION_TRUST_ENROLLMENT_DAG_RE_DERIVATION_AND_ADMINISTRATIVE_ENTRY_POINT_ARCHITECTURE.md"
).read_text(encoding="utf-8")

_SIGNER_KEY_ID = "aa" * 16
_PRINCIPAL_ID = "principal-x"


def _load_hw_module():
    spec = importlib.util.spec_from_file_location("hw_script_2l2", _HW_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_ps_module():
    spec = importlib.util.spec_from_file_location("ps_script_2l2", _PS_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ═══════════════════════════════════════════════════════════════════════════
# 1. Independent CLI grammar reconstruction (§6/§7 of the phase spec)
# ═══════════════════════════════════════════════════════════════════════════


class TestIndependentCliGrammar:
    def test_hardware_script_subcommands_are_exactly_enroll_recover_revoke(self):
        module = _load_hw_module()
        parser = module._build_parser()
        sub = next(a for a in parser._subparsers._group_actions if a.dest == "ceremony")
        assert set(sub.choices.keys()) == {"enroll", "recover", "revoke"}

    def test_principal_signer_script_subcommands_are_exactly_four(self):
        module = _load_ps_module()
        parser = module._build_parser()
        sub = next(a for a in parser._subparsers._group_actions if a.dest == "ceremony")
        assert set(sub.choices.keys()) == {"enroll-principal", "revoke-principal", "enroll-signer", "revoke-signer"}

    @staticmethod
    def _subparser_choices(parser):
        sub_action = next(a for a in parser._subparsers._group_actions if a.dest == "ceremony")
        return sub_action.choices

    def test_enroll_has_no_credential_identity_flags(self):
        module = _load_hw_module()
        parser = module._build_parser()
        choices = self._subparser_choices(parser)
        enroll_actions = {opt for a in choices["enroll"]._actions for opt in a.option_strings}
        for forbidden in ("--signer-key-id", "--public-key-hex", "--algorithm", "--provider-profile"):
            assert forbidden not in enroll_actions

    def test_recover_requires_full_manual_identity_fields(self):
        module = _load_hw_module()
        parser = module._build_parser()
        choices = self._subparser_choices(parser)
        recover_actions = {opt for a in choices["recover"]._actions for opt in a.option_strings}
        for required in ("--signer-key-id", "--public-key-hex", "--algorithm", "--provider-profile", "--protocol-name"):
            assert required in recover_actions

    def test_no_store_root_or_output_override_flag_exists_on_either_script(self):
        for path in (_HW_SCRIPT_PATH, _PS_SCRIPT_PATH):
            module = _load_hw_module() if path is _HW_SCRIPT_PATH else _load_ps_module()
            parser = module._build_parser()
            for sub_parser in self._subparser_choices(parser).values():
                option_strings = {opt for a in sub_parser._actions for opt in a.option_strings}
                for forbidden in ("--store-root", "--output", "--protected-root", "--hardware-store-root"):
                    assert forbidden not in option_strings


# ═══════════════════════════════════════════════════════════════════════════
# 2. Thin-wrapper proof (§8/§9) -- no re-implemented authority logic
# ═══════════════════════════════════════════════════════════════════════════


class TestThinWrapperProof:
    def test_hardware_script_has_no_json_load_dump_or_fcntl_calls(self):
        src = _HW_SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        forbidden_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("dump", "dumps", "load", "loads", "flock"):
                forbidden_calls.add(node.attr)
        assert not forbidden_calls, f"script directly performs registry/lock primitives: {forbidden_calls}"

    def test_principal_signer_script_has_no_json_load_dump_or_fcntl_calls(self):
        src = _PS_SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        forbidden_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("dump", "dumps", "load", "loads", "flock"):
                forbidden_calls.add(node.attr)
        assert not forbidden_calls

    def test_hardware_script_imports_only_core_writer_public_symbols(self):
        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        core_imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("pcae.core")]
        modules = {n.module for n in core_imports}
        assert modules <= {
            "pcae.core.hatp_hardware_credential_admin",
            "pcae.core.hatp_hardware_credentials",
            "pcae.core.hatp_providers",
            "pcae.core.hatp_fido2_provider",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 3. Confirmation boundary -- zero-touch on decline (§22)
# ═══════════════════════════════════════════════════════════════════════════


class TestConfirmationZeroTouch:
    def test_enroll_declined_confirmation_makes_zero_register_calls(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        calls = []
        monkeypatch.setattr(module, "register_credential", lambda **kw: calls.append(kw) or (_ for _ in ()).throw(AssertionError("must not write")))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))

        def fake_ceremony(**kw):
            class _E:
                credential_id_hex = _SIGNER_KEY_ID
                provider_profile = "HATP_HARDWARE_PROVIDER_V1"
                algorithm = "ES256"
                public_key_hex = "bb" * 8
            return _E()

        monkeypatch.setattr(module, "_run_enrollment_ceremony", lambda **kw: fake_ceremony())
        monkeypatch.setattr("builtins.input", lambda: "no")
        code = module.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-1"])
        assert code == 1
        assert calls == []
        assert not (store / "hardware-credentials.json").exists()

    def test_recover_declined_confirmation_makes_zero_write(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        monkeypatch.setattr("builtins.input", lambda: "no")
        code = module.main([
            "recover", "--repository-root", str(tmp_path),
            "--signer-key-id", _SIGNER_KEY_ID, "--provider-profile", "HATP_HARDWARE_PROVIDER_V1",
            "--protocol-name", "FIDO2", "--algorithm", "ES256", "--public-key-hex", "cc" * 8,
            "--enrollment-reference", "CHGR-2",
        ])
        assert code == 1
        assert not (store / "hardware-credentials.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Recovery must not touch hardware (§14)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecoveryNeverTouchesHardware:
    def test_recover_path_never_imports_fido2_provider(self):
        tree = ast.parse(_HW_SCRIPT_PATH.read_text(encoding="utf-8"))
        recover_fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_cmd_recover")
        names_used = {n.id for n in ast.walk(recover_fn) if isinstance(n, ast.Name)}
        attrs_used = {n.attr for n in ast.walk(recover_fn) if isinstance(n, ast.Attribute)}
        assert "_run_enrollment_ceremony" not in names_used
        assert "enroll_credential" not in attrs_used

    def test_recover_makes_zero_calls_into_run_enrollment_ceremony(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        ceremony_calls = []
        monkeypatch.setattr(module, "_run_enrollment_ceremony", lambda **kw: ceremony_calls.append(kw))
        monkeypatch.setattr(module, "register_credential", lambda **kw: hw_admin.register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        code = module.main([
            "recover", "--repository-root", str(tmp_path), "--assume-yes",
            "--signer-key-id", _SIGNER_KEY_ID, "--provider-profile", "HATP_HARDWARE_PROVIDER_V1",
            "--protocol-name", "FIDO2", "--algorithm", "ES256", "--public-key-hex", "cc" * 8,
            "--enrollment-reference", "CHGR-2",
        ])
        assert code == 0
        assert ceremony_calls == []


# ═══════════════════════════════════════════════════════════════════════════
# 5. RECOVER SCOPE + PROVENANCE -- documents the Blocking finding (§18/§19/§43)
# ═══════════════════════════════════════════════════════════════════════════


class TestRecoverScopeAndProvenance:
    def test_hhce_contract_never_mentions_recover(self):
        assert "recover" not in _HHCE_CONTRACT.lower(), (
            "HHCE-001 v1.1 defines no 'recover' operation or concept anywhere in its text "
            "(HHCE-REQ-015 names exactly register_credential/revoke_credential)"
        )

    def test_2l_architecture_doc_names_only_register_revoke_for_hardware_script(self):
        # Phase 149O.20L.7O.2L's own architecture-freeze document, §"Selected
        # design", explicitly enumerates the intended hardware-script CLI
        # surface as "(register/revoke, mirroring hatp_deployment_binding_
        # admin.py's CLI shape ...; never caller-supplied credential ID/
        # public key)" -- a single, unqualified statement, with no carve-out
        # for a separate manual-entry recovery subcommand.
        match = re.search(
            r"`scripts/hatp_hardware_credential_admin\.py` \(register/revoke.*?never caller-supplied credential ID/public key\)\.",
            _2L_ARCH_DOC,
        )
        assert match is not None, "2L architecture doc no longer names exactly register/revoke for the hardware script"
        assert "recover" not in match.group(0)

    def test_2l_architecture_doc_describes_recovery_as_in_process_retry_not_new_cli_surface(self):
        # §6 of the architecture doc: recovery = retrying register_credential()
        # with evidence "already held by the caller" from the SAME failed
        # attempt -- "no additional recovery state machine is required ...
        # not a new mechanism this phase needs to invent."
        assert "no additional recovery state machine is required" in _2L_ARCH_DOC
        assert "not by a new mechanism this phase needs to invent" in _2L_ARCH_DOC

    def test_recover_accepts_fully_fabricated_evidence_with_no_prior_ceremony(self, monkeypatch, tmp_path: Path):
        """BLOCKING FINDING (documented, not repaired in this phase): `recover`
        never verifies that its caller-supplied signer_key_id/public_key_hex
        ever originated from a real hardware ceremony. It is functionally a
        generic, unauthenticated credential-import facility gated only by
        local `--assume-yes`/interactive confirmation -- OS write access is
        the only real boundary, identical to every other field in this
        architecture, but this specific subcommand was never named by the
        149O.20L.7O.2L architecture freeze that authorized these scripts."""
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "register_credential", lambda **kw: hw_admin.register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))

        # Fabricated identity: no `enroll` / `_run_enrollment_ceremony` call
        # of any kind ever occurred for this signer_key_id/public_key_hex.
        fabricated_signer_key_id = "ff" * 16
        fabricated_pubkey_hex = "11" * 32
        code = module.main([
            "recover", "--repository-root", str(tmp_path), "--assume-yes",
            "--signer-key-id", fabricated_signer_key_id,
            "--provider-profile", "HATP_HARDWARE_PROVIDER_V1",
            "--protocol-name", "FIDO2", "--algorithm", "ES256",
            "--public-key-hex", fabricated_pubkey_hex,
            "--enrollment-reference", "CHGR-fabricated",
        ])
        assert code == 0, "recover persisted fully-fabricated, never-ceremony-derived evidence as an authoritative record"
        raw = (store / "hardware-credentials.json").read_text(encoding="utf-8")
        assert fabricated_signer_key_id in raw
        assert fabricated_pubkey_hex in raw


# ═══════════════════════════════════════════════════════════════════════════
# 6. Two-lock live instrumentation (§27) -- enroll-signer
# ═══════════════════════════════════════════════════════════════════════════


class TestTwoLockLiveInstrumentation:
    def test_enroll_signer_acquires_outer_then_inner_lock_continuously(self, monkeypatch, tmp_path: Path):
        events = []
        real_hw_lock = ps_admin.hardware_credential_transition_lock
        real_bind_lock = ps_admin._deployment_binding_transition_lock

        from contextlib import contextmanager

        @contextmanager
        def traced_hw_lock(root):
            events.append(("hw_acquire", root))
            with real_hw_lock(root):
                yield
            events.append(("hw_release", root))

        @contextmanager
        def traced_bind_lock(root):
            events.append(("bind_acquire", root))
            with real_bind_lock(root):
                yield
            events.append(("bind_release", root))

        monkeypatch.setattr(ps_admin, "hardware_credential_transition_lock", traced_hw_lock)
        monkeypatch.setattr(ps_admin, "_deployment_binding_transition_lock", traced_bind_lock)

        hw_store = tmp_path / "hwstore"
        hw_store.mkdir()
        bind_store = tmp_path / "bindstore"
        bind_store.mkdir()

        # Register the hardware credential and principal directly against
        # disposable roots (setup only -- not the code path under test).
        hw_admin.register_credential(
            repository_root=tmp_path,
            evidence=hw_admin.CredentialEnrollmentEvidence(
                signer_key_id=_SIGNER_KEY_ID, provider_profile="HATP_HARDWARE_PROVIDER_V1",
                protocol_name="FIDO2", algorithm="ES256", public_key_hex="ab" * 8,
                enrollment_reference="CHGR-setup",
            ),
            _store_root=hw_store,
        )
        ps_admin.enroll_principal(
            repository_root=tmp_path,
            evidence=ps_admin.PrincipalEnrollmentEvidence(principal_id=_PRINCIPAL_ID, election_reference="CHGR-setup2"),
            _protected_root=bind_store,
        )

        events.clear()
        ps_admin.enroll_signer(
            repository_root=tmp_path,
            evidence=ps_admin.SignerEnrollmentEvidence(
                principal_id=_PRINCIPAL_ID, signer_key_id=_SIGNER_KEY_ID,
                provider_profile="HATP_HARDWARE_PROVIDER_V1", election_reference="CHGR-3",
            ),
            _protected_root=bind_store,
            _hardware_store_root=hw_store,
        )

        kinds = [e[0] for e in events]
        assert kinds == ["hw_acquire", "bind_acquire", "bind_release", "hw_release"], (
            f"expected outer hw lock / inner bind lock nesting, got {kinds}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 7. No DeploymentBinding / HMIC / HATP activation side effects (§34/35/36)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoOutOfScopeSideEffects:
    def test_no_deployment_bindings_file_created_by_hardware_script_ops(self, monkeypatch, tmp_path: Path):
        module = _load_hw_module()
        store = tmp_path / "hwstore"
        store.mkdir()
        monkeypatch.setattr(module, "register_credential", lambda **kw: hw_admin.register_credential(_store_root=store, **kw))
        monkeypatch.setattr(module, "preview_register_credential", lambda **kw: hw_admin.preview_register_credential(_store_root=store, **kw))
        module.main([
            "recover", "--repository-root", str(tmp_path), "--assume-yes",
            "--signer-key-id", _SIGNER_KEY_ID, "--provider-profile", "HATP_HARDWARE_PROVIDER_V1",
            "--protocol-name", "FIDO2", "--algorithm", "ES256", "--public-key-hex", "cc" * 8,
            "--enrollment-reference", "CHGR-2",
        ])
        assert not list(tmp_path.rglob("deployment-bindings.json"))
        assert not list(store.rglob("deployment-bindings.json"))

    def test_neither_script_source_references_create_deployment_binding_or_certify(self):
        for path in (_HW_SCRIPT_PATH, _PS_SCRIPT_PATH):
            src = path.read_text(encoding="utf-8")
            assert "create_deployment_binding(" not in src
            assert re.search(r"\bcertify\(", src) is None
            assert "activate_hatp_mandatory" not in src


# ═══════════════════════════════════════════════════════════════════════════
# 8. Secret-safety (§30)
# ═══════════════════════════════════════════════════════════════════════════


class TestSecretSafety:
    def test_no_secret_like_cli_flag_exists(self):
        for path in (_HW_SCRIPT_PATH, _PS_SCRIPT_PATH):
            src = path.read_text(encoding="utf-8").lower()
            for forbidden in ("--pin", "--private-key", "--secret", "--password", "--bearer-token"):
                assert forbidden not in src
