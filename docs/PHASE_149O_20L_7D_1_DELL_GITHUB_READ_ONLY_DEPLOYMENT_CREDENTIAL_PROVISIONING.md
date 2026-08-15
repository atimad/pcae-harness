# Phase 149O.20L.7D.1: Dell GitHub Read-Only Deployment Credential Provisioning

## 1. Phase Entry State

- **Phase-entry commit:** `3298667c` (`Phase 149O.20L.7D: sync phase-completion
  metadata to post-push state`), branch `main`, `origin/main..HEAD` empty
  (nothing to push at entry).
- **7D rollback-state independent re-verification (this phase, live SSH to
  `hac-dell`):**
  - `getent passwd pcae` / `getent group pcae` → both exit `2` (absent).
  - `/etc/pcae`, `/opt/pcae`, `/var/lib/pcae`, `/var/log/pcae`, `/home/pcae`
    → all absent (`test -e` exit `1`).
  - `dpkg -l python3-venv python3-pip` → both `un` (not installed).
  - `/root/.ssh/` contained only an empty `authorized_keys`; no
    `id_ed25519`, no `known_hosts` github.com entry, no `config` file.
  - `~codex/.ssh/` had no `github.com` entry in `known_hosts`.
  - Conclusion: **rollback confirmed bit-for-bit clean** — entering
    UNPROVISIONED — CLEAN PRE-EXECUTION STATE, as required before any
    credential mutation.

## 2. Immutable Action-6 Secret-Boundary Reconstruction

Recovered from pinned commit `f9e33232c83163aad5e50bc94db7cab51b844ac5`
(`docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md`,
§ "Action 6 — Clone canonical PCAE source at the pinned commit"), read via
`git show` against the immutable object, not the working tree.

Frozen forward command (verbatim, no `-i`/`GIT_SSH_COMMAND` override):

```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
```

The proposition's own disclosed secret boundary: *"cloning
`git@github.com:atimad/pcae-harness.git` over SSH requires a deploy-capable
SSH key readable by the invoking (`root`/`codex`-sudo) process. This
proposition does not name, provision, or embed that key or its filesystem
location — key provisioning is a separate admin-channel concern, out of
scope here."*

## 3. Outcome A/B Adjudication

**Outcome A (anticipated external prerequisite) — established.**

Rationale: the frozen Action 6 command contains no identity flags; SSH
identity resolution for `git@github.com` is entirely ambient (resolved via
root's SSH client configuration at invocation time). Provisioning a
dedicated key plus a `Host github.com` stanza in `/root/.ssh/config` that
pins `IdentityFile`/`IdentitiesOnly` changes *which key root's ambient SSH
client resolves* — it does not change the clone command text, the
repository URL, the pinned SHA, the target path, or any other
authority-bearing token of Action 6. This is exactly the class of
prerequisite the proposition explicitly disclosed and excluded from
Boundary P. No Outcome-B trigger (URL change, protocol change, command
rewrite, unreviewed dependency, different principal) applies.

**CHGR `chgr-96a0ce12756e4cc892492a87af1db832` remains current, subject to
fresh 7D.2 entry checks.** Not independently consumed by this phase (this
phase performed zero Boundary-P mutation actions).

## 4. Dell Identity Reconfirmation

Live read-only SSH this phase: `machine-id 54ff22ce400b475aa0d55cb68f4a3334`,
`hostname atila-Latitude-E5470`, Ubuntu 24.04.3 LTS, x86_64 — exact match to
the expected target.

## 5. Credential Architecture

- **Scope:** dedicated, freshly generated Ed25519 keypair, used solely for
  read-only retrieval of `atimad/pcae-harness` from GitHub. Not the
  operator's personal key, not the existing Dell login key (`~codex/.ssh`
  was untouched aside from an unrelated pre-existing `known_hosts` file),
  not reused from any other project.
- **Ownership model:** Action 6 clones via `sudo` (root). The key is owned
  by `root:root`, stored under `/root/.ssh/`, unreadable by `codex` or any
  other principal (mode `600`).
- **Exact key path:** `/root/.ssh/pcae_harness_deploy_ed25519` (dedicated,
  unambiguous name — deliberately not `id_ed25519`, to avoid identity
  ambiguity with any future root default key).
