# Phase 149O.20L.7B.1 — Dell Boundary-P Proposition Materialization (Amendment)

## 0. Phase Identity and Type

**Phase:** 149O.20L.7B.1
**Type:** PLANNING / PROPOSITION-REPAIR ONLY. Materialize the four
amendments elected by the human governance authority in Phase
149O.20L.7B's AMEND election. No provisioning. No new election. No
CHGR. No certification. No activation. No runtime-capability change.
**Basis:** Phase 149O.20L.7B (`docs/PHASE_149O_20L_7B_DELL_CLASS_B_
BOUNDARY_P_AUTHORIZATION_RECORD_CAPTURE.md`), decision session
`CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af`; Phase 149O.20L.7A (`docs/
PHASE_149O_20L_7A_CLASS_B_DELL_TARGET_RE_SELECTION_AND_READ_ONLY_
PREFLIGHT.md`) §26/§27/§34 (frozen literal names, nine-action plan,
draft proposition); `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(HBDC-001 v1.0); `docs/contracts/HATP_MANDATORY_INDEPENDENT_
VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001 v1.3); `docs/
contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001
v1.1); live inspection of `src/pcae/core/hatp_class_b_conformance.py`,
`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`
this phase; a live, read-only SSH reconfirmation of the Dell conducted
this phase.

## 1. Entering State (Independently Reconfirmed)

```
$ git status --short                → (clean)
$ git status --branch --short       → ## main...origin/main
$ git log --oneline origin/main..HEAD → (empty)
$ git rev-list --count origin/main..HEAD → 0
```

- `pcae health`: healthy. Agent lock: held by `claude-code`. Session
  continuity: verified. Git status: clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing, historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase by many prior phases; unrelated; outside this phase's allowed-
  file scope; not remediated here.
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: 149O.20L.7B's canonical report,
  consistent; recommended next phase names this phase (149O.20L.7B.1).
- `pcae phase-report reconcile --phase-id 149O.20L.7B`: `status:
  reconciled`, `mutation: none (inspection only)`.

Entering authority state:

```
Boundary P: NOT AUTHORIZED
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

This phase's entering commit is `7a3fa971304521cdcb44251e07ef1966baec686a`
— the same commit this phase independently selects as the pinned
deployment source in §5 (not a coincidence requiring self-reference:
this phase's own new commits are added *after* this commit and do not
touch `src/pcae/**`, so binding the entering commit introduces no
circularity — see §5's rationale).

## 2. Reconstruction of the 7B AMEND Election (Independently Re-Verified)

```
$ pcae decision-session status CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af --json
```

Confirmed fields, byte-for-byte against the phase document and against
this phase's own fresh CLI query:

- `session_id`: `CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af`
- `session_state`: `Confirmed`
- `human_selection_id`: `amend` (not `approve`, not `decline`)
- `options_presented`: `["approve", "decline", "amend"]`
- `owner_identity`: `Atila Madai`
- `subject_ref`: names the Dell explicitly by `hac-dell /
  atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334`
- `human_rationale_text` (verbatim, unedited): the four-item AMEND
  rationale quoted in full in 149O.20L.7B §8.
- `human_conditions_text` (verbatim, unedited): restates "AMEND, not
  APPROVE. Boundary P remains NOT AUTHORIZED. No CHGR to be published
  for this election," the same four amendment items (a)-(d), and the
  full preservation/exclusion list.
- `readiness_package_status`: `pending` (never published as a CHGR).

**The four requested amendments, verified present verbatim in
`human_rationale_text`/`human_conditions_text`, and treated as the
exclusive scope of this phase:**

1. Bind the exact PCAE source commit SHA to be cloned and installed
   (Action 6).
2. Bind the exact forward, read-back, rollback, and rollback-
   verification commands for all nine actions, immutable by
   proposition content.
3. Bind the exact launch-wrapper content and environment contract
   (Action 8).
4. Clarify that `/opt/pcae/projects/<repo-slug>/repo` is a future
   per-repository path template, not standing authority to create
   arbitrary repositories during initial Dell provisioning.

No unrelated amendment is added. No amendment is dropped.

## 3. What Remains Frozen (Preserved Unless Directly Contradicted)

Re-confirmed unchanged from 149O.20L.7A §26/§34 and 149O.20L.7B §7,
each independently re-checked this phase (§4):

- **Target:** `hac-dell` / `192.168.192.200`, hostname
  `atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334`,
  Dell Inc. Latitude E5470, Ubuntu 24.04.3 LTS, amd64.
- **Principal model (Model 1):** `codex` = existing admin/provisioning
  channel (sudo, no new account); `pcae` = new deployment/execution
  principal, `nologin`, no sudo, no admin, no unrelated group
  membership, no SSH login surface. No second `pcae-deploy` OS account.
  PCAE development remains exclusively on the Mac.
- **Product model:** one repository ⇄ one independently governed PCAE
  project. Centralized multi-repository/company governance remains
  explicitly deferred (§13 below).
- **Nine-action structure:** preserved, same order, same dependency
  shape — see §9. One narrow, disclosed correction is required to
  Action 9's own success-condition text (not its structure/order/
  privilege) — see §14; this is not a contradiction of the
  nine-action *structure* itself, which is otherwise unchanged.

No contradiction requiring a structural redesign was found (§14 is a
success-criterion correction internal to Action 9's own verification
step, not a change to the nine-action graph, its order, its privilege
classification, or its count).

## 4. Minimal Live Dell Reconfirmation (Read-Only, This Phase)

```
$ ssh -o BatchMode=yes -o ConnectTimeout=8 hac-dell \
    "echo CONNECTED as \$(whoami); cat /etc/machine-id; hostname; \
     . /etc/os-release; echo \"\$PRETTY_NAME\"; dpkg --print-architecture"
CONNECTED as codex
54ff22ce400b475aa0d55cb68f4a3334
atila-Latitude-E5470
Ubuntu 24.04.3 LTS
amd64
```

Matches §3 exactly. Material-drift check (read-only, this phase):

```
$ getent passwd pcae         → exit 2 (not found)
$ getent group pcae          → exit 2 (not found)
$ getent passwd pcae-deploy  → exit 2 (not found)
$ ls -ld /opt/pcae /etc/pcae /var/lib/pcae /var/log/pcae
    → all "No such file or directory"
$ sudo -n -l → codex still holds (ALL:ALL) NOPASSWD:ALL
$ command -v git; git --version   → /usr/bin/git, git version 2.43.0
$ command -v python3; python3 --version → /usr/bin/python3, Python 3.12.3
$ python3 -m pip --version        → No module named pip (still absent)
$ python3 -m venv --help          → succeeds (module present)
$ ls -ld /home/pcae               → No such file or directory
```

