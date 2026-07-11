"""Regression coverage for the 134E.1V-finalization identity repair.

Phase 134E.1V's own canonical report/metadata consistency check
mis-parsed the phase-completion-report.md title "# Phase 134E.1V
Complete — ..." as phase_id "134E" (collapsing the sub-phase and its
verification suffix into the bare family), because the shared title
regex's trailing ``\\b`` could not be satisfied when a dotted sub-phase
number was immediately followed by a bare letter. Fixed by
``pcae.core.phase_reports._extract_canonical_title_phase_id()``, the one
shared extraction path now used by both ``validate_canonical_report()``
and ``_check_canonical_metadata_consistency()``.
"""

from __future__ import annotations

from pcae.core.phase_reports import (
    _extract_canonical_title_phase_id,
    _check_canonical_metadata_consistency,
    make_phase_report,
    validate_canonical_report,
    COMPLETENESS_COMPLETE,
)
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    validate_transition,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1-4: exact parsing of dotted/verification-suffixed identifiers
# ─────────────────────────────────────────────────────────────────────────────

def test_exact_parsing_134e_1v():
    assert _extract_canonical_title_phase_id("# Phase 134E.1V Complete — X\n") == "134E.1V"


def test_exact_parsing_134e_2():
    assert _extract_canonical_title_phase_id("# Phase 134E.2 Complete — X\n") == "134E.2"


def test_exact_parsing_134e_10():
    assert _extract_canonical_title_phase_id("# Phase 134E.10 Complete — X\n") == "134E.10"


def test_exact_parsing_134e_10v():
    assert _extract_canonical_title_phase_id("# Phase 134E.10V Complete — X\n") == "134E.10V"


# ─────────────────────────────────────────────────────────────────────────────
# 5-6: parent/sub-phase remain unequal; verification suffix is part of identity
# ─────────────────────────────────────────────────────────────────────────────

def test_parent_and_sub_phase_identifiers_remain_unequal():
    parent = _extract_canonical_title_phase_id("# Phase 134E Complete — X\n")
    sub = _extract_canonical_title_phase_id("# Phase 134E.1V Complete — X\n")
    assert parent == "134E"
    assert sub == "134E.1V"
    assert parent != sub


def test_verification_suffix_remains_part_of_identity():
    without_suffix = _extract_canonical_title_phase_id("# Phase 134E.1 Complete — X\n")
    with_suffix = _extract_canonical_title_phase_id("# Phase 134E.1V Complete — X\n")
    assert without_suffix == "134E.1"
    assert with_suffix == "134E.1V"
    assert without_suffix != with_suffix


# ─────────────────────────────────────────────────────────────────────────────
# 7: report title and metadata resolve identically across both call sites
# ─────────────────────────────────────────────────────────────────────────────

def test_title_extraction_agrees_across_both_consumers():
    content = (
        "# Phase 134E.1V Complete — Canonical Engineering Evidence Executable "
        "Model Independent Verification\n\nStatus: completed\nPushed: pushed\n"
    )

    ok, warnings = validate_canonical_report(
        content, "134E.1V", "Canonical Engineering Evidence Executable Model Independent Verification", "completed",
    )
    assert ok is True
    assert warnings == []

    r = make_phase_report(
        phase_id="134E.1V", phase_name="Canonical Engineering Evidence Executable Model Independent Verification",
        status="completed", summary="done", files_changed=1, tests_run=1,
        test_results={"a": "1/1"}, governance_results={"h": "healthy"},
        commits=["abc1234"], pushed_status="pushed",
        recommended_next_phase="134E.2 — Evidence Extraction",
        canonical_report_content=content,
    )
    _check_canonical_metadata_consistency(r)
    assert not any("title phase_id" in w for w in r.trust_warnings)


# ─────────────────────────────────────────────────────────────────────────────
# 8-9: stale parent metadata conflicts with sub-phase finalization; fails closed
# ─────────────────────────────────────────────────────────────────────────────

def test_stale_truncated_parent_still_detected_as_mismatch_pre_fix_scenario():
    """Simulates what the pre-fix truncation would have produced (title
    resolving to the bare parent "134E" while the declared identity is
    "134E.1V") and confirms the consistency check still correctly flags
    it as a mismatch, not a false match -- i.e. the *fixed* extractor
    does not accidentally make truncation look consistent; genuine
    mismatches remain caught.
    """
    content = "# Phase 134E Complete — Wrong (Truncated) Title\n\nbody\n"
    r = make_phase_report(
        phase_id="134E.1V", phase_name="X", status="completed", summary="done",
        files_changed=1, tests_run=1, test_results={"a": "1/1"},
        governance_results={"h": "healthy"}, commits=["abc1234"], pushed_status="pushed",
        recommended_next_phase="134E.2",
        canonical_report_content=content,
    )
    _check_canonical_metadata_consistency(r)
    assert any("134E" in w and "134E.1V" in w for w in r.trust_warnings)


def test_identity_conflict_fails_closed_at_transition_validator():
    """Stale/parent-collapsed metadata identity disagreeing with the
    active task's own sub-phase identity must fail closed at the shared
    repository transition validator -- confirming this repair did not
    quietly rely on report_reports.py alone; the independent identity
    authority still rejects the conflict too.
    """
    state = RepositoryState(
        phase_id="134E.1V",
        active_task_phase_id="134E.1V",
        metadata_phase_id="134E",  # collapsed-to-parent, as the pre-fix bug would have written
        artifact_state=ArtifactState.CERTIFIED,
    )
    result = validate_transition(
        state,
        ProposedTransition(kind=TransitionKind.REPORT_PROMOTION, payload={}),
        ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="134E.1V"),
    )
    assert result.verdict in (TransitionVerdict.REJECT, TransitionVerdict.QUARANTINE)


