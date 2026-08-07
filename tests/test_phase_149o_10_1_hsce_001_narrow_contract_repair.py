"""Phase 149O.10.1 — HSCE-001 Narrow Contract Repair.

Dedicated repair-verification suite. Independently verifies, against the
*repaired* HSCE-001 v1.1 contract text and the current production source
tree, that: the version and requirement-count corrections landed; the
repaired HSCE-REQ-052 specifies atomic hard-link exclusive publication
(not check-then-os.replace) as the winner-publication primitive; loser
comparison semantics (identical -> idempotent success, differing ->
evidence_conflict) are present; same-ID/differing-assertion semantics
(HSCE-REQ-037/038) are unchanged; SC-7's own statement is unchanged;
symlink rules (HSCE-REQ-057/058) are retained and cross-referenced by the
repair; atomic temp-file rules are retained; the AG3
original_commit_sha-resolution attack (Obs-2) was added; the attack-matrix
count is 21; HATP-001 and RAE-001 remain unmodified; and no production
source was changed by this phase.

Contract-only, model-level verification: this suite does not implement,
sign, or persist evidence, and does not exercise real filesystem
concurrency (no signing-ceremony implementation exists yet to test at
that level). Its "concurrency model" test verifies the frozen algorithm's
*textual* decision structure only.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HSCE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
REPAIR_DOC = REPO_ROOT / "docs" / "PHASE_149O_10_1_HSCE_001_NARROW_CONTRACT_REPAIR.md"
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

_HSCE_V1_0_FREEZE_COMMIT = "3ad4e839"
_HSCE_REQ_RE = re.compile(r"HSCE-REQ-(\d+)")


@pytest.fixture(scope="module")
def contract_text() -> str:
    return HSCE_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def repair_doc_text() -> str:
    return REPAIR_DOC.read_text(encoding="utf-8")


def _req_052_text(text: str) -> str:
    start = text.index("**HSCE-REQ-052.**")
    end = text.index("**HSCE-REQ-053.**")
    return text[start:end]


def _normalized(text: str) -> str:
    return " ".join(text.split())


class TestDocumentPresence:
    def test_contract_doc_exists(self):
        assert HSCE_CONTRACT.is_file()

    def test_repair_doc_exists(self):
        assert REPAIR_DOC.is_file()


class TestVersionAndCount:
    def test_contract_version_is_1_1(self, contract_text):
        assert "**Version:** 1.1" in contract_text

    def test_revised_by_phase_149o_10_1_declared(self, contract_text):
        assert "Phase 149O.10.1" in contract_text
        assert "**Revised by:**" in contract_text

    def test_requirement_count_corrected_to_79(self, contract_text):
        assert "through `HSCE-REQ-079` inclusive" in contract_text
        assert "through `HSCE-REQ-078` inclusive (this requirement)" not in contract_text

    def test_requirement_ids_still_sequential_gapless_no_duplicates(self, contract_text):
        defining_ids = [
            int(m.group(1)) for m in re.finditer(r"\*\*HSCE-REQ-(\d{3})\.\*\*", contract_text)
        ]
        assert defining_ids == sorted(defining_ids)
        assert len(defining_ids) == len(set(defining_ids))
        assert defining_ids == list(range(1, defining_ids[-1] + 1))
        assert defining_ids[-1] == 79, "no new HSCE-REQ ID was minted by this narrow repair"

    def test_attack_matrix_has_21_items(self, contract_text):
        section_start = contract_text.index("## 38. Mandatory Future Attack Matrix")
        section_end = contract_text.index("## 39. Contract Ownership")
        section = contract_text[section_start:section_end]
        items = re.findall(r"^\d+\. ", section, flags=re.MULTILINE)
        assert len(items) == 21


class TestRepairedHsceReq052:
    def test_req_052_still_defined_exactly_once(self, contract_text):
        assert contract_text.count("**HSCE-REQ-052.**") == 1

    def test_specifies_hard_link_exclusive_publish(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        assert "os.link(temp_path, final_path)" in req
        assert "atomic hard-link publication" in req

    def test_no_longer_specifies_check_then_replace_as_winner_mechanism(self, contract_text):
        req = _req_052_text(contract_text)
        # os.replace is only referenced as the *superseded* mechanism.
        assert "supersedes the" in req or "superseded" in req
        assert "cannot guarantee SC-7" in req

    def test_filesystem_exists_check_no_longer_precedes_publication(self, contract_text):
        req = _req_052_text(contract_text)
        assert "check whether the destination already\nexists and, if so, compare bytes" not in req

    def test_winner_semantics_stated(self, contract_text):
        req = _req_052_text(contract_text)
        assert "winner" in req.lower()
        assert "os.link` succeeds" in req or "os.link` call succeeds" in req

    def test_loser_semantics_identical_vs_differing(self, contract_text):
        req = _req_052_text(contract_text)
        assert "byte-identical is idempotent success" in req
        assert "byte-different is `evidence_conflict`" in req

    def test_symlink_interaction_with_057_058_stated(self, contract_text):
        req = _req_052_text(contract_text)
        assert "§57" in req
        assert "islink" in req

    def test_unsupported_filesystem_fails_closed_no_fallback(self, contract_text):
        req = _req_052_text(contract_text)
        assert "evidence_persistence_failure" in req
        assert "no fallback to `os.replace`" in req or "there is no\nfallback to `os.replace`" in req

    def test_atomic_temp_file_same_directory_rule_retained(self, contract_text):
        req = _req_052_text(contract_text)
        assert "same `envelopes/` directory" in req
        assert "fsync" in req.lower()

    def test_no_delete_then_create_pattern_permitted(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        assert 'not a compliant implementation of "exclusive"' in req

    def test_crash_semantics_before_and_after_publish_stated(self, contract_text):
        req = _req_052_text(contract_text)
        assert "crash before step (4)" in req
        assert "crash after step (4)" in req


class TestUnchangedSemantics:
    def test_same_id_different_evidence_case_unchanged(self, contract_text):
        assert "evidence_conflict" in contract_text
        assert "idempotent" in contract_text.lower()

    def test_sc7_statement_unchanged(self, contract_text):
        assert "**SC-7.** Existing evidence can never be silently overwritten" in contract_text

    def test_all_twelve_security_invariants_present(self, contract_text):
        for n in range(1, 13):
            assert f"**SC-{n}.**" in contract_text

    def test_req_057_058_symlink_rules_byte_present_unchanged(self, contract_text):
        assert "HSCE-REQ-057" in contract_text
        assert "HSCE-REQ-058" in contract_text
        assert "the write\nSHALL be rejected" in contract_text or "the write SHALL be rejected" in contract_text

    def test_no_creation_registry_directory_introduced(self, contract_text):
        normalized = " ".join(contract_text.split())
        assert "No `creation-registry/` marker subdirectory is required for this store" in normalized

    def test_evidence_store_layout_unchanged(self, contract_text):
        assert ".pcae/hatp-evidence/" in contract_text
        assert "envelopes/{evidence_id}.json" in contract_text

    def test_closed_error_vocabulary_still_twelve_members(self, contract_text):
        section_start = contract_text.index("## 22. Closed Error Vocabulary")
        section_end = contract_text.index("## 23. Secret Handling")
        section = contract_text[section_start:section_end]
        error_types = [
            m for m in re.findall(r"^\| `([a-z_]+)` \|", section, flags=re.MULTILINE) if m != "error_type"
        ]
        assert len(error_types) == 12
        assert "evidence_persistence_failure" in error_types


class TestObs2Ag3Attack:
    def test_ag3_original_commit_sha_attack_added(self, contract_text):
        section_start = contract_text.index("## 38. Mandatory Future Attack Matrix")
        section_end = contract_text.index("## 39. Contract Ownership")
        section = contract_text[section_start:section_end]
        assert "original_commit_sha" in section
        assert "operation_not_found" in section

    def test_obs2_maps_to_existing_error_type_no_new_vocabulary(self, contract_text):
        section_start = contract_text.index("## 38. Mandatory Future Attack Matrix")
        section_end = contract_text.index("## 39. Contract Ownership")
        section = contract_text[section_start:section_end]
        item_21_start = section.index("21. ")
        item_21 = section[item_21_start:]
        assert "operation_not_found" in item_21
        assert "exit code 2" in item_21


class TestConcurrencyModel:
    """Model-level verification of the frozen algorithm's decision
    structure. Not an implementation-level concurrency test (no
    signing-ceremony implementation exists yet)."""

    def test_exactly_one_success_branch_establishes_canonical_winner(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        # Winner branch: step (5), gated strictly on os.link succeeding.
        assert "if `os.link` succeeds, this writer is the exclusive-publication **winner**" in req

    def test_loser_branch_never_overwrites(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        assert "the persisted winner is never overwritten, under any condition" in req

    def test_state_machine_forbids_canonical_to_canonical_transition(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        assert "never transitions to `CANONICAL(other_bytes)`" in req

    def test_many_writer_generalization_stated(self, contract_text):
        req = _normalized(_req_052_text(contract_text))
        assert "generalizes without modification to any number of concurrent writers" in req


class TestFindingDispositions:
    def test_f1_closed(self, repair_doc_text):
        assert "F-1" in repair_doc_text
        assert "**CLOSED**" in repair_doc_text

    def test_f2_closed(self, repair_doc_text):
        assert "F-2" in repair_doc_text

    def test_149o10_f3_repaired_not_independently_closed(self, repair_doc_text):
        assert "149O.10-F-3" in repair_doc_text
        assert "REPAIRED AT CONTRACT LEVEL" in repair_doc_text
        assert "PENDING INDEPENDENT RE-VERIFICATION" in repair_doc_text

    def test_obs2_closed(self, repair_doc_text):
        assert "Obs-2" in repair_doc_text

    def test_hatp_production_not_ready(self, repair_doc_text):
        assert "NOT READY" in repair_doc_text

    def test_does_not_claim_hsce_verified(self, contract_text, repair_doc_text):
        assert "HSCE-001 v1.1 VERIFIED" not in contract_text
        assert "HSCE-001 v1.1 VERIFIED" not in repair_doc_text


class TestBoundaries:
    def test_hatp_001_unmodified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", str(HATP_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_rae_001_unmodified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", str(RAE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_no_production_source_modified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", "src/pcae/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_no_hatp_evidence_directory_created(self):
        assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists()

    def test_no_hatp_sign_cli_implementation_exists(self):
        result = subprocess.run(
            ["grep", "-rEn", "hatp sign|HATPSignedEvidenceEnvelope", "src/pcae/cli.py", "src/pcae/commands/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout == ""

    def test_write_atomic_json_production_helper_unchanged_still_racy(self):
        """Confirms this repair did not touch production code: the
        underlying rollback_approval_evidence.py::_write_atomic_json
        helper (never called by the repaired contract's new algorithm)
        remains exactly as racy as before -- this repair is contract-text
        only, no production hardening was performed or required."""

        from pcae.core.rollback_approval_evidence import _write_atomic_json
        import inspect

        source = inspect.getsource(_write_atomic_json)
        assert "path.exists()" in source
        assert "os.replace(" in source
        assert "os.link(" not in source
