# Phase 149O.20L.7D.4 — Action-6 + Continuation-Baseline Amendment Independent Verification

## 0. Phase Identity and Type

**Phase:** 149O.20L.7D.4
**Type:** INDEPENDENT VERIFICATION ONLY. Does **not** execute repaired
Action 6. Does **not** execute Actions 7-9. Does **not** rerun Actions
1-5. Does **not** mutate Dell Class-B infrastructure. Does **not**
create a DeploymentBinding. Does **not** certify. Does **not**
activate. All Dell interaction this phase is read-only SSH.
**Basis:** Phase 149O.20L.7D.3 (Action-6 file-mode + continuation-
baseline proposition amendment); CHGR
`chgr-541cb08c313b4f8884970172d37c5a1d`; historical CHGR
`chgr-96a0ce12756e4cc892492a87af1db832`.

## 1. Methodology

Every claim in this report is independently re-derived from a primary
artifact — the immutable 149O.20L.7B.1 commit
(`f9e33232c83163aad5e50bc94db7cab51b844ac5`), the 149O.20L.7D.2 and
149O.20L.7D.3 phase docs (read as primary execution/amendment records,
not paraphrased), the two CHGR JSON artifacts, the decision-session
JSON artifacts (session + orchestration), the production source
(`src/pcae/core/hatp_class_b_conformance.py`,
`src/pcae/commands/governance_record.py`, `src/pcae/cli.py`), and
disposable local scratch clones of this repository — never the
149O.20L.7D.3 companion test module, and never 7D.3's prose
conclusions taken on faith. Where 7D.3's own conclusions are cited
below, they are cited only after being independently re-derived and
found to match.

## 2. Entry Checks (Read-Only)

**True phase-entry commit:** `119eeba06765ebb470a5e758c28f07a04eb152fa`
(`origin/main` tip at phase entry; `git rev-list --count
origin/main..HEAD` → `0`).

```
$ pcae health                       → healthy
$ pcae check                        → passed
$ pcae status coherence             → coherent
$ pcae doctor task-memory           → warnings (pre-existing, historical
                                        tasks/done/ pileup predating this
                                        phase by ~30+ prior phases; unrelated;
                                        not remediated here, matching 7D.2/
                                        7D.3's own disclosure of the same
                                        debt)
$ pcae push check                   → clean (nothing_to_push)
$ pcae runtime inspect              → Observed / observe / unavailable
$ pcae notify status                → Telegram configured/enabled
$ pcae phase-report show --latest   → 149O.20L.7D.3's canonical report,
                                        consistent; recommends this phase
$ pcae phase-report reconcile --phase-id 149O.20L.7D.3
                                     → status: reconciled, mutation: none
                                       (inspection only)
```

All reconciliation was read-only. No prior phase artifact was mutated.

## 3. Independent Reconstruction of 7D.2 (Section 4 of the Governing Instruction)

Read directly from `docs/PHASE_149O_20L_7D_2_DELL_CLASS_B_REAL_HOST_PROVISIONING_EXECUTION_RETRY.md`
(7D.2's own primary execution record, not 7D.3's summary of it):

- Entering state: absent-everything host, matching the original CHGR's
  authorized entering state exactly.
- Actions 1-5 executed and read back exactly as frozen: packages
  installed; `pcae` principal freshly issued (`uid=1004 gid=1004
  groups=1004`, `/usr/sbin/nologin`, no sudo); Protected Root and all 8
  runtime/state paths `root:pcae 0750`; `/home/pcae` `pcae:pcae 0750`.
- Action 6: clone + detached checkout at the pinned SHA succeeded;
  `chown -R root:pcae` and the two frozen `find`/`chmod` lines ran
  exactly as written; the read-back's clean-working-tree requirement
  (`git status --short` empty) **failed** with exactly six mode-only
  modifications (`.githooks/pre-commit`, `.githooks/pre-push`, three
  `.pcae/**` JSON artifacts, `scripts/check-docs-updated.sh`), `git
  diff --stat` confirming `0 insertions(+), 0 deletions(-)`.
- No substitute command was invented; STOP was declared at Action 6's
  read-back gate; the frozen rollback (`rm -rf`; `mkdir -p`; `chown`;
  `chmod 0750`) was executed and independently verified empty,
  `root:pcae 0750`.
- Actions 7-9 were not attempted.
- The CHGR (`chgr-96a0ce12756e4cc892492a87af1db832`) was reconfirmed
  unchanged, digest-stable, not marked consumed.

This reconstruction matches 7D.3's own citation of 7D.2 exactly — no
discrepancy found between 7D.2's primary record and 7D.3's summary of
it.

## 4. Independent Reconstruction of the Original Action 6 (Section 5)

Recovered directly from the immutable commit
`f9e33232c83163aad5e50bc94db7cab51b844ac5`
(`git show --stat --name-only` → exactly two files, the 7B.1 doc and
its companion test, 1490 insertions, nothing else — independently
reconfirmed, not merely cited):

**Original forward command (verbatim, §9 "Action 6" of that commit):**
```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -exec chmod 0640 {} \;
```
Preflight (ABSENT/EXACTLY SATISFIED/CONFLICTING), read-back (full
40-char SHA compare, detached-HEAD check, empty `git status --short`,
remote URL, two file-presence checks), rollback (`rm -rf`; `mkdir -p`;
`chown`; `chmod 0750`), and stop semantics were all extracted directly
from this commit, not from any later paraphrase — reproduced verbatim
in the companion test module
(`test_original_action_6_forward_command_is_unconditional_chmod`,
`test_repaired_action_6_rollback_unchanged_from_original`). The
forward command's final line is unconditional — it does not consult
any file's own Git-index mode.