# ─────────────────────────────────────────────────────────────────────────────
# 10: metadata repair produces the full exact identifier
# ─────────────────────────────────────────────────────────────────────────────

def test_metadata_repair_produces_full_exact_identifier(tmp_path, monkeypatch):
    import json
    import argparse
    from pcae.commands.phase import run_phase_metadata_repair

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps({"phase_id": "134E.1", "phase_name": "Old"})
    )
    (tmp_path / ".pcae" / "phase-completion-report.md").write_text(
        "# Phase 134E.1V Complete — Canonical Engineering Evidence Executable Model Independent Verification\n\nbody\n"
    )
    args = argparse.Namespace(json=True)
    exit_code = run_phase_metadata_repair(args)
    assert exit_code == 0

    repaired = json.loads((tmp_path / ".pcae" / "phase-completion-metadata.json").read_text())
    assert repaired["phase_id"] == "134E.1V"  # full identifier, not truncated to "134E"


# ─────────────────────────────────────────────────────────────────────────────
# 11: report promotion rejects truncated identity
# ─────────────────────────────────────────────────────────────────────────────

def test_report_promotion_rejects_truncated_identity_via_completeness_downgrade():
    """A canonical report whose title the (pre-fix) extractor would have
    truncated to the parent phase must not be treated as trust-complete
    -- report_completeness downgrades and metadata_consistency is
    recorded as a missing trust field, blocking promotion.
    """
    content = "# Phase 134E Complete — Truncated\n\nbody\n"
    r = make_phase_report(
        phase_id="134E.1V", phase_name="X", status="completed", summary="done",
        files_changed=1, tests_run=1, test_results={"a": "1/1"},
        governance_results={"h": "healthy"}, commits=["abc1234"], pushed_status="pushed",
        recommended_next_phase="134E.2",
        canonical_report_content=content,
    )
    r.apply_trust_assessment()
    _check_canonical_metadata_consistency(r)
    assert r.report_completeness != COMPLETENESS_COMPLETE
    assert "metadata_consistency" in r.missing_trust_fields


# ─────────────────────────────────────────────────────────────────────────────
# 12: notification not dispatched for unresolved identity mismatch
# ─────────────────────────────────────────────────────────────────────────────

def test_correctly_titled_report_is_trust_complete_and_eligible_for_dispatch():
    """The positive control: once the title genuinely matches (post-fix
    extraction), the report reaches COMPLETENESS_COMPLETE with no
    metadata_consistency blocker -- i.e. dispatch eligibility is restored
    for a correctly-identified sub-phase, not just permanently blocked.
    """
    content = (
        "# Phase 134E.1V Complete — Canonical Engineering Evidence Executable "
        "Model Independent Verification\n\nStatus: completed\nPushed: pushed\n"
    )
    governance_results = {
        "pcae_health": "healthy", "pcae_check": "passed",
        "pcae_doctor_task_memory": "clean", "pcae_push_check": "clean",
        "telegram_runtime": "loaded",
    }
    test_results = {
        "report_notification_tests": "1/1", "bootstrap_session_reporting_tests": "1/1",
        "fast_green": "1/1",
    }
    r = make_phase_report(
        phase_id="134E.1V", phase_name="Canonical Engineering Evidence Executable Model Independent Verification",
        status="completed", summary="done", files_changed=1, tests_run=1,
        test_results=test_results, governance_results=governance_results,
        commits=["abc1234"], pushed_status="pushed",
        recommended_next_phase="134E.2 — Evidence Extraction",
        canonical_report_content=content,
    )
    r.apply_trust_assessment()
    _check_canonical_metadata_consistency(r)
    assert r.report_completeness == COMPLETENESS_COMPLETE
    assert "metadata_consistency" not in r.missing_trust_fields


# ─────────────────────────────────────────────────────────────────────────────
# 13-14: existing simple identifiers and 134B.3-class identity regressions
# ─────────────────────────────────────────────────────────────────────────────

def test_existing_simple_phase_identifiers_remain_compatible():
    for title, expected in (
        ("# Phase 92D.8.3 Complete — X\n", "92D.8.3"),
        ("# Phase 134B Complete — X\n", "134B"),
        ("# Phase 134B.3 Complete — X\n", "134B.3"),
        ("# Phase 113X.4 Complete — X\n", "113X.4"),
    ):
        assert _extract_canonical_title_phase_id(title) == expected


def test_134b3_style_identity_consistency_regression_still_enforced():
    """Reproduces 134B.3's own identity-conflict scenario (stale metadata
    one phase behind) through the same consistency-check function this
    repair touched, confirming the fix did not weaken that unrelated,
    already-correct behavior.
    """
    content = "# Phase 134B.2 Complete — Old Title\n\nbody\n"
    r = make_phase_report(
        phase_id="134B.3", phase_name="X", status="completed", summary="done",
        files_changed=1, tests_run=1, test_results={"a": "1/1"},
        governance_results={"h": "healthy"}, commits=["abc1234"], pushed_status="pushed",
        recommended_next_phase="134C",
        canonical_report_content=content,
    )
    _check_canonical_metadata_consistency(r)
    assert any("134B.2" in w and "134B.3" in w for w in r.trust_warnings)
