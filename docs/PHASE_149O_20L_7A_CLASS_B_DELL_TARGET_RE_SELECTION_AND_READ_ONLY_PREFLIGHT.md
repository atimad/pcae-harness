# Phase 149O.20L.7A — Class-B Dell Target Re-Selection & Read-Only Preflight

## 0. Phase Identity and Type

**Phase:** 149O.20L.7A
**Type:** PLANNING / PREFLIGHT. Read-only against the Dell. No provisioning.
No CHGR published. This document, its companion test file, and ordinary
task/lifecycle/report bookkeeping are the only artifacts this phase
produces.
**Basis:** Phase 149O.20L.7 §8 (this phase's own predecessor-defined
mandate); `docs/PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_
AUTHORIZATION_AND_PLANNING.md`; `docs/PHASE_149O_20L_5A_CLASS_B_
PROVISIONING_TARGET_ENVIRONMENT_SELECTION_AND_PREFLIGHT.md`; `docs/
PHASE_149O_20L_6_CLASS_B_PROVISIONING_AUTHORIZATION_RECORD_CAPTURE.md`;
`docs/PHASE_149O_20L_6A_CLASS_B_PROVISIONING_AUTHORIZATION_RECORD_
INDEPENDENT_VERIFICATION.md`; `docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md` (HBDC-001 v1.0); `docs/contracts/HATP_MANDATORY_INDEPENDENT_
VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001 v1.3); `docs/contracts/
HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001 v1.1); live
inspection of `src/pcae/core/hatp_class_b_conformance.py`,
`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
`hatp_bootstrap.py`; a live, first legitimate, read-only SSH session to
the Dell (`hac-dell`, `192.168.192.200`) conducted this phase.

## 1. Entering State (Independently Reconfirmed)

```
$ git status --short                → (clean)
$ git status --branch --short       → ## main...origin/main
$ git log --oneline origin/main..HEAD → (empty)
$ git rev-list --count origin/main..HEAD → 0
```

- `pcae health`: healthy. Required PCAE files: all present. Policy
  validation: valid. Agent lock: held by `claude-local`. Session
  continuity: verified. Git status: clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing, historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase by many prior phases. Unrelated to Dell target re-selection;
  outside this phase's allowed-file scope; not remediated here.
- `pcae push check`: clean (`nothing_to_push`), task memory warnings
  noted (same pre-existing set), lifecycle review missing (routine),
  phase report trust/identity both passed.
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: 149O.20L.7's canonical report,
  consistent; recommended next phase names this phase (149O.20L.7A).
- `pcae phase-report reconcile --phase-id 149O.20L.7`: `status:
  reconciled`, `mutation: none (inspection only)`.

Entering authority state, reconfirmed at this phase's own entry:

```
Boundary P: NOT AUTHORIZED (chgr-d4343fa51b9743f3abaeb87a881a78b1 remains
            the only CHGR on record; it is a valid, unrevoked, Mac-target
            record and is not authority for the Dell — see §2)
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

## 2. Historical Mac CHGR — Disposition (Retained, Not Reused)

`chgr-d4343fa51b9743f3abaeb87a881a78b1` at
`.pcae/publication-execution/records/chgr-d4343fa51b9743f3abaeb87a881a78b1.json`
was independently re-inspected this phase. It is unchanged from L.7's
own §2/§6 findings: `lifecycle_state: published`, `selected_option_id:
approve`, no `revocation_ref`/`superseded_by`/`deprecated_by` field,
`decision_subject` names `Atilas-MacBook-Pro.local` specifically, and
`conditions` names L.5A §18's material-drift invalidation rule against
itself. This phase does not create, edit, revoke, or supersede it. It
remains on record as a real, valid, historical Mac-target Boundary-P
election — evidence, not authority for anything this phase does.

## 3. Dell Now Explicitly In Scope

Phase 149O.20L.7 recorded the human governance authority's explicit
instruction changing the deployment target from the Mac to the Dell
Ubuntu host, previously excluded by name in L.5A §3/§6 as "unrelated."
That exclusion is superseded for this phase by that same instruction.
`hac-windows` (`192.168.192.104`) remains unrelated and out of scope —
not probed, not connected to, this phase.

## 4. First Dell SSH Connection

A read-only SSH connection to the Dell was made this phase — the first
one made under this governed line of work. It used the pre-existing
`~/.ssh/config` entry `Host hac-dell` (`HostName 192.168.192.200`, `User
codex`, `IdentityFile ~/.ssh/id_ed25519_hac_dell`), an already-existing
account and key, both created prior to this phase (key file dated
2026-07-27, well before this phase). The key was passphrase-protected;
the operator loaded it into their own `ssh-agent` in their own terminal
session at the operator's own initiative, and this phase's SSH calls
used the already-agent-loaded key — the passphrase itself was never
seen, requested, or handled by this phase. No account, group, SSH key,
or sudoers entry was created on the Dell by this phase.

```
$ ssh -o BatchMode=yes -o ConnectTimeout=8 hac-dell "echo CONNECTED as \$(whoami)"
CONNECTED as codex
```

## 5. Actual Host Identity

Captured read-only, directly from the Dell:

```
$ hostname
atila-Latitude-E5470
$ hostname -f
atila-Latitude-E5470
$ uname -a
Linux atila-Latitude-E5470 7.0.0-28-generic #28~24.04.1-Ubuntu SMP
PREEMPT_DYNAMIC Wed Jul 1 15:50:57 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
$ hostnamectl
 Static hostname: atila-Latitude-E5470
Machine ID: 54ff22ce400b475aa0d55cb68f4a3334
Boot ID: d7937938cfa44a2db39dc4ff67edb647
Hardware Vendor: Dell Inc.
Hardware Model: Latitude E5470
Architecture: x86-64
$ dpkg --print-architecture
amd64
```

**Host identity, independent of IP/hostname (per §5 instruction not to
rely solely on `192.168.192.200`):** Dell Inc. Latitude E5470 laptop,
`/etc/machine-id` = `54ff22ce400b475aa0d55cb68f4a3334`, Ubuntu 24.04.3
LTS (Noble Numbat), kernel `7.0.0-28-generic`, amd64. The machine-id is
the durable, host-specific identity value this phase recommends binding
any future `DeploymentBinding` to (see §15/§25).

## 6. Actual Operator/SSH Account Identity

```
$ id
uid=1003(codex) gid=1003(codex) groups=1003(codex),27(sudo),100(users)
$ whoami
codex
$ groups
codex sudo users
$ getent passwd codex
codex:x:1003:1003:codex,,,:/home/codex:/bin/bash
```

`codex` (uid 1003) is an already-existing account, a member of the
`sudo` group, with:

