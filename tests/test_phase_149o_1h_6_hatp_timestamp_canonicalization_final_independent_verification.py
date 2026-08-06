"""Phase 149O.1H.6 -- HATP Timestamp Canonicalization Final Independent
Verification (verification-only; no production change).

Independently re-derives, rather than trusts, 149O.1H.5's claim that
`_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\\d{2})[.,](\\d+)")` closes
the effective bypass surface of the raw-lexical fractional-precision
guard (Stage 1) that runs before `datetime.fromisoformat` (Stage 2) ever
lossily truncates sub-microsecond precision.

This suite:

  * independently reproduces, against an isolated pre-149O.1H.5 import
    of commit 3d6b5a9a, both the historical non-colon-offset bypass
    (B-149O.1H.4-1) and the historical decimal-comma bypass -- neither
    is trusted from the 149O.1H.5 report without being re-derived here;
  * independently probes this runtime's `datetime.fromisoformat` offset
    and separator grammar rather than copying 149O.1H.5's matrix;
  * attacks the new regex's generic `(?<=:\\d{2})` seconds-field anchor
    for offset-seconds / offset-fraction ambiguity -- specifically
    whether `re.search`'s leftmost-match semantics could let an
    offset-seconds fraction (e.g. `+00:00:00.1234567`) hide an invalid
    main-timestamp fraction, or a valid main fraction get misclassified
    by an offset fraction that follows it;
  * sweeps fraction length 0..50 across every runtime-supported suffix
    for both `.` and `,` separators;
  * attacks malformed/near-valid forms (multi-dot, mixed separators,
    exponent, signed fraction, naive, lowercase `z`, whitespace);
  * re-verifies parser/constructor equivalence, closed-schema/duplicate-
    key/AG3-AG5 discrimination (B-149O.1H-2), and independently
    recomputes an AG3 golden vector + SHA-256 digest without calling the
    production canonicalizer.

Does not modify `src/pcae/core/human_approval_trusted_provenance.py` or
any `docs/contracts/**` file. Does not implement Wave 4, signature
verification, attestation verification, trusted-signer resolution,
human-presence verification, or any FIDO2/PIV provider.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
    MalformedProofError,
    RollbackSite,
    _FRACTIONAL_SECONDS_RE,
    canonicalize_hatp_proof_payload,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
    parse_hatp_proof,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Exact 149O.1H.5 production repair boundary (independently confirmed
# below by `test_exact_149o_1h_5_production_boundary_reconstructed`).
PRE_149O_1H_5_COMMIT = "3d6b5a9a"
POST_149O_1H_5_COMMIT = "66fde5c3"


def _repo_id() -> str:
    return str(uuid.uuid4())


def _valid_document(family: str = "AG3", **overrides: object) -> dict:
    doc: dict = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": _repo_id(),
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": family,
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    if family == "AG3":
        doc["job_id"] = "job-1"
        doc["original_commit_sha"] = "c" * 40
    else:
        doc["per_id"] = "per-1"
        doc["ecp_id"] = "ecp-1"
    doc.update(overrides)
    return doc


def _valid_kwargs(family: str = "AG3", **overrides: object) -> dict:
    common: dict = dict(
        proof_version=1,
        principal_id="alice",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=_repo_id(),
        decision_record_id="chgr-record-1",
        decision_record_digest="a" * 64,
        binding_id="rae-binding-1",
        binding_digest="b" * 64,
        issued_at="2026-08-06T00:00:00.000Z",
    )
    if family == "AG3":
        common["rollback_site"] = RollbackSite.AG3
        common["operation_reference"] = Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    else:
        common["rollback_site"] = RollbackSite.AG5
        common["operation_reference"] = Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    common.update(overrides)
    return common


def _parse(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_valid_document(family, issued_at=issued_at)))


def _construct(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(**_valid_kwargs(family, issued_at=issued_at))


# Runtime-discovered (Section A), not assumed from documentation or
# copied from 149O.1H.5's own matrix.
DISCOVERED_SUPPORTED_SUFFIXES = [
    "Z",
    "+00:00",
    "+0000",
    "+00",
    "+01:00",
    "+0100",
    "+01",
    "-05:00",
    "-0500",
    "-05",
]


# ═══════════════════════════════════════════════════════════════════════════
# Section A -- independent runtime datetime.fromisoformat grammar probe
# (items 8, 9, 10, 29, 30). Derives the accepted grammar directly; does
# not trust 149O.1H.5's own probe results.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", DISCOVERED_SUPPORTED_SUFFIXES)
def test_runtime_grammar_probe_offset_suffix_accepted(suffix: str) -> None:
    raw = "2026-01-01T12:00:00.001" + suffix
    text = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    parsed = datetime.fromisoformat(text)
    assert parsed.microsecond == 1000


def test_runtime_grammar_probe_comma_separator_accepted() -> None:
    parsed = datetime.fromisoformat("2026-01-01T12:00:00,001+00:00")
    assert parsed.microsecond == 1000


def test_runtime_grammar_probe_space_date_time_separator_accepted() -> None:
    parsed = datetime.fromisoformat("2026-01-01 12:00:00.001+00:00")
    assert parsed.microsecond == 1000


def test_runtime_grammar_probe_offset_seconds_field_accepted() -> None:
    """`+HH:MM:SS` and compact `+HHMMSS` offset-seconds forms are
    accepted by this runtime (item 8)."""
    for raw in ("2026-01-01T12:00:00+00:00:30", "2026-01-01T12:00:00+000030"):
        parsed = datetime.fromisoformat(raw)
        assert parsed.utcoffset().total_seconds() == 30


def test_runtime_grammar_probe_offset_fractional_seconds_accepted_and_discarded() -> None:
    """`+HH:MM:SS.fff` is accepted, but any sub-second component of the
    *offset itself* is silently discarded by `datetime.fromisoformat` on
    this runtime -- it never affects `utcoffset()` (item 9)."""
    parsed_dot = datetime.fromisoformat("2026-01-01T12:00:00+00:00:00.5")
    parsed_comma = datetime.fromisoformat("2026-01-01T12:00:00+00:00:00,5")
    assert parsed_dot.utcoffset().total_seconds() == 0
    assert parsed_comma.utcoffset().total_seconds() == 0


def test_runtime_grammar_probe_lowercase_z_rejected() -> None:
    with pytest.raises(ValueError):
        datetime.fromisoformat("2026-01-01t12:00:00z")


def test_runtime_grammar_probe_naive_accepted_by_fromisoformat_but_hatp_must_reject() -> None:
    """`datetime.fromisoformat` itself accepts a naive (no-tzinfo)
    timestamp; HATP's own `_parse_iso_timestamp` must independently
    reject it regardless (item 31)."""
    assert datetime.fromisoformat("2026-01-01T12:00:00").tzinfo is None
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00")


# ═══════════════════════════════════════════════════════════════════════════
# Section B -- exact 149O.1H.5 production diff reconstruction (items 3,
# 65, 66).
# ═══════════════════════════════════════════════════════════════════════════


def test_exact_149o_1h_5_production_boundary_reconstructed() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{PRE_149O_1H_5_COMMIT}..{POST_149O_1H_5_COMMIT}", "--", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == ["src/pcae/core/human_approval_trusted_provenance.py"]


def test_149o_1h_5_diff_hunk_is_single_lexical_guard_change_only() -> None:
    """UNRELATED = 0: the only functional line changed is the
    `_FRACTIONAL_SECONDS_RE` assignment (plus its comment)."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "-U0",
            f"{PRE_149O_1H_5_COMMIT}..{POST_149O_1H_5_COMMIT}",
            "--",
            "src/pcae/core/human_approval_trusted_provenance.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    added_code_lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++") and not line.lstrip("+ ").startswith("#")
    ]
    assert added_code_lines == ['+_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\\d{2})[.,](\\d+)")']


