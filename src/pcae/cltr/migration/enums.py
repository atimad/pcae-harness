"""Stage 1 migration wire enums (Phase 135O).

None of these identifiers are frozen verbatim by 135M/135N (confirmed
during 135O's required source inspection: no ``MigrationStage`` enum or
literal stage token appears in the migration plan or its verification —
only prose stage names/descriptions, §6). 135O therefore names them,
consistent with 135M's six-stage prose description, and documents the
choice here rather than treating it as pre-frozen.
"""

from __future__ import annotations

from enum import Enum


class MigrationStage(str, Enum):
    """135M §6's six prose stages. Only the first two are implemented with
    active behavior by 135O; later values exist as placeholders only and
    must fail closed if ever selected (§4 of the phase brief)."""

    SHADOW_OBSERVATION = "shadow_observation"
    DUAL_DERIVATION_LEGACY_AUTHORITY = "dual_derivation_legacy_authority"
    DUAL_PUBLICATION_REHEARSAL = "dual_publication_rehearsal"
    CLTR_AUTHORITY_WITH_LEGACY_VERIFICATION = "cltr_authority_with_legacy_verification"
    LEGACY_DEMOTION = "legacy_demotion"
    LEGACY_RETIREMENT = "legacy_retirement"


#: Stages 135O actually implements active behavior for. Any other stage
#: value selected via configuration must fail closed (never silently
#: degrade to a supported stage).
ACTIVE_STAGES = frozenset({MigrationStage.SHADOW_OBSERVATION, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY})


class ProductionAuthority(str, Enum):
    """135M §5/§40 authority-epoch vocabulary. Only ``LEGACY`` is ever
    active through Stage 1; ``CLTR`` exists as a schema placeholder only
    and this package never transitions authority to it."""

    LEGACY = "legacy"
    CLTR = "cltr"


class InputStage(str, Enum):
    """135M §8.4's two binding capture points, as actually reconciled by
    135N's repair. §8.4 quotes the assembler as running exactly twice: once
    for "pre-transaction facts" (before either derivation begins) and once
    for "in-transaction completion identities" (captured from legacy's own
    completed sequential path, at the same point ``_observe_shadow_cltr``
    already occupies). 135O's implementation therefore uses exactly these
    two stages rather than inventing the phase brief's illustrative
    four-way Stage A/B/C/D split, which §8.4 itself does not require and
    which the current legacy finalization pipeline does not expose as four
    independently observable points (it returns report/promotion/
    checkpoint/marker/receipt/notification data as one atomic block from
    ``promote_and_dispatch()``). This mapping is documented as a disclosed
    implementation decision, not a silent deviation:

      * Stage A (pre-finalization identity)  -> ``PRE_TRANSACTION``
      * Stage B/C/D (certified/promoted/terminal enrichment) -> collapsed
        into the single ``LEGACY_COMPLETION`` capture, exactly as §8.4
        binds it.
    """

    PRE_TRANSACTION = "pre_transaction_identity_package"
    LEGACY_COMPLETION = "legacy_completion_enrichment"


class ComparisonResultClass(str, Enum):
    """135M §12's comparison-result vocabulary, exact wire identifiers."""

    EXACT_MATCH = "exact_match"
    SEMANTIC_MATCH = "semantic_match"
    UNVERIFIABLE = "unverifiable"
    EXPECTED_REPRESENTATION_DIFFERENCE = "expected_representation_difference"
    LEGACY_MISSING = "legacy_missing"
    CLTR_MISSING = "cltr_missing"
    NON_AUTHORITY_MISMATCH = "non_authority_mismatch"
    AUTHORITY_RELEVANT_MISMATCH = "authority_relevant_mismatch"
    IDENTITY_MISMATCH = "identity_mismatch"
    TRANSITION_MISMATCH = "transition_mismatch"
    STATE_MISMATCH = "state_mismatch"
    DIGEST_MISMATCH = "digest_mismatch"
    COMMIT_OWNERSHIP_MISMATCH = "commit_ownership_mismatch"
    NOTIFICATION_MISMATCH = "notification_mismatch"
    MARKER_MISMATCH = "marker_mismatch"
    RECEIPT_MISMATCH = "receipt_mismatch"
    TEMPORAL_ORDER_MISMATCH = "temporal_order_mismatch"
    RECOVERY_CLASSIFICATION_MISMATCH = "recovery_classification_mismatch"