Contract versions independently re-read this phase from
`docs/contracts/`: HBDC-001 **v1.0** (unchanged), HMIC-001 **v1.3**
(unchanged), HMRC-001 **v1.1** (unchanged) — identical to 149O.20L.7A/
7B's own citations. **No material drift found. The proposition below
supersedes 149O.20L.7A §34 with the same target, same principals, same
topology, and the four amendments materialized — nothing else changed.**

## 5. Amendment 1 — Pinned Source Commit SHA (Critical)

**Bound value:**

```
7a3fa971304521cdcb44251e07ef1966baec686a
```

Full, immutable, 40-character Git commit SHA. Not `HEAD`, not `main`,
not `origin/main`, not a short SHA, not "commit at execution time."

**Rationale — why this exact commit is the deployment source
boundary:**

- It is this phase's own **entering commit** (§1) — the commit already
  current in this repository, on `origin/main`, before this phase's own
  documentation/governance commits are made. It contains the complete
  production implementation and contracts being authorized: HBDC-001
  v1.0, HMIC-001 v1.3, HMRC-001 v1.1, and
  `src/pcae/core/hatp_class_b_conformance.py`,
  `hatp_class_b_topology_verifier.py`,
  `hatp_environment_lock_verifier.py`, `hatp_bootstrap.py` — verified
  present at this exact commit, independently, this phase (§7).
- **Avoiding self-reference:** this phase's *own* documentation/test/
  governance commits (this file, its companion test, `PROJECT_STATUS.md`,
  `CHANGELOG.md`, task-lifecycle files) are added *after*
  `7a3fa971304521cdcb44251e07ef1966baec686a` and do not modify
  `src/pcae/**`, `scripts/**`, or `docs/contracts/**` (verified in §18).
  Binding the entering commit therefore does not require this document
  to embed its own future SHA — the deployment source boundary is fixed
  *before* this document exists, and this document's own governance
  trail is provably outside the bound source tree.
- **Confirmed already pushed and immutable:**
  `git merge-base --is-ancestor 7a3fa971304521cdcb44251e07ef1966baec686a
  origin/main` succeeds — this commit is `origin/main`'s own tip,
  already on the remote, not a local-only or rewritable ref.
