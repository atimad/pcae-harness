"""Independent contract IV. Passing findings tests reproduce a BLOCKED verdict.
No production admission implementation or imported predecessor model is used.
"""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.fast_green
ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs/evidence/helper-installation-identity-iv'
BASE = json.loads((E / 'baseline.json').read_text())
INV = json.loads((E / 'inventory.json').read_text())
M = json.loads((E / 'matrices.json').read_text())
GRAPH = json.loads((E / 'trust-graph.json').read_text())
TEXT = {k: (ROOT / 'docs/contracts' / v['file']).read_text() for k, v in INV.items()}


def clause(contract, number):
    return ' '.join(next(r['text'] for r in INV[contract]['requirements'] if r['id'].endswith('-' + number)).split())


def acyclic(edges):
    pending = set(itertools.chain.from_iterable(edges))
    while pending:
        roots = {n for n in pending if not any(a in pending and b == n for a, b in edges)}
        if not roots:
            return False
        pending -= roots
    return True


@pytest.mark.parametrize('name,version,count,max_id,invariants', [
    ('HELPER','4.0',184,183,24), ('PAWA','3.0',344,344,17), ('PPA','2.1',108,108,12)])
def test_independent_inventory(name,version,count,max_id,invariants):
    d=INV[name]
    assert d['version']==version
    assert len(d['requirements'])==count==len({r['id'] for r in d['requirements']})
    nums=[int(r['id'].rsplit('-',1)[1]) for r in d['requirements'] if r['id'][-1].isdigit()]
    assert sorted(nums)==list(range(1,max_id+1))
    assert len(set(d['invariants']))==invariants
    assert BASE['predecessor'] in TEXT[name].split('##',1)[0]
    assert 'FROZEN' in TEXT[name][:1600] and 'PENDING' in TEXT[name][:1600]


@pytest.mark.parametrize('name', list(INV))
def test_all_self_requirement_references_resolve(name):
    prefix=INV[name]['requirements'][0]['id'].rsplit('-',1)[0]
    refs=set(re.findall(r'\b'+prefix+r'-\d+[A-Z]?\b',TEXT[name]))
    assert refs <= {r['id'] for r in INV[name]['requirements']}
    assert all(r['section'] and r['traceability'] and r['text'] for r in INV[name]['requirements'])


@pytest.mark.parametrize('matrix,case',[(k,r) for k,rows in M.items() for r in rows],ids=[k+':'+r['case'] for k,rows in M.items() for r in rows])
def test_complete_fresh_matrix_and_normative_trace(matrix,case):
    assert len(M)==12
    assert case['result'] in {'PERMIT','DENY','NOT APPLICABLE','DEFERRED IMPLEMENTATION DEPENDENCY'}
    required={'identity_source','identity_consumer','trusted_origin','currentness_proof','installation_binding','generation_binding','peer_binding','configured_agent_binding','request_controllability','replayability','failure_mode','authority_conveyed','authority_not_conveyed'}
    assert all(case[k] for k in required)
    for ref in case['requirements']:
        name,num=re.fullmatch(r'(HELPER|PAWA|PPA)(\d+)',ref).groups()
        assert clause(name,num)


def test_runtime_identity_graph_is_directional_but_bootstrap_graph_cycles():
    assert acyclic(GRAPH['runtime_edges'])
    assert not acyclic(GRAPH['bootstrap_edges'])
    assert 'PAWA never needs H/P registration' in clause('PAWA','341')
    assert 'transaction is itself driven through the §33C helper boundary' in clause('PAWA','328')
    assert 'RegisteredGenerationMatch' in clause('PAWA','311')


@pytest.mark.parametrize('action', ['install','rotate','revoke'])
def test_f1_no_consistent_executor_for_initial_or_sole_current_lineage(action):
    # Literal contract constraints:328 routes registration mutation via admitted H;
    #311/342 require current H first;175 bars its own executing lineage changes.
    def admitted_executor(kind, registered, own_lineage):
        return kind=='H' and registered and not own_lineage
    initial = action=='install'
    candidates=[('external',False,False),('P',True,False),('H',not initial,not initial)]
    assert not any(admitted_executor(*c) for c in candidates)
    assert 'external' in clause('HELPER','175')
    assert 'register/rotate/revoke its own active executing lineage' in clause('HELPER','175')
    assert 'written by a verified helper process' in clause('PAWA','328')
    assert 'PAWA writer provenance' in clause('HELPER','023')
    assert 'HPAC-PAWA-HELPER-INSTALLATION' not in clause('PAWA','056')
    assert 'agent-exclusion' in clause('PAWA','194').lower() or 'AGENT-EXCLUSION' in clause('PAWA','194')


def test_f1_is_not_hidden_by_assuming_external_coordinator_changes_executor():
    assert 'external' in clause('PAWA','343')
    assert 'admin_mutation' in clause('PAWA','328')
    assert 'replaces REQ-328' not in TEXT['PAWA']
    assert 'supersedes REQ-328' not in TEXT['HELPER']
    assert GRAPH['findings'][0]['verdict']=='BLOCKING'


@pytest.mark.parametrize('bad', [None,'',{},[],{'uid':None},{'uid':0},{'uid':17,'trusted':False},{'uid':17,'ambiguous':True}])
def test_agent_fail_closed_specification_vectors(bad):
    # Independent requirement model, never production authorization.
    def eligible(agent):
        return isinstance(agent,dict) and agent.get('trusted') is True and agent.get('ambiguous') is False and type(agent.get('uid')) is int and agent['uid'] != 0
    assert not eligible(bad)
    assert 'Missing/unresolvable/None identity' in clause('HELPER','178')
    assert 'never task label or caller claim' in clause('PAWA','344')


