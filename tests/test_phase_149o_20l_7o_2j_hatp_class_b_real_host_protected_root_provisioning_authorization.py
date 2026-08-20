"""Phase 149O.20L.7O.2J — HATP Class-B Real Host Protected Root Provisioning
Authorization.

Authorization/planning-only evidence checks. These tests do not build a
remote provisioning engine and perform no SSH/host mutation. They
mechanically confirm the primary-source facts this phase's document
relies on: the exact Protected Root resolution path, the exact readiness
checks that (per repo-committed real-host evidence) already evaluate
compliant on hac-dell, the HMIC 36/7 frozen-identity baseline, and that
no production source changed since phase entry.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_SRC = REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
CUTOVER_SRC = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
CONFORMANCE_SRC = REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py"
CERTIFICATION_SRC = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
HBDC_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
HMIC_CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2J_HATP_CLASS_B_REAL_HOST_PROTECTED_ROOT_PROVISIONING_AUTHORIZATION.md"
)

pytestmark = pytest.mark.fast_green


def test_protected_root_resolution_has_no_override_surface():
    text = BOOTSTRAP_SRC.read_text(encoding="utf-8")
    assert 'def _default_production_trust_root() -> Path:' in text
    assert '_LINUX_FIXED_TRUST_ROOT = Path("/etc/pcae/hatp/trust-store")' in text
    assert "def production(cls)" in text
    idx_def = text.index("def production(cls)")
    idx_doc = text.index('"""The only production construction path.', idx_def)
    assert idx_doc - idx_def < 80


def test_readiness_protected_storage_check_is_pure_directory_existence():
    text = CUTOVER_SRC.read_text(encoding="utf-8")
    assert '"class_b_protected_storage_available"' in text
    idx = text.index('"class_b_protected_storage_available"')
    window = text[idx : idx + 400]
    assert "protected_root_available" in window


def test_readiness_authority_check_uses_mode_bits_0o022():
    text = CUTOVER_SRC.read_text(encoding="utf-8")
    assert '"protected_activation_authority_mechanism_available"' in text
    assert "mode & 0o022" in text


def test_hbdc_req_042_is_the_deployment_identity_binding_check_not_protected_root():
    text = CONFORMANCE_SRC.read_text(encoding="utf-8")
    assert "HBDC-REQ-042" in text
    assert "no_active_deployment_binding_matches_repository_and_root" in text
    assert "no_repository_identity_present" in text


def test_hbdc_contract_protected_root_requirements_present_and_numbered():
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "**Version:** 1.2" in text
    for req in (
        "HBDC-REQ-011",
        "HBDC-REQ-012",
        "HBDC-REQ-013",
        "HBDC-REQ-014",
        "HBDC-REQ-015",
        "HBDC-REQ-016",
        "HBDC-REQ-017",
        "HBDC-REQ-018",
    ):
        assert req in text


def test_hmic_frozen_identity_is_still_exactly_36_members_27_plus_9():
    """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
    governing prompt): true at this phase's own exit commit
    (e2c1772d). Superseded for LIVE production state by Phase
    149O.20L.7O.2M's own HMIC v1.7 widening (36 -> 38)."""

    text = subprocess.check_output(
        ["git", "show", "e2c1772d:src/pcae/core/hatp_mandatory_certification.py"],
        cwd=REPO_ROOT,
        text=True,
    )
    src_block = re.search(
        r"_FROZEN_SRC_PCAE_RELATIVE_FILES.*?=\s*\((.*?)\)\n\n",
        text,
        re.DOTALL,
    )
    root_block = re.search(
        r"_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES.*?=\s*\((.*?)\)\n\n",
        text,
        re.DOTALL,
    )
    assert src_block is not None and root_block is not None
    src_count = len(re.findall(r'"[^"]+"\s*,', src_block.group(1)))
    root_count = len(re.findall(r'"[^"]+"\s*,', root_block.group(1)))
    assert src_count == 27, src_count
    assert root_count == 9, root_count
    assert src_count + root_count == 36


def test_hmic_contract_still_version_1_6_frozen():
    """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
    governing prompt) -- see docstring above."""

    text = subprocess.check_output(
        ["git", "show", "e2c1772d:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"],
        cwd=REPO_ROOT,
        text=True,
    )
    assert "**Version:** 1.6" in text
    assert "FROZEN" in text[:400]


def test_no_production_source_changed_since_phase_entry_commit():
    """Pinned to this phase's own entry/exit commits (§26 of the
    149O.20L.7O.2M governing prompt: historical snapshot, preserved)."""

    entry_commit = "8871b4bf34009b3db29a2d4f83cf78f3e93d2c6a"
    exit_commit = "e2c1772d"
    diff = subprocess.run(
        ["git", "diff", "--name-only", entry_commit, exit_commit, "--", "src", "docs/contracts"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    assert changed == [], f"unexpected production/contract changes: {changed}"


def test_no_real_trust_enrollment_or_certification_state_files_exist():
    forbidden_names = {
        "certifications.json",
        "certification-bindings.json",
        "hardware-credentials.json",
    }
    found = []
    for path in REPO_ROOT.rglob("*.json"):
        if ".claude/worktrees" in str(path):
            continue
        if path.name in forbidden_names:
            found.append(str(path.relative_to(REPO_ROOT)))
    assert found == [], f"real certification/enrollment state files found: {found}"


def test_authorization_doc_exists_states_no_creation_authorized():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    assert len(text) > 4000
    normalized = " ".join(text.split())
    assert "NO CREATION AUTHORIZATION IS ISSUED OR REQUIRED" in normalized
    assert "no SSH connection was opened to hac-dell" in text


def test_authorization_doc_cites_prior_real_host_evidence_dates():
    text = DOC.read_text(encoding="utf-8")
    for phase_marker in ("149O.20L.7E", "149O.20L.7N.5", "149O.20L.7O.2A.5", "149O.20L.7O.2B.1"):
        assert phase_marker in text
    assert "2026-08-18" in text
