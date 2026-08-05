"""Phase 149O.1C -- Human Approval Trusted Provenance Contract Independent
Verification.

Independent adversarial verification of HATP-001 v1.0 (frozen by Phase
149O.1B.3, `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`).
This suite does NOT trust the 149O.1B.3 phase report, `PROJECT_STATUS.md`,
or `CHANGELOG.md` as evidence; every assertion is derived from an
independent re-read of the current contract text. HATP-001 has no
production implementation (`src/pcae/**` is untouched by this phase and
unconsulted by this suite) -- this is a contract-text/structure
verification suite, not a behavioral suite, mirroring
`tests/test_phase_149j_rollback_approval_evidence_contract_independent_verification.py`'s
methodology for RAE-001.

This suite modifies no contract text, implements nothing, provisions no
OS boundary, and closes no B-149O finding.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"


@pytest.fixture(scope="module")
def hatp_text() -> str:
    return HATP_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hatp_text_flat(hatp_text) -> str:
    """Contract prose word-wraps at ~72 columns; normalize whitespace so
    substring checks aren't defeated by an arbitrary line break."""
    return re.sub(r"\s+", " ", hatp_text)


# ── 1. Requirement inventory (independently re-derived, not reused) ──────


class TestRequirementInventory:
    def test_requirement_ids_sequential_no_gaps_no_duplicates(self, hatp_text):
        ids = sorted(int(m) for m in re.findall(r"\*\*HATP-REQ-(\d+)\.\*\*", hatp_text))
        assert ids, "no HATP-REQ-* requirement definitions found"
        assert ids == list(range(1, len(ids) + 1)), (
            "HATP-REQ-* numbering has a gap or duplicate"
        )
        assert len(ids) == 117, (
            "requirement count drifted from the independently reconstructed "
            "count of 117 -- re-verify before trusting this suite's other "
            "section-scoped assertions"
        )

    def test_status_frozen(self, hatp_text):
        assert "**Status:** FROZEN" in hatp_text

    def test_version_1_0(self, hatp_text):
        assert "**Version:** 1.0" in hatp_text

    def test_frozen_by_149o_1b_3(self, hatp_text):
        assert "Phase 149O.1B.3" in hatp_text


# ── 2. Root 1 -- Proof Production ─────────────────────────────────────────


class TestRoot1ProofProduction:
    def test_hardware_backed_nonexportable_key_required(self, hatp_text_flat):
        assert "non-exportable private key" in hatp_text_flat

    def test_fresh_presence_per_operation_required(self, hatp_text_flat):
        assert "fresh human-presence event" in hatp_text_flat

    def test_one_presence_one_proof_strict(self, hatp_text_flat):
        assert "one human-presence action SHALL produce at most one HATP proof" in hatp_text_flat

    def test_unattended_session_reuse_forbidden(self, hatp_text_flat):
        assert '"unlock once, sign many"' in hatp_text_flat
        assert "SHALL NOT be HATP-compliant" in hatp_text_flat

    def test_unattended_legitimate_signer_abuse_forbidden(self, hatp_text_flat):
        assert "without a fresh human physical-presence event, SHALL NOT obtain a valid HATP proof" in hatp_text_flat

    def test_no_silent_software_key_downgrade(self, hatp_text_flat):
        assert "SHALL NOT silently substitute for a required hardware signer" in hatp_text_flat

    def test_no_fido2_piv_interchangeability_overclaim(self, hatp_text_flat):
        assert "not declared interchangeable by this contract" in hatp_text_flat

    def test_no_test_provider_silent_production_fallback(self, hatp_text_flat):
        assert "no default-enabled test provider, no silent fallback" in hatp_text_flat


# ── 3. Root 2A -- Device / Provider Genuineness ───────────────────────────


class TestRoot2aAttestation:
    def test_attestation_does_not_establish_authority_alone(self, hatp_text_flat):
        assert (
            "SHALL NOT by itself establish PCAE principal identity, rollback "
            "approval authority, or repository authorization" in hatp_text_flat
        )

    def test_attestation_root_not_self_selected(self, hatp_text_flat):
        assert "SHALL NOT self-select an arbitrary attestation root" in hatp_text_flat

    def test_valid_attestation_without_enrollment_grants_nothing(self, hatp_text_flat):
        assert "does not grant PCAE approval authority" in hatp_text_flat


