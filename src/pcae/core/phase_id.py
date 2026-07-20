"""Canonical Phase ID parser — Phase 137R implementation of CPIPC-001 v1.0.

This module is the sole authority (CPIPC-REQ-018) for recognition,
validation, normalization, formatting, comparison, and error
classification of PCAE Phase ID text, per the Canonical Phase ID Parsing
Contract (``docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md``,
CPIPC-001 v1.0, frozen by Phase 137Q from the Phase 137P architecture).

Grammar (CPIPC-001 §4, frozen verbatim from Phase 137P §4.2)::

    phase-id        = series , branch , { "." , subphase-segment } ;
    series          = digit , { digit } ;
    branch          = letter , { letter } ;
    subphase-segment
                    = numeric-segment | letter-segment ;
    numeric-segment = digit , { digit } , [ letter , { letter } ] ;
    letter-segment  = letter , { letter } ;

This module is deterministic, side-effect-free, stateless, thread-safe,
authority-neutral, and runtime-neutral (CPIPC-001 §16). It performs no
filesystem, repository, or network access, and consults nothing about
governance, task, or runtime state. Callers that need candidate Phase ID
text from a file or free text SHALL read/locate that text themselves and
hand only the text to this module (CPIPC-REQ-027).

Runtime remains Observed / observe / unavailable throughout; this module
introduces no execution capability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Tuple, Union

__all__ = [
    "PhaseId",
    "PhaseIdError",
    "ErrorKind",
    "parse",
    "is_valid",
    "normalize",
    "format",
    "validate",
    "scan_tokens",
    "find_first_token",
    "match_leading_token",
    "equals",
    "compare",
    "same_series",
    "same_branch",
]


# ---------------------------------------------------------------------------
# Error taxonomy (CPIPC-001 §11) — closed, nine-kind set.
# ---------------------------------------------------------------------------

ErrorKind = Literal[
    "empty_input",
    "invalid_syntax",
    "missing_branch",
    "malformed_subphase",
    "unsupported_syntax",
    "reserved_syntax",
    "ambiguous_syntax",
    "truncated_extraction",
    "unexpected_suffix",
]


class PhaseIdError(Exception):
    """A classified Phase ID parsing failure (CPIPC-001 §11).

    ``kind`` is always one of the nine closed :data:`ErrorKind` values.
    ``source_text`` is the original, unnormalized text that failed to
    parse, retained for diagnostics only (never for comparison).
    """

    def __init__(self, kind: ErrorKind, source_text: str, detail: str) -> None:
        self.kind = kind
        self.source_text = source_text
        self.detail = detail
        super().__init__(f"PhaseIdError({kind}): {detail!r} (input={source_text!r})")


# ---------------------------------------------------------------------------
# Canonical representation (CPIPC-001 §5).
# ---------------------------------------------------------------------------

# Each subphase segment is (number, letters):
#   numeric-segment "10"  -> (10, "")
#   numeric-segment "1V"  -> (1, "V")
#   letter-segment  "R"   -> (None, "R")
SubphaseSegment = Tuple[Optional[int], str]


@dataclass(frozen=True)
class PhaseId:
    """The canonical, immutable parsed representation of a Phase ID
    (CPIPC-001 §5). Construct only via :func:`parse` or :func:`from_parts`
    — never by hand-assembling the fields, so ``normalized_text``,
    ``comparison_identity``, and ``serialization_identity`` can never
    drift from the grammar (CPIPC-REQ-016, CPIPC-REQ-030).
    """

    series: int
    branch: str
    subphase: tuple[SubphaseSegment, ...]
    source_text: str

    @property
    def normalized_text(self) -> str:
        parts = [f"{self.series}{self.branch}"]
        for number, letters in self.subphase:
            parts.append(letters if number is None else f"{number}{letters}")
        return ".".join(parts)

    @property
    def comparison_identity(self) -> tuple[int, str, tuple[SubphaseSegment, ...]]:
        return (self.series, self.branch, self.subphase)

    @property
    def serialization_identity(self) -> str:
        return self.normalized_text


# ---------------------------------------------------------------------------
# Canonical grammar (CPIPC-001 §4) — single source of truth.
# ---------------------------------------------------------------------------

_SERIES = r"[0-9]+"
_BRANCH = r"[A-Za-z]+"
_NUMERIC_SEGMENT = r"[0-9]+[A-Za-z]*"
_LETTER_SEGMENT = r"[A-Za-z]+"
_SUBPHASE_SEGMENT = rf"(?:{_NUMERIC_SEGMENT}|{_LETTER_SEGMENT})"

_PHASE_ID_RE = re.compile(
    rf"^(?P<series>{_SERIES})(?P<branch>{_BRANCH})"
    rf"(?P<subphase>(?:\.{_SUBPHASE_SEGMENT})*)$"
)

_SUBPHASE_SEGMENT_RE = re.compile(r"^([0-9]+)([A-Za-z]*)$|^([A-Za-z]+)$")

# Reserved forms (CPIPC-001 §4.2): recognized but not accepted as valid.
_RESERVED_BARE_SERIES_RE = re.compile(r"^[0-9]+$")
_RESERVED_LEADING_ZERO_RE = re.compile(r"^0[0-9]*[A-Za-z]+(?:\.(?:[0-9]+[A-Za-z]*|[A-Za-z]+))*$")

# Token scanner (CPIPC-001 §8): locates a candidate span; the acceptance
# decision remains exclusively with `parse` (CPIPC-REQ-038). Deliberately
# permissive at the lexical-candidate level (any run of the grammar's
# alphabet, `.` included) so it can never itself under- or over-accept —
# every candidate is handed to `parse`, never judged here.
_TOKEN_CANDIDATE_RE = re.compile(r"[0-9]+[A-Za-z]+(?:\.[0-9A-Za-z]+)*")


def _classify_invalid(stripped: str) -> PhaseIdError:
    """Classify a string that failed the main grammar into one of the
    closed error kinds (CPIPC-001 §11). Called only after the fast-path
    grammar match has already failed.
    """
    if not stripped:
        return PhaseIdError("empty_input", stripped, "input was empty or whitespace-only")

    if _RESERVED_LEADING_ZERO_RE.match(stripped):
        return PhaseIdError(
            "unsupported_syntax", stripped,
            "leading-zero series is reserved (CPIPC-001 §4.2), not supported",
        )

    if _RESERVED_BARE_SERIES_RE.match(stripped):
        return PhaseIdError(
            "reserved_syntax", stripped,
            "bare numeric series with no branch letters is reserved (CPIPC-001 §4.2)",
        )

    # Series present but no branch letters anywhere after it: missing_branch.
    # 137T repair: branch letters separated from the series by a stray
    # "." (e.g. "134.A", "134..A") are present, just misplaced -- that is
    # a syntax violation (invalid_syntax), not an absence of branch
    # letters (missing_branch), per CPIPC-001 §11's own stated meaning
    # for each kind. Checking for ANY letter in the tail (not just a
    # leading one) distinguishes "no letters at all" from "letters
    # present but wrongly placed."
    m = re.match(r"^([0-9]+)([A-Za-z.]*)$", stripped)
    if m and m.group(1) and not re.search(r"[A-Za-z]", m.group(2) or ""):
        return PhaseIdError(
            "missing_branch", stripped,
            "a numeric series was present with no branch letters",
        )

    # A well-formed series+branch prefix exists, but something after it
    # does not fit the grammar: distinguish malformed_subphase (dotted
    # segment shape violation) from unexpected_suffix (trailing junk with
    # no leading dot) and invalid_syntax (no recognizable prefix at all).
    prefix_m = re.match(rf"^({_SERIES})({_BRANCH})", stripped)
    if prefix_m:
        rest = stripped[prefix_m.end():]
        if rest.startswith("."):
            return PhaseIdError(
                "malformed_subphase", stripped,
                f"dotted segment does not fit the subphase grammar: {rest!r}",
            )
        if rest:
            return PhaseIdError(
                "unexpected_suffix", stripped,
                f"trailing characters after a valid series+branch prefix: {rest!r}",
            )

    return PhaseIdError(
        "invalid_syntax", stripped, "input does not match the Phase ID grammar at all",
    )


def parse(text: str | None) -> PhaseId:
    """Parse ``text`` into a canonical :class:`PhaseId`, or raise a
    classified :class:`PhaseIdError` (CPIPC-001 §8, §9). The sole entry
    point; every other operation in this module is built on it.

    Leading/trailing ASCII whitespace is stripped before matching;
    internal whitespace is never valid (CPIPC-REQ-032). Recognition is
    ``fullmatch``-based and case-insensitive at the lexical level, with
    mandatory uppercasing on success (CPIPC-REQ-014, CPIPC-REQ-033).
    """
    if text is None:
        raise PhaseIdError("empty_input", "", "input was None")

    stripped = text.strip()
    match = _PHASE_ID_RE.match(stripped)
    if match is None:
        raise _classify_invalid(stripped)

    series_text = match.group("series")
    if len(series_text) > 1 and series_text[0] == "0":
        raise PhaseIdError(
            "unsupported_syntax", stripped,
            "leading-zero series is reserved (CPIPC-001 §4.2), not supported",
        )

    series = int(series_text)
    branch = match.group("branch").upper()
    subphase_str = match.group("subphase")

    subphase: list[SubphaseSegment] = []
    if subphase_str:
        for piece in subphase_str.split(".")[1:]:
            seg_match = _SUBPHASE_SEGMENT_RE.match(piece)
            if seg_match is None:  # pragma: no cover — grammar guarantees a match here
                raise PhaseIdError(
                    "malformed_subphase", stripped, f"unparseable subphase segment: {piece!r}",
                )
            digits, num_letters, letter_only = seg_match.groups()
            if digits is not None:
                subphase.append((int(digits), num_letters.upper()))
            else:
                subphase.append((None, letter_only.upper()))

    return PhaseId(series=series, branch=branch, subphase=tuple(subphase), source_text=text)


def is_valid(text: str | None) -> bool:
    """Boolean convenience over :func:`parse` (CPIPC-REQ-029): "did
    parse succeed," never an independently-implemented check."""
    try:
        parse(text)
        return True
    except PhaseIdError:
        return False


