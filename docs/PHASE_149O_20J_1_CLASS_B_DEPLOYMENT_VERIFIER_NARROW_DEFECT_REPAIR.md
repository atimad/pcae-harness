# Phase 149O.20J.1 — Class-B Deployment Verifier / Model-A Environment-Lock Narrow Defect Repair

**Status:** Repair implemented. **NARROW DEFECT REPAIR ONLY** — repairs
exactly the three Blocking findings recorded by Phase 149O.20J, and
nothing else. No HMIC source-scope evolution, no Class-B provisioning,
no readiness/certification/activation change. Verifier source remains
outside HMIC's frozen identity; `COMPLIANT` remains diagnostic-only.
**INDEPENDENT RE-VERIFICATION PENDING** (recommended: Phase 149O.20J.2).

## 0. Baseline

Phase 149O.20J (independent implementation verification of the three
149O.20I production modules) found exactly three Blocking-for-
HMIC-binding-progression defects and recorded them without repair, per
its own explicit record-do-not-repair scope. Phase entry for 149O.20J.1
is 149O.20J's own exit state: repo clean, `origin/main..HEAD = 0`, all
governance checks passing, 149O.20J reconciled.

## 1. The Three Blocking Findings (as recorded by 149O.20J)

| ID | Module | Requirement | Defect |
|---|---|---|---|
| B-CBV-J-1 | `hatp_environment_lock_verifier.py` | HBDC-REQ-031 | `_check_pth_files`'s executable-import predicate (`line.strip().startswith("import ")`) misses the tab-delimited `import\t` form that CPython's real `site.addpackage()` still executes. |
| B-CBV-J-2 | `hatp_class_b_topology_verifier.py` | (all effective-write-access checks) | `_current_agent_identity()` derives effective groups from `os.getgroups()` alone, never independently folding in `os.getegid()`. POSIX does not guarantee the effective gid appears in the supplementary-group list in every process-identity configuration. |
| B-CBV-J-3 | `hatp_environment_lock_verifier.py` / `hatp_class_b_topology_verifier.py` | HBDC-REQ-038 | `_resolve_trusted_executable` (backing `_check_trusted_git`) checks only mode+group bits, never ACL, deliberately, to avoid recursion into `getfacl` resolution — an ACL-only agent write grant to the git executable, its ancestors, or a PATH-preceding directory would not be detected. |

## 2. Historical Reproduction (before repair)

Each finding was independently reproduced against the phase-entry source
before any production edit, matching 149O.20J's own evidence:

- **J-1**: confirmed CPython's real `site.py` `addpackage()` source
  (running interpreter, 3.14) reads `if line.startswith(("import ",
  "import\t")): exec(line)` against the **raw, unstripped** line (after
  first excluding `#`-prefixed comment lines and blank lines). The
  pre-repair predicate `line.strip().startswith("import ")` recognizes
  only the space-delimited form.
- **J-2**: confirmed `_current_agent_identity`'s pre-repair source
  contained no reference to `os.getegid()` (`inspect.getsource`); the
  151O.20J suite's own `test_agent_effective_gid_not_in_getgroups_can_
  be_missed` documents the same absence as evidence.
- **J-3**: confirmed `_resolve_trusted_executable`'s pre-repair source
  called only `_mode_and_group_write_access`, never `_effective_write_
  access`/`_acl_grants_agent_write`, by direct `inspect.getsource`
  inspection, matching the 149O.20J suite's own
  `test_git_acl_only_write_grant_is_not_detected_by_trusted_executable_
  resolution`.

All three were independently reproducible; none required reassessment
per item 3's stop condition.

## 3. J-1 Repair — `.pth` Executable-Import Detection

Added `_pth_line_is_executable(line: str) -> bool` in
`hatp_environment_lock_verifier.py`, mirroring CPython's own
`site.addpackage()` per-line classification exactly (verified against
the running interpreter's `site` module source, not against prior-phase
prose):

```python
def _pth_line_is_executable(line: str) -> bool:
    if line.startswith("#"):
        return False
    if line.strip() == "":
        return False
    return line.startswith(("import ", "import\t"))
