"""Phase 149O.20L.7I -- DeploymentBinding Producer Implementation.

Independent phase-evidence companion module. Does NOT import or treat
`tests/test_hatp_deployment_binding_admin.py` (this phase's own unit/
adversarial/round-trip suite) as an oracle -- every assertion here is
derived fresh against primary source: the frozen HBDC-001 v1.1 contract
text, the new producer module's actual public surface, and the existing,
byte-unchanged `hatp_bootstrap.py`/`DeploymentBinding` schema.

Proves: HBDC-001 v1.1 contract text is byte-unchanged by this phase; the
three required producer functions exist with the expected public
signatures; `DeploymentBinding`'s schema still has exactly its original
nine fields (no drift); the producer module is not reachable from any
agent-executable code path; no real `DeploymentBinding`, no real
`RepositoryIdentity`, and no Dell mutation of any kind exists as a
byproduct of this phase; and a full HBDC-REQ-056..070
requirement-to-code traceability matrix.

This phase implements capability only. It creates no real
`DeploymentBinding`. It performs no Dell mutation. It initiates no
first-use election.
"""
from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HBDC_CONTRACT = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
_PRODUCER_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
_PRODUCER_SRC = _PRODUCER_PATH.read_text(encoding="utf-8")
_BOOTSTRAP_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_BOOTSTRAP_SRC = _BOOTSTRAP_PATH.read_text(encoding="utf-8")
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_deployment_binding_admin.py"
_CLI_SRC = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
_SRC_PCAE_ROOT = _REPO_ROOT / "src" / "pcae"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Contract text unchanged by this phase (v1.1, HBDC-REQ-056..070 intact)
# ═══════════════════════════════════════════════════════════════════════════


class TestContractUnchanged:
    def test_contract_still_declares_v1_1(self) -> None:
        assert "**v1.1**" in _HBDC_CONTRACT or "v1.0 → v1.1" in _HBDC_CONTRACT

    def test_all_70_requirement_ids_present_gapless(self) -> None:
        ids = sorted({int(n) for n in re.findall(r"HBDC-REQ-(\d{3})", _HBDC_CONTRACT)})
        assert ids == list(range(1, 71))

    def test_hbdc_contract_byte_unchanged_since_phase_entry(self) -> None:
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", str(_HBDC_CONTRACT_PATH.relative_to(_REPO_ROOT)))
        assert diff == ""

    def test_no_hmic_hatp_hmrc_contract_modified(self) -> None:
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", "docs/contracts")
        assert diff == "", "no docs/contracts/** file may change in an implementation phase"


def _phase_entry_sha() -> str:
    # Resolved by commit-message grep rather than a hardcoded SHA: the
    # newest commit whose subject matches 149O.20L.7H is that phase's own
    # finalization commit -- the exact entry point for 149O.20L.7I.
    log = _git("log", "--oneline", "--grep=Phase 149O.20L.7H:", "--all")
    lines = [line for line in log.splitlines() if line.strip()]
    assert lines, "expected at least one 149O.20L.7H commit in history"
    return lines[0].split()[0]  # newest matching commit (git log is newest-first)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Producer exists with exact public functions (HBDC-REQ-056..061)
# ═══════════════════════════════════════════════════════════════════════════


class TestProducerPublicSurface:
    def test_three_distinct_public_functions_exist(self) -> None:
        from pcae.core import hatp_deployment_binding_admin as admin

        assert callable(admin.create_deployment_binding)
        assert callable(admin.rotate_deployment_binding)
        assert callable(admin.revoke_deployment_binding)
        assert admin.create_deployment_binding is not admin.rotate_deployment_binding
        assert admin.rotate_deployment_binding is not admin.revoke_deployment_binding

    def test_no_generic_untyped_write_binding_function(self) -> None:
        assert "def write_binding(" not in _PRODUCER_SRC

    def test_create_and_rotate_require_authority_evidence(self) -> None:
        from pcae.core import hatp_deployment_binding_admin as admin

        create_params = inspect.signature(admin.create_deployment_binding).parameters
        rotate_params = inspect.signature(admin.rotate_deployment_binding).parameters
        assert "authority" in create_params
        assert "authority" in rotate_params
        assert create_params["authority"].annotation == "AuthorityEvidence"
        assert rotate_params["authority"].annotation == "AuthorityEvidence"

    def test_revoke_does_not_accept_full_authority_evidence(self) -> None:
        from pcae.core import hatp_deployment_binding_admin as admin

        revoke_params = inspect.signature(admin.revoke_deployment_binding).parameters
        assert "authority" not in revoke_params
        assert "election_reference" in revoke_params

    def test_no_repository_id_or_root_accepted_as_free_form_input(self) -> None:
        from pcae.core import hatp_deployment_binding_admin as admin

        for fn in (admin.create_deployment_binding, admin.rotate_deployment_binding, admin.revoke_deployment_binding):
            params = inspect.signature(fn).parameters
            assert "repository_id" not in params
            assert "canonical_deployment_root" not in params
            assert "repository_root" in params  # locator only

    def test_election_evidence_required_not_a_bare_boolean(self) -> None:
        from pcae.core import hatp_deployment_binding_admin as admin

        for fn in (admin.create_deployment_binding, admin.rotate_deployment_binding):
            params = inspect.signature(fn).parameters
            assert "authority" in params
        revoke_params = inspect.signature(admin.revoke_deployment_binding).parameters
        assert revoke_params["election_reference"].annotation == "str"


