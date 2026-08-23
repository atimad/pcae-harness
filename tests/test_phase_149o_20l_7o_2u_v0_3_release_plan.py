"""Phase 149O.20L.7O.2U -- mechanical verification of the v0.3 release plan's grounding facts."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_DOC = REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md"
STRATEGY_DOC = REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2P_V0_3_RELEASE_STRATEGY_AND_CAPABILITY_PRIORITIZATION_REASSESSMENT.md"


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_plan_doc_exists_and_is_substantive():
    assert PLAN_DOC.exists()
    text = PLAN_DOC.read_text()
    assert len(text.splitlines()) > 200


def test_strategy_doc_unmodified_since_authoring():
    log = _git("log", "--follow", "--format=%H", "--", str(STRATEGY_DOC.relative_to(REPO_ROOT)))
    commits = [c for c in log.splitlines() if c]
    assert len(commits) == 1


def test_only_two_release_tags_exist():
    tags = set(_git("tag", "-l").splitlines())
    assert tags == {"v0.1.0-rc1", "v0.2.0"}


def test_plan_names_both_release_tags():
    text = PLAN_DOC.read_text()
    assert "v0.1.0-rc1" in text
    assert "v0.2.0" in text


def test_plan_freezes_next_phase_and_decision_points():
    text = PLAN_DOC.read_text()
    assert "149O.20L.7O.2U.1" in text
    assert "MAJOR HUMAN DECISIONS REQUIRED BEFORE IMPLEMENTATION" in text


def test_plan_does_not_claim_execution_enabled():
    text = PLAN_DOC.read_text()
    assert "No execution capability is enabled in this phase" in text


def test_no_production_source_changed_this_phase():
    diff = _git("diff", "--stat", "HEAD", "--", "src/pcae", "scripts")
    assert diff == ""


def test_no_hatp_webauthn_file_touched_this_phase():
    diff = _git("diff", "--name-only", "HEAD")
    staged = _git("diff", "--name-only", "--cached")
    touched = set(diff.splitlines()) | set(staged.splitlines())
    for path in touched:
        lowered = path.lower()
        assert "hatp" not in lowered
        assert "webauthn" not in lowered
        assert "fido2" not in lowered