#: Deterministic precedence when multiple mismatch classes apply to the
#: same field comparison (lower index = higher precedence / reported
#: first). Authority-relevant classes always precede non-authority ones.
COMPARISON_RESULT_PRECEDENCE: tuple[ComparisonResultClass, ...] = (
    ComparisonResultClass.IDENTITY_MISMATCH,
    ComparisonResultClass.TRANSITION_MISMATCH,
    ComparisonResultClass.STATE_MISMATCH,
    ComparisonResultClass.DIGEST_MISMATCH,
    ComparisonResultClass.COMMIT_OWNERSHIP_MISMATCH,
    ComparisonResultClass.NOTIFICATION_MISMATCH,
    ComparisonResultClass.MARKER_MISMATCH,
    ComparisonResultClass.RECEIPT_MISMATCH,
    ComparisonResultClass.TEMPORAL_ORDER_MISMATCH,
    ComparisonResultClass.RECOVERY_CLASSIFICATION_MISMATCH,
    ComparisonResultClass.AUTHORITY_RELEVANT_MISMATCH,
    ComparisonResultClass.NON_AUTHORITY_MISMATCH,
    ComparisonResultClass.LEGACY_MISSING,
    ComparisonResultClass.CLTR_MISSING,
    ComparisonResultClass.UNVERIFIABLE,
    ComparisonResultClass.EXPECTED_REPRESENTATION_DIFFERENCE,
    ComparisonResultClass.SEMANTIC_MATCH,
    ComparisonResultClass.EXACT_MATCH,
)

#: Classes that block Stage 1 migration-progression eligibility (§33 of
#: the phase brief; §12/§20 of 135M). Never includes plain
#: ``UNVERIFIABLE`` collapse-to-strength -- unverifiable also blocks
#: eligibility (handled explicitly in comparison.py), it is simply not an
#: "authority-relevant mismatch" class by name.
AUTHORITY_RELEVANT_CLASSES = frozenset(
    {
        ComparisonResultClass.AUTHORITY_RELEVANT_MISMATCH,
        ComparisonResultClass.IDENTITY_MISMATCH,
        ComparisonResultClass.TRANSITION_MISMATCH,
        ComparisonResultClass.STATE_MISMATCH,
        ComparisonResultClass.DIGEST_MISMATCH,
        ComparisonResultClass.COMMIT_OWNERSHIP_MISMATCH,
        ComparisonResultClass.NOTIFICATION_MISMATCH,
        ComparisonResultClass.MARKER_MISMATCH,
        ComparisonResultClass.RECEIPT_MISMATCH,
        ComparisonResultClass.TEMPORAL_ORDER_MISMATCH,
        ComparisonResultClass.RECOVERY_CLASSIFICATION_MISMATCH,
    }
)


class MigrationRecoveryClassification(str, Enum):
    """Explicit recovery classification the *caller* must supply (never
    inferred from titles, latest files, or git history -- phase brief
    §26)."""

    ORDINARY = "ordinary_finalization"
    TASK_FINISH = "task_finish_finalization"
    PHASE_COMPLETE = "phase_complete_finalization"
    REPORT_CREATE_RECOVERY = "report_create_recovery"
    ALLOW_PARTIAL_REPORT_RECOVERY = "allow_partial_report_recovery"
    MANUAL_RECOVERY = "manual_governed_recovery"
    PAUSED_TASK = "paused_task_handling"
    STALE_METADATA_CONFLICT = "stale_metadata_conflict"
    UNCERTAIN_PROMOTION = "uncertain_promotion"
    REJECTED_CANDIDATE = "rejected_candidate"
    PARTIAL_CANDIDATE = "partial_candidate"
    RECONCILIATION_ONLY = "reconciliation_only_inspection"


#: Recovery classifications that must never receive migration progression
#: credit or a conformant comparison result, regardless of comparison
#: outcome (135H.1 escape prevention, phase brief §27).
NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS = frozenset(
    {
        MigrationRecoveryClassification.REJECTED_CANDIDATE,
        MigrationRecoveryClassification.PARTIAL_CANDIDATE,
        MigrationRecoveryClassification.STALE_METADATA_CONFLICT,
        MigrationRecoveryClassification.UNCERTAIN_PROMOTION,
        MigrationRecoveryClassification.RECONCILIATION_ONLY,
    }
)
