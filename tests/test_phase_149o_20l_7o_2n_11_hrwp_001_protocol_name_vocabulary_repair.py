"""Phase 149O.20L.7O.2N.11 -- HRWP-001 protocol_name Closed-Vocabulary
Contract Clarification.

Repairs the CONTRACT TEXT ONLY for NBF-149O.20L.7O.2N.8-1 (found by Phase
149O.20L.7O.2N.8's independent verification, reconfirmed by Phase
149O.20L.7O.2N.10): HRWP-REQ-019 v1.0 claimed protocol_name = "WEBAUTHN"
requires "no schema widening" at all; production's `_PROTOCOL_VALUES` is
in fact a closed frozenset, so an additive vocabulary widening (not a
structural schema widening) is required before a real remote-WebAuthn
record could ever be durably enrolled.

CONTRACT-TEXT REPAIR ONLY. No implementation. No protocol_name value is
added to production here -- `_PROTOCOL_VALUES` remains exactly
{"FIDO2", "PIV"} in this phase.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HHCE_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
_HSCE_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
_CREDENTIALS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"


def _hrwp_text() -> str:
    return _HRWP_PATH.read_text(encoding="utf-8")


def test_hrwp_version_bumped_to_1_1_and_status_reflects_repair():
    text = _hrwp_text()
    assert "**Version:** 1.1" in text
    assert "CONTRACT REPAIRED" in text
    assert "NBF-149O.20L.7O.2N.8-1" in text


def test_hrwp_req_019_revised_in_place_same_identity_no_renumbering():
    text = _hrwp_text()
    numbers = [int(n) for n in re.findall(r"\*\*HRWP-REQ-(\d+)", text)]
    unique_numbers = sorted(set(numbers))
    assert unique_numbers == list(range(1, 69)), "HRWP-REQ-001..068 must remain sequential, gapless, unique"
    assert "**HRWP-REQ-019 (revised, v1.1" in text


def test_hrwp_req_019_correctly_states_closed_vocabulary_requires_widening():
    text = _hrwp_text()
    req_019_match = re.search(
        r"\*\*HRWP-REQ-019 \(revised.*?\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", text, re.DOTALL
    )
    assert req_019_match is not None
    req_019_text = req_019_match.group(1)
    assert "_PROTOCOL_VALUES" in req_019_text
    assert "closed" in req_019_text.lower()
    assert "widen" in req_019_text.lower()
    # No longer claims zero vocabulary work is required.
    assert "requiring no schema widening" not in req_019_text


def test_hrwp_req_019_still_distinguishes_schema_shape_from_vocabulary():
    """The repair must not blur structural schema (unchanged) with closed
    vocabulary (must expand) -- both claims must survive, distinctly."""
    text = _hrwp_text()
    req_019_match = re.search(
        r"\*\*HRWP-REQ-019 \(revised.*?\*\*(.*?)(?=\n\n\*\*HRWP-REQ-020)", text, re.DOTALL
    )
    assert req_019_match is not None
    req_019_text = req_019_match.group(1)
    assert "no `HardwareCredentialRecord` structural schema widening" in req_019_text
    assert "additive closed-vocabulary widening" in req_019_text


def test_hrwp_structural_schema_claims_elsewhere_are_unchanged():
    """§10/§31-§33's "no schema widening required" claims for
    HardwareCredentialRecord/SignerRecord/DeploymentBinding are untouched
    by this repair -- only HRWP-REQ-019's vocabulary claim changes."""
    text = _hrwp_text()
    assert "**HRWP-REQ-056.** No `HardwareCredentialRecord`/HHCE-001 schema field changes are required" in text
    assert "**HRWP-REQ-057.** No `SignerRecord`/HPSE-001 schema field changes are required." in text
    assert "**HRWP-REQ-058.** No `DeploymentBinding`/HBDC-001 schema change is required." in text


def test_hrwp_v1_1_repair_section_present_and_names_disposition():
    text = _hrwp_text()
    assert "## 45. v1.1 Repair (Phase 149O.20L.7O.2N.11" in text
    assert "REPAIRED — INDEPENDENT VERIFICATION PENDING" in text
    assert "add exactly one value, `\"WEBAUTHN\"`, to `_PROTOCOL_VALUES`" in text


def test_hrwp_repair_section_records_no_hrac_hsce_hhce_amendment():
    text = _hrwp_text()
    repair_section = text[text.index("## 45. v1.1 Repair"):]
    assert "**HRAC-001:** No amendment, no version bump." in repair_section
    assert "**HSCE-001:** No amendment, no version bump." in repair_section
    assert "**HHCE-001:** No amendment, no version bump." in repair_section


def test_requirement_count_note_updated_to_reflect_in_place_revision():
    text = _hrwp_text()
    assert "This count is unchanged by the v1.1 repair (§45)" in text
    assert "68 normative requirements" in text


def test_production_protocol_values_still_exactly_fido2_piv_no_implementation_here():
    """Contract-text-only phase: _PROTOCOL_VALUES SHALL NOT be touched by
    this phase."""
    src = _CREDENTIALS_SRC.read_text(encoding="utf-8")
    match = re.search(r"_PROTOCOL_VALUES\s*=\s*frozenset\(\{([^}]*)\}\)", src)
    assert match is not None
    values = {v.strip().strip('"') for v in match.group(1).split(",") if v.strip()}
    assert values == {"FIDO2", "PIV"}, "production _PROTOCOL_VALUES must remain unimplemented/unwidened this phase"
    assert "WEBAUTHN" not in src


def test_hrac_hsce_hhce_contracts_unmodified_by_this_phase():
    """This is a narrow HRWP-001-only text repair; HRAC-001/HSCE-001/
    HHCE-001 SHALL NOT gain new content or a version bump."""
    assert "**Version:** 1.0" in _HRAC_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.1" in _HHCE_PATH.read_text(encoding="utf-8")
    hsce_text = _HSCE_PATH.read_text(encoding="utf-8")
    assert "**Contract:** HSCE-001" in hsce_text


def test_hrac_finding_disposition_text_is_still_accurate_after_repair():
    """HRAC-001's own §44 already described this finding as "carried
    forward, not resolved" -- that description remains accurate: this
    phase resolves the contract-text mismatch, not the production
    _PROTOCOL_VALUES widening HRAC-REQ-066/074 name as still pending."""
    hrac_text = _HRAC_PATH.read_text(encoding="utf-8")
    assert "HRAC-REQ-066" in hrac_text
    assert "does not depend on that finding being resolved" in hrac_text
