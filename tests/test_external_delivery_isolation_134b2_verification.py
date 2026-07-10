"""Phase 134B.2 — independent adversarial verification of the 134B.1 external
notification isolation repair.

These tests do not repeat 134B.1's own regression file. They probe the
architectural question 134B.1 did not ask: is isolation enforced at a shared,
transport-independent external-delivery authorization boundary, or does it
merely happen to cover the one channel-specific environment-variable list a
human enumerated by hand?

No test in this file performs real network I/O. Where a probe must show that
a code path *would* reach a transport call, it patches ``urllib.request.
urlopen`` to a recording fake first.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pcae.core.notifications import (
    NotificationSink,
    NotificationResult,
    dispatch,
    make_notification_event,
    EVENT_TYPE_MANUAL_TEST,
    TelegramSink,
)
from pcae.core.phase_reports import (
    make_phase_report,
    write_phase_report,
    read_notification_dispatch_marker,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _no_network_opener():
    """A urlopen replacement that must never be reachable from these tests
    unless a probe is deliberately proving a bypass exists. Raising loudly
    beats a silent successful mock: if this is ever hit unexpectedly, the
    test fails instead of pretending delivery succeeded.
    """
    def opener(req):  # pragma: no cover - only invoked on genuine bypass
        raise AssertionError(
            "REAL TRANSPORT REACHED: a probe invoked the network opener. "
            "This indicates an isolation bypass, not a false positive."
        )
    return opener


# ─────────────────────────────────────────────────────────────────────────────
# Probe 1 — generic (non-Telegram) synthetic external adapter
# ─────────────────────────────────────────────────────────────────────────────


class _FutureChannelSink:
    """A synthetic stand-in for a delivery adapter that does not exist yet
    (e.g. Slack/email/Discord/webhook). Reads its own, made-up environment
    variable names -- not any name 134B.1's sanitizer enumerates -- and
    records whether it was ever asked to send. Performs no network I/O.
    """

    ENV_ENABLED = "PCAE_FUTURECHANNEL_ENABLED"
    ENV_TARGET = "PCAE_FUTURECHANNEL_TARGET"

    def __init__(self):
        self.sent: list[str] = []

    def is_enabled(self) -> bool:
        return os.environ.get(self.ENV_ENABLED, "").lower() in ("1", "true", "yes")

    def send(self, event) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                sink_name="futurechannel", success=False,
                message="disabled", event_id=event.event_id, error="disabled",
            )
        self.sent.append(event.event_id)
        return NotificationResult(
            sink_name="futurechannel", success=True,
            message="sent", event_id=event.event_id,
        )


def test_sanitizer_allowlist_is_enumerated_by_name_not_by_concept(monkeypatch):
    """134B.1's isolation list is five literal environment-variable names.

    A hypothetical future channel's env vars are not, and structurally
    cannot be, present in that list -- proving the boundary is a per-name
    enumeration rather than a generic 'external delivery' concept. This is
    the direct architectural counter-evidence to 134B.1's claim of
    channel-agnostic compatibility.
    """
    from conftest import _EXTERNAL_NOTIFICATION_ENV

    assert _FutureChannelSink.ENV_ENABLED not in _EXTERNAL_NOTIFICATION_ENV
    assert _FutureChannelSink.ENV_TARGET not in _EXTERNAL_NOTIFICATION_ENV

    # Demonstrate the practical consequence: even inside an isolated test,
    # setting the future channel's own env var is untouched by the fixture.
    monkeypatch.setenv(_FutureChannelSink.ENV_ENABLED, "1")
    assert os.environ.get(_FutureChannelSink.ENV_ENABLED) == "1"


def test_future_adapter_is_blocked_by_dispatch_without_any_new_code(monkeypatch):
    """Phase 134B.2 repair verification: `dispatch()` now fail-closes any
    sink that is not on its known local/no-network allowlist, unless
    PCAE_NOTIFY_ENABLED is truthy -- so a brand-new adapter class dispatch()
    has never seen before (this test defines one inline) is protected
    automatically, without touching conftest.py's sanitizer or writing any
    adapter-specific code.
    """
    monkeypatch.setenv(_FutureChannelSink.ENV_ENABLED, "1")
    sink = _FutureChannelSink()
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST, title="t", message="m",
    )

    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    results = dispatch(event, [sink])
    assert results[0].success is False
    assert results[0].error == "external_delivery_not_authorized"
    assert sink.sent == [], "the future adapter's send() must not have been reached"

    # With the master switch explicitly authorized, delivery proceeds --
    # proving the gate is a real switch, not a permanent block.
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    results2 = dispatch(event, [sink])
    assert results2[0].success is True
    assert sink.sent == [event.event_id]


# ─────────────────────────────────────────────────────────────────────────────
# Probe 2 — future-adapter registration through the real extension point
# ─────────────────────────────────────────────────────────────────────────────


def test_real_sink_construction_is_a_hardcoded_name_chain():
    """The real sink-construction site (phase_reports.finalize_phase_report)
    is an if/elif chain keyed on literal sink names, not an adapter
    registry. Confirmed by source inspection: this test pins that fact so
    a future refactor cannot silently reintroduce the same shape without
    the test noticing the source no longer matches.
    """
    import inspect
    from pcae.core import phase_reports

    src = inspect.getsource(phase_reports.finalize_phase_report)
    assert 'name == "telegram"' in src
    assert 'name == "filesystem"' in src
    # No adapter-registry / plugin lookup exists on this path.
    assert "adapter_registry" not in src
    assert "ADAPTER_REGISTRY" not in src


# ─────────────────────────────────────────────────────────────────────────────
# Probe 3 — direct concrete-adapter bypass of the "shared" master switch
# ─────────────────────────────────────────────────────────────────────────────


def test_notify_send_report_now_honors_the_master_notify_switch(monkeypatch, tmp_path):
    """Phase 134B.2 finding (BLOCKING, repaired): `pcae notify send-report`
    (commands.notifications.run_notify_send_report) constructs
    ``TelegramSink()`` and calls ``dispatch()`` directly. Before this phase
    it never read ``PCAE_NOTIFY_ENABLED``/``PCAE_NOTIFY_SINKS`` -- the
    master switch ``finalize_phase_report()`` uses -- at all, and was
    protected under ordinary tests only because TelegramSink's own three
    env-var names happened to be in 134B.1's literal sanitizer list, not
    because of any shared authorization boundary.

    ``dispatch()`` now enforces the master switch itself (see
    ``_requires_external_delivery_authorization`` in
    ``pcae.core.notifications``), so this call site is protected even when
    live-looking Telegram credentials are introduced through a mechanism
    the sanitizer never anticipated (Core Question 6/12) and
    ``PCAE_NOTIFY_ENABLED`` is left OFF the entire time.
    """
    import pcae.commands.notifications as notify_cmd

    captured: dict[str, object] = {}

    def fake_opener(req):
        captured["called"] = True
        captured["url"] = req.full_url
        resp = MagicMock()
        resp.read.return_value = json.dumps({"ok": True, "result": {}}).encode()
        resp.__enter__ = lambda self=resp: self
        resp.__exit__ = lambda self, *a: False
        return resp

    monkeypatch.setattr("urllib.request.urlopen", fake_opener)

    # Simulate credentials arriving through a channel the sanitizer never
    # anticipated (e.g. a config-file loader, a later fixture, a wrapper
    # script) -- deliberately NOT going through the isolation fixture's
    # env-deletion path, and deliberately leaving PCAE_NOTIFY_ENABLED unset.
    monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "fake-chat")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    monkeypatch.delenv("PCAE_NOTIFY_SINKS", raising=False)

    # The finalization gate's own strictness is out of scope for this
    # probe (it is unrelated to the external-delivery authorization
    # question) -- bypass it deliberately so the probe isolates exactly
    # one variable: does the master PCAE_NOTIFY_ENABLED switch matter here.
    monkeypatch.setattr(
        "pcae.core.phase_reports.validate_finalization_gate",
        lambda **kwargs: {"finalizable": True, "blockers": []},
    )

    reports_dir = tmp_path / "reports"
    report = make_phase_report(
        phase_id="134B2-PROBE", phase_name="Probe", status="completed",
        summary="synthetic probe report, not a real phase",
    )
    write_phase_report(report, reports_dir)

    marker_path = tmp_path / ".last-notified.json"
    monkeypatch.setattr(
        "pcae.core.phase_reports._NOTIFICATION_MARKER_PATH", marker_path,
    )

    args = MagicMock()
    args.reports_dir = str(reports_dir)
    args.json = False

    notify_cmd.run_notify_send_report(args)

    assert captured.get("called") is None, (
        "REGRESSION: run_notify_send_report reached the real Telegram "
        "transport call while PCAE_NOTIFY_ENABLED was unset -- the "
        "dispatch()-level authorization gate must block this."
    )


def test_finalize_phase_report_path_correctly_honors_master_switch(monkeypatch, tmp_path):
    """Control probe: the OTHER real call site (finalize_phase_report) does
    honor PCAE_NOTIFY_ENABLED before sink construction. Included so the
    contrast with the probe above is a verified fact, not an assumption.
    """
    from pcae.core.phase_reports import finalize_phase_report

    monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "fake-chat")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

    called = {"opener": False}

    def fake_opener(req):
        called["opener"] = True
        raise AssertionError("must not be reached when PCAE_NOTIFY_ENABLED is unset")

    monkeypatch.setattr("urllib.request.urlopen", fake_opener)

    result = finalize_phase_report(
        phase_id="134B2-CTRL", phase_name="Control", status="completed",
        summary="control probe", reports_dir=tmp_path / "reports",
    )
    assert result["notification_skipped"] is True
    assert called["opener"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Probe 4 — message vs document delivery share one gate (within TelegramSink)
# ─────────────────────────────────────────────────────────────────────────────


def test_message_and_document_delivery_share_a_single_enabled_check(monkeypatch):
    """Within TelegramSink itself (today's only real adapter), both the
    sendMessage summary and the sendDocument attachment are gated by the
    same ``is_enabled()`` call inside one ``send()`` invocation -- there is
    no separate, independently-bypassable path for the document leg.
    """
    sink = TelegramSink(bot_token="", chat_id="", enabled=True)
    assert sink.is_configured() is False
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST, title="t", message="m",
        artifact_paths=["some/file.md"],
    )

    def fail_opener(req):
        raise AssertionError("no network call should occur when unconfigured")

    monkeypatch.setattr("urllib.request.urlopen", fail_opener)
    result = sink.send(event)
    assert result.success is False
    assert result.error == "disabled_or_unconfigured"


# ─────────────────────────────────────────────────────────────────────────────
# Probe 5 — retry / fallback path
# ─────────────────────────────────────────────────────────────────────────────


def test_no_retry_loop_exists_to_escape_isolation():
    """134B.1 reported no automatic retry loop in TelegramSink.send(). Pin
    that as a structural fact: no retry/backoff call wraps _send_message or
    _send_document_bytes, so isolation cannot be defeated by a later retry
    attempt happening outside the original isolated context.
    """
    import inspect
    src = inspect.getsource(TelegramSink.send)
    assert "retry" not in src.lower()
    assert "for attempt in" not in src


# ─────────────────────────────────────────────────────────────────────────────
# Probe 6 — subprocess probe with an unanticipated adapter env var present
# ─────────────────────────────────────────────────────────────────────────────


def test_subprocess_env_construction_strips_known_names_only():
    """Extends 134B.1's own subprocess probe at the source of truth: the
    exact ``isolate_external_notification_env()`` function a subprocess
    helper would need to call before constructing a child environment.
    Feed it a dict simulating production config (all five known live-
    delivery variables) plus a synthetic future-adapter variable. The five
    known variables are correctly stripped (134B.1's fix works); the
    unknown one passes through untouched -- the boundary's protection is
    exactly as wide as its literal name list and no wider.
    """
    from conftest import isolate_external_notification_env, _EXTERNAL_NOTIFICATION_ENV

    env = {key: f"live-{key}" for key in _EXTERNAL_NOTIFICATION_ENV}
    env[_FutureChannelSink.ENV_ENABLED] = "1"

    isolate_external_notification_env(env)

    assert all(key not in env for key in _EXTERNAL_NOTIFICATION_ENV)
    assert env.get(_FutureChannelSink.ENV_ENABLED) == "1", (
        "an unenumerated future-adapter variable passes straight through the "
        "isolation boundary unchanged -- the boundary is name-specific, not "
        "concept-generic"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Probe 7 — import/cache probe
# ─────────────────────────────────────────────────────────────────────────────


def test_telegram_sink_reads_environment_at_construction_not_import(monkeypatch):
    """TelegramSink resolves token/chat/enabled from os.environ inside
    __init__, not at module import time and not cached on the class -- so
    the isolation fixture's per-test env changes always take effect for a
    freshly constructed sink, and no earlier test's live values can leak in
    through a cached instance or class attribute.
    """
    monkeypatch.delenv("PCAE_TELEGRAM_ENABLED", raising=False)
    monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)
    sink_a = TelegramSink()
    assert sink_a.is_enabled() is False

    monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "c")
    sink_b = TelegramSink()
    assert sink_b.is_enabled() is True
    # sink_a, constructed earlier, is unaffected by the later env change.
    assert sink_a.is_enabled() is False


# ─────────────────────────────────────────────────────────────────────────────
# Probe 9 — synthetic lifecycle classification: marker pollution
# ─────────────────────────────────────────────────────────────────────────────


def test_synthetic_send_report_cannot_write_the_real_dispatch_marker(monkeypatch, tmp_path):
    """`pcae notify send-report` writes the notification-dispatch idempotency
    marker on success using a hardcoded default path
    (``.pcae/phase-reports/.last-notified.json``) rather than a path
    derived from ``--reports-dir``. If a synthetic/test invocation of this
    command ever produced success=True while cwd is the real repository,
    it would durably mark a synthetic phase id as genuinely notified in
    real governance state. Today this cannot happen only because
    TelegramSink.is_enabled() is False in isolated tests -- prove that
    marker pollution does NOT occur even when the same fake-opener/fake-
    credential conditions from Probe 3 are combined with a real-looking
    success response.
    """
    import pcae.commands.notifications as notify_cmd

    def fake_opener(req):
        resp = MagicMock()
        resp.read.return_value = json.dumps({"ok": True, "result": {}}).encode()
        resp.__enter__ = lambda self=resp: self
        resp.__exit__ = lambda self, *a: False
        return resp

    monkeypatch.setattr("urllib.request.urlopen", fake_opener)
    monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")
    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "fake-chat")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    monkeypatch.setattr(
        "pcae.core.phase_reports.validate_finalization_gate",
        lambda **kwargs: {"finalizable": True, "blockers": []},
    )

    marker_path = tmp_path / ".last-notified.json"
    monkeypatch.setattr(
        "pcae.core.phase_reports._NOTIFICATION_MARKER_PATH", marker_path,
    )

    reports_dir = tmp_path / "reports"
    report = make_phase_report(
        phase_id="134B2-MARKER-PROBE", phase_name="Marker probe",
        status="completed", summary="synthetic",
    )
    write_phase_report(report, reports_dir)

    args = MagicMock()
    args.reports_dir = str(reports_dir)
    args.json = False
    notify_cmd.run_notify_send_report(args)

    marker = read_notification_dispatch_marker(marker_path)
    assert marker.get("phase_id") != "134B2-MARKER-PROBE" or not marker, (
        "a synthetic send-report invocation must not write a real "
        "phase-completion dispatch marker"
    )