# ── 4. Root 2B -- Bootstrap Security Boundary ─────────────────────────────


class TestRoot2bBootstrapBoundary:
    def test_bootstrap_model_class_b(self, hatp_text_flat):
        assert "Bootstrap Model Class B" in hatp_text_flat

    def test_two_principal_topology(self, hatp_text_flat):
        assert "exactly two principals" in hatp_text_flat

    def test_no_privilege_escalation_path(self, hatp_text_flat):
        assert "SHALL NOT possess any" in hatp_text_flat
        assert "privilege-escalation path" in hatp_text_flat

    def test_same_user_deployment_not_ready(self, hatp_text_flat):
        assert "SHALL NOT be considered" in hatp_text_flat
        assert "operationally ready" in hatp_text_flat
        assert "**NOT READY**" in hatp_text_flat

    def test_trust_store_not_agent_writable(self, hatp_text_flat):
        assert "NOT writable, replaceable, or deletable by the Agent OS principal" in hatp_text_flat

    def test_parent_directory_replacement_protection_survived_freeze(self, hatp_text_flat):
        """Load-bearing architecture requirement (149O.1B.1) -- verify it
        was not dropped/weakened during contract freeze."""
        assert "parent-directory replacement" in hatp_text_flat

    def test_permission_and_acl_protection_survived_freeze(self, hatp_text_flat):
        assert "permission weakening, and ACL modification" in hatp_text_flat

    def test_no_environment_variable_trust_root_redirection(self, hatp_text_flat):
        assert "SHALL NOT be able to redirect the authoritative trust store" in hatp_text_flat

    def test_no_cli_trust_root_override_flag(self, hatp_text_flat):
        assert "SHALL NOT accept an override flag" in hatp_text_flat


# ── 5. Enrollment / Authority ─────────────────────────────────────────────


class TestEnrollmentAndAuthority:
    def test_self_enrollment_prohibited(self, hatp_text_flat):
        assert "self-enrollment prohibition" in hatp_text_flat

    def test_verifier_key_replacement_prohibited(self, hatp_text_flat):
        assert "verifier-key-replacement prohibition" in hatp_text_flat

    def test_unenrolled_device_possession_is_unauthorized_not_unverified(self, hatp_text_flat):
        assert "is **UNAUTHORIZED**, not merely unverified" in hatp_text_flat

    def test_enrollment_does_not_itself_approve(self, hatp_text_flat):
        assert "Enrollment establishes who may approve. It does not itself approve any rollback" in hatp_text_flat

    def test_authority_repository_specific_not_global(self, hatp_text_flat):
        assert "assigns repository-specific rollback authority" in hatp_text_flat

    def test_authority_mapping_never_from_proof_content_alone(self, hatp_text_flat):
        assert "never from proof content alone" in hatp_text_flat


# ── 6. CRI Model A / Repository Identity ──────────────────────────────────


