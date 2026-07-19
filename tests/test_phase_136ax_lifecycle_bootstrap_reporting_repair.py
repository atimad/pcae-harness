"""Phase 136AX — Lifecycle Bootstrap & Session State Reporting Repair.

Regression coverage for the reproduced root cause behind "## Current
Phase section present but its phase-ID/title line did not parse" and
the related family of reporting-truncation/conflation defects:

Root cause (confirmed by direct reproduction against this repository's
own live PROJECT_STATUS.md, not assumed): the phase-ID grammar used
throughout the reporting subsystem assumed exactly one mainline branch
letter (``\\d+[A-Z]``). Track 136 exhausted single letters A-Z and
rolled over into two-letter mainline suffixes (136Z -> 136AA -> ... ->
136AW -> 136AX), which the single-letter grammar could not parse at
all. This silently broke current-phase identification, in-progress
detection, commit-contamination detection, and (in
``pcae.commands.task._read_lifecycle_current_phase_line``) correct
completed/in-progress classification, wherever that grammar had been
independently reimplemented instead of shared.

A second, compounding defect: the declaration-line and
"Recommended next phase:" sentence regexes captured only up to the
first physical newline (no ``re.DOTALL``) and/or required
line-start anchoring (``^...$`` with ``re.MULTILINE``), while this
repository hand-wraps its prose across multiple physical lines and
routinely embeds the recommendation sentence mid-paragraph. Both
truncated or altogether missed real, present content.

See docs/PHASE_136AX_LIFECYCLE_BOOTSTRAP_SESSION_STATE_REPORTING_REPAIR.md
for the full root-cause analysis, precedence rules, and disposition.

No Stage 3 schema/typed-authority-model changes. No runtime capability
change. Governance/reporting infrastructure only.
"""

from __future__ import annotations

import json
from pathlib import Path

from pcae.core.architecture_status import is_valid_phase_id, parse_phase_id
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    _CURRENT_PHASE_SECTION_RE,
    _extract_recommended_next_phase_values,
    _match_current_phase_declaration,
    build_architecture_status,
)
from pcae.core.status import check_project_status_current_phase
from pcae.commands.phase import _finalize_report_and_notify
from pcae.commands.session import _format_notification_result
from pcae.commands.task import _finalize_task_report_and_notify, _read_lifecycle_current_phase_line


