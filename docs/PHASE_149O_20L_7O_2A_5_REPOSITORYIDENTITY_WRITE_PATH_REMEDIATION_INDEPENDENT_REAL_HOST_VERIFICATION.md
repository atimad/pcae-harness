# Phase 149O.20L.7O.2A.5 -- RepositoryIdentity Write-Path Remediation Independent Real-Host Verification

## 1. Scope

Verification-only phase. Independently verifies, from a fresh SSH
session to `hac-dell`, that the sole real-host mutation performed under
`chgr-86aeb5cfa7c44020ad002bc9f80c5856` in Phase 149O.20L.7O.2A.4 was
exactly the authorized transition:

```
/opt/pcae/runtime/src/.pcae
root:pcae 0750 -> root:pcae 1770
```

with no collateral state change. Does **not** trust 7O.2A.4's own
report, companion tests, prior SSH session, or read-back as an oracle
-- every claim below was independently re-derived this phase.

No Dell mutation of any kind was performed this phase (no chmod, chown,
setfacl, RepositoryIdentity creation, `ensure_repository_identity()`,
`pcae init`, DeploymentBinding creation, Protected Root mutation,
source mutation, HMIC certification, Boundary C, or HATP activation).

## 2. Phase-entry state

- Phase-entry commit: `e99abe55` (Phase 149O.20L.7O.2A.4: repair
  pushed_status/pcae_push_check trust fields post-push).
- `git status --short`: clean.
- `git status --branch --short`: `## main...origin/main` (up to date).
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy, all required files present, git status
  clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings only -- 30 active-looking task
  files and multiple `tasks/done/` entries not listed in
  `tasks/DONE.md`, all pre-existing and predating this phase, outside
  this phase's allowed-file scope, not remediated here.
- `pcae push check`: clean, nothing to push.
- `pcae runtime inspect`: Runtime status `not_implemented`, Runtime
  state `Observed`, execution capability `unavailable`, maximum
  plugin capability `observe`.
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: latest completed phase
  149O.20L.7O.2A.4, recommended next phase 149O.20L.7O.2A.5 (this
  phase).
- `pcae phase-report reconcile --phase-id 149O.20L.7O.2A.4`:
  reconciled, marker `already_dispatched`, checkpoint `completed`,
  receipt `finalized`, mutation `none (inspection only)`.

## 3. Fresh SSH session

Opened a fresh SSH session to `hac-dell` this phase; did not reuse the
7O.2A.4 session. Every remote command in this phase was read-only
(`stat`, `getfacl`, `find`, `git rev-parse`/`status`/`diff`, `sha256sum`,
`readlink`, `cat`, `id`, `getent`, `journalctl`/`grep` over
`/var/log/auth.log*`, plus two disposable read-only Python invocations
-- see SS9-10). No write/mutating command (`chmod`, `chown`, `setfacl`,
`touch`, `mkdir`, `rm` other than deleting this phase's own disposable
scripts, `git checkout/fetch/pull`, `pcae init`) was issued against
`hac-dell` at any point.

## 4. Machine identity

Freshly verified this phase, live:

| Check | Expected | Live result | Match |
|---|---|---|---|
| `hostname` | `atila-Latitude-E5470` | `atila-Latitude-E5470` | yes |
| `/etc/machine-id` | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` | yes |
| `uname -m` | (arch, informational) | `x86_64` | -- |
| `/etc/os-release` | (informational) | `Ubuntu 24.04.3 LTS` (noble) | -- |

Zero drift. No mismatch trigger fired.

## 5. Source identity

```
sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
  -> b0840e96a7ffb12308e95828aa5927c3e7c770c0
sudo -n git -C /opt/pcae/runtime/src symbolic-ref -q HEAD
  -> exit 1 (no symbolic ref -- HEAD is detached)
sudo -n git -C /opt/pcae/runtime/src status --porcelain
  -> empty (clean)
sudo -n git -C /opt/pcae/runtime/src diff --stat HEAD
  -> empty (no tracked-content drift)
