"""Tests for hook-bypass policy formalization (Phase 79D)."""
from __future__ import annotations

import json

from pcae.hook_bypass import evaluate_hook_bypass


def test_no_bypass_is_allowed():
    r = evaluate_hook_bypass(bypass_detected=False)
    assert r.status == "no_bypass_detected"
    assert r.outcome == "allowed"
    assert not r.bypass_detected
    assert not r.blockers


def test_documented_bounded_exception_allowed():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="Adoption commit requires --no-verify",
        expected_commit_message="Adopt backend-created docs",
        actual_commit_message="Adopt backend-created docs",
        allowed_files=["docs/REAL_CAPTURED_TASKS.md"],
        actual_files=["docs/REAL_CAPTURED_TASKS.md"],
    )
    assert r.status == "documented_bounded_exception"
    assert r.outcome == "allowed"
    assert not r.blockers


def test_undocumented_bypass_blocks():
    r = evaluate_hook_bypass(bypass_detected=True, bypass_documented=False)
    assert r.status == "undocumented_bypass"
    assert r.outcome == "blocked"
    assert len(r.blockers) > 0


def test_broad_allowed_file_pattern_blocks():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="broad",
        allowed_files=["*"],
        actual_files=["anything.py"],
    )
    assert r.status == "broad_scope_bypass"
    assert r.outcome == "blocked"
    assert r.broad_scope_detected


def test_unexpected_commit_message_blocks():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="adoption",
        expected_commit_message="Adopt docs",
        actual_commit_message="Random commit",
        allowed_files=["docs/REAL_CAPTURED_TASKS.md"],
        actual_files=["docs/REAL_CAPTURED_TASKS.md"],
    )
    assert r.status == "unexpected_commit_message"
    assert r.outcome == "blocked"


def test_unexpected_files_block():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="adoption",
        expected_commit_message="Adopt",
        actual_commit_message="Adopt",
        allowed_files=["docs/REAL_CAPTURED_TASKS.md"],
        actual_files=["docs/REAL_CAPTURED_TASKS.md", "src/evil.py"],
    )
    assert r.status == "unexpected_files"
    assert r.outcome == "blocked"
    assert "src/evil.py" in r.unexpected_files


def test_normalized_bypass_blocks():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        hook_bypass_normalized=True,
    )
    assert r.status == "normalized_bypass"
    assert r.outcome == "blocked"
    assert r.hook_bypass_normalized


def test_force_push_with_bypass_blocks():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="adoption",
        expected_commit_message="Adopt",
        actual_commit_message="Adopt",
        allowed_files=["docs/X.md"],
        actual_files=["docs/X.md"],
        force_push_performed=True,
    )
    assert r.outcome == "blocked"
    assert r.force_push_performed


def test_policy_output_is_json_serializable():
    r = evaluate_hook_bypass(
        bypass_detected=True,
        bypass_documented=True,
        bypass_reason="test",
        expected_commit_message="msg",
        actual_commit_message="msg",
        allowed_files=["f.md"],
        actual_files=["f.md"],
    )
    d = r.to_dict()
    s = json.dumps(d)
    assert isinstance(s, str)
    assert d["hook_bypass_policy_status"] == "documented_bounded_exception"
