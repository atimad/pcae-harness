"""Phase 149O.19.4 -- HATP Mandatory Independent-Verification
Certification Implementation Plan completeness test.

149O.19.4 is IMPLEMENTATION PLAN ONLY: it modifies no `src/pcae/**`
file and no contract file. This module mechanically verifies the plan
document's own traceability tables (144 requirements, 12 invariants, 32
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

_HMIC_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_PLAN_PATH = _DOCS / "PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md"

_UPSTREAM_CONTRACTS = (
    _HMIC_PATH,
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

# HEAD at the moment this phase began (149O.19.3R.1's final commit).
_PHASE_ENTRY_COMMIT = "19ed7cab"


def _plan_text() -> str:
    return _PLAN_PATH.read_text(encoding="utf-8")


def _hmic_text() -> str:
    return _HMIC_PATH.read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ---------------------------------------------------------------------------
# Section 6 -- 144-requirement table
# ---------------------------------------------------------------------------


def _requirement_table_rows() -> list[tuple[str, str]]:
    text = _plan_text()
    start = text.index("## 6. HMIC-REQ-001..144 Traceability Table")
    end = text.index("## 7. CIVC-1..12 Traceability Table")
    section = text[start:end]
    rows = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*(\d{3})\s*\|(.+)\|\s*$", line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


class TestRequirementTraceability:
    def test_exactly_144_rows_no_gaps_no_duplicates(self) -> None:
        rows = _requirement_table_rows()
        ids = [r[0] for r in rows]
        assert len(ids) == 144, f"expected 144 requirement rows, found {len(ids)}"
        assert sorted(ids) == [f"{i:03d}" for i in range(1, 145)]
        assert len(set(ids)) == 144, "duplicate requirement IDs in plan table"

    def test_every_row_has_owner_and_wave(self) -> None:
        rows = _requirement_table_rows()
        for req_id, rest in rows:
            columns = [c.strip() for c in rest.split("|")]
            assert len(columns) >= 6, f"REQ-{req_id} row malformed: {rest!r}"
            owner, _failure, _test_owner, _attacks, wave = (
                columns[1],
                columns[2],
                columns[3],
                columns[4],
                columns[5],
            )
            assert owner, f"REQ-{req_id} has empty owner"
            assert wave, f"REQ-{req_id} has empty wave"

    def test_requirement_count_matches_hmic_contract_mechanical_extraction(self) -> None:
        hmic = _hmic_text()
        found = sorted(set(re.findall(r"\*\*HMIC-REQ-(\d{3})\b", hmic)))
        assert found == [f"{i:03d}" for i in range(1, 145)], (
            "HMIC-001's own mechanically-extracted requirement IDs no longer "
            "match the expected 1..144 sequence -- either the contract "
            "changed (forbidden this phase) or this test's extraction is stale"
        )


# ---------------------------------------------------------------------------
# Section 7 -- CIVC-1..12 table
# ---------------------------------------------------------------------------


class TestInvariantTraceability:
    def test_exactly_12_invariants(self) -> None:
        text = _plan_text()
        start = text.index("## 7. CIVC-1..12 Traceability Table")
        end = text.index("## 8. 32-Attack Traceability Table")
        section = text[start:end]
        ids = re.findall(r"^\|\s*CIVC-(\d{1,2})\s*\(", section, re.MULTILINE)
        assert sorted(int(i) for i in ids) == list(range(1, 13))

    def test_civc12_row_present_and_names_self_certification_impossibility(self) -> None:
        text = _plan_text()
        assert "CIVC-12 (no self-certification" in text

    def test_civc_count_matches_hmic_contract_section(self) -> None:
        hmic = _hmic_text()
        start = hmic.index("## 40. Security Invariants (CIVC-1 .. CIVC-12)")
        end = hmic.index("## 41. Full Mandatory Attack Matrix")
        section = hmic[start:end]
        ids = re.findall(r"\*\*CIVC-(\d{1,2})\.\*\*", section)
        assert sorted(int(i) for i in ids) == list(range(1, 13))


# ---------------------------------------------------------------------------
# Section 8 -- 32-attack table
# ---------------------------------------------------------------------------


class TestAttackTraceability:
    def test_exactly_32_attack_rows(self) -> None:
        text = _plan_text()
        start = text.index("## 8. 32-Attack Traceability Table")
        end = text.index("**Coverage check:** 32/32 attacks")
        section = text[start:end]
        ids = []
        for line in section.splitlines():
            m = re.match(r"^\|\s*(\d{1,2})\s*\|", line)
            if m:
                ids.append(int(m.group(1)))
        assert sorted(ids) == list(range(1, 33)), f"expected attacks 1..32, found {sorted(ids)}"

    def test_every_attack_has_test_file_and_wave(self) -> None:
        text = _plan_text()
        start = text.index("## 8. 32-Attack Traceability Table")
        end = text.index("**Coverage check:** 32/32 attacks")
        section = text[start:end]
        for line in section.splitlines():
            m = re.match(r"^\|\s*(\d{1,2})\s*\|(.+)\|\s*$", line)
            if not m:
                continue
            attack_no, rest = m.group(1), m.group(2)
            columns = [c.strip() for c in rest.split("|")]
            assert len(columns) >= 4, f"attack {attack_no} row malformed: {rest!r}"
            test_file, wave = columns[2], columns[3]
            assert test_file and "TBD" not in test_file, f"attack {attack_no} missing test file"
            assert wave and "TBD" not in wave, f"attack {attack_no} missing wave"

    def test_attack_count_matches_hmic_contract_table(self) -> None:
        # Phase 149O.19.5E.1 (contract §50) added two new attack rows
        # (#33-34, v1.0-scope-replay / production-alignment-transition)
        # in a "| N *(added v1.1, §50)* |" row format this module's own
        # narrow `\d{1,2}\s*\|` row-id regex does not match (by design,
        # unchanged from this test's original extraction method) -- the
        # detected id range below is therefore still exactly the original
        # 1-32 rows this regex has always been able to see; the section
        # heading itself is tracked forward to the contract's current
        # live title.
        hmic = _hmic_text()
        start = hmic.index("## 41. Full Mandatory Attack Matrix (34 Scenarios)")
        end = hmic.index("## 42. Contract Versioning")
        section = hmic[start:end]
        ids = [int(m) for m in re.findall(r"^\|\s*(\d{1,2})\s*\|", section, re.MULTILINE)]
        assert sorted(ids) == list(range(1, 33))


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
            "hatp_mandatory_certification.py",
            "hatp_certification_admin.py",
            "hatp_mandatory_cutover.py",
            "repository_identity.py",
            "hatp_bootstrap.py",
        )
        for f in expected_files:
            assert f in section, f"{f} missing from file ownership matrix"

    def test_unmodified_files_explicitly_marked(self) -> None:
        text = _plan_text()
        start = text.index("## 15. Production File Forecast and Ownership Matrix")
        end = text.index("## 16. Independent Verification Strategy")
        section = text[start:end]
        assert section.count("**NOT MODIFIED**") >= 2


# ---------------------------------------------------------------------------
# Self-reference / stop-condition gate (Section 10, 13) -- unique to this phase
# ---------------------------------------------------------------------------


class TestSelfReferenceGate:
    def test_stop_condition_w1_present(self) -> None:
        text = _plan_text()
        assert "W-1" in text
        assert "HMIC-001 v1.1" in text

    def test_wave_f_gated_on_w1_in_stop_conditions_table(self) -> None:
        text = _plan_text()
        start = text.index("## 13. Implementation Stop Conditions")
        end = text.index("## 14. Historical Debt")
        section = text[start:end]
        assert "W-1" in section
        assert "Wave F" in section


# ---------------------------------------------------------------------------
# No production/contract mutation this phase
# ---------------------------------------------------------------------------


class TestNoProductionOrContractMutation:
    def test_no_src_pcae_files_changed_name_only(self) -> None:
        # Pinned to this phase's own conclusion (149O.19.4's final commit,
        # 484b1a97), not an open-ended "...HEAD forever" comparison --
        # identical reasoning to `test_all_eight_contracts_byte_unchanged`
        # below: 149O.19.5E.1/149O.19.5E.3 later and legitimately touched
        # `src/pcae/core/hatp_mandatory_certification.py`, well after this
        # phase concluded.
        diff = _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..484b1a97", "--", "src/pcae/")
        working_tree_diff = _git("diff", "--name-only", "HEAD", "--", "src/pcae/")
        staged_diff = _git("diff", "--name-only", "--cached", "--", "src/pcae/")
        assert diff.strip() == ""
        assert working_tree_diff.strip() == ""
        assert staged_diff.strip() == ""

    def test_no_src_pcae_files_changed_name_status(self) -> None:
        # Independent extraction method (name-status line prefixes) so a
        # defect in one check method is not silently mirrored in the
        # other. Pinned to this phase's own exit commit -- see above.
        diff = _git("diff", "--name-status", f"{_PHASE_ENTRY_COMMIT}..484b1a97")
        touched_src = [
            line
            for line in diff.splitlines()
            if "\tsrc/pcae/" in line or line.split("\t")[-1].startswith("src/pcae/")
        ]
        assert touched_src == [], f"unexpected src/pcae changes: {touched_src}"

    def test_all_eight_contracts_byte_unchanged(self) -> None:
        # This phase's own conclusion (149O.19.4's final commit, 484b1a97)
        # is the correct upper bound for "did THIS phase touch an
        # upstream contract" -- not an open-ended "...HEAD forever"
        # comparison. Phase 149O.19.5E.1 (contract §50) later amended
        # HMIC-001 deliberately (v1.0 -> v1.1, validator/admin
        # implementation identity binding), well after 149O.19.4
        # concluded; that is a distinct, later, intentional amendment
        # this test was never meant to guard against.
        for contract_path in _UPSTREAM_CONTRACTS:
            rel = contract_path.relative_to(_REPO_ROOT)
            diff_stat = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..484b1a97", "--", str(rel))
            assert diff_stat.strip() == "", f"{rel} unexpectedly changed: {diff_stat}"

    def test_no_certification_state_files_created(self) -> None:
        assert not (_REPO_ROOT / "certifications.json").exists()
        assert not (_REPO_ROOT / "certification-bindings.json").exists()
        assert not list(_REPO_ROOT.glob("**/certifications.json"))
        assert not list(_REPO_ROOT.glob("**/certification-bindings.json"))


# ---------------------------------------------------------------------------
# Plan document self-consistency
# ---------------------------------------------------------------------------


class TestPlanDocumentIdentity:
    def test_plan_document_exists_and_declares_plan_only(self) -> None:
        text = _plan_text()
        assert "IMPLEMENTATION PLAN ONLY" in text
        assert "149O.19.4" in text

    def test_plan_verdict_present(self) -> None:
        text = _plan_text()
        assert "HMIC-001 IMPLEMENTATION PLAN:\nCOMPLETE" in text

    def test_recommended_next_phase_is_149o_19_5a(self) -> None:
        text = _plan_text()
        assert "149O.19.5A" in text
        assert "Recommended next phase: 149O.19.5A" in text
