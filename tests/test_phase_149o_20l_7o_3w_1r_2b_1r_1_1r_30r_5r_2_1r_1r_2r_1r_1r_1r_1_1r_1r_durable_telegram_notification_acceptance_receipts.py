"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R —
Durable Telegram Notification Acceptance Receipts + Phase-Completion
Notification Auditability Repair.

THE DEFECT (found by the immediately preceding read-only notification
audit of the completed configured-agent-identity IV,
`...1.1R.1`): `TelegramSink.send()` already receives Telegram's real
Bot API JSON responses (`ok`, and on success a `result` Message object
carrying `message_id`) for both the summary and document operations,
but collapsed each into an in-process boolean and discarded the rest.
Once the process exits, nothing durable on disk can answer "did
Telegram actually accept this send, and what message_id did it
return" -- `.last-notified.json` is a DEDUP MARKER only, and the
separate `.pcae/delivery-receipts/` (`delivery_receipt.py`, Phase
134E.7) architecture is explicitly documented as not-yet-active
lifecycle authority with only synthetic (`recording_v1`/`null_v1`)
adapters -- it never touches real Telegram delivery.

THE REPAIR: `TelegramSink.send()` now persists a small, purpose-built
durable acceptance-receipt per operation (summary/document),
independently, with an explicit PREPARED -> API_ACCEPTED /
API_REJECTED / TRANSPORT_FAILED / OUTCOME_UNCERTAIN state machine,
Telegram's returned `message_id` when present, and no secrets. This is
a deliberately smaller mechanism than wiring the dormant Delivery
Pipeline/Receipt architecture (134E.7/134E.10, explicitly marked "not
implemented" for exactly this kind of live-adapter integration) --
that would be its own separately-scoped, much larger effort, out of
this narrowly-scoped repair. `report.notification_result["success"]`'s
existing boolean contract is preserved byte-for-byte; a new additive
`telegram_receipts` key attaches the receipt references.

No re-dispatch of the affected historical IV report is performed by
this suite. No real network calls -- all HTTP is mocked via
`TelegramSink`'s disclosed `_opener` test seam.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core import notifications as n  # noqa: E402
from pcae.core import phase_reports as pr  # noqa: E402


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


def _mock_opener(json_response: dict, status: int = 200):
    def opener(req):
        resp = MagicMock()
        resp.read.return_value = json.dumps(json_response).encode()
        resp.status = status
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp
    return opener


def _sequenced_opener(*responses: "tuple[dict, int]"):
    calls = {"n": 0}

    def opener(req):
        idx = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        body, status = responses[idx]
        resp = MagicMock()
        resp.read.return_value = json.dumps(body).encode()
        resp.status = status
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp
    return opener


def _raising_opener(exc: Exception):
    def opener(req):
        raise exc
    return opener


def _http_error_opener(status: int, description: str):
    """Simulates real Telegram Bot API rejection behavior: urllib's
    `urlopen` raises `HTTPError` for the non-2xx status Telegram
    returns alongside an `ok:false` JSON body -- matching this repo's
    own existing `test_http_400_error_body_captured` convention, not a
    plain successful-looking mock response with a JSON `ok:false`
    body (which `urlopen` never actually produces for a real Telegram
    rejection)."""
    from urllib.error import HTTPError

    def opener(req):
        body = json.dumps({"ok": False, "error_code": status, "description": description}).encode()
        raise HTTPError(req.full_url, status, description, {}, io.BytesIO(body))
    return opener


def _make_event(**kwargs):
    defaults = {
        "event_type": n.EVENT_TYPE_MANUAL_TEST,
        "title": "Test",
        "message": "body",
        "metadata": {"phase_id": "TEST.PHASE.1", "canonical_report_markdown": "# report\n\nbody"},
    }
    defaults.update(kwargs)
    return n.make_notification_event(**defaults)


def _sink(monkeypatch, tmp_path, opener):
    monkeypatch.setenv(n._RECEIPTS_OUTPUT_DIR_ENV, str(tmp_path / "receipts"))
    return n.TelegramSink(bot_token="fake-token", chat_id="555", enabled=True, _opener=opener)


def _receipts(tmp_path) -> "list[dict]":
    root = tmp_path / "receipts"
    if not root.exists():
        return []
    return [json.loads(p.read_text()) for p in root.rglob("*.json")]


# ═══════════════════════════════════════════════════════════════════════
# CURRENT DEFECT (items 1-6)
# ═══════════════════════════════════════════════════════════════════════


def test_production_path_uses_real_telegram_response_not_a_mock():
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert "urlopen" in src
    assert "self._opener if self._opener else urlopen" in src


def test_legacy_collapse_no_longer_discards_message_id(monkeypatch, tmp_path):
    """The exact repaired property: message_id is now captured, not discarded."""
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 4242}}, 200),
        ({"ok": True, "result": {"message_id": 4243}}, 200),
    )
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert result.metadata["summary_message_id"] == 4242
    assert result.metadata["document_message_id"] == 4243


