# Phase 149O.20L.7D — Dell Class-B Real Host Provisioning Execution

**Phase ID:** 149O.20L.7D
**Type:** Execution attempt (real host, live SSH) — **blocked, rolled back, no net mutation**
**Predecessor:** 149O.20L.7C (Dell Class-B Boundary-P Authorization Independent Verification)
**Entry repository commit:** `fdbc4246` (`Phase 149O.20L.7C: sync active-task allowed-file list`)

## 0. Outcome summary

This is the first phase permitted to mutate the Dell under CHGR
`chgr-96a0ce12756e4cc892492a87af1db832`. Every read-only entry/CHGR/
source/identity/collision/privilege check passed exactly as expected.
Actions 1–5 of the frozen 149O.20L.7B.1 nine-action plan were executed
against the live Dell (`hac-dell`, machine-id
`54ff22ce400b475aa0d55cb68f4a3334`) and independently verified
byte-for-byte against the frozen spec. **Action 6 (clone the pinned
commit from `git@github.com:atimad/pcae-harness.git`) could not proceed**:
neither `root` nor `codex` has any SSH private key usable for GitHub on
the Dell, and `github.com` was absent from `known_hosts`. The
149O.20L.7B.1 proposition explicitly discloses this key as an
out-of-scope prerequisite this phase may not provision or substitute for.

Per the frozen rollback semantics, Actions 5→4→3→2→1 were rolled back in
the prescribed safe order (all created resources were still empty) and
the resulting state was independently re-verified against the Dell.
**Net Dell mutation: none.** No DeploymentBinding, certification, or
activation was attempted at any point. No unrelated Dell principal,
service, or project was touched.

## 1. CHGR entry verification

`chgr-96a0ce12756e4cc892492a87af1db832` re-inspected before any mutation
(`.pcae/publication-execution/records/chgr-96a0ce12756e4cc892492a87af1db832.json`):

- `lifecycle_state`: `published`
- `selected_option_id`: `approve`
- `decision_subject`: Boundary-P provisioning authorization for Class-B
  target Dell (`hac-dell` / `atila-Latitude-E5470`, machine-id
  `54ff22ce400b475aa0d55cb68f4a3334`), per 149O.20L.7B.1 §19 amended
  proposition, re-presented in 149O.20L.7B.2
- `decision_maker_identity_evidence.identifier`: `Atila Madai`
- Pinned source SHA in `rationale`:
  `7a3fa971304521cdcb44251e07ef1966baec686a` (matches)
- `conditions` field explicitly excludes DeploymentBinding, Boundary C,
  Boundary A, HATP_MANDATORY activation, Cutover Record, Permission
  Broker changes, unrelated Dell mutation, arbitrary repository
  onboarding, Mac provisioning, centralized governance — all preserved
  throughout this phase.
- No revocation/supersession record found for this `record_id`.

**Result: VERIFIED, unrevoked, unsuperseded, scope as expected.**

## 2. Revocation/supersession result

None found. No other `chgr-*` record references or supersedes
`chgr-96a0ce12756e4cc892492a87af1db832`.

## 3. Immutable proposition reconstruction

Recovered `docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md`
directly from commit `f9e33232c83163aad5e50bc94db7cab51b844ac5` (`git
show`, not the mutable working tree). Extracted the exact nine-action
command plan (§9) and the exact 188-byte wrapper script (§12). Locally
recomputed the wrapper digest from those exact bytes:
`b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32` —
**matches** the CHGR-cited digest exactly.

## 4. Source freshness

- `7a3fa971304521cdcb44251e07ef1966baec686a` exists in this repository's
  history (`git cat-file -t` → `commit`).
- `git diff --stat 7a3fa971..HEAD -- src/pcae docs/contracts scripts`:
  **empty** — zero commits since the pin touched production source,
  contracts, or scripts.
- At the pinned commit: `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` declares
  **HBDC-001 v1.0**; `HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
  declares **HMIC-001 v1.3**; HMIC-001's own depends-on header cites
  **HMRC-001 v1.1**. All three match the phase brief exactly.
- `src/pcae/core/hatp_class_b_conformance.py` and
  `src/pcae/core/hatp_class_b_topology_verifier.py` present at the pin.

**Result: no material source drift. No repin performed.**

## 5. Dell identity

Read-only SSH (`ssh hac-dell`) at execution entry:

| Field | Expected | Observed |
|---|---|---|
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` |
| hostname | `atila-Latitude-E5470` | `atila-Latitude-E5470` |
| OS | Ubuntu 24.04.3 LTS | Ubuntu 24.04.3 LTS |
| arch | amd64/x86_64 | x86_64 |

**Match exactly. No STOP triggered.**

## 6. Collision preflight

All fresh immediately before Action 1: `pcae` group/user absent
(`getent` exit 2/2), `/etc/pcae`, `/opt/pcae`, `/var/lib/pcae`,
`/var/log/pcae`, `/home/pcae`, `/opt/pcae/runtime/bin/pcae-launch` all
absent (`test -e` exit 1). Ancestors `/` and `/etc` both `root:root
755`. No wrapper, no conflicting checkout, no conflicting venv.

