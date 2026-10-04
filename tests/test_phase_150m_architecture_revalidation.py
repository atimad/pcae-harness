"""Independent target-contract audit; NOT runtime provenance enforcement."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "944228ac9cdbe91711c5e4c32190640cec467068"
CONTRACT = ROOT / "docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md"
ARCH = ROOT / "docs/PHASE_150L_GENERATION_PROVENANCE_ARCHITECTURE.md"
FIELDS = ("schema root_epoch repository_id phase_instance_id phase_id task_id sequence generation_id role "
          "report_json_sha256 report_markdown_sha256 predecessor_certificate_id input_commit "
          "completion_metadata_sha256 authorization_event_id issuance_event_id certificate_id").split()
# The ELEVEN architectural domains are NOT the THIRTEEN RootEvent wire kinds.
ROOT_KINDS = ("bootstrap open_phase authorize_manifest issue_generation observe_promotion accept_push "
              "complete_task certify_terminal bind_checkpoint bind_receipt record_notification "
              "close_delivery activate_cutover").split()
EVENT_CROSSWALK = {
    1: "issue_generation", 2: "observe_promotion", 3: "issue_generation",
    4: "authorize_manifest", 5: "accept_push", 6: "bind_checkpoint",
    7: "certify_terminal", 8: "bind_receipt", 9: "record_notification",
    10: "issue_generation", 11: None,  # retention/read membership, not a new issuance
}
ATTACK_REQUIREMENTS = {
    1: 9, 2: 10, 3: 3, 4: 6, 5: 13, 6: 4, 7: 14, 8: 14, 9: 14,
    10: 15, 11: 16, 12: 16, 13: 10, 14: 10, 15: 10, 16: 10, 17: 10,
    18: 6, 19: 10, 20: 10, 21: 10, 22: 5, 23: 5, 24: 9, 25: 8,
    26: 11, 27: 12, 28: 16, 29: 16, 30: 22, 31: 20, 32: 17,
}


def section(text, heading, next_heading):
    return text.split(heading, 1)[1].split(next_heading, 1)[0]


def test_exact_gap_free_inventories_and_no_undefined_references():
    contract, arch = CONTRACT.read_text(), ARCH.read_text()
    for prefix, count in (("REQ", 26), ("INV", 12)):
        defined = re.findall(rf"^GCP-{prefix}-(\d{{3}}):", contract, re.M)
        assert defined == [f"{n:03}" for n in range(1, count + 1)]
        refs = set(re.findall(rf"GCP-{prefix}-(\d{{3}})\b", contract + arch))
        assert refs <= set(defined)
    table = section(contract, "### 3.1 GenerationCertificate", "### 3.2 TerminalCertificate")
    assert re.findall(r"^\| ([a-z_][a-z_0-9]*) \|", table, re.M) == FIELDS
    assert re.findall(r"^\| E(\d+) ", arch, re.M) == [str(n) for n in range(1, 12)]
    assert re.findall(r"^\| CR(\d+) ", arch, re.M) == [str(n) for n in range(1, 13)]
    attacks = section(arch, "## 10. Architecture attack matrix", "## 11.")
    assert re.findall(r"^\| (\d+) \|", attacks, re.M) == [str(n) for n in range(1, 33)]


def test_architecture_domains_do_not_silently_contract_root_event_schema():
    text = CONTRACT.read_text()
    kinds = section(text, "event_kind is one of ", ".\nBootstrap").replace("\n", "")
    assert [x.strip() for x in kinds.split(",")] == ROOT_KINDS
    assert set(EVENT_CROSSWALK) == set(range(1, 12))
    assert set(EVENT_CROSSWALK.values()) - {None} <= set(ROOT_KINDS)
    # Independent control/completion events accompany domains; not missing domains.
    extra = set(ROOT_KINDS) - (set(EVENT_CROSSWALK.values()) - {None})
    assert extra == {"bootstrap", "open_phase", "complete_task", "close_delivery", "activate_cutover"}


@pytest.mark.parametrize("row", range(1, 33))
def test_each_attack_has_defined_requirement_invariant_and_target_defense(row):
    contract, arch = CONTRACT.read_text(), ARCH.read_text()
    table = section(arch, "## 10. Architecture attack matrix", "## 11.")
    cells = re.search(rf"^\| {row} \| (.+)$", table, re.M).group(1).split("|")
    action, invariant, result, defense = [x.strip() for x in cells if x.strip()]
    assert re.search(rf"^{invariant}: ", contract, re.M)
    req = f"GCP-REQ-{ATTACK_REQUIREMENTS[row]:03}"
    assert re.search(rf"^{req}: ", contract, re.M)
    assert action and result and defense
    assert "NOT implemented test success" in arch


@pytest.mark.parametrize("number,clause", [
    (2, "Ordinary agent credentials SHALL NOT append"),
    (3, "Reviewer/publisher credentials and authorization-channel state SHALL be outside"),
    (4, "both protected-reference ancestry"),
    (5, "excluding their own\nID and detached anchor proof"),
    (8, "accepts a root event/certificate before canonical promotion"),
    (9, "pre-canonical-code-push, NOT pre-any-commit"),
    (10, "one certified linear generation\nchain"),
    (11, "after independently accepted push and completed task events"),
    (12, "forbids new generations after terminal certification"),
    (13, "cannot select it"), (14, "certifies NONE of issuance/terminal/chain directly"),
    (15, "absence/unknown outcome never becomes a sent claim"),
    (16, "never a selector/root"), (17, "never generation provenance"),
    (18, "Artifact\ntimestamps, missing certificates, user metadata or feature flags cannot choose"),
    (19, "Do not rewrite old report/cp/receipt/marker bytes"),
    (20, "Terminal provenance and delivery completeness are separate axes"),
    (21, "Old status='reconciled'/exit 0 is NOT strong certification"),
    (22, "no 'pick the candidate that passes'"),
    (24, "No delivery success may be inferred from"),
    (25, "no lifecycle writes or authority\nresolution"),
])
def test_normative_non_circular_boundaries_are_preserved(number, clause):
    text = CONTRACT.read_text()
    requirement = text.split(f"GCP-REQ-{number:03}: ", 1)[1]
    requirement = re.split(r"GCP-REQ-\d{3}: ", requirement, maxsplit=1)[0]
    assert " ".join(clause.split()) in " ".join(requirement.split())


@pytest.mark.parametrize("relative,digest", [
    ("docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md", "d72d93451a28befd39febd51473e05f020649afe26886742838a1adae119c51f"),
    (".pcae/phase-reports/20261004-202343-150L.json", "8070a4016915dad3f7d45f5ea88b8c9df2cb078fd8d9e253d7d897cbe4d4874a"),
    (".pcae/phase-reports/20261004-202343-150L.md", "18d66beecdb1d219495d13a8be322436c90c4ca8fdde6117d61050634a211c3e"),
    (".pcae/finalization-transactions/150L.json", "26a33dbfa1ead42b8b3d5985a50b4f5207583c92b56b0cbcff211d1a44f90e02"),
    (".pcae/delivery-receipts/receipts/dfad1a7ceb5b29384d435bedcedb364057d1db8d99369822b90722ba4a74bff0/receipt.json", "38679c3e4d70d3ef2dc12e9698c609579be0c6d28f0d20f8096daffabbf691f4"),
])
def test_original_target_and_150l_artifacts_are_byte_preserved(relative, digest):
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_blocked_150l_truth_is_permanently_retained_in_repository_history():
    text = subprocess.check_output(["git", "show", ENTRY + ":.pcae/phase-completion-report.md"], cwd=ROOT, text=True)
    assert "COMPLETE — ARCHITECTURE NOT ADJUDICATED / BLOCKED" in text
    assert "payload_conflict" in text and "985 passed / 7 failed" in text


def test_no_production_contract_or_lifecycle_consumer_delta():
    delta = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", ENTRY,
                                     "--", "src/pcae", "docs/contracts"], cwd=ROOT, text=True)
    assert delta == ""
    for path in (ROOT / "src/pcae").rglob("*.py"):
        text = path.read_text()
        assert "gcp-generation/1.0" not in text and "gcp-terminal/1.0" not in text


def test_legacy_inventory_remains_explicitly_non_certifying():
    text = ARCH.read_text()
    table = section(text, "## 7. Legacy inventory", "## 8.")
    for identity in ("150G", "150H", "150I", "150J", "150K", "133B", "113B"):
        row = re.search(rf"^\| {identity}[^\n]*", table, re.M).group()
        assert "NO" in row
    assert "LEGACY-D for current selection" in table
    assert "not production reclassification" in table
    assert "legacy compatibility != retroactive provenance certification" in CONTRACT.read_text()
