"""Phase 149O.20L.7O.2S.5 — FGSC-001 Staleness Carve-Out Attribution
Completeness Repair Independent Verification.

Fresh, independently-constructed adversarial suite (not copied from the
149O.20L.7O.2S.3/2S.4 suites) verifying the 149O.20L.7O.2S.4 repair of the
2S.3 Blocking finding: ``validate_structured_fast_green()``
(``src/pcae/core/fast_green_attribution.py``) now runs its freshness
(staleness) check *last*, after every other non-freshness structured-
evidence validity check -- including independent attribution/conservation
recomputation -- has already had a chance to append its own issue, so a
"staleness only" issue list is now sound proof nothing else is wrong.

Root-cause reproduction of the exact 2S.3 defect against the pre-repair
checkpoint (commit b9b83c28) is done separately as a disposable script
(not part of this suite, since it requires swapping PYTHONPATH to an old
git worktree) -- see the 2S.5 phase report/doc for that transcript. This
suite exercises current HEAD only.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.core import fast_green_attribution as fga
from pcae.core.phase_reports import PhaseReport, validate_derived_correctness

PHASE_ID = "IV2S5"


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True
    ).stdout.decode().strip()


@pytest.fixture
def repo_and_checkpoint(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "iv25@iv.example"], repo)
    _run(["git", "config", "user.name", "IV25"], repo)
    (repo / "pytest.ini").write_text("[pytest]\nmarkers =\n    fast_green: fg\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_sample.py").write_text(
        "import pytest\n\n@pytest.mark.fast_green\ndef test_ok():\n    assert True\n"
    )
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "chore: pre-phase"], repo)
    (repo / "IMPLEMENTATION.txt").write_text("x")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: implement"], repo)
    return repo, _head(repo)


def _capture(repo: Path, checkpoint: str, pushed_status: str = "local_only") -> dict:
    evidence = fga.build_attribution_evidence(
        repo_root=str(repo), phase_id=PHASE_ID, pushed_status=pushed_status,
        candidate_commit=checkpoint, timeout=120,
    )
    return fga.persist_evidence(str(repo), evidence)


def _finalize_commit(repo: Path) -> None:
    """One ordinary, FGSC-allowed finalization commit that advances HEAD
    past the captured checkpoint."""
    (repo / "PROJECT_STATUS.md").write_text("status\n")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status sync"], repo)


def _retamper(repo: Path, structured: dict, mutate) -> dict:
    artifact_path = repo / structured["provenance"]["artifact_path"]
    persisted = json.loads(artifact_path.read_text())
    mutate(persisted)
    new_digest = fga._canonical_digest(persisted)
    new_artifact_path = artifact_path.parent / f"{new_digest}.json"
    new_artifact_path.write_text(json.dumps(persisted, sort_keys=True, indent=2))
    tampered = dict(persisted)
    tampered["provenance"] = {
        "generated_by_command": structured["provenance"]["generated_by_command"],
        "artifact_path": str(new_artifact_path.relative_to(repo)),
        "artifact_digest": new_digest,
    }
    return tampered


def _certify(repo: Path, tampered: dict, monkeypatch, pushed_status: str = "local_only"):
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "pcae.core.phase_reports.run_stage_b_focused_checks", lambda repo_root: []
    )
    report = PhaseReport(
        phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
        pushed_status=pushed_status,
        test_results={"fast_green": tampered},
    )
    return validate_derived_correctness(report), report


class TestSoleStalenessAccepted:
    def test_valid_sole_staleness_certifies_finalization_verified(
        self, repo_and_checkpoint, monkeypatch
    ):
        """Handoff item 8: an otherwise-fully-valid artifact whose only
        structured issue is checkpoint staleness must still reach
        FINALIZATION_VERIFIED -- the repair must not disable FGSC-001's
        purpose."""
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        tampered = _retamper(repo, structured, lambda p: None)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert issues == [], issues
        assert report.metadata.get("fgsc_lifecycle_state") == "FINALIZATION_VERIFIED"


class TestStalenessPlusEachDefectRejected:
    """Handoff items 9-19: staleness combined with exactly one other
    structured-evidence defect must always reject, and the defect must
    remain visible/attributable rather than being suppressed by the
    staleness carve-out."""

    def test_staleness_plus_attributable_regression(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)

        def mutate(p):
            p["raw_failed"] = sorted(p["raw_failed"] + ["tests/test_sample.py::test_new_regression"])

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("attributable_failures" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_omitted_raw_node(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        pre = "tests/test_sample.py::test_pre"
        omitted = "tests/test_sample.py::test_omitted"

        def mutate(p):
            p["raw_failed"] = sorted([pre, omitted])
            p["baseline_raw_failed"] = [pre]
            p["excluded_preexisting_failures"] = [{
                "node_id": pre, "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            p["attributable_failures"] = []  # omitted node accounted nowhere

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("attributable_failures" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_duplicate_cross_bucket_node(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_dup"

        def mutate(p):
            p["raw_failed"] = [node]
            p["baseline_raw_failed"] = [node]
            p["excluded_preexisting_failures"] = [{
                "node_id": node, "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            p["excluded_environment_failures"] = [{
                "node_id": node, "rerun_result": "pass",
                "rerun_at": "2026-01-01T00:00:00+00:00",
                "rerun_commit": p["candidate_commit"],
            }]
            p["attributable_failures"] = []

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("bucket membership overlaps" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_forged_preexisting(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_forged"

        def mutate(p):
            p["raw_failed"] = [node]  # not in baseline
            p["excluded_preexisting_failures"] = [{
                "node_id": node, "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            p["attributable_failures"] = []

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("excluded_preexisting_failures does not match" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_count_conservation_mismatch(self, repo_and_checkpoint, monkeypatch):
        """Claimed attributable_failures set disagrees with raw/bucket
        cardinality even though every individual bucket looks internally
        plausible."""
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_uncounted"

        def mutate(p):
            p["raw_failed"] = [node]
            p["attributable_failures"] = []  # should be [node]; nothing excludes it

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("attributable_failures" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_raw_error_node(self, repo_and_checkpoint, monkeypatch):
        """A collection/setup error (raw_errors, not raw_failed) must stay
        inside conservation/attribution semantics under staleness too."""
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        err_node = "tests/test_sample.py::test_collection_error"

        def mutate(p):
            p["raw_errors"] = [err_node]
            p["attributable_failures"] = []  # error node unaccounted

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("attributable_failures" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_environment_exclusion_abuse(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        nodes = [f"tests/test_sample.py::test_env_{i}" for i in range(fga.ENVIRONMENT_EXCLUSION_BOUND + 1)]

        def mutate(p):
            p["raw_failed"] = sorted(nodes)
            p["excluded_environment_failures"] = [{
                "node_id": n, "rerun_result": "pass",
                "rerun_at": "2026-01-01T00:00:00+00:00",
                "rerun_commit": p["candidate_commit"],
            } for n in nodes]
            p["attributable_failures"] = []

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("exceeds the bounded policy" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"
        assert fga.ENVIRONMENT_EXCLUSION_BOUND == 3, "2S.4 must not alter the frozen bound"

    def test_staleness_plus_expected_artifact_abuse(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint, pushed_status="local_only")
        node = "tests/test_sample.py::test_arbitrary_expected_artifact"

        def mutate(p):
            p["raw_failed"] = [node]
            p["expected_phase_artifacts"] = [{
                "node_id": node, "predicted_by": "pushed_status",
                "predicted_value": "local_only",
            }]
            p["attributable_failures"] = []

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch, pushed_status="local_only")
        assert any("does not match the closed test identity" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_digest_provenance_defect(self, repo_and_checkpoint, monkeypatch):
        """Corrupt the persisted artifact after digesting so its content no
        longer matches its own claimed digest -- no carve-out for
        artifact-integrity failures."""
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        _finalize_commit(repo)
        artifact_path = repo / structured["provenance"]["artifact_path"]
        persisted = json.loads(artifact_path.read_text())
        persisted["raw_failed"] = ["tests/test_sample.py::test_after_digest_tamper"]
        artifact_path.write_text(json.dumps(persisted, sort_keys=True, indent=2))
        issues, report = _certify(repo, structured, monkeypatch)
        assert any("digest mismatch" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_wrong_baseline(self, repo_and_checkpoint, monkeypatch):
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)

        def mutate(p):
            p["baseline_commit"] = "0" * 40  # not the authoritative phase-entry baseline

        tampered = _retamper(repo, structured, mutate)
        _finalize_commit(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("baseline is not authoritative" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"


class TestNonFGSCFreshnessStillStrict:
    def test_bare_validator_still_flags_staleness_without_fgsc_wiring(self, repo_and_checkpoint):
        """Handoff item 20: calling validate_structured_fast_green()
        directly (outside phase_reports' FGSC carve-out wiring) must still
        report staleness as an issue -- the repair only changed *ordering*,
        not whether freshness is checked."""
        repo, checkpoint = repo_and_checkpoint
        structured = _capture(repo, checkpoint)
        tampered = _retamper(repo, structured, lambda p: None)
        _finalize_commit(repo)
        issues = fga.validate_structured_fast_green(tampered, str(repo), PHASE_ID, "local_only")
        assert any(i.startswith("structured fast_green evidence is stale") for i in issues), issues


class TestIssueIdentityNotOverbroad:
    def test_no_other_issue_message_shares_the_staleness_prefix(self):
        """Handoff item 25: phase_reports.validate_derived_correctness()
        recognizes the sole-staleness carve-out via
        ``issue.startswith("structured fast_green evidence is stale")``,
        a prefix match rather than an exact-identity match. Statically
        confirm no other issue string literal produced anywhere in
        validate_structured_fast_green's source shares that prefix (i.e.
        the prefix match is not currently overbroad in practice, even
        though it is not as robust as a typed/coded identity)."""
        import inspect
        src = inspect.getsource(fga.validate_structured_fast_green)
        prefix = "structured fast_green evidence is stale"
        # Every f-string/string literal issues.append(...) call in the
        # function; crude but sufficient static scan for this closed set.
        import re
        literals = re.findall(r'issues\.append\(\s*f?"([^"]*)"', src)
        stale_literals = [lit for lit in literals if lit.startswith(prefix)]
        assert len(stale_literals) == 1, (
            "expected exactly one issue-message template sharing the "
            f"staleness prefix (the freshness check itself); got {stale_literals!r}"
        )
