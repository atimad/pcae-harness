"""N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR.

Fresh adversarial tests proving the stale full-tree ``src/pcae/**``
hash-freeze test (previously
``test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py::
test_all_production_sources_remain_byte_identical_to_recorded_baseline``)
was repaired correctly: the original historical security claim ("this
contract-only phase made zero src/pcae/** changes") is preserved exactly,
scoped to its own two pinned historical commits, instead of being asserted
forever against today's (or any future) HEAD.

Test/evidence-only phase. Zero src/pcae/** or docs/contracts/** changes.
N-16-5 remains OPEN; N-16-6/N-16-7 untouched; runtime remains
Observed / observe / unavailable.
"""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

pytestmark = pytest.mark.fast_green

ROOT = Path(__file__).resolve().parents[1]

# The historical N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR
# phase's own entry and final commits (reconstructed from PROJECT_STATUS.md
# and git history, not guessed).
_HISTORICAL_ENTRY_COMMIT = '79ea7e1644535d011da6ca3869b5557b44c50737'
_HISTORICAL_FINAL_COMMIT = 'c4f452c6a8e5d45b7076cd984d6f701a01cfa5e4'

# This repair phase's own entry commit (origin/main == HEAD, clean, at
# preflight time for this phase).
_THIS_PHASE_ENTRY_COMMIT = '4ddd5dd460355c39e842cf25e92532933b3343e9'

_STALE_TEST_FILE = ROOT / 'tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py'
_STALE_TEST_SOURCE = _STALE_TEST_FILE.read_text()

# Files repaired by the immediate predecessor phase
# (N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR); must remain
# byte-identical throughout this phase.
_HELPER_CONFORMANCE_REPAIR_FILES = (
    'src/pcae/core/hpac_pawa_helper_protocol.py',
    'src/pcae/core/hpac_pawa_helper_store_adapter.py',
    'src/pcae/core/hpac_pawa_helper_operations.py',
)

_CONTRACT_FILES = (
    'docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md',
    'docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md',
    'docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md',
)


def _git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout


def _historical_src_pcae_diff():
    return _git('diff', '--name-only', _HISTORICAL_ENTRY_COMMIT,
                _HISTORICAL_FINAL_COMMIT, '--', 'src/pcae').strip()


def test_exact_stale_test_node_identified():
    """The stale test was
    ``test_all_production_sources_remain_byte_identical_to_recorded_baseline``
    in the identity-contract-repair test module; it no longer exists under
    that name, and its historical-commit-scoped replacement does."""
    assert 'def test_all_production_sources_remain_byte_identical_to_recorded_baseline' not in _STALE_TEST_SOURCE
    assert 'def test_historical_identity_contract_repair_phase_touched_zero_production_sources' in _STALE_TEST_SOURCE


def test_originating_phase_and_entry_final_commits_identified():
    """The originating phase's baseline.json records phase-entry commit
    79ea7e16; its own final commit (reconstructed independently from git
    history) is c4f452c6 -- the commit immediately preceding the next
    phase's (IV's) own preflight baseline."""
    baseline = json.loads((ROOT / 'docs/evidence/helper-installation-identity/baseline.json').read_text())
    assert baseline['baseline'] == _HISTORICAL_ENTRY_COMMIT
    # Both commits must actually exist in this repository's history.
    for commit in (_HISTORICAL_ENTRY_COMMIT, _HISTORICAL_FINAL_COMMIT):
        _git('cat-file', '-e', f'{commit}^{{commit}}')
    # c4f452c6 is reachable from, and an ancestor of, HEAD.
    assert _git('merge-base', '--is-ancestor', _HISTORICAL_FINAL_COMMIT, 'HEAD') == ''


def test_historical_scope_reconstructed_as_zero_src_pcae_diff():
    """The historical phase's actual claim, reconstructed from evidence: it
    is a contract-text-only phase (docs/contracts/**), and it made zero
    src/pcae/** changes between its own entry and final commits."""
    assert _historical_src_pcae_diff() == ''
    changed_all = set(_git('diff', '--name-only', _HISTORICAL_ENTRY_COMMIT,
                            _HISTORICAL_FINAL_COMMIT).splitlines())
    assert changed_all, 'the historical phase must have changed something (contracts/docs/tests)'
    assert all(not path.startswith('src/pcae/') for path in changed_all)


def test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason():
    """Proves *why* the old test was stale: at least one src/pcae/** file
    now legitimately differs from the pinned baseline.json hashes, because
    of the immediate predecessor's authorized source-conformance repair --
    not because of any unauthorized drift."""
    baseline = json.loads((ROOT / 'docs/evidence/helper-installation-identity/baseline.json').read_text())
    source_hashes = {p: digest for p, digest in baseline['hashes'].items() if p.startswith('src/pcae/')}
    now_differs = [
        path for path, expected in source_hashes.items()
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected
    ]
    assert now_differs, 'expected at least one legitimate later src/pcae/** edit to differ from the stale baseline'
    assert set(now_differs) <= set(_HELPER_CONFORMANCE_REPAIR_FILES)


def test_replacement_invariant_passes_at_the_correct_historical_boundary():
    """The repaired test's own logic, re-run directly here, passes when
    scoped to the historical phase's real boundary -- regardless of what
    src/pcae/** looks like today."""
    assert _historical_src_pcae_diff() == ''