def test_no_src_pcae_files_modified_this_phase() -> None:
    """149O.1H.6 was verification-only: at that phase's own commit time,
    this asserted the working tree carried no uncommitted change under
    `src/pcae/`. That was a live-working-tree check, not a check against
    149O.1H.6's own frozen commit range -- it is structurally unable to
    remain meaningful once any later phase (e.g. 149O.1I, which
    legitimately modifies `src/pcae/core/human_approval_trusted_provenance.py`
    and adds `src/pcae/core/hatp_providers.py`, per §7 of the 149O.1D
    plan) makes its own committed/uncommitted changes -- there is no
    retroactive way to re-scope this test to "only 149O.1H.6's own diff"
    without a base-commit reference this test never recorded. Retired to
    a documented no-op rather than deleted, preserving discoverability of
    what this test used to verify (§54 of the governing prompt: report
    findings, do not silently delete history)."""
    pytest.skip(
        "149O.1H.6-era live-working-tree invariant; structurally "
        "unrenewable after any later phase's own src/pcae/ changes "
        "(retired 149O.1I, non-blocking -- see docstring)"
    )


def test_hatp_contract_byte_unchanged_this_phase() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "docs/contracts/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# Section C -- independent historical bypass reproduction against an
# isolated importlib load of the pre-149O.1H.5 commit (items 4, 5).
# Never mutates `sys.modules` for the live production module.
# ═══════════════════════════════════════════════════════════════════════════


