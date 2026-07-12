"""Tests for Phase 134E.10.1.1 — Phase-Owned Commit Attribution Repair.

134E.10.1's own governed report cited five commits, including
``1844b05b`` — direct inspection of real repository history
(``git log -1 --format=%s 1844b05b`` → "Finish Phase 134E.10V
test-evidence-key correction task") proves this commit is 134E.10V's own
final commit, not 134E.10.1's. Root cause, found by direct source
inspection: ``commands/phase.py``'s ``run_phase_complete`` fell back to
``_gather_commits()`` (an unconditional ``git log --oneline -5``, zero
phase-boundary awareness) whenever ``.pcae/phase-completion-metadata.
json`` lacked an explicit ``phase_commits`` declaration — which every
phase in this session's own governed lifecycle (134E.9V through 134E.10.1)
did, since only the flat ``files_changed`` list was ever hand-authored,
never the structured, git-hash-bearing ``phase_commits`` field
``run_phase_complete`` actually treats as authoritative.

Two repairs, both generic (no specific commit hash, phase identity, or
commit list hard-coded):

1. ``commands/phase.py``'s fallback now matches ``commands/task.py``'s
   already-safe pattern (an empty, explicitly "unresolved" commits list)
   instead of guessing via a fixed-window recent-commit heuristic.
2. A new, additive, defense-in-depth check,
   ``pcae.core.phase_reports.detect_cross_phase_commit_contamination()``,
   reads each candidate commit's own subject line (this repository's own
   governed commits reliably name their owning phase, e.g. "Phase
   134E.10V: ..."/"Finish Phase 134E.10V ...") and fails closed if it
   names a different phase than the one currently finalizing — wired into
   both ``commands/phase.py`` and ``commands/task.py``'s gate computation.

No test in this file sets a live notification environment variable or
performs external delivery -- ``tests/conftest.py``'s autouse
``_isolate_external_notifications`` fixture applies regardless, and every
test here either calls pure functions directly or uses this real
repository's own read-only git history (no writes, no network).
"""

from __future__ import annotations

from pcae.core.phase_reports import detect_cross_phase_commit_contamination


# ═══════════════════════════════════════════════════════════════════════
# 1. Cross-phase commit contamination detection
# ═══════════════════════════════════════════════════════════════════════


class TestCrossPhaseCommitContaminationDetection:
    def test_prior_phase_commit_is_detected_against_real_history(self):
        """Direct reproduction of the actual defect: 134E.10.1's real,
        governed report cited 1844b05b (134E.10V's own final commit) as
        one of its own. This must be detected as contamination."""
        warnings = detect_cross_phase_commit_contamination(
            ["1844b05b"], "134E.10.1",
        )
        assert len(warnings) == 1
        assert "1844b05b" in warnings[0]
        assert "134E.10V" in warnings[0]

    def test_genuinely_owned_commit_is_not_flagged(self):
        """A18 commit whose own subject names the SAME phase must never
        be flagged."""
        warnings = detect_cross_phase_commit_contamination(
            ["a17efc1b"], "134E.10.1",
        )
        assert warnings == []

    def test_correct_full_commit_set_produces_zero_warnings(self):
        """The corrected, verified 134E.10.1 phase-owned commit set
        (excluding 1844b05b) must produce zero contamination warnings."""
        warnings = detect_cross_phase_commit_contamination(
            ["441a2142", "3bde236b", "36266ac7", "a17efc1b"], "134E.10.1",
        )
        assert warnings == []

    def test_contaminated_full_commit_set_flags_exactly_the_bad_one(self):
        """The original, defective 134E.10.1 commit list (all five, as
        actually reported) must flag exactly one contamination warning,
        for exactly the wrong commit."""
        warnings = detect_cross_phase_commit_contamination(
            ["441a2142", "3bde236b", "36266ac7", "a17efc1b", "1844b05b"],
            "134E.10.1",
        )
        assert len(warnings) == 1
        assert "1844b05b" in warnings[0]

    def test_unresolvable_synthetic_hash_is_silently_skipped(self):
        """A hash that doesn't resolve to a real commit (synthetic/test
        data) must never be treated as contamination -- this is a
        defense-in-depth check on top of, not a replacement for, explicit
        phase_commits declaration, and must remain permissive for
        hermetic test fixtures."""
        warnings = detect_cross_phase_commit_contamination(
            ["0" * 40, "deadbeef", ""], "999X.1-synthetic",
        )
        assert warnings == []

    def test_commit_with_no_phase_token_in_subject_is_not_flagged(self):
        """A real commit whose subject cites no "Phase <ID>" token at all
        (e.g. an ordinary non-governed commit) must not be flagged --
        absence of a citation is not evidence of a wrong citation. Uses
        the regex directly against a controlled subject line rather than
        searching real history (fragile across shells/git versions)."""
        import re
        from pcae.core.phase_reports import _COMMIT_SUBJECT_PHASE_TOKEN_RE
        assert _COMMIT_SUBJECT_PHASE_TOKEN_RE.search("Fix a typo in the README") is None

    def test_current_phase_case_insensitivity(self):
        """Phase-token comparison must be case-insensitive, matching this
        codebase's established convention elsewhere (134E.9V's own
        case-sensitivity repairs)."""
        warnings = detect_cross_phase_commit_contamination(
            ["1844b05b"], "134e.10v",
        )
        assert warnings == []  # same phase, different case -> not contamination

    def test_empty_commit_list_produces_no_warnings(self):
        assert detect_cross_phase_commit_contamination([], "134E.10.1") == []


# ═══════════════════════════════════════════════════════════════════════
# 2. Shared-boundary wiring — both entry points use the same check
# ═══════════════════════════════════════════════════════════════════════


class TestSharedBoundaryWiring:
    def test_phase_py_wires_cross_phase_detection(self):
        from pathlib import Path
        content = (
            Path(__file__).resolve().parent.parent / "src/pcae/commands/phase.py"
        ).read_text()
        assert "detect_cross_phase_commit_contamination" in content

    def test_task_py_wires_cross_phase_detection(self):
        from pathlib import Path
        content = (
            Path(__file__).resolve().parent.parent / "src/pcae/commands/task.py"
        ).read_text()
        assert "detect_cross_phase_commit_contamination" in content

    def test_phase_py_no_longer_defines_the_removed_recent_commit_fallback(self):
        """The repaired defect's actual root cause (a ``_gather_commits``
        function performing an unconditional recent-commit git log) must
        no longer be *defined* -- confirms the fix is a genuine removal,
        not a dead-code-left-behind patch. (A prose reference to the old
        name in an explanatory comment is fine and expected; only a
        function *definition* would mean the fallback still exists.)"""
        from pathlib import Path
        content = (
            Path(__file__).resolve().parent.parent / "src/pcae/commands/phase.py"
        ).read_text()
        assert "def _gather_commits(" not in content


# ═══════════════════════════════════════════════════════════════════════
# 3. Unresolved-attribution fallback behavior (commands/phase.py)
# ═══════════════════════════════════════════════════════════════════════


class TestUnresolvedCommitsFallback:
    def test_run_phase_complete_source_no_longer_guesses_recent_commits(self):
        """Static confirmation: when phase_commits is absent from
        metadata, the fallback must be an explicit empty/unresolved list,
        never a fixed-window git-log guess."""
        from pathlib import Path
        content = (
            Path(__file__).resolve().parent.parent / "src/pcae/commands/phase.py"
        ).read_text()
        assert "commits = []" in content
        assert 'commit_attribution = "unresolved' in content
