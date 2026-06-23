"""Tests for artifact metadata consistency validator (Phase 79E)."""
from __future__ import annotations

import json

from pcae.artifact_metadata import validate_artifact_metadata

REAL_SHA = "1cb1f79314496bb014908fb8f1644267bcf43f70090e1e6d0924d9444ca39f57"
OTHER_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_exact_metadata_match_passes():
    r = validate_artifact_metadata(
        path="docs/REAL_CAPTURED_TASKS.md",
        expected_size=26621, actual_size=26621,
        expected_line_count=695, actual_line_count=695,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
    )
    assert r.status == "consistent"
    assert r.outcome == "valid"
    assert r.authoritative_sha_match
    assert not r.blockers


def test_full_sha_mismatch_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_sha256=REAL_SHA, actual_sha256=OTHER_SHA,
    )
    assert r.status == "sha_mismatch"
    assert r.outcome == "blocked"
    assert len(r.blockers) > 0


def test_short_sha_prefix_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_sha256=REAL_SHA[:16], actual_sha256=REAL_SHA[:16],
    )
    assert r.status == "short_sha_only"
    assert r.outcome == "blocked"
    assert r.short_sha_only


def test_missing_sha256_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_sha256="", actual_sha256=REAL_SHA,
    )
    assert r.status == "missing_authoritative_sha"
    assert r.outcome == "blocked"


def test_path_mismatch_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_path="docs/X.md", actual_path="docs/Y.md",
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
    )
    assert r.status == "path_mismatch"
    assert r.outcome == "blocked"
    assert not r.path_match


def test_missing_file_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
        file_exists=False,
    )
    assert r.status == "missing_file"
    assert r.outcome == "blocked"


def test_size_mismatch_with_sha_mismatch_blocks():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_size=100, actual_size=200,
        expected_sha256=REAL_SHA, actual_sha256=OTHER_SHA,
    )
    assert r.outcome == "blocked"


def test_size_mismatch_with_sha_match_advisory():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_size=26373, actual_size=26621,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
        strict=False,
    )
    assert r.status == "warning_consistent_sha"
    assert r.outcome == "valid_with_warnings"
    assert r.authoritative_sha_match
    assert not r.size_match
    assert len(r.advisory_mismatches) > 0


def test_line_count_mismatch_advisory():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_line_count=690, actual_line_count=695,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
        strict=False,
    )
    assert r.outcome == "valid_with_warnings"
    assert not r.line_count_match
    assert len(r.warnings) > 0


def test_strict_mode_blocks_size_mismatch():
    r = validate_artifact_metadata(
        path="docs/X.md",
        expected_size=100, actual_size=200,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
        strict=True,
    )
    assert r.outcome == "blocked"
    assert len(r.blockers) > 0


def test_json_output_serializable():
    r = validate_artifact_metadata(
        path="docs/REAL_CAPTURED_TASKS.md",
        expected_size=26621, actual_size=26621,
        expected_line_count=695, actual_line_count=695,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
    )
    d = r.to_dict()
    s = json.dumps(d)
    assert isinstance(s, str)
    assert d["artifact_metadata_status"] == "consistent"


def test_real_file_metadata_representation():
    """Validate known metadata without reading live file."""
    r = validate_artifact_metadata(
        path="docs/REAL_CAPTURED_TASKS.md",
        expected_path="docs/REAL_CAPTURED_TASKS.md",
        actual_path="docs/REAL_CAPTURED_TASKS.md",
        expected_size=26621, actual_size=26621,
        expected_line_count=695, actual_line_count=695,
        expected_sha256=REAL_SHA, actual_sha256=REAL_SHA,
    )
    assert r.status == "consistent"
    assert r.outcome == "valid"
    assert r.path_match
    assert r.size_match
    assert r.line_count_match
    assert r.authoritative_sha_match
