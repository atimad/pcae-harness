"""Repository-wide Phase ID grammar drift-prevention (Phase 137T).

CPIPC-001 (CPIPC-REQ-018/019/020) designates ``pcae.core.phase_id`` the
sole authority for Phase ID recognition, validation, normalization,
comparison, and error classification. This test is the automated guard
against future silent re-duplication of that grammar: it scans every
``.py`` file under ``src/pcae/`` (excluding ``phase_id.py`` itself) for
regex string literals matching the structural *signature* of a
hand-rolled Phase ID grammar fragment (a digit-quantifier immediately
adjacent to a letter-class, or vice versa -- the shape every one of the
duplicate regexes 137P/137R/137S/137T found and repaired shared), and
fails if any such literal appears at a location not already present in
the reviewed, disclosed ``ALLOWLIST`` below.

This is a *closed-world* guard, not an open one: adding a new entry to
``ALLOWLIST`` is a real code-review decision (is this a boundary/
adapter, or an unauthorized parser?), not a rubber stamp -- exactly the
disposition categories CPIPC-001's own conformance framework uses
(canonical / adapter / boundary representation / unauthorized /
false positive).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "pcae"

# The structural signature every hand-rolled Phase-ID-shaped grammar
# fragment found by 137P/137R/137S/137T shared: a digit-quantifier
# directly adjacent (within a few characters, allowing for a capture
# group or non-capturing group boundary) to a letter-class, in either
# order.
_SIGNATURE_RE = re.compile(r"\\d.{0,4}\[A-Za-z\]|\[A-Za-z\].{0,4}\\d")

# Regex-producing call names whose first positional argument is the
# pattern text (covers both ``re.compile(...)`` and the module-level
# ``re.match``/``re.search``/``re.findall``/``re.finditer`` shortcuts).
_REGEX_CALL_NAMES = {"compile", "match", "search", "findall", "finditer", "fullmatch"}

# ── Reviewed, disclosed exceptions (137T) ───────────────────────────────
#
# Every entry here was found by 137T's fresh repository-wide audit and
# received an explicit disposition (see
# docs/PHASE_137T_CANONICAL_PHASE_ID_REPOSITORY_WIDE_CONFORMANCE.md).
# A new, undisclosed hit anywhere else in the tree fails this test.
ALLOWLIST: frozenset[tuple[str, int]] = frozenset({
    # `evidence_phase_ids` free-text candidate scanner inside
    # `validate_derived_correctness()`. Intentionally retained: this is
    # a *candidate* net over test-result prose (not itself an acceptance
    # decision) -- every candidate it turns up is then compared for
    # "same series" via the canonical `same_series()` predicate (137T),
    # not by ad hoc string comparison. Broadening it to the canonical
    # grammar exactly would not change any currently-passing test and
    # is deferred as low-value, not high-risk.
    ("src/pcae/core/phase_reports.py", 1365),
    # The four structural "## Phase X Complete" / "## Current Phase"
    # header and declaration-line regexes feeding
    # `_match_current_phase_declaration()`. Deliberately NOT migrated in
    # 137T: these are safety-critical, heavily-regression-tested
    # MULTILINE/DOTALL document-structure parsers where the phase-ID
    # sub-pattern is one piece of a much larger structural match: e.g.
    # capture start, required trailing "(completed)"/"(not started)"
    # status-marker alternation, or the "## Phase X Complete" heading
    # shape itself. A structural rewrite carries real regression risk
    # in the phase-completion identity path for no live defect (direct
    # comparison confirms the embedded grammar sub-pattern is a STRICT
    # SUBSET of CPIPC-001's canonical grammar -- it can only reject
    # forms the canonical grammar accepts, never falsely accept
    # anything the canonical grammar itself rejects). Documented
    # exception; a dedicated future phase should retire these once a
    # canonical two-step "locate loosely, then delegate" rewrite can be
    # given its own regression scaffolding.
    #
    # Phase 144J moved/added lines within this same disclosed group
    # while repairing the marker-bounded grammars' truncation defect
    # (see `_PHASE_LABEL_LINE_WITH_STATUS_RE`'s own comment in
    # phase_reports.py): the two lines that were 2487/2492 are now
    # 2525/2530 (unchanged content, shifted down by new code above
    # them), and one new structural regex,
    # `_PHASE_LABEL_LINE_WITH_STATUS_RE` (2468), was added as the
    # sibling of `_CURRENT_PHASE_LINE_WITH_STATUS_RE` for the "## Phase
    # X Complete" header's own label line -- same disposition as the
    # rest of this group (structural document parser, phase-ID
    # sub-pattern is a strict subset of the canonical grammar).
    ("src/pcae/core/phase_reports.py", 2450),
    ("src/pcae/core/phase_reports.py", 2454),
    ("src/pcae/core/phase_reports.py", 2468),
    ("src/pcae/core/phase_reports.py", 2525),
    ("src/pcae/core/phase_reports.py", 2530),
})

# `cltr/authority/identity.py`'s `_PHASE_IDENTITY_PATTERN` is a pure
# charset+length boundary check (`^[A-Za-z0-9.]{1,16}$`) with no
# digit-adjacent-to-letter-class structure at all -- it does not match
# `_SIGNATURE_RE` and needs no allowlist entry. Documented separately
# (137P §15 "charset-reservation risk", re-verified 137T) as a
# deliberately deferred, distinct wire-boundary type, not a Phase ID
# grammar duplicate.


def _resolve_string_expr(node: ast.AST, name_table: dict[str, str]) -> str | None:
    """Best-effort static resolution of a regex-pattern expression:
    handles a plain string literal, ``"a" "b"`` implicit concatenation
    (already folded by the parser into one Constant), ``"a" + "b"``
    explicit concatenation (including a mix of literals and simple
    module-level string-constant names), and simple ``Name`` lookups.
    Returns ``None`` when the expression can't be statically resolved
    (e.g. an f-string or a non-string-constant name) -- such patterns
    are simply not checked, rather than producing a false signature
    match."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_string_expr(node.left, name_table)
        right = _resolve_string_expr(node.right, name_table)
        if left is not None and right is not None:
            return left + right
        return None
    if isinstance(node, ast.Name):
        return name_table.get(node.id)
    return None


