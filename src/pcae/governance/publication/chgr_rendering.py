"""Deterministic human-readable rendering of a Human Governance Record
(Phase 146G; CHGR-REQ-203, CHGR-001 §3 invariant 4).

``render_human_governance_record`` is a pure function of its input only:
no current-time call, no environment read, no locale-dependent
formatting. Given the same substantive decision content twice, it
produces byte-identical output both times.

Renders only the human-meaningful decision content 146F §3.8 names --
decision subject, template, selection, decision-maker, rationale/
conditions, assurance level, lifecycle state -- deliberately never the
cross-artifact reference fields (``confirmation_evidence_ref``/
``provenance_ref``/``integrity_ref``), which are technical plumbing a
human never confirmed. This also breaks the forward-reference cycle
146F §3.3 (Risk R-1) identifies between
``human_governance_record.integrity_ref`` and
``governance_record_integrity.payload_digest``: the rendering (and its
digest) never needs to wait for ``integrity_ref`` to be finalized.
"""
from __future__ import annotations

from typing import Any, Dict

_NOT_PROVIDED = "(not provided)"


def render_human_governance_record(content: Dict[str, Any]) -> str:
    """Render the substantive content of one Human Governance Record.

    ``content`` need carry only the human-meaningful keys this function
    reads below; any other key (e.g. envelope or cross-reference fields)
    is ignored, never rendered.
    """

    template_ref = content.get("template_ref") or {}
    identity_evidence = content.get("decision_maker_identity_evidence") or {}
    lines = [
        "Human Governance Record",
        "========================",
        f"Decision subject: {content.get('decision_subject') or _NOT_PROVIDED}",
        f"Template: {template_ref.get('template_id') or _NOT_PROVIDED} "
        f"v{template_ref.get('version') or _NOT_PROVIDED}",
        f"Selected option: {content.get('selected_option_id') or _NOT_PROVIDED}",
        f"Decision maker evidence kind: {identity_evidence.get('evidence_kind') or _NOT_PROVIDED}",
        f"Decision maker identifier: {identity_evidence.get('identifier') or _NOT_PROVIDED}",
        f"Rationale: {content.get('rationale') or _NOT_PROVIDED}",
        f"Conditions: {content.get('conditions') or _NOT_PROVIDED}",
        f"Assurance level: {content.get('assurance_level') or _NOT_PROVIDED}",
        f"Lifecycle state: {content.get('lifecycle_state') or _NOT_PROVIDED}",
    ]
    return "\n".join(lines) + "\n"


__all__ = ["render_human_governance_record"]
