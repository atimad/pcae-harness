# Phase 149O.20J.7 — Class-B writesecurity/chown ACL-Right Reclassification Narrow Repair

## Status

Complete. Narrow production repair implemented and self-verified (not independently verified — see Recommended Next Phase).

## Objective

Repair the remaining known-safe-vocabulary gap in **B-149O.20J.4-1** (macOS ACL-only higher-ancestor detection defect) independently identified by Phase 149O.20J.6: `hatp_class_b_topology_verifier.py`'s `_MACOS_ACL_KNOWN_SAFE_RIGHTS` classified `writesecurity` and `chown` as harmless, when both are write-equivalent/transitively dangerous authority per primary macOS ACL documentation. This phase performs *only* that narrow reclassification (plus a bounded completeness audit of the rest of the known-safe vocabulary) — no ACL-evaluation redesign, no HMIC source-scope evolution, no readiness integration, no Class-B provisioning, no HATP certification/activation.

## Primary-Source Derivation

Before editing, independently inspected (not trusted from any prior phase's report):

- **HBDC-001 v1.0** (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`), specifically HBDC-REQ-016 (no ACL entry may grant agent write access, even where mode bits deny it), HBDC-REQ-017 (full ancestor non-writability, closing the directory-entry-replacement channel), HBDC-REQ-020 (delete/rename of an authority-bearing file's directory entry is a write-equivalent compliance failure), and CBD-1/CBD-3 (agent cannot write protected authority state; agent cannot redirect Protected Root via symlink/ACL/group/parent-path channels).
- Current production `hatp_class_b_topology_verifier.py` (869 lines, read in full).
- Phase 149O.20J.5's repair diff (commit `6a265e09`) and Phase 149O.20J.6's verification document/report (commit `4c4fd16d`), read as historical record, not as an unverified oracle.
- `man chmod`'s ACL MANIPULATION OPTIONS section, read directly on this host (`man chmod | col -b`), including the full rights vocabulary table.
- Fresh, real `chmod +a` grants on this host confirming canonical token spelling for every currently-known-safe right (`writesecurity`, `chown`, `readsecurity`, `read`, `execute`, `readattr`, `readextattr`, `list`, `search`, `file_inherit`, `directory_inherit`, `limit_inherit`, `only_inherit`) — none render with the man-page's example hyphenated form (`write-security`); all render as the exact unhyphenated tokens the parser's `_MACOS_ACL_KNOWN_RIGHTS` vocabulary already expects.

## writesecurity Semantic Derivation

`man chmod`, read on this host: `writesecurity` — *"Write an object's security information (ownership, mode, ACL)."* This is not "an immediate content-write operation" — it is authority to rewrite the object's own protection state. A holder can:
1. Edit the ACL itself (grant itself `add_file`/`write`/`delete_child`/etc. via a further `chmod +a`), or
2. Flip POSIX mode bits directly (`chmod`), or
3. Change ownership-related security metadata.

Each of these three is independently sufficient to obtain subsequent write/replacement authority over the object or its descendants. Traced to the HBDC threat model: HBDC-REQ-016/017/020 all reach beyond direct content writes to *directory-entry replacement and rename channels* on exactly this transitive-authority reasoning — a `writesecurity` grant on a higher ancestor is squarely the class of authority those requirements exist to close. The relevant question per the governing prompt is not whether an immediate content-write fails in a narrow fixture, but whether the holder can *subsequently* obtain write/replacement authority — and per `writesecurity`'s own primary definition, it plainly can.

## chown Semantic Derivation

`man chmod`: `chown` — *"Change an object's ownership."* Distinguishing the three layers the governing prompt calls for:
1. **ACL right's semantic authority**: the holder can become the object's owner.
2. **Separate OS policy restrictions**: macOS may restrict *which* ownership transitions are accepted (e.g. only to oneself, or requiring additional privilege for arbitrary reassignment) — this phase does not claim unrestricted chown-to-anyone authority.
3. **This host's same-owner conditions**: on this single-user development host, the tester is always already the object's owner, making a same-owner test non-discriminating (see below).

Independent of exactly which ownership transitions OS policy permits, `man chmod`'s own text elsewhere states plainly: *"Only the owner of a file or the super-user is permitted to change the mode of a file."* Becoming the owner (via `chown`) confers ordinary owner-mode-bit write authority (`S_IWUSR`) — the same authority `_effective_write_access` already treats as an unconditional write grant (`st_uid == agent_uid and mode & stat.S_IWUSR`). This holds even for a chown-to-self transition, which is squarely within uncontroversial policy on every POSIX-like system: an agent that can make itself the owner has thereby made itself write-authorized, without needing any other ACL grant.

Per HBDC's fail-closed posture, and because this cannot be proven harmless for all supported Class-B configurations (a chown holder could plausibly become owner of a higher ancestor under configurations this host cannot exhaustively enumerate), `chown` belongs on the dangerous/indeterminate side, not the known-safe side.

## Critique of the Same-Owner Differential (Avoided, Not Repeated)

149O.20J.5's original safety claim for `writesecurity`/`chown` rested on an empirical test that granted the right and observed no *new* effective write capability. 149O.20J.6 independently identified the flaw: on a single-user host the tester is *always* the object's owner, and an owner can already `chmod`/`chown`-equivalent-mutate their own object with **no ACL grant at all** — demonstrated again in this phase's own test suite (`test_self_owner_methodology_limitation_disclosed`). Granting vs. not granting `writesecurity`/`chown` is therefore not a meaningful differential in a same-owner fixture: it cannot distinguish the ACE's own effect from pre-existing owner authority. The only principal HBDC-REQ-009 actually contemplates holding such a grant — a non-owner agent against an admin-owned ancestor — was never tested by that differential, and this phase does not repeat it. No second local user account exists on this host, and this phase does not create one (would require separate governance and host provisioning, both out of scope). The classification instead rests on `man chmod`'s own unambiguous primary-source definition, combined with HBDC's fail-closed principle that an unproven-safe right belongs on the dangerous side.

## Exact Vocabulary Diff

`src/pcae/core/hatp_class_b_topology_verifier.py` — single file, single logical change:

- `_MACOS_ACL_WRITE_CAPABLE_RIGHTS`: added `"writesecurity"`, `"chown"`.
- `_MACOS_ACL_KNOWN_SAFE_RIGHTS`: removed `"writesecurity"`, `"chown"`.
- `_MACOS_ACL_KNOWN_RIGHTS` (the union) is unchanged — no right was added to or dropped from the combined recognized vocabulary, only reclassified between the two subsets.
- Added documentation of the transitive-authority classification principle directly above both constants (not merely a changelog note): *"a grant of this right can enable the holder to obtain write, ACL, mode, ownership, or descendant-mutation authority over the object"* — not a lexical "write-like names" heuristic.

No other function, branch, or control-flow path in the module was touched. `_acl_grants_agent_write_macos`, `_macos_acl_principal_matches_agent`, `_ancestor_chain_safe`, `_effective_write_access`, allow/deny handling, principal resolution, symlink handling, and every check function are byte-identical to the pre-repair state.

## Complete Known-Safe-Vocabulary Audit

Per-right derivation for every right remaining in `_MACOS_ACL_KNOWN_SAFE_RIGHTS` after the move, each cross-checked with a real `chmod +a` grant on this host confirming canonical token rendering:

| Right | `man chmod` definition | Transitive-authority assessment |
|---|---|---|
| `read` | Open for reading | Read-only; no content/ACL/ownership/mode/descendant effect |
| `execute` | Execute the file as script/program | Executes as the holder's own uid; confers no authority *over the object itself* (no setuid-equivalent ACL right exists) |
| `readattr` | Read an object's basic attributes | Read-only |
| `readextattr` | Read extended attributes | Read-only |
| `readsecurity` | Read an object's extended security information (ACL) | Read-only — explicitly distinguished from `writesecurity` by `man chmod`'s own adjacent, differently-worded entry (verified: no "Write" token appears in `readsecurity`'s definition snippet) |
| `list` | List directory entries | Read-only enumeration |
| `search` | Look up files by name | Read/traversal only; required for path resolution, confers no mutation |
| `file_inherit` | Inherit to files (ACE-propagation modifier) | Not a standalone permission — modifies how an *accompanying* right in the same ACE propagates to children; grants nothing by itself. A write-capable right in the same ACE is still independently detected by the existing per-right scan, so this modifier cannot mask a real grant. |
| `directory_inherit` | Inherit to directories (ACE-propagation modifier) | Same as above |
| `limit_inherit` | Clears `directory_inherit` on the inherited copy (ACE-propagation modifier) | Same as above |
| `only_inherit` | Entry inherited by created items but not considered for the object itself (ACE-propagation modifier) | Same as above. Note: an `only_inherit` ACE whose *other* rights include a write-capable token is, if anything, over-classified dangerous by the current parser (which does not special-case `only_inherit` before the write-capable scan) — a **false positive**, not a false negative, and therefore consistent with HBDC's fail-closed/conservative-classification requirement. No change needed. |

Audit method: for each right, granted alone via real `chmod +a` to a fixture file/directory, confirmed the repaired parser returns `False` (not write-capable), and for the two read/security-adjacent rights additionally confirmed via a real ground-truth open attempt that no write access is conferred. All eleven remaining safe-vocabulary rights are read-only or non-standalone inheritance modifiers; none directly or transitively confers content, ACL/security, ownership, mode, or descendant-mutation authority. **Acceptance criterion met**: no known-dangerous or authority-transitive ACL right remains classified known-safe.

## Real-ACL Evidence

### writesecurity / chown parser and ground-truth evidence

- Canonical ACL output confirmed to contain the exact `writesecurity`/`chown` tokens the parser expects (real `chmod +a` grants, `ls -le`/`ls -lde` output inspected directly).
- Repaired parser (`_acl_grants_agent_write_macos`) classifies a matching-principal `allow` entry carrying either right as dangerous (`True`) on both files and directories.
- `_effective_write_access` no longer returns safe for an object carrying either right alone (`write is True`, `reason == "acl_grants_agent_write"`).
- `_ancestor_chain_safe` rejects when either right is the only dangerous authority on a higher ancestor, at both the immediate-grandparent level and a deeper (great-grandparent) level.
- `test_writesecurity_ground_truth_permits_self_granted_write_authority` empirically demonstrates the mechanism `writesecurity`'s definition names (self-service ACL editing) as the object's owner — the only account available on this host — which demonstrates the *mechanism*, not a non-owner differential; the non-owner limitation is separately and explicitly disclosed (`test_self_owner_methodology_limitation_disclosed`), not overclaimed.
- No system principals were created; no host provisioning occurred; the host remains unprovisioned throughout.

## Ancestor / Trusted-Git / Protected-Root Composition

- `writesecurity` and `chown` each independently exercised at a grandparent ancestor: `_ancestor_chain_safe` rejects (`safe is False`), diagnostic cites `ancestor_writable:<grandparent>`.
- Each independently exercised one level deeper (great-grandparent): same rejection.
- A fully safe control chain (no ACL grants anywhere) still reaches the filesystem root (`safe is True`, terminal diagnostic `ancestor_walk_reached_filesystem_root`) — confirms the repair did not introduce a false-positive-unsafe regression on the safe path.
- Trusted-Git path (`_resolve_trusted_executable_with_effective_access("git")`): a `writesecurity`- or `chown`-only grant on a higher ancestor above the trusted executable causes trust resolution to fail (`None`), for both rights independently.
- Protected-Root path (`_check_ancestor_chain`): identical rejection for both rights via the shared `_ancestor_chain_safe` primitive — Git and Protected Root continue to use identical, unforked semantics (`test_git_and_protected_root_use_identical_shared_semantics`).

## Allow/Deny Disposition

Unchanged and re-verified: a `deny`-only entry for `writesecurity`/`chown` is never treated as a grant (`test_dangerous_right_deny_only_not_treated_as_allow`, both rights). The conservative simplification already documented in the module (a matching dangerous `allow` is treated as writable even if a co-existing unrelated `deny` might narrow real NFSv4 effective access) is unchanged and was not the subject of this repair; no primary evidence surfaced during this phase required full NFSv4 ACE-ordering implementation to eliminate a false-negative-safe result. This remains a disclosed limitation in the conservative (false-positive-unsafe-only) direction.

## Principal-Resolution Regression

Re-run for both `writesecurity` and `chown`: current-user principal (detected), unrelated user principal `daemon` (not detected), effective/supplementary group principal `everyone`/gid 12 (detected, no special-casing), unrelated group principal `_postfix` (not detected), unresolvable/malformed principal (fails closed, `None`). All pass, matching the existing principal-resolution primitive `_macos_acl_principal_matches_agent`, which this repair did not modify.

## Existing Dangerous-Right and Regression Coverage

- Directory: `add_file`, `add_subdirectory`, `delete_child`, `delete` — all still detected.
- File: `write`, `append`, `writeextattr` — all still detected.
- POSIX-safe, no-ACL control — still correctly not detected.
- Unknown ACL right token — still fails closed (`None`), confirming the known-safe set was not widened to accommodate future unrecognized rights.
- **J-1** (environment-lock `.pth` fix): `hatp_environment_lock_verifier.py` confirmed byte-unchanged since the pre-repair commit.
- **J-2** (effective-gid folding): `_current_agent_identity` still unions `os.getgroups()` with `os.getegid()` independently; confirmed.
- **J-3** (core file-level ACL write rejection on a trusted executable): re-confirmed via a fresh fixture.
- **B-149O.20J.2-1** (full ancestor-chain early-stop defect): re-confirmed closed — a POSIX-mode-writable (non-ACL) grandparent is still correctly rejected, not stopped at early.
- Symlinked higher ancestor: still never becomes safe.
- Indeterminate-ACL-above-safe-ancestor: still never resolves to safe (`None`, not `True`).

## Production Scope

`git diff <commit-before-this-repair> -- src/` (working tree, pre-commit) and post-commit `git diff <pre-repair-commit> HEAD -- src/` both confirmed limited to exactly:

- `src/pcae/core/hatp_class_b_topology_verifier.py`

Confirmed unchanged: `src/pcae/core/hatp_environment_lock_verifier.py`, `src/pcae/core/hatp_class_b_conformance.py`. No HMIC-bound production source changed. No contract file changed — no primary evidence surfaced during derivation revealed genuine contract ambiguity requiring a contract-text change.

## HMIC Frozen Scope

`hatp_mandatory_certification._FROZEN_AUTHORITY_BEARING_FILES`: still exactly 25 entries, none naming any of the three Class-B modules. `_CONTRACT_IDENTITY_FILES`: still exactly 5. CBV-S1 remains OPEN — HMIC source-scope binding still pending, untouched by this phase.

## Zero-Consumer Confirmation

`git grep` across `src/` for the three Class-B module names and their public entry points returns hits in exactly the three-module island itself (`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py`) and nowhere else — no readiness, certification, activation, Permission Broker, rollback, or runtime-execution consumer exists.

## Read-Only Wall

Source-inspected: no `os.chmod`, `os.chown`, `os.mkdir`, `os.makedirs`, `shutil.rmtree`, `os.remove`, `os.unlink`, `os.rename`, `os.replace`, `os.symlink`, `os.link`, `.write_text`, or `.write_bytes` call appears anywhere in the three-module island. Test fixtures create and clean up isolated `tmp_path`-rooted ACL state only; `git status --porcelain -- src/` confirmed identical before and after calling `verify_class_b_deployment_conformance()`.

## Real-Host Result

`verify_class_b_deployment_conformance()` on this deliberately unprovisioned host returns `NON_COMPLIANT`, unchanged. Host was not provisioned; no additional user/group principal was created.

## Tests Run

New dedicated module: `tests/test_phase_149o_20j_7_class_b_writesecurity_chown_acl_right_reclassification_narrow_repair.py` — 72 tests, all passing, deterministic across three repeated runs. Covers: primary-source semantic derivation, exact vocabulary diff, complete known-safe-vocabulary audit (17 parametrized + 2 summary cases), writesecurity/chown real-fixture parser + ground-truth detection (file and directory), principal-resolution regression (6 cases × 2 rights), ancestor-chain composition (grandparent + deeper level × 2 rights), safe full-chain control, Trusted-Git and Protected-Root composition (× 2 rights) plus equivalence, existing dangerous-right regression (directory + file), J-1/J-2/J-3/B-149O.20J.2-1/symlink/indeterminate-ACL regressions, HMIC 25/5, zero consumers, read-only wall, real-host `NON_COMPLIANT`, repository-state-unchanged.

One pre-existing J.6 test (`test_writesecurity_and_chown_are_currently_classified_known_safe`) asserted the *live* production classification as of J.6; since this phase intentionally changes that classification, the assertion was updated to pin against the historical J.6 commit blob (`git show 4c4fd16d:...`) rather than the live module — preserving the historical record as a permanent, commit-pinned fact rather than leaving it broken by an authorized later change (same precedent as 149O.20J.5 removing 149O.20J.4's own pre-authorized `xfail` markers once its repair made them pass). All 67 J.6 tests pass after this update.

Broader regression: `pytest -k 'class_b or hbdc or 149o_20j' -n auto` — clean baseline (via `git stash push -u`, no J.7 changes): 11 failed / 725 passed / 5 skipped / 1 pre-existing collection error (fido2 module). With J.7 changes restored: 16 failed / 792 passed / 5 skipped / 1 pre-existing collection error — the 5 additional failures are exactly the expected "working tree touches src/pcae" self-checks from historical phases (149O.20D, 149O.20D.1, 149O.20E, 149O.20H, 149O.20C) that trip on any uncommitted change and self-resolve once this phase's changes are committed; zero of the 5 involve new logic regressions. 792 passed = 725 baseline + 67 (of this phase's own 72 new tests that were not among the 5 expected dirty-tree failures — no new test in this phase's own file failed).

`fast_green` (`pytest -m fast_green -n auto`, fido2 module ignored — pre-existing/unrelated): raw run 81 failed / 6761 passed / 5 skipped / 1 pre-existing collection error; clean-deselected citation (exact raw failing node IDs deselected via argv-list subprocess, not shell string interpolation): **0 failed / 6761 passed / 5 skipped / 1 pre-existing collection error**; zero of the 81 raw failures are in this phase's own test file.

## Governance Results

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — historical `tasks/done/` entries missing from `tasks/DONE.md`, predating this phase, not remediated here — outside this phase's allowed-file scope)
- `pcae_push_check`: see Pushed Status below
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: telegram configured/enabled

## Finding Status at Exit

- **B-149O.20J.4-1**: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.
- **CBV-S1**: OPEN — HMIC source-scope binding still pending.
- **CBV-S10**: OPEN — readiness contract/integration gap, unchanged.

## Class-B / HATP / Runtime Status

- **Class-B**: CONTRACT VERIFIED — ACL AUTHORITY-VOCABULARY REPAIR IMPLEMENTED NON-AUTHORITATIVELY — INDEPENDENT VERIFICATION PENDING — NOT PROVISIONED.
- **HATP**: NOT READY.
- **Runtime**: Observed / observe / unavailable.

## Recommended Next Phase

**149O.20J.8 — Class-B writesecurity/chown ACL-Right Reclassification Repair Independent Verification.**

J.8 must independently re-derive and attack the authority vocabulary (not trust this phase's report, tests, or rationale) before B-149O.20J.4-1 can be closed. Only after a clean J.8 may 149O.20K (HMIC Class-B Verifier Source-Scope Contract Evolution) become eligible — and 149O.20K must still perform its own fresh HMIC-REQ-052 transitive authority-dependency closure analysis rather than assuming the HMIC source count changes.
