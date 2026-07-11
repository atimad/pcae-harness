"""Phase 134E.5: Rendering Architecture.

Implements a deterministic, reusable, transport-independent Rendering
layer over the verified structured derived views (134E.3's Phase
Report View, 134E.4's Operator Report View). Rendering answers exactly
one question: "how shall a verified structured view be transformed
into a presentation format, without changing evidence meaning?" It
never selects evidence, composes new evidence, summarizes
independently, infers missing facts, strengthens conclusions, or
decides delivery strategy.

**This module is not yet active lifecycle authority**, exactly like
``canonical_engineering_evidence.py``, ``evidence_extraction.py``,
``phase_report_view.py``, and ``operator_report_view.py`` before it.
Nothing in the current governed reporting/finalization/notification
path imports or calls into this module. It imports the two view
modules (``phase_report_view``, ``operator_report_view``) and
``evidence_extraction``/``canonical_engineering_evidence`` shared
types, plus stdlib only.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Evidence Extraction
            |
            v
    Derived Evidence View Composition (134E.3, 134E.4)
            |
            v
    Rendering                            <- this module
            |
            v
    Delivery Pipeline                    (134E.6, not implemented)
            |
            v
    Delivery Adapters                    (not implemented)

Design note -- why ``render()`` accepts both a view and its source
``ExtractionResult``: 134E.3/134E.4 deliberately designed their section
models as *references* (category name, requirement level,
applicability, finding classifications) rather than copies of
canonical content, to avoid unnecessary duplication (independently
confirmed correct, not a defect, by 134E.3V/134E.4V). A renderer
consuming only the view therefore cannot reproduce actual field
content (objective text, finding descriptions, governance status
strings) -- it can only reproduce structural facts already present on
the view itself. To produce genuinely content-rich presentation output
while remaining fail-closed against forged input, ``render()`` accepts
the originating ``ExtractionResult`` as a second argument and verifies
it against the view's own recorded ``source_extraction_digest`` before
using it as a value-resolution source. This is not "recomposing a
view" -- no category-to-section assignment, completeness computation,
or profile-rule evaluation runs; the extraction result is used purely
to resolve already-decided category references to their concrete,
already-selected values.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from pcae.core.evidence_extraction import ExtractionResult, SelectedEvidenceItem
from pcae.core.operator_report_view import (
    DecisionCompleteness,
    OPERATOR_SECTION_ORDER,
    OperatorReportCompleteness,
    OperatorReportView,
    OperatorSectionId,
    OperatorSectionRecord,
)
from pcae.core.phase_report_view import (
    PFR_SECTION_ORDER,
    PFRSectionId,
    PhaseReportView,
    SectionRecord,
    ViewCompleteness,
)


VIEW_TYPE_PHASE_REPORT = "phase_report_view"
VIEW_TYPE_OPERATOR_REPORT = "operator_report_view"

MEDIA_TYPE_MARKDOWN = "text/markdown"
MEDIA_TYPE_PLAIN_TEXT = "text/plain"
MEDIA_TYPE_JSON = "application/json"

RENDERER_ID_PHASE_REPORT_MARKDOWN = "phase_report_markdown_v1"
RENDERER_ID_PHASE_REPORT_PLAIN_TEXT = "phase_report_plain_text_v1"
RENDERER_ID_PHASE_REPORT_JSON = "phase_report_json_v1"
RENDERER_ID_OPERATOR_REPORT_MARKDOWN = "operator_report_markdown_v1"
RENDERER_ID_OPERATOR_REPORT_PLAIN_TEXT = "operator_report_plain_text_v1"
RENDERER_ID_OPERATOR_REPORT_JSON = "operator_report_json_v1"

_RENDERER_VERSION = "1.0"


class RenderingCompleteness(str, Enum):
    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


_COMPLETENESS_RANK: dict[str, int] = {
    "complete": 0,
    "complete_with_limitations": 1,
    "incomplete": 2,
    "invalid": 3,
}


def _worse(a: str, b: str) -> str:
    return a if _COMPLETENESS_RANK[a] >= _COMPLETENESS_RANK[b] else b


@dataclass(frozen=True)
class RenderingDiagnostic:
    code: str
    message: str
    blocking: bool

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "blocking": self.blocking}


@dataclass(frozen=True)
class RenderingResult:
    """The deterministic output of one rendering invocation. Contains
    the rendered presentation artifact plus full traceability back to
    its source view and canonical evidence -- never itself a delivery
    payload, never itself finalization/notification authority.
    """

    renderer_id: str
    renderer_version: str
    source_view_type: str
    source_view_id: str
    source_view_version: str
    source_view_digest: str
    source_evidence_id: str
    source_record_digest: str
    profile_id: str
    profile_version: str
    media_type: str
    rendered_content: str
    completeness: RenderingCompleteness
    content_preserved: bool
    diagnostics: tuple[RenderingDiagnostic, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "renderer_id": self.renderer_id,
            "renderer_version": self.renderer_version,
            "source_view_type": self.source_view_type,
            "source_view_id": self.source_view_id,
            "source_view_version": self.source_view_version,
            "source_view_digest": self.source_view_digest,
            "source_evidence_id": self.source_evidence_id,
            "source_record_digest": self.source_record_digest,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "media_type": self.media_type,
            "rendered_content": self.rendered_content,
            "completeness": self.completeness.value,
            "content_preserved": self.content_preserved,
            "diagnostics": [d_.to_dict() for d_ in self.diagnostics],
            "limitations": list(self.limitations),
        }
        if include_digest:
            d["rendering_digest"] = self.compute_digest()
        return d

    def compute_digest(self) -> str:
        """SHA-256 over the canonical sorted-key JSON serialization,
        excluding the digest field itself. Follows the identical
        convention 134E.1-134E.4 established. Includes ``rendered_
        content`` (so material content changes alter it) and excludes
        no field of this model -- there is no rendering/delivery state
        on this model to exclude in the first place (no timestamp, no
        transport, no destination).
        """
        d = self.to_dict(include_digest=False)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Renderer registry -- a small explicit dict, not a plugin framework
# ═══════════════════════════════════════════════════════════════════════

RenderFn = Callable[[Any, ExtractionResult], tuple[str, tuple[RenderingDiagnostic, ...], set]]


@dataclass(frozen=True)
class RendererDescriptor:
    renderer_id: str
    renderer_version: str
    accepted_view_types: frozenset[str]
    media_type: str
    render_fn: RenderFn

    def __post_init__(self) -> None:
        if not self.renderer_id:
            raise ValueError("RendererDescriptor.renderer_id must be non-empty")
        if not self.renderer_version:
            raise ValueError("RendererDescriptor.renderer_version must be non-empty")
        if not self.accepted_view_types:
            raise ValueError("RendererDescriptor.accepted_view_types must be non-empty")
        object.__setattr__(self, "accepted_view_types", frozenset(self.accepted_view_types))


_RENDERER_REGISTRY: dict[str, RendererDescriptor] = {}


def register_renderer(descriptor: RendererDescriptor) -> None:
    """Register a renderer. Fail-closed against silent overwrite,
    mirroring ``evidence_extraction.register_profile()``'s own
    established convention: registering a renderer under an
    already-registered ``renderer_id`` with different content raises;
    an identical re-registration (same id, version, accepted types,
    media type, and render function) is a harmless no-op.
    """
    existing = _RENDERER_REGISTRY.get(descriptor.renderer_id)
    if existing is not None and (
        existing.renderer_version != descriptor.renderer_version
        or existing.accepted_view_types != descriptor.accepted_view_types
        or existing.media_type != descriptor.media_type
        or existing.render_fn is not descriptor.render_fn
    ):
        raise ValueError(
            f"Renderer {descriptor.renderer_id!r} is already registered "
            f"(version {existing.renderer_version!r}); refusing to silently "
            f"overwrite with a different renderer (version "
            f"{descriptor.renderer_version!r}). Register under a new "
            f"renderer_id instead."
        )
    _RENDERER_REGISTRY[descriptor.renderer_id] = descriptor


def get_renderer(renderer_id: str) -> RendererDescriptor:
    if renderer_id not in _RENDERER_REGISTRY:
        raise ValueError(f"Unsupported renderer: {renderer_id!r}")
    return _RENDERER_REGISTRY[renderer_id]


def _view_type_of(view: Any) -> str:
    if isinstance(view, PhaseReportView):
        return VIEW_TYPE_PHASE_REPORT
    if isinstance(view, OperatorReportView):
        return VIEW_TYPE_OPERATOR_REPORT
    raise ValueError(f"Unsupported view type: {type(view)!r}")


# ═══════════════════════════════════════════════════════════════════════
# Deterministic value resolution and escaping helpers
# ═══════════════════════════════════════════════════════════════════════


def _selected_by_category(source: ExtractionResult) -> dict[str, SelectedEvidenceItem]:
    return {item.category: item for item in source.selected_evidence}


def _stringify_value(value: Any) -> tuple[str, ...]:
    """Deterministically render one selected category's canonical value
    into a tuple of plain lines. Never invents, summarizes, or judges
    content -- every branch is a direct, lossless textual projection of
    an already-known structured type.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, tuple):
        lines: list[str] = []
        for item in value:
            lines.extend(_stringify_value(item))
        return tuple(lines)
    if hasattr(value, "to_dict"):
        d = value.to_dict()
        return (json.dumps(d, sort_keys=True, default=str),)
    return (str(value),)


