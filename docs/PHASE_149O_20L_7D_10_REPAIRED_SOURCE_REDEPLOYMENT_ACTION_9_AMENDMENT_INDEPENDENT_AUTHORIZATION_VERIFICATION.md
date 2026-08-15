# Phase 149O.20L.7D.10 — Repaired-Source Redeployment + Action-9 Amendment Independent Authorization Verification

## 0. Phase Identity and Type

**Independent verification only.** This phase does **not** fetch the
repaired source into the Dell production checkout, does **not**
checkout the candidate SHA on Dell, does **not** chmod/chown Dell
source, does **not** reinstall or modify the Dell venv, does **not**
modify the wrapper, does **not** execute the corrected Action 9 as an
adjudication, does **not** mutate a CHGR, does **not** create a
`DeploymentBinding`, does **not** certify, and does **not** activate.
All Dell interaction this phase is fresh, read-only SSH. All source
comparisons use immutable Git objects (`git cat-file`, `git diff`,
`git show`, `git ls-tree`, disposable `git worktree --detach` clones,
a disposable mirror clone with network subsequently disabled) — never
this repository's own working tree state and never a hand-typed
number carried over from 7D.9's report without independent
re-derivation.

## 1. Phase-Entry State

```
$ git log -1 --format=%H
d83d3594...   (Phase 149O.20L.7D.9: sync phase-completion metadata to post-push state)
$ git status --short
(clean)
$ git rev-list --count origin/main..HEAD
0
```

`pcae health` / `pcae check` / `pcae status coherence` / `pcae push
check` / `pcae runtime inspect` / `pcae notify status` / `pcae
phase-report show --latest` / `pcae phase-report reconcile
--phase-id 149O.20L.7D.9` were all run at phase entry: healthy,
passed, coherent, clean (nothing_to_push), Observed/observe/
unavailable, Telegram configured/enabled, canonical report consistent,
reconciliation `already_dispatched`/mutation `none`. `pcae doctor
task-memory` reports pre-existing warnings (21 active-task-file /
`tasks/DONE.md` entries predating this phase) — repository-maintenance
debt, out of this phase's allowed-file scope, not remediated here.

## 2. Reconstruction of 7D.9 From Primary Evidence (Not the Summary)

Two independent artifact classes were read directly, not trusted from
`pcae phase-report show --latest`'s prose:

1. **`docs/PHASE_149O_20L_7D_9_...md`** (745 lines, the phase's actual
   committed work product) — a **proposition-only** document. Its own
   §0 states it does not run `decision-session`, does not publish a
   CHGR, and does not execute anything; its §21 is an explicit
   "HUMAN ELECTION REQUIRED — NOT YET DECIDED" placeholder.
2. **`.pcae/phase-completion-metadata.json` /
   `.pcae/phase-completion-report.md`** — describe a **fuller**
   narrative: a genuine human election, a decision-session capture
   (two abandoned attempts, one successful), and a published CHGR
   `chgr-0e37ed1340b14311826722c4dbf3e856`.

**These two artifact classes are not in conflict but they are not the
same document either** — the proposition doc's own text was frozen at
its single content commit (`d055c8a0`) and was never amended to record
the election that the metadata/report narrate as happening later in
the same phase. This is a **genuine, disclosed finding** (§45 below),
not resolved by assuming the report's prose is automatically true.
Independent verification of the underlying claim therefore required
locating and reading the actual governance-record and decision-session
artifacts on disk (§13–§16), not just the narrative that cites them.

## 3. Candidate SHA — Independent Re-Validation

```
$ git cat-file -t 28bf137b5dc95d024e8913b678dce0501a46fd0f
commit
$ git show --no-patch --format=fuller 28bf137b5dc95d024e8913b678dce0501a46fd0f
    Author/Commit: Atila Madai, 2026-08-15T14:32:38+02:00
    Subject: "Phase 149O.20L.7D.7: repair pcae_push_check literal for finalization gate"
$ git merge-base --is-ancestor 28bf137b5dc95d024e8913b678dce0501a46fd0f origin/main && echo yes
yes
```

