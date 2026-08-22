"""Phase 149O.20L.7O.2S.2 — FGSC-001 Structured Fast Green Self-
Certification Lifecycle Implementation.

Focused + adversarial tests for the FGSC-001 v1.0 mechanism
(``docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md``):
path classification (contract §4), diff authority (§6/§7), and the
lifecycle-freshness carve-out wired into
``validate_derived_correctness()`` (§14). Uses small synthetic git
repositories (never the real pcae-harness checkout) so each scenario stays
fast and self-contained, mirroring
``tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core import fast_green_attribution as fga
from pcae.core.phase_reports import (
    PhaseReport,
    run_stage_b_focused_checks,
    validate_derived_correctness,
)

PHASE_ID = "TESTPH.2"


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True
    ).stdout.decode().strip()


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


_TESTS_SRC = '''
import pytest


@pytest.mark.fast_green
def test_always_pass():
    assert True
'''


def _make_repo_with_checkpoint(tmp_path: Path) -> tuple[Path, str, str]:
    """Repo with one pre-phase commit and one phase-attributed commit whose
    HEAD becomes the checkpoint once evidence is captured against it."""
    repo = _init_repo(tmp_path)
    (repo / "tests" / "test_sample.py").write_text(_TESTS_SRC)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "chore: initial pre-phase state"], repo)

    (repo / "src" / "thing.py").write_text("VALUE = 1\n")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: implement change"], repo)
    checkpoint = _head(repo)
    return repo, checkpoint, checkpoint


def _capture_structured_evidence(repo: Path, checkpoint: str) -> dict:
    evidence = fga.build_attribution_evidence(
        repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
        candidate_commit=checkpoint, timeout=120,
    )
    return fga.persist_evidence(str(repo), evidence)


# ---------------------------------------------------------------------
# Path classification (contract §4)
# ---------------------------------------------------------------------

class TestPathClassification:
    @pytest.mark.parametrize("path", [
        "src/pcae/core/foo.py",
        "scripts/bootstrap.sh",
        "tests/test_x.py",
        "docs/contracts/SOME_CONTRACT.md",
        "pyproject.toml",
        "conftest.py",
        "sub/dir/conftest.py",
        ".githooks/pre-commit",
    ])
    def test_class_a_paths(self, path):
        assert fga.classify_finalization_path(path) == fga.FinalizationPathClass.A

    @pytest.mark.parametrize("path", [
        ".pcae/phase-completion-metadata.json",
        ".pcae/phase-completion-report.md",
        "PROJECT_STATUS.md",
        "CHANGELOG.md",
        "tasks/DONE.md",
        "tasks/active/x.md",
        "tasks/done/y.md",
        ".pcae/fast-green-attribution/abc123.json",
        ".pcae/session.json",
    ])
    def test_class_b_paths(self, path):
        assert fga.classify_finalization_path(path) == fga.FinalizationPathClass.B

    def test_unknown_path_fails_closed_to_class_a(self):
        assert fga.classify_finalization_path("random/never/seen.txt") == fga.FinalizationPathClass.A

    def test_class_b_directory_with_wrong_extension_is_class_a(self):
        # Content-sensitivity restriction: an executable-shaped file under
        # an otherwise-open directory is still Class A.
        assert fga.classify_finalization_path("tasks/active/hook.py") == fga.FinalizationPathClass.A

    def test_executable_mode_forces_class_a(self):
        assert fga.classify_finalization_path(
            "PROJECT_STATUS.md", mode="100755"
        ) == fga.FinalizationPathClass.A

    def test_symlink_mode_forces_class_a(self):
        assert fga.classify_finalization_path(
            ".pcae/phase-completion-report.md", mode="120000"
        ) == fga.FinalizationPathClass.A

    def test_gitlink_mode_forces_class_a(self):
        assert fga.classify_finalization_path(
            "tasks/active/submod", mode="160000"
        ) == fga.FinalizationPathClass.A


# ---------------------------------------------------------------------
# Diff authority (contract §6/§7)
# ---------------------------------------------------------------------

class TestDiffAuthority:
    def test_empty_delta_when_checkpoint_equals_final_head(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        assert fga.check_finalization_delta(str(repo), checkpoint, checkpoint) == []

    def test_allowed_class_b_finalization_delta_accepted(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "PROJECT_STATUS.md").write_text("# Status\n")
        (repo / ".pcae").mkdir(exist_ok=True)
        (repo / ".pcae" / "phase-completion-metadata.json").write_text("{}\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: finalization metadata"], repo)
        final_head = _head(repo)
        assert fga.check_finalization_delta(str(repo), checkpoint, final_head) == []

    def test_src_change_after_checkpoint_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "src" / "thing.py").write_text("VALUE = 2\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: oops fix"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert issues != []
        assert any("src/thing.py" in i for i in issues)

    def test_tests_change_after_checkpoint_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "tests" / "test_new.py").write_text(_TESTS_SRC)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: add test"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("tests/test_new.py" in i for i in issues)

    def test_docs_contracts_change_after_checkpoint_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "docs").mkdir(exist_ok=True)
        (repo / "docs" / "contracts").mkdir(exist_ok=True)
        (repo / "docs" / "contracts" / "SOME.md").write_text("x\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: contract edit"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("docs/contracts/SOME.md" in i for i in issues)

    def test_unknown_path_after_checkpoint_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "mystery.dat").write_text("x\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: mystery file"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("mystery.dat" in i for i in issues)

    def test_rename_evaluates_both_old_and_new_path(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        (repo / "src" / "thing.py").rename(repo / "src" / "renamed.py")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: rename"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert issues != []  # src/** rename is Class A regardless of direction

    def test_rewritten_or_unrelated_ancestry_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        # An orphan branch shares no ancestry with `checkpoint` at all —
        # the same failure mode a history rewrite (amend/rebase/reset)
        # produces: the checkpoint SHA is no longer a real ancestor.
        _run(["git", "checkout", "-q", "--orphan", "orphan-branch"], repo)
        _run(["git", "rm", "-rq", "--cached", "."], repo)
        (repo / "orphan.txt").write_text("x\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "orphan commit"], repo)
        final_head = _head(repo)
        issues = fga.diff_authority_issues(str(repo), checkpoint, final_head)
        assert any("not an ancestor" in i for i in issues)

    def test_merge_commit_in_range_rejected(self, tmp_path):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        _run(["git", "checkout", "-q", "-b", "side"], repo)
        (repo / "PROJECT_STATUS.md").write_text("side\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: side status"], repo)
        _run(["git", "checkout", "-q", "-"], repo)
        _run(["git", "checkout", "-q", "-b", "main2"], repo)
        (repo / "CHANGELOG.md").write_text("main2\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: main2 changelog"], repo)
        _run(["git", "merge", "-q", "--no-ff", "-m", "merge side into main2", "side"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("merge commit" in i for i in issues)


# ---------------------------------------------------------------------
# End-to-end lifecycle carve-out inside validate_derived_correctness (§14)
# ---------------------------------------------------------------------

class TestLifecycleFreshnessIntegration:
    def test_finalization_delta_after_checkpoint_accepted(self, tmp_path, monkeypatch):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        structured_value = _capture_structured_evidence(repo, checkpoint)

        (repo / "PROJECT_STATUS.md").write_text("# Status\n")
        (repo / ".pcae").mkdir(exist_ok=True)
        (repo / ".pcae" / "phase-completion-metadata.json").write_text("{}\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: finalization metadata"], repo)
        final_head = _head(repo)
        assert final_head != checkpoint

        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "pcae.core.phase_reports.run_stage_b_focused_checks", lambda repo_root: []
        )
        report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": structured_value},
        )
        issues = validate_derived_correctness(report)
        assert issues == []
        assert report.metadata["fgsc_verification_checkpoint_commit"] == checkpoint
        assert report.metadata["fgsc_final_phase_head"] == final_head
        assert report.metadata["fgsc_lifecycle_state"] == "FINALIZATION_VERIFIED"

    def test_forbidden_change_after_checkpoint_still_blocks_completion(self, tmp_path, monkeypatch):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        structured_value = _capture_structured_evidence(repo, checkpoint)

        (repo / "src" / "thing.py").write_text("VALUE = 999\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: forbidden post-checkpoint src change"], repo)

        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "pcae.core.phase_reports.run_stage_b_focused_checks", lambda repo_root: []
        )
        report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": structured_value},
        )
        issues = validate_derived_correctness(report)
        assert issues != []
        assert any("src/thing.py" in i for i in issues)
        assert "fgsc_verification_checkpoint_commit" not in report.metadata

    def test_stage_b_failure_blocks_completion_even_with_clean_delta(self, tmp_path, monkeypatch):
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        structured_value = _capture_structured_evidence(repo, checkpoint)

        (repo / "PROJECT_STATUS.md").write_text("# Status\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: status update"], repo)

        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "pcae.core.phase_reports.run_stage_b_focused_checks",
            lambda repo_root: ["pcae check failed: 1 violation(s)"],
        )
        report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": structured_value},
        )
        issues = validate_derived_correctness(report)
        assert any("Stage B focused check failed" in i for i in issues)
        assert "fgsc_verification_checkpoint_commit" not in report.metadata

    def test_scalar_mode_entirely_unaffected(self):
        # Contract §16 — no structured evidence, no checkpoint concept.
        report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": "0 passed, 0 failed"},
        )
        issues = validate_derived_correctness(report)
        assert not any("FGSC" in i or "checkpoint" in i for i in issues)
        assert report.metadata == {}

    def test_crash_resume_reconstructable_from_git_and_artifact_alone(self, tmp_path):
        """Contract §21 item 12 — the lifecycle-freshness decision must be
        fully reconstructable from Git history + the persisted evidence
        artifact, with no ephemeral in-process state required."""
        repo, checkpoint, _ = _make_repo_with_checkpoint(tmp_path)
        structured_value = _capture_structured_evidence(repo, checkpoint)
        (repo / "CHANGELOG.md").write_text("entry\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", "Phase TESTPH.2: changelog"], repo)
        final_head = _head(repo)

        # Simulate a fresh process: re-read the checkpoint from the
        # persisted artifact on disk (never from memory) and recompute.
        artifact_path = Path(structured_value["provenance"]["artifact_path"])
        import json
        reloaded = json.loads((repo / artifact_path).read_text())
        reconstructed_checkpoint = reloaded["candidate_commit"]
        assert reconstructed_checkpoint == checkpoint

        issues = fga.check_finalization_delta(str(repo), reconstructed_checkpoint, final_head)
        assert issues == []


# ---------------------------------------------------------------------
# Stage B focused-check runner (contract §8)
# ---------------------------------------------------------------------

class TestStageBFocusedChecks:
    def test_runs_against_real_repo_without_raising(self):
        repo_root = str(Path(__file__).resolve().parents[1])
        issues = run_stage_b_focused_checks(repo_root)
        assert isinstance(issues, list)

    def test_flags_pcae_check_failure(self, monkeypatch, tmp_path):
        class _FakeResult:
            passed = False
            violations = ["bad"]

        monkeypatch.setattr("pcae.core.check.run_checks", lambda root: _FakeResult())
        issues = run_stage_b_focused_checks(str(tmp_path))
        assert any("pcae check failed" in i for i in issues)

    def test_flags_task_memory_errors(self, monkeypatch, tmp_path):
        class _FakeDiagnostics:
            has_errors = True

        monkeypatch.setattr(
            "pcae.core.tasks.diagnose_task_memory", lambda root: _FakeDiagnostics()
        )
        issues = run_stage_b_focused_checks(str(tmp_path))
        assert any("task-memory" in i for i in issues)
