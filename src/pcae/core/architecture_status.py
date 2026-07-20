"""Architecture Status canonical identity, ordering, and validation — Phase 134E.8.

Phase 134E.8 repairs generated PCAE Architecture Status blocks that
reported completed work (Track 132's Repository Intelligence Service)
as still "Planned" while claiming automatic canonical derivation. Root
cause (confirmed by direct source/state inspection, not assumption):

1. The "planned" derivation regex only matched the literal historical
   wording "Recommended next repo phase:" -- current phase reports use
   "Recommended next phase:" (no "repo"). Because the current phase's
   own recommendation sentence never matched, the generator silently
   fell back to a whole-file search for the *old* wording, and took the
   first (i.e. most historically distant, since PROJECT_STATUS.md is
   ordered newest-first) match it found -- landing on a Track 132 phase
   from many phases in the past.
2. "Completed" derivation was hard-scoped to the 110-113 series only
   (Phase 113X.5's deliberate scope boundary for the Advisory Runtime
   chapter), so even a corrected "planned" fix would have left Tracks
   125-134 permanently invisible in "Completed" -- an omission, not a
   maturity claim, but one that made "Planned: 132F" look uncontradicted
   by anything above it.
3. The "current phase" line regex could not parse dotted sub-phase +
   verification-suffix identities (e.g. "134E.7V"), so the *actual*
   current phase silently vanished from "In Progress" too.

This module holds the identity grammar, ordering, freshness, and
validation pieces of the repair that are independent of PROJECT_STATUS.md
parsing (which stays in ``pcae.core.phase_reports.build_architecture_status``,
next to the header-scanning regexes it already owns). It intentionally
reuses the canonical phase-ID grammar established by 134B.3's canonical
report-title identity resolution
(``phase_reports._CANONICAL_TITLE_PHASE_ID_RE``: digits, one mainline
letter, then zero or more ``.N`` sub-phase segments each with one
optional trailing verification letter) rather than inventing a second,
competing phase-identity system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pcae.core import phase_id as canonical_phase_id

# Locates a trailing "(...)" at the end of an "In Progress" display
# string (e.g. "Some Title (134E.7V)"). This is display-format business
# logic, not Phase ID grammar; the parenthesized content is handed to
# the canonical parser (CPIPC-001 §6) for the actual recognition.
_TRAILING_PARENTHETICAL_RE = re.compile(r"\(([^()]+)\)\s*$")

ARCHITECTURE_STATUS_SCHEMA_VERSION = "1.0"

FRESHNESS_FRESH = "fresh"
FRESHNESS_FRESH_WITH_LIMITATIONS = "fresh_with_limitations"
FRESHNESS_STALE = "stale"
FRESHNESS_INVALID = "invalid"

VALID_FRESHNESS_STATES: frozenset[str] = frozenset({
    FRESHNESS_FRESH,
    FRESHNESS_FRESH_WITH_LIMITATIONS,
    FRESHNESS_STALE,
    FRESHNESS_INVALID,
})

PhaseIdKey = tuple[int, str, tuple[tuple[int, str], ...]]


def parse_phase_id(phase_id: str) -> PhaseIdKey | None:
    """Parse a phase ID into ``(series, branch, subphase)`` for exact
    identity comparison and deterministic ordering.

    ``subphase`` is a tuple of ``(number, verification_letter)`` pairs,
    one per dotted segment -- so ``"134E.10V"`` and ``"134E.10"`` are
    distinct identities (differ in the verification letter) that still
    sort adjacently (differ only in that last field), and ``"134E.10"``
    correctly sorts after ``"134E.2"`` (numeric, not lexical, comparison
    of the subphase number). Returns ``None`` for anything that does not
    match this repository's phase-ID grammar -- callers must not guess.
    """
    if not phase_id or not isinstance(phase_id, str):
        return None
    try:
        parsed = canonical_phase_id.parse(phase_id)
    except canonical_phase_id.PhaseIdError:
        return None
    parts: list[tuple[int, str]] = []
    for number, letters in parsed.subphase:
        if number is None:
            # This call site's PhaseIdKey representation is a numeric
            # (number, letters) pair per segment; a letter-only segment
            # (the rare dotted repair-suffix form, e.g. "113D.R") has no
            # numeric analogue and is outside what this narrower,
            # ordering-focused entry point accepts.
            return None
        parts.append((number, letters))
    return parsed.series, parsed.branch, tuple(parts)


def is_valid_phase_id(phase_id: str) -> bool:
    """True if ``phase_id`` matches this repository's canonical phase-ID
    grammar exactly (no prefix matching, no truncation)."""
    return parse_phase_id(phase_id) is not None


def phase_sort_key(phase_id: str) -> tuple[int, Any]:
    """Deterministic sort key for phase IDs, independent of filesystem
    or dict iteration order. Parsable IDs sort by their structured
    identity (series, branch, subphase-by-subphase numeric/letter
    comparison); unparsable IDs sort after all parsable ones, by their
    raw string, so a malformed ID never silently reorders valid ones
    around it.

    Ordering does not imply completion or dependency -- it is a display
    convenience only.
    """
    parsed = parse_phase_id(phase_id)
    if parsed is None:
        return (1, (str(phase_id),))
    return (0, parsed)


@dataclass
class ArchitectureStatusValidation:
    """Result of validating a generated Architecture Status dict."""

    issues: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.issues


def validate_architecture_status(status: dict[str, Any]) -> list[str]:
    """Validate a structured Architecture Status dict (the return value
    of ``phase_reports.build_architecture_status()``) for the Semantic
    Freshness Invariant. Returns a list of human-readable issues -- empty
    means valid. Never raises on malformed input; unexpected shapes are
    themselves reported as issues.
    """
    issues: list[str] = []
    if not isinstance(status, dict):
        return ["architecture_status is not a dict"]

    schema_version = status.get("schema_version")
    if schema_version is not None and schema_version != ARCHITECTURE_STATUS_SCHEMA_VERSION:
        issues.append(
            f"unsupported architecture_status schema_version {schema_version!r} "
            f"(expected {ARCHITECTURE_STATUS_SCHEMA_VERSION!r})"
        )

    completed_ids = status.get("completed_phase_ids", []) or []
    planned_ids = status.get("planned_phase_ids", []) or []
    current_id = status.get("current_phase_id", "") or ""
    in_progress = [str(item) for item in (status.get("in_progress", []) or [])]
    in_progress_ids: set[str] = set()
    for item in in_progress:
        paren_match = _TRAILING_PARENTHETICAL_RE.search(item)
        if paren_match is None:
            continue
        try:
            in_progress_ids.add(canonical_phase_id.parse(paren_match.group(1)).normalized_text)
        except canonical_phase_id.PhaseIdError:
            continue

    # Exact phase-identity syntax and uniqueness.
    seen: set[str] = set()
    for pid in completed_ids:
        if not is_valid_phase_id(pid):
            issues.append(f"invalid phase-ID syntax in completed_phase_ids: {pid!r}")
        if pid in seen:
            issues.append(f"duplicate phase ID in completed_phase_ids: {pid!r}")
        seen.add(pid)

    # Completed/planned disjointness -- a completed phase cannot remain
    # planned (the exact defect this phase repairs).
    completed_set = set(completed_ids)
    for pid in planned_ids:
        if pid and pid in completed_set:
            issues.append(
                f"{pid!r} is both completed and planned "
                f"(a completed phase cannot remain planned)"
            )

    # Current/completed consistency: an active phase already marked
    # completed elsewhere is a lifecycle conflict, not current work.
    if current_id and current_id in completed_set:
        if any(current_id in item for item in in_progress):
            issues.append(
                f"current_phase_id {current_id!r} is also present in "
                f"completed_phase_ids while still listed as in-progress"
            )

    planned_set = set(planned_ids)
    if current_id and current_id in planned_set:
        issues.append(
            f"current_phase_id {current_id!r} is also planned "
            "(in-progress and planned sets must be disjoint)"
        )
    completed_upper = {str(pid).upper() for pid in completed_ids}
    planned_upper = {str(pid).upper() for pid in planned_ids}
    for pid in sorted(in_progress_ids):
        if pid in completed_upper:
            issues.append(f"phase {pid!r} appears under both Completed and In Progress")
        if pid in planned_upper:
            issues.append(f"phase {pid!r} appears under both In Progress and Planned")
    for item in in_progress:
        if re.search(r"\(completed\)", item, re.IGNORECASE):
            issues.append(f"In Progress entry claims completed state: {item!r}")

    if current_id and not is_valid_phase_id(current_id):
        issues.append(f"invalid phase-ID syntax for current_phase_id: {current_id!r}")

    # Chapter membership / duplicate chapter ownership.
    chapters = status.get("completed_chapters", []) or []
    chapter_ids: set[str] = set()
    phase_to_chapter: dict[str, str] = {}
    for chapter in chapters:
        chapter_id = chapter.get("chapter") if isinstance(chapter, dict) else None
        if chapter_id in chapter_ids:
            issues.append(f"duplicate chapter label/identity: {chapter_id!r}")
        elif chapter_id is not None:
            chapter_ids.add(chapter_id)
        for pid in (chapter.get("phase_ids", []) if isinstance(chapter, dict) else []):
            if pid in phase_to_chapter and phase_to_chapter[pid] != chapter_id:
                issues.append(
                    f"phase {pid!r} belongs to multiple incompatible chapters: "
                    f"{phase_to_chapter[pid]!r} and {chapter_id!r}"
                )
            phase_to_chapter[pid] = chapter_id

    # Runtime-state validity: Observed must never coexist with an
    # available execution boundary (this codebase's non-executing
    # ceiling -- see Runtime State Model, 110A).
    runtime_state = status.get("current_runtime_state", "")
    execution_availability = status.get("execution_availability", "")
    if (
        runtime_state == "Observed"
        and execution_availability
        and execution_availability.lower() != "unavailable"
    ):
        issues.append(
            f"current_runtime_state is 'Observed' but execution_availability "
            f"is {execution_availability!r}, not 'unavailable'"
        )

    # Freshness must be one of the declared states.
    freshness = status.get("freshness")
    if freshness is not None and freshness not in VALID_FRESHNESS_STATES:
        issues.append(f"invalid freshness state: {freshness!r}")

    # Declared conflicts must not coexist with a "fresh" freshness claim.
    conflicts = status.get("conflicts", []) or []
    if conflicts and freshness == FRESHNESS_FRESH:
        issues.append(
            "freshness is 'fresh' but conflicts are present -- conflicted "
            "state must be disclosed as at most 'fresh_with_limitations', "
            "or 'invalid' when unresolved"
        )

    # Deterministic ordering: completed/planned lists must already be in
    # phase_sort_key() order (never asserted here as "must equal a fixed
    # order" -- only that whatever order is present is self-consistent
    # with the deterministic key, so re-sorting never changes output).
    for label, ids in (("completed_phase_ids", completed_ids), ("planned_phase_ids", planned_ids)):
        keys = [phase_sort_key(pid) for pid in ids]
        if keys != sorted(keys):
            issues.append(f"{label} is not in deterministic phase-ID order")

    return issues