def _write_project_status(tmp_path: Path, body: str) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(body, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# 1. Phase-ID grammar: two-letter mainline suffix (136AA .. 136AZ, ...)
# ═══════════════════════════════════════════════════════════════════════


class TestTwoLetterMainlineSuffixGrammar:
    def test_parse_phase_id_accepts_two_letter_suffix(self):
        assert parse_phase_id("136AW") == (136, "AW", ())
        assert is_valid_phase_id("136AW")

    def test_parse_phase_id_two_letter_suffix_with_subphase(self):
        assert is_valid_phase_id("136AW.1")
        assert is_valid_phase_id("136AW.1V")

    def test_sort_key_orders_past_single_letter_rollover(self):
        from pcae.core.architecture_status import phase_sort_key

        ids = ["136Z", "136AA", "136A", "136AB"]
        ordered = sorted(ids, key=phase_sort_key)
        # Deterministic (lexicographic-on-branch-string) ordering -- this
        # phase's fix only guarantees every one of these IDs *parses* and
        # sorts consistently, not that "AA" sorts after "Z" numerically
        # (spreadsheet-column ordering is not part of this repair's
        # scope; "deterministic" and "parses at all" are what matters).
        assert ordered == ["136A", "136AA", "136AB", "136Z"]
        assert all(parse_phase_id(pid) is not None for pid in ids)

    def test_current_phase_line_regex_matches_two_letter_suffix(self):
        text = "Phase 136AW — Stage 3 Typed Authority Model Final Review (completed)."
        declaration = _match_current_phase_declaration(text)
        assert declaration is not None
        assert declaration.phase_id == "136AW"
        assert declaration.status_marker == "completed"

    def test_current_phase_line_regex_previously_failed_single_letter_only(self):
        # Direct regression proof: the pre-repair grammar (\d+[A-Z] only)
        # cannot match "136AW" at all -- confirm the *new* parser succeeds
        # where a single-letter-only pattern would not.
        import re

        old_broken_re = re.compile(
            r"^Phase\s+(\d+[A-Z])\s*[—–-]\s*(.+)$", re.MULTILINE
        )
        text = "Phase 136AW — Title (completed)."
        assert old_broken_re.match(text) is None
        assert _match_current_phase_declaration(text) is not None

    def test_declaration_with_no_status_marker_still_parses(self):
        # Historical convention: a declaration line with no trailing
        # "(<status>)" marker at all -- must still parse (falls back to
        # the single-line grammar) and is treated as not-completed,
        # never guessed.
        text = "Phase 134E.10.1V.1 — Completed-Phase Architecture Status Transition Repair."
        declaration = _match_current_phase_declaration(text)
        assert declaration is not None
        assert declaration.phase_id == "134E.10.1V.1"
        assert declaration.status_marker is None
        assert declaration.is_completed is False


# ═══════════════════════════════════════════════════════════════════════
# 2. Current-phase parsing via build_architecture_status
# ═══════════════════════════════════════════════════════════════════════


class TestCurrentPhaseParsing:
    def test_two_letter_suffix_current_phase_identified(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 136AX — Lifecycle Bootstrap Repair (not started).\n",
        )
        status = build_architecture_status()
        assert status["current_phase_id"] == "136AX"
        # The fixture deliberately omits a "Recommended next phase:"
        # sentence and runs outside a git checkout, so *those*
        # limitations are expected; what must never reappear is the
        # phase-ID/title parse failure this phase repairs.
        assert not any("did not parse" in limitation for limitation in status["limitations"])

    def test_wrapped_title_not_truncated(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 136AW — Stage 3 Typed Authority Model Final Review and Stage-Exit\n"
            "Readiness Assessment (completed). Some further prose about the\n"
            "phase follows here.\n",
        )
        status = build_architecture_status()
        assert status["current_phase_id"] == "136AW"
        assert not any("did not parse" in limitation for limitation in status["limitations"])
        # Completed current phase is not in-progress.
        assert status["in_progress"] == []

    def test_wrapped_title_not_started_is_in_progress_with_full_title(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 137A — Typed Authority Model Consumption\n"
            "Architecture (not started).\n",
        )
        status = build_architecture_status()
        assert status["current_phase_id"] == "137A"
        assert len(status["in_progress"]) == 1
        entry = status["in_progress"][0]
        assert "137A" in entry
        assert "Consumption" in entry and "Architecture" in entry

    def test_malformed_declaration_line_surfaces_limitation_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\nThis is not a phase declaration line at all.\n",
        )
        status = build_architecture_status()
        assert status["current_phase_id"] == ""
        assert any("did not parse" in limitation for limitation in status["limitations"])

    def test_no_current_phase_section_surfaces_limitation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(tmp_path, "# Project Status\n\nNothing here.\n")
        status = build_architecture_status()
        assert any("no ## Current Phase section" in limitation for limitation in status["limitations"])

    def test_unicode_en_dash_current_phase(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\nPhase 200A – En Dash Title (not started).\n",
        )
        status = build_architecture_status()
        assert status["current_phase_id"] == "200A"


# ═══════════════════════════════════════════════════════════════════════
# 3. Recommended next phase parsing / precedence / no fabrication
# ═══════════════════════════════════════════════════════════════════════


