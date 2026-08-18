# Phase 149O.20L.7O.2A.4 — RepositoryIdentity Write-Path Remediation Execution

## 1. Scope

Execute exactly the independently verified, human-approved `.pcae`
permission remediation authorized by CHGR `chgr-86aeb5cfa7c44020ad002bc9f80c5856`
(human-confirmed preview digest
`616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd`,
decision session `CDS-bc9a70fc-3913-4c8b-b95e-50ca0c26091c`).

The sole authorized mutation:

```
chmod 1770 /opt/pcae/runtime/src/.pcae
```

on host `hac-dell` (hostname `atila-Latitude-E5470`, machine-id
`54ff22ce400b475aa0d55cb68f4a3334`), followed by mandatory read-back.
This phase does **not** create RepositoryIdentity, does **not** create
DeploymentBinding, and stops after the permission transition and its
verification.

## 2. Phase-entry state

- Phase-entry commit: `8fbdf18e` (Phase 149O.20L.7O.2A.3: repair
  pushed_status/pcae_push_check trust fields post-push).
- `git status --short`: clean.
- `git log origin/main..HEAD`: 0 commits ahead at entry.
- `pcae health`: healthy. `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings only (pre-existing, unrelated —
  historical `tasks/done/` entries predating this phase, outside this
  phase's allowed-file scope; identical class of warning already
  disclosed and accepted in 149O.20L.7O.2A.3's own report).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: recommended next phase confirmed
  as this exact phase, 149O.20L.7O.2A.4, chmod-only.
- `pcae phase-report reconcile --phase-id 149O.20L.7O.2A.3`: reconciled,
  mutation: none (inspection only).

## 3. Immediate pre-mutation CHGR re-verification

Re-read `chgr-86aeb5cfa7c44020ad002bc9f80c5856` fresh this phase (not
trusting 149O.20L.7O.2A.3's own report as an oracle):

- `decision_subject`: "Authorize changing only
  `/opt/pcae/runtime/src/.pcae` on hac-dell from `root:pcae 0750` to
  `root:pcae 1770` (chmod 1770) ... Excludes RepositoryIdentity and
  DeploymentBinding..." — exact path/mode match confirmed.
- `decision_maker_identity_evidence.identifier`: "Atila Madai",
  `evidence_kind`: `typed_confirmation_only`, captured
  `2026-08-18T10:30:12.528314Z`.
- `assurance_level`: `L0`.
- `conditions` §1–23 restated the exact target, before/after state,
  operation, and all 20 exclusions (RepositoryIdentity, DeploymentBinding,
  Protected Root, source mutation, venv/wrapper, Permission Broker,
  certification, Boundary A/C, HATP_MANDATORY, recursive/chown/setfacl,
  unrelated paths) — identical in substance to this governing prompt.
- Ran `pcae governance-record verify` with all three related artifacts
  (confirmation, provenance, integrity):

```
pcae governance-record verify .pcae/publication-execution/records/chgr-86aeb5cfa7c44020ad002bc9f80c5856.json \
    --related .pcae/publication-execution/records/chgrconf-698eefcec95841ef8350e94fa7a59ea8.json \
    --related .pcae/publication-execution/records/chgrprov-5a681f551c3646af81d7ecdb1a3ccff1.json \
    --related .pcae/publication-execution/records/chgrintg-2fa93bd13e7e440f8c98a283cff99872.json \
    --json
