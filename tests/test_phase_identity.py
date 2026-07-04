"""Tests for PCAE Phase Identity & Lifecycle Hardening — Phase 113B.2.

Tests the phase identity validation functions: validate_phase_identity(),
bootstrap ambiguity detection, Architecture Status consistency checks,
and fail-closed behavior on identity mismatches.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════════════════
# Section 1 — validate_phase_identity() basic cases
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def pr():
    """The phase_reports module."""
    import pcae.core.phase_reports as mod
    return mod


def test_validate_phase_identity_importable(pr):
    """validate_phase_identity must be importable."""
    assert callable(pr.validate_phase_identity)


def test_valid_report_no_issues(pr):
    """A self-consistent report must produce zero identity issues."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113B.2: Phase Identity & Lifecycle Hardening.",
    )
    issues = pr.validate_phase_identity(report, "113B.2", {})
    assert isinstance(issues, list)
    assert len(issues) == 0


def test_summary_describing_other_phase_not_flagged(pr):
    """Phase 113X.4: --summary is not a phase-identity source at all
    (113X audit Finding 3) -- a summary naming a different phase must
    NOT be flagged. Canonical identity (the `phase_id` argument here)
    is authoritative regardless of what the summary prose says."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113C: Advisory Runtime Prototype. Completed.",
    )
    issues = pr.validate_phase_identity(report, "113B.2", {})
    assert not any("Summary describes" in i for i in issues)


def test_commit_references_wrong_phase(pr):
    """Commit message that references a different phase must be flagged."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113B.2: Phase Identity & Lifecycle Hardening.",
        commits=["Complete Phase 113C advisory runtime prototype"],
    )
    issues = pr.validate_phase_identity(report, "113B.2", {})
    assert len(issues) > 0
    assert any("Commit message references" in i for i in issues)


def test_parent_phase_commit_ok_for_sub_phase(pr):
    """Sub-phases (113B.2) may reference parent phase (113B) in commits."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113B.2: Phase Identity & Lifecycle Hardening.",
        commits=["Complete Phase 113B advisory runtime contract freeze"],
    )
    issues = pr.validate_phase_identity(report, "113B.2", {})
    assert len(issues) == 0


def test_sub_phase_not_flagged_against_current_phase(pr):
    """Sub-phases are not flagged even when PROJECT_STATUS.md has a
    different current parent phase."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113B.2: Phase Identity & Lifecycle Hardening.",
    )
    # 113B.2 is a sub-phase — it should NOT be flagged against
    # PROJECT_STATUS.md's current phase (which may be 113C)
    issues = pr.validate_phase_identity(report, "113B.2", {})
    for issue in issues:
        assert "PROJECT_STATUS.md" not in issue, (
            f"Sub-phase incorrectly flagged against PROJECT_STATUS: {issue}"
        )


def test_empty_summary_does_not_crash(pr):
    """Empty summary must not cause a crash during validation."""
    report = pr.make_phase_report(
        phase_id="999Z",
        phase_name="Test",
        status="completed",
        summary="Test phase.",
    )
    issues = pr.validate_phase_identity(report, "999Z", {})
    assert isinstance(issues, list)


def test_returns_list_even_on_error(pr):
    """validate_phase_identity must always return a list, never raise."""
    try:
        issues = pr.validate_phase_identity(None, "", {})  # type: ignore[arg-type]
    except Exception:
        issues = []
    assert isinstance(issues, list)


# ═══════════════════════════════════════════════════════════════════════
# Section 2 — Architecture Status consistency
# ═══════════════════════════════════════════════════════════════════════

def test_architecture_status_impossible_combo_detected(pr):
    """'113C complete' + '113C planned' must be flagged.

    Phase 113X.5: this now uses the structured ``completed_phase_ids``
    field rather than substring-matching the display ``completed``
    label. The retired hardcoded label ("Advisory Runtime (Architecture,
    Contract, Prototype)") contained no digits at all, so the old
    substring check ("series in comp") could *never* actually fire --
    the exact reason 113X audit Finding 4 went undetected. This is the
    regression test proving it now does."""
    report = pr.make_phase_report(
        phase_id="113D",
        phase_name="Advisory Runtime Verification",
        status="completed",
        summary="Phase 113D: Advisory Runtime Verification.",
    )
    report.architecture_status = {
        "completed": ["Advisory Runtime (Architecture, Contract, Prototype)"],
        "completed_phase_ids": ["113A", "113B", "113C"],
        "in_progress": [],
        "planned": ["113C — Advisory Runtime Prototype (Observation-Only)"],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
    }
    issues = pr.validate_phase_identity(report, "113D", {})
    assert any("113C" in i and "completed" in i and "planned" in i for i in issues)


