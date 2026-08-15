# Phase 149O.20L.7D.11 — Repaired-Source Dell Redeployment + Action-9 Re-Adjudication Execution

## 0. Phase Identity and Type

**Real-host execution phase.** This phase performed exactly the
independently-verified (7D.10), human-authorized (`chgr-0e37ed1340b14311826722c4dbf3e856`)
repaired-source transition against the live `hac-dell` host and ran
the corrected read-only Action 9. Governed via `ssh hac-dell`
(`192.168.192.200`, user `codex`). Full literal command log is
reproduced below; every command actually run against Dell is either
read-only or one of the exact SS10/SS12/SS16 commands materialized in
`docs/PHASE_149O_20L_7D_9_REPAIRED_SOURCE_REDEPLOYMENT_ACTION_9_INVOCATION_AMENDMENT_PROPOSITION.md`.

## 1. True Phase-Entry Commit

```
$ git log -1 --format=%H
adfcdd78... (Phase 149O.20L.7D.10: sync phase-completion metadata to post-push state)
$ git status --short
(clean)
$ git log --oneline origin/main..HEAD
(empty)
$ git rev-list --count origin/main..HEAD
0
```

## 2. Governing CHGR Currentness (Sec.10)

`chgr-0e37ed1340b14311826722c4dbf3e856` re-read this phase, immediately
before Dell mutation: `lifecycle_state: published`,
`selected_option_id: approve`, `decision_subject` and `rationale` bind
the exact candidate SHA `28bf137b5dc95d024e8913b678dce0501a46fd0f`, the
exact corrected Action-9 PATH
(`/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`), the
no-venv-refresh and unchanged-wrapper conditions, the expected residual
`{HBDC-REQ-042}` with mandatory STOP-on-anything-else semantics, and
the explicit HMIC NOT-CERTIFIED-FOR-BOUNDARY-C disclosure.
`pcae governance-record verify` (with `--related` confirmation/
provenance/integrity artifacts) reports `outcome: verified` across all
seven applicable structural checks. **PASSED.**

## 3. Both Old-CHGR Fallback Rejections (Sec.11)

- `chgr-96a0ce12756e4cc892492a87af1db832` — `decision_subject`/
  `rationale` read directly this phase: no reference to
  `28bf137b...` anywhere in either field. **Not applicable.**
- `chgr-541cb08c313b4f8884970172d37c5a1d` — `decision_subject`/
  `rationale` read directly this phase: no reference to
  `28bf137b...` anywhere in either field. **Not applicable.**

Neither used as fallback authority anywhere in this phase.

## 4. D3-3 Carried Status

`CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION
HARDENING GAP RETAINED` — carried forward unchanged. No formal
revocation or machine-readable supersession is claimed. Execution
safety this phase remained proposition/applicability-based (Sec.2-3
above).

## 5. Candidate Currentness (Sec.11 of governing instruction)

```
$ git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f
commit
$ git merge-base --is-ancestor 28bf137b5dc95d024e8913b678dce0501a46fd0f origin/main && echo yes
yes
$ git diff --stat 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD -- src/ scripts/ docs/contracts/ pyproject.toml
(empty)
```

Zero authority-relevant drift between candidate and current HEAD.

## 6. Candidate Exact Repaired-Byte Verification (Sec.12)

```
$ git diff 28bf137b... HEAD -- <three repaired files>
(empty diffs for all three)
```

Independently re-derived SHA-256 of each file's git blob at the
candidate SHA, cross-checked against the SHA-256 computed live on Dell
of the actually-deployed file bytes after checkout — **exact match**
for all three:

| File | SHA-256 (candidate blob == Dell-deployed file) |
|---|---|
| `hatp_class_b_conformance.py` | `dc2f26e21613e7f600cae8e2ea3187601e4b2ab84741792cf69c7170e1a696b5` |
| `hatp_class_b_topology_verifier.py` | `edba46128d5c18d40843302360dcb161ab20b83dbe3f44b2f0c67f3cae0d5687` |
| `hatp_environment_lock_verifier.py` | `1d28fec0ecc5518cf212b3534b7a0520731e9da2274b45186ce8bb2141b44bea` |

## 7. Candidate Contract Versions (Sec.13)

Read directly from the candidate's own git object:
HBDC-001 **v1.0**, HMIC-001 **v1.3**, HMRC-001 **v1.1** — unchanged
from the old-deployed SHA.

## 8. Dell Machine Identity (Sec.14)