```

Matches the expected election-time SHA exactly; detached and clean
confirmed independently.

Note: the SSH principal `codex` does not itself have read/traverse
access into `/opt/pcae` (`0750 root:pcae`, `codex` not a member of
group `pcae`) -- all remote reads in this phase were therefore issued
via `sudo -n` (the same pre-existing, already-used-read-only-in-every-
prior-149O.20L.7* phase, `codex ALL=(ALL) NOPASSWD: ALL` sudoers
scope), never as an unprivileged direct read.

## 6. `.pcae` exact mode

```
sudo -n stat /opt/pcae/runtime/src/.pcae
  File: /opt/pcae/runtime/src/.pcae
  Access: (1770/drwxrwx--T)  Uid: (0/root)  Gid: (1004/pcae)
```

Exactly `1770`, owner `root`, group `pcae`, type `directory`. No
approximation -- this is the literal `stat` mode field, not a summary.

## 7. ACL state

```
sudo -n getfacl -p /opt/pcae/runtime/src/.pcae
  # file: /opt/pcae/runtime/src/.pcae
  # owner: root
  # group: pcae
  # flags: --t
  user::rwx
  group::rwx
  other::---
```

Only the three base ACL entries (`user::`, `group::`, `other::`),
consistent with `stat`'s `1770` mode bits. No named-user entry, no
named-group entry, no default ACL, sticky flag (`--t`) represented
consistently with `stat`'s `T` bit. No extended ACL.

## 8. Path identity / symlink state

```
sudo -n stat -c '%F' /opt/pcae/runtime/src/.pcae      -> directory
sudo -n test -L /opt/pcae/runtime/src/.pcae            -> false (NOT_SYMLINK)
sudo -n realpath /opt/pcae/runtime/src/.pcae           -> /opt/pcae/runtime/src/.pcae (self)
sudo -n stat -c '%n %F %U:%G %a' \
  /opt/pcae/runtime/src /opt/pcae/runtime /opt/pcae /opt
  -> src        directory root:pcae 750
  -> runtime    directory root:pcae 750
  -> pcae       directory root:pcae 750
  -> (/opt)     directory root:root 755
```

`.pcae` is a real directory, not a symlink, `realpath` resolves to
itself (no path substitution). The parent chain retains its own
pre-existing `750` modes unchanged -- the child's `1770` mode change
did not propagate to or alter any parent.

## 9. Existing entry inventory

```
sudo -n find /opt/pcae/runtime/src/.pcae -mindepth 1 | wc -l          -> 131
sudo -n find /opt/pcae/runtime/src/.pcae -mindepth 1 -maxdepth 1 \
  -printf '%y %m %p\n' | wc -l                                        -> 17
sudo -n find /opt/pcae/runtime/src/.pcae -mindepth 1 \
  ! -user root -o ! -group pcae | xargs -r stat -c '%U:%G %n'         -> (empty)
```

17 top-level entries, 131 total entries (recursive), matching
7O.2A.4's independently-counted "17 pre-existing root-owned `.pcae`
entries" baseline exactly. Zero entries with any owner/group other
than `root:pcae` anywhere in the tree -- no unexpected deletion,
addition, rename, or file-type/ownership drift detected. Full
recursive listing (type, owner:group, mode, path) captured and
diffed against the 7O.2A.4 report's inventory; no discrepancy found.

## 10. Root-owned governed entries

Every one of the 131 entries under `.pcae` (see SS9) is individually
`root:pcae`, with directories at `750` and files at `640`, except the
parent `.pcae` itself (`1770`, the sole authorized change) and four
pre-existing files under `publication-execution/published/` which
carry `750` (a producer-set mode pre-dating this and the prior phase,
unrelated to and untouched by the CHGR's chmod). No child entry's
owner, group, or mode differs from the 7O.2A.4 post-mutation baseline.
The parent mode change did not alter any child metadata.

## 11. RepositoryIdentity absence

```
sudo -n test -e /opt/pcae/runtime/src/.pcae/repository-identity.json
  -> ABSENT
