"""Phase 149O.20L.5A — Class-B Provisioning Target Environment Selection &
Preflight.

Planning/contract-only test coverage. No production host mutation is
performed or tested here; every assertion is either a static check against
the phase's own planning document, or a real, read-only, unmocked
re-invocation of the existing Class-B verifier followed by a repo-hygiene
check that no mutation occurred.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_5A_CLASS_B_PROVISIONING_TARGET_ENVIRONMENT_SELECTION_AND_PREFLIGHT.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _section(doc_text: str, heading: str) -> str:
    """Extract the body of a top-level (##) section by its exact heading text."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(doc_text)
    assert match, f"section {heading!r} not found in {DOC_PATH.name}"
    return match.group(1)


def _normalize(text: str) -> str:
    """Collapse whitespace and strip markdown blockquote '> ' line prefixes,
    so multi-line prose reads as one contiguous string for phrase checks."""
    lines = [line.strip().lstrip(">").strip() for line in text.splitlines()]
    return " ".join(part for part in lines if part)


def _extract_hbdc_ids(text: str) -> "set[str]":
    """Expand bundled citations like 'HBDC-REQ-007/013/014' into individual
    'HBDC-REQ-###' IDs."""
    ids: "set[str]" = set()
    for match in re.finditer(r"HBDC-REQ-(\d{3})((?:[/–-]\d{3}|\.\.\d{3})*)", text):
        ids.add(f"HBDC-REQ-{match.group(1)}")
        for part in re.findall(r"\d{3}", match.group(2)):
            ids.add(f"HBDC-REQ-{part}")
    return ids


def test_doc_exists_and_is_nonempty(doc_text: str) -> None:
    assert len(doc_text) > 5000


def _live_unmet_requirement_ids_and_status() -> "tuple[set[str], str]":
    """Invoke the verifier in a fresh, isolated interpreter subprocess
    (matching 149O.20L.5's own disclosed method) to avoid pytest's own
    assertion-rewrite meta_path finder producing a spurious HBDC-REQ-032
    result."""
    script = (
        "import sys; sys.path.insert(0, 'src')\n"
        "from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance\n"
        "r = verify_class_b_deployment_conformance()\n"
        "print(r.status.value)\n"
        "print('\\n'.join(c.check_id for c in r.checks if not c.satisfied))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.splitlines()
    status = lines[0].strip() if lines else ""
    ids = {line.strip() for line in lines[1:] if line.strip()}
    return ids, status


def test_real_host_class_b_conformance_is_not_compliant_and_host_unchanged() -> None:
    """Real, unmocked, read-only re-invocation -- must not be trusted from any
    earlier phase's report. Per HBDC-REQ-052/053 (closed vocabulary, no
    partial credit), any non-COMPLIANT status -- NON_COMPLIANT or
    INDETERMINATE alike -- confirms the host remains unprovisioned; this
    phase does not require an exact status-label match to L.5's own capture,
    since this document's own §4 discloses genuine environmental drift
    between the two live captures."""
    _, status = _live_unmet_requirement_ids_and_status()
    assert status != "COMPLIANT"

    status_after = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    allowed_relative_paths = {
        str(DOC_PATH.relative_to(REPO_ROOT)),
        str(Path(__file__).resolve().relative_to(REPO_ROOT)),
    }
    for line in status_after.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        assert path in allowed_relative_paths or any(
            path.startswith(prefix)
            for prefix in ("tasks/", ".pcae/", "PROJECT_STATUS.md", "CHANGELOG.md")
        ), f"unexpected git status entry outside this phase's own artifacts: {line!r}"


def test_every_live_non_compliant_reason_is_addressed_in_the_preflight_matrix(doc_text: str) -> None:
    matrix_section = _section(
        doc_text,
        "12. Preflight — Selected Target Against the 23 (Now 22, §4) Live HBDC Failure Categories",
    )
    live_ids, _status = _live_unmet_requirement_ids_and_status()
    assert live_ids, "expected at least one live non-COMPLIANT requirement on an unprovisioned host"

    mapped_ids = _extract_hbdc_ids(matrix_section)
    for req_id in live_ids:
        assert req_id in mapped_ids, (
            f"live-failing {req_id} is not present in the §12 preflight matrix"
        )


def test_preflight_matrix_has_no_unsupported_disposition(doc_text: str) -> None:
    matrix_section = _section(
        doc_text,
        "12. Preflight — Selected Target Against the 23 (Now 22, §4) Live HBDC Failure Categories",
    )
    assert "**Unsupported category:** none found" in matrix_section


def test_target_classified_as_provisionable_shell(doc_text: str) -> None:
    section = _section(doc_text, "9. Target Existence Classification")
    assert "**PROVISIONABLE TARGET SHELL.**" in section


def test_dev_deploy_separation_decision_is_explicit(doc_text: str) -> None:
    section = _section(doc_text, "8. Development/Deployment Separation Decision")
    normalized = _normalize(section).lower()
    assert "not, not as currently configured" in normalized or "no, not as currently configured" in normalized
    assert "dedicated clone" in normalized or "dedicated" in normalized


def test_current_dev_host_still_classified_unsuitable(doc_text: str) -> None:
    section = _section(doc_text, "5. Independent Reconstruction of Host Ineligibility (§2 of the Governing Prompt)")
    normalized = _normalize(section)
    assert "not silently reversed" in normalized.lower()
    assert "verdict stands unchanged" in normalized.lower()


def test_authorization_proposition_names_concrete_target_and_excludes_activation_certification(
    doc_text: str,
) -> None:
    section = _section(
        doc_text,
        "19. Boundary-P Proposition (Draft, Refined From L.5 §29 With a Concrete Target)",
    )
    normalized = _normalize(section).lower()
    assert "atilas-macbook-pro.local" in normalized
    assert "newly created, dedicated os admin principal" in normalized
    assert "without authorizing hmic certification" in normalized
    assert "without authorizing real" in normalized and "activation" in normalized
    assert "activate_hatp_mandatory" not in section


def test_explicit_exclusions_cover_developer_own_environment(doc_text: str) -> None:
    section = _section(doc_text, "21. Explicit Exclusions")
    normalized = _normalize(section)
    required_phrases = [
        "real OS principal",
        "real Protected Root",
        "real Python-",
        "HMIC certification",
        "HATP_MANDATORY` activation",
        "Permission Broker",
        "POL-005",
        "COMP-002",
        "developer's own existing account",
    ]
    for phrase in required_phrases:
        assert phrase in normalized, f"expected exclusion phrase {phrase!r} in §21"


def test_target_plan_and_proposition_sections_contain_no_activation_call(doc_text: str) -> None:
    """The plan/proposition sections may *disclaim* activation/certification
    in prose (they explicitly should), but must not contain an actual call
    reference or SSH-connection command anywhere in their own text."""
    forbidden = ["activate_hatp_mandatory(", "certify(", "revoke(", "ssh hac-", "ssh 192.168"]
    for heading in (
        "13. Target-Specific Mutation Plan (Recomputed, Not Reused Blindly)",
        "19. Boundary-P Proposition (Draft, Refined From L.5 §29 With a Concrete Target)",
    ):
        section = _section(doc_text, heading).lower()
        for token in forbidden:
            assert token.lower() not in section, f"forbidden token found in {heading!r}: {token!r}"


def test_human_clarification_on_candidate_hosts_recorded(doc_text: str) -> None:
    section = _section(doc_text, "3. Human Clarification Obtained This Phase")
    normalized = _normalize(section).lower()
    assert "unrelated" in normalized
    assert "exclude them" in normalized


def test_phase_exit_state_banner_shows_not_provisioned_not_ready(doc_text: str) -> None:
    exit_section = _section(doc_text, "26. Class-B / HATP / Runtime State (Phase Exit)")
    assert "NOT PROVISIONED" in exit_section
    assert "NOT READY" in exit_section
    assert "NOT AUTHORIZED" in exit_section


def test_this_phase_does_not_claim_human_authorization(doc_text: str) -> None:
    section = _section(doc_text, "22. Do Not Infer Authorization")
    normalized = _normalize(section).lower()
    assert "confers no authorization" in normalized


def test_repo_clean_and_no_production_source_touched() -> None:
    """This test file and the companion planning doc are the only new
    artifacts this phase introduces to src/pcae or docs/contracts."""
    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    for path in changed:
        assert not path.startswith("src/pcae/"), f"unexpected src/pcae/ modification: {path}"
        assert not path.startswith("docs/contracts/"), f"unexpected contract modification: {path}"
        assert not path.startswith("scripts/"), f"unexpected scripts/ modification: {path}"