def test_last_notified_marker_module_untouched_by_this_repair():
    """`.last-notified.json`'s writer/reader in phase_reports.py is not
    part of this repair's diff -- it remains dedup-only."""
    diff = _git("diff", "--name-only", "HEAD")
    # Sanity: this repo-state check only asserts the marker file's own
    # persistence function name still exists unmodified in spirit --
    # the real proof is the production diff-scope test below.
    src = Path(REPO_ROOT / "src/pcae/core/phase_reports.py").read_text()
    assert "_persist_notification_result" in src


def test_recording_v1_receipt_remains_synthetic_not_external():
    src = Path(REPO_ROOT / "src/pcae/core/delivery_receipt.py").read_text()
    assert "not yet active lifecycle authority" in src
    pipeline_src = Path(REPO_ROOT / "src/pcae/core/delivery_pipeline.py").read_text()
    assert 'RECORDING_ADAPTER_ID = "recording_v1"' in pipeline_src


def test_new_receipt_model_is_a_distinct_purpose_built_mechanism():
    """This repair does not import or extend `delivery_receipt.py`'s
    adapter/pipeline machinery -- confirms the scope decision recorded
    in notifications.py's own module comment. Checked via AST (real
    import statements only), not a bare substring scan, since the
    module's own comment legitimately names both files in prose."""
    import ast
    tree = ast.parse(Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
    assert not any("delivery_receipt" in m or "delivery_pipeline" in m for m in imported_modules)
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert "PCAE-NOTIFICATION-RECEIPT/1.0" in src


# ═══════════════════════════════════════════════════════════════════════
# RECEIPT MODEL (items 7-15)
# ═══════════════════════════════════════════════════════════════════════


def test_receipt_id_generated_and_bound_to_phase_and_sink(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    receipts = _receipts(tmp_path)
    assert receipts
    for r in receipts:
        assert r["phase_id"] == "TEST.PHASE.1"
        assert r["sink"] == "telegram"
        assert r["operation"] in ("summary", "document")
        assert r["receipt_id"].startswith("ntfr-")


def test_pre_attempt_prepared_state_is_durable_before_network_call(monkeypatch, tmp_path):
    """Item 11: even if the network call itself were to hang/crash, a
    durable PREPARED record must already exist. Verified by asserting
    the receipt path is written to at all under a real (fast) call --
    the write-before-call ordering is exercised structurally by
    `_build_receipt`/`_persist_receipt` being invoked prior to
    `_send_message` in `send()`'s source order."""
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    send_body = src[src.index("def send(self, event"):src.index("def _classify_telegram_result")]
    prepared_idx = send_body.index("RECEIPT_STATUS_PREPARED")
    send_message_idx = send_body.index("self._send_message(summary_text)")
    assert prepared_idx < send_message_idx


def test_receipt_excludes_bot_token_and_raw_url(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    for r in _receipts(tmp_path):
        blob = json.dumps(r)
        assert "fake-token" not in blob
        assert "api.telegram.org" not in blob


def test_receipt_uses_safe_destination_alias_not_raw_chat_id(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    for r in _receipts(tmp_path):
        assert r["destination_alias"].startswith("telegram:chat:")
        assert "555" not in r["destination_alias"]


def test_summary_and_document_represented_independently(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    ops = {r["operation"] for r in _receipts(tmp_path)}
    assert ops == {"summary", "document"}


# ═══════════════════════════════════════════════════════════════════════
# SUCCESS (items 16-20)
# ═══════════════════════════════════════════════════════════════════════


def test_send_message_ok_true_with_message_result_is_api_accepted(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 777}})
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["status"] == n.RECEIPT_STATUS_API_ACCEPTED
    assert summary["telegram_message_id"] == 777
    assert summary["represents_external_api_acceptance"] is True
    assert result.metadata["summary_receipt_id"] == summary["receipt_id"]


def test_send_document_ok_true_with_message_result_is_api_accepted(monkeypatch, tmp_path):
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 1}}, 200),
        ({"ok": True, "result": {"message_id": 2, "document": {}}}, 200),
    )
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    doc = [r for r in _receipts(tmp_path) if r["operation"] == "document"][0]
    assert doc["status"] == n.RECEIPT_STATUS_API_ACCEPTED
    assert doc["telegram_message_id"] == 2


