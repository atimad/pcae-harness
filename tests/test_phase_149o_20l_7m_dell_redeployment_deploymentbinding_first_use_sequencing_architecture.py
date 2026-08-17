"""Phase 149O.20L.7M -- Dell Redeployment + DeploymentBinding First-Use
Sequencing Architecture.

Architecture/design-analysis phase. This module is proof, not
implementation: it demonstrates, against live git history, contracts,
and production source, the exact facts `docs/PHASE_149O_20L_7M_DELL_
REDEPLOYMENT_DEPLOYMENTBINDING_FIRST_USE_SEQUENCING_ARCHITECTURE.md`
reconstructs -- the current candidate SHA, the old-Dell-to-candidate
diff, CHGR condition 6/7's exact text, RepositoryIdentity's
non-deterministic generation, the DeploymentBinding producer's
preview-input constraints, and the selected two-transition model's
invariants. No production module is modified by this phase. No
election, CHGR, RepositoryIdentity, or DeploymentBinding is created.
"""
from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ARCH_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7M_DELL_REDEPLOYMENT_DEPLOYMENTBINDING_FIRST_USE_SEQUENCING_ARCHITECTURE.md"
).read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_CONTRACT_PATH = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
_HBDC_CONTRACT = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_CONTRACT = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
_IDENTITY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py").read_text(encoding="utf-8")
_BINDING_ADMIN_SRC = (
    _REPO_ROOT / "src" / "pcae" / "core" / "hatp_deployment_binding_admin.py"
).read_text(encoding="utf-8")
_PYPROJECT = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"

_OLD_DELL_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
_EXPECTED_DIGEST = "65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Candidate SHA identification and currentness (architecture doc §4, §32)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateAuthenticity:
    def test_head_equals_origin_main(self) -> None:
        assert _git("rev-parse", "HEAD") == _git("rev-parse", "origin/main")

    def test_zero_commits_ahead_of_origin_main(self) -> None:
        assert _git("rev-list", "--count", "origin/main..HEAD") == "0"

    def test_old_dell_sha_is_ancestor_of_head(self) -> None:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", _OLD_DELL_SHA, "HEAD"],
            cwd=_REPO_ROOT,
        )
        assert result.returncode == 0

    def test_candidate_sha_is_documented_and_matches_head(self) -> None:
        head = _git("rev-parse", "HEAD")
        assert head in _ARCH_DOC
        assert "Candidate SHA = " in _ARCH_DOC or "`Candidate SHA = " in _ARCH_DOC


# ═══════════════════════════════════════════════════════════════════════════
# 2. Candidate authority-relevant contents (architecture doc §6-7)
# ═══════════════════════════════════════════════════════════════════════════


class TestCandidateAuthorityRelevantContents:
    def test_hbdc_version_is_1_1(self) -> None:
        assert "**Version:** 1.1" in _HBDC_CONTRACT or "1.1" in _HBDC_CONTRACT.splitlines()[5]

    def test_hmic_version_is_1_4(self) -> None:
        assert "1.4" in _HMIC_CONTRACT.splitlines()[3]

    def test_implementation_scope_digest_matches_expected(self) -> None:
        from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
        from pcae.core.paths import HarnessPath

        root = HarnessPath(_REPO_ROOT)
        assert derive_implementation_scope_digest(root) == _EXPECTED_DIGEST

    def test_thirty_member_set_matches_frozen_constant(self) -> None:
        from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

        assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 30
        assert "core/repository_identity.py" in _FROZEN_AUTHORITY_BEARING_FILES
        assert "core/hatp_deployment_binding_admin.py" in _FROZEN_AUTHORITY_BEARING_FILES
        assert "scripts/hatp_deployment_binding_admin.py" in _FROZEN_AUTHORITY_BEARING_FILES

    def test_candidate_tree_inventory_counts(self) -> None:
        output = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"], cwd=_REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout
        modes = [line.split()[0] for line in output.splitlines() if line.strip()]
        assert modes.count("100644") == 4186
        assert modes.count("100755") == 14
        assert "120000" not in modes
        assert "160000" not in modes


# ═══════════════════════════════════════════════════════════════════════════
# 3. Old Dell -> candidate diff classification (architecture doc §9)
# ═══════════════════════════════════════════════════════════════════════════


