"""Stage 2 rehearsal comparison (135Q §22/§31; F-135P-2's
``EXPECTED_REPRESENTATION_DIFFERENCE`` disposition).

Reuses Stage 1's own ``compare()`` (``pcae.cltr.migration.comparison``)
for the authority-relevant legacy-vs-CLTR field comparison unchanged --
Stage 2 never invents a second, competing comparison engine for that
part. This module adds exactly the piece Stage 1 never needed: fields
that cannot match because an external effect Stage 2 never attempts
(notification dispatch) has not occurred, for the three candidate kinds
whose content depends on it (notification, marker, receipt). Those are
classified ``EXPECTED_REPRESENTATION_DIFFERENCE`` -- never a fabricated
match, never a silently dropped/unclassified mismatch (135Q §31,
independently confirmed reachable-and-correct by 135R §32).
"""

from __future__ import annotations

import dataclasses

from pcae.cltr.migration.comparison import ComparisonResult
from pcae.cltr.migration.enums import ComparisonResultClass
from pcae.cltr.migration.rehearsal.enums import EXPECTED_DIFFERENCE_KINDS, CandidateKind


@dataclasses.dataclass(frozen=True)
class RehearsalComparisonSummary:
    stage1_overall_class: ComparisonResultClass
    stage1_authority_relevant_mismatch: bool
    stage1_unverifiable: bool
    expected_difference_kinds: tuple[str, ...]
    mismatch_classes: tuple[str, ...]

    @property
    def blocks_publication(self) -> bool:
        return self.stage1_authority_relevant_mismatch or self.stage1_unverifiable


def summarize(stage1_comparison: ComparisonResult) -> RehearsalComparisonSummary:
    mismatch_classes = tuple(
        sorted({c.result_class.value for c in stage1_comparison.comparisons if c.result_class != ComparisonResultClass.EXACT_MATCH})
    )
    return RehearsalComparisonSummary(
        stage1_overall_class=stage1_comparison.overall_class,
        stage1_authority_relevant_mismatch=stage1_comparison.authority_relevant_mismatch,
        stage1_unverifiable=stage1_comparison.unverifiable,
        expected_difference_kinds=tuple(k.value for k in EXPECTED_DIFFERENCE_KINDS),
        mismatch_classes=mismatch_classes,
    )


def classify_candidate_field(kind: CandidateKind, *, external_effect_occurred: bool) -> ComparisonResultClass:
    """A field on a notification/marker/receipt candidate that depends on
    an external effect Stage 2 never attempts is always
    ``EXPECTED_REPRESENTATION_DIFFERENCE`` when that effect did not
    occur -- never ``EXACT_MATCH`` (fabricated) and never silently
    dropped."""

    if kind in EXPECTED_DIFFERENCE_KINDS and not external_effect_occurred:
        return ComparisonResultClass.EXPECTED_REPRESENTATION_DIFFERENCE
    return ComparisonResultClass.EXACT_MATCH