```

- `outcome`: `verified`.
  - `schema_shape`: passed
  - `digest_self_consistency`: passed
  - `lifecycle_structural_legality`: passed
  - `confirmation_binding`: passed
  - `assurance_truthfulness`: passed
  - `provenance_consistency`: passed
  - `integrity_consistency`: passed
  - `template_resolution`: skipped (no matching `decision_template`-typed
    related artifact exists anywhere in this repository — the same
    disclosed, non-defect skip already established in 149O.20L.7O.2A.3).
- Uniqueness re-confirmed independently: read all six `chgr-*.json`
  records under `.pcae/publication-execution/records/`; only
  `chgr-86aeb5cfa7c44020ad002bc9f80c5856` names
  `/opt/pcae/runtime/src/.pcae` in its `decision_subject`.
  `chgr-541cb08c313b4f8884970172d37c5a1d` ("Amended continuation
  authorization for Dell Class-B Boundary-P provisioning ... repairs
  Action 6 file-mode defect") is a distinct, earlier, unrelated
  continuation authorization from Phase 149O.20L.7D.3 — not a fallback
  and not consulted. No CHGR carries a `revoked`/`superseded`
  `lifecycle_state`.

No mismatch found. Proceeded to fresh Dell preflight.

## 4. Fresh Dell preflight (live, this phase)

Opened a fresh SSH session to `hac-dell`.

| Check | Expected | Live result | Match |
|---|---|---|---|
| `hostname` | `atila-Latitude-E5470` | `atila-Latitude-E5470` | yes |
| `/etc/machine-id` | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` | yes |
| `git -C /opt/pcae/runtime/src rev-parse HEAD` | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` | yes |
| `git status --porcelain` | clean | empty | yes |
| detached HEAD | detached | detached (`symbolic-ref -q HEAD` fails) | yes |
| `.pcae` owner:group:mode | `root:pcae 0750` | `root:pcae 750` | yes |
| `.pcae` extended ACL | none | `getfacl -p`: `user::rwx`, `group::r-x`, `other::---` only | yes |
| RepositoryIdentity under `.pcae` | absent | not found | yes |
| DeploymentBinding / Protected Root (`/etc/pcae/hatp/trust-store`) | empty | `ls -la` → only `.`/`..`, dated `Aug 15 08:55` | yes |
| Certification artifacts under `/etc/pcae` | absent | none found | yes |
| HMIC digest (`derive_implementation_scope_digest`, live) | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` | yes |
| Canonical HBDC (`verify_class_b_deployment_conformance`, live) | `NON_COMPLIANT`, sole residual `HBDC-REQ-042`, `HBDC-REQ-036` True | `NON_COMPLIANT`, sole residual `HBDC-REQ-042` (`no_repository_identity_present`), `HBDC-REQ-036` True | yes |

Zero drift on every dimension. HMIC/HBDC checks were run the same way as
149O.20L.7O.2A.3: two disposable, read-only Python scripts copied to
`/tmp` via `scp`, executed as `pcae` under
`sudo -n -u pcae env -i PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/home/pcae PYTHONNOUSERSITE=1`,
and deleted (`rm -f`) immediately after use; deletion was independently
confirmed (`ls` on the deleted paths reported "No such file or directory").

## 5. Independent command safety review (pre-mutation)

Before execution, independently reviewed the exact command as a systems
operation:

- Absolute path exact: `/opt/pcae/runtime/src/.pcae` — yes.
- Target is a directory: confirmed via `stat -c %F` → `directory`.
- Target is not a symlink: confirmed via `test -L` (false) and `stat -c %F`
  (not `symbolic link`).
- No recursive flag: command has no `-R`/`--recursive`.
- No ownership change: `chmod` alone does not touch owner/group.
- No ACL change: no `setfacl` invoked; `.pcae` carried no extended ACL
  entries before mutation, so `chmod` only updates the three base
  entries mirrored from the mode bits.
- Sticky-bit mode encoded correctly: `1` (S_ISVTX) + `7` (owner rwx) +
  `7` (group rwx) + `0` (other) = `1770`, matching the CHGR exactly.
- Single target, cannot affect Protected Root or any unrelated path:
  the command names exactly one absolute path.
- Principal: SSH session user `codex` (invoking), executing via
  `sudo -n` as `root`; confirmed via `sudo -n -l` this session:
  `(ALL : ALL) NOPASSWD: ALL` on `atila-Latitude-E5470` for `codex` —
  the same pre-existing sudoers scope already used, read-only, in
  every prior 149O.20L.7* Dell phase.

No technical objection found. Proceeded to mutation.

## 6. The mutation

Executed exactly:

```
sudo -n chmod 1770 /opt/pcae/runtime/src/.pcae
```

- Invoking principal: `codex` (SSH session user) via `sudo -n` as `root`.
- Pre-mutation timestamp: `2026-08-18T11:27:28.649460109Z`.
- Exit status: `0`.
- Post-mutation timestamp: `2026-08-18T11:27:28.661248436Z`.