_MARKDOWN_ESCAPE_RE = re.compile(r"([\\`*_{}\[\]()#+\-.!|>~])")


def _escape_markdown(text: str) -> str:
    """Deterministic Markdown metacharacter escaping. Escapes
    metacharacters only; never truncates, never rewrites content, never
    strips control characters (multiline evidence must remain
    multiline). Code-fence sequences (three or more backticks) are
    neutralized by zero-width-joining the backtick run so an embedded
    fence cannot terminate the outer fence prematurely -- content
    remains fully present, only its fence-breaking capability is
    disabled.
    """
    if "```" in text:
        text = text.replace("```", "`​`​`")
    return _MARKDOWN_ESCAPE_RE.sub(r"\\\1", text)


def _escape_plain_text(text: str) -> str:
    """Deterministic plain-text control-character handling. Replaces
    ASCII control characters (except newline and tab) with their
    visible ``\\xNN`` escape so no material content silently
    disappears from terminal/log display; newlines are preserved
    verbatim to keep multiline evidence multiline.
    """
    out = []
    for ch in text:
        code = ord(ch)
        if ch in ("\n", "\t"):
            out.append(ch)
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\x{code:02x}")
        else:
            out.append(ch)
    return "".join(out)


_PHASE_SECTION_TITLES: dict[PFRSectionId, str] = {
    PFRSectionId.PHASE_IDENTITY: "Phase Identity",
    PFRSectionId.EXECUTIVE_SUMMARY: "Executive Summary",
    PFRSectionId.ARCHITECTURAL_FINDINGS: "Architectural Findings",
    PFRSectionId.IMPLEMENTATION_FINDINGS: "Implementation Findings",
    PFRSectionId.VERIFICATION_FINDINGS: "Verification Findings",
    PFRSectionId.TECHNICAL_DEBT_REVIEW: "Technical Debt Review",
    PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE: "Notable Engineering Knowledge",
    PFRSectionId.GOVERNANCE_RESULTS: "Governance Results",
    PFRSectionId.TEST_RESULTS: "Test Results",
    PFRSectionId.NO_GO_CONFIRMATION: "No-Go Confirmation",
    PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION: "Architectural Boundary Confirmation",
    PFRSectionId.TRACK_PROGRESS: "Track Progress",
    PFRSectionId.NEXT_PHASE: "Next Phase",
}

