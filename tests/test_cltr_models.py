"""Phase 135K — contract inventory and typed-model tests for src/pcae/cltr."""

from __future__ import annotations

import pytest

from pcae.cltr import schema
from pcae.cltr.enums import (
    FORBIDDEN_TRANSITIONS,
    INVARIANT_CATALOG,
    PERMITTED_TRANSITIONS,
    ALL_LIFECYCLE_STATE_NAMES,
    LifecycleState,
    RepresentationKind,
    TransitionType,
)
from pcae.cltr.models import CommitOwnershipEntry, ProductionCltrRecord, ShadowTransitionInput
from pcae.cltr.enums import CertificationState


def test_exact_14_lifecycle_states():
    assert len(ALL_LIFECYCLE_STATE_NAMES) == 14
    assert len(set(ALL_LIFECYCLE_STATE_NAMES)) == 14


def test_exact_16_transitions():
    assert len(list(TransitionType)) == 16
    assert len({t.value for t in TransitionType}) == 16


def test_exact_14_forbidden_transitions():
    assert len(FORBIDDEN_TRANSITIONS) == 14
    assert set(FORBIDDEN_TRANSITIONS).isdisjoint(set(PERMITTED_TRANSITIONS))


def test_exact_37_invariants():
    assert len(INVARIANT_CATALOG) == 37
    assert len({row[0] for row in INVARIANT_CATALOG}) == 37


def test_exact_15_representation_kinds():
    assert len(list(RepresentationKind)) == 15
    assert len({k.value for k in RepresentationKind}) == 15


def test_schema_version_is_1_0_1():
    assert schema.SCHEMA_VERSION == "1.0.1"
    assert schema.is_supported_schema_version("1.0.1") is True


def test_schema_version_1_0_0_is_unsupported():
    assert schema.is_supported_schema_version("1.0.0") is False


def test_schema_version_future_unsupported():
    assert schema.is_supported_schema_version("2.0.0") is False
    assert schema.is_supported_schema_version("1.1.0") is False
    assert schema.is_supported_schema_version("") is False


def _minimal_record(**overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id="135K-UNIT",
        phase_id="135K-UNIT",
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.PROPOSE_TRANSITION,
        lifecycle_state=LifecycleState.PROPOSED,
        source_revision="abc123",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def test_record_construction_requires_transition_id():
    with pytest.raises(ValueError):
        _minimal_record(transition_id="")


def test_record_construction_requires_source_revision():
    with pytest.raises(ValueError):
        _minimal_record(source_revision="")


def test_record_rejects_unsupported_schema_version():
    with pytest.raises(ValueError):
        _minimal_record(schema_version="1.0.0")


def test_record_is_deeply_immutable():
    record = _minimal_record(certified_state={"a": {"b": 1}})
    with pytest.raises(Exception):
        record.certified_state["a"] = 2  # type: ignore[index]
    with pytest.raises(Exception):
        record.transition_id = "other"  # type: ignore[misc]


def test_commit_ownership_entry_requires_hash():
    with pytest.raises(ValueError):
        CommitOwnershipEntry(
            commit_hash="",
            repository_identity="repo",
            branch_identity="main",
            certification_state=CertificationState.UNVERIFIABLE,
        )


def test_shadow_transition_input_freezes_collections():
    inp = ShadowTransitionInput(
        entry_point="phase_complete",
        phase_id="135K",
        transition_type=TransitionType.CLOSE_SUCCESS,
        intended_lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        source_revision="abc",
        repository_identity="repo",
        branch_identity="main",
        notification_ids=["a", "b"],  # type: ignore[arg-type]
    )
    assert inp.notification_ids == ("a", "b")
    assert isinstance(inp.notification_ids, tuple)


def test_no_narrative_fallback_missing_source_revision_is_none_not_guessed():
    inp = ShadowTransitionInput(
        entry_point="phase_complete",
        phase_id="135K",
        transition_type=TransitionType.CLOSE_SUCCESS,
        intended_lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        source_revision=None,
        repository_identity="repo",
        branch_identity="main",
    )
    assert inp.source_revision is None