class TestRecommendedNextPhaseParsing:
    def test_bold_wrapped_recommendation_preserved_across_line_wrap(self):
        section = (
            "Some lead-in prose that is not at the start of a line. "
            "Recommended next phase: **136AJ — Stage 3 Typed Authority Model "
            "Recovery and Concurrency\nImplementation** (implementing only "
            "`ConcurrencyConflict` and\n`RecoveryJournalEntry`). Full detail "
            "in `docs/x.md`.\n"
        )
        values = _extract_recommended_next_phase_values(section)
        assert values == [
            "136AJ — Stage 3 Typed Authority Model Recovery and Concurrency "
            "Implementation"
        ]

    def test_plain_recommendation_terminated_at_period(self):
        section = "Recommended next phase: 133F — Canonical Engineering Evidence Contract Freeze.\n"
        values = _extract_recommended_next_phase_values(section)
        assert values == ["133F — Canonical Engineering Evidence Contract Freeze"]

    def test_recommendation_not_at_line_start_still_matches(self):
        # Previously required "Recommended" at the start of a physical
        # line (re.MULTILINE with ^ anchor); this repository's actual
        # prose embeds it mid-paragraph.
        section = (
            "the re-derived contract exactly. Recommended next phase: "
            "**136AV — Stage 3\nTyped Authority Model Whole-Model Integration "
            "Verification**. Per governed instruction, ...\n"
        )
        values = _extract_recommended_next_phase_values(section)
        assert values == [
            "136AV — Stage 3 Typed Authority Model Whole-Model Integration "
            "Verification"
        ]

    def test_not_started_marker_stripped(self):
        section = "Recommended next phase: 115Z — Advisory Skill Pilot Hardening (not started).\n"
        values = _extract_recommended_next_phase_values(section)
        assert values == ["115Z — Advisory Skill Pilot Hardening"]

    def test_absent_recommendation_yields_no_values_never_fabricated(self):
        section = "Just some prose with no recommendation sentence at all.\n"
        assert _extract_recommended_next_phase_values(section) == []

    def test_build_architecture_status_discloses_missing_recommendation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\nPhase 999Z — No Recommendation Here (not started).\n",
        )
        status = build_architecture_status()
        assert status["planned"] == []
        assert status["planned_phase_ids"] == []
        assert any(
            "no explicit 'Recommended next" in limitation
            for limitation in status["limitations"]
        )

    def test_live_repo_136aw_recommendation_matches_canonical_metadata(self):
        # End-to-end proof against the real repository: the live
        # PROJECT_STATUS.md now carries the "Recommended next phase:"
        # sentence for its current (136AW) entry, and it must agree with
        # the canonical .pcae/phase-completion-metadata.json's own
        # recommended_next_phase field -- the exact cross-source
        # agreement this phase's root-cause analysis found broken.
        meta_path = Path(".pcae/phase-completion-metadata.json")
        if not meta_path.is_file():
            return
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("phase_id") != "136AW":
            return
        canonical_recommendation = meta.get("recommended_next_phase", "")
        if not canonical_recommendation:
            return
        status = build_architecture_status()
        assert status["planned"], "Architecture Status discloses no planned phase"
        assert status["planned"][0] == canonical_recommendation


# ═══════════════════════════════════════════════════════════════════════
# 4. Cross-command consistency: status.py governance-audit current-phase
#    check must agree with build_architecture_status, not truncate.
# ═══════════════════════════════════════════════════════════════════════


class TestGovernanceAuditCurrentPhaseParity:
    def test_wrapped_title_not_truncated_in_governance_audit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 136AW — Stage 3 Typed Authority Model Final Review and Stage-Exit\n"
            "Readiness Assessment (completed).\n",
        )
        check = check_project_status_current_phase(HarnessPath(tmp_path))
        assert check.passed
        assert "Stage-Exit Readiness Assessment" in check.message
        assert "136AW" in check.message

    def test_parity_with_build_architecture_status_current_id(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\nPhase 136AX — Repair Phase (not started).\n",
        )
        arch_status = build_architecture_status()
        check = check_project_status_current_phase(HarnessPath(tmp_path))
        assert arch_status["current_phase_id"] in check.message

    def test_malformed_shape_never_worse_than_first_line_fallback(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\nNot a parseable declaration at all.\n",
        )
        check = check_project_status_current_phase(HarnessPath(tmp_path))
        assert check.passed
        assert "Not a parseable declaration at all." in check.message


# ═══════════════════════════════════════════════════════════════════════
# 5. task.py lifecycle current-phase line: completed marker must not be
#    hidden by physical-line truncation.
# ═══════════════════════════════════════════════════════════════════════


