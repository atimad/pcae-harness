# Phase 149O.20J.8 — Class-B writesecurity/chown ACL-Right Reclassification Repair Independent Verification

## Purpose

Independently verify Phase 149O.20J.7's repair of the remaining known-safe-vocabulary
gap in **B-149O.20J.4-1** (macOS ACL-only higher-ancestor detection gap): J.7 moved
`writesecurity` and `chown` from `_MACOS_ACL_KNOWN_SAFE_RIGHTS` into
`_MACOS_ACL_WRITE_CAPABLE_RIGHTS` in `hatp_class_b_topology_verifier.py`. This phase
does not trust J.7's report, tests, vocabulary audit, writesecurity/chown reasoning,
Fast Green attribution, or historical-test-pinning justification — every material
conclusion below is re-derived from primary sources or exercised via fresh real ACL
fixtures. Verification-only: no production source was modified.

## 1. Production diff reconstruction

True immediate parent of repair commit `26545b90` is `71613327` (`git rev-parse
26545b90^`), independently confirmed. `git diff 71613327 26545b90 -- src/` touches
exactly one file: `hatp_class_b_topology_verifier.py` (52 insertions / 6 deletions).
`hatp_environment_lock_verifier.py` and `hatp_class_b_conformance.py` are byte-identical
before/after (`git show <rev>:<path>` diffed directly). An AST-level function-by-function
diff (`ast.dump` per `FunctionDef`) confirms every function in the module is byte-identical
except the two frozenset literals themselves (now spanning multiple lines) and their
surrounding comments — no parser logic, principal-matching logic, ancestor-walker,
Trusted-Git resolver, Protected-Root check, or Linux ACL path changed.

## 2. HBDC authority criterion (independently re-derived)