sudo -n find /opt/pcae/runtime/src/.pcae \
  -iname '*repository-identity*' -o -iname '.tmp-repository-identity-*'
  -> (empty -- none found)
```

Canonical path confirmed absent; no stray temp-identity files of
either the canonical or producer temp-naming pattern found anywhere
under `.pcae`. Nothing was created to test this.

## 12. DeploymentBinding / Protected Root absence

```
sudo -n ls -la /etc/pcae/hatp/trust-store
  total 8
  drwxr-x--- 2 root pcae 4096 Aug 15 08:55 .
  drwxr-xr-x 3 root root 4096 Aug 15 08:55 ..
```

Empty (only `.`/`..`, dated from initial provisioning, unchanged since).
No DeploymentBinding artifact present. No create/rotate/revoke issued.

## 13. Certification absence

```
sudo -n find /opt/pcae/runtime/src/.pcae -iname '*certif*'  -> (empty)
sudo -n find /etc/pcae -iname '*certif*'                    -> (empty)
```

No CertificationRecord, CertificationBinding, or active certification
artifact found under either location.

## 14. Protected Root integrity

Protected Root (`/etc/pcae/hatp/trust-store`) path, owner (`root:pcae`),
mode (`0750`), and contents (empty) all confirmed unchanged this phase
(SS12) -- identical to the 7O.2A.4 and 7O.2A.3 baselines, timestamped
from initial provisioning (`Aug 15 08:55`), predating this phase's CHGR
entirely. `.pcae`'s remediation shares no filesystem ancestor with
Protected Root and did not affect it.

## 15. Source tracked-content identity

Covered in SS5: `git status --porcelain` empty, `git diff --stat HEAD`
empty. No tracked mutation on `hac-dell` since the election-time SHA.

## 16. HMIC implementation digest (live invocation)

A disposable, read-only Python script
(`sys.path.insert(0, "/opt/pcae/runtime/src/src")`, then
`derive_implementation_scope_digest(HarnessPath(Path("/opt/pcae/runtime/src")))`)
was written locally this phase (not copied from any prior phase's
script), `scp`'d to `/tmp` on `hac-dell`, and executed as:

```
sudo -n -u pcae env -i \
  PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  HOME=/home/pcae PYTHONNOUSERSITE=1 \
  python3 /tmp/hmic_verify.py
```

Result:

```
65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
```

Matches the expected constant exactly -- actually invoked live, not
copied as proof. The script was deleted (`rm -f /tmp/hmic_verify.py`)
immediately after use; deletion independently confirmed (`ls` on the
deleted path reported "No such file or directory").

## 17. Wrapper

```
sudo -n sha256sum /opt/pcae/runtime/bin/pcae-launch
  -> b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
sudo -n stat -c 'owner=%U group=%G mode=%a' /opt/pcae/runtime/bin/pcae-launch
  -> owner=root group=pcae mode=750
```

Digest and owner/group/mode unchanged from the fixed baseline
re-verified across every 149O.20L.7* Dell phase.

## 18. Venv

```
sudo -n readlink -f /opt/pcae/runtime/venv/bin/python3
  -> /usr/bin/python3.12
sudo -n stat -c 'owner=%U group=%G mode=%a type=%F' \
  /opt/pcae/runtime/venv/bin/python3
  -> owner=root group=pcae mode=777 type=symbolic link
sudo -n find /opt/pcae/runtime/venv -maxdepth 5 \
  -iname '*.pth' -o -iname 'direct_url.json'
  -> .../site-packages/_editable_impl_pcae_harness.pth
  -> .../pcae_harness-0.2.0.dist-info/direct_url.json
sudo -n cat .../_editable_impl_pcae_harness.pth
  -> /opt/pcae/runtime/src/src
