"""Tests for the canonical Phase ID parser (Phase 137R, CPIPC-001 v1.0).

Covers grammar acceptance/rejection, normalization, comparison semantics,
the closed error taxonomy, historical compatibility, and regression
protection for the specific truncation defects CPIPC-001 exists to
foreclose (137F.1V, 137MV.1, and the still-open
repository_transition_integration.py sibling this phase migrates).
"""

from __future__ import annotations

import pytest

from pcae.core import phase_id as pid


# ---------------------------------------------------------------------------
# Grammar: supported forms.
# ---------------------------------------------------------------------------

HISTORICAL_VALID_IDS = [
    "92A",
    "96D",
    "119AB",
    "119AC",
    "135H",
    "135H.2",
    "137MV",
    "137F.1V",
    "134E.10",
    "134E.10.1V",
    "134E.10.1.1",
    "113X.1",
    "113X.2",
    "113D.R",
    "136Z",
    "136AA",
    "136AX",
    "136AY",
    "137N",
]


@pytest.mark.parametrize("phase_id", HISTORICAL_VALID_IDS)
def test_historical_valid_ids_parse(phase_id: str) -> None:
    parsed = pid.parse(phase_id)
    assert parsed.normalized_text == phase_id.upper()


def test_supported_forms_round_trip_through_format() -> None:
    for phase_id in HISTORICAL_VALID_IDS:
        parsed = pid.parse(phase_id)
        assert pid.format(parsed) == pid.normalize(phase_id)


# ---------------------------------------------------------------------------
# Grammar: reserved forms (CPIPC-001 §4.2).
# ---------------------------------------------------------------------------


def test_bare_numeric_series_is_reserved_not_missing_branch() -> None:
    err = pid.validate("134")
    assert err is not None
    assert err.kind == "reserved_syntax"


# ---------------------------------------------------------------------------
# 137T repair: branch letters separated from the series by a stray "."
# are present-but-misplaced (invalid_syntax), not absent (missing_branch)
# -- 137S non-blocking finding, disclosed and repaired in 137T.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["134.A", "134..A", "134.AB", "134...A"])
def test_stray_dot_before_branch_letters_is_invalid_syntax_not_missing_branch(
    text: str,
) -> None:
    err = pid.validate(text)
    assert err is not None
    assert err.kind == "invalid_syntax"


@pytest.mark.parametrize("text", ["134.", "134..", "134"])
def test_truly_absent_branch_letters_still_missing_branch_or_reserved(
    text: str,
) -> None:
    err = pid.validate(text)
    assert err is not None
    assert err.kind in ("missing_branch", "reserved_syntax")


def test_leading_zero_series_is_unsupported() -> None:
    err = pid.validate("007A")
    assert err is not None
    assert err.kind == "unsupported_syntax"


# ---------------------------------------------------------------------------
# Grammar: invalid forms (CPIPC-001 §4.3).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_input,expected_kind",
    [
        ("", "empty_input"),
        ("   ", "empty_input"),
        ("A", "invalid_syntax"),
        ("abc", "invalid_syntax"),
        ("A134", "invalid_syntax"),
        ("134E.V1", "malformed_subphase"),
        ("134E..1", "malformed_subphase"),
        ("134E.", "malformed_subphase"),
        ("137N-extra", "unexpected_suffix"),
        ("137 N", "invalid_syntax"),
    ],
)
def test_invalid_forms_classify_correctly(invalid_input: str, expected_kind: str) -> None:
    err = pid.validate(invalid_input)
    assert err is not None
    assert err.kind == expected_kind


def test_none_input_is_empty_input() -> None:
    err = pid.validate(None)
    assert err is not None
    assert err.kind == "empty_input"


def test_rejection_never_raises_uncaught_for_is_valid() -> None:
    assert pid.is_valid("") is False
    assert pid.is_valid(None) is False
    assert pid.is_valid("not a phase id") is False