## 5. Independent Defect Reproduction (D3-1) — Disposable Scratch

A disposable local clone of this repository (`git clone --no-checkout
~/repos/pcae-harness <scratch>; git checkout --detach 7a3fa971...`,
outside any tracked or production path, destroyed after use) was used
to independently re-run the **original** frozen forward command's two
`find`/`chmod` lines:

```
$ git status --short
 M .githooks/pre-commit
 M .githooks/pre-push
 M .pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json
 M .pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json
 M .pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json
 M scripts/check-docs-updated.sh
$ git diff --stat → 6 files changed, 0 insertions(+), 0 deletions(-)
$ git diff .githooks/pre-commit → old mode 100755 / new mode 100644
```

Exact match to both 7D.2's live-Dell evidence and 7D.3's own scratch
reproduction — independently confirmed, not assumed. Companion tests:
`test_defect_reproduces_in_disposable_scratch`,
`test_defect_reproduction_files_match_claimed_six_paths`.

## 6. Complete Tracked-Mode Inventory (Section 7) — Independently Enumerated

```
$ git ls-tree -r 7a3fa971304521cdcb44251e07ef1966baec686a | awk '{print $1}' | sort | uniq -c
    4024 100644
       6 100755
$ git ls-tree -r 7a3fa971... | wc -l   → 4030
```
Zero `120000` (symlink) entries, zero `160000` (submodule) entries.
**Independently confirmed: 4030 tracked paths, 4024×100644, 6×100755,
0 symlinks, 0 submodules — exact match to 7D.3's claimed inventory.**

## 7. The Six Executable Paths (Section 8)

```
$ git ls-tree -r 7a3fa971... | grep '^100755'
.githooks/pre-commit
.githooks/pre-push
.pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json
.pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json
.pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json
scripts/check-docs-updated.sh
```
Exact match to 7D.3's disclosed set. Two Git hooks and one directly-
invoked shell script are correctly executable — a repository shipping
non-executable hooks/scripts would itself be the defect. The three
JSON governance-record artifacts' `100755` mode is a pre-existing,
disclosed, unrelated cosmetic anomaly (not caused by, or a cause of,
the Action-6 defect); this phase does not repin the source or hand-
edit these files to "fix" them — the pinned Git tree is the
deployment-source authority, and no independent evidence establishes
a production defect requiring repair. **The amended mapping correctly
preserves all six as executable** (§8-9 below), not merely the three
that are executed code.

## 8. Repaired Action 6 — Exact Text, Independently Extracted (Section 9)

From `docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md`
§11 (literal, no paraphrase):

```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```

Independently diffed against §4's original text: the clone, checkout,
and `chown -R` lines are byte-identical; only the final unconditional
`chmod 0640` line is replaced by two lines conditioned on
`-perm -u+x`. Read-back, rollback, and stop semantics are unchanged
text, with one addition — a mode-preservation spot-check
(`stat -c '%a' .githooks/pre-commit → 750`;
`stat -c '%a' pyproject.toml → 640`).

## 9. Mode-Mapping Algorithm Attack (Section 10)

All attacks below ran against disposable scratch clones, never
production, and are encoded in the companion test module.

- **Checkout-umask effects:** re-cloned and checked out under a
  restrictive `umask 077`. `git checkout` still wrote the owner-
  executable bit from the Git index regardless of umask
  (`.githooks/pre-commit` → `0700`; `pyproject.toml` → `0600`) — only
  group/other bits were affected by umask, confirming the two
  `-perm -u+x` branches key off a Git guarantee, not an ambient
  filesystem default. Repaired sequence still produced empty `git
  status --short` under this umask. (`test_repair_robust_under_restrictive_umask`)
- **`core.fileMode`:** confirmed `true` in this repository
  (`git config core.fileMode`); the repair's correctness does not
  depend on this setting — it depends only on the on-disk bit
  `git checkout` writes, which `core.fileMode` does not affect
  (`core.fileMode` governs `diff`/`status` interpretation, not what
  `checkout` writes).
- **Branch-ordering correctness (Section 11, deserving explicit
  proof):** the first branch (`-perm -u+x`) sets `0750` only on files
  that already satisfy `-perm -u+x`; `chmod` on a matched file cannot
  alter the mode of any *other*, unmatched file. Independently proved
  by snapshotting every regular file's owner-exec bit before the first
  branch runs and again immediately after, before the second branch
  runs: **the two snapshots are identical for every one of the 4030
  files** — the first branch neither adds nor removes `u+x` on any file
  it does not itself match, so the second branch's `! -perm -u+x`
  predicate always sees the same classification it would have seen
  before the first branch ran. No cross-classification is possible by
  construction, not merely by observation.
  (`test_branch_order_cannot_cross_classify_files`)
- **Ordering exhaustiveness:** every file is `-perm -u+x` or
  `! -perm -u+x` — the two branches partition all 4030 regular files
  with no gap and no overlap; independently confirmed by the zero-
  mismatch full-inventory cross-check (§10 below).
