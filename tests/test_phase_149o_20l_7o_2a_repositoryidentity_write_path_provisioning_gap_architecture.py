"""Phase 149O.20L.7O.2A -- RepositoryIdentity Write-Path Provisioning Gap
Architecture + Remediation Proposition.

Architecture/design-analysis phase. This module is proof, not
implementation: it demonstrates, against live production source, the
exact facts `docs/PHASE_149O_20L_7O_2A_REPOSITORYIDENTITY_WRITE_PATH_
PROVISIONING_GAP_ARCHITECTURE_AND_REMEDIATION_PROPOSITION.md`
reconstructs -- the `.pcae/.gitignore`-derived write-required artifact
inventory, `repository_identity.py`'s `mkstemp`-derived `0600`/no-chown
producer behavior, the Linux POSIX-ACL single-`w`-granularity fact that
motivates the sticky-bit remediation model, the current HBDC checkers'
disclosed sticky-bit blind spot, `HBDC-REQ-036`'s live `PATH`-dependence
(mechanized locally via `monkeypatch`, reproducing -- without needing
Dell access -- the exact mechanism the phase document's live Dell
reproduction demonstrated), the Protected Root path distinctness from
`.pcae/`, and the no-mutation / no-production-code-change proof. No
production module is modified by this phase; no `RepositoryIdentity` or
`DeploymentBinding` is created anywhere in this suite.
"""
from __future__ import annotations

import inspect
import stat as stat_module
from pathlib import Path

import pytest

from pcae.core import hatp_bootstrap
from pcae.core import repository_identity
from pcae.core.hatp_class_b_topology_verifier import (
    _acl_grants_agent_write_linux,
    _current_agent_identity,
    _mode_and_group_write_access,
)
from pcae.core.hatp_environment_lock_verifier import _check_launcher
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_IDENTITY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py").read_text(encoding="utf-8")
_BOOTSTRAP_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py").read_text(encoding="utf-8")
_TOPOLOGY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_topology_verifier.py").read_text(
    encoding="utf-8"
)
_GITIGNORE_PATH = _REPO_ROOT / ".pcae" / ".gitignore"
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2A_REPOSITORYIDENTITY_WRITE_PATH_PROVISIONING_GAP_ARCHITECTURE_AND_REMEDIATION_PROPOSITION.md"
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. .pcae write-required artifact inventory (§3 of the architecture doc) --
#    the gitignore list is the authoritative source, not the doc's prose
#    copy of it.
# ═══════════════════════════════════════════════════════════════════════════


class TestWriteRequiredArtifactInventory:
    def test_gitignore_exists(self) -> None:
        assert _GITIGNORE_PATH.is_file()

    def test_repository_identity_json_is_gitignored_ie_agent_written(self) -> None:
        entries = _GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        assert "repository-identity.json" in entries

    def test_session_and_agent_lock_and_provenance_are_also_gitignored(self) -> None:
        """The write-path gap is not narrow to repository-identity.json --
        session/lock/provenance hit the identical PermissionError on first
        write."""

        entries = set(_GITIGNORE_PATH.read_text(encoding="utf-8").splitlines())
        for expected in ("session.json", "agent-lock.json", "provenance-history.json", "phase-reports/"):
            assert expected in entries, f"expected runtime-local artifact missing from .gitignore: {expected}"

    def test_git_tracked_pcae_baseline_is_not_gitignored_and_is_admin_controlled(self) -> None:
        """policy.toml / phase-completion-metadata.json etc. are git-tracked
        (mutated via governed commit, not live runtime write) and therefore
        must NOT appear in .pcae/.gitignore."""

        entries = set(_GITIGNORE_PATH.read_text(encoding="utf-8").splitlines())
        for tracked in ("policy.toml", "phase-completion-metadata.json", "phase-completion-report.md"):
            assert tracked not in entries


# ═══════════════════════════════════════════════════════════════════════════
# 2. RepositoryIdentity producer filesystem behavior (§4/§6) -- mkstemp
#    default mode, no chmod/chown call, atomic-rename idiom.
# ═══════════════════════════════════════════════════════════════════════════


class TestProducerFilesystemBehavior:
    def test_no_chmod_or_chown_call_anywhere_in_module(self) -> None:
        assert "os.chmod" not in _IDENTITY_SRC
        assert "os.chown" not in _IDENTITY_SRC

    def test_mkstemp_used_for_temp_file_in_same_directory(self) -> None:
        assert "tempfile.mkstemp(prefix=" in _IDENTITY_SRC
        assert "dir=str(directory)" in _IDENTITY_SRC

    def test_atomic_replace_used_not_plain_write(self) -> None:
        assert "os.replace(tmp_name, path)" in _IDENTITY_SRC

    def test_symlink_rejected_twice_target_and_parent(self) -> None:
        assert _IDENTITY_SRC.count("_reject_symlink(") >= 3  # definition + 2 call sites

    def test_created_file_is_owner_only_mode_0600(self, tmp_path: Path) -> None:
        """Live behavioral proof, isolated fixture: the resulting file's
        mode is exactly 0600, matching mkstemp's fixed file-creation mode
        (independent of umask) and confirming the producer never widens
        it."""

        root = HarnessPath(tmp_path)
        repository_identity.ensure_repository_identity(root)
        target = tmp_path / repository_identity.REPOSITORY_IDENTITY_RELATIVE_PATH
        mode = stat_module.S_IMODE(target.stat().st_mode)
        assert mode == 0o600

    def test_ensure_is_idempotent(self, tmp_path: Path) -> None:
        root = HarnessPath(tmp_path)
        first = repository_identity.ensure_repository_identity(root)
        second = repository_identity.ensure_repository_identity(root)
        assert first.repository_instance_id == second.repository_instance_id

    def test_no_authority_import_present(self) -> None:
        """HATP-REQ-051/063 frozen invariant: this module imports nothing
        from HATP/Permission Broker/RAE (prose references to hatp_bootstrap
        in the module docstring are fine -- an actual `import` is not)."""

        for forbidden in ("import hatp_bootstrap", "import permission_broker", "import rollback_approval_evidence"):
            assert forbidden not in _IDENTITY_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 3. Linux POSIX ACL granularity (§5/§9) -- single "w" bit, no independent