def test_replacement_invariant_is_independent_of_later_head_movement():
    """A legitimate, unrelated later source change (this repository's own
    current HEAD has moved well past the historical final commit, and
    src/pcae/** has legitimately changed since) does not affect the
    historical-boundary check -- it is pinned to two fixed commits, not to
    'current HEAD'."""
    head = _git('rev-parse', 'HEAD').strip()
    assert head != _HISTORICAL_FINAL_COMMIT
    assert _historical_src_pcae_diff() == ''


def test_replacement_does_not_skip_or_xfail_enforcement():
    """The repaired test performs real assertions (git diff / hash checks),
    not a skip/xfail no-op."""
    func_source = _STALE_TEST_SOURCE.split(
        'def test_historical_identity_contract_repair_phase_touched_zero_production_sources', 1)[1]
    assert 'pytest.skip' not in func_source
    assert 'pytest.mark.skip' not in _STALE_TEST_SOURCE.split(
        'def test_historical_identity_contract_repair_phase_touched_zero_production_sources', 1)[0][-200:]
    assert 'xfail' not in func_source
    assert 'assert' in func_source


def test_no_current_head_full_tree_freeze_assertion_remains():
    """No remaining assertion in the repaired module compares current-disk
    src/pcae/** bytes against the pinned baseline without going through a
    specific historical git commit first."""
    assert "(ROOT / 'src/pcae').rglob" not in _STALE_TEST_SOURCE
    assert "(ROOT / path).read_bytes()).hexdigest() == expected" not in _STALE_TEST_SOURCE


def test_mutation_sensitivity_detects_synthetic_unauthorized_drift(tmp_path):
    """Constructs a synthetic two-commit scratch repository mirroring the
    historical shape (protected file untouched vs. protected file mutated)
    to prove the replacement invariant's underlying mechanism -- a
    ``git diff --name-only <a> <b> -- <scope>`` emptiness check -- still
    flags real drift inside the protected historical scope, and does not
    false-positive on an unrelated file changing outside that scope."""
    repo = tmp_path / 'scratch'
    repo.mkdir()
    run = lambda *args: subprocess.run(['git', *args], cwd=repo, capture_output=True,
                                        text=True, check=True)
    run('init', '-q')
    run('config', 'user.email', 'scratch@example.invalid')
    run('config', 'user.name', 'scratch')
    (repo / 'src').mkdir()
    (repo / 'src' / 'protected.py').write_text('ORIGINAL\n')
    (repo / 'unrelated.py').write_text('ORIGINAL\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'entry')
    entry = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True,
                            text=True, check=True).stdout.strip()

    # Legitimate: only the unrelated, out-of-scope file changes.
    (repo / 'unrelated.py').write_text('LEGITIMATE LATER EDIT\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'legitimate later change')
    legitimate_final = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True,
                                       text=True, check=True).stdout.strip()
    legit_diff = subprocess.run(['git', 'diff', '--name-only', entry, legitimate_final, '--', 'src'],
                                 cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    assert legit_diff == '', 'legitimate out-of-scope change must not be flagged'

    # Unauthorized: the protected in-scope file changes.
    (repo / 'src' / 'protected.py').write_text('UNAUTHORIZED MUTATION\n')
    run('add', '-A')
    run('commit', '-q', '-m', 'unauthorized drift')
    drifted_final = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True,
                                    text=True, check=True).stdout.strip()
    drift_diff = subprocess.run(['git', 'diff', '--name-only', entry, drifted_final, '--', 'src'],
                                 cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    assert drift_diff == 'src/protected.py', 'unauthorized in-scope drift must be detected'


def test_no_production_source_changed_in_this_phase():
    """This test/evidence-only phase changes zero src/pcae/** paths from its
    own entry commit."""
    changed = _git('diff', '--name-only', _THIS_PHASE_ENTRY_COMMIT, 'HEAD',
                    '--', 'src/pcae').strip()
    assert changed == ''


def test_helper_source_conformance_repair_remains_byte_identical():
    """The immediately preceding phase's repaired production files remain
    byte-identical from this phase's entry commit through to now."""
    for path in _HELPER_CONFORMANCE_REPAIR_FILES:
        entry_bytes = subprocess.run(
            ['git', 'show', f'{_THIS_PHASE_ENTRY_COMMIT}:{path}'],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.encode('utf-8')
        current_bytes = (ROOT / path).read_bytes()
        assert hashlib.sha256(current_bytes).hexdigest() == hashlib.sha256(entry_bytes).hexdigest(), path


def test_current_contracts_remain_byte_identical():
    """HPAC-PAWA-001 v4.0, HPAC-PAWA-HELPER-001 v5.0, and HPAC-PPA-001 v2.1
    are unchanged by this phase."""
    for path in _CONTRACT_FILES:
        entry_bytes = subprocess.run(
            ['git', 'show', f'{_THIS_PHASE_ENTRY_COMMIT}:{path}'],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.encode('utf-8')
        current_bytes = (ROOT / path).read_bytes()
        assert hashlib.sha256(current_bytes).hexdigest() == hashlib.sha256(entry_bytes).hexdigest(), path


def test_n16_5_status_and_runtime_posture_unchanged():
    """N-16-5 remains NOT CLOSED (OPEN); runtime posture is unaffected by
    this test/evidence-only repair -- N16-5-F-5-TB-FAST-GREEN-BASELINE-
    FREEZE-EVIDENCE-REPAIR performs no runtime, contract, or production
    source change of any kind."""
    status_text = (ROOT / 'PROJECT_STATUS.md').read_text()
    assert 'N-16-5' in status_text
    assert ('NOT CLOSED' in status_text) or ('N-16-5 remains OPEN' in status_text) or ('N-16-5 OPEN' in status_text)
