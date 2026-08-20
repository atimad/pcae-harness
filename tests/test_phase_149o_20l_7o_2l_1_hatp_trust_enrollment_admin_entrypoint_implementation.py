"""Phase 149O.20L.7O.2L.1 -- HATP Trust-Enrollment Standalone Protected
Admin Entry-Point Implementation.

Independent phase-evidence companion module (does NOT import or treat
`tests/test_hatp_hardware_credential_admin_script.py`/`tests/
test_hatp_principal_signer_admin_script.py` -- this phase's own focused
suites -- as an oracle; every assertion here is derived fresh against
primary source: the frozen HHCE-001 v1.1/HPSE-001 v1.1 contract text
(byte-unchanged by this phase), the two new scripts' actual public
surface, and the current `hatp_mandatory_certification.py` frozen
source-scope constants).

Implements exactly `scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py` as thin, fail-closed Protected
Admin CLI wrappers over the already-implemented, already-HMIC-bound core
writers (`pcae.core.hatp_hardware_credential_admin`, `pcae.core.
hatp_principal_signer_admin`). No physical FIDO2/PIV hardware touched by
this test module. No real HardwareCredentialRecord/Principal/Signer/
DeploymentBinding created. No HMIC scope change performed. No Dell
redeployment. No HATP activation.
"""
from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HHCE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
_HPSE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HHCE_CONTRACT = _HHCE_CONTRACT_PATH.read_text(encoding="utf-8")
_HPSE_CONTRACT = _HPSE_CONTRACT_PATH.read_text(encoding="utf-8")
_HW_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"
_PS_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_principal_signer_admin.py"
_HW_SCRIPT_SRC = _HW_SCRIPT_PATH.read_text(encoding="utf-8")
_PS_SCRIPT_SRC = _PS_SCRIPT_PATH.read_text(encoding="utf-8")
_CLI_SRC = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _phase_entry_sha() -> str:
    log = _git("log", "--oneline", "--grep=Phase 149O.20L.7O.2L:", "--all")
    lines = [line for line in log.splitlines() if line.strip()]
    assert lines, "expected at least one 149O.20L.7O.2L commit in history"
    return lines[-1].split()[0]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Contracts byte-unchanged by this implementation phase
# ═══════════════════════════════════════════════════════════════════════════


class TestContractsUnchanged:
    def test_hhce_still_v1_1(self) -> None:
        assert "**Version:** 1.1" in _HHCE_CONTRACT

    def test_hpse_still_v1_1(self) -> None:
        assert "**Version:** 1.1" in _HPSE_CONTRACT

    def test_all_hhce_requirement_ids_present_gapless(self) -> None:
        ids = sorted({int(n) for n in re.findall(r"HHCE-REQ-(\d{3})", _HHCE_CONTRACT)})
        assert ids == list(range(1, 53))

    def test_all_hpse_requirement_ids_present_gapless(self) -> None:
        ids = sorted({int(n) for n in re.findall(r"HPSE-REQ-(\d{3})", _HPSE_CONTRACT)})
        assert ids == list(range(1, 75))

    def test_no_docs_contracts_file_modified(self) -> None:
        """Pinned to this phase's own entry/exit commits (§26 of the
        149O.20L.7O.2M governing prompt: historical snapshot,
        preserved) -- not `..HEAD`, which a later, separately-governed
        phase (149O.20L.7O.2M) legitimately advances past."""

        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..c97a07b2", "--", "docs/contracts")
        assert diff == "", "no docs/contracts/** file may change in an implementation phase"

    def test_no_core_writer_module_modified(self) -> None:
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
        assert diff == "", "this phase implements wrapper scripts only, never the core writers"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Scripts exist, are standalone, are thin (no reimplemented logic)
# ═══════════════════════════════════════════════════════════════════════════


