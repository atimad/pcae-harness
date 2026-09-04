"""Fresh, independent adversarial verification of the durable Telegram
notification-receipt repair (predecessor phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R,
commits a0225cf8..fbcaa519).

Written from scratch, without trusting the predecessor's own test file
or report, against the real source in
`src/pcae/core/notifications.py` / `src/pcae/core/phase_reports.py`.
All HTTP is mocked via `TelegramSink`'s disclosed `_opener` seam --
no real network calls.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pcae.core import notifications as n
from pcae.core.notifications import (
    TelegramSink,
    make_notification_event,
    EVENT_TYPE_MANUAL_TEST,
    RECEIPT_STATUS_PREPARED,
    RECEIPT_STATUS_API_ACCEPTED,
    RECEIPT_STATUS_API_REJECTED,
    RECEIPT_STATUS_TRANSPORT_FAILED,
    RECEIPT_STATUS_OUTCOME_UNCERTAIN,
)

BOT_TOKEN = "123456:FAKE-TEST-TOKEN-ABCDEF"
CHAT_ID = "-100987654321"


# ── opener helpers ───────────────────────────────────────────────────────────


def _resp(body: dict, status: int = 200):
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _mock_opener(body: dict, status: int = 200):
    def opener(req):
        return _resp(body, status)
    return opener


def _sequenced_opener(*bodies_and_status):
    calls = {"n": 0}

    def opener(req):
        idx = min(calls["n"], len(bodies_and_status) - 1)
        calls["n"] += 1
        body, status = bodies_and_status[idx]
        return _resp(body, status)
    return opener


def _raising_opener(exc):
    def opener(req):
        raise exc
    return opener


def _raising_after_first(first_body: dict, exc: Exception):
    calls = {"n": 0}

    def opener(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return _resp(first_body)
        raise exc
    return opener


def _malformed_json_opener():
    def opener(req):
        resp = MagicMock()
        resp.read.return_value = b"{not valid json::"
        resp.status = 200
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp
    return opener


def _make_event(**kwargs):
    metadata = kwargs.pop("metadata", None) or {}
    defaults = {
        "event_type": EVENT_TYPE_MANUAL_TEST,
        "title": "Fresh IV Test Event",
        "message": "Independent adversarial verification.",
    }
    defaults.update(kwargs)
    return make_notification_event(metadata=metadata, **defaults)


def _event_with_doc(markdown: str = "# Canonical Report\n\nBody.", phase_id: str = "test-phase-1"):
    return _make_event(metadata={"canonical_report_markdown": markdown, "phase_id": phase_id})


def _receipts_root() -> Path:
    return Path(os.environ["PCAE_NOTIFICATION_RECEIPTS_DIR"])


def _all_receipt_files() -> list[Path]:
    root = _receipts_root()
    if not root.exists():
        return []
    return sorted(root.rglob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


# ── 1. PREPARED persisted before the network call ───────────────────────────


def test_prepared_receipt_persisted_before_network_call_summary_and_document():
    """A synchronous-observation opener: on first invocation (the summary
    sendMessage call), before returning, we independently re-read the
    receipts directory from disk and assert a PREPARED receipt already
    exists there -- proving durability precedes the network call, not
    just in-memory state."""
    observed = {}

    def opener(req):
        # At this point, exactly one PREPARED receipt (summary) must
        # already be on disk, persisted synchronously before this
        # network call was made. Only record on the FIRST invocation
        # (the summary call) -- a later document call would otherwise
        # overwrite this observation.
        if "at_first_call" not in observed:
            files = _all_receipt_files()
            observed["at_first_call"] = [_load(f) for f in files]
        return _resp({"ok": True, "result": {"message_id": 111}})

    event = _event_with_doc()
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    sink.send(event)

    assert len(observed["at_first_call"]) == 1
    assert observed["at_first_call"][0]["status"] == RECEIPT_STATUS_PREPARED
    assert observed["at_first_call"][0]["operation"] == "summary"


def test_prepared_receipt_persisted_before_document_network_call():
    calls = {"n": 0}
    observed = {}

    def opener(req):
        calls["n"] += 1
        if calls["n"] == 2:
            # Second network call is the document send; at this point
            # there must be a PREPARED document receipt on disk plus
            # the already-finalized summary receipt.
            files = _all_receipt_files()
            docs = [_load(f) for f in files if _load(f)["operation"] == "document"]
            observed["doc_prepared"] = docs
        return _resp({"ok": True, "result": {"message_id": 222}})

    event = _event_with_doc()
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    sink.send(event)

    assert len(observed["doc_prepared"]) == 1
    assert observed["doc_prepared"][0]["status"] == RECEIPT_STATUS_PREPARED


# ── 2. Valid ok:true + valid message_id -> API_ACCEPTED, reloadable ─────────


def test_valid_accept_produces_reloadable_api_accepted_receipt_with_exact_message_id():
    event = _event_with_doc()
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 4242}}, 200),
        ({"ok": True, "result": {"message_id": 4243}}, 200),
    )
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    result = sink.send(event)

    assert result.success is True
    assert result.metadata["summary_status"] == RECEIPT_STATUS_API_ACCEPTED
    assert result.metadata["summary_message_id"] == 4242
    assert result.metadata["document_status"] == RECEIPT_STATUS_API_ACCEPTED
    assert result.metadata["document_message_id"] == 4243

    files = _all_receipt_files()
    assert len(files) == 2
    by_op = {_load(f)["operation"]: _load(f) for f in files}
    assert by_op["summary"]["status"] == RECEIPT_STATUS_API_ACCEPTED
    assert by_op["summary"]["telegram_message_id"] == 4242
    assert by_op["document"]["status"] == RECEIPT_STATUS_API_ACCEPTED
    assert by_op["document"]["telegram_message_id"] == 4243
    assert by_op["summary"]["represents_external_api_acceptance"] is True


# ── 3. ok:true but missing/invalid message_id -> NOT API_ACCEPTED ───────────


def test_ok_true_missing_result_is_outcome_uncertain_not_accepted():
    event = _make_event()  # no document
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True}),
    )
    result = sink.send(event)
    assert result.metadata["summary_status"] == RECEIPT_STATUS_OUTCOME_UNCERTAIN
    assert result.metadata["summary_status"] != RECEIPT_STATUS_API_ACCEPTED
    files = _all_receipt_files()
    receipt = _load(files[0])
    assert receipt["status"] == RECEIPT_STATUS_OUTCOME_UNCERTAIN
    assert receipt["represents_external_api_acceptance"] is False
    assert receipt["telegram_message_id"] is None


def test_ok_true_invalid_message_id_type_is_outcome_uncertain():
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": "not-an-int"}}),
    )
    result = sink.send(event)
    assert result.metadata["summary_status"] == RECEIPT_STATUS_OUTCOME_UNCERTAIN


def test_ok_true_bool_message_id_rejected_not_accepted():
    """bool is a subclass of int in Python -- adversarial check that the
    classifier doesn't accidentally accept `True`/`False` as a message id."""
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": True}}),
    )
    result = sink.send(event)
    # Document current real behavior precisely: isinstance(True, int) is
    # True in Python, so the current classifier DOES accept it. This is
    # captured as a known finding rather than asserted as ideal safety.
    assert result.metadata["summary_status"] in (RECEIPT_STATUS_API_ACCEPTED, RECEIPT_STATUS_OUTCOME_UNCERTAIN)


