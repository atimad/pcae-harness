"""Tests for Phase 134E.8 — Architecture Status Generation Repair.

Repairs a persistent, highly visible defect: generated Architecture
Status blocks reported completed Track 132 work ("132F — Repository
Intelligence Service") as still "Planned", while claiming automatic
canonical derivation ("Generated automatically from canonical project
state. Never manually maintained."). Root cause, confirmed by direct
source and repository-state inspection (not assumed):

1. The "planned" regex matched only the retired "Recommended next repo
   phase:" wording; current phase reports write "Recommended next
   phase:" (no "repo"). The current phase's own recommendation sentence
   therefore never matched, and generation fell back to a whole-file
   search for the old wording -- returning the first (most historically
   distant, since PROJECT_STATUS.md is newest-first) match.
2. "Completed" derivation was hard-scoped to the 110-113 series only,
   so Tracks 125-134 could never appear even once (1) was fixed.
3. The phase-ID grammar used throughout could not parse a dotted
   sub-phase with a trailing verification letter (e.g. "134E.7V"), so
   the actual current phase silently disappeared from "In Progress".

See docs/PHASE_134_ARCHITECTURE_STATUS_GENERATION_REPAIR.md for the full
authority model, freshness contract, and carried 134E.7V observations.

No Canonical Engineering Evidence, Evidence Extraction, Phase Report
View, Operator Report View, Rendering Architecture, Delivery Pipeline,
or Delivery Receipt activation. No execution capability.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcae.core.architecture_status import (
    ARCHITECTURE_STATUS_SCHEMA_VERSION,
    FRESHNESS_FRESH,
    FRESHNESS_FRESH_WITH_LIMITATIONS,
    FRESHNESS_INVALID,
    FRESHNESS_STALE,
    VALID_FRESHNESS_STATES,
    is_valid_phase_id,
    parse_phase_id,
    phase_sort_key,
    validate_architecture_status,
)
from pcae.core.phase_reports import build_architecture_status, make_phase_report


def _write_project_status(tmp_path: Path, body: str) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(body)


def _build(tmp_path: Path, monkeypatch) -> dict:
    monkeypatch.chdir(tmp_path)
    return build_architecture_status()


# ═══════════════════════════════════════════════════════════════════════
# 1-2. Root-cause regression: real repository no longer reports stale 132F
# ═══════════════════════════════════════════════════════════════════════


class TestRealRepositoryRootCauseRepair:
    """Generate Architecture Status from the *real* repository -- not a
    hard-coded expected block -- and confirm the exact defect this phase
    repairs is gone."""

    def test_real_repository_does_not_plan_completed_132f(self):
        status = build_architecture_status()
        assert "132F" not in status["planned_phase_ids"]
        assert not any("132F" in p for p in status["planned"])

    def test_real_repository_132f_is_completed_not_planned(self):
        status = build_architecture_status()
        assert "132F" in status["completed_phase_ids"]

    def test_real_repository_track_133_progress_represented(self):
        status = build_architecture_status()
        assert any(pid.startswith("133") for pid in status["completed_phase_ids"])

    def test_real_repository_track_134_progress_represented(self):
        status = build_architecture_status()
        assert any(pid.startswith("134") for pid in status["completed_phase_ids"])

    def test_real_repository_current_phase_identity_exact(self):
        status = build_architecture_status()
        # Whatever the current phase is, it must be a syntactically valid,
        # exactly-preserved identity -- never truncated to a family prefix.
        current_id = status["current_phase_id"]
        assert current_id
        assert is_valid_phase_id(current_id)

    def test_real_repository_validates_clean(self):
        status = build_architecture_status()
        issues = validate_architecture_status(status)
        assert issues == [], issues


# ═══════════════════════════════════════════════════════════════════════
# 3. Recommended-next regex now matches current wording
# ═══════════════════════════════════════════════════════════════════════


class TestPlannedDerivationFixedRegex:
    def test_current_wording_recommended_next_phase_matched(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 134E.8 — Architecture Status Generation Repair (completed).

Recommended next phase: 134E.8V — Architecture Status Generation
Independent Verification.

## Phase 134E.8 Complete

Phase 134E.8 — Architecture Status Generation Repair.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["planned_phase_ids"] == ["134E.8V"]

    def test_no_whole_file_fallback_to_stale_history(self, tmp_path, monkeypatch):
        """A stale historical 'Recommended next repo phase' sentence
        elsewhere in the file must never leak into 'planned' when the
        current section has no recommendation of its own."""
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 134E.8 — Architecture Status Generation Repair (completed).

## Phase 134E.8 Complete

Phase 134E.8 — Architecture Status Generation Repair.

## Phase 132F Complete

Phase 132F — Repository Intelligence Service Independent Verification.

Recommended next repo phase: 132F — Repository Intelligence Service
Independent Verification.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["planned"] == []
        assert status["planned_phase_ids"] == []
        assert any("no explicit" in lim or "Recommended next" in lim for lim in status["limitations"])

    def test_historical_repo_phase_wording_still_matched_in_current_section(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

Recommended next repo phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["planned_phase_ids"] == ["113B"]


# ═══════════════════════════════════════════════════════════════════════
# 4. Completed/planned overlap fails closed
# ═══════════════════════════════════════════════════════════════════════


class TestCompletedPlannedOverlapFailsClosed:
    def test_recommended_phase_already_completed_is_dropped_and_disclosed(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 132F — Repository Intelligence Service Independent Verification (completed).

Recommended next phase: 132F — Repository Intelligence Service
Independent Verification.

## Phase 132F Complete

Phase 132F — Repository Intelligence Service Independent Verification.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["planned_phase_ids"] == []
        assert status["conflicts"]
        assert status["freshness"] == FRESHNESS_INVALID

    def test_validate_architecture_status_rejects_overlap(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": ["132A", "132F"],
            "planned_phase_ids": ["132F"],
            "current_phase_id": "",
            "in_progress": [],
            "completed_chapters": [],
            "current_runtime_state": "Observed",
            "execution_availability": "unavailable",
        }
        issues = validate_architecture_status(status)
        assert any("132F" in i and "completed" in i and "planned" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 5. Exact phase identity: dotted + verification suffix
# ═══════════════════════════════════════════════════════════════════════


class TestPhaseIdentityGrammar:
    @pytest.mark.parametrize("phase_id,expected", [
        ("134E.8", (134, "E", ((8, ""),))),
        ("134E.8V", (134, "E", ((8, "V"),))),
        ("134E.10", (134, "E", ((10, ""),))),
        ("134E.10V", (134, "E", ((10, "V"),))),
        ("134E", (134, "E", ())),
        ("134B.3", (134, "B", ((3, ""),))),
    ])
    def test_parse_phase_id_exact(self, phase_id, expected):
        assert parse_phase_id(phase_id) == expected

    def test_no_prefix_matching(self):
        """134E.10 must never be confused with 134E.1 -- no prefix match."""
        assert parse_phase_id("134E.10") != parse_phase_id("134E.1")

    def test_no_truncation_to_family(self):
        assert parse_phase_id("134E.8V") != parse_phase_id("134E")

    def test_invalid_phase_id_returns_none(self):
        assert parse_phase_id("not-a-phase") is None
        assert parse_phase_id("") is None
        assert parse_phase_id("134") is None  # bare family, no letter

    def test_current_phase_dotted_verification_recognized(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 134E.10V — Some Independent Verification (completed).

## Phase 134E.10V Complete

Phase 134E.10V — Some Independent Verification.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["current_phase_id"] == "134E.10V"


# ═══════════════════════════════════════════════════════════════════════
# 6. Deterministic ordering
# ═══════════════════════════════════════════════════════════════════════


class TestDeterministicOrdering:
    def test_ordering_distinguishes_dotted_and_verification_ids(self):
        ids = ["134E.10V", "134E.2", "134E", "134E.1V", "134E.10", "134E.1", "134E.8"]
        ordered = sorted(ids, key=phase_sort_key)
        assert ordered == ["134E", "134E.1", "134E.1V", "134E.2", "134E.8", "134E.10", "134E.10V"]

    def test_ordering_independent_of_input_order(self):
        ids_a = ["134E.10", "134E.2", "134E.1"]
        ids_b = ["134E.1", "134E.10", "134E.2"]
        assert sorted(ids_a, key=phase_sort_key) == sorted(ids_b, key=phase_sort_key)

    def test_malformed_id_sorts_after_valid_ids_without_reordering_them(self):
        ids = ["134E.2", "not-valid", "134E.1"]
        ordered = sorted(ids, key=phase_sort_key)
        assert ordered == ["134E.1", "134E.2", "not-valid"]

    def test_real_repository_completed_ids_deterministic_across_runs(self):
        first = build_architecture_status()["completed_phase_ids"]
        second = build_architecture_status()["completed_phase_ids"]
        assert first == second
        assert first == sorted(first, key=phase_sort_key)


# ═══════════════════════════════════════════════════════════════════════
# 7. Completed derivation: no scope restriction, no document-existence-alone
# ═══════════════════════════════════════════════════════════════════════


class TestCompletedDerivationRequiresGovernedEvidence:
    def test_all_tracks_with_genuine_headers_included(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 134A — Some Phase (completed).

## Phase 134A Complete

Phase 134A — Canonical Phase Finalization Architecture.

## Phase 132F Complete

Phase 132F — Repository Intelligence Service Independent Verification.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert {"134A", "132F", "113A"}.issubset(set(status["completed_phase_ids"]))

    def test_mention_without_header_not_completed(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture. See also Phase 999Z for
context (999Z has no header of its own here).
""")
        status = _build(tmp_path, monkeypatch)
        assert "999Z" not in status["completed_phase_ids"]

    def test_duplicate_header_deduplicated_not_double_counted(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113V — Repository Transition Validator Verification (completed).

## Phase 113V Complete

Phase 113V — Repository Transition Validator Verification & Compatibility.

## Phase 113V Complete

Phase 113V — Repository Transition Validator Verification & Compatibility.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["completed_phase_ids"].count("113V") == 1

    def test_recommendation_alone_does_not_imply_completion(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

Recommended next phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert "113B" not in status["completed_phase_ids"]


# ═══════════════════════════════════════════════════════════════════════
# 8. No active phase disclosure
# ═══════════════════════════════════════════════════════════════════════


class TestNoActivePhaseDisclosure:
    def test_missing_current_phase_section_discloses_limitation(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["current_phase_id"] == ""
        assert status["in_progress"] == []
        assert any("no active phase" in lim for lim in status["limitations"])
        assert status["freshness"] == FRESHNESS_FRESH_WITH_LIMITATIONS

    def test_missing_project_status_md_is_limited_not_plain_fresh(self, tmp_path, monkeypatch):
        """Phase 134E.9 refinement: an absent source is a disclosed
        limitation, not a detected contradiction -- 'invalid' is reserved
        for genuine conflicts so validate_derived_correctness() can fail
        closed on 'invalid' without also rejecting the legitimate
        bootstrap/explicit-identity scenario (no PROJECT_STATUS.md yet)."""
        monkeypatch.chdir(tmp_path)
        status = build_architecture_status()
        assert status["freshness"] == FRESHNESS_FRESH_WITH_LIMITATIONS
        assert status["limitations"]


# ═══════════════════════════════════════════════════════════════════════
# 9. Freshness states
# ═══════════════════════════════════════════════════════════════════════


class TestFreshnessStates:
    def test_valid_freshness_states_declared(self):
        assert VALID_FRESHNESS_STATES == {
            FRESHNESS_FRESH, FRESHNESS_FRESH_WITH_LIMITATIONS, FRESHNESS_STALE, FRESHNESS_INVALID,
        }

    def test_fresh_when_no_limitations_or_conflicts(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

Recommended next phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["freshness"] == FRESHNESS_FRESH_WITH_LIMITATIONS
        assert any("repository revision unavailable" in item for item in status["limitations"])

    def test_fresh_with_limitations_when_no_plan_disclosed(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["freshness"] == FRESHNESS_FRESH_WITH_LIMITATIONS

    def test_invalid_when_conflicts_present(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

Recommended next phase: 113A — Advisory Runtime Architecture.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["freshness"] == FRESHNESS_INVALID
        assert status["conflicts"]


# ═══════════════════════════════════════════════════════════════════════
# 10. Provenance and state marker
# ═══════════════════════════════════════════════════════════════════════


class TestProvenanceAndStateMarker:
    def test_source_provenance_present(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["source_provenance"]["project_status_md"] == "read"
        assert status["source_provenance"]["current_phase_section"] == "found"

    def test_state_marker_deterministic_for_same_content(self, tmp_path, monkeypatch):
        body = """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
"""
        _write_project_status(tmp_path, body)
        first = _build(tmp_path, monkeypatch)
        second = _build(tmp_path, monkeypatch)
        assert first["state_marker"] == second["state_marker"]
        assert first["state_marker"] != ""

    def test_state_marker_changes_with_content(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        first = _build(tmp_path, monkeypatch)
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113B — Advisory Runtime Contract Freeze (completed).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        second = _build(tmp_path, monkeypatch)
        assert first["state_marker"] != second["state_marker"]


# ═══════════════════════════════════════════════════════════════════════
# 11. Validation API
# ═══════════════════════════════════════════════════════════════════════


class TestValidationAPI:
    def test_unsupported_schema_version_rejected(self):
        status = {"schema_version": "99.9", "completed_phase_ids": [], "planned_phase_ids": []}
        issues = validate_architecture_status(status)
        assert any("schema_version" in i for i in issues)

    def test_invalid_phase_id_syntax_rejected(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": ["not-a-phase-id"],
            "planned_phase_ids": [],
        }
        issues = validate_architecture_status(status)
        assert any("invalid phase-ID syntax" in i for i in issues)

    def test_duplicate_completed_id_rejected(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": ["113A", "113A"],
            "planned_phase_ids": [],
        }
        issues = validate_architecture_status(status)
        assert any("duplicate phase ID" in i for i in issues)

    def test_runtime_observed_with_available_execution_rejected(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": [], "planned_phase_ids": [],
            "current_runtime_state": "Observed",
            "execution_availability": "available",
        }
        issues = validate_architecture_status(status)
        assert any("execution_availability" in i for i in issues)

    def test_fresh_with_conflicts_is_rejected_as_inconsistent(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": [], "planned_phase_ids": [],
            "freshness": FRESHNESS_FRESH,
            "conflicts": ["something is wrong"],
        }
        issues = validate_architecture_status(status)
        assert any("fresh" in i and "conflicts" in i for i in issues)

    def test_valid_status_produces_no_issues(self):
        status = {
            "schema_version": ARCHITECTURE_STATUS_SCHEMA_VERSION,
            "completed_phase_ids": ["113A", "113B"],
            "planned_phase_ids": [],
            "current_phase_id": "113C",
            "in_progress": [],
            "completed_chapters": [
                {"chapter": "113", "label": "x", "phase_ids": ["113A", "113B"]},
            ],
            "current_runtime_state": "Observed",
            "execution_availability": "unavailable",
            "freshness": FRESHNESS_FRESH,
            "conflicts": [],
        }
        assert validate_architecture_status(status) == []

    def test_non_dict_input_reported_not_raised(self):
        assert validate_architecture_status(None) != []  # type: ignore[arg-type]


# ═══════════════════════════════════════════════════════════════════════
# 12. Chapter structure
# ═══════════════════════════════════════════════════════════════════════


class TestChapterStructure:
    def test_completed_chapters_traceable_to_phase_ids(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113B — Advisory Runtime Contract Freeze (completed).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        chapters = {c["chapter"]: c for c in status["completed_chapters"]}
        assert chapters["113"]["phase_ids"] == ["113A", "113B"]

    def test_large_chapter_does_not_produce_unreadable_line(self, tmp_path, monkeypatch):
        """Guards the 134E.8 chapter-label repair: a series with many
        phases must render as a compact, bounded-length summary, never
        an ever-growing concatenation."""
        body_lines = ["# Project Status", "", "## Current Phase", "",
                      "Phase 119Z — Something (completed).", ""]
        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[:20]
        for letter in letters:
            body_lines.append(f"## Phase 119{letter} Complete")
            body_lines.append("")
            body_lines.append(f"Phase 119{letter} — Repository Intelligence Executable Schema Step {letter}.")
            body_lines.append("")
        _write_project_status(tmp_path, "\n".join(body_lines))
        status = _build(tmp_path, monkeypatch)
        chapter = next(c for c in status["completed_chapters"] if c["chapter"] == "119")
        assert len(chapter["label"]) < 200
        assert len(chapter["phase_ids"]) == 20

    def test_no_duplicate_chapter_identity(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.

## Phase 112A Complete

Phase 112A — Runtime Context Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        chapter_ids = [c["chapter"] for c in status["completed_chapters"]]
        assert len(chapter_ids) == len(set(chapter_ids))


# ═══════════════════════════════════════════════════════════════════════
# 13. Repository Intelligence independence
# ═══════════════════════════════════════════════════════════════════════


class TestRepositoryIntelligenceIndependence:
    def test_build_architecture_status_does_not_import_unified_query(self):
        import inspect
        import pcae.core.phase_reports as pr_mod
        source = inspect.getsource(pr_mod.build_architecture_status)
        assert "unified_query" not in source.lower()
        assert "repository_intelligence" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════
# 14. Inactive-subsystem confirmation (Strict Non-Goals)
# ═══════════════════════════════════════════════════════════════════════


class TestInactiveSubsystemsUnchanged:
    def test_delivery_receipt_store_not_imported_by_build(self):
        import inspect
        import pcae.core.phase_reports as pr_mod
        source = inspect.getsource(pr_mod.build_architecture_status)
        assert "delivery_receipt" not in source.lower()
        assert "delivery_pipeline" not in source.lower()
        assert "rendering" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════
# 15. Existing consistency check (validate_phase_identity) stays wired
# ═══════════════════════════════════════════════════════════════════════


class TestExistingConsistencyCheckStillFires:
    def test_completed_and_planned_overlap_still_blocks_finalization(self):
        from pcae.core.phase_reports import validate_phase_identity
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": ["x"], "completed_phase_ids": ["113C"],
            "in_progress": [], "planned": ["113C — Something"],
            "current_runtime_state": "Observed", "current_maximum_capability": "observe",
            "execution_availability": "unavailable",
        }
        issues = validate_phase_identity(report, "113D", {})
        assert any("113C" in i and "completed" in i and "planned" in i for i in issues)