class TestRepositoryIdentity:
    def test_cri_model_a_adopted(self, hatp_text_flat):
        assert "CRI Model A" in hatp_text_flat

    def test_repository_id_not_authority_mandatory_statement(self, hatp_text_flat):
        assert (
            "Possession, knowledge, copying, or modification of `repository_id` "
            "SHALL NOT by itself grant HATP approval authority" in hatp_text_flat
        )

    def test_repository_local_metadata_alone_cannot_transfer_authority(self, hatp_text_flat):
        assert (
            "repository-local metadata alone SHALL NOT be sufficient to transfer "
            "HATP authorization to a new local deployment" in hatp_text_flat
        )

    def test_full_copy_does_not_transfer_authority(self, hatp_text_flat):
        assert "**Full directory copy:**" in hatp_text_flat
        assert "SHALL NOT transfer HATP authority" in hatp_text_flat

    def test_git_clone_does_not_inherit_authority(self, hatp_text_flat):
        assert "**Git clone:**" in hatp_text_flat
        assert "SHALL NOT automatically inherit HATP repository authority" in hatp_text_flat

    def test_fork_does_not_inherit_authority(self, hatp_text_flat):
        assert "**Fork:**" in hatp_text_flat

    def test_worktree_requires_separate_enrollment(self, hatp_text_flat):
        assert "**Git worktree:**" in hatp_text_flat
        assert "distinct repository-instance identity" in hatp_text_flat
        assert "require separate bootstrap enrollment" in hatp_text_flat

    def test_repository_id_theft_does_not_confer_authority(self, hatp_text_flat):
        assert "**Repository-ID theft:**" in hatp_text_flat

    def test_same_id_cross_deployment_still_unauthorized(self, hatp_text_flat):
        assert "**Same-ID cross-deployment:**" in hatp_text_flat
        assert "the wrong deployment SHALL be treated as unauthorized" in hatp_text_flat

    def test_path_move_preserves_id_but_may_invalidate_binding(self, hatp_text_flat):
        assert "**Path move:**" in hatp_text_flat
        assert "SHALL be unavailable until an admin-authorized rebind occurs" in hatp_text_flat

    def test_id_mutation_missing_malformed_unknown_all_fail_closed(self, hatp_text_flat):
        assert "**Repository-ID mutation, missing, malformed, or unknown:**" in hatp_text_flat
        assert "fail closed in every case" in hatp_text_flat


# ── 7. Protected Deployment Binding ───────────────────────────────────────


class TestDeploymentBinding:
    def test_deployment_binding_is_layer_2_load_bearing(self, hatp_text_flat):
        assert "load-bearing" in hatp_text_flat

    def test_canonical_root_resolved_deterministically_not_from_raw_path(self, hatp_text_flat):
        assert "never trusting a raw caller-supplied path string" in hatp_text_flat

    def test_proof_does_not_carry_raw_deployment_path(self, hatp_text_flat):
        assert "SHALL NOT include the raw canonical local deployment path" in hatp_text_flat

    def test_only_human_admin_can_rebind(self, hatp_text_flat):
        assert "The agent cannot rebind itself" in hatp_text_flat


# ── 8. Canonical Payload / Proof Schema ───────────────────────────────────


class TestCanonicalPayload:
    REQUIRED_FIELDS = [
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "repository_id",
        "decision_record_id",
        "decision_record_digest",
        "binding_id",
        "binding_digest",
        "rollback_site",
        "job_id",
        "original_commit_sha",
        "per_id",
        "ecp_id",
        "issued_at",
        "proof_version",
    ]

    def test_all_minimum_payload_fields_present(self, hatp_text):
        for field in self.REQUIRED_FIELDS:
            assert field in hatp_text, f"canonical payload missing required field {field!r}"

    def test_generic_action_label_without_operation_fields_insufficient(self, hatp_text_flat):
        assert "`approve_rollback`" in hatp_text_flat
        assert "SHALL be treated as `WRONG_OPERATION` or `MALFORMED`" in hatp_text_flat

    def test_decision_mutation_invalidates_proof(self, hatp_text_flat):
        assert (
            "Mutation of the referenced Decision content after proof creation "
            "SHALL invalidate the proof" in hatp_text_flat
        )

    def test_binding_mutation_invalidates_proof(self, hatp_text_flat):
        assert (
            "Mutation of the referenced Binding content after proof creation "
            "SHALL invalidate the proof" in hatp_text_flat
        )

    def test_repository_id_change_invalidates_proof(self, hatp_text_flat):
        assert "Changing `repository_id` after proof creation SHALL invalidate the proof" in hatp_text_flat

    def test_proof_payload_has_no_explicit_closed_schema_requirement(self, hatp_text):
        """Finding F1 (non-blocking): unlike the closed verification
        vocabulary (HATP-REQ-078), the proof *payload* has no requirement
        governing unknown/extra fields. This test documents the gap as an
        expected, reported, non-blocking finding -- it must keep failing
        (i.e. this assertion must keep passing, meaning the phrase is
        absent) until a future contract amendment adds one."""
        for phrase in ("unknown field", "closed schema", "additional field", "extra field"):
            assert phrase not in hatp_text.lower()


