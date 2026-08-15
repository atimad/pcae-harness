# Phase 149O.20L.7D.3 — Action-6 File-Mode + Continuation-Baseline Proposition Amendment

## 0. Phase Identity and Type

Analysis + proposition amendment + human election + authorization
publication only. This phase does **not** execute Action 6, does
**not** execute Actions 7-9, does **not** rerun Actions 1-5, does
**not** mutate Dell Class-B infrastructure, does **not** create a
DeploymentBinding, does **not** certify, and does **not** activate.
All Dell interaction this phase is read-only SSH.

## 1. Entering State

```
$ git status --short                → (clean)
$ git status --branch --short       → ## main...origin/main
$ git log --oneline origin/main..HEAD → (empty)
$ git rev-list --count origin/main..HEAD → 0
```

- `pcae health`: healthy. Agent lock: held by `claude-local`. Git
  status: clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing, historical
  `tasks/done/` entries missing from `tasks/DONE.md` (18+ entries
  predating this phase by many prior phases); unrelated; outside this
  phase's allowed-file scope; not remediated here.
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: 149O.20L.7D.2's canonical report,
  consistent; recommended next phase names this phase
  (149O.20L.7D.3).
- `pcae phase-report reconcile --phase-id 149O.20L.7D.2`: `status:
  reconciled`, `mutation: none (inspection only)`.

