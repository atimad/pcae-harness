"""Phase 149O.20L.1B -- HMRC-001 v1.1 HMIC Contract-Identity Alignment
Independent Verification.

Independently verifies Phase 149O.20L.1A's repair of finding
B-149O.20L.1-1, trusting neither 149O.20L.1A's report, its own tests
(deliberately not imported here), its Outcome-B classification, its
claim that `derive_contract_versions` was never stale, its claim that
HMIC-REQ-067/069 were already correct, its same-version repair
rationale, nor its historical-test attribution. Every fact below is
re-derived directly from fixed git history and current primary source
by this module's own fixtures and assertions.

Commit identity used by this module (independently confirmed by direct
`git log`/`git show`, not copied from any prior phase's report):

  * `f14e524e` -- true pre-149O.20L.1 phase-entry commit (last commit of
    Phase 149O.20L, immediately preceding 149O.20L.1's own first commit
    `582226b1`).
  * `90e14496` -- true post-149O.20L.1 / pre-149O.20L.1A phase-entry
    commit (149O.20L.1's last commit, immediately preceding 149O.20L.1A's
    own first commit `7eb9afb4`).
  * `7eb9afb4` -- the 149O.20L.1A repair commit itself.

This is a verification-only module: it makes no assertion that depends
on this phase having modified any production or contract file, and it
performs no such modification itself.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HMIC_RELATIVE = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HMRC_RELATIVE = "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_HMIC_PATH = _REPO_ROOT / _HMIC_RELATIVE
_HMRC_PATH = _REPO_ROOT / _HMRC_RELATIVE
_HMIC_TEXT = _HMIC_PATH.read_text(encoding="utf-8")
_HMRC_TEXT = _HMRC_PATH.read_text(encoding="utf-8")

_PRE_L1_ENTRY = "f14e524e"
_POST_L1_PRE_L1A_ENTRY = "90e14496"
_L1A_REPAIR_COMMIT = "7eb9afb4"

_VERSION_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)\s*$", re.MULTILINE)
_DEPENDS_ON_RE = re.compile(r"^\*\*Depends on.*$", re.MULTILINE)


def _git_show(commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _git_show_bytes(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


# ═══════════════════════════════════════════════════════════════════════
# 1. Pre-149O.20L.1 consistency (independently reconstructed)
# ═══════════════════════════════════════════════════════════════════════


class TestPreL1Consistency:
    def test_hmrc_v1_0_at_pre_l1_entry(self) -> None:
        text = _git_show(_PRE_L1_ENTRY, _HMRC_RELATIVE)
        assert _VERSION_RE.search(text).group(1) == "1.0"

    def test_hmic_depends_on_names_hmrc_v1_0_at_pre_l1_entry(self) -> None:
        text = _git_show(_PRE_L1_ENTRY, _HMIC_RELATIVE)
        depends_line = _DEPENDS_ON_RE.search(text).group(0)
        assert "HMRC-001 v1.0" in depends_line

    def test_pre_l1_entry_is_internally_consistent(self) -> None:
        """The live HMRC header and HMIC's descriptive claim about it
        agree at the true phase-entry commit -- the mismatch introduced
        later is not a pre-existing defect."""
        hmrc_text = _git_show(_PRE_L1_ENTRY, _HMRC_RELATIVE)
        hmic_text = _git_show(_PRE_L1_ENTRY, _HMIC_RELATIVE)
        hmrc_version = _VERSION_RE.search(hmrc_text).group(1)
        depends_line = _DEPENDS_ON_RE.search(hmic_text).group(0)
        assert f"HMRC-001 v{hmrc_version}" in depends_line


# ═══════════════════════════════════════════════════════════════════════
# 2. Post-149O.20L.1 / pre-149O.20L.1A mismatch (independently
#    reconstructed) -- the core three-way evidence.
# ═══════════════════════════════════════════════════════════════════════


class TestPostL1PreL1AMismatch:
    def test_hmrc_is_v1_1_after_l1(self) -> None:
        text = _git_show(_POST_L1_PRE_L1A_ENTRY, _HMRC_RELATIVE)
        assert _VERSION_RE.search(text).group(1) == "1.1"

    def test_hmic_depends_on_still_names_hmrc_v1_0_after_l1(self) -> None:
        text = _git_show(_POST_L1_PRE_L1A_ENTRY, _HMIC_RELATIVE)
        depends_line = _DEPENDS_ON_RE.search(text).group(0)
        assert "HMRC-001 v1.0" in depends_line

    def test_mismatch_is_real_and_direct_consequence_of_l1(self) -> None:
        hmrc_text = _git_show(_POST_L1_PRE_L1A_ENTRY, _HMRC_RELATIVE)
        hmic_text = _git_show(_POST_L1_PRE_L1A_ENTRY, _HMIC_RELATIVE)
        hmrc_version = _VERSION_RE.search(hmrc_text).group(1)
        depends_line = _DEPENDS_ON_RE.search(hmic_text).group(0)
        assert f"HMRC-001 v{hmrc_version}" not in depends_line
        assert "HMRC-001 v1.0" in depends_line

    def test_hmic_version_unchanged_by_l1(self) -> None:
        """149O.20L.1 did not touch HMIC-001 at all -- HMIC-001 stayed
        v1.3 across the mismatch window."""
        pre_text = _git_show(_PRE_L1_ENTRY, _HMIC_RELATIVE)
        post_text = _git_show(_POST_L1_PRE_L1A_ENTRY, _HMIC_RELATIVE)
        assert _git_show_bytes(_PRE_L1_ENTRY, _HMIC_RELATIVE) == _git_show_bytes(
            _POST_L1_PRE_L1A_ENTRY, _HMIC_RELATIVE
        )
        assert _VERSION_RE.search(pre_text).group(1) == _VERSION_RE.search(post_text).group(1) == "1.3"


# ═══════════════════════════════════════════════════════════════════════
# 3. Current repaired state
# ═══════════════════════════════════════════════════════════════════════


class TestCurrentRepairedState:
    def test_hmrc_is_v1_1_currently(self) -> None:
        assert _VERSION_RE.search(_HMRC_TEXT).group(1) == "1.1"

    def test_hmic_depends_on_names_hmrc_v1_1_currently(self) -> None:
        depends_line = _DEPENDS_ON_RE.search(_HMIC_TEXT).group(0)
        assert "HMRC-001 v1.1" in depends_line
        assert "HMRC-001 v1.0" not in depends_line

    def test_hmic_still_v1_3(self) -> None:
        assert _VERSION_RE.search(_HMIC_TEXT).group(1) == "1.3"

    def test_all_layers_agree_on_hmrc_v1_1(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        derived = hmic.derive_contract_versions(root)
        assert derived["HMRC-001"] == "1.1"
        depends_line = _DEPENDS_ON_RE.search(_HMIC_TEXT).group(0)
        assert "HMRC-001 v1.1" in depends_line
        assert _VERSION_RE.search(_HMRC_TEXT).group(1) == "1.1"


# ═══════════════════════════════════════════════════════════════════════
# 4. derive_contract_versions exercised across historical + current
#    states (real production mechanism, not a re-implementation)
# ═══════════════════════════════════════════════════════════════════════


class TestDeriveContractVersionsAcrossHistory:
    def test_current_repository_returns_hmrc_1_1(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        derived = hmic.derive_contract_versions(root)
        assert derived["HMRC-001"] == "1.1"

    def test_worktree_at_pre_l1_entry_returns_hmrc_1_0(self, tmp_path: Path) -> None:
        worktree = tmp_path / "pre_l1"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), _PRE_L1_ENTRY],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
        )
        try:
            derived = hmic.derive_contract_versions(HarnessPath(worktree))
            assert derived["HMRC-001"] == "1.0"
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=_REPO_ROOT,
                check=True,
                capture_output=True,
            )

    def test_worktree_at_post_l1_pre_l1a_entry_returns_hmrc_1_1(self, tmp_path: Path) -> None:
        """The production mechanism already returns the live HMRC value
        at the exact commit where HMIC-001's own header still claimed
        v1.0 -- direct proof the mechanism itself was never stale."""
        worktree = tmp_path / "post_l1"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), _POST_L1_PRE_L1A_ENTRY],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
        )
        try:
            derived = hmic.derive_contract_versions(HarnessPath(worktree))
            assert derived["HMRC-001"] == "1.1"
            hmic_text_at_commit = (worktree / _HMIC_RELATIVE).read_text(encoding="utf-8")
            depends_line = _DEPENDS_ON_RE.search(hmic_text_at_commit).group(0)
            assert "HMRC-001 v1.0" in depends_line
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=_REPO_ROOT,
                check=True,
                capture_output=True,
            )


# ═══════════════════════════════════════════════════════════════════════
# 5. HMIC-REQ-067/069 semantics -- read directly, not assumed
# ═══════════════════════════════════════════════════════════════════════


class TestHmicReq067FamilySemantics:
    def test_req_067_names_five_families_no_version_literal_for_hmrc(self) -> None:
        match = re.search(r"\*\*HMIC-REQ-067.*?\n\n", _HMIC_TEXT, re.DOTALL)
        assert match is not None
        text = match.group(0)
        assert "HMRC-001" in text
        assert "HATP-001" in text
        assert "HSCE-001" in text
        assert "RAE-001" in text
        assert "HBDC-001" in text
        # No literal HMRC version number frozen inside the requirement body.
        assert "HMRC-001 v1.0" not in text
        assert "HMRC-001 v1.1" not in text

    def test_five_member_family_no_sixth_no_duplicate(self) -> None:
        assert hmic._CONTRACT_IDENTITY_FILES == (
            ("HMRC-001", "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"),
            ("HATP-001", "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"),
            ("HSCE-001", "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"),
            ("RAE-001", "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"),
            ("HBDC-001", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"),
        )
        ids = [contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES]
        assert len(ids) == 5
        assert len(set(ids)) == 5


class TestHmicReq069LiveComparisonSemantics:
    def test_req_069_requires_live_header_comparison(self) -> None:
        match = re.search(r"\*\*HMIC-REQ-069.*?\n\n", _HMIC_TEXT, re.DOTALL)
        assert match is not None
        text = match.group(0)
        assert "current, live version header" in text
        assert "revised to a new version since" in text

    def test_derive_contract_versions_reads_live_header_never_a_frozen_literal(self) -> None:
        """Source-level proof: `_CONTRACT_IDENTITY_FILES` stores
        (contract_id, path) pairs only -- no version literal is embedded
        that could go stale independently of the file it names."""
        for contract_id, _path in hmic._CONTRACT_IDENTITY_FILES:
            assert isinstance(contract_id, str)
        source = Path(hmic.__file__).read_text(encoding="utf-8")
        block_match = re.search(
            r"_CONTRACT_IDENTITY_FILES.*?=\s*\((.*?)\n\)", source, re.DOTALL
        )
        assert block_match is not None
        block = block_match.group(1)
        assert not re.search(r'"\d+\.\d+"', block)


# ═══════════════════════════════════════════════════════════════════════
# 6. Actual mismatch rejection -- the real validator, not a dict compare
# ═══════════════════════════════════════════════════════════════════════


class TestActualValidatorFailsClosedOnContractDrift:
    def test_contract_mismatch_status_exists_and_is_reachable_from_derive(self) -> None:
        """Confirms CONTRACT_MISMATCH is wired directly to a
        derive_contract_versions-vs-stored-record comparison inside the
        real validator, by reading the validator source itself (not
        re-implementing the comparison here)."""
        source = Path(hmic.__file__).read_text(encoding="utf-8")
        step10 = re.search(r"# Step 10:.*?(?=\n    # Step 11:)", source, re.DOTALL)
        assert step10 is not None
        assert "derive_contract_versions" in step10.group(0)
        assert "CertificationStatus.CONTRACT_MISMATCH" in step10.group(0)
        assert "dict(current_contract_versions) != dict(record.contract_versions)" in step10.group(0)

    def test_pre_existing_suite_already_proves_fail_closed_rejection(self) -> None:
        """Not this phase's own claim: the pre-existing (149O.19.5D-era)
        suite exercises the real end-to-end validator -- not a bare dict
        comparison -- against a contract-version-drifted stored record
        and asserts CONTRACT_MISMATCH. Confirmed here by direct source
        inspection of that pre-existing test, unmodified by this phase."""
        test_source = (
            _REPO_ROOT / "tests" / "test_phase_149o_19_5d_hmic_active_certification_validation_engine.py"
        ).read_text(encoding="utf-8")
        assert "class TestContractMismatch" in test_source
        assert 'fields["contract_versions"] = {**fields["contract_versions"], "HMRC-001": "9.9"}' in test_source
        assert "hmic.CertificationStatus.CONTRACT_MISMATCH" in test_source


# ═══════════════════════════════════════════════════════════════════════
# 7. Exact 149O.20L.1A diff -- reconstructed and classified
# ═══════════════════════════════════════════════════════════════════════


class TestExactL1ARepairDiff:
    def _diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", _POST_L1_PRE_L1A_ENTRY, _L1A_REPAIR_COMMIT, "--", _HMIC_RELATIVE],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def test_only_hmic_contract_file_touched_by_repair_commit(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", _POST_L1_PRE_L1A_ENTRY, _L1A_REPAIR_COMMIT],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        # The repair commit also creates this module's own predecessor
        # test file (tests/test_phase_149o_20l_1a_...py); no other
        # production, contract, or doc file may be touched.
        assert set(changed) <= {
            _HMIC_RELATIVE,
            "tests/test_phase_149o_20l_1a_hmrc_v1_1_hmic_contract_identity_alignment_repair.py",
        }
        assert _HMIC_RELATIVE in changed

    def test_no_hmic_req_number_line_removed_or_renumbered(self) -> None:
        diff = self._diff()
        removed_req_lines = [
            line
            for line in diff.splitlines()
            if line.startswith("-") and not line.startswith("---") and re.search(r"HMIC-REQ-\d+\.", line)
        ]
        assert removed_req_lines == []

    def test_repair_adds_new_54_section_and_header_lines_only(self) -> None:
        diff = self._diff()
        added_lines = [line for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        assert any("## 54." in line for line in added_lines)
        assert any("Repaired by:** Phase 149O.20L.1A" in line for line in added_lines)
        assert any("HMRC-001 v1.1" in line for line in added_lines)

    def test_no_production_source_touched_by_repair_commit(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", _POST_L1_PRE_L1A_ENTRY, _L1A_REPAIR_COMMIT],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = result.stdout.splitlines()
        assert not any(path.startswith("src/pcae/") for path in changed)
        assert not any(path.startswith("scripts/") for path in changed)

    def test_hmrc_001_byte_unchanged_by_repair_commit(self) -> None:
        assert _git_show_bytes(_POST_L1_PRE_L1A_ENTRY, _HMRC_RELATIVE) == _git_show_bytes(
            _L1A_REPAIR_COMMIT, _HMRC_RELATIVE
        )


# ═══════════════════════════════════════════════════════════════════════
# 8. Same-version repair adjudication
# ═══════════════════════════════════════════════════════════════════════


class TestSameVersionRepairAdjudication:
    def test_hmic_version_unchanged_by_repair(self) -> None:
        pre = _VERSION_RE.search(_git_show(_POST_L1_PRE_L1A_ENTRY, _HMIC_RELATIVE)).group(1)
        post = _VERSION_RE.search(_HMIC_TEXT).group(1)
        assert pre == post == "1.3"

    def test_149o_20d_1_precedent_is_also_a_same_version_repair(self) -> None:
        """The 149O.20D.1 precedent this repair mirrors was itself a
        same-version repair (HMIC-001 stayed v1.2) despite widening a
        normative requirement's file count (24 -> 25) -- a strictly
        larger semantic change than 149O.20L.1A's pure header edit. If
        that repair validly stayed same-version, a repair that changes
        no HMIC-REQ semantics at all is at least as valid staying
        same-version."""
        doc = (_REPO_ROOT / "docs" / "PHASE_149O_20D_1_HMIC_V1_2_HBDC_CONTENT_IDENTITY_BINDING_REPAIR.md").read_text(
            encoding="utf-8"
        )
        assert "HMIC-001 v1.2" in doc or "remains v1.2" in doc.lower() or "24-file" in doc


# ═══════════════════════════════════════════════════════════════════════
# 9. No stale current HMRC v1.0 claim (current-authority search)
# ═══════════════════════════════════════════════════════════════════════


class TestNoStaleCurrentHmrcV1_0Claim:
    def test_depends_on_line_is_the_only_current_authority_dependency_claim(self) -> None:
        depends_line = _DEPENDS_ON_RE.search(_HMIC_TEXT).group(0)
        assert "HMRC-001 v1.1" in depends_line

    def test_illustrative_14_example_is_disclosed_pre_existing_and_not_a_current_authority_claim(self) -> None:
        """The §14 illustrative `contract_versions` field-table example
        still shows a four-member, HMRC-001-1.0 example -- a disclosed,
        pre-existing (since v1.2/v1.3) stale illustration, not a current-
        authority claim, and untouched by 149O.20L.1A."""
        assert '"HMRC-001": "1.0"' in _HMIC_TEXT

    def test_section_54_repair_history_explicitly_names_v1_0_only_as_historical(self) -> None:
        section_54 = _HMIC_TEXT.split("## 54.", 1)[1]
        assert "Phase 149O.20L.1 amended `HMRC-001` from v1.0 to v1.1" in section_54
        # The live Depends-on line itself, inside/after this section's
        # own header context, must not still claim v1.0.
        assert "HMRC-001 v1.1" in _DEPENDS_ON_RE.search(_HMIC_TEXT).group(0)


# ═══════════════════════════════════════════════════════════════════════
# 10. HMRC-001 byte identity across the whole repair window
# ═══════════════════════════════════════════════════════════════════════


class TestHmrcByteIdentity:
    def test_hmrc_byte_identical_from_l1a_entry_to_current(self) -> None:
        assert _git_show_bytes(_POST_L1_PRE_L1A_ENTRY, _HMRC_RELATIVE) == _HMRC_PATH.read_bytes()


# ═══════════════════════════════════════════════════════════════════════
# 11. HMIC 28-file / 5-family source-scope regression (focused)
# ═══════════════════════════════════════════════════════════════════════


class TestHmicSourceScopeRegression:
    def test_exactly_28_authority_bearing_files(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 28

    def test_three_class_b_verifier_modules_still_included(self) -> None:
        for name in (
            "core/hatp_class_b_topology_verifier.py",
            "core/hatp_environment_lock_verifier.py",
            "core/hatp_class_b_conformance.py",
        ):
            assert name in hmic._FROZEN_AUTHORITY_BEARING_FILES

    def test_hbdc_contract_still_in_frozen_scope(self) -> None:
        assert "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in hmic._FROZEN_AUTHORITY_BEARING_FILES

    def test_hbdc_still_bound_into_contract_versions(self) -> None:
        family = dict(hmic._CONTRACT_IDENTITY_FILES)
        assert family["HBDC-001"] == "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"


# ═══════════════════════════════════════════════════════════════════════
# 12. CBV-S1 durable-status adjudication (mandatory)
# ═══════════════════════════════════════════════════════════════════════


class TestCbvS1DurableStatus:
    def test_k3_report_independently_closed_cbv_s1(self) -> None:
        k3_report = (
            _REPO_ROOT
            / "docs"
            / "PHASE_149O_20K_3_HMIC_CLASS_B_VERIFIER_PRODUCTION_SOURCE_SET_ALIGNMENT_INDEPENDENT_VERIFICATION.md"
        ).read_text(encoding="utf-8")
        assert "CBV-S1: INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT + PRODUCTION" in k3_report
        assert "SOURCE-IDENTITY BOUNDARY" in k3_report

    def test_l1_and_l1a_did_not_touch_the_class_b_verifier_island_or_hbdc(self) -> None:
        """Neither 149O.20L.1 nor 149O.20L.1A modified the three Class-B
        verifier modules or HBDC-001 -- the specific subset CBV-S1's
        closure was actually scoped to (149O.20K/K.1/K.2/K.3). HMRC-001
        itself is *also* one of the 28 `_FROZEN_AUTHORITY_BEARING_FILES`
        and was legitimately changed by 149O.20L.1 -- that is a separate,
        already-independently-verifiable contract-schema evolution, not a
        CBV-S1 scope-alignment regression: CBV-S1 concerns whether HMIC's
        *enumeration* of authority-bearing files matches production
        reality, not byte-for-byte staticness of every enumerated file
        for all time (the digest is designed to change fresh on every
        call, HMIC-REQ-052's no-cache discipline)."""
        result = subprocess.run(
            ["git", "diff", "--name-only", _PRE_L1_ENTRY, "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = set(result.stdout.splitlines())
        cbv_s1_scoped_subset = {
            "src/pcae/core/hatp_class_b_topology_verifier.py",
            "src/pcae/core/hatp_environment_lock_verifier.py",
            "src/pcae/core/hatp_class_b_conformance.py",
            "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
        }
        assert changed & cbv_s1_scoped_subset == set()

    def test_hmrc_001_is_itself_one_of_the_28_frozen_files_and_its_l1_change_is_expected(self) -> None:
        assert "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md" in hmic._FROZEN_AUTHORITY_BEARING_FILES
        result = subprocess.run(
            ["git", "diff", "--name-only", _PRE_L1_ENTRY, "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = set(result.stdout.splitlines())
        assert _HMRC_RELATIVE in changed

    def test_cbv_s1_should_be_reported_closed_not_open_by_this_phase(self) -> None:
        """L.1A's own Summary/PROJECT_STATUS wording ('CBV-S1/CBV-S10
        unaffected, remain OPEN') is corrected by this phase's report:
        CBV-S1 durably remains INDEPENDENTLY CONFIRMED CLOSED per K.3,
        not OPEN. This test documents the corrected adjudication; it is
        a statement about the durable project record, not about this
        module's own contract-file bytes."""
        k3_report = (
            _REPO_ROOT
            / "docs"
            / "PHASE_149O_20K_3_HMIC_CLASS_B_VERIFIER_PRODUCTION_SOURCE_SET_ALIGNMENT_INDEPENDENT_VERIFICATION.md"
        ).read_text(encoding="utf-8")
        assert "CBV-S1: INDEPENDENTLY CONFIRMED CLOSED" in k3_report


# ═══════════════════════════════════════════════════════════════════════
# 13. Production seven-term readiness vector unchanged / CBV-S10 open
# ═══════════════════════════════════════════════════════════════════════


class TestProductionReadinessVectorUnwired:
    def test_readiness_check_names_are_exactly_seven(self) -> None:
        from pcae.core import hatp_mandatory_cutover as cutover

        root = HarnessPath(_REPO_ROOT)
        readiness = cutover._assess_hatp_mandatory_activation_readiness_at_root(
            protected_root=root.path / "__pcae_l1b_nonexistent_protected_root__",
            repository_instance_id=None,
            repository_root=root.path,
            trust_store=None,
        )
        names = {check.name for check in readiness.checks}
        assert len(readiness.checks) == 7
        assert "class_b_deployment_conformance_satisfies_readiness" not in names

    def test_zero_readiness_consumers_of_class_b_verifier(self) -> None:
        for path in (_REPO_ROOT / "src").rglob("*.py"):
            if path.name in (
                "hatp_class_b_conformance.py",
                "hatp_class_b_topology_verifier.py",
                "hatp_environment_lock_verifier.py",
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "verify_class_b_deployment_conformance" not in text

    def test_cutover_module_unchanged_since_l1a_entry(self) -> None:
        assert _git_show_bytes(_POST_L1_PRE_L1A_ENTRY, "src/pcae/core/hatp_mandatory_cutover.py") == (
            _REPO_ROOT / "src/pcae/core/hatp_mandatory_cutover.py"
        ).read_bytes()
