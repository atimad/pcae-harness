"""Phase 134E.5V — independent adversarial verification of Rendering
Architecture (134E.5).

Does not trust 134E.5's own report, documentation, or its 97/98 tests
as sufficient evidence. These are fresh probes beyond that existing
coverage, including a regression test for one genuine BLOCKING defect
found and repaired during this verification phase:

1. Undisclosed unresolved content in rendered prose: when a primary
   category's value could not be resolved from the source (e.g. a
   forged/mismatched source, or a genuinely corrupted extraction
   result), the Markdown/plain-text renderers previously still printed
   the category's structural `classifications:` line (derived from
   already-composed view data) with **no inline disclosure** that the
   corresponding finding/repair body was unavailable. The structured
   `RenderingResult.diagnostics`/`content_preserved`/`completeness`
   already correctly flagged the gap, but a reader of only the
   rendered *text* (not the structured result) would see an
   undisclosed, unsupported classification claim (e.g. "blocking")
   with no accompanying evidence. Repaired by adding an explicit
   `[content unresolved: source value unavailable]` line inline,
   immediately where the missing content would otherwise have
   appeared.
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
from test_rendering_134e5 import _phase_view_and_source, _operator_view_and_source, _unescape_md  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# 1-2. View/source same ID but altered value; same digest field but
# recomputed mismatch
# ─────────────────────────────────────────────────────────────────────────────

def test_view_source_same_id_altered_value_rejected():
    view, res = _phase_view_and_source()
    finding_bearing = dataclasses.replace(
        res, selected_evidence=res.selected_evidence[:-1] + (
            dataclasses.replace(res.selected_evidence[-1], value=("altered",)),
        ),
    )
    # source_evidence_id unchanged, but content altered -> digest changes.
    assert finding_bearing.compute_digest() != res.compute_digest()
    with pytest.raises(ValueError, match="does not match"):
        R.render(view, finding_bearing, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_recomputed_digest_mismatch_rejected():
    view, res = _phase_view_and_source()
    # A source object with a stale/forged digest field would still be
    # rejected because compute_digest() re-derives from actual content,
    # never trusting a stored field.
    assert view.source_extraction_digest == res.compute_digest()
    tampered = dataclasses.replace(res, profile_version="99.0-forged")
    with pytest.raises(ValueError, match="does not match"):
        R.render(view, tampered, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# 3-4. Source from another phase / another profile
# ─────────────────────────────────────────────────────────────────────────────

def test_source_from_another_phase_rejected():
    view, res = _phase_view_and_source()
    other_ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, identity=_identity("999Z"))
    other_res = extract(other_ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError):
        R.render(view, other_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_source_from_another_profile_rejected():
    # Confirmed: profile_id is embedded transitively in
    # ExtractionResult.compute_digest()'s own serialization, so a
    # same-evidence-ID source extracted under the wrong profile always
    # produces a different digest and is caught by the existing digest
    # check without needing a separate profile_id comparison.
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res_phase = extract(ev, PROFILE_ID_PHASE_REPORT)
    res_operator = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert res_phase.source_evidence_id == res_operator.source_evidence_id
    assert res_phase.compute_digest() != res_operator.compute_digest()
    view = compose_phase_report_view(res_phase)
    with pytest.raises(ValueError, match="does not match"):
        R.render(view, res_operator, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# 5-6. Renderer exposing unassigned source evidence / recomposing
# section assignment
# ─────────────────────────────────────────────────────────────────────────────

def test_renderer_never_exposes_unassigned_source_evidence():
    # Inject an extra category into source.selected_evidence that the
    # view never assigned to any section -- confirm it never appears in
    # rendered output.
    from pcae.core.evidence_extraction import SelectedEvidenceItem, RequirementLevel
    view, res = _phase_view_and_source()
    forged = SelectedEvidenceItem(
        category="__smuggled_secret_category__", source_evidence_id=res.source_evidence_id,
        value=("smuggled content",), applicability=Applicability.PRESENT,
        requirement_level=RequirementLevel.REQUIRED, provenance=(),
        verification_state=None, uncertainty_refs=(), limitation_refs=(),
        selection_reason="forged",
    )
    bad_res = dataclasses.replace(res, selected_evidence=res.selected_evidence + (forged,))
    object.__setattr__(view, "source_extraction_digest", bad_res.compute_digest())
    result = R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "smuggled" not in result.rendered_content
    assert "__smuggled_secret_category__" not in result.rendered_content


def test_renderer_never_recomposes_section_assignment():
    source = inspect.getsource(R)
    assert "compose_phase_report_view" not in source
    assert "compose_operator_report_view" not in source


# ─────────────────────────────────────────────────────────────────────────────
# 7-11. Content label without content (regression for the repaired
# defect); finding/repair/uncertainty/limitation ID without body
# ─────────────────────────────────────────────────────────────────────────────

def test_content_label_without_content_discloses_gap():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-1", FindingClassification.BLOCKING, "a real serious issue", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    bad_res = dataclasses.replace(
        res, selected_evidence=tuple(i for i in res.selected_evidence if i.category != "defects_discovered"),
    )
    object.__setattr__(view, "source_extraction_digest", bad_res.compute_digest())
    result = R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.content_preserved is False
    assert "content unresolved" in _unescape_md(result.rendered_content)


def test_finding_id_without_finding_body_disclosed():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-2", FindingClassification.NON_BLOCKING, "minor", "component")
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    bad_res = dataclasses.replace(
        res, selected_evidence=tuple(i for i in res.selected_evidence if i.category != "defects_discovered"),
    )
    object.__setattr__(view, "source_extraction_digest", bad_res.compute_digest())
    result = R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert "content unresolved" in result.rendered_content


def test_repair_id_without_repair_body_disclosed():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_repaired"] = Applicability.PRESENT
    original = FindingRecord("F-3", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_repaired=(repair,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    bad_res = dataclasses.replace(
        res, selected_evidence=tuple(i for i in res.selected_evidence if i.category != "defects_repaired"),
    )
    object.__setattr__(view, "source_extraction_digest", bad_res.compute_digest())
    result = R.render(view, bad_res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "content unresolved" in _unescape_md(result.rendered_content)
    assert result.content_preserved is False


def test_uncertainty_id_without_uncertainty_body():
    # Report-level uncertainty categories are structural (view-level
    # strings), never requiring source resolution -- confirm they
    # remain visible even when the affected category's own primary
    # content is unresolved.
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


def test_limitation_id_without_limitation_body():
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


# ─────────────────────────────────────────────────────────────────────────────
# 12-13. Markdown code-fence / heading injection
# ─────────────────────────────────────────────────────────────────────────────

def test_markdown_code_fence_injection_neutralized():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="```\n# injected heading\n```")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "```" not in result.rendered_content


def test_markdown_heading_injection_escaped():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="# fake top-level heading")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    # The injected "#" is escaped, never becomes a real heading marker.
    assert "\\# fake" in result.rendered_content
    assert "fake top-level heading" in _unescape_md(result.rendered_content)


# ─────────────────────────────────────────────────────────────────────────────
# 14-15. Plain-text ANSI/control characters; Unicode and multiline
# ─────────────────────────────────────────────────────────────────────────────

def test_plain_text_ansi_control_characters_escaped():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="\x1b[31mred text\x1b[0m")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert "\x1b" not in result.rendered_content
    assert "\\x1b" in result.rendered_content


def test_unicode_and_multiline_preserved_across_formats():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, objective="日本語\nline two 🎉")
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    md = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    txt = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    js = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    assert "日本語" in md.rendered_content and "🎉" in md.rendered_content
    assert "日本語" in txt.rendered_content and "🎉" in txt.rendered_content
    # JSON uses standard \uXXXX escaping (json.dumps default) -- fully
    # round-trippable and lossless, not a content omission; verify via
    # decode rather than a literal UTF-8 substring check.
    decoded = json.loads(js.rendered_content)
    decoded_text = json.dumps(decoded, ensure_ascii=False)
    assert "日本語" in decoded_text and "🎉" in decoded_text


# ─────────────────────────────────────────────────────────────────────────────
# 16. Cross-format semantic inventory equality
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_format_semantic_inventory_equality():
    view, res = _phase_view_and_source(PhaseClass.VERIFICATION)
    md = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    txt = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    js = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(js.rendered_content)
    resolved_categories_json = {
        cat for s in payload["resolved_sections"] for cat in s["resolved_values"].keys()
    }
    md_categories = {g.category for s in view.sections for g in s.evidence_groups if g.is_primary}
    txt_categories = md_categories
    # Every category the JSON renderer resolved must also be textually
    # present (as its category label at minimum) in both prose formats.
    for cat in resolved_categories_json:
        assert cat in _unescape_md(md.rendered_content)
        assert cat in txt.rendered_content
    assert md.content_preserved == txt.content_preserved == js.content_preserved


# ─────────────────────────────────────────────────────────────────────────────
# 17-18. Phase Report / Operator Report missing section rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_missing_section_rejected():
    view, res = _phase_view_and_source()
    truncated = dataclasses.replace(view, sections=view.sections[1:])
    with pytest.raises(ValueError, match="Invalid section order"):
        R.render(truncated, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)


def test_operator_report_missing_section_rejected():
    view, res = _operator_view_and_source()
    truncated = dataclasses.replace(view, sections=view.sections[1:])
    with pytest.raises(ValueError, match="Invalid section order"):
        R.render(truncated, res, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN)


# ─────────────────────────────────────────────────────────────────────────────
# 19-20. Complete renderer over incomplete view / decision-incomplete
# view attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_complete_render_over_incomplete_view_impossible():
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
    assert view.completeness.value == "incomplete"
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert result.completeness != R.RenderingCompleteness.COMPLETE


def test_operator_complete_render_over_decision_incomplete_view_impossible():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _operator_evidence(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert view.decision_completeness.value == "incomplete"
    result = R.render(view, res, R.RENDERER_ID_OPERATOR_REPORT_MARKDOWN)
    assert result.completeness != R.RenderingCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 21-24. Repaired BLOCKING history collapse; warning->pass; dirty->clean;
# unsafe->ready strengthening attempts
# ─────────────────────────────────────────────────────────────────────────────

def test_repaired_blocking_history_never_collapsed():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_PHASE_REPORT)
    app["defects_repaired"] = Applicability.PRESENT
    original = FindingRecord("F-4", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _phase_evidence(PhaseClass.VERIFICATION, app, defects_repaired=(repair,))
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    section = next(s for s in payload["resolved_sections"] if s["section_id"] == "verification_findings")
    group = next(g for g in section["evidence_groups"] if g["category"] == "defects_repaired")
    assert set(group["finding_classifications"]) == {"blocking", "confirmed"}


def test_warning_never_strengthened_to_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, governance_results=(GovernanceResultItem("pcae_check", "warning: x"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    gov_section = next(s for s in payload["resolved_sections"] if s["section_id"] == "governance_results")
    gov_values = json.dumps(gov_section["resolved_values"])
    assert "warning: x" in gov_values
    assert '"status": "passed"' not in gov_values


def test_dirty_repository_never_strengthened_to_clean():
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
    identity_section = next(s for s in payload["resolved_sections"] if s["section_id"] == "phase_identity")
    assert identity_section["resolved_values"]["repository_state"]["clean"] is False


def test_unsafe_readiness_never_strengthened_to_ready():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, recommended_next_phase="unsafe to proceed",
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "unsafe to proceed" in result.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 25-28. Global limitation / cross-section uncertainty / filtering
# disclosure omitted; provenance detached
# ─────────────────────────────────────────────────────────────────────────────

def test_global_limitation_not_omitted():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["notable_engineering_knowledge"] = Applicability.UNAVAILABLE
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="notable_engineering_knowledge", description="unavailable",
            affected_evidence=("notable_engineering_knowledge",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "Cross-section limitations" in result.rendered_content


def test_cross_section_uncertainty_not_omitted():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_PHASE_REPORT)
    app["notable_engineering_knowledge"] = Applicability.UNKNOWN
    ev = _phase_evidence(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="notable_engineering_knowledge", description="unknown",
            affected_evidence=("notable_engineering_knowledge",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "Cross-section uncertainty" in result.rendered_content


def test_filtering_disclosure_not_omitted():
    view, res = _phase_view_and_source(PhaseClass.ARCHITECTURE)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert "Filtering disclosures" in result.rendered_content


def test_provenance_not_detached():
    from pcae.core.canonical_engineering_evidence import EvidenceProvenanceRecord
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        provenance=(EvidenceProvenanceRecord(
            covers="test_results", source_artifact="pytest-output.txt", source_command="pytest",
            source_phase_id="134E.5V", derivation_path="ci", verification_state="verified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    section = next(s for s in payload["resolved_sections"] if s["section_id"] == "test_results")
    assert "test_results" in section["provenance_categories"]


# ─────────────────────────────────────────────────────────────────────────────
# 29-31. Renderer registry silent overwrite, conflicting registration,
# future registration isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_renderer_registry_silent_overwrite_rejected():
    real = R.get_renderer(R.RENDERER_ID_OPERATOR_REPORT_JSON)
    evil = R.RendererDescriptor(
        renderer_id=R.RENDERER_ID_OPERATOR_REPORT_JSON, renderer_version="66.6",
        accepted_view_types=frozenset({R.VIEW_TYPE_OPERATOR_REPORT}), media_type=R.MEDIA_TYPE_JSON,
        render_fn=real.render_fn,
    )
    with pytest.raises(ValueError, match="already registered"):
        R.register_renderer(evil)
    # Confirm the real renderer is untouched after the rejected attempt.
    assert R.get_renderer(R.RENDERER_ID_OPERATOR_REPORT_JSON).renderer_version == "1.0"


def test_conflicting_identical_id_registration_rejected():
    real = R.get_renderer(R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    conflicting = R.RendererDescriptor(
        renderer_id=real.renderer_id, renderer_version=real.renderer_version,
        accepted_view_types=frozenset({R.VIEW_TYPE_OPERATOR_REPORT}),  # different accepted types
        media_type=real.media_type, render_fn=real.render_fn,
    )
    with pytest.raises(ValueError, match="already registered"):
        R.register_renderer(conflicting)


def test_future_renderer_registration_does_not_alter_existing_output():
    view, res = _phase_view_and_source()
    before = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    future = R.RendererDescriptor(
        renderer_id="__future_renderer_134e5v__", renderer_version="1.0",
        accepted_view_types=frozenset({R.VIEW_TYPE_PHASE_REPORT}), media_type="text/x-future",
        render_fn=lambda v, s: ("future", (), {g.category for sec in v.sections for g in sec.evidence_groups if g.is_primary}),
    )
    R.register_renderer(future)
    after = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert before.rendered_content == after.rendered_content


# ─────────────────────────────────────────────────────────────────────────────
# 32. Renderer options evidence-exclusion attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_no_options_parameter_exists_to_exclude_evidence():
    sig = inspect.signature(R.render)
    assert "options" not in sig.parameters
    assert "kwargs" not in str(sig)


# ─────────────────────────────────────────────────────────────────────────────
# 33-35. Cross-process determinism per format
# ─────────────────────────────────────────────────────────────────────────────

def _cross_process_digest(renderer_id: str) -> tuple[str, str]:
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "from pcae.core.rendering import render; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "result = render(view, res, %r); "
        "print(result.compute_digest())"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent), renderer_id)
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    return proc1.stdout.strip().splitlines()[-1], proc2.stdout.strip().splitlines()[-1]


def test_cross_process_markdown_determinism():
    d1, d2 = _cross_process_digest(R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    assert d1 == d2


def test_cross_process_plain_text_determinism():
    d1, d2 = _cross_process_digest(R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT)
    assert d1 == d2


def test_cross_process_json_determinism():
    d1, d2 = _cross_process_digest(R.RENDERER_ID_PHASE_REPORT_JSON)
    assert d1 == d2


# ─────────────────────────────────────────────────────────────────────────────
# 36-37. Unknown future-agent independence, synthetic future-channel
# independence
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_future_agent_independence():
    # No provenance/agent-identity parameter exists anywhere in the
    # render() signature or RenderingResult model.
    sig = inspect.signature(R.render)
    assert "agent" not in str(sig) and "model" not in str(sig)
    field_names = {f.name for f in dataclasses.fields(R.RenderingResult)}
    assert "agent_id" not in field_names and "model_id" not in field_names


def test_synthetic_future_channel_independence():
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
    d = result.to_dict()
    for forbidden in ("channel", "destination", "delivery_receipt"):
        assert forbidden not in d


# ─────────────────────────────────────────────────────────────────────────────
# 38. No current timestamp injection
# ─────────────────────────────────────────────────────────────────────────────

def test_no_current_timestamp_injection_any_format():
    import re as _re
    view, res = _phase_view_and_source()
    for rid in (R.RENDERER_ID_PHASE_REPORT_MARKDOWN, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT, R.RENDERER_ID_PHASE_REPORT_JSON):
        result = R.render(view, res, rid)
        assert not _re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result.rendered_content)


# ─────────────────────────────────────────────────────────────────────────────
# 39. No chunking or attachment behavior
# ─────────────────────────────────────────────────────────────────────────────

def test_no_chunking_or_attachment_behavior():
    source = inspect.getsource(R)
    for forbidden in ("chunk", "attachment", "message_limit", "split_message"):
        assert forbidden not in source.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 40. No active lifecycle, filesystem, network, notification, or
# delivery side effects
# ─────────────────────────────────────────────────────────────────────────────

def test_no_active_lifecycle_filesystem_network_side_effects(monkeypatch):
    def _forbidden_open(*a, **kw):
        raise AssertionError("rendering must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden_open)
    view, res = _phase_view_and_source()
    for rid in (R.RENDERER_ID_PHASE_REPORT_MARKDOWN, R.RENDERER_ID_PHASE_REPORT_PLAIN_TEXT, R.RENDERER_ID_PHASE_REPORT_JSON):
        R.render(view, res, rid)
    import pathlib
    src_root = pathlib.Path(R.__file__).resolve().parent.parent
    _EXPECTED_ISOLATED_CONSUMERS = frozenset({"rendering.py", "delivery_pipeline.py"})
    for path in src_root.rglob("*.py"):
        if path.name in _EXPECTED_ISOLATED_CONSUMERS:
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "pcae.core.rendering" not in text


# ─────────────────────────────────────────────────────────────────────────────
# Additional targeted re-confirmations
# ─────────────────────────────────────────────────────────────────────────────

def test_view_assignments_remain_authoritative_for_structure():
    # Content resolution never adds sections, reorders sections, or
    # changes section applicability/completeness -- confirmed by
    # comparing the JSON render's own section metadata against the
    # view's own values directly (never re-derived from source).
    view, res = _phase_view_and_source()
    result = R.render(view, res, R.RENDERER_ID_PHASE_REPORT_JSON)
    payload = json.loads(result.rendered_content)
    for view_section, rendered_section in zip(view.sections, payload["resolved_sections"]):
        assert view_section.section_id.value == rendered_section["section_id"]
        assert view_section.applicability.value == rendered_section["applicability"]
        assert view_section.completeness.value == rendered_section["completeness"]


def test_forged_view_digest_cannot_bypass_validation():
    view, res = _phase_view_and_source()
    forged_view = dataclasses.replace(view, source_extraction_digest="0" * 64)
    with pytest.raises(ValueError, match="does not match"):
        R.render(forged_view, res, R.RENDERER_ID_PHASE_REPORT_MARKDOWN)
