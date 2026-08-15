# Phase 149O.20L.7D.9 — Repaired-Source Redeployment + Action-9 Invocation Amendment Proposition

## 0. Phase Identity and Type

**Proposition / authority-capture phase. Analysis and document drafting
only.** This phase does **not** touch Dell in any mutating way, does
**not** touch this Mac's production source tree, does **not** run `git
commit`/`git push`, does **not** run `pcae decision-session`/`pcae
governance-record publish`/`pcae phase complete`/`pcae task`, does
**not** create a CHGR, does **not** create a `DeploymentBinding`, does
**not** certify, and does **not** activate. All Dell interaction this
phase is read-only SSH (`cat`, `stat`, `id`, `git status`/`rev-parse`/
`log`, `ls`, `getfacl`, `sha256sum`, `pip show`, `which`, `test -w`,
`env -i ... which` diagnostics). No `chmod`/`chown`/`git fetch`/`git
checkout`/`pip install`/`systemctl`/write of any kind was issued
against Dell. The two work products are this document and its
companion pytest module, both written to disk, **neither committed to
git**.

## 1. Phase-Entry State

```
$ git log -1 --format=%H
0985dc5b7dcf49c46889c2ad9d77c21a91203457
$ git status --short
(clean)
```

Entering commit is `0985dc5b` ("Phase 149O.20L.7D.8: sync
phase-completion metadata to post-push state"), the tip of `main` at
phase start.

## 2. Candidate SHA — Independent Validation

**Candidate:** `28bf137b5dc95d024e8913b678dce0501a46fd0f` (subject:
"Phase 149O.20L.7D.7: repair pcae_push_check literal for finalization
gate").

Independently re-derived, this phase, not merely accepted from the
orchestrating session's brief:

```
$ git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f
commit
$ git merge-base --is-ancestor 28bf137b5dc95d024e8913b678dce0501a46fd0f origin/main && echo yes
yes
$ git merge-base --is-ancestor 73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2 28bf137b5dc95d024e8913b678dce0501a46fd0f && echo yes
yes
```

**Why the candidate's own commit subject is misleading, and why that
does not disqualify it.** The subject line names an unrelated
finalization-gate literal repair (`pcae_push_check`), not the Class-B
verifier repair. `28bf137b...` is a *later* commit than the actual
repair commit `73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2` (Phase
149O.20L.7D.7's own repair commit, independently verified by 7D.8 §2-3
via `git log -1 73ea8b23^` and a full `git diff 8a18f73d..73ea8b23`
touching exactly three production files). `git merge-base
--is-ancestor` above proves `73ea8b23` is an ancestor of `28bf137b...`
— i.e. every byte of the verifier repair is present in the candidate;
the candidate is simply a later point on `main` that happens to also
contain governance/doc/task-lifecycle commits made after the repair,
none of which touch `src/`, `scripts/`, or `docs/contracts/` (§3).
**Conclusion: the candidate SHA is correct and is preserved unchanged
as this proposition's bound future Dell source SHA.**

## 3. Post-Candidate Drift Analysis

```
$ git diff --stat 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD -- src/ scripts/ docs/contracts/ pyproject.toml
(empty)
```

Zero authority-relevant files have changed between the candidate and
the current repository tip (`0985dc5b`). Independently confirmed this
phase, not re-derived from the orchestrating session's claim alone —
the diff was re-run against this phase's own live `HEAD`.

## 4. Old-Deployed-to-Candidate Scoped Diff

```
$ git diff --name-status 7a3fa971304521cdcb44251e07ef1966baec686a 28bf137b5dc95d024e8913b678dce0501a46fd0f -- src/ scripts/ docs/contracts/ pyproject.toml
M	src/pcae/core/hatp_class_b_conformance.py
M	src/pcae/core/hatp_class_b_topology_verifier.py
M	src/pcae/core/hatp_environment_lock_verifier.py
```

Exactly three files, matching the repair diff independently
reconstructed by Phase 149O.20L.7D.8 §3 (`hatp_class_b_conformance.py`
1 line, `hatp_class_b_topology_verifier.py` +87/-1 lines,
`hatp_environment_lock_verifier.py` 1 line). No other production,
script, or contract file changed between the two SHAs.

## 5. Contract Version Verification (Candidate)

Read directly from the candidate's own git object, not from HEAD:

```
$ git show 28bf137b...:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md | grep -i version | head -1
**Version:** 1.0
$ git show 28bf137b...:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md | grep -i version | head -1
**Version:** 1.3
$ git show 28bf137b...:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md | grep -i version | head -1
**Version:** 1.1
```

HBDC-001 v1.0, HMIC-001 v1.3, HMRC-001 v1.1 — unchanged from the
old-deployed SHA (§3/§4 confirm `docs/contracts/` is untouched across
the entire old-deployed → candidate span). **Contract identity is
unchanged; only implementation/source identity changed** (§6).

## 6. HMIC Identity Consequence — Explicit Disclosure

**HMIC contract identity: UNCHANGED.** HMIC-001 remains v1.3, bytes
identical to what is bound today.

**HMIC implementation/source identity: CHANGED.** Independently
recomputed this phase, via disposable `git worktree --detach` checkouts
(never against the live repository's own `HEAD`, never against Dell),
using the production `derive_implementation_scope_digest()` function
itself (`src/pcae/core/hatp_mandatory_certification.py`):

```
candidate SHA (28bf137b...)  digest = 4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac
old-deployed SHA (7a3fa971...) digest = b728d368ee830d1e6f6e3c1fc44ca97d4826e3cf124c47c7c549b307dd1a545d
current repo HEAD (0985dc5b)  digest = 4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac (identical to candidate)
```

These three numbers were computed independently in this phase's own
disposable worktrees, not copied from 7D.8's report — they match 7D.8's
own reported values exactly, confirming the digests are real and
reproducible, not merely trusted prose.

**Consequence, stated explicitly:** the redeployment proposed below
changes Dell's HMIC *implementation* source identity from
`b728d368...` to `4e3452ba...`. **No HMIC certification exists anywhere
in this repository or, per live Dell evidence (§9), on Dell** — there
is no existing certification to invalidate. This proposition does
**not** compute, issue, or authorize any HMIC certification. **NOT
CERTIFIED FOR BOUNDARY C.** Any future certification attempt must
re-derive `implementation_scope_digest` against whatever Dell tree
exists at that time — this proposition does not pre-bind a future
certification's outcome.

## 7. Live Dell Baseline — Independently Re-Verified This Phase (Read-Only)

All commands below were executed live, this phase, over
`ssh hac-dell` (`192.168.192.200`, user `codex`, key
`~/.ssh/id_ed25519_hac_dell`). Every command is read-only; the full
literal SSH command log appears in the final report to the
orchestrating session.

### 7.1 Machine identity

```
/etc/machine-id: 54ff22ce400b475aa0d55cb68f4a3334
hostname: atila-Latitude-E5470
```
Exact match to every prior phase's binding.

### 7.2 Current source checkout

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD
    → 7a3fa971304521cdcb44251e07ef1966baec686a   EXACT MATCH (unchanged from 7D.5/7D.6/7D.8)
sudo git -C /opt/pcae/runtime/src symbolic-ref -q HEAD; echo $?
    → exit 1 (detached)
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all
    → empty
sudo git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
sudo stat -c '%U:%G %a %n' /opt/pcae/runtime/src
    → root:pcae 750
```

