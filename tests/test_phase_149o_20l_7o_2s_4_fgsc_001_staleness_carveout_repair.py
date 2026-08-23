"""Phase 149O.20L.7O.2S.4 — FGSC-001 Staleness Carve-Out / Attribution
Completeness Narrow Repair.

Focused + adversarial tests for the repair of the 149O.20L.7O.2S.3 Blocking
finding: ``validate_structured_fast_green()``'s freshness (staleness) check
used to be computed *before* independent attribution/conservation
recomputation, and an internal ``if issues: return issues`` guard could
return a "staleness only" issue list to
``phase_reports.validate_derived_correctness()`` *before* the real
attribution defect had been computed at all -- letting the FGSC-001
carve-out (docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_
CONTRACT.md) incorrectly certify FINALIZATION_VERIFIED for an artifact that
also carried a genuine, unclassified regression.

The repair (``src/pcae/core/fast_green_attribution.py``) moves the
freshness check to run *last*, after every other non-freshness structured-
evidence validity check (including the independent attribution/
conservation recomputation) has already had a chance to append its own
issue. A "staleness only" result is therefore now sound proof that nothing
else is wrong.

This suite builds its own disposable synthetic git repositories (mirrors
``tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_
verification.py``'s style) and exercises the exact attack matrix required
by the 2S.4 handoff: a valid nonzero-raw-but-fully-excluded case that must
still pass under staleness, and five independent "staleness + some other
structured-evidence defect" cases that must all still fail. The genuine
"staleness + unclassified regression" case (the 2S.3 headline finding
itself) is covered by the two now-flipped tests in
``test_phase_149o_20l_7o_2s_3_...py::TestStalenessCarveOutSoundness`` and is
deliberately not duplicated here.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.core import fast_green_attribution as fga
from pcae.core.phase_reports import PhaseReport, validate_derived_correctness

PHASE_ID = "IV2S4"


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True
    ).stdout.decode().strip()


def _checkpoint_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "iv@iv.example"], repo)
    _run(["git", "config", "user.name", "IndependentVerifier"], repo)
    (repo / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    fast_green: fast green tests\n"
    )
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "tests" / "test_sample.py").write_text(
        "import pytest\n\n\n@pytest.mark.fast_green\ndef test_always_pass():\n    assert True\n"
    )
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "chore: pre-phase state"], repo)
    (repo / "src" / "thing.py").write_text("VALUE = 1\n")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: implement change"], repo)
    return repo, _head(repo)


def _capture(repo: Path, checkpoint: str, pushed_status: str = "local_only") -> dict:
    evidence = fga.build_attribution_evidence(
        repo_root=str(repo), phase_id=PHASE_ID, pushed_status=pushed_status,
        candidate_commit=checkpoint, timeout=120,
    )
    return fga.persist_evidence(str(repo), evidence)


def _restale(repo: Path) -> None:
    """One ordinary, contract-allowed Class-B finalization commit."""
    (repo / "PROJECT_STATUS.md").write_text("status\n")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)


def _persist_mutation(repo: Path, structured: dict, mutate) -> dict:
    """Apply `mutate` to the persisted evidence dict, re-digest, write a new
    content-addressed artifact, and return a tampered structured value
    wired to it (mirrors the 2S.3 suite's approach: mutating the persisted
    artifact directly is the honest way to synthesize an otherwise-
    unreachable evidence shape without hand-forging digests)."""
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


def _certify(repo: Path, tampered: dict, monkeypatch, pushed_status: str = "local_only") -> list[str]:
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


class TestValidStalenessCasesStillPass:
    def test_nonzero_raw_fully_preexisting_and_stale_still_passes(self, tmp_path, monkeypatch):
        """Item 11 — nonzero raw failures, all genuinely pre-existing
        against baseline, zero independently recomputed attributable
        failures, staleness present only via an allowed finalization
        delta. Must still reach FINALIZATION_VERIFIED: the repair must not
        disable FGSC's purpose."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_flaky_but_preexisting"

        def mutate(p):
            p["raw_failed"] = sorted(p["raw_failed"] + [node])
            p["baseline_raw_failed"] = sorted(p["baseline_raw_failed"] + [node])
            p["excluded_preexisting_failures"] = p["excluded_preexisting_failures"] + [{
                "node_id": node,
                "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert issues == [], f"expected sole-staleness (with valid exclusions) to pass; got {issues!r}"
        assert report.metadata.get("fgsc_lifecycle_state") == "FINALIZATION_VERIFIED"


class TestStalenessPlusOtherDefectsStillFail:
    """Items 13-17. Each scenario combines an allowed finalization delta
    (staleness) with exactly one other structured-evidence defect. All must
    still be rejected -- staleness eligibility must never suppress any of
    these checks."""

    def test_staleness_plus_omitted_node_rejected(self, tmp_path, monkeypatch):
        """Item 13 — one raw failure correctly excluded as pre-existing,
        one raw failure omitted from every bucket (falsely absent from
        attributable_failures too)."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint)
        preexisting_node = "tests/test_sample.py::test_flaky"
        omitted_node = "tests/test_sample.py::test_evil_omitted"

        def mutate(p):
            p["raw_failed"] = sorted([preexisting_node, omitted_node])
            p["baseline_raw_failed"] = [preexisting_node]
            p["excluded_preexisting_failures"] = [{
                "node_id": preexisting_node,
                "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            # attributable_failures falsely claims empty -- omitted_node
            # accounted for nowhere.
            p["attributable_failures"] = []

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("attributable_failures" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_cross_bucket_duplicate_rejected(self, tmp_path, monkeypatch):
        """Item 14 — the same node ID claimed in two buckets at once
        (excluded_preexisting_failures and excluded_environment_failures)."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_flaky"

        def mutate(p):
            p["raw_failed"] = [node]
            p["baseline_raw_failed"] = [node]
            p["excluded_preexisting_failures"] = [{
                "node_id": node,
                "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            p["excluded_environment_failures"] = [{
                "node_id": node,
                "rerun_result": "pass",
                "rerun_at": "2026-01-01T00:00:00+00:00",
                "rerun_commit": p["candidate_commit"],
            }]
            p["attributable_failures"] = []

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("bucket membership overlaps" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_forged_preexisting_label_rejected(self, tmp_path, monkeypatch):
        """Item 15 — a genuine candidate-only failure (absent from
        baseline) falsely labeled excluded_preexisting_failures."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint)
        node = "tests/test_sample.py::test_evil_forged_preexisting"

        def mutate(p):
            p["raw_failed"] = [node]
            # baseline_raw_failed deliberately left empty -- node is NOT
            # actually pre-existing.
            p["excluded_preexisting_failures"] = [{
                "node_id": node,
                "baseline_commit": p["baseline_commit"],
                "baseline_evidence": "failed_in_baseline",
            }]
            p["attributable_failures"] = []

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any(
            "excluded_preexisting_failures does not match the recomputed" in i
            for i in issues
        ), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"

    def test_staleness_plus_environment_bound_abuse_rejected(self, tmp_path, monkeypatch):
        """Item 16 — environment-exclusion volume abuse (exceeding the
        frozen ENVIRONMENT_EXCLUSION_BOUND=3) must still be caught under
        staleness. (A single structurally well-formed environment-rerun
        entry is a pre-existing, carried, non-Blocking trust concern (2R.1
        'environment-timeout exclusion weakness') that this narrow repair
        does not touch or newly claim to close; the bound itself, which
        2S.4 must not alter, is what this test exercises.)"""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint)
        nodes = [f"tests/test_sample.py::test_evil_env_{i}" for i in range(4)]

        def mutate(p):
            p["raw_failed"] = sorted(nodes)
            p["excluded_environment_failures"] = [
                {
                    "node_id": n,
                    "rerun_result": "pass",
                    "rerun_at": "2026-01-01T00:00:00+00:00",
                    "rerun_commit": p["candidate_commit"],
                }
                for n in nodes
            ]
            p["attributable_failures"] = []

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch)
        assert any("exceeds the bounded policy" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"
        assert fga.ENVIRONMENT_EXCLUSION_BOUND == 3

    def test_staleness_plus_expected_artifact_abuse_rejected(self, tmp_path, monkeypatch):
        """Item 17 — an arbitrary failure (not the closed
        test_head_equals_origin_main identity) falsely labeled
        expected_phase_artifacts."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = _capture(repo, checkpoint, pushed_status="local_only")
        node = "tests/test_sample.py::test_evil_expected_artifact_abuse"

        def mutate(p):
            p["raw_failed"] = [node]
            p["expected_phase_artifacts"] = [{
                "node_id": node,
                "predicted_by": "pushed_status",
                "predicted_value": "local_only",
            }]
            p["attributable_failures"] = []

        tampered = _persist_mutation(repo, structured, mutate)
        _restale(repo)
        issues, report = _certify(repo, tampered, monkeypatch, pushed_status="local_only")
        assert any("does not match the closed test identity" in i for i in issues), issues
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"