def test_positive_os_identity_topology_is_satisfiable_without_aliasing_installations():
    owner,helper,peer,agent=0,0,0,65534
    assert helper==peer==owner and helper!=agent
    ids=['hpawi-'+'a'*32,'hpahi-'+'a'*32,'hppi-'+'a'*32]
    assert len(set(ids))==3
    assert 'both' in clause('HELPER','178').lower()
    assert 'Equal integer values do not bind them' in clause('PPA','104')


@pytest.mark.parametrize('field', ['profile','installation_id','generation','installation_digest','helper_sha256','pawa_binding'])
def test_mixed_or_stale_execution_tuple_never_matches_live_tuple(field):
    live=dict(profile='privileged',installation_id='hpahi-'+'a'*32,generation=7,installation_digest='a'*64,helper_sha256='b'*64,pawa_binding={'installation_id':'hpawi-'+'c'*32,'generation':3,'descriptor_digest':'d'*64,'agent_exclusion_digest':'e'*64,'protected_root_identity':{'device':1,'inode':2}})
    supplied=copy.deepcopy(live);supplied[field]='attacker-or-stale'
    assert supplied != live
    assert 'At admission and immediately before mutation' in clause('HELPER','176')
    assert 'invalidates outstanding admission' in clause('HELPER','181')


@pytest.mark.parametrize('missing',range(13))
def test_every_pawa_admission_conjunct_is_necessary(missing):
    predicates=[True]*13;predicates[missing]=False
    assert not all(predicates)
    assert 'failure of **ANY** conjunct' in clause('PAWA','311')
    assert 'All other conjuncts' in clause('PAWA','342')


def test_p_ceremony_admission_and_write_eligibility_remain_distinct():
    assert 'before presentation' in clause('HELPER','180')
    assert 'after independently observing one valid APPROVE' in clause('HELPER','180')
    assert 'internal event cannot' in clause('HELPER','180')
    assert 'CEREMONY_ADMITTED' in clause('PPA','091')
    assert 'internal post-election persistence action' in clause('PPA','106')


def test_identity_data_copy_does_not_prove_admission_or_writer():
    data={'installation_id':'hpahi-'+'a'*32}
    assert json.loads(json.dumps(data))==copy.deepcopy(data)==data
    assert 'descriptors only, never active authority' in clause('HELPER','179')
    assert 'never a replacement writer' in clause('HELPER','176')
    assert '**no** generic' in clause('PAWA','324').lower()


def test_versioning_is_authority_semantics_not_schema_number_semver():
    assert 'MAJOR' in clause('HELPER','183') and 'REQ-108' in clause('HELPER','183')
    assert 'MAJOR' in clause('PAWA','344') and 'REQ-153' in clause('PAWA','344')
    assert 'tighten a bound' in clause('PPA','070')
    assert 'MINOR under REQ-070' in clause('PPA','108')
    assert 'sole evidence author' in clause('PPA','106')


def test_whole_production_and_contract_baseline_byte_identity():
    for field in ('source_hashes','contract_hashes'):
        for file,digest in BASE[field].items():
            assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==digest,file
    assert set(BASE['source_hashes'])=={str(f.relative_to(ROOT)) for f in (ROOT/'src/pcae').rglob('*.py')}


def test_current_source_defects_are_evidence_not_silently_repaired():
    import inspect
    from pcae.core.hpac_pawa_helper_entrypoint import handle_one_request
    from pcae.core.hpac_pawa_helper_protocol import HelperContext
    from pcae.core.hpac_pawa_helper_os import authenticate_peer
    assert 'authenticate_peer' not in inspect.getsource(handle_one_request)
    assert not any('admission' in x for x in HelperContext.__dataclass_fields__)
    assert 'agent_identity is not None' in inspect.getsource(authenticate_peer)
    assert inspect.signature(authenticate_peer).parameters['configured_agent'].default is None


def test_model_e_and_legacy_factory_wall_unchanged():
    s=(ROOT/'src/pcae/core/hpac_pawa_helper_writer_authority.py').read_text()
    tree=ast.parse(s)
    for name in ('HelperAdminMutationAuthority','HelperCertificationWriteAuthority','HelperPresentationEvidenceAuthority'):
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
        assert not any(isinstance(b,ast.Name) and b.id=='HPACWriterCapability' for b in node.bases)
    assert 'no legacy factory/seal import' in clause('HELPER','183')
    assert 'No H context authorizes the presentation' in clause('HELPER','176')


def test_foundation_read_dependency_separate_from_bootstrap_contract_defect():
    import inspect
    from pcae.core.hpac_foundation import HPACStoreAuthority
    assert '_ensure_root' in inspect.getsource(HPACStoreAuthority.verify_record)
    assert '_PRODUCTION_WRITER_FACTORY_SEAL' in inspect.getsource(HPACStoreAuthority._bind_configured_agent_identity)
    assert 'canonical reads AND writes' in clause('HELPER','183')
    assert 'trusted bootstrap reads' in clause('HELPER','179')
    assert 'No _ensure_root bypass' in clause('HELPER','183')


def test_platform_and_mobile_neutrality_not_identity_authority():
    assert 'platform cannot' in clause('HELPER','029') and 'STOPS BLOCKED' in clause('HELPER','029')
    assert 'Kernel SO_PEERCRED' in clause('HELPER','178')
    assert 'no new authentication method' in clause('PPA','106')
    assert 'Human' in clause('HELPER','178')


def test_runtime_and_scope_remain_closed():
    s=(ROOT/'PROJECT_STATUS.md').read_text()
    assert 'Observed / observe / unavailable' in s
    assert 'N-16-5 OPEN' in s
    assert 'N-16-6/N-16-7 untouched' in s
