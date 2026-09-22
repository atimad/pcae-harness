"""Admission preflight contradiction evidence for a truthful BLOCKED phase.

These tests inspect the immutable phase-entry source baseline. They DO NOT
claim admission is repaired or endorse its unsafe defaults. No production
code, protected state, remote topology, or ceremony is changed.
"""
import ast
from pathlib import Path
import subprocess

import pytest

pytestmark = pytest.mark.fast_green

BASELINE = 'fabbfac07276b7e9b44b25295943d24e77a27229'
ROOT = Path(__file__).resolve().parents[1]


def baseline(relative):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{relative}'],
                                   cwd=ROOT, text=True)


def source(name):
    return baseline(f'src/pcae/core/{name}.py')


def function(text, name):
    return next(node for node in ast.walk(ast.parse(text))
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)


def calls(node):
    return {ast.unparse(item.func) for item in ast.walk(node) if isinstance(item, ast.Call)}


def test_baseline_authenticate_peer_none_skips_exclusion():
    node = function(source('hpac_pawa_helper_os'), 'authenticate_peer')
    assert ast.literal_eval(node.args.kw_defaults[-1]) is None
    assert 'resolve_configured_agent_identity' not in calls(node)
    guarded = [item for item in ast.walk(node) if isinstance(item, ast.If)
               and 'agent_identity is not None' in ast.unparse(item.test)]
    assert len(guarded) == 1
    assert 'credential.uid == agent_identity.uid' in ast.unparse(guarded[0].test)


def test_baseline_helper_entrypoint_dispatches_without_peer_admission():
    node = function(source('hpac_pawa_helper_entrypoint'), 'handle_one_request')
    assert 'dispatch' in calls(node)
    assert 'authenticate_peer' not in calls(node)
    assert 'resolve_configured_agent_identity' not in calls(node)
    assert 'require_verified_admission' not in calls(node)


def test_baseline_helper_context_has_no_verified_provenance():
    tree = ast.parse(source('hpac_pawa_helper_protocol'))
    context = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'HelperContext')
    fields = {node.target.id for node in context.body if isinstance(node, ast.AnnAssign)}
    assert fields == {'replay_ledger', 'evidence_stager', 'supported_operations', 'store'}


def test_normative_helper_lineage_is_pawa_not_ppa():
    contract = baseline('docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md')
    start = contract.index('- **HPAC-PAWA-HELPER-REQ-021.')
    end = contract.index('- **HPAC-PAWA-HELPER-REQ-023.', start)
    lineage = contract[start:end]
    assert 'HPAC-PAWA-HELPER-INSTALLATION/1.0' in lineage
    assert '^hpahi-[0-9a-f]{32}$' in lineage
    assert '**equal to** the PAWA `installation_id`' in lineage
    assert 'pawa-helper/current-generation.json' in lineage


def test_baseline_launcher_resolves_different_ppa_lineage():
    text = source('hpac_pawa_helper_store_adapter')
    node = function(text, 'resolve_launcher_deployment_metadata')
    assert 'ProtectedPresentationInstallationStore' in calls(node)
    assert 'store.resolve_current_generation' in calls(node)
    ppa = source('protected_presentation_installation')
    assert 'hppi-' in ast.unparse(function(ppa, 'new_installation_id'))
    assert 'HPAC-PRESENTATION-INSTALLATION/1.0' in ppa


def test_baseline_modele_requires_same_ppa_lineage():
    node = function(source('hpac_pawa_helper_store_adapter'), '_require_currentness')
    assert 'ProtectedPresentationInstallationStore' in calls(node)
    text = ast.unparse(node)
    assert 'resolved.record.installation_id != installation_id' in text
    assert 'resolved.anchor.current_generation != generation' in text


def test_baseline_dedicated_helper_registration_schema_not_implemented():
    files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE,
                                     'src/pcae/core'], cwd=ROOT, text=True).splitlines()
    matches = [path for path in files if path.endswith('.py') and
               'HPAC-PAWA-HELPER-INSTALLATION/1.0' in baseline(path)]
    assert matches == []