```
$ ssh hac-dell 'cat /etc/machine-id; hostname; cat /etc/os-release; uname -m'
54ff22ce400b475aa0d55cb68f4a3334
atila-Latitude-E5470
Ubuntu 24.04.3 LTS (noble)
x86_64
```

**Exact match.** No mismatch; proceeded.

## 9. Retained Actions 1-5 Gates (Sec.15) — Read-Only

```
id pcae                                     → uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)
/etc/pcae/hatp/trust-store                  → root:pcae 750
/opt/pcae, /opt/pcae/runtime,
/opt/pcae/runtime/venv, /opt/pcae/runtime/bin,
/var/lib/pcae, /var/log/pcae                → all root:pcae 750
/home/pcae                                  → pcae:pcae 750
```

Exact match to the retained baseline everywhere. No mismatch; no
repair performed or needed.

## 10. Source Credential State (Sec.16)

```
/root/.ssh/pcae_harness_deploy_ed25519      → exists, root:root 600
/root/.ssh/config                           → Host github.com, User git,
                                               IdentityFile pcae_harness_deploy_ed25519,
                                               IdentitiesOnly yes
github.com in known_hosts                   → trusted
git ls-remote --exit-code origin HEAD       → READ_OK
```

No test push. No credential mutation. No secret content read.

## 11. Old Source Baseline (Sec.17)

```
HEAD                    → 7a3fa971304521cdcb44251e07ef1966baec686a  EXACT
symbolic-ref -q HEAD    → exit 1 (detached)
status --short          → empty (clean)
remote origin           → git@github.com:atimad/pcae-harness.git
ownership                → root:pcae 750
ls-files | wc -l         → 4030
mode inventory            → 4024x100644, 6x100755
```

Exact match. Proceeding.

## 12. Local Old-Object Rollback Availability (Sec.18)

```
$ ssh hac-dell 'sudo git -C /opt/pcae/runtime/src cat-file -e 7a3fa971...^{commit}'
exit 0 — old object present locally, rollback prerequisite satisfied.
```

## 13. Venv Retained Baseline (Sec.19)

```
.pth                → /opt/pcae/runtime/src/src
direct_url.json      → {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
pip show pcae-harness → Version 0.2.0, Editable project location /opt/pcae/runtime/src
console script        → shebang + `from pcae.cli import main`, no caching
```

Path-bound, not byte-bound. No reinstall required or performed.

## 14. Wrapper Retained Baseline (Sec.20)

```
sha256sum → b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
stat      → root:pcae 750, 188 bytes
wc -l     → 9 lines
symlink?  → no
ACL       → default entries only (user::rwx group::r-x other::---), no extra ACE
```

Exact match. No modification made or authorized.

## 15. No-DeploymentBinding Entry Gate (Sec.21)

```
$ ssh hac-dell 'sudo find /opt/pcae /etc/pcae -iname "*deploymentbinding*"'
(zero matches)
$ find .pcae -iname "*deploymentbinding*"   (this repository)
(zero matches)
```

Confirmed absent before proceeding to mutation.

## 16. Exact Authorized Source-Update Commands (Sec.22)

Recovered verbatim from
`docs/PHASE_149O_20L_7D_9_REPAIRED_SOURCE_REDEPLOYMENT_ACTION_9_INVOCATION_AMENDMENT_PROPOSITION.md`
§9–§12, §16 (the human-approved 7D.9 proposition bound by
`chgr-0e37ed1340b14311826722c4dbf3e856`). No paraphrasing. No
substitute commands. Reproduced in Sec.17-19 below exactly as executed.

## 17. Candidate Fetch Result (Sec.24)

```
$ ssh hac-dell 'sudo git -C /opt/pcae/runtime/src fetch origin 28bf137b5dc95d024e8913b678dce0501a46fd0f'
From github.com:atimad/pcae-harness
 * branch              28bf137b5dc95d024e8913b678dce0501a46fd0f -> FETCH_HEAD
```

Post-fetch object presence: `cat-file -e 28bf137b...^{commit}` → exit
0. Candidate confirmed locally present before checkout.

## 18. Candidate Checkout Result (Sec.26)

```
$ ssh hac-dell 'sudo git -C /opt/pcae/runtime/src checkout --detach 28bf137b5dc95d024e8913b678dce0501a46fd0f'
Previous HEAD position was 7a3fa971 ...
HEAD is now at 28bf137b Phase 149O.20L.7D.7: repair pcae_push_check literal for finalization gate
```

**Candidate full SHA:** `28bf137b5dc95d024e8913b678dce0501a46fd0f`.
Detached (no branch checkout). No `git restore` used.

## 19. Ownership/Mode Mapping Applied (Sec.27)