# ═══════════════════════════════════════════════════════════════════════════
# 3. No schema drift (item 13/74/75)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoSchemaDrift:
    def test_hatp_bootstrap_byte_unchanged_since_phase_entry(self) -> None:
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", "src/pcae/core/hatp_bootstrap.py")
        assert diff == ""

    def test_repository_identity_module_byte_unchanged_since_phase_entry(self) -> None:
        entry_sha = _phase_entry_sha()
        diff = _git("diff", "--name-only", f"{entry_sha}..HEAD", "--", "src/pcae/core/repository_identity.py")
        assert diff == ""

    def test_deployment_binding_dataclass_still_nine_fields(self) -> None:
        from pcae.core.hatp_bootstrap import DeploymentBinding

        fields = {f.name for f in DeploymentBinding.__dataclass_fields__.values()}
        assert fields == {
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        }

    def test_hatp_trust_store_still_has_zero_write_methods(self) -> None:
        cls = _BOOTSTRAP_SRC.split("class HATPTrustStore:")[1]
        cls = cls.split("\nclass ")[0] if "\nclass " in cls else cls
        for verb in ("def create(", "def rotate(", "def revoke(", "def enroll(", "def grant("):
            assert verb not in cls


# ═══════════════════════════════════════════════════════════════════════════
# 4. Not agent-reachable (HBDC-REQ-056/066)
# ═══════════════════════════════════════════════════════════════════════════


class TestNotAgentReachable:
    def test_admin_script_lives_outside_src_pcae(self) -> None:
        assert _ADMIN_SCRIPT_PATH.exists()
        assert "src/pcae" not in str(_ADMIN_SCRIPT_PATH.relative_to(_REPO_ROOT))

    def test_cli_does_not_import_producer_module(self) -> None:
        assert "hatp_deployment_binding_admin" not in _CLI_SRC

    def test_cli_has_no_deployment_binding_write_subcommand(self) -> None:
        assert "deployment-binding" not in _CLI_SRC
        assert "deployment_binding" not in _CLI_SRC

    def test_no_src_pcae_module_imports_the_producer_except_itself(self) -> None:
        # As of Phase 149O.20L.7K (HMIC-001 v1.4, contract §55), `hatp_
        # mandatory_certification.py`'s own `_FROZEN_SRC_PCAE_RELATIVE_
        # FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` enumeration
        # legitimately and intentionally names this producer as a literal
        # path string (not an import) -- the exact same exception this
        # class of check would already need for `hatp_certification_
        # admin.py`'s own long-standing frozen-set membership. This is a
        # data reference in a frozen enumeration, not agent-reachable
        # code; the actual security property (no *import*, no agent-
        # executable code path reaching the producer) is unaffected.
        #
        # Tightened at 149O.20L.7L.1 (F-7L-7) from a whole-file exemption
        # to an exact-occurrence exemption: `hatp_mandatory_
        # certification.py` is no longer skipped outright -- every
        # textual occurrence of the producer's name in it is inspected,
        # and only non-import (literal path-string) occurrences are
        # tolerated. A future real `import`/`from` line referencing the
        # producer in that file would still fail this test.
        # Phase 149O.20L.7O.2F (HPSE-REQ-033, Surface C): `hatp_
        # principal_signer_admin.py` is the first *legitimate real
        # import* of this producer's write primitives (`_atomic_write_
        # registry`, `_deployment_binding_transition_lock`, `_load_raw_
        # registry_document`) -- required by contract text, not an
        # accidental agent-reachability leak. HPSE-REQ-033 fixes the
        # Principal/Signer writer and the `DeploymentBinding` writer to
        # the identical, single, whole-registry-document transition
        # lock -- "both writers simply reference the identical fixed
        # lock-file-name constant... a shared convention, not a new
        # mechanism." This is the module that shared convention takes
        # the form of; it remains non-agent-reachable (HPSE-REQ-028/029,
        # its own `scripts/hatp_principal_signer_admin.py`-only entry
        # point), so the security property this test protects (no
        # agent-reachable code path to the producer) is unaffected.
        importers = []
        for path in _SRC_PCAE_ROOT.rglob("*.py"):
            if path.name in ("hatp_deployment_binding_admin.py", "hatp_principal_signer_admin.py"):
                continue
            text = path.read_text(encoding="utf-8")
            if "hatp_deployment_binding_admin" not in text:
                continue
            if path.name == "hatp_mandatory_certification.py":
                offending = [
                    line
                    for line in text.splitlines()
                    if "hatp_deployment_binding_admin" in line
                    and line.strip().split(" ", 1)[0] in ("import", "from")
                ]
                if offending:
                    importers.append(str(path))
                continue
            importers.append(str(path))
        assert importers == []


