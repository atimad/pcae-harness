"""Read-only compatibility adapters for legacy/current artifacts (135E §19).

Every function here reads exactly the file path the caller supplies —
never a directory scan, never "the latest," never `git log` inference. No
adapter mutates the source artifact. Missing fields are disclosed
explicitly (`missing_fields`); nothing is manufactured to fill a gap.

This is the *only* module in this package permitted to parse narrative
report titles — and even here, only for comparison/disclosure, never as an
input to `generator.py`'s identity resolution (135E §8.4, §21 item 1/8, the
direct 135D.1 rehearsal).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pcae.core import phase_id as canonical_phase_id
from pcae.cltr_prototype.models import CompatibilityConfidence, ConformanceClassification

# Phase 137R — narrative-only, comparison-only extraction of a phase id
# from a canonical report's title line (e.g. "# Phase Report: ... (135F)"
# or "Phase 135F — ...") now delegates token scanning and recognition
# entirely to the canonical parser (``pcae.core.phase_id``, CPIPC-001
# §6, §8). Its output is NEVER treated as authoritative; it exists
# solely so `compare()` can disclose a narrative/explicit disagreement.


@dataclass(frozen=True)
class CompatibilityResult:
    artifact_path: str
    artifact_kind: str
    classification: str
    missing_fields: tuple = field(default_factory=tuple)
    identity_confidence: str = CompatibilityConfidence.EXPLICIT_DECLARED.value
    disclosed_identity: dict = field(default_factory=dict)
    limitation: Optional[str] = None


_STRUCTURED_FIELDS_BY_KIND = {
    "canonical_report": ("transition_id", "phase_id", "repository_identity", "branch_identity"),
    "completion_metadata": ("transition_id", "phase_id", "repository_identity"),
    "checkpoint": ("transition_id", "phase_id"),
    "marker": ("transition_id", "phase_id"),
    "receipt": ("transition_id", "phase_id"),
}


def _extract_narrative_phase_id(text: str) -> Optional[str]:
    for line in text.splitlines()[:20]:
        if "phase" not in line.lower():
            continue
        token = canonical_phase_id.find_first_token(line)
        if token is not None:
            return token.source_text
    return None


def classify_legacy_artifact(path: Path, kind: str, *, declared_identity: Optional[dict] = None) -> CompatibilityResult:
    """Classify one explicitly-named artifact against the fields a CLTR
    record's corresponding representation is expected to carry.

    `declared_identity`, if supplied, is the *already-resolved* explicit
    identity (from `identity.resolve_identity`) to compare the artifact's
    own claims against — never used to repair the artifact, only to detect
    and disclose a conflict (135E §8.4/§21).
    """

    path = Path(path)
    if not path.exists():
        return CompatibilityResult(
            artifact_path=str(path),
            artifact_kind=kind,
            classification=ConformanceClassification.UNVERIFIABLE.value,
            missing_fields=tuple(_STRUCTURED_FIELDS_BY_KIND.get(kind, ())),
            limitation="artifact path does not exist",
        )

    text = path.read_text(encoding="utf-8")
    structured: dict = {}
    if path.suffix == ".json":
        try:
            structured = json.loads(text)
        except json.JSONDecodeError:
            return CompatibilityResult(
                artifact_path=str(path),
                artifact_kind=kind,
                classification=ConformanceClassification.UNVERIFIABLE.value,
                limitation="artifact could not be parsed as JSON",
            )

    expected_fields = _STRUCTURED_FIELDS_BY_KIND.get(kind, ())
    missing = tuple(f for f in expected_fields if f not in structured)

    narrative_phase_id = _extract_narrative_phase_id(text) if path.suffix != ".json" else None
    disclosed_identity: dict = {}
    identity_confidence = CompatibilityConfidence.EXPLICIT_DECLARED.value
    if structured:
        disclosed_identity = {k: structured[k] for k in expected_fields if k in structured}
    elif narrative_phase_id is not None:
        disclosed_identity = {"phase_id": narrative_phase_id}
        identity_confidence = CompatibilityConfidence.NARRATIVE_PARSED_COMPARISON_ONLY.value

    conflict_detail: Optional[str] = None
    if declared_identity is not None:
        for key, value in disclosed_identity.items():
            declared_value = declared_identity.get(key)
            if declared_value is not None and value != declared_value:
                conflict_detail = (
                    f"declared {key}={declared_value!r} disagrees with artifact-disclosed {key}={value!r} "
                    f"(source: {identity_confidence}) — reported as a conflict, never silently repaired"
                )

    if conflict_detail is not None:
        classification = ConformanceClassification.CONFLICTING.value
    elif missing and "transition_id" in missing:
        classification = ConformanceClassification.CONFORMANT_WITH_LEGACY_ADAPTER.value
    elif missing:
        classification = ConformanceClassification.INCOMPLETE.value
    else:
        classification = ConformanceClassification.CONFORMANT.value

    return CompatibilityResult(
        artifact_path=str(path),
        artifact_kind=kind,
        classification=classification,
        missing_fields=missing,
        identity_confidence=identity_confidence,
        disclosed_identity=disclosed_identity,
        limitation=conflict_detail,
    )
