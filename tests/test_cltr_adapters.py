"""Phase 135K — fifteen representation adapter tests."""

from __future__ import annotations

from pcae.cltr import schema
from pcae.cltr.adapters import AdapterSources, run_all_adapters
from pcae.cltr.enums import (
    REPRESENTATION_COMPARISON_MODE,
    AdapterComparisonMode,
    ConformanceState,
    LifecycleState,
    RepresentationKind,
    TransitionType,
)
from pcae.cltr.models import CommitOwnershipEntry, ProductionCltrRecord
from pcae.cltr.enums import CertificationState


def _record(**overrides) -> ProductionCltrRecord:
    fields = dict(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id="135K-ADAPT",
        phase_id="135K-ADAPT",
        repository_identity="repo",
        branch_identity="main",
        transition_type=TransitionType.CLOSE_SUCCESS,
        lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        source_revision="abc123",
        certified_state={"x": 1},
        report_id="r1", report_digest="a" * 64,
        metadata_id="m1", metadata_digest="b" * 64,
        snapshot_id="s1", snapshot_digest="c" * 64,
        promotion_id="p1",
    )
    fields.update(overrides)
    return ProductionCltrRecord(**fields)


def test_all_15_kinds_produced_with_correct_comparison_mode():
    results = run_all_adapters(_record(), AdapterSources())
    assert len(results) == 15
    kinds = {r.representation_kind for r in results}
    assert kinds == set(RepresentationKind)
    for result in results:
        assert result.comparison_mode == REPRESENTATION_COMPARISON_MODE[result.representation_kind]


def test_no_source_means_unverifiable_not_fabricated_conformance():
    results = run_all_adapters(_record(), AdapterSources())
    digest_kinds = {
        RepresentationKind.CANONICAL_REPORT,
        RepresentationKind.COMPLETION_METADATA,
        RepresentationKind.IMMUTABLE_SNAPSHOT,
        RepresentationKind.PROMOTED_REPORT,
        RepresentationKind.PROMOTED_METADATA,
    }
    for result in results:
        if result.representation_kind in digest_kinds:
            assert result.conformance_state == ConformanceState.UNVERIFIABLE
            assert result.limitations


def test_matching_report_digest_is_conformant():
    record = _record()
    sources = AdapterSources(live_report_digest=record.report_digest)
    results = run_all_adapters(record, sources)
    report_result = next(r for r in results if r.representation_kind == RepresentationKind.CANONICAL_REPORT)
    assert report_result.conformance_state == ConformanceState.CONFORMANT


def test_mismatched_digest_is_conflicting():
    record = _record()
    sources = AdapterSources(live_report_digest="f" * 64)
    results = run_all_adapters(record, sources)
    report_result = next(r for r in results if r.representation_kind == RepresentationKind.CANONICAL_REPORT)
    assert report_result.conformance_state == ConformanceState.CONFLICTING


def test_wrong_phase_checkpoint_is_conflicting():
    record = _record()
    sources = AdapterSources(live_checkpoint={"phase_id": "SOME-OTHER-PHASE"})
    results = run_all_adapters(record, sources)
    checkpoint_result = next(r for r in results if r.representation_kind == RepresentationKind.CHECKPOINT)
    assert checkpoint_result.conformance_state == ConformanceState.CONFLICTING


def test_git_attribution_view_unresolved_hash_is_unverifiable():
    record = _record(
        phase_commit_ownership=(
            CommitOwnershipEntry(commit_hash="deadbeef", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
        )
    )
    sources = AdapterSources(live_resolved_commit_hashes=frozenset())
    results = run_all_adapters(record, sources)
    git_result = next(r for r in results if r.representation_kind == RepresentationKind.GIT_ATTRIBUTION_VIEW)
    assert git_result.conformance_state == ConformanceState.UNVERIFIABLE


def test_git_attribution_view_resolved_hash_is_conformant():
    record = _record(
        phase_commit_ownership=(
            CommitOwnershipEntry(commit_hash="deadbeef", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
        )
    )
    sources = AdapterSources(live_resolved_commit_hashes=frozenset({"deadbeef"}))
    results = run_all_adapters(record, sources)
    git_result = next(r for r in results if r.representation_kind == RepresentationKind.GIT_ATTRIBUTION_VIEW)
    assert git_result.conformance_state == ConformanceState.CONFORMANT


def test_diagnostic_envelope_is_presentation_only():
    results = run_all_adapters(_record(), AdapterSources())
    diag = next(r for r in results if r.representation_kind == RepresentationKind.DIAGNOSTIC_ENVELOPE)
    assert diag.comparison_mode == AdapterComparisonMode.PRESENTATION_ONLY


def test_marker_absent_is_incomplete_not_conformant():
    results = run_all_adapters(_record(marker_id=None), AdapterSources())
    marker = next(r for r in results if r.representation_kind == RepresentationKind.MARKER)
    assert marker.conformance_state != ConformanceState.CONFORMANT


def test_no_adapter_ever_strengthens_authority_above_v_or_declared_role():
    results = run_all_adapters(_record(), AdapterSources())
    for result in results:
        assert result.authority_role in ("S", "R", "D", "E", "V")
        # None of these adapters may claim sole (S) authority -- that
        # would contradict 135I §4.3's inheritance rule.
        assert result.authority_role != "S"