- **Untracked files / directories:** `git status --porcelain --ignored`
  on the freshly-checked-out scratch clone returned zero untracked
  entries before any mode command ran; `find -type f` and
  `find -type d` are disjoint by `find`'s own type predicate, so no
  directory is ever mode-mapped by the file-mode branches.
- **Partial-failure / race behavior (Section 18):** Action 6's rollback
  (`rm -rf` the entire target directory, unconditionally) does not
  depend on which of the six forward-command lines completed. A
  failure after `chown` but before either `find` branch, after the
  first branch but before the second, or mid-branch, all leave
  `/opt/pcae/runtime/src` in a state fully covered by an unconditional
  `rm -rf` of that one explicit, non-glob, already-owned path — rollback
  safety does not depend on which partial mode state was reached.
  (`test_rollback_returns_to_empty_0750_directory`)

## 10. Mode-Mapping Verification (Section 12) — Full Inventory, Not Spot-Check

Independent Python cross-check (`git ls-tree -r` index modes vs.
`os.lstat` filesystem modes for all 4030 tracked paths, after applying
the repaired sequence to a fresh disposable scratch clone):

```
total checked: 4030
mismatches:    0
```
`100644 → 0640` and `100755 → 0750` hold for **every** tracked path,
not only the six originally exposed by `git status`. All directories
independently confirmed `0750`. Companion tests:
`test_repaired_sequence_zero_mode_mismatch_across_all_4030_paths`,
`test_repaired_sequence_all_directories_are_0750`.

## 11. Clean Git Semantics (Section 13)

```
$ git status --short          → (empty)
$ git diff --stat             → (empty)
$ git diff 7a3fa971... -- .   → 0 lines (zero content diff)
$ git status --porcelain --ignored | grep '^??' | wc -l  → 0 (no untracked)
```
Detached HEAD confirmed via `git symbolic-ref -q HEAD` (non-zero exit,
unchanged from the original); exact pinned HEAD confirmed via
`git rev-parse HEAD`. **Clean Git semantics: PASSED, independently.**

## 12. Content Identity (Section 14)

`git diff <pinned-sha> -- .` in the repaired scratch clone produced
**zero lines** — no content mutation is hidden behind the file-mode
repair; both the defect reproduction and the repair are pure
filesystem-metadata operations layered on an unmodified checkout.
(`test_repaired_sequence_produces_clean_status_and_zero_content_diff`)

## 13. Executable Behavior (Section 15)

- `.githooks/pre-commit`, `.githooks/pre-push`,
  `scripts/check-docs-updated.sh`: `os.access(..., os.X_OK)` → `True`
  after the repair.
- `pyproject.toml` (representative `100644` file): `os.access(...,
  os.X_OK)` → `False`.
- No path is silently special-cased beyond the deterministic
  index-mode mapping itself.

## 14. Ownership/Trust Semantics (Section 16)

The repair's `chown -R root:pcae` line is byte-identical to the
original — not independently re-derivable in local scratch (scratch
runs as the invoking Mac user, not root, and targets no production
path). Verified instead against the **live Dell host** (§16 below):
Protected Root and all runtime/state paths remain `root:pcae 0750`
with only standard POSIX ACL entries (`getfacl -p`); no world/group-
write anywhere; `pcae` has no writable authority-bearing source path.

## 15. Rollback Verification (Section 17)

Repaired sequence applied to disposable scratch, then the frozen
rollback (`rm -rf`; `mkdir -p`; `chown` would require root, so this
step used the unprivileged equivalent `mkdir` + `chmod 0750`,
sufficient to verify the postcondition's mode/emptiness shape — the
`chown root:pcae` step itself is independently reconfirmed live on
Dell, §16):

```
$ find <scratch> -mindepth 1 | wc -l   → 0
$ stat -f '%p' <scratch>                → 40750 (0750)
```
Matches Action 4's own postcondition exactly. No residue.
(`test_rollback_returns_to_empty_0750_directory`)

## 16. Live Dell Read-Only Baseline Reverification (Sections 19-22)

Independent read-only SSH this phase (no prior-phase assertion taken
on faith):

```
$ ssh hac-dell "cat /etc/machine-id; hostname; . /etc/os-release; echo $PRETTY_NAME; dpkg --print-architecture"
54ff22ce400b475aa0d55cb68f4a3334
atila-Latitude-E5470
Ubuntu 24.04.3 LTS
amd64
```
Exact match.

| Action | Independent check this phase | Result |
|---|---|---|
| 1 | `dpkg-query -W` python3-venv, python3-pip | both `install ok installed` |
| 2 | `id pcae` | `uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)`, `/usr/sbin/nologin` |
| 3 | `stat`/`getfacl` `/etc/pcae/hatp/trust-store` | `root:pcae 750`; 3 standard POSIX ACL entries |
| 4 | `stat` all 8 paths under `/opt/pcae`, `/var/lib/pcae`, `/var/log/pcae` | all `root:pcae 750` |
| 5 | `stat` `/home/pcae` | `pcae:pcae 750` |
| 6 | `find /opt/pcae/runtime/src -mindepth 1 \| wc -l`; no `.git` metadata | `0`; `root:pcae 750`; no hidden checkout |
| 7-9 | `find /opt/pcae/runtime/venv`; `test -e .../pcae-launch` | both absent |

