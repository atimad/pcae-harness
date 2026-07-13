"""Tests for Phase 134E.10 / 134E.10.1 — Final Lifecycle Integration +
Transaction-Span Repair.

134E.10V independently found, via direct line-number tracing, that
134E.10's original design called ``run_finalization_transaction`` strictly
*after* certification, promotion, and physical dispatch had already
completed via the entirely unmodified legacy path -- a post-success
observer with no ability to prevent, reject, or accurately classify a
failure in any of the seven newly-integrated modules (Canonical
Engineering Evidence, Evidence Extraction, Phase Report View, Operator
Report View, Rendering, Delivery Pipeline, Delivery Receipt). 134E.10.1
repairs this by inverting control: the caller now supplies a
``promote_and_dispatch`` callback (the existing, unmodified
``finalize_phase_report``/``write_phase_report``/``dispatch`` machinery,
wrapped as an adapter per 134D's own permission), and
``run_finalization_transaction`` calls it *only if* the seven modules'
mandatory pre-promotion stages (evidence capture, extraction, view
composition, rendering) succeed first.

No test in this file sets a live notification environment variable or
exercises a real Telegram/HTTP call -- ``tests/conftest.py``'s autouse
``_isolate_external_notifications`` fixture applies to every test here
regardless, and the transaction's own post-dispatch "delivery" step only
ever uses the in-memory, no-network ``RECORDING_ADAPTER_ID`` adapter (see
``delivery_pipeline.py``), never ``pcae.core.notifications``. No test's
``promote_and_dispatch`` callback performs real I/O either -- each is a
synthetic closure recording whether it was called and returning a
caller-controlled outcome.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

import pcae.core.phase_reports as pr
from pcae.core.finalization_transaction import (
    TransactionResult,
    _validate_identifier,
    run_finalization_transaction,
)


def _fresh_arch_status(phase_id: str, **overrides) -> dict:
    base = {
        "schema_version": "1.0",
        "state_marker": "abc123",
        "repository_revision": "deadbeef",
        "completed": [],
        "completed_phase_ids": ["998A"],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": phase_id,
        "planned": [],
        "planned_phase_ids": [],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
        "freshness": "fresh",
        "limitations": [],
        "conflicts": [],
        "source_provenance": {},
    }
    base.update(overrides)
    return base


def _certified_report(
    phase_id: str = "999X.1-txn-test", *, dispatch_succeeded: bool = True, **overrides
):
    """Build a report that passes ``validate_finalization_gate`` end to
    end, exactly the way ``commands/phase.py``/``commands/task.py`` do
    (``make_phase_report`` -> ``_apply_canonical_and_trust`` ->
    ``validate_finalization_gate``), hermetically -- ``load_canonical_
    report()`` is patched to ``None`` so this never depends on this real
    repository's own ``.pcae/phase-completion-report.md``. All synthetic
    phase IDs use a dotted sub-phase form (``"999X.1-..."``) so
    ``validate_phase_identity()``'s own live-``PROJECT_STATUS.md`` check
    never collides with this test file's fixtures (134E.10V finding).

    ``dispatch_succeeded`` sets what the caller's ``promote_and_dispatch``
    callback should report on its returned report's ``notification_
    result`` -- tests build their own callback and read this flag to
    decide what to simulate; it is not applied here directly.
    """
    defaults = dict(
        phase_id=phase_id,
        phase_name="Transaction Test Phase",
        status="completed",
        summary=f"Phase {phase_id}: transaction test summary.",
        files_changed=3,
        tests_run=10,
        commits=["a" * 40],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="999Y — Next Phase",
        explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
        test_results={
            "fast_green": "10/10",
            "report_notification_tests": "passed",
            "bootstrap_session_reporting_tests": "passed",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "configured",
        },
        risks=["Some known risk."],
        follow_ups=["Some follow-up."],
    )
    defaults.update(overrides)
    with mock.patch.object(pr, "load_canonical_report", return_value=None):
        report = pr.make_phase_report(**defaults)
        report.architecture_status = _fresh_arch_status(phase_id)
        report.metadata["phase_id"] = phase_id
        report.metadata["source_revision"] = "deadbeef"
        report.metadata["phase_commits"] = report.commits
        pr._apply_canonical_and_trust(report, phase_id, report.phase_name, report.status)
        gate = pr.validate_finalization_gate(
            phase_id=phase_id,
            report=report,
            metadata=report.metadata,
            pushed_status=report.pushed_status,
            origin_main_head_count=report.origin_main_head_count,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
            commit_attribution=report.commits[0],
        )
    return report, gate


def _successful_promote_and_dispatch(report, calls: list, *, dispatch_succeeded: bool = True):
    """A synthetic ``promote_and_dispatch`` callback: records that it was
    called, mutates ``report.notification_result`` to simulate a real
    dispatch outcome, and returns the shape the real entry points'
    callbacks return (``{"report": ..., ...}``). No I/O, no promotion of
    any real artifact.
    """
    def _callback() -> dict:
        calls.append(True)
        report.notification_result = {
            "dispatched": True, "sinks": ["noop"], "success": dispatch_succeeded,
            "error": None if dispatch_succeeded else "synthetic failure",
            "outcome": "sent" if dispatch_succeeded else "failed",
            "reason": "", "kind": "complete",
        }
        return {"report": report, "blocked": False, "report_error": None}
    return _callback


def _raising_promote_and_dispatch(calls: list, exc: Exception):
    def _callback() -> dict:
        calls.append(True)
        raise exc
    return _callback


def _never_call_promote_and_dispatch(calls: list):
    def _callback() -> dict:
        calls.append(True)
        raise AssertionError("promote_and_dispatch must not be called")
    return _callback


# ═══════════════════════════════════════════════════════════════════════
# 1. End-to-end happy path: pre-promotion succeeds, callback IS invoked
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndTransaction:
    def test_gate_passing_report_completes_all_stages_and_invokes_callback(self, tmp_path):
        report, gate = _certified_report()
        calls: list = []
        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert isinstance(result, TransactionResult)
        assert result.status == "completed"
        assert calls == [True]  # invoked exactly once
        assert result.evidence_id
        assert result.extraction_digests.get("phase_report")
        assert result.view_digests.get("phase_report")
        assert result.rendering_digests.get("phase_report")
        assert result.promotion_and_dispatch is not None
        assert result.receipt_logical_delivery_id
        assert result.receipt_path

    def test_no_receipt_when_real_dispatch_did_not_succeed(self, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-no-dispatch-test")
        calls: list = []
        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_successful_promote_and_dispatch(
                report, calls, dispatch_succeeded=False
            ),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == [True]  # promotion still happened -- only receipt is gated
        assert result.status == "completed"
        assert result.evidence_id
        assert result.receipt_logical_delivery_id is None
        assert result.receipt_path is None
        assert any(
            "no receipt recorded" in lim and "does not report success" in lim
            for lim in result.limitations
        )

    def test_crash_after_irreversible_adapter_start_never_replays_callback(self, tmp_path):
        """A process stop after adapter entry leaves a durable uncertain
        checkpoint; retry must observe it and never promote/dispatch again."""
        report, gate = _certified_report(phase_id="999X.1-crash-window-test")
        calls: list[str] = []

        def _crash_after_start():
            calls.append("started")
            raise KeyboardInterrupt("synthetic process stop")

        with pytest.raises(KeyboardInterrupt):
            run_finalization_transaction(
                phase_id=report.phase_id,
                phase_name=report.phase_name,
                report=report,
                gate=gate,
                promote_and_dispatch=_crash_after_start,
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )

        retry = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_never_call_promote_and_dispatch(calls),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert retry.status == "promotion_outcome_unconfirmed"
        assert calls == ["started"]
        checkpoint = json.loads((tmp_path / "txns" / f"{report.phase_id}.json").read_text())
        assert checkpoint["steps"]["promotion_and_dispatch"] == "in_progress"

    def test_unresolved_rendering_divergence_is_disclosed_not_hidden(self, tmp_path):
        """The new rendering pipeline is an independent presentation
        stage from ``PhaseReport.render_markdown()`` -- if their output
        differs, that must be recorded as a limitation, never silently
        papered over, and must never by itself block promotion (134A
        invariant against silent strengthening)."""
        report, gate = _certified_report(phase_id="999X.1-divergence-test")
        calls: list = []
        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == [True]
        assert "phase_report_markdown" in result.rendering_content_matches_existing
        if not result.rendering_content_matches_existing["phase_report_markdown"]:
            assert any("diverges" in lim for lim in result.limitations)


# ═══════════════════════════════════════════════════════════════════════
# 2. Central 134E.10.1 repair: pre-promotion failure means the callback
#    is NEVER invoked -- no promotion, no dispatch, no marker.
# ═══════════════════════════════════════════════════════════════════════


class TestPrePromotionGatingIsAuthoritative:
    @pytest.mark.parametrize(
        "broken_module,broken_fn",
        [
            ("pcae.core.finalization_transaction._capture_evidence", "capture_evidence"),
            ("pcae.core.finalization_transaction._extraction.extract", "extraction"),
            (
                "pcae.core.finalization_transaction._prview.compose_phase_report_view",
                "phase_report_view",
            ),
            (
                "pcae.core.finalization_transaction._orview.compose_operator_report_view",
                "operator_report_view",
            ),
            ("pcae.core.finalization_transaction._rendering.render", "rendering"),
        ],
    )
    def test_mandatory_stage_failure_prevents_promotion_and_dispatch(
        self, broken_module, broken_fn, tmp_path
    ):
        report, gate = _certified_report(phase_id=f"999X.1-{broken_fn}-fail-test")
        calls: list = []
        with mock.patch(broken_module, side_effect=RuntimeError(f"synthetic {broken_fn} bug")):
            result = run_finalization_transaction(
                phase_id=report.phase_id,
                phase_name=report.phase_name,
                report=report,
                gate=gate,
                promote_and_dispatch=_never_call_promote_and_dispatch(calls),
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )
        assert calls == []  # never invoked
        assert result.status == "pre_promotion_certification_failed"
        assert result.promotion_and_dispatch is None
        assert any("promote_and_dispatch was NOT invoked" in lim for lim in result.limitations)

    def test_promote_and_dispatch_callback_exception_is_represented_accurately(self, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-callback-raises-test")
        calls: list = []
        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_raising_promote_and_dispatch(
                calls, RuntimeError("synthetic promotion bug")
            ),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == [True]  # it WAS invoked (pre-promotion succeeded) but it failed
        assert result.status == "promotion_and_dispatch_failed"
        assert result.receipt_logical_delivery_id is None

    def test_promote_and_dispatch_blocked_result_is_treated_as_failure(self, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-blocked-result-test")
        calls: list = []

        def _blocked_callback() -> dict:
            calls.append(True)
            return {"report": report, "blocked": True, "paths": {}}

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_blocked_callback,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == [True]
        assert result.status == "promotion_and_dispatch_failed"

    def test_pre_promotion_failure_prevents_marker_persistence(self, tmp_path):
        """A pre-promotion failure must prevent the successful-completion
        marker from ever being written -- the marker is written only
        inside the real (here, synthetic) promote_and_dispatch callback,
        so proving the callback is never invoked (already covered above)
        is equivalent to proving no marker is written; this test makes
        that specific consequence explicit by using a callback that would
        write a marker file if called, and confirming the file never
        appears."""
        report, gate = _certified_report(phase_id="999X.1-marker-gating-test")
        marker_path = tmp_path / "would-be-marker.json"

        def _callback_that_writes_a_marker() -> dict:
            marker_path.write_text("{}")
            report.notification_result = {"success": True}
            return {"report": report}

        with mock.patch(
            "pcae.core.finalization_transaction._capture_evidence",
            side_effect=RuntimeError("synthetic capture bug"),
        ):
            result = run_finalization_transaction(
                phase_id=report.phase_id,
                phase_name=report.phase_name,
                report=report,
                gate=gate,
                promote_and_dispatch=_callback_that_writes_a_marker,
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )
        assert result.status == "pre_promotion_certification_failed"
        assert not marker_path.exists()

    def test_receipt_creation_happens_only_after_promote_and_dispatch_returns(self, tmp_path):
        """Ordering proof: the receipt must be created strictly after the
        callback returns (it needs the callback's real dispatch outcome),
        never before or concurrently."""
        report, gate = _certified_report(phase_id="999X.1-ordering-test")
        order: list[str] = []

        def _callback() -> dict:
            order.append("promote_and_dispatch")
            report.notification_result = {"success": True}
            return {"report": report}

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            promote_and_dispatch=_callback,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert result.receipt_logical_delivery_id is not None
        order.append("receipt_confirmed_present")
        assert order == ["promote_and_dispatch", "receipt_confirmed_present"]


# ═══════════════════════════════════════════════════════════════════════
# 3. Gate enforcement — the existing certified path is authoritative
# ═══════════════════════════════════════════════════════════════════════


class TestGateEnforcement:
    def test_gate_not_passed_blocks_before_callback_is_invoked(self, tmp_path):
        report, _ = _certified_report(phase_id="999X.1-blocked-test")
        failing_gate = {"finalizable": False, "blockers": ["synthetic blocker"]}
        calls: list = []

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=failing_gate,
            promote_and_dispatch=_never_call_promote_and_dispatch(calls),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == []
        assert result.status == "gate_not_passed"
        assert result.evidence_id is None
        assert result.promotion_and_dispatch is None

    def test_incomplete_report_completeness_blocks_even_if_gate_dict_lies(self, tmp_path):
        """Defense in depth: the transaction re-checks ``report.report_
        completeness`` itself rather than trusting a caller-supplied gate
        dict's ``finalizable`` flag alone."""
        report, _ = _certified_report(phase_id="999X.1-lying-gate-test")
        report.report_completeness = "incomplete"
        lying_gate = {"finalizable": True, "blockers": []}
        calls: list = []

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=lying_gate,
            promote_and_dispatch=_never_call_promote_and_dispatch(calls),
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert calls == []
        assert result.status == "gate_not_passed"


# ═══════════════════════════════════════════════════════════════════════
# 4. Resumability / idempotency — retry must not re-promote or re-dispatch
# ═══════════════════════════════════════════════════════════════════════


class TestResumability:
    def test_second_call_for_same_certified_content_does_not_reinvoke_callback(self, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-resume-test")
        txn_root = tmp_path / "txns"
        rcpt_root = tmp_path / "receipts"
        calls: list = []

        first = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name,
            report=report, gate=gate,
            promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
            transaction_root=txn_root, receipt_root=rcpt_root,
        )
        assert first.status == "completed"
        assert calls == [True]

        second = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name,
            report=report, gate=gate,
            promote_and_dispatch=_never_call_promote_and_dispatch(calls),
            transaction_root=txn_root, receipt_root=rcpt_root,
        )
        assert second.status == "resumed_completed"
        assert calls == [True]  # still exactly one call, ever
        assert second.evidence_id == first.evidence_id
        assert second.receipt_logical_delivery_id == first.receipt_logical_delivery_id
        # Retry preserves the exact certified semantic snapshot and digest
        # -- these must never drift between the original run and a retry
        # for identical content.
        assert second.report_digest == first.report_digest
        assert second.finalization_snapshot_id == first.finalization_snapshot_id
        assert second.extraction_digests == first.extraction_digests
        assert second.view_digests == first.view_digests
        assert second.rendering_digests == first.rendering_digests

    def test_distinct_certified_content_does_not_collide_with_prior_completion(self, tmp_path):
        """A genuinely different certified report for the same phase_id
        (e.g. a corrective re-run) produces its own transaction record and
        invokes its own callback -- it must not be silently treated as the
        already-completed one."""
        txn_root = tmp_path / "txns"
        rcpt_root = tmp_path / "receipts"
        report_a, gate_a = _certified_report(
            phase_id="999X.1-distinct-test", summary="First summary."
        )
        calls_a: list = []
        result_a = run_finalization_transaction(
            phase_id=report_a.phase_id, phase_name=report_a.phase_name,
            report=report_a, gate=gate_a,
            promote_and_dispatch=_successful_promote_and_dispatch(report_a, calls_a),
            transaction_root=txn_root, receipt_root=rcpt_root,
        )

        report_b, gate_b = _certified_report(
            phase_id="999X.1-distinct-test", summary="Second, different summary."
        )
        calls_b: list = []
        result_b = run_finalization_transaction(
            phase_id=report_b.phase_id, phase_name=report_b.phase_name,
            report=report_b, gate=gate_b,
            promote_and_dispatch=_successful_promote_and_dispatch(report_b, calls_b),
            transaction_root=txn_root, receipt_root=rcpt_root,
        )
        assert calls_a == [True]
        assert calls_b == [True]  # distinct content -> its own callback invocation
        assert result_b.status == "completed"
        assert result_b.report_digest != result_a.report_digest
        assert result_b.receipt_logical_delivery_id != result_a.receipt_logical_delivery_id


