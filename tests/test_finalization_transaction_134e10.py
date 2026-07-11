"""Tests for Phase 134E.10 — Final Lifecycle Integration.

The 134D implementation plan's authoritative scope for 134E.10 (see
docs/PHASE_134_CANONICAL_PHASE_FINALIZATION_IMPLEMENTATION_PLAN.md,
"134E.10 — Final Lifecycle Integration"): integrate Stages 9 and 12
(repository/governance certification; exactly-once logical governed
completion) with 134E.1-134E.9's previously-inert machinery, without
introducing a second completion authority and without regressing the
existing, already-governed finalization path.

``src/pcae/core/finalization_transaction.py`` is the one place any of the
seven 134E.1-134E.7 modules (Canonical Engineering Evidence, Evidence
Extraction, Phase Report View, Operator Report View, Rendering, Delivery
Pipeline, Delivery Receipt) are invoked. It is called from four production
entry points (``commands/phase.py``, ``commands/task.py``,
``commands/phase_reports.py``, ``commands/notifications.py`` -- a fifth,
push-time reconciliation, funnels into ``phase.py``) strictly *after* each
entry point's existing, unmodified certified-report path has already
promoted the report and (if applicable) already dispatched. The module
never re-decides completeness, never re-promotes, and never performs a
second physical send -- see its own module docstring for the full
authority-boundary rationale.

No test in this file sets a live notification environment variable or
exercises a real Telegram/HTTP call -- ``tests/conftest.py``'s autouse
``_isolate_external_notifications`` fixture applies to every test here
regardless, and the transaction's own "delivery" step only ever uses the
in-memory, no-network ``RECORDING_ADAPTER_ID`` adapter (see
``delivery_pipeline.py``), never ``pcae.core.notifications``.
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


def _certified_report(phase_id: str = "999X-txn-test", **overrides):
    """Build a report that passes ``validate_finalization_gate`` end to
    end, exactly the way ``commands/phase.py``/``commands/task.py`` do
    (``make_phase_report`` -> ``_apply_canonical_and_trust`` ->
    ``validate_finalization_gate``), hermetically -- ``load_canonical_
    report()`` is patched to ``None`` so this never depends on this real
    repository's own ``.pcae/phase-completion-report.md``.
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


# ═══════════════════════════════════════════════════════════════════════
# 1. End-to-end happy path
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndTransaction:
    def test_gate_passing_report_completes_all_new_pipeline_steps(self, tmp_path):
        report, gate = _certified_report()
        assert gate["finalizable"] is True

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert isinstance(result, TransactionResult)
        assert result.status == "completed"
        assert result.evidence_id
        assert result.extraction_digests.get("phase_report")
        assert result.extraction_digests.get("operator_report")
        assert result.view_digests.get("phase_report")
        assert result.view_digests.get("operator_report")
        assert result.rendering_digests.get("phase_report")
        assert result.receipt_logical_delivery_id
        assert result.receipt_path

    def test_unresolved_rendering_divergence_is_disclosed_not_hidden(self, tmp_path):
        """The new rendering pipeline is an independent presentation
        stage from ``PhaseReport.render_markdown()`` -- if their output
        differs, that must be recorded as a limitation, never silently
        papered over (134A invariant against silent strengthening)."""
        report, gate = _certified_report(phase_id="999X-divergence-test")
        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=gate,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert "phase_report_markdown" in result.rendering_content_matches_existing
        if not result.rendering_content_matches_existing["phase_report_markdown"]:
            assert any("diverges" in lim for lim in result.limitations)


# ═══════════════════════════════════════════════════════════════════════
# 2. Gate enforcement — the existing certified path is authoritative
# ═══════════════════════════════════════════════════════════════════════


class TestGateEnforcement:
    def test_gate_not_passed_blocks_before_any_new_pipeline_step(self, tmp_path):
        report, _ = _certified_report(phase_id="999X-blocked-test")
        failing_gate = {"finalizable": False, "blockers": ["synthetic blocker"]}

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=failing_gate,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert result.status == "gate_not_passed"
        assert result.evidence_id is None
        assert result.receipt_logical_delivery_id is None

    def test_incomplete_report_completeness_blocks_even_if_gate_dict_lies(self, tmp_path):
        """Defense in depth: the transaction re-checks ``report.report_
        completeness`` itself rather than trusting a caller-supplied gate
        dict's ``finalizable`` flag alone."""
        report, _ = _certified_report(phase_id="999X-lying-gate-test")
        report.report_completeness = "incomplete"
        lying_gate = {"finalizable": True, "blockers": []}

        result = run_finalization_transaction(
            phase_id=report.phase_id,
            phase_name=report.phase_name,
            report=report,
            gate=lying_gate,
            transaction_root=tmp_path / "txns",
            receipt_root=tmp_path / "receipts",
        )
        assert result.status == "gate_not_passed"


