"""Phase 149O.20L.7N.1 -- Dell Current-Source Redeployment Proposition
Independent Authority Verification.

Independent adversarial re-verification of the 149O.20L.7N proposition
(`docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_
AUTHORITY_PREPARATION.md`), performed *without* importing that phase's
own companion test module
(`tests/test_phase_149o_20l_7n_dell_current_source_redeployment_
proposition_authority_preparation.py`) as an oracle. Every fixture value
below is re-derived here, independently, from immutable git objects and
a disposable detached worktree of the exact candidate commit -- never
copied from 7N's test module or its prose.

This is a verification-only phase. It performs zero Dell access, zero
election-machinery invocation, zero CHGR publication, zero
RepositoryIdentity/DeploymentBinding creation, zero certification, zero
activation. All of that is asserted below as an absence, not assumed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROP_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md"
)

# Candidate/old SHAs as literally given in the 7N.1 task brief. Both are
# independently re-measured (not assumed) to be exactly 40 hex characters
# -- i.e. ordinary Git SHA-1 object ids -- contrary to the brief's own
# caveat that they might be "one character too long".
_CANDIDATE_SHA = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
_OLD_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"

_EXPECTED_DIGEST = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"

_AUTHORITY_SURFACES = ("src/pcae", "scripts", "docs/contracts", "schemas", "pyproject.toml")

_HISTORICAL_CHGR_IDS = {
    "chgr-0e37ed1340b14311826722c4dbf3e856",
    "chgr-96a0ce12756e4cc892492a87af1db832",
    "chgr-d4343fa51b9743f3abaeb87a881a78b1",
    "chgr-541cb08c313b4f8884970172d37c5a1d",
}


def _git(*args: str, cwd: Path = _REPO_ROOT) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _git_rc(*args: str, cwd: Path = _REPO_ROOT) -> int:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).returncode


@pytest.fixture(scope="module")
def candidate_worktree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A disposable, detached worktree checked out at the exact candidate
    SHA -- independent of the repository's own current working tree and
    of any worktree 7N or 7N.1's authoring session may have created."""
    dest = tmp_path_factory.mktemp("cand7n1") / "wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(dest), _CANDIDATE_SHA],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    yield dest
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(dest)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Candidate SHA authenticity / hex-length / no moving refs (checklist 1, 6)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateAuthenticity:
    def test_candidate_sha_is_exactly_40_hex_characters(self) -> None:
        assert len(_CANDIDATE_SHA) == 40
        int(_CANDIDATE_SHA, 16)  # must be valid hex

    def test_old_sha_is_exactly_40_hex_characters(self) -> None:
        assert len(_OLD_SHA) == 40
        int(_OLD_SHA, 16)

    def test_candidate_resolves_to_commit_type_unabbreviated(self) -> None:
        assert _git("cat-file", "-t", _CANDIDATE_SHA) == "commit"

    def test_old_sha_resolves_to_commit_type_unabbreviated(self) -> None:
        assert _git("cat-file", "-t", _OLD_SHA) == "commit"

    def test_candidate_full_sha_round_trips_through_rev_parse(self) -> None:
        # A moving ref (branch/tag) would not round-trip to the identical
        # 40-char literal; an exact commit object id always does.
        assert _git("rev-parse", _CANDIDATE_SHA) == _CANDIDATE_SHA