Unrelated principals reconfirmed unchanged: `atila` (uid 1000, groups
include `sudo`/`adm`/etc.), `uosserver` (uid 1001, own group),
`clawdbot` (uid 995, group `devbots`) — no PCAE-related drift.

**Source credential prerequisite (Section 22):** `/root/.ssh/pcae_harness_deploy_ed25519`
`root:root 600`, `.pub` `root:root 644`; `/root/.ssh/config` `Host
github.com` stanza present, unmodified; 3 `github.com` entries in
`known_hosts`; auth-only handshake (`Hi atimad/pcae-harness! ...
GitHub does not provide shell access`) succeeded, no push attempted;
independently re-queried from the Mac via `gh api
repos/atimad/pcae-harness/keys` → `id: 160313031`, `read_only: true`,
`verified: true`, `enabled: true`, `added_by: atimad` — unchanged. No
private key bytes read or reported.

**Result: live state matches the claimed 7D.2/7D.3 baseline exactly.
No STOP required. No Dell mutation performed — every command above was
read-only (`stat`, `find`, `id`, `getfacl`, `dpkg-query`, `test -e`,
`ssh -T` auth handshake).**

## 17. D3-2 Independent Adjudication (Sections 23-27)

The original CHGR's `decision_subject`/`rationale`
(`.pcae/publication-execution/records/chgr-96a0ce12756e4cc892492a87af1db832.json`)
cites "the exact nine-action provisioning plan" via the 7B.1/7B.2
proposition; that proposition's own §4 ("Minimal Live Dell
Reconfirmation") independently confirms the entering-state assumption
it was authorized against: `pcae` absent, all target paths absent,
`/home/pcae` absent — an absent-everything host. The current retained
baseline (Actions 1-5 already provisioned) is a materially different
starting condition that record's decision-maker never reviewed.

**Independent textual proof the old plan cannot literally proceed from
today's state:** the original Action 2 preflight (§9 of the 7B.1
commit) has explicitly **no EXACTLY SATISFIED branch** — "Either exit
zero (exists) → CONFLICTING → STOP. No reuse, no silent adoption,
regardless of whether the existing account's properties happen to
match." Since `pcae` already exists on the live host, an operator
literally executing the old plan's own frozen action graph "exactly
... in the stated order" (per the CHGR-cited §19 proposition text)
would be **stopped at Action 2**, before Action 6 is ever reached —
this is a textual, machine-/operator-visible precondition embedded in
the plan the old CHGR itself cites, not merely a conservative
inference layered on afterward. **Answer to the required question: No
— the old CHGR cannot validly authorize execution from the current
retained baseline without reinterpretation; its own frozen Action 2
would STOP first.**

The current retained-baseline binding (7D.3 §8-§9, §13) is therefore
correctly treated as a fresh, explicitly-gated continuation
precondition, not an implicit consequence of "successful partial
execution." Continuation gates (7D.3 §13) are read-only (no mutation
commands re-run), exact (literal expected values, not ranges),
sufficient (cover all five retained postconditions), and fail-closed
(any mismatch → STOP, no silent repair). Section 26 (baseline-drift
attack): because these gates are explicitly bound to "verify... do not
rerun," any future 149O.20L.7D.5 must re-run them immediately before
mutation — the gates are a re-verification step, not a one-time check
consumed by this phase.

## 18. Action-2 Continuation Attack (Section 24 detail)

