"""Phase 149O.20L.7O.2R — Attribution-Aware Verification Gate Implementation.

Focused tests for `pcae.core.fast_green_attribution` and its wiring into
`validate_derived_correctness()`. Uses small synthetic git repositories
(never the real pcae-harness checkout) so each isolated-worktree Fast
Green run stays fast and self-contained.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.core import fast_green_attribution as fga
from pcae.core.phase_reports import PhaseReport, validate_derived_correctness


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "t@t.example"], repo)
    _run(["git", "config", "user.name", "Test"], repo)
    (repo / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    fast_green: fast green tests\n"
    )
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    return repo


_BASELINE_TESTS = '''
import pytest


@pytest.mark.fast_green
def test_preexisting_fail():
    assert False


@pytest.mark.fast_green
def test_always_pass():
    assert True
'''

_CANDIDATE_TESTS_CLEAN_REGRESSION_FREE = '''
import pytest


@pytest.mark.fast_green
def test_preexisting_fail():
    assert False


@pytest.mark.fast_green
def test_always_pass():
    assert True


@pytest.mark.fast_green
def test_new_passing():
    assert True
'''

_CANDIDATE_TESTS_WITH_REGRESSION = '''
import pytest


@pytest.mark.fast_green
def test_preexisting_fail():
    assert False


@pytest.mark.fast_green
def test_always_pass():
    assert True


@pytest.mark.fast_green
def test_new_regression():
    assert False
'''

PHASE_ID = "TESTPH.1"


def _make_repo_with_baseline_and_candidate(tmp_path: Path, candidate_tests: str) -> tuple[Path, str, str]:
    repo = _init_repo(tmp_path)
    (repo / "tests" / "test_sample.py").write_text(_BASELINE_TESTS)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "chore: initial pre-phase state"], repo)
    baseline_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True
    ).stdout.decode().strip()

    (repo / "tests" / "test_sample.py").write_text(candidate_tests)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: implement change"], repo)
    candidate_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True
    ).stdout.decode().strip()

    return repo, baseline_sha, candidate_sha


class TestBaselineDerivation:
    def test_derives_parent_of_first_phase_attributed_commit(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        derived, method = fga.derive_phase_entry_baseline(str(repo), PHASE_ID)
        assert derived == baseline_sha
        assert method == "parent_of_oldest_phase_attributed_commit"

    def test_no_phase_commits_collapses_to_head(self, tmp_path):
        repo = _init_repo(tmp_path)
        (repo / "tests" / "test_sample.py").write_text(_BASELINE_TESTS)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "chore: unrelated work"], repo)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True).stdout.decode().strip()
        derived, method = fga.derive_phase_entry_baseline(str(repo), "NOPHASE.9")
        assert derived == head
        assert method == "no_phase_commits_found_baseline_collapses_to_head"


class TestStructuredAcceptance:
    """Section 27/44 REQUIRED test: structured path accepts a raw-nonzero,
    zero-attributable case that the scalar path would reject."""

    def test_raw_nonzero_zero_attributable_structured_pass_scalar_would_reject(self, tmp_path, monkeypatch):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        monkeypatch.chdir(repo)
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        assert evidence["baseline_commit"] == baseline_sha
        assert evidence["raw_failed"] == ["tests/test_sample.py::test_preexisting_fail"]
        assert evidence["attributable_failures"] == []
        assert len(evidence["excluded_preexisting_failures"]) == 1

        structured_value = fga.persist_evidence(str(repo), evidence)

        # Scalar path: the equivalent raw text would be rejected.
        scalar_report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            test_results={"fast_green": "1 passed, 1 failed"},
        )
        scalar_issues = validate_derived_correctness(scalar_report)
        assert any("fast_green" in i for i in scalar_issues)

        # Structured path: accepted.
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert issues == []

        structured_report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": structured_value},
        )
        structured_report_issues = validate_derived_correctness(structured_report)
        assert structured_report_issues == []


class TestStructuredRejection:
    """Section 27/44 REQUIRED test: a near-identical raw-nonzero structured
    case with exactly one broken invariant is rejected."""

    def _valid_structured_value(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        return repo, fga.persist_evidence(str(repo), evidence)

    def test_omitted_node_rejected(self, tmp_path):
        repo, structured_value = self._valid_structured_value(tmp_path)
        broken = dict(structured_value)
        broken["excluded_preexisting_failures"] = []  # drop the one classification
        # attributable_failures left at [] (already empty) -> now raw node
        # unclassified: neither preexisting nor attributable.
        broken_persist = fga.persist_evidence(str(repo), {k: v for k, v in broken.items() if k != "provenance"})
        issues = fga.validate_structured_fast_green(
            broken_persist, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert issues != []
        assert any("excluded_preexisting_failures" in i or "attributable" in i for i in issues)

    def test_stale_candidate_rejected(self, tmp_path):
        repo, structured_value = self._valid_structured_value(tmp_path)
        # Move HEAD forward with a disposable commit after evidence capture.
        (repo / "README.md").write_text("post-evidence change\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "chore: post-evidence change"], repo)

        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("stale" in i for i in issues)

    def test_duplicate_bucket_membership_rejected(self, tmp_path):
        repo, structured_value = self._valid_structured_value(tmp_path)
        node_id = structured_value["excluded_preexisting_failures"][0]["node_id"]
        broken = dict(structured_value)
        # Also claim the same node as an expected artifact (impossible name
        # match, but exercises the duplicate-membership / unrecognized
        # predicted_by rejection path independently).
        broken["expected_phase_artifacts"] = [
            {"node_id": node_id, "predicted_by": "pushed_status", "predicted_value": "local_only"}
        ]
        broken_persist = fga.persist_evidence(str(repo), {k: v for k, v in broken.items() if k != "provenance"})
        issues = fga.validate_structured_fast_green(
            broken_persist, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert issues != []

    def test_attributable_regression_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_WITH_REGRESSION
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        assert "tests/test_sample.py::test_new_regression" in evidence["attributable_failures"]
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("attributable_failures" in i for i in issues)


class TestHandAuthoredEvidenceRejection:
    def test_missing_artifact_file_rejected(self, tmp_path):
        repo = _init_repo(tmp_path)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "chore: init"], repo)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True).stdout.decode().strip()

        hand_authored = {
            "schema_version": fga.SCHEMA_VERSION,
            "method": "baseline_vs_candidate_isolated_worktree",
            "baseline_commit": head,
            "candidate_commit": head,
            "command": f"whatever -m pytest -m fast_green -q --no-header",
            "raw_failed": [],
            "raw_errors": [],
            "attributable_failures": [],
            "excluded_preexisting_failures": [],
            "excluded_environment_failures": [],
            "expected_phase_artifacts": [],
            "provenance": {
                "generated_by_command": "pcae phase fast-green-attribution",
                "artifact_path": ".pcae/fast-green-attribution/does-not-exist.json",
                "artifact_digest": "deadbeef",
            },
        }
        issues = fga.validate_structured_fast_green(
            hand_authored, repo_root=str(repo), phase_id="X.1", pushed_status="local_only",
        )
        assert any("not found" in i for i in issues)

    def test_digest_mismatch_rejected(self, tmp_path):
        repo = _init_repo(tmp_path)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "chore: init"], repo)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True).stdout.decode().strip()

        artifact_dir = repo / ".pcae" / "fast-green-attribution"
        artifact_dir.mkdir(parents=True)
        artifact_path = artifact_dir / "fake.json"
        artifact_path.write_text(json.dumps({"attributable_failures": [0, 1, 2]}))

        hand_authored = {
            "schema_version": fga.SCHEMA_VERSION,
            "method": "baseline_vs_candidate_isolated_worktree",
            "baseline_commit": head,
            "candidate_commit": head,
            "command": "irrelevant",
            "raw_failed": [], "raw_errors": [], "attributable_failures": [],
            "excluded_preexisting_failures": [], "excluded_environment_failures": [],
            "expected_phase_artifacts": [],
            "provenance": {
                "generated_by_command": "pcae phase fast-green-attribution",
                "artifact_path": ".pcae/fast-green-attribution/fake.json",
                "artifact_digest": "0000000000000000000000000000000000000000000000000000000000000",
            },
        }
        issues = fga.validate_structured_fast_green(
            hand_authored, repo_root=str(repo), phase_id="X.1", pushed_status="local_only",
        )
        assert any("digest mismatch" in i for i in issues)


class TestBaselineManipulationRejection:
    def test_wrong_baseline_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        # Point at a convenient, non-authoritative commit instead.
        evidence["baseline_commit"] = candidate_sha
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("not authoritative" in i for i in issues)


class TestDeselectAttackRejection:
    def test_foreign_command_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        evidence["command"] += " --deselect tests/test_sample.py::test_preexisting_fail"
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("deselection" in i or "does not match the governed" in i for i in issues)


class TestEnvironmentExclusionAbuse:
    def test_missing_rerun_evidence_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_WITH_REGRESSION
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        node = "tests/test_sample.py::test_new_regression"
        assert node in evidence["attributable_failures"]
        evidence["attributable_failures"] = [n for n in evidence["attributable_failures"] if n != node]
        evidence["excluded_environment_failures"] = [
            {"node_id": node, "rerun_result": "narratively a flake, trust me"}
        ]
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("excluded_environment_failures" in i for i in issues)

    def test_bound_exceeded_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_CLEAN_REGRESSION_FREE
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        evidence["excluded_environment_failures"] = [
            {"node_id": f"tests/test_sample.py::fake_{i}", "rerun_result": "pass",
             "rerun_at": "2026-01-01T00:00:00+00:00", "rerun_commit": candidate_sha}
            for i in range(fga.ENVIRONMENT_EXCLUSION_BOUND + 1)
        ]
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("exceeds the bounded policy" in i for i in issues)


class TestExpectedArtifactAbuse:
    def test_arbitrary_test_labeled_expected_rejected(self, tmp_path):
        repo, baseline_sha, candidate_sha = _make_repo_with_baseline_and_candidate(
            tmp_path, _CANDIDATE_TESTS_WITH_REGRESSION
        )
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=candidate_sha, timeout=120,
        )
        node = "tests/test_sample.py::test_new_regression"
        evidence["attributable_failures"] = [n for n in evidence["attributable_failures"] if n != node]
        evidence["expected_phase_artifacts"] = [
            {"node_id": node, "predicted_by": "pushed_status", "predicted_value": "local_only"}
        ]
        structured_value = fga.persist_evidence(str(repo), evidence)
        issues = fga.validate_structured_fast_green(
            structured_value, repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        )
        assert any("closed test identity" in i for i in issues)

    def test_expected_artifact_rejected_once_pushed(self, tmp_path):
        # Even the correctly-named node cannot use this exclusion once
        # pushed_status is already a "pushed" literal (2Q.1 Section 20).
        # The test must be *new* at the candidate commit (not present at
        # baseline), otherwise it would already be classified preexisting.
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("initial\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "chore: init"], repo)
        (repo / "tests" / "test_sample.py").write_text(
            "import pytest\n\n@pytest.mark.fast_green\n"
            "def test_head_equals_origin_main():\n    assert False\n"
        )
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: work"], repo)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True).stdout.decode().strip()

        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="pushed",
            candidate_commit=candidate_sha, timeout=120,
        )
        # Because pushed_status="pushed" was supplied at build time, the
        # tool itself never classifies the node as expected -- it defaults
        # to attributable, matching the closed §20 rule.
        assert "tests/test_sample.py::test_head_equals_origin_main" in evidence["attributable_failures"]


class TestScalarBackwardCompatibility:
    def test_scalar_clean_pass_unaffected(self):
        report = PhaseReport(
            phase_id="X.1", phase_name="x", status="completed", summary="x",
            test_results={"fast_green": "4390/4390"},
        )
        assert validate_derived_correctness(report) == []

    def test_scalar_failing_unaffected(self):
        report = PhaseReport(
            phase_id="X.1", phase_name="x", status="completed", summary="x",
            test_results={"fast_green": "4389/4390, one pre-existing unrelated failure"},
        )
        issues = validate_derived_correctness(report)
        assert any("fast_green" in i for i in issues)

    def test_plain_dict_scalar_mapping_form_unaffected(self):
        report = PhaseReport(
            phase_id="X.1", phase_name="x", status="completed", summary="x",
            test_results={"fast_green": {"passed": 10, "failed": 0}},
        )
        assert validate_derived_correctness(report) == []