```

`_check_pth_files` now calls this helper instead of the inline
`line.strip().startswith("import ")` predicate.

**CPython grammar comparison** (from `site.addpackage()`, CPython
3.14's actual `site.py`):

```python
for n, line in enumerate(pth_content.splitlines(), 1):
    if line.startswith("#"):
        continue
    if line.strip() == "":
        continue
    try:
        if line.startswith(("import ", "import\t")):
            exec(line)
            continue
        line = line.rstrip()
        dir, dircase = makepath(sitedir, line)
        ...
```

The repaired helper is a direct transcription of this classification —
comment check first (raw line), blank check second, then the two-form
executable check on the **raw** (not `.strip()`-ed) line. This also
corrects a second, narrower divergence beyond the reported tab-form
miss: the pre-repair `.strip()`-first predicate would have over-flagged
a line like `"  import foo"` (leading whitespace) as executable, which
real CPython does **not** execute (its own `startswith` check runs on
the raw line, unstripped) — the repair matches CPython exactly in both
directions, not just the disclosed direction.

Non-executable path-line detection (agent-writable `.pth` file, path
injection) is unaffected — `_check_pth_files` still flags the whole
file unsafe if it is itself agent-writable, independent of line
content.

## 4. J-2 Repair — Effective Group Derivation

`_current_agent_identity()` in `hatp_class_b_topology_verifier.py`:

```python
def _current_agent_identity() -> "tuple[int, frozenset[int]]":
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}
```

`frozenset(os.getgroups()) | {os.getegid()}` is a set union: `os.
getegid()` is always folded in independently of whatever `os.
getgroups()` returns, and duplicates (the common case, where the
supplementary-group convention already includes the effective gid) are
naturally deduplicated by set semantics — no behavior regression for
hosts where the two already agree. `os.getgid()` (real gid) is not
substituted for `os.getegid()` (effective gid) anywhere; the function
still returns `os.geteuid()` (effective uid) unchanged for the first
element.

This is the only call site of process-group derivation in either
module; every check in both `hatp_class_b_topology_verifier.py` and
`hatp_environment_lock_verifier.py` receives `agent_gids` from this one
function (directly or via a caller that itself calls it), so the repair
is centralized, not duplicated.

## 5. J-3 Repair — Trusted-Git Effective-Access (ACL) Check

**Design constraint (no-recursion trap):** `_resolve_trusted_executable`
is the PATH-precedence walk used both directly by `_check_trusted_git`
and indirectly by the ACL branch itself (`_acl_grants_agent_write_
linux`/`_macos` resolve `getfacl`/`ls` through it). Giving that walk
ACL awareness would make ACL-tool resolution mutually recursive against
itself. The repair therefore leaves `_resolve_trusted_executable`
byte-for-byte unchanged (still `_mode_and_group_write_access`-only,
confirmed by `tests/test_phase_149o_20j_1_..._narrow_defect_repair.py
::test_resolve_trusted_executable_base_primitive_unchanged`) and adds a
new function that composes it with the *existing*, already-ACL-aware
Protected Root primitives instead of writing a second ACL parser:

```python
def _resolve_trusted_executable_with_effective_access(name: str) -> Optional[Path]:
    resolved = _resolve_trusted_executable(name)
    if resolved is None:
        return None
    agent_uid, agent_gids = _current_agent_identity()
    write, _reason, _evidence = _effective_write_access(resolved, agent_uid, agent_gids)
    if write is not False:
        return None  # writable (mode/group/ACL) or indeterminate -> untrusted
    safe, _diagnostics = _ancestor_chain_safe(resolved, agent_uid, agent_gids)
    if safe is not True:
        return None  # ancestor writable (incl. ACL) or indeterminate -> untrusted
    return resolved
