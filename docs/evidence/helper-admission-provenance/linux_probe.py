import os,sys,json,socket,subprocess,pwd,runpy
from pathlib import Path
root=Path('/etc/pcae/hpac/protected-root')
if len(sys.argv)>1 and sys.argv[1]=='setup':
    from pcae.core.hpac_protected_admin_writer import provision_protected_root
    fixture=runpy.run_path('tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py')
    account=pwd.getpwnam('nobody')
    provision_protected_root(protected_root=root,agent_account='nobody',agent_uid=account.pw_uid)
    installed=fixture['_install_mechanism'](fixture['_authority'](root),root)
    print(installed.record.installation_id)
    raise SystemExit(0)
ppa=subprocess.check_output([sys.executable,__file__,'setup'],text=True).strip()
# Setup imports legacy only in a separate disposable provisioner process.
from pcae.core.hpac_foundation import HPACStoreAuthority,read_canonical_json_document
from pcae.core.hpac_pawa_helper_os import authenticate_peer,get_kernel_peer_credential
from pcae.core.hpac_pawa_agent_exclusion import ConfiguredAgentAuthorityIdentity
from pcae.core.hpac_pawa_helper_writer_authority import mint_and_perform_admin_mutation
from pcae.core.hpac_pawa_helper_store_adapter import resolve_launcher_deployment_metadata
assert 'pcae.core.hpac_protected_admin_writer' not in sys.modules
store=HPACStoreAuthority.production()
pawa=read_canonical_json_document(root/'.authority/deployment-owner.json')['installation_id']
try:
    resolve_launcher_deployment_metadata(store)
    metadata_error=None
except Exception as exc:
    metadata_error=str(exc)
out={'kernel':os.uname().sysname,'helper_uid':os.geteuid(),'agent_uid':pwd.getpwnam('nobody').pw_uid,
     'root_mode':oct(root.stat().st_mode & 0o777),'pawa_id':pawa,'ppa_id':ppa,'legacy_imported':False,'production_metadata_read_error':metadata_error}
a,b=socket.socketpair()
try:
    out['kernel_peer']=get_kernel_peer_credential(a).__dict__
    out['none_admission']=authenticate_peer(a,deployment_owner_uid=os.geteuid()).__dict__
    same=ConfiguredAgentAuthorityIdentity(os.geteuid(),frozenset({os.getegid()}),'root','0'*64)
    try:authenticate_peer(a,deployment_owner_uid=os.geteuid(),configured_agent=same)
    except Exception as e:out['explicit_same_identity']=str(e)
    distinct=ConfiguredAgentAuthorityIdentity(pwd.getpwnam('nobody').pw_uid,frozenset({pwd.getpwnam('nobody').pw_gid}),'nobody','0'*64)
    out['explicit_distinct_identity']=authenticate_peer(a,deployment_owner_uid=os.geteuid(),configured_agent=distinct).__dict__
finally:a.close();b.close()
for label,installation in [('contract_hpahi','hpahi-'+'a'*32),('current_hppi',ppa)]:
    try:
        mint_and_perform_admin_mutation(store,mutation='enroll_principal',subject='hp-'+'a'*32,session_id='disposable',request_id=label,installation_id=installation,generation=1,operation_params={'enrollment_provenance_ref':'disposable','enrolled_at':'2026-09-18T00:00:00Z'})
        out[label]='UNEXPECTED WRITE'
    except Exception as e:out[label]={'type':type(e).__name__,'error':str(e)}
try:store._ensure_root(create=True)
except Exception as e:out['foundation']=str(e)
assert pawa.startswith('hpawi-') and ppa.startswith('hppi-')
assert 'not protected from the configured agent principal' in out['contract_hpahi']['error']
assert 'not protected from the configured agent principal' in out['foundation']
assert not (root/'human-principals').exists()
print(json.dumps(out,indent=2))