def test_parse_raises_classified_error() -> None:
    with pytest.raises(pid.PhaseIdError) as excinfo:
        pid.parse("not-a-phase-id")
    assert excinfo.value.kind in pid.ErrorKind.__args__  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Case sensitivity / normalization (CPIPC-001 §4.4, §9).
# ---------------------------------------------------------------------------


def test_case_insensitive_recognition_normalizes_to_uppercase() -> None:
    assert pid.normalize("137mv") == "137MV"
    assert pid.normalize("137Mv") == "137MV"
    assert pid.normalize("137MV") == "137MV"


def test_case_variants_are_the_same_phase_id() -> None:
    assert pid.equals(pid.parse("137mv"), pid.parse("137MV"))


def test_whitespace_stripped_but_internal_whitespace_rejected() -> None:
    assert pid.normalize("  137N  ") == "137N"
    assert pid.is_valid("137 N") is False


# ---------------------------------------------------------------------------
# Canonical representation (CPIPC-001 §5).
# ---------------------------------------------------------------------------


def test_137f1v_and_137f1_are_distinct_identities() -> None:
    a = pid.parse("137F.1V")
    b = pid.parse("137F.1")
    assert not pid.equals(a, b)


def test_comparison_identity_equals_normalized_text_content() -> None:
    parsed = pid.parse("134E.10.1V")
    series, branch, subphase = parsed.comparison_identity
    assert (series, branch) == (134, "E")
    assert subphase == ((10, ""), (1, "V"))
    assert parsed.serialization_identity == parsed.normalized_text


def test_source_text_preserved_but_not_used_for_equality() -> None:
    a = pid.parse("137mv")
    b = pid.parse("137MV")
    assert a.source_text != b.source_text
    assert pid.equals(a, b)


# ---------------------------------------------------------------------------
# Comparison semantics (CPIPC-001 §10).
# ---------------------------------------------------------------------------


def test_numeric_subphase_compares_as_integer_not_string() -> None:
    assert pid.compare(pid.parse("134E.2"), pid.parse("134E.10")) == "less"
    assert pid.compare(pid.parse("134E.10"), pid.parse("134E.2")) == "greater"


def test_branch_rollover_ordering() -> None:
    assert pid.compare(pid.parse("136Z"), pid.parse("136AA")) == "less"
    assert pid.compare(pid.parse("136AW"), pid.parse("136AX")) == "less"
    assert pid.compare(pid.parse("136AX"), pid.parse("136AY")) == "less"


def test_branch_rollover_is_not_lexical() -> None:
    # Lexically "AA" < "B", but AA is the rollover *after* Z, so it must
    # rank after every single-letter branch.
    assert pid.compare(pid.parse("136AA"), pid.parse("136B")) == "greater"


def test_exceptional_branch_not_comparable_to_mainline() -> None:
    assert pid.compare(pid.parse("113D"), pid.parse("113X.2")) == "not_comparable"
    assert pid.compare(pid.parse("113X.2"), pid.parse("113D")) == "not_comparable"


def test_exceptional_branch_comparable_to_itself() -> None:
    assert pid.compare(pid.parse("113X.1"), pid.parse("113X.2")) == "less"


def test_different_series_not_comparable() -> None:
    assert pid.compare(pid.parse("92A"), pid.parse("93A")) == "not_comparable"


def test_equal_identity_compares_equal() -> None:
    assert pid.compare(pid.parse("137mv"), pid.parse("137MV")) == "equal"


def test_no_artificial_total_ordering_between_series() -> None:
    outcomes = {
        pid.compare(pid.parse("10A"), pid.parse("9A")),
        pid.compare(pid.parse("9A"), pid.parse("10A")),
    }
    assert outcomes == {"not_comparable"}


