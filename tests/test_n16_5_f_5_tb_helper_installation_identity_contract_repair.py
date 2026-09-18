"""Contract specification checks, NOT a production admission implementation/proof.

The deliberately small evaluator below models the normative JSON and §30D
constraints. Production sources remain baseline-identical and non-conformant;
passing these tests neither admits a process nor authorizes a protected write.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest

pytestmark = pytest.mark.fast_green
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/contracts'
SPEC = json.loads((DOCS / 'helper_installation_identity_constraints.json').read_text())
CONTRACTS = {
    'HPAC-PAWA-HELPER-001': ('HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md', 'HPAC-PAWA-HELPER', 183),
    'HPAC-PAWA-001': ('HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md', 'HPAC-PAWA', 344),
    'HPAC-PPA-001': ('HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md', 'HPAC-PPA', 108),
}
TEXT = {key: (DOCS / value[0]).read_text() for key, value in CONTRACTS.items()}
HELPER = TEXT['HPAC-PAWA-HELPER-001'].split('## 30D. Installation identity reconciliation', 1)[1]


def _parent():
    return dict(installation_id='hpawi-' + '1' * 32, generation=7,
                descriptor_digest='a' * 64, agent_exclusion_digest='b' * 64,
                protected_root_identity={'device': 3, 'inode': 9})


def _execution(profile='privileged'):
    identity = SPEC['profiles'][profile]['identity']
    return dict(profile=profile, installation_id=SPEC['identities'][identity]['prefix'] + '2' * 32,
                generation=3, installation_digest='c' * 64, helper_sha256='d' * 64,
                pawa_binding=_parent())


def _grammar(binding):
    """Closed descriptive tuple grammar, with no seals or active authority."""
    if not isinstance(binding, dict) or set(binding) != set(SPEC['execution_binding_fields']):
        return False
    profile = SPEC['profiles'].get(binding['profile'])
    if profile is None:
        return False
    prefix = SPEC['identities'][profile['identity']]['prefix']
    parent = binding['pawa_binding']
    if not isinstance(parent, dict) or set(parent) != set(SPEC['pawa_binding_fields']):
        return False
    if not re.fullmatch(prefix + '[0-9a-f]{32}', str(binding['installation_id'])):
        return False
    if not re.fullmatch(SPEC['identities']['pawa']['prefix'] + '[0-9a-f]{32}', str(parent['installation_id'])):
        return False
    for value in (binding['generation'], parent['generation']):
        if type(value) is not int or value < 1:
            return False
    for value in (binding['installation_digest'], binding['helper_sha256'], parent['descriptor_digest'], parent['agent_exclusion_digest']):
        if not re.fullmatch('[0-9a-f]{64}', str(value)):
            return False
    root = parent['protected_root_identity']
    return isinstance(root, dict) and set(root) == {'device', 'inode'} and all(type(v) is int and v >= 0 for v in root.values())


def _current(asserted, recognized, parent, schema=2):
    """Equality model only: recognized state is a test premise, not proof."""
    return (schema == 2 and _grammar(asserted) and _grammar(recognized)
            and asserted == recognized and recognized['pawa_binding'] == parent)


def _topology(values):
    if values.get('configured_agent_uid') is None or values.get('agent_writable') is not False:
        return False
    for constraint in SPEC['constraints']:
        left, right = values.get(constraint['left']), values.get(constraint['right'])
        if left is None or right is None:
            return False
        if (left == right) != (constraint['relation'] == '=='):
            return False
    return True


def _valid_topology():
    return dict(helper_uid=1000, peer_uid=1000, deployment_owner_uid=1000,
                configured_agent_uid=1001, agent_writable=False,
                pawa_id='hpawi-' + '1' * 32, privileged_id='hpahi-' + '2' * 32,
                presentation_id='hppi-' + '3' * 32)


@pytest.mark.parametrize('key', CONTRACTS)
def test_current_contract_versions_and_gap_free_unique_requirements(key):
    _, prefix, maximum = CONTRACTS[key]
    assert TEXT[key].startswith(f'# {key} v{SPEC["contract_versions"][key]} ')
    declarations = re.findall(r'\*\*' + prefix + r'-REQ-(\d+)(?:\.| \()', TEXT[key])
    numbers = [int(x) for x in declarations]
    assert sorted(numbers) == list(range(1, maximum + 1))
    if key == 'HPAC-PAWA-HELPER-001':
        assert TEXT[key].count('**HPAC-PAWA-HELPER-REQ-114A (') == 1


def test_frozen_model_and_specification_are_normatively_linked():
    assert SPEC['specification'] == 'HPAC-INSTALLATION-IDENTITY-CONSTRAINTS/1.0'
    assert SPEC['status'] == 'FROZEN_PENDING_INDEPENDENT_VERIFICATION'
    assert SPEC['selected_model'] == 'I-B'
    assert SPEC['production_implemented'] is False
    assert 'helper_installation_identity_constraints.json` is normative' in HELPER
    assert 'Contracts do not repair source' in HELPER


def test_three_installation_vocabularies_are_disjoint_not_os_identities():
    assert set(SPEC['identities']) == {'pawa', 'privileged', 'presentation'}
    prefixes = {v['prefix'] for v in SPEC['identities'].values()}
    assert prefixes == {'hpawi-', 'hpahi-', 'hppi-'}
    assert all(v['category'] == 'logical_installation' for v in SPEC['identities'].values())
    assert 'never OS identities' in HELPER
    assert 'sharing a root does not imply ID\nequality' in HELPER


def test_authority_dependency_graph_is_acyclic_and_has_one_root():
    graph = {}
    for child, parent in SPEC['authority_dependencies']:
        graph.setdefault(child, []).append(parent)
    def visit(node, path):
        assert node not in path, f'Circular identity trust: {path + [node]}'
        for parent in graph.get(node, []):
            visit(parent, path + [node])
    for node in graph:
        visit(node, [])
    assert set(p for parents in graph.values() for p in parents) - set(graph) == {'root_os_boundary'}
    assert graph == {'pawa': ['root_os_boundary'], 'privileged': ['pawa'], 'presentation': ['pawa']}
    assert 'PAWA recognition never depends on H/P installation' in HELPER


def test_equality_union_has_no_inequality_contradiction():
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    for c in SPEC['constraints']:
        assert c['relation'] in {'==', '!='}
        assert c['source'] in {'HELPER-172', 'HELPER-178'}
        if c['relation'] == '==':
            parent[find(c['left'])] = find(c['right'])
    for c in SPEC['constraints']:
        if c['relation'] == '!=':
            assert find(c['left']) != find(c['right'])
    assert _topology(_valid_topology())


@pytest.mark.parametrize('field,value', [
    ('configured_agent_uid', None), ('configured_agent_uid', 1000),
    ('helper_uid', 1001), ('peer_uid', 1001), ('deployment_owner_uid', 1001),
    ('agent_writable', True), ('agent_writable', None),
    ('privileged_id', 'hpawi-' + '1' * 32), ('presentation_id', 'hpahi-' + '2' * 32),
])
def test_identity_and_effective_access_denial_vectors(field, value):
    values = _valid_topology()
    values[field] = value
    assert not _topology(values)


def test_parent_and_component_generation_counters_are_independent():
    binding = _execution()
    assert binding['generation'] != binding['pawa_binding']['generation']
    assert _current(binding, deepcopy(binding), _parent())
    assert SPEC['currentness']['independent_generation_counters']
    assert 'never compare H generation to P or PAWA generation' in HELPER


@pytest.mark.parametrize('field', SPEC['execution_binding_fields'])
def test_every_execution_tuple_member_is_required_and_current(field):
    trusted = _execution()
    missing = deepcopy(trusted)
    del missing[field]
    assert not _current(missing, trusted, _parent())
    altered = deepcopy(trusted)
    replacement = {'profile': 'presentation', 'installation_id': 'hpahi-' + '4' * 32,
                   'generation': 4, 'installation_digest': 'e' * 64,
                   'helper_sha256': 'f' * 64, 'pawa_binding': {**_parent(), 'generation': 8}}
    altered[field] = replacement[field]
    assert not _current(altered, trusted, _parent())


@pytest.mark.parametrize('field', SPEC['pawa_binding_fields'])
def test_parent_rotation_or_substitution_invalidates_even_matching_component_pair(field):
    trusted = _execution()
    parent = _parent()
    replacements = {'installation_id': 'hpawi-' + '4' * 32, 'generation': 8,
                    'descriptor_digest': 'e' * 64, 'agent_exclusion_digest': 'f' * 64,
                    'protected_root_identity': {'device': 3, 'inode': 10}}
    parent[field] = replacements[field]
    assert not _current(trusted, deepcopy(trusted), parent)
    missing = deepcopy(trusted)
    del missing['pawa_binding'][field]
    assert not _grammar(missing)


@pytest.mark.parametrize('profile', ['privileged', 'presentation'])
def test_both_profile_tuples_are_valid_but_schema1_is_not_real_current(profile):
    binding = _execution(profile)
    assert _current(binding, deepcopy(binding), _parent())
    assert not _current(binding, binding, _parent(), schema=1)
    assert SPEC['currentness']['schema1_real_accepted'] is False
    assert SPEC['currentness']['historical_migration_is_runtime_admission'] is False
    assert 'Historical validation does not\nmake stale records runtime-current' in HELPER


@pytest.mark.parametrize('bad', [True, 0, -1, '3'])
def test_component_and_parent_generation_types_are_closed(bad):
    binding = _execution()
    binding['generation'] = bad
    assert not _grammar(binding)
    binding = _execution()
    binding['pawa_binding']['generation'] = bad
    assert not _grammar(binding)


def test_unknown_profiles_fields_and_identity_prefix_translation_deny():
    for field, value in [('profile', 'root'), ('installation_id', 'hppi-' + '2' * 32),
                         ('installation_digest', 'A' * 64)]:
        binding = _execution()
        binding[field] = value
        assert not _grammar(binding)
    binding = _execution()
    binding['privileged'] = True
    assert not _grammar(binding)
    assert 'no silent schema1 upgrade or alias-prefix translation' in HELPER


def test_all_five_operations_and_three_families_have_exact_profile_partition():
    profiles = SPEC['profiles']
    operations = [o for p in profiles.values() for o in p['operations']]
    assert len(operations) == len(set(operations)) == 5
    assert set(operations) == {'admin_mutation', 'certification_write', 'certification_read', 'ceremony_entry', 'presentation_evidence_write'}
    assert profiles['privileged']['families'] == ['HelperAdminMutationAuthority', 'HelperCertificationWriteAuthority']
    assert profiles['presentation']['families'] == ['HelperPresentationEvidenceAuthority']
    assert 'No H context authorizes the presentation\nfamily, nor P the admin/certification families' in HELPER
    assert 'exact-type/seal recognition, role/subtype restrictions' in HELPER


def test_presentation_has_same_process_actual_election_not_generic_ipc_authority():
    presentation = SPEC['profiles']['presentation']
    assert presentation['requires_actual_election'] == 'APPROVE'
    assert presentation['event_source'] == 'admitted_same_process_ceremony'
    assert 'There is no generic IPC request that can invoke the fifth operation' in HELPER
    assert 'Only that same protected presentation\nprocess' in HELPER
    assert 'REJECT/cancel/expiry/currentness failure yields no evidence' in HELPER


def test_configured_agent_source_is_protected_record_and_live_os_resolution():
    agent = SPEC['configured_agent']
    assert agent['source'] == '.authority/agent-exclusion.json'
    assert agent['schema'] == 'HPAC-PAWA-AGENT-EXCLUSION/1.0'
    assert agent['resolver'] == 'resolve_configured_agent_identity'
    assert all(agent[k] is True for k in ('live_account', 'uid_pin', 'live_groups'))
    assert agent['unresolved'] == 'agent_principal_unknown'
    assert agent['request_authority'] is agent['logical_agent_label_mapping'] is False
    for clause in ('Missing/unresolvable/None identity', 'Kernel SO_PEERCRED',
                   'checking the opposite endpoint is not sufficient', 'Effective group/ACL/ancestor write access'):
        assert clause in HELPER


def test_admission_order_preserves_reads_replay_and_bootstrap_non_circularity():
    assert SPEC['admission_order'] == ['verified_execution', 'private_channel',
        'kernel_peer_and_pawa_recognition', 'request_schema_and_profile', 'freshness_and_durable_replay', 'dispatch']
    for clause in ('before operation-driven reads or ceremony',
                   'trusted bootstrap reads needed for PAWA recognition are not request-driven reads',
                   'Complete PAWA, peer and schema/', 'profile checks before durable replay reservation',
                   'changing the tuple cannot make a consumed ceremony\nunused'):
        assert clause in HELPER


def test_authority_and_runtime_walls_are_explicit():
    walls = SPEC['walls']
    assert all(walls[k] is False for k in ('second_trust_root', 'legacy_factory_import',
        'authority_export', 'authority_persistence', 'generic_writer', 'request_selects_profile'))
    assert walls['runtime'] == 'Observed / observe / unavailable'
    assert walls['plugins'] == walls['capabilities'] == 0
    for clause in ('REQ-033/129/171 prohibition remains exact', 'no legacy factory/seal import',
                   'no Model D', 'no same-interpreter provenance substitute',
                   'clone, JSON/pickle/deepcopy preserve descriptors only',
                   'No _ensure_root bypass is authorized'):
        assert clause in HELPER


_HISTORICAL_ENTRY_COMMIT = '79ea7e1644535d011da6ca3869b5557b44c50737'
_HISTORICAL_FINAL_COMMIT = 'c4f452c6a8e5d45b7076cd984d6f701a01cfa5e4'


def _git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout


def test_historical_identity_contract_repair_phase_touched_zero_production_sources():
    """Repaired by N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR.

    This test used to assert that every current-HEAD `src/pcae/**` file's
    bytes equal this phase's entry-commit (79ea7e16) baseline hashes forever
    -- a permanent global freeze that broke on the very next legitimate
    `src/pcae/**` edit by construction (it was never that; see below).

    The historical N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR
    phase (contract-text only, no production changes authorized) actually
    only ever claimed: THIS phase, from its own entry commit (79ea7e16) to
    its own final commit (c4f452c6), made zero `src/pcae/**` changes. That
    claim is a fixed historical fact, checkable forever against those two
    pinned commits, and does not care what `src/pcae/**` looks like today.
    """
    baseline = json.loads((ROOT / 'docs/evidence/helper-installation-identity/baseline.json').read_text())
    assert baseline['baseline'] == _HISTORICAL_ENTRY_COMMIT
    recorded_source_hashes = {p: digest for p, digest in baseline['hashes'].items() if p.startswith('src/pcae/')}
    assert recorded_source_hashes

    # baseline.json is an accurate historical record of commit 79ea7e16
    # itself (not of today's disk) -- verified against git's own historical
    # blob content at that pinned commit.
    for path, expected in recorded_source_hashes.items():
        historical_bytes = _git('show', f'{_HISTORICAL_ENTRY_COMMIT}:{path}').encode('utf-8')
        assert hashlib.sha256(historical_bytes).hexdigest() == expected, path

    # The actual historical claim: zero src/pcae/** paths differ between this
    # specific phase's own entry and final commits.
    changed = _git('diff', '--name-only', _HISTORICAL_ENTRY_COMMIT,
                    _HISTORICAL_FINAL_COMMIT, '--', 'src/pcae').strip()
    assert changed == '', f'historical phase unexpectedly touched src/pcae paths: {changed}'