_OPERATOR_SECTION_TITLES: dict[OperatorSectionId, str] = {
    OperatorSectionId.PHASE_OUTCOME: "Phase Outcome",
    OperatorSectionId.KEY_DECISIONS_AND_CHANGES: "Key Engineering Decisions and Changes",
    OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS: "Discoveries, Defects, and Repairs",
    OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS: "Verification and Remaining Findings",
    OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK: "Technical Debt and Deferred Work",
    OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE: "Architectural Significance",
    OperatorSectionId.BOUNDARIES_AND_NO_GO: "Boundaries and No-Go Confirmation",
    OperatorSectionId.TESTS_AND_GOVERNANCE: "Tests and Governance",
    OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE: "Repository and Runtime State",
    OperatorSectionId.NEXT_PHASE_AND_READINESS: "Next Phase and Readiness",
    OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE: "Notable Engineering Knowledge",
    OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS: "Disclosures, Uncertainty, and Limitations",
}


# ═══════════════════════════════════════════════════════════════════════
# Generic section-content resolution (shared by all six renderers)
# ═══════════════════════════════════════════════════════════════════════


def _resolve_section_lines(
    section: Any, selected: dict[str, SelectedEvidenceItem],
    rendered_categories: set[str],
) -> list[str]:
    """Resolve one section's evidence groups into deterministic text
    lines, recording which primary categories were successfully
    resolved (for content-preservation accounting). Cross-referenced
    (non-primary) groups are rendered as a compact classification
    pointer rather than duplicating full content -- the full record
    remains available exactly once, at its primary section.
    """
    lines: list[str] = []
    for group in section.evidence_groups:
        item = selected.get(group.category)
        if group.is_primary:
            lines.append(f"- {group.category} [{group.applicability}, {group.requirement_level}]")
            if group.finding_classifications:
                lines.append(f"  classifications: {', '.join(group.finding_classifications)}")
            if item is not None:
                # Only count a primary category as content-preserved once
                # its actual value has been resolved and written -- a
                # category *label* alone (e.g. when the source no longer
                # carries the item) must never satisfy preservation
                # accounting (134E.5 self-caught finding, fixed before
                # any test asserted the wrong behavior).
                rendered_categories.add(group.category)
                for value_line in _stringify_value(item.value):
                    lines.append(f"  {value_line}")
        else:
            lines.append(
                f"- {group.category} (see primary section) "
                f"[{group.applicability}, {group.requirement_level}]"
                + (f", classifications: {', '.join(group.finding_classifications)}"
                   if group.finding_classifications else "")
            )
    if section.missing_required_categories:
        lines.append(f"- missing/disclosed: {', '.join(section.missing_required_categories)}")
    if section.not_applicable_reason:
        lines.append(f"- not applicable: {section.not_applicable_reason}")
    if section.uncertainty_categories:
        lines.append(f"- uncertainty: {', '.join(section.uncertainty_categories)}")
    if section.limitation_categories:
        lines.append(f"- limitations: {', '.join(section.limitation_categories)}")
    if section.filtering_disclosure_categories:
        lines.append(f"- filtering disclosed: {', '.join(section.filtering_disclosure_categories)}")
    if section.provenance_categories:
        lines.append(f"- provenance: {', '.join(section.provenance_categories)}")
    return lines


