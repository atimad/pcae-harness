"""Phase 149O.16.1: Publication Coordinator Python 3.9/3.10 Timestamp
Compatibility Repair (149O.12B-Obs-PY39-1).

Exercises the real, unpatched production
`pcae.governance.publication.coordinator._parse_timestamp` -- no
monkeypatch -- to confirm a trailing UTC "Z" is now normalized before
`datetime.fromisoformat` the same way
`pcae.core.rollback_approval_evidence._parse_iso_timestamp` already
does, restoring Python 3.9/3.10 lexical compatibility without changing
the parsed instant, existing "+00:00"/offset behavior, fractional
seconds, or invalid-input rejection.
"""
from __future__ import annotations

import inspect
from datetime import timezone
from pathlib import Path

import pytest

from pcae.governance.publication.coordinator import (
    PublicationCoordinator,
    _parse_timestamp,
)
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

pytestmark = pytest.mark.fast_green

_PREVIEW_DIGEST = "a" * 64


# ═══════════════════════════════════════════════════════════════════════
# Direct parser tests (real production function, no monkeypatch)
# ═══════════════════════════════════════════════════════════════════════


def test_terminal_z_suffix_now_accepted():
    parsed = _parse_timestamp("2026-08-08T12:34:56Z")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_z_and_explicit_offset_produce_identical_instant():
    from_z = _parse_timestamp("2026-08-08T12:34:56Z")
    from_offset = _parse_timestamp("2026-08-08T12:34:56+00:00")
    assert from_z == from_offset


def test_existing_plus_offset_input_unchanged():
    parsed = _parse_timestamp("2026-08-08T12:34:56+00:00")
    assert parsed.isoformat() == "2026-08-08T12:34:56+00:00"


def test_fractional_seconds_with_z_suffix_accepted():
    parsed = _parse_timestamp("2026-08-08T12:34:56.123Z")
    assert parsed.microsecond == 123000
    assert parsed.utcoffset().total_seconds() == 0


def test_non_utc_offset_input_unchanged():
    parsed = _parse_timestamp("2026-08-08T14:34:56+02:00")
    assert parsed.utcoffset().total_seconds() == 2 * 3600
    # Same instant as the equivalent UTC "Z" timestamp, not converted.
    assert parsed.astimezone(timezone.utc) == _parse_timestamp("2026-08-08T12:34:56Z")


def test_lowercase_z_still_rejected():
    # Only the canonical uppercase "Z" designator is normalized; existing
    # domain semantics for other malformed input are preserved.
    with pytest.raises(ValueError):
        _parse_timestamp("2026-08-08T12:34:56z")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-a-timestamp",
        "2026-08-08T12:34:56+00:00Z",  # double timezone suffix
        "2026-13-40T99:99:99Z",  # malformed date/time components
    ],
)
def test_invalid_inputs_remain_invalid(value):
    with pytest.raises(ValueError):
        _parse_timestamp(value)


def test_production_diff_is_terminal_z_normalization_only():
    source = inspect.getsource(_parse_timestamp)
    assert 'value.endswith("Z")' in source
    assert '[:-1] + "+00:00"' in source


# ═══════════════════════════════════════════════════════════════════════
# Real CHGR Decision / RAE Binding creation path (no monkeypatch)
# ═══════════════════════════════════════════════════════════════════════


def _z_suffixed_package(tmp_path: Path, built_at: str) -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id="pkg-149o-16-1",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest=_PREVIEW_DIGEST,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=built_at,
        decision_subject="subject-1",
        template_id="template-1",
        template_version="1.0",
        selected_option_id="option-a",
        rationale_text="Because the data supports it.",
        conditions_text=None,
        options_presented=("option-a", "option-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": built_at,
        },
        preview_rendered_content="Confirm selection: option-a",
        confirmation_statement="Accepted",
        confirmation_timestamp=built_at,
    )


def test_chgr_publication_with_z_suffixed_timestamps_succeeds(tmp_path):
    coordinator = PublicationCoordinator(store=PublicationRecordStore(root=tmp_path / "pub-exec"))
    package = _z_suffixed_package(tmp_path, built_at="2026-08-08T10:00:00Z")
    event = coordinator.authorize(
        operator_id="alice",
        package_id=package.package_id,
        invoked_at="2026-08-08T11:00:00Z",
    )
    result = coordinator.execute(package, event)
    assert result.success