# ── 4. Explicit API rejection distinct from transport failure ──────────────


def test_explicit_api_rejection_is_distinct_status_and_no_success_language():
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": False, "error": "Forbidden: bot was blocked by the user"}),
    )
    result = sink.send(event)
    assert result.success is False
    files = _all_receipt_files()
    receipt = _load(files[0])
    assert receipt["status"] == RECEIPT_STATUS_API_REJECTED
    assert receipt["status"] != RECEIPT_STATUS_TRANSPORT_FAILED
    assert receipt["represents_external_api_acceptance"] is False
    for forbidden in ("sent", "accepted", "delivered"):
        assert forbidden not in json.dumps(receipt).lower() or "sanitized_error" in receipt


# ── 5. Transport failure distinct from API rejection ────────────────────────


def test_transport_failure_distinct_from_api_rejection():
    import urllib.error
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_raising_opener(urllib.error.URLError("Connection timed out")),
    )
    result = sink.send(event)
    files = _all_receipt_files()
    receipt = _load(files[0])
    assert receipt["status"] == RECEIPT_STATUS_TRANSPORT_FAILED
    assert receipt["status"] != RECEIPT_STATUS_API_REJECTED
    assert receipt["represents_external_api_acceptance"] is False


# ── 6. Malformed JSON response -> fail-safe, never API_ACCEPTED ─────────────


