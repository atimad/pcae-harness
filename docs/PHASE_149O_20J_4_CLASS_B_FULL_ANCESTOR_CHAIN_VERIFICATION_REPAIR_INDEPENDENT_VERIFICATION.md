# Phase 149O.20J.4 — Class-B Full Ancestor-Chain Verification Repair Independent Verification

## 1. Governing purpose

Independently verify 149O.20J.3's repair of **B-149O.20J.2-1** (the shared
`_ancestor_chain_safe` early-stop bypass) from primary contracts, fixed
Git source, and current production source — not from 149O.20J.3's report,
its own new test suite, or its stated filesystem-root boundary claim.

This phase is verification-only. It does not evolve HMIC source scope, do
readiness integration, provisioning, certification, or activation.

## 2. Methodology

1. Read-only governance/repository inspection (`pcae health`/`check`/
   `status coherence`/`doctor task-memory`/`push check`/`runtime inspect`/
   `notify status`, `phase-report show --latest`, `phase-report reconcile
   --phase-id 149O.20J.3`) before any independent analysis.
2. Reconstructed the pre-repair `_ancestor_chain_safe` from `git show
   72eaa241^:src/pcae/core/hatp_class_b_topology_verifier.py` (verbatim,
   not retyped) and executed it directly against a real filesystem
   fixture to reproduce the historical defect.
3. Independently re-derived the ancestor trust boundary from HBDC-001
   (HBDC-REQ-017/020, CBD-3/CBD-7) and the 149O.20A/149O.20H architecture
   documents, before reading 149O.20J.3's own boundary claim in detail.
4. Inspected the current repaired `_ancestor_chain_safe` structurally and
   by control flow (not AST-absence-of-`Return` alone).
5. Wrote a fresh, independently-derived test module (`tests/
   test_phase_149o_20j_4_class_b_full_ancestor_chain_verification_repair_
   independent_verification.py`, 25 tests, not copied/renamed from the
   J.3 suite) covering every attack class required by this phase's
   governing prompt, executed against real chmod/ACL/symlink filesystem
   state wherever practical, with all stubbing explicitly documented
   in-line.
6. Only after independent fixtures were written and run did this phase
   read the J.3 test suite, to compare methodology (§13).
7. Ran `pytest -m fast_green -n auto` (clean-deselected citation) and a
   narrower Class-B/HBDC/149O.20J broad-sweep selector, compared against
   the known pre-existing failure list.

## 3. Historical defect reproduction (§1 of the governing prompt)

Extracted the exact pre-repair `_ancestor_chain_safe` from commit
`72eaa241^` (= `0f2bb93c`, the 149O.20J.1 commit that last touched this
file before the J.3 repair) via `git show`, executed it as an isolated
module against a real three-level fixture (`grandparent` agent-writable,
`parent` mode `0o555` proven locally-safe, `subject` mode `0o555`), with
`PATH` restricted to `/usr/bin:/bin` so the module's own trusted-tool
resolution for ACL inspection resolves deterministically rather than
going indeterminate because of user-writable Homebrew directories ahead
of `/bin` in this host's ambient `PATH` (a test-environment artifact, not
a change to the function under test).

**Result:** the historical function returns `(True, ("ancestor_boundary:
<parent>",))` — it stops at the first proven-safe ancestor (`parent`) and
never inspects the writable `grandparent`. Confirmed by the same fixture
against current production source returning `(False, (...
"ancestor_writable:<grandparent>:agent_is_owner_with_write_bit"))`.
Reproduced in `test_historical_defect_reproduced_from_fixed_source`.

## 4. Independently derived ancestor trust boundary (§2)