# ═══════════════════════════════════════════════════════════════════════
# Phase Report renderers
# ═══════════════════════════════════════════════════════════════════════


def _render_phase_report_markdown(
    view: PhaseReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    lines: list[str] = [
        f"# Phase Report: {view.phase_id}",
        "",
        f"- Phase class: {view.phase_class.value}",
        f"- Report status: {view.report_status}",
        f"- Completeness: {view.completeness.value}",
        f"- Source evidence: `{view.source_evidence_id}` (digest `{view.source_record_digest}`)",
        f"- Extraction profile: {view.profile_id} v{view.profile_version}",
        f"- View version: {view.view_version}",
        "",
    ]
    for section in view.sections:
        title = _PHASE_SECTION_TITLES[section.section_id]
        lines.append(f"## {_escape_markdown(title)}")
        lines.append(f"_applicability: {section.applicability.value}; completeness: {section.completeness.value}_")
        lines.append("")
        for raw_line in _resolve_section_lines(section, selected, rendered_categories):
            lines.append(_escape_markdown(raw_line))
        lines.append("")
    if view.cross_section_uncertainty:
        lines.append(f"**Cross-section uncertainty:** {', '.join(view.cross_section_uncertainty)}")
    if view.cross_section_limitation:
        lines.append(f"**Cross-section limitations:** {', '.join(view.cross_section_limitation)}")
    if view.filtering_disclosures:
        lines.append(f"**Filtering disclosures:** {', '.join(view.filtering_disclosures)}")
    lines.append("")
    lines.append(
        f"---\n_Rendered by {RENDERER_ID_PHASE_REPORT_MARKDOWN} v{_RENDERER_VERSION} "
        f"from view `{view.view_id}` (digest `{view.compute_digest()}`)._"
    )
    return "\n".join(lines), (), rendered_categories


def _render_phase_report_plain_text(
    view: PhaseReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    lines: list[str] = [
        f"PHASE REPORT: {view.phase_id}",
        f"phase class: {view.phase_class.value}",
        f"report status: {view.report_status}",
        f"completeness: {view.completeness.value}",
        f"source evidence: {view.source_evidence_id} (digest {view.source_record_digest})",
        f"extraction profile: {view.profile_id} v{view.profile_version}",
        "",
    ]
    for section in view.sections:
        title = _PHASE_SECTION_TITLES[section.section_id]
        lines.append(f"== {title} ==")
        lines.append(f"applicability: {section.applicability.value}; completeness: {section.completeness.value}")
        for raw_line in _resolve_section_lines(section, selected, rendered_categories):
            lines.append(_escape_plain_text(raw_line))
        lines.append("")
    if view.cross_section_uncertainty:
        lines.append(f"cross-section uncertainty: {', '.join(view.cross_section_uncertainty)}")
    if view.cross_section_limitation:
        lines.append(f"cross-section limitations: {', '.join(view.cross_section_limitation)}")
    if view.filtering_disclosures:
        lines.append(f"filtering disclosures: {', '.join(view.filtering_disclosures)}")
    lines.append(
        f"-- rendered by {RENDERER_ID_PHASE_REPORT_PLAIN_TEXT} v{_RENDERER_VERSION} "
        f"from view {view.view_id} (digest {view.compute_digest()})"
    )
    return "\n".join(lines), (), rendered_categories


def _render_phase_report_json(
    view: PhaseReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    resolved_sections = []
    for section in view.sections:
        section_dict = section.to_dict()
        resolved_values: dict[str, Any] = {}
        for group in section.evidence_groups:
            if group.is_primary:
                item = selected.get(group.category)
                if item is not None:
                    rendered_categories.add(group.category)
                    resolved_values[group.category] = _jsonable_value(item.value)
        section_dict["resolved_values"] = resolved_values
        resolved_sections.append(section_dict)
    payload = {
        "view": view.to_dict(),
        "resolved_sections": resolved_sections,
        "renderer_id": RENDERER_ID_PHASE_REPORT_JSON,
        "renderer_version": _RENDERER_VERSION,
    }
    content = json.dumps(payload, sort_keys=True, default=str, indent=2)
    return content, (), rendered_categories


def _jsonable_value(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_jsonable_value(v) for v in value]
    return value


# ═══════════════════════════════════════════════════════════════════════
# Operator Report renderers
# ═══════════════════════════════════════════════════════════════════════


def _render_operator_report_markdown(
    view: OperatorReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    lines: list[str] = [
        f"# Operator Report: {view.phase_id}",
        "",
        f"- Phase title: {_escape_markdown(view.phase_title) if view.phase_title else '(unavailable)'}",
        f"- Phase class: {view.phase_class.value}",
        f"- Terminal status: {view.terminal_status}",
        f"- Completeness: {view.completeness.value}",
        f"- Decision completeness: {view.decision_completeness.value}",
        f"- Source evidence: `{view.source_evidence_id}` (digest `{view.source_record_digest}`)",
        f"- Extraction profile: {view.profile_id} v{view.profile_version}",
        "",
    ]
    for section in view.sections:
        title = _OPERATOR_SECTION_TITLES[section.section_id]
        lines.append(f"## {_escape_markdown(title)}")
        lines.append(f"_applicability: {section.applicability.value}; completeness: {section.completeness.value}_")
        lines.append("")
        for raw_line in _resolve_section_lines(section, selected, rendered_categories):
            lines.append(_escape_markdown(raw_line))
        lines.append("")
    if view.cross_section_uncertainty:
        lines.append(f"**Cross-section uncertainty:** {', '.join(view.cross_section_uncertainty)}")
    if view.cross_section_limitation:
        lines.append(f"**Cross-section limitations:** {', '.join(view.cross_section_limitation)}")
    if view.filtering_disclosures:
        lines.append(f"**Filtering disclosures:** {', '.join(view.filtering_disclosures)}")
    lines.append("")
    lines.append(
        f"---\n_Rendered by {RENDERER_ID_OPERATOR_REPORT_MARKDOWN} v{_RENDERER_VERSION} "
        f"from view `{view.view_id}` (digest `{view.compute_digest()}`)._"
    )
    return "\n".join(lines), (), rendered_categories


def _render_operator_report_plain_text(
    view: OperatorReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    lines: list[str] = [
        f"OPERATOR REPORT: {view.phase_id}",
        f"phase title: {view.phase_title or '(unavailable)'}",
        f"phase class: {view.phase_class.value}",
        f"terminal status: {view.terminal_status}",
        f"completeness: {view.completeness.value}",
        f"decision completeness: {view.decision_completeness.value}",
        f"source evidence: {view.source_evidence_id} (digest {view.source_record_digest})",
        "",
    ]
    for section in view.sections:
        title = _OPERATOR_SECTION_TITLES[section.section_id]
        lines.append(f"== {title} ==")
        lines.append(f"applicability: {section.applicability.value}; completeness: {section.completeness.value}")
        for raw_line in _resolve_section_lines(section, selected, rendered_categories):
            lines.append(_escape_plain_text(raw_line))
        lines.append("")
    if view.cross_section_uncertainty:
        lines.append(f"cross-section uncertainty: {', '.join(view.cross_section_uncertainty)}")
    if view.cross_section_limitation:
        lines.append(f"cross-section limitations: {', '.join(view.cross_section_limitation)}")
    if view.filtering_disclosures:
        lines.append(f"filtering disclosures: {', '.join(view.filtering_disclosures)}")
    lines.append(
        f"-- rendered by {RENDERER_ID_OPERATOR_REPORT_PLAIN_TEXT} v{_RENDERER_VERSION} "
        f"from view {view.view_id} (digest {view.compute_digest()})"
    )
    return "\n".join(lines), (), rendered_categories


def _render_operator_report_json(
    view: OperatorReportView, source: ExtractionResult,
) -> tuple[str, tuple[RenderingDiagnostic, ...], set[str]]:
    selected = _selected_by_category(source)
    rendered_categories: set[str] = set()
    resolved_sections = []
    for section in view.sections:
        section_dict = section.to_dict()
        resolved_values: dict[str, Any] = {}
        for group in section.evidence_groups:
            if group.is_primary:
                item = selected.get(group.category)
                if item is not None:
                    rendered_categories.add(group.category)
                    resolved_values[group.category] = _jsonable_value(item.value)
        section_dict["resolved_values"] = resolved_values
        resolved_sections.append(section_dict)
    payload = {
        "view": view.to_dict(),
        "resolved_sections": resolved_sections,
        "renderer_id": RENDERER_ID_OPERATOR_REPORT_JSON,
        "renderer_version": _RENDERER_VERSION,
    }
    content = json.dumps(payload, sort_keys=True, default=str, indent=2)
    return content, (), rendered_categories


# ═══════════════════════════════════════════════════════════════════════
# Registration (module load time, deterministic, order-independent)
# ═══════════════════════════════════════════════════════════════════════


register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_PHASE_REPORT_MARKDOWN, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_PHASE_REPORT}), media_type=MEDIA_TYPE_MARKDOWN,
    render_fn=_render_phase_report_markdown,
))
register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_PHASE_REPORT_PLAIN_TEXT, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_PHASE_REPORT}), media_type=MEDIA_TYPE_PLAIN_TEXT,
    render_fn=_render_phase_report_plain_text,
))
register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_PHASE_REPORT_JSON, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_PHASE_REPORT}), media_type=MEDIA_TYPE_JSON,
    render_fn=_render_phase_report_json,
))
register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_OPERATOR_REPORT_MARKDOWN, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_OPERATOR_REPORT}), media_type=MEDIA_TYPE_MARKDOWN,
    render_fn=_render_operator_report_markdown,
))
register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_OPERATOR_REPORT_PLAIN_TEXT, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_OPERATOR_REPORT}), media_type=MEDIA_TYPE_PLAIN_TEXT,
    render_fn=_render_operator_report_plain_text,
))
register_renderer(RendererDescriptor(
    renderer_id=RENDERER_ID_OPERATOR_REPORT_JSON, renderer_version=_RENDERER_VERSION,
    accepted_view_types=frozenset({VIEW_TYPE_OPERATOR_REPORT}), media_type=MEDIA_TYPE_JSON,
    render_fn=_render_operator_report_json,
))