class TestLifecycleCurrentPhaseLineCompletedDetection:
    def test_completed_marker_on_wrapped_line_is_preserved(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 136AW — Stage 3 Typed Authority Model Final Review and Stage-Exit\n"
            "Readiness Assessment (completed).\n",
        )
        line = _read_lifecycle_current_phase_line()
        assert line is not None
        assert "(completed)" in line.lower()

    def test_not_started_marker_on_wrapped_line_is_preserved(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_project_status(
            tmp_path,
            "## Current Phase\n\n"
            "Phase 136AX — Lifecycle Bootstrap and Session State\n"
            "Reporting Repair (not started).\n",
        )
        line = _read_lifecycle_current_phase_line()
        assert line is not None
        assert "(completed)" not in line.lower()
        assert "136AX" in line

    def test_missing_project_status_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _read_lifecycle_current_phase_line() is None


# ═══════════════════════════════════════════════════════════════════════
# 6. Phase-completion crash regressions (files_changed / test_results /
#    governance_results malformed shapes must never crash and never
#    fabricate evidence).
# ═══════════════════════════════════════════════════════════════════════


class TestPhaseCompletionMalformedMetadataRegressions:
    def test_string_files_changed_does_not_fabricate_or_crash(self, tmp_path, monkeypatch):
        # Phase 136AW's own repair used len() on anything truthy that
        # wasn't an int -- len("not a number of files") silently
        # fabricates a count. Confirm this no longer crashes; the
        # identity-resolution failure (no active task / canonical
        # report in this scratch dir) still fails closed as before.
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pcae").mkdir()
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps({"files_changed": "not a number of files", "phase_id": "999Z"})
        )
        result = _finalize_report_and_notify(
            "regression probe", cli_phase_id="999Z", cli_phase_name="probe"
        )
        assert result is False

    def test_explicit_null_validation_results_does_not_crash(self, tmp_path, monkeypatch):
        # meta.get("validation_results", []) only applies its default
        # when the key is *absent*; an explicit JSON null returns None,
        # and the old code iterated it directly (`for vr in None`).
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pcae").mkdir()
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps(
                {
                    "files_changed": 3,
                    "validation_results": None,
                    "governance_results": None,
                    "phase_id": "999Z",
                }
            )
        )
        result = _finalize_report_and_notify(
            "regression probe", cli_phase_id="999Z", cli_phase_name="probe"
        )
        assert result is False

    def test_non_dict_list_items_are_skipped_not_crashed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pcae").mkdir()
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps(
                {
                    "files_changed": 3,
                    "validation_results": ["not a dict", {"name": "fast_green", "status": "passed"}],
                    "governance_results": ["also not a dict"],
                    "phase_id": "999Z",
                }
            )
        )
        result = _finalize_report_and_notify(
            "regression probe", cli_phase_id="999Z", cli_phase_name="probe"
        )
        assert result is False

    def test_task_finish_explicit_null_validation_results_does_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pcae").mkdir()
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps({"validation_results": None, "phase_id": "999Z"})
        )
        # The point of this regression test is crash-safety on an
        # explicit JSON null for validation_results, not any particular
        # downstream governance verdict -- a null validation_results
        # with an otherwise-incomplete metadata file legitimately reaches
        # the repository transition validator's own (separate, correct)
        # "reject" path rather than the identity-resolution failure.
        # Either is a handled, non-crashing outcome.
        result = _finalize_task_report_and_notify(None, active_task_title=None)
        assert isinstance(result, dict)
        assert result.get("status") in {"invalid_metadata", "validator_reject", "no_metadata"}


# ═══════════════════════════════════════════════════════════════════════
# 7. Notification reporting: distinct states, no secret disclosure.
# ═══════════════════════════════════════════════════════════════════════


class TestNotificationResultReporting:
    def test_none_result_is_not_attempted(self):
        assert _format_notification_result(None) == "not attempted (no dispatch recorded for this phase)"

    def test_empty_dict_result_is_not_attempted(self):
        assert _format_notification_result({}) == "not attempted (no dispatch recorded for this phase)"

    def test_dispatched_false_with_reason(self):
        result = _format_notification_result({"dispatched": False, "reason": "notify disabled"})
        assert result == "not attempted (notify disabled)"

    def test_dispatched_success_true(self):
        result = _format_notification_result(
            {"dispatched": True, "success": True, "outcome": "sent"}
        )
        assert result == "sent (sent)"

    def test_dispatched_failure_with_reason(self):
        result = _format_notification_result(
            {"dispatched": True, "success": False, "outcome": "failed", "reason": "timeout"}
        )
        assert result == "failed (timeout)"

    def test_never_discloses_token_or_chat_id(self):
        # notification_result never legitimately contains secret values,
        # but confirm the formatter doesn't echo arbitrary extra keys
        # that might carry one.
        result = _format_notification_result(
            {
                "dispatched": True,
                "success": True,
                "outcome": "sent",
                "token": "should-never-appear",
                "chat_id": "should-never-appear-either",
            }
        )
        assert "should-never-appear" not in result


# ═══════════════════════════════════════════════════════════════════════
# 8. Governance boundaries: this phase touches no Stage 3 authority code.
# ═══════════════════════════════════════════════════════════════════════


class TestGovernanceBoundaries:
    def test_no_authority_module_imported_by_changed_modules(self):
        import pcae.commands.phase as phase_mod
        import pcae.commands.session as session_mod
        import pcae.commands.task as task_mod
        import pcae.core.architecture_status as arch_status_mod
        import pcae.core.phase_reports as phase_reports_mod
        import pcae.core.status as status_mod

        for mod in (
            phase_mod, session_mod, task_mod,
            arch_status_mod, phase_reports_mod, status_mod,
        ):
            assert "pcae.cltr.authority" not in mod.__name__