HBDC-REQ-017: *"Every ancestor directory of Protected Root, up to the
point the agent principal has no write access at all, SHALL be
non-agent-writable."* Read in isolation this sentence is ambiguous
between "stop at the first non-writable ancestor" and "the entire chain
must be non-writable." HBDC-REQ-020 resolves the ambiguity: directory-
entry replacement (rename/delete without touching the target's own
bytes) is treated as write-equivalent, and this authority lives in the
**containing** directory, not the entry itself. This makes the threat
recursively compositional: a writable ancestor at *any* depth can replace
the directory entry naming everything beneath it, regardless of how many
provably-safe ancestors sit between it and Protected Root. CBD-3 confirms
this is meant to be unconditional ("no override path exists, and
symlink/ACL/group/parent-path channels are closed"), and CBD-7 requires
fail-closed on any indeterminate finding anywhere in that chain.

No document in this repository (`docs/contracts/
HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, `PHASE_149O_20A_...`,
`PHASE_149O_20C_...`) names an intermediate, architecture-defined trust
anchor between Protected Root and the filesystem root. Given HBDC-REQ-020's
recursive threat model and the absence of any such anchor, the only
contract-supportable termination point is the actual filesystem root —
independently converging with 149O.20J.3's own conclusion and its
repaired docstring's rationale, but derived here before that docstring
was read in detail.

**Adjudication on 149O.20H's original design:** `PHASE_149O_20H_..._
IMPLEMENTATION_PLAN.md` §11 explicitly designed the terminating-walk
("does not need to prove *every* ancestor up to `/`... only that there
exists an unbroken non-writable boundary") and §428 (CBV-S3) claimed this
design "mitigated" full ancestor-replacement authority. That claim is
refuted by HBDC-REQ-020's own mechanics: a non-writable parent does not
protect against a writable grandparent replacing the parent's own
directory entry. This was a genuine design error in 149O.20H, not a
legitimate alternative contract reading — root-causing B-149O.20J.2-1.

## 5. Current repaired implementation — structural/control-flow inspection (§3)

Direct inspection of `_ancestor_chain_safe` (current production,
`src/pcae/core/hatp_class_b_topology_verifier.py:298-341`) confirms:

- No `return` on a locally-safe (`write is False`) result — only a
  diagnostic append (`ancestor_safe:...`), loop continues.
- `write is True` (proven unsafe) returns `False` immediately — correct,
  one unsafe ancestor is sufficient to reject.
- `write is None` sets `saw_indeterminate = True` and continues; the
  final result is `None` (never `True`) if any indeterminate was seen and
  no unsafe ancestor was found — fail-closed per CBD-7.
- Loop advances via `current = parent` each iteration; terminates only
  when `parent == current` (filesystem root, since `Path('/').parent ==
  Path('/')`) or `guard > 2048`, which now explicitly returns `None`
  (indeterminate) instead of falling through to stale tail logic.
- Diagnostics record every traversed ancestor with its classification.
- Both callers (§7 below) pass the actual target path into this function
  unmodified — no caller can inject a weaker boundary.

## 6. Independent attack results (§4-9)

All executed in `tests/test_phase_149o_20j_4_..._independent_
verification.py` against real filesystem state (chmod, real ACLs via
`chmod +a`, real symlinks) except where explicitly stubbed (see module
docstring: the real ancestor chain above any `tmp_path` fixture on this
development host is itself agent-writable — the user's own home
directory tree — so an unstubbed real walk to `/` would correctly reject
for a reason unrelated to the property under test; `_effective_write_
access` is monkeypatched to a fixed proven-safe result for paths outside
the constructed fixture subtree only, documented per-test).

| Attack | Result |
|---|---|
| Immediate parent writable | **Rejects** |
| Safe parent + writable grandparent (the decisive B-149O.20J.2-1 case) | **Rejects** |
| Multiple higher levels, each independently writable (4 distinct levels exercised) | **Rejects** at every level |
| Fully safe chain (positive case) | **Succeeds**, stable across repeated runs |
| Effective-GID-only higher-ancestor write (`os.getgroups()` excludes the gid; only `os.getegid()` grants it) | **Rejects** |
| Symlinked higher ancestor (constructed chain with a real symlink partway up) | **Rejects**, never silently skips past the symlink |
| Inspection error injected above a safe ancestor | **Result is `None`** (indeterminate), never `True` |
| Indeterminate ACL result injected at a higher ancestor | **Result is `None`**, fails closed |
| Real host, unprovisioned | `verify_class_b_deployment_conformance()` returns **not `COMPLIANT`** |

## 7. ACL-only higher-ancestor write — BLOCKING independent finding (§6)

This is the one attack class in §4-9 that **does not** pass, and it is
**not** the B-149O.20J.2-1 early-stop defect that 149O.20J.3 repaired.

**Ground truth:** on macOS, `chmod +a "<user> allow add_file,delete_child"
<dir>` (mode bits otherwise `0o555`, no POSIX write bit anywhere) grants
the agent real, directly-verified authority to create and delete
directory entries in `<dir>` — exactly the HBDC-REQ-020 threat. Confirmed
by directly creating and deleting a probe file through the ACL grant
alone.

**Defect:** `_acl_grants_agent_write_macos` (unchanged by 149O.20J.3;
pre-existing) detects an ACL grant only by searching for the literal
substring `"write"` in `ls -lde` output (`if "write" in entry or "allow
write" in entry: return True`). macOS canonicalizes directory ACL rights
to `add_file` / `add_subdirectory` / `delete_child` — confirmed
empirically: `chmod +a "... allow write" <dir>` on a directory is itself
silently rewritten by the OS to `add_file` in the stored/displayed ACL.
None of `add_file`, `add_subdirectory`, `delete_child` contain the
substring `"write"`. **A real, exploitable directory-entry-replacement
ACL grant on any ancestor is therefore never detected**, regardless of
149O.20J.3's structurally-correct complete-walk repair, because the
underlying evidence primitive it depends on for ACL facts is blind to
the realistic form of a macOS directory ACL grant.

Verified two ways:
- `test_acl_grants_agent_write_macos_direct_ground_truth` — direct call
  to `_acl_grants_agent_write` on a real ACL-granted directory, ground
  truth `True`, detected `False`.
- `test_acl_only_higher_ancestor_write_macos` — full `_ancestor_chain_
  safe` walk with grandparent ACL-granted, parent/subject POSIX-safe,
  everything above the fixture root stubbed safe: overall result `True`
  (incorrectly safe).

Both are marked `xfail(strict=True)` in the new test module (not
silently skipped) so they read as a persistent, disclosed regression
signal — not a pass — and will fail loudly (XPASS) if a future phase
repairs this without removing the marker.

**Scope note:** the file-ACL path (used for the Trusted-Git executable's
*own* ACL check, not its ancestors) is unaffected — a file's `write`
right is displayed literally as `write` by `ls -lde` (independently
confirmed), only *directory* ACL rights are canonicalized away from that
substring. The defect is specific to ancestor-directory ACL evaluation,
which is exactly the surface HBDC-REQ-017/020 and J-3's "Trusted-Git ACL
blindness... its ancestors" scope cover.

**Why 149O.20J.3's (and prior phases') test suites did not catch this:**
every existing ACL-only-higher-ancestor test in this repository —
`test_phase_149o_20j_3_..._narrow_repair.py::
test_live_acl_only_higher_ancestor_write_rejected`,
`test_phase_149o_20j_2_..._independent_verification.py::
test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_boundary`,
and the 149O.20I-era tests — monkeypatch `_acl_grants_agent_write`
directly to a fake function (e.g. `lambda path, uid, gids: path ==
grandparent`) rather than exercising the real `ls -lde`-parsing
implementation against a genuine OS-level ACL grant. This correctly
tests that `_ancestor_chain_safe` *propagates* an ACL signal, but never
tests that the signal is *computed correctly* from real ACL state. A
`git grep` confirms `tests/test_phase_149o_20j_4_..._independent_
verification.py` (this phase) is the only test file in the repository
that ever exercises a real `chmod +a` grant. This is an honest test-
design gap, not a deliberate concealment — but it is the reason a real,
independently-demonstrated bypass persisted through J-3's prior "closed"
determination and through 149O.20J.3's own attack-matrix claims.

## 8. Effective-GID-only attack, J-2 regression (§7, §15)

`_current_agent_identity()` still independently folds `os.getegid()` into
the agent's group set (`frozenset(os.getgroups()) | {os.getegid()}`),
unchanged by 149O.20J.3. An attack that monkeypatches `os.getgroups()` to
explicitly exclude the real effective gid, leaving only `os.getegid()` to
supply it, still correctly rejects a group-writable grandparent. J-2
remains independently closed; no regression.

## 9. Symlinked higher ancestor (§8)

`_is_symlink_unsafe` is applied at every level of the walk (not only
`start`), confirmed both by direct call on a symlinked path and by a
constructed chain where a symlink sits at the grandparent position: the
walk rejects and the diagnostics show the symlink was recorded, not
silently passed through to classify the real target beneath it as safe.

## 10. Higher-ancestor inspection errors (§9)

Injecting a `None` (indeterminate) result at the grandparent level, above
an otherwise locally-safe parent, forces the overall `_ancestor_chain_
safe` result to `None` — never `True`. The same holds when the
indeterminacy is injected specifically into `_acl_grants_agent_write` at
that level. Confirms CBD-7 (fail-closed on incomplete evidence) holds
throughout the full chain, not only at the level nearest the subject.

## 11. Trusted Git and Protected Root complete-chain semantics (§10-12)

Both call sites pass the actual target path directly into `_ancestor_
chain_safe` with no pre-truncation or transformation:

- `_resolve_trusted_executable_with_effective_access` (Trusted Git,
  `hatp_environment_lock_verifier._check_trusted_git` → `_resolve_
  trusted_executable_with_effective_access("git")`): `_ancestor_chain_
  safe(resolved, agent_uid, agent_gids)` where `resolved` is the git
  binary's real resolved path.
- `_check_ancestor_chain` / `_check_ancestor_replacement_equivalence`
  (Protected Root, HBDC-REQ-017/020): `_ancestor_chain_safe(root,
  agent_uid, agent_gids)` where `root` is Protected Root's resolved path.

Both independently attacked with a writable-grandparent-of-the-resolved-
target fixture (fake `git` binary for Trusted Git; the same three-level
fixture for Protected Root) and both reject. Both share the identical
symbol and identical unmodified-path-in semantics — confirmed by source
inspection (`inspect.getsource`), not assumed from symbol identity alone.
Both are equally subject to the §7 ACL-detection finding, since both
route through the same `_effective_write_access` → `_acl_grants_agent_
write` primitive; no divergence between the two call paths was found.

## 12. J.3 test-suite change review (§13)

The one 149O.20I test 149O.20J.3 modified
(`test_phase_149o_20i_hatp_class_b_topology_verifier.py::
test_ancestor_chain_safe_boundary`) added a documented stub for
`_effective_write_access` outside its own constructed fixture (treating
the region outside the fixture as an admin-controlled boundary,
analogous to Protected Root's real ancestors being admin-owned in
production) and kept its original positive assertion (`safe is True`),
adding a stronger one (`ancestor_safe` diagnostic present for the
originally-tested boundary). This preserves the test's original intent
and does not weaken the requirement — it removes host-environment
contamination from a real writable ancestor above `tmp_path`, exactly the
same technique this phase's own positive-case test uses, independently
arrived at.

Two historical assertions were left deliberately unmodified and now fail
as expected, not as regressions:
`test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_
lock_independent_implementation_verification.py::
test_deep_ancestor_writable_beyond_immediate_parent_is_caught` and
`test_phase_149o_20j_2_..._independent_verification.py::
test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_boundary`.
Both encode the pre-repair early-stop-boundary assumption directly in
their names/assertions; both are correctly superseded by this phase's own
`test_writable_grandparent_with_safe_parent_rejects` and the Trusted-Git
ancestor test in §11. No concealment: these failures are visible in both
the raw fast_green run and the narrow broad-sweep selector, consistent
with 149O.20J.3's own disclosure.

## 13. J-1 / J-3 regression (§14, §16)

`hatp_environment_lock_verifier.py` is confirmed **byte-unchanged** since
before 149O.20J.3 (`git diff --stat 72eaa241^ HEAD -- src/pcae/core/
hatp_environment_lock_verifier.py` is empty) — the `.pth` tab-form
parsing logic (J-1) is untouched by construction, independently
re-confirmed via `git diff`, not report assertion. `_resolve_trusted_
executable_with_effective_access` still runs `_effective_write_access`
(ACL-inclusive) on the resolved executable itself — J-3's file-level ACL
awareness is intact. J-3's *ancestor*-ACL awareness is exactly the §7
finding: not a regression introduced by 149O.20J.3 (the underlying ACL
primitive was already broken before J-3's original "closed"
determination), but not soundly closed either.

## 14. Production-source scope (§17)

`git diff --name-only 72eaa241^ 72eaa241 -- src/` = exactly
`src/pcae/core/hatp_class_b_topology_verifier.py`. `hatp_environment_
lock_verifier.py` and `hatp_class_b_conformance.py` confirmed byte-
unchanged (`git diff --stat` empty) across the full four-commit J.3
range (`72eaa241`, `c029a5f1`, `8bfb89a5`, `4d6bec5d`). Of those four,
only `72eaa241` touches `src/`; `c029a5f1` touches only the test file
(self-check fix, 19 lines); `8bfb89a5`/`4d6bec5d` are report/lifecycle-
metadata-only commits. No current HMIC-25 file changed.

## 15. HMIC non-binding, zero-consumer, read-only wall (§18-20)

- `_FROZEN_AUTHORITY_BEARING_FILES` in `hatp_mandatory_certification.py`:
  `assert len(...) == 25` still holds; none of the three Class-B verifier
  module paths appear in it (`git-grep`-confirmed).
- `_CONTRACT_IDENTITY_FILES`: still exactly 5 members (HMRC-001,
  HATP-001, HSCE-001, RAE-001, HBDC-001).
- Zero-consumer: `git grep` for each of `hatp_class_b_topology_verifier`,
  `hatp_environment_lock_verifier`, `hatp_class_b_conformance` under
  `src/` returns only the three modules themselves (no external
  production consumer). No readiness, certification, activation,
  Permission Broker, or rollback code path references them.
- Read-only wall: source inspection of both modules confirms no
  `os.chmod`/`os.chown`/`os.mkdir`/`os.makedirs`/`shutil.rmtree`/
  `os.remove`/`os.unlink`/file-write call anywhere.
- Real-host result: `verify_class_b_deployment_conformance()` on this
  (deliberately unprovisioned) host returns a non-`COMPLIANT` status;
  `git status --short` before/after this phase's test run shows no
  filesystem mutation.

## 16. Test results actually run

- `tests/test_phase_149o_20j_4_class_b_full_ancestor_chain_verification_
  repair_independent_verification.py`: **25/25** (23 passed, 2 xfailed —
  both documenting the §7 finding, `strict=True`).
- `pytest -m fast_green -n auto` (raw): 71 failed / 6771 passed / 5
  skipped / 1 pre-existing collection error (`fido2` missing, unrelated).
  None of the 71 failures are in the new J.4 test file. Deselecting the
  exact 71 raw-failing node IDs (argv-list subprocess, not shell
  interpolation) via a fresh Python-driven rerun: **clean-deselected
  citation: 0 failed, 6771 passed, 5 skipped, 1 pre-existing collection
  error** — cited as the canonical `test_results.fast_green` value.
- `pytest -k "class_b or hbdc or 149o_20j" -n auto`: 11 failed / 617
  passed / 5 skipped / 2 xfailed / 1 pre-existing collection error — all
  11 failures are pre-existing fixed-commit self-checks or the two
  intentionally-superseded historical assertions (§12), zero delta
  attributable to this phase's own work.
- `git status --short` before writing the report/metadata files: only
  the new test module, no production source changes.

## 17. Adjudications

- **B-149O.20J.2-1** (the early-stop bypass specifically): the repaired
  `_ancestor_chain_safe` complete-walk structure is independently
  verified correct against every attack class in this phase's scope
  except the pre-existing ACL-detection primitive defect (§7), which is
  a **distinct** defect from the early-stop bypass this ID names.
  **B-149O.20J.2-1: INDEPENDENTLY CONFIRMED CLOSED AT NON-AUTHORITATIVE
  VERIFIER IMPLEMENTATION BOUNDARY** (the early-stop-specific defect
  only; this does not imply HMIC binding, deployment, readiness, or
  operational closure).
- **New finding, tracked as B-149O.20J.4-1** — ACL-only higher-ancestor
  write on macOS (directory ACL rights canonicalized away from the
  literal substring `"write"`) is **not detected**, in
  `_acl_grants_agent_write_macos`. **STATUS: OPEN — BLOCKING for any
  claim that HBDC-REQ-016/017/020's ACL channel is closed on macOS.**
  This also means J-3's original "ACL-only... ancestors" closure claim
  should be understood as closed only for the file-level (Trusted-Git
  executable's own) ACL check, not for ancestor-directory ACL grants;
  J-3 is not reopened wholesale (the file-level and complete-walk-
  structure aspects it actually tested remain independently confirmed),
  but its ancestor-ACL sub-claim is now known-incomplete.
- **J-1**: REMAINS INDEPENDENTLY CLOSED (byte-unchanged, re-confirmed).
- **J-2**: REMAINS INDEPENDENTLY CLOSED (re-confirmed end-to-end).
- **J-3**: file-level ACL awareness REMAINS INDEPENDENTLY CLOSED;
  ancestor-level ACL awareness is now known-incomplete per B-149O.20J.4-1
  (not reopened as a regression — the defect predates J-3's repair and
  J-3 never actually exercised real ACL state).
- **CBV-S1**: **OPEN — HMIC SOURCE-SCOPE BINDING STILL PENDING.** The
  verifier source remains outside HMIC-001's frozen 25-file identity.
  This phase does not HMIC-bind anything.
- **CBV-S10**: **OPEN — READINESS CONTRACT/INTEGRATION GAP.** No
  readiness contract or integration changed in this phase.
- **Class-B**: CONTRACT VERIFIED — VERIFIER IMPLEMENTATION
  INDEPENDENTLY VERIFIED FOR THE EARLY-STOP DEFECT — **ONE KNOWN OPEN
  ACL-DETECTION GAP (B-149O.20J.4-1)** — NOT PROVISIONED.
- **HATP**: NOT READY.
- **Runtime**: Observed / observe / unavailable (confirmed via `pcae
  runtime inspect`).

## 18. Next-phase recommendation

Because a genuine, independently-demonstrated defect was found
(B-149O.20J.4-1), this phase does **not** recommend proceeding to
149O.20K (HMIC Class-B Verifier Source-Scope Contract Evolution) as the
next phase. It recommends, as the **narrowest justified follow-up**:

**149O.20J.5 — Class-B ACL-Only Higher-Ancestor Detection Repair
(macOS)**: repair `_acl_grants_agent_write_macos`'s right-name matching
so it recognizes the real macOS directory ACL rights relevant to
HBDC-REQ-020 (`add_file`, `add_subdirectory`, `delete_child`, plus the
file-level `write`/`append`/`writeextattr` rights already covered by
substring match), re-verify against real `chmod +a` grants (not
mocked), and add at least one real-ACL test to the permanent suite so
this class of gap cannot silently recur. Only once 149O.20J.5 is
independently verified should 149O.20K be reconsidered, and 149O.20K
must still perform its own fresh transitive authority-dependency closure
analysis under HMIC-REQ-052 rather than assuming the HMIC source count
becomes 28.

This phase does not authorize 149O.20J.5. Repair was not performed here:
this is a verification-only phase, and no explicit governed-phase rule
was located authorizing an in-phase bounded repair of a newly-discovered
defect outside B-149O.20J.2-1's own scope.

## 19. Governance results

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, outside this phase's allowed-file scope)
- `pcae_push_check`: clean (nothing_to_push, prior to this phase's commits)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: telegram configured/enabled
- `pcae_phase_report_reconcile` (149O.20J.3, read-only): reconciled, no mutation
