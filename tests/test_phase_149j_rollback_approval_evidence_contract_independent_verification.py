"""Phase 149J -- Rollback Approval Evidence Contract Independent
Verification.

Independent adversarial verification of RAE-001 v1.0 (frozen by Phase
149I, `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`). This
suite does NOT trust 149I's own summary as evidence; every assertion is
derived from independently re-reading RAE-001's current contract text
and independently exercising the real, unmodified Permission Broker
Foundation (`pcae.core.permission_broker_foundation`). No production
code is exercised for its *execution* effects -- no rollback, git
revert, or filesystem mutation is ever performed by this suite. Live
Foundation calls are made only against hand-constructed
`PermissionBrokerRequest` instances, exactly as RAE-001 §23's own
tracing methodology does, never against a mocked or simulated broker.

This is a read-only, contract-verification-only suite. It implements no
Evidence Validator, no Decision Template, no Binding-record schema, and
wires nothing to AG3/AG5. It modifies no production file and amends no
contract.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf

REPO_ROOT = Path(__file__).resolve().parents[1]
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"
CHGR_CONTRACT = REPO_ROOT / "docs" / "contracts" / "CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md"
TAMC_CONTRACT = REPO_ROOT / "docs" / "contracts" / "TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md"
AGENT_PY = REPO_ROOT / "src" / "pcae" / "core" / "agent.py"


@pytest.fixture(scope="module")
def rae_text() -> str:
    return RAE_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rae_text_flat(rae_text) -> str:
    """Contract prose word-wraps at ~72 columns; normalize whitespace so
    substring checks aren't defeated by an arbitrary line break."""
    return re.sub(r"\s+", " ", rae_text)


# ── 1. Requirement traceability (independently re-derived) ────────────


class TestRequirementTraceability:
    def test_requirement_ids_sequential_no_gaps_no_duplicates(self, rae_text):
        ids = sorted(int(m) for m in re.findall(r"\*\*RAE-REQ-(\d+)", rae_text))
        assert ids, "no RAE-REQ-* requirements found"
        assert ids == list(range(ids[0], ids[-1] + 1)), (
            "RAE-REQ-* numbering has a gap or duplicate"
        )
        assert ids[0] == 1
        assert len(ids) == 81, (
            "requirement count drifted from the independently reconstructed "
            "count of 81 -- re-verify before trusting this suite's other "
            "section-scoped assertions"
        )

    def test_status_frozen(self, rae_text):
        assert "**Status:** FROZEN" in rae_text

    def test_version_1_0(self, rae_text):
        assert "**Version:** 1.0" in rae_text


# ── 2. CHGR/TAM wall (§5) -- independently re-confirmed, not trusted ──


class TestChgrTamWall:
    def test_rae_never_declares_tam_human_authorization_record_type(self, rae_text_flat):
        """RAE-REQ-003: the Binding record SHALL NOT declare
        record_type: human_authorization or any TAM record_family value."""
        assert "SHALL NOT be a Typed Authority Model" in rae_text_flat
        assert "record_type: human_authorization" in rae_text_flat

    def test_rae_never_stores_under_cltr_cutover_namespace(self, rae_text_flat):
        assert "SHALL NOT be stored under" in rae_text_flat
        assert "cltr_cutover" in rae_text_flat

    def test_chgr_tam_wall_cited_from_chgr_19_1_and_tamc(self, rae_text):
        assert "CHGR-001 §19.1" in rae_text
        assert "TAMC-REQ-024" in rae_text
        assert "TAMC-REQ-025" in rae_text
        assert "TAMC-REQ-036" in rae_text

    def test_chgr_001_actually_states_the_wall(self):
        """Independently re-read CHGR-001 itself -- do not trust RAE-001's
        paraphrase of what CHGR-001 says."""
        text = CHGR_CONTRACT.read_text(encoding="utf-8")
        assert "wholly separate artifact family from CHGR" in text or (
            "never composed, subclassed, or wrapped" in text
        )

    def test_tamc_001_actually_states_req_024_025_036(self):
        text = TAMC_CONTRACT.read_text(encoding="utf-8")
        assert "TAMC-REQ-024" in text
        assert "TAMC-REQ-025" in text
        assert "TAMC-REQ-036" in text
        assert "Never establish, activate, transfer, select, or revoke" in text


# ── 3. Human identity / authority claims (§6) -- no overclaiming ──────


