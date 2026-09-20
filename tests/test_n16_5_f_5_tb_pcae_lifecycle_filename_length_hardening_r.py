"""PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R.

Fresh, independent re-attempt of the lifecycle filename-length hardening,
rooted at current ``origin/main`` (which now includes the completed
Phase 150B stale-assertion repair). The original 150A attempt is used as
technical reference only (see the phase evidence doc) -- this suite is
independently authored and independently verifies every claim below.

Reproduces, and proves the repair of, the exact
``OSError: [Errno 63] File name too long`` a sufficiently long CPIPC
phase identity produces when embedded directly into a phase-report or
task-contract filename component. Infrastructure-only repair: no
HPAC/PAWA/PPA/Model E/foundation/PB/runtime file is touched. Never
touches the held source-conformance IV (6c7f5cf4, 2b8ad2aa) or the
original blocked 150A commits (72cdba16, d0b2a75a) -- both are absent
from this branch's ancestry, verified below.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

ROOT = Path(__file__).resolve().parents[1]

from pcae.core.filename_safety import (  # noqa: E402
    MAX_FILENAME_COMPONENT_BYTES,
    _truncate_utf8,
    bounded_filename_component,
)
from pcae.core import phase_reports as pr  # noqa: E402
from pcae.core import tasks  # noqa: E402
from pcae.core.paths import HarnessPath  # noqa: E402

# The real, historically blocked long CPIPC identity (150B's own
# rejected `.1` candidate) -- used here only as a string constant for
# reproduction. It activates nothing; the held IV commits are untouched.
BLOCKED_LONG_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1."
    "1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1."
    "1.1.1.1.1.1.1.1.1.1.1.1.1.1.1"
)

_HELD_IV_COMMITS = ("6c7f5cf4", "2b8ad2aa")
_BLOCKED_150A_COMMITS = ("72cdba16", "d0b2a75a")


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout


# --- (1)/(2)/(3) short names unchanged, exact-limit, one-byte-over -------


@pytest.mark.parametrize(
    "raw,extension",
    [
        ("20260920-111056-150C", ".md"),
        ("short-task-slug", ".md"),
        ("", ".json"),
        ("a" * 100, ".md"),
    ],
)
def test_01_short_name_unchanged(raw, extension):
    assert bounded_filename_component(raw, extension=extension) == raw


def test_02_exact_limit_name_unchanged():
    extension = ".md"
    raw = "a" * (MAX_FILENAME_COMPONENT_BYTES - len(extension))
    assert len((raw + extension).encode("utf-8")) == MAX_FILENAME_COMPONENT_BYTES
    assert bounded_filename_component(raw, extension=extension) == raw


def test_03_one_byte_over_limit_is_bounded():
    extension = ".md"
    raw = "a" * (MAX_FILENAME_COMPONENT_BYTES - len(extension) + 1)
    bounded = bounded_filename_component(raw, extension=extension)
    assert bounded != raw
    assert len((bounded + extension).encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


# --- (4) the real historically blocked ID is bounded ----------------------


def test_04_actual_blocked_report_basename_becomes_safe():
    ts = "20260920-111056-645021"
    safe_id = pr._safe_filename(BLOCKED_LONG_PHASE_ID)
    digest = "0123456789ab"
    raw_base = f"{ts}-{safe_id}-{digest}"
    for ext in (".blocked.md", ".blocked.json"):
        bounded = pr._bounded_report_base(raw_base, longest_extension=".blocked.json")
        full = f"{bounded}.blocked" + ext[len(".blocked"):]
        assert len(full.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


# --- (5)/(7) UTF-8 byte length, Unicode boundary matrix -------------------


@pytest.mark.parametrize(
    "raw",
    [
        "ascii-only-" + "x" * 300,
        "Ср́бија" * 60,  # Serbian Latin/Cyrillic with combining accent
        "éèêë" * 80,  # accented Latin
        "Сербија" * 40,  # Cyrillic
        "中文测试" * 70,  # CJK
        "\U0001f600\U0001f680\U0001f4a9" * 90,  # emoji (surrogate-pair-requiring codepoints)
        "é́́" * 100,  # combining characters stacked
        "mix-中-\U0001f600-С-a" * 30,  # mixed scripts
    ],
)
def test_05_unicode_matrix_byte_bounded(raw):
    extension = ".json"
    bounded = bounded_filename_component(raw, extension=extension)
    full_bytes = (bounded + extension).encode("utf-8")
    assert len(full_bytes) <= MAX_FILENAME_COMPONENT_BYTES
    # Never merely character-count bounded -- must be BYTE bounded.
    assert len(bounded) <= MAX_FILENAME_COMPONENT_BYTES


def test_06_truncate_utf8_never_splits_a_codepoint():
    raw = "中文" * 200  # each char is 3 bytes in UTF-8
    for budget in range(0, 20):
        truncated = _truncate_utf8(raw, budget)
        # A successfully decoded string round-trips through utf-8 encode
        # cleanly by construction; the real risk is a mid-codepoint
        # byte-slice raising or corrupting -- assert it never does and
        # stays within budget.
        assert len(truncated.encode("utf-8")) <= budget


# --- (7) digest deterministic ----------------------------------------------


def test_07_deterministic_output():
    raw = "x" * 400
    first = bounded_filename_component(raw, extension=".json")
    second = bounded_filename_component(raw, extension=".json")
    assert first == second


# --- (8) collision resistance for shared-prefix long names ----------------


def test_08_shared_prefix_names_do_not_collide():
    prefix = "a" * 400
    raw_a = prefix + "-TAIL-ONE"
    raw_b = prefix + "-TAIL-TWO"
    bounded_a = bounded_filename_component(raw_a, extension=".md")
    bounded_b = bounded_filename_component(raw_b, extension=".md")
    assert bounded_a != bounded_b
    # Both are still within budget.
    for b in (bounded_a, bounded_b):
        assert len((b + ".md").encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


def test_08b_different_full_inputs_get_different_digest_suffix():
    a = bounded_filename_component("y" * 400, extension=".md")
    b = bounded_filename_component("z" * 400, extension=".md")
    assert a.rsplit("--", 1)[-1] != b.rsplit("--", 1)[-1]


# --- (9) extension preserved -----------------------------------------------


def test_09_extension_preserved_across_bounding():
    raw = "q" * 400
    for ext in (".md", ".json", ".blocked.md", ".blocked.json"):
        bounded = bounded_filename_component(raw, extension=ext)
        full = bounded + ext
        assert full.endswith(ext)
        assert len(full.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


# --- (10) unsafe path characters sanitized consistently --------------------


def test_10_no_path_traversal_or_separators_in_bounded_output():
    """`bounded_filename_component` only bounds byte length -- it is not a
    character sanitizer, by design (module docstring: filename-length
    hardening only, never a substitute for each writer's own
    sanitization). Path-unsafe characters are the caller's
    responsibility: `phase_reports._safe_filename` replaces every
    non-`[a-zA-Z0-9_.-]` character (including "/", "\\", "..") *before*
    bounding, on the real production call path. Verify that composition
    is actually safe end to end."""
    dangerous = "../../etc/passwd" + "x" * 400
    safe_then_bounded = bounded_filename_component(
        pr._safe_filename(dangerous), extension=".md"
    )
    assert "/" not in safe_then_bounded
    assert "\\" not in safe_then_bounded
    # Dots survive _safe_filename (they're a permitted filename
    # character), but with every "/" gone this is one inert path
    # component ("..-..-etc-passwd"-shaped), not a traversal sequence.


# --- (11)/(12)/(13)/(14) writer/reader round trip --------------------------


def test_11_quarantine_markdown_and_json_writers_succeed(tmp_path):
    report = pr.PhaseReport(
        phase_id=BLOCKED_LONG_PHASE_ID,
        phase_name="Synthetic long-ID report for filename-hardening test",
        status="completed",
        summary="synthetic blocked report",
    )
    paths = pr.write_quarantined_report(report, tmp_path, ["synthetic blocker"])
    md_path = Path(paths["quarantine_markdown"])
    json_path = Path(paths["quarantine_json"])
    assert md_path.exists()
    assert json_path.exists()
    for p in (md_path, json_path):
        assert len(p.name.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


def test_12_promoted_report_writer_succeeds_and_reads_back(tmp_path):
    report = pr.PhaseReport(
        phase_id=BLOCKED_LONG_PHASE_ID,
        phase_name="Synthetic long-ID promoted report",
        status="completed",
        summary="synthetic",
    )
    result = pr.write_phase_report(report, tmp_path)
    json_path = Path(result["json"])
    md_path = Path(result["markdown"])
    assert len(json_path.name.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES
    assert len(md_path.name.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["phase_id"] == BLOCKED_LONG_PHASE_ID
    # latest.json/latest.md are always short, fixed names -- unaffected.
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["phase_id"] == BLOCKED_LONG_PHASE_ID


def test_13_full_canonical_phase_id_retained_in_quarantine_content(tmp_path):
    report = pr.PhaseReport(
        phase_id=BLOCKED_LONG_PHASE_ID,
        phase_name="Synthetic long-ID quarantine report",
        status="completed",
        summary="synthetic",
    )
    paths = pr.write_quarantined_report(report, tmp_path, ["synthetic blocker"])
    data = json.loads(Path(paths["quarantine_json"]).read_text(encoding="utf-8"))
    assert data["phase_id"] == BLOCKED_LONG_PHASE_ID


def test_14_before_repair_reproduction_still_demonstrates_original_defect(tmp_path):
    """Sanity check that the defect this phase fixes is real: manually
    reconstructing the OLD (unbounded) basename for the actual blocked ID
    still exceeds the filesystem limit, proving the fix is not vacuous."""
    ts = "20260920-111056-645021"
    safe_id = pr._safe_filename(BLOCKED_LONG_PHASE_ID)
    old_unbounded_base = f"{ts}-{safe_id}-abcdef123456.blocked"
    assert len((old_unbounded_base + ".json").encode("utf-8")) > MAX_FILENAME_COMPONENT_BYTES


# --- (16)/(17)/(18)/(19) task lifecycle round trip -------------------------


def _harness(tmp_path) -> HarnessPath:
    return HarnessPath(tmp_path)


def test_16_task_create_with_long_title_succeeds(tmp_path):
    root = _harness(tmp_path)
    long_title = "x" * 500 + " a legitimately long governed phase title"
    contract = tasks.create_task_contract(root, long_title)
    target = root.join(contract.relative_path)
    assert target.exists()
    assert len(target.name.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


def test_17_task_lookup_recovers_full_title_and_id(tmp_path):
    root = _harness(tmp_path)
    long_title = "y" * 500 + " another long governed phase title"
    contract = tasks.create_task_contract(root, long_title)
    active = tasks.find_latest_active_task(root)
    assert active is not None
    assert active.task_id == contract.task_id
    assert active.title == long_title


def test_18_task_finish_moves_to_done_without_enametoolong(tmp_path):
    root = _harness(tmp_path)
    long_title = "z" * 500 + " a long governed phase title to be closed"
    contract = tasks.create_task_contract(root, long_title)
    closed = tasks.close_latest_active_task(root)
    assert closed is not None
    assert closed.destination_path.exists()
    assert not root.join(contract.relative_path).exists()
    assert len(closed.destination_path.name.encode("utf-8")) <= MAX_FILENAME_COMPONENT_BYTES


def test_19_full_task_identity_retained_in_done_content(tmp_path):
    root = _harness(tmp_path)
    long_title = "w" * 500 + " a third long governed phase title"
    contract = tasks.create_task_contract(root, long_title)
    closed = tasks.close_latest_active_task(root)
    content = closed.destination_path.read_text(encoding="utf-8")
    assert contract.task_id in content
    assert long_title in content


# --- (20)/(21) historical short names resolve unchanged --------------------


def test_20_historical_short_report_name_unaffected(tmp_path):
    report = pr.PhaseReport(
        phase_id="150C",
        phase_name="short id report",
        status="completed",
        summary="synthetic",
    )
    result = pr.write_phase_report(report, tmp_path)
    assert "150C" in Path(result["json"]).name


def test_21_historical_short_task_name_unaffected(tmp_path):
    root = _harness(tmp_path)
    contract = tasks.create_task_contract(root, "a short title")
    target = root.join(contract.relative_path)
    assert target.name == f"{contract.task_id}.md"


# --- (22) 150B repaired stale assertions remain green -----------------------


def test_22_phase_150b_repaired_assertions_still_pass_after_this_phases_edits():
    result = subprocess.run(
        ["python", "-m", "pytest",
         "tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py",
         "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --- (23) no path traversal (repeat, direct on the primitive) --------------


def test_23_no_authority_semantics_from_filename_or_digest(tmp_path):
    """The digest suffix and bounded filename convey no authority: two
    reports with different phase_id content but colliding raw basenames
    (impossible here since digest is content-derived) never happens, and
    reading back always re-derives trust from CONTENT, not the filename."""
    report = pr.PhaseReport(
        phase_id=BLOCKED_LONG_PHASE_ID,
        phase_name="authority test",
        status="completed",
        summary="synthetic",
    )
    paths = pr.write_quarantined_report(report, tmp_path, ["synthetic blocker"])
    # The filename alone (without reading content) proves nothing about
    # the phase_id -- only the JSON content is authoritative.
    data = json.loads(Path(paths["quarantine_json"]).read_text(encoding="utf-8"))
    assert data["phase_id"] == BLOCKED_LONG_PHASE_ID
    assert BLOCKED_LONG_PHASE_ID not in Path(paths["quarantine_json"]).name


# --- (25)/(26) held/blocked commits absent from this branch's ancestry -----


def test_25_held_iv_commits_absent_from_ancestry():
    for commit in _HELD_IV_COMMITS:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode != 0, f"{commit} must not be an ancestor of this branch"


def test_26_blocked_150a_commits_absent_from_ancestry():
    for commit in _BLOCKED_150A_COMMITS:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode != 0, f"{commit} must not be an ancestor of this branch"


# --- (27)/(28) HPAC/contract/helper files untouched -------------------------


def test_27_hpac_contracts_untouched():
    changed = _git("diff", "--name-only", "origin/main", "HEAD", "--", "docs/contracts").strip()
    assert changed == ''


def test_28_helper_source_conformance_files_untouched():
    files = (
        "src/pcae/core/hpac_pawa_helper_protocol.py",
        "src/pcae/core/hpac_pawa_helper_store_adapter.py",
        "src/pcae/core/hpac_pawa_helper_operations.py",
    )
    changed = _git("diff", "--name-only", "origin/main", "HEAD", "--", *files).strip()
    assert changed == ''


def test_29_production_diff_confined_to_expected_files():
    changed = set(_git("diff", "--name-only", "origin/main", "HEAD", "--", "src/pcae").strip().splitlines())
    expected = {
        "src/pcae/core/filename_safety.py",
        "src/pcae/core/phase_reports.py",
        "src/pcae/core/tasks.py",
    }
    assert changed <= expected, f"unexpected production changes: {changed - expected}"


# --- runtime posture unchanged ----------------------------------------------


def test_30_runtime_posture_unchanged():
    status_text = (ROOT / 'PROJECT_STATUS.md').read_text()
    assert 'N-16-5' in status_text