**No CONFLICTING state anywhere.**

## 7. Privilege posture

`sudo -n -l` for `codex` on the Dell: `(ALL : ALL) ALL`, `(ALL : ALL)
NOPASSWD: ALL` — matches the expected ability to perform the exact
authorized actions. No sudoers changes made.

## 8. Complete before-state

- Packages: `python3-venv` not-installed, `python3-pip` not-installed.
- Principals: `pcae` user/group absent.
- Paths: all eight target paths + wrapper path absent; ancestor chain
  `root:root 755`.
- Git/Python identity: `/usr/bin/git` 2.43.0, `/usr/bin/python3` 3.12.3.
- Environment: `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`,
  `PYTHONPATH` unset.

## 9. Rollback readiness gate

Every action classified before Action 1: Actions 1–4 and 6–8 ABSENT →
CREATE; Action 5 depends on Action 2. No CONFLICTING classification
anywhere. Clear to proceed.

## 10–17. Action results

| # | Action | Result |
|---|---|---|
| 1 | Install `python3-venv`/`python3-pip` | **CREATE**, then rolled back (simulated removal named only these two packages; matched frozen criterion; actually removed; verified 0 installed) |
| 2 | Create `pcae` group/user | **CREATE** — read-back `uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)`, shell `/usr/sbin/nologin`, no sudo/other groups — exactly as required; then rolled back (`userdel -r` + `groupdel`), verified absent |
| 3 | Create Protected Root `/etc/pcae/hatp/trust-store` | **CREATE** — read-back `root:pcae 750`, ancestors `root:root 755`, ACL exactly the 3 standard POSIX entries; then rolled back (`rmdir` × 3, directory was empty), verified absent |
| 4 | Create runtime/project/state tree (8 paths) | **CREATE** — all 8 paths read back as `root:pcae 750` exactly; then rolled back (`rmdir` × 8, all empty), verified absent |
| 5 | Normalize `/home/pcae` | **CREATE** (idempotent re-apply) — read-back `pcae:pcae 750`; no independent rollback (covered by Action 2's `userdel -r`) |
| 6 | Clone pinned commit | **BLOCKED — not attempted.** No deploy-capable SSH key for `git@github.com` present for `root` or `codex`; `github.com` absent from `known_hosts`. Out-of-scope prerequisite per 7B.1 §9 Action 6 "Secret boundary." No substitute command generated. |
| 7 | Create venv + editable install | **NOT ATTEMPTED** (depends on Actions 1+6; 6 blocked) |
| 8 | Create launch wrapper | **NOT ATTEMPTED** (independent of 6/7, but withheld — see §21 rationale below) |
| 9 | Class-B verifier | **NOT ATTEMPTED** (depends on 2–8) |

Action 8 was deliberately not attempted out of order even though it has
no direct dependency on Action 6: with Action 6/7 blocked, deploying
only the wrapper would leave a permanently-broken `pcae-launch` (it
`exec`s a venv that doesn't exist) — a conflicting/misleading partial
state on next attempt, not a clean rollback boundary. Withholding it
keeps the actual-mutation set minimal and fully reversible.

**Exact wrapper digest (recomputed, never deployed):**
`b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`

## 18. Action 9 measured verifier output

**Not run.** Action 9 depends on Actions 2–8, which are incomplete.

## 19. Expected-vs-actual HBDC result

Not applicable — no verifier run.

## 20. Actual mutation inventory

| Action | Resource | Before | After rollback |
|---|---|---|---|
| 1 | `python3-venv`, `python3-pip` dpkg state | not-installed | not-installed (installed then removed) |
| 2 | `/etc/passwd`, `/etc/group`, `/home/pcae` | absent | absent (created then `userdel -r`/`groupdel`) |
| 3 | `/etc/pcae/hatp/trust-store` | absent | absent (created then `rmdir`) |
| 4 | `/opt/pcae/*`, `/var/lib/pcae`, `/var/log/pcae` | absent | absent (created then `rmdir`) |
| 5 | `/home/pcae` ownership/mode | n/a (removed with Action 2) | n/a |

**Every mutation made falls within CHGR-authorized scope (Actions
1–5 of the exact nine-action plan). Every mutation was reverted and the
reversion independently verified. Zero unexplained mutation. Net
persistent Dell state change: none.**

## 21. No-op actions

None — every mutated action found the target ABSENT (fresh CREATE), not
EXACTLY SATISFIED, since the Dell had no prior PCAE footprint.

## 22. Failures/rollbacks

One blocking failure: Action 6 preflight discovered a missing
prerequisite (GitHub SSH key) that this phase is not authorized to
provision. Rollback of Actions 5→4→3→2→1 executed per the frozen
per-action rollback procedures, in the frozen safe order, and
independently re-verified against the live Dell (§23). Rollback did not
itself fail at any step.

## 23. Idempotency inspection (post-rollback)

Fresh re-read of the Dell after rollback: `pcae` group/user absent
(`getent` exit 2/2); `/etc/pcae`, `/opt/pcae`, `/var/lib/pcae`,
`/var/log/pcae`, `/home/pcae` all absent (`test -e` exit 1);
`python3-venv`/`python3-pip` dpkg status empty (not installed);
unrelated principal `atila` (uid 1000, groups
`adm,cdrom,sudo,dip,plugdev,users,lpadmin,uosserver,devbots`) unchanged.
State is bit-for-bit equivalent to §8's before-state.

## 24. Principal/group final state

`pcae` group and user: absent (never left behind).

## 25. Filesystem/ACL final state

All eight target paths and the wrapper path: absent. Ancestors `/` and
`/etc`: unchanged `root:root 755`.

## 26. Source checkout final state

Never created. `/opt/pcae/runtime/src` does not exist.

## 27. Venv/install final state

Never created. `/opt/pcae/runtime/venv` does not exist.

## 28. Wrapper/environment final state

Never created. `/opt/pcae/runtime/bin/pcae-launch` does not exist.

## 29. Developer/source separation

Mac development checkout (`~/repos/pcae-harness`) unchanged throughout
(`git status --short` clean before and after; no commits touched
`src/pcae/**`, `docs/contracts/**`, or `scripts/**`). No Dell runtime
was created, so no dependency questions on Mac/other-project paths
arise this phase.

## 30. Proof no DeploymentBinding

No `DeploymentBinding`, certification pointer, Cutover Record, or
activation artifact was created, read, or referenced for mutation
purposes at any point in this phase.

## 31. Boundary status

- **Boundary P:** authorized (CHGR `chgr-96a0ce12756e4cc892492a87af1db832`), **execution attempted, blocked before completion, net mutation reverted to zero.**
- **Boundary C:** NOT AUTHORIZED — untouched.
- **Boundary A:** NOT AUTHORIZED — untouched.
- **HATP:** NOT READY — unchanged.
- **Runtime:** Observed / observe / unavailable — unchanged.

## 32. Unrelated-project preservation

`atila`, `uosserver`, `devbots`/`clawdbot`, `hac-windows`, and all other
principals/services/projects on the Dell: not read, not modified.
Confirmed via `id atila` (unrelated to mutation) — no other host,
service, or account was touched at any point.

## 33. Repository-onboarding prohibition preserved

No project repository cloned, no `.pcae` project directory created, no
repo-slug initialized, no governed coding work run on the Dell.

## 34. Centralized-governance deferral preserved

No central repository registry, multi-project control plane,
company-wide governance, central scheduling, or fleet orchestration
implemented.

## 35. CHGR post-execution integrity

`chgr-96a0ce12756e4cc892492a87af1db832.json`: `git status --short` on
the file shows no change; not staged, not modified, not touched by this
phase. Not marked "consumed" — no canonical mechanism in this repository
requires that, and none was invented here.

## 36. Software/source changes

None. No changes to `src/pcae/**`, `docs/contracts/**`, or `scripts/**`
were needed or made. The Action 6 blocker is an operational
(missing-credential) gap, not a software or contract defect.

## 37. Tests

`tests/test_phase_149o_20l_7d_dell_class_b_real_host_provisioning_execution.py`
— read-only, static-repository-state assertions (CHGR record content
and integrity, pinned commit existence and source-drift absence,
wrapper byte/digest reconstruction, HBDC/HMIC/HMRC contract versions at
the pin, this phase's own doc content matching the actually-observed
outcome). No user/directory creation or deletion performed by the test
suite itself — the live-Dell mutation-and-rollback evidence is
documented in this report (§10–§23), independently reproducible via SSH,
not re-executed by CI.

## 38. Governance checks

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae push check`: clean prior to this phase's commits.
`pcae doctor task-memory`: pre-existing warnings only (stale
`tasks/active/*` idle files and `tasks/DONE.md` entries predating this
phase — unrelated, not introduced or fixed by this phase, out of scope
per §29 of the governing instruction).

## 39. Commits, pushed status, origin/main..HEAD

Recorded in the governed task-lifecycle commits for this phase (see
`git log`). `origin/main..HEAD` and push status confirmed via `pcae
push check` immediately before and after finalization.

## 40. Recommended next phase

Not 149O.20L.7E (independent verification of a completed provisioning —
provisioning did not complete). Recommended: **149O.20L.7D.1 — Dell
Deploy-Key Provisioning + Real Host Provisioning Execution Retry**, a
narrowly-scoped phase that (a) provisions, via the disclosed
separate admin channel, a deploy-capable SSH key for
`git@github.com:atimad/pcae-harness.git` readable by `root`/`codex`-sudo
on the Dell, with `github.com`'s host key recorded in `known_hosts`
through a verified fingerprint, then (b) re-runs this exact same
149O.20L.7B.1 nine-action plan under the same (still valid, unrevoked,
unsuperseded) CHGR from a verified-clean slate. 149O.20L.7E (independent
verification) remains correctly sequenced to follow only a
*successfully completed* provisioning attempt.

No DeploymentBinding created. No certification. No activation. Phase
149O.20L.7D stops here.