def _load_module_at_commit(commit: str, tmp_path: Path):
    text = subprocess.run(
        ["git", "show", f"{commit}:src/pcae/core/human_approval_trusted_provenance.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    dest = tmp_path / f"hatp_at_{commit}.py"
    dest.write_text(text)
    module_name = f"hatp_isolated_149o_1h_6_{commit}"
    spec = importlib.util.spec_from_file_location(module_name, dest)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        del sys.modules[module_name]
    return mod


@pytest.fixture(scope="module")
def pre_149o_1h_5_module(tmp_path_factory: pytest.TempPathFactory):
    return _load_module_at_commit(PRE_149O_1H_5_COMMIT, tmp_path_factory.mktemp("pre_149o_1h_5"))


def test_pre_repair_regex_never_matches_non_colon_offset(pre_149o_1h_5_module) -> None:
    """Independent re-derivation of B-149O.1H.4-1's root cause: the
    pre-149O.1H.5 regex's suffix lookahead (`Z$|[+-]\\d{2}:\\d{2}$`)
    never matches a non-colon offset, so the >6-digit guard never fires
    for it."""
    old_re = pre_149o_1h_5_module._FRACTIONAL_SECONDS_RE
    for raw in (
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000009+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00.0000009+0000",
    ):
        assert old_re.search(raw) is None


def test_pre_repair_non_colon_offset_collision_reproduced(pre_149o_1h_5_module) -> None:
    """The exact historical collision: two distinct sub-microsecond
    fractions truncate to the identical parsed datetime under the
    pre-149O.1H.5 source."""
    d1 = pre_149o_1h_5_module._parse_iso_timestamp("2026-01-01T12:00:00.0000001+00")
    d2 = pre_149o_1h_5_module._parse_iso_timestamp("2026-01-01T12:00:00.0000009+00")
    assert d1 is not None and d2 is not None
    assert d1 == d2
    assert d1.microsecond == 0


def test_pre_repair_regex_never_matches_comma_separator(pre_149o_1h_5_module) -> None:
    """Independent re-derivation of the decimal-comma bypass: the
    pre-149O.1H.5 regex is anchored on a literal `\\.`, so it never
    matches a `,`-separated fraction through any suffix, including `Z`."""
    old_re = pre_149o_1h_5_module._FRACTIONAL_SECONDS_RE
    for raw in (
        "2026-01-01T12:00:00,0000001Z",
        "2026-01-01T12:00:00,0000009Z",
        "2026-01-01T12:00:00,0000001+00:00",
        "2026-01-01T12:00:00,0000009+00:00",
    ):
        assert old_re.search(raw) is None


def test_pre_repair_comma_collision_reproduced(pre_149o_1h_5_module) -> None:
    d1 = pre_149o_1h_5_module._parse_iso_timestamp("2026-01-01T12:00:00,0000001Z")
    d2 = pre_149o_1h_5_module._parse_iso_timestamp("2026-01-01T12:00:00,0000009Z")
    assert d1 is not None and d2 is not None
    assert d1 == d2
    assert d1.microsecond == 0


# ═══════════════════════════════════════════════════════════════════════════
# Section D -- live module: both historical bypass classes now rejected,
# via parser and constructor (items 22, 23, 38).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000009+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00.0000009+0000",
        "2026-01-01T12:00:00,0000001Z",
        "2026-01-01T12:00:00,0000009Z",
        "2026-01-01T12:00:00,0000001+00:00",
        "2026-01-01T12:00:00,0000009+00:00",
    ],
)
def test_live_module_rejects_both_historical_bypass_classes_parser(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00,0000001Z",
    ],
)
def test_live_module_rejects_both_historical_bypass_classes_constructor(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section E -- multi-match / offset-fraction ambiguity attack (items 11,
# 12, 13, 27, 28). Directly attacks whether `re.search`'s first-match
# semantics could let an offset-seconds fraction hide an invalid main
# fraction, or vice versa.
# ═══════════════════════════════════════════════════════════════════════════


def test_regex_can_have_multiple_matches_in_one_accepted_string() -> None:
    """Confirms the attack surface exists at all: a single
    parser-accepted string CAN contain two `:\\d{2}[.,]\\d+` structures
    (main seconds fraction, offset-seconds fraction)."""
    raw = "2026-01-01T12:00:00.123+00:00:00.456"
    matches = _FRACTIONAL_SECONDS_RE.findall(raw)
    assert matches == ["123", "456"]


def test_regex_search_returns_leftmost_match_which_is_always_main_fraction() -> None:
    """The main timestamp's seconds field always precedes any offset
    seconds field lexically in valid ISO-8601 syntax, so `re.search`'s
    leftmost-match semantics always select the MAIN fraction first --
    this is a structural (not incidental) property, verified here
    directly against the production regex object."""
    raw = "2026-01-01T12:00:00.1234567+00:00:00.5"
    match = _FRACTIONAL_SECONDS_RE.search(raw)
    assert match is not None
    assert match.group(1) == "1234567"


def test_over_long_main_fraction_not_hidden_by_short_offset_fraction() -> None:
    """Attack: main fraction >6 digits, offset fraction <=6 digits --
    the guard must still reject on the main fraction (item 13)."""
    raw = "2026-01-01T12:00:00.1234567+00:00:00.5"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_short_main_fraction_not_corrupted_by_long_offset_fraction() -> None:
    """Reverse: main fraction <=6 digits (valid), offset fraction >6
    digits -- the guard must not spuriously reject based on the offset's
    own fraction length, and the parsed instant must reflect only the
    main fraction (item 13 reversed)."""
    raw = "2026-01-01T12:00:00.123+00:00:00.1234567"
    proof = _parse(raw)
    assert proof.issued_at == "2026-01-01T12:00:00.123Z"


def test_both_fractions_over_long_still_rejected_on_main() -> None:
    raw = "2026-01-01T12:00:00.1234567+00:00:00.1234567"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_offset_only_fraction_over_long_with_no_main_fraction_is_safely_over_rejected() -> None:
    """When the MAIN timestamp carries no fraction at all but the offset
    itself has a >6-digit fractional-seconds component, `re.search`
    matches the offset's fraction (the only one present) and the guard
    rejects. This is the safe direction (over-rejection of a
    theoretically fraction-free instant) and is explicitly a
    NON-BLOCKING observation, not a bypass -- there is no parser-
    accepted string in which a real >6-digit MAIN fraction goes
    undetected."""
    raw = "2026-01-01T12:00:00+00:00:00.12345678"
    assert datetime.fromisoformat(raw).microsecond == 0  # offset fraction is discarded by the parser
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_offset_seconds_digits_alone_never_counted_as_main_fraction() -> None:
    """`+HH:MM:SS` with no fractional component must not be
    miscounted -- there is no `.`/`,` character for the lookbehind
    anchor to match against (item 27)."""
    raw = "2026-01-01T12:00:00.123+00:00:30"
    match = _FRACTIONAL_SECONDS_RE.search(raw)
    assert match is not None
    assert match.group(1) == "123"


@pytest.mark.parametrize(
    "main_frac,offset_digits,should_reject,expected_ms",
    [
        # main >6 digits always rejects (on the main fraction itself),
        # regardless of what the offset's own fraction looks like.
        (".1111111", 1, True, None),
        (".1111111", 6, True, None),
        (".1111111", 7, True, None),
        # main <=6 digits, millisecond-aligned, must ACCEPT regardless of
        # a >6-digit offset fraction (the offset fraction is a red
        # herring the guard must not react to when a valid earlier main
        # match exists).
        (".100000", 7, False, "100"),
        (".100", 7, False, "100"),
        # main has NO fraction at all: the only `:\\d{2}[.,]\\d+` in the
        # string is the offset's -- a >6-digit offset fraction is safely
        # over-rejected (documented non-blocking direction), not a
        # bypass, since the actual instant has zero main-fraction
        # precision to lose.
        ("", 7, True, None),
    ],
)
def test_multiple_fraction_candidate_matrix(
    main_frac: str, offset_digits: int, should_reject: bool, expected_ms: str | None
) -> None:
    """Broad sweep of item 13's matrix: for every combination of
    main-fraction x offset-fraction-length, the guard's verdict must
    depend only on the MAIN fraction, when a main fraction is present."""
    raw = f"2026-01-01T12:00:00{main_frac}+00:00:00.{'1' * offset_digits}"
    if should_reject:
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)
    else:
        proof = _parse(raw)
        assert proof.issued_at == f"2026-01-01T12:00:00.{expected_ms}Z"


# ═══════════════════════════════════════════════════════════════════════════
# Section F -- suffix-independence property, re-derived directly against
# the live regex object rather than trusted from 149O.1H.5 (items 24,
# 25, 26).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", DISCOVERED_SUPPORTED_SUFFIXES + [""])
def test_fraction_digit_count_identical_across_every_suffix(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00.1234567{suffix}"
    match = _FRACTIONAL_SECONDS_RE.search(raw)
    assert match is not None
    assert len(match.group(1)) == 7


@pytest.mark.parametrize("suffix", DISCOVERED_SUPPORTED_SUFFIXES)
def test_no_fraction_form_reports_no_main_fraction_for_every_suffix(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00{suffix}"
    assert _FRACTIONAL_SECONDS_RE.search(raw) is None


@pytest.mark.parametrize(
    "suffix,should_accept_no_frac",
    [(s, True) for s in DISCOVERED_SUPPORTED_SUFFIXES],
)
def test_cartesian_suffix_matrix_guard_coverage(suffix: str, should_accept_no_frac: bool) -> None:
    """Item 24's cartesian matrix: no-fraction / 3-digit aligned /
    6-digit aligned / 6-digit non-aligned / 7-digit all-zero / 7-digit
    significant, for every discovered suffix."""
    cases = {
        "no_frac": (f"2026-01-01T12:00:00{suffix}", True),
        "ms3": (f"2026-01-01T12:00:00.123{suffix}", True),
        "ms6_aligned": (f"2026-01-01T12:00:00.123000{suffix}", True),
        "ms6_nonaligned": (f"2026-01-01T12:00:00.123456{suffix}", False),
        "sevendigit_zero": (f"2026-01-01T12:00:00.0000000{suffix}", False),
        "sevendigit_significant": (f"2026-01-01T12:00:00.1234567{suffix}", False),
    }
    for label, (raw, should_accept) in cases.items():
        if should_accept:
            _parse(raw)
        else:
            with pytest.raises(InvalidProofSchemaError):
                _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section G -- fraction-length matrix 0..50, both separators (items 16,
# 17, 18, 19, 20, 21).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("sep", [".", ","])
def test_fraction_length_0_to_6_accepted(n: int, sep: str) -> None:
    frac = sep + ("0" * n) if n else ""
    raw = f"2026-01-01T12:00:00{frac}Z"
    proof = _parse(raw)
    assert proof.issued_at == "2026-01-01T12:00:00.000Z"


@pytest.mark.parametrize("n", [7, 8, 9, 10, 12, 20, 50])
@pytest.mark.parametrize("sep", [".", ","])
def test_fraction_length_7_plus_rejected_all_zero(n: int, sep: str) -> None:
    raw = f"2026-01-01T12:00:00{sep}{'0' * n}Z"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


@pytest.mark.parametrize("n", [7, 8, 20])
@pytest.mark.parametrize("sep", [".", ","])
def test_fraction_length_7_plus_rejected_significant(n: int, sep: str) -> None:
    raw = f"2026-01-01T12:00:00{sep}{'9' * n}Z"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_original_149o_1h_pair_still_rejected() -> None:
    for raw in ("2026-01-01T12:00:00.0001Z", "2026-01-01T12:00:00.0009Z"):
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)


def test_millisecond_domain_boundary_unchanged() -> None:
    for accept in (".000000", ".001", ".0010", ".00100", ".001000", ".123", ".123000", ".999", ".999000"):
        _parse(f"2026-01-01T12:00:00{accept}Z")
    for reject in (".000001", ".000999", ".001001", ".123456", ".999999"):
        with pytest.raises(InvalidProofSchemaError):
            _parse(f"2026-01-01T12:00:00{reject}Z")


# ═══════════════════════════════════════════════════════════════════════════
# Section H -- malformed / near-valid adversarial forms (items 34-37).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.123.456Z",
        "2026-01-01T12:00:00,123,456Z",
        "2026-01-01T12:00:00.,123Z",
        "2026-01-01T12:00:00..123Z",
        "2026-01-01T12:00:00.123,456Z",
        "2026-01-01T12:00:00,123.456Z",
        "2026-01-01T12:00:00.1e3Z",
        "2026-01-01T12:00:00.+123Z",
        "2026-01-01T12:00:00.-123Z",
    ],
)
def test_malformed_near_valid_forms_rejected(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_multi_dot_attack_guard_does_not_miscount_from_first_dot_group() -> None:
    """`12:00:00.123.456Z` is ultimately rejected by the downstream
    parser, not because the guard itself miscounts; confirms the guard
    only captures the first contiguous digit run (`123`), never the
    full `123456` across the malformed second dot (item 34)."""
    match = _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.123.456Z")
    assert match is not None
    assert match.group(1) == "123"


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01t12:00:00z",
        " 2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00Z ",
        "2026-01-01T12:00:00Z\n",
    ],
)
def test_lowercase_z_and_whitespace_rejected(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section I -- accepted-domain losslessness + injectivity + same-instant
# equivalence (items 41, 42, 43, 44).
# ═══════════════════════════════════════════════════════════════════════════


def test_losslessness_guard_runs_before_lossy_parse_for_every_rejected_case() -> None:
    """Ordering proof (item 7) via source inspection: the guard call
    precedes the `datetime.fromisoformat` call in
    `_parse_iso_timestamp`'s source text."""
    import inspect

    from pcae.core import human_approval_trusted_provenance as hatp_module

    src = inspect.getsource(hatp_module._parse_iso_timestamp)
    guard_pos = src.index("_reject_excess_fractional_precision")
    parse_pos = src.index("datetime.fromisoformat")
    assert guard_pos < parse_pos


@pytest.mark.parametrize(
    "raw_variants",
    [
        [
            "2026-01-01T12:00:00.001Z",
            "2026-01-01T12:00:00.001+00:00",
            "2026-01-01T12:00:00.001+0000",
            "2026-01-01T12:00:00.001+00",
            "2026-01-01T12:00:00,001Z",
        ],
        [
            "2026-01-01T13:00:00.001+01:00",
            "2026-01-01T13:00:00.001+0100",
            "2026-01-01T13:00:00.001+01",
        ],
    ],
)
def test_same_instant_equivalent_representations_canonicalize_identically(raw_variants: list) -> None:
    canonicals = {_parse(v).issued_at for v in raw_variants}
    assert len(canonicals) == 1


def test_distinct_instants_canonicalize_distinctly_injectivity() -> None:
    seen: dict = {}
    fractions = ["000", "001", "002", "500", "999"]
    for frac in fractions:
        proof = _parse(f"2026-01-01T12:00:00.{frac}Z")
        canon = proof.issued_at
        assert canon not in seen, f"collision: {frac} and {seen.get(canon)} both -> {canon}"
        seen[canon] = frac
    assert len(seen) == len(fractions)


def test_distinct_millisecond_payload_produces_distinct_digest() -> None:
    doc1 = _valid_document(issued_at="2026-01-01T12:00:00.001Z")
    doc2 = _valid_document(**{**doc1, "issued_at": "2026-01-01T12:00:00.002Z", "repository_id": doc1["repository_id"]})
    proof1 = parse_hatp_proof(json.dumps(doc1))
    proof2 = parse_hatp_proof(json.dumps(doc2))
    assert digest_hatp_proof_payload(proof1) != digest_hatp_proof_payload(proof2)


# ═══════════════════════════════════════════════════════════════════════════
# Section J -- parser/constructor equivalence over the newly-probed
# forms (items 38).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.123+00",
        "2026-01-01T12:00:00.123+0000",
        "2026-01-01T12:00:00,123Z",
        "2026-01-01T13:00:00.123+01",
    ],
)
def test_parser_constructor_equivalence_accept(raw: str) -> None:
    parsed = _parse(raw)
    constructed = _construct(raw)
    assert parsed.issued_at == constructed.issued_at


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.1234567+00",
        "2026-01-01T12:00:00,1234567Z",
        "2026-01-01T12:00:00",
        "2026-01-01T12:00:00.123456Z",
    ],
)
def test_parser_constructor_equivalence_reject(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)
    with pytest.raises(InvalidProofSchemaError):
        _construct(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section K -- B-149O.1H-2 regression: constructor hardening, closed
# schema, duplicate keys, AG3/AG5 discrimination (items 39, 40, 45, 46,
# 47).
# ═══════════════════════════════════════════════════════════════════════════


def test_constructor_rejects_bool_proof_version() -> None:
    with pytest.raises((InvalidProofSchemaError, Exception)):
        HumanApprovalProvenanceProof(**_valid_kwargs(proof_version=True))


def test_constructor_rejects_invalid_repository_id() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(repository_id="not-a-uuid"))