```
$ sudo -n -l
User codex may run the following commands on atila-Latitude-E5470:
    (ALL : ALL) ALL
    (ALL : ALL) NOPASSWD: ALL
```

`codex` therefore has unrestricted, passwordless sudo — sufficient
privilege for every later provisioning action in §16's proposed action
graph. `codex` is used this phase strictly as the read-only inspection
and (in a future phase) admin-invocation channel — it is **not** the
proposed PCAE agent principal (see §9). Login history (`last -n 20`)
shows `codex` and `atila` as the two accounts actively used
interactively on this host; `codex` itself already appears to be used
for other work on this Dell (SSH sessions from `192.168.192.104`/
`192.168.192.81` over several weeks) — this reinforces that a
*separate*, dedicated, unprivileged `pcae` identity is required rather
than running PCAE's agent automation as `codex` itself.

## 7. Sudo/Privilege Availability (Read-Only)

Confirmed via `sudo -n -l` above (no mutating command run). `codex`
holds `(ALL : ALL) NOPASSWD: ALL`, which is sufficient, read-only
confirmed, to later perform: user/group creation, directory creation,
ownership/mode changes, package installation, and service-unit
installation. No sudoers file was read, edited, or probed beyond the
non-mutating `-n -l` listing.

## 8. Existing Principals — Collision Check

```
$ getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 {print}'
atila:x:1000:1000:Atila Madai:/home/atila:/bin/bash
uosserver:x:1001:1001::/home/uosserver:/bin/sh
codex:x:1003:1003:codex,,,:/home/codex:/bin/bash

$ getent group | awk -F: '$3 >= 1000 {print}'
atila:x:1000:
uosserver:x:1001:atila
devbots:x:1002:atila,clawdbot
codex:x:1003:

$ getent passwd pcae        → exit 2 (not found)
$ getent passwd pcae-deploy  → exit 2 (not found)
$ getent group pcae         → exit 2 (not found)
$ getent group pcae-deploy   → exit 2 (not found)

$ getent passwd clawdbot
clawdbot:x:995:983::/home/clawdbot:/usr/sbin/nologin

$ ls -la /home/
drwxr-x--- 23 atila     atila     .../atila
drwxr-x---  6 clawdbot  clawdbot  .../clawdbot
drwxr-x--- 26 codex     codex     .../codex
drwxr-x---  6 uosserver uosserver .../uosserver
```

No name collision for `pcae` or `pcae-deploy` at either user or group
level. Four other principals already exist on this host (`atila` —
owner/primary account, uid 1000; `uosserver` — separate service
account, uid 1001; `codex` — this session's account, uid 1003;
`clawdbot` — a `nologin` service account, uid/gid 995/983) plus a shared
`devbots` group (`atila`, `clawdbot`). Each home directory is mode
`0750`, owner-only-readable — confirmed isolated:

```
$ ls -la /home/atila
ls: cannot open directory '/home/atila': Permission denied   (as codex, no sudo used)
```

This host is shared with other work under separate Unix accounts, per
the human's own L.7 instruction — the isolation finding above is direct
evidence that ordinary POSIX permissions already keep those accounts'
data out of `codex`'s (and would keep it out of a future `pcae`'s)
reach without any additional configuration.

## 9. Deployment-Principal Architecture — Decision

**Model 1 chosen: a single new dedicated Ubuntu identity, `pcae`,
created as the HBDC *agent* principal.** No second new
`pcae-deploy`-style OS account is proposed.

Reasoning: HBDC-001 §7 (HBDC-REQ-001–005) requires exactly two
*distinct* OS principals — an agent principal (execution authority
only, no write authority over Protected Root/HMIC records/
DeploymentBinding/hardware-credential registry/Cutover Record/
environment-lock) and an admin principal (write authority over exactly
those resources, HBDC-REQ-009/010). §9 of this contract explicitly
frames the admin role in v1 as a "combined human-approver/bootstrap-
admin role" — i.e., HBDC does not require a second *persistent
unprivileged* OS account to serve as admin; it requires that admin
write-authority be exercised distinctly from agent execution authority.
That distinction is already fully satisfied by `codex`'s existing,
already-audited, sudo-gated channel (§7) acting as admin during
provisioning/certification, versus `pcae` (created with no sudo
membership) acting as agent at runtime. Inventing a second persistent
`pcae-deploy` identity would duplicate a role the operator's own account
already fills, with no additional isolation benefit identified — per
this phase's own instruction, Model 2 is adopted "only if the
requirements establish a real authority/security benefit," and none was
found. `pcae` is created strictly as a **deployment/execution** identity
— not a second "development" account; PCAE source development remains
exclusively on the Mac (`~/repos/pcae-harness`), per the human's own
standing instruction.

Ownership pattern that follows from this (detailed fully in §16):
Protected Root, the PCAE runtime install, and the production venv are
**root-owned**, group `pcae`, mode `0750` — `pcae` gets read/execute via
group membership (satisfying HBDC §8's "agent may read/execute/
inspect") but never write (satisfying HBDC-REQ-006–008's "agent SHALL
NOT write authority-bearing state"). Per-repository governed-repo
workspaces (§13) are **`pcae`-owned**, full read-write — ordinary
governed-repository content is not itself HBDC "authority-bearing
state," and normal PCAE agent operation (committing, editing, running
`pcae` subcommands inside a governed repo) requires write access there.

## 10. SSH Model — Decision

