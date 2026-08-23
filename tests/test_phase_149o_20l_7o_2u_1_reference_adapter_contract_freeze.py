"""Phase 149O.20L.7O.2U.1 -- mechanical verification of the reference adapter contract freeze."""
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2U_1_REFERENCE_ADAPTER_CONTRACT_FREEZE.md"


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def test_contract_doc_exists_and_is_substantive():
    assert CONTRACT_DOC.exists()
    text = CONTRACT_DOC.read_text()
    assert len(text.splitlines()) > 100


def test_contract_doc_defines_frozen_schema_fields():
    text = CONTRACT_DOC.read_text()
    for field in [
        "intake_contract_version",
        "proposed_changes",
        "content_hash_after",
        "producer_claims",
        "promotion_eligible",
    ]:
        assert field in text


def _schema_block(text):
    start = text.index('"intake_contract_version"')
    end = text.index("```", start)
    return text[max(0, start - 20):end]


def test_schema_block_contains_no_claude_code_identifier():
    text = CONTRACT_DOC.read_text()
    block = _schema_block(text)
    assert "claude" not in block.lower() or "e.g." in block.lower()


def test_contract_names_existing_unmodified_commands():
    text = CONTRACT_DOC.read_text()
    for cmd in ["execution-activation", "promotion-review", "pcae promote"]:
        assert cmd in text


def test_no_production_code_modified_this_phase():
    diff = _git("diff", "--stat", "HEAD", "--", "src/pcae", "scripts")
    assert diff.strip() == ""


def test_no_hatp_webauthn_file_touched_this_phase():
    diff = _git("diff", "--name-only", "HEAD")
    staged = _git("diff", "--name-only", "--cached")
    touched = set(diff.splitlines()) | set(staged.splitlines())
    for path in touched:
        lowered = path.lower()
        assert "hatp" not in lowered
        assert "webauthn" not in lowered
        assert "fido2" not in lowered


def test_no_intake_cli_command_implemented_yet():
    result = subprocess.run(
        ["grep", "-rn", '"intake"', str(REPO_ROOT / "src" / "pcae" / "cli.py")],
        capture_output=True, text=True,
    )
    assert result.stdout.strip() == ""