sudo -n cat .../direct_url.json
  -> {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
```

All unchanged: interpreter symlink target, `.pth` editable-install
path, and `direct_url.json` all still point at
`/opt/pcae/runtime/src`(`/src`), consistent with the unmoved,
unmutated source tree.

## 19. Canonical HBDC (two independent runs)

A second disposable, read-only Python script
(`verify_class_b_deployment_conformance(HarnessPath(Path("/opt/pcae/runtime/src")))`)
was written locally this phase, `scp`'d to `/tmp`, and executed twice
under the identical canonical environment as SS16:

Run 1:
```
status: ClassBConformanceStatus.NON_COMPLIANT
failing checks: [('HBDC-REQ-042', 'no_repository_identity_present')]
HBDC-REQ-036: True
total checks: 34
```

Run 2 (determinism check, same session, immediately after):
```
status: ClassBConformanceStatus.NON_COMPLIANT
failing checks: [('HBDC-REQ-042', 'no_repository_identity_present')]
HBDC-REQ-036: True
total checks: 34
```

Identical on both runs. `NON_COMPLIANT`, sole residual `HBDC-REQ-042`
(`no_repository_identity_present`), `HBDC-REQ-036` satisfied `True`,
34 total checks evaluated, all others `True`. No new residual
appeared. Script deleted and deletion confirmed identically to SS16.

## 20. CHGR integrity (independent re-read)

Independently re-read `chgr-86aeb5cfa7c44020ad002bc9f80c5856` and its
three related artifacts from the local repository mirror
(`.pcae/publication-execution/records/`) this phase -- not trusting
7O.2A.4's own re-verification:

```
pcae governance-record verify \
  .pcae/publication-execution/records/chgr-86aeb5cfa7c44020ad002bc9f80c5856.json \
  --related .../chgrconf-698eefcec95841ef8350e94fa7a59ea8.json \
  --related .../chgrintg-2fa93bd13e7e440f8c98a283cff99872.json \
  --related .../chgrprov-5a681f551c3646af81d7ecdb1a3ccff1.json

  outcome: verified
    check: schema_shape                  passed
    check: digest_self_consistency       passed
    check: lifecycle_structural_legality passed
    check: confirmation_binding          passed
    check: assurance_truthfulness        passed
    check: provenance_consistency        passed
    check: integrity_consistency         passed
    check: template_resolution           skipped  no matching related template supplied
```

`outcome: verified`, every applicable check passed. `template_resolution`
remains a legitimate skip -- no `decision_template`-typed artifact
exists anywhere in this repository, same disclosed condition as every
prior 149O.20L.7O.2A.* phase.

`lifecycle_state`: `published` (unrevoked). `decision_maker_identity_evidence.identifier`:
`Atila Madai` (unchanged).

Independently re-confirmed uniqueness among all six published CHGRs
(`chgr-0e37ed13...`, `chgr-541cb08c...`, `chgr-71bd24f9...`,
`chgr-86aeb5cf...`, `chgr-96a0ce12...`, `chgr-d4343fa5...`, all
`lifecycle_state: published`): only `chgr-86aeb5cfa7c44020ad002bc9f80c5856`'s
`decision_subject` names `/opt/pcae/runtime/src/.pcae` and the exact
`0750 -> 1770` transition.

## 21. CHGR scope vs live state

The CHGR's `decision_subject` and `conditions` authorize exactly:
target `/opt/pcae/runtime/src/.pcae`, `chmod 1770` only (no `-R`, no
`chown`, no `setfacl`), owner/group unchanged. The live state observed
this phase (SS6-7) is exactly that transition and nothing more. No
scope excess detected.

## 22. Mutation inventory reconstruction

Reconstructed from `sudo` command audit evidence
(`journalctl _COMM=sudo` and `/var/log/auth.log*`) on `hac-dell`,
filtered to `chmod`/`chown`/`setfacl` activity:

- Exactly one `chmod` targeting `/opt/pcae/runtime/src/.pcae` appears
  in the entire retained audit window:
  `2026-08-18T13:27:28.656635+02:00 ... USER=root ; COMMAND=/usr/bin/chmod 1770 /opt/pcae/runtime/src/.pcae`
  -- matching 7O.2A.4's reported execution timestamp and command
  exactly.
- No `chown` or `setfacl` command targeting `.pcae` or any path under
  it appears anywhere in the retained audit window (`auth.log` back
  through its `.4.gz` rotation, covering well before the CHGR's
  `2026-08-18T10:30:17Z` creation time).
- All other `chmod`/`chown` entries in the window are either: (a)
  bulk baseline-permission-setting from the 2026-08-15 initial
  deployment and the 2026-08-17T22:20 source redeployment (a separate,
  earlier-authorized CHGR's scope, predating and unrelated to
  `chgr-86aeb5cfa7c44020ad002bc9f80c5856`), or (b) this phase's own
  and 7O.2A.4's read-only `stat`/`getfacl`/`find` invocations (no
  mutation), or (c) an unrelated `chown pcae:pcae /tmp/...` on a
  disposable script from a prior phase (outside `.pcae`, outside
  scope).
- No child-file chmod inside `.pcae` appears in the window.

Conclusion: exactly one intended host-state change is evidenced --
`/opt/pcae/runtime/src/.pcae` mode `0750 -> 1770` -- with no
collateral chown, setfacl, child chmod, or source mutation.

## 23. Sticky-bit evidence qualification

Preserved unchanged: sticky-bit semantics
(`S_ISVTX`/`check_sticky()`/`fs/namei.c`) remain REFERENCE-VERIFIED
FROM PRIMARY LINUX/POSIX SOURCES, not empirically exercised by
creating synthetic root-owned files on `hac-dell` this phase or any
prior phase. No file was created this phase to strengthen this claim,
per governing-prompt SS25.

## 24. architecture-history.json correction

Carried forward unchanged: P-A' (the `chmod 1770` remediation) fixes
38 of the 39 declared write-required `.pcae` artifact paths. It does
**not** fix `architecture-history.json`, whose producer
(`write_architecture_history_snapshot`) uses a direct truncating
`open("w")` on a pre-existing, root-owned `0640` file rather than the
mkstemp+`os.replace` atomic-create idiom -- a directory-mode-only
change cannot grant write access denied by the file's own mode bits.
Not repaired this phase; no full `.pcae`-producer remediation is
claimed.

## 25. `pcae` principal state

```
sudo -n -u pcae id
  uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)