# ── 9. Proof Verification / Closed Vocabulary / VALID Conjunction ────────


class TestProofVerification:
    CLOSED_VOCABULARY = [
        "VALID",
        "MISSING",
        "MALFORMED",
        "INVALID_SIGNATURE",
        "UNKNOWN_SIGNER",
        "UNAUTHORIZED_SIGNER",
        "REVOKED_SIGNER",
        "INVALID_ATTESTATION",
        "USER_PRESENCE_NOT_PROVEN",
        "WRONG_OPERATION",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "EXPIRED",
    ]

    def test_closed_vocabulary_all_terms_present(self, hatp_text):
        for term in self.CLOSED_VOCABULARY:
            assert term in hatp_text, f"missing closed-vocabulary term {term!r}"

    def test_vocabulary_disjoint_from_permission_broker_and_rae(self, hatp_text_flat):
        assert "SHALL NOT reuse Permission Broker decision names" in hatp_text_flat
        assert "RAE-001's own vocabulary" in hatp_text_flat

    def test_valid_requires_conjunctive_no_partial_success(self, hatp_text_flat):
        assert "VALID` only when every applicable term succeeds, conjunctively, with no partial success" in hatp_text_flat

    def test_valid_conjunction_covers_all_expected_factors(self, hatp_text_flat):
        expected_factor_phrases = [
            "proof structurally valid",
            "provider profile accepted",
            "signature/assertion valid",
            "required human presence proven",
            "signer key known",
            "principal mapping valid",
            "principal authority valid",
            "`repository_id` matches the proof",
            "protected deployment registration matches the current deployment",
            "`decision_record_digest` matches",
            "`binding_digest` matches",
            "operation identity matches",
            "proof time valid",
            "signer not revoked",
        ]
        for phrase in expected_factor_phrases:
            assert phrase in hatp_text_flat, f"VALID conjunction missing factor: {phrase!r}"

    def test_missing_bootstrap_state_fails_closed(self, hatp_text_flat):
        assert "Missing trusted bootstrap state SHALL cause verification to fail closed" in hatp_text_flat

    def test_cross_repository_replay_rejected(self, hatp_text_flat):
        assert "**Cross-repository replay:**" in hatp_text_flat

    def test_same_id_replay_defense(self, hatp_text_flat):
        assert "**Same-ID replay defense:**" in hatp_text_flat

    def test_operation_replay_rejected(self, hatp_text_flat):
        assert "**Operation replay:**" in hatp_text_flat


# ── 10. Freshness / Revocation ────────────────────────────────────────────


class TestFreshnessAndRevocation:
    def test_no_conflicting_longer_approval_lifetime(self, hatp_text_flat):
        assert "SHALL NOT create a conflicting, longer approval lifetime" in hatp_text_flat

    def test_future_dated_issued_at_treated_expired(self, hatp_text_flat):
        assert "SHALL be treated as `EXPIRED`/invalid" in hatp_text_flat

    def test_authority_revocation_effective_at_consumption_time(self, hatp_text_flat):
        assert "authority MUST remain valid **at proof-consumption (verification) time**" in hatp_text_flat
        assert "regardless of validity at the time of signing" in hatp_text_flat

    def test_no_agent_driven_key_rotation(self, hatp_text_flat):
        assert "No agent-driven rotation is permitted" in hatp_text_flat


# ── 11. Failure Semantics / Fail-Closed ───────────────────────────────────


class TestFailClosed:
    def test_non_valid_outcome_never_default_allow(self, hatp_text_flat):
        assert "never in a default-allow or best-effort partial trust outcome" in hatp_text_flat

    def test_unsafe_deployment_no_procedural_fallback(self, hatp_text_flat):
        assert 'No procedural fallback (e.g. "trust anyway with a warning") is permitted' in hatp_text_flat

    def test_current_deployment_readiness_status_block_frozen(self, hatp_text_flat):
        for line in (
            "HATP CONTRACT: FROZEN",
            "HATP IMPLEMENTATION: NOT IMPLEMENTED",
            "CLASS-B OS BOUNDARY: NOT PROVISIONED",
            "REPOSITORY IDENTITY: NOT IMPLEMENTED",
            "HATP BOOTSTRAP ENVIRONMENT: NOT READY",
        ):
            assert line in hatp_text_flat