**No direct SSH login for `pcae`.** `pcae` is created with shell
`/usr/sbin/nologin` (or equivalent) and no `authorized_keys` file — it
is never an SSH login target. The operator continues to reach the Dell
through the already-existing, already-proven `codex` account (§4/§6),
and switches context to `pcae` only via `sudo -u pcae <command>` /
`sudo -iu pcae` for actual PCAE execution or inspection. This keeps a
single, already-audited SSH entry point (`sshd` logs on `codex`) rather
than provisioning a second SSH key/account surface, and matches the
Mac plan's own posture of not adding new remote-login surface for the
deployment identity. This model is frozen for the next phase's
proposition (§10 of the phase spec: "Freeze the intended model for
later authorization") — no key or account is created by this phase.

Live-confirmed supporting facts (read-only): `sshd -T` on the Dell
reports `pubkeyauthentication yes`, `passwordauthentication yes`,
`permitrootlogin without-password` — password auth is currently enabled
host-wide (an existing host-level posture, unrelated to and unchanged
by this phase; noted here only because a future hardening phase for
this host, if ever in scope, would need to consider it — out of scope
for PCAE's own deployment identity either way, since `pcae` gets no
login method at all under this model).

## 11. Existing Development Projects — Isolation Findings

Per the human's own instruction, this phase did **not** inspect the
*content* of `atila`'s, `uosserver`'s, or `clawdbot`'s home directories
or work — only enough to prove separation exists. Findings:

- `codex` cannot read `/home/atila`, `/home/uosserver`, or
  `/home/clawdbot` (permission denied, no sudo invoked to bypass this).
- All candidate PCAE deployment ancestor paths (`/`, `/etc`, `/opt`,
  `/srv`, `/var/lib`) are root-owned, mode `0755`, and confirmed
  (`test -w`) **not** writable by `codex` without sudo — i.e. not
  writable by any of the other unprivileged accounts either, since none
  of them have broader privilege than `codex` was shown to have by
  default membership (`sudo` membership is `atila`, `codex` — see §8;
  `uosserver` and `clawdbot` are not in the `sudo` group and hold no
  elevated privilege over these paths).
- No existing file or directory anywhere probed (`/opt`, `/srv`,
  `/var/lib`, `/var/log`, `/etc`) is `pcae`-named or otherwise
  PCAE-related — a completely clean namespace to provision into.
- `atila` **is** in the `sudo` group (confirmed via `getent group
  sudo` → `sudo:x:27:atila,codex`) and is therefore also capable of
  administering PCAE's resources if `atila` is the human operator's own
  account on this machine — this is expected and consistent with §7
  ("Admin ... combined human-approver ... role"), not an isolation
  violation; sudo-capable accounts are, by definition, capable of admin
  actions across the host, which is exactly why HBDC treats "admin
  authority" as a role fulfilled by the operator's own privileged
  channel rather than a filesystem-permission boundary.

Conclusion: the Dell being shared with `atila`'s/`uosserver`'s/
`clawdbot`'s other work is acceptable — PCAE's deployment boundary
(`pcae`-owned or root-owned/`pcae`-group resources under `/opt/pcae`,
`/etc/pcae`, `/var/lib/pcae`, `/var/log/pcae`) is fully isolable from
all of them using ordinary POSIX ownership/mode, with no observed
pre-existing condition that would compromise that isolation.

## 12. Filesystem Topology — Candidate Locations Inspected

Read-only, no path created:

```
/opt        drwxr-xr-x root root   (exists)
/srv        drwxr-xr-x root root   (exists)
/var/lib    drwxr-xr-x root root   (exists)
/var/log    drwxr-xr-x root syslog (exists)
/etc/pcae         → does not exist
/opt/pcae         → does not exist
/srv/pcae         → does not exist
/var/lib/pcae     → does not exist
/var/log/pcae     → does not exist
/               ext4, /dev/nvme0n1p6, 394G total, 320G available
```

`getfacl -p /opt` and `getfacl -p /etc` both show only the three
standard POSIX entries (`user::rwx`, `group::r-x`, `other::r-x`) — no
extra ACL entries on either ancestor. `getfacl`/`setfacl` (`acl`
package) are both installed (`getfacl 2.3.2`); the root filesystem is
`ext4` with default Ubuntu 24.04 ACL support enabled (POSIX ACLs work
out of the box on `ext4` since kernel default `acl` mount behavior —
confirmed functionally by `getfacl` succeeding, not merely by mount
options).

Mapping candidate roots to HBDC resource types:

| Path prefix | HBDC resource type | Chosen? |
|---|---|---|
| `/etc/pcae/hatp/trust-store` | Protected Root (fixed by code resolver, §14) | Yes — no choice |
| `/opt/pcae/runtime` | Canonical deployment root / Model-A install (HBDC-REQ-022-024) | Yes |
| `/opt/pcae/projects/<slug>/repo` | Per-repository governed workspace | Yes |
| `/var/lib/pcae` | Non-repo-scoped authority-bearing state (hardware-credential registry, DeploymentBinding records) | Yes |
| `/var/log/pcae` | Launcher/service logs | Yes |
| `/srv/pcae` | (not used) | No — `/srv` is conventionally for service-served data; nothing PCAE provisions is served content, so `/opt` (add-on software) and `/var/lib` (persistent state) are the better FHS fit. |

## 13. Per-Repository Layout — Consumption Model Frozen

Preserving the current live product model (each governed repository is
an independently governed PCAE project — exactly as `~/repos/
pcae-harness` on the Mac carries its own `.pcae/` directory today):

```
/opt/pcae/runtime/                  (shared, root-owned, group pcae, r-x)
├── src/                            canonical Model-A checkout (pinned commit)
├── venv/                           production Python venv (Model-A editable install)
└── bin/pcae-launch                 launch wrapper (env-lock enforcement)

/etc/pcae/hatp/trust-store/         (shared, root-owned, group pcae, r-x) — Protected Root

/var/lib/pcae/                      (shared, root-owned, group pcae, r-x)
└── hardware-credential-registry/, deployment-bindings/   (non-repo-scoped authority state)

/var/log/pcae/                      (shared, root-owned, group pcae, r-x)

/opt/pcae/projects/                 (pcae-owned, rwx — agent working area)
├── pcae-harness/
│   ├── repo/                       git checkout of this governed repository
│   │   └── .pcae/                  per-repository PCAE project/governance state (as today)
│   └── venv/                       (only if a project needs deps beyond the shared runtime venv — not needed for pcae-harness itself, since it *is* the runtime)
└── <future-project-B>/
    ├── repo/
    │   └── .pcae/
    └── venv/  (if required)
```

Shared vs. per-repository vs. per-workspace, per current live
architecture (`pcae init` writes `.pcae/` into the repository it's run
in — confirmed by this session's own `pcae health`/`pcae check`
inspecting `.pcae/` at the pcae-harness repo root, not any shared
location): the PCAE **install/runtime** (interpreter, venv, source) is
shared across all governed repositories on this host; PCAE **governance
state** (`.pcae/`, tasks, phase reports, CHGRs) is strictly
per-repository, living inside each repository's own checkout, exactly
as it does today on the Mac. This phase invents no new capability —
`/opt/pcae/projects/<slug>/venv` per-project override is listed only as
a structural placeholder for a project with different dependencies than
PCAE itself; nothing in current PCAE architecture requires or provides
per-project virtual environments today, so it is not part of this
phase's action graph (§16) and is not claimed as implemented.

## 14. No Accidental Centralization

Explicitly preserved and frozen as the *current* consumption model: one
governed repository ⇄ one independently governed PCAE project
(`.pcae/` state, task lifecycle, phase reports, CHGRs — all
per-repository, as today). A shared runtime install is a deployment
convenience (avoid re-provisioning Python/venv per project), **not** a
step toward centralized cross-repository governance, scheduling, or
policy distribution — those remain explicitly deferred, out of scope,
not designed, not implemented, not hinted at in the action graph below.

## 15. Migration-Aware Design

| Category | Classification | Notes |
|---|---|---|
| PCAE source code (`/opt/pcae/runtime/src`) | Portable | Ordinary git-clonable content; no host binding. |
| Governance record schemas, `.pcae/` per-repo state structure | Portable | Format is host-agnostic. |
| OS principal (`pcae` uid/gid) | Machine-specific | Freshly issued per host by design (HBDC-REQ-001/002 — never hand-picked, never reused across hosts). |
| Protected Root contents (HATP trust store) | Machine-specific | Bound to this host's provisioning act; HBDC-REQ-042-046 treats a host migration as requiring an independent new binding, not a copy. |
| `DeploymentBinding` (repository ⇄ host) | Machine-specific | Must name `54ff22ce400b475aa0d55cb68f4a3334` (this Dell's own `/etc/machine-id`, §5) explicitly; not portable to a future replacement machine. |
| Hardware-credential registry (if/when HATP hardware provider is bound) | Machine-specific | Tied to this host's own hardware. |
| HMIC certification state | Machine-specific | Certifies *this deployment's* frozen implementation identity; a new host requires fresh certification, not a copy. |
| Per-repository `.pcae/` governance history that predates any Dell binding (e.g. this repo's own task/phase history) | Portable | Already git-tracked, host-agnostic; only the *binding record*, not the history, is host-specific. |

Per this phase's own instruction, host-binding is **not** weakened to
ease a future hardware swap. A future replacement machine requires
fresh provisioning (§16's action graph re-run against the new host),
fresh `DeploymentBinding`, and fresh HMIC certification — this is
treated as expected, bounded, one-time migration cost, not a defect to
design away.

## 16. Python Environment (Read-Only Findings)

```
$ command -v python3   → /usr/bin/python3
$ python3 --version    → Python 3.12.3
$ python3 -m site
sys.path = ['/home/codex', '/usr/lib/python312.zip', '/usr/lib/python3.12',
            '/usr/lib/python3.12/lib-dynload',
            '/usr/local/lib/python3.12/dist-packages',
            '/usr/lib/python3/dist-packages']
USER_BASE: '/home/codex/.local' (exists)
USER_SITE: '/home/codex/.local/lib/python3.12/site-packages' (doesn't exist)
ENABLE_USER_SITE: True
$ python3 -m pip --version       → No module named pip
$ python3 -m ensurepip --version → No module named ensurepip
$ find /usr/lib/python3.12 -maxdepth 1 -iname EXTERNALLY-MANAGED → present
$ python3 -m venv --help  → succeeds (venv module itself present)
$ find / -iname sitecustomize.py -o -iname usercustomize.py (maxdepth 6)
  /usr/lib/python3.12/sitecustomize.py
  /etc/python3.12/sitecustomize.py
$ env | grep -i python → (empty; PYTHONPATH unset for codex)
```

**Precondition identified (not present in the Mac plan):** `pip` and
`ensurepip` are not installed system-wide (Ubuntu 24.04 ships them as
separate `python3-pip` packages, and this system does not have it
installed), and the system Python is PEP 668 "externally managed."
`python3 -m venv` itself works. Provisioning must therefore either (a)
`apt-get install python3-venv python3-pip` before creating the
production venv and using its own bundled `pip`, or (b) rely solely on
`python3 -m venv` (which can self-bootstrap `pip` inside the venv via
`ensurepip` if the `python3-venv` apt package, which bundles `ensurepip`
support, is present) — either way, an explicit apt-package step is a
new, Ubuntu-specific precondition action not needed on the Mac
(§17/§27, action 1).

The two existing `sitecustomize.py` files are system-package-owned
(`/usr/lib/...`, `/etc/python3.12/...`), unrelated to any future PCAE
venv's own `site-packages`, and were not modified or read for content
beyond confirming their existence/location.

## 17. Git (Read-Only Findings)

```
$ command -v git   → /usr/bin/git
$ git --version    → git version 2.43.0
$ ls -la /usr/bin/git
-rwxr-xr-x 1 root root 4066232 Jul 2 2025 /usr/bin/git
```

`git` is root-owned, mode `0755` — not writable by `codex` or any
future `pcae` principal without sudo, and resolves from a fixed system
path (`/usr/bin`) that is not ahead of any agent-writable directory in
the default `PATH`. This satisfies HBDC-REQ-038's trusted-executable-
resolution requirement without any provisioning action needed against
`git` itself — the only work required is ensuring the *production
launch wrapper's* own `PATH` places `/usr/bin` (or an equivalent
resolved absolute path) ahead of anything agent-writable, which is
folded into §16's launch-wrapper action.

## 18. ACL Support (Read-Only Findings)

Already reported in §12: `getfacl`/`setfacl` present (`acl` package
2.3.2), functional on this host's `ext4` root filesystem, and the two
ancestor directories inspected (`/opt`, `/etc`) carry no ACL entries
beyond the three standard POSIX ones. This is the "Linux equivalent"
the live Class-B topology verifier's own code already implements
(`_acl_grants_agent_write_linux()`, using `getfacl -p` and POSIX ACL
entry parsing) — confirmed by source inspection this phase, not by
executing the verifier against the Dell (§22).

## 19. Candidate Protected Root

`/etc/pcae/hatp/trust-store` — **not a choice made by this phase**; it
is the fixed constant already present in
`src/pcae/core/hatp_bootstrap.py`'s `_default_production_trust_root()`
(`sys.platform == "linux"` branch), frozen prior to this phase. Live
ancestor-chain inspection this phase (`/`, `/etc`) confirms both are
root-owned, mode `0755`, no ACL entries, not writable by `codex` without
sudo — i.e. already satisfying HBDC-REQ-017's ancestor-chain-safety
requirement for this exact path, with zero remediation needed on the
ancestor chain itself. Required final state once created: owner `root`,
group `pcae`, mode `0750` (owner rwx, group r-x — read/traverse only for
the agent principal — other none). This satisfies HBDC-REQ-013
(admin-owned), HBDC-REQ-014 (mode excludes group/other write, `0750 &
0022 == 0`), HBDC-REQ-015/016 (no ACL grants agent write — none will be
added), and HBDC-REQ-017 (ancestor chain already confirmed safe).

## 20. Deployment Source Model

**Model A only**, per HBDC-REQ-022-024 (already contractually the sole
authorized model — this phase does not re-open that question). The
Dell's `/opt/pcae/runtime/src` is populated by a fresh `git clone` of
the canonical Mac-developed repository (this repository's own `origin`
remote — the same remote this Mac checkout pushes to), checked out at
an explicit pinned commit (the commit current at the time the next
phase's CHGR is drafted), followed by `pip install -e
/opt/pcae/runtime/src` inside the dedicated production venv. This is
the same reproducible mechanism already used for this Mac checkout — no
new release/packaging mechanism is invented. Per this phase's own
boundary (§20/§35 of the governing instruction), **the clone itself is
not performed this phase** — it is listed as action 6 of the deferred
provisioning plan (§16), not executed here; nothing was written to the
Dell's filesystem by this phase.

## 21. Repository-Under-Governance Source Model (Distinct From PCAE's Own Deployment)

Separately from how *PCAE itself* reaches the Dell (§20), a *future
governed project repository* (e.g. a hypothetical `project-B`) is
attached to PCAE the same way any repository is today — confirmed
against the live CLI this session:

```
$ pcae init --help
usage: pcae init [-h] [--dry-run] [--force]
Create PCAE memory files in the current repository.
```

i.e. `cd <project-repo> && pcae init`, using whichever `pcae`
executable is on the invoking shell's `PATH` — for a Dell-hosted
project this would be the production venv's own `pcae` entry point
(`/opt/pcae/runtime/venv/bin/pcae`, reached via the launch wrapper or an
activated venv), not a separately installed copy. No unrelated real
repository was modified or `pcae init`-run against by this phase — this
section is confirmed against this repository's own live `--help` output
only.

## 22. Live Verifier Portability Analysis

`verify_class_b_deployment_conformance()` (`src/pcae/core/
hatp_class_b_conformance.py:135`) takes only an optional `HarnessPath`
repository-root locator — **no host, connection, or credential
parameter exists**. Internally (and in the topology/environment-lock
verifiers it calls) it inspects only the *local calling process's own*
`os.geteuid()`/`os.getgroups()`, local filesystem `stat()`, local `PATH`
environment variable, and local `subprocess.run()` invocations — grep
across all three modules for `ssh`/`paramiko`/`fabric`/`remote_host`
returns zero hits. **It cannot evaluate a remote target by being
invoked from the Mac.** To honestly evaluate the Dell, the verifier
(and, practically, the whole PCAE checkout it's part of) must execute
*as a process running on the Dell itself*.

This phase does **not** fake a Dell result by running the verifier
locally on the Mac and reporting it as Dell's state, and does not run
it on the Dell either (§23).

## 23. Why the Verifier Was Not Run Live Against the Dell This Phase

Running `verify_class_b_deployment_conformance()` on the Dell requires
PCAE's own source to be present on the Dell's filesystem first (§22) —
there is no way to execute it there without placing at least the
`hatp_class_b_conformance.py` module tree (in practice, effectively the
whole `src/pcae/core` package and its imports) onto the target disk.
That is source-materialization on the target host — exactly the "clone
creation" this phase's own governing instruction (§20/§35) reserves for
provisioning, not preflight. This is classified as an **expected
pre-provisioning absence / deployment concern**, not a product
implementation gap: the verifier's local-only design is intentional and
correct (it must inspect the actual live process's own `euid`/
environment/filesystem state, which is only meaningful executed on the
target itself — a remote-abstraction verifier would be inspecting the
wrong process). No separate implementation phase is recommended on this
basis. Consequently, §24's failure inventory below is a **reasoned,
disclosed expectation from the live read-only findings in §5-§21**, not
a measured live verifier result — labeled as such throughout, never
presented as an actual `COMPLIANT`/`NON_COMPLIANT` verifier output.

## 24. Reasoned (Not Measured) HBDC Failure Inventory

| HBDC requirement family | Expected status if verifier ran today | Basis |
|---|---|---|
| §7 Principal Model (REQ-001–005) | FAIL | `pcae` principal does not exist yet (§8). |
| §10-§11 Protected Root (REQ-011–021) | FAIL | `/etc/pcae/hatp/trust-store` does not exist yet (§12/§19). |
| §12 Model-A Deployment (REQ-022–024) | INDETERMINATE | No source present at any canonical root on the Dell yet to classify. |
| §13 Environment Lock (REQ-025–039) | FAIL | No dedicated production venv exists; `pip`/`ensurepip` not yet installed system-wide (§16). |
| §16 Repository/Deployment Identity (REQ-042–046) | FAIL | No `DeploymentBinding` exists for this repository against machine-id `54ff22ce400b475aa0d55cb68f4a3334` (§5/§15). |
| §20 Conformance Vocabulary | N/A — not measured | Verifier not executed this phase (§23); this table is a reasoned expectation, not a live `INDETERMINATE`/`NON_COMPLIANT` call. |

Every row maps to "observation only" or "authorized future mutation" —
none map to "unsupported implementation gap" (§23).

## 25. Ubuntu-Specific Target Eligibility Verdict

Applying L.5A §7's twelve criteria (research-reconstructed verbatim
list), adapted to Linux/Ubuntu, against this Dell:

1. Principal isolation — **satisfiable**: no `pcae`/`pcae-deploy` name
   collision (§8); host already demonstrates working principal
   isolation among four existing accounts (§8/§11).
2. Filesystem ownership isolation — **satisfiable**: clean, unclaimed
   namespace under `/opt`, `/etc`, `/var/lib`, `/var/log` (§12).
3. Protected Root feasibility — **satisfiable**: fixed path already
   resolvable by existing code; ancestor chain already safe (§19).
4. Complete ancestor-chain trust — **confirmed**: `/` and `/etc` both
   root-owned, `0755`, no ACLs, not `codex`-writable (§19).
5. ACL support — **confirmed present**: POSIX ACLs functional, verifier
   already has a Linux ACL code path (§18).
6. Environment-lock feasibility — **satisfiable with precondition**:
   `python3 -m venv` works; `pip`/`ensurepip` require an apt-package
   install first (§16).
7. Model-A Python environment — **satisfiable**: standard `git clone` +
   venv + editable install, no obstruction found (§20).
8. Trusted Git feasibility — **confirmed**: `/usr/bin/git`, root-owned,
   `0755`, fixed `PATH` position (§17).
9. Repository deployment identity — **satisfiable**: stable
   `/etc/machine-id` available to bind a `DeploymentBinding` to (§5/§15).
10. Rollback capability — **satisfiable**: every action in §16's action
    graph targets newly-created resources only (same structural
    property as the Mac plan, §16 dependency notes).
11. Privilege availability — **confirmed**: `codex` holds
    passwordless, unrestricted sudo (§7).
12. No collision with active development workflow — **confirmed clear**:
    other accounts/homes on this host are permission-isolated already;
    no PCAE-named resource exists anywhere probed (§8/§11).

**Verdict: ELIGIBLE WITH PRECONDITIONS.**

Preconditions (all deferred to a future provisioning phase, none
performed here): (a) `apt-get install python3-venv python3-pip` (or
equivalent) before venv creation, since system `pip`/`ensurepip` are
currently absent and the system interpreter is PEP-668
externally-managed; (b) creation of the `pcae` agent principal/group;
(c) creation of the Protected Root and runtime/state directory tree
with the ownership/mode described in §9/§19; (d) a fresh, Dell-specific
CHGR naming this host and its machine-id explicitly (§2/§26/§28).

No criterion above was found INELIGIBLE or "impossible/unsafe without
restructuring" — this is a materially cleaner target than the Mac
plan's Option B was ever documented to be, because it starts from a
namespace with zero pre-existing PCAE-adjacent artifacts to collide
with.

## 26. Concrete Literal Names (Frozen For The Next Proposition)

| Item | Value |
|---|---|
| Target host | `hac-dell` / `192.168.192.200`, hostname `atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334` |
| Deployment (agent) principal | `pcae` (new, uid freshly OS-issued at creation time, no hand-picked uid) |
| Deployment group | `pcae` (new, primary group of `pcae`; also the read-grant group on root-owned protected/runtime resources) |
| Agent shell | `/usr/sbin/nologin` (no interactive/SSH login) |
| Protected Root | `/etc/pcae/hatp/trust-store` (root:pcae, `0750`) — fixed by existing code, not a choice |
| PCAE runtime install root | `/opt/pcae/runtime` (root:pcae, `0750`) |
| PCAE canonical source checkout | `/opt/pcae/runtime/src` (root:pcae, `0750`, pinned-commit `git clone` of this repository's own `origin`) |
| Production venv | `/opt/pcae/runtime/venv` (root:pcae, `0750`) |
| Launch wrapper | `/opt/pcae/runtime/bin/pcae-launch` (root:pcae, `0750`, executable) |
| Per-repository project root | `/opt/pcae/projects/<repo-slug>/repo` (pcae:pcae, `0750`, rw for agent) |
| Non-repo-scoped state | `/var/lib/pcae` (root:pcae, `0750`) |
| Logs | `/var/log/pcae` (root:pcae, `0750`) |
| Admin/provisioning channel | existing `codex` account via `sudo` (no new admin OS account) |

No placeholder remains among these — every value above is exact and
literal, ready for the next phase's proposition.

## 27. Concrete Command Plan (Not Executed — Proposed Only)

Dependency shape: action 2 (`pcae` principal) is the sole prerequisite
for actions 4–8; action 1 (apt packages) is a prerequisite only for
action 7 (venv/pip); action 9 depends on all of 2–8.

**Action 1 — Install Python venv/pip support packages**
- Command: `sudo apt-get update && sudo apt-get install -y python3-venv python3-pip`
- Privilege: root (sudo).
- Precondition: `python3 -m pip --version` fails (confirmed §16).
- Expected mutation: `python3-venv`, `python3-pip` packages installed.
- Read-back: `python3 -m pip --version` succeeds.
- Rollback: `sudo apt-get remove -y python3-venv python3-pip` (safe — no
  dependent PCAE resource created yet at this point in the sequence).
- Rollback verification: `dpkg -l | grep -E 'python3-venv|python3-pip'`
  returns nothing.

**Action 2 — Create `pcae` group and principal**
- Commands: `sudo groupadd pcae` then `sudo useradd -m -g pcae -s
  /usr/sbin/nologin -c "PCAE agent principal" pcae`
- Privilege: root (sudo).
- Precondition: §8's collision check (no `pcae` user/group exists) —
  must be re-confirmed live immediately before this action in the
  actual provisioning phase, not assumed from this phase's snapshot.
- Expected mutation: new group `pcae` (fresh gid); new user `pcae`
  (fresh uid), primary group `pcae`, home `/home/pcae`, shell
  `/usr/sbin/nologin`, no `sudo`/`devbots`/other group membership.
- Read-back: `id pcae`.
- Rollback: `sudo userdel -r pcae && sudo groupdel pcae` — safe only if
  no later action has yet created a resource owned by `pcae`'s uid/gid;
  not safe once actions 4–8 have run (see failure semantics, §29).
- Rollback verification: `getent passwd pcae` / `getent group pcae`
  both fail.

**Action 3 — Create Protected Root**
- Commands: `sudo mkdir -p /etc/pcae/hatp/trust-store && sudo chown
  root:pcae /etc/pcae/hatp/trust-store && sudo chmod 0750
  /etc/pcae/hatp/trust-store`
- Privilege: root (sudo).
- Precondition: action 2 complete; path confirmed absent (§12).
- Expected mutation: directory exists, `root:pcae`, mode `0750`.
- Read-back: `stat -c '%U:%G %a' /etc/pcae/hatp/trust-store` →
  `root:pcae 750`; `getfacl -p` shows no extra ACL entries.
- Rollback: `sudo rmdir /etc/pcae/hatp/trust-store` (and `/etc/pcae/hatp`,
  `/etc/pcae` if this action also created those parent directories and
  nothing else uses them) — safe, nothing references it yet.
- Rollback verification: path absent.

**Action 4 — Create runtime/project/state directory tree**
- Commands: `sudo mkdir -p /opt/pcae/runtime/{src,venv,bin}
  /opt/pcae/projects /var/lib/pcae /var/log/pcae && sudo chown -R
  root:pcae /opt/pcae /var/lib/pcae /var/log/pcae && sudo chmod 0750
  /opt/pcae /opt/pcae/runtime /opt/pcae/projects /var/lib/pcae
  /var/log/pcae`
- Privilege: root (sudo).
- Precondition: action 2 complete; paths confirmed absent (§12).
- Expected mutation: directory tree exists as specified, `root:pcae`,
  mode `0750` on each directory listed.
- Read-back: `stat -c '%U:%G %a'` on each created directory.
- Rollback: `sudo rm -rf /opt/pcae /var/lib/pcae /var/log/pcae` — safe
  if action 6/7 (source/venv) have not yet populated it with anything
  the agent depends on at runtime; unsafe after activation.
- Rollback verification: paths absent.

**Action 5 — Set `pcae`'s own home directory to a safe, minimal state**
- Command: `sudo chmod 0750 /home/pcae && sudo chown pcae:pcae /home/pcae`
- Privilege: root (sudo).
- Precondition: action 2 complete (home already created by `useradd -m`).
- Expected mutation: mode/owner confirmed/normalized (idempotent if
  `useradd -m` already set this correctly).
- Read-back: `stat -c '%U:%G %a' /home/pcae`.
- Rollback: n/a (covered by action 2's own rollback).
- Rollback verification: n/a.

**Action 6 — Clone canonical PCAE source at a pinned commit**
- Command: `sudo git clone --branch main <origin-url> /opt/pcae/runtime/src
  && sudo git -C /opt/pcae/runtime/src checkout <pinned-commit-sha> &&
  sudo chown -R root:pcae /opt/pcae/runtime/src && sudo find
  /opt/pcae/runtime/src -type d -exec chmod 0750 {} \; && sudo find
  /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;`
- Privilege: root (sudo).
- Precondition: action 4 complete; `<origin-url>`/`<pinned-commit-sha>`
  supplied explicitly by the phase that authorizes this action (not
  invented by this phase — no placeholder is carried forward
  un-filled, but the *value itself* is necessarily time-of-execution,
  since it must be the commit current when that phase runs).
- Expected mutation: working tree at the pinned commit, `root:pcae`
  ownership, no world access.
- Read-back: `git -C /opt/pcae/runtime/src rev-parse HEAD` matches
  `<pinned-commit-sha>`; `git -C ... status --short` empty.
- Rollback: `sudo rm -rf /opt/pcae/runtime/src`.
- Rollback verification: path absent.

**Action 7 — Create production venv and editable-install PCAE**
- Command: `sudo python3 -m venv /opt/pcae/runtime/venv && sudo
  /opt/pcae/runtime/venv/bin/pip install -e /opt/pcae/runtime/src &&
  sudo chown -R root:pcae /opt/pcae/runtime/venv && sudo find
  /opt/pcae/runtime/venv -type d -exec chmod 0750 {} \; && sudo find
  /opt/pcae/runtime/venv -type f -exec chmod 0640 {} \; && sudo chmod
  0750 /opt/pcae/runtime/venv/bin/*`
- Privilege: root (sudo).
- Precondition: actions 1 and 6 complete.
- Expected mutation: venv exists at the given path, editable install of
  `/opt/pcae/runtime/src` present, `root:pcae`, no world/agent-write
  access, executables retain `0750` (group-execute for `pcae`).
- Read-back: `/opt/pcae/runtime/venv/bin/pcae --version` (run as
  `pcae`, via `sudo -u pcae`) succeeds; `sudo -u pcae test -w
  /opt/pcae/runtime/venv` fails (confirms agent-unwritable).
- Rollback: `sudo rm -rf /opt/pcae/runtime/venv`.
- Rollback verification: path absent.

**Action 8 — Create and lock the launch wrapper**
- Command: write `/opt/pcae/runtime/bin/pcae-launch` (root-owned,
  `0750`, group `pcae`) — a shell script that: unsets `PYTHONPATH`,
  sets `PYTHONNOUSERSITE=1`, sets an explicit `PATH` beginning with
  `/usr/bin` (where `git` resolves, §17) ahead of anything
  agent-writable, `cd`s to an explicit non-agent-writable working
  directory, then `exec`s `/opt/pcae/runtime/venv/bin/pcae "$@"`.
- Privilege: root (sudo) to write/chown/chmod the file.
- Precondition: action 7 complete.
- Expected mutation: wrapper file exists, executable by `pcae` (group
  `0750`), not writable by `pcae`.
- Read-back: `sudo -u pcae /opt/pcae/runtime/bin/pcae-launch --version`
  succeeds; `sudo -u pcae test -w
  /opt/pcae/runtime/bin/pcae-launch` fails.
- Rollback: `sudo rm /opt/pcae/runtime/bin/pcae-launch`.
- Rollback verification: path absent.

**Action 9 — Final full-verifier confirmation (read-only)**
- Command: `sudo -u pcae /opt/pcae/runtime/bin/pcae-launch health` and
  a direct `verify_class_b_deployment_conformance()` invocation run as
  `pcae` on the Dell itself.
- Privilege: none beyond `pcae`'s own (read-only).
- Precondition: actions 1–8 complete.
- Expected postcondition: none (read-only).
- Verification: fresh live result — exact-identity `COMPLIANT`
  required, never partial/truthiness credit (mirrors the Mac plan's own
  final-step discipline, L.5 §9 action 9).
- Rollback: n/a.

## 28. Action Count — Why Nine, And Why The Composition Differs From The Mac Plan

Nine actions, same count as the Mac plan's own nine — but this is
coincidental, not inherited: this plan adds a step the Mac never
needed (**Action 1**, apt-installing `python3-venv`/`python3-pip`,
because macOS's Python already carries a usable `pip`/`ensurepip` where
this Ubuntu image currently does not, §16), and correspondingly merges
work the Mac plan split across separate steps — the Mac plan's distinct
"configure Protected Root ACL/group/ancestor chain" step (its action 3)
collapses into this plan's single Action 3, because this Dell's
ancestor chain and default POSIX permissions already satisfy the ACL
requirement with zero extra ACL entries needed (§12/§18/§19), leaving
nothing separate to "configure." Likewise the Mac plan's three-way split
of `PYTHONPATH`-lockdown / `sitecustomize`-lockdown / trusted-`git`-PATH
(its actions 5, 6, 7) collapses into this plan's single Action 8 (the
launch wrapper), because a from-scratch Ubuntu wrapper script can set
all of `PYTHONNOUSERSITE`, `PATH`, and CWD in one file rather than
requiring three separately-verified interventions against an existing
macOS shell-profile-adjacent configuration surface. The two plans are
independently derived from the same HBDC requirement families against
two structurally different starting states, not copies of one another.

## 29. Idempotency

Each action in §27 is idempotent by construction: actions 1–4, 6–8 are
all "create if absent" operations against paths independently confirmed
absent this phase (§8/§12); a re-run against a host where the resource
already exists in the expected state (owner/mode/content match) is a
no-op read-back rather than a re-mutation (e.g. `useradd` would itself
fail loudly on an existing name — the actual provisioning phase's own
preflight must re-check absence immediately before running, not rely on
this phase's snapshot). Any state that does not match expectations
(e.g. a `pcae` user existing with the wrong uid/shell/group) must be
treated as an **unexpected conflicting state**, not silently overwritten
— the provisioning phase must stop and require human adjudication
rather than force-correcting it.

## 30. Failure Semantics

- **Preflight failure** (any action's precondition unmet at execution
  time): stop before that action; no partial mutation from that action
  occurs; prior completed actions are not automatically rolled back
  unless the operator explicitly chooses to abort the whole sequence.
- **Partial mutation** (an action fails mid-command, e.g. `mkdir`
  succeeds but `chown` fails): the action's own read-back step (§27)
  catches this — provisioning must not proceed to the next action until
  the current action's read-back passes.
- **Rollback order**: reverse of forward order (9→1), since each later
  action depends on an earlier one (§27's dependency shape) — Action 2
  (principal) must be rolled back last, as Actions 3–8 all depend on it
  existing.
- **Rollback failure** (e.g. `userdel` fails because a process still
  runs as `pcae`): stop; do not force (`userdel -f` / `rm -rf` beyond
  the specific path); report to the operator for manual adjudication —
  this mirrors HBDC's own fail-closed posture (§20 of HBDC-001).
- **Stop conditions**: any live read-back mismatch; any precondition
  re-check failure; any sign of a pre-existing conflicting resource not
  present in this phase's own snapshot (§29).

## 31. Developer/Environment Separation — Preflight Demonstration

- `atila`'s, `uosserver`'s, and `clawdbot`'s home directories remain
  untouched — not written to, not even listable by `codex` (§8/§11).
- No unrelated repository or project content was inspected or modified.
- The proposed `pcae` deployment identity uses no shared venv, no
  shared `PYTHONPATH`, and no shared `site-packages` with any other
  account — its production venv (§26/§27 Action 7) is a fresh,
  dedicated tree under `/opt/pcae/runtime/venv`, and its launch wrapper
  (§27 Action 8) explicitly clears `PYTHONPATH` and disables user-site.
- No unrelated development user is granted write authority over any
  proposed PCAE deployment resource — every proposed resource is either
  `root:pcae 0750` (write: root/sudo only) or `pcae:pcae 0750`
  (write: `pcae` only) — `atila`, `uosserver`, and `clawdbot` hold
  neither.

## 32. Current-Product Architecture Freeze

**Current:** Mac = PCAE development (`~/repos/pcae-harness`, unchanged).
Dell Ubuntu host (`atila-Latitude-E5470`, machine-id
`54ff22ce400b475aa0d55cb68f4a3334`) = PCAE deployment/execution target
(not yet provisioned). PCAE is consumed per repository — each
repository retains independent `.pcae/` governance state (§13/§14).

**Deferred (explicitly out of scope, not designed, not implemented):**
centralized fleet/project registration; organization-wide control
plane; centralized multi-repository scheduling; company-wide policy
distribution; enterprise dashboard/fleet orchestration.

## 33. No CHGR Election This Phase

`pcae decision-session` was **not** invoked this phase. No CHGR was
drafted or published for the Dell. Boundary P remains **NOT
AUTHORIZED** at phase exit, for any target.

## 34. Draft Next Proposition — DRAFT — NOT AUTHORIZED

> **DRAFT — NOT AUTHORIZED.** The following is a complete draft of the
> Boundary-P proposition for Phase 149O.20L.7B's own `pcae
> decision-session`, prepared for human review. It has no governance
> force until independently elected via a fresh `pcae decision-session`
> → `pcae governance-record publish` in that later phase.
>
> - **Target host:** `hac-dell` / `192.168.192.200`, hostname
>   `atila-Latitude-E5470`, machine-id
>   `54ff22ce400b475aa0d55cb68f4a3334`, Dell Inc. Latitude E5470, Ubuntu
>   24.04.3 LTS.
> - **Deployment (agent) principal / group:** `pcae` / `pcae` (new,
>   nologin, no login surface).
> - **Admin channel:** existing `codex` account via `sudo` (no new
>   admin OS account).
> - **Paths:** as frozen in §26.
> - **Source binding:** Model A only — pinned-commit `git clone` of
>   this repository's own `origin` into `/opt/pcae/runtime/src`,
>   editable-installed into `/opt/pcae/runtime/venv` (§20/§27 Action 6-7).
> - **Contracts:** HBDC-001 v1.0, HMIC-001 v1.3, HMRC-001 v1.1 (pin
>   exact versions current at the time this proposition is actually
>   voted on, not necessarily these — re-verify at 149O.20L.7B entry).
> - **Action graph:** exactly the nine actions in §27, in the stated
>   order, each gated on its own read-back before the next proceeds.
> - **Privileged operations:** Actions 1-4, 6-8 require root/sudo via
>   the existing `codex` channel; Action 9 requires no privilege.
> - **Rollback semantics:** §29-30.
> - **Exclusions:** no SSH login surface for `pcae` (§10); no
>   modification of `atila`/`uosserver`/`clawdbot` accounts or data
>   (§31); no centralized multi-repository control plane (§32); no
>   Boundary C (HMIC certification) or Boundary A (`HATP_MANDATORY`
>   activation) in scope — those remain separate, later, separately
>   authorized phases.
> - **Migration implications:** §15 — a future hardware replacement
>   requires fresh provisioning, fresh `DeploymentBinding`, fresh HMIC
>   certification; this is accepted, not designed away.
>
> **This proposition is a draft only. Boundary P is NOT AUTHORIZED by
> this document. No election has occurred.**

## 35-37. Boundaries Held Throughout This Phase

No account, group, SSH key, or sudoers entry was created on the Dell.
No directory was created, `chmod`'d, `chown`'d, or ACL-mutated on the
Dell. No clone, venv, or package installation occurred on the Dell. No
service was created. No certification or activation occurred.

```
Boundary P: NOT AUTHORIZED
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

## 38. Companion Tests

`tests/test_phase_149o_20l_7a_class_b_dell_target_re_selection_and_read_only_preflight.py`
asserts documentary/planning content of this document and the continued
absence of any Dell-provisioning or CHGR-publication artifact in this
repository. It does not attempt live Dell SSH within routine pytest
execution — the live evidence this phase gathered is preserved in this
document (§4-§25) rather than re-derived destructively by the test
suite on every run.

## 39. Phase Verdict

```
TARGET: DELL UBUNTU SELECTED — READ-ONLY PREFLIGHT COMPLETE
HOST: atila-Latitude-E5470 (hac-dell, 192.168.192.200), machine-id 54ff22ce400b475aa0d55cb68f4a3334
ELIGIBILITY: ELIGIBLE WITH PRECONDITIONS
BOUNDARY P: NOT AUTHORIZED — DELL-SPECIFIC PROPOSITION READY FOR HUMAN ELECTION
BOUNDARY C: NOT AUTHORIZED
BOUNDARY A: NOT AUTHORIZED
CLASS-B: NOT PROVISIONED
HATP: NOT READY
RUNTIME: Observed / observe / unavailable
NO DELL MUTATION OCCURRED
NO NEW CHGR PUBLISHED
RECOMMENDED NEXT PHASE: 149O.20L.7B — Dell Class-B Boundary-P Authorization Record Capture
```

## 40. Recommended Next Phase

**Phase 149O.20L.7B — Dell Class-B Boundary-P Authorization Record
Capture.** Must present the complete literal proposition in §34 to the
human governance authority and capture a fresh APPROVE/DECLINE/AMEND
election via `pcae decision-session` → `pcae governance-record
publish`. It must not provision. It must not skip directly to
execution.

## 41. Governance

`pcae check`: passed. `pcae health`: healthy. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings (pre-existing, unrelated,
not remediated here). Fresh, dedicated `Phase 149O.20L.7A: ...` task
used throughout (not a reused idle placeholder). No raw `git
commit`/`push` used — all commits via `pcae commit`/`pcae phase
complete`/`pcae push`. No lifecycle bypass, no `--no-verify`, no force
push. No Dell mutation occurred at any point in this phase. No CHGR was
published this phase.
