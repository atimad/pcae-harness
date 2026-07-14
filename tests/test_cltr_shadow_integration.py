"""Phase 135K — shadow integration service and feature-flag tests."""

from __future__ import annotations

import pytest

from pcae.cltr.enums import CertificationState, LifecycleState, NotificationState, TransitionType
from pcae.cltr.models import CommitOwnershipEntry, EvidenceReference, ShadowTransitionInput
from pcae.cltr.persistence import list_generations, read_current_generation
from pcae.cltr.shadow import (
    FEATURE_FLAG_ENV_VAR,
    is_shadow_enabled,
    observe_finalized_transition,
    observe_finalized_transition_best_effort,
)


def _input(**overrides) -> ShadowTransitionInput:
    fields = dict(
        entry_point="phase_complete",
        phase_id="135K-SHADOW",
        transition_type=TransitionType.CLOSE_SUCCESS,
        intended_lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        source_revision="abc123",
        repository_identity="repo",
        branch_identity="main",
        report_id="r1", report_digest="a" * 64,
        metadata_id="m1", metadata_digest="b" * 64,
        snapshot_id="s1", snapshot_digest="c" * 64,
        promotion_id="p1",
        notification_ids=("n1",),
        notification_state=NotificationState.CONFIRMED,
        receipt_id="rcpt1",
        phase_commit_ownership=(
            CommitOwnershipEntry(commit_hash="deadbeef", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
        ),
        evidence_refs=(EvidenceReference(evidence_id="e1", evidence_kind="test_suite", reference="pytest::fast_green"),),
    )
    fields.update(overrides)
    return ShadowTransitionInput(**fields)


def test_disabled_flag_is_a_pure_no_op(tmp_path, monkeypatch):
    monkeypatch.delenv(FEATURE_FLAG_ENV_VAR, raising=False)
    assert is_shadow_enabled() is False
    root = tmp_path / "cltr-shadow"
    result = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    assert result is None
    assert not root.exists()


def test_enabled_true_variants(monkeypatch):
    for value in ("1", "true", "TRUE", "yes", "Yes"):
        monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, value)
        assert is_shadow_enabled() is True
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "0")
    assert is_shadow_enabled() is False
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "")
    assert is_shadow_enabled() is False


def test_enabled_publishes_a_generation(tmp_path, monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "true")
    root = tmp_path / "cltr-shadow"
    result = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    assert result.status == "published"
    generation = read_current_generation(root)
    assert generation["record"]["phase_id"] == "135K-SHADOW"
    assert generation["record"]["shadow_mode"] is True
    assert generation["record"]["authoritative"] is False


def test_missing_mandatory_input_produces_explicit_failure_never_a_guess(tmp_path):
    root = tmp_path / "cltr-shadow"
    incomplete = _input(source_revision=None)
    result = observe_finalized_transition(incomplete, shadow_root=root)
    assert result.status == "missing_mandatory_input"
    assert "source_revision" in result.construction_errors
    assert list_generations(root) == []


def test_missing_phase_id_is_explicit_failure(tmp_path):
    root = tmp_path / "cltr-shadow"
    incomplete = _input(phase_id="")
    result = observe_finalized_transition(incomplete, shadow_root=root)
    assert result.status == "missing_mandatory_input"
    assert "phase_id" in result.construction_errors


def test_certified_content_missing_produces_validation_failure(tmp_path):
    root = tmp_path / "cltr-shadow"
    incomplete = _input(report_id=None, report_digest=None)
    result = observe_finalized_transition(incomplete, shadow_root=root)
    assert result.status == "validation_failed"
    assert result.validation_errors


def test_invariant_blocking_failure_never_publishes(tmp_path):
    root = tmp_path / "cltr-shadow"
    # No evidence_refs and no limitations -> CLTR-EVID-1 fails.
    bad = _input(evidence_refs=())
    result = observe_finalized_transition(bad, shadow_root=root)
    assert result.status == "invariant_failed"
    assert list_generations(root) == []


def test_shadow_result_never_authoritative(tmp_path, monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "true")
    root = tmp_path / "cltr-shadow"
    result = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    assert result.shadow_mode is True
    assert result.authoritative is False


def test_idempotent_repeat_invocation_no_duplicate_current_state(tmp_path, monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "true")
    root = tmp_path / "cltr-shadow"
    r1 = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    r2 = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    assert r1.status == "published"
    assert r2.status == "published"
    assert r1.record_digest == r2.record_digest
    assert len(list_generations(root)) == 1


def test_unexpected_exception_is_contained_never_raised(tmp_path, monkeypatch):
    monkeypatch.setenv(FEATURE_FLAG_ENV_VAR, "true")
    root = tmp_path / "cltr-shadow"

    import pcae.cltr.shadow as shadow_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated unexpected internal failure")

    monkeypatch.setattr(shadow_module, "observe_finalized_transition", _boom)
    result = observe_finalized_transition_best_effort(_input(), shadow_root=root)
    assert result is not None
    assert result.status == "publish_failed"
    assert "simulated unexpected internal failure" in result.limitations[0]
