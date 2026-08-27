"""Tests for Phase 149O.20L.7O.3W — `RuntimeInvocationApproval` model,
RIASC-001 v1.0 schema shape, digest canonicalization, closed-field
policy, and the `pcae.prompt-semantic.v1` canonicalizer.

Pure in-process, zero subprocess/network/credential access, pytest-xdist
safe.
"""

from __future__ import annotations

import copy

import pytest

from pcae.core import runtime_authority as ra

from _rdw3w_helpers import build_approval


def test_valid_approval_passes_schema_shape_validation():
    approval = build_approval()
    assert ra.validate_riasc_schema_shape(approval.to_dict()) == ()


def test_exactly_sixteen_required_top_level_fields():
    approval = build_approval()
    data = approval.to_dict()
    assert set(data.keys()) == {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "approval_id",
        "record_digest",
        "created_at",
        "expires_at",
        "subject",
        "governance_context",
        "prompt_hash_profile",
        "approval_scope",
        "adapter_binding",
        "freshness_snapshot",
        "provenance",
        "attempt_limit",
    }
    assert len(data) == 16


def test_exactly_five_member_subject():
    approval = build_approval()
    assert set(approval.subject.to_dict().keys()) == {
        "invocation_id",
        "runtime_target_id",
        "prompt_hash",
        "repository_identity",
        "task_id",
    }


@pytest.mark.parametrize("field", [
    "schema_id", "schema_version", "contract_version", "record_type",
    "approval_id", "record_digest", "created_at", "expires_at", "subject",
    "governance_context", "prompt_hash_profile", "approval_scope",
    "adapter_binding", "freshness_snapshot", "provenance", "attempt_limit",
])
def test_missing_required_field_fails_closed(field):
    data = build_approval().to_dict()
    del data[field]
    issues = ra.validate_riasc_schema_shape(data)
    assert any("missing_field" in i for i in issues), issues


def test_unknown_top_level_field_rejected():
    data = build_approval().to_dict()
    data["extra_field"] = "not allowed"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("unknown_field:extra_field" in i for i in issues)


@pytest.mark.parametrize("shortcut_key", [
    "approved", "authorized", "permission", "pb_allow", "execution_allowed",
])
def test_authority_shortcut_field_rejected_anywhere_in_document(shortcut_key):
    data = build_approval().to_dict()
    data["subject"][shortcut_key] = True
    issues = ra.validate_riasc_schema_shape(data)
    assert any("forbidden_authority_shortcut" in i for i in issues), issues


def test_authority_shortcut_rejected_at_root():
    data = build_approval().to_dict()
    data["approved"] = True
    issues = ra.validate_riasc_schema_shape(data)
    assert any("forbidden_authority_shortcut" in i or "unknown_field:approved" in i for i in issues)


def test_no_model_field_is_named_an_authority_shortcut():
    """RIASC-001 §0 extends to the in-memory representation itself, not
    just the wire document."""
    approval = build_approval()
    for obj in (
        approval, approval.subject, approval.governance_context,
        approval.approval_scope, approval.adapter_binding,
        approval.freshness_snapshot, approval.provenance,
    ):
        field_names = set(vars(obj).keys())
        assert field_names.isdisjoint(ra.FORBIDDEN_AUTHORITY_SHORTCUT_KEYS)


def test_wrong_type_fails_closed():
    data = build_approval().to_dict()
    data["attempt_limit"] = 2
    issues = ra.validate_riasc_schema_shape(data)
    assert any("attempt_limit" in i for i in issues)


def test_bad_contract_version_fails_closed():
    data = build_approval().to_dict()
    data["contract_version"] = "RIHAC-001/9.9"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("contract_version" in i for i in issues)


def test_bad_schema_version_fails_closed():
    data = build_approval().to_dict()
    data["schema_version"] = "2.0"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("schema_version" in i for i in issues)


def test_malformed_approval_id_fails_closed():
    data = build_approval().to_dict()
    data["approval_id"] = "not-a-valid-id"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("approval_id" in i for i in issues)


def test_malformed_invocation_id_fails_closed():
    data = build_approval().to_dict()
    data["subject"]["invocation_id"] = "inv-tooshort"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("invocation_id" in i for i in issues)


def test_malformed_sha256_field_fails_closed():
    data = build_approval().to_dict()
    data["subject"]["prompt_hash"] = "not-hex"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("prompt_hash" in i for i in issues)


def test_malformed_timestamp_fails_closed():
    data = build_approval().to_dict()
    data["created_at"] = "not-a-timestamp"
    issues = ra.validate_riasc_schema_shape(data)
    assert any("created_at" in i for i in issues)


@pytest.mark.parametrize("nested_obj_key,unknown_key", [
    ("subject", "extra"), ("governance_context", "extra"),
    ("approval_scope", "extra"), ("adapter_binding", "extra"),
    ("freshness_snapshot", "extra"), ("provenance", "extra"),
])
def test_closed_nested_objects_reject_unknown_fields(nested_obj_key, unknown_key):
    data = build_approval().to_dict()
    data[nested_obj_key][unknown_key] = "not allowed"
    issues = ra.validate_riasc_schema_shape(data)
    assert any(f"{nested_obj_key}_unknown_field:{unknown_key}" in i for i in issues)


def test_governance_context_session_id_optional_present_when_session_scoped():
    approval = build_approval(session_id="sess-123")
    assert approval.governance_context.session_id == "sess-123"
    assert ra.validate_riasc_schema_shape(approval.to_dict()) == ()