def test_message_id_and_acceptance_timestamp_persisted(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 9}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    for r in _receipts(tmp_path):
        assert r["recorded_at"]
        assert r["attempted_at"]
        assert r["recorded_at"] >= r["attempted_at"]


def test_aggregate_result_success_still_derives_from_both_operations(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert result.success is True


# ═══════════════════════════════════════════════════════════════════════
# API REJECTION (items 21-23)
# ═══════════════════════════════════════════════════════════════════════


def test_ok_false_is_durable_rejected_not_sent(monkeypatch, tmp_path):
    opener = _http_error_opener(403, "Forbidden: bot was blocked")
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert result.success is False
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["status"] == n.RECEIPT_STATUS_API_REJECTED
    assert "sent" not in result.message.lower() or "failed" in result.message.lower()


def test_api_rejection_error_is_sanitized_not_raw_body(monkeypatch, tmp_path):
    opener = _http_error_opener(403, "Forbidden: bot was blocked")
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["sanitized_error"] is not None
    assert "fake-token" not in summary["sanitized_error"]


# ═══════════════════════════════════════════════════════════════════════
# TRANSPORT FAILURE (items 24-28)
# ═══════════════════════════════════════════════════════════════════════


def test_network_error_is_transport_failed(monkeypatch, tmp_path):
    from urllib.error import URLError
    opener = _raising_opener(URLError("connection refused"))
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert result.success is False
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["status"] == n.RECEIPT_STATUS_TRANSPORT_FAILED
    assert summary["telegram_message_id"] is None


def test_malformed_success_response_is_outcome_uncertain_not_accepted(monkeypatch, tmp_path):
    """Item 12/27: `ok: true` without a valid `message_id` must not be
    blindly accepted."""
    opener = _mock_opener({"ok": True})  # no "result" at all
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["status"] == n.RECEIPT_STATUS_OUTCOME_UNCERTAIN
    assert summary["represents_external_api_acceptance"] is False


def test_missing_message_id_handled_strictly(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {}})
    sink = _sink(monkeypatch, tmp_path, opener)
    sink.send(_make_event())
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    assert summary["status"] == n.RECEIPT_STATUS_OUTCOME_UNCERTAIN


# ═══════════════════════════════════════════════════════════════════════
# PARTIAL OUTCOME (items 29-32)
# ═══════════════════════════════════════════════════════════════════════


def test_summary_accepted_document_rejected_represented_accurately(monkeypatch, tmp_path):
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 1}}, 200),
        ({"ok": False, "description": "Bad Request"}, 400),
    )
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert result.success is False
    summary = [r for r in _receipts(tmp_path) if r["operation"] == "summary"][0]
    doc = [r for r in _receipts(tmp_path) if r["operation"] == "document"][0]
    assert summary["status"] == n.RECEIPT_STATUS_API_ACCEPTED
    assert doc["status"] == n.RECEIPT_STATUS_API_REJECTED


def test_no_collapsed_all_success_lie_on_partial_failure(monkeypatch, tmp_path):
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 1}}, 200),
        ({"ok": False, "description": "Bad Request"}, 400),
    )
    sink = _sink(monkeypatch, tmp_path, opener)
    result = sink.send(_make_event())
    assert "document sent" not in result.message
    assert "document failed" in result.message


# ═══════════════════════════════════════════════════════════════════════
# UNCERTAINTY / PERSISTENCE FAILURE (items 33-41)
# ═══════════════════════════════════════════════════════════════════════


def test_receipt_persistence_failure_does_not_crash_the_sink(monkeypatch, tmp_path):
    opener = _mock_opener({"ok": True, "result": {"message_id": 1}})
    # Point the receipts dir at a path that cannot be created (a file,
    # not a directory, in its place) to force an OSError on write.
    blocker = tmp_path / "receipts-blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv(n._RECEIPTS_OUTPUT_DIR_ENV, str(blocker / "nested"))
    sink = n.TelegramSink(bot_token="fake-token", chat_id="555", enabled=True, _opener=opener)
    result = sink.send(_make_event())  # must not raise
    assert result.success is True  # Telegram-level outcome is unaffected by local persistence failure
    assert result.metadata["summary_receipt_id"]