Read directly from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`:
HBDC-REQ-016 (no ACL entry may grant agent write access); HBDC-REQ-017 (every ancestor
up to the point of no write access is non-agent-writable — an agent that can rename/replace
a directory entry can redirect a "safe" child even without write access to the child's own
bytes); HBDC-REQ-020 (directory-entry replacement/rename is a compliance failure equivalent
to direct write, satisfied jointly with HBDC-REQ-017, "not separately re-derivable from
file-level mode bits alone"); CBD-1 (agent cannot write protected authority state);
CBD-3 (agent cannot redirect Protected Root via symlink/ACL/group/parent-path channels).

**Derived criterion:** an ACL right is dangerous under HBDC if a grant of it can, directly
or transitively, enable content mutation, ACL/security mutation, mode mutation, ownership
mutation, or directory-entry replacement (create/delete/rename) — not merely "performs an
immediate byte-level content write."

## 3. Independent macOS ACL right inventory

`man chmod`'s ACL MANIPULATION OPTIONS section, read directly on this host, yields:

- All-object rights (8): `delete`, `readattr`, `writeattr`, `readextattr`, `writeextattr`,
  `readsecurity`, `writesecurity`, `chown`
- Directory-only rights (5): `list`, `search`, `add_file`, `add_subdirectory`, `delete_child`
- File-only rights (4): `read`, `write`, `append`, `execute`
- Inheritance-propagation modifiers (4): `file_inherit`, `directory_inherit`, `limit_inherit`,
  `only_inherit`

Total: **21**, independently re-typed before comparing to production. Production's combined
`_MACOS_ACL_KNOWN_RIGHTS` (`_MACOS_ACL_WRITE_CAPABLE_RIGHTS | _MACOS_ACL_KNOWN_SAFE_RIGHTS`)
is exactly this same 21-member set (`test_production_combined_vocabulary_exactly_equals_
independent_inventory`) — no gap, no unrecognized-but-real right, no extra unsupported
right silently accepted as safe.

The man page's inheritance-example block renders one entry as the hyphenated
`write-security` — ground-truth-verified via real `chmod +a "... allow writesecurity"` +
`ls -le` on this host to **not** match real canonical output, which always renders the
unhyphenated `writesecurity` token production's vocabulary actually matches. Confirms J.7's
disclosed caution about not assuming man-page example spelling was warranted and correctly
applied.

## 4. writesecurity adjudication

Primary definition (`man chmod`, re-read on this host): "Write an object's security
information (ownership, mode, ACL)." A holder can rewrite the object's own ACL — including
granting itself `add_file`/`write`/`delete_child`/etc. — and flip mode bits directly, with
no pre-existing write grant. Under the derived criterion (§2), a right that can rewrite the
ACL granting write access is itself write-equivalent, by the same transitive-authority logic
HBDC-REQ-017/020 already apply to parent-directory replacement. **Independent verdict:
DANGEROUS.** Real fixture ground truth (`test_real_fixture_ground_truth_token_and_parser_
detection`, file and directory, mode bits denying so the ACL branch is genuinely exercised):
parser classifies the grant `True` in every case.

## 5. chown adjudication

Primary definition: "Change an object's ownership." Separating the four requested
dimensions: (1) the semantic right itself confers no bytes until exercised; (2) OS
restrictions on which transitions a concrete process may perform are irrelevant to the ACL
right's own authority; (3) becoming owner is the direct consequence of exercising the right;
(4) an owner has ordinary `S_IWUSR` mode-bit write authority with **no ACL grant required at
all**. This channel — ACL-granted ownership transfer leading to unconditional mode-bit write
authority — is not provable harmless across all HBDC Class-B deployments, and this single-
user development host's same-owner state must not substitute for that broader claim (the
same-owner differential critique applies to *test method*, not to this semantic conclusion).
**Independent verdict: DANGEROUS**, fail-closed-consistent even without asserting a specific
transition succeeds on this host.

## 6–9. Real ACL canonicalization, ancestor-chain, Trusted-Git, Protected-Root composition

All exercised with fresh fixtures (not copied from J.7), `PATH` restricted to
`/usr/bin:/bin` (this dev host's ordinary PATH carries agent-writable entries ahead of
`/bin`, independently confirmed to make `_resolve_trusted_executable("ls")` return `None`
— i.e. every ACL check indeterminate — unless restricted; same technique J.6/J.7 required,
independently re-verified necessary here):

- File and directory grants of `writesecurity`/`chown`, mode bits denying, ACL branch
  genuinely reached: parser returns `True` in all four combinations.
- Grandparent-level and great-grandparent (3 levels deep) dangerous ACL grants: full-chain
  walk (`_ancestor_chain_safe`) rejects (`False`) in all cases, with the correct offending
  ancestor named in diagnostics.
- Fully safe control chain: rather than a constructed fixture (self-owned by definition,
  cannot demonstrate reaching the true boundary), `_ancestor_chain_safe(Path("/bin/ls"),
  ...)` was exercised directly against this real, pre-existing, root-owned system file —
  returns `True`, diagnostics end in `ancestor_walk_reached_filesystem_root`.
- Trusted-Git (`_resolve_trusted_executable_with_effective_access`): dangerous-ACL ancestor
  for both rights rejects (`None`); a real file-level `write` ACL directly on the candidate
  Git executable itself (J-3 core regression) also rejects.
- Protected-Root (`_check_ancestor_chain`): dangerous-ACL ancestor for both rights rejects
  (`satisfied=False`, `agent_writable_ancestor_found`).
- Confirmed both composition paths share the identical `_ancestor_chain_safe` primitive by
  source inspection (`inspect.getsource`).

## 10–11. Known-safe vocabulary audit + inheritance-modifier masking check

Independently classified all 11 remaining known-safe rights **before** consulting the
parser (parser used only as a post-hoc confirmation, never as the classification oracle):
`read`, `execute`, `readattr`, `readextattr`, `readsecurity` — read-only, cannot mutate
content/ACL/mode/ownership; `list`, `search` — directory enumeration/lookup, read-only;
`file_inherit`, `directory_inherit`, `limit_inherit`, `only_inherit` — man page: propagation
modifiers "which may only be applied to directories" and (`only_inherit`) "not considered
when processing the ACL" for the entry's own object access — grant no capability alone.
Set-exhaustiveness independently confirmed equal to live `_MACOS_ACL_KNOWN_SAFE_RIGHTS`.
Each right's real grant, fresh fixture, confirmed parser-safe (`False`) — post-hoc only.

**Combination/masking check (critical J.8 requirement):** real `chmod +a` grants of
`add_file,file_inherit` / `writesecurity,directory_inherit` / `chown,limit_inherit` /
`delete,only_inherit` on fresh directories — parser correctly returns `True` in every case
(dangerous sibling right is never masked by a co-occurring inherit modifier), because the
parser iterates every comma-separated right in the ACE and treats presence of *any*
write-capable token as sufficient. Pure-modifier or pure-safe combinations
(`only_inherit` alone; all four modifiers together; `list,search`; `read,execute`;
`readsecurity,readattr`) correctly remain `False`. **No masking defect found.**

## 12. readsecurity

Man page: "Read an object's extended security information (ACL)" — read-only, cannot
itself modify ACL/mode/ownership. Ground-truth grant confirmed rendering and parser-safe
classification, consulted only after the semantic conclusion above.

## 13. Contextual aliases

Ground-truth confirmed (fresh grants, not accepted from prior phases): granting `execute`
on a directory canonicalizes to `search` in `ls -lde`; granting `search` on a file
canonicalizes to `execute` in `ls -le` — the same underlying bit, contextually rendered,
analogous to the pre-existing `write`/`add_file` aliasing. Unlike the original defect, both
alias spellings (`execute` and `search`; `read` and `list`) are already present in the safe
set — **no alias gap exists.**

## 14. Unknown-right fail-closed regression

Real `chmod` rejects genuinely unknown tokens at the OS level, so a future/unrecognized
right was simulated via a crafted `ls -le`-shaped subprocess stub (the same technique
required to unit-test a fail-closed branch for a token that cannot exist in today's real
ACL vocabulary): unknown alone, unknown+safe, unknown+dangerous, and unknown+inherit-modifier
all independently confirmed to return `None` (indeterminate) — critically, unknown+dangerous
never resolves to `False` (masked-safe).

## 15. Principal resolution regression

Fresh: current user matches (`True`); unrelated user `daemon` (`False`); unresolvable
user/group (`None`, fail-closed); malformed principal shape (`None`); an actual effective
group of this process (`True`); an unrelated group `_postfix` (`False`).

## 16. Allow/deny safety-direction

Deny-only: `False`. Allow+deny same principal, same dangerous right: **`True`** — a deny
entry never suppresses a matching allow (conservative false-positive-unsafe is acceptable;
false-negative-safe never occurs, independently confirmed). Allow-for-unrelated-principal +
deny-for-agent: `False` (no match, correctly ignores the irrelevant deny).

## 17. Dangerous-rights regression

All established directory rights (`add_file`, `add_subdirectory`, `delete_child`, `delete`,
`writesecurity`, `chown`) and file rights (`write`, `append`, `writeextattr`,
`writesecurity`, `chown`) independently re-granted fresh and detected `True`.

## 18–21. B-149O.20J.2-1 / J-1 / J-2 / J-3 regression

B-149O.20J.2-1 (early-stop bypass): writable grandparent behind a safe parent still
rejects the full chain — no early stop reappears. J-1: `.pth` tab-delimited
`import\t...` lines still classified executable (mirrors CPython's `site.addpackage`).
J-2: `os.getgroups()` mocked empty — `_current_agent_identity()` still independently
includes the real `os.getegid()`. J-3 core: real file-level `write` ACL on the Git
executable itself rejects Trusted-Git resolution; a real ACL-only higher ancestor
(`write` grant, three levels up) rejects through the complete-chain parser. Historical
scope preserved as-is per prior phases' narrowing — not restored to any earlier
overbroad claim.

## 22. Symlink / error / indeterminate regression

Symlinked ancestor component: `_ancestor_chain_safe` rejects (`False`,
`ancestor_symlink:...`). Malformed ACL entry line and ACL-tool nonzero-exit: both `None`.
Indeterminate-ACL-tooling-only ancestor above a locally-mode-safe subject: `None`, never
`True` — required using `tmp_path.resolve()` (not the raw `tempfile.mkdtemp()` path) to
avoid this host's `/tmp → /var/... ` symlink hop being (correctly) detected as an
unrelated real symlink ancestor before reaching the intended indeterminate condition;
this is a test-construction detail, not a production defect. The `_stub_outside`
test-isolation helper itself was independently verified to only affect paths outside its
declared boundary.

## 23. J.6 historical-test-pin adjudication

`git diff 71613327 26545b90 -- tests/test_phase_149o_20j_6_...py` shows exactly one test
modified: `test_writesecurity_and_chown_are_currently_classified_known_safe` →
`test_writesecurity_and_chown_were_classified_known_safe_at_j6`, now fetching the real
historical blob via `git show 4c4fd16d:src/pcae/core/hatp_class_b_topology_verifier.py`
and asserting against that text rather than the live module. Independently confirmed:
(1) `4c4fd16d` is genuinely J.6's own phase-implementing commit and a strict ancestor of
J.7's parent (`git merge-base --is-ancestor`); (2) the pinned assertion is factually true
against the freshly re-fetched historical blob (both rights genuinely were in the safe set,
genuinely not in the write-capable set, at that commit); (3) no other J.6 assertion was
touched — the diff contains exactly this one test; (4) all 67 J.6 tests pass against current
production after the update. **Classification: legitimate historical snapshot pinning** —
not evidence laundering, not mere benign supersession (it is a git-verified byte-identical
historical pin, strictly stronger than a paraphrase). J.8 does not reopen this on that basis.

## 24–25. Fixed-baseline Fast Green / broad-sweep comparison

Fixed pre-J.7 baseline established via **isolated `git worktree add` at `71613327`** (J.7's
true parent, per §1) — not the current failing-node set used as its own oracle, and not
`git stash` (avoids touching the working tree at all).

**Broad sweep** (`pytest -k 'class_b or hbdc or 149o_20j' -n auto`): baseline worktree
11 failed / 725 passed / 5 skipped / 1 pre-existing collection error — exactly matches
J.7's own reported clean-baseline count, independently reproduced via a different mechanism.
Current committed HEAD (including this phase's new test file): re-run twice, giving 11
failed (exact same 11 node IDs as baseline) on one run and 12 failed with one extra
(`test_real_host_invocation_does_not_mutate_repo_or_cwd_state`) on another; that test passes
cleanly in isolation, confirming order/parallelism-dependent flakiness under `-n auto`
unrelated to any committed change (repo is clean; this is not a dirty-tree artifact). **Exact
node-ID delta attributable to J.7/J.8: zero.**

**Fast Green** (`pytest -m fast_green -n auto`, `fido2` module ignored — pre-existing/
unrelated): baseline worktree 72 failed / 6770 passed / 5 skipped / 1 collection error,
exact node IDs captured. Current HEAD: 72 raw failed on the final captured run; exact-set
comparison against the baseline shows precisely one node in, one node out — both inside
`tests/test_shell_gate.py::TestAuditPersistence`, confirmed to pass cleanly when that test
class is run in isolation (order/parallelism flake, wholly unrelated to Class-B/ACL logic
and to any file this phase or J.7 touched). **Zero of J.8's 106 new tests appear in any raw
failure across three independent runs.** Clean-deselected citation (exact raw failing node
IDs from the final run, deselected via argv-list subprocess, not shell interpolation):
**0 failed, 6770 passed, 5 skipped, 1 pre-existing collection error.**

## 26. HMIC non-binding

Fresh load: `_FROZEN_AUTHORITY_BEARING_FILES` — exactly 25, none of the three Class-B
modules present. `_CONTRACT_IDENTITY_FILES` — exactly 5. HMIC not modified by this phase.
**CBV-S1 remains OPEN — HMIC SOURCE-SCOPE BINDING STILL PENDING**, independent of this
phase's clean result.

## 27. Zero production consumers

`src/` searched (excluding the three-module island itself) for any reference to the three
module names — zero hits.

## 28. Read-only wall

AST-scanned all three modules for any of `mkdir/makedirs/chmod/chown/unlink/rmdir/rename/
replace/symlink/link/write_text/write_bytes` attribute access — zero found in any of the
three modules.

## 29. Real-host result

`verify_class_b_deployment_conformance()` on this real, deliberately unprovisioned host:
**NON_COMPLIANT**. `git status --porcelain -- src/` identical (empty) immediately before
and after the call.

## 30. B-149O.20J.4-1 adjudication

All required conditions independently established: marker-gate/ACL-grammar repair
(inherited from J.5/J.6, re-confirmed passing); directory- and file-right vocabulary
complete (§3); writesecurity dangerous classification correct (§4); chown dangerous
classification correct (§5); remaining known-safe vocabulary semantically safe (§10);
inheritance modifiers cannot mask dangerous authority (§11); contextual aliases have no
gap (§13); principal handling sound (§15); allow/deny simplification cannot produce a
false-negative-safe (§16); full-chain/Trusted-Git/Protected-Root composition sound
(§6–9); no relevant regression (§17–22); J.6 historical pin legitimate (§23); zero
attributable Fast Green/broad-sweep delta (§24–25).

**B-149O.20J.4-1: INDEPENDENTLY CONFIRMED CLOSED AT NON-AUTHORITATIVE VERIFIER
IMPLEMENTATION BOUNDARY.**

## 31. Terminal statuses

- **B-149O.20J.2-1:** INDEPENDENTLY CONFIRMED CLOSED AT NON-AUTHORITATIVE VERIFIER
  IMPLEMENTATION BOUNDARY (re-confirmed, not reopened).
- **B-149O.20J.4-1:** INDEPENDENTLY CONFIRMED CLOSED AT NON-AUTHORITATIVE VERIFIER
  IMPLEMENTATION BOUNDARY.
- **J-1:** remains independently closed.
- **J-2:** remains independently closed.
- **J-3 core:** remains independently closed, historical ancestor-real-ACL scope
  qualification preserved as previously narrowed.
- **CBV-S1:** OPEN — HMIC SOURCE-SCOPE BINDING STILL PENDING.
- **CBV-S10:** OPEN — READINESS CONTRACT/INTEGRATION GAP.
- **Class-B:** CONTRACT VERIFIED — CLASS-B VERIFIER REPAIR LINE INDEPENDENTLY VERIFIED —
  NOT PROVISIONED.
- **HATP:** NOT READY.
- **Runtime:** Observed / observe / unavailable.

## Tests actually run

- New: `tests/test_phase_149o_20j_8_class_b_writesecurity_chown_acl_right_reclassification_repair_independent_verification.py`
  — 106 tests, 0 failed, run three times for determinism (identical results each time),
  zero repository mutation (`git status --short -- src/` empty before/after every run).
- Regressed fresh: J.3, J.4, J.5, J.6 test modules; broad Class-B/HBDC/J sweep; Fast Green
  (full suite, fido2 module ignored).
- Fixed pre-J.7 baseline: isolated `git worktree add` at commit `71613327`, same commands,
  same environment (`PYTHONPATH` pointed at the worktree's own `src/`).

## Governance

- Governed task opened/closed per PCAE lifecycle; production files
  (`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
  `hatp_class_b_conformance.py`, HBDC-001/HMIC-001 contract files) explicitly forbidden
  in the task contract and confirmed untouched.
- No production source modification. No HMIC/HBDC/readiness/Permission Broker/POL-005/
  COMP-002/provisioning/certification/activation/runtime-capability change.
- `pcae commit implementation`, `pcae phase complete`, governed push — no raw `git commit`,
  no raw `git push`, no `--no-verify`, no force push, no hook bypass.

## Recommended next phase

**149O.20K — HMIC Class-B Verifier Source-Scope Contract Evolution.** Per this phase's
explicit charter, 149O.20K is NOT begun here and must not assume the HMIC source count
moves from 25 to any specific new number — it must freshly derive the complete
HMIC-REQ-052 transitive authority-dependency closure via its own AST/import/dependency
analysis of the Class-B verifier derivation before any HMIC amendment is authorized.
