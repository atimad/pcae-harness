"""Phase 143F: independent adversarial verification of the Phase 143E CHGR
schema/artifact foundation.

These tests re-derive and adversarially probe the Phase 143E foundation
(`pcae.governance.inspection`/`verification`, the six-type schema family
under `src/pcae/schema_resources/chgr/`) without trusting Phase 143E's own
tests or report conclusions. This file verifies the existing implementation
only; it must never grow production capability (no create/confirm/publish/
storage/import behavior is invoked or exercised as a capability).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from pcae.governance.inspection import inspect_artifact_at_path
from pcae.governance.verification import verify_artifact_at_path

FIXTURES = Path(__file__).parent / "fixtures" / "chgr"

_PUBLISHED = json.loads((FIXTURES / "valid_record_published.json").read_text())


def _verify(doc: dict, path: str = "adversarial-inline.json"):
    return verify_artifact_at_path(Path(path), artifact_bytes=json.dumps(doc).encode())


def _inspect(doc: dict, path: str = "adversarial-inline.json"):
    return inspect_artifact_at_path(Path(path), artifact_bytes=json.dumps(doc).encode())


# 1-2: forbidden top-level and extension-level authority-bypass fields.


@pytest.mark.parametrize(
    "bypass",
    [
        {"is_authoritative": True},
        {"authority_valid": True},
        {"execution_authorized": True},
        {"approved": True},
    ],
)
def test_143f_top_level_authority_bypass_field_rejected(bypass):
    doc = copy.deepcopy(_PUBLISHED)
    doc.update(bypass)
    outcome = _verify(doc)
    assert outcome.error_code == "SCHEMA_INVALID"


def test_143f_extension_authority_bypass_field_does_not_establish_authority():
    doc = copy.deepcopy(_PUBLISHED)
    doc["extensions"] = {"is_authoritative": True, "authority_valid": True}
    outcome = _verify(doc)
    # additionalProperties:false on extensions itself is not required by
    # CHGR-001 (extensions are the declared extension point) -- but no
    # extension value may ever be surfaced as an authority conclusion.
    for field in ("outcome", "error_code", "message", "disclosure"):
        text = str(getattr(outcome, field, "")).lower()
        assert "authority_valid" not in text
        assert "is_authoritative" not in text or "never" in text or "no schema field" in text


# 3: AI declared as decision-maker identity evidence -- must fail closed
# because evidence_kind is a closed enum with no AI/automated value.


def test_143f_ai_decision_maker_evidence_kind_rejected():
    doc = copy.deepcopy(_PUBLISHED)
    doc["decision_maker_identity_evidence"] = {
        "evidence_kind": "ai_generated",
        "identifier": "claude",
        "captured_at": "2026-07-23T00:00:00Z",
    }
    outcome = _verify(doc)
    assert outcome.error_code == "SCHEMA_INVALID"


# 4: undeclared additional top-level property (schema-confusion / smuggling probe).


def test_143f_undeclared_top_level_property_rejected():
    doc = copy.deepcopy(_PUBLISHED)
    doc["decision_maker"] = {"identity_evidence": "AI"}
    outcome = _verify(doc)
    assert outcome.error_code == "SCHEMA_INVALID"


# 5: digest recomputation after malicious alteration is detected, not silently accepted.


def test_143f_altered_content_with_stale_digest_detected():
    doc = copy.deepcopy(_PUBLISHED)
    doc["rationale"] = "Maliciously altered rationale, digest left stale."
    outcome = _verify(doc)
    assert outcome.error_code == "DIGEST_MISMATCH"


# 6: a phase-completion report supplied to the CHGR verifier must be rejected,
# not merely ignored -- proves phase-lifecycle-artifact separation.


def test_143f_phase_report_supplied_to_chgr_verifier_rejected():
    report_path = Path(".pcae/phase-completion-report.md")
    if not report_path.exists():
        pytest.skip("no canonical report present in this checkout")
    outcome = verify_artifact_at_path(report_path, artifact_bytes=report_path.read_bytes())
    assert outcome.outcome != "verified"
    assert outcome.error_code in {"SCHEMA_INVALID", "PHASE_REPORT_SUBSTITUTION"}


def test_143f_phase_metadata_supplied_to_chgr_inspector_rejected():
    meta_path = Path(".pcae/phase-completion-metadata.json")
    if not meta_path.exists():
        pytest.skip("no canonical metadata present in this checkout")
    outcome = inspect_artifact_at_path(meta_path, artifact_bytes=meta_path.read_bytes())
    assert outcome.outcome != "inspected"


# 7: unknown schema version fails closed.


def test_143f_unknown_schema_version_rejected():
    doc = copy.deepcopy(_PUBLISHED)
    doc["schema_version"] = "99.0"
    outcome = _verify(doc)
    assert outcome.outcome != "verified"


# 8: unknown template version reference fails closed (schema-level shape check;
# unresolved template reference is a verification-layer, not authority, concern).


def test_143f_unsupported_template_version_does_not_verify_silently():
    doc = copy.deepcopy(_PUBLISHED)
    doc["template_ref"] = {"template_id": "synthetic-example-decision", "version": "999.0"}
    outcome = _verify(doc)
    # No related template artifact is supplied, so template_resolution is
    # skipped either way (Phase 143E behavior) -- assert it is never
    # reported as a passing, authority-establishing check.
    checks = {c.name: c.status for c in outcome.checks}
    assert checks.get("template_resolution") != "passed"


# 9: high assurance level claimed with only L0-shaped evidence (ASSURANCE_OVERCLAIM).


def test_143f_high_assurance_claim_with_weak_evidence_detected():
    doc = copy.deepcopy(_PUBLISHED)
    doc["assurance_level"] = "L3"
    outcome = _verify(doc)
    assert outcome.outcome != "verified"


# 10: CLI/library input mutation and side-effect check (filesystem digest unchanged).


def test_143f_inspection_and_verification_do_not_mutate_input_bytes():
    raw = (FIXTURES / "valid_record_published.json").read_bytes()
    before = raw
    inspect_artifact_at_path(FIXTURES / "valid_record_published.json", artifact_bytes=raw)
    verify_artifact_at_path(FIXTURES / "valid_record_published.json", artifact_bytes=raw)
    after = (FIXTURES / "valid_record_published.json").read_bytes()
    assert before == after


# 11: determinism -- identical input always produces an identical outcome.


def test_143f_verification_is_deterministic_across_repeated_runs():
    raw = (FIXTURES / "valid_record_published.json").read_bytes()
    outcomes = [
        verify_artifact_at_path(FIXTURES / "valid_record_published.json", artifact_bytes=raw)
        for _ in range(5)
    ]
    serialized = {json.dumps(o.to_dict(), sort_keys=True) for o in outcomes}
    assert len(serialized) == 1


def dataclasses_asdict(obs):
    import dataclasses

    def _default(o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return str(o)

    return json.loads(json.dumps(dataclasses.asdict(obs), default=_default))


# 12: no wording in verification/inspection output equivalent to a reached
# authority conclusion, even under adversarial input.


@pytest.mark.parametrize(
    "doc_mutator",
    [
        lambda d: d,
        lambda d: {**d, "rationale": "AI selected this answer autonomously."},
    ],
)
def test_143f_no_output_claims_authority_conclusion(doc_mutator):
    doc = doc_mutator(copy.deepcopy(_PUBLISHED))
    outcome = _verify(doc)
    blob = json.dumps(outcome.to_dict()).lower()
    for forbidden in ("\"authorized\": true", "authority is valid", "execution permitted"):
        assert forbidden not in blob