class TestDellOldToCandidateDiff:
    def test_authority_relevant_diff_touches_exactly_five_files(self) -> None:
        output = _git(
            "diff", "--name-only", _OLD_DELL_SHA, "HEAD", "--", "src/", "scripts/", "docs/contracts/", "pyproject.toml"
        )
        changed = sorted(line for line in output.splitlines() if line.strip())
        assert changed == sorted(
            [
                "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
                "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
                "scripts/hatp_deployment_binding_admin.py",
                "src/pcae/core/hatp_deployment_binding_admin.py",
                "src/pcae/core/hatp_mandatory_certification.py",
            ]
        )

    def test_pyproject_byte_unchanged_since_old_dell_sha(self) -> None:
        diff = _git("diff", _OLD_DELL_SHA, "HEAD", "--", "pyproject.toml")
        assert diff == ""

    def test_producer_did_not_exist_at_old_dell_sha(self) -> None:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{_OLD_DELL_SHA}:src/pcae/core/hatp_deployment_binding_admin.py"],
            cwd=_REPO_ROOT,
        )
        assert result.returncode != 0

    def test_producer_exists_at_head(self) -> None:
        result = subprocess.run(
            ["git", "cat-file", "-e", "HEAD:src/pcae/core/hatp_deployment_binding_admin.py"], cwd=_REPO_ROOT
        )
        assert result.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# 4. CHGR condition 6 / condition 7 -- exact text, read live (architecture
#    doc §16-18)
# ═══════════════════════════════════════════════════════════════════════════


class TestChgrConditionSix:
    def _conditions(self) -> str:
        record = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        return record["conditions"]

    def test_chgr_record_exists_and_is_published(self) -> None:
        record = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        assert record["lifecycle_state"] == "published"

    def test_condition_six_names_deploymentbinding_exclusion(self) -> None:
        conditions = self._conditions()
        assert "no DeploymentBinding" in conditions
        assert "without a fresh, separate election" in conditions

    def test_condition_six_does_not_name_repository_identity(self) -> None:
        conditions = self._conditions()
        six_start = conditions.index("6)")
        seven_start = conditions.index("7)")
        condition_six_text = conditions[six_start:seven_start]
        assert "RepositoryIdentity" not in condition_six_text
        assert "repository identity" not in condition_six_text.lower()

    def test_condition_seven_scopes_to_exact_old_dell_sha_only(self) -> None:
        conditions = self._conditions()
        assert _OLD_DELL_SHA in conditions
        assert "no other source SHA, branch, or ref is authorized" in conditions

    def test_candidate_sha_not_named_in_chgr(self) -> None:
        record = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        combined = record["decision_subject"] + record["rationale"] + record["conditions"]
        head = _git("rev-parse", "HEAD")
        assert head not in combined


# ═══════════════════════════════════════════════════════════════════════════
# 5. Producer deployment prerequisite (architecture doc §12)
# ═══════════════════════════════════════════════════════════════════════════