- **Owner/group/mode:** `root:root 600` (private key), `root:root 644`
  (public key). Verified via `stat -c '%U:%G %a %n'` immediately after
  generation.
- **Generation:** `ssh-keygen -t ed25519 -N "" -f <path> -C
  "pcae-harness-deploy-readonly@hac-dell"` — fresh keypair, no existing
  file overwritten (target path was independently confirmed absent
  immediately beforehand; generation would have aborted otherwise).
- **Passphrase policy — disclosed tradeoff:** intentionally **unencrypted
  on disk**. Action 6 runs unattended via `sudo` with no interactive
  terminal for a passphrase prompt; a passphrase-protected key would make
  the frozen command non-functional. Compensating control: root-only
  filesystem access (`600`, `root:root`, no `pcae`/`codex`/group/world
  readability) plus GitHub-side repository-scoped, read-only authority
  (§8) — a stolen key can only read one repository, not act as the
  operator or any other principal.
- **Public-key fingerprint:** `SHA256:pSD+FImEdVWIut+199XjrkqMeeu6eCOZd1FldrMiTrk`
  (ED25519, comment `pcae-harness-deploy-readonly@hac-dell`).

## 6. GitHub Registration

Registered via `gh api repos/atimad/pcae-harness/keys` (authenticated as
repo admin `atimad`, token scopes include `admin:public_key`, `repo`) as a
**repository deploy key**, `read_only: true`:

```
{"id":160313031,"title":"pcae-harness-deploy-readonly@hac-dell",
 "verified":true,"read_only":true,"enabled":true,"added_by":"atimad"}
```

Deploy keys are inherently repository-scoped by GitHub's own mechanism
(cannot access any other repository) and `read_only: true` disables write
access at the GitHub-API level — this is the GitHub-side setting cited as
proof of no write authority (§9 below), independent of any test push.

## 7. GitHub Host Identity / known_hosts

Host key fingerprints were **not** accepted from the network on
trust-on-first-use. They were independently retrieved from GitHub's own
published meta endpoint (`https://api.github.com/meta`, `ssh_keys` array,
fetched over TLS) and written verbatim into `/root/.ssh/known_hosts`
(`ed25519`, `ecdsa-sha2-nistp256`, `rsa` entries for `github.com`).

- **known_hosts path (matching Action 6's actual SSH context — root, since
  the clone runs via `sudo`):** `/root/.ssh/known_hosts`.
- **Owner/group/mode:** `root:root 600`.
- `StrictHostKeyChecking=no` was never used at any point.

## 8. Deterministic Identity Selection

`/root/.ssh/config`:

```
Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/pcae_harness_deploy_ed25519
    IdentitiesOnly yes
```

`IdentitiesOnly yes` guarantees the clone cannot silently succeed via a
different identity (ssh-agent, a different root/codex key, etc.). This
stanza only affects identity *resolution*; the Action 6 command string is
untouched, consistent with the Outcome-A adjudication in §3.

## 9. Read-Only Verification (no production clone, no test push)

- `sudo ssh -T git@github.com` → `Hi atimad/pcae-harness! You've
  successfully authenticated, but GitHub does not provide shell access.`
  — the response naming exactly one repository is direct evidence the key
  is scoped to that repository, not the account.
- `sudo git ls-remote git@github.com:atimad/pcae-harness.git` → succeeded,
  listing `HEAD`/`refs/heads/main`/tags. Read access confirmed.
- Pinned-SHA reachability was verified **without** touching
  `/opt/pcae/runtime/src`: a disposable bare repo was created under
  `/tmp` (`git init --bare`), `git fetch --depth=1
  git@github.com:atimad/pcae-harness.git
  7a3fa971304521cdcb44251e07ef1966baec686a` succeeded, `FETCH_HEAD`
  resolved to `7a3fa971304521cdcb44251e07ef1966baec686a` exactly, and the
  disposable directory was then `rm -rf`'d and independently reconfirmed
  absent. No write/push operation was attempted at any point.
- **Proof of no write authority:** the GitHub API's own `read_only: true`
  field on the registered deploy key (§6) — the authoritative, non-testing
  source for this fact, per this phase's constraint against attempting a
  test push.

## 10. Credential Persistence / Rollback Procedure (not executed this phase)

