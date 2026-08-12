# Phase 149O.20J.6 — Class-B macOS ACL-Only Higher-Ancestor Detection Repair Independent Verification

**Status:** COMPLETE (independent verification only; no production repair)
**Scope:** Independently verify 149O.20J.5's repair of B-149O.20J.4-1. Trusts nothing from 149O.20J.5 — not its report, tests, rights vocabulary, ACL description, mode-marker interpretation, or J-3 scope adjudication. Re-derives from primary contracts, fixed historical source, current production source, real macOS ACL probes, and current OS behavior.

## 1. Primary contract re-derivation (independent of 149O.20J.5)

Read directly from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (not phase-doc paraphrases):

- **HBDC-REQ-016**: "No POSIX ACL, extended ACL, default ACL, or inherited ACL entry SHALL grant the agent principal write access to Protected Root or any descendant path, even where base mode bits would otherwise deny it."
- **HBDC-REQ-017**: every ancestor of Protected Root, up to the point the agent has no write access at all, SHALL be non-agent-writable — because a writable parent lets the agent rename/replace the directory entry naming Protected Root even without write on Protected Root's own bytes.
- **HBDC-REQ-020**: deleting/renaming the directory entry naming an authority-bearing file is a compliance failure equivalent to a direct write, satisfied jointly by HBDC-REQ-017.

Derived (before inspecting production code) dangerous-authority classes:

- **Ancestor directory**: create a replacement/child entry, create a subdirectory, delete a child, delete/rename the directory itself — i.e. any capability over the directory's *entry topology*.
- **Trusted file**: modify content, append content, alter authority-sensitive extended attributes.

This matches the classes 149O.20J.5 independently arrived at (`add_file`/`add_subdirectory`/`delete_child`/`delete` for directories; `write`/`append`/`writeattr`/`writeextattr` for files) — convergent, not copied.

## 2. Fixed historical defect: independent reproduction

