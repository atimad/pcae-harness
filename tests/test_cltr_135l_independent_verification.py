"""Phase 135L — independent adversarial verification tests.

These tests reproduce findings from the 135L independent verification of the
135K production shadow integration (see
docs/PHASE_135_PRODUCTION_CLTR_SHADOW_INTEGRATION_INDEPENDENT_VERIFICATION.md).
They are written fresh against production behavior, not the 135K fixtures,
and exercise the actual production call site rather than only the CLTR
package in isolation.
"""

from __future__ import annotations

import inspect
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

from pcae.cltr.enums import CertificationState, LifecycleState, NotificationState, TransitionType
from pcae.cltr.models import CommitOwnershipEntry, EvidenceReference, ShadowTransitionInput
from pcae.cltr.persistence import ConflictingGenerationError, read_current_pointer
from pcae.cltr.shadow import observe_finalized_transition


def _input(**overrides) -> ShadowTransitionInput:
    fields = dict(
        entry_point="phase_complete",
        phase_id="135L-VERIFY",
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
        evidence_refs=(EvidenceReference(evidence_id="e1", evidence_kind="test_suite", reference="pytest::135l"),),
    )
    fields.update(overrides)
    return ShadowTransitionInput(**fields)


class TestNoSubprocessNoSocket:
    """135L §34 — monkeypatch-based verification, not AST-inspection alone."""

    def test_full_publish_path_never_touches_subprocess_or_socket(self, tmp_path, monkeypatch):
        tripped = {"subprocess": 0, "socket": 0}

        def _trip(*a, **k):
            tripped["subprocess"] += 1
            raise AssertionError("subprocess invoked from CLTR shadow path")

        def _trip_socket(*a, **k):
            tripped["socket"] += 1
            raise AssertionError("socket invoked from CLTR shadow path")

        monkeypatch.setattr(subprocess, "Popen", _trip)
        monkeypatch.setattr(subprocess, "run", _trip)
        monkeypatch.setattr(socket, "socket", _trip_socket)

        result = observe_finalized_transition(
            _input(limitations=("no evidence collected",)), shadow_root=tmp_path / "shadow"
        )
        assert result.status == "published"
        assert tripped == {"subprocess": 0, "socket": 0}


class TestAdapterSourcesProductionWiring:
    """135L finding: the one real production call site
    (``finalization_transaction._observe_shadow_cltr``) never supplies
    ``adapter_sources``, so most comparison adapters are unverifiable-by-
    construction in real production use today (Non-Blocking; correctly
    fails closed, never fabricates conformance)."""

    def test_production_call_site_does_not_wire_adapter_sources(self):
        from pcae.core import finalization_transaction as ft

        source = inspect.getsource(ft._observe_shadow_cltr)
        assert "adapter_sources=" not in source, (
            "if this now passes adapter_sources, update the 135L report's "
            "disposition of this finding and re-verify the adapter matrix"
        )

    def test_unwired_adapter_sources_yields_mostly_unverifiable_not_false_conformant(self, tmp_path):
        result = observe_finalized_transition(
            _input(limitations=("no evidence collected",)), shadow_root=tmp_path / "shadow"
        )
        assert result.status == "published"
        by_kind = {a.representation_kind.value: a for a in result.adapter_results}
        # These are exactly the kinds whose adapters require live sources this
        # call site never supplies. None may report a false CONFORMANT.
        starved_kinds = (
            "canonical_report", "completion_metadata", "architecture_status",
            "immutable_snapshot", "checkpoint", "promoted_report",
            "promoted_metadata", "notification_payload", "receipt",
            "repository_transition_view", "git_attribution_view",
        )
        for kind in starved_kinds:
            assert by_kind[kind].conformance_state.value == "unverifiable", (
                f"{kind} unexpectedly resolved without live sources: {by_kind[kind]}"
            )


class TestTransitionIdEqualsPhaseIdRetryCollision:
    """135L finding: production constructs ``transition_id`` as exactly
    ``phase_id`` (single-snapshot scope, disclosed). A later, content-
    different observation for the *same* phase_id (e.g. a partial-then-
    corrected-to-success reconciliation) collides with the first immutable
    generation. This fails closed safely (ConflictingGenerationError is
    contained as a disclosed shadow ``publish_failed``, never corrupts the
    current pointer or silently overwrites history) but the corrected
    content is never published as shadow current."""

    def test_second_different_content_observation_for_same_phase_fails_closed(self, tmp_path):
        shadow_root = tmp_path / "shadow"
        first = _input(
            transition_type=TransitionType.CLOSE_PARTIAL,
            intended_lifecycle_state=LifecycleState.TERMINAL_PARTIAL_EXTERNAL,
            notification_state=NotificationState.UNCONFIRMED,
            notification_ids=("n-first",),
            receipt_id=None,
            limitations=("no evidence collected",),
        )
        r1 = observe_finalized_transition(first, shadow_root=shadow_root)
        assert r1.status == "published"

        second = _input(
            transition_type=TransitionType.CLOSE_SUCCESS,
            intended_lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
            notification_state=NotificationState.CONFIRMED,
            notification_ids=("n-second",),
            receipt_id="rcpt-second",
            limitations=("no evidence collected",),
        )
        r2 = observe_finalized_transition(second, shadow_root=shadow_root)

        # Fails closed: never published as a silent overwrite, never raises
        # into the caller, and the immutable first generation is untouched.
        assert r2.status == "publish_failed"
        pointer = read_current_pointer(shadow_root)
        assert pointer["record_digest"] == r1.record_digest

    def test_repeat_identical_observation_is_idempotent_not_conflicting(self, tmp_path):
        shadow_root = tmp_path / "shadow"
        one = _input(limitations=("no evidence collected",))
        r1 = observe_finalized_transition(one, shadow_root=shadow_root)
        r2 = observe_finalized_transition(one, shadow_root=shadow_root)
        assert r1.status == r2.status == "published"
        assert r1.record_digest == r2.record_digest