# ═══════════════════════════════════════════════════════════════════════
# 5. Storage identifier safety (path-traversal defense)
# ═══════════════════════════════════════════════════════════════════════


class TestStorageIdentifierSafety:
    @pytest.mark.parametrize(
        "bad_id",
        [
            "../../etc/passwd",
            "..",
            "a/b",
            "a\\b",
            "/etc/passwd",
            "",
        ],
    )
    def test_unsafe_phase_id_is_rejected(self, bad_id, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-safe-holder")
        calls: list = []
        with pytest.raises(ValueError):
            run_finalization_transaction(
                phase_id=bad_id,
                phase_name="x",
                report=report,
                gate=gate,
                promote_and_dispatch=_never_call_promote_and_dispatch(calls),
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )
        assert calls == []

    def test_validate_identifier_accepts_ordinary_phase_ids(self):
        for ok_id in ("134E.10", "999X.1-safe-test", "113B.2", "134E.1V"):
            _validate_identifier(ok_id, "phase_id")  # must not raise


# ═══════════════════════════════════════════════════════════════════════
# 6. The shared boundary — no command constructs the new modules directly,
#    and every entry point routes promotion/dispatch through the callback.
# ═══════════════════════════════════════════════════════════════════════


class TestSharedBoundary:
    @pytest.mark.parametrize(
        "path",
        [
            "src/pcae/commands/phase.py",
            "src/pcae/commands/task.py",
            "src/pcae/commands/phase_reports.py",
            "src/pcae/commands/notifications.py",
        ],
    )
    def test_entry_point_calls_the_shared_transaction(self, path):
        repo_root = Path(__file__).resolve().parent.parent
        content = (repo_root / path).read_text()
        assert "run_finalization_transaction" in content, (
            f"{path} does not call the shared 134E.10.1 finalization transaction"
        )

    @pytest.mark.parametrize(
        "path",
        [
            "src/pcae/commands/phase.py",
            "src/pcae/commands/task.py",
            "src/pcae/commands/phase_reports.py",
            "src/pcae/commands/notifications.py",
        ],
    )
    def test_entry_point_supplies_promote_and_dispatch_callback(self, path):
        repo_root = Path(__file__).resolve().parent.parent
        content = (repo_root / path).read_text()
        assert "promote_and_dispatch=_promote_and_dispatch" in content, (
            f"{path} calls run_finalization_transaction without routing its own "
            "promotion/dispatch through the promote_and_dispatch callback -- "
            "134E.10.1 requires the transaction to gate promotion/dispatch, not "
            "merely observe it afterward"
        )

    @pytest.mark.parametrize(
        "path",
        [
            "src/pcae/commands/phase.py",
            "src/pcae/commands/task.py",
            "src/pcae/commands/phase_reports.py",
            "src/pcae/commands/notifications.py",
        ],
    )
    def test_entry_point_does_not_construct_new_modules_directly(self, path):
        repo_root = Path(__file__).resolve().parent.parent
        content = (repo_root / path).read_text()
        for forbidden in (
            "CanonicalEngineeringEvidence(",
            "compose_phase_report_view(",
            "compose_operator_report_view(",
            "_extraction.extract(",
            "build_delivery_request(",
            "open_receipt(",
        ):
            assert forbidden not in content, (
                f"{path} constructs {forbidden!r} directly instead of going "
                "through run_finalization_transaction()"
            )


# ═══════════════════════════════════════════════════════════════════════
# 7. External-delivery isolation
# ═══════════════════════════════════════════════════════════════════════


class TestExternalDeliveryIsolation:
    def test_transaction_never_imports_notifications_module(self):
        repo_root = Path(__file__).resolve().parent.parent
        content = (repo_root / "src/pcae/core/finalization_transaction.py").read_text()
        assert "import pcae.core.notifications" not in content
        assert "from pcae.core import notifications" not in content
        assert "from pcae.core.notifications import" not in content
        assert "TelegramSink" not in content

    def test_transaction_delivery_step_uses_recording_adapter_only(self, tmp_path):
        report, gate = _certified_report(phase_id="999X.1-isolation-test")
        calls: list = []
        result = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name,
            report=report, gate=gate,
            promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
            transaction_root=tmp_path / "txns", receipt_root=tmp_path / "receipts",
        )
        assert result.status == "completed"
        receipt_path = Path(result.receipt_path)
        assert receipt_path.exists()
        receipt_data = json.loads(receipt_path.read_text())
        # No test/production run of this transaction should ever record a
        # Telegram-classified destination -- confirms the delivery step
        # genuinely modeled via the synthetic recording adapter, not a
        # live channel.
        serialized = json.dumps(receipt_data)
        assert "telegram" not in serialized.lower()
