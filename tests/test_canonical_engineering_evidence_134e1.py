"""Phase 134E.1 — focused tests for the Canonical Engineering Evidence
executable model (``pcae.core.canonical_engineering_evidence``).

This model is not yet active lifecycle authority (see the module's own
docstring). These tests exercise the model in isolation; regression
coverage for existing phase-report/notification/identity/finalization
behavior is provided by re-running the existing suites unchanged
(tests/test_phase_reports.py, tests/test_notifications.py,
tests/test_finalization_gate_enforcement.py, etc. — none of which import
or reference this new module).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from types import MappingProxyType

import pytest

from pcae.core import canonical_engineering_evidence as cee
from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CanonicalEngineeringEvidence,
    CommitPushInfo,
    CorrectionMetadata,
    EvidenceIdentity,
    EvidencePhaseIdentity,
    EvidenceProvenanceRecord,
    EvidenceRecordState,
    FindingClassification,
    FindingRecord,
    LimitationItem,
    PhaseClass,
    REQUIRED_APPLICABILITY_CATEGORIES,
    RepairRecord,
    RepositoryStateSnapshot,
    RuntimeStateSnapshot,
    SCHEMA_VERSION,
    UncertaintyItem,
)


def _identity(phase_id: str = "999X", version: int = 1, correction_of: str | None = None) -> EvidenceIdentity:
    return EvidenceIdentity(
        phase=EvidencePhaseIdentity(phase_id=phase_id, phase_name="Test Phase", source="cli_argument"),
        record_version=version,
        correction_of=correction_of,
    )


def _repo_state(**overrides) -> RepositoryStateSnapshot:
    defaults = dict(commit="abc1234", branch="main", pushed_status="pushed",
                     origin_main_head_count=0, clean=True)
    defaults.update(overrides)
    return RepositoryStateSnapshot(**defaults)


def _runtime_state(**overrides) -> RuntimeStateSnapshot:
    defaults = dict(runtime_state="Observed", maximum_capability="observe",
                     execution_availability="unavailable")
    defaults.update(overrides)
    return RuntimeStateSnapshot(**defaults)


def _commit_push(**overrides) -> CommitPushInfo:
    defaults = dict(commits=("abc1234",), pushed_status="pushed", origin_main_head_count=0)
    defaults.update(overrides)
    return CommitPushInfo(**defaults)


def _all_not_applicable() -> MappingProxyType:
    return MappingProxyType({c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES})


def _minimal_evidence(phase_class: PhaseClass, **overrides) -> CanonicalEngineeringEvidence:
    kwargs = dict(
        identity=_identity(),
        phase_class=phase_class,
        task_id=None,
        objective="minimal test objective",
        engineering_actions=(),
        architectural_findings=(),
        implementation_findings=(),
        verification_findings=(),
        defects_discovered=(),
        defects_repaired=(),
        incorrect_assumptions_corrected=(),
        technical_debt_reviewed=(),
        technical_debt_introduced=(),
        notable_engineering_knowledge=(),
        governance_results=(),
        test_results=(),
        repository_state=_repo_state(),
        runtime_state=_runtime_state(),
        no_go_confirmations=(),
        architectural_boundary_confirmations=(),
        track_progress="minimal track progress",
        recommended_next_phase="999Y",
        commit_and_push=_commit_push(),
        provenance=(),
        uncertainty=(),
        limitations=(),
        correction=CorrectionMetadata(),
        applicability=_all_not_applicable(),
        created_at="2026-01-01T00:00:00+00:00",
    )
    kwargs.update(overrides)
    return CanonicalEngineeringEvidence(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1-6: minimal valid evidence per phase class
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_class", list(PhaseClass))
def test_minimal_valid_evidence_per_phase_class(phase_class):
    ev = _minimal_evidence(phase_class)
    issues = ev.validate()
    if phase_class in (PhaseClass.IMPLEMENTATION, PhaseClass.VERIFICATION):
        # These two classes require their own mandatory-present category
        # (see _PHASE_CLASS_MANDATORY_PRESENT) -- the all-NOT_APPLICABLE
        # minimal fixture is deliberately invalid for them; confirmed
        # separately in test_phase_class_applicability_enforced below.
        assert any(i.code == "contradictory_applicability" for i in issues)
    else:
        assert issues == ()
        ev.finalize()


def test_minimal_valid_implementation_phase_evidence():
    app = dict(_all_not_applicable())
    app["implementation_findings"] = Applicability.PRESENT
    ev = _minimal_evidence(
        PhaseClass.IMPLEMENTATION,
        implementation_findings=(
            FindingRecord("F1", FindingClassification.CONFIRMED, "did the thing", "module_x"),
        ),
        applicability=MappingProxyType(app),
    )
    assert ev.validate() == ()
    ev.finalize()


def test_minimal_valid_verification_phase_evidence():
    app = dict(_all_not_applicable())
    app["verification_findings"] = Applicability.PRESENT
    ev = _minimal_evidence(
        PhaseClass.VERIFICATION,
        verification_findings=(
            FindingRecord("F1", FindingClassification.CONFIRMED, "verified the thing", "module_x"),
        ),
        applicability=MappingProxyType(app),
    )
    assert ev.validate() == ()
    ev.finalize()


# ─────────────────────────────────────────────────────────────────────────────
# 7: required phase identity
# ─────────────────────────────────────────────────────────────────────────────

def test_required_phase_identity():
    with pytest.raises(ValueError):
        EvidencePhaseIdentity(phase_id="", phase_name="x", source="cli_argument")
    with pytest.raises(ValueError):
        EvidencePhaseIdentity(phase_id="1", phase_name="", source="cli_argument")


def test_validate_flags_missing_phase_identity_defensively():
    # Construction already prevents an empty phase_id, but validate()
    # independently checks it too (defense in depth, deterministic result).
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    assert not any(i.code == "missing_phase_identity" for i in ev.validate())


# ─────────────────────────────────────────────────────────────────────────────
# 8: required task identity behavior
# ─────────────────────────────────────────────────────────────────────────────

def test_task_identity_optional_but_not_blank():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE, task_id=None)
    assert ev.validate() == ()
    ev_blank = _minimal_evidence(PhaseClass.ARCHITECTURE, task_id="   ")
    issues = ev_blank.validate()
    assert any(i.code == "invalid_task_identity" for i in issues)
    ev_present = _minimal_evidence(PhaseClass.ARCHITECTURE, task_id="20260101-0000-some-task")
    assert ev_present.validate() == ()


# ─────────────────────────────────────────────────────────────────────────────
# 9-10: phase-class applicability, explicit not-applicable handling
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_class_applicability_enforced():
    app = dict(_all_not_applicable())  # implementation_findings NOT_APPLICABLE
    ev = _minimal_evidence(PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app))
    issues = ev.validate()
    assert any(i.code == "contradictory_applicability" for i in issues)


def test_explicit_not_applicable_handling():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    assert ev.applicability["implementation_findings"] == Applicability.NOT_APPLICABLE
    d = ev.to_dict()
    assert d["applicability"]["implementation_findings"] == "not_applicable"


# ─────────────────────────────────────────────────────────────────────────────
# 11: unknown vs unavailable distinction
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_versus_unavailable_distinction():
    assert Applicability.UNKNOWN != Applicability.UNAVAILABLE
    app = dict(_all_not_applicable())
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app),
        limitations=(LimitationItem(
            category="data_gap", description="debt review data unavailable this phase",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    assert ev.validate() == ()

    app2 = dict(_all_not_applicable())
    app2["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev2 = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app2),
        limitations=(LimitationItem(
            category="data_gap", description="debt review data unavailable this phase",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    assert ev2.validate() == ()
    assert ev.applicability["technical_debt_reviewed"] != ev2.applicability["technical_debt_reviewed"]


# ─────────────────────────────────────────────────────────────────────────────
# 12-14: deterministic normalization, ordering, serialization
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_normalization_equivalent_input():
    ev1 = _minimal_evidence(PhaseClass.ARCHITECTURE)
    ev2 = _minimal_evidence(PhaseClass.ARCHITECTURE)
    assert ev1.to_dict(include_digest=False) == ev2.to_dict(include_digest=False)


def test_deterministic_ordering_of_applicability_keys():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    d = ev.to_dict()
    assert list(d["applicability"].keys()) == sorted(d["applicability"].keys())


def test_deterministic_serialization_byte_identical():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    s1 = json.dumps(ev.to_dict(include_digest=False), sort_keys=True)
    s2 = json.dumps(ev.to_dict(include_digest=False), sort_keys=True)
    assert s1 == s2


# ─────────────────────────────────────────────────────────────────────────────
# 15-16: round-trip serialization, stable record identity
# ─────────────────────────────────────────────────────────────────────────────

def test_round_trip_serialization():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE).finalize()
    d = ev.to_dict()
    rt = CanonicalEngineeringEvidence.from_dict(d)
    assert rt.to_dict() == d


def test_stable_record_identity():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE, identity=_identity(phase_id="42Z", version=1))
    assert ev.identity.evidence_id == "42Z#1"
    ev2 = _minimal_evidence(PhaseClass.ARCHITECTURE, identity=_identity(phase_id="42Z", version=1))
    assert ev.identity.evidence_id == ev2.identity.evidence_id


# ─────────────────────────────────────────────────────────────────────────────
# 17-18: stable digest, digest changes on material change
# ─────────────────────────────────────────────────────────────────────────────

def test_stable_digest_for_equivalent_evidence():
    ev1 = _minimal_evidence(PhaseClass.ARCHITECTURE, created_at="2026-01-01T00:00:00+00:00")
    ev2 = _minimal_evidence(PhaseClass.ARCHITECTURE, created_at="2026-06-06T12:00:00+00:00")
    # Different approved timestamps, otherwise equivalent content -> same digest.
    assert ev1.compute_digest() == ev2.compute_digest()


def test_digest_changes_on_material_evidence_change():
    ev1 = _minimal_evidence(PhaseClass.ARCHITECTURE, objective="objective A")
    ev2 = _minimal_evidence(PhaseClass.ARCHITECTURE, objective="objective B")
    assert ev1.compute_digest() != ev2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 19-20: rendering/delivery data excluded, secrets rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_and_delivery_data_excluded_from_model():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    d = ev.to_dict()
    forbidden_substrings = ("render", "telegram", "sink", "delivery", "notif")
    dumped = json.dumps(d).lower()
    for substr in forbidden_substrings:
        assert substr not in dumped, f"unexpected {substr!r} in serialized evidence"


def test_secrets_rejected():
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        objective="configured PCAE_TELEGRAM_BOT_TOKEN=123456:abcdefGHIJKLMNOPQRSTUVWXYZ0123456",
    )
    issues = ev.validate()
    assert any(i.code == "likely_secret_material" for i in issues)


def test_secrets_absent_does_not_flag():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE, objective="no secrets here")
    assert not any(i.code == "likely_secret_material" for i in ev.validate())


# ─────────────────────────────────────────────────────────────────────────────
# 21-22: finding classification validation, three-way representation
# ─────────────────────────────────────────────────────────────────────────────

def test_finding_classification_validation():
    with pytest.raises(ValueError):
        FindingClassification("not_a_real_classification")


def test_confirmed_non_blocking_blocking_representation():
    for classification in FindingClassification:
        f = FindingRecord("F1", classification, "desc", "component")
        assert f.to_dict()["classification"] == classification.value


# ─────────────────────────────────────────────────────────────────────────────
# 23: repair preserves original finding
# ─────────────────────────────────────────────────────────────────────────────

def test_repair_preserves_original_finding():
    original = FindingRecord("F1", FindingClassification.BLOCKING, "bad thing happened", "module_x")
    repair = RepairRecord(
        original_finding=original,
        repair_action="fixed the bad thing",
        affected_artifact="module_x.py",
        verification_evidence="test_module_x_fixed passed",
        resulting_status=FindingClassification.CONFIRMED,
    )
    d = repair.to_dict()
    assert d["original_finding"]["classification"] == "blocking"
    assert d["resulting_status"] == "confirmed"


def test_repair_rejects_already_confirmed_original():
    original = FindingRecord("F1", FindingClassification.CONFIRMED, "fine", "module_x")
    with pytest.raises(ValueError):
        RepairRecord(
            original_finding=original, repair_action="x", affected_artifact="y",
            verification_evidence="z", resulting_status=FindingClassification.CONFIRMED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 24: provenance completeness
# ─────────────────────────────────────────────────────────────────────────────

def test_provenance_completeness():
    prov = EvidenceProvenanceRecord(
        covers="test_results", source_artifact="pytest output",
        source_command="python -m pytest -m fast_green", source_phase_id="999X",
        derivation_path="direct capture", verification_state="verified",
    )
    assert prov.to_dict()["covers"] == "test_results"
    with pytest.raises(ValueError):
        EvidenceProvenanceRecord(
            covers="", source_artifact="x", source_command=None,
            source_phase_id=None, derivation_path="y", verification_state="z",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 25-27: uncertainty, limitations, cannot be silently discarded
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_representation():
    u = UncertaintyItem(
        category="data_gap", description="exact count not reconstructible",
        affected_evidence=("test_results",), source="incident review",
        verification_state="unresolved",
    )
    assert u.to_dict()["category"] == "data_gap"


def test_limitation_representation():
    lim = LimitationItem(
        category="tooling_gap", description="no durable receipt ledger",
        affected_evidence=("test_results",),
    )
    assert lim.to_dict()["category"] == "tooling_gap"


def test_uncertainty_and_limitations_cannot_be_silently_discarded():
    app = dict(_all_not_applicable())
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app),
        uncertainty=(), limitations=(),  # deliberately no disclosure
    )
    issues = ev.validate()
    assert any(i.code == "missing_uncertainty_disclosure" for i in issues)


# ─────────────────────────────────────────────────────────────────────────────
# 28-29: contradictory status rejection, invalid phase-class rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_contradictory_status_present_but_empty():
    app = dict(_all_not_applicable())
    app["engineering_actions"] = Applicability.PRESENT
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app))
    issues = ev.validate()
    assert any(i.code == "contradictory_status" for i in issues)


def test_contradictory_status_not_applicable_but_populated():
    app = dict(_all_not_applicable())
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app),
        engineering_actions=("did something",),
    )
    issues = ev.validate()
    assert any(i.code == "contradictory_status" for i in issues)


def test_invalid_phase_class_rejection():
    with pytest.raises(ValueError):
        PhaseClass("not_a_real_phase_class")


# ─────────────────────────────────────────────────────────────────────────────
# 30-31: invalid version rejection, duplicate identity rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_version_rejection():
    with pytest.raises(ValueError):
        _minimal_evidence(PhaseClass.ARCHITECTURE, schema_version="99.9")


def test_duplicate_finding_identifier_rejection():
    app = dict(_all_not_applicable())
    app["architectural_findings"] = Applicability.PRESENT
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app),
        architectural_findings=(
            FindingRecord("DUP", FindingClassification.CONFIRMED, "a", "x"),
            FindingRecord("DUP", FindingClassification.CONFIRMED, "b", "y"),
        ),
    )
    issues = ev.validate()
    assert any(i.code == "duplicate_finding_identifier" for i in issues)


# ─────────────────────────────────────────────────────────────────────────────
# 32: finalized evidence immutability
# ─────────────────────────────────────────────────────────────────────────────

def test_finalized_evidence_immutability():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE).finalize()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.objective = "mutated"
    with pytest.raises(ValueError):
        ev.finalize()  # already finalized


def test_finalize_never_mutates_draft_in_place():
    draft = _minimal_evidence(PhaseClass.ARCHITECTURE)
    finalized = draft.finalize()
    assert draft.state == EvidenceRecordState.DRAFT
    assert finalized.state == EvidenceRecordState.FINALIZED
    assert draft is not finalized


# ─────────────────────────────────────────────────────────────────────────────
# 33: correction/supersession metadata validation
# ─────────────────────────────────────────────────────────────────────────────

def test_correction_metadata_validation():
    with pytest.raises(ValueError):
        CorrectionMetadata(is_correction=True)  # missing supersedes/reason
    with pytest.raises(ValueError):
        CorrectionMetadata(supersedes_evidence_id="999X#1")  # set without is_correction
    ok = CorrectionMetadata(
        is_correction=True, supersedes_evidence_id="999X#1",
        reason="original had a factual error", authority="operator",
    )
    assert ok.to_dict()["is_correction"] is True


def test_correction_identity_consistency_enforced_at_evidence_level():
    correction = CorrectionMetadata(
        is_correction=True, supersedes_evidence_id="999X#1",
        reason="repair", authority="operator",
    )
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        identity=_identity(phase_id="999X", version=2, correction_of="999X#1"),
        correction=correction,
    )
    assert ev.validate() == ()

    mismatched = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        identity=_identity(phase_id="999X", version=2, correction_of="999X#1"),
        correction=CorrectionMetadata(
            is_correction=True, supersedes_evidence_id="999X#0",  # mismatch
            reason="repair", authority="operator",
        ),
    )
    issues = mismatched.validate()
    assert any(i.code == "correction_identity_mismatch" for i in issues)


# ─────────────────────────────────────────────────────────────────────────────
# 34-38: no model-specific behavior, no RI leakage, no notification
# dependency, no runtime mutation, no repository mutation
# ─────────────────────────────────────────────────────────────────────────────

def test_no_model_or_agent_specific_semantic_behavior():
    src = inspect.getsource(cee)
    lowered = src.lower()
    for marker in ("deepseek", "claude", "codex", "gpt", "gemini"):
        assert marker not in lowered


def test_no_repository_intelligence_authority_leakage():
    src = inspect.getsource(cee)
    assert "repository_intelligence" not in src.lower()


def test_no_notification_or_delivery_dependency():
    # Prose in the module docstring legitimately explains *why* this
    # module is disconnected from notification/delivery (mirroring
    # core/evidence.py's own convention) -- what matters is that no
    # concrete adapter/dispatch symbol is actually used or imported.
    src = inspect.getsource(cee)
    for marker in ("TelegramSink(", "dispatch(", "NotificationSink", "import notifications"):
        assert marker not in src


def test_no_runtime_state_mutation():
    rs = _runtime_state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        rs.runtime_state = "Unknown"


def test_no_repository_mutation_or_io():
    src = inspect.getsource(cee)
    for marker in ("open(", "subprocess", "os.system", "requests.", "urllib.request", "socket."):
        assert marker not in src


def test_module_has_zero_internal_pcae_imports():
    import ast
    tree = ast.parse(inspect.getsource(cee))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("pcae"), (
                f"unexpected internal PCAE import: {node.module}"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("pcae"), (
                    f"unexpected internal PCAE import: {alias.name}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# 39-40: byte determinism, fail-closed invalid input
# ─────────────────────────────────────────────────────────────────────────────

def test_byte_determinism_across_independent_constructions():
    ev1 = _minimal_evidence(PhaseClass.ARCHITECTURE)
    ev2 = _minimal_evidence(PhaseClass.ARCHITECTURE)
    b1 = json.dumps(ev1.to_dict(include_digest=False), sort_keys=True).encode()
    b2 = json.dumps(ev2.to_dict(include_digest=False), sort_keys=True).encode()
    assert b1 == b2


def test_fail_closed_invalid_input_missing_required_key():
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE)
    d = ev.to_dict()
    del d["objective"]
    with pytest.raises(KeyError):
        CanonicalEngineeringEvidence.from_dict(d)


def test_fail_closed_invalid_commit_hash():
    ev = _minimal_evidence(
        PhaseClass.ARCHITECTURE,
        commit_and_push=_commit_push(commits=("not-a-valid-hash!!",)),
    )
    issues = ev.validate()
    assert any(i.code == "invalid_commit" for i in issues)


def test_fail_closed_missing_required_applicability_category():
    incomplete = MappingProxyType({
        c: Applicability.NOT_APPLICABLE
        for c in list(REQUIRED_APPLICABILITY_CATEGORIES)[:-1]  # drop one
    })
    with pytest.raises(ValueError):
        _minimal_evidence(PhaseClass.ARCHITECTURE, applicability=incomplete)


def test_fail_closed_does_not_coerce_invalid_evidence():
    """validate() reports issues; it never silently repairs them."""
    app = dict(_all_not_applicable())
    app["engineering_actions"] = Applicability.PRESENT  # contradictory, empty tuple
    ev = _minimal_evidence(PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app))
    assert ev.applicability["engineering_actions"] == Applicability.PRESENT
    assert ev.engineering_actions == ()  # untouched, not coerced
    with pytest.raises(ValueError):
        ev.finalize()