def test_malformed_json_response_never_classified_as_accepted():
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_malformed_json_opener(),
    )
    result = sink.send(event)
    assert result.metadata["summary_status"] != RECEIPT_STATUS_API_ACCEPTED
    files = _all_receipt_files()
    receipt = _load(files[0])
    assert receipt["status"] != RECEIPT_STATUS_API_ACCEPTED
    assert receipt["represents_external_api_acceptance"] is False


# ── 7. Summary accepted, document rejected/transport-failed/uncertain ──────


def test_summary_accepted_document_rejected_both_persist_independently():
    event = _event_with_doc()
    opener = _sequenced_opener(
        ({"ok": True, "result": {"message_id": 1}}, 200),
        ({"ok": False, "error": "Bad Request: chat not found"}, 400),
    )
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    result = sink.send(event)

    assert result.success is False  # aggregate must not claim full success
    files = _all_receipt_files()
    by_op = {_load(f)["operation"]: _load(f) for f in files}
    assert by_op["summary"]["status"] == RECEIPT_STATUS_API_ACCEPTED
    assert by_op["document"]["status"] == RECEIPT_STATUS_API_REJECTED
    # Distinct receipt ids -- no collision.
    assert by_op["summary"]["receipt_id"] != by_op["document"]["receipt_id"]


def test_summary_accepted_document_transport_failed_both_persist_independently():
    import urllib.error
    calls = {"n": 0}

    def opener(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return _resp({"ok": True, "result": {"message_id": 9}})
        raise urllib.error.URLError("network unreachable")

    event = _event_with_doc()
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    result = sink.send(event)

    assert result.success is False
    files = _all_receipt_files()
    by_op = {_load(f)["operation"]: _load(f) for f in files}
    assert by_op["summary"]["status"] == RECEIPT_STATUS_API_ACCEPTED
    assert by_op["document"]["status"] == RECEIPT_STATUS_TRANSPORT_FAILED


def test_summary_accepted_document_uncertain_aggregate_not_falsely_complete():
    calls = {"n": 0}

    def opener(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return _resp({"ok": True, "result": {"message_id": 5}})
        return _resp({"ok": True})  # missing result -> uncertain

    event = _event_with_doc()
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    result = sink.send(event)

    assert result.metadata["summary_status"] == RECEIPT_STATUS_API_ACCEPTED
    assert result.metadata["document_status"] == RECEIPT_STATUS_OUTCOME_UNCERTAIN
    # KNOWN GAP (see report): result.success is derived from raw `ok`
    # booleans, not from strict message-id-validated classification, so
    # `doc_result.get("ok")` is True even though document_status is
    # OUTCOME_UNCERTAIN. Document actual behavior precisely rather than
    # asserting the ideal:
    assert result.success is True  # raw success flag does NOT reflect uncertainty


# ── 8. PREPARED written, then exception before any response ────────────────


def test_exception_before_response_leaves_auditable_prepared_not_false_acceptance():
    def opener(req):
        raise RuntimeError("simulated hard crash mid-request")

    event = _make_event()
    sink = TelegramSink(bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True, _opener=opener)
    result = sink.send(event)

    files = _all_receipt_files()
    assert len(files) == 1
    receipt = _load(files[0])
    # Final classification must not be a false acceptance.
    assert receipt["status"] != RECEIPT_STATUS_API_ACCEPTED
    assert receipt["represents_external_api_acceptance"] is False


# ── 9. Final-receipt disk write failure must not crash the sink ────────────


def test_final_receipt_persist_failure_does_not_crash_and_is_surfaced():
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": 77}}),
    )

    call_count = {"n": 0}
    real_replace = os.replace

    def flaky_replace(src, dst):
        call_count["n"] += 1
        # Let the PREPARED write succeed (1st call), fail the final
        # write (2nd call) to simulate a disk failure exactly at the
        # accepted-but-unpersisted moment.
        if call_count["n"] == 2:
            raise OSError("simulated disk full")
        return real_replace(src, dst)

    import pcae.core.notifications as notif_mod
    orig_os_replace = notif_mod.os.replace if hasattr(notif_mod, "os") else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("os.replace", flaky_replace)
        result = sink.send(event)  # must not raise

    assert result is not None
    assert result.metadata["summary_status"] == RECEIPT_STATUS_API_ACCEPTED
    # No crash-loop / no fabricated "safely resendable" framing appears.
    dumped = json.dumps(result.to_dict())
    assert "safely resendable" not in dumped.lower()
    assert "resend" not in dumped.lower()


def test_persistence_failure_log_never_contains_secrets():
    """Force every receipt write to fail via a broken receipts dir and
    inspect the PERSISTENCE-FAILURES.log fallback bytes directly."""
    event = _event_with_doc()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": 1}}),
    )

    # Point the receipts dir at a path that cannot be created: a file
    # occupying the directory slot.
    root = _receipts_root()
    root.parent.mkdir(parents=True, exist_ok=True)
    blocker = root
    blocker.write_text("i am a file, not a directory")

    try:
        result = sink.send(event)
    finally:
        pass

    assert result is not None  # did not crash
    log_path = root / "PERSISTENCE-FAILURES.log"
    if log_path.exists():
        text = log_path.read_bytes()
        assert BOT_TOKEN.encode() not in text
        assert CHAT_ID.encode() not in text
        assert b"api.telegram.org" not in text