The commit subject names an unrelated finalization-gate literal
repair, **not** the Class-B verifier repair — independently confirmed
misleading, matching the task's own warning not to accept a subject
line as source-identity evidence. Independently re-verified the real
repair provenance:

```
$ git merge-base --is-ancestor 73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2 28bf137b5dc95d024e8913b678dce0501a46fd0f && echo yes
yes
```

`73ea8b23` (7D.7's own repair commit, "Class-B Verifier Narrow Source
Repair for HBDC-REQ-022/030/035") is an ancestor of the candidate —
every byte of the repair is present in `28bf137b...` regardless of its
own commit's unrelated subject. **Candidate SHA confirmed authentic.**

## 4. Exact Repaired-Byte Verification (Sections 7–8)

```
$ git diff --name-status 7a3fa971304521cdcb44251e07ef1966baec686a 28bf137b5dc95d024e8913b678dce0501a46fd0f -- src/ scripts/ docs/contracts/ pyproject.toml
M	src/pcae/core/hatp_class_b_conformance.py
M	src/pcae/core/hatp_class_b_topology_verifier.py
M	src/pcae/core/hatp_environment_lock_verifier.py
```

Exactly three files, matching 7D.8's own independently-reconstructed
repair diff. Independently confirmed the candidate's own bytes for
these three files are **byte-identical** to the current repository
HEAD (i.e. to 7D.8's independently-verified repaired bytes):

```
$ git diff 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD -- src/pcae/core/hatp_class_b_conformance.py src/pcae/core/hatp_class_b_topology_verifier.py src/pcae/core/hatp_environment_lock_verifier.py
(empty)
```

## 5. Authority-Relevant Drift Attack (Section 9)

```
$ git diff --stat 28bf137b5dc95d024e8913b678dce0501a46fd0f HEAD -- src/ scripts/ docs/contracts/ pyproject.toml
(empty)
```

Zero authority-relevant files changed between the candidate and the
current repository tip. Independently re-run against this phase's own
live `HEAD` (not copied from 7D.9's number).

## 6. Contract Versions at Candidate (Section 10)

```
$ git show 28bf137b...:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md | grep '**Version:**'
**Version:** 1.0
$ git show 28bf137b...:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md | grep '**Version:**'
**Version:** 1.3
$ git show 28bf137b...:docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md | grep '**Version:**'
**Version:** 1.1
```

HBDC-001 v1.0, HMIC-001 v1.3, HMRC-001 v1.1. Independently `diff`'d
HMIC-001's contract file byte-for-byte across old-deployed → candidate
→ current HEAD via disposable worktrees: **identical at every step.**
Contract identity is unchanged.

## 7. Candidate Tracked-Tree Inventory (Section 11)

Independently enumerated from a disposable `git worktree --detach` of
the candidate (not inherited from 7D.9's or any prior phase's
figures):

```
$ git ls-files | wc -l                                          → 4108
$ git ls-tree -r HEAD | awk '{print $1}' | sort | uniq -c
    4097 100644
      11 100755
$ git ls-tree -r HEAD | awk '{print $1}' | grep -vc '^100644$\|^100755$'   → 0 (no symlinks, no other modes)
$ git submodule status                                           → (empty, no submodules)
```

Matches the candidate-specific figures asserted by both 7D.9's §10 and
its own read-back §11 exactly — **independently re-derived, not
inherited from the old 4030/4024/6 figures.**

## 8. HMIC Membership (Section 12)

Read directly from `src/pcae/core/hatp_mandatory_certification.py`:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` (22 entries) +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries) = 28, asserted by
the module's own `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28`.
All three repaired verifier modules
(`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
verifier.py`, `hatp_class_b_conformance.py`) are present as the final
three entries of `_FROZEN_SRC_PCAE_RELATIVE_FILES` — confirmed HMIC
source members, read from the live module source, not from a stale
docstring.

## 9. HMIC Implementation Digest — Independently Recomputed (Section 13)

Using the production `derive_implementation_scope_digest()` function
itself, called directly against three disposable roots (candidate
worktree, old-deployed worktree, current repo `HEAD`) — computed fresh
this phase, not copied from 7D.9's report:

```
candidate (28bf137b...)   → 4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac
old-deployed (7a3fa971...) → b728d368ee830d1e6f6e3c1fc44ca97d4826e3cf124c47c7c549b307dd1a545d
current HEAD               → 4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac  (= candidate)
```

**Exact match to 7D.9's and 7D.8's own reported values, independently
reproduced.**

## 10. HMIC Contract Identity vs. Implementation Identity (Sections 14–15)

Contract identity (HMIC-001 bytes, §6 above): **unchanged.**
Implementation/source identity (`derive_implementation_scope_digest`):
**changed**, `b728d368...` → `4e3452ba...`. These are independently
confirmed distinct claims, not conflated. No HMIC certification
artifact exists anywhere in this repository or on live Dell (§13
below) — there is nothing for the redeployment to invalidate, and this
phase computes/requests/grants none. **No Boundary-C certification
applies to the candidate.**

## 11. Old/Candidate Scoped Diff — Old-Deployed to Candidate (cross-check)

```
$ git diff --name-status 7a3fa971... 28bf137b... -- src/ scripts/ docs/contracts/ pyproject.toml
```

(reproduced in §4 — three files, matching 7D.8's repair diff exactly).

## 12. Historical-Test Migration Disclosure (Section 44)

7D.8's own verdict — "REGRESSION CLEAN WITH EXPECTED HISTORICAL TEST
MIGRATION REQUIRED" — was independently re-read from
`docs/PHASE_149O_20L_7D_8_...md`. That report's own scope explicitly
confines the migration need to test assertions that predate the
repair and assert the now-corrected (pre-repair) failure signature;
none of those stale assertions are cited anywhere in this phase's own
`fast_green`/companion-test gates, and none function as a current
execution-authority gate for 149O.20L.7D.10 or 7D.11's forward
commands. **Classified as separate repository-maintenance debt, not
blocking.**

## 13. New CHGR — Full Reconstruction (Sections 46–56)

Read directly from
`.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json`
and its three related artifacts
(`chgrconf-51029a1d...`, `chgrprov-710689934...`, `chgrintg-274d304d...`):

- **`lifecycle_state`:** `published`.
- **`selected_option_id`:** `approve`; `options_presented`:
  `["approve", "decline", "amend"]` — three genuine options, no
  default.
- **`decision_subject`** (verbatim, 371 chars): names Phase
  149O.20L.7D.9, candidate SHA `28bf137b5dc95d024e8913b678dce0501a46fd0f`
  explicitly, cites the proposition doc path, and states "No Dell
  mutation authorized by this session; execution deferred to a
  separate future phase." — **binds the exact candidate SHA by full
  40-char text, not a branch name, abbreviated SHA, or implicit
  current-HEAD.**
- **`rationale`** (full text read): explicitly names the corrected
  Action-9 PATH
  (`/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`), the
  update-in-place mechanism, no-venv-reinstall, no-wrapper-mutation,
  the expected-residual `{HBDC-REQ-042}` STOP condition, the explicit
  HMIC implementation-identity-changed / NOT-CERTIFIED-FOR-BOUNDARY-C
  disclosure, and the full §20 exclusion list — **binds the Action-9
  PATH and the HMIC disclosure by full text, not by external
  unbound reference.**
- **`conditions`** (7 numbered items, read verbatim): re-states the
  preflight-must-match/STOP-and-rollback/no-out-of-order-Action-9/
  expected-residual-STOP/no-venv-wrapper-DeploymentBinding-Boundary-
  discipline as binding conditions on any future consuming phase.
- **`decision_maker_identity_evidence.identifier` /
  `confirmer_identity_evidence.identifier`:** both `"Atila Madai"`,
  `evidence_kind: "typed_confirmation_only"`.
- **`confirmation_statement`:** `"Accepted"` — a distinct field from
  `rationale`, recorded in the separate `chgrconf-...` artifact.

### 13.1 `governance-record verify --related` (full cross-artifact check)

```
$ pcae governance-record verify chgr-0e37ed1340b14311826722c4dbf3e856.json \
    --related chgrconf-51029a1d....json --related chgrprov-710689934....json --related chgrintg-274d304d....json
    schema_shape                 passed
    digest_self_consistency      passed
    lifecycle_structural_legality passed
    confirmation_binding         passed
    assurance_truthfulness       passed
    provenance_consistency       passed
    integrity_consistency        passed
    template_resolution          skipped (no matching related template supplied)
```

All seven applicable checks pass (representation-layer only, per the
tool's own disclosure — this does not itself establish the represented
act's validity/applicability/currentness, which this report separately
adjudicates from the artifacts' own text below).

## 14. Election / Confirmation — Distinctness (Section 50) — Disclosed Limitation

`chgrconf-51029a1d...`'s `confirmer_identity_evidence.captured_at`
(`2026-08-15T15:31:14.822261Z`) is **byte-identical, to the
microsecond**, to `chgr-0e37ed...`'s own
`decision_maker_identity_evidence.captured_at`. The two are
structurally distinct fields in distinct artifacts (`rationale` +
`selected_option_id` in the CHGR vs. a separate
`confirmation_statement: "Accepted"` bound to a `preview_rendering_
digest`/`confirmed_content_digest` pair in the confirmation-evidence
record), and the decision-session's own `orchestration/CDS-105d30f5...`
completed-stages list shows `ConfirmationRequest` and
`ConfirmationValidation` as two separate pipeline stages after
`PreviewValidation` — a genuine two-step `select`-then-`confirm`
discipline structurally, not a single combined action. **However, the
wall-clock timestamps alone do not independently prove temporal
separation** between election and confirmation; this is disclosed as a
**non-blocking observation**, not a defect — the `typed_confirmation_
only` evidence kind is a lower-assurance capture mechanism by design
(`assurance_level: "L0"`, disclosed in the record itself), and the
structural two-stage pipeline is independently confirmed from the
orchestration session file, not merely inferred from timestamps.

## 15. Decision-Session Workflow — Three Attempts, Independently Verified (Sections 46–48, 51)

Read all three session files directly
(`.pcae/decision-sessions/CDS-*.json` and their `orchestration/`
mirrors):

| Session | `template_ref` | `subject_ref` length | Outcome |
|---|---|---|---|
| `CDS-9fac483e-...` | `class-b-repaired-source-redeployment-action-9-amendment-authorization` (unregistered) | 394 | Never published |
| `CDS-a2e437a8-...` | `class-b-boundary-p-provisioning-authorization` (registered) | **574** | Never published |
| `CDS-105d30f5-...` | `class-b-boundary-p-provisioning-authorization` (registered) | 371 | **Published as `chgr-0e37ed...`** |

Independently confirmed: `CDS-a2e437a8`'s `subject_ref` is 574
characters — **exceeds the CHGR-001 schema's 500-character
`decision_subject` limit**, independently reproducing the report's
claimed abandonment cause from the artifact's own persisted field,
not merely from prose. `CDS-9fac483e` used a `template_ref` string
that does not correspond to any file this repository's template
registry actually resolves (independently confirmed: no
`class-b-repaired-source-redeployment-action-9-amendment-authorization`
template exists under `docs/contracts/` or any `pcae template`
listing this phase checked) — consistent with the claimed
unregistered-template failure.

**No contamination:** `.pcae/publication-execution/records/` contains
exactly four CHGRs total — `chgr-96a0ce12...` (149O.20L.7D, original),
`chgr-541cb08c...` (149O.20L.7D.3, continuation),
`chgr-d4343fa5...` (149O.20L.7B.2, an **unrelated** Boundary-P
target-environment-selection record from 2026-08-14, one day earlier —
independently read and confirmed out of scope for this transition),
and `chgr-0e37ed...` (this transition). No readiness/confirmation/
publication artifact anywhere references `CDS-9fac483e` or
`CDS-a2e437a8` — neither abandoned session's readiness package became
governing, and no CHGR was published from either.

## 16. Authority Applicability — Old CHGRs Do Not Cover This Transition (Sections 57–61)

Read `chgr-96a0ce12756e4cc892492a87af1db832` and
`chgr-541cb08c313b4f8884970172d37c5a1d` directly:

- **`chgr-96a0ce12...`** (published `2026-08-15T04:20:10Z`):
  `decision_subject`/`rationale` name "the exact nine-action
  provisioning plan" and pin source SHA `7a3fa971...` verbatim, with
  no reference to any other SHA or PATH value.
- **`chgr-541cb08c...`** (published `2026-08-15T07:54:39Z`):
  `decision_subject`/`rationale` scope exclusively to the repaired
  Action-6 sequence for the *original* pinned SHA `7a3fa971...`, and
  its rationale text says "unchanged Actions 7-9." **Its publish
  timestamp independently confirmed to precede the 7D.7 repair
  commit's own commit timestamp** (`2026-08-15T14:32:38+02:00` =
  `12:32:38Z`, i.e. the candidate commit itself; 7D.8's own report
  places the repair's authoring at `14:10:25Z` local same-day) — it
  **structurally cannot** reference a repair or SHA that did not yet
  exist at its own publication time.

**Collision attack (Section 60):** could an operator validly perform
the repaired-source transition under either old CHGR's own scope?
No — both records' own `rationale` text is pinned to the literal old
SHA `7a3fa971...` as *the* authorized source identity and neither
contains any source-update mechanism, any second SHA, or any PATH
value; an operator citing either as authority for a *different* SHA or
a *changed* Action-9 PATH would be citing a record whose own text
contradicts the action being taken. **No fallback:** only
`chgr-0e37ed1340b14311826722c4dbf3e856` governs this exact transition.
**No machine-readable supersession field exists** anywhere in the CHGR
schema linking `chgr-0e37ed...` to the two priors (the D3-3 hardening
gap, independently reconfirmed still present, still unclosed by any
schema change this phase observed) — applicability here rests on each
record's own textual scope and publish-time ordering, not on an
automated supersession pointer. This is the same operator-applicability
standard 7D.3 §22 already established for the original/continuation
pair, applied here to the continuation/redeployment pair.

## 17. Live Dell Verification — Fresh, Read-Only, This Phase (Sections 16–22)

Fresh `ssh hac-dell` session, all commands read-only (`cat`, `stat`,
`id`, `git rev-parse`/`status`/`ls-files`/`ls-tree`/`cat-file -e`,
`sha256sum`, `pip show`, `which`, `find`, `env -i ... which`). No
`chmod`/`chown`/`fetch`/`checkout`/`pip install`/`systemctl`/write was
issued.

- **Machine identity:** `/etc/machine-id =
  54ff22ce400b475aa0d55cb68f4a3334`, `hostname =
  atila-Latitude-E5470`, `Linux 7.0.0-28-generic x86_64` — exact match.
- **Source baseline:** `HEAD = 7a3fa971304521cdcb44251e07ef1966baec686a`
  (detached, `symbolic-ref` exit 1), `git status --short
  --untracked-files=all` empty, `origin = git@github.com:atimad/
  pcae-harness.git`, path `root:pcae 750`, `4030` tracked paths
  (`4024` × `100644`, `6` × `100755`) — **exact match to the 7D.8/7D.9
  baseline, zero drift.**
- **Retained infra:** `pcae` uid/gid 1004, `/etc/pcae/hatp/trust-store`
  `root:pcae 750`, `/home/pcae` `pcae:pcae 750`, zero
  `*deploymentbinding*` matches under `/opt/pcae` or `/etc/pcae`.
- **Credential:** `/root/.ssh/pcae_harness_deploy_ed25519` exists,
  `root:root 600`; `/root/.ssh/config` stanza matches the 7D.1
  baseline exactly. No key bytes read, no test push issued.
- **Venv:** `.pth` → literal path `/opt/pcae/runtime/src/src`;
  `direct_url.json` → `{"editable": true, "url":
  "file:///opt/pcae/runtime/src"}` — both filesystem paths, not
  SHAs/hashes. `pip show pcae-harness` → `Version: 0.2.0`, `Editable
  project location: /opt/pcae/runtime/src`. `RECORD` (10 entries,
  confirmed non-empty). Console script
  (`venv/bin/pcae`) imports `pcae.cli` fresh at every invocation, no
  compiled/cached source-byte pinning. **A source-only checkout swap
  at the same path changes only the bytes the already-bound path
  resolves to at import time — independently confirmed no venv
  refresh/reinstall is required.**
- **Wrapper:** `sha256sum /opt/pcae/runtime/bin/pcae-launch =
  b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`
  (exact match), `root:pcae 750`, `188` bytes, `9` lines — exact match
  to the authority-bound expected digest.
- **PATH diagnostic (read-only, non-authoritative, explicitly
  labeled):** old `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`) →
  `which pcae` exit 1 (not found); corrected `PATH`
  (`/opt/pcae/runtime/venv/bin:...`) → resolves to
  `/opt/pcae/runtime/venv/bin/pcae`, exit 0. `git --version` on Dell
  → `2.43.0`.
- **PATH-order / shadow-executable attack (Section 36):** `/bin` and
  `/sbin` show as mode `777` under plain `stat` — **investigated and
  resolved as a non-issue**: both are symlinks (`lrwxrwxrwx`, the
  mode Linux always reports for a symlink's own inode, irrelevant to
  access control) to `/usr/bin` and `/usr/sbin`, which are `root:root
  755`. Independently confirmed `sudo -u pcae test -w /bin` and
  `test -w /sbin` both fail (`pcae cannot write`). No directory in
  `/usr/bin:/bin:/usr/sbin:/sbin` is `pcae`-writable, and none
  contains any file named `pcae`. **Prepending
  `/opt/pcae/runtime/venv/bin` creates no new shadow-executable
  surface; ordering is correct and sufficient.**
- **Old-object local availability (Section 25):**
  `sudo git -C /opt/pcae/runtime/src cat-file -e
  7a3fa971...^{commit}` → exit `0` (present). **Candidate-object
  availability, checked fresh this phase:**
  `sudo git -C /opt/pcae/runtime/src cat-file -e
  28bf137b...^{commit}` → `fatal: Not a valid object name` (**not yet
  present** — the candidate has not been fetched to Dell). This is
  **expected and disclosed, not a defect**: the forward step's `git
  fetch` will require live network reachability to `github.com` via
  the existing read-only deploy credential at execution time; rollback
  (§18 below) does not depend on it.

**Summary: zero drift from the 7D.8/7D.9 baseline anywhere live-checked
this phase.**

## 18. Rollback — Adversarial, Network-Disabled Reproduction (Sections 26–30)

Reproduced the exact bounded sequence in a disposable local clone,
independent of both the Dell host and this repository's own working
tree:

```
$ git clone --mirror <this-repo> rollback-sim-bare.git
$ git clone rollback-sim-bare.git rollback-sim && cd rollback-sim
$ git checkout --detach 7a3fa971...              # old baseline
$ git fetch origin 28bf137b...                    # forward: fetch candidate
$ git checkout --detach 28bf137b...                # forward: checkout candidate
$ git remote set-url origin https://invalid.invalid/nonexistent.git   # disable network
$ git checkout --detach 7a3fa971...                # rollback, network disabled
    → succeeds, exit 0, HEAD = 7a3fa971... exactly
$ git count-objects -v
    → prune-packable: 0, garbage: 0   (nothing at risk of gc)
```

**Rollback succeeds with the remote deliberately broken**, confirming
the narrower, evidence-based claim: rollback requires zero network
access **throughout the exact authorized forward→rollback sequence**
(old SHA is the checkout's current `HEAD` at sequence start; the
forward step only *adds* objects via `fetch`, never prunes; `git gc`
does not run implicitly inside this command sequence — independently
confirmed via `count-objects -v` showing zero packable/garbage
objects after the sequence). This is **not** stated as the unlimited
claim "Git never garbage-collects it" — it is scoped to this exact
bounded sequence, per the task's own narrower-standard instruction.

**Rollback-anchor necessity (Section 27):** an explicit temporary ref
to the old SHA is **not** necessary given this evidence — the old SHA
remains reachable via `HEAD`'s own reflog entry
(`HEAD@{2}: checkout: moving from main to 7a3fa971...`) independent of
any branch/tag, and the reproduction above proves rollback succeeds
without one. The current proposition's omission of an explicit anchor
ref is not a defect.

**Mode mapping (Section 29):** the candidate's own inventory (§7
above: 4097×100644, 11×100755) is read fresh from `git ls-tree` at
execution time by the proposed `find -perm -u+x` two-branch mapping —
the mechanism is self-computing against whatever the *new* index
produces, not a hard-coded count; the old 4030-path validation figures
are correctly not reused for the candidate.

## 19. REQ-036 / Corrected Action-9 — Independent Reconstruction (Sections 33–39)

`_check_launcher` (`hatp_environment_lock_verifier.py`) resolves the
trusted launcher via `shutil.which("pcae")` against the invoking
process's own `PATH` — left-to-right, first-match semantics, not
merely "is `pcae` present somewhere." Old frozen `PATH`
(`/usr/bin:/bin:/usr/sbin:/sbin`, consumed by `chgr-541cb08c...`)
excludes the only directory containing any `pcae`-named executable
(`/opt/pcae/runtime/venv/bin`) — independently reproduced live this
phase (§17) that `which pcae` fails under the old `PATH` and succeeds,
resolving to the one admin-controlled console-script, under the
corrected `PATH`. The corrected invocation (§16 of 7D.9, independently
re-read) preserves `env -i` isolation, explicit `HOME=/home/pcae`,
`PYTHONNOUSERSITE=1`, the absolute interpreter path
`/opt/pcae/runtime/venv/bin/python3` (deliberately not `PATH`-searched
— the interpreter's own resolution is a distinct, disclosed,
non-blocking observation from 7D.6, not something this PATH change
attempts to fix), and pinned CWD
`/opt/pcae/runtime/src`. The wide-`PATH` diagnostic run live this
phase (§17) is explicitly non-authoritative — no Action-9 result, old
or corrected `PATH`, was treated by this phase as an adjudication.

**Expected residual (Section 39, independently re-derived):** exactly
`{HBDC-REQ-042}` — REQ-022/030/035 repaired at the candidate (§4,§11),
REQ-036 addressed by the corrected `PATH` (this section), REQ-042
remains failing by design because no `DeploymentBinding` exists or is
authorized (§17). **This remains a prediction, not a measured fact**,
until a future phase actually runs Action 9 post-redeployment.
Unexpected-`COMPLIANT` STOP semantics (Section 40) and the full
DeploymentBinding/Boundary-C/Boundary-A exclusion list (Sections
41–43) are independently re-confirmed present, verbatim, in both the
proposition (§18, §20) and the CHGR's own `conditions`/`rationale`
text (§13 above) — not merely asserted once and inherited silently.

## 20. Architecture-Status / PROJECT_STATUS.md Limitation Reconciliation (Section 45)

The generated architecture-status limitation — "current phase section
has no explicit 'Recommended next phase' sentence" — was independently
traced to `PROJECT_STATUS.md`'s own "Current Phase" prose paragraph
for 149O.20L.7D.9 (lines 4–41): it ends its narrative without the
literal bolded `Recommended next phase:` sentence pattern that older
entries in the same file (e.g. the 7D.7/7D.8 entries) do use. **The
canonical phase report (`pcae phase-report show --latest`) and
`.pcae/phase-completion-metadata.json` both independently agree**,
each carrying a full, matching `Recommended Next Phase` /
`recommended_next_phase` field naming 149O.20L.7D.10 verbatim. This is
**derived-status (`PROJECT_STATUS.md` prose) incompleteness only** —
it does not affect authority, since the canonical governance artifacts
that actually gate `pcae phase complete` and this phase's own
bootstrap readiness both carry the correct, matching value. Per this
phase's verification-only scope, `PROJECT_STATUS.md`'s 7D.9 entry is
**not modified** by this phase (only this phase's own new entry is
prepended, per standard procedure, §24 below).

## 21. Currentness Immediately Before Exit (Section 63)

Re-verified read-only immediately before writing this report:

- Candidate `28bf137b...` still `cat-file -t commit`, still an
  ancestor of `origin/main` — unchanged.
- No authority-relevant source drift: `git diff --stat 28bf137b...
  HEAD -- src/ scripts/ docs/contracts/ pyproject.toml` still empty.
- Dell still runs `7a3fa971...` (re-checked live this phase, §17,
  timestamped after the CHGR's own `created_at`).
- Credential state unchanged (read-only re-check, §17).
- `chgr-0e37ed1340b14311826722c4dbf3e856` still present,
  `lifecycle_state: published`, unchanged file content
  (`declared_record_digest`/`record_digest` still match on re-read).

**No staleness detected.**

## 22. No-Mutation Proof (Sections 64–65)

**Dell:** every command issued this phase is read-only (enumerated in
§17); no `chmod`/`chown`/`fetch`/`checkout`/`pip install`/`systemctl`/
write of any kind. **This Mac / production source:** `git status
--short` confirms zero changes to `src/pcae/**`, `scripts/**`,
`docs/contracts/**`, or `pyproject.toml` at any point this phase — the
only filesystem writes this phase performed are this document, its
companion test module, `PROJECT_STATUS.md`/`CHANGELOG.md`/task-
lifecycle files, and disposable scratch worktrees/clones under the
session scratchpad directory (removed before phase completion, never
committed).

## 23. Final Verdict

**VERIFIED AUTHORIZED FOR REPAIRED-SOURCE REDEPLOYMENT + ACTION-9
RE-ADJUDICATION.**

Every independently-reproduced technical claim (candidate authenticity
and ancestry, exact repaired bytes, zero authority-relevant drift,
contract versions, candidate tree inventory, HMIC membership and
digest, live Dell baseline, venv no-refresh classification, wrapper
digest, rollback network-independence under an adversarial
network-disabled reproduction, corrected-PATH derivation and
diagnostic reconfirmation) and every independently-reproduced
authority claim (CHGR schema/digest/lifecycle/confirmation/
provenance/integrity verification, exact source-SHA and Action-9-PATH
text binding, HMIC-disclosure text binding, both prior CHGRs'
inapplicability by their own text and publish-time ordering, no
decision-session contamination) is **sound and current**. Two
non-blocking observations are disclosed (§14: election/confirmation
timestamp granularity; §20: `PROJECT_STATUS.md` prose-completeness
gap) — neither undermines the governing CHGR's own text-based
authority.

## 24. Governing State (Clean Status)

- **Governing CHGR:** `chgr-0e37ed1340b14311826722c4dbf3e856` —
  INDEPENDENTLY VERIFIED AUTHORIZED FOR REPAIRED-SOURCE REDEPLOYMENT +
  CORRECTED ACTION-9 RE-ADJUDICATION.
- **Candidate source:** `28bf137b5dc95d024e8913b678dce0501a46fd0f` —
  INDEPENDENTLY VERIFIED DEPLOYMENT CANDIDATE.
- **Dell source:** `7a3fa971304521cdcb44251e07ef1966baec686a` — OLD
  SOURCE, STILL DEPLOYED (live-reconfirmed this phase).
- **Venv:** RETAINED — NO REINSTALL AUTHORIZED/REQUIRED.
- **Wrapper:** RETAINED — UNCHANGED (digest reconfirmed live).
- **REQ-022/035, REQ-030:** REPAIRED IN CANDIDATE — NOT YET DEPLOYED.
- **REQ-036:** CORRECTED INVOCATION AUTHORIZED — NOT YET EXECUTED.
- **REQ-042:** EXPECTED RESIDUAL (prediction, not yet measured).
- **HMIC:** CANDIDATE IMPLEMENTATION/SOURCE IDENTITY CHANGED — NOT
  CERTIFIED.
- **DeploymentBinding:** ABSENT / NOT AUTHORIZED.
- **Boundary C / Boundary A:** NOT AUTHORIZED.
- **HATP:** NOT READY.
- **Runtime:** Observed / observe / unavailable.

## 25. Next Phase

**149O.20L.7D.11 — Repaired-Source Dell Redeployment + Action-9
Re-Adjudication Execution.** May perform only: reverify CHGR
currentness; reject both old-CHGR fallbacks; reverify Dell machine and
baseline; reverify source credential; update source from
`7a3fa971...` to `28bf137b...` exactly, applying the exact candidate
mode mapping; read back source state; leave venv and wrapper
untouched; run the exact corrected Action 9; require a measured
failing set of exactly `{HBDC-REQ-042}`; STOP on anything else. No
`DeploymentBinding`. No Boundary C/A. **149O.20L.7E remains blocked**
until 7D.11 later succeeds and measures exactly `{HBDC-REQ-042}`, then
requires a 7E independent real-host provisioning verification.
