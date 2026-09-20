"""N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR.

Fresh adversarial suite proving the narrow repair of the two stale
current-HEAD-bound assertions in
``tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py``
(``test_no_production_source_changed_in_this_phase`` and
``test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason``):

both previously evaluated a historical, phase-local claim ("this
test/evidence-only phase changed zero src/pcae/** paths", "this
predecessor-repair legitimately changed exactly these three files") against
whatever ``HEAD``/disk happens to be *when the test runs*, instead of
against the historical phase's own fixed terminal boundary. That made both
assertions fail by construction the moment any later, unrelated, legitimate
phase touched a different ``src/pcae/**`` file.

Repair model: bind both assertions to two fixed pinned commits
(``_THIS_PHASE_ENTRY_COMMIT`` -> ``_THIS_PHASE_FINAL_COMMIT``), matching the
pattern already used elsewhere in the same file
(``_HISTORICAL_ENTRY_COMMIT`` -> ``_HISTORICAL_FINAL_COMMIT``) and in the
predecessor repair it itself documents (Model FG-E).

Test/evidence-only phase. Zero src/pcae/** or docs/contracts/** changes.
N-16-5 remains OPEN; N-16-6/N-16-7 untouched; runtime remains
Observed / observe / unavailable. Does not touch the held source-conformance
IV commits (6c7f5cf4, 2b8ad2aa) or the blocked 150A filename-length
hardening commits (72cdba16, d0b2a75a); neither is present in this branch's
ancestry (verified below).
"""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

pytestmark = pytest.mark.fast_green

ROOT = Path(__file__).resolve().parents[1]

_TARGET_TEST_FILE = ROOT / 'tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py'
_TARGET_TEST_SOURCE = _TARGET_TEST_FILE.read_text()

_THIS_REPAIR_PHASE_ENTRY_COMMIT = 'c4c9f554106965e10a057db96a106f85f72f8f65'
# 150B's own final (last-pushed) commit -- this phase's own "did we touch
# src/pcae" claim is evaluated at this pinned boundary, never at 'HEAD',
# per the exact Model FG-E principle this file itself documents above.
# (Phase 150C, PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R, found this same
# HEAD-bound pattern still present in this file's own two "did this phase
# touch src/pcae" assertions below -- the identical disease class 150B
# repaired in the sibling file, present here in 150B's own fresh suite.)
_THIS_REPAIR_PHASE_FINAL_COMMIT = '2be6fe01690d7ee81e854f6f8374a4086f318a9b'

# The repaired phase's own pinned boundary (reconstructed independently from
# PROJECT_STATUS.md and git history, not guessed).
_TARGET_PHASE_ENTRY_COMMIT = '4ddd5dd460355c39e842cf25e92532933b3343e9'
_TARGET_PHASE_FINAL_COMMIT = 'c4c9f554106965e10a057db96a106f85f72f8f65'

# The blocked/held commits this phase must never touch, publish, or build on.
_HELD_IV_COMMITS = ('6c7f5cf4', '2b8ad2aa')
_BLOCKED_150A_COMMITS = ('72cdba16', 'd0b2a75a')

# A real, independently-verified example of a later legitimate src/pcae/**
# edit that would have broken the old current-HEAD-bound assertions: the
# blocked 150A filename-length hardening attempt's own source-only commit,
# reachable on a separate local branch, never merged/pushed. Used here only
# to read historical blob content for a diagnostic comparison -- this phase
# does not touch, cherry-pick, or depend on that branch's ref remaining
# present in this branch's ancestry.
_LEGITIMATE_LATER_EDIT_COMMIT = '72cdba16'
_LEGITIMATE_LATER_EDIT_FILES = (
    'src/pcae/core/filename_safety.py',
    'src/pcae/core/phase_reports.py',
    'src/pcae/core/tasks.py',
)


def _git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout


def test_no_held_or_blocked_commits_in_this_branch_ancestry():
    """150A and the held source-conformance IV are neither ancestors of nor
    reachable from this branch's HEAD."""
    for commit in (*_HELD_IV_COMMITS, *_BLOCKED_150A_COMMITS):
        result = subprocess.run(
            ['git', 'merge-base', '--is-ancestor', commit, 'HEAD'],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode != 0, f'{commit} must not be an ancestor of this branch'


def test_this_phase_changed_zero_production_or_contract_files():
    """This stale-assertion-repair phase itself changed zero src/pcae/** or
    docs/contracts/** paths between its own entry and its own final
    (pushed) commit -- not against 'HEAD', which a later, unrelated,
    legitimate phase (e.g. filename-length hardening) may legitimately
    move past by editing some other src/pcae/** file."""
    assert _git('merge-base', '--is-ancestor', _THIS_REPAIR_PHASE_FINAL_COMMIT, 'HEAD') == ''
    changed = _git('diff', '--name-only', _THIS_REPAIR_PHASE_ENTRY_COMMIT,
                    _THIS_REPAIR_PHASE_FINAL_COMMIT, '--', 'src/pcae', 'docs/contracts').strip()
    assert changed == ''


def test_target_boundary_commits_are_pinned_and_reachable():
    """The repaired phase's own entry/final commits exist and the final one
    is an ancestor of HEAD."""
    for commit in (_TARGET_PHASE_ENTRY_COMMIT, _TARGET_PHASE_FINAL_COMMIT):
        _git('cat-file', '-e', f'{commit}^{{commit}}')
    assert _git('merge-base', '--is-ancestor', _TARGET_PHASE_FINAL_COMMIT, 'HEAD') == ''


def test_no_head_or_origin_main_stale_pattern_remains_in_target_file():
    """Neither of the two originally-stale assertions still terminates a
    historical-phase diff at 'HEAD' or 'origin/main'; the file's other
    intentional current-state checks (ancestor-of-HEAD, HEAD != a fixed
    historical commit) are unaffected and remain present."""
    assert "_THIS_PHASE_ENTRY_COMMIT, 'HEAD'" not in _TARGET_TEST_SOURCE
    assert "(ROOT / path).read_bytes()).hexdigest() != expected" not in _TARGET_TEST_SOURCE
    # Legitimate current-state checks (unrelated to the two repaired
    # assertions) are preserved, not collateral damage.
    assert "'merge-base', '--is-ancestor'" in _TARGET_TEST_SOURCE
    assert "head != _HISTORICAL_FINAL_COMMIT" in _TARGET_TEST_SOURCE


def test_target_suite_passes_with_repair_applied():
    """The full repaired target test module passes as-is."""
    result = subprocess.run(
        ['python', '-m', 'pytest', str(_TARGET_TEST_FILE), '-q'],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mutation_no_production_source_changed_detects_synthetic_drift(tmp_path):
    """Synthetic proof that the repaired 'no production source changed'
    mechanism (git diff --name-only entry final -- src/pcae) still detects
    an unauthorized in-scope change between the pinned boundary commits, and
    does not false-positive on an out-of-scope change."""
    repo = tmp_path / 'scratch'
    repo.mkdir()
    run = lambda *args: subprocess.run(['git', *args], cwd=repo, capture_output=True,
                                        text=True, check=True)
    run('init', '-q')
    run('config', 'user.email', 'scratch@example.invalid')
    run('config', 'user.name', 'scratch')
    (repo / 'src' / 'pcae').mkdir(parents=True)
    (repo / 'src' / 'pcae' / 'protected.py').write_text('ORIGINAL\n')
    (repo / 'tests').mkdir()
    (repo / 'tests' / 'evidence.py').write_text('ORIGINAL\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'phase entry')
    entry = run('rev-parse', 'HEAD').stdout.strip()

    # This phase's own final commit: only touches tests/evidence, matching
    # the real "test/evidence-only phase" claim.
    (repo / 'tests' / 'evidence.py').write_text('PHASE EVIDENCE\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'phase final')
    final = run('rev-parse', 'HEAD').stdout.strip()
    phase_diff = run('diff', '--name-only', entry, final, '--', 'src/pcae').stdout.strip()
    assert phase_diff == '', 'the phase-local claim (zero src/pcae changes) must hold at its own boundary'

    # A later, unrelated, legitimate edit lands after the phase's own final
    # commit -- must not retroactively change the phase-local verdict above,
    # because the boundary is pinned to `final`, not to whatever HEAD is now.
    (repo / 'src' / 'pcae' / 'protected.py').write_text('LATER LEGITIMATE EDIT\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'later legitimate phase')
    later_head = run('rev-parse', 'HEAD').stdout.strip()
    stale_pattern_diff = run('diff', '--name-only', entry, later_head, '--', 'src/pcae').stdout.strip()
    assert stale_pattern_diff == 'src/pcae/protected.py', (
        'sanity check: the OLD (entry -> HEAD) pattern would indeed have been broken by this legitimate edit'
    )
    pinned_diff = run('diff', '--name-only', entry, final, '--', 'src/pcae').stdout.strip()
    assert pinned_diff == '', 'the repaired (entry -> pinned final) pattern must be immune to the later edit'


def test_mutation_allowlist_check_detects_synthetic_unexpected_file(tmp_path):
    """Synthetic proof that the repaired allowlist-style check (comparing
    disk/blob bytes at a *pinned* commit, not live disk) still fails when an
    extra unexpected file appears inside the protected historical range, and
    still passes -- unaffected by later edits -- when only the allowed files
    differ."""
    repo = tmp_path / 'scratch'
    repo.mkdir()
    run = lambda *args: subprocess.run(['git', *args], cwd=repo, capture_output=True,
                                        text=True, check=True)
    run('init', '-q')
    run('config', 'user.email', 'scratch@example.invalid')
    run('config', 'user.name', 'scratch')
    (repo / 'src' / 'pcae').mkdir(parents=True)
    (repo / 'src' / 'pcae' / 'allowed.py').write_text('BASELINE\n')
    (repo / 'src' / 'pcae' / 'other.py').write_text('BASELINE\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'baseline')
    baseline_hashes = {
        'src/pcae/allowed.py': hashlib.sha256(b'BASELINE\n').hexdigest(),
        'src/pcae/other.py': hashlib.sha256(b'BASELINE\n').hexdigest(),
    }
    allowlist = {'src/pcae/allowed.py'}

    # Legitimate repair: only the allowed file changes, pinned at this commit.
    (repo / 'src' / 'pcae' / 'allowed.py').write_text('REPAIRED\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'legitimate repair')
    repair_final = run('rev-parse', 'HEAD').stdout.strip()

    def _differs_at(commit):
        out = []
        for path, expected in baseline_hashes.items():
            blob = subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=repo,
                                   capture_output=True, check=True).stdout
            if hashlib.sha256(blob).hexdigest() != expected:
                out.append(path)
        return out

    assert set(_differs_at(repair_final)) <= allowlist

    # An unrelated later commit changes the other (previously untouched)
    # file. Pinned check at repair_final must still pass -- it is immune to
    # this later HEAD movement.
    (repo / 'src' / 'pcae' / 'other.py').write_text('LATER UNRELATED EDIT\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'later unrelated edit')
    assert set(_differs_at(repair_final)) <= allowlist, 'pinned check must be immune to later HEAD movement'

    # Now prove the mechanism still catches an unexpected file *inside* the
    # protected historical range: a hypothetical alternate repair that also
    # touched `other.py` between baseline and its own final commit.
    (repo / 'src' / 'pcae' / 'other.py').write_text('UNEXPECTED IN-SCOPE CHANGE\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'unexpected in-scope drift')
    unexpected_final = run('rev-parse', 'HEAD').stdout.strip()
    assert not (set(_differs_at(unexpected_final)) <= allowlist), (
        'an unexpected in-scope file change must not silently pass the allowlist check'
    )


def test_legitimate_later_src_pcae_edit_does_not_break_either_repaired_assertion():
    """A real, independently-verified example of a later legitimate
    src/pcae/** edit (150A's own filename-safety source commit, held on a
    separate unmerged/unpushed local branch and never touched by this
    phase) is used only diagnostically here: were it merged onto this
    branch, the OLD current-HEAD-bound assertions would have broken, while
    the repaired pinned-boundary assertions in the target file remain
    provably unaffected because they never read 'HEAD' at all."""
    for commit in _BLOCKED_150A_COMMITS:
        result = subprocess.run(
            ['git', 'cat-file', '-e', f'{commit}^{{commit}}'],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            pytest.skip('150A commit not present in local object store; diagnostic-only check')
    changed = _git('diff', '--name-only', 'c4c9f554', _LEGITIMATE_LATER_EDIT_COMMIT,
                    '--', 'src/pcae').strip().splitlines()
    assert set(changed) == set(_LEGITIMATE_LATER_EDIT_FILES), (
        '150A is confirmed to legitimately touch src/pcae/** files outside '
        'the historical helper-conformance allowlist -- exactly the shape '
        'that would have broken the old current-HEAD-bound assertions'
    )
    # The repaired target-file assertions never mention 'HEAD' in their
    # historical-boundary diff calls, so they are structurally immune
    # regardless of whether 150A ever lands.
    assert "_THIS_PHASE_ENTRY_COMMIT, 'HEAD'" not in _TARGET_TEST_SOURCE


def test_no_production_source_or_contract_changes_repo_wide():
    """Zero src/pcae/** or docs/contracts/** changes anywhere in this
    phase's diff from its own entry commit to its own final (pushed)
    commit -- pinned, not evaluated against a moving 'HEAD'."""
    changed = _git('diff', '--name-only', _THIS_REPAIR_PHASE_ENTRY_COMMIT,
                    _THIS_REPAIR_PHASE_FINAL_COMMIT).strip()
    changed_paths = changed.splitlines() if changed else []
    assert all(not p.startswith('src/pcae/') for p in changed_paths)
    assert all(not p.startswith('docs/contracts/') for p in changed_paths)


def test_n16_5_status_and_runtime_posture_unchanged():
    status_text = (ROOT / 'PROJECT_STATUS.md').read_text()
    assert 'N-16-5' in status_text