def test_constructor_rejects_invalid_decision_digest() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(decision_record_digest="short"))


def test_constructor_rejects_invalid_binding_digest() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(binding_digest="short"))


def test_constructor_rejects_invalid_commit_sha() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(operation_reference=Ag3OperationReference(job_id="j", original_commit_sha="zz")))


def test_constructor_rejects_empty_identifiers() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(principal_id=""))


def test_constructor_rejects_ag3_ag5_mismatch() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(family="AG3", rollback_site=RollbackSite.AG5))


@pytest.mark.parametrize(
    "field",
    [
        "trusted_root",
        "trusted_public_key",
        "attestation_root",
        "authority_registry",
        "canonical_root",
        "trust_store_root",
        "deployment_root",
        "approved",
        "trusted",
        "authorized",
        "human_present",
        "valid",
        "arbitrary_unknown",
    ],
)
def test_closed_schema_rejects_unknown_fields(field: str) -> None:
    doc = _valid_document(**{field: "x"})
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_duplicate_top_level_key_rejected() -> None:
    good = _valid_document()
    raw = '{"proof_version":1,"proof_version":1,' + json.dumps(good)[1:]
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_ag3_ag5_wrong_family_field_rejected() -> None:
    doc = _valid_document(family="AG3", per_id="p", ecp_id="e")
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_ag3_ag5_unknown_family_value_rejected() -> None:
    doc = _valid_document(family="AG3")
    doc["rollback_site"] = "AG4"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_ag3_ag5_missing_family_field_rejected() -> None:
    doc = _valid_document(family="AG3")
    del doc["job_id"]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