def validate(text: str | None) -> PhaseIdError | None:
    """:func:`parse` used for its classified-error behavior: returns
    ``None`` on success, or the :class:`PhaseIdError` that would have
    been raised, without raising it."""
    try:
        parse(text)
        return None
    except PhaseIdError as exc:
        return exc


def normalize(value: PhaseId | str) -> str:
    """Return ``normalized_text`` for an already-parsed :class:`PhaseId`,
    or for raw text that parses successfully (CPIPC-REQ-035)."""
    parsed = value if isinstance(value, PhaseId) else parse(value)
    return parsed.normalized_text


def format(value: PhaseId) -> str:
    """Canonical text for a :class:`PhaseId` value, however obtained.
    Converges with :func:`normalize` for the same identity by
    construction (both read ``normalized_text``)."""
    return value.normalized_text


# ---------------------------------------------------------------------------
# Token scanning (CPIPC-001 §8) — distinct from `parse`; never its own
# competing acceptance rule (CPIPC-REQ-038).
# ---------------------------------------------------------------------------


def scan_tokens(text: str) -> list[PhaseId]:
    """Locate every candidate Phase ID substring in free ``text`` (a
    commit subject, task title, report heading) and return the
    :class:`PhaseId` values for every candidate that also passes
    :func:`parse`. Candidates that fail to parse are silently skipped —
    token scanning locates spans; it never raises on a non-match
    (CPIPC-REQ-038)."""
    results: list[PhaseId] = []
    for candidate in _TOKEN_CANDIDATE_RE.findall(text or ""):
        try:
            results.append(parse(candidate))
        except PhaseIdError:
            continue
    return results