def test_same_series_and_same_branch_predicates() -> None:
    a = pid.parse("134E.2")
    b = pid.parse("134E.10")
    c = pid.parse("134F.1")
    d = pid.parse("135E.1")
    assert pid.same_series(a, b) and pid.same_branch(a, b)
    assert pid.same_series(a, c) and not pid.same_branch(a, c)
    assert not pid.same_series(a, d)


# ---------------------------------------------------------------------------
# Token scanning (CPIPC-001 §8) — distinct from `parse`.
# ---------------------------------------------------------------------------


def test_scan_tokens_finds_every_valid_candidate() -> None:
    text = "Phase 137MV: fix things, see also 92A and totally-not-a-phase-id"
    tokens = [t.normalized_text for t in pid.scan_tokens(text)]
    assert tokens == ["137MV", "92A"]


def test_find_first_token_returns_first_match() -> None:
    token = pid.find_first_token("Finish Phase 134E.10.1V test-evidence-key correction task")
    assert token is not None
    assert token.normalized_text == "134E.10.1V"


def test_find_first_token_returns_none_when_absent() -> None:
    assert pid.find_first_token("no phase reference here") is None


def test_token_scanner_never_raises_on_no_match() -> None:
    assert pid.scan_tokens("") == []
    assert pid.scan_tokens("nothing to see") == []


# ---------------------------------------------------------------------------
# Historical regression protection — the specific truncation defects
# CPIPC-001 exists to foreclose (Phase 137P §2.2).
# ---------------------------------------------------------------------------


def test_two_letter_branch_suffix_not_truncated() -> None:
    # 137MV.1: prior _PHASE_TOKEN_RE (`[A-Za-z]`, exactly one) truncated
    # "137MV" to "137M".
    parsed = pid.parse("137MV")
    assert parsed.branch == "MV"
    assert parsed.normalized_text == "137MV"


def test_dotted_verification_suffix_not_truncated() -> None:
    # 137F.1V: prior regexes with a trailing \b after an unquantified
    # dotted group truncated "137F.1V" to "137F.1".
    parsed = pid.parse("137F.1V")
    assert parsed.subphase == ((1, "V"),)
    assert parsed.normalized_text == "137F.1V"


def test_one_letter_suffix_not_truncated() -> None:
    parsed = pid.parse("134E.10V")
    assert parsed.subphase == ((10, "V"),)


def test_repository_transition_integration_defect_input_now_parses_correctly() -> None:
    # The still-open truncation defect this contract explicitly notes
    # (CPIPC-REQ-056): a two-letter branch inside free text must not
    # collapse to a truncated one-letter match.
    token = pid.find_first_token("current phase: Phase 137MV (in progress)")
    assert token is not None
    assert token.normalized_text == "137MV"


def test_branch_comparison_not_naive_lexicographic() -> None:
    # Phase 113X.3: naive lexicographic comparison treated "113D" < "113X.2"
    # as meaningful. The canonical comparator must report not_comparable.
    assert pid.compare(pid.parse("113D"), pid.parse("113X.2")) == "not_comparable"


def test_duplicate_parser_divergence_scenario() -> None:
    # Every historically-divergent grammar variant must agree once routed
    # through the single canonical parser.
    for phase_id in ("136AX", "119AB", "137MV", "134E.10.1V"):
        assert pid.is_valid(phase_id)
        assert pid.parse(phase_id).normalized_text == phase_id


# ---------------------------------------------------------------------------
# Determinism / security (CPIPC-001 §16).
# ---------------------------------------------------------------------------


def test_parse_is_deterministic() -> None:
    results = {pid.parse("137F.1V").comparison_identity for _ in range(50)}
    assert len(results) == 1


def test_module_has_no_mutable_module_state_leak() -> None:
    pid.parse("137F.1V")
    pid.parse("92A")
    # A second, independent parse of the same input must be unaffected
    # by any prior call (no caching keyed on ambient state).
    assert pid.parse("137F.1V").normalized_text == "137F.1V"