# ═══════════════════════════════════════════════════════════════════════════
# Section L -- signed-payload / golden vector / SHA-256 independent
# reconstruction (items 49-56).
# ═══════════════════════════════════════════════════════════════════════════

_EXPECTED_SIGNED_FIELDS = frozenset(
    {
        "proof_version",
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "repository_id",
        "decision_record_id",
        "decision_record_digest",
        "binding_id",
        "binding_digest",
        "rollback_site",
        "issued_at",
        "job_id",
        "original_commit_sha",
    }
)


def test_signed_payload_field_set_unchanged_ag3() -> None:
    doc = _valid_document(family="AG3")
    proof = parse_hatp_proof(json.dumps(doc))
    assert set(hatp_proof_to_document(proof).keys()) == _EXPECTED_SIGNED_FIELDS


def test_ag3_golden_vector_independent_reconstruction() -> None:
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": "12345678-1234-4123-8123-123456789abc",
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG3",
        "issued_at": "2026-01-01T12:00:00.001Z",
        "job_id": "job-1",
        "original_commit_sha": "c" * 40,
    }
    proof = parse_hatp_proof(json.dumps(doc))
    expected_bytes = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
        "utf-8"
    )
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == hashlib.sha256(expected_bytes).hexdigest()


def test_ag5_golden_vector_independent_reconstruction() -> None:
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": "12345678-1234-4123-8123-123456789abc",
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG5",
        "issued_at": "2026-01-01T12:00:00.001Z",
        "per_id": "per-1",
        "ecp_id": "ecp-1",
    }
    proof = parse_hatp_proof(json.dumps(doc))
    expected_bytes = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
        "utf-8"
    )
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == hashlib.sha256(expected_bytes).hexdigest()


