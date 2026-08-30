"""Fresh static verification for Phase 149O...3W.1R.2B.1R.1.1R.

Contract text only: this module imports no PCAE production package and makes
no authenticator, runtime, network, credential, or hardware call.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "contracts"
HPAC = (CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md").read_text()
RIHAC = (CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md").read_text()
RIASC_PATH = CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
PBRD_PATH = CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = (CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md").read_text()
RPAC_PATH = CONTRACTS / "RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
VERIFY = (
    ROOT
    / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1_INDEPENDENT_VERIFICATION_CROSS_CONTRACT_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_FREEZE_REPAIR.md"
).read_text()
HPAC_FLAT = " ".join(HPAC.split())
RIHAC_FLAT = " ".join(RIHAC.split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_primary_evidence_contains_exact_open_findings() -> None:
    assert (
        "B-3 — Blind touch can substitute for informed approval.** No "
        "non-forgeable confirmation evidence or trusted subject display is bound."
    ) in VERIFY
    assert (
        "B-4 — Proof schema/store/reference contract is incomplete and "
        "internally inconsistent.** Canonical resolution cannot be implemented uniquely."
    ) in VERIFY
    assert "OPEN ORIGINAL BLOCKING: B-3, B-4" in VERIFY


def test_active_contract_versions_after_1r15_4_normalization() -> None:
    # `.1R` left these at v2.0/v3.0; `.1R.15.4` normalized RDGO->v3.1,
    # PBRD->v2.1, HPAC->v2.1 (all MINOR). RIHAC v2.0, RIASC v3.0, RPAC v1.0
    # unchanged.
    assert HPAC.startswith("# HPAC-001 v2.1")
    assert RIHAC.startswith("# RIHAC-001 v2.0")
    assert RIASC_PATH.read_text().startswith("# RIASC-001 v3.0")
    assert PBRD_PATH.read_text().startswith("# PBRD-001 v2.1")
    assert RDGO.startswith("# RDGO-001 v3.1")
    rpac = RPAC_PATH.read_text()
    assert "**Contract:** RPAC-001" in rpac
    assert "**Version:** 1.0" in rpac


def test_rpac_companion_contract_is_byte_identical_and_riasc_pbrd_only_normalized() -> None:
    # RPAC-001 is untouched by `.1R` and by `.1R.15.4`. RIASC-001 / PBRD-001
    # carry only the authorized `.1R.15.4` normalization (RIASC §9 errata,
    # PBRD §4a representation-equivalence clause + v2.1 header).
    assert sha256(RPAC_PATH) == "395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89"
    assert PBRD_PATH.read_text().startswith("# PBRD-001 v2.1")
    assert "Errata note (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — V-3" in RIASC_PATH.read_text()


def test_hpac_requirement_declarations_are_unique_and_gapless() -> None:
    declared = [
        int(value)
        for value in re.findall(r"\*\*HPAC-REQ-(\d{3})(?:\s*\([^)]*\))?\.\*\*", HPAC)
    ]
    assert declared == list(range(1, 106))


def test_canonical_approval_subject_is_closed_and_exact() -> None:
    for token in (
        "HPAC-APPROVAL-SUBJECT/2.0",
        "the exact closed five-field RIASC-001 v3.0 `subject` object",
        "the exact closed RIASC-001 v3.0 `approval_scope` object",
        "`approval_preview_digest`",
        "`expires_at`",
        "`attempt_limit` (const `1`)",
    ):
        assert token in HPAC_FLAT


def test_presentation_mechanism_is_protected_and_not_repo_selectable() -> None:
    assert "HPAC-PRESENTATION-MECHANISM/2.0" in HPAC
    assert "<HPAC_PROTECTED_ROOT>/presentation-mechanisms/v2/<mechanism_id>/descriptor.json" in HPAC
    assert "`agent_substitution_resistant` (const `true`)" in HPAC
    assert "Ordinary terminal stdout/stdin cannot truthfully satisfy" in HPAC
    assert "Repository, task, agent," in HPAC


def test_presentation_evidence_schema_and_path_are_canonical() -> None:
    for token in (
        "HPAC-PRESENTATION-EVIDENCE/2.0",
        "`hpe-<32-lowercase-hex>`",
        "`presentation_digest`",
        "`canonical_subject`",
        "`mechanism_ref`",
        "`human_visible_facts`",
        "`human_visible_representation_digest`",
        "`mechanism_attestation`",
        "<HPAC_PROTECTED_ROOT>/presentations/v2/<presentation_id>/presentation.json",
    ):
        assert token in HPAC


def test_presentation_contains_human_usable_authority_facts() -> None:
    for field in (
        "`repository_display`",
        "`task_display`",
        "`runtime_target_display`",
        "`operation_effect_scope_display`",
        "`prompt_instruction_display`",
        "`invocation_display`",
        "`expires_at`",
        "`one_shot_notice`",
    ):
        assert field in HPAC
    assert "opaque digest alone forbidden" in HPAC


def test_presentation_attestation_is_exact_and_not_self_authenticating() -> None:
    assert "HPAC-PRESENTATION-ATTESTATION/2.0" in HPAC
    assert "no other or omitted field is permitted" in HPAC
    assert "Digest agreement without successful attestation verification is non-authority" in HPAC_FLAT
    assert "`approval_preview_digest` SHALL equal this exact `human_visible_representation_digest`" in HPAC_FLAT
    assert "only the protected mechanism" in HPAC


def test_blind_touch_is_normatively_rejected() -> None:
    assert "Valid FIDO2 signature, UP, and UV without a successfully resolved" in HPAC
    assert "is a blind touch and SHALL NOT satisfy" in HPAC
    assert "caller-created evidence" in RDGO


def test_challenge_domain_and_wire_schema_are_unchanged() -> None:
    assert "pcae.hpac.runtime-invocation-approval.v2" in HPAC
    assert "`HPAC-CHALLENGE/2.0`" in HPAC
    assert "`HPAC-PROOF/2.0`" in HPAC
    assert "does not change\n  `HPAC-CHALLENGE/2.0`, `HPAC-PROOF/2.0`" in HPAC


def test_proof_lifecycle_event_schema_path_and_binding_are_exact() -> None:
    assert "HPAC-PROOF-LIFECYCLE-EVENT/2.0" in HPAC
    assert "<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/lifecycle/<sequence-four-digits>.json" in HPAC
    for field in (
        "`approval_id`",
        "`invocation_id`",
        "`attempt_id`",
        "`principal_id`",
        "`credential_id`",
        "`mechanism_id`",
        "`approval_subject_digest`",
        "`trusted_presentation_ref`",
        "`challenge_digest`",
    ):
        assert field in HPAC


def test_lifecycle_sequence_separates_raw_assertion_proof_and_binding() -> None:
    expected = (
        "`0 CHALLENGE_CREATED`",
        "`1 ASSERTION_RECEIVED`",
        "`2 PROOF_VERIFIED`",
        "`3 PROOF_VERIFIED_AND_BOUND`",
    )
    positions = [HPAC.index(token) for token in expected]
    assert positions == sorted(positions)
    assert "An unverified response is transient" in HPAC
    assert "it is not a\n  `HumanAuthenticationProof`" in HPAC


def test_gate5_binding_is_durable_idempotent_and_non_consuming() -> None:
    assert "Gate 5 reruns HPAC-REQ-054" in HPAC
    assert "sequence 3" in HPAC
    assert "byte-identical sequence-3 event" in HPAC_FLAT
    gate5 = RDGO[RDGO.index("## 6. Gate 5"):RDGO.index("## 7. Gate 6")]
    assert "does not consume" in gate5
    assert "PROOF_VERIFIED_AND_BOUND" in gate5


def test_gate9_has_one_canonical_atomic_consumption_artifact() -> None:
    for token in (
        "RuntimeInvocationAuthorityConsumption",
        "HPAC-AUTHORITY-CONSUMPTION/2.0",
        "<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json",
        "single authoritative fact",
        "atomic, create-only, same-filesystem durable commit",
        "final artifact absent",
        "one complete valid final artifact present",
    ):
        assert token in HPAC_FLAT


def test_gate9_consumption_binds_all_authority_and_attempt_identities() -> None:
    authority = HPAC[HPAC.index("| `authority_binding`"):HPAC.index("| `pb_binding`")]
    for field in (
        "`approval_id`",
        "`approval_digest`",
        "`proof_id`",
        "`proof_digest`",
        "`approval_subject_digest`",
        "`trusted_presentation_ref`",
        "`challenge_digest`",
    ):
        assert field in authority
    assert "`invocation_id`, `attempt_id`, `idempotency_key`" in HPAC


def test_gate9_revalidation_closes_revocation_expiry_toctou() -> None:
    assert "Revocation, expiry, invalidation, or drift after gate 5 but before" in HPAC
    gate9 = RDGO[RDGO.index("## 10. Gate 9"):RDGO.index("## 11. Gate 10")]
    # RDGO-001 v3.1 (.1R.15.4 — V-15-1): the "Immediately before
    # compare-and-create ... while holding the serialization boundary"
    # wording is normalized to the create-only-linearization + zero-I/O
    # S1/S2 authority-generation-token re-check model.
    assert "Immediately before that create" in gate9
    assert "revalidation battery" in gate9
    assert "no TOCTOU allowance" in gate9


def test_crash_and_retry_outcomes_are_deterministic() -> None:
    assert "absent means no effect" in HPAC
    assert "valid present means consumed" in HPAC_FLAT
    assert "ambiguous or corrupt means fail closed" in HPAC_FLAT
    assert "every retry requires a fresh invocation, attempt, presentation, challenge, proof, and approval" in HPAC_FLAT


def test_rdg_order_and_first_effect_remain_exact() -> None:
    gates = re.findall(r"^\|\s*(\d+)\s*\|", RDGO, flags=re.MULTILINE)
    assert gates[:11] == [str(i) for i in range(1, 12)]
    assert "Gate 10 is the first external execution effect" in RDGO
    assert "Gate count: 11 (unchanged)" in RDGO


def test_rihac_reserves_identity_and_requires_canonical_evidence() -> None:
    assert "reserves `approval_id` before the protected ceremony" in RIHAC
    assert "`TrustedApprovalPresentationEvidence` resolved and verified under HPAC-001 §39" in RIHAC_FLAT
    assert "HPAC-001 §41's canonical consumption path" in RIHAC


def test_no_authority_shortcut_or_cross_domain_substitution() -> None:
    assert "Caller-created principal, presentation, lifecycle, proof, approval, or projection objects" in HPAC_FLAT
    assert "HATP registry/evidence" in HPAC
    assert "zero authority, closing N2 at the contract layer" in HPAC_FLAT


def test_pbrd_remains_projection_only_and_pol005_remains_hard_deny() -> None:
    pbrd = PBRD_PATH.read_text()
    assert "PB SHALL NOT authenticate humans" in pbrd
    assert "RIHAC owns fresh authority validation" in pbrd
    assert "POL-005 production behavior: UNCHANGED" in pbrd


def test_contract_only_no_implementation_claim() -> None:
    assert "`HumanAuthenticator` implementation: NOT BUILT / NOT AUTHORIZED" in HPAC
    assert "**Real execution: UNAVAILABLE.**" in HPAC
    assert "**Real execution: UNAVAILABLE.**" in RIHAC
    assert "**Real execution: UNAVAILABLE.**" in RDGO