class TestScriptsExistAndAreStandalone:
    def test_both_scripts_exist_outside_src_pcae(self) -> None:
        assert _HW_SCRIPT_PATH.is_file()
        assert _PS_SCRIPT_PATH.is_file()
        assert "src/pcae" not in str(_HW_SCRIPT_PATH.relative_to(_REPO_ROOT))
        assert "src/pcae" not in str(_PS_SCRIPT_PATH.relative_to(_REPO_ROOT))

    def test_neither_script_imported_by_agent_reachable_modules(self) -> None:
        assert "hatp_hardware_credential_admin" not in _CLI_SRC
        assert "hatp_principal_signer_admin" not in _CLI_SRC
        agent_src = (_REPO_ROOT / "src" / "pcae" / "commands" / "agent.py").read_text(encoding="utf-8")
        core_agent_src = (_REPO_ROOT / "src" / "pcae" / "core" / "agent.py").read_text(encoding="utf-8")
        for src in (agent_src, core_agent_src):
            assert "hatp_hardware_credential_admin" not in src
            assert "hatp_principal_signer_admin" not in src

    def test_scripts_never_reimplement_atomic_write_or_locking(self) -> None:
        for src in (_HW_SCRIPT_SRC, _PS_SCRIPT_SRC):
            assert "fcntl" not in src
            assert "mkstemp" not in src
            assert "os.replace" not in src

    def test_scripts_never_parse_registry_json_directly(self) -> None:
        for src in (_HW_SCRIPT_SRC, _PS_SCRIPT_SRC):
            assert "json.load" not in src
            assert "json.dump" not in src

    def test_hardware_script_imports_only_core_writer_public_surface(self) -> None:
        import ast

        tree = ast.parse(_HW_SCRIPT_SRC)
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert modules <= {
            "__future__", "argparse", "sys", "pathlib", "typing",
            "pcae.core.hatp_hardware_credential_admin",
            "pcae.core.hatp_hardware_credentials",
            "pcae.core.hatp_providers",
            "pcae.core.hatp_fido2_provider",
        }

    def test_principal_signer_script_imports_only_core_writer_public_surface(self) -> None:
        import ast

        tree = ast.parse(_PS_SCRIPT_SRC)
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert modules <= {
            "__future__", "argparse", "sys", "pathlib", "typing",
            "pcae.core.hatp_bootstrap",
            "pcae.core.hatp_hardware_credentials",
            "pcae.core.hatp_principal_signer_admin",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 3. No real effect proof
# ═══════════════════════════════════════════════════════════════════════════


class TestNoRealEffect:
    def test_neither_script_creates_deployment_binding(self) -> None:
        for src in (_HW_SCRIPT_SRC, _PS_SCRIPT_SRC):
            assert "create_deployment_binding" not in src
            assert "DeploymentBinding(" not in src

    def test_neither_script_performs_hmic_certification_action(self) -> None:
        for src in (_HW_SCRIPT_SRC, _PS_SCRIPT_SRC):
            assert "hatp_mandatory_certification" not in src
            assert "certify" not in src.lower()

    def test_neither_script_calls_fido2_request_signature_or_verify(self) -> None:
        """These scripts enroll/register/revoke identity records; they
        never themselves produce or verify a signing assertion."""

        assert "request_signature" not in _HW_SCRIPT_SRC
        assert ".verify(" not in _HW_SCRIPT_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 4. HHCE-REQ-019/020 & HPSE-REQ-028/029 -- standalone, admin-only,
#    never a `pcae` subcommand
# ═══════════════════════════════════════════════════════════════════════════


class TestProtectedAdminBoundary:
    def test_hardware_script_has_own_main_and_is_directly_executable(self) -> None:
        assert 'if __name__ == "__main__":' in _HW_SCRIPT_SRC
        assert "def main(" in _HW_SCRIPT_SRC

    def test_principal_signer_script_has_own_main_and_is_directly_executable(self) -> None:
        assert 'if __name__ == "__main__":' in _PS_SCRIPT_SRC
        assert "def main(" in _PS_SCRIPT_SRC

    def test_hardware_script_help_runs_out_of_process(self) -> None:
        result = subprocess.run(
            ["python3", str(_HW_SCRIPT_PATH), "--help"],
            cwd=_REPO_ROOT, capture_output=True, text=True,
            env={"PYTHONPATH": str(_REPO_ROOT / "src")},
        )
        assert result.returncode == 0
        assert "enroll" in result.stdout and "revoke" in result.stdout
        assert "recover" not in result.stdout, (
            "Phase 149O.20L.7O.2L.3 removed the `recover` subcommand (independently verified "
            "Blocking finding, Phase 149O.20L.7O.2L.2)"
        )

    def test_principal_signer_script_help_runs_out_of_process(self) -> None:
        result = subprocess.run(
            ["python3", str(_PS_SCRIPT_PATH), "--help"],
            cwd=_REPO_ROOT, capture_output=True, text=True,
            env={"PYTHONPATH": str(_REPO_ROOT / "src")},
        )
        assert result.returncode == 0
        assert "enroll-principal" in result.stdout and "enroll-signer" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# 5. Continuous two-lock critical section preserved (HHCE-REQ-037,
#    HPSE-REQ-057) -- the script never decomposes `enroll_signer`'s own
#    call into multiple pieces; it is one function call.
# ═══════════════════════════════════════════════════════════════════════════


class TestTwoLockCriticalSectionPreserved:
    def test_enroll_signer_called_exactly_once_as_a_single_function_call(self) -> None:
        import ast

        tree = ast.parse(_PS_SCRIPT_SRC)
        call_sites = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "enroll_signer"
        ]
        assert len(call_sites) == 1
        # No manual lock acquisition anywhere in the script -- the
        # continuous two-lock hold is entirely internal to the one
        # `enroll_signer()` call this script makes.
        assert "hardware_credential_transition_lock" not in _PS_SCRIPT_SRC
        assert "_deployment_binding_transition_lock" not in _PS_SCRIPT_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 6. HHCE-REQ-012/§10 -- no caller-supplied credential identity anywhere