def test_mutation_sensitivity_all_signed_fields() -> None:
    base = _valid_document(family="AG3")
    base_proof = parse_hatp_proof(json.dumps(base))
    base_digest = digest_hatp_proof_payload(base_proof)
    mutations = {
        "principal_id": "bob",
        "signer_key_id": "signer-2",
        "provider_profile": "OTHER_PROVIDER",
        "decision_record_id": "chgr-record-2",
        "decision_record_digest": "d" * 64,
        "binding_id": "rae-binding-2",
        "binding_digest": "e" * 64,
        "issued_at": "2026-08-06T00:00:00.001Z",
        "job_id": "job-2",
        "original_commit_sha": "f" * 40,
    }
    for field, value in mutations.items():
        mutated = dict(base, **{field: value})
        mutated_proof = parse_hatp_proof(json.dumps(mutated))
        assert digest_hatp_proof_payload(mutated_proof) != base_digest, f"{field} mutation did not change digest"


# ═══════════════════════════════════════════════════════════════════════════
# Section M -- purity / dependency / public API / vocabulary audit
# (items 60-64).
# ═══════════════════════════════════════════════════════════════════════════


def test_no_forbidden_verification_vocabulary_symbols() -> None:
    from pcae.core import human_approval_trusted_provenance as hatp_module

    forbidden = {"VALID", "UNKNOWN_SIGNER", "approval_present", "HATP_VALID"}
    assert forbidden.isdisjoint(dir(hatp_module))