def find_first_token(text: str) -> PhaseId | None:
    """The first candidate in ``text`` that parses successfully, or
    ``None`` if none does. A convenience over :func:`scan_tokens` for the
    common single-token extraction call sites."""
    for candidate in _TOKEN_CANDIDATE_RE.finditer(text or ""):
        try:
            return parse(candidate.group(0))
        except PhaseIdError:
            continue
    return None


def match_leading_token(text: str) -> PhaseId | None:
    """A candidate anchored at the very start of (stripped) ``text``
    that also parses successfully, or ``None``. For call sites that
    historically used an anchored ``match`` (e.g. "does this title begin
    with a Phase ID") rather than a free ``search`` anywhere in the
    string."""
    stripped = (text or "").strip()
    candidate = _TOKEN_CANDIDATE_RE.match(stripped)
    if candidate is None:
        return None
    try:
        return parse(candidate.group(0))
    except PhaseIdError:
        return None


# ---------------------------------------------------------------------------
# Comparison semantics (CPIPC-001 §10).
# ---------------------------------------------------------------------------

_EXCEPTIONAL_BRANCH = "X"


def _is_exceptional_branch(branch: str) -> bool:
    return branch.upper() == _EXCEPTIONAL_BRANCH


def same_series(a: PhaseId, b: PhaseId) -> bool:
    """First-class "same series" predicate (CPIPC-REQ-043)."""
    return a.series == b.series


