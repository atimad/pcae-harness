"""Phase 149O.20L.1A -- HMRC-001 v1.1 HMIC Contract-Identity Alignment
Repair.

Repairs finding B-149O.20L.1-1: Phase 149O.20L.1 amended `HMRC-001` from
v1.0 to v1.1 without touching `HMIC-001` (out of scope for that phase).
This left `HMIC-001`'s own header `Depends on` line -- a descriptive
summary field, not a normative requirement body -- claiming `HMRC-001
v1.0, byte-unchanged`, which became false the moment HMRC-001 was
amended.

This module independently re-derives, without trusting this phase's own
report or 149O.20L.1's report:

  * the pre-149O.20L.1 baseline (HMRC-001 and HMIC-001's `Depends on`
    line agreed at v1.0, at the true 149O.20L.1 phase-entry commit
    `f14e524e`);
  * the post-149O.20L.1, pre-repair mismatch (HMRC-001 live at v1.1,
    HMIC-001's header line still claiming v1.0);
  * that `HMIC-REQ-067`/`HMIC-REQ-069` and production's
    `derive_contract_versions` mechanism were never themselves stale --
    the mechanism reads each bound contract's live `**Version:**` header
    on every call and already, independently of this repair, returns
    `HMRC-001: "1.1"` (Outcome B: pure descriptive-header staleness, not
    a mechanism defect);
  * the exact repair delta in the current, repaired document;
  * that the five-member `contract_versions` family, HMRC-001's own
    bytes, the other four bound-contract identities, HMIC-001's
    twenty-eight-file source scope, the three Class-B verifier modules,
    and production's unwired seven-term readiness vector are all
    unaffected by this repair.

Scope discipline: this phase touches only `HMIC-001`'s own header block
and adds a new descriptive §54 section. No `HMRC-001` byte, no Class-B
verifier module, no other `src/pcae/**` file, and no other contract
file is modified by this phase.
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
_HMIC_CONTRACT_PATH = _REPO_ROOT / "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HMRC_CONTRACT_PATH = _REPO_ROOT / "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_HMIC_TEXT = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
_HMRC_TEXT = _HMRC_CONTRACT_PATH.read_text(encoding="utf-8")

# The true 149O.20L.1 phase-entry commit, independently confirmed via
# `git log --oneline` (the commit immediately preceding 149O.20L.1's own
# first commit, 582226b1) -- not assumed from any prior phase's report.
_PRE_20L1_COMMIT = "f14e524e"


def _git_show(commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


class TestPreviousStateIndependentlyReconstructed:
    """§54.2: at the true 149O.20L.1 phase-entry commit, HMRC-001 and
    HMIC-001's Depends-on line agreed -- the mismatch is a direct, sole
    consequence of 149O.20L.1, not a pre-existing defect."""

    def test_hmrc_was_v1_0_at_phase_entry(self) -> None:
        text = _git_show(_PRE_20L1_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        assert re.search(r"^\*\*Version:\*\*\s*1\.0\s*$", text, re.MULTILINE)

    def test_hmic_depends_on_line_named_hmrc_v1_0_at_phase_entry(self) -> None:
        text = _git_show(
            _PRE_20L1_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        depends_line = re.search(r"^\*\*Depends on.*$", text, re.MULTILINE).group(0)
        assert "HMRC-001 v1.0" in depends_line

    def test_pre_phase_entry_state_was_internally_consistent(self) -> None:
        hmrc_text = _git_show(_PRE_20L1_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        hmic_text = _git_show(
            _PRE_20L1_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        hmrc_version = re.search(r"^\*\*Version:\*\*\s*(\S+)\s*$", hmrc_text, re.MULTILINE).group(1)
        depends_line = re.search(r"^\*\*Depends on.*$", hmic_text, re.MULTILINE).group(0)
        assert f"HMRC-001 v{hmrc_version}" in depends_line


class TestPostL1PreRepairMismatchIndependentlyReconstructed:
    """§54.1: immediately after 149O.20L.1 (the commit this repair phase
    began from), HMRC-001 was v1.1 live while HMIC-001's own header
    still claimed v1.0 -- reconstructed from git history, not assumed."""

    _POST_L1_PRE_REPAIR_COMMIT = "90e14496"  # 149O.20L.1's own final commit, this repair phase's entry point

    def test_hmrc_was_v1_1_immediately_after_149o_20l_1(self) -> None:
        text = _git_show(self._POST_L1_PRE_REPAIR_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        assert re.search(r"^\*\*Version:\*\*\s*1\.1\s*$", text, re.MULTILINE)

    def test_hmic_depends_on_line_still_named_hmrc_v1_0_immediately_after_149o_20l_1(self) -> None:
        text = _git_show(
            self._POST_L1_PRE_REPAIR_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        depends_line = re.search(r"^\*\*Depends on.*$", text, re.MULTILINE).group(0)
        assert "HMRC-001 v1.0" in depends_line

    def test_pre_repair_state_was_a_genuine_mismatch(self) -> None:
        hmrc_text = _git_show(self._POST_L1_PRE_REPAIR_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        hmic_text = _git_show(
            self._POST_L1_PRE_REPAIR_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        hmrc_version = re.search(r"^\*\*Version:\*\*\s*(\S+)\s*$", hmrc_text, re.MULTILINE).group(1)
        depends_line = re.search(r"^\*\*Depends on.*$", hmic_text, re.MULTILINE).group(0)
        assert f"HMRC-001 v{hmrc_version}" not in depends_line


class TestOutcomeBMechanismNeverStale:
    """§54.3: HMIC-REQ-067's normative text and `derive_contract_versions`
    never pinned a version literal for HMRC-001 -- the live-header
    comparison mechanism was correct throughout; only this document's
    own descriptive header line was stale."""

    def test_hmic_req_067_names_no_version_literal_for_hmrc(self) -> None:
        section = re.search(r"\*\*HMIC-REQ-067.*?(?=\*\*HMIC-REQ-068)", _HMIC_TEXT, re.DOTALL).group(0)
        assert "HMRC-001" in section
        assert "1.0" not in section
        assert "1.1" not in section

    def test_hmic_req_069_requires_live_header_comparison(self) -> None:
        section = re.search(r"\*\*HMIC-REQ-069.*?(?=\*\*HMIC-REQ-070)", _HMIC_TEXT, re.DOTALL).group(0)
        assert "current, live version header" in section

    def test_production_contract_identity_files_store_paths_not_versions(self) -> None:
        for contract_id, value in hmic._CONTRACT_IDENTITY_FILES:
            assert isinstance(contract_id, str)
            assert value.startswith("docs/contracts/"), "second tuple element must be a path, never a version literal"

    def test_derive_contract_versions_already_returns_hmrc_1_1(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        versions = hmic.derive_contract_versions(root)
        assert versions["HMRC-001"] == "1.1"


class TestRepairedHeaderState:
    """§54.4: the repaired document's header now accurately states
    HMRC-001 v1.1."""

    def test_depends_on_line_now_states_hmrc_v1_1(self) -> None:
        depends_line = re.search(r"^\*\*Depends on.*$", _HMIC_TEXT, re.MULTILINE).group(0)
        assert "HMRC-001 v1.1" in depends_line
        assert "HMRC-001 v1.0" not in depends_line

    def test_repaired_by_149o_20l_1a_line_present(self) -> None:
        assert "**Repaired by:** Phase 149O.20L.1A" in _HMIC_TEXT

    def test_status_line_names_this_repair(self) -> None:
        status_line = re.search(r"^\*\*Status:\*\*.*$", _HMIC_TEXT, re.MULTILINE).group(0)
        assert "149O.20L.1A" in status_line

    def test_derived_versions_now_match_the_depends_on_line_exactly(self) -> None:
        """The repaired header line and the live derivation mechanism
        must agree for every one of the five members -- not just
        HMRC-001."""
        depends_line = re.search(r"^\*\*Depends on.*:\*\*\s*(.*)$", _HMIC_TEXT, re.MULTILINE).group(1)
        stated = dict(re.findall(r"(\S+-001) v(\S+?)(?:,|$)", depends_line))
        root = HarnessPath(_REPO_ROOT)
        live = dict(hmic.derive_contract_versions(root))
        assert stated == live


class TestVersionUnchangedSameVersionRepair:
    """§54.4: HMIC-001 stays v1.3 -- a same-version repair, mirroring
    §52's (149O.20D.1) precedent."""

    def test_hmic_version_header_still_1_3(self) -> None:
        assert re.search(r"^\*\*Version:\*\*\s*1\.3\s*$", _HMIC_TEXT, re.MULTILINE)

    def test_no_new_hmic_req_identifier_introduced(self) -> None:
        pre_repair_text = _git_show(
            TestPostL1PreRepairMismatchIndependentlyReconstructed._POST_L1_PRE_REPAIR_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        pre_ids = set(re.findall(r"\*\*HMIC-REQ-(\d{3})", pre_repair_text))
        post_ids = set(re.findall(r"\*\*HMIC-REQ-(\d{3})", _HMIC_TEXT))
        assert pre_ids == post_ids


class TestFiveMemberContractFamilyPreserved:
    """§54.5: the contract_versions family is unchanged -- same five
    members, same order, no member displaced by this repair."""

    def test_req_067_still_names_exactly_five_members_same_order(self) -> None:
        section = re.search(r"\*\*HMIC-REQ-067.*?(?=\*\*HMIC-REQ-068)", _HMIC_TEXT, re.DOTALL).group(0)
        order = re.findall(r"`(HMRC-001|HATP-001|HSCE-001|RAE-001|HBDC-001)`", section)
        # dedupe while preserving first-seen order
        seen: "list[str]" = []
        for entry in order:
            if entry not in seen:
                seen.append(entry)
        assert seen == ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"]

    def test_production_contract_identity_files_still_exactly_five_same_order(self) -> None:
        assert [contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES] == [
            "HMRC-001",
            "HATP-001",
            "HSCE-001",
            "RAE-001",
            "HBDC-001",
        ]

    def test_other_four_members_versions_unchanged_by_this_repair(self) -> None:
        pre_repair_text = _git_show(
            TestPostL1PreRepairMismatchIndependentlyReconstructed._POST_L1_PRE_REPAIR_COMMIT,
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        )
        pre_line = re.search(r"^\*\*Depends on.*$", pre_repair_text, re.MULTILINE).group(0)
        post_line = re.search(r"^\*\*Depends on.*$", _HMIC_TEXT, re.MULTILINE).group(0)
        for contract_id in ("HATP-001", "HSCE-001", "RAE-001", "HBDC-001"):
            pre = re.search(rf"{contract_id} v(\S+?)(?:,|$)", pre_line).group(1)
            post = re.search(rf"{contract_id} v(\S+?)(?:,|$)", post_line).group(1)
            assert pre == post, f"{contract_id} version changed by this repair"


class TestHmrcBytesUnchangedByThisPhase:
    """This phase must not touch HMRC-001 at all -- it remains exactly
    as 149O.20L.1 left it."""

    def test_hmrc_bytes_identical_since_this_phase_entry(self) -> None:
        pre_repair_bytes = _git_show(
            TestPostL1PreRepairMismatchIndependentlyReconstructed._POST_L1_PRE_REPAIR_COMMIT,
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        )
        assert pre_repair_bytes == _HMRC_TEXT

    def test_hmrc_still_declares_v1_1(self) -> None:
        assert re.search(r"^\*\*Version:\*\*\s*1\.1\s*$", _HMRC_TEXT, re.MULTILINE)


class TestHmicSourceScopeAndClassBBindingUnaffected:
    """§54.5: this repair touches only HMIC-001's own header/§54 --
    HMIC-REQ-050/052/053 (source scope, twenty-eight files) and
    production's frozen file/contract identity constants are untouched."""

    def test_req_050_still_names_exactly_28(self) -> None:
        assert "twenty-eight" in _HMIC_TEXT

    def test_production_frozen_authority_bearing_files_still_28(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 28

    def test_class_b_verifier_modules_still_present_in_frozen_set(self) -> None:
        for module in (
            "core/hatp_class_b_topology_verifier.py",
            "core/hatp_environment_lock_verifier.py",
            "core/hatp_class_b_conformance.py",
        ):
            assert module in hmic._FROZEN_AUTHORITY_BEARING_FILES

    def test_other_contract_files_not_modified_since_this_phase_entry(self) -> None:
        # Compares the true phase-entry commit against the live working
        # tree (not `HEAD`), so this remains correct both before and
        # after this phase's own commit lands.
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                TestPostL1PreRepairMismatchIndependentlyReconstructed._POST_L1_PRE_REPAIR_COMMIT,
                "--",
                "docs/contracts",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        assert changed == ["docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"]

    def test_no_src_pcae_or_scripts_file_changed_since_this_phase_entry(self) -> None:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                TestPostL1PreRepairMismatchIndependentlyReconstructed._POST_L1_PRE_REPAIR_COMMIT,
                "--",
                "src/pcae",
                "scripts",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""


class TestMismatchFailClosedProof:
    """§54.6: constructs the exact channel this repair closes --
    demonstrating (a) a stored certification with a stale `HMRC-001:
    1.0` expectation genuinely mismatches the live `1.1` state (the
    defect class this finding names, if it were ever load-bearing), and
    (b) the repaired, accurate expectation matches live state exactly."""

    def test_stale_v1_0_expectation_mismatches_live_state(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        live = dict(hmic.derive_contract_versions(root))
        stale_expectation = dict(live)
        stale_expectation["HMRC-001"] = "1.0"
        assert stale_expectation != live

    def test_repaired_v1_1_expectation_matches_live_state(self) -> None:
        root = HarnessPath(_REPO_ROOT)
        live = dict(hmic.derive_contract_versions(root))
        repaired_expectation = dict(live)
        repaired_expectation["HMRC-001"] = "1.1"
        assert repaired_expectation == live


class TestZeroReadinessConsumerAndCbvStatusUnaffected:
    """§17/§18/§19 (steps 17-19 of the governing brief): production
    readiness remains the unwired seven-term vector; CBV-S10/CBV-S1
    verdicts are unaffected by this identity-alignment repair."""

    _CUTOVER_PATH = _REPO_ROOT / "src/pcae/core/hatp_mandatory_cutover.py"

    def test_verify_class_b_deployment_conformance_not_referenced_in_cutover(self) -> None:
        text = self._CUTOVER_PATH.read_text(encoding="utf-8")
        assert "verify_class_b_deployment_conformance" not in text
        assert "class_b_deployment_conformance_satisfies_readiness" not in text

    def test_cbv_s10_remains_open_in_hmic_contract(self) -> None:
        assert "CBV-S10" in _HMIC_TEXT

    def test_cbv_s1_scoped_regression_language_present(self) -> None:
        assert "CBV-S1" in _HMIC_TEXT
        section54 = re.search(r"## 54\..*", _HMIC_TEXT, re.DOTALL).group(0)
        assert "CBV-S1" in section54
        assert "unaffected" in section54.lower()


class TestB149O20L1FindingStatus:
    def test_finding_recorded_as_repaired_not_closed(self) -> None:
        section54 = re.search(r"## 54\..*", _HMIC_TEXT, re.DOTALL).group(0)
        assert "B-149O.20L.1-1: REPAIRED" in section54
        assert "NOT CLOSED" in section54

    def test_recommended_next_phase_is_149o_20l_1b(self) -> None:
        section54 = re.search(r"## 54\..*", _HMIC_TEXT, re.DOTALL).group(0)
        assert "149O.20L.1B" in section54
        assert "149O.20L.2" in section54
