"""Phase 149O.17 -- HATP Mandatory Production Consumption Implementation
Plan completeness test.

149O.17 is IMPLEMENTATION PLAN ONLY: it modifies no `src/pcae/**` file
and no contract file. This module mechanically verifies the plan
document's own traceability tables (85 requirements, 14 invariants, 45
attacks) are complete and internally consistent, and that no production
source or contract file was touched by this phase -- by parsing the
actual files, not by trusting the plan document's prose.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_DOCS = _REPO_ROOT / "docs"

_HMRC_PATH = _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_PLAN_PATH = _DOCS / "PHASE_149O_17_HATP_MANDATORY_PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md"

_UPSTREAM_CONTRACTS = (
    _HMRC_PATH,
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

# HEAD at the moment this phase began (149O.16.2's final commit).
_PHASE_ENTRY_COMMIT = "1063d405"


def _plan_text() -> str:
    return _PLAN_PATH.read_text(encoding="utf-8")


def _hmrc_text() -> str:
    return _HMRC_PATH.read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ---------------------------------------------------------------------------
# Section 6 -- 85-requirement table
# ---------------------------------------------------------------------------

_REQ_ROW_RE = re.compile(r"^\|\s*(\d{3})\s*\|(.+)\|\s*$", re.MULTILINE)


def _requirement_table_rows() -> list[tuple[str, str]]:
    text = _plan_text()
    start = text.index("## 6. HMRC-REQ-001..085 Traceability Table")
    end = text.index("## 7. MC-1..MC-14 Traceability Table")
    section = text[start:end]
    rows = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*(\d{3})\s*\|(.+)\|\s*$", line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


class TestRequirementTraceability:
    def test_exactly_85_rows_no_gaps_no_duplicates(self) -> None:
        rows = _requirement_table_rows()
        ids = [r[0] for r in rows]
        assert len(ids) == 85, f"expected 85 requirement rows, found {len(ids)}"
        assert sorted(ids) == [f"{i:03d}" for i in range(1, 86)]
        assert len(set(ids)) == 85, "duplicate requirement IDs in plan table"

    def test_every_row_has_owner_and_wave(self) -> None:
        rows = _requirement_table_rows()
        for req_id, rest in rows:
            columns = [c.strip() for c in rest.split("|")]
            assert len(columns) >= 6, f"REQ-{req_id} row malformed: {rest!r}"
            owner, _failure, _test_owner, _attacks, wave = columns[1], columns[2], columns[3], columns[4], columns[5]
            assert owner, f"REQ-{req_id} has empty owner"
            assert wave, f"REQ-{req_id} has empty wave"

    def test_requirement_count_matches_hmrc_contract_mechanical_extraction(self) -> None:
        hmrc = _hmrc_text()
        found = sorted(set(re.findall(r"\*\*HMRC-REQ-(\d{3})\b", hmrc)))
        assert found == [f"{i:03d}" for i in range(1, 86)], (
            "HMRC-001's own mechanically-extracted requirement IDs no longer "
            "match the expected 1..85 sequence -- either the contract changed "
            "(forbidden this phase) or this test's extraction is stale"
        )


# ---------------------------------------------------------------------------
# Section 7 -- MC-1..MC-14 table
# ---------------------------------------------------------------------------


class TestInvariantTraceability:
    def test_exactly_14_invariants(self) -> None:
        text = _plan_text()
        start = text.index("## 7. MC-1..MC-14 Traceability Table")
        end = text.index("## 8. 45-Attack Traceability Table")
        section = text[start:end]
        ids = re.findall(r"^\|\s*MC-(\d{1,2})\s*\(", section, re.MULTILINE)
        assert sorted(int(i) for i in ids) == list(range(1, 15))

    def test_mc14_row_present_and_names_effect_truthful_requirement(self) -> None:
        text = _plan_text()
        assert "MC-14 (effect-truthful PB requirement)" in text.lower() or "MC-14 (effect-truthful PB requirement)" in text


# ---------------------------------------------------------------------------
# Section 8 -- 45-attack table
# ---------------------------------------------------------------------------


class TestAttackTraceability:
    def test_exactly_45_attack_rows(self) -> None:
        text = _plan_text()
        start = text.index("## 8. 45-Attack Traceability Table")
        end = text.index("**Coverage check:** 45/45 attacks")
        section = text[start:end]
        ids = []
        for line in section.splitlines():
            m = re.match(r"^\|\s*(\d{1,2})\s*\|", line)
            if m:
                ids.append(int(m.group(1)))
        assert sorted(ids) == list(range(1, 46)), f"expected attacks 1..45, found {sorted(ids)}"

    def test_every_attack_has_test_file_and_wave(self) -> None:
        text = _plan_text()
        start = text.index("## 8. 45-Attack Traceability Table")
        end = text.index("**Coverage check:** 45/45 attacks")
        section = text[start:end]
        for line in section.splitlines():
            m = re.match(r"^\|\s*(\d{1,2})\s*\|(.+)\|\s*$", line)
            if not m:
                continue
            attack_no, rest = m.group(1), m.group(2)
            columns = [c.strip() for c in rest.split("|")]
            assert len(columns) >= 6, f"attack {attack_no} row malformed: {rest!r}"
            test_file, wave = columns[4], columns[5]
            assert test_file and "TBD" not in test_file, f"attack {attack_no} missing test file"
            assert wave and "TBD" not in wave, f"attack {attack_no} missing wave"

    def test_attack_count_matches_hmrc_contract_table(self) -> None:
        hmrc = _hmrc_text()
        start = hmrc.index("## 29. Full Mandatory Attack Matrix (45 Scenarios)")
        end = hmrc.index("## 30. Contract Versioning")
        section = hmrc[start:end]
        ids = [int(m) for m in re.findall(r"^\|\s*(\d{1,2})\s*\|", section, re.MULTILINE)]
        assert sorted(ids) == list(range(1, 46))


# ---------------------------------------------------------------------------
# Production file ownership matrix (Section 15)
# ---------------------------------------------------------------------------


class TestFileOwnershipCompleteness:
    def test_every_planned_production_file_appears_in_ownership_matrix(self) -> None:
        text = _plan_text()
        start = text.index("## 15. Production File Forecast and Ownership Matrix")
        end = text.index("## 16. Independent Verification Strategy")
        section = text[start:end]
        expected_files = (
            "hatp_mandatory_cutover.py",
            "hatp_rollback_consumption.py",
            "core/agent.py",
            "commands/agent.py",
            "cli.py",
            "hatp_ag_authority.py",
        )
        for f in expected_files:
            assert f in section, f"{f} missing from file ownership matrix"

    def test_unmodified_engines_explicitly_marked(self) -> None:
        text = _plan_text()
        start = text.index("## 15. Production File Forecast and Ownership Matrix")
        end = text.index("## 16. Independent Verification Strategy")
        section = text[start:end]
        assert section.count("**NOT MODIFIED**") >= 6


# ---------------------------------------------------------------------------
# No production/contract mutation this phase
# ---------------------------------------------------------------------------


class TestNoProductionOrContractMutation:
    def test_no_src_pcae_files_changed_name_only(self) -> None:
        diff = _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/")
        working_tree_diff = _git("diff", "--name-only", "HEAD", "--", "src/pcae/")
        staged_diff = _git("diff", "--name-only", "--cached", "--", "src/pcae/")
        assert diff.strip() == ""
        assert working_tree_diff.strip() == ""
        assert staged_diff.strip() == ""

    def test_no_src_pcae_files_changed_name_status(self) -> None:
        # Independent extraction method (name-status line prefixes) so a
        # defect in one check method is not silently mirrored in the other.
        diff = _git("diff", "--name-status", f"{_PHASE_ENTRY_COMMIT}..HEAD")
        touched_src = [
            line for line in diff.splitlines() if "\tsrc/pcae/" in line or line.split("\t")[-1].startswith("src/pcae/")
        ]
        assert touched_src == [], f"unexpected src/pcae changes: {touched_src}"

    def test_all_seven_contracts_byte_unchanged(self) -> None:
        for contract_path in _UPSTREAM_CONTRACTS:
            rel = contract_path.relative_to(_REPO_ROOT)
            diff_stat = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", str(rel))
            assert diff_stat.strip() == "", f"{rel} unexpectedly changed: {diff_stat}"


# ---------------------------------------------------------------------------
# Plan document self-consistency
# ---------------------------------------------------------------------------


class TestPlanDocumentIdentity:
    def test_plan_document_exists_and_declares_plan_only(self) -> None:
        text = _plan_text()
        assert "IMPLEMENTATION PLAN ONLY" in text
        assert "PHASE_149O_17" in _PLAN_PATH.name.upper() or "149O_17" in _PLAN_PATH.name

    def test_plan_verdict_present(self) -> None:
        text = _plan_text()
        assert "HATP MANDATORY PRODUCTION CONSUMPTION IMPLEMENTATION PLAN: COMPLETE" in text

    def test_recommended_next_phase_is_149o_18a(self) -> None:
        text = _plan_text()
        assert "149O.18A" in text
        assert "Recommended next phase: 149O.18A" in text
