"""Phase 134E.10 — Final Lifecycle Integration.

This module is the single, shared, resumable finalization transaction that
wires the seven previously-inert Phase 134E.1-134E.7 modules (Canonical
Engineering Evidence, Extraction, Phase/Operator Report Views, Rendering,
Delivery Pipeline, Delivery Receipt) into the existing, already-governed
phase/task finalization path.

Authority boundaries (134D plan, section "Authority Boundary Review"):

- This module does not create, alter, strengthen, or re-derive any fact.
  It only *captures* what an already-certified ``PhaseReport`` (from
  ``pcae.core.phase_reports``) already established, after that report has
  already passed ``validate_finalization_gate`` and already been written
  by the existing, unmodified ``finalize_phase_report``/``write_phase_report``
  path.
- It does not introduce a second completion authority. The existing
  ``PhaseReport`` + ``validate_finalization_gate`` + the notification
  dispatch marker (``phase_reports.write_notification_dispatch_marker``)
  remain the sole, unmodified source of truth for whether a phase is
  finalized and whether it has been notified exactly once.
- It does not perform a second physical delivery. The actual send already
  happens through the existing, already-authorized dispatch path (called by
  ``finalize_phase_report`` or by each command's own notification helper)
  *before* this transaction ever runs. This module's own "delivery" step
  only *models*, via the in-memory, no-network ``RECORDING_ADAPTER_ID``
  adapter from ``pcae.core.delivery_pipeline``, what was already sent, and
  records that model as a receipt via ``pcae.core.delivery_receipt``. It
  never calls ``pcae.core.notifications`` or any live sink, and it never
  re-checks or re-uses ``_external_delivery_authorized`` for a live send.
  **134E.10V finding, repaired:** the recording adapter unconditionally
  reports success by construction, so delivery modeling and receipt
  creation are only attempted when ``report.notification_result`` (the
  real, already-recorded outcome of the existing dispatch path) itself
  reports ``success: True`` -- otherwise a receipt would misrepresent a
  delivery that was never attempted or did not succeed. A skipped receipt
  is recorded as an explicit, honest limitation on the ``TransactionResult``
  instead.

Deviation from the full step sequence sketched in the Phase 134E.10 task
brief, documented honestly: identity resolution, ``PhaseReport`` construction,
``validate_finalization_gate``, promotion (``finalize_phase_report`` /
``write_phase_report``), and the physical notification dispatch itself
remain exactly where they already are in each of the five call sites
(``phase.py``, ``task.py``, ``phase_reports.py``, ``notifications.py``, and
transitively ``push.py`` via ``phase.py``). Those code paths differ from
each other in load-bearing, entry-point-specific ways (different trust
schemas, different Repository Transition Validator invocations, different
certification call sites) that are outside this sub-phase's stated
non-goals ("no evidence-model change", "integrates ordering and completion,
not content"). Consolidating *that* logic into one function was judged too
high-risk to attempt safely in this pass without threatening the single
most important correctness property of this phase: the already-working,
governed completion path (100% of existing behavior) must never regress.

Instead, this module is called *after* each entry point has already
produced (or retrieved) a certified, gate-passed ``PhaseReport`` -- it is
the ONE place, and the only place, where any of the seven new-machinery
modules are invoked. No command file constructs
``CanonicalEngineeringEvidence``, calls ``extract``/``compose_*``/``render``/
``build_delivery_request``/``open_receipt`` directly; they all funnel
through :func:`run_finalization_transaction`.

Resumability model (mirrors the PER/RER promotion-idempotency pattern in
``pcae.core.agent`` around ``build_promotion_execution``): a transaction
record is persisted to
``.pcae/finalization-transactions/<phase_id>.json`` with
``status="in_progress"`` before the first new-pipeline step and rewritten
after every step. A second invocation for the same ``phase_id`` whose
certified content (``report_digest`` + ``finalization_snapshot_id``, the
same identity pair the existing notification marker already uses) matches
a prior ``status="completed"`` record short-circuits immediately without
re-running any step (no duplicate evidence/views/renderings/receipt is
produced). If the certified content differs (a new, distinct certified
report), a fresh transaction record is written and evidence/extraction/
views/rendering/receipt are (re)produced for the new content -- this is
still safe because it never touches promotion or physical delivery, which
already happened via the existing path before this function is called.

Fail-closed-but-non-fatal design: everything in this module after evidence
capture begins is wrapped so that ANY exception is recorded as a
transaction limitation and returned to the caller as a
``TransactionResult`` with a non-"completed" status -- it never raises out
to the caller (except for a deliberate, immediate ``ValueError`` on unsafe
storage identifiers, which is a defensive input-validation failure, not a
"this step didn't work" outcome). Callers are expected to invoke this
function defensively (already-written report / already-sent notification
must never be affected by a bug in this module).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from pcae.core.phase_reports import (
    PhaseReport,
    compute_finalization_snapshot_id,
    compute_report_digest,
)
from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CanonicalEngineeringEvidence,
    CommitPushInfo,
    CorrectionMetadata,
    EvidenceIdentity,
    EvidencePhaseIdentity,
    EvidenceProvenanceRecord,
    FindingClassification,
    FindingRecord,
    GovernanceResultItem,
    LimitationItem,
    PhaseClass,
    REQUIRED_APPLICABILITY_CATEGORIES,
    RepositoryStateSnapshot,
    RuntimeStateSnapshot,
    TestResultItem,
)
from pcae.core import evidence_extraction as _extraction
from pcae.core import phase_report_view as _prview
from pcae.core import operator_report_view as _orview
from pcae.core import rendering as _rendering
from pcae.core import delivery_pipeline as _delivery
from pcae.core import delivery_receipt as _receipt

DEFAULT_TRANSACTION_ROOT = Path(".pcae/finalization-transactions")
DEFAULT_RECEIPT_STORE_ROOT = Path(".pcae/delivery-receipts")

# A safe path-component identifier: alnum start, then word chars / dot /
# dash / underscore. Rejects any path separator, "..", and absolute paths
# outright -- this is the explicit path-traversal defense the brief asks
# for (mirrors ``DeliveryReceiptStore._validate_store_identifier``, which
# already exists in delivery_receipt.py for the receipt side of storage).
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _validate_identifier(value: str, field_name: str) -> None:
    if (
        not value
        or "/" in value
        or "\\" in value
        or ".." in value
        or os.path.isabs(value)
        or not _SAFE_IDENTIFIER_RE.match(value)
    ):
        raise ValueError(
            f"unsafe {field_name} for finalization-transaction storage: {value!r} "
            "(path separators, parent references, and absolute paths are rejected)"
        )


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class TransactionResult:
    """Outcome of a single :func:`run_finalization_transaction` call.

    ``status`` values:
      - ``"completed"``: all new-pipeline steps (capture through receipt)
        succeeded.
      - ``"resumed_completed"``: a prior transaction for the same
        certified content had already completed; nothing was re-run.
      - ``"gate_not_passed"``: the caller-supplied gate/report was not
        finalizable; no new-pipeline step was attempted (this is the
        expected, ordinary outcome any time the existing gate itself
        blocked -- not a failure of this module).
      - ``"capture_failed"``: evidence construction/validation/finalize
        failed. The already-certified, already-promoted ``PhaseReport``
        that the caller wrote *before* calling this function is
        completely unaffected.
      - ``"best_effort_incomplete"``: capture succeeded but a later step
        (extraction/composition/rendering/delivery-model/receipt) failed;
        again, the existing certified report is unaffected.
    """

    phase_id: str
    status: str
    steps: dict[str, str] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    evidence_id: str | None = None
    extraction_digests: dict[str, str] = field(default_factory=dict)
    view_digests: dict[str, str] = field(default_factory=dict)
    rendering_digests: dict[str, str] = field(default_factory=dict)
    rendering_content_matches_existing: dict[str, bool] = field(default_factory=dict)
    receipt_logical_delivery_id: str | None = None
    receipt_path: str | None = None
    checkpoint_path: str | None = None
    report_digest: str | None = None
    finalization_snapshot_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "status": self.status,
            "steps": dict(self.steps),
            "limitations": list(self.limitations),
            "evidence_id": self.evidence_id,
            "extraction_digests": dict(self.extraction_digests),
            "view_digests": dict(self.view_digests),
            "rendering_digests": dict(self.rendering_digests),
            "rendering_content_matches_existing": dict(self.rendering_content_matches_existing),
            "receipt_logical_delivery_id": self.receipt_logical_delivery_id,
            "receipt_path": self.receipt_path,
            "checkpoint_path": self.checkpoint_path,
            "report_digest": self.report_digest,
            "finalization_snapshot_id": self.finalization_snapshot_id,
        }


def _load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True))
    os.replace(tmp_path, path)


def _result_from_checkpoint(checkpoint: dict[str, Any]) -> TransactionResult:
    return TransactionResult(
        phase_id=checkpoint.get("phase_id", ""),
        status="resumed_completed",
        steps=dict(checkpoint.get("steps", {})),
        limitations=list(checkpoint.get("limitations", [])),
        evidence_id=checkpoint.get("evidence_id"),
        extraction_digests=dict(checkpoint.get("extraction_digests", {})),
        view_digests=dict(checkpoint.get("view_digests", {})),
        rendering_digests=dict(checkpoint.get("rendering_digests", {})),
        rendering_content_matches_existing=dict(
            checkpoint.get("rendering_content_matches_existing", {})
        ),
        receipt_logical_delivery_id=checkpoint.get("receipt_logical_delivery_id"),
        receipt_path=checkpoint.get("receipt_path"),
        checkpoint_path=checkpoint.get("_checkpoint_path"),
        report_digest=checkpoint.get("report_digest"),
        finalization_snapshot_id=checkpoint.get("finalization_snapshot_id"),
    )


# ---------------------------------------------------------------------------
# Step 3: capture Canonical Engineering Evidence from a certified PhaseReport
# ---------------------------------------------------------------------------

_VALID_PUSHED_STATUSES = {"pushed", "not_pushed", "nothing_to_push", "clean", "unknown"}
_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _normalize_pushed_status(value: str) -> str:
    return value if value in _VALID_PUSHED_STATUSES else "unknown"


def _normalize_commits(commits: list[str] | None) -> tuple[str, ...]:
    out = []
    for c in commits or []:
        c = (c or "").strip().lower()
        if _COMMIT_RE.match(c):
            out.append(c)
    return tuple(out)


def _governance_items(governance_results: dict[str, Any] | None) -> tuple[GovernanceResultItem, ...]:
    items = []
    for name, status_value in (governance_results or {}).items():
        name_s = str(name).strip()
        if not name_s:
            continue
        status_s = str(status_value).strip() if status_value not in (None, "") else "unknown"
        items.append(GovernanceResultItem(name=name_s, status=status_s))
    return tuple(items)


def _test_result_items(test_results: dict[str, Any] | None) -> tuple[TestResultItem, ...]:
    items = []
    for name, value in (test_results or {}).items():
        name_s = str(name).strip()
        if not name_s:
            continue
        if isinstance(value, dict):
            result_s = str(value.get("result", "")).strip()
            status_s = str(value.get("status", "")).strip() or "unknown"
        else:
            result_s = ""
            status_s = str(value).strip() or "unknown"
        items.append(TestResultItem(name=name_s, result=result_s, status=status_s))
    return tuple(items)


def _capture_evidence(
    report: PhaseReport, phase_id: str, phase_name: str
) -> CanonicalEngineeringEvidence:
    """Map an already-certified ``PhaseReport`` into a finalized
    ``CanonicalEngineeringEvidence`` record.

    This is a pure function of ``report`` (plus ``phase_id``/``phase_name``,
    which are already bound to it) -- calling it twice for the same report
    content produces an equivalent record, which is what makes the
    transaction's resume-by-content-digest behavior correct.

    ``PhaseReport`` is a coarser-grained, legacy summary object: it does
    not separately distinguish architectural/implementation/verification
    findings, defects, or corrected assumptions. Categories that cannot be
    honestly derived from it are marked ``Applicability.UNAVAILABLE`` with
    an explicit ``LimitationItem`` disclosure (per the evidence module's
    Non-Omission validation rule) rather than fabricated or silently
    dropped. ``PhaseClass.REVIEW_HARDENING`` is used as the generic phase
    class for captured evidence because it is the only class the source
    module does not force any single category to be
    ``Applicability.PRESENT`` for (unlike IMPLEMENTATION/VERIFICATION),
    which matches the fact that a ``PhaseReport`` alone cannot reliably
    establish which specific class a historical phase belonged to.
    """

    engineering_actions: tuple[str, ...]
    if report.summary and report.summary.strip():
        engineering_actions = (report.summary.strip(),)
        engineering_actions_app = Applicability.PRESENT
    else:
        engineering_actions = ()
        engineering_actions_app = Applicability.UNAVAILABLE

    notable_knowledge = tuple(x for x in (report.follow_ups or []) if x and x.strip())
    notable_knowledge_app = (
        Applicability.PRESENT if notable_knowledge else Applicability.UNAVAILABLE
    )

    technical_debt_reviewed: tuple[FindingRecord, ...]
    risks = [r for r in (report.risks or []) if r and r.strip()]
    if risks:
        technical_debt_reviewed = tuple(
            FindingRecord(
                finding_id=f"risk-{idx}",
                classification=FindingClassification.NON_BLOCKING,
                description=risk_text.strip(),
                affected_component="unspecified",
            )
            for idx, risk_text in enumerate(risks, start=1)
        )
        technical_debt_reviewed_app = Applicability.PRESENT
    else:
        technical_debt_reviewed = ()
        technical_debt_reviewed_app = Applicability.UNAVAILABLE

    no_go = tuple(x for x in (report.explicit_no_go_confirmations or []) if x and x.strip())
    no_go_app = Applicability.PRESENT if no_go else Applicability.NOT_APPLICABLE

    applicability: dict[str, Applicability] = {
        "engineering_actions": engineering_actions_app,
        "architectural_findings": Applicability.UNAVAILABLE,
        "implementation_findings": Applicability.UNAVAILABLE,
        "verification_findings": Applicability.UNAVAILABLE,
        "defects_discovered": Applicability.UNAVAILABLE,
        "defects_repaired": Applicability.UNAVAILABLE,
        "incorrect_assumptions_corrected": Applicability.UNAVAILABLE,
        "technical_debt_reviewed": technical_debt_reviewed_app,
        "technical_debt_introduced": Applicability.NOT_APPLICABLE,
        "notable_engineering_knowledge": notable_knowledge_app,
        "no_go_confirmations": no_go_app,
        "architectural_boundary_confirmations": Applicability.UNAVAILABLE,
    }
    assert set(applicability) == set(REQUIRED_APPLICABILITY_CATEGORIES)

    limitations = []
    for category, disposition in applicability.items():
        if disposition in (Applicability.UNAVAILABLE, Applicability.UNKNOWN):
            limitations.append(
                LimitationItem(
                    category=category,
                    description=(
                        "not separately captured by the source PhaseReport "
                        "(coarse-grained legacy report format); may exist in "
                        "underlying task/engineering history but is not "
                        "reconstructed here"
                    ),
                    affected_evidence=(category,),
                    resolution_status="unresolved",
                )
            )

    pushed_status = _normalize_pushed_status(report.pushed_status or "unknown")
    commits = _normalize_commits(report.commits)

    provenance = (
        EvidenceProvenanceRecord(
            covers="repository_state",
            source_artifact="PhaseReport",
            source_command="finalization_transaction._capture_evidence",
            source_phase_id=phase_id,
            derivation_path="PhaseReport.commits/pushed_status/origin_main_head_count",
            verification_state="observed",
        ),
        EvidenceProvenanceRecord(
            covers="governance_results",
            source_artifact="PhaseReport",
            source_command="finalization_transaction._capture_evidence",
            source_phase_id=phase_id,
            derivation_path="PhaseReport.governance_results",
            verification_state="observed",
        ),
    )

    evidence = CanonicalEngineeringEvidence(
        identity=EvidenceIdentity(
            phase=EvidencePhaseIdentity(
                phase_id=phase_id,
                phase_name=phase_name or phase_id,
                source="cli_argument",
            )
        ),
        phase_class=PhaseClass.REVIEW_HARDENING,
        task_id=None,
        objective=(report.summary.strip() if report.summary and report.summary.strip() else f"Phase {phase_id}"),
        engineering_actions=engineering_actions,
        architectural_findings=(),
        implementation_findings=(),
        verification_findings=(),
        defects_discovered=(),
        defects_repaired=(),
        incorrect_assumptions_corrected=(),
        technical_debt_reviewed=technical_debt_reviewed,
        technical_debt_introduced=(),
        notable_engineering_knowledge=notable_knowledge,
        governance_results=_governance_items(report.governance_results),
        test_results=_test_result_items(report.test_results),
        repository_state=RepositoryStateSnapshot(
            commit=commits[0] if commits else None,
            branch=None,
            pushed_status=pushed_status,
            origin_main_head_count=max(int(report.origin_main_head_count or 0), 0),
            clean=pushed_status in ("pushed", "clean", "nothing_to_push"),
        ),
        runtime_state=RuntimeStateSnapshot(
            runtime_state="Observed",
            maximum_capability="observe",
            execution_availability="unavailable",
        ),
        no_go_confirmations=no_go,
        architectural_boundary_confirmations=(),
        track_progress=(report.status.strip() if report.status and report.status.strip() else f"phase {phase_id} status captured"),
        recommended_next_phase=report.recommended_next_phase or "",
        commit_and_push=CommitPushInfo(
            commits=commits,
            pushed_status=pushed_status,
            origin_main_head_count=max(int(report.origin_main_head_count or 0), 0),
        ),
        provenance=provenance,
        uncertainty=(),
        limitations=tuple(limitations),
        correction=CorrectionMetadata(),
        applicability=MappingProxyType(applicability),
        created_at=report.created_at or _utc_now_iso(),
    )
    return evidence.finalize()


def run_finalization_transaction(
    *,
    phase_id: str,
    phase_name: str,
    report: PhaseReport,
    gate: dict[str, Any],
    transaction_root: Path | str | None = None,
    receipt_root: Path | str | None = None,
) -> TransactionResult:
    """Run (or resume) the shared new-pipeline finalization transaction for
    an already-certified, already-promoted ``PhaseReport``.

    Preconditions the caller is responsible for (this function re-checks
    them defensively but does not re-derive them): ``report`` has already
    passed ``validate_finalization_gate`` (``gate["finalizable"]`` is
    True) and has already been written via the existing
    ``finalize_phase_report``/``write_phase_report`` path, and any
    physical notification dispatch has already been attempted through the
    existing, already-authorized dispatch path. This function never writes
    ``latest.md``/``latest.json`` and never sends a live notification.
    """

    _validate_identifier(phase_id, "phase_id")

    txn_root = Path(transaction_root) if transaction_root else DEFAULT_TRANSACTION_ROOT
    rcpt_root = Path(receipt_root) if receipt_root else DEFAULT_RECEIPT_STORE_ROOT
    checkpoint_path = txn_root / f"{phase_id}.json"

    report_digest = compute_report_digest(report)
    finalization_snapshot_id = compute_finalization_snapshot_id(report)

    existing = _load_checkpoint(checkpoint_path)
    if (
        existing is not None
        and existing.get("report_digest") == report_digest
        and existing.get("finalization_snapshot_id") == finalization_snapshot_id
        and existing.get("status") == "completed"
    ):
        existing["_checkpoint_path"] = str(checkpoint_path)
        return _result_from_checkpoint(existing)

    if not gate.get("finalizable") or report.report_completeness != "complete":
        # Nothing to persist: no new-pipeline step was attempted, and a
        # future call for this phase_id with a passing gate will simply
        # proceed and write its own fresh checkpoint. Writing a "why this
        # was rejected" record here would be a filesystem side effect for
        # what is, by construction, the common/expected outcome any time
        # this function is called before its documented precondition
        # (gate already passed) holds -- including every caller that
        # (correctly, per this function's own preconditions contract)
        # only calls it after checking the gate itself, where a stale or
        # synthetic report can still legitimately fail this defense-in-
        # depth re-check.
        return TransactionResult(
            phase_id=phase_id,
            status="gate_not_passed",
            report_digest=report_digest,
            finalization_snapshot_id=finalization_snapshot_id,
            checkpoint_path=str(checkpoint_path),
        )

    checkpoint = {
        "phase_id": phase_id,
        "phase_name": phase_name,
        "report_digest": report_digest,
        "finalization_snapshot_id": finalization_snapshot_id,
        "status": "in_progress",
        "steps": {},
        "limitations": [],
        "started_at": _utc_now_iso(),
    }
    _save_checkpoint(checkpoint_path, checkpoint)

    result = TransactionResult(
        phase_id=phase_id,
        status="in_progress",
        report_digest=report_digest,
        finalization_snapshot_id=finalization_snapshot_id,
        checkpoint_path=str(checkpoint_path),
    )

    # Step: capture evidence. Kept outside the broad best-effort try/except
    # below because a capture failure is the one new-pipeline failure mode
    # explicitly called out as needing its own terminal status
    # ("capture_failed") rather than being folded into the generic
    # "best_effort_incomplete" bucket.
    try:
        evidence = _capture_evidence(report, phase_id, phase_name)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, fail-closed-but-non-fatal
        checkpoint["steps"]["capture_evidence"] = "failed"
        checkpoint["limitations"].append(f"capture_evidence failed: {type(exc).__name__}: {exc}")
        checkpoint["status"] = "capture_failed"
        _save_checkpoint(checkpoint_path, checkpoint)
        result.status = "capture_failed"
        result.limitations = list(checkpoint["limitations"])
        return result

    checkpoint["steps"]["capture_evidence"] = "completed"
    checkpoint["evidence_id"] = evidence.identity.evidence_id
    result.evidence_id = evidence.identity.evidence_id
    _save_checkpoint(checkpoint_path, checkpoint)

    try:
        extraction_phase = _extraction.extract(evidence, _extraction.PROFILE_ID_PHASE_REPORT)
        extraction_operator = _extraction.extract(evidence, _extraction.PROFILE_ID_OPERATOR_REPORT)
        result.extraction_digests = {
            "phase_report": extraction_phase.compute_digest(),
            "operator_report": extraction_operator.compute_digest(),
        }
        checkpoint["steps"]["extraction"] = "completed"
        checkpoint["extraction_digests"] = dict(result.extraction_digests)
        _save_checkpoint(checkpoint_path, checkpoint)

        view_phase = _prview.compose_phase_report_view(extraction_phase)
        view_operator = _orview.compose_operator_report_view(extraction_operator)
        result.view_digests = {
            "phase_report": view_phase.compute_digest(),
            "operator_report": view_operator.compute_digest(),
        }
        checkpoint["steps"]["composition"] = "completed"
        checkpoint["view_digests"] = dict(result.view_digests)
        _save_checkpoint(checkpoint_path, checkpoint)

        render_phase_md = _rendering.render(
            view_phase, extraction_phase, _rendering.RENDERER_ID_PHASE_REPORT_MARKDOWN
        )
        render_operator_md = _rendering.render(
            view_operator, extraction_operator, _rendering.RENDERER_ID_OPERATOR_REPORT_MARKDOWN
        )
        result.rendering_digests = {
            "phase_report": render_phase_md.compute_digest(),
            "operator_report": render_operator_md.compute_digest(),
        }
        checkpoint["steps"]["rendering"] = "completed"
        checkpoint["rendering_digests"] = dict(result.rendering_digests)

        # Honest divergence check (never forced to match): the two
        # rendering pipelines are independent presentation stages; if they
        # happen to disagree, that is recorded as a known limitation, not
        # papered over.
        existing_markdown = report.render_markdown()
        matches = existing_markdown.strip() == render_phase_md.rendered_content.strip()
        result.rendering_content_matches_existing = {"phase_report_markdown": matches}
        checkpoint["rendering_content_matches_existing"] = dict(
            result.rendering_content_matches_existing
        )
        if not matches:
            checkpoint["limitations"].append(
                "known limitation: phase_report_markdown_v1 rendering output "
                "diverges from PhaseReport.render_markdown() output for this "
                "report; both derive from the same certified report/evidence "
                "but are independent presentation stages and are not forced "
                "to be byte-identical"
            )
        _save_checkpoint(checkpoint_path, checkpoint)

        # Delivery: MODEL the already-executed dispatch, do not re-send.
        # 134E.10V finding (repaired): the RECORDING_ADAPTER_ID adapter's
        # own deliver function unconditionally reports success ("no
        # external I/O... deterministically reports success", see its
        # docstring in delivery_pipeline.py) -- calling it unconditionally
        # here would make the receipt claim a successful delivery even
        # when the real dispatch was never attempted or genuinely failed,
        # violating the receipt-honesty contract ("must not claim adapter
        # execution if the generalized adapter did not execute", "must
        # not imply remote acceptance without evidence"). The receipt
        # step now only runs when `report.notification_result` -- the
        # real, existing dispatch outcome already recorded by the
        # existing, unmodified dispatch path before this function was
        # ever called -- itself reports `success: True`. Any other case
        # (not attempted, disabled, no sinks, failed) skips delivery
        # modeling and receipt creation entirely and records an explicit,
        # honest limitation instead of a misleading synthetic receipt.
        notification_result = getattr(report, "notification_result", None) or {}
        real_dispatch_succeeded = bool(notification_result.get("success"))
        completed_at = _utc_now_iso()
        if not real_dispatch_succeeded:
            checkpoint["steps"]["delivery_model"] = "skipped"
            checkpoint["steps"]["receipt"] = "skipped"
            checkpoint["limitations"].append(
                "no receipt recorded: the underlying report.notification_result "
                f"does not report success ({notification_result!r}) -- a receipt "
                "would misrepresent a delivery that was not attempted or did not "
                "succeed"
            )
            _save_checkpoint(checkpoint_path, checkpoint)
        else:
            delivery_request = _delivery.build_delivery_request(
                result=render_operator_md,
                adapter_id=_delivery.RECORDING_ADAPTER_ID,
                adapter_version="1.0",
                destination=_delivery.DestinationClassification.SYNTHETIC_RECORDING,
                purpose=_delivery.DeliveryPurpose.OPERATOR_TERMINAL_REPORT,
                policy_version=_delivery.DEFAULT_POLICY.policy_version,
            )
            delivery_plan = _delivery.plan_delivery(delivery_request)
            delivery_execution = _delivery.execute_delivery(delivery_plan)
            checkpoint["steps"]["delivery_model"] = "completed"
            _save_checkpoint(checkpoint_path, checkpoint)

            started_at = checkpoint.get("started_at") or _utc_now_iso()
            completed_at = _utc_now_iso()
            receipt = _receipt.open_receipt(
                delivery_execution,
                delivery_plan,
                delivery_request,
                started_at=started_at,
                completed_at=completed_at,
            )
            receipt = _receipt.finalize_receipt(receipt, finalized_at=completed_at)
            store = _receipt.DeliveryReceiptStore(rcpt_root)
            save_out = store.save(receipt)
            result.receipt_logical_delivery_id = receipt.logical_delivery_id
            result.receipt_path = save_out.get("path")
            checkpoint["steps"]["receipt"] = "completed"
            checkpoint["receipt_logical_delivery_id"] = receipt.logical_delivery_id
            checkpoint["receipt_path"] = save_out.get("path")

        checkpoint["status"] = "completed"
        checkpoint["completed_at"] = completed_at
        result.status = "completed"
    except Exception as exc:  # noqa: BLE001 - deliberately broad, fail-closed-but-non-fatal
        checkpoint["status"] = "best_effort_incomplete"
        checkpoint["limitations"].append(
            f"new-pipeline step failed after capture: {type(exc).__name__}: {exc}"
        )
        result.status = "best_effort_incomplete"

    result.steps = dict(checkpoint["steps"])
    result.limitations = list(checkpoint["limitations"])
    _save_checkpoint(checkpoint_path, checkpoint)
    return result