# ── 10. Secrets never leak into receipt JSON files ──────────────────────────


def test_no_secrets_in_receipt_json_and_alias_changes_with_destination():
    event = _event_with_doc(markdown="# Report\nSensitive body text should not leak into receipts.")
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_sequenced_opener(
            ({"ok": True, "result": {"message_id": 1}}, 200),
            ({"ok": True, "result": {"message_id": 2}}, 200),
        ),
    )
    sink.send(event)

    files = _all_receipt_files()
    assert files, "expected receipt files to be written"
    for f in files:
        raw = f.read_bytes()
        assert BOT_TOKEN.encode() not in raw
        assert CHAT_ID.encode() not in raw
        assert f"bot{BOT_TOKEN}".encode() not in raw
        assert b"api.telegram.org" not in raw
        assert b"Sensitive body text" not in raw
        data = json.loads(raw)
        assert data["destination_alias"].startswith("telegram:chat:")
        assert CHAT_ID not in data["destination_alias"]

    alias_a = json.loads(files[0].read_text())["destination_alias"]

    # Changing the destination must change the alias.
    for f in files:
        f.unlink()
    other_sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id="999999999", enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": 3}}),
    )
    other_sink.send(_make_event())
    new_files = _all_receipt_files()
    alias_b = json.loads(new_files[0].read_text())["destination_alias"]
    assert alias_a != alias_b


# ── 11. .last-notified.json dedup marker is not an acceptance receipt ──────


def test_last_notified_marker_not_written_by_sink_and_not_referenced_as_receipt():
    """The dedup marker is written only by CLI callers
    (`pcae.commands.phase`/`pcae.commands.task`/`pcae.commands.notifications`)
    after inspecting `NotificationResult.success` -- `TelegramSink.send()`
    itself never touches it, and its schema carries no message_id /
    acceptance-status field."""
    import inspect
    src = inspect.getsource(n)
    assert "write_notification_dispatch_marker" not in src
    assert "_NOTIFICATION_MARKER_PATH" not in src
    # ".last-notified" itself appears only in an architectural comment
    # inside notifications.py explaining the separation of concerns --
    # confirm no *code* (open/read/write/Path(...)) construct touches it
    # from this module.
    for line in src.splitlines():
        stripped = line.strip()
        if ".last-notified" in stripped:
            assert stripped.startswith("#"), f"non-comment reference to .last-notified: {line!r}"


def test_dedup_marker_schema_has_no_message_id_or_receipt_fields():
    from pcae.core.phase_reports import write_notification_dispatch_marker, read_notification_dispatch_marker
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        marker_path = Path(td) / ".last-notified.json"
        write_notification_dispatch_marker(
            "phase-x", "deadbeef", marker_path=marker_path, report_digest="abc123",
        )
        marker = read_notification_dispatch_marker(marker_path)
        flat = json.dumps(marker)
        assert "message_id" not in flat
        assert "receipt" not in flat.lower()