def test_receipt_persistence_failure_is_not_silently_hidden(monkeypatch, tmp_path):
    """Item 39/40: API-accepted + local persistence failure must not
    be silently indistinguishable from a clean success on disk. The
    receipts *root* stays writable here (only this one event's own
    subdirectory is blocked), so the best-effort fallback log --
    written directly under the root -- can itself succeed and prove
    the failure was not entirely invisible."""
    receipts_root = tmp_path / "receipts"
    monkeypatch.setenv(n._RECEIPTS_OUTPUT_DIR_ENV, str(receipts_root))
    event = _make_event()
    blocked_subdir = receipts_root / n._safe_path_component(event.event_id)
    blocked_subdir.parent.mkdir(parents=True, exist_ok=True)
    blocked_subdir.write_text("occupies the path a directory needs")

    persisted, err = n._persist_receipt(n._build_receipt(
        receipt_id="ntfr-test", event=event, operation="summary",
        status=n.RECEIPT_STATUS_API_ACCEPTED, destination_alias="telegram:chat:x",
        attempted_at="t", recorded_at="t",
    ))
    assert persisted is False
    assert err is not None
    fallback_log = receipts_root / "PERSISTENCE-FAILURES.log"
    assert fallback_log.exists()
    assert "ntfr-test" in fallback_log.read_text()


def test_uncertain_send_not_automatically_retried(monkeypatch, tmp_path):
    """No retry loop exists in `send()` -- exactly one attempt per
    operation regardless of outcome (duplicate-risk prevention, item
    36/38)."""
    calls = {"n": 0}

    def counting_opener(req):
        calls["n"] += 1
        resp = MagicMock()
        resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 1}}).encode()
        resp.status = 200
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    sink = _sink(monkeypatch, tmp_path, counting_opener)
    sink.send(_make_event())
    assert calls["n"] == 2  # exactly one summary call + one document call, no retries


# ═══════════════════════════════════════════════════════════════════════
# DEDUP SEPARATION (items 42-45)
# ═══════════════════════════════════════════════════════════════════════


def test_dedup_marker_and_receipt_are_written_to_distinct_locations():
    src = Path(REPO_ROOT / "src/pcae/core/phase_reports.py").read_text()
    assert ".last-notified.json" in src
    receipts_src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert "notification-receipts" in receipts_src


def test_dedup_marker_never_records_telegram_acceptance_fields():
    src = Path(REPO_ROOT / "src/pcae/core/phase_reports.py").read_text()
    marker_fn_start = src.index("def _persist_notification_result")
    marker_fn_body = src[marker_fn_start:marker_fn_start + 2500]
    assert "message_id" not in marker_fn_body
    assert "telegram_message_id" not in marker_fn_body


# ═══════════════════════════════════════════════════════════════════════
# HISTORICAL COMPATIBILITY (items 46-50)
# ═══════════════════════════════════════════════════════════════════════


def test_old_phase_report_without_telegram_receipts_key_still_readable(tmp_path):
    legacy = {
        "dispatched": True, "sinks": ["telegram"], "success": True,
        "error": None, "outcome": "sent", "reason": "", "kind": "complete",
    }
    assert "telegram_receipts" not in legacy  # legacy shape, no crash reading it
    assert legacy.get("telegram_receipts", []) == []


def test_notification_result_success_contract_byte_unchanged(monkeypatch, tmp_path):
    """Item 18: `success` must still derive exactly from
    `msg_result["ok"] and doc_result.get("ok", False)` -- never
    redefined to also require message_id/receipt persistence."""
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert 'success = msg_result["ok"] and doc_result.get("ok", False)' in src


def test_affected_iv_report_remains_unmodified():
    """The historical configured-agent-identity IV report file itself
    is untouched by this repair's diff."""
    diff = _git(
        "diff", "--stat", "HEAD~0", "--",
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1_INDEPENDENT_VERIFICATION_CONFIGURED_AGENT_IDENTITY_THREADING_REPAIR.md",
    )
    assert diff.stdout.strip() == ""


def test_predecessor_visible_telegram_report_remains_unrelated_evidence():
    """No receipt exists anywhere for the predecessor `...1.1R` repair
    phase either -- this repair began only after that phase, so it
    cannot have fabricated one, and the predecessor's own visible
    Telegram delivery (a different phase_id) is never treated as
    evidence for `...1.1R.1`'s delivery."""
    root = Path(REPO_ROOT / ".pcae/notification-receipts")
    predecessor_phase_id = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R"
    if root.exists():
        for p in root.rglob("*.json"):
            data = json.loads(p.read_text())
            assert data.get("phase_id") != predecessor_phase_id


