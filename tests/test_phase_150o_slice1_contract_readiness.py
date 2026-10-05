"""Phase 150O diagnostic evidence only; no generation/certificate issuance.

The digest probes are incomplete illustrative data, NOT issuance certificates.
Neither candidate encoding is adopted. The frozen contract remains unchanged.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "d5a717fd9afa936f4643a06649984a9631f23a1b"
CONTRACT = ROOT / "docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md"
ARCH = ROOT / "docs/PHASE_150L_GENERATION_PROVENANCE_ARCHITECTURE.md"
EVIDENCE = ROOT / "docs/PHASE_150O_SLICE1_CONTRACT_READINESS.md"
SHA = "d72d93451a28befd39febd51473e05f020649afe26886742838a1adae119c51f"
FIELDS = ("schema root_epoch repository_id phase_instance_id phase_id task_id sequence "
          "generation_id role report_json_sha256 report_markdown_sha256 "
          "predecessor_certificate_id input_commit completion_metadata_sha256 "
          "authorization_event_id issuance_event_id certificate_id").split()
EVENTS = ("bootstrap open_phase authorize_manifest issue_generation observe_promotion "
          "accept_push complete_task certify_terminal bind_checkpoint bind_receipt "
          "record_notification close_delivery activate_cutover").split()


def section(text, first, last):
    return text.split(first, 1)[1].split(last, 1)[0]


def test_contract_identity_is_unchanged():
    assert hashlib.sha256(CONTRACT.read_bytes()).hexdigest() == SHA
    assert "Contract ID: GCP-001" in CONTRACT.read_text()
    assert "Version: 1.0" in CONTRACT.read_text()


@pytest.mark.parametrize("prefix,count", [("REQ", 26), ("INV", 12)])
def test_exact_requirement_invariant_inventory(prefix, count):
    actual = re.findall(rf"^GCP-{prefix}-(\d{{3}}):", CONTRACT.read_text(), re.M)
    assert actual == [f"{i:03}" for i in range(1, count + 1)]


@pytest.mark.parametrize("index,name", list(enumerate(FIELDS, 1)))
def test_exact_field_inventory_and_no_implementation_claim(index, name):
    table = section(CONTRACT.read_text(), "### 3.1 GenerationCertificate", "### 3.2")
    actual = re.findall(r"^\| ([a-z_][a-z_0-9]*) \|", table, re.M)
    assert actual == FIELDS
    assert actual[index - 1] == name
    assert f"| {index} | {name} |" in EVIDENCE.read_text()


def test_eleven_architecture_domains_are_not_thirteen_wire_kinds():
    actual = section(CONTRACT.read_text(), "event_kind is one of ", ".\nBootstrap")
    assert [v.strip() for v in actual.replace("\n", "").split(",")] == EVENTS
    assert len(EVENTS) == 13
    assert re.findall(r"^\| E(\d+) ", ARCH.read_text(), re.M) == [str(i) for i in range(1, 12)]
    assert re.findall(r"^\| CR(\d+) ", ARCH.read_text(), re.M) == [str(i) for i in range(1, 13)]


@pytest.mark.parametrize("schema", ["gcp-generation/1.0", "gcp-terminal/1.0"])
def test_domain_separation_without_frozen_framing_is_not_unique(schema):
    # ASCII + integer-free body is a JCS-compatible subset. It is intentionally
    # NOT a closed certificate. This isolates framing, not issuance or trust.
    body = {"schema": schema, "probe": "non-certificate diagnostic data"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    domain = schema.encode("ascii")
    nul_framed = domain + b"\0" + canonical
    length_framed = len(domain).to_bytes(4, "big") + domain + canonical
    assert nul_framed.endswith(canonical) and length_framed.endswith(canonical)
    assert hashlib.sha256(nul_framed).digest() != hashlib.sha256(length_framed).digest()
    # Reordering input does not explain the divergence: same canonical body.
    reordered = dict(reversed(list(body.items())))
    assert canonical == json.dumps(reordered, sort_keys=True, separators=(",", ":")).encode()


def test_contract_requires_domain_separation_but_does_not_supply_test_vector():
    text = CONTRACT.read_text()
    assert "Certificate IDs hash the domain-separated canonical body" in text
    assert "excluding their own\nID and detached anchor proof" in text
    # Evidence explicitly records the bounded search and does not pretend that
    # this textual inventory alone is executable certificate validation.
    assert "No candidate framing is selected" in EVIDENCE.read_text()
    assert "GCP-REQ-005" in EVIDENCE.read_text()


@pytest.mark.parametrize("n", range(1, 27))
def test_all_requirements_have_honest_blocked_traceability(n):
    assert f"| GCP-REQ-{n:03} |" in EVIDENCE.read_text()


@pytest.mark.parametrize("n", range(1, 13))
def test_invariants_are_not_claimed_implemented(n):
    text = EVIDENCE.read_text()
    assert f"GCP-INV-{n:03}" in text
    assert "Production symbol: NONE" in text


@pytest.mark.parametrize("n", range(1, 33))
def test_each_attack_row_is_explicitly_deferred(n):
    text = EVIDENCE.read_text()
    assert f"| {n} |" in section(text, "## Attack applicability", "## Disposition")
    assert "No attack closure is claimed" in text


def test_this_diagnostic_phase_preserves_source_and_contracts_at_its_boundary():
    lines = subprocess.check_output(["git", "log", "--format=%H %s"], cwd=ROOT, text=True).splitlines()
    own = [line.split(" ", 1)[0] for line in lines if " Phase 150O:" in line]
    revisions = [ENTRY, own[0]] if own else [ENTRY]
    diff = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", *revisions,
                                    "--", "src/pcae", "docs/contracts"], cwd=ROOT, text=True)
    assert diff == ""
    # Pin this phase too: future implementation must not retroactively fail it.
    tree = own[0] if own else ENTRY
    result = subprocess.run(["git", "grep", "-n", "-e", "gcp-generation/1.0", "-e",
                             "gcp-terminal/1.0", tree, "--", "src/pcae"], cwd=ROOT, capture_output=True)
    assert result.returncode == 1 and not result.stdout