- No later commit is required to be bound "as well" — later
  documentation/governance-only commits (this phase's own, and any
  future phase's) may occur after this pinned commit without
  invalidating it, provided they do not modify the bound deployable
  source/contracts (§6).

## 6. Source-Drift / Invalidation Rule (Frozen)

Execution authority derived from this proposition (once a future
APPROVE election occurs) is **invalidated** by any post-binding change
to:

- `src/pcae/**`
- Deployment-affecting scripts (`scripts/**` where they affect
  install/deploy behavior)
- HBDC/HMIC/HMRC contract documents (`docs/contracts/HATP_CLASS_B_
  DEPLOYMENT_CONTRACT.md`, `docs/contracts/HATP_MANDATORY_INDEPENDENT_
  VERIFICATION_CERTIFICATION_CONTRACT.md`, `docs/contracts/HATP_
  MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`)
- The Class-B verifier implementation (`hatp_class_b_conformance.py`,
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
  verifier.py`) or `hatp_bootstrap.py`
- Runtime/install behavior actually exercised by Actions 6-9 below

...**unless** separately reconciled by a new proposition-amendment or
re-binding phase before execution. Ordinary phase-report/documentation/
task-lifecycle commits that do not touch the paths above are **not**
treated as source drift and do not invalidate this binding — e.g. this
very phase's own commits (doc, test, `PROJECT_STATUS.md`, `CHANGELOG.md`,
task files) do not invalidate it, because none of them touch the listed
paths (§18).

## 7. Pinned Commit Availability — Verified (Read-Only)

```
$ git rev-parse origin/main
7a3fa971304521cdcb44251e07ef1966baec686a
$ git merge-base --is-ancestor 7a3fa971304521cdcb44251e07ef1966baec686a origin/main && echo ANCESTOR
ANCESTOR
$ git branch -r --contains 7a3fa971304521cdcb44251e07ef1966baec686a
  origin/HEAD -> origin/main
  origin/main
$ git cat-file -e 7a3fa971304521cdcb44251e07ef1966baec686a:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md && echo PRESENT
PRESENT
$ git cat-file -e 7a3fa971304521cdcb44251e07ef1966baec686a:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md && echo PRESENT
PRESENT
$ git cat-file -e 7a3fa971304521cdcb44251e07ef1966baec686a:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md && echo PRESENT
PRESENT
$ git cat-file -e 7a3fa971304521cdcb44251e07ef1966baec686a:src/pcae/core/hatp_class_b_conformance.py && echo PRESENT
PRESENT
$ git show 7a3fa971304521cdcb44251e07ef1966baec686a:src/pcae/core/hatp_class_b_conformance.py | grep -n 'def verify_class_b_deployment_conformance'
135:def verify_class_b_deployment_conformance(
```

Exists locally, exists in `origin`'s own history (it *is* `origin/
main`'s tip), contains the expected production files, contains HBDC-001
v1.0 / HMIC-001 v1.3 / HMRC-001 v1.1, and contains the Class-B verifier
implementation. No push or new source revision was created to satisfy
this section.

## 8. Source Retrieval Semantics — Freezing Action 6 Against Moving-Ref Ambiguity

Action 6 (§9) is structured so that "clone `main` today" can never
silently mean "whatever `main` contains later":

1. `git clone --no-checkout` (no working tree materialized from a
   branch tip at all — nothing to be "the wrong revision" yet).
2. `git checkout --detach <exact 40-char SHA>` — detached HEAD at the
   exact pinned commit; no local branch is created that could later be
   fast-forwarded to a newer `main`.
3. **Exact read-back required before Action 6 is considered complete:**
   `git rev-parse HEAD` must equal
   `7a3fa971304521cdcb44251e07ef1966baec686a` **exactly** (full 40-char
   string compare, not a prefix match), and `git symbolic-ref -q HEAD`
   must fail (confirms detached, not on a branch).

## 9. Amendment 2 — Exact Command Plan For All Nine Actions (Critical)

Dependency shape unchanged from 149O.20L.7A §27: Action 2 is the sole
prerequisite for Actions 4-8; Action 1 is a prerequisite only for
Action 7; Action 9 depends on all of 2-8. Every command below is
literal — the only parameterized value anywhere is the future
per-repository slug (§13), which is **not exercised** by any action
below.

Idempotency classes used throughout: **ABSENT → CREATE**, **EXACTLY
SATISFIED → NO-OP**, **CONFLICTING → STOP** (§11).

---

### Action 1 — Install Python venv/pip support packages

**Preflight (read-only):**
```
dpkg-query -W -f='${Status}\n' python3-venv 2>&1
dpkg-query -W -f='${Status}\n' python3-pip 2>&1
```
- Both report `install ok installed` → **EXACTLY SATISFIED**: this
  action becomes an idempotent no-op; skip the forward command below
  entirely; proceed directly to read-back.
- Either is absent/not-installed → **ABSENT**: run the forward command.

**Forward (only if ABSENT):**
```
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```
Privilege: root (`sudo`, via `codex`).

**Read-back (always, both branches):**
```
dpkg-query -W -f='${Status}\n' python3-venv → install ok installed
dpkg-query -W -f='${Status}\n' python3-pip  → install ok installed
python3 -m pip --version   → succeeds (exit 0)
python3 -m venv --help     → succeeds (exit 0)
```

**Rollback — only if this action's own forward command ran (i.e., only
if the packages were ABSENT before this action; never if EXACTLY
SATISFIED, since PCAE did not install a package that was already
present):**
```
sudo apt-get remove -y -s python3-venv python3-pip
```
(`-s` = simulate.) If the simulated removal plan names **only**
`python3-venv` and `python3-pip` as `Remv` targets, proceed:
```
sudo apt-get remove -y python3-venv python3-pip
```
If the simulated plan names *any other* package (a reverse dependency),
**STOP** — do not remove; disclose to the operator that automatic
package rollback is unsafe here and requires manual adjudication. This
is the disclosed, honest limit on package-rollback reversibility (no
fabricated "always safe" claim).

**Rollback verification (if rollback executed):**
```
dpkg-query -W -f='${Status}\n' python3-venv python3-pip 2>&1 | grep -c 'install ok installed' → 0
```

---

### Action 2 — Create `pcae` group and principal

**Preflight (read-only):**
```
getent group pcae ; echo "group_exit=$?"
getent passwd pcae ; echo "passwd_exit=$?"
```
- Both exit non-zero (not found) → **ABSENT**: proceed to forward.
- Either exit zero (exists) → **CONFLICTING → STOP.** No reuse, no
  silent adoption, regardless of whether the existing account's
  properties happen to match — HBDC-REQ-001/002 requires a freshly
  OS-issued identity, never hand-picked or reused. There is no
  "EXACTLY SATISFIED" idempotent case for this action by design.

**Forward:**
```
sudo groupadd pcae
sudo useradd -m -g pcae -s /usr/sbin/nologin -c "PCAE agent principal" pcae
```
Privilege: root (`sudo`).

**Read-back:**
```
id pcae
```
Expected: `uid=<fresh>(pcae) gid=<fresh>(pcae) groups=<fresh>(pcae)` —
primary and *only* group is `pcae`; no `sudo`, no `devbots`, no other
group membership.
```
getent passwd pcae | cut -d: -f7   → /usr/sbin/nologin
```

**Rollback — safe only if no later action (3-9) has yet run against
this host in the current execution attempt:**
```
sudo userdel -r pcae
sudo groupdel pcae
```
Unsafe once Actions 3-8 have created resources owned by `pcae`'s uid/
gid — in that case, roll back 8→7→6→5→4→3 first (§11), or stop and
require manual adjudication if any of those individually fail to roll
back cleanly.

**Rollback verification:**
```
getent passwd pcae ; echo $?   → non-zero
getent group pcae  ; echo $?   → non-zero
```

---

### Action 3 — Create Protected Root

**Preflight (read-only):**
```
test -e /etc/pcae ; echo $?
```
- Non-zero (absent) → **ABSENT**: proceed to forward.
- Zero (exists) →
  ```
  stat -c '%U:%G %a' /etc/pcae/hatp/trust-store 2>&1
  ```
  If it exactly equals `root:pcae 750` and `getfacl -p
  /etc/pcae/hatp/trust-store` shows only the three standard POSIX
  entries and the directory is empty → **EXACTLY SATISFIED → NO-OP**.
  Otherwise → **CONFLICTING → STOP.**
- Ancestor-chain re-check (must repeat live, not rely on this
  document's snapshot): `/` and `/etc` both `root:root 0755`, no ACL
  entries beyond the three standard POSIX ones.

**Forward (only if ABSENT):**
```
sudo mkdir -p /etc/pcae/hatp/trust-store
sudo chown root:pcae /etc/pcae/hatp/trust-store
sudo chmod 0750 /etc/pcae/hatp/trust-store
```
Privilege: root (`sudo`). `mkdir -p` also creates the `/etc/pcae` and
`/etc/pcae/hatp` parent directories with default `root:root 0755`
(system umask) — no additional chown/chmod is applied to those parents;
their default mode already satisfies HBDC-REQ-017's ancestor-chain-
safety requirement (§4, re-confirmed live) with zero extra
configuration.

**Read-back:**
```
stat -c '%U:%G %a' /etc/pcae/hatp/trust-store   → root:pcae 750
stat -c '%U:%G %a' /etc/pcae/hatp               → root:root 755
stat -c '%U:%G %a' /etc/pcae                    → root:root 755
getfacl -p /etc/pcae/hatp/trust-store           → only the 3 standard POSIX entries
```

**Rollback — safe only if this action itself created all three of
`/etc/pcae`, `/etc/pcae/hatp`, and `/etc/pcae/hatp/trust-store` (i.e.
preflight found `/etc/pcae` fully absent), and nothing has since been
written into the trust store (no HATP certification/binding activity —
out of scope for this proposition entirely):**
```
sudo rmdir /etc/pcae/hatp/trust-store
sudo rmdir /etc/pcae/hatp
sudo rmdir /etc/pcae
```
`rmdir` (never `rm -rf`) — fails loudly and leaves the directory intact
if non-empty, which is the correct fail-closed behavior if unexpected
content appeared.

**Rollback verification:**
```
test -e /etc/pcae ; echo $?   → non-zero
```

---

### Action 4 — Create runtime/project/state directory tree

**Preflight (read-only):**
```
for p in /opt/pcae /var/lib/pcae /var/log/pcae; do test -e "$p"; echo "$p:$?"; done
```
- All absent → **ABSENT**: proceed to forward.
- All exist with exactly `root:pcae 0750` on every one of the eight
  paths below, each empty except pre-created by this same idempotent
  action → **EXACTLY SATISFIED → NO-OP**.
- Any other partial/mismatched state → **CONFLICTING → STOP.**

**Forward (only if ABSENT), explicit per-path — no recursive glob
chown over unrelated trees:**
```
sudo mkdir -p /opt/pcae/runtime/src /opt/pcae/runtime/venv /opt/pcae/runtime/bin /opt/pcae/projects /var/lib/pcae /var/log/pcae
sudo chown root:pcae /opt/pcae /opt/pcae/runtime /opt/pcae/runtime/src /opt/pcae/runtime/venv /opt/pcae/runtime/bin /opt/pcae/projects /var/lib/pcae /var/log/pcae
sudo chmod 0750 /opt/pcae /opt/pcae/runtime /opt/pcae/runtime/src /opt/pcae/runtime/venv /opt/pcae/runtime/bin /opt/pcae/projects /var/lib/pcae /var/log/pcae
```
Privilege: root (`sudo`). Note: `/opt/pcae/projects` itself is created
`root:pcae 0750` here (an infrastructure container, matching L.7A §26);
no repository-specific subdirectory under it is created by this or any
other action (§13).

**Read-back:**
```
for p in /opt/pcae /opt/pcae/runtime /opt/pcae/runtime/src /opt/pcae/runtime/venv /opt/pcae/runtime/bin /opt/pcae/projects /var/lib/pcae /var/log/pcae; do
  stat -c "%n %U:%G %a" "$p"
done
```
Every line printed by the loop must read: the directory's own name,
followed by `root:pcae 750`.

**Rollback — safe only while every one of the eight directories is
still empty (i.e. Actions 6-8 have not yet populated `src`/`venv`/
`bin`):**
```
sudo rmdir /opt/pcae/runtime/src /opt/pcae/runtime/venv /opt/pcae/runtime/bin /opt/pcae/runtime /opt/pcae/projects /opt/pcae /var/lib/pcae /var/log/pcae
```
`rmdir` only — if Actions 6/7/8 already populated `src`/`venv`/`bin`,
`rmdir` fails loudly by construction; that failure is the correct STOP
signal requiring manual adjudication, not a trigger for `rm -rf`.

**Rollback verification:**
```
test -e /opt/pcae ; echo $?          → non-zero
test -e /var/lib/pcae ; echo $?      → non-zero
test -e /var/log/pcae ; echo $?      → non-zero
```

---

### Action 5 — Normalize `pcae`'s own home directory

**Preflight:** Action 2 complete (home already created by `useradd -m`).
```
stat -c '%U:%G %a' /home/pcae
```

**Forward (idempotent by construction — same commands whether or not
`useradd -m` already set this correctly):**
```
sudo chown pcae:pcae /home/pcae
sudo chmod 0750 /home/pcae
```
Privilege: root (`sudo`).

**Read-back:**
```
stat -c '%U:%G %a' /home/pcae   → pcae:pcae 750
```

**Rollback:** n/a — `/home/pcae` is removed by Action 2's own rollback
(`userdel -r`), not independently here.

**Rollback verification:** n/a.

---

### Action 6 — Clone canonical PCAE source at the pinned commit

**Preflight (read-only):**
```
test -d /opt/pcae/runtime/src ; echo $?
sudo find /opt/pcae/runtime/src -mindepth 1 -maxdepth 1 2>&1
```
- Directory exists (from Action 4) and is empty → **ABSENT** (of a
  checkout): proceed to forward.
- Directory already contains a checkout whose `git rev-parse HEAD`
  equals `7a3fa971304521cdcb44251e07ef1966baec686a` exactly, whose
  `git remote get-url origin` equals
  `git@github.com:atimad/pcae-harness.git`, and whose `git status
  --short` is empty → **EXACTLY SATISFIED → NO-OP.**
- Directory non-empty and not matching the above exactly → **CONFLICTING
  → STOP.**

**Forward (only if ABSENT):**
```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;
```
Privilege: root (`sudo`). Precondition: Action 4 complete.

**Secret boundary (disclosed, no secret embedded):** cloning
`git@github.com:atimad/pcae-harness.git` over SSH requires a
deploy-capable SSH key readable by the invoking (`root`/`codex`-sudo)
process. This proposition does not name, provision, or embed that key
or its filesystem location — key provisioning is a separate admin-
channel concern, out of scope here, exactly as `codex`'s own existing
key material (§6 of 149O.20L.7A) was never provisioned by any PCAE
phase.

**Read-back:**
```
git -C /opt/pcae/runtime/src rev-parse HEAD
    → must equal 7a3fa971304521cdcb44251e07ef1966baec686a EXACTLY (full 40-char compare)
git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    → non-zero (detached HEAD, not on a branch)
git -C /opt/pcae/runtime/src status --short
    → empty (no local modifications)
git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
test -f /opt/pcae/runtime/src/docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md ; echo $?
    → 0
test -f /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_conformance.py ; echo $?
    → 0
```

**Rollback — restore Action 4's empty-directory postcondition (safe
unless Action 7/8 already depend on this checkout, in which case roll
back 8→7 first):**
```
sudo rm -rf /opt/pcae/runtime/src
sudo mkdir -p /opt/pcae/runtime/src
sudo chown root:pcae /opt/pcae/runtime/src
sudo chmod 0750 /opt/pcae/runtime/src
```
This `rm -rf` targets exactly one explicit, non-glob, already-owned-by-
this-action path — not a broad or wildcarded removal.

**Rollback verification:**
```
sudo find /opt/pcae/runtime/src -mindepth 1 | wc -l   → 0
stat -c '%U:%G %a' /opt/pcae/runtime/src               → root:pcae 750
```

---

### Action 7 — Create production venv and editable-install PCAE

**Preflight:** Actions 1 and 6 complete.
```
test -d /opt/pcae/runtime/venv ; echo $?
sudo find /opt/pcae/runtime/venv -mindepth 1 -maxdepth 1 2>&1
```
- Empty → **ABSENT**: proceed to forward.
- Already contains a venv whose `bin/pcae --version` succeeds (run as
  `pcae`) and whose editable-install target resolves to
  `/opt/pcae/runtime/src` (§ read-back below) → **EXACTLY SATISFIED →
  NO-OP.**
- Anything else → **CONFLICTING → STOP.**

**Forward (only if ABSENT):**
```
sudo python3 -m venv /opt/pcae/runtime/venv
sudo /opt/pcae/runtime/venv/bin/pip install --no-cache-dir -e /opt/pcae/runtime/src
sudo chown -R root:pcae /opt/pcae/runtime/venv
sudo find /opt/pcae/runtime/venv -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/venv -type f -exec chmod 0640 {} \;
sudo find /opt/pcae/runtime/venv/bin -maxdepth 1 -type f -exec chmod 0750 {} \;
```
Privilege: root (`sudo`).

**Editable-install / environment-lock reconciliation (HBDC-REQ-025-
039):** the `pcae` *package identity* resolves strictly to the pinned
checkout at `/opt/pcae/runtime/src` (PEP 660 editable install,
confirmed via `direct_url.json`'s `editable: true` — the same check
`_check_model_a_deployment()` in `hatp_class_b_conformance.py`
performs). This is the environment-lock-relevant binding. Ordinary
third-party dependency versions resolve normally from PyPI per the
pinned checkout's own `pyproject.toml` at install time — this is the
same mechanism already used for the Mac's own development venv and is
not a new release/packaging model.

**Read-back:**
```
sudo -u pcae /opt/pcae/runtime/venv/bin/pcae --version
    → succeeds
sudo -u pcae test -w /opt/pcae/runtime/venv ; echo $?
    → non-zero (agent cannot write)
cat /opt/pcae/runtime/venv/lib/python3.12/site-packages/__editable__.pcae*.pth 2>/dev/null \
  || cat /opt/pcae/runtime/venv/lib/python3.12/site-packages/*.pth
    → references /opt/pcae/runtime/src
```

**Rollback — restore Action 4's empty-directory postcondition (safe
unless Action 8 already depends on it):**
```
sudo rm -rf /opt/pcae/runtime/venv
sudo mkdir -p /opt/pcae/runtime/venv
sudo chown root:pcae /opt/pcae/runtime/venv
sudo chmod 0750 /opt/pcae/runtime/venv
```

**Rollback verification:**
```
sudo find /opt/pcae/runtime/venv -mindepth 1 | wc -l   → 0
stat -c '%U:%G %a' /opt/pcae/runtime/venv                → root:pcae 750
```

---

### Action 8 — Create and lock the launch wrapper

See §12 for the exact wrapper script bytes, digest, and environment
contract. Wrapper path: `/opt/pcae/runtime/bin/pcae-launch`.

**Preflight:**
```
test -e /opt/pcae/runtime/bin/pcae-launch ; echo $?
```
- Absent → **ABSENT**: proceed to forward.
- Exists with `sha256sum` exactly matching
  `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`
  and `stat` exactly `root:pcae 750` → **EXACTLY SATISFIED → NO-OP.**
- Exists with any other content/owner/mode → **CONFLICTING → STOP** —
  never silently overwrite.

**Forward (only if ABSENT):** exact command in §12.

**Read-back:**
```
sha256sum /opt/pcae/runtime/bin/pcae-launch
    → b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
stat -c '%U:%G %a' /opt/pcae/runtime/bin/pcae-launch
    → root:pcae 750
sudo -u pcae test -w /opt/pcae/runtime/bin/pcae-launch ; echo $?
    → non-zero (agent cannot write)
sudo -u pcae /opt/pcae/runtime/bin/pcae-launch --version
    → succeeds
```

**Rollback — always safe (single leaf file, nothing depends on it
going forward except the read-only Action 9):**
```
sudo rm /opt/pcae/runtime/bin/pcae-launch
```

**Rollback verification:**
```
test -e /opt/pcae/runtime/bin/pcae-launch ; echo $?   → non-zero
```

---

### Action 9 — Final local conformance check (read-only)

**Command (run as `pcae`, using the deployed production venv only):**
```
sudo -u pcae /opt/pcae/runtime/bin/pcae-launch health
sudo -u pcae env -i HOME=/home/pcae PATH=/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c "
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
result = verify_class_b_deployment_conformance()
print(result.status.value)
for c in result.checks:
    print(c.check_id, c.satisfied, c.status)
"
```
Run from a working directory under `/opt/pcae/runtime/src` (the
deployed checkout) so `verify_class_b_deployment_conformance()`'s
default `root=HarnessPath.cwd()` resolves there — never invoked from
the Mac, never invoked as `codex` or `root`, never invoked against any
other checkout.

Privilege: none beyond `pcae`'s own (strictly read-only — confirmed by
source inspection, §14).

**Expected postcondition:** none (read-only).

**Expected result — corrected per the finding in §14:** individual
checks HBDC-REQ-022 (Model-A editable install), the topology checks,
and the environment-lock checks are each expected `satisfied: True`
given Actions 1-8 completed correctly; HBDC-REQ-042 (deployment-
identity binding) is expected `satisfied: False`
(`no_active_deployment_binding_matches_repository_and_root` or
`no_repository_identity_present`), because no `DeploymentBinding` is
created by this or any other action in this graph — that is a
separate, later, repository-onboarding-scoped step (§13), not part of
infrastructure provisioning. Aggregate `.status` is therefore expected
`NON_COMPLIANT`, driven **only** by HBDC-REQ-042 — **not** `COMPLIANT`.
If any *other* check unexpectedly fails (topology, environment-lock, or
Model-A), or if the reported failing set is not exactly `{HBDC-REQ-042}`,
**STOP** and require manual adjudication — that would indicate Actions
1-8 did not provision correctly, which is exactly the scenario this
read-only check exists to catch.

**Rollback:** n/a — read-only, no mutation, nothing to roll back
(§11).

---

## 10. Privilege Map

| # | Action | Execution identity | Root/sudo required | Mutation target | No-op case | Rollback authority |
|---|---|---|---|---|---|---|
| 1 | apt packages | `codex` via `sudo` | Yes | `python3-venv`, `python3-pip` dpkg state | Both already installed | Conditional (simulate-checked) |
| 2 | `pcae` group/user | `codex` via `sudo` | Yes | `/etc/passwd`, `/etc/group`, `/home/pcae` | None — always CREATE or STOP | Safe only pre-Action-3 |
| 3 | Protected Root | `codex` via `sudo` | Yes | `/etc/pcae/hatp/trust-store` | Exact prior match | Safe (rmdir, empty-only) |
| 4 | Runtime/state tree | `codex` via `sudo` | Yes | `/opt/pcae/**`, `/var/lib/pcae`, `/var/log/pcae` | Exact prior match | Safe while empty |
| 5 | Home normalize | `codex` via `sudo` | Yes | `/home/pcae` mode/owner | Idempotent always | n/a (Action 2's) |
| 6 | Source checkout | `codex` via `sudo` | Yes | `/opt/pcae/runtime/src` | Exact SHA/remote match | Safe (recreate empty) |
| 7 | venv + install | `codex` via `sudo` | Yes | `/opt/pcae/runtime/venv` | Exact install match | Safe (recreate empty) |
| 8 | Launch wrapper | `codex` via `sudo` | Yes | `/opt/pcae/runtime/bin/pcae-launch` | Exact digest match | Always safe (rm) |
| 9 | Verifier check | `pcae` (no sudo) | No | none (read-only) | n/a — always runs | n/a |

Only `codex` (via already-audited, pre-existing `sudo`) provides
administrative privilege at any point. `pcae` itself receives no sudo
authority, no `authorized_keys`, no interactive shell (§3).

## 11. Idempotency Classes, Before-State Capture, Failure and Rollback Semantics (Generic Rules)

**Idempotency classes** (applied per-action in §9): **ABSENT → CREATE**;
**EXACTLY SATISFIED → NO-OP**; **CONFLICTING → STOP.** No action
silently repairs a CONFLICTING pre-existing state.

**Before-state capture:** the future execution phase must capture
fresh before-state evidence immediately before Action 1 — package
presence, user/group presence, target path existence/metadata/ACLs,
existing `git`/`python3`/`pip` state, `/home/pcae` absence, `sudo -n -l`
posture — re-run live, not inherited from this document's own §4
snapshot, which is preflight evidence only and will be stale by
execution time.

**Sequence (per action):** inspect → compare against expected
idempotency class → mutate only if `ABSENT` → read back → verify
against the exact expected result in §9 → continue only on exact match.

**Stop conditions (any of):** a precondition mismatch; a command
failure; a read-back mismatch; an unexpected (`CONFLICTING`) resource;
an unexpected owner/mode/ACL; a source digest/commit mismatch (Action
6); a verifier result outside the exact expected set (Action 9, §14);
`apt-get remove -y -s` naming an unexpected package (Action 1
rollback). **No unreviewed remediation follows a STOP** — the future
execution phase must halt and report to the operator.

**Rollback order:** reverse dependency order, but **only for actions
that actually performed a mutation and have a safe frozen rollback** —
not a mechanical 9→1 sweep. Action 9 is read-only and therefore
ordinarily has **nothing to roll back**, ever (clarified explicitly,
per the governing instruction's own §32). If Action 1 was a no-op
(`EXACTLY SATISFIED`), it is skipped in the rollback sweep as well —
there is nothing PCAE mutated to undo.

**Rollback failure:** if a rollback command itself fails (e.g. a
process still runs as `pcae`, blocking `userdel`), **stop; do not
force** (`userdel -f`, `rm -rf` beyond the specific documented path);
report for manual adjudication — mirrors HBDC-001's own fail-closed
posture.

## 12. Amendment 3 — Exact Launch-Wrapper Script Content and Environment Contract (Critical)

**Path:** `/opt/pcae/runtime/bin/pcae-launch` — `root:pcae`, mode
`0750`, executable.

**Exact literal script content (9 lines, 188 bytes, no trailing
whitespace on any line, single trailing newline):**

```sh
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

**Content digest (SHA-256 of the exact bytes above):**
```
b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
```

**Environment semantics — explicit, not "no PYTHONPATH":**

- `PYTHONPATH`: **unset** (`unset PYTHONPATH`) — not set to empty, not
  left as inherited from the caller's environment; removed from the
  process environment entirely before `exec`.
- `PYTHONNOUSERSITE`: set to `1` and exported — disables Python's
  per-user `site-packages` (`~/.local/lib/...`) from ever being
  consulted, regardless of `pcae`'s own `$HOME`.
- `PATH`: reassigned to the fixed literal
  `/usr/bin:/bin:/usr/sbin:/sbin` and exported — this is where `git`
  (§17 of 149O.20L.7A) and system Python live; it deliberately excludes
  any agent-writable directory, `/opt/pcae/runtime/venv/bin` itself, or
  any per-user path.
- Working directory: `cd /opt/pcae/runtime` — a `root:pcae 0750`
  directory the `pcae` principal cannot write to (§9 Action 4
  read-back), before the final `exec`.
- `exec /opt/pcae/runtime/venv/bin/pcae "$@"`: replaces the wrapper's
  own shell process (no leftover parent shell); forwards all arguments
  unmodified; runs the pinned venv's own `pcae` entry point exclusively
  — never a system-installed `pcae`, never a different checkout.
- `set -eu`: the wrapper itself fails closed on any unset-variable
  reference or any of its own internal command failures, before ever
  reaching `exec`.
- The wrapper sources **no** developer shell profile, no
  `~/.bashrc`/`~/.profile`, no activation script, and no unrelated
  project environment file — it is a fixed, self-contained `/bin/sh`
  script with no `source`/`.` directive anywhere in it.

## 13. Wrapper Trust Boundary

- Owner: `root`. Group: `pcae`. Mode: `0750` (owner rwx, group r-x,
  other none — `pcae` may read/execute, never write).
- ACL expectation: no extra ACL entries beyond the three standard POSIX
  ones (verified via `getfacl -p`, same discipline as §3/§9 Action 3).
- Ancestor requirement: `/opt/pcae/runtime/bin` itself is `root:pcae
  0750` (§9 Action 4) — `pcae` cannot rename, replace, or delete the
  wrapper file even though it can execute it (directory write is
  required to unlink/replace a file; `pcae` has no write on the parent).
- `sudo -u pcae test -w /opt/pcae/runtime/bin/pcae-launch` must fail
  (§9 Action 8 read-back) — the deployment principal cannot mutate the
  root-owned wrapper/runtime authority files, satisfying HBDC's
  agent-cannot-write-authority-bearing-state property.

## 14. Finding — Action 9's Success-Condition Text Requires Correction (Disclosed, Not Silently Redesigned)

Independent inspection of `verify_class_b_deployment_conformance()`
this phase (`src/pcae/core/hatp_class_b_conformance.py:135` and
`_check_deployment_identity()` above it) found:

> `_check_deployment_identity()`'s own docstring: "On a host with no
> provisioned `DeploymentBinding` (the expected current state, per
> phase entry baseline), this reports `NON_COMPLIANT`, never
> `COMPLIANT` by default."

Actions 1-8 above (infrastructure provisioning only) never create a
`DeploymentBinding` — binding a specific governed repository to this
host is explicitly a separate, later, per-repository onboarding
operation (§13 of this document / §23-25 of the governing instruction),
deliberately out of scope for initial Dell infrastructure provisioning.
Consequently, **`verify_class_b_deployment_conformance()` run at the
end of Actions 1-8, rooted at `/opt/pcae/runtime/src`, is expected to
report `NON_COMPLIANT` — driven specifically and only by HBDC-REQ-042 —
never `COMPLIANT`,** as a direct, documented, intended consequence of
this action graph's own scope boundary. This is not a production code
defect (the code behaves exactly as its own docstring says it should);
it is a correction owed to 149O.20L.7A §27 Action 9's and this
governing instruction's own §21/§22 prose, which stated Action 9's
success condition as "exact-identity `COMPLIANT` required... any other
status: STOP" without accounting for HBDC-REQ-042's deployment-binding
requirement.

**Materiality:** this is exactly the kind of "one of the commands
cannot truthfully implement [the stated result]" contradiction the
governing instruction's §3 anticipates — but it is narrowly scoped to
Action 9's own *expected result text*, not to the nine-action
structure, order, count, or privilege classification, all of which are
unaffected and preserved. Per the same governing instruction's own
practice elsewhere (e.g. 149O.20L.7A §22-23's verifier-locality
disclosure), the correct response is **honest disclosure and a
corrected expected-result text (§9 Action 9, above)**, not a silent
redesign of the action graph, not fabricating an achievable `COMPLIANT`
result, and not halting this entire materialization phase over a
scope-boundary fact that was always true of this design. **No
`src/pcae/**` change is proposed or required** — the verifier's
behavior is correct; only this proposition's own prose is corrected.

**Consequence for a future execution phase:** full Class-B `COMPLIANT`
status (all of HBDC-REQ-022/042 plus topology/environment-lock)
requires a subsequent, separately-authorized repository-onboarding/
`DeploymentBinding`-creation phase, after this infrastructure
provisioning — not invented, designed, or authorized by this document.
This is now explicit, frozen proposition content rather than an
implicit gap.

## 15. Amendment 4 — Per-Repository Path Template Scope Clarification

`/opt/pcae/projects/<repo-slug>/repo` is **not** a literal
initial-provisioning path. Normatively, for this and any future
proposition inheriting this text:

- `<repo-slug>` is a future per-repository parameter, supplied **only**
  when a specific repository is separately onboarded/governed in its
  own later, separately authorized phase.
- Initial Dell infrastructure provisioning (this proposition, Actions
  1-9) authorizes creation **only** of the shared project-root
  container `/opt/pcae/projects` itself (§9 Action 4) — exactly the
  path named in 149O.20L.7A §12/§26, no deeper.
- It does **not** authorize creation of: arbitrary repository
  directories under `/opt/pcae/projects/`; arbitrary clones; arbitrary
  repo-slugs; project-specific `.pcae/` state; project-specific task
  artifacts. None of Actions 1-9 above create any path deeper than
  `/opt/pcae/projects` itself.
- Each governed repository remains an independently governed PCAE
  project (§16 below) — this clarification forecloses any future
  reading of the path template as standing authority to create
  repositories beyond the one (if any) named at a future, separate
  election.

## 16. Repository-Onboarding Boundary

Explicitly distinguished:

- **Dell infrastructure provisioning** — this Boundary-P proposition,
  Actions 1-9. Creates the shared `pcae` principal, Protected Root,
  runtime install, and empty `/opt/pcae/projects` container only.
- **Repository onboarding** — a future, separate operation applying
  PCAE to one named repository (`cd <project-repo> && pcae init`,
  confirmed against the live CLI in 149O.20L.7A §21), which also
  creates that repository's own `DeploymentBinding` (§14). Not
  authorized, not scheduled, not performed by this document.

No future repository mutation is smuggled into this infrastructure
authorization.

## 17. Per-Repository Product Model (Preserved)

Preserved unchanged: **one repository → one independently governed
PCAE project.** Each repository will carry its own governed `.pcae/`
state, task lifecycle, and phase-report history, exactly as this
Mac-hosted `pcae-harness` repository does today. The shared Dell
runtime (`/opt/pcae/runtime`) is a deployment convenience — it does
**not** make project governance centralized.

## 18. Centralized Governance — Remains Deferred

Explicitly excluded, unchanged from 149O.20L.7A §14/§32: an
organization-wide repository registry; a central company policy plane;
cross-project scheduling; fleet orchestration; cross-project authority
aggregation; an enterprise dashboard/control plane. All remain future,
undesigned, unimplemented work.

## 19. Full Literal Revised Proposition — DRAFT — NOT AUTHORIZED

> **DRAFT — NOT AUTHORIZED.** This is a complete, revised draft of the
> Boundary-P proposition for a future 149O.20L.7B-style election
> phase, superseding 149O.20L.7A §34 in full. It has no governance
> force until independently elected via a fresh `pcae decision-session`
> → `pcae governance-record publish` in that future phase.
>
> - **Target host:** `hac-dell` / `192.168.192.200`, hostname
>   `atila-Latitude-E5470`, machine-id
>   `54ff22ce400b475aa0d55cb68f4a3334`, Dell Inc. Latitude E5470, Ubuntu
>   24.04.3 LTS, amd64. Reconfirmed live, read-only, this phase (§4) —
>   no drift since 149O.20L.7A/7B.
> - **Deployment (agent) principal / group:** `pcae` / `pcae` (new,
>   freshly OS-issued, `nologin`, no login surface, no sudo, no
>   unrelated group membership).
> - **Admin channel:** existing `codex` account via `sudo` (no new
>   admin OS account).
> - **Paths:** exactly as frozen in 149O.20L.7A §26 (Protected Root
>   `/etc/pcae/hatp/trust-store`; runtime install `/opt/pcae/runtime`
>   with `src`/`venv`/`bin`; per-repository project root
>   `/opt/pcae/projects/<repo-slug>/repo`, future-template-only per §15
>   above; non-repo-scoped state `/var/lib/pcae`; logs `/var/log/pcae`).
> - **Source binding:** Model A only — pinned-commit `git clone` of
>   `git@github.com:atimad/pcae-harness.git` at commit
>   `7a3fa971304521cdcb44251e07ef1966baec686a` into
>   `/opt/pcae/runtime/src` (§5-§8), editable-installed into
>   `/opt/pcae/runtime/venv` (§9 Action 7). Source-drift invalidation
>   rule frozen at §6.
> - **Contracts:** HBDC-001 v1.0, HMIC-001 v1.3, HMRC-001 v1.1 —
>   re-verified unchanged this phase (§4/§7); a future election phase
>   must re-verify once more immediately before voting.
> - **Action graph:** exactly the nine actions in §9 above, in the
>   stated order, each gated on its own exact literal read-back before
>   the next proceeds, each idempotency-classed per §11, with Action
>   9's corrected expected result per §14.
> - **Privileged operations:** exactly per §10's privilege map — Actions
>   1-8 require root/sudo via the existing `codex` channel; Action 9
>   requires no privilege.
> - **Launch wrapper:** exact content, digest, and environment contract
>   per §12-13.
> - **Rollback semantics:** exactly per §9 (per-action) and §11
>   (generic rules).
> - **Repository-onboarding boundary:** exactly per §15-17 —
>   infrastructure provisioning only; no repository is created, cloned,
>   or bound by this proposition.
> - **Exclusions:** no SSH login surface for `pcae`; no modification of
>   `atila`/`uosserver`/`clawdbot` accounts or data; no centralized
>   multi-repository control plane (§18); no Boundary C (HMIC
>   certification) or Boundary A (`HATP_MANDATORY` activation) in scope
>   — those remain separate, later, separately authorized phases; no
>   full Class-B `COMPLIANT` claim at the end of this action graph
>   (§14) — that requires a later, separate repository-onboarding/
>   binding phase.
> - **Migration implications:** unchanged from 149O.20L.7A §15 — a
>   future hardware replacement requires fresh provisioning, fresh
>   `DeploymentBinding`, fresh HMIC certification; accepted, not
>   designed away.
>
> **This proposition is a draft only. Boundary P is NOT AUTHORIZED by
> this document. No election has occurred. This document does not
> authorize provisioning.**

## 20. Proposition Integrity — Digest Binding (Existing Mechanism Reused)

No new authority artifact or parallel digest machinery is invented.
Per the existing `pcae decision-session` design (already used
identically in 149O.20L.7B §9 step 2, where the entering-commit hash
was `--declare`d as evidence), the future election phase's own
`pcae decision-session evidence <session-id> --declare` step must cite:

1. This document's own Git blob reference once committed — i.e. the
   commit hash of the commit that introduces
   `docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_
   AMENDMENT.md` (recorded in §23's governance section below once that
   commit exists), which is immutable once pushed.
2. The pinned deployment source SHA (§5):
   `7a3fa971304521cdcb44251e07ef1966baec686a`.
3. The wrapper content digest (§12):
   `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`.

The `pcae decision-session preview` step's own `preview_digest`
mechanism (already exercised in 149O.20L.7B §9 step 4) then
independently binds the exact subject/rationale/conditions text of that
future election to this exact evidence set — no separate hashing
utility is introduced by this phase.

## 21. No Election This Phase

`pcae decision-session` **create/select/confirm/readiness** were **not**
invoked this phase. No new election was held. No CHGR was published or
drafted. The existing `CDS-cf123bbf-a5d7-4f0f-ac22-0baa257990af` session
(§2) is preserved exactly as `Confirmed`/`amend`, not reinterpreted,
not transformed into an APPROVE session, not consumed as authority for
anything in this document.

## 22. Historical Mac CHGR — Unchanged

`chgr-d4343fa51b9743f3abaeb87a881a78b1` was not read, modified, or cited
as authority this phase beyond the directory-listing confirmation in
§23 that it remains the only `chgr-*.json` on record. It names
`Atilas-MacBook-Pro.local`, not the Dell, and never authorizes the
Dell. Unchanged.

## 23. Production/Contracts Scope — Proof

```
$ git status --short (post phase-doc/test authoring, pre-commit)
$ git diff --name-only HEAD
```
Only `docs/PHASE_149O_20L_7B_1_*.md`,
`tests/test_phase_149o_20l_7b_1_*.py`, `PROJECT_STATUS.md`,
`CHANGELOG.md`, `tasks/**`, `.pcae/phase-completion-*` changed by this
phase's own commits — confirmed at phase close (§25). Zero
`src/pcae/**`, `docs/contracts/**`, or `scripts/**` paths touched. No
`src/pcae/**` code change was needed to produce a truthful proposition
— the one finding (§14) is a proposition-prose correction, not a code
defect requiring repair.

## 24. Dell Mutation Prohibition — Proof

Every command run against the Dell this phase (§4) was read-only:
`whoami`, `cat /etc/machine-id`, `hostname`, `/etc/os-release` sourcing,
`dpkg --print-architecture`, `getent passwd`/`getent group` × 3, `ls
-ld` against four non-existent paths and one non-existent home
directory, `sudo -n -l`, `command -v`/`--version` for `git`/`python3`,
`python3 -m pip --version`, `python3 -m venv --help`. No account,
group, key, sudoers entry, directory, package, clone, venv, or service
was created, modified, or removed on the Dell. All command-plan text
in §9 above is proposed-only prose in this document — none of it was
executed against the Dell this phase.

## 25. Companion Tests

`tests/test_phase_149o_20l_7b_1_dell_boundary_p_proposition_
materialization_amendment.py` (§27 lists the full assertion set). Does
not execute any provisioning command and does not attempt live Dell SSH
within routine pytest execution — it asserts against this phase's own
already-materialized document content.

## 26. Boundary Status After This Phase

```
Boundary P: NOT AUTHORIZED — AMENDED PROPOSITION READY FOR FRESH HUMAN ELECTION
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

No Dell provisioning authority exists. No election occurred. No CHGR
was published. This phase's output is a revised draft proposition
only.

## 27. Governance

```
$ pcae check           → passed
$ pcae health           → healthy
$ pcae status coherence → coherent
$ pcae doctor task-memory → warnings (pre-existing, unrelated, not remediated here)
```
Fresh, dedicated `Phase 149O.20L.7B.1: ...` task used throughout (not a
reused idle placeholder — `pcae task transition --next "Phase
149O.20L.7B.1: ..."` was run at phase start). No raw `git commit`/
`push` used — all commits via `pcae commit`/`pcae phase complete`/
`pcae push`. No lifecycle bypass, no `--no-verify`, no force push. No
Dell mutation occurred at any point in this phase (§24). No election
was held (§21). No CHGR was published (§21-22).

## 28. Phase Verdict

```
DELL TARGET: SELECTED — PREFLIGHTED — MATERIALIZED PROPOSITION READY
DELL BOUNDARY P: NOT AUTHORIZED — AMENDED PROPOSITION READY FOR FRESH HUMAN ELECTION
CLASS-B: NOT PROVISIONED
BOUNDARY C: NOT AUTHORIZED
BOUNDARY A: NOT AUTHORIZED
HATP: NOT READY
RUNTIME: Observed / observe / unavailable
AMENDMENT 1 (pinned source SHA): MATERIALIZED — 7a3fa971304521cdcb44251e07ef1966baec686a
AMENDMENT 2 (exact per-action commands): MATERIALIZED — all nine actions, §9
AMENDMENT 3 (exact launch-wrapper content): MATERIALIZED — §12, digest b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
AMENDMENT 4 (repo-slug scope clarification): MATERIALIZED — §15-17
FINDING: Action 9 success-condition text corrected (HBDC-REQ-042 disclosure, §14) — no src/pcae/** change required
NO DELL MUTATION OCCURRED
NO NEW ELECTION HELD
NO NEW CHGR PUBLISHED
HISTORICAL MAC CHGR UNCHANGED, NOT REUSED
RECOMMENDED NEXT PHASE: 149O.20L.7B.2 — Dell Class-B Boundary-P Authorization Record Re-Capture
```

## 29. Recommended Next Phase

**Phase 149O.20L.7B.2 — Dell Class-B Boundary-P Authorization Record
Re-Capture.** Must, without provisioning: reconstruct this phase's
revised proposition (§19) exactly; reconfirm Dell identity/freshness
live, read-only, once more; present the complete materialized
proposition (including §14's Action 9 finding) to the human governance
authority; obtain a new, explicit APPROVE/DECLINE/AMEND election via
`pcae decision-session`, citing the digest bindings in §20 as
`--declare`d evidence; publish a Dell CHGR only if the canonical
workflow and the election outcome permit (i.e., only on a concluded
APPROVE or DECLINE, mirroring 149O.20L.7B's own withheld-publication
reasoning for AMEND outcomes); perform no provisioning at any point.
After any future APPROVE publication, independent authorization
verification must still occur before any Dell mutation, and a
subsequent, separately authorized execution phase — not this one, not
7B.2 — performs Actions 1-9.