# ── 12. Layering / Compatibility Boundaries ───────────────────────────────


class TestLayeringAndCompatibility:
    def test_semantic_distinctions_frozen(self, hatp_text_flat):
        assert "human presence" in hatp_text_flat and "principal identity" in hatp_text_flat
        assert "a valid HATP proof" in hatp_text_flat and "valid RAE evidence" in hatp_text_flat

    def test_rae_necessary_not_sufficient(self, hatp_text_flat):
        assert "necessary but not sufficient for a rollback to proceed" in hatp_text_flat

    def test_rae_compatible_as_is(self, hatp_text_flat):
        assert "RAE-001 v1.0 is **COMPATIBLE AS-IS**" in hatp_text_flat

    def test_fresh_broker_reevaluation_required_after_valid_proof(self, hatp_text_flat):
        assert (
            "A `VALID` HATP proof does not itself transform an existing "
            "`HUMAN_REVIEW` Permission Broker result into `ALLOW`" in hatp_text_flat
        )

    def test_iwc_confirmation_distinct_from_approval(self, hatp_text_flat):
        assert "confirmation remains distinct from HATP approval" in hatp_text_flat

    def test_aesic_aem_disclosure_only(self, hatp_text_flat):
        assert "AESIC-001 v1.3 and AEM-001 v1.0 remain disclosure-only" in hatp_text_flat

    def test_tamc_never_composed_subclassed_wrapped(self, hatp_text_flat):
        assert "never composed, subclassed, or wrapped by a HATP artifact" in hatp_text_flat

    def test_rwmpc_pbpa_pbpc_unamended(self, hatp_text_flat):
        assert "does not alter mutation freshness or execution ownership" in hatp_text_flat
        assert "introduces no change to POL applicability" in hatp_text_flat

    def test_compatibility_reconfirmation_lists_all_eight_dependency_contracts(self, hatp_text_flat):
        for contract in (
            "RAE-001 v1.0",
            "CHGR-001 v1.3",
            "RWMPC-001 v1.0",
            "PBPA-001 v1.0",
            "PBPC-001 v1.2",
            "IWC-001 v1.2",
            "AESIC-001 v1.3",
            "TAMC-001 v1.0",
        ):
            assert contract in hatp_text_flat, f"compatibility reconfirmation missing {contract!r}"


# ── 13. Open Findings / B-149O ────────────────────────────────────────────


class TestOpenFindings:
    def test_b149o_findings_remain_open(self, hatp_text_flat):
        assert "B-149O-1 through B-149O-4 remain **OPEN**" in hatp_text_flat

    def test_this_freeze_does_not_repair_findings(self, hatp_text_flat):
        assert "This contract freeze does not repair them" in hatp_text_flat


# ── 14. Mandatory Future Acceptance Attack Matrix (20 attacks) ───────────


class TestMandatoryAttackMatrix:
    def test_twenty_attacks_enumerated(self, hatp_text):
        # Matches "1. ", "2. ", ... "20." at the start of a matrix line.
        matrix_section = hatp_text.split("## 39. Mandatory Future Acceptance Attack Matrix")[1]
        matrix_section = matrix_section.split("## 40.")[0]
        numbered = re.findall(r"^\d+\.\s", matrix_section, flags=re.MULTILINE)
        assert len(numbered) == 20, f"expected 20 mandatory attacks, found {len(numbered)}"

    @pytest.mark.parametrize(
        "expected_outcome",
        [
            "invalid",
            "`UNKNOWN_SIGNER`",
            "`UNAUTHORIZED_SIGNER`",
            "`USER_PRESENCE_NOT_PROVEN`",
            "denied by OS bootstrap authority",
            "`WRONG_OPERATION`",
            "`WRONG_REPOSITORY`",
            "`WRONG_DEPLOYMENT`",
            "`REVOKED_SIGNER`",
            "`EXPIRED`",
            "`VALID`",
        ],
    )
    def test_attack_matrix_expected_outcomes_present(self, hatp_text, expected_outcome):
        assert expected_outcome in hatp_text


