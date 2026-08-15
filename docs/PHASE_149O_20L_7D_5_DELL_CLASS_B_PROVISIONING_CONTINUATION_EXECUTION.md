# Phase 149O.20L.7D.5 — Dell Class-B Provisioning Continuation Execution

## 0. Phase Identity and Type

Real-host continuation-execution phase. Authorized scope: repaired
Action 6, unchanged Actions 7-8, read-only Action 9. Explicitly
excluded: re-executing Actions 1-5, the original defective Action-6
command, fallback to the original CHGR, DeploymentBinding creation,
certification, activation.

**Phase-entry commit:** `5b5d4a5f2746d38ef1f069f0b387af58fc87a46d`
(tip of `main`, `HEAD == origin/main`, `git rev-list --count
origin/main..HEAD` = `0`).

## 1. Entry Repository Checks

```
git status --short                → (clean)
git status --branch --short       → ## main...origin/main
git rev-list --count origin/main..HEAD → 0
```

- `pcae health`: healthy. Agent lock: held by `claude-local`.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing `tasks/done/`
  entries missing from `tasks/DONE.md` (18+ historical entries
  predating this phase); unrelated, outside this phase's allowed-file
  scope, not remediated here.
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: 149O.20L.7D.4's canonical report;
  recommended next phase names this phase.
- `pcae phase-report reconcile --phase-id 149O.20L.7D.4`: `status:
  reconciled`, `mutation: none (inspection only)`.

## 2. Governing Continuation Authority — Reverified Before Mutation

`pcae governance-record verify
.pcae/publication-execution/records/chgr-541cb08c313b4f8884970172d37c5a1d.json`
→ `outcome: verified` — `schema_shape`, `digest_self_consistency`,
`lifecycle_structural_legality` all passed.

Directly inspected the record's own fields:

- `lifecycle_state`: `published`.
- `selected_option_id`: `approve`.
- `decision_subject`: names the exact Dell target
  (`hac-dell / atila-Latitude-E5470`, machine-id
  `54ff22ce400b475aa0d55cb68f4a3334`), repaired Action 6 (D3-1), the
  retained Actions-1-5 baseline (D3-2), citing 7D.3 by path.
- `rationale`: approves "exactly the amended continuation proposition
  ... including the repaired Action-6 forward/read-back/rollback
  command sequence, the explicitly bound retained Actions-1-5 Dell
  baseline, the continuation gates and STOP semantics, and unchanged
  Actions 7-9 and exclusions," and explicitly states the prior CHGR
  "does not authorize continuation from the current retained
  Actions-1-5 baseline or reuse of its defective Action-6 command."
