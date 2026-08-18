"""Phase 149O.20L.7O.2A.1 -- RepositoryIdentity Write-Path Remediation
Proposition Independent Verification.

Independent-verification phase. This module proves, against live
production source (not `149O.20L.7O.2A`'s own prose as an oracle), the
facts `docs/PHASE_149O_20L_7O_2A_1_REPOSITORYIDENTITY_WRITE_PATH_
REMEDIATION_PROPOSITION_INDEPENDENT_VERIFICATION.md` reconstructs --
most importantly the real `.pcae/.gitignore` entry count (39, not the
prior phase's transcribed 34) and the `architecture-history.json`
producer-mechanism finding (direct truncating `open("w")` on a
pre-existing, git-tracked, root-owned file, not the atomic
`mkstemp`+`os.replace` idiom `repository_identity.py` uses). No
production module is modified by this phase; no `RepositoryIdentity`
or `DeploymentBinding` is created anywhere in this suite; no Dell
command of any kind is issued.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pcae.core import agent as agent_module
from pcae.core import architecture as architecture_module
from pcae.core import hatp_bootstrap
from pcae.core import hatp_mandatory_certification
from pcae.core import repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GITIGNORE_PATH = _REPO_ROOT / ".pcae" / ".gitignore"
_ARCHITECTURE_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "architecture.py").read_text(encoding="utf-8")
_AGENT_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "agent.py").read_text(encoding="utf-8")
_IDENTITY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py").read_text(encoding="utf-8")
_HMIC_SRC = (
    _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
).read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Real .gitignore inventory -- independently reconstructed, not accepted
#    as "34" from 149O.20L.7O.2A's own prose transcription.
# ═══════════════════════════════════════════════════════════════════════════


class TestRealGitignoreInventory:
    def test_gitignore_has_39_entries_not_34(self) -> None:
        entries = [line for line in _GITIGNORE_PATH.read_text(encoding="utf-8").splitlines() if line]
        assert len(entries) == 39, (
            "149O.20L.7O.2A §3 transcribed 34 entries from this file; the real "
            f"file has {len(entries)} -- architecture-history.json was silently "
            "omitted from that transcription (see next test)."
        )

    def test_architecture_history_json_is_gitignored(self) -> None:
        entries = set(_GITIGNORE_PATH.read_text(encoding="utf-8").splitlines())
        assert "architecture-history.json" in entries

    def test_architecture_history_json_is_also_git_tracked(self) -> None:
        """The contradiction this phase independently found: gitignored
        (declared runtime-local) AND git-tracked (root-owned, checked-in) at
        the same time -- unlike every other gitignore entry."""

        import subprocess

        result = subprocess.run(
            ["git", "ls-files", ".pcae/architecture-history.json"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ".pcae/architecture-history.json"

    def test_other_gitignore_entries_are_not_tracked(self) -> None:
        """Confirms architecture-history.json is the sole exception, not a
        symptom of a broader pattern."""

        import subprocess

        entries = [line for line in _GITIGNORE_PATH.read_text(encoding="utf-8").splitlines() if line]
        for entry in entries:
            if entry in ("architecture-history.json", ".gitignore"):
                continue
            name = entry.rstrip("/")
            result = subprocess.run(
                ["git", "ls-files", f".pcae/{name}"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "", f".pcae/{name} unexpectedly tracked"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Producer-mechanism divergence: repository_identity.py (atomic rename,
#    fixed by directory-mode-only remediation) vs architecture.py (direct
#    truncating open, NOT fixed by directory-mode-only remediation) vs
#    agent.py (exclusive-create, fixed by directory-mode-only remediation).
# ═══════════════════════════════════════════════════════════════════════════


class TestProducerMechanismDivergence:
    def test_repository_identity_uses_mkstemp_and_replace(self) -> None:
        assert "tempfile.mkstemp(prefix=" in _IDENTITY_SRC
        assert "os.replace(tmp_name, path)" in _IDENTITY_SRC

    def test_architecture_history_uses_direct_truncating_open_not_atomic_replace(self) -> None:
        """This is the independently-found gap: unlike repository_identity.py,
        this producer never creates a temp file and never calls os.replace --
        it opens the final path directly in truncate mode, which requires
        write permission on the *existing* file's own mode bits, not just
        directory-level create rights."""

        assert "def write_architecture_history_snapshot" in _ARCHITECTURE_SRC
        assert 'target.open("w", encoding="utf-8"' in _ARCHITECTURE_SRC
        assert "os.replace" not in _ARCHITECTURE_SRC
        assert "tempfile.mkstemp" not in _ARCHITECTURE_SRC

    def test_architecture_history_snapshot_is_called_from_governed_hot_path(self) -> None:
        pipeline_src = (_REPO_ROOT / "src" / "pcae" / "core" / "pipeline.py").read_text(encoding="utf-8")
        session_cmd_src = (_REPO_ROOT / "src" / "pcae" / "commands" / "session.py").read_text(encoding="utf-8")
        assert "write_architecture_history_snapshot(root, check_result)" in pipeline_src
        assert "write_architecture_history_snapshot(root, check_result)" in session_cmd_src

    def test_agent_lock_uses_exclusive_create_not_atomic_replace(self) -> None:
        """A third, distinct pattern: open("x", ...) is still a pure
        directory-create operation (like mkstemp), so it IS fixed by a
        directory-mode-only remediation -- unlike architecture.py's pattern."""

        assert 'target.open("x", encoding="utf-8"' in _AGENT_SRC

    def test_release_agent_lock_only_unlinks_its_own_path(self) -> None:
        assert "target.unlink()" in _AGENT_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 3. Sticky-bit blind spot in the existing HBDC checkers -- reference-verified