def _build_module_string_constant_table(tree: ast.AST) -> dict[str, str]:
    table: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        value = _resolve_string_expr(node.value, table)
        if value is not None:
            table[target.id] = value
    return table


def _iter_regex_pattern_literals(tree: ast.AST):
    name_table = _build_module_string_constant_table(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in _REGEX_CALL_NAMES:
            continue
        if not node.args:
            continue
        first = node.args[0]
        pattern = _resolve_string_expr(first, name_table)
        if pattern is not None:
            yield pattern, first.lineno


def _find_phase_id_shaped_regex_hits() -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.name == "phase_id.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for pattern, lineno in _iter_regex_pattern_literals(tree):
            if _SIGNATURE_RE.search(pattern):
                rel = path.relative_to(REPO_ROOT).as_posix()
                hits.append((rel, lineno, pattern))
    return hits


def test_no_undisclosed_phase_id_shaped_regex_outside_canonical_parser() -> None:
    hits = _find_phase_id_shaped_regex_hits()
    found = {(rel, lineno) for rel, lineno, _pattern in hits}
    undisclosed = sorted(found - ALLOWLIST)
    assert not undisclosed, (
        "New Phase-ID-grammar-shaped regex literal(s) found outside the "
        "canonical parser (pcae.core.phase_id) and outside the reviewed "
        "137T allowlist. Per CPIPC-REQ-018, Phase ID recognition must "
        "delegate to pcae.core.phase_id. If this is a genuine boundary/ "
        "adapter case (not a duplicate grammar), add it to ALLOWLIST in "
        "this file with an explicit disposition; otherwise migrate it. "
        f"Undisclosed hits: {undisclosed}"
    )


def test_allowlist_entries_still_exist_at_their_recorded_locations() -> None:
    """A stale allowlist entry (line moved/removed) is itself a drift
    signal -- either the exception was fixed (shrink the allowlist) or
    the file changed underneath it (re-verify and update the line)."""
    hits = _find_phase_id_shaped_regex_hits()
    found = {(rel, lineno) for rel, lineno, _pattern in hits}
    stale = sorted(ALLOWLIST - found)
    assert not stale, (
        "Allowlist entries no longer match a real Phase-ID-shaped regex "
        f"at their recorded location -- re-verify and update: {stale}"
    )


@pytest.mark.parametrize(
    "pattern",
    [
        r"\d{3}[A-Za-z](?:\.[A-Za-z0-9]+)?",
        r"\d+[A-Za-z]+(?:\.\d+[A-Za-z]?)*",
        r"[A-Za-z]+\d+",
    ],
)
def test_signature_heuristic_detects_known_duplicate_shapes(pattern: str) -> None:
    """Positive control: confirms the heuristic itself still fires on the
    exact shapes 137P/137R/137S/137T found and repaired, so a change to
    the heuristic can't silently stop detecting them."""
    assert _SIGNATURE_RE.search(pattern) is not None


def test_signature_heuristic_does_not_flag_unrelated_patterns() -> None:
    """Negative control: ordinary regexes with no digit/letter-class
    adjacency must not spuriously trip the guard."""
    for pattern in [r"^\s+$", r"[^()]+", r"Phase\s+", r"\bNo\s+", r"[a-z0-9-]{8,128}"]:
        assert _SIGNATURE_RE.search(pattern) is None, pattern
