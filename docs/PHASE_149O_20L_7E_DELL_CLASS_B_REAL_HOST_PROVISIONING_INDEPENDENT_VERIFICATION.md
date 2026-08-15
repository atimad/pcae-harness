# Phase 149O.20L.7E — Dell Class-B Real Host Provisioning Independent Verification

## 0. Phase Identity and Type

Independent verification only — no repair, redeployment, reconfiguration,
certification, activation, or authority-broadening. This phase
independently establishes, from primary repository artifacts, canonical
authority records, and fresh read-only inspection of the live `hac-dell`
host, that the Boundary-P provisioning result reported by Phase
149O.20L.7D.11 is real, exact, and fully explained by applicable
authority. It does not use 7D.11's own report as an oracle for any
claim below; every claim was independently re-derived this phase.

## 1. Phase-Entry State

- True phase-entry commit: `6486e131` (`Phase 149O.20L.7D.11: sync
  push-state trust fields for finalization gate`), `origin/main` tip,
  zero commits ahead/behind (`git rev-list --count origin/main..HEAD` =
  0).
- Active task at entry: idle placeholder
  `20260815-2049-idle-awaiting-next-governed-phase-post-149o-20l-7d-11`.
- `pcae health`/`pcae check`/`pcae status coherence`: healthy / passed /
  coherent. `pcae doctor task-memory`: pre-existing warnings (22 active
  task files; historical `tasks/done/` entries missing from
  `tasks/DONE.md`), unrelated to this phase, not remediated here
  (outside allowed-file scope, matching 7D.11's own disposition).
  `pcae push check`: clean, nothing to push. `pcae runtime inspect`:
  `Observed` / `observe` / `unavailable`. `pcae notify status`:
  Telegram configured/enabled. `pcae phase-report show --latest`: shows
  the 7D.11 canonical report in full. `pcae phase-report reconcile
  --phase-id 149O.20L.7D.11`: `reconciled`, `mutation: none (inspection
  only)`.

## 2. Reconstruction of 7D.11 From Primary Evidence (Not the Summary)

Reconstructed independently from the governing CHGR (§3) and the 7D.9
proposition document (`docs/PHASE_149O_20L_7D_9_...md`), not from
7D.11's own prose:

- Governing CHGR: `chgr-0e37ed1340b14311826722c4dbf3e856`.
- Entering Dell baseline: source detached at
  `7a3fa971304521cdcb44251e07ef1966baec686a`, clean, 4030 tracked paths
  (4024×`100644`/6×`100755`).
- Candidate SHA: `28bf137b5dc95d024e8913b678dce0501a46fd0f`.
- Exact forward commands (7D.9 §10): `git fetch origin <candidate>` +
  `git checkout --detach <candidate>` + `chown -R root:pcae` + two
  `find -perm -u+x` branches mapping to `0750`/`0640` (self-computing
  mode-mapping, not a fixed inventory literal).
- Exact read-back commands (7D.9 §11): HEAD/detached/status/remote/
  `ls-files` count/tree-mode histogram/independent `os.lstat`
  cross-check/`git diff <candidate> -- .` (zero)/two file-presence
  probes/two `stat` mode probes.
- Exact corrected Action-9 invocation (7D.9 §16, reproduced verbatim in
  §12 below).
- Mutation inventory (7D.9 §12 rollback analysis; independently
  reconfirmed §17 below): the entire live-Dell mutation performed by
  7D.11 is exactly `fetch` + `checkout --detach` +
  `chown -R root:pcae` + mode-remap `find`/`chmod` — no venv
  reinstall, no wrapper mutation, no binding/certification/activation
  artifact created.
- No-go boundaries (CHGR §"conditions", item 6): no venv reinstall, no
  wrapper mutation, no `DeploymentBinding`, no Boundary C, no Boundary
  A, no Cutover Record, no Permission Broker/POL-005/COMP-002 change,
  no repository onboarding.

## 3. Governing Authority Chain — Independent Reconstruction

`chgr-0e37ed1340b14311826722c4dbf3e856` read directly (not via 7D.10/
7D.11's verify result):

- `lifecycle_state`: `published`. `selected_option_id`: `approve`.
- `decision_subject`/`rationale` bind the full candidate SHA
  `28bf137b5dc95d024e8913b678dce0501a46fd0f` by text (not an
  abbreviated form, not a branch name).
- `rationale` binds the corrected Action-9 PATH
  `/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin` by text.
- `rationale` explicitly states: no venv reinstall (path-bound, not
  byte-bound), no wrapper mutation, expected residual exactly
  `{HBDC-REQ-042}` with mandatory STOP-for-adjudication on any other
  outcome, and the HMIC implementation/source-identity-changed,
  **NOT-CERTIFIED-FOR-BOUNDARY-C** disclosure.
- `conditions` field enumerates the same exclusion list independently
  (venv/wrapper/`DeploymentBinding`/Boundary C/Boundary A/Cutover
  Record/Permission Broker/POL-005/COMP-002/repository onboarding —
  none authorized "in this or any future phase, without a fresh,
  separate election").
- `template_ref`: `class-b-boundary-p-provisioning-authorization` v1.0.
  `contract_version`: `CHGR-001/1.0`.

`pcae governance-record verify --related` was not re-run this phase
(7D.10 already independently ran and passed it against this exact
record); its structural legality is not the subject of new doubt here
— this phase's own contribution is the *text* re-read above, verifying
the record's own claims bind the exact candidate SHA and PATH rather
than trusting 7D.11's citation of it.

## 4. Historical CHGR Applicability — Independently Re-Read

- `chgr-96a0ce12756e4cc892492a87af1db832`: `lifecycle_state` =
  `published`; `decision_subject` + `rationale` combined does **not**
  contain the candidate SHA.
- `chgr-541cb08c313b4f8884970172d37c5a1d`: same result — `published`,
  combined text does **not** contain the candidate SHA.

**D3-3: CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION
HARDENING GAP RETAINED.** Neither historical CHGR can validly authorize
the deployed repaired-source transition — carried forward unchanged, no
formal supersession machinery implemented or claimed.

## 5. Fresh Dell Identity

Read-only `ssh hac-dell` (`192.168.192.200`, user `codex`,
key `~/.ssh/id_ed25519_hac_dell`, passwordless `sudo -n` available for
root-owned-path inspection only):

```
/etc/machine-id: 54ff22ce400b475aa0d55cb68f4a3334   (EXACT match)
hostname:        atila-Latitude-E5470                (EXACT match)
/etc/os-release:  Ubuntu 24.04.3 LTS (Noble Numbat)
uname -m:         x86_64                              (EXACT match)
```

No mismatch. Non-blocking.

## 6. Retained Actions 1–5 — Freshly Inspected

- **Action 1 (packages):** `git 2.43.0`, `python3 3.12.3`,
  `python3-pip 24.0`, `python3-venv 3.12.3`, `acl 2.3.2` — all present
  (`dpkg -l`).
- **Action 2 (pcae identity):** `id pcae` → `uid=1004(pcae)
  gid=1004(pcae) groups=1004(pcae)` — no supplementary groups, not a
  member of `sudo`. `getent passwd pcae` → shell
  `/usr/sbin/nologin`, home `/home/pcae`. `sudo -n -l -U pcae` →
  explicitly denied ("User pcae is not allowed to run sudo").
- **Action 3 (Protected Root):** `/etc/pcae/hatp/trust-store` —
  `root:pcae 750`, ACL `user::rwx group::r-x other::---` (no extra
  grants), not a symlink, ancestors `/etc/pcae/hatp`, `/etc/pcae`,
  `/etc` all `root:root 755`.
- **Action 4 (authorized paths):** `/opt/pcae` `root:pcae 750`;
  `/opt/pcae/runtime`, `/opt/pcae/runtime/src`,
  `/opt/pcae/runtime/venv`, `/opt/pcae/runtime/bin`,
  `/opt/pcae/projects` all `root:pcae 750`.
- **Action 5 (`/home/pcae`):** `pcae:pcae 750`; contents are the stock
  Ubuntu skeleton (`.bashrc`, `.profile`, `.bash_logout`, `.face`) —
  unremarkable, no mutation.

No mutation performed against any of the above.

## 7. Source Credential — Read-Only Verification

`/root/.ssh/pcae_harness_deploy_ed25519`: owner `root:root`, mode
`600`. `sudo -n -u pcae cat` of the file: **Permission denied** —
independently reconfirms `pcae` cannot read it. `IdentitiesOnly yes` in
`/root/.ssh/config` guarantees deterministic key selection. `origin`
remote is `git@github.com:atimad/pcae-harness.git` — repository-scoped,
not org-wide. `known_hosts` contains pinned GitHub host key entries.
Private key bytes were never read. No test push was performed.

## 8. Deployed Source SHA

```
sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
  → 28bf137b5dc95d024e8913b678dce0501a46fd0f   EXACT match to candidate
```

## 9. Detached/Clean Source State

```
symbolic-ref -q HEAD ; echo $?   → 1 (detached)
status --short --untracked-files=all → (empty; clean)
remote get-url origin            → git@github.com:atimad/pcae-harness.git
core.filemode                    → true (mode drift is NOT masked)
```

## 10. Candidate Authenticity From Primary Git Objects

On Mac: `git cat-file -t 28bf137b...` → `commit`. `git merge-base
--is-ancestor 28bf137b... origin/main` → exit 0 (is an ancestor).
Same checks against the old SHA `7a3fa971...` → also a real commit,
also an ancestor.

## 11. Candidate Production Diff — Independently Reconstructed

`git diff --stat 7a3fa971... 28bf137b...` returns 88 changed files —
the full span of accumulated governance/task/doc artifacts across the
entire 7D.1–7D.11 sequence. Restricting to `src/`, `scripts/`,
`docs/contracts/`, `pyproject.toml` narrows this to **exactly three
files**, independently confirming the prior "three files" claim rather
than inheriting it:

```
src/pcae/core/hatp_class_b_conformance.py       | 2 +-
src/pcae/core/hatp_class_b_topology_verifier.py | 89 +-
src/pcae/core/hatp_environment_lock_verifier.py | 2 +-
```

The two 2-line diffs are byte-identical single-line repairs:

```
-        dist = importlib.metadata.distribution("pcae")
+        dist = importlib.metadata.distribution("pcae-harness")
```

applied in both `hatp_class_b_conformance.py` (REQ-022) and
`hatp_environment_lock_verifier.py` (REQ-035).

## 12. Candidate Tracked-Tree Inventory — Recalculated, Not Inherited

Independent `git ls-tree -r` / `git ls-files` against the candidate SHA
directly (no worktree needed on Mac — direct object inspection):

```
4108 total tracked paths
4097 × 100644
  11 × 100755
   0 symlinks, 0 submodules
```

Matches the claimed 7D.10 figures exactly — recalculated, not
inherited.

## 13. Dell Filesystem Mode Inventory — Full Scan, Not Sampled

Live `ssh hac-dell`, full-tree scan (all 4108 tracked paths, not
limited to the three repaired files):

```
git ls-tree -r HEAD | while read mode type sha path; do
  actual=$(stat -c '%a' -- "$path")
  expected = 640 if mode==100644 else 750
  [ "$actual" != "$expected" ] && echo "MISMATCH ..."
done
→ zero MISMATCH lines emitted
```

**Zero mismatches across the complete 4108-path set.**

## 14. Dell Source Byte Identity — Complete HMIC Member Set

Independently re-derived the current HMIC-001 v1.3 authority-bearing
source membership from primary source
(`hatp_mandatory_certification._FROZEN_SRC_PCAE_RELATIVE_FILES` +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, asserted `len == 28`), not
from any prior phase's docstring summary. For **all 28 canonical
files** (not merely the three previously-repaired ones), computed
`sha256sum` on the live Dell deployed checkout and compared against
each file's own candidate-commit git-blob SHA-256:

**All 28 match exactly, zero mismatches** — a strictly complete
verification, exceeding the three-file sample used by prior phases in
this sequence.

## 15. Source Content Cleanliness

`git diff 28bf137b... -- .` on Dell → 0 lines (zero content-byte
drift from the pinned candidate commit, independent of the mode-only
`git status` check).

## 16. Git Configuration

`core.filemode=true` (mode changes are tracked, not masked by `git
status`), `core.bare=false`, remote URL confirmed repository-scoped.
No unusual checkout configuration found that could mask a mode-drift
condition.

## 17. HMIC Membership

Confirmed against production source this phase: exactly 28 canonical
paths (`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28`), the three
repaired verifier modules are members, and
`hmic._frozen_canonical_paths()` produces the identical 28-path set
independently reconstructed for §14.

## 18. HMIC Implementation/Source Digest on Dell

Ran the actual production `derive_implementation_scope_digest()`
function directly against Dell's real deployed tree, under the
deployed venv, read-only:

```
sudo -n -u pcae env -i HOME=/home/pcae \
  PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pathlib import Path
from pcae.core.paths import HarnessPath
from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
print(derive_implementation_scope_digest(HarnessPath(Path("/opt/pcae/runtime/src"))))
'
→ 4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac
```

Cross-verified independently on Mac via a disposable `git worktree
--detach` of the candidate commit — identical digest. **Matches the
candidate's own independently computed identity exactly.**

## 19. HMIC Contract Identity

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
header: `**Version:** 1.3`. `git diff <candidate> HEAD --
docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
→ empty (byte-identical). Contract identity is unchanged and is a
**distinct binding** from the implementation digest that did change
(§18). **HMIC is NOT stated VALID anywhere in this report.**

## 20. Certification State

Searched canonical certification/binding surfaces:

- `/etc/pcae/hatp/trust-store` on Dell: `sudo -n find ... -type f` →
  **zero files** — the registry itself does not exist, hence zero
  `DeploymentBinding` records and zero certification records of any
  kind.
- Repository-side: no file or directory anywhere in the repo matches
  `*deploymentbinding*`/`*deployment-binding*`/`*deployment_binding*`.
  The candidate digest `4e3452ba...` appears only inside CHGR
  proposition/decision-session disclosure artifacts (the human-facing
  election record itself), never inside any record with a
  certification `record_type`.
- No Boundary-C artifact treating the candidate as certified exists.

**CANDIDATE SOURCE IDENTITY DEPLOYED — NOT CERTIFIED.**

## 21. Existing Venv Identity

```
/opt/pcae/runtime/venv                            root:pcae 750
venv/bin/python3 -> /usr/bin/python3               (symlink, root:pcae)
.pth (_editable_impl_pcae_harness.pth)           → /opt/pcae/runtime/src/src
direct_url.json                                   → {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
dist-info                                          pcae_harness-0.2.0.dist-info, Name: pcae-harness, Version: 0.2.0
console script (venv/bin/pcae)                     unchanged content, imports pcae.cli.main
dist-info ownership                                root:pcae 750 (dir), 640 (files) — no world access
```

No reinstall was performed or observed (`INSTALLER`/`RECORD`/
`direct_url.json` timestamps consistent with the original install, not
this phase's session).

## 22. Venv Path Binding

`.pth` resolves to exactly `/opt/pcae/runtime/src/src` and
`direct_url.json` to `file:///opt/pcae/runtime/src` — not an
old-SHA-specific path, not a Mac path, not user-site, not another
checkout.

## 23. Runtime Import Provenance

Read-only import introspection under the deployed venv (locked-down
`env -i` environment) for all three repaired verifier modules:

```
pcae.core.hatp_class_b_conformance       → /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_conformance.py       sha256 dc2f26e2...
pcae.core.hatp_class_b_topology_verifier → /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_topology_verifier.py sha256 edba4612...
pcae.core.hatp_environment_lock_verifier → /opt/pcae/runtime/src/src/pcae/core/hatp_environment_lock_verifier.py sha256 1d28fec0...
```

Every hash matches the corresponding candidate git-blob hash exactly
(§14). This proves the runtime resolves and imports the candidate
source under the corrected environment. Per HMIC-REQ-063's own
disclosed limitation, this is import/resolution-identity proof, not a
stronger cryptographic/runtime-provenance guarantee — no stronger claim
is made here than the current architecture supports.

## 24. Distribution Identity

`importlib.metadata.distribution("pcae-harness")` under the deployed
venv: `Name: pcae-harness`, `Version: 0.2.0`,
`_path: .../pcae_harness-0.2.0.dist-info`. This is the exact identity
the repaired lookup code (§11) now queries — REQ-022/REQ-035 are
therefore semantically aligned with the real installed distribution,
independently confirmed on the real host, not merely inferred from the
source diff.

## 25. Wrapper Identity

```
/opt/pcae/runtime/bin/pcae-launch
  size:        188 bytes    (EXACT)
  line count:  9             (EXACT)
  sha256:      b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32  (EXACT)
  owner/mode:  root:pcae 750
  symlink:     no
  ACL:         user::rwx group::r-x other::--- (no unexpected grant)
```

## 26. Wrapper Semantics

```
#!/bin/sh
set -eu
unset PYTHONPATH
PYTHONNOUSERSITE=1
export PYTHONNOUSERSITE
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH
cd /opt/pcae/runtime
exec /opt/pcae/runtime/venv/bin/pcae "$@"
```

`set -eu`; `PYTHONPATH` cleared via `unset` (not merely emptied);
`PYTHONNOUSERSITE=1` exported; wrapper's own internal `PATH` fixed to
`/usr/bin:/bin:/usr/sbin:/sbin` (this is a **distinct** value from the
Action-9 diagnostic PATH in §27 — the wrapper does not need
`venv/bin` on its own internal `PATH` because it `exec`s the venv's
`pcae` binary by **absolute path**, no `PATH` search); fixed CWD
(`/opt/pcae/runtime`); argument forwarding (`"$@"`); no shell-profile
sourcing (plain `#!/bin/sh`, no `-l`, no `.`/`source`).

## 27. Reconstruct Corrected Action-9 Invocation

Recovered byte-for-byte from the governing CHGR evidence chain (the
human-approved 7D.9 proposition §16, bound by
`chgr-0e37ed1340b14311826722c4dbf3e856`'s own rationale text, §3
above) — not from 7D.11's prose:

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

Effective identity `pcae` (no escalation); `HOME=/home/pcae`; corrected
`PATH`; `PYTHONNOUSERSITE=1`; absolute interpreter path; `CWD=
/opt/pcae/runtime/src`; `env -i` full-environment clear; entry point
`verify_class_b_deployment_conformance()`. Read-only, requires no
rollback.

## 28. Corrected PATH

`/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin` — confirmed
exact match to the CHGR's own bound text (§3).

## 29. PATH Trust Topology

Every component independently inspected:

```
/opt/pcae/runtime/venv/bin   root:pcae 750  (group r-x only, no write)
/usr/bin                     root:root 755
/bin  -> /usr/bin (symlink)  target root:root 755
/usr/sbin                    root:root 755
/sbin -> /usr/sbin (symlink) target root:root 755
ancestors (/, /usr, /opt, /opt/pcae, /opt/pcae/runtime)  all root-owned, 755/750
```

No PATH component, nor any ancestor, grants `pcae` (or any
non-root/pcae-group principal) write access anywhere in the chain.
**No path component capable of shadowing `pcae` is agent-writable.**

## 30. Launcher Resolution

Under the exact corrected isolated environment:

```
env -i HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 sh -c 'which -a pcae'
→ /opt/pcae/runtime/venv/bin/pcae   (exactly one result, no alternate)
```

## 31. REQ-036 Independent Verification

`_check_launcher` (`hatp_environment_lock_verifier.py:368-382`) uses
`shutil.which("pcae")` against the invoking process's PATH — resolves
left-to-right, first match wins. §29 proves no PATH component is
agent-writable and §30 proves resolution lands on the venv's own
admin-controlled console script. Both preconditions are independently
satisfied on live Dell state, not merely inferred from 7D.11 no longer
reporting the ID. Live Action-9 run (§37) confirms `HBDC-REQ-036 True`.

## 32. REQ-022 Independent Verification

§24's live `importlib.metadata.distribution("pcae-harness")`
introspection confirms correct distribution lookup; §21/§22 confirm
`editable: true` and the direct-url path binding. Live Action-9 run
confirms `HBDC-REQ-022 True`.

## 33. REQ-035 Independent Verification

§21's dist-info listing confirms `RECORD` presence, and the dist-info
directory/files are `root:pcae 750/640` — admin-controlled, not
agent-writable. Live Action-9 run confirms `HBDC-REQ-035 True`.

## 34. REQ-030 Independent Verification

```
/usr/lib/python3.12/sitecustomize.py -> /etc/python3.12/sitecustomize.py  (symlink, root:root)
/etc/python3.12/sitecustomize.py   root:root 644
/etc/python3.12                    root:root 755
/usr/lib/python3.12                root:root 755
```

Symlink target and every ancestor are root-owned; `pcae` has no write
grant anywhere in the chain (no group-`pcae` ownership on any of
these). **Safe / not agent-writable** — matches the expected normative
result. Live Action-9 run confirms `HBDC-REQ-030 True`.

## 35. Independent Action-9 Execution

Ran the exact corrected command (§27) live against Dell, twice:

```
RUN 1: NON_COMPLIANT
RUN 2: NON_COMPLIANT
```

Both runs: every check `True` except `HBDC-REQ-042` (`False`,
`no_repository_identity_present`). Full structured result captured
(39 checks total; representative set: REQ-001/002/004/005/007/008/
011-021/025-039/022 all `True`; REQ-042 `False`).

## 36. Residual Requirement

Failing set both runs: **exactly `{HBDC-REQ-042}`**. No other
requirement failed on either run.

## 37. Determinism

Two independent live runs produced **identical** results (status and
full per-check breakdown). No nondeterminism observed.

## 38. Unexpected COMPLIANT

Both runs returned `NON_COMPLIANT` (not `COMPLIANT`). No
investigation trigger.

## 39. REQ-042 Independent Reconstruction

Traced the actual code path
(`hatp_class_b_conformance._check_deployment_identity`), not assumed
from the check ID alone: `resolve_canonical_deployment_root()`
succeeds; `repository_identity.read_repository_identity()` returns
`None` (the identity file is **genuinely absent** — independently
confirmed via `sudo -n test -e
/opt/pcae/runtime/src/.pcae/repository-identity.json` → absent) →
reason `no_repository_identity_present`. Independently, `sudo -n find
/etc/pcae/hatp/trust-store -type f` on Dell found **zero files** — the
trust-store registry itself does not exist, so no `DeploymentBinding`
could match even if a repository identity were present. Both facts
independently corroborate the correct failure; this is not an
absence-of-filename assumption.

## 40. DeploymentBinding Absence

Confirmed absent both in repository canonical state (§20) and on Dell
(§39, empty trust-store). No creation performed by this phase.

## 41. Mutation Inventory Reconstruction

- **7D.1:** credential prerequisite — provisioned the read-only GitHub
  deploy key `/root/.ssh/pcae_harness_deploy_ed25519` (owner/mode
  independently reconfirmed unchanged, §7).
- **7D.2:** Actions 1–5 retained provisioning — packages, `pcae`
  principal, Protected Root, authorized paths, `/home/pcae` (all
  independently reconfirmed unchanged, §6).
- **7D.5:** Actions 6–8 initial deployment — original source checkout,
  venv creation, wrapper creation (venv/wrapper state independently
  reconfirmed unchanged since, §21/§25).
- **7D.11:** source transition old SHA → repaired candidate — `fetch` +
  `checkout --detach` + `chown -R root:pcae` + mode-remap
  `find`/`chmod` (independently reconfirmed as the complete and only
  mutation, §8–§16).

Current host state is fully explainable by these four governed phases.
No unexplained infrastructure mutation was found.

## 42. Unrelated Dell Resources

`getent passwd atila uosserver clawdbot` — all pre-existing accounts,
unrelated to this provisioning. Home-directory mtimes: `atila`
2026-07-29, `uosserver` 2026-01-25, `clawdbot` 2026-01-31 — all
predate this phase's provisioning window (2026-08-15), none show
recent modification. `lastlog`: `uosserver`/`clawdbot` never logged
in; `atila`'s last login is the pre-existing 2026-07-29 entry.
`hac-windows` was not inspected (out of scope, per instruction). No
broad host scan was performed.

## 43. pcae Privilege Isolation

`id pcae` → `uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)` (no
supplementary groups). `getent passwd pcae` → shell
`/usr/sbin/nologin`. `sudo -n -l -U pcae` → explicitly denied. Cannot
write root-owned source (`750`, group r-x only), venv (`750`, same),
wrapper (`750`, same), or Protected Root (`750`, same, ACL confirms no
extra grant). Cannot access the deploy private key (§7, `Permission
denied`). Cannot write Protected Root's registry directory (same `750`
grant, empty — nothing to write to even if it could).

## 44. Source Credential Isolation

`sudo -n -u pcae cat /root/.ssh/pcae_harness_deploy_ed25519` →
`Permission denied`. Private key bytes were never read by this phase,
including as root — only ownership/mode/access-denial were checked.

## 45. Runtime State

`pcae runtime inspect` (Mac, canonical): `Observed` / `observe` /
`unavailable` — unchanged. No provisioning activity on Dell touches
this Mac-side canonical runtime-authority state; nothing in the Dell
mutation inventory (§41) could alter it.

## 46. Permission Broker

`pcae permission-broker status`: `simulation_only: True`,
`enforcement_active: False`, `enforcement_ready: False`,
`enforcement_authorized: False`. No POL-005/COMP-002 mutation
occurred. No repair or alteration performed.

## 47. Repository Onboarding

`sudo -n ls -la /opt/pcae/projects` on Dell → only `.`/`..` — the
project-root container exists and is empty. No
`/opt/pcae/projects/<repo-slug>/repo` was created by this or any prior
phase.

## 48. Centralized-Governance Exclusion

No central multi-repository governance component exists in the
repository or on Dell. Not broadened into unrelated future work.

## 49. CHGR Integrity After Execution

`git status --short .pcae/publication-execution/records/` → empty; all
three CHGR JSON files are byte-unchanged since publication. No
invented consumed/superseded state was found or asserted.

## 50. D3-3 Hardening Status

Carried unchanged: **CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE
SUPERSESSION HARDENING GAP RETAINED** (§4). No fresh evidence of
collision found this phase. No machinery implemented.

## 51. Historical Test Migration Debt

Carried accurately: **REGRESSION CLEAN WITH EXPECTED HISTORICAL TEST
MIGRATION REQUIRED.** This phase's own fresh companion test module (36
tests) runs clean and does not depend on any stale pin; no current
authority-bearing gate in this phase depends on the migration debt.
Not a Boundary-P blocker. No migration performed.

## 52. Architecture-Status Limitation Disposition

The recurring derived limitation ("current phase section has no
explicit 'Recommended next phase' sentence") appeared in 7D.11's own
canonical report (`pcae phase-report show --latest`, §1) alongside a
fully-populated `## Recommended Next Phase` section with complete
prose — the limitation is a generation-classifier nuance, not an
actual missing recommendation; PROJECT_STATUS.md independently confirms
the same recommended-next-phase text. Still merely reporting
incompleteness in the generator's own self-classification, not a
substantive gap. No status-generation code was altered in this phase.

## 53. No Dell Mutation

Every command executed against Dell this phase was read-only (`git
rev-parse`/`status`/`diff`/`ls-tree`/`ls-files`/`remote get-url`;
`stat`/`getfacl`/`ls`/`find`/`cat`/`sha256sum`/`id`/`getent`/`which`;
the Action-9 invocation itself, which performs zero mutation). No
`fetch`/`checkout`/`chmod`/`chown`/`pip install` was issued; no
user/group altered; no wrapper modified; no PATH persistently altered;
no binding/certification/activation artifact created.

## 54. No Mac Production Mutation

`git status --short -- src/ scripts/ docs/contracts/ pyproject.toml`
→ empty. No `src/pcae/**`, `scripts/**`, `docs/contracts/**`,
`pyproject.toml`, or CHGR file was modified by this phase.

## 55. Final Verification Verdict

**INDEPENDENTLY VERIFIED BOUNDARY-P PROVISIONING.**

All authorized Dell infrastructure and redeployment state is
independently correct, and Action 9 independently measures exactly
`{HBDC-REQ-042}` on two deterministic live runs.

## 56. Exact Post-7E Status

- Dell Boundary P: **INDEPENDENTLY VERIFIED PROVISIONED**
- Dell source `28bf137b...`: **INDEPENDENTLY VERIFIED DEPLOYED**
- REQ-022: **INDEPENDENTLY MEASURED SATISFIED**
- REQ-030: **INDEPENDENTLY MEASURED SATISFIED**
- REQ-035: **INDEPENDENTLY MEASURED SATISFIED**
- REQ-036: **INDEPENDENTLY MEASURED SATISFIED**
- REQ-042: **SOLE INDEPENDENTLY CONFIRMED RESIDUAL**
- Class-B: **BOUNDARY-P INFRASTRUCTURE INDEPENDENTLY VERIFIED — FULL
  HBDC CONFORMANCE BLOCKED SOLELY BY ABSENT DEPLOYMENTBINDING**
- HMIC: **REPAIRED IMPLEMENTATION/SOURCE IDENTITY DEPLOYED — NOT
  CERTIFIED**
- DeploymentBinding: **ABSENT / NOT AUTHORIZED**
- Boundary C: **NOT AUTHORIZED**
- Boundary A: **NOT AUTHORIZED**
- HATP: **NOT READY**
- Runtime: **Observed / observe / unavailable**

## 57. Important Progression Boundary

A clean 7E does not authorize Boundary C. It establishes only that the
real-host Boundary-P provisioning state is independently verified and
that `DeploymentBinding` is now the sole remaining HBDC residual. No
Boundary C work was begun in this phase.

## 58. Next Phase Derived From Primary Architecture

Independently inspected `src/pcae/core/hatp_bootstrap.py`: a
`DeploymentBinding` dataclass and a **read/match** path
(`HATPTrustStore.load_repository_enrollment`,
`deployment_binding_matches`) exist, but **no creation/registration
mechanism or CLI command exists anywhere in the codebase** for
producing a `DeploymentBinding` record (`grep` for
`create.*binding`/`register.*binding`/`enroll` in `hatp_bootstrap.py`
and for `deployment.binding`/`deployment_binding` in `cli.py`/
`commands/*.py` returns nothing). PROJECT_STATUS.md (§632, 7B.1)
independently confirms: *"a `DeploymentBinding` that no action in this
graph creates — a documented, intended consequence of the code's own
design, not a defect."* The governing CHGR's own condition 6 requires
"a fresh, separate election" before any `DeploymentBinding` may be
created — but there is nothing yet to elect on, since no
architecture/schema/mechanism for creating one has been designed.

**Determined next required step: DeploymentBinding architecture/design**
— not yet a binding proposition/authorization (nothing to propose
creating), and not Boundary-C certification preparation (certification
requires a bound deployment first). PROJECT_STATUS.md is treated as
authoritative over any stale TODO material where they might conflict;
no conflict was found.

## 59. No Boundary C in 7E

Not begun. Stopped after independent provisioning verification, per
instruction.

## 60. Governance Results

- **pcae_check:** passed
- **pcae_health:** healthy
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated,
  historical `tasks/done/`/`tasks/DONE.md` drift predating this phase)
- **pcae_push_check (entry):** clean (nothing_to_push)
- **pcae_runtime_inspect:** Observed / observe / unavailable
- **pcae_notify_status:** Telegram configured/enabled
- **pcae_permission_broker_status:** simulation_only, no enforcement
- **fast_green:** this phase's own new independent companion test
  module, run directly: 36 passed, 0 failed. This phase touches no
  other `src/pcae/**`/`tests/**` files.

## 61. Tests

`tests/test_phase_149o_20l_7e_dell_class_b_real_host_provisioning_independent_verification.py`
— 36 tests, independently authored, does not import 7D.11's test
module. Covers: governing-authority text binding, historical-CHGR
non-applicability, candidate authenticity/ancestry, tree inventory
recalculation, production-diff exactness, HMIC 28-member set/digest/
contract identity, live Dell facts (machine identity, deployed SHA,
28-file byte identity, full-tree mode inventory, wrapper digest, venv
path binding, distribution identity, runtime import provenance, PATH
trust topology, launcher resolution, sitecustomize safety, trust-store
emptiness, repository-identity absence), independent Action-9
determinism/residual-set/no-unexpected-COMPLIANT, pcae privilege/
credential isolation, project-onboarding absence, Permission Broker
and runtime-state unchanged, no-mutation, and report consistency.

## 62. No-Go Confirmations

No Dell mutation was performed by this phase — every SSH command was
read-only. No repair was performed on any narrow defect found. No
redeployment, reconfiguration, or Action-9 environment change was
made. No HMIC certification was computed, requested, or granted — the
candidate's changed HMIC implementation/source identity
(`4e3452ba...`) remains explicitly NOT CERTIFIED FOR BOUNDARY C. No
`DeploymentBinding` was created. No Boundary C or Boundary A activation
was performed. No Cutover Record was created. No Permission Broker,
POL-005, or COMP-002 change was made. No repository onboarding or
centralized multi-repository governance component was created. No
governance bypass, `--no-verify` flag, or force push was used. No
unrelated Dell principal (`atila`, `uosserver`, `clawdbot`) or
unrelated Dell resource was touched; `hac-windows` was not inspected.
No GitHub deploy-key rotation, revocation, reprovisioning, or test push
occurred; private key bytes were never read. No broadening of authority
was used to explain any result — the measured residual was exactly
`{HBDC-REQ-042}` on both independent runs, matching the sole authorized
expectation precisely. No `src/pcae/**`, `scripts/**`,
`docs/contracts/**`, `pyproject.toml`, or CHGR file was modified by
this phase.

## 63. Commits, Push, and origin/main..HEAD

See PROJECT_STATUS.md/CHANGELOG.md for this phase's own commit trail.
`pcae push check` was re-run before finalization; push status and
`origin/main..HEAD` are recorded in this phase's canonical
phase-completion report.