def same_branch(a: PhaseId, b: PhaseId) -> bool:
    """First-class "same branch" predicate (CPIPC-REQ-043): equal
    series and equal branch."""
    return a.series == b.series and a.branch == b.branch


def equals(a: PhaseId, b: PhaseId) -> bool:
    """Equality on canonical, normalized structure (CPIPC-REQ-039)."""
    return a.comparison_identity == b.comparison_identity


def _branch_rank(branch: str) -> int:
    """Spreadsheet-column rank for a mainline branch: A=1, B=2, ...,
    Z=26, AA=27, AB=28, ... (CPIPC-REQ-040). Not defined for the
    exceptional branch — callers must exclude it first."""
    rank = 0
    for ch in branch:
        rank = rank * 26 + (ord(ch) - ord("A") + 1)
    return rank


def compare(a: PhaseId, b: PhaseId) -> Literal["less", "greater", "equal", "not_comparable"]:
    """Ordering within a comparable family only (CPIPC-REQ-040/041/042).

    Two Phase IDs are comparable only if they share the same ``series``
    and are either both mainline or both on the exceptional (``"X"``)
    branch — never one of each. No artificial total ordering is
    introduced: a non-comparable pair always yields ``"not_comparable"``,
    never a coerced True/False answer.
    """
    if a.series != b.series:
        return "not_comparable"
    if _is_exceptional_branch(a.branch) != _is_exceptional_branch(b.branch):
        return "not_comparable"
    if a.comparison_identity == b.comparison_identity:
        return "equal"

    if _is_exceptional_branch(a.branch):
        # Both on "X": branch is identical by construction above; order
        # is decided purely by subphase, element-wise (CPIPC-REQ-040).
        branch_cmp = 0
    else:
        a_rank, b_rank = _branch_rank(a.branch), _branch_rank(b.branch)
        branch_cmp = (a_rank > b_rank) - (a_rank < b_rank)

    if branch_cmp != 0:
        return "less" if branch_cmp < 0 else "greater"

    sub_cmp = _compare_subphase(a.subphase, b.subphase)
    if sub_cmp == 0:
        return "equal"
    return "less" if sub_cmp < 0 else "greater"


def _compare_subphase(
    a: tuple[SubphaseSegment, ...], b: tuple[SubphaseSegment, ...],
) -> int:
    """Element-wise subphase comparison: numeric sub-component first as
    an integer, then trailing letters lexically (CPIPC-REQ-040). A
    letter-only segment's number is ``None``, sorted before any numeric
    segment at the same position (no historical evidence orders it
    otherwise; this is the only well-defined choice given the grammar).
    A shorter subphase tuple that is a prefix of a longer one sorts
    before it, the natural generalization of "134E" < "134E.1"."""
    for (a_num, a_letters), (b_num, b_letters) in zip(a, b):
        if a_num != b_num:
            if a_num is None:
                return -1
            if b_num is None:
                return 1
            return -1 if a_num < b_num else 1
        if a_letters != b_letters:
            return -1 if a_letters < b_letters else 1
    if len(a) != len(b):
        return -1 if len(a) < len(b) else 1
    return 0
