# Phase 149O.20L.7N — Dell Current-Source Redeployment Proposition + Authority Preparation

## 0. Status

**Proposition + authority-preparation only.** No human election initiated. No APPROVE/DECLINE/AMEND presented. No CHGR published. No Dell mutation (no SSH session to any Dell host was opened this phase — every fact below is either independently re-derived from the local git object store and production source, or cited from prior phases' own independently verified, same-week live Dell evidence). No RepositoryIdentity created. No DeploymentBinding created. No producer invoked. No HMIC certification performed. Boundary C, Boundary A, HATP activation, and Cutover Record all remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `b83d6623c0dea24bad699f52aa6861804a0f29dd` (`Phase 149O.20L.7M: repair pcae_push_check literal and pushed_status field for finalization gate`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

**Governing entering architecture (149O.20L.7M):** the two-transition sequence — Transition 1 (this line of work): current verified source redeployment to Dell; Transition 2 (separately governed, later): RepositoryIdentity + DeploymentBinding first use. This phase does not combine them.

## 1. Candidate Currentness Gate (§3)

```
cd ~/repos/pcae-harness
git cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0   -> commit
git merge-base --is-ancestor b0840e96a7ffb12308e95828aa5927c3e7c770c0 origin/main -> exit 0 (ancestor)
git rev-parse HEAD                                          -> b83d6623c0dea24bad699f52aa6861804a0f29dd
git rev-parse origin/main                                   -> b83d6623c0dea24bad699f52aa6861804a0f29dd
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f     -> commit
git rev-list --count b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -> 8
```

Candidate `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (`Phase 149O.20L.7L.6: repair commit-hash mention in canonical staging report for finalization gate`) is a genuine ancestor of the current `origin/main`/`HEAD`. Old rollback-target SHA `28bf137b5dc95d024e8913b678dce0501a46fd0f` is a valid, locally present commit object.

**Authority-relevant drift check, candidate → HEAD (8 commits):**

```
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0 HEAD -- src/pcae scripts docs/contracts schemas pyproject.toml
    -> (empty — zero changes)
```

Full diffstat of the 8 intervening commits (all outside the authority-bearing surface):

```
.pcae/phase-completion-metadata.json                                        | 113 ++---
.pcae/phase-completion-report.md                                            | 125 ++---
CHANGELOG.md                                                                 |  18 +
PROJECT_STATUS.md                                                            |  53 +++
docs/PHASE_149O_20L_7M_DELL_REDEPLOYMENT_DEPLOYMENTBINDING_FIRST_USE_...md   | 501 +++++
tasks/DONE.md                                                                |   1 +
tasks/done/...idle-awaiting-next-governed-phase-post-149o-20l-7m.md         |  87 ++++
tasks/done/...dell-redeployment-deploymentbinding-first-use-sequencing...md |  75 +++
tests/...test_dell_redeployment_deploymentbinding_first_use_sequencing...py | 386 +++
```

All 9 files are governance bookkeeping (phase-completion metadata/report, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`/`tasks/done/`), the 149O.20L.7M architecture doc itself, and its companion test file — none touch `src/pcae/**`, `scripts/**`, `docs/contracts/**`, `schemas/**`, or `pyproject.toml`. **No authority-bearing drift found. Candidate remains current. Proposition preparation proceeds — no STOP.**

## 2. Candidate Contract State (§4)

Read directly from candidate blobs (`git show b0840e96a7...:<path>`), not inherited from 7M's prose:

| Contract | Contract ID | Version |
|---|---|---|
| `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` | HBDC-001 | **1.1** |
| `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` | HMIC-001 | **1.4** |
| `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` | HMRC-001 | **1.1** |

HMIC-001 v1.4 header (candidate blob): "Amended by: Phase 149O.20D (v1.1 → v1.2 ...); Repaired by: Phase 149O.20D.1 (... same version, additionally binding HBDC-001's document bytes ...)". No other HMIC-bound contract exists beyond the five listed in the frozen repository-root-relative set (§3 below).

## 3. Candidate HMIC Implementation Identity (§5)

Computed live against a detached candidate worktree (`git worktree add --detach <scratch> b0840e96a7...`), not copied from 7M:

```python
from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
from pcae.core.paths import HarnessPath
from pathlib import Path
derive_implementation_scope_digest(HarnessPath(Path('.').resolve()))
```

**Result:** `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`

**Exact match** to the expected, previously verified value. No reconciliation required.

## 4. Frozen Membership (§6)

Read live from `_FROZEN_AUTHORITY_BEARING_FILES` in `src/pcae/core/hatp_mandatory_certification.py` at the candidate blob (`git show b0840e96a7...:src/pcae/core/hatp_mandatory_certification.py`) — 23 `src/pcae/`-relative + 7 repository-root-relative = **30 members**, `assert len(...) == 30` present in the candidate source itself:

**`src/pcae/`-relative (23):** `core/hatp_mandatory_cutover.py`, `core/hatp_ag_authority.py`, `core/hatp_rollback_consumption.py`, `core/hatp_bootstrap.py`, `core/human_approval_trusted_provenance.py`, `core/repository_identity.py`, `core/rollback_approval_evidence.py`, `core/hatp_evidence_store.py`, `core/hatp_signed_evidence.py`, `core/agent.py`, `commands/agent.py`, `cli.py`, `core/permission_broker.py`, `core/permission_broker_foundation.py`, `core/hatp_providers.py`, `core/hatp_fido2_provider.py`, `core/hatp_piv_provider.py`, `core/hatp_hardware_credentials.py`, `core/hatp_mandatory_certification.py`, `core/hatp_class_b_topology_verifier.py`, `core/hatp_environment_lock_verifier.py`, `core/hatp_class_b_conformance.py`, **`core/hatp_deployment_binding_admin.py`**.

**Repository-root-relative (7):** `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`, `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`, `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, `scripts/hatp_certification_admin.py`, **`scripts/hatp_deployment_binding_admin.py`**.

Confirmed: candidate independently contains both `src/pcae/core/hatp_deployment_binding_admin.py` and `scripts/hatp_deployment_binding_admin.py` in the frozen set (`git cat-file -e b0840e96a7...:src/pcae/core/hatp_deployment_binding_admin.py` and `...:scripts/hatp_deployment_binding_admin.py`, both exit 0). No assumption made.

## 5. Candidate Tree Inventory (§7)

Freshly enumerated against the detached candidate worktree, not reused from the old 4108-path inventory:

```
git ls-tree -r HEAD --name-only | wc -l          -> 4200   (total tracked paths)
git ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    4186 100644
      14 100755