**Live, freshly-recounted tracked-path/mode inventory (not assumed from
prior phases' 4030/4024/6 figures):**

```
sudo git -C /opt/pcae/runtime/src ls-files | wc -l                → 4030
sudo git -C /opt/pcae/runtime/src ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    → 4024 100644
    →    6 100755
[independent Python os.lstat cross-check against every one of the 4030 tracked paths]
    → total 4030, ok640 4024, ok750 6, other 0, mismatches 0
```

Exact match to Actions 1-8's postcondition throughout the 7D.x sequence.
**No drift. Proceeding on a confirmed-accurate baseline.**

### 7.3 pcae principal, Protected Root, credential

```
id pcae → uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)
stat -c '%U:%G %a %n' /etc/pcae/hatp/trust-store → root:pcae 750
sudo stat -c '%n %U:%G %a' <8 paths under /opt/pcae, /var/lib/pcae, /var/log/pcae>
    → every line root:pcae 750
stat -c '%U:%G %a %n' /home/pcae → pcae:pcae 750
sudo test -f /root/.ssh/pcae_harness_deploy_ed25519 → KEY_EXISTS
sudo stat -c '%U:%G %a %n' /root/.ssh/pcae_harness_deploy_ed25519 → root:root 600
sudo cat /root/.ssh/config →
    Host github.com
        HostName github.com
        User git
        IdentityFile /root/.ssh/pcae_harness_deploy_ed25519
        IdentitiesOnly yes
```

Exact match to the 7D.1/7D.5/7D.6/7D.8 baseline. No credential rotation,
no test push, no content read of the private key — only `test -f`/
`stat`/`cat` of the (non-secret) public config stanza.

### 7.4 Editable-install venv inspection

```
sudo find /opt/pcae/runtime/venv -iname '*.pth' -exec cat {} \;
    → /opt/pcae/runtime/src/src
sudo find /opt/pcae/runtime/venv -iname 'direct_url.json' -exec cat {} \;
    → {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
sudo find /opt/pcae/runtime/venv -iname '*.dist-info' -maxdepth 6
    → ... pcae_harness-0.2.0.dist-info ... (plus jsonschema/attrs/referencing/rpds_py/typing_extensions/pip)
sudo -u pcae /opt/pcae/runtime/venv/bin/pip show pcae-harness
    → Name: pcae-harness, Version: 0.2.0, Editable project location: /opt/pcae/runtime/src
sudo cat /opt/pcae/runtime/venv/bin/pcae
    → #!/opt/pcae/runtime/venv/bin/python3 ... from pcae.cli import main ... sys.exit(main())
```

**Classification: NO VENV MUTATION REQUIRED.**

Evidence: the `.pth` file's content is the literal path
`/opt/pcae/runtime/src/src` — a filesystem path, not a pinned commit
SHA, content hash, or version string. `direct_url.json`'s `url` field is
likewise `file:///opt/pcae/runtime/src` — again a path, not a SHA. Both
artifacts bind the venv's import resolution to *the directory*, not to
*the bytes currently checked out there*. A source-only checkout swap
(fetch + `checkout --detach` to a new SHA at the same
`/opt/pcae/runtime/src` path) changes only the file bytes under that
already-referenced path; it does not change the path itself, so neither
the `.pth` entry nor `direct_url.json` becomes stale. The console-script
entry point `venv/bin/pcae` imports `pcae.cli` fresh at every invocation
— no caching, no compiled artifact pinning source bytes, confirmed by
its own shebang/import-at-call-time structure above. `RECORD` (10 lines,
confirmed non-empty, listing install manifest entries — unrelated to
source content). **No `pip install -e` re-run, no venv recreation, no
`RECORD`/`.pth`/`direct_url.json` regeneration is required or authorized
by this proposition.** Current venv state is bound as retained/untouched
(§13).

### 7.5 Wrapper digest

```
sudo sha256sum /opt/pcae/runtime/bin/pcae-launch
    → b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
```

**Exact match** to the authority-bound expected digest
`b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`. No
modification made or authorized. Wrapper bound as retained (§14).

### 7.6 DeploymentBinding — zero anywhere

```
sudo find /opt/pcae /etc/pcae -iname '*deploymentbinding*'   → zero matches
$ find .pcae -iname '*deploymentbinding*' (this repository)  → zero matches
```

### 7.7 PATH-resolution diagnostic (read-only `which`, no state change)

```
sudo -u pcae env -i HOME=/home/pcae PATH=/usr/bin:/bin:/usr/sbin:/sbin which pcae
    → (nothing), exit 1
sudo -u pcae env -i HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin which pcae
    → /opt/pcae/runtime/venv/bin/pcae, exit 0
git --version (Dell) → 2.43.0
```

Confirms 7D.6's diagnosis (§12 of that report) directly, live, this
phase: prepending `/opt/pcae/runtime/venv/bin` is necessary and
sufficient for `shutil.which("pcae")` to resolve, and it resolves to
the one admin-controlled (`root:pcae 750`), agent-unwritable launcher
artifact already present.

### 7.8 Summary

**No drift from the expected 7D.8 close-of-phase baseline anywhere.**
All eight prior findings (machine-id, source SHA/mode inventory, `pcae`
identity, Protected Root topology, credential, venv/editable-install
metadata, wrapper digest, DeploymentBinding absence) independently
re-verified true, live, this phase. Proceeding.

## 8. Update-in-Place vs. Staged-Replacement — Choice and Justification

**Chosen: update-in-place** — `git fetch` the candidate SHA into the
existing `/opt/pcae/runtime/src` checkout, then `git checkout --detach`
to it, re-applying the same mode-mapping discipline 7D.3/7D.5 already
established, using the candidate's own freshly-enumerated inventory
(§10).

**Rejected: staged-replacement** (fresh clone elsewhere, atomic
directory swap). Rejected because:

1. **It is not what 7D.5 established as the provisioning pattern.**
   7D.3/7D.5's own repaired Action 6 is itself an update-in-place
   pattern relative to Action 4's pre-created, pre-owned directory
   (clone into an already-`root:pcae 0750` path, not a swap of a
   populated directory) — introducing a parallel-clone-then-swap
   mechanism here would be a new command class this proposition would
   have to separately justify and would not reuse any already-verified
   forward/read-back/rollback text.
2. **A staged replacement would require re-establishing directory
   identity** (a `mv`/`rename` or bind-mount step) that touches
   `/opt/pcae/runtime/src`'s own inode/mount identity — a broader
   filesystem operation than a `git checkout` inside an already-owned,
   already-verified path.
3. **The venv's `.pth`/`direct_url.json` bind to the path, not the
   inode** (§7.4) — an update-in-place checkout at the same path is
   the narrowest mechanism consistent with "no venv mutation required."
   A staged-replacement swap that changed the path (even
   transiently) would risk invalidating that binding and reopen the
   venv-refresh question this proposition otherwise closes.
4. **Rollback simplicity.** Update-in-place rollback is a second
   `checkout --detach` to the old SHA inside the same, already-verified
   directory — no second directory to create, own, mode, and later
   garbage-collect.

## 9. Exact Preflight Commands (Read-Only)

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD
    → must equal 7a3fa971304521cdcb44251e07ef1966baec686a EXACTLY
sudo git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    → non-zero (detached)
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all
    → empty
sudo git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
stat -c '%U:%G %a %n' /opt/pcae/runtime/src
    → root:pcae 750
sudo git -C /opt/pcae/runtime/src cat-file -e 28bf137b5dc95d024e8913b678dce0501a46fd0f^{commit} ; echo $?
    → informational only (0 if already present in the local object store from a
      prior fetch, non-zero if a network fetch via the existing read-only
      deploy credential will be required in the forward step below)
```

**Preflight disposition:**
- All five checks above match exactly (as independently confirmed live,
  §7.2) → **EXACTLY SATISFIED entering condition, proceed to forward
  (§10).**
- Any preflight line not matching exactly → **STOP.** Do not proceed. Do
  not invent a substitute command. Disclose to the operator.

## 10. Exact Forward Mutation Commands (Not Yet Authorized — Materialized Here for the Human Election)

```
sudo git -C /opt/pcae/runtime/src fetch origin 28bf137b5dc95d024e8913b678dce0501a46fd0f
sudo git -C /opt/pcae/runtime/src checkout --detach 28bf137b5dc95d024e8913b678dce0501a46fd0f
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

Privilege: root (`sudo`, via `codex`). Mode-mapping logic (two `find
-perm -u+x` branches keyed on each file's own on-disk executable bit,
as `git checkout` already sets it from the Git index) is byte-identical
to 7D.3 §11 / 7D.5 §10's repaired Action-6 text — **not** the original
defective single-line `chmod 0640`. Applied here against the
**candidate's own inventory** (4097×`100644`, 11×`100755`, 4108 total —
§2 of the governing instruction's Dell facts, independently
reconfirmed via `git ls-tree -r 28bf137b...` this phase, matching the
orchestrating session's figures exactly), not the old 4030/4024/6
figures — the mode-mapping mechanism is self-computing at execution
time (it reads whatever `git checkout` produces from the *new* index),
so no manual inventory substitution is required in the command text
itself, but the read-back below asserts against the candidate's own
count explicitly, not the old count.

## 11. Exact Read-Back Commands

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD
    → must equal 28bf137b5dc95d024e8913b678dce0501a46fd0f EXACTLY
sudo git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    → non-zero (detached)
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all
    → empty
sudo git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
sudo git -C /opt/pcae/runtime/src ls-files | wc -l
    → 4108
sudo git -C /opt/pcae/runtime/src ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    → 4097 100644
    →   11 100755
[independent Python os.lstat cross-check against every one of the 4108 tracked paths,
 identical script pattern to §7.2, run against the candidate's own tree]
    → total 4108, ok640 4097, ok750 11, other 0, mismatches 0
sudo git -C /opt/pcae/runtime/src diff 28bf137b5dc95d024e8913b678dce0501a46fd0f -- . | wc -l
    → 0   (zero content bytes drift from the pinned candidate commit)
test -f /opt/pcae/runtime/src/docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md ; echo $?
    → 0
test -f /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_conformance.py ; echo $?
    → 0
sudo stat -c '%a' /opt/pcae/runtime/src/.githooks/pre-commit    → 750
sudo stat -c '%a' /opt/pcae/runtime/src/pyproject.toml          → 640
```

**Stop semantics — unchanged from the 7D.3/7D.5 precedent:** any
read-back line not matching exactly → STOP, execute the rollback below,
do not invent a substitute command, disclose to the operator.

## 12. Exact Rollback Commands and Network-Independence Analysis

```
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

**Rollback verification:**

```
sudo git -C /opt/pcae/runtime/src rev-parse HEAD → 7a3fa971304521cdcb44251e07ef1966baec686a EXACT
sudo git -C /opt/pcae/runtime/src status --short --untracked-files=all → empty
sudo git -C /opt/pcae/runtime/src ls-files | wc -l → 4030
sudo git -C /opt/pcae/runtime/src ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    → 4024 100644
    →    6 100755
```

**Network-independence — stated explicitly, analyzed, not assumed.**
`7a3fa971304521cdcb44251e07ef1966baec686a` is the SHA the Dell checkout
is **currently detached at, right now** (§7.2, live-reconfirmed this
phase). Git never garbage-collects a commit that is the current `HEAD`
of a checkout (it is always reachable via `HEAD` itself, independent of
any ref/branch), and rollback here does not delete or prune the
repository's object store at any point before switching back — the
forward step (§10) only *adds* the candidate's objects via `fetch`, it
does not remove or repack away the old SHA's objects. Therefore: **the
old commit `7a3fa971...` and every object it references (its full tree
and blob set) is guaranteed already present in Dell's local git object
store before the forward step ever runs, and remains present after it**
— rollback is a pure local `checkout --detach`, requiring **zero
network access, zero GitHub reachability, and zero use of the deploy
credential**. This is a structural guarantee (Git's own reachability
rule for the current `HEAD`), not an assumption dependent on `fetch`
having succeeded or having been run recently.

## 13. Venv — No Mutation Authorized

Per §7.4's independent classification (**NO VENV MUTATION REQUIRED**):
this proposition does **not** authorize `pip install -e` re-run, venv
recreation, or `.pth`/`direct_url.json`/`RECORD` regeneration. **Venv
reinstall is explicitly PROHIBITED by this proposition.** Current venv
state (`.pth` → `/opt/pcae/runtime/src/src`; `direct_url.json` →
`file:///opt/pcae/runtime/src`, `editable: true`;
`pcae_harness-0.2.0.dist-info`; console-script `venv/bin/pcae`) is
bound as **retained, untouched** across the source-checkout swap
proposed in §10.

## 14. Wrapper — No Mutation Authorized

No wrapper mutation is authorized by this proposition. Current wrapper
content, ownership (`root:pcae 750`), and digest
(`b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`,
independently re-verified live this phase, §7.5) are bound as the
**retained-gate value**. No `cp`/`chmod`/`chown` against
`/opt/pcae/runtime/bin/pcae-launch` is proposed anywhere in this
document.

## 15. REQ-036 Reconstruction — Old vs. Corrected Action-9 Invocation

**Old (frozen, currently authorized-and-consumed by
`chgr-541cb08c313b4f8884970172d37c5a1d`) environment:**
`PATH=/usr/bin:/bin:/usr/sbin:/sbin` — excludes
`/opt/pcae/runtime/venv/bin`, the only directory containing any
`which`-discoverable, admin-controlled `pcae` executable. This is
7D.6's independently diagnosed cause of the unexpected HBDC-REQ-036
failure (Finding B-149O.20L.7D.6-2), reconfirmed unrepaired by 7D.7/7D.8
(neither touched Action 9 or the wrapper), and reconfirmed live this
phase (§7.7).

**Corrected PATH:**
`/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin` — matches
7D.6's own confirmed-sufficient diagnostic counterfactual exactly.
**Independently re-derived, not merely copied**, from normative
environment-lock semantics this phase: HBDC-REQ-036 requires that if
production execution passes through a launcher, that launcher
configuration be admin-controlled and agent-unwritable *to the extent
it affects module resolution*. `_check_launcher`
(`hatp_environment_lock_verifier.py:368-382`) implements this via
`shutil.which("pcae")` against the invoking process's own `PATH` —
`shutil.which` resolves left-to-right and returns the *first* match, so
ordering matters for correctness, not just presence. Placing
`/opt/pcae/runtime/venv/bin` **first** guarantees the check resolves to
the venv's own admin-controlled console-script entry point
(`root:pcae 750`, confirmed §7.3/§7.4) rather than risking resolution
to any other `pcae`-named executable that might exist elsewhere on a
wider `PATH` — live-verified this phase (§7.7) that no directory in
the remaining `/usr/bin:/bin:/usr/sbin:/sbin` segment contains anything
named `pcae`, so ordering is not merely a theoretical concern deferred
to future drift; it is the exact, narrowest, currently-correct
placement. No other `PATH` widening (e.g. appending rather than
prepending, or adding additional directories) is proposed — this is
the minimum PATH change that resolves REQ-036 under the property
already independently confirmed true today (§7.5, §7.7).

## 16. Exact Corrected Action-9 Invocation (Full Literal Command)

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

Element-by-element, matching every item required by the governing
instruction:

- **Effective identity:** `sudo -u pcae` — no further privilege
  escalation, no root execution of the verifier itself.
- **HOME:** `/home/pcae` — the principal's own home, `pcae:pcae 750`
  (§7.3), consistent with every prior Action-9 invocation in this
  sequence.
- **Corrected PATH:** `/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`
  — §15's derivation; unchanged from 7D.6's confirmed-sufficient
  counterfactual.
- **PYTHONNOUSERSITE=1:** set explicitly, disabling user-site package
  injection (HBDC-REQ-029's own invariant), unchanged from every prior
  Action-9 invocation.
- **Absolute interpreter path:**
  `/opt/pcae/runtime/venv/bin/python3` — invoked directly, no `PATH`
  search for the interpreter itself (this is intentionally distinct
  from the `pcae` launcher `PATH` resolution being tested — see
  B-149O.20L.7D.6-4's disclosed, non-blocking observation that this
  project's own preferred invocation style is itself absolute-path-only
  for the interpreter, not `which`-discoverable, which is why this
  proposition does not attempt to "fix" the interpreter's own
  resolution by any `PATH` mechanism).
- **CWD:** `/opt/pcae/runtime/src` — the pinned checkout root, matching
  where HBDC-REQ-042's `repository_identity` evidence and the
  `pyproject.toml`/`docs/contracts/` presence checks (§11) expect to
  find their files.
- **`env -i` isolation:** the entire ambient environment is cleared
  first; only the four `KEY=value` pairs above are then set. No
  inherited `PYTHONPATH` (absent, not merely empty — `env -i` guarantees
  this). No shell profile is sourced (`sh -c` with an inline command
  string, no `-l`/login-shell flag, no `.` / `source` directive
  anywhere in the invocation).
- **Verifier entry point:** `pcae.core.hatp_class_b_conformance.verify_class_b_deployment_conformance()`,
  invoked via inline `python3 -c`, matching 7D.6's own reconstruction
  (§4 of that report) and 7D.5's original invocation shape (§18)
  byte-for-byte apart from the single `PATH` value change.

**Read-only.** `verify_class_b_deployment_conformance()` performs zero
mutation (confirmed by every prior phase in this sequence, most
recently 7D.5 §22 and 7D.8 §15) — this invocation, if and when
authorized and run in a future phase, requires no rollback of its own.

## 17. Diagnostic-Only Nature of the Counterfactual

The wide-`PATH` `which pcae` probe reproduced live in §7.7 of this
document, and 7D.6's own original counterfactual (its §12), are
**diagnostic evidence only**. Neither constitutes, nor is treated as,
an authorized Action-9 re-adjudication. No Action-9 result — old
`PATH`, wide `PATH`, or any other variant — has been, or is, treated as
a successful HBDC conformance measurement by this document. The only
purpose of §7.7's live reproduction is to confirm, on today's actual
Dell state, that the `PATH` correction proposed in §15-16 is still
sufficient before asking a human to authorize it — not to pre-declare
success.

## 18. Expected Residual After Both Changes Land

**Expected: exactly `{HBDC-REQ-042}`.**

Rationale, independently re-confirmed this phase:

- **HBDC-REQ-022/HBDC-REQ-035** (distribution-name lookup mismatch):
  repaired at the candidate SHA (§4, §6) — 7D.7's repair, 7D.8's
  independent verification, both confirmed via this phase's own
  candidate-ancestry check (§2).
- **HBDC-REQ-030** (symlink false positive): repaired at the candidate
  SHA (§4, §6) — same provenance.
- **HBDC-REQ-036** (Action-9 `PATH` gap): addressed by the corrected
  invocation (§15-16), not by any source change — confirmed live this
  phase (§7.7) that the corrected `PATH` resolves to the one
  admin-controlled launcher artifact.
- **HBDC-REQ-042** (`no_repository_identity_present`): remains failing
  by design — no `DeploymentBinding` exists or is authorized anywhere
  (§7.6), and this proposition does not create one. This is the
  architecturally-mandated residual under the current
  (no-`DeploymentBinding`) architecture, unchanged since 7D.5/7D.6/7D.7/7D.8.

**If a future real re-run measures anything other than exactly
`{HBDC-REQ-042}` — broader, narrower, or full `COMPLIANT` — that future
execution phase MUST STOP for read-only adjudication.** It must not
treat a narrower-than-expected or `COMPLIANT` result as an automatic
success, must not repair anything under that phase's own authority, and
must not broaden authority to explain the discrepancy. This mirrors
§41 of the governing instruction pattern already applied by 7D.5 when
its own actual residual came out broader than authorized.

## 19. Current-CHGR Insufficiency Statement

**`chgr-96a0ce12756e4cc892492a87af1db832`** (published
`2026-08-15T04:20:10Z`) — its own `decision_subject` and `rationale`
name "the exact nine-action provisioning plan," pinned source SHA
`7a3fa971304521cdcb44251e07ef1966baec686a` verbatim, and the original
(defective) Action-6 command text. Its `rationale` explicitly binds
"pinned source SHA 7a3fa971304521cdcb44251e07ef1966baec686a" as the
authorized source identity and makes no reference to any other SHA, any
source-update mechanism, or any Action-9 `PATH` value. **It does not
authorize the new source SHA, the source-identity transition proposed
here, or the changed Action-9 PATH** — read directly from the record's
own text, not inferred.

**`chgr-541cb08c313b4f8884970172d37c5a1d`** (published
`2026-08-15T07:54:39Z`) — its `decision_subject` and `rationale` scope
exclusively to "the repaired Action-6 forward/read-back/rollback
command sequence, the explicitly bound retained Actions-1-5 Dell
baseline, the continuation gates and STOP semantics, and unchanged
Actions 7-9" for the *original* pinned SHA `7a3fa971304521cdcb44251e07ef1966baec686a`.
This is the record actually consumed by 7D.5's real Action 6/7/8
execution and Action 9's (broader-than-expected) measurement. Its
`rationale` says nothing about a different source SHA and — because it
was published hours *before* the 7D.7 repair commit even existed
(`2026-08-15T07:54:39Z` vs. the repair's `14:10:25Z` same day,
independently reconfirmed by 7D.8 §9) — **it cannot, on its own text or
by publication-time ordering, reference the verifier source repair or
any new source SHA.** It explicitly excludes "any Dell mutation" beyond
the specific Action 6/7/8 sequence it binds, and does not authorize
Action 9's `PATH` value being anything other than the frozen text its
own `rationale` names ("unchanged Actions 7-9").

**Neither CHGR authorizes: (a) the new source SHA
`28bf137b5dc95d024e8913b678dce0501a46fd0f`, (b) the source-identity
transition from `7a3fa971...` to it, or (c) the changed Action-9 PATH
proposed in §15-16.** A fresh, separate CHGR (or an explicit textual
amendment following the 7D.3 precedent) is required before any future
phase may execute any command in §10 or §16 against Dell.

## 20. Explicit Full Exclusion List

This proposition, and any authority a human election on it may
eventually produce, explicitly excludes:

- **Actions 1-5 rerun.** The retained Actions-1-5 baseline (§7.3) is
  read-only reverified, never re-executed.
- **DeploymentBinding creation** of any kind, real or fake.
- **Boundary C** certification of any kind.
- **Boundary A** activation of any kind.
- **Cutover Record** creation.
- **Permission Broker** changes.
- **POL-005** changes.
- **COMP-002** changes.
- **Repository onboarding** — no `/opt/pcae/projects/<repo-slug>/repo`
  creation, no centralized multi-repository governance component.
- **Unrelated Dell users or Mac provisioning** — `atila`, `uosserver`,
  `clawdbot`, `hac-windows`, or any other principal/host are untouched
  and out of scope.
- **Deploy-key mutation** — the 7D.1 credential
  (`/root/.ssh/pcae_harness_deploy_ed25519`, GitHub deploy key id
  `160313031`) is read-only reverified (§7.3), never rotated, revoked,
  or reprovisioned by this proposition.
- **Arbitrary other source** — the only source identity this proposition
  binds is `28bf137b5dc95d024e8913b678dce0501a46fd0f`; no other SHA,
  branch, or ref is proposed.
- **Venv reinstall** (§13) and **wrapper mutation** (§14) — both
  explicitly prohibited, not merely unaddressed.
- **HMIC certification** or any certification-adjacent artifact
  computation (§6) — this proposition discloses the HMIC
  implementation-identity consequence but does not compute, request, or
  authorize a certification.
- **Execution in this phase.** This document and its companion tests
  are the entire work product; no command in §9/§10/§11/§12/§16 is run
  by this phase.

## 21. HUMAN ELECTION REQUIRED — NOT YET DECIDED

**This section is a placeholder.** It is not a decision, not an
approval, not an inferred selection, and not a request framed to imply
a default. The orchestrating session — not this phase — is responsible
for presenting this complete proposition to the human governance
authority via the real `pcae decision-session create` /
`... evidence` / `... select` / `... preview` / `... confirm` workflow
(the canonical CLI shape reconstructed at
`docs/PHASE_149O_20L_7B_DELL_CLASS_B_BOUNDARY_P_AUTHORIZATION_RECORD_CAPTURE.md`
§6) and for recording whatever the human actually types, verbatim, in a
future phase's own report — not here.

Three genuine options are available, with no default and no inferred
selection:

- **APPROVE** — authorize exactly the redeployment mechanism (§8-§12),
  the corrected Action-9 invocation (§15-§16), and every exclusion in
  §20, as presented in this document, with no material change.
- **DECLINE** — do not authorize any part of this proposition. Dell
  remains pinned to `7a3fa971304521cdcb44251e07ef1966baec686a`
  indefinitely, under the existing (already-consumed)
  `chgr-541cb08c313b4f8884970172d37c5a1d`. The HBDC-REQ-036 and
  HBDC-REQ-022/030/035 residuals remain open on the live Dell host.
- **AMEND** — request specific, named changes to this proposition
  (e.g., a different mode-mapping mechanism, a different PATH ordering,
  additional read-back checks) before a fresh election is sought,
  following the precedent set by the 7B.1 AMEND election.

No phase, agent, or process may treat silence, elapsed time, or a
request to "proceed" as an implicit APPROVE. No governance-record
publication, decision-session, or execution phase may consume this
proposition as authority until a real human election — with the
recorded verbatim election text and a separately confirmed preview
digest, per the CHGR-001 contract's own two-step
`select`-then-`confirm` discipline — actually occurs.

## 22. Recommended Next Phase (Not Authorized by This Phase)

Contingent entirely on the human election in §21:

- **If APPROVE:** a decision-session capture phase (analogous to 7B/7B.2
  and 7D.3's own CHGR-publication pattern) to record the election and
  publish a fresh CHGR explicitly superseding
  `chgr-541cb08c313b4f8884970172d37c5a1d` for redeployment purposes
  (per the same textual-precedence discipline 7D.3 §22 already
  established for `chgr-96a0ce12756e4cc892492a87af1db832`), followed by
  a real-host execution phase (analogous to 7D.5) that runs exactly
  §9-§12's commands, then §16's corrected Action-9 invocation, and
  measures the actual residual against §18's expectation.
- **If DECLINE:** no further phase in this sequence is recommended;
  the sequence closes with Dell pinned to `7a3fa971...` and both open
  findings (HBDC-REQ-022/030/035's source-side repair undeployed,
  HBDC-REQ-036's proposition-side repair unauthorized) left in their
  current diagnosed-but-undeployed/diagnosed-but-unamended state.
- **If AMEND:** a fresh proposition-amendment phase (analogous to
  7D.3's own relationship to the original 7B.1/7B.2 plan), materializing
  exactly the named changes before a new election is sought.

This phase does not itself recommend a specific outcome among the
three — it presents the bounded proposition and stops.
