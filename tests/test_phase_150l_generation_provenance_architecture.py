"""Architecture freeze coverage, NOT enforcement of an implemented trust root.

These tests lint normative decisions and independently preserve historical bytes.
Phase 150J/K executable defect witnesses remain the current production reality.
No moving-HEAD/latest-notification assumptions or synthetic certificates are used.
"""
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md"
ARCH = ROOT / "docs/PHASE_150L_GENERATION_PROVENANCE_ARCHITECTURE.md"
ENTRY = "8c998d2b2654e45e189bc3bfda57c7b6ecd71d7f"
# Includes architecture, closure, and the truthful blocked-disposition correction.
PHASE_END = "944228ac9cdbe91711c5e4c32190640cec467068"


@pytest.mark.parametrize("number", range(1, 27))
def test_each_requirement_defined_once(number):
    assert len(re.findall(rf"^GCP-REQ-{number:03}: ", CONTRACT.read_text(), re.M)) == 1


@pytest.mark.parametrize("number", range(1, 13))
def test_invariant_defined_and_attack_traced(number):
    ident = f"GCP-INV-{number:03}"
    assert len(re.findall(rf"^{ident}: ", CONTRACT.read_text(), re.M)) == 1
    assert ident in ARCH.read_text().split("## 10. Architecture attack matrix")[1].split("## 11.")[0]


@pytest.mark.parametrize("number", range(1, 33))
def test_attack_has_invariant_result_and_defense(number):
    attack_matrix = ARCH.read_text().split("## 10. Architecture attack matrix")[1].split("## 11.")[0]
    rows = re.findall(rf"^\| {number} \| (.+)$", attack_matrix, re.M)
    assert len(rows) == 1
    cells = [x.strip() for x in rows[0].split("|") if x.strip()]
    assert len(cells) == 4 and re.fullmatch(r"GCP-INV-\d{3}", cells[1])
    assert len(cells[2]) >= 5 and len(cells[3]) >= 20


@pytest.mark.parametrize("number", range(1, 13))
def test_crash_state_has_explicit_recovery(number):
    rows = re.findall(rf"^\| CR{number} (.+)$", ARCH.read_text(), re.M)
    assert len(rows) == 1 and len(rows[0].split("|")) >= 4


@pytest.mark.parametrize("number", range(1, 12))
def test_required_lifecycle_event_modeled(number):
    assert len(re.findall(rf"^\| E{number} ", ARCH.read_text(), re.M)) == 1


@pytest.mark.parametrize("field", ["schema", "root_epoch", "repository_id", "phase_instance_id",
    "phase_id", "task_id", "sequence", "generation_id", "role", "report_json_sha256",
    "report_markdown_sha256", "predecessor_certificate_id", "input_commit",
    "completion_metadata_sha256", "authorization_event_id", "issuance_event_id", "certificate_id"])
def test_generation_field_has_type_class_and_proof_purpose(field):
    rows = re.findall(rf"^\| {field} \| (.+)$", CONTRACT.read_text(), re.M)
    assert len(rows) == 1
    cells = [x.strip() for x in rows[0].split("|") if x.strip()]
    assert len(cells) == 3 and cells[1] in {"identity", "provenance", "ordering"}
    assert len(cells[2]) > 10


@pytest.mark.parametrize("model", ["R1", "R2", "R3", "R4", "R5", "R6"])
def test_root_candidates_compared(model):
    assert re.search(rf"^\| {model}\b", ARCH.read_text(), re.M)


@pytest.mark.parametrize("path,digest", [
    (".pcae/phase-reports/20260922-203915-150G.json", "5509cb71fab2ad6bc0f6474fda3bb08bea2ead17a8c2ddd2d8c96ff25a5a3c12"),
    (".pcae/phase-reports/20260922-203915-150G.md", "da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551"),
    (".pcae/phase-reports/20260922-210046-150G.json", "deafa34cd8d4c7802def8445308b502c9c93603fdc622e1b28bae79a5ed5651d"),
    (".pcae/phase-reports/20260922-210046-150G.md", "5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1"),
    (".pcae/finalization-transactions/150G.json", "d0bbbb3e2719352ce2f54e3b63f10d16bf739671b00ceb441dd82d06d8e327da"),
    (".pcae/delivery-receipts/receipts/ed1ac26782164d4f443356bdf99a7aa57e96a45b56e139745bd82c202b18d23e/receipt.json", "057a4539d89d0c4aceb55dde87857f508b36ff87cb7b47a424088304a51e4881"),
])
def test_150g_historical_bytes_preserved(path, digest):
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_target_not_deployed_and_legacy_not_certified():
    text = CONTRACT.read_text()
    assert "NOT IMPLEMENTED; CUTOVER INACTIVE" in text
    for item in ("LEGACY-A", "LEGACY-B", "LEGACY-C", "LEGACY-D", "NO MIGRATION",
                 "certified/current", "certified/historical", "legacy-provenance-incomplete"):
        assert item in text
    assert "including 150L, remain legacy" in text
    assert "legacy compatibility != retroactive provenance certification" in text


def test_independent_root_not_same_process_pseudo_authority():
    text = CONTRACT.read_text()
    for clause in ("outside", "independently authenticated reviewer", "ordinary origin/main",
        "provider-authenticated", "approved policy, NOT proposed repository code",
        "exact event manifest", "fresh authenticated root", "No self-hashed authorization",
        "input commit exists", "forbids new generations after terminal certification",
        "latest/current is a derived cache/index", "HASH CONSISTENCY != PROVENANCE"):
        assert clause in text


def test_slice_one_is_not_lifecycle_implementation():
    assert "no root lookup/write, no lifecycle integration, no trusted result" in ARCH.read_text()
    assert "recognition-core IV remains on hold" in ARCH.read_text()


def test_zero_production_delta_from_fixed_entry():
    changes = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", ENTRY, PHASE_END, "--", "src/pcae"], cwd=ROOT, text=True)
    assert not changes.strip()


def test_existing_contracts_unchanged():
    changes = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", ENTRY, PHASE_END, "--", "docs/contracts"], cwd=ROOT, text=True)
    assert set(changes.splitlines()) <= {"docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md"}
