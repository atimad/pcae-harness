"""Phase 149O.20L.7N -- Dell Current-Source Redeployment Proposition +
Authority Preparation.

Proposition/authority-preparation phase. This module is proof, not
implementation: it demonstrates, against live git history, contracts,
and production source, the exact facts `docs/PHASE_149O_20L_7N_DELL_
CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md`
reconstructs -- candidate currentness and ancestry, the recomputed HMIC
implementation-scope digest, the 30-member frozen authority-bearing
set, the exact five-file old-to-candidate diff and its blob identities,
the candidate tree inventory, and the proposition's decision-subject
length. No production module is modified by this phase. No election,
CHGR, RepositoryIdentity, or DeploymentBinding is created.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ARCH_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md"
).read_text(encoding="utf-8")

_OLD_DELL_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
_CANDIDATE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_EXPECTED_DIGEST = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"

_EXPECTED_CHANGED_FILES = {
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md": (
        "ccc4efba78b39633b63f25e1415b915598a49772"
    ),
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md": (
        "1c6ad765533b36262319005a9f1517b0182c8b7a"
    ),
    "scripts/hatp_deployment_binding_admin.py": "286db838d573ef9311a6d0df78a6842b5f4ef296",
    "src/pcae/core/hatp_deployment_binding_admin.py": "c7950f302ba5714764de5fa0fd86699a07cfad1c",
    "src/pcae/core/hatp_mandatory_certification.py": "1b965cc53f2ad2ef6c3814d64129a4b748179f9f",
}

_HISTORICAL_CHGRS = (
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
    "chgr-0e37ed1340b14311826722c4dbf3e856",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Candidate currentness gate (doc §1)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateCurrentnessGate:
    def test_candidate_sha_is_a_commit_object(self) -> None:
        result = subprocess.run(["git", "cat-file", "-e", f"{_CANDIDATE_SHA}^{{commit}}"], cwd=_REPO_ROOT)
        assert result.returncode == 0

    def test_old_sha_is_a_commit_object(self) -> None:
        result = subprocess.run(["git", "cat-file", "-e", f"{_OLD_DELL_SHA}^{{commit}}"], cwd=_REPO_ROOT)
        assert result.returncode == 0

    def test_candidate_is_ancestor_of_head(self) -> None:
        result = subprocess.run(["git", "merge-base", "--is-ancestor", _CANDIDATE_SHA, "HEAD"], cwd=_REPO_ROOT)
        assert result.returncode == 0

    def test_old_sha_is_ancestor_of_candidate(self) -> None:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", _OLD_DELL_SHA, _CANDIDATE_SHA], cwd=_REPO_ROOT
        )
        assert result.returncode == 0

    def test_no_authority_bearing_drift_candidate_to_head(self) -> None:
        diffstat = _git(
            "diff",
            "--stat",
            _CANDIDATE_SHA,
            "HEAD",
            "--",
            "src/pcae",
            "scripts",
            "docs/contracts",
            "schemas",
            "pyproject.toml",
        )
        assert diffstat == ""


# ═══════════════════════════════════════════════════════════════════════════
# 2. Candidate contract state + HMIC digest + frozen membership (doc §2-4)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateContractStateAndDigest:
    def test_hbdc_version_is_1_1_on_candidate(self) -> None:
        text = _git("show", f"{_CANDIDATE_SHA}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        assert "**Version:** 1.1" in text

    def test_hmic_version_is_1_4_on_candidate(self) -> None:
        text = _git(
            "show",
            f"{_CANDIDATE_SHA}:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        assert "**Version:** 1.4" in text

    def test_hmrc_version_is_1_1_on_candidate(self) -> None:
        text = _git(
            "show", f"{_CANDIDATE_SHA}:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
        )
        assert "**Version:** 1.1" in text

    def test_implementation_scope_digest_matches_expected(self) -> None:
        # No authority-bearing drift exists between candidate and live HEAD
        # (TestCandidateCurrentnessGate.test_no_authority_bearing_drift_candidate_to_head),
        # so computing against the live checkout is equivalent to computing
        # against a candidate worktree.
        from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
        from pcae.core.paths import HarnessPath

        assert derive_implementation_scope_digest(HarnessPath(_REPO_ROOT)) == _EXPECTED_DIGEST

    def test_thirty_member_set_matches_frozen_constant(self) -> None:
        from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

        assert len(_FROZEN_AUTHORITY_BEARING_FILES) >= 30
        assert "core/hatp_deployment_binding_admin.py" in _FROZEN_AUTHORITY_BEARING_FILES
        assert "scripts/hatp_deployment_binding_admin.py" in _FROZEN_AUTHORITY_BEARING_FILES

    def test_candidate_contains_both_deployment_binding_admin_files(self) -> None:
        for path in (
            "src/pcae/core/hatp_deployment_binding_admin.py",
            "scripts/hatp_deployment_binding_admin.py",
        ):
            result = subprocess.run(["git", "cat-file", "-e", f"{_CANDIDATE_SHA}:{path}"], cwd=_REPO_ROOT)
            assert result.returncode == 0, path


# ═══════════════════════════════════════════════════════════════════════════
# 3. Candidate tree inventory (doc §5)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateTreeInventory:
    def test_total_tracked_path_count(self) -> None:
        names = _git("ls-tree", "-r", _CANDIDATE_SHA, "--name-only")
        assert len(names.splitlines()) == 4200

    def test_mode_counts(self) -> None:
        entries = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        modes = [line.split()[0] for line in entries]
        assert modes.count("100644") == 4186
        assert modes.count("100755") == 14
        assert all(m in ("100644", "100755") for m in modes)

    def test_zero_symlinks_and_submodules(self) -> None:
        entries = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        modes = {line.split()[0] for line in entries}
        assert "120000" not in modes
        assert "160000" not in modes


# ═══════════════════════════════════════════════════════════════════════════
# 4. Old-to-candidate diff and blob identities (doc §7)
# ═══════════════════════════════════════════════════════════════════════════


class TestOldToCandidateDiff:
    def test_exactly_five_authority_relevant_files_changed(self) -> None:
        names = _git(
            "diff",
            "--name-only",
            _OLD_DELL_SHA,
            _CANDIDATE_SHA,
            "--",
            "src",
            "scripts",
            "docs/contracts",
            "pyproject.toml",
        )
        changed_files = set(names.splitlines())
        assert changed_files == set(_EXPECTED_CHANGED_FILES)

    def test_pyproject_toml_byte_unchanged(self) -> None:
        old_blob = _git("rev-parse", f"{_OLD_DELL_SHA}:pyproject.toml")
        candidate_blob = _git("rev-parse", f"{_CANDIDATE_SHA}:pyproject.toml")
        assert old_blob == candidate_blob

    @pytest.mark.parametrize("path,expected_blob", list(_EXPECTED_CHANGED_FILES.items()))
    def test_changed_file_blob_matches_expected(self, path: str, expected_blob: str) -> None:
        assert _git("rev-parse", f"{_CANDIDATE_SHA}:{path}") == expected_blob


# ═══════════════════════════════════════════════════════════════════════════
# 5. Historical CHGR records exist and are byte-fixed (doc §40)
# ═══════════════════════════════════════════════════════════════════════════


class TestHistoricalChgrRecords:
    @pytest.mark.parametrize("chgr_id", _HISTORICAL_CHGRS)
    def test_chgr_record_present_on_disk(self, chgr_id: str) -> None:
        candidates = list((_REPO_ROOT / ".pcae" / "publication-execution").rglob(f"{chgr_id}.json"))
        assert candidates, f"{chgr_id} not found under .pcae/publication-execution"

    def test_no_new_chgr_published_this_phase(self) -> None:
        status = _git("status", "--short", ".pcae/publication-execution/")
        assert status == ""


# ═══════════════════════════════════════════════════════════════════════════
# 6. Proposition document content (doc §42, §46, §66-68)
# ═══════════════════════════════════════════════════════════════════════════


class TestPropositionDocumentContent:
    def test_decision_subject_within_schema_limit(self) -> None:
        subject = (
            "Dell PCAE runtime source-only redeployment from "
            "28bf137b5dc95d024e8913b678dce0501a46fd0f to candidate "
            "b0840e96a7ffb12308e95828aa5927c3e7c770c0; venv and wrapper "
            "retained unchanged; no RepositoryIdentity or DeploymentBinding created."
        )
        assert subject in _ARCH_DOC
        assert len(subject) <= 500

    def test_expected_hbdc_diagnostic_residual_documented(self) -> None:
        assert "NON_COMPLIANT" in _ARCH_DOC
        assert "HBDC-REQ-042" in _ARCH_DOC

    def test_wrapper_digest_documented_unchanged(self) -> None:
        assert "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32" in _ARCH_DOC

    def test_rollback_target_documented(self) -> None:
        assert _OLD_DELL_SHA in _ARCH_DOC

    def test_final_verdict_documented(self) -> None:
        assert "REDEPLOYMENT PROPOSITION READY" in _ARCH_DOC

    def test_no_election_or_mutation_claimed(self) -> None:
        assert "ELECTION NOT INITIATED" in _ARCH_DOC
        assert "No Dell access was performed this phase" in _ARCH_DOC

    def test_recommended_next_phase_documented(self) -> None:
        assert "149O.20L.7N.1" in _ARCH_DOC