Exact literal commands executed, byte-identical to the 7D.9
proposition §10:

```
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

## 20. Candidate 4,108-Path Mode Inventory (Sec.28)

Independent Python `os.lstat` cross-check against every one of the
4,108 tracked paths (same script pattern as prior phases, run fresh
against the candidate's own tree):

```
total 4108, ok640 4097, ok750 11, other 0, mismatches 0
```

Zero mismatches. Rollback not triggered.

## 21. Full Read-Back Result (Sec.11 of proposition / Sec.29 of instruction)

```
HEAD                     → 28bf137b5dc95d024e8913b678dce0501a46fd0f  EXACT
symbolic-ref -q HEAD     → exit 1 (detached)
status --short           → empty (clean, no staged changes, no untracked files)
remote origin            → git@github.com:atimad/pcae-harness.git
ls-files | wc -l         → 4108
mode inventory (index)   → 4097x100644, 11x100755
diff 28bf137b -- .       → 0 lines (zero content drift)
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md exists → exit 0
src/pcae/core/hatp_class_b_conformance.py exists          → exit 0
.githooks/pre-commit mode → 750
pyproject.toml mode       → 640
```

**All read-back checks passed exactly.** No rollback required.

## 22. Repaired Verifier Byte Result on Dell (Sec.30)

Independent per-file SHA-256 comparison between candidate git blob (computed
locally) and the actually-deployed file bytes on Dell (computed live via
SSH) — see Sec.6 table above. **Exact byte match, all three files.**
Byte match confirmed via full-file hash, not solely via HEAD SHA.

## 23. Physically-Deployed Repair Evidence (Sec.31-32) — Not Yet "Measured Satisfied"

```
grep 'importlib.metadata.distribution("pcae-harness")' hatp_class_b_conformance.py → present
grep 'is_symlink' / 'writesecurity' hatp_class_b_topology_verifier.py              → present
```

Repair bytes confirmed physically deployed. Requirement-satisfaction is
adjudicated only by the actual Action-9 measurement (Sec.26 below), per
governing-instruction Sec.31-32's explicit distinction.

## 24. Venv-Unchanged Proof (Sec.33)

```
.pth                 → /opt/pcae/runtime/src/src              (unchanged)
direct_url.json      → file:///opt/pcae/runtime/src, editable  (unchanged)
```

No `pip install`, no reinstall, no `.pth`/`direct_url.json`
regeneration performed at any point.

## 25. Runtime-Import Candidate-Source Proof (Sec.34)

Read-only diagnostic import from the deployed venv (no environment
mutation):

```
sudo -u pcae env -i HOME=/home/pcae PATH=/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '<import three modules, print __file__ and sha256>'

pcae.core.hatp_class_b_conformance      /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_conformance.py       dc2f26e2...
pcae.core.hatp_class_b_topology_verifier /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_topology_verifier.py edba4612...
pcae.core.hatp_environment_lock_verifier /opt/pcae/runtime/src/src/pcae/core/hatp_environment_lock_verifier.py 1d28fec0...
```

All three digests match the candidate blob digests exactly (Sec.6).
Runtime confirmed consuming candidate source under
`/opt/pcae/runtime/src/src/...`.

## 26. Wrapper-Unchanged Proof (Sec.35)

```
$ ssh hac-dell 'sudo sha256sum /opt/pcae/runtime/bin/pcae-launch'
b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
```

**Exact match**, unchanged before/after the source transition.

## 27. Source-Transition Rollback (Sec.36-38)

**Not triggered.** Every read-back check (Sec.21), byte-match check
(Sec.22), venv check (Sec.24), runtime-consumption check (Sec.25), and
wrapper check (Sec.26) passed exactly. No rollback command was issued.

## 28. Corrected Action-9 Command (Sec.39 / proposition Sec.16)

Recovered verbatim, no substitution:

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i \
  HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
result = verify_class_b_deployment_conformance()
print(result.status.value)
for c in result.checks:
    print(c.check_id, c.satisfied, c.status)
'"
```

## 29. Corrected PATH Trust Result (Sec.41)

```
which pcae (under corrected PATH)  → /opt/pcae/runtime/venv/bin/pcae
executable stat                    → root:pcae 750 (not pcae-writable)
venv/bin stat                      → root:pcae 750 (not pcae-writable)
ancestor chain (/opt/pcae/runtime/venv, /opt/pcae/runtime, /opt/pcae, /opt)
                                    → root:pcae 750 / root:pcae 750 / root:pcae 750 / root:root 755
shadow-pcae search on remaining PATH segments (/usr/bin, /bin, /usr/sbin, /sbin)
                                    → zero matches
```