#    on the hardware script's public surface. Originally, `recover` was
#    the named exception accepting full manual identity fields; Phase
#    149O.20L.7O.2L.2 independently verified that this made `recover` a
#    generic, unauthenticated credential-import facility (Blocking
#    finding), and Phase 149O.20L.7O.2L.3 removed it entirely -- no
#    subcommand accepts caller-supplied credential identity now.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallerSuppliedCredentialIdentityOnNormalPath:
    def test_enroll_subcommand_never_declares_credential_identity_flags(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("hw_script_ast_check", _HW_SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        enroll_actions = module._build_parser()._subparsers._group_actions[0].choices["enroll"]._actions
        dests = {a.dest for a in enroll_actions}
        assert not (dests & {"credential_id", "public_key", "public_key_hex", "signer_key_id"})

    def test_no_subcommand_anywhere_accepts_credential_identity_fields(self) -> None:
        """Repaired boundary (Phase 149O.20L.7O.2L.3): no subcommand on
        the hardware script's public surface -- not `enroll`, not
        `revoke`, and there is no longer a `recover` subcommand at all --
        accepts caller-supplied `signer_key_id`/`provider_profile`/
        `algorithm`/`public_key_hex` for record CREATION. (`revoke`
        legitimately takes `signer_key_id` to target an EXISTING record
        for revocation, not to construct new identity material -- it
        never accepts `public_key_hex`/`algorithm`/`provider_profile`.)"""

        import importlib.util

        spec = importlib.util.spec_from_file_location("hw_script_ast_check_2", _HW_SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sub = module._build_parser()._subparsers._group_actions[0]
        assert set(sub.choices.keys()) == {"enroll", "revoke"}
        for name, forbidden in (
            ("enroll", {"signer_key_id", "provider_profile", "algorithm", "public_key_hex"}),
            ("revoke", {"provider_profile", "algorithm", "public_key_hex"}),
        ):
            dests = {a.dest for a in sub.choices[name]._actions}
            assert not (dests & forbidden), f"{name} unexpectedly accepts identity-construction field(s): {dests & forbidden}"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Fresh HMIC-REQ-052 analysis (governing prompt §30/§31) -- performed
#    independently against current production `hatp_mandatory_
#    certification.py`, not merely restated from Phase 149O.20L.7O.2L's
#    own prose. Confirms the analysis's conclusion, performs NO HMIC
#    amendment (this file lives in tests/, changes nothing in
#    hatp_mandatory_certification.py or any contract).
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshHmicReq052Analysis:
    def test_current_frozen_set_is_still_exactly_36_unmodified_by_this_phase(self) -> None:
        """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
        governing prompt): true of the phase-149O.20L.7O.2L.1-exit
        commit, superseded for LIVE production state by Phase
        149O.20L.7O.2M's own HMIC v1.7 widening (36 -> 38), which is the
        exact future action this phase's own docstring anticipated."""

        import subprocess

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text

    def test_new_scripts_are_not_yet_hmic_bound(self) -> None:
        """This phase performed NO HMIC action (governing prompt §29/§33):
        the two new scripts were deliberately left out of the frozen set
        at THIS phase's own exit. Historical snapshot, preserved (§26 of
        the 149O.20L.7O.2M governing prompt) -- superseded for LIVE
        production state by Phase 149O.20L.7O.2M's own HMIC v1.7
        widening, the exact future action anticipated below."""

        import subprocess

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )
        assert '"scripts/hatp_hardware_credential_admin.py"' not in text
        assert '"scripts/hatp_principal_signer_admin.py"' not in text

    def test_both_core_writer_modules_the_scripts_call_are_already_hmic_bound(self) -> None:
        """The scripts' entire mutating surface routes through modules
        already inside `_FROZEN_SRC_PCAE_RELATIVE_FILES` -- meaning an
        attacker modifying ONLY the new scripts, with every currently
        frozen v1.6 member byte-identical, changes what administrative
        CLI ceremony reaches those already-bound writers: the writers'
        own authority is unchanged, but which invocation of them is
        possible is script-controlled. This is exactly why the scripts
        themselves are, independently, authority-sensitive."""

        from pcae.core import hatp_mandatory_certification as hmic

        assert "core/hatp_hardware_credential_admin.py" in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES
        assert "core/hatp_principal_signer_admin.py" in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES

    def test_scripts_answer_yes_to_the_governing_prompt_30_question(self) -> None:
        """"If an attacker/developer modified only this script while
        every current HMIC v1.6 frozen member remained byte-identical,
        could the protected Trust-Enrollment result change?" -- YES for
        both scripts: each is the sole, real, standalone administrative
        ceremony (HHCE-REQ-020/HPSE-REQ-029) that decides WHICH
        `register_credential`/`revoke_credential`/`enroll_principal`/
        `enroll_signer`/`revoke_principal`/`revoke_signer` call happens,
        with what evidence, after what confirmation -- an attacker who
        rewrote e.g. `_cmd_enroll` to skip the confirmation prompt, or
        `recover` to accept mismatched evidence silently, would change
        the protected registry's real content without touching any
        currently-frozen file. Confirmed structurally here: each script
        is the one and only call site invoking its core writer's
        mutating operations from outside the core module itself."""

        for src, funcs in (
            (_HW_SCRIPT_SRC, ("register_credential(", "revoke_credential(")),
            (_PS_SCRIPT_SRC, ("enroll_principal(", "revoke_principal(", "enroll_signer(", "revoke_signer(")),
        ):
            for func in funcs:
                assert func in src, f"expected {func} to be called by this admin script"

    def test_exact_future_hmic_delta_is_the_two_new_scripts_only(self) -> None:
        """Governing prompt §31: derive the exact closure, not merely
        assume it is two files. Both scripts' own import graphs (AST
        Section 2 tests above) resolve entirely within the set of
        modules ALREADY inside `_FROZEN_SRC_PCAE_RELATIVE_FILES` --
        `hatp_hardware_credential_admin`/`hatp_principal_signer_admin`
        (already bound), `hatp_hardware_credentials`/`hatp_bootstrap`
        (already bound, being read-only registry siblings of the already
        -bound writers), `hatp_providers`/`hatp_fido2_provider` (already
        bound). No new, not-yet-bound transitive dependency is
        introduced -- unlike the paths.py precedent this governing
        prompt explicitly warns against repeating, where a call-graph
        edge to an UNFROZEN module was initially missed. The exact
        expected future HMIC-REQ-050 count is therefore 36 + 2 = 38,
        both additions in `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`
        (repository-root-relative, mirroring `scripts/hatp_certification_
        admin.py`/`scripts/hatp_deployment_binding_admin.py`'s own
        existing binding precedent), never `_FROZEN_SRC_PCAE_RELATIVE_
        FILES` (that constant is `src/pcae/`-relative only, and these
        scripts live outside `src/pcae/` by design, HHCE-REQ-019/
        HPSE-REQ-028)."""

        import subprocess

        from pcae.core import hatp_mandatory_certification as hmic

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:src/pcae/core/hatp_mandatory_certification.py"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        )
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text
        historical_count = 36
        expected_future = historical_count + 2
        assert expected_future == 38
        # Phase 149O.20L.7O.2M performed exactly this predicted widening;
        # confirmed against LIVE production state, not merely restated.
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == expected_future


# ═══════════════════════════════════════════════════════════════════════════
# 8. No secret material anywhere in the scripts' static source (defense
#    in depth alongside the runtime tests in the two focused suites).
# ═══════════════════════════════════════════════════════════════════════════


class TestNoSecretMaterialInSource:
    def test_no_pin_or_password_or_private_key_cli_flags(self) -> None:
        for src in (_HW_SCRIPT_SRC, _PS_SCRIPT_SRC):
            assert "--pin" not in src
            assert "--password" not in src
            assert "--private-key" not in src
            assert "--bearer-token" not in src
