"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R
— Checkpointed RHAMP Execution-Time Class-Identity / State-Trace Campaign
Continuation, Batch-013 Causal Isolation, Production-Reachability
Determination, and F-5 Hold Re-Adjudication.

Fresh, additive-only, minimal phase-specific verification. Diagnostic/
adjudication phase: no production or existing-test change, so this suite
verifies the durable checkpoint/campaign/evidence artifacts this phase
produced (continuing, not resetting, the predecessor's checkpoint chain),
plus the identified root-cause claim itself. Does not modify, skip, or
reference-remove any existing test.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PREDECESSOR_PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R"
PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R"
CAMPAIGN_ID = "RHAMP-XTEST-IDENTITY-TRACE/1"
CORPUS_ID = "RHAMP-XTEST-CORPUS/1"

P_ENTRY = "ac6aee007540cb2433b1714f0c09b7cbbcf19920"
P_CHANGE = "5c86c630"
P_FINAL = "4fe1ba70"  # == this phase's own R0

EVIDENCE_DIR = REPO_ROOT / ".pcae" / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CORPUS_1_manifest.json"
CHECKPOINT_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CHECKPOINT_current.json"
EXPERIMENT_LOG_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CORPUS_1_experiment_log.md"

TRIGGER_FILE = REPO_ROOT / "tests" / "test_phase_147h_authority_evaluation_independent_verification.py"
TRIGGER_NODE = (
    "TestForbiddenDependenciesIndependent::"
    "test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone"
)


def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


class TestPhaseLineageAndCPIPCSuccessor:
    def test_predecessor_entry_commit_is_true_git_parent_of_this_phase_series(self):
        subject = _run_git("log", "-1", "--format=%s", P_ENTRY)
        assert PREDECESSOR_PHASE_ID in subject
        assert "open task" in subject

    def test_predecessor_no_production_diff_from_true_entry_to_final(self):
        diff = _run_git(
            "diff", "--name-only", P_ENTRY, P_FINAL,
            "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts",
        )
        assert diff.strip() == ""

    def test_predecessor_no_existing_test_modification_from_true_entry_to_final(self):
        diff = _run_git("diff", "--name-status", P_ENTRY, P_FINAL, "--", "tests/")
        for line in diff.strip().splitlines():
            status = line.split("\t", 1)[0]
            assert status in ("A",), (
                "predecessor phase must only ADD new test/evidence files, "
                f"never modify an existing one; saw: {line!r}"
            )

    def test_candidate_phase_id_is_a_direct_cpipc_successor_of_the_predecessor(self):
        import sys

        sys.path.insert(0, str(REPO_ROOT / "src"))
        from pcae.core import phase_id as pid

        cand = pid.parse(PHASE_ID)
        pred = pid.parse(PREDECESSOR_PHASE_ID)
        assert pid.same_series(cand, pred)
        assert pid.same_branch(cand, pred)
        assert pid.compare(pred, cand) == "less"
        # Direct successor: candidate's subphase tuple is the predecessor's
        # tuple plus exactly one additional trailing segment.
        assert cand.subphase[: len(pred.subphase)] == pred.subphase
        assert len(cand.subphase) == len(pred.subphase) + 1


class TestCampaignContinuityNotReset:
    def _manifest(self):
        return json.loads(MANIFEST_PATH.read_text())

    def _checkpoint(self):
        return json.loads(CHECKPOINT_PATH.read_text())

    def test_campaign_and_corpus_ids_unchanged(self):
        ck = self._checkpoint()
        assert ck["campaign_id"] == CAMPAIGN_ID
        assert ck["corpus_id"] == CORPUS_ID

    def test_manifest_k0_matches_true_predecessor_entry_commit(self):
        assert self._manifest()["K0"] == P_ENTRY

    def test_checkpoint_chain_references_predecessor_digest(self):
        ck = self._checkpoint()
        assert ck["previous_checkpoint_digest"] == (
            "sha256:3f8ef56abe51e29072bae0fdf13d82a2a1c555788c76745f4c491872368dcf09"
        )

    def test_coverage_categories_reconcile_to_31(self):
        ck = self._checkpoint()
        clean = len(ck["completed_unit_ids"])
        non_clean = len(ck["failed_unit_ids"])
        inconclusive = len(ck["inconclusive_unit_ids"])
        # pending_unit_count is "not yet in completed_unit_ids" (predecessor's
        # own accounting convention) -- i.e. non_clean + inconclusive + never_attempted.
        never_attempted = ck["pending_unit_count"] - inconclusive - non_clean
        assert clean == 18
        assert non_clean == 1
        assert inconclusive == 7
        assert never_attempted == 5
        assert clean + non_clean + inconclusive + never_attempted == 31

    def test_18_clean_batch_ids_unchanged_from_predecessor(self):
        ck = self._checkpoint()
        assert len(ck["completed_unit_ids"]) == 18
        assert not any(
            "batch-013" in uid for uid in ck["completed_unit_ids"]
        ), "the 18 clean batches must not be re-marked, and batch-013 must not be moved into them"

    def test_batch013_evidence_preserved_and_root_caused(self):
        ck = self._checkpoint()
        assert ck["failed_unit_ids"] == ["RHAMP-XTEST-CORPUS-1/batch-013/d164660ae659233b"]
        assert ck["current_root_cause_status"] == "IDENTIFIED"
        assert "root_cause" in ck
        assert ck["root_cause"]["trigger_file"] == (
            "tests/test_phase_147h_authority_evaluation_independent_verification.py"
        )


class TestRootCauseClaimIsSourceVerifiable:
    def test_trigger_file_exists_and_contains_the_named_node(self):
        assert TRIGGER_FILE.exists()
        src = TRIGGER_FILE.read_text()
        assert "def test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone" in src
        assert "class TestForbiddenDependenciesIndependent" in src

    def test_trigger_node_deletes_sys_modules_entries_matching_pcae_core(self):
        src = TRIGGER_FILE.read_text()
        assert '"pcae.core"' in src
        assert "_FORBIDDEN_IMPORT_ROOTS" in src
        assert "del sys.modules[mod_name]" in src

    def test_mechanism_absent_from_production_source(self):
        for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
            src = path.read_text()
            assert "del sys.modules[" not in src, f"sys.modules deletion found in production: {path}"

    def test_mechanism_absent_from_ppa_registration_scripts(self):
        for name in (
            "hpac_protected_presentation_admin.py",
            "hpac_protected_root_admin.py",
        ):
            path = REPO_ROOT / "scripts" / name
            if path.exists():
                src = path.read_text()
                assert "sys.modules" not in src

    def test_trigger_pattern_is_unique_among_all_test_files_touching_pcae_core(self):
        import re

        hits = []
        for path in sorted((REPO_ROOT / "tests").glob("test_*.py")):
            if path == Path(__file__):
                continue  # this suite quotes the pattern in prose/assertions, not as live code
            src = path.read_text(errors="ignore")
            if "del sys.modules[" in src and re.search(r'["\']pcae\.core["\']', src):
                hits.append(path.name)
        assert hits == ["test_phase_147h_authority_evaluation_independent_verification.py"]


class TestF5HoldReAdjudication:
    def test_f5_hold_remains_with_narrow_recorded_reason(self):
        ck = json.loads(CHECKPOINT_PATH.read_text())
        assert ck["current_F5_hold"] == "REMAINS"
        assert "PermissionError" in ck["current_F5_hold_reason"]
        assert "_PROTECTED_ROOT" in ck["current_F5_hold_reason"]

    def test_location_status_is_test_harness_only(self):
        ck = json.loads(CHECKPOINT_PATH.read_text())
        assert ck["current_location_status"] == "TEST_HARNESS_ONLY"


class TestNoProductionOrExistingTestChangeThisPhase:
    def test_no_src_pcae_scripts_pyproject_change_since_r0(self):
        diff = _run_git(
            "diff", "--name-only", P_FINAL, "HEAD",
            "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts",
        )
        assert diff.strip() == ""

    def test_no_existing_test_file_modified_since_r0_only_additions(self):
        diff = _run_git("diff", "--name-status", P_FINAL, "HEAD", "--", "tests/")
        for line in diff.strip().splitlines():
            if not line:
                continue
            status = line.split("\t", 1)[0]
            assert status == "A", f"only new test files may be added this phase; saw: {line!r}"

    def test_no_no_go_mutation_of_the_authority_scripts_this_phase(self):
        diff = _run_git("diff", "--name-only", P_FINAL, "HEAD", "--", "scripts/")
        assert diff.strip() == ""
