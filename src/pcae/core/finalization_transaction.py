"""Phase 134E.10 / 134E.10.1 — Final Lifecycle Integration + Transaction-Span
Repair.

This module is the single, shared, resumable finalization transaction that
wires the seven previously-inert Phase 134E.1-134E.7 modules (Canonical
Engineering Evidence, Extraction, Phase/Operator Report Views, Rendering,
Delivery Pipeline, Delivery Receipt) into the governed phase/task
finalization path.

**134E.10.1 architectural repair.** 134E.10V independently found, via
direct line-number tracing, that 134E.10's original design called this
module strictly *after* certification, promotion, and physical dispatch
had already completed via the entirely unmodified legacy path -- making it
a post-success observer with no ability to prevent, reject, or accurately
classify a failure in any of the seven newly-integrated stages. 134D's own
completion criteria for 134E.10 require "one resumable transaction [that]
spans the full lifecycle." This module now satisfies that requirement by
*inverting control*: :func:`run_finalization_transaction` is called
*before* promotion and dispatch, runs the seven modules' mandatory
pre-promotion stages (evidence capture, extraction, view composition,
rendering) with veto power, and only if they all succeed does it *call*
the entry point's own certification-and-promotion logic (still exactly the
existing, unmodified ``finalize_phase_report``/``write_phase_report``/
``dispatch`` machinery -- 134D's own "wrap it behind the transaction; treat
it as an adapter" permission, not a rewrite of that machinery) through a
caller-supplied ``promote_and_dispatch`` callback. A failure in any
mandatory pre-promotion stage means the callback is **never invoked at
all** -- no promotion, no latest-pointer change, no external delivery, no
successful marker, exactly as 134D requires.

Authority boundaries (134D plan, section "Authority Boundary Review"),
updated for 134E.10.1:

- This module does not create, alter, strengthen, or re-derive any fact
  beyond what the caller-supplied, already-gate-passed trial ``PhaseReport``
  already established. It still does not reimplement
  ``validate_finalization_gate``/``_apply_canonical_and_trust`` -- those
  remain the caller's responsibility, run *before* this function is
  invoked, exactly as before 134E.10.1. What changed is *what runs after*
  a passing gate: promotion and dispatch are now behind, not before, this
  module's own mandatory stages.
- It does not introduce a second completion authority in the sense that
  matters: it still never independently writes ``latest.md``/``latest.json``,
  never independently dispatches, and never independently writes the
  ``.last-notified.json`` marker -- all three remain the exclusive
  responsibility of the ``promote_and_dispatch`` callback (i.e., the
  existing, unmodified ``finalize_phase_report``/``write_phase_report``/
  dispatch functions), invoked *by* this module rather than *before* it.
- It does not perform a second physical delivery. The real send still
  happens exactly once, inside the caller-supplied ``promote_and_dispatch``
  callback, using the existing, already-authorized dispatch path. This
  module's own "delivery" step (post-dispatch) only *models*, via the
  in-memory, no-network ``RECORDING_ADAPTER_ID`` adapter from
  ``pcae.core.delivery_pipeline``, what the callback's real dispatch
  actually did, and records that model as a receipt via
  ``pcae.core.delivery_receipt``. It never calls
  ``pcae.core.notifications`` or any live sink itself.
  **134E.10V finding, repaired (unchanged by 134E.10.1):** the recording
  adapter unconditionally reports success by construction, so delivery
  modeling and receipt creation are only attempted when the *actually
  promoted* report's ``notification_result`` (read from
  ``promote_and_dispatch()``'s own return value, not the pre-promotion
  trial report) reports ``success: True`` -- otherwise a receipt would
  misrepresent a delivery that was never attempted or did not succeed.

No command file constructs ``CanonicalEngineeringEvidence``, calls
``extract``/``compose_*``/``render``/``build_delivery_request``/
``open_receipt`` directly; they all funnel through
:func:`run_finalization_transaction`, and (134E.10.1) they now also funnel
their own promotion/dispatch calls through it via the
``promote_and_dispatch`` callback, rather than calling
``finalize_phase_report``/``write_phase_report``/``dispatch`` directly
themselves.

Resumability model (mirrors the PER/RER promotion-idempotency pattern in
``pcae.core.agent`` around ``build_promotion_execution``): a transaction
record is persisted to ``.pcae/finalization-transactions/<phase_id>.json``
with ``status="in_progress"`` before the first pre-promotion step and
rewritten after every step. A second invocation for the same ``phase_id``
whose certified content (``report_digest`` + ``finalization_snapshot_id``,
computed from the pre-promotion trial report -- the same identity pair the
existing notification marker already uses) matches a prior
``status="completed"`` record short-circuits immediately: the
``promote_and_dispatch`` callback is **not called again**, so a retry can
never re-promote or re-dispatch for content already known to be finalized
-- this is a stronger, structural exactly-once guarantee than 134E.10's
original design offered (which relied solely on the pre-existing
``.last-notified.json`` marker for dedup, checked independently by each
entry point).

Fail-closed-but-non-fatal-*after-promotion* design: pre-promotion stage
failures are fail-closed and fatal to the *transaction* (the callback is
never invoked, so nothing irreversible has happened yet -- returning
failure to the caller is safe and correct). Once ``promote_and_dispatch``
has been called, its outcome is authoritative and irreversible; this
module's remaining post-dispatch steps (receipt modeling) are then
best-effort and non-fatal, matching 134E.10's original design for that
specific, inherently-after-the-fact portion of the sequence -- a receipt
bug must never be able to un-promote or un-send something that already,
legitimately happened.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

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
      - ``"completed"``: all mandatory pre-promotion stages succeeded, the
        ``promote_and_dispatch`` callback was invoked and returned, and
        post-dispatch receipt modeling ran (a skipped-but-honest receipt,
        per the 134E.10V repair, still counts as ``"completed"`` -- see
        ``limitations``).
      - ``"resumed_completed"``: a prior transaction for the same
        certified content had already completed; the callback was
        **not** invoked this call (no re-promotion, no re-dispatch).
      - ``"gate_not_passed"``: the caller-supplied gate/report was not
        finalizable; the callback was never invoked (this is the
        expected, ordinary outcome any time the existing gate itself
        blocked -- not a failure of this module).
      - ``"pre_promotion_certification_failed"``: a mandatory
        pre-promotion stage (evidence capture, extraction, view
        composition, or rendering) raised. **The ``promote_and_dispatch``
        callback was never invoked** -- no promotion, no latest-pointer
        change, no external delivery, no successful marker. This is the
        134E.10.1 repair's central new behavior: 134E.10's original
        design had no status equivalent to this because the callback
        (then just the legacy path, called directly by the entry point)
        had already run unconditionally before this module was ever
        reached.
      - ``"promotion_and_dispatch_failed"``: pre-promotion stages
        succeeded, the callback was invoked, but it raised or returned a
        result indicating failure (``blocked``/``report_error``). No
        further transaction steps ran.
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
    promotion_and_dispatch: dict[str, Any] | None = None

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


def _build_pre_promotion_artifacts(report: PhaseReport, phase_id: str, phase_name: str):
    """Run the mandatory pre-promotion stages (134E.10.1). Raises on any
    failure -- the caller (:func:`run_finalization_transaction`) treats any
    exception here as fatal to the transaction, and never invokes
    ``promote_and_dispatch`` when this raises. Returns the tuple of
    artifacts the post-promotion steps need.
    """
    evidence = _capture_evidence(report, phase_id, phase_name)
    extraction_phase = _extraction.extract(evidence, _extraction.PROFILE_ID_PHASE_REPORT)
    extraction_operator = _extraction.extract(evidence, _extraction.PROFILE_ID_OPERATOR_REPORT)
    view_phase = _prview.compose_phase_report_view(extraction_phase)
    view_operator = _orview.compose_operator_report_view(extraction_operator)
    render_phase_md = _rendering.render(
        view_phase, extraction_phase, _rendering.RENDERER_ID_PHASE_REPORT_MARKDOWN
    )
    render_operator_md = _rendering.render(
        view_operator, extraction_operator, _rendering.RENDERER_ID_OPERATOR_REPORT_MARKDOWN
    )
    return (
        evidence, extraction_phase, extraction_operator,
        view_phase, view_operator, render_phase_md, render_operator_md,
    )


def run_finalization_transaction(
    *,
    phase_id: str,
    phase_name: str,
    report: PhaseReport,
    gate: dict[str, Any],
    promote_and_dispatch: Callable[[], dict[str, Any]],
    transaction_root: Path | str | None = None,
    receipt_root: Path | str | None = None,
) -> TransactionResult:
    """Run (or resume) the authoritative finalization transaction (134E.10.1).

    Unlike 134E.10's original design, this function is called *before*
    promotion and dispatch, not after. ``report`` is the caller's
    already-gate-passed *trial* report (identical in content to what the
    caller would otherwise pass directly to ``finalize_phase_report``/
    ``write_phase_report``, but not yet promoted). ``promote_and_dispatch``
    is a zero-argument callback the caller supplies that performs the
    actual, unmodified legacy promotion-and-dispatch work (calling
    ``finalize_phase_report``, ``write_phase_report``, ``dispatch``, etc.)
    and returns a dict containing at least a ``"report"`` key -- the real,
    now-promoted ``PhaseReport`` object, with ``notification_result``
    populated if a dispatch was attempted.

    This function calls the seven newly-integrated modules' mandatory
    pre-promotion stages (evidence capture, extraction, view composition,
    rendering) *before* calling ``promote_and_dispatch``. **If any of them
    raises, ``promote_and_dispatch`` is never invoked** -- no promotion, no
    dispatch, no marker, no external delivery. This is the 134E.10.1
    repair's central behavior change from 134E.10's original design.

    Preconditions the caller is responsible for (this function re-checks
    them defensively but does not re-derive them): ``report`` has already
    passed ``validate_finalization_gate`` (``gate["finalizable"]`` is
    True).
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
        # Resumed: the callback is NOT invoked -- this content was already
        # promoted/dispatched by a prior call. Retrying a completed
        # transaction must never re-promote or re-dispatch.
        existing["_checkpoint_path"] = str(checkpoint_path)
        return _result_from_checkpoint(existing)

    if not gate.get("finalizable") or report.report_completeness != "complete":
        # Nothing to persist and, critically, promote_and_dispatch is NOT
        # called: a gate-failing report must never be promoted or
        # dispatched, exactly as before 134E.10.1.
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

    # ── Mandatory pre-promotion stages (134E.10.1: gating, fatal to the
    # transaction; promote_and_dispatch is never called if this raises) ──
    try:
        (
            evidence, extraction_phase, extraction_operator,
            view_phase, view_operator, render_phase_md, render_operator_md,
        ) = _build_pre_promotion_artifacts(report, phase_id, phase_name)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, fail-closed
        checkpoint["steps"]["pre_promotion_certification"] = "failed"
        checkpoint["limitations"].append(
            f"pre_promotion_certification failed: {type(exc).__name__}: {exc} "
            "-- promote_and_dispatch was NOT invoked"
        )
        checkpoint["status"] = "pre_promotion_certification_failed"
        _save_checkpoint(checkpoint_path, checkpoint)
        result.status = "pre_promotion_certification_failed"
        result.limitations = list(checkpoint["limitations"])
        return result

    result.evidence_id = evidence.identity.evidence_id
    result.extraction_digests = {
        "phase_report": extraction_phase.compute_digest(),
        "operator_report": extraction_operator.compute_digest(),
    }
    result.view_digests = {
        "phase_report": view_phase.compute_digest(),
        "operator_report": view_operator.compute_digest(),
    }
    result.rendering_digests = {
        "phase_report": render_phase_md.compute_digest(),
        "operator_report": render_operator_md.compute_digest(),
    }
    # Honest divergence check (never forced to match): the two rendering
    # pipelines are independent presentation stages; if they happen to
    # disagree, that is recorded as a known limitation, not papered over,
    # and (unchanged from 134E.10) never blocks promotion by itself.
    existing_markdown = report.render_markdown()
    matches = existing_markdown.strip() == render_phase_md.rendered_content.strip()
    result.rendering_content_matches_existing = {"phase_report_markdown": matches}
    if not matches:
        checkpoint["limitations"].append(
            "known limitation: phase_report_markdown_v1 rendering output "
            "diverges from PhaseReport.render_markdown() output for this "
            "report; both derive from the same certified report/evidence "
            "but are independent presentation stages and are not forced "
            "to be byte-identical"
        )

    checkpoint["steps"]["pre_promotion_certification"] = "completed"
    checkpoint["evidence_id"] = evidence.identity.evidence_id
    checkpoint["extraction_digests"] = dict(result.extraction_digests)
    checkpoint["view_digests"] = dict(result.view_digests)
    checkpoint["rendering_digests"] = dict(result.rendering_digests)
    checkpoint["rendering_content_matches_existing"] = dict(
        result.rendering_content_matches_existing
    )
    _save_checkpoint(checkpoint_path, checkpoint)

    # ── Promotion and dispatch: the caller-supplied adapter, invoked ONLY
    # because pre-promotion certification succeeded. This is the real,
    # unmodified legacy machinery (finalize_phase_report/write_phase_
    # report/dispatch) -- 134D's "wrap it behind the transaction; treat it
    # as an adapter" permission, not a reimplementation. ─────────────────
    try:
        promotion_result = promote_and_dispatch()
    except Exception as exc:  # noqa: BLE001 - the callback itself failing is authoritative
        checkpoint["steps"]["promotion_and_dispatch"] = "failed"
        checkpoint["limitations"].append(
            f"promote_and_dispatch raised: {type(exc).__name__}: {exc}"
        )
        checkpoint["status"] = "promotion_and_dispatch_failed"
        _save_checkpoint(checkpoint_path, checkpoint)
        result.status = "promotion_and_dispatch_failed"
        result.limitations = list(checkpoint["limitations"])
        return result

    if promotion_result.get("blocked") or promotion_result.get("report_error"):
        checkpoint["steps"]["promotion_and_dispatch"] = "failed"
        checkpoint["limitations"].append(
            "promote_and_dispatch reported failure: "
            f"blocked={promotion_result.get('blocked')!r} "
            f"report_error={promotion_result.get('report_error')!r}"
        )
        checkpoint["status"] = "promotion_and_dispatch_failed"
        _save_checkpoint(checkpoint_path, checkpoint)
        result.status = "promotion_and_dispatch_failed"
        result.limitations = list(checkpoint["limitations"])
        return result

    checkpoint["steps"]["promotion_and_dispatch"] = "completed"
    _save_checkpoint(checkpoint_path, checkpoint)
    result.promotion_and_dispatch = promotion_result
    promoted_report = promotion_result.get("report") or report

    # ── Post-dispatch: receipt modeling (best-effort, non-fatal -- the
    # promotion/dispatch above already, irreversibly, happened). ─────────
    try:
        # 134E.10V finding (repaired, preserved unchanged by 134E.10.1):
        # the RECORDING_ADAPTER_ID adapter unconditionally reports success
        # by construction, so delivery modeling and receipt creation are
        # only attempted when the REAL, now-promoted report's
        # notification_result itself reports success: True.
        notification_result = getattr(promoted_report, "notification_result", None) or {}
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
        # Promotion/dispatch already, irreversibly, succeeded above -- a
        # receipt-modeling bug must never be represented as un-doing that.
        checkpoint["status"] = "completed_receipt_best_effort_incomplete"
        checkpoint["limitations"].append(
            f"post-dispatch receipt modeling failed: {type(exc).__name__}: {exc}"
        )
        result.status = "completed_receipt_best_effort_incomplete"

    result.steps = dict(checkpoint["steps"])
    result.limitations = list(checkpoint["limitations"])
    _save_checkpoint(checkpoint_path, checkpoint)
    return result
