from __future__ import annotations

import pytest

from pcae.cltr_prototype.models import (
    ALL_LIFECYCLE_STATE_NAMES,
    EvidenceRef,
    EvidenceType,
    EvidenceVerificationStatus,
    Identity,
    OrthogonalFlag,
    SpineState,
    TERMINAL_SPINE_STATES,
    TransitionRecord,
)


def test_all_14_lifecycle_states_named():
    assert len(ALL_LIFECYCLE_STATE_NAMES) == 14
    assert len(set(ALL_LIFECYCLE_STATE_NAMES)) == 14


def test_spine_state_has_12_members():
    assert len(list(SpineState)) == 12


def test_orthogonal_flag_has_2_members():
    assert len(list(OrthogonalFlag)) == 2


def test_identity_requires_all_fields():
    with pytest.raises(ValueError):
        Identity(transition_id="", phase_id="135F", repository_identity="r", branch_identity="main")
    with pytest.raises(ValueError):
        Identity(transition_id="t1", phase_id="", repository_identity="r", branch_identity="main")


def test_identity_task_id_optional():
    ident = Identity(transition_id="t1", phase_id="135F", repository_identity="r", branch_identity="main")
    assert ident.task_id is None


def test_transition_record_requires_source_revision():
    ident = Identity(transition_id="t1", phase_id="135F", repository_identity="r", branch_identity="main")
    with pytest.raises(ValueError):
        TransitionRecord(identity=ident, spine_state=SpineState.PROPOSED, source_revision="")


def test_transition_record_certified_requires_certified_state():
    ident = Identity(transition_id="t1", phase_id="135F", repository_identity="r", branch_identity="main")
    with pytest.raises(ValueError):
        TransitionRecord(identity=ident, spine_state=SpineState.CERTIFIED, source_revision="abc")


def test_with_updates_produces_new_immutable_value():
    ident = Identity(transition_id="t1", phase_id="135F", repository_identity="r", branch_identity="main")
    record = TransitionRecord(identity=ident, spine_state=SpineState.PROPOSED, source_revision="abc")
    updated = record.with_updates(spine_state=SpineState.CERTIFYING)
    assert record.spine_state == SpineState.PROPOSED  # original unchanged
    assert updated.spine_state == SpineState.CERTIFYING
    assert record is not updated


def test_transition_record_nested_authoritative_content_is_immutable():
    ident = Identity(transition_id="immutable-1", phase_id="135F", repository_identity="repo", branch_identity="main")
    record = TransitionRecord(
        identity=ident,
        spine_state=SpineState.CERTIFIED,
        source_revision="rev",
        certified_state={"nested": {"value": 1}},
        timestamps={"CERTIFIED": "now"},
    )
    with pytest.raises(TypeError):
        record.certified_state["nested"]["value"] = 2
    with pytest.raises(TypeError):
        record.timestamps["MUTATED"] = "later"


def test_is_terminal():
    ident = Identity(transition_id="t1", phase_id="135F", repository_identity="r", branch_identity="main")
    for state in SpineState:
        record = TransitionRecord(
            identity=ident,
            spine_state=state,
            source_revision="abc",
            certified_state={"x": 1} if state not in (SpineState.PROPOSED, SpineState.CERTIFYING, SpineState.FAILED_PRE_CERT) else None,
        )
        assert record.is_terminal == (state in TERMINAL_SPINE_STATES)


def test_evidence_ref_requires_ids():
    with pytest.raises(ValueError):
        EvidenceRef(
            evidence_id="",
            evidence_type=EvidenceType.REPORT,
            transition_id="t1",
            phase_id="135F",
            verification_status=EvidenceVerificationStatus.BOUND,
        )
