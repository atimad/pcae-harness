"""Phase 149O.20L.7O.2S.3 — FGSC-001 Structured Fast Green Self-
Certification Lifecycle Implementation Independent Verification.

Adversarial, independent tests against the 149O.20L.7O.2S.2 implementation
(``src/pcae/core/fast_green_attribution.py`` FGSC-001 section,
``src/pcae/core/phase_reports.py`` carve-out wiring). Deliberately does not
reuse or import fixtures from
``tests/test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py`` —
each scenario here builds its own disposable synthetic git repository.

This suite additionally covers attacks not exercised by the 2S.2 suite:
real (not synthetic-mode-string) symlink/gitlink/mode-only diffs, rename in
both directions end-to-end through ``check_finalization_delta``, and —
the headline finding of this phase — the interaction between
``validate_structured_fast_green()``'s internal early-return control flow
and the 2S.2 carve-out's "only staleness" precondition.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.core import fast_green_attribution as fga
from pcae.core.phase_reports import PhaseReport, validate_derived_correctness

PHASE_ID = "IV2S3"


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
    return repo


def _checkpoint_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = _init_repo(tmp_path)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", "chore: pre-phase state"], repo)
    (repo / "src" / "thing.py").write_text("VALUE = 1\n")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: implement change"], repo)
    return repo, _head(repo)


# ---------------------------------------------------------------------
# Real (non-synthetic-mode-string) path-classification attacks
# ---------------------------------------------------------------------

class TestRealDiffAttacks:
    def test_mode_only_chmod_on_class_b_file_rejected(self, tmp_path):
        repo, checkpoint = _checkpoint_repo(tmp_path)
        (repo / "PROJECT_STATUS.md").write_text("status\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)
        (repo / "PROJECT_STATUS.md").chmod(0o755)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: chmod status executable"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("PROJECT_STATUS.md" in i for i in issues)

    def test_real_symlink_at_class_b_name_rejected(self, tmp_path):
        repo, checkpoint = _checkpoint_repo(tmp_path)
        (repo / "PROJECT_STATUS.md").write_text("status\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)
        (repo / "CHANGELOG.md").symlink_to("PROJECT_STATUS.md")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: symlink changelog"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("CHANGELOG.md" in i for i in issues)

    def test_real_gitlink_under_open_directory_rejected(self, tmp_path):
        repo, checkpoint = _checkpoint_repo(tmp_path)
        sub = tmp_path / "sub"
        sub.mkdir()
        _run(["git", "init", "-q"], sub)
        _run(["git", "config", "user.email", "iv@iv.example"], sub)
        _run(["git", "config", "user.name", "IndependentVerifier"], sub)
        (sub / "f.txt").write_text("z\n")
        _run(["git", "add", "-A"], sub)
        _run(["git", "commit", "-q", "-m", "sub init"], sub)
        sub_sha = _head(sub)
        _run(["git", "update-index", "--add", "--cacheinfo",
              f"160000,{sub_sha},tasks/active/embedded"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: gitlink under tasks/active"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("tasks/active/embedded" in i for i in issues)

    def test_unsafe_to_safe_rename_rejected_via_old_path(self, tmp_path):
        repo, checkpoint = _checkpoint_repo(tmp_path)
        _run(["git", "mv", "src/thing.py", "CHANGELOG.md"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: rename src file to changelog path"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("src/thing.py" in i for i in issues)

    def test_safe_to_unsafe_rename_rejected_via_new_path(self, tmp_path):
        repo, checkpoint = _checkpoint_repo(tmp_path)
        # Content long enough to survive Git's rename-similarity threshold.
        (repo / "PROJECT_STATUS.md").write_text("status line " * 40 + "\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)
        (repo / "src" / "pcae").mkdir(parents=True)
        _run(["git", "mv", "PROJECT_STATUS.md", "src/pcae/evil.py"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: rename status into src tree"], repo)
        final_head = _head(repo)
        issues = fga.check_finalization_delta(str(repo), checkpoint, final_head)
        assert any("src/pcae/evil.py" in i for i in issues)


# ---------------------------------------------------------------------
# 2S.3 BLOCKING FINDING (repaired in 149O.20L.7O.2S.4): staleness
# carve-out precondition was unsound.
#
# ``phase_reports.py``'s carve-out treats "structured_issues == [staleness
# only]" as proof that nothing else is wrong with the evidence. Before the
# 2S.4 repair, ``validate_structured_fast_green()`` computed the freshness
# (staleness) issue *before* independently recomputing
# ``attributable_failures`` and the conservation/bucket checks, and
# contained an internal ``if issues: return issues`` guard between the
# expected_phase_artifacts loop and the "Conservation" section that fired
# as soon as *any* issue had accumulated -- including the harmless,
# expected staleness issue itself. This meant the independent
# recomputation of ``attributable_failures`` (2Q.1's core anti-forgery
# property: "recomputes independently... rather than trusting the
# artifact's own bucket labels") was *never reached* whenever staleness was
# already present. Since routine post-checkpoint finalization commits
# *always* produce staleness (that is the entire premise FGSC-001 exists
# to forgive), this meant: a persisted evidence artifact carrying an
# unclassified, unattributed real test regression -- one that a
# non-FGSC-mode phase's ``validate_structured_fast_green()`` call would
# have rejected outright ("has nonzero attributable_failures") -- could be
# silently certified FINALIZATION_VERIFIED by the FGSC-001 carve-out, with
# no trace of the suppressed defect in the returned issue list.
#
# This was exactly the "broad issue filtering" failure mode Phase 149O.
# 20L.7O.2S.3's verification brief names as Blocking (its §9: "prove the
# caller cannot suppress ... attributable failures ... merely because FGSC
# mode is active").
#
# 149O.20L.7O.2S.4 repair: the freshness check in
# ``validate_structured_fast_green()`` now runs *last*, after every other
# non-freshness structured-evidence validity check (including independent
# attribution/conservation recomputation) has already had the chance to
# append its own issue. A "staleness only" result is therefore now sound
# proof that nothing else is wrong. The tests below assert the corrected
# (rejecting) behavior.
# ---------------------------------------------------------------------

class TestStalenessCarveOutSoundness:
    def _capture(self, repo: Path, checkpoint: str) -> dict:
        evidence = fga.build_attribution_evidence(
            repo_root=str(repo), phase_id=PHASE_ID, pushed_status="local_only",
            candidate_commit=checkpoint, timeout=120,
        )
        return fga.persist_evidence(str(repo), evidence)

    def test_validate_structured_fast_green_skips_attribution_recompute_once_stale(
        self, tmp_path
    ):
        """Isolates the root cause at the fast_green_attribution layer,
        independent of the phase_reports.py carve-out wiring."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = self._capture(repo, checkpoint)

        # Inject a genuine, unclassified failing node directly into the
        # persisted artifact (simulating either a build_attribution_evidence
        # defect or filesystem tampering -- the exact residual-risk actor
        # the module's own docstring already names) and re-sign the digest
        # so the artifact is internally self-consistent.
        artifact_path = repo / structured["provenance"]["artifact_path"]
        persisted = json.loads(artifact_path.read_text())
        persisted["raw_failed"] = sorted(
            persisted["raw_failed"] + ["tests/test_sample.py::test_evil_new_failure"]
        )
        new_digest = fga._canonical_digest(persisted)
        new_artifact_path = artifact_path.parent / f"{new_digest}.json"
        new_artifact_path.write_text(json.dumps(persisted, sort_keys=True, indent=2))
        tampered = dict(persisted)
        tampered["provenance"] = {
            "generated_by_command": structured["provenance"]["generated_by_command"],
            "artifact_path": str(new_artifact_path.relative_to(repo)),
            "artifact_digest": new_digest,
        }

        # Sanity: with the checkpoint == current HEAD (no staleness), the
        # independent recomputation *does* catch the injected regression.
        issues_fresh = fga.validate_structured_fast_green(
            tampered, str(repo), PHASE_ID, "local_only"
        )
        assert any("attributable_failures" in i for i in issues_fresh), (
            "sanity check failed: recomputation should catch the injected "
            f"regression when not stale; got {issues_fresh!r}"
        )

        # Now advance HEAD with an ordinary Class-B finalization commit
        # (routine, contract-permitted) so the evidence becomes stale.
        (repo / "PROJECT_STATUS.md").write_text("status\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)

        issues_stale = fga.validate_structured_fast_green(
            tampered, str(repo), PHASE_ID, "local_only"
        )
        stale_only = [
            i for i in issues_stale
            if i.startswith("structured fast_green evidence is stale")
        ]
        non_stale = [i for i in issues_stale if i not in stale_only]

        # 149O.20L.7O.2S.4 repair: the freshness check now runs last, after
        # independent attribution/conservation recomputation, so the
        # injected regression remains visible even once staleness is also
        # present.
        assert any("attributable_failures" in i for i in non_stale), (
            f"expected the attribution defect to remain visible once stale; "
            f"got non_stale={non_stale!r}"
        )

    def test_carve_out_certifies_finalization_verified_despite_hidden_regression(
        self, tmp_path, monkeypatch
    ):
        """End-to-end through validate_derived_correctness (the actual
        pre-promotion gate) -- confirms the defect is exploitable at the
        real call site used by ``pcae phase complete``, not just at the
        lower-level validator."""
        repo, checkpoint = _checkpoint_repo(tmp_path)
        structured = self._capture(repo, checkpoint)

        artifact_path = repo / structured["provenance"]["artifact_path"]
        persisted = json.loads(artifact_path.read_text())
        persisted["raw_failed"] = sorted(
            persisted["raw_failed"] + ["tests/test_sample.py::test_evil_new_failure"]
        )
        new_digest = fga._canonical_digest(persisted)
        new_artifact_path = artifact_path.parent / f"{new_digest}.json"
        new_artifact_path.write_text(json.dumps(persisted, sort_keys=True, indent=2))
        tampered = dict(persisted)
        tampered["provenance"] = {
            "generated_by_command": structured["provenance"]["generated_by_command"],
            "artifact_path": str(new_artifact_path.relative_to(repo)),
            "artifact_digest": new_digest,
        }

        (repo / "PROJECT_STATUS.md").write_text("status\n")
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-q", "-m", f"Phase {PHASE_ID}: status"], repo)

        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "pcae.core.phase_reports.run_stage_b_focused_checks", lambda repo_root: []
        )
        report = PhaseReport(
            phase_id=PHASE_ID, phase_name="x", status="completed", summary="x",
            pushed_status="local_only",
            test_results={"fast_green": tampered},
        )
        issues = validate_derived_correctness(report)

        # 149O.20L.7O.2S.4 repair: the real pre-promotion gate now rejects
        # this artifact — `raw_failed` contains a node no bucket accounts
        # for, and that is caught before the staleness-only carve-out can
        # be considered.
        assert any("attributable_failures" in i for i in issues), (
            f"expected the carve-out to reject the hidden regression; got {issues!r}"
        )
        assert report.metadata.get("fgsc_lifecycle_state") != "FINALIZATION_VERIFIED"


# ---------------------------------------------------------------------
# Push trust boundary (contract §17) and recursion safety (contract §8/§30)
# ---------------------------------------------------------------------

class TestPushTrustBoundaryAndRecursionSafety:
    def test_push_module_has_no_fgsc_or_attribution_awareness(self):
        import pcae.commands.push as push_mod

        src = Path(push_mod.__file__).read_text()
        assert "fast_green_attribution" not in src
        assert "fgsc" not in src.lower()

    def test_stage_b_focused_check_functions_do_not_import_finalization_path(self):
        from pcae.core import check as check_mod
        from pcae.core import status as status_mod
        from pcae.core import tasks as tasks_mod

        for mod in (check_mod, status_mod, tasks_mod):
            src = Path(mod.__file__).read_text()
            assert "validate_derived_correctness" not in src
            assert "finalization_transaction" not in src