No second mutation was issued before read-back.

## 7. Immediate read-back

```
stat -c "owner=%U group=%G mode=%a type=%F" /opt/pcae/runtime/src/.pcae
  -> owner=root group=pcae mode=1770 type=directory

test -L /opt/pcae/runtime/src/.pcae
  -> not a symlink

getfacl -p /opt/pcae/runtime/src/.pcae
  -> # owner: root
     # group: pcae
     # flags: --t
     user::rwx
     group::rwx
     other::---
```

Mode is exactly `1770`; owner/group unchanged (`root`/`pcae`); still a
directory, not a symlink; `getfacl` shows only the three base entries
derived from the mode bits (sticky flag `--t`) — no unintended extended
ACL entries were added.

## 8. Existing-entry preservation

Read-only inventory of `.pcae`'s immediate children, post-mutation:

```
find /opt/pcae/runtime/src/.pcae -maxdepth 1 -printf "%m %u:%g %y %p\n"
```

All 17 pre-existing entries (`.gitignore`, `architecture-history.json`,
`audit/`, `authority-evaluation/`, `decision-sessions/`, `exports/`,
`fleet-exports/`, `fleet.json`, `phase-completion-metadata.json`,
`phase-completion-report.md`, `phase-metadata-repairs.log`,
`policy.toml`, `publication-execution/`, `repository-intelligence/`,
`skills/`, `strategic-lineage.json`, `strategic_reviews.json`) retained
`root:pcae` ownership and their pre-existing modes (`640` for files,
`750` for directories) exactly — matching the CHGR's own §7 count of
"17 existing root-owned governed `.pcae` entries." No file was created,
deleted, or had its own owner/group/mode changed. Only the parent
directory's own mode changed, as authorized.

## 9. RepositoryIdentity / DeploymentBinding absence

- No `repository-identity.json` (or any `*repository-identity*` /
  `*RepositoryIdentity*` file) appears in the `.pcae` inventory above —
  confirmed absent, as required for a chmod-only phase.
- `/etc/pcae/hatp/trust-store` (Protected Root): re-checked live,
  post-mutation — still only `.`/`..`, dated `Aug 15 08:55`, unchanged
  from pre-mutation. No DeploymentBinding artifact exists.
- No certification artifact under `/etc/pcae` (`find ... -iname '*certif*' -o -iname '*hmic*'`
  returned no matches, pre- and post-mutation).

## 10. Source integrity

Re-checked live, post-mutation:

```
git -C /opt/pcae/runtime/src rev-parse HEAD
  -> b0840e96a7ffb12308e95828aa5927c3e7c770c0   (unchanged)
git -C /opt/pcae/runtime/src status --porcelain
  -> (empty; clean)
```

HEAD is unchanged and the detached checkout remains clean. No tracked
byte changed.

## 11. HMIC digest (post-chmod)

Recomputed live, same disposable-script method as §4:

```
derive_implementation_scope_digest(HarnessPath("/opt/pcae/runtime/src"))
  -> 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8
```

