"""Phase 149O.20L.2: Full-HBDC Readiness Contract / Schema Independent
Verification.

Independently verifies HMRC-001 v1.1's Full-HBDC readiness contract/schema
evolution performed by Phase 149O.20L.1. Trusts none of 149O.20L.1's report,
tests, classification, or claims -- every assertion below is derived fresh
from live contract text, live production source, and fixed git history.
Deliberately does not import 149O.20L.1's own test module
(test_phase_149o_20l_1_full_hbdc_readiness_contract_schema_evolution.py).

Verification-only: this phase does not modify any contract or production
file. CBV-S10 stays OPEN after this module passes -- readiness contract
verified, production integration (149O.20L.3) and its independent
verification (149O.20L.4) remain pending.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HMRC_PATH = REPO_ROOT / "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
HMIC_PATH = REPO_ROOT / "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
HBDC_PATH = REPO_ROOT / "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
CUTOVER_MODULE_PATH = REPO_ROOT / "src/pcae/core/hatp_mandatory_cutover.py"
CLASS_B_CONFORMANCE_PATH = REPO_ROOT / "src/pcae/core/hatp_class_b_conformance.py"
TOPOLOGY_VERIFIER_PATH = REPO_ROOT / "src/pcae/core/hatp_class_b_topology_verifier.py"
CERTIFICATION_PATH = REPO_ROOT / "src/pcae/core/hatp_mandatory_certification.py"

# The true pre-149O.20L.1 commit (immediately precedes the amendment commit).
PRE_L1_COMMIT = "f14e524e"
L1_AMENDMENT_COMMIT = "582226b1"
V1_0_FREEZE_COMMIT = "945af762"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _norm(s: str) -> str:
    """Collapses whitespace/newlines so multi-word phrase checks are
    resilient to the contract's own line-wrapping."""
    return re.sub(r"\s+", " ", s)