sudo -n getent passwd pcae
  pcae:x:1004:1004:PCAE agent principal:/home/pcae:/usr/sbin/nologin
```

No supplementary groups beyond its own primary group, shell
`/usr/sbin/nologin` (no interactive login), consistent with every
prior phase's baseline. No drift.

## 26. Runtime state

`pcae runtime inspect` (local, SS2): Runtime state `Observed`,
maximum plugin capability `observe`, execution capability
`unavailable`. Unchanged; no activation occurred this phase.

## 27. Final verdict

**INDEPENDENTLY VERIFIED -- PERMISSION REMEDIATION COMPLETE.**

Every postcondition matches its expected value exactly, independently
re-derived this phase from a fresh SSH session, without trusting
7O.2A.4's report, tests, session, or read-back as an oracle:

- `.pcae`: `root:pcae 1770`, no extended ACL, not a symlink, real
  directory -- verified.
- 17 top-level / 131 total pre-existing entries preserved, all
  `root:pcae`, no ownership/mode/type drift -- verified.
- RepositoryIdentity: absent, no temp-file trace -- verified.
- DeploymentBinding / Protected Root: absent/unchanged -- verified.
- Certification: absent -- verified.
- Source: `b0840e96a7ffb12308e95828aa5927c3e7c770c0`, detached, clean
  -- verified.
- HMIC digest: `65ff8ab0...` live-invoked, matches -- verified.
- Wrapper: digest and mode unchanged -- verified.
- Venv: interpreter/`.pth`/`direct_url.json` unchanged -- verified.
- Canonical HBDC: `NON_COMPLIANT`, sole residual `HBDC-REQ-042`,
  `HBDC-REQ-036` True, identical across two independent runs --
  verified.
- CHGR: published, unrevoked, sole record naming this exact
  transition, integrity chain binds -- verified.
- Mutation inventory: exactly one `chmod 1770` event, no chown/setfacl
  collateral -- verified.
- `pcae` principal, runtime state: unchanged -- verified.

No non-blocking finding arose this phase beyond the two disclosed,
carried-forward evidence-tier qualifications already on record
(sticky-bit reference-verification tier, `architecture-history.json`
carve-out) -- both preserved, neither newly discovered, neither
treated as blocking.

## 28. Tests

`pytest -m fast_green` (deselected pre-existing baseline failures,
identical deselect set as every prior 149O.20L.7* phase; see SS29):
clean pass for this phase's own test file plus the full fast_green
suite. This phase's dedicated test file
(`tests/test_phase_149o_20l_7o_2a_5_repositoryidentity_write_path_remediation_independent_real_host_verification.py`)
asserts local invariants only (CHGR self-consistency, uniqueness,
zero local RepositoryIdentity/DeploymentBinding artifacts, source
unchanged since election, doc self-consistency with the exact live
values reported above) -- the live-host findings above are not
reproducible in CI (no route to `hac-dell` exists there), consistent
with the precedent set by 7O.2A.4's own test file.

## 29. Governance results

- `pcae_health`: healthy
- `pcae_check`: passed
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated --
  historical `tasks/done/` entries predating this phase, outside this
  phase's allowed-file scope, not remediated here)
- `pcae_push_check`: clean (pre-implementation-commit baseline)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: Telegram configured/enabled
- `chgr_independent_reverify`: verified, all applicable checks passed
- `fresh_dell_live_verification`: zero drift on every dimension in
  SS4-26

## 30. No-Go confirmations

No Dell mutation of any kind was performed this phase: no `chmod`,
`chown`, or `setfacl` was issued against `hac-dell` (every remote
command this phase was a read command -- `stat`, `getfacl`, `find`,
`git rev-parse`/`status`/`diff`, `sha256sum`, `readlink`, `cat`, `id`,
`getent`, `journalctl`/log `grep`, and two disposable read-only Python
script executions, deleted immediately after use). No RepositoryIdentity
was created. No `ensure_repository_identity()` call was made. No
`pcae init` was run against `hac-dell`. No DeploymentBinding was
created, rotated, or revoked. No Protected Root mutation occurred. No
source mutation occurred (`git status --porcelain` empty both before
and after this phase's inspection). No HMIC certification was
performed. No Boundary C action was taken. No HATP activation
occurred. No synthetic file was created on `hac-dell` to empirically
test sticky-bit semantics. No new CHGR was published; no
decision-session was opened. No `src/pcae/**`, `scripts/**`,
`docs/contracts/**`, or `schemas/**`/`pyproject.toml` file was
modified this phase.

## 31. Recommended next phase

**149O.20L.7O.2B -- RepositoryIdentity Creation Retry on Dell.**

That phase should: fresh-check `.pcae` `1770`; re-derive the
pcae-principal identity-only command; execute exactly one
`ensure_repository_identity()` call; read back the exact
`repository_id`; verify `pcae:pcae 0600` on the resulting artifact;
verify idempotency; verify Git/HMIC unchanged; verify HBDC transitions
from `no_repository_identity_present` to
`no_active_deployment_binding_matches_repository_and_root`; stop
before DeploymentBinding field resolution/election if needed.

Not started this phase.

## Strategic breakpoint

Preserved, not begun this phase: after eventual RepositoryIdentity +
DeploymentBinding first-use execution and clean independent real-host
verification, pause before Boundary C, then begin (1) DeepSeek Harness
vs PCAE Comparative Architecture Study and (2) PCAE Runtime Adapter +
Plugin Architecture.
