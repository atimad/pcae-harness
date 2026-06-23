"""Artifact metadata consistency validator (Phase 79E).

Validates file metadata (path, size, line count, SHA256) for governance
artifact consistency. Full SHA256 is authoritative; short prefixes are
insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactMetadataResult:
    status: str
    outcome: str
    path: str
    expected_path: str
    actual_path: str
    expected_size: int | None
    actual_size: int | None
    expected_line_count: int | None
    actual_line_count: int | None
    expected_sha256: str
    actual_sha256: str
    authoritative_sha_match: bool
    short_sha_only: bool
    size_match: bool
    line_count_match: bool
    path_match: bool
    strict: bool
    advisory_mismatches: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "actual_line_count": self.actual_line_count,
            "actual_path": self.actual_path,
            "actual_sha256": self.actual_sha256,
            "actual_size": self.actual_size,
            "advisory_mismatches": list(self.advisory_mismatches),
            "artifact_metadata_outcome": self.outcome,
            "artifact_metadata_status": self.status,
            "authoritative_sha_match": self.authoritative_sha_match,
            "blockers": list(self.blockers),
            "expected_line_count": self.expected_line_count,
            "expected_path": self.expected_path,
            "expected_sha256": self.expected_sha256,
            "expected_size": self.expected_size,
            "line_count_match": self.line_count_match,
            "path": self.path,
            "path_match": self.path_match,
            "short_sha_only": self.short_sha_only,
            "size_match": self.size_match,
            "strict": self.strict,
            "warnings": list(self.warnings),
        }


def validate_artifact_metadata(
    path: str,
    expected_path: str = "",
    actual_path: str = "",
    expected_size: int | None = None,
    actual_size: int | None = None,
    expected_line_count: int | None = None,
    actual_line_count: int | None = None,
    expected_sha256: str = "",
    actual_sha256: str = "",
    file_exists: bool = True,
    strict: bool = True,
) -> ArtifactMetadataResult:
    bl: list[str] = []
    wl: list[str] = []
    advisory: list[str] = []

    ep = expected_path or path
    ap = actual_path or path

    if not file_exists:
        bl.append(f"File does not exist: {ap}")
        return _result("missing_file", "blocked", path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        False, False, False, False, False,
                        strict, (), tuple(bl), ())

    path_ok = ep == ap
    if not path_ok:
        bl.append(f"Path mismatch: expected '{ep}', got '{ap}'.")
        return _result("path_mismatch", "blocked", path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        False, False, False, False, path_ok,
                        strict, (), tuple(bl), ())

    # SHA256 checks
    short_sha_only = False
    sha_match = False

    if not expected_sha256:
        bl.append("Missing authoritative SHA256.")
        return _result("missing_authoritative_sha", "blocked", path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        False, False, False, False, path_ok,
                        strict, (), tuple(bl), ())

    if len(expected_sha256) < 64 or len(actual_sha256) < 64:
        short_sha_only = True
        bl.append("Short SHA prefix only; full SHA256 required for authoritative match.")
        return _result("short_sha_only", "blocked", path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        False, True, False, False, path_ok,
                        strict, (), tuple(bl), ())

    sha_match = expected_sha256 == actual_sha256
    if not sha_match:
        bl.append(f"SHA256 mismatch: expected {expected_sha256[:16]}..., got {actual_sha256[:16]}...")
        return _result("sha_mismatch", "blocked", path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        False, False, False, False, path_ok,
                        strict, (), tuple(bl), ())

    # Size check
    size_ok = True
    if expected_size is not None and actual_size is not None:
        size_ok = expected_size == actual_size
        if not size_ok:
            msg = f"Size mismatch: expected {expected_size}, got {actual_size}."
            if strict:
                bl.append(msg)
            else:
                advisory.append(msg)
                wl.append(msg)

    # Line count check
    lc_ok = True
    if expected_line_count is not None and actual_line_count is not None:
        lc_ok = expected_line_count == actual_line_count
        if not lc_ok:
            msg = f"Line count mismatch: expected {expected_line_count}, got {actual_line_count}."
            if strict:
                bl.append(msg)
            else:
                advisory.append(msg)
                wl.append(msg)

    if bl:
        return _result("blocking" if strict else "warning_consistent_sha",
                        "blocked" if strict else "valid_with_warnings",
                        path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        sha_match, False, size_ok, lc_ok, path_ok,
                        strict, tuple(advisory), tuple(bl), tuple(wl))

    if advisory:
        return _result("warning_consistent_sha", "valid_with_warnings",
                        path, ep, ap,
                        expected_size, actual_size,
                        expected_line_count, actual_line_count,
                        expected_sha256, actual_sha256,
                        sha_match, False, size_ok, lc_ok, path_ok,
                        strict, tuple(advisory), (), tuple(wl))

    return _result("consistent", "valid", path, ep, ap,
                    expected_size, actual_size,
                    expected_line_count, actual_line_count,
                    expected_sha256, actual_sha256,
                    True, False, size_ok, lc_ok, path_ok,
                    strict, (), (), ())


def _result(
    status, outcome, path, ep, ap, es, az, elc, alc,
    esha, asha, sha_match, short_sha, size_ok, lc_ok, path_ok,
    strict, advisory, bl, wl,
) -> ArtifactMetadataResult:
    return ArtifactMetadataResult(
        status=status, outcome=outcome, path=path,
        expected_path=ep, actual_path=ap,
        expected_size=es, actual_size=az,
        expected_line_count=elc, actual_line_count=alc,
        expected_sha256=esha, actual_sha256=asha,
        authoritative_sha_match=sha_match, short_sha_only=short_sha,
        size_match=size_ok, line_count_match=lc_ok, path_match=path_ok,
        strict=strict, advisory_mismatches=advisory,
        blockers=bl, warnings=wl,
    )