Unchanged from the pre-mutation value. A directory-mode chmod on
`.pcae` (which is not among HMIC's frozen source paths) cannot affect
this digest, and empirically did not.

## 12. Venv / wrapper (read-only)

```
sha256sum /opt/pcae/runtime/bin/pcae-launch
  -> b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32
stat -c "owner=%U group=%G mode=%a" /opt/pcae/runtime/bin/pcae-launch
  -> owner=root group=pcae mode=750
```

Wrapper digest matches the fixed constant re-verified across every
149O.20L.7* Dell phase (`b3e969...c32`), unchanged. `venv/bin/python3`
remains a symlink to `/usr/bin/python3` as before, owner/group/mode
unaffected (not touched by this phase's chmod, which targeted only
`.pcae` under `/opt/pcae/runtime/src`).

## 13. Canonical HBDC post-chmod

Ran the canonical corrected Action-9 environment live, post-mutation,
identical method to §4:

```
verify_class_b_deployment_conformance(HarnessPath("/opt/pcae/runtime/src"))
  -> status: NON_COMPLIANT
     failing: HBDC-REQ-042 (no_repository_identity_present)
     HBDC-REQ-036 satisfied: True
     total checks evaluated: 34
```

Identical to the pre-mutation baseline (§4) — the chmod did not itself
satisfy `HBDC-REQ-042` (expected: RepositoryIdentity still does not
exist) and did not introduce any new failing requirement.

## 14. Rollback

**Not triggered.** Every postcondition in §7–§13 matched its expected
value exactly:

- `.pcae` post-mode is exactly `1770` — matched.
- Owner/group unchanged — matched.
- ACL unchanged (no extended entries) — matched.
- No unrelated `.pcae` entry changed — matched.
- Source/HMIC unchanged — matched.
- HBDC gained no new failing requirement — matched.
- Target path identity unchanged (same directory, not a symlink) —
  matched.
- No unintended mutation attributable to the chmod was detected.

RepositoryIdentity remaining absent is expected, not a rollback
trigger (per governing-prompt §21).

## 15. Mutation inventory

Exactly one host state change, matching the authorized scope exactly:

```
/opt/pcae/runtime/src/.pcae
  mode: 0750 -> 1770
  owner: root (unchanged)
  group: pcae (unchanged)
  extended ACL: none (unchanged)
```

No other file, directory, permission, ownership, or ACL anywhere on
`hac-dell` was touched. No RepositoryIdentity or DeploymentBinding
artifact was created. No source, venv, or wrapper mutation occurred.

## 16. Disclosed correction carried forward

P-A′ (this chmod) fixes the directory-write provisioning issue for 38
of the 39 declared write-required `.pcae` artifacts. It does **not**
fix `architecture-history.json`, which remains a separate
producer/write-pattern issue, deferred and out of scope for this
phase. This execution does not solve the complete `.pcae` write
architecture.

## 17. Sticky-bit evidence qualification

Linux sticky-bit semantics (`S_ISVTX` / `check_sticky()` / `fs/namei.c`)
are **REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCES**. They were
**not** empirically tested using synthetic root-owned files on
`hac-dell` in this phase — per governing-prompt §24/§25, no disposable
test file was created inside `.pcae`, and no synthetic root/`pcae` file
was created elsewhere on Dell, and no RepositoryIdentity-creation
capability probe (`touch`, `mkstemp`, `ensure_repository_identity`,
`pcae init`, `echo >`) was run. The `getfacl -p` sticky flag (`--t`,
§7) and the primary-source semantics are the entirety of this phase's
sticky-bit evidence. This is not converted into an empirical
host-verification claim.

## 18. Final verdict

**PERMISSION REMEDIATION EXECUTED SUCCESSFULLY — INDEPENDENT
VERIFICATION PENDING.**

This is *not* claimed as independently verified. That determination is
reserved for Phase 149O.20L.7O.2A.5, run from a fresh session, per
governing-prompt §30.

## 19. Regression scope

No production source (`src/pcae/**`, `scripts/**`, `docs/contracts/**`,
`schemas/**`, `pyproject.toml`) was modified this phase — this phase's
only Dell action was the single authorized chmod, and this phase's only
local changes are this doc, its companion test file, and governed
task/status artifacts. `pytest -m fast_green` regression scope and
classification are recorded in the phase-completion metadata; no
runtime test outcome is attributed to the Dell chmod, which cannot
affect local test execution.

## 20. Next phase

**149O.20L.7O.2A.5 — RepositoryIdentity Write-Path Remediation
Independent Real-Host Verification.** From a fresh session, must
independently verify: exact `1770` mode; owner/group; ACL; preserved
root-owned `.pcae` entries; source SHA/cleanliness; HMIC digest; HBDC
baseline; RepositoryIdentity absence; DeploymentBinding absence;
Protected Root state; CHGR integrity; and this phase's mutation
inventory. Only after a clean 7O.2A.5 may RepositoryIdentity creation
be retried, under a new phase. RepositoryIdentity creation is **not**
retried here.

The planned strategic breakpoint (pause before Boundary C and begin
the DeepSeek Harness vs PCAE comparative architecture work, followed by
PCAE runtime-adapter/plugin architecture, after RepositoryIdentity +
DeploymentBinding first use is independently verified and HBDC is
clean) is preserved and not begun this phase.