# ═══════════════════════════════════════════════════════════════════════════
# 2. Candidate currentness against live HEAD/origin/main (checklist 5, 7)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateCurrentness:
    def test_candidate_is_ancestor_of_head(self) -> None:
        assert _git_rc("merge-base", "--is-ancestor", _CANDIDATE_SHA, "HEAD") == 0

    def test_candidate_is_ancestor_of_origin_main(self) -> None:
        assert _git_rc("merge-base", "--is-ancestor", _CANDIDATE_SHA, "origin/main") == 0

    def test_old_sha_is_ancestor_of_candidate(self) -> None:
        assert _git_rc("merge-base", "--is-ancestor", _OLD_SHA, _CANDIDATE_SHA) == 0

    def test_head_equals_origin_main(self) -> None:
        assert _git("rev-parse", "HEAD") == _git("rev-parse", "origin/main")

    def test_no_authority_bearing_drift_candidate_to_head(self) -> None:
        diffstat = _git("diff", "--stat", _CANDIDATE_SHA, "HEAD", "--", *_AUTHORITY_SURFACES)
        assert diffstat == "", (
            "authority-bearing drift found between candidate and HEAD -- "
            "candidate would be STALE"
        )

    def test_intervening_commits_are_governance_bookkeeping_only(self) -> None:
        changed = _git("diff", "--name-only", _CANDIDATE_SHA, "HEAD").splitlines()
        assert changed, "expected at least one intervening commit's worth of files"
        forbidden_prefixes = ("src/pcae/", "scripts/", "docs/contracts/", "schemas/")
        for path in changed:
            assert not path.startswith(forbidden_prefixes), path
            assert path != "pyproject.toml"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Candidate contract versions read from candidate blobs (checklist 8, 9)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateContractVersions:
    def test_hbdc_001_version_1_1_on_candidate(self) -> None:
        text = _git("show", f"{_CANDIDATE_SHA}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        assert "**Version:** 1.1" in text

    def test_hmic_001_version_1_4_on_candidate(self) -> None:
        text = _git(
            "show",
            f"{_CANDIDATE_SHA}:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        assert "**Version:** 1.4" in text

    def test_hmrc_001_version_1_1_on_candidate(self) -> None:
        text = _git(
            "show", f"{_CANDIDATE_SHA}:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
        )
        assert "**Version:** 1.1" in text


# ═══════════════════════════════════════════════════════════════════════════
# 4. HMIC digest + 30-member frozen set, recomputed against a *disposable*
#    detached worktree using the production function (checklist 10, 11, 12)
# ═══════════════════════════════════════════════════════════════════════════


class TestHmicDigestAndFrozenSet:
    def test_expected_digest_is_a_valid_sha256_hex_string(self) -> None:
        assert len(_EXPECTED_DIGEST) == 64
        int(_EXPECTED_DIGEST, 16)

    def test_digest_recomputed_against_disposable_candidate_worktree(
        self, candidate_worktree: Path
    ) -> None:
        script = (
            "import sys; sys.path.insert(0, 'src'); "
            "from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest; "
            "from pcae.core.paths import HarnessPath; from pathlib import Path; "
            "print(derive_implementation_scope_digest(HarnessPath(Path('.').resolve())))"
        )
        result = subprocess.run(
            ["python3", "-c", script], cwd=candidate_worktree, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == _EXPECTED_DIGEST

    def test_frozen_set_has_exactly_30_members_on_disposable_worktree(
        self, candidate_worktree: Path
    ) -> None:
        script = (
            "import sys; sys.path.insert(0, 'src'); "
            "from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES as f; "
            "print(len(f))"
        )
        result = subprocess.run(
            ["python3", "-c", script], cwd=candidate_worktree, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "30"

    def test_both_deploymentbinding_producer_surfaces_are_frozen_members(
        self, candidate_worktree: Path
    ) -> None:
        script = (
            "import sys; sys.path.insert(0, 'src'); "
            "from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES as f; "
            "print('core/hatp_deployment_binding_admin.py' in f); "
            "print('scripts/hatp_deployment_binding_admin.py' in f)"
        )
        result = subprocess.run(
            ["python3", "-c", script], cwd=candidate_worktree, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        lines = result.stdout.strip().splitlines()
        assert lines == ["True", "True"]

    def test_all_frozen_paths_exist_are_regular_files_not_symlinks_no_dupes(
        self, candidate_worktree: Path
    ) -> None:
        script = (
            "import sys, os, json; sys.path.insert(0, 'src'); "
            "from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES as f; "
            "from pathlib import Path; "
            "issues = []; seen = set()\n"
            "for name in sorted(f):\n"
            "    c1 = Path('src/pcae') / name\n"
            "    c2 = Path('.') / name\n"
            "    p = c1 if c1.exists() else c2\n"
            "    if not p.exists(): issues.append('missing:' + name)\n"
            "    elif p.is_symlink(): issues.append('symlink:' + name)\n"
            "    elif not p.is_file(): issues.append('notfile:' + name)\n"
            "    norm = os.path.normpath(str(p))\n"
            "    if norm in seen: issues.append('dup:' + name)\n"
            "    seen.add(norm)\n"
            "print(json.dumps(issues))"
        )
        result = subprocess.run(
            ["python3", "-c", script], cwd=candidate_worktree, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout.strip()) == []


# ═══════════════════════════════════════════════════════════════════════════
# 5. Candidate tree inventory, freshly enumerated (checklist 13)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateTreeInventory:
    def test_total_tracked_path_count_is_4200(self) -> None:
        lines = _git("ls-tree", "-r", _CANDIDATE_SHA, "--name-only").splitlines()
        assert len(lines) == 4200

    def test_mode_histogram_matches_4186_100644_and_14_100755(self) -> None:
        lines = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        modes = [line.split()[0] for line in lines]
        assert modes.count("100644") == 4186
        assert modes.count("100755") == 14
        assert len(modes) == 4200

    def test_zero_symlinks(self) -> None:
        lines = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        assert sum(1 for line in lines if line.split()[0] == "120000") == 0

    def test_zero_submodules(self) -> None:
        lines = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        assert sum(1 for line in lines if line.split()[0] == "160000") == 0

    def test_no_unexpected_modes(self) -> None:
        lines = _git("ls-tree", "-r", _CANDIDATE_SHA).splitlines()
        modes = {line.split()[0] for line in lines}
        assert modes == {"100644", "100755"}


# ═══════════════════════════════════════════════════════════════════════════
# 6. Exact five-file old->candidate diff + changed-file blob hashes
#    (checklist 15, 16, 17)
# ═══════════════════════════════════════════════════════════════════════════

_EXPECTED_CHANGED = {
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md": "ccc4efba78b39633b63f25e1415b915598a49772",
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md": (
        "1c6ad765533b36262319005a9f1517b0182c8b7a"
    ),
    "scripts/hatp_deployment_binding_admin.py": "286db838d573ef9311a6d0df78a6842b5f4ef296",
    "src/pcae/core/hatp_deployment_binding_admin.py": "c7950f302ba5714764de5fa0fd86699a07cfad1c",
    "src/pcae/core/hatp_mandatory_certification.py": "1b965cc53f2ad2ef6c3814d64129a4b748179f9f",
}


class TestOldToCandidateDiff:
    def test_exactly_five_files_changed_across_authority_surfaces(self) -> None:
        changed = _git(
            "diff",
            "--name-only",
            _OLD_SHA,
            _CANDIDATE_SHA,
            "--",
            "src",
            "scripts",
            "docs/contracts",
            "schemas",
            "pyproject.toml",
        ).splitlines()
        assert set(changed) == set(_EXPECTED_CHANGED)
        assert len(changed) == 5

    def test_pyproject_toml_byte_unchanged(self) -> None:
        diff = _git("diff", _OLD_SHA, _CANDIDATE_SHA, "--", "pyproject.toml")
        assert diff == ""

    @pytest.mark.parametrize("path,expected_blob", sorted(_EXPECTED_CHANGED.items()))
    def test_changed_file_candidate_blob_matches(self, path: str, expected_blob: str) -> None:
        assert _git("rev-parse", f"{_CANDIDATE_SHA}:{path}") == expected_blob


# ═══════════════════════════════════════════════════════════════════════════
# 7. Command literalization / no moving-ref / mutation classification
#    (checklist 26-29, 31, 58, 63)
# ═══════════════════════════════════════════════════════════════════════════


class TestCommandLiteralizationAndMutationClassification:
    def test_fetch_command_targets_exact_sha_not_branch(self) -> None:
        assert f"fetch origin {_CANDIDATE_SHA}" in _PROP_DOC.read_text(encoding="utf-8")

    def test_no_git_pull_anywhere_in_proposition(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        assert "git pull" not in text.lower() or "no `git pull`" in text.lower()
        # Explicitly forbid any literal invocation form (not just the prose ban).
        for line in text.splitlines():
            stripped = line.strip().lstrip("$ ")
            assert not stripped.startswith("git pull")
            assert not stripped.startswith("sudo git") or "pull" not in stripped

    def test_checkout_command_is_detached_to_exact_candidate_sha(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        assert f"checkout --detach {_CANDIDATE_SHA}" in text

    def test_rollback_checkout_command_targets_exact_old_sha(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        assert f"checkout --detach {_OLD_SHA}" in text

    def test_mode_normalization_uses_find_exec_not_for_loop_word_splitting(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        # The unsafe pattern this checks for is `for x in $(...)`, which
        # breaks on filenames containing whitespace. The proposition must
        # use `find ... -exec ... {} \;` instead, which never word-splits.
        assert "for f in $(" not in text
        assert "-exec" in text

    def test_pip_install_never_appears_as_a_literal_command_only_as_prohibition_prose(
        self,
    ) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("`pip install") or stripped.startswith("- `pip install"):
                continue  # prohibition-list prose, not a command
            assert "pip install -e ." not in stripped
            assert not stripped.startswith("pip install")
            assert not stripped.startswith("sudo pip install")

    def test_ownership_command_scoped_to_source_tree_only(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        assert "chown -R root:pcae /opt/pcae/runtime/src" in text
        assert "chown -R root:pcae /opt/pcae\n" not in text
        assert "chown -R root:pcae /opt/pcae `" not in text


# ═══════════════════════════════════════════════════════════════════════════
# 8. Local rollback rehearsal: network-independent, disposable clone
#    (checklist 47-51, 83)
# ═══════════════════════════════════════════════════════════════════════════


class TestLocalRollbackRehearsal:
    def test_rollback_rehearsal_in_disposable_clone_without_remote(self, tmp_path: Path) -> None:
        clone = tmp_path / "rollback-rehearsal"
        subprocess.run(
            ["git", "clone", "--no-hardlinks", str(_REPO_ROOT), str(clone)],
            check=True,
            capture_output=True,
            text=True,
        )
        try:
            subprocess.run(
                ["git", "checkout", "--detach", _OLD_SHA], cwd=clone, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "checkout", "--detach", _CANDIDATE_SHA],
                cwd=clone,
                check=True,
                capture_output=True,
            )
            assert _git("rev-parse", "HEAD", cwd=clone) == _CANDIDATE_SHA
            # Sever network dependency entirely.
            subprocess.run(
                ["git", "remote", "remove", "origin"], cwd=clone, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "checkout", "--detach", _OLD_SHA], cwd=clone, check=True, capture_output=True
            )
            assert _git("rev-parse", "HEAD", cwd=clone) == _OLD_SHA
            assert _git("status", "--short", "--untracked-files=all", cwd=clone) == ""
        finally:
            shutil.rmtree(clone, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
# 9. Candidate mode-mapping rehearsal across all 4200 paths (checklist 84)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateModeMappingRehearsal:
    def test_all_4200_paths_map_correctly_in_disposable_worktree(
        self, candidate_worktree: Path
    ) -> None:
        subprocess.run(
            ["find", ".", "-type", "d", "-exec", "chmod", "0750", "{}", ";"],
            cwd=candidate_worktree,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["find", ".", "-type", "f", "-perm", "-u+x", "-exec", "chmod", "0750", "{}", ";"],
            cwd=candidate_worktree,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["find", ".", "-type", "f", "!", "-perm", "-u+x", "-exec", "chmod", "0640", "{}", ";"],
            cwd=candidate_worktree,
            check=True,
            capture_output=True,
        )
        lines = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"], cwd=candidate_worktree, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        total = ok640 = ok750 = mismatches = 0
        import os

        for line in lines:
            meta, path = line.split("\t", 1)
            mode = meta.split()[0]
            total += 1
            st = os.lstat(candidate_worktree / path)
            fsmode = oct(st.st_mode & 0o777)
            if mode == "100644":
                ok640 += fsmode == "0o640"
            elif mode == "100755":
                ok750 += fsmode == "0o750"
            else:
                mismatches += 1
        assert total == 4200
        assert ok640 == 4186
        assert ok750 == 14
        assert mismatches == 0


# ═══════════════════════════════════════════════════════════════════════════
# 10. No RepositoryIdentity / DeploymentBinding / certification / election /
#     CHGR state exists (checklist 58-61, 64-66, 75-76, 78)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoAuthorityStateAdvanced:
    def test_no_repository_identity_file_in_repo_root(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_working_tree_clean_for_pcae_directory(self) -> None:
        assert _git("status", "--short", ".pcae/") == ""

    def test_published_chgr_directory_contains_no_new_chgr_for_candidate(self) -> None:
        published = _REPO_ROOT / ".pcae" / "publication-execution" / "published"
        if not published.exists():
            return
        for entry in published.iterdir():
            assert _CANDIDATE_SHA not in entry.read_text(encoding="utf-8")

    def test_exactly_four_historical_chgr_records_exist(self) -> None:
        records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
        found = {p.stem for p in records_dir.glob("chgr-*.json")}
        assert found == _HISTORICAL_CHGR_IDS

    def test_no_historical_chgr_mentions_candidate_sha(self) -> None:
        records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
        for chgr_id in _HISTORICAL_CHGR_IDS:
            text = (records_dir / f"{chgr_id}.json").read_text(encoding="utf-8")
            assert _CANDIDATE_SHA not in text

    def test_no_decision_session_references_candidate_sha(self) -> None:
        sessions_dir = _REPO_ROOT / ".pcae" / "decision-sessions"
        if not sessions_dir.exists():
            return
        for entry in sessions_dir.glob("*.json"):
            assert _CANDIDATE_SHA not in entry.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 11. Proposition subject length + bound exclusions (checklist 67, 69, 70, 79)
# ═══════════════════════════════════════════════════════════════════════════


class TestPropositionSubjectAndExclusions:
    def test_decision_subject_schema_max_length_is_500(self) -> None:
        schema_path = (
            _REPO_ROOT
            / "src"
            / "pcae"
            / "schema_resources"
            / "chgr"
            / "records"
            / "human_governance_record.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["properties"]["decision_subject"]["maxLength"] == 500

    def test_draft_decision_subject_text_is_within_schema_limit(self) -> None:
        import re

        text = _PROP_DOC.read_text(encoding="utf-8")
        match = re.search(r'> "(.*?)"', text, re.S)
        assert match is not None
        subject = match.group(1)
        assert len(subject) <= 500
        assert _OLD_SHA in subject
        assert _CANDIDATE_SHA in subject

    def test_proposition_contains_no_first_use_authorization_language(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8").lower()
        forbidden = (
            "this authorizes first use",
            "authorizes deploymentbinding creation",
            "authorizes repositoryidentity creation",
        )
        for phrase in forbidden:
            assert phrase not in text

    def test_all_named_exclusions_present_in_proposition_text(self) -> None:
        text = _PROP_DOC.read_text(encoding="utf-8")
        for term in (
            "RepositoryIdentity creation",
            "DeploymentBinding create/rotate/revoke",
            "Boundary C",
            "Boundary A",
            "HATP activation",
        ):
            assert term in text


# ═══════════════════════════════════════════════════════════════════════════
# 12. Runtime state re-confirmation (checklist 79)
# ═══════════════════════════════════════════════════════════════════════════


class TestRuntimeStateReconfirmation:
    def test_runtime_inspect_reports_observed_not_executing(self) -> None:
        result = subprocess.run(
            ["python3", "-m", "pcae", "runtime", "inspect"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Runtime state:             Observed" in result.stdout
        assert "Execution capability:      unavailable" in result.stdout