```

`_check_trusted_git()` now calls this wrapper instead of the bare
`_resolve_trusted_executable`.

**Why this does not recurse:** the wrapper's own nested calls
(`_effective_write_access` → `_acl_grants_agent_write` →
`_resolve_trusted_executable("getfacl")`/`("ls")`) always resolve
through the narrow, unchanged base primitive, never through this
wrapper — the wrapper is a one-way composition, not a cycle. Confirmed
directly by `test_no_acl_tool_resolution_recursion_through_wrapper`,
which poisons the wrapper itself to raise if ever re-entered and
exercises the real ACL branch's tool-resolution path.

**Shared effective-access semantics:** the wrapper reuses
`_effective_write_access` and `_ancestor_chain_safe` — the exact same
primitives already backing Protected Root's `HBDC-REQ-016`
(ACL-effective-access) and `HBDC-REQ-017` (ancestor chain, itself ACL-
aware). Topology and trusted-Git checks now share one effective-access
policy, not two divergent ones.

**Fail-closed on ACL indeterminacy:** `_effective_write_access` returns
`(None, "acl_inspection_unavailable", ...)` when ACL tooling is
unresolvable; the wrapper's `write is not False` check treats `None`
(indeterminate) identically to `True` (writable) — both reject. Same
pattern for the ancestor walk. ACL-tool unavailability is never
interpreted as "no ACL exists."

**Git-executable and ancestor ACL coverage:** the wrapper checks ACL on
the resolved git executable itself (`_effective_write_access`) and on
its full ancestor chain (`_ancestor_chain_safe`, which is itself
ACL-aware per-ancestor) — both the "Git executable ACL" and "Git
ancestor ACL" requirements from the governing prompt are covered by
this single composition, not two separate mechanisms.

**PATH-preceding-directory defense preserved:** unchanged — still
performed entirely inside the untouched `_resolve_trusted_executable`.

## 6. Regression Results

### 6.1 Existing 20I test suites (98 tests)

`tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py`,
`tests/test_phase_149o_20i_hatp_environment_lock_verifier.py`,
`tests/test_phase_149o_20i_hatp_class_b_conformance.py`: **98/98
passed**, zero regressions, including
`test_trusted_git_fake_git_earlier_on_path_rejected` and both `.pth`
detection tests.

### 6.2 Frozen 20J independent-verification suite (63 tests)

`tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_
environment_lock_independent_implementation_verification.py`: **61
passed, 1 skipped (pre-existing, unrelated), 1 failed** —
`test_agent_effective_gid_not_in_getgroups_can_be_missed`. This is a
**disclosed, expected, single regression**: the test is not a security
behavior assertion but a source-absence finding-confirmation
(`assert "getegid" not in src`), and its own docstring instructs:
*"if this assertion now fails, the gap has been closed and this test
should be updated."* Per item 34 (historical-defect-snapshot
preservation), this frozen file is left unmodified — the pre-repair
state remains reconstructable via git history at 149O.20J's own
commits (`fa5f54af`, `cfd93180`). The other two finding-tests in this
suite (`test_pth_executable_import_line_with_tab_bypasses_detection`,
`test_git_acl_only_write_grant_is_not_detected_by_trusted_executable_
resolution`) continue to pass unmodified: the former asserts against an
inlined copy of the *old* predicate (not live production code), and the
latter asserts against `_resolve_trusted_executable`'s own source,
which — by design (§5 above) — remains byte-unchanged.

### 6.3 New repair-verification suite (26 tests, new)

`tests/test_phase_149o_20j_1_class_b_deployment_verifier_narrow_defect_
repair.py`: **26/26 passed.** Independently targets exactly J-1/J-2/J-3
with positive security assertions against the live repaired production
functions (never inlined pre-repair logic), plus cross-cutting
regression guards (read-only AST scan across all three modules, public
API zero-parameter signatures, real-host non-COMPLIANT result,
aggregator byte-unchanged-since-HEAD check).

### 6.4 Broad sweep (`pytest -k "class_b or hbdc or hmic or 149o_20"`)

Before repair (phase-entry baseline, `git stash -u`): 44 failed / 1107
passed / 5 skipped / 1 collection error (`test_phase_149o_7_...` —
missing `fido2` dependency, pre-existing, unrelated, excluded from the
delta below). After repair: 52 failed / 1125 passed / 5 skipped / 1
collection error (same).

**Net delta: +8 failed, +18 passed.** Every one of the 8 new failures
is explained:

- 7 are **pre-existing "no dirty `src/pcae/` working-tree changes"
  snapshot tests** belonging to unrelated historical phases (149O.19.4,
  20a, 20c, 20d, 20d.1, 20e, 20h) — each independently re-derives `git
  diff HEAD -- src/pcae/` (or an equivalent working-tree check) and
  necessarily fails while this phase's two production files are
  uncommitted. Confirmed by direct source inspection (e.g.
  `test_phase_149o_17_hmrc_implementation_plan_completeness.py::test_
  no_src_pcae_files_changed_name_only` runs `_git("diff", "--name-only",
  "HEAD", "--", "src/pcae/")`) that these check the *current* working
  tree, not a permanently frozen historical diff — they resolve once
  this phase's commit lands (re-verified in §16 below).
- 1 is the disclosed `test_agent_effective_gid_not_in_getgroups_can_be_
  missed` regression from §6.2.

Zero unexplained new failures.

### 6.5 Fast Green

Phase-entry baseline (`git stash -u`, `pytest -m fast_green -n auto`,
deselecting the pre-existing `fido2`-import collection error): **69
failed / 6720 passed / 5 skipped / 1 error** (matches 149O.20J's own
citation). After repair: **80 failed / 6735 passed / 5 skipped / 1
error.** Net delta: **+11 failed, +15 passed** (parametrization/xdist
worker-count variance accounts for the passed-count not equaling the
raw +26 new-test count exactly; see §6.3 for the direct, deterministic
26/26 figure). The 11 new failures are exactly the same 10 dirty-
working-tree snapshot tests (a superset of §6.4's 7, since fast_green
sweeps more phases) plus the same single disclosed regression — no
additional, unexplained failures.

## 7. HBDC Requirement / Check Mapping Regression

All `HBDC-REQ-*` check rows present before repair remain present after
repair; no check was removed, renamed, or had its `check_id` changed.
`verify_class_b_topology_conformance()` and
`verify_environment_lock_conformance()` both still enumerate the same
requirement sets confirmed by `test_all_hbdc_req_rows_present` (20I
suite, unmodified, still passing).

## 8. CBD Invariants

149O.20J recorded the two implementation-side gaps against **CBD-3**
(effective-access, not raw mode bits — the `os.getegid()` gap) and
**CBD-6** (Model-A environment lock — the `.pth` tab-form and
trusted-Git ACL gaps). Both are now implementation-repaired at the
verifier-module level: CBD-3's effective-access derivation now
independently folds in `os.getegid()`; CBD-6's `.pth` detection now
matches CPython's real executable-line grammar and its trusted-Git
check now applies the same ACL-inclusive effective-access policy used
elsewhere. **This phase does not claim independent closure of CBD-3 or
CBD-6** — that determination belongs to 149O.20J.2's independent
re-verification, not to the repairing phase itself.

## 9. 21 HBDC Attacks + Additional Attack Regression

Re-ran the fake-Git-via-hostile-PATH attack
(`test_fake_git_via_hostile_path_is_rejected`, 20J suite, unmodified,
still passing, plus a repair-suite duplicate exercising the new
wrapper directly), the PATH-preceding-directory attack, the `.pth`
path-injection attack, the `sys.meta_path` re-attack, the CWD-shadow
attack, and the fake-PCAE / module-origin-containment attack (all in
the unmodified 20I/20J suites) — all still reject as before. No new
bypass found in any of the 21 frozen HBDC attacks or the additional
20C-style attack list; none of the three repairs touches any of those
checks' logic.

## 10. Self-Caught 20I Defect Regression

Both of 149O.20I's own self-caught fixes — the `sys.meta_path`
class-vs-instance identity fix and the `HBDC-REQ-004`
`environ`-false-positive narrowing — are exercised by the unmodified
20I/20J suites (`test_meta_path_recognizes_class_based_and_instance_
based_expected_finders` and the environ-admin-inference scan tests) and
continue to pass unchanged.

## 11. Real-Host Result and Non-Mutation

Invoked all three modules' public APIs read-only against the real,
unprovisioned dev host after repair. Result unchanged: `NOT_COMPLIANT`
(no provisioning was performed or expected). Before/after `git status
--short` (outside this phase's own tracked edits), `.pcae/` directory
listing, and environment snapshot confirmed zero mutation from any
verifier invocation.

## 12. Zero Production Authority Consumers / HMIC Non-Binding

Repository-wide search (`grep -r` across `src/pcae/**`) confirms zero
files outside the three-module island import or reference
`hatp_class_b_topology_verifier`, `hatp_environment_lock_verifier`, or
`hatp_class_b_conformance` by name, other than the three modules
referencing each other. `hatp_mandatory_cutover.py`,
`hatp_mandatory_certification.py`, and
`scripts/hatp_certification_admin.py` were individually re-confirmed to
contain none of the three module names. `HMIC-REQ-050`'s
`_FROZEN_AUTHORITY_BEARING_FILES` constant and the
`_AUTHORITY_MODULE_RELATIVE_PATHS` 19-entry literal in
`hatp_environment_lock_verifier.py` were **not** touched by this phase.

## 13. CBV-S1 / CBV-S10

**CBV-S1: REPAIR IMPLEMENTED — INDEPENDENT VERIFICATION REQUIRED — HMIC
SOURCE-SCOPE BINDING STILL PENDING — NOT CLOSED.** The current-state
safety half of CBV-S1 (new verifier source unbound; zero production
authority consumers) is re-confirmed unchanged by this phase (§12); the
progression half (whether the repaired implementation is now suitable
for a future, separately-governed HMIC-binding phase) is explicitly
**not** adjudicated here — that is 149O.20J.2's and, later, 149O.20K's
job.

**CBV-S10: UNCHANGED — READINESS CONTRACT/INTEGRATION GAP REMAINS — NOT
CLOSED.** No readiness contract or integration code was touched.

## 14. Aggregator Stability

`hatp_class_b_conformance.py` was read during primary-source review;
none of the three findings required any change to it (its aggregation
logic only combines already-produced `ClassBCheckResult` rows and does
not itself derive process identity, `.pth` content, or trusted-Git
resolution). Confirmed **byte-unchanged** by
`git diff --name-only HEAD -- src/pcae/core/hatp_class_b_conformance.py`
returning empty, both manually and via the new suite's
`test_aggregator_module_byte_unchanged_since_20i`.

## 15. Findings

No new findings beyond the three repaired. One **disclosed, expected,
non-blocking** regression: `test_agent_effective_gid_not_in_getgroups_
can_be_missed` (frozen 149O.20J evidence, superseded per its own
docstring — see §6.2). One pre-existing, unrelated, non-blocking
observation carried forward unchanged: `HBDC-REQ-012`'s own AST
self-check still only scans `hatp_class_b_topology_verifier.py`'s own
source, not the other two modules (149O.20J's own disclosed
observation; out of this narrow repair's scope).

## 16. Governance Close Checks (post-commit)

Re-ran `pcae health`, `pcae check`, `pcae status coherence`, `pcae
doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae
notify status` after this phase's commit landed, and re-ran the 10
previously-new "dirty working tree" test failures from §6.4/§6.5 in
isolation to confirm they resolve once `git diff HEAD -- src/pcae/` is
empty again. Results recorded in the final report below.

## 17. Repair Verdict

**CLASS-B VERIFIER NARROW DEFECT REPAIR: IMPLEMENTED — 3/3 BLOCKING
FINDINGS REPAIRED — INDEPENDENT RE-VERIFICATION PENDING — VERIFIER
REMAINS NON-AUTHORITATIVE — SOURCE REMAINS OUTSIDE HMIC — POSITIVE
CONSUMPTION REMAINS FORBIDDEN.**

- J-1: **REPAIRED — INDEPENDENT VERIFICATION PENDING**
- J-2: **REPAIRED — INDEPENDENT VERIFICATION PENDING**
- J-3: **REPAIRED — INDEPENDENT VERIFICATION PENDING**

**CBV-S1:** REPAIR IMPLEMENTED — INDEPENDENT VERIFICATION REQUIRED —
HMIC SOURCE-SCOPE BINDING STILL PENDING — NOT CLOSED.
**CBV-S10:** UNCHANGED / NOT CLOSED.
**Class-B:** CONTRACT VERIFIED — VERIFIER REPAIRED
NON-AUTHORITATIVELY — NOT PROVISIONED.
**HATP:** NOT READY.

## 18. Recommended Next Phase

**149O.20J.2 — Class-B Deployment Verifier Narrow Defect Repair
Independent Verification.** Must independently: reproduce the three
historical defects from pre-repair source (this phase's own parent
commit); prove `.pth` detection now matches supported CPython
executable-line semantics including the tab form (and the
leading-whitespace non-executable case); prove `os.getegid()` is
independently folded into effective groups and that an effective-GID-
only group-write is now detected; independently attack trusted-Git
executable and ancestor ACL; verify ACL-inspection-failure fail-closed
behavior; verify no ACL-tool recursion was introduced; re-run the
fake-Git PATH attack; confirm topology/Git effective-access policy
equivalence; confirm read-only behavior and zero authority consumers;
confirm the verifier remains outside HMIC scope. Only after
149O.20J.2 passes should 149O.20K (HMIC source-scope contract
evolution) be attempted. **Not started, not authorized by this phase.**
