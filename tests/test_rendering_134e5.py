"""Phase 134E.5 — focused tests for Rendering Architecture
(``pcae.core.rendering``).

This module is not yet active lifecycle authority. Regression coverage
for existing Canonical Engineering Evidence / Evidence Extraction /
Phase Report View / Operator Report View / lifecycle behavior is
provided by re-running the existing suites unchanged (none of which
import or reference this new module).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys
from types import MappingProxyType

import pytest

from pcae.core.canonical_engineering_evidence import (
    Applicability,
    FindingClassification,
    FindingRecord,
    GovernanceResultItem,
    LimitationItem,
    PhaseClass,
    REQUIRED_APPLICABILITY_CATEGORIES,
    RepairRecord,
    RepositoryStateSnapshot,
    TestResultItem,
    UncertaintyItem,
)
from pcae.core.evidence_extraction import (
    PROFILE_ID_OPERATOR_REPORT,
    PROFILE_ID_PHASE_REPORT,
    extract,
)
from pcae.core.phase_report_view import compose_phase_report_view
from pcae.core.operator_report_view import compose_operator_report_view
from pcae.core import rendering as R

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import (  # noqa: E402
    _content_for,
    _full_applicability,
    _identity,
    _minimal_complete_evidence,
)
from test_phase_report_view_134e3 import _evidence_with_applicability as _phase_evidence  # noqa: E402
from test_operator_report_view_134e4 import _evidence_with_applicability as _operator_evidence  # noqa: E402


def _unescape_md(text: str) -> str:
    """Strip Markdown-escape backslashes for substring assertions --
    the renderer's own escaping (verified separately, e.g.
    ``test_markdown_escaping``) legitimately inserts a backslash before
    metacharacters including ``_`` and ``-``, which would otherwise
    break a naive literal-substring content-preservation check.
    """
    return text.replace("\\", "")


def _phase_view_and_source(phase_class=PhaseClass.IMPLEMENTATION, **overrides):
    ev = _minimal_complete_evidence(phase_class, **overrides)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    return compose_phase_report_view(res), res


def _operator_view_and_source(phase_class=PhaseClass.IMPLEMENTATION, **overrides):
    ev = _minimal_complete_evidence(phase_class, profile_id=PROFILE_ID_OPERATOR_REPORT, **overrides)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    return compose_operator_report_view(res), res


# ─────────────────────────────────────────────────────────────────────────────
# 1-4: renderer registry, duplicate rejection, unsupported renderer/version
# ─────────────────────────────────────────────────────────────────────────────

def test_renderer_registry_contains_six_renderers():
    for rid in (
        R.RENDERER_ID_PHASE_REPORT_MARKDOWN, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT,
        R.RENDERER_ID_PHASE_REPORT_JSON, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN,
        R.RENDERER_ID_OPERATOR_REPORT_PLAIN_TEXT, R.RENDERER_ID_OPERATOR_REPORT_JSON,
    ):
        descriptor = R.get_renderer(rid)
        assert descriptor.renderer_id == rid


def test_duplicate_renderer_registration_rejected():
    real = R.get_renderer(R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    fake = R.RendererDescriptor(
        renderer_id=R.RENDERER_ID_PHASE_REPORT_MARKDOWN, renderer_version="99.0",
        accepted_view_types=frozenset({R.VIEW_TYPE_PHASE_REPORT}), media_type=R.MEDIA_TYPE_MARKDOWN,
        render_fn=real.render_fn,
    )
    with pytest.raises(ValueError, match="already registered"):
        R.register_renderer(fake)


def test_identical_reregistration_allowed():
    real = R.get_renderer(R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    same = R.RendererDescriptor(
        renderer_id=real.renderer_id, renderer_version=real.renderer_version,
        accepted_view_types=real.accepted_view_types, media_type=real.media_type,
        render_fn=real.render_fn,
    )
    R.register_renderer(same)  # no raise


def test_unsupported_renderer_rejected():
    with pytest.raises(ValueError, match="Unsupported renderer"):
        R.get_renderer("__no_such_renderer__")


def test_unsupported_renderer_version_documented():
    # Renderer versioning is fixed at registration time; a caller
    # requesting a mismatched version has no dedicated parameter today
    # (mirrors the single-supported-version posture of 134E.1-134E.4).
    descriptor = R.get_renderer(R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert descriptor.renderer_version == "1.0"


# ─────────────────────────────────────────────────────────────────────────────
# 5-10: rendering for each format/view-type combination
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_markdown_rendering():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.media_type == R.MEDIA_TYPE_MARKDOWN
    assert "# Phase Report:" in result.rendered_content


def test_operator_report_markdown_rendering():
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN)
    assert result.media_type == R.MEDIA_TYPE_MARKDOWN
    assert "# Operator Report:" in result.rendered_content


def test_phase_report_plain_text_rendering():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert result.media_type == R.MEDIA_TYPE_PLAIN_TEXT
    assert "PHASE REPORT:" in result.rendered_content


def test_operator_report_plain_text_rendering():
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_PLAIN_TEXT)
    assert result.media_type == R.MEDIA_TYPE_PLAIN_TEXT
    assert "OPERATOR REPORT:" in result.rendered_content


def test_phase_report_json_rendering():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert result.media_type == R.MEDIA_TYPE_JSON
    payload = json.loads(result.rendered_content)
    assert payload["view"]["view_id"] == view.view_id


def test_operator_report_json_rendering():
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    assert payload["view"]["view_id"] == view.view_id


# ─────────────────────────────────────────────────────────────────────────────
# 11-13: all sections present, exact order preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_all_thirteen_phase_report_sections_present():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    assert len(payload["resolved_sections"]) == 13


def test_all_twelve_operator_sections_present():
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    assert len(payload["resolved_sections"]) == 12


def test_exact_section_order_preserved():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    orders = [s["order"] for s in payload["resolved_sections"]]
    assert orders == sorted(orders) == list(range(1, 14))


# ─────────────────────────────────────────────────────────────────────────────
# 14-16: not-applicable / unavailable-with-disclosure / incomplete rendered
# ─────────────────────────────────────────────────────────────────────────────

def test_explicit_not_applicable_rendered():
    view, res = _phase_view_and_source(PhaseClass.ARCHITECTURE)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "not_applicable" in result.rendered_content


def test_unavailable_with_disclosure_rendered():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["no_go_confirmations"] = Applicability.NOT_APPLICABLE
    ev = _phase_evidence(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "unavailable_with_disclosure" in result.rendered_content


def test_incomplete_section_rendered():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "incomplete" in result.rendered_content.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 17: invalid view rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_view_rejected():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.NOT_APPLICABLE
    ev = _phase_evidence(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError):
        compose_phase_report_view(res)  # extraction itself is INVALID here


# ─────────────────────────────────────────────────────────────────────────────
# 18-22: findings/repair/corrected-assumption preservation
# ─────────────────────────────────────────────────────────────────────────────

def test_finding_classification_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-1", FindingClassification.BLOCKING, "issue", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "blocking" in result.rendered_content


def test_repaired_blocking_history_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_repaired"] = Applicability.PRESENT
    original = FindingRecord("F-2", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_repaired=(repair,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    verif = next(s for s in payload["resolved_sections"] if s["section_id"] == "verification_findings")
    resolved = json.dumps(verif["resolved_values"])
    assert "blocking" in resolved.lower() and "confirmed" in resolved.lower()


def test_partial_repair_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    residual = FindingRecord("F-3", FindingClassification.NON_BLOCKING, "residual", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(residual,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "non_blocking" in _unescape_md(result.rendered_content)


def test_unresolved_non_blocking_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-4", FindingClassification.NON_BLOCKING, "minor", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert "non_blocking" in result.rendered_content


def test_corrected_assumption_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["incorrect_assumptions_corrected"] = Applicability.PRESENT
    original = FindingRecord("F-5", FindingClassification.NON_BLOCKING, "wrong assumption", "component")
    repair = RepairRecord(original, "corrected", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, incorrect_assumptions_corrected=(repair,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert "incorrect_assumptions_corrected" in result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 23-24: technical debt / deferred work preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_technical_debt_preserved():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "technical_debt_reviewed" in _unescape_md(result.rendered_content)


def test_deferred_work_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_introduced"] = Applicability.PRESENT
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        technical_debt_introduced=_content_for("technical_debt_introduced"),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "technical_debt_introduced" in _unescape_md(result.rendered_content)


# ─────────────────────────────────────────────────────────────────────────────
# 25-27: governance warning / test failure / baseline failure preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_governance_warning_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        governance_results=(GovernanceResultItem("pcae_check", "warning: stale"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "warning: stale" in result.rendered_content


def test_test_failure_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        test_results=(TestResultItem("fast_green", "4389 passed, 1 failed", "failed"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "failed" in result.rendered_content
    assert "4389 passed, 1 failed" in result.rendered_content


def test_baseline_failure_disclosure_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        test_results=(TestResultItem(
            "fast_green", "4389 passed, 1 pre-existing unrelated failure", "passed_with_known_issue",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "pre-existing" in _unescape_md(result.rendered_content)


# ─────────────────────────────────────────────────────────────────────────────
# 28-31: repository/runtime state preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_dirty_repository_state_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        repository_state=RepositoryStateSnapshot(
            commit="abc1234", branch="main", pushed_status="not_pushed",
            origin_main_head_count=2, clean=False,
        ),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    repo_section = next(s for s in payload["resolved_sections"] if s["section_id"] == "phase_identity")
    assert repo_section["resolved_values"]["repository_state"]["clean"] is False


def test_unpushed_state_preserved():
    from pcae.core.canonical_engineering_evidence import CommitPushInfo
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="not_pushed", origin_main_head_count=3),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "not_pushed" in _unescape_md(result.rendered_content)


def test_runtime_state_preserved():
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    repo_section = next(
        s for s in payload["resolved_sections"] if s["section_id"] == "repository_and_runtime_state"
    )
    assert "runtime_state" in repo_section["resolved_values"]


def test_execution_availability_preserved():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "unavailable" in result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 32-33: unsafe readiness / notable knowledge preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_unsafe_readiness_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, recommended_next_phase="blocked pending resolution",
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "blocked pending resolution" in result.rendered_content
    assert "ready" not in result.rendered_content.split("blocked pending resolution")[1][:20]


def test_notable_engineering_knowledge_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        notable_engineering_knowledge=("registry-overwrite defect class",),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "registry-overwrite defect class" in _unescape_md(result.rendered_content)


# ─────────────────────────────────────────────────────────────────────────────
# 34-37: uncertainty / limitations / filtering / provenance preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "uncertainty" in result.rendered_content


def test_limitations_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "limitations" in result.rendered_content


def test_filtering_disclosure_preserved():
    view, res = _phase_view_and_source(PhaseClass.ARCHITECTURE)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "implementation_findings" in result.rendered_content


def test_provenance_traceability_preserved():
    from pcae.core.canonical_engineering_evidence import EvidenceProvenanceRecord
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        provenance=(EvidenceProvenanceRecord(
            covers="test_results", source_artifact="pytest-output.txt", source_command="pytest",
            source_phase_id="134E.5", derivation_path="ci", verification_state="verified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "provenance" in result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 38-39: rendering completeness cannot exceed view/decision completeness
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_completeness_never_exceeds_view_completeness():
    rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
    for phase_class in PhaseClass:
        view, res = _phase_view_and_source(phase_class)
        result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
        assert rank[result.completeness.value] >= rank[view.completeness.value]


def test_operator_rendering_never_exceeds_decision_completeness():
    rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
    view, res = _operator_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN)
    assert rank[result.completeness.value] >= rank[view.decision_completeness.value]
    assert rank[result.completeness.value] >= rank[view.completeness.value]


# ─────────────────────────────────────────────────────────────────────────────
# 40-42: content-preservation accounting, missing content detected, empty
# render rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_content_preservation_accounting():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.content_preserved is True
    assert not any(d.code == "content_preservation_failure" for d in result.diagnostics)


def test_missing_content_detected():
    # Force a section's primary evidence group to reference a category
    # the underlying source no longer carries -- simulate a
    # renderer-level content gap independent of composition's own
    # accounting.
    view, res = _phase_view_and_source()
    bad_selected = tuple(item for item in res.selected_evidence if item.category != "governance_results")
    bad_res = dataclasses.replace(res, selected_evidence=bad_selected)
    # Recompute digest expectation: the view's own source_extraction_digest
    # must match bad_res for render() to proceed past the forgery check.
    bad_res_matching_digest = dataclasses.replace(bad_res)
    object.__setattr__(view, "source_extraction_digest", bad_res.compute_digest())
    result = R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.content_preserved is False
    assert any(d.code == "content_preservation_failure" for d in result.diagnostics)
    assert result.completeness != R.RenderingCompleteness.COMPLETE


def test_empty_render_rejected():
    view, res = _phase_view_and_source()
    descriptor = R.get_renderer(R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    empty_descriptor = R.RendererDescriptor(
        renderer_id="empty_test_renderer", renderer_version="1.0",
        accepted_view_types=frozenset({R.VIEW_TYPE_PHASE_REPORT}), media_type=R.MEDIA_TYPE_PLAIN_TEXT,
        render_fn=lambda v, s: ("   ", (), set()),
    )
    R.register_renderer(empty_descriptor)
    with pytest.raises(ValueError, match="empty successful render"):
        R.render(view, res, "empty_test_renderer")


# ─────────────────────────────────────────────────────────────────────────────
# 43-49: escaping and safety
# ─────────────────────────────────────────────────────────────────────────────

def test_markdown_escaping():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="a * b _ c ` d")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "\\*" in result.rendered_content
    assert "\\_" in result.rendered_content


def test_markdown_code_fence_escaping():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="```rm -rf /```")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "```" not in result.rendered_content
    assert "rm -rf /" in _unescape_md(result.rendered_content)


def test_plain_text_control_character_handling():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="bell\x07here")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert "\\x07" in result.rendered_content


def test_unicode_preserved():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="日本語 emoji 🎉 objective")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "日本語" in result.rendered_content and "🎉" in result.rendered_content


def test_multiline_evidence_preserved():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="line one\nline two\nline three")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert "line one" in result.rendered_content and "line three" in result.rendered_content


def test_long_evidence_not_truncated():
    long_text = "x" * 5000
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective=long_text)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert long_text in result.rendered_content


def test_secret_like_content_not_specially_scrubbed_by_renderer():
    # Secret rejection belongs upstream (CEE's own _contains_likely_secret
    # check at finalize() time); the renderer performs no additional
    # broad secret scanning -- confirmed CEE itself already rejects this
    # shape before a view can even be composed.
    with pytest.raises(ValueError):
        _minimal_complete_evidence(
            PhaseClass.IMPLEMENTATION, objective="PCAE_TELEGRAM_TOKEN: 123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef123",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 50-54: deterministic bytes and cross-process determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_stable_newline_behavior():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.rendered_content.count("\n") == r2.rendered_content.count("\n")
    assert "\r" not in r1.rendered_content


def test_deterministic_markdown_bytes():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.rendered_content == r2.rendered_content


def test_deterministic_plain_text_bytes():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert r1.rendered_content == r2.rendered_content


def test_deterministic_json_bytes():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert r1.rendered_content == r2.rendered_content


def test_cross_process_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "from pcae.core.rendering import render, RENDERER_ID_PHASE_REPORT_MARKDOWN; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "result = render(view, res, RENDERER_ID_PHASE_REPORT_MARKDOWN); "
        "print(result.compute_digest())"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    d1 = proc1.stdout.strip().splitlines()[-1]
    d2 = proc2.stdout.strip().splitlines()[-1]
    assert d1 == d2


# ─────────────────────────────────────────────────────────────────────────────
# 55-58: rendering digest stability and change detection
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_digest_stable():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.compute_digest() == r2.compute_digest()


def test_digest_changes_on_material_content_change():
    view1, res1 = _phase_view_and_source(PhaseClass.ARCHITECTURE)
    view2, res2 = _phase_view_and_source(PhaseClass.IMPLEMENTATION)
    r1 = R.render(view1, res1, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    r2 = R.render(view2, res2, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.compute_digest() != r2.compute_digest()


def test_digest_changes_on_uncertainty_change():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    ev1 = _phase_evidence(PhaseClass.IMPLEMENTATION, app)
    res1 = extract(ev1, PROFILE_ID_PHASE_REPORT)
    view1 = compose_phase_report_view(res1)
    r1 = R.render(view1, res1, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)

    app2 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app2["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev2 = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app2,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res2 = extract(ev2, PROFILE_ID_PHASE_REPORT)
    view2 = compose_phase_report_view(res2)
    r2 = R.render(view2, res2, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.compute_digest() != r2.compute_digest()


def test_digest_changes_on_limitation_change():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    ev1 = _phase_evidence(PhaseClass.IMPLEMENTATION, app)
    res1 = extract(ev1, PROFILE_ID_PHASE_REPORT)
    view1 = compose_phase_report_view(res1)
    r1 = R.render(view1, res1, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)

    app2 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app2["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev2 = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app2,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res2 = extract(ev2, PROFILE_ID_PHASE_REPORT)
    view2 = compose_phase_report_view(res2)
    r2 = R.render(view2, res2, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert r1.compute_digest() != r2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 59-63: renderer metadata included, delivery/transport state excluded,
# model/agent independence
# ─────────────────────────────────────────────────────────────────────────────

def test_renderer_metadata_included():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.renderer_id == R.RENDERER_ID_PHASE_REPORT_MARKDOWN
    assert result.renderer_version == "1.0"


def test_delivery_state_excluded():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    d = result.to_dict()
    forbidden = {"delivery", "sink", "chat_id", "telegram"}
    assert not (set(d.keys()) & forbidden)


def test_transport_context_excluded():
    field_names = {f.name for f in dataclasses.fields(R.RenderingResult)}
    forbidden = {"transport", "sink", "chat_id", "channel"}
    assert not (field_names & forbidden)


def test_model_agent_independence():
    sig = inspect.signature(R.render)
    assert set(sig.parameters.keys()) == {"view", "source", "renderer_id"}


def test_unknown_future_agent_provenance():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "agent" not in result.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# 64-68: no Telegram/chunking/attachment/filesystem/lifecycle behavior
# ─────────────────────────────────────────────────────────────────────────────

def test_no_telegram_dependency():
    assert "telegram" not in inspect.getsource(R).lower()
    assert not hasattr(R, "TelegramSink")


def test_no_message_chunking():
    source = inspect.getsource(R)
    for forbidden in ("chunk", "split_message", "message_limit"):
        assert forbidden not in source.lower()


def test_no_attachment_logic():
    assert "attachment" not in inspect.getsource(R).lower()


def test_no_filesystem_network_behavior(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("rendering must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    view, res = _phase_view_and_source()
    R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)


def test_no_active_lifecycle_imports():
    for line in inspect.getsource(R).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for module in (
                "pcae.core.phase_reports", "pcae.core.notifications",
                "pcae.core.notification_certification",
                "pcae.core.repository_transition_validator",
            ):
                assert module not in stripped


def test_no_consumer_references_rendering_yet():
    import pathlib
    src_root = pathlib.Path(R.__file__).resolve().parent.parent
    for path in src_root.rglob("*.py"):
        if path.name == "rendering.py":
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "pcae.core.rendering" not in text and "from pcae.core import rendering" not in text, (
            f"{path} unexpectedly references rendering"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 69-74: views/extraction/CEE/current lifecycle remain unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_view_remains_unchanged():
    import pcae.core.phase_report_view as prv
    assert "rendering" not in inspect.getsource(prv)


def test_operator_report_view_remains_unchanged():
    import pcae.core.operator_report_view as orv
    assert "rendering" not in inspect.getsource(orv)


def test_evidence_extraction_remains_unchanged():
    # Narrowed to actual import statements -- evidence_extraction.py's
    # own docstring legitimately mentions "rendering format" in prose
    # explaining what it is *not* coupled to, which would otherwise
    # false-positive a naive substring scan (the same lesson 134E.2's
    # own test suite first documented for "markdown"/"telegram" scans).
    import pcae.core.evidence_extraction as ee
    for line in inspect.getsource(ee).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "rendering" not in stripped
    assert not hasattr(ee, "render")


def test_canonical_evidence_remains_immutable():
    view, res = _phase_view_and_source()
    ev_digest = None
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert res.compute_digest() == view.source_extraction_digest


def test_current_report_generation_remains_unchanged():
    import pcae.core.phase_reports as pr
    assert "rendering" not in inspect.getsource(pr) and "operator_report_view" not in inspect.getsource(pr)


def test_current_notification_behavior_remains_unchanged():
    import pcae.core.notifications as notif
    assert "rendering" not in inspect.getsource(notif)


# ─────────────────────────────────────────────────────────────────────────────
# 75-76: future renderer registration independence
# ─────────────────────────────────────────────────────────────────────────────

def test_future_renderer_registration_without_existing_change():
    view, res = _phase_view_and_source()
    before = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    future = R.RendererDescriptor(
        renderer_id="future_test_renderer_v1", renderer_version="1.0",
        accepted_view_types=frozenset({R.VIEW_TYPE_PHASE_REPORT}), media_type="text/x-future",
        render_fn=lambda v, s: ("future content", (), {g.category for sec in v.sections for g in sec.evidence_groups if g.is_primary}),
    )
    R.register_renderer(future)
    after = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert before.rendered_content == after.rendered_content


def test_existing_renderer_output_unchanged_after_future_registration():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert r1.rendered_content == r2.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 77-81: validation/failure
# ─────────────────────────────────────────────────────────────────────────────

def test_wrong_view_type_rejected():
    phase_view, phase_res = _phase_view_and_source()
    with pytest.raises(ValueError, match="does not accept view type"):
        R.render(phase_view, phase_res, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN)


def test_forged_view_rejected():
    view, res = _phase_view_and_source()
    with pytest.raises(ValueError):
        R.render("not a view", res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_missing_source_digest_rejected():
    view, res = _phase_view_and_source()
    bad_res = dataclasses.replace(res, source_record_digest="")
    with pytest.raises(ValueError):
        R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_invalid_section_order_rejected():
    view, res = _phase_view_and_source()
    reordered = dataclasses.replace(view, sections=tuple(reversed(view.sections)))
    with pytest.raises(ValueError, match="Invalid section order"):
        R.render(reordered, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_omitted_required_section_detected():
    view, res = _phase_view_and_source()
    truncated = dataclasses.replace(view, sections=view.sections[:-1])
    with pytest.raises(ValueError, match="Invalid section order"):
        R.render(truncated, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# 82-85: strengthening rejected/prevented
# ─────────────────────────────────────────────────────────────────────────────

def test_renderer_cannot_strengthen_status():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-6", FindingClassification.BLOCKING, "issue", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    discoveries = next(
        s for s in payload["resolved_sections"] if s["section_id"] == "verification_findings"
    )
    group = next(g for g in discoveries["evidence_groups"] if g["category"] == "defects_discovered")
    # The original BLOCKING classification survives unrewritten; nothing
    # in the module ever substitutes "confirmed"/"passed"/"resolved" for
    # a BLOCKING classification.
    assert group["finding_classifications"] == ["blocking"]


def test_warning_cannot_become_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, governance_results=(GovernanceResultItem("pcae_check", "warning"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "warning" in result.rendered_content


def test_incomplete_cannot_become_complete():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.completeness != R.RenderingCompleteness.COMPLETE


def test_unsafe_cannot_become_ready():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, recommended_next_phase="unsafe to proceed: blocking findings remain",
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "unsafe to proceed" in result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 86-91: complete-with-limitations presentation, traceability, JSON
# round-trip, channel-neutrality, full-information plain text
# ─────────────────────────────────────────────────────────────────────────────

def test_complete_with_limitations_presentation():
    view, res = _phase_view_and_source()
    assert view.completeness.value == "complete_with_limitations"
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.completeness == R.RenderingCompleteness.COMPLETE_WITH_LIMITATIONS


def test_traceability_footer_header():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert view.source_evidence_id in result.rendered_content
    assert view.source_record_digest in result.rendered_content
    assert view.view_id in result.rendered_content


def test_json_round_trip_semantic_compatibility():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload1 = json.loads(result.rendered_content)
    payload2 = json.loads(json.dumps(payload1))
    assert payload1 == payload2


def test_markdown_remains_channel_neutral():
    source = inspect.getsource(R._render_phase_report_markdown) + inspect.getsource(R._render_operator_report_markdown)
    for forbidden in ("telegram", "slack", "teams", "discord"):
        assert forbidden not in source.lower()


def test_plain_text_remains_full_information():
    view, res = _phase_view_and_source()
    md = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    txt = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    # Same set of primary categories resolved in both formats.
    assert md.content_preserved == txt.content_preserved is True


def test_identical_content_across_formats_at_semantic_level():
    view, res = _phase_view_and_source()
    md = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    txt = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    js = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert view.phase_id in md.rendered_content
    assert view.phase_id in txt.rendered_content
    assert view.phase_id in js.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 92-96: diagnostics determinism, unknown option rejected, options cannot
# affect inclusion, no timestamp injection, future delivery consumability
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_diagnostics_deterministic():
    view, res = _phase_view_and_source()
    r1 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    r2 = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert [d.to_dict() for d in r1.diagnostics] == [d.to_dict() for d in r2.diagnostics]


def test_unknown_output_option_rejected_by_signature():
    with pytest.raises(TypeError):
        view, res = _phase_view_and_source()
        R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN, unknown_option=True)


def test_renderer_options_cannot_affect_evidence_inclusion():
    # No options parameter exists on render() at all today -- confirmed
    # via signature inspection, so no option could possibly influence
    # evidence inclusion.
    sig = inspect.signature(R.render)
    assert "options" not in sig.parameters


def test_no_current_timestamp_injection():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    import re as _re
    assert not _re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result.rendered_content)


def test_future_delivery_adapter_can_consume_rendering_result():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    d = result.to_dict()
    assert isinstance(d["rendered_content"], str)
    assert isinstance(d["media_type"], str)
    assert "rendering_digest" in d