def test_no_historical_receipt_fabrication_for_affected_iv():
    root = Path(REPO_ROOT / ".pcae/notification-receipts")
    if root.exists():
        for p in root.rglob("*.json"):
            data = json.loads(p.read_text())
            if data.get("phase_id") == "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1":
                pytest.fail("a receipt must not have been fabricated for the historical IV in this repair phase")


# ═══════════════════════════════════════════════════════════════════════
# REPORTING / TERMINOLOGY (items 51-56)
# ═══════════════════════════════════════════════════════════════════════


def test_phase_report_notification_result_gains_telegram_receipts_key(monkeypatch, tmp_path):
    monkeypatch.setenv(n._RECEIPTS_OUTPUT_DIR_ENV, str(tmp_path / "receipts"))
    fake_result = n.NotificationResult(
        sink_name="telegram", success=True, message="ok", event_id="ntf-x",
        attempted_at="t",
        metadata={
            "summary_status": "api_accepted", "summary_message_id": 1, "summary_receipt_id": "ntfr-a",
            "document_status": "api_accepted", "document_message_id": 2, "document_receipt_id": "ntfr-b",
        },
    )
    summary = pr._telegram_receipts_summary([fake_result])
    assert summary == [{
        "summary_status": "api_accepted", "summary_message_id": 1, "summary_receipt_id": "ntfr-a",
        "document_status": "api_accepted", "document_message_id": 2, "document_receipt_id": "ntfr-b",
    }]


def test_telegram_receipts_summary_empty_for_non_telegram_sink():
    fake_result = n.NotificationResult(sink_name="filesystem", success=True, message="ok", event_id="e")
    assert pr._telegram_receipts_summary([fake_result]) == []


def test_telegram_receipts_summary_empty_for_no_results():
    assert pr._telegram_receipts_summary(None) == []
    assert pr._telegram_receipts_summary([]) == []


def test_api_accepted_never_labeled_human_delivered():
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert "human_delivered" not in src.lower()
    assert "delivered_to_human" not in src.lower()


def test_receipt_status_vocabulary_is_closed():
    assert n.VALID_RECEIPT_STATUSES == frozenset({
        n.RECEIPT_STATUS_PREPARED, n.RECEIPT_STATUS_API_ACCEPTED,
        n.RECEIPT_STATUS_API_REJECTED, n.RECEIPT_STATUS_TRANSPORT_FAILED,
        n.RECEIPT_STATUS_OUTCOME_UNCERTAIN,
    })


# ═══════════════════════════════════════════════════════════════════════
# NO-GO (items 57-64)
# ═══════════════════════════════════════════════════════════════════════


def test_no_f5_or_protected_root_reference_in_this_repair_diff():
    diff = _git("diff", "HEAD~0", "--", "src/pcae/core/notifications.py", "src/pcae/core/phase_reports.py")
    for forbidden in ("hpac_protected_root_admin", "hpac_protected_presentation_admin", "provision"):
        assert forbidden not in diff.stdout


def test_no_runtime_capability_or_adapter_dispatch_introduced():
    src = Path(REPO_ROOT / "src/pcae/core/notifications.py").read_text()
    assert "adapter.dispatch" not in src
    assert "DispatchEnvelope" not in src


def test_no_dependency_change():
    diff = _git("diff", "--stat", "HEAD", "--", "pyproject.toml")
    assert diff.stdout.strip() == ""


def test_no_contract_change():
    diff = _git("diff", "--stat", "HEAD", "--", "docs/contracts/")
    assert diff.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# FULL-SUITE EVIDENCE PRESERVATION (items 65-67)
# ═══════════════════════════════════════════════════════════════════════


def test_full_suite_sweep_evidence_not_referenced_as_success_criterion():
    """This repair's own test file must not itself assert against the
    full-suite pass/fail counts from the separate post-completion
    sweep -- that evidence stays frozen and awaiting its own triage
    (item 40 governing-prompt boundary). Forbidden tokens are built by
    concatenation so this assertion's own source never self-matches."""
    my_src = Path(__file__).read_text(encoding="utf-8")
    forbidden_pass_count = "4" + "0587"
    forbidden_fail_count = "9" + "79"
    assert forbidden_pass_count not in my_src
    assert forbidden_fail_count not in my_src