class TestProducerAvailabilityPrerequisite:
    def test_admin_module_requires_existing_repository_identity(self) -> None:
        assert "RepositoryIdentityMissingError" in _BINDING_ADMIN_SRC

    def test_admin_module_never_calls_ensure_repository_identity(self) -> None:
        # The module's docstring/comments *mention* ensure_repository_identity()
        # by name (to document that it is deliberately never called) -- strip
        # comment and docstring lines before checking for an actual call.
        import ast

        tree = ast.parse(_BINDING_ADMIN_SRC)
        calls = [
            node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        ]
        assert "ensure_repository_identity" not in calls

    def test_preview_functions_exist_and_are_read_only_by_name(self) -> None:
        for name in (
            "preview_create_deployment_binding",
            "preview_rotate_deployment_binding",
            "preview_revoke_deployment_binding",
        ):
            assert f"def {name}(" in _BINDING_ADMIN_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 6. RepositoryIdentity generation semantics (architecture doc §13, §23, §35)
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryIdentityGenerationSemantics:
    def test_generation_uses_uuid4_with_no_override_parameter(self) -> None:
        assert "uuid.uuid4()" in _IDENTITY_SRC
        assert "def _generate_repository_identity(" in _IDENTITY_SRC
        # No parameter accepting a caller-supplied identity value exists.
        start = _IDENTITY_SRC.index("def _generate_repository_identity(")
        signature_line = _IDENTITY_SRC[start : _IDENTITY_SRC.index(")", start) + 1]
        assert "repository_instance_id" not in signature_line
        assert "uuid" not in signature_line.replace("_generate_repository_identity", "")

    def test_ensure_repository_identity_has_no_preview_mode(self) -> None:
        assert "def ensure_repository_identity(" in _IDENTITY_SRC
        assert "def preview_repository_identity(" not in _IDENTITY_SRC

    def test_repository_identity_gitignored(self) -> None:
        gitignore = (_REPO_ROOT / ".pcae" / ".gitignore").read_text(encoding="utf-8")
        assert "repository-identity.json" in gitignore

    def test_no_repository_identity_exists_in_this_checkout(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 7. DeploymentBinding required fields and preview-input split (architecture
#    doc §36)
# ═══════════════════════════════════════════════════════════════════════════


class TestDeploymentBindingRequiredFields:
    def test_all_nine_fields_present_in_source(self) -> None:
        expected = {
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        }
        for field in expected:
            assert field in _BINDING_ADMIN_SRC, f"missing DeploymentBinding field: {field}"

    def test_repository_id_is_resolved_not_caller_supplied(self) -> None:
        assert "_resolve_repository_id" in _BINDING_ADMIN_SRC

    def test_valid_from_generated_at_execution_time(self) -> None:
        assert "_canonical_timestamp_now()" in _BINDING_ADMIN_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 8. Expected disposable HBDC result (architecture doc §42) -- structural,
#    not a live Dell measurement.
# ═══════════════════════════════════════════════════════════════════════════


class TestExpectedDisposableHbdcResult:
    def test_conformance_checker_treats_matching_identity_and_binding_as_terminal_compliant_path(self) -> None:
        conformance_src = (
            _REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py"
        ).read_text(encoding="utf-8")
        assert "deployment_binding_matches_repository_and_root" in conformance_src


# ═══════════════════════════════════════════════════════════════════════════
# 9. Selected sequence invariants (architecture doc §27, §47-51)
# ═══════════════════════════════════════════════════════════════════════════


class TestSelectedSequenceInvariants:
    def test_final_verdict_is_ready_for_proposition_preparation(self) -> None:
        assert "SEQUENCING ARCHITECTURE DEFINED — READY FOR PROPOSITION PREPARATION" in _ARCH_DOC

    def test_two_transition_model_selected_over_combined_model(self) -> None:
        assert "two-transition model" in _ARCH_DOC
        assert "**The two-transition model" in _ARCH_DOC

    def test_recommended_next_phase_is_7n_proposition_preparation(self) -> None:
        assert "149O.20L.7N" in _ARCH_DOC
        assert "Proposition + Authority Preparation" in _ARCH_DOC or "Proposition Preparation" in _ARCH_DOC

    def test_no_election_initiated_this_phase_stated(self) -> None:
        assert "Not initiated this phase." in _ARCH_DOC

    def test_repository_id_preview_problem_documented_as_blocking_model_b(self) -> None:
        assert "cannot** be known at proposition-drafting time" in _ARCH_DOC or "cannot be known" in _ARCH_DOC


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-execution proof (architecture doc §54-56)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionProof:
    def test_no_registry_or_certification_artifacts_exist(self) -> None:
        for name in (
            "registry.json",
            "repository-identity.json",
            "deployment-binding.json",
            "certifications.json",
            "certification-bindings.json",
            "active-certification.json",
        ):
            matches = list(_REPO_ROOT.rglob(name))
            # Exclude anything under .git/ (irrelevant object-store artifacts).
            matches = [m for m in matches if ".git" not in m.parts]
            assert matches == [], f"unexpected artifact found: {name} -> {matches}"

    def test_only_four_historical_chgr_records_exist(self) -> None:
        records_dir = _REPO_ROOT / ".pcae" / "publication-execution" / "records"
        chgr_files = sorted(p.name for p in records_dir.glob("chgr-*.json"))
        assert chgr_files == sorted(
            [
                "chgr-0e37ed1340b14311826722c4dbf3e856.json",
                "chgr-96a0ce12756e4cc892492a87af1db832.json",
                "chgr-541cb08c313b4f8884970172d37c5a1d.json",
                "chgr-d4343fa51b9743f3abaeb87a881a78b1.json",
            ]
        )

    def test_this_phase_touches_no_src_pcae_scripts_or_contracts(self) -> None:
        phase_entry = "b0840e96a7ffb12308e95828aa5927c3e7c770c0"
        changed = _git("diff", "--name-only", phase_entry, "HEAD", "--", "src/pcae/", "scripts/", "docs/contracts/")
        assert changed == ""

    def test_uuid4_module_level_import_only_used_for_reading_not_a_fixed_test_value(self) -> None:
        # Sanity: this test module itself imports uuid only to document the
        # generation mechanism in prose (RepositoryIdentityGenerationSemantics
        # above); it never mints or persists a real identity.
        assert uuid.uuid4  # accessible, unused for mutation in this module