# ═══════════════════════════════════════════════════════════════════════
# Content-preservation accounting
# ═══════════════════════════════════════════════════════════════════════


def _required_primary_categories(view: Any) -> set[str]:
    return {
        g.category
        for s in view.sections
        for g in s.evidence_groups
        if g.is_primary
    }


# ═══════════════════════════════════════════════════════════════════════
# Rendering entry point
# ═══════════════════════════════════════════════════════════════════════


def render(view: Any, source: ExtractionResult, renderer_id: str) -> RenderingResult:
    """Render a verified structured view (``PhaseReportView`` or
    ``OperatorReportView``) using a registered renderer.

    Fail-closed (raises ``ValueError``) for: an unsupported
    ``renderer_id``; a view type the renderer does not accept; a
    ``source`` whose digest does not match the view's own recorded
    ``source_extraction_digest`` (forged/mismatched input); a missing
    source identity/digest on the view itself; an invalid (structurally
    malformed section order, or completeness-invalid) view; or an
    empty successful render.

    Returns normally (never raises) for every ordinary rendering-
    completeness outcome, mirroring the exact posture 134E.1-134E.4
    established for their own entry points.
    """
    view_type = _view_type_of(view)
    descriptor = get_renderer(renderer_id)
    if view_type not in descriptor.accepted_view_types:
        raise ValueError(
            f"Renderer {renderer_id!r} does not accept view type {view_type!r}; "
            f"accepts: {sorted(descriptor.accepted_view_types)}"
        )

    if not view.source_evidence_id:
        raise ValueError("view.source_evidence_id must be non-empty")
    if not view.source_record_digest:
        raise ValueError("view.source_record_digest must be non-empty")

    if source.source_evidence_id != view.source_evidence_id:
        raise ValueError(
            "Forged/mismatched source: source.source_evidence_id "
            f"{source.source_evidence_id!r} != view.source_evidence_id "
            f"{view.source_evidence_id!r}"
        )
    if source.compute_digest() != view.source_extraction_digest:
        raise ValueError(
            "Forged/mismatched source: source.compute_digest() does not "
            "match view.source_extraction_digest"
        )

    if view_type == VIEW_TYPE_PHASE_REPORT:
        expected_order = PFR_SECTION_ORDER
        if view.completeness == ViewCompleteness.INVALID:
            raise ValueError("Cannot render an INVALID Phase Report View")
    else:
        expected_order = OPERATOR_SECTION_ORDER
        if view.completeness == OperatorReportCompleteness.INVALID:
            raise ValueError("Cannot render an INVALID Operator Report View")
        if view.decision_completeness == DecisionCompleteness.INVALID:
            raise ValueError("Cannot render an Operator Report View with INVALID decision completeness")

    actual_order = tuple(s.section_id for s in view.sections)
    if actual_order != tuple(expected_order):
        raise ValueError(
            f"Invalid section order/inventory: {actual_order} != {tuple(expected_order)}"
        )
    if len(actual_order) != len(set(actual_order)):
        raise ValueError("Duplicate section identity detected in view")

    content, render_diagnostics, rendered_categories = descriptor.render_fn(view, source)

    if not content.strip():
        raise ValueError("Renderer produced an empty successful render -- refusing")

    required = _required_primary_categories(view)
    missing = required - rendered_categories
    diagnostics: list[RenderingDiagnostic] = list(render_diagnostics)
    content_preserved = not missing
    if missing:
        diagnostics.append(RenderingDiagnostic(
            code="content_preservation_failure",
            message=f"primary categories not resolved into rendered content: {sorted(missing)}",
            blocking=True,
        ))

    limitations: list[str] = []
    view_completeness_value = view.completeness.value
    rendering_rank_floor = view_completeness_value
    if view_type == VIEW_TYPE_OPERATOR_REPORT:
        # Operator rendering completeness may never exceed decision
        # completeness either -- both dimensions are informational
        # floors this rendering result must respect simultaneously.
        rendering_rank_floor = _worse(rendering_rank_floor, view.decision_completeness.value)
    if not content_preserved:
        rendering_rank_floor = _worse(rendering_rank_floor, "incomplete")
        limitations.append("content_preservation_failure: see diagnostics")

    completeness = RenderingCompleteness(rendering_rank_floor)

    return RenderingResult(
        renderer_id=descriptor.renderer_id,
        renderer_version=descriptor.renderer_version,
        source_view_type=view_type,
        source_view_id=view.view_id,
        source_view_version=view.view_version,
        source_view_digest=view.compute_digest(),
        source_evidence_id=view.source_evidence_id,
        source_record_digest=view.source_record_digest,
        profile_id=view.profile_id,
        profile_version=view.profile_version,
        media_type=descriptor.media_type,
        rendered_content=content,
        completeness=completeness,
        content_preserved=content_preserved,
        diagnostics=tuple(diagnostics),
        limitations=tuple(limitations),
    )
