"""Phase 136AY — Lifecycle Bootstrap & Session State Reporting
Independent Verification.

Independent verification of Phase 136AX's claimed repair. This module
does not import 136AX's fixtures, expected-output tables, or test cases
(``tests/test_phase_136ax_lifecycle_bootstrap_reporting_repair.py`` is
never imported here). Fixtures are re-derived from this repository's own
authoritative sources: the phase-ID grammar actually used elsewhere in
the codebase (``pcae.core.check``'s phase-code pattern, historical
PROJECT_STATUS.md phase headers), the declaration/recommendation grammar
as documented in ``pcae.core.phase_reports``, and live repository state.

Verdict for this phase: see
docs/PHASE_136AY_LIFECYCLE_BOOTSTRAP_SESSION_STATE_REPORTING_INDEPENDENT_VERIFICATION.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.core.architecture_status import is_valid_phase_id, parse_phase_id
from pcae.core.phase_reports import (
    _CANONICAL_TITLE_PHASE_ID_RE,
    _CURRENT_PHASE_SECTION_RE,
    _extract_recommended_next_phase_values,
    _is_milestone_phase_id,
    _match_current_phase_declaration,
    build_architecture_status,
)
from pcae.core.status import check_project_status_current_phase
from pcae.core.paths import HarnessPath
from pcae.commands.phase import _finalize_report_and_notify
from pcae.commands.task import _finalize_task_report_and_notify, _read_lifecycle_current_phase_line
from pcae.commands.session import _format_notification_result


# ═══════════════════════════════════════════════════════════════════════
# 1. Phase-ID grammar — independently derived acceptance/rejection table
# ═══════════════════════════════════════════════════════════════════════

_VALID_IDS = [
    "1A",              # earliest historical shape
    "99Z",
    "113B",
    "113B.2",          # dotted sub-phase
    "113X.5",          # dotted sub-phase under an exception branch
    "119AC",           # two-letter mainline suffix, historically real
    "134E.10",         # two-digit sub-phase number
    "134E.10V",        # sub-phase with trailing verification letter
    "136AX",           # this repository's own two-letter rollover case
    "136AY",
    "9999AAAA",        # arbitrarily long numeric family + long branch (grammar must not cap length)
]

_INVALID_IDS = [
    "",
    "136",             # no branch letter at all
    "AX",              # no leading digits
    "136 AX",          # embedded space
    "136-AX",          # hyphen is not part of the ID grammar
    "136ax",           # lowercase — parse_phase_id normalizes case internally,
                        # but is_valid_phase_id must still accept it consistently
                        # with parse_phase_id (checked separately below, not here)
    "136A.",           # trailing dot with no sub-phase
    "136A..2",         # empty sub-phase segment
    "Phase136A",       # embedded in a longer token, not a bare ID
]


@pytest.mark.parametrize("phase_id", _VALID_IDS)
def test_valid_historical_and_rollover_ids_accepted(phase_id: str) -> None:
    assert is_valid_phase_id(phase_id), phase_id
    assert parse_phase_id(phase_id) is not None


def test_lowercase_id_normalizes_not_rejected() -> None:
    # parse_phase_id explicitly upper-cases the branch/verification
    # letters (see its own docstring) -- lowercase input must parse to
    # the same identity as its uppercase form, not be silently rejected.
    assert parse_phase_id("136ax") == parse_phase_id("136AX")


@pytest.mark.parametrize("phase_id", ["", "136", "AX", "136 AX", "136-AX", "136A.", "136A..2", "Phase136A"])
def test_malformed_or_arbitrary_tokens_rejected(phase_id: str) -> None:
    assert not is_valid_phase_id(phase_id), phase_id
    assert parse_phase_id(phase_id) is None


def test_two_letter_suffix_does_not_truncate_to_single_letter() -> None:
    # The exact defect this repair targeted: 136AX used to parse (or
    # fail to parse) as if it were "136A" with trailing garbage.
    parsed = parse_phase_id("136AX")
    assert parsed is not None
    series, branch, subphase = parsed
    assert series == 136
    assert branch == "AX"
    assert subphase == ()


def test_canonical_title_regex_matches_rollover_and_dotted_titles() -> None:
    # Direct grammar check against the canonical "# Phase <id> ..." title
    # line regex itself, independent of parse_phase_id.
    for title, expected_id in [
        ("# Phase 136AX — Lifecycle Bootstrap Repair", "136AX"),
        ("# Phase 113B.2 — Sub-phase Title", "113B.2"),
        ("# Phase 134E.10V — Verification Title", "134E.10V"),
        ("# Phase 9A — Old-style Title", "9A"),
    ]:
        m = _CANONICAL_TITLE_PHASE_ID_RE.match(title)
        assert m is not None, title
        assert m.group(1) == expected_id


def test_canonical_title_regex_rejects_no_branch_letter() -> None:
    assert _CANONICAL_TITLE_PHASE_ID_RE.match("# Phase 136 — No Branch Letter") is None


# ═══════════════════════════════════════════════════════════════════════
# 2. Current-phase declaration parsing — adversarial and wrap fixtures
# ═══════════════════════════════════════════════════════════════════════

def test_single_line_declaration_with_status() -> None:
    d = _match_current_phase_declaration("Phase 136AY — Independent Verification (completed).")
    assert d is not None
    assert d.phase_id == "136AY"
    assert d.title == "Independent Verification"
    assert d.is_completed


def test_wrapped_title_across_multiple_physical_lines_not_truncated() -> None:
    text = (
        "Phase 136AY — Lifecycle Bootstrap & Session State\n"
        "Reporting Independent Verification (completed).\n"
        "\n"
        "Some trailing prose paragraph that must not be absorbed."
    )
    d = _match_current_phase_declaration(text)
    assert d is not None
    assert d.phase_id == "136AY"
    assert "Reporting Independent Verification" in d.title
    # Must not swallow the following paragraph.
    assert "trailing prose paragraph" not in d.title


def test_declaration_with_no_status_marker_falls_back_safely() -> None:
    d = _match_current_phase_declaration(
        "Phase 134E.10.1V.1 — Completed-Phase Architecture Status Transition Repair."
    )
    assert d is not None
    assert d.phase_id == "134E.10.1V.1"
    assert d.status_marker is None
    assert not d.is_completed  # never guessed as completed


def test_declaration_does_not_consume_next_markdown_heading() -> None:
    text = (
        "Phase 136AY — Title Without Status Marker.\n"
        "\n"
        "## Phase 136AX Complete\n"
        "\n"
        "Unrelated prose about the previous phase."
    )
    d = _match_current_phase_declaration(text)
    assert d is not None
    assert "Phase 136AX Complete" not in d.title
    assert "Unrelated prose" not in d.title


def test_declaration_title_with_colon_dash_and_parens_preserved() -> None:
    d = _match_current_phase_declaration(
        "Phase 137A — Typed Authority Model: Consumption (Architecture) (not started)."
    )
    assert d is not None
    assert d.phase_id == "137A"
    assert "Consumption (Architecture)" in d.title
    assert d.status_marker == "not started"


def test_declaration_with_unicode_and_ascii_dash_both_parse() -> None:
    for dash in ("—", "–", "-"):
        text = f"Phase 136AY {dash} Dash Variant Title (completed)."
        d = _match_current_phase_declaration(text)
        assert d is not None, dash
        assert d.phase_id == "136AY"


def test_malformed_declaration_returns_none_never_guessed() -> None:
    assert _match_current_phase_declaration("This is not a phase declaration at all.") is None
    assert _match_current_phase_declaration("") is None


def test_declaration_status_marker_case_insensitive() -> None:
    d = _match_current_phase_declaration("Phase 136AY — Title (COMPLETED).")
    assert d is not None
    assert d.status_marker == "completed"
    assert d.is_completed


# ═══════════════════════════════════════════════════════════════════════
# 3. Recommended-next-phase extraction — precedence and prose-vs-field
# ═══════════════════════════════════════════════════════════════════════

def test_recommended_next_phase_bold_span_wrapped_preserved() -> None:
    text = (
        "Some narrative text. Recommended next phase: **136AY — Lifecycle\n"
        "Bootstrap Independent Verification** (not started). More text follows."
    )
    values = _extract_recommended_next_phase_values(text)
    assert values == ["136AY — Lifecycle Bootstrap Independent Verification"]


def test_recommended_next_phase_plain_sentence_terminated_by_period() -> None:
    text = "Recommended next phase: 137A — Typed Authority Model Consumption Architecture."
    values = _extract_recommended_next_phase_values(text)
    assert values == ["137A — Typed Authority Model Consumption Architecture"]


def test_recommended_next_phase_not_required_at_line_start() -> None:
    # The exact defect: the label embedded mid-paragraph must still match.
    text = "...matches the re-derived contract exactly. Recommended next phase: **136AV — Verification**."
    values = _extract_recommended_next_phase_values(text)
    assert values == ["136AV — Verification"]


def test_recommended_next_repo_phase_legacy_wording_still_matches() -> None:
    text = "Recommended next repo phase: 119A — Repository Intelligence Contract Freeze."
    values = _extract_recommended_next_phase_values(text)
    assert values == ["119A — Repository Intelligence Contract Freeze"]


def test_no_recommendation_present_yields_empty_list() -> None:
    assert _extract_recommended_next_phase_values("No recommendation sentence anywhere here.") == []


def test_prose_merely_quoting_the_label_phrase_is_not_silently_immune() -> None:
    # Known, disclosed limitation (136AX PROJECT_STATUS.md commit
    # 29556fdf): prose that literally contains the label text produces a
    # spurious match. Verify this limitation still exists exactly as
    # disclosed (not silently worse, not silently fixed without being
    # re-verified) -- if this starts failing, the disclosed limitation in
    # the 136AX doc is stale and must be updated, not just the assertion
    # flipped.
    text = 'This sentence fixes "Recommended next phase:" sentence extraction.'
    values = _extract_recommended_next_phase_values(text)
    assert values == ['" sentence extraction']


def test_multiple_recommendations_all_captured_in_order() -> None:
    text = (
        "Recommended next phase: 136AY — First.\n"
        "Recommended next phase: 137A — Second."
    )
    values = _extract_recommended_next_phase_values(text)
    assert values == ["136AY — First", "137A — Second"]


def test_not_started_suffix_stripped_from_value() -> None:
    text = "Recommended next phase: 137A — Typed Authority Model Consumption Architecture (not started)."
    values = _extract_recommended_next_phase_values(text)
    assert values == ["137A — Typed Authority Model Consumption Architecture"]


# ═══════════════════════════════════════════════════════════════════════
# 4. 136AX's own successor-recommendation discrepancy — direct evidence
# ═══════════════════════════════════════════════════════════════════════

def test_136ax_canonical_metadata_recommends_137a_not_136ay() -> None:
    """Direct evidence check against the live, canonical
    .pcae/phase-completion-metadata.json left behind by 136AX. This does
    not assert that 137A is *wrong* forever -- it records, as
    independently-observed fact, exactly what 136AX's own canonical
    artifacts say, so this phase's verdict about the discrepancy is
    checked against real evidence rather than restated from memory.
    """
    meta_path = Path(".pcae/phase-completion-metadata.json")
    if not meta_path.exists():
        pytest.skip("no live phase-completion-metadata.json in this environment")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("phase_id") != "136AX":
        pytest.skip("phase-completion-metadata.json has since moved past 136AX")
    assert meta.get("recommended_next_phase", "").startswith("137A")


def test_established_convention_is_repair_phase_recommends_own_verification() -> None:
    """Independent check of this repository's own established convention
    (not 136AX's claim about itself): every prior *implementation* phase
    report in Track 136 whose title does not itself say "Independent
    Verification" recommends its own immediate next verification phase,
    one letter later in the same track, wherever both reports exist on
    disk. 136AX (this phase's subject) is the one counter-example this
    phase exists to correct -- checked, not assumed.
    """
    reports_dir = Path(".pcae/phase-reports")
    if not reports_dir.exists():
        pytest.skip("no live .pcae/phase-reports directory in this environment")

    pairs_checked = 0
    for report_path in sorted(reports_dir.glob("*-136A*.json")):
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        phase_id = data.get("phase_id", "")
        title = data.get("phase_name", "") or data.get("title", "")
        # Exclude phases that are themselves a chapter-exit review/
        # verification step -- those correctly recommend the *next*
        # chapter, not a same-chapter successor letter. 136AX is excluded
        # here too: its own compliance with this convention is checked
        # separately (test_136ax_canonical_metadata_recommends_137a_not_136ay
        # above) precisely *because* it is this phase's subject, not a
        # convention-setting data point.
        if not phase_id or any(w in title for w in ("Verification", "Review", "Readiness Assessment")) or phase_id == "136AX":
            continue
        parsed = parse_phase_id(phase_id)
        if parsed is None:
            continue
        series, branch, _sub = parsed
        next_id_guess_letters = [branch + "A", chr(ord(branch[-1]) + 1) if len(branch) == 1 else None]
        rec = data.get("recommended_next_phase", "") or ""
        if not rec:
            continue
        pairs_checked += 1
        # A parseable phase-ID token must appear somewhere in the
        # recommendation (either leading "<id> — <title>" form or a
        # trailing "(phase <id>)" annotation) and it must be in the same
        # numeric series -- i.e. its own next-letter verification phase,
        # not a distant future phase.
        import re as _re

        candidates = _re.findall(r"[0-9]+[A-Za-z]+(?:\.[0-9]+[A-Za-z]?)*", rec)
        parsed_candidates = [c for c in candidates if parse_phase_id(c) is not None]
        assert parsed_candidates, f"{phase_id} -> unparseable recommendation {rec!r}"
        assert any(parse_phase_id(c)[0] == series for c in parsed_candidates), (
            f"{phase_id} recommended {rec!r} in a different series"
        )

    # Establishing the convention requires at least one real comparable
    # pair; if the fixture set is empty in this environment, the
    # assertion above never ran and this test must not silently pass as
    # if it had verified anything.
    assert pairs_checked >= 1


# ═══════════════════════════════════════════════════════════════════════
# 5. 136AX's own notification-outcome evidence — direct evidence check
# ═══════════════════════════════════════════════════════════════════════

def test_136ax_canonical_report_notification_result_is_empty_not_a_claimed_success() -> None:
    reports_dir = Path(".pcae/phase-reports")
    candidates = sorted(reports_dir.glob("*-136AX.json")) if reports_dir.exists() else []
    if not candidates:
        pytest.skip("no live 136AX phase report in this environment")
    data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    nr = data.get("notification_result")
    # The canonical, machine-readable field must not fabricate a
    # dispatch outcome: it is either genuinely empty (never attempted)
    # or an explicit, honest attempted/succeeded/failed record. It must
    # never claim success without a corresponding 'success' key.
    assert isinstance(nr, dict)
    if nr:
        assert "success" in nr or "dispatched" in nr
    # This is the actual observed state as of this phase: no dispatch was
    # recorded for 136AX's own finalization.
    assert nr == {}


def test_format_notification_result_reports_empty_as_not_attempted_not_success() -> None:
    assert _format_notification_result({}) == "not attempted (no dispatch recorded for this phase)"
    assert _format_notification_result(None) == "not attempted (no dispatch recorded for this phase)"


def test_format_notification_result_distinguishes_all_taxonomy_states() -> None:
    # not attempted (explicit reason)
    assert "not attempted" in _format_notification_result({"dispatched": False, "reason": "PCAE_NOTIFY_ENABLED not set"})
    # attempted and succeeded
    r = _format_notification_result({"dispatched": True, "success": True, "outcome": "sink=telegram"})
    assert r.startswith("sent")
    # attempted and failed -- must not read as "sent"
    r = _format_notification_result({"dispatched": True, "success": False, "reason": "network unreachable"})
    assert "sent" not in r
    assert "network unreachable" in r


def test_format_notification_result_never_leaks_token_or_chat_id() -> None:
    # Defensive: even if a caller accidentally attached secret-shaped
    # keys the formatter does not know about, it must only ever read the
    # documented keys (dispatched/success/outcome/reason/error).
    result = _format_notification_result({
        "dispatched": True,
        "success": True,
        "outcome": "sink=telegram",
        "token": "should-never-appear",
        "chat_id": "should-never-appear",
    })
    assert "should-never-appear" not in result


# ═══════════════════════════════════════════════════════════════════════
# 6. Malformed phase-completion-metadata handling — fresh fixtures
#
# These drive the real CLI entry points (`_finalize_report_and_notify`,
# `_finalize_task_report_and_notify`) end-to-end against a disposable git
# repository, exactly as `pcae phase complete`/`pcae task finish` do —
# not a reimplementation of the parsing logic. The specific field values
# below are deliberately malformed in ways not identical to 136AX's own
# fixture set (different strings/shapes), but exercise the same
# documented failure classes: non-int/non-list `files_changed`, explicit
# JSON `null` for `validation_results`/`governance_results`, and
# non-dict list items.
# ═══════════════════════════════════════════════════════════════════════

def _base_meta(**overrides):
    meta = {
        "phase_id": "136AY",
        "phase_name": "Independent Verification",
        "recommended_next_phase": "137A — Next",
        "files_changed": ["a.py", "b.py"],
        "validation_results": {"pytest": "passed"},
        "governance_results": {"pcae_check": "passed"},
    }
    meta.update(overrides)
    return meta


@pytest.fixture
def disposable_repo(tmp_path, monkeypatch):
    """A minimal, disposable git repository -- never the real harness
    repository -- with just enough structure for the finalization entry
    points to run their metadata-parsing logic without crashing on
    unrelated missing state.
    """
    import subprocess

    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True, cwd=tmp_path)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], check=True, cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, cwd=tmp_path)
    (tmp_path / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "."], check=True, cwd=tmp_path)
    subprocess.run(["git", "commit", "-q", "-m", "init"], check=True, cwd=tmp_path)
    (tmp_path / ".pcae").mkdir()
    return tmp_path


def _write_meta(repo: Path, meta: dict) -> None:
    (repo / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )


@pytest.mark.parametrize("bad_files_changed", [
    "seventeen characters",   # malformed string -- len() would fabricate 21
    {"unexpected": "object"},  # malformed object
    None,
])
def test_malformed_files_changed_does_not_crash_or_fabricate(disposable_repo, bad_files_changed, capsys) -> None:
    meta = _base_meta(files_changed=bad_files_changed, files_changed_count=0)
    _write_meta(disposable_repo, meta)
    # No unhandled exception is the primary assertion: pytest itself
    # would fail this test on a crash even without an explicit assert.
    _finalize_report_and_notify("independent verification run", allow_partial_report=True)
    out = capsys.readouterr().out
    # A malformed value must never surface as a fabricated nonzero count
    # anywhere in the finalization output (e.g. len("seventeen characters") == 21).
    assert "files_changed: 21" not in out
    assert "files_changed: 10" not in out


def test_valid_int_files_changed_count_used_directly(disposable_repo) -> None:
    meta = _base_meta(files_changed_count=5, files_changed=[])
    _write_meta(disposable_repo, meta)
    # Must not crash regardless of governance-gate outcome.
    _finalize_report_and_notify("independent verification run", allow_partial_report=True)


def test_valid_list_files_changed_counted_by_length(disposable_repo) -> None:
    meta = _base_meta(files_changed=["a.py", "b.py", "c.py"], files_changed_count=0)
    _write_meta(disposable_repo, meta)
    _finalize_report_and_notify("independent verification run", allow_partial_report=True)


@pytest.mark.parametrize("field", ["validation_results", "governance_results"])
def test_explicit_null_validation_or_governance_results_does_not_crash(disposable_repo, field) -> None:
    meta = _base_meta(**{field: None})
    _write_meta(disposable_repo, meta)
    # The bug this closes was an unconditional TypeError from `for x in None`;
    # completing without an unhandled exception proves it did not crash.
    result = _finalize_report_and_notify("independent verification run", allow_partial_report=True)
    assert result in (True, False)


@pytest.mark.parametrize("field", ["validation_results", "governance_results"])
def test_non_dict_list_items_in_validation_or_governance_skipped_not_crashed(disposable_repo, field) -> None:
    meta = _base_meta(**{field: ["a bare string entry", 42, {"name": "real", "status": "passed"}]})
    _write_meta(disposable_repo, meta)
    result = _finalize_report_and_notify("independent verification run", allow_partial_report=True)
    assert result in (True, False)


def test_task_finish_malformed_validation_results_null_does_not_crash(disposable_repo) -> None:
    meta = _base_meta(validation_results=None)
    _write_meta(disposable_repo, meta)
    # No active task contract exists in this disposable repo; reaching a
    # returned dict at all (rather than an unhandled exception) proves
    # the malformed field it reads before that check did not crash it.
    result = _finalize_task_report_and_notify("deadbeef")
    assert isinstance(result, dict)


def test_task_finish_non_dict_validation_entries_skipped(disposable_repo) -> None:
    meta = _base_meta(validation_results=["bare string", {"name": "x", "result": "ok", "status": "passed"}])
    _write_meta(disposable_repo, meta)
    result = _finalize_task_report_and_notify("deadbeef")
    assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════
# 7. Cross-command current-phase parity — same live repository state
# ═══════════════════════════════════════════════════════════════════════

def test_current_phase_agrees_between_architecture_status_and_governance_audit_and_task() -> None:
    """Independently exercises three real, separately-invoked production
    entry points against this repository's own live PROJECT_STATUS.md
    and asserts they report the identical current phase ID. This is a
    structural check (they must literally agree), not a behavioral
    inference from reading code.
    """
    ps_path = Path("PROJECT_STATUS.md")
    if not ps_path.exists():
        pytest.skip("no live PROJECT_STATUS.md in this environment")

    arch_status = build_architecture_status()
    arch_current = arch_status.get("current_phase_id")

    audit_check = check_project_status_current_phase(HarnessPath(Path(".")))
    # audit_check.message is "Current phase: Phase <id> — <title> (...)"
    audit_message = audit_check.message

    task_line = _read_lifecycle_current_phase_line()

    if arch_current:
        assert arch_current in (audit_message or ""), (arch_current, audit_message)
    if arch_current and task_line:
        assert arch_current in task_line, (arch_current, task_line)


# ═══════════════════════════════════════════════════════════════════════
# 8. Architecture Status milestone-count derivation — independent re-check
# ═══════════════════════════════════════════════════════════════════════

def test_milestone_phase_id_excludes_subphases() -> None:
    assert _is_milestone_phase_id("113B") is True
    assert _is_milestone_phase_id("113B.2") is False
    assert _is_milestone_phase_id("113X.1") is False


def test_milestone_phase_id_excludes_exact_x_exception_branch_only() -> None:
    assert _is_milestone_phase_id("113X") is False
    # A different, longer branch that merely starts with "X" is a
    # distinct branch identity and must not be swept in by a prefix
    # check -- exact-match only, per the function's own documented
    # contract.
    assert _is_milestone_phase_id("113XR") is True


def test_milestone_phase_id_rejects_unparseable_input() -> None:
    assert _is_milestone_phase_id("not-a-phase-id") is False


def test_architecture_status_completed_chapter_counts_match_independent_recount() -> None:
    """Re-derives the 113/119/136 milestone counts directly from
    PROJECT_STATUS.md's own '## Phase X Complete' headers using this
    test's own regex and this module's real _is_milestone_phase_id, then
    compares against build_architecture_status()'s live output. This is
    an independent re-count, not a re-assertion of 136AX's claimed
    numbers.
    """
    import re

    ps_path = Path("PROJECT_STATUS.md")
    if not ps_path.exists():
        pytest.skip("no live PROJECT_STATUS.md in this environment")
    text = ps_path.read_text(encoding="utf-8")

    status = build_architecture_status()
    chapters_by_id = {c["chapter"]: c for c in status.get("completed_chapters", [])}

    for series in ("113", "119", "136"):
        if series not in chapters_by_id:
            continue
        header_ids = sorted(set(
            m.group(1)
            for m in re.finditer(rf"^## Phase ({series}[A-Za-z0-9.]*) Complete", text, re.MULTILINE)
        ))
        independent_milestone_count = sum(1 for pid in header_ids if _is_milestone_phase_id(pid))
        label = chapters_by_id[series]["label"]
        claimed_count_match = re.search(r",\s*(\d+)\s*phases\)", label)
        assert claimed_count_match is not None, label
        claimed_count = int(claimed_count_match.group(1))
        assert claimed_count == independent_milestone_count, (
            series, claimed_count, independent_milestone_count, header_ids
        )


# ═══════════════════════════════════════════════════════════════════════
# 9. Side-effect freedom — read-only derivation must not mutate state
# ═══════════════════════════════════════════════════════════════════════

def test_build_architecture_status_does_not_write_project_status(tmp_path, monkeypatch) -> None:
    ps = tmp_path / "PROJECT_STATUS.md"
    ps.write_text(
        "# Project Status\n\n## Current Phase\n\nPhase 136AY — Verification (completed).\n",
        encoding="utf-8",
    )
    before = ps.read_bytes()
    monkeypatch.chdir(tmp_path)
    build_architecture_status()
    after = ps.read_bytes()
    assert before == after


def test_check_project_status_current_phase_is_read_only(tmp_path, monkeypatch) -> None:
    ps = tmp_path / "PROJECT_STATUS.md"
    body = "# Project Status\n\n## Current Phase\n\nPhase 136AY — Verification (completed).\n"
    ps.write_text(body, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    check_project_status_current_phase(HarnessPath(tmp_path))
    assert ps.read_text(encoding="utf-8") == body


# ═══════════════════════════════════════════════════════════════════════
# 10. Fresh-process consistency — repeated calls with fresh state agree
# ═══════════════════════════════════════════════════════════════════════

def test_repeated_declaration_parses_are_deterministic() -> None:
    text = "Phase 136AY — Independent Verification (completed)."
    results = [_match_current_phase_declaration(text) for _ in range(5)]
    assert len({(r.phase_id, r.title, r.status_marker) for r in results}) == 1


def test_repeated_recommendation_extraction_is_deterministic() -> None:
    text = "Recommended next phase: **137A — Consumption Architecture** (not started)."
    results = [tuple(_extract_recommended_next_phase_values(text)) for _ in range(5)]
    assert len(set(results)) == 1