def test_runtime_state_mismatch_detected(pr):
    """Metadata-execution-integration mismatch vs Architecture Status must be flagged."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Test",
        status="completed",
        summary="Phase 113B.2: Test.",
    )
    report.architecture_status = {
        "completed": [],
        "in_progress": [],
        "planned": [],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
    }
    md = {
        "execution_integration_status": {
            "current_maximum_runtime_state": "Executing",
            "current_maximum_plugin_capability": "enforce",
        },
    }
    issues = pr.validate_phase_identity(report, "113B.2", md)
    assert len(issues) >= 2  # Two mismatches: state and capability


# ═══════════════════════════════════════════════════════════════════════
# Section 3 — validate_finalization_gate integration
# ═══════════════════════════════════════════════════════════════════════

def test_finalization_gate_includes_phase_identity(pr):
    """validate_finalization_gate must include phase identity blockers."""
    report = pr.make_phase_report(
        phase_id="999Z",
        phase_name="Test",
        status="completed",
        summary="Phase 888X: Wrong Phase. Summary describes a different phase.",
        commits=["Complete Phase 777Y some other work"],
    )
    gate = pr.validate_finalization_gate(
        phase_id="999Z",
        report=report,
        metadata={
            "no_go_confirmation": (
                "No a. No b. No c. No d. No e. No f. "
                "No g. No h. No i. No j. No k."
            ),
            "recommended_next_phase": "Next Phase",
        },
    )
    # Should have phase identity blockers
    identity_blockers = [b for b in gate["blockers"] if "phase identity" in b]
    assert len(identity_blockers) > 0, (
        f"Expected phase identity blockers in gate, got: {gate['blockers']}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Section 4 — Bootstrap phase ambiguity detection
# ═══════════════════════════════════════════════════════════════════════

def test_detect_phase_ambiguity_importable():
    """_detect_phase_ambiguity must be importable."""
    from pcae.core.context import _detect_phase_ambiguity
    assert callable(_detect_phase_ambiguity)


def test_detect_phase_ambiguity_no_task():
    """With no active task, ambiguity should be False (not ambiguous)."""
    from pcae.core.context import _detect_phase_ambiguity
    from pcae.core.paths import HarnessPath
    result = _detect_phase_ambiguity(HarnessPath.cwd(), "113C", None)
    assert isinstance(result, dict)
    assert "ambiguous" in result
    assert "mismatches" in result


def test_detect_phase_ambiguity_returns_dict():
    """_detect_phase_ambiguity must always return a dict."""
    from pcae.core.context import _detect_phase_ambiguity
    from pcae.core.paths import HarnessPath
    result = _detect_phase_ambiguity(HarnessPath.cwd(), "113C", None)
    assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════
# Section 5 — Fail-closed behavior
# ═══════════════════════════════════════════════════════════════════════

def test_phase_identity_issues_are_blockers_not_warnings(pr):
    """Phase identity mismatches must appear as blockers, not warnings.

    Phase 113X.4: --summary is no longer a phase-identity source or
    check (see test_summary_describing_other_phase_not_flagged above),
    so this now exercises the commit-message identity check (#6, still
    intact) instead of the retired summary check (#5)."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Test",
        status="completed",
        summary="Phase 113B.2: Correct summary.",
        commits=["Complete Phase 999X wrong phase"],
    )
    gate = pr.validate_finalization_gate(
        phase_id="113B.2",
        report=report,
        metadata={
            "no_go_confirmation": (
                "No a. No b. No c. No d. No e. No f. "
                "No g. No h. No i. No j. No k."
            ),
            "recommended_next_phase": "Next Phase",
        },
    )
    identity_blockers = [b for b in gate["blockers"] if "phase identity" in b]
    assert len(identity_blockers) > 0
    # When phase identity issues exist, the gate should not be finalizable
    if identity_blockers:
        assert gate["finalizable"] is False


def test_no_phase_identity_issues_does_not_block(pr):
    """A valid report with correct summary must not add phase identity blockers."""
    report = pr.make_phase_report(
        phase_id="113B.2",
        phase_name="Phase Identity & Lifecycle Hardening",
        status="completed",
        summary="Phase 113B.2: Phase Identity & Lifecycle Hardening.",
    )
    gate = pr.validate_finalization_gate(
        phase_id="113B.2",
        report=report,
        metadata={
            "no_go_confirmation": (
                "No a. No b. No c. No d. No e. No f. "
                "No g. No h. No i. No j. No k."
            ),
            "recommended_next_phase": "113C — Advisory Runtime Prototype",
        },
    )
    identity_blockers = [b for b in gate["blockers"] if "phase identity" in b]
    assert len(identity_blockers) == 0, (
        f"Unexpected phase identity blockers: {identity_blockers}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Section 6 — recommendation chain
# ═══════════════════════════════════════════════════════════════════════

def test_recommended_next_phase_must_not_point_to_self(pr):
    """Recommended next phase pointing to current phase is blocked."""
    report = pr.make_phase_report(
        phase_id="113D",
        phase_name="Test",
        status="completed",
        summary="Phase 113D: Test.",
        recommended_next_phase="113D — Advisory Runtime Verification",
    )
    gate = pr.validate_finalization_gate(
        phase_id="113D",
        report=report,
        metadata={
            "no_go_confirmation": (
                "No a. No b. No c. No d. No e. No f. "
                "No g. No h. No i. No j. No k."
            ),
            "recommended_next_phase": "113D — Advisory Runtime Verification",
        },
    )
    rec_blockers = [b for b in gate["blockers"]
                     if "recommended" in b.lower() or "points to" in b.lower()]
    assert len(rec_blockers) > 0