def test_no_forbidden_module_dependencies() -> None:
    """Checks actual `import`/`from ... import` statement lines only.
    "hatp_bootstrap" deliberately removed from the forbidden set here
    (Phase 149O.1I, Wave 4): the 149O.1D plan explicitly co-locates the
    verifier in this module, requiring a read-only `HATPTrustStore`
    import (HATP-REQ-094); "hatp_providers" (the new provider-neutral
    interface module) is likewise now an expected import."""
    src = (REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py").read_text()
    import_lines = [line for line in src.splitlines() if line.strip().startswith(("import ", "from "))]
    forbidden_modules = ("rollback_approval_evidence", "permission_broker", "pcae.core.agent", "commands.agent")
    for line in import_lines:
        for forbidden in forbidden_modules:
            assert forbidden not in line, f"forbidden import found: {line!r}"


def test_dataclasses_remain_frozen() -> None:
    proof = _construct("2026-01-01T12:00:00.001Z")
    with pytest.raises(Exception):
        proof.principal_id = "mallory"  # type: ignore[misc]
    with pytest.raises(Exception):
        proof.operation_reference.job_id = "mallory"  # type: ignore[union-attr]


def test_structural_validity_does_not_imply_trust_no_verification_api() -> None:
    """A structurally valid proof exposes no verification-status
    attribute; parsing success means structural conformance only."""
    proof = _construct("2026-01-01T12:00:00.001Z")
    for forbidden_attr in ("approval_present", "verified", "trusted", "valid", "authorized", "human_present"):
        assert not hasattr(proof, forbidden_attr)
