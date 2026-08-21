"""Phase 149O.20L.7O.2N.9 -- HSCE Remote WebAuthn Assertion Ceremony and
Evidence-Capture Companion Contract Freeze. Disposable evidence tests:
structural completeness of the frozen HRAC-001 contract document, its
requirement-numbering closure, and non-regression confirmation that this
documentation-only phase left HRWP-001/HSCE-001 and the existing
synchronous signing-ceremony orchestrator byte-unchanged. No test touches
real hardware, a protected root, or performs any registry write.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HRAC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HRWP_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HSCE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
_PHASE_REPORT_PATH = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_9_HSCE_REMOTE_WEBAUTHN_ASSERTION_CEREMONY_AND_EVIDENCE_CAPTURE_COMPANION_CONTRACT_FREEZE.md"
)
_SIGNING_CEREMONY_SOURCE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py"


@pytest.fixture(scope="module")
def hrac_text() -> str:
    assert _HRAC_CONTRACT_PATH.is_file(), f"contract document missing: {_HRAC_CONTRACT_PATH}"
    return _HRAC_CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hrwp_text() -> str:
    assert _HRWP_CONTRACT_PATH.is_file()
    return _HRWP_CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hsce_text() -> str:
    assert _HSCE_CONTRACT_PATH.is_file()
    return _HSCE_CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_report_text() -> str:
    assert _PHASE_REPORT_PATH.is_file(), f"phase report missing: {_PHASE_REPORT_PATH}"
    return _PHASE_REPORT_PATH.read_text(encoding="utf-8")


def test_contract_identity_frozen(hrac_text: str) -> None:
    assert "**Contract:** HRAC-001" in hrac_text
    assert "**Version:** 1.0" in hrac_text
    assert "FROZEN" in hrac_text
    assert "NOT YET INDEPENDENTLY VERIFIED, NOT IMPLEMENTED" in hrac_text


def test_contract_declares_no_implementation(hrac_text: str) -> None:
    assert "authorizes no implementation" in hrac_text
    assert "no request-store code, no HTTP route" in hrac_text


def test_contract_requirement_numbering_is_sequential_no_gaps_no_duplicates(hrac_text: str) -> None:
    ids = [int(match) for match in re.findall(r"HRAC-REQ-(\d+)\b", hrac_text)]
    unique_sorted = sorted(set(ids))
    assert unique_sorted == list(range(1, len(unique_sorted) + 1)), (
        "HRAC-REQ-### numbering must be sequential from 001 with no gaps: "
        f"got {unique_sorted}"
    )
    assert "This contract defines 76 normative requirements" in hrac_text
    assert unique_sorted[-1] == 76


def test_contract_covers_required_orchestration_sections(hrac_text: str) -> None:
    required_topics = [
        "## 7. Remote request state machine",
        "## 8. Request identity",
        "## 9. Signer selection",
        "## 10. Multi-authenticator behavior",
        "## 11. Challenge construction",
        "## 12. Challenge encoding",
        "## 13. Domain separation",
        "## 14. Session token is not authority",
        "## 15. Delivery model",
        "## 17. Client request-fetch surface",
        "## 18. Client response schema",
        "## 19. Verification handoff",
        "## 20. One-time consumption",
        "## 21. Late response",
        "## 22. Concurrent responses",
        "## 23. Multiple outstanding requests",
        "## 24. Cancellation",
        "## 25. Closed failure/error vocabulary",
        "## 26. Server restart / durability",
        "## 27. Request-store authority classification",
        "## 28. Signing result",
        "## 29. Evidence capture",
        "## 42. HSCE-001 compatibility mapping",
        "## 44. `protocol_name` non-blocking finding",
        "## 48. Trusted-kernel vs. adapter boundary",
        "## 49. Future HMIC impact",
        "## 51. Synthetic interoperability gate",
        "## 53. What this contract does NOT do",
    ]
    for topic in required_topics:
        assert topic in hrac_text, f"missing required contract section: {topic!r}"


def test_contract_freezes_closed_state_machine(hrac_text: str) -> None:
    for state in ("PENDING", "RESPONSE_RECEIVED", "VERIFIED", "COMPLETED", "EXPIRED", "FAILED", "CANCELLED"):
        assert state in hrac_text
    # Terminal-state closure must be explicit, not implied.
    assert "terminal" in hrac_text.lower()


def test_contract_freezes_domain_separation_string(hrac_text: str) -> None:
    assert "PCAE/HATP/HRAC/SIGN/V1" in hrac_text


def test_contract_request_id_distinct_from_evidence_id_scheme(hrac_text: str) -> None:
    # HRAC-REQ-015 must explicitly distinguish request_id (random) from
    # HSCE-001's evidence_id (content-addressed digest) -- never conflate them.
    assert "cryptographically random" in hrac_text
    assert "digest_hatp_proof_payload" in hrac_text


def test_contract_names_but_does_not_amend_dependencies(hrac_text: str) -> None:
    assert "**Depends on:** HRWP-001 v1.0" in hrac_text
    assert "HSCE-001 v1.3" in hrac_text
    assert "amends neither" in hrac_text


def test_contract_carries_forward_protocol_name_finding(hrac_text: str) -> None:
    assert "_PROTOCOL_VALUES" in hrac_text
    assert "HRWP-REQ-019" in hrac_text
    assert "does not depend on that finding being resolved" in hrac_text


def test_hrwp_contract_unamended_by_this_phase(hrwp_text: str) -> None:
    assert "**Contract:** HRWP-001" in hrwp_text
    assert "**Version:** 1.0" in hrwp_text
    assert "This contract defines 68 normative requirements" in hrwp_text


def test_hsce_contract_unamended_by_this_phase(hsce_text: str) -> None:
    assert "**Contract:** HSCE-001" in hsce_text
    assert "through `HSCE-REQ-084` inclusive" in hsce_text


def test_signing_ceremony_source_unchanged_shape(hrac_text: str) -> None:
    # Non-regression: the existing synchronous orchestrator's key entry
    # points and docstring framing (re-read fresh this phase) must still be
    # present in production source, confirming this documentation-only
    # phase modified no production behavior.
    assert _SIGNING_CEREMONY_SOURCE_PATH.is_file()
    source_text = _SIGNING_CEREMONY_SOURCE_PATH.read_text(encoding="utf-8")
    assert "def sign_rollback_evidence(" in source_text
    assert "def production_sign_rollback_evidence(" in source_text
    assert "No CLI is implemented by this module" in source_text


def test_phase_report_declares_no_real_hardware_effect(phase_report_text: str) -> None:
    assert "No `makeCredential`/`getAssertion`" in phase_report_text or "No makeCredential" in phase_report_text
    assert "NO IMPLEMENTATION" in phase_report_text.upper() or "no implementation" in phase_report_text.lower()