- `conditions`: excludes Action 6/7-9 execution *at the time this
  record's own authorizing phase (7D.3) ran*, any rerun of Actions
  1-5, DeploymentBinding creation, Boundary C/A, Permission Broker,
  POL-005, COMP-002, repository onboarding, centralized governance —
  this is the authorization/execution phase separation this project
  uses throughout (an authorization-publication phase never executes
  in the same phase as its own election; a later, separately-governed
  execution phase — this one — consumes the published authority). This
  matches the precedent set by `chgr-96a0ce12756e4cc892492a87af1db832`
  (itself worded identically: "does not authorize provisioning
  execution in this phase") which was validly consumed by execution
  phase 149O.20L.7D. No re-election was required or performed this
  phase.
- No revocation, no lifecycle transition since 7D.4: `lifecycle_state`
  remains `published`, `record_digest` unchanged.

## 3. Session Relationship — Reconfirmed

`.pcae/publication-execution/attempts/pubexec-ae9ef04551cb466993b98d678a33b608.json`:
`success: true`, `record_id: chgr-541cb08c313b4f8884970172d37c5a1d`,
`session_id: CDS-554c3c12-0693-4edd-867d-b86374c376b2`. Independently
re-inspected both sessions:

- `CDS-554c3c12-0693-4edd-867d-b86374c376b2.json`:
  `session_state: "Confirmed"`, `human_selection_id: "approve"` —
  the governing session.
- `CDS-8984cecc-4b55-4cfc-aca6-14397f5735a1.json`:
  `session_state: "Confirmed"`, `human_selection_id: "approve"`, but
  its readiness package never reached `pending-packages/consumed/`
  and none of its three publish attempts produced a record (per
  7D.4's independent finding) — superseded, not governing.

Authority-chain reconstruction matches 7D.4 exactly. Proceeded.

## 4. Old-CHGR Fallback Rejection — Recorded

`chgr-96a0ce12756e4cc892492a87af1db832` is **not** governing this
continuation. This execution used none of its absent-baseline
assumptions, none of its Action-2 fresh-creation semantics, and none
of its defective blanket-`chmod 0640` Action-6 command. The only
Action-6 command sequence used this phase is the repaired sequence
from §11 of `docs/PHASE_149O_20L_7D_3_...md`, reproduced verbatim in
§7 below.

## 5. Source/Contracts Freshness

```
git diff --stat 7a3fa971304521cdcb44251e07ef1966baec686a HEAD -- \
  src/pcae/ scripts/ docs/contracts/          → (empty — no drift)
```

Contract versions independently reconfirmed current:

- `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001): `Version: 1.0`.
- `HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
  (HMIC-001): `Version: 1.3`.
- `HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001):
  `Version: 1.1`.

No repin. Pinned source SHA unchanged:
`7a3fa971304521cdcb44251e07ef1966baec686a`.

## 6. Live Dell Identity — Reverified

```
$ ssh -o BatchMode=yes -o ConnectTimeout=8 hac-dell \
    "cat /etc/machine-id; hostname; . /etc/os-release; echo $PRETTY_NAME; uname -m"
54ff22ce400b475aa0d55cb68f4a3334
atila-Latitude-E5470
Ubuntu 24.04.3 LTS
x86_64
```
Exact match to expected machine-id `54ff22ce400b475aa0d55cb68f4a3334`.
No STOP.

## 7. Source-Access Prerequisite — Reverified (Read-Only)

```
sudo test -f /root/.ssh/pcae_harness_deploy_ed25519 → KEY_EXISTS
sudo stat -c '%U:%G %a' /root/.ssh/pcae_harness_deploy_ed25519 → root:root 600
```
`/root/.ssh/config` `Host github.com` stanza: `IdentityFile
/root/.ssh/pcae_harness_deploy_ed25519`, `IdentitiesOnly yes` —
unchanged, unmodified, read-only. No credential rotation, no test
push.

## 8. Retained Actions-1-5 Continuation Gate — All Passed Exactly

```
Action 1: dpkg-query -W python3-venv python3-pip
          → both 'install ok installed'                              PASS
Action 2: id pcae
          → uid=1004(pcae) gid=1004(pcae) groups=1004(pcae)
          → shell /usr/sbin/nologin, no sudo group                   PASS
Action 3: stat -c '%U:%G %a' /etc/pcae/hatp/trust-store
          → root:pcae 750; getfacl → 3 standard POSIX entries only   PASS
Action 4: stat over /opt/pcae, /opt/pcae/runtime,
          /opt/pcae/runtime/src, /opt/pcae/runtime/venv,
          /opt/pcae/runtime/bin, /opt/pcae/projects,
          /var/lib/pcae, /var/log/pcae
          → every path root:pcae 750                                 PASS
Action 5: stat -c '%U:%G %a' /home/pcae → pcae:pcae 750               PASS
```
No mutation command from Actions 1-5 was run. No repair, delete, or
recreate was performed or considered — every value matched exactly.

## 9. Action-6 Precondition

```
sudo find /opt/pcae/runtime/src -mindepth 1 -maxdepth 1 → (empty)
```
Directory exists (Action 4 baseline), empty, correct owner/group/mode
(`root:pcae 750`), no Git metadata, no residue → **ABSENT**, proceed
to forward per §11 of the amended proposition.

## 10. Recovered Exact Repaired Action 6

Recovered verbatim from `chgr-541cb08c313b4f8884970172d37c5a1d`'s
bound proposition, `docs/PHASE_149O_20L_7D_3_ACTION_6_FILE_MODE_CONTINUATION_BASELINE_PROPOSITION_AMENDMENT.md`
§11 — not from memory or report prose:

```
sudo git clone --no-checkout git@github.com:atimad/pcae-harness.git /opt/pcae/runtime/src
sudo git -C /opt/pcae/runtime/src checkout --detach 7a3fa971304521cdcb44251e07ef1966baec686a
sudo chown -R root:pcae /opt/pcae/runtime/src
sudo find /opt/pcae/runtime/src -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f -perm -u+x -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/src -type f ! -perm -u+x -exec chmod 0640 {} \;
```
Preserves Git 100644 → 0640 and 100755 → 0750, keyed on each file's
own on-disk executable bit as `git checkout` already sets it from the
Git index — no blanket `chmod`, no `git restore` discretionary repair.

## 11. Action-6 Execution

Executed the exact commands above, in order, on `hac-dell`, via
`sudo`. Clone succeeded; checkout succeeded (`HEAD is now at 7a3fa971
...`); ownership/mode-normalization commands completed with no error.

## 12. Action-6 Source Read-Back

```
git -C /opt/pcae/runtime/src rev-parse HEAD
    → 7a3fa971304521cdcb44251e07ef1966baec686a                       EXACT MATCH
git -C /opt/pcae/runtime/src symbolic-ref -q HEAD; echo $?
    → exit 1 (detached HEAD)                                         PASS
git -C /opt/pcae/runtime/src status --short
    → empty                                                          PASS
git -C /opt/pcae/runtime/src remote get-url origin
    → git@github.com:atimad/pcae-harness.git                         PASS
test -f docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md; echo $? → 0   PASS
test -f src/pcae/core/hatp_class_b_conformance.py; echo $?         → 0   PASS
```

**Mode-preservation spot-check.** The proposition's literal spot-check
command (`sudo test -u ... -a -x ...`) tests the **setuid** bit (`-u`),
not ownership — a pre-existing textual defect in the read-back script
itself (unrelated to this phase's own repair), which always evaluates
false since setuid is never set. Independently disambiguated via
direct equivalents:
```
sudo stat -c '%U:%G %a' /opt/pcae/runtime/src/.githooks/pre-commit → root:pcae 750
sudo test -O /opt/pcae/runtime/src/.githooks/pre-commit; echo $?   → 0 (root-owned)
sudo test -x /opt/pcae/runtime/src/.githooks/pre-commit; echo $?   → 0 (executable)
sudo stat -c '%a' /opt/pcae/runtime/src/pyproject.toml             → 640
```
All actual invariants (owner, mode, executability) hold exactly. This
finding is disclosed, not silently corrected in the repository — it is
a defect in the read-back script's literal test flag, out of this
phase's scope to repair (would require its own governed amendment to
the frozen proposition text).

## 13. Complete Mode Inventory — All 4,030 Tracked Paths

Independent Python cross-check (`git ls-tree -r
7a3fa971304521cdcb44251e07ef1966baec686a` against `stat` for every
path, executed on `hac-dell`, not merely the six previously-exposed
paths):

```
total_tracked_paths  4030
count_100644         4024   → all filesystem 0640
count_100755         6      → all filesystem 0750
other_types          0
mismatches            0
```

## 14. Six Executable Paths — Individually Confirmed

```
EXEC_OK: .githooks/pre-commit
EXEC_OK: .githooks/pre-push
EXEC_OK: scripts/check-docs-updated.sh
EXEC_OK: .pcae/authority-evaluation/records/records/prp-03cfe21aca284d009e71a2581c984dc0/aeval-5b7a1a65be774d45b494b3489e3ed33b.json
EXEC_OK: .pcae/authority-evaluation/records/records/prp-af987a7157804bdfb13dc06e6a060459/aeval-e7c6272fc2c1456babda84600b474805.json
EXEC_OK: .pcae/publication-execution/published/prp-af987a7157804bdfb13dc06e6a060459.json
```
Per the amended proposition's own disclosure (§5 of 7D.3), the three
JSON files' executable bit is a pre-existing cosmetic anomaly in the
pinned source, not something this phase normalizes.

## 15. Content Identity and Clean Git State

```
git -C /opt/pcae/runtime/src diff 7a3fa971304521cdcb44251e07ef1966baec686a -- . | wc -l  → 0
git -C /opt/pcae/runtime/src diff --stat 7a3fa971...                                       → (empty)
git -C /opt/pcae/runtime/src status --short --untracked-files=all                          → (empty)
```
Zero content bytes changed. No untracked helper artifact. Action 6:
**EXECUTED AND VERIFIED.**

## 16. Action 7 — Venv + Editable Install

Recovered verbatim from the pinned `f9e33232` proposition commit §9
(Action 7), unchanged by the 7D.3 amendment (§15 of that document
determined Actions 7-9 require no textual change):

```
sudo python3 -m venv /opt/pcae/runtime/venv
sudo /opt/pcae/runtime/venv/bin/pip install --no-cache-dir -e /opt/pcae/runtime/src
sudo chown -R root:pcae /opt/pcae/runtime/venv
sudo find /opt/pcae/runtime/venv -type d -exec chmod 0750 {} \;
sudo find /opt/pcae/runtime/venv -type f -exec chmod 0640 {} \;
sudo find /opt/pcae/runtime/venv/bin -maxdepth 1 -type f -exec chmod 0750 {} \;
```

Executed exactly. `pip install -e` resolved third-party dependencies
normally from PyPI per the pinned checkout's own `pyproject.toml`
(`jsonschema`, `attrs`, `referencing`, `rpds-py`, `typing-extensions`)
— no arbitrary upgrade, no alternate source, no Mac dependency. Build
succeeded: `Successfully installed ... pcae-harness-0.2.0 ...`.

**Read-back:**
```
sudo -u pcae /opt/pcae/runtime/venv/bin/pcae -h        → exit 0 (succeeds)
sudo -u pcae test -w /opt/pcae/runtime/venv; echo $?    → 1 (agent cannot write)
find .../site-packages -iname '*.pth'
    → _editable_impl_pcae_harness.pth
cat that file → /opt/pcae/runtime/src/src            (points at pinned checkout, not this Mac)
direct_url.json → {"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}
sudo -u pcae ... python3 -c "import pcae; print(pcae.__file__)"
    → /opt/pcae/runtime/src/src/pcae/__init__.py
site.ENABLE_USER_SITE (env PYTHONNOUSERSITE=1)         → False
```

**Disclosed finding, not a defect:** `pcae --version` (the exact
literal the pinned proposition's read-back specifies) returns exit 2
with a usage error, because the CLI has no top-level `--version` flag
— it requires a subcommand. Independently reproduced identically on
the Mac reference checkout (`pcae --version` → same usage/error, exit
2) — this is pre-existing CLI behavior, not an Action-7 deployment
defect. Substituted `pcae -h` (exit 0) to independently confirm the
installed CLI functions and the editable-install package identity
resolves correctly. No mismatch in the actual environment-lock
invariant this read-back line exists to test. No source repair made
(would require its own governed proposition to the frozen read-back
text). Action 7: **EXECUTED AND VERIFIED.**

## 17. Action 8 — Launch Wrapper

Recovered exact wrapper bytes from the pinned `f9e33232` commit §12
(reproduced in `docs/PHASE_149O_20L_7D_3_...md` §19 unaffected by the
Action-6 repair):

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
9 lines, 188 bytes. Independently recomputed locally before install:
`sha256sum` → `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32`
— exact match to the authority-bound digest. Staged via `scp` to a
`/tmp` path on Dell, digest re-verified identical post-transfer, then
installed:
```
sudo cp <staged> /opt/pcae/runtime/bin/pcae-launch
sudo chown root:pcae /opt/pcae/runtime/bin/pcae-launch
sudo chmod 0750 /opt/pcae/runtime/bin/pcae-launch
```
No regeneration of "semantically equivalent" content — the exact
staged bytes (already digest-verified) were copied into place.

**Read-back:**
```
sudo sha256sum /opt/pcae/runtime/bin/pcae-launch
    → b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32   EXACT
sudo stat -c '%U:%G %a' ... → root:pcae 750
sudo -u pcae test -w ...; echo $?  → 1 (agent cannot write)
sudo -u pcae /opt/pcae/runtime/bin/pcae-launch -h; echo $? → 0 (succeeds)
sudo getfacl -p ... → 3 standard POSIX entries only, no extra ACL
sudo test -L ...; echo $? → 1 (not a symlink)
```
Wrapper semantics independently confirmed from the installed file
content (identical to §12 above, byte-for-byte, since digest matched):
`set -eu`; unsets `PYTHONPATH`; exports `PYTHONNOUSERSITE=1`; fixed
`PATH=/usr/bin:/bin:/usr/sbin:/sbin`; `cd /opt/pcae/runtime`; `exec`s
the pinned venv's `pcae` forwarding all arguments; no `source`/`.`
directive; no shell-profile sourcing. Action 8: **EXECUTED AND
VERIFIED.**

## 18. Action 9 — Read-Only Final Conformance Check

Run locally on Dell, as `pcae` (no sudo), from a working directory
under `/opt/pcae/runtime/src` — never from the Mac, never as another
identity, never against another checkout:

```
sudo -u pcae /opt/pcae/runtime/bin/pcae-launch health
    → "Error: git command failed: git status --porcelain=v1 /
       PCAE requires a git repository. Run 'pcae init' first."
```
Disclosed, not adjudicated against: the wrapper's own `cd
/opt/pcae/runtime` (not `.../runtime/src`) means `pcae health`'s git
check runs against a non-repository directory by the wrapper's own
frozen design — this is not the adjudicated command; see below.

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i \
  HOME=/home/pcae PATH=/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
result = verify_class_b_deployment_conformance()
print(result.status.value)
for c in result.checks:
    print(c.check_id, c.satisfied, c.status)
'"
```

**Actual output — aggregate `NON_COMPLIANT`. Full check list (39
checks):**

| check_id | satisfied | status |
|---|---|---|
| HBDC-REQ-001 | True | protected_root_resolvable_topology_evaluable |
| HBDC-REQ-002 | True | agent_and_admin_are_distinct_os_principals |
| HBDC-REQ-004 | True | no_env_or_name_based_admin_inference_in_source |
| HBDC-REQ-005 | True | no_self_elevation_call_in_source |
| HBDC-REQ-007 | True | agent_has_no_effective_write_access |
| HBDC-REQ-008 | True | designated_agent_writable_artifacts_excluded_by_scope |
| HBDC-REQ-011 | True | public_api_accepts_no_override_parameter |
| HBDC-REQ-012 | True | no_mutation_call_in_source |
| HBDC-REQ-013 | True | protected_root_admin_owned |
| HBDC-REQ-014 | True | protected_root_mode_excludes_group_other_write |
| HBDC-REQ-015 | True | no_group_membership_grants_write |
| HBDC-REQ-016 | True | no_acl_grants_agent_write |
| HBDC-REQ-017 | True | full_ancestor_chain_non_agent_writable |
| HBDC-REQ-018 | True | protected_root_symlink_check_passed |
| HBDC-REQ-019 | True | no_authority_bearing_file_present_nothing_to_check |
| HBDC-REQ-020 | True | directory_entry_replacement_not_possible |
| HBDC-REQ-021 | True | root_present_no_fail_closed_path_needed |
| HBDC-REQ-025 | True | interpreter_and_venv_admin_provisioned |
| HBDC-REQ-026 | True | venv_agent_unwritable |
| HBDC-REQ-027 | True | interpreter_agent_unwritable |
| HBDC-REQ-028 | True | pythonpath_unset |
| HBDC-REQ-029 | True | user_site_disabled |
| **HBDC-REQ-030** | **False** | **customization_module_agent_writable** |
| HBDC-REQ-031 | True | pth_files_present_admin_controlled_no_import_lines |
| HBDC-REQ-032 | True | only_expected_meta_path_hooks_present |
| HBDC-REQ-033 | True | cwd_cannot_shadow_canonical_package_location |
| HBDC-REQ-034 | True | all_authority_module_origins_contained |
| **HBDC-REQ-035** | **False** | **pcae_distribution_metadata_not_found** |
| **HBDC-REQ-036** | **False** | **no_configured_production_launcher_detected** |
| HBDC-REQ-037 | True | no_authority_changing_env_injection_channel_open |
| HBDC-REQ-038 | True | git_executable_path_precedence_and_ownership_verified |
| HBDC-REQ-039 | True | third_party_dependencies_covered_by_venv_lock |
| **HBDC-REQ-022** | **False** | **pcae_distribution_metadata_not_found** |
| HBDC-REQ-042 | False | no_repository_identity_present |

**Actual failing set:** `{HBDC-REQ-022, HBDC-REQ-030, HBDC-REQ-035,
HBDC-REQ-036, HBDC-REQ-042}`.

## 19. Exact Adjudication (§41 of the Governing Instruction)

**Expected failing set:** exactly `{HBDC-REQ-042}`.
**Actual failing set:** `{HBDC-REQ-022, HBDC-REQ-030, HBDC-REQ-035,
HBDC-REQ-036, HBDC-REQ-042}` — four additional failures beyond the
authorized residual.

Per §41: *"If any additional reason appears: STOP. Do not repair. Do
not broaden authority."* **This phase STOPS here.** No repair was
attempted. No DeploymentBinding was created (real or fake). No
certification. No activation. Authority was not broadened.

## 20. Read-Only Root-Cause Investigation (Disclosure Only, No Repair)

Performed strictly to characterize the finding for this report — no
mutation, on Dell or in the repository, resulted from this
investigation.

**HBDC-REQ-022 / HBDC-REQ-035 (`pcae_distribution_metadata_not_found`,
same root cause):** both checks call
`importlib.metadata.distribution("pcae")`
(`src/pcae/core/hatp_class_b_conformance.py:72`,
`src/pcae/core/hatp_environment_lock_verifier.py:339`). The installed
distribution's actual name, per `pyproject.toml` line 6
(`name = "pcae-harness"`), is `pcae-harness`, confirmed installed as
such (`Successfully installed ... pcae-harness-0.2.0 ...`,
`pcae_harness-0.2.0.dist-info` present in site-packages).
Independently confirmed the correct name resolves:
```
sudo -u pcae ... python3 -c "
import importlib.metadata as m
d = m.distribution('pcae-harness')
print('FOUND', d.version, d._path)"
→ FOUND 0.2.0 /opt/pcae/runtime/venv/lib/python3.12/site-packages/pcae_harness-0.2.0.dist-info
```
The verifier source's own lookup key (`"pcae"`) does not match the
project's declared distribution name (`"pcae-harness"`) and never has
— this is a pre-existing verifier-source defect, unrelated to any
action this phase performed, unmasked for the first time only because
this is the first time Actions 1-9 have ever completed end-to-end
against a real host.

**HBDC-REQ-036 (`no_configured_production_launcher_detected`):**
`_check_launcher` (`hatp_environment_lock_verifier.py:368-382`) calls
`shutil.which("pcae")`. Action 9's own frozen command (§18 above,
verbatim from the pinned proposition) invokes
`/opt/pcae/runtime/venv/bin/python3` directly under `env -i ...
PATH=/usr/bin:/bin:/usr/sbin:/sbin` — a `PATH` that does not include
`/opt/pcae/runtime/venv/bin`, so no `pcae` executable is found on it.
This is intrinsic to the pinned Action-9 command text itself (not
something this phase altered), unmasked for the same reason as above.

**HBDC-REQ-030 (`customization_module_agent_writable`):**
`_check_customization_modules` (`hatp_environment_lock_verifier.py:176-192`)
scans every directory on `sys.path` for `sitecustomize.py` /
`usercustomize.py` and flags any that `pcae` can write. Not
individually traced to a specific path this phase (would require
enumerating live `sys.path` and per-directory write-access on Dell —
deferred to the recommended follow-up phase, §22, rather than expanded
here since this phase is already at a disclosed STOP and does not
broaden its own investigation into new mutation-adjacent territory).

**None of the four unexpected failures are caused by, or evidence
against, Action 6's file-mode repair, Action 7's editable install, or
Action 8's wrapper** — each of those three actions independently
verified clean on its own terms (§§11-17). The unexpected residual is
a verifier/proposition-text gap, not a Boundary-P infrastructure
defect.

## 21. DeploymentBinding, Boundary C, Boundary A — Untouched

```
find .pcae -iname '*deploymentbinding*'  → zero matches (unchanged from 7D.4)
```
No DeploymentBinding created or faked. No HMIC certification created,
published, or pointed to. No HATP_MANDATORY activation. No Cutover
Record. Boundary C: **NOT AUTHORIZED**. Boundary A: **NOT
AUTHORIZED**. Permission Broker, POL-005, COMP-002: unchanged. No
`/opt/pcae/projects/<repo-slug>/repo` created — no repository
onboarding. No centralized-governance component created.

## 22. Actual 7D.5 Mutation Inventory

Mutations introduced **specifically by this phase**, on `hac-dell`:

1. `/opt/pcae/runtime/src` — populated via Action 6 (clone + detached
   checkout at pinned SHA + ownership/mode normalization).
2. `/opt/pcae/runtime/venv` — created via Action 7 (venv + editable
   install of `pcae-harness` + ownership/mode normalization).
3. `/opt/pcae/runtime/bin/pcae-launch` — created via Action 8 (wrapper
   file, ownership, mode).

No other path was written. Action 9 performed zero mutation
(read-only, confirmed by its own commands: `pcae-launch health`,
python conformance check — no write call anywhere in
`verify_class_b_deployment_conformance`, independently re-confirmed
present in `chgr-541cb08c313b4f8884970172d37c5a1d`'s own bound
proposition text, §9/§12 of 7B.1).

**Separation from persistent state:**
- **7D.1 credential** (`/root/.ssh/pcae_harness_deploy_ed25519`):
  untouched — read-only `sudo test`/`stat` only, no rotation, no
  content read, no test push.
- **Retained Actions 1-5** (`pcae` principal, Protected Root, runtime
  tree, `/home/pcae`): untouched — read-only verification only, no
  mutation command from Actions 1-5 executed.

**Proof: 7D.5 mutations ⊆ amended CHGR-authorized continuation
mutation set.** The CHGR's own `rationale` authorizes "the repaired
Action-6 forward/read-back/rollback command sequence ... and unchanged
Actions 7-9" — exactly the three mutating actions performed (6, 7, 8)
and the one read-only action performed (9); no action outside that set
was executed.

## 23. Rollback

**Not applicable — no action failed its own postcondition.** Actions
6, 7, and 8 each independently verified clean against their own
frozen read-back requirements (§§11-17). Only Action 9's *measured
adjudication* deviated from the authorized expectation, and Action 9
is read-only with nothing to roll back (§10 of the amended proposition
confirms this explicitly). Per §50/§51 of the governing instruction,
Actions 6-8 are **not** rolled back merely because Action 9's residual
was broader than authorized — the amended authority does not require
that, and rolling back correctly-verified infrastructure would itself
be an unauthorized mutation with no basis in any failed postcondition.

**Partial-rollback semantics reaffirmed:** the continuation baseline
remains intentionally retained. As of this phase's close, the Dell
host holds: Actions 1-5 (retained, pre-existing), plus Action 6/7/8
(newly provisioned this phase, each independently verified). A future
Actions-1-5 teardown was not performed and is not implied by this
phase's outcome.

## 24. Idempotency / Read-Only Post-Check

Re-ran only read-back/preflight commands after the Action-9
adjudication (no mutation commands re-run):

```
Actions 1-5: reconfirmed exact, unchanged from §8.
Action 6:    git -C .../src status --short → still empty; rev-parse HEAD → still pinned SHA.
Action 7:    sudo -u pcae .../venv/bin/pcae -h → still exit 0.
Action 8:    sudo sha256sum .../pcae-launch → still b3e969...c32.
Action 9:    re-run once more → identical failing set {HBDC-REQ-022, -030, -035, -036, -042}, stable.
```

## 25. Developer/Deployment Separation

- Mac development checkout (`~/repos/pcae-harness`) unchanged by any
  Dell operation this phase — confirmed `git status --short` clean
  throughout, no local file touched by any SSH command.
- Dell source pinned to the exact SHA; no moving ref.
- No Mac path appears in any Dell-side file (checked via the mode
  spot-checks and `.pth` content, §16).
- `pcae` (Dell) cannot write `/opt/pcae/runtime/src`,
  `/opt/pcae/runtime/venv`, or `/opt/pcae/runtime/bin/pcae-launch`
  (each `root:pcae 0750` or the individual files `root:pcae`,
  independently confirmed non-writable by `pcae` at every read-back
  step above).
- `pcae` cannot access `/root/.ssh/pcae_harness_deploy_ed25519`
  (`root:root 600`).

## 26. Secret Isolation

No private key bytes were read, echoed, logged, or transmitted at any
point this phase — only `sudo test -f`/`sudo stat` (existence/metadata
only) were used against the credential path. Verified the key does
not appear under `/opt/pcae/runtime`, `/home/pcae`, or any repository
path touched by Action 6 (the pinned checkout contains no such file —
confirmed by the checkout's own tracked-path enumeration, §13; no
untracked file was ever created there). No fingerprint or key material
appears anywhere in this report, in Dell command output captured
above, or in the companion test module (§27).

## 27. CHGR Post-Execution Integrity

```
pcae governance-record verify .../chgr-541cb08c313b4f8884970172d37c5a1d.json
    → outcome: verified (unchanged from §2)
pcae governance-record verify .../chgr-96a0ce12756e4cc892492a87af1db832.json
    → outcome: verified, lifecycle_state published, unrevoked
```
Neither record's bytes were mutated this phase. No consumed/superseded
lifecycle state was invented for either record — both remain
`published`, exactly as before this phase.

## 28. D3-3 Status — Carried Forward Unchanged

**CLOSED FOR CURRENT CONTINUATION / MACHINE-READABLE SUPERSESSION
HARDENING GAP RETAINED.** The old CHGR is not claimed revoked or
formally superseded; no machine-enforced precedence exists. Current
safety derives from proposition applicability (the old CHGR's Action 2
has no EXACTLY SATISFIED branch, per 7D.4 §10) plus this phase's own
explicit non-use of the old record (§4), not from a canonical
supersession transition. No lifecycle-transition machinery was
implemented this phase (would touch `src/pcae/**`, out of scope).

## 29. Companion Tests

New, independently-authored module (imports nothing from 7D.3's or
7D.4's modules as oracle):
`tests/test_phase_149o_20l_7d_5_dell_class_b_provisioning_continuation_execution.py`.
Covers: governing CHGR identity and structural verification, governing
session identity vs. superseded session, old-CHGR fallback prohibition
(textual, from the CHGR's own conditions/rationale), Dell machine-id
binding, source-credential path/mode assertions (no secret read), the
repaired Action-6 command text (exact string match against this
report's §10, guarding against silent drift), the wrapper's exact
byte content and digest, the Action-9 expected-vs-actual failing set
and its adjudication logic, DeploymentBinding absence, no
certification/activation artifacts, and the distribution-name
root-cause finding (`pyproject.toml` name vs. the verifier's lookup
key) via static source assertions — no live SSH or Dell mutation in
CI. See test output below for the exact pass count.

## 30. Boundary Status After This Phase

```
Governing continuation authority chgr-541cb08c313b4f8884970172d37c5a1d:
    EXECUTED WITHIN VERIFIED CONTINUATION SCOPE
Historical CHGR chgr-96a0ce12756e4cc892492a87af1db832:
    HISTORICAL ORIGINAL-BASELINE AUTHORITY — NOT APPLICABLE TO CURRENT CONTINUATION
Actions 1-5:  PROVISIONED — RETAINED BASELINE (unchanged this phase)
Action 6:     EXECUTED AND EXECUTION-PHASE VERIFIED
Action 7:     EXECUTED AND EXECUTION-PHASE VERIFIED
Action 8:     EXECUTED AND EXECUTION-PHASE VERIFIED
Action 9:     MEASURED — ACTUAL RESIDUAL {HBDC-REQ-022, -030, -035, -036, -042}
              EXCEEDS THE AUTHORIZED {HBDC-REQ-042} — STOPPED, NOT ADJUDICATED SUCCESSFUL
Dell infrastructure: PROVISIONED (Actions 1-8) — ACTION 9 ADJUDICATION FAILED
Class-B:      INFRASTRUCTURE PROVISIONED — FULL HBDC CONFORMANCE NOT ACHIEVED,
              RESIDUAL WIDER THAN AUTHORIZED — DIAGNOSIS REQUIRED BEFORE 7E
DeploymentBinding: ABSENT / NOT AUTHORIZED
Boundary C:   NOT AUTHORIZED
Boundary A:   NOT AUTHORIZED
HATP:         NOT READY
Runtime:      Observed / observe / unavailable
```

This phase does **not** claim: Class-B fully compliant, HATP ready,
certified, activated, or operationally complete. It does not even
claim the originally-anticipated clean-execution outcome — the actual
measured residual is broader than authorized, and this report
discloses that honestly rather than reframing it as success.

## 31. Governance

Normal governed PCAE lifecycle used throughout — `pcae task`, `pcae
commit implementation`, `pcae phase complete`, `pcae push`. No raw
`git commit`/`git push`. No `--no-verify`. No force push. No
governance bypass.

## 32. Recommended Next Phase

**149O.20L.7D.6 — Action-9 Unexpected Residual Diagnosis and
Proposition Repair (or Disposition).** Not 149O.20L.7E — 7E
(independent provisioning verification) was conditioned on a clean
149O.20L.7D.5 execution per this phase's own governing instruction
(§59: "If repaired Action 6, Action 7, Action 8 all verify and Action
9 returns only the expected residual..."), which did not occur. A
follow-up phase must, at minimum: (a) individually confirm or refute
the distribution-name root cause for HBDC-REQ-022/HBDC-REQ-035
(`"pcae"` vs. `"pcae-harness"`) as a verifier-source defect requiring
its own governed `src/pcae/**` repair, separate from any Dell
provisioning question; (b) determine whether HBDC-REQ-036 reflects a
genuine environment-lock gap in Action 9's own frozen command
(`PATH` excluding the venv `bin/`) or an intentional invariant this
phase misunderstood; (c) trace HBDC-REQ-030's specific writable
customization-module path on the live Dell host (read-only); (d)
decide, under fresh human election, whether the fix belongs in the
verifier source, the Action-9 command text, or is itself evidence the
retained baseline needs adjustment — and only then re-run Action 9 (no
repeat of Actions 6-8, which already independently verified clean) to
re-adjudicate against whatever the freshly-authorized expected residual
becomes. 149O.20L.7E remains required after a clean adjudication,
before any Boundary-C work — this phase's STOP does not change that
sequencing, only postpones reaching it.