`0b2fd134` independently confirmed as the true immediate parent of repair commit `6a265e09` via `git rev-parse 6a265e09^` (not merely trusted from J.5's citation).

Extracted the exact pre-repair `_acl_grants_agent_write_macos` via `git show 0b2fd134:src/pcae/core/hatp_class_b_topology_verifier.py` (not retyped). Confirmed the exact defect shape by string match against the extracted blob:

```python
if "+" not in mode_line.split()[0] if mode_line.split() else True:
    return False  # no ACL marker on the mode string -> no ACL present
for line in lines[1:]:
    entry = line.strip()
    if "write" in entry or "allow write" in entry:
        return True
```

Real fixture (isolated at `/private/tmp`, restricted `PATH=/usr/bin:/bin` so `_resolve_trusted_executable("ls")` resolves through only admin-owned directories, avoiding this dev host's user-writable `PATH` entries): a directory at POSIX mode `500` (no owner/group/other write) granted `chmod +a "$(whoami) allow add_file,delete_child"`. Ground truth: creating a file inside the directory succeeded despite mode 500. The extracted historical function returned `False` (misclassified as non-write) for this directory — reproduced independently, matching J.5's claimed defect.

## 3. Mode-marker reliability

Confirmed empirically on this host (macOS 26.6.1 / Darwin 25.6.0, arm64): a freshly created directory already carries a `com.apple.provenance` extended attribute (`xattr -l`), confirmed **non-removable** (`xattr -d com.apple.provenance` is a silent no-op — the attribute persists). This renders the `ls -lde` mode-column marker `@` (extended attributes) rather than `+`, even when a real ACL is simultaneously present. Security-relevant conclusion, stated independent of the `com.apple.provenance` explanation: **the trailing mode-column marker character is not a reliable signal for ACL presence and must not gate ACL inspection.** Source-inspected the current production `_acl_grants_agent_write_macos`: no `"+"` or `'+'` literal appears anywhere in the function — confirmed it does not gate on the marker at all, deriving ACL presence from entry-line content only.

## 4. Real macOS ACL grammar (independent derivation)

Derived from `man chmod`'s ACL MANIPULATION OPTIONS section (read directly on this host, via `col -b`) and fresh `chmod +a` grants — not from J.5's prose:

- Numbered entry line: `<N>: <principal> allow|deny <right1,right2,...>`.
- Principal form observed: `user:<name>` / `group:<name>`.
- Directory rights include `add_file`, `add_subdirectory`, `delete_child`, `delete`, plus non-dangerous `list`/`search`/inheritance flags.
- File (non-directory) rights include `read`, `write`, `append`, `execute`.
- Rights applicable to both: `writeattr`, `writeextattr`, `readsecurity`, `writesecurity`, `chown`.
- **`write`(file) and `add_file`(directory) render the identical underlying ACE contextually** — independently confirmed by granting the literal token `add_file` to a directory and `write` to a file and observing `ls -le` render each in its own canonical spelling; likewise `append`/`add_subdirectory`.

The production `_MACOS_ACL_KNOWN_RIGHTS` set was checked to be a superset of every right `man chmod` documents — confirmed.

## 5/6. Real directory- and file-right attacks

Fresh real `chmod +a` fixtures, capability-specific ground-truth probes (create-file for `add_file`, create-subdirectory for `add_subdirectory`, delete-a-preexisting-child for `delete_child`; a plain `O_WRONLY` open for `write`, an `O_APPEND` open for `append`):

- All four directory rights individually and combined (`add_file,delete_child`) detected correctly by the current parser, each ground-truth-verified first.
- POSIX-safe directory with no ACL correctly not detected.
- File-level `write`/`append`/`writeextattr` each individually detected; irrelevant read-only rights not detected.

**Independent host discovery** (not previously documented in J.5's own report): `open(file, "a")` is an `O_APPEND` open, and macOS's ACL evaluation checks that specifically against the **`append`** right, not `write` — a `write`-only grant with POSIX mode denying owner-write allows a plain `O_WRONLY` open (confirmed via `dd`) but **not** an `O_APPEND` open. This is a real, independently discovered nuance of macOS ACL/kauth evaluation; it does not affect the production classifier's correctness (both `write` and `append` are independently in the write-capable vocabulary and each is individually ground-truth-verified above) but is recorded as new host evidence.

## Central finding — B-149O.20J.4-1 remains OPEN

`man chmod`, read directly on this host:

> `writesecurity` — Write an object's security information (**ownership, mode, ACL**).
> `chown` — Change an object's ownership.

Both rights are classified in `_MACOS_ACL_KNOWN_SAFE_RIGHTS` by the current (149O.20J.5) production implementation. Both are, by their own primary-documentation definition, **transitively write-equivalent authority**:

- A `writesecurity` holder can rewrite the object's own ACL (grant itself `write`/`add_file`/etc.), rewrite its mode bits directly (set an owner/group/other write bit), or rewrite its ownership — any one of which yields full write authority.
- A `chown` holder can make itself the object's owner, at which point ordinary POSIX owner-write mode-bit semantics govern — bypassing HBDC-REQ-013 (admin ownership) entirely for that ancestor.

149O.20J.5's own doc (`docs/PHASE_149O_20J_5_CLASS_B_ACL_ONLY_HIGHER_ANCESTOR_DETECTION_NARROW_REPAIR.md` §6.4) justifies the safe classification as "empirically confirmed to not confer any effective write authority when granted alone." Independently reproduced the exact test conditions that claim rests on: a same-owner fixture. On a single-user development host the tester is always the object's owner, and **an owner can already `chmod`/rewrite their own object's mode with no ACL grant at all** (independently confirmed here: `chmod 700` on an un-ACL'd, mode-500, owner-held directory succeeds unconditionally). This means a same-owner "grant it, then try to escalate" test cannot distinguish "the ACE does nothing" from "the tester already had that authority as owner, independent of the ACE" — it is not a valid test for the specific principal HBDC-REQ-009 actually contemplates holding such a grant (a non-owner **agent** principal against an **admin-owned** ancestor). No second real user account was available on this host to run a genuine cross-principal exploitation test; the finding rests on `man chmod`'s own unambiguous primary-source definition of the two rights, which is decisive on its own and is the same authoritative documentation this entire repair's rights vocabulary is derived from.

Per the governing prompt's explicit criterion (§10): *"A false negative write classification is Blocking... If the latter is possible, the repair is not complete."* This is exactly that case.

**Adjudication: B-149O.20J.4-1 = REPAIRED (marker/substring-search defect, independently verified) — A DISTINCT KNOWN-SAFE-VOCABULARY GAP FOUND (writesecurity/chown) — NOT CLOSED.**

## 7. Contextual rendering

Confirmed `write`/`add_file` and `append`/`add_subdirectory` are the same underlying ACE rendered contextually (§4 above). No alias gap found in the current vocabulary beyond the writesecurity/chown finding above.

## 8. Unknown-right fail-closed

Independently constructed parser inputs with a fabricated right token (`totallyfakeacenevermade`) alone, combined with a known-safe right, and combined with a known-dangerous right (`add_file`). In every case the current `_acl_grants_agent_write_macos` returns `None` (indeterminate/fail-closed), never silently drops the unknown token. Confirmed the `None` propagates through `_effective_write_access` (`reason == "acl_inspection_unavailable"`) and would propagate through `_ancestor_chain_safe` (that function's own `write is None` branch marks the ancestor indeterminate, never safe).

## 9. Principal identity verification

- Current user (`user:<whoami>`): detected.
- Unrelated user (`daemon`): not detected.
- Effective group (`everyone`, real gid 12, not special-cased — independently confirmed to be a real supplementary group of this process via `os.getgroups()`): detected.
- Unrelated group (`_postfix`, gid 27, independently confirmed not a membership of this process): not detected.
- Unresolvable principal name on a write-capable allow entry: fails closed (`None`).
- Malformed principal shape (no `user:`/`group:` prefix): fails closed (`None`).

## 10. Allow/deny safety direction

- A deny-only entry is never treated as a grant.
- An allow for a write-capable right remains classified as writable even in the presence of an unrelated deny entry on the same object (ground-truth-confirmed the allow is genuinely still exploitable) — confirms the disclosed simplification is conservative (over-cautious), never a masked grant, in every case tested. No false-negative-masking-by-deny scenario found (independent of the writesecurity/chown finding, which is a vocabulary gap, not an allow/deny ordering defect).

**Real host discovery during this section's testing**: an explicit ACL `deny` entry on a right (e.g. `delete_child`) blocks even the file's *owner* from exercising that specific action, overriding ordinary owner mode-bit authority for that one right — recorded as fixture-cleanup evidence (required stripping the ACL before test-fixture teardown could proceed), not a defect in the production classifier.

## 11. Known-safe vocabulary attack

Independently inspected every right in `_MACOS_ACL_KNOWN_SAFE_RIGHTS`: `read`, `execute`, `readattr`, `readextattr`, `readsecurity`, `writesecurity`, `chown`, `list`, `search`, and the four inheritance flags. **`writesecurity` and `chown` are the Blocking finding above.** All other rights checked against their `man chmod` definitions do not confer content, descendant-creation, descendant-deletion, replacement, or rename-relevant authority (`readsecurity` is read-only per its own definition; the inheritance flags only affect propagation to future children, not present authority; `list`/`search`/`read*`/`execute` are read/traverse-only).

## 12/13. Malformed ACL entries / inspection failure

Constructed: non-numbered line, missing colon, missing principal, missing allow/deny token, empty rights, unexpected decision token, duplicated separator (empty right token), extra whitespace, truncated line. None produce a positive write grant. ACL tool unavailable (`PATH=""`) and non-zero subprocess exit both fail closed to `None`. A path that disappears between existence check and stat also fails closed (`path_missing`, `None`), never falls back to a mode-bit-only "safe" verdict.

## 14. Complete ancestor-chain composition

This dev host's own home-directory tree is agent-writable at every level up to `/Users/atilamadai` (mode `750`, owned by this user) — an unavoidable confound for any real-filesystem-root walk from a `tmp_path`-rooted fixture (independently rediscovered; 149O.20J.5's suite discloses and handles the identical issue). Where isolating a specific ancestor level is the point of the test, `_effective_write_access` is monkeypatched to report a fixed proven-safe result for paths *outside* the constructed fixture subtree; every path inside the fixture subtree goes through the real, unmodified production function against real `chmod +a` state.

- One-level (ACL-only grandparent, safe parent): real `_ancestor_chain_safe` rejects, diagnostic specifically attributes the rejection to the ACL-granted grandparent path.
- Two-level (ACL-only great-grandparent, safe parent and grandparent): rejects, diagnostic attributes rejection to the correct level.
- Fully safe chain: reaches `"ancestor_walk_reached_filesystem_root"`.

## 15/16. Trusted-Git and Protected-Root composition

Fresh fixtures: a fake `git` executable under a constructed `PATH`, with an ACL-only-writable ancestor directory above it — `_resolve_trusted_executable_with_effective_access("git")` returns `None` (rejects trust). A fresh real file-level `write` ACL grant directly on the executable's own bytes is independently rejected (re-confirms J-3's core delegation/wiring). `_check_ancestor_chain` (the Protected-Root-equivalent check) rejects the identical ACL-only-grandparent scenario via the same shared `_ancestor_chain_safe` primitive — confirmed Trusted-Git and Protected-Root use the identical ancestor boundary, ACL parser, and identity resolution (same underlying function call, not two independently-forked implementations).

## 17. J-3 historical scope adjudication

Independently read the primary phase documents (not J.5's summary):

- `docs/PHASE_149O_20J_1_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR.md`: the original `B-CBV-J-3` finding text explicitly states an ACL-only agent write grant "to the git executable, its ancestors, or a PATH-preceding directory would not be detected" — confirms ancestor-ACL blindness was named in the original finding.
- `docs/PHASE_149O_20J_2_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR_INDEPENDENT_VERIFICATION.md`: contains the literal phrases "simulated an ACL-only write grant" and the ACL sub-check "forced to report" no ACL — confirms J.2's verification of the ancestor-ACL claim used simulation, never a real `chmod +a` grant.

Independent adjudication (matches J.5's OUTCOME B, arrived at independently, not copied): J-3's core delegation/wiring defect (ACL consulted at all, for both the executable's own bytes and its ancestor chain) remains independently closed — re-confirmed end-to-end in §15/16 above with fresh real ACL grants. The original closure's specific ancestor-real-ACL-coverage sub-claim was evidentially unsupported (simulation only) until 149O.20J.5's real-host repair — narrowed, not rewritten; no historical document edited.

## 18. J.5/J.4 test-change review

149O.20J.5 removed two `strict=True` xfail markers from 149O.20J.4's own suite. Their reason text explicitly conditioned removal on "a follow-up phase repairs the ACL right-name matching and this test genuinely passes" — 149O.20J.5 is that phase, and its own new real-ACL tests (independently re-verified to pass in this phase's regression run) confirm the condition was satisfied. No other assertion in that file was touched (confirmed by inspecting the diff scope — the only other changes to that file across this window are lifecycle metadata, not test assertions).

## 19. Structural review of current repair

Source-inspected the current `_acl_grants_agent_write_macos`/`_macos_acl_principal_matches_agent`: no mode-column marker gate; ACL entry lines parsed directly via regex; principal identity resolved explicitly via `pwd.getpwnam`/`grp.getgrnam`; dangerous rights classified against an explicit set; unknown rights fail closed; malformed entries fail closed; deny entries never create a grant; unresolved dangerous principals fail closed; identity supplied from `_current_agent_identity()` (no caller-supplied override parameter exists in the function signature). Darwin dispatch in `_acl_grants_agent_write` passes `agent_uid`/`agent_gids` through; the Linux branch (`_acl_grants_agent_write_linux`) is untouched by this diff (confirmed via §20's diff reconstruction).

## 20. Production diff reconstruction

`git diff --name-only 0b2fd134 6a265e09 -- src/` independently confirmed: exactly one file, `src/pcae/core/hatp_class_b_topology_verifier.py` (108 insertions, 7 deletions). `hatp_environment_lock_verifier.py` and `hatp_class_b_conformance.py` unchanged in that diff.

## 21–24. Regressions

- B-149O.20J.2-1 (early-stop): a POSIX-mode-writable grandparent behind a safe parent is still rejected by the full-chain walk, attributed correctly in diagnostics — remains independently closed.
- J-1: `hatp_environment_lock_verifier.py` byte-unchanged since `0b2fd134` (`git diff --name-only` empty for that path over that range).
- J-2: `_current_agent_identity()` still folds `os.getegid()` into the returned group set.
- Symlink: a symlinked higher ancestor is never classified safe (`ancestor_symlink` diagnostic, `safe=False`).
- Indeterminate: an ACL-inspection-indeterminate ancestor above an otherwise-safe chain never resolves to `safe=True` (`safe is None`).

## 25/26/27/28. HMIC non-binding, zero consumers, read-only wall, real host

- `hatp_mandatory_certification._FROZEN_AUTHORITY_BEARING_FILES`: independently loaded and counted — exactly 25, none of the three Class-B modules present. `_CONTRACT_IDENTITY_FILES`: exactly 5.
- `git grep` across `src/` for references to any of the three modules or their public entry points: zero hits outside the three-module island itself.
- Source-inspected all three modules for mutating calls (`os.chmod`/`chown`/`mkdir`/`makedirs`/`rmtree`/`remove`/`unlink`/`rename`/`replace`/`symlink`/`link`/`write_text`/`write_bytes`): zero found.
- `verify_class_b_deployment_conformance()` on this real, deliberately unprovisioned host: `NON_COMPLIANT`.
- `git status --porcelain -- src/` before and after running the full verifier: identical (no repository mutation from inspection).

## 29. Finding adjudication

Per the governing prompt's own rule ("If any effective ACL grant can still be classified safe, keep the finding OPEN"): **B-149O.20J.4-1 is NOT closed by this phase.** The marker/substring-search defect that was this repair's original target is independently confirmed fixed; a distinct, real, primary-evidence-grounded gap (writesecurity/chown misclassification) was found during this phase's independent attack and keeps the finding open. CBV-S1, CBV-S10, HMIC binding, readiness, provisioning, deployment activation, and HATP readiness are all unaffected and remain exactly as they were (all still OPEN/NOT READY/unprovisioned) — this phase changed no production source and made no readiness claim.

## 30. Terminal status

- **B-149O.20J.2-1**: INDEPENDENTLY CONFIRMED CLOSED AT NON-AUTHORITATIVE VERIFIER IMPLEMENTATION BOUNDARY (unchanged, reconfirmed).
- **B-149O.20J.4-1**: REPAIRED (marker/grammar defect) — INDEPENDENTLY VERIFIED FOR THAT DEFECT — A DISTINCT KNOWN-SAFE-VOCABULARY GAP FOUND (writesecurity/chown) — **NOT CLOSED**.
- **J-1**: remains independently closed.
- **J-2**: remains independently closed.
- **J-3 core**: remains independently closed; historical ancestor-ACL closure language remains narrowed per the independently-reconfirmed adjudication in §17.
- **CBV-S1**: OPEN — HMIC SOURCE-SCOPE BINDING STILL PENDING.
- **CBV-S10**: OPEN — READINESS CONTRACT/INTEGRATION GAP.
- **Class-B**: CONTRACT VERIFIED — MARKER/GRAMMAR DEFECT INDEPENDENTLY VERIFIED — KNOWN-SAFE-VOCABULARY GAP OPEN — NOT PROVISIONED.
- **HATP**: NOT READY.
- **Runtime**: Observed / observe / unavailable.

## 31. Recommended next phase

**Phase 149O.20J.7 — Class-B `writesecurity`/`chown` ACL-Right Reclassification Repair.** Narrow production repair: move `writesecurity` and `chown` from `_MACOS_ACL_KNOWN_SAFE_RIGHTS` to `_MACOS_ACL_WRITE_CAPABLE_RIGHTS` (or otherwise classify them as write-equivalent) in `hatp_class_b_topology_verifier.py`, with real-ACL evidence and, if at all obtainable, a genuine cross-principal (non-owner) test rather than a same-owner test. Only after that repair is independently re-verified may B-149O.20J.4-1 be considered for closure, and only then should **149O.20J.6-equivalent re-verification** (or a fresh 149O.20J.8) be attempted before 149O.20K (HMIC Class-B Verifier Source-Scope Contract Evolution) begins. 149O.20K must not begin until B-149O.20J.4-1 is actually closed, and must still perform its own fresh HMIC-REQ-052 transitive authority-dependency closure analysis rather than assuming the HMIC source count changes.

## Tests run

- `tests/test_phase_149o_20j_6_class_b_acl_only_higher_ancestor_detection_repair_independent_verification.py` — 67 new, fresh (none copied from 149O.20J.5's suite), real-ACL-backed. Run twice for determinism: 67/67 passed both times, zero warnings, zero repository mutation.
- `pytest -k 'class_b or hbdc or 149o_20j' -n auto`: 11 failed / 658 passed / 5 skipped / 1 pre-existing collection error — byte-identical to 149O.20J.5's own citation; zero of the 11 in this phase's own test file.
- `pytest -m fast_green -n auto` (fido2 module ignored, pre-existing/unrelated): stable at the pre-existing 71–72 flaky band, independently reconfirmed non-deterministic **both with and without this phase's changes present** (identical failing-test sets across repeated runs regardless of stash state) — a pre-existing xdist-collection-order nondeterminism, not attributable to this phase. Zero of these failures are in this phase's own test file.

## Governance

- `pcae session bootstrap --agent-id claude-local`, `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory` (pre-existing warnings, unrelated), `pcae push check`, `pcae runtime inspect` (Observed/observe/unavailable), `pcae notify status` (Telegram configured), `pcae phase-report show --latest`, `pcae phase-report reconcile --phase-id 149O.20J.5` (read-only, no mutation) all run at phase entry.
- Governed task lifecycle: closed the stale post-149O.20J.5 idle task, opened `20260812-2205-phase-149o-20j-6-...` with the new test file and this document allowed, the three Class-B modules and HMIC-adjacent modules explicitly forbidden (verification-only scope).
- No raw `git commit`/`git push`, no `--no-verify`, no force push, no hook bypass, no lifecycle bypass.