@pytest.mark.parametrize('name', ['hpac_foundation', 'hpac_pawa_helper_writer_authority'])
def test_deferred_authority_production_files_unchanged(name):
    relative = f'src/pcae/core/{name}.py'
    assert (ROOT / relative).read_text() == baseline(relative)


def test_hpac_protected_admin_writer_deferred_authority_still_absent():
    """``hpac_protected_admin_writer.py`` was byte-identical to this
    test's baseline (``fabbfac0``) until Phase 150G
    (N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION), which
    legitimately, explicitly-authorizedly extracted its §33 steps 1-8 into
    the new ``hpac_pawa_recognition_core`` module (a read-only,
    non-authoritative refactor -- see that phase's own evidence). A literal
    byte-identity assertion against this one file is now permanently
    stale by design (the exact pattern Phase 150C already repaired in an
    analogous predecessor suite); this narrower check preserves the
    original assertion's actual intent -- that the deferred helper-side
    authority/registration lineage this whole test file is about is still
    NOT implemented here -- without pinning to an unchanging byte
    snapshot. The other two files in the parametrized case above are
    untouched by Phase 150G and remain checked by literal byte-identity."""
    text = (ROOT / 'src/pcae/core/hpac_protected_admin_writer.py').read_text()
    assert 'HPAC-PAWA-HELPER-INSTALLATION/1.0' not in text
    assert 'authenticate_peer' not in text
    assert 'require_verified_admission' not in text


def test_current_store_rejects_contract_helper_identity(tmp_path):
    """Actual store predicate with disclosed fixture topology; no live writes."""
    import runpy
    from pcae.core.hpac_foundation import read_canonical_json_document
    from pcae.core.hpac_pawa_helper_store_adapter import _require_currentness
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError
    fixtures = runpy.run_path(str(ROOT / 'tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py'))
    root = fixtures['_root'](tmp_path)
    authority = fixtures['_authority'](root)
    ppa = fixtures['_install_mechanism'](authority, root)
    pawa = read_canonical_json_document(root / '.authority/deployment-owner.json')
    assert pawa['installation_id'].startswith('hpawi-')
    assert ppa.record.installation_id.startswith('hppi-')
    with pytest.raises(HelperProtocolError, match='descriptor_installation_mismatch'):
        _require_currentness(authority, installation_id='hpahi-' + 'a' * 32, generation=1)


def test_current_generation_read_reaches_foundation_boundary(tmp_path, monkeypatch):
    """Read provenance verification contradicts predecessor read separation claim."""
    import runpy
    from pcae.core.hpac_foundation import HPACAuthorityError
    from pcae.core.hpac_pawa_helper_store_adapter import resolve_launcher_deployment_metadata
    from pcae.core.protected_presentation_installation import ProtectedPresentationIntegrityError
    fixtures = runpy.run_path(str(ROOT / 'tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py'))
    root = fixtures['_root'](tmp_path)
    authority = fixtures['_authority'](root)
    fixtures['_install_mechanism'](authority, root)
    def blocked(self):
        raise HPACAuthorityError('sentinel: production boundary reached')
    monkeypatch.setattr(type(authority), '_validate_production_boundary', blocked)
    with pytest.raises(ProtectedPresentationIntegrityError, match='sentinel: production boundary reached'):
        resolve_launcher_deployment_metadata(authority)


def test_helper_equal_to_pawa_contract_id_is_unsatisfiable():
    helper = baseline('docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md')
    pawa = baseline('docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md')
    assert '^hpahi-[0-9a-f]{32}$' in helper
    assert '**equal to** the PAWA `installation_id`' in helper
    assert 'hpawi-' in pawa
    from pcae.core.hpac_pawa_schemas import require_installation_id, PawaSchemaError
    with pytest.raises(PawaSchemaError):
        require_installation_id('hpahi-' + 'a' * 32)