class TestHumanIdentityClaims:
    def test_no_authenticated_identity_language(self, rae_text):
        """RAE-001 must not claim authenticated, cryptographically proven,
        or unforgeable identity anywhere -- it must state the honest
        self-declared ceiling instead."""
        forbidden_phrases = [
            "authenticated approver identity",
            "cryptographically proven identity",
            "unforgeable principal identity",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in rae_text, (
                f"RAE-001 appears to overclaim identity strength: {phrase!r}"
            )
        assert "self-declared string" in rae_text

    def test_strategic_gaps_disclosed_not_hidden(self, rae_text):
        assert rae_text.count("STRATEGIC_GAP") >= 2
        assert "no stronger-than-self-declared human identity substrate" in rae_text.lower() \
            or "No stronger-than-self-declared human identity substrate" in rae_text

    def test_approval_authority_distinct_from_approval_event(self, rae_text):
        """§3/RAE-REQ-008: Approval Authority (eligibility) and Approval
        Event (the actual decision) must be two independent facts."""
        assert "Approval Authority" in rae_text
        assert "Approval Event" in rae_text
        assert "both required" in rae_text


# ── 4. Decision Template closed vocabulary (§7) ────────────────────────


class TestDecisionTemplateClosedVocabulary:
    def test_exactly_two_options(self, rae_text):
        assert "Exactly two: `approve_rollback`, `deny_rollback`" in rae_text

    def test_no_flag_may_substitute_for_a_published_decision(self, rae_text):
        assert "RAE-REQ-014" in rae_text
        assert "No CLI flag, function argument, environment variable" in rae_text

    def test_decision_not_conflated_with_broker_decision(self, rae_text):
        """RAE-REQ-015: approve_rollback != Permission Broker ALLOW."""
        assert "not, and SHALL NOT be conflated" in rae_text
        assert "Permission Broker" in rae_text


# ── 5. Binding record / operation identity (§8-11) ─────────────────────


class TestOperationBinding:
    def test_ag3_profile_job_id_and_original_commit_sha(self, rae_text):
        assert "{job_id, original_commit_sha}" in rae_text

    def test_ag5_profile_per_id_and_ecp_id(self, rae_text):
        assert "{per_id, ecp_id}" in rae_text

    def test_family_locking_stated(self, rae_text):
        assert "family-locked" in rae_text

    def test_exact_nonfuzzy_matching_required(self, rae_text):
        """RAE-REQ-024: exact, non-fuzzy matching between the live
        operation identity and the Binding's rollback_operation_reference."""
        assert "exact, non-fuzzy matching" in rae_text

    def test_changed_payload_invalidates_binding(self, rae_text):
        """RAE-REQ-025: no 'equivalent regeneration' exception."""
        assert '"equivalent regeneration" exception is defined by this contract' in rae_text

    def test_agent_operation_identity_fields_match_live_code(self):
        """Independently re-confirm against production source (not RAE-001's
        prose) that execute_rollback (AG3) resolves original_commit_sha
        internally via build_rollback_review, and build_rollback_execution
        (AG5) resolves ecp_id internally via the PromotionExecutionRecord --
        matching RAE-REQ-020/RAE-REQ-021's claimed derivation."""
        text = AGENT_PY.read_text(encoding="utf-8")
        assert "def execute_rollback(root: HarnessPath, job_id: str)" in text
        assert "def build_rollback_execution(" in text
        assert 'ecp_id = per.get("ecp_id")' in text
        assert 'original_commit_sha: str = job.get("commit_sha") or ""' in text


# ── 6. approval_present derivation conjunction (§13) ───────────────────

_CONJUNCTION_TERMS = [
    "a Rollback Approval Binding record exists",
    "resolves to",
    "selected_option_id is",
    "matching the",
    "exactly",
    "state is",
    "expires_at has not passed",
    "supersedes this one",
    "digests are valid",
]


class TestApprovalPresentDerivation:
    def test_derivation_is_strict_conjunction_of_nine_conditions(self, rae_text):
        block_start = rae_text.index("approval_present = True")
        block_end = rae_text.index("approval_present = False", block_start)
        block = rae_text[block_start:block_end]
        conditions = re.findall(r"\(\w\)\s", block)
        assert len(conditions) == 9, (
            f"expected 9 lettered conjunction terms (a)-(i), found {len(conditions)}"
        )

    def test_false_is_the_explicit_default_otherwise(self, rae_text):
        assert "approval_present = False\n    OTHERWISE" in rae_text

    def test_fail_closed_on_validator_internal_error(self, rae_text):
        assert "fail-closed, RAE-REQ-042" in rae_text

    def test_no_flag_or_agent_claim_ever_sets_approval_present(self, rae_text_flat):
        """RAE-REQ-039."""
        assert "never set by any CLI flag, caller-supplied boolean, or agent-authored claim" in rae_text_flat

    def test_approval_not_permission_stated(self, rae_text):
        """RAE-REQ-040: approve_rollback != Permission Broker ALLOW, and
        other policies still apply independently."""
        assert "Approval is not permission" in rae_text


# ── 7. IWC / AESIC exclusion (§18) ──────────────────────────────────────


class TestIwcAesicExclusion:
    def test_iwc_confirmation_never_itself_evidence(self, rae_text_flat):
        assert "IWC's own confirmation artifact" in rae_text_flat
        assert "is never itself Rollback" in rae_text_flat
        assert "Approval Evidence" in rae_text_flat

    def test_aesic_never_contributes_to_approval(self, rae_text):
        assert "Authority Evaluation / AESIC results SHALL NOT" in rae_text
        assert "constitute, contribute to, or be consulted" in rae_text


# ── 8. Legacy flag exclusion (§19) ──────────────────────────────────────


class TestLegacyFlagExclusion:
    def test_all_known_legacy_flags_frozen_as_non_evidence(self, rae_text):
        flags = [
            "--promotion-authorized",
            "--reviewed-by",
            "change_approval_state",
            "--approve-keep",
            "--approved-by",
            "--reason",
        ]
        section_start = rae_text.index("## 19. Legacy Flag Exclusion")
        section_end = rae_text.index("## 20.", section_start)
        section = rae_text[section_start:section_end]
        for flag in flags:
            assert flag in section, f"legacy flag {flag!r} not frozen as non-evidence"

    def test_bare_state_flag_function_distinguished_from_decision_template_option(self, rae_text):
        """RAE-REQ-060 explicitly distinguishes agent.py's bare
        approve_rollback(root, job_id) function from this contract's
        approve_rollback Decision Template option -- verify the contract
        text itself draws this distinction, and verify the cited line
        actually is that bare function in production source."""
        assert "src/pcae/core/agent.py:5146" in rae_text
        assert "not to be confused with this contract's" in rae_text
        text = AGENT_PY.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert "def approve_rollback(root: HarnessPath, job_id: str)" in lines[5145]


# ── 9. Freshness (§14) -- 24h TTL provenance, independently traced ────


class TestFreshnessTtlProvenance:
    def test_24_hour_window_stated(self, rae_text):
        assert "24-hour" in rae_text

    def test_ttl_is_disclosed_as_structural_reuse_not_invented(self, rae_text):
        assert "never an arbitrarily invented duration" in rae_text

    def test_ttl_amendment_path_disclosed(self, rae_text):
        """RAE-REQ-043: a future amendment MAY revise the duration; this
        contract does not pre-authorize such a revision."""
        assert "A future contract amendment MAY" in rae_text
        assert "does not pre-authorize" in rae_text

    def test_24_hour_precedent_independently_locatable_in_primary_source(self):
        """Independent verification finding: RAE-001 itself never cites a
        file:line for the 24-hour duration it reuses. Confirm the
        underlying fact is nonetheless real and independently locatable
        in CLTR-CUTOVER-001 (Phase 135's frozen contract), not fabricated."""
        cutover_doc = (
            REPO_ROOT / "docs" / "PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md"
        )
        assert cutover_doc.exists()
        text = re.sub(r"\s+", " ", cutover_doc.read_text(encoding="utf-8"))
        assert "expires **24 hours** after the authorization timestamp" in text
        assert "the default and floor are frozen here at 24 hours" in text


# ── 10. Revocation / supersession / replay (§15-16) ─────────────────────


class TestRevocationSupersessionReplay:
    def test_revoked_binding_never_resolves_true(self, rae_text):
        assert "A revoked Binding record SHALL NEVER resolve `approval_present=True`" in rae_text

    def test_supersession_requires_explicit_evidence_id_still(self, rae_text):
        """RAE-REQ-047: supersession determines which record is
        authoritative; it does not create an implicit 'latest' lookup."""
        assert "does not create an implicit “latest” lookup" in rae_text \
            or "does not create an implicit \"latest\" lookup" in rae_text

    def test_no_latest_approval_resolution(self, rae_text):
        """RAE-REQ-041."""
        assert "SHALL NOT select a Rollback Approval Binding merely because it" in rae_text
        assert "is the most recent Binding" in rae_text

    def test_replay_binding_single_use_mechanism(self, rae_text):
        assert "replay_binding" in rae_text
        assert "one-time-use token" in rae_text

    def test_retry_requires_fresh_broker_evaluation(self, rae_text):
        """RAE-REQ-053: no prior broker ALLOW decision is ever reused."""
        assert "No prior broker `ALLOW` decision is" in rae_text
        assert "ever reused across attempts" in rae_text


# ── 11. Live Foundation satisfiability (§23) -- real code, no mocks ────


def _rollback_request(*, approval_present: bool, simulation_only: bool = True,
                       task_id: str | None = "task-149j-verify",
                       requested_component: str = "COMP-008") -> pbf.PermissionBrokerRequest:
    return pbf.PermissionBrokerRequest(
        request_id="149j-verify-probe",
        timestamp="2026-08-04T00:00:00Z",
        action_type=pbf.ACTION_ROLLBACK,
        execution_class=pbf.EXECUTION_CLASS_ROLLBACK,
        task_id=task_id,
        phase_id="149J",
        requested_component=requested_component,
        requested_capability="execute_rollback",
        requested_resource=None,
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=simulation_only,
    )


class TestLiveFoundationSatisfiability:
    """Exercises the real, unmodified PermissionBroker. No mocks. Every
    call is decision-only (simulation_only defaults True); no git command,
    no filesystem mutation is ever executed by this suite."""

    def test_execution_class_rollback_is_a_real_known_class(self):
        assert pbf.EXECUTION_CLASS_ROLLBACK == "rollback"
        assert pbf.EXECUTION_CLASS_ROLLBACK in pbf.KNOWN_EXECUTION_CLASSES

    def test_pol_004_scoped_to_include_rollback(self):
        rule = pbf.MissingHumanApprovalRule()
        assert pbf.EXECUTION_CLASS_ROLLBACK in rule.applicable_execution_classes

    def test_valid_approval_otherwise_valid_resolves_allow(self):
        broker = pbf.PermissionBroker()
        decision = broker.evaluate(_rollback_request(approval_present=True))
        assert decision.decision == pbf.DECISION_ALLOW
        assert "POL-004" not in decision.triggered_policy_ids
        assert "POL-005" not in decision.triggered_policy_ids

    def test_missing_approval_resolves_human_review(self):
        broker = pbf.PermissionBroker()
        decision = broker.evaluate(_rollback_request(approval_present=False))
        assert decision.decision == pbf.DECISION_HUMAN_REVIEW
        assert "POL-004" in decision.triggered_policy_ids

    def test_valid_approval_is_not_a_blanket_allow_other_policy_still_denies(self):
        """RAE-REQ-040: approval is not permission. A missing active task
        (POL-001) must still deny even with approval_present=True."""
        broker = pbf.PermissionBroker()
        decision = broker.evaluate(_rollback_request(approval_present=True, task_id=None))
        assert decision.decision == pbf.DECISION_DENY
        assert "POL-001" in decision.triggered_policy_ids

    def test_real_non_simulated_execution_still_denied_pol_005(self):
        """POL-005 remains unconditionally active regardless of approval."""
        broker = pbf.PermissionBroker()
        decision = broker.evaluate(
            _rollback_request(approval_present=True, simulation_only=False)
        )
        assert decision.decision == pbf.DECISION_DENY
        assert "POL-005" in decision.triggered_policy_ids

    def test_unrecognized_component_still_denies_even_with_approval(self):
        """POL-007 independently applies; RAE-001 grants no policy-selection
        power to approval evidence (RAE-REQ-063 threats via §13 conjunction
        cannot bypass unrelated policies)."""
        broker = pbf.PermissionBroker()
        decision = broker.evaluate(
            _rollback_request(approval_present=True, requested_component="AG3-not-a-component-id")
        )
        assert decision.decision == pbf.DECISION_DENY
        assert "POL-007" in decision.triggered_policy_ids


# ── 12. Compatibility confirmations (§24) / production & contract boundary ──


class TestCompatibilityAndBoundary:
    def test_rwmpc_pbpa_pbpc_require_no_amendment_claim_present(self, rae_text):
        assert "RAE-REQ-071" in rae_text
        assert "RAE-REQ-072" in rae_text
        assert "RAE-REQ-073" in rae_text

    def test_no_blocking_finding_declared(self, rae_text):
        assert "No BLOCKING finding is raised." in rae_text

    def test_contract_freeze_verdict_present(self, rae_text):
        assert "ROLLBACK APPROVAL EVIDENCE CONTRACT (RAE-001) v1.0 FROZEN" in rae_text

    def test_non_goals_exclude_implementation(self, rae_text):
        section_start = rae_text.index("## 27. Non-Goals")
        section = rae_text[section_start:section_start + 1200]
        assert "Rollback production implementation" in section
        assert "AG3/AG5 Permission Broker wiring" in section
        assert "Runtime activation of any kind" in section
