"""Static verification for Phase 149O.20L.7O.3W.1R.2B.1R.1.

Contract-only: no production imports, authenticators, runtime, or network.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/contracts"
RIHAC = CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
HPAC = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
PBRD = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RPAC = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
PRIMARY = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1_INDEPENDENT_VERIFICATION_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE.md"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_CROSS_CONTRACT_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_FREEZE_REPAIR.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(path: Path) -> str:
    return " ".join(text(path).split())


def test_primary_inventory_is_exactly_seven_plus_two() -> None:
    source = text(PRIMARY)
    section = source.split("## Findings", 1)[1].split("### NON-BLOCKING", 1)[0]
    assert len(re.findall(r"^\d+\. \*\*B-[1-7] —", section, re.M)) == 7
    assert len(re.findall(r"^\d+\. \*\*M-[1-2] —", section, re.M)) == 2


def test_active_versions_and_supersession() -> None:
    expected = {
        RIHAC: ("# RIHAC-001 v2.0", "**Version:** 2.0"),
        RIASC: ("# RIASC-001 v3.0", "**Version:** 3.0"),
        HPAC: ("# HPAC-001 v2.0", "**Version:** 2.0"),
        PBRD: ("# PBRD-001 v2.0", "**Version:** 2.0"),
        RDGO: ("# RDGO-001 v3.0", "**Version:** 3.0"),
    }
    for path, markers in expected.items():
        body = text(path)
        assert all(marker in body for marker in markers)
        assert "**Supersedes:**" in body
        assert "no migration" in body.lower() or "no authority migration" in body.lower()


def test_rpac_is_byte_unchanged() -> None:
    assert hashlib.sha256(RPAC.read_bytes()).hexdigest() == "395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89"


def test_hpac_protected_root_and_repository_independence() -> None:
    body = flat(HPAC)
    for marker in (
        "protected administration principal unavailable to ordinary same-user agent execution",
        "reject symlinks, traversal, owner/ACL mismatch",
        "Repository/task/agent-controlled state SHALL NOT",
        "ordinary same-UID process state",
    ):
        assert marker in body


def test_bootstrap_and_enrollment_are_non_circular_and_presence_gated() -> None:
    body = flat(HPAC)
    assert "externally established deployment-owner administration principal" in body
    assert "require authenticator UP and UV" in body
    assert "same-UID agent invocation SHALL be denied" in body
    assert "cryptographically verify the ceremony evidence" in body


def test_up_uv_and_intent_are_distinct_and_uv_is_mandatory() -> None:
    body = flat(HPAC)
    assert "user presence != user verification" in body
    assert "user verification != informed approval intent" in body
    assert "both UP and UV are mandatory" in body
    assert "UP-only proofs" in body and "SHALL NOT authorize real runtime" in body


def test_trusted_presentation_and_blind_touch_defense() -> None:
    hpac, rihac = flat(HPAC), flat(RIHAC)
    assert "TrustedApprovalPresentation" in hpac
    assert "ordinary agent-controlled stdout/stdin" in hpac
    assert "blind touch" in rihac.lower()
    assert "trusted_subject_bound_confirmation" in rihac


def test_challenge_domain_and_exact_binding() -> None:
    body = flat(HPAC)
    assert "pcae.hpac.runtime-invocation-approval.v2" in body
    for field in (
        "approval_subject_digest",
        "trusted_presentation_digest",
        "nonce",
        "principal_id",
        "credential_id",
        "proof_schema_version",
    ):
        assert field in body


def test_proof_schema_store_and_reference_are_exact() -> None:
    hpac, riasc = text(HPAC), text(RIASC)
    assert "HPAC-PROOF/2.0" in hpac
    assert "<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/proof.json" in hpac
    assert "(proof_id, proof_digest)" in hpac
    schema = json.loads(re.search(r"```json\n(.*?)\n```", riasc, re.S).group(1))
    proof_ref = schema["$defs"]["authentication_proof_ref"]
    assert proof_ref["required"] == ["proof_id", "proof_digest"]
    assert schema["properties"]["provenance"]["properties"]["authentication_proof_ref"] == {
        "$ref": "#/$defs/authentication_proof_ref"
    }


def test_riasc_v3_constants_and_required_shape() -> None:
    body = text(RIASC)
    schema = json.loads(re.search(r"```json\n(.*?)\n```", body, re.S).group(1))
    assert schema["properties"]["schema_version"] == {"const": "3.0"}
    assert schema["properties"]["contract_version"] == {"const": "RIHAC-001/2.0"}
    assert schema["properties"]["provenance"]["properties"]["approval_mechanism"] == {
        "const": "trusted_subject_bound_confirmation"
    }
    assert len(schema["required"]) == 16


def test_proof_lifecycle_binds_at_gate5_and_consumes_at_gate9() -> None:
    hpac, rdgo = text(HPAC), text(RDGO)
    assert "PROOF_VERIFIED_AND_BOUND" in hpac
    assert "PROOF_CONSUMED_WITH_APPROVAL" in hpac
    assert "Gate-5 verification binds but does not" in hpac
    assert "single atomic approval-and-proof consumption point" in rdgo
    assert "does not consume the approval" in rdgo


def test_revocation_invalidates_every_unconsumed_authority_layer() -> None:
    hpac, rihac = text(HPAC), text(RIHAC)
    assert "unconsumed approvals, and derived PB authority projections invalid" in hpac
    assert "immediately invalidates every unconsumed approval" in rihac


def test_pbrd_consumes_typed_authority_evidence_not_fido2() -> None:
    body = text(PBRD)
    for field in (
        "authority_projection_id",
        "authority_projection_digest",
        "authority_contract_version",
        "proof_validation_digest",
        "request_binding_digest",
    ):
        assert field in body
    assert "PB SHALL NOT authenticate humans" in body
    assert "PB evaluation never consumes an approval" in body


def test_human_review_and_pol005_are_not_relaxed() -> None:
    body = text(PBRD)
    assert "Other applicable policies remain free to produce `DENY` or" in body
    assert "valid human authority does not suppress them" in body
    assert "POL-005 (`ExecutionDisabledRule`) is unchanged" in body


def test_rdgo_keeps_eleven_gates_and_first_effect_at_ten() -> None:
    body = text(RDGO)
    rows = re.findall(r"^\| (\d+) \|", body, re.M)
    assert rows[:11] == [str(i) for i in range(1, 12)]
    assert "Gate 10 is the first external execution effect" in body


def test_cross_contract_headers_close_active_version_graph() -> None:
    assert "RIHAC-001 v2.0" in text(PBRD).split("## 0.", 1)[0]
    rdgo_header = text(RDGO).split("## 0.", 1)[0]
    for marker in ("RIHAC-001 v2.0", "RIASC-001 v3.0", "HPAC-001 v2.0", "PBRD-001 v2.0"):
        assert marker in rdgo_header


def test_hatp_domain_is_separate() -> None:
    body = flat(HPAC)
    assert "separate registry" in body.lower()
    assert "A future implementation SHALL NOT allow an HPAC-001 verification to accept a HATP" in body


def test_required_report_has_all_55_sections_and_matrices() -> None:
    body = text(REPORT)
    for number in range(1, 56):
        assert re.search(rf"^## {number}\. ", body, re.M), number
    for label in ("Matrix A", "Matrix B", "Matrix C", "Matrix D", "Matrix E", "Matrix F", "Matrix G"):
        assert label in body


def test_report_freeze_verdict_and_no_go_state() -> None:
    body = text(REPORT)
    for marker in (
        "ORIGINAL BLOCKING: 7 / 7 CLOSED",
        "MUST-FIX: 2 / 2 CLOSED",
        "NEW BLOCKING: 0",
        "N2 CONTRACT GAP: CLOSED",
        "production source modified: NO",
        "hardware touched: NO",
        "execution activated: NO",
        "Observed / observe / unavailable",
    ):
        assert marker in body