#    from this repo's own source, no S_ISVTX handling anywhere.
# ═══════════════════════════════════════════════════════════════════════════


def test_no_s_isvtx_reference_anywhere_in_src_pcae() -> None:
    import subprocess

    result = subprocess.run(
        ["grep", "-rl", "S_ISVTX", str(_REPO_ROOT / "src" / "pcae")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, "expected no matches (grep exit 1); a match would mean sticky-bit awareness now exists"
    assert result.stdout == ""


# ═══════════════════════════════════════════════════════════════════════════
# 4. HMIC frozen scope is a source-file list, not a .pcae-runtime-path list --
#    unaffected by RepositoryIdentity creation or any .pcae permission change.
# ═══════════════════════════════════════════════════════════════════════════


class TestHmicFrozenScopeUnaffected:
    def test_frozen_scope_names_source_files_not_pcae_paths(self) -> None:
        assert '"core/repository_identity.py"' in _HMIC_SRC
        assert '"core/hatp_class_b_conformance.py"' in _HMIC_SRC
        assert ".pcae/repository-identity.json" not in _HMIC_SRC

    def test_derive_implementation_scope_digest_exists(self) -> None:
        assert hasattr(hatp_mandatory_certification, "derive_implementation_scope_digest")


# ═══════════════════════════════════════════════════════════════════════════
# 5. Protected Root distinctness -- reconfirmed directly.
# ═══════════════════════════════════════════════════════════════════════════


class TestProtectedRootReconfirmed:
    def test_trust_store_root_unrelated_to_pcae_directory(self) -> None:
        root = hatp_bootstrap._LINUX_FIXED_TRUST_ROOT
        assert str(root) == "/etc/pcae/hatp/trust-store"
        assert ".pcae" not in root.parts


# ═══════════════════════════════════════════════════════════════════════════
# 6. Idempotent-ensure name-squatting surface -- traced, not speculated:
#    no ownership check exists before an existing identity is trusted.
# ═══════════════════════════════════════════════════════════════════════════


class TestIdempotentEnsureHasNoOwnershipCheck:
    def test_ensure_repository_identity_never_checks_file_owner(self) -> None:
        assert "st_uid" not in _IDENTITY_SRC
        assert "getuid" not in _IDENTITY_SRC

    def test_read_repository_identity_validates_schema_only(self, tmp_path) -> None:
        from pcae.core.paths import HarnessPath

        root = HarnessPath(tmp_path)
        pcae_dir = tmp_path / ".pcae"
        pcae_dir.mkdir()
        (pcae_dir / "repository-identity.json").write_text(
            '{"schema_version": 1, "repository_instance_id": '
            '"11111111-1111-4111-8111-111111111111", "created_at": '
            '"2026-01-01T00:00:00.000Z"}\n',
            encoding="utf-8",
        )
        # An "attacker"-authored (here: test-authored) pre-existing file with
        # a self-chosen but schema-valid UUID4 is accepted unchanged by
        # ensure_repository_identity -- no ownership/provenance check exists.
        identity = repository_identity.ensure_repository_identity(root)
        assert identity.repository_instance_id == "11111111-1111-4111-8111-111111111111"


# ═══════════════════════════════════════════════════════════════════════════
# 7. No-mutation proof for this phase itself.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoMutationProofThisPhase:
    def test_no_repository_identity_file_created_in_this_working_tree(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_architecture_document_exists_and_states_no_dell_mutation(self) -> None:
        doc_path = (
            _REPO_ROOT
            / "docs"
            / "PHASE_149O_20L_7O_2A_1_REPOSITORYIDENTITY_WRITE_PATH_REMEDIATION_PROPOSITION_INDEPENDENT_VERIFICATION.md"
        )
        assert doc_path.is_file()
        text = doc_path.read_text(encoding="utf-8")
        assert "No Dell mutation" in text
        assert "INDEPENDENTLY VERIFIED" in text
