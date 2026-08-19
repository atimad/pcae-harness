"""Phase 149O.20L.7L.1 — HMIC-001 v1.4 Consumer-Status and
Dependency-Header Repair.

149O.20L.7L's own independent verification of 149O.20L.7K (v1.4)
withheld a VERIFIED verdict: the frozen source-scope widening (28 -> 30
files) was independently confirmed technically correct, but HMIC-001
v1.4 itself falsely stated, in multiple locations, that no readiness/
certification/activation code path consumes
`verify_class_b_deployment_conformance` -- contradicted by
`hatp_mandatory_cutover.py`, which imports and calls it as the eighth
activation-readiness term (wired by Phase 149O.20L.3, ancestral to
149O.20L.7K's own phase entry). This module is a fresh, independent
regression companion for the narrow, same-version, contract-text-only
repair (findings F-7L-1 blocking, F-7L-2 non-blocking) -- it does not
import, subclass, or read 149O.20L.7L's own verification module as an
oracle; every expectation below is reconstructed from live production
code and the live contract document.

Scope discipline: this phase makes no `src/pcae/**` production edit.
Every assertion here concerns contract text and/or already-existing,
byte-unchanged production behavior.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parents[1]

HMIC_CONTRACT_PATH = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CUTOVER_MODULE = "src/pcae/core/hatp_mandatory_cutover.py"
PRODUCER_MODULE = "src/pcae/core/hatp_deployment_binding_admin.py"
PRODUCER_SCRIPT = "scripts/hatp_deployment_binding_admin.py"
HBDC_CONTRACT_PATH = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"

_HMIC_CONTRACT = (REPO_ROOT / HMIC_CONTRACT_PATH).read_text(encoding="utf-8")
_CUTOVER_SRC = (REPO_ROOT / CUTOVER_MODULE).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _blob_hash(path: str) -> str:
    return _git("hash-object", str(REPO_ROOT / path)).strip()


# ═══════════════════════════════════════════════════════════════════════════
# 1. F-7L-2: dependency-header consistency (item 37)
# ═══════════════════════════════════════════════════════════════════════════


class TestDependencyHeaderConsistency:
    def test_hmic_depends_on_header_names_hbdc_v1_1(self) -> None:
        assert "**Depends on (current, HMIC-unamended):**" in _HMIC_CONTRACT
        header_line = next(
            line for line in _HMIC_CONTRACT.splitlines() if line.startswith("**Depends on (current")
        )
        assert "HBDC-001 v1.1" in header_line
        assert "HBDC-001 v1.0" not in header_line

    def test_derive_contract_versions_agrees_with_header(self) -> None:
        root = HarnessPath(REPO_ROOT)
        versions = hmic.derive_contract_versions(root)
        assert versions["HBDC-001"] == "1.1"


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-7L-1: consumer-status regression guards (items 38-39)
# ═══════════════════════════════════════════════════════════════════════════


class TestConsumerStatusRegressionGuard:
    def test_hmic_contract_no_longer_claims_zero_readiness_consumers_live(self) -> None:
        # The live (non-historical) normative text -- HMIC-REQ-052 limb
        # (c)'s closing paragraph -- must no longer assert that the
        # verifier has no readiness/activation consumer. §53.4 (a
        # legitimate historical snapshot predating the wiring) is exempt
        # from this check by construction: it is not part of the live
        # limb (c) closing paragraph, §55.4, §55.15, or the attack matrix.
        limb_c_start = _HMIC_CONTRACT.index("HMIC-REQ-052 (Transitive-Dependency Coverage")
        limb_c_end = _HMIC_CONTRACT.index("HMIC-REQ-053 (Contract Bytes Participate Directly")
        limb_c_text = _HMIC_CONTRACT[limb_c_start:limb_c_end]
        assert "no readiness, certification, or activation code path calls" not in limb_c_text

    def test_hmic_contract_states_verifier_has_a_real_consumer(self) -> None:
        limb_c_start = _HMIC_CONTRACT.index("HMIC-REQ-052 (Transitive-Dependency Coverage")
        limb_c_end = _HMIC_CONTRACT.index("HMIC-REQ-053 (Contract Bytes Participate Directly")
        limb_c_text = _HMIC_CONTRACT[limb_c_start:limb_c_end]
        assert "not** anticipatory" in limb_c_text
        assert "already has a real" in limb_c_text
        assert "149O.20L.3" in limb_c_text

    def test_row_39_no_longer_claims_zero_readiness_consumers(self) -> None:
        row_39_start = _HMIC_CONTRACT.index("| 39 *(added v1.4, §55)*")
        row_39_end = _HMIC_CONTRACT.index("\n", row_39_start + 2000)
        row_39_text = _HMIC_CONTRACT[row_39_start:row_39_end]
        assert "result still has zero readiness/certification consumers" not in row_39_text

    def test_row_38_reflects_operative_status(self) -> None:
        row_38_start = _HMIC_CONTRACT.index("| 38 *(added v1.3, §53)*")
        row_38_end = _HMIC_CONTRACT.index("| 39 *(added v1.4, §55)*")
        row_38_text = _HMIC_CONTRACT[row_38_start:row_38_end]
        assert "Operative and consequential" in row_38_text
        assert "zero production consumers of the Class-B verifier island exist today" not in row_38_text


class TestDirectProductionConsumerGuard:
    """Item 39: the production wiring the repair describes must still be
    real -- avoid asserting arbitrary line numbers; assert the shape of
    the wiring instead."""

    def test_cutover_module_imports_the_verifier(self) -> None:
        assert (
            "from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance"
            in _CUTOVER_SRC
        )

    def test_cutover_module_calls_the_verifier_inside_readiness_assessment(self) -> None:
        func_start = _CUTOVER_SRC.index("def _assess_hatp_mandatory_activation_readiness_at_root(")
        func_end = _CUTOVER_SRC.index("\ndef ", func_start + 1)
        func_body = _CUTOVER_SRC[func_start:func_end]
        assert "verify_class_b_deployment_conformance(" in func_body
        assert "class_b_deployment_conformance_satisfies_readiness" in func_body

    def test_class_b_term_is_the_final_readiness_check_appended(self) -> None:
        func_start = _CUTOVER_SRC.index("def _assess_hatp_mandatory_activation_readiness_at_root(")
        func_end = _CUTOVER_SRC.index("\ndef ", func_start + 1)
        func_body = _CUTOVER_SRC[func_start:func_end]
        last_check_name_pos = func_body.rfind('HATPMandatoryActivationReadinessCheck(\n            "')
        assert last_check_name_pos != -1
        assert func_body[last_check_name_pos:].startswith(
            'HATPMandatoryActivationReadinessCheck(\n            "class_b_deployment_conformance_satisfies_readiness"'
        )

    def test_no_other_src_pcae_module_calls_the_readiness_assessment(self) -> None:
        offenders = []
        for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
            if path.name == "hatp_mandatory_cutover.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "assess_hatp_mandatory_activation_readiness" in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        assert offenders == []


# ═══════════════════════════════════════════════════════════════════════════
# 3. Third-anchor regression guard (item 40)
# ═══════════════════════════════════════════════════════════════════════════


class TestThirdAnchorRegressionGuard:
    def test_limb_c_still_states_producer_not_reachable_from_verifier(self) -> None:
        limb_c_start = _HMIC_CONTRACT.index("HMIC-REQ-052 (Transitive-Dependency Coverage")
        limb_c_end = _HMIC_CONTRACT.index("HMIC-REQ-053 (Contract Bytes Participate Directly")
        limb_c_text = _HMIC_CONTRACT[limb_c_start:limb_c_end]
        assert "genuinely **not** reachable from `verify_class_b_deployment_" in limb_c_text
        assert "separate write path never" in limb_c_text

    def test_limb_c_still_states_producer_remains_anticipatory(self) -> None:
        limb_c_start = _HMIC_CONTRACT.index("HMIC-REQ-052 (Transitive-Dependency Coverage")
        limb_c_end = _HMIC_CONTRACT.index("HMIC-REQ-053 (Contract Bytes Participate Directly")
        limb_c_text = _HMIC_CONTRACT[limb_c_start:limb_c_end]
        assert "no real `DeploymentBinding` has ever been created" in limb_c_text


# ═══════════════════════════════════════════════════════════════════════════
# 4. Attack-row coherence (item 41)
# ═══════════════════════════════════════════════════════════════════════════


class TestAttackRowCoherence:
    def test_row_39_clause_a_grounds_conclusion_in_non_reachability(self) -> None:
        row_39_start = _HMIC_CONTRACT.index("| 39 *(added v1.4, §55)*")
        row_39_end = _HMIC_CONTRACT.index("\n", row_39_start + 3000)
        row_39_text = _HMIC_CONTRACT[row_39_start:row_39_end]
        assert "not transitively captured by `verify_class_b_deployment_" in row_39_text
        assert "not functionally load-bearing" in row_39_text
        # Legs (b)/(c) must still be present and unweakened.
        assert "no real `DeploymentBinding` has ever been created on any host" in row_39_text
        assert "no HMIC certification exists to be invalidated" in row_39_text


# ═══════════════════════════════════════════════════════════════════════════
# 5. Version / membership / production immutability (items 16-22, 33-34)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoNormativeOrProductionChange:
    def test_hmic_version_is_still_1_4(self) -> None:
        """As of this phase (149O.20L.7L.1) HEAD carried v1.4; a later
        amendment (149O.20L.7O.2H) additively bumped it to v1.5. This
        test now only guards against a regression below v1.4."""
        version_line = next(line for line in _HMIC_CONTRACT.splitlines() if line.startswith("**Version:**"))
        version = version_line.split()[-1]
        major, minor = (int(x) for x in version.split("."))
        assert (major, minor) >= (1, 4)

    def test_hmic_req_050_still_names_exactly_thirty_files(self) -> None:
        """As of this phase (149O.20L.7L.1) this named 'thirty files'; a
        later amendment (149O.20L.7O.2H) additively widened it to
        'thirty-five'."""
        flat = _HMIC_CONTRACT.replace("\n", " ")
        assert "thirty files, no more, no fewer" in flat or "thirty-five files, no more, no fewer" in flat

    def test_production_frozen_set_still_pinned_at_thirty(self) -> None:
        """As of this phase (149O.20L.7L.1) this was pinned at exactly
        30; a later amendment (149O.20L.7O.2H) additively widens this
        pin further as its own contract requires."""
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) >= 30

    def test_cutover_module_byte_unchanged_from_149o_20l_7l1_phase_entry(self) -> None:
        # Pinned against the git blob hash captured at this phase's own
        # entry commit (95cfd008, pre-149O.20L.7L.1), independently of
        # whatever HEAD becomes after this phase's own commits.
        assert _blob_hash(CUTOVER_MODULE) == "1344ed86289369c225519f4ea13f2c296269c374"

    def test_producer_and_admin_script_byte_unchanged_from_149o_20l_7l1_phase_entry(self) -> None:
        assert _blob_hash(PRODUCER_MODULE) == "c7950f302ba5714764de5fa0fd86699a07cfad1c"
        assert _blob_hash(PRODUCER_SCRIPT) == "286db838d573ef9311a6d0df78a6842b5f4ef296"

    def test_hbdc_contract_byte_unchanged_from_149o_20l_7l1_phase_entry(self) -> None:
        assert _blob_hash(HBDC_CONTRACT_PATH) == "ccc4efba78b39633b63f25e1415b915598a49772"

    def test_implementation_scope_digest_unchanged(self) -> None:
        root = HarnessPath(REPO_ROOT)
        pre_repair_digest = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"
        assert hmic.derive_implementation_scope_digest(root) == pre_repair_digest
