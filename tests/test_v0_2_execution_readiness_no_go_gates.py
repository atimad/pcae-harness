"""Tests for Phase 107C — Execution Readiness No-Go Gate Freeze.

Documentation-focused: verifies the frozen no-go gates document and its
accompanying phase document exist and make the required (and only the
required) claims. No live network access. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATES_PATH = REPO_ROOT / "docs" / "V0_2_EXECUTION_READINESS_NO_GO_GATES.md"
PHASE_DOC_PATH = REPO_ROOT / "docs" / "PHASE_107_EXECUTION_READINESS_NO_GO_GATE_FREEZE.md"

NG_IDS = [f"NG-{n:03d}" for n in range(1, 26)]

REQUIRED_FIELDS = [
    "Condition",
    "Rationale",
    "Required Remediation",
    "Recoverable",
    "Human Override Allowed",
    "Related Invariant",
    "Related Component",
    "Current Implementation Status",
]


@pytest.fixture(scope="module")
def gates_text() -> str:
    return GATES_PATH.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text()


# --- existence ---------------------------------------------------------------


def test_no_go_gates_doc_exists():
    assert GATES_PATH.is_file()


def test_phase_doc_exists():
    assert PHASE_DOC_PATH.is_file()


# --- all NG IDs exist ----------------------------------------------------------


@pytest.mark.parametrize("ng_id", NG_IDS)
def test_ng_id_present(gates_text, ng_id):
    assert ng_id in gates_text


def test_exactly_25_gate_headings(gates_text):
    headings = [f"### NG-{n:03d}" for n in range(1, 26)]
    for heading in headings:
        assert heading in gates_text


# --- each gate has all required fields -----------------------------------------


def _gate_sections(gates_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for i, ng_id in enumerate(NG_IDS):
        heading = f"### {ng_id}"
        start = gates_text.index(heading)
        if i + 1 < len(NG_IDS):
            next_heading = f"### {NG_IDS[i + 1]}"
            end = gates_text.index(next_heading)
        else:
            end = gates_text.index("## Gate Index")
        sections[ng_id] = gates_text[start:end]
    return sections


@pytest.fixture(scope="module")
def gate_sections(gates_text) -> dict[str, str]:
    return _gate_sections(gates_text)


@pytest.mark.parametrize("ng_id", NG_IDS)
@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_gate_has_required_field(gate_sections, ng_id, field):
    section = gate_sections[ng_id]
    assert f"**{field}:**" in section, f"{ng_id} missing field {field}"


# --- default human override posture ---------------------------------------------


def test_default_human_override_posture_is_no(gates_text):
    assert "Human override is `no` for every gate" in gates_text


@pytest.mark.parametrize("ng_id", NG_IDS)
def test_gate_human_override_is_no(gate_sections, ng_id):
    section = gate_sections[ng_id]
    idx = section.index("**Human Override Allowed:**")
    window = section[idx : idx + 60]
    assert "no" in window.lower()


# --- fail-closed rules -----------------------------------------------------------


def test_missing_evidence_fails_closed(gates_text):
    lowered = gates_text.lower()
    assert "missing evidence" in lowered
    assert "results in denial" in lowered or "fail closed" in lowered or "fail-closed" in lowered


def test_ambiguity_fails_closed(gates_text):
    lowered = gates_text.lower()
    assert "ambiguity" in lowered
    assert "fail closed" in lowered or "fail-closed" in lowered


def test_unavailable_broker_fails_closed(gates_text):
    lowered = gates_text.lower()
    assert "unavailable" in lowered
    assert "permission broker" in lowered


def test_unavailable_audit_fails_closed(gates_text):
    assert "NG-013" in gates_text
    assert "Audit Readiness Missing" in gates_text


def test_unavailable_rollback_fails_closed(gates_text):
    assert "NG-012" in gates_text
    assert "Rollback Readiness Missing" in gates_text


def test_emergency_stop_blocks_execution(gates_text):
    assert "NG-014" in gates_text
    lowered = " ".join(gates_text.lower().split())
    assert "overrides all execution authorization" in lowered or "overrides every" in lowered


def test_execution_enablement_remains_unavailable_default_off(gates_text):
    assert "NG-021" in gates_text
    lowered = gates_text.lower()
    assert "default-off" in lowered or "default off" in lowered


def test_telegram_inbound_remains_out_of_scope(gates_text):
    assert "NG-022" in gates_text
    lowered = gates_text.lower()
    assert "outbound-only" in lowered
    assert "no inbound handler" in lowered or "categorically no inbound" in lowered


# --- no overclaiming -------------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["gates_text", "phase_doc_text"])
def test_docs_do_not_claim_no_go_enforcement_implemented(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "no-go gate runtime enforcement is implemented" not in text
    assert "no-go gates are enforced" not in text


@pytest.mark.parametrize("fixture_name", ["gates_text", "phase_doc_text"])
def test_docs_do_not_claim_execution_available(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "execution is available" not in text
    assert "execution remains unavailable" in text or "execution unavailable" in text


@pytest.mark.parametrize("fixture_name", ["gates_text", "phase_doc_text"])
def test_docs_do_not_claim_autonomous_execution_available(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "autonomous execution is available" not in text


# --- recommended next phase -------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["gates_text", "phase_doc_text"])
def test_docs_recommend_next_phase_107d(fixture_name, request):
    text = request.getfixturevalue(fixture_name)
    assert "107D" in text
    assert "PR-Compatible Governed Development Workflow Design" in text