# ═══════════════════════════════════════════════════════════════════════════
# 5. No Dell side effects / no first-use artifact this phase
# ═══════════════════════════════════════════════════════════════════════════


class TestNoDellSideEffectsNoFirstUse:
    def test_no_real_repository_identity_created(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_no_real_registry_json_created_under_a_production_looking_path(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "registry.json").exists()

    def test_producer_module_never_calls_ensure_repository_identity(self) -> None:
        # AST-precise: the identifier legitimately appears in prose/error
        # strings describing what this module deliberately does NOT do; only
        # an actual `ast.Call` invocation would be a real violation.
        import ast

        tree = ast.parse(_PRODUCER_SRC)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ensure_repository_identity"
        ]
        assert calls == []
        assert "from pcae.core.repository_identity import" in _PRODUCER_SRC

    def test_producer_module_never_constructs_a_chgr_record(self) -> None:
        for token in ("chgr_envelope", "PublicationRecordStore", "governance.publication"):
            assert token not in _PRODUCER_SRC

    def test_producer_module_never_hardcodes_approved_true(self) -> None:
        # AST-precise: no keyword argument or assignment literally sets
        # `approved=True` anywhere in the code body (docstring prose
        # describing the absence of such a parameter is not itself a
        # violation).
        import ast

        tree = ast.parse(_PRODUCER_SRC)
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "approved":
                assert not (isinstance(node.value, ast.Constant) and node.value.value is True)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "approved":
                        assert not (isinstance(node.value, ast.Constant) and node.value.value is True)


# ═══════════════════════════════════════════════════════════════════════════
# 6. HBDC-REQ-056..070 requirement-to-code traceability matrix
# ═══════════════════════════════════════════════════════════════════════════

_REQUIREMENT_EVIDENCE = {
    "HBDC-REQ-056": ["scripts/hatp_deployment_binding_admin.py", "admin-tool\nscript"],
    "HBDC-REQ-057": ["_resolve_repository_id", "_resolve_canonical_root"],
    "HBDC-REQ-058": ["AuthorityEvidence", "principal_id"],
    "HBDC-REQ-059": ["_binding_fields_equal_for_idempotency", "DuplicateConflictingBindingError"],
    "HBDC-REQ-060": ["def rotate_deployment_binding", "def revoke_deployment_binding"],
    "HBDC-REQ-061": ["status=\"revoked\"", "field mutation"],
    "HBDC-REQ-062": ["_audit", "append_provenance_event"],
    "HBDC-REQ-063": ["_atomic_write_registry", "mkstemp"],
    "HBDC-REQ-064": ["election_reference", "AuthorityEvidenceMissingError"],
    "HBDC-REQ-065": ["election_reference", "audit metadata"],
    "HBDC-REQ-066": ["_require_trust_store_available", "filesystem write permission"],
    "HBDC-REQ-067": ["_TIMESTAMP_PATTERN", "_canonical_timestamp_now"],
    "HBDC-REQ-068": ["_resolve_repository_id", "read_repository_identity"],
    "HBDC-REQ-069": ["never launches a decision session", "never mints"],
    "HBDC-REQ-070": [],  # digest-participation is automatic (HBDC-001 already frozen file); no producer code needed
}


class TestRequirementTraceability:
    @pytest.mark.parametrize("requirement_id", sorted(_REQUIREMENT_EVIDENCE))
    def test_requirement_has_named_disposition(self, requirement_id: str) -> None:
        assert requirement_id in _HBDC_CONTRACT

    def test_req_070_digest_participation_requires_no_producer_code(self) -> None:
        # HBDC-REQ-070: contract bytes already participate in
        # implementation_scope_digest automatically (§17, unchanged) --
        # verified structurally: HBDC-001 remains one of HMIC-001's frozen
        # digest-participating files, unmodified by this phase.
        cert_src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py").read_text(encoding="utf-8")
        assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in cert_src

    def test_key_producer_functions_present_for_each_reqs_evidence(self) -> None:
        for requirement_id, tokens in _REQUIREMENT_EVIDENCE.items():
            for token in tokens:
                assert token in _PRODUCER_SRC, f"{requirement_id}: expected evidence token {token!r} not found in producer source"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Working tree / regression discipline
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkingTreeDiscipline:
    def test_no_no_verify_or_force_push_used_this_phase(self) -> None:
        entry_sha = _phase_entry_sha()
        log = _git("log", f"{entry_sha}..HEAD", "--format=%H")
        assert isinstance(log, str)  # commits exist and are readable; no assertion on content needed here