# ═══════════════════════════════════════════════════════════════════════
# 3. Capture failure never affects the already-certified report
# ═══════════════════════════════════════════════════════════════════════


class TestCaptureFailureIsNonFatal:
    def test_capture_exception_yields_capture_failed_not_a_raise(self, tmp_path):
        report, gate = _certified_report(phase_id="999X-capture-fail-test")

        with mock.patch(
            "pcae.core.finalization_transaction._capture_evidence",
            side_effect=RuntimeError("synthetic capture bug"),
        ):
            result = run_finalization_transaction(
                phase_id=report.phase_id,
                phase_name=report.phase_name,
                report=report,
                gate=gate,
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )
        assert result.status == "capture_failed"
        assert any("capture_evidence failed" in lim for lim in result.limitations)
        # The critical non-regression property: the report object itself
        # (already written by the caller before this function was ever
        # invoked) is completely untouched.
        assert report.report_completeness == "complete"

    def test_post_capture_step_exception_yields_best_effort_incomplete(self, tmp_path):
        report, gate = _certified_report(phase_id="999X-post-capture-fail-test")

        with mock.patch(
            "pcae.core.finalization_transaction._extraction.extract",
            side_effect=RuntimeError("synthetic extraction bug"),
        ):
            result = run_finalization_transaction(
                phase_id=report.phase_id,
                phase_name=report.phase_name,
                report=report,
                gate=gate,
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )
        assert result.status == "best_effort_incomplete"
        # Evidence capture itself still succeeded before the injected failure.
        assert result.evidence_id
        assert report.report_completeness == "complete"


# ═══════════════════════════════════════════════════════════════════════
# 4. Resumability / idempotency
# ═══════════════════════════════════════════════════════════════════════


class TestResumability:
    def test_second_call_for_same_certified_content_short_circuits(self, tmp_path):
        report, gate = _certified_report(phase_id="999X-resume-test")
        txn_root = tmp_path / "txns"
        rcpt_root = tmp_path / "receipts"

        first = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name,
            report=report, gate=gate, transaction_root=txn_root, receipt_root=rcpt_root,
        )
        assert first.status == "completed"

        with mock.patch(
            "pcae.core.finalization_transaction._capture_evidence",
            side_effect=AssertionError("must not be called on resume"),
        ):
            second = run_finalization_transaction(
                phase_id=report.phase_id, phase_name=report.phase_name,
                report=report, gate=gate, transaction_root=txn_root, receipt_root=rcpt_root,
            )
        assert second.status == "resumed_completed"
        assert second.evidence_id == first.evidence_id
        assert second.receipt_logical_delivery_id == first.receipt_logical_delivery_id

    def test_distinct_certified_content_does_not_collide_with_prior_completion(self, tmp_path):
        """A genuinely different certified report for the same phase_id
        (e.g. a corrective re-run) produces its own transaction record --
        it must not be silently treated as the already-completed one."""
        txn_root = tmp_path / "txns"
        rcpt_root = tmp_path / "receipts"
        report_a, gate_a = _certified_report(
            phase_id="999X-distinct-test", summary="First summary."
        )
        result_a = run_finalization_transaction(
            phase_id=report_a.phase_id, phase_name=report_a.phase_name,
            report=report_a, gate=gate_a, transaction_root=txn_root, receipt_root=rcpt_root,
        )

        report_b, gate_b = _certified_report(
            phase_id="999X-distinct-test", summary="Second, different summary."
        )
        result_b = run_finalization_transaction(
            phase_id=report_b.phase_id, phase_name=report_b.phase_name,
            report=report_b, gate=gate_b, transaction_root=txn_root, receipt_root=rcpt_root,
        )
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
        report, gate = _certified_report(phase_id="999X-safe-holder")
        with pytest.raises(ValueError):
            run_finalization_transaction(
                phase_id=bad_id,
                phase_name="x",
                report=report,
                gate=gate,
                transaction_root=tmp_path / "txns",
                receipt_root=tmp_path / "receipts",
            )

    def test_validate_identifier_accepts_ordinary_phase_ids(self):
        for ok_id in ("134E.10", "999X-safe-test", "113B.2", "134E.1V"):
            _validate_identifier(ok_id, "phase_id")  # must not raise


# ═══════════════════════════════════════════════════════════════════════
# 6. The shared boundary — no command constructs the new modules directly
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
            f"{path} does not call the shared 134E.10 finalization transaction"
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
        report, gate = _certified_report(phase_id="999X-isolation-test")
        result = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name,
            report=report, gate=gate,
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
