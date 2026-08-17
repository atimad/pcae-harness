# Phase 149O.20L.7N.4 — Dell Current-Source Redeployment Execution

## 0. Status

**Execution-only, completed successfully.** This phase executed the exact, independently verified Dell source-only redeployment authorized by `chgr-71bd24f9d3d742d6baac772e480fc876` and independently verified by Phase 149O.20L.7N.3. Live SSH access to `hac-dell` was opened this phase for the first time in this chain segment (7N/7N.1/7N.2/7N.3 all performed zero Dell access). All mutation commands were recovered directly from the canonical proposition, `docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md` §15–§21/§35, not reconstructed from conversational memory. No RepositoryIdentity created. No DeploymentBinding created. No HMIC certification performed. Boundary C, Boundary A, and HATP activation remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `e3440957` (`Phase 149O.20L.7N.3: sync active task allowed-file list`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

## 1. Governing Authority

Sole governing authority: `chgr-71bd24f9d3d742d6baac772e480fc876`, independently re-verified by Phase 149O.20L.7N.3 (governing decision session `CDS-64779ace-4532-43ed-af46-8727c1378552`, APPROVE + separate cryptographically-tied confirmation). No historical CHGR was used as fallback; the four historical records (`chgr-d4343fa5...`, `chgr-96a0ce12...`, `chgr-541cb08c...`, `chgr-0e37ed13...`) remain explicitly inapplicable per the proposition's own §40 analysis, carried unchanged. D3-3 status carried unchanged: CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION HARDENING GAP RETAINED. No supersession invented.

## 2. Candidate Currentness Recheck (local, pre-Dell-access)

```
git cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> commit
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f    -> commit
```

Both objects confirmed present in the local (Mac) object store before any Dell access, per the candidate-currentness and rollback-object-locality gates.

## 3. Fresh Dell Identity Gate (live, read-only)

```
ssh hac-dell 'hostname; cat /etc/machine-id'
    hostname    -> atila-Latitude-E5470   (exact match)
    machine-id  -> 54ff22ce400b475aa0d55cb68f4a3334  (exact match)
```

## 4. Fresh Preflight Baseline (live, read-only, against proposition §12/§13)

| Item | Expected | Live (this phase) | Match |
|---|---|---|---|
| OS | Ubuntu 24.04.3 LTS, amd64 | Ubuntu 24.04.3 LTS, x86_64 | Yes |
| Current source SHA | `28bf137b5dc95d024e8913b678dce0501a46fd0f` | same | Yes |
| Detached | yes | `symbolic-ref -q HEAD` exit 1 | Yes |
| Clean | yes | empty `status --short` | Yes |
| Remote | `git@github.com:atimad/pcae-harness.git` | same | Yes |
| core.fileMode | true | true | Yes |
| Rollback object local | commit | `commit` | Yes |
| Candidate object local (pre-fetch) | absent | absent (`fatal: could not get object info`) | Yes |
| Tracked paths | 4108 (4097×644, 11×755) | same | Yes |
| RepositoryIdentity | absent | no matches | Yes |
| DeploymentBinding | absent | no matches | Yes |
| Venv `.pth` | `/opt/pcae/runtime/src/src` | same | Yes |
| Venv `direct_url.json` | editable, `file:///opt/pcae/runtime/src` | same | Yes |
| Wrapper digest | `b3e969128ff...753c32` | same | Yes |
| Deploy key | root:root 0600 priv / 0644 pub | same | Yes |

No drift found. No STOP triggered. Execution proceeded.

## 5. First Mutation Boundary

The first mutating command was the exact authorized `git fetch` (proposition §15/§58/§63). Everything before it (identity gate, baseline preflight, object-store checks) was strictly read-only.

## 6. Exact Mutation Sequence Executed (recovered verbatim from proposition §15–§21)

```
sudo git -C /opt/pcae/runtime/src fetch origin b0840e96a7ffb12308e95828aa5927c3e7c770c0
    -> exit 0; FETCH_HEAD updated

sudo git -C /opt/pcae/runtime/src cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0
    -> commit

sudo git -C /opt/pcae/runtime/src checkout --detach b0840e96a7ffb12308e95828aa5927c3e7c770c0
    -> exit 0; "Previous HEAD position was 28bf137b ..."; "HEAD is now at b0840e96 ..."

sudo chown -R root:pcae /opt/pcae/runtime/src
    -> exit 0

sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
    -> exit 0 (all three)
```

No branch/moving ref was used anywhere; only full 40-hex-character SHAs. No `git pull`. No command outside `/opt/pcae/runtime/src`.

## 7. Full Post-Mutation Read-Back (proposition §20–§30)

```
git rev-parse HEAD                     -> b0840e96a7ffb12308e95828aa5927c3e7c770c0  EXACT
git symbolic-ref -q HEAD; echo $?      -> exit 1 (detached)
git status --short --untracked-files=all -> (empty)
git remote get-url origin              -> git@github.com:atimad/pcae-harness.git
git ls-files | wc -l                   -> 4200
git ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c -> 4186 100644 / 14 100755
git diff b0840e96a7... -- . | wc -l    -> 0  (zero content-byte drift)
git config core.fileMode               -> true
```

**Independent `os.lstat` cross-check** (Python, run as root, all 4200 tracked paths):

```
total 4200, ok640 4186, ok750 14, other 0, mismatches 0
```

## 8. Thirty-Member HMIC Byte Identity

All 30 frozen authority-bearing files (23 `src/pcae/`-relative + 7 repository-root-relative, per proposition §4, including both `hatp_deployment_binding_admin.py` producer surfaces) individually diffed against the candidate blob:

```
for f in <all 30 canonical paths>; do
  git diff b0840e96a7... -- "$f" | wc -l
done
-> every line 0
```

**Zero mismatches across all 30 files.**

## 9. Live HMIC Implementation Digest

```
sudo -u pcae ... /opt/pcae/runtime/venv/bin/python3 -c 'derive_implementation_scope_digest(...)'
    -> 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
```

**Exact match** to the candidate-derived expected value (proposition §3).

## 10. Live Contract Versions

```
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                                -> Version: 1.1
docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md  -> Version: 1.4
docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md                    -> Version: 1.1
```

Exact match to proposition §2/§24. No stale old-source values observed.

## 11. Producer Import / Byte Verification

```
python3 -c 'import pcae.core.hatp_deployment_binding_admin as m; print(m.__file__)'
    -> /opt/pcae/runtime/src/src/pcae/core/hatp_deployment_binding_admin.py

git diff b0840e96a7... -- src/pcae/core/hatp_deployment_binding_admin.py | wc -l
    -> 0
```

Import only — no function of the module was invoked.

## 12. Admin Script Verification

```
sudo test -f /opt/pcae/runtime/src/scripts/hatp_deployment_binding_admin.py; echo $?  -> 0
git diff b0840e96a7... -- scripts/hatp_deployment_binding_admin.py | wc -l            -> 0
```

Existence and byte-match only — no `create`/`rotate`/`revoke` invocation.

(Note: an initial non-`sudo` `test -f` against the same path returned a false "absent" due to the tree's `0750` mode denying access to the unprivileged SSH login user — corrected immediately by re-running with `sudo`, which succeeded. No repair, no state change; a read-only tooling correction only.)

## 13. Agent Reachability

```
sudo -u pcae env -i ... which pcae   -> /opt/pcae/runtime/venv/bin/pcae, exit 0
```

Only the admin-controlled launcher resolves; no separate agent-reachable entry point for the DeploymentBinding producer/admin script exists under the candidate, consistent with 7D.6/7D.9/7D.11's established posture.

## 14. Venv Postcondition

```
.pth              -> /opt/pcae/runtime/src/src           (unchanged)
direct_url.json   -> editable: true, file:///opt/pcae/runtime/src (unchanged)
pip show pcae-harness -> Version: 0.2.0, unchanged
```

No pip operation occurred.

## 15. Wrapper Postcondition

```
sudo sha256sum /opt/pcae/runtime/bin/pcae-launch
    -> b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32  EXACT MATCH, unchanged
```

## 16. RepositoryIdentity / DeploymentBinding / Certification Postcondition

```
find /opt/pcae /etc/pcae -iname '*repositoryidentity*'  -> (empty)
find /opt/pcae /etc/pcae -iname '*deploymentbinding*' -not -path '*runtime/src*' -> (empty)
```

Both still absent. No certification artifact created. No `pcae init`, no `ensure_repository_identity()`, no producer mutation call.

## 17. Optional HBDC Diagnostic (proposition §33)

```
verify_class_b_deployment_conformance()
    -> NON_COMPLIANT
    -> every HBDC-REQ-* True except HBDC-REQ-042 False (no_repository_identity_present)
```

**Exact expected residual** — matches proposition §33/§36 precisely. Not a rollback trigger.

## 18. Rollback Decision

**Not triggered.** No read-back line, mode check, content check, HMIC-file check, digest check, venv/wrapper postcondition, or HBDC diagnostic deviated from the proposition's expected values at any point. Rollback commands (proposition §35, network-independent, local-object-only) were reviewed but not executed.

## 19. Mutation Inventory (exact)

1. Git object-store fetch of one commit object (`b0840e96a7...`) into `/opt/pcae/runtime/src/.git`.
2. Detached checkout of that commit at `/opt/pcae/runtime/src`.
3. `chown -R root:pcae` of `/opt/pcae/runtime/src`.
4. Mode normalization (`0750` dirs, `0750`/`0640` files per Git's own on-disk exec bit) of `/opt/pcae/runtime/src`.

No other host path, user, service, or credential was touched. `hac-windows` was not accessed. Venv and wrapper are confirmed byte/state-unchanged.

## 20. Boundary State

- Boundary C: not authorized (unchanged).
- Boundary A: not authorized (unchanged).
- HATP activation: not authorized (unchanged).
- Runtime: Observed / observe / unavailable (unchanged).

## 21. CHGR Post-Execution Integrity

`chgr-71bd24f9d3d742d6baac772e480fc876` was not re-published, amended, or mutated by this phase. Historical CHGR records untouched. `.pcae/publication-execution/` unmodified by this phase (only local repository governance bookkeeping — task lifecycle, this doc, phase-completion metadata — changed).

## 22. Final Verdict

**REDEPLOYMENT EXECUTED SUCCESSFULLY — INDEPENDENT VERIFICATION PENDING.**

| Item | Status |
|---|---|
| Dell source | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` — DEPLOYED — INDEPENDENT VERIFICATION PENDING |
| HMIC v1.4 implementation/source identity | DEPLOYED — NOT CERTIFIED |
| HMIC certification | absent |
| RepositoryIdentity | absent |
| DeploymentBinding | absent |
| HBDC diagnostic | NON_COMPLIANT {HBDC-REQ-042} — expected pre-first-use residual |
| Boundary C / Boundary A | not authorized |
| HATP | not ready |
| Runtime | Observed / observe / unavailable |

## 23. Recommended Next Phase

**149O.20L.7N.5 — Dell Current-Source Redeployment Independent Verification.** Must independently re-inspect the live Dell host from scratch (fresh SSH session, no reuse of this phase's own findings as an oracle) and re-derive: candidate exact SHA, detached/clean state, all 4200 path modes, tracked-content identity, all 30 HMIC authority-bearing bytes, implementation digest, contract versions, producer/admin availability, venv/wrapper unchanged, RepositoryIdentity/DeploymentBinding absence, HBDC expected residual, no unrelated host mutation, governing CHGR unchanged. Only after a clean 7N.5 may first-use RepositoryIdentity/DeploymentBinding proposition preparation (Transition 2) begin.

## Proof of No Prohibited Action

- **No election initiated:** no `pcae decision-session`/`pcae governance-record`/`pcae authority` command that creates or advances authority state was invoked this phase.
- **No new CHGR published.**
- **No RepositoryIdentity created:** §16.
- **No DeploymentBinding created:** §16.
- **No certification performed:** §9's digest is source identity only, not characterized as certification.
- **No activation:** Boundary C/A/HATP remain NOT AUTHORIZED, §20.
- **No unrelated Dell mutation:** §19 — mutation inventory bounded to exactly `/opt/pcae/runtime/src`.

## Governance

Normal governed PCAE lifecycle used throughout (`pcae task`, `pcae commit implementation`, `pcae phase complete`, `pcae push`). No raw `git commit`/`git push`. No `--no-verify`. No force push. No hook/finalization bypass.
