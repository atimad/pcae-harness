"""Phase 149O.20L.7G -- DeploymentBinding Producer Contract/Schema
Evolution and Implementation Planning.

Contract/schema-evolution and implementation-planning phase. This module
is proof, not implementation: it demonstrates, against live contract and
production source, the exact facts `docs/PHASE_149O_20L_7G_
DEPLOYMENTBINDING_PRODUCER_CONTRACT_SCHEMA_EVOLUTION_AND_IMPLEMENTATION_
PLANNING.md` freezes -- HBDC-001's new v1.1 producer requirements
(HBDC-REQ-056..070), the F3/F4 normative resolutions, the unchanged
`DeploymentBinding` schema, the CHGR condition 6 exclusion list, and the
absence of any producer implementation or DeploymentBinding creation.
This module does not treat the 7F companion test module as an oracle --
every assertion here is derived fresh from primary source.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_CONTRACT_PATH = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
_HBDC_CONTRACT = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_CONTRACT = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
_ARCH_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7G_DEPLOYMENTBINDING_PRODUCER_CONTRACT_SCHEMA_EVOLUTION_AND_IMPLEMENTATION_PLANNING.md"
).read_text(encoding="utf-8")
_BOOTSTRAP_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py").read_text(encoding="utf-8")
_IDENTITY_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py").read_text(encoding="utf-8")
_CLI_SRC = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"
_SRC_PCAE_ROOT = _REPO_ROOT / "src" / "pcae"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Contract home selection -- HBDC-001 extended in place, v1.0 -> v1.1
# ═══════════════════════════════════════════════════════════════════════════


class TestContractHomeSelection:
    def test_hbdc_version_is_1_1(self) -> None:
        assert "**Version:** 1.1" in _HBDC_CONTRACT

    def test_no_new_dbpc_style_contract_file_was_created(self) -> None:
        contracts_dir = _REPO_ROOT / "docs" / "contracts"
        names = {p.name for p in contracts_dir.iterdir()}
        assert not any("DBPC" in n.upper() or "DEPLOYMENTBINDING_PRODUCER" in n.upper() for n in names)

    def test_hbdc_001_already_bound_into_hmic_frozen_file_set(self) -> None:
        cert_src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py").read_text(
            encoding="utf-8"
        )
        assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in cert_src

    def test_hbdc_055_preexisting_requirements_unmodified_count(self) -> None:
        import re

        ids = sorted(
            {int(m) for m in re.findall(r"HBDC-REQ-(\d+)", _HBDC_CONTRACT)}
        )
        assert ids[0] == 1
        assert ids[-1] == 70
        assert ids == list(range(1, 71))


# ═══════════════════════════════════════════════════════════════════════════
# 2. New requirement text -- HBDC-REQ-056..070, each bold-defined exactly once
# ═══════════════════════════════════════════════════════════════════════════


class TestNewRequirementInventory:
    @pytest.mark.parametrize("req_id", [f"HBDC-REQ-{n:03d}" for n in range(56, 71)])
    def test_each_new_requirement_bold_defined_exactly_once(self, req_id: str) -> None:
        assert _HBDC_CONTRACT.count(f"**{req_id}.**") == 1

    @pytest.mark.parametrize("req_id", [f"HBDC-REQ-{n:03d}" for n in range(56, 71)])
    def test_each_new_requirement_appears_in_traceability_table(self, req_id: str) -> None:
        table_section = _HBDC_CONTRACT.split("## 24. Full Requirement Traceability")[1].split("## 25.")[0]
        assert req_id in table_section

    def test_writer_is_not_agent_reachable(self) -> None:
        assert "HBDC-REQ-056" in _HBDC_CONTRACT
        assert "never a subcommand of the ordinary agent-reachable `pcae` CLI" in _HBDC_CONTRACT

    def test_revocation_is_field_mutation_not_deletion(self) -> None:
        assert "SHALL NOT be deleted" in _HBDC_CONTRACT

    def test_no_history_array_required_in_trust_store(self) -> None:
        assert "the trust store retains no history of prior field values" in _HBDC_CONTRACT

    def test_cbd_9_and_cbd_10_added(self) -> None:
        assert "**CBD-9**" in _HBDC_CONTRACT
        assert "**CBD-10**" in _HBDC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 3. F3 -- DeploymentBinding / CertificationRecord cross-consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestFindingF3:
    def test_certification_record_has_no_binding_id_or_digest_field(self) -> None:
        schema_section = _HMIC_CONTRACT.split("## 11. `CertificationRecord` Schema")[1].split("## 12.")[0]
        assert "binding_id" not in schema_section
        assert "deployment_binding_digest" not in schema_section
        assert "certification_id" in schema_section

    def test_hmic_req_043_044_045_derive_read_only_exactly_as_binding_defines(self) -> None:
        binding_section = _HMIC_CONTRACT.split("## 15. Repository and Deployment Binding")[1].split("## 16.")[0]
        assert "HMIC-REQ-043" in binding_section
        assert "HMIC-REQ-044" in binding_section
        assert "HMIC-REQ-045" in binding_section
        assert "never accepted as caller input on" in binding_section
        assert "either path" in binding_section

    def test_validation_algorithm_step_7_does_not_reference_trust_store(self) -> None:
        validation_section = _HMIC_CONTRACT.split("## 31. Validation Algorithm")[1].split("## 32.")[0]
        assert "WRONG_REPOSITORY" in validation_section
        # HATPTrustStore.production() is referenced only to resolve the
        # Protected Root path (step 1); the algorithm never loads a
        # DeploymentBinding registry entry or checks its status -- this is
        # the F3-residual gap, confirmed by absence of both.
        assert "HATPTrustStore.production().root" in validation_section
        assert "load_repository_enrollment" not in validation_section
        assert "deployment_bindings" not in validation_section
        assert "binding.status" not in validation_section

    def test_f3_disposition_resolved_normatively_no_schema_change(self) -> None:
        assert "F3" in _ARCH_DOC
        assert "RESOLVED NORMATIVELY" in _ARCH_DOC
        assert "F3-residual" in _ARCH_DOC


# ═══════════════════════════════════════════════════════════════════════════
# 4. F4 -- rotation/revocation lifecycle
# ═══════════════════════════════════════════════════════════════════════════


class TestFindingF4:
    def test_status_vocabulary_is_closed_two_state(self) -> None:
        assert '_STATUS_VALUES = frozenset({"active", "revoked"})' in _BOOTSTRAP_SRC

    def test_registry_parser_rejects_duplicate_repository_id_entries(self) -> None:
        assert "duplicate conflicting deployment binding" in _BOOTSTRAP_SRC

    def test_no_no_schema_addition_for_lifecycle_states(self) -> None:
        # Confirms this phase did not add candidate/inactive/superseded/expired
        # anywhere in the production dataclass -- the schema is untouched.
        binding_block = _BOOTSTRAP_SRC.split("class DeploymentBinding:")[1].split("class ")[0]
        for forbidden in ("candidate", "inactive", "superseded", "expired"):
            assert forbidden not in binding_block

    def test_f4_disposition_resolved_normatively_implementation_pending(self) -> None:
        assert "F4" in _ARCH_DOC
        assert "RESOLVED NORMATIVELY — IMPLEMENTATION PENDING" in _ARCH_DOC


# ═══════════════════════════════════════════════════════════════════════════
# 5. Active-binding uniqueness, idempotency, atomicity (unchanged, reaffirmed)
# ═══════════════════════════════════════════════════════════════════════════


class TestUniquenessIdempotencyAtomicity:
    def test_deployment_bindings_dict_keyed_only_by_repository_id(self) -> None:
        parse_fn = _BOOTSTRAP_SRC.split("def _parse_registry_document")[1].split("def ")[0]
        assert "deployment_bindings: dict[str, DeploymentBinding] = {}" in parse_fn

    def test_idempotent_create_requirement_present(self) -> None:
        assert "HBDC-REQ-059" in _HBDC_CONTRACT
        assert "idempotent-preserve" in _HBDC_CONTRACT

    def test_atomic_write_discipline_reused_not_reinvented(self) -> None:
        assert "no new idiom SHALL be invented" in _HBDC_CONTRACT
        assert "_write_atomic" in _IDENTITY_SRC


# ═══════════════════════════════════════════════════════════════════════════
# 6. Authority evidence, RepositoryIdentity prerequisite, election preservation
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorityAndPrerequisites:
    def test_writer_requires_explicit_election_evidence(self) -> None:
        assert "HBDC-REQ-064" in _HBDC_CONTRACT
        assert "SHALL NOT accept an unverified boolean" in _HBDC_CONTRACT

    def test_repository_identity_creation_not_gated_by_new_election_requirement(self) -> None:
        assert "HBDC-REQ-068" in _HBDC_CONTRACT
        assert "HATP-REQ-048" in _HBDC_CONTRACT

    def test_amendment_does_not_itself_satisfy_any_chgr_election(self) -> None:
        assert "HBDC-REQ-069" in _HBDC_CONTRACT
        assert "does not itself satisfy" in _HBDC_CONTRACT

    def test_chgr_condition_6_verbatim_still_excludes_deploymentbinding(self) -> None:
        record = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        conditions = record["conditions"]
        assert "no DeploymentBinding" in conditions
        assert "no repository onboarding" in conditions
        assert "fresh, separate election" in conditions
        # Repository-identity creation is NOT named in the exclusion list.
        assert "repository-identity creation" not in conditions
        assert "repository identity creation" not in conditions


# ═══════════════════════════════════════════════════════════════════════════
# 7. Binding-before-certification ordering and no-cycle (re-confirmed)
# ═══════════════════════════════════════════════════════════════════════════


class TestOrderingAndNoCycle:
    def test_hmic_req_044_confirms_binding_upstream_of_certification(self) -> None:
        assert "HMIC-REQ-044" in _HMIC_CONTRACT
        binding_section = _HMIC_CONTRACT.split("## 15. Repository and Deployment Binding")[1].split("## 16.")[0]
        assert "DeploymentBinding` already define" in binding_section

    def test_hbdc_req_049_certification_not_gated_by_hbdc_compliance(self) -> None:
        assert "does not mechanically gate" in _HBDC_CONTRACT

    def test_creation_ceremony_reads_existing_binding_does_not_create_one(self) -> None:
        ceremony_section = _HMIC_CONTRACT.split("## 23. Creation Ceremony")[1].split("## 24.")[0]
        assert "repository_instance_id (read-only, §15), canonical_deployment_root" in ceremony_section
        assert "(read-only, §15)" in ceremony_section


# ═══════════════════════════════════════════════════════════════════════════
# 8. No producer implementation, no DeploymentBinding creation, no Dell mutation
# ═══════════════════════════════════════════════════════════════════════════


class TestNoImplementationNoMutation:
    def test_no_new_write_function_added_to_hatp_bootstrap(self) -> None:
        for forbidden in (
            "def create_deployment_binding",
            "def rotate_deployment_binding",
            "def revoke_deployment_binding",
            "def enroll_deployment",
            "def register_binding",
        ):
            assert forbidden not in _BOOTSTRAP_SRC

    def test_hatp_trust_store_still_has_zero_write_methods(self) -> None:
        store_block = _BOOTSTRAP_SRC.split("class HATPTrustStore:")[1]
        for forbidden in ("def create(", "def enroll(", "def revoke(", "def rotate(", "def write("):
            assert forbidden not in store_block

    def test_no_deployment_binding_admin_script_created(self) -> None:
        if _SCRIPTS_ROOT.exists():
            names = {p.name for p in _SCRIPTS_ROOT.iterdir()}
            assert "hatp_deployment_binding_admin.py" not in names

    def test_no_pcae_repository_identity_json_created_locally(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_no_cli_write_subcommand_for_deployment_binding(self) -> None:
        assert "deployment-binding-create" not in _CLI_SRC
        assert "deployment_binding_create" not in _CLI_SRC

    def test_no_src_pcae_dataclass_field_added_to_deployment_binding(self) -> None:
        binding_block = _BOOTSTRAP_SRC.split("class DeploymentBinding:")[1].split("class ")[0]
        expected_fields = {
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
        found_fields = {
            line.strip().split(":")[0].strip()
            for line in binding_block.splitlines()
            if ":" in line and not line.strip().startswith("#")
        }
        assert found_fields == expected_fields


# ═══════════════════════════════════════════════════════════════════════════
# 9. Timestamp grammar finding (new this phase)
# ═══════════════════════════════════════════════════════════════════════════


class TestTimestampGrammarFinding:
    def test_hatp_bootstrap_timestamp_parser_is_permissive(self) -> None:
        parse_fn = _BOOTSTRAP_SRC.split("def _parse_iso_timestamp")[1].split("\n\n\n")[0]
        assert "datetime.fromisoformat" in parse_fn

    def test_strict_pattern_exists_elsewhere_and_is_not_yet_reused_here(self) -> None:
        cutover_src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py").read_text(
            encoding="utf-8"
        )
        assert "_TIMESTAMP_PATTERN" in cutover_src
        assert "_TIMESTAMP_PATTERN" not in _BOOTSTRAP_SRC

    def test_hbdc_req_067_binds_future_writer_output_to_strict_grammar(self) -> None:
        assert "HBDC-REQ-067" in _HBDC_CONTRACT
        assert r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$" in _HBDC_CONTRACT


# ═══════════════════════════════════════════════════════════════════════════
# 10. Verdict and no src/pcae mutation proof
# ═══════════════════════════════════════════════════════════════════════════


class TestVerdictAndScope:
    def test_final_verdict_is_contract_evolution_complete(self) -> None:
        assert "CONTRACT/SCHEMA EVOLUTION COMPLETE — READY FOR INDEPENDENT VERIFICATION" in _ARCH_DOC

    def test_recommended_next_phase_is_7h_independent_verification(self) -> None:
        assert "149O.20L.7H" in _ARCH_DOC
        assert "Independent Verification" in _ARCH_DOC

    def test_req_042_still_open_in_architecture_doc(self) -> None:
        assert "OPEN — SOLE HBDC RESIDUAL" in _ARCH_DOC