# ── 15. Blocking-Condition Self-Check (independently re-derived) ─────────


class TestBlockingConditionSelfCheck:
    BLOCKING_CONDITIONS_RESOLVED_NO = [
        "Human presence bypassable by unattended agent",
        "Trusted bootstrap state agent-writable",
        "Agent has a privilege-escalation route to Human/Admin context",
        "Self-enrollment prevention only an application convention",
        "Verifier-key-replacement prevention only an application convention",
        "`repository_id` alone can confer authority",
        "Repo copy/clone can silently inherit HATP authority",
        "Deployment-binding semantics ambiguous",
        "Proof can self-select trusted signer",
        "Proof does not bind concrete operation",
        "Wrong repository can replay a proof",
        "RAE integration contradicts frozen RAE semantics",
        "Provider profile assumes unsupported arbitrary-signing behavior",
    ]

    def test_all_thirteen_blocking_conditions_present_and_resolved_no(self, hatp_text):
        for condition in self.BLOCKING_CONDITIONS_RESOLVED_NO:
            assert condition in hatp_text, f"blocking-condition row missing: {condition!r}"

    def test_no_condition_left_unresolved(self, hatp_text_flat):
        assert "No condition in this list is unresolved. This contract is FROZEN v1.0" in hatp_text_flat


# ── 16. Requirement-Sequence Self-Check (Finding F2, independently verified) ─


class TestRequirementSequenceSelfCheck:
    def test_hatp_req_116_undercounts_its_own_contract_by_one(self, hatp_text):
        """Finding F2 (non-blocking, editorial): HATP-REQ-116 asserts the
        contract runs 001..116, but HATP-REQ-117 (Versioning, section 44)
        follows it in the same document. The independently re-derived
        count (117, see TestRequirementInventory) is authoritative; this
        test documents the self-referential requirement's own miscount so
        a future contract amendment can correct it without re-discovering
        the defect."""
        assert "through `HATP-REQ-116` inclusive" in hatp_text
        assert "**HATP-REQ-117.**" in hatp_text
        ids = sorted(int(m) for m in re.findall(r"\*\*HATP-REQ-(\d+)\.\*\*", hatp_text))
        assert max(ids) == 117, (
            "if this fails because the contract was amended, HATP-REQ-116's "
            "self-count sentence should be re-checked for correctness too"
        )

    def test_rae_001_has_no_equivalent_self_referential_sequence_requirement(self):
        """Independently confirms HATP-001's self-count requirement is a
        HATP-specific addition, not an existing RAE-001 convention that
        HATP-001 merely (correctly) mirrored -- supports Finding F2's
        framing that this is a fresh, HATP-only editorial slip."""
        rae_text = RAE_CONTRACT.read_text(encoding="utf-8")
        assert "Sequence Verification" not in rae_text
        assert "sequential, no gaps, no duplicates" not in rae_text


# ── 17. Versioning ─────────────────────────────────────────────────────────


class TestVersioning:
    def test_amendment_requires_governed_phase(self, hatp_text_flat):
        assert "SHALL proceed through a governed contract-amendment phase" in hatp_text_flat
        assert "never through silent reinterpretation of this text" in hatp_text_flat


# ── 18. Recommended Next Phase (as stated by the contract itself) ─────────


class TestRecommendedNextPhase:
    def test_contract_recommends_149o_1c_independent_verification(self, hatp_text):
        """HATP-001 §47 recommends 149O.1C -- this phase -- as its own next
        step; 149O.1D (implementation planning) is this *phase's* report's
        recommendation for what follows 149O.1C, not the contract's own."""
        assert "149O.1C" in hatp_text
        assert "Human Approval Trusted Provenance Contract Independent Verification" in hatp_text