No mismatch. Proceeded to Action 9.

## 30. Complete Action-9 Output (Sec.42)

```
NON_COMPLIANT
HBDC-REQ-001  True   protected_root_resolvable_topology_evaluable
HBDC-REQ-002  True   agent_and_admin_are_distinct_os_principals
HBDC-REQ-004  True   no_env_or_name_based_admin_inference_in_source
HBDC-REQ-005  True   no_self_elevation_call_in_source
HBDC-REQ-007  True   agent_has_no_effective_write_access
HBDC-REQ-008  True   designated_agent_writable_artifacts_excluded_by_scope
HBDC-REQ-011  True   public_api_accepts_no_override_parameter
HBDC-REQ-012  True   no_mutation_call_in_source
HBDC-REQ-013  True   protected_root_admin_owned
HBDC-REQ-014  True   protected_root_mode_excludes_group_other_write
HBDC-REQ-015  True   no_group_membership_grants_write
HBDC-REQ-016  True   no_acl_grants_agent_write
HBDC-REQ-017  True   full_ancestor_chain_non_agent_writable
HBDC-REQ-018  True   protected_root_symlink_check_passed
HBDC-REQ-019  True   no_authority_bearing_file_present_nothing_to_check
HBDC-REQ-020  True   directory_entry_replacement_not_possible
HBDC-REQ-021  True   root_present_no_fail_closed_path_needed
HBDC-REQ-025  True   interpreter_and_venv_admin_provisioned
HBDC-REQ-026  True   venv_agent_unwritable
HBDC-REQ-027  True   interpreter_agent_unwritable
HBDC-REQ-028  True   pythonpath_unset
HBDC-REQ-029  True   user_site_disabled
HBDC-REQ-030  True   customization_modules_present_admin_controlled
HBDC-REQ-031  True   pth_files_present_admin_controlled_no_import_lines
HBDC-REQ-032  True   only_expected_meta_path_hooks_present
HBDC-REQ-033  True   cwd_cannot_shadow_canonical_package_location
HBDC-REQ-034  True   all_authority_module_origins_contained
HBDC-REQ-035  True   editable_install_metadata_admin_controlled
HBDC-REQ-036  True   launcher_agent_unwritable
HBDC-REQ-037  True   no_authority_changing_env_injection_channel_open
HBDC-REQ-038  True   git_executable_path_precedence_and_ownership_verified
HBDC-REQ-039  True   third_party_dependencies_covered_by_venv_lock
HBDC-REQ-022  True   model_a_editable_install_confirmed
HBDC-REQ-042  False  no_repository_identity_present
```

Captured complete, unfiltered. Re-run once for determinism (Sec.60):
identical `NON_COMPLIANT` status, identical `['HBDC-REQ-042']` failing
set.

## 31. Exact Measured Failing Set

**`{HBDC-REQ-042}`** — exactly one requirement unsatisfied, exactly as
authorized.

## 32. Expected-vs-Actual Adjudication

Expected: `{HBDC-REQ-042}`. Actual: `{HBDC-REQ-042}`. **Exact match.**
Classified: **Action-9 re-adjudication SUCCESSFUL for this execution
phase.** No unexpected `COMPLIANT` (Sec.45 not triggered — result was
`NON_COMPLIANT`, not `COMPLIANT`). No repair performed. No authority
broadened.

## 33. Per-Requirement Status

| Requirement | Status |
|---|---|
| HBDC-REQ-022 | **MEASURED SATISFIED** under corrected deployed source |
| HBDC-REQ-030 | **MEASURED SATISFIED** under corrected deployed source |
| HBDC-REQ-035 | **MEASURED SATISFIED** under corrected deployed source |
| HBDC-REQ-036 | **MEASURED SATISFIED UNDER CORRECTED INVOCATION** |
| HBDC-REQ-042 | **SOLE EXPECTED RESIDUAL** — no DeploymentBinding authority exists |

## 34. Rollback

**Not used.** Source transition succeeded on first attempt with zero
read-back/byte/venv/wrapper mismatches.

## 35. Actual Mutation Inventory (Sec.61)

Exactly, and only:

1. `git fetch origin 28bf137b...` into the existing Dell checkout
   (adds objects only).
2. `git checkout --detach` old SHA → candidate SHA.
3. `chown -R root:pcae` + two-branch `chmod` mode normalization for the
   candidate's own tracked source tree (`0750` dirs, `0750`
   executable-bit files, `0640` non-executable files).

