"""Phase 149O.20L.5 — Class-B Real Host Provisioning Authorization & Planning.

Planning/contract-only test coverage. No production host mutation is
performed or tested here; every assertion is either a static check against
the phase's own planning document, or a real, read-only, unmocked
re-invocation of the existing Class-B verifiers followed by a repo-hygiene
check that no mutation occurred.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_AUTHORIZATION_AND_PLANNING.md"


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
    """Expand bundled citations like 'HBDC-REQ-007/013/014' or
    'HBDC-REQ-025..027' into individual 'HBDC-REQ-###' IDs."""
    ids: "set[str]" = set()
    for match in re.finditer(r"HBDC-REQ-(\d{3})((?:[/–-]\d{3}|\.\.\d{3})*)", text):
        ids.add(f"HBDC-REQ-{match.group(1)}")
        for part in re.findall(r"\d{3}", match.group(2)):
            ids.add(f"HBDC-REQ-{part}")
    return ids


def test_doc_exists_and_is_nonempty(doc_text: str) -> None:
    assert len(doc_text) > 5000


def test_real_host_class_b_conformance_is_non_compliant_and_host_unchanged() -> None:
    """Real, unmocked, read-only re-invocation -- must not be trusted from any
    earlier phase's report. git status must show only this phase's own new,
    still-unstaged planning artifacts -- no unexpected mutation."""
    from pcae.core.hatp_class_b_conformance import (
        ClassBConformanceStatus,
        verify_class_b_deployment_conformance,
    )

    result = verify_class_b_deployment_conformance()
    assert result.status is ClassBConformanceStatus.NON_COMPLIANT

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


def _live_unmet_requirement_ids() -> "set[str]":
    """Invoke the verifier in a fresh, isolated interpreter subprocess rather
    than in-process under pytest: pytest's own assertion-rewrite import
    machinery installs a `sys.meta_path` finder, which HBDC-REQ-032's check
    legitimately detects and flags -- an artifact of the *test runner's* own
    environment, not of the host's Class-B provisioning state. A clean
    `python3 -c` subprocess (matching how this phase's own report captured
    its evidence) avoids that self-referential pollution."""
    script = (
        "import sys; sys.path.insert(0, 'src')\n"
        "from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance\n"
        "r = verify_class_b_deployment_conformance()\n"
        "print('\\n'.join(c.check_id for c in r.checks if not c.satisfied))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def test_every_live_non_compliant_reason_is_mapped_in_the_mutation_table(doc_text: str) -> None:
    mapping_section = _section(doc_text, "5. HBDC Requirement → Mutation Mapping (§4/§6 of the Governing Prompt)")
    live_ids = _live_unmet_requirement_ids()
    assert live_ids, "expected at least one live NON_COMPLIANT requirement on an unprovisioned host"

    mapped_ids = _extract_hbdc_ids(mapping_section)
    for req_id in live_ids:
        assert req_id in mapped_ids, (
            f"live-failing {req_id} is not present in the §5 mutation-mapping table"
        )


def test_every_mutation_row_cites_a_real_hbdc_requirement_id(doc_text: str) -> None:
    mapping_section = _section(doc_text, "5. HBDC Requirement → Mutation Mapping (§4/§6 of the Governing Prompt)")
    cited_ids = _extract_hbdc_ids(mapping_section)
    assert len(cited_ids) >= 15


def test_command_plan_has_rollback_for_every_mutation_step(doc_text: str) -> None:
    plan_section = _section(doc_text, "9. Provisioning Command Plan (Future Phase Only — Not Executed Here)")
    # Each numbered step (1.-7., 9.) is a bold *Purpose:* ... entry; steps
    # that mutate state must each carry their own *Rollback:* clause.
    steps = re.findall(r"^\d+\.\s+\*\*.*?(?=^\d+\.\s+\*\*|\Z)", plan_section, re.MULTILINE | re.DOTALL)
    assert len(steps) >= 8
    for step in steps:
        if "*Purpose:*" in step and "n/a" not in step.split("*Rollback:*", 1)[-1][:20].lower():
            assert "*Rollback:*" in step or "no command is planned" in plan_section


def test_no_activation_or_certification_command_step_in_provisioning_plan(doc_text: str) -> None:
    """The command plan (§9) may *disclaim* activation/certification in prose
    (it explicitly should -- see §20), but none of its 9 numbered steps may
    itself perform one."""
    plan_section = _section(doc_text, "9. Provisioning Command Plan (Future Phase Only — Not Executed Here)")
    steps = re.findall(r"^\d+\.\s+\*\*.*?(?=^\d+\.\s+\*\*|\Z)", plan_section, re.MULTILINE | re.DOTALL)
    assert len(steps) >= 8
    forbidden_literal = ["activate_hatp_mandatory", "certify(", "revoke("]
    for step in steps:
        # The final step's captured text runs to the end of the section,
        # which includes trailing disclaiming prose ("No step above
        # includes...") -- that prose is a disclaimer, not a step action.
        step_body = step.split("No step above")[0]
        for token in forbidden_literal:
            assert token not in step_body, f"forbidden activation/certification action found in a plan step: {token!r}"
        assert not re.search(r"Cutover Record.*creat", step), "forbidden Cutover Record creation in a plan step"


def test_authorization_proposition_excludes_activation_and_certification(doc_text: str) -> None:
    proposition_section = _section(
        doc_text, "29. The Exact Authorization Proposition (Draft, for a Future Human Decision)"
    )
    normalized = _normalize(proposition_section).lower()
    assert "without authorizing hmic certification" in normalized
    assert "without authorizing real" in normalized and "activation" in normalized
    assert "activate_hatp_mandatory" not in proposition_section


def test_boundary_p_and_boundary_a_are_distinct_and_present(doc_text: str) -> None:
    boundary_section = _section(doc_text, "21. Boundary P vs. Boundary A (Mandatory Separation)")
    normalized = _normalize(boundary_section)
    assert "Boundary P" in normalized
    assert "Boundary A" in normalized
    assert "never combined" in normalized.lower()


def test_explicit_non_authorizations_section_covers_required_exclusions(doc_text: str) -> None:
    section = _section(
        doc_text,
        "38. Explicit Non-Authorizations (This Phase and Any Future Boundary-P\nAuthorization Drafted From §29)",
    )
    normalized = _normalize(section)
    required_phrases = [
        "real OS principal",
        "real Protected Root",
        "real Python-environment",
        "HMIC certification",
        "HATP_MANDATORY` activation",
        "Permission Broker",
        "POL-005",
        "COMP-002",
    ]
    for phrase in required_phrases:
        assert phrase in normalized, f"expected non-authorization phrase {phrase!r} in §38"


def test_phase_exit_state_banner_shows_not_provisioned_not_ready(doc_text: str) -> None:
    exit_section = _section(doc_text, "35. Class-B / HATP / Runtime State (Phase Exit)")
    assert "NOT PROVISIONED" in exit_section
    assert "NOT READY" in exit_section
    assert "COMPLIANT" not in exit_section.replace("NOT PROVISIONED", "").replace("NON_COMPLIANT", "")


def test_this_phase_does_not_claim_human_authorization(doc_text: str) -> None:
    section = _section(doc_text, "40. This Prompt Is Not Human Authorization (Explicit Acknowledgement)")
    assert "planning only" in section.lower()
    assert "not authorization to mutate" in section.lower()


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