Entering authority state (unchanged from 7D.2's close):

```
Boundary P: AUTHORIZED (chgr-96a0ce12756e4cc892492a87af1db832) for the
            frozen nine-action plan text as originally published —
            see §7 for why that authorization no longer suffices for
            further execution.
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    PARTIALLY PROVISIONED (Actions 1-5)
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

This phase's entering commit is `348e8779` (the tip of `main` at
phase start, HEAD == `origin/main`).

## 2. Immutable-Plan Reconstruction (from Commit, Not the 7D.2 Report's Paraphrase)

Retrieved via `git show f9e33232c83163aad5e50bc94db7cab51b844ac5:docs/PHASE_149O_20L_7B_1_DELL_BOUNDARY_P_PROPOSITION_MATERIALIZATION_AMENDMENT.md`
(1209 lines; `docs/PHASE_149O_20L_7B_1_...md` +
`tests/test_phase_149o_20l_7b_1_...py`, 1490 insertions, nothing
else — confirmed via `git show --stat`).

### Action 6 — exact original text (§9, lines 540-611 of that commit)

**Preflight (read-only):**
```
test -d /opt/pcae/runtime/src ; echo $?
sudo find /opt/pcae/runtime/src -mindepth 1 -maxdepth 1 2>&1
```
Directory exists (from Action 4) and is empty → **ABSENT** (of a
checkout): proceed to forward. Already contains a checkout matching
pinned SHA/remote/clean status → **EXACTLY SATISFIED → NO-OP**.
Non-empty and not matching → **CONFLICTING → STOP**.

**Forward (only if ABSENT) — the defective command sequence:**
```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;
```

**Read-back (the postcondition that Action 6 failed):**
```
git -C /opt/pcae/runtime/src rev-parse HEAD
    → must equal 7a3fa971304521cdcb44251e07ef1966baec686a EXACTLY
git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    → non-zero (detached HEAD)
git -C /opt/pcae/runtime/src status --short
    → empty (no local modifications)
git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
test -f .../docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md ; echo $?  → 0
test -f .../src/pcae/core/hatp_class_b_conformance.py ; echo $?          → 0
```

**Rollback:**
```
sudo rm -rf /opt/pcae/runtime/src
sudo mkdir -p /opt/pcae/runtime/src
sudo chown root:pcae /opt/pcae/runtime/src
sudo chmod 0750 /opt/pcae/runtime/src
```

**Rollback verification:**
```
sudo find /opt/pcae/runtime/src -mindepth 1 | wc -l   → 0
stat -c '%U:%G %a' /opt/pcae/runtime/src               → root:pcae 750
```

Actions 1-5, 7-9, the privilege map, idempotency rules, wrapper bytes/
digest, and stop semantics were independently re-read from the same
commit and are reproduced/re-cited by reference at the exact points
below where each is used (§3, §9, §11, §12).

## 3. Reconstruction of the Real 7D.2 Failure (Primary Evidence)

`git show 33f1dc0bae9c0fdba1bc792673ceb8193993734a --stat` →
`docs/PHASE_149O_20L_7D_2_...md` + a companion test file, 676
insertions, nothing else. Section 12 of that document ("Action 6 —
source clone at pinned commit — FAILED READ-BACK, STOPPED, ROLLED
BACK") records:

- The clone and detached checkout **succeeded**: `git rev-parse HEAD`
  returned the pinned SHA exactly; `git symbolic-ref -q HEAD` failed
  (exit 1, correctly detached); the pinned contract and verifier files
  were present.
- The forward command's final two lines then ran exactly as frozen
  (`find ... -type d -exec chmod 0750`, `find ... -type f -exec chmod
  0640`).
- Read-back's clean-working-tree check failed:
  ```
  $ sudo git -C /opt/pcae/runtime/src status --short
   M .githooks/pre-commit
   M .githooks/pre-push
   M .pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json
   M .pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json
   M .pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json
   M scripts/check-docs-updated.sh
  ```
- `git diff --stat` → `6 files changed, 0 insertions(+), 0
  deletions(-)` — **zero content bytes changed**, confirming a
  pure-mode diff.
- `git diff .githooks/pre-commit` → `old mode 100755` / `new mode
  100644` for every one of the six files (independently reproduced in
  scratch, §5 below — identical for all six).
- Exact point of failure: Action 6's own read-back gate
  (`git status --short` non-empty), immediately after the frozen
  forward command completed and before any rollback began.
- Rollback executed exactly as frozen (`rm -rf`; `mkdir -p`;
  `chown root:pcae`; `chmod 0750`) and independently verified:
  `find /opt/pcae/runtime/src -mindepth 1 | wc -l` → `0`;
  `stat -c '%U:%G %a' /opt/pcae/runtime/src` → `root:pcae 750` — exact
  match to Action 4's own postcondition.
- No substitute command was invented at any point; Actions 7-9 were
  not attempted.

No repair was made in 7D.2 — that phase's own governing instruction
required disclosure and STOP, not repair. Nothing in this section
repairs anything; it only reconstructs what actually happened.

## 4. Defect Classification (Independently Derived, Not Assumed)

Three hypotheses were evaluated:

1. **Proposition defect** — the frozen command text itself conflicts
   with its own read-back requirement.
2. **Production/source defect** — the repository contains incorrect
   tracked file modes.
3. **Host/tooling defect** — Git or filesystem behavior differs from
   what the proposition assumed.

**Evidence against (2):** `.githooks/pre-commit`, `.githooks/pre-push`,
and `scripts/check-docs-updated.sh` are git hooks / a directly-invoked
shell script — tracking them `100755` is *correct*, not a defect; a
repository that ships executable hooks and scripts as non-executable
would itself be the actual defect. (The three JSON files' `100755`
mode is separately assessed in §5 as an unrelated cosmetic anomaly,
not the cause of this failure and not something this phase repairs.)

**Evidence against (3):** the scratch reproduction (§6) exactly
reproduces the same six-file, zero-content, mode-only diff using
ordinary `git`/`chmod`/`find` on a different machine (this Mac) against
the identical pinned commit, using the same command text. Git and
filesystem behavior are consistent and expected — `find -type f -exec
chmod 0640 {} \;` unconditionally sets `0640` on every regular file
regardless of its prior mode, and Git tracks executable bits in its
index (mode `100755` vs `100644`) and reports a mode-only diff as
`modified` in `git status --short` by design (`core.fileMode` is `true`
in this repository, confirmed via `git config core.fileMode`, and
default on the Dell host per its own `git version 2.43.0`
installation) — exactly the behavior the frozen read-back relies on
for every *other* check in the plan (rev-parse, remote URL,
contract-file presence). Nothing here is anomalous host/tooling
behavior.

**Evidence for (1):** the forward command's own last line
(`find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;`) is
*unconditional* — it does not consult the Git index mode of any file
it touches. The read-back's clean-working-tree requirement is
*conditional on Git's own index* — it fails on any tracked-mode
mismatch, executable or not. These two requirements are mutually
exclusive whenever the pinned commit tracks even one executable file,
which it does (six, per §5). The frozen command sequence cannot
satisfy its own frozen read-back for this repository, independent of
host, timing, or execution identity.

**Conclusion, independently derived: this is a proposition (command-
text) defect — Finding D3-1 (§10).** Not a production/source defect,
not a host/tooling defect.

## 5. Complete Tracked-Mode Inventory at the Pinned Source Commit

At `7a3fa971304521cdcb44251e07ef1966baec686a`
(`git ls-tree -r <sha>`), enumerated in full, not limited to the six
paths `git status` exposed:

| Git index mode | Count |
|---|---|
| `100644` (regular, non-executable) | 4024 |
| `100755` (regular, executable) | 6 |
| `120000` (symlink) | 0 |
| `160000` (submodule/gitlink) | 0 |
| **Total tracked paths** | **4030** |

The six `100755` paths, in full:

1. `.githooks/pre-commit`
2. `.githooks/pre-push`
3. `scripts/check-docs-updated.sh`
4. `.pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json`
5. `.pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json`
6. `.pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json`

Items 1-3 are intentional: two Git hooks and one directly-invoked
shell script must be executable to function; this matches the
repository's own convention throughout its history.

Items 4-6 are **disclosed as a separate anomaly, not silently
normalized**: these are JSON governance-record artifacts (not
executed code) that this repository's own history shows were added in
commit `21c33c18` ("Phase 149O.20L.6: Class-B Provisioning
Authorization Record Capture") already carrying mode `100755` — most
likely an accidental executable bit picked up from the authoring
machine's `umask`/tooling at `git add` time (macOS, confirmed:
`ls -la` on the working tree shows `-rwxr-xr-x` for these files
locally right now), never touched by anything Action-6-related. Their
content is JSON, never executed, and is byte-identical regardless of
mode. This phase does **not** repin the source or hand-edit these
files' modes in the repository to "fix" them — per §9 of the
governing instruction, no independent evidence establishes that this
cosmetic anomaly is itself a defect *requiring a separate production
repair phase* (it does not break anything, is not the cause of the
Action-6 failure, and correcting it would need its own governed commit
touching `.pcae/**` history, out of scope here). It is disclosed here
so a future phase can decide whether it warrants cleanup; the pinned
source commit `7a3fa971` is preserved unchanged.

No symlinks or submodules exist in the pinned tree, so those two
classes require no further analysis for Action 6's mode handling.

## 6. Scratch Reproduction and Candidate Repair Validation (Disposable, Never Production)

All commands in this section ran in a disposable local clone under
this Mac's scratch directory (`git clone --no-checkout
~/repos/pcae-harness <scratch>/src`, then `git checkout --detach
7a3fa971...`), never against `/opt/pcae/runtime/src` on the Dell, and
the scratch directory was deleted (`rm -rf`) immediately after use.
No `sudo`, no Dell SSH session, and no production path was touched in
this section.

### 6.1 Defect reproduction (confirms §3/§4 exactly)

```
find src -type d -exec chmod 0750 {} \;
find src -type f -exec chmod 0640 {} \;
```
Result: `git -C src status --short` produced the identical six-path
list as the real 7D.2 Dell execution; `git diff --stat` →
`6 files changed, 0 insertions(+), 0 deletions(-)`; `git diff
.githooks/pre-commit` → `old mode 100755` / `new mode 100644`. Exact
match to §3's primary evidence.

### 6.2 Rejected shortcut — analyzed, not used (per governing instruction §12)

`git restore .` after the blanket chmod was considered and rejected as
the forward-command strategy: it would restore Git's *recorded* mode
bits via a second mutation that depends on `core.fileMode` being
`true` (a repository/host configuration setting, not a Git guarantee)
and would intentionally create a dirty tree merely to clean it
afterward — obscuring the actual provisioning invariant ("apply the
correct mode once") behind a "mutate wrong, then repair" two-step that
has no read-back advantage over getting it right the first time. It
also does nothing to address ownership/mode *hardening* (dropping
world access), which is the actual purpose of Action 6's mode step —
`git restore .` alone would leave file modes at whatever `git
checkout` produced by default (typically `0644`/`0755` under a `022`
umask), which is world-readable and does not satisfy the trust
model's intended group-only access. Rejected in favor of §6.3.

### 6.3 Repaired candidate — deterministic index-mode mapping (selected, §7)

```
find src -type d -exec chmod 0750 {} \;
find src -type f -perm -u+x -exec chmod 0750 {} \;
find src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

This replaces the single unconditional line with two branches keyed
on the file's **current owner-execute bit**, which `git checkout`
already sets correctly from the Git index for every one of the 4030
tracked paths (verified independently below, not merely assumed from
Git's documented behavior) — no `git ls-files -s` parsing or
Git-index re-reading is required at chmod time; the on-disk bit
`git checkout` leaves behind *is* the index classification.

**Validation, all in the same disposable scratch clone:**

- `git -C src status --short` → **empty**.
- `git -C src diff --stat` → **empty**.
- `git -C src diff 7a3fa971304521cdcb44251e07ef1966baec686a -- .` (full
  content diff against the pinned commit) → **0 lines** — zero content
  drift.
- Full cross-check (Python, `git ls-tree -r <sha>` against
  `os.lstat` for all 4030 tracked paths): **0 mismatches** between
  each path's Git index mode and its resulting filesystem mode
  (`100644` → `0640`, `100755` → `0750`, verified for every single
  tracked path, not just the six originally exposed).
- `.githooks/pre-commit` and `scripts/check-docs-updated.sh`: `test -x`
  → **true** (remain invokable).
- `pyproject.toml` (representative `100644` file): `test -x` → **false**
  (remains non-executable).
- Rollback (unchanged from the original frozen rollback — this repair
  does not touch rollback): `rm -rf`; `mkdir -p`; `chmod 0750`;
  verified `find -mindepth 1 | wc -l` → `0`.
- Scratch directory disposed (`rm -rf`) immediately after validation.

No content bytes were altered by either the defect reproduction or the
repaired candidate at any point — both are pure filesystem-metadata
operations layered on an unmodified Git checkout.

## 7. Repair Selection Rationale

Three families of candidate were analyzed per governing instruction
§11:

1. **Preserve modes exactly as checked out, change ownership only**
   (drop both `find -type ... -exec chmod` lines entirely). Rejected:
   leaves files at whatever mode `git checkout` produces under the
   host's ambient umask (world-readable by default), failing the
   trust model's group-only access requirement (invariant 5/6 in §10
   of the governing instruction) — correct for tracked-mode
   preservation but silently drops a real hardening requirement the
   original Action 6 was also trying to satisfy.
2. **Normalize directory modes only, leave all tracked file execute
   bits untouched** — equivalent in effect to family 1 for files;
   same rejection.
3. **Deterministically map Git index `100644`/`100755` to approved
   filesystem modes `0640`/`0750`** (§6.3) — satisfies both the
   original hardening intent (group-only access, no world access) and
   tracked-mode preservation simultaneously, using only information
   already present on disk after checkout (no additional Git queries,
   no dependency on `core.fileMode` for correctness — the two `find
   -perm -u+x` branches key off the actual filesystem bit `git
   checkout` already wrote, which itself does depend on Git having
   applied the index mode during checkout — a Git guarantee
   independent of `core.fileMode`, which only affects *diff/status*
   interpretation, not what mode `checkout` writes).

**Selected: family 3 (§6.3).** It is the narrowest change to the
frozen forward command — two `find` invocations replace one, with
identical privilege, identical scope (`/opt/pcae/runtime/src` only),
and no new command classes introduced.

## 8. Continuation-Baseline Problem (Mandatory)

The next execution attempt does **not** begin from a fresh host with
Actions 1-5 absent. It begins from:

```
Actions 1-5: ALREADY PROVISIONED AND INDEPENDENTLY READ-BACK VERIFIED
             (by 7D.2, re-verified read-only by this phase, §9 below)
Action 6:    EMPTY — reverted to Action 4's own postcondition
             (root:pcae 0750, 0 entries) by 7D.2's own frozen rollback
Actions 7-9: NEVER ATTEMPTED
```

This is authority-bearing, not incidental: `chgr-96a0ce12756e4cc892
492a87af1db832`'s own `decision_subject` and `rationale` (verified
§13) authorize "the exact nine-action provisioning plan" **starting
from the entering state reconfirmed in that phase's own §4** — a host
with `pcae`, all target paths, and `/home/pcae` absent. The current
real host state is materially different (Actions 1-5 already done).
The original record does not, and cannot, distinguish "run all nine
actions against an absent-everything host" from "verify five
postconditions already met, then run four remaining actions" — it was
authorized against the former, not the latter. **This is not treated
as equivalent — Finding D3-2 (§10).** The amended proposition in §11
defines continuation gates precisely so a fresh human election can
knowingly authorize the latter.

## 9. Fresh Read-Only Dell Baseline Verification (This Phase)

```
$ ssh -o BatchMode=yes -o ConnectTimeout=8 hac-dell \
    "echo CONNECTED as $(whoami); cat /etc/machine-id; hostname; \
     . /etc/os-release; echo $PRETTY_NAME; dpkg --print-architecture"
CONNECTED as codex
54ff22ce400b475aa0d55cb68f4a3334
atila-Latitude-E5470
Ubuntu 24.04.3 LTS
amd64
```
Matches §3/§8's expected identity exactly.

| Action | Check | Result |
|---|---|---|
| 1 | `dpkg-query` python3-venv, python3-pip | both `install ok installed` |
| 2 | `id pcae` | `uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)`; shell `/usr/sbin/nologin` |
| 3 | `stat`/`getfacl` `/etc/pcae/hatp/trust-store` | `root:pcae 750`; only 3 standard POSIX ACL entries |
| 4 | `stat` all 8 paths under `/opt/pcae`, `/var/lib/pcae`, `/var/log/pcae` | all `root:pcae 750` |
| 5 | `stat` `/home/pcae` | `pcae:pcae 750` |
| 6 | `sudo find /opt/pcae/runtime/src -mindepth 1 \| wc -l` | `0` (empty, matches Action 4 postcondition) |
| 7 | `sudo find /opt/pcae/runtime/venv -mindepth 1 -maxdepth 1 \| wc -l` | `0` (absent/empty) |
| 8 | `test -e /opt/pcae/runtime/bin/pcae-launch` | non-zero exit (absent) |
| 9 | — | not run (no prior attempt to verify) |

Unrelated principals reconfirmed unchanged: `id atila`, `id
uosserver`, `id clawdbot` all match known baselines (`atila`
uid 1000 with `sudo`/`adm`/etc. groups; `uosserver` uid 1001 own
group; `clawdbot` uid 995, `devbots` group) — no PCAE-related group
membership drift.

Credential prerequisite (149O.20L.7D.1) reconfirmed unchanged and
read-only: `/root/.ssh/pcae_harness_deploy_ed25519` → `root:root 600`;
`/root/.ssh/config` `Host github.com` stanza → `IdentityFile
/root/.ssh/pcae_harness_deploy_ed25519` present, unmodified.

**Result: actual live state matches the claimed 7D.2 end-state and
§8's stated baseline exactly. No STOP required by §16 of the governing
instruction — proceeding to write the amendment against this
confirmed-accurate baseline.**

## 10. Required Adjudications

**Finding D3-1 — Action-6 file-mode defect.** Cause: the frozen
Action-6 forward command's final line
(`sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;`) is
unconditional and strips the executable bit from every tracked file
regardless of the file's own Git index mode, while the frozen
read-back requires `git status --short` to be exactly empty — a
repository tracking any executable file (this one tracks six, §5)
makes these two frozen requirements mutually unsatisfiable together.
Repaired semantics (§6.3, §11): replace the single unconditional
`chmod 0640` line with two branches keyed on each file's already-
correct on-disk executable bit (`git checkout` already applies the
Git index mode), mapping `100644`→`0640` and `100755`→`0750`
deterministically, preserving both tracked-executable and tracked-
non-executable semantics simultaneously while still hardening every
file to group-only access. Validated with zero content diff, zero
mode diff, and clean `git status --short` across all 4030 tracked
paths in disposable scratch (§6.3).

**Finding D3-2 — retained-baseline authority gap.** The original
authority (`chgr-96a0ce12756e4cc892492a87af1db832`) authorizes the
nine-action plan starting from the specific entering state
independently reconfirmed in 149O.20L.7B.1 §4 (a host with `pcae`,
target paths, and `/home/pcae` all absent). It does not, on its own
text, authorize resuming Actions 6-9 against a host where Actions 1-5
are *already* provisioned — a materially different starting
condition that record's own decision-maker never reviewed. Per
governing instruction §41 ("successful partial execution ≠ authority
to resume"), **the original authority is conservatively treated as
insufficient for continuation, even though Actions 1-5 were
themselves originally authorized and executed correctly.** A fresh
amended proposition (§11-§13) explicitly binds the retained
Actions-1-5 baseline as a stated precondition, subject to its own
continuation gates (§13), rather than silently treating "already
provisioned" as interchangeable with "freshly authorized to
provision."

**Finding D3-3 — CHGR supersession/lifecycle-transition machinery does
not yet exist (disclosed, addressed by textual precedence, not by an
invented mechanism).** `human_governance_record.schema.json` declares
optional `predecessor_record_id`/`successor_record_id` fields
("carried in the record itself, never inferred from filename or
timestamp ordering"), and a separate
`governance_record_lifecycle_event.schema.json` models an eight-state
lifecycle (`published`, `suspended`, `superseded`, `revoked`,
`invalidated`, etc.) — but that second schema's own description states
verbatim: *"No transition command exists this increment (Phase
143E) — this schema exists so the eight-state model and its linked
evidence can be structurally represented and tested without enabling
any lifecycle operation."* Independently confirmed against the CLI:
`pcae governance-record publish <package-id> --operator-id <id>` takes
no predecessor/successor/supersession argument and derives the
published record entirely from the decision-session's own confirmed
content (`src/pcae/commands/governance_record.py::run_governance_
record_publish` calls `PublicationApplicationService.resume_
publication(package_id, operator_id=...)` — package-id and operator-id
only); no CLI verb performs suspend/revoke/supersede on an existing
record. **Per governing instruction §33, this phase does not invent a
supersession mechanism the CLI does not provide, and does not hand-
edit `predecessor_record_id` into a record outside the canonical
publish flow.** Separately, `CANONICAL_HUMAN_GOVERNANCE_RECORD_
CONTRACT.md` §17 already establishes that *no* runtime path currently
gates any command's behavior on any CHGR's presence or state — CHGR
consumption is entirely representation-only today, for every record,
not specifically for supersession. Given that, the practical
precedence risk this phase must resolve is confined to a **human or a
future agent session** reading `.pcae/publication-execution/records/`
and being unable to tell which of two records governs — not an
automated/machine-checkable ambiguity, since nothing automated reads
these records today. This phase resolves that narrower risk the same
way `149O.20L.7B.1`/`7B.2` already resolved an analogous
re-presentation relationship: the new record's own `decision_subject`
and `rationale` text will explicitly name and supersede
`chgr-96a0ce12756e4cc892492a87af1db832` for continuation purposes
(§14), and this phase's canonical report / `PROJECT_STATUS.md` will
state the same in prose. **A dedicated future authority-model-repair
phase to implement the CHGR lifecycle-event transition command (so
future phases do not have to rely on textual-only precedence) is
recommended (§20) — this phase does not attempt that implementation
itself, since it would touch `src/pcae/**` and materially broaden this
phase's scope beyond proposition-repair.**

## 11. Repaired Exact Action-6 Section (Literal, No Discretion Left)

**Preflight (read-only, unchanged from the original):**
```
test -d /opt/pcae/runtime/src ; echo $?
sudo find /opt/pcae/runtime/src -mindepth 1 -maxdepth 1 2>&1
```
- Directory exists (from retained Action 4) and is empty →
  **ABSENT** (of a checkout): proceed to forward.
- Directory already contains a checkout whose `git rev-parse HEAD`
  equals `7a3fa971304521cdcb44251e07ef1966baec686a` exactly, whose
  `git remote get-url origin` equals
  `git@github.com:atimad/pcae-harness.git`, and whose `git status
  --short` is empty → **EXACTLY SATISFIED → NO-OP.**
- Directory non-empty and not matching the above exactly →
  **CONFLICTING → STOP.**

**Classification (new — precedes the forward mode-normalization
step):** none required beyond the preflight above; the repair applies
uniformly to every regular file under the checkout via the two `find
-perm -u+x` branches in the forward step, keyed on each file's own
on-disk bit as `git checkout` sets it — no separate manual
classification pass is needed.

**Forward (only if ABSENT) — repaired:**
```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```
Privilege: root (`sudo`, via `codex`). Precondition: retained Action 4
baseline verified (§13 continuation gate). Only the final two lines
differ from the original frozen text (§2) — one unconditional `chmod
0640` line replaced by two conditional lines keyed on the file's own
already-correct on-disk executable bit. Clone, checkout, and `chown`
lines are byte-identical to the original.

**Read-back (unchanged from the original — the repair makes this
requirement satisfiable, it does not weaken it):**
```
git -C /opt/pcae/runtime/src rev-parse HEAD
    → must equal 7a3fa971304521cdcb44251e07ef1966baec686a EXACTLY (full 40-char compare)
git -C /opt/pcae/runtime/src symbolic-ref -q HEAD ; echo $?
    → non-zero (detached HEAD, not on a branch)
git -C /opt/pcae/runtime/src status --short
    → empty (no local modifications) — now achievable per §6.3/§7
git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git
test -f /opt/pcae/runtime/src/docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md ; echo $?
    → 0
test -f /opt/pcae/runtime/src/src/pcae/core/hatp_class_b_conformance.py ; echo $?
    → 0
```
**New read-back addition — mode-preservation spot-check (defense in
depth beyond `git status --short` alone):**
```
sudo test -u /opt/pcae/runtime/src/.githooks/pre-commit -a -x /opt/pcae/runtime/src/.githooks/pre-commit ; echo $?
    → 0 (owned by root, owner-executable)
stat -c '%a' /opt/pcae/runtime/src/.githooks/pre-commit    → 750
stat -c '%a' /opt/pcae/runtime/src/pyproject.toml          → 640
```

**Rollback — unchanged from the original (this repair does not touch
rollback):**
```
sudo rm -rf /opt/pcae/runtime/src
sudo mkdir -p /opt/pcae/runtime/src
sudo chown root:pcae /opt/pcae/runtime/src
sudo chmod 0750 /opt/pcae/runtime/src
```
This `rm -rf` targets exactly one explicit, non-glob, already-owned-by-
this-action path.

**Rollback verification — unchanged from the original:**
```
sudo find /opt/pcae/runtime/src -mindepth 1 | wc -l   → 0
stat -c '%U:%G %a' /opt/pcae/runtime/src               → root:pcae 750
```

**Stop semantics — unchanged from the original:** any read-back line
not matching exactly → STOP, execute the rollback above, do not invent
a substitute command, disclose to the operator.

## 12. Repaired-Action-6 Invariant Checklist (§10 of the Governing Instruction)

1. Exact pinned source commit — unchanged, still
   `7a3fa971304521cdcb44251e07ef1966baec686a`. ✓
2. Detached HEAD — unchanged (`checkout --detach`). ✓
3. Clean Git working tree — **now achievable** (§6.3, §7). ✓
4. Intended root/pcae trust ownership — unchanged (`chown -R
   root:pcae`). ✓
5. Required directory protection — unchanged (`chmod 0750` on all
   directories). ✓
6. Tracked executable semantics preserved — **new**: `100755` → `0750`
   deterministically. ✓
7. Tracked non-executable semantics preserved — **new**: `100644` →
   `0640` deterministically. ✓
8. No untracked/unreviewed executable material introduced — the
   repair only ever sets `0750` on a file that `git checkout` already
   made owner-executable from the Git index; it never adds `+x` to
   anything the index did not already mark executable. ✓
9. No developer path leakage — unchanged; no absolute host-specific
   path appears in the repaired commands beyond the same
   `/opt/pcae/runtime/src` already used throughout. ✓
10. Deterministic GitHub deploy credential — unchanged, still the
    149O.20L.7D.1 credential, untouched by this amendment (§17). ✓
11. Rollback to exact Action-4 source-directory baseline — unchanged
    (§11 above). ✓

## 13. Continuation Semantics (Explicit)

**Continuation gates for Actions 1-5 (read-only verify only — do not
rerun their mutation commands):**

```
Action 1: dpkg-query -W -f='${Status}\n' python3-venv python3-pip
          → both must read exactly 'install ok installed'
Action 2: id pcae → must read exactly
          'uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)'; shell
          /usr/sbin/nologin; no sudo group membership (§14 below)
Action 3: stat -c '%U:%G %a' /etc/pcae/hatp/trust-store → root:pcae 750;
          getfacl -p /etc/pcae/hatp/trust-store → only 3 standard
          POSIX entries
Action 4: stat -c '%n %U:%G %a' over all 8 paths under /opt/pcae,
          /var/lib/pcae, /var/log/pcae → every line root:pcae 750
Action 5: stat -c '%U:%G %a' /home/pcae → pcae:pcae 750
```
If **any** retained postcondition differs from the exact values above:
**STOP. No repair under continuation authority** — return to a fresh
proposition/authorization phase; do not silently "fix" a drifted
Action 1-5 state as part of executing Action 6 onward.

**Execute repaired Action 6 (§11)** — only after all five continuation
gates above pass exactly.

**Then Actions 7-9 — execute their original frozen commands unchanged
(§2, §16 confirms no textual change is required)** — this is a new,
amended **continuation** plan (retained-baseline-aware), not a
re-execution of the original nine-action plan from an absent-
everything host, and not described as such in any future report.

## 14. Action-2 Continuation Adjudication (Explicit, Mandatory)

The original Action 2 has **no EXACTLY SATISFIED branch by design**
(§9 of the immutable plan: "There is no 'EXACTLY SATISFIED' idempotent
case for this action" — CONFLICTING → STOP is the only non-ABSENT
outcome under the *original* authorization). The current host,
however, already has a `pcae` principal — created correctly by 7D.2
under that same original authorization, not by any unauthorized or
out-of-band actor.

This amendment does **not** pretend the existing `pcae` principal is a
fresh-creation ABSENT state, and does **not** delete/recreate the
account merely to simulate that state. Instead: the current principal
is explicitly defined as a **required retained baseline**, verified
before continuation (§13's Action-2 gate) against the exact identity
7D.2 itself read back and this phase independently reconfirmed in §9
(`uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)`,
`/usr/sbin/nologin`, no `sudo`/other group membership). If that exact
identity does not match at continuation time: **STOP** — do not
delete/recreate the account under this amendment; that would require
a separately authorized, explicitly disclosed principal-recreation
proposition, not an implicit side effect of continuing Class-B
provisioning.

## 15. Actions 7-9 Change Determination

Actions 7 (venv + editable-install), 8 (launch wrapper), and 9 (final
conformance check) were independently re-read from the pinned
`f9e33232` commit (§2's citation method) and compared against: (a) the
Action-6 repair (§11), and (b) the retained-baseline continuation
semantics (§13). **Neither requires any textual change.** Action 7's
`ABSENT`/`EXACTLY SATISFIED`/`CONFLICTING` preflight, forward,
read-back, rollback are unaffected by how Action 6's file modes are
computed — Action 7 only depends on Action 6 having produced a clean
checkout at the pinned SHA (a postcondition, not a mechanism), which
the repair still produces. Action 8's wrapper creation is entirely
independent of the source checkout's own file modes (§17, §22 confirm
the wrapper digest itself is unaffected). Action 9's read-only
verifier invocation depends only on Actions 1-8 having completed, not
on any Action-6 internal command detail. **Determination: Actions 7-9
are bound into this amendment unchanged, verbatim from §2's citation —
no downstream change is hidden.**

## 16. Rollback Semantics From the Retained Baseline (Explicit)

- **Action-6 rollback** → returns to the retained Action-4/5
  baseline (§11's rollback, unchanged) — i.e., an empty, `root:pcae
  0750` `/opt/pcae/runtime/src`, exactly the state this phase found at
  entry (§9).
- **Action-7 rollback** → unchanged from the original frozen text
  (`rm -rf` the venv directory; recreate empty `root:pcae 0750`) —
  returns to the post-repaired-Action-6 state, not to Action 1-5.
- **Action-8 rollback** → unchanged from the original frozen text
  (single `rm` of the wrapper file) — always safe, no dependency
  chain.
- **Action-9** → read-only, no mutation, nothing to roll back.
- **Actions 1-5 are explicitly NOT automatically rolled back on any
  future Actions 6-9 failure.** The retained baseline is itself
  deliberate state (§8, §13) — a future execution phase's failure
  during Actions 6-9 rolls back only the specific action that failed
  (per that action's own rollback text above), leaving Actions 1-5
  provisioned and verified, exactly as this phase (and 7D.2 before it)
  leaves them. A full Actions-1-5 teardown would require its own
  explicit, separately authorized proposition — never an implicit
  consequence of an Actions 6-9 failure under this amendment.

## 17. Deployment Credential — External Prerequisite, Unchanged

The 149O.20L.7D.1 credential (`/root/.ssh/pcae_harness_deploy_
ed25519`, GitHub deploy key id `160313031`, read-only, repository-
scoped, root-only) remains persistent, outside Class-B infrastructure
mutation, and is **not** amended by this phase (§9 independently
reconfirmed it unchanged, read-only, this phase). The repaired Action
6 (§11) still consumes it via the identical `git clone
git@github.com:atimad/pcae-harness.git` invocation — no change to
repository URL, source identity, or credential-consumption mechanism.

## 18. Source SHA — Fixed, Unchanged

The amended proposition continues to deploy
`7a3fa971304521cdcb44251e07ef1966baec686a`. No evidence gathered this
phase demonstrates this is impossible or unsafe (§5's disclosed JSON-
mode anomaly does not affect deployability — see §5's own rejection of
repinning). No repin is proposed.

## 19. Wrapper and Action-9 Expectation — Reconfirmed Unaffected

Wrapper digest `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912
b1cfc3753c32` (§9/§12 of the pinned `f9e33232` commit) is unaffected
by the Action-6 repair — Action 8's wrapper-creation command sequence
is untouched by §11, and the wrapper's own content does not derive
from anything Action 6 computes. Bound unchanged.

`HBDC-REQ-042` reconfirmed this phase directly against the pinned
verifier source (`src/pcae/core/hatp_class_b_conformance.py`,
`_check_deployment_identity()`): the check's `satisfied: False`
outcome is driven exclusively by `no_active_deployment_binding_
matches_repository_and_root` / `no_repository_identity_present` — i.e.
by the intentional absence of a `DeploymentBinding`, never by any
file-mode state under `/opt/pcae/runtime/src`. Action 6's mode repair
has no bearing on this check. Expectation preserved unchanged: Action
9's aggregate result remains expected `NON_COMPLIANT`, driven **only**
by `{HBDC-REQ-042}`.

## 20. Recommended Future Authority-Model Repair (Disclosed, Not Performed This Phase)

Per Finding D3-3 (§10): a future, separately scoped and separately
authorized phase should implement a canonical CLI transition command
for `governance_record_lifecycle_event` (suspend/supersede/revoke),
wiring `predecessor_record_id`/`successor_record_id` so future
amendment phases do not have to rely on textual-only precedence
between two published, un-linked `human_governance_record` artifacts.
This phase does not implement that command (it would touch
`src/pcae/**`, materially broadening this phase's proposition-only
scope) and does not invent an ad hoc substitute for it.

## 21. Exclusions (Explicit, Preserved)

- **No DeploymentBinding** creation, mutation, or publication — the
  repaired Action 6 (§11) makes no reference to one.
- **Boundary C: NOT AUTHORIZED. Boundary A: NOT AUTHORIZED.** No HMIC
  certification. No HATP_MANDATORY activation. No Cutover Record.
- **Permission Broker, POL-005, COMP-002, arbitrary repository
  onboarding, `/opt/pcae/projects/<repo-slug>/repo`, and centralized
  multi-repository governance** remain excluded — none is named,
  touched, or implied by this amendment.
- **No Dell mutation this phase.** All Dell interaction (§9) was
  read-only SSH; no clone, chmod, package install/uninstall, user/
  group change, directory alteration, venv creation, wrapper creation,
  or repair command was executed against the Dell host.
- **No production/contracts modification.** `src/pcae/**`,
  `scripts/**`, and `docs/contracts/**` are unmodified by this phase —
  confirmed via `git diff --stat` at phase close (§23 of the final
  report).

## 22. Relationship to the Existing CHGR

`chgr-96a0ce12756e4cc892492a87af1db832` was validly published and
independently verified before 7D.2's execution attempt (§13 of the
final report re-confirms `pcae governance-record verify` still reports
`outcome: verified`, digest unchanged). It remains part of the
historical execution chain and is **not** rewritten, revoked, or
declared intrinsically invalid by this phase. However, because (a)
Finding D3-1 requires materially amending Action 6's own command text,
and (b) Finding D3-2 requires binding a retained-baseline continuation
precondition the original record's decision-maker never reviewed,
further execution must rely on a **new** canonical authority artifact
that binds the corrected plan — not a silent reinterpretation of the
existing record. Per Finding D3-3, no canonical in-place transition or
machine-checkable linkage mechanism exists yet; precedence is
established textually: the new record's own `decision_subject` and
`rationale` will state explicitly that it supersedes
`chgr-96a0ce12756e4cc892492a87af1db832` for the purpose of authorizing
any future Actions 6-9 retry, and this phase's canonical report /
`PROJECT_STATUS.md` will state the same.

## 23. The Complete Bounded Proposition Being Presented for Election

Everything above (§1-§22) constitutes the single, complete, bounded
proposition presented to the human governance authority in §24 for
election — not an isolated diff fragment. It contains: the exact Dell
machine-id (§9); the current retained Actions-1-5 baseline (§8-§9);
the exact deploy-credential prerequisite relationship (§17); the
pinned source SHA (§18); the repaired exact Action-6 commands,
read-back, and rollback (§11); continuation semantics (§13); the
Action-2 continuation adjudication (§14); Actions 7-9 unchanged
determination (§15); rollback semantics from the retained baseline
(§16); the wrapper digest and `HBDC-REQ-042` semantics (§19); all
stop conditions (§11, §13, §14); DeploymentBinding/Boundary-C/
Boundary-A/onboarding/centralization exclusions (§21); and the
relationship to the original CHGR (§22).

## 24. Human Election

See the final phase report (§ "Human Election and Confirmation") for
the exact decision-session ID, the exact human selection recorded via
`pcae decision-session select`, and the exact separately-confirmed
preview digest via `pcae decision-session confirm`. No default is
assumed; no prior approval, request-to-run, or agreement that the
original command was defective is treated as this election.

## 25. Companion Tests

`tests/test_phase_149o_20l_7d_3_action_6_file_mode_continuation_
baseline_proposition_amendment.py` — see the final phase report for
the full coverage list and the pass count.

## 26. Boundary Status After This Phase (Expected, Pending Election)

```
Actions 1-5: PROVISIONED — RETAINED BASELINE VERIFIED
Action 6:    REPAIRED PROPOSITION AUTHORIZED — NOT YET EXECUTED
             (pending human election, §24)
Actions 7-9: NOT YET EXECUTED
Boundary P:  AMENDED CONTINUATION AUTHORIZED — INDEPENDENT
             AUTHORIZATION VERIFICATION PENDING (pending election)
Class-B:     PARTIALLY PROVISIONED — CONTINUATION NOT YET EXECUTED
DeploymentBinding: ABSENT / NOT AUTHORIZED
Boundary C:  NOT AUTHORIZED
Boundary A:  NOT AUTHORIZED
HATP:        NOT READY
Runtime:     Observed / observe / unavailable
```

## 27. Governance

Normal governed PCAE lifecycle used throughout — `pcae task`,
`pcae commit implementation`, `pcae phase complete`, `pcae push`. No
raw `git commit`/`git push`, no `--no-verify`, no force push, no
governance bypass.

## 28. Recommended Next Phase

**149O.20L.7D.4 — Action-6 + Continuation-Baseline Amendment
Independent Verification.** Must independently attack: the repaired
Action-6 commands (§11); scratch reproduction and mode-mapping
correctness (§6); source-mode preservation across all 4030 tracked
paths, not just the six originally exposed; the retained Actions-1-5
baseline (§8-§9); continuation semantics (§13); Action-2 continuation
adjudication (§14); rollback semantics (§16); the human election and
separate confirmation (§24); the new authority artifact and its
relationship to `chgr-96a0ce12756e4cc892492a87af1db832` (§22, Finding
D3-3); and confirm no ambiguity remains before recommending
**149O.20L.7D.5 — Dell Class-B Provisioning Continuation Execution**
(execute the repaired Action 6, then Actions 7-9, only after clean
independent verification).