**No** venv mutation. **No** wrapper mutation. **No** Actions 1-5
mutation. **No** credential mutation. **No** binding/certification/
activation mutation. **No** repository mutation (this Mac's own
working tree, `.pcae/` records, and CHGRs are all unchanged — confirmed
`git status --short` clean throughout except for this phase's own new
doc/test/task/metadata files).

## 36. Separation from Historical Retained State (Sec.62)

Distinct from: 7D.1's deploy credential provisioning (read-only
reverified, never touched); prior Actions 1-5 infrastructure
(read-only reverified, never re-run); prior venv/wrapper creation
(read-only reverified, never touched). This phase's own mutation is
confined strictly to Sec.35 above.

## 37. Final Source State

`28bf137b5dc95d024e8913b678dce0501a46fd0f`, detached, clean,
`root:pcae 750`, 4,108 tracked paths (4,097×`0640`, 11×`0750`, zero
mismatches — independently re-verified post-success).

## 38. Final Venv State

Unchanged: `.pth` → `/opt/pcae/runtime/src/src`; `direct_url.json` →
`file:///opt/pcae/runtime/src`, `editable: true`; `pip show` still
reports `Version: 0.2.0`, `Editable project location:
/opt/pcae/runtime/src`.

## 39. Final Wrapper State

Unchanged digest `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`
— re-verified post-success.

## 40. HMIC Source-Identity Status

**CANDIDATE HMIC IMPLEMENTATION/SOURCE IDENTITY DEPLOYED — NOT
CERTIFIED.** HMIC-001 contract identity remains v1.3, unchanged.
Implementation/source identity digest is now `4e3452ba...` on Dell
(was `b728d368...`). No HMIC certification computed, requested, or
granted — even though Action 9 measured only `HBDC-REQ-042` residual.

## 41. DeploymentBinding State

**ABSENT / NOT AUTHORIZED.** Re-verified absent both before (Sec.15)
and after (Sec.20 of the "Post-success" checks, folded into Sec.35's
mutation inventory — no binding artifact created anywhere).

## 42. Boundary C / Boundary A / HATP State

**NOT AUTHORIZED / NOT READY.** No HMIC certification computed. No
`HATP_MANDATORY` activation. No Cutover Record created. No runtime
elevation.

## 43. Runtime State

```
$ pcae runtime inspect
Runtime status: not_implemented
Runtime state: Observed
Execution capability: unavailable
```

Unchanged throughout — provisioning/redeployment does not change
runtime capability.

## 44. CHGR Integrity (Sec.63)

```
$ git status --short .pcae/publication-execution/records/
(empty)
```

`chgr-0e37ed1340b14311826722c4dbf3e856` and both historical CHGRs
confirmed byte-unchanged by this phase. No consumption/supersession
state invented.

## 45. Historical-Test Migration Status

Carried unchanged from 7D.8: `REGRESSION CLEAN WITH EXPECTED
HISTORICAL TEST MIGRATION REQUIRED`. No test migration performed this
phase; no execution gate this phase depended on the migration debt.

## 46. Tests

`tests/test_phase_149o_20l_7d_11_repaired_source_dell_redeployment_action_9_re_adjudication_execution.py`
— new, independent companion module. Result recorded in
`.pcae/phase-completion-metadata.json`.

## 47. Governance Results

`pcae check` passed. `pcae health` healthy. `pcae status coherence`
coherent. `pcae doctor task-memory`: pre-existing warnings only
(historical `tasks/done/` entries missing from `tasks/DONE.md`,
predating this phase, outside this phase's allowed-file scope — not
remediated here). `pcae push check`: clean before this phase's own
commits. `pcae runtime inspect`: `Observed / observe / unavailable`.
Telegram: configured/enabled.

## 48. Commits / Pushed Status / origin/main..HEAD

Recorded in `.pcae/phase-completion-metadata.json` at finalization
time, per this project's established governed finalization procedure.

## 49. Exact Recommended Next Phase (Sec.71-72)

**149O.20L.7E — Dell Class-B Real Host Provisioning Independent
Verification.** Contingent on this phase's clean success (confirmed
above): 7E must independently inspect actual Dell state without
trusting this report — re-verifying governing-authority relationship,
candidate deployment/bytes/modes, source cleanliness, venv/wrapper
unchanged, corrected Action-9 environment, the actual measured residual
`{HBDC-REQ-042}`, DeploymentBinding absence, HMIC source-identity
changed-but-not-certified status, absence of unrelated mutation, and
unchanged runtime. 7E must not begin Boundary C.