Executing the old plan literally from current state would **fail** at
Action 2's explicit CONFLICTING→STOP (§17 above) — not collide, not
require deletion/recreation under the old plan's own text (deletion is
never proposed by the original Action 2's CONFLICTING branch; it is
simply STOP). The new amendment's §14 explicitly forbids treating the
retained `pcae` principal as either a fresh-ABSENT state or a
delete/recreate target — it is bound as a required retained baseline,
itself gated (§13's Action-2 gate: exact `uid=1004 gid=1004
groups=1004`, `/usr/sbin/nologin`, no other group). This independently
confirms 7D.3's adjudication and adds the textual "old plan
structurally cannot skip Action 2" proof as new evidence not present
in 7D.3's own report.

## 19. Actions 7-9 Unchanged (Sections 6, 27)

Independently re-read Actions 7 (venv + editable install), 8 (wrapper
creation), 9 (read-only conformance check) from the immutable
`f9e33232` commit and diffed against 7D.3 §15's citation: no textual
change in either. Action 7's preflight/forward/read-back/rollback
depend only on Action 6 having produced a clean checkout at the pinned
SHA (a postcondition), not on how file modes were computed. Action 8's
wrapper content is independent of the source checkout's file modes.
Action 9 depends only on Actions 1-8 having completed.

## 20. Wrapper Digest and HBDC-REQ-042 (Sections 28-29)

**Wrapper digest:** independently reconstructed the exact 9-line,
188-byte script content from the immutable 7B.1 commit and recomputed
SHA-256 locally:
```
$ shasum -a 256 <reconstructed wrapper>
b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
```
Exact match, byte-for-byte, to the expected digest. The Action-6
repair does not touch Action 8's command sequence or the wrapper's own
content — unaffected.

**HBDC-REQ-042:** independently re-read directly from
`src/pcae/core/hatp_class_b_conformance.py::_check_deployment_identity`
— the check's only two failure reasons are
`no_repository_identity_present` and
`no_active_deployment_binding_matches_repository_and_root`; neither
references any file-mode, `chmod`, or executable-bit state anywhere in
the function. **Independently confirmed: driven exclusively by
DeploymentBinding absence, architecturally predicted, not a measured
Dell postcondition yet** — this remains a prediction until a future
Action 9 run, and any future execution must STOP on any *additional*,
unexpected HBDC failure beyond `{HBDC-REQ-042}`.

## 21. Exclusion Verification (Sections 30-32)

`chgr-541cb08c313b4f8884970172d37c5a1d`'s own `conditions` field
(authority-bearing text, independently read) lists, verbatim: Action 6
execution, Actions 7-9 execution, any rerun of Actions 1-5, any Dell
Class-B mutation, DeploymentBinding creation, Boundary C certification,
Boundary A activation, HATP_MANDATORY activation, Cutover Record
creation, Permission Broker changes, POL-005, COMP-002, arbitrary
repository onboarding, and centralized multi-repository governance —
all thirteen exclusions independently confirmed present, verbatim, in
the record's own conditions text (not merely in phase-report prose).
`find .pcae -iname '*deploymentbinding*'` (case-insensitive, both
casings) → zero matches anywhere in the repository.

## 22. Decision Session Reconstruction (Sections 33-35) — Including a Correction to the Governing Instruction's Own Cited Session ID

**Finding (independently discovered this phase, not present in any
prior phase's report):** the governing instruction for this phase
named `CDS-8984cecc-4b55-4cfc-aca6-14397f5735a1` as "the" decision
session. Independent inspection of that session
(`.pcae/decision-sessions/CDS-8984cecc-....json`) shows
`session_state: "Confirmed"` with an explicit APPROVE — but
cross-checking `PROJECT_STATUS.md`'s "Current Phase" entry (a primary,
independently-consultable artifact) revealed this session's own
`decision_subject` (500+ chars) **exceeded the CHGR schema's 500-
character `decision_subject` limit**, and every one of its three
publication attempts
(`.pcae/publication-execution/attempts/pubexec-{53ef215a,c2a19ea0,
cbacf5c6}...json`) independently confirmed `success: false`,
`record_id: null`, with `failure_reason` citing exactly
`ChgrSchemaConformanceError` at `/decision_subject`. Its own
readiness package (`prp-e1dbe29743f743c5b5ccd6880cb7446b`) remains in
`.pcae/decision-sessions/pending-packages/` — **never** moved to
`pending-packages/consumed/`. **This session did not, and could not
have, produced the published CHGR — it is Confirmed-but-unpublished, a
superseded evidentiary artifact, not the governing election.**

**The actually-governing session, independently resolved from the
publication-execution attempt record that succeeded**
(`.pcae/publication-execution/attempts/pubexec-ae9ef04551cb466993b98d678a33b608.json`
— `success` implied by `record_id:
chgr-541cb08c313b4f8884970172d37c5a1d` matching the published record
exactly, `session_id: CDS-554c3c12-0693-4edd-867d-b86374c376b2`,
`package_id: prp-f7d04d6a3918448fae4edbac22e4842e`, which **is**
present in `pending-packages/consumed/`), is
**`CDS-554c3c12-0693-4edd-867d-b86374c376b2`**. This is the session
this report verifies below. This is exactly the authority-wall
distinction "published ≠ independently verified": the CHGR being
published is a fact about the record; which session produced it is a
separate fact that must be resolved from the publication-execution
artifacts themselves, not merely from whichever session ID prose
happens to cite.

`.pcae/decision-sessions/CDS-554c3c12-0693-4edd-867d-b86374c376b2.json`
independently inspected: `session_state: "Confirmed"`,
`human_selection_id: "approve"`, `options_presented: ["approve",
"decline", "amend"]` — a real three-way choice, not a single-option
rubber stamp. `human_rationale_text` and `human_conditions_text` match
the published CHGR's `rationale`/`conditions` verbatim. Its
`subject_ref` (the corrected, shortened text) matches the published
CHGR's own `decision_subject` **exactly**, character for character —
independent confirmation this is the record-producing session.

**Separate confirmation, independently verified via the orchestration
record** (`.pcae/decision-sessions/orchestration/CDS-554c3c12-....json`):
- `last_preview.preview_timestamp`: `2026-08-15T07:52:41Z`.
- `confirmation_responses[0].confirmed_at`: `2026-08-15T07:54:35Z` —
  **strictly later** than the preview timestamp, confirming preview
  construction and confirmation were temporally distinct steps, not a
  single combined action.
- `confirmation_requests[0].preview_digest` ==
  `confirmation_responses[0].preview_digest` ==
  `61499f38a196003eebc1533b95a2e07618682c9b0a862925489c52bb6d662526`,
  and `confirmation_requests[0].preview_id` ==
  `last_preview.preview_id` == `prev-9082693cb1d64d639a4d380d8b197e24`
  — the confirmed digest is bound to the exact rendered preview, not
  inferred.
- `confirmation_responses[0].metadata.statement` explicitly names both
  `preview_id` and `digest`, **and explicitly discloses the prior
  attempt's failure**: "re-rendered under a corrected subject-ref after
  the first attempt's decision_subject exceeded the CHGR schema's
  500-char limit" — the two-attempt history is disclosed in the human's
  own recorded confirmation text, not hidden.

**Proposition completeness:** `last_preview.rendered_content`
independently inspected — it embeds the Dell machine-id, "repaired
Action-6," "retained Actions-1-5," and "does not authorize execution"
verbatim, and `last_preview.evidence_refs` cites all three governing
docs (7B.1, 7D.2, 7D.3) by path, not a short summary. **No inferred
confirmation; the preview bound the complete proposition.**

Companion test:
`test_published_chgr_is_bound_to_the_correct_session_not_the_superseded_one`
— independently resolves the session-to-record binding from the
publication-execution attempt records and package-consumption state,
confirming the superseded session's package was never consumed and
every one of its attempts failed with `record_id: null`.

## 23. New CHGR Reconstruction (Section 36)

`chgr-541cb08c313b4f8884970172d37c5a1d` independently inspected:
`lifecycle_state: published`; `selected_option_id: approve`;
`decision_subject` names the exact Dell target and cites 7D.3 by path;
`rationale` (quoted in full in §21/§24); `conditions` (§21);
`decision_maker_identity_evidence.identifier: "Atila Madai"`,
`evidence_kind: typed_confirmation_only`, `captured_at:
2026-08-15T07:54:35Z`; `confirmation_evidence_ref` /
`provenance_ref` / `integrity_ref` all point to persisted, resolvable
artifacts (not dangling references) — confirmed by resolving each and
supplying them to `pcae governance-record verify --related`.

## 24. New CHGR Verification (Section 37) — Re-Run Independently

```
$ pcae governance-record verify chgr-541cb08c313b4f8884970172d37c5a1d.json \
    --related chgrconf-c8d3e0b12eb34958af6f93135c4f5970.json \
    --related chgrprov-478806423b9e4f3786b7385733a99bb4.json \
    --related chgrintg-cb6d788751e74d9d99c09b9869b6ad2a.json
outcome: verified
  schema_shape                 passed
  digest_self_consistency      passed
  lifecycle_structural_legality passed
  confirmation_binding         passed
  assurance_truthfulness       passed
  provenance_consistency       passed
  integrity_consistency        passed
  template_resolution          skipped (no matching related template supplied)
```
Every substantive check independently re-run this phase (not cited
from 7D.3) and adjudicated: 6 passed, 1 skipped (template not
supplied — representation-only, non-authoritative per the tool's own
disclosure, consistent with every other CHGR verification in this
repository's history).

## 25. New CHGR Immutability (Section 38)

`git status --short -- .pcae/publication-execution/records/chgr-541cb08c313b4f8884970172d37c5a1d.json`
→ empty at phase close (identical to phase entry). Record bytes
unmutated by this phase.

## 26. Revocation/Supersession State of the New CHGR (Section 39)

`lifecycle_state: "published"`, unrevoked. No CLI verb for suspend/
revoke/supersede exists (§27 below) — no formal supersession mechanism
is available to apply even if desired.

## 27. Old CHGR Reconstruction and Applicability (Sections 26-27, 41)

`chgr-96a0ce12756e4cc892492a87af1db832` independently re-inspected:
`lifecycle_state: published`, unrevoked, digest
`2ff0b0f87d0775b94b3153e94ae14604e44cf840625f3c6ebb55a5b9454befbb`
(via `pcae governance-record verify --json` → `input_digest`) —
byte-identical to the digest cited at 7D.2/7D.3 entry; `git status
--short` on the record file empty. Its own text authorizes "the exact
nine-action provisioning plan" against the absent-everything entering
state independently reconfirmed in §17 above (7B.1 §4). **Its own
frozen Action 2 cannot proceed past CONFLICTING→STOP given the current
retained baseline — it does not, and cannot, validly authorize
resuming at Action 6 without an operator affirmatively disregarding
that STOP, which the record's own text does not sanction.**

## 28. New CHGR Applicability (Section 42)

`chgr-541cb08c313b4f8884970172d37c5a1d`'s `decision_subject` names
"Amended continuation authorization for Dell Class-B Boundary-P
provisioning... binds retained Actions-1-5 baseline as continuation
precondition (D3-2)" — its applicability is bound explicitly to the
current retained baseline by its own subject/rationale text, not
merely by publication recency. Its `rationale` further states, in its
own authority-bearing text (not phase-report prose): *"Any future
continuation from the current Dell state must rely on the newly
approved amended authority."*

## 29. Old/New Collision Attack (Section 43) — Constructed and Evaluated

**Attempted construction:** an operator sees both `chgr-96a0ce12...`
and `chgr-541cb08c...` published and verified; selects the old record;
attempts to reach Action 6 from the current retained-baseline state;
executes the defective (unrepaired) command.

**Result: this path does not survive without violating a visible
precondition.** Following the old record's own cited plan literally,
in order (as its §19 proposition text requires — "exactly the nine
actions... in the stated order"), the operator is stopped at Action
2's explicit `CONFLICTING → STOP` (§27) before Action 6 is reached —
this is not a report-level caveat but a precondition written directly
into the plan text the old CHGR itself cites. Reaching Action 6 under
old authority requires the operator to affirmatively skip/ignore this
STOP — a deliberate departure from the record's own text, not a
plausible good-faith reading of it.

Separately, even setting the Action-2 STOP aside: the new CHGR's own
`rationale` (§28, read in isolation, without needing any phase report)
explicitly names the old record by ID and states it "does not
authorize continuation from the current retained Actions-1-5 baseline
or reuse of its defective Action-6 command" — an operator who reads
*either* record's authority-bearing text in full encounters an
explicit disclaimer, not silence.

**No plausible execution path was found that reaches the defective
Action 6 without violating a visible precondition in the governing
text itself.**

## 30. D3-3 Severity Classification (Sections 45-46)

**Machine-enforcement vs. operator-governance distinction (Section
45):** independently reconfirmed against `src/pcae/cli.py` (the
`governance-record` subcommand set is exactly `{inspect, verify,
template, publish}` — no `supersede`/`suspend`/`revoke`/`transition`
verb anywhere in that parser's construction) and
`src/pcae/commands/governance_record.py::run_governance_record_publish`
(takes only `package_id`/`operator_id`, no predecessor/successor
argument) and
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §17
("no runtime code path reads `.pcae/governance-records/` as of this
contract's freeze, no command gates any other command's behavior on a
CHGR's presence"). **Unambiguity here rests on textual precedence in
both records' own authority-bearing content plus a structural block in
the old plan's own Action 2 — not on any machine-enforced supersession
mechanism, which does not exist for any CHGR in this system, not
specifically this pair.**

**Classification:**

```
D3-3: CLOSED FOR CURRENT CONTINUATION / HARDENING GAP RETAINED
```

Old record (`chgr-96a0ce12756e4cc892492a87af1db832`) is inapplicable to
the current retained baseline (its own frozen Action 2 blocks reaching
Action 6 from this state) and the new record
(`chgr-541cb08c313b4f8884970172d37c5a1d`) is uniquely, textually
applicable, despite absent generic supersession machinery. This is a
disclosed, retained hardening-gap finding for a future authority-model
phase (§31), not a fabricated fix and not force-closed.

## 31. Future Authority-Model Repair (Retained, Not Implemented)

Per Section 47, this finding is retained, not implemented: a future,
separately authorized phase should implement a canonical CLI
transition command for `governance_record_lifecycle_event`
(suspend/supersede/revoke), wiring `predecessor_record_id`/
`successor_record_id` (already present as optional schema fields, per
`human_governance_record.schema.json`) so future amendment phases do
not have to rely on textual-only precedence plus per-record disclaimer
text. Not implemented this phase — it would touch `src/pcae/**` and
require its own separately authorized proposition.

## 32. No-Fallback Requirement (Section 44) — Independently Verified

The new CHGR's own `rationale` field (authority-bearing, not
phase-report prose) already states the no-fallback rule explicitly:
old CHGR "does not authorize continuation from the current retained
Actions-1-5 baseline or reuse of its defective Action-6 command," and
"[a]ny future continuation from the current Dell state must rely on
the newly approved amended authority." A future 149O.20L.7D.5 prompt
must repeat this rule explicitly (per the governing instruction) —
this record already carries it independently of that repetition.

## 33. No Dell Mutation This Phase (Section 48)

All Dell interaction this phase (§16) was read-only: `ssh` identity
check, `id`, `stat`, `getfacl`, `dpkg-query`, `find`, `test -e`, `ssh
-T` auth-only handshake. No `clone`, `chmod`, `chown`, package
install/remove, user/group change, directory creation, venv creation,
or wrapper creation was executed against the Dell host. All scratch
testing (§5, §9, §10, §12, §15) ran in `tempfile.mkdtemp()`-derived
local directories on this Mac, disposed of after use — never
`/opt/pcae/runtime/src`, never any Dell path.

## 34. Companion Tests

`tests/test_phase_149o_20l_7d_4_action_6_continuation_baseline_amendment_independent_verification.py`
— 37 tests, independently authored (imports/executes nothing from the
149O.20L.7D.3 companion module), re-run three consecutive times: 37
passed, 0 failed, 0 flaked, each run. Coverage: original-defect
reconstruction, complete tracked-mode inventory, repaired mode
mapping, branch-order proof, restrictive-umask attack, clean-tree/
content-identity, executable/non-executable preservation, rollback,
continuation gates, Action-2 old-plan-STOP attack, Actions 7-9
unchanged, wrapper digest, HBDC-REQ-042 semantics, exclusions,
decision-session election/confirmation/preview-binding (including the
superseded-vs-governing session resolution, §22), new/old CHGR
integrity and no-CLI-supersession confirmation, no-production-
modification.

## 35. Governance Results

```
$ pcae check                → passed
$ pcae health                → healthy
$ pcae status coherence      → coherent
$ pcae doctor task-memory    → warnings (pre-existing, unrelated, not
                                remediated here — see §2)
$ pcae notify status         → telegram configured/enabled
$ pcae runtime inspect       → Observed / observe / unavailable (unchanged)
```
No raw `git commit`/`git push` used. No `--no-verify`. No force push.
No lifecycle bypass.

## 36. Final Adjudication

```
CHGR ENTRY / RECONSTRUCTION:        COMPLETE, INDEPENDENTLY VERIFIED
FINDING D3-1 (Action-6 defect):     INDEPENDENTLY REPRODUCED, CONFIRMED
REPAIR (mode-mapping):              INDEPENDENTLY VALIDATED — ZERO DIFF
                                     ACROSS ALL 4030 TRACKED PATHS
BRANCH-ORDER CORRECTNESS:           PROVEN, NOT MERELY OBSERVED
CLEAN-TREE / CONTENT IDENTITY:      PASSED, INDEPENDENTLY
EXECUTABLE/NON-EXECUTABLE:          PRESERVED, INDEPENDENTLY VERIFIED
ROLLBACK:                           VERIFIED CLEAN
LIVE DELL BASELINE (Actions 1-5):   INDEPENDENTLY RECONFIRMED, EXACT MATCH
ACTION-6 BASELINE:                  EMPTY, NO RESIDUE, INDEPENDENTLY CONFIRMED
ACTIONS 7-9:                        CONFIRMED ABSENT, TEXT UNCHANGED
CREDENTIAL PREREQUISITE:            UNCHANGED, INDEPENDENTLY RECONFIRMED
FINDING D3-2 (retained baseline):   INDEPENDENTLY ADJUDICATED — CONFIRMED
                                     INSUFFICIENT WITHOUT AMENDMENT, WITH
                                     NEW TEXTUAL PROOF (OLD ACTION 2 STOP)
ACTION-2 CONTINUATION GATE:         SOUND, PROPERLY BOUND TO NEW AMENDMENT
WRAPPER DIGEST:                     RECOMPUTED BYTE-FOR-BYTE, EXACT MATCH
HBDC-REQ-042 SEMANTICS:             CONFIRMED, DEPLOYMENTBINDING-ONLY
EXCLUSIONS:                         ALL PRESENT, VERBATIM, IN RECORD TEXT
HUMAN ELECTION:                     EXPLICIT APPROVE, INDEPENDENTLY CONFIRMED
SEPARATE CONFIRMATION:              DIGEST-BOUND, TEMPORALLY DISTINCT,
                                     INDEPENDENTLY CONFIRMED
NEW CHGR:                           INDEPENDENTLY VERIFIED (6 PASSED, 1
                                     SKIPPED/NON-APPLICABLE)
OLD CHGR:                           BYTE-IDENTICAL, UNREVOKED, INAPPLICABLE
                                     TO CURRENT BASELINE
COLLISION/FALLBACK ATTACK (D3-3):   NO SURVIVING PATH FOUND
D3-3 SEVERITY:                      CLOSED FOR CURRENT CONTINUATION /
                                     HARDENING GAP RETAINED
NO DELL MUTATION:                   PROVEN — ALL COMMANDS READ-ONLY OR
                                     DISPOSABLE-SCRATCH-ONLY

FINAL VERDICT: VERIFIED AUTHORIZED FOR CONTINUATION
```

## 37. Expected Clean State

```
Governing continuation CHGR: chgr-541cb08c313b4f8884970172d37c5a1d
    INDEPENDENTLY VERIFIED AUTHORIZED FOR CURRENT RETAINED-BASELINE
    CONTINUATION
Historical original CHGR: chgr-96a0ce12756e4cc892492a87af1db832
    HISTORICAL ORIGINAL-BASELINE AUTHORITY — NOT APPLICABLE TO CURRENT
    RETAINED-BASELINE CONTINUATION
Actions 1-5:  PROVISIONED — RETAINED BASELINE INDEPENDENTLY VERIFIED
Action 6:     REPAIRED CONTINUATION AUTHORIZED — NOT EXECUTED
Actions 7-9:  NOT EXECUTED
Class-B:      PARTIALLY PROVISIONED — CONTINUATION AUTHORIZED
DeploymentBinding: ABSENT / NOT AUTHORIZED
Boundary C:   NOT AUTHORIZED
Boundary A:   NOT AUTHORIZED
HATP:         NOT READY
Runtime:      Observed / observe / unavailable
```

Neither CHGR is described as "formally superseded" — no canonical
mechanism supports that word; precedence is textual, disclosed as
such.

## 38. Recommended Next Phase

**149O.20L.7D.5 — Dell Class-B Provisioning Continuation Execution.**
Must, in order: (1) reverify `chgr-541cb08c313b4f8884970172d37c5a1d`
currentness; (2) explicitly reject old-CHGR (`chgr-96a0ce12...`)
fallback per §32; (3) reverify Dell identity; (4) reverify source/
contracts freshness; (5) reverify credential prerequisite; (6)
reverify the retained Actions-1-5 baseline against the exact
continuation gates (7D.3 §13); (7) STOP on any baseline mismatch; (8)
execute the repaired Action 6 (§8 above) only; (9) verify it; (10)
execute unchanged Action 7; (11) verify it; (12) execute unchanged
Action 8; (13) verify it; (14) run read-only Action 9; (15) accept only
the authorized `{HBDC-REQ-042}` measured residual; (16) stop. Must not
re-execute Actions 1-5.

Even after a successful 149O.20L.7D.5, per Section 54, provisioning
must not be treated as independently established for progression
toward Boundary-C work — **149O.20L.7E — Dell Class-B Real Host
Provisioning Independent Verification** remains required first.

## 39. Commits and Push Status

This phase's own commits (task lifecycle, this doc, the companion test
module, `PROJECT_STATUS.md`/`CHANGELOG.md`, `.pcae/` finalization
metadata) are enumerated in the git log at phase close; see `git log
--oneline -15` and `git rev-list --count origin/main..HEAD` at that
point for the exact set. Push status and `origin/main..HEAD` are
reported at finalization (§35 governance block covers pre-push state;
finalization proceeds per this repository's standard `pcae push`
sequence after this report is staged).