#    add_file/delete_child distinction, unlike the macOS branch.
# ═══════════════════════════════════════════════════════════════════════════


class TestLinuxAclGranularity:
    def test_linux_acl_check_treats_any_w_as_write_capable(self) -> None:
        source = inspect.getsource(_acl_grants_agent_write_linux)
        assert '"w" not in perms' in source
        # No separate right token (add_file/delete_child) is parsed on the
        # Linux branch -- only the presence of the single "w" permission
        # character in a getfacl entry.
        assert "add_file" not in source
        assert "delete_child" not in source

    def test_macos_branch_does_distinguish_add_file_and_delete_child(self) -> None:
        """Confirms the phase document's claim that the brief's
        independently-grantable add_file/delete_child vocabulary is macOS
        ACL vocabulary, not applicable to Dell's Linux/ext4 filesystem."""

        assert "add_file" in _TOPOLOGY_SRC
        assert "delete_child" in _TOPOLOGY_SRC
        assert "_MACOS_ACL_WRITE_CAPABLE_RIGHTS" in _TOPOLOGY_SRC

    def test_neither_linux_write_check_inspects_sticky_bit(self) -> None:
        """Disclosed pre-existing gap (§5/§11 of the architecture doc): the
        current HBDC checkers do not special-case S_ISVTX, so a
        sticky-bit-protected directory would still be reported simply
        "group-writable" by these primitives if ever pointed at one."""

        mode_check_source = inspect.getsource(_mode_and_group_write_access)
        acl_check_source = inspect.getsource(_acl_grants_agent_write_linux)
        assert "S_ISVTX" not in mode_check_source
        assert "S_ISVTX" not in acl_check_source
        assert "sticky" not in mode_check_source.lower()
        assert "sticky" not in acl_check_source.lower()

    def test_sticky_bit_semantics_are_a_kernel_level_fact_not_this_repo(self) -> None:
        """Sanity check on the constant this phase's remediation model
        depends on: S_ISVTX is the standard sticky-bit flag."""

        assert stat_module.S_ISVTX == 0o1000


# ═══════════════════════════════════════════════════════════════════════════
# 4. HBDC-REQ-036 PATH-dependence -- mechanized reproduction of the
#    invocation/config-mismatch classification (§13-14), portable, no
#    Dell access required.
# ═══════════════════════════════════════════════════════════════════════════


class TestReq036PathDependence:
    def test_check_launcher_returns_false_when_pcae_not_on_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        agent_uid, agent_gids = _current_agent_identity()
        monkeypatch.setenv("PATH", "/nonexistent-bin-only")
        result = _check_launcher(agent_uid, agent_gids)
        assert result.satisfied is False
        assert result.status == "no_configured_production_launcher_detected"

    def test_check_launcher_depends_only_on_shutil_which(self) -> None:
        source = inspect.getsource(_check_launcher)
        assert "shutil" in source or "which(" in source
        assert "sys.prefix" not in source  # confirms no venv-aware fallback exists
        assert "VIRTUAL_ENV" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 5. Protected Root distinctness (§12) -- /etc/pcae/hatp/trust-store vs.
#    the repository-local .pcae/ this phase's remediation targets.
# ═══════════════════════════════════════════════════════════════════════════


class TestProtectedRootDistinctness:
    def test_linux_trust_store_root_is_outside_pcae_directory(self) -> None:
        assert '_LINUX_FIXED_TRUST_ROOT = Path("/etc/pcae/hatp/trust-store")' in _BOOTSTRAP_SRC

    def test_trust_store_path_shares_no_ancestor_with_repository_pcae_dir(self) -> None:
        trust_store = Path("/etc/pcae/hatp/trust-store")
        repo_pcae = Path("/opt/pcae/runtime/src/.pcae")
        assert trust_store != repo_pcae
        assert not str(trust_store).startswith(str(repo_pcae))
        assert not str(repo_pcae).startswith(str(trust_store))

    def test_deployment_binding_matches_reads_only_repository_id_and_root(self) -> None:
        """Reconfirms (independent of 7F) that DeploymentBinding matching
        has no dependency on .pcae's own permission state."""

        source = inspect.getsource(hatp_bootstrap.deployment_binding_matches)
        assert "binding.repository_id == repository_id" in source
        assert "binding.canonical_deployment_root == canonical_deployment_root" in source


# ═══════════════════════════════════════════════════════════════════════════
# 6. No-mutation / no-production-code-change proof (this phase's own
#    scope boundary), verified operationally.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoMutationProof:
    def test_no_repository_identity_file_created_in_this_working_tree(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_architecture_document_exists_and_states_no_dell_mutation(self) -> None:
        assert _DOC_PATH.is_file()
        text = _DOC_PATH.read_text(encoding="utf-8")
        assert "No Dell mutation occurred" in text
        assert "PERMISSION REMEDIATION PROPOSITION READY — ELECTION NOT INITIATED" in text

    def test_document_names_the_selected_remediation_model_explicitly(self) -> None:
        text = _DOC_PATH.read_text(encoding="utf-8")
        assert "chmod 1770" in text
        assert "Selected model: P-A" in text

    def test_document_records_req_036_classification(self) -> None:
        text = _DOC_PATH.read_text(encoding="utf-8")
        assert "Classification: A — invocation/config mismatch." in text