git ls-tree -r HEAD | awk '$1=="120000"{print}'  -> (none — zero symlinks)
git ls-tree -r HEAD | awk '$1=="160000"{print}'  -> (none — zero submodules)
git ls-tree -r HEAD | awk '$1!="100644" && $1!="100755"{print $1}' | sort -u -> (empty — no other modes)
```

**4200 total tracked paths: 4186 × `100644`, 14 × `100755`. Zero symlinks, zero submodules, zero other Git modes.**

The 14 `100755` paths: `.githooks/pre-commit`, `.githooks/pre-push`, 7 `.pcae/authority-evaluation/records/records/prp-*/aeval-*.json` files, 4 `.pcae/publication-execution/published/prp-*.json` files, and `scripts/check-docs-updated.sh`. This is the execution/read-back oracle for a future forward transition (§56).

## 6. Filesystem Mode Mapping (§8)

Unchanged from the mapping already authorized and re-verified across the 7B→7E→7D.9→7D.11 chain, and re-confirmed as the still-current Dell provisioning model:

- Git `100644` → filesystem `0640`
- Git `100755` → filesystem `0750`

Mode classification is derived **from Git's own on-disk executable bit** (two `find -perm -u+x` branches keyed on what `git checkout` already set from the index), never from filename pattern-matching or a blanket `chmod`. This is the identical mechanism used by the repaired Action 6 (149O.20L.7D.3/7D.5) and the 7D.9 proposition — reused verbatim here, not reinvented.

## 7. Old→Candidate Diff (§9)

```
git diff --stat 28bf137b5dc95d024e8913b678dce0501a46fd0f b0840e96a7ffb12308e95828aa5927c3e7c770c0 -- src scripts docs/contracts pyproject.toml
```

```
 docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                              |   64 +-
 docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md| 1364 +++++++++++++++++++-
 scripts/hatp_deployment_binding_admin.py                                        |  245 ++++
 src/pcae/core/hatp_deployment_binding_admin.py                                  |  953 ++++++++++++++
 src/pcae/core/hatp_mandatory_certification.py                                   |   46 +-
 5 files changed, 2598 insertions(+), 74 deletions(-)
```

**Independently reconfirmed: exactly five files, matching 7M's reported count.** No unexpected sixth authority-relevant file. Classification and blob identities (computed against the candidate, `git rev-parse b0840e96a7...:<path>` / SHA-256 of `git show b0840e96a7...:<path>`):

| # | File | Classification | Git blob SHA (candidate) | SHA-256 (candidate content) |
|---|---|---|---|---|
| 1 | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` | Contract (HBDC-001 amendment content, v1.0→v1.1) | `ccc4efba78b39633b63f25e1415b915598a49772` | `f9a82b53abe74f73de2158adc8063785ab1a96460ef4bac9a1c48e96cee3d370` |
| 2 | `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` | Contract (HMIC-001 amendment, v1.1→v1.4 across intervening amendments/repairs) | `1c6ad765533b36262319005a9f1517b0182c8b7a` | `6fe5fed66617218f74ffc252a76738bdf067f1b8bb4532430931789a091382f8` |
| 3 | `scripts/hatp_deployment_binding_admin.py` | Producer (Protected Admin DeploymentBinding ceremony script, new file) | `286db838d573ef9311a6d0df78a6842b5f4ef296` | `fe7869362431d74a46a64b8db825311914c7b4c34d46ad72ee09fd4df3dcfcdb` |
| 4 | `src/pcae/core/hatp_deployment_binding_admin.py` | Producer / HMIC membership implementation (new file, new frozen-set member) | `c7950f302ba5714764de5fa0fd86699a07cfad1c` | `582785eb3468a506aeaa3ff00cb906181a1e649ff83afcb9a05916465999f02e` |
| 5 | `src/pcae/core/hatp_mandatory_certification.py` | HMIC membership implementation (frozen-set constant + digest-derivation update) | `1b965cc53f2ad2ef6c3814d64129a4b748179f9f` | `6894f8de03cf35abd5e006b23fe6798f1234c6cafc718c7db17f05a22a7749b3` |

No sixth authority-relevant file exists in the diff. `pyproject.toml` is byte-unchanged between old and candidate (absent from the diffstat above — confirmed, not merely inferred).

## 8. Packaging Comparison (§10)

`pyproject.toml` has **zero diff** between `28bf137b...` and `b0840e96a7...` (§7). Candidate's sole runtime dependency is unchanged (`jsonschema>=4.18,<5`); the optional `hatp-hardware` extra (`fido2`, `cryptography`) is unneeded for this producer chain. Console-script entry point is unchanged: `[project.scripts]` → `pcae = "pcae.cli:main"`.

**Independently confirmed (not inherited from 7M): candidate redeployment requires no venv reinstall, no pip reinstall, no editable-install recreation.**

## 9. Editable-Install Semantics (§11)

Reconstructed from Dell's own live-verified evidence (149O.20L.7D.9 §7.4, re-confirmed 7D.11/7E, no live Dell access performed this phase):

```
sudo find /opt/pcae/runtime/venv -iname '*.pth' -exec cat {} \;
    -> /opt/pcae/runtime/src/src
sudo find /opt/pcae/runtime/venv -iname 'direct_url.json' -exec cat {} \;
    -> {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
sudo -u pcae /opt/pcae/runtime/venv/bin/pip show pcae-harness
    -> Name: pcae-harness, Version: 0.2.0, Editable project location: /opt/pcae/runtime/src
sudo cat /opt/pcae/runtime/venv/bin/pcae
    -> #!/opt/pcae/runtime/venv/bin/python3 ... from pcae.cli import main ... sys.exit(main())
```

Both the `.pth` entry (`/opt/pcae/runtime/src/src`, a filesystem path) and `direct_url.json`'s `url` field (`file:///opt/pcae/runtime/src`, likewise a path) bind the venv's import resolution to **the directory**, not to the bytes currently checked out there. The console-script entry point imports `pcae.cli` fresh at every invocation — no compiled artifact pins source bytes. **Source checkout changes at the same path are consumed through this existing path-bound editable install; neither artifact becomes stale across an in-place `checkout --detach` swap.**

## 10. Venv Decision (§12)

**RETAIN UNCHANGED.**

Per §8–§9, no `pip install -e` re-run, venv recreation, or `.pth`/`direct_url.json`/`RECORD` regeneration is required or authorized. Future execution (a later, separately elected phase) must prohibit:

- `pip install` (of any kind, including `-e`)
- venv recreation
- package reinstall
- dependency update

## 11. Wrapper Decision (§13)

**RETAIN UNCHANGED.**

Canonical wrapper: `/opt/pcae/runtime/bin/pcae-launch`. Expected digest, re-verified live at every phase from 7B through 7D.9 (most recently 149O.20L.7D.9 §7.5, no fresh Dell access this phase):

```
sudo sha256sum /opt/pcae/runtime/bin/pcae-launch
    -> b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
```

The wrapper lives at a fixed path **outside** the git repository's tracked tree — it is not `git`-cloned, so a source-tree checkout swap inside `/opt/pcae/runtime/src` is structurally incapable of mutating it. Candidate→HEAD's diff (§1) and old→candidate diff (§7) touch no wrapper-adjacent mechanism. **No wrapper rewrite is proposed or authorized.**

## 12. Dell Entering Baseline (§14)

Materialized from independently verified historical evidence (149O.20L.7A/7D.1/7D.9/7E, no fresh Dell access this phase — all facts below are re-cited, not re-measured):

| Item | Expected value |
|---|---|
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` |
| hostname | `atila-Latitude-E5470` |
| OS | Ubuntu 24.04.3 LTS, `noble`, kernel `7.0.0-28-generic`, `amd64`; Dell Latitude E5470, x86-64 |
| `pcae` principal | `uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)`, no supplementary groups, not in `sudo`; shell `/usr/sbin/nologin`; `sudo -n -l -U pcae` denied |
| Protected Root | `/etc/pcae/hatp/trust-store`, `root:pcae 0750`, not a symlink, ancestors `/etc/pcae`, `/etc` both `root:root 0755` |
| Retained Actions 1–5 | 1: apt packages (`python3-venv`, `python3-pip`, `git 2.43.0`, `python3 3.12.3`, `acl 2.3.2`) present; 2: `pcae` group/user created; 3: Protected Root (above); 4: runtime/state tree `/opt/pcae/**`, `/var/lib/pcae`, `/var/log/pcae` all `root:pcae 0750`; 5: `/home/pcae` = `pcae:pcae 0750`, stock skeleton |
| Deploy credential | Dedicated Ed25519 keypair `/root/.ssh/pcae_harness_deploy_ed25519`, `root:root 0600` (private) / `0644` (public), unreadable by `pcae`/`codex`; registered as a GitHub repository deploy key on `atimad/pcae-harness`, `read_only: true`; fingerprint `SHA256:pSD+FImEdVWIut+199XjrkqMeeu6eCOZd1FldrMiTrk` |
| Current source SHA | `28bf137b5dc95d024e8913b678dce0501a46fd0f` (live-confirmed 7D.11/7E, unchanged since) |
| Tree state | detached (`symbolic-ref -q HEAD` exit 1), clean (`status --short --untracked-files=all` empty), `origin` = `git@github.com:atimad/pcae-harness.git`, `core.filemode=true` |
| Filesystem mode inventory | 4108 tracked paths: 4097 × `100644` (fs `0640`), 11 × `100755` (fs `0750`); zero mismatches against `os.lstat` cross-check |
| Venv | `.pth` → `/opt/pcae/runtime/src/src`; `direct_url.json` → `file:///opt/pcae/runtime/src`, `editable: true`; `pcae_harness-0.2.0.dist-info` |
| Wrapper | digest `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`, `root:pcae 0750` |
| RepositoryIdentity | absent (`find /opt/pcae /etc/pcae -iname '*repositoryidentity*'` → zero matches, and no `.pcae/repository-identity.json` in any checkout consumed by Dell) |
| DeploymentBinding | absent (`find /opt/pcae /etc/pcae -iname '*deploymentbinding*'` → zero matches) |
| Runtime state | Observed / observe / unavailable (unchanged HATP posture) |

**These are stated as required preconditions for a future execution phase, not assumptions this phase relies on for its own (non-mutating) work.**

## 13. Fresh Execution Preflight (§15)

A future execution phase **must STOP before any mutation** if any entering-baseline item in §12 differs from live re-measurement at that time. No "repair while executing." Explicit STOP triggers: wrong machine-id; wrong old SHA; dirty tree; unexpected DeploymentBinding; unexpected RepositoryIdentity; wrapper digest mismatch; venv state mismatch; source credential mismatch; unexpected trust-store contents.

## 14. Source Credential (§16)

Reconstructed, not rotated: dedicated, root-owned Ed25519 SSH key at `/root/.ssh/pcae_harness_deploy_ed25519` (mode `0600`, owner `root:root`); GitHub repository-scoped, read-only deploy key on `atimad/pcae-harness` (`read_only: true`, cannot access any other repository by GitHub's own mechanism); deterministic `/root/.ssh/config` `Host github.com` stanza (`IdentityFile`, `IdentitiesOnly yes`); no TOFU (`known_hosts` pre-populated by prior provisioning). **This proposition uses this credential only for the exact candidate fetch (§16 below) in a future execution phase. No credential rotation is proposed.** No private key content, token, or secret material appears anywhere in this document — only credential metadata (path, ownership, mode, fingerprint of the *public* key).

## 15. Exact Fetch Strategy (§17)

```
sudo git -C /opt/pcae/runtime/src fetch origin b0840e96a7ffb12308e95828aa5927c3e7c770c0
```

Exact commit object requested — no branch name, no moving ref (`main`, `origin/main`) used as the fetch argument. No `git pull` (which would merge/fast-forward against a moving branch tip) is authorized anywhere in this document.

## 16. Candidate Local-Object Verification (§18)

```
sudo git -C /opt/pcae/runtime/src cat-file -t b0840e96a7ffb12308e95828aa5927c3e7c770c0
    -> must equal exactly: commit
```

Full, unabbreviated 40-hex-character SHA used throughout — no abbreviated SHA is used for any authority check in this document.

## 17. Exact Checkout (§19)

```
sudo git -C /opt/pcae/runtime/src checkout --detach b0840e96a7ffb12308e95828aa5927c3e7c770c0
```

Detached checkout only. No branch switch, no `merge`, no `rebase`, no `pull`.

## 18. Ownership Normalization (§20)

```
sudo chown -R root:pcae /opt/pcae/runtime/src
```

Scoped exactly to `/opt/pcae/runtime/src` — no broader ownership change outside that path. Preserves the existing Dell source trust model (root-owned tree, `pcae`-group-readable, `pcae` itself has no write access).

## 19. Mode Normalization (§21)

```
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

Executable classification is derived from each file's own on-disk executable bit as `git checkout` already set it from the candidate's index (§6) — not from filename pattern-matching, and not a blanket `chmod 0640`. Byte-identical mechanism to the repaired Action 6 (149O.20L.7D.3 §11 / 7D.5 §10) and the 7D.9 proposition — reused verbatim, not reinvented.

## 20. Full Source Read-Back (§22)

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD
    -> must equal b0840e96a7ffb12308e95828aa5927c3e7c770c0 EXACTLY
sudo git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    -> non-zero (detached)
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all
    -> must be empty (no staged changes, no untracked files)
sudo git -C /opt/pcae/runtime/src remote get-url origin
    -> must equal git@github.com:atimad/pcae-harness.git EXACTLY
sudo git -C /opt/pcae/runtime/src ls-files | wc -l
    -> must equal 4200 EXACTLY
sudo git -C /opt/pcae/runtime/src ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    -> must equal:  4186 100644 /  14 100755
[independent Python os.lstat cross-check against every one of the 4200 tracked paths,
 identical script pattern to prior phases' read-back, run against the candidate's own tree]
    -> must equal: total 4200, ok640 4186, ok750 14, other 0, mismatches 0
sudo git -C /opt/pcae/runtime/src diff b0840e96a7ffb12308e95828aa5927c3e7c770c0 -- . | wc -l
    -> must equal 0 (zero content bytes drift from the pinned candidate commit)
```

Any read-back line not matching exactly → **STOP**, execute the rollback (§22/§39), do not invent a substitute command, disclose to the operator.

## 21. `core.fileMode` (§23)

```
sudo git -C /opt/pcae/runtime/src config core.fileMode
    -> must equal true
```

Read-back must confirm `core.fileMode=true` (mode changes tracked, not masked). If `false`, filesystem-mode drift could exist invisibly to `git status` — STOP and diagnose rather than trust `git status`'s silence.

## 22. Authority-Bearing Byte Identity (§24)

Future execution must compare deployed bytes for **all 30** HMIC authority-bearing files (§4) against candidate Git blobs — not merely the two new producer files:

```
for f in <all 30 frozen-set canonical paths>; do
  sudo git -C /opt/pcae/runtime/src diff b0840e96a7ffb12308e95828aa5927c3e7c770c0 -- "$f" | wc -l
done
-> every line must equal 0 (zero mismatches across all 30 files)
```

## 23. HMIC Digest on Dell (§25)

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i \
  HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
from pcae.core.paths import HarnessPath
from pathlib import Path
print(derive_implementation_scope_digest(HarnessPath(Path.cwd())))
'"
    -> must equal 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8 EXACTLY (§3)
```

This is **source identity only** — it is not, and must not be characterized as, HMIC certification.

## 24. Contract Versions on Dell (§26)

Future execution must derive current contract versions from the deployed candidate tree (grep the deployed files, not re-read from this document): HBDC-001 → `1.1`, HMIC-001 → `1.4`, HMRC-001 → `1.1` (§2). No stale old-source contract versions (any version read that differs from these is a STOP condition).

## 25. Producer Availability (§27)

```
sudo -u pcae env -i HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
import pcae.core.hatp_deployment_binding_admin as m
print(m.__file__)
'
    -> must resolve under /opt/pcae/runtime/src/src/pcae/core/hatp_deployment_binding_admin.py
sudo git -C /opt/pcae/runtime/src diff b0840e96a7ffb12308e95828aa5927c3e7c770c0 -- src/pcae/core/hatp_deployment_binding_admin.py | wc -l
    -> must equal 0
```

Import only — **no invocation of any function within the module.**

## 26. Admin Script Availability (§28)

```
test -f /opt/pcae/runtime/src/scripts/hatp_deployment_binding_admin.py ; echo $?
    -> 0
sudo git -C /opt/pcae/runtime/src diff b0840e96a7ffb12308e95828aa5927c3e7c770c0 -- scripts/hatp_deployment_binding_admin.py | wc -l
    -> must equal 0
```

Existence and byte-match only — **no `create`/`rotate`/`revoke` invocation of the admin script.**

## 27. Agent Reachability After Redeployment (§29)

Future read-back must independently re-verify the producer remains non-agent-reachable under the candidate — the same PATH-resolution diagnostic already established (149O.20L.7D.9 §7.7 / 7D.11 §29):

```
sudo -u pcae env -i HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin which pcae
    -> /opt/pcae/runtime/venv/bin/pcae, exit 0 (the one admin-controlled, agent-unwritable launcher)
```

No separate agent-reachable entry point for the DeploymentBinding producer/admin script is expected or authorized — this preserves the independently verified security posture established across 7D.6/7D.9/7D.11.

## 28. Runtime Import Provenance (§30)

Future execution must use the deployed venv (§9's `/opt/pcae/runtime/venv/bin/python3`) to inspect module paths for the two changed core modules (§25 above and an equivalent check for `hatp_mandatory_certification`). This demonstrates **import-path provenance only** — it does not, and cannot, cryptographically prove which specific bytes executed for any prior invocation. **HMIC-REQ-063's residual limitation is carried forward unchanged**, not silently closed by this evidence.

## 29. Venv Postcondition (§31)

Future read-back must re-read `.pth`, `direct_url.json`, distribution identity (`pcae_harness-0.2.0.dist-info`), interpreter path, and relevant permissions — expected **byte/state unchanged** from §9 (the checkout swap changes only the bytes at the already-referenced path; it does not touch venv artifacts at all per §10).

## 30. Wrapper Postcondition (§32)

```
sudo sha256sum /opt/pcae/runtime/bin/pcae-launch
    -> must equal b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32 EXACTLY (unchanged, §11)
```

## 31. No RepositoryIdentity Creation (§33)

This proposition explicitly **prohibits** creation of `.pcae/repository-identity.json` on Dell and prohibits running `pcae init` there. RepositoryIdentity remains absent through the entirety of this transition.

## 32. No DeploymentBinding Creation (§34)

This proposition explicitly **prohibits**: DeploymentBinding create; rotate; revoke; any preview operation that writes; and any trust-store mutation. **Producer presence (§25) does not authorize use.**

## 33. No HBDC Operational Reclassification (§35–37)

**Architecture choice: include a read-only HBDC diagnostic (Action 9) after candidate deployment, informationally only.** This is the same Action-9 command already established and re-verified across 149O.20L.7D.9/7D.11 (recovered verbatim, no substitution):

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

**Expected result: `NON_COMPLIANT`, with exactly one failing requirement — `HBDC-REQ-042` (`no_repository_identity_present`) — every other requirement `True`.** This is derived directly from the candidate source and the absence of RepositoryIdentity (§31), not from any first-use compliance target. **If the diagnostic returns any other failure set, or an unexpected `COMPLIANT`, future execution STOPs for diagnosis** — it does not proceed to declare success and does not attempt any repair (e.g., creating RepositoryIdentity) to force a passing result. The purpose of Transition 1 is source currentness, not first-use compliance; **full HBDC compliance is explicitly deferred to Transition 2** (RepositoryIdentity + DeploymentBinding first use), consistent with 149O.20L.7M's two-transition sequencing (§0). Diagnostic-only — no repair authorized regardless of outcome.

## 34. Exact Rollback Target (§38)

**`28bf137b5dc95d024e8913b678dce0501a46fd0f`** — the currently deployed Dell SHA (§12), independently re-confirmed live by 149O.20L.7D.11/7E, unchanged since.

**Local-object prerequisite:**

```
git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f
    -> commit  (confirmed §1, this Mac checkout)
```

On Dell itself, `28bf137b...` is guaranteed present because it is the checkout's **current `HEAD`** at the moment the forward transition begins — Git never garbage-collects a commit that is the current `HEAD` of a checkout, and the forward step (§15) only *adds* the candidate's objects via `fetch`; it does not remove or repack away the old SHA's objects. This is a structural guarantee (Git's reachability rule for `HEAD`), not an assumption dependent on any prior `fetch` having been run recently.

## 35. Network-Independent Rollback (§39)

```
sudo git -C /opt/pcae/runtime/src checkout --detach 28bf137b5dc95d024e8913b678dce0501a46fd0f
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

**Rollback verification:**

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD -> 28bf137b5dc95d024e8913b678dce0501a46fd0f EXACT
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all -> empty
sudo git -C /opt/pcae/runtime/src ls-files | wc -l -> 4108
sudo git -C /opt/pcae/runtime/src ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    -> 4097 100644
    ->   11 100755
```

Requires **zero network access, zero GitHub reachability, and zero use of the deploy credential** — a pure local `checkout --detach` per §34's reachability guarantee.

## 36. Rollback Trigger Matrix (§40)

| Trigger | Rollback? |
|---|---|
| Candidate checkout failure (§17) | Yes |
| Read-back content mismatch (§20, `diff ... | wc -l` ≠ 0) | Yes |
| Read-back mode mismatch (§20/§21) | Yes |
| Authority-bearing byte mismatch, any of the 30 files (§22) | Yes |
| HMIC digest mismatch (§23) | Yes |
| Venv no longer consumes source correctly (§29 postcondition fails) | Yes |
| Wrapper digest unexpectedly changed (§30) | Yes |
| Candidate producer/module import failure (§25/§27) | Yes |
| HBDC Action-9 diagnostic returns a failure set other than exactly `{HBDC-REQ-042}`, or an unexpected `COMPLIANT` (§33) | Yes — STOP and diagnose (rollback if diagnosis cannot resolve without deviating from this proposition) |
| HBDC Action-9 diagnostic returns exactly `NON_COMPLIANT {HBDC-REQ-042}` as expected (§33) | **No** — this is the expected, source-only residual; not a rollback trigger |

## 37. Source-Only Rollback Boundary (§41)

Because this transition creates no RepositoryIdentity and no DeploymentBinding, rollback is cleanly isolated to source deployment — no first-use artifact needs unwinding, no trust-store entry needs revocation, no HMIC certification record needs invalidation. This narrow blast radius is one of the reasons the two-transition (Model A/C) sequence was selected at 149O.20L.7M over a combined single-transition model.

## 38. Post-Success Status (§42)

If the candidate transition succeeds (per the future execution phase's own read-back, §20–§30):

| Item | Status |
|---|---|
| Dell source | CURRENT VERIFIED CANDIDATE DEPLOYED (`b0840e96a7ffb12308e95828aa5927c3e7c770c0`) |
| HMIC source identity | Candidate implementation/source identity deployed (§23) |
| HMIC certification | Still absent |
| RepositoryIdentity | Absent |
| DeploymentBinding | Absent |
| HBDC | Still not fully compliant until first-use transition (expected `NON_COMPLIANT {HBDC-REQ-042}`, §33) |
| Boundary C | Not authorized |
| Boundary A | Not authorized |
| HATP | Not ready |
| Runtime | Observed / observe / unavailable |

## 39. Governing Authority Requirement (§43)

This exact source transition requires a **new** CHGR. All four historical CHGRs are inapplicable (§40).

## 40. Historical CHGR Inventory (§44)

| CHGR | Origin phase | Why inapplicable to this transition |
|---|---|---|
| `chgr-0e37ed1340b14311826722c4dbf3e856` | 149O.20L.7D.9→7D.10→7D.11 (published via `CDS-105d30f5-...`, 371-char subject) | Its own condition 7 states verbatim: *"This CHGR authorizes exactly the source-identity transition to `28bf137b5dc95d024e8913b678dce0501a46fd0f` and the Action-9 PATH amendment described in §§15-16 — no other source SHA, branch, or ref is authorized."* The candidate here (`b0840e96a7...`) is a different SHA — outside its subject by its own explicit text. Its condition 6 also excludes DeploymentBinding creation without a fresh election, and RepositoryIdentity is outside its subject entirely. |
| `chgr-96a0ce12756e4cc892492a87af1db832` | 149O.20L.7D provisioning chain | Independently confirmed by 149O.20L.7E §4 and re-confirmed by 7M §17 (byte-unchanged since) not to name the candidate SHA in either `decision_subject` or `rationale`; scoped to the original host-provisioning execution (Actions 1–8), not to any source-SHA transition. |
| `chgr-541cb08c313b4f8884970172d37c5a1d` | 149O.20L.7D.3 (continuation) | Same confirmation as above (7E §4 / 7M §17) — a provisioning-continuation record (repaired Action 6 baseline), not naming the candidate SHA; scoped to the original provisioning continuation, not a subsequent source-SHA transition. |
| `chgr-d4343fa51b9743f3abaeb87a881a78b1` | 149O.20L.7B.2 | An unrelated Boundary-P target-environment-selection record from 2026-08-14 (one day before the 7D chain), plan/commit-bound to Git commit `2e97651ef9366e6427b26ea061deac827b6485e9` and an earlier HMIC-001 v1.3/HBDC-001 v1.0 version pair. Its `conditions` text explicitly excludes HMIC certification/binding/revocation (Boundary C). Cannot authorize the candidate transition, RepositoryIdentity creation, or DeploymentBinding creation. **Note:** two prior phases (149O.20L.7A §-cite, 7B §-cite) describe this record's `decision_subject` as naming `Atilas-MacBook-Pro.local` specifically, while 149O.20L.7M's own prose describes the same record's subject as "Boundary-P provisioning authorization for Class-B target Option B ... per 7B.1 §19 proposition." Both descriptions independently agree the record is inapplicable to the candidate Dell source transition; the discrepancy in exactly how each phase characterized the record's `decision_subject` text is a pre-existing, disclosed prose inconsistency in the historical record chain, not resolved by this phase (out of this phase's allowed-file scope; flagged here for a future phase to reconcile if it becomes load-bearing). |

**No fallback exists.** Four CHGRs total; none authorizes the candidate transition, RepositoryIdentity creation, or DeploymentBinding creation.

## 41. D3-3 Status — No Supersession Claimed (§45)

**Carried, unchanged: D3-3 CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION HARDENING GAP RETAINED** (substance established 149O.20L.7D.3 §10; status label first attached 149O.20L.7E §4/§50; carried unchanged by 7D.11 §4 and 7M §53). No `predecessor_record_id`/`successor_record_id` linkage exists between any of the four historical CHGRs and a future fresh CHGR for this transition — `pcae governance-record publish` takes no supersession argument, and no lifecycle-transition machinery exists this increment. **Historical CHGRs remain published records.** The future fresh CHGR will be authoritative by exact applicability of its own `decision_subject`/`rationale`/`conditions` text (§40's method) — not by any invented or claimed supersession relationship to the four historical records.

## 42. Proposition Decision Subject (§46)

Draft text for the future election's `decision_subject` (final wording is that phase's own responsibility — this is proposition-preparation material, not a submitted or published value):

> "Dell PCAE runtime source-only redeployment from 28bf137b5dc95d024e8913b678dce0501a46fd0f to candidate b0840e96a7ffb12308e95828aa5927c3e7c770c0; venv and wrapper retained unchanged; no RepositoryIdentity or DeploymentBinding created."

Length: 218 characters — within the CHGR-001 schema's 500-character `decision_subject` limit (the same limit that caused the prior `CDS-a2e437a8-...` session's 574-character subject to fail to publish, 149O.20L.7D.10 §15) by a wide margin, avoiding a repeat of that failure mode.

## 43. Proposition Rationale (§47)

- **Why current Dell source is stale:** Dell is deployed at `28bf137b5dc95d024e8913b678dce0501a46fd0f`; `b0840e96a7ffb12308e95828aa5927c3e7c770c0` is a later, independently verified ancestor of `origin/main` (§1) containing HMIC-001 v1.4's completed DeploymentBinding producer/admin surface (§7) that `28bf137b...` lacks.
- **Why the candidate is independently verified:** §1 (currentness/ancestry), §2 (contract versions read live), §3 (HMIC digest recomputed and matched), §4 (30-member frozen set reconstructed and matched), §5 (tree inventory freshly enumerated) — none of these facts are inherited from 149O.20L.7M's own prose without independent recomputation.
- **Exact delta:** §7 — exactly five files, all classified, all blob-hashed.
- **No venv reinstall:** §8–§10.
- **No wrapper change:** §11, §30.
- **Rollback:** §34–§37 — network-independent, source-only, structurally guaranteed.
- **No first-use artifacts:** §31–§32.
- **No Boundary C:** §38 (post-success status explicitly leaves Boundary C `NOT AUTHORIZED`).

## 44. Proposition Conditions (§48)

1. Target machine identity: `hac-dell` / machine-id `54ff22ce400b475aa0d55cb68f4a3334` / hostname `atila-Latitude-E5470` (§12) — future execution STOPs on any mismatch (§13).
2. Entering old SHA: `28bf137b5dc95d024e8913b678dce0501a46fd0f`, detached, clean (§12).
3. Candidate exact SHA: `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, no branch/moving ref (§15, §17).
4. Venv retained, unchanged (§10).
5. Wrapper retained, unchanged (§11).
6. No RepositoryIdentity creation authorized (§31).
7. No DeploymentBinding creation/rotation/revocation authorized (§32).
8. No HMIC certification authorized.
9. No Boundary C / Boundary A / HATP activation authorized.
10. Rollback conditions: per the trigger matrix (§36), executed via §35's network-independent commands.
11. Source-readback requirements: per §20–§30, all must pass exactly or STOP.
12. First-use transition (RepositoryIdentity + DeploymentBinding) remains separately gated — a distinct future phase, its own proposition, its own independent verification, its own election, its own CHGR (§39, 149O.20L.7M §48 steps 6–8).

## 45. Proposition Exclusions (§49)

Explicitly excluded from this transition's authority, in any current or future phase deriving from it without a fresh, separate election: RepositoryIdentity creation; DeploymentBinding create/rotate/revoke; first-use election; Boundary C; HMIC certification; Boundary A; Cutover Record; `HATP_MANDATORY` activation; Permission Broker / POL-005 / COMP-002 changes; repository onboarding; centralized multi-repo governance; unrelated Dell principals/resources; `hac-windows`.

## 46. Preview Content (§50)

Materialized preview text for the future human election (no ambiguous phrasing such as "latest source" anywhere):

> **Proposed action:** Redeploy the Dell (`hac-dell`) PCAE runtime source from commit `28bf137b5dc95d024e8913b678dce0501a46fd0f` (currently deployed) to commit `b0840e96a7ffb12308e95828aa5927c3e7c770c0` (independently verified candidate, HMIC-001 v1.4 implementation digest `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`).
>
> **Mutation paths:** `/opt/pcae/runtime/src` only (in-place `git fetch` + `checkout --detach`, ownership `chown -R root:pcae`, mode remap per Git's own `100644`→`0640`/`100755`→`0750` mapping). No other filesystem path is touched.
>
> **Candidate tree:** 4200 tracked paths (4186 × `100644`, 14 × `100755`); zero symlinks, zero submodules.
>
> **Venv:** `/opt/pcae/runtime/venv` — unchanged, retained (`.pth`/`direct_url.json`/dist-info untouched).
>
> **Wrapper:** `/opt/pcae/runtime/bin/pcae-launch` — unchanged, retained (digest `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`, outside the git-managed tree).
>
> **Rollback target:** `28bf137b5dc95d024e8913b678dce0501a46fd0f` — network-independent, local `checkout --detach` only.
>
> **Expected post-state:** Dell source current; HMIC certification still absent; RepositoryIdentity absent; DeploymentBinding absent; HBDC diagnostic (optional, read-only) expected `NON_COMPLIANT {HBDC-REQ-042}`; Boundary C/A not authorized.
>
> **Excluded from this authorization:** RepositoryIdentity creation, DeploymentBinding create/rotate/revoke, HMIC certification, Boundary C, Boundary A, Cutover Record, HATP activation, Permission Broker/POL-005/COMP-002 changes, repository onboarding.

## 47. Election Not Yet Initiated (§51)

No `pcae decision-session`/`pcae governance-record`/`pcae authority` command that creates or advances authority state was invoked this phase. §42/§46's text is proposition material embedded in this document only — not submitted to, nor generated by, any election-machinery tool call. No non-authoritative "draft" object was created via tooling either; the text exists solely as prose in this markdown file.

## 48. No CHGR Publication (§52)

No CHGR was published this phase. `.pcae/publication-execution/published/` was not written to. Confirmed:

```
git status --short .pcae/publication-execution/ -> (empty — no changes)
```

## 49. Future Election Phase (§53)

Per 149O.20L.7M §48's 11-step decomposition (§50 below), the next phase is:

**149O.20L.7N.1 — Dell Current-Source Redeployment Proposition Independent Authority Verification** (mirrors the 7D.9→7D.10 pattern: independently re-verify this proposition's factual claims — currentness, digest, diff, tree inventory, all command literalizations — before it is presented for election).

This phase (7N) does **not** execute 7N.1. It stops here.

## 50. Independent Authority Verification Required After Election (§54)

The architecture requires a separate phase after CHGR publication and before Dell mutation. Per 149O.20L.7M §48, the full future chain is: **7N (this phase, proposition) → 7N.1 (independent proposition verification) → 7O/7P (election + CHGR publication, publication only, no mutation) → 7P/7Q (execution) → 7Q/7R (independent real-host verification)** — before Transition 2 (first-use identity/binding, steps 6–11 of the same decomposition) even begins. Election and execution are never collapsed into the same phase anywhere in this chain.

## 51. Exact Future Phase Decomposition (§55)

Reproducing 149O.20L.7M §48's 11-step decomposition verbatim, with this phase's position marked:

1. **149O.20L.7N — Dell Current-Source Redeployment Proposition + Authority Preparation.** ← **this phase.**
2. 149O.20L.7N.1 (or 7O) — Redeployment Proposition Independent Authority Verification. *Remains open.*
3. 149O.20L.7O (or 7P) — Redeployment Election + CHGR Publication. *Remains open.*
4. 149O.20L.7P (or 7Q) — Redeployment Execution. *Remains open.*
5. 149O.20L.7Q (or 7R) — Redeployment Independent Real-Host Verification. *Remains open.*
6. 149O.20L.7R (or 7S) — First-Use Identity/Binding Proposition Preparation. *Remains open.*
7. 149O.20L.7S (or 7T) — First-Use Proposition Independent Authority Verification. *Remains open.*
8. 149O.20L.7T (or 7U) — First-Use Election + CHGR Publication. *Remains open.*
9. 149O.20L.7U (or 7V) — First-Use Execution + HBDC Re-Adjudication. *Remains open.*
10. 149O.20L.7V (or 7W) — First-Use Independent Real-Host Verification. *Remains open.*
11. 149O.20L.7W (or 7X) — Boundary-C Preparation. *Remains open* (not Boundary-C authorization itself).

Steps 2–11 all remain open after this phase. No step is skipped.

## 52. Candidate Mode Inventory in Proposition (§56)

Recorded in full at §5 — no placeholders. This is the execution read-back oracle for §20.

## 53. Candidate Changed-File Inventory (§57)

Recorded in full at §7 — the exact five-file authority-relevant delta, no summary-only wording.

## 54. Changed-File Byte Identities (§58)

Recorded in full at §7's table — Git blob SHA and SHA-256 for each of the five changed authority-relevant files, computed against the candidate.

## 55. Production Command Literalization (§59)

Every mutation-relevant command is literalized exactly, no "equivalent commands allowed" language, at: §15 (fetch), §16 (candidate object verification), §17 (checkout), §18 (ownership normalization), §19 (mode normalization), §20–§21 (read-back), §23 (HMIC digest computation), §25/§27/§28 (runtime import/producer/admin-script verification), §33 (optional HBDC diagnostic), §35 (rollback), §13 (preflight, reusing §12's baseline as the exact expected values).

## 56. Shell Safety (§60–§61)

All commands above use explicit absolute paths (`/opt/pcae/runtime/src`, `/opt/pcae/runtime/venv/bin/python3`, `/opt/pcae/runtime/bin/pcae-launch`); `sudo -u pcae env -i ... PATH=...` explicitly resets environment/PATH rather than relying on ambient shell state or aliases; `sudo git -C <path>` fixes the working directory explicitly per invocation rather than a persistent `cd`; no glob is used in any mutation command; no caller-provided branch or ref is ever accepted — every SHA is embedded literally (§61: no runtime `git rev-parse origin/main` for target selection anywhere in the mutation path).

## 57. Read-Only Preflight vs. Mutation Commands (§62)

- **Read-only preflight:** §13 (baseline re-check against §12), §16 (candidate object type check).
- **Forward mutation:** §15 (fetch — network, no local state mutation until checkout), §17 (checkout — first working-tree mutation), §18 (ownership), §19 (mode).
- **Read-back:** §20–§30 (all read-only against the now-mutated tree).
- **Rollback:** §35 (mutation back to old SHA).

## 58. First Mutation Boundary (§63)

The first mutating command is §17's `git checkout --detach b0840e96a7ffb12308e95828aa5927c3e7c770c0` (the `fetch` in §15 only adds objects to the local store — it does not alter the working tree or `HEAD`). Everything before it (§13 preflight, §16 candidate-object check, and the fetch itself) is safe to execute during independent authority verification (7N.1) if that phase's own scope permits read-only/fetch-only Dell access — that determination belongs to 7N.1, not this phase.

## 59. Stop Conditions (§64)

Enumerated in full: §1 (authority-bearing drift beyond candidate), §13 (any entering-baseline mismatch), §16 (candidate object not type `commit`), §20 (any read-back line mismatch), §21 (`core.fileMode` not `true`), §22 (any of the 30 authority-bearing files byte-mismatched), §23 (HMIC digest mismatch), §25/§27/§28 (producer/admin-script import or byte-match failure), §33 (HBDC diagnostic result other than exactly `NON_COMPLIANT {HBDC-REQ-042}`), §29/§30 (venv or wrapper postcondition mismatch). **No automatic repair is authorized for any of these — STOP and disclose to the operator in every case.**

## 60. Secrets (§65)

No private key contents, tokens, or sensitive credential material appear anywhere in this document — §14 references credential metadata (path, ownership, mode, public-key fingerprint) only, all already independently disclosed in prior published phase docs.

## 61. Dell Access (§66)

**No Dell access was performed this phase.** Every fact in this document is either (a) independently recomputed against the local git object store / candidate worktree (§1–§7, §42's length count), or (b) cited from 149O.20L.7A/7D.1/7D.9/7D.11/7E's own independently verified, already-published, same-week live Dell evidence — not re-measured. This follows 149O.20L.7M's own precedent (§54: "No SSH session to any Dell host was opened this phase").

## 62. Candidate Currentness at Phase Close (§67)

Re-checked immediately before finalizing this document:

```
git rev-parse HEAD          -> b83d6623c0dea24bad699f52aa6861804a0f29dd  (unchanged since §1)
git rev-parse origin/main   -> b83d6623c0dea24bad699f52aa6861804a0f29dd  (unchanged since §1)
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0 HEAD -- src/pcae scripts docs/contracts schemas pyproject.toml
    -> (empty, unchanged since §1)
```

`HEAD` has not moved during this phase's own drafting — no distinction between "phase-proposition candidate source commit" and "documentation/finalization commits" is needed this time, because no intervening commit was created before this check. (This phase's own finalization commits, created after this check, are themselves an instance of the same category of non-authority-bearing drift analyzed in §1 — they will not touch `src/pcae/**`/`scripts/**`/`docs/contracts/**`/`schemas/**`/`pyproject.toml` either, per this phase's own allowed-file scope, §67 note below.)

## 63. Proposition Commit Binding (§68)

Following the existing CHGR architecture (`chgr-0e37ed...`'s own pattern, §40): the future CHGR's `decision_subject`/`conditions` should bind to the **source candidate SHA only** (`b0840e96a7ffb12308e95828aa5927c3e7c770c0`) as the authoritative transition target — not to this document's own commit SHA, since the document is prose/evidence, not the authority artifact itself (consistent with `chgr-0e37ed...` naming `28bf137b...` directly in its own `decision_subject`/conditions rather than naming a phase-doc commit).

## 64. Human-Readable vs. Machine-Bound Representation (§69)

The exact SHA/commands/conditions in this document (§7, §12, §15–§21, §34–§36, §44–§45) are captured here as the canonical proposition prose. Per §63, when the future election tool captures the machine-bound representation, it must bind the SHA values (`b0840e96a7ffb12308e95828aa5927c3e7c770c0` old-target, `28bf137b5dc95d024e8913b678dce0501a46fd0f` rollback) directly into the election record's own `decision_subject`/`conditions` fields — not solely rely on this prose document.

## 65. No First-Use Preview Yet (§70)

No DeploymentBinding preview was attempted. RepositoryIdentity remains absent and (per its own random-identifier generation design) undetermined. That belongs to Transition 2, a later phase.

## 66. Final Verdict (§71)

**REDEPLOYMENT PROPOSITION READY — ELECTION NOT INITIATED.**

Exact source transition is fully materialized (§1–§46) and ready for a future human decision in a dedicated election phase (§49–§51). No candidate staleness (§1), no incomplete command literalization (§55–§59), no authority-model blocker identified.

## 67. Expected Clean State (§72)

| Item | Value |
|---|---|
| Candidate | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` — still exact proposed source target |
| Redeployment proposition | READY |
| Human election | NOT INITIATED |
| CHGR | NOT CREATED |
| Dell source | still old: `28bf137b5dc95d024e8913b678dce0501a46fd0f` |
| RepositoryIdentity | absent |
| DeploymentBinding | absent |
| HMIC certification | absent |
| Boundary C / Boundary A | not authorized |
| Runtime | Observed / observe / unavailable |

## 68. Recommended Next Phase (§73)

**149O.20L.7N.1 — Dell Current-Source Redeployment Proposition Independent Authority Verification.**

Should independently re-verify: candidate currentness (fresh `origin/main` re-check), the recomputed HMIC digest, the 30-member frozen-set reconstruction, the five-file diff and its blob hashes, the tree inventory, and every literalized command in §15–§21/§35 — before any human election phase (7O/7P per §51) presents APPROVE/DECLINE/AMEND. That subsequent election phase must: present this exact proposition; collect APPROVE/DECLINE/AMEND; require separate confirmation; publish a CHGR if approved; perform no Dell mutation. Independent CHGR verification must occur before execution.

## Governance

Normal governed PCAE lifecycle used throughout (`pcae task`, `pcae commit implementation`, `pcae phase complete`, `pcae push`). No raw `git commit`/`git push`. No `--no-verify`. No force push. No hook/finalization bypass.

## Proof of No Prohibited Action

- **No election initiated:** §47 — no election-machinery tool call made.
- **No CHGR published:** §48 — `.pcae/publication-execution/` untouched.
- **No Dell mutation:** §61 — no SSH session to any Dell host opened this phase.
- **No RepositoryIdentity created:** confirmed via `git status --short .pcae/` (no `repository-identity.json` in this checkout, consistent with 149O.20L.7M §13's identical confirmation) and §61 (no Dell access to create one there either).
- **No DeploymentBinding created:** §61 (no Dell access) and §32 (explicit prohibition).
- **No certification performed:** §23 computes source identity only, explicitly not characterized as certification (§23's own text).
- **No activation:** Boundary C/A/HATP all remain `NOT AUTHORIZED` per §38/§67.

## Proposition Artifact Location

This document, `docs/PHASE_149O_20L_7N_DELL_CURRENT_SOURCE_REDEPLOYMENT_PROPOSITION_AUTHORITY_PREPARATION.md`, is the canonical proposition artifact for this phase. All exact SHA/command/condition text a future election tool consumes should be read from the sections cited above, not paraphrased.
