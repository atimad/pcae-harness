"""Authority Evaluation Service (AES) -- AESIC-001 v1.3 §5.

AES is the sole orchestrator of the integration surface: the sole reader
of ``Session.owner_identity`` for evaluation purposes, the sole resolver
of Decision Templates, the sole caller of ``AuthorityRegistry.resolve()``,
and the sole invoker of ``evaluate()`` (AESIC-REQ-005/006). It is
stateless between invocations apart from the durable AER store it
delegates all persistence to (AESIC-REQ-017).
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from pcae.authority_evaluation.errors import (
    AuthorityRegistryCorruptError,
    AuthorityRegistryUnavailableError,
)
from pcae.authority_evaluation.evaluation import evaluate
from pcae.aesic.errors import (
    AuthorityEvaluationServiceRegistryCorruptError,
    AuthorityEvaluationServiceRegistryUnavailableError,
    CanonicalPointerUpdateFailedError,
    DecisionTemplateCitationEmptyError,
    DecisionTemplateMalformedError,
    DecisionTemplateNotFoundError,
    DecisionTemplateResolutionFailedError,
    Stage1HandoffInvalidError,
    Stage1HandoffInvalidReason,
)
from pcae.authority_evaluation.models import EVALUATOR_VERSION
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    Stage1EvaluationResult,
    aer_to_payload,
    stage_1_evidence_equivalent,
)
from pcae.authority_evaluation.registry import AuthorityRegistry
from pcae.aesic.resolution import DecisionTemplateResolution
from pcae.aesic.storage import AuthorityEvaluationRecordStore
from pcae.interactive_workflow.models.session import Session

logger = logging.getLogger("pcae.aesic.service")


def _new_evaluation_id() -> str:
    return f"aeval-{uuid.uuid4().hex}"


def _new_record_id() -> str:
    return f"aer-{uuid.uuid4().hex}"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime())


def _outcome_fields_equal(left, right) -> bool:
    """AESIC-REQ-121 comparison (1): every field except ``evaluated_at``."""

    return (
        left.template_ref == right.template_ref
        and left.template_version == right.template_version
        and left.claimed_identity == right.claimed_identity
        and left.evaluation_result == right.evaluation_result
        and left.declaration_ref == right.declaration_ref
        and left.citation_text == right.citation_text
        and left.evaluator_version == right.evaluator_version
        and left.schema_version == right.schema_version
    )


class AuthorityEvaluationService:
    """The sole Authority Evaluation lifecycle orchestrator (§5.1)."""

    def __init__(
        self,
        registry: AuthorityRegistry,
        aer_store: AuthorityEvaluationRecordStore,
        *,
        template_root=None,
    ) -> None:
        self._registry = registry
        self._aer_store = aer_store
        self._resolution = (
            DecisionTemplateResolution(registry, template_root)
            if template_root is not None
            else DecisionTemplateResolution(registry)
        )

    # -- Internal: resolution + evaluation (shared by both stages) ----------

    def _resolve_and_evaluate(self, *, session: Session, evaluation_id: str):
        try:
            resolution = self._resolution.resolve(session.template_ref, session.template_version)
        except (DecisionTemplateNotFoundError, DecisionTemplateMalformedError, DecisionTemplateCitationEmptyError) as exc:
            logger.info(
                "authority_evaluation.resolution_failed evaluation_id=%s template_ref=%s "
                "template_version=%s error=%s",
                evaluation_id,
                session.template_ref,
                session.template_version,
                exc.__class__.__name__,
            )
            raise DecisionTemplateResolutionFailedError(str(exc)) from exc
        except AuthorityRegistryUnavailableError as exc:
            logger.info(
                "authority_evaluation.registry_unavailable evaluation_id=%s template_ref=%s "
                "template_version=%s",
                evaluation_id,
                session.template_ref,
                session.template_version,
            )
            raise AuthorityEvaluationServiceRegistryUnavailableError(str(exc)) from exc
        except AuthorityRegistryCorruptError as exc:
            logger.info(
                "authority_evaluation.registry_corrupt evaluation_id=%s template_ref=%s "
                "template_version=%s",
                evaluation_id,
                session.template_ref,
                session.template_version,
            )
            raise AuthorityEvaluationServiceRegistryCorruptError(str(exc)) from exc

        logger.info(
            "authority_evaluation.resolution_ok evaluation_id=%s template_ref=%s template_version=%s",
            evaluation_id,
            session.template_ref,
            session.template_version,
        )

        outcome = evaluate(
            template_ref=session.template_ref,
            template_version=session.template_version,
            claimed_identity=session.owner_identity,
            declaration=resolution.declaration,
            evaluated_at=_now_iso(),
            evaluator_version=EVALUATOR_VERSION,
            citation_text=resolution.citation_text,
        )
        logger.info(
            "authority_evaluation.evaluated evaluation_id=%s evaluation_result=%s",
            evaluation_id,
            outcome.evaluation_result.value,
        )
        return outcome

    # -- Stage 1: advisory ----------------------------------------------------

    def evaluate_stage_1(self, *, session: Session) -> Stage1EvaluationResult:
        evaluation_id = _new_evaluation_id()
        logger.info("authority_evaluation.stage_1_request evaluation_id=%s session_id=%s", evaluation_id, session.session_id)
        outcome = self._resolve_and_evaluate(session=session, evaluation_id=evaluation_id)
        result = Stage1EvaluationResult(
            outcome=outcome, evaluation_id=evaluation_id, session_id=session.session_id
        )
        logger.info("authority_evaluation.stage_1_result evaluation_id=%s", evaluation_id)
        return result

    # -- Stage 1 handoff validation (AESIC-REQ-123) --------------------------

    def _validate_stage_1_handoff(
        self, *, session: Session, stage_1_result: Optional[Stage1EvaluationResult]
    ) -> Optional[Stage1EvaluationResult]:
        if stage_1_result is None:
            return None

        if not isinstance(stage_1_result, Stage1EvaluationResult):
            raise Stage1HandoffInvalidError(
                Stage1HandoffInvalidReason.MALFORMED,
                f"stage_1_result must be a Stage1EvaluationResult or None, got {stage_1_result!r}.",
            )
        try:
            # Re-validates AuthorityEvaluationOutcome's own construction
            # invariants (structural check 1) by reconstruction.
            _ = stage_1_result.outcome.evaluation_result
        except Exception as exc:  # noqa: BLE001
            raise Stage1HandoffInvalidError(
                Stage1HandoffInvalidReason.MALFORMED,
                f"stage_1_result.outcome is not a well-formed AuthorityEvaluationOutcome: {exc}.",
            ) from exc

        if stage_1_result.session_id != session.session_id:
            raise Stage1HandoffInvalidError(
                Stage1HandoffInvalidReason.SESSION_MISMATCH,
                f"stage_1_result.session_id {stage_1_result.session_id!r} does not match "
                f"session.session_id {session.session_id!r}.",
            )
        if stage_1_result.outcome.claimed_identity != session.owner_identity:
            raise Stage1HandoffInvalidError(
                Stage1HandoffInvalidReason.IDENTITY_MISMATCH,
                f"stage_1_result.outcome.claimed_identity {stage_1_result.outcome.claimed_identity!r} "
                f"does not match session.owner_identity {session.owner_identity!r}.",
            )
        if (
            stage_1_result.outcome.template_ref != session.template_ref
            or stage_1_result.outcome.template_version != session.template_version
        ):
            raise Stage1HandoffInvalidError(
                Stage1HandoffInvalidReason.TEMPLATE_MISMATCH,
                f"stage_1_result.outcome's own template "
                f"({stage_1_result.outcome.template_ref!r}, {stage_1_result.outcome.template_version!r}) "
                f"does not match session's ({session.template_ref!r}, {session.template_version!r}).",
            )
        return stage_1_result

    # -- Stage 2: publication-fresh, persisted -------------------------------

    def evaluate_stage_2(
        self,
        *,
        session: Session,
        package_id: str,
        stage_1_result: Optional[Stage1EvaluationResult] = None,
    ) -> AuthorityEvaluationRecord:
        evaluation_id = _new_evaluation_id()
        logger.info(
            "authority_evaluation.stage_2_request evaluation_id=%s package_id=%s session_id=%s",
            evaluation_id,
            package_id,
            session.session_id,
        )

        # AESIC-REQ-124: validation completes, pass or fail, before any
        # other Stage 2 work begins -- no Registry call, no Resolution
        # attempt, no store write on failure.
        validated_stage_1 = self._validate_stage_1_handoff(session=session, stage_1_result=stage_1_result)

        outcome = self._resolve_and_evaluate(session=session, evaluation_id=evaluation_id)

        evaluated_at = outcome.evaluated_at
        candidate_stage_1_ref = (
            Stage1EvaluationResult(
                outcome=validated_stage_1.outcome,
                evaluation_id=validated_stage_1.evaluation_id,
                session_id=validated_stage_1.session_id,
            )
            if validated_stage_1 is not None
            else None
        )

        # AESIC-REQ-121/023: fresh resolution+evaluation always happens
        # first (above); now compare against the current canonical AER.
        current = self._aer_store.read_canonical(package_id)

        if current is not None and _outcome_fields_equal(current.outcome, outcome) and stage_1_evidence_equivalent(
            current.stage_1_outcome_ref, candidate_stage_1_ref
        ):
            logger.info(
                "authority_evaluation.stage_2_idempotent_noop evaluation_id=%s package_id=%s "
                "canonical_record_id=%s",
                evaluation_id,
                package_id,
                current.record_id,
            )
            return current

        # AESIC-REQ-023(b): changed (or first-ever) -- persist a new,
        # distinct AER under a fresh compound key and advance the pointer.
        record = AuthorityEvaluationRecord(
            record_id=_new_record_id(),
            package_id=package_id,
            evaluation_id=evaluation_id,
            outcome=outcome,
            evaluated_at=evaluated_at,
            stage_1_outcome_ref=candidate_stage_1_ref,
        )
        self._aer_store.write_record(record)
        logger.info(
            "authority_evaluation.aer_committed evaluation_id=%s package_id=%s record_id=%s",
            evaluation_id,
            package_id,
            record.record_id,
        )

        record_digest = aer_to_payload(record)["record_digest"]
        pointer = CanonicalPointer(
            package_id=package_id,
            evaluation_id=evaluation_id,
            record_id=record.record_id,
            record_digest=record_digest,
        )
        try:
            self._aer_store.write_pointer(pointer)
        except OSError as exc:
            logger.warning(
                "authority_evaluation.pointer_update_failed evaluation_id=%s package_id=%s "
                "record_id=%s error=%s",
                evaluation_id,
                package_id,
                record.record_id,
                exc,
            )
            raise CanonicalPointerUpdateFailedError(
                f"AER {record.record_id!r} was committed for package {package_id!r}, but the "
                f"canonical pointer update failed: {exc}. The AER remains durably persisted; "
                "retry the same evaluate_stage_2 call to complete pointer publication."
            ) from exc

        logger.info(
            "authority_evaluation.pointer_updated evaluation_id=%s package_id=%s record_id=%s",
            evaluation_id,
            package_id,
            record.record_id,
        )
        return record


__all__ = ["AuthorityEvaluationService"]