def test_governance_context_absent_session_means_not_session_scoped():
    approval = build_approval()
    assert approval.governance_context.session_id is None
    assert "session_id" not in approval.to_dict()["governance_context"]


# ── Digest canonicalization (RIASC-001 §8) ──────────────────────────────


def test_record_digest_matches_recomputation():
    approval = build_approval()
    assert ra.compute_record_digest(approval) == approval.record_digest


def test_record_digest_changes_when_any_field_changes():
    approval = build_approval()
    tampered = ra.RuntimeInvocationApproval(
        **{**approval.__dict__, "created_at": "2026-08-27T00:00:01Z"}
    )
    assert ra.compute_record_digest(tampered) != approval.record_digest


def test_record_digest_excludes_itself_from_payload():
    approval = build_approval()
    payload = approval.digest_payload()
    assert "record_digest" not in payload


def test_record_digest_is_deterministic():
    a1 = build_approval(created_at="2026-08-27T00:00:00Z", expires_at="2026-08-27T01:00:00Z")
    # Two structurally-identical-but-distinct approvals still each satisfy
    # digest recomputation independently.
    assert ra.compute_record_digest(a1) == a1.record_digest


def test_nfc_normalization_produces_stable_digest():
    """A precomposed vs. decomposed Unicode form of the same string must
    canonicalize to the same digest (RIASC-001 §8 step 2)."""
    precomposed = "café"  # é as one code point
    decomposed = "café"  # e + combining acute accent
    assert precomposed != decomposed  # sanity: genuinely different bytes
    d1 = ra._digest({"x": precomposed})
    d2 = ra._digest({"x": decomposed})
    assert d1 == d2


# ── pcae.prompt-semantic.v1 canonicalizer (RIHAC-001 §10) ───────────────


def test_prompt_hash_deterministic_for_identical_components():
    c = [ra.PromptSemanticComponent(kind="system", content="hello")]
    assert ra.compute_prompt_semantic_hash(c) == ra.compute_prompt_semantic_hash(c)


def test_prompt_hash_changes_on_single_character_change():
    c1 = [ra.PromptSemanticComponent(kind="system", content="hello")]
    c2 = [ra.PromptSemanticComponent(kind="system", content="hellp")]
    assert ra.compute_prompt_semantic_hash(c1) != ra.compute_prompt_semantic_hash(c2)


def test_prompt_hash_changes_on_component_order_change():
    c1 = [
        ra.PromptSemanticComponent(kind="a", content="1"),
        ra.PromptSemanticComponent(kind="b", content="2"),
    ]
    c2 = list(reversed(c1))
    assert ra.compute_prompt_semantic_hash(c1) != ra.compute_prompt_semantic_hash(c2)


def test_prompt_hash_normalizes_crlf_to_lf():
    c1 = [ra.PromptSemanticComponent(kind="system", content="line1\r\nline2")]
    c2 = [ra.PromptSemanticComponent(kind="system", content="line1\nline2")]
    assert ra.compute_prompt_semantic_hash(c1) == ra.compute_prompt_semantic_hash(c2)


def test_prompt_hash_normalizes_bare_cr_to_lf():
    c1 = [ra.PromptSemanticComponent(kind="system", content="line1\rline2")]
    c2 = [ra.PromptSemanticComponent(kind="system", content="line1\nline2")]
    assert ra.compute_prompt_semantic_hash(c1) == ra.compute_prompt_semantic_hash(c2)


def test_prompt_hash_does_not_trim_or_collapse_whitespace():
    c1 = [ra.PromptSemanticComponent(kind="system", content="  hello  ")]
    c2 = [ra.PromptSemanticComponent(kind="system", content="hello")]
    assert ra.compute_prompt_semantic_hash(c1) != ra.compute_prompt_semantic_hash(c2)


def test_prompt_hash_is_64_lowercase_hex():
    digest = ra.compute_prompt_semantic_hash([ra.PromptSemanticComponent(kind="a", content="b")])
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


# ── Approval creation invariants ────────────────────────────────────────


def test_create_approval_rejects_expiry_not_after_created():
    with pytest.raises(ValueError):
        build_approval(created_at="2026-08-27T01:00:00Z", expires_at="2026-08-27T00:00:00Z")


def test_create_approval_rejects_expiry_equal_created():
    with pytest.raises(ValueError):
        build_approval(created_at="2026-08-27T00:00:00Z", expires_at="2026-08-27T00:00:00Z")


def test_create_approval_rejects_unknown_identity_evidence_kind():
    with pytest.raises(ValueError):
        ra.create_runtime_invocation_approval(
            subject=build_approval().subject,
            governance_context=ra.GovernanceContext(phase_id="p"),
            approval_scope=build_approval().approval_scope,
            adapter_binding=build_approval().adapter_binding,
            freshness_snapshot=build_approval().freshness_snapshot,
            approver_id="atila-madai",
            identity_evidence_kind="magic_shortcut",
            created_at="2026-08-27T00:00:00Z",
            expires_at="2026-08-27T01:00:00Z",
        )


def test_approval_id_matches_ria_pattern():
    approval = build_approval()
    assert ra.is_valid_approval_id(approval.approval_id)


def test_approval_ids_are_unique_across_creations():
    a1 = build_approval()
    a2 = build_approval()
    assert a1.approval_id != a2.approval_id


def test_provenance_producer_is_fixed_trusted_component():
    approval = build_approval()
    assert approval.provenance.producer_component == ra.PRODUCER_COMPONENT_V1


def test_provenance_mechanism_is_fixed_v1_mechanism():
    approval = build_approval()
    assert approval.provenance.approval_mechanism == ra.APPROVAL_MECHANISM_V1