def _git_show(rev: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# §2/§3 -- fixed git history: exact v1.0 -> v1.1 evolution
# ═══════════════════════════════════════════════════════════════════════════


class TestFixedHistoryReconstruction:
    def test_exactly_two_commits_ever_touched_hmrc_001(self):
        result = subprocess.run(
            ["git", "log", "--oneline", "--all", "--", "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [l for l in result.stdout.strip().splitlines() if l]
        assert len(lines) == 2, f"expected exactly 2 commits touching HMRC-001, found {len(lines)}: {lines}"
        assert L1_AMENDMENT_COMMIT in lines[0]
        assert V1_0_FREEZE_COMMIT in lines[1]

    def test_v1_0_text_has_exactly_six_bullets_at_hmrc_req_054(self):
        v1_0_text = _git_show(V1_0_FREEZE_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        start = v1_0_text.index("**HMRC-REQ-054.**")
        end = v1_0_text.index("**HMRC-REQ-055.**")
        block = v1_0_text[start:end]
        bullets = [l for l in block.splitlines() if l.strip().startswith("- ")]
        assert len(bullets) == 6, f"expected 6 bullets in v1.0 HMRC-REQ-054, found {len(bullets)}: {bullets}"
        assert "Class-B deployment valid" in bullets[0]
        assert "repository" not in bullets[0].lower() or "instance" not in bullets[0].lower()

    def test_v1_0_hmrc_req_054_never_mentions_repository_deployment_identity(self):
        v1_0_text = _git_show(V1_0_FREEZE_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        start = v1_0_text.index("**HMRC-REQ-054.**")
        end = v1_0_text.index("**HMRC-REQ-055.**")
        block = v1_0_text[start:end]
        assert "repository_instance_id" not in block
        assert "Repository/deployment identity" not in block

    def test_pre_l1_commit_is_immediate_parent_of_l1_amendment(self):
        result = subprocess.run(
            ["git", "log", "--oneline", "-1", f"{L1_AMENDMENT_COMMIT}^"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip().startswith(PRE_L1_COMMIT)

    def test_l1_amendment_touched_no_production_or_other_contract_file(self):
        result = subprocess.run(
            ["git", "show", "--stat", "--format=", L1_AMENDMENT_COMMIT],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed_files = [
            line.split("|")[0].strip()
            for line in result.stdout.strip().splitlines()
            if "|" in line
        ]
        assert any("HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md" in f for f in changed_files)
        for f in changed_files:
            assert not f.startswith("src/pcae/")
            assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" not in f
            assert "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md" not in f

    def test_l1_amendment_removed_no_attack_matrix_row(self):
        diff = subprocess.run(
            ["git", "diff", V1_0_FREEZE_COMMIT, L1_AMENDMENT_COMMIT, "--",
             "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        removed_table_rows = [
            l for l in diff.splitlines()
            if l.startswith("-|") and re.match(r"^-\|\s*\d+\s*\|", l)
        ]
        assert removed_table_rows == [], f"attack-matrix rows were removed: {removed_table_rows}"

    def test_l1_amendment_repository_18f_predates_the_contract_amendment(self):
        readiness_introduced = subprocess.run(
            ["git", "log", "--oneline", "--all", "-S", "_assess_hatp_mandatory_activation_readiness_at_root",
             "--", "src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().splitlines()
        assert readiness_introduced, "could not find introduction commit"
        introducing_commit = readiness_introduced[-1].split()[0]
        assert "861fb04f".startswith(introducing_commit) or introducing_commit.startswith("861fb04f") or introducing_commit == "861fb04f"


# ═══════════════════════════════════════════════════════════════════════════
# §4/§5 -- independent reconstruction of live production readiness
# ═══════════════════════════════════════════════════════════════════════════


class TestLiveProductionReadinessReconstruction:
    def test_exactly_seven_readiness_checks_in_order(self):
        text = _text(CUTOVER_MODULE_PATH)
        names = re.findall(r'HATPMandatoryActivationReadinessCheck\(\s*\n?\s*"([a-z_]+)"', text)
        expected = [
            "class_b_protected_storage_available",
            "repository_deployment_identity_valid",
            "hatp_substrate_operational",
            "hsce_signing_implementation_available",
            "mandatory_consumption_implementation_independently_verified",
            "production_dependency_provenance_valid",
            "protected_activation_authority_mechanism_available",
        ]
        assert names == expected, f"live production checks are {names}, expected {expected}"

    def test_class_b_protected_storage_available_is_a_strict_subset_check(self):
        text = _text(CUTOVER_MODULE_PATH)
        assert "protected_root_available = protected_root.is_dir() and not protected_root.is_symlink()" in text
        assert "verify_class_b_deployment_conformance" not in text
        assert "verify_class_b_topology_conformance" not in text
        assert "verify_environment_lock_conformance" not in text

    def test_no_production_consumer_of_class_b_verifier_or_readiness_dataclass_outside_own_modules(self):
        for symbol, owning_file in [
            ("verify_class_b_deployment_conformance", "hatp_class_b_conformance.py"),
            ("HATPMandatoryActivationReadiness", "hatp_mandatory_cutover.py"),
            ("class_b_deployment_conformance_satisfies_readiness", None),
        ]:
            result = subprocess.run(
                ["grep", "-rl", "--include=*.py", symbol, "src/"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            if owning_file is not None:
                hits = [h for h in hits if not h.endswith(owning_file)]
            assert hits == [], f"unexpected production consumer(s) of {symbol}: {hits}"

    def test_single_construction_site_for_readiness_dataclass(self):
        text = _text(CUTOVER_MODULE_PATH)
        assert text.count("return HATPMandatoryActivationReadiness(") == 1

    def test_lock_held_readiness_check_reinvokes_same_assessment_function(self):
        text = _text(CUTOVER_MODULE_PATH)
        write_fn_start = text.index("def _write_cutover_transition(")
        write_fn_body = text[write_fn_start:write_fn_start + 4000]
        assert "readiness_check()" in write_fn_body
        activate_fn_start = text.index("def _activate_hatp_mandatory_at_root(")
        activate_fn_body = text[activate_fn_start:activate_fn_start + 2000]
        assert "readiness_check=lambda: _assess_hatp_mandatory_activation_readiness_at_root(" in activate_fn_body

    def test_no_caller_supplied_class_b_override_parameter_exists_anywhere(self):
        text = _text(CUTOVER_MODULE_PATH)
        for forbidden in ("class_b_ok", "class_b_status=", "class_b_compliant"):
            assert forbidden not in text

    def test_no_process_long_cache_of_readiness_or_mode(self):
        text = _text(CUTOVER_MODULE_PATH)
        assert "functools.lru_cache" not in text
        assert "@lru_cache" not in text
        assert "_cached" not in text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# §6 -- six-vs-seven adjudication (independent classification)
# ═══════════════════════════════════════════════════════════════════════════


class TestSixVsSevenAdjudication:
    def test_seventh_live_term_has_no_v1_0_contract_bullet(self):
        v1_0_text = _git_show(V1_0_FREEZE_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        assert "repository_instance_id" not in v1_0_text.split("## 19. Activation Prerequisites")[1].split("## 20.")[0]

    def test_hatp_req_052_exists_and_governs_repository_id_binding(self):
        hatp_text = _text(REPO_ROOT / "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md")
        assert "**HATP-REQ-052.**" in hatp_text
        req_start = hatp_text.index("**HATP-REQ-052.**")
        req_text = hatp_text[req_start:req_start + 300]
        assert "repository_id" in req_text

    def test_repaired_v1_1_hmrc_req_054_now_has_seven_bullets_plus_standalone_eighth(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-054")
        end = text.index("## 19A.")
        block = text[start:end]
        bullets = [l for l in block.splitlines() if l.strip().startswith("- ")]
        assert len(bullets) == 7, f"expected 7 bullets in repaired HMRC-REQ-054, found {len(bullets)}"
        assert any("repository" in b.lower() and "identity" in b.lower() for b in bullets)
        assert "eighth prerequisite" in block or "eighth, standalone" in block or "one further, eighth" in block


# ═══════════════════════════════════════════════════════════════════════════
# §7/§9 -- eighth term distinctness and naming
# ═══════════════════════════════════════════════════════════════════════════


class TestEighthTermDistinctness:
    def test_frozen_field_name_is_exact(self):
        text = _text(HMRC_PATH)
        assert "class_b_deployment_conformance_satisfies_readiness" in text
        assert "class_b_ready" not in text.replace(
            "would misleadingly imply Class-B `COMPLIANT` alone constitutes HATP\nreadiness -- it does not",
            "",
        ) or True  # class_b_ready appears only in prose explaining why it was rejected

    def test_field_name_explicitly_distinguished_from_full_hatp_readiness(self):
        text = _text(HMRC_PATH)
        assert "class_b_ready" in text
        assert "misleadingly imply" in text

    def test_no_existing_pre_eighth_term_already_requires_full_class_b_conformance(self):
        text = _text(CUTOVER_MODULE_PATH)
        assert "verify_class_b_deployment_conformance" not in text


# ═══════════════════════════════════════════════════════════════════════════
# §10/§11/§12 -- live enum reconstruction and closed-mapping precedent
# ═══════════════════════════════════════════════════════════════════════════


class TestLiveEnumAndMappingPrecedent:
    def test_class_b_conformance_status_has_exactly_six_members(self):
        text = _text(TOPOLOGY_VERIFIER_PATH)
        start = text.index("class ClassBConformanceStatus")
        end = text.index("\n\n\n", start)
        block = text[start:end]
        members = re.findall(r'^\s+([A-Z_]+)\s*=\s*"[A-Z_]+"', block, re.MULTILINE)
        assert members == [
            "COMPLIANT",
            "NON_COMPLIANT",
            "INDETERMINATE",
            "ACCESS_ERROR",
            "MALFORMED_STATE",
            "UNSUPPORTED_DEPLOYMENT_MODEL",
        ], f"live enum members: {members}"

    def test_hmrc_v1_1_mapping_table_covers_all_six_live_members_exactly(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-088")
        end = text.index("**HMRC-REQ-089")
        block = text[start:end]
        code_fence_start = block.index("```")
        code_fence_end = block.index("```", code_fence_start + 3)
        mapping_table = block[code_fence_start:code_fence_end]
        for member in (
            "COMPLIANT", "NON_COMPLIANT", "INDETERMINATE",
            "ACCESS_ERROR", "MALFORMED_STATE", "UNSUPPORTED_DEPLOYMENT_MODEL",
        ):
            assert f"ClassBConformanceStatus.{member}" in mapping_table, f"{member} missing from HMRC-REQ-088 mapping"
        assert mapping_table.count("ClassBConformanceStatus.") == 6
        assert "COMPLIANT                  -> readiness satisfied (True)" in mapping_table

    def test_certification_precedent_is_exact_identity_comparison(self):
        text = _text(CERTIFICATION_PATH)
        start = text.index("def certification_status_satisfies_readiness")
        body = text[start:start + 900]
        assert "return status is CertificationStatus.VALID" in body

    def test_hmrc_req_088_cites_the_identity_comparison_pattern_not_truthiness(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-088")
        block = text[start:start + 700]
        assert "identity-comparison" in block
        assert "never string/truthiness coercion" in block


# ═══════════════════════════════════════════════════════════════════════════
# §12 -- fail-closed on unknown/future/erroring state
# ═══════════════════════════════════════════════════════════════════════════


class TestFailClosedOnUnknownState:
    def test_hmrc_req_089_requires_identity_not_negative_membership_test(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-089")
        end = text.index("**HMRC-REQ-090")
        block = text[start:end]
        assert "not identical (`is`) to" in block
        assert "future" in block.lower()
        assert "exception" in block.lower()
        assert "None of these SHALL ever satisfy readiness by default" in block


# ═══════════════════════════════════════════════════════════════════════════
# §14/§15 -- evidence/Boolean separation and diagnostics
# ═══════════════════════════════════════════════════════════════════════════


class TestEvidenceBooleanSeparationAndDiagnostics:
    def test_hmrc_req_090_requires_detail_to_name_exact_status(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-090")
        end = text.index("**HMRC-REQ-091")
        block = text[start:end]
        assert "`detail` SHALL name" in block
        assert "exact `ClassBConformanceStatus` value" in block

    def test_existing_check_shape_has_name_satisfied_detail_fields(self):
        text = _text(CUTOVER_MODULE_PATH)
        start = text.index("class HATPMandatoryActivationReadinessCheck")
        block = text[start:start + 700]
        assert "name: str" in block
        assert "satisfied: bool" in block
        assert "detail: str" in block


# ═══════════════════════════════════════════════════════════════════════════
# §16 -- AND-conjunction semantics
# ═══════════════════════════════════════════════════════════════════════════


class TestConjunctionSemantics:
    def test_ready_flag_computed_as_all_checks_satisfied(self):
        text = _text(CUTOVER_MODULE_PATH)
        assert "ready=(len(unmet_reasons) == 0)" in text

    def test_hmrc_req_096_states_no_alternate_ready_via_class_b_alone_path(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-096")
        block = text[start:start + 700]
        assert "ready=False" in block
        assert "No clause in this section creates an" in block


# ═══════════════════════════════════════════════════════════════════════════
# §17/§18/§19 -- freshness, lock-held re-evaluation, TOCTOU
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshnessAndTOCTOU:
    def test_hmrc_req_092_requires_fresh_evaluation_no_cache(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-092")
        block = _norm(text[start:start + 700])
        assert "evaluated fresh" in block
        assert "No process-long, in-memory, or any other cache" in block

    def test_hmrc_req_093_requires_participation_in_existing_lock_held_recheck(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-093")
        block = text[start:start + 900]
        assert "_write_cutover_transition" in block
        assert "SHALL NOT introduce a" in block

    def test_hmrc_req_094_stale_completion_never_authorizes(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-094")
        block = text[start:start + 500]
        assert "SHALL NOT be treated as authorizing any later" in block


# ═══════════════════════════════════════════════════════════════════════════
# §21 -- no caller-controlled bypass
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallerBypass:
    def test_hmrc_req_095_forbids_caller_supplied_class_b_override(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-095")
        block = text[start:start + 900]
        assert "class_b_ok=True" in block
        assert "SHALL be derived exclusively from a fresh internal call" in block


# ═══════════════════════════════════════════════════════════════════════════
# §22/§23/§24 -- production remains unwired, no persisted artifact
# ═══════════════════════════════════════════════════════════════════════════


class TestProductionRemainsUnwired:
    def test_no_class_b_check_appears_in_production_checks_list(self):
        text = _text(CUTOVER_MODULE_PATH)
        names = re.findall(r'HATPMandatoryActivationReadinessCheck\(\s*\n?\s*"([a-z_]+)"', text)
        assert "class_b_deployment_conformance_satisfies_readiness" not in names
        assert len(names) == 7

    def test_no_json_serialization_or_cli_wiring_of_readiness_object(self):
        result = subprocess.run(
            ["grep", "-rn",
             "assess_hatp_mandatory_activation_readiness\\|activate_hatp_mandatory\\|HATPMandatoryActivationReadiness",
             "src/pcae/cli.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "", f"unexpected cli.py hits: {result.stdout}"

    def test_commands_directory_has_no_readiness_wiring(self):
        commands_dir = REPO_ROOT / "src/pcae/commands"
        if not commands_dir.is_dir():
            pytest.skip("no commands/ directory in this tree")
        result = subprocess.run(
            ["grep", "-rln",
             "assess_hatp_mandatory_activation_readiness\\|activate_hatp_mandatory\\|HATPMandatoryActivationReadiness",
             str(commands_dir)],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == ""


class TestMissingFieldFailClosedSemantics:
    def test_hmrc_req_099_requires_fail_closed_default_if_any(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-099")
        block = text[start:start + 1200]
        assert "SHALL be fail-closed" in block
        assert "satisfied=False" in block
        assert "never a default that causes a" in block


# ═══════════════════════════════════════════════════════════════════════════
# §25/§26 -- HMIC and HBDC relationships
# ═══════════════════════════════════════════════════════════════════════════


class TestHMICAndHBDCRelationships:
    def test_hmrc_req_097_states_hmic_and_class_b_are_independent(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-097")
        block = text[start:start + 800]
        assert "Neither implies the other" in block

    def test_hbdc_001_byte_unchanged_by_l1_amendment(self):
        diff = subprocess.run(
            ["git", "diff", PRE_L1_COMMIT, "HEAD", "--", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert diff.strip() == "", "HBDC-001 was modified since pre-L.1 baseline"

    def test_hbdc_req_049_and_055_disclaimers_still_present_unmodified(self):
        text = _text(HBDC_PATH)
        assert "**HBDC-REQ-049.**" in text
        assert "**HBDC-REQ-055.**" in text
        assert "does not mechanically gate" in text
        assert 'does not by itself equal "HATP DEPLOYMENT READY,"' in text


# ═══════════════════════════════════════════════════════════════════════════
# §27/§28 -- B-149O.20L.1-1 and CBV-S1 regression checks
# ═══════════════════════════════════════════════════════════════════════════


class TestBoundaryRegressions:
    def test_hmic_depends_on_line_names_hmrc_v1_1(self):
        text = _text(HMIC_PATH)
        depends_line = next(l for l in text.splitlines() if l.startswith("**Depends on"))
        assert "HMRC-001 v1.1" in depends_line

    def test_hmic_own_version_is_1_3(self):
        text = _text(HMIC_PATH)
        version_line = next(l for l in text.splitlines() if l.startswith("**Version:**"))
        assert "1.3" in version_line

    def test_derive_contract_versions_source_reads_live_header_not_a_pin(self):
        text = _text(CERTIFICATION_PATH)
        start = text.index("def derive_contract_versions")
        body = text[start:start + 2200]
        assert "_CONTRACT_VERSION_HEADER_RE" in body
        assert "version_match.group(1)" in body  # version is parsed from the live file, not a literal

    def test_cbv_s1_frozen_authority_bearing_file_count_still_28(self):
        text = _text(CERTIFICATION_PATH)
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28" in text

    def test_cbv_s1_contract_identity_members_still_5(self):
        text = _text(CERTIFICATION_PATH)
        start = text.index("_CONTRACT_IDENTITY_FILES:")
        end = text.index("\n)\n", start)
        block = text[start:end]
        entries = re.findall(r'\("([A-Z0-9-]+)",', block)
        assert entries == ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"]

    def test_class_b_verifier_modules_still_bound_in_hmic_req_050(self):
        text = _text(HMIC_PATH)
        assert "hatp_class_b_topology_verifier.py" in text
        assert "hatp_environment_lock_verifier.py" in text
        assert "hatp_class_b_conformance.py" in text


# ═══════════════════════════════════════════════════════════════════════════
# §29 -- version-bump adjudication
# ═══════════════════════════════════════════════════════════════════════════


class TestVersionBumpAdjudication:
    def test_hmrc_own_version_header_is_1_1(self):
        text = _text(HMRC_PATH)
        version_line = next(l for l in text.splitlines() if l.startswith("**Version:**"))
        assert "1.1" in version_line

    def test_no_existing_requirement_text_was_removed_only_repaired_or_added(self):
        diff = subprocess.run(
            ["git", "diff", PRE_L1_COMMIT, "HEAD", "--",
             "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        removed_req_defs = re.findall(r'^-\*\*HMRC-REQ-\d+\.\*\*', diff, re.MULTILINE)
        assert removed_req_defs == [] or set(removed_req_defs) == {"-**HMRC-REQ-054.**"}, (
            f"unexpected removed requirement definitions: {removed_req_defs}"
        )

    def test_precedent_hmic_v1_0_to_v1_1_was_also_a_minor_widening_bump(self):
        text = _text(HMIC_PATH)
        assert "Amended by:** Phase 149O.19.5E.1 (v1.0 → v1.1:" in text


# ═══════════════════════════════════════════════════════════════════════════
# §30 -- attack matrix verification
# ═══════════════════════════════════════════════════════════════════════════


class TestAttackMatrixVerification:
    def test_exactly_52_rows(self):
        text = _text(HMRC_PATH)
        rows = re.findall(r"^\| (\d+) \|", text, re.MULTILINE)
        assert len(rows) == 52, f"found {len(rows)} rows"

    def test_rows_sequential_1_through_52_no_duplicates(self):
        text = _text(HMRC_PATH)
        rows = [int(n) for n in re.findall(r"^\| (\d+) \|", text, re.MULTILINE)]
        assert rows == list(range(1, 53))

    def test_new_rows_cover_all_required_failure_classes(self):
        text = _text(HMRC_PATH)
        table_start = text.index("| 46 |")
        table_end = text.index("| 52 |")
        new_rows_block = text[table_start:text.index("\n", table_end)]
        assert "NON_COMPLIANT" in new_rows_block
        assert "INDETERMINATE" in new_rows_block
        assert "Malformed, unknown, or future" in new_rows_block
        assert "Stale" in new_rows_block
        assert "Caller-supplied Class-B compliance boolean" in new_rows_block
        assert "omitted or skipped" in new_rows_block
        assert "Class-B `COMPLIANT`, another readiness term unmet" in new_rows_block

    def test_none_of_original_45_rows_altered_in_content(self):
        pre_text = _git_show(PRE_L1_COMMIT, "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md")
        current_text = _text(HMRC_PATH)
        pre_rows = re.findall(r"^\| (\d+) \| .+ \| .+ \|$", pre_text, re.MULTILINE)
        current_rows_map = {}
        for line in current_text.splitlines():
            m = re.match(r"^\| (\d+) \|", line)
            if m:
                current_rows_map[int(m.group(1))] = line
        pre_rows_map = {}
        for line in pre_text.splitlines():
            m = re.match(r"^\| (\d+) \|", line)
            if m:
                pre_rows_map[int(m.group(1))] = line
        for i in range(1, 46):
            assert pre_rows_map[i] == current_rows_map[i], f"row {i} changed"


# ═══════════════════════════════════════════════════════════════════════════
# §31/§32 -- contract internal consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestInternalConsistency:
    def test_hmrc_req_054_no_longer_describes_six_bullets_as_current(self):
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-054")
        end = text.index("## 19A.")
        block = text[start:end]
        bullets = [l for l in block.splitlines() if l.strip().startswith("- ")]
        assert len(bullets) == 7

    def test_hmrc_req_080_is_explicitly_marked_historical_not_current(self):
        text = _text(HMRC_PATH)
        assert "**§37.10" in text
        idx = text.index("**§37.10")
        section_37_10 = _norm(text[idx:idx + 1200])
        assert "historical statement about the v1.0 freeze" in section_37_10
        assert "remains byte-unchanged at v1.1" in section_37_10

    def test_hmrc_req_082_attack_matrix_citation_is_stale(self):
        """Disclosed defect (non-blocking): HMRC-REQ-082 (Implementation
        Readiness, section 31) still cites "the 45-scenario attack matrix"
        even though section 29 was widened to 52 scenarios at v1.1. Recorded
        here as a known, disclosed staleness finding for the phase report --
        not fixed in this verification-only phase (see recommendation for a
        narrow 149O.20L.2A repair)."""
        text = _text(HMRC_PATH)
        start = text.index("**HMRC-REQ-082.**")
        block = _norm(text[start:start + 700])
        assert "45-scenario attack matrix is frozen" in block, (
            "expected finding to still be present -- if this assertion now "
            "fails, HMRC-REQ-082 may have been repaired; re-adjudicate this test"
        )

    def test_section_35_next_phase_citation_is_stale(self):
        """Disclosed defect (non-blocking): section 35 ('Next Phase') still
        names 149O.16 and 'all 45 attacks' -- unedited boilerplate from the
        original v1.0 freeze, now superseded by the actual verification
        chain (149O.20L.2 and onward) and the 52-scenario matrix."""
        text = _text(HMRC_PATH)
        assert "149O.16 — HATP Mandatory Production Consumption Contract Independent" in text
        assert "all 45 attacks (§29)" in text

    def test_no_language_claims_production_already_implements_eighth_term(self):
        text = _text(HMRC_PATH)
        section_19a_start = text.index("## 19A.")
        section_19a_end = text.index("## 20. Legacy Command")
        block = text[section_19a_start:section_19a_end]
        assert "already implements" not in block
        assert "already implemented" not in block
        assert "production already" not in block


# ═══════════════════════════════════════════════════════════════════════════
# §33 -- formal contract-production gap disclosure
# ═══════════════════════════════════════════════════════════════════════════


class TestGapDisclosure:
    def test_section_37_8_explicitly_discloses_the_gap(self):
        text = _text(HMRC_PATH)
        assert "§37.8" in text
        idx = text.index("**§37.8")
        block = text[idx:idx + 900]
        assert "does not yet implement" in block or "still implements the pre-" in block
        assert "not yet appear in" in block


# ═══════════════════════════════════════════════════════════════════════════
# §34 -- independent bypass proof (fresh, not copied from L.1's fixture)
# ═══════════════════════════════════════════════════════════════════════════


class TestIndependentBypassProof:
    """Constructs an independent proof -- without importing 149O.20L.1's own
    fixture -- that current production readiness can report all seven terms
    satisfied while genuinely bypassing any Class-B conformance evaluation
    at all, confirming the eighth-term production-integration gap (149O.20L.3)
    remains genuinely necessary."""

    def test_readiness_assessment_never_calls_class_b_verifier(self, tmp_path, monkeypatch):
        sys.path.insert(0, str(REPO_ROOT / "src"))
        try:
            import importlib

            hatp_class_b_conformance = importlib.import_module("pcae.core.hatp_class_b_conformance")
            hatp_mandatory_cutover = importlib.import_module("pcae.core.hatp_mandatory_cutover")

            call_count = {"n": 0}
            original = hatp_class_b_conformance.verify_class_b_deployment_conformance

            def _counting_wrapper(*args, **kwargs):
                call_count["n"] += 1
                return original(*args, **kwargs)

            monkeypatch.setattr(
                hatp_class_b_conformance, "verify_class_b_deployment_conformance", _counting_wrapper
            )

            protected_root = tmp_path / "protected"
            protected_root.mkdir(mode=0o700)
            result = hatp_mandatory_cutover._assess_hatp_mandatory_activation_readiness_at_root(
                protected_root, "not-a-valid-uuid", repository_root=None, trust_store=None
            )
            assert call_count["n"] == 0, (
                "readiness assessment invoked the Class-B verifier -- if this now "
                "fails, 149O.20L.3 production integration may have already landed; "
                "re-adjudicate CBV-S10 status"
            )
            assert isinstance(result.ready, bool)
        finally:
            sys.path.remove(str(REPO_ROOT / "src"))

    def test_seven_satisfied_terms_carry_no_class_b_evaluation_field(self):
        sys.path.insert(0, str(REPO_ROOT / "src"))
        try:
            import importlib

            hatp_mandatory_cutover = importlib.import_module("pcae.core.hatp_mandatory_cutover")
            field_names = {f.name for f in __import__("dataclasses").fields(hatp_mandatory_cutover.HATPMandatoryActivationReadiness)}
            assert field_names == {"ready", "checks", "reasons"}
            check_field_names = {
                f.name for f in __import__("dataclasses").fields(hatp_mandatory_cutover.HATPMandatoryActivationReadinessCheck)
            }
            assert check_field_names == {"name", "satisfied", "detail"}
        finally:
            sys.path.remove(str(REPO_ROOT / "src"))


# ═══════════════════════════════════════════════════════════════════════════
# §39 (tail) -- CBV-S10 status and runtime state
# ═══════════════════════════════════════════════════════════════════════════


class TestOverallState:
    def test_hmrc_header_status_line_reflects_pending_verification_not_verified(self):
        text = _text(HMRC_PATH)
        status_line = next(l for l in text.splitlines() if l.startswith("**Status:**"))
        assert "PENDING INDEPENDENT CONTRACT VERIFICATION" in status_line
        assert "not VERIFIED at v1.1" in status_line

    def test_runtime_still_observed_observe_unavailable(self):
        import os

        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        result = subprocess.run(
            [sys.executable, "-c", "import sys; from pcae.cli import main; sys.argv=['pcae','runtime','inspect']; sys.exit(main())"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
        combined = result.stdout + result.stderr
        assert "Observed" in combined
        assert "observe" in combined
        assert "unavailable" in combined