Unlike 7D's fully-rolled-back attempt, this phase's clean-success end
state **intentionally leaves host mutation in place**:

- Dell: `/root/.ssh/pcae_harness_deploy_ed25519{,.pub}`,
  `/root/.ssh/known_hosts` (github.com entries appended),
  `/root/.ssh/config` (github.com stanza).
- GitHub: deploy key id `160313031` on `atimad/pcae-harness`.

**Rollback/revocation procedure, defined but not executed:**

- Dell: `sudo rm -f /root/.ssh/pcae_harness_deploy_ed25519{,.pub}`;
  remove only the `Host github.com` stanza this phase added from
  `/root/.ssh/config`; remove only the three `github.com` lines this
  phase appended to `/root/.ssh/known_hosts` (provenance-safe — no other
  entries existed at those paths before this phase).
- GitHub: `gh api -X DELETE repos/atimad/pcae-harness/keys/160313031`.

This distinguishes **Class-B infrastructure: NOT PROVISIONED** (unchanged)
from **source-access prerequisite: INSTALLED**. The Dell is not
"globally clean" after this phase.

## 11. Secret-Leakage Check

`git status --porcelain` / `git diff --stat` against this phase's changes
were inspected before finalization: only this doc, the companion test
module, `PROJECT_STATUS.md`, `CHANGELOG.md`, and `tasks/**` governance
artifacts changed. No private key bytes, no passphrase, no raw SSH config
secret material was ever written to this repository, any log captured in
this repository, or this report. Only the public fingerprint and
non-secret GitHub API metadata are recorded above.

## 12. No Class-B / DeploymentBinding / Boundary C / Boundary A Actions

Independently re-confirmed at phase close via live SSH:

- `getent passwd pcae` / `getent group pcae` → still absent.
- `/etc/pcae`, `/opt/pcae`, `/var/lib/pcae`, `/var/log/pcae`, `/home/pcae`
  → still absent.
- `python3-venv`/`python3-pip` → still not installed.
- No DeploymentBinding, HMIC certification, Cutover Record, or activation
  marker was created. No Permission Broker / POL-005 / COMP-002 change was
  made. Runtime state unchanged: `Observed` / `observe` / `unavailable`.
- No unrelated Dell principal, `hac-windows`, or other project was
  touched.

## 13. Governance Results (this phase, local repo)

- `pcae health` → healthy.
- `pcae check` → passed.
- `pcae status coherence` → coherent.
- `pcae doctor task-memory` → warnings (pre-existing `tasks/done/` /
  `tasks/DONE.md` bookkeeping pileup, predating this phase, outside this
  phase's allowed-file scope — not remediated here).
- `pcae push check` (pre-implementation) → clean, `nothing_to_push`.
- `pcae runtime inspect` → `Observed` / `observe` / `unavailable`.
- `pcae notify status` → Telegram configured/enabled.

## 14. CHGR / Class-B / Boundary State Summary

- **Source-access prerequisite:** PROVISIONED — dedicated read-only GitHub
  deploy credential verified (fingerprint
  `SHA256:pSD+FImEdVWIut+199XjrkqMeeu6eCOZd1FldrMiTrk`).
- **Dell Class-B infrastructure:** NOT PROVISIONED.
- **Dell Boundary P:** independently verified authorization retained —
  fresh execution-entry validation required at 7D.2 entry.
- **DeploymentBinding:** NOT AUTHORIZED.
- **Boundary C:** NOT AUTHORIZED.
- **Boundary A:** NOT AUTHORIZED.
- **HATP:** NOT READY.
- **Runtime:** Observed / observe / unavailable.
- **CHGR `chgr-96a0ce12756e4cc892492a87af1db832`:** REMAINS CURRENT
  SUBJECT TO FRESH 7D.2 ENTRY CHECKS.

## 15. Recommended Next Phase

**149O.20L.7D.2 — Dell Class-B Real Host Provisioning Execution Retry.**
Must independently reverify the CHGR, verify this credential prerequisite,
verify machine/source/contracts, verify Class-B infrastructure remains
absent, verify no collisions, verify the pinned SHA, verify the exact
frozen command plan, verify the wrapper digest, then execute the original
nine-action plan (149O.20L.7B.1) from a freshly reverified entry state.
This phase (7D.1) does not combine with or execute any part of that retry.