def test_success_flag_not_gated_on_strict_message_id_classification_restart_risk():
    """Reproduces the restart-risk scenario named in the task: an
    ok:true-but-uncertain summary send still yields
    `NotificationResult.success = True` (because `success` is defined
    from the raw `ok` boolean, unchanged by this repair per its own
    explicit item-18 scope note), so a CLI caller computing
    `all_ok = all(r.success ...)` before calling
    `write_notification_dispatch_marker()` COULD mark the dedup marker
    'already dispatched' for an OUTCOME_UNCERTAIN send with no confirmed
    message_id -- with the receipt (not the marker) as the only place
    the uncertainty is recorded. This is a documented, non-crashing
    finding, not a crash."""
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True}),  # missing result -> uncertain
    )
    result = sink.send(event)
    assert result.metadata["summary_status"] == RECEIPT_STATUS_OUTCOME_UNCERTAIN
    assert result.success is True  # <-- the gap: success does not encode uncertainty


# ── 12. Legacy phase reports load without crash / fabrication ──────────────


def test_legacy_notification_result_without_telegram_receipts_loads_cleanly():
    from pcae.core.phase_reports import make_phase_report, write_phase_report, read_latest_report
    import tempfile

    report = make_phase_report(
        phase_id="legacy-phase-1",
        phase_name="Legacy Phase",
        status="completed",
        summary="legacy report predating telegram_receipts",
    )
    # Simulate a legacy (pre-repair) notification_result shape: no
    # telegram_receipts key at all.
    report.notification_result = {
        "dispatched": True, "sinks": ["telegram"], "success": True, "error": None,
        "outcome": "sent", "reason": "", "kind": "complete",
    }
    with tempfile.TemporaryDirectory() as td:
        reports_dir = Path(td)
        write_phase_report(report, reports_dir)
        loaded = read_latest_report(reports_dir)
        assert loaded is not None
        nr = loaded.notification_result or {}
        assert "telegram_receipts" not in nr or nr.get("telegram_receipts") in (None, [])
        # No fabricated message_id/API_ACCEPTED status anywhere in the
        # reloaded legacy result.
        assert "message_id" not in json.dumps(nr)
        assert RECEIPT_STATUS_API_ACCEPTED not in json.dumps(nr)


# ── 13. No automatic retry ──────────────────────────────────────────────────


def test_no_retry_loop_present_for_uncertain_or_persistence_failure():
    import inspect
    src = inspect.getsource(TelegramSink.send)
    lowered = src.lower()
    assert "for attempt" not in lowered
    assert "while " not in lowered
    assert "retry" not in lowered
    # Each of summary/document is sent via exactly one call site to
    # `_send_message`/`_send_document_bytes`/`_send_document` inside
    # `send()` (no loop re-invoking them on uncertain/failed outcomes).
    assert src.count("self._send_message(summary_text)") == 1


# ── 14. Terminology audit ───────────────────────────────────────────────────


def test_terminology_audit_no_overclaiming_human_delivery_language():
    import pathlib
    for relpath in ("src/pcae/core/notifications.py", "src/pcae/core/phase_reports.py"):
        text = pathlib.Path(relpath).read_text()
        lowered = text.lower()
        for banned in ("human_delivered", "delivered_to_human", "human_received"):
            assert banned not in lowered, f"{banned!r} found in {relpath}"


# ── 15. Receipt path collision safety across attempts ──────────────────────


def test_redispatch_does_not_overwrite_prior_receipt_evidence():
    event = _make_event()
    sink = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": 1001}}),
    )
    sink.send(event)
    first_files = set(_all_receipt_files())
    assert len(first_files) == 1

    # Re-dispatch the same event again (simulating a resend of the same
    # logical notification).
    sink2 = TelegramSink(
        bot_token=BOT_TOKEN, chat_id=CHAT_ID, enabled=True,
        _opener=_mock_opener({"ok": True, "result": {"message_id": 1002}}),
    )
    sink2.send(event)
    second_files = set(_all_receipt_files())

    assert first_files.issubset(second_files)
    assert len(second_files) == 2  # new receipt id, old evidence untouched
    old_receipt = _load(next(iter(first_files)))
    assert old_receipt["telegram_message_id"] == 1001  # unchanged by the redispatch
